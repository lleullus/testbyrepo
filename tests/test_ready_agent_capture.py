from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


EVALUATION = Path(__file__).resolve().parents[1] / "evaluation/ready-verification"


def load_module(name: str):
    sys.path.insert(0, str(EVALUATION))
    try:
        spec = importlib.util.spec_from_file_location(f"capture_test_{name}", EVALUATION / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def message(reason: str, text: str, **extra) -> dict:
    return {"type": "message_end", "message": {
        "role": "assistant", "stopReason": reason,
        "provider": "opencodex", "model": "gpt-6-astra",
        "content": [{"type": "text", "text": text}], **extra,
    }}


class ReadyAgentCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = load_module("run_agent")

    def test_provider_failure_cannot_supply_a_verdict(self) -> None:
        for reason in ("error", "aborted", "length"):
            with self.subTest(reason=reason):
                summary = self.capture.summarize([
                    message(reason, "Verification Verdict: VERIFIED\nProbe Completion: COMPLETE\nIMPLEMENT RESULT\nCompletion: COMPLETE"),
                    {"type": "agent_end", "isTerminal": True},
                ])
                self.assertTrue(summary["agent_ended"])
                self.assertFalse(summary["model_completed"])
                self.assertIsNone(summary["parsed_verdict"])
                self.assertIsNone(summary["probe_completion"])
                self.assertIsNone(summary["implementation_completion"])

    def test_terminal_error_detail_and_empty_response_are_preserved(self) -> None:
        summary = self.capture.summarize([
            message("error", "", errorMessage="The usage limit has been reached"),
            {"type": "agent_end"},
        ])
        self.assertFalse(summary["model_completed"])
        self.assertEqual(summary["terminal_text"], "")
        self.assertEqual(summary["error_message"], "The usage limit has been reached")

    def test_later_tool_call_cannot_reuse_an_earlier_verdict(self) -> None:
        summary = self.capture.summarize([
            message("stop", "Verification Verdict: VERIFIED\nIMPLEMENT RESULT\nCompletion: COMPLETE"),
            message("toolUse", "", content=[{"type": "toolCall", "name": "read", "arguments": {"path": "app.py"}}]),
            {"type": "agent_end"},
        ])
        self.assertFalse(summary["model_completed"])
        self.assertEqual(summary["terminal_text"], "")
        self.assertIsNone(summary["parsed_verdict"])
        self.assertIsNone(summary["implementation_completion"])

    def test_complete_implementation_terminal_exposes_its_completion(self) -> None:
        for completion in ("COMPLETE", "BLOCKED", "PARTIAL"):
            with self.subTest(completion=completion):
                summary = self.capture.summarize([
                    message("stop", f"## IMPLEMENT RESULT\n\n- **Ticket:** T-1\n- **Completion:** {completion} — 현재 요청 범위의 결과입니다."),
                    {"type": "agent_end"},
                ])
                self.assertTrue(summary["model_completed"])
                self.assertEqual(summary["implementation_completion"], completion)

    def test_implementation_completion_rejects_previous_quoted_and_conflicting_results(self) -> None:
        false_terminals = (
            "> IMPLEMENT RESULT\n> Completion: COMPLETE",
            "Previous report:\n```text\nIMPLEMENT RESULT\nCompletion: COMPLETE\n```",
            "IMPLEMENT RESULT\nCompletion: COMPLETE\nCompletion: BLOCKED",
            "IMPLEMENT RESULT\nCompletion: COMPLETE\nIMPLEMENT RESULT\nCompletion: BLOCKED",
        )
        for terminal in false_terminals:
            with self.subTest(terminal=terminal):
                summary = self.capture.summarize([message("stop", terminal), {"type": "agent_end"}])
                self.assertTrue(summary["model_completed"])
                self.assertIsNone(summary["implementation_completion"])
        summary = self.capture.summarize([
            message("stop", "IMPLEMENT RESULT\nCompletion: COMPLETE"),
            message("stop", "The previous implementation report is no longer current."),
            {"type": "agent_end"},
        ])
        self.assertIsNone(summary["implementation_completion"])

    def test_current_probe_terminal_preserves_completion_state(self) -> None:
        for completion in ("COMPLETE", "PARTIAL", "BLOCKED"):
            with self.subTest(completion=completion):
                terminal = f"## READY TICKET HEURISTIC PROBE RESULT\n- **Probe Completion:** {completion}"
                summary = self.capture.summarize([message("stop", terminal), {"type": "agent_end"}])
                self.assertEqual(summary["probe_completion"], completion)
                self.assertIsNone(summary["parsed_verdict"])

    def test_probe_admission_rejects_quoted_conflicting_and_superseded_completion(self) -> None:
        for terminal in (
            "> READY TICKET HEURISTIC PROBE RESULT\n> Probe Completion: COMPLETE",
            "Previous result:\n```text\nREADY TICKET HEURISTIC PROBE RESULT\nProbe Completion: COMPLETE\n```",
            "READY TICKET HEURISTIC PROBE RESULT\nProbe Completion: COMPLETE\nProbe Completion: BLOCKED",
            "READY TICKET HEURISTIC PROBE RESULT\nProbe Completion: COMPLETE\nREADY TICKET HEURISTIC PROBE RESULT\nProbe Completion: PARTIAL",
        ):
            with self.subTest(terminal=terminal):
                summary = self.capture.summarize([message("stop", terminal), {"type": "agent_end"}])
                self.assertIsNone(summary["probe_completion"])
        summary = self.capture.summarize([
            message("stop", "READY TICKET HEURISTIC PROBE RESULT\nProbe Completion: COMPLETE"),
            message("stop", "The earlier Probe result is no longer current."),
            {"type": "agent_end"},
        ])
        self.assertIsNone(summary["probe_completion"])

    def test_normal_domain_failure_is_not_a_transport_failure(self) -> None:
        summary = self.capture.summarize([
            {"type": "tool_execution_end", "isError": True},
            message("stop", "Verification Verdict: INCONCLUSIVE"),
            {"type": "agent_end"},
        ])
        self.assertTrue(summary["model_completed"])
        self.assertEqual(summary["parsed_verdict"], "INCONCLUSIVE")

    def test_success_requires_nonempty_final_response_and_agent_end(self) -> None:
        for events in (
            [message("stop", "Verification Verdict: VERIFIED\nIMPLEMENT RESULT\nCompletion: COMPLETE")],
            [message("stop", " \n"), {"type": "agent_end"}],
            [{"type": "agent_end"}],
        ):
            with self.subTest(events=events):
                summary = self.capture.summarize(events)
                self.assertFalse(summary["model_completed"])
                self.assertIsNone(summary["implementation_completion"])

    def test_planning_report_and_resume_reject_old_clean_flag(self) -> None:
        planning = load_module("planning")
        with tempfile.TemporaryDirectory() as directory:
            arena = Path(directory)
            metadata_path = planning.prepare("current-evidence--current", arena, "B", 1)
            metadata = json.loads(metadata_path.read_text())
            run_root = Path(metadata["run_root"])
            turn_root = run_root / "turn-1"
            turn_root.mkdir()
            events_path = turn_root / "events.jsonl"
            events_path.write_text("".join(json.dumps(event) + "\n" for event in [
                message("error", "", errorMessage="provider unavailable"), {"type": "agent_end"},
            ]))
            terminal_path = turn_root / "terminal.txt"
            terminal_path.write_text("")
            digest = hashlib.sha256(events_path.read_bytes()).hexdigest()
            metadata["turns"] = [{
                "raw_events": str(events_path), "raw_events_sha256": digest,
                "terminal": str(terminal_path), "terminal_sha256": hashlib.sha256(b"").hexdigest(),
                "clean_transport": True, "product_mutated": False,
                "pre_snapshot": metadata["initial_snapshot"], "post_snapshot": metadata["initial_snapshot"],
                "actual_models": ["opencodex/gpt-6-astra"],
            }]
            planning.write_json(metadata_path, metadata)
            cohort = arena / "cohort.json"
            reviews = arena / "reviews.json"
            planning.write_json(cohort, {
                "case_ids": [metadata["case_id"]], "variants": ["B"], "repetitions": [1],
                "model": "opencodex/gpt-6-astra", "runs": [{
                    **{key: metadata[key] for key in ("case_id", "run_id", "variant", "repetition")},
                    "metadata": str(metadata_path),
                }],
            })
            planning.write_json(reviews, [{
                "run_id": metadata["run_id"], "causal_evidence_sufficient": True,
                "reason": "A positive review cannot override a native failure.",
                "evidence_refs": [{"path": str(events_path), "sha256": digest}],
            }])

            report = planning.report(cohort, reviews)
            self.assertFalse(report["causal_gate_pass"])
            self.assertIn("model_not_cleanly_terminated", {error["code"] for error in report["errors"]})
            with self.assertRaises(ValueError):
                planning.run_turn(metadata_path, "Continue", agent_dir=arena / "missing",
                                  payload=arena / "missing", runtime_data=arena,
                                  model="opencodex/gpt-6-astra")
            self.assertFalse((run_root / "turn-2").exists())

    def test_planning_rejects_unbound_preparation_before_model_invocation(self) -> None:
        planning = load_module("planning")
        with tempfile.TemporaryDirectory() as directory:
            arena = Path(directory)
            metadata_path = planning.prepare("current-evidence--current", arena, "B", 1)
            metadata = json.loads(metadata_path.read_text())
            run_root = Path(metadata["run_root"])
            for provenance in (None, "0" * 64):
                with self.subTest(provenance=provenance):
                    metadata.pop("fixture_source_sha256", None)
                    if provenance is not None:
                        metadata["fixture_source_sha256"] = provenance
                    planning.write_json(metadata_path, metadata)
                    with mock.patch.object(planning, "invoke", side_effect=AssertionError("Model must not run")):
                        with self.assertRaises(ValueError):
                            planning.run_turn(metadata_path, "Start", agent_dir=arena / "missing",
                                              payload=arena / "missing", runtime_data=arena,
                                              model="opencodex/gpt-6-astra")
                    self.assertFalse((run_root / "turn-1").exists())

    def test_planning_source_change_invalidates_loaded_generator_and_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "planning.py"
            source.write_bytes((EVALUATION / "planning.py").read_bytes())
            (root / "planning-cases.json").write_bytes((EVALUATION / "planning-cases.json").read_bytes())
            spec = importlib.util.spec_from_file_location("changed_planning", source)
            planning = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(planning)
            metadata_path = planning.prepare("current-evidence--current", root / "prepared", "B", 1)
            original_metadata = metadata_path.read_bytes()
            source.write_text(source.read_text().replace("policy=strict", "policy=revised"))
            with self.assertRaises(ValueError):
                planning.prepare("current-evidence--current", root / "stale", "B", 1)
            self.assertFalse((root / "stale").exists())
            with mock.patch.object(planning, "invoke", side_effect=AssertionError("Model must not run")):
                with self.assertRaises(ValueError):
                    planning.run_turn(metadata_path, "Start", agent_dir=root / "missing",
                                      payload=root / "missing", runtime_data=root,
                                      model="opencodex/gpt-6-astra")
            self.assertEqual(metadata_path.read_bytes(), original_metadata)
            self.assertFalse((metadata_path.parent / "turn-1").exists())


if __name__ == "__main__":
    unittest.main()
