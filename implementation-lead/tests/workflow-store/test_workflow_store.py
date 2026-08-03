from __future__ import annotations

import importlib.util
import hashlib
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/workflow-store/workflow_store.py"
V7_SCHEMA_FIXTURE = ROOT / "tests/workflow-store/fixtures/workflow-schema-v7.sql"
SPEC = importlib.util.spec_from_file_location("workflow_store", MODULE)
assert SPEC and SPEC.loader
workflow_store = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow_store)


class WorkflowStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.audit_private = self.base / "audit-private"
        self.audit_private.mkdir(mode=0o700)
        self.guard_sequence = 0
        self.store = self.open_store(self.base / "store")
        self.planning = "a" * 64
        self.source = "sha256:" + "b" * 64
        self.root_ref = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        self.root = self.seed_initial_handoff(
            self.store,
            self.root_ref,
            self.planning,
            self.source,
            self.handoff_payload(self.root_ref, self.source, self.source),
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

    def guard(self, store_root: Path, label: str = "open"):
        self.guard_sequence += 1
        return workflow_store._mint_test_guard_session(
            store_root=store_root,
            identity=f"workflow-store-test:{label}:{self.guard_sequence}",
            is_active=lambda: True,
        )

    def open_store(self, root: Path, *, migration_hook=None):
        return workflow_store.audit_and_open_workflow_store(
            root,
            guard=self.guard(root, root.name),
            private_parent=self.audit_private,
            _migration_hook=migration_hook,
        ).store

    @staticmethod
    def create_v7_fixture(root: Path) -> Path:
        root.mkdir(mode=0o700)
        database = root / "workflow.sqlite3"
        connection = sqlite3.connect(database)
        try:
            connection.executescript(V7_SCHEMA_FIXTURE.read_text(encoding="utf-8"))
            connection.commit()
        finally:
            connection.close()
        database.chmod(0o600)
        return database

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

    @staticmethod
    def seed_initial_handoff(
        store,
        node_ref: str,
        planning_identity: str,
        source_identity: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        """Seed mechanics-only lineage without adding a production publication API."""
        encoded = workflow_store.canonical_json(payload)
        created_at = workflow_store.utc_now()
        with store._transaction() as connection:
            connection.execute(
                """
                INSERT INTO nodes(
                    node_ref, node_kind, protocol_version, root_ref, planning_identity,
                    source_identity, verification_status, payload_json, payload_sha256, created_at
                ) VALUES (?, 'IMPLEMENTATION_HANDOFF', 'implementation-handoff-v1', ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    node_ref,
                    node_ref,
                    planning_identity,
                    source_identity,
                    encoded,
                    hashlib.sha256(encoded).hexdigest(),
                    created_at,
                ),
            )
        return store.read_node(node_ref)

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

    def acquire_release_candidate(
        self,
        *,
        spend_reserved: dict[str, int] | None = None,
        closure_reserved: dict[str, int] | None = None,
    ) -> tuple[dict[str, str], dict[str, object], dict[str, object]]:
        assessor = self.issue_claimant("ASSESSOR")
        reservation = self.store.reserve_budget(
            coordinator_capability=self.coordinator["capability"],
            transition_kind="VERIFY",
            spend=spend_reserved
            or self.budget_vector(effectfulActions=2, toolCostUnits=4),
            closure_reserve=closure_reserved
            or self.budget_vector(toolCostUnits=2, closureOperations=2),
        )
        claim = self.store.acquire_claim(
            coordinator_capability=self.coordinator["capability"],
            claimant_actor_ref=assessor["actorRef"],
            tip_ref=self.root_ref,
            transition_kind="VERIFY",
            planning_identity=self.planning,
            source_identity=self.source,
            execution_ref=workflow_store.allocate_ref("VERIFY"),
            budget_reservation_ref=reservation["reservationRef"],
        )
        return assessor, reservation, claim

    def release_rows(
        self, reservation_ref: str, claim_ref: str
    ) -> tuple[dict[str, int], str, str]:
        connection = self.store._connect()
        try:
            invocation = connection.execute(
                "SELECT consumed_json FROM invocations WHERE invocation_ref = ?",
                (self.invocation_ref,),
            ).fetchone()
            claim = connection.execute(
                "SELECT state FROM claims WHERE claim_ref = ?", (claim_ref,)
            ).fetchone()
            reservation = connection.execute(
                "SELECT state FROM budget_reservations WHERE reservation_ref = ?",
                (reservation_ref,),
            ).fetchone()
        finally:
            connection.close()
        return (
            self.store._stored_budget(invocation["consumed_json"], "invocation.consumed"),
            claim["state"],
            reservation["state"],
        )

    def publish_result_fixture(
        self,
        store,
        root_ref: str,
        assessor: dict[str, str],
        claim: dict[str, object],
        status: str,
        *,
        planning_identity: str,
        source_identity: str,
        charge_closure: bool = True,
    ) -> dict[str, object]:
        ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
        payload = {
            "protocolVersion": "verification-result-v1",
            "verificationResultRef": ref,
            "verificationStatus": status,
            "implementationHandoffRef": root_ref,
            "planningSealDigest": planning_identity,
            "finalSourceIdentity": source_identity,
        }
        payload.update(
            {
                "verificationRunRef": claim["executionRef"],
                "sealedPlanDigest": None,
            }
        )
        with store._transaction() as connection:
            preflight = workflow_store.canonical_json(
                {"stage": "TERMINAL", "draftDigest": "0" * 64, "observations": []}
            )
            connection.execute(
                """
                INSERT INTO verification_runs(
                    run_ref, root_ref, claim_ref, assessor_actor_ref,
                    implementation_handoff_ref, project_root, planning_identity,
                    source_identity, preflight_json, sealed_plan_json,
                    sealed_plan_sha256, state, closure_json, created_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, '/test', ?, ?, ?, NULL, NULL, 'PREFLIGHT', NULL, ?, NULL)
                """,
                (
                    claim["executionRef"],
                    root_ref,
                    claim["claimRef"],
                    assessor["actorRef"],
                    root_ref,
                    planning_identity,
                    source_identity,
                    preflight,
                    workflow_store.utc_now(),
                ),
            )
            if charge_closure:
                store._ensure_claim_closure_budget_locked(
                    connection,
                    claimant_capability=assessor["capability"],
                    claim_ref=claim["claimRef"],
                    amounts=self.budget_vector(closureOperations=1),
                )
            return store._close_successor_locked(
                connection,
                claimant_capability=assessor["capability"],
                claim_ref=claim["claimRef"],
                node_ref=ref,
                node_kind="VERIFICATION_RESULT",
                protocol_version="verification-result-v1",
                planning_identity=planning_identity,
                source_identity=source_identity,
                verification_status=status,
                payload=payload,
                verification_run_ref=claim["executionRef"],
                created_at=workflow_store.utc_now(),
            )

    def publish_result(
        self,
        assessor: dict[str, str],
        claim: dict[str, object],
        status: str,
    ) -> dict[str, object]:
        return self.publish_result_fixture(
            self.store,
            self.root_ref,
            assessor,
            claim,
            status,
            planning_identity=self.planning,
            source_identity=self.source,
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
            "PUBLICATION_SURFACE_RETIRED",
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

    def test_direct_constructor_is_retired_before_filesystem_or_sqlite_side_effects(self) -> None:
        root = self.base / "direct-constructor-must-not-exist"
        with patch.object(workflow_store.sqlite3, "connect") as connect:
            self.assert_code(
                "AUDITED_OPEN_REQUIRED", lambda: workflow_store.WorkflowStore(root)
            )
        connect.assert_not_called()
        self.assertFalse(root.exists())

    def test_public_factory_cannot_replace_pinned_schema_authority(self) -> None:
        root = self.base / "schema-authority-override-must-not-exist"
        self.assertFalse(hasattr(workflow_store, "GuardSession"))
        with self.assertRaises(TypeError):
            workflow_store.audit_and_open_workflow_store(
                root,
                guard=self.guard(root, "schema-authority"),
                private_parent=self.audit_private,
                expected_schema_fingerprints={9: {"0" * 64}},
            )
        self.assertFalse(root.exists())

    def test_inactive_guard_blocks_factory_before_mkdir_chmod_or_sqlite(self) -> None:
        root = self.base / "guard-blocked-root"
        guard = workflow_store._mint_test_guard_session(
            store_root=root,
            identity="workflow-store-test:inactive",
            is_active=lambda: False,
        )
        with patch.object(Path, "mkdir") as mkdir, patch.object(
            workflow_store.os, "chmod"
        ) as chmod, patch.object(workflow_store.sqlite3, "connect") as connect:
            self.assert_code(
                "AUDIT_GUARD_NOT_HELD",
                lambda: workflow_store.audit_and_open_workflow_store(
                    root,
                    guard=guard,
                    private_parent=self.audit_private,
                ),
            )
        mkdir.assert_not_called()
        chmod.assert_not_called()
        connect.assert_not_called()
        self.assertFalse(root.exists())

    def test_locked_fd_guard_is_live_for_audited_open_and_fails_after_close(self) -> None:
        lock_path = self.base / "deployment.lock"
        store_root = self.base / "fd-guard-store"
        with lock_path.open("w+") as lock_stream:
            guard = workflow_store.guard_session_from_locked_fd(
                lock_stream.fileno(), store_root=store_root
            )
            opened = workflow_store.audit_and_open_workflow_store(
                store_root,
                guard=guard,
                private_parent=self.audit_private,
            )
            self.assertEqual("EXCLUSIVE_LOCK", opened.report.guard_kind)
            guard.assert_active()
            other_root = self.base / "wrong-guard-root"
            self.assert_code(
                "AUDIT_GUARD_ROOT_MISMATCH",
                lambda: workflow_store.audit_and_open_workflow_store(
                    other_root,
                    guard=guard,
                    private_parent=self.audit_private,
                ),
            )
            self.assertFalse(other_root.exists())
        with self.assertRaises(RuntimeError):
            guard.assert_active()

        read_fd, write_fd = workflow_store.os.pipe()
        try:
            self.assert_code(
                "AUDIT_GUARD_NOT_HELD",
                lambda: workflow_store.guard_session_from_locked_fd(
                    read_fd, store_root=self.base / "invalid-fd-root"
                ),
            )
        finally:
            workflow_store.os.close(read_fd)
            workflow_store.os.close(write_fd)

    def test_actual_pinned_v7_fixture_migrates_atomically_to_v9(self) -> None:
        root = self.base / "actual-v7"
        database = self.create_v7_fixture(root)

        migrated = self.open_store(root)
        connection = sqlite3.connect(database)
        try:
            meta = dict(connection.execute("SELECT key, value FROM store_meta"))
            indexes = {
                row[1]: (row[2], row[4])
                for row in connection.execute(
                    "PRAGMA index_list('implementation_envelopes')"
                )
            }
            table_sql = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'implementation_envelopes'"
            ).fetchone()[0]
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            connection.close()
        self.assertEqual(str(workflow_store.SCHEMA_VERSION), meta["schema_version"])
        self.assertEqual(workflow_store.EXECUTOR_FLOOR, meta["executor_floor"])
        self.assertEqual((0, 0), indexes["implementation_envelopes_by_transaction"])
        self.assertEqual((1, 1), indexes["one_active_envelope_per_transaction"])
        self.assertNotIn("UNIQUE(transaction_ref, task_id)", table_sql)
        self.assertEqual([], foreign_keys)
        self.assertEqual(database, migrated.database_path)
        reopened = self.open_store(root)
        self.assertEqual(9, reopened.audit_report.schema_version)
        self.assertEqual(
            "209e0d14c52fe855b7ca90794b64e087561b62a28296c2ac0b14a33125c4446a",
            reopened.audit_report.schema_fingerprint,
        )

    def test_each_v7_migration_failpoint_rolls_back_table_indexes_and_version(self) -> None:
        for stage in (
            "after_rename",
            "after_copy",
            "after_indexes",
            "before_version",
            "after_version",
        ):
            with self.subTest(stage=stage):
                root = self.base / f"rollback-{stage}"
                database = self.create_v7_fixture(root)

                def failpoint(observed: str, *, expected: str = stage) -> None:
                    if observed == expected:
                        raise RuntimeError(f"migration failpoint: {expected}")

                with self.assertRaisesRegex(RuntimeError, stage):
                    self.open_store(root, migration_hook=failpoint)

                connection = sqlite3.connect(database)
                try:
                    meta = dict(connection.execute("SELECT key, value FROM store_meta"))
                    table_sql = connection.execute(
                        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'implementation_envelopes'"
                    ).fetchone()[0]
                    stale_table = connection.execute(
                        "SELECT name FROM sqlite_master WHERE name = 'implementation_envelopes_v7'"
                    ).fetchone()
                    indexes = {
                        row[1]
                        for row in connection.execute(
                            "PRAGMA index_list('implementation_envelopes')"
                        )
                    }
                finally:
                    connection.close()
                self.assertEqual("7", meta["schema_version"])
                self.assertNotIn("executor_floor", meta)
                self.assertIn("UNIQUE(transaction_ref, task_id)", table_sql)
                self.assertIsNone(stale_table)
                self.assertNotIn("implementation_envelopes_by_transaction", indexes)
                self.assertNotIn("one_active_envelope_per_transaction", indexes)

    def test_v6_metadata_on_actual_v7_shape_is_blocked_without_source_mutation(self) -> None:
        root = self.base / "unverified-v6"
        database = self.create_v7_fixture(root)
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "UPDATE store_meta SET value = '6' WHERE key = 'schema_version'"
            )
            connection.commit()
        finally:
            connection.close()
        before = database.read_bytes()

        self.assert_code(
            "WORKFLOW_STORE_OPEN_BLOCKED", lambda: self.open_store(root)
        )

        self.assertEqual(before, database.read_bytes())
        self.assertFalse(Path(f"{database}-wal").exists())
        self.assertFalse(Path(f"{database}-shm").exists())

    def test_public_generic_publication_bypass_is_retired_for_all_four_statuses(self) -> None:
        assessor = self.issue_claimant("ASSESSOR")
        claim = self.acquire_verify(assessor)
        self.store.ensure_claim_closure_budget(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
            amounts=self.budget_vector(closureOperations=1),
        )

        for status in ("VERIFIED", "VERIFICATION_FAILED", "INCOMPLETE", "BLOCKED"):
            result_ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
            self.assert_code(
                "PUBLICATION_SURFACE_RETIRED",
                lambda status=status, result_ref=result_ref: self.store.publish_successor(
                    claimant_capability=assessor["capability"],
                    claim_ref=claim["claimRef"],
                    node_ref=result_ref,
                    node_kind="VERIFICATION_RESULT",
                    protocol_version="verification-result-v1",
                    planning_identity=self.planning,
                    source_identity=self.source,
                    verification_status=status,
                    payload=self.result_payload(result_ref, self.root_ref, self.source, status),
                ),
            )

        self.assertEqual(self.root_ref, self.store.current_tip(self.root_ref)["nodeRef"])
        self.assertEqual(claim["claimRef"], self.store.active_claim(self.root_ref)["claim_ref"])

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
            "PUBLICATION_SURFACE_RETIRED",
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
        self.assert_code(
            "CLOSURE_BUDGET_UNUSED",
            lambda: self.publish_result_fixture(
                self.store,
                self.root_ref,
                assessor,
                claim,
                "INCOMPLETE",
                planning_identity=self.planning,
                source_identity=self.source,
                charge_closure=False,
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
        result = self.publish_result_fixture(
            self.store,
            self.root_ref,
            assessor,
            claim,
            "INCOMPLETE",
            planning_identity=self.planning,
            source_identity=self.source,
            charge_closure=False,
        )
        self.assertEqual(result["nodeRef"], self.store.current_tip(self.root_ref)["nodeRef"])

    def test_budget_exhaustion_blocks_new_units_without_changing_public_tip(self) -> None:
        small_store = self.open_store(self.base / "budget-store")
        root_ref = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        self.seed_initial_handoff(
            small_store,
            root_ref,
            self.planning,
            self.source,
            self.handoff_payload(root_ref, self.source, self.source),
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
        result = self.publish_result_fixture(
            small_store,
            root_ref,
            assessor,
            claim,
            "INCOMPLETE",
            planning_identity=self.planning,
            source_identity=self.source,
            charge_closure=False,
        )
        self.assertEqual(result["nodeRef"], small_store.current_tip(root_ref)["nodeRef"])

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
            "PUBLICATION_SURFACE_RETIRED",
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
        other_store = self.open_store(self.base / "other-store")
        self.seed_initial_handoff(
            other_store,
            other_root,
            self.planning,
            self.source,
            self.handoff_payload(other_root, self.source, self.source),
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
        failed = self.publish_result_fixture(
            other_store,
            other_root,
            failed_assessor,
            claim,
            "VERIFICATION_FAILED",
            planning_identity=self.planning,
            source_identity=self.source,
            charge_closure=False,
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
            "PUBLICATION_SURFACE_RETIRED",
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

    def test_release_unstarted_claim_conserves_zero_spend_closure_and_both_usage(self) -> None:
        cases = (
            ("zero", self.budget_vector(), self.budget_vector()),
            (
                "spend",
                self.budget_vector(effectfulActions=1, toolCostUnits=2),
                self.budget_vector(),
            ),
            (
                "closure",
                self.budget_vector(),
                self.budget_vector(toolCostUnits=1, closureOperations=1),
            ),
            (
                "both",
                self.budget_vector(effectfulActions=1, toolCostUnits=2),
                self.budget_vector(toolCostUnits=1, closureOperations=1),
            ),
        )
        expected = self.budget_vector()
        for name, spend_used, closure_used in cases:
            with self.subTest(name=name):
                assessor, reservation, claim = self.acquire_release_candidate()
                if any(spend_used.values()):
                    self.store.consume_budget(
                        actor_capability=assessor["capability"],
                        reservation_ref=reservation["reservationRef"],
                        category="SPEND",
                        amounts=spend_used,
                    )
                if any(closure_used.values()):
                    self.store.consume_budget(
                        actor_capability=assessor["capability"],
                        reservation_ref=reservation["reservationRef"],
                        category="CLOSURE",
                        amounts=closure_used,
                    )
                released = self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"],
                    claim_ref=claim["claimRef"],
                )
                expected = {
                    field: expected[field] + spend_used[field] + closure_used[field]
                    for field in workflow_store.BUDGET_FIELDS
                }
                consumed, claim_state, reservation_state = self.release_rows(
                    reservation["reservationRef"], claim["claimRef"]
                )
                self.assertEqual("RELEASED", released["state"])
                self.assertEqual(expected, consumed)
                self.assertEqual("RELEASED", claim_state)
                self.assertEqual("CLOSED", reservation_state)

    def test_audited_reopen_preserves_unstarted_claim_release_for_both_transitions(
        self,
    ) -> None:
        assessor, verify_reservation, verify_claim = self.acquire_release_candidate()
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=verify_reservation["reservationRef"],
            category="SPEND",
            amounts=self.budget_vector(effectfulActions=1, toolCostUnits=1),
        )
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=verify_reservation["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(toolCostUnits=1, closureOperations=1),
        )
        reopened = self.open_store(self.store.store_root)
        verify_release = reopened.release_unstarted_claim(
            claimant_capability=assessor["capability"],
            claim_ref=verify_claim["claimRef"],
        )
        self.assertEqual("RELEASED", verify_release["state"])
        self.assertTrue(str(verify_release["closureRef"]).startswith("closure:unstarted:v2:"))
        self.open_store(self.store.store_root)

        failed_assessor = self.issue_claimant("ASSESSOR")
        failed_claim = self.acquire_verify(failed_assessor)
        failed = self.publish_result(failed_assessor, failed_claim, "VERIFICATION_FAILED")
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
        reopened = self.open_store(self.store.store_root)
        remediation_release = reopened.release_unstarted_claim(
            claimant_capability=remediator["capability"],
            claim_ref=remediation_claim["claimRef"],
        )
        self.assertEqual("RELEASED", remediation_release["state"])
        self.assertTrue(
            str(remediation_release["closureRef"]).startswith("closure:unstarted:v2:")
        )
        self.open_store(self.store.store_root)

    def test_conserved_release_reopen_rejects_missing_invocation_consumption(
        self,
    ) -> None:
        assessor, reservation, claim = self.acquire_release_candidate()
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=reservation["reservationRef"],
            category="SPEND",
            amounts=self.budget_vector(effectfulActions=1, toolCostUnits=1),
        )
        released = self.store.release_unstarted_claim(
            claimant_capability=assessor["capability"],
            claim_ref=claim["claimRef"],
        )
        self.assertTrue(str(released["closureRef"]).startswith("closure:unstarted:v2:"))

        connection = sqlite3.connect(self.store.database_path)
        try:
            connection.execute(
                "UPDATE invocations SET consumed_json = ? WHERE invocation_ref = ?",
                (workflow_store.canonical_json(self.budget_vector()), self.invocation_ref),
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaises(workflow_store.WorkflowStoreError) as raised:
            self.open_store(self.store.store_root)
        self.assertEqual("WORKFLOW_STORE_OPEN_BLOCKED", raised.exception.code)
        self.assertIn("CONSERVED_USAGE_MISSING_FROM_INVOCATION", raised.exception.message)

    def test_zero_usage_release_reclaims_full_budget_for_re_reservation(self) -> None:
        spend = self.budget_vector(
            workerCalls=10,
            remediationTransactions=10,
            effectfulActions=10,
            toolCostUnits=90,
        )
        closure = self.budget_vector(toolCostUnits=10, closureOperations=100)
        assessor, reservation, claim = self.acquire_release_candidate(
            spend_reserved=spend,
            closure_reserved=closure,
        )

        self.store.release_unstarted_claim(
            claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
        )
        replacement = self.store.reserve_budget(
            coordinator_capability=self.coordinator["capability"],
            transition_kind="VERIFY",
            spend=spend,
            closure_reserve=closure,
        )

        self.assertEqual("ACTIVE", replacement["state"])
        consumed, claim_state, reservation_state = self.release_rows(
            reservation["reservationRef"], claim["claimRef"]
        )
        self.assertEqual(self.budget_vector(), consumed)
        self.assertEqual("RELEASED", claim_state)
        self.assertEqual("CLOSED", reservation_state)

    def test_repeated_release_is_rejected_without_double_consumption(self) -> None:
        assessor, reservation, claim = self.acquire_release_candidate()
        spend = self.budget_vector(effectfulActions=1, toolCostUnits=1)
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=reservation["reservationRef"],
            category="SPEND",
            amounts=spend,
        )
        self.store.release_unstarted_claim(
            claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
        )
        before, _, _ = self.release_rows(reservation["reservationRef"], claim["claimRef"])

        self.assert_code(
            "CLAIM_NOT_ACTIVE",
            lambda: self.store.release_unstarted_claim(
                claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
            ),
        )
        after, claim_state, reservation_state = self.release_rows(
            reservation["reservationRef"], claim["claimRef"]
        )
        self.assertEqual(before, after)
        self.assertEqual("RELEASED", claim_state)
        self.assertEqual("CLOSED", reservation_state)

    def test_release_with_durable_transition_fact_preserves_active_accounting(self) -> None:
        assessor, reservation, claim = self.acquire_release_candidate()
        with self.store._transaction() as connection:
            preflight = workflow_store.canonical_json(
                {"stage": "STARTED", "draftDigest": "0" * 64, "observations": []}
            )
            connection.execute(
                """
                INSERT INTO verification_runs(
                    run_ref, root_ref, claim_ref, assessor_actor_ref,
                    implementation_handoff_ref, project_root, planning_identity,
                    source_identity, preflight_json, sealed_plan_json,
                    sealed_plan_sha256, state, closure_json, created_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, '/test', ?, ?, ?, NULL, NULL, 'PREFLIGHT', NULL, ?, NULL)
                """,
                (
                    claim["executionRef"],
                    self.root_ref,
                    claim["claimRef"],
                    assessor["actorRef"],
                    self.root_ref,
                    self.planning,
                    self.source,
                    preflight,
                    workflow_store.utc_now(),
                ),
            )

        self.assert_code(
            "CLAIM_HAS_DURABLE_FACTS",
            lambda: self.store.release_unstarted_claim(
                claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
            ),
        )
        consumed, claim_state, reservation_state = self.release_rows(
            reservation["reservationRef"], claim["claimRef"]
        )
        self.assertEqual(self.budget_vector(), consumed)
        self.assertEqual("ACTIVE", claim_state)
        self.assertEqual("ACTIVE", reservation_state)

    def test_release_rejects_each_malformed_reservation_vector_without_mutation(self) -> None:
        for column in (
            "spend_reserved_json",
            "closure_reserved_json",
            "spend_used_json",
            "closure_used_json",
        ):
            with self.subTest(column=column):
                assessor, reservation, claim = self.acquire_release_candidate()
                connection = self.store._connect()
                try:
                    original = connection.execute(
                        f"SELECT {column} FROM budget_reservations WHERE reservation_ref = ?",
                        (reservation["reservationRef"],),
                    ).fetchone()[0]
                    connection.execute(
                        f"UPDATE budget_reservations SET {column} = ? WHERE reservation_ref = ?",
                        (workflow_store.canonical_json({}), reservation["reservationRef"]),
                    )
                finally:
                    connection.close()
                self.assert_code(
                    "STORE_CORRUPT",
                    lambda: self.store.release_unstarted_claim(
                        claimant_capability=assessor["capability"],
                        claim_ref=claim["claimRef"],
                    ),
                )
                consumed, claim_state, reservation_state = self.release_rows(
                    reservation["reservationRef"], claim["claimRef"]
                )
                self.assertEqual(self.budget_vector(), consumed)
                self.assertEqual("ACTIVE", claim_state)
                self.assertEqual("ACTIVE", reservation_state)
                connection = self.store._connect()
                try:
                    connection.execute(
                        f"UPDATE budget_reservations SET {column} = ? WHERE reservation_ref = ?",
                        (original, reservation["reservationRef"]),
                    )
                finally:
                    connection.close()
                self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
                )

    def test_release_rejects_malformed_invocation_vectors_without_mutation(self) -> None:
        for column in ("limits_json", "consumed_json"):
            with self.subTest(column=column):
                assessor, reservation, claim = self.acquire_release_candidate()
                connection = self.store._connect()
                try:
                    original = connection.execute(
                        f"SELECT {column} FROM invocations WHERE invocation_ref = ?",
                        (self.invocation_ref,),
                    ).fetchone()[0]
                    connection.execute(
                        f"UPDATE invocations SET {column} = ? WHERE invocation_ref = ?",
                        (workflow_store.canonical_json({}), self.invocation_ref),
                    )
                finally:
                    connection.close()
                self.assert_code(
                    "STORE_CORRUPT",
                    lambda: self.store.release_unstarted_claim(
                        claimant_capability=assessor["capability"],
                        claim_ref=claim["claimRef"],
                    ),
                )
                connection = self.store._connect()
                try:
                    claim_state = connection.execute(
                        "SELECT state FROM claims WHERE claim_ref = ?", (claim["claimRef"],)
                    ).fetchone()[0]
                    reservation_state = connection.execute(
                        "SELECT state FROM budget_reservations WHERE reservation_ref = ?",
                        (reservation["reservationRef"],),
                    ).fetchone()[0]
                    connection.execute(
                        f"UPDATE invocations SET {column} = ? WHERE invocation_ref = ?",
                        (original, self.invocation_ref),
                    )
                finally:
                    connection.close()
                self.assertEqual("ACTIVE", claim_state)
                self.assertEqual("ACTIVE", reservation_state)
                self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
                )

    def test_release_rejects_used_over_reserved_and_transition_mismatch(self) -> None:
        corruptions = (
            (
                "used-over-reserved",
                "UPDATE budget_reservations SET spend_used_json = ? WHERE reservation_ref = ?",
                workflow_store.canonical_json(
                    self.budget_vector(effectfulActions=3, toolCostUnits=4)
                ),
            ),
            (
                "transition-mismatch",
                "UPDATE budget_reservations SET transition_kind = 'REMEDIATE' WHERE reservation_ref = ?",
                None,
            ),
        )
        for name, statement, value in corruptions:
            with self.subTest(name=name):
                assessor, reservation, claim = self.acquire_release_candidate()
                connection = self.store._connect()
                try:
                    parameters = (
                        (reservation["reservationRef"],)
                        if value is None
                        else (value, reservation["reservationRef"])
                    )
                    connection.execute(statement, parameters)
                finally:
                    connection.close()
                self.assert_code(
                    "STORE_CORRUPT",
                    lambda: self.store.release_unstarted_claim(
                        claimant_capability=assessor["capability"],
                        claim_ref=claim["claimRef"],
                    ),
                )
                consumed, claim_state, reservation_state = self.release_rows(
                    reservation["reservationRef"], claim["claimRef"]
                )
                self.assertEqual(self.budget_vector(), consumed)
                self.assertEqual("ACTIVE", claim_state)
                self.assertEqual("ACTIVE", reservation_state)
                connection = self.store._connect()
                try:
                    if value is None:
                        connection.execute(
                            "UPDATE budget_reservations SET transition_kind = 'VERIFY' WHERE reservation_ref = ?",
                            (reservation["reservationRef"],),
                        )
                    else:
                        connection.execute(
                            "UPDATE budget_reservations SET spend_used_json = ? WHERE reservation_ref = ?",
                            (workflow_store.canonical_json(self.budget_vector()), reservation["reservationRef"]),
                        )
                finally:
                    connection.close()
                self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
                )

    def test_release_rejects_consumed_over_limits_and_next_consumed_over_limits(self) -> None:
        cases = (
            (
                "consumed-over-limits",
                self.budget_vector(effectfulActions=11),
                self.budget_vector(),
            ),
            (
                "next-consumed-over-limits",
                self.budget_vector(effectfulActions=10),
                self.budget_vector(effectfulActions=1),
            ),
        )
        for name, corrupt_consumed, spend_used in cases:
            with self.subTest(name=name):
                assessor, reservation, claim = self.acquire_release_candidate()
                if any(spend_used.values()):
                    self.store.consume_budget(
                        actor_capability=assessor["capability"],
                        reservation_ref=reservation["reservationRef"],
                        category="SPEND",
                        amounts=spend_used,
                    )
                connection = self.store._connect()
                try:
                    connection.execute(
                        "UPDATE invocations SET consumed_json = ? WHERE invocation_ref = ?",
                        (
                            workflow_store.canonical_json(corrupt_consumed),
                            self.invocation_ref,
                        ),
                    )
                finally:
                    connection.close()
                self.assert_code(
                    "STORE_CORRUPT",
                    lambda: self.store.release_unstarted_claim(
                        claimant_capability=assessor["capability"],
                        claim_ref=claim["claimRef"],
                    ),
                )
                consumed, claim_state, reservation_state = self.release_rows(
                    reservation["reservationRef"], claim["claimRef"]
                )
                self.assertEqual(corrupt_consumed, consumed)
                self.assertEqual("ACTIVE", claim_state)
                self.assertEqual("ACTIVE", reservation_state)
                connection = self.store._connect()
                try:
                    connection.execute(
                        "UPDATE invocations SET consumed_json = ? WHERE invocation_ref = ?",
                        (workflow_store.canonical_json(self.budget_vector()), self.invocation_ref),
                    )
                finally:
                    connection.close()
                self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
                )

    def test_release_rejects_actor_claim_reservation_invocation_relational_corruption(self) -> None:
        second_invocation = self.store.start_invocation(
            root_ref=self.root_ref,
            elapsed_seconds=600,
            limits=self.limits,
        )
        cases = (
            (
                "claimant-invocation",
                "actors",
                "invocation_ref",
                second_invocation["invocationRef"],
            ),
            (
                "claimant-bound-claim",
                "actors",
                "bound_claim_ref",
                None,
            ),
            (
                "claim-coordinator",
                "claims",
                "coordinator_actor_ref",
                second_invocation["coordinator"]["actorRef"],
            ),
            (
                "reservation-invocation",
                "budget_reservations",
                "invocation_ref",
                second_invocation["invocationRef"],
            ),
        )
        for name, table, column, corrupt_value in cases:
            with self.subTest(name=name):
                assessor, reservation, claim = self.acquire_release_candidate()
                target_ref = (
                    assessor["actorRef"]
                    if table == "actors"
                    else claim["claimRef"]
                    if table == "claims"
                    else reservation["reservationRef"]
                )
                ref_column = (
                    "actor_ref"
                    if table == "actors"
                    else "claim_ref"
                    if table == "claims"
                    else "reservation_ref"
                )
                connection = self.store._connect()
                try:
                    original = connection.execute(
                        f"SELECT {column} FROM {table} WHERE {ref_column} = ?", (target_ref,)
                    ).fetchone()[0]
                    connection.execute(
                        f"UPDATE {table} SET {column} = ? WHERE {ref_column} = ?",
                        (corrupt_value, target_ref),
                    )
                finally:
                    connection.close()
                self.assert_code(
                    "STORE_CORRUPT",
                    lambda: self.store.release_unstarted_claim(
                        claimant_capability=assessor["capability"],
                        claim_ref=claim["claimRef"],
                    ),
                )
                consumed, claim_state, reservation_state = self.release_rows(
                    reservation["reservationRef"], claim["claimRef"]
                )
                self.assertEqual(self.budget_vector(), consumed)
                self.assertEqual("ACTIVE", claim_state)
                self.assertEqual("ACTIVE", reservation_state)
                connection = self.store._connect()
                try:
                    connection.execute(
                        f"UPDATE {table} SET {column} = ? WHERE {ref_column} = ?",
                        (original, target_ref),
                    )
                finally:
                    connection.close()
                self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
                )

    def test_release_conditional_update_failure_rolls_back_every_accounting_change(self) -> None:
        assessor, reservation, claim = self.acquire_release_candidate()
        spend = self.budget_vector(effectfulActions=1, toolCostUnits=2)
        closure = self.budget_vector(toolCostUnits=1, closureOperations=1)
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=reservation["reservationRef"],
            category="SPEND",
            amounts=spend,
        )
        self.store.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=reservation["reservationRef"],
            category="CLOSURE",
            amounts=closure,
        )
        connection = self.store._connect()
        try:
            connection.execute(
                f"""
                CREATE TRIGGER ignore_release_reservation_close
                BEFORE UPDATE OF state ON budget_reservations
                WHEN OLD.reservation_ref = '{reservation['reservationRef']}' AND NEW.state = 'CLOSED'
                BEGIN SELECT RAISE(IGNORE); END
                """
            )
        finally:
            connection.close()
        try:
            self.assert_code(
                "ATOMIC_RELEASE_CONFLICT",
                lambda: self.store.release_unstarted_claim(
                    claimant_capability=assessor["capability"],
                    claim_ref=claim["claimRef"],
                ),
            )
            consumed, claim_state, reservation_state = self.release_rows(
                reservation["reservationRef"], claim["claimRef"]
            )
            self.assertEqual(self.budget_vector(), consumed)
            self.assertEqual("ACTIVE", claim_state)
            self.assertEqual("ACTIVE", reservation_state)
        finally:
            connection = self.store._connect()
            try:
                connection.execute("DROP TRIGGER IF EXISTS ignore_release_reservation_close")
            finally:
                connection.close()

        released = self.store.release_unstarted_claim(
            claimant_capability=assessor["capability"], claim_ref=claim["claimRef"]
        )
        expected = {
            field: spend[field] + closure[field] for field in workflow_store.BUDGET_FIELDS
        }
        consumed, claim_state, reservation_state = self.release_rows(
            reservation["reservationRef"], claim["claimRef"]
        )
        self.assertEqual("RELEASED", released["state"])
        self.assertEqual(expected, consumed)
        self.assertEqual("RELEASED", claim_state)
        self.assertEqual("CLOSED", reservation_state)

    def assert_code_for_store(self, store, code: str, operation) -> None:
        with self.assertRaises(workflow_store.WorkflowStoreError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
