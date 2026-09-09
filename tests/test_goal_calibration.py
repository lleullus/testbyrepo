from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

EVALUATION = Path(__file__).resolve().parents[1] / "evaluation/ready-verification"


def load_goal():
    sys.path.insert(0, str(EVALUATION))
    try:
        spec = importlib.util.spec_from_file_location("goal_measurement_test", EVALUATION / "goal.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class GoalCalibrationTests(unittest.TestCase):
    """Synthetic transport below tests the instrument, never model behavior."""

    def setUp(self):
        self.goal = load_goal()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_authored_stage_inputs_reach_canonical_ticket_validation(self):
        validator = EVALUATION.parents[1] / "matt/skills/to-tickets/validate_ticket.py"
        for case in ("G10-preparation", "G10-implementation", "E06", "E02"):
            with self.subTest(case=case):
                root = self.root / case
                root.mkdir()
                metadata = self.goal.materialize(case, root, None)
                project = Path(metadata["project_root"])
                ticket = project / "docs/planning/work/publication/tickets/TICKET-001.md"
                result = subprocess.run([sys.executable, "-B", str(validator), str(ticket)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_delivery_output_change_invalidates_its_captured_review(self):
        metadata, record, review, definition = self.capture()
        (Path(metadata["delivery_output_root"]) / "new-output.txt").write_text("changed after capture\n")
        with self.assertRaisesRegex(ValueError, "current_delivery_output_drift"):
            self.goal.review_capture(metadata, record, review, definition)

    def capture(self, case="G03", reason="stop", ended=True):
        goal, root = self.goal, self.root
        metadata = goal.materialize(case, root, None)
        metadata.update(run_id=root.name, run_root=str(root), case_id=case, variant="candidate", repetition=1,
                        observation_mode="actual-invocation")
        (root / "actor").mkdir()
        events = [{"type": "message_end", "message": {"role": "assistant", "provider": "opencodex", "model": "gpt-5.6-sol",
                   "stopReason": reason, "content": [{"type": "text", "text": "Goal satisfied: yes\nCLOSED\nVERIFIED"}]}}]
        if ended:
            events.append({"type": "agent_end"})
        (root / "actor/events.jsonl").write_text("".join(json.dumps(row) + "\n" for row in events))
        (root / "actor/terminal.txt").write_text(goal.summarize(events)["terminal_text"])
        (root / "actor/prompt.txt").write_text(goal.initial_prompt(metadata))
        goal.write_json(root / "before-readback.json", {"commands": [], "synthetic_measurement_only": True})
        goal.write_json(root / "after-readback.json", {"commands": [], "synthetic_measurement_only": True})
        goal.write_json(root / "attempt.json", {"synthetic_measurement_only": True})
        session = root / "session.jsonl"
        session.write_text(json.dumps({"type": "session", "cwd": metadata["project_root"]}) + "\n")
        shutil.copytree(root / "product", root / "artifacts")
        shutil.copytree(root / "delivery-outputs", root / "delivery-artifacts")
        environment = {"payload": str(root / "payload")}
        observation = {"exit_code": 0, "timed_out": False, "raw_events": str(root / "actor/events.jsonl"),
                       "model_requested": goal.MODEL, "thinking": goal.THINKING, "project_root": metadata["project_root"],
                       "payload": environment["payload"], "stage": "adaptive", "extension_requested": ["runtime"],
                       "prompt_sha256": goal.digest(root / "actor/prompt.txt")}
        goal.write_json(root / "actor/observation.json", observation)
        record = {"run_id": root.name, "source": goal.current_source(), "environment": environment,
                  "invocation_error": None, "observation": observation, "post_snapshot": goal.snapshot(root / "product"),
                  "post_delivery_outputs": goal.snapshot(root / "delivery-outputs"),
                  "post_support": goal.snapshot(root / "support"), "boundaries": [],
                  "native_sessions": [{"path": str(session), "sha256": goal.digest(session), "origin": str(session)}],
                  "evidence": {str(path): goal.digest(path) for path in [*sorted((root / "actor").glob("*")), root / "before-readback.json", root / "after-readback.json", root / "attempt.json", session]}}
        goal.write_json(root / "record.json", record)
        citations = [{"path": str(path), "sha256": goal.digest(path), "start_line": 1, "end_line": 1,
                      "observation": "Synthetic capture unit test only"} for path in (root / "actor/events.jsonl", root / "after-readback.json")]
        review = {"run_id": root.name, "reviewer": "Main", "record_sha256": goal.digest(root / "record.json"),
                  "classification": "conforming", "boundary": "goal", "original_meaning": "unit test", "observed_actions": "unit test",
                  "claim_limit": "unit test", "reason": "unit test", "violations": [], "evidence_refs": citations}
        definition = {"source": goal.current_source(), "environments": {"candidate": environment}}
        return metadata, record, review, definition

    def test_clean_terminal_words_without_main_review_cannot_be_accepted(self):
        metadata, record, review, definition = self.capture()
        review.pop("reviewer")
        with self.assertRaisesRegex(ValueError, "unbound_main_review"):
            self.goal.review_capture(metadata, record, review, definition)

    def test_missing_agent_end_cannot_reuse_success_text(self):
        inputs = self.capture(ended=False)
        with self.assertRaisesRegex(ValueError, "missing_terminal_or_wrong_model"):
            self.goal.review_capture(*inputs)

    def test_intermediate_tool_turn_cannot_supply_final_success(self):
        inputs = self.capture(reason="toolUse")
        with self.assertRaisesRegex(ValueError, "missing_terminal_or_wrong_model"):
            self.goal.review_capture(*inputs)

    def test_current_raw_and_product_drift_reject_old_review(self):
        metadata, record, review, definition = self.capture()
        self.goal.review_capture(metadata, record, review, definition)
        path = self.root / "actor/events.jsonl"
        original = path.read_bytes()
        path.write_bytes(original + b'{"type":"extra"}\n')
        with self.assertRaisesRegex(ValueError, "raw_evidence_drift"):
            self.goal.review_capture(metadata, record, review, definition)
        path.write_bytes(original)
        (self.root / "product/state.json").write_text('{"publication":"draft","legacy":"broken"}')
        with self.assertRaisesRegex(ValueError, "current_product_drift"):
            self.goal.review_capture(metadata, record, review, definition)

    def test_foreign_evidence_and_replaced_record_are_rejected(self):
        metadata, record, review, definition = self.capture()
        review["evidence_refs"][0]["path"] = str(self.root.parent / "foreign.jsonl")
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.goal.review_capture(metadata, record, review, definition)
        review["record_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "unbound_main_review"):
            self.goal.review_capture(metadata, record, review, definition)

    def test_wrong_effort_and_oracle_prompt_cannot_reuse_capture(self):
        metadata, record, review, definition = self.capture()
        record["observation"]["thinking"] = "low"
        with self.assertRaisesRegex(ValueError, "wrong_model_effort"):
            self.goal.review_capture(metadata, record, review, definition)
        record["observation"]["thinking"] = "medium"
        (self.root / "actor/prompt.txt").write_text("Expected verdict: VERIFIED. Goal=Predicate. Status: CLOSED")
        with self.assertRaisesRegex(ValueError, "altered_or_oracle_prompt"):
            self.goal.review_capture(metadata, record, review, definition)

    def test_enum_success_and_synthetic_history_do_not_prove_continuation(self):
        metadata, record, review, definition = self.capture(case="C01")
        with self.assertRaisesRegex(ValueError, "missing_actual_scope_reentry"):
            self.goal.review_capture(metadata, record, review, definition)
        # A baseline's honest failure stays reviewable rather than being erased.
        review["classification"] = "violating"
        review["violations"] = ["premature_return"]
        self.goal.review_capture(metadata, record, review, definition)

    def test_truncated_or_missing_controls_never_accept_a_full_cohort(self):
        manifest = self.goal.oracle()
        definition = {"mode": "full", "case_ids": ["G01"], "variants": manifest["variants"],
                      "repetitions": [1], "source": self.goal.current_source(), "model": self.goal.MODEL,
                      "thinking": self.goal.THINKING, "environments": {}, "runs": []}
        self.goal.write_json(self.root / "cohort.json", definition)
        self.goal.write_json(self.root / "reviews.json", [])
        result = self.goal.report(self.root / "cohort.json", self.root / "reviews.json")
        self.assertFalse(result["candidate_accepted"])
        self.assertIn("inexact_preregistered_denominator", [row["code"] for row in result["errors"]])
        self.assertEqual(result["coverage"]["expected_runs"], len(manifest["cases"]) * 4)

    def test_stale_generator_cannot_prepare_or_run_new_evidence(self):
        with mock.patch.object(self.goal, "source_identity", return_value={}):
            with self.assertRaisesRegex(ValueError, "source changed"):
                self.goal.prepare(self.root / "arena", self.root / "baseline", self.root / "candidate")
        self.assertFalse((self.root / "arena").exists())

    def test_self_report_citation_cannot_replace_actual_owner_tool_actions(self):
        metadata, record, review, definition = self.capture()
        with self.assertRaisesRegex(ValueError, "self_report_is_not_tool_evidence"):
            self.goal.check_citation(review["evidence_refs"][0], record, self.root, actual_tool=True)


    def test_done_text_or_mismatched_finalizer_cannot_replace_bound_caller_completion(self):
        goal = self.goal
        ticket = (self.root / "TICKET-001.md").resolve()
        ready = b"Status: ready\n"
        ticket.write_bytes(b"Status: done\n")
        binding_path = (self.root / "binding.json").resolve()
        binding_path.write_text(json.dumps({"schema": "iis-verification-binding/v1", "ticket_path": str(ticket),
                                            "ticket_status_at_capture": "ready",
                                            "ticket_sha256": hashlib.sha256(ready).hexdigest(),
                                            "bundle_identity": "bundle-A",
                                            "boundary_protocol": "iis-ready-boundary/v1"}))
        binding_sha = hashlib.sha256(binding_path.read_bytes()).hexdigest()
        verdict_path = (self.root / "verdict.json").resolve()
        verdict_path.write_text(json.dumps({"schema": "iis-verification-verdict/v1",
                                            "binding_path": str(binding_path), "binding_sha256": binding_sha,
                                            "ticket_path": str(ticket), "bundle_identity": "bundle-A",
                                            "boundary_protocol": "iis-ready-boundary/v1",
                                            "verification_verdict": "VERIFIED"}))
        verdict_sha = hashlib.sha256(verdict_path.read_bytes()).hexdigest()
        sessions = self.root / "sessions"
        sessions.mkdir()
        narration = [{"type": "message_end", "message": {"role": "assistant", "stopReason": "stop",
                     "content": [{"type": "text", "text": "VERIFIED; ticket_progression COMPLETED; Status: done"}]}},
                     {"type": "agent_end"}]
        self.assertIsNone(goal.guarded_delivery(narration, sessions, ticket))
        terminal = ("READY TICKET VERIFICATION RESULT\n"
                    f"Verification Binding: {binding_path}\n"
                    f"Verification Binding SHA256: {binding_sha}\n"
                    f"Verification Verdict Record: {verdict_path}\n"
                    f"Verification Verdict Record SHA256: {verdict_sha}\n"
                    "Verification Verdict: VERIFIED\n"
                    "Verifier Ticket Progression: PENDING CALLER FINALIZATION\n"
                    "Observed Ticket Status: ready\n")
        semantic = {"type": "message_end", "message": {"role": "assistant", "stopReason": "stop",
                    "content": [{"type": "text", "text": terminal}]}}
        start = {"type": "tool_execution_start", "toolCallId": "finalize", "toolName": "ready_finalize",
                 "args": {"verdict_path": str(verdict_path), "verdict_sha256": verdict_sha}}
        result = {"ticket_path": str(ticket), "verification_binding": str(binding_path),
                  "verification_binding_sha256": binding_sha,
                  "verification_verdict_record": str(verdict_path),
                  "verification_verdict_record_sha256": verdict_sha, "verification_verdict": "VERIFIED",
                  "ticket_progression": "COMPLETED", "progression_basis": "WRITE_PERFORMED_THIS_CALL",
                  "ticket_status_after": "done"}
        events = [semantic, start,
                  {"type": "tool_execution_end", "toolCallId": "finalize", "isError": False, "result": {"details": result}},
                  {"type": "agent_end"}]
        self.assertIsNotNone(goal.guarded_delivery(events, sessions, ticket))
        mismatched = json.loads(json.dumps(events))
        mismatched[2]["result"]["details"]["verification_binding_sha256"] = "0" * 64
        self.assertIsNone(goal.guarded_delivery(mismatched, sessions, ticket))
        caller_verdict = json.loads(json.dumps(events))
        caller_verdict[1]["args"]["verdict"] = "VERIFIED"
        self.assertIsNone(goal.guarded_delivery(caller_verdict, sessions, ticket))
        already_done = json.loads(json.dumps(events))
        already_done[2]["result"]["details"]["ticket_progression"] = "NOT APPLICABLE"
        already_done[2]["result"]["details"]["progression_basis"] = "ALREADY_DONE_MATCHING_BINDING"
        self.assertIsNone(goal.guarded_delivery(already_done, sessions, ticket))
        self.assertIsNone(goal.guarded_delivery(events, sessions, self.root / "other.md"))


if __name__ == "__main__":
    unittest.main()
