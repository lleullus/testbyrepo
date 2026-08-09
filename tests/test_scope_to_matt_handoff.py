from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ScopeToMattHandoffTests(unittest.TestCase):
    def test_handoff_uses_canonical_validator_and_transfers_only_scope_authority(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "scope-shaper/tools/validate_scope_result.py",
            "selected-Work-Package raw-path gate",
            "Status: confirmed",
            "Planning-Shape: bounded",
            "Status: ready-for-matt",
            "Suggested-Work-Slug",
            "Planning Boundary",
            "Planning Constraints",
            "Decisions Reserved For Matt",
            "Delivery Context only as non-normative evidence",
        ):
            self.assertIn(required, matt)

    def test_invalid_handoffs_stop_before_planning(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(matt.split())
        self.assertIn("Draft, invalid, unresolved, wrong-project", normalized)
        self.assertIn("deferred, or drifted sources or packages", normalized)
        self.assertIn("do not begin the normal flow", normalized)


if __name__ == "__main__":
    unittest.main()
