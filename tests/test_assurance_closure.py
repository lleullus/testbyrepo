import unittest

from assurance_support import AssuranceFixture, assurance


class ClosureTests(AssuranceFixture, unittest.TestCase):
    def test_failed_direct_readback_blocks_other_successes(self):
        assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        self.observation(outcome="VIOLATED")
        self.assertIn("OBSERVATION_NOT_SATISFIED", self.closure()["reasons"])

    def test_started_result_cannot_be_removed_from_denominator(self):
        assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        assurance.begin_host_invocation(self.store, self.binding, "observation", "readback")
        self.assertIn("STARTED_RESULT_MISSING", self.closure()["reasons"])

    def test_required_work_not_started_is_detected_from_host_ledger(self):
        assurance.run_gate(
            self.baseline_path,
            self.store,
            self.binding,
            "native",
            self.arena / ("native-capture-" + self.binding["run_id"]),
        )
        self.assertIn("REQUIRED_WORK_NOT_STARTED", self.closure()["reasons"])

    def test_unknown_effect_blocks_even_when_checks_pass(self):
        self.evidence()
        evidence = assurance.capture_invocation_evidence(
            self.store,
            self.binding,
            "effect-owner",
            {"effect/state.txt": b"unknown\n"},
        )
        assurance.record_effect(
            self.store,
            self.binding,
            "write",
            owner="native",
            state="UNKNOWN",
            evidence=evidence,
        )
        self.assertIn("UNSETTLED_EFFECT", self.closure()["reasons"])

    def test_optional_started_probe_is_in_denominator_and_material_finding_blocks(self):
        targeted = {
            "id": "targeted",
            "surfaces": ["entry"],
            "required": True,
            "min_actions": 1,
            "budget": "one trace",
            "safety": "read-only",
        }
        scout = {**targeted, "id": "scout", "required": False}
        self.baseline.update(
            surfaces=[{"id": "entry", "boundary": "actual CLI"}],
            lanes=[targeted, scout],
            no_probe_reason=None,
        )
        self.seal()
        self.evidence()
        self.probe("targeted", outcome="NO_COUNTEREXAMPLE_WITHIN_BUDGET")
        self.assertEqual(self.closure()["status"], "EVIDENCE_COMPLETE")
        self.probe("scout", outcome="COUNTEREXAMPLE_FOUND", material=True)
        self.assertIn("UNRESOLVED_COUNTEREXAMPLE", self.closure()["reasons"])

    def test_optional_started_probe_without_terminal_result_blocks(self):
        targeted = {
            "id": "targeted",
            "surfaces": ["entry"],
            "required": True,
            "min_actions": 1,
            "budget": "one trace",
            "safety": "read-only",
        }
        scout = {**targeted, "id": "scout", "required": False}
        self.baseline.update(
            surfaces=[{"id": "entry", "boundary": "actual CLI"}],
            lanes=[targeted, scout],
            no_probe_reason=None,
        )
        self.seal()
        self.evidence()
        self.probe("targeted", outcome="NO_COUNTEREXAMPLE_WITHIN_BUDGET")
        assurance.begin_host_invocation(self.store, self.binding, "probe", "scout")
        self.assertIn("STARTED_RESULT_MISSING", self.closure()["reasons"])


if __name__ == "__main__":
    unittest.main()
