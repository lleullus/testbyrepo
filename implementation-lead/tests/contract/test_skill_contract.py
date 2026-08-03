from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")
HANDOFF_REFERENCE = (
    ROOT / "implementation-lead/references/implementation-handoff-v1.md"
).read_text(encoding="utf-8")
HISTORICAL_V3 = (
    ROOT / "implementation-lead/references/completion-record-v3.md"
).read_text(encoding="utf-8")
FAILURE_ROUTING = (
    ROOT / "implementation-lead/references/implementation-failure-routing.md"
).read_text(encoding="utf-8")
UI_REFERENCE = (ROOT / "implementation-lead/references/ui-ticket.md").read_text(encoding="utf-8")
WINDOWS_REFERENCE = (
    ROOT / "implementation-lead/references/windows-hyperv-execution.md"
).read_text(encoding="utf-8")
GREENFIELD_REFERENCE = (
    ROOT / "implementation-lead/references/greenfield-implementation.md"
).read_text(encoding="utf-8")
TO_TICKETS = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
FREEZE_EVIDENCE = (
    ROOT / "verification-lead/references/freeze-22-evidence.md"
).read_text(encoding="utf-8")


def compact(value: str) -> str:
    return " ".join(value.split())


class ImplementationAndVerificationContractTests(unittest.TestCase):
    def test_implementation_lead_ends_in_handoff_not_verification(self) -> None:
        self.assertIn("implementation-handoff-v1", IMPLEMENTATION_SKILL)
        self.assertIn("IMPLEMENTATION_HANDOFF_COMPLETE", IMPLEMENTATION_SKILL)
        self.assertIn("independent verification is pending", IMPLEMENTATION_SKILL)
        self.assertIn("does not certify the final product behavior", IMPLEMENTATION_SKILL)
        self.assertIn("must not label a provisional smoke", IMPLEMENTATION_SKILL)

    def test_only_two_public_contracts_are_named(self) -> None:
        expected = (
            "Implementation Lead -> implementation-handoff-v1\n"
            "Verification Lead   -> verification-result-v1"
        )
        self.assertIn(expected, IMPLEMENTATION_SKILL)
        self.assertIn("implementation-handoff-v1", VERIFICATION_SKILL)
        self.assertIn("verification-result-v1", VERIFICATION_SKILL)

    def test_v3_is_explicitly_retired_and_read_only(self) -> None:
        self.assertIn("retired for every new publication", IMPLEMENTATION_SKILL)
        self.assertIn("PROTOCOL_RETIRED", HISTORICAL_V3)
        self.assertIn("byte-preserving historical read", HISTORICAL_V3)
        self.assertIn("no dual publication", HISTORICAL_V3.lower())
        self.assertIn("never converted to a handoff", HANDOFF_REFERENCE)

    def test_handoff_payload_and_derivation_are_exact(self) -> None:
        for field in (
            "implementationHandoffRef",
            "planningSealDigest",
            "baselineCapsuleRef",
            "baselineSourceIdentity",
            "finalSourceIdentity",
            "implementationDeltaRef",
            "criterionAccounting[]",
            "unresolvedImplementationItems = []",
        ):
            self.assertIn(field, HANDOFF_REFERENCE)
        self.assertIn("derives, rather than trusts caller claims", IMPLEMENTATION_SKILL)
        self.assertIn("Publication and transaction closure are atomic", compact(IMPLEMENTATION_SKILL))

    def test_worker_mutation_and_ownership_boundary_are_explicit(self) -> None:
        self.assertIn("Only the selected Worker may mutate", IMPLEMENTATION_SKILL)
        self.assertIn("before/after ownership snapshots", IMPLEMENTATION_SKILL)
        self.assertIn("cannot be added to the envelope after the fact", compact(IMPLEMENTATION_SKILL))
        self.assertIn("Preserve external paths exactly", IMPLEMENTATION_SKILL)
        self.assertIn("Never reset, checkout, stash, clean", IMPLEMENTATION_SKILL)

    def test_both_implementation_transaction_modes_and_safe_release_are_documented(self) -> None:
        self.assertIn("INITIAL_IMPLEMENTATION", IMPLEMENTATION_SKILL)
        self.assertIn("VERIFICATION_REMEDIATION", IMPLEMENTATION_SKILL)
        self.assertIn("CLOSED_NO_SUCCESSOR", IMPLEMENTATION_SKILL)
        self.assertIn("current physical identity = exact failed predecessor identity", IMPLEMENTATION_SKILL)
        self.assertIn("externalEffectState = CLEAR", IMPLEMENTATION_SKILL)

    def test_remediation_requires_published_failure_and_authority_delta(self) -> None:
        self.assertIn("current tip = exact published VERIFICATION_FAILED", FAILURE_ROUTING)
        self.assertIn("A draft rationale", FAILURE_ROUTING)
        self.assertIn("does not authorize remediation", FAILURE_ROUTING)
        self.assertIn("new material decision cannot", FAILURE_ROUTING)
        self.assertIn("leaves the failed result as the current tip", FAILURE_ROUTING)

    def test_successful_remediation_requires_new_handoff_and_fresh_assessor(self) -> None:
        self.assertIn("non-empty authorized tool-owned delta", FAILURE_ROUTING)
        self.assertIn("new non-ancestor source", FAILURE_ROUTING)
        self.assertIn("successor `ImplementationHandoff`", FAILURE_ROUTING)
        self.assertIn("fresh Assessor", FAILURE_ROUTING)
        self.assertIn("Old attempts, mappings, rationale", VERIFICATION_SKILL)

    def test_exact_repeat_uses_three_valued_mechanical_guard(self) -> None:
        self.assertIn("Only `MATCH` stops", VERIFICATION_SKILL)
        self.assertIn("`NO_MATCH` may continue", VERIFICATION_SKILL)
        self.assertIn("`UNAVAILABLE` creates no generic", VERIFICATION_SKILL)
        self.assertIn("structured terminal fact", VERIFICATION_SKILL)

    def test_verification_roles_are_strictly_separated(self) -> None:
        for role in ("Coordinator", "Assessor", "Remediation Lead", "Worker"):
            self.assertIn(role, VERIFICATION_SKILL)
        self.assertIn("does not implement product changes", VERIFICATION_SKILL)
        self.assertIn("fresh read-only Assessor", VERIFICATION_SKILL)
        self.assertIn("A Worker actor cannot be reused", compact(VERIFICATION_SKILL))

    def test_owner_store_claim_and_atomic_linearity_are_required(self) -> None:
        self.assertIn("exclusive `VERIFY` or `REMEDIATE` claim", VERIFICATION_SKILL)
        self.assertIn("at most one active claim", VERIFICATION_SKILL)
        self.assertIn("successor node, continuation edge, claim consumption", VERIFICATION_SKILL)
        self.assertIn("following unique immutable edges", VERIFICATION_SKILL)
        self.assertIn("VERIFIED -> terminal", compact(VERIFICATION_SKILL))

    def test_finite_budget_includes_execution_and_closure_dimensions(self) -> None:
        for field in (
            "workerCalls",
            "remediationTransactions",
            "effectfulActions",
            "toolCostUnits",
            "closureOperations",
        ):
            self.assertIn(field, VERIFICATION_SKILL)
        self.assertIn("Exhaustion blocks a new unit", VERIFICATION_SKILL)
        self.assertIn("never abandons containment", VERIFICATION_SKILL)

    def test_preflight_fail_closed_contract_is_explicit(self) -> None:
        self.assertIn("CANDIDATE_IDENTITY_UNAVAILABLE_AT_START", VERIFICATION_SKILL)
        self.assertIn("zero product attempts", VERIFICATION_SKILL)
        self.assertIn("sealedPlanDigest = null", VERIFICATION_SKILL)
        self.assertIn("Planning or authorization prohibition publishes `BLOCKED`", VERIFICATION_SKILL)

    def test_exact_ac_mapping_and_basis_anchor_contract_are_explicit(self) -> None:
        self.assertIn("criterionIndex", VERIFICATION_SKILL)
        self.assertIn("criterionRawSha256", VERIFICATION_SKILL)
        self.assertIn("exact and bidirectional", compact(VERIFICATION_SKILL))
        self.assertIn("canonicalPath", VERIFICATION_SKILL)
        self.assertIn("selectedTextSha256", VERIFICATION_SKILL)
        self.assertIn("copying or delta-editing an ancestor plan", VERIFICATION_SKILL)

    def test_process_executor_is_fixed_concrete_and_no_shell(self) -> None:
        self.assertIn("initial callable executor set is closed to `PROCESS`", VERIFICATION_SKILL)
        self.assertIn("executes directly", VERIFICATION_SKILL)
        self.assertIn("with no shell", VERIFICATION_SKILL)
        self.assertIn("accepts no replacement request", VERIFICATION_SKILL)
        self.assertIn("runtime plugins", VERIFICATION_SKILL)

    def test_cardinality_polling_and_ledger_are_complete(self) -> None:
        self.assertIn("ACTION and CLEANUP logical step can start at most once", VERIFICATION_SKILL)
        self.assertIn("`1..10` identical-request polls", VERIFICATION_SKILL)
        self.assertIn("Every miss, error, output digest", compact(VERIFICATION_SKILL))
        self.assertIn("can never be retried in the same run", VERIFICATION_SKILL)

    def test_correlation_is_bounded_and_not_a_dsl(self) -> None:
        self.assertIn("tool generates a unique correlation token", VERIFICATION_SKILL)
        self.assertIn("No regex, JSONPath, DOM extraction", VERIFICATION_SKILL)
        self.assertIn("`MATCH`", VERIFICATION_SKILL)
        self.assertIn("`UNAVAILABLE`", VERIFICATION_SKILL)

    def test_retain_and_contradiction_stop_are_explicit(self) -> None:
        self.assertIn("RETAIN flow can be verified only", compact(VERIFICATION_SKILL))
        self.assertIn("final sealed step is an actually executed READBACK", VERIFICATION_SKILL)
        self.assertIn("ACTION_STOPPED_AFTER_CONTRADICTION", VERIFICATION_SKILL)
        self.assertIn("NOT_RUN_PRIOR_CONTRADICTION", VERIFICATION_SKILL)

    def test_result_input_excludes_self_attested_facts_and_derives_status(self) -> None:
        self.assertIn("cannot submit receipts, selected attempts", VERIFICATION_SKILL)
        self.assertIn("aggregate status", VERIFICATION_SKILL)
        self.assertIn("valid exact contradiction -> VERIFICATION_FAILED", VERIFICATION_SKILL)
        self.assertIn("FORGED", VERIFICATION_SKILL.upper())
        for status in ("VERIFIED", "VERIFICATION_FAILED", "INCOMPLETE", "BLOCKED"):
            self.assertIn(status, VERIFICATION_SKILL)

    def test_cross_run_effect_replay_requires_mechanical_safety(self) -> None:
        self.assertIn("does not erase ambiguous", VERIFICATION_SKILL)
        self.assertIn("authoritative readback", VERIFICATION_SKILL)
        self.assertIn("exact-idempotency", VERIFICATION_SKILL)
        self.assertIn("unique-correlation", VERIFICATION_SKILL)
        self.assertIn("Per-run cardinality alone", VERIFICATION_SKILL)

    def test_ui_and_windows_checks_are_provisional_until_fresh_verification(self) -> None:
        self.assertIn("fresh Verification Assessor", UI_REFERENCE)
        self.assertIn("do not establish a public criterion", UI_REFERENCE)
        self.assertIn("provisional implementation facts", WINDOWS_REFERENCE)
        self.assertIn("not final runtime evidence", WINDOWS_REFERENCE)
        self.assertIn("successor handoff", WINDOWS_REFERENCE)

    def test_windows_agentbridge_window_mode_is_explicit_and_fail_closed(self) -> None:
        self.assertIn("Every newly submitted bounded AgentBridge job JSON", WINDOWS_REFERENCE)
        self.assertIn("`hiddenConsole`", WINDOWS_REFERENCE)
        self.assertIn("`interactiveGui`", WINDOWS_REFERENCE)
        self.assertIn("actual runtime consumer", WINDOWS_REFERENCE)
        self.assertIn("fail before process start", WINDOWS_REFERENCE)
        self.assertIn("A missing or unsupported `windowMode`", compact(WINDOWS_REFERENCE))
        for forbidden_inference in (
            "file name",
            "extension",
            "path",
            "job name",
            "`waitForExit`",
            "`captureScreenshot`",
            "screenshot presence",
        ):
            self.assertIn(forbidden_inference, compact(WINDOWS_REFERENCE))

    def test_windows_agentbridge_maintenance_actions_are_not_ordinary_execution(self) -> None:
        self.assertIn("`configure-worker-window`", WINDOWS_REFERENCE)
        self.assertIn("`-ApplyWindowHideStaging`", WINDOWS_REFERENCE)
        self.assertIn("explicitly authorized AgentBridge\nmaintenance operation", WINDOWS_REFERENCE)
        self.assertIn("action count, Execute,\nArguments, WorkingDirectory", WINDOWS_REFERENCE)
        self.assertIn("`Settings.Hidden`", WINDOWS_REFERENCE)
        self.assertNotIn("windowMode", IMPLEMENTATION_SKILL)

    def test_greenfield_joins_handoff_not_retired_result(self) -> None:
        self.assertIn("`implementation-handoff-v1` flow", GREENFIELD_REFERENCE)
        self.assertIn("fresh Verification Assessor", compact(GREENFIELD_REFERENCE))
        self.assertNotIn("v3 result flow", GREENFIELD_REFERENCE)

    def test_to_tickets_preserves_shared_raw_ac_identity(self) -> None:
        self.assertIn("shared\n`criterionIndex` and `criterionRawSha256` identity", TO_TICKETS)
        self.assertIn("`implementation-handoff-v1`", TO_TICKETS)
        self.assertIn("every sealed VerificationRun", TO_TICKETS)
        self.assertIn("`verification-result-v1`", TO_TICKETS)

    def test_to_tickets_assigns_final_product_flow_to_verification_assessor(self) -> None:
        self.assertIn("fresh read-only Verification Assessor", TO_TICKETS)
        self.assertIn("presealed source reviews and/or concrete product flows", TO_TICKETS)
        self.assertIn("do not establish an Acceptance-\nCriterion verdict", TO_TICKETS)

    def test_repository_readme_exposes_verification_component(self) -> None:
        self.assertIn("`verification-lead/`", README)
        self.assertIn("verification-result-v1", README)
        self.assertIn("PROCESS executor", README)

    def test_freeze_evidence_registers_all_twenty_two_conditions(self) -> None:
        checklist_rows = [
            line for line in FREEZE_EVIDENCE.splitlines() if line.startswith("| ") and "| [x] |" in line
        ]
        self.assertEqual(22, len(checklist_rows))
        for number, row in enumerate(checklist_rows, start=1):
            self.assertTrue(row.startswith(f"| {number} | [x] |"), row)


if __name__ == "__main__":
    unittest.main()
