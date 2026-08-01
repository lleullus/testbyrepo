#!/usr/bin/env python3
"""Publish an immutable ImplementationResult bound to current source and planning bytes."""

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
from typing import Any, Mapping


PROTOCOL_VERSION = "implementation-result-v2"
RESULT_REF_PATTERN = re.compile(r"^implementation:v2:[a-f0-9]{32}$")
CAPSULE_REF_PATTERN = re.compile(r"^capsule:v1:[a-f0-9]{32}$")
IDENTITY_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
DEFAULT_RESULT_ROOT = Path.home() / ".local/state/opencode/implementation-results"

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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise ResultError("PLANNING_INPUT_CHANGED", f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def _write_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    except FileExistsError as exc:
        raise ResultError("IMMUTABLE_RESULT_EXISTS", f"refusing to overwrite {path}") from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _mapping(value: Any, locator: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResultError("MALFORMED_RESULT", f"{locator} must be an object")
    return value


def _validate_planning_seal(value: Any) -> dict[str, Any]:
    seal = _mapping(value, "planningSeal")
    fields = {"ticketPath", "ticketSha256", "specPath", "specSha256", "blockerFiles"}
    if set(seal) != fields:
        raise ResultError("MALFORMED_RESULT", "planningSeal fields are invalid")
    normalized = dict(seal)
    for role, path_key, digest_key in (
        ("Ticket", "ticketPath", "ticketSha256"),
        ("Spec", "specPath", "specSha256"),
    ):
        path = Path(str(seal[path_key]))
        digest = str(seal[digest_key])
        if not path.is_absolute() or not SHA256_PATTERN.fullmatch(digest):
            raise ResultError("MALFORMED_RESULT", f"{role} planning seal is malformed")
        try:
            canonical = path.resolve(strict=True)
        except OSError as exc:
            raise ResultError("PLANNING_INPUT_CHANGED", f"cannot resolve {role}: {exc}") from exc
        if str(canonical) != str(path) or _sha256(canonical) != digest:
            raise ResultError("PLANNING_INPUT_CHANGED", f"{role} path or digest changed")
    blockers = seal["blockerFiles"]
    if not isinstance(blockers, list):
        raise ResultError("MALFORMED_RESULT", "planningSeal.blockerFiles must be an array")
    for index, raw_blocker in enumerate(blockers):
        blocker = _mapping(raw_blocker, f"blockerFiles[{index}]")
        if set(blocker) != {"path", "sha256", "status"}:
            raise ResultError("MALFORMED_RESULT", f"blockerFiles[{index}] fields are invalid")
        path = Path(str(blocker["path"]))
        digest = str(blocker["sha256"])
        if not path.is_absolute() or not SHA256_PATTERN.fullmatch(digest) or blocker["status"] not in {"resolved", "done"}:
            raise ResultError("MALFORMED_RESULT", f"blockerFiles[{index}] is malformed")
        try:
            canonical = path.resolve(strict=True)
        except OSError as exc:
            raise ResultError("PLANNING_INPUT_CHANGED", f"cannot resolve blocker {path}: {exc}") from exc
        if str(canonical) != str(path) or _sha256(canonical) != digest:
            raise ResultError("PLANNING_INPUT_CHANGED", f"blocker changed: {path}")
    return normalized


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

    def publish(self, request: Mapping[str, Any]) -> dict[str, Any]:
        fields = {
            "protocolVersion",
            "implementationStatus",
            "projectRoot",
            "planningSeal",
            "capsuleRef",
            "finalSourceIdentity",
        }
        if set(request) != fields:
            raise ResultError("MALFORMED_RESULT", "ImplementationResult request fields are invalid")
        if request["protocolVersion"] != PROTOCOL_VERSION:
            raise ResultError("UNKNOWN_PROTOCOL_VERSION", "protocolVersion is not implementation-result-v2")
        if request["implementationStatus"] != "IMPLEMENTATION_COMPLETE":
            raise ResultError("INVALID_IMPLEMENTATION_STATUS", "only IMPLEMENTATION_COMPLETE can be published")
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
        planning_seal = _validate_planning_seal(request["planningSeal"])
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
        finally:
            self.capsule_store.release_read(view["readLeaseId"])
        token = uuid.uuid4().hex
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "implementationResultRef": f"implementation:v2:{token}",
            "implementationStatus": "IMPLEMENTATION_COMPLETE",
            "projectRoot": str(project_root),
            "planningSeal": planning_seal,
            "capsuleRef": capsule_ref,
            "baselineSourceIdentity": view["baselineSourceIdentity"],
            "finalSourceIdentity": final_identity,
            "completedAt": datetime.now(timezone.utc).isoformat(),
        }
        _write_exclusive(self.result_root / f"{token}.json", result)
        return result


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
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
