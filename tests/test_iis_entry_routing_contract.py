from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
REPO_ROUTER = ROOT / "iis-workflow/SKILL.md"
CANONICAL_ROUTER = Path("/home/user01/project/iis-skills/iis-workflow/SKILL.md")
INSTALLED_ROUTER = Path("/home/user01/.codex/skills/iis-workflow/SKILL.md")


class IISEntryRoutingContractTests(unittest.TestCase):
    def test_generic_iis_is_not_ask_matt_alias(self) -> None:
        body = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        self.assertIn('A generic request to "start the IIS workflow" is not an alias for Ask Matt', body)
        self.assertIn("next-increment-ready", body)
        self.assertIn("coherent outcomes that still require choosing what should exist first", body)
        self.assertIn("route directly to Ask Matt only when", body)

    def test_scope_shaper_has_construction_selection_precedence(self) -> None:
        shaper = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        router = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        self.assertIn("choose exactly one durable next product construction Increment", shaper)
        self.assertIn("Scope Shaper has entry precedence whenever the next durable construction increment still has to be selected", router)

    def test_current_planning_state_check_is_read_only_and_stops(self) -> None:
        router = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        for required in (
            "Current Planning State Check",
            "read-only status inspection",
            "Treat `Status: done` Tickets as completed delivery units",
            "A prior Increment with `Status: superseded` is historical planning state",
            "does not block reporting the current planning position",
            "report that exact Increment and `Ask Matt` as the next leaf",
            "report that Work Package as the next candidate area and `Scope Shaper` as the leaf",
            "After reporting the state and next pointer, **STOP**",
            "Do not invoke or execute Scope Shaper, Ask Matt, To Spec, To Tickets",
        ):
            self.assertIn(required, router)

        for forbidden in (
            "IIS CONTINUATION: DELIVERY REMAINS",
            "IIS CONTINUATION: ARTIFACT REPAIR REQUIRED",
            "route to Scope Shaper for a fresh actual-product reinspection",
        ):
            self.assertNotIn(forbidden, router)

    def test_explicit_ask_matt_keeps_leaf_but_not_admission_bypass(self) -> None:
        router = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        matt = " ".join((ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("An explicit Ask Matt request enters Ask Matt's own admission preflight", router)
        self.assertIn("it does not waive this admission contract", matt)
        self.assertIn("ASK MATT: SCOPE SHAPING REQUIRED", matt)

    def test_unrooted_greenfield_can_shape_before_project_root_exists(self) -> None:
        shaper = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Unrooted greenfield", shaper)
        self.assertIn("is not blocked merely because the root does not exist yet", shaper)
        self.assertIn("SCOPE SHAPING: PROJECT ROOT REQUIRED FOR ARTIFACTS", shaper)
        self.assertIn("without a second approval ceremony", shaper)
        self.assertIn("IIS does not create the project root or bootstrap product source", shaper)
        self.assertIn("A supplied but unavailable project root returns `SCOPE SHAPING: BLOCKED`", shaper)

    def test_scope_runners_are_explicit_user_authority_only(self) -> None:
        shaper_raw = (ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8")
        shaper = " ".join(shaper_raw.split())
        runner = (ROOT / "scope-investigation-runner/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("A Lead-only shaping pass requires no Investigation Runner roster", shaper)
        self.assertIn("only when the user has explicitly authorized Runner use", shaper)
        self.assertIn("Never infer, select, substitute, expand, or reorder Runner identities", shaper)
        self.assertIn("Terminal Status: COMPLETED | BLOCKED | FAILED | TIMEOUT | INVALID_REPORT", shaper)
        self.assertIn("Question Resolution: VERIFIED_FROM_REPORT | LEAD_DIRECT | NO_LONGER_MATERIAL | UNRESOLVED", shaper)
        canonical_field = "Why the answer can change the planning boundary:"
        self.assertIn(canonical_field, shaper_raw)
        self.assertIn(canonical_field, runner)

    def test_router_is_planning_only_and_increment_terminal(self) -> None:
        body = " ".join(REPO_ROUTER.read_text(encoding="utf-8").split())
        for required in (
            "IIS is a planning system",
            "Scope Shaper",
            "Ask Matt",
            "To Spec",
            "To Tickets",
            "IIS CURRENT INCREMENT PLANNING COMPLETE",
            "Implementation and verification are outside IIS",
            "classify the request as outside IIS Planning",
            "Do not automatically continue into implementation, verification, or planning of a later increment",
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
