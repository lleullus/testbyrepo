from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/workflow-store/workflow_store_preopen.py"
SPEC = importlib.util.spec_from_file_location("workflow_store_preopen", MODULE)
assert SPEC and SPEC.loader
workflow_store_preopen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow_store_preopen
SPEC.loader.exec_module(workflow_store_preopen)

WORKFLOW_MODULE = ROOT / "tools/workflow-store/workflow_store.py"
V7_SCHEMA_FIXTURE = ROOT / "tests/workflow-store/fixtures/workflow-schema-v7.sql"
WORKFLOW_SPEC = importlib.util.spec_from_file_location(
    "workflow_store_for_preopen_schema", WORKFLOW_MODULE
)
assert WORKFLOW_SPEC and WORKFLOW_SPEC.loader
workflow_store = importlib.util.module_from_spec(WORKFLOW_SPEC)
sys.modules[WORKFLOW_SPEC.name] = workflow_store
WORKFLOW_SPEC.loader.exec_module(workflow_store)


class WorkflowStorePreOpenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.private_parent = self.base / "private"
        self.private_parent.mkdir(mode=0o700)
        self.fixture_fingerprints: dict[Path, str] = {}
        self.guard_state = {"active": True}
        self.last_guard = None

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def budget(**updates: int) -> str:
        value = {field: 0 for field in workflow_store_preopen.BUDGET_FIELDS}
        value.update(updates)
        return json.dumps(value, separators=(",", ":"))

    def create_store(self, name: str = "store", *, version: int = 7) -> tuple[Path, sqlite3.Connection]:
        root = self.base / name
        root.mkdir(mode=0o700)
        database = root / workflow_store_preopen.DATABASE_FILENAME
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE store_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE implementation_transactions(
                transaction_ref TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                state TEXT NOT NULL,
                closed_at TEXT
            );
            CREATE TABLE implementation_envelopes(
                envelope_ref TEXT PRIMARY KEY,
                transaction_ref TEXT NOT NULL,
                task_id TEXT NOT NULL,
                state TEXT NOT NULL,
                closed_at TEXT
            );
            CREATE TABLE verification_runs(
                run_ref TEXT PRIMARY KEY,
                claim_ref TEXT NOT NULL,
                state TEXT NOT NULL,
                closed_at TEXT,
                sealed_plan_json BLOB,
                sealed_plan_sha256 TEXT
            );
            CREATE TABLE invocations(
                invocation_ref TEXT PRIMARY KEY,
                limits_json BLOB NOT NULL,
                consumed_json BLOB NOT NULL,
                state TEXT NOT NULL
            );
            CREATE TABLE actors(
                actor_ref TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                root_ref TEXT NOT NULL,
                invocation_ref TEXT NOT NULL,
                bound_claim_ref TEXT
            );
            CREATE TABLE budget_reservations(
                reservation_ref TEXT PRIMARY KEY,
                invocation_ref TEXT NOT NULL,
                transition_kind TEXT NOT NULL,
                spend_reserved_json BLOB NOT NULL,
                closure_reserved_json BLOB NOT NULL,
                spend_used_json BLOB NOT NULL,
                closure_used_json BLOB NOT NULL,
                state TEXT NOT NULL,
                closed_at TEXT
            );
            CREATE TABLE claims(
                claim_ref TEXT PRIMARY KEY,
                root_ref TEXT NOT NULL,
                transition_kind TEXT NOT NULL,
                execution_ref TEXT NOT NULL,
                closure_ref TEXT,
                closed_at TEXT,
                claimant_actor_ref TEXT NOT NULL,
                budget_reservation_ref TEXT NOT NULL,
                state TEXT NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO store_meta(key, value) VALUES ('schema_version', ?)",
            (str(version),),
        )
        connection.commit()
        os.chmod(database, 0o600)
        objects = workflow_store_preopen._schema_inventory(connection)
        self.fixture_fingerprints[root.resolve()] = workflow_store_preopen._schema_fingerprint(
            objects
        )
        return root, connection

    def audit(self, root: Path, **kwargs):
        fingerprint = self.fixture_fingerprints.get(root.resolve(strict=False))
        if fingerprint is not None and "_expected_schema_fingerprints" not in kwargs:
            kwargs["_expected_schema_fingerprints"] = {7: {fingerprint}}
        guard = kwargs.pop("guard", None) or self.guard_for(root)
        self.last_guard = guard
        return workflow_store_preopen.audit_workflow_store(
            root,
            guard=guard,
            private_parent=self.private_parent,
            **kwargs,
        )

    def guard_for(self, root: Path, *, identity: str = "deployment:test:1"):
        return workflow_store_preopen._mint_guard_session(
            identity=identity,
            kind="EXCLUSIVE_LOCK",
            is_active=lambda: self.guard_state["active"],
            raw_root=root,
        )

    def assert_error(self, code: str, operation) -> RuntimeError:
        with self.assertRaises(workflow_store_preopen.PreOpenAuditError) as raised:
            operation()
        self.assertEqual(code, raised.exception.code)
        return raised.exception

    def test_no_store_does_not_create_root_and_lease_is_single_use(self) -> None:
        root = self.base / "absent"

        outcome = self.audit(root)

        self.assertEqual("NO_STORE", outcome.report.disposition)
        self.assertFalse(root.exists())
        self.assertIsNotNone(outcome.lease)
        assert outcome.lease is not None
        assert self.last_guard is not None
        observed = outcome.lease.consume(
            guard=self.last_guard,
            opener=lambda canonical_root, report: (
                canonical_root,
                report.source_manifest.digest,
            ),
        )
        self.assertEqual(root.resolve(strict=False), observed[0])
        self.assertFalse(root.exists())
        self.assert_error(
            "AUDIT_LEASE_ALREADY_CONSUMED",
            lambda: outcome.lease.consume(
                guard=self.last_guard,
                opener=lambda _root, _report: None,
            ),
        )

    def test_guard_requires_private_mint_and_is_bound_to_one_exact_root(self) -> None:
        root = self.base / "guard-root"
        with self.assertRaises(TypeError):
            workflow_store_preopen.GuardSession(
                identity="forged-public-guard",
                kind="QUIESCENCE",
                is_active=lambda: True,
                canonical_root=str(root),
            )

        guard = self.guard_for(root)
        other_root = self.base / "other-guard-root"
        self.assert_error(
            "AUDIT_GUARD_ROOT_MISMATCH",
            lambda: workflow_store_preopen.audit_workflow_store(
                other_root,
                guard=guard,
                private_parent=self.private_parent,
            ),
        )
        self.assertFalse(other_root.exists())

    def test_orphan_sidecars_and_rollback_journal_block_without_sqlite_open(self) -> None:
        for suffix, blocker in (
            ("-wal", "ORPHAN_SIDECAR:WAL"),
            ("-shm", "ORPHAN_SIDECAR:SHM"),
            ("-journal", "ORPHAN_SIDECAR:JOURNAL"),
        ):
            with self.subTest(suffix=suffix):
                root = self.base / f"orphan-{suffix[1:]}"
                root.mkdir()
                (root / f"workflow.sqlite3{suffix}").write_bytes(b"orphan")
                with patch.object(workflow_store_preopen.sqlite3, "connect") as connect:
                    outcome = self.audit(root)
                self.assertEqual("BLOCKED", outcome.report.disposition)
                self.assertIn(blocker, outcome.report.blockers)
                self.assertIsNone(outcome.lease)
                connect.assert_not_called()

        root, connection = self.create_store("journal")
        connection.close()
        (root / "workflow.sqlite3-journal").write_bytes(b"journal")
        with patch.object(workflow_store_preopen.sqlite3, "connect") as connect:
            outcome = self.audit(root)
        self.assertEqual(("ROLLBACK_JOURNAL_PRESENT",), outcome.report.blockers)
        connect.assert_not_called()

    def test_symlink_and_non_regular_source_objects_fail_closed(self) -> None:
        symlink_root = self.base / "symlink-root"
        real_root = self.base / "real-root"
        real_root.mkdir()
        symlink_root.symlink_to(real_root, target_is_directory=True)
        self.assert_error("SOURCE_ROOT_SYMLINK", lambda: self.audit(symlink_root))

        file_root = self.base / "file-root"
        file_root.write_bytes(b"not-a-directory")
        self.assert_error("SOURCE_ROOT_NON_DIRECTORY", lambda: self.audit(file_root))

        database_root = self.base / "symlink-database"
        database_root.mkdir()
        target = self.base / "database-target"
        target.write_bytes(b"not-opened")
        (database_root / "workflow.sqlite3").symlink_to(target)
        self.assert_error("SOURCE_FILE_SYMLINK", lambda: self.audit(database_root))

        fifo_root = self.base / "fifo-database"
        fifo_root.mkdir()
        os.mkfifo(fifo_root / "workflow.sqlite3")
        self.assert_error("SOURCE_FILE_NON_REGULAR", lambda: self.audit(fifo_root))

    def test_private_db_wal_copy_reads_latest_commit_and_preserves_source_manifest(self) -> None:
        root, setup = self.create_store("wal")
        setup.close()
        database = root / "workflow.sqlite3"
        writer = sqlite3.connect(database)
        try:
            self.assertEqual("wal", writer.execute("PRAGMA journal_mode = WAL").fetchone()[0])
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            writer.execute(
                "INSERT INTO implementation_transactions VALUES (?, ?, ?, NULL)",
                ("implementation:transaction:v1:wal", "INITIAL_IMPLEMENTATION", "OPEN"),
            )
            writer.execute(
                "INSERT INTO implementation_envelopes VALUES (?, ?, ?, ?, NULL)",
                (
                    "implementation:envelope:v1:wal",
                    "implementation:transaction:v1:wal",
                    "task-wal",
                    "FROZEN",
                ),
            )
            writer.commit()
            self.assertTrue(Path(f"{database}-wal").exists())
            before = workflow_store_preopen.capture_source_manifest(root)
            real_connect = sqlite3.connect
            opened: list[Path] = []

            def guarded_connect(path, *args, **kwargs):
                opened_path = Path(path).resolve(strict=False)
                opened.append(opened_path)
                self.assertNotEqual(database.resolve(), opened_path)
                return real_connect(path, *args, **kwargs)

            with patch.object(
                workflow_store_preopen.sqlite3,
                "connect",
                side_effect=guarded_connect,
            ):
                outcome = self.audit(root)
            after = workflow_store_preopen.capture_source_manifest(root)
        finally:
            writer.close()

        self.assertEqual(before, after)
        self.assertEqual("CLEAR", outcome.report.disposition)
        self.assertEqual(7, outcome.report.schema_version)
        self.assertEqual(
            ("implementation:transaction:v1:wal",),
            tuple(item.transaction_ref for item in outcome.report.open_transactions),
        )
        self.assertEqual(
            ("implementation:envelope:v1:wal",),
            tuple(item.envelope_ref for item in outcome.report.open_envelopes),
        )
        self.assertEqual(1, len(opened))
        self.assertEqual((str(opened[0]),), outcome.report.sqlite_database_paths)
        self.assertFalse(opened[0].parent.exists())
        self.assertEqual(0o700, stat.S_IMODE(self.private_parent.stat().st_mode))

    def test_immutable_sqlite_misses_an_uncheckpointed_wal_commit(self) -> None:
        root, setup = self.create_store("immutable-negative")
        setup.close()
        database = root / "workflow.sqlite3"
        writer = sqlite3.connect(database)
        try:
            writer.execute("PRAGMA journal_mode = WAL")
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            writer.execute(
                "INSERT INTO implementation_transactions VALUES (?, ?, ?, NULL)",
                ("implementation:transaction:v1:latest", "INITIAL_IMPLEMENTATION", "OPEN"),
            )
            writer.commit()
            immutable = sqlite3.connect(f"file:{database}?immutable=1", uri=True)
            try:
                count = immutable.execute(
                    "SELECT count(*) FROM implementation_transactions"
                ).fetchone()[0]
            finally:
                immutable.close()
        finally:
            writer.close()
        self.assertEqual(0, count)

    def test_direct_read_only_sqlite_can_create_source_shm(self) -> None:
        root, setup = self.create_store("readonly-negative")
        setup.close()
        database = root / "workflow.sqlite3"
        crash_writer = """
import os
import sqlite3
import sys

connection = sqlite3.connect(sys.argv[1])
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA wal_autocheckpoint = 0")
connection.execute(
    "INSERT INTO implementation_transactions VALUES (?, ?, ?, NULL)",
    ("implementation:transaction:v1:ro", "INITIAL_IMPLEMENTATION", "OPEN"),
)
connection.commit()
os._exit(0)
"""
        subprocess.run(
            [sys.executable, "-c", crash_writer, str(database)],
            check=True,
        )
        shm = Path(f"{database}-shm")
        self.assertTrue(Path(f"{database}-wal").exists())
        self.assertTrue(shm.exists())
        shm.unlink()
        self.assertFalse(shm.exists())

        reader = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        try:
            self.assertEqual(
                1,
                reader.execute(
                    "SELECT count(*) FROM implementation_transactions"
                ).fetchone()[0],
            )
            self.assertTrue(shm.exists())
        finally:
            reader.close()

    def test_change_between_manifest_passes_is_rejected_before_sqlite(self) -> None:
        root, connection = self.create_store("pass-race")
        connection.close()
        database = root / "workflow.sqlite3"

        def append_after_first(_manifest) -> None:
            with database.open("ab") as stream:
                stream.write(b"race")

        hooks = workflow_store_preopen._AuditHooks(
            after_first_manifest_pass=append_after_first
        )
        with patch.object(workflow_store_preopen.sqlite3, "connect") as connect:
            self.assert_error(
                "UNSTABLE_SOURCE_MANIFEST",
                lambda: self.audit(root, _hooks=hooks),
            )
        connect.assert_not_called()

    def test_path_swap_between_passes_is_rejected(self) -> None:
        root, connection = self.create_store("path-swap")
        connection.close()
        database = root / "workflow.sqlite3"
        moved = root / "workflow.sqlite3.original"

        def swap(_manifest) -> None:
            database.rename(moved)
            database.symlink_to(moved.name)

        hooks = workflow_store_preopen._AuditHooks(after_first_manifest_pass=swap)
        self.assert_error("SOURCE_FILE_SYMLINK", lambda: self.audit(root, _hooks=hooks))

    def test_copy_digest_mismatch_fails_before_sqlite_and_cleans_private_copy(self) -> None:
        root, connection = self.create_store("copy-mismatch")
        connection.close()
        captured: list[Path] = []

        def corrupt(private_database: Path) -> None:
            captured.append(private_database.parent)
            with private_database.open("ab") as stream:
                stream.write(b"corrupt")

        hooks = workflow_store_preopen._AuditHooks(after_private_copy=corrupt)
        with patch.object(workflow_store_preopen.sqlite3, "connect") as connect:
            self.assert_error(
                "PRIVATE_COPY_DIGEST_MISMATCH",
                lambda: self.audit(root, _hooks=hooks),
            )
        connect.assert_not_called()
        self.assertEqual(1, len(captured))
        self.assertFalse(captured[0].exists())

    def test_source_change_during_private_audit_discards_result_and_copy(self) -> None:
        root, connection = self.create_store("post-audit-race")
        connection.close()
        database = root / "workflow.sqlite3"
        private_roots: list[Path] = []

        def mutate_source() -> None:
            with database.open("ab") as stream:
                stream.write(b"late")

        def remember_copy(private_database: Path) -> None:
            private_roots.append(private_database.parent)

        hooks = workflow_store_preopen._AuditHooks(
            after_private_copy=remember_copy,
            before_post_audit_manifest=mutate_source,
        )
        self.assert_error("AUDIT_SOURCE_CHANGED", lambda: self.audit(root, _hooks=hooks))
        self.assertEqual(1, len(private_roots))
        self.assertFalse(private_roots[0].exists())

    def test_lease_rechecks_manifest_and_never_calls_opener_after_change(self) -> None:
        root, connection = self.create_store("lease-race")
        connection.close()
        outcome = self.audit(root)
        assert outcome.lease is not None
        assert self.last_guard is not None
        with (root / "workflow.sqlite3").open("ab") as stream:
            stream.write(b"after-audit")
        opened: list[Path] = []
        self.assert_error(
            "AUDIT_SOURCE_CHANGED",
            lambda: outcome.lease.consume(
                guard=self.last_guard,
                opener=lambda path, _report: opened.append(path),
            ),
        )
        self.assertEqual([], opened)
        self.assertTrue(outcome.lease.consumed)

    def test_guard_failure_prevents_manifest_copy_sqlite_and_opener(self) -> None:
        root, connection = self.create_store("guard-failure")
        connection.close()
        self.guard_state["active"] = False
        before = tuple(self.private_parent.iterdir())
        with patch.object(workflow_store_preopen.sqlite3, "connect") as connect:
            self.assert_error("AUDIT_GUARD_NOT_HELD", lambda: self.audit(root))
        connect.assert_not_called()
        self.assertEqual(before, tuple(self.private_parent.iterdir()))

        self.guard_state["active"] = True
        outcome = self.audit(root)
        assert outcome.lease is not None
        assert self.last_guard is not None
        replacement = workflow_store_preopen._mint_guard_session(
            identity=self.last_guard.identity,
            kind=self.last_guard.kind,
            is_active=lambda: True,
            raw_root=root,
        )
        opened: list[Path] = []
        self.assert_error(
            "AUDIT_GUARD_MISMATCH",
            lambda: outcome.lease.consume(
                guard=replacement,
                opener=lambda path, _report: opened.append(path),
            ),
        )
        self.assertEqual([], opened)

    def test_v6_is_explicitly_blocked_and_v7_fingerprint_can_be_pinned(self) -> None:
        v6_root, v6 = self.create_store("v6", version=6)
        v6.close()
        v6_outcome = self.audit(v6_root)
        self.assertEqual("BLOCKED", v6_outcome.report.disposition)
        self.assertEqual(
            ("UPGRADE_BLOCKED_UNVERIFIED_V6",), v6_outcome.report.blockers
        )
        self.assertIsNone(v6_outcome.lease)

        v7_root, v7 = self.create_store("v7")
        v7.close()
        admitted = self.audit(v7_root)
        assert admitted.report.schema_fingerprint is not None
        assert admitted.lease is not None
        admitted.lease.discard()
        pinned = self.audit(
            v7_root,
            _expected_schema_fingerprints={7: {admitted.report.schema_fingerprint}},
        )
        self.assertEqual("CLEAR", pinned.report.disposition)
        assert pinned.lease is not None
        pinned.lease.discard()
        mismatch = self.audit(
            v7_root,
            _expected_schema_fingerprints={7: {"0" * 64}},
        )
        self.assertEqual("BLOCKED", mismatch.report.disposition)
        self.assertEqual(
            ("SCHEMA_FINGERPRINT_MISMATCH:7",), mismatch.report.blockers
        )

    def test_schema_mismatch_short_circuits_all_semantic_queries(self) -> None:
        root, connection = self.create_store("schema-short-circuit")
        connection.execute("CREATE TABLE unexpected_schema_object(value TEXT)")
        connection.commit()
        connection.close()

        with patch.object(
            workflow_store_preopen,
            "_open_legacy_facts",
            side_effect=AssertionError("legacy queries must not run"),
        ) as legacy, patch.object(
            workflow_store_preopen,
            "_historical_released_facts",
            side_effect=AssertionError("accounting queries must not run"),
        ) as historical:
            outcome = self.audit(root)

        self.assertEqual("BLOCKED", outcome.report.disposition)
        self.assertEqual(("SCHEMA_FINGERPRINT_MISMATCH:7",), outcome.report.blockers)
        self.assertEqual((), outcome.report.open_transactions)
        self.assertEqual((), outcome.report.historical_released)
        legacy.assert_not_called()
        historical.assert_not_called()

    def test_legacy_state_matrix_blocks_unsafe_continuation_and_open_runs(self) -> None:
        root, connection = self.create_store("legacy-state-matrix")
        connection.executemany(
            "INSERT INTO implementation_transactions VALUES (?, ?, ?, ?)",
            (
                ("tx-open-closed", "INITIAL_IMPLEMENTATION", "OPEN", "closed"),
                ("tx-closed-open", "INITIAL_IMPLEMENTATION", "CLOSED_WITH_HANDOFF", None),
                ("tx-failed", "INITIAL_IMPLEMENTATION", "FAILED", None),
                ("tx-dispatched", "INITIAL_IMPLEMENTATION", "WORKER_ACTIVE", None),
                ("tx-multiple", "INITIAL_IMPLEMENTATION", "OPEN", None),
            ),
        )
        connection.executemany(
            "INSERT INTO implementation_envelopes VALUES (?, ?, ?, ?, ?)",
            (
                ("env-dispatched", "tx-dispatched", "task-1", "DISPATCHED", None),
                ("env-multiple-1", "tx-multiple", "task-1", "FROZEN", None),
                ("env-multiple-2", "tx-multiple", "task-2", "FROZEN", None),
            ),
        )
        connection.executemany(
            "INSERT INTO verification_runs VALUES (?, ?, ?, ?, NULL, NULL)",
            (
                ("run-open", "claim-open", "SEALED", None),
                ("run-closed-missing-time", "claim-closed", "CLOSED", None),
            ),
        )
        connection.commit()
        connection.close()

        outcome = self.audit(root)

        self.assertEqual("BLOCKED", outcome.report.disposition)
        self.assertIn(
            "LEGACY_TRANSACTION:tx-open-closed:OPEN_STATE_HAS_CLOSED_AT",
            outcome.report.blockers,
        )
        self.assertIn(
            "LEGACY_TRANSACTION:tx-closed-open:CLOSED_STATE_MISSING_CLOSED_AT",
            outcome.report.blockers,
        )
        self.assertIn(
            "LEGACY_TRANSACTION:tx-failed:UNSUPPORTED_STATE:FAILED",
            outcome.report.blockers,
        )
        self.assertIn(
            "LEGACY_ENVELOPE:env-dispatched:CONTINUATION_NOT_ADMITTED:DISPATCHED",
            outcome.report.blockers,
        )
        self.assertIn(
            "LEGACY_TRANSACTION:tx-multiple:MULTIPLE_ACTIVE_ENVELOPES:2",
            outcome.report.blockers,
        )
        self.assertIn(
            "LEGACY_RUN:run-open:CONTROLLED_DRAIN_REQUIRED:SEALED",
            outcome.report.blockers,
        )
        self.assertIn(
            "LEGACY_RUN:run-closed-missing-time:CLOSED_STATE_MISSING_CLOSED_AT",
            outcome.report.blockers,
        )

    def test_single_frozen_envelope_remains_revalidation_candidate(self) -> None:
        root, connection = self.create_store("legacy-frozen-candidate")
        connection.execute(
            "INSERT INTO implementation_transactions VALUES (?, ?, ?, NULL)",
            ("tx-frozen", "INITIAL_IMPLEMENTATION", "OPEN"),
        )
        connection.execute(
            "INSERT INTO implementation_envelopes VALUES (?, ?, ?, ?, NULL)",
            ("env-frozen", "tx-frozen", "task-1", "FROZEN"),
        )
        connection.commit()
        connection.close()

        outcome = self.audit(root)

        self.assertEqual("CLEAR", outcome.report.disposition)
        self.assertEqual(("tx-frozen",), tuple(x.transaction_ref for x in outcome.report.open_transactions))
        self.assertEqual(("env-frozen",), tuple(x.envelope_ref for x in outcome.report.open_envelopes))
        assert outcome.lease is not None
        outcome.lease.discard()

    def test_default_authority_pins_actual_v7_and_blocks_schema_tamper(self) -> None:
        root = self.base / "authoritative-v7"
        root.mkdir(mode=0o700)
        database = root / workflow_store_preopen.DATABASE_FILENAME
        connection = sqlite3.connect(database)
        try:
            connection.executescript(V7_SCHEMA_FIXTURE.read_text(encoding="utf-8"))
            connection.commit()
        finally:
            connection.close()
        os.chmod(database, 0o600)

        admitted = workflow_store_preopen.audit_workflow_store(
            root,
            guard=self.guard_for(root),
            private_parent=self.private_parent,
        )

        self.assertEqual("CLEAR", admitted.report.disposition)
        self.assertEqual(7, admitted.report.schema_version)
        self.assertIn(
            admitted.report.schema_fingerprint,
            workflow_store_preopen.AUTHORITATIVE_SCHEMA_FINGERPRINTS[7],
        )
        assert admitted.lease is not None
        admitted.lease.discard()

        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "CREATE TABLE schema_tamper_but_required_tables_remain(value TEXT)"
            )
            connection.commit()
        finally:
            connection.close()
        tampered = workflow_store_preopen.audit_workflow_store(
            root,
            guard=self.guard_for(root),
            private_parent=self.private_parent,
        )
        self.assertEqual("BLOCKED", tampered.report.disposition)
        self.assertIn("SCHEMA_FINGERPRINT_MISMATCH:7", tampered.report.blockers)
        self.assertIsNone(tampered.lease)

    def test_v9_executor_floor_is_a_private_copy_admission_barrier(self) -> None:
        for mutation in ("missing", "wrong"):
            with self.subTest(mutation=mutation):
                root = self.base / f"v9-floor-{mutation}"
                workflow_guard = workflow_store._mint_test_guard_session(
                    store_root=root,
                    identity=f"workflow-create:{mutation}",
                    is_active=lambda: True,
                )
                store = workflow_store.audit_and_open_workflow_store(
                    root,
                    guard=workflow_guard,
                    private_parent=self.private_parent,
                ).store
                connection = sqlite3.connect(store.database_path)
                try:
                    if mutation == "missing":
                        connection.execute(
                            "DELETE FROM store_meta WHERE key = 'executor_floor'"
                        )
                    else:
                        connection.execute(
                            "UPDATE store_meta SET value = 'process-v2' WHERE key = 'executor_floor'"
                        )
                    connection.commit()
                finally:
                    connection.close()
                before = workflow_store_preopen.capture_source_manifest(root)

                outcome = workflow_store_preopen.audit_workflow_store(
                    root,
                    guard=self.guard_for(root),
                    private_parent=self.private_parent,
                )
                after = workflow_store_preopen.capture_source_manifest(root)

                self.assertEqual(before, after)
                self.assertEqual("BLOCKED", outcome.report.disposition)
                self.assertIn("EXECUTOR_FLOOR_MISMATCH:9", outcome.report.blockers)
                self.assertIsNone(outcome.lease)

    def test_v9_open_run_classifier_admits_only_current_process_policy(self) -> None:
        step = {
            "executorKind": "PROCESS",
            "executorVersion": "process-v3",
            "environmentPolicy": "SEALED_EMPTY_BASE_V1",
            "executableIdentity": {
                "canonicalPath": "/usr/bin/tool",
                "contentSha256": "a" * 64,
                "byteCount": 1,
                "executableMode": 0o755,
                "ownerUid": 0,
                "ownerGid": 0,
            },
            "canonicalRequestDigest": "b" * 64,
            "repeatRequestDigest": "c" * 64,
        }
        plan = json.dumps(
            {"flows": [{"flowId": "flow-1", "steps": [step]}]},
            separators=(",", ":"),
        ).encode()
        current = workflow_store_preopen.LegacyRunFact(
            "run-v3",
            "claim-v3",
            "SEALED",
            None,
            plan,
            hashlib.sha256(plan).hexdigest(),
        )
        self.assertEqual(
            (),
            workflow_store_preopen._legacy_fact_blockers(
                (), (), (current,), schema_version=9
            ),
        )
        self.assertIn(
            "LEGACY_RUN:run-v3:CONTROLLED_DRAIN_REQUIRED:SEALED",
            workflow_store_preopen._legacy_fact_blockers(
                (), (), (current,), schema_version=7
            ),
        )

        legacy_step = dict(step)
        legacy_step["executorVersion"] = "process-v2"
        legacy_plan = json.dumps(
            {"flows": [{"flowId": "flow-1", "steps": [legacy_step]}]},
            separators=(",", ":"),
        ).encode()
        legacy = workflow_store_preopen.LegacyRunFact(
            "run-v2",
            "claim-v2",
            "SEALED",
            None,
            legacy_plan,
            hashlib.sha256(legacy_plan).hexdigest(),
        )
        self.assertIn(
            "LEGACY_RUN:run-v2:NON_V3_OR_MALFORMED_EXECUTOR",
            workflow_store_preopen._legacy_fact_blockers(
                (), (), (legacy,), schema_version=9
            ),
        )

        preflight = workflow_store_preopen.LegacyRunFact(
            "run-preflight", "claim-preflight", "PREFLIGHT", None, None, None
        )
        self.assertEqual(
            (),
            workflow_store_preopen._legacy_fact_blockers(
                (), (), (preflight,), schema_version=9
            ),
        )

    def insert_historical_release(
        self,
        connection: sqlite3.Connection,
        *,
        claim_ref: str,
        spend_used: str | None = None,
        closure_used: str | None = None,
        actor_invocation: str = "invocation:1",
        closure_version: int = 1,
    ) -> None:
        zero = self.budget()
        spend_used = zero if spend_used is None else spend_used
        closure_used = zero if closure_used is None else closure_used
        connection.execute(
            "INSERT INTO invocations VALUES (?, ?, ?, 'ACTIVE')",
            ("invocation:1", self.budget(workerCalls=10), zero),
        )
        connection.execute(
            "INSERT INTO actors VALUES ('actor:1', 'ASSESSOR', 'root:1', ?, ?)",
            (actor_invocation, claim_ref),
        )
        connection.execute(
            """
            INSERT INTO budget_reservations VALUES(
                'reservation:1', 'invocation:1', 'VERIFY', ?, ?, ?, ?, 'CLOSED', 'closed'
            )
            """,
            (
                self.budget(workerCalls=10),
                self.budget(closureOperations=10),
                spend_used,
                closure_used,
            ),
        )
        connection.execute(
            """
            INSERT INTO claims VALUES(
                ?, 'root:1', 'VERIFY', 'verification:run:v1:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                ?, 'closed', 'actor:1', 'reservation:1', 'RELEASED'
            )
            """,
            (claim_ref, f"closure:unstarted:v{closure_version}:{'a' * 32}"),
        )
        connection.commit()

    def test_historical_zero_usage_is_reported_and_nonzero_usage_blocks(self) -> None:
        zero_root, zero_connection = self.create_store("historical-zero")
        self.insert_historical_release(zero_connection, claim_ref="claim:zero")
        zero_connection.close()
        zero = self.audit(zero_root)
        self.assertEqual("CLEAR", zero.report.disposition)
        self.assertEqual(("claim:zero",), tuple(x.claim_ref for x in zero.report.historical_released))
        self.assertEqual((), zero.report.historical_released[0].issues)

        used_root, used_connection = self.create_store("historical-used")
        self.insert_historical_release(
            used_connection,
            claim_ref="claim:used",
            spend_used=self.budget(workerCalls=1),
            closure_used=self.budget(closureOperations=1),
        )
        used_connection.close()
        used = self.audit(used_root)
        self.assertEqual("BLOCKED", used.report.disposition)
        self.assertIn(
            "HISTORICAL_RELEASED:claim:used:HISTORICAL_SPEND_USAGE_UNPROVABLE",
            used.report.blockers,
        )
        self.assertIn(
            "HISTORICAL_RELEASED:claim:used:HISTORICAL_CLOSURE_USAGE_UNPROVABLE",
            used.report.blockers,
        )
        self.assertIsNone(used.lease)

    def test_conserved_release_marker_is_not_authority_in_schema_v7(self) -> None:
        root, connection = self.create_store("historical-v2-on-v7")
        self.insert_historical_release(
            connection,
            claim_ref="claim:v2-on-v7",
            spend_used=self.budget(workerCalls=1),
            closure_version=2,
        )
        connection.close()

        outcome = self.audit(root)

        self.assertEqual("BLOCKED", outcome.report.disposition)
        self.assertIn(
            "HISTORICAL_RELEASED:claim:v2-on-v7:CONSERVED_CLOSURE_REQUIRES_V9",
            outcome.report.blockers,
        )
        self.assertIsNone(outcome.lease)

    def test_historical_relational_and_json_corruption_blocks(self) -> None:
        root, connection = self.create_store("historical-corrupt")
        self.insert_historical_release(
            connection,
            claim_ref="claim:corrupt",
            spend_used='{"wrong":0}',
            actor_invocation="invocation:other",
        )
        connection.execute(
            """
            UPDATE actors
            SET role = 'WORKER', root_ref = 'root:other', bound_claim_ref = 'claim:other'
            WHERE actor_ref = 'actor:1'
            """
        )
        connection.execute(
            "UPDATE budget_reservations SET transition_kind = 'REMEDIATE' WHERE reservation_ref = 'reservation:1'"
        )
        connection.execute(
            "UPDATE invocations SET state = 'BROKEN' WHERE invocation_ref = 'invocation:1'"
        )
        execution_ref = "verification:run:v1:" + "a" * 32
        connection.execute(
            "INSERT INTO verification_runs VALUES (?, 'claim:corrupt', 'CLOSED', 'closed', NULL, NULL)",
            (execution_ref,),
        )
        connection.execute(
            "INSERT INTO implementation_transactions VALUES (?, 'INITIAL_IMPLEMENTATION', 'CLOSED_NO_SUCCESSOR', 'closed')",
            (execution_ref,),
        )
        connection.commit()
        connection.close()

        outcome = self.audit(root)

        self.assertEqual("BLOCKED", outcome.report.disposition)
        self.assertIn(
            "HISTORICAL_RELEASED:claim:corrupt:ACTOR_INVOCATION_MISMATCH",
            outcome.report.blockers,
        )
        self.assertIn(
            "HISTORICAL_RELEASED:claim:corrupt:MALFORMED_SPEND_USED_JSON",
            outcome.report.blockers,
        )
        for issue in (
            "TRANSITION_KIND_MISMATCH",
            "CLAIMANT_ROLE_MISMATCH",
            "ACTOR_ROOT_MISMATCH",
            "ACTOR_CLAIM_BINDING_MISMATCH",
            "INVOCATION_STATE_INVALID",
            "DURABLE_VERIFICATION_RUN_PRESENT",
            "DURABLE_IMPLEMENTATION_TRANSACTION_PRESENT",
        ):
            self.assertIn(
                f"HISTORICAL_RELEASED:claim:corrupt:{issue}",
                outcome.report.blockers,
            )


if __name__ == "__main__":
    unittest.main()
