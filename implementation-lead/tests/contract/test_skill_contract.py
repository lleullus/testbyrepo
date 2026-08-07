from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_EXECUTION_CONTRACT = (ROOT / "PHASE-5-VERIFICATION-EXECUTION-CONTRACT.md").read_text(encoding="utf-8")


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

    def test_verification_skill_names_direct_verification_and_remediation_contract(self) -> None:
        verification_skill = " ".join(VERIFICATION_SKILL.split())
        self.assertIn("same exact ready local Markdown Ticket", VERIFICATION_SKILL)
        self.assertIn("current project", VERIFICATION_SKILL)
        self.assertIn("allowed verification surface", VERIFICATION_SKILL)
        self.assertIn("user-facing lead session", verification_skill)
        self.assertIn("delegated subagent", verification_skill)
        self.assertIn("user-facing commentary channel", verification_skill)
        self.assertIn("stop as `unsupported` before any direct evidence acquisition", verification_skill)
        self.assertIn("Verification Lead itself designs one or", VERIFICATION_SKILL)
        self.assertIn("performs a read-only lead-first planning inspection", verification_skill)
        self.assertIn("must not be preserved or reused as direct AC evidence", verification_skill)
        self.assertIn("identify the required product entrypoint", verification_skill)
        for prerequisite in (
            "agent, model, thinking, tool, executable",
            "fixture, sentinel, failure-hook, provider-target",
            "authority, credential, network, cleanup, readback",
            "universal, and negative-proof requirements",
        ):
            self.assertIn(prerequisite, verification_skill)
        self.assertIn("Invoke one or more `Readiness Research Agent`s", verification_skill)
        self.assertIn("through the host's `Host Subagent Invocation Mechanism`", verification_skill)
        self.assertIn(
            "It must not perform broad product discovery, take ownership of an AC range, design or select scenarios, "
            "assign readiness, acquire direct AC evidence, mutate the product or environment, or decide AC verdicts",
            verification_skill,
        )
        self.assertIn("Its report is advisory; Verification Lead directly verifies every readiness fact used below", verification_skill)
        self.assertIn("new evidence observation", verification_skill)
        self.assertIn("`Verification Scenarios`", verification_skill)
        self.assertIn("stable scenario ID, AC", verification_skill)
        self.assertIn("procedure and verification surface", verification_skill)
        self.assertIn("Readiness is a pre-execution fact, not an AC verdict, and is exactly one of", verification_skill)
        self.assertIn("`PREPARABLE` when a material prerequisite is currently absent", verification_skill)
        self.assertIn("is a pre-execution fact, not an AC verdict", verification_skill)
        self.assertIn("required preparation or dependency, and authority or approval needed", verification_skill)
        self.assertIn("After directly checking every identified prerequisite", verification_skill)
        self.assertIn("explicitly approve the disclosed scenario plan and preparation scope", verification_skill)
        self.assertIn("Before that approval, do not prepare the environment or acquire direct evidence", verification_skill)
        self.assertIn(
            "If the user rejects or changes the plan, revise the choices, scenario paragraphs, readiness facts, and bottom "
            "summary table, then request new approval",
            verification_skill,
        )
        self.assertIn("Approval is a workflow gate only", verification_skill)
        self.assertIn("it is not direct evidence or authority", verification_skill)
        self.assertIn("After approval, prepare only the approved verification environment", verification_skill)
        self.assertIn("do not mutate shared or external state or credentials", verification_skill)
        self.assertIn("chat approval does not supply them", verification_skill)
        self.assertIn("After preparation and before any direct evidence acquisition, directly recheck every prerequisite", verification_skill)
        self.assertIn("Execute only `READY` scenarios", verification_skill)
        self.assertIn(
            "Report every remaining `PREPARABLE`, `NOT_READY`, `UNSUPPORTED`, or `UNSAFE` scenario and its affected AC "
            "before execution; do not attempt it",
            verification_skill,
        )
        self.assertIn("`replaces <old scenario ID>` relationship", verification_skill)
        self.assertIn(
            "show the revised complete scenario paragraphs and bottom summary table, obtain explicit approval, prepare and "
            "recheck readiness, and only then acquire replacement evidence",
            verification_skill,
        )
        self.assertIn("Do not relabel evidence acquired for the old scenario as evidence for its replacement", verification_skill)
        for scenario_field in (
            "observation target",
            "procedure",
            "expected result",
            "direct evidence to collect",
            "decision criteria",
        ):
            self.assertIn(scenario_field, VERIFICATION_SKILL)
        self.assertIn("Host Subagent Invocation Mechanism", VERIFICATION_SKILL)
        self.assertIn("Remediation Agent", VERIFICATION_SKILL)
        self.assertIn("read-only", VERIFICATION_SKILL)
        self.assertIn("product files unmodified", VERIFICATION_SKILL)
        self.assertIn("exactly one result row for every Markdown AC", VERIFICATION_SKILL)
        self.assertIn("all applicable stable scenario IDs, their final readiness and execution facts", verification_skill)
        self.assertIn("each executed scenario's admissible direct evidence", verification_skill)
        self.assertIn("An unshared scenario execution cannot support `SATISFIED`", verification_skill)
        for status in ("SATISFIED", "NOT_SATISFIED", "UNDETERMINED"):
            self.assertIn(status, VERIFICATION_SKILL)
        self.assertIn("`SATISFIED` and `UNDETERMINED` ACs are never remediation targets", VERIFICATION_SKILL)
        self.assertIn("direct evidence", VERIFICATION_SKILL)
        self.assertIn("expected/actual difference", VERIFICATION_SKILL)
        self.assertIn("same cause and the same minimal change", VERIFICATION_SKILL)
        self.assertIn("minimum product change directly required", VERIFICATION_SKILL)
        self.assertIn("changed files and scope", VERIFICATION_SKILL)
        self.assertIn("Agent narration or metadata does not determine", VERIFICATION_SKILL)
        self.assertIn("directly re-verifies", VERIFICATION_SKILL)
        self.assertIn("at most three cycles", verification_skill)
        self.assertIn("cannot start chained remediation", verification_skill)

        ordered_contract = (
            "After directly checking every identified prerequisite",
            "explicitly approve the disclosed scenario plan and preparation scope",
            "After approval, prepare only the approved verification environment",
            "After preparation and before any direct evidence acquisition, directly recheck every prerequisite",
            "Execute only `READY` scenarios",
            "If a scenario changes before or during execution",
        )
        positions = [verification_skill.index(text) for text in ordered_contract]
        self.assertEqual(positions, sorted(positions))

        verification_execution_contract = " ".join(VERIFICATION_EXECUTION_CONTRACT.split())
        for contract_text in (
            "If the user designates a Readiness Research Agent, Verification Lead invokes it through the Host Subagent Invocation Mechanism",
            "A rejection or change requires a revised complete table and new approval",
            "chat approval is not that authority",
            "Every remaining `NOT_READY`, `UNSUPPORTED` or `UNSAFE` scenario and affected AC is reported before execution and is not attempted",
            "explicit approval, preparation and readiness recheck before any replacement evidence",
        ):
            self.assertIn(contract_text, verification_execution_contract)
        for criterion in (
            "모든 AC가 SATISFIED -> VERIFIED",
            "하나 이상의 AC가 NOT_SATISFIED -> NOT_SATISFIED",
            "그 외 하나 이상의 AC가 UNDETERMINED -> UNDETERMINED",
        ):
            self.assertIn(criterion, verification_execution_contract)
        self.assertNotIn("LEAD_FAILURE", VERIFICATION_SKILL)
        self.assertNotIn("LEAD_FAILURE", VERIFICATION_EXECUTION_CONTRACT)

    def test_verification_skill_removes_retired_verification_role_names(self) -> None:
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
