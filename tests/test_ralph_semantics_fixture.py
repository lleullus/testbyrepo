from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class RalphSemanticsFixtureTests(unittest.TestCase):
    """Exercise the desired loop semantics without claiming agent/leaf execution."""

    def test_same_delivery_unit_repeats_until_all_current_acceptance_rows_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            product = Path(temporary) / "product-state.json"
            product.write_text(
                json.dumps({"outcome_1": False, "outcome_2": False}, sort_keys=True),
                encoding="utf-8",
            )

            def observe() -> tuple[bool, bool]:
                state = json.loads(product.read_text(encoding="utf-8"))
                return state["outcome_1"], state["outcome_2"]

            def bounded_correction(outcome: str) -> None:
                state = json.loads(product.read_text(encoding="utf-8"))
                state[outcome] = True
                product.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

            initial = observe()
            self.assertEqual(initial, (False, False))

            # First implementation iteration on the same conceptual Ticket.
            bounded_correction("outcome_1")
            after_first = observe()
            self.assertEqual(after_first, (True, False))
            self.assertFalse(all(after_first), "partial improvement must not complete the Goal")

            # A newly exposed defect remains the same delivery unit, not a new Goal.
            bounded_correction("outcome_2")
            after_second = observe()
            self.assertEqual(after_second, (True, True))

            # Final completion is derived from a new read, not the implementation narration.
            fresh_final = observe()
            self.assertTrue(all(fresh_final))

    def test_regression_after_a_correction_returns_the_same_goal_to_open(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            product = Path(temporary) / "product-state.json"
            product.write_text(
                json.dumps({"owned": True, "preserved": True}, sort_keys=True),
                encoding="utf-8",
            )

            def observe() -> dict[str, bool]:
                return json.loads(product.read_text(encoding="utf-8"))

            state = observe()
            state["owned"] = True
            state["preserved"] = False
            product.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

            current = observe()
            self.assertTrue(current["owned"])
            self.assertFalse(current["preserved"])
            self.assertFalse(all(current.values()), "a preserved-Behavior regression keeps the Goal open")

    def test_one_fresh_acquisition_can_classify_multiple_acs_after_each_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            product = Path(temporary) / "product-state.json"
            product.write_text(
                json.dumps({"ac_1": False, "ac_2": False, "preserved": True}, sort_keys=True),
                encoding="utf-8",
            )
            acquisitions = 0

            def acquire_current_boundary() -> dict[str, bool]:
                nonlocal acquisitions
                acquisitions += 1
                return json.loads(product.read_text(encoding="utf-8"))

            before = acquire_current_boundary()
            self.assertEqual(acquisitions, 1)
            self.assertEqual(
                {key: before[key] for key in ("ac_1", "ac_2", "preserved")},
                {"ac_1": False, "ac_2": False, "preserved": True},
            )

            changed = dict(before)
            changed["ac_1"] = True
            changed["preserved"] = False
            product.write_text(json.dumps(changed, sort_keys=True), encoding="utf-8")

            # The pre-mutation acquisition is stale. One new acquisition after the
            # mutation separately exposes both the repaired AC and sibling regression.
            after = acquire_current_boundary()
            self.assertEqual(acquisitions, 2)
            self.assertTrue(after["ac_1"])
            self.assertFalse(after["ac_2"])
            self.assertFalse(after["preserved"])
            self.assertFalse(all(after.values()))

    def test_distinct_inputs_and_states_remain_distinct_acquisitions(self) -> None:
        acquisitions: list[tuple[str, str]] = []
        product = {
            ("nominal", "ready"): {"ac_1": True},
            ("invalid", "ready"): {"ac_2": True},
        }

        def acquire(input_name: str, state_name: str) -> dict[str, bool]:
            acquisitions.append((input_name, state_name))
            return product[(input_name, state_name)]

        nominal = acquire("nominal", "ready")
        invalid = acquire("invalid", "ready")
        self.assertTrue(nominal["ac_1"])
        self.assertTrue(invalid["ac_2"])
        self.assertEqual(acquisitions, [("nominal", "ready"), ("invalid", "ready")])

    def test_implementation_context_is_reused_only_while_the_same_ticket_is_active(self) -> None:
        next_context = 0
        active_ticket: str | None = None
        active_context: int | None = None

        def implementation_context_for(ticket: str) -> int:
            nonlocal next_context, active_ticket, active_context
            if ticket != active_ticket:
                next_context += 1
                active_ticket = ticket
                active_context = next_context
            assert active_context is not None
            return active_context

        first_a = implementation_context_for("TICKET-A")
        second_a = implementation_context_for("TICKET-A")
        first_b = implementation_context_for("TICKET-B")
        later_a = implementation_context_for("TICKET-A")

        self.assertEqual(first_a, second_a, "same active Ticket keeps its working context")
        self.assertNotEqual(first_a, first_b, "Ticket transition must discard the prior context")
        self.assertNotEqual(first_a, later_a, "returning later to a left Ticket starts fresh context")

    def test_verification_can_surface_more_work_while_same_ticket_implementation_is_in_flight(self) -> None:
        product = {"a": False, "b": False}
        events: list[str] = []
        active_workers: set[str] = set()
        transition_verification_authoritative = True

        def observe(name: str) -> bool:
            events.append(f"verify:{name}")
            return product[name]

        def dispatch(name: str) -> None:
            nonlocal transition_verification_authoritative
            transition_verification_authoritative = False
            active_workers.add(name)
            events.append(f"dispatch:{name}")

        self.assertFalse(observe("a"))
        dispatch("a")
        self.assertFalse(observe("b"), "verification continues while the first worker is active")
        dispatch("b")
        events.append("verification-finished")

        self.assertLess(events.index("dispatch:a"), events.index("verify:b"))
        self.assertLess(events.index("dispatch:b"), events.index("verification-finished"))
        self.assertFalse(
            transition_verification_authoritative,
            "a verifier overlapped by mutation cannot authorize leaving the Ticket",
        )

        for name in tuple(active_workers):
            product[name] = True
            active_workers.remove(name)
            events.append(f"worker-finished:{name}")

        self.assertFalse(active_workers)
        final_fresh = {name: product[name] for name in ("a", "b")}
        events.append("fresh-final-verification")
        self.assertTrue(all(final_fresh.values()))
        self.assertGreater(
            events.index("fresh-final-verification"),
            max(events.index("worker-finished:a"), events.index("worker-finished:b")),
        )

    def test_late_worker_rechecks_current_product_and_noops_when_sibling_already_satisfied_the_work(self) -> None:
        product = {"primary": False, "secondary": False}
        mutations: list[str] = []

        def first_worker() -> None:
            current = dict(product)
            current["primary"] = True
            current["secondary"] = True
            product.update(current)
            mutations.append("first")

        def later_worker() -> None:
            if product["secondary"]:
                return
            product["secondary"] = True
            mutations.append("later")

        first_worker()
        later_worker()

        self.assertEqual(product, {"primary": True, "secondary": True})
        self.assertEqual(mutations, ["first"], "stale work must not be applied after a sibling already fixed it")


if __name__ == "__main__":
    unittest.main()
