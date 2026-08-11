from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTALLED_ROUTER = Path("/home/user01/.codex/skills/iis-workflow/SKILL.md")


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

    def test_independent_verification_is_explicitly_unsupported(self) -> None:
        router = INSTALLED_ROUTER.read_text(encoding="utf-8")
        normalized = " ".join(router.split())
        self.assertIn(
            "IIS does not provide independent Ticket verification. Only an "
            "Implementation Lead result is supported; it is not an independent "
            "verification result or AC verdict.",
            normalized,
        )
        for required in (
            "Do not dispatch a child",
            "select another agent",
            "route to Implementation Lead",
            "provide a compatibility command",
            "approximate the removed action with implementation checks",
        ):
            self.assertIn(required, normalized)
        for forbidden in (
            "verification-lead/SKILL.md",
            "verification-runtime/iis-verify",
            "`iis-verify`",
            "Primary Verifier",
        ):
            self.assertNotIn(forbidden, router)


if __name__ == "__main__":
    unittest.main()
