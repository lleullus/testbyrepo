from __future__ import annotations

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

    def test_manifest_has_unique_core_and_holdout_cases_without_extra_verdict_classes(self) -> None:
        self.assertEqual(self.manifest["schema"], "iis-ready-verification-calibration/v1")
        cases = self.manifest["cases"]
        ids = [case["case_id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(cases), 20)
        allowed = {"VERIFIED", "FAILED", "INCONCLUSIVE", "VERIFICATION NOT STARTED"}
        self.assertTrue(all(case["expected"] in allowed for case in cases))
        self.assertTrue(all(case["expected"] == "VERIFIED" for case in cases if case["normal_twin"]))
        self.assertEqual(self.manifest["release_gate"]["malformed_terminal"], 0)
        self.assertEqual(self.manifest["release_gate"]["target_mutation_runs"], 0)

        by_family: dict[str, list[dict[str, object]]] = {}
        for case in cases:
            by_family.setdefault(str(case["family"]), []).append(case)
        for family, family_cases in by_family.items():
            with self.subTest(family=family):
                self.assertTrue(any("holdout" in str(case["variant"]) for case in family_cases))
                self.assertTrue(any("holdout" not in str(case["variant"]) for case in family_cases))

    def test_scorer_reports_baseline_target_mutation_as_false_verified_and_incomplete(self) -> None:
        records = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        report = self.scorer.score(self.manifest, records)
        self.assertFalse(report["release_pass"])
        self.assertEqual(report["false_verified"], 1)
        self.assertEqual(report["target_mutation_runs"], 1)
        self.assertGreater(len(report["missing_cases"]), 0)

    def test_complete_expected_result_set_passes_release_gate(self) -> None:
        records = [
            {
                "case_id": case["case_id"],
                "parsed_verdict": case["expected"],
                "target_mutated": False,
            }
            for case in self.manifest["cases"]
        ]
        report = self.scorer.score(self.manifest, records)
        self.assertTrue(report["release_pass"])
        self.assertEqual(report["false_verified"], 0)
        self.assertEqual(report["normal_false_rejection"], 0)
        self.assertEqual(report["malformed_terminal"], 0)
        self.assertEqual(report["target_mutation_runs"], 0)
        self.assertEqual(report["missing_cases"], [])

    def test_release_gate_rejects_target_mutation_even_when_verdicts_match(self) -> None:
        records = [
            {
                "case_id": case["case_id"],
                "parsed_verdict": case["expected"],
                "target_mutated": index == 0,
            }
            for index, case in enumerate(self.manifest["cases"])
        ]
        report = self.scorer.score(self.manifest, records)
        self.assertEqual(report["false_verified"], 0)
        self.assertEqual(report["target_mutation_runs"], 1)
        self.assertFalse(report["release_pass"])

    def test_release_gate_rejects_malformed_terminal_without_false_verified(self) -> None:
        defect_index = next(
            index for index, case in enumerate(self.manifest["cases"])
            if not case["normal_twin"]
        )
        records = [
            {
                "case_id": case["case_id"],
                "parsed_verdict": "unexpected terminal" if index == defect_index else case["expected"],
                "target_mutated": False,
            }
            for index, case in enumerate(self.manifest["cases"])
        ]
        report = self.scorer.score(self.manifest, records)
        self.assertEqual(report["false_verified"], 0)
        self.assertEqual(report["malformed_terminal"], 1)
        self.assertFalse(report["release_pass"])

    def test_scorer_counts_false_verified_without_using_record_supplied_oracle(self) -> None:
        defect = next(case for case in self.manifest["cases"] if case["expected"] == "FAILED")
        records = [
            {
                "case_id": defect["case_id"],
                "parsed_verdict": "VERIFIED",
                "expected": "VERIFIED",
                "target_mutated": False,
            }
        ]
        report = self.scorer.score(self.manifest, records)
        self.assertEqual(report["false_verified"], 1)
        self.assertFalse(report["release_pass"])


if __name__ == "__main__":
    unittest.main()
