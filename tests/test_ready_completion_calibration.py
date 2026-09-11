from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "evaluation/ready-verification"
COMPLETION = EVALUATION / "completion.py"
ORACLE = EVALUATION / "completion-cases.json"


def load_completion():
    sys.path.insert(0, str(EVALUATION))
    try:
        spec = importlib.util.spec_from_file_location("ready_completion_calibration", COMPLETION)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load completion calibration CLI")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class ReadyCompletionCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.completion = load_completion()
        self.oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)


    def test_prepare_keeps_oracle_and_case_identity_outside_product_and_prompt(self) -> None:
        metadata_path, metadata = self.completion.prepare(
            "parent-obligation-unowned", self.root / "arena", "candidate", 1,
        )
        prompt = self.completion.completion_prompt(metadata)
        product = Path(metadata["project_root"])

        self.assertNotIn(metadata["case_id"], prompt)
        self.assertNotIn("expected_completion", prompt)
        self.assertNotIn("parent-obligation-unowned", "\n".join(str(path.relative_to(product)) for path in product.rglob("*")))
        self.assertIn("synthetic fixture setup history", prompt)

    def test_actual_ordinary_readback_distinguishes_preserved_and_regressed_state(self) -> None:
        outputs = []
        for index, case_id in enumerate(("later-change-preserved", "later-change-regressed"), 1):
            _, metadata = self.completion.prepare(case_id, self.root / f"arena-{index}", "candidate", 1)
            result = subprocess.run(metadata["trigger_argv"], check=True, capture_output=True, text=True)
            outputs.append(json.loads(result.stdout))

        self.assertEqual(outputs[0], {"input": "legacy", "value": "stable-value"})
        self.assertEqual(outputs[1], {"input": "legacy", "value": "regressed-value"})

    def test_operator_result_uses_separate_authority_and_rejects_its_drift(self) -> None:
        metadata_path, metadata = self.completion.prepare("operator-proof-current", self.root / "operator", "candidate", 1)
        product = Path(metadata["project_root"])
        self.completion.write_json(product / "evidence/operator-current.json", {"approved": False})
        observed = subprocess.run(metadata["trigger_argv"], check=True, capture_output=True, text=True)
        self.assertIs(json.loads(observed.stdout)["approved"], True)
        (product / "evidence/operator-current.json").unlink()

        self.completion.write_json(Path(metadata["support_root"]) / "operator-current.json", {"approved": False})
        observed = subprocess.run(metadata["trigger_argv"], check=True, capture_output=True, text=True)
        self.assertIs(json.loads(observed.stdout)["approved"], False)
        with self.assertRaises(ValueError):
            self.completion.run(metadata_path, agent_dir=self.root, payload=self.root,
                                model="opencodex/gpt-6-astra", thinking="medium", timeout=480)

    def test_operator_readback_computes_self_check_from_current_request(self) -> None:
        _, metadata = self.completion.prepare("operator-proof-current", self.root / "self-check", "candidate", 1)
        observed = subprocess.run(metadata["trigger_argv"], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(observed.stdout)["product_self_check"], "passed")
        self.completion.write_json(Path(metadata["project_root"]) / "state/current.json", {"requested_action": ""})
        observed = subprocess.run(metadata["trigger_argv"], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(observed.stdout)["product_self_check"], "failed")
        self.assertIs(json.loads(observed.stdout)["approved"], True)

    def test_done_label_cannot_replace_required_actual_setup(self) -> None:
        metadata_path, metadata = self.completion.prepare("verification-current", self.root / "setup", "candidate", 1)
        ticket = Path(metadata["ticket_path"])
        ticket.write_text(ticket.read_text().replace("Status: ready\n", "Status: done\n", 1))
        with self.assertRaises(ValueError):
            self.completion.run(metadata_path, agent_dir=self.root / "unavailable", payload=self.root / "unavailable",
                                model="opencodex/gpt-6-astra", thinking="medium", timeout=480)

    def test_parser_accepts_only_official_success_or_explicit_noncompletion(self) -> None:
        self.assertIs(self.completion.parse_completion("IIS ADAPTIVE RUN COMPLETE\n\nSTOP\n"), True)
        self.assertIs(self.completion.parse_completion("**IIS ADAPTIVE CURRENT INCREMENT IMPLEMENTED**\nSTOP\n"), True)
        self.assertIs(self.completion.parse_completion("IIS ADAPTIVE COMPLETION EVIDENCE REQUIRED\nWhole-run completion: no\nSTOP\n"), False)
        self.assertIs(self.completion.parse_completion("**Whole-run predicate satisfied:** no\nSTOP\n"), False)
        self.assertIs(self.completion.parse_completion("Existing owner result\nWhole-run completion: no\nSTOP\n"), False)
        self.assertIsNone(self.completion.parse_completion("The current state looks complete."))
        self.assertIsNone(self.completion.parse_completion("IIS ADAPTIVE RUN COMPLETE\nWhole-run completion: no\n"))
        self.assertIsNone(self.completion.parse_completion("IIS ADAPTIVE RUN COMPLETE\n", transport_valid=False))
        self.assertIsNone(self.completion.parse_completion("```text\nIIS ADAPTIVE RUN COMPLETE\n```"))
        self.assertIsNone(self.completion.parse_completion("> IIS ADAPTIVE RUN COMPLETE"))

    def test_preparation_file_without_actual_roles_cannot_close_run(self) -> None:
        metadata_path, metadata = self.completion.prepare("preparation-current", self.root / "plans", "candidate", 1)
        output = Path(metadata["run_root"]) / "prepare"
        output.mkdir()
        (output / "plan-review.json").write_text(json.dumps({"schema": "iis-plan-review/v1", "decisions": [{"decision": "ADMIT"}]}))
        (output / "record.json").write_text(json.dumps({"parsed_completion": "COMPLETE", "roles": []}))
        with self.assertRaises(ValueError):
            self.completion.run(metadata_path, agent_dir=self.root, payload=self.root,
                                model="opencodex/gpt-6-astra", thinking="high", timeout=60)

    def test_stale_five_role_preparation_record_cannot_close_run(self) -> None:
        metadata_path, metadata = self.completion.prepare("preparation-current", self.root / "legacy-roles", "candidate", 1)
        output = Path(metadata["run_root"]) / "prepare"
        output.mkdir()
        (output / "plan-review.json").write_text(json.dumps({"schema": "iis-plan-review/v1", "decisions": [{"decision": "ADMIT"}]}))
        roles = [{"role": role} for role in ("planner", "heuristic", "revision", "reviewer", "lead")]
        (output / "record.json").write_text(json.dumps({"parsed_completion": "COMPLETE", "roles": roles}))
        with self.assertRaises(ValueError):
            self.completion.run(metadata_path, agent_dir=self.root, payload=self.root,
                                model="opencodex/gpt-6-astra", thinking="high", timeout=60)

    def build_complete_candidate_cohort(self) -> tuple[list[Path], list[dict[str, object]], list[dict[str, object]]]:
        metadata_paths: list[Path] = []
        records: list[dict[str, object]] = []
        reviews: list[dict[str, object]] = []
        for repetition in self.oracle["required_repetitions"]:
            for case in self.oracle["cases"]:
                metadata_path, metadata = self.completion.prepare(
                    "parent-obligation-owned", self.root / f"cohort-r{repetition}-{case['case_id']}", "candidate", repetition,
                )
                # These are synthetic reporter-protocol records, not model evidence.
                metadata["case_id"] = case["case_id"]
                self.completion.write_json(metadata_path, metadata)
                metadata_paths.append(metadata_path)
                run_root = Path(metadata["run_root"])
                completion_dir = run_root / "completion"
                completion_dir.mkdir()
                events_path = completion_dir / "events.jsonl"
                terminal_path = completion_dir / "terminal.txt"
                terminal_path.write_text(
                    "IIS ADAPTIVE RUN COMPLETE\n" if case["expected_completion"] else "Whole-run completion: no\n",
                    encoding="utf-8",
                )
                events_path.write_text(json.dumps({
                    "type": "message_end", "message": {
                        "role": "assistant", "stopReason": "stop",
                        "provider": "opencodex", "model": "gpt-6-astra",
                        "content": [{"type": "text", "text": terminal_path.read_text()}],
                    },
                }) + '\n{"type":"agent_end"}\n', encoding="utf-8")
                product_digest = self.completion.snapshot_digest(
                    self.completion.product_snapshot(Path(metadata["project_root"]))
                )
                record = {
                    "schema": "iis-completion-observation/v1",
                    "case_id": metadata["case_id"],
                    "run_id": metadata["run_id"],
                    "variant": "candidate",
                    "repetition": repetition,
                    "parsed_completion": case["expected_completion"],
                    "parse_status": "complete" if case["expected_completion"] else "incomplete",
                    "raw_events": str(events_path.resolve()),
                    "raw_events_sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
                    "raw_terminal_result": str(terminal_path.resolve()),
                    "terminal_sha256": hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
                    "model_requested": "opencodex/gpt-6-astra",
                    "actual_models": ["opencodex/gpt-6-astra"],
                    "thinking": "medium",
                    "exit_code": 0,
                    "timed_out": False,
                    "agent_ended": True,
                    "target_mutated": False,
                    "changed_paths": [],
                    "pre_project_root_digest": product_digest,
                    "post_project_root_digest": product_digest,
                    "elapsed_seconds": 1.0,
                    "usage": {},
                    "fixture_history_limit": metadata["fixture_history_limit"],
                    "causal_review": "PENDING_INDEPENDENT_MAIN_REVIEW",
                }
                self.completion.write_json(completion_dir / "record.json", record)
                records.append(record)
                reviews.append({
                    "case_id": metadata["case_id"],
                    "run_id": metadata["run_id"],
                    "causal_evidence_sufficient": True,
                    "reason": "Raw events and current fixture boundary were independently inspected.",
                    "boundary_review": "The ordinary readback and exact current ownership/evidence state causally support this completion classification.",
                    "evidence_refs": [{
                        "path": str(events_path.resolve()),
                        "sha256": hashlib.sha256(events_path.read_bytes()).hexdigest(),
                    }],
                })
        return metadata_paths, records, reviews

    def test_report_rejects_provider_error_despite_successful_process_and_text(self) -> None:
        metadata_paths, records, reviews = self.build_complete_candidate_cohort()
        record = records[0]
        events_path = Path(record["raw_events"])
        events = [json.loads(line) for line in events_path.read_text().splitlines()]
        events[0]["message"]["stopReason"] = "error"
        events[0]["message"]["errorMessage"] = "The usage limit has been reached"
        events_path.write_text("".join(json.dumps(event) + "\n" for event in events))
        record["raw_events_sha256"] = hashlib.sha256(events_path.read_bytes()).hexdigest()
        self.completion.write_json(events_path.parent / "record.json", record)
        reviews[0]["evidence_refs"][0]["sha256"] = record["raw_events_sha256"]
        cohort = self.root / "cohort.json"
        results = self.root / "results.json"
        review_path = self.root / "reviews.json"
        self.completion.write_json(cohort, [str(path) for path in metadata_paths])
        self.completion.write_json(results, records)
        self.completion.write_json(review_path, reviews)

        report = self.completion.report(cohort, results, review_path)

        self.assertFalse(report["candidate_accepted"])
        self.assertIn("model_not_cleanly_terminated", {error["code"] for error in report["errors"]})

    def test_report_requires_exact_reviewed_capture_and_repetition_denominator(self) -> None:
        metadata_paths, records, reviews = self.build_complete_candidate_cohort()
        report = self.completion.build_report(metadata_paths, records, reviews, self.oracle)

        self.assertTrue(report["label_pass"])
        self.assertTrue(report["candidate_accepted"])
        self.assertEqual(report["errors"], [])

        missing_repetition = [path for path in metadata_paths if json.loads(path.read_text())["repetition"] == 1]
        retained_run_ids = {json.loads(path.read_text())["run_id"] for path in missing_repetition}
        missing_records = [record for record in records if record["run_id"] in retained_run_ids]
        missing_reviews = [review for review in reviews if review["run_id"] in retained_run_ids]
        incomplete = self.completion.build_report(missing_repetition, missing_records, missing_reviews, self.oracle)
        self.assertFalse(incomplete["candidate_accepted"])
        self.assertIn("inexact_repetition_denominator", {error["code"] for error in incomplete["errors"]})

    def test_report_rejects_selected_record_rewrite_target_change_and_false_review(self) -> None:
        metadata_paths, records, reviews = self.build_complete_candidate_cohort()
        changed_records = copy.deepcopy(records)
        changed_records[0]["parsed_completion"] = not changed_records[0]["parsed_completion"]
        changed_records[1]["target_mutated"] = True
        changed_records[1]["post_project_root_digest"] = "different"
        changed_reviews = copy.deepcopy(reviews)
        changed_reviews[2]["causal_evidence_sufficient"] = False
        changed_reviews[3]["evidence_refs"][0]["sha256"] = "0" * 64

        report = self.completion.build_report(metadata_paths, changed_records, changed_reviews, self.oracle)
        codes = {error["code"] for error in report["errors"]}

        self.assertFalse(report["candidate_accepted"])
        self.assertFalse(report["label_pass"])
        self.assertIn("capture_record_mismatch", codes)
        self.assertIn("target_changed", codes)
        self.assertIn("insufficient_causal_evidence", codes)
        self.assertIn("evidence_hash_mismatch", codes)

    def test_report_rejects_a_capture_that_also_used_another_model(self) -> None:
        metadata_paths, records, reviews = self.build_complete_candidate_cohort()
        records[0]["actual_models"].append("another-provider/fallback")
        self.completion.write_json(metadata_paths[0].parent / "completion/record.json", records[0])
        report = self.completion.build_report(metadata_paths, records, reviews, self.oracle)
        self.assertFalse(report["candidate_accepted"])
        self.assertIn("model_mismatch", {error["code"] for error in report["errors"]})


if __name__ == "__main__":
    unittest.main()
