from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ASK_MATT = (ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
GRILL_ME = (ROOT / "matt/skills/grill-me/SKILL.md").read_text(encoding="utf-8")
GRILL_DOCS = (ROOT / "matt/skills/grill-with-docs/SKILL.md").read_text(encoding="utf-8")
GRILLING = (ROOT / "matt/skills/grilling/SKILL.md").read_text(encoding="utf-8")
TO_SPEC = (ROOT / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8")
TO_TICKETS = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
IMPLEMENTATION = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
SPEC_TEMPLATE = (ROOT / "matt/examples/SPEC.template.md").read_text(encoding="utf-8")
PLANNING_WORKSPACE = (ROOT / "planning-workspace/README.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class UIPlanningDecouplingTests(unittest.TestCase):
    def test_active_ui_path_has_no_ima2_or_image_approval_dependency(self) -> None:
        active = (
            ASK_MATT,
            GRILL_ME,
            GRILL_DOCS,
            GRILLING,
            TO_SPEC,
            TO_TICKETS,
            IMPLEMENTATION,
        )
        for contract in active:
            for forbidden in (
                "ima2-uiux",
                "ima2-front",
                "image-first",
                "HOTL",
                "Final Approval Render",
                "Final approval render",
                "design-concepts",
                "terminal render disposition",
                "stale-disposition",
            ):
                self.assertNotIn(forbidden, contract)

    def test_material_ui_still_requires_complete_approved_authority(self) -> None:
        matt = normalized(ASK_MATT)
        spec = normalized(TO_SPEC)
        for required in (
            "`MATERIAL_RENDERED_UI`",
            "complete, approved local UI/UX authority",
            "Matt directly performs enough rendered-design judgment",
            "every currently determinable material user-owned rendered decision",
            "`Status: approved`",
            "`Open Questions` is `None`",
            "explicitly approves it",
        ):
            self.assertIn(required, matt)
        for required in (
            "Terminal UI / UX Authority Gate",
            "complete, approved local UI/UX authority",
            "explicit user or planning-owner approval",
            "shared understanding explicitly adopts it",
        ):
            self.assertIn(required, spec)

    def test_direct_ui_judgment_stays_in_initial_integrated_frontier(self) -> None:
        for contract, graph_phrase in (
            (GRILL_ME, "one dependency graph"),
            (GRILL_DOCS, "one dependency graph"),
            (GRILLING, "same graph"),
        ):
            body = normalized(contract)
            self.assertIn("direct UI judgment", body)
            self.assertIn("currently determinable user-owned", body)
            self.assertIn(graph_phrase, body)
        matt = normalized(ASK_MATT)
        self.assertIn("Complete this UI judgment before the first user-facing decision response", matt)
        self.assertIn("same initial dependency graph as Grill and Behavior", matt)
        self.assertIn("Do not postpone UI analysis until after the first frontier", matt)

    def test_visual_material_never_becomes_authority_by_itself(self) -> None:
        matt = normalized(ASK_MATT)
        spec = normalized(TO_SPEC)
        template = normalized(SPEC_TEMPLATE)
        self.assertIn("visual reference, style choice, default, prototype, generated concept", matt)
        self.assertIn("Only decisions explicitly adopted into `DESIGN.md` can become UI authority", matt)
        self.assertIn("visual reference, style choice, default, prototype, or generated concept alone is insufficient", spec)
        self.assertIn("Prototype, visual reference, style 선택, 생성 concept", template)

    def test_to_spec_still_fails_closed_on_missing_ui_authority_without_image_gate(self) -> None:
        body = normalized(TO_SPEC)
        self.assertIn("BLOCKED: UI / UX authority required before SPEC.md", body)
        self.assertIn("missing, incomplete, unapproved, inapplicable, or not-explicitly-adopted authority", body)
        self.assertIn("return to Matt's UI authority flow", body)
        self.assertNotIn("render disposition", body.lower())
        self.assertNotIn("image-generation", body.lower())

    def test_legacy_image_review_metadata_is_non_normative_only(self) -> None:
        self.assertIn("Legacy image-review process metadata", ASK_MATT)
        self.assertIn("New planning neither requires nor writes it", ASK_MATT)
        self.assertIn("Legacy image-review process metadata", TO_SPEC)
        self.assertIn("not required for Spec admission", normalized(TO_SPEC))

    def test_lightweight_ui_routes_remain_lightweight(self) -> None:
        matt = normalized(ASK_MATT)
        for route in ("`NON_UI`", "`ENGINEERING_ONLY`", "`BOUNDED_RENDERED_CONTRACT`"):
            self.assertIn(route, matt)
        self.assertIn("do not require a separate full `DESIGN.md`", matt)
        spec = normalized(TO_SPEC)
        self.assertIn("A bounded rendered contract does not require a separate pre-Spec `DESIGN.md`", spec)
        self.assertIn("Do not block non-UI work or an engineering-only frontend change", spec)

    def test_planning_workspace_no_longer_contracts_an_image_concept_directory(self) -> None:
        self.assertIn("DESIGN.md", PLANNING_WORKSPACE)
        self.assertIn("SPEC.md", PLANNING_WORKSPACE)
        self.assertIn("tickets/", PLANNING_WORKSPACE)
        self.assertNotIn("design-concepts/", PLANNING_WORKSPACE)


if __name__ == "__main__":
    unittest.main()
