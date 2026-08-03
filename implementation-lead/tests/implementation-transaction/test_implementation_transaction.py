from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
        self.guard = implementation_transaction.workflow_store._mint_test_guard_session(
            store_root=self.workflow_root,
            identity=f"test-quiescence:{self.workflow_root}",
            is_active=lambda: True,
        )
        self.store = implementation_transaction.ImplementationTransactionStore(
            self.workflow_root, self.capsule_root, guard=self.guard
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

    @staticmethod
    def repeat_keys_fixture(
        *,
        final_source: str,
        canonical_digest: str,
        repeat_digest: str | None,
        executor_version: str = "process-v3",
    ) -> set[str] | None:
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.executescript(
            """
            CREATE TABLE verification_runs(
                run_ref TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                sealed_plan_json BLOB,
                sealed_plan_sha256 TEXT
            );
            CREATE TABLE verification_attempts(
                attempt_id INTEGER PRIMARY KEY,
                run_ref TEXT NOT NULL,
                flow_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                status TEXT NOT NULL,
                request_sha256 TEXT NOT NULL,
                result_json BLOB NOT NULL
            );
            """
        )
        step: dict[str, object] = {
            "stepId": "step-1",
            "role": "ACTION",
            "executorKind": "PROCESS",
            "executorVersion": executor_version,
            "environmentPolicy": "SEALED_EMPTY_BASE_V1",
            "canonicalRequestDigest": canonical_digest,
            "executableIdentity": {
                "canonicalPath": "/usr/bin/tool",
                "contentSha256": "1" * 64,
                "byteCount": 1,
                "executableMode": 0o755,
                "ownerUid": 0,
                "ownerGid": 0,
            },
            "sourceBinding": {
                "mode": "EXACT_SOURCE_IDENTITY",
                "finalSourceIdentity": final_source,
                "targetIdentityOrRevision": final_source,
                "bindingBasisAnchors": [],
            },
        }
        if repeat_digest is not None:
            step["repeatRequestDigest"] = repeat_digest
        plan = {
            "criteria": [
                {
                    "criterionIndex": 1,
                    "criterionRawSha256": "b" * 64,
                    "flowIds": ["flow-1"],
                }
            ],
            "flows": [
                {
                    "flowId": "flow-1",
                    "claim": "returns ready",
                    "expectedTerminalObservation": "ready",
                    "steps": [step],
                }
            ],
        }
        sealed = implementation_transaction._canonical_json(plan)
        run_ref = "verification:run:v1:" + "a" * 32
        connection.execute(
            "INSERT INTO verification_runs VALUES (?, 'CLOSED', ?, ?)",
            (run_ref, sealed, hashlib.sha256(sealed).hexdigest()),
        )
        result = implementation_transaction._canonical_json(
            {
                "exitCode": 1,
                "errorCode": None,
                "stdout": {"sha256": "2" * 64},
                "stderr": {"sha256": "3" * 64},
            }
        )
        connection.execute(
            "INSERT INTO verification_attempts VALUES (1, ?, 'flow-1', 'step-1', 'EXITED', ?, ?)",
            (run_ref, canonical_digest, result),
        )
        result_row = {
            "payload_json": implementation_transaction._canonical_json(
                {
                    "verificationRunRef": run_ref,
                    "criterionResults": [
                        {
                            "criterionIndex": 1,
                            "criterionRawSha256": "b" * 64,
                            "verdict": "CONTRADICTED",
                        }
                    ],
                }
            )
        }
        try:
            return implementation_transaction.ImplementationTransactionStore._repeat_keys_for_failed_result(
                connection, result_row
            )
        finally:
            connection.close()

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

    def test_repeat_guard_uses_sealed_v3_repeat_digest_and_excludes_only_final_source(self) -> None:
        first = self.repeat_keys_fixture(
            final_source="sha256:" + "1" * 64,
            canonical_digest="a" * 64,
            repeat_digest="c" * 64,
        )
        source_changed = self.repeat_keys_fixture(
            final_source="sha256:" + "2" * 64,
            canonical_digest="b" * 64,
            repeat_digest="c" * 64,
        )
        executable_identity_changed = self.repeat_keys_fixture(
            final_source="sha256:" + "2" * 64,
            canonical_digest="d" * 64,
            repeat_digest="e" * 64,
        )

        self.assertIsNotNone(first)
        self.assertEqual(first, source_changed)
        self.assertNotEqual(first, executable_identity_changed)

    def test_repeat_guard_does_not_reinterpret_legacy_or_malformed_v3_plans(self) -> None:
        legacy = self.repeat_keys_fixture(
            final_source="sha256:" + "1" * 64,
            canonical_digest="a" * 64,
            repeat_digest="c" * 64,
            executor_version="process-v2",
        )
        self.assertIsNone(legacy)

        with self.assertRaises(implementation_transaction.TransactionError) as raised:
            self.repeat_keys_fixture(
                final_source="sha256:" + "1" * 64,
                canonical_digest="a" * 64,
                repeat_digest=None,
            )
        self.assertEqual("STORE_CORRUPT", raised.exception.code)

    def assert_code(self, code: str, operation) -> None:
        with self.assertRaises(implementation_transaction.TransactionError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)

    def assert_pre_dispatch_invalidation(
        self,
        transaction: dict[str, object],
        envelope: dict[str, object],
        expected_paths: list[str],
    ) -> dict[str, object]:
        self.assert_code(
            "SOURCE_CHANGED_BEFORE_WORKER_DISPATCH",
            lambda: self.store.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            ),
        )
        view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual("OPEN", view["state"])
        self.assertEqual("RECONCILED", view["envelopes"][-1]["state"])
        self.assertEqual(expected_paths, view["envelopes"][-1]["delta"]["changedPaths"])
        self.assertEqual(
            {
                "disposition": "CONTINUE",
                "workerAttributablePaths": [],
                "externalPaths": expected_paths,
                "preservedUserChanges": expected_paths,
                "externalEffectState": "CLEAR",
            },
            view["envelopes"][-1]["reconciliation"],
        )
        self.assertNotIn(
            "WORKER_CALL_STARTED", [event["eventKind"] for event in view["events"]]
        )
        event = view["events"][-1]
        self.assertEqual("ENVELOPE_INVALIDATED_BEFORE_DISPATCH", event["eventKind"])
        self.assertEqual(envelope["envelopeRef"], event["payload"]["envelopeRef"])
        self.assertNotEqual(event["payload"]["oldIdentity"], event["payload"]["newIdentity"])
        self.assertEqual(expected_paths, event["payload"]["changedPaths"])
        self.assertEqual([], event["payload"]["workerAttributablePaths"])
        self.assertEqual(expected_paths, event["payload"]["externalPaths"])
        self.assertEqual(expected_paths, event["payload"]["preservedUserChanges"])
        return view

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

    def test_tracked_drift_before_dispatch_is_durably_reconciled_without_worker(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="tracked-drift",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "app.txt").write_text("external\n", encoding="utf-8")

        self.assert_pre_dispatch_invalidation(transaction, envelope, ["app.txt"])

    def test_untracked_drift_before_dispatch_is_not_ignored(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="untracked-drift",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "untracked.txt").write_text("external\n", encoding="utf-8")

        self.assert_pre_dispatch_invalidation(transaction, envelope, ["untracked.txt"])

    def test_mode_and_symlink_drift_before_dispatch_are_rejected(self) -> None:
        for drift_kind in ("mode", "symlink"):
            with self.subTest(drift_kind=drift_kind):
                if drift_kind == "symlink":
                    (self.project / "other.txt").write_text("other\n", encoding="utf-8")
                    (self.project / "link.txt").symlink_to("app.txt")
                transaction = self.start_initial()
                envelope = self.store.freeze_envelope(
                    transaction_capability=transaction["transactionCapability"],
                    task_id=f"{drift_kind}-drift",
                    criterion_refs=self.criterion_refs,
                    allowed_paths=["**"],
                    forbidden_paths=[],
                )
                if drift_kind == "mode":
                    os.chmod(self.project / "app.txt", 0o744)
                    expected = ["app.txt"]
                else:
                    (self.project / "link.txt").unlink()
                    (self.project / "link.txt").symlink_to("other.txt")
                    expected = ["link.txt"]
                self.assert_pre_dispatch_invalidation(transaction, envelope, expected)
                if drift_kind == "mode":
                    os.chmod(self.project / "app.txt", 0o644)
                else:
                    (self.project / "link.txt").unlink()

    def test_stored_before_snapshot_digest_and_schema_tamper_leave_envelope_frozen(self) -> None:
        for tamper_kind in ("digest", "schema", "policy", "identity"):
            with self.subTest(tamper_kind=tamper_kind):
                transaction = self.start_initial()
                envelope = self.store.freeze_envelope(
                    transaction_capability=transaction["transactionCapability"],
                    task_id=f"tamper-{tamper_kind}",
                    criterion_refs=self.criterion_refs,
                    allowed_paths=["app.txt"],
                    forbidden_paths=[],
                )
                connection = self.store.workflow._connect()
                try:
                    row = connection.execute(
                        """
                        SELECT before_snapshot_json, before_snapshot_sha256
                        FROM implementation_envelopes WHERE envelope_ref = ?
                        """,
                        (envelope["envelopeRef"],),
                    ).fetchone()
                    snapshot = json.loads(bytes(row["before_snapshot_json"]))
                    if tamper_kind == "digest":
                        payload = bytes(row["before_snapshot_json"])
                        digest_value = "0" * 64
                    else:
                        if tamper_kind == "schema":
                            snapshot["schemaVersion"] = "task-ownership-snapshot-v0"
                        elif tamper_kind == "policy":
                            snapshot["policy"]["gitMetadata"] = "included"
                        else:
                            snapshot["identity"] = "sha256:" + "0" * 64
                        payload = json.dumps(
                            snapshot, ensure_ascii=False, separators=(",", ":"), sort_keys=False
                        ).encode("utf-8")
                        digest_value = hashlib.sha256(payload).hexdigest()
                    connection.execute(
                        """
                        UPDATE implementation_envelopes
                        SET before_snapshot_json = ?, before_snapshot_sha256 = ?
                        WHERE envelope_ref = ?
                        """,
                        (payload, digest_value, envelope["envelopeRef"]),
                    )
                finally:
                    connection.close()
                self.assert_code(
                    "STORE_CORRUPT",
                    lambda: self.store.begin_worker_call(
                        worker_capability=transaction["workerCapability"],
                        envelope_ref=envelope["envelopeRef"],
                    ),
                )
                view = self.store.read_transaction(transaction["transactionRef"])
                self.assertEqual("FROZEN", view["envelopes"][0]["state"])
                self.assertNotIn(
                    "WORKER_CALL_STARTED", [event["eventKind"] for event in view["events"]]
                )

    def test_dispatch_capture_failure_leaves_frozen_envelope_unchanged(self) -> None:
        transaction = self.start_initial()
        envelope = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="unstable-capture",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        before_view = self.store.read_transaction(transaction["transactionRef"])
        with mock.patch.object(
            implementation_transaction.ownership_snapshot,
            "capture",
            side_effect=implementation_transaction.ownership_snapshot.SnapshotError(
                "SOURCE_CHANGED_DURING_CAPTURE", "simulated unstable tree"
            ),
        ):
            self.assert_code(
                "SOURCE_CHANGED_DURING_CAPTURE",
                lambda: self.store.begin_worker_call(
                    worker_capability=transaction["workerCapability"],
                    envelope_ref=envelope["envelopeRef"],
                ),
            )
        after_view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual(before_view, after_view)

    def test_second_task_dispatch_uses_its_envelope_not_transaction_baseline(self) -> None:
        transaction = self.start_initial()
        first = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="first-task",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"], envelope_ref=first["envelopeRef"]
        )
        (self.project / "app.txt").write_text("first task\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=first["envelopeRef"],
        )
        self.reconcile_worker_delta(transaction, first, ["app.txt"])
        second = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="second-task",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )

        dispatched = self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"], envelope_ref=second["envelopeRef"]
        )

        self.assertTrue(dispatched["workerCallAuthorized"])

    @unittest.skipIf(
        implementation_transaction.workflow_store.SCHEMA_VERSION < 8,
        "same-task replacement requires the workflow-store envelope v8 migration",
    )
    def test_same_task_replacement_with_disjoint_external_and_worker_paths_succeeds(self) -> None:
        transaction = self.start_initial()
        first = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="stable-task",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "external.txt").write_text("external\n", encoding="utf-8")
        self.assert_pre_dispatch_invalidation(transaction, first, ["external.txt"])
        second = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="stable-task",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"],
            envelope_ref=second["envelopeRef"],
        )
        (self.project / "app.txt").write_text("worker\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=second["envelopeRef"],
        )

        reconciled = self.reconcile_worker_delta(transaction, second, ["app.txt"])

        self.assertEqual("RECONCILED", reconciled["state"])

    @unittest.skipIf(
        implementation_transaction.workflow_store.SCHEMA_VERSION < 8,
        "same-task replacement requires the workflow-store envelope v8 migration",
    )
    def test_same_task_replacement_overlap_stays_captured_and_fails_closed(self) -> None:
        transaction = self.start_initial()
        first = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="stable-task",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "app.txt").write_text("external\n", encoding="utf-8")
        self.assert_pre_dispatch_invalidation(transaction, first, ["app.txt"])
        second = self.store.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="stable-task",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.store.begin_worker_call(
            worker_capability=transaction["workerCapability"],
            envelope_ref=second["envelopeRef"],
        )
        (self.project / "app.txt").write_text("worker\n", encoding="utf-8")
        self.store.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=second["envelopeRef"],
        )

        self.assert_code(
            "RECONCILIATION_INCOMPLETE",
            lambda: self.reconcile_worker_delta(transaction, second, ["app.txt"]),
        )
        view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual("CAPTURED", view["envelopes"][-1]["state"])

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
        handoff_payload = {
                "protocolVersion": "implementation-handoff-v1",
                "implementationHandoffRef": root_ref,
                "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
                "planningSealDigest": self.planning,
                "baselineSourceIdentity": source,
                "finalSourceIdentity": source,
            }
        encoded_handoff = implementation_transaction.workflow_store.canonical_json(handoff_payload)
        with graph._transaction() as connection:
            connection.execute(
                """
                INSERT INTO nodes(
                    node_ref, node_kind, protocol_version, root_ref, planning_identity,
                    source_identity, verification_status, payload_json, payload_sha256, created_at
                ) VALUES (?, 'IMPLEMENTATION_HANDOFF', 'implementation-handoff-v1', ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    root_ref,
                    root_ref,
                    self.planning,
                    source,
                    encoded_handoff,
                    hashlib.sha256(encoded_handoff).hexdigest(),
                    implementation_transaction.workflow_store.utc_now(),
                ),
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
        verify_run_ref = implementation_transaction.workflow_store.allocate_ref("VERIFY")
        verify_claim = graph.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=assessor["actorRef"],
            tip_ref=root_ref,
            transition_kind="VERIFY",
            planning_identity=self.planning,
            source_identity=source,
            execution_ref=verify_run_ref,
            budget_reservation_ref=verify_budget["reservationRef"],
        )
        graph.consume_budget(
            actor_capability=assessor["capability"],
            reservation_ref=verify_budget["reservationRef"],
            category="CLOSURE",
            amounts=self.budget_vector(closureOperations=1),
        )
        result_ref = implementation_transaction.workflow_store.allocate_ref("VERIFICATION_RESULT")
        result_payload = {
                "protocolVersion": "verification-result-v1",
                "verificationResultRef": result_ref,
                "verificationStatus": "VERIFICATION_FAILED",
                "implementationHandoffRef": root_ref,
                "planningSealDigest": self.planning,
                "finalSourceIdentity": source,
                "verificationRunRef": verify_run_ref,
                "sealedPlanDigest": None,
                "criterionResults": [
                    {
                        **self.criterion_refs[0],
                        "verdict": "CONTRADICTED",
                        "semanticRationale": "tool-owned contradiction",
                    }
                ],
                "reasonCodes": ["CRITERION_CONTRADICTED"],
                "completedAt": implementation_transaction.workflow_store.utc_now(),
            }
        with graph._transaction() as connection:
            preflight = implementation_transaction.workflow_store.canonical_json(
                {"stage": "TERMINAL", "draftDigest": "0" * 64, "observations": []}
            )
            connection.execute(
                """
                INSERT INTO verification_runs(
                    run_ref, root_ref, claim_ref, assessor_actor_ref,
                    implementation_handoff_ref, project_root, planning_identity,
                    source_identity, preflight_json, sealed_plan_json,
                    sealed_plan_sha256, state, closure_json, created_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'PREFLIGHT', NULL, ?, NULL)
                """,
                (
                    verify_run_ref,
                    root_ref,
                    verify_claim["claimRef"],
                    assessor["actorRef"],
                    root_ref,
                    str(self.project.resolve()),
                    self.planning,
                    source,
                    preflight,
                    implementation_transaction.workflow_store.utc_now(),
                ),
            )
            failed = graph._close_successor_locked(
                connection,
                claimant_capability=assessor["capability"],
                claim_ref=verify_claim["claimRef"],
                node_ref=result_ref,
                node_kind="VERIFICATION_RESULT",
                protocol_version="verification-result-v1",
                planning_identity=self.planning,
                source_identity=source,
                verification_status="VERIFICATION_FAILED",
                payload=result_payload,
                verification_run_ref=verify_run_ref,
                created_at=implementation_transaction.workflow_store.utc_now(),
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

    def test_remediation_drift_reconciliation_ignores_expired_and_exhausted_spend_gate(self) -> None:
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
            task_id="expired-drift",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        connection = self.store.workflow._connect()
        try:
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                (workflow["budget"]["reservationRef"],),
            ).fetchone()
            used = self.store.workflow._stored_budget(
                reservation["spend_used_json"], "reservation.spendUsed"
            )
            used["workerCalls"] = 1
            connection.execute(
                "UPDATE budget_reservations SET spend_used_json = ? WHERE reservation_ref = ?",
                (
                    implementation_transaction._canonical_json(used),
                    workflow["budget"]["reservationRef"],
                ),
            )
            connection.execute(
                "UPDATE invocations SET deadline_at = ? WHERE invocation_ref = ?",
                ("2000-01-01T00:00:00+00:00", reservation["invocation_ref"]),
            )
        finally:
            connection.close()
        (self.project / "app.txt").write_text("external after expiry\n", encoding="utf-8")

        self.assert_code(
            "SOURCE_CHANGED_BEFORE_WORKER_DISPATCH",
            lambda: self.store.begin_worker_call(
                worker_capability=workflow["worker"]["capability"],
                envelope_ref=envelope["envelopeRef"],
            ),
        )

        view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual("RECONCILED", view["envelopes"][0]["state"])
        self.assertNotIn(
            "WORKER_CALL_STARTED", [event["eventKind"] for event in view["events"]]
        )
        connection = self.store.workflow._connect()
        try:
            reservation = connection.execute(
                "SELECT spend_used_json FROM budget_reservations WHERE reservation_ref = ?",
                (workflow["budget"]["reservationRef"],),
            ).fetchone()
            used_after = self.store.workflow._stored_budget(
                reservation["spend_used_json"], "reservation.spendUsed"
            )
        finally:
            connection.close()
        self.assertEqual(1, used_after["workerCalls"])

    def test_remediation_dispatch_capture_failure_does_not_consume_worker_budget(self) -> None:
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
            task_id="unstable-remediation",
            criterion_refs=self.criterion_refs,
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        with mock.patch.object(
            implementation_transaction.ownership_snapshot,
            "capture",
            side_effect=implementation_transaction.ownership_snapshot.SnapshotError(
                "SOURCE_CHANGED_DURING_CAPTURE", "simulated unstable remediation tree"
            ),
        ):
            self.assert_code(
                "SOURCE_CHANGED_DURING_CAPTURE",
                lambda: self.store.begin_worker_call(
                    worker_capability=workflow["worker"]["capability"],
                    envelope_ref=envelope["envelopeRef"],
                ),
            )

        view = self.store.read_transaction(transaction["transactionRef"])
        self.assertEqual("FROZEN", view["envelopes"][0]["state"])
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
        self.assertEqual(0, used["workerCalls"])


if __name__ == "__main__":
    unittest.main()
