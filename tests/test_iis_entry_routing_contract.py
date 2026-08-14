from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
REPO_ROUTER = ROOT / "iis-workflow/SKILL.md"
CANONICAL_ROUTER = Path("/home/user01/project/iis-skills/iis-workflow/SKILL.md")
INSTALLED_ROUTER = Path("/home/user01/.codex/skills/iis-workflow/SKILL.md")


class IISEntryRoutingContractTests(unittest.TestCase):
    def test_scope_shaper_has_entry_precedence(self) -> None:
        shaper = (ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8")
        router = REPO_ROUTER.read_text(encoding="utf-8")
        self.assertIn("Explicit Scope Shaper requests and initiative-scale IIS requests take precedence over Ask Matt", shaper)
        self.assertIn("Scope Shaper has entry precedence for initiative-scale work", router)

    def test_router_is_planning_only(self) -> None:
        body = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        for required in (
            "IIS is a planning system",
            "Scope Shaper",
            "Ask Matt",
            "To Spec",
            "To Tickets",
            "IIS PLANNING COMPLETE",
            "validated complete Ready Ticket Set",
            "Implementation and verification are outside IIS",
            "classify the request as outside IIS Planning",
        ):
            self.assertIn(required, body)
        for forbidden in (
            "iis-goal-loop/SKILL.md",
            "implementation-lead/SKILL.md",
            "verification-lead/SKILL.md",
            "verification-runner/SKILL.md",
            "goal-verification-lead/SKILL.md",
            "GOAL ACHIEVED",
        ):
            self.assertNotIn(forbidden, body)

    def test_adversarial_gate_is_preserved_as_planning_only(self) -> None:
        body = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        for required in (
            "explicit instruction to run adversarial consensus",
            "`Adversarial Planning Challenger` binding",
            "A Challenger designation alone does not activate the gate",
            "Pass an explicit user instruction to run adversarial consensus",
            "only when both the activation instruction and exact binding are current",
            "planning-only advisory counterpart",
        ):
            self.assertIn(required, body)

    def test_explicit_ticket_delivery_is_not_expanded_by_iis(self) -> None:
        body = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        self.assertIn("Do not reinterpret a request naming one exact Ticket as permission to complete sibling Tickets or the whole Spec", body)
        self.assertIn("IIS does not route or supervise that layer", body)

    def test_live_installed_router_matches_current_canonical_installation(self) -> None:
        self.assertTrue(INSTALLED_ROUTER.is_file())
        self.assertTrue(CANONICAL_ROUTER.is_file())
        self.assertEqual(INSTALLED_ROUTER.read_bytes(), CANONICAL_ROUTER.read_bytes())


if __name__ == "__main__":
    unittest.main()
