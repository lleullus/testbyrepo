#!/usr/bin/env python3
"""Side-effect-free pre-open audit for workflow SQLite stores.

The source database is never passed to SQLite.  Source files are observed and
copied through no-follow file descriptors, and all semantic inspection happens
against an owner-only private DB/WAL copy.  A successful report grants only a
short-lived, single-use lease bound to the exact guard session and source
manifest that were audited.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import tempfile
import threading
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TypeVar


DATABASE_FILENAME = "workflow.sqlite3"
SOURCE_FILE_NAMES = (
    ("MAIN", DATABASE_FILENAME),
    ("WAL", f"{DATABASE_FILENAME}-wal"),
    ("SHM", f"{DATABASE_FILENAME}-shm"),
    ("JOURNAL", f"{DATABASE_FILENAME}-journal"),
)
# Derived from an actual schema-v7 database created by release revision
# b0a747e7676710cfba4033611fbc89955271fc51.  The digest covers the ordered
# sqlite_master type/name/table/sql inventory, excluding SQLite-owned objects.
# A version-to-set mapping permits an explicitly reviewed fingerprint addition
# when a future release schema (for example v9) becomes authoritative.
AUTHORITATIVE_SCHEMA_FINGERPRINTS: Mapping[int, frozenset[str]] = MappingProxyType(
    {
        7: frozenset(
            {"317dabdf6e624e6365adffc7599a8b45e0576a4352e4d481a6ffe4396bdc0518"}
        ),
        9: frozenset(
            {"209e0d14c52fe855b7ca90794b64e087561b62a28296c2ac0b14a33125c4446a"}
        ),
    }
)
SUPPORTED_SCHEMA_VERSIONS = frozenset(AUTHORITATIVE_SCHEMA_FINGERPRINTS)
BUDGET_FIELDS = (
    "workerCalls",
    "remediationTransactions",
    "effectfulActions",
    "toolCostUnits",
    "closureOperations",
)
OPEN_TRANSACTION_STATES = frozenset(
    {"OPEN", "WORKER_ACTIVE", "RECONCILING", "READY_FOR_HANDOFF"}
)
CLOSED_TRANSACTION_STATES = frozenset(
    {"CLOSED_WITH_HANDOFF", "CLOSED_NO_SUCCESSOR"}
)
LEGACY_CONTINUATION_ENVELOPE_STATES = frozenset(
    {"DISPATCHED", "CAPTURED", "RECONCILED"}
)
LEGACY_UNSTARTED_CLOSURE_PATTERN = re.compile(
    r"^closure:unstarted:v1:[a-f0-9]{32}$"
)
CONSERVED_UNSTARTED_CLOSURE_PATTERN = re.compile(
    r"^closure:unstarted:v2:[a-f0-9]{32}$"
)

GuardKind = Literal["EXCLUSIVE_LOCK", "QUIESCENCE"]
AuditDisposition = Literal["CLEAR", "NO_STORE", "BLOCKED"]
T = TypeVar("T")
_GUARD_MINT_TOKEN = object()


class PreOpenAuditError(RuntimeError):
    """Fail-closed pre-open error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class GuardSession:
    """Evidence that writers are excluded for the whole audit/open window.

    ``is_active`` must continue to attest the same deployment-exclusive lock or
    deployment-owner quiescence session.  The audit lease also binds to this
    exact Python object, preventing a same-text identity from replacing the
    original session proof.
    """

    __slots__ = ("_canonical_root", "_identity", "_is_active", "_kind")

    def __init__(
        self,
        *,
        identity: str,
        kind: GuardKind,
        is_active: Callable[[], bool],
        canonical_root: str,
        _mint_token: object | None = None,
    ) -> None:
        if _mint_token is not _GUARD_MINT_TOKEN:
            raise TypeError(
                "GuardSession is authority-bearing and must be minted by an approved guard factory"
            )
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("guard identity must be a non-empty string")
        if kind not in ("EXCLUSIVE_LOCK", "QUIESCENCE"):
            raise ValueError("unsupported guard kind")
        if not callable(is_active):
            raise TypeError("guard is_active must be callable")
        if not isinstance(canonical_root, str) or not os.path.isabs(canonical_root):
            raise ValueError("guard canonical root must be an absolute path")
        self._identity = identity.strip()
        self._kind = kind
        self._is_active = is_active
        self._canonical_root = os.path.realpath(canonical_root)

    @property
    def identity(self) -> str:
        return self._identity

    @property
    def kind(self) -> GuardKind:
        return self._kind

    @property
    def canonical_root(self) -> str:
        return self._canonical_root

    def assert_root(self, raw_root: Path | str) -> None:
        lexical = os.path.abspath(os.fspath(Path(raw_root).expanduser()))
        canonical = os.path.realpath(lexical)
        if canonical != self._canonical_root:
            raise PreOpenAuditError(
                "AUDIT_GUARD_ROOT_MISMATCH",
                "guard session is not bound to the selected workflow root",
            )

    def assert_active(self) -> None:
        try:
            active = self._is_active()
        except BaseException as exc:
            raise PreOpenAuditError(
                "AUDIT_GUARD_UNPROVABLE",
                f"guard session {self.identity!r} could not be verified",
            ) from exc
        if active is not True:
            raise PreOpenAuditError(
                "AUDIT_GUARD_NOT_HELD",
                f"guard session {self.identity!r} is not active",
            )


def _mint_guard_session(
    *,
    identity: str,
    kind: GuardKind,
    is_active: Callable[[], bool],
    raw_root: Path | str,
) -> GuardSession:
    """Private authority seam used by the locked-FD adapter and tests."""

    lexical = os.path.abspath(os.fspath(Path(raw_root).expanduser()))
    return GuardSession(
        identity=identity,
        kind=kind,
        is_active=is_active,
        canonical_root=os.path.realpath(lexical),
        _mint_token=_GUARD_MINT_TOKEN,
    )


@dataclass(frozen=True)
class RootIdentity:
    exists: bool
    device: int | None
    inode: int | None
    mode: int | None
    uid: int | None
    gid: int | None
    mtime_ns: int | None

    def as_dict(self) -> dict[str, object]:
        return {
            "exists": self.exists,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "uid": self.uid,
            "gid": self.gid,
            "mtimeNs": self.mtime_ns,
        }


@dataclass(frozen=True)
class SourceFileManifest:
    role: str
    path: str
    exists: bool
    device: int | None
    inode: int | None
    mode: int | None
    uid: int | None
    gid: int | None
    size: int | None
    mtime_ns: int | None
    sha256: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "path": self.path,
            "exists": self.exists,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "uid": self.uid,
            "gid": self.gid,
            "size": self.size,
            "mtimeNs": self.mtime_ns,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class SourceManifest:
    raw_root: str
    canonical_root: str
    canonical_database_path: str
    root: RootIdentity
    files: tuple[SourceFileManifest, ...]
    digest: str

    def file(self, role: str) -> SourceFileManifest:
        for entry in self.files:
            if entry.role == role:
                return entry
        raise KeyError(role)

    def as_dict(self) -> dict[str, object]:
        return {
            "rawRoot": self.raw_root,
            "canonicalRoot": self.canonical_root,
            "canonicalDatabasePath": self.canonical_database_path,
            "root": self.root.as_dict(),
            "files": [entry.as_dict() for entry in self.files],
            "digest": self.digest,
        }


@dataclass(frozen=True)
class SchemaObject:
    object_type: str
    name: str
    table_name: str
    sql: str | None


@dataclass(frozen=True)
class LegacyTransactionFact:
    transaction_ref: str
    mode: str
    state: str
    closed_at: str | None


@dataclass(frozen=True)
class LegacyEnvelopeFact:
    envelope_ref: str
    transaction_ref: str
    task_id: str
    state: str
    closed_at: str | None


@dataclass(frozen=True)
class LegacyRunFact:
    run_ref: str
    claim_ref: str
    state: str
    closed_at: str | None
    sealed_plan_json: bytes | None
    sealed_plan_sha256: str | None


BudgetItems = tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class HistoricalReleasedFact:
    claim_ref: str
    closure_ref: str | None
    reservation_ref: str | None
    claimant_actor_ref: str
    invocation_ref: str | None
    spend_used: BudgetItems | None
    closure_used: BudgetItems | None
    issues: tuple[str, ...]


@dataclass(frozen=True)
class AuditReport:
    disposition: AuditDisposition
    guard_identity: str
    guard_kind: GuardKind
    source_manifest: SourceManifest
    schema_version: int | None
    schema_fingerprint: str | None
    schema_objects: tuple[SchemaObject, ...]
    sqlite_database_paths: tuple[str, ...]
    open_transactions: tuple[LegacyTransactionFact, ...]
    open_envelopes: tuple[LegacyEnvelopeFact, ...]
    open_runs: tuple[LegacyRunFact, ...]
    historical_released: tuple[HistoricalReleasedFact, ...]
    blockers: tuple[str, ...]

    @property
    def is_admitted(self) -> bool:
        return self.disposition in ("CLEAR", "NO_STORE")

    @property
    def executor_floor(self) -> str | None:
        return "process-v3" if self.schema_version == 9 else None


@dataclass(frozen=True)
class AuditOutcome:
    report: AuditReport
    lease: AuditLease | None


@dataclass(frozen=True)
class _AuditHooks:
    """Deterministic race/failure hooks used only by regression tests."""

    after_first_manifest_pass: Callable[[SourceManifest], None] | None = None
    after_private_copy: Callable[[Path], None] | None = None
    before_post_audit_manifest: Callable[[], None] | None = None


class AuditLease:
    """Single-use authority to invoke an opener immediately after revalidation."""

    def __init__(
        self,
        *,
        report: AuditReport,
        raw_root: Path,
        guard: GuardSession,
        ttl_seconds: float,
    ) -> None:
        if not report.is_admitted:
            raise ValueError("a blocked report cannot issue an audit lease")
        self._report = report
        self._raw_root = raw_root
        self._guard = guard
        self._expires_at = time.monotonic() + ttl_seconds
        self._state_lock = threading.Lock()
        self._consumed = False

    @property
    def report(self) -> AuditReport:
        return self._report

    @property
    def consumed(self) -> bool:
        with self._state_lock:
            return self._consumed

    def discard(self) -> None:
        with self._state_lock:
            self._consumed = True

    def consume(
        self,
        *,
        guard: GuardSession,
        opener: Callable[[Path, AuditReport], T],
    ) -> T:
        """Revalidate and synchronously call the one authorized opener.

        The lease is spent even when revalidation or the opener fails.  This
        prevents a stale audit from becoming reusable after any failed cutover
        attempt.
        """

        if not callable(opener):
            raise TypeError("opener must be callable")
        with self._state_lock:
            if self._consumed:
                raise PreOpenAuditError(
                    "AUDIT_LEASE_ALREADY_CONSUMED", "audit lease is single-use"
                )
            self._consumed = True

        if guard is not self._guard:
            raise PreOpenAuditError(
                "AUDIT_GUARD_MISMATCH",
                "audit lease must be consumed by the original guard session",
            )
        if time.monotonic() > self._expires_at:
            raise PreOpenAuditError("AUDIT_LEASE_EXPIRED", "audit lease expired")
        guard.assert_root(self._raw_root)
        guard.assert_active()
        current = capture_source_manifest(self._raw_root)
        if current != self._report.source_manifest:
            raise PreOpenAuditError(
                "AUDIT_SOURCE_CHANGED",
                "source manifest changed after the private-copy audit",
            )
        guard.assert_active()
        return opener(Path(self._report.source_manifest.canonical_root), self._report)


def _json_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _resolve_root(raw_root: Path | str) -> tuple[Path, Path, RootIdentity, int | None]:
    raw = _lexical_absolute(Path(raw_root))
    try:
        raw_stat = os.lstat(raw)
    except FileNotFoundError:
        canonical = Path(os.path.realpath(raw))
        return (
            raw,
            canonical,
            RootIdentity(False, None, None, None, None, None, None),
            None,
        )
    except OSError as exc:
        raise PreOpenAuditError(
            "SOURCE_ROOT_UNREADABLE", f"cannot inspect workflow root {raw}"
        ) from exc

    if stat.S_ISLNK(raw_stat.st_mode):
        raise PreOpenAuditError(
            "SOURCE_ROOT_SYMLINK", f"workflow root is a symlink: {raw}"
        )
    if not stat.S_ISDIR(raw_stat.st_mode):
        raise PreOpenAuditError(
            "SOURCE_ROOT_NON_DIRECTORY", f"workflow root is not a directory: {raw}"
        )

    try:
        canonical = raw.resolve(strict=True)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        root_fd = os.open(canonical, flags)
    except OSError as exc:
        raise PreOpenAuditError(
            "SOURCE_ROOT_UNREADABLE", f"cannot open workflow root {raw}"
        ) from exc
    opened = os.fstat(root_fd)
    canonical_stat = os.stat(canonical, follow_symlinks=False)
    if not stat.S_ISDIR(opened.st_mode) or _stat_key(opened) != _stat_key(canonical_stat):
        os.close(root_fd)
        raise PreOpenAuditError(
            "SOURCE_ROOT_RACE", f"workflow root changed while opening: {raw}"
        )
    identity = RootIdentity(
        True,
        opened.st_dev,
        opened.st_ino,
        stat.S_IMODE(opened.st_mode),
        opened.st_uid,
        opened.st_gid,
        opened.st_mtime_ns,
    )
    return raw, canonical, identity, root_fd


def _stat_key(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_uid,
        value.st_gid,
        value.st_size,
        value.st_mtime_ns,
    )


def _missing_file(role: str, path: Path) -> SourceFileManifest:
    return SourceFileManifest(
        role,
        str(path),
        False,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )


def _open_source_file(root_fd: int, name: str, role: str) -> tuple[int, os.stat_result]:
    try:
        observed = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise PreOpenAuditError(
            "SOURCE_FILE_UNREADABLE", f"cannot lstat source {role}"
        ) from exc
    if stat.S_ISLNK(observed.st_mode):
        raise PreOpenAuditError(
            "SOURCE_FILE_SYMLINK", f"source {role} must not be a symlink"
        )
    if not stat.S_ISREG(observed.st_mode):
        raise PreOpenAuditError(
            "SOURCE_FILE_NON_REGULAR", f"source {role} must be a regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        source_fd = os.open(name, flags, dir_fd=root_fd)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise PreOpenAuditError(
                "SOURCE_FILE_SYMLINK", f"source {role} became a symlink"
            ) from exc
        raise PreOpenAuditError(
            "SOURCE_FILE_UNREADABLE", f"cannot no-follow open source {role}"
        ) from exc
    opened = os.fstat(source_fd)
    if not stat.S_ISREG(opened.st_mode) or _stat_key(opened) != _stat_key(observed):
        os.close(source_fd)
        raise PreOpenAuditError(
            "SOURCE_FILE_RACE", f"source {role} changed while opening"
        )
    return source_fd, observed


def _observe_file(
    *, root_fd: int, canonical_root: Path, role: str, name: str
) -> SourceFileManifest:
    path = canonical_root / name
    try:
        source_fd, observed = _open_source_file(root_fd, name, role)
    except FileNotFoundError:
        return _missing_file(role, path)
    digest = hashlib.sha256()
    try:
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after_read = os.fstat(source_fd)
        try:
            after_path = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            raise PreOpenAuditError(
                "SOURCE_FILE_RACE", f"source {role} disappeared while hashing"
            ) from exc
        if _stat_key(observed) != _stat_key(after_read) or _stat_key(observed) != _stat_key(
            after_path
        ):
            raise PreOpenAuditError(
                "SOURCE_FILE_RACE", f"source {role} changed while hashing"
            )
    finally:
        os.close(source_fd)
    return SourceFileManifest(
        role,
        str(path),
        True,
        observed.st_dev,
        observed.st_ino,
        stat.S_IMODE(observed.st_mode),
        observed.st_uid,
        observed.st_gid,
        observed.st_size,
        observed.st_mtime_ns,
        digest.hexdigest(),
    )


def capture_source_manifest(raw_root: Path | str) -> SourceManifest:
    """Capture one fd-verified manifest without creating or SQLite-opening source."""

    raw, canonical, root_identity, root_fd = _resolve_root(raw_root)
    files: list[SourceFileManifest] = []
    try:
        if root_fd is None:
            files = [
                _missing_file(role, canonical / name) for role, name in SOURCE_FILE_NAMES
            ]
        else:
            for role, name in SOURCE_FILE_NAMES:
                files.append(
                    _observe_file(
                        root_fd=root_fd,
                        canonical_root=canonical,
                        role=role,
                        name=name,
                    )
                )
            current_root = os.fstat(root_fd)
            if (
                current_root.st_dev != root_identity.device
                or current_root.st_ino != root_identity.inode
                or stat.S_IMODE(current_root.st_mode) != root_identity.mode
                or current_root.st_uid != root_identity.uid
                or current_root.st_gid != root_identity.gid
                or current_root.st_mtime_ns != root_identity.mtime_ns
            ):
                raise PreOpenAuditError(
                    "SOURCE_ROOT_RACE", "workflow root changed during manifest capture"
                )
            path_stat = os.stat(canonical, follow_symlinks=False)
            if path_stat.st_dev != root_identity.device or path_stat.st_ino != root_identity.inode:
                raise PreOpenAuditError(
                    "SOURCE_ROOT_RACE", "workflow root path was replaced during capture"
                )
    finally:
        if root_fd is not None:
            os.close(root_fd)

    payload = {
        "rawRoot": str(raw),
        "canonicalRoot": str(canonical),
        "canonicalDatabasePath": str(canonical / DATABASE_FILENAME),
        "root": root_identity.as_dict(),
        "files": [entry.as_dict() for entry in files],
    }
    return SourceManifest(
        str(raw),
        str(canonical),
        str(canonical / DATABASE_FILENAME),
        root_identity,
        tuple(files),
        _json_digest(payload),
    )


def _classify_manifest(manifest: SourceManifest) -> tuple[AuditDisposition, tuple[str, ...]]:
    main = manifest.file("MAIN")
    sidecars = tuple(entry for entry in manifest.files if entry.role != "MAIN")
    if not main.exists:
        orphaned = tuple(entry.role for entry in sidecars if entry.exists)
        if orphaned:
            return "BLOCKED", tuple(f"ORPHAN_SIDECAR:{role}" for role in orphaned)
        return "NO_STORE", ()
    journal = manifest.file("JOURNAL")
    if journal.exists:
        return "BLOCKED", ("ROLLBACK_JOURNAL_PRESENT",)
    return "CLEAR", ()


def _write_all(file_descriptor: int, data: bytes) -> None:
    remaining = memoryview(data)
    while remaining:
        written = os.write(file_descriptor, remaining)
        if written <= 0:
            raise OSError("short write while copying private audit file")
        remaining = remaining[written:]


def _copy_source_file(
    *, root_fd: int, source_name: str, expected: SourceFileManifest, destination: Path
) -> None:
    source_fd, observed = _open_source_file(root_fd, source_name, expected.role)
    if (
        observed.st_dev != expected.device
        or observed.st_ino != expected.inode
        or stat.S_IMODE(observed.st_mode) != expected.mode
        or observed.st_uid != expected.uid
        or observed.st_gid != expected.gid
        or observed.st_size != expected.size
        or observed.st_mtime_ns != expected.mtime_ns
    ):
        os.close(source_fd)
        raise PreOpenAuditError(
            "SOURCE_FILE_RACE", f"source {expected.role} differs from stable manifest"
        )
    destination_flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    destination_fd: int | None = None
    source_digest = hashlib.sha256()
    try:
        destination_fd = os.open(destination, destination_flags, 0o600)
        os.fchmod(destination_fd, 0o600)
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            source_digest.update(chunk)
            _write_all(destination_fd, chunk)
        os.fsync(destination_fd)
        after = os.fstat(source_fd)
        if _stat_key(after) != _stat_key(observed):
            raise PreOpenAuditError(
                "SOURCE_FILE_RACE", f"source {expected.role} changed during copy"
            )
    except PreOpenAuditError:
        raise
    except OSError as exc:
        raise PreOpenAuditError(
            "PRIVATE_COPY_FAILED", f"could not copy source {expected.role}"
        ) from exc
    finally:
        os.close(source_fd)
        if destination_fd is not None:
            os.close(destination_fd)
    if source_digest.hexdigest() != expected.sha256:
        raise PreOpenAuditError(
            "PRIVATE_COPY_DIGEST_MISMATCH",
            f"source {expected.role} digest differs from stable manifest",
        )


def _digest_regular_private(path: Path) -> tuple[int, str]:
    try:
        observed = os.lstat(path)
    except OSError as exc:
        raise PreOpenAuditError(
            "PRIVATE_COPY_MISSING", f"private audit file is absent: {path.name}"
        ) from exc
    if not stat.S_ISREG(observed.st_mode) or stat.S_IMODE(observed.st_mode) != 0o600:
        raise PreOpenAuditError(
            "PRIVATE_COPY_INVALID", f"private audit file is not owner-only: {path.name}"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PreOpenAuditError(
            "PRIVATE_COPY_INVALID", f"cannot open private audit file: {path.name}"
        ) from exc
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if _stat_key(opened) != _stat_key(observed):
            raise PreOpenAuditError(
                "PRIVATE_COPY_INVALID", f"private audit file changed: {path.name}"
            )
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        if _stat_key(os.fstat(descriptor)) != _stat_key(observed):
            raise PreOpenAuditError(
                "PRIVATE_COPY_INVALID", f"private audit file changed: {path.name}"
            )
    finally:
        os.close(descriptor)
    return observed.st_size, digest.hexdigest()


def _make_private_copy(
    manifest: SourceManifest,
    *,
    private_parent: Path | None,
    guard: GuardSession,
) -> tuple[Path, Path]:
    canonical_root = Path(manifest.canonical_root)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    private_root: Path | None = None
    try:
        root_fd = os.open(canonical_root, flags)
    except OSError as exc:
        raise PreOpenAuditError(
            "SOURCE_ROOT_RACE", "cannot reopen workflow root for private copy"
        ) from exc
    try:
        opened_root = os.fstat(root_fd)
        if opened_root.st_dev != manifest.root.device or opened_root.st_ino != manifest.root.inode:
            raise PreOpenAuditError(
                "SOURCE_ROOT_RACE", "workflow root differs from stable manifest"
            )
        parent_text = None if private_parent is None else os.fspath(private_parent)
        private_root = Path(tempfile.mkdtemp(prefix="workflow-preopen-", dir=parent_text))
        os.chmod(private_root, 0o700)
        if stat.S_IMODE(os.lstat(private_root).st_mode) != 0o700:
            raise PreOpenAuditError(
                "PRIVATE_COPY_PERMISSIONS", "private audit directory is not owner-only"
            )
        guard.assert_active()
        for role, source_name in SOURCE_FILE_NAMES[:2]:
            expected = manifest.file(role)
            if expected.exists:
                _copy_source_file(
                    root_fd=root_fd,
                    source_name=source_name,
                    expected=expected,
                    destination=private_root / source_name,
                )
        return private_root, private_root / DATABASE_FILENAME
    except BaseException:
        if private_root is not None:
            shutil.rmtree(private_root)
        raise
    finally:
        os.close(root_fd)


def _verify_private_copy(private_database: Path, manifest: SourceManifest) -> None:
    for role, name in SOURCE_FILE_NAMES[:2]:
        expected = manifest.file(role)
        private_path = private_database.parent / name
        if not expected.exists:
            if private_path.exists():
                raise PreOpenAuditError(
                    "PRIVATE_COPY_UNEXPECTED_FILE", f"unexpected private {role} copy"
                )
            continue
        size, digest = _digest_regular_private(private_path)
        if size != expected.size or digest != expected.sha256:
            raise PreOpenAuditError(
                "PRIVATE_COPY_DIGEST_MISMATCH",
                f"private {role} differs from initial source manifest",
            )
    for role, name in SOURCE_FILE_NAMES[2:]:
        if (private_database.parent / name).exists():
            raise PreOpenAuditError(
                "PRIVATE_COPY_UNEXPECTED_FILE", f"source {role} must not be copied"
            )


def _decode_budget(value: object, locator: str) -> BudgetItems:
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{locator} is not UTF-8") from exc
    if not isinstance(value, str):
        raise ValueError(f"{locator} is not JSON text")
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{locator} is malformed JSON") from exc
    if not isinstance(decoded, dict) or set(decoded) != set(BUDGET_FIELDS):
        raise ValueError(f"{locator} has invalid fields")
    result: list[tuple[str, int]] = []
    for field_name in BUDGET_FIELDS:
        amount = decoded[field_name]
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError(f"{locator}.{field_name} is invalid")
        result.append((field_name, amount))
    return tuple(result)


def _budget_mapping(items: BudgetItems) -> dict[str, int]:
    return dict(items)


def _schema_inventory(connection: sqlite3.Connection) -> tuple[SchemaObject, ...]:
    rows = connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()
    return tuple(
        SchemaObject(str(row[0]), str(row[1]), str(row[2]), row[3]) for row in rows
    )


def _schema_fingerprint(objects: tuple[SchemaObject, ...]) -> str:
    return _json_digest(
        [
            {
                "type": item.object_type,
                "name": item.name,
                "tableName": item.table_name,
                "sql": item.sql,
            }
            for item in objects
        ]
    )


def _read_schema_version(connection: sqlite3.Connection) -> int:
    rows = connection.execute(
        "SELECT value FROM store_meta WHERE key = 'schema_version'"
    ).fetchall()
    if len(rows) != 1:
        raise PreOpenAuditError(
            "SCHEMA_VERSION_INVALID", "store_meta must contain exactly one schema version"
        )
    raw = rows[0][0]
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdigit():
        raise PreOpenAuditError(
            "SCHEMA_VERSION_INVALID", "workflow schema version is malformed"
        )
    return int(raw)


def _executor_floor_blockers(
    connection: sqlite3.Connection, schema_version: int
) -> tuple[str, ...]:
    rows = connection.execute(
        "SELECT value FROM store_meta WHERE key = 'executor_floor'"
    ).fetchall()
    if schema_version == 9:
        if len(rows) != 1 or rows[0][0] != "process-v3":
            return ("EXECUTOR_FLOOR_MISMATCH:9",)
        return ()
    if rows:
        return (f"UNEXPECTED_EXECUTOR_FLOOR:{schema_version}",)
    return ()


def _open_legacy_facts(
    connection: sqlite3.Connection,
) -> tuple[
    tuple[LegacyTransactionFact, ...],
    tuple[LegacyEnvelopeFact, ...],
    tuple[LegacyRunFact, ...],
]:
    transaction_rows = connection.execute(
        """
        SELECT transaction_ref, mode, state, closed_at
        FROM implementation_transactions
        WHERE state NOT IN ('CLOSED_WITH_HANDOFF', 'CLOSED_NO_SUCCESSOR')
           OR closed_at IS NULL
        ORDER BY transaction_ref
        """
    ).fetchall()
    transactions = tuple(
        LegacyTransactionFact(str(row[0]), str(row[1]), str(row[2]), row[3])
        for row in transaction_rows
    )
    open_refs = tuple(item.transaction_ref for item in transactions)
    envelopes: tuple[LegacyEnvelopeFact, ...] = ()
    if open_refs:
        placeholders = ",".join("?" for _ in open_refs)
        envelope_rows = connection.execute(
            f"""
            SELECT envelope_ref, transaction_ref, task_id, state, closed_at
            FROM implementation_envelopes
            WHERE transaction_ref IN ({placeholders})
            ORDER BY transaction_ref, envelope_ref
            """,
            open_refs,
        ).fetchall()
        envelopes = tuple(
            LegacyEnvelopeFact(
                str(row[0]), str(row[1]), str(row[2]), str(row[3]), row[4]
            )
            for row in envelope_rows
        )
    run_rows = connection.execute(
        """
        SELECT run_ref, claim_ref, state, closed_at, sealed_plan_json, sealed_plan_sha256
        FROM verification_runs
        WHERE state != 'CLOSED' OR closed_at IS NULL
        ORDER BY run_ref
        """
    ).fetchall()
    runs = tuple(
        LegacyRunFact(
            str(row[0]),
            str(row[1]),
            str(row[2]),
            row[3],
            None if row[4] is None else bytes(row[4]),
            None if row[5] is None else str(row[5]),
        )
        for row in run_rows
    )
    return transactions, envelopes, runs


def _legacy_fact_blockers(
    transactions: tuple[LegacyTransactionFact, ...],
    envelopes: tuple[LegacyEnvelopeFact, ...],
    runs: tuple[LegacyRunFact, ...],
    *,
    schema_version: int,
) -> tuple[str, ...]:
    """Classify legacy facts without granting them new-code semantics.

    A lone FROZEN envelope on a well-shaped open transaction remains eligible
    only for the new dispatch-time revalidation.  Anything that was already
    dispatched, captured, or reconciled by legacy code is diagnostic evidence,
    not authority to continue through a migration.
    """

    blockers: list[str] = []
    transaction_states: dict[str, str] = {}
    for transaction_fact in transactions:
        transaction_states[transaction_fact.transaction_ref] = transaction_fact.state
        locator = f"LEGACY_TRANSACTION:{transaction_fact.transaction_ref}"
        if transaction_fact.state in OPEN_TRANSACTION_STATES:
            if transaction_fact.closed_at is not None:
                blockers.append(f"{locator}:OPEN_STATE_HAS_CLOSED_AT")
        elif transaction_fact.state in CLOSED_TRANSACTION_STATES:
            if transaction_fact.closed_at is None:
                blockers.append(f"{locator}:CLOSED_STATE_MISSING_CLOSED_AT")
        else:
            blockers.append(f"{locator}:UNSUPPORTED_STATE:{transaction_fact.state}")

    active_counts: dict[str, int] = {}
    for envelope_fact in envelopes:
        locator = f"LEGACY_ENVELOPE:{envelope_fact.envelope_ref}"
        transaction_state = transaction_states.get(envelope_fact.transaction_ref)
        if transaction_state is None:
            blockers.append(f"{locator}:TRANSACTION_FACT_MISSING")
            continue
        if envelope_fact.state != "RECONCILED":
            active_counts[envelope_fact.transaction_ref] = (
                active_counts.get(envelope_fact.transaction_ref, 0) + 1
            )
        if transaction_state not in OPEN_TRANSACTION_STATES:
            continue
        if envelope_fact.state == "FROZEN":
            if envelope_fact.closed_at is not None:
                blockers.append(f"{locator}:FROZEN_HAS_CLOSED_AT")
            continue
        if envelope_fact.state in LEGACY_CONTINUATION_ENVELOPE_STATES:
            blockers.append(
                f"{locator}:CONTINUATION_NOT_ADMITTED:{envelope_fact.state}"
            )
            continue
        blockers.append(f"{locator}:UNSUPPORTED_STATE:{envelope_fact.state}")
    for transaction_ref, count in sorted(active_counts.items()):
        if count > 1:
            blockers.append(
                f"LEGACY_TRANSACTION:{transaction_ref}:MULTIPLE_ACTIVE_ENVELOPES:{count}"
            )

    for run_fact in runs:
        locator = f"LEGACY_RUN:{run_fact.run_ref}"
        if run_fact.state == "CLOSED":
            if run_fact.closed_at is None:
                blockers.append(f"{locator}:CLOSED_STATE_MISSING_CLOSED_AT")
            continue
        if run_fact.closed_at is not None:
            blockers.append(f"{locator}:OPEN_STATE_HAS_CLOSED_AT")
        if schema_version != 9:
            blockers.append(f"{locator}:CONTROLLED_DRAIN_REQUIRED:{run_fact.state}")
            continue
        if run_fact.state == "PREFLIGHT":
            if (
                run_fact.sealed_plan_json is not None
                or run_fact.sealed_plan_sha256 is not None
            ):
                blockers.append(f"{locator}:PREFLIGHT_HAS_SEALED_PLAN")
            continue
        if run_fact.state != "SEALED":
            blockers.append(f"{locator}:UNSUPPORTED_STATE:{run_fact.state}")
            continue
        sealed = run_fact.sealed_plan_json
        sealed_digest = run_fact.sealed_plan_sha256
        if (
            sealed is None
            or sealed_digest is None
            or re.fullmatch(r"[a-f0-9]{64}", sealed_digest) is None
            or hashlib.sha256(sealed).hexdigest() != sealed_digest
        ):
            blockers.append(f"{locator}:SEALED_PLAN_DIGEST_INVALID")
            continue
        try:
            plan = json.loads(sealed)
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append(f"{locator}:SEALED_PLAN_UNREADABLE")
            continue
        flows = plan.get("flows") if isinstance(plan, dict) else None
        if not isinstance(flows, list):
            blockers.append(f"{locator}:SEALED_PLAN_MALFORMED")
            continue
        invalid_policy = False
        for flow in flows:
            steps = flow.get("steps") if isinstance(flow, dict) else None
            if not isinstance(steps, list):
                invalid_policy = True
                break
            for step in steps:
                if not isinstance(step, dict):
                    invalid_policy = True
                    break
                identity = step.get("executableIdentity")
                if (
                    step.get("executorKind") != "PROCESS"
                    or step.get("executorVersion") != "process-v3"
                    or step.get("environmentPolicy") != "SEALED_EMPTY_BASE_V1"
                    or not isinstance(identity, dict)
                    or set(identity)
                    != {
                        "canonicalPath",
                        "contentSha256",
                        "byteCount",
                        "executableMode",
                        "ownerUid",
                        "ownerGid",
                    }
                    or re.fullmatch(r"[a-f0-9]{64}", str(step.get("canonicalRequestDigest")))
                    is None
                    or re.fullmatch(r"[a-f0-9]{64}", str(step.get("repeatRequestDigest")))
                    is None
                ):
                    invalid_policy = True
                    break
            if invalid_policy:
                break
        if invalid_policy:
            blockers.append(f"{locator}:NON_V3_OR_MALFORMED_EXECUTOR")
    return tuple(blockers)


def _active_claim_blockers(
    connection: sqlite3.Connection, *, schema_version: int
) -> tuple[str, ...]:
    """Cross-check active claim ownership before admitting a writable open."""

    rows = connection.execute(
        """
        SELECT
            c.*,
            claimant.role AS claimant_role,
            claimant.root_ref AS claimant_root_ref,
            claimant.invocation_ref AS claimant_invocation_ref,
            claimant.bound_claim_ref AS claimant_bound_claim_ref,
            coordinator.role AS coordinator_role,
            coordinator.root_ref AS coordinator_root_ref,
            coordinator.invocation_ref AS coordinator_invocation_ref,
            br.invocation_ref AS reservation_invocation_ref,
            br.transition_kind AS reservation_transition_kind,
            br.state AS reservation_state,
            i.root_ref AS invocation_root_ref,
            i.state AS invocation_state,
            tip.root_ref AS tip_root_ref,
            edge.successor_ref AS tip_successor_ref,
            vr.run_ref AS run_ref,
            vr.claim_ref AS run_claim_ref,
            vr.assessor_actor_ref AS run_assessor_actor_ref,
            vr.root_ref AS run_root_ref,
            vr.state AS run_state,
            it.transaction_ref AS transaction_ref,
            it.claim_ref AS transaction_claim_ref,
            it.owner_actor_ref AS transaction_owner_actor_ref,
            it.root_ref AS transaction_root_ref,
            it.state AS transaction_state
        FROM claims AS c
        LEFT JOIN actors AS claimant
          ON claimant.actor_ref = c.claimant_actor_ref
        LEFT JOIN actors AS coordinator
          ON coordinator.actor_ref = c.coordinator_actor_ref
        LEFT JOIN budget_reservations AS br
          ON br.reservation_ref = c.budget_reservation_ref
        LEFT JOIN invocations AS i
          ON i.invocation_ref = br.invocation_ref
        LEFT JOIN nodes AS tip
          ON tip.node_ref = c.tip_ref
        LEFT JOIN edges AS edge
          ON edge.predecessor_ref = c.tip_ref
        LEFT JOIN verification_runs AS vr
          ON vr.run_ref = c.execution_ref
        LEFT JOIN implementation_transactions AS it
          ON it.transaction_ref = c.execution_ref
        WHERE c.state = 'ACTIVE'
        ORDER BY c.claim_ref
        """
    ).fetchall()
    blockers: list[str] = []
    for row in rows:
        claim_ref = str(row["claim_ref"])
        locator = f"ACTIVE_CLAIM:{claim_ref}"
        transition = row["transition_kind"]
        expected_role = {"VERIFY": "ASSESSOR", "REMEDIATE": "REMEDIATOR"}.get(
            transition
        )
        if (
            expected_role is None
            or row["claimant_role"] != expected_role
            or row["claimant_root_ref"] != row["root_ref"]
            or row["claimant_bound_claim_ref"] != claim_ref
            or row["coordinator_role"] != "COORDINATOR"
            or row["coordinator_root_ref"] != row["root_ref"]
            or row["coordinator_invocation_ref"] != row["claimant_invocation_ref"]
            or row["reservation_invocation_ref"] != row["claimant_invocation_ref"]
            or row["reservation_transition_kind"] != transition
            or row["reservation_state"] != "ACTIVE"
            or row["invocation_root_ref"] != row["root_ref"]
            or row["invocation_state"] != "ACTIVE"
            or row["tip_root_ref"] != row["root_ref"]
            or row["tip_successor_ref"] is not None
        ):
            blockers.append(f"{locator}:OWNERSHIP_RELATION_MISMATCH")
            continue
        if transition == "VERIFY":
            if row["transaction_ref"] is not None:
                blockers.append(f"{locator}:VERIFY_EXECUTION_RELATION_MISMATCH")
            elif row["run_ref"] is None:
                # Claim acquisition deliberately precedes creation of its
                # durable execution fact.  This is the recoverable unstarted
                # state consumed by release_unstarted_claim().
                continue
            elif (
                row["run_ref"] != row["execution_ref"]
                or row["run_claim_ref"] != claim_ref
                or row["run_assessor_actor_ref"] != row["claimant_actor_ref"]
                or row["run_root_ref"] != row["root_ref"]
                or row["run_state"] not in {"PREFLIGHT", "SEALED"}
            ):
                blockers.append(f"{locator}:VERIFY_EXECUTION_RELATION_MISMATCH")
            elif schema_version != 9:
                blockers.append(f"{locator}:CONTROLLED_DRAIN_REQUIRED")
        elif row["run_ref"] is not None:
            blockers.append(f"{locator}:REMEDIATE_EXECUTION_RELATION_MISMATCH")
        elif row["transaction_ref"] is None:
            # The implementation transaction is created only after the
            # remediation claim has been acquired and the audited store has
            # been reopened.  Absence here is therefore the valid unstarted
            # claim state, not a dangling execution relation.
            continue
        elif (
            row["transaction_ref"] != row["execution_ref"]
            or row["transaction_claim_ref"] != claim_ref
            or row["transaction_owner_actor_ref"] != row["claimant_actor_ref"]
            or row["transaction_root_ref"] != row["root_ref"]
            or row["transaction_state"]
            not in {"OPEN", "WORKER_ACTIVE", "RECONCILING", "READY_FOR_HANDOFF"}
        ):
            blockers.append(f"{locator}:REMEDIATE_EXECUTION_RELATION_MISMATCH")
    return tuple(blockers)


def _historical_released_facts(
    connection: sqlite3.Connection,
    *,
    schema_version: int,
) -> tuple[HistoricalReleasedFact, ...]:
    rows = connection.execute(
        """
        SELECT
            c.claim_ref,
            c.closure_ref,
            c.root_ref AS claim_root_ref,
            c.transition_kind AS claim_transition_kind,
            c.execution_ref AS claim_execution_ref,
            c.closed_at AS claim_closed_at,
            c.claimant_actor_ref,
            c.budget_reservation_ref AS claimed_reservation_ref,
            br.reservation_ref,
            br.invocation_ref AS reservation_invocation_ref,
            br.transition_kind AS reservation_transition_kind,
            br.spend_reserved_json,
            br.closure_reserved_json,
            br.spend_used_json,
            br.closure_used_json,
            br.state AS reservation_state,
            br.closed_at AS reservation_closed_at,
            a.actor_ref,
            a.role AS actor_role,
            a.root_ref AS actor_root_ref,
            a.invocation_ref AS actor_invocation_ref,
            a.bound_claim_ref,
            i.invocation_ref,
            i.limits_json,
            i.consumed_json,
            i.state AS invocation_state,
            vr.run_ref AS durable_verification_run_ref,
            it.transaction_ref AS durable_implementation_transaction_ref
        FROM claims AS c
        LEFT JOIN budget_reservations AS br
          ON br.reservation_ref = c.budget_reservation_ref
        LEFT JOIN actors AS a
          ON a.actor_ref = c.claimant_actor_ref
        LEFT JOIN invocations AS i
          ON i.invocation_ref = br.invocation_ref
        LEFT JOIN verification_runs AS vr
          ON vr.run_ref = c.execution_ref
        LEFT JOIN implementation_transactions AS it
          ON it.transaction_ref = c.execution_ref
        WHERE c.state = 'RELEASED'
          AND (
              c.closure_ref LIKE 'closure:unstarted:v1:%'
              OR c.closure_ref LIKE 'closure:unstarted:v2:%'
          )
        ORDER BY c.claim_ref
        """
    ).fetchall()
    facts: list[HistoricalReleasedFact] = []
    conserved_totals: dict[str, dict[str, int]] = {}
    consumed_by_invocation: dict[str, dict[str, int]] = {}
    for row in rows:
        claim_ref = str(row[0])
        closure_ref = None if row[1] is None else str(row[1])
        issues: list[str] = []
        legacy_unproved = (
            closure_ref is not None
            and LEGACY_UNSTARTED_CLOSURE_PATTERN.fullmatch(closure_ref) is not None
        )
        conserved_release = (
            closure_ref is not None
            and CONSERVED_UNSTARTED_CLOSURE_PATTERN.fullmatch(closure_ref) is not None
        )
        if not legacy_unproved and not conserved_release:
            issues.append("MALFORMED_CLOSURE_REF")
        if conserved_release and schema_version != 9:
            issues.append("CONSERVED_CLOSURE_REQUIRES_V9")
        if row[5] is None:
            issues.append("CLAIM_NOT_CLOSED")
        reservation_ref = None if row[8] is None else str(row[8])
        if reservation_ref is None:
            issues.append("MISSING_RESERVATION")
        elif str(row[7]) != reservation_ref:
            issues.append("RESERVATION_REF_MISMATCH")
        if row[15] != "CLOSED" or row[16] is None:
            issues.append("RESERVATION_NOT_CLOSED")
        if row[3] != row[10]:
            issues.append("TRANSITION_KIND_MISMATCH")
        if row[17] is None:
            issues.append("MISSING_CLAIMANT_ACTOR")
        elif str(row[17]) != str(row[6]):
            issues.append("CLAIMANT_ACTOR_MISMATCH")
        expected_role = {"VERIFY": "ASSESSOR", "REMEDIATE": "REMEDIATOR"}.get(row[3])
        if expected_role is None or row[18] != expected_role:
            issues.append("CLAIMANT_ROLE_MISMATCH")
        if row[19] is None or str(row[19]) != str(row[2]):
            issues.append("ACTOR_ROOT_MISMATCH")
        if row[21] is None or str(row[21]) != claim_ref:
            issues.append("ACTOR_CLAIM_BINDING_MISMATCH")
        reservation_invocation = None if row[9] is None else str(row[9])
        if row[20] is None or reservation_invocation is None or str(row[20]) != reservation_invocation:
            issues.append("ACTOR_INVOCATION_MISMATCH")
        invocation_ref = None if row[22] is None else str(row[22])
        if invocation_ref is None:
            issues.append("MISSING_INVOCATION")
        elif invocation_ref != reservation_invocation:
            issues.append("INVOCATION_REF_MISMATCH")
        if row[25] not in {"ACTIVE", "CLOSED"}:
            issues.append("INVOCATION_STATE_INVALID")
        if row[26] is not None:
            issues.append("DURABLE_VERIFICATION_RUN_PRESENT")
        if row[27] is not None:
            issues.append("DURABLE_IMPLEMENTATION_TRANSACTION_PRESENT")

        vectors: dict[str, BudgetItems] = {}
        for locator, index in (
            ("spend_reserved_json", 11),
            ("closure_reserved_json", 12),
            ("spend_used_json", 13),
            ("closure_used_json", 14),
            ("limits_json", 23),
            ("consumed_json", 24),
        ):
            try:
                vectors[locator] = _decode_budget(row[index], locator)
            except ValueError:
                issues.append(f"MALFORMED_{locator.upper()}")
        spend_used = vectors.get("spend_used_json")
        closure_used = vectors.get("closure_used_json")
        spend_reserved = vectors.get("spend_reserved_json")
        closure_reserved = vectors.get("closure_reserved_json")
        if spend_used is not None and spend_reserved is not None:
            used = _budget_mapping(spend_used)
            reserved = _budget_mapping(spend_reserved)
            if any(used[field_name] > reserved[field_name] for field_name in BUDGET_FIELDS):
                issues.append("SPEND_USED_EXCEEDS_RESERVED")
        if closure_used is not None and closure_reserved is not None:
            used = _budget_mapping(closure_used)
            reserved = _budget_mapping(closure_reserved)
            if any(used[field_name] > reserved[field_name] for field_name in BUDGET_FIELDS):
                issues.append("CLOSURE_USED_EXCEEDS_RESERVED")
        limits = vectors.get("limits_json")
        consumed = vectors.get("consumed_json")
        if limits is not None and consumed is not None:
            limit_map = _budget_mapping(limits)
            consumed_map = _budget_mapping(consumed)
            if any(
                consumed_map[field_name] > limit_map[field_name]
                for field_name in BUDGET_FIELDS
            ):
                issues.append("INVOCATION_CONSUMED_EXCEEDS_LIMITS")
        if (
            conserved_release
            and schema_version == 9
            and invocation_ref is not None
            and spend_used is not None
            and closure_used is not None
            and consumed is not None
        ):
            total = conserved_totals.setdefault(
                invocation_ref, {field_name: 0 for field_name in BUDGET_FIELDS}
            )
            spend_map = _budget_mapping(spend_used)
            closure_map = _budget_mapping(closure_used)
            for field_name in BUDGET_FIELDS:
                total[field_name] += spend_map[field_name] + closure_map[field_name]
            consumed_by_invocation[invocation_ref] = _budget_mapping(consumed)
        if (
            legacy_unproved
            and spend_used is not None
            and any(amount for _, amount in spend_used)
        ):
            issues.append("HISTORICAL_SPEND_USAGE_UNPROVABLE")
        if (
            legacy_unproved
            and closure_used is not None
            and any(amount for _, amount in closure_used)
        ):
            issues.append("HISTORICAL_CLOSURE_USAGE_UNPROVABLE")
        facts.append(
            HistoricalReleasedFact(
                claim_ref,
                closure_ref,
                reservation_ref,
                str(row[6]),
                invocation_ref,
                spend_used,
                closure_used,
                tuple(dict.fromkeys(issues)),
            )
        )
    undercounted = {
        invocation_ref
        for invocation_ref, total in conserved_totals.items()
        if invocation_ref not in consumed_by_invocation
        or any(
            consumed_by_invocation[invocation_ref][field_name] < total[field_name]
            for field_name in BUDGET_FIELDS
        )
    }
    if undercounted:
        facts = [
            replace(
                fact,
                issues=tuple(
                    dict.fromkeys(
                        (*fact.issues, "CONSERVED_USAGE_MISSING_FROM_INVOCATION")
                    )
                ),
            )
            if fact.invocation_ref in undercounted
            and fact.closure_ref is not None
            and CONSERVED_UNSTARTED_CLOSURE_PATTERN.fullmatch(fact.closure_ref)
            is not None
            else fact
            for fact in facts
        ]
    return tuple(facts)


def _audit_private_database(
    private_database: Path,
    *,
    _expected_schema_fingerprints: Mapping[int, Collection[str]] | None,
) -> tuple[
    int,
    str,
    tuple[SchemaObject, ...],
    tuple[str, ...],
    tuple[LegacyTransactionFact, ...],
    tuple[LegacyEnvelopeFact, ...],
    tuple[LegacyRunFact, ...],
    tuple[HistoricalReleasedFact, ...],
    tuple[str, ...],
]:
    try:
        connection = sqlite3.connect(private_database, timeout=5.0, isolation_level=None)
    except sqlite3.Error as exc:
        raise PreOpenAuditError(
            "PRIVATE_SQLITE_OPEN_FAILED", "private workflow database could not be opened"
        ) from exc
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        query_only = connection.execute("PRAGMA query_only").fetchone()
        if query_only is None or query_only[0] != 1:
            raise PreOpenAuditError(
                "PRIVATE_QUERY_ONLY_FAILED", "private SQLite connection is not query-only"
            )
        database_rows = connection.execute("PRAGMA database_list").fetchall()
        sqlite_paths = tuple(str(Path(row[2]).resolve(strict=True)) for row in database_rows)
        expected_path = str(private_database.resolve(strict=True))
        if sqlite_paths != (expected_path,):
            raise PreOpenAuditError(
                "PRIVATE_SQL_PATH_MISMATCH",
                "SQLite opened a path outside the canonical private database",
            )
        objects = _schema_inventory(connection)
        fingerprint = _schema_fingerprint(objects)
        table_names = {item.name for item in objects if item.object_type == "table"}
        required_tables = {
            "store_meta",
            "implementation_transactions",
            "implementation_envelopes",
            "verification_runs",
            "claims",
            "budget_reservations",
            "actors",
            "invocations",
        }
        missing = sorted(required_tables - table_names)
        if missing:
            raise PreOpenAuditError(
                "SCHEMA_FINGERPRINT_MISMATCH",
                f"required workflow tables are missing: {', '.join(missing)}",
            )
        version = _read_schema_version(connection)
        fingerprint_authority = (
            AUTHORITATIVE_SCHEMA_FINGERPRINTS
            if _expected_schema_fingerprints is None
            else _expected_schema_fingerprints
        )
        admitted_versions = frozenset(fingerprint_authority)
        blockers: list[str] = []
        if version == 6:
            blockers.append("UPGRADE_BLOCKED_UNVERIFIED_V6")
        elif version not in admitted_versions:
            blockers.append(f"UNSUPPORTED_SCHEMA_VERSION:{version}")
        if version in admitted_versions:
            expected = fingerprint_authority.get(version)
            if expected is None or fingerprint not in set(expected):
                blockers.append(f"SCHEMA_FINGERPRINT_MISMATCH:{version}")
            blockers.extend(_executor_floor_blockers(connection, version))
        # Never issue semantic queries against a schema whose exact authority is
        # absent or mismatched.  Merely having similarly named tables is not an
        # admission signal.
        if blockers:
            return (
                version,
                fingerprint,
                objects,
                sqlite_paths,
                (),
                (),
                (),
                (),
                tuple(blockers),
            )
        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_issues:
            blockers.extend(
                f"FOREIGN_KEY_CHECK:{row[0]}:{row[1]}:{row[2]}:{row[3]}"
                for row in foreign_key_issues
            )
        transactions, envelopes, runs = _open_legacy_facts(connection)
        blockers.extend(
            _legacy_fact_blockers(
                transactions,
                envelopes,
                runs,
                schema_version=version,
            )
        )
        if _expected_schema_fingerprints is None:
            blockers.extend(
                _active_claim_blockers(connection, schema_version=version)
            )
        historical = _historical_released_facts(
            connection, schema_version=version
        )
        for fact in historical:
            blockers.extend(
                f"HISTORICAL_RELEASED:{fact.claim_ref}:{issue}" for issue in fact.issues
            )
        return (
            version,
            fingerprint,
            objects,
            sqlite_paths,
            transactions,
            envelopes,
            runs,
            historical,
            tuple(blockers),
        )
    except PreOpenAuditError:
        raise
    except sqlite3.Error as exc:
        raise PreOpenAuditError(
            "PRIVATE_AUDIT_QUERY_FAILED", "private workflow audit query failed"
        ) from exc
    finally:
        connection.close()


def _empty_report(
    *,
    disposition: AuditDisposition,
    guard: GuardSession,
    manifest: SourceManifest,
    blockers: tuple[str, ...],
) -> AuditReport:
    return AuditReport(
        disposition,
        guard.identity,
        guard.kind,
        manifest,
        None,
        None,
        (),
        (),
        (),
        (),
        (),
        (),
        blockers,
    )


def audit_workflow_store(
    raw_root: Path | str,
    *,
    guard: GuardSession,
    private_parent: Path | str | None = None,
    lease_ttl_seconds: float = 300.0,
    _hooks: _AuditHooks | None = None,
    _expected_schema_fingerprints: Mapping[int, Collection[str]] | None = None,
) -> AuditOutcome:
    """Audit one selected workflow root and optionally issue a guarded lease.

    ``NO_STORE`` means the main DB and every known sidecar are exactly absent;
    it does not create the root.  Expected unsafe legacy conditions are returned
    as ``BLOCKED`` reports.  Observation/copy races and malformed source objects
    raise :class:`PreOpenAuditError`; both paths issue no lease.
    """

    if isinstance(lease_ttl_seconds, bool) or lease_ttl_seconds <= 0:
        raise ValueError("lease_ttl_seconds must be positive")
    raw_path = Path(raw_root)
    parent = None if private_parent is None else Path(private_parent)
    hooks = _hooks or _AuditHooks()

    guard.assert_root(raw_path)
    guard.assert_active()
    first = capture_source_manifest(raw_path)
    if hooks.after_first_manifest_pass is not None:
        hooks.after_first_manifest_pass(first)
    guard.assert_active()
    second = capture_source_manifest(raw_path)
    if first != second:
        raise PreOpenAuditError(
            "UNSTABLE_SOURCE_MANIFEST", "the two source manifest passes differ"
        )
    disposition, classification_blockers = _classify_manifest(first)
    if disposition == "BLOCKED":
        return AuditOutcome(
            _empty_report(
                disposition="BLOCKED",
                guard=guard,
                manifest=first,
                blockers=classification_blockers,
            ),
            None,
        )
    if disposition == "NO_STORE":
        report = _empty_report(
            disposition="NO_STORE", guard=guard, manifest=first, blockers=()
        )
        return AuditOutcome(
            report,
            AuditLease(
                report=report,
                raw_root=raw_path,
                guard=guard,
                ttl_seconds=float(lease_ttl_seconds),
            ),
        )

    private_root: Path | None = None
    try:
        guard.assert_active()
        private_root, private_database = _make_private_copy(
            first, private_parent=parent, guard=guard
        )
        if hooks.after_private_copy is not None:
            hooks.after_private_copy(private_database)
        _verify_private_copy(private_database, first)
        guard.assert_active()
        (
            schema_version,
            schema_fingerprint,
            schema_objects,
            sqlite_paths,
            transactions,
            envelopes,
            runs,
            historical,
            semantic_blockers,
        ) = _audit_private_database(
            private_database,
            _expected_schema_fingerprints=_expected_schema_fingerprints,
        )
        if hooks.before_post_audit_manifest is not None:
            hooks.before_post_audit_manifest()
        guard.assert_active()
        after_audit = capture_source_manifest(raw_path)
        if after_audit != first:
            raise PreOpenAuditError(
                "AUDIT_SOURCE_CHANGED", "source changed during private-copy audit"
            )
        disposition = "BLOCKED" if semantic_blockers else "CLEAR"
        report = AuditReport(
            disposition,
            guard.identity,
            guard.kind,
            first,
            schema_version,
            schema_fingerprint,
            schema_objects,
            sqlite_paths,
            transactions,
            envelopes,
            runs,
            historical,
            semantic_blockers,
        )
    finally:
        if private_root is not None:
            shutil.rmtree(private_root)

    lease = None
    if report.is_admitted:
        lease = AuditLease(
            report=report,
            raw_root=raw_path,
            guard=guard,
            ttl_seconds=float(lease_ttl_seconds),
        )
    return AuditOutcome(report, lease)
