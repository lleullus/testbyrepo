from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from iis_artifacts.admission import AdmissionError, admit_scope
from iis_artifacts.store import ArtifactStore

SPEC = importlib.util.spec_from_file_location("thesis_lifecycle_test", ROOT / "product-thesis/tools/lifecycle.py")
assert SPEC is not None and SPEC.loader is not None
lifecycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lifecycle)


class ThesisLifecycleRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="thesis-lifecycle-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.store = ArtifactStore(self.root / "store", "project")
        self.logical = "docs/planning/product-thesis/demo/THESIS-001.md"
        self.candidate = self.project / self.logical
        self.candidate.parent.mkdir(parents=True)
        self.candidate.write_text(
            "# Product Thesis\n\n## Core Utility\nReturn the attributable result.\n",
            encoding="utf-8",
        )

    def start(self) -> str:
        return lifecycle.start(self.store, "Define the attributable result.")

    def add_resolved_frontier(self, run_id: str) -> None:
        lifecycle.add_frontier(
            self.store,
            run_id,
            item_id="truth",
            origin="current request",
            question="What makes the result attributable?",
            material_change="A different answer changes product success.",
            decision_bearing=True,
        )
        lifecycle.disposition_frontier(
            self.store,
            run_id,
            "truth",
            "RESOLVED",
            "The current request requires the returned result to remain attributable to the triggering identity.",
        )

    def run_source_review(self, run_id: str) -> None:
        inv = lifecycle.begin_review(self.store, run_id, "SOURCE_FRONTIER", [])
        lifecycle.complete_review(self.store, inv, result={"actual_host_delivery": True})

    def submit_and_challenge(self, run_id: str, generation: int) -> dict:
        candidate = lifecycle.submit_candidate(
            self.store,
            run_id,
            self.candidate,
            self.logical,
            expected_generation=generation,
        )
        inv = lifecycle.begin_review(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE", [candidate])
        lifecycle.complete_review(self.store, inv, result={"actual_host_delivery": True}, findings=[])
        return candidate

    def make_ready_scope(self, thesis_ref: dict) -> Path:
        scope = self.project / "docs/planning/work/demo/SCOPE.md"
        scope.parent.mkdir(parents=True, exist_ok=True)
        scope.write_text(
            "# Demo\n"
            "Schema: iis-scope/v2\n"
            f"Project-Root: {self.project}\n"
            "Status: ready\n\n"
            "## Product Authority\n"
            "```iis-sources\n"
            + json.dumps([thesis_ref], indent=2)
            + "\n```\n\n"
            "## Outcome\nReturn the attributable result.\n\n"
            "## Acceptance\nThe triggering identity reads back its own result.\n\n"
            "## Open Decisions\nNone\n",
            encoding="utf-8",
        )
        return scope

    def test_model_claim_alone_cannot_close(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        lifecycle.submit_candidate(self.store, run_id, self.candidate, self.logical, expected_generation=0)
        verdict = lifecycle.evaluate_closure(self.store, run_id)
        reasons = {item["reason"] for item in verdict["tasks"]}
        self.assertEqual(verdict["result"], "REWORK_REQUIRED")
        self.assertIn("SOURCE_FRONTIER_REVIEW_REQUIRED", reasons)
        self.assertIn("CURRENT_CANDIDATE_CHALLENGE_REQUIRED", reasons)

    def test_candidate_change_invalidates_candidate_specific_challenge(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        first = self.submit_and_challenge(run_id, 0)
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "ELIGIBLE")

        self.candidate.write_text(
            "# Product Thesis\n\n## Core Utility\nReturn and preserve the attributable result.\n",
            encoding="utf-8",
        )
        second = lifecycle.submit_candidate(self.store, run_id, self.candidate, self.logical, expected_generation=1)
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        verdict = lifecycle.evaluate_closure(self.store, run_id)
        self.assertEqual(verdict["result"], "REWORK_REQUIRED")
        self.assertIn("CURRENT_CANDIDATE_CHALLENGE_REQUIRED", {item["reason"] for item in verdict["tasks"]})

    def test_material_finding_blocks_until_dispositioned(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        candidate = lifecycle.submit_candidate(self.store, run_id, self.candidate, self.logical, expected_generation=0)
        inv = lifecycle.begin_review(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE", [candidate])
        lifecycle.complete_review(
            self.store,
            inv,
            result={"actual_host_delivery": True},
            findings=[{
                "finding_id": "cx-1",
                "anchor": "Core Utility",
                "scenario": "A different identity can read the result.",
                "apparent_success": "A result exists.",
                "broken_result": "Attribution is false.",
                "materiality": "MATERIAL",
                "disposition": "OPEN",
            }],
        )
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "REWORK_REQUIRED")
        lifecycle.disposition_finding(
            self.store,
            run_id,
            "cx-1",
            "DISMISSED",
            "The adopted identity rule directly forbids the proposed cross-identity read.",
        )
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "ELIGIBLE")

    def test_common_admission_requires_closed_thesis(self) -> None:
        snapshot = self.store.capture_files(self.project, [self.candidate], kind="candidate")
        unclosed = {"snapshot": snapshot, "path": self.logical}
        scope = self.make_ready_scope(unclosed)
        with self.assertRaisesRegex(AdmissionError, "THESIS_CLOSURE_REQUIRED"):
            admit_scope(self.store, scope, role="scope-plan")

    def test_closed_thesis_admits_ready_scope(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        candidate = self.submit_and_challenge(run_id, 0)
        closure = lifecycle.close_request(self.store, run_id, self.project)
        self.assertEqual(closure["result"], "CALIBRATED")
        scope = self.make_ready_scope(candidate)
        admission = admit_scope(self.store, scope, role="scope-plan")
        self.assertEqual(admission["status"], "ELIGIBLE")
        self.assertEqual(admission["product_authorities"], [candidate])


if __name__ == "__main__":
    unittest.main()
