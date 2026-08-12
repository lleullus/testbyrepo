from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL = (ROOT / "goal-verification-lead/SKILL.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class GoalVerificationLeadContractTests(unittest.TestCase):
    def test_spec_is_completion_authority_and_ticket_results_are_navigation_only(self) -> None:
        body = normalized(SKILL)
        for required in (
            "The approved Spec is the completion authority",
            "ready Ticket set supplies only current decomposition",
            "Ticket verdicts, implementation results, tests, candidate recipes, prior product observations",
            "do not supply final Goal evidence",
            "Do not require an Implementation Lead result",
        ):
            self.assertIn(required, body)

    def test_denominator_covers_each_spec_outcome_and_global_contract(self) -> None:
        body = normalized(SKILL)
        for required in (
            "exactly one row for every current top-level parent-Spec `## Verification Expectations` item",
            "one `Global Contract` row",
            "Requirement, Non-Goal, Implementation Constraint, adopted Behavior obligation",
            "UI obligation, preserved invariant, and delivery boundary",
            "invocation-local obligation-closure audit",
            "no current normative clause is omitted",
        ):
            self.assertIn(required, body)

    def test_historical_only_clause_blocks_final_verification(self) -> None:
        body = normalized(SKILL)
        for required in (
            "historical implementation steps",
            "Worker/Lead reports",
            "old diffs",
            "prior execution records",
            "`GOAL VERIFICATION NOT STARTED`",
            "do not weaken the clause",
            "invent a durable history mechanism",
        ):
            self.assertIn(required, body)

    def test_final_evidence_is_fresh_and_direct(self) -> None:
        body = normalized(SKILL)
        for required in (
            "Obtain evidence now from the current authoritative boundary",
            "current product result and authoritative readback",
            "direct current canonical source/artifact/document inspection",
            "current rendered UI state and interaction readback",
            "Ticket verifier rows",
            "cannot supply a final `PASS`",
            "Tests passing alone never decide an outcome",
        ):
            self.assertIn(required, body)

    def test_operator_assisted_keeps_verdict_with_verifier(self) -> None:
        body = normalized(SKILL)
        for required in (
            "operator performs only the exact approved action",
            "operator-owned readback",
            "operator never interprets an AC or Goal obligation",
            "This leaf reads the current readback and owns the verdict",
            "affected row is `INCONCLUSIVE`",
        ):
            self.assertIn(required, body)

    def test_not_independently_verifiable_cannot_achieve_goal(self) -> None:
        body = normalized(SKILL)
        self.assertIn("The affected outcome is always `INCONCLUSIVE`", body)
        self.assertIn("it can never contribute to `GOAL VERIFIED`", body)

    def test_aggregate_is_closed_and_only_all_pass_verifies(self) -> None:
        body = SKILL
        self.assertIn("all rows PASS                    -> GOAL VERIFIED", body)
        self.assertIn("one or more rows FAIL            -> GOAL FAILED", body)
        self.assertIn("otherwise                        -> GOAL INCONCLUSIVE", body)
        self.assertIn("No other result is allowed to mean completion", normalized(body))

    def test_current_authority_chain_is_revalidated_before_product_observation(self) -> None:
        body = normalized(SKILL)
        for required in (
            "freshly revalidate the authority chain",
            "same canonical project-local authority target",
            "remains readable and `Status: approved`",
            "required terminal render disposition",
            "Authority-chain drift is a planning/admission defect",
            "`GOAL VERIFICATION NOT STARTED`",
        ):
            self.assertIn(required, body)

    def test_fresh_verification_prefers_current_readback_over_replaying_effects(self) -> None:
        body = normalized(SKILL)
        for required in (
            "fresh current read of the approved authoritative boundary",
            "does not require replaying a product effect",
            "Prefer that current readback over duplicating an effect",
            "Re-trigger only when the approved verification contract actually requires it",
        ):
            self.assertIn(required, body)

    def test_non_pass_rows_identify_exact_obligation_and_current_candidate_ownership(self) -> None:
        body = normalized(SKILL)
        for required in (
            "Exact obligation:",
            "Candidate ownership:",
            "For every `FAIL` or `INCONCLUSIVE` outcome",
            "current `Parent outcome ordinal` / flow / AC trace",
            "non-PASS Global Contract",
            "exact `None` when no ready Ticket owns the needed mutation",
            "must never authorize Ralph to widen a Ticket",
        ):
            self.assertIn(required, body)

    def test_verifier_never_remediates_or_runs_ralph(self) -> None:
        body = normalized(SKILL)
        for required in (
            "Do not remediate product code",
            "rewrite planning",
            "create Tickets",
            "invoke Implementation Lead",
            "continue the Ralph loop",
            "Do not create verification state",
        ):
            self.assertIn(required, body)


if __name__ == "__main__":
    unittest.main()
