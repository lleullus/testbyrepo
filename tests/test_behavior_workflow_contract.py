from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class BehaviorWorkflowContractTests(unittest.TestCase):
    def test_behavior_lead_is_mandatory_independent_and_project_local(self) -> None:
        lead = (ROOT / "behavior-design-lead" / "SKILL.md").read_text(encoding="utf-8")
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        normalized_matt = " ".join(matt.split())
        self.assertIn("Every Matt planning unit uses this same procedure", lead)
        self.assertIn("host's subagent invocation mechanism", lead)
        self.assertIn("must not simulate the role inline", lead)
        self.assertIn("docs/planning/behavior/", lead)
        self.assertIn("Every Matt planning unit must run", matt)
        self.assertIn("must not perform the leaf inline", normalized_matt)

    def test_spec_ticket_and_leads_consume_behavior_authority(self) -> None:
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")
        implementation = (ROOT / "implementation-lead" / "SKILL.md").read_text(encoding="utf-8")
        verification = (ROOT / "verification-lead" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Behavior Authority Gate", to_spec)
        self.assertIn("## Behavior Authorities", to_spec)
        self.assertIn("## Behavior authority rules", to_tickets)
        self.assertNotIn("criterionRawSha256", to_tickets)
        self.assertNotIn("Verification Assessor", to_tickets)
        self.assertIn("compound direct implementation contract", implementation)
        self.assertIn("Ticket-declared Behavior", verification)
        for contract in (to_spec, to_tickets, implementation, verification):
            self.assertIn("canonical parent", contract)
            self.assertIn("behavior/contexts/", contract)
            self.assertIn("lifecycles/", contract)
            self.assertIn("invariants/", contract)

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


if __name__ == "__main__":
    unittest.main()
