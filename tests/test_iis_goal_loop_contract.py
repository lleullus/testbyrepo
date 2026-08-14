from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
LOOP = (ROOT / "iis-goal-loop/SKILL.md").read_text(encoding="utf-8")
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
MATT = (ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
TO_TICKETS = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


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

    def test_active_summaries_describe_streaming_evidence_driven_ralph_not_one_ac_dispatch(self) -> None:
        loop = normalized(LOOP)
        readme = normalized(README)
        for required in (
            "act on current in-Scope evidence inside the active Ticket",
            "bounded same-Ticket implementation overlap when it is useful and safe",
            "converge to a settled current product",
        ):
            self.assertIn(required, loop)
        for required in (
            "acts on current in-Scope evidence inside the active Ticket",
            "When timing is left to Ralph, later overlap waits for that first work to settle",
            "An exact user instruction to overlap now overrides that Lead-owned wait/efficiency choice",
            "settled fresh Ticket/whole-Spec verification before completion",
        ):
            self.assertIn(required, readme)
        self.assertNotIn("select one unmet Acceptance Criterion", loop)
        self.assertNotIn("repeatedly selects current unmet Ticket ACs", readme)

    def test_same_ticket_repeats_for_new_in_scope_causes_without_dynamic_ticket_authoring(self) -> None:
        body = normalized(LOOP)
        for required in (
            "newly discovered technical cause does not create a new Ticket",
            "same Ticket Scope",
            "Reinvoke the same Ticket",
            "materially different in-Scope changes",
            "Do not dynamically author a new Ticket inside the loop",
            "Do not widen Ticket authority",
        ):
            self.assertIn(required, body)
        self.assertIn("without inventing a new Ticket, queue, root-cause registry, or other planning state", body)

    def test_settled_active_ticket_is_fully_reobserved_and_final_goal_is_fresh(self) -> None:
        body = normalized(LOOP)
        for required in (
            "While another authorized same-Ticket product/source mutation remains in flight",
            "does not need to stop the useful work merely to perform a full Ticket reobservation after each individual result",
            "all current-Ralph implementation mutation for the active Ticket must finish",
            "earlier Ticket Verification Lead/Runner cycle that overlapped that mutation must have quiesced",
            "every Runner must have returned or been host-confirmed stopped",
            "every Runner-started product effect must have reached its authored terminal/cleanup boundary",
            "Do not start the settled fresh reobservation or a new authoritative verification cycle while an earlier navigation-only Runner or one of its still-running effects can still change the target",
            "reviews the resulting current project as one combined product",
            "settled changes remain inside the Ticket Scope and preserve current user/concurrent changes without an unresolved integration conflict",
            "freshly reobserves every AC of the active Ticket",
            "A regression in a previously satisfied AC becomes current unfinished work immediately",
            "no observation from before or during the mutation interval may be reused",
            "complete ready Ticket set",
            "Only when the complete Ticket set is provisionally satisfied",
            "goal-verification-lead/SKILL.md",
            "Implementation reports, candidate recipes, Ticket checkpoints, tests, prior Runner observations, prior Ticket-verification evidence",
            "navigation hints only",
            "No other result completes the Goal",
        ):
            self.assertIn(required, body)

    def test_ticket_verified_and_tests_cannot_complete_goal(self) -> None:
        body = normalized(LOOP + "\n" + ROUTER)
        for required in (
            "It never completes the parent Goal",
            "`GOAL VERIFIED` permits `GOAL ACHIEVED`",
            "Ticket readiness",
            "passing tests",
            "`VERIFIED` for one Ticket",
            "partial improvement",
        ):
            self.assertIn(required, body)

    def test_no_progress_requires_bounded_evidence_and_correction_closure(self) -> None:
        body = normalized(LOOP)
        for required in (
            "same Ticket + materially unchanged current observations + the same attempted implementation with unchanged inputs",
            "Starting or resuming another Worker does not turn that repetition into progress",
            "invocation-local bounded evidence/correction closure audit",
            "no materially different in-Scope correction",
            "no safe direct observation or authoritative readback still available",
            "no exact operator/environment/authority action that could restore evidence",
            "path is not exhausted merely because its first endpoint, representation, transport, tool, or readback failed",
            "Do not turn this audit into broad repository discovery, arbitrary endpoint hunting, a durable path registry, or a scheduler",
            "Only when the current invocation has an open Goal and that bounded audit closes every such path",
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

    def test_required_inflight_work_blocks_terminal_result_and_user_action_none_keeps_ralph_running(self) -> None:
        body = normalized(LOOP)
        for required in (
            "host-known required Implementation Lead, Implementation Subagent, Verification Lead, Goal Verification Lead, Verification Runner invocation, or Runner-started product effect",
            "still active, waiting for a required current reply, or still capable of producing authorized current evidence/correction is an unexhausted path",
            "nonterminal progress update while such work continues",
            "must not close the current invocation with a Goal result or `GOAL OPEN — NO PROGRESS`",
            "ceases to count as in-flight when it returns, is host-confirmed stopped, or the host establishes that it can no longer produce a current result",
            "Clearing that liveness blocker does not itself authorize a terminal Ralph result",
            "including a fresh replacement invocation or another contract-admitted path when one remains justified",
            "invocation-local host awareness only; do not persist a task registry, queue, or scheduler",
            "`GOAL OPEN — PROGRESSED` is a nonterminal progress report",
            "It is not a handoff of due-now work to the user",
            "When a report says `User Action: None`, Ralph continues executing every remaining authorized evidence/correction path",
            "do not instruct the user to resume later, retry when a dependency recovers, wait for a background task, or perform an unspecified next step",
        ):
            self.assertIn(required, body)

    def test_progress_reporting_keeps_tests_separate_from_direct_completion_evidence(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Keep implementation checks and completion evidence visibly separate",
            "Test/build/lint counts may be reported as implementation checks",
            "never fill `Current direct evidence:` or final `Evidence:`",
            "do not outrank current CLI/product/persistence/rendered/canonical authoritative readback",
            "report the exact evidence limit instead of substituting a passing test count or Worker narration",
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

    def test_explicitly_preserved_predecessor_is_bounded_navigation_not_authority(self) -> None:
        body = normalized(LOOP)
        for required in (
            "approved Scope/Spec/Ticket explicitly says the current work preserves, replaces, rebuilds, or migrates an existing product capability",
            "bounded predecessor implementation and its currently used product boundaries are relevant navigation",
            "before Ralph concludes that an external dependency is unavailable or that no in-Scope correction remains",
            "implementation details, policy, schema, fallback strategy, or historical behavior do not become new product authority",
            "not a license for broad legacy archaeology",
        ):
            self.assertIn(required, body)

    def test_working_observation_is_readback_first_boundary_scoped_and_does_not_duplicate_effects(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Prefer reading an already-current authoritative product state or readback",
            "Failure of one endpoint, representation, transport, tool, or readback establishes only that exact failed boundary",
            "Do not promote it to dependency-wide unavailability",
            "approved contract, current product/config/source, or other current direct evidence",
            "do not invent arbitrary fallbacks or perform broad endpoint discovery",
            "alternate representation may establish that the dependency is reachable or expose candidate integration work",
            "never substitutes for an exact authored endpoint, representation, or readback unless the approved contract permits that equivalence",
            "known usable representation exists but the current product does not support or reach it",
            "candidate current in-Scope product/integration work rather than an external-dependency conclusion",
            "Do not re-run payment, message, deployment, destructive, irreversible",
            "one-shot, or duplicate-sensitive effects",
            "keep the item `UNRESOLVED` or request the exact approved operator action",
        ):
            self.assertIn(required, body)

    def test_every_independent_ticket_including_last_or_only_runs_ticket_verification(self) -> None:
        body = normalized(LOOP)
        for required in (
            "before Ralph treats that Ticket as verified for progression",
            "applies to every such Ticket, including the last or only Ticket immediately before whole-Spec Goal Verification",
            "Goal Verification is not a substitute for this Ticket-level streaming feedback cycle",
            "`VERIFIED` permits Ralph to leave/close the Ticket for navigation only",
            "It never completes the parent Goal",
            "must not prescribe a reduced verification subset, forbid an authored observation on its own authority",
            "its own decision not to attempt a boundary as dependency unavailability",
            "Do not skip required Independent Ticket Verification because the Ticket is the last/only Ticket",
            "Prefer a fresh read of already-current authoritative state/readback",
            "serialize relevant Runner work",
            "accept `INCONCLUSIVE` with the exact environment/operator/authority evidence limit",
            "Do not leap directly to Goal Verification to avoid this cycle",
        ):
            self.assertIn(required, body)
        self.assertNotIn("about to leave it for a different Ticket", body)
        self.assertNotIn("last remaining Ticket and fresh whole-Spec Goal Verification will run immediately", body)

    def test_mutation_overlap_invalidates_whole_ticket_verification_cycle(self) -> None:
        body = normalized(LOOP)
        for required in (
            "whole cycle immediately loses Ticket-progression authority",
            "Still-safe Runner observations may remain navigation",
            "let every Runner from the overlapped cycle return or be host-confirmed stopped",
            "every Runner-started product effect has reached its authored terminal/cleanup boundary",
            "reviews the combined current project",
            "freshly reobserves every AC of the active Ticket",
            "new Verification Lead cycle with fresh Runner invocations",
            "Do not carry forward earlier PASS rows or an earlier aggregate across that mutation boundary",
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
            "terminates only that Goal Verification invocation",
            "not Goal completion, product impossibility, dependency-wide unavailability",
            "Ralph immediately re-enters current bounded resolution",
            "another currently known contract-admitted authoritative readback/direct observation",
            "Only the exact owning gate may stop further automatic work",
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

    def test_same_ticket_roles_are_bounded_and_never_carry_authority(self) -> None:
        body = normalized(LOOP)
        for required in (
            "host-provided invocation-local `Implementation Subagent` roles for the currently active Ticket",
            "more than one same-Ticket Implementation Lead invocation active",
            "Ordered Implementation Subagent bindings are reusable dispatch precedence, not one-use tokens",
            "highest-priority currently eligible binding that is not already occupied by useful in-flight work",
            "A returned invocation makes its binding eligible again",
            "freshly reinvoke the same higher-priority binding rather than silently advancing the authored order",
            "default Lead-owned scheduling",
            "useful critical-path benefit that is not outweighed by coordination, duplication, or edit-contention cost",
            "exact current user instruction to start another implementation invocation now or before the first returns",
            "Do not use Lead-owned efficiency or coordination preference to silently serialize an exact user-fixed immediate overlap",
            "Except for properties the user explicitly fixed, the exact number, timing, and technical allocation of invocations remain implementation-owned",
            "Scheduling repair is prospective",
            "a role may be resumed for later materially different work",
            "retained context remains bounded, relevant, and likely to reduce technical rediscovery",
            "every Implementation Lead entry must freshly revalidate",
            "never remain current merely because a role context was resumed or another same-Ticket role is already active",
            "assignment ledger",
            "Never resume an implementation role across a Ticket change",
            "entry into whole-Spec Goal Verification",
            "`GOAL OPEN — NO PROGRESS`",
        ):
            self.assertIn(required, body)

    def test_user_designated_implementation_roles_keep_binding_and_consumption_timing(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Role-First Invocation Dispatch",
            "resolve the IIS role required by the current protocol step",
            "Restrict current-conversation bindings to that role",
            "Never choose an assignee first and reinterpret its role",
            "Implementation Lead receives `Implementation Subagent`",
            "Verification Lead and Goal Verification Lead receive only `Verification Runner` bindings",
            "current-conversation `Implementation Subagent` role bindings, reservations, ordering, consumption timing, or concurrency limits",
            "pre-consume a role the user reserved for a later correction",
            "A separate user designation is required when the same configured model/agent is to serve a different IIS role",
            "Except for properties the user explicitly fixed",
            "give the observation to that existing invocation first",
            "Do not open a duplicate invocation or consume another user-reserved implementation role merely because the finding arrived separately",
            "not defect/AC/file ownership",
            "does not erase a still-current user role designation",
            "must not treat the prior invocation's technical context or source facts as current",
        ):
            self.assertIn(required, body)

    def test_implementation_input_is_current_navigation_not_new_authority(self) -> None:
        body = normalized(LOOP)
        for required in (
            "current direct observations relevant to the in-Scope work being attempted",
            "current preservation or regression observations when materially relevant",
            "current observations that justify implementation are navigation only",
            "do not add, strengthen, split, or reorder Ticket authority",
            "Do not serialize the working observations",
            "gap registry",
        ):
            self.assertIn(required, body)

    def test_shared_acquisition_never_weakens_settled_post_mutation_reobservation(self) -> None:
        body = normalized(LOOP)
        for required in (
            "acquire that shared boundary once and classify each linked AC separately",
            "authored flows actually use that same trigger/input, relevant state",
            "Distinct inputs, states, branches, lifecycle boundaries, or readbacks remain distinct acquisitions",
            "do not infer equivalence merely because the ACs concern nearby product behavior",
            "no combined AC verdict",
            "Any product/source mutation after the acquisition invalidates it",
            "settled post-mutation reobservation",
            "one fresh execution/readback may decide several linked AC observations",
            "every AC remains separately classified",
            "no observation from before or during the mutation interval may be reused",
        ):
            self.assertIn(required, body)

    def test_runner_finding_can_stream_to_ralph_without_waiting_for_other_runners(self) -> None:
        body = normalized(LOOP)
        for required in (
            "Verification Lead forwards a qualifying current finding from a fresh Runner before the cycle finishes",
            "immediately act on it under steps 2 and 3",
            "instead of waiting for the remaining Runner assignments or final aggregate",
            "Other still-safe Runner observations may continue",
            "Verification Lead may forward additional qualifying findings",
            "Only Ralph decides whether a finding justifies same-Ticket implementation or belongs at an operator, environment, or authority gate",
            "only Ralph decides whether and when to invoke more same-Ticket implementation within the user's role bindings and consumption conditions",
            "instead of consuming another reserved role merely because a separate Runner found it",
            "Neither Runner nor Verification Lead dispatches mutation or remediates product code itself",
        ):
            self.assertIn(required, body)

    def test_loop_has_no_controller_runtime_or_durable_orchestration_state(self) -> None:
        body = normalized(LOOP + "\n" + ROUTER).lower()
        for prohibited in (
            "controller runtime",
            "workflow database",
            "dispatch queue",
            "worker/assignment ledger",
            "attempt ledger",
            "replay engine",
            "claim/capability registry",
            "persistent queue",
            "stored scheduler",
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
