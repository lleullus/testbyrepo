from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/implementation-result/implementation_result.py"
SPEC = importlib.util.spec_from_file_location("implementation_result", MODULE)
assert SPEC and SPEC.loader
implementation_result = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_result)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ImplementationHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        temporary_root = Path(self.temporary.name)
        self.project = temporary_root / "project"
        self.project.mkdir()
        (self.project / "app.txt").write_text("before\n", encoding="utf-8")
        self.planning = temporary_root / "planning"
        self.planning.mkdir()
        self.ticket = self.planning / "TICKET.md"
        self.spec = self.planning / "SPEC.md"
        self.spec.write_text("# Spec\nStatus: approved\nOwner: user\n", encoding="utf-8")
        self.write_ticket("- The final source contains the approved marker.\n")
        self.workflow_root = temporary_root / "workflow"
        self.capsule_root = temporary_root / "capsules"
        self.historical_root = temporary_root / "historical"
        self.publisher = implementation_result.HandoffPublisher(
            self.workflow_root, self.capsule_root
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_ticket(self, acceptance_body: str) -> None:
        self.ticket.write_text(
            "# Ticket\n"
            "Status: ready\n"
            "Parent-Spec: SPEC.md\n"
            f"Project-Root: {self.project}\n"
            "Worker:\n"
            "UI: no\n\n"
            "## Goal\nResult.\n\n"
            "## Acceptance Criteria\n"
            f"{acceptance_body}\n"
            "## Scope\nProject.\n\n"
            "## Non-Goals\nNone\n\n"
            "## Blockers\nNone\n\n"
            "## Verification\nObserve the result.\n\n"
            "## References\nNone\n",
            encoding="utf-8",
        )

    def planning_seal(self) -> dict[str, object]:
        return {
            "ticketPath": str(self.ticket.resolve()),
            "ticketSha256": digest(self.ticket),
            "specPath": str(self.spec.resolve()),
            "specSha256": digest(self.spec),
            "blockerFiles": [],
        }

    @staticmethod
    def budget_vector(**overrides: int) -> dict[str, int]:
        result = {
            field: 0 for field in implementation_result.workflow_store.BUDGET_FIELDS
        }
        result.update(overrides)
        return result

    def criteria(self) -> list[dict[str, object]]:
        return implementation_result.acceptance_criteria_from_ticket(self.ticket)

    def prepare_initial(self, *, mutate: bool) -> dict[str, object]:
        planning_identity = implementation_result.planning_seal_digest(self.planning_seal())
        transaction = self.publisher.transactions.start_initial(
            project_root=self.project,
            planning_identity=planning_identity,
            selected_worker="worker",
        )
        task_ids: list[str] = []
        if mutate:
            task_id = "task-1"
            envelope = self.publisher.transactions.freeze_envelope(
                transaction_capability=transaction["transactionCapability"],
                task_id=task_id,
                criterion_refs=self.criteria(),
                allowed_paths=["app.txt"],
                forbidden_paths=[],
            )
            self.publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
            (self.project / "app.txt").write_text("approved marker\n", encoding="utf-8")
            self.publisher.transactions.capture_after(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
            self.publisher.transactions.reconcile_envelope(
                transaction_capability=transaction["transactionCapability"],
                envelope_ref=envelope["envelopeRef"],
                reconciliation={
                    "disposition": "CONTINUE",
                    "workerAttributablePaths": ["app.txt"],
                    "externalPaths": [],
                    "preservedUserChanges": [],
                    "externalEffectState": "CLEAR",
                },
            )
            task_ids.append(task_id)
        prepared = self.publisher.transactions.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )
        return {**transaction, **prepared, "taskIds": task_ids}

    def request(
        self, transaction: dict[str, object], *, actor_capability: str | None = None
    ) -> dict[str, object]:
        return {
            "protocolVersion": "implementation-handoff-v1",
            "implementationTransactionRef": transaction["transactionRef"],
            "actorCapability": actor_capability,
            "planningSeal": self.planning_seal(),
            "criterionAccounting": [
                {**criterion, "taskIds": list(transaction["taskIds"])}
                for criterion in self.criteria()
            ],
            "unresolvedImplementationItems": [],
        }

    def assert_code(self, code: str, operation) -> None:
        with self.assertRaises(implementation_result.HandoffError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)

    def test_initial_handoff_is_transaction_derived_and_round_trips(self) -> None:
        transaction = self.prepare_initial(mutate=True)

        handoff = self.publisher.publish(self.request(transaction))

        self.assertEqual("implementation-handoff-v1", handoff["protocolVersion"])
        self.assertEqual("IMPLEMENTATION_HANDOFF_COMPLETE", handoff["implementationStatus"])
        self.assertRegex(
            handoff["implementationHandoffRef"], r"^implementation:handoff:v1:[a-f0-9]{32}$"
        )
        self.assertEqual(transaction["implementationDeltaRef"], handoff["implementationDeltaRef"])
        self.assertEqual(transaction["finalSourceIdentity"], handoff["finalSourceIdentity"])
        self.assertNotIn("sourceEvidence", handoff)
        self.assertNotIn("runtimeObservations", handoff)
        self.assertNotIn("verificationStatus", handoff)
        stored = self.publisher.workflow.read_node(handoff["implementationHandoffRef"])
        self.assertEqual(handoff, stored["payload"])
        closed = self.publisher.transactions.read_transaction(transaction["transactionRef"])
        self.assertEqual("CLOSED_WITH_HANDOFF", closed["state"])
        self.assertEqual("HANDOFF_PUBLISHED", closed["events"][-1]["eventKind"])

    def test_initial_zero_mutation_handoff_has_empty_tool_owned_delta(self) -> None:
        transaction = self.prepare_initial(mutate=False)

        handoff = self.publisher.publish(self.request(transaction))

        self.assertEqual(transaction["baselineSourceIdentity"], handoff["finalSourceIdentity"])
        self.assertEqual([], handoff["criterionAccounting"][0]["taskIds"])

    def test_criterion_accounting_must_match_exact_ticket_and_transaction_tasks(self) -> None:
        transaction = self.prepare_initial(mutate=True)
        request = self.request(transaction)
        request["criterionAccounting"][0]["taskIds"] = []
        self.assert_code(
            "INCOMPLETE_CRITERION_ACCOUNTING", lambda: self.publisher.publish(request)
        )

        request = self.request(transaction)
        request["criterionAccounting"][0]["criterionRawSha256"] = "0" * 64
        self.assert_code("ACCEPTANCE_CRITERIA_MISMATCH", lambda: self.publisher.publish(request))

    def test_unresolved_items_and_caller_status_fields_are_rejected(self) -> None:
        transaction = self.prepare_initial(mutate=False)
        request = self.request(transaction)
        request["unresolvedImplementationItems"] = ["gap"]
        self.assert_code("UNRESOLVED_IMPLEMENTATION_ITEMS", lambda: self.publisher.publish(request))

        request = self.request(transaction)
        request["implementationStatus"] = "IMPLEMENTATION_HANDOFF_COMPLETE"
        self.assert_code("MALFORMED_HANDOFF", lambda: self.publisher.publish(request))

    def test_planning_or_source_drift_leaves_transaction_ready_and_no_node(self) -> None:
        transaction = self.prepare_initial(mutate=False)
        request = self.request(transaction)
        self.ticket.write_text("changed\n", encoding="utf-8")
        self.assert_code("PLANNING_INPUT_CHANGED", lambda: self.publisher.publish(request))
        self.assertEqual(
            "READY_FOR_HANDOFF",
            self.publisher.transactions.read_transaction(transaction["transactionRef"])["state"],
        )

        self.write_ticket("- The final source contains the approved marker.\n")
        transaction = self.prepare_initial(mutate=False)
        request = self.request(transaction)
        (self.project / "late.txt").write_text("late\n", encoding="utf-8")
        self.assert_code("SOURCE_IDENTITY_MISMATCH", lambda: self.publisher.publish(request))
        connection = self.publisher.workflow._connect()
        try:
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
        finally:
            connection.close()

    def test_transaction_cannot_publish_twice(self) -> None:
        transaction = self.prepare_initial(mutate=False)
        self.publisher.publish(self.request(transaction))
        self.assert_code(
            "IMPLEMENTATION_TRANSACTION_NOT_READY",
            lambda: self.publisher.publish(self.request(transaction)),
        )

    def test_all_new_v3_publications_are_retired_before_shape_validation(self) -> None:
        for legacy_kind in ("SOURCE", "RUNTIME"):
            with self.subTest(legacy_kind=legacy_kind):
                self.assert_code(
                    "PROTOCOL_RETIRED",
                    lambda kind=legacy_kind: self.publisher.publish(
                        {
                            "protocolVersion": "implementation-result-v3",
                            "legacyClaimedKind": kind,
                            "completionRecord": {"callerAuthoredOutcome": "success"},
                        }
                    ),
                )

    def test_historical_v3_is_read_only_and_never_adapted(self) -> None:
        self.historical_root.mkdir()
        token = "1" * 32
        result_ref = f"implementation:v3:{token}"
        path = self.historical_root / f"{token}.json"
        value = {
            "protocolVersion": "implementation-result-v3",
            "implementationResultRef": result_ref,
            "implementationStatus": "IMPLEMENTATION_COMPLETE",
            "completionRecord": {"runtimeObservations": [{"callerAuthored": True}]},
        }
        path.write_text(json.dumps(value), encoding="utf-8")
        before = path.read_bytes()

        readback = implementation_result.HistoricalV3Store(self.historical_root).read(result_ref)

        self.assertEqual(value, readback)
        self.assertEqual(before, path.read_bytes())
        self.assertNotIn("implementationHandoffRef", readback)

    def failed_workflow(self) -> dict[str, object]:
        initial = self.prepare_initial(mutate=False)
        handoff = self.publisher.publish(self.request(initial))
        root_ref = handoff["implementationHandoffRef"]
        source = handoff["finalSourceIdentity"]
        graph = self.publisher.workflow
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
        assessor = graph.issue_actor(
            coordinator_capability=coordinator["capability"], role="ASSESSOR"
        )
        worker = graph.issue_actor(
            coordinator_capability=coordinator["capability"], role="WORKER"
        )
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
            planning_identity=handoff["planningSealDigest"],
            source_identity=source,
            execution_ref=implementation_result.workflow_store.allocate_ref("VERIFY"),
            budget_reservation_ref=verify_budget["reservationRef"],
        )
        graph.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=verify_budget["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        result_ref = implementation_result.workflow_store.allocate_ref("VERIFICATION_RESULT")
        failed = graph.publish_successor(
            claimant_capability=assessor["capability"],
            claim_ref=verify_claim["claimRef"],
            node_ref=result_ref,
            node_kind="VERIFICATION_RESULT",
            protocol_version="verification-result-v1",
            planning_identity=handoff["planningSealDigest"],
            source_identity=source,
            verification_status="VERIFICATION_FAILED",
            payload={
                "protocolVersion": "verification-result-v1",
                "verificationResultRef": result_ref,
                "verificationStatus": "VERIFICATION_FAILED",
                "implementationHandoffRef": root_ref,
                "planningSealDigest": handoff["planningSealDigest"],
                "finalSourceIdentity": source,
                "criterionResults": [
                    {
                        **self.criteria()[0],
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
            spend=self.budget_vector(
                remediationTransactions=1, workerCalls=1, toolCostUnits=3
            ),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=2),
        )
        claim = graph.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=remediator["actorRef"],
            tip_ref=failed["nodeRef"],
            transition_kind="REMEDIATE",
            planning_identity=handoff["planningSealDigest"],
            source_identity=source,
            execution_ref=implementation_result.workflow_store.allocate_ref("REMEDIATE"),
            budget_reservation_ref=remediation_budget["reservationRef"],
        )
        return {
            "handoff": handoff,
            "coordinator": coordinator,
            "worker": worker,
            "remediator": remediator,
            "budget": remediation_budget,
            "claim": claim,
        }

    def test_remediation_handoff_closes_transaction_and_advances_failed_tip_atomically(self) -> None:
        workflow = self.failed_workflow()
        transaction = self.publisher.transactions.start_remediation(
            remediator_capability=workflow["remediator"]["capability"],
            worker_capability=workflow["worker"]["capability"],
            claim_ref=workflow["claim"]["claimRef"],
            project_root=self.project,
            admission={
                "disposition": "ADMITTED",
                "criterionRefs": self.criteria(),
                "authorityDeltaDigest": "c" * 64,
                "desiredOutcomeUnchanged": True,
                "acceptanceMeaningUnchanged": True,
                "scopeAndNonGoalsUnchanged": True,
                "materialProductDecisionRequired": False,
                "safetyAndOwnershipAuthorized": True,
            },
        )
        envelope = self.publisher.transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="remediation-1",
            criterion_refs=self.criteria(),
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.publisher.transactions.begin_worker_call(
            worker_capability=workflow["worker"]["capability"],
            envelope_ref=envelope["envelopeRef"],
        )
        (self.project / "app.txt").write_text("fixed\n", encoding="utf-8")
        self.publisher.transactions.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
        )
        self.publisher.transactions.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=envelope["envelopeRef"],
            reconciliation={
                "disposition": "CONTINUE",
                "workerAttributablePaths": ["app.txt"],
                "externalPaths": [],
                "preservedUserChanges": [],
                "externalEffectState": "CLEAR",
            },
        )
        prepared = self.publisher.transactions.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )
        graph = self.publisher.workflow
        graph.consume_budget(
            actor_capability=workflow["remediator"]["capability"],
            reservation_ref=workflow["budget"]["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        request_transaction = {**transaction, **prepared, "taskIds": ["remediation-1"]}

        handoff = self.publisher.publish(
            self.request(
                request_transaction,
                actor_capability=workflow["remediator"]["capability"],
            )
        )

        self.assertEqual(
            workflow["handoff"]["finalSourceIdentity"], handoff["baselineSourceIdentity"]
        )
        self.assertNotEqual(handoff["baselineSourceIdentity"], handoff["finalSourceIdentity"])
        self.assertEqual(
            "CLOSED_WITH_HANDOFF",
            self.publisher.transactions.read_transaction(transaction["transactionRef"])["state"],
        )
        self.assertEqual(
            handoff["implementationHandoffRef"],
            graph.current_tip(workflow["handoff"]["implementationHandoffRef"])["nodeRef"],
        )
        self.assertEqual(3, len(graph.lineage(workflow["handoff"]["implementationHandoffRef"])))

    def test_acceptance_criterion_parser_preserves_raw_ranges(self) -> None:
        self.write_ticket("- First line.\r\n  continuation.\r\n\r\n- Second line.\r\n")
        criteria = implementation_result.acceptance_criteria_from_ticket(self.ticket)
        self.assertEqual([1, 2], [item["criterionIndex"] for item in criteria])
        self.assertEqual(
            hashlib.sha256(b"- First line.\r\n  continuation.\r\n\r\n").hexdigest(),
            criteria[0]["criterionRawSha256"],
        )


if __name__ == "__main__":
    unittest.main()
