import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("assurance_score_test", ROOT / "evaluation/ready-verification/score_assurance.py")
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


class CausalScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.candidate = self.ref("candidate", {"source": "fixture-candidate"})
        self.conditions = self.ref("conditions", {"model": "not-invoked-unit-fixture", "budget": 1})
        self.inputs = self.ref("inputs", {"fixture": "paired-entry"})
        self.manifest = {"schema": "iis-assurance-experiment/v2", "experiment_id": "exp-1", "repetitions": 1,
                         "variants": {"candidate": {"candidate": [self.candidate], "conditions": [self.conditions]}},
                         "cases": [{"id": "bad", "expected": "DEFECT", "defect_id": "wrong-entry", "inputs": [self.inputs], "oracle": {"path": ["value"], "equals": "old"}},
                                   {"id": "good", "expected": "NORMAL", "defect_id": None, "inputs": [self.inputs], "oracle": {"path": ["value"], "equals": "new"}}],
                         "limits": {"min_detection": 1, "max_false_completion": 0, "max_false_block": 0, "max_incomplete": 0}}
        self.records = [self.record("bad", "old"), self.record("good", "new")]

    def ref(self, name, value):
        path = self.root / (name + ".json")
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        return {"path": str(path)}

    def record(self, case, value):
        run = case + "-run"
        target = {"source": "source-a", "artifact": "native-source", "runtime": "python-fixture", "mechanism": "capture-v1"}
        trace = self.ref(case + "-trace", {"run_id": run, "target": target, "initial_state": "fresh fixture", "trigger": "actual-entry", "readback": {"value": value}})
        return {"experiment_id": "exp-1", "variant": "candidate", "case_id": case, "repetition": 1, "run_id": run,
                "candidate": [self.candidate], "conditions": [self.conditions], "inputs": [self.inputs],
                "events": [trace], "state": "COMPLETE", "target": target, "observation": trace,
                "mutation": self.ref(case + "-mutation", {"run_id": run, "target_mutated": False}),
                "settlement": self.ref(case + "-settlement", {"run_id": run, "state": "SETTLED"}),
                "closure": "BLOCKED" if case == "bad" else "EVIDENCE_COMPLETE",
                "findings": [{"defect_id": "wrong-entry", "lane": "targeted", "trace": trace}] if case == "bad" else [],
                "cost": {"tokens": 10, "tool_calls": 2, "wall_seconds": 1, "correction_seconds": 0}}

    def score(self):
        return scorer.score(self.manifest, self.records)

    def test_causal_pair_and_duplicate_lanes_do_not_inflate_detection(self):
        self.records[0]["findings"].append({**self.records[0]["findings"][0], "lane": "scout"})
        report = self.score()
        self.assertTrue(report["evaluation_pass"])
        variant = report["variants"]["candidate"]
        self.assertEqual(variant["detected_runs"], 1)
        self.assertEqual(variant["duplicate_traces"], 1)
        self.assertEqual(variant["lanes"]["scout"]["unique_contribution"], 0)

    def test_expected_field_cannot_override_causal_readback(self):
        bad = self.records[0]
        bad["expected"] = "DEFECT"
        bad["observation"] = self.ref("fabricated", {"run_id": bad["run_id"], "target": bad["target"], "initial_state": "fresh", "trigger": "actual-entry", "readback": {"value": "new"}})
        self.assertFalse(self.score()["evaluation_pass"])

    def test_missing_raw_evidence_does_not_pass_on_matching_labels(self):
        self.records[0]["events"] = []
        self.assertFalse(self.score()["evaluation_pass"])

    def test_missing_run_identity_and_duplicate_repetition_are_rejected(self):
        del self.records[0]["run_id"]
        self.assertFalse(self.score()["evaluation_pass"])
        self.records = [self.record("bad", "old"), self.record("good", "new")]
        self.records.append(copy.deepcopy(self.records[0]))
        self.assertFalse(self.score()["evaluation_pass"])

    def test_missing_repetitions_remain_in_denominator(self):
        self.manifest["repetitions"] = 2
        report = self.score()
        self.assertFalse(report["evaluation_pass"])
        self.assertEqual(len(report["missing"]), 2)
        self.assertEqual(report["variants"]["candidate"]["detection"], 0.5)

    def test_all_blocked_is_not_a_quality_success(self):
        for record in self.records:
            record.update(state="BLOCKED", reason="boundary unavailable", closure="BLOCKED")
        report = self.score()
        self.assertFalse(report["evaluation_pass"])
        self.assertEqual(report["variants"]["candidate"]["incomplete"], 2)
        self.assertEqual(report["variants"]["candidate"]["cost"]["tokens"], 20)

    def test_missing_mutation_observation_is_not_default_false(self):
        self.records[1]["mutation"] = self.ref("missing-mutation", {"run_id": "good-run"})
        self.assertFalse(self.score()["evaluation_pass"])

    def test_unknown_settlement_cannot_support_completion(self):
        self.records[1]["settlement"] = self.ref("unknown-settlement", {"run_id": "good-run", "state": "UNKNOWN"})
        report = self.score()
        self.assertFalse(report["evaluation_pass"])
        self.assertEqual(report["variants"]["candidate"]["false_completion"], 1)

    def test_foreign_target_trace_is_rejected(self):
        record = self.records[0]
        record["observation"] = self.ref("foreign", {"run_id": record["run_id"], "target": {**record["target"], "source": "other"}, "initial_state": "fresh", "trigger": "actual-entry", "readback": {"value": "old"}})
        self.assertFalse(self.score()["evaluation_pass"])
