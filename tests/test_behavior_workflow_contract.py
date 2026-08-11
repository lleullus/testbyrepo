from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class BehaviorWorkflowContractTests(unittest.TestCase):
    def test_behavior_design_is_mandatory_matt_performed_and_project_local(self) -> None:
        lead = (ROOT / "behavior-design-lead" / "SKILL.md").read_text(encoding="utf-8")
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Every Matt planning unit uses this same procedure", lead)
        self.assertIn("Matt directly performs this complete phase", lead)
        self.assertIn("This phase has no\nseparate execution role or context", lead)
        self.assertIn("docs/planning/behavior/", lead)
        self.assertIn("Every Matt planning unit must complete", matt)
        self.assertIn("Matt directly reads and performs the complete canonical leaf", matt)
        self.assertIn("the phase has no separate execution role or context", matt)
        for heading in (
            "## Existing Authority First",
            "## Lead-First Investigation",
            "## Behavioral Design",
            "## Counterexample Stress Test",
            "## Product Decision Synthesis",
            "## Authority Output",
            "## Completion",
        ):
            self.assertIn(heading, lead)
        for contract in (lead, matt):
            self.assertNotIn("Behavior subagent", contract)
            self.assertNotIn("subagent invocation mechanism", contract)
            self.assertNotIn("separate lead context", contract)

    def test_spec_ticket_and_implementation_consume_behavior_authority(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        implementation = (ROOT / "implementation-lead" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Behavior Authority Gate", to_spec)
        self.assertIn("## Behavior Authorities", to_spec)
        self.assertIn("## Behavior authority rules", to_tickets)
        self.assertNotIn("criterionRawSha256", to_tickets)
        self.assertNotIn("Verification Assessor", to_tickets)
        self.assertIn("compound direct implementation contract", implementation)
        for contract in (to_spec, to_tickets, implementation):
            self.assertIn("canonical parent", contract)
            self.assertIn("behavior/contexts/", contract)
            self.assertIn("lifecycles/", contract)
            self.assertIn("invariants/", contract)

    def test_ui_authority_reaches_implementation_and_is_revalidated(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        implementation = (ROOT / "implementation-lead" / "SKILL.md").read_text(encoding="utf-8")
        for producer in (to_spec, to_tickets):
            self.assertIn("complete", producer)
            self.assertIn("approved", producer)
        for lead in (implementation,):
            normalized = " ".join(lead.split())
            for required in (
                "UI: yes",
                "same canonical target",
                "Status: approved",
                "applicable rendered",
                "Open Questions: None",
                "MATERIAL_RENDERED_UI",
                "bounded parent-Spec",
            ):
                self.assertIn(required, normalized)
            self.assertIn("UI: no", normalized)

    def test_ui_authority_blocks_unresolved_or_incomplete_approved_content(self) -> None:
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        implementation = (ROOT / "implementation-lead" / "SKILL.md").read_text(encoding="utf-8")
        for lead in (to_tickets, implementation):
            normalized = " ".join(lead.split())
            self.assertIn("complete", normalized)
            self.assertIn("no unresolved", normalized)
            self.assertIn("incomplete", normalized)
            self.assertIn("Owner:", normalized)
            self.assertIn("Scope:", normalized)
            self.assertIn("Open Questions: None", normalized)
            self.assertIn("terminal disposition", normalized)

    def test_behavior_approval_state_precedes_completion_without_unlocking_spec(self) -> None:
        lead = (ROOT / "behavior-design-lead" / "SKILL.md").read_text(encoding="utf-8")
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("BEHAVIOR AUTHORITY APPROVAL REQUIRED", lead)
        self.assertIn("never permits `to-spec`", lead)
        self.assertIn("BEHAVIOR AUTHORITY APPROVAL REQUIRED", matt)
        self.assertIn("pre-completion approval state", matt)

    def test_batch_adapter_is_explicit_only(self) -> None:
        adapter = (ROOT / "matt" / "skills" / "batch-grill-me" / "SKILL.md").read_text(encoding="utf-8")
        grilling = (ROOT / "matt" / "skills" / "grilling" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("explicit-only IIS interaction adapter", adapter)
        self.assertIn("does not activate it", adapter)
        self.assertIn("Never infer, default to, or fall back", grilling)

    def test_questions_follow_initial_integrated_analysis_without_late_rounds(self) -> None:
        lead = (ROOT / "behavior-design-lead" / "SKILL.md").read_text(encoding="utf-8")
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        grilling = (ROOT / "matt" / "skills" / "grilling" / "SKILL.md").read_text(encoding="utf-8")
        batch = (ROOT / "matt" / "skills" / "batch-grill-me" / "SKILL.md").read_text(encoding="utf-8")
        normalized_grilling = " ".join(grilling.split())
        self.assertIn("before Matt's first user-facing decision", lead)
        self.assertIn("not a separate user-facing stage", lead)
        self.assertIn("Before the first decision response", matt)
        self.assertIn("whole current frontier in this response", grilling)
        self.assertIn("Late fact-finding, late Behavior analysis", normalized_grilling)
        self.assertIn("late Behavior analysis never creates a valid Batch", batch)
        for contract in (lead, matt, grilling):
            self.assertIn("newly identifiable", contract)

    def test_scope_package_frame_and_ui_decisions_join_the_first_frontier(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        grill_me = (ROOT / "matt" / "skills" / "grill-me" / "SKILL.md").read_text(encoding="utf-8")
        grill_docs = (
            ROOT / "matt" / "skills" / "grill-with-docs" / "SKILL.md"
        ).read_text(encoding="utf-8")
        grilling = (ROOT / "matt" / "skills" / "grilling" / "SKILL.md").read_text(encoding="utf-8")
        shaper = (ROOT / "scope-shaper" / "SKILL.md").read_text(encoding="utf-8")
        brief = (
            ROOT
            / "scope-shaper"
            / "templates"
            / "WORK-PACKAGE.template.md"
        ).read_text(encoding="utf-8")
        self.assertIn("before the\nfirst user-facing decision response", matt)
        self.assertIn("Grill, Behavior, UI, and applicable Scope Shaper package-frame decisions", matt)
        self.assertIn("later explicit user action naming the", shaper)
        self.assertIn("first integrated frontier", " ".join(brief.split()))
        for contract in (grill_me, grill_docs, grilling):
            normalized = " ".join(contract.split())
            self.assertIn("Central UI / UX Routing", normalized)
            self.assertIn("ima2-uiux", contract)


if __name__ == "__main__":
    unittest.main()
