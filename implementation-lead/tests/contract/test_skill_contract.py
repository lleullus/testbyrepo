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

    def test_verification_skill_names_fresh_direct_evidence_contract(self) -> None:
        self.assertIn("same exact ready local Markdown Ticket", VERIFICATION_SKILL)
        self.assertIn("Fresh Verification Subagent", VERIFICATION_SKILL)
        self.assertIn("Host Subagent Invocation Mechanism", VERIFICATION_SKILL)
        self.assertIn("do not provide the Implementation Lead's or Implementation Subagent's", VERIFICATION_SKILL)
        self.assertIn("narration or conclusions at all", VERIFICATION_SKILL)
        self.assertIn("read-only", VERIFICATION_SKILL)
        self.assertIn("exactly one result row for every Markdown AC", VERIFICATION_SKILL)
        for status in ("SATISFIED", "NOT_SATISFIED", "UNDETERMINED"):
            self.assertIn(status, VERIFICATION_SKILL)
        self.assertIn("direct evidence", VERIFICATION_SKILL)

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
