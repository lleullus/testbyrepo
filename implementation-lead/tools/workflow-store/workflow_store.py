#!/usr/bin/env python3
"""Owner-only immutable workflow nodes, linear continuation, and transition claims.

This module owns mechanical workflow serialization only. It does not interpret a
Ticket, assess an Acceptance Criterion, authorize product mutation, or execute a
verification step.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping


SCHEMA_VERSION = 7
DEFAULT_STORE_ROOT = Path.home() / ".local/state/opencode/implementation-workflows"

NODE_KINDS = {"IMPLEMENTATION_HANDOFF", "VERIFICATION_RESULT"}
TRANSITION_KINDS = {"VERIFY", "REMEDIATE"}
ACTOR_ROLES = {"COORDINATOR", "ASSESSOR", "REMEDIATOR", "WORKER"}
VERIFICATION_STATUSES = {"VERIFIED", "VERIFICATION_FAILED", "INCOMPLETE", "BLOCKED"}
BUDGET_FIELDS = (
    "workerCalls",
    "remediationTransactions",
    "effectfulActions",
    "toolCostUnits",
    "closureOperations",
)

REF_PATTERNS = {
    "IMPLEMENTATION_HANDOFF": re.compile(r"^implementation:handoff:v1:[a-f0-9]{32}$"),
    "VERIFICATION_RESULT": re.compile(r"^verification:result:v1:[a-f0-9]{32}$"),
}
EXECUTION_REF_PATTERN = re.compile(
    r"^(verification:run|implementation:transaction):v1:[a-f0-9]{32}$"
)
ACTOR_REF_PATTERN = re.compile(r"^actor:v1:(coordinator|assessor|remediator|worker):[a-f0-9]{32}$")
CLAIM_REF_PATTERN = re.compile(r"^claim:v1:[a-f0-9]{32}$")
INVOCATION_REF_PATTERN = re.compile(r"^verification:invocation:v1:[a-f0-9]{32}$")
BUDGET_REF_PATTERN = re.compile(r"^budget:reservation:v1:[a-f0-9]{32}$")
AUTHORIZATION_REF_PATTERN = re.compile(r"^authorization:v1:[a-f0-9]{32}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SOURCE_IDENTITY_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
CAPABILITY_PATTERN = re.compile(r"^cap:v1:[a-f0-9]{64}$")

MAX_PAYLOAD_BYTES = 1024 * 1024
MAX_LINEAGE_NODES = 1024


class WorkflowStoreError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_time(value: str, locator: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowStoreError("STORE_CORRUPT", f"{locator} is not ISO-8601") from exc
    if parsed.tzinfo is None:
        raise WorkflowStoreError("STORE_CORRUPT", f"{locator} has no timezone")
    return parsed.astimezone(timezone.utc)


def _budget_vector(value: Any, locator: str, *, require_closure: bool = False) -> dict[str, int]:
    mapping = _mapping(value, locator)
    if set(mapping) != set(BUDGET_FIELDS):
        raise WorkflowStoreError("MALFORMED_BUDGET", f"{locator} fields are invalid")
    normalized: dict[str, int] = {}
    for field in BUDGET_FIELDS:
        amount = mapping[field]
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise WorkflowStoreError("MALFORMED_BUDGET", f"{locator}.{field} must be a non-negative integer")
        normalized[field] = amount
    if require_closure and normalized["closureOperations"] <= 0:
        raise WorkflowStoreError("MALFORMED_BUDGET", f"{locator} must reserve closure operations")
    return normalized


def _zero_budget() -> dict[str, int]:
    return {field: 0 for field in BUDGET_FIELDS}


def _add_budget(*vectors: Mapping[str, int]) -> dict[str, int]:
    return {field: sum(int(vector[field]) for vector in vectors) for field in BUDGET_FIELDS}


def canonical_json(value: object) -> bytes:
    try:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise WorkflowStoreError("MALFORMED_ARTIFACT", f"value is not JSON serializable: {exc}") from exc
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise WorkflowStoreError("MALFORMED_ARTIFACT", f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
    return payload


def allocate_ref(kind: str) -> str:
    token = uuid.uuid4().hex
    if kind == "IMPLEMENTATION_HANDOFF":
        return f"implementation:handoff:v1:{token}"
    if kind == "VERIFICATION_RESULT":
        return f"verification:result:v1:{token}"
    if kind == "VERIFY":
        return f"verification:run:v1:{token}"
    if kind == "REMEDIATE":
        return f"implementation:transaction:v1:{token}"
    if kind == "INVOCATION":
        return f"verification:invocation:v1:{token}"
    raise WorkflowStoreError("INVALID_KIND", f"cannot allocate ref for {kind}")


def _capability_digest(capability: str) -> str:
    if not isinstance(capability, str) or not CAPABILITY_PATTERN.fullmatch(capability):
        raise WorkflowStoreError("INVALID_CAPABILITY", "capability is malformed")
    return hashlib.sha256(capability.encode("ascii")).hexdigest()


def _mapping(value: Any, locator: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkflowStoreError("MALFORMED_ARTIFACT", f"{locator} must be an object")
    return value


def _validate_node_payload(
    *,
    node_ref: str,
    node_kind: str,
    protocol_version: str,
    planning_identity: str,
    source_identity: str,
    verification_status: str | None,
    payload: Mapping[str, Any],
) -> bytes:
    if node_kind not in NODE_KINDS:
        raise WorkflowStoreError("INVALID_NODE_KIND", f"unsupported node kind: {node_kind}")
    if not REF_PATTERNS[node_kind].fullmatch(node_ref):
        raise WorkflowStoreError("MALFORMED_ARTIFACT", f"node ref does not match {node_kind}")
    if not isinstance(protocol_version, str) or not protocol_version:
        raise WorkflowStoreError("MALFORMED_ARTIFACT", "protocol version is required")
    if not SHA256_PATTERN.fullmatch(planning_identity):
        raise WorkflowStoreError("MALFORMED_ARTIFACT", "planning identity must be a lowercase SHA-256")
    if not SOURCE_IDENTITY_PATTERN.fullmatch(source_identity):
        raise WorkflowStoreError("MALFORMED_ARTIFACT", "source identity is malformed")
    if payload.get("protocolVersion") != protocol_version:
        raise WorkflowStoreError("MALFORMED_ARTIFACT", "payload protocolVersion differs")
    if payload.get("planningSealDigest") != planning_identity:
        raise WorkflowStoreError("PLANNING_IDENTITY_MISMATCH", "payload planning identity differs")
    if payload.get("finalSourceIdentity") != source_identity:
        raise WorkflowStoreError("SOURCE_IDENTITY_MISMATCH", "payload source identity differs")
    if node_kind == "IMPLEMENTATION_HANDOFF":
        if payload.get("implementationHandoffRef") != node_ref:
            raise WorkflowStoreError("MALFORMED_ARTIFACT", "handoff ref differs from node ref")
        if verification_status is not None:
            raise WorkflowStoreError("MALFORMED_ARTIFACT", "handoff cannot carry verification status")
    else:
        if payload.get("verificationResultRef") != node_ref:
            raise WorkflowStoreError("MALFORMED_ARTIFACT", "result ref differs from node ref")
        if verification_status not in VERIFICATION_STATUSES:
            raise WorkflowStoreError("MALFORMED_ARTIFACT", "verification status is invalid")
        if payload.get("verificationStatus") != verification_status:
            raise WorkflowStoreError("MALFORMED_ARTIFACT", "payload verification status differs")
    return canonical_json(payload)


class WorkflowStore:
    """SQLite-backed append-only graph with atomic claim consumption."""

    def __init__(self, store_root: Path | str = DEFAULT_STORE_ROOT) -> None:
        self.store_root = Path(store_root).expanduser().resolve()
        self.store_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.store_root.is_symlink() or not self.store_root.is_dir():
            raise WorkflowStoreError("INVALID_STORE", "workflow store root must be a real directory")
        os.chmod(self.store_root, 0o700)
        self.database_path = self.store_root / "workflow.sqlite3"
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _enforce_owner_only_modes(self) -> None:
        os.chmod(self.store_root, 0o700)
        for suffix in ("", "-journal", "-wal", "-shm"):
            path = Path(f"{self.database_path}{suffix}")
            if path.exists():
                os.chmod(path, 0o600)

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
            self._enforce_owner_only_modes()

    def _initialize(self) -> None:
        with self._transaction() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS store_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS nodes (
                    node_ref TEXT PRIMARY KEY,
                    node_kind TEXT NOT NULL CHECK (node_kind IN ('IMPLEMENTATION_HANDOFF', 'VERIFICATION_RESULT')),
                    protocol_version TEXT NOT NULL,
                    root_ref TEXT NOT NULL,
                    planning_identity TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    verification_status TEXT,
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS edges (
                    predecessor_ref TEXT PRIMARY KEY REFERENCES nodes(node_ref),
                    successor_ref TEXT NOT NULL UNIQUE REFERENCES nodes(node_ref),
                    transition_kind TEXT NOT NULL CHECK (transition_kind IN ('VERIFY', 'REMEDIATE')),
                    claim_ref TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS invocations (
                    invocation_ref TEXT PRIMARY KEY,
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    deadline_at TEXT NOT NULL,
                    limits_json BLOB NOT NULL,
                    consumed_json BLOB NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CLOSED')),
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS actors (
                    actor_ref TEXT PRIMARY KEY,
                    role TEXT NOT NULL CHECK (role IN ('COORDINATOR', 'ASSESSOR', 'REMEDIATOR', 'WORKER')),
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    invocation_ref TEXT NOT NULL REFERENCES invocations(invocation_ref),
                    capability_sha256 TEXT NOT NULL UNIQUE,
                    bound_claim_ref TEXT UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS authorizations (
                    authorization_ref TEXT PRIMARY KEY,
                    invocation_ref TEXT NOT NULL REFERENCES invocations(invocation_ref),
                    scope_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS budget_reservations (
                    reservation_ref TEXT PRIMARY KEY,
                    invocation_ref TEXT NOT NULL REFERENCES invocations(invocation_ref),
                    transition_kind TEXT NOT NULL CHECK (transition_kind IN ('VERIFY', 'REMEDIATE')),
                    spend_reserved_json BLOB NOT NULL,
                    closure_reserved_json BLOB NOT NULL,
                    spend_used_json BLOB NOT NULL,
                    closure_used_json BLOB NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CLOSED')),
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS claims (
                    claim_ref TEXT PRIMARY KEY,
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    tip_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    transition_kind TEXT NOT NULL CHECK (transition_kind IN ('VERIFY', 'REMEDIATE')),
                    coordinator_actor_ref TEXT NOT NULL REFERENCES actors(actor_ref),
                    claimant_actor_ref TEXT NOT NULL UNIQUE REFERENCES actors(actor_ref),
                    planning_identity TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    execution_ref TEXT NOT NULL UNIQUE,
                    budget_reservation_ref TEXT NOT NULL UNIQUE REFERENCES budget_reservations(reservation_ref),
                    state TEXT NOT NULL CHECK (state IN ('ACTIVE', 'CONSUMED', 'RELEASED')),
                    successor_ref TEXT REFERENCES nodes(node_ref),
                    closure_ref TEXT,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS implementation_transactions (
                    transaction_ref TEXT PRIMARY KEY,
                    mode TEXT NOT NULL CHECK (mode IN ('INITIAL_IMPLEMENTATION', 'VERIFICATION_REMEDIATION')),
                    root_ref TEXT REFERENCES nodes(node_ref),
                    claim_ref TEXT UNIQUE REFERENCES claims(claim_ref),
                    owner_actor_ref TEXT REFERENCES actors(actor_ref),
                    worker_actor_ref TEXT REFERENCES actors(actor_ref),
                    selected_worker TEXT NOT NULL,
                    capability_sha256 TEXT NOT NULL UNIQUE,
                    worker_capability_sha256 TEXT NOT NULL,
                    project_root TEXT NOT NULL,
                    planning_identity TEXT NOT NULL,
                    baseline_capsule_ref TEXT NOT NULL,
                    baseline_source_identity TEXT NOT NULL,
                    admission_json BLOB,
                    state TEXT NOT NULL CHECK (
                        state IN ('OPEN', 'WORKER_ACTIVE', 'RECONCILING', 'READY_FOR_HANDOFF',
                                  'CLOSED_WITH_HANDOFF', 'CLOSED_NO_SUCCESSOR', 'FAILED')
                    ),
                    final_source_identity TEXT,
                    implementation_delta_ref TEXT,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS implementation_envelopes (
                    envelope_ref TEXT PRIMARY KEY,
                    transaction_ref TEXT NOT NULL REFERENCES implementation_transactions(transaction_ref),
                    task_id TEXT NOT NULL,
                    criterion_refs_json BLOB NOT NULL,
                    allowed_paths_json BLOB NOT NULL,
                    forbidden_paths_json BLOB NOT NULL,
                    before_snapshot_json BLOB NOT NULL,
                    before_snapshot_sha256 TEXT NOT NULL,
                    after_snapshot_json BLOB,
                    after_snapshot_sha256 TEXT,
                    delta_json BLOB,
                    reconciliation_json BLOB,
                    state TEXT NOT NULL CHECK (state IN ('FROZEN', 'DISPATCHED', 'CAPTURED', 'RECONCILED')),
                    created_at TEXT NOT NULL,
                    closed_at TEXT,
                    UNIQUE(transaction_ref, task_id)
                );

                CREATE TABLE IF NOT EXISTS implementation_checks (
                    check_ref TEXT PRIMARY KEY,
                    transaction_ref TEXT NOT NULL REFERENCES implementation_transactions(transaction_ref),
                    request_json BLOB NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    result_json BLOB NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS implementation_deltas (
                    delta_ref TEXT PRIMARY KEY,
                    transaction_ref TEXT NOT NULL UNIQUE REFERENCES implementation_transactions(transaction_ref),
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS implementation_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_ref TEXT NOT NULL REFERENCES implementation_transactions(transaction_ref),
                    event_kind TEXT NOT NULL,
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS verification_runs (
                    run_ref TEXT PRIMARY KEY,
                    root_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    claim_ref TEXT NOT NULL UNIQUE REFERENCES claims(claim_ref),
                    assessor_actor_ref TEXT NOT NULL UNIQUE REFERENCES actors(actor_ref),
                    implementation_handoff_ref TEXT NOT NULL REFERENCES nodes(node_ref),
                    project_root TEXT NOT NULL,
                    planning_identity TEXT NOT NULL,
                    source_identity TEXT NOT NULL,
                    preflight_json BLOB NOT NULL,
                    sealed_plan_json BLOB,
                    sealed_plan_sha256 TEXT,
                    state TEXT NOT NULL CHECK (state IN ('PREFLIGHT', 'SEALED', 'CLOSED')),
                    closure_json BLOB,
                    created_at TEXT NOT NULL,
                    closed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS verification_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    flow_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_role TEXT NOT NULL CHECK (step_role IN ('ACTION', 'READBACK', 'CLEANUP')),
                    poll_index INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    request_sha256 TEXT NOT NULL,
                    source_identity_before TEXT,
                    source_identity_after TEXT,
                    artifact_ref TEXT,
                    result_json BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(run_ref, flow_id, step_id, poll_index)
                );

                CREATE TABLE IF NOT EXISTS verification_step_executions (
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    flow_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('STARTED', 'COMPLETED', 'NOT_RUN')),
                    request_sha256 TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    PRIMARY KEY(run_ref, flow_id, step_id)
                );

                CREATE TABLE IF NOT EXISTS verification_artifacts (
                    artifact_ref TEXT PRIMARY KEY,
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    media_type TEXT NOT NULL,
                    payload BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    byte_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS verification_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_ref TEXT NOT NULL REFERENCES verification_runs(run_ref),
                    event_kind TEXT NOT NULL,
                    payload_json BLOB NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS one_active_claim_per_tip
                    ON claims(tip_ref) WHERE state = 'ACTIVE';
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_claim_per_root
                    ON claims(root_ref) WHERE state = 'ACTIVE';

                CREATE TRIGGER IF NOT EXISTS nodes_no_update
                BEFORE UPDATE ON nodes BEGIN SELECT RAISE(ABORT, 'immutable nodes'); END;
                CREATE TRIGGER IF NOT EXISTS nodes_no_delete
                BEFORE DELETE ON nodes BEGIN SELECT RAISE(ABORT, 'immutable nodes'); END;
                CREATE TRIGGER IF NOT EXISTS edges_no_update
                BEFORE UPDATE ON edges BEGIN SELECT RAISE(ABORT, 'immutable edges'); END;
                CREATE TRIGGER IF NOT EXISTS edges_no_delete
                BEFORE DELETE ON edges BEGIN SELECT RAISE(ABORT, 'immutable edges'); END;
                CREATE TRIGGER IF NOT EXISTS implementation_checks_no_update
                BEFORE UPDATE ON implementation_checks BEGIN SELECT RAISE(ABORT, 'immutable implementation checks'); END;
                CREATE TRIGGER IF NOT EXISTS implementation_checks_no_delete
                BEFORE DELETE ON implementation_checks BEGIN SELECT RAISE(ABORT, 'immutable implementation checks'); END;
                CREATE TRIGGER IF NOT EXISTS implementation_deltas_no_update
                BEFORE UPDATE ON implementation_deltas BEGIN SELECT RAISE(ABORT, 'immutable implementation deltas'); END;
                CREATE TRIGGER IF NOT EXISTS implementation_deltas_no_delete
                BEFORE DELETE ON implementation_deltas BEGIN SELECT RAISE(ABORT, 'immutable implementation deltas'); END;
                CREATE TRIGGER IF NOT EXISTS implementation_events_no_update
                BEFORE UPDATE ON implementation_events BEGIN SELECT RAISE(ABORT, 'immutable implementation events'); END;
                CREATE TRIGGER IF NOT EXISTS implementation_events_no_delete
                BEFORE DELETE ON implementation_events BEGIN SELECT RAISE(ABORT, 'immutable implementation events'); END;
                CREATE TRIGGER IF NOT EXISTS authorizations_no_update
                BEFORE UPDATE ON authorizations BEGIN SELECT RAISE(ABORT, 'immutable authorizations'); END;
                CREATE TRIGGER IF NOT EXISTS authorizations_no_delete
                BEFORE DELETE ON authorizations BEGIN SELECT RAISE(ABORT, 'immutable authorizations'); END;
                CREATE TRIGGER IF NOT EXISTS verification_attempts_no_update
                BEFORE UPDATE ON verification_attempts BEGIN SELECT RAISE(ABORT, 'immutable verification attempts'); END;
                CREATE TRIGGER IF NOT EXISTS verification_attempts_no_delete
                BEFORE DELETE ON verification_attempts BEGIN SELECT RAISE(ABORT, 'immutable verification attempts'); END;
                CREATE TRIGGER IF NOT EXISTS verification_step_executions_no_delete
                BEFORE DELETE ON verification_step_executions BEGIN SELECT RAISE(ABORT, 'immutable verification step executions'); END;
                CREATE TRIGGER IF NOT EXISTS verification_artifacts_no_update
                BEFORE UPDATE ON verification_artifacts BEGIN SELECT RAISE(ABORT, 'immutable verification artifacts'); END;
                CREATE TRIGGER IF NOT EXISTS verification_artifacts_no_delete
                BEFORE DELETE ON verification_artifacts BEGIN SELECT RAISE(ABORT, 'immutable verification artifacts'); END;
                CREATE TRIGGER IF NOT EXISTS verification_events_no_update
                BEFORE UPDATE ON verification_events BEGIN SELECT RAISE(ABORT, 'immutable verification events'); END;
                CREATE TRIGGER IF NOT EXISTS verification_events_no_delete
                BEFORE DELETE ON verification_events BEGIN SELECT RAISE(ABORT, 'immutable verification events'); END;
                """
            )
            row = connection.execute("SELECT value FROM store_meta WHERE key = 'schema_version'").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO store_meta(key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif row["value"] == "6":
                # v7 adds only the owner-controlled exactly-once verification-step
                # execution table and its delete guard, both created idempotently above.
                connection.execute(
                    "UPDATE store_meta SET value = ? WHERE key = 'schema_version'",
                    (str(SCHEMA_VERSION),),
                )
            elif row["value"] != str(SCHEMA_VERSION):
                raise WorkflowStoreError("UNSUPPORTED_STORE", "workflow store schema version differs")

    @staticmethod
    def _node_view(row: sqlite3.Row) -> dict[str, Any]:
        try:
            payload = json.loads(bytes(row["payload_json"]))
        except (TypeError, json.JSONDecodeError) as exc:
            raise WorkflowStoreError("STORE_CORRUPT", "stored node payload is unreadable") from exc
        actual_digest = hashlib.sha256(bytes(row["payload_json"])).hexdigest()
        if actual_digest != row["payload_sha256"]:
            raise WorkflowStoreError("STORE_CORRUPT", f"node payload digest differs: {row['node_ref']}")
        return {
            "nodeRef": row["node_ref"],
            "nodeKind": row["node_kind"],
            "protocolVersion": row["protocol_version"],
            "rootRef": row["root_ref"],
            "planningIdentity": row["planning_identity"],
            "sourceIdentity": row["source_identity"],
            "verificationStatus": row["verification_status"],
            "payloadSha256": row["payload_sha256"],
            "payload": payload,
            "createdAt": row["created_at"],
        }

    def publish_initial_handoff(
        self,
        *,
        node_ref: str,
        protocol_version: str,
        planning_identity: str,
        source_identity: str,
        payload: Mapping[str, Any],
        implementation_transaction_ref: str | None = None,
        validate_currentness: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        encoded = _validate_node_payload(
            node_ref=node_ref,
            node_kind="IMPLEMENTATION_HANDOFF",
            protocol_version=protocol_version,
            planning_identity=planning_identity,
            source_identity=source_identity,
            verification_status=None,
            payload=_mapping(payload, "payload"),
        )
        created_at = utc_now()
        try:
            with self._transaction() as connection:
                transaction = None
                if implementation_transaction_ref is not None:
                    transaction = connection.execute(
                        "SELECT * FROM implementation_transactions WHERE transaction_ref = ?",
                        (implementation_transaction_ref,),
                    ).fetchone()
                    if (
                        transaction is None
                        or transaction["mode"] != "INITIAL_IMPLEMENTATION"
                        or transaction["state"] != "READY_FOR_HANDOFF"
                    ):
                        raise WorkflowStoreError(
                            "IMPLEMENTATION_TRANSACTION_NOT_READY",
                            "initial handoff requires one ready initial transaction",
                        )
                    if (
                        transaction["planning_identity"] != planning_identity
                        or transaction["final_source_identity"] != source_identity
                        or payload.get("baselineSourceIdentity") != transaction["baseline_source_identity"]
                        or payload.get("baselineCapsuleRef") != transaction["baseline_capsule_ref"]
                        or payload.get("implementationDeltaRef") != transaction["implementation_delta_ref"]
                    ):
                        raise WorkflowStoreError(
                            "IMPLEMENTATION_TRANSACTION_MISMATCH",
                            "handoff facts differ from the ready transaction",
                        )
                if validate_currentness is not None:
                    validate_currentness()
                connection.execute(
                    """
                    INSERT INTO nodes(
                        node_ref, node_kind, protocol_version, root_ref, planning_identity,
                        source_identity, verification_status, payload_json, payload_sha256, created_at
                    ) VALUES (?, 'IMPLEMENTATION_HANDOFF', ?, ?, ?, ?, NULL, ?, ?, ?)
                    """,
                    (
                        node_ref,
                        protocol_version,
                        node_ref,
                        planning_identity,
                        source_identity,
                        encoded,
                        hashlib.sha256(encoded).hexdigest(),
                        created_at,
                    ),
                )
                row = connection.execute("SELECT * FROM nodes WHERE node_ref = ?", (node_ref,)).fetchone()
                assert row is not None
                view = self._node_view(row)
                if transaction is not None:
                    connection.execute(
                        """
                        UPDATE implementation_transactions
                        SET state = 'CLOSED_WITH_HANDOFF', closed_at = ?
                        WHERE transaction_ref = ? AND state = 'READY_FOR_HANDOFF'
                        """,
                        (created_at, implementation_transaction_ref),
                    )
                    event_payload = canonical_json({"implementationHandoffRef": node_ref})
                    connection.execute(
                        """
                        INSERT INTO implementation_events(
                            transaction_ref, event_kind, payload_json, payload_sha256, created_at
                        ) VALUES (?, 'HANDOFF_PUBLISHED', ?, ?, ?)
                        """,
                        (
                            implementation_transaction_ref,
                            event_payload,
                            hashlib.sha256(event_payload).hexdigest(),
                            created_at,
                        ),
                    )
        except sqlite3.IntegrityError as exc:
            raise WorkflowStoreError("IMMUTABLE_NODE_EXISTS", f"refusing duplicate node: {node_ref}") from exc
        return view

    def read_node(self, node_ref: str) -> dict[str, Any]:
        connection = self._connect()
        try:
            row = connection.execute("SELECT * FROM nodes WHERE node_ref = ?", (node_ref,)).fetchone()
            if row is None:
                raise WorkflowStoreError("NODE_NOT_FOUND", f"unknown node: {node_ref}")
            return self._node_view(row)
        finally:
            connection.close()

    @staticmethod
    def _current_tip_locked(connection: sqlite3.Connection, root_ref: str) -> sqlite3.Row:
        current = connection.execute("SELECT * FROM nodes WHERE node_ref = ?", (root_ref,)).fetchone()
        if current is None or current["root_ref"] != root_ref:
            raise WorkflowStoreError("ROOT_NOT_FOUND", f"unknown workflow root: {root_ref}")
        seen: set[str] = set()
        for _ in range(MAX_LINEAGE_NODES):
            current_ref = str(current["node_ref"])
            if current_ref in seen:
                raise WorkflowStoreError("STORE_CORRUPT", "workflow continuation contains a cycle")
            seen.add(current_ref)
            edge = connection.execute(
                "SELECT successor_ref FROM edges WHERE predecessor_ref = ?", (current_ref,)
            ).fetchone()
            if edge is None:
                return current
            current = connection.execute(
                "SELECT * FROM nodes WHERE node_ref = ?", (edge["successor_ref"],)
            ).fetchone()
            if current is None or current["root_ref"] != root_ref:
                raise WorkflowStoreError("STORE_CORRUPT", "workflow edge points outside its root")
        raise WorkflowStoreError("STORE_CORRUPT", "workflow lineage exceeds its bounded maximum")

    def current_tip(self, root_ref: str) -> dict[str, Any]:
        connection = self._connect()
        try:
            return self._node_view(self._current_tip_locked(connection, root_ref))
        finally:
            connection.close()

    def lineage(self, root_ref: str) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            current = connection.execute("SELECT * FROM nodes WHERE node_ref = ?", (root_ref,)).fetchone()
            if current is None or current["root_ref"] != root_ref:
                raise WorkflowStoreError("ROOT_NOT_FOUND", f"unknown workflow root: {root_ref}")
            result: list[dict[str, Any]] = []
            seen: set[str] = set()
            for _ in range(MAX_LINEAGE_NODES):
                current_ref = str(current["node_ref"])
                if current_ref in seen:
                    raise WorkflowStoreError("STORE_CORRUPT", "workflow continuation contains a cycle")
                seen.add(current_ref)
                result.append(self._node_view(current))
                edge = connection.execute(
                    "SELECT successor_ref FROM edges WHERE predecessor_ref = ?", (current_ref,)
                ).fetchone()
                if edge is None:
                    return result
                current = connection.execute(
                    "SELECT * FROM nodes WHERE node_ref = ?", (edge["successor_ref"],)
                ).fetchone()
                if current is None or current["root_ref"] != root_ref:
                    raise WorkflowStoreError("STORE_CORRUPT", "workflow edge points outside its root")
            raise WorkflowStoreError("STORE_CORRUPT", "workflow lineage exceeds its bounded maximum")
        finally:
            connection.close()

    def start_invocation(
        self,
        *,
        root_ref: str,
        elapsed_seconds: int,
        limits: Mapping[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, int) or elapsed_seconds <= 0:
            raise WorkflowStoreError("MALFORMED_BUDGET", "elapsedSeconds must be a positive integer")
        normalized_limits = _budget_vector(limits, "limits")
        if normalized_limits["closureOperations"] <= 0:
            raise WorkflowStoreError("MALFORMED_BUDGET", "invocation must include finite closure capacity")
        invocation_ref = allocate_ref("INVOCATION")
        observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        deadline = observed + timedelta(seconds=elapsed_seconds)
        capability = f"cap:v1:{secrets.token_hex(32)}"
        actor_ref = f"actor:v1:coordinator:{uuid.uuid4().hex}"
        with self._transaction() as connection:
            root = connection.execute("SELECT node_ref FROM nodes WHERE node_ref = ?", (root_ref,)).fetchone()
            if root is None:
                raise WorkflowStoreError("ROOT_NOT_FOUND", f"unknown workflow root: {root_ref}")
            connection.execute(
                """
                INSERT INTO invocations(
                    invocation_ref, root_ref, deadline_at, limits_json, consumed_json,
                    state, created_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, NULL)
                """,
                (
                    invocation_ref,
                    root_ref,
                    deadline.isoformat(),
                    canonical_json(normalized_limits),
                    canonical_json(_zero_budget()),
                    observed.isoformat(),
                ),
            )
            connection.execute(
                """
                INSERT INTO actors(
                    actor_ref, role, root_ref, invocation_ref, capability_sha256,
                    bound_claim_ref, created_at
                ) VALUES (?, 'COORDINATOR', ?, ?, ?, NULL, ?)
                """,
                (
                    actor_ref,
                    root_ref,
                    invocation_ref,
                    _capability_digest(capability),
                    observed.isoformat(),
                ),
            )
        return {
            "invocationRef": invocation_ref,
            "rootRef": root_ref,
            "deadlineAt": deadline.isoformat(),
            "limits": normalized_limits,
            "coordinator": {
                "actorRef": actor_ref,
                "role": "COORDINATOR",
                "capability": capability,
            },
        }

    def issue_actor(self, *, coordinator_capability: str, role: str) -> dict[str, str]:
        if role not in ACTOR_ROLES - {"COORDINATOR"}:
            raise WorkflowStoreError("INVALID_ROLE", f"unsupported delegated actor role: {role}")
        role_segment = role.lower()
        actor_ref = f"actor:v1:{role_segment}:{uuid.uuid4().hex}"
        capability = f"cap:v1:{secrets.token_hex(32)}"
        with self._transaction() as connection:
            coordinator = self._actor_for_capability_locked(
                connection, coordinator_capability, expected_role="COORDINATOR"
            )
            invocation = connection.execute(
                "SELECT state FROM invocations WHERE invocation_ref = ?", (coordinator["invocation_ref"],)
            ).fetchone()
            if invocation is None or invocation["state"] != "ACTIVE":
                raise WorkflowStoreError("INVOCATION_NOT_ACTIVE", "cannot issue an actor for a closed invocation")
            connection.execute(
                """
                INSERT INTO actors(
                    actor_ref, role, root_ref, invocation_ref, capability_sha256,
                    bound_claim_ref, created_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    actor_ref,
                    role,
                    coordinator["root_ref"],
                    coordinator["invocation_ref"],
                    _capability_digest(capability),
                    utc_now(),
                ),
            )
        return {"actorRef": actor_ref, "role": role, "capability": capability}

    def issue_authorization(
        self, *, coordinator_capability: str, scope_sha256: str
    ) -> dict[str, str]:
        if not SHA256_PATTERN.fullmatch(scope_sha256):
            raise WorkflowStoreError("MALFORMED_AUTHORIZATION", "authorization scope digest is malformed")
        authorization_ref = f"authorization:v1:{uuid.uuid4().hex}"
        created_at = utc_now()
        with self._transaction() as connection:
            coordinator = self._actor_for_capability_locked(
                connection, coordinator_capability, expected_role="COORDINATOR"
            )
            invocation = connection.execute(
                "SELECT state FROM invocations WHERE invocation_ref = ?",
                (coordinator["invocation_ref"],),
            ).fetchone()
            if invocation is None or invocation["state"] != "ACTIVE":
                raise WorkflowStoreError("INVOCATION_NOT_ACTIVE", "authorization invocation is not active")
            connection.execute(
                """
                INSERT INTO authorizations(authorization_ref, invocation_ref, scope_sha256, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (authorization_ref, coordinator["invocation_ref"], scope_sha256, created_at),
            )
        return {
            "authorizationRef": authorization_ref,
            "invocationRef": coordinator["invocation_ref"],
            "scopeSha256": scope_sha256,
            "createdAt": created_at,
        }

    @staticmethod
    def _actor_for_capability_locked(
        connection: sqlite3.Connection, capability: str, *, expected_role: str | None = None
    ) -> sqlite3.Row:
        digest = _capability_digest(capability)
        row = connection.execute("SELECT * FROM actors WHERE capability_sha256 = ?", (digest,)).fetchone()
        if row is None:
            raise WorkflowStoreError("INVALID_CAPABILITY", "capability is unknown")
        if expected_role is not None and row["role"] != expected_role:
            raise WorkflowStoreError(
                "ROLE_CAPABILITY_MISMATCH", f"operation requires {expected_role}, not {row['role']}"
            )
        return row

    @staticmethod
    def _stored_budget(value: Any, locator: str) -> dict[str, int]:
        try:
            decoded = json.loads(bytes(value))
        except (TypeError, json.JSONDecodeError) as exc:
            raise WorkflowStoreError("STORE_CORRUPT", f"{locator} is unreadable") from exc
        try:
            return _budget_vector(decoded, locator)
        except WorkflowStoreError as exc:
            raise WorkflowStoreError("STORE_CORRUPT", exc.message) from exc

    @staticmethod
    def _assert_invocation_spend_open_locked(
        connection: sqlite3.Connection,
        invocation_ref: str,
        *,
        now: datetime | None = None,
    ) -> None:
        """Reject a new spend unit after the finite invocation deadline.

        Closure deliberately does not use this guard: already-started work keeps
        its reserved containment and publication capacity after elapsed-time
        exhaustion.
        """
        invocation = connection.execute(
            "SELECT state, deadline_at FROM invocations WHERE invocation_ref = ?",
            (invocation_ref,),
        ).fetchone()
        if invocation is None or invocation["state"] != "ACTIVE":
            raise WorkflowStoreError("INVOCATION_NOT_ACTIVE", "invocation is not active")
        observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if observed >= _parse_time(invocation["deadline_at"], "invocation.deadlineAt"):
            raise WorkflowStoreError(
                "BUDGET_EXHAUSTED", "invocation elapsed-time budget is exhausted"
            )

    def reserve_budget(
        self,
        *,
        coordinator_capability: str,
        transition_kind: str,
        spend: Mapping[str, Any],
        closure_reserve: Mapping[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if transition_kind not in TRANSITION_KINDS:
            raise WorkflowStoreError("INVALID_TRANSITION", f"unsupported transition: {transition_kind}")
        normalized_spend = _budget_vector(spend, "spend")
        normalized_closure = _budget_vector(closure_reserve, "closureReserve", require_closure=True)
        reservation_ref = f"budget:reservation:v1:{uuid.uuid4().hex}"
        observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._transaction() as connection:
            coordinator = self._actor_for_capability_locked(
                connection, coordinator_capability, expected_role="COORDINATOR"
            )
            invocation = connection.execute(
                "SELECT * FROM invocations WHERE invocation_ref = ?", (coordinator["invocation_ref"],)
            ).fetchone()
            if invocation is None or invocation["state"] != "ACTIVE":
                raise WorkflowStoreError("INVOCATION_NOT_ACTIVE", "invocation is not active")
            if observed >= _parse_time(invocation["deadline_at"], "invocation.deadlineAt"):
                raise WorkflowStoreError("BUDGET_EXHAUSTED", "invocation elapsed-time budget is exhausted")
            limits = self._stored_budget(invocation["limits_json"], "invocation.limits")
            consumed = self._stored_budget(invocation["consumed_json"], "invocation.consumed")
            active_total = _zero_budget()
            active_rows = connection.execute(
                """
                SELECT spend_reserved_json, closure_reserved_json
                FROM budget_reservations
                WHERE invocation_ref = ? AND state = 'ACTIVE'
                """,
                (coordinator["invocation_ref"],),
            ).fetchall()
            for index, row in enumerate(active_rows):
                active_total = _add_budget(
                    active_total,
                    self._stored_budget(row["spend_reserved_json"], f"reservation[{index}].spend"),
                    self._stored_budget(row["closure_reserved_json"], f"reservation[{index}].closure"),
                )
            requested = _add_budget(consumed, active_total, normalized_spend, normalized_closure)
            exhausted = [field for field in BUDGET_FIELDS if requested[field] > limits[field]]
            if exhausted:
                raise WorkflowStoreError(
                    "BUDGET_EXHAUSTED", f"insufficient invocation budget: {', '.join(exhausted)}"
                )
            connection.execute(
                """
                INSERT INTO budget_reservations(
                    reservation_ref, invocation_ref, transition_kind,
                    spend_reserved_json, closure_reserved_json,
                    spend_used_json, closure_used_json, state, created_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, NULL)
                """,
                (
                    reservation_ref,
                    coordinator["invocation_ref"],
                    transition_kind,
                    canonical_json(normalized_spend),
                    canonical_json(normalized_closure),
                    canonical_json(_zero_budget()),
                    canonical_json(_zero_budget()),
                    observed.isoformat(),
                ),
            )
        return {
            "reservationRef": reservation_ref,
            "invocationRef": coordinator["invocation_ref"],
            "transitionKind": transition_kind,
            "spendReserved": normalized_spend,
            "closureReserved": normalized_closure,
            "state": "ACTIVE",
        }

    def consume_budget(
        self,
        *,
        actor_capability: str,
        reservation_ref: str,
        category: str,
        amounts: Mapping[str, Any],
        now: datetime | None = None,
    ) -> dict[str, int]:
        if not BUDGET_REF_PATTERN.fullmatch(reservation_ref):
            raise WorkflowStoreError("MALFORMED_BUDGET", "reservation ref is malformed")
        if category not in {"SPEND", "CLOSURE"}:
            raise WorkflowStoreError("MALFORMED_BUDGET", "category must be SPEND or CLOSURE")
        normalized = _budget_vector(amounts, "amounts")
        reserved_column = "spend_reserved_json" if category == "SPEND" else "closure_reserved_json"
        used_column = "spend_used_json" if category == "SPEND" else "closure_used_json"
        with self._transaction() as connection:
            actor = self._actor_for_capability_locked(connection, actor_capability)
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?", (reservation_ref,)
            ).fetchone()
            if reservation is None or reservation["state"] != "ACTIVE":
                raise WorkflowStoreError("BUDGET_RESERVATION_NOT_ACTIVE", "reservation is absent or closed")
            if actor["invocation_ref"] != reservation["invocation_ref"]:
                raise WorkflowStoreError("ACTOR_CONTEXT_MISMATCH", "actor and reservation invocations differ")
            claim = connection.execute(
                "SELECT claimant_actor_ref FROM claims WHERE budget_reservation_ref = ?",
                (reservation_ref,),
            ).fetchone()
            if claim is None:
                raise WorkflowStoreError(
                    "BUDGET_RESERVATION_NOT_BOUND",
                    "spend or closure consumption requires a claim-bound reservation",
                )
            if claim["claimant_actor_ref"] != actor["actor_ref"]:
                raise WorkflowStoreError(
                    "CLAIM_ACTOR_MISMATCH", "only the claim owner may consume its reservation"
                )
            if category == "SPEND":
                self._assert_invocation_spend_open_locked(
                    connection,
                    reservation["invocation_ref"],
                    now=now,
                )
            reserved = self._stored_budget(reservation[reserved_column], f"reservation.{category}.reserved")
            used = self._stored_budget(reservation[used_column], f"reservation.{category}.used")
            next_used = _add_budget(used, normalized)
            exceeded = [field for field in BUDGET_FIELDS if next_used[field] > reserved[field]]
            if exceeded:
                raise WorkflowStoreError(
                    "BUDGET_RESERVATION_EXCEEDED", f"reservation exceeded: {', '.join(exceeded)}"
                )
            connection.execute(
                f"UPDATE budget_reservations SET {used_column} = ? WHERE reservation_ref = ?",
                (canonical_json(next_used), reservation_ref),
            )
        return next_used

    def ensure_claim_closure_budget(
        self,
        *,
        claimant_capability: str,
        claim_ref: str,
        amounts: Mapping[str, Any],
    ) -> dict[str, int]:
        """Record a claim's single result-closure charge without double spending on retry.

        A claim can publish at most one successor.  Closure work may finish before
        successor publication, so a process interruption between those operations
        must not make the still-active claim unpublishable.  This owner-store
        operation therefore consumes the requested closure vector exactly once for
        the claim: an already-recorded closure operation is returned unchanged.
        """
        if not CLAIM_REF_PATTERN.fullmatch(claim_ref):
            raise WorkflowStoreError("MALFORMED_CLAIM", "claim ref is malformed")
        normalized = _budget_vector(amounts, "amounts")
        if normalized["closureOperations"] != 1 or any(
            normalized[field] != 0 for field in BUDGET_FIELDS if field != "closureOperations"
        ):
            raise WorkflowStoreError(
                "MALFORMED_BUDGET",
                "claim result closure must consume exactly one closure operation",
            )
        with self._transaction() as connection:
            claimant = self._actor_for_capability_locked(connection, claimant_capability)
            claim = connection.execute(
                "SELECT * FROM claims WHERE claim_ref = ?", (claim_ref,)
            ).fetchone()
            if claim is None or claim["state"] != "ACTIVE":
                raise WorkflowStoreError("CLAIM_NOT_ACTIVE", "claim is absent or already closed")
            if claim["claimant_actor_ref"] != claimant["actor_ref"]:
                raise WorkflowStoreError("CLAIM_ACTOR_MISMATCH", "capability does not own this claim")
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                (claim["budget_reservation_ref"],),
            ).fetchone()
            if reservation is None or reservation["state"] != "ACTIVE":
                raise WorkflowStoreError(
                    "BUDGET_RESERVATION_NOT_ACTIVE", "claim budget reservation is absent or closed"
                )
            if reservation["invocation_ref"] != claimant["invocation_ref"]:
                raise WorkflowStoreError("ACTOR_CONTEXT_MISMATCH", "claim budget invocation differs")
            used = self._stored_budget(reservation["closure_used_json"], "reservation.CLOSURE.used")
            if used["closureOperations"] > 0:
                return used
            reserved = self._stored_budget(
                reservation["closure_reserved_json"], "reservation.CLOSURE.reserved"
            )
            next_used = _add_budget(used, normalized)
            exceeded = [field for field in BUDGET_FIELDS if next_used[field] > reserved[field]]
            if exceeded:
                raise WorkflowStoreError(
                    "BUDGET_RESERVATION_EXCEEDED", f"reservation exceeded: {', '.join(exceeded)}"
                )
            connection.execute(
                "UPDATE budget_reservations SET closure_used_json = ? WHERE reservation_ref = ?",
                (canonical_json(next_used), reservation["reservation_ref"]),
            )
        return next_used

    def close_budget_reservation(
        self, *, actor_capability: str, reservation_ref: str
    ) -> dict[str, Any]:
        with self._transaction() as connection:
            actor = self._actor_for_capability_locked(
                connection, actor_capability, expected_role="COORDINATOR"
            )
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?", (reservation_ref,)
            ).fetchone()
            if reservation is None or reservation["state"] != "ACTIVE":
                raise WorkflowStoreError("BUDGET_RESERVATION_NOT_ACTIVE", "reservation is absent or closed")
            if actor["invocation_ref"] != reservation["invocation_ref"]:
                raise WorkflowStoreError("ACTOR_CONTEXT_MISMATCH", "actor and reservation invocations differ")
            active_claim = connection.execute(
                "SELECT claim_ref FROM claims WHERE budget_reservation_ref = ? AND state = 'ACTIVE'",
                (reservation_ref,),
            ).fetchone()
            if active_claim is not None:
                raise WorkflowStoreError(
                    "CLAIM_NOT_CLOSED", "a claim-bound reservation closes with claim consumption or safe release"
                )
            spend_used = self._stored_budget(reservation["spend_used_json"], "reservation.spendUsed")
            closure_used = self._stored_budget(reservation["closure_used_json"], "reservation.closureUsed")
            invocation = connection.execute(
                "SELECT consumed_json FROM invocations WHERE invocation_ref = ?",
                (reservation["invocation_ref"],),
            ).fetchone()
            if invocation is None:
                raise WorkflowStoreError("STORE_CORRUPT", "reservation invocation is absent")
            consumed = self._stored_budget(invocation["consumed_json"], "invocation.consumed")
            next_consumed = _add_budget(consumed, spend_used, closure_used)
            closed_at = utc_now()
            connection.execute(
                "UPDATE invocations SET consumed_json = ? WHERE invocation_ref = ?",
                (canonical_json(next_consumed), reservation["invocation_ref"]),
            )
            connection.execute(
                """
                UPDATE budget_reservations
                SET state = 'CLOSED', closed_at = ?
                WHERE reservation_ref = ? AND state = 'ACTIVE'
                """,
                (closed_at, reservation_ref),
            )
        return {"reservationRef": reservation_ref, "state": "CLOSED", "consumed": next_consumed}

    def acquire_claim(
        self,
        *,
        coordinator_capability: str,
        claimant_actor_ref: str,
        tip_ref: str,
        transition_kind: str,
        planning_identity: str,
        source_identity: str,
        execution_ref: str,
        budget_reservation_ref: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if transition_kind not in TRANSITION_KINDS:
            raise WorkflowStoreError("INVALID_TRANSITION", f"unsupported transition: {transition_kind}")
        if not EXECUTION_REF_PATTERN.fullmatch(execution_ref):
            raise WorkflowStoreError("MALFORMED_CLAIM", "execution ref is malformed")
        if not BUDGET_REF_PATTERN.fullmatch(budget_reservation_ref):
            raise WorkflowStoreError("MALFORMED_CLAIM", "budget reservation ref is malformed")
        expected_prefix = "verification:run" if transition_kind == "VERIFY" else "implementation:transaction"
        if not execution_ref.startswith(expected_prefix):
            raise WorkflowStoreError("MALFORMED_CLAIM", "execution ref does not match transition kind")
        expected_claimant_role = "ASSESSOR" if transition_kind == "VERIFY" else "REMEDIATOR"
        claim_ref = f"claim:v1:{uuid.uuid4().hex}"
        observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        created_at = observed.isoformat()
        try:
            with self._transaction() as connection:
                coordinator = self._actor_for_capability_locked(
                    connection, coordinator_capability, expected_role="COORDINATOR"
                )
                claimant = connection.execute(
                    "SELECT * FROM actors WHERE actor_ref = ?", (claimant_actor_ref,)
                ).fetchone()
                if claimant is None:
                    raise WorkflowStoreError("ACTOR_NOT_FOUND", f"unknown claimant: {claimant_actor_ref}")
                if claimant["role"] != expected_claimant_role:
                    raise WorkflowStoreError(
                        "ROLE_CAPABILITY_MISMATCH",
                        f"{transition_kind} requires {expected_claimant_role}, not {claimant['role']}",
                    )
                if claimant["bound_claim_ref"] is not None:
                    raise WorkflowStoreError("ACTOR_CONTEXT_REUSED", "claimant actor was already bound")
                if (
                    coordinator["root_ref"] != claimant["root_ref"]
                    or coordinator["invocation_ref"] != claimant["invocation_ref"]
                ):
                    raise WorkflowStoreError("ACTOR_CONTEXT_MISMATCH", "actors are not from one invocation")
                invocation = connection.execute(
                    "SELECT * FROM invocations WHERE invocation_ref = ?", (coordinator["invocation_ref"],)
                ).fetchone()
                if invocation is None or invocation["state"] != "ACTIVE":
                    raise WorkflowStoreError("INVOCATION_NOT_ACTIVE", "invocation is not active")
                if observed >= _parse_time(invocation["deadline_at"], "invocation.deadlineAt"):
                    raise WorkflowStoreError("BUDGET_EXHAUSTED", "invocation expired before claim acquisition")
                reservation = connection.execute(
                    "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                    (budget_reservation_ref,),
                ).fetchone()
                if (
                    reservation is None
                    or reservation["state"] != "ACTIVE"
                    or reservation["invocation_ref"] != coordinator["invocation_ref"]
                    or reservation["transition_kind"] != transition_kind
                ):
                    raise WorkflowStoreError(
                        "BUDGET_RESERVATION_MISMATCH",
                        "claim requires an active matching invocation reservation",
                    )
                tip = self._current_tip_locked(connection, str(coordinator["root_ref"]))
                if tip["node_ref"] != tip_ref:
                    raise WorkflowStoreError("STALE_WORKFLOW_TIP", "claim does not target the current workflow tip")
                if tip["planning_identity"] != planning_identity:
                    raise WorkflowStoreError("PLANNING_IDENTITY_MISMATCH", "claim planning identity differs")
                if tip["source_identity"] != source_identity:
                    raise WorkflowStoreError("SOURCE_IDENTITY_MISMATCH", "claim source identity differs")
                if transition_kind == "VERIFY":
                    allowed = tip["node_kind"] == "IMPLEMENTATION_HANDOFF" or (
                        tip["node_kind"] == "VERIFICATION_RESULT"
                        and tip["verification_status"] in {"INCOMPLETE", "BLOCKED"}
                    )
                else:
                    allowed = (
                        tip["node_kind"] == "VERIFICATION_RESULT"
                        and tip["verification_status"] == "VERIFICATION_FAILED"
                    )
                if not allowed:
                    raise WorkflowStoreError(
                        "TRANSITION_NOT_ALLOWED", f"{transition_kind} is not allowed from the current tip"
                    )
                connection.execute(
                    """
                    INSERT INTO claims(
                        claim_ref, root_ref, tip_ref, transition_kind, coordinator_actor_ref,
                        claimant_actor_ref, planning_identity, source_identity, execution_ref,
                        budget_reservation_ref, state, successor_ref, closure_ref, created_at, closed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', NULL, NULL, ?, NULL)
                    """,
                    (
                        claim_ref,
                        coordinator["root_ref"],
                        tip_ref,
                        transition_kind,
                        coordinator["actor_ref"],
                        claimant_actor_ref,
                        planning_identity,
                        source_identity,
                        execution_ref,
                        budget_reservation_ref,
                        created_at,
                    ),
                )
                connection.execute(
                    "UPDATE actors SET bound_claim_ref = ? WHERE actor_ref = ?",
                    (claim_ref, claimant_actor_ref),
                )
        except sqlite3.IntegrityError as exc:
            raise WorkflowStoreError("TRANSITION_CLAIM_CONFLICT", "workflow tip already has a claim") from exc
        return {
            "claimRef": claim_ref,
            "rootRef": coordinator["root_ref"],
            "tipRef": tip_ref,
            "transitionKind": transition_kind,
            "claimantActorRef": claimant_actor_ref,
            "executionRef": execution_ref,
            "budgetReservationRef": budget_reservation_ref,
            "state": "ACTIVE",
            "createdAt": created_at,
        }

    def active_claim(self, root_ref: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM claims WHERE root_ref = ? AND state = 'ACTIVE'", (root_ref,)
            ).fetchone()
            return None if row is None else dict(row)
        finally:
            connection.close()

    def release_unstarted_claim(
        self, *, claimant_capability: str, claim_ref: str
    ) -> dict[str, Any]:
        if not CLAIM_REF_PATTERN.fullmatch(claim_ref):
            raise WorkflowStoreError("MALFORMED_CLAIM", "claim ref is malformed")
        closed_at = utc_now()
        closure_ref = f"closure:unstarted:v1:{uuid.uuid4().hex}"
        with self._transaction() as connection:
            claimant = self._actor_for_capability_locked(connection, claimant_capability)
            claim = connection.execute("SELECT * FROM claims WHERE claim_ref = ?", (claim_ref,)).fetchone()
            if claim is None or claim["state"] != "ACTIVE":
                raise WorkflowStoreError("CLAIM_NOT_ACTIVE", "claim is absent or already closed")
            if claim["claimant_actor_ref"] != claimant["actor_ref"]:
                raise WorkflowStoreError("CLAIM_ACTOR_MISMATCH", "capability does not own this claim")
            verification_facts = connection.execute(
                "SELECT 1 FROM verification_runs WHERE run_ref = ? LIMIT 1", (claim["execution_ref"],)
            ).fetchone()
            implementation_facts = connection.execute(
                "SELECT 1 FROM implementation_transactions WHERE transaction_ref = ? LIMIT 1",
                (claim["execution_ref"],),
            ).fetchone()
            if verification_facts is not None or implementation_facts is not None:
                raise WorkflowStoreError(
                    "CLAIM_HAS_DURABLE_FACTS", "a started transition must close through its durable artifact"
                )
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                (claim["budget_reservation_ref"],),
            ).fetchone()
            if reservation is None or reservation["state"] != "ACTIVE":
                raise WorkflowStoreError("BUDGET_RESERVATION_NOT_ACTIVE", "claim reservation is not active")
            connection.execute(
                """
                UPDATE claims
                SET state = 'RELEASED', closure_ref = ?, closed_at = ?
                WHERE claim_ref = ? AND state = 'ACTIVE'
                """,
                (closure_ref, closed_at, claim_ref),
            )
            connection.execute(
                """
                UPDATE budget_reservations
                SET state = 'CLOSED', closed_at = ?
                WHERE reservation_ref = ? AND state = 'ACTIVE'
                """,
                (closed_at, reservation["reservation_ref"]),
            )
        return {"claimRef": claim_ref, "state": "RELEASED", "closureRef": closure_ref}

    def publish_successor(
        self,
        *,
        claimant_capability: str,
        claim_ref: str,
        node_ref: str,
        node_kind: str,
        protocol_version: str,
        planning_identity: str,
        source_identity: str,
        verification_status: str | None,
        payload: Mapping[str, Any],
        implementation_transaction_ref: str | None = None,
        verification_run_ref: str | None = None,
        validate_currentness: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        if not CLAIM_REF_PATTERN.fullmatch(claim_ref):
            raise WorkflowStoreError("MALFORMED_CLAIM", "claim ref is malformed")
        encoded = _validate_node_payload(
            node_ref=node_ref,
            node_kind=node_kind,
            protocol_version=protocol_version,
            planning_identity=planning_identity,
            source_identity=source_identity,
            verification_status=verification_status,
            payload=_mapping(payload, "payload"),
        )
        created_at = utc_now()
        try:
            with self._transaction() as connection:
                claimant = self._actor_for_capability_locked(connection, claimant_capability)
                claim = connection.execute("SELECT * FROM claims WHERE claim_ref = ?", (claim_ref,)).fetchone()
                if claim is None or claim["state"] != "ACTIVE":
                    raise WorkflowStoreError("CLAIM_NOT_ACTIVE", "claim is absent or already closed")
                if claim["claimant_actor_ref"] != claimant["actor_ref"]:
                    raise WorkflowStoreError("CLAIM_ACTOR_MISMATCH", "capability does not own this claim")
                expected_role = "ASSESSOR" if claim["transition_kind"] == "VERIFY" else "REMEDIATOR"
                if claimant["role"] != expected_role:
                    raise WorkflowStoreError("ROLE_CAPABILITY_MISMATCH", "claimant role differs")
                reservation = connection.execute(
                    "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                    (claim["budget_reservation_ref"],),
                ).fetchone()
                if reservation is None or reservation["state"] != "ACTIVE":
                    raise WorkflowStoreError(
                        "BUDGET_RESERVATION_NOT_ACTIVE", "claim budget reservation is absent or closed"
                    )
                if reservation["invocation_ref"] != claimant["invocation_ref"]:
                    raise WorkflowStoreError("ACTOR_CONTEXT_MISMATCH", "claim budget invocation differs")
                spend_used = self._stored_budget(reservation["spend_used_json"], "reservation.spendUsed")
                closure_used = self._stored_budget(reservation["closure_used_json"], "reservation.closureUsed")
                if closure_used["closureOperations"] <= 0:
                    raise WorkflowStoreError(
                        "CLOSURE_BUDGET_UNUSED", "successor publication requires recorded closure work"
                    )
                expected_kind = (
                    "VERIFICATION_RESULT" if claim["transition_kind"] == "VERIFY" else "IMPLEMENTATION_HANDOFF"
                )
                if node_kind != expected_kind:
                    raise WorkflowStoreError("INVALID_SUCCESSOR_KIND", "node kind does not match claim transition")
                implementation_transaction = None
                verification_run = None
                if claim["transition_kind"] == "REMEDIATE":
                    if verification_run_ref is not None:
                        raise WorkflowStoreError(
                            "VERIFICATION_RUN_MISMATCH",
                            "remediation successor cannot close a VerificationRun",
                        )
                    if implementation_transaction_ref != claim["execution_ref"]:
                        raise WorkflowStoreError(
                            "IMPLEMENTATION_TRANSACTION_NOT_READY",
                            "remediation successor must use the claim-bound transaction",
                        )
                    implementation_transaction = connection.execute(
                        "SELECT * FROM implementation_transactions WHERE transaction_ref = ?",
                        (implementation_transaction_ref,),
                    ).fetchone()
                    if (
                        implementation_transaction is None
                        or implementation_transaction["mode"] != "VERIFICATION_REMEDIATION"
                        or implementation_transaction["state"] != "READY_FOR_HANDOFF"
                        or implementation_transaction["claim_ref"] != claim_ref
                    ):
                        raise WorkflowStoreError(
                            "IMPLEMENTATION_TRANSACTION_NOT_READY",
                            "remediation implementation transaction is not ready",
                        )
                elif implementation_transaction_ref is not None:
                    raise WorkflowStoreError(
                        "IMPLEMENTATION_TRANSACTION_MISMATCH",
                        "verification result cannot close an implementation transaction",
                    )
                elif verification_run_ref is not None:
                    if verification_run_ref != claim["execution_ref"]:
                        raise WorkflowStoreError(
                            "VERIFICATION_RUN_MISMATCH", "result must use the claim-bound VerificationRun"
                        )
                    verification_run = connection.execute(
                        "SELECT * FROM verification_runs WHERE run_ref = ?", (verification_run_ref,)
                    ).fetchone()
                    if (
                        verification_run is None
                        or verification_run["state"] not in {"PREFLIGHT", "SEALED"}
                        or verification_run["claim_ref"] != claim_ref
                        or verification_run["assessor_actor_ref"] != claimant["actor_ref"]
                    ):
                        raise WorkflowStoreError("VERIFICATION_RUN_NOT_READY", "VerificationRun is not publishable")
                tip = self._current_tip_locked(connection, claim["root_ref"])
                if tip["node_ref"] != claim["tip_ref"]:
                    raise WorkflowStoreError("STALE_WORKFLOW_TIP", "claim no longer owns the current tip")
                if planning_identity != claim["planning_identity"] or planning_identity != tip["planning_identity"]:
                    raise WorkflowStoreError("PLANNING_IDENTITY_MISMATCH", "successor planning identity differs")

                if claim["transition_kind"] == "VERIFY":
                    if source_identity != claim["source_identity"] or source_identity != tip["source_identity"]:
                        raise WorkflowStoreError("SOURCE_IDENTITY_MISMATCH", "verification changed source identity")
                    expected_handoff = (
                        tip["node_ref"]
                        if tip["node_kind"] == "IMPLEMENTATION_HANDOFF"
                        else json.loads(bytes(tip["payload_json"]))["implementationHandoffRef"]
                    )
                    if payload.get("implementationHandoffRef") != expected_handoff:
                        raise WorkflowStoreError("HANDOFF_IDENTITY_MISMATCH", "result references another handoff")
                    if verification_run is not None:
                        if (
                            verification_run["implementation_handoff_ref"] != expected_handoff
                            or verification_run["planning_identity"] != planning_identity
                            or verification_run["source_identity"] != source_identity
                            or payload.get("verificationRunRef") != verification_run_ref
                            or payload.get("sealedPlanDigest") != verification_run["sealed_plan_sha256"]
                        ):
                            raise WorkflowStoreError(
                                "VERIFICATION_RUN_MISMATCH", "result facts differ from its VerificationRun"
                            )
                else:
                    assert implementation_transaction is not None
                    if (
                        implementation_transaction["planning_identity"] != planning_identity
                        or implementation_transaction["baseline_source_identity"] != tip["source_identity"]
                        or implementation_transaction["final_source_identity"] != source_identity
                        or payload.get("baselineCapsuleRef") != implementation_transaction["baseline_capsule_ref"]
                        or payload.get("implementationDeltaRef")
                        != implementation_transaction["implementation_delta_ref"]
                    ):
                        raise WorkflowStoreError(
                            "IMPLEMENTATION_TRANSACTION_MISMATCH",
                            "remediation handoff facts differ from its transaction",
                        )
                    if payload.get("baselineSourceIdentity") != tip["source_identity"]:
                        raise WorkflowStoreError("SOURCE_IDENTITY_MISMATCH", "remediation baseline differs")
                    if source_identity == tip["source_identity"]:
                        raise WorkflowStoreError("EMPTY_REMEDIATION_DELTA", "remediation must create a new identity")
                    ancestor = connection.execute(
                        "SELECT 1 FROM nodes WHERE root_ref = ? AND source_identity = ? LIMIT 1",
                        (claim["root_ref"], source_identity),
                    ).fetchone()
                    if ancestor is not None:
                        raise WorkflowStoreError("ANCESTOR_SOURCE_REUSED", "remediation reused an ancestor identity")

                if validate_currentness is not None:
                    validate_currentness()

                connection.execute(
                    """
                    INSERT INTO nodes(
                        node_ref, node_kind, protocol_version, root_ref, planning_identity,
                        source_identity, verification_status, payload_json, payload_sha256, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        node_ref,
                        node_kind,
                        protocol_version,
                        claim["root_ref"],
                        planning_identity,
                        source_identity,
                        verification_status,
                        encoded,
                        hashlib.sha256(encoded).hexdigest(),
                        created_at,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO edges(predecessor_ref, successor_ref, transition_kind, claim_ref, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (claim["tip_ref"], node_ref, claim["transition_kind"], claim_ref, created_at),
                )
                connection.execute(
                    """
                    UPDATE claims
                    SET state = 'CONSUMED', successor_ref = ?, closed_at = ?
                    WHERE claim_ref = ? AND state = 'ACTIVE'
                    """,
                    (node_ref, created_at, claim_ref),
                )
                invocation = connection.execute(
                    "SELECT consumed_json FROM invocations WHERE invocation_ref = ?",
                    (reservation["invocation_ref"],),
                ).fetchone()
                if invocation is None:
                    raise WorkflowStoreError("STORE_CORRUPT", "claim invocation is absent")
                consumed = self._stored_budget(invocation["consumed_json"], "invocation.consumed")
                next_consumed = _add_budget(consumed, spend_used, closure_used)
                connection.execute(
                    "UPDATE invocations SET consumed_json = ? WHERE invocation_ref = ?",
                    (canonical_json(next_consumed), reservation["invocation_ref"]),
                )
                connection.execute(
                    """
                    UPDATE budget_reservations
                    SET state = 'CLOSED', closed_at = ?
                    WHERE reservation_ref = ? AND state = 'ACTIVE'
                    """,
                    (created_at, reservation["reservation_ref"]),
                )
                if implementation_transaction is not None:
                    connection.execute(
                        """
                        UPDATE implementation_transactions
                        SET state = 'CLOSED_WITH_HANDOFF', closed_at = ?
                        WHERE transaction_ref = ? AND state = 'READY_FOR_HANDOFF'
                        """,
                        (created_at, implementation_transaction_ref),
                    )
                    event_payload = canonical_json({"implementationHandoffRef": node_ref})
                    connection.execute(
                        """
                        INSERT INTO implementation_events(
                            transaction_ref, event_kind, payload_json, payload_sha256, created_at
                        ) VALUES (?, 'HANDOFF_PUBLISHED', ?, ?, ?)
                        """,
                        (
                            implementation_transaction_ref,
                            event_payload,
                            hashlib.sha256(event_payload).hexdigest(),
                            created_at,
                        ),
                    )
                if verification_run is not None:
                    closure_payload = canonical_json(
                        {
                            "verificationResultRef": node_ref,
                            "verificationStatus": verification_status,
                            "completedAt": created_at,
                        }
                    )
                    connection.execute(
                        """
                        UPDATE verification_runs
                        SET state = 'CLOSED', closure_json = ?, closed_at = ?
                        WHERE run_ref = ? AND state IN ('PREFLIGHT', 'SEALED')
                        """,
                        (closure_payload, created_at, verification_run_ref),
                    )
                    event_payload = canonical_json({"verificationResultRef": node_ref})
                    connection.execute(
                        """
                        INSERT INTO verification_events(
                            run_ref, event_kind, payload_json, payload_sha256, created_at
                        ) VALUES (?, 'RESULT_PUBLISHED', ?, ?, ?)
                        """,
                        (
                            verification_run_ref,
                            event_payload,
                            hashlib.sha256(event_payload).hexdigest(),
                            created_at,
                        ),
                    )
                row = connection.execute("SELECT * FROM nodes WHERE node_ref = ?", (node_ref,)).fetchone()
                assert row is not None
                view = self._node_view(row)
        except sqlite3.IntegrityError as exc:
            raise WorkflowStoreError("ATOMIC_CONTINUATION_CONFLICT", "successor publication conflicted") from exc
        return view

    def database_mode(self) -> int:
        return stat.S_IMODE(self.database_path.stat().st_mode)


__all__ = [
    "ACTOR_ROLES",
    "BUDGET_FIELDS",
    "DEFAULT_STORE_ROOT",
    "NODE_KINDS",
    "TRANSITION_KINDS",
    "VERIFICATION_STATUSES",
    "WorkflowStore",
    "WorkflowStoreError",
    "allocate_ref",
    "canonical_json",
]
