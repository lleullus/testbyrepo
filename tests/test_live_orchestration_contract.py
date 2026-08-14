from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
LOOP = (ROOT / "iis-goal-loop/SKILL.md").read_text(encoding="utf-8")
IMPLEMENTATION = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")
GOAL_VERIFICATION = (ROOT / "goal-verification-lead/SKILL.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class LiveOrchestrationContractTests(unittest.TestCase):
    def test_orchestration_is_live_and_event_driven_without_repeated_context_rechecks(self) -> None:
        body = normalized(ROUTER + "\n" + LOOP)
        for required in (
            "Do not freeze IIS orchestration",
            "When a new user orchestration instruction or coherent canonical IIS change is actually observed",
            "apply only the material scheduling delta",
            "If no new instruction or contract change is observed, continue without a new orchestration checkpoint",
            "Do not poll or re-read the full conversation at every control boundary",
            "If the host knows a newer direction exists but cannot observe its content",
            "block only the affected new dispatch, mutation authorization, or progression decision",
            "Invocation start does not freeze an older scheduling contract",
        ):
            self.assertIn(required, body)

    def test_live_orchestration_does_not_smuggle_product_contract_changes(self) -> None:
        body = normalized(ROUTER + "\n" + LOOP + "\n" + IMPLEMENTATION)
        for required in (
            "This live reconciliation changes orchestration, not product meaning",
            "Outcome, Scope, Non-Goals, Behavior/UI meaning",
            "return to the owning planning authority",
            "Do not reinterpret a product-contract delta as implementation scheduling",
            "A live product-contract change is not implementation scheduling",
        ):
            self.assertIn(required, body)

    def test_inflight_role_reconciliation_is_prospective_and_minimizes_context_disruption(self) -> None:
        body = normalized(ROUTER + "\n" + LOOP)
        for required in (
            "treat the correction prospectively",
            "Do not undo completed mutation or restart already-satisfied work merely to make history match",
            "If continuing an in-flight invocation would itself violate an exact current user instruction",
            "stop assigning it new duties",
            "Otherwise let its current bounded action return",
            "reapply the current user-authored ordering to the next dispatch",
            "Before progression that depends on affected mutation",
            "combined current product must be freshly reobserved",
        ):
            self.assertIn(required, body)

    def test_first_implementation_is_single_unless_newer_explicit_user_direction_changes_it(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Unless a newer explicit user orchestration direction expressly changes the initial schedule",
            "first implementation dispatch for an active Ticket starts exactly one Implementation Lead invocation",
            "Lead receives exactly one admitted `Implementation Subagent`",
            "Do not fan out the first implementation merely because multiple bindings are available",
            "Ticket is broad or greenfield",
            "maximum concurrency greater than one is allowed",
        ):
            self.assertIn(required, body)

    def test_role_count_and_max_concurrency_are_capacity_not_mandatory_consumption(self) -> None:
        body = normalized(LOOP + "\n" + VERIFICATION + "\n" + GOAL_VERIFICATION)
        for required in (
            "maximum-concurrency value is capacity, not mandatory consumption",
            "Available Runner bindings and a maximum concurrency are capacity, not mandatory consumption",
            "Available Runner bindings and maximum concurrency are capacity, not mandatory consumption",
            "unless the user separately fixed exact consumption",
        ):
            self.assertIn(required, body)

    def test_default_later_parallelism_waits_for_first_return_but_exact_user_overlap_can_release_only_that_time_barrier(self) -> None:
        body = normalized(LOOP)
        for required in (
            "When the user has not fixed an earlier overlap time, wait for that first Implementation Lead invocation to return",
            "freshly reobserve the affected current product/Ticket boundaries",
            "An exact current user instruction to start another implementation invocation now or before the first returns overrides only this default wait",
            "A maximum-concurrency increase, additional eligible binding, or general permission for parallelism is not by itself an immediate-overlap instruction",
            "Do not use Lead-owned efficiency or coordination preference to silently serialize an exact user-fixed immediate overlap",
            "give the observation to that existing invocation first",
        ):
            self.assertIn(required, body)

    def test_ordered_implementation_bindings_are_reusable_precedence_not_one_shot_slots(self) -> None:
        body = normalized(LOOP + "\n" + IMPLEMENTATION)
        for required in (
            "Ordered Implementation Subagent bindings are reusable dispatch precedence, not one-use tokens",
            "reapply the authored order from the top",
            "A returned invocation makes its binding eligible again",
            "do not advance to a lower-priority binding merely because a higher-priority binding was used earlier",
            "Context resumption and binding eligibility are separate decisions",
            "freshly reinvoke the same higher-priority binding",
            "one-shot use, a usage limit, rotation",
            "another eligibility-ending condition",
        ):
            self.assertIn(required, body)

    def test_scheduling_repair_is_prospective_not_ceremonial_replay(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Scheduling repair is prospective",
            "product-authorized mutation produced by an otherwise eligible implementation binding that was selected at the wrong authored order or timing",
            "remains current product state",
            "Do not roll it back, repeat the same correction, or reassign that completed correction merely to reconstruct the preferred historical role order",
            "Freshly reobserve the combined current product",
            "only genuinely unfinished current in-Scope work is eligible for a new implementation dispatch",
            "does not preserve Scope-exceeding, wrong-role, unauthorized-dangerous-effect, or user-explicitly-rejected mutation",
        ):
            self.assertIn(required, body)

    def test_observed_scheduling_delta_is_sent_once_as_delta_only_to_affected_active_roles(self) -> None:
        body = normalized(ROUTER + "\n" + LOOP + "\n" + IMPLEMENTATION)
        for required in (
            "send exactly one concise delta-only update to each affected active role",
            "changed scheduling fact",
            "effective boundary",
            "Ticket, Scope, AC, Behavior/UI, and unchanged user intent remain unchanged",
            "Do not resend the full conversation, closed scheduling history, or unaffected authority",
            "Unrelated active roles receive no update",
        ):
            self.assertIn(required, body)

    def test_exact_immediate_overlap_conflict_is_reported_not_silently_serialized(self) -> None:
        body = normalized(LOOP)
        for required in (
            "ORCHESTRATION CONFLICT",
            "Instruction: <exact user-authored immediate-overlap instruction>",
            "Concrete conflict: <unavailable exact binding | no in-Scope unfinished work to assign | incompatible current mutation | conflicting user instruction | missing required authority>",
            "Preserved work: <current work that may continue without violating the instruction>",
            "Lead-owned efficiency or coordination preference is never a conflict reason",
        ):
            self.assertIn(required, body)

    def test_one_implementation_lead_never_fans_out_multiple_subagents_or_rechecks_full_context_without_delta(self) -> None:
        body = normalized(IMPLEMENTATION)
        for required in (
            "One Implementation Lead invocation consumes at most one admitted `Implementation Subagent`",
            "never authorize this Lead to fan out additional Subagents",
            "uses separate Implementation Lead invocations",
            "each with its own one admitted Subagent",
            "Do not independently re-read the full user conversation before every Subagent call or mutation",
            "caller/host actually reports a newer orchestration delta",
            "keep the admitted binding without adding a freshness ceremony",
            "host explicitly knows a newer direction exists but cannot provide enough",
            "return control before the affected new mutation",
        ):
            self.assertIn(required, body)

    def test_ticket_verification_invalidates_only_for_material_evidence_or_role_authority_delta(self) -> None:
        body = normalized(VERIFICATION)
        for required in (
            "A scheduling change alone does not invalidate a Ticket Verification cycle",
            "Invalidate the cycle only when a newly observed change affects product/source state, authored coverage, currentness, attribution, role authority already used by the cycle, or target/effect safety",
            "whole Lead/Runner cycle loses Ticket-progression authority",
            "A future implementation-role order or concurrency change unrelated to this cycle does not invalidate it",
            "Stop assigning new work to a withdrawn or newly ineligible Runner",
            "obtains whatever fresh authoritative observation that path requires",
            "Do not carry forward an earlier PASS row or aggregate across a mutation-invalidated cycle",
        ):
            self.assertIn(required, body)

    def test_goal_verification_invalidates_only_for_material_final_evidence_or_role_authority_delta(self) -> None:
        body = normalized(GOAL_VERIFICATION)
        for required in (
            "A scheduling change alone does not invalidate a Goal Verification cycle",
            "Invalidate final authority only when a newly observed change affects product/source state, final coverage, currentness, attribution, role authority already used by the cycle, or target/effect safety",
            "same loss of final progression authority applies",
            "A future implementation-role order or concurrency change unrelated to final observation does not invalidate the cycle",
            "materially superseded Runner whose effect or evidence is part of the invalidated boundary must return or be host-confirmed stopped",
            "new fresh Runner invocations only after quiescence and only under the current contract",
        ):
            self.assertIn(required, body)

    def test_prospective_runner_withdrawal_preserves_already_valid_evidence(self) -> None:
        body = normalized(VERIFICATION + "\n" + GOAL_VERIFICATION)
        for required in (
            "A prospective Runner withdrawal or future-assignment change does not retroactively invalidate evidence obtained while that Runner was validly admitted",
            "Retain that evidence when product/source currentness, coverage, attribution, target/effect safety, and the user's instruction do not reject the already-obtained observation",
            "Invalidate prior evidence only when the user explicitly rejects that prior observation, the Runner was never eligible for that role, or one of those evidence-meaning conditions changed",
        ):
            self.assertIn(required, body)

    def test_independent_ticket_avoids_double_full_ac_acquisition_before_ticket_verification(self) -> None:
        body = normalized(LOOP)
        for required in (
            "For an all-`Independent` Ticket that will enter Ticket Verification, do not perform a second Ralph full-AC product acquisition merely to pre-screen the verifier",
            "Verification Lead becomes the first settled fresh full-AC observer after mutation quiescence",
            "Ralph performs only a lightweight current integration and authority preflight",
            "Mixed or non-independent Tickets retain Ralph fresh AC reobservation because no Ticket Verification Lead can adjudicate those flows",
        ):
            self.assertIn(required, body)

    def test_last_or_only_independent_ticket_can_go_directly_to_goal_verification(self) -> None:
        body = normalized(LOOP)
        for required in (
            "When the active Ticket is the last or only unfinished Ticket",
            "skip a separate post-mutation Ticket Verification cycle and enter fresh whole-Spec Goal Verification directly",
            "unless the user explicitly requested a separate Ticket-level verdict",
            "Goal Verification is the first settled independent full observation for that last/only Ticket and still returns exact candidate Ticket/flow/AC ownership on non-PASS",
            "This optimization never skips Ticket Verification for an earlier Ticket that Ralph must leave before the Goal-final boundary",
        ):
            self.assertIn(required, body)

    def test_invalidated_streaming_verification_does_not_finish_navigation_for_ceremony(self) -> None:
        body = normalized(LOOP + "\n" + VERIFICATION)
        for required in (
            "After mutation invalidates Ticket-progression authority, do not create new Runner assignments merely to finish the invalidated cycle's old coverage or roster",
            "already-active Runner observation may continue only when it can still materially surface a distinct current correction or the user explicitly required that continued observation",
            "otherwise request stop at the next host-controllable boundary",
            "already-started product effects still reach their authored terminal/cleanup boundary",
        ):
            self.assertIn(required, body)

    def test_implementation_checks_do_not_pre_run_full_independent_verification_matrix(self) -> None:
        body = normalized(IMPLEMENTATION)
        for required in (
            "Implementation-stage checks are a minimum focused liveness/integration gate, not a rehearsal of independent verification",
            "Do not execute the complete authored browser, viewport, state, lifecycle, or AC matrix merely to pre-prove the Ticket before Verification Lead or Goal Verification Lead runs",
            "Exercise only the changed materially distinct routes and the minimum representative rendered/runtime conditions needed to catch an obvious broken integration",
            "Full authored verification coverage remains with the later verification authority",
        ):
            self.assertIn(required, body)

    def test_partial_or_conflicting_canonical_update_fails_closed_for_affected_dispatch(self) -> None:
        body = normalized(ROUTER)
        for required in (
            "canonical IIS update is partially applied or internally conflicting",
            "fail closed only on new dispatch/progression",
            "until a coherent current contract can be read",
            "do not choose whichever old or new rule is more convenient",
        ):
            self.assertIn(required, body)


if __name__ == "__main__":
    unittest.main()
