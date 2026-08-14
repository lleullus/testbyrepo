from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
CLOSURE = (ROOT / "ARCHITECTURE-CLOSURE.md").read_text(encoding="utf-8")


class ArchitectureClosureTests(unittest.TestCase):
    def test_finite_failure_surface_has_exactly_nine_numbered_classes(self) -> None:
        headings = re.findall(r"(?m)^### (\d+)\. (.+)$", CLOSURE)
        self.assertEqual([int(number) for number, _ in headings], list(range(1, 10)))

    def test_each_failure_class_has_a_terminal_classification(self) -> None:
        headings = [line for line in CLOSURE.splitlines() if line.startswith("### ")]
        allowed = ("PROVED", "ACCEPTED TRADE-OFF", "OUT OF SUPPORTED RANGE")
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertTrue(any(token in heading for token in allowed), heading)

    def test_ticket_projection_closure_explicitly_preserves_semantic_decomposition(self) -> None:
        required = (
            "Ralph independently revalidates current Spec-to-Ticket semantic compatibility before mutation",
            "An unchanged `Status: ready` is not sufficient",
            "The validator does **not** decide semantic equivalence",
            "Exact string equality would reject valid solution-independent decomposition",
            "agent-quality/evaluation issue unless the authored contract itself permits stale mutation",
        )
        for text in required:
            self.assertIn(text, CLOSURE)

    def test_recorded_user_directed_streaming_evolution_is_explicit_and_re_frozen(self) -> None:
        section = " ".join(
            CLOSURE.split("## Recorded User-Directed Architecture Evolution", 1)[1]
            .split("## Contract-Preserving Execution Optimization Boundary", 1)[0]
            .split()
        )
        for required in (
            "explicitly chose to evolve the supported Ralph execution model",
            "bounded same-Ticket streaming remediation",
            "intentional architecture generation change",
            "not a faithful-contract counterexample",
            "not a change admitted through either contract-preserving optimization lane",
            "fresh verification observation may surface a qualifying direct contradiction",
            "concrete current Ticket-owned implementation/integration/surface/readback absence",
            "additional same-Ticket implementation may overlap",
            "user role-consumption constraints",
            "does **not** change product authority, Ticket Scope",
            "Verification observation uses fresh Runner leaves",
            "Runner reports are not votes",
            "user-designated role binding/consumption timing is preserved",
            "no persistent scheduler, finding queue, assignment ledger, Runner/Worker identity system, evidence cache, or controller",
            "every overlapped Runner/effect must quiesce",
            "review the combined current project and freshly reobserve the full active Ticket",
            "new Verification Lead cycle with fresh Runner invocation(s)",
            "Every provisionally satisfied all-Independent Ticket therefore runs Ticket Verification, including the last or only Ticket",
            "`GOAL INCONCLUSIVE` ends only the current final-verification invocation",
            "one failed endpoint/representation does not establish dependency-wide unavailability",
            "host-known required work still in flight is an unexhausted path",
            "returned or host-confirmed stopped/unproductive invocation clears only that liveness blocker",
            "still closes any remaining bounded evidence or correction path before a terminal result",
            "must not be cited as permission for ordinary latency complaints",
        ):
            self.assertIn(required, section)

    def test_streaming_ralph_closure_keeps_fresh_transition_and_goal_barriers(self) -> None:
        section = CLOSURE.split("### 3. Ralph Repetition And Regression Recovery — PROVED", 1)[1].split(
            "### 4. Completion Boundary — PROVED", 1
        )[0]
        for required in (
            "Fresh Verification Runner observation may surface a qualifying current contradiction",
            "Ticket-owned implementation/integration/surface/readback absence",
            "Current-conversation user role binding, reusable ordering, reservation",
            "role reserved for later remediation is not consumed for initial fan-out",
            "Ordered Implementation Subagent bindings are reusable precedence, not one-use slots",
            "returned invocation is eligible again",
            "default first implementation dispatch is one Lead / one Subagent",
            "maximum-concurrency increase or another available binding is capacity, not an immediate-overlap instruction",
            "feeds the finding to that existing invocation first",
            "not persistent defect/AC/file ownership",
            "Under Lead-owned scheduling, an additional same-Ticket Implementation Lead invocation requires materially distinct useful work",
            "exact user-authored immediate-overlap instruction overrides only the default wait and Lead-owned efficiency preference",
            "Scheduling repair is prospective",
            "not rolled back, ceremonially repeated, or reassigned merely to reconstruct preferred historical role order",
            "freshly rechecks current authority, source, feasibility, and concurrent changes before mutation",
            "bounded predecessor implementation is navigation",
            "Every provisionally satisfied all-Independent Ticket runs Ticket Verification, including the last/only Ticket",
            "invalidates the whole cycle for progression",
            "An unrelated scheduling change does not",
            "every relevant Runner/effect must quiesce",
            "freshly reobserves every AC",
            "new Verification Lead cycle with fresh Runner invocation(s)",
            "One endpoint/representation/transport/readback failure establishes only that boundary",
            "cannot silently satisfy an exact authored representation unless the approved contract permits equivalence",
            "A bounded Runner assignment decomposes observation only; it never defines or narrows authored verification coverage",
            "A decision not to attempt a required boundary is an evidence limit, not evidence of dependency unavailability",
            "`GOAL INCONCLUSIVE` ends only its Goal Verification invocation",
            "Before `GOAL OPEN — NO PROGRESS`, Ralph closes every currently known bounded evidence/correction path",
        ):
            self.assertIn(required, section)

    def test_2026_08_14_intent_retention_generation_is_explicit_and_re_frozen(self) -> None:
        section = " ".join(
            CLOSURE.split("A further 2026-08-14 user-directed generation change", 1)[1]
            .split("The five-condition Core Freeze Admission below", 1)[0]
            .split()
        )
        for required in (
            "user-intent retention and low-context orchestration load explicit architecture priorities",
            "repeatedly re-injects the full conversation",
            "extra context can itself cause instruction drift",
            "Live orchestration is therefore event-driven",
            "only the affected scheduling change is propagated",
            "ordering is reusable precedence rather than implicit one-shot slot consumption",
            "returned role is eligible again",
            "maximum concurrency is capacity rather than a command to fan out",
            "exact user-authored immediate-overlap instruction outranks Ralph's Lead-owned efficiency preference",
            "Scheduling repair is prospective",
            "does not roll back or replay the same correction",
            "active gate cannot be bypassed by an explicit To Spec request",
            "routine repository-disclosure approval is not added",
            "No mandatory live-Challenger smoke",
            "Future implementation-role ordering/concurrency changes or other unrelated scheduling changes do not discard attributable evidence",
            "implicit one-use role slots",
            "repeated whole-conversation freshness rereads by every Lead/Subagent/Runner",
            "historical rollback/replay merely to reconstruct preferred dispatch order",
        ):
            self.assertIn(required, section)

    def test_contract_preserving_optimization_boundary_is_narrow_and_fallback_safe(self) -> None:
        section = CLOSURE.split("## Contract-Preserving Execution Optimization Boundary", 1)[1].split(
            "## Core Freeze Admission", 1
        )[0]
        for required in (
            "fits exactly one lane below and satisfies every condition in that lane",
            "Lane A — Monotonic Deduplication Refinement",
            "no denominator row disappears, merges, or inherits another row's verdict",
            "distinct inputs, relevant states, branches, lifecycle boundaries, or authoritative readbacks remain distinct acquisitions",
            "governed expensive acquisition count is weakly reduced or unchanged",
            "ordinary separate fresh acquisition with unchanged semantics",
            "Lane B — Conditional Invocation-Local Locality Optimization",
            "not claimed to be a monotonic wall-clock improvement",
            "noisy, oversized, materially contradicted, no longer relevant",
            "baseline fresh invocation remains fully supported",
            "performance claim remains limited to the structurally removed cold rediscovery",
            "does **not** admit impacted-only AC reobservation, verifier-context reuse, evidence caching",
        ):
            self.assertIn(required, section)

    def test_freeze_reopening_requires_all_five_admission_conditions(self) -> None:
        section = CLOSURE.split("## Core Freeze Admission", 1)[1].split("## Explicit Non-Reasons", 1)[0]
        for label in (
            "Faithful-contract counterexample",
            "Architecture-general",
            "Material failure class",
            "Invariant repair",
            "Complexity test",
        ):
            self.assertIn(label, section)
        self.assertIn("Any other future issue may reopen core architecture only when **all** of the following are true", section)
        self.assertIn("fails the Contract-Preserving Execution Optimization Boundary", section)

    def test_freeze_rejects_agent_quality_and_project_specific_patch_pressure(self) -> None:
        for text in (
            "an agent missed a useful field, endpoint, helper, source location, or root cause",
            "a different technical correction would have been better",
            "an iteration was inefficient",
            "parser, retry, fallback, storage, or deployment-specific rule",
            "agent-quality variance without a faithful-contract architecture counterexample",
        ):
            self.assertIn(text, CLOSURE)

    def test_state_tradeoff_stays_explicitly_state_free(self) -> None:
        section = CLOSURE.split("### 9. State, Restart, And Historical Efficiency — ACCEPTED TRADE-OFF", 1)[1]
        for text in (
            "No durable attempt history",
            "Same-Ticket concurrent implementation can create stale planned work, edit contention, or wasted Worker effort",
            "When scheduling is left to Ralph, it avoids knowingly duplicating materially the same in-flight work",
            "When the user fixed exact immediate overlap, that Lead-owned efficiency preference does not override the instruction",
            "Event-driven live reconciliation deliberately gives up repeated proof-of-currentness checks",
            "lower context noise and less instruction drift",
            "Ordered reusable bindings may cause the same configured implementation role to be invoked repeatedly across distinct corrections",
            "Prospective scheduling repair",
            "not ceremonial rollback/replay",
            "wait for or host-confirmedly stop every overlapped Runner",
            "Runner-started product effect to reach its authored terminal/cleanup boundary",
            "residual wait plus a fresh cycle are deliberate costs paid for a non-overlapping evidence boundary",
            "last/only all-Independent Ticket now pays a Ticket Verification cycle before whole-Spec Goal Verification",
            "duplicate-observation cost is intentional because Ticket Verification is the streaming correction engine",
            "Bounded evidence/correction closure before `NO PROGRESS` may spend additional investigation time",
            "rather than becoming arbitrary endpoint discovery or a persistent path registry",
            "does not add a scheduler database, dispatch ledger, Worker identity system, or persistent finding queue",
            "Positional ordinals",
            "Complete ready Ticket-set planning",
            "does not persist a Goal-achieved marker",
            "semantic hashes",
            "controller databases",
        ):
            self.assertIn(text, section)


if __name__ == "__main__":
    unittest.main()
