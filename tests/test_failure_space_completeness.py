from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluation/ready-verification/failure_space_fixtures.py"
CASES = ROOT / "evaluation/ready-verification/failure-space-cases.json"


def load_fixtures():
    spec = importlib.util.spec_from_file_location("failure_space_fixtures", FIXTURES)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load failure-space fixtures")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FailureSpaceContractHandoffTests(unittest.TestCase):
    def test_existing_roles_carry_frontier_without_new_review_schema(self) -> None:
        paths = {
            "plan_skill": "companion-skills/scope-plan/SKILL.md",
            "plan": "companion-skills/scope-plan/references/plan.md",
            "review": "companion-skills/scope-plan/references/review.md",
            "implement": "companion-skills/scope-implement/references/implement.md",
            "verify": "companion-skills/scope-verify/references/verify.md",
            "probe": "companion-skills/production-heuristic-probing/SKILL.md",
        }
        text = {name: (ROOT / path).read_text(encoding="utf-8") for name, path in paths.items()}
        expected = {
            "plan_skill": "implementation-grounded failure frontier",
            "plan": "## Implementation-grounded failure frontier",
            "review": "Independently derive the important implementation-grounded failure frontier",
            "implement": "minimum subsequent operation or authoritative readback",
            "verify": "bounded as-built failure frontier",
            "probe": "residual heuristic search",
        }
        for name, phrase in expected.items():
            with self.subTest(role=name):
                self.assertIn(phrase, text[name])
        self.assertIn('"schema": "iis-scope-plan-review/v2"', text["review"])
        self.assertNotIn("iis-scope-plan-review/v3", "\n".join(text.values()))

    def test_evaluation_inventory_is_explicit_and_bounded(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "iis-failure-space-cases/v1")
        ids = [case["case_id"] for case in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 9)
        for case in data["cases"]:
            self.assertTrue(case["minimum_discriminator"].strip())
            self.assertTrue(case["expected_earliest_owner"].strip())


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

    def test_unavailable_boundary_remains_inconclusive(self) -> None:
        disposition = self.fx.evidence_disposition
        self.assertEqual(disposition(required_runtime_available=False, contradiction_observed=False), "INCONCLUSIVE")
        self.assertEqual(disposition(required_runtime_available=True, contradiction_observed=True), "FAILED")
        self.assertEqual(disposition(required_runtime_available=True, contradiction_observed=False), "VERIFIED")


if __name__ == "__main__":
    unittest.main()
