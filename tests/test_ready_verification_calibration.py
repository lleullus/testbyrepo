from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evaluation" / "ready-verification"
MANIFEST_PATH = EVAL / "manifest.json"
BASELINE_PATH = EVAL / "baseline-observations.json"
SCORER_PATH = EVAL / "score_result.py"


def load_scorer():
    spec = importlib.util.spec_from_file_location("ready_verification_score_result", SCORER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Ready verification scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



class ReadyVerificationCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.scorer = load_scorer()

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




if __name__ == "__main__":
    unittest.main()
