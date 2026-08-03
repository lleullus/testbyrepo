#!/usr/bin/env python3
"""Fail-closed executable observation for sealed PROCESS requests.

The public projection deliberately excludes device, inode, and timestamps. Those values are
single-observation stability facts only and must not become cross-time executable identity.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping, TypedDict


_PROJECTION_FIELDS = frozenset(
    {
        "canonicalPath",
        "contentSha256",
        "byteCount",
        "executableMode",
        "ownerUid",
        "ownerGid",
    }
)
_SHA256_PATTERN = re.compile(r"[a-f0-9]{64}")
_READABLE_BITS = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
_EXECUTABLE_BITS = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
_STREAM_CHUNK_BYTES = 1024 * 1024


class ExecutableIdentityProjection(TypedDict):
    canonicalPath: str
    contentSha256: str
    byteCount: int
    executableMode: int
    ownerUid: int
    ownerGid: int


class ExecutableIdentityError(RuntimeError):
    def __init__(self, code: str, message: str, *, bytes_hashed: int = 0) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.bytes_hashed = bytes_hashed


def _strict_canonical_path(value: Path | str) -> str:
    if not isinstance(value, (Path, str)):
        raise ExecutableIdentityError(
            "EXECUTABLE_PATH_INVALID", "executable path must be a string or Path"
        )
    raw = str(value)
    if not raw or "\x00" in raw:
        raise ExecutableIdentityError(
            "EXECUTABLE_PATH_INVALID", "executable path is empty or contains NUL"
        )
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_PATH_INVALID", "executable path must be valid UTF-8"
        ) from exc
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise ExecutableIdentityError(
            "EXECUTABLE_PATH_INVALID", "executable path must be absolute"
        )
    try:
        canonical = str(candidate.resolve(strict=True))
    except (OSError, RuntimeError) as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_UNAVAILABLE", f"cannot resolve executable path: {exc}"
        ) from exc
    if canonical != raw:
        raise ExecutableIdentityError(
            "EXECUTABLE_PATH_INVALID",
            "executable path must already be canonical and cannot traverse symlinks",
        )
    return canonical


def _projection_path(value: Any, locator: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", f"{locator} must be a canonical absolute path"
        )
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", f"{locator} must be valid UTF-8"
        ) from exc
    if not value.startswith("/") or value.startswith("//"):
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", f"{locator} must be a canonical absolute path"
        )
    segments = value.split("/")[1:]
    if not segments or any(segment in {"", ".", ".."} for segment in segments):
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", f"{locator} must be a canonical absolute path"
        )
    return value


def _metadata_tuple(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_gid,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _require_regular_readable_executable(metadata: os.stat_result, canonical_path: str) -> None:
    mode = metadata.st_mode
    if not stat.S_ISREG(mode):
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_REGULAR", f"executable is not a regular file: {canonical_path}"
        )
    if not mode & _READABLE_BITS:
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_READABLE", f"executable has no readable mode: {canonical_path}"
        )
    if not mode & _EXECUTABLE_BITS:
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_EXECUTABLE", f"executable has no executable mode: {canonical_path}"
        )


def _require_path_access(canonical_path: str) -> None:
    try:
        readable = os.access(
            canonical_path,
            os.R_OK,
            effective_ids=True,
            follow_symlinks=False,
        )
        executable = os.access(
            canonical_path,
            os.X_OK,
            effective_ids=True,
            follow_symlinks=False,
        )
    except (NotImplementedError, TypeError):
        readable = os.access(canonical_path, os.R_OK)
        executable = os.access(canonical_path, os.X_OK)
    if not readable:
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_READABLE", f"executable is not readable: {canonical_path}"
        )
    if not executable:
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_EXECUTABLE", f"executable is not executable: {canonical_path}"
        )


def _path_stat(canonical_path: str, *, phase: str) -> os.stat_result:
    try:
        return os.stat(canonical_path, follow_symlinks=False)
    except PermissionError as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_READABLE", f"cannot stat executable during {phase}: {exc}"
        ) from exc
    except OSError as exc:
        code = "EXECUTABLE_UNAVAILABLE" if phase == "pre-open" else "EXECUTABLE_IDENTITY_UNSTABLE"
        raise ExecutableIdentityError(
            code, f"cannot stat executable during {phase}: {exc}"
        ) from exc


def _open_readonly(canonical_path: str) -> int:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    if not isinstance(no_follow, int) or no_follow == 0:
        raise ExecutableIdentityError(
            "EXECUTABLE_IDENTITY_UNSUPPORTED",
            "platform cannot provide O_NOFOLLOW executable observation",
        )
    flags = os.O_RDONLY
    flags |= no_follow
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_BINARY", 0)
    try:
        descriptor = os.open(canonical_path, flags)
    except PermissionError as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_NOT_READABLE", f"cannot open executable for hashing: {exc}"
        ) from exc
    except OSError as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_IDENTITY_UNSTABLE",
            f"executable changed between path stat and descriptor open: {exc}",
        ) from exc
    if not hasattr(os, "O_CLOEXEC"):
        try:
            os.set_inheritable(descriptor, False)
        except OSError as exc:
            os.close(descriptor)
            raise ExecutableIdentityError(
                "EXECUTABLE_IDENTITY_UNSTABLE",
                f"cannot make executable descriptor close-on-exec: {exc}",
            ) from exc
    return descriptor


def _fd_stat(descriptor: int, *, phase: str) -> os.stat_result:
    try:
        return os.fstat(descriptor)
    except OSError as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_IDENTITY_UNSTABLE",
            f"cannot stat executable descriptor during {phase}: {exc}",
        ) from exc


def _stream_digest(descriptor: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    try:
        while True:
            chunk = os.read(descriptor, _STREAM_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
    except OSError as exc:
        raise ExecutableIdentityError(
            "EXECUTABLE_IDENTITY_UNSTABLE",
            f"cannot hash executable: {exc}",
            bytes_hashed=byte_count,
        ) from exc
    return digest.hexdigest(), byte_count


def observe_executable_identity(path: Path | str) -> ExecutableIdentityProjection:
    """Observe one stable executable without accepting any caller-authored identity fields."""
    canonical_path = _strict_canonical_path(path)
    path_before = _path_stat(canonical_path, phase="pre-open")
    _require_regular_readable_executable(path_before, canonical_path)
    _require_path_access(canonical_path)

    descriptor = _open_readonly(canonical_path)
    byte_count = 0
    try:
        descriptor_before = _fd_stat(descriptor, phase="pre-read")
        _require_regular_readable_executable(descriptor_before, canonical_path)
        content_sha256, byte_count = _stream_digest(descriptor)
        descriptor_after = _fd_stat(descriptor, phase="post-read")
        _require_regular_readable_executable(descriptor_after, canonical_path)
        path_after = _path_stat(canonical_path, phase="post-read")
        _require_regular_readable_executable(path_after, canonical_path)
        observations = (
            _metadata_tuple(path_before),
            _metadata_tuple(descriptor_before),
            _metadata_tuple(descriptor_after),
            _metadata_tuple(path_after),
        )
        if len(set(observations)) != 1:
            raise ExecutableIdentityError(
                "EXECUTABLE_IDENTITY_UNSTABLE",
                "pre/post path and descriptor metadata differ during executable hashing",
                bytes_hashed=byte_count,
            )
        observed_size = observations[0][5]
        if byte_count != observed_size:
            raise ExecutableIdentityError(
                "EXECUTABLE_IDENTITY_UNSTABLE",
                "streamed executable byte count differs from stable stat size",
                bytes_hashed=byte_count,
            )
        _require_path_access(canonical_path)
        projection: ExecutableIdentityProjection = {
            "canonicalPath": canonical_path,
            "contentSha256": content_sha256,
            "byteCount": byte_count,
            "executableMode": stat.S_IMODE(descriptor_after.st_mode),
            "ownerUid": descriptor_after.st_uid,
            "ownerGid": descriptor_after.st_gid,
        }
        return validate_executable_identity(
            projection, expected_canonical_path=canonical_path
        )
    except ExecutableIdentityError as exc:
        if exc.bytes_hashed == 0 and byte_count:
            exc.bytes_hashed = byte_count
        raise
    finally:
        os.close(descriptor)


def validate_executable_identity(
    value: Any,
    expected_canonical_path: Path | str | None = None,
) -> ExecutableIdentityProjection:
    """Validate an already tool-observed or stored public identity projection."""
    if not isinstance(value, Mapping) or set(value) != _PROJECTION_FIELDS:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", "executable identity fields are invalid"
        )
    canonical_path = _projection_path(value["canonicalPath"], "canonicalPath")
    digest = value["contentSha256"]
    if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", "contentSha256 must be a lowercase SHA-256"
        )

    integers: dict[str, int] = {}
    for field in ("byteCount", "executableMode", "ownerUid", "ownerGid"):
        item = value[field]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise ExecutableIdentityError(
                "INVALID_EXECUTABLE_IDENTITY", f"{field} must be a nonnegative integer"
            )
        integers[field] = item
    if integers["executableMode"] > 0o7777:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", "executableMode is outside stat.S_IMODE range"
        )
    if not integers["executableMode"] & _READABLE_BITS:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", "executableMode has no readable bit"
        )
    if not integers["executableMode"] & _EXECUTABLE_BITS:
        raise ExecutableIdentityError(
            "INVALID_EXECUTABLE_IDENTITY", "executableMode has no executable bit"
        )

    if expected_canonical_path is not None:
        expected_raw = str(expected_canonical_path)
        expected = _projection_path(expected_raw, "expected_canonical_path")
        if canonical_path != expected:
            raise ExecutableIdentityError(
                "EXECUTABLE_PATH_MISMATCH",
                "identity canonicalPath differs from the expected executable path",
            )
    return {
        "canonicalPath": canonical_path,
        "contentSha256": digest,
        "byteCount": integers["byteCount"],
        "executableMode": integers["executableMode"],
        "ownerUid": integers["ownerUid"],
        "ownerGid": integers["ownerGid"],
    }


def executable_identities_equal(expected: Any, observed: Any) -> bool:
    """Strictly validate and compare all public executable identity fields."""
    return validate_executable_identity(expected) == validate_executable_identity(observed)
