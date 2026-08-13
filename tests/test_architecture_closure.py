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
            "transition verifier may surface a qualifying current observation before finishing",
            "concrete current Ticket-owned implementation/integration/surface/readback absence",
            "additional same-Ticket implementation may overlap",
            "useful work already in flight",
            "does **not** change product authority, Ticket Scope",
            "does not add a persistent scheduler, finding queue, assignment ledger, Worker identity system, or controller",
            "every overlapped Ticket verifier must return or be host-confirmed stopped",
            "product effect it already started must be terminal/cleaned up or established unable to mutate the target further",
            "review the combined current project",
            "new fresh transition Verification must run before leaving the Ticket",
            "must not be cited as permission for ordinary latency complaints",
        ):
            self.assertIn(required, section)

    def test_streaming_ralph_closure_keeps_fresh_transition_and_goal_barriers(self) -> None:
        section = CLOSURE.split("### 3. Ralph Repetition And Regression Recovery — PROVED", 1)[1].split(
            "### 4. Completion Boundary — PROVED", 1
        )[0]
        for required in (
            "may report a qualifying current observation before finishing",
            "concrete current Ticket-owned implementation/integration/surface/readback absence",
            "more than one same-Ticket Implementation Lead invocation in flight",
            "does not knowingly duplicate materially the same work against materially the same evidence merely to increase concurrency",
            "Concurrency is not itself progress",
            "coordination, duplication, or edit-contention cost outweighs useful critical path overlap, Ralph stays serial",
            "independently rechecks current authority, source, feasibility",
            "full Ticket preservation awareness does not require duplicating concrete work already known to be active in a sibling invocation",
            "every overlapped verifier must also have returned or be host-confirmed stopped",
            "product effect it already started must have reached the authored terminal/cleanup boundary or be established unable to mutate the target further",
            "reviews the resulting current project as one combined product for Ticket Scope, preservation, and unresolved integration conflict",
            "freshly reobserves every AC",
            "only a new fresh transition Verification may authorize the Ticket transition",
            "Goal Verification begins only after all current implementation mutation has ended",
            "product effect started by such a verifier is terminal/cleaned up or established unable to mutate the target further",
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
            "avoids knowingly duplicating materially the same in-flight work",
            "Ralph may serialize whenever overlap is not useful or safe",
            "wait for or host-confirmedly stop that verifier and wait for any verifier-started product effect to reach its authored terminal/cleanup boundary",
            "possible residual wait plus a new fresh verifier are deliberate costs paid for a non-overlapping final evidence boundary",
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
