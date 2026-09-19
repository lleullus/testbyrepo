from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluation/ready-verification/failure_space_fixtures.py"


def load_fixtures():
    spec = importlib.util.spec_from_file_location("failure_space_fixtures", FIXTURES)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load failure-space fixtures")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FailureSpaceDiscriminatingFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = load_fixtures()

    def test_adjacent_transition_requires_next_operation(self) -> None:
        bad, good = self.fx.AdjacentTransition(True), self.fx.AdjacentTransition(False)
        self.assertTrue(bad.action_x() and good.action_x())
        self.assertEqual(bad.state, good.state)
        self.assertFalse(bad.next_operation())
        self.assertTrue(good.next_operation())

    def test_threshold_crossing_checks_original_consumer(self) -> None:
        bad, good = self.fx.ThresholdStream(True), self.fx.ThresholdStream(False)
        self.assertEqual(bad.produce_while_paused(9), "producer-complete")
        self.assertEqual(good.produce_while_paused(9), "producer-complete")
        self.assertIsNone(bad.next_consumer_read_after_resume())
        self.assertEqual(good.next_consumer_read_after_resume(), "next-output")

    def test_hidden_phase_separates_transport_and_application(self) -> None:
        bad, good = self.fx.SchedulerRecovery(True), self.fx.SchedulerRecovery(False)
        for recovery in (bad, good):
            recovery.start_hidden()
            self.assertTrue(recovery.transport_pong())
            recovery.settle_parser()
        self.assertFalse(bad.ready)
        self.assertTrue(good.ready)

    def test_liveness_proxy_does_not_prove_usable_owner(self) -> None:
        bad, good = self.fx.OwnerLiveness(True), self.fx.OwnerLiveness(False)
        self.assertTrue(bad.owner_is_usable())
        self.assertFalse(good.owner_is_usable())
        good.application_progress = True
        self.assertTrue(good.owner_is_usable())

    def test_same_instance_exposes_terminal_state_residue(self) -> None:
        for defective, expected in ((True, False), (False, True)):
            terminal = self.fx.TerminalLifecycle(defective)
            terminal.observe_exit()
            terminal.start_new()
            self.assertEqual(terminal.first_input(), expected)
        fresh = self.fx.TerminalLifecycle(True)
        fresh.start_new()
        self.assertTrue(fresh.first_input(), "a fresh-only check would miss the residue")

    def test_delayed_callback_exposes_lifetime_violation(self) -> None:
        bad, good = self.fx.DelayedClose(True), self.fx.DelayedClose(False)
        self.assertTrue(bad.release_before_callback())
        self.assertFalse(good.release_before_callback())
        self.assertEqual(bad.run_callback(), "use-after-free")
        self.assertEqual(good.run_callback(), "closed-once")
        self.assertEqual(self.fx.DelayedClose(True).run_callback(), "closed-once")

    def test_scope_omission_is_a_contract_gap(self) -> None:
        self.assertEqual(
            self.fx.semantic_preflight({"happy", "recovery"}, {"happy"}),
            ("contract-gap", ("recovery",)),
        )
        self.assertEqual(
            self.fx.semantic_preflight({"happy", "recovery"}, {"happy", "recovery"}),
            ("ready", ()),
        )

    def test_artifact_control_does_not_invent_runtime_frontier(self) -> None:
        self.assertEqual(self.fx.implementation_frontier(artifact_only=True, runtime_clues=()), ())
        self.assertEqual(
            self.fx.implementation_frontier(artifact_only=False, runtime_clues=("buffer",)),
            ("buffer",),
        )

    def test_observation_outcome_distinguishes_violation_and_unknown(self) -> None:
        disposition = self.fx.evidence_disposition
        self.assertEqual(disposition(required_runtime_available=False, contradiction_observed=False), "UNOBSERVABLE")
        self.assertEqual(disposition(required_runtime_available=True, contradiction_observed=True), "VIOLATED")
        self.assertEqual(disposition(required_runtime_available=True, contradiction_observed=False), "SATISFIED")


if __name__ == "__main__":
    unittest.main()
