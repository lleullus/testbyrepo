from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
TO_TICKETS_SKILL = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
EXAMPLES = ROOT / "matt/examples"


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text)
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group(1).strip()


def top_level_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        if line.startswith("- "):
            items.append(line[2:])
        elif line.strip() and not line.startswith("  "):
            raise AssertionError(f"non-item top-level content: {line}")
    return items


class ActiveSkillContractTests(unittest.TestCase):
    def test_ticket_verification_flows_remain_exact_product_authority(self) -> None:
        normalized = " ".join(TO_TICKETS_SKILL.split())
        for required in (
            "states how the Ticket's Acceptance Criteria can be observed",
            "observable product flow, expected effect, and readback",
            "one exact top-level `- ` list item in authored order",
            "Preserve its count, order, product trigger, expected effect, readback, grouping, and meaning",
            "do not merge materially distinct flows",
            "split one flow into implementation seams",
            "weaken it into optional guidance",
        ):
            self.assertIn(required, normalized)

        tickets = [EXAMPLES / "TICKET.template.md"]
        tickets.extend(
            EXAMPLES / name / "tickets/TICKET-001.md"
            for name in ("simple-non-ui", "ui-prototype", "large-scope-shaping")
        )
        for ticket_path in tickets:
            with self.subTest(ticket=ticket_path):
                items = top_level_items(
                    section(ticket_path.read_text(encoding="utf-8"), "Verification")
                )
                self.assertTrue(items)

    def test_implementation_skill_preserves_direct_assignment_and_review(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "exact ready local Markdown Ticket",
            "Implementation Subagent",
            "Host Subagent Invocation Mechanism",
            "current project directly",
            "actual project diff",
            "every Markdown acceptance criterion (AC)",
            "same admitted Implementation Subagent",
            "no known correctable in-scope due-now implementation work remains",
            "Gross actual-product liveness",
            "actual execution context and direct raw product-boundary result",
            "same-Ticket due-now implementation work",
            "checks actually performed",
            "exact unresolved limitations",
        ):
            self.assertIn(required, normalized)

    def test_ralph_worker_exception_is_narrow_invocation_local_and_explicit_leaf_stays_user_designated(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "In an explicit Implementation Lead request, that role remains user-designated",
            "only exception is an invocation from the canonical `../iis-goal-loop/SKILL.md`",
            "user-designated `Implementation Subagent` role when one applies to the current consumption point",
            "otherwise a host-provided invocation-local role",
            "exception grants no new Ticket authority",
            "Never write the internal role to `Worker:`",
            "`Worker:` remains empty",
            "Ralph-provided current observation is navigation context only",
            "cannot add or strengthen a Ticket obligation",
        ):
            self.assertIn(required, normalized)
        self.assertIn("current parent-outcome/AC/Behavior trace", normalized)

    def test_ralph_resumption_reuses_only_same_ticket_working_context(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "same Ticket remains active inside that exact Ralph invocation",
            "host may resume the same invocation-local role",
            "only while retained technical context remains bounded, relevant, and likely to reduce rediscovery",
            "noisy, oversized, materially contradicted, no longer relevant, or likely to cost more than fresh technical rehydration",
            "reinvoke a fresh role with the same admission source instead",
            "Resumption preserves only technical working context",
            "does not preserve feasibility, current-source facts, prior observations, authority currentness",
            "does not make a retained shell, working directory, dev server",
            "browser/profile, process, cache, database connection, or other tool/runtime state current",
            "directly confirming that it still reflects the current project, current authorized target",
            "otherwise recreate or rebind it before relying on its result",
            "Do not resume that role across a Ticket change",
            "whole-Spec Goal Verification",
            "`GOAL OPEN — NO PROGRESS`",
            "before any project mutation, revalidate",
            "session registry",
        ):
            self.assertIn(required, normalized)

    def test_same_ticket_concurrency_rechecks_current_source_and_never_applies_stale_work(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "another Implementation Lead invocation for the same active Ticket in flight at the same time",
            "grants no shared feasibility, source fact, diagnosis, or mutation ownership",
            "independently rechecks the current project immediately before mutation",
            "preserves every user and concurrent change already present",
            "already been satisfied, superseded, or materially changed by another actor",
            "do not apply a stale planned change",
            "revise the in-Scope implementation from current evidence instead",
        ):
            self.assertIn(required, normalized)

    def test_same_ticket_overlap_preserves_full_contract_awareness_without_duplicate_mutation_duty(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "do not defer it merely to make this invocation appear complete",
            "does not require a second invocation to duplicate concrete work",
            "current caller has already identified as actively in flight in another same-Ticket invocation",
            "feed it to the existing admitted role first rather than consuming another user-reserved role",
            "recheck current source and revise or abandon stale technical assumptions",
            "creates no permanent defect, AC, or file ownership",
            "Full Ticket Scope, AC, Behavior/UI preservation, and integration awareness still apply",
            "if that work remains current after the sibling activity settles, it is ordinary due-now work again",
        ):
            self.assertIn(required, normalized)

    def test_role_designations_do_not_cross_consume_without_separate_user_authority(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "Consume only the `Implementation Subagent` binding admitted for implementation",
            "A `Verification Runner` or other IIS-role binding is not eligible for implementation or implementation research",
            "cross-role use requires the user's separate designation for that exact role",
            "A `Verification Runner` designation and an `Implementation Subagent` designation are not implementation-research designations",
            "unless the user separately designated that same configured model/agent for implementation research",
            "Role binding comes from the explicit designation, not model identity",
            "user's explicit role binding, reservation, ordering, consumption timing, concurrency, and parallel-execution choices",
            "host controls only the remaining invocation, communication, resumption, retry, and scheduling details",
        ):
            self.assertIn(required, normalized)

    def test_explicitly_preserved_predecessor_is_bounded_navigation_not_inherited_authority(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "approved Scope/Spec/Ticket explicitly preserves, replaces, rebuilds, or migrates an existing product capability",
            "directly inspect the bounded predecessor implementation and the current product boundaries it actually uses",
            "before concluding that an external dependency is unavailable or that no in-Scope implementation path remains",
            "Use that predecessor only as navigation and preservation context",
            "do not inherit its internal design, policy, schema, fallback behavior, or historical semantics as authority",
            "do not broaden this into legacy-repository archaeology",
        ):
            self.assertIn(required, normalized)

    def test_behavior_trace_is_semantic_guardrail_not_implementation_mechanism(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "`Parent outcome ordinal`",
            "`AC ordinals`",
            "`Behavior authority ordinals`",
            "mapped Behavior items supply semantic guardrails",
            "current technical diagnosis remains implementation-owned and non-normative",
            "Do not change or bypass the trace merely because a different implementation mechanism is selected",
        ):
            self.assertIn(required, normalized)

    def test_research_remains_user_bounded_and_advisory(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "using only those designated models",
            "must not assign a separate research agent",
            "explicitly chooses parallel execution",
            "do not create additional delegation cost",
            "Its findings are advisory",
            "The Implementation Lead directly confirms",
            "limited to research models already designated by the user",
        ):
            self.assertIn(required, normalized)

    def test_result_cannot_become_independent_verification_or_ac_verdict(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for forbidden_claim in (
            "Do not assign independent verification readiness",
            "claim independent or direct AC evidence",
            "issue an AC verdict",
            "report final `VERIFIED` or any equivalent whole-Ticket success status",
        ):
            self.assertIn(forbidden_claim, normalized)
        self.assertIn(
            "implementation-result limitation",
            normalized,
        )
        self.assertIn(
            "outside the supported IIS lifecycle; do not claim it was established",
            normalized,
        )

    def test_no_verification_handoff_or_replacement_artifact_remains(self) -> None:
        for forbidden in (
            "Primary Verifier",
            "Runtime Runner",
            "route-navigation",
            "iis_ephemeral_transport",
            "publish_route_navigation",
            "serialized handoff exception",
            "verification-only",
        ):
            self.assertNotIn(forbidden, IMPLEMENTATION_SKILL)
        self.assertIn(
            "Do not create a serialized handoff, sidecar, replacement verification artifact, or approval workflow",
            " ".join(IMPLEMENTATION_SKILL.split()),
        )

    def test_structural_validator_is_admission_support_not_semantic_authority(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        self.assertIn("../matt/skills/to-tickets/validate_ticket.py", normalized)
        self.assertIn("resolved from this skill's canonical physical directory", normalized)
        self.assertIn("nonzero result blocks assignment before mutation", normalized)
        for excluded in (
            "does not establish product meaning",
            "AC-to-flow or Behavior-to-flow semantic correctness",
            "implementation feasibility",
            "runtime availability",
            "evidence, or a verdict",
        ):
            self.assertIn(excluded, normalized)
        self.assertIn("Implementation Lead still performs every semantic", normalized)

    def test_scope_owned_acceptance_surface_is_due_now_but_external_surface_is_not(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "`Acceptance surface` is `Ticket Scope creates`",
            "ordinary product surface and authoritative readback same-Ticket due-now implementation work",
            "Do not report implementation completion while it is missing",
            "Do not expand implementation responsibility for `Operator-owned` surfaces",
            "Do not create a surface identified as `Delivery contract guarantees`",
        ):
            self.assertIn(required, normalized)
        self.assertIn("paragraphs 8 and 9", normalized)

    def test_candidate_recipe_is_optional_current_result_only(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for field in (
            "Candidate Execution Recipe (optional, non-authoritative, current implementation result only)",
            "Verification flow ordinal:",
            "Observed current-source binding:",
            "Entrypoint or inspection target:",
            "Working directory and general environment:",
            "Input:",
            "Authoritative readback:",
            "Cleanup or disposal:",
            "Checks actually performed:",
        ):
            self.assertIn(field, IMPLEMENTATION_SKILL)
        self.assertIn("A future fresh verification session does not require a Recipe", normalized)
        self.assertIn("Its absence is not a readiness or admission defect", normalized)
        self.assertIn("detect staleness and bound location checking", normalized)
        self.assertIn("cannot prove currentness in a later session", normalized)

    def test_candidate_recipe_cannot_carry_verdict_flow_replacement_or_durable_identity(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for forbidden_claim in (
            "does not add, replace, merge, split, or reinterpret a flow",
            "Do not include an AC mapping, expected result, `PASS`, `FAIL`, `VERIFIED`",
            "claim of independent evidence",
            "not durable candidate/source identity",
            "sidecar, Recipe file, database, store, capsule, retained source, digest, run ID",
        ):
            self.assertIn(forbidden_claim, normalized)

    def test_active_contracts_exclude_removed_roles_and_runtime(self) -> None:
        combined = IMPLEMENTATION_SKILL + "\n" + TO_TICKETS_SKILL
        for forbidden in (
            "Primary Verifier",
            "Runtime Runner",
            "coverage_gate.py",
            "route-navigation",
            "iis_ephemeral_transport",
            "iis-verify",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
