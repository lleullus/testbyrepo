from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/implementation-transaction/implementation_transaction.py"
SPEC = importlib.util.spec_from_file_location("implementation_transaction", MODULE)
assert SPEC and SPEC.loader
implementation_transaction = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_transaction)


class ImplementationTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        temporary_root = Path(self.temporary.name)
        self.project = temporary_root / "project"
        self.project.mkdir()
        (self.project / "app.txt").write_text("before\n", encoding="utf-8")
        self.workflow_root = temporary_root / "workflow"
        self.capsule_root = temporary_root / "capsules"
        self.store = implementation_transaction.ImplementationTransactionStore(
            self.workflow_root, self.capsule_root
        )
        self.planning = "a" * 64
        self.criterion_refs = [{"criterionIndex": 1, "criterionRawSha256": "b" * 64}]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def budget_vector(**overrides: int) -> dict[str, int]:
        result = {
            field: 0 for field in implementation_transaction.workflow_store.BUDGET_FIELDS
        }
        result.update(overrides)
        return result

    def start_initial(self) -> dict[str, object]:
        return self.store.start_initial(
            project_root=self.project,
            planning_identity=self.planning,
            selected_worker="worker",
        )

    def reconcile_worker_delta(
        self, transaction: dict[str, object], envelope: dict[str, object], worker_paths: list[str]
    ) -> dict[str, object]:
        return self.store.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": worker_paths,
                "externalPaths": [],
                "preservedUserChanges": [],
                "externalEffectState": "CLEAR",
            },
        )

    def assert_code(self, code: str, operation) -> None:
        with self.assertRaises(implementation_transaction.TransactionError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)

    def test_initial_transaction_captures_tool_owned_delta_and_check(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="task-1",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=["secrets/**"],
        )
        self.assert_code(
            "WORKER_CAPABILITY_MISMATCH",
            lambda: self.store.begin_worker_call(
                worker_capability="cap:v1:" + "0" * 64,
                envelope_ref=envelope["envelopeRef"],
            ),
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        (self.project / "app.txt").write_text("after\n", encoding="utf-8")
        check = self.store.run_check(
            transaction_capability=transaction["transactionCapability"],
            executable="python3",
            argv=["-c", "from pathlib import Path; assert Path('app.txt').read_text() == 'after\\n'"],
            cwd=self.project,
        )
        self.assertEqual(0, check["result"]["exitCode"])
        after = self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.assertEqual(["app.txt"], after["delta"]["changedPaths"])
        self.reconcile_worker_delta(transaction, envelope, ["app.txt"])

        prepared = self.store.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )

        self.assertRegex(prepared["implementationDeltaRef"], r"^implementation:delta:v1:[a-f0-9]{32}$")
        self.assertEqual(["app.txt"], prepared["changedPaths"])
        self.assertNotEqual(prepared["baselineSourceIdentity"], prepared["finalSourceIdentity"])
        view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual("READY_FOR_HANDOFF", view["state"])
        self.assertEqual(1, len(view["checks"]))
        self.assertEqual(
            [
                "TRANSACTION_STARTED",
                "ENVELOPE_FROZEN",
                "WORKER_CALL_STARTED",
                "IMPLEMENTATION_CHECK_RECORDED",
                "AFTER_SNAPSHOT_CAPTURED",
                "OWNERSHIP_RECONCILED",
                "HANDOFF_PREPARED",
            ],
            [event["eventKind"] for event in view["events"]],
        )

    def test_capture_requires_selected_worker_dispatch_and_dispatch_is_single_use(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="task-1",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.assert_code(
            "ENVELOPE_NOT_DISPATCHED",
            lambda: self.store.capture_after(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
            ),
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.assert_code(
            "ENVELOPE_NOT_FROZEN",
            lambda: self.store.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            ),
        )

    def test_out_of_envelope_worker_attribution_cannot_be_reconciled(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="task-1",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"], envelope_ref=envelope["envelopeRef"]
        )
        (self.project / "outside.txt").write_text("unexpected\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.assert_code(
            "RECONCILIATION_INCOMPLETE",
            lambda: self.reconcile_worker_delta(transaction, envelope, ["outside.txt"]),
        )

    def test_unobserved_delta_after_reconciliation_blocks_handoff(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="task-1",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"], envelope_ref=envelope["envelopeRef"]
        )
        (self.project / "app.txt").write_text("after\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.reconcile_worker_delta(transaction, envelope, ["app.txt"])
        (self.project / "late.txt").write_text("late\n", encoding="utf-8")

        self.assert_code(
            "UNOBSERVED_PRODUCT_DELTA",
            lambda: self.store.prepare_handoff(
                transaction_capability=transaction["transactionCapability"]
            ),
        )

    def test_initial_zero_mutation_handoff_is_allowed(self) -> None:
        transaction = self.start_initial()

        prepared = self.store.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )

        self.assertEqual([], prepared["changedPaths"])
        self.assertEqual(prepared["baselineSourceIdentity"], prepared["finalSourceIdentity"])

    def failed_workflow(self) -> dict[str, object]:
        graph = self.store.workflow
        source = implementation_transaction.baseline_capsule.capture_identity(self.project)["sourceIdentity"]
        root_ref = implementation_transaction.workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        graph.publish_initial_handoff(
            node_ref=root_ref,
            protocol_version="implementation-handoff-v1",
            planning_identity=self.planning,
            source_identity=source,
            payload={
                "protocolVersion": "implementation-handoff-v1",
                "implementationHandoffRef": root_ref,
                "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
                "planningSealDigest": self.planning,
                "baselineSourceIdentity": source,
                "finalSourceIdentity": source,
            },
        )
        invocation = graph.start_invocation(
            root_ref=root_ref,
            elapsed_seconds=600,
            limits=self.budget_vector(
                workerCalls=2,
                remediationTransactions=1,
                effectfulActions=1,
                toolCostUnits=10,
                closureOperations=5,
            ),
        )
        coordinator = invocation["coordinator"]
        assessor = graph.issue_actor(coordinator_capability=coordinator["capability"], role="ASSESSOR")
        worker = graph.issue_actor(coordinator_capability=coordinator["capability"], role="WORKER")
        verify_budget = graph.reserve_budget(
            coordinator_capability=coordinator["capability"],
            transition_kind="VERIFY",
            spend=self.budget_vector(effectfulActions=1, toolCostUnits=2),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=1),
        )
        verify_claim = graph.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=assessor["actorRef"],
            tip_ref=root_ref,
            transition_kind="VERIFY",
            planning_identity=self.planning,
            source_identity=source,
            execution_ref=implementation_transaction.workflow_store.allocate_ref("VERIFY"),
            budget_reservation_ref=verify_budget["reservationRef"],
        )
        graph.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=verify_budget["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        result_ref = implementation_transaction.workflow_store.allocate_ref("VERIFICATION_RESULT")
        failed = graph.publish_successor(
            claimant_capability=assessor["capability"],
            claim_ref=verify_claim["claimRef"],
            node_ref=result_ref,
            node_kind="VERIFICATION_RESULT",
            protocol_version="verification-result-v1",
            planning_identity=self.planning,
            source_identity=source,
            verification_status="VERIFICATION_FAILED",
            payload={
                "protocolVersion": "verification-result-v1",
                "verificationResultRef": result_ref,
                "verificationStatus": "VERIFICATION_FAILED",
                "implementationHandoffRef": root_ref,
                "planningSealDigest": self.planning,
                "finalSourceIdentity": source,
                "criterionResults": [
                    {
                        **self.criterion_refs[0],
                        "verdict": "CONTRADICTED",
                        "semanticRationale": "tool-owned contradiction",
                    }
                ],
            },
        )
        remediator = graph.issue_actor(
            coordinator_capability=coordinator["capability"], role="REMEDIATOR"
        )
        remediation_budget = graph.reserve_budget(
            coordinator_capability=coordinator["capability"],
            transition_kind="REMEDIATE",
            spend=self.budget_vector(remediationTransactions=1, workerCalls=1, toolCostUnits=3),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=2),
        )
        remediation_claim = graph.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=remediator["actorRef"],
            tip_ref=failed["nodeRef"],
            transition_kind="REMEDIATE",
            planning_identity=self.planning,
            source_identity=source,
            execution_ref=implementation_transaction.workflow_store.allocate_ref("REMEDIATE"),
            budget_reservation_ref=remediation_budget["reservationRef"],
        )
        return {
            "rootRef": root_ref,
            "sourceIdentity": source,
            "coordinator": coordinator,
            "worker": worker,
            "remediator": remediator,
            "claim": remediation_claim,
            "budget": remediation_budget,
        }

    def admission(self) -> dict[str, object]:
        return {
            "disposition": "ADMITTED",
            "criterionRefs": self.criterion_refs,
            "authorityDeltaDigest": "c" * 64,
            "desiredOutcomeUnchanged": True,
            "acceptanceMeaningUnchanged": True,
            "scopeAndNonGoalsUnchanged": True,
            "materialProductDecisionRequired": False,
            "safetyAndOwnershipAuthorized": True,
        }

    def test_remediation_requires_admission_and_non_empty_delta(self) -> None:
        workflow = self.failed_workflow()
        rejected = self.admission()
        rejected["materialProductDecisionRequired"] = True
        self.assert_code(
            "REMEDIATION_NOT_ADMITTED",
            lambda: self.store.start_remediation(
                remediator_capability=workflow["remediator"]["capability"],
                worker_capability=workflow["worker"]["capability"],
                claim_ref=workflow["claim"]["claimRef"],
                project_root=self.project,
                admission=rejected,
            ),
        )
        transaction = self.store.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission=self.admission(),
        )
        self.assertEqual("UNAVAILABLE", transaction["exactRepeatDisposition"])
        self.assert_code(
            "EMPTY_REMEDIATION_DELTA",
            lambda: self.store.prepare_handoff(
                transaction_capability=transaction["transactionCapability"]
            ),
        )

    def test_remediation_delta_is_bound_to_failed_source_and_selected_worker(self) -> None:
        workflow = self.failed_workflow()
        transaction = self.store.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission=self.admission(),
        )
        self.assertEqual(workflow["sourceIdentity"], transaction["baselineSourceIdentity"])
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="remediation-1",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.assert_code(
            "WORKER_CAPABILITY_MISMATCH",
            lambda: self.store.begin_worker_call(
                worker_capability="cap:v1:" + "0" * 64,
                envelope_ref=envelope["envelopeRef"],
            ),
        )
        self.store.begin_worker_call(
            worker_capability=workflow["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        (self.project / "app.txt").write_text("fixed\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.reconcile_worker_delta(transaction, envelope, ["app.txt"])

        prepared = self.store.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )

        self.assertNotEqual(workflow["sourceIdentity"], prepared["finalSourceIdentity"])
        self.assertEqual(["app.txt"], prepared["changedPaths"])
        view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual(["app.txt"], view["implementationDelta"]["workerAttributablePaths"])
        self.assertEqual([], view["implementationDelta"]["preservedExternalPaths"])

    def test_external_only_delta_cannot_satisfy_remediation_progress(self) -> None:
        workflow = self.failed_workflow()
        transaction = self.store.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission=self.admission(),
        )
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="external-only",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=workflow["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        (self.project / "concurrent.txt").write_text("external\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.store.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": [],
                "externalPaths": ["concurrent.txt"],
                "preservedUserChanges": ["concurrent.txt"],
                "externalEffectState": "CLEAR",
            },
        )

        self.assert_code(
            "EMPTY_REMEDIATION_DELTA",
            lambda: self.store.prepare_handoff(
                transaction_capability=transaction["transactionCapability"]
            ),
        )
        self.assertEqual(
            workflow["claim"]["claimRef"],
            self.store.workflow.active_claim(workflow["rootRef"])["claim_ref"],
        )

    def test_no_delta_remediation_releases_claim_only_after_reconciled_safe_closure(self) -> None:
        workflow = self.failed_workflow()
        transaction = self.store.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission=self.admission(),
        )
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="no-delta",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=workflow["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.reconcile_worker_delta(transaction, envelope, [])

        closed = self.store.close_without_successor(
            transaction_capability=transaction["transactionCapability"],
            remediator_capability=workflow["remediator"]["capability"],
        )

        self.assertEqual("CLOSED_NO_SUCCESSOR", closed["state"])
        self.assertEqual([], closed["closure"]["changedPaths"])
        self.assertIsNone(self.store.workflow.active_claim(workflow["rootRef"]))
        self.assertEqual("VERIFICATION_RESULT", self.store.workflow.current_tip(workflow["rootRef"])["nodeKind"])
        self.assertEqual("CLOSED_NO_SUCCESSOR", self.store.read_transaction(transaction["transactionRef"])["state"])

    def test_retained_delta_or_unreconciled_envelope_keeps_remediation_claim(self) -> None:
        workflow = self.failed_workflow()
        transaction = self.store.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission=self.admission(),
        )
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="retained",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=workflow["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        (self.project / "app.txt").write_text("retained\n", encoding="utf-8")

        self.assert_code(
            "SUCCESSORLESS_RELEASE_NOT_SAFE",
            lambda: self.store.close_without_successor(
                transaction_capability=transaction["transactionCapability"],
                remediator_capability=workflow["remediator"]["capability"],
            ),
        )
        self.assertEqual(workflow["claim"]["claimRef"], self.store.workflow.active_claim(workflow["rootRef"])["claim_ref"])

        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.reconcile_worker_delta(transaction, envelope, ["app.txt"])
        self.assert_code(
            "SUCCESSORLESS_RELEASE_NOT_SAFE",
            lambda: self.store.close_without_successor(
                transaction_capability=transaction["transactionCapability"],
                remediator_capability=workflow["remediator"]["capability"],
            ),
        )
        self.assertEqual(workflow["claim"]["claimRef"], self.store.workflow.active_claim(workflow["rootRef"])["claim_ref"])

    def test_remediation_worker_dispatch_consumes_reserved_worker_call_budget(self) -> None:
        workflow = self.failed_workflow()
        transaction = self.store.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission=self.admission(),
        )
        first = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="first",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=workflow["worker"]["capability"],
            envelope_ref=first["envelopeRef"],
        )
        check = self.store.run_check(
            transaction_capability=transaction["transactionCapability"],
            executable="python3",
            argv=["-c", "print('bounded remediation check')"],
            cwd=self.project,
        )
        self.assertEqual(0, check["result"]["exitCode"])
        connection = self.store.workflow._connect()
        try:
            reservation = connection.execute(
                "SELECT spend_used_json FROM budget_reservations WHERE reservation_ref = ?",
                (workflow["budget"]["reservationRef"],),
            ).fetchone()
            used = self.store.workflow._stored_budget(
                reservation["spend_used_json"], "reservation.spendUsed"
            )
        finally:
            connection.close()
        self.assertEqual(1, used["toolCostUnits"])
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=first["envelopeRef"],
        )
        self.reconcile_worker_delta(transaction, first, [])
        second = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="second",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.assert_code(
            "BUDGET_RESERVATION_EXCEEDED",
            lambda: self.store.begin_worker_call(
                worker_capability=workflow["worker"]["capability"],
                envelope_ref=second["envelopeRef"],
            ),
        )


if __name__ == "__main__":
    unittest.main()
