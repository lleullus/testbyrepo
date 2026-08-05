from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")


class ActiveSkillContractTests(unittest.TestCase):
    def test_implementation_skill_names_ticket_terra_and_module_surface(self) -> None:
        self.assertIn("Ticket", IMPLEMENTATION_SKILL)
        self.assertIn("TerraWorker", IMPLEMENTATION_SKILL)
        self.assertIn("Module.implement", IMPLEMENTATION_SKILL)
        self.assertIn("private-workspace executor", IMPLEMENTATION_SKILL)
        self.assertIn("agent text cannot make that check pass", IMPLEMENTATION_SKILL)

    def test_verification_skill_names_fresh_luna_and_module_surface(self) -> None:
        self.assertIn("fresh Luna", VERIFICATION_SKILL)
        self.assertIn("Module.verify", VERIFICATION_SKILL)
        self.assertIn("Module.inspect", VERIFICATION_SKILL)
        self.assertIn("no continuation", VERIFICATION_SKILL)
        self.assertIn("Module owns observation execution", VERIFICATION_SKILL)

    def test_active_skills_exclude_retired_public_mechanism_terms(self) -> None:
        combined = (IMPLEMENTATION_SKILL + "\n" + VERIFICATION_SKILL).lower()
        for term in (
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
