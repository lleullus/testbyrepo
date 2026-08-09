from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")


class ActiveSkillContractTests(unittest.TestCase):
    def test_implementation_skill_names_direct_subagent_and_review_contract(self) -> None:
        implementation_skill = " ".join(IMPLEMENTATION_SKILL.split())
        implementation_skill_lower = implementation_skill.lower()
        self.assertIn("exact ready local Markdown Ticket", IMPLEMENTATION_SKILL)
        self.assertIn("Implementation Subagent", IMPLEMENTATION_SKILL)
        self.assertIn("Host Subagent Invocation Mechanism", IMPLEMENTATION_SKILL)
        self.assertIn("current project directly", IMPLEMENTATION_SKILL)
        self.assertIn("actual project diff", IMPLEMENTATION_SKILL)
        self.assertIn("every Markdown acceptance criterion (AC)", IMPLEMENTATION_SKILL)
        self.assertIn("known remaining implementation work", implementation_skill)
        self.assertIn("same user-designated Implementation Subagent", implementation_skill)
        self.assertIn("no known correctable in-scope due-now implementation work remains", implementation_skill)
        self.assertIn("requires direct runtime evidence", implementation_skill)
        self.assertIn("must not report", IMPLEMENTATION_SKILL)

        self.assertIn(
            "If the user explicitly designates one or more implementation research models, invoke "
            "`Implementation Research Agent` roles using only those designated models",
            implementation_skill,
        )
        self.assertIn(
            "using only those designated models through the host's `Host Subagent Invocation Mechanism`",
            implementation_skill,
        )
        self.assertIn(
            "If the user does not designate an implementation research model, the Implementation Lead performs "
            "the needed research directly and must not assign a separate research agent",
            implementation_skill,
        )
        self.assertIn(
            "Parallel research is allowed only when the user designates multiple research models and explicitly "
            "chooses parallel execution",
            implementation_skill,
        )
        self.assertIn(
            "without such a model designation, do not create additional delegation cost",
            implementation_skill,
        )
        for research_surface in (
            "implementation and integration surfaces",
            "pre-existing or concurrent changes",
            "required files, executables, dependencies, and focused-check availability",
            "scope, dependency, authority, or contract conflicts",
        ):
            self.assertIn(research_surface, implementation_skill)
        self.assertIn(
            "Its findings are advisory and do not bind the Implementation Subagent's internal design, exact file "
            "list, implementation sequence, or technical steps",
            implementation_skill,
        )
        self.assertIn("do not assign an AC or whole-Ticket verdict", implementation_skill)
        self.assertIn(
            "The Implementation Lead directly confirms the material current-project facts used for the assignment "
            "decision",
            implementation_skill,
        )
        self.assertIn(
            "Any further delegated research is limited to research models already designated by the user",
            implementation_skill,
        )
        self.assertIn(
            "only then invoke the user-designated `Implementation Subagent`",
            implementation_skill,
        )
        for role_only_research_bypass in (
            "models or roles",
            "model or role",
            "multiple research models or roles",
            "models or roles already designated",
        ):
            self.assertNotIn(role_only_research_bypass, implementation_skill_lower)

    def test_implementation_skill_gates_actual_product_handoff_before_verification(self) -> None:
        implementation_skill = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "concrete post-implementation actual-product handoff-check plan",
            "Ticket-created first executable",
            "current absence of that Ticket-owned artifact is not a feasibility failure",
            "unavailable focused-check capability",
            "pre-mutation blocker",
            "gross handoff-liveness",
            "Ticket-required nominal success class",
            "Ticket-unowned debug hook or seam",
            "leave residual causal uncertainty for Verification",
            "actual execution context and direct raw product-boundary result",
            "same-Ticket due-now implementation work",
            "classify it neither as verification-only work nor as a new feature or Ticket",
            "every materially distinct required route has current gross actual-product handoff-liveness evidence",
            "nominated implementation-route index",
            "navigation only, not a runtime-readiness claim or independent AC evidence",
            "must not constrain or reduce the Verification Lead's independent scenario design",
        ):
            self.assertIn(required, implementation_skill)

        ordered_contract = (
            "concrete post-implementation actual-product handoff-check plan",
            "After implementation, for each materially distinct route",
            "same-Ticket due-now implementation work",
            "Begin independent verification only after",
            "nominated implementation-route index",
        )
        positions = [implementation_skill.index(text) for text in ordered_contract]
        self.assertEqual(positions, sorted(positions))

    def test_verification_skill_names_direct_verification_and_remediation_contract(self) -> None:
        verification_skill = " ".join(VERIFICATION_SKILL.split())
        for required in (
            "same exact ready local Markdown Ticket",
            "allowed verification surface",
            "exactly three operational product-verification roles",
            "`Runtime Runner`",
            "`Verification Lead`",
            "`Remediation Agent`",
            "`Coverage Challenger`",
            "Pre-Approval Coverage Gate",
            "coverage_gate.py",
            "COVERAGE_GATE_UNSUPPORTED",
            "PRE_APPROVAL_COVERAGE_GATE_FAILURE",
            "pre-approval runtime-readiness investigator",
            "direct review of Runtime Runner results",
            "No Runner assertion itself establishes a fact",
            "Runtime Runner must not interpret or decompose AC obligations",
            "acquire direct AC evidence or reach the first AC-deciding observation",
            "Verification Lead itself designs one or more verification scenarios",
            "Ask the user to explicitly approve the disclosed scenario plan",
            "Before that approval, do not prepare the environment or acquire direct evidence",
            "After approval, prepare only the approved verification environment",
            "Execute only `READY` scenarios",
            "exactly one result row for every Markdown AC",
            "`SATISFIED` and `UNDETERMINED` ACs are never remediation targets",
            "minimum product change directly required",
            "at most three cycles",
        ):
            self.assertIn(required, verification_skill)

        for required in (
            "nominated implementation-route index",
            "non-authoritative route-discovery and navigation input",
            "establish any runtime-readiness fact only through the existing Runtime Runner boundary",
            "do not enter the Canonical Source Package or Coverage Challenge",
            "must not constrain candidate search or independent scenario design",
            "does not block Verification",
        ):
            self.assertIn(required, verification_skill)

        ordered_contract = (
            "Verification Lead itself performs a read-only lead-first planning inspection",
            "After independently decomposing the Ticket into coverage units",
            "nominated implementation-route index",
            "For each unit, identify the required product entrypoint",
            "Verification Lead invokes one or more instances of the official `Runtime Runner`",
            "Verification Lead itself designs one or more verification scenarios",
            "Ask the user to explicitly approve the disclosed scenario plan",
            "After approval, prepare only the approved verification environment",
            "Execute only `READY` scenarios",
        )
        positions = [verification_skill.index(text) for text in ordered_contract]
        self.assertEqual(positions, sorted(positions))

        self.assertNotIn("LEAD_FAILURE", VERIFICATION_SKILL)

    def test_verification_skill_removes_retired_verification_role_names(self) -> None:
        self.assertNotIn("Readiness Research Agent", VERIFICATION_SKILL)
        self.assertNotIn("Fresh Verification Lead", VERIFICATION_SKILL)
        self.assertNotIn("Fresh Verification Subagent", VERIFICATION_SKILL)

    def test_active_skills_exclude_retired_mechanism_terms(self) -> None:
        combined = (IMPLEMENTATION_SKILL + "\n" + VERIFICATION_SKILL).lower()
        for term in (
            "implementation verification module",
            "module.implement",
            "module.verify",
            "module.inspect",
            "opencode worker",
            "opencode verifier",
            "terraworker",
            "fresh luna",
            "implementation-handoff",
            "verification-result",
            "verification-run",
            "workflow-store",
            "baseline capsule",
        ):
            self.assertNotIn(term, combined)


if __name__ == "__main__":
    unittest.main()
