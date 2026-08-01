#!/usr/bin/env python3
"""Publish an immutable v3 ImplementationResult from complete, current evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


PROTOCOL_VERSION = "implementation-result-v3"
RESULT_REF_PATTERN = re.compile(r"^implementation:v3:[a-f0-9]{32}$")
CAPSULE_REF_PATTERN = re.compile(r"^capsule:v1:[a-f0-9]{32}$")
IDENTITY_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
DEFAULT_RESULT_ROOT = Path.home() / ".local/state/opencode/implementation-results"

MAX_REQUEST_BYTES = 256 * 1024
MAX_SUMMARY_BYTES = 4096
MAX_LOCATOR_BYTES = 2048
MAX_CRITERIA = 128
MAX_REQUIREMENTS = 512
MAX_EVIDENCE_RECORDS = 512
MAX_AUTHORITY_BINDINGS = 128
MAX_REFS_PER_RECORD = 128

PLANNING_SEAL_FIELDS = (
    "ticketPath",
    "ticketSha256",
    "specPath",
    "specSha256",
    "blockerFiles",
)
BLOCKER_FIELDS = ("path", "sha256", "status")

CAPSULE_MODULE_PATH = Path(
    os.environ.get(
        "BASELINE_CAPSULE_MODULE",
        str(Path(__file__).resolve().parents[3] / "baseline-capsule" / "baseline_capsule.py"),
    )
)
CAPSULE_SPEC = importlib.util.spec_from_file_location("implementation_baseline_capsule", CAPSULE_MODULE_PATH)
if CAPSULE_SPEC is None or CAPSULE_SPEC.loader is None:
    raise RuntimeError(f"cannot load Baseline Capsule module: {CAPSULE_MODULE_PATH}")
baseline_capsule = importlib.util.module_from_spec(CAPSULE_SPEC)
CAPSULE_SPEC.loader.exec_module(baseline_capsule)


class ResultError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise ResultError("PLANNING_INPUT_CHANGED", f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    except FileExistsError as exc:
        raise ResultError("IMMUTABLE_RESULT_EXISTS", f"refusing to overwrite {path}") from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _result_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False).encode() + b"\n"


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _mapping(value: Any, locator: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResultError("MALFORMED_RESULT", f"{locator} must be an object")
    return value


def _fields(value: Mapping[str, Any], expected: set[str], locator: str) -> None:
    if set(value) != expected:
        raise ResultError("MALFORMED_RESULT", f"{locator} fields are invalid")


def _ordered_fields(value: Mapping[str, Any], expected: tuple[str, ...], locator: str) -> None:
    if tuple(value) != expected:
        raise ResultError("MALFORMED_RESULT", f"{locator} fields or field order are invalid")


def _array(value: Any, locator: str, maximum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ResultError("MALFORMED_RESULT", f"{locator} must be an array with at most {maximum} items")
    return value


def _string(value: Any, locator: str, maximum: int = MAX_SUMMARY_BYTES, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value) or len(value.encode("utf-8")) > maximum:
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise ResultError("MALFORMED_RESULT", f"{locator} must be a bounded {qualifier} string")
    return value


def _identifier(value: Any, locator: str) -> str:
    result = _string(value, locator, 128)
    if not ID_PATTERN.fullmatch(result):
        raise ResultError("MALFORMED_RESULT", f"{locator} is not a valid identifier")
    return result


def _string_list(value: Any, locator: str, *, require_nonempty: bool = False) -> list[str]:
    raw = _array(value, locator, MAX_REFS_PER_RECORD)
    result = [_string(item, f"{locator}[{index}]", MAX_LOCATOR_BYTES) for index, item in enumerate(raw)]
    if require_nonempty and not result:
        raise ResultError("MALFORMED_RESULT", f"{locator} must not be empty")
    if len(set(result)) != len(result):
        raise ResultError("MALFORMED_RESULT", f"{locator} contains duplicates")
    return result


def _validate_payload_bound(value: Mapping[str, Any]) -> None:
    try:
        size = len(_canonical_json(value))
    except (TypeError, ValueError) as exc:
        raise ResultError("MALFORMED_RESULT", f"request is not JSON serializable: {exc}") from exc
    if size > MAX_REQUEST_BYTES:
        raise ResultError("MALFORMED_RESULT", f"request exceeds {MAX_REQUEST_BYTES} bytes")


def _line_content(line: bytes) -> bytes:
    if line.endswith(b"\r\n"):
        return line[:-2]
    if line.endswith(b"\n") or line.endswith(b"\r"):
        return line[:-1]
    return line


def acceptance_criteria_from_ticket(path: Path | str) -> list[dict[str, Any]]:
    """Return exact ordered top-level AC locators from current Ticket bytes."""
    ticket = Path(path)
    try:
        raw = ticket.read_bytes()
        raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ResultError("PLANNING_INPUT_CHANGED", f"cannot read Ticket Acceptance Criteria: {exc}") from exc
    lines = raw.splitlines(keepends=True)
    headings = [index for index, line in enumerate(lines) if _line_content(line) == b"## Acceptance Criteria"]
    if len(headings) != 1:
        raise ResultError("MALFORMED_TICKET", "Ticket must contain one exact ## Acceptance Criteria heading")
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
        raise ResultError("MALFORMED_TICKET", "Acceptance Criteria must contain top-level list items")

    criteria_bytes: list[bytes] = []
    current: list[bytes] = []
    for line in body:
        content = _line_content(line)
        if content.startswith(b"- "):
            if not content[2:].strip():
                raise ResultError("MALFORMED_TICKET", "Acceptance Criterion item must not be empty")
            if current:
                criteria_bytes.append(b"".join(current))
            current = [line]
        elif current and (content == b"" or content.startswith(b"  ")):
            current.append(line)
        else:
            raise ResultError(
                "MALFORMED_TICKET",
                "Acceptance Criteria allows only exact top-level '- ' items and two-space continuations",
            )
    if current:
        criteria_bytes.append(b"".join(current))
    if not criteria_bytes or len(criteria_bytes) > MAX_CRITERIA:
        raise ResultError("MALFORMED_TICKET", f"Acceptance Criteria must contain 1-{MAX_CRITERIA} items")
    return [
        {
            "criterionIndex": index,
            "criterionRawSha256": hashlib.sha256(raw_item).hexdigest(),
        }
        for index, raw_item in enumerate(criteria_bytes, start=1)
    ]


def acceptance_criteria_digest(criteria: list[dict[str, Any]]) -> str:
    ordered = [
        {
            "criterionIndex": criterion["criterionIndex"],
            "criterionRawSha256": criterion["criterionRawSha256"],
        }
        for criterion in criteria
    ]
    return hashlib.sha256(_canonical_json(ordered)).hexdigest()


def planning_seal_digest(seal: Mapping[str, Any]) -> str:
    seal_mapping = _mapping(seal, "planningSeal")
    _fields(seal_mapping, set(PLANNING_SEAL_FIELDS), "planningSeal")
    blockers = _array(seal_mapping["blockerFiles"], "planningSeal.blockerFiles", MAX_AUTHORITY_BINDINGS)
    canonical_blockers: list[dict[str, Any]] = []
    for index, raw_blocker in enumerate(blockers):
        blocker = _mapping(raw_blocker, f"planningSeal.blockerFiles[{index}]")
        _fields(blocker, set(BLOCKER_FIELDS), f"planningSeal.blockerFiles[{index}]")
        canonical_blockers.append(
            {
                "path": blocker["path"],
                "sha256": blocker["sha256"],
                "status": blocker["status"],
            }
        )
    canonical = {
        "ticketPath": seal_mapping["ticketPath"],
        "ticketSha256": seal_mapping["ticketSha256"],
        "specPath": seal_mapping["specPath"],
        "specSha256": seal_mapping["specSha256"],
        "blockerFiles": canonical_blockers,
    }
    return hashlib.sha256(_canonical_json(canonical)).hexdigest()


def _canonical_regular_file(raw_path: Any, locator: str, changed_code: str) -> Path:
    path_value = _string(raw_path, locator, MAX_LOCATOR_BYTES)
    path = Path(path_value)
    if not path.is_absolute():
        raise ResultError("MALFORMED_RESULT", f"{locator} must be absolute")
    try:
        canonical = path.resolve(strict=True)
    except OSError as exc:
        raise ResultError(changed_code, f"cannot resolve {locator}: {exc}") from exc
    if str(canonical) != path_value or not canonical.is_file():
        raise ResultError(changed_code, f"{locator} is not the same canonical regular file")
    return canonical


def _validate_planning_seal(value: Any) -> dict[str, Any]:
    seal = _mapping(value, "planningSeal")
    _ordered_fields(seal, PLANNING_SEAL_FIELDS, "planningSeal")
    normalized: dict[str, Any] = {}
    for role, path_key, digest_key in (
        ("Ticket", "ticketPath", "ticketSha256"),
        ("Spec", "specPath", "specSha256"),
    ):
        path = _canonical_regular_file(seal[path_key], f"planningSeal.{path_key}", "PLANNING_INPUT_CHANGED")
        digest = _string(seal[digest_key], f"planningSeal.{digest_key}", 64)
        if not SHA256_PATTERN.fullmatch(digest):
            raise ResultError("MALFORMED_RESULT", f"{role} planning digest is malformed")
        if _sha256(path) != digest:
            raise ResultError("PLANNING_INPUT_CHANGED", f"{role} digest changed")
        normalized[path_key] = str(path)
        normalized[digest_key] = digest
    blockers = _array(seal["blockerFiles"], "planningSeal.blockerFiles", MAX_AUTHORITY_BINDINGS)
    normalized_blockers: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for index, raw_blocker in enumerate(blockers):
        blocker = _mapping(raw_blocker, f"planningSeal.blockerFiles[{index}]")
        _ordered_fields(blocker, BLOCKER_FIELDS, f"planningSeal.blockerFiles[{index}]")
        path = _canonical_regular_file(
            blocker["path"], f"planningSeal.blockerFiles[{index}].path", "PLANNING_INPUT_CHANGED"
        )
        digest = _string(blocker["sha256"], f"planningSeal.blockerFiles[{index}].sha256", 64)
        status = _string(blocker["status"], f"planningSeal.blockerFiles[{index}].status", 16)
        if not SHA256_PATTERN.fullmatch(digest) or status not in {"resolved", "done"}:
            raise ResultError("MALFORMED_RESULT", f"planningSeal.blockerFiles[{index}] is malformed")
        if str(path) in seen_paths:
            raise ResultError("MALFORMED_RESULT", "planningSeal.blockerFiles contains duplicate canonical paths")
        if _sha256(path) != digest:
            raise ResultError("PLANNING_INPUT_CHANGED", f"blocker changed: {path}")
        seen_paths.add(str(path))
        normalized_blockers.append({"path": str(path), "sha256": digest, "status": status})
    normalized["blockerFiles"] = normalized_blockers
    return normalized


def _validate_supplemental_authorities(value: Any) -> tuple[list[dict[str, str]], set[str]]:
    raw_bindings = _array(value, "completionRecord.supplementalLocalAuthorityBindings", MAX_AUTHORITY_BINDINGS)
    bindings: list[dict[str, str]] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, raw_binding in enumerate(raw_bindings):
        locator = f"completionRecord.supplementalLocalAuthorityBindings[{index}]"
        binding = _mapping(raw_binding, locator)
        _fields(binding, {"authorityBindingId", "role", "canonicalPath", "rawSha256"}, locator)
        binding_id = _identifier(binding["authorityBindingId"], f"{locator}.authorityBindingId")
        role = _string(binding["role"], f"{locator}.role", 128)
        path = _canonical_regular_file(binding["canonicalPath"], f"{locator}.canonicalPath", "AUTHORITY_CHANGED")
        digest = _string(binding["rawSha256"], f"{locator}.rawSha256", 64)
        if not SHA256_PATTERN.fullmatch(digest):
            raise ResultError("MALFORMED_RESULT", f"{locator}.rawSha256 is malformed")
        if binding_id in ids or str(path) in paths:
            raise ResultError("MALFORMED_RESULT", "supplemental authority id or canonical path is duplicated")
        if _sha256(path) != digest:
            raise ResultError("AUTHORITY_CHANGED", f"supplemental authority changed: {path}")
        ids.add(binding_id)
        paths.add(str(path))
        bindings.append(
            {
                "authorityBindingId": binding_id,
                "role": role,
                "canonicalPath": str(path),
                "rawSha256": digest,
            }
        )
    return bindings, ids


def _validate_authority_refs(
    raw_locators: Any,
    raw_binding_refs: Any,
    locator: str,
    authority_ids: set[str],
    used_authorities: set[str],
    *,
    require_authority: bool = False,
) -> tuple[list[str], list[str]]:
    locators = _string_list(raw_locators, f"{locator}.authorityLocators")
    refs = _string_list(raw_binding_refs, f"{locator}.authorityBindingRefs")
    unknown = set(refs) - authority_ids
    if unknown:
        raise ResultError("MALFORMED_RESULT", f"{locator} references unknown authority bindings")
    if require_authority and not locators and not refs:
        raise ResultError("MALFORMED_RESULT", f"{locator} must identify entry-point authority")
    used_authorities.update(refs)
    return locators, refs


def _validate_completion_record(
    value: Any,
    criteria: list[dict[str, Any]],
    criteria_digest: str,
    seal_digest: str,
    final_identity: str,
) -> dict[str, Any]:
    record = _mapping(value, "completionRecord")
    _fields(
        record,
        {
            "acceptanceCriteriaDigest",
            "supplementalLocalAuthorityBindings",
            "coverage",
            "sourceEvidence",
            "runtimeObservations",
            "unresolvedItems",
        },
        "completionRecord",
    )
    supplied_digest = _string(record["acceptanceCriteriaDigest"], "completionRecord.acceptanceCriteriaDigest", 64)
    if supplied_digest != criteria_digest:
        raise ResultError("ACCEPTANCE_CRITERIA_MISMATCH", "Acceptance Criteria digest is not current")

    authorities, authority_ids = _validate_supplemental_authorities(record["supplementalLocalAuthorityBindings"])
    used_authorities: set[str] = set()
    raw_coverage = _array(record["coverage"], "completionRecord.coverage", MAX_CRITERIA)
    if len(raw_coverage) != len(criteria):
        raise ResultError("INCOMPLETE_COVERAGE", "coverage must contain every current Acceptance Criterion")

    coverage: list[dict[str, Any]] = []
    requirements: dict[str, dict[str, Any]] = {}
    for offset, (raw_criterion, expected) in enumerate(zip(raw_coverage, criteria)):
        locator = f"completionRecord.coverage[{offset}]"
        criterion = _mapping(raw_criterion, locator)
        _fields(criterion, {"criterionIndex", "criterionRawSha256", "state", "evidenceRequirements"}, locator)
        criterion_index = criterion["criterionIndex"]
        if (
            isinstance(criterion_index, bool)
            or not isinstance(criterion_index, int)
            or criterion_index != expected["criterionIndex"]
            or criterion["criterionRawSha256"] != expected["criterionRawSha256"]
        ):
            raise ResultError("ACCEPTANCE_CRITERIA_MISMATCH", f"{locator} does not match current Ticket bytes")
        if criterion["state"] != "ESTABLISHED":
            raise ResultError("INCOMPLETE_COVERAGE", f"{locator}.state must be ESTABLISHED")
        raw_requirements = _array(criterion["evidenceRequirements"], f"{locator}.evidenceRequirements", MAX_REQUIREMENTS)
        if not raw_requirements:
            raise ResultError("INCOMPLETE_COVERAGE", f"{locator} has no Evidence Requirement")
        normalized_requirements: list[dict[str, Any]] = []
        for req_offset, raw_requirement in enumerate(raw_requirements):
            req_locator = f"{locator}.evidenceRequirements[{req_offset}]"
            requirement = _mapping(raw_requirement, req_locator)
            _fields(requirement, {"requirementId", "kind", "state", "evidenceRefs"}, req_locator)
            requirement_id = _identifier(requirement["requirementId"], f"{req_locator}.requirementId")
            kind = requirement["kind"]
            if kind not in {"SOURCE", "RUNTIME"}:
                raise ResultError("MALFORMED_RESULT", f"{req_locator}.kind is invalid")
            if requirement["state"] != "ESTABLISHED":
                raise ResultError("INCOMPLETE_COVERAGE", f"{req_locator}.state must be ESTABLISHED")
            refs = _string_list(requirement["evidenceRefs"], f"{req_locator}.evidenceRefs", require_nonempty=True)
            if requirement_id in requirements:
                raise ResultError("MALFORMED_RESULT", f"duplicate requirementId: {requirement_id}")
            requirements[requirement_id] = {"kind": kind, "evidenceRefs": refs}
            normalized_requirements.append(
                {"requirementId": requirement_id, "kind": kind, "state": "ESTABLISHED", "evidenceRefs": refs}
            )
        coverage.append(
            {
                "criterionIndex": expected["criterionIndex"],
                "criterionRawSha256": expected["criterionRawSha256"],
                "state": "ESTABLISHED",
                "evidenceRequirements": normalized_requirements,
            }
        )
    if len(requirements) > MAX_REQUIREMENTS:
        raise ResultError("MALFORMED_RESULT", f"Completion Record exceeds {MAX_REQUIREMENTS} requirements")

    evidence: dict[str, dict[str, Any]] = {}
    source_evidence: list[dict[str, Any]] = []
    for index, raw_evidence in enumerate(
        _array(record["sourceEvidence"], "completionRecord.sourceEvidence", MAX_EVIDENCE_RECORDS)
    ):
        locator = f"completionRecord.sourceEvidence[{index}]"
        item = _mapping(raw_evidence, locator)
        _fields(
            item,
            {
                "evidenceId",
                "coveredRequirementIds",
                "authorityLocators",
                "authorityBindingRefs",
                "sourceIdentity",
                "reviewSummary",
            },
            locator,
        )
        evidence_id = _identifier(item["evidenceId"], f"{locator}.evidenceId")
        covered = _string_list(item["coveredRequirementIds"], f"{locator}.coveredRequirementIds", require_nonempty=True)
        authority_locators, authority_refs = _validate_authority_refs(
            item["authorityLocators"], item["authorityBindingRefs"], locator, authority_ids, used_authorities
        )
        if item["sourceIdentity"] != final_identity:
            raise ResultError("SOURCE_IDENTITY_MISMATCH", f"{locator}.sourceIdentity is not final")
        if evidence_id in evidence:
            raise ResultError("MALFORMED_RESULT", f"duplicate evidenceId: {evidence_id}")
        evidence[evidence_id] = {"kind": "SOURCE", "coveredRequirementIds": covered}
        source_evidence.append(
            {
                "evidenceId": evidence_id,
                "coveredRequirementIds": covered,
                "authorityLocators": authority_locators,
                "authorityBindingRefs": authority_refs,
                "sourceIdentity": final_identity,
                "reviewSummary": _string(item["reviewSummary"], f"{locator}.reviewSummary"),
            }
        )

    runtime_observations: list[dict[str, Any]] = []
    for index, raw_observation in enumerate(
        _array(record["runtimeObservations"], "completionRecord.runtimeObservations", MAX_EVIDENCE_RECORDS)
    ):
        locator = f"completionRecord.runtimeObservations[{index}]"
        item = _mapping(raw_observation, locator)
        _fields(
            item,
            {
                "observationId",
                "coveredRequirementIds",
                "entryPointAuthority",
                "executionTargetBinding",
                "redactedInvocationSummary",
                "expectedEffectSummary",
                "observedEffectSummary",
                "observationMode",
                "readbackSummaryOrDigest",
                "planningSealDigest",
                "sourceIdentityBefore",
                "sourceIdentityAfter",
                "projectDeltaBinding",
                "cleanupDisposition",
                "observedAt",
            },
            locator,
        )
        observation_id = _identifier(item["observationId"], f"{locator}.observationId")
        covered = _string_list(item["coveredRequirementIds"], f"{locator}.coveredRequirementIds", require_nonempty=True)
        if observation_id in evidence:
            raise ResultError("MALFORMED_RESULT", f"duplicate evidenceId: {observation_id}")

        entry_authority = _mapping(item["entryPointAuthority"], f"{locator}.entryPointAuthority")
        _fields(entry_authority, {"authorityLocators", "authorityBindingRefs"}, f"{locator}.entryPointAuthority")
        entry_locators, entry_refs = _validate_authority_refs(
            entry_authority["authorityLocators"],
            entry_authority["authorityBindingRefs"],
            f"{locator}.entryPointAuthority",
            authority_ids,
            used_authorities,
            require_authority=True,
        )

        target = _mapping(item["executionTargetBinding"], f"{locator}.executionTargetBinding")
        _fields(
            target,
            {
                "mode",
                "authorityLocators",
                "finalSourceIdentity",
                "targetIdentityOrRevision",
                "bindingSummaryOrDigest",
            },
            f"{locator}.executionTargetBinding",
        )
        mode = target["mode"]
        if mode not in {"CURRENT_PROJECT_ROOT", "SOURCE_BOUND_MATERIALIZATION", "REVISION_BOUND_TARGET"}:
            raise ResultError("MALFORMED_RESULT", f"{locator}.executionTargetBinding.mode is invalid")
        target_locators = _string_list(
            target["authorityLocators"], f"{locator}.executionTargetBinding.authorityLocators"
        )
        if target["finalSourceIdentity"] != final_identity:
            raise ResultError("SOURCE_IDENTITY_MISMATCH", f"{locator} target is not bound to final source")
        target_identity = _string(
            target["targetIdentityOrRevision"], f"{locator}.executionTargetBinding.targetIdentityOrRevision", 512
        )
        if mode in {"CURRENT_PROJECT_ROOT", "SOURCE_BOUND_MATERIALIZATION"} and target_identity != final_identity:
            raise ResultError("SOURCE_IDENTITY_MISMATCH", f"{locator} target identity is not final")
        if mode == "REVISION_BOUND_TARGET" and not target_locators:
            raise ResultError("MALFORMED_RESULT", f"{locator} revision target requires authority locators")

        if item["planningSealDigest"] != seal_digest:
            raise ResultError("PLANNING_INPUT_CHANGED", f"{locator}.planningSealDigest is not current")
        if item["sourceIdentityBefore"] != final_identity or item["sourceIdentityAfter"] != final_identity:
            raise ResultError("SOURCE_IDENTITY_MISMATCH", f"{locator} source identities are not final")

        delta = _mapping(item["projectDeltaBinding"], f"{locator}.projectDeltaBinding")
        _fields(
            delta,
            {
                "ownershipSnapshotIdentityBefore",
                "ownershipSnapshotIdentityAfter",
                "changedPathCount",
                "deltaSummaryOrDigest",
                "disposition",
            },
            f"{locator}.projectDeltaBinding",
        )
        before = delta["ownershipSnapshotIdentityBefore"]
        after = delta["ownershipSnapshotIdentityAfter"]
        if not isinstance(before, str) or not IDENTITY_PATTERN.fullmatch(before) or before != after:
            raise ResultError("PROJECT_DELTA_NOT_CLEAR", f"{locator} ownership identities differ")
        if isinstance(delta["changedPathCount"], bool) or delta["changedPathCount"] != 0 or delta["disposition"] != "CLEAR":
            raise ResultError("PROJECT_DELTA_NOT_CLEAR", f"{locator} project delta is not clear")

        cleanup = _mapping(item["cleanupDisposition"], f"{locator}.cleanupDisposition")
        _fields(
            cleanup,
            {"required", "state", "authorityOrRationale", "readbackSummaryOrDigest"},
            f"{locator}.cleanupDisposition",
        )
        required = cleanup["required"]
        if not isinstance(required, bool):
            raise ResultError("MALFORMED_RESULT", f"{locator}.cleanupDisposition.required must be boolean")
        cleanup_state = cleanup["state"]
        cleanup_authority = _string(
            cleanup["authorityOrRationale"], f"{locator}.cleanupDisposition.authorityOrRationale"
        )
        cleanup_readback = _string(
            cleanup["readbackSummaryOrDigest"],
            f"{locator}.cleanupDisposition.readbackSummaryOrDigest",
            allow_empty=not required,
        )
        if required and cleanup_state != "COMPLETE":
            raise ResultError("INCOMPLETE_CLEANUP", f"{locator} required cleanup is not COMPLETE")
        if not required and cleanup_state != "NOT_REQUIRED":
            raise ResultError("INCOMPLETE_CLEANUP", f"{locator} cleanup state must be NOT_REQUIRED")

        observation_mode = item["observationMode"]
        if observation_mode not in {"DIRECT_RESULT", "INDEPENDENT_READBACK"}:
            raise ResultError("MALFORMED_RESULT", f"{locator}.observationMode is invalid")
        observed_at = _string(item["observedAt"], f"{locator}.observedAt", 128)
        try:
            parsed_time = datetime.fromisoformat(observed_at)
        except ValueError as exc:
            raise ResultError("MALFORMED_RESULT", f"{locator}.observedAt is not ISO-8601") from exc
        if parsed_time.tzinfo is None:
            raise ResultError("MALFORMED_RESULT", f"{locator}.observedAt must include a timezone")

        evidence[observation_id] = {"kind": "RUNTIME", "coveredRequirementIds": covered}
        runtime_observations.append(
            {
                "observationId": observation_id,
                "coveredRequirementIds": covered,
                "entryPointAuthority": {
                    "authorityLocators": entry_locators,
                    "authorityBindingRefs": entry_refs,
                },
                "executionTargetBinding": {
                    "mode": mode,
                    "authorityLocators": target_locators,
                    "finalSourceIdentity": final_identity,
                    "targetIdentityOrRevision": target_identity,
                    "bindingSummaryOrDigest": _string(
                        target["bindingSummaryOrDigest"],
                        f"{locator}.executionTargetBinding.bindingSummaryOrDigest",
                    ),
                },
                "redactedInvocationSummary": _string(
                    item["redactedInvocationSummary"], f"{locator}.redactedInvocationSummary"
                ),
                "expectedEffectSummary": _string(
                    item["expectedEffectSummary"], f"{locator}.expectedEffectSummary"
                ),
                "observedEffectSummary": _string(
                    item["observedEffectSummary"], f"{locator}.observedEffectSummary"
                ),
                "observationMode": observation_mode,
                "readbackSummaryOrDigest": _string(
                    item["readbackSummaryOrDigest"], f"{locator}.readbackSummaryOrDigest"
                ),
                "planningSealDigest": seal_digest,
                "sourceIdentityBefore": final_identity,
                "sourceIdentityAfter": final_identity,
                "projectDeltaBinding": {
                    "ownershipSnapshotIdentityBefore": before,
                    "ownershipSnapshotIdentityAfter": after,
                    "changedPathCount": 0,
                    "deltaSummaryOrDigest": _string(
                        delta["deltaSummaryOrDigest"], f"{locator}.projectDeltaBinding.deltaSummaryOrDigest"
                    ),
                    "disposition": "CLEAR",
                },
                "cleanupDisposition": {
                    "required": required,
                    "state": cleanup_state,
                    "authorityOrRationale": cleanup_authority,
                    "readbackSummaryOrDigest": cleanup_readback,
                },
                "observedAt": observed_at,
            }
        )

    for evidence_id, item in evidence.items():
        for requirement_id in item["coveredRequirementIds"]:
            requirement = requirements.get(requirement_id)
            if requirement is None or requirement["kind"] != item["kind"]:
                raise ResultError("MALFORMED_RESULT", f"{evidence_id} covers an unknown or wrong-kind requirement")
    for requirement_id, requirement in requirements.items():
        expected_refs = {
            evidence_id
            for evidence_id, item in evidence.items()
            if requirement_id in item["coveredRequirementIds"] and item["kind"] == requirement["kind"]
        }
        supplied_refs = set(requirement["evidenceRefs"])
        if supplied_refs != expected_refs or not expected_refs:
            raise ResultError("INCOMPLETE_COVERAGE", f"{requirement_id} evidence references are incomplete or inconsistent")
    if set(evidence) != {
        evidence_ref for requirement in requirements.values() for evidence_ref in requirement["evidenceRefs"]
    }:
        raise ResultError("MALFORMED_RESULT", "unreferenced evidence record is not allowed")
    if used_authorities != authority_ids:
        raise ResultError("MALFORMED_RESULT", "unreferenced supplemental authority binding is not allowed")

    unresolved = _array(record["unresolvedItems"], "completionRecord.unresolvedItems", MAX_REQUIREMENTS)
    if unresolved:
        raise ResultError("UNRESOLVED_ITEMS", "completionRecord.unresolvedItems must be empty")
    return {
        "acceptanceCriteriaDigest": criteria_digest,
        "supplementalLocalAuthorityBindings": authorities,
        "coverage": coverage,
        "sourceEvidence": source_evidence,
        "runtimeObservations": runtime_observations,
        "unresolvedItems": [],
    }


class ResultStore:
    def __init__(
        self,
        result_root: Path | str = DEFAULT_RESULT_ROOT,
        capsule_store_root: Path | str | None = None,
    ) -> None:
        self.result_root = Path(result_root).expanduser().resolve()
        self.result_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.result_root, 0o700)
        self.capsule_store = baseline_capsule.CapsuleStore(
            capsule_store_root or os.environ.get("BASELINE_CAPSULE_STORE", baseline_capsule.DEFAULT_STORE_ROOT)
        )

    def _publication_checkpoint(self, stage: str) -> None:
        """Test seam for deterministic mutation at publication boundaries."""

    def _validate_publication_currentness(
        self,
        planning_seal: Mapping[str, Any],
        criteria: list[dict[str, Any]],
        supplemental_authorities: list[dict[str, str]],
        project_root: Path,
        final_identity: str,
    ) -> None:
        current_seal = _validate_planning_seal(planning_seal)
        if current_seal != planning_seal:
            raise ResultError("PLANNING_INPUT_CHANGED", "PlanningInputSeal identity changed during publication")
        if acceptance_criteria_from_ticket(current_seal["ticketPath"]) != criteria:
            raise ResultError("PLANNING_INPUT_CHANGED", "Ticket Acceptance Criteria changed during publication")
        current_authorities, _ = _validate_supplemental_authorities(supplemental_authorities)
        if current_authorities != supplemental_authorities:
            raise ResultError("AUTHORITY_CHANGED", "supplemental authority changed during publication")
        observed = baseline_capsule.capture_identity(project_root)["sourceIdentity"]
        if observed != final_identity:
            raise ResultError(
                "SOURCE_IDENTITY_MISMATCH",
                f"final source changed during publication: expected {final_identity}, observed {observed}",
            )

    def _publish_stable(
        self,
        token: str,
        result: Mapping[str, Any],
        validate_currentness: Callable[[], None],
    ) -> None:
        pending = self.result_root / f".pending-{token}"
        published = self.result_root / f"{token}.json"
        payload = _result_json(result)
        linked = False
        try:
            self._publication_checkpoint("before_candidate_write")
            validate_currentness()
            _write_exclusive(pending, payload)
            if pending.read_bytes() != payload:
                raise ResultError("PUBLICATION_FAILED", "pending result readback differs")

            self._publication_checkpoint("after_candidate_write")
            validate_currentness()
            self._publication_checkpoint("before_commit")
            validate_currentness()
            try:
                os.link(pending, published)
            except FileExistsError as exc:
                raise ResultError("IMMUTABLE_RESULT_EXISTS", f"refusing to overwrite {published}") from exc
            linked = True
            pending.unlink()
            _fsync_directory(self.result_root)

            self._publication_checkpoint("after_commit")
            validate_currentness()
            if published.read_bytes() != payload:
                raise ResultError("PUBLICATION_FAILED", "published result readback differs")
        except Exception as publication_error:
            cleanup_errors: list[str] = []
            removed = False
            for path in (published if linked else None, pending):
                if path is not None:
                    try:
                        existed = path.exists()
                        path.unlink(missing_ok=True)
                        removed = removed or existed
                    except OSError as exc:
                        cleanup_errors.append(f"cannot remove {path.name}: {exc}")
            if removed:
                try:
                    _fsync_directory(self.result_root)
                except OSError as exc:
                    cleanup_errors.append(f"cannot fsync result directory: {exc}")
            if cleanup_errors:
                detail = "; ".join(cleanup_errors)
                raise ResultError("PUBLICATION_CLEANUP_FAILED", detail[:MAX_SUMMARY_BYTES]) from publication_error
            raise

    def publish(self, request: Mapping[str, Any]) -> dict[str, Any]:
        _validate_payload_bound(request)
        fields = {
            "protocolVersion",
            "projectRoot",
            "planningSeal",
            "capsuleRef",
            "finalSourceIdentity",
            "completionRecord",
        }
        _fields(request, fields, "ImplementationResult request")
        if request["protocolVersion"] != PROTOCOL_VERSION:
            raise ResultError("UNKNOWN_PROTOCOL_VERSION", f"protocolVersion is not {PROTOCOL_VERSION}")
        capsule_ref = str(request["capsuleRef"])
        final_identity = str(request["finalSourceIdentity"])
        if not CAPSULE_REF_PATTERN.fullmatch(capsule_ref) or not IDENTITY_PATTERN.fullmatch(final_identity):
            raise ResultError("MALFORMED_RESULT", "capsuleRef or finalSourceIdentity is malformed")
        try:
            project_root = Path(str(request["projectRoot"])).resolve(strict=True)
        except OSError as exc:
            raise ResultError("INVALID_PROJECT_ROOT", f"cannot resolve project root: {exc}") from exc
        if not project_root.is_dir() or str(project_root) != str(request["projectRoot"]):
            raise ResultError("INVALID_PROJECT_ROOT", "projectRoot must be one canonical absolute directory")
        if self.result_root == project_root or self.result_root.is_relative_to(project_root):
            raise ResultError("INVALID_RESULT_ROOT", "ImplementationResult store must be outside projectRoot")

        planning_seal = _validate_planning_seal(request["planningSeal"])
        criteria = acceptance_criteria_from_ticket(planning_seal["ticketPath"])
        criteria_digest = acceptance_criteria_digest(criteria)
        seal_digest = planning_seal_digest(planning_seal)
        completion_record = _validate_completion_record(
            request["completionRecord"], criteria, criteria_digest, seal_digest, final_identity
        )

        view = self.capsule_store.acquire_read(capsule_ref)
        try:
            if view["canonicalProjectRoot"] != str(project_root):
                raise ResultError("CAPSULE_PROJECT_MISMATCH", "Capsule project root differs")
            observed = baseline_capsule.capture_identity(project_root)["sourceIdentity"]
            if observed != final_identity:
                raise ResultError(
                    "SOURCE_IDENTITY_MISMATCH",
                    f"final source changed: expected {final_identity}, observed {observed}",
                )
            token = uuid.uuid4().hex
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "implementationResultRef": f"implementation:v3:{token}",
                "implementationStatus": "IMPLEMENTATION_COMPLETE",
                "projectRoot": str(project_root),
                "planningSeal": planning_seal,
                "planningSealDigest": seal_digest,
                "capsuleRef": capsule_ref,
                "baselineSourceIdentity": view["baselineSourceIdentity"],
                "finalSourceIdentity": final_identity,
                "completionRecord": completion_record,
                "completedAt": datetime.now(timezone.utc).isoformat(),
            }
            self._publish_stable(
                token,
                result,
                lambda: self._validate_publication_currentness(
                    planning_seal,
                    criteria,
                    completion_record["supplementalLocalAuthorityBindings"],
                    project_root,
                    final_identity,
                ),
            )
            return result
        finally:
            self.capsule_store.release_read(view["readLeaseId"])


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_REQUEST_BYTES:
            raise ResultError("MALFORMED_RESULT", f"request exceeds {MAX_REQUEST_BYTES} bytes")
        value = json.loads(path.read_text(encoding="utf-8"))
    except ResultError:
        raise
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ResultError("MALFORMED_RESULT", f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ResultError("MALFORMED_RESULT", f"expected an object in {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-root", default=os.environ.get("IMPLEMENTATION_RESULT_STORE", str(DEFAULT_RESULT_ROOT)))
    parser.add_argument("--capsule-store", default=os.environ.get("BASELINE_CAPSULE_STORE"))
    parser.add_argument("publish")
    parser.add_argument("--request", required=True)
    args = parser.parse_args(argv)
    try:
        result = ResultStore(args.result_root, args.capsule_store).publish(_read_json(Path(args.request)))
    except (ResultError, baseline_capsule.CapsuleError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
