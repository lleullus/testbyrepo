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

    def test_recorded_user_directed_streaming_evolution_is_explicit_and_later_supersession_is_bounded(self) -> None:
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
            "fresh verification observation may surface a qualifying direct contradiction",
            "concrete current Ticket-owned implementation/integration/surface/readback absence",
            "additional same-Ticket implementation may overlap",
            "did **not** change product authority, Ticket Scope",
            "fresh Runner leaves while Verification Lead / Goal Verification Lead alone adjudicated verdicts",
            "later efficiency generation below supersedes only that redundant observer sequence",
            "mutation-invalidated progression authority and the fresh independent barrier remain unchanged",
            "historical generation bought an extra streaming feedback cycle at the cost of a duplicate settled observation",
            "later efficiency generation below supersedes that last/only extra cycle",
            "`GOAL INCONCLUSIVE` ends only the current final-verification invocation",
            "one failed endpoint/representation does not establish dependency-wide unavailability",
            "host-known required work still in flight is an unexhausted path",
            "returned or host-confirmed stopped/unproductive invocation clears only that liveness blocker",
            "still closes any remaining bounded evidence or correction path before a terminal result",
        ):
            self.assertIn(required, section)

    def test_streaming_ralph_closure_keeps_fresh_transition_and_goal_barriers_without_duplicate_observers(self) -> None:
        section = CLOSURE.split("### 3. Ralph Repetition And Regression Recovery — PROVED", 1)[1].split(
            "### 4. Completion Boundary — PROVED", 1
        )[0]
        for required in (
            "Fresh Verification Runner observation may surface a qualifying current contradiction",
            "Ticket-owned implementation/integration/surface/readback absence",
            "Current-conversation user role binding, reusable ordering, reservation",
            "Ordered Implementation Subagent bindings are reusable precedence, not one-use slots",
            "default first implementation dispatch is one Lead / one Subagent",
            "exact user-authored immediate-overlap instruction overrides only the default wait and Lead-owned efficiency preference",
            "Scheduling repair is prospective",
            "product-authorized mutation produced by an otherwise eligible implementation binding",
            "observed scheduling delta is sent once, delta-only, to affected active roles",
            "minimum focused liveness/integration checks",
            "lightweight integration/authority preflight rather than a duplicate full-AC acquisition",
            "Verification Lead is the first settled full-AC observer when Ralph must leave that Ticket",
            "mixed/non-independent Tickets retain Ralph fresh AC reobservation",
            "last/only all-`Independent` Ticket goes directly to fresh whole-Spec Goal Verification",
            "no new Runner assignment exists merely to finish the old roster/coverage",
            "prospective Runner withdrawal/future-assignment change does not retroactively discard attributable evidence",
            "One endpoint/representation/transport/readback failure establishes only that boundary",
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
            "each affected active role receives exactly one concise delta-only update",
            "unaffected roles receive nothing",
            "ordering is reusable precedence rather than implicit one-shot slot consumption",
            "returned role is eligible again",
            "maximum concurrency is capacity rather than a command to fan out",
            "exact user-authored immediate-overlap instruction outranks Ralph's Lead-owned efficiency preference",
            "returns that exact `ORCHESTRATION CONFLICT` rather than silently serializing",
            "Scheduling repair is prospective",
            "product-authorized mutation at the wrong authored order or timing",
            "does not roll back or replay the same correction",
            "Scope-exceeding, wrong-role, unauthorized-dangerous-effect, or user-rejected mutation is not protected",
            "active gate cannot be bypassed by an explicit To Spec request",
            "routine repository-disclosure approval is not added",
            "No mandatory live-Challenger smoke",
            "prospective Runner withdrawal or future-assignment change does not retroactively discard evidence",
            "implicit one-use role slots",
            "repeated whole-conversation freshness rereads by every Lead/Subagent/Runner",
            "silently serializing an exact user-fixed overlap for Lead convenience",
        ):
            self.assertIn(required, section)

    def test_2026_08_14_efficiency_generation_removes_only_duplicate_success_path_work(self) -> None:
        section = " ".join(
            CLOSURE.split("A subsequent 2026-08-14 efficiency generation", 1)[1]
            .split("The five-condition Core Freeze Admission below", 1)[0]
            .split()
        )
        for required in (
            "removes duplicate observation work that contributed no additional verdict authority",
            "no longer pays both a Ralph full-AC acquisition and a Verification Lead full-AC acquisition",
            "lightweight integration/ authority preflight and the verifier is the first settled full observer",
            "Mixed or non-independent Tickets retain Ralph fresh AC reobservation",
            "Earlier Independent Tickets still obtain Ticket Verification before Ralph leaves them",
            "last/only Ticket, fresh Goal Verification immediately supplies the first settled independent full observation",
            "unless the user explicitly requested that separate Ticket-level verdict",
            "Whole-Spec `GOAL VERIFIED` authority and final fresh evidence are unchanged",
            "invalidated cycle never receives new Runner assignments merely to complete its old roster/coverage",
            "Already-active observation continues only when it can materially surface a distinct current correction",
            "Implementation Lead likewise stops short of rehearsing independent verification",
            "complete browser/viewport/state/lifecycle/AC matrix remains with Verification Lead or Goal Verification Lead",
            "Rejected efficiency alternatives are impacted-only final verification, evidence caching across mutation, verifier-context reuse as evidence",
            "removes only duplicate success-path acquisition/cycles and low-value invalidated work",
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
            "efficiency rule stops creating new old-cycle assignments after invalidation",
            "already-started effects still reach their authored terminal/cleanup boundary",
            "Settled all-Independent success paths intentionally use one full observer per transition boundary",
            "last/only Ticket uses Goal Verification directly unless the user requested a separate Ticket verdict",
            "removal of an entire duplicate browser/runtime/persistence acquisition without weakening verdict authority",
            "Implementation Lead intentionally limits product checks to changed/integration-affected gross liveness",
            "duplicate full-matrix execution adds context and runtime cost without adding independent verdict authority",
            "prospective Runner withdrawal does not invalidate already attributable evidence",
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
