#!/usr/bin/env python3
"""Durable implementation/ownership transactions for initial work and remediation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import secrets
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


TOOLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workflow_store = _load_module(
    "implementation_workflow_store", TOOLS_ROOT / "workflow-store" / "workflow_store.py"
)
ownership_snapshot = _load_module(
    "implementation_ownership_snapshot",
    TOOLS_ROOT / "task-ownership-snapshot" / "ownership_snapshot.py",
)
baseline_capsule = _load_module(
    "implementation_transaction_baseline_capsule",
    REPOSITORY_ROOT / "baseline-capsule" / "baseline_capsule.py",
)


TRANSACTION_REF_PATTERN = re.compile(r"^implementation:transaction:v1:[a-f0-9]{32}$")
ENVELOPE_REF_PATTERN = re.compile(r"^implementation:envelope:v1:[a-f0-9]{32}$")
DELTA_REF_PATTERN = re.compile(r"^implementation:delta:v1:[a-f0-9]{32}$")
CHECK_REF_PATTERN = re.compile(r"^implementation:check:v1:[a-f0-9]{32}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SOURCE_IDENTITY_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
CAPABILITY_PATTERN = re.compile(r"^cap:v1:[a-f0-9]{64}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

MAX_PATH_PATTERNS = 256
MAX_CRITERIA = 128
MAX_COMMAND_PARTS = 256
MAX_OUTPUT_BYTES = 64 * 1024
MAX_TIMEOUT_SECONDS = 900

_DISPATCH_ENVELOPE_FIELDS = (
    "envelope_ref",
    "transaction_ref",
    "task_id",
    "criterion_refs_json",
    "allowed_paths_json",
    "forbidden_paths_json",
    "before_snapshot_json",
    "before_snapshot_sha256",
    "after_snapshot_json",
    "after_snapshot_sha256",
    "delta_json",
    "reconciliation_json",
    "state",
    "created_at",
    "closed_at",
)
_DISPATCH_TRANSACTION_FIELDS = (
    "transaction_ref",
    "mode",
    "root_ref",
    "claim_ref",
    "owner_actor_ref",
    "worker_actor_ref",
    "selected_worker",
    "worker_capability_sha256",
    "project_root",
    "planning_identity",
    "baseline_source_identity",
    "state",
)
_INVALIDATION_EVENT_FIELDS = {
    "envelopeRef",
    "oldIdentity",
    "newIdentity",
    "changedPaths",
    "workerAttributablePaths",
    "externalPaths",
    "preservedUserChanges",
}


class TransactionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TransactionError("MALFORMED_TRANSACTION", f"value is not JSON serializable: {exc}") from exc


def _capability_digest(capability: str) -> str:
    if not isinstance(capability, str) or not CAPABILITY_PATTERN.fullmatch(capability):
        raise TransactionError("INVALID_CAPABILITY", "transaction capability is malformed")
    return hashlib.sha256(capability.encode("ascii")).hexdigest()


def _mapping(value: Any, locator: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TransactionError("MALFORMED_TRANSACTION", f"{locator} must be an object")
    return value


def _strings(value: Any, locator: str, *, maximum: int = MAX_PATH_PATTERNS) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise TransactionError("MALFORMED_TRANSACTION", f"{locator} must be a bounded array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item or len(item.encode("utf-8")) > 4096:
            raise TransactionError("MALFORMED_TRANSACTION", f"{locator}[{index}] is invalid")
        result.append(item)
    if len(set(result)) != len(result):
        raise TransactionError("MALFORMED_TRANSACTION", f"{locator} contains duplicates")
    return result


def _criterion_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value or len(value) > MAX_CRITERIA:
        raise TransactionError("MALFORMED_TRANSACTION", "criterionRefs must be a non-empty bounded array")
    result: list[dict[str, Any]] = []
    seen: set[int] = set()
    for offset, raw in enumerate(value):
        item = _mapping(raw, f"criterionRefs[{offset}]")
        if set(item) != {"criterionIndex", "criterionRawSha256"}:
            raise TransactionError("MALFORMED_TRANSACTION", f"criterionRefs[{offset}] fields are invalid")
        index = item["criterionIndex"]
        digest = item["criterionRawSha256"]
        if isinstance(index, bool) or not isinstance(index, int) or index <= 0 or index in seen:
            raise TransactionError("MALFORMED_TRANSACTION", f"criterionRefs[{offset}] index is invalid")
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
            raise TransactionError("MALFORMED_TRANSACTION", f"criterionRefs[{offset}] digest is invalid")
        seen.add(index)
        result.append({"criterionIndex": index, "criterionRawSha256": digest})
    return result


def _decode_json(value: Any, locator: str) -> Any:
    try:
        return json.loads(bytes(value))
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransactionError("STORE_CORRUPT", f"{locator} is unreadable") from exc


def _stored_payload(value: Any, expected_digest: Any, locator: str) -> tuple[bytes, Any]:
    """Authenticate one stored JSON blob before decoding it."""
    try:
        encoded = bytes(value)
    except (TypeError, ValueError) as exc:
        raise TransactionError("STORE_CORRUPT", f"{locator} is not a byte payload") from exc
    if (
        not isinstance(expected_digest, str)
        or SHA256_PATTERN.fullmatch(expected_digest) is None
        or hashlib.sha256(encoded).hexdigest() != expected_digest
    ):
        raise TransactionError("STORE_CORRUPT", f"{locator} payload digest differs")
    try:
        return encoded, json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransactionError("STORE_CORRUPT", f"{locator} is unreadable") from exc


def _stored_snapshot(
    value: Any,
    expected_digest: Any,
    locator: str,
    *,
    expected_project_root: Path | str,
) -> tuple[bytes, dict[str, Any]]:
    encoded, decoded = _stored_payload(value, expected_digest, locator)
    try:
        validated = ownership_snapshot.validate_snapshot(
            decoded, expected_project_root=expected_project_root
        )
    except ownership_snapshot.SnapshotError as exc:
        raise TransactionError("STORE_CORRUPT", f"{locator} is invalid: {exc.message}") from exc
    return encoded, validated


def _stored_strings(value: Any, locator: str) -> list[str]:
    decoded = _decode_json(value, locator)
    try:
        return _strings(decoded, locator)
    except TransactionError as exc:
        raise TransactionError("STORE_CORRUPT", f"{locator} is invalid: {exc.message}") from exc


def _row_fingerprint(row: Any, fields: Sequence[str]) -> tuple[Any, ...]:
    return tuple(bytes(row[field]) if isinstance(row[field], memoryview) else row[field] for field in fields)


def _bounded_output(value: bytes) -> dict[str, Any]:
    truncated = len(value) > MAX_OUTPUT_BYTES
    bounded = value[:MAX_OUTPUT_BYTES]
    return {
        "sha256": hashlib.sha256(value).hexdigest(),
        "byteCount": len(value),
        "truncated": truncated,
        "text": bounded.decode("utf-8", errors="replace"),
    }


class ImplementationTransactionStore:
    def __init__(
        self,
        workflow_root: Path | str | None = None,
        capsule_root: Path | str | None = None,
        *,
        guard: Any | None = None,
        workflow: Any | None = None,
    ) -> None:
        if workflow is not None:
            if not isinstance(workflow, workflow_store.WorkflowStore):
                raise TransactionError(
                    "INVALID_WORKFLOW_STORE", "injected workflow is not an audited WorkflowStore"
                )
            if workflow_root is not None:
                try:
                    expected_root = Path(workflow_root).expanduser().resolve()
                except (OSError, RuntimeError) as exc:
                    raise TransactionError(
                        "INVALID_WORKFLOW_STORE", "workflow root cannot be canonicalized"
                    ) from exc
                if expected_root != workflow.store_root:
                    raise TransactionError(
                        "INVALID_WORKFLOW_STORE",
                        "injected workflow differs from the requested workflow root",
                    )
            self.workflow = workflow
        else:
            if guard is None:
                raise TransactionError(
                    "AUDIT_GUARD_REQUIRED",
                    "implementation transactions require a live audited-open guard session",
                )
            try:
                opened = workflow_store.audit_and_open_workflow_store(
                    workflow_root or workflow_store.DEFAULT_STORE_ROOT,
                    guard=guard,
                )
            except workflow_store.WorkflowStoreError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            self.workflow = opened.store
        self.capsules = baseline_capsule.CapsuleStore(
            capsule_root or os.environ.get("BASELINE_CAPSULE_STORE", baseline_capsule.DEFAULT_STORE_ROOT)
        )

    def _event_locked(
        self,
        connection,
        transaction_ref: str,
        event_kind: str,
        payload: Mapping[str, Any],
    ) -> None:
        encoded = _canonical_json(payload)
        connection.execute(
            """
            INSERT INTO implementation_events(
                transaction_ref, event_kind, payload_json, payload_sha256, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (transaction_ref, event_kind, encoded, hashlib.sha256(encoded).hexdigest(), _now()),
        )

    @staticmethod
    def _transaction_for_capability_locked(connection, capability: str):
        digest = _capability_digest(capability)
        row = connection.execute(
            "SELECT * FROM implementation_transactions WHERE capability_sha256 = ?", (digest,)
        ).fetchone()
        if row is None:
            raise TransactionError("INVALID_CAPABILITY", "transaction capability is unknown")
        return row

    def _remediation_dispatch_authority_locked(
        self,
        connection: sqlite3.Connection,
        transaction: Any,
        *,
        worker_digest: str,
    ) -> tuple[Any, ...] | None:
        """Validate and fingerprint the full claim-bound remediation authority chain.

        This intentionally does not enforce the invocation deadline or remaining
        Worker-call allowance. Those are spend gates and apply only after source
        currentness chooses the actual-dispatch branch.
        """
        if transaction["mode"] != "VERIFICATION_REMEDIATION":
            return None
        claim = connection.execute(
            "SELECT * FROM claims WHERE claim_ref = ?", (transaction["claim_ref"],)
        ).fetchone()
        if claim is None or claim["state"] != "ACTIVE":
            raise TransactionError(
                "REMEDIATION_CLAIM_MISMATCH", "remediation claim is not active"
            )
        if (
            claim["claim_ref"] != transaction["claim_ref"]
            or claim["root_ref"] != transaction["root_ref"]
            or claim["transition_kind"] != "REMEDIATE"
            or claim["execution_ref"] != transaction["transaction_ref"]
            or claim["claimant_actor_ref"] != transaction["owner_actor_ref"]
            or claim["planning_identity"] != transaction["planning_identity"]
            or claim["source_identity"] != transaction["baseline_source_identity"]
            or claim["successor_ref"] is not None
            or claim["closure_ref"] is not None
            or claim["closed_at"] is not None
        ):
            raise TransactionError(
                "REMEDIATION_CLAIM_MISMATCH",
                "remediation claim authority differs from its implementation transaction",
            )
        try:
            tip = self.workflow._current_tip_locked(connection, transaction["root_ref"])
        except workflow_store.WorkflowStoreError as exc:
            raise TransactionError(exc.code, exc.message) from exc
        if tip["node_ref"] != claim["tip_ref"]:
            raise TransactionError(
                "STALE_WORKFLOW_TIP", "remediation claim no longer targets the current tip"
            )

        owner = connection.execute(
            "SELECT * FROM actors WHERE actor_ref = ?", (transaction["owner_actor_ref"],)
        ).fetchone()
        worker = connection.execute(
            "SELECT * FROM actors WHERE actor_ref = ?", (transaction["worker_actor_ref"],)
        ).fetchone()
        coordinator = connection.execute(
            "SELECT * FROM actors WHERE actor_ref = ?", (claim["coordinator_actor_ref"],)
        ).fetchone()
        if (
            owner is None
            or worker is None
            or coordinator is None
            or owner["role"] != "REMEDIATOR"
            or worker["role"] != "WORKER"
            or coordinator["role"] != "COORDINATOR"
            or owner["bound_claim_ref"] != claim["claim_ref"]
            or worker["bound_claim_ref"] is not None
            or coordinator["bound_claim_ref"] is not None
            or transaction["selected_worker"] != worker["actor_ref"]
            or worker["capability_sha256"] != worker_digest
            or transaction["worker_capability_sha256"] != worker_digest
        ):
            raise TransactionError(
                "ACTOR_CONTEXT_MISMATCH",
                "remediation owner or selected Worker authority differs",
            )
        invocation_ref = owner["invocation_ref"]
        if any(
            actor["root_ref"] != transaction["root_ref"]
            or actor["invocation_ref"] != invocation_ref
            for actor in (owner, worker, coordinator)
        ):
            raise TransactionError(
                "ACTOR_CONTEXT_MISMATCH", "remediation actors are not in one root invocation"
            )

        reservation = connection.execute(
            "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
            (claim["budget_reservation_ref"],),
        ).fetchone()
        if (
            reservation is None
            or reservation["state"] != "ACTIVE"
            or reservation["reservation_ref"] != claim["budget_reservation_ref"]
            or reservation["transition_kind"] != "REMEDIATE"
            or reservation["invocation_ref"] != invocation_ref
            or reservation["closed_at"] is not None
        ):
            raise TransactionError(
                "BUDGET_RESERVATION_MISMATCH",
                "remediation claim has no active matching reservation",
            )
        invocation = connection.execute(
            "SELECT * FROM invocations WHERE invocation_ref = ?", (invocation_ref,)
        ).fetchone()
        if (
            invocation is None
            or invocation["state"] != "ACTIVE"
            or invocation["root_ref"] != transaction["root_ref"]
            or invocation["closed_at"] is not None
        ):
            raise TransactionError(
                "INVOCATION_NOT_ACTIVE", "remediation invocation is absent, closed, or mismatched"
            )
        try:
            self.workflow._stored_budget(
                reservation["spend_reserved_json"], "reservation.spendReserved"
            )
            self.workflow._stored_budget(
                reservation["closure_reserved_json"], "reservation.closureReserved"
            )
            self.workflow._stored_budget(
                reservation["spend_used_json"], "reservation.spendUsed"
            )
            self.workflow._stored_budget(
                reservation["closure_used_json"], "reservation.closureUsed"
            )
            self.workflow._stored_budget(invocation["limits_json"], "invocation.limits")
            self.workflow._stored_budget(
                invocation["consumed_json"], "invocation.consumed"
            )
        except workflow_store.WorkflowStoreError as exc:
            raise TransactionError(exc.code, exc.message) from exc
        return (
            _row_fingerprint(
                claim,
                (
                    "claim_ref",
                    "root_ref",
                    "tip_ref",
                    "transition_kind",
                    "coordinator_actor_ref",
                    "claimant_actor_ref",
                    "planning_identity",
                    "source_identity",
                    "execution_ref",
                    "budget_reservation_ref",
                    "state",
                ),
            ),
            _row_fingerprint(
                owner,
                (
                    "actor_ref",
                    "role",
                    "root_ref",
                    "invocation_ref",
                    "capability_sha256",
                    "bound_claim_ref",
                ),
            ),
            _row_fingerprint(
                worker,
                (
                    "actor_ref",
                    "role",
                    "root_ref",
                    "invocation_ref",
                    "capability_sha256",
                    "bound_claim_ref",
                ),
            ),
            _row_fingerprint(
                coordinator,
                (
                    "actor_ref",
                    "role",
                    "root_ref",
                    "invocation_ref",
                    "capability_sha256",
                    "bound_claim_ref",
                ),
            ),
            _row_fingerprint(
                reservation,
                (
                    "reservation_ref",
                    "invocation_ref",
                    "transition_kind",
                    "spend_reserved_json",
                    "closure_reserved_json",
                    "spend_used_json",
                    "closure_used_json",
                    "state",
                ),
            ),
            _row_fingerprint(
                invocation,
                (
                    "invocation_ref",
                    "root_ref",
                    "deadline_at",
                    "limits_json",
                    "consumed_json",
                    "state",
                    "closed_at",
                ),
            ),
        )

    def _dispatch_authority_locked(
        self,
        connection: sqlite3.Connection,
        *,
        envelope_ref: str,
        worker_digest: str,
    ) -> tuple[Any, Any, tuple[Any, ...] | None]:
        envelope = connection.execute(
            "SELECT * FROM implementation_envelopes WHERE envelope_ref = ?", (envelope_ref,)
        ).fetchone()
        if envelope is None or envelope["state"] != "FROZEN":
            raise TransactionError(
                "ENVELOPE_NOT_FROZEN", "envelope is absent or no longer frozen"
            )
        transaction = connection.execute(
            "SELECT * FROM implementation_transactions WHERE transaction_ref = ?",
            (envelope["transaction_ref"],),
        ).fetchone()
        if transaction is None:
            raise TransactionError("STORE_CORRUPT", "envelope transaction is absent")
        if transaction["state"] != "OPEN":
            raise TransactionError(
                "TRANSACTION_NOT_READY", "transaction is not exactly OPEN for Worker dispatch"
            )
        if transaction["worker_capability_sha256"] != worker_digest:
            raise TransactionError(
                "WORKER_CAPABILITY_MISMATCH", "only the selected Worker may begin this call"
            )
        authority = self._remediation_dispatch_authority_locked(
            connection, transaction, worker_digest=worker_digest
        )
        return envelope, transaction, authority

    @staticmethod
    def _project_root(raw: Path | str) -> Path:
        try:
            root = Path(raw).resolve(strict=True)
        except OSError as exc:
            raise TransactionError("INVALID_PROJECT_ROOT", f"cannot resolve project root: {exc}") from exc
        if not root.is_dir():
            raise TransactionError("INVALID_PROJECT_ROOT", "project root is not a directory")
        return root

    def _create_baseline(self, project_root: Path) -> dict[str, Any]:
        try:
            return self.capsules.create(project_root)
        except baseline_capsule.CapsuleError as exc:
            raise TransactionError(exc.code, exc.message) from exc

    def start_initial(
        self,
        *,
        project_root: Path | str,
        planning_identity: str,
        selected_worker: str,
    ) -> dict[str, Any]:
        root = self._project_root(project_root)
        if not isinstance(planning_identity, str) or not SHA256_PATTERN.fullmatch(planning_identity):
            raise TransactionError("MALFORMED_TRANSACTION", "planning identity is malformed")
        if not isinstance(selected_worker, str) or not selected_worker.strip():
            raise TransactionError("MALFORMED_TRANSACTION", "selected Worker is required")
        baseline = self._create_baseline(root)
        transaction_ref = workflow_store.allocate_ref("REMEDIATE")
        capability = f"cap:v1:{secrets.token_hex(32)}"
        worker_capability = f"cap:v1:{secrets.token_hex(32)}"
        created_at = _now()
        with self.workflow._transaction() as connection:
            connection.execute(
                """
                INSERT INTO implementation_transactions(
                    transaction_ref, mode, root_ref, claim_ref, owner_actor_ref, worker_actor_ref,
                    selected_worker, capability_sha256, worker_capability_sha256,
                    project_root, planning_identity, baseline_capsule_ref,
                    baseline_source_identity, admission_json, state, final_source_identity,
                    implementation_delta_ref, created_at, closed_at
                ) VALUES (?, 'INITIAL_IMPLEMENTATION', NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?, ?, ?, NULL,
                          'OPEN', NULL, NULL, ?, NULL)
                """,
                (
                    transaction_ref,
                    selected_worker.strip(),
                    _capability_digest(capability),
                    _capability_digest(worker_capability),
                    str(root),
                    planning_identity,
                    baseline["capsuleRef"],
                    baseline["baselineSourceIdentity"],
                    created_at,
                ),
            )
            self._event_locked(
                connection,
                transaction_ref,
                "TRANSACTION_STARTED",
                {
                    "mode": "INITIAL_IMPLEMENTATION",
                    "projectRoot": str(root),
                    "planningIdentity": planning_identity,
                    "baselineCapsuleRef": baseline["capsuleRef"],
                    "baselineSourceIdentity": baseline["baselineSourceIdentity"],
                    "selectedWorker": selected_worker.strip(),
                },
            )
        return {
            "transactionRef": transaction_ref,
            "mode": "INITIAL_IMPLEMENTATION",
            "transactionCapability": capability,
            "workerCapability": worker_capability,
            "projectRoot": str(root),
            "planningIdentity": planning_identity,
            "baselineCapsuleRef": baseline["capsuleRef"],
            "baselineSourceIdentity": baseline["baselineSourceIdentity"],
            "state": "OPEN",
        }

    @staticmethod
    def _remediation_admission(value: Any) -> dict[str, Any]:
        admission = _mapping(value, "admission")
        expected = {
            "disposition",
            "criterionRefs",
            "authorityDeltaDigest",
            "desiredOutcomeUnchanged",
            "acceptanceMeaningUnchanged",
            "scopeAndNonGoalsUnchanged",
            "materialProductDecisionRequired",
            "safetyAndOwnershipAuthorized",
        }
        if set(admission) != expected or admission.get("disposition") != "ADMITTED":
            raise TransactionError("REMEDIATION_NOT_ADMITTED", "remediation disposition is not ADMITTED")
        normalized = {
            "disposition": "ADMITTED",
            "criterionRefs": _criterion_refs(admission["criterionRefs"]),
            "authorityDeltaDigest": admission["authorityDeltaDigest"],
            "desiredOutcomeUnchanged": admission["desiredOutcomeUnchanged"],
            "acceptanceMeaningUnchanged": admission["acceptanceMeaningUnchanged"],
            "scopeAndNonGoalsUnchanged": admission["scopeAndNonGoalsUnchanged"],
            "materialProductDecisionRequired": admission["materialProductDecisionRequired"],
            "safetyAndOwnershipAuthorized": admission["safetyAndOwnershipAuthorized"],
        }
        if not isinstance(normalized["authorityDeltaDigest"], str) or not SHA256_PATTERN.fullmatch(
            normalized["authorityDeltaDigest"]
        ):
            raise TransactionError("REMEDIATION_NOT_ADMITTED", "authority delta digest is malformed")
        booleans = (
            "desiredOutcomeUnchanged",
            "acceptanceMeaningUnchanged",
            "scopeAndNonGoalsUnchanged",
            "materialProductDecisionRequired",
            "safetyAndOwnershipAuthorized",
        )
        if any(not isinstance(normalized[field], bool) for field in booleans):
            raise TransactionError("REMEDIATION_NOT_ADMITTED", "admission predicates must be boolean")
        if not (
            normalized["desiredOutcomeUnchanged"]
            and normalized["acceptanceMeaningUnchanged"]
            and normalized["scopeAndNonGoalsUnchanged"]
            and not normalized["materialProductDecisionRequired"]
            and normalized["safetyAndOwnershipAuthorized"]
        ):
            raise TransactionError("REMEDIATION_NOT_ADMITTED", "authority delta requires replanning or authorization")
        return normalized

    @staticmethod
    def _repeat_keys_for_failed_result(connection, result_row) -> set[str] | None:
        """Return mechanically exact contradiction keys, or None when unavailable."""

        try:
            payload = _decode_json(result_row["payload_json"], "verificationResult")
            run_ref = payload.get("verificationRunRef")
            criterion_results = payload.get("criterionResults")
            if not isinstance(run_ref, str) or not isinstance(criterion_results, list):
                return None
            run = connection.execute(
                "SELECT * FROM verification_runs WHERE run_ref = ? AND state = 'CLOSED'", (run_ref,)
            ).fetchone()
            if run is None or run["sealed_plan_json"] is None:
                return None
            sealed = bytes(run["sealed_plan_json"])
            if hashlib.sha256(sealed).hexdigest() != run["sealed_plan_sha256"]:
                raise TransactionError("STORE_CORRUPT", "repeat guard sealed plan digest differs")
            plan = json.loads(sealed)
            if not isinstance(plan, dict):
                return None
            contradicted = {
                (item.get("criterionIndex"), item.get("criterionRawSha256"))
                for item in criterion_results
                if isinstance(item, Mapping) and item.get("verdict") == "CONTRADICTED"
            }
            if not contradicted:
                return None
            criteria = {
                (item.get("criterionIndex"), item.get("criterionRawSha256")): item
                for item in plan.get("criteria", [])
                if isinstance(item, Mapping)
            }
            flows = {
                item.get("flowId"): item
                for item in plan.get("flows", [])
                if isinstance(item, Mapping) and isinstance(item.get("flowId"), str)
            }
            keys: set[str] = set()
            for identity in contradicted:
                criterion = criteria.get(identity)
                if not isinstance(criterion, Mapping) or not criterion.get("flowIds"):
                    return None
                flow_facts: list[dict[str, Any]] = []
                for flow_id in criterion["flowIds"]:
                    flow = flows.get(flow_id)
                    if not isinstance(flow, Mapping):
                        return None
                    step_facts: list[dict[str, Any]] = []
                    for step in flow.get("steps", []):
                        if not isinstance(step, Mapping):
                            return None
                        executor_version = step.get("executorVersion")
                        if executor_version != "process-v3":
                            # Retired, mixed, and unknown plans never receive a
                            # new-code exact-repeat interpretation.
                            return None
                        repeat_digest = step.get("repeatRequestDigest")
                        canonical_digest = step.get("canonicalRequestDigest")
                        identity_projection = step.get("executableIdentity")
                        if (
                            step.get("executorKind") != "PROCESS"
                            or step.get("environmentPolicy") != "SEALED_EMPTY_BASE_V1"
                            or not isinstance(repeat_digest, str)
                            or not SHA256_PATTERN.fullmatch(repeat_digest)
                            or not isinstance(canonical_digest, str)
                            or not SHA256_PATTERN.fullmatch(canonical_digest)
                            or not isinstance(identity_projection, Mapping)
                            or set(identity_projection)
                            != {
                                "canonicalPath",
                                "contentSha256",
                                "byteCount",
                                "executableMode",
                                "ownerUid",
                                "ownerGid",
                            }
                        ):
                            raise TransactionError(
                                "STORE_CORRUPT",
                                "process-v3 repeat request authority is malformed",
                            )
                        attempts = connection.execute(
                            """
                            SELECT * FROM verification_attempts
                            WHERE run_ref = ? AND flow_id = ? AND step_id = ?
                            ORDER BY attempt_id
                            """,
                            (run_ref, flow_id, step.get("stepId")),
                        ).fetchall()
                        if not attempts or any(
                            attempt["status"] in {"NOT_RUN", "ATTEMPT_RECORD_INCOMPLETE"}
                            for attempt in attempts
                        ):
                            return None
                        if any(
                            attempt["request_sha256"] != canonical_digest
                            for attempt in attempts
                        ):
                            raise TransactionError(
                                "STORE_CORRUPT",
                                "repeat guard attempt differs from the sealed request",
                            )
                        terminal = attempts[-1]
                        result = _decode_json(terminal["result_json"], "terminalAttempt")
                        if not isinstance(result, Mapping):
                            return None
                        stdout = result.get("stdout")
                        stderr = result.get("stderr")
                        if not isinstance(stdout, Mapping) or not isinstance(stderr, Mapping):
                            return None
                        terminal_fact = {
                            "status": terminal["status"],
                            "exitCode": result.get("exitCode"),
                            "errorCode": result.get("errorCode"),
                            "stdoutSha256": stdout.get("sha256"),
                            "stderrSha256": stderr.get("sha256"),
                        }
                        if not all(
                            value is None or isinstance(value, (str, int))
                            for value in terminal_fact.values()
                        ):
                            return None
                        step_facts.append(
                            {
                                "stepId": step.get("stepId"),
                                "role": step.get("role"),
                                "obligationRequestDigest": repeat_digest,
                                "terminalFact": terminal_fact,
                            }
                        )
                    flow_facts.append(
                        {
                            "flowId": flow_id,
                            "claimSha256": hashlib.sha256(
                                str(flow.get("claim", "")).encode("utf-8")
                            ).hexdigest(),
                            "expectedTerminalObservationSha256": hashlib.sha256(
                                str(flow.get("expectedTerminalObservation", "")).encode("utf-8")
                            ).hexdigest(),
                            "steps": step_facts,
                        }
                    )
                key = {
                    "criterionRawSha256": identity[1],
                    "flows": flow_facts,
                }
                keys.add(hashlib.sha256(_canonical_json(key)).hexdigest())
            return keys or None
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def _exact_repeat_disposition_locked(self, connection, current_result) -> str:
        current_keys = self._repeat_keys_for_failed_result(connection, current_result)
        if current_keys is None:
            return "UNAVAILABLE"
        predecessor = connection.execute(
            "SELECT predecessor_ref FROM edges WHERE successor_ref = ?",
            (current_result["node_ref"],),
        ).fetchone()
        comparable = False
        for _ in range(workflow_store.MAX_LINEAGE_NODES):
            if predecessor is None:
                break
            node = connection.execute(
                "SELECT * FROM nodes WHERE node_ref = ?", (predecessor["predecessor_ref"],)
            ).fetchone()
            if node is None:
                raise TransactionError("STORE_CORRUPT", "repeat guard lineage is broken")
            if node["node_kind"] == "VERIFICATION_RESULT" and node["verification_status"] == "VERIFICATION_FAILED":
                prior_keys = self._repeat_keys_for_failed_result(connection, node)
                if prior_keys is not None:
                    comparable = True
                    if current_keys.intersection(prior_keys):
                        return "MATCH"
            predecessor = connection.execute(
                "SELECT predecessor_ref FROM edges WHERE successor_ref = ?",
                (node["node_ref"],),
            ).fetchone()
        return "NO_MATCH" if comparable else "UNAVAILABLE"

    def start_remediation(
        self,
        *,
        remediator_capability: str,
        worker_capability: str,
        claim_ref: str,
        project_root: Path | str,
        admission: Mapping[str, Any],
    ) -> dict[str, Any]:
        root = self._project_root(project_root)
        normalized_admission = self._remediation_admission(admission)
        worker_digest = hashlib.sha256(worker_capability.encode("ascii")).hexdigest() if isinstance(worker_capability, str) else ""
        repeat_disposition = "UNAVAILABLE"
        with self.workflow._transaction() as connection:
            remediator = self.workflow._actor_for_capability_locked(
                connection, remediator_capability, expected_role="REMEDIATOR"
            )
            worker = self.workflow._actor_for_capability_locked(
                connection, worker_capability, expected_role="WORKER"
            )
            claim = connection.execute("SELECT * FROM claims WHERE claim_ref = ?", (claim_ref,)).fetchone()
            if (
                claim is None
                or claim["state"] != "ACTIVE"
                or claim["transition_kind"] != "REMEDIATE"
                or claim["claimant_actor_ref"] != remediator["actor_ref"]
            ):
                raise TransactionError("REMEDIATION_CLAIM_MISMATCH", "remediation claim is not active and owned")
            if worker["root_ref"] != claim["root_ref"] or worker["invocation_ref"] != remediator["invocation_ref"]:
                raise TransactionError("ACTOR_CONTEXT_MISMATCH", "selected Worker is outside the remediation invocation")
            reused_worker = connection.execute(
                "SELECT 1 FROM implementation_transactions WHERE worker_actor_ref = ? LIMIT 1",
                (worker["actor_ref"],),
            ).fetchone()
            if worker["bound_claim_ref"] is not None or reused_worker is not None:
                raise TransactionError("ACTOR_CONTEXT_REUSED", "selected Worker context was already used")
            if not TRANSACTION_REF_PATTERN.fullmatch(claim["execution_ref"]):
                raise TransactionError("REMEDIATION_CLAIM_MISMATCH", "claim transaction ref is malformed")
            tip = self.workflow._current_tip_locked(connection, claim["root_ref"])
            if tip["node_ref"] != claim["tip_ref"]:
                raise TransactionError("STALE_WORKFLOW_TIP", "remediation claim no longer owns the current tip")
            failed_payload = _decode_json(tip["payload_json"], "failedVerificationResult")
            raw_results = failed_payload.get("criterionResults")
            if not isinstance(raw_results, list):
                raise TransactionError(
                    "REMEDIATION_NOT_ADMITTED",
                    "failed result has no exact contradicted criterion evidence",
                )
            contradicted: set[tuple[int, str]] = set()
            for index, raw_result in enumerate(raw_results):
                result = _mapping(raw_result, f"criterionResults[{index}]")
                if result.get("verdict") != "CONTRADICTED":
                    continue
                criterion_index = result.get("criterionIndex")
                criterion_digest = result.get("criterionRawSha256")
                if (
                    isinstance(criterion_index, bool)
                    or not isinstance(criterion_index, int)
                    or criterion_index <= 0
                    or not isinstance(criterion_digest, str)
                    or not SHA256_PATTERN.fullmatch(criterion_digest)
                ):
                    raise TransactionError(
                        "REMEDIATION_NOT_ADMITTED", "failed result criterion evidence is malformed"
                    )
                contradicted.add((criterion_index, criterion_digest))
            admitted_refs = {
                (item["criterionIndex"], item["criterionRawSha256"])
                for item in normalized_admission["criterionRefs"]
            }
            if not contradicted or not admitted_refs.issubset(contradicted):
                raise TransactionError(
                    "REMEDIATION_NOT_ADMITTED",
                    "admission must reference only exact causally contradicted criteria",
                )
            repeat_disposition = self._exact_repeat_disposition_locked(connection, tip)
            try:
                current = baseline_capsule.capture_identity(root)["sourceIdentity"]
            except baseline_capsule.CapsuleError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            if current != claim["source_identity"]:
                raise TransactionError("SOURCE_IDENTITY_MISMATCH", "current source differs from failed result")
            selected_worker = worker["actor_ref"]
            transaction_ref = claim["execution_ref"]
            planning_identity = claim["planning_identity"]

        if repeat_disposition == "MATCH":
            try:
                self.workflow.release_unstarted_claim(
                    claimant_capability=remediator_capability,
                    claim_ref=claim_ref,
                )
            except workflow_store.WorkflowStoreError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            raise TransactionError(
                "EXACT_REPEAT_REMEDIATION_STOP",
                "structured contradiction key exactly matches an ancestor failure",
            )

        baseline = self._create_baseline(root)
        if baseline["baselineSourceIdentity"] != current:
            raise TransactionError("SOURCE_IDENTITY_MISMATCH", "source changed during remediation admission")
        capability = f"cap:v1:{secrets.token_hex(32)}"
        created_at = _now()
        with self.workflow._transaction() as connection:
            claim = connection.execute("SELECT * FROM claims WHERE claim_ref = ?", (claim_ref,)).fetchone()
            tip = self.workflow._current_tip_locked(connection, claim["root_ref"] if claim else "")
            if claim is None or claim["state"] != "ACTIVE" or tip["node_ref"] != claim["tip_ref"]:
                raise TransactionError("STALE_WORKFLOW_TIP", "remediation claim changed during baseline capture")
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                (claim["budget_reservation_ref"],),
            ).fetchone()
            if reservation is None or reservation["state"] != "ACTIVE":
                raise TransactionError("BUDGET_RESERVATION_NOT_ACTIVE", "remediation budget is not active")
            try:
                self.workflow._assert_invocation_spend_open_locked(
                    connection, reservation["invocation_ref"]
                )
            except workflow_store.WorkflowStoreError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            spend_reserved = self.workflow._stored_budget(
                reservation["spend_reserved_json"], "reservation.spendReserved"
            )
            spend_used = self.workflow._stored_budget(reservation["spend_used_json"], "reservation.spendUsed")
            if spend_used["remediationTransactions"] + 1 > spend_reserved["remediationTransactions"]:
                raise TransactionError("BUDGET_RESERVATION_EXCEEDED", "no remediation transaction budget remains")
            spend_used["remediationTransactions"] += 1
            connection.execute(
                "UPDATE budget_reservations SET spend_used_json = ? WHERE reservation_ref = ?",
                (_canonical_json(spend_used), reservation["reservation_ref"]),
            )
            connection.execute(
                """
                INSERT INTO implementation_transactions(
                    transaction_ref, mode, root_ref, claim_ref, owner_actor_ref, worker_actor_ref,
                    selected_worker, capability_sha256, worker_capability_sha256,
                    project_root, planning_identity, baseline_capsule_ref,
                    baseline_source_identity, admission_json, state, final_source_identity,
                    implementation_delta_ref, created_at, closed_at
                ) VALUES (?, 'VERIFICATION_REMEDIATION', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          'OPEN', NULL, NULL, ?, NULL)
                """,
                (
                    transaction_ref,
                    claim["root_ref"],
                    claim_ref,
                    claim["claimant_actor_ref"],
                    worker["actor_ref"],
                    selected_worker,
                    _capability_digest(capability),
                    worker_digest,
                    str(root),
                    planning_identity,
                    baseline["capsuleRef"],
                    baseline["baselineSourceIdentity"],
                    _canonical_json(normalized_admission),
                    created_at,
                ),
            )
            self._event_locked(
                connection,
                transaction_ref,
                "TRANSACTION_STARTED",
                {
                    "mode": "VERIFICATION_REMEDIATION",
                    "claimRef": claim_ref,
                    "baselineSourceIdentity": baseline["baselineSourceIdentity"],
                    "workerActorRef": worker["actor_ref"],
                    "admission": normalized_admission,
                    "exactRepeatDisposition": repeat_disposition,
                },
            )
        return {
            "transactionRef": transaction_ref,
            "mode": "VERIFICATION_REMEDIATION",
            "transactionCapability": capability,
            "workerActorRef": selected_worker,
            "projectRoot": str(root),
            "planningIdentity": planning_identity,
            "baselineCapsuleRef": baseline["capsuleRef"],
            "baselineSourceIdentity": baseline["baselineSourceIdentity"],
            "exactRepeatDisposition": repeat_disposition,
            "state": "OPEN",
        }

    def freeze_envelope(
        self,
        *,
        transaction_capability: str,
        task_id: str,
        criterion_refs: Sequence[Mapping[str, Any]],
        allowed_paths: Sequence[str],
        forbidden_paths: Sequence[str],
        exclusions: Sequence[str] = (),
    ) -> dict[str, Any]:
        if not isinstance(task_id, str) or not ID_PATTERN.fullmatch(task_id):
            raise TransactionError("MALFORMED_TRANSACTION", "taskId is invalid")
        criteria = _criterion_refs(list(criterion_refs))
        allowed = _strings(list(allowed_paths), "allowedPaths")
        forbidden = _strings(list(forbidden_paths), "forbiddenPaths")
        excluded = _strings(list(exclusions), "exclusions")
        if not allowed:
            raise TransactionError("MALFORMED_TRANSACTION", "a mutation envelope needs allowed paths")
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["state"] not in {"OPEN", "RECONCILING"}:
                raise TransactionError("TRANSACTION_NOT_READY", "transaction cannot freeze another envelope")
            active = connection.execute(
                """
                SELECT envelope_ref FROM implementation_envelopes
                WHERE transaction_ref = ? AND state != 'RECONCILED'
                """,
                (transaction["transaction_ref"],),
            ).fetchone()
            if active is not None:
                raise TransactionError("ENVELOPE_ALREADY_ACTIVE", "one envelope is already active")
            project_root = transaction["project_root"]

        try:
            before = ownership_snapshot.capture(project_root, exclusions=excluded)
            before = ownership_snapshot.validate_snapshot(
                before, expected_project_root=project_root
            )
        except (OSError, ownership_snapshot.SnapshotError) as exc:
            code = exc.code if isinstance(exc, ownership_snapshot.SnapshotError) else "SNAPSHOT_FAILED"
            raise TransactionError(code, str(exc)) from exc
        envelope_ref = f"implementation:envelope:v1:{uuid.uuid4().hex}"
        before_payload = _canonical_json(before)
        created_at = _now()
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["state"] not in {"OPEN", "RECONCILING"}:
                raise TransactionError("TRANSACTION_NOT_READY", "transaction changed during capture")
            active = connection.execute(
                """
                SELECT envelope_ref FROM implementation_envelopes
                WHERE transaction_ref = ? AND state != 'RECONCILED'
                """,
                (transaction["transaction_ref"],),
            ).fetchone()
            if active is not None:
                raise TransactionError(
                    "ENVELOPE_ALREADY_ACTIVE", "one envelope became active during snapshot capture"
                )
            try:
                connection.execute(
                    """
                    INSERT INTO implementation_envelopes(
                        envelope_ref, transaction_ref, task_id, criterion_refs_json,
                        allowed_paths_json, forbidden_paths_json, before_snapshot_json,
                        before_snapshot_sha256, after_snapshot_json, after_snapshot_sha256,
                        delta_json, reconciliation_json, state, created_at, closed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, 'FROZEN', ?, NULL)
                    """,
                    (
                        envelope_ref,
                        transaction["transaction_ref"],
                        task_id,
                        _canonical_json(criteria),
                        _canonical_json(allowed),
                        _canonical_json(forbidden),
                        before_payload,
                        hashlib.sha256(before_payload).hexdigest(),
                        created_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise TransactionError(
                    "ENVELOPE_ALREADY_ACTIVE",
                    "envelope insert conflicts with an active or legacy same-task envelope",
                ) from exc
            self._event_locked(
                connection,
                transaction["transaction_ref"],
                "ENVELOPE_FROZEN",
                {
                    "envelopeRef": envelope_ref,
                    "taskId": task_id,
                    "criterionRefs": criteria,
                    "allowedPaths": allowed,
                    "forbiddenPaths": forbidden,
                    "beforeIdentity": before["identity"],
                },
            )
        return {
            "envelopeRef": envelope_ref,
            "transactionRef": transaction["transaction_ref"],
            "taskId": task_id,
            "criterionRefs": criteria,
            "allowedPaths": allowed,
            "forbiddenPaths": forbidden,
            "beforeIdentity": before["identity"],
            "state": "FROZEN",
        }

    def begin_worker_call(self, *, worker_capability: str, envelope_ref: str) -> dict[str, Any]:
        worker_digest = _capability_digest(worker_capability)
        connection = self.workflow._connect()
        try:
            connection.execute("BEGIN")
            envelope, transaction, remediation_authority = self._dispatch_authority_locked(
                connection, envelope_ref=envelope_ref, worker_digest=worker_digest
            )
            before_raw, before = _stored_snapshot(
                envelope["before_snapshot_json"],
                envelope["before_snapshot_sha256"],
                "beforeSnapshot",
                expected_project_root=transaction["project_root"],
            )
            allowed = _stored_strings(envelope["allowed_paths_json"], "allowedPaths")
            envelope_fingerprint = _row_fingerprint(envelope, _DISPATCH_ENVELOPE_FIELDS)
            transaction_fingerprint = _row_fingerprint(
                transaction, _DISPATCH_TRANSACTION_FIELDS
            )
        finally:
            connection.rollback()
            connection.close()

        try:
            fresh = ownership_snapshot.capture(
                transaction["project_root"], exclusions=before["policy"]["exclusions"]
            )
            fresh = ownership_snapshot.validate_snapshot(
                fresh, expected_project_root=transaction["project_root"]
            )
            delta = ownership_snapshot.compare(
                before, fresh, allowed_mutation_scopes=allowed
            )
        except (OSError, ownership_snapshot.SnapshotError) as exc:
            code = exc.code if isinstance(exc, ownership_snapshot.SnapshotError) else "SNAPSHOT_FAILED"
            raise TransactionError(code, str(exc)) from exc

        invalidated = before["identity"] != fresh["identity"]
        after_payload = _canonical_json(fresh)
        delta_payload = _canonical_json(delta)
        changed_paths = list(delta["changedPaths"])
        reconciliation = {
            "disposition": "CONTINUE",
            "workerAttributablePaths": [],
            "externalPaths": changed_paths,
            "preservedUserChanges": changed_paths,
            "externalEffectState": "CLEAR",
        }
        with self.workflow._transaction() as connection:
            locked_envelope, locked_transaction, locked_authority = (
                self._dispatch_authority_locked(
                    connection,
                    envelope_ref=envelope_ref,
                    worker_digest=worker_digest,
                )
            )
            if (
                _row_fingerprint(locked_envelope, _DISPATCH_ENVELOPE_FIELDS)
                != envelope_fingerprint
                or _row_fingerprint(locked_transaction, _DISPATCH_TRANSACTION_FIELDS)
                != transaction_fingerprint
                or locked_authority != remediation_authority
            ):
                raise TransactionError(
                    "DISPATCH_STATE_CHANGED", "dispatch authority changed during source capture"
                )
            locked_raw, locked_before = _stored_snapshot(
                locked_envelope["before_snapshot_json"],
                locked_envelope["before_snapshot_sha256"],
                "beforeSnapshot",
                expected_project_root=locked_transaction["project_root"],
            )
            if locked_raw != before_raw or locked_before != before:
                raise TransactionError(
                    "DISPATCH_STATE_CHANGED", "stored before snapshot changed during recapture"
                )

            if invalidated:
                cursor = connection.execute(
                    """
                    UPDATE implementation_envelopes
                    SET after_snapshot_json = ?, after_snapshot_sha256 = ?, delta_json = ?,
                        reconciliation_json = ?, state = 'RECONCILED', closed_at = ?
                    WHERE envelope_ref = ? AND state = 'FROZEN'
                    """,
                    (
                        after_payload,
                        hashlib.sha256(after_payload).hexdigest(),
                        delta_payload,
                        _canonical_json(reconciliation),
                        _now(),
                        envelope_ref,
                    ),
                )
                if cursor.rowcount != 1:
                    raise TransactionError(
                        "DISPATCH_STATE_CHANGED", "frozen envelope changed before invalidation"
                    )
                self._event_locked(
                    connection,
                    locked_transaction["transaction_ref"],
                    "ENVELOPE_INVALIDATED_BEFORE_DISPATCH",
                    {
                        "envelopeRef": envelope_ref,
                        "oldIdentity": before["identity"],
                        "newIdentity": fresh["identity"],
                        "changedPaths": changed_paths,
                        "workerAttributablePaths": [],
                        "externalPaths": changed_paths,
                        "preservedUserChanges": changed_paths,
                    },
                )
            else:
                if locked_transaction["mode"] == "VERIFICATION_REMEDIATION":
                    claim = connection.execute(
                        "SELECT * FROM claims WHERE claim_ref = ?",
                        (locked_transaction["claim_ref"],),
                    ).fetchone()
                    reservation = connection.execute(
                        "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                        (claim["budget_reservation_ref"],),
                    ).fetchone()
                    try:
                        self.workflow._assert_invocation_spend_open_locked(
                            connection, reservation["invocation_ref"]
                        )
                        reserved = self.workflow._stored_budget(
                            reservation["spend_reserved_json"], "reservation.spendReserved"
                        )
                        used = self.workflow._stored_budget(
                            reservation["spend_used_json"], "reservation.spendUsed"
                        )
                    except workflow_store.WorkflowStoreError as exc:
                        raise TransactionError(exc.code, exc.message) from exc
                    if used["workerCalls"] + 1 > reserved["workerCalls"]:
                        raise TransactionError(
                            "BUDGET_RESERVATION_EXCEEDED", "no Worker-call budget remains"
                        )
                    used["workerCalls"] += 1
                    cursor = connection.execute(
                        """
                        UPDATE budget_reservations SET spend_used_json = ?
                        WHERE reservation_ref = ? AND state = 'ACTIVE'
                        """,
                        (_canonical_json(used), reservation["reservation_ref"]),
                    )
                    if cursor.rowcount != 1:
                        raise TransactionError(
                            "DISPATCH_STATE_CHANGED", "Worker-call reservation changed"
                        )
                cursor = connection.execute(
                    """
                    UPDATE implementation_envelopes SET state = 'DISPATCHED'
                    WHERE envelope_ref = ? AND state = 'FROZEN'
                    """,
                    (envelope_ref,),
                )
                if cursor.rowcount != 1:
                    raise TransactionError(
                        "DISPATCH_STATE_CHANGED", "frozen envelope changed before dispatch"
                    )
                cursor = connection.execute(
                    """
                    UPDATE implementation_transactions SET state = 'WORKER_ACTIVE'
                    WHERE transaction_ref = ? AND state = 'OPEN'
                    """,
                    (locked_transaction["transaction_ref"],),
                )
                if cursor.rowcount != 1:
                    raise TransactionError(
                        "DISPATCH_STATE_CHANGED", "transaction changed before dispatch"
                    )
                self._event_locked(
                    connection,
                    locked_transaction["transaction_ref"],
                    "WORKER_CALL_STARTED",
                    {
                        "envelopeRef": envelope_ref,
                        "selectedWorker": locked_transaction["selected_worker"],
                    },
                )
        if invalidated:
            raise TransactionError(
                "SOURCE_CHANGED_BEFORE_WORKER_DISPATCH",
                "source differs from the exact frozen envelope snapshot; no Worker call was authorized",
            )
        return {"envelopeRef": envelope_ref, "workerCallAuthorized": True}

    def run_check(
        self,
        *,
        transaction_capability: str,
        executable: str,
        argv: Sequence[str],
        cwd: Path | str,
        environment_delta: Mapping[str, str] | None = None,
        timeout_seconds: int = 120,
    ) -> dict[str, Any]:
        if not isinstance(executable, str) or not executable or os.path.sep in executable:
            raise TransactionError("MALFORMED_CHECK", "executable must be one PATH-resolved name")
        arguments = _strings(list(argv), "argv", maximum=MAX_COMMAND_PARTS)
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not (1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS):
            raise TransactionError("MALFORMED_CHECK", "timeout is outside the bounded range")
        env_delta = dict(environment_delta or {})
        if any(not isinstance(key, str) or not key or not isinstance(value, str) for key, value in env_delta.items()):
            raise TransactionError("MALFORMED_CHECK", "environment delta must contain string keys and values")
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["state"] != "WORKER_ACTIVE":
                raise TransactionError("TRANSACTION_NOT_READY", "checks run before after-snapshot capture")
            project_root = Path(transaction["project_root"])
            if transaction["mode"] == "VERIFICATION_REMEDIATION":
                claim = connection.execute(
                    "SELECT * FROM claims WHERE claim_ref = ?", (transaction["claim_ref"],)
                ).fetchone()
                if claim is None or claim["state"] != "ACTIVE":
                    raise TransactionError(
                        "REMEDIATION_CLAIM_MISMATCH", "remediation claim is not active"
                    )
                reservation = connection.execute(
                    "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                    (claim["budget_reservation_ref"],),
                ).fetchone()
                if reservation is None or reservation["state"] != "ACTIVE":
                    raise TransactionError(
                        "BUDGET_RESERVATION_NOT_ACTIVE", "remediation budget is not active"
                    )
                reserved = self.workflow._stored_budget(
                    reservation["spend_reserved_json"], "reservation.spendReserved"
                )
                used = self.workflow._stored_budget(
                    reservation["spend_used_json"], "reservation.spendUsed"
                )
                if used["toolCostUnits"] + 1 > reserved["toolCostUnits"]:
                    raise TransactionError(
                        "BUDGET_RESERVATION_EXCEEDED", "no implementation-check tool budget remains"
                    )
                used["toolCostUnits"] += 1
                connection.execute(
                    "UPDATE budget_reservations SET spend_used_json = ? WHERE reservation_ref = ?",
                    (_canonical_json(used), reservation["reservation_ref"]),
                )
        try:
            working_directory = Path(cwd).resolve(strict=True)
        except OSError as exc:
            raise TransactionError("MALFORMED_CHECK", f"cannot resolve cwd: {exc}") from exc
        if not working_directory.is_dir() or not (
            working_directory == project_root or working_directory.is_relative_to(project_root)
        ):
            raise TransactionError("MALFORMED_CHECK", "check cwd must be inside the project root")
        request = {
            "executable": executable,
            "argv": arguments,
            "cwd": str(working_directory),
            "environmentDelta": {
                key: {"valueSha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}
                for key, value in sorted(env_delta.items())
            },
            "timeoutSeconds": timeout_seconds,
        }
        started_at = _now()
        try:
            completed = subprocess.run(
                [executable, *arguments],
                cwd=working_directory,
                env={**os.environ, **env_delta},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
            result = {
                "status": "EXITED",
                "exitCode": completed.returncode,
                "stdout": _bounded_output(completed.stdout),
                "stderr": _bounded_output(completed.stderr),
                "startedAt": started_at,
                "completedAt": _now(),
            }
        except subprocess.TimeoutExpired as exc:
            result = {
                "status": "TIMED_OUT",
                "exitCode": None,
                "stdout": _bounded_output(exc.stdout or b""),
                "stderr": _bounded_output(exc.stderr or b""),
                "startedAt": started_at,
                "completedAt": _now(),
            }
        except OSError as exc:
            result = {
                "status": "TOOL_ERROR",
                "exitCode": None,
                "stdout": _bounded_output(b""),
                "stderr": _bounded_output(str(exc).encode("utf-8")),
                "startedAt": started_at,
                "completedAt": _now(),
            }
        check_ref = f"implementation:check:v1:{uuid.uuid4().hex}"
        request_payload = _canonical_json(request)
        result_payload = _canonical_json(result)
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["state"] != "WORKER_ACTIVE":
                raise TransactionError("TRANSACTION_NOT_READY", "transaction changed while check ran")
            connection.execute(
                """
                INSERT INTO implementation_checks(
                    check_ref, transaction_ref, request_json, request_sha256,
                    result_json, result_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check_ref,
                    transaction["transaction_ref"],
                    request_payload,
                    hashlib.sha256(request_payload).hexdigest(),
                    result_payload,
                    hashlib.sha256(result_payload).hexdigest(),
                    _now(),
                ),
            )
            self._event_locked(
                connection,
                transaction["transaction_ref"],
                "IMPLEMENTATION_CHECK_RECORDED",
                {"checkRef": check_ref, "requestSha256": hashlib.sha256(request_payload).hexdigest(), "result": result},
            )
        return {"checkRef": check_ref, "request": request, "result": result}

    def capture_after(
        self, *, transaction_capability: str, envelope_ref: str
    ) -> dict[str, Any]:
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            envelope = connection.execute(
                "SELECT * FROM implementation_envelopes WHERE envelope_ref = ? AND transaction_ref = ?",
                (envelope_ref, transaction["transaction_ref"]),
            ).fetchone()
            if envelope is None or envelope["state"] != "DISPATCHED":
                raise TransactionError("ENVELOPE_NOT_DISPATCHED", "envelope is absent or was not dispatched")
            before_raw, before = _stored_snapshot(
                envelope["before_snapshot_json"],
                envelope["before_snapshot_sha256"],
                "beforeSnapshot",
                expected_project_root=transaction["project_root"],
            )
            allowed = _stored_strings(envelope["allowed_paths_json"], "allowedPaths")
            exclusions = before["policy"]["exclusions"]
            project_root = transaction["project_root"]
        try:
            after = ownership_snapshot.capture(project_root, exclusions=exclusions)
            after = ownership_snapshot.validate_snapshot(
                after, expected_project_root=project_root
            )
            delta = ownership_snapshot.compare(before, after, allowed_mutation_scopes=allowed)
        except (OSError, ownership_snapshot.SnapshotError) as exc:
            code = exc.code if isinstance(exc, ownership_snapshot.SnapshotError) else "SNAPSHOT_FAILED"
            raise TransactionError(code, str(exc)) from exc
        after_payload = _canonical_json(after)
        delta_payload = _canonical_json(delta)
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            envelope = connection.execute(
                "SELECT * FROM implementation_envelopes WHERE envelope_ref = ? AND transaction_ref = ?",
                (envelope_ref, transaction["transaction_ref"]),
            ).fetchone()
            if envelope is None or envelope["state"] != "DISPATCHED":
                raise TransactionError("ENVELOPE_NOT_DISPATCHED", "envelope changed during capture")
            locked_raw, locked_before = _stored_snapshot(
                envelope["before_snapshot_json"],
                envelope["before_snapshot_sha256"],
                "beforeSnapshot",
                expected_project_root=transaction["project_root"],
            )
            if locked_raw != before_raw or locked_before != before:
                raise TransactionError(
                    "DISPATCH_STATE_CHANGED", "before snapshot changed during after capture"
                )
            cursor = connection.execute(
                """
                UPDATE implementation_envelopes
                SET after_snapshot_json = ?, after_snapshot_sha256 = ?, delta_json = ?,
                    state = 'CAPTURED', closed_at = ?
                WHERE envelope_ref = ? AND state = 'DISPATCHED'
                """,
                (
                    after_payload,
                    hashlib.sha256(after_payload).hexdigest(),
                    delta_payload,
                    _now(),
                    envelope_ref,
                ),
            )
            if cursor.rowcount != 1:
                raise TransactionError(
                    "DISPATCH_STATE_CHANGED", "dispatched envelope changed during after capture"
                )
            cursor = connection.execute(
                """
                UPDATE implementation_transactions SET state = 'RECONCILING'
                WHERE transaction_ref = ? AND state = 'WORKER_ACTIVE'
                """,
                (transaction["transaction_ref"],),
            )
            if cursor.rowcount != 1:
                raise TransactionError(
                    "DISPATCH_STATE_CHANGED", "transaction changed during after capture"
                )
            self._event_locked(
                connection,
                transaction["transaction_ref"],
                "AFTER_SNAPSHOT_CAPTURED",
                {"envelopeRef": envelope_ref, "afterIdentity": after["identity"], "delta": delta},
            )
        return {"envelopeRef": envelope_ref, "afterIdentity": after["identity"], "delta": delta, "state": "CAPTURED"}

    def reconcile_envelope(
        self,
        *,
        transaction_capability: str,
        envelope_ref: str,
        reconciliation: Mapping[str, Any],
    ) -> dict[str, Any]:
        value = _mapping(reconciliation, "reconciliation")
        expected = {
            "disposition",
            "workerAttributablePaths",
            "externalPaths",
            "preservedUserChanges",
            "externalEffectState",
        }
        if set(value) != expected or value["disposition"] != "CONTINUE":
            raise TransactionError("RECONCILIATION_INCOMPLETE", "reconciliation disposition must be CONTINUE")
        worker_paths = _strings(value["workerAttributablePaths"], "workerAttributablePaths")
        external_paths = _strings(value["externalPaths"], "externalPaths")
        preserved = _strings(value["preservedUserChanges"], "preservedUserChanges")
        if value["externalEffectState"] != "CLEAR":
            raise TransactionError("RECONCILIATION_INCOMPLETE", "external effect state is not CLEAR")
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            envelope = connection.execute(
                "SELECT * FROM implementation_envelopes WHERE envelope_ref = ? AND transaction_ref = ?",
                (envelope_ref, transaction["transaction_ref"]),
            ).fetchone()
            if envelope is None or envelope["state"] != "CAPTURED":
                raise TransactionError("ENVELOPE_NOT_CAPTURED", "envelope is absent or not captured")
            delta = _decode_json(envelope["delta_json"], "delta")
            forbidden = _decode_json(envelope["forbidden_paths_json"], "forbiddenPaths")
            changed = set(delta["changedPaths"])
            worker_set = set(worker_paths)
            external_set = set(external_paths)
            if worker_set & external_set or worker_set | external_set != changed:
                raise TransactionError("RECONCILIATION_INCOMPLETE", "changed path partition is incomplete")
            if not worker_set.issubset(set(delta["inScopePaths"])):
                raise TransactionError("RECONCILIATION_INCOMPLETE", "Worker-attributable path is outside the envelope")
            try:
                forbidden_worker_path = any(
                    ownership_snapshot.path_matches_any(path, tuple(forbidden))
                    for path in worker_set
                )
            except ownership_snapshot.SnapshotError as exc:
                raise TransactionError(
                    "STORE_CORRUPT", f"stored envelope path policy is invalid: {exc.message}"
                ) from exc
            if forbidden_worker_path:
                raise TransactionError(
                    "RECONCILIATION_INCOMPLETE", "Worker-attributable path is forbidden"
                )
            if external_set and not external_set.issubset(set(preserved)):
                raise TransactionError("RECONCILIATION_INCOMPLETE", "external paths are not recorded as preserved")
            prior_envelopes = connection.execute(
                """
                SELECT envelope_ref, delta_json, reconciliation_json, state
                FROM implementation_envelopes
                WHERE transaction_ref = ? AND task_id = ? AND envelope_ref != ?
                """,
                (transaction["transaction_ref"], envelope["task_id"], envelope_ref),
            ).fetchall()
            prior_by_ref = {row["envelope_ref"]: row for row in prior_envelopes}
            invalidation_rows = connection.execute(
                """
                SELECT payload_json, payload_sha256
                FROM implementation_events
                WHERE transaction_ref = ?
                  AND event_kind = 'ENVELOPE_INVALIDATED_BEFORE_DISPATCH'
                ORDER BY event_id
                """,
                (transaction["transaction_ref"],),
            ).fetchall()
            invalidations: dict[str, list[Mapping[str, Any]]] = {}
            for offset, event_row in enumerate(invalidation_rows):
                _, raw_event = _stored_payload(
                    event_row["payload_json"],
                    event_row["payload_sha256"],
                    f"invalidationEvent[{offset}]",
                )
                if (
                    not isinstance(raw_event, Mapping)
                    or set(raw_event) != _INVALIDATION_EVENT_FIELDS
                    or not isinstance(raw_event.get("envelopeRef"), str)
                ):
                    raise TransactionError(
                        "STORE_CORRUPT", f"invalidationEvent[{offset}] shape is invalid"
                    )
                invalidations.setdefault(raw_event["envelopeRef"], []).append(raw_event)
            prior_external_paths: set[str] = set()
            for prior_ref, prior in prior_by_ref.items():
                prior_events = invalidations.get(prior_ref, [])
                if not prior_events:
                    continue
                if len(prior_events) != 1 or prior["state"] != "RECONCILED":
                    raise TransactionError(
                        "STORE_CORRUPT", "prior same-task invalidation facts are inconsistent"
                    )
                prior_delta = _decode_json(prior["delta_json"], "priorInvalidation.delta")
                prior_reconciliation = _decode_json(
                    prior["reconciliation_json"], "priorInvalidation.reconciliation"
                )
                prior_event = prior_events[0]
                if (
                    not isinstance(prior_delta, Mapping)
                    or not isinstance(prior_reconciliation, Mapping)
                    or prior_event["changedPaths"] != prior_delta.get("changedPaths")
                    or prior_event["workerAttributablePaths"] != []
                    or prior_event["externalPaths"] != prior_reconciliation.get("externalPaths")
                    or prior_event["preservedUserChanges"]
                    != prior_reconciliation.get("preservedUserChanges")
                    or prior_event["externalPaths"] != prior_event["changedPaths"]
                    or prior_event["preservedUserChanges"] != prior_event["changedPaths"]
                ):
                    raise TransactionError(
                        "STORE_CORRUPT", "prior same-task invalidation partition differs"
                    )
                try:
                    prior_external_paths.update(
                        _strings(
                            prior_event["externalPaths"],
                            "priorInvalidation.externalPaths",
                        )
                    )
                except TransactionError as exc:
                    raise TransactionError(
                        "STORE_CORRUPT", f"prior invalidation paths are invalid: {exc.message}"
                    ) from exc
            if worker_set & prior_external_paths:
                raise TransactionError(
                    "RECONCILIATION_INCOMPLETE",
                    "same-task Worker attribution overlaps prior pre-dispatch external drift",
                )
            normalized = {
                "disposition": "CONTINUE",
                "workerAttributablePaths": worker_paths,
                "externalPaths": external_paths,
                "preservedUserChanges": preserved,
                "externalEffectState": "CLEAR",
            }
            connection.execute(
                """
                UPDATE implementation_envelopes
                SET reconciliation_json = ?, state = 'RECONCILED', closed_at = ?
                WHERE envelope_ref = ? AND state = 'CAPTURED'
                """,
                (_canonical_json(normalized), _now(), envelope_ref),
            )
            connection.execute(
                "UPDATE implementation_transactions SET state = 'OPEN' WHERE transaction_ref = ?",
                (transaction["transaction_ref"],),
            )
            self._event_locked(
                connection,
                transaction["transaction_ref"],
                "OWNERSHIP_RECONCILED",
                {"envelopeRef": envelope_ref, "reconciliation": normalized},
            )
        return {"envelopeRef": envelope_ref, "state": "RECONCILED", "reconciliation": normalized}

    def prepare_handoff(self, *, transaction_capability: str) -> dict[str, Any]:
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["state"] != "OPEN":
                raise TransactionError("TRANSACTION_NOT_READY", "transaction has an active or unresolved envelope")
            envelopes = connection.execute(
                "SELECT * FROM implementation_envelopes WHERE transaction_ref = ? ORDER BY created_at",
                (transaction["transaction_ref"],),
            ).fetchall()
            if any(envelope["state"] != "RECONCILED" for envelope in envelopes):
                raise TransactionError("RECONCILIATION_INCOMPLETE", "an envelope is not reconciled")
            checks = connection.execute(
                "SELECT result_json FROM implementation_checks WHERE transaction_ref = ?",
                (transaction["transaction_ref"],),
            ).fetchall()
            for index, check in enumerate(checks):
                result = _decode_json(check["result_json"], f"check[{index}]")
                if result.get("status") != "EXITED" or result.get("exitCode") != 0:
                    raise TransactionError("IMPLEMENTATION_CHECK_FAILED", "a recorded mandatory check did not pass")
            project_root = Path(transaction["project_root"])
            baseline_ref = transaction["baseline_capsule_ref"]
            baseline_identity = transaction["baseline_source_identity"]

        try:
            lease = self.capsules.acquire_read(baseline_ref)
            try:
                baseline_manifest = baseline_capsule.capture_identity(lease["sealedRoot"])
                final_manifest = baseline_capsule.capture_identity(project_root)
            finally:
                self.capsules.release_read(lease["readLeaseId"])
        except baseline_capsule.CapsuleError as exc:
            raise TransactionError(exc.code, exc.message) from exc
        if baseline_manifest["sourceIdentity"] != baseline_identity:
            raise TransactionError("CAPSULE_CORRUPT", "baseline source identity differs")
        changed_paths = baseline_capsule.changed_paths(baseline_manifest, final_manifest)
        observed_paths: set[str] = set()
        worker_attributable_paths: set[str] = set()
        external_paths: set[str] = set()
        for envelope in envelopes:
            delta = _decode_json(envelope["delta_json"], "envelope.delta")
            reconciliation = _decode_json(
                envelope["reconciliation_json"], "envelope.reconciliation"
            )
            observed_paths.update(delta["changedPaths"])
            worker_attributable_paths.update(reconciliation["workerAttributablePaths"])
            external_paths.update(reconciliation["externalPaths"])
        if not set(changed_paths).issubset(observed_paths):
            raise TransactionError("UNOBSERVED_PRODUCT_DELTA", "final delta contains a path outside ownership captures")
        retained_paths = set(changed_paths)
        retained_worker_paths = retained_paths & worker_attributable_paths
        retained_external_paths = retained_paths & external_paths
        if retained_worker_paths & retained_external_paths:
            raise TransactionError(
                "RECONCILIATION_INCOMPLETE",
                "a retained path has conflicting Worker and external attribution",
            )
        if retained_paths != retained_worker_paths | retained_external_paths:
            raise TransactionError(
                "RECONCILIATION_INCOMPLETE",
                "the final physical delta is not completely attributed",
            )
        final_identity = final_manifest["sourceIdentity"]
        if transaction["mode"] == "VERIFICATION_REMEDIATION" and (
            not retained_worker_paths or final_identity == baseline_identity
        ):
            raise TransactionError(
                "EMPTY_REMEDIATION_DELTA",
                "remediation handoff requires a retained Worker-attributable product delta",
            )
        before_entries = baseline_manifest["entries"]
        after_entries = final_manifest["entries"]
        before_paths = set(before_entries)
        after_paths = set(after_entries)
        delta_payload_value = {
            "schemaVersion": "implementation-delta-v1",
            "transactionRef": transaction["transaction_ref"],
            "projectRoot": str(project_root),
            "baselineSourceIdentity": baseline_identity,
            "finalSourceIdentity": final_identity,
            "created": sorted(after_paths - before_paths),
            "modified": sorted(path for path in before_paths & after_paths if before_entries[path] != after_entries[path]),
            "deleted": sorted(before_paths - after_paths),
            "changedPaths": changed_paths,
            "workerAttributablePaths": sorted(retained_worker_paths),
            "preservedExternalPaths": sorted(retained_external_paths),
        }
        delta_ref = f"implementation:delta:v1:{uuid.uuid4().hex}"
        delta_payload = _canonical_json(delta_payload_value)
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["state"] != "OPEN":
                raise TransactionError("TRANSACTION_NOT_READY", "transaction changed during delta capture")
            try:
                current = baseline_capsule.capture_identity(transaction["project_root"])[
                    "sourceIdentity"
                ]
            except baseline_capsule.CapsuleError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            if current != final_identity:
                raise TransactionError("SOURCE_IDENTITY_MISMATCH", "source changed during handoff preparation")
            if transaction["mode"] == "VERIFICATION_REMEDIATION":
                ancestor = connection.execute(
                    "SELECT 1 FROM nodes WHERE root_ref = ? AND source_identity = ? LIMIT 1",
                    (transaction["root_ref"], final_identity),
                ).fetchone()
                if ancestor is not None:
                    raise TransactionError(
                        "ANCESTOR_SOURCE_REUSED",
                        "remediation final source identity already exists in this lineage",
                    )
            connection.execute(
                """
                INSERT INTO implementation_deltas(
                    delta_ref, transaction_ref, payload_json, payload_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    delta_ref,
                    transaction["transaction_ref"],
                    delta_payload,
                    hashlib.sha256(delta_payload).hexdigest(),
                    _now(),
                ),
            )
            connection.execute(
                """
                UPDATE implementation_transactions
                SET state = 'READY_FOR_HANDOFF', final_source_identity = ?, implementation_delta_ref = ?
                WHERE transaction_ref = ? AND state = 'OPEN'
                """,
                (final_identity, delta_ref, transaction["transaction_ref"]),
            )
            self._event_locked(
                connection,
                transaction["transaction_ref"],
                "HANDOFF_PREPARED",
                {"deltaRef": delta_ref, "finalSourceIdentity": final_identity, "changedPaths": changed_paths},
            )
        return {
            "transactionRef": transaction["transaction_ref"],
            "mode": transaction["mode"],
            "baselineCapsuleRef": baseline_ref,
            "baselineSourceIdentity": baseline_identity,
            "finalSourceIdentity": final_identity,
            "implementationDeltaRef": delta_ref,
            "changedPaths": changed_paths,
            "state": "READY_FOR_HANDOFF",
        }

    def close_without_successor(
        self,
        *,
        transaction_capability: str,
        remediator_capability: str,
    ) -> dict[str, Any]:
        """Release a remediation claim only after exact no-delta safe closure.

        A Worker call may be rejected, make no change, or be fully reversed.  The
        claim remains exclusive until the owner store can prove that the project is
        exactly back at the failed predecessor identity and every ownership envelope
        is reconciled with no unresolved external effect.
        """

        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            if transaction["mode"] != "VERIFICATION_REMEDIATION":
                raise TransactionError(
                    "SUCCESSORLESS_RELEASE_NOT_ALLOWED", "only remediation transactions may close without a handoff"
                )
            if transaction["state"] != "OPEN" or transaction["implementation_delta_ref"] is not None:
                raise TransactionError(
                    "SUCCESSORLESS_RELEASE_NOT_SAFE", "transaction is active, unresolved, or already prepared"
                )
            try:
                remediator = self.workflow._actor_for_capability_locked(
                    connection, remediator_capability, expected_role="REMEDIATOR"
                )
            except workflow_store.WorkflowStoreError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            claim = connection.execute(
                "SELECT * FROM claims WHERE claim_ref = ?", (transaction["claim_ref"],)
            ).fetchone()
            if (
                claim is None
                or claim["state"] != "ACTIVE"
                or claim["transition_kind"] != "REMEDIATE"
                or claim["claimant_actor_ref"] != remediator["actor_ref"]
                or claim["execution_ref"] != transaction["transaction_ref"]
            ):
                raise TransactionError(
                    "REMEDIATION_CLAIM_MISMATCH", "only the active claim-owning Remediator may close"
                )
            envelopes = connection.execute(
                "SELECT * FROM implementation_envelopes WHERE transaction_ref = ? ORDER BY created_at",
                (transaction["transaction_ref"],),
            ).fetchall()
            if any(envelope["state"] != "RECONCILED" for envelope in envelopes):
                raise TransactionError(
                    "SUCCESSORLESS_RELEASE_NOT_SAFE", "every started ownership envelope must be reconciled"
                )
            for index, envelope in enumerate(envelopes):
                reconciliation = _decode_json(
                    envelope["reconciliation_json"], f"envelope[{index}].reconciliation"
                )
                if reconciliation.get("externalEffectState") != "CLEAR":
                    raise TransactionError(
                        "SUCCESSORLESS_RELEASE_NOT_SAFE", "an external or ambiguous effect remains unresolved"
                    )
                external = set(reconciliation.get("externalPaths", []))
                preserved = set(reconciliation.get("preservedUserChanges", []))
                if not external.issubset(preserved):
                    raise TransactionError(
                        "SUCCESSORLESS_RELEASE_NOT_SAFE", "pre-existing or concurrent work is not preserved"
                    )
            project_root = Path(transaction["project_root"])
            baseline_ref = transaction["baseline_capsule_ref"]
            baseline_identity = transaction["baseline_source_identity"]

        try:
            lease = self.capsules.acquire_read(baseline_ref)
            try:
                retained = baseline_capsule.capture_identity(lease["sealedRoot"])
                current = baseline_capsule.capture_identity(project_root)
            finally:
                self.capsules.release_read(lease["readLeaseId"])
        except baseline_capsule.CapsuleError as exc:
            raise TransactionError(exc.code, exc.message) from exc
        if retained["sourceIdentity"] != baseline_identity:
            raise TransactionError("CAPSULE_CORRUPT", "remediation baseline capsule identity differs")
        changed_paths = baseline_capsule.changed_paths(retained, current)
        if current["sourceIdentity"] != baseline_identity or changed_paths:
            raise TransactionError(
                "SUCCESSORLESS_RELEASE_NOT_SAFE", "a product delta remains or predecessor identity was not restored"
            )

        closed_at = _now()
        closure_ref = f"closure:remediation-no-successor:v1:{uuid.uuid4().hex}"
        closure = {
            "closureRef": closure_ref,
            "disposition": "NO_SUCCESSOR_SAFE_RELEASE",
            "baselineSourceIdentity": baseline_identity,
            "finalObservedSourceIdentity": current["sourceIdentity"],
            "changedPaths": [],
            "ownershipEnvelopeCount": len(envelopes),
            "externalEffectState": "CLEAR",
            "closedAt": closed_at,
        }
        with self.workflow._transaction() as connection:
            transaction = self._transaction_for_capability_locked(connection, transaction_capability)
            claim = connection.execute(
                "SELECT * FROM claims WHERE claim_ref = ?", (transaction["claim_ref"],)
            ).fetchone()
            if transaction["state"] != "OPEN" or claim is None or claim["state"] != "ACTIVE":
                raise TransactionError("REMEDIATION_CLAIM_MISMATCH", "transaction changed during closure")
            try:
                observed = baseline_capsule.capture_identity(transaction["project_root"])[
                    "sourceIdentity"
                ]
            except baseline_capsule.CapsuleError as exc:
                raise TransactionError(exc.code, exc.message) from exc
            if observed != baseline_identity:
                raise TransactionError(
                    "SUCCESSORLESS_RELEASE_NOT_SAFE", "source changed during successorless closure"
                )
            reservation = connection.execute(
                "SELECT * FROM budget_reservations WHERE reservation_ref = ?",
                (claim["budget_reservation_ref"],),
            ).fetchone()
            if reservation is None or reservation["state"] != "ACTIVE":
                raise TransactionError("BUDGET_RESERVATION_NOT_ACTIVE", "claim budget is not active")
            closure_reserved = self.workflow._stored_budget(
                reservation["closure_reserved_json"], "reservation.closureReserved"
            )
            closure_used = self.workflow._stored_budget(
                reservation["closure_used_json"], "reservation.closureUsed"
            )
            closure_delta = {field: 0 for field in workflow_store.BUDGET_FIELDS}
            closure_delta["toolCostUnits"] = 1
            closure_delta["closureOperations"] = 1
            next_closure = {
                field: closure_used[field] + closure_delta[field]
                for field in workflow_store.BUDGET_FIELDS
            }
            exceeded = [
                field
                for field in workflow_store.BUDGET_FIELDS
                if next_closure[field] > closure_reserved[field]
            ]
            if exceeded:
                raise TransactionError(
                    "BUDGET_RESERVATION_EXCEEDED",
                    f"safe closure exceeds reserved budget: {', '.join(exceeded)}",
                )
            spend_used = self.workflow._stored_budget(
                reservation["spend_used_json"], "reservation.spendUsed"
            )
            invocation = connection.execute(
                "SELECT consumed_json FROM invocations WHERE invocation_ref = ?",
                (reservation["invocation_ref"],),
            ).fetchone()
            if invocation is None:
                raise TransactionError("STORE_CORRUPT", "remediation invocation is absent")
            consumed = self.workflow._stored_budget(invocation["consumed_json"], "invocation.consumed")
            next_consumed = {
                field: consumed[field] + spend_used[field] + next_closure[field]
                for field in workflow_store.BUDGET_FIELDS
            }
            connection.execute(
                "UPDATE invocations SET consumed_json = ? WHERE invocation_ref = ?",
                (_canonical_json(next_consumed), reservation["invocation_ref"]),
            )
            connection.execute(
                """
                UPDATE budget_reservations
                SET closure_used_json = ?, state = 'CLOSED', closed_at = ?
                WHERE reservation_ref = ? AND state = 'ACTIVE'
                """,
                (_canonical_json(next_closure), closed_at, reservation["reservation_ref"]),
            )
            connection.execute(
                """
                UPDATE implementation_transactions
                SET state = 'CLOSED_NO_SUCCESSOR', final_source_identity = ?, closed_at = ?
                WHERE transaction_ref = ? AND state = 'OPEN'
                """,
                (baseline_identity, closed_at, transaction["transaction_ref"]),
            )
            connection.execute(
                """
                UPDATE claims
                SET state = 'RELEASED', closure_ref = ?, closed_at = ?
                WHERE claim_ref = ? AND state = 'ACTIVE'
                """,
                (closure_ref, closed_at, claim["claim_ref"]),
            )
            self._event_locked(
                connection,
                transaction["transaction_ref"],
                "NO_SUCCESSOR_SAFE_RELEASE",
                closure,
            )
        return {
            "transactionRef": transaction["transaction_ref"],
            "claimRef": claim["claim_ref"],
            "state": "CLOSED_NO_SUCCESSOR",
            "closure": closure,
        }

    def read_transaction(self, transaction_ref: str) -> dict[str, Any]:
        if not isinstance(transaction_ref, str) or not TRANSACTION_REF_PATTERN.fullmatch(
            transaction_ref
        ):
            raise TransactionError("MALFORMED_TRANSACTION", "transaction ref is malformed")
        connection = self.workflow._connect()
        try:
            transaction = connection.execute(
                "SELECT * FROM implementation_transactions WHERE transaction_ref = ?", (transaction_ref,)
            ).fetchone()
            if transaction is None:
                raise TransactionError("TRANSACTION_NOT_FOUND", f"unknown transaction: {transaction_ref}")
            envelopes = connection.execute(
                "SELECT * FROM implementation_envelopes WHERE transaction_ref = ? ORDER BY created_at",
                (transaction_ref,),
            ).fetchall()
            checks = connection.execute(
                "SELECT * FROM implementation_checks WHERE transaction_ref = ? ORDER BY created_at",
                (transaction_ref,),
            ).fetchall()
            delta = connection.execute(
                "SELECT * FROM implementation_deltas WHERE transaction_ref = ?",
                (transaction_ref,),
            ).fetchone()
            events = connection.execute(
                "SELECT * FROM implementation_events WHERE transaction_ref = ? ORDER BY event_id",
                (transaction_ref,),
            ).fetchall()
            return {
                "transactionRef": transaction_ref,
                "mode": transaction["mode"],
                "rootRef": transaction["root_ref"],
                "claimRef": transaction["claim_ref"],
                "selectedWorker": transaction["selected_worker"],
                "projectRoot": transaction["project_root"],
                "planningIdentity": transaction["planning_identity"],
                "baselineCapsuleRef": transaction["baseline_capsule_ref"],
                "baselineSourceIdentity": transaction["baseline_source_identity"],
                "state": transaction["state"],
                "finalSourceIdentity": transaction["final_source_identity"],
                "implementationDeltaRef": transaction["implementation_delta_ref"],
                "implementationDelta": None
                if delta is None
                else _decode_json(delta["payload_json"], "implementationDelta"),
                "envelopes": [
                    {
                        "envelopeRef": row["envelope_ref"],
                        "taskId": row["task_id"],
                        "state": row["state"],
                        "delta": None if row["delta_json"] is None else _decode_json(row["delta_json"], "delta"),
                        "reconciliation": None
                        if row["reconciliation_json"] is None
                        else _decode_json(row["reconciliation_json"], "reconciliation"),
                    }
                    for row in envelopes
                ],
                "checks": [
                    {
                        "checkRef": row["check_ref"],
                        "request": _decode_json(row["request_json"], "check.request"),
                        "result": _decode_json(row["result_json"], "check.result"),
                    }
                    for row in checks
                ],
                "events": [
                    {
                        "eventKind": row["event_kind"],
                        "payload": _decode_json(row["payload_json"], "event.payload"),
                        "createdAt": row["created_at"],
                    }
                    for row in events
                ],
            }
        finally:
            connection.close()


__all__ = ["ImplementationTransactionStore", "TransactionError"]
