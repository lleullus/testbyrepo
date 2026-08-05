from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")


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
        self.assertIn("same exact ready local Markdown Ticket", VERIFICATION_SKILL)
        self.assertIn("current project", VERIFICATION_SKILL)
        self.assertIn("allowed verification surface", VERIFICATION_SKILL)
        self.assertIn("Verification Lead itself designs one or", VERIFICATION_SKILL)
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
