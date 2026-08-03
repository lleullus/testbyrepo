from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/workflow-store/workflow_store.py"
SPEC = importlib.util.spec_from_file_location("workflow_store", MODULE)
assert SPEC and SPEC.loader
workflow_store = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow_store)


class WorkflowStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = workflow_store.WorkflowStore(Path(self.temporary.name) / "store")
        self.planning = "a" * 64
        self.source = "sha256:" + "b" * 64
        self.root_ref = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        self.root = self.store.publish_initial_handoff(
            node_ref=self.root_ref,
            protocol_version="implementation-handoff-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            payload=self.handoff_payload(self.root_ref, self.source, self.source),
        )
        self.limits = self.budget_vector(
            workerCalls=10,
            remediationTransactions=10,
            effectfulActions=10,
            toolCostUnits=100,
            closureOperations=100,
        )
        self.invocation = self.store.start_invocation(
            root_ref=self.root_ref, elapsed_seconds=600, limits=self.limits
        )
        self.invocation_ref = self.invocation["invocationRef"]
        self.coordinator = self.invocation["coordinator"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def handoff_payload(self, ref: str, baseline: str, final: str) -> dict[str, object]:
        return {
            "protocolVersion": "implementation-handoff-v1",
            "implementationHandoffRef": ref,
            "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
            "planningSealDigest": self.planning,
            "baselineSourceIdentity": baseline,
            "finalSourceIdentity": final,
        }

    def result_payload(
        self, ref: str, handoff_ref: str, source: str, status: str
    ) -> dict[str, object]:
        return {
            "protocolVersion": "verification-result-v1",
            "verificationResultRef": ref,
            "verificationStatus": status,
            "implementationHandoffRef": handoff_ref,
            "planningSealDigest": self.planning,
            "finalSourceIdentity": source,
        }

    @staticmethod
    def budget_vector(**overrides: int) -> dict[str, int]:
        result = {field: 0 for field in workflow_store.BUDGET_FIELDS}
        result.update(overrides)
        return result

    def issue_claimant(self, role: str) -> dict[str, str]:
        return self.store.issue_actor(coordinator_capability=self.coordinator["capability"], role=role)

    def reserve(self, transition_kind: str) -> dict[str, object]:
        return self.store.reserve_budget(
            coordinator_capability=self.coordinator["capability"],
            transition_kind=transition_kind,
            spend=self.budget_vector(
                remediationTransactions=1 if transition_kind == "REMEDIATE" else 0,
                effectfulActions=1 if transition_kind == "VERIFY" else 0,
                toolCostUnits=2,
            ),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=2),
        )

    def acquire_verify(self, assessor: dict[str, str], *, tip_ref: str | None = None) -> dict[str, object]:
        tip = self.store.current_tip(self.root_ref)
        reservation = self.reserve("VERIFY")
        return self.store.acquire_claim(
            coordinator_capability=self.coordinator["capability"],
            claimant_actor_ref=assessor["actorRef"],
            tip_ref=tip_ref or tip["nodeRef"],
            transition_kind="VERIFY",
            planning_identity=tip["planningIdentity"],
            source_identity=tip["sourceIdentity"],
            execution_ref=workflow_store.allocate_ref("VERIFY"),
            budget_reservation_ref=reservation["reservationRef"],
        )

    def publish_result(
        self,
        assessor: dict[str, str],
        claim: dict[str, object],
        status: str,
    ) -> dict[str, object]:
        ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=claim["budgetReservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        return self.store.publish_successor(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
            node_ref=ref,
            node_kind="VERIFICATION_RESULT",
            protocol_version="verification-result-v1",
            planning_identity=self.planning,
            source_identity=self.store.current_tip(self.root_ref)["sourceIdentity"],
            verification_status=status,
            payload=self.result_payload(ref, self.root_ref, self.source, status),
        )

    def assert_code(self, code: str, operation) -> None:
        with self.assertRaises(workflow_store.WorkflowStoreError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)

    def test_owner_only_store_and_immutable_initial_node_round_trip(self) -> None:
        self.assertEqual(0o700, self.store.store_root.stat().st_mode & 0o777)
        self.assertEqual(0o600, self.store.database_mode())
        self.assertEqual(self.root, self.store.read_node(self.root_ref))
        self.assertEqual(self.root_ref, self.store.current_tip(self.root_ref)["nodeRef"])
        self.assert_code(
            "IMMUTABLE_NODE_EXISTS",
            lambda: self.store.publish_initial_handoff(
                node_ref=self.root_ref,
                protocol_version="implementation-handoff-v1",
                planning_identity=self.planning,
                source_identity=self.source,
                payload=self.handoff_payload(self.root_ref, self.source, self.source),
            ),
        )
        connection = sqlite3.connect(self.store.database_path)
        try:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable nodes"):
                connection.execute(
                    "UPDATE nodes SET source_identity = ? WHERE node_ref = ?",
                    ("sha256:" + "c" * 64, self.root_ref),
                )
        finally:
            connection.close()

        # The only supported in-place migration is v6 -> v7.  Reopening a v6
        # store must retain all data and install the exactly-once step guard.
        connection = sqlite3.connect(self.store.database_path)
        try:
            connection.execute(
                "UPDATE store_meta SET value = '6' WHERE key = 'schema_version'"
            )
            connection.commit()
        finally:
            connection.close()
        migrated = workflow_store.WorkflowStore(self.store.store_root)
        connection = sqlite3.connect(migrated.database_path)
        try:
            version = connection.execute(
                "SELECT value FROM store_meta WHERE key = 'schema_version'"
            ).fetchone()[0]
            step_table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'verification_step_executions'"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(str(workflow_store.SCHEMA_VERSION), version)
        self.assertEqual("verification_step_executions", step_table[0])

    def test_claim_blocks_competing_execution_before_publication(self) -> None:
        first = self.issue_claimant("ASSESSOR")
        second = self.issue_claimant("ASSESSOR")
        claim = self.acquire_verify(first)

        self.assertEqual(claim["claimRef"], self.store.active_claim(self.root_ref)["claim_ref"])
        self.assert_code("TRANSITION_CLAIM_CONFLICT", lambda: self.acquire_verify(second))

    def test_concurrent_claim_race_has_exactly_one_winner(self) -> None:
        actors = [self.issue_claimant("ASSESSOR"), self.issue_claimant("ASSESSOR")]

        def attempt(actor: dict[str, str]) -> str:
            try:
                self.acquire_verify(actor)
                return "ACQUIRED"
            except workflow_store.WorkflowStoreError as exc:
                return exc.code

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, actors))

        self.assertEqual(["ACQUIRED", "TRANSITION_CLAIM_CONFLICT"], sorted(outcomes))

    def test_matching_claim_atomically_publishes_one_successor_and_advances_tip(self) -> None:
        assessor = self.issue_claimant("ASSESSOR")
        claim = self.acquire_verify(assessor)
        result = self.publish_result(assessor, claim, "INCOMPLETE")

        self.assertEqual(result["nodeRef"], self.store.current_tip(self.root_ref)["nodeRef"])
        self.assertEqual([self.root_ref, result["nodeRef"]], [node["nodeRef"] for node in self.store.lineage(self.root_ref)])
        self.assertIsNone(self.store.active_claim(self.root_ref))
        duplicate_ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
        self.assert_code(
            "CLAIM_NOT_ACTIVE",
            lambda: self.store.publish_successor(
                claimant_capability=assessor["capability"],
                claim_ref=claim["claimRef"],
                node_ref=duplicate_ref,
                node_kind="VERIFICATION_RESULT",
                protocol_version="verification-result-v1",
                planning_identity=self.planning,
                source_identity=self.source,
                verification_status="INCOMPLETE",
                payload=self.result_payload(
                    duplicate_ref, self.root_ref, self.source, "INCOMPLETE"
                ),
            ),
        )

    def test_publication_requires_reserved_closure_work(self) -> None:
        assessor = self.issue_claimant("ASSESSOR")
        claim = self.acquire_verify(assessor)
        ref = workflow_store.allocate_ref("VERIFICATION_RESULT")

        self.assert_code(
            "CLOSURE_BUDGET_UNUSED",
            lambda: self.store.publish_successor(
                claimant_capability=assessor["capability"],
                claim_ref=claim["claimRef"],
                node_ref=ref,
                node_kind="VERIFICATION_RESULT",
                protocol_version="verification-result-v1",
                planning_identity=self.planning,
                source_identity=self.source,
                verification_status="INCOMPLETE",
                payload=self.result_payload(ref, self.root_ref, self.source, "INCOMPLETE"),
            ),
        )
        self.assertEqual(self.root_ref, self.store.current_tip(self.root_ref)["nodeRef"])
        self.assertEqual(claim["claimRef"], self.store.active_claim(self.root_ref)["claim_ref"])

        first_charge = self.store.ensure_claim_closure_budget(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
            amounts=self.budget_vector(closureOperations=1),
        )
        retry_charge = self.store.ensure_claim_closure_budget(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
            amounts=self.budget_vector(closureOperations=1),
        )
        self.assertEqual(first_charge, retry_charge)
        self.assertEqual(1, retry_charge["closureOperations"])
        result = self.store.publish_successor(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
            node_ref=ref,
            node_kind="VERIFICATION_RESULT",
            protocol_version="verification-result-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            verification_status="INCOMPLETE",
            payload=self.result_payload(ref, self.root_ref, self.source, "INCOMPLETE"),
        )
        self.assertEqual(ref, result["nodeRef"])

    def test_budget_exhaustion_blocks_new_units_without_changing_public_tip(self) -> None:
        small_store = workflow_store.WorkflowStore(Path(self.temporary.name) / "budget-store")
        root_ref = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        small_store.publish_initial_handoff(
            node_ref=root_ref,
            protocol_version="implementation-handoff-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            payload=self.handoff_payload(root_ref, self.source, self.source),
        )
        self.assert_code_for_store(
            small_store,
            "MALFORMED_BUDGET",
            lambda: small_store.start_invocation(
                root_ref=root_ref,
                elapsed_seconds=60,
                limits=self.budget_vector(effectfulActions=1),
            ),
        )
        started = datetime(2026, 8, 3, tzinfo=timezone.utc)
        invocation = small_store.start_invocation(
            root_ref=root_ref,
            elapsed_seconds=1,
            limits=self.budget_vector(effectfulActions=1, toolCostUnits=3, closureOperations=2),
            now=started,
        )
        coordinator = invocation["coordinator"]
        self.assert_code_for_store(
            small_store,
            "MALFORMED_BUDGET",
            lambda: small_store.reserve_budget(
                coordinator_capability=coordinator["capability"],
                transition_kind="VERIFY",
                spend=self.budget_vector(),
                closure_reserve=self.budget_vector(),
                now=started,
            ),
        )
        assessor = small_store.issue_actor(
            coordinator_capability=coordinator["capability"], role="ASSESSOR"
        )
        reservation = small_store.reserve_budget(
            coordinator_capability=coordinator["capability"],
            transition_kind="VERIFY",
            spend=self.budget_vector(effectfulActions=1, toolCostUnits=2),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=1),
            now=started,
        )
        claim = small_store.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=assessor["actorRef"],
            tip_ref=root_ref,
            transition_kind="VERIFY",
            planning_identity=self.planning,
            source_identity=self.source,
            execution_ref=workflow_store.allocate_ref("VERIFY"),
            budget_reservation_ref=reservation["reservationRef"],
            now=started,
        )

        with self.assertRaises(workflow_store.WorkflowStoreError) as raised:
            small_store.reserve_budget(
                coordinator_capability=coordinator["capability"],
                transition_kind="VERIFY",
                spend=self.budget_vector(),
                closure_reserve=self.budget_vector(closureOperations=1),
                now=started + timedelta(seconds=2),
            )
        self.assertEqual("BUDGET_EXHAUSTED", raised.exception.code)
        self.assertEqual(root_ref, small_store.current_tip(root_ref)["nodeRef"])

        self.assert_code_for_store(
            small_store,
            "BUDGET_EXHAUSTED",
            lambda: small_store.consume_budget(
                actor_capability=assessor["capability"],
                reservation_ref=reservation["reservationRef"],
                category="SPEND",
                amounts=self.budget_vector(effectfulActions=1),
                now=started + timedelta(seconds=2),
            ),
        )

        # An already claimed unit retains its reserved containment/closure capacity.
        small_store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=reservation["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        result_ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
        result = small_store.publish_successor(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
            node_ref=result_ref,
            node_kind="VERIFICATION_RESULT",
            protocol_version="verification-result-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            verification_status="INCOMPLETE",
            payload=self.result_payload(result_ref, root_ref, self.source, "INCOMPLETE"),
        )
        self.assertEqual(result_ref, result["nodeRef"])

    def test_role_capabilities_cannot_cross_claim_or_publication_boundaries(self) -> None:
        remediator = self.issue_claimant("REMEDIATOR")
        verify_reservation = self.reserve("VERIFY")
        self.assert_code(
            "ROLE_CAPABILITY_MISMATCH",
            lambda: self.store.acquire_claim(
                coordinator_capability=self.coordinator["capability"],
                claimant_actor_ref=remediator["actorRef"],
                tip_ref=self.root_ref,
                transition_kind="VERIFY",
                planning_identity=self.planning,
                source_identity=self.source,
                execution_ref=workflow_store.allocate_ref("VERIFY"),
                budget_reservation_ref=verify_reservation["reservationRef"],
            ),
        )

        assessor = self.issue_claimant("ASSESSOR")
        claim = self.acquire_verify(assessor)
        ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
        self.assert_code(
            "CLAIM_ACTOR_MISMATCH",
            lambda: self.store.consume_budget(
                actor_capability=remediator["capability"],
                reservation_ref=claim["budgetReservationRef"],
                category="CLOSURE",
                amounts=self.budget_vector(closureOperations=1),
            ),
        )
        self.assert_code(
            "CLAIM_ACTOR_MISMATCH",
            lambda: self.store.publish_successor(
                claimant_capability=remediator["capability"],
                claim_ref=claim["claimRef"],
                node_ref=ref,
                node_kind="VERIFICATION_RESULT",
                protocol_version="verification-result-v1",
                planning_identity=self.planning,
                source_identity=self.source,
                verification_status="INCOMPLETE",
                payload=self.result_payload(ref, self.root_ref, self.source, "INCOMPLETE"),
            ),
        )

    def test_incomplete_allows_fresh_verify_but_reusing_actor_is_rejected(self) -> None:
        first = self.issue_claimant("ASSESSOR")
        first_claim = self.acquire_verify(first)
        first_result = self.publish_result(first, first_claim, "INCOMPLETE")

        reuse_reservation = self.reserve("VERIFY")
        self.assert_code(
            "ACTOR_CONTEXT_REUSED",
            lambda: self.store.acquire_claim(
                coordinator_capability=self.coordinator["capability"],
                claimant_actor_ref=first["actorRef"],
                tip_ref=first_result["nodeRef"],
                transition_kind="VERIFY",
                planning_identity=self.planning,
                source_identity=self.source,
                execution_ref=workflow_store.allocate_ref("VERIFY"),
                budget_reservation_ref=reuse_reservation["reservationRef"],
            ),
        )
        second = self.issue_claimant("ASSESSOR")
        second_claim = self.acquire_verify(second)
        self.assertEqual(first_result["nodeRef"], second_claim["tipRef"])

    def test_verified_is_terminal_and_failed_allows_only_remediation(self) -> None:
        assessor = self.issue_claimant("ASSESSOR")
        verified_claim = self.acquire_verify(assessor)
        verified = self.publish_result(assessor, verified_claim, "VERIFIED")
        later = self.issue_claimant("ASSESSOR")
        self.assert_code("TRANSITION_NOT_ALLOWED", lambda: self.acquire_verify(later))

        other_root = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        other_store = workflow_store.WorkflowStore(Path(self.temporary.name) / "other-store")
        other_store.publish_initial_handoff(
            node_ref=other_root,
            protocol_version="implementation-handoff-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            payload=self.handoff_payload(other_root, self.source, self.source),
        )
        invocation = other_store.start_invocation(
            root_ref=other_root, elapsed_seconds=600, limits=self.limits
        )
        coordinator = invocation["coordinator"]
        failed_assessor = other_store.issue_actor(
            coordinator_capability=coordinator["capability"], role="ASSESSOR"
        )
        verify_reservation = other_store.reserve_budget(
            coordinator_capability=coordinator["capability"],
            transition_kind="VERIFY",
            spend=self.budget_vector(effectfulActions=1, toolCostUnits=2),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=2),
        )
        claim = other_store.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=failed_assessor["actorRef"],
            tip_ref=other_root,
            transition_kind="VERIFY",
            planning_identity=self.planning,
            source_identity=self.source,
            execution_ref=workflow_store.allocate_ref("VERIFY"),
            budget_reservation_ref=verify_reservation["reservationRef"],
        )
        other_store.consume_budget(
            actor_capability=failed_assessor["capability"],
            reservation_ref=verify_reservation["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        result_ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
        failed = other_store.publish_successor(
            claimant_capability=failed_assessor["capability"],
            claim_ref=claim["claimRef"],
            node_ref=result_ref,
            node_kind="VERIFICATION_RESULT",
            protocol_version="verification-result-v1",
            planning_identity=self.planning,
            source_identity=self.source,
            verification_status="VERIFICATION_FAILED",
            payload=self.result_payload(result_ref, other_root, self.source, "VERIFICATION_FAILED"),
        )
        retry_assessor = other_store.issue_actor(
            coordinator_capability=coordinator["capability"], role="ASSESSOR"
        )
        retry_reservation = other_store.reserve_budget(
            coordinator_capability=coordinator["capability"],
            transition_kind="VERIFY",
            spend=self.budget_vector(effectfulActions=1, toolCostUnits=2),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=2),
        )
        self.assert_code_for_store(
            other_store,
            "TRANSITION_NOT_ALLOWED",
            lambda: other_store.acquire_claim(
                coordinator_capability=coordinator["capability"],
                claimant_actor_ref=retry_assessor["actorRef"],
                tip_ref=failed["nodeRef"],
                transition_kind="VERIFY",
                planning_identity=self.planning,
                source_identity=self.source,
                execution_ref=workflow_store.allocate_ref("VERIFY"),
                budget_reservation_ref=retry_reservation["reservationRef"],
            ),
        )
        remediator = other_store.issue_actor(
            coordinator_capability=coordinator["capability"], role="REMEDIATOR"
        )
        remediation_reservation = other_store.reserve_budget(
            coordinator_capability=coordinator["capability"],
            transition_kind="REMEDIATE",
            spend=self.budget_vector(remediationTransactions=1, toolCostUnits=2),
            closure_reserve=self.budget_vector(toolCostUnits=1, closureOperations=2),
        )
        remediation_claim = other_store.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=remediator["actorRef"],
            tip_ref=failed["nodeRef"],
            transition_kind="REMEDIATE",
            planning_identity=self.planning,
            source_identity=self.source,
            execution_ref=workflow_store.allocate_ref("REMEDIATE"),
            budget_reservation_ref=remediation_reservation["reservationRef"],
        )
        self.assertEqual("REMEDIATE", remediation_claim["transitionKind"])
        self.assertEqual(verified["verificationStatus"], "VERIFIED")

    def test_remediation_successor_requires_claim_bound_ready_transaction(self) -> None:
        assessor = self.issue_claimant("ASSESSOR")
        verify_claim = self.acquire_verify(assessor)
        failed = self.publish_result(assessor, verify_claim, "VERIFICATION_FAILED")
        remediator = self.issue_claimant("REMEDIATOR")
        remediation_reservation = self.reserve("REMEDIATE")
        remediation_claim = self.store.acquire_claim(
            coordinator_capability=self.coordinator["capability"],
            claimant_actor_ref=remediator["actorRef"],
            tip_ref=failed["nodeRef"],
            transition_kind="REMEDIATE",
            planning_identity=self.planning,
            source_identity=self.source,
            execution_ref=workflow_store.allocate_ref("REMEDIATE"),
            budget_reservation_ref=remediation_reservation["reservationRef"],
        )
        self.store.consume_budget(
            actor_capability=remediator["capability"],
            reservation_ref=remediation_reservation["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )

        same_ref = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        self.assert_code(
            "IMPLEMENTATION_TRANSACTION_NOT_READY",
            lambda: self.store.publish_successor(
                claimant_capability=remediator["capability"],
                claim_ref=remediation_claim["claimRef"],
                node_ref=same_ref,
                node_kind="IMPLEMENTATION_HANDOFF",
                protocol_version="implementation-handoff-v1",
                planning_identity=self.planning,
                source_identity=self.source,
                verification_status=None,
                payload=self.handoff_payload(same_ref, self.source, self.source),
            ),
        )

    def assert_code_for_store(self, store, code: str, operation) -> None:
        with self.assertRaises(workflow_store.WorkflowStoreError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
