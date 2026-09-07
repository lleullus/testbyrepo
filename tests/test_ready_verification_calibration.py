from __future__ import annotations

import copy
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evaluation" / "ready-verification"
MANIFEST_PATH = EVAL / "manifest.json"
BASELINE_PATH = EVAL / "baseline-observations.json"
SCORER_PATH = EVAL / "score_result.py"
CALIBRATE_PATH = EVAL / "calibrate.py"


def load_scorer():
    spec = importlib.util.spec_from_file_location("ready_verification_score_result", SCORER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Ready verification scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_calibrate():
    sys.path.insert(0, str(EVAL))
    try:
        spec = importlib.util.spec_from_file_location("ready_verification_calibrate", CALIBRATE_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load Ready verification calibration CLI")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class ReadyVerificationCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.scorer = load_scorer()
        self.calibrate = load_calibrate()

    @staticmethod
    def manifest_with(cases: list[dict[str, object]], **gate_overrides: int) -> dict[str, object]:
        gate = {
            "false_verified": 0,
            "normal_false_rejection": 0,
            "malformed_terminal": 0,
            "target_mutation_runs": 0,
            "missing_cases": 0,
        }
        gate.update(gate_overrides)
        return {
            "schema": "iis-ready-verification-calibration/v1",
            "release_gate": gate,
            "cases": cases,
        }

    @staticmethod
    def case(case_id: str, expected: str, **overrides: object) -> dict[str, object]:
        case = {
            "case_id": case_id,
            "family": "calibration",
            "variant": "core",
            "expected": expected,
            "normal_twin": expected == "VERIFIED",
        }
        case.update(overrides)
        return case

    @staticmethod
    def expected_records(manifest: dict[str, object]) -> list[dict[str, object]]:
        minimum_runs = manifest.get("minimum_runs_per_case", 1)
        if isinstance(minimum_runs, bool) or not isinstance(minimum_runs, int) or minimum_runs < 1:
            minimum_runs = 1
        return [
            {
                "case_id": case["case_id"],
                "parsed_verdict": case["expected"],
                "target_mutated": False,
            }
            for case in manifest["cases"]
            for _ in range(minimum_runs)
        ]

    @staticmethod
    def write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def report_inputs(self, root: Path) -> tuple[Path, Path, dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
        run_root = root / "run-a"
        events_path = run_root / "verify" / "events.jsonl"
        events_path.parent.mkdir(parents=True)
        events_path.write_text(json.dumps({
            "type": "message_end", "message": {
                "role": "assistant", "stopReason": "stop",
                "provider": "opencodex", "model": "gpt-6-astra",
                "content": [{"type": "text", "text": "Verification Verdict: VERIFIED"}],
            },
        }) + '\n{"type":"agent_end"}\n', encoding="utf-8")
        metadata_path = root / "metadata.json"
        self.write_json(metadata_path, {"case_id": "report-normal", "run_id": "run-a", "run_root": str(run_root)})
        cohort_path = root / "cohort.json"
        self.write_json(cohort_path, [str(metadata_path)])
        manifest = self.manifest_with([self.case("report-normal", "VERIFIED")])
        manifest_path = root / "manifest.json"
        self.write_json(manifest_path, manifest)
        records = [{"case_id": "report-normal", "run_id": "run-a", "parsed_verdict": "VERIFIED", "target_mutated": False}]
        reviews = [{
            "case_id": "report-normal",
            "run_id": "run-a",
            "causal_evidence_sufficient": True,
            "evidence_refs": [{"path": str(events_path), "sha256": hashlib.sha256(events_path.read_bytes()).hexdigest()}],
            "reason": "Independent review checked this run's raw verification events.",
        }]
        return cohort_path, manifest_path, manifest, records, reviews

    def run_report_cli(self, root: Path, cohort_path: Path, manifest_path: Path, records: list[dict[str, object]],
                       reviews: list[dict[str, object]], name: str) -> tuple[int, dict[str, object]]:
        results_path, reviews_path = root / f"{name}-results.json", root / f"{name}-reviews.json"
        self.write_json(results_path, records)
        self.write_json(reviews_path, reviews)
        stdout = io.StringIO()
        argv = ["calibrate.py", "report", "--cohort", str(cohort_path), "--results", str(results_path),
                "--reviews", str(reviews_path), "--manifest", str(manifest_path)]
        with patch.object(sys, "argv", argv), redirect_stdout(stdout):
            exit_code = self.calibrate.main()
        return exit_code, json.loads(stdout.getvalue())

    def test_scorer_reports_baseline_target_mutation_as_false_verified_and_incomplete(self) -> None:
        records = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        report = self.scorer.score(self.manifest, records)

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["false_verified"], 1)
        self.assertEqual(report["target_mutation_runs"], 1)
        self.assertGreater(len(report["missing_cases"]), 0)

    def test_expected_verdicts_pass_without_pinning_fixture_inventory(self) -> None:
        report = self.scorer.score(self.manifest, self.expected_records(self.manifest))

        self.assertTrue(report["release_pass"])
        self.assertEqual(report["class_confusion"], {
            f'{case["expected"]} -> {case["expected"]}': sum(
                1 for candidate in self.manifest["cases"] if candidate["expected"] == case["expected"]
            )
            for case in self.manifest["cases"]
        })

    def test_allowed_alternative_verdict_is_not_an_unexpected_classification(self) -> None:
        manifest = self.manifest_with(
            [
                self.case(
                    "evidence-limited",
                    "INCONCLUSIVE",
                    allowed_verdicts=["INCONCLUSIVE", "VERIFICATION NOT STARTED"],
                    required_observations={"INCONCLUSIVE": ["the protected surface was unavailable"]},
                )
            ]
        )
        report = self.scorer.score(
            manifest,
            [{"case_id": "evidence-limited", "parsed_verdict": "VERIFICATION NOT STARTED"}],
        )

        self.assertTrue(report["release_pass"])
        self.assertEqual(report["unexpected_verdict_runs"], 0)

    def test_explicitly_allowed_verified_is_not_a_false_verified(self) -> None:
        manifest = self.manifest_with([
            self.case("conditional-evidence", "INCONCLUSIVE", allowed_verdicts=["INCONCLUSIVE", "VERIFIED"])
        ])
        report = self.scorer.score(manifest, [{"case_id": "conditional-evidence", "parsed_verdict": "VERIFIED"}])
        self.assertTrue(report["release_pass"])
        self.assertEqual(report["false_verified"], 0)

    def test_defect_suite_cannot_pass_by_returning_inconclusive_for_every_run(self) -> None:
        manifest = self.manifest_with(
            [self.case("defect-a", "FAILED"), self.case("defect-b", "FAILED")]
        )
        report = self.scorer.score(
            manifest,
            [
                {"case_id": "defect-a", "parsed_verdict": "INCONCLUSIVE"},
                {"case_id": "defect-b", "parsed_verdict": "INCONCLUSIVE"},
            ],
        )

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["unexpected_verdict_runs"], 2)
        self.assertEqual(report["class_confusion"], {"FAILED -> INCONCLUSIVE": 2})

    def test_evidence_limited_case_cannot_be_reported_as_failed(self) -> None:
        manifest = self.manifest_with(
            [
                self.case(
                    "unavailable-surface",
                    "INCONCLUSIVE",
                    allowed_verdicts=["INCONCLUSIVE", "VERIFICATION NOT STARTED"],
                )
            ]
        )
        report = self.scorer.score(
            manifest,
            [{"case_id": "unavailable-surface", "parsed_verdict": "FAILED"}],
        )

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["unexpected_verdict_runs"], 1)

    def test_target_mutation_blocks_an_otherwise_expected_result_set(self) -> None:
        records = self.expected_records(self.manifest)
        records[0]["target_mutated"] = True
        report = self.scorer.score(self.manifest, records)

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["target_mutation_runs"], 1)

    def test_normal_twin_rejection_remains_a_release_gate(self) -> None:
        manifest = self.manifest_with([self.case("normal", "VERIFIED", normal_twin=True)])
        report = self.scorer.score(
            manifest,
            [{"case_id": "normal", "parsed_verdict": "INCONCLUSIVE"}],
        )

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["normal_false_rejection"], 1)

    def test_unknown_records_remain_a_release_gate(self) -> None:
        records = self.expected_records(self.manifest)
        records.append({"case_id": "not-in-manifest", "parsed_verdict": "VERIFIED"})
        report = self.scorer.score(self.manifest, records)

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["unknown_record_case_ids"], ["not-in-manifest"])

    def test_invalid_terminal_is_unexpected_and_blocks_release(self) -> None:
        records = self.expected_records(self.manifest)
        records[0]["parsed_verdict"] = "unparseable terminal output"
        report = self.scorer.score(self.manifest, records)

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["malformed_terminal"], 1)
        self.assertEqual(report["unexpected_verdict_runs"], 1)

    def test_record_supplied_oracle_cannot_make_a_wrong_verdict_pass(self) -> None:
        manifest = self.manifest_with([self.case("known-defect", "FAILED")])
        report = self.scorer.score(
            manifest,
            [
                {
                    "case_id": "known-defect",
                    "parsed_verdict": "VERIFIED",
                    "expected": "VERIFIED",
                }
            ],
        )

        self.assertFalse(report["release_pass"])
        self.assertEqual(report["false_verified"], 1)
        self.assertEqual(report["unexpected_verdict_runs"], 1)

    def test_invalid_or_empty_allowed_verdicts_cannot_relax_the_gate(self) -> None:
        for allowed_verdicts in ([], "FAILED"):
            with self.subTest(allowed_verdicts=allowed_verdicts):
                manifest = self.manifest_with(
                    [self.case("invalid-contract", "FAILED", allowed_verdicts=allowed_verdicts)],
                    unexpected_verdict_runs=1,
                )
                report = self.scorer.score(
                    manifest,
                    [{"case_id": "invalid-contract", "parsed_verdict": "FAILED"}],
                )

                self.assertFalse(report["release_pass"])
                self.assertEqual(report["invalid_allowed_verdict_cases"], ["invalid-contract"])

    def test_repeated_execution_requires_unique_run_ids_and_minimum_runs(self) -> None:
        duplicate_records = self.expected_records(self.manifest)
        for record in duplicate_records:
            record["run_id"] = "reused-run"
        duplicate_report = self.scorer.score(self.manifest, duplicate_records)

        repeated_manifest = copy.deepcopy(self.manifest)
        repeated_manifest["minimum_runs_per_case"] = 2
        one_run_records = [
            {
                "case_id": case["case_id"],
                "parsed_verdict": case["expected"],
                "target_mutated": False,
            }
            for case in repeated_manifest["cases"]
        ]
        insufficient_report = self.scorer.score(repeated_manifest, one_run_records)

        self.assertFalse(duplicate_report["release_pass"])
        self.assertFalse(insufficient_report["release_pass"])
        self.assertTrue(insufficient_report["under_run_cases"])


    def test_report_cli_accepts_exact_reviewed_cohort_without_changing_label_score(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cohort_path, manifest_path, manifest, records, reviews = self.report_inputs(root)
            exit_code, report = self.run_report_cli(root, cohort_path, manifest_path, records, reviews, "accepted")

        self.assertEqual(exit_code, 0)
        self.assertTrue(report["candidate_accepted"])
        self.assertEqual(report["label_score"], self.scorer.score(manifest, records))
        self.assertEqual(report["causal_review"], {
            "coverage": {
                "expected_runs": [{"case_id": "report-normal", "run_id": "run-a"}],
                "result_runs": [{"case_id": "report-normal", "run_id": "run-a"}],
                "review_runs": [{"case_id": "report-normal", "run_id": "run-a"}],
            },
            "errors": [],
        })

    def test_report_rejects_provider_failure_even_with_passing_score_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cohort_path, manifest_path, _, records, reviews = self.report_inputs(root)
            events_path = Path(reviews[0]["evidence_refs"][0]["path"])
            events = [json.loads(line) for line in events_path.read_text().splitlines()]
            events[0]["message"]["stopReason"] = "error"
            events[0]["message"]["errorMessage"] = "provider unavailable"
            events_path.write_text("".join(json.dumps(event) + "\n" for event in events))
            reviews[0]["evidence_refs"][0]["sha256"] = hashlib.sha256(events_path.read_bytes()).hexdigest()
            exit_code, report = self.run_report_cli(root, cohort_path, manifest_path, records, reviews, "provider-error")

        self.assertEqual(exit_code, 1)
        self.assertTrue(report["label_score"]["release_pass"])
        self.assertFalse(report["candidate_accepted"])
        self.assertIn("model_not_cleanly_terminated", {error["code"] for error in report["causal_review"]["errors"]})

    def test_report_cli_rejects_incomplete_or_untrusted_causal_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cohort_path, manifest_path, _, records, reviews = self.report_inputs(root)
            foreign_events = root / "foreign-run" / "verify" / "events.jsonl"
            foreign_events.parent.mkdir(parents=True)
            foreign_events.write_text('{"type":"foreign"}\n', encoding="utf-8")
            external_result = {"case_id": "outside-cohort", "run_id": "foreign", "parsed_verdict": "FAILED", "target_mutated": False}
            external_review = copy.deepcopy(reviews[0])
            external_review.update(case_id="outside-cohort", run_id="foreign")
            false_review = copy.deepcopy(reviews[0])
            false_review["causal_evidence_sufficient"] = False
            missing_evidence_review = copy.deepcopy(reviews[0])
            missing_evidence_review["evidence_refs"] = [{"path": str(root / "missing" / "verify" / "events.jsonl"), "sha256": "0" * 64}]
            mismatched_hash_review = copy.deepcopy(reviews[0])
            mismatched_hash_review["evidence_refs"][0]["sha256"] = "0" * 64
            foreign_events_review = copy.deepcopy(reviews[0])
            foreign_events_review["evidence_refs"] = [{
                "path": str(foreign_events), "sha256": hashlib.sha256(foreign_events.read_bytes()).hexdigest(),
            }]
            variants = [
                ("missing-result", [], reviews, "missing_result"),
                ("duplicate-result", [*records, copy.deepcopy(records[0])], reviews, "duplicate_result"),
                ("external-result", [*records, external_result], reviews, "external_result"),
                ("missing-review", records, [], "missing_review"),
                ("duplicate-review", records, [*reviews, copy.deepcopy(reviews[0])], "duplicate_review"),
                ("external-review", records, [external_review], "external_review"),
                ("false-causal-review", records, [false_review], "insufficient_causal_evidence"),
                ("missing-evidence", records, [missing_evidence_review], "missing_evidence_ref"),
                ("mismatched-hash", records, [mismatched_hash_review], "evidence_hash_mismatch"),
                ("foreign-verify-events", records, [foreign_events_review], "foreign_verify_events_ref"),
            ]
            for name, candidate_records, candidate_reviews, expected_error in variants:
                with self.subTest(name=name):
                    exit_code, report = self.run_report_cli(
                        root, cohort_path, manifest_path, candidate_records, candidate_reviews, name,
                    )
                    error_codes = {error["code"] for error in report["causal_review"]["errors"]}
                    self.assertEqual(exit_code, 1)
                    self.assertFalse(report["candidate_accepted"])
                    self.assertIn(expected_error, error_codes)
            Path(reviews[0]["evidence_refs"][0]["path"]).unlink()
            with self.subTest(name="missing-required-verify-events"):
                exit_code, report = self.run_report_cli(
                    root, cohort_path, manifest_path, records, reviews, "missing-required-verify-events",
                )
                error_codes = {error["code"] for error in report["causal_review"]["errors"]}
                self.assertEqual(exit_code, 1)
                self.assertFalse(report["candidate_accepted"])
                self.assertIn("missing_verify_events", error_codes)
            empty_cohort_path, empty_manifest_path = root / "empty-cohort.json", root / "empty-manifest.json"
            self.write_json(empty_cohort_path, [])
            self.write_json(empty_manifest_path, self.manifest_with([]))
            with self.subTest(name="empty-cohort"):
                exit_code, report = self.run_report_cli(
                    root, empty_cohort_path, empty_manifest_path, [], [], "empty-cohort",
                )
                error_codes = {error["code"] for error in report["causal_review"]["errors"]}
                self.assertEqual(exit_code, 1)
                self.assertFalse(report["candidate_accepted"])
                self.assertIn("empty_cohort", error_codes)


if __name__ == "__main__":
    unittest.main()
