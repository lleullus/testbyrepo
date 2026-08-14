from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verdict_contract import aggregate, classify_boundary


SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
NORMALIZED = " ".join(SKILL.split())


class VerificationLeadContractTests(unittest.TestCase):
    def test_runner_assignment_cannot_borrow_other_iis_role_bindings(self) -> None:
        for required in (
            "Consume only `Verification Runner` bindings at this boundary",
            "`Implementation Subagent`, `Implementation Research Agent`, or any other IIS-role binding is not eligible for Runner assignment",
            "unless the user separately designated that same configured model/agent as a `Verification Runner`",
        ):
            self.assertIn(required, NORMALIZED)

    def test_runner_assignment_decomposes_observation_without_narrowing_authored_coverage(self) -> None:
        for required in (
            "exact authored verification property",
            "authored or approved-contract-admitted trigger/inspection boundary and authoritative readback",
            "decomposes observation only",
            "must not narrow, forbid, replace, or pre-resolve authored verification coverage",
            "Do not define AC/flow/defect/file-",
            "per-Runner fixed decomposition",
        ):
            self.assertIn(required, NORMALIZED)

    def test_no_recipe_fresh_ticket_and_project_are_default_inputs(self) -> None:
        self.assertIn("fresh session with only those inputs is the normal valid starting point", NORMALIZED)
        self.assertIn("A Candidate Execution Recipe is optional", SKILL)
        self.assertIn("do not require an implementation result, Recipe", NORMALIZED)
        self.assertIn("do not reject the Ticket merely because the Recipe is absent or stale", NORMALIZED)

    def test_structural_validator_is_not_semantic_authority(self) -> None:
        self.assertIn("../matt/skills/to-tickets/validate_ticket.py", SKILL)
        self.assertIn("Treat it only as structural support", NORMALIZED)
        self.assertIn("does not establish semantic mapping", NORMALIZED)

    def test_preflight_not_started_contract_is_exact(self) -> None:
        for defect in (
            "acceptance boundary or authoritative readback is undefined",
            "AC-to-flow closure is missing",
            "independent disposition is invalid",
            "required authority/status/path is invalid",
            "verification target source cannot be identified before product execution",
        ):
            self.assertIn(defect, NORMALIZED)
        self.assertIn("VERIFICATION NOT STARTED\nTicket: <exact path>", SKILL)
        self.assertIn("AC verdicts: Not issued", SKILL)
        self.assertEqual(
            classify_boundary(admission_complete=False, attempted=False, contradiction=False),
            "VERIFICATION NOT STARTED",
        )
        with self.assertRaises(ValueError):
            classify_boundary(admission_complete=False, attempted=True, contradiction=False)

    def test_valid_attempt_without_evidence_is_inconclusive_not_fail(self) -> None:
        self.assertEqual(
            classify_boundary(admission_complete=True, attempted=True, contradiction=False),
            "INCONCLUSIVE",
        )
        for limitation in (
            "runtime/target availability",
            "missing implemented surface/readback",
            "observation failure",
            "authority loss",
            "execution-time source drift",
            "result-attribution failure",
        ):
            self.assertIn(limitation, NORMALIZED)
        self.assertIn("A runtime or readback error is not `FAIL`", NORMALIZED)
        self.assertIn("does not assume that the implemented surface is present or working", NORMALIZED)
        self.assertIn("following fresh attempt", NORMALIZED)

    def test_currentness_is_rechecked_before_verdict_without_durable_identity(self) -> None:
        self.assertIn("After each materially distinct observation", NORMALIZED)
        self.assertIn("no later than before assigning its affected AC verdicts", NORMALIZED)
        self.assertIn("freshly recheck only the bounded source", NORMALIZED)
        self.assertIn("If a bound fact changed or cannot be rechecked", NORMALIZED)
        self.assertIn("the affected ACs are `INCONCLUSIVE`", NORMALIZED)
        self.assertIn("This currentness recheck does not replace product evidence", NORMALIZED)
        self.assertIn("Do not create a digest, snapshot, retained source, or durable identity", NORMALIZED)

    def test_mutation_overlap_invalidates_whole_runner_cycle_for_progression(self) -> None:
        for required in (
            "Ticket Verification Lead cycle can authorize the caller to leave the Ticket only when the product/source observed by that cycle remained stable",
            "whole Lead/Runner cycle loses Ticket-progression authority",
            "must not use any row or aggregate from that cycle to leave the Ticket",
            "every Runner from the overlapped cycle must return or be host-confirmed stopped",
            "every Runner-started product effect must reach its authored terminal/cleanup boundary",
            "freshly reobserves the full active Ticket",
            "new Verification Lead cycle with fresh Runner invocations",
            "Do not carry forward an earlier PASS row or aggregate",
            "creates no retained verification state, cycle ID, Runner registry, or generation identity",
        ):
            self.assertIn(required, NORMALIZED)

    def test_only_direct_contradiction_is_fail(self) -> None:
        self.assertEqual(
            classify_boundary(admission_complete=True, attempted=True, contradiction=True),
            "FAIL",
        )
        self.assertIn("`FAIL` only when admissible fresh direct evidence", NORMALIZED)
        self.assertIn("Missing implementation entrypoint or verification readback alone is not an AC contradiction", NORMALIZED)
        self.assertIn("canonical-target presence/absence is itself the authored claim", NORMALIZED)

    def test_runner_finding_can_be_forwarded_before_final_aggregate(self) -> None:
        for required in (
            "fresh Runner reports admissible current evidence",
            "concrete current Ticket-owned implementation, integration, surface, or readback absence",
            "Verification Lead forwards that exact current observation to the caller immediately",
            "instead of waiting for the remaining Runner assignments or final aggregate",
            "neither Runner nor Lead turns it into an early AC verdict, remediation instruction, or new authority",
            "Other still-safe Runner observations may continue",
            "caller alone decides whether current in-Scope implementation should begin or whether the observation belongs at an operator, environment, or authority gate",
            "mutation-overlap rule below applies to the whole cycle",
            "Additional qualifying Runner findings may likewise be forwarded",
            "host cannot carry intermediate communication",
            "without inventing another transport or state mechanism",
        ):
            self.assertIn(required, NORMALIZED)

    def test_runner_reports_are_not_votes_and_missing_raw_readback_cannot_pass(self) -> None:
        for required in (
            "Never derive an AC verdict or aggregate by vote, majority, consensus, model agreement, or counting Runner labels",
            "Ignore Runner verdict-like claims",
            "unresolved conflict is `INCONCLUSIVE`",
            "not a reason to wait for a tie-breaking Runner or choose the most common claim",
            "A `PASS` requires an attributable raw authoritative readback from the current Runner observation",
            "disposable target is gone and only Runner narration remains",
            "affected AC is `INCONCLUSIVE`",
        ):
            self.assertIn(required, NORMALIZED)

    def test_exact_once_rows_and_aggregate(self) -> None:
        self.assertEqual(aggregate(2, [(1, "PASS"), (2, "PASS")]), "VERIFIED")
        self.assertEqual(aggregate(2, [(1, "PASS"), (2, "FAIL")]), "FAILED")
        self.assertEqual(aggregate(2, [(1, "PASS"), (2, "INCONCLUSIVE")]), "INCONCLUSIVE")
        for rows in (
            [(1, "PASS")],
            [(1, "PASS"), (1, "PASS")],
            [(2, "PASS"), (1, "PASS")],
            [(1, "PASS"), (2, "UNKNOWN")],
        ):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                aggregate(2, rows)

    def test_direct_evidence_boundaries_are_claim_specific(self) -> None:
        for phrase in (
            "violating input",
            "authoritative rejection",
            "absence claim reaches its authored terminal condition",
            "Ordering uses the authored authoritative event source",
            "same storage identity",
            "current canonical source inspection",
            "current generated artifact or document inspection",
            "rendered state and interaction readback",
        ):
            self.assertIn(phrase, SKILL)

    def test_implementation_checks_alone_cannot_pass(self) -> None:
        self.assertIn("implementation tests", SKILL)
        self.assertIn("cannot by itself produce `PASS`", NORMALIZED)
        self.assertIn("checks named in a Recipe", NORMALIZED)

    def test_recipe_is_stale_detection_and_bounded_binding_only(self) -> None:
        self.assertIn("Compare its current flow ordinal and observed source facts", NORMALIZED)
        self.assertIn("Use a current Recipe only to shorten bounded binding", NORMALIZED)
        self.assertIn("Never adopt its checks as direct evidence", NORMALIZED)
        self.assertIn("Resolve current source directly in all cases", NORMALIZED)

    def test_bounded_resolution_forbids_broad_research(self) -> None:
        for allowed in (
            "canonical executable path",
            "current package command",
            "actual generated artifact/canonical document location",
            "existing documented launch command",
        ):
            self.assertIn(allowed, NORMALIZED)
        for forbidden in (
            "search every runtime alternative",
            "broad repository discovery",
            "invent a scenario",
            "design a fixture/hook/provider",
            "different entrypoint is equivalent",
            "coordinate runtime acquisition",
        ):
            self.assertIn(forbidden, NORMALIZED)

    def test_unsafe_effect_does_not_authorize_skipping_ticket_verification(self) -> None:
        self.assertIn("Safe local execution and read-only canonical inspection need no scenario approval", NORMALIZED)
        self.assertIn("without existing concrete authority", NORMALIZED)
        for required in (
            "Do not skip an otherwise-required Independent Ticket Verification cycle",
            "Prefer a fresh current authoritative readback",
            "one valid shared acquisition",
            "serialize relevant Runner observations",
            "decision not to attempt a required boundary does not establish dependency unavailability",
            "does not remove that property from the authored denominator",
            "Unavailability requires fresh current observation or authoritative current readback",
            "unless the approved contract admits that surface as equivalent for that exact obligation",
            "issue `INCONCLUSIVE` with the exact environment/operator/authority evidence limit",
            "rather than leaping to Goal Verification",
        ):
            self.assertIn(required, NORMALIZED)

    def test_no_mutation_or_second_verdict_authority(self) -> None:
        for required in (
            "Do not directly modify product source",
            "Do not remediate",
            "create or propose a follow-up Ticket",
            "`verification-runner` is the only subordinate verification execution role",
            "second verdict authority",
            "Primary Verifier",
            "Coverage Challenger",
            "remediation role",
            "double run",
            "scenario plan approval",
            "safe-local approval",
        ):
            self.assertIn(required, NORMALIZED)

    def test_authored_product_effect_is_not_verifier_mutation(self) -> None:
        self.assertIn("An authored product trigger may create or change its expected product state", NORMALIZED)
        self.assertIn("safe disposable acceptance target", NORMALIZED)
        self.assertIn("must not directly edit source, configuration, product state, artifacts, or readback", NORMALIZED)
        self.assertIn("does not prohibit an authorized authored product trigger", NORMALIZED)

    def test_no_runtime_state_machinery_files_or_terms(self) -> None:
        files = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()}
        self.assertEqual(
            files,
            {
                "SKILL.md",
                "run_tests.py",
                "verdict_contract.py",
                "tests/test_contract.py",
                "tests/pilot/test_representative_pilots.py",
            },
        )
        source = SKILL + (ROOT / "verdict_contract.py").read_text(encoding="utf-8")
        for forbidden in (
            "coverage_gate.py",
            "iis_ephemeral_transport",
            "workflow database",
            "Primary Verifier is",
            "publish_plan",
            "plan envelope",
            "approval receipt",
            "remediation cycle",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
