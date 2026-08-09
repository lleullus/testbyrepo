from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class IISEntryRoutingContractTests(unittest.TestCase):
    def test_ask_matt_is_bounded_and_fail_closed(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ordinary bounded planning request", matt)
        self.assertIn("## Entry Routing And Scope Handoff Preflight", matt)
        self.assertIn("named initiative Scope result without one exact selected ready Work Package", matt)
        self.assertIn("ASK MATT: BLOCKED", matt)
        self.assertLess(
            matt.index("## Entry Routing And Scope Handoff Preflight"),
            matt.index("## Main Flow"),
        )

    def test_scope_shaper_has_entry_precedence(self) -> None:
        shaper = (ROOT / "scope-shaper" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Explicit Scope Shaper requests and initiative-scale IIS requests take precedence over Ask Matt",
            shaper,
        )


if __name__ == "__main__":
    unittest.main()
