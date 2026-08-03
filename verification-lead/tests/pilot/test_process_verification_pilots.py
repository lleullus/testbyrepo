from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "verification-lead/tools/verification-run/verification_run.py"
SPEC = importlib.util.spec_from_file_location("pilot_verification_run", MODULE)
assert SPEC and SPEC.loader
verification_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verification_run)


class ProcessVerificationPilots(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.project = root / "project"
        self.project.mkdir()
        self.product = self.project / "product.txt"
        self.product.write_text("before\n", encoding="utf-8")
        self.ticket = self.project / "TICKET.md"
        self.spec_file = self.project / "SPEC.md"
        self.ticket.write_text(
            "# Ticket\n\n## Acceptance Criteria\n\n- The intended product flow returns ready.\n",
            encoding="utf-8",
        )
        self.spec_file.write_text("# Spec\nStatus: approved\n", encoding="utf-8")
        self.seal_value = {
            "ticketPath": str(self.ticket.resolve()),
            "ticketSha256": hashlib.sha256(self.ticket.read_bytes()).hexdigest(),
            "specPath": str(self.spec_file.resolve()),
            "specSha256": hashlib.sha256(self.spec_file.read_bytes()).hexdigest(),
            "blockerFiles": [],
        }
        self.criteria = verification_run.handoff_contract.acceptance_criteria_from_ticket(self.ticket)
        self.planning = verification_run.handoff_contract.planning_seal_digest(self.seal_value)
        self.source = verification_run.baseline_capsule.capture_identity(self.project)["sourceIdentity"]
        self.workflow_root = root / "workflow"
        self.capsule_root = root / "capsules"
        self.service = verification_run.VerificationService(self.workflow_root)
        self.root_ref = verification_run.workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        self.service.workflow.publish_initial_handoff(
            node_ref=self.root_ref,
            protocol_version="implementation-handoff-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            payload={
                "protocolVersion": "implementation-handoff-v1",
                "implementationHandoffRef": self.root_ref,
                "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
                "projectRoot": str(self.project.resolve()),
                "planningSeal": self.seal_value,
                "planningSealDigest": self.planning,
                "baselineCapsuleRef": "capsule:v1:" + "1" * 32,
                "baselineSourceIdentity": self.source,
                "finalSourceIdentity": self.source,
                "implementationDeltaRef": "implementation:delta:v1:" + "2" * 32,
                "criterionAccounting": [{**self.criteria[0], "taskIds": ["initial"]}],
                "unresolvedImplementationItems": [],
                "completedAt": "2026-08-03T00:00:00+00:00",
            },
        )
        self.invocation = self.service.workflow.start_invocation(
            root_ref=self.root_ref,
            elapsed_seconds=900,
            limits=self.budget(
                workerCalls=10,
                remediationTransactions=10,
                effectfulActions=50,
                toolCostUnits=300,
                closureOperations=100,
            ),
        )
        self.coordinator = self.invocation["coordinator"]
        self.anchor = verification_run.basis_anchor(
            self.ticket,
            1,
            len(self.ticket.read_bytes().splitlines(keepends=True)),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def budget(**values: int) -> dict[str, int]:
        result = {field: 0 for field in verification_run.workflow_store.BUDGET_FIELDS}
        result.update(values)
        return result

    def open_verify(self):
        return self.service.open_verification(
            coordinator_capability=self.coordinator["capability"],
            implementation_handoff_ref=self.root_ref,
            spend_budget=self.budget(effectfulActions=10, toolCostUnits=40),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )

    def step(
        self,
        step_id: str,
        role: str,
        code: str,
        *,
        extra: list[str] | None = None,
        polls: int = 1,
        interval: int = 0,
    ) -> dict[str, object]:
        return {
            "stepId": step_id,
            "role": role,
            "executorKind": "PROCESS",
            "executable": str(Path(sys.executable).resolve()),
            "argv": ["-c", code, *(extra or [])],
            "cwd": str(self.project.resolve()),
            "environmentDelta": {},
            "inputRefs": [],
            "sourceBinding": {
                "mode": "CURRENT_PROJECT_ROOT",
                "finalSourceIdentity": self.source,
                "targetIdentityOrRevision": str(self.project.resolve()),
                "bindingBasisAnchors": [],
            },
            "pollPolicy": {"maxAttempts": polls, "intervalMs": interval} if role == "READBACK" else None,
        }

    def flow(self, flow_id: str, steps: list[dict[str, object]]) -> dict[str, object]:
        return {
            "flowId": flow_id,
            "criterionRefs": self.criteria,
            "claim": "The intended product flow returns ready.",
            "expectedTerminalObservation": "Runner-owned output establishes ready.",
            "basisAnchors": [self.anchor],
            "productTargetRequirement": "NOT_APPLICABLE",
            "steps": steps,
            "optionalCorrelationBindings": [],
        }

    def draft(self, flows: list[dict[str, object]]) -> dict[str, object]:
        return {
            "authorizationRefs": [],
            "criteria": [
                {
                    **self.criteria[0],
                    "sourceReviewIds": [],
                    "flowIds": [str(flow["flowId"]) for flow in flows],
                }
            ],
            "sourceReviews": [],
            "flows": flows,
        }

    def seal(self, opened, flows):
        return self.service.seal_run(
            assessor_capability=opened["assessor"]["capability"],
            claim_ref=opened["claim"]["claimRef"],
            implementation_handoff_ref=self.root_ref,
            verification_draft=self.draft(flows),
        )

    def assess(self, opened, sealed, verdict: str):
        return self.service.publish_result(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            criterion_assessments=[
                {
                    **self.criteria[0],
                    "verdict": verdict,
                    "semanticRationale": "The complete runner-owned product-flow fact is evaluated against the exact AC.",
                }
            ],
        )

    def test_direct_result_positive(self) -> None:
        opened = self.open_verify()
        sealed = self.seal(
            opened,
            [self.flow("direct", [self.step("direct-action", "ACTION", "print('ready')")])],
        )
        execution = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="direct",
            step_id="direct-action",
        )
        result = self.assess(opened, sealed, "SATISFIED")
        artifact = self.service.read_artifact(
            assessor_capability=opened["assessor"]["capability"],
            artifact_ref=execution["attempts"][0]["artifactRef"],
        )
        self.assertEqual("VERIFIED", result["verificationStatus"])
        self.assertEqual("ready\n", artifact["payload"]["stdout"]["text"])

    def test_disconnected_flow_negative(self) -> None:
        opened = self.open_verify()
        producer = self.flow("producer-a", [self.step("produce-a", "ACTION", "print('resource-a')")])
        direct_seed = self.flow("consumer-b", [self.step("consume-b", "ACTION", "print('resource-b')")])
        required = self.flow("required-flow", [self.step("required", "ACTION", "print('not-run')")])
        sealed = self.seal(opened, [producer, direct_seed, required])
        for flow_id, step_id in (("producer-a", "produce-a"), ("consumer-b", "consume-b")):
            self.service.execute_step(
                assessor_capability=opened["assessor"]["capability"],
                verification_run_ref=sealed["verificationRunRef"],
                flow_id=flow_id,
                step_id=step_id,
            )
        with self.assertRaises(verification_run.VerificationError) as raised:
            self.assess(opened, sealed, "SATISFIED")
        self.assertEqual("FORGED_OUTCOME_WITHOUT_EXECUTION", raised.exception.code)
        incomplete = self.assess(opened, sealed, "INCONCLUSIVE")
        self.assertEqual("INCOMPLETE", incomplete["verificationStatus"])

    def test_delayed_readback_positive(self) -> None:
        state = Path(self.temporary.name) / "delayed-state"
        action_code = (
            "import subprocess,sys; subprocess.Popen([sys.executable,'-c',"
            "'import pathlib,time,sys; time.sleep(0.25); pathlib.Path(sys.argv[1]).write_text(\"ready\")',"
            "sys.argv[1]], start_new_session=True, stdout=subprocess.DEVNULL, "
            "stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL); print('queued')"
        )
        read_code = (
            "from pathlib import Path; import sys; p=Path(sys.argv[1]); "
            "print(p.read_text() if p.exists() else 'miss'); raise SystemExit(0 if p.exists() else 7)"
        )
        opened = self.open_verify()
        sealed = self.seal(
            opened,
            [
                self.flow(
                    "delayed",
                    [
                        self.step("enqueue", "ACTION", action_code, extra=[str(state)]),
                        self.step("read", "READBACK", read_code, extra=[str(state)], polls=5, interval=100),
                    ],
                )
            ],
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="delayed",
            step_id="enqueue",
        )
        readback = self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="delayed",
            step_id="read",
        )
        exits = [attempt["result"]["exitCode"] for attempt in readback["attempts"]]
        result = self.assess(opened, sealed, "SATISFIED")
        self.assertIn(7, exits)
        self.assertIn(0, exits)
        self.assertEqual(5, len(readback["attempts"]))
        self.assertEqual(1, len({item["canonicalRequestDigest"] for item in readback["attempts"]}))
        self.assertEqual("VERIFIED", result["verificationStatus"])

    def publish_failure(self):
        opened = self.open_verify()
        sealed = self.seal(
            opened,
            [self.flow("defect", [self.step("observe", "ACTION", "print('contradiction')")])],
        )
        self.service.execute_step(
            assessor_capability=opened["assessor"]["capability"],
            verification_run_ref=sealed["verificationRunRef"],
            flow_id="defect",
            step_id="observe",
        )
        return self.assess(opened, sealed, "CONTRADICTED"), opened, sealed

    def test_in_ticket_remediation_positive(self) -> None:
        failed, first_open, first_sealed = self.publish_failure()
        remediation = self.service.open_remediation(
            coordinator_capability=self.coordinator["capability"],
            failed_verification_result_ref=failed["verificationResultRef"],
            spend_budget=self.budget(remediationTransactions=1, workerCalls=1, toolCostUnits=5),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )
        transactions = verification_run.handoff_contract.implementation_transaction.ImplementationTransactionStore(
            self.workflow_root,
            self.capsule_root,
        )
        transaction = transactions.start_remediation(
            remediator_capability=remediation["remediator"]["capability"],
            worker_capability=remediation["worker"]["capability"],
            claim_ref=remediation["claim"]["claimRef"],
            project_root=self.project,
            admission={
                "disposition": "ADMITTED",
                "criterionRefs": self.criteria,
                "authorityDeltaDigest": "c" * 64,
                "desiredOutcomeUnchanged": True,
                "acceptanceMeaningUnchanged": True,
                "scopeAndNonGoalsUnchanged": True,
                "materialProductDecisionRequired": False,
                "safetyAndOwnershipAuthorized": True,
            },
        )
        envelope = transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="fix",
            criterion_refs=self.criteria,
            allowed_paths=["product.txt"],
            forbidden_paths=[],
        )
        transactions.begin_worker_call(
            worker_capability=remediation["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.product.write_text("fixed\n", encoding="utf-8")
        transactions.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        transactions.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": ["product.txt"],
                "externalPaths": [],
                "preservedUserChanges": [],
                "externalEffectState": "CLEAR",
            },
        )
        transactions.prepare_handoff(transaction_capability=transaction["transactionCapability"])
        self.service.workflow.consume_budget(
            actor_capability=remediation["remediator"]["capability"],
            reservation_ref=remediation["budgetReservation"]["reservationRef"],
            category="CLOSURE",
            amounts=self.budget(closureOperations=1),
        )
        successor = verification_run.handoff_contract.HandoffPublisher(
            self.workflow_root,
            self.capsule_root,
        ).publish(
            {
                "protocolVersion": "implementation-handoff-v1",
                "implementationTransactionRef": transaction["transactionRef"],
                "actorCapability": remediation["remediator"]["capability"],
                "planningSeal": self.seal_value,
                "criterionAccounting": [{**self.criteria[0], "taskIds": ["fix"]}],
                "unresolvedImplementationItems": [],
            }
        )
        self.root_ref = successor["implementationHandoffRef"]
        self.source = successor["finalSourceIdentity"]
        fresh = self.open_verify()
        fresh_sealed = self.seal(
            fresh,
            [self.flow("fresh-all-ac", [self.step("fresh-observe", "ACTION", "print('ready')")])],
        )
        self.service.execute_step(
            assessor_capability=fresh["assessor"]["capability"],
            verification_run_ref=fresh_sealed["verificationRunRef"],
            flow_id="fresh-all-ac",
            step_id="fresh-observe",
        )
        verified = self.assess(fresh, fresh_sealed, "SATISFIED")
        self.assertNotEqual(first_open["assessor"]["actorRef"], fresh["assessor"]["actorRef"])
        self.assertNotEqual(first_sealed["verificationRunRef"], fresh_sealed["verificationRunRef"])
        self.assertEqual("VERIFIED", verified["verificationStatus"])

    def test_authority_delta_negative(self) -> None:
        failed, _, _ = self.publish_failure()
        source_before = verification_run.baseline_capsule.capture_identity(self.project)["sourceIdentity"]
        remediation = self.service.open_remediation(
            coordinator_capability=self.coordinator["capability"],
            failed_verification_result_ref=failed["verificationResultRef"],
            spend_budget=self.budget(remediationTransactions=1, workerCalls=1, toolCostUnits=5),
            closure_budget=self.budget(toolCostUnits=2, closureOperations=2),
        )
        transactions = verification_run.handoff_contract.implementation_transaction.ImplementationTransactionStore(
            self.workflow_root,
            self.capsule_root,
        )
        with self.assertRaises(
            verification_run.handoff_contract.implementation_transaction.TransactionError
        ) as raised:
            transactions.start_remediation(
                remediator_capability=remediation["remediator"]["capability"],
                worker_capability=remediation["worker"]["capability"],
                claim_ref=remediation["claim"]["claimRef"],
                project_root=self.project,
                admission={
                    "disposition": "ADMITTED",
                    "criterionRefs": self.criteria,
                    "authorityDeltaDigest": "d" * 64,
                    "desiredOutcomeUnchanged": True,
                    "acceptanceMeaningUnchanged": True,
                    "scopeAndNonGoalsUnchanged": True,
                    "materialProductDecisionRequired": True,
                    "safetyAndOwnershipAuthorized": True,
                },
            )
        self.assertEqual("REMEDIATION_NOT_ADMITTED", raised.exception.code)
        self.assertEqual(source_before, verification_run.baseline_capsule.capture_identity(self.project)["sourceIdentity"])
        workflow_root_ref = self.service.workflow.read_node(self.root_ref)["rootRef"]
        self.assertEqual(failed["verificationResultRef"], self.service.workflow.current_tip(workflow_root_ref)["nodeRef"])
        with self.assertRaises(
            verification_run.handoff_contract.implementation_transaction.TransactionError
        ):
            transactions.read_transaction(remediation["implementationTransactionRef"])


if __name__ == "__main__":
    unittest.main()
