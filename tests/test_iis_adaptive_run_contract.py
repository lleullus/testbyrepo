from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "iis-adaptive-planning"


class IISAdaptiveRunContractTests(unittest.TestCase):
    def test_run_contract_closes_before_first_mutation_without_form_ceremony(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        template = (ADAPTIVE / "templates" / "ADAPTIVE-RUN-CONTRACT.template.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Before the first Adaptive planning mutation", skill)
        self.assertIn("Status: CLOSED | USER_INPUT_REQUIRED", template)
        self.assertIn("do not ask the user to restate", contract.lower())
        self.assertIn("ask only for the smallest unresolved field", contract)
        self.assertIn("A fully derived `CLOSED` form proceeds without another approval prompt", contract)

    def test_run_contract_is_an_exact_adaptive_delta_before_routing(self) -> None:
        coexistence = (ADAPTIVE / "references" / "00-baseline-coexistence.md").read_text(
            encoding="utf-8"
        )
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Run Contract closure and terminal discipline", coexistence)
        self.assertIn("Run Contract admission precedes routing", routing)
        self.assertIn("hard STOP before mutation", routing)
        self.assertIn("does not alter ordinary IIS requests", routing)

    def test_mixed_required_and_candidate_items_are_lossless(self) -> None:
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        template = (ADAPTIVE / "templates" / "ADAPTIVE-RUN-CONTRACT.template.md").read_text(
            encoding="utf-8"
        )
        reshape = (ADAPTIVE / "references" / "04-increment-reshaping.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Required Named Items", template)
        self.assertIn("## Candidate Named Items", template)
        self.assertIn("## Required Item Policy", template)
        self.assertIn("Required Named Items: A, B", contract)
        self.assertIn("Candidate Named Items: C", contract)
        self.assertIn("Required and candidate lists may coexist", contract)
        self.assertIn("No item may appear in both lists", contract)
        self.assertIn("must remain mixed", reshape)
        self.assertNotIn("## Named Item Semantics", template)

    def test_implementation_and_verification_are_independent(self) -> None:
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        template = (ADAPTIVE / "templates" / "ADAPTIVE-RUN-CONTRACT.template.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Implementation: yes | no", template)
        self.assertIn("Verification: yes | no", template)
        self.assertIn("implement but do not verify -> `yes` / `no`", contract)
        self.assertIn("CURRENT_INCREMENT_IMPLEMENTED", contract)
        self.assertIn("do not verify -> never run the verifier or claim `done`", contract)
        self.assertIn("do not verify", continuation)
        self.assertIn("no success re-entry into another Increment", continuation)
        self.assertNotIn("PLANNING_ONLY | PLAN_IMPLEMENT_VERIFY", template)

    def test_run_completion_boundary_prevents_smaller_phase_from_claiming_success(self) -> None:
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        terminal = (ADAPTIVE / "references" / "07-terminal-report.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )

        for value in (
            "READY_TICKET_SET",
            "CURRENT_INCREMENT_IMPLEMENTED",
            "CURRENT_INCREMENT_DELIVERED",
            "NAMED_REQUIRED_ITEMS_DELIVERED",
            "BOUNDED_OUTCOME_SATISFIED",
            "MANDATE_OUTCOME_SATISFIED",
        ):
            self.assertIn(value, contract)
            self.assertIn(value, continuation)

        self.assertIn("Planning phase completion is not Adaptive run completion", contract)
        self.assertIn("IIS ADAPTIVE PLANNING PHASE COMPLETE", terminal)
        self.assertIn("IIS ADAPTIVE CURRENT INCREMENT IMPLEMENTED", terminal)
        self.assertIn("IIS ADAPTIVE RUN COMPLETE", terminal)
        self.assertIn("every current canonical Ticket", continuation)

    def test_mandate_continuation_authority_is_a_ceiling_not_the_run_terminal(self) -> None:
        mandate = (ADAPTIVE / "references" / "01-mandate-contract.md").read_text(
            encoding="utf-8"
        )
        mandate_template = (
            ADAPTIVE / "templates" / "ADAPTIVE-PLANNING-MANDATE.template.md"
        ).read_text(encoding="utf-8")
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("maximum success-continuation ceiling", mandate)
        self.assertIn("not the actual terminal of the current invocation", mandate)
        self.assertIn("Run Completion Boundary and Completion Predicate", mandate)
        self.assertIn("maximum authorized success-continuation ceiling", mandate_template)
        self.assertIn("Mandate Continuation Authority: CURRENT_INCREMENT", contract)
        self.assertIn("This form is not `CLOSED`", contract)
        self.assertIn("revise/adopt the Mandate before mutation", contract)
        self.assertNotIn("the success boundary after a delivered current Increment", mandate)

    def test_run_contract_is_invocation_local_not_persistent_controller_state(self) -> None:
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        artifact = (ADAPTIVE / "references" / "05-artifact-contract.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("not a required third durable companion artifact", artifact)
        self.assertIn("invocation-local authority", contract)
        self.assertIn("workflow database", contract)
        self.assertIn("Do not add the form to canonical IIS artifacts", artifact)

    def test_default_prompt_preserves_defaults_without_erasing_overrides(self) -> None:
        agent = (ADAPTIVE / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("close the invocation-local Adaptive Run Contract", agent)
        self.assertIn("Required Named Items distinct from Candidate Named Items", agent)
        self.assertIn("Implementation and Verification independently", agent)
        self.assertIn("both yes by default unless I override either stage", agent)
        self.assertIn("whole-run completion", agent)


if __name__ == "__main__":
    unittest.main()
