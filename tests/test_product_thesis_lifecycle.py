from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

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
        self.candidate.write_text("# Product Thesis\n\n## Core Utility\nReturn the attributable result.\n", encoding="utf-8")

    def start(self, *, budget: int | None = None) -> str:
        return lifecycle.start(self.store, "Define the attributable result.", budget=budget)

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
        inputs = lifecycle.required_review_inputs(self.store, run_id, "SOURCE_FRONTIER")
        inv = lifecycle.begin_review(self.store, run_id, "SOURCE_FRONTIER", inputs)
        lifecycle.complete_review(self.store, inv, result={"host_terminal": True, "review": "source"})

    def submit_candidate(self, run_id: str, generation: int) -> dict:
        return lifecycle.submit_candidate(
            self.store,
            run_id,
            self.candidate,
            self.logical,
            expected_generation=generation,
        )

    def run_candidate_review(self, run_id: str, *, findings: list[dict] | None = None) -> list[str]:
        inputs = lifecycle.required_review_inputs(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE")
        inv = lifecycle.begin_review(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE", inputs)
        return lifecycle.complete_review(
            self.store,
            inv,
            result={"host_terminal": True, "review": "candidate"},
            findings=findings or [],
        )

    def ready_to_close(self, *, budget: int | None = None) -> tuple[str, dict]:
        run_id = self.start(budget=budget)
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        candidate = self.submit_candidate(run_id, 0)
        self.run_candidate_review(run_id)
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "ELIGIBLE")
        return run_id, candidate

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

    def test_candidate_path_is_restricted_to_canonical_product_thesis_revision(self) -> None:
        run_id = self.start()
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "INVALID_THESIS_CANDIDATE_PATH"):
            lifecycle.submit_candidate_bytes(
                self.store,
                run_id,
                b"forged\n",
                "README.md",
                expected_generation=0,
            )

    def test_review_must_receive_host_fixed_required_inputs(self) -> None:
        run_id = self.start()
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "REVIEW_INPUT_MISMATCH"):
            lifecycle.begin_review(self.store, run_id, "SOURCE_FRONTIER", [])
        self.run_source_review(run_id)
        self.submit_candidate(run_id, 0)
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "REVIEW_INPUT_MISMATCH"):
            lifecycle.begin_review(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE", [])

    def test_empty_review_result_cannot_complete(self) -> None:
        run_id = self.start()
        inputs = lifecycle.required_review_inputs(self.store, run_id, "SOURCE_FRONTIER")
        inv = lifecycle.begin_review(self.store, run_id, "SOURCE_FRONTIER", inputs)
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "nonempty"):
            lifecycle.complete_review(self.store, inv, result={})
        self.assertIn("REVIEW_RESULT_PENDING", {item["reason"] for item in lifecycle.evaluate_closure(self.store, run_id)["tasks"]})

    def test_started_review_blocks_closure_until_result_is_recovered(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        inputs = lifecycle.required_review_inputs(self.store, run_id, "SOURCE_FRONTIER")
        lifecycle.begin_review(self.store, run_id, "SOURCE_FRONTIER", inputs)
        verdict = lifecycle.evaluate_closure(self.store, run_id)
        self.assertIn("REVIEW_RESULT_PENDING", {item["reason"] for item in verdict["tasks"]})

    def test_candidate_change_invalidates_candidate_specific_challenge(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        first = self.submit_candidate(run_id, 0)
        self.run_candidate_review(run_id)
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "ELIGIBLE")
        self.candidate.write_text("# Product Thesis\n\n## Core Utility\nReturn and preserve the attributable result.\n", encoding="utf-8")
        second = self.submit_candidate(run_id, 1)
        self.assertNotEqual(first["snapshot"], second["snapshot"])
        verdict = lifecycle.evaluate_closure(self.store, run_id)
        self.assertIn("CURRENT_CANDIDATE_CHALLENGE_REQUIRED", {item["reason"] for item in verdict["tasks"]})

    def test_same_reported_finding_id_never_overwrites_prior_finding(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        self.submit_candidate(run_id, 0)
        finding = {
            "finding_id": "cx-1",
            "anchor": "Core Utility",
            "scenario": "A different identity can read the result.",
            "apparent_success": "A result exists.",
            "broken_result": "Attribution is false.",
            "materiality": "MATERIAL",
        }
        first_keys = self.run_candidate_review(run_id, findings=[finding])
        second = {**finding, "scenario": "A second concrete cross-identity path exists."}
        second_keys = self.run_candidate_review(run_id, findings=[second])
        self.assertNotEqual(first_keys[0], second_keys[0])
        state = lifecycle.inspect(self.store, run_id)
        self.assertEqual(len([item for item in state["findings"] if item["reported_id"] == "cx-1"]), 2)
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "ambiguous"):
            lifecycle.disposition_finding(self.store, run_id, "cx-1", "DISMISSED", "ambiguous must fail")
        lifecycle.disposition_finding(self.store, run_id, first_keys[0], "DISMISSED", "first path excluded by authority")
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "REWORK_REQUIRED")

    def test_cancelled_run_cannot_close_and_late_result_is_only_preserved(self) -> None:
        run_id = self.start()
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        self.submit_candidate(run_id, 0)
        inputs = lifecycle.required_review_inputs(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE")
        inv = lifecycle.begin_review(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE", inputs)
        lifecycle.cancel(self.store, run_id)
        self.assertEqual(lifecycle.close_request(self.store, run_id, self.project)["result"], "CANCELLED")
        lifecycle.complete_review(self.store, inv, result={"host_terminal": True, "late": True})
        review = next(item for item in lifecycle.inspect(self.store, run_id)["reviews"] if item["invocation_id"] == inv)
        self.assertEqual(review["status"], "LATE")
        self.assertEqual(lifecycle.evaluate_closure(self.store, run_id)["result"], "CANCELLED")

    def test_resume_invalidates_prior_request_reviews_and_candidate(self) -> None:
        run_id, _candidate = self.ready_to_close()
        lifecycle.add_frontier(
            self.store,
            run_id,
            item_id="choice",
            origin="current request",
            question="Which visible identity?",
            material_change="Different answer changes result ownership.",
            decision_bearing=True,
        )
        lifecycle.disposition_frontier(self.store, run_id, "choice", "USER_CHOICE", "User owns the choice.")
        self.assertEqual(lifecycle.close_request(self.store, run_id, self.project)["result"], "WAITING_USER")
        lifecycle.resume(self.store, run_id, "Use the account identity.")
        state = lifecycle.inspect(self.store, run_id)
        self.assertEqual(state["request_generation"], 1)
        self.assertIsNone(state["candidate"])
        reasons = {item["reason"] for item in lifecycle.evaluate_closure(self.store, run_id)["tasks"]}
        self.assertIn("SOURCE_FRONTIER_REVIEW_REQUIRED", reasons)
        self.assertIn("CURRENT_CANDIDATE_CHALLENGE_REQUIRED", reasons)

    def test_budget_is_enforced_at_review_start(self) -> None:
        run_id = self.start(budget=1)
        self.add_resolved_frontier(run_id)
        self.run_source_review(run_id)
        self.submit_candidate(run_id, 0)
        inputs = lifecycle.required_review_inputs(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE")
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "BUDGET_EXHAUSTED"):
            lifecycle.begin_review(self.store, run_id, "CANDIDATE_COUNTEREXAMPLE", inputs)
        self.assertEqual(lifecycle.inspect(self.store, run_id)["phase"], "BUDGET_EXHAUSTED")

    def test_close_rechecks_expected_generation(self) -> None:
        run_id, _candidate = self.ready_to_close()
        with self.assertRaisesRegex(lifecycle.ThesisLifecycleError, "GENERATION_CONFLICT"):
            lifecycle.close_request(self.store, run_id, self.project, expected_generation=999)

    def test_closing_run_recovers_pending_publication_after_replace_failure(self) -> None:
        run_id, _candidate = self.ready_to_close()
        real_publish = lifecycle.publish_ref

        def fail_after_replace(store, source_ref, project_root, logical_path, *, expected_prior):
            return real_publish(
                store,
                source_ref,
                project_root,
                logical_path,
                expected_prior=expected_prior,
                fault_after_replace=True,
            )

        with mock.patch.object(lifecycle, "publish_ref", side_effect=fail_after_replace):
            with self.assertRaisesRegex(OSError, "injected publication failure"):
                lifecycle.close_request(
                    self.store,
                    run_id,
                    self.project,
                    expected_generation=1,
                )
        self.assertEqual(lifecycle.inspect(self.store, run_id)["phase"], "CLOSING")
        recovered = lifecycle.close_request(
            self.store,
            run_id,
            self.project,
            expected_generation=1,
        )
        self.assertEqual(recovered["result"], "CALIBRATED")
        self.assertEqual(lifecycle.inspect(self.store, run_id)["phase"], "CLOSED")

    def test_common_admission_requires_closed_thesis(self) -> None:
        snapshot = self.store.capture_files(self.project, [self.candidate], kind="candidate")
        unclosed = {"snapshot": snapshot, "path": self.logical}
        scope = self.make_ready_scope(unclosed)
        with self.assertRaisesRegex(AdmissionError, "THESIS_CLOSURE_REQUIRED"):
            admit_scope(self.store, scope, role="scope-plan", current_request="Plan the demo.")

    def test_closed_thesis_admits_exact_fixed_scope(self) -> None:
        run_id, candidate = self.ready_to_close()
        closure = lifecycle.close_request(self.store, run_id, self.project, expected_generation=1)
        self.assertEqual(closure["result"], "CALIBRATED")
        scope = self.make_ready_scope(candidate)
        admission = admit_scope(self.store, scope, role="scope-plan", current_request="Plan the demo.")
        self.assertEqual(admission["schema"], "iis-admission/v2")
        self.assertEqual(admission["status"], "ELIGIBLE")
        fixed_scope = admission["scope"]
        scope.write_text(scope.read_text(encoding="utf-8").replace("Return the attributable result.", "MUTATED LIVE SCOPE."), encoding="utf-8")
        self.assertNotIn(b"MUTATED LIVE SCOPE", self.store.read_bytes(fixed_scope))


if __name__ == "__main__":
    unittest.main()
