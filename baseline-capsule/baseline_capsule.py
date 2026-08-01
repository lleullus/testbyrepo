#!/usr/bin/env python3
"""Immutable source baselines for identity-bound implementation completion."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping


FORMAT_VERSION = "baseline-capsule-v1"
PROJECTION_POLICY_ID = "source-evidence-v1"
DEFAULT_STORE_ROOT = Path.home() / ".local/state/opencode/baseline-capsules"
DEFAULT_RETENTION_SECONDS = 7 * 24 * 60 * 60
DEFAULT_MAX_FILE_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_LEASE_SECONDS = 24 * 60 * 60

CAPSULE_PATTERN = re.compile(r"^capsule:v1:([a-f0-9]{32})$")
LEASE_PATTERN = re.compile(r"^lease:v1:([a-f0-9]{32}):([a-f0-9]{32})$")
VCS_ROOTS = {".git", ".hg", ".svn"}
DEPENDENCY_ROOTS = {"node_modules", ".tox", ".nox"}
CACHE_ROOTS = {
    ".gocache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".turbo",
    ".parcel-cache",
    ".nyc_output",
}


class CapsuleError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise CapsuleError("CAPSULE_CORRUPT", f"{field} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CapsuleError("CAPSULE_CORRUPT", f"{field} is invalid") from exc
    if parsed.tzinfo is None:
        raise CapsuleError("CAPSULE_CORRUPT", f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _write_exclusive(path: Path, payload: bytes, mode: int = 0o400) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    except FileExistsError as exc:
        raise CapsuleError("CAPSULE_CORRUPT", f"refusing to overwrite {path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapsuleError("CAPSULE_CORRUPT", f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CapsuleError("CAPSULE_CORRUPT", f"expected an object in {path}")
    return value


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _remove_tree(path: Path) -> None:
    def repair_and_retry(function: Any, target: str, _error: object) -> None:
        os.chmod(target, 0o700)
        function(target)

    shutil.rmtree(path, onerror=repair_and_retry)


def _is_sequence(parts: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    if len(parts) < len(sequence):
        return False
    return any(parts[index : index + len(sequence)] == sequence for index in range(len(parts) - len(sequence) + 1))


def _excluded(relative: str, path: Path, *, is_directory: bool) -> bool:
    parts = tuple(Path(relative).parts)
    if any(part in VCS_ROOTS or part in DEPENDENCY_ROOTS or part in CACHE_ROOTS for part in parts):
        return True
    if _is_sequence(parts, (".cache", "go-build")) or _is_sequence(parts, (".next", "cache")):
        return True
    name = parts[-1]
    if name == ".eslintcache" or name.endswith(".tsbuildinfo"):
        return True
    if is_directory and (path / "pyvenv.cfg").is_file():
        return True
    return False


def _manifest_identity(entries: Mapping[str, Any]) -> str:
    value = {"projectionPolicyId": PROJECTION_POLICY_ID, "entries": entries}
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _scan(root: Path, *, max_file_bytes: int, max_total_bytes: int) -> tuple[dict[str, dict[str, Any]], int]:
    entries: dict[str, dict[str, Any]] = {}
    total_bytes = 0

    def visit(directory: Path, relative_directory: str = "") -> None:
        nonlocal total_bytes
        try:
            children = sorted(os.scandir(directory), key=lambda child: os.fsencode(child.name))
        except OSError as exc:
            raise CapsuleError("INVALID_PROJECT_ROOT", f"cannot scan {directory}: {exc}") from exc
        for child in children:
            relative = f"{relative_directory}/{child.name}" if relative_directory else child.name
            try:
                metadata = child.stat(follow_symlinks=False)
            except OSError as exc:
                raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", f"cannot stat {relative}: {exc}") from exc
            mode = metadata.st_mode
            path = Path(child.path)
            is_directory = stat.S_ISDIR(mode)
            if _excluded(relative, path, is_directory=is_directory):
                continue
            if stat.S_ISLNK(mode):
                try:
                    target = os.readlink(path)
                except OSError as exc:
                    raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", f"cannot read symlink {relative}: {exc}") from exc
                if os.path.isabs(target):
                    raise CapsuleError("SYMLINK_ESCAPE", f"absolute symlink is not retained: {relative}")
                resolved = (path.parent / target).resolve(strict=False)
                if resolved != root and not resolved.is_relative_to(root):
                    raise CapsuleError("SYMLINK_ESCAPE", f"symlink escapes project root: {relative}")
                entries[relative] = {
                    "kind": "symlink",
                    "mode": stat.S_IMODE(mode),
                    "target": target,
                }
                continue
            if is_directory:
                entries[relative] = {"kind": "directory", "mode": stat.S_IMODE(mode)}
                visit(path, relative)
                continue
            if not stat.S_ISREG(mode):
                raise CapsuleError("UNSUPPORTED_ENTRY", f"unsupported filesystem entry: {relative}")
            before = path.stat(follow_symlinks=False)
            if before.st_size > max_file_bytes:
                raise CapsuleError(
                    "FILE_QUOTA_EXCEEDED",
                    f"{relative} is {before.st_size} bytes; limit is {max_file_bytes}",
                )
            total_bytes += before.st_size
            if total_bytes > max_total_bytes:
                raise CapsuleError(
                    "CAPSULE_QUOTA_EXCEEDED",
                    f"projected payload is larger than {max_total_bytes} bytes",
                )
            digest = hashlib.sha256()
            try:
                with path.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        digest.update(chunk)
            except OSError as exc:
                raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", f"cannot hash {relative}: {exc}") from exc
            after = path.stat(follow_symlinks=False)
            stable_fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns")
            if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
                raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", f"source changed while hashing {relative}")
            entries[relative] = {
                "kind": "file",
                "mode": stat.S_IMODE(mode),
                "size": after.st_size,
                "sha256": digest.hexdigest(),
            }

    visit(root)
    return entries, total_bytes


def capture_identity(
    project_root: Path | str,
    *,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> dict[str, Any]:
    try:
        root = Path(project_root).resolve(strict=True)
    except OSError as exc:
        raise CapsuleError("INVALID_PROJECT_ROOT", f"cannot resolve project root: {exc}") from exc
    if not root.is_dir():
        raise CapsuleError("INVALID_PROJECT_ROOT", f"project root is not a directory: {root}")
    first, first_bytes = _scan(root, max_file_bytes=max_file_bytes, max_total_bytes=max_total_bytes)
    second, second_bytes = _scan(root, max_file_bytes=max_file_bytes, max_total_bytes=max_total_bytes)
    if first != second or first_bytes != second_bytes:
        raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", "source changed between stability passes")
    return {
        "formatVersion": FORMAT_VERSION,
        "projectionPolicyId": PROJECTION_POLICY_ID,
        "projectRoot": str(root),
        "sourceIdentity": _manifest_identity(second),
        "payloadBytes": second_bytes,
        "entries": second,
    }


def changed_paths(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    before_entries = before.get("entries")
    after_entries = after.get("entries")
    if not isinstance(before_entries, Mapping) or not isinstance(after_entries, Mapping):
        raise CapsuleError("CAPSULE_CORRUPT", "manifest entries are malformed")
    return sorted(
        path
        for path in set(before_entries) | set(after_entries)
        if before_entries.get(path) != after_entries.get(path)
        and not (
            (before_entries.get(path) or {}).get("kind") == "directory"
            or (after_entries.get(path) or {}).get("kind") == "directory"
        )
    )


class CapsuleStore:
    def __init__(
        self,
        store_root: Path | str = DEFAULT_STORE_ROOT,
        *,
        retention_seconds: int = DEFAULT_RETENTION_SECONDS,
        max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None:
        if min(retention_seconds, max_file_bytes, max_total_bytes, lease_seconds) <= 0:
            raise CapsuleError("CAPSULE_CORRUPT", "retention, quota, and lease values must be positive")
        self.store_root = Path(store_root).expanduser().resolve()
        self.retention_seconds = retention_seconds
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self.lease_seconds = lease_seconds
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.store_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.store_root, 0o700)
        for name in ("capsules", "staging", "leases", "locks"):
            path = self.store_root / name
            path.mkdir(mode=0o700, exist_ok=True)
            os.chmod(path, 0o700)

    def _assert_external_store(self, project_root: Path) -> None:
        if self.store_root == project_root or self.store_root.is_relative_to(project_root):
            raise CapsuleError("STORE_INSIDE_PROJECT", "capsule store must be outside the project root")
        if project_root.is_relative_to(self.store_root):
            raise CapsuleError("PROJECT_INSIDE_STORE", "project root must not be inside the capsule store")

    @staticmethod
    def _capsule_id(capsule_ref: str) -> str:
        match = CAPSULE_PATTERN.fullmatch(capsule_ref)
        if not match:
            raise CapsuleError("INVALID_CAPSULE_REF", f"malformed capsule ref: {capsule_ref}")
        return match.group(1)

    @staticmethod
    def _lease_parts(lease_id: str) -> tuple[str, str]:
        match = LEASE_PATTERN.fullmatch(lease_id)
        if not match:
            raise CapsuleError("INVALID_LEASE", f"malformed lease id: {lease_id}")
        return match.group(1), match.group(2)

    def _capsule_path(self, capsule_id: str) -> Path:
        path = self.store_root / "capsules" / capsule_id
        if not path.is_dir():
            raise CapsuleError("CAPSULE_NOT_FOUND", f"capsule does not exist: capsule:v1:{capsule_id}")
        return path

    @contextlib.contextmanager
    def _coordination_lock(self, capsule_id: str) -> Iterator[None]:
        lock_path = self.store_root / "locks" / f"{capsule_id}.lock"
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _copy_payload(self, source_root: Path, destination_root: Path, manifest: Mapping[str, Any]) -> None:
        destination_root.mkdir(mode=0o700)
        entries = manifest["entries"]
        directory_modes: list[tuple[Path, int]] = []
        for relative, entry in sorted(entries.items(), key=lambda item: (len(Path(item[0]).parts), item[0])):
            source = source_root / relative
            destination = destination_root / relative
            kind = entry["kind"]
            if kind == "directory":
                destination.mkdir(mode=0o700)
                directory_modes.append((destination, int(entry["mode"])))
                continue
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if kind == "symlink":
                os.symlink(str(entry["target"]), destination)
                continue
            try:
                descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, int(entry["mode"]))
                with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
                    shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
                    output_handle.flush()
                    os.fsync(output_handle.fileno())
                os.chmod(destination, int(entry["mode"]))
            except OSError as exc:
                raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", f"cannot retain {relative}: {exc}") from exc
        for directory, mode in reversed(directory_modes):
            os.chmod(directory, mode)

    def create(self, project_root: Path | str, *, now: datetime | None = None) -> dict[str, Any]:
        source_manifest = capture_identity(
            project_root,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
        )
        root = Path(str(source_manifest["projectRoot"]))
        self._assert_external_store(root)
        created = (now or _utc_now()).astimezone(timezone.utc)
        expires = created + timedelta(seconds=self.retention_seconds)
        capsule_id = uuid.uuid4().hex
        capsule_ref = f"capsule:v1:{capsule_id}"
        staging_path = self.store_root / "staging" / capsule_id
        final_path = self.store_root / "capsules" / capsule_id
        staging_path.mkdir(mode=0o700)
        try:
            sealed_root = staging_path / "root"
            self._copy_payload(root, sealed_root, source_manifest)
            source_after = capture_identity(
                root,
                max_file_bytes=self.max_file_bytes,
                max_total_bytes=self.max_total_bytes,
            )
            retained = capture_identity(
                sealed_root,
                max_file_bytes=self.max_file_bytes,
                max_total_bytes=self.max_total_bytes,
            )
            if source_manifest["entries"] != source_after["entries"]:
                raise CapsuleError("SOURCE_CHANGED_DURING_CAPTURE", "source changed while retaining payload")
            if source_manifest["entries"] != retained["entries"]:
                raise CapsuleError("CAPSULE_CORRUPT", "retained payload differs from source projection")
            manifest_value = {
                "formatVersion": FORMAT_VERSION,
                "projectionPolicyId": PROJECTION_POLICY_ID,
                "baselineSourceIdentity": source_manifest["sourceIdentity"],
                "payloadBytes": source_manifest["payloadBytes"],
                "entries": source_manifest["entries"],
            }
            manifest_payload = _json_bytes(manifest_value)
            descriptor_value = {
                "formatVersion": FORMAT_VERSION,
                "projectionPolicyId": PROJECTION_POLICY_ID,
                "capsuleRef": capsule_ref,
                "canonicalProjectRoot": str(root),
                "baselineSourceIdentity": source_manifest["sourceIdentity"],
                "createdAt": _timestamp(created),
                "expiresAt": _timestamp(expires),
                "retentionSeconds": self.retention_seconds,
                "maxFileBytes": self.max_file_bytes,
                "maxTotalBytes": self.max_total_bytes,
                "payloadBytes": source_manifest["payloadBytes"],
                "entryCount": len(source_manifest["entries"]),
                "manifestSha256": hashlib.sha256(manifest_payload).hexdigest(),
            }
            _write_exclusive(staging_path / "manifest.json", manifest_payload)
            _write_exclusive(staging_path / "descriptor.json", _json_bytes(descriptor_value))
            _fsync_directory(staging_path)
            os.rename(staging_path, final_path)
            _fsync_directory(final_path.parent)
        except BaseException:
            if staging_path.exists():
                _remove_tree(staging_path)
            raise
        return {
            "capsuleRef": capsule_ref,
            "formatVersion": FORMAT_VERSION,
            "projectionPolicyId": PROJECTION_POLICY_ID,
            "baselineSourceIdentity": source_manifest["sourceIdentity"],
            "createdAt": _timestamp(created),
            "expiresAt": _timestamp(expires),
        }

    def _validated_descriptor(self, capsule_path: Path, *, now: datetime | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        descriptor = _read_json(capsule_path / "descriptor.json")
        required = {
            "formatVersion",
            "projectionPolicyId",
            "capsuleRef",
            "canonicalProjectRoot",
            "baselineSourceIdentity",
            "createdAt",
            "expiresAt",
            "retentionSeconds",
            "maxFileBytes",
            "maxTotalBytes",
            "payloadBytes",
            "entryCount",
            "manifestSha256",
        }
        if set(descriptor) != required:
            raise CapsuleError("CAPSULE_CORRUPT", "capsule descriptor fields are invalid")
        if descriptor["formatVersion"] != FORMAT_VERSION or descriptor["projectionPolicyId"] != PROJECTION_POLICY_ID:
            raise CapsuleError("UNSUPPORTED_FORMAT", "capsule format or projection is unsupported")
        expires = _parse_timestamp(descriptor["expiresAt"], "expiresAt")
        if (now or _utc_now()).astimezone(timezone.utc) >= expires:
            raise CapsuleError("CAPSULE_EXPIRED", f"capsule expired at {descriptor['expiresAt']}")
        manifest_path = capsule_path / "manifest.json"
        try:
            manifest_payload = manifest_path.read_bytes()
        except OSError as exc:
            raise CapsuleError("CAPSULE_CORRUPT", f"cannot read capsule manifest: {exc}") from exc
        if hashlib.sha256(manifest_payload).hexdigest() != descriptor["manifestSha256"]:
            raise CapsuleError("CAPSULE_CORRUPT", "capsule manifest digest differs")
        try:
            manifest = json.loads(manifest_payload)
        except json.JSONDecodeError as exc:
            raise CapsuleError("CAPSULE_CORRUPT", "capsule manifest is malformed") from exc
        if not isinstance(manifest, dict) or manifest.get("entries") is None:
            raise CapsuleError("CAPSULE_CORRUPT", "capsule manifest shape is invalid")
        retained = capture_identity(
            capsule_path / "root",
            max_file_bytes=int(descriptor["maxFileBytes"]),
            max_total_bytes=int(descriptor["maxTotalBytes"]),
        )
        if (
            retained["sourceIdentity"] != descriptor["baselineSourceIdentity"]
            or retained["sourceIdentity"] != manifest.get("baselineSourceIdentity")
            or retained["entries"] != manifest.get("entries")
        ):
            raise CapsuleError("CAPSULE_CORRUPT", "retained payload identity differs")
        return descriptor, manifest

    def acquire_read(self, capsule_ref: str, *, now: datetime | None = None) -> dict[str, Any]:
        capsule_id = self._capsule_id(capsule_ref)
        observed = (now or _utc_now()).astimezone(timezone.utc)
        with self._coordination_lock(capsule_id):
            capsule_path = self._capsule_path(capsule_id)
            descriptor, _manifest = self._validated_descriptor(capsule_path, now=observed)
            lease_token = uuid.uuid4().hex
            lease_id = f"lease:v1:{capsule_id}:{lease_token}"
            lease_value = {
                "leaseId": lease_id,
                "capsuleRef": capsule_ref,
                "createdAt": _timestamp(observed),
                "expiresAt": _timestamp(observed + timedelta(seconds=self.lease_seconds)),
            }
            lease_directory = self.store_root / "leases" / capsule_id
            lease_directory.mkdir(mode=0o700, exist_ok=True)
            os.chmod(lease_directory, 0o700)
            _write_exclusive(lease_directory / f"{lease_token}.json", _json_bytes(lease_value))
        return {
            "readLeaseId": lease_id,
            "formatVersion": descriptor["formatVersion"],
            "projectionPolicyId": descriptor["projectionPolicyId"],
            "canonicalProjectRoot": descriptor["canonicalProjectRoot"],
            "baselineSourceIdentity": descriptor["baselineSourceIdentity"],
            "sealedRoot": str(capsule_path / "root"),
        }

    def release_read(self, lease_id: str) -> None:
        capsule_id, lease_token = self._lease_parts(lease_id)
        with self._coordination_lock(capsule_id):
            lease_path = self.store_root / "leases" / capsule_id / f"{lease_token}.json"
            if not lease_path.is_file():
                raise CapsuleError("INVALID_LEASE", f"lease does not exist: {lease_id}")
            value = _read_json(lease_path)
            if value.get("leaseId") != lease_id:
                raise CapsuleError("INVALID_LEASE", f"lease identity differs: {lease_id}")
            lease_path.unlink()

    def _has_active_lease(self, capsule_id: str, now: datetime) -> bool:
        lease_directory = self.store_root / "leases" / capsule_id
        if not lease_directory.is_dir():
            return False
        active = False
        for lease_path in sorted(lease_directory.glob("*.json")):
            try:
                lease = _read_json(lease_path)
                expires = _parse_timestamp(lease.get("expiresAt"), "lease.expiresAt")
            except CapsuleError:
                active = True
                continue
            if expires > now:
                active = True
            else:
                lease_path.unlink(missing_ok=True)
        return active

    def cleanup_expired(self, *, now: datetime | None = None) -> list[str]:
        observed = (now or _utc_now()).astimezone(timezone.utc)
        removed: list[str] = []
        for capsule_path in sorted((self.store_root / "capsules").iterdir()):
            if not capsule_path.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", capsule_path.name):
                continue
            capsule_id = capsule_path.name
            with self._coordination_lock(capsule_id):
                descriptor = _read_json(capsule_path / "descriptor.json")
                expires = _parse_timestamp(descriptor.get("expiresAt"), "expiresAt")
                if expires > observed or self._has_active_lease(capsule_id, observed):
                    continue
                _remove_tree(capsule_path)
                lease_directory = self.store_root / "leases" / capsule_id
                if lease_directory.exists():
                    _remove_tree(lease_directory)
                removed.append(f"capsule:v1:{capsule_id}")
        return removed


def _store_from_args(args: argparse.Namespace) -> CapsuleStore:
    return CapsuleStore(
        args.store_root,
        retention_seconds=getattr(args, "retention_seconds", DEFAULT_RETENTION_SECONDS),
        max_file_bytes=getattr(args, "max_file_bytes", DEFAULT_MAX_FILE_BYTES),
        max_total_bytes=getattr(args, "max_total_bytes", DEFAULT_MAX_TOTAL_BYTES),
        lease_seconds=getattr(args, "lease_seconds", DEFAULT_LEASE_SECONDS),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store-root", default=os.environ.get("BASELINE_CAPSULE_STORE", str(DEFAULT_STORE_ROOT)))
    commands = parser.add_subparsers(dest="command", required=True)

    create_parser = commands.add_parser("create")
    create_parser.add_argument("--project-root", required=True)
    create_parser.add_argument("--retention-seconds", type=int, default=DEFAULT_RETENTION_SECONDS)
    create_parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    create_parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES)

    identity_parser = commands.add_parser("identity")
    identity_parser.add_argument("--project-root", required=True)
    identity_parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    identity_parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES)

    acquire_parser = commands.add_parser("acquire-read")
    acquire_parser.add_argument("--capsule-ref", required=True)
    acquire_parser.add_argument("--lease-seconds", type=int, default=DEFAULT_LEASE_SECONDS)

    release_parser = commands.add_parser("release-read")
    release_parser.add_argument("--lease-id", required=True)

    commands.add_parser("cleanup-expired")
    args = parser.parse_args(argv)
    try:
        if args.command == "identity":
            result = capture_identity(
                args.project_root,
                max_file_bytes=args.max_file_bytes,
                max_total_bytes=args.max_total_bytes,
            )
        else:
            store = _store_from_args(args)
            if args.command == "create":
                result = store.create(args.project_root)
            elif args.command == "acquire-read":
                result = store.acquire_read(args.capsule_ref)
            elif args.command == "release-read":
                store.release_read(args.lease_id)
                result = {"released": True, "readLeaseId": args.lease_id}
            else:
                result = {"removedCapsuleRefs": store.cleanup_expired()}
    except CapsuleError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": exc.message}}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
