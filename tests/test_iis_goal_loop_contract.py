from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
LOOP = (ROOT / "iis-goal-loop/SKILL.md").read_text(encoding="utf-8")
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
MATT = (ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
TO_TICKETS = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class IISGoalLoopContractTests(unittest.TestCase):
    def test_loop_uses_spec_and_complete_ready_ticket_set_as_fixed_contract(self) -> None:
        body = normalized(LOOP)
        for required in (
            "one exact absolute canonical `Status: approved` Spec",
            "canonical sibling Ticket set",
            "validate_ticket_set.py",
            "The approved Spec remains the product Goal authority",
            "Each ready Ticket is a delivery unit, not an implementation attempt",
            "Behavior is the semantic guardrail; ACs are the observable work queue",
            "Parent outcome ordinal",
            "Behavior authority ordinals",
            "positional locators only and never durable identity",
        ):
            self.assertIn(required, body)

    def test_same_ticket_repeats_for_new_in_scope_causes_without_dynamic_ticket_authoring(self) -> None:
        body = normalized(LOOP)
        for required in (
            "newly discovered technical cause does not create a new Ticket",
            "same Ticket Scope",
            "Reinvoke the same Ticket",
            "materially different in-Scope corrections",
            "Do not dynamically author a new Ticket inside the loop",
            "Do not widen Ticket authority",
        ):
            self.assertIn(required, body)
        self.assertIn("Do not create a root-cause queue or dynamic gap taxonomy", body)

    def test_every_implementation_reobserves_active_ticket_and_final_goal_is_fresh(self) -> None:
        body = normalized(LOOP)
        for required in (
            "After every implementation result, freshly reobserve every AC of the active Ticket",
            "A regression in a previously satisfied AC becomes current unfinished work immediately",
            "complete ready Ticket set",
            "Only when the complete Ticket set is provisionally satisfied",
            "goal-verification-lead/SKILL.md",
            "Implementation reports, candidate recipes, Ticket checkpoints, tests, prior observations",
            "navigation hints only",
            "No other result completes the Goal",
        ):
            self.assertIn(required, body)

    def test_ticket_verified_and_tests_cannot_complete_goal(self) -> None:
        body = normalized(LOOP + "\n" + ROUTER)
        for required in (
            "Ticket-level checkpoint never completes the parent Goal",
            "`GOAL VERIFIED` permits `GOAL ACHIEVED`",
            "Ticket readiness",
            "passing tests",
            "`VERIFIED` for one Ticket",
            "partial improvement",
        ):
            self.assertIn(required, body)

    def test_no_progress_is_invocation_circuit_breaker_not_goal_impossibility(self) -> None:
        body = normalized(LOOP)
        for required in (
            "same Ticket + same unmet AC set + same direct observation + same correction",
            "That is not Ralph progress",
            "`GOAL OPEN — NO PROGRESS`",
            "circuit breaker for the current attempt, not a claim that the Goal is impossible",
            "later invocation starts from the same approved Spec, validated Ticket set, and fresh current product state",
        ):
            self.assertIn(required, body)

    def test_user_is_not_made_internal_workflow_operator(self) -> None:
        body = normalized(LOOP + "\n" + ROUTER)
        for required in (
            "Do not ask the user whether to continue between iterations",
            "Do not ask the user which endpoint, parser, fallback, retry policy",
            "Do not ask the user for implementation mechanics",
            "ask the user only for a real product, Scope, completion-contract, or dangerous-authority decision",
        ):
            self.assertIn(required, body)

    def test_planning_leaves_still_stop_and_router_alone_reuses_end_to_end_intent(self) -> None:
        matt = normalized(MATT)
        tickets = normalized(TO_TICKETS)
        router = normalized(ROUTER)
        self.assertIn("After ready Tickets exist, stop the Matt flow", matt)
        self.assertIn("Ask Matt itself never invokes Implementation Lead, the Ralph loop", matt)
        self.assertIn("To Tickets itself never asks for or suggests a Worker", tickets)
        self.assertIn("To Tickets does not gain orchestration or implementation authority", tickets)
        self.assertIn("router may enter the Ralph loop without asking the user to say \"continue\"", router)
        self.assertIn("If the user requested planning only, do not enter Ralph", router)

    def test_explicit_leaf_requests_take_precedence_over_broad_goal_routing(self) -> None:
        body = normalized(ROUTER)
        self.assertIn("Apply explicit leaf requests before broad IIS inference", body)
        self.assertIn("Do not silently convert an explicit one-Ticket implementation request into Ralph Goal fulfillment", body)
        self.assertIn("This is verification only", body)
        self.assertIn("Explicit leaf semantics stay valid and take precedence", body)

    def test_ralph_admission_requires_a_completable_spec_before_mutation(self) -> None:
        body = normalized(LOOP)
        for required in (
            "`--require-completable`",
            "`Not independently verifiable`",
            "stop before mutation",
            "establish an Independent acceptance path",
            "approve an Operator-assisted action/readback",
        ):
            self.assertIn(required, body)

    def test_working_observation_is_readback_first_and_does_not_duplicate_effects(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Prefer reading an already-current authoritative product state or readback",
            "Do not re-run payment, message, deployment, destructive, irreversible",
            "one-shot, or duplicate-sensitive effects",
            "keep the item `UNRESOLVED` or request the exact approved operator action",
        ):
            self.assertIn(required, body)

    def test_independent_ticket_transition_checkpoint_is_default_but_not_ceremony(self) -> None:
        body = normalized(LOOP)
        for required in (
            "default transition checkpoint",
            "`VERIFIED` permits moving to another Ticket",
            "`FAILED` returns to the same Ticket",
            "last remaining Ticket and fresh whole-Spec Goal Verification will run immediately",
            "materially duplicate an unsafe/non-repeatable effect",
        ):
            self.assertIn(required, body)

    def test_final_non_pass_requires_exact_obligation_and_current_ownership(self) -> None:
        body = normalized(LOOP)
        for required in (
            "exact failed obligation",
            "Ticket/Verification-flow/AC ownership",
            "exact `None` when no ready Ticket owns",
            "`None` returns to ordinary Ticket planning",
            "exact evidence-limited obligation",
        ):
            self.assertIn(required, body)

    def test_ralph_completion_is_bounded_to_one_spec_not_parent_initiative(self) -> None:
        body = normalized(LOOP + "\n" + ROUTER)
        for required in (
            "exactly one bounded approved Spec",
            "must never be promoted to completion of a parent Scope Shaper initiative",
            "must not promote that package's `GOAL ACHIEVED` to completion of the parent initiative",
            "Do not invent fan-in orchestration",
        ):
            self.assertIn(required, body)

    def test_ralph_rejects_semantically_stale_ready_ticket_before_mutation(self) -> None:
        body = normalized(LOOP)
        for required in (
            "revalidate the current Spec-to-Ticket semantic projection before mutation",
            "rather than a previously approved meaning at the same work path",
            "reject any remaining semantic stale projection",
            "Return that Ticket to ordinary To Tickets review",
            "unchanged `Status: ready` keeps it current",
        ):
            self.assertIn(required, body)

    def test_loop_has_no_controller_runtime_or_durable_orchestration_state(self) -> None:
        body = normalized(LOOP + "\n" + ROUTER).lower()
        for prohibited in (
            "controller runtime",
            "workflow database",
            "attempt ledger",
            "replay engine",
            "claim/capability registry",
            "persistent queue",
            "generic dsl",
        ):
            self.assertIn(prohibited, body)
        self.assertFalse((ROOT / "iis-controller").exists())
        for path in (
            ROOT / "iis-goal-loop/state",
            ROOT / "iis-goal-loop/runtime",
            ROOT / "iis-goal-loop/tools",
        ):
            self.assertFalse(path.exists(), path)


if __name__ == "__main__":
    unittest.main()
