from __future__ import annotations

import json
import tempfile
import threading
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

    def test_disjoint_workers_can_overlap_and_preserve_combined_current_product(self) -> None:
        product: dict[str, object] = {"route_a": False, "route_b": False, "user_change": "keep"}
        ready = threading.Barrier(2)
        events: list[str] = []

        def worker(key: str) -> None:
            ready.wait(timeout=1)
            self.assertEqual(product["user_change"], "keep")
            product[key] = True
            events.append(f"finished:{key}")

        first = threading.Thread(target=worker, args=("route_a",))
        second = threading.Thread(target=worker, args=("route_b",))
        first.start()
        second.start()
        first.join(timeout=1)
        second.join(timeout=1)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(set(events), {"finished:route_a", "finished:route_b"})
        self.assertEqual(product, {"route_a": True, "route_b": True, "user_change": "keep"})

    def test_fresh_transition_verification_waits_for_overlapped_verifier_and_its_late_effect(self) -> None:
        product = {"late_verifier_effect": False}
        events: list[str] = []
        old_started = threading.Event()
        allow_old_return = threading.Event()
        old_finished = threading.Event()
        allow_effect_finish = threading.Event()
        effect_finished = threading.Event()
        fresh_finished = threading.Event()
        effect_threads: list[threading.Thread] = []

        def late_effect() -> None:
            self.assertTrue(allow_effect_finish.wait(timeout=1))
            product["late_verifier_effect"] = True
            events.append("old-effect-terminal")
            effect_finished.set()

        def old_navigation_verifier() -> None:
            events.append("old-verifier-start")
            old_started.set()
            self.assertTrue(allow_old_return.wait(timeout=1))
            effect = threading.Thread(target=late_effect)
            effect_threads.append(effect)
            effect.start()
            events.append("old-verifier-return")
            old_finished.set()

        def fresh_verifier_after_quiescence() -> None:
            self.assertTrue(old_finished.wait(timeout=1))
            self.assertTrue(effect_finished.wait(timeout=1))
            events.append("fresh-verifier-start")
            self.assertTrue(product["late_verifier_effect"])
            fresh_finished.set()

        old = threading.Thread(target=old_navigation_verifier)
        fresh = threading.Thread(target=fresh_verifier_after_quiescence)
        old.start()
        self.assertTrue(old_started.wait(timeout=1))
        events.extend(("worker-start", "worker-finish"))
        fresh.start()
        self.assertNotIn("fresh-verifier-start", events)
        allow_old_return.set()
        old.join(timeout=1)
        self.assertIn("old-verifier-return", events)
        self.assertNotIn("fresh-verifier-start", events)
        allow_effect_finish.set()
        for effect in effect_threads:
            effect.join(timeout=1)
        fresh.join(timeout=1)

        self.assertTrue(fresh_finished.is_set())
        self.assertLess(events.index("old-verifier-return"), events.index("old-effect-terminal"))
        self.assertLess(events.index("old-effect-terminal"), events.index("fresh-verifier-start"))


if __name__ == "__main__":
    unittest.main()
