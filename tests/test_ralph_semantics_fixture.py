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

    def test_user_role_binding_and_consumption_timing_drive_streaming_remediation(self) -> None:
        product = {"initial": False, "related": False, "distinct": False}
        events: list[str] = []
        consumed_implementation_roles: list[str] = []
        verification_roles = ["verification-runner-primary", "verification-runner-secondary", "verification-runner-later"]
        reserved_remediation_roles = ["remediation-next", "remediation-after-next"]
        active_corrections: dict[str, str] = {}
        verification_cycle_authoritative = True

        # The user's initial implementation designation is consumed at the initial
        # phase; remediation roles remain reserved instead of being used for fan-out.
        initial_role = "implementation-initial"
        consumed_implementation_roles.append(initial_role)
        product["initial"] = True
        events.append(f"implemented:{initial_role}")
        self.assertEqual(consumed_implementation_roles, [initial_role])
        self.assertEqual(reserved_remediation_roles, ["remediation-next", "remediation-after-next"])

        def start_new_correction(correction: str) -> str:
            nonlocal verification_cycle_authoritative
            role = reserved_remediation_roles.pop(0)
            consumed_implementation_roles.append(role)
            active_corrections[correction] = role
            verification_cycle_authoritative = False
            events.append(f"dispatch:{correction}:{role}")
            return role

        def route_finding(correction: str, detail: str) -> str:
            # A finding about work already in flight goes to that invocation first;
            # it does not consume another reserved role merely because another
            # verification Runner found additional evidence.
            if correction in active_corrections:
                role = active_corrections[correction]
                events.append(f"refine:{correction}:{role}:{detail}")
                return role
            return start_new_correction(correction)

        events.append(f"observe:{verification_roles[0]}:related")
        related_worker = route_finding("related", "first contradiction")
        self.assertEqual(related_worker, "remediation-next")
        self.assertEqual(reserved_remediation_roles, ["remediation-after-next"])

        events.append(f"observe:{verification_roles[1]}:related-more")
        same_worker = route_finding("related", "additional current evidence")
        self.assertEqual(same_worker, related_worker)
        self.assertEqual(
            reserved_remediation_roles,
            ["remediation-after-next"],
            "related evidence must not consume a new reserved implementation role",
        )

        # Verification may continue as navigation after mutation overlap. A truly
        # distinct safe correction may consume the next user-authorized role.
        events.append(f"observe:{verification_roles[2]}:distinct")
        distinct_worker = route_finding("distinct", "separate contradiction")
        self.assertEqual(distinct_worker, "remediation-after-next")
        self.assertFalse(verification_cycle_authoritative)
        self.assertNotIn("verification-runner-primary", consumed_implementation_roles)
        self.assertNotIn("verification-runner-secondary", consumed_implementation_roles)
        self.assertNotIn("verification-runner-later", consumed_implementation_roles)

        # All mutation settles before a fresh authoritative Ticket-verification
        # cycle; the overlapped cycle cannot authorize progression.
        product["related"] = True
        product["distinct"] = True
        active_corrections.clear()
        events.append("quiescent")
        fresh_ticket_verification = dict(product)
        events.append("fresh-ticket-verification")
        self.assertTrue(all(fresh_ticket_verification.values()))

        # Goal verification is a separate fresh final read, not reuse of Runner
        # context or the overlapped verification aggregate.
        fresh_goal_verification = dict(product)
        events.append("fresh-goal-verification")
        self.assertTrue(all(fresh_goal_verification.values()))
        self.assertLess(events.index("dispatch:related:remediation-next"), events.index("observe:verification-runner-secondary:related-more"))
        self.assertLess(events.index("quiescent"), events.index("fresh-ticket-verification"))
        self.assertLess(events.index("fresh-ticket-verification"), events.index("fresh-goal-verification"))

    def test_inconclusive_with_known_bounded_path_cannot_become_no_progress(self) -> None:
        paths = {
            "authored-boundary": {"known": True, "safe": True, "exhausted": True},
            "bounded-alternate-readback": {"known": True, "safe": True, "exhausted": False},
        }
        materially_distinct_correction = False

        def closure_complete() -> bool:
            return materially_distinct_correction is False and all(
                not path["known"] or not path["safe"] or path["exhausted"]
                for path in paths.values()
            )

        self.assertFalse(
            closure_complete(),
            "GOAL INCONCLUSIVE cannot become NO PROGRESS while a known safe bounded evidence path remains",
        )

        paths["bounded-alternate-readback"]["exhausted"] = True
        materially_distinct_correction = True
        self.assertFalse(
            closure_complete(),
            "a newly established in-Scope correction keeps Ralph open even after the evidence path is exhausted",
        )

        materially_distinct_correction = False
        self.assertTrue(closure_complete())

    def test_alternate_representation_diagnoses_reachability_without_replacing_exact_authored_boundary(self) -> None:
        observations = {
            "authored-representation": "unavailable",
            "alternate-representation": "reachable",
        }
        exact_authored_representation_required = True

        dependency_wholly_unavailable = all(value == "unavailable" for value in observations.values())
        authored_outcome_satisfied = (
            observations["authored-representation"] == "reachable"
            if exact_authored_representation_required
            else any(value == "reachable" for value in observations.values())
        )

        self.assertFalse(dependency_wholly_unavailable)
        self.assertFalse(
            authored_outcome_satisfied,
            "an alternate representation may diagnose reachability but cannot silently replace an exact authored representation",
        )

    def test_inflight_work_resolution_does_not_bypass_remaining_closure(self) -> None:
        invocation = {"active": True, "can_still_report": True, "host_stopped": False}
        known_safe_path_remaining = True

        def in_flight() -> bool:
            return invocation["active"] and invocation["can_still_report"] and not invocation["host_stopped"]

        def terminal_no_progress_allowed() -> bool:
            return not in_flight() and not known_safe_path_remaining

        self.assertFalse(terminal_no_progress_allowed())

        invocation.update({"active": False, "can_still_report": False, "host_stopped": True})
        self.assertFalse(
            terminal_no_progress_allowed(),
            "ending an in-flight invocation only removes that liveness blocker; it does not exhaust other evidence paths",
        )

        known_safe_path_remaining = False
        self.assertTrue(terminal_no_progress_allowed())


if __name__ == "__main__":
    unittest.main()
