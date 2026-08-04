from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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
        self.guard = implementation_result.workflow_store._mint_test_guard_session(
            store_root=self.workflow_root,
            identity=f"test-quiescence:{self.workflow_root}",
            is_active=lambda: True,
        )
        self.publisher = implementation_result.HandoffPublisher(
            self.workflow_root, self.capsule_root, guard=self.guard
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
        self.assertEqual(self.planning_seal(), handoff["planningSeal"])
        self.assertEqual(
            implementation_result.planning_seal_digest(self.planning_seal()),
            handoff["planningSealDigest"],
        )
        self.assertEqual(transaction["finalSourceIdentity"], handoff["finalSourceIdentity"])
        self.assertEqual(
            [{**self.criteria()[0], "taskIds": ["task-1"]}],
            handoff["criterionAccounting"],
        )
        self.assertEqual([], handoff["unresolvedImplementationItems"])
        self.assertNotIn("sourceEvidence", handoff)
        self.assertNotIn("runtimeObservations", handoff)
        self.assertNotIn("criterionResults", handoff)
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

    def test_ready_transaction_cannot_bypass_publisher_with_caller_authored_handoff(self) -> None:
        transaction = self.prepare_initial(mutate=False)
        forged_ref = implementation_result.workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        forged_payload = {
            "protocolVersion": "implementation-handoff-v1",
            "implementationHandoffRef": forged_ref,
            "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
            "projectRoot": str(self.project.resolve()),
            "planningSeal": self.planning_seal(),
            "planningSealDigest": implementation_result.planning_seal_digest(
                self.planning_seal()
            ),
            "baselineCapsuleRef": transaction["baselineCapsuleRef"],
            "baselineSourceIdentity": transaction["baselineSourceIdentity"],
            "finalSourceIdentity": transaction["finalSourceIdentity"],
            "implementationDeltaRef": transaction["implementationDeltaRef"],
            "criterionAccounting": [{**self.criteria()[0], "taskIds": ["forged-task"]}],
            "unresolvedImplementationItems": [],
            "completedAt": "2026-08-03T00:00:00+00:00",
        }
        with self.assertRaises(Exception) as raised:
            self.publisher.workflow.publish_initial_handoff(
                node_ref=forged_ref,
                protocol_version="implementation-handoff-v1",
                planning_identity=forged_payload["planningSealDigest"],
                source_identity=transaction["finalSourceIdentity"],
                payload=forged_payload,
                implementation_transaction_ref=transaction["transactionRef"],
            )
        self.assertEqual("PUBLICATION_SURFACE_RETIRED", raised.exception.code)
        self.assertEqual(
            "READY_FOR_HANDOFF",
            self.publisher.transactions.read_transaction(transaction["transactionRef"])["state"],
        )

    def test_initial_handoff_event_failure_rolls_back_node_and_transaction_then_retries(self) -> None:
        transaction = self.prepare_initial(mutate=False)
        request = self.request(transaction)
        connection = self.publisher.workflow._connect()
        try:
            connection.execute(
                """
                CREATE TRIGGER fail_initial_handoff_event
                BEFORE INSERT ON implementation_events
                WHEN NEW.event_kind = 'HANDOFF_PUBLISHED'
                BEGIN SELECT RAISE(ABORT, 'simulated initial handoff event failure'); END
                """
            )
            self.assert_code(
                "ATOMIC_PUBLICATION_CONFLICT", lambda: self.publisher.publish(request)
            )
            self.assertEqual(0, connection.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
            self.assertEqual(
                0,
                connection.execute(
                    "SELECT COUNT(*) FROM implementation_events WHERE event_kind = 'HANDOFF_PUBLISHED'"
                ).fetchone()[0],
            )
        finally:
            connection.execute("DROP TRIGGER fail_initial_handoff_event")
            connection.close()
        self.assertEqual(
            "READY_FOR_HANDOFF",
            self.publisher.transactions.read_transaction(transaction["transactionRef"])["state"],
        )
        result = self.publisher.publish(request)
        self.assertEqual(result, self.publisher.workflow.read_node(result["implementationHandoffRef"])["payload"])

    def test_publisher_derives_deterministic_task_id_order(self) -> None:
        planning_identity = implementation_result.planning_seal_digest(self.planning_seal())
        transaction = self.publisher.transactions.start_initial(
            project_root=self.project,
            planning_identity=planning_identity,
            selected_worker="worker",
        )
        for task_id, content in (("task-z", "z\n"), ("task-a", "a\n")):
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
            (self.project / "app.txt").write_text(content, encoding="utf-8")
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
        request = self.request({**transaction, **prepared, "taskIds": ["task-z", "task-a"]})
        self.assert_code(
            "INCOMPLETE_CRITERION_ACCOUNTING", lambda: self.publisher.publish(request)
        )
        request["criterionAccounting"][0]["taskIds"] = ["task-a", "task-z"]
        result = self.publisher.publish(request)
        self.assertEqual(
            ["task-a", "task-z"], result["criterionAccounting"][0]["taskIds"]
        )

    def test_invalidated_before_dispatch_envelope_does_not_create_criterion_linkage(self) -> None:
        planning_identity = implementation_result.planning_seal_digest(self.planning_seal())
        transaction = self.publisher.transactions.start_initial(
            project_root=self.project,
            planning_identity=planning_identity,
            selected_worker="worker",
        )
        envelope = self.publisher.transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="invalidated-task",
            criterion_refs=self.criteria(),
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "app.txt").write_text("external drift\n", encoding="utf-8")
        with self.assertRaises(
            implementation_result.implementation_transaction.TransactionError
        ) as raised:
            self.publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
        self.assertEqual("SOURCE_CHANGED_BEFORE_WORKER_DISPATCH", raised.exception.code)
        prepared = self.publisher.transactions.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )

        handoff = self.publisher.publish(
            self.request({**transaction, **prepared, "taskIds": []})
        )

        self.assertEqual([], handoff["criterionAccounting"][0]["taskIds"])

    def test_criterion_linkage_rejects_event_digest_and_selected_worker_tamper(self) -> None:
        for tamper_kind in ("digest", "selected-worker", "other-envelope"):
            with self.subTest(tamper_kind=tamper_kind):
                (self.project / "app.txt").write_text(
                    f"before {tamper_kind}\n", encoding="utf-8"
                )
                transaction = self.prepare_initial(mutate=True)
                connection = self.publisher.workflow._connect()
                try:
                    connection.execute("DROP TRIGGER IF EXISTS implementation_events_no_update")
                    row = connection.execute(
                        """
                        SELECT event_id, payload_json
                        FROM implementation_events
                        WHERE transaction_ref = ? AND event_kind = 'WORKER_CALL_STARTED'
                        """,
                        (transaction["transactionRef"],),
                    ).fetchone()
                    if tamper_kind == "digest":
                        connection.execute(
                            "UPDATE implementation_events SET payload_sha256 = ? WHERE event_id = ?",
                            ("0" * 64, row["event_id"]),
                        )
                    else:
                        payload = json.loads(bytes(row["payload_json"]))
                        if tamper_kind == "selected-worker":
                            payload["selectedWorker"] = "another-worker"
                        else:
                            payload["envelopeRef"] = (
                                "implementation:envelope:v1:" + "0" * 32
                            )
                        encoded = implementation_result._canonical_json(payload)
                        connection.execute(
                            """
                            UPDATE implementation_events
                            SET payload_json = ?, payload_sha256 = ? WHERE event_id = ?
                            """,
                            (encoded, hashlib.sha256(encoded).hexdigest(), row["event_id"]),
                        )
                finally:
                    connection.close()

                self.assert_code(
                    "TRANSACTION_CORRUPT",
                    lambda: self.publisher.publish(self.request(transaction)),
                )
                self.assertEqual(
                    "READY_FOR_HANDOFF",
                    self.publisher.transactions.read_transaction(transaction["transactionRef"])[
                        "state"
                    ],
                )

    def test_criterion_linkage_cross_checks_frozen_row_task_and_criteria(self) -> None:
        for tamper_kind in ("task", "criteria"):
            with self.subTest(tamper_kind=tamper_kind):
                (self.project / "app.txt").write_text(
                    f"before {tamper_kind}\n", encoding="utf-8"
                )
                transaction = self.prepare_initial(mutate=True)
                connection = self.publisher.workflow._connect()
                try:
                    if tamper_kind == "task":
                        connection.execute(
                            """
                            UPDATE implementation_envelopes SET task_id = 'row-tampered'
                            WHERE transaction_ref = ?
                            """,
                            (transaction["transactionRef"],),
                        )
                    else:
                        changed = [{"criterionIndex": 1, "criterionRawSha256": "0" * 64}]
                        connection.execute(
                            """
                            UPDATE implementation_envelopes SET criterion_refs_json = ?
                            WHERE transaction_ref = ?
                            """,
                            (
                                implementation_result._canonical_json(changed),
                                transaction["transactionRef"],
                            ),
                        )
                finally:
                    connection.close()

                self.assert_code(
                    "TRANSACTION_CORRUPT",
                    lambda: self.publisher.publish(self.request(transaction)),
                )

    def test_invalidation_event_partition_tamper_is_rejected(self) -> None:
        planning_identity = implementation_result.planning_seal_digest(self.planning_seal())
        transaction = self.publisher.transactions.start_initial(
            project_root=self.project,
            planning_identity=planning_identity,
            selected_worker="worker",
        )
        envelope = self.publisher.transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="invalidation-tamper",
            criterion_refs=self.criteria(),
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "app.txt").write_text("external drift\n", encoding="utf-8")
        with self.assertRaises(
            implementation_result.implementation_transaction.TransactionError
        ):
            self.publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
        prepared = self.publisher.transactions.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )
        transaction = {**transaction, **prepared, "taskIds": []}
        connection = self.publisher.workflow._connect()
        try:
            connection.execute("DROP TRIGGER IF EXISTS implementation_events_no_update")
            row = connection.execute(
                """
                SELECT event_id, payload_json FROM implementation_events
                WHERE transaction_ref = ?
                  AND event_kind = 'ENVELOPE_INVALIDATED_BEFORE_DISPATCH'
                """,
                (transaction["transactionRef"],),
            ).fetchone()
            payload = json.loads(bytes(row["payload_json"]))
            payload["externalPaths"] = []
            encoded = implementation_result._canonical_json(payload)
            connection.execute(
                """
                UPDATE implementation_events SET payload_json = ?, payload_sha256 = ?
                WHERE event_id = ?
                """,
                (encoded, hashlib.sha256(encoded).hexdigest(), row["event_id"]),
            )
        finally:
            connection.close()

        self.assert_code(
            "TRANSACTION_CORRUPT", lambda: self.publisher.publish(self.request(transaction))
        )

    def test_one_envelope_cannot_be_both_invalidated_and_worker_started(self) -> None:
        planning_identity = implementation_result.planning_seal_digest(self.planning_seal())
        transaction = self.publisher.transactions.start_initial(
            project_root=self.project,
            planning_identity=planning_identity,
            selected_worker="worker",
        )
        envelope = self.publisher.transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="both-facts",
            criterion_refs=self.criteria(),
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "app.txt").write_text("external drift\n", encoding="utf-8")
        with self.assertRaises(
            implementation_result.implementation_transaction.TransactionError
        ):
            self.publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=envelope["envelopeRef"],
            )
        prepared = self.publisher.transactions.prepare_handoff(
            transaction_capability=transaction["transactionCapability"]
        )
        transaction = {**transaction, **prepared, "taskIds": []}
        started = implementation_result._canonical_json(
            {"envelopeRef": envelope["envelopeRef"], "selectedWorker": "worker"}
        )
        connection = self.publisher.workflow._connect()
        try:
            connection.execute(
                """
                INSERT INTO implementation_events(
                    transaction_ref, event_kind, payload_json, payload_sha256, created_at
                ) VALUES (?, 'WORKER_CALL_STARTED', ?, ?, ?)
                """,
                (
                    transaction["transactionRef"],
                    started,
                    hashlib.sha256(started).hexdigest(),
                    implementation_result.workflow_store.utc_now(),
                ),
            )
        finally:
            connection.close()

        self.assert_code(
            "TRANSACTION_CORRUPT", lambda: self.publisher.publish(self.request(transaction))
        )

    @unittest.skipIf(
        implementation_result.workflow_store.SCHEMA_VERSION < 8,
        "same-task replacement requires the workflow-store envelope v8 migration",
    )
    def test_same_task_replacement_links_only_exact_dispatched_envelope_criteria(self) -> None:
        self.write_ticket("- First criterion.\n- Second criterion.\n")
        criteria = self.criteria()
        planning_identity = implementation_result.planning_seal_digest(self.planning_seal())
        transaction = self.publisher.transactions.start_initial(
            project_root=self.project,
            planning_identity=planning_identity,
            selected_worker="worker",
        )
        first = self.publisher.transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="task-T",
            criterion_refs=[criteria[0]],
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        (self.project / "external.txt").write_text("external drift\n", encoding="utf-8")
        with self.assertRaises(
            implementation_result.implementation_transaction.TransactionError
        ) as raised:
            self.publisher.transactions.begin_worker_call(
                worker_capability=transaction["workerCapability"],
                envelope_ref=first["envelopeRef"],
            )
        self.assertEqual("SOURCE_CHANGED_BEFORE_WORKER_DISPATCH", raised.exception.code)
        second = self.publisher.transactions.freeze_envelope(
            transaction_capability=transaction["transactionCapability"],
            task_id="task-T",
            criterion_refs=[criteria[1]],
            allowed_paths=["app.txt"],
            forbidden_paths=[],
        )
        self.publisher.transactions.begin_worker_call(
            worker_capability=transaction["workerCapability"],
            envelope_ref=second["envelopeRef"],
        )
        (self.project / "app.txt").write_text("worker result\n", encoding="utf-8")
        self.publisher.transactions.capture_after(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=second["envelopeRef"],
        )
        self.publisher.transactions.reconcile_envelope(
            transaction_capability=transaction["transactionCapability"],
            envelope_ref=second["envelopeRef"],
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
        request = self.request({**transaction, **prepared, "taskIds": []})
        request["criterionAccounting"] = [
            {**criteria[0], "taskIds": []},
            {**criteria[1], "taskIds": ["task-T"]},
        ]

        handoff = self.publisher.publish(request)

        self.assertEqual([], handoff["criterionAccounting"][0]["taskIds"])
        self.assertEqual(["task-T"], handoff["criterionAccounting"][1]["taskIds"])

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

    def test_historical_cli_is_store_free_and_publish_requires_guard_before_open(self) -> None:
        self.historical_root.mkdir()
        token = "e" * 32
        result_ref = f"implementation:v3:{token}"
        historical = {
            "protocolVersion": "implementation-result-v3",
            "implementationResultRef": result_ref,
        }
        (self.historical_root / f"{token}.json").write_text(
            json.dumps(historical), encoding="utf-8"
        )
        untouched_root = Path(self.temporary.name) / "cli-must-not-open"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status = implementation_result.main(
                [
                    "--workflow-root",
                    str(untouched_root),
                    "--historical-root",
                    str(self.historical_root),
                    "read-historical-v3",
                    "--ref",
                    result_ref,
                ]
            )
        self.assertEqual(0, status)
        self.assertFalse(untouched_root.exists())

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as stderr:
            status = implementation_result.main(
                [
                    "--workflow-root",
                    str(untouched_root),
                    "publish",
                    "--request",
                    str(Path(self.temporary.name) / "absent-request.json"),
                ]
            )
        self.assertEqual(2, status)
        self.assertIn("AUDIT_GUARD_REQUIRED", stderr.getvalue())
        self.assertFalse(untouched_root.exists())

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
        verify_run_ref = implementation_result.workflow_store.allocate_ref("VERIFY")
        verify_claim = graph.acquire_claim(
            coordinator_capability=coordinator["capability"],
            claimant_actor_ref=assessor["actorRef"],
            tip_ref=root_ref,
            transition_kind="VERIFY",
            planning_identity=handoff["planningSealDigest"],
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
        result_ref = implementation_result.workflow_store.allocate_ref("VERIFICATION_RESULT")
        result_payload = {
                "protocolVersion": "verification-result-v1",
                "verificationResultRef": result_ref,
                "verificationStatus": "VERIFICATION_FAILED",
                "implementationHandoffRef": root_ref,
                "planningSealDigest": handoff["planningSealDigest"],
                "finalSourceIdentity": source,
                "verificationRunRef": verify_run_ref,
                "sealedPlanDigest": None,
                "criterionResults": [
                    {
                        **self.criteria()[0],
                        "verdict": "CONTRADICTED",
                        "semanticRationale": "tool-owned contradiction",
                    }
                ],
                "reasonCodes": ["CRITERION_CONTRADICTED"],
                "completedAt": "2026-08-03T00:00:00+00:00",
            }
        with graph._transaction() as connection:
            preflight = implementation_result.workflow_store.canonical_json(
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
                    handoff["planningSealDigest"],
                    source,
                    preflight,
                    "2026-08-03T00:00:00+00:00",
                ),
            )
            failed = graph._close_successor_locked(
                connection,
                claimant_capability=assessor["capability"],
                claim_ref=verify_claim["claimRef"],
                node_ref=result_ref,
                node_kind="VERIFICATION_RESULT",
                protocol_version="verification-result-v1",
                planning_identity=handoff["planningSealDigest"],
                source_identity=source,
                verification_status="VERIFICATION_FAILED",
                payload=result_payload,
                verification_run_ref=verify_run_ref,
                created_at="2026-08-03T00:00:00+00:00",
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
        publication_request = self.request(
            request_transaction,
            actor_capability=workflow["remediator"]["capability"],
        )
        connection = graph._connect()
        try:
            before_consumption = bytes(
                connection.execute(
                    "SELECT closure_used_json FROM budget_reservations WHERE reservation_ref = ?",
                    (workflow["budget"]["reservationRef"],),
                ).fetchone()[0]
            )
            connection.execute(
                """
                CREATE TRIGGER fail_remediation_handoff_event
                BEFORE INSERT ON implementation_events
                WHEN NEW.event_kind = 'HANDOFF_PUBLISHED'
                BEGIN SELECT RAISE(ABORT, 'simulated remediation handoff event failure'); END
                """
            )
            self.assert_code(
                "ATOMIC_PUBLICATION_CONFLICT",
                lambda: self.publisher.publish(publication_request),
            )
            claim_state = connection.execute(
                "SELECT state FROM claims WHERE claim_ref = ?", (workflow["claim"]["claimRef"],)
            ).fetchone()[0]
            reservation = connection.execute(
                "SELECT state, closure_used_json FROM budget_reservations WHERE reservation_ref = ?",
                (workflow["budget"]["reservationRef"],),
            ).fetchone()
            published_events = connection.execute(
                "SELECT COUNT(*) FROM implementation_events WHERE transaction_ref = ? AND event_kind = 'HANDOFF_PUBLISHED'",
                (transaction["transactionRef"],),
            ).fetchone()[0]
        finally:
            connection.execute("DROP TRIGGER fail_remediation_handoff_event")
            connection.close()
        self.assertEqual("ACTIVE", claim_state)
        self.assertEqual("ACTIVE", reservation["state"])
        self.assertEqual(before_consumption, bytes(reservation["closure_used_json"]))
        self.assertEqual(0, published_events)
        self.assertEqual(
            "READY_FOR_HANDOFF",
            self.publisher.transactions.read_transaction(transaction["transactionRef"])["state"],
        )
        self.assertEqual(
            workflow["claim"]["tipRef"],
            graph.current_tip(workflow["handoff"]["implementationHandoffRef"])["nodeRef"],
        )

        handoff = self.publisher.publish(publication_request)

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
