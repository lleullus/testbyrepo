from __future__ import annotations

import re
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
SKILL = (IMPLEMENTATION_ROOT / "SKILL.md").read_text(encoding="utf-8")
FAILURE_ROUTING = (IMPLEMENTATION_ROOT / "references/implementation-failure-routing.md").read_text(
    encoding="utf-8"
)
TASK_OWNERSHIP = (IMPLEMENTATION_ROOT / "references/task-ownership.md").read_text(encoding="utf-8")
PLANNING_CURRENTNESS = (
    IMPLEMENTATION_ROOT / "references/planning-input-currentness.md"
).read_text(encoding="utf-8")
PLANNING_TICKET = (IMPLEMENTATION_ROOT / "references/planning-ticket.md").read_text(encoding="utf-8")
TO_TICKETS = (IMPLEMENTATION_ROOT.parent / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")


class ImplementationSkillContractTests(unittest.TestCase):
    def test_adapter_native_mechanics_are_absent(self) -> None:
        forbidden = [
            r"\bNode\b",
            r"\bPython\b",
            r"\bGo\b",
            r"nativeReport",
            r"contextDigest",
            r"adapterVersion",
            r"references/adapters",
            r"adapters/node",
            r"adapters/python",
            r"adapters/go",
            r"per-task Fast",
            r"Full entry",
        ]
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, SKILL), pattern)

    def test_run_state_is_implementation_only(self) -> None:
        for state in (
            "PREFLIGHT",
            "IMPLEMENTING",
            "RECONCILING",
            "FINAL_REVIEW",
            "IMPLEMENTATION_COMPLETE",
            "INCOMPLETE",
            "BLOCKED",
            "PENDING",
            "WORKER_RUNNING",
            "REVIEWING",
            "IMPLEMENTED",
        ):
            self.assertIn(state, SKILL)
        for removed in (
            "READY_FOR_VERIFICATION",
            "verificationSessionId",
            "verificationResultId",
            "verificationVerdict",
            "currentnessResult",
            "checkpointHistoryRefs",
            "ImplementationHandoff",
            "assertCurrent",
            "RUNTIME_EXERCISE",
            "runtimeExercise",
            "targetBinding",
            "implementation-result-v3",
        ):
            self.assertNotIn(removed, SKILL)

    def test_attribution_and_scope_states_are_not_conflated(self) -> None:
        self.assertIn("`attributionState` is `UNASSESSED`, `RECONCILING`, `CLEAR`, or `BLOCKED`", SKILL)
        self.assertIn("A scope comparison never sets\nit directly", SKILL)
        self.assertIn("`scopeComparisonState` is the tool-reported", SKILL)
        self.assertIn("it does not\nclaim that the actor of every disjoint external path is known", SKILL)

    def test_first_worker_requires_baseline_capsule_not_verification_lead(self) -> None:
        self.assertIn("../baseline-capsule/baseline_capsule.py create", SKILL)
        self.assertIn("canonical physical directory containing this `SKILL.md`", SKILL)
        self.assertIn("Never search for or substitute another same-named Baseline Capsule copy", SKILL)
        self.assertIn("Immediately before dispatching the first\nWorker", SKILL)
        self.assertIn("require exact equality with\n`baselineSourceIdentity`", SKILL)
        self.assertIn("Do not invoke Verification Lead from this skill", SKILL)

    def test_capsule_failure_prevents_worker_dispatch(self) -> None:
        self.assertIn("no Worker may run after a terminal result", SKILL)
        self.assertIn("missing or expired Capsules are never silently replaced", SKILL)
        self.assertIn("For a genuine zero-source-mutation Ticket path, create the Capsule", SKILL)

    def test_zero_source_mutation_runtime_coverage_has_an_executable_path(self) -> None:
        self.assertIn("proceed directly to\n`FINAL_REVIEW` only when every Acceptance Criterion is already `ESTABLISHED`", SKILL)
        self.assertIn("If required\nruntime-dependent coverage remains `PARTIAL`, enter `IMPLEMENTING`", SKILL)
        self.assertIn("dispatch the same check as a run-scoped\nexception while `currentTaskId` remains empty", SKILL)
        self.assertIn("create no TaskState or task record", SKILL)
        self.assertIn("confirming a valid empty ownership delta", SKILL)

    def test_implemented_is_source_review_not_verification(self) -> None:
        self.assertIn("task_implementation_review_complete", SKILL)
        self.assertIn("does not claim a separate\ntechnical verification verdict", SKILL)
        self.assertIn("Implementation completion and Acceptance Criterion coverage", SKILL)

    def test_runtime_dependent_coverage_requires_direct_product_evidence(self) -> None:
        self.assertIn("criterion remains `PARTIAL` after source integration", SKILL)
        self.assertIn("representative runtime exercise observes its expected effect", SKILL)
        self.assertIn("authoritative product readback", SKILL)
        self.assertIn("internal-helper call alone is not\nthat evidence", SKILL)
        self.assertIn("source artifact, static schema,\ndocument, or structural constraint", SKILL)

    def test_runtime_exercise_reuses_existing_task_flow(self) -> None:
        self.assertIn("focused Worker check, not a RunState or an evidence-only task", SKILL)
        self.assertIn("without creating an evidence-only task", SKILL)
        self.assertIn("for a no-mutation focused check with an empty mutation envelope", SKILL)
        self.assertIn("bounded remediation or no-mutation focused check", SKILL)
        self.assertIn("One exercise may support multiple criteria", SKILL)

    def test_runtime_evidence_reopens_affected_work_and_carries_forward_only_when_safe(self) -> None:
        self.assertIn("Affected runtime-dependent coverage returns to `PARTIAL`", SKILL)
        self.assertIn("Do not rerun an exercise solely because an\nunrelated change altered the physical source identity", SKILL)
        self.assertIn("affected task to `REVIEWING`", SKILL)
        self.assertIn("re-enter `IMPLEMENTING`", SKILL)

    def test_runtime_failures_distinguish_product_environment_and_authority(self) -> None:
        self.assertIn("expected effect that is absent", FAILURE_ROUTING)
        self.assertIn("Ticket-authorized defect attributable to the task", FAILURE_ROUTING)
        self.assertIn("Without an authoritative readback, the runtime-dependent Acceptance Criterion remains `PARTIAL`", FAILURE_ROUTING)
        self.assertIn("reliable target-to-source binding is\n  `INCOMPLETE`", FAILURE_ROUTING)
        self.assertIn("Unclear target authority, an unapproved external effect", FAILURE_ROUTING)
        self.assertIn("A project delta during a no-mutation focused check", FAILURE_ROUTING)

    def test_runtime_safety_and_ticket_observability_are_explicit(self) -> None:
        self.assertIn("Prefer the current checkout with task-owned local or temporary state", SKILL)
        self.assertIn("without safe cleanup is not a safe target", SKILL)
        self.assertIn("Do not automatically use production, real money, real messages, user data", SKILL)
        self.assertIn("explicit user authorization for this invocation", SKILL)
        self.assertIn("observable product flow, expected effect, and readback", TO_TICKETS)
        self.assertIn("A separate Verification Lead owns an\nindependent technical verification verdict", TO_TICKETS)
        self.assertIn("but does not itself add a\npositive completion condition", PLANNING_TICKET)

    def test_final_review_binds_two_equal_source_identities(self) -> None:
        self.assertIn("finalReviewStartIdentity", SKILL)
        self.assertIn("finalSourceIdentity", SKILL)
        self.assertIn("Require exact equality between both final-review identities after any permitted restart", SKILL)

    def test_unexpected_delta_is_reconciled_before_terminal_routing(self) -> None:
        self.assertIn("change is evidence to reconcile", SKILL)
        self.assertIn("Continue automatically when the unexpected delta is external or remains unattributed", SKILL)
        self.assertIn("Record `CONTINUE` only when", SKILL)
        self.assertIn("Record `REMEDIATE` only for", SKILL)

    def test_blocked_is_reserved_for_authority_overlap_or_preservation_loss(self) -> None:
        self.assertIn("Return `BLOCKED` only when planning authority changed", SKILL)
        self.assertIn("pre-existing work was overwritten", SKILL)

    def test_other_scratch_work_is_not_automatically_blocking(self) -> None:
        self.assertIn("Another `.scratch/<work-slug>/**` tree is not automatically safe or unsafe", SKILL)
        self.assertIn("Do not globally exclude `.scratch/**`", SKILL)

    def test_reconciled_external_changes_are_auditable_and_not_completion_evidence(self) -> None:
        self.assertIn("Each reconciled external-change record contains", SKILL)
        self.assertIn("preservationBeforeIdentity, preservationAfterIdentity", SKILL)
        self.assertIn("excludedFromCoverage = true", SKILL)
        self.assertIn("must not infer an actor from path spelling", SKILL)

    def test_scope_remediation_cannot_launder_an_out_of_envelope_delta(self) -> None:
        self.assertIn("does not retroactively\nmake the original out-of-envelope delta valid task evidence", SKILL)
        self.assertIn("Never use remediation to retain\nan unplanned path", SKILL)

    def test_operational_failures_do_not_become_ownership_blockers(self) -> None:
        self.assertIn("Ownership compare exit `10`: enter `RECONCILING`", FAILURE_ROUTING)
        self.assertIn("retry the same bounded call once", FAILURE_ROUTING)
        self.assertIn("A second\n  no-delta runtime failure is `INCOMPLETE`", FAILURE_ROUTING)
        self.assertIn("never re-seal", FAILURE_ROUTING)
        self.assertIn("ImplementationResult `PLANNING_INPUT_CHANGED`: `BLOCKED`", FAILURE_ROUTING)

    def test_reconciliation_scenario_matrix_is_closed(self) -> None:
        self.assertIn("Preserved external change, disjoint from planning authority and task impact", FAILURE_ROUTING)
        self.assertIn("Worker-attributable scope violation", FAILURE_ROUTING)
        self.assertIn("Overlapping product path with unclear actor", FAILURE_ROUTING)
        self.assertIn("overwritten pre-existing work", FAILURE_ROUTING)
        self.assertIn("A path inside the envelope can still be externally edited", FAILURE_ROUTING)
        self.assertIn("`WITHIN_ENVELOPE` means only", TASK_OWNERSHIP)
        self.assertIn("blocked: planning input changed", PLANNING_CURRENTNESS)

    def test_final_review_has_one_disjoint_restart(self) -> None:
        self.assertIn("restart the complete final review once", SKILL)
        self.assertIn("a second disjoint identity drift is\n   `INCOMPLETE`", SKILL)

    def test_completion_publishes_independent_result(self) -> None:
        self.assertIn("implementation-result-v2", SKILL)
        self.assertIn("implementation_result.py publish", SKILL)
        self.assertIn("immutable ImplementationResult publication succeeded", SKILL)
        self.assertIn("It does not mean `VERIFIED`", SKILL)

    def test_later_verification_cannot_reopen_implementation(self) -> None:
        self.assertIsNotNone(
            re.search(
                r"later independent Verification invocation starts\s+a new Implementation\s+Lead "
                r"invocation; it never reopens this one",
                SKILL,
            )
        )
        self.assertIn("cannot retroactively alter this\ninvocation's immutable result", SKILL)


if __name__ == "__main__":
    unittest.main()
