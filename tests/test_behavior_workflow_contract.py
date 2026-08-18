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

    def test_spec_and_ticket_preserve_behavior_authority(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Behavior Authority Gate", to_spec)
        self.assertIn("## Behavior Authorities", to_spec)
        self.assertIn("## Behavior authority rules", to_tickets)
        self.assertNotIn("criterionRawSha256", to_tickets)
        self.assertNotIn("Verification Assessor", to_tickets)
        for contract in (to_spec, to_tickets):
            self.assertIn("canonical parent", contract)
            self.assertIn("behavior/contexts/", contract)
            self.assertIn("lifecycles/", contract)
            self.assertIn("invariants/", contract)

    def test_matt_closes_verification_feasibility_before_to_spec(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(matt.split())
        for required in (
            "verification-feasibility decisions",
            "acceptance boundary",
            "authoritative readback",
            "Independent",
            "Operator-assisted",
            "Not independently verifiable",
            "Ticket-Scope-owned product behavior",
            "confirmed delivery contract",
            "source, artifact, document, or structure claim",
        ):
            self.assertIn(required, normalized)
        self.assertLess(
            normalized.index("close the verification-feasibility decisions"),
            normalized.index("Use `to-spec` when"),
        )
        self.assertIn("must not be forced through a runtime command", normalized)
        self.assertIn("never the normative product boundary or authoritative readback", normalized)
        self.assertIn("do not infer a sandbox", normalized)
        self.assertIn("turn user approval into evidence", normalized)

    def test_to_spec_serializes_confirmed_verification_without_invention(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(to_spec.split())
        for label in (
            "Outcome:",
            "Acceptance boundary:",
            "Trigger or inspection target:",
            "Expected observable result:",
            "Authoritative readback:",
            "Disposition:",
            "Independent verification required:",
            "Acceptance surface:",
            "External condition:",
        ):
            self.assertIn(label, to_spec)
        self.assertIn("Do not invent a value omitted by the confirmed shared understanding", normalized)
        self.assertIn("keeps the Spec draft", normalized)
        self.assertIn("`Not available` is not a placeholder", normalized)
        self.assertIn("cannot be combined with `Operator-assisted`", normalized)
        self.assertIn("Delivery contract guarantees", normalized)
        self.assertIn("actually guarantees the named disposable target", normalized)
        self.assertIn("not permission to infer a sandbox", normalized)
        self.assertIn("do not add a runtime command", normalized)
        for forbidden_authority in ("Internal tests", "mocks", "private helpers"):
            self.assertIn(forbidden_authority, to_spec)

    def test_to_spec_rejects_historical_only_goal_clauses(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(to_spec.split())
        for required in (
            "Every normative Goal-level clause must also be decidable during fresh completion verification",
            "current authoritative product, canonical artifact, source, approved operator-owned readback",
            "historical implementation steps, implementation reports, diffs, or prior execution records",
            "must not be approved as a Goal-level Requirement, Non-Goal, or Implementation Constraint",
            "Move a bounded mutation restriction to the applicable Ticket Scope or Non-Goals",
            "Do not weaken fresh completion verification or introduce a durable history mechanism",
        ):
            self.assertIn(required, normalized)

    def test_to_tickets_projects_without_strengthening_or_semantic_validation(self) -> None:
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(to_tickets.split())
        for required in (
            "one-based locators",
            "current positional locators, not outcome names, AC names, rule IDs, persistent IDs",
            "`Parent outcome ordinal`",
            "`Behavior authority ordinals`",
            "return the Ticket to `draft`",
            "without making it stronger, more solution-specific",
            "must not introduce a new product precondition",
            "does not judge product semantics",
            "Behavior-to-flow semantic correctness",
            "material flow merge/split",
            "runtime availability, evidence, or verdicts",
            "validate_ticket_set.py",
            "collectively cover every current parent-Spec Verification Expectation",
            "not silently treated as `Independent`",
        ):
            self.assertIn(required, normalized)
        for forbidden_surface in (
            "internal test command",
            "mock",
            "private helper",
        ):
            self.assertIn(forbidden_surface, normalized)

    def test_spec_and_ticket_self_review_are_leaf_local_transition_guards(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Self-review is a leaf-local transition guard", to_spec)
        self.assertIn("By default, change the exact status value to `approved`", to_spec)
        self.assertIn("whole-Set review", to_tickets)
        self.assertIn("structural validator on every exact draft candidate", to_tickets)
        self.assertIn("one bounded readiness", to_tickets)
        self.assertIn("restore only Tickets", to_tickets)
        for text in (to_spec, to_tickets):
            self.assertNotIn("self-reviewing", text)
            self.assertNotIn("review-failed", text)
            self.assertNotIn("approval ledger", text)

    def test_ui_authority_reaches_ready_ticket(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        for producer in (to_spec, to_tickets):
            self.assertIn("complete", producer)
            self.assertIn("approved", producer)
        normalized = " ".join(to_tickets.split())
        for required in (
            "UI: yes",
            "same canonical UI authority target",
            "Open Questions: None",
        ):
            self.assertIn(required, normalized)
        self.assertIn("UI: yes | no", normalized)

    def test_ui_authority_blocks_unresolved_or_incomplete_approved_content(self) -> None:
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(to_tickets.split())
        self.assertIn("complete", normalized)
        self.assertIn("no unresolved", normalized)
        self.assertIn("incomplete", normalized)
        self.assertIn("Owner:", normalized)
        self.assertIn("Scope:", normalized)
        self.assertIn("Open Questions: None", normalized)

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

    def test_scope_increment_frame_and_ui_decisions_join_the_first_frontier(self) -> None:
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        grill_me = (ROOT / "matt" / "skills" / "grill-me" / "SKILL.md").read_text(encoding="utf-8")
        grill_docs = (
            ROOT / "matt" / "skills" / "grill-with-docs" / "SKILL.md"
        ).read_text(encoding="utf-8")
        grilling = (ROOT / "matt" / "skills" / "grilling" / "SKILL.md").read_text(encoding="utf-8")
        shaper = (ROOT / "scope-shaper" / "SKILL.md").read_text(encoding="utf-8")
        increment = (
            ROOT
            / "scope-shaper"
            / "templates"
            / "INCREMENT.template.md"
        ).read_text(encoding="utf-8")
        self.assertIn("before the first user-facing decision response", " ".join(matt.split()))
        self.assertIn("Grill, Behavior, UI, and applicable Scope Shaper Increment-frame decisions", matt)
        self.assertIn("later explicit user action naming the", shaper)
        self.assertIn("Plan only this Increment", increment)
        for contract in (grill_me, grill_docs, grilling):
            normalized = " ".join(contract.split())
            self.assertIn("Central UI / UX Routing", normalized)
            self.assertIn("direct UI judgment", normalized)
            self.assertIn("currently determinable user-owned", normalized)


if __name__ == "__main__":
    unittest.main()
