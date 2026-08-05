from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_EXECUTION_CONTRACT = (ROOT / "PHASE-5-VERIFICATION-EXECUTION-CONTRACT.md").read_text(encoding="utf-8")


class ActiveSkillContractTests(unittest.TestCase):
    def test_implementation_skill_names_direct_subagent_and_review_contract(self) -> None:
        self.assertIn("exact ready local Markdown Ticket", IMPLEMENTATION_SKILL)
        self.assertIn("Implementation Subagent", IMPLEMENTATION_SKILL)
        self.assertIn("Host Subagent Invocation Mechanism", IMPLEMENTATION_SKILL)
        self.assertIn("current project directly", IMPLEMENTATION_SKILL)
        self.assertIn("actual project diff", IMPLEMENTATION_SKILL)
        self.assertIn("every Markdown acceptance criterion (AC)", IMPLEMENTATION_SKILL)
        self.assertIn("must not report", IMPLEMENTATION_SKILL)

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
        self.assertIn("Planning inspection is read-only", verification_skill)
        self.assertIn("must not be preserved or reused as direct AC evidence", verification_skill)
        self.assertIn("identify the prerequisites that can change whether each AC scenario is executable", verification_skill)
        for prerequisite in (
            "agent, model, thinking, tool, executable, browser, and process requirements",
            "fixtures, sentinels, failure hooks, provider targets, inputs, and isolated workspace",
            "authority, credentials, network or external effects, cleanup and readback",
            "proof method required for a universal or negative condition",
        ):
            self.assertIn(prerequisite, verification_skill)
        self.assertIn("If the user designates a `Readiness Research Agent`", verification_skill)
        self.assertIn("invoke it through the host's `Host Subagent Invocation Mechanism`", verification_skill)
        self.assertIn(
            "It must not mutate the product or environment, acquire direct evidence, select or approve scenarios, "
            "assign readiness, or decide AC verdicts",
            verification_skill,
        )
        self.assertIn("Its report is advisory; Verification Lead directly verifies every readiness fact", verification_skill)
        self.assertIn("new evidence observation", verification_skill)
        self.assertIn("`Verification Scenarios`", verification_skill)
        self.assertIn("stable scenario ID, AC", verification_skill)
        self.assertIn("procedure and verification surface", verification_skill)
        self.assertIn("Readiness is exactly one of `READY`, `NOT_READY`, `UNSUPPORTED`, or `UNSAFE`", verification_skill)
        self.assertIn("is a pre-execution fact, not an AC verdict", verification_skill)
        self.assertIn("required preparation or dependency, and authority or approval needed", verification_skill)
        self.assertIn("After directly checking every identified prerequisite", verification_skill)
        self.assertIn("explicitly approve the scenario plan and its stated preparation scope", verification_skill)
        self.assertIn("Before that approval, do not prepare the environment or acquire direct evidence", verification_skill)
        self.assertIn(
            "If the user rejects or changes the plan, revise the scenarios and readiness facts, show the complete table again, "
            "and request new approval",
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
            "Report every remaining `NOT_READY`, `UNSUPPORTED`, or `UNSAFE` scenario and its affected AC before execution; "
            "do not attempt it",
            verification_skill,
        )
        self.assertIn("`replaces <old scenario ID>` relationship", verification_skill)
        self.assertIn(
            "show the revised complete table, obtain explicit approval, prepare and recheck readiness, and only then acquire "
            "replacement evidence",
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
        self.assertIn("does not contain a final verdict", VERIFICATION_SKILL)
        self.assertIn("directly re-verifies", VERIFICATION_SKILL)
        self.assertIn("at most once", VERIFICATION_SKILL)
        self.assertIn("does not start chained remediation", VERIFICATION_SKILL)

        ordered_contract = (
            "After directly checking every identified prerequisite",
            "explicitly approve the scenario plan and its stated preparation scope",
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
            "candidate",
            "opencode worker",
            "opencode verifier",
            "terraworker",
            "fresh luna",
            "implementation-handoff",
            "verification-result",
            "actor",
            "capability",
            "claim",
            "replay",
            "verification-run",
            "workflow-store",
            "baseline capsule",
        ):
            self.assertNotIn(term, combined)


if __name__ == "__main__":
    unittest.main()
