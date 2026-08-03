#!/usr/bin/env python3
"""Publish implementation-handoff-v1 and read immutable historical v3 results."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workflow_store = _load_module(
    "handoff_workflow_store", IMPLEMENTATION_ROOT / "tools/workflow-store/workflow_store.py"
)
implementation_transaction = _load_module(
    "handoff_implementation_transaction",
    IMPLEMENTATION_ROOT / "tools/implementation-transaction/implementation_transaction.py",
)
baseline_capsule = implementation_transaction.baseline_capsule


PROTOCOL_VERSION = "implementation-handoff-v1"
RETIRED_PROTOCOL_VERSION = "implementation-result-v3"
HANDOFF_REF_PATTERN = re.compile(r"^implementation:handoff:v1:[a-f0-9]{32}$")
HISTORICAL_V3_REF_PATTERN = re.compile(r"^implementation:v3:[a-f0-9]{32}$")
TRANSACTION_REF_PATTERN = re.compile(r"^implementation:transaction:v1:[a-f0-9]{32}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

DEFAULT_WORKFLOW_ROOT = workflow_store.DEFAULT_STORE_ROOT
DEFAULT_HISTORICAL_ROOT = Path.home() / ".local/state/opencode/implementation-results"
MAX_REQUEST_BYTES = 256 * 1024
MAX_CRITERIA = 128
MAX_TASK_IDS = 512
MAX_PATH_BYTES = 4096

PLANNING_SEAL_FIELDS = (
    "ticketPath",
    "ticketSha256",
    "specPath",
    "specSha256",
    "blockerFiles",
)
BLOCKER_FIELDS = ("path", "sha256", "status")


class HandoffError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> bytes:
    try:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HandoffError("MALFORMED_HANDOFF", f"request is not JSON serializable: {exc}") from exc
    if len(payload) > MAX_REQUEST_BYTES:
        raise HandoffError("MALFORMED_HANDOFF", f"request exceeds {MAX_REQUEST_BYTES} bytes")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise HandoffError("PLANNING_INPUT_CHANGED", f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def _mapping(value: Any, locator: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HandoffError("MALFORMED_HANDOFF", f"{locator} must be an object")
    return value


def _fields(value: Mapping[str, Any], expected: set[str], locator: str) -> None:
    if set(value) != expected:
        raise HandoffError("MALFORMED_HANDOFF", f"{locator} fields are invalid")


def _ordered_fields(value: Mapping[str, Any], expected: tuple[str, ...], locator: str) -> None:
    if tuple(value) != expected:
        raise HandoffError("MALFORMED_HANDOFF", f"{locator} fields or field order are invalid")


def _line_content(line: bytes) -> bytes:
    if line.endswith(b"\r\n"):
        return line[:-2]
    if line.endswith(b"\n") or line.endswith(b"\r"):
        return line[:-1]
    return line


def acceptance_criteria_from_ticket(path: Path | str) -> list[dict[str, Any]]:
    ticket = Path(path)
    try:
        raw = ticket.read_bytes()
        raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise HandoffError("PLANNING_INPUT_CHANGED", f"cannot read Ticket Acceptance Criteria: {exc}") from exc
    lines = raw.splitlines(keepends=True)
    headings = [index for index, line in enumerate(lines) if _line_content(line) == b"## Acceptance Criteria"]
    if len(headings) != 1:
        raise HandoffError("MALFORMED_TICKET", "Ticket must contain one exact ## Acceptance Criteria heading")
    start = headings[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if _line_content(lines[index]).startswith(b"## "):
            end = index
            break
    body = lines[start:end]
    while body and _line_content(body[0]) == b"":
        body.pop(0)
    while body and _line_content(body[-1]) == b"":
        body.pop()
    if not body:
        raise HandoffError("MALFORMED_TICKET", "Acceptance Criteria must contain top-level list items")
    criteria_bytes: list[bytes] = []
    current: list[bytes] = []
    for line in body:
        content = _line_content(line)
        if content.startswith(b"- "):
            if not content[2:].strip():
                raise HandoffError("MALFORMED_TICKET", "Acceptance Criterion item must not be empty")
            if current:
                criteria_bytes.append(b"".join(current))
            current = [line]
        elif current and (content == b"" or content.startswith(b"  ")):
            current.append(line)
        else:
            raise HandoffError(
                "MALFORMED_TICKET",
                "Acceptance Criteria allows only exact top-level '- ' items and two-space continuations",
            )
    if current:
        criteria_bytes.append(b"".join(current))
    if not criteria_bytes or len(criteria_bytes) > MAX_CRITERIA:
        raise HandoffError("MALFORMED_TICKET", f"Acceptance Criteria must contain 1-{MAX_CRITERIA} items")
    return [
        {"criterionIndex": index, "criterionRawSha256": hashlib.sha256(raw_item).hexdigest()}
        for index, raw_item in enumerate(criteria_bytes, start=1)
    ]


def acceptance_criteria_digest(criteria: list[dict[str, Any]]) -> str:
    ordered = [
        {"criterionIndex": item["criterionIndex"], "criterionRawSha256": item["criterionRawSha256"]}
        for item in criteria
    ]
    return hashlib.sha256(_canonical_json(ordered)).hexdigest()


def planning_seal_digest(seal: Mapping[str, Any]) -> str:
    value = _mapping(seal, "planningSeal")
    _fields(value, set(PLANNING_SEAL_FIELDS), "planningSeal")
    blockers = value["blockerFiles"]
    if not isinstance(blockers, list) or len(blockers) > 128:
        raise HandoffError("MALFORMED_HANDOFF", "planningSeal.blockerFiles is invalid")
    normalized_blockers: list[dict[str, Any]] = []
    for index, raw in enumerate(blockers):
        blocker = _mapping(raw, f"planningSeal.blockerFiles[{index}]")
        _fields(blocker, set(BLOCKER_FIELDS), f"planningSeal.blockerFiles[{index}]")
        normalized_blockers.append({field: blocker[field] for field in BLOCKER_FIELDS})
    normalized = {
        "ticketPath": value["ticketPath"],
        "ticketSha256": value["ticketSha256"],
        "specPath": value["specPath"],
        "specSha256": value["specSha256"],
        "blockerFiles": normalized_blockers,
    }
    return hashlib.sha256(_canonical_json(normalized)).hexdigest()


def _canonical_file(raw_path: Any, locator: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path or len(raw_path.encode("utf-8")) > MAX_PATH_BYTES:
        raise HandoffError("MALFORMED_HANDOFF", f"{locator} is invalid")
    path = Path(raw_path)
    if not path.is_absolute():
        raise HandoffError("MALFORMED_HANDOFF", f"{locator} must be absolute")
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise HandoffError("PLANNING_INPUT_CHANGED", f"cannot resolve {locator}: {exc}") from exc
    if str(canonical) != raw_path or not canonical.is_file():
        raise HandoffError("PLANNING_INPUT_CHANGED", f"{locator} is not the same canonical regular file")
    return canonical


def _validate_planning_seal(raw: Any) -> dict[str, Any]:
    seal = _mapping(raw, "planningSeal")
    _ordered_fields(seal, PLANNING_SEAL_FIELDS, "planningSeal")
    normalized: dict[str, Any] = {}
    for role, path_key, digest_key in (
        ("Ticket", "ticketPath", "ticketSha256"),
        ("Spec", "specPath", "specSha256"),
    ):
        path = _canonical_file(seal[path_key], f"planningSeal.{path_key}")
        digest = seal[digest_key]
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
            raise HandoffError("MALFORMED_HANDOFF", f"{role} planning digest is malformed")
        if _sha256(path) != digest:
            raise HandoffError("PLANNING_INPUT_CHANGED", f"{role} digest changed")
        normalized[path_key] = str(path)
        normalized[digest_key] = digest
    blockers = seal["blockerFiles"]
    if not isinstance(blockers, list) or len(blockers) > 128:
        raise HandoffError("MALFORMED_HANDOFF", "planningSeal.blockerFiles is invalid")
    normalized_blockers: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw_blocker in enumerate(blockers):
        blocker = _mapping(raw_blocker, f"planningSeal.blockerFiles[{index}]")
        _ordered_fields(blocker, BLOCKER_FIELDS, f"planningSeal.blockerFiles[{index}]")
        path = _canonical_file(blocker["path"], f"planningSeal.blockerFiles[{index}].path")
        digest = blocker["sha256"]
        status = blocker["status"]
        if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest) or status not in {"resolved", "done"}:
            raise HandoffError("MALFORMED_HANDOFF", f"planningSeal.blockerFiles[{index}] is malformed")
        if str(path) in seen or _sha256(path) != digest:
            raise HandoffError("PLANNING_INPUT_CHANGED", f"blocker changed or duplicated: {path}")
        seen.add(str(path))
        normalized_blockers.append({"path": str(path), "sha256": digest, "status": status})
    normalized["blockerFiles"] = normalized_blockers
    return normalized


def _validate_criterion_accounting(
    raw: Any,
    criteria: list[dict[str, Any]],
    transaction_view: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or len(raw) != len(criteria):
        raise HandoffError("INCOMPLETE_CRITERION_ACCOUNTING", "criterionAccounting must contain every exact AC")
    expected_tasks: dict[int, set[str]] = {item["criterionIndex"]: set() for item in criteria}
    for envelope in transaction_view["envelopes"]:
        event = next(
            (
                item
                for item in transaction_view["events"]
                if item["eventKind"] == "ENVELOPE_FROZEN"
                and item["payload"].get("envelopeRef") == envelope["envelopeRef"]
            ),
            None,
        )
        if event is None:
            raise HandoffError("TRANSACTION_CORRUPT", "envelope has no immutable freeze event")
        for criterion in event["payload"]["criterionRefs"]:
            index = criterion["criterionIndex"]
            expected = next((item for item in criteria if item["criterionIndex"] == index), None)
            if expected != criterion:
                raise HandoffError("ACCEPTANCE_CRITERIA_MISMATCH", "transaction criterion identity is stale")
            expected_tasks[index].add(envelope["taskId"])
    normalized: list[dict[str, Any]] = []
    for offset, (raw_item, expected) in enumerate(zip(raw, criteria)):
        item = _mapping(raw_item, f"criterionAccounting[{offset}]")
        _fields(item, {"criterionIndex", "criterionRawSha256", "taskIds"}, f"criterionAccounting[{offset}]")
        if item["criterionIndex"] != expected["criterionIndex"] or item["criterionRawSha256"] != expected["criterionRawSha256"]:
            raise HandoffError("ACCEPTANCE_CRITERIA_MISMATCH", f"criterionAccounting[{offset}] is stale")
        task_ids = item["taskIds"]
        if not isinstance(task_ids, list) or len(task_ids) > MAX_TASK_IDS:
            raise HandoffError("MALFORMED_HANDOFF", f"criterionAccounting[{offset}].taskIds is invalid")
        if any(not isinstance(task, str) or not ID_PATTERN.fullmatch(task) for task in task_ids):
            raise HandoffError("MALFORMED_HANDOFF", f"criterionAccounting[{offset}].taskIds is invalid")
        if len(set(task_ids)) != len(task_ids) or set(task_ids) != expected_tasks[expected["criterionIndex"]]:
            raise HandoffError(
                "INCOMPLETE_CRITERION_ACCOUNTING",
                f"criterionAccounting[{offset}] does not match transaction task linkage",
            )
        normalized.append({**expected, "taskIds": task_ids})
    return normalized


class HandoffPublisher:
    def __init__(
        self,
        workflow_root: Path | str = DEFAULT_WORKFLOW_ROOT,
        capsule_root: Path | str | None = None,
    ) -> None:
        self.transactions = implementation_transaction.ImplementationTransactionStore(
            workflow_root, capsule_root
        )
        self.workflow = self.transactions.workflow

    def _currentness_validator(
        self,
        *,
        planning_seal: Mapping[str, Any],
        criteria: list[dict[str, Any]],
        project_root: Path,
        final_identity: str,
    ) -> None:
        current_seal = _validate_planning_seal(planning_seal)
        if current_seal != planning_seal:
            raise HandoffError("PLANNING_INPUT_CHANGED", "planning seal changed during publication")
        if acceptance_criteria_from_ticket(current_seal["ticketPath"]) != criteria:
            raise HandoffError("PLANNING_INPUT_CHANGED", "Ticket Acceptance Criteria changed")
        try:
            observed = baseline_capsule.capture_identity(project_root)["sourceIdentity"]
        except baseline_capsule.CapsuleError as exc:
            raise HandoffError(exc.code, exc.message) from exc
        if observed != final_identity:
            raise HandoffError("SOURCE_IDENTITY_MISMATCH", "final source changed during publication")

    def publish(self, request: Mapping[str, Any]) -> dict[str, Any]:
        request = _mapping(request, "ImplementationHandoff request")
        _canonical_json(request)
        if request.get("protocolVersion") == RETIRED_PROTOCOL_VERSION:
            raise HandoffError("PROTOCOL_RETIRED", "implementation-result-v3 no longer accepts publications")
        _fields(
            request,
            {
                "protocolVersion",
                "implementationTransactionRef",
                "actorCapability",
                "planningSeal",
                "criterionAccounting",
                "unresolvedImplementationItems",
            },
            "ImplementationHandoff request",
        )
        if request["protocolVersion"] != PROTOCOL_VERSION:
            raise HandoffError("UNKNOWN_PROTOCOL_VERSION", f"protocolVersion is not {PROTOCOL_VERSION}")
        transaction_ref = request["implementationTransactionRef"]
        if not isinstance(transaction_ref, str) or not TRANSACTION_REF_PATTERN.fullmatch(transaction_ref):
            raise HandoffError("MALFORMED_HANDOFF", "implementationTransactionRef is malformed")
        if request["unresolvedImplementationItems"] != []:
            raise HandoffError("UNRESOLVED_IMPLEMENTATION_ITEMS", "handoff cannot contain unresolved items")
        planning_seal = _validate_planning_seal(request["planningSeal"])
        planning_identity = planning_seal_digest(planning_seal)
        criteria = acceptance_criteria_from_ticket(planning_seal["ticketPath"])
        transaction = self.transactions.read_transaction(transaction_ref)
        if transaction["state"] != "READY_FOR_HANDOFF":
            raise HandoffError("IMPLEMENTATION_TRANSACTION_NOT_READY", "transaction is not ready for handoff")
        if transaction["planningIdentity"] != planning_identity:
            raise HandoffError("PLANNING_INPUT_CHANGED", "transaction planning identity differs")
        criterion_accounting = _validate_criterion_accounting(
            request["criterionAccounting"], criteria, transaction
        )
        project_root = Path(transaction["projectRoot"])
        final_identity = transaction["finalSourceIdentity"]
        baseline_identity = transaction["baselineSourceIdentity"]
        delta_ref = transaction["implementationDeltaRef"]
        if not isinstance(final_identity, str) or not isinstance(delta_ref, str):
            raise HandoffError("IMPLEMENTATION_TRANSACTION_NOT_READY", "transaction closure facts are missing")
        try:
            lease = self.transactions.capsules.acquire_read(transaction["baselineCapsuleRef"])
            try:
                if (
                    lease["canonicalProjectRoot"] != str(project_root)
                    or lease["baselineSourceIdentity"] != baseline_identity
                ):
                    raise HandoffError("CAPSULE_PROJECT_MISMATCH", "baseline capsule differs from transaction")
            finally:
                self.transactions.capsules.release_read(lease["readLeaseId"])
        except baseline_capsule.CapsuleError as exc:
            raise HandoffError(exc.code, exc.message) from exc
        self._currentness_validator(
            planning_seal=planning_seal,
            criteria=criteria,
            project_root=project_root,
            final_identity=final_identity,
        )
        handoff_ref = workflow_store.allocate_ref("IMPLEMENTATION_HANDOFF")
        completed_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "protocolVersion": PROTOCOL_VERSION,
            "implementationHandoffRef": handoff_ref,
            "implementationStatus": "IMPLEMENTATION_HANDOFF_COMPLETE",
            "projectRoot": str(project_root),
            "planningSeal": planning_seal,
            "planningSealDigest": planning_identity,
            "baselineCapsuleRef": transaction["baselineCapsuleRef"],
            "baselineSourceIdentity": baseline_identity,
            "finalSourceIdentity": final_identity,
            "implementationDeltaRef": delta_ref,
            "criterionAccounting": criterion_accounting,
            "unresolvedImplementationItems": [],
            "completedAt": completed_at,
        }
        def validator() -> None:
            self._currentness_validator(
                planning_seal=planning_seal,
                criteria=criteria,
                project_root=project_root,
                final_identity=final_identity,
            )
        try:
            if transaction["mode"] == "INITIAL_IMPLEMENTATION":
                if request["actorCapability"] is not None:
                    raise HandoffError("ROLE_CAPABILITY_MISMATCH", "initial handoff has no verification actor")
                node = self.workflow.publish_initial_handoff(
                    node_ref=handoff_ref,
                    protocol_version=PROTOCOL_VERSION,
                    planning_identity=planning_identity,
                    source_identity=final_identity,
                    payload=payload,
                    implementation_transaction_ref=transaction_ref,
                    validate_currentness=validator,
                )
            elif transaction["mode"] == "VERIFICATION_REMEDIATION":
                actor_capability = request["actorCapability"]
                if not isinstance(actor_capability, str):
                    raise HandoffError("ROLE_CAPABILITY_MISMATCH", "remediation handoff requires its Remediator")
                claim_ref = transaction["claimRef"]
                node = self.workflow.publish_successor(
                    claimant_capability=actor_capability,
                    claim_ref=claim_ref,
                    node_ref=handoff_ref,
                    node_kind="IMPLEMENTATION_HANDOFF",
                    protocol_version=PROTOCOL_VERSION,
                    planning_identity=planning_identity,
                    source_identity=final_identity,
                    verification_status=None,
                    payload=payload,
                    implementation_transaction_ref=transaction_ref,
                    validate_currentness=validator,
                )
            else:
                raise HandoffError("MALFORMED_HANDOFF", "transaction mode is invalid")
        except workflow_store.WorkflowStoreError as exc:
            raise HandoffError(exc.code, exc.message) from exc
        if node["payload"] != payload:
            raise HandoffError("PUBLICATION_FAILED", "stored handoff readback differs")
        return payload


class HistoricalV3Store:
    def __init__(self, result_root: Path | str = DEFAULT_HISTORICAL_ROOT) -> None:
        self.result_root = Path(result_root).expanduser().resolve()

    def read(self, result_ref: str) -> dict[str, Any]:
        if not isinstance(result_ref, str) or not HISTORICAL_V3_REF_PATTERN.fullmatch(result_ref):
            raise HandoffError("MALFORMED_HISTORICAL_REF", "historical v3 ref is malformed")
        token = result_ref.rsplit(":", 1)[-1]
        path = self.result_root / f"{token}.json"
        try:
            if path.stat().st_size > MAX_REQUEST_BYTES:
                raise HandoffError("HISTORICAL_ARTIFACT_CORRUPT", "historical artifact is oversized")
            value = json.loads(path.read_text(encoding="utf-8"))
        except HandoffError:
            raise
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise HandoffError("HISTORICAL_ARTIFACT_UNAVAILABLE", f"cannot read historical result: {exc}") from exc
        if (
            not isinstance(value, dict)
            or value.get("protocolVersion") != RETIRED_PROTOCOL_VERSION
            or value.get("implementationResultRef") != result_ref
        ):
            raise HandoffError("HISTORICAL_ARTIFACT_CORRUPT", "historical result identity differs")
        return value


def _read_request(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_REQUEST_BYTES:
            raise HandoffError("MALFORMED_HANDOFF", "request is oversized")
        value = json.loads(path.read_text(encoding="utf-8"))
    except HandoffError:
        raise
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HandoffError("MALFORMED_HANDOFF", f"cannot read request: {exc}") from exc
    if not isinstance(value, dict):
        raise HandoffError("MALFORMED_HANDOFF", "request must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-root", default=os.environ.get("IMPLEMENTATION_WORKFLOW_STORE", str(DEFAULT_WORKFLOW_ROOT)))
    parser.add_argument("--capsule-store", default=os.environ.get("BASELINE_CAPSULE_STORE"))
    parser.add_argument("--historical-root", default=os.environ.get("IMPLEMENTATION_RESULT_STORE", str(DEFAULT_HISTORICAL_ROOT)))
    commands = parser.add_subparsers(dest="command", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("--request", required=True)
    historical = commands.add_parser("read-historical-v3")
    historical.add_argument("--ref", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "publish":
            result = HandoffPublisher(args.workflow_root, args.capsule_store).publish(
                _read_request(Path(args.request))
            )
        else:
            result = HistoricalV3Store(args.historical_root).read(args.ref)
    except (HandoffError, implementation_transaction.TransactionError) as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
