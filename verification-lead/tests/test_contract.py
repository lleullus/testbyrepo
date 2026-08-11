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

    def test_only_direct_contradiction_is_fail(self) -> None:
        self.assertEqual(
            classify_boundary(admission_complete=True, attempted=True, contradiction=True),
            "FAIL",
        )
        self.assertIn("`FAIL` only when admissible fresh direct evidence", NORMALIZED)
        self.assertIn("Missing implementation entrypoint or verification readback alone is not an AC contradiction", NORMALIZED)
        self.assertIn("canonical-target presence/absence is itself the authored claim", NORMALIZED)

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

    def test_safety_needs_no_safe_local_approval_and_no_unsafe_execution(self) -> None:
        self.assertIn("Safe local execution and read-only canonical inspection need no scenario approval", NORMALIZED)
        self.assertIn("without existing concrete authority", NORMALIZED)
        self.assertIn("never route it to another agent or present it as independent success", NORMALIZED)

    def test_no_mutation_remediation_or_choreography(self) -> None:
        for forbidden_action in (
            "Do not directly modify product source",
            "Do not remediate",
            "create or propose a follow-up Ticket",
            "runtime acquisition agent",
            "second verifier",
            "Coverage Challenger",
            "double run",
            "scenario plan approval",
            "safe-local approval",
        ):
            self.assertIn(forbidden_action, SKILL)

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
