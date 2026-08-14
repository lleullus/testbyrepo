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
    def test_orchestration_is_live_at_control_boundaries_not_frozen_at_invocation_start(self) -> None:
        body = normalized(ROUTER + "\n" + LOOP)
        for required in (
            "Do not freeze IIS orchestration",
            "latest explicit current-conversation user direction",
            "current canonical IIS contract",
            "new downstream role invocation",
            "new product/source mutation authorization",
            "verification-cycle start or progression decision",
            "whole-Spec Goal Verification",
            "user-facing completion result",
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

    def test_inflight_role_reconciliation_respects_new_user_scheduling_and_quiescence(self) -> None:
        body = normalized(ROUTER + "\n" + LOOP)
        for required in (
            "withdraws an active role or reduces allowed concurrency below the current in-flight set",
            "stop assigning affected roles new work",
            "Honor an explicitly user-selected role to retain",
            "earliest safe host-controllable boundary",
            "all affected mutation and product effects must quiesce",
            "combined current product must be freshly reobserved",
            "has no progression authority merely because it began under an older contract",
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

    def test_later_parallel_implementation_requires_initial_return_quiescence_fresh_evidence_and_tradeoff(self) -> None:
        body = normalized(LOOP)
        for required in (
            "After that first Implementation Lead invocation returns and its mutation is quiescent",
            "freshly reobserve the affected current product/Ticket boundaries",
            "fresh current evidence then shows materially distinct remaining in-Scope work",
            "more than one same-Ticket Implementation Lead invocation active",
            "accounts for the useful work already known to be in flight",
            "does not knowingly duplicate materially the same implementation work",
            "coordination, duplication, or edit-contention cost outweighs the useful critical path overlap",
            "safe beneficial non-duplicative overlap is unclear, serial execution is the fallback",
            "give the observation to that existing invocation first",
        ):
            self.assertIn(required, body)

    def test_one_implementation_lead_never_fans_out_multiple_subagents(self) -> None:
        body = normalized(IMPLEMENTATION)
        for required in (
            "One Implementation Lead invocation consumes at most one admitted `Implementation Subagent`",
            "never authorize this Lead to fan out additional Subagents",
            "uses separate Implementation Lead invocations",
            "each with its own one admitted Subagent",
            "latest explicit user orchestration direction and current canonical IIS contract",
            "return control without consuming the stale admission",
        ):
            self.assertIn(required, body)

    def test_ticket_verification_live_material_delta_invalidates_progression_but_wording_only_does_not(self) -> None:
        body = normalized(VERIFICATION)
        for required in (
            "Before each new Runner assignment and again before using the cycle for Ticket progression",
            "Invocation start does not freeze an older Runner roster",
            "live user/canonical IIS change materially changes Runner eligibility",
            "coverage, attribution, or effect safety",
            "whole Lead/Runner cycle loses Ticket-progression authority",
            "wording-only or other orchestration change that cannot affect coverage, currentness, attribution, safety, or the progression decision does not invalidate the cycle",
            "Stop assigning new work to a withdrawn or newly ineligible Runner",
            "fresh Runner invocations under the current contract",
            "Do not carry forward an earlier PASS row or aggregate",
        ):
            self.assertIn(required, body)

    def test_goal_verification_live_material_delta_invalidates_final_authority_and_requires_fresh_cycle(self) -> None:
        body = normalized(GOAL_VERIFICATION)
        for required in (
            "Before each new final Runner assignment and again before returning the Goal aggregate",
            "Invocation start does not freeze an older Runner roster",
            "live user/canonical IIS change materially changes final Runner eligibility",
            "same loss of final progression authority applies",
            "wording-only or other orchestration change that cannot affect final coverage, currentness, attribution, safety, or aggregate does not invalidate the cycle",
            "materially superseded Runner must return or be host-confirmed stopped",
            "new fresh Runner invocations only after quiescence and only under the current contract",
        ):
            self.assertIn(required, body)

    def test_partial_or_conflicting_canonical_update_fails_closed_for_affected_dispatch(self) -> None:
        body = normalized(ROUTER)
        for required in (
            "canonical IIS update is partially applied or internally conflicting",
            "fail closed on new dispatch/progression",
            "until a coherent current contract can be read",
            "do not choose whichever old or new rule is more convenient",
        ):
            self.assertIn(required, body)


if __name__ == "__main__":
    unittest.main()
