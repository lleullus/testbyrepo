#!/usr/bin/env python3
"""Owner-controlled sealed verification runs and verification-result-v1 publication.

The caller may describe a concrete plan and provide semantic criterion verdicts.  It
cannot submit execution outcomes, select attempts, change a sealed request, or choose
the aggregate public status.  PROCESS is the deliberately small MVP executor.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_ROOT = REPOSITORY_ROOT / "implementation-lead"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workflow_store = _load_module(
    "verification_workflow_store",
    IMPLEMENTATION_ROOT / "tools/workflow-store/workflow_store.py",
)
handoff_contract = _load_module(
    "verification_handoff_contract",
    IMPLEMENTATION_ROOT / "tools/implementation-result/implementation_result.py",
)
baseline_capsule = handoff_contract.baseline_capsule
executable_identity = _load_module(
    "verification_executable_identity",
    Path(__file__).resolve().with_name("executable_identity.py"),
)


PROTOCOL_VERSION = "verification-result-v1"
PROCESS_EXECUTOR_VERSION = "process-v3"
PROCESS_ENVIRONMENT_POLICY = "SEALED_EMPTY_BASE_V1"
RUN_REF_PATTERN = re.compile(r"^verification:run:v1:[a-f0-9]{32}$")
RESULT_REF_PATTERN = re.compile(r"^verification:result:v1:[a-f0-9]{32}$")
HANDOFF_REF_PATTERN = re.compile(r"^implementation:handoff:v1:[a-f0-9]{32}$")
CAPSULE_REF_PATTERN = re.compile(r"^capsule:v1:[a-f0-9]{32}$")
DELTA_REF_PATTERN = re.compile(r"^implementation:delta:v1:[a-f0-9]{32}$")
CLAIM_REF_PATTERN = re.compile(r"^claim:v1:[a-f0-9]{32}$")
AUTHORIZATION_REF_PATTERN = re.compile(r"^authorization:v1:[a-f0-9]{32}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SOURCE_IDENTITY_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ENV_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")

STEP_ROLES = {"ACTION", "READBACK", "CLEANUP"}
TARGET_REQUIREMENTS = {"RETAIN", "DISPOSABLE", "NOT_APPLICABLE"}
CRITERION_VERDICTS = {"SATISFIED", "CONTRADICTED", "INCONCLUSIVE", "BLOCKED"}
TERMINAL_STATUSES = {"VERIFIED", "VERIFICATION_FAILED", "INCOMPLETE", "BLOCKED"}
AMBIGUOUS_ACTION_STATUSES = {
    "TIMED_OUT",
    "TOOL_ERROR",
    "IDENTITY_DRIFT",
    "EXECUTABLE_IDENTITY_DRIFT",
    "ATTEMPT_RECORD_INCOMPLETE",
}
PROCESS_OBSERVATION_UNCERTAINTY_STATUSES = {"TIMED_OUT", "TOOL_ERROR"}

MAX_DRAFT_BYTES = 512 * 1024
MAX_PLAN_ITEMS = 256
MAX_STEPS_PER_FLOW = 64
MAX_STRING_BYTES = 16 * 1024
MAX_RATIONALE_BYTES = 32 * 1024
MAX_ARGV_PARTS = 256
MAX_ENVIRONMENT_KEYS = 128
MAX_OUTPUT_BYTES = 64 * 1024
MAX_PROCESS_TIMEOUT_SECONDS = 60
MAX_POLL_ATTEMPTS = 10
MAX_POLL_INTERVAL_MS = 2_000

LIVE_EXECUTION_LOCK_DIRECTORY = ".verification-live-step-locks-v1"


class VerificationError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class _PreflightTerminal(RuntimeError):
    def __init__(self, status: str, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.reason_code = reason_code
        self.message = message


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"value is not JSON serializable: {exc}") from exc
    if len(encoded) > MAX_DRAFT_BYTES:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "verification value is oversized")
    return encoded


def _decode_json(value: Any, locator: str) -> Any:
    try:
        return json.loads(bytes(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise VerificationError("STORE_CORRUPT", f"{locator} is unreadable") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _mapping(value: Any, locator: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} must be an object")
    return value


def _fields(value: Mapping[str, Any], expected: set[str], locator: str) -> None:
    if set(value) != expected:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} fields are invalid")


def _bounded_string(value: Any, locator: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} must be a string")
    if (not allow_empty and not value) or len(value.encode("utf-8")) > MAX_STRING_BYTES or "\x00" in value:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} is invalid")
    return value


def _identifier(value: Any, locator: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} is not a bounded identifier")
    return value


def _sha256(value: Any, locator: str) -> str:
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} is not a lowercase SHA-256")
    return value


def _criterion_ref(raw: Any, locator: str) -> dict[str, Any]:
    value = _mapping(raw, locator)
    _fields(value, {"criterionIndex", "criterionRawSha256"}, locator)
    index = value["criterionIndex"]
    if isinstance(index, bool) or not isinstance(index, int) or index <= 0:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.criterionIndex is invalid")
    return {
        "criterionIndex": index,
        "criterionRawSha256": _sha256(
            value["criterionRawSha256"], f"{locator}.criterionRawSha256"
        ),
    }


def _criterion_refs(raw: Any, locator: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw or len(raw) > MAX_PLAN_ITEMS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} must be a non-empty bounded array")
    result = [_criterion_ref(item, f"{locator}[{index}]") for index, item in enumerate(raw)]
    keys = [(item["criterionIndex"], item["criterionRawSha256"]) for item in result]
    if len(set(keys)) != len(keys):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} contains duplicates")
    return result


def _id_list(raw: Any, locator: str) -> list[str]:
    if not isinstance(raw, list) or len(raw) > MAX_PLAN_ITEMS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} must be a bounded array")
    result = [_identifier(value, f"{locator}[{index}]") for index, value in enumerate(raw)]
    if len(set(result)) != len(result):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} contains duplicates")
    return result


def _basis_anchor(raw: Any, locator: str) -> dict[str, Any]:
    value = _mapping(raw, locator)
    _fields(value, {"canonicalPath", "rawSha256", "startLine", "endLine", "selectedTextSha256"}, locator)
    path = _bounded_string(value["canonicalPath"], f"{locator}.canonicalPath")
    if not Path(path).is_absolute():
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.canonicalPath must be absolute")
    start = value["startLine"]
    end = value["endLine"]
    if (
        isinstance(start, bool)
        or isinstance(end, bool)
        or not isinstance(start, int)
        or not isinstance(end, int)
        or start <= 0
        or end < start
    ):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} line range is invalid")
    return {
        "canonicalPath": path,
        "rawSha256": _sha256(value["rawSha256"], f"{locator}.rawSha256"),
        "startLine": start,
        "endLine": end,
        "selectedTextSha256": _sha256(
            value["selectedTextSha256"], f"{locator}.selectedTextSha256"
        ),
    }


def _basis_anchors(raw: Any, locator: str, *, required: bool = True) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or len(raw) > MAX_PLAN_ITEMS or (required and not raw):
        qualifier = "non-empty " if required else ""
        raise VerificationError(
            "MALFORMED_VERIFICATION_DRAFT", f"{locator} must be a {qualifier}bounded array"
        )
    result = [_basis_anchor(item, f"{locator}[{index}]") for index, item in enumerate(raw)]
    identities = [
        (item["canonicalPath"], item["startLine"], item["endLine"], item["selectedTextSha256"])
        for item in result
    ]
    if len(set(identities)) != len(identities):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} contains duplicate anchors")
    return result


def _check_anchor(anchor: Mapping[str, Any], locator: str) -> dict[str, Any]:
    raw_path = str(anchor["canonicalPath"])
    try:
        path = Path(raw_path).resolve(strict=True)
        if str(path) != raw_path or not path.is_file():
            raise OSError("path is not the same canonical regular file")
        raw = path.read_bytes()
    except OSError as exc:
        raise _PreflightTerminal("BLOCKED", "BASIS_AUTHORITY_UNAVAILABLE", f"{locator}: {exc}") from exc
    if hashlib.sha256(raw).hexdigest() != anchor["rawSha256"]:
        raise _PreflightTerminal("BLOCKED", "BASIS_AUTHORITY_CHANGED", f"{locator} whole-file hash changed")
    lines = raw.splitlines(keepends=True)
    start = int(anchor["startLine"])
    end = int(anchor["endLine"])
    if end > len(lines):
        raise _PreflightTerminal("BLOCKED", "BASIS_AUTHORITY_CHANGED", f"{locator} range exceeds file")
    selected = b"".join(lines[start - 1 : end])
    if hashlib.sha256(selected).hexdigest() != anchor["selectedTextSha256"]:
        raise _PreflightTerminal("BLOCKED", "BASIS_AUTHORITY_CHANGED", f"{locator} selected bytes changed")
    return dict(anchor)


def basis_anchor(path: Path | str, start_line: int, end_line: int) -> dict[str, Any]:
    """Build an exact local-file basis anchor for callers and tests."""

    try:
        canonical = Path(path).resolve(strict=True)
        raw = canonical.read_bytes()
    except OSError as exc:
        raise VerificationError("BASIS_AUTHORITY_UNAVAILABLE", f"cannot read basis anchor: {exc}") from exc
    lines = raw.splitlines(keepends=True)
    if start_line <= 0 or end_line < start_line or end_line > len(lines):
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "basis anchor line range is invalid")
    selected = b"".join(lines[start_line - 1 : end_line])
    return {
        "canonicalPath": str(canonical),
        "rawSha256": hashlib.sha256(raw).hexdigest(),
        "startLine": start_line,
        "endLine": end_line,
        "selectedTextSha256": hashlib.sha256(selected).hexdigest(),
    }


def _source_binding(raw: Any, locator: str, expected_source: str) -> dict[str, Any]:
    value = _mapping(raw, locator)
    _fields(
        value,
        {"mode", "finalSourceIdentity", "targetIdentityOrRevision", "bindingBasisAnchors"},
        locator,
    )
    if value["mode"] != "CURRENT_PROJECT_ROOT":
        raise VerificationError("UNSUPPORTED_EXECUTOR", "MVP supports CURRENT_PROJECT_ROOT source binding only")
    if value["finalSourceIdentity"] != expected_source:
        raise VerificationError("SOURCE_BINDING_MISMATCH", f"{locator} uses another source identity")
    target = _bounded_string(value["targetIdentityOrRevision"], f"{locator}.targetIdentityOrRevision")
    return {
        "mode": "CURRENT_PROJECT_ROOT",
        "finalSourceIdentity": expected_source,
        "targetIdentityOrRevision": target,
        "bindingBasisAnchors": _basis_anchors(
            value["bindingBasisAnchors"], f"{locator}.bindingBasisAnchors", required=False
        ),
    }


def _environment(raw: Any, locator: str) -> dict[str, str]:
    value = _mapping(raw, locator)
    if len(value) > MAX_ENVIRONMENT_KEYS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} is oversized")
    result: dict[str, str] = {}
    for key, raw_value in value.items():
        if not isinstance(key, str) or not ENV_KEY_PATTERN.fullmatch(key):
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} contains an invalid key")
        result[key] = _bounded_string(raw_value, f"{locator}.{key}", allow_empty=True)
    return {key: result[key] for key in sorted(result)}


def _normalize_step(raw: Any, locator: str, expected_source: str) -> dict[str, Any]:
    value = _mapping(raw, locator)
    _fields(
        value,
        {
            "stepId",
            "role",
            "executorKind",
            "executable",
            "argv",
            "cwd",
            "environmentDelta",
            "inputRefs",
            "sourceBinding",
            "pollPolicy",
        },
        locator,
    )
    role = value["role"]
    if role not in STEP_ROLES:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.role is invalid")
    if value["executorKind"] != "PROCESS":
        raise VerificationError("UNSUPPORTED_EXECUTOR", "MVP supports the fixed PROCESS executor only")
    executable = _bounded_string(value["executable"], f"{locator}.executable")
    cwd = _bounded_string(value["cwd"], f"{locator}.cwd")
    if not Path(executable).is_absolute() or not Path(cwd).is_absolute():
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} executable and cwd must be absolute")
    argv = value["argv"]
    if not isinstance(argv, list) or len(argv) > MAX_ARGV_PARTS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.argv is invalid")
    normalized_argv = [
        _bounded_string(part, f"{locator}.argv[{index}]", allow_empty=True)
        for index, part in enumerate(argv)
    ]
    if value["inputRefs"] != []:
        raise VerificationError("UNSUPPORTED_EXECUTOR", "PROCESS MVP requires empty inputRefs")
    poll_policy = value["pollPolicy"]
    if role == "READBACK":
        policy = _mapping(poll_policy, f"{locator}.pollPolicy")
        _fields(policy, {"maxAttempts", "intervalMs"}, f"{locator}.pollPolicy")
        maximum = policy["maxAttempts"]
        interval = policy["intervalMs"]
        if (
            isinstance(maximum, bool)
            or not isinstance(maximum, int)
            or not 1 <= maximum <= MAX_POLL_ATTEMPTS
            or isinstance(interval, bool)
            or not isinstance(interval, int)
            or not 0 <= interval <= MAX_POLL_INTERVAL_MS
        ):
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.pollPolicy is outside bounds")
        normalized_policy: dict[str, int] | None = {"maxAttempts": maximum, "intervalMs": interval}
    else:
        if poll_policy is not None:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "only READBACK may have pollPolicy")
        normalized_policy = None
    return {
        "stepId": _identifier(value["stepId"], f"{locator}.stepId"),
        "role": role,
        "executorKind": "PROCESS",
        "executable": executable,
        "argv": normalized_argv,
        "cwd": cwd,
        "environmentDelta": _environment(value["environmentDelta"], f"{locator}.environmentDelta"),
        "inputRefs": [],
        "sourceBinding": _source_binding(value["sourceBinding"], f"{locator}.sourceBinding", expected_source),
        "pollPolicy": normalized_policy,
    }


def _request_payload(step: Mapping[str, Any]) -> dict[str, Any]:
    _require_current_process_policy(step)
    try:
        identity = executable_identity.validate_executable_identity(
            step.get("executableIdentity"),
            expected_canonical_path=step.get("executable"),
        )
    except executable_identity.ExecutableIdentityError as exc:
        raise VerificationError(
            "SEALED_EXECUTABLE_IDENTITY_INVALID", exc.message
        ) from exc
    return {
        "executorKind": step["executorKind"],
        "executorVersion": step["executorVersion"],
        "environmentPolicy": step["environmentPolicy"],
        "executable": step["executable"],
        "executableIdentity": identity,
        "argv": step["argv"],
        "cwd": step["cwd"],
        "environmentDelta": step["environmentDelta"],
        "inputRefs": step["inputRefs"],
        "sourceBinding": step["sourceBinding"],
    }


def _repeat_request_payload(step: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact-repeat projection, omitting only final source identity."""

    payload = json.loads(_canonical_json(_request_payload(step)))
    binding = payload.get("sourceBinding")
    if not isinstance(binding, dict) or "finalSourceIdentity" not in binding:
        raise VerificationError(
            "SEALED_REQUEST_MISMATCH",
            "repeat request source binding has no final source identity",
        )
    del binding["finalSourceIdentity"]
    return payload


def _finalize_request_digests(step: dict[str, Any]) -> None:
    step["canonicalRequestDigest"] = _digest(_request_payload(step))
    step["repeatRequestDigest"] = _digest(_repeat_request_payload(step))
    step["sourceBindingDigest"] = _digest(step["sourceBinding"])


def _require_current_process_policy(step: Mapping[str, Any]) -> None:
    if (
        step.get("executorKind") != "PROCESS"
        or step.get("executorVersion") != PROCESS_EXECUTOR_VERSION
        or step.get("environmentPolicy") != PROCESS_ENVIRONMENT_POLICY
    ):
        raise VerificationError(
            "SEALED_EXECUTOR_POLICY_RETIRED",
            "PROCESS plan does not seal the current closed-environment executor policy; open a fresh run",
        )


def _require_current_process_plan(plan: Mapping[str, Any]) -> None:
    policy = plan.get("executorPolicy")
    if policy != {
        "executorVersion": PROCESS_EXECUTOR_VERSION,
        "environmentPolicy": PROCESS_ENVIRONMENT_POLICY,
    }:
        raise VerificationError(
            "SEALED_EXECUTOR_POLICY_RETIRED",
            "sealed plan predates the process-v3 executable-identity policy; historical reads remain available",
        )
    flows = plan.get("flows")
    if not isinstance(flows, list):
        raise VerificationError("STORE_CORRUPT", "sealed plan flows are malformed")
    for flow in flows:
        if not isinstance(flow, Mapping) or not isinstance(flow.get("steps"), list):
            raise VerificationError("STORE_CORRUPT", "sealed plan flow is malformed")
        bindings = flow.get("correlationBindings")
        if not isinstance(bindings, list):
            raise VerificationError("STORE_CORRUPT", "sealed correlation bindings are malformed")
        for binding in bindings:
            if not isinstance(binding, Mapping) or set(binding) != {
                "bindingId",
                "actionStepId",
                "readbackStepId",
                "token",
                "tokenSha256",
            }:
                raise VerificationError("STORE_CORRUPT", "sealed correlation binding is malformed")
            token = binding["token"]
            if (
                not isinstance(token, str)
                or hashlib.sha256(token.encode("utf-8")).hexdigest()
                != binding["tokenSha256"]
            ):
                raise VerificationError("STORE_CORRUPT", "sealed correlation token digest differs")
        for step in flow["steps"]:
            if not isinstance(step, Mapping):
                raise VerificationError("STORE_CORRUPT", "sealed PROCESS step is malformed")
            _require_current_process_policy(step)
            if set(step) != {
                "stepId",
                "role",
                "executorKind",
                "executorVersion",
                "environmentPolicy",
                "executable",
                "executableIdentity",
                "argv",
                "cwd",
                "environmentDelta",
                "inputRefs",
                "sourceBinding",
                "pollPolicy",
                "canonicalRequestDigest",
                "repeatRequestDigest",
                "sourceBindingDigest",
            }:
                raise VerificationError(
                    "SEALED_REQUEST_MISMATCH",
                    "sealed PROCESS step fields differ from process-v3",
                )
            try:
                request_digest = step.get("canonicalRequestDigest")
                repeat_digest = step.get("repeatRequestDigest")
                source_digest = step.get("sourceBindingDigest")
                digests_match = (
                    _digest(_request_payload(step)) == request_digest
                    and _digest(_repeat_request_payload(step)) == repeat_digest
                    and _digest(step.get("sourceBinding")) == source_digest
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise VerificationError(
                    "SEALED_REQUEST_MISMATCH", "sealed PROCESS request is malformed"
                ) from exc
            if not digests_match:
                raise VerificationError(
                    "SEALED_REQUEST_MISMATCH",
                    "sealed PROCESS request, repeat projection, or source binding differs",
                )


def _replace_correlation(value: str, tokens: Mapping[str, str]) -> tuple[str, set[str]]:
    replaced = value
    used: set[str] = set()
    for binding_id, token in tokens.items():
        placeholder = "{{CORRELATION:" + binding_id + "}}"
        if placeholder in replaced:
            replaced = replaced.replace(placeholder, token)
            used.add(binding_id)
    return replaced, used


def _normalize_correlation_bindings(
    flow_id: str,
    steps: list[dict[str, Any]],
    raw_bindings: Any,
) -> list[dict[str, Any]]:
    if not isinstance(raw_bindings, list) or len(raw_bindings) > MAX_PLAN_ITEMS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"flows[{flow_id}].optionalCorrelationBindings is invalid")
    by_step = {step["stepId"]: step for step in steps}
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_bindings):
        locator = f"flows[{flow_id}].optionalCorrelationBindings[{index}]"
        item = _mapping(raw, locator)
        _fields(item, {"bindingId", "actionStepId", "readbackStepId"}, locator)
        binding_id = _identifier(item["bindingId"], f"{locator}.bindingId")
        action_id = _identifier(item["actionStepId"], f"{locator}.actionStepId")
        readback_id = _identifier(item["readbackStepId"], f"{locator}.readbackStepId")
        if binding_id in seen or action_id not in by_step or readback_id not in by_step:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} references invalid or duplicate IDs")
        if by_step[action_id]["role"] != "ACTION" or by_step[readback_id]["role"] != "READBACK":
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} roles are invalid")
        seen.add(binding_id)
        normalized.append(
            {
                "bindingId": binding_id,
                "actionStepId": action_id,
                "readbackStepId": readback_id,
            }
        )
    for binding in normalized:
        placeholder = "{{CORRELATION:" + binding["bindingId"] + "}}"
        for field in ("actionStepId", "readbackStepId"):
            step = by_step[binding[field]]
            values = [*step["argv"], *step["environmentDelta"].values()]
            if not any(placeholder in value for value in values):
                raise VerificationError(
                    "MALFORMED_VERIFICATION_DRAFT",
                    f"correlation {binding['bindingId']} placeholder must occur in its ACTION and READBACK requests",
                )
    return normalized


def _apply_correlations(
    steps: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tokens: dict[str, str] = {}
    finalized_bindings: list[dict[str, Any]] = []
    for binding in bindings:
        token = f"verification-correlation-v1-{uuid.uuid4().hex}"
        tokens[binding["bindingId"]] = token
        finalized_bindings.append(
            {
                **binding,
                "token": token,
                "tokenSha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
            }
        )
    usage: dict[tuple[str, str], set[str]] = {}
    correlated_steps: list[dict[str, Any]] = []
    for step in steps:
        copy = dict(step)
        new_argv: list[str] = []
        used: set[str] = set()
        for arg in step["argv"]:
            replaced, hits = _replace_correlation(arg, tokens)
            new_argv.append(replaced)
            used.update(hits)
        new_env: dict[str, str] = {}
        for key, raw_value in step["environmentDelta"].items():
            replaced, hits = _replace_correlation(raw_value, tokens)
            new_env[key] = replaced
            used.update(hits)
        copy["argv"] = new_argv
        copy["environmentDelta"] = new_env
        for binding_id in used:
            usage.setdefault((binding_id, step["stepId"]), set()).add(binding_id)
        correlated_steps.append(copy)
    for binding in finalized_bindings:
        binding_id = binding["bindingId"]
        if (binding_id, binding["actionStepId"]) not in usage or (
            binding_id,
            binding["readbackStepId"],
        ) not in usage:
            raise VerificationError(
                "MALFORMED_VERIFICATION_DRAFT",
                f"correlation {binding_id} placeholder must occur in its ACTION and READBACK requests",
            )
    return correlated_steps, finalized_bindings


def _normalize_authorizations(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list) or len(raw) > MAX_PLAN_ITEMS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "authorizationRefs must be a bounded array")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw_item in enumerate(raw):
        locator = f"authorizationRefs[{index}]"
        item = _mapping(raw_item, locator)
        _fields(item, {"authorizationRef", "scopeSha256"}, locator)
        ref = item["authorizationRef"]
        if not isinstance(ref, str) or not AUTHORIZATION_REF_PATTERN.fullmatch(ref) or ref in seen:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.authorizationRef is invalid")
        seen.add(ref)
        result.append(
            {
                "authorizationRef": ref,
                "scopeSha256": _sha256(item["scopeSha256"], f"{locator}.scopeSha256"),
            }
        )
    return result


def _expected_criteria(handoff: Mapping[str, Any]) -> list[dict[str, Any]]:
    accounting = handoff.get("criterionAccounting")
    if not isinstance(accounting, list) or not accounting:
        raise VerificationError("HANDOFF_CONTRACT_INVALID", "handoff has no exact criterion accounting")
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(accounting):
        item = _mapping(raw, f"handoff.criterionAccounting[{index}]")
        result.append(
            _criterion_ref(
                {
                    "criterionIndex": item.get("criterionIndex"),
                    "criterionRawSha256": item.get("criterionRawSha256"),
                },
                f"handoff.criterionAccounting[{index}]",
            )
        )
    if [item["criterionIndex"] for item in result] != list(range(1, len(result) + 1)):
        raise VerificationError("HANDOFF_CONTRACT_INVALID", "handoff criteria are not exact ordered AC identities")
    return result


def _normalize_draft(
    raw: Any,
    *,
    handoff: Mapping[str, Any],
    expected_source: str,
) -> dict[str, Any]:
    draft = _mapping(raw, "verificationDraft")
    _fields(draft, {"authorizationRefs", "criteria", "sourceReviews", "flows"}, "verificationDraft")
    expected = _expected_criteria(handoff)
    criteria_raw = draft["criteria"]
    if not isinstance(criteria_raw, list) or len(criteria_raw) != len(expected):
        raise VerificationError("ACCEPTANCE_CRITERIA_MISMATCH", "criteria must contain every exact AC once")
    criteria: list[dict[str, Any]] = []
    for offset, (raw_item, expected_item) in enumerate(zip(criteria_raw, expected)):
        locator = f"criteria[{offset}]"
        item = _mapping(raw_item, locator)
        _fields(item, {"criterionIndex", "criterionRawSha256", "sourceReviewIds", "flowIds"}, locator)
        identity = _criterion_ref(
            {
                "criterionIndex": item["criterionIndex"],
                "criterionRawSha256": item["criterionRawSha256"],
            },
            locator,
        )
        if identity != expected_item:
            raise VerificationError("ACCEPTANCE_CRITERIA_MISMATCH", f"{locator} is stale or reordered")
        source_ids = _id_list(item["sourceReviewIds"], f"{locator}.sourceReviewIds")
        criterion_flow_ids = _id_list(item["flowIds"], f"{locator}.flowIds")
        if not source_ids and not criterion_flow_ids:
            raise VerificationError("INCOMPLETE_OBLIGATION_MAPPING", f"{locator} has no obligation")
        criteria.append(
            {**identity, "sourceReviewIds": source_ids, "flowIds": criterion_flow_ids}
        )

    raw_reviews = draft["sourceReviews"]
    if not isinstance(raw_reviews, list) or len(raw_reviews) > MAX_PLAN_ITEMS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "sourceReviews must be a bounded array")
    reviews: list[dict[str, Any]] = []
    review_ids: set[str] = set()
    for offset, raw_review in enumerate(raw_reviews):
        locator = f"sourceReviews[{offset}]"
        review = _mapping(raw_review, locator)
        _fields(review, {"sourceReviewId", "criterionRefs", "basisAnchors"}, locator)
        review_id = _identifier(review["sourceReviewId"], f"{locator}.sourceReviewId")
        if review_id in review_ids:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "sourceReviewId is duplicated")
        review_ids.add(review_id)
        reviews.append(
            {
                "sourceReviewId": review_id,
                "criterionRefs": _criterion_refs(review["criterionRefs"], f"{locator}.criterionRefs"),
                "basisAnchors": _basis_anchors(review["basisAnchors"], f"{locator}.basisAnchors"),
            }
        )

    raw_flows = draft["flows"]
    if not isinstance(raw_flows, list) or len(raw_flows) > MAX_PLAN_ITEMS:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "flows must be a bounded array")
    flows: list[dict[str, Any]] = []
    flow_ids: set[str] = set()
    global_step_ids: set[str] = set()
    for offset, raw_flow in enumerate(raw_flows):
        locator = f"flows[{offset}]"
        flow = _mapping(raw_flow, locator)
        _fields(
            flow,
            {
                "flowId",
                "criterionRefs",
                "claim",
                "expectedTerminalObservation",
                "basisAnchors",
                "productTargetRequirement",
                "steps",
                "optionalCorrelationBindings",
            },
            locator,
        )
        flow_id = _identifier(flow["flowId"], f"{locator}.flowId")
        if flow_id in flow_ids:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "flowId is duplicated")
        flow_ids.add(flow_id)
        requirement = flow["productTargetRequirement"]
        if requirement not in TARGET_REQUIREMENTS:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.productTargetRequirement is invalid")
        raw_steps = flow["steps"]
        if not isinstance(raw_steps, list) or not raw_steps or len(raw_steps) > MAX_STEPS_PER_FLOW:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator}.steps is invalid")
        steps = [
            _normalize_step(step, f"{locator}.steps[{index}]", expected_source)
            for index, step in enumerate(raw_steps)
        ]
        local_ids = [step["stepId"] for step in steps]
        if len(set(local_ids)) != len(local_ids) or global_step_ids.intersection(local_ids):
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", "stepId must be unique in the run")
        global_step_ids.update(local_ids)
        bindings = _normalize_correlation_bindings(
            flow_id, steps, flow["optionalCorrelationBindings"]
        )
        flows.append(
            {
                "flowId": flow_id,
                "criterionRefs": _criterion_refs(flow["criterionRefs"], f"{locator}.criterionRefs"),
                "claim": _bounded_string(flow["claim"], f"{locator}.claim"),
                "expectedTerminalObservation": _bounded_string(
                    flow["expectedTerminalObservation"], f"{locator}.expectedTerminalObservation"
                ),
                "basisAnchors": _basis_anchors(flow["basisAnchors"], f"{locator}.basisAnchors"),
                "productTargetRequirement": requirement,
                "steps": steps,
                "correlationBindings": bindings,
            }
        )

    review_by_id = {review["sourceReviewId"]: review for review in reviews}
    flow_by_id = {flow["flowId"]: flow for flow in flows}
    expected_pairs = {
        (criterion["criterionIndex"], criterion["criterionRawSha256"]): criterion
        for criterion in criteria
    }
    reverse_reviews: dict[str, set[tuple[int, str]]] = {key: set() for key in review_by_id}
    reverse_flows: dict[str, set[tuple[int, str]]] = {key: set() for key in flow_by_id}
    for criterion in criteria:
        pair = (criterion["criterionIndex"], criterion["criterionRawSha256"])
        for review_id in criterion["sourceReviewIds"]:
            if review_id not in review_by_id:
                raise VerificationError("INCOMPLETE_OBLIGATION_MAPPING", f"unknown sourceReviewId: {review_id}")
            reverse_reviews[review_id].add(pair)
        for flow_id in criterion["flowIds"]:
            if flow_id not in flow_by_id:
                raise VerificationError("INCOMPLETE_OBLIGATION_MAPPING", f"unknown flowId: {flow_id}")
            reverse_flows[flow_id].add(pair)
    for review in reviews:
        actual = {(item["criterionIndex"], item["criterionRawSha256"]) for item in review["criterionRefs"]}
        if not actual.issubset(expected_pairs) or actual != reverse_reviews[review["sourceReviewId"]]:
            raise VerificationError("POST_HOC_MAPPING_REJECTED", "source review criterion mapping is not bidirectional")
    for flow in flows:
        actual = {(item["criterionIndex"], item["criterionRawSha256"]) for item in flow["criterionRefs"]}
        if not actual.issubset(expected_pairs) or actual != reverse_flows[flow["flowId"]]:
            raise VerificationError("POST_HOC_MAPPING_REJECTED", "flow criterion mapping is not bidirectional")

    return {
        "authorizationRefs": _normalize_authorizations(draft["authorizationRefs"]),
        "criteria": criteria,
        "sourceReviews": reviews,
        "flows": flows,
    }


def _bounded_output(value: bytes) -> dict[str, Any]:
    bounded = value[:MAX_OUTPUT_BYTES]
    return {
        "sha256": hashlib.sha256(value).hexdigest(),
        "byteCount": len(value),
        "truncated": len(value) > MAX_OUTPUT_BYTES,
        "text": bounded.decode("utf-8", errors="replace"),
    }


def _artifact_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "sha256": value["sha256"],
        "byteCount": value["byteCount"],
        "truncated": value["truncated"],
    }


def _budget_vector(**values: int) -> dict[str, int]:
    result = {field: 0 for field in workflow_store.BUDGET_FIELDS}
    result.update(values)
    return result


def _public_step(step: Mapping[str, Any]) -> dict[str, Any]:
    environment = {
        key: {"valueSha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}
        for key, value in step["environmentDelta"].items()
    }
    argv = [
        {
            "valueSha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
            "byteCount": len(value.encode("utf-8")),
        }
        for value in step["argv"]
    ]
    result = {
        "stepId": step["stepId"],
        "role": step["role"],
        "executorKind": step["executorKind"],
        "executorVersion": step.get("executorVersion", "process-v1"),
        "environmentPolicy": step.get("environmentPolicy", "AMBIENT_OVERLAY_RETIRED"),
        "canonicalRequestDigest": step["canonicalRequestDigest"],
        "canonicalRequest": {
            "executable": step["executable"],
            "executableIdentity": step.get("executableIdentity"),
            "argv": argv,
            "cwd": step["cwd"],
            "environmentDelta": environment,
            "inputRefs": step["inputRefs"],
        },
        "sourceBinding": step["sourceBinding"],
        "sourceBindingDigest": step["sourceBindingDigest"],
        "pollPolicy": step["pollPolicy"],
    }
    if "repeatRequestDigest" in step:
        result["repeatRequestDigest"] = step["repeatRequestDigest"]
    return result


class VerificationService:
    """Coordinates claims and owns sealed-run execution and result publication."""

    def __init__(
        self,
        workflow_root: Path | str | None = None,
        *,
        guard: Any | None = None,
        workflow: Any | None = None,
    ) -> None:
        if workflow is not None:
            if not isinstance(workflow, workflow_store.WorkflowStore):
                raise VerificationError(
                    "INVALID_WORKFLOW_STORE",
                    "injected workflow is not an audited WorkflowStore",
                )
            if workflow_root is not None:
                try:
                    expected_root = Path(workflow_root).expanduser().resolve()
                except (OSError, RuntimeError) as exc:
                    raise VerificationError(
                        "INVALID_WORKFLOW_STORE",
                        "workflow root cannot be canonicalized",
                    ) from exc
                if expected_root != workflow.store_root:
                    raise VerificationError(
                        "INVALID_WORKFLOW_STORE",
                        "injected workflow differs from requested workflow root",
                    )
            self.workflow = workflow
            return
        if guard is None:
            raise VerificationError(
                "AUDIT_GUARD_REQUIRED",
                "verification service requires a live audited-open guard session",
            )
        try:
            opened = workflow_store.audit_and_open_workflow_store(
                workflow_root or workflow_store.DEFAULT_STORE_ROOT,
                guard=guard,
            )
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        self.workflow = opened.store

    @staticmethod
    def _step_execution_lock_name(run_ref: str, flow_id: str, step_id: str) -> str:
        identity = _canonical_json(
            {
                "protocolVersion": "verification-live-step-lock-v1",
                "verificationRunRef": run_ref,
                "flowId": flow_id,
                "stepId": step_id,
            }
        )
        return f"{hashlib.sha256(identity).hexdigest()}.lock"

    @staticmethod
    def _require_owner_only_lock_object(
        observed: os.stat_result,
        *,
        locator: str,
        expected_kind: str,
    ) -> None:
        kind_matches = (
            stat.S_ISDIR(observed.st_mode)
            if expected_kind == "directory"
            else stat.S_ISREG(observed.st_mode)
        )
        if (
            not kind_matches
            or observed.st_uid != os.geteuid()
            or stat.S_IMODE(observed.st_mode) & 0o077
            or (expected_kind == "file" and observed.st_nlink != 1)
        ):
            raise VerificationError(
                "STEP_EXECUTION_LOCK_UNSAFE",
                f"{locator} is not a stable owner-only {expected_kind}",
            )

    def _open_step_execution_lock_file(
        self,
        *,
        run_ref: str,
        flow_id: str,
        step_id: str,
    ) -> int:
        """Open one persistent, no-follow lock inode below the audited store root."""

        directory_flags = os.O_RDONLY | os.O_CLOEXEC
        directory_flags |= getattr(os, "O_DIRECTORY", 0)
        directory_flags |= getattr(os, "O_NOFOLLOW", 0)
        file_flags = os.O_RDWR | os.O_CLOEXEC
        file_flags |= getattr(os, "O_NOFOLLOW", 0)
        root_fd: int | None = None
        directory_fd: int | None = None
        lock_fd: int | None = None
        keep_lock_fd = False
        try:
            root_fd = os.open(self.workflow.store_root, directory_flags)
            self._require_owner_only_lock_object(
                os.fstat(root_fd),
                locator="workflow store root",
                expected_kind="directory",
            )
            try:
                os.mkdir(
                    LIVE_EXECUTION_LOCK_DIRECTORY,
                    0o700,
                    dir_fd=root_fd,
                )
            except FileExistsError:
                pass
            directory_fd = os.open(
                LIVE_EXECUTION_LOCK_DIRECTORY,
                directory_flags,
                dir_fd=root_fd,
            )
            self._require_owner_only_lock_object(
                os.fstat(directory_fd),
                locator="live execution lock directory",
                expected_kind="directory",
            )
            lock_name = self._step_execution_lock_name(run_ref, flow_id, step_id)
            try:
                lock_fd = os.open(
                    lock_name,
                    file_flags | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=directory_fd,
                )
            except FileExistsError:
                lock_fd = os.open(lock_name, file_flags, dir_fd=directory_fd)
            observed = os.fstat(lock_fd)
            self._require_owner_only_lock_object(
                observed,
                locator="live execution lock file",
                expected_kind="file",
            )
            linked = os.stat(lock_name, dir_fd=directory_fd, follow_symlinks=False)
            if (linked.st_dev, linked.st_ino) != (observed.st_dev, observed.st_ino):
                raise VerificationError(
                    "STEP_EXECUTION_LOCK_UNSAFE",
                    "live execution lock file changed while opening",
                )
            keep_lock_fd = True
            return lock_fd
        except VerificationError:
            raise
        except OSError as exc:
            raise VerificationError(
                "STEP_EXECUTION_LOCK_UNAVAILABLE",
                "live execution ownership lock could not be opened",
            ) from exc
        finally:
            if lock_fd is not None and not keep_lock_fd:
                os.close(lock_fd)
            if directory_fd is not None:
                os.close(directory_fd)
            if root_fd is not None:
                os.close(root_fd)

    def _acquire_step_execution_lock(
        self,
        *,
        run_ref: str,
        flow_id: str,
        step_id: str,
    ) -> int:
        lock_fd = self._open_step_execution_lock_file(
            run_ref=run_ref,
            flow_id=flow_id,
            step_id=step_id,
        )
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(lock_fd)
            if exc.errno in {errno.EACCES, errno.EAGAIN}:
                raise VerificationError(
                    "STEP_EXECUTION_ACTIVE",
                    "a live executor owns this sealed step",
                ) from exc
            raise VerificationError(
                "STEP_EXECUTION_LOCK_UNAVAILABLE",
                "live execution ownership lock could not be acquired",
            ) from exc
        return lock_fd

    def _validate_verifiable_handoff_locked(self, connection, handoff_ref: str) -> dict[str, Any]:
        row = connection.execute(
            "SELECT * FROM nodes WHERE node_ref = ? AND node_kind = 'IMPLEMENTATION_HANDOFF'",
            (handoff_ref,),
        ).fetchone()
        if row is None:
            raise VerificationError("HANDOFF_NOT_FOUND", "implementation handoff is absent")
        try:
            view = self.workflow._node_view(row)
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        handoff = view["payload"]
        required = {
            "protocolVersion",
            "implementationHandoffRef",
            "implementationStatus",
            "projectRoot",
            "planningSeal",
            "planningSealDigest",
            "baselineCapsuleRef",
            "baselineSourceIdentity",
            "finalSourceIdentity",
            "implementationDeltaRef",
            "criterionAccounting",
            "unresolvedImplementationItems",
            "completedAt",
        }
        if (
            set(handoff) != required
            or row["protocol_version"] != "implementation-handoff-v1"
            or view["protocolVersion"] != "implementation-handoff-v1"
            or handoff.get("protocolVersion") != "implementation-handoff-v1"
            or handoff.get("implementationHandoffRef") != handoff_ref
            or handoff.get("implementationStatus") != "IMPLEMENTATION_HANDOFF_COMPLETE"
            or row["verification_status"] is not None
            or not isinstance(row["planning_identity"], str)
            or not SHA256_PATTERN.fullmatch(row["planning_identity"])
            or not isinstance(row["source_identity"], str)
            or not SOURCE_IDENTITY_PATTERN.fullmatch(row["source_identity"])
            or handoff.get("planningSealDigest") != row["planning_identity"]
            or handoff.get("finalSourceIdentity") != row["source_identity"]
            or handoff.get("unresolvedImplementationItems") != []
        ):
            raise VerificationError(
                "HANDOFF_CONTRACT_INVALID", "implementation handoff contract or node binding differs"
            )
        baseline_capsule_ref = handoff["baselineCapsuleRef"]
        baseline_source_identity = handoff["baselineSourceIdentity"]
        implementation_delta_ref = handoff["implementationDeltaRef"]
        completed_at = handoff["completedAt"]
        if (
            not isinstance(baseline_capsule_ref, str)
            or not CAPSULE_REF_PATTERN.fullmatch(baseline_capsule_ref)
            or not isinstance(baseline_source_identity, str)
            or not SOURCE_IDENTITY_PATTERN.fullmatch(baseline_source_identity)
            or not isinstance(implementation_delta_ref, str)
            or not DELTA_REF_PATTERN.fullmatch(implementation_delta_ref)
            or not isinstance(completed_at, str)
        ):
            raise VerificationError(
                "HANDOFF_CONTRACT_INVALID",
                "handoff baseline, delta, or completion binding is malformed",
            )
        try:
            parsed_completed_at = datetime.fromisoformat(completed_at)
            parsed_node_created_at = datetime.fromisoformat(row["created_at"])
        except (TypeError, ValueError) as exc:
            raise VerificationError(
                "HANDOFF_CONTRACT_INVALID", "handoff/node completion time is not ISO-8601"
            ) from exc
        if (
            parsed_completed_at.tzinfo is None
            or parsed_node_created_at.tzinfo is None
            or parsed_completed_at.astimezone(timezone.utc)
            > parsed_node_created_at.astimezone(timezone.utc)
        ):
            raise VerificationError(
                "HANDOFF_CONTRACT_INVALID",
                "handoff completion time is unbound to node publication time",
            )
        accounting = handoff.get("criterionAccounting")
        if not isinstance(accounting, list) or not accounting:
            raise VerificationError("HANDOFF_CONTRACT_INVALID", "handoff criterion accounting is absent")
        for index, raw in enumerate(accounting):
            if not isinstance(raw, Mapping) or set(raw) != {
                "criterionIndex",
                "criterionRawSha256",
                "taskIds",
            }:
                raise VerificationError(
                    "HANDOFF_CONTRACT_INVALID", f"handoff criterionAccounting[{index}] is malformed"
                )
            task_ids = raw["taskIds"]
            if (
                not isinstance(task_ids, list)
                or task_ids != sorted(task_ids)
                or len(task_ids) != len(set(task_ids))
                or any(not isinstance(task, str) or not ID_PATTERN.fullmatch(task) for task in task_ids)
            ):
                raise VerificationError(
                    "HANDOFF_CONTRACT_INVALID",
                    f"handoff criterionAccounting[{index}].taskIds is non-canonical",
                )
        try:
            project_root = self._project_root(handoff)
            self._verify_planning(handoff)
            observed_source = self._capture_source(project_root)
        except _PreflightTerminal as exc:
            raise VerificationError(exc.reason_code, exc.message) from exc
        if observed_source != row["source_identity"]:
            raise VerificationError(
                "SOURCE_IDENTITY_MISMATCH", "implementation handoff source is not current"
            )
        return view

    @staticmethod
    def preview_process_step(
        *,
        step: Mapping[str, Any],
        project_root: Path | str,
        final_source_identity: str,
    ) -> dict[str, Any]:
        """Canonicalize one non-correlated PROCESS step for authorization scoping."""

        if not SOURCE_IDENTITY_PATTERN.fullmatch(final_source_identity):
            raise VerificationError("SOURCE_BINDING_MISMATCH", "final source identity is malformed")
        try:
            root = Path(project_root).resolve(strict=True)
        except OSError as exc:
            raise VerificationError("PROCESS_TARGET_UNAVAILABLE", str(exc)) from exc
        normalized = _normalize_step(step, "step", final_source_identity)
        if any("{{CORRELATION:" in value for value in normalized["argv"]) or any(
            "{{CORRELATION:" in value for value in normalized["environmentDelta"].values()
        ):
            raise VerificationError(
                "MALFORMED_REPLAY_SAFETY",
                "correlated steps receive a tool token only during whole-flow sealing",
            )
        try:
            identity = executable_identity.observe_executable_identity(
                normalized["executable"]
            )
            cwd = Path(normalized["cwd"]).resolve(strict=True)
        except executable_identity.ExecutableIdentityError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        except OSError as exc:
            raise VerificationError("PROCESS_TARGET_UNAVAILABLE", str(exc)) from exc
        if not cwd.is_dir() or (cwd != root and root not in cwd.parents):
            raise VerificationError("PROCESS_TARGET_OUTSIDE_PROJECT", "cwd is outside project root")
        if normalized["sourceBinding"]["targetIdentityOrRevision"] != str(root):
            raise VerificationError("SOURCE_BINDING_MISMATCH", "source target differs from project root")
        normalized["executorVersion"] = PROCESS_EXECUTOR_VERSION
        normalized["environmentPolicy"] = PROCESS_ENVIRONMENT_POLICY
        normalized["executable"] = identity["canonicalPath"]
        normalized["executableIdentity"] = identity
        normalized["cwd"] = str(cwd)
        _finalize_request_digests(normalized)
        return {
            "executorVersion": PROCESS_EXECUTOR_VERSION,
            "environmentPolicy": PROCESS_ENVIRONMENT_POLICY,
            "executableIdentity": identity,
            "canonicalRequestDigest": normalized["canonicalRequestDigest"],
            "repeatRequestDigest": normalized["repeatRequestDigest"],
            "sourceBindingDigest": normalized["sourceBindingDigest"],
        }

    def open_verification(
        self,
        *,
        coordinator_capability: str,
        implementation_handoff_ref: str,
        spend_budget: Mapping[str, Any],
        closure_budget: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(implementation_handoff_ref, str) or not HANDOFF_REF_PATTERN.fullmatch(
            implementation_handoff_ref
        ):
            raise VerificationError("MALFORMED_HANDOFF_REF", "implementation handoff ref is malformed")
        try:
            with self.workflow._transaction() as connection:
                coordinator = self.workflow._actor_for_capability_locked(
                    connection, coordinator_capability, expected_role="COORDINATOR"
                )
                tip = self.workflow._current_tip_locked(connection, coordinator["root_ref"])
                tip_payload = _decode_json(tip["payload_json"], "current tip")
                expected_handoff = (
                    tip["node_ref"]
                    if tip["node_kind"] == "IMPLEMENTATION_HANDOFF"
                    else tip_payload.get("implementationHandoffRef")
                )
                if expected_handoff != implementation_handoff_ref:
                    raise VerificationError("HANDOFF_IDENTITY_MISMATCH", "handoff is not the current verifiable candidate")
                handoff_view = self._validate_verifiable_handoff_locked(
                    connection, implementation_handoff_ref
                )
                if (
                    handoff_view["planningIdentity"] != tip["planning_identity"]
                    or handoff_view["sourceIdentity"] != tip["source_identity"]
                ):
                    raise VerificationError(
                        "HANDOFF_IDENTITY_MISMATCH",
                        "current tip and implementation handoff identity differ",
                    )
                tip_view = dict(tip)
            assessor = self.workflow.issue_actor(
                coordinator_capability=coordinator_capability, role="ASSESSOR"
            )
            reservation = self.workflow.reserve_budget(
                coordinator_capability=coordinator_capability,
                transition_kind="VERIFY",
                spend=spend_budget,
                closure_reserve=closure_budget,
            )
            run_ref = workflow_store.allocate_ref("VERIFY")
            try:
                claim = self.workflow.acquire_claim(
                    coordinator_capability=coordinator_capability,
                    claimant_actor_ref=assessor["actorRef"],
                    tip_ref=tip_view["node_ref"],
                    transition_kind="VERIFY",
                    planning_identity=tip_view["planning_identity"],
                    source_identity=tip_view["source_identity"],
                    execution_ref=run_ref,
                    budget_reservation_ref=reservation["reservationRef"],
                )
            except BaseException:
                self.workflow.close_budget_reservation(
                    actor_capability=coordinator_capability,
                    reservation_ref=reservation["reservationRef"],
                )
                raise
        except VerificationError:
            raise
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        return {
            "verificationRunRef": run_ref,
            "implementationHandoffRef": implementation_handoff_ref,
            "assessor": assessor,
            "claim": claim,
            "budgetReservation": reservation,
        }

    def open_remediation(
        self,
        *,
        coordinator_capability: str,
        failed_verification_result_ref: str,
        spend_budget: Mapping[str, Any],
        closure_budget: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Mechanically allocate fresh Remediator/Worker contexts and a REMEDIATE claim.

        This operation does not decide authority-delta admission and does not start a
        Worker call.  The fresh Remediator must separately admit and start the
        implementation transaction after this claim exists.
        """

        if not isinstance(failed_verification_result_ref, str) or not RESULT_REF_PATTERN.fullmatch(
            failed_verification_result_ref
        ):
            raise VerificationError("MALFORMED_RESULT_REF", "failed VerificationResult ref is malformed")
        try:
            with self.workflow._transaction() as connection:
                coordinator = self.workflow._actor_for_capability_locked(
                    connection, coordinator_capability, expected_role="COORDINATOR"
                )
                tip = self.workflow._current_tip_locked(connection, coordinator["root_ref"])
                if (
                    tip["node_ref"] != failed_verification_result_ref
                    or tip["node_kind"] != "VERIFICATION_RESULT"
                    or tip["verification_status"] != "VERIFICATION_FAILED"
                ):
                    raise VerificationError(
                        "REMEDIATION_REQUIRES_PUBLISHED_FAILURE",
                        "current tip is not the exact immutable VERIFICATION_FAILED result",
                    )
                tip_view = dict(tip)
            remediator = self.workflow.issue_actor(
                coordinator_capability=coordinator_capability, role="REMEDIATOR"
            )
            worker = self.workflow.issue_actor(
                coordinator_capability=coordinator_capability, role="WORKER"
            )
            reservation = self.workflow.reserve_budget(
                coordinator_capability=coordinator_capability,
                transition_kind="REMEDIATE",
                spend=spend_budget,
                closure_reserve=closure_budget,
            )
            transaction_ref = workflow_store.allocate_ref("REMEDIATE")
            try:
                claim = self.workflow.acquire_claim(
                    coordinator_capability=coordinator_capability,
                    claimant_actor_ref=remediator["actorRef"],
                    tip_ref=failed_verification_result_ref,
                    transition_kind="REMEDIATE",
                    planning_identity=tip_view["planning_identity"],
                    source_identity=tip_view["source_identity"],
                    execution_ref=transaction_ref,
                    budget_reservation_ref=reservation["reservationRef"],
                )
            except BaseException:
                self.workflow.close_budget_reservation(
                    actor_capability=coordinator_capability,
                    reservation_ref=reservation["reservationRef"],
                )
                raise
        except VerificationError:
            raise
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        return {
            "failedVerificationResultRef": failed_verification_result_ref,
            "implementationTransactionRef": transaction_ref,
            "remediator": remediator,
            "worker": worker,
            "claim": claim,
            "budgetReservation": reservation,
        }

    def _claim_context(
        self,
        *,
        assessor_capability: str,
        claim_ref: str,
        implementation_handoff_ref: str,
    ) -> dict[str, Any]:
        if not isinstance(claim_ref, str) or not CLAIM_REF_PATTERN.fullmatch(claim_ref):
            raise VerificationError("MALFORMED_CLAIM", "claim ref is malformed")
        try:
            with self.workflow._transaction() as connection:
                assessor = self.workflow._actor_for_capability_locked(
                    connection, assessor_capability, expected_role="ASSESSOR"
                )
                claim = connection.execute("SELECT * FROM claims WHERE claim_ref = ?", (claim_ref,)).fetchone()
                if (
                    claim is None
                    or claim["state"] != "ACTIVE"
                    or claim["transition_kind"] != "VERIFY"
                    or claim["claimant_actor_ref"] != assessor["actor_ref"]
                ):
                    raise VerificationError("VERIFY_CLAIM_MISMATCH", "VERIFY claim is absent, closed, or owned by another actor")
                tip = self.workflow._current_tip_locked(connection, claim["root_ref"])
                if tip["node_ref"] != claim["tip_ref"]:
                    raise VerificationError("STALE_WORKFLOW_TIP", "VERIFY claim no longer owns the current tip")
                tip_payload = _decode_json(tip["payload_json"], "current tip")
                expected_handoff = (
                    tip["node_ref"]
                    if tip["node_kind"] == "IMPLEMENTATION_HANDOFF"
                    else tip_payload.get("implementationHandoffRef")
                )
                if expected_handoff != implementation_handoff_ref:
                    raise VerificationError("HANDOFF_IDENTITY_MISMATCH", "claim points at another implementation handoff")
                handoff_row = connection.execute(
                    "SELECT * FROM nodes WHERE node_ref = ? AND node_kind = 'IMPLEMENTATION_HANDOFF'",
                    (implementation_handoff_ref,),
                ).fetchone()
                if handoff_row is None:
                    raise VerificationError("HANDOFF_NOT_FOUND", "implementation handoff is absent")
                handoff = _decode_json(handoff_row["payload_json"], "implementation handoff")
                return {
                    "assessor": dict(assessor),
                    "claim": dict(claim),
                    "tip": dict(tip),
                    "handoff": handoff,
                }
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc

    @staticmethod
    def _project_root(handoff: Mapping[str, Any]) -> Path:
        raw = handoff.get("projectRoot")
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            raise VerificationError("HANDOFF_CONTRACT_INVALID", "handoff projectRoot is invalid")
        try:
            root = Path(raw).resolve(strict=True)
        except OSError as exc:
            raise VerificationError("HANDOFF_CONTRACT_INVALID", f"handoff projectRoot is unavailable: {exc}") from exc
        if not root.is_dir() or str(root) != raw:
            raise VerificationError("HANDOFF_CONTRACT_INVALID", "handoff projectRoot is not canonical")
        return root

    def _insert_preflight_run(
        self,
        *,
        context: Mapping[str, Any],
        project_root: Path,
        draft_digest: str,
    ) -> None:
        claim = context["claim"]
        run_ref = claim["execution_ref"]
        preflight = {
            "stage": "STARTED",
            "draftDigest": draft_digest,
            "observations": [],
        }
        encoded = _canonical_json(preflight)
        created_at = _now()
        try:
            with self.workflow._transaction() as connection:
                current_claim = connection.execute(
                    "SELECT * FROM claims WHERE claim_ref = ?", (claim["claim_ref"],)
                ).fetchone()
                if current_claim is None or current_claim["state"] != "ACTIVE":
                    raise VerificationError("VERIFY_CLAIM_MISMATCH", "claim closed before preflight")
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
                        run_ref,
                        claim["root_ref"],
                        claim["claim_ref"],
                        context["assessor"]["actor_ref"],
                        context["handoff"]["implementationHandoffRef"],
                        str(project_root),
                        claim["planning_identity"],
                        claim["source_identity"],
                        encoded,
                        created_at,
                    ),
                )
                self._event_locked(
                    connection,
                    run_ref,
                    "PREFLIGHT_STARTED",
                    {"draftDigest": draft_digest, "startedAt": created_at},
                )
        except VerificationError:
            raise
        except Exception as exc:
            if isinstance(exc, workflow_store.WorkflowStoreError):
                raise VerificationError(exc.code, exc.message) from exc
            raise

    @staticmethod
    def _event_locked(connection, run_ref: str, event_kind: str, payload: Mapping[str, Any]) -> None:
        encoded = _canonical_json(payload)
        connection.execute(
            """
            INSERT INTO verification_events(run_ref, event_kind, payload_json, payload_sha256, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_ref, event_kind, encoded, hashlib.sha256(encoded).hexdigest(), _now()),
        )

    @staticmethod
    def _capture_source(project_root: Path) -> str:
        try:
            return baseline_capsule.capture_identity(project_root)["sourceIdentity"]
        except baseline_capsule.CapsuleError as exc:
            raise _PreflightTerminal("INCOMPLETE", "SOURCE_IDENTITY_UNAVAILABLE", exc.message) from exc

    @staticmethod
    def _verify_planning(handoff: Mapping[str, Any]) -> None:
        try:
            seal = handoff_contract._validate_planning_seal(handoff.get("planningSeal"))
            digest = handoff_contract.planning_seal_digest(seal)
            criteria = handoff_contract.acceptance_criteria_from_ticket(seal["ticketPath"])
        except handoff_contract.HandoffError as exc:
            raise _PreflightTerminal("BLOCKED", "PLANNING_AUTHORITY_UNAVAILABLE", exc.message) from exc
        if digest != handoff.get("planningSealDigest") or criteria != _expected_criteria(handoff):
            raise _PreflightTerminal("BLOCKED", "PLANNING_AUTHORITY_CHANGED", "planning authority or exact AC changed")

    def _verify_authorizations(
        self,
        *,
        context: Mapping[str, Any],
        plan: Mapping[str, Any],
    ) -> list[dict[str, str]]:
        observed: list[dict[str, str]] = []
        with self.workflow._transaction() as connection:
            for entry in plan["authorizationRefs"]:
                row = connection.execute(
                    "SELECT * FROM authorizations WHERE authorization_ref = ?",
                    (entry["authorizationRef"],),
                ).fetchone()
                if (
                    row is None
                    or row["invocation_ref"] != context["assessor"]["invocation_ref"]
                    or row["scope_sha256"] != entry["scopeSha256"]
                ):
                    raise _PreflightTerminal(
                        "BLOCKED",
                        "AUTHORIZATION_UNAVAILABLE",
                        "authorization ref is absent, stale, or outside this invocation",
                    )
                observed.append(dict(entry))
        return observed

    @staticmethod
    def _finalize_paths(plan: Mapping[str, Any], project_root: Path) -> dict[str, Any]:
        finalized = json.loads(_canonical_json(plan))
        finalized["executorPolicy"] = {
            "executorVersion": PROCESS_EXECUTOR_VERSION,
            "environmentPolicy": PROCESS_ENVIRONMENT_POLICY,
        }
        for review_index, review in enumerate(finalized["sourceReviews"]):
            for anchor_index, anchor in enumerate(review["basisAnchors"]):
                _check_anchor(anchor, f"sourceReviews[{review_index}].basisAnchors[{anchor_index}]")
        for flow_index, flow in enumerate(finalized["flows"]):
            for anchor_index, anchor in enumerate(flow["basisAnchors"]):
                _check_anchor(anchor, f"flows[{flow_index}].basisAnchors[{anchor_index}]")
            for step_index, step in enumerate(flow["steps"]):
                for anchor_index, anchor in enumerate(step["sourceBinding"]["bindingBasisAnchors"]):
                    _check_anchor(
                        anchor,
                        f"flows[{flow_index}].steps[{step_index}].sourceBinding.bindingBasisAnchors[{anchor_index}]",
                    )
                try:
                    identity = executable_identity.observe_executable_identity(
                        step["executable"]
                    )
                    cwd = Path(step["cwd"]).resolve(strict=True)
                except executable_identity.ExecutableIdentityError as exc:
                    raise _PreflightTerminal("INCOMPLETE", exc.code, exc.message) from exc
                except OSError as exc:
                    raise _PreflightTerminal("INCOMPLETE", "PROCESS_TARGET_UNAVAILABLE", str(exc)) from exc
                if not cwd.is_dir() or (cwd != project_root and project_root not in cwd.parents):
                    raise _PreflightTerminal("BLOCKED", "PROCESS_TARGET_OUTSIDE_PROJECT", "cwd is outside project root")
                if step["sourceBinding"]["targetIdentityOrRevision"] != str(project_root):
                    raise _PreflightTerminal(
                        "BLOCKED", "SOURCE_BINDING_MISMATCH", "CURRENT_PROJECT_ROOT target differs from project root"
                    )
                step["executorVersion"] = PROCESS_EXECUTOR_VERSION
                step["environmentPolicy"] = PROCESS_ENVIRONMENT_POLICY
                step["executable"] = identity["canonicalPath"]
                step["executableIdentity"] = identity
                step["cwd"] = str(cwd)
            flow["steps"], flow["correlationBindings"] = _apply_correlations(
                flow["steps"], flow["correlationBindings"]
            )
            for step in flow["steps"]:
                _finalize_request_digests(step)
        return finalized

    @staticmethod
    def replay_authorization_scope(
        *,
        mechanism: str,
        prior_run_ref: str,
        prior_flow_id: str,
        prior_step_id: str,
        new_request_digest: str,
        target_binding_digest: str,
    ) -> str:
        if mechanism not in {"EXACT_IDEMPOTENCY", "UNIQUE_CORRELATION"}:
            raise VerificationError("MALFORMED_REPLAY_SAFETY", "unsupported replay-safety mechanism")
        if not isinstance(prior_run_ref, str) or not RUN_REF_PATTERN.fullmatch(prior_run_ref):
            raise VerificationError("MALFORMED_REPLAY_SAFETY", "prior run ref is malformed")
        prior_flow_id = _identifier(prior_flow_id, "priorFlowId")
        prior_step_id = _identifier(prior_step_id, "priorStepId")
        new_request_digest = _sha256(new_request_digest, "newRequestDigest")
        target_binding_digest = _sha256(target_binding_digest, "targetBindingDigest")
        return _digest(
            {
                "protocol": "verification-replay-safety-v1",
                "mechanism": mechanism,
                "priorRunRef": prior_run_ref,
                "priorFlowId": prior_flow_id,
                "priorStepId": prior_step_id,
                "newRequestDigest": new_request_digest,
                "targetBindingDigest": target_binding_digest,
            }
        )

    def _replay_preflight(
        self,
        *,
        context: Mapping[str, Any],
        plan: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        tip = context["tip"]
        if tip["node_kind"] != "VERIFICATION_RESULT" or tip["verification_status"] not in {
            "INCOMPLETE",
            "BLOCKED",
        }:
            return []
        predecessor_runs: list[str] = []
        with self.workflow._transaction() as connection:
            current = connection.execute(
                "SELECT * FROM nodes WHERE node_ref = ?", (tip["node_ref"],)
            ).fetchone()
            for _ in range(workflow_store.MAX_LINEAGE_NODES):
                if current is None or current["node_kind"] != "VERIFICATION_RESULT":
                    break
                payload = _decode_json(current["payload_json"], "predecessor result")
                if payload.get("implementationHandoffRef") != context["handoff"]["implementationHandoffRef"]:
                    break
                prior_run_ref = payload.get("verificationRunRef")
                if not isinstance(prior_run_ref, str) or not RUN_REF_PATTERN.fullmatch(prior_run_ref):
                    raise _PreflightTerminal(
                        "INCOMPLETE", "PRIOR_EFFECT_EVIDENCE_UNAVAILABLE", "prior run ref is absent"
                    )
                predecessor_runs.append(prior_run_ref)
                edge = connection.execute(
                    "SELECT predecessor_ref FROM edges WHERE successor_ref = ?",
                    (current["node_ref"],),
                ).fetchone()
                if edge is None:
                    break
                current = connection.execute(
                    "SELECT * FROM nodes WHERE node_ref = ?", (edge["predecessor_ref"],)
                ).fetchone()
            rows = []
            for prior_run_ref in predecessor_runs:
                rows.extend(
                    connection.execute(
                        """
                        SELECT run_ref, flow_id, step_id, status, request_sha256
                        FROM verification_attempts
                        WHERE run_ref = ? AND step_role IN ('ACTION', 'CLEANUP')
                        ORDER BY attempt_id
                        """,
                        (prior_run_ref,),
                    ).fetchall()
                )
        ambiguous = [row for row in rows if row["status"] in AMBIGUOUS_ACTION_STATUSES]
        if not ambiguous:
            return []
        action_steps = [
            (flow, step)
            for flow in plan["flows"]
            for step in flow["steps"]
            if step["role"] in {"ACTION", "CLEANUP"}
        ]
        if not action_steps:
            return [
                {
                    "priorRunRefs": predecessor_runs,
                    "disposition": "NO_NEW_EFFECTFUL_STEP",
                    "ambiguousAttemptCount": len(ambiguous),
                }
            ]
        authorized_scopes = {entry["scopeSha256"] for entry in plan["authorizationRefs"]}
        guards: list[dict[str, Any]] = []
        for prior in ambiguous:
            for flow, step in action_steps:
                candidate_methods = ["EXACT_IDEMPOTENCY"]
                if any(
                    binding["actionStepId"] == step["stepId"]
                    for binding in flow["correlationBindings"]
                ):
                    candidate_methods.append("UNIQUE_CORRELATION")
                matched = None
                for mechanism in candidate_methods:
                    request_digest = (
                        step["repeatRequestDigest"]
                        if mechanism == "EXACT_IDEMPOTENCY"
                        else step["canonicalRequestDigest"]
                    )
                    scope = self.replay_authorization_scope(
                        mechanism=mechanism,
                        prior_run_ref=prior["run_ref"],
                        prior_flow_id=prior["flow_id"],
                        prior_step_id=prior["step_id"],
                        new_request_digest=request_digest,
                        target_binding_digest=step["sourceBindingDigest"],
                    )
                    if scope in authorized_scopes:
                        matched = {"mechanism": mechanism, "scopeSha256": scope}
                        break
                if matched is None:
                    raise _PreflightTerminal(
                        "BLOCKED",
                        "AMBIGUOUS_PRIOR_EFFECT_REPLAY_FORBIDDEN",
                        "effectful replay lacks authoritative readback, exact idempotency, or unique correlation authority",
                    )
                guards.append(
                    {
                        "priorRunRef": prior["run_ref"],
                        "priorFlowId": prior["flow_id"],
                        "priorStepId": prior["step_id"],
                        "newFlowId": flow["flowId"],
                        "newStepId": step["stepId"],
                        **matched,
                    }
                )
        return guards

    def _update_preflight(
        self,
        *,
        run_ref: str,
        preflight: Mapping[str, Any],
        event_kind: str,
    ) -> None:
        encoded = _canonical_json(preflight)
        with self.workflow._transaction() as connection:
            run = connection.execute("SELECT state FROM verification_runs WHERE run_ref = ?", (run_ref,)).fetchone()
            if run is None or run["state"] != "PREFLIGHT":
                raise VerificationError("VERIFICATION_RUN_NOT_PREFLIGHT", "run cannot accept preflight observations")
            connection.execute(
                "UPDATE verification_runs SET preflight_json = ? WHERE run_ref = ? AND state = 'PREFLIGHT'",
                (encoded, run_ref),
            )
            self._event_locked(connection, run_ref, event_kind, preflight)

    def _seal_plan(self, *, run_ref: str, plan: Mapping[str, Any], preflight: Mapping[str, Any]) -> str:
        _require_current_process_plan(plan)
        encoded = _canonical_json(plan)
        plan_digest = hashlib.sha256(encoded).hexdigest()
        with self.workflow._transaction() as connection:
            run = connection.execute("SELECT state FROM verification_runs WHERE run_ref = ?", (run_ref,)).fetchone()
            if run is None or run["state"] != "PREFLIGHT":
                raise VerificationError("VERIFICATION_RUN_NOT_PREFLIGHT", "run cannot be sealed")
            connection.execute(
                """
                UPDATE verification_runs
                SET preflight_json = ?, sealed_plan_json = ?, sealed_plan_sha256 = ?, state = 'SEALED'
                WHERE run_ref = ? AND state = 'PREFLIGHT'
                """,
                (_canonical_json(preflight), encoded, plan_digest, run_ref),
            )
            self._event_locked(
                connection,
                run_ref,
                "PLAN_SEALED",
                {"sealedPlanDigest": plan_digest, "sealedAt": _now()},
            )
        return plan_digest

    def _publish_preflight_result(
        self,
        *,
        assessor_capability: str,
        run_ref: str,
    ) -> dict[str, Any]:
        try:
            with self.workflow._transaction() as connection:
                _, run, claim = self._run_for_actor_locked(
                    connection, assessor_capability, run_ref
                )
                if (
                    run["state"] != "PREFLIGHT"
                    or claim["state"] != "ACTIVE"
                    or claim["transition_kind"] != "VERIFY"
                    or claim["execution_ref"] != run_ref
                    or run["root_ref"] != claim["root_ref"]
                    or run["planning_identity"] != claim["planning_identity"]
                    or run["source_identity"] != claim["source_identity"]
                ):
                    raise VerificationError(
                        "VERIFICATION_RUN_NOT_PUBLISHABLE",
                        "preflight run identity is not publishable",
                    )
                preflight = _decode_json(run["preflight_json"], "terminal preflight")
                terminal_events = connection.execute(
                    """
                    SELECT payload_json, payload_sha256
                    FROM verification_events
                    WHERE run_ref = ? AND event_kind = 'PREFLIGHT_TERMINAL'
                    ORDER BY event_id
                    """,
                    (run_ref,),
                ).fetchall()
                if len(terminal_events) != 1:
                    raise VerificationError(
                        "STORE_CORRUPT", "preflight requires exactly one terminal event"
                    )
                event_bytes = bytes(terminal_events[0]["payload_json"])
                if hashlib.sha256(event_bytes).hexdigest() != terminal_events[0]["payload_sha256"]:
                    raise VerificationError(
                        "STORE_CORRUPT", "preflight terminal event digest differs"
                    )
                event_payload = _decode_json(event_bytes, "preflight terminal event")
                terminals = [
                    item
                    for item in preflight.get("observations", [])
                    if isinstance(item, Mapping)
                    and item.get("observation") == "PREFLIGHT_TERMINAL"
                ]
                if preflight.get("stage") != "TERMINAL" or len(terminals) != 1:
                    raise VerificationError(
                        "STORE_CORRUPT", "stored terminal preflight is malformed"
                    )
                terminal = terminals[0]
                status = terminal.get("status")
                reason_code = terminal.get("reasonCode")
                if (
                    event_payload != preflight
                    or status not in {"INCOMPLETE", "BLOCKED"}
                    or not isinstance(reason_code, str)
                    or not reason_code
                ):
                    raise VerificationError(
                        "STORE_CORRUPT", "preflight terminal event and run facts differ"
                    )
                self.workflow._ensure_claim_closure_budget_locked(
                    connection,
                    claimant_capability=assessor_capability,
                    claim_ref=claim["claim_ref"],
                    amounts=_budget_vector(closureOperations=1),
                )
                result_ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
                completed_at = _now()
                payload = {
                    "protocolVersion": PROTOCOL_VERSION,
                    "verificationResultRef": result_ref,
                    "verificationStatus": status,
                    "implementationHandoffRef": run["implementation_handoff_ref"],
                    "planningSealDigest": run["planning_identity"],
                    "finalSourceIdentity": run["source_identity"],
                    "verificationRunRef": run_ref,
                    "sealedPlanDigest": None,
                    "criterionResults": [],
                    "reasonCodes": [reason_code],
                    "completedAt": completed_at,
                }
                node = self.workflow._close_successor_locked(
                    connection,
                    claimant_capability=assessor_capability,
                    claim_ref=claim["claim_ref"],
                    node_ref=result_ref,
                    node_kind="VERIFICATION_RESULT",
                    protocol_version=PROTOCOL_VERSION,
                    planning_identity=run["planning_identity"],
                    source_identity=run["source_identity"],
                    verification_status=status,
                    payload=payload,
                    verification_run_ref=run_ref,
                    created_at=completed_at,
                )
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        except sqlite3.IntegrityError as exc:
            raise VerificationError(
                "ATOMIC_PUBLICATION_CONFLICT", "preflight result publication conflicted"
            ) from exc
        if node["payload"] != payload:
            raise VerificationError("PUBLICATION_FAILED", "stored preflight result readback differs")
        return payload

    def seal_run(
        self,
        *,
        assessor_capability: str,
        claim_ref: str,
        implementation_handoff_ref: str,
        verification_draft: Mapping[str, Any],
    ) -> dict[str, Any]:
        context = self._claim_context(
            assessor_capability=assessor_capability,
            claim_ref=claim_ref,
            implementation_handoff_ref=implementation_handoff_ref,
        )
        claim = context["claim"]
        run_ref = claim["execution_ref"]
        if not RUN_REF_PATTERN.fullmatch(run_ref):
            raise VerificationError("VERIFY_CLAIM_MISMATCH", "claim run ref is malformed")
        try:
            normalized = _normalize_draft(
                verification_draft,
                handoff=context["handoff"],
                expected_source=claim["source_identity"],
            )
            draft_digest = _digest(normalized)
            project_root = self._project_root(context["handoff"])
        except VerificationError as exc:
            try:
                self.workflow.release_unstarted_claim(
                    claimant_capability=assessor_capability, claim_ref=claim_ref
                )
            except workflow_store.WorkflowStoreError:
                pass
            raise exc

        with self.workflow._transaction() as connection:
            existing_run = connection.execute(
                "SELECT * FROM verification_runs WHERE run_ref = ?", (run_ref,)
            ).fetchone()
        if existing_run is None:
            self._insert_preflight_run(
                context=context,
                project_root=project_root,
                draft_digest=draft_digest,
            )
        else:
            if (
                existing_run["claim_ref"] != claim_ref
                or existing_run["assessor_actor_ref"] != context["assessor"]["actor_ref"]
                or existing_run["implementation_handoff_ref"] != implementation_handoff_ref
                or existing_run["project_root"] != str(project_root)
                or existing_run["planning_identity"] != claim["planning_identity"]
                or existing_run["source_identity"] != claim["source_identity"]
            ):
                raise VerificationError(
                    "VERIFICATION_RUN_MISMATCH", "existing run differs from the claim context"
                )
            stored_preflight = _decode_json(
                existing_run["preflight_json"], "existing verification preflight"
            )
            if stored_preflight.get("draftDigest") != draft_digest:
                raise VerificationError(
                    "SEALED_PLAN_RETRY_MISMATCH", "seal retry supplied another verification draft"
                )
            if existing_run["state"] == "SEALED":
                stored_plan = self._load_plan(existing_run)
                _require_current_process_plan(stored_plan)
                return {
                    "verificationRunRef": run_ref,
                    "implementationHandoffRef": implementation_handoff_ref,
                    "sealedPlanDigest": existing_run["sealed_plan_sha256"],
                    "state": "SEALED",
                    "plan": self._public_plan(stored_plan),
                }
            terminal = next(
                (
                    item
                    for item in reversed(stored_preflight.get("observations", []))
                    if isinstance(item, Mapping)
                    and item.get("observation") == "PREFLIGHT_TERMINAL"
                ),
                None,
            )
            if stored_preflight.get("stage") == "TERMINAL" and terminal is not None:
                terminal_status = terminal.get("status")
                terminal_reason = terminal.get("reasonCode")
                if terminal_status not in {"INCOMPLETE", "BLOCKED"} or not isinstance(
                    terminal_reason, str
                ):
                    raise VerificationError(
                        "STORE_CORRUPT", "stored terminal preflight closure is malformed"
                    )
                return self._publish_preflight_result(
                    assessor_capability=assessor_capability,
                    run_ref=run_ref,
                )
            if existing_run["state"] != "PREFLIGHT" or stored_preflight.get("stage") != "STARTED":
                raise VerificationError(
                    "VERIFICATION_RUN_NOT_PREFLIGHT", "existing run cannot resume preflight"
                )
        observations: list[dict[str, Any]] = []
        try:
            observed_source = self._capture_source(project_root)
            observations.append(
                {
                    "observation": "CURRENT_PROJECT_SOURCE",
                    "expected": claim["source_identity"],
                    "actual": observed_source,
                }
            )
            if observed_source != claim["source_identity"]:
                raise _PreflightTerminal(
                    "INCOMPLETE",
                    "CANDIDATE_IDENTITY_UNAVAILABLE_AT_START",
                    "current project identity differs from the implementation handoff",
                )
            self._verify_planning(context["handoff"])
            observations.append({"observation": "PLANNING_AUTHORITY", "state": "CURRENT"})
            finalized = self._finalize_paths(normalized, project_root)
            observations.append({"observation": "BASIS_AND_PROCESS_TARGETS", "state": "CURRENT"})
            authorizations = self._verify_authorizations(context=context, plan=finalized)
            observations.append(
                {
                    "observation": "AUTHORIZATION_REFS",
                    "state": "CURRENT",
                    "authorizationRefs": authorizations,
                }
            )
            replay_guards = self._replay_preflight(context=context, plan=finalized)
            observations.append(
                {"observation": "CROSS_RUN_REPLAY", "state": "SAFE", "guards": replay_guards}
            )
        except _PreflightTerminal as terminal:
            observations.append(
                {
                    "observation": "PREFLIGHT_TERMINAL",
                    "status": terminal.status,
                    "reasonCode": terminal.reason_code,
                    "messageSha256": hashlib.sha256(terminal.message.encode("utf-8")).hexdigest(),
                }
            )
            preflight = {
                "stage": "TERMINAL",
                "draftDigest": draft_digest,
                "observations": observations,
            }
            self._update_preflight(
                run_ref=run_ref,
                preflight=preflight,
                event_kind="PREFLIGHT_TERMINAL",
            )
            return self._publish_preflight_result(
                assessor_capability=assessor_capability,
                run_ref=run_ref,
            )

        preflight = {
            "stage": "PASSED",
            "draftDigest": draft_digest,
            "observations": observations,
        }
        plan_digest = self._seal_plan(run_ref=run_ref, plan=finalized, preflight=preflight)
        return {
            "verificationRunRef": run_ref,
            "implementationHandoffRef": implementation_handoff_ref,
            "sealedPlanDigest": plan_digest,
            "state": "SEALED",
            "plan": self._public_plan(finalized),
        }

    @staticmethod
    def _public_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
        result = json.loads(_canonical_json(plan))
        for flow in result["flows"]:
            flow["steps"] = [_public_step(step) for step in flow["steps"]]
            for binding in flow["correlationBindings"]:
                binding.pop("token", None)
        return result

    def _run_for_actor_locked(self, connection, assessor_capability: str, run_ref: str):
        if not isinstance(run_ref, str) or not RUN_REF_PATTERN.fullmatch(run_ref):
            raise VerificationError("MALFORMED_RUN_REF", "verification run ref is malformed")
        try:
            assessor = self.workflow._actor_for_capability_locked(
                connection, assessor_capability, expected_role="ASSESSOR"
            )
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        run = connection.execute("SELECT * FROM verification_runs WHERE run_ref = ?", (run_ref,)).fetchone()
        if run is None or run["assessor_actor_ref"] != assessor["actor_ref"]:
            raise VerificationError("VERIFICATION_RUN_ACTOR_MISMATCH", "run is absent or owned by another Assessor")
        claim = connection.execute("SELECT * FROM claims WHERE claim_ref = ?", (run["claim_ref"],)).fetchone()
        if claim is None or claim["claimant_actor_ref"] != assessor["actor_ref"]:
            raise VerificationError("VERIFY_CLAIM_MISMATCH", "run claim differs from Assessor")
        return assessor, run, claim

    @staticmethod
    def _load_plan(run) -> dict[str, Any]:
        if run["state"] not in {"SEALED", "CLOSED"} or run["sealed_plan_json"] is None:
            raise VerificationError("VERIFICATION_RUN_NOT_SEALED", "run has no sealed plan")
        encoded = bytes(run["sealed_plan_json"])
        if hashlib.sha256(encoded).hexdigest() != run["sealed_plan_sha256"]:
            raise VerificationError("STORE_CORRUPT", "sealed plan digest differs")
        value = _decode_json(encoded, "sealed plan")
        if not isinstance(value, dict):
            raise VerificationError("STORE_CORRUPT", "sealed plan is not an object")
        return value

    @staticmethod
    def _find_step(plan: Mapping[str, Any], flow_id: str, step_id: str) -> tuple[dict[str, Any], dict[str, Any], int]:
        flow = next((item for item in plan["flows"] if item["flowId"] == flow_id), None)
        if flow is None:
            raise VerificationError("SEALED_STEP_NOT_FOUND", "flow is not in the sealed plan")
        for index, step in enumerate(flow["steps"]):
            if step["stepId"] == step_id:
                return flow, step, index
        raise VerificationError("SEALED_STEP_NOT_FOUND", "step is not in the sealed plan")

    def _start_step_locked(
        self,
        connection,
        *,
        run,
        claim,
        flow: Mapping[str, Any],
        step: Mapping[str, Any],
        step_index: int,
    ) -> None:
        if run["state"] != "SEALED" or claim["state"] != "ACTIVE":
            raise VerificationError("VERIFICATION_RUN_NOT_EXECUTABLE", "run or claim is closed")
        if step["role"] == "ACTION":
            contradiction = connection.execute(
                """
                SELECT 1 FROM verification_events
                WHERE run_ref = ? AND event_kind = 'CONTRADICTION_DECLARED'
                LIMIT 1
                """,
                (run["run_ref"],),
            ).fetchone()
            if contradiction is not None:
                raise VerificationError(
                    "ACTION_STOPPED_AFTER_CONTRADICTION",
                    "new effectful ACTION is forbidden after a durable contradiction declaration",
                )
        existing = connection.execute(
            "SELECT state FROM verification_step_executions WHERE run_ref = ? AND flow_id = ? AND step_id = ?",
            (run["run_ref"], flow["flowId"], step["stepId"]),
        ).fetchone()
        if existing is not None:
            raise VerificationError("STEP_CARDINALITY_EXCEEDED", "sealed step already started")
        for prior in flow["steps"][:step_index]:
            row = connection.execute(
                "SELECT state FROM verification_step_executions WHERE run_ref = ? AND flow_id = ? AND step_id = ?",
                (run["run_ref"], flow["flowId"], prior["stepId"]),
            ).fetchone()
            if row is None or row["state"] != "COMPLETED":
                raise VerificationError("STEP_SEQUENCE_VIOLATION", "prior sealed step is not complete")
        reservation = connection.execute(
            "SELECT * FROM budget_reservations WHERE reservation_ref = ?", (claim["budget_reservation_ref"],)
        ).fetchone()
        if reservation is None or reservation["state"] != "ACTIVE":
            raise VerificationError("BUDGET_RESERVATION_NOT_ACTIVE", "run budget reservation is closed")
        if step["role"] == "ACTION":
            try:
                self.workflow._assert_invocation_spend_open_locked(
                    connection, reservation["invocation_ref"]
                )
            except workflow_store.WorkflowStoreError as exc:
                raise VerificationError(exc.code, exc.message) from exc
        spend = self.workflow._stored_budget(reservation["spend_reserved_json"], "reservation.spendReserved")
        used = self.workflow._stored_budget(reservation["spend_used_json"], "reservation.spendUsed")
        poll_count = step["pollPolicy"]["maxAttempts"] if step["role"] == "READBACK" else 1
        delta = _budget_vector(
            effectfulActions=1 if step["role"] in {"ACTION", "CLEANUP"} else 0,
            toolCostUnits=poll_count,
        )
        next_used = {field: used[field] + delta[field] for field in workflow_store.BUDGET_FIELDS}
        exceeded = [field for field in workflow_store.BUDGET_FIELDS if next_used[field] > spend[field]]
        if exceeded:
            raise VerificationError("BUDGET_RESERVATION_EXCEEDED", f"step exceeds reserved budget: {', '.join(exceeded)}")
        started_at = _now()
        connection.execute(
            "UPDATE budget_reservations SET spend_used_json = ? WHERE reservation_ref = ?",
            (_canonical_json(next_used), reservation["reservation_ref"]),
        )
        connection.execute(
            """
            INSERT INTO verification_step_executions(
                run_ref, flow_id, step_id, state, request_sha256, started_at, completed_at
            ) VALUES (?, ?, ?, 'STARTED', ?, ?, NULL)
            """,
            (run["run_ref"], flow["flowId"], step["stepId"], step["canonicalRequestDigest"], started_at),
        )
        self._event_locked(
            connection,
            run["run_ref"],
            "STEP_STARTED",
            {
                "flowId": flow["flowId"],
                "stepId": step["stepId"],
                "role": step["role"],
                "canonicalRequestDigest": step["canonicalRequestDigest"],
            },
        )

    def _capture_identity_for_attempt(self, project_root: Path) -> tuple[str | None, str | None]:
        try:
            return baseline_capsule.capture_identity(project_root)["sourceIdentity"], None
        except baseline_capsule.CapsuleError as exc:
            return None, exc.code

    @staticmethod
    def _observe_executable_for_attempt(
        path: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None, int]:
        started = time.monotonic()
        try:
            identity = dict(executable_identity.observe_executable_identity(path))
            error = None
        except executable_identity.ExecutableIdentityError as exc:
            identity = None
            error = {"code": exc.code, "bytesHashed": exc.bytes_hashed}
        return identity, error, int((time.monotonic() - started) * 1000)

    def _append_attempt(
        self,
        *,
        run_ref: str,
        flow: Mapping[str, Any],
        step: Mapping[str, Any],
        poll_index: int,
        status: str,
        source_before: str | None,
        source_after: str | None,
        artifact_payload: Mapping[str, Any] | None,
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        created_at = _now()
        artifact_ref: str | None = None
        encoded_result = _canonical_json(result)
        with self.workflow._transaction() as connection:
            run = connection.execute("SELECT state FROM verification_runs WHERE run_ref = ?", (run_ref,)).fetchone()
            if run is None or run["state"] != "SEALED":
                raise VerificationError("VERIFICATION_RUN_NOT_EXECUTABLE", "run closed during step execution")
            if artifact_payload is not None:
                artifact_ref = f"verification:artifact:v1:{uuid.uuid4().hex}"
                encoded_artifact = _canonical_json(artifact_payload)
                connection.execute(
                    """
                    INSERT INTO verification_artifacts(
                        artifact_ref, run_ref, media_type, payload, payload_sha256, byte_count, created_at
                    ) VALUES (?, ?, 'application/json', ?, ?, ?, ?)
                    """,
                    (
                        artifact_ref,
                        run_ref,
                        encoded_artifact,
                        hashlib.sha256(encoded_artifact).hexdigest(),
                        len(encoded_artifact),
                        created_at,
                    ),
                )
            cursor = connection.execute(
                """
                INSERT INTO verification_attempts(
                    run_ref, flow_id, step_id, step_role, poll_index, status,
                    request_sha256, source_identity_before, source_identity_after,
                    artifact_ref, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_ref,
                    flow["flowId"],
                    step["stepId"],
                    step["role"],
                    poll_index,
                    status,
                    step["canonicalRequestDigest"],
                    source_before,
                    source_after,
                    artifact_ref,
                    encoded_result,
                    created_at,
                ),
            )
            attempt_id = int(cursor.lastrowid)
            result_digest = hashlib.sha256(encoded_result).hexdigest()
            self._event_locked(
                connection,
                run_ref,
                "ATTEMPT_APPENDED",
                {
                    "attemptId": attempt_id,
                    "flowId": flow["flowId"],
                    "stepId": step["stepId"],
                    "pollIndex": poll_index,
                    "status": status,
                    "artifactRef": artifact_ref,
                    "canonicalRequestDigest": step["canonicalRequestDigest"],
                    "resultDigest": result_digest,
                },
            )
            if status == "EXECUTABLE_IDENTITY_DRIFT":
                self._event_locked(
                    connection,
                    run_ref,
                    "EXECUTABLE_IDENTITY_DRIFT",
                    {
                        "attemptId": attempt_id,
                        "flowId": flow["flowId"],
                        "stepId": step["stepId"],
                        "pollIndex": poll_index,
                        "canonicalRequestDigest": step["canonicalRequestDigest"],
                        "phase": result.get("executableIdentityPhase"),
                        "processStarted": result.get("processStarted"),
                        "expectedExecutableIdentity": result.get(
                            "expectedExecutableIdentity"
                        ),
                        "observedExecutableIdentity": result.get(
                            "observedExecutableIdentity"
                        ),
                        "identityError": result.get("executableIdentityError"),
                        "bytesHashed": result.get("executableBytesHashed"),
                        "durationMs": result.get("durationMs"),
                        "resultDigest": result_digest,
                    },
                )
        return {
            "attemptId": attempt_id,
            "flowId": flow["flowId"],
            "stepId": step["stepId"],
            "pollIndex": poll_index,
            "status": status,
            "canonicalRequestDigest": step["canonicalRequestDigest"],
            "sourceIdentityBefore": source_before,
            "sourceIdentityAfter": source_after,
            "artifactRef": artifact_ref,
            "result": dict(result),
            "createdAt": created_at,
        }

    def execute_step(
        self,
        *,
        assessor_capability: str,
        verification_run_ref: str,
        flow_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        if not isinstance(verification_run_ref, str) or not RUN_REF_PATTERN.fullmatch(
            verification_run_ref
        ):
            raise VerificationError(
                "MALFORMED_RUN_REF", "verification run ref is malformed"
            )
        flow_id = _identifier(flow_id, "flowId")
        step_id = _identifier(step_id, "stepId")
        lock_fd = self._acquire_step_execution_lock(
            run_ref=verification_run_ref,
            flow_id=flow_id,
            step_id=step_id,
        )
        try:
            return self._execute_step_owned(
                assessor_capability=assessor_capability,
                verification_run_ref=verification_run_ref,
                flow_id=flow_id,
                step_id=step_id,
            )
        finally:
            os.close(lock_fd)

    def _execute_step_owned(
        self,
        *,
        assessor_capability: str,
        verification_run_ref: str,
        flow_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        with self.workflow._transaction() as connection:
            _, run, claim = self._run_for_actor_locked(connection, assessor_capability, verification_run_ref)
            plan = self._load_plan(run)
            _require_current_process_plan(plan)
            flow, step, step_index = self._find_step(plan, flow_id, step_id)
            self._start_step_locked(
                connection,
                run=run,
                claim=claim,
                flow=flow,
                step=step,
                step_index=step_index,
            )

        project_root = Path(run["project_root"])
        expected_source = run["source_identity"]
        poll_count = step["pollPolicy"]["maxAttempts"] if step["role"] == "READBACK" else 1
        attempts: list[dict[str, Any]] = []
        expected_executable_identity = dict(step["executableIdentity"])
        for poll_index in range(1, poll_count + 1):
            if poll_index > 1:
                time.sleep(step["pollPolicy"]["intervalMs"] / 1000.0)
            source_before, before_error = self._capture_identity_for_attempt(project_root)
            if before_error is not None or source_before != expected_source:
                identity_result: dict[str, Any] = {
                    "executor": "PROCESS",
                    "executorVersion": step["executorVersion"],
                    "environmentPolicy": step["environmentPolicy"],
                    "processStarted": False,
                    "identityError": before_error,
                    "expectedExecutableIdentity": expected_executable_identity,
                    "observedExecutableIdentity": None,
                    "executableIdentityBefore": None,
                    "executableIdentityAfter": None,
                    "executableIdentityPhase": None,
                    "executableIdentityError": None,
                    "executableBytesHashed": {"before": 0, "after": 0, "total": 0},
                    "durationMs": 0,
                    "actualSourceBinding": {
                        "mode": "CURRENT_PROJECT_ROOT",
                        "sourceIdentity": source_before,
                        "projectRoot": str(project_root),
                    },
                }
                attempts.append(
                    self._append_attempt(
                        run_ref=verification_run_ref,
                        flow=flow,
                        step=step,
                        poll_index=poll_index,
                        status="IDENTITY_DRIFT",
                        source_before=source_before,
                        source_after=source_before,
                        artifact_payload=None,
                        result=identity_result,
                    )
                )
                break

            executable_before, executable_before_error, before_identity_ms = (
                self._observe_executable_for_attempt(step["executable"])
            )
            executable_before_bytes = (
                int(executable_before["byteCount"])
                if executable_before is not None
                else int((executable_before_error or {}).get("bytesHashed", 0))
            )
            if executable_before_error is None and not executable_identity.executable_identities_equal(
                expected_executable_identity, executable_before
            ):
                executable_before_error = {
                    "code": "EXECUTABLE_IDENTITY_MISMATCH",
                    "bytesHashed": executable_before_bytes,
                }
            if executable_before_error is not None:
                pre_result: dict[str, Any] = {
                    "executor": "PROCESS",
                    "executorVersion": step["executorVersion"],
                    "environmentPolicy": step["environmentPolicy"],
                    "processStarted": False,
                    "expectedExecutableIdentity": expected_executable_identity,
                    "observedExecutableIdentity": executable_before,
                    "executableIdentityBefore": executable_before,
                    "executableIdentityAfter": None,
                    "executableIdentityPhase": "PRE",
                    "executableIdentityError": executable_before_error,
                    "executableBytesHashed": {
                        "before": executable_before_bytes,
                        "after": 0,
                        "total": executable_before_bytes,
                    },
                    "durationMs": before_identity_ms,
                    "identityObservationDurationMs": {
                        "before": before_identity_ms,
                        "after": 0,
                    },
                    "exitCode": None,
                    "errorCode": executable_before_error["code"],
                    "stdout": _artifact_projection(_bounded_output(b"")),
                    "stderr": _artifact_projection(_bounded_output(b"")),
                    "actualSourceBinding": {
                        "mode": "CURRENT_PROJECT_ROOT",
                        "sourceIdentity": source_before,
                        "projectRoot": str(project_root),
                    },
                }
                attempts.append(
                    self._append_attempt(
                        run_ref=verification_run_ref,
                        flow=flow,
                        step=step,
                        poll_index=poll_index,
                        status="EXECUTABLE_IDENTITY_DRIFT",
                        source_before=source_before,
                        source_after=source_before,
                        artifact_payload=None,
                        result=pre_result,
                    )
                )
                break

            environment = dict(step["environmentDelta"])
            started = time.monotonic()
            stdout = b""
            stderr = b""
            exit_code: int | None = None
            status = "EXITED"
            error_code: str | None = None
            process_started = False
            try:
                completed = subprocess.run(
                    [step["executable"], *step["argv"]],
                    cwd=step["cwd"],
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=MAX_PROCESS_TIMEOUT_SECONDS,
                )
                stdout = completed.stdout
                stderr = completed.stderr
                exit_code = completed.returncode
                process_started = True
            except subprocess.TimeoutExpired as exc:
                status = "TIMED_OUT"
                process_started = True
                stdout = exc.stdout if isinstance(exc.stdout, bytes) else (exc.stdout or "").encode("utf-8")
                stderr = exc.stderr if isinstance(exc.stderr, bytes) else (exc.stderr or "").encode("utf-8")
                error_code = "PROCESS_TIMEOUT"
            except OSError as exc:
                status = "TOOL_ERROR"
                error_code = type(exc).__name__
                stderr = str(exc).encode("utf-8", errors="replace")
            elapsed_ms = int((time.monotonic() - started) * 1000)
            source_after, after_error = self._capture_identity_for_attempt(project_root)
            if after_error is not None or source_after != expected_source:
                status = "IDENTITY_DRIFT"
            executable_after, executable_after_error, after_identity_ms = (
                self._observe_executable_for_attempt(step["executable"])
            )
            executable_after_bytes = (
                int(executable_after["byteCount"])
                if executable_after is not None
                else int((executable_after_error or {}).get("bytesHashed", 0))
            )
            if executable_after_error is None and not executable_identity.executable_identities_equal(
                expected_executable_identity, executable_after
            ):
                executable_after_error = {
                    "code": "EXECUTABLE_IDENTITY_MISMATCH",
                    "bytesHashed": executable_after_bytes,
                }
            if executable_after_error is not None:
                status = "EXECUTABLE_IDENTITY_DRIFT"
            stdout_full = _bounded_output(stdout)
            stderr_full = _bounded_output(stderr)
            artifact = {
                "protocolVersion": "verification-process-artifact-v1",
                "canonicalRequestDigest": step["canonicalRequestDigest"],
                "stdout": stdout_full,
                "stderr": stderr_full,
            }
            process_result: dict[str, Any] = {
                "executor": "PROCESS",
                "executorVersion": step["executorVersion"],
                "environmentPolicy": step["environmentPolicy"],
                "processStarted": process_started,
                "expectedExecutableIdentity": expected_executable_identity,
                "observedExecutableIdentity": executable_after,
                "executableIdentityBefore": executable_before,
                "executableIdentityAfter": executable_after,
                "executableIdentityPhase": (
                    "POST" if executable_after_error is not None else None
                ),
                "executableIdentityError": executable_after_error,
                "executableBytesHashed": {
                    "before": executable_before_bytes,
                    "after": executable_after_bytes,
                    "total": executable_before_bytes + executable_after_bytes,
                },
                "exitCode": exit_code,
                "durationMs": elapsed_ms,
                "identityObservationDurationMs": {
                    "before": before_identity_ms,
                    "after": after_identity_ms,
                },
                "errorCode": (
                    executable_after_error["code"]
                    if executable_after_error is not None
                    else error_code or after_error
                ),
                "stdout": _artifact_projection(stdout_full),
                "stderr": _artifact_projection(stderr_full),
                "actualSourceBinding": {
                    "mode": "CURRENT_PROJECT_ROOT",
                    "sourceIdentity": source_after,
                    "projectRoot": str(project_root),
                },
            }
            attempts.append(
                self._append_attempt(
                    run_ref=verification_run_ref,
                    flow=flow,
                    step=step,
                    poll_index=poll_index,
                    status=status,
                    source_before=source_before,
                    source_after=source_after,
                    artifact_payload=artifact,
                    result=process_result,
                )
            )
            if status in {"TOOL_ERROR", "IDENTITY_DRIFT", "EXECUTABLE_IDENTITY_DRIFT"}:
                break

        completed_at = _now()
        with self.workflow._transaction() as connection:
            completed = connection.execute(
                """
                UPDATE verification_step_executions
                SET state = 'COMPLETED', completed_at = ?
                WHERE run_ref = ? AND flow_id = ? AND step_id = ? AND state = 'STARTED'
                """,
                (completed_at, verification_run_ref, flow_id, step_id),
            )
            if completed.rowcount != 1:
                raise VerificationError(
                    "STORE_CORRUPT", "step execution changed before durable completion"
                )
            self._event_locked(
                connection,
                verification_run_ref,
                "STEP_COMPLETED",
                {
                    "flowId": flow_id,
                    "stepId": step_id,
                    "attemptCount": len(attempts),
                    "completedAt": completed_at,
                },
            )
        return {
            "verificationRunRef": verification_run_ref,
            "flowId": flow_id,
            "stepId": step_id,
            "logicalExecution": "COMPLETED",
            "attempts": attempts,
        }

    def declare_contradiction(
        self,
        *,
        assessor_capability: str,
        verification_run_ref: str,
        criterion_ref: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Durably stop later ACTIONs after one exact, complete obligation contradicts."""

        identity = _criterion_ref(criterion_ref, "criterionRef")
        with self.workflow._transaction() as connection:
            _, run, claim = self._run_for_actor_locked(
                connection, assessor_capability, verification_run_ref
            )
            if run["state"] != "SEALED" or claim["state"] != "ACTIVE":
                raise VerificationError("VERIFICATION_RUN_NOT_EXECUTABLE", "run or claim is closed")
            plan = self._load_plan(run)
            _require_current_process_plan(plan)
            criterion = next(
                (
                    item
                    for item in plan["criteria"]
                    if item["criterionIndex"] == identity["criterionIndex"]
                    and item["criterionRawSha256"] == identity["criterionRawSha256"]
                ),
                None,
            )
            if criterion is None:
                raise VerificationError("ACCEPTANCE_CRITERIA_MISMATCH", "criterion is not in the sealed plan")
            attempt_rows = connection.execute(
                "SELECT * FROM verification_attempts WHERE run_ref = ? ORDER BY attempt_id",
                (verification_run_ref,),
            ).fetchall()
            self._validate_attempt_event_ledger_locked(
                connection, verification_run_ref, attempt_rows
            )
            execution_rows = connection.execute(
                "SELECT * FROM verification_step_executions WHERE run_ref = ?",
                (verification_run_ref,),
            ).fetchall()
            artifacts = connection.execute(
                "SELECT artifact_ref, payload, payload_sha256 FROM verification_artifacts WHERE run_ref = ?",
                (verification_run_ref,),
            ).fetchall()
            existing_events = connection.execute(
                """
                SELECT payload_json FROM verification_events
                WHERE run_ref = ? AND event_kind = 'CONTRADICTION_DECLARED'
                """,
                (verification_run_ref,),
            ).fetchall()
        for event in existing_events:
            payload = _decode_json(event["payload_json"], "contradiction event")
            if (
                payload.get("criterionIndex") == identity["criterionIndex"]
                and payload.get("criterionRawSha256") == identity["criterionRawSha256"]
            ):
                raise VerificationError("CONTRADICTION_ALREADY_DECLARED", "criterion contradiction is already durable")
        executions = {(row["flow_id"], row["step_id"]): row["state"] for row in execution_rows}
        attempts = [self._attempt_view(row) for row in attempt_rows]
        artifact_tokens: dict[str, bytes] = {}
        for row in artifacts:
            artifact_bytes = bytes(row["payload"])
            if hashlib.sha256(artifact_bytes).hexdigest() != row["payload_sha256"]:
                raise VerificationError("STORE_CORRUPT", "verification artifact digest differs")
            artifact_tokens[row["artifact_ref"]] = artifact_bytes
        review_complete, flow_complete, _, drift, executable_drift, flow_uncertainty = self._evidence_state(
            plan=plan,
            executions=executions,
            attempts=attempts,
            expected_source=run["source_identity"],
            artifact_tokens=artifact_tokens,
        )
        complete_obligation = any(
            review_complete.get(review_id, False) for review_id in criterion["sourceReviewIds"]
        ) or any(flow_complete.get(flow_id, False) for flow_id in criterion["flowIds"])
        mapped_flow_uncertainty = any(
            flow_uncertainty.get(flow_id, False) for flow_id in criterion["flowIds"]
        )
        if not complete_obligation or drift or executable_drift or mapped_flow_uncertainty:
            raise VerificationError(
                "CONTRADICTION_WITHOUT_COMPLETE_EVIDENCE",
                "a contradiction declaration needs one presealed exact-identity complete obligation",
            )
        declared_at = _now()
        payload = {
            **identity,
            "lastAttemptId": max((item["attemptId"] for item in attempts), default=None),
            "declaredAt": declared_at,
        }
        with self.workflow._transaction() as connection:
            _, current_run, current_claim = self._run_for_actor_locked(
                connection, assessor_capability, verification_run_ref
            )
            if current_run["state"] != "SEALED" or current_claim["state"] != "ACTIVE":
                raise VerificationError("VERIFICATION_RUN_NOT_EXECUTABLE", "run closed during declaration")
            self._event_locked(
                connection,
                verification_run_ref,
                "CONTRADICTION_DECLARED",
                payload,
            )
        return {"verificationRunRef": verification_run_ref, **payload}

    @staticmethod
    def _normalize_assessments(raw: Any, criteria: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        if not isinstance(raw, list) or len(raw) != len(criteria):
            raise VerificationError("INCOMPLETE_CRITERION_ASSESSMENT", "every exact AC must be assessed once")
        result: list[dict[str, Any]] = []
        for offset, (raw_item, criterion) in enumerate(zip(raw, criteria)):
            locator = f"criterionAssessments[{offset}]"
            item = _mapping(raw_item, locator)
            _fields(item, {"criterionIndex", "criterionRawSha256", "verdict", "semanticRationale"}, locator)
            identity = _criterion_ref(
                {
                    "criterionIndex": item["criterionIndex"],
                    "criterionRawSha256": item["criterionRawSha256"],
                },
                locator,
            )
            expected = {
                "criterionIndex": criterion["criterionIndex"],
                "criterionRawSha256": criterion["criterionRawSha256"],
            }
            if identity != expected:
                raise VerificationError("ACCEPTANCE_CRITERIA_MISMATCH", f"{locator} is stale or reordered")
            verdict = item["verdict"]
            if verdict not in CRITERION_VERDICTS:
                raise VerificationError("MALFORMED_CRITERION_ASSESSMENT", f"{locator}.verdict is invalid")
            rationale = _bounded_string(item["semanticRationale"], f"{locator}.semanticRationale")
            if len(rationale.encode("utf-8")) > MAX_RATIONALE_BYTES:
                raise VerificationError("MALFORMED_CRITERION_ASSESSMENT", f"{locator}.semanticRationale is oversized")
            result.append({**identity, "verdict": verdict, "semanticRationale": rationale})
        return result

    @staticmethod
    def _attempt_view(row) -> dict[str, Any]:
        return {
            "attemptId": row["attempt_id"],
            "flowId": row["flow_id"],
            "stepId": row["step_id"],
            "stepRole": row["step_role"],
            "pollIndex": row["poll_index"],
            "status": row["status"],
            "canonicalRequestDigest": row["request_sha256"],
            "sourceIdentityBefore": row["source_identity_before"],
            "sourceIdentityAfter": row["source_identity_after"],
            "artifactRef": row["artifact_ref"],
            "result": _decode_json(row["result_json"], "verification attempt"),
            "createdAt": row["created_at"],
        }

    @staticmethod
    def _validate_attempt_event_ledger_locked(connection, run_ref: str, attempt_rows) -> None:
        event_rows = connection.execute(
            """
            SELECT event_kind, payload_json, payload_sha256
            FROM verification_events
            WHERE run_ref = ?
              AND event_kind IN ('ATTEMPT_APPENDED', 'EXECUTABLE_IDENTITY_DRIFT')
            ORDER BY event_id
            """,
            (run_ref,),
        ).fetchall()
        generic_events: dict[int, Mapping[str, Any]] = {}
        drift_events: dict[int, Mapping[str, Any]] = {}
        for event in event_rows:
            encoded = bytes(event["payload_json"])
            if hashlib.sha256(encoded).hexdigest() != event["payload_sha256"]:
                raise VerificationError("STORE_CORRUPT", "attempt event digest differs")
            payload = _decode_json(encoded, "attempt event")
            if not isinstance(payload, Mapping):
                raise VerificationError("STORE_CORRUPT", "attempt event payload is malformed")
            attempt_id = payload.get("attemptId")
            target = (
                drift_events
                if event["event_kind"] == "EXECUTABLE_IDENTITY_DRIFT"
                else generic_events
            )
            if (
                isinstance(attempt_id, bool)
                or not isinstance(attempt_id, int)
                or attempt_id in target
            ):
                raise VerificationError("STORE_CORRUPT", "attempt event linkage is not one-to-one")
            target[attempt_id] = payload

        expected_ids: set[int] = set()
        expected_drift_ids: set[int] = set()
        for row in attempt_rows:
            attempt_id = int(row["attempt_id"])
            expected_ids.add(attempt_id)
            encoded_result = bytes(row["result_json"])
            result = _decode_json(encoded_result, "verification attempt")
            if not isinstance(result, Mapping):
                raise VerificationError("STORE_CORRUPT", "attempt result is malformed")
            result_digest = hashlib.sha256(encoded_result).hexdigest()
            expected_generic = {
                "attemptId": attempt_id,
                "flowId": row["flow_id"],
                "stepId": row["step_id"],
                "pollIndex": row["poll_index"],
                "status": row["status"],
                "artifactRef": row["artifact_ref"],
                "canonicalRequestDigest": row["request_sha256"],
                "resultDigest": result_digest,
            }
            if generic_events.get(attempt_id) != expected_generic:
                raise VerificationError(
                    "STORE_CORRUPT", "attempt row and ATTEMPT_APPENDED event differ"
                )
            if row["status"] == "EXECUTABLE_IDENTITY_DRIFT":
                expected_drift_ids.add(attempt_id)
                expected_drift = {
                    "attemptId": attempt_id,
                    "flowId": row["flow_id"],
                    "stepId": row["step_id"],
                    "pollIndex": row["poll_index"],
                    "canonicalRequestDigest": row["request_sha256"],
                    "phase": result.get("executableIdentityPhase"),
                    "processStarted": result.get("processStarted"),
                    "expectedExecutableIdentity": result.get(
                        "expectedExecutableIdentity"
                    ),
                    "observedExecutableIdentity": result.get(
                        "observedExecutableIdentity"
                    ),
                    "identityError": result.get("executableIdentityError"),
                    "bytesHashed": result.get("executableBytesHashed"),
                    "durationMs": result.get("durationMs"),
                    "resultDigest": result_digest,
                }
                if drift_events.get(attempt_id) != expected_drift:
                    raise VerificationError(
                        "STORE_CORRUPT",
                        "executable drift attempt and durable event differ",
                    )
        if set(generic_events) != expected_ids or set(drift_events) != expected_drift_ids:
            raise VerificationError("STORE_CORRUPT", "attempt/event cardinality differs")

    @staticmethod
    def _anchor_is_current(anchor: Mapping[str, Any]) -> bool:
        try:
            _check_anchor(anchor, "publication basis anchor")
            return True
        except _PreflightTerminal:
            return False

    @staticmethod
    def _validate_attempt_executable_binding(
        attempt: Mapping[str, Any], step: Mapping[str, Any]
    ) -> None:
        result = attempt.get("result")
        if not isinstance(result, Mapping):
            raise VerificationError("STORE_CORRUPT", "attempt result is not an object")
        if (
            result.get("executor") != "PROCESS"
            or result.get("executorVersion") != PROCESS_EXECUTOR_VERSION
            or result.get("environmentPolicy") != PROCESS_ENVIRONMENT_POLICY
        ):
            raise VerificationError(
                "STORE_CORRUPT", "attempt executor policy differs from sealed process-v3"
            )
        try:
            sealed_identity = executable_identity.validate_executable_identity(
                step.get("executableIdentity"),
                expected_canonical_path=step.get("executable"),
            )
            result_expected = executable_identity.validate_executable_identity(
                result.get("expectedExecutableIdentity"),
                expected_canonical_path=step.get("executable"),
            )
        except executable_identity.ExecutableIdentityError as exc:
            raise VerificationError("STORE_CORRUPT", exc.message) from exc
        if sealed_identity != result_expected:
            raise VerificationError(
                "STORE_CORRUPT", "attempt expected executable identity differs from seal"
            )
        duration = result.get("durationMs")
        byte_counts = result.get("executableBytesHashed")
        if (
            isinstance(duration, bool)
            or not isinstance(duration, int)
            or duration < 0
            or not isinstance(byte_counts, Mapping)
            or set(byte_counts) != {"before", "after", "total"}
            or any(
                isinstance(byte_counts.get(key), bool)
                or not isinstance(byte_counts.get(key), int)
                or int(byte_counts[key]) < 0
                for key in ("before", "after", "total")
            )
            or byte_counts["total"] != byte_counts["before"] + byte_counts["after"]
        ):
            raise VerificationError(
                "STORE_CORRUPT", "attempt executable byte/duration accounting is malformed"
            )
        status = attempt["status"]
        if status in {"NOT_RUN", "ATTEMPT_RECORD_INCOMPLETE"}:
            process_started = result.get("processStarted")
            if process_started is not False and process_started is not None:
                raise VerificationError(
                    "STORE_CORRUPT", "unexecuted attempt has invalid processStarted"
                )
            if byte_counts != {"before": 0, "after": 0, "total": 0}:
                raise VerificationError(
                    "STORE_CORRUPT", "unexecuted attempt claims executable hashing"
                )
            return
        if status == "IDENTITY_DRIFT" and result.get("processStarted") is False:
            if (
                result.get("executableIdentityBefore") is not None
                or result.get("executableIdentityAfter") is not None
                or byte_counts != {"before": 0, "after": 0, "total": 0}
            ):
                raise VerificationError(
                    "STORE_CORRUPT", "pre-source-drift attempt unexpectedly observed executable"
                )
            return
        if status == "EXECUTABLE_IDENTITY_DRIFT":
            phase = result.get("executableIdentityPhase")
            error = result.get("executableIdentityError")
            if (
                phase not in {"PRE", "POST"}
                or not isinstance(error, Mapping)
                or set(error) != {"code", "bytesHashed"}
                or not isinstance(error.get("code"), str)
                or isinstance(error.get("bytesHashed"), bool)
                or not isinstance(error.get("bytesHashed"), int)
                or int(error["bytesHashed"]) < 0
                or (phase == "PRE" and result.get("processStarted") is not False)
                or (phase == "POST" and not isinstance(result.get("processStarted"), bool))
            ):
                raise VerificationError(
                    "STORE_CORRUPT", "executable drift attempt shape is malformed"
                )
            observed = result.get("observedExecutableIdentity")
            observed_identity = None
            if observed is not None:
                try:
                    observed_identity = executable_identity.validate_executable_identity(
                        observed, expected_canonical_path=step.get("executable")
                    )
                except executable_identity.ExecutableIdentityError as exc:
                    raise VerificationError("STORE_CORRUPT", exc.message) from exc
            before_raw = result.get("executableIdentityBefore")
            after_raw = result.get("executableIdentityAfter")
            if phase == "PRE":
                before_identity = observed_identity
                expected_before_bytes = (
                    before_identity["byteCount"]
                    if before_identity is not None
                    else error["bytesHashed"]
                )
                if (
                    before_raw != observed
                    or after_raw is not None
                    or byte_counts["before"] != expected_before_bytes
                    or byte_counts["after"] != 0
                    or before_identity == sealed_identity
                ):
                    raise VerificationError(
                        "STORE_CORRUPT", "PRE executable drift accounting differs"
                    )
            else:
                try:
                    before_identity = executable_identity.validate_executable_identity(
                        before_raw, expected_canonical_path=step.get("executable")
                    )
                except executable_identity.ExecutableIdentityError as exc:
                    raise VerificationError("STORE_CORRUPT", exc.message) from exc
                expected_after_bytes = (
                    observed_identity["byteCount"]
                    if observed_identity is not None
                    else error["bytesHashed"]
                )
                if (
                    before_identity != sealed_identity
                    or after_raw != observed
                    or byte_counts["before"] != sealed_identity["byteCount"]
                    or byte_counts["after"] != expected_after_bytes
                    or observed_identity == sealed_identity
                ):
                    raise VerificationError(
                        "STORE_CORRUPT", "POST executable drift accounting differs"
                    )
            return
        before_raw = result.get("executableIdentityBefore")
        after_raw = result.get("executableIdentityAfter")
        try:
            before = executable_identity.validate_executable_identity(
                before_raw, expected_canonical_path=step.get("executable")
            )
            after = executable_identity.validate_executable_identity(
                after_raw, expected_canonical_path=step.get("executable")
            )
        except executable_identity.ExecutableIdentityError as exc:
            raise VerificationError("STORE_CORRUPT", exc.message) from exc
        if (
            before != sealed_identity
            or after != sealed_identity
            or result.get("executableIdentityError") is not None
            or result.get("executableIdentityPhase") is not None
            or result.get("observedExecutableIdentity") != after_raw
            or not isinstance(result.get("processStarted"), bool)
            or byte_counts["before"] != before["byteCount"]
            or byte_counts["after"] != after["byteCount"]
        ):
            raise VerificationError(
                "STORE_CORRUPT", "attempt executable observations differ from sealed identity"
            )

    @staticmethod
    def _validate_attempt_artifact_binding(
        attempt: Mapping[str, Any], artifact_tokens: Mapping[str, bytes]
    ) -> None:
        artifact_ref = attempt.get("artifactRef")
        status = attempt.get("status")
        no_artifact_statuses = {"NOT_RUN", "ATTEMPT_RECORD_INCOMPLETE"}
        result = attempt.get("result")
        if not isinstance(result, Mapping):
            raise VerificationError("STORE_CORRUPT", "attempt result is not an object")
        if artifact_ref is None:
            if status in no_artifact_statuses:
                return
            if status in {"IDENTITY_DRIFT", "EXECUTABLE_IDENTITY_DRIFT"} and result.get(
                "processStarted"
            ) is False:
                return
            raise VerificationError(
                "STORE_CORRUPT", "started process attempt has no runner-owned artifact"
            )
        raw = artifact_tokens.get(str(artifact_ref))
        if raw is None:
            raise VerificationError("STORE_CORRUPT", "attempt artifact ref is absent")
        artifact = _decode_json(raw, "verification process artifact")
        if not isinstance(artifact, Mapping) or set(artifact) != {
            "protocolVersion",
            "canonicalRequestDigest",
            "stdout",
            "stderr",
        }:
            raise VerificationError("STORE_CORRUPT", "process artifact shape is malformed")
        stdout = artifact.get("stdout")
        stderr = artifact.get("stderr")
        if (
            artifact.get("protocolVersion") != "verification-process-artifact-v1"
            or artifact.get("canonicalRequestDigest")
            != attempt.get("canonicalRequestDigest")
            or not isinstance(stdout, Mapping)
            or not isinstance(stderr, Mapping)
            or set(stdout) != {"sha256", "byteCount", "truncated", "text"}
            or set(stderr) != {"sha256", "byteCount", "truncated", "text"}
            or result.get("stdout") != _artifact_projection(stdout)
            or result.get("stderr") != _artifact_projection(stderr)
        ):
            raise VerificationError(
                "STORE_CORRUPT", "attempt result and process artifact digests differ"
            )

    def _evidence_state(
        self,
        *,
        plan: Mapping[str, Any],
        executions: Mapping[tuple[str, str], str],
        attempts: Sequence[Mapping[str, Any]],
        expected_source: str,
        artifact_tokens: Mapping[str, bytes],
    ) -> tuple[
        dict[str, bool],
        dict[str, bool],
        dict[str, str],
        bool,
        bool,
        dict[str, bool],
    ]:
        review_complete: dict[str, bool] = {}
        for review in plan["sourceReviews"]:
            review_complete[review["sourceReviewId"]] = all(
                self._anchor_is_current(anchor) for anchor in review["basisAnchors"]
            )
        by_step: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
        for attempt in attempts:
            by_step.setdefault((attempt["flowId"], attempt["stepId"]), []).append(attempt)
        flow_complete: dict[str, bool] = {}
        flow_uncertainty: dict[str, bool] = {}
        correlation: dict[str, str] = {}
        drift = False
        executable_drift = False
        for flow in plan["flows"]:
            complete = all(self._anchor_is_current(anchor) for anchor in flow["basisAnchors"])
            for step in flow["steps"]:
                key = (flow["flowId"], step["stepId"])
                step_attempts = by_step.get(key, [])
                if executions.get(key) != "COMPLETED" or not step_attempts:
                    complete = False
                expected_polls = step["pollPolicy"]["maxAttempts"] if step["role"] == "READBACK" else 1
                if len(step_attempts) > expected_polls:
                    raise VerificationError("STORE_CORRUPT", "attempt cardinality exceeds sealed plan")
                for attempt in step_attempts:
                    if attempt["canonicalRequestDigest"] != step["canonicalRequestDigest"]:
                        raise VerificationError("SEALED_REQUEST_MISMATCH", "attempt request differs from sealed request")
                    if attempt["status"] in {
                        "NOT_RUN",
                        "ATTEMPT_RECORD_INCOMPLETE",
                    }:
                        complete = False
                    if attempt["status"] == "EXECUTABLE_IDENTITY_DRIFT":
                        executable_drift = True
                    self._validate_attempt_executable_binding(attempt, step)
                    self._validate_attempt_artifact_binding(attempt, artifact_tokens)
                    if (
                        attempt["sourceIdentityBefore"] != expected_source
                        or attempt["sourceIdentityAfter"] != expected_source
                    ):
                        drift = True
                        complete = False
            for binding in flow["correlationBindings"]:
                action_attempts = by_step.get((flow["flowId"], binding["actionStepId"]), [])
                readback_attempts = by_step.get((flow["flowId"], binding["readbackStepId"]), [])
                token = binding["token"].encode("utf-8")
                action_match = any(
                    attempt["status"] != "EXECUTABLE_IDENTITY_DRIFT"
                    and attempt["status"] != "IDENTITY_DRIFT"
                    and
                    attempt.get("artifactRef") in artifact_tokens
                    and token in artifact_tokens[attempt["artifactRef"]]
                    for attempt in action_attempts
                )
                readback_match = any(
                    attempt["status"] != "EXECUTABLE_IDENTITY_DRIFT"
                    and attempt["status"] != "IDENTITY_DRIFT"
                    and
                    attempt.get("artifactRef") in artifact_tokens
                    and token in artifact_tokens[attempt["artifactRef"]]
                    for attempt in readback_attempts
                )
                state = "MATCH" if action_match and readback_match else "UNAVAILABLE"
                correlation[binding["bindingId"]] = state
                if state != "MATCH":
                    complete = False
            flow_complete[flow["flowId"]] = complete
            unresolved = False
            for step_index, step in enumerate(flow["steps"]):
                step_attempts = by_step.get((flow["flowId"], step["stepId"]), [])
                if not any(
                    attempt["status"] in PROCESS_OBSERVATION_UNCERTAINTY_STATUSES
                    for attempt in step_attempts
                ):
                    continue
                if step["role"] == "READBACK":
                    if not self._has_exact_process_observation(
                        step_attempts,
                        expected_source=expected_source,
                        artifact_tokens=artifact_tokens,
                    ):
                        unresolved = True
                elif step["role"] == "CLEANUP":
                    unresolved = True
                else:
                    later_readbacks = [
                        later
                        for later in flow["steps"][step_index + 1 :]
                        if later["role"] == "READBACK"
                    ]
                    resolved_by_readback = any(
                        self._has_exact_process_observation(
                            by_step.get((flow["flowId"], readback["stepId"]), []),
                            expected_source=expected_source,
                            artifact_tokens=artifact_tokens,
                        )
                        for readback in later_readbacks
                    )
                    action_binding_ids = [
                        binding["bindingId"]
                        for binding in flow["correlationBindings"]
                        if binding["actionStepId"] == step["stepId"]
                    ]
                    bindings_match = all(
                        correlation.get(binding_id) == "MATCH"
                        for binding_id in action_binding_ids
                    )
                    if not resolved_by_readback or not bindings_match:
                        unresolved = True
            flow_uncertainty[flow["flowId"]] = unresolved
        return (
            review_complete,
            flow_complete,
            correlation,
            drift,
            executable_drift,
            flow_uncertainty,
        )

    @staticmethod
    def _has_exact_process_observation(
        attempts: Sequence[Mapping[str, Any]],
        *,
        expected_source: str,
        artifact_tokens: Mapping[str, bytes],
    ) -> bool:
        for attempt in attempts:
            if (
                attempt["status"] != "EXITED"
                or attempt["sourceIdentityBefore"] != expected_source
                or attempt["sourceIdentityAfter"] != expected_source
                or attempt.get("artifactRef") not in artifact_tokens
            ):
                continue
            result = attempt.get("result")
            if not isinstance(result, Mapping) or result.get("processStarted") is not True:
                continue
            if result.get("executableIdentityError") is not None:
                continue
            try:
                expected = executable_identity.validate_executable_identity(
                    result.get("expectedExecutableIdentity")
                )
                before = executable_identity.validate_executable_identity(
                    result.get("executableIdentityBefore")
                )
                after = executable_identity.validate_executable_identity(
                    result.get("executableIdentityAfter")
                )
            except executable_identity.ExecutableIdentityError:
                continue
            if expected == before == after:
                return True
        return False

    def _finalize_ledger(
        self,
        *,
        run_ref: str,
        plan: Mapping[str, Any],
        assessments: Sequence[Mapping[str, Any]],
    ) -> None:
        _require_current_process_plan(plan)
        contradiction = any(item["verdict"] == "CONTRADICTED" for item in assessments)
        reason = "NOT_RUN_PRIOR_CONTRADICTION" if contradiction else "NOT_RUN_UNEXECUTED"
        assessment_digest = _digest(list(assessments))
        created_at = _now()
        with contextlib.ExitStack() as live_execution_locks, self.workflow._transaction() as connection:
            existing = connection.execute(
                """
                SELECT payload_json FROM verification_events
                WHERE run_ref = ? AND event_kind = 'LEDGER_COMPLETED'
                ORDER BY event_id LIMIT 1
                """,
                (run_ref,),
            ).fetchone()
            if existing is not None:
                existing_payload = _decode_json(existing["payload_json"], "ledger closure event")
                if existing_payload.get("assessmentDigest") != assessment_digest:
                    raise VerificationError(
                        "RESULT_RETRY_MISMATCH",
                        "result retry changed criterion assessments after ledger closure",
                    )
                return
            for flow in plan["flows"]:
                for step in flow["steps"]:
                    execution = connection.execute(
                        "SELECT * FROM verification_step_executions WHERE run_ref = ? AND flow_id = ? AND step_id = ?",
                        (run_ref, flow["flowId"], step["stepId"]),
                    ).fetchone()
                    status = None
                    if execution is None:
                        connection.execute(
                            """
                            INSERT INTO verification_step_executions(
                                run_ref, flow_id, step_id, state, request_sha256, started_at, completed_at
                            ) VALUES (?, ?, ?, 'NOT_RUN', ?, ?, ?)
                            """,
                            (
                                run_ref,
                                flow["flowId"],
                                step["stepId"],
                                step["canonicalRequestDigest"],
                                created_at,
                                created_at,
                            ),
                        )
                        status = "NOT_RUN"
                    elif execution["state"] == "STARTED":
                        lock_fd = self._acquire_step_execution_lock(
                            run_ref=run_ref,
                            flow_id=flow["flowId"],
                            step_id=step["stepId"],
                        )
                        live_execution_locks.callback(os.close, lock_fd)
                        completed = connection.execute(
                            """
                            UPDATE verification_step_executions
                            SET state = 'COMPLETED', completed_at = ?
                            WHERE run_ref = ? AND flow_id = ? AND step_id = ? AND state = 'STARTED'
                            """,
                            (created_at, run_ref, flow["flowId"], step["stepId"]),
                        )
                        if completed.rowcount != 1:
                            raise VerificationError(
                                "STORE_CORRUPT",
                                "started step changed during crash-gap recovery",
                            )
                        status = "ATTEMPT_RECORD_INCOMPLETE"
                    if status is not None:
                        result = {
                            "reason": reason if status == "NOT_RUN" else "RUNNER_INTERRUPTED_AFTER_STEP_START",
                            "executor": step["executorKind"],
                            "executorVersion": step["executorVersion"],
                            "environmentPolicy": step["environmentPolicy"],
                            "processStarted": False if status == "NOT_RUN" else None,
                            "expectedExecutableIdentity": step["executableIdentity"],
                            "observedExecutableIdentity": None,
                            "executableIdentityBefore": None,
                            "executableIdentityAfter": None,
                            "executableIdentityPhase": None,
                            "executableIdentityError": None,
                            "executableBytesHashed": {
                                "before": 0,
                                "after": 0,
                                "total": 0,
                            },
                            "durationMs": 0,
                        }
                        encoded_result = _canonical_json(result)
                        cursor = connection.execute(
                            """
                            INSERT INTO verification_attempts(
                                run_ref, flow_id, step_id, step_role, poll_index, status,
                                request_sha256, source_identity_before, source_identity_after,
                                artifact_ref, result_json, created_at
                            ) VALUES (?, ?, ?, ?, 0, ?, ?, NULL, NULL, NULL, ?, ?)
                            """,
                            (
                                run_ref,
                                flow["flowId"],
                                step["stepId"],
                                step["role"],
                                status,
                                step["canonicalRequestDigest"],
                                encoded_result,
                                created_at,
                            ),
                        )
                        self._event_locked(
                            connection,
                            run_ref,
                            "ATTEMPT_APPENDED",
                            {
                                "attemptId": int(cursor.lastrowid),
                                "flowId": flow["flowId"],
                                "stepId": step["stepId"],
                                "pollIndex": 0,
                                "status": status,
                                "artifactRef": None,
                                "canonicalRequestDigest": step[
                                    "canonicalRequestDigest"
                                ],
                                "resultDigest": hashlib.sha256(
                                    encoded_result
                                ).hexdigest(),
                            },
                        )
            self._event_locked(
                connection,
                run_ref,
                "LEDGER_COMPLETED",
                {
                    "completedAt": created_at,
                    "defaultNotRunReason": reason,
                    "assessmentDigest": assessment_digest,
                },
            )

    @staticmethod
    def _aggregate(
        assessments: Sequence[Mapping[str, Any]],
        *,
        system_incomplete: bool,
        system_blocked: bool,
    ) -> str:
        if any(item["verdict"] == "CONTRADICTED" for item in assessments):
            return "VERIFICATION_FAILED"
        if system_blocked or any(item["verdict"] == "BLOCKED" for item in assessments):
            return "BLOCKED"
        if system_incomplete or any(item["verdict"] == "INCONCLUSIVE" for item in assessments):
            return "INCOMPLETE"
        return "VERIFIED"

    def _publish_sealed_result_atomic(
        self,
        *,
        assessor_capability: str,
        verification_run_ref: str,
        criterion_assessments: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Re-read every terminal fact and publish on one owner transaction."""
        try:
            with self.workflow._transaction() as connection:
                assessor, run, claim = self._run_for_actor_locked(
                    connection, assessor_capability, verification_run_ref
                )
                if (
                    run["state"] != "SEALED"
                    or claim["state"] != "ACTIVE"
                    or claim["transition_kind"] != "VERIFY"
                    or claim["execution_ref"] != verification_run_ref
                    or run["claim_ref"] != claim["claim_ref"]
                    or run["root_ref"] != claim["root_ref"]
                    or run["assessor_actor_ref"] != assessor["actor_ref"]
                    or run["planning_identity"] != claim["planning_identity"]
                    or run["source_identity"] != claim["source_identity"]
                ):
                    raise VerificationError(
                        "VERIFICATION_RUN_NOT_PUBLISHABLE",
                        "sealed run, claim, and Assessor identity differ",
                    )
                tip = self.workflow._current_tip_locked(connection, claim["root_ref"])
                if (
                    tip["node_ref"] != claim["tip_ref"]
                    or tip["planning_identity"] != run["planning_identity"]
                    or tip["source_identity"] != run["source_identity"]
                ):
                    raise VerificationError(
                        "STALE_WORKFLOW_TIP", "sealed run no longer owns its exact workflow tip"
                    )
                plan = self._load_plan(run)
                _require_current_process_plan(plan)
                assessments = self._normalize_assessments(
                    list(criterion_assessments), plan["criteria"]
                )
                ledger_events = connection.execute(
                    """
                    SELECT payload_json, payload_sha256
                    FROM verification_events
                    WHERE run_ref = ? AND event_kind = 'LEDGER_COMPLETED'
                    ORDER BY event_id
                    """,
                    (verification_run_ref,),
                ).fetchall()
                if len(ledger_events) != 1:
                    raise VerificationError(
                        "STORE_CORRUPT", "sealed publication requires exactly one ledger closure"
                    )
                ledger_bytes = bytes(ledger_events[0]["payload_json"])
                if hashlib.sha256(ledger_bytes).hexdigest() != ledger_events[0]["payload_sha256"]:
                    raise VerificationError("STORE_CORRUPT", "ledger closure digest differs")
                ledger = _decode_json(ledger_bytes, "ledger closure event")
                if ledger.get("assessmentDigest") != _digest(assessments):
                    raise VerificationError(
                        "RESULT_RETRY_MISMATCH",
                        "result retry changed criterion assessments after ledger closure",
                    )

                execution_rows = connection.execute(
                    "SELECT * FROM verification_step_executions WHERE run_ref = ?",
                    (verification_run_ref,),
                ).fetchall()
                attempt_rows = connection.execute(
                    "SELECT * FROM verification_attempts WHERE run_ref = ? ORDER BY attempt_id",
                    (verification_run_ref,),
                ).fetchall()
                self._validate_attempt_event_ledger_locked(
                    connection, verification_run_ref, attempt_rows
                )
                artifact_rows = connection.execute(
                    "SELECT artifact_ref, payload, payload_sha256 FROM verification_artifacts WHERE run_ref = ?",
                    (verification_run_ref,),
                ).fetchall()
                contradiction_rows = connection.execute(
                    """
                    SELECT payload_json, payload_sha256 FROM verification_events
                    WHERE run_ref = ? AND event_kind = 'CONTRADICTION_DECLARED'
                    ORDER BY event_id
                    """,
                    (verification_run_ref,),
                ).fetchall()

                expected_steps = {
                    (flow["flowId"], step["stepId"]): step
                    for flow in plan["flows"]
                    for step in flow["steps"]
                }
                executions: dict[tuple[str, str], str] = {}
                for row in execution_rows:
                    key = (row["flow_id"], row["step_id"])
                    step = expected_steps.get(key)
                    if (
                        step is None
                        or key in executions
                        or row["state"] not in {"COMPLETED", "NOT_RUN"}
                        or row["request_sha256"] != step["canonicalRequestDigest"]
                    ):
                        raise VerificationError(
                            "STORE_CORRUPT", "terminal execution ledger differs from sealed plan"
                        )
                    executions[key] = row["state"]
                if set(executions) != set(expected_steps):
                    raise VerificationError(
                        "STORE_CORRUPT", "terminal execution ledger is incomplete"
                    )
                attempts = [self._attempt_view(row) for row in attempt_rows]
                attempts_by_step: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
                for attempt in attempts:
                    key = (attempt["flowId"], attempt["stepId"])
                    step = expected_steps.get(key)
                    if step is None or attempt["canonicalRequestDigest"] != step["canonicalRequestDigest"]:
                        raise VerificationError(
                            "STORE_CORRUPT", "attempt ledger differs from sealed plan"
                        )
                    attempts_by_step.setdefault(key, []).append(attempt)
                if any(key not in attempts_by_step for key in expected_steps):
                    raise VerificationError("STORE_CORRUPT", "terminal attempt ledger is incomplete")

                artifact_tokens: dict[str, bytes] = {}
                for row in artifact_rows:
                    artifact_bytes = bytes(row["payload"])
                    if hashlib.sha256(artifact_bytes).hexdigest() != row["payload_sha256"]:
                        raise VerificationError("STORE_CORRUPT", "verification artifact digest differs")
                    artifact_tokens[row["artifact_ref"]] = artifact_bytes
                review_complete, flow_complete, correlation, drift, executable_drift, flow_uncertainty = (
                    self._evidence_state(
                        plan=plan,
                        executions=executions,
                        attempts=attempts,
                        expected_source=run["source_identity"],
                        artifact_tokens=artifact_tokens,
                    )
                )
                for flow in plan["flows"]:
                    action_started = any(
                        executions.get((flow["flowId"], step["stepId"])) == "COMPLETED"
                        for step in flow["steps"]
                        if step["role"] == "ACTION"
                    )
                    missing_cleanup = any(
                        executions.get((flow["flowId"], step["stepId"])) != "COMPLETED"
                        for step in flow["steps"]
                        if step["role"] == "CLEANUP"
                    )
                    if action_started and missing_cleanup:
                        raise VerificationError(
                            "REQUIRED_CLEANUP_NOT_EXECUTED",
                            "a flow with a started ACTION must attempt every presealed CLEANUP before closure",
                        )

                criterion_complete: dict[int, bool] = {}
                for criterion in plan["criteria"]:
                    complete = all(
                        review_complete.get(key, False)
                        for key in criterion["sourceReviewIds"]
                    )
                    complete = complete and all(
                        flow_complete.get(key, False) for key in criterion["flowIds"]
                    )
                    criterion_complete[criterion["criterionIndex"]] = complete
                declared_contradictions: set[tuple[Any, Any]] = set()
                for row in contradiction_rows:
                    encoded = bytes(row["payload_json"])
                    if hashlib.sha256(encoded).hexdigest() != row["payload_sha256"]:
                        raise VerificationError(
                            "STORE_CORRUPT", "contradiction event digest differs"
                        )
                    event_payload = _decode_json(encoded, "contradiction event")
                    declared_contradictions.add(
                        (
                            event_payload.get("criterionIndex"),
                            event_payload.get("criterionRawSha256"),
                        )
                    )
                assessment_evidence_incomplete = any(
                    assessment["verdict"] in {"SATISFIED", "CONTRADICTED"}
                    and not criterion_complete[assessment["criterionIndex"]]
                    and (
                        assessment["criterionIndex"],
                        assessment["criterionRawSha256"],
                    )
                    not in declared_contradictions
                    for assessment in assessments
                )

                missing_or_ambiguous = any(
                    attempt["status"] in {"NOT_RUN", "ATTEMPT_RECORD_INCOMPLETE"}
                    for attempt in attempts
                )
                unresolved_process_uncertainty = any(flow_uncertainty.values())
                correlation_incomplete = any(value != "MATCH" for value in correlation.values())
                retain_missing = False
                retain_inconclusive = False
                for flow in plan["flows"]:
                    if flow["productTargetRequirement"] != "RETAIN":
                        continue
                    if not flow["steps"] or flow["steps"][-1]["role"] != "READBACK":
                        retain_missing = True
                        continue
                    last_key = (flow["flowId"], flow["steps"][-1]["stepId"])
                    if executions.get(last_key) != "COMPLETED":
                        retain_missing = True
                    elif not self._has_exact_process_observation(
                        attempts_by_step.get(last_key, []),
                        expected_source=run["source_identity"],
                        artifact_tokens=artifact_tokens,
                    ):
                        retain_inconclusive = True
                    last_cleanup = max(
                        (
                            index
                            for index, step in enumerate(flow["steps"])
                            if step["role"] == "CLEANUP"
                        ),
                        default=-1,
                    )
                    if last_cleanup >= len(flow["steps"]) - 1:
                        retain_missing = True
                retain_violation = retain_missing or retain_inconclusive

                project_root = Path(run["project_root"])
                current_source, source_error = self._capture_identity_for_attempt(project_root)
                publication_drift = source_error is not None or current_source != run["source_identity"]
                planning_blocked = False
                handoff_row = connection.execute(
                    "SELECT * FROM nodes WHERE node_ref = ? AND node_kind = 'IMPLEMENTATION_HANDOFF'",
                    (run["implementation_handoff_ref"],),
                ).fetchone()
                if handoff_row is None:
                    planning_blocked = True
                    stored_handoff: Mapping[str, Any] | None = None
                else:
                    try:
                        stored_handoff = self.workflow._node_view(handoff_row)["payload"]
                        self._verify_planning(stored_handoff)
                    except (_PreflightTerminal, workflow_store.WorkflowStoreError):
                        planning_blocked = True
                        stored_handoff = None
                status = (
                    "VERIFICATION_FAILED"
                    if declared_contradictions
                    else self._aggregate(
                        assessments,
                        system_incomplete=(
                            assessment_evidence_incomplete
                            or missing_or_ambiguous
                            or unresolved_process_uncertainty
                            or drift
                            or executable_drift
                            or publication_drift
                            or correlation_incomplete
                            or retain_violation
                        ),
                        system_blocked=planning_blocked,
                    )
                )
                if status == "VERIFIED" and retain_violation:
                    raise VerificationError(
                        "RETAIN_TERMINAL_READBACK_REQUIRED",
                        "RETAIN flow lacks executed terminal READBACK",
                    )

                reason_codes: list[str] = []
                if status == "VERIFICATION_FAILED":
                    reason_codes.append("CRITERION_CONTRADICTED")
                if planning_blocked:
                    reason_codes.append("PLANNING_AUTHORITY_UNAVAILABLE_AT_PUBLICATION")
                if drift or publication_drift:
                    reason_codes.append("SOURCE_IDENTITY_DRIFT")
                if executable_drift:
                    reason_codes.append("EXECUTABLE_IDENTITY_DRIFT")
                if missing_or_ambiguous:
                    reason_codes.append("INCOMPLETE_ATTEMPT_LEDGER")
                if unresolved_process_uncertainty and status != "VERIFIED":
                    reason_codes.append("PROCESS_OBSERVATION_INCONCLUSIVE")
                if correlation_incomplete:
                    reason_codes.append("CORRELATION_UNAVAILABLE")
                if retain_missing:
                    reason_codes.append("RETAIN_TERMINAL_READBACK_MISSING")
                if retain_inconclusive:
                    reason_codes.append("RETAIN_TERMINAL_READBACK_INCONCLUSIVE")
                if any(item["verdict"] == "BLOCKED" for item in assessments):
                    reason_codes.append("CRITERION_BLOCKED")
                if any(item["verdict"] == "INCONCLUSIVE" for item in assessments):
                    reason_codes.append("CRITERION_INCONCLUSIVE")
                reason_codes = list(dict.fromkeys(reason_codes))
                if status != "VERIFIED" and not reason_codes:
                    reason_codes.append("VERIFICATION_NOT_COMPLETE")

                # VERIFIED alone is rechecked immediately before the immutable insert.
                # Failure/incomplete/blocked remain publishable after live drift.
                if status == "VERIFIED":
                    try:
                        observed = baseline_capsule.capture_identity(project_root)["sourceIdentity"]
                    except baseline_capsule.CapsuleError as exc:
                        raise VerificationError(exc.code, exc.message) from exc
                    if observed != run["source_identity"]:
                        raise VerificationError(
                            "SOURCE_IDENTITY_DRIFT", "source changed during VERIFIED publication"
                        )
                    if stored_handoff is None:
                        raise VerificationError(
                            "PLANNING_AUTHORITY_UNAVAILABLE_AT_PUBLICATION",
                            "planning authority is unavailable during VERIFIED publication",
                        )
                    try:
                        self._verify_planning(stored_handoff)
                    except _PreflightTerminal as exc:
                        raise VerificationError(exc.reason_code, exc.message) from exc

                self.workflow._ensure_claim_closure_budget_locked(
                    connection,
                    claimant_capability=assessor_capability,
                    claim_ref=claim["claim_ref"],
                    amounts=_budget_vector(closureOperations=1),
                )
                result_ref = workflow_store.allocate_ref("VERIFICATION_RESULT")
                completed_at = _now()
                payload = {
                    "protocolVersion": PROTOCOL_VERSION,
                    "verificationResultRef": result_ref,
                    "verificationStatus": status,
                    "implementationHandoffRef": run["implementation_handoff_ref"],
                    "planningSealDigest": run["planning_identity"],
                    "finalSourceIdentity": run["source_identity"],
                    "verificationRunRef": verification_run_ref,
                    "sealedPlanDigest": run["sealed_plan_sha256"],
                    "criterionResults": assessments,
                    "reasonCodes": reason_codes,
                    "completedAt": completed_at,
                }
                node = self.workflow._close_successor_locked(
                    connection,
                    claimant_capability=assessor_capability,
                    claim_ref=claim["claim_ref"],
                    node_ref=result_ref,
                    node_kind="VERIFICATION_RESULT",
                    protocol_version=PROTOCOL_VERSION,
                    planning_identity=run["planning_identity"],
                    source_identity=run["source_identity"],
                    verification_status=status,
                    payload=payload,
                    verification_run_ref=verification_run_ref,
                    created_at=completed_at,
                )
        except VerificationError:
            raise
        except workflow_store.WorkflowStoreError as exc:
            raise VerificationError(exc.code, exc.message) from exc
        except sqlite3.IntegrityError as exc:
            raise VerificationError(
                "ATOMIC_PUBLICATION_CONFLICT", "VerificationResult publication conflicted"
            ) from exc
        if node["payload"] != payload:
            raise VerificationError("PUBLICATION_FAILED", "stored VerificationResult readback differs")
        return payload

    def publish_result(
        self,
        *,
        assessor_capability: str,
        verification_run_ref: str,
        criterion_assessments: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        with self.workflow._transaction() as connection:
            _, run, claim = self._run_for_actor_locked(connection, assessor_capability, verification_run_ref)
            if run["state"] != "SEALED" or claim["state"] != "ACTIVE":
                raise VerificationError("VERIFICATION_RUN_NOT_PUBLISHABLE", "run or claim is not open")
            plan = self._load_plan(run)
            _require_current_process_plan(plan)
            assessments = self._normalize_assessments(criterion_assessments, plan["criteria"])
            execution_rows = connection.execute(
                "SELECT * FROM verification_step_executions WHERE run_ref = ?",
                (verification_run_ref,),
            ).fetchall()
            attempt_rows = connection.execute(
                "SELECT * FROM verification_attempts WHERE run_ref = ? ORDER BY attempt_id",
                (verification_run_ref,),
            ).fetchall()
            self._validate_attempt_event_ledger_locked(
                connection, verification_run_ref, attempt_rows
            )
            artifacts = connection.execute(
                "SELECT artifact_ref, payload, payload_sha256 FROM verification_artifacts WHERE run_ref = ?",
                (verification_run_ref,),
            ).fetchall()
            contradiction_events = connection.execute(
                """
                SELECT payload_json FROM verification_events
                WHERE run_ref = ? AND event_kind = 'CONTRADICTION_DECLARED'
                """,
                (verification_run_ref,),
            ).fetchall()
            ledger_events = connection.execute(
                """
                SELECT event_id FROM verification_events
                WHERE run_ref = ? AND event_kind = 'LEDGER_COMPLETED'
                ORDER BY event_id
                """,
                (verification_run_ref,),
            ).fetchall()
            if len(ledger_events) > 1:
                raise VerificationError(
                    "STORE_CORRUPT", "run has more than one ledger closure event"
                )

        if ledger_events:
            # The immutable assessment digest is the retry anchor. Evidence and
            # live currentness may have changed since the unpublished attempt, so
            # do not re-admit or rewrite the already-fixed semantic assessments.
            self._finalize_ledger(
                run_ref=verification_run_ref,
                plan=plan,
                assessments=assessments,
            )
            return self._publish_sealed_result_atomic(
                assessor_capability=assessor_capability,
                verification_run_ref=verification_run_ref,
                criterion_assessments=assessments,
            )

        executions = {(row["flow_id"], row["step_id"]): row["state"] for row in execution_rows}
        attempts = [self._attempt_view(row) for row in attempt_rows]
        artifact_tokens: dict[str, bytes] = {}
        for row in artifacts:
            artifact_bytes = bytes(row["payload"])
            if hashlib.sha256(artifact_bytes).hexdigest() != row["payload_sha256"]:
                raise VerificationError("STORE_CORRUPT", "verification artifact digest differs")
            artifact_tokens[row["artifact_ref"]] = artifact_bytes
        review_complete, flow_complete, correlation, drift, executable_drift, flow_uncertainty = self._evidence_state(
            plan=plan,
            executions=executions,
            attempts=attempts,
            expected_source=run["source_identity"],
            artifact_tokens=artifact_tokens,
        )
        for flow in plan["flows"]:
            action_started = any(
                executions.get((flow["flowId"], step["stepId"])) in {"STARTED", "COMPLETED"}
                for step in flow["steps"]
                if step["role"] == "ACTION"
            )
            missing_cleanup = any(
                executions.get((flow["flowId"], step["stepId"])) != "COMPLETED"
                for step in flow["steps"]
                if step["role"] == "CLEANUP"
            )
            if action_started and missing_cleanup:
                raise VerificationError(
                    "REQUIRED_CLEANUP_NOT_EXECUTED",
                    "a flow with a started ACTION must attempt every presealed CLEANUP before closure",
                )
        criterion_complete: dict[int, bool] = {}
        criterion_flow_ids: dict[int, set[str]] = {}
        for criterion in plan["criteria"]:
            complete = all(review_complete.get(key, False) for key in criterion["sourceReviewIds"])
            complete = complete and all(flow_complete.get(key, False) for key in criterion["flowIds"])
            criterion_complete[criterion["criterionIndex"]] = complete
            criterion_flow_ids[criterion["criterionIndex"]] = set(criterion["flowIds"])
        executable_drift_flows = {
            str(attempt["flowId"])
            for attempt in attempts
            if attempt["status"] == "EXECUTABLE_IDENTITY_DRIFT"
        }
        declared_contradictions = {
            (
                event_payload.get("criterionIndex"),
                event_payload.get("criterionRawSha256"),
            )
            for event_payload in (
                _decode_json(row["payload_json"], "contradiction event")
                for row in contradiction_events
            )
        }
        for assessment in assessments:
            identity = (assessment["criterionIndex"], assessment["criterionRawSha256"])
            if identity in declared_contradictions and assessment["verdict"] != "CONTRADICTED":
                raise VerificationError(
                    "DECLARED_CONTRADICTION_MISMATCH",
                    "a durable contradiction must remain CONTRADICTED in the immutable result",
                )
            conclusive_without_evidence = (
                assessment["verdict"] == "SATISFIED"
                and not criterion_complete[assessment["criterionIndex"]]
            ) or (
                assessment["verdict"] == "CONTRADICTED"
                and identity not in declared_contradictions
                and (
                    not criterion_complete[assessment["criterionIndex"]]
                    or bool(
                        criterion_flow_ids[assessment["criterionIndex"]]
                        & executable_drift_flows
                    )
                )
            )
            if conclusive_without_evidence:
                code = (
                    "FORGED_OUTCOME_WITHOUT_EXECUTION"
                    if assessment["verdict"] == "SATISFIED"
                    else "CONTRADICTION_WITHOUT_COMPLETE_EVIDENCE"
                )
                raise VerificationError(code, "conclusive verdict lacks every presealed obligation")

        self._finalize_ledger(
            run_ref=verification_run_ref,
            plan=plan,
            assessments=assessments,
        )
        return self._publish_sealed_result_atomic(
            assessor_capability=assessor_capability,
            verification_run_ref=verification_run_ref,
            criterion_assessments=assessments,
        )

    def read_run(self, verification_run_ref: str) -> dict[str, Any]:
        if not isinstance(verification_run_ref, str) or not RUN_REF_PATTERN.fullmatch(verification_run_ref):
            raise VerificationError("MALFORMED_RUN_REF", "verification run ref is malformed")
        connection = self.workflow._connect()
        try:
            run = connection.execute(
                "SELECT * FROM verification_runs WHERE run_ref = ?", (verification_run_ref,)
            ).fetchone()
            if run is None:
                raise VerificationError("VERIFICATION_RUN_NOT_FOUND", "verification run is absent")
            attempts = connection.execute(
                "SELECT * FROM verification_attempts WHERE run_ref = ? ORDER BY attempt_id",
                (verification_run_ref,),
            ).fetchall()
            executions = connection.execute(
                "SELECT * FROM verification_step_executions WHERE run_ref = ? ORDER BY started_at, flow_id, step_id",
                (verification_run_ref,),
            ).fetchall()
            events = connection.execute(
                "SELECT * FROM verification_events WHERE run_ref = ? ORDER BY event_id",
                (verification_run_ref,),
            ).fetchall()
            artifacts = connection.execute(
                "SELECT artifact_ref, media_type, payload_sha256, byte_count, created_at FROM verification_artifacts WHERE run_ref = ? ORDER BY created_at, artifact_ref",
                (verification_run_ref,),
            ).fetchall()
        finally:
            connection.close()
        plan = None if run["sealed_plan_json"] is None else self._public_plan(self._load_plan(run))
        return {
            "verificationRunRef": run["run_ref"],
            "implementationHandoffRef": run["implementation_handoff_ref"],
            "planningSealDigest": run["planning_identity"],
            "finalSourceIdentity": run["source_identity"],
            "preflight": _decode_json(run["preflight_json"], "verification preflight"),
            "sealedPlanDigest": run["sealed_plan_sha256"],
            "sealedPlan": plan,
            "state": run["state"],
            "stepExecutions": [
                {
                    "flowId": row["flow_id"],
                    "stepId": row["step_id"],
                    "state": row["state"],
                    "canonicalRequestDigest": row["request_sha256"],
                    "startedAt": row["started_at"],
                    "completedAt": row["completed_at"],
                }
                for row in executions
            ],
            "attempts": [self._attempt_view(row) for row in attempts],
            "artifacts": [dict(row) for row in artifacts],
            "events": [
                {
                    "eventId": row["event_id"],
                    "eventKind": row["event_kind"],
                    "payload": _decode_json(row["payload_json"], "verification event"),
                    "payloadSha256": row["payload_sha256"],
                    "createdAt": row["created_at"],
                }
                for row in events
            ],
            "closure": None if run["closure_json"] is None else _decode_json(run["closure_json"], "verification closure"),
            "createdAt": run["created_at"],
            "closedAt": run["closed_at"],
        }

    def read_artifact(self, *, assessor_capability: str, artifact_ref: str) -> dict[str, Any]:
        if not isinstance(artifact_ref, str) or not re.fullmatch(r"verification:artifact:v1:[a-f0-9]{32}", artifact_ref):
            raise VerificationError("MALFORMED_ARTIFACT_REF", "verification artifact ref is malformed")
        with self.workflow._transaction() as connection:
            assessor = self.workflow._actor_for_capability_locked(
                connection, assessor_capability, expected_role="ASSESSOR"
            )
            row = connection.execute(
                """
                SELECT artifact.*
                FROM verification_artifacts AS artifact
                JOIN verification_runs AS run ON run.run_ref = artifact.run_ref
                WHERE artifact.artifact_ref = ? AND run.assessor_actor_ref = ?
                """,
                (artifact_ref, assessor["actor_ref"]),
            ).fetchone()
            if row is None:
                raise VerificationError(
                    "ARTIFACT_NOT_FOUND",
                    "artifact is absent or not owned by this Assessor",
                )
            payload = bytes(row["payload"])
            if hashlib.sha256(payload).hexdigest() != row["payload_sha256"]:
                raise VerificationError("STORE_CORRUPT", "artifact digest differs")
            value = _decode_json(payload, "verification artifact")
        return {
            "artifactRef": artifact_ref,
            "mediaType": row["media_type"],
            "payloadSha256": row["payload_sha256"],
            "byteCount": row["byte_count"],
            "payload": value,
            "createdAt": row["created_at"],
        }


__all__ = [
    "PROTOCOL_VERSION",
    "VerificationError",
    "VerificationService",
    "basis_anchor",
]


def _read_json(path: Path, locator: str) -> Any:
    try:
        if path.stat().st_size > MAX_DRAFT_BYTES:
            raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"{locator} is oversized")
        return json.loads(path.read_text(encoding="utf-8"))
    except VerificationError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("MALFORMED_VERIFICATION_DRAFT", f"cannot read {locator}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow-root",
        default=os.environ.get("IMPLEMENTATION_WORKFLOW_STORE", str(workflow_store.DEFAULT_STORE_ROOT)),
    )
    parser.add_argument(
        "--workflow-guard-fd",
        type=int,
        help="caller-owned deployment lock fd (required for store-backed commands)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start-invocation")
    start.add_argument("--root-ref", required=True)
    start.add_argument("--elapsed-seconds", type=int, required=True)
    start.add_argument("--limits", type=Path, required=True)

    authorize = commands.add_parser("issue-authorization")
    authorize.add_argument("--coordinator-capability", required=True)
    authorize.add_argument("--scope-sha256", required=True)

    open_verify = commands.add_parser("open-verification")
    open_verify.add_argument("--coordinator-capability", required=True)
    open_verify.add_argument("--handoff-ref", required=True)
    open_verify.add_argument("--spend", type=Path, required=True)
    open_verify.add_argument("--closure", type=Path, required=True)

    seal = commands.add_parser("seal-run")
    seal.add_argument("--assessor-capability", required=True)
    seal.add_argument("--claim-ref", required=True)
    seal.add_argument("--handoff-ref", required=True)
    seal.add_argument("--draft", type=Path, required=True)

    execute = commands.add_parser("execute-step")
    execute.add_argument("--assessor-capability", required=True)
    execute.add_argument("--run-ref", required=True)
    execute.add_argument("--flow-id", required=True)
    execute.add_argument("--step-id", required=True)

    contradict = commands.add_parser("declare-contradiction")
    contradict.add_argument("--assessor-capability", required=True)
    contradict.add_argument("--run-ref", required=True)
    contradict.add_argument("--criterion-ref", type=Path, required=True)

    publish = commands.add_parser("publish-result")
    publish.add_argument("--assessor-capability", required=True)
    publish.add_argument("--run-ref", required=True)
    publish.add_argument("--assessments", type=Path, required=True)

    read = commands.add_parser("read-run")
    read.add_argument("--run-ref", required=True)

    read_artifact = commands.add_parser("read-artifact")
    read_artifact.add_argument("--assessor-capability", required=True)
    read_artifact.add_argument("--artifact-ref", required=True)

    preview = commands.add_parser("preview-process-step")
    preview.add_argument("--step", type=Path, required=True)
    preview.add_argument("--project-root", required=True)
    preview.add_argument("--source-identity", required=True)

    replay_scope = commands.add_parser("replay-authorization-scope")
    replay_scope.add_argument(
        "--mechanism", choices=["EXACT_IDEMPOTENCY", "UNIQUE_CORRELATION"], required=True
    )
    replay_scope.add_argument("--prior-run-ref", required=True)
    replay_scope.add_argument("--prior-flow-id", required=True)
    replay_scope.add_argument("--prior-step-id", required=True)
    replay_scope.add_argument("--new-request-digest", required=True)
    replay_scope.add_argument("--target-binding-digest", required=True)

    open_remediation = commands.add_parser("open-remediation")
    open_remediation.add_argument("--coordinator-capability", required=True)
    open_remediation.add_argument("--failed-result-ref", required=True)
    open_remediation.add_argument("--spend", type=Path, required=True)
    open_remediation.add_argument("--closure", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "preview-process-step":
            result = VerificationService.preview_process_step(
                step=_mapping(_read_json(args.step, "step"), "step"),
                project_root=args.project_root,
                final_source_identity=args.source_identity,
            )
        elif args.command == "replay-authorization-scope":
            result = {
                "scopeSha256": VerificationService.replay_authorization_scope(
                    mechanism=args.mechanism,
                    prior_run_ref=args.prior_run_ref,
                    prior_flow_id=args.prior_flow_id,
                    prior_step_id=args.prior_step_id,
                    new_request_digest=args.new_request_digest,
                    target_binding_digest=args.target_binding_digest,
                )
            }
        else:
            if args.workflow_guard_fd is None:
                raise VerificationError(
                    "AUDIT_GUARD_REQUIRED",
                    "store-backed verification commands require --workflow-guard-fd",
                )
            try:
                guard = workflow_store.guard_session_from_locked_fd(
                    args.workflow_guard_fd,
                    store_root=args.workflow_root,
                )
            except workflow_store.WorkflowStoreError as exc:
                raise VerificationError(exc.code, exc.message) from exc
            service = VerificationService(args.workflow_root, guard=guard)
            if args.command == "start-invocation":
                result = service.workflow.start_invocation(
                    root_ref=args.root_ref,
                    elapsed_seconds=args.elapsed_seconds,
                    limits=_mapping(_read_json(args.limits, "limits"), "limits"),
                )
            elif args.command == "issue-authorization":
                result = service.workflow.issue_authorization(
                    coordinator_capability=args.coordinator_capability,
                    scope_sha256=args.scope_sha256,
                )
            elif args.command == "open-verification":
                result = service.open_verification(
                    coordinator_capability=args.coordinator_capability,
                    implementation_handoff_ref=args.handoff_ref,
                    spend_budget=_mapping(_read_json(args.spend, "spend"), "spend"),
                    closure_budget=_mapping(_read_json(args.closure, "closure"), "closure"),
                )
            elif args.command == "seal-run":
                result = service.seal_run(
                    assessor_capability=args.assessor_capability,
                    claim_ref=args.claim_ref,
                    implementation_handoff_ref=args.handoff_ref,
                    verification_draft=_mapping(_read_json(args.draft, "draft"), "draft"),
                )
            elif args.command == "execute-step":
                result = service.execute_step(
                    assessor_capability=args.assessor_capability,
                    verification_run_ref=args.run_ref,
                    flow_id=args.flow_id,
                    step_id=args.step_id,
                )
            elif args.command == "declare-contradiction":
                result = service.declare_contradiction(
                    assessor_capability=args.assessor_capability,
                    verification_run_ref=args.run_ref,
                    criterion_ref=_mapping(
                        _read_json(args.criterion_ref, "criterionRef"), "criterionRef"
                    ),
                )
            elif args.command == "publish-result":
                assessments = _read_json(args.assessments, "criterionAssessments")
                if not isinstance(assessments, list):
                    raise VerificationError(
                        "MALFORMED_CRITERION_ASSESSMENT",
                        "criterionAssessments must be an array",
                    )
                result = service.publish_result(
                    assessor_capability=args.assessor_capability,
                    verification_run_ref=args.run_ref,
                    criterion_assessments=assessments,
                )
            elif args.command == "read-run":
                result = service.read_run(args.run_ref)
            elif args.command == "read-artifact":
                result = service.read_artifact(
                    assessor_capability=args.assessor_capability,
                    artifact_ref=args.artifact_ref,
                )
            else:
                result = service.open_remediation(
                    coordinator_capability=args.coordinator_capability,
                    failed_verification_result_ref=args.failed_result_ref,
                    spend_budget=_mapping(_read_json(args.spend, "spend"), "spend"),
                    closure_budget=_mapping(_read_json(args.closure, "closure"), "closure"),
                )
    except VerificationError as exc:
        print(
            json.dumps({"error": {"code": exc.code, "message": exc.message}}, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    except workflow_store.WorkflowStoreError as exc:
        print(
            json.dumps({"error": {"code": exc.code, "message": exc.message}}, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
