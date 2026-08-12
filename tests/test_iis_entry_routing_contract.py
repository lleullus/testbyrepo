from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPO_ROUTER = ROOT / "iis-workflow/SKILL.md"
INSTALLED_ROUTER = Path("/home/user01/.codex/skills/iis-workflow/SKILL.md")


class IISEntryRoutingContractTests(unittest.TestCase):
    def test_ask_matt_is_bounded_and_fail_closed(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ordinary bounded planning request", matt)
        self.assertIn("## Entry Routing And Scope Handoff Preflight", matt)
        self.assertIn("named initiative Scope result without one exact selected ready Work Package", matt)
        self.assertIn("ASK MATT: BLOCKED", matt)
        self.assertLess(matt.index("## Entry Routing And Scope Handoff Preflight"), matt.index("## Main Flow"))

    def test_scope_shaper_has_entry_precedence(self) -> None:
        shaper = (ROOT / "scope-shaper" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Explicit Scope Shaper requests and initiative-scale IIS requests take precedence over Ask Matt",
            shaper,
        )
        router = REPO_ROUTER.read_text(encoding="utf-8")
        self.assertIn("Scope Shaper has entry precedence for initiative-scale work", router)

    def test_repository_router_preserves_explicit_leaf_routes(self) -> None:
        router = REPO_ROUTER.read_text(encoding="utf-8")
        normalized = " ".join(router.split())
        for required in (
            "/home/user01/project/iis-skills/implementation-lead/SKILL.md",
            "/home/user01/project/iis-skills/verification-lead/SKILL.md",
            "one exact ready local Markdown Ticket",
            "exact `Project-Root`",
            "Candidate Execution Recipe is optional",
            "Do not require an Implementation Lead result",
            "independent authority, direct evidence, and an AC verdict",
            "`Operator-assisted`",
            "`Not independently verifiable`",
            "has no independent IIS verification route",
            "Do not bypass that boundary through Implementation Lead",
            "another agent",
            "compatibility command",
            "instead of selecting a fallback",
            "Apply explicit leaf requests before broad IIS inference",
        ):
            self.assertIn(required, normalized)
        for forbidden in ("verification-runtime/iis-verify", "`iis-verify`", "Primary Verifier"):
            self.assertNotIn(forbidden, router)

    def test_repository_router_routes_end_to_end_goal_to_ralph_only_after_planning(self) -> None:
        router = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        for required in (
            "/home/user01/project/iis-skills/iis-goal-loop/SKILL.md",
            "/home/user01/project/iis-skills/goal-verification-lead/SKILL.md",
            "If one exact approved Spec and its validated complete ready Ticket set already exist",
            "first run the same ordinary Scope Shaper / Ask Matt / To Spec / To Tickets leaves",
            "Each planning leaf still stops at its own normal boundary",
            "without asking the user to say \"continue\"",
            "If the user requested planning only, do not enter Ralph",
            "Only fresh whole-Spec `GOAL VERIFIED`",
        ):
            self.assertIn(required, router)

    def test_installed_router_is_byte_identical_to_repository_router(self) -> None:
        self.assertTrue(INSTALLED_ROUTER.is_file())
        self.assertEqual(INSTALLED_ROUTER.read_bytes(), REPO_ROUTER.read_bytes())


if __name__ == "__main__":
    unittest.main()
