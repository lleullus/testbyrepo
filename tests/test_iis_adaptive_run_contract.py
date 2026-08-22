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
        self.assertIn(
            "A fully derived `CLOSED` form proceeds without another approval prompt only when",
            contract,
        )

    def test_explicit_run_contract_approval_gate_is_local_and_direct_user_only(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        coexistence = (ADAPTIVE / "references" / "00-baseline-coexistence.md").read_text(
            encoding="utf-8"
        )
        delegated = (ADAPTIVE / "references" / "02-delegated-decision-policy.md").read_text(
            encoding="utf-8"
        )
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        template = (ADAPTIVE / "templates" / "ADAPTIVE-RUN-CONTRACT.template.md").read_text(
            encoding="utf-8"
        )
        mandate = (ADAPTIVE / "references" / "01-mandate-contract.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Run Contract Approval Gate: required | not_required", template)
        self.assertIn("`/승인게이트`", skill)
        self.assertIn("`/승인게이트`", coexistence)
        self.assertIn("quoted, explanatory, hypothetical, or negated", contract)
        self.assertIn("does not activate Adaptive by itself", contract)
        self.assertIn("Run Contract-local execution release only", contract)
        self.assertIn("standing delegation cannot satisfy this gate", contract)
        self.assertIn("Run Contract Approval Gate explicitly activated", delegated)
        self.assertIn(
            "direct user approval of the exact rendered current `CLOSED` Run Contract",
            delegated,
        )
        self.assertIn(
            "does not add Mandate, Scope, Ask Matt, Spec, Ticket, implementation, or verification approval gates",
            template,
        )
        self.assertNotIn("Run Contract Approval Gate", mandate)
        self.assertNotIn("Run Contract Approval Gate", continuation)

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
        self.assertNotIn("IIS ADAPTIVE MANDATE COMPLETE", terminal)
        self.assertIn("every current canonical Ticket", continuation)

    def test_default_adaptive_execution_closes_at_current_increment_delivery(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )

        for text in (skill, contract, continuation):
            self.assertIn("Implementation: yes", text)
            self.assertIn("Verification: yes", text)
            self.assertIn("CURRENT_INCREMENT_DELIVERED", text)

        self.assertIn("default current-Increment terminal", contract)
        self.assertIn("Required-item coverage invariant", contract)
        self.assertIn("broader outcome", contract)

    def test_post_delivery_dispositions_are_closed_and_consistent(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        terminal = (ADAPTIVE / "references" / "07-terminal-report.md").read_text(
            encoding="utf-8"
        )
        artifact = (ADAPTIVE / "references" / "05-artifact-contract.md").read_text(
            encoding="utf-8"
        )

        dispositions = (
            "RUN_CONTRACT_SATISFIED",
            "NEXT_INCREMENT_REQUIRED",
            "USER_DECISION_REQUIRED",
            "EVIDENCE_REQUIRED",
        )
        for disposition in dispositions:
            self.assertIn(disposition, skill)
            self.assertIn(disposition, continuation)
            self.assertIn(disposition, terminal)

        self.assertIn("RUN_CONTRACT_SATISFIED", artifact)
        self.assertNotIn("MANDATE_SATISFIED", skill)
        self.assertNotIn("MANDATE_SATISFIED", continuation)
        self.assertNotIn("MANDATE_SATISFIED", terminal)

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

    def test_required_scope_boundary_scenarios_and_post_shape_revalidation(self) -> None:
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )

        expected = {
            "WHOLE_REQUIRED_NO_INCREMENT": (
                "current-Increment coverage is not established",
                "`CLOSED` is forbidden",
            ),
            "WHOLE_REQUIRED_FOUNDATION_INCREMENT": (
                "foundation/partial Increment",
                "`CONTRACT_DRIFT`",
            ),
            "CURRENT_INCREMENT_REQUIRED_ONLY": (
                "every unsatisfied Required Named Item is covered",
                "current-Increment boundary is allowed",
            ),
            "WHOLE_REQUIRED_BOUNDED_OUTCOME": (
                "`BOUNDED_OUTCOME_SATISFIED`",
                "preserving outer Required Named Items",
            ),
            "LEAF_APPROVAL_ONLY": (
                "owning leaf approval/confirmation",
                "Run Completion Boundary, and Completion Predicate remain unchanged",
            ),
            "DEFAULT_ADAPTIVE_CURRENT_INCREMENT": (
                "no narrower stop",
                "`CURRENT_INCREMENT_DELIVERED` as the default current-Increment terminal",
            ),
            "REQUIRED_REMAINS_AFTER_DELIVERY": (
                "current Increment is delivered",
                "`RUN_COMPLETE` is forbidden",
            ),
            "POST_DELIVERY_EVIDENCE_GAP": (
                "authoritative readback cannot determine satisfaction",
                "return `EVIDENCE_REQUIRED`",
            ),
        }

        rows: dict[str, tuple[str, str]] = {}
        for line in contract.splitlines():
            stripped = line.strip()
            if not stripped.startswith("| `"):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) != 3:
                continue
            scenario = cells[0].strip("`")
            if scenario in expected:
                self.assertNotIn(scenario, rows)
                rows[scenario] = (cells[1], cells[2])

        self.assertEqual(set(rows), set(expected))
        for scenario, (condition_fragment, result_fragment) in expected.items():
            condition, result = rows[scenario]
            self.assertIn(condition_fragment, condition)
            self.assertIn(result_fragment, result)
            self.assertEqual(contract.count(f"| `{scenario}` |"), 1)

        self.assertIn(
            "A form is `CLOSED` only when satisfying its Run Completion Boundary",
            contract,
        )
        self.assertIn("required-item coverage is unknown or partial", contract)
        self.assertIn(
            "A broader ceiling does not silently upgrade a narrower active boundary",
            contract,
        )
        self.assertIn(
            "is leaf-local and is not by itself an outer Run Contract revision",
            contract,
        )
        self.assertIn("#### Post-shape Run Contract revalidation", routing)
        self.assertIn(
            "Repeat the same revalidation whenever a material reshape changes",
            routing,
        )
        self.assertIn("do not enter Ask Matt", routing)

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
        self.assertIn("CURRENT_INCREMENT_DELIVERED by default", agent)
        self.assertIn("whole-run completion", agent)


if __name__ == "__main__":
    unittest.main()
