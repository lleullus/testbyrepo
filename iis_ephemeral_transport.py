"""Bounded local transport for IIS handoff and verification artifacts.

This module owns only the five negotiated local artifact slots beneath
``~/.iis``.  It deliberately has no discovery, history, recovery, or generic
JSON-storage interface.  Every public read validates the exact current Ticket
binding before returning an artifact-specific view.
"""

from __future__ import annotations

import copy
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ROUTE_SCHEMA = "iis-route-navigation/v1"
PLAN_SCHEMA = "iis-verification-plan/v1"
APPROVAL_SCHEMA = "iis-user-approval/v1"
FINAL_SCHEMA = "iis-final-outcome/v1"
REMEDIATION_SCHEMA = "iis-remediation-current/v1"

_DIRECTORY_MODE = 0o700
_FILE_MODE = 0o600
_MAX_ARTIFACT_BYTES = 1_000_000
_MAX_DEPTH = 32
_MAX_ARRAY_ITEMS = 256
_MAX_OBJECT_KEYS = 128
_MAX_TEXT_LENGTH = 4_096
_MAX_ROUTES = 64
_MAX_ANCHORS = 64
_MAX_EVIDENCE_RECORDS = 256
_MAX_AC_ROWS = 256
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9._:@-]{0,127}$")
_NONCE = re.compile(r"^vx-[a-f0-9]{32}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_EVIDENCE_TYPES = frozenset(
    {
        "runner-raw",
        "readiness-fact",
        "static-support",
        "source-conflict/canonical-authority",
        "source-conflict/product-static",
        "direct-evidence",
    }
)
_VERDICTS = frozenset({"SATISFIED", "NOT_SATISFIED", "UNDETERMINED"})
_SAFE_ABANDONMENT_STATES = frozenset(
    {"MUTATION_NOT_RUN", "MUTATION_STATE_RECONCILED"}
)
_DEPENDENCY_KINDS = frozenset(
    {"canonical-source", "product-source-anchor", "runtime-dependency"}
)
_VERIFICATION_THREAD_LOCK = threading.RLock()
_VERIFICATION_LOCK_STATE = threading.local()


class TransportError(RuntimeError):
    """A local IIS transport artifact is absent, unsafe, stale, or malformed."""


class ArtifactNotFound(TransportError):
    """The one exact artifact slot requested by a caller is absent."""


__all__ = (
    "ArtifactNotFound",
    "TransportError",
    "abandon_remediation",
    "append_remediation_cycle",
    "begin_remediation",
    "cleanup_expired_route_navigation",
    "mark_route_navigation_terminal",
    "publish_final_outcome",
    "publish_plan_envelope",
    "publish_route_navigation",
    "publish_user_approval",
    "render_approval_disclosure",
    "read_final_outcome",
    "read_lead_producer_provenance_view",
    "read_plan_envelope",
    "read_primary_navigation_view",
    "read_remediation_current",
    "read_user_approval",
    "record_remediation_mutation",
    "record_remediation_reconciliation",
    "ticket_key",
)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TransportError(f"artifact is not canonical JSON: {exc}") from exc


def _json_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _json_object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TransportError(f"artifact JSON contains a duplicate key: {key}")
        result[key] = value
    return result


def _file_digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise TransportError(f"cannot read {path}: {exc}") from exc


def _require_keys(
    value: dict[str, Any],
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    allowed = required | (optional or set())
    missing = required - value.keys()
    extra = value.keys() - allowed
    if missing:
        raise TransportError(f"{label} is missing fields: {sorted(missing)}")
    if extra:
        raise TransportError(f"{label} has unsupported fields: {sorted(extra)}")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TransportError(f"{label} must be an object")
    return value


def _array(value: Any, label: str, *, maximum: int = _MAX_ARRAY_ITEMS) -> list[Any]:
    if not isinstance(value, list):
        raise TransportError(f"{label} must be an array")
    if len(value) > maximum:
        raise TransportError(f"{label} exceeds its bounded item count")
    return value


def _text(value: Any, label: str, *, maximum: int = _MAX_TEXT_LENGTH) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TransportError(f"{label} must be a non-empty trimmed string")
    if len(value) > maximum or "\x00" in value or "\n" in value or "\r" in value:
        raise TransportError(f"{label} is not bounded single-line text")
    return value


def _identifier(value: Any, label: str) -> str:
    result = _text(value, label, maximum=128)
    if not _IDENTIFIER.fullmatch(result):
        raise TransportError(f"{label} must be a bounded stable identifier")
    return result


def _sha256(value: Any, label: str) -> str:
    result = _text(value, label, maximum=64)
    if not _SHA256.fullmatch(result):
        raise TransportError(f"{label} must be a lowercase SHA-256 digest")
    return result


def _timestamp(value: Any, label: str) -> dt.datetime:
    result = _text(value, label, maximum=20)
    if not _TIMESTAMP.fullmatch(result):
        raise TransportError(f"{label} must be an RFC3339 UTC timestamp")
    try:
        return dt.datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc
        )
    except ValueError as exc:
        raise TransportError(f"{label} is not a valid UTC timestamp") from exc


def _format_timestamp(value: dt.datetime | None = None) -> str:
    current = value or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        raise TransportError("timestamps must be timezone-aware")
    return current.astimezone(dt.timezone.utc).replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _string_ids(
    value: Any,
    label: str,
    *,
    allow_empty: bool = False,
    maximum: int = _MAX_ARRAY_ITEMS,
) -> list[str]:
    values = [_identifier(item, f"{label} item") for item in _array(value, label, maximum=maximum)]
    if not allow_empty and not values:
        raise TransportError(f"{label} must not be empty")
    if len(values) != len(set(values)):
        raise TransportError(f"{label} must not contain duplicates")
    if values != sorted(values):
        raise TransportError(f"{label} must be sorted")
    return values


def _bounded_json(
    value: Any,
    label: str,
    depth: int = 0,
    *,
    maximum_text_length: int = _MAX_TEXT_LENGTH,
) -> None:
    if depth > _MAX_DEPTH:
        raise TransportError(f"{label} exceeds bounded JSON nesting")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > 2**53:
            raise TransportError(f"{label} integer is outside the bounded range")
        return
    if isinstance(value, str):
        if len(value) > maximum_text_length or "\x00" in value:
            raise TransportError(f"{label} contains unbounded text")
        return
    if isinstance(value, list):
        if len(value) > _MAX_ARRAY_ITEMS:
            raise TransportError(f"{label} exceeds bounded array size")
        for index, item in enumerate(value):
            _bounded_json(
                item,
                f"{label}[{index}]",
                depth + 1,
                maximum_text_length=maximum_text_length,
            )
        return
    if isinstance(value, dict):
        if len(value) > _MAX_OBJECT_KEYS:
            raise TransportError(f"{label} exceeds bounded object size")
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 128:
                raise TransportError(f"{label} has an invalid JSON key")
            _bounded_json(
                item,
                f"{label}.{key}",
                depth + 1,
                maximum_text_length=maximum_text_length,
            )
        return
    raise TransportError(f"{label} contains an unsupported JSON value")


def _lstat(path: Path, label: str) -> os.stat_result:
    try:
        return path.lstat()
    except FileNotFoundError as exc:
        raise ArtifactNotFound(f"{label} is absent: {path}") from exc
    except OSError as exc:
        raise TransportError(f"cannot inspect {label} {path}: {exc}") from exc


def _canonical_directory(
    path: Path,
    label: str,
    *,
    private: bool,
) -> Path:
    if not path.is_absolute():
        raise TransportError(f"{label} must be an absolute directory")
    details = _lstat(path, label)
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise TransportError(f"{label} must be a non-symlink directory: {path}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise TransportError(f"cannot resolve {label} {path}: {exc}") from exc
    if resolved != path:
        raise TransportError(f"{label} must be canonical: {path}")
    if private:
        if details.st_uid != os.geteuid():
            raise TransportError(f"{label} is not owned by the current user: {path}")
        if stat.S_IMODE(details.st_mode) != _DIRECTORY_MODE:
            raise TransportError(f"{label} must have mode 0700: {path}")
    return path


def _ensure_private_directory(path: Path, label: str, *, create: bool) -> Path:
    try:
        return _canonical_directory(path, label, private=True)
    except ArtifactNotFound:
        if not create:
            raise
    parent = path.parent
    _canonical_directory(parent, f"{label} parent", private=False)
    parent_details = _lstat(parent, f"{label} parent")
    if parent_details.st_uid != os.geteuid():
        raise TransportError(f"{label} parent is not owned by the current user: {parent}")
    if parent_details.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise TransportError(f"{label} parent has unsafe group/other write permission: {parent}")
    try:
        path.mkdir(mode=_DIRECTORY_MODE)
    except FileExistsError:
        return _canonical_directory(path, label, private=True)
    except OSError as exc:
        raise TransportError(f"cannot create {label} {path}: {exc}") from exc
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise TransportError(f"cannot open new {label} {path}: {exc}") from exc
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISDIR(details.st_mode) or details.st_uid != os.geteuid():
            raise TransportError(f"new {label} is not a current-user directory: {path}")
        os.fchmod(descriptor, _DIRECTORY_MODE)
    except OSError as exc:
        raise TransportError(f"cannot set mode on new {label} {path}: {exc}") from exc
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    return _canonical_directory(path, label, private=True)


def _state_root(*, create: bool) -> Path:
    return _ensure_private_directory(Path.home() / ".iis", "IIS state root", create=create)


def _route_directory(*, create: bool) -> Path:
    root = _state_root(create=create)
    return _ensure_private_directory(
        root / "route-navigation", "route navigation directory", create=create
    )


def _route_file(key: str, *, create: bool) -> Path:
    return _route_directory(create=create) / f"{key}.json"


@contextmanager
def _route_navigation_write_lock(*, create: bool) -> Iterator[Path]:
    """Serialize one sidecar's replacement, terminal mark, and cleanup in-memory."""

    directory = _route_directory(create=create)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError as exc:
        raise TransportError(f"cannot open route navigation directory {directory}: {exc}") from exc
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield directory
    except OSError as exc:
        raise TransportError(f"cannot lock route navigation directory {directory}: {exc}") from exc
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(descriptor)
        except OSError:
            pass


def _verification_ticket_directory(key: str, *, create: bool) -> Path:
    root = _state_root(create=create)
    verification = _ensure_private_directory(
        root / "verification", "verification directory", create=create
    )
    return _ensure_private_directory(
        verification / key, "Ticket verification directory", create=create
    )


def _verification_file(key: str, name: str, *, create: bool) -> Path:
    return _verification_ticket_directory(key, create=create) / name


@contextmanager
def _verification_write_lock(key: str, *, create: bool) -> Iterator[Path]:
    """Serialize one Ticket's short verification artifact transitions."""

    with _VERIFICATION_THREAD_LOCK:
        held = getattr(_VERIFICATION_LOCK_STATE, "directories", None)
        if held is None:
            held = {}
            _VERIFICATION_LOCK_STATE.directories = held
        if key in held:
            yield held[key]
            return
        directory = _verification_ticket_directory(key, create=create)
        flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(directory, flags)
        except OSError as exc:
            raise TransportError(
                f"cannot open Ticket verification directory {directory}: {exc}"
            ) from exc
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
        except OSError as exc:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise TransportError(
                f"cannot lock Ticket verification directory {directory}: {exc}"
            ) from exc
        held[key] = directory
        try:
            yield directory
        finally:
            held.pop(key, None)
            if not held:
                delattr(_VERIFICATION_LOCK_STATE, "directories")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(descriptor)
            except OSError:
                pass


def _private_file(path: Path, label: str) -> os.stat_result:
    details = _lstat(path, label)
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
        raise TransportError(f"{label} must be a non-symlink regular file: {path}")
    if details.st_uid != os.geteuid():
        raise TransportError(f"{label} is not owned by the current user: {path}")
    if stat.S_IMODE(details.st_mode) != _FILE_MODE:
        raise TransportError(f"{label} must have mode 0600: {path}")
    if details.st_nlink != 1:
        raise TransportError(f"{label} must not have hard links: {path}")
    return details


def _read_artifact(path: Path, label: str) -> dict[str, Any]:
    before = _private_file(path, label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise TransportError(f"cannot open {label} {path}: {exc}") from exc
    try:
        details = os.fstat(descriptor)
        if (
            details.st_dev != before.st_dev
            or details.st_ino != before.st_ino
            or not stat.S_ISREG(details.st_mode)
            or details.st_uid != os.geteuid()
            or stat.S_IMODE(details.st_mode) != _FILE_MODE
            or details.st_nlink != 1
        ):
            raise TransportError(f"{label} changed while being opened: {path}")
        if details.st_size > _MAX_ARTIFACT_BYTES:
            raise TransportError(f"{label} exceeds its bounded byte size")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(_MAX_ARTIFACT_BYTES + 1)
    except OSError as exc:
        raise TransportError(f"cannot read {label} {path}: {exc}") from exc
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    if len(payload) > _MAX_ARTIFACT_BYTES:
        raise TransportError(f"{label} exceeds its bounded byte size")
    try:
        decoded = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_json_object_without_duplicates
        )
    except (TransportError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransportError(f"{label} is not valid JSON: {exc}") from exc
    result = _object(decoded, label)
    _bounded_json(
        result,
        label,
        maximum_text_length=(
            _MAX_ARTIFACT_BYTES if label == "plan envelope" else _MAX_TEXT_LENGTH
        ),
    )
    return result


def _write_artifact(path: Path, value: dict[str, Any], label: str) -> None:
    _bounded_json(
        value,
        label,
        maximum_text_length=(
            _MAX_ARTIFACT_BYTES if label == "plan envelope" else _MAX_TEXT_LENGTH
        ),
    )
    parent = _canonical_directory(path.parent, f"{label} directory", private=True)
    try:
        existing = path.lstat()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise TransportError(f"cannot inspect {label} destination {path}: {exc}") from exc
    if existing is not None:
        _private_file(path, f"{label} destination")
    rendered = _canonical_json_bytes(value) + b"\n"
    if len(rendered) > _MAX_ARTIFACT_BYTES:
        raise TransportError(f"{label} exceeds its bounded byte size")
    descriptor = -1
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=parent
        )
        os.fchmod(descriptor, _FILE_MODE)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as exc:
        raise TransportError(f"cannot atomically publish {label} {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
    _private_file(path, label)


def _remove_artifact(path: Path, label: str) -> None:
    _private_file(path, label)
    try:
        os.unlink(path)
    except OSError as exc:
        raise TransportError(f"cannot remove {label} {path}: {exc}") from exc


def _canonical_project_and_ticket(
    project_root: str | Path,
    ticket_path: str | Path,
) -> tuple[Path, Path]:
    root = _canonical_directory(Path(project_root).expanduser(), "Project Root", private=False)
    ticket = Path(ticket_path).expanduser()
    if not ticket.is_absolute():
        raise TransportError("Ticket path must be absolute")
    details = _lstat(ticket, "Ticket")
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
        raise TransportError(f"Ticket must be a non-symlink regular file: {ticket}")
    try:
        resolved = ticket.resolve(strict=True)
    except OSError as exc:
        raise TransportError(f"cannot resolve Ticket {ticket}: {exc}") from exc
    if resolved != ticket:
        raise TransportError(f"Ticket path must be canonical: {ticket}")
    try:
        ticket.relative_to(root)
    except ValueError as exc:
        raise TransportError("Ticket must be inside the exact Project Root") from exc
    return root, ticket


def _binding(project_root: str | Path, ticket_path: str | Path) -> dict[str, str]:
    root, ticket = _canonical_project_and_ticket(project_root, ticket_path)
    return {
        "project_root": str(root),
        "ticket_path": str(ticket),
        "ticket_sha256": _file_digest(ticket),
    }


def ticket_key(project_root: str | Path, ticket_path: str | Path) -> str:
    """Return the one deterministic local slot key for this canonical Ticket."""

    root, ticket = _canonical_project_and_ticket(project_root, ticket_path)
    return hashlib.sha256(f"{root}\0{ticket}".encode("utf-8")).hexdigest()


def _validate_binding(
    value: Any,
    expected: dict[str, str],
    *,
    require_current_digest: bool = True,
) -> dict[str, str]:
    binding = _object(value, "binding")
    _require_keys(binding, "binding", {"project_root", "ticket_path", "ticket_sha256"})
    project = _text(binding["project_root"], "binding.project_root")
    ticket = _text(binding["ticket_path"], "binding.ticket_path")
    digest = _sha256(binding["ticket_sha256"], "binding.ticket_sha256")
    if project != expected["project_root"] or ticket != expected["ticket_path"]:
        raise TransportError("artifact Project Root or Ticket binding does not match")
    if require_current_digest and digest != expected["ticket_sha256"]:
        raise TransportError("artifact Ticket binding is stale")
    return {"project_root": project, "ticket_path": ticket, "ticket_sha256": digest}


def _canonical_source_path(project_root: Path, value: Any, label: str) -> Path:
    relative = _text(value, label, maximum=512)
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise TransportError(f"{label} must be a canonical Project-Root-relative path")
    try:
        resolved = (project_root / candidate).resolve(strict=True)
    except OSError as exc:
        raise TransportError(f"cannot resolve {label}: {exc}") from exc
    try:
        relative_resolved = resolved.relative_to(project_root).as_posix()
    except ValueError as exc:
        raise TransportError(f"{label} escapes the Project Root") from exc
    if relative_resolved != relative:
        raise TransportError(f"{label} must be canonical")
    details = _lstat(resolved, label)
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
        raise TransportError(f"{label} must name a non-symlink regular file")
    return resolved


def _validate_anchors(
    value: Any,
    project_root: Path,
    label: str,
    *,
    require_current_digest: bool,
) -> list[dict[str, str]]:
    anchors: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(_array(value, label, maximum=_MAX_ANCHORS)):
        item = _object(raw, f"{label}[{index}]")
        _require_keys(item, f"{label}[{index}]", {"path", "sha256"})
        path_text = _text(item["path"], f"{label}[{index}].path", maximum=512)
        digest = _sha256(item["sha256"], f"{label}[{index}].sha256")
        if path_text in seen:
            raise TransportError(f"{label} contains duplicate paths")
        seen.add(path_text)
        if require_current_digest:
            source = _canonical_source_path(project_root, path_text, f"{label}[{index}].path")
            if _file_digest(source) != digest:
                raise TransportError(f"{label}[{index}] is stale")
        anchors.append({"path": path_text, "sha256": digest})
    if not anchors:
        raise TransportError(f"{label} must not be empty")
    if anchors != sorted(anchors, key=lambda item: item["path"]):
        raise TransportError(f"{label} must be sorted by path")
    return anchors


def _redacted_identifier(value: Any, label: str) -> str:
    result = _identifier(value, label)
    lowered = result.lower()
    if any(
        token in lowered
        for token in (
            "secret",
            "password",
            "credential",
            "token",
            "private",
            "endpoint",
            "hostname",
            "environment",
            "readiness",
            "evidence",
            "verdict",
            "satisfied",
            "scenario",
            "acceptance",
        )
    ):
        raise TransportError(f"{label} must be a redacted identifier")
    return result


def _validate_navigation_routes(
    value: Any, project_root: Path, *, require_current_digest: bool
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(_array(value, "navigation routes", maximum=_MAX_ROUTES)):
        route = _object(raw, f"navigation routes[{index}]")
        _require_keys(
            route,
            f"navigation routes[{index}]",
            {
                "route_id",
                "startup_or_execution_path",
                "trigger_boundary",
                "source_integration_anchors",
                "outcome_readback",
            },
        )
        route_id = _identifier(route["route_id"], f"navigation routes[{index}].route_id")
        if route_id in seen:
            raise TransportError("navigation routes contain duplicate route IDs")
        seen.add(route_id)
        routes.append(
            {
                "route_id": route_id,
                "startup_or_execution_path": _text(
                    route["startup_or_execution_path"],
                    f"navigation routes[{index}].startup_or_execution_path",
                ),
                "trigger_boundary": _text(
                    route["trigger_boundary"], f"navigation routes[{index}].trigger_boundary"
                ),
                "source_integration_anchors": _validate_anchors(
                    route["source_integration_anchors"],
                    project_root,
                    f"navigation routes[{index}].source_integration_anchors",
                    require_current_digest=require_current_digest,
                ),
                "outcome_readback": _text(
                    route["outcome_readback"], f"navigation routes[{index}].outcome_readback"
                ),
            }
        )
    if not routes:
        raise TransportError("navigation routes must not be empty")
    if routes != sorted(routes, key=lambda item: item["route_id"]):
        raise TransportError("navigation routes must be sorted by route_id")
    return routes


def _validate_provenance_routes(value: Any) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(_array(value, "producer provenance routes", maximum=_MAX_ROUTES)):
        route = _object(raw, f"producer provenance routes[{index}]")
        observed_class = _text(
            route.get("observed_class"),
            f"producer provenance routes[{index}].observed_class",
            maximum=64,
        )
        required = {
            "route_id",
            "execution_surface",
            "trigger_boundary",
            "outcome_readback",
            "observed_class",
        }
        if observed_class == "BLOCKED_WHEN_RECORDED":
            required.update({"redacted_condition", "next_owner"})
        elif observed_class != "GROSS_NOMINAL_BOUNDARY_REACHED":
            raise TransportError("producer provenance has an unsupported observed class")
        _require_keys(route, f"producer provenance routes[{index}]", required)
        route_id = _redacted_identifier(
            route["route_id"], f"producer provenance routes[{index}].route_id"
        )
        if route_id in seen:
            raise TransportError("producer provenance routes contain duplicate route IDs")
        seen.add(route_id)
        normalized: dict[str, Any] = {
            "route_id": route_id,
            "execution_surface": _redacted_identifier(
                route["execution_surface"],
                f"producer provenance routes[{index}].execution_surface",
            ),
            "trigger_boundary": _redacted_identifier(
                route["trigger_boundary"],
                f"producer provenance routes[{index}].trigger_boundary",
            ),
            "outcome_readback": _redacted_identifier(
                route["outcome_readback"],
                f"producer provenance routes[{index}].outcome_readback",
            ),
            "observed_class": observed_class,
        }
        if observed_class == "BLOCKED_WHEN_RECORDED":
            normalized["redacted_condition"] = _redacted_identifier(
                route["redacted_condition"],
                f"producer provenance routes[{index}].redacted_condition",
            )
            normalized["next_owner"] = _redacted_identifier(
                route["next_owner"],
                f"producer provenance routes[{index}].next_owner",
            )
        routes.append(normalized)
    if not routes:
        raise TransportError("producer provenance routes must not be empty")
    if routes != sorted(routes, key=lambda item: item["route_id"]):
        raise TransportError("producer provenance routes must be sorted by route_id")
    return routes


def _validate_retention(value: Any) -> dict[str, Any]:
    retention = _object(value, "retention")
    _require_keys(
        retention,
        "retention",
        {"created_at", "cleanup_after", "terminal_published_at"},
    )
    created = _timestamp(retention["created_at"], "retention.created_at")
    cleanup_after = _timestamp(retention["cleanup_after"], "retention.cleanup_after")
    terminal = retention["terminal_published_at"]
    if terminal is not None:
        terminal_time = _timestamp(terminal, "retention.terminal_published_at")
        if terminal_time < created:
            raise TransportError("terminal route publication precedes creation")
        if cleanup_after < terminal_time + dt.timedelta(days=7):
            raise TransportError("terminal route retention must include a seven-day grace")
        if cleanup_after > max(created + dt.timedelta(days=30), terminal_time + dt.timedelta(days=7)):
            raise TransportError("terminal route retention exceeds its bounded grace")
    elif cleanup_after > created + dt.timedelta(days=30):
        raise TransportError("orphan route retention exceeds its thirty-day ceiling")
    if cleanup_after < created:
        raise TransportError("route cleanup eligibility precedes creation")
    return {
        "created_at": retention["created_at"],
        "cleanup_after": retention["cleanup_after"],
        "terminal_published_at": terminal,
    }


def _validate_route_sidecar(
    value: Any,
    expected_binding: dict[str, str],
    *,
    require_current_ticket: bool,
    require_current_anchors: bool,
) -> dict[str, Any]:
    sidecar = _object(value, "route navigation")
    _require_keys(
        sidecar,
        "route navigation",
        {
            "schema",
            "binding",
            "producer_run_nonce",
            "navigation_view",
            "producer_provenance_view",
            "retention",
        },
    )
    if sidecar["schema"] != ROUTE_SCHEMA:
        raise TransportError("route navigation schema is invalid")
    binding = _validate_binding(
        sidecar["binding"], expected_binding, require_current_digest=require_current_ticket
    )
    nonce = _text(sidecar["producer_run_nonce"], "producer_run_nonce", maximum=64)
    if not re.fullmatch(r"^pr-[a-f0-9]{32}$", nonce):
        raise TransportError("producer_run_nonce is invalid")
    project_root = Path(binding["project_root"])
    navigation = _object(sidecar["navigation_view"], "navigation_view")
    _require_keys(navigation, "navigation_view", {"routes"})
    routes = _validate_navigation_routes(
        navigation["routes"], project_root, require_current_digest=require_current_anchors
    )
    provenance = _object(sidecar["producer_provenance_view"], "producer_provenance_view")
    _require_keys(provenance, "producer_provenance_view", {"recorded_at", "routes"})
    _timestamp(provenance["recorded_at"], "producer_provenance_view.recorded_at")
    provenance_routes = _validate_provenance_routes(provenance["routes"])
    if [route["route_id"] for route in routes] != [route["route_id"] for route in provenance_routes]:
        raise TransportError("navigation and producer provenance routes do not match")
    return {
        "schema": ROUTE_SCHEMA,
        "binding": binding,
        "producer_run_nonce": nonce,
        "navigation_view": {"routes": routes},
        "producer_provenance_view": {
            "recorded_at": provenance["recorded_at"],
            "routes": provenance_routes,
        },
        "retention": _validate_retention(sidecar["retention"]),
    }


def _read_route_sidecar(
    project_root: str | Path,
    ticket_path: str | Path,
    *,
    require_current_ticket: bool,
    require_current_anchors: bool,
) -> tuple[Path, dict[str, Any], dict[str, str]]:
    binding = _binding(project_root, ticket_path)
    path = _route_file(ticket_key(project_root, ticket_path), create=False)
    sidecar = _validate_route_sidecar(
        _read_artifact(path, "route navigation"),
        binding,
        require_current_ticket=require_current_ticket,
        require_current_anchors=require_current_anchors,
    )
    return path, sidecar, binding


def _read_route_sidecar_at(
    path: Path,
    binding: dict[str, str],
    *,
    require_current_ticket: bool,
    require_current_anchors: bool,
) -> dict[str, Any]:
    return _validate_route_sidecar(
        _read_artifact(path, "route navigation"),
        binding,
        require_current_ticket=require_current_ticket,
        require_current_anchors=require_current_anchors,
    )


def publish_route_navigation(
    project_root: str | Path,
    ticket_path: str | Path,
    navigation_routes: list[dict[str, Any]],
    producer_provenance_routes: list[dict[str, Any]],
    *,
    now: dt.datetime | None = None,
) -> dict[str, str]:
    """Atomically replace the one navigation sidecar for a Ticket."""

    binding = _binding(project_root, ticket_path)
    project = Path(binding["project_root"])
    timestamp = _format_timestamp(now)
    created = _timestamp(timestamp, "route creation timestamp")
    sidecar = {
        "schema": ROUTE_SCHEMA,
        "binding": binding,
        "producer_run_nonce": f"pr-{secrets.token_hex(16)}",
        "navigation_view": {
            "routes": _validate_navigation_routes(
                navigation_routes, project, require_current_digest=True
            )
        },
        "producer_provenance_view": {
            "recorded_at": timestamp,
            "routes": _validate_provenance_routes(producer_provenance_routes),
        },
        "retention": {
            "created_at": timestamp,
            "cleanup_after": _format_timestamp(created + dt.timedelta(days=30)),
            "terminal_published_at": None,
        },
    }
    _validate_route_sidecar(
        sidecar,
        binding,
        require_current_ticket=True,
        require_current_anchors=True,
    )
    key = ticket_key(project_root, ticket_path)
    with _route_navigation_write_lock(create=True) as directory:
        _write_artifact(directory / f"{key}.json", sidecar, "route navigation")
    return {"producer_run_nonce": sidecar["producer_run_nonce"]}


def read_primary_navigation_view(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    """Return only the safe route-navigation projection for Primary Verifier."""

    _path, sidecar, _binding_value = _read_route_sidecar(
        project_root,
        ticket_path,
        require_current_ticket=True,
        require_current_anchors=True,
    )
    return {
        "binding": copy.deepcopy(sidecar["binding"]),
        "routes": copy.deepcopy(sidecar["navigation_view"]["routes"]),
    }


def read_lead_producer_provenance_view(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    """Return only the quarantined producer observation projection for the Lead."""

    _path, sidecar, _binding_value = _read_route_sidecar(
        project_root,
        ticket_path,
        require_current_ticket=True,
        require_current_anchors=True,
    )
    return {
        "binding": copy.deepcopy(sidecar["binding"]),
        "producer_run_nonce": sidecar["producer_run_nonce"],
        "recorded_at": sidecar["producer_provenance_view"]["recorded_at"],
        "routes": copy.deepcopy(sidecar["producer_provenance_view"]["routes"]),
    }


def mark_route_navigation_terminal(
    project_root: str | Path,
    ticket_path: str | Path,
    terminal_published_at: str,
) -> None:
    """Extend an existing sidecar's mechanical cleanup grace after terminal output."""

    terminal = _timestamp(terminal_published_at, "terminal_published_at")
    binding = _binding(project_root, ticket_path)
    key = ticket_key(project_root, ticket_path)
    with _route_navigation_write_lock(create=False) as directory:
        path = directory / f"{key}.json"
        sidecar = _read_route_sidecar_at(
            path,
            binding,
            require_current_ticket=True,
            require_current_anchors=False,
        )
        existing = _timestamp(sidecar["retention"]["cleanup_after"], "retention.cleanup_after")
        cleanup_after = max(existing, terminal + dt.timedelta(days=7))
        sidecar["retention"] = {
            "created_at": sidecar["retention"]["created_at"],
            "cleanup_after": _format_timestamp(cleanup_after),
            "terminal_published_at": terminal_published_at,
        }
        _validate_route_sidecar(
            sidecar,
            binding,
            require_current_ticket=True,
            require_current_anchors=False,
        )
        _write_artifact(path, sidecar, "route navigation")


def cleanup_expired_route_navigation(
    project_root: str | Path,
    ticket_path: str | Path,
    *,
    now: dt.datetime | None = None,
) -> bool:
    """Remove only this sidecar after its mechanical cleanup eligibility time."""

    binding = _binding(project_root, ticket_path)
    key = ticket_key(project_root, ticket_path)
    try:
        with _route_navigation_write_lock(create=False) as directory:
            path = directory / f"{key}.json"
            sidecar = _read_route_sidecar_at(
                path,
                binding,
                require_current_ticket=False,
                require_current_anchors=False,
            )
            if _timestamp(sidecar["retention"]["cleanup_after"], "retention.cleanup_after") > (
                now or dt.datetime.now(dt.timezone.utc)
            ).astimezone(dt.timezone.utc):
                return False
            _remove_artifact(path, "route navigation")
            return True
    except ArtifactNotFound:
        return False


_coverage_gate_module: Any | None = None


def _coverage_gate() -> Any:
    global _coverage_gate_module
    if _coverage_gate_module is not None:
        return _coverage_gate_module
    path = Path(__file__).with_name("verification-lead") / "coverage_gate.py"
    spec = importlib.util.spec_from_file_location("_iis_coverage_gate", path)
    if spec is None or spec.loader is None:
        raise TransportError("coverage gate module is unavailable")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (ImportError, OSError) as exc:
        raise TransportError(f"cannot load coverage gate module: {exc}") from exc
    _coverage_gate_module = module
    return module


def _validate_gate_package(
    envelope: Any,
    receipt: Any,
    approval: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    gate = _coverage_gate()
    envelope_value = _object(envelope, "coverage_gate_envelope")
    receipt_value = _object(receipt, "accepted_challenger_receipt")
    approval_value = _object(approval, "gate_approval")
    _bounded_json(
        envelope_value,
        "coverage_gate_envelope",
        maximum_text_length=_MAX_ARTIFACT_BYTES,
    )
    _bounded_json(receipt_value, "accepted_challenger_receipt")
    _bounded_json(approval_value, "gate_approval")
    try:
        gate._validate_envelope(envelope_value)
        gate._validate_receipt(envelope_value, receipt_value)
        expected_approval = gate.approve(envelope_value, receipt_value)
    except Exception as exc:
        raise TransportError(f"coverage gate package is invalid: {exc}") from exc
    if receipt_value.get("effective_result") != "PASS":
        raise TransportError("accepted Challenger receipt must have effective PASS")
    if approval_value != expected_approval:
        raise TransportError("gate approval does not match the accepted gate package")
    if approval_value.get("mode") not in {"TOTAL", "PARTIAL"}:
        raise TransportError("only TOTAL or PARTIAL gate approval may be published")
    fingerprints = _object(envelope_value.get("fingerprints"), "coverage gate fingerprints")
    if (
        approval_value.get("challenge_fp") != fingerprints.get("challenge_fp")
        or approval_value.get("plan_fp") != fingerprints.get("plan_fp")
        or approval_value.get("attestation_digest") != receipt_value.get("attestation_digest")
        or not isinstance(approval_value.get("approval_id"), str)
    ):
        raise TransportError("gate approval chain is incomplete")
    return envelope_value, receipt_value, approval_value


def _validate_gate_binding(
    envelope: dict[str, Any], binding: dict[str, str]
) -> None:
    canonical = _object(envelope.get("canonical"), "coverage gate canonical package")
    project_root = _text(canonical.get("project_root"), "coverage gate canonical project_root")
    ticket_relative = _text(canonical.get("ticket"), "coverage gate canonical ticket")
    expected_relative = Path(binding["ticket_path"]).relative_to(
        Path(binding["project_root"])
    ).as_posix()
    if project_root != binding["project_root"] or ticket_relative != expected_relative:
        raise TransportError("coverage gate package does not bind the exact Ticket")


def _verification_path(
    project_root: str | Path,
    ticket_path: str | Path,
    name: str,
    *,
    create: bool,
) -> Path:
    return _verification_file(
        ticket_key(project_root, ticket_path), name, create=create
    )


def _plan_path(
    project_root: str | Path,
    ticket_path: str | Path,
    *,
    create: bool,
) -> Path:
    return _verification_path(
        project_root,
        ticket_path,
        "plan-envelope.json",
        create=create,
    )


def _approval_path(
    project_root: str | Path,
    ticket_path: str | Path,
    *,
    create: bool,
) -> Path:
    return _verification_path(
        project_root,
        ticket_path,
        "user-approval.json",
        create=create,
    )


def _final_path(
    project_root: str | Path,
    ticket_path: str | Path,
    *,
    create: bool,
) -> Path:
    return _verification_path(
        project_root,
        ticket_path,
        "final-outcome.json",
        create=create,
    )


def _remediation_path(
    project_root: str | Path,
    ticket_path: str | Path,
    *,
    create: bool,
) -> Path:
    return _verification_path(
        project_root,
        ticket_path,
        "remediation-current.json",
        create=create,
    )


def _validate_plan(value: Any, expected_binding: dict[str, str]) -> dict[str, Any]:
    plan = _object(value, "plan envelope")
    _require_keys(
        plan,
        "plan envelope",
        {
            "schema",
            "verification_execution_id",
            "binding",
            "coverage_gate_envelope",
            "accepted_challenger_receipt",
            "gate_approval",
        },
    )
    if plan["schema"] != PLAN_SCHEMA:
        raise TransportError("plan envelope schema is invalid")
    execution_id = _text(plan["verification_execution_id"], "verification_execution_id", maximum=64)
    if not _NONCE.fullmatch(execution_id):
        raise TransportError("verification_execution_id is invalid")
    binding = _validate_binding(plan["binding"], expected_binding)
    envelope, receipt, approval = _validate_gate_package(
        plan["coverage_gate_envelope"],
        plan["accepted_challenger_receipt"],
        plan["gate_approval"],
    )
    _validate_gate_binding(envelope, binding)
    return {
        "schema": PLAN_SCHEMA,
        "verification_execution_id": execution_id,
        "binding": binding,
        "coverage_gate_envelope": envelope,
        "accepted_challenger_receipt": receipt,
        "gate_approval": approval,
    }


def _remediation_slot_state(
    project_root: str | Path,
    ticket_path: str | Path,
) -> str | None:
    try:
        path = _remediation_path(project_root, ticket_path, create=False)
    except ArtifactNotFound:
        return None
    try:
        raw = _read_artifact(path, "remediation checkpoint")
    except ArtifactNotFound:
        return None
    checkpoint = _object(raw, "remediation checkpoint")
    _require_keys(
        checkpoint,
        "remediation checkpoint",
        {
            "schema",
            "verification_execution_id",
            "plan_and_approval_binding",
            "failure_origin",
            "cycles",
            "state",
            "safe_abandonment",
        },
    )
    if checkpoint["schema"] != REMEDIATION_SCHEMA:
        raise TransportError("remediation checkpoint schema is invalid")
    state = _text(checkpoint["state"], "remediation state", maximum=32)
    if state not in {"ACTIVE", "SAFE_ABANDONED"}:
        raise TransportError("remediation state is invalid")
    if state == "SAFE_ABANDONED":
        _validate_safe_abandonment_base(checkpoint["safe_abandonment"])
    elif checkpoint["safe_abandonment"] is not None:
        raise TransportError("active remediation cannot contain safe abandonment")
    return state


def _require_replaceable_remediation_checkpoint(
    project_root: str | Path,
    ticket_path: str | Path,
) -> None:
    try:
        path = _remediation_path(project_root, ticket_path, create=False)
        raw = _read_artifact(path, "remediation checkpoint")
    except ArtifactNotFound:
        return
    if not _safe_abandoned_checkpoint_is_replaceable(project_root, ticket_path, raw):
        raise TransportError(
            "an unresolved remediation checkpoint prevents replacement of the plan package"
        )


def _safe_abandoned_checkpoint_is_replaceable(
    project_root: str | Path,
    ticket_path: str | Path,
    raw: dict[str, Any],
) -> bool:
    checkpoint = _object(raw, "remediation checkpoint")
    _require_keys(
        checkpoint,
        "remediation checkpoint",
        {
            "schema",
            "verification_execution_id",
            "plan_and_approval_binding",
            "failure_origin",
            "cycles",
            "state",
            "safe_abandonment",
        },
    )
    if checkpoint["schema"] != REMEDIATION_SCHEMA:
        raise TransportError("remediation checkpoint schema is invalid")
    state = _text(checkpoint["state"], "remediation state", maximum=32)
    if state == "ACTIVE":
        return False
    if state != "SAFE_ABANDONED":
        raise TransportError("remediation state is invalid")
    execution_id = _text(
        checkpoint["verification_execution_id"], "remediation verification_execution_id", maximum=64
    )
    if not _NONCE.fullmatch(execution_id):
        raise TransportError("remediation verification_execution_id is invalid")
    abandonment = _validate_safe_abandonment_base(checkpoint["safe_abandonment"])
    binding = _object(checkpoint["plan_and_approval_binding"], "plan_and_approval_binding")
    _require_keys(
        binding,
        "plan_and_approval_binding",
        {
            "verification_execution_id",
            "binding",
            "plan_fp",
            "gate_approval_id",
            "approval_projection_sha256",
        },
    )
    stored_execution_id = _text(
        binding["verification_execution_id"], "stored remediation verification_execution_id", maximum=64
    )
    if not _NONCE.fullmatch(stored_execution_id):
        raise TransportError("stored remediation verification_execution_id is invalid")
    if stored_execution_id != execution_id:
        raise TransportError("remediation execution IDs do not match")
    _sha256(binding["plan_fp"], "stored remediation plan_fp")
    _identifier(binding["gate_approval_id"], "stored remediation gate_approval_id")
    _sha256(
        binding["approval_projection_sha256"],
        "stored remediation approval_projection_sha256",
    )
    stored = _object(binding["binding"], "stored remediation binding")
    expected = _binding(project_root, ticket_path)
    stored_binding = _validate_binding(
        stored,
        expected,
        require_current_digest=False,
    )
    stored_project_root = Path(stored_binding["project_root"])
    origin = _object(checkpoint["failure_origin"], "failure_origin")
    _require_keys(
        origin,
        "failure_origin",
        {
            "target_ac_ids",
            "observed_product_boundary",
            "expected_actual_difference",
            "direct_evidence_refs",
            "relevant_source_anchors",
        },
    )
    _string_ids(origin["target_ac_ids"], "failure_origin.target_ac_ids")
    _text(origin["observed_product_boundary"], "failure_origin.observed_product_boundary")
    _text(origin["expected_actual_difference"], "failure_origin.expected_actual_difference")
    _string_ids(origin["direct_evidence_refs"], "failure_origin.direct_evidence_refs")
    _validate_anchors(
        origin["relevant_source_anchors"],
        stored_project_root,
        "failure_origin.relevant_source_anchors",
        require_current_digest=False,
    )
    cycles = _array(checkpoint["cycles"], "remediation cycles", maximum=3)
    if not cycles:
        raise TransportError("remediation checkpoint must contain the authorized first cycle")
    normalized_cycles: list[dict[str, Any]] = []
    for index, raw_cycle in enumerate(cycles, start=1):
        label = f"remediation cycles[{index - 1}]"
        cycle = _object(raw_cycle, label)
        _require_keys(
            cycle,
            label,
            {
                "cycle",
                "remediation_agent_proposal",
                "lead_authorization",
                "pre_mutation_anchor_digests",
                "mutation_report",
                "primary_verifier_reconciliation",
            },
        )
        if cycle["cycle"] != index:
            raise TransportError(f"{label}.cycle must be {index}")
        proposal = _object(cycle["remediation_agent_proposal"], f"{label}.remediation_agent_proposal")
        _require_keys(
            proposal,
            f"{label}.remediation_agent_proposal",
            {"target_ac_ids", "hypothesis", "authorized_seam", "minimum_change"},
        )
        _string_ids(
            proposal["target_ac_ids"], f"{label}.remediation_agent_proposal.target_ac_ids"
        )
        _text(proposal["hypothesis"], f"{label}.remediation_agent_proposal.hypothesis")
        _text(proposal["authorized_seam"], f"{label}.remediation_agent_proposal.authorized_seam")
        _text(proposal["minimum_change"], f"{label}.remediation_agent_proposal.minimum_change")
        _validate_lead_authorization(cycle["lead_authorization"], f"{label}.lead_authorization")
        anchors = _validate_anchors(
            cycle["pre_mutation_anchor_digests"],
            stored_project_root,
            f"{label}.pre_mutation_anchor_digests",
            require_current_digest=False,
        )
        report = cycle["mutation_report"]
        reconciliation = cycle["primary_verifier_reconciliation"]
        if report is None and reconciliation is not None:
            raise TransportError(f"{label} cannot reconcile before its mutation report")
        if report is not None:
            _validate_mutation_report(report, f"{label}.mutation_report")
        if reconciliation is not None:
            normalized_reconciliation = _object(
                reconciliation, f"{label}.primary_verifier_reconciliation"
            )
            _require_keys(
                normalized_reconciliation,
                f"{label}.primary_verifier_reconciliation",
                {
                    "reconciled_at",
                    "target_ac_ids",
                    "affected_ac_ids",
                    "result",
                    "direct_evidence_refs",
                },
            )
            _timestamp(
                normalized_reconciliation["reconciled_at"],
                f"{label}.primary_verifier_reconciliation.reconciled_at",
            )
            _string_ids(
                normalized_reconciliation["target_ac_ids"],
                f"{label}.primary_verifier_reconciliation.target_ac_ids",
            )
            _string_ids(
                normalized_reconciliation["affected_ac_ids"],
                f"{label}.primary_verifier_reconciliation.affected_ac_ids",
            )
            result = _text(
                normalized_reconciliation["result"],
                f"{label}.primary_verifier_reconciliation.result",
                maximum=32,
            )
            if result not in _VERDICTS:
                raise TransportError(f"{label}.primary_verifier_reconciliation.result is invalid")
            _string_ids(
                normalized_reconciliation["direct_evidence_refs"],
                f"{label}.primary_verifier_reconciliation.direct_evidence_refs",
            )
        normalized_cycles.append(
            {
                "anchors": anchors,
                "mutation_report": report,
                "primary_verifier_reconciliation": reconciliation,
            }
        )
    if abandonment["mutation_state"] == "MUTATION_NOT_RUN":
        current = normalized_cycles[-1]
        if (
            current["mutation_report"] is not None
            or current["primary_verifier_reconciliation"] is not None
        ):
            raise TransportError("MUTATION_NOT_RUN requires an unexecuted current cycle")
        if any(
            cycle["mutation_report"] is None
            or cycle["primary_verifier_reconciliation"] is None
            for cycle in normalized_cycles[:-1]
        ):
            raise TransportError("MUTATION_NOT_RUN requires all earlier cycles to be reconciled")
        _validate_anchors(
            cycles[-1]["pre_mutation_anchor_digests"],
            stored_project_root,
            "safe_abandonment.current_pre_mutation_anchor_digests",
            require_current_digest=True,
        )
    elif any(
        cycle["mutation_report"] is None
        or cycle["primary_verifier_reconciliation"] is None
        for cycle in normalized_cycles
    ):
        raise TransportError("MUTATION_STATE_RECONCILED requires every cycle to be complete")
    return True


def publish_plan_envelope(
    project_root: str | Path,
    ticket_path: str | Path,
    coverage_gate_envelope: dict[str, Any],
    accepted_challenger_receipt: dict[str, Any],
    gate_approval: dict[str, Any],
) -> dict[str, str]:
    """Publish one complete accepted plan package with a fresh local nonce."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=True):
        _require_replaceable_remediation_checkpoint(project_root, ticket_path)
        plan = _publish_plan_envelope_unlocked(
            project_root,
            ticket_path,
            coverage_gate_envelope,
            accepted_challenger_receipt,
            gate_approval,
        )
    return {
        "verification_execution_id": plan["verification_execution_id"],
        "plan_fp": plan["gate_approval"]["plan_fp"],
        "gate_approval_id": plan["gate_approval"]["approval_id"],
    }


def _publish_plan_envelope_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    coverage_gate_envelope: dict[str, Any],
    accepted_challenger_receipt: dict[str, Any],
    gate_approval: dict[str, Any],
 ) -> dict[str, Any]:
    binding = _binding(project_root, ticket_path)
    envelope, receipt, approval = _validate_gate_package(
        coverage_gate_envelope, accepted_challenger_receipt, gate_approval
    )
    plan = {
        "schema": PLAN_SCHEMA,
        "verification_execution_id": f"vx-{secrets.token_hex(16)}",
        "binding": binding,
        "coverage_gate_envelope": envelope,
        "accepted_challenger_receipt": receipt,
        "gate_approval": approval,
    }
    _validate_plan(plan, binding)
    path = _plan_path(project_root, ticket_path, create=True)
    _write_artifact(path, plan, "plan envelope")
    return plan


def read_plan_envelope(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    """Read the one current plan package after validating its complete gate chain."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        return _read_plan_envelope_unlocked(project_root, ticket_path)


def _read_plan_envelope_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    binding = _binding(project_root, ticket_path)
    path = _plan_path(project_root, ticket_path, create=False)
    return _validate_plan(_read_artifact(path, "plan envelope"), binding)


def _scenario_projection(plan: dict[str, Any]) -> list[dict[str, Any]]:
    envelope = plan["coverage_gate_envelope"]
    ac_ids = {root["id"] for root in envelope["canonical"]["roots"] if root["kind"] == "AC"}
    unit_by_id = {unit["id"]: unit for unit in envelope["units"]}
    edges_by_scenario: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for edge in envelope["coverage_edges"]:
        edges_by_scenario.setdefault((edge["scenario_id"], edge["scenario_revision"]), []).append(edge)
    projections: list[dict[str, Any]] = []
    for scenario in envelope["scenarios"]:
        key = (scenario["id"], scenario["revision"])
        edges = sorted(edges_by_scenario.get(key, []), key=lambda item: item["id"])
        mapped_ac_ids = sorted(
            {
                root_id
                for edge in edges
                for root_id in unit_by_id[edge["unit_id"]]["root_ids"]
                if root_id in ac_ids
            }
        )
        projections.append(
            {
                "scenario_id": scenario["id"],
                "scenario_revision": scenario["revision"],
                "procedure": scenario["procedure"],
                "mapped_ac_ids": mapped_ac_ids,
                "readiness": scenario["readiness"],
                "coverage": [
                    {
                        "coverage_edge_id": edge["id"],
                        "trigger": edge["trigger"],
                        "product_path": edge["product_boundary"],
                        "observation_readback": edge["observation_readback"],
                        "expected_result": edge["expected_result"],
                        "forbidden_result": edge["forbidden_result"],
                        "decision_boundary": edge["decision_predicate"],
                        "identity_correlation": edge["identity_correlation"],
                    }
                    for edge in edges
                ],
                "preparation_scope": scenario["preparation_scope"],
            }
        )
    return projections


def _approval_projection_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    envelope = plan["coverage_gate_envelope"]
    approval = plan["gate_approval"]
    partial_projection: dict[str, Any] | None = None
    if approval["mode"] == "PARTIAL":
        ac_ids = {root["id"] for root in envelope["canonical"]["roots"] if root["kind"] == "AC"}
        blocked = []
        for unit in envelope["units"]:
            if unit["disposition"] == "PLANNED":
                continue
            blocked.append(
                {
                    "unit_id": unit["id"],
                    "classification": unit["disposition"],
                    "mapped_ac_ids": sorted(
                        root_id for root_id in unit["root_ids"] if root_id in ac_ids
                    ),
                }
            )
        partial = envelope["partial"]
        if partial is None:
            raise TransportError("PARTIAL plan is missing its disclosed decision value")
        partial_projection = {
            "blocked_coverage": blocked,
            "decision_value": partial["decision_value"],
            "decision_unit_ids": partial["decision_unit_ids"],
            "contradiction_unit_ids": partial["contradiction_unit_ids"],
        }
    return {
        "gate_mode": approval["mode"],
        "gate_approval_id": approval["approval_id"],
        "scenarios": _scenario_projection(plan),
        "partial": partial_projection,
    }


def render_approval_disclosure(
    project_root: str | Path,
    ticket_path: str | Path,
) -> str:
    """Render the current normalized approval projection deterministically."""

    plan = read_plan_envelope(project_root, ticket_path)
    return json.dumps(
        _approval_projection_from_plan(plan),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _validate_approval(
    value: Any,
    expected_binding: dict[str, str],
    plan: dict[str, Any],
) -> dict[str, Any]:
    approval = _object(value, "user approval")
    _require_keys(
        approval,
        "user approval",
        {
            "schema",
            "verification_execution_id",
            "binding",
            "plan_fp",
            "gate_approval_id",
            "approval_projection",
            "approval_projection_sha256",
            "approval_observation",
            "approved_at",
        },
    )
    if approval["schema"] != APPROVAL_SCHEMA:
        raise TransportError("user approval schema is invalid")
    if approval["verification_execution_id"] != plan["verification_execution_id"]:
        raise TransportError("user approval execution ID does not match the plan")
    binding = _validate_binding(approval["binding"], expected_binding)
    gate_approval = plan["gate_approval"]
    if (
        approval["plan_fp"] != gate_approval["plan_fp"]
        or approval["gate_approval_id"] != gate_approval["approval_id"]
    ):
        raise TransportError("user approval does not match the gate-approved plan")
    projection = _object(approval["approval_projection"], "approval_projection")
    _bounded_json(projection, "approval_projection")
    expected_projection = _approval_projection_from_plan(plan)
    if projection != expected_projection:
        raise TransportError("user approval projection is incomplete or does not match the plan")
    if approval["approval_projection_sha256"] != _json_digest(projection):
        raise TransportError("user approval projection digest is invalid")
    if approval["approval_observation"] != "EXPLICIT_APPROVAL_OBSERVED":
        raise TransportError("user approval must record explicit approval observation")
    _timestamp(approval["approved_at"], "approved_at")
    return {
        "schema": APPROVAL_SCHEMA,
        "verification_execution_id": plan["verification_execution_id"],
        "binding": binding,
        "plan_fp": gate_approval["plan_fp"],
        "gate_approval_id": gate_approval["approval_id"],
        "approval_projection": projection,
        "approval_projection_sha256": approval["approval_projection_sha256"],
        "approval_observation": "EXPLICIT_APPROVAL_OBSERVED",
        "approved_at": approval["approved_at"],
    }


def publish_user_approval(
    project_root: str | Path,
    ticket_path: str | Path,
    approved_at: str,
) -> dict[str, str]:
    """Publish an explicit approval receipt for the one current plan package."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        return _publish_user_approval_unlocked(project_root, ticket_path, approved_at)


def _publish_user_approval_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    approved_at: str,
) -> dict[str, str]:
    if _remediation_slot_state(project_root, ticket_path) == "ACTIVE":
        raise TransportError("an unresolved remediation checkpoint prevents approval replacement")
    plan = _read_plan_envelope_unlocked(project_root, ticket_path)
    binding = _binding(project_root, ticket_path)
    receipt = {
        "schema": APPROVAL_SCHEMA,
        "verification_execution_id": plan["verification_execution_id"],
        "binding": binding,
        "plan_fp": plan["gate_approval"]["plan_fp"],
        "gate_approval_id": plan["gate_approval"]["approval_id"],
        "approval_projection": _approval_projection_from_plan(plan),
        "approval_projection_sha256": _json_digest(_approval_projection_from_plan(plan)),
        "approval_observation": "EXPLICIT_APPROVAL_OBSERVED",
        "approved_at": approved_at,
    }
    receipt = _validate_approval(receipt, binding, plan)
    path = _approval_path(project_root, ticket_path, create=False)
    _write_artifact(path, receipt, "user approval")
    return {
        "verification_execution_id": receipt["verification_execution_id"],
        "plan_fp": receipt["plan_fp"],
        "gate_approval_id": receipt["gate_approval_id"],
    }


def read_user_approval(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    """Read the one approval receipt only when it still matches the current plan."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        return _read_user_approval_unlocked(project_root, ticket_path)


def _read_user_approval_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    plan = _read_plan_envelope_unlocked(project_root, ticket_path)
    binding = _binding(project_root, ticket_path)
    path = _approval_path(project_root, ticket_path, create=False)
    return _validate_approval(_read_artifact(path, "user approval"), binding, plan)


def _plan_and_approval_binding(
    plan: dict[str, Any], approval: dict[str, Any]
) -> dict[str, Any]:
    return {
        "verification_execution_id": plan["verification_execution_id"],
        "binding": copy.deepcopy(plan["binding"]),
        "plan_fp": plan["gate_approval"]["plan_fp"],
        "gate_approval_id": plan["gate_approval"]["approval_id"],
        "approval_projection_sha256": approval["approval_projection_sha256"],
    }


def _validate_plan_and_approval_binding(
    value: Any,
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    binding = _object(value, "plan_and_approval_binding")
    _require_keys(
        binding,
        "plan_and_approval_binding",
        {
            "verification_execution_id",
            "binding",
            "plan_fp",
            "gate_approval_id",
            "approval_projection_sha256",
        },
    )
    expected = _plan_and_approval_binding(plan, approval)
    if binding != expected:
        raise TransportError("plan and approval binding does not match the current receipts")
    return copy.deepcopy(expected)


def _ac_root_ids(plan: dict[str, Any]) -> list[str]:
    return [
        root["id"]
        for root in plan["coverage_gate_envelope"]["canonical"]["roots"]
        if root["kind"] == "AC"
    ]


def _verification_root_ids(plan: dict[str, Any]) -> list[str]:
    return [
        root["id"]
        for root in plan["coverage_gate_envelope"]["canonical"]["roots"]
        if root["kind"] == "V"
    ]


def _validate_failure_origin(
    value: Any,
    ac_ids: set[str],
    project_root: Path,
    *,
    require_current_anchors: bool,
) -> dict[str, Any]:
    origin = _object(value, "failure_origin")
    _require_keys(
        origin,
        "failure_origin",
        {
            "target_ac_ids",
            "observed_product_boundary",
            "expected_actual_difference",
            "direct_evidence_refs",
            "relevant_source_anchors",
        },
    )
    target_ac_ids = _string_ids(origin["target_ac_ids"], "failure_origin.target_ac_ids")
    if not set(target_ac_ids) <= ac_ids:
        raise TransportError("failure origin targets an AC outside the current plan")
    return {
        "target_ac_ids": target_ac_ids,
        "observed_product_boundary": _text(
            origin["observed_product_boundary"], "failure_origin.observed_product_boundary"
        ),
        "expected_actual_difference": _text(
            origin["expected_actual_difference"], "failure_origin.expected_actual_difference"
        ),
        "direct_evidence_refs": _string_ids(
            origin["direct_evidence_refs"], "failure_origin.direct_evidence_refs"
        ),
        "relevant_source_anchors": _validate_anchors(
            origin["relevant_source_anchors"],
            project_root,
            "failure_origin.relevant_source_anchors",
            require_current_digest=require_current_anchors,
        ),
    }


def _validate_remediation_proposal(value: Any, ac_ids: set[str], label: str) -> dict[str, Any]:
    proposal = _object(value, label)
    _require_keys(
        proposal,
        label,
        {"target_ac_ids", "hypothesis", "authorized_seam", "minimum_change"},
    )
    target_ac_ids = _string_ids(proposal["target_ac_ids"], f"{label}.target_ac_ids")
    if not set(target_ac_ids) <= ac_ids:
        raise TransportError(f"{label} targets an AC outside the current plan")
    return {
        "target_ac_ids": target_ac_ids,
        "hypothesis": _text(proposal["hypothesis"], f"{label}.hypothesis"),
        "authorized_seam": _text(proposal["authorized_seam"], f"{label}.authorized_seam"),
        "minimum_change": _text(proposal["minimum_change"], f"{label}.minimum_change"),
    }


def _validate_lead_authorization(value: Any, label: str) -> dict[str, str]:
    authorization = _object(value, label)
    _require_keys(authorization, label, {"authorization_id", "authorized_at"})
    _timestamp(authorization["authorized_at"], f"{label}.authorized_at")
    return {
        "authorization_id": _identifier(
            authorization["authorization_id"], f"{label}.authorization_id"
        ),
        "authorized_at": authorization["authorized_at"],
    }


def _validate_mutation_report(value: Any, label: str) -> dict[str, Any]:
    report = _object(value, label)
    _require_keys(report, label, {"reported_at", "changed_anchors", "summary"})
    _timestamp(report["reported_at"], f"{label}.reported_at")
    anchors: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(_array(report["changed_anchors"], f"{label}.changed_anchors", maximum=_MAX_ANCHORS)):
        anchor = _object(raw, f"{label}.changed_anchors[{index}]")
        _require_keys(anchor, f"{label}.changed_anchors[{index}]", {"path", "sha256"})
        path = _text(anchor["path"], f"{label}.changed_anchors[{index}].path", maximum=512)
        if Path(path).is_absolute() or ".." in Path(path).parts or "." in Path(path).parts:
            raise TransportError(f"{label}.changed_anchors[{index}].path is not project-relative")
        if path in seen:
            raise TransportError(f"{label}.changed_anchors contains duplicate paths")
        seen.add(path)
        anchors.append({"path": path, "sha256": _sha256(anchor["sha256"], f"{label}.changed_anchors[{index}].sha256")})
    if not anchors:
        raise TransportError(f"{label}.changed_anchors must not be empty")
    if anchors != sorted(anchors, key=lambda item: item["path"]):
        raise TransportError(f"{label}.changed_anchors must be sorted by path")
    return {
        "reported_at": report["reported_at"],
        "changed_anchors": anchors,
        "summary": _text(report["summary"], f"{label}.summary"),
    }


def _validate_reconciliation(value: Any, ac_ids: set[str], label: str) -> dict[str, Any]:
    reconciliation = _object(value, label)
    _require_keys(
        reconciliation,
        label,
        {
            "reconciled_at",
            "target_ac_ids",
            "affected_ac_ids",
            "result",
            "direct_evidence_refs",
        },
    )
    _timestamp(reconciliation["reconciled_at"], f"{label}.reconciled_at")
    target_ac_ids = _string_ids(reconciliation["target_ac_ids"], f"{label}.target_ac_ids")
    affected_ac_ids = _string_ids(reconciliation["affected_ac_ids"], f"{label}.affected_ac_ids")
    if not set(target_ac_ids) <= ac_ids or not set(affected_ac_ids) <= ac_ids:
        raise TransportError(f"{label} references an AC outside the current plan")
    result = _text(reconciliation["result"], f"{label}.result", maximum=32)
    if result not in _VERDICTS:
        raise TransportError(f"{label}.result is invalid")
    return {
        "reconciled_at": reconciliation["reconciled_at"],
        "target_ac_ids": target_ac_ids,
        "affected_ac_ids": affected_ac_ids,
        "result": result,
        "direct_evidence_refs": _string_ids(
            reconciliation["direct_evidence_refs"], f"{label}.direct_evidence_refs"
        ),
    }


def _validate_remediation_cycle(
    value: Any,
    expected_cycle: int,
    ac_ids: set[str],
    project_root: Path,
    label: str,
    *,
    require_current_pre_mutation_anchors: bool,
) -> dict[str, Any]:
    cycle = _object(value, label)
    _require_keys(
        cycle,
        label,
        {
            "cycle",
            "remediation_agent_proposal",
            "lead_authorization",
            "pre_mutation_anchor_digests",
            "mutation_report",
            "primary_verifier_reconciliation",
        },
    )
    if cycle["cycle"] != expected_cycle:
        raise TransportError(f"{label}.cycle must be {expected_cycle}")
    report = cycle["mutation_report"]
    reconciliation = cycle["primary_verifier_reconciliation"]
    if report is None and reconciliation is not None:
        raise TransportError(f"{label} cannot reconcile before its mutation report")
    normalized_report = (
        None if report is None else _validate_mutation_report(report, f"{label}.mutation_report")
    )
    normalized_reconciliation = (
        None
        if reconciliation is None
        else _validate_reconciliation(
            reconciliation, ac_ids, f"{label}.primary_verifier_reconciliation"
        )
    )
    return {
        "cycle": expected_cycle,
        "remediation_agent_proposal": _validate_remediation_proposal(
            cycle["remediation_agent_proposal"], ac_ids, f"{label}.remediation_agent_proposal"
        ),
        "lead_authorization": _validate_lead_authorization(
            cycle["lead_authorization"], f"{label}.lead_authorization"
        ),
        "pre_mutation_anchor_digests": _validate_anchors(
            cycle["pre_mutation_anchor_digests"],
            project_root,
            f"{label}.pre_mutation_anchor_digests",
            require_current_digest=require_current_pre_mutation_anchors,
        ),
        "mutation_report": normalized_report,
        "primary_verifier_reconciliation": normalized_reconciliation,
    }


def _validate_safe_abandonment_base(value: Any) -> dict[str, str]:
    abandonment = _object(value, "safe_abandonment")
    _require_keys(abandonment, "safe_abandonment", {"established_at", "mutation_state", "reason"})
    _timestamp(abandonment["established_at"], "safe_abandonment.established_at")
    state = _text(abandonment["mutation_state"], "safe_abandonment.mutation_state", maximum=64)
    if state not in _SAFE_ABANDONMENT_STATES:
        raise TransportError("safe_abandonment.mutation_state is invalid")
    return {
        "established_at": abandonment["established_at"],
        "mutation_state": state,
        "reason": _text(abandonment["reason"], "safe_abandonment.reason"),
    }


def _validate_safe_abandonment(
    value: Any,
    cycles: list[dict[str, Any]],
    project_root: Path,
) -> dict[str, str]:
    abandonment = _validate_safe_abandonment_base(value)
    current = cycles[-1]
    if abandonment["mutation_state"] == "MUTATION_NOT_RUN":
        if (
            current["mutation_report"] is not None
            or current["primary_verifier_reconciliation"] is not None
        ):
            raise TransportError("MUTATION_NOT_RUN requires an unexecuted current cycle")
        if any(
            cycle["mutation_report"] is None
            or cycle["primary_verifier_reconciliation"] is None
            for cycle in cycles[:-1]
        ):
            raise TransportError("MUTATION_NOT_RUN requires all earlier cycles to be reconciled")
        _validate_anchors(
            current["pre_mutation_anchor_digests"],
            project_root,
            "safe_abandonment.current_pre_mutation_anchor_digests",
            require_current_digest=True,
        )
    elif any(
        cycle["mutation_report"] is None
        or cycle["primary_verifier_reconciliation"] is None
        for cycle in cycles
    ):
        raise TransportError("MUTATION_STATE_RECONCILED requires every cycle to be complete")
    return abandonment


def _validate_remediation(
    value: Any,
    plan: dict[str, Any],
    approval: dict[str, Any],
    *,
    require_current_pre_mutation_anchors: bool,
) -> dict[str, Any]:
    remediation = _object(value, "remediation checkpoint")
    _require_keys(
        remediation,
        "remediation checkpoint",
        {
            "schema",
            "verification_execution_id",
            "plan_and_approval_binding",
            "failure_origin",
            "cycles",
            "state",
            "safe_abandonment",
        },
    )
    if remediation["schema"] != REMEDIATION_SCHEMA:
        raise TransportError("remediation checkpoint schema is invalid")
    if remediation["verification_execution_id"] != plan["verification_execution_id"]:
        raise TransportError("remediation checkpoint execution ID does not match the plan")
    binding = _validate_plan_and_approval_binding(
        remediation["plan_and_approval_binding"], plan, approval
    )
    project_root = Path(binding["binding"]["project_root"])
    ac_ids = set(_ac_root_ids(plan))
    cycles = _array(remediation["cycles"], "remediation cycles", maximum=3)
    if not cycles:
        raise TransportError("remediation checkpoint must contain the authorized first cycle")
    normalized_origin = _validate_failure_origin(
        remediation["failure_origin"],
        ac_ids,
        project_root,
        require_current_anchors=require_current_pre_mutation_anchors,
    )
    normalized_cycles = [
        _validate_remediation_cycle(
            raw,
            index,
            ac_ids,
            project_root,
            f"remediation cycles[{index - 1}]",
            require_current_pre_mutation_anchors=require_current_pre_mutation_anchors,
        )
        for index, raw in enumerate(cycles, start=1)
    ]
    used_reconciliation_refs = set(normalized_origin["direct_evidence_refs"])
    for cycle in normalized_cycles:
        reconciliation = cycle["primary_verifier_reconciliation"]
        if reconciliation is None:
            continue
        references = set(reconciliation["direct_evidence_refs"])
        if references & used_reconciliation_refs:
            raise TransportError(
                "remediation reconciliation evidence must be fresh for each cycle"
            )
        used_reconciliation_refs.update(references)
    state = _text(remediation["state"], "remediation state", maximum=32)
    safe_abandonment = remediation["safe_abandonment"]
    if state == "ACTIVE":
        if safe_abandonment is not None:
            raise TransportError("active remediation cannot contain safe abandonment")
        normalized_abandonment = None
    elif state == "SAFE_ABANDONED":
        normalized_abandonment = _validate_safe_abandonment(
            safe_abandonment, normalized_cycles, project_root
        )
    else:
        raise TransportError("remediation state is invalid")
    return {
        "schema": REMEDIATION_SCHEMA,
        "verification_execution_id": plan["verification_execution_id"],
        "plan_and_approval_binding": binding,
        "failure_origin": normalized_origin,
        "cycles": normalized_cycles,
        "state": state,
        "safe_abandonment": normalized_abandonment,
    }


def _read_current_plan_and_approval(
    project_root: str | Path,
    ticket_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    plan = _read_plan_envelope_unlocked(project_root, ticket_path)
    binding = _binding(project_root, ticket_path)
    path = _approval_path(project_root, ticket_path, create=False)
    approval = _validate_approval(
        _read_artifact(path, "user approval"), binding, plan
    )
    return plan, approval


def _read_remediation(
    project_root: str | Path,
    ticket_path: str | Path,
    require_current_pre_mutation_anchors: bool,
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    plan, approval = _read_current_plan_and_approval(project_root, ticket_path)
    path = _remediation_path(project_root, ticket_path, create=False)
    remediation = _validate_remediation(
        _read_artifact(path, "remediation checkpoint"),
        plan,
        approval,
        require_current_pre_mutation_anchors=require_current_pre_mutation_anchors,
    )
    return path, remediation, plan, approval


def _read_matching_final_if_present(
    project_root: str | Path,
    ticket_path: str | Path,
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any] | None:
    path = _final_path(project_root, ticket_path, create=False)
    try:
        raw = _read_artifact(path, "final outcome")
    except ArtifactNotFound:
        return None
    execution_id = raw.get("verification_execution_id")
    if not isinstance(execution_id, str):
        raise TransportError("final outcome execution ID is malformed")
    if execution_id != plan["verification_execution_id"]:
        return None
    expected = _binding(project_root, ticket_path)
    final = _validate_final_outcome(raw, expected, plan, approval)
    return final


def _require_no_current_terminal(
    project_root: str | Path,
    ticket_path: str | Path,
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> None:
    if _read_matching_final_if_present(project_root, ticket_path, plan, approval) is not None:
        raise TransportError("current verification execution already has a terminal final outcome")


def begin_remediation(
    project_root: str | Path,
    ticket_path: str | Path,
    failure_origin: dict[str, Any],
    remediation_agent_proposal: dict[str, Any],
    lead_authorization: dict[str, Any],
    pre_mutation_anchor_digests: list[dict[str, str]],
) -> None:
    """Create the sole mutation checkpoint immediately before cycle-one mutation."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        _begin_remediation_unlocked(
            project_root,
            ticket_path,
            failure_origin,
            remediation_agent_proposal,
            lead_authorization,
            pre_mutation_anchor_digests,
        )


def _begin_remediation_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    failure_origin: dict[str, Any],
    remediation_agent_proposal: dict[str, Any],
    lead_authorization: dict[str, Any],
    pre_mutation_anchor_digests: list[dict[str, str]],
) -> None:
    plan, approval = _read_current_plan_and_approval(project_root, ticket_path)
    _require_no_current_terminal(project_root, ticket_path, plan, approval)
    path = _remediation_path(project_root, ticket_path, create=True)
    raw_existing: dict[str, Any] | None
    try:
        raw_existing = _read_artifact(path, "remediation checkpoint")
    except ArtifactNotFound:
        raw_existing = None
    if raw_existing is not None:
        raw_execution_id = raw_existing.get("verification_execution_id")
        if not isinstance(raw_execution_id, str):
            raise TransportError("remediation checkpoint is malformed")
        if raw_execution_id == plan["verification_execution_id"]:
            raise TransportError("safe abandonment requires a fresh plan before another mutation")
        if not _safe_abandoned_checkpoint_is_replaceable(
            project_root, ticket_path, raw_existing
        ):
            raise TransportError("an active remediation checkpoint prevents duplicate mutation")
        # A prior safe abandonment records the only mutation state needed to
        # avoid duplicate work. A new accepted execution may replace this one
        # bounded checkpoint; no historical slot is retained.
    binding = _plan_and_approval_binding(plan, approval)
    project = Path(binding["binding"]["project_root"])
    ac_ids = set(_ac_root_ids(plan))
    checkpoint = {
        "schema": REMEDIATION_SCHEMA,
        "verification_execution_id": plan["verification_execution_id"],
        "plan_and_approval_binding": binding,
        "failure_origin": _validate_failure_origin(
            failure_origin, ac_ids, project, require_current_anchors=True
        ),
        "cycles": [
            {
                "cycle": 1,
                "remediation_agent_proposal": _validate_remediation_proposal(
                    remediation_agent_proposal, ac_ids, "remediation_agent_proposal"
                ),
                "lead_authorization": _validate_lead_authorization(
                    lead_authorization, "lead_authorization"
                ),
                "pre_mutation_anchor_digests": _validate_anchors(
                    pre_mutation_anchor_digests,
                    project,
                    "pre_mutation_anchor_digests",
                    require_current_digest=True,
                ),
                "mutation_report": None,
                "primary_verifier_reconciliation": None,
            }
        ],
        "state": "ACTIVE",
        "safe_abandonment": None,
    }
    checkpoint = _validate_remediation(
        checkpoint,
        plan,
        approval,
        require_current_pre_mutation_anchors=True,
    )
    _write_artifact(path, checkpoint, "remediation checkpoint")


def _write_remediation_update(
    path: Path,
    previous: dict[str, Any],
    updated: dict[str, Any],
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> None:
    normalized = _validate_remediation(
        updated,
        plan,
        approval,
        require_current_pre_mutation_anchors=False,
    )
    if normalized["failure_origin"] != previous["failure_origin"]:
        raise TransportError("remediation failure origin is immutable")
    if normalized["plan_and_approval_binding"] != previous["plan_and_approval_binding"]:
        raise TransportError("remediation plan and approval binding is immutable")
    previous_cycles = previous["cycles"]
    new_cycles = normalized["cycles"]
    if len(new_cycles) == len(previous_cycles):
        if previous["state"] != "ACTIVE" or normalized["state"] not in {
            "ACTIVE",
            "SAFE_ABANDONED",
        }:
            raise TransportError("remediation checkpoint cannot be reopened or rewritten")
        for index, prior_cycle in enumerate(previous_cycles[:-1]):
            if new_cycles[index] != prior_cycle:
                raise TransportError("completed remediation cycles are immutable")
        prior_current = previous_cycles[-1]
        next_current = new_cycles[-1]
        if prior_current["remediation_agent_proposal"] != next_current["remediation_agent_proposal"]:
            raise TransportError("remediation proposal is immutable")
        if prior_current["lead_authorization"] != next_current["lead_authorization"]:
            raise TransportError("remediation authorization is immutable")
        if prior_current["pre_mutation_anchor_digests"] != next_current["pre_mutation_anchor_digests"]:
            raise TransportError("pre-mutation anchors are immutable")
        if prior_current["mutation_report"] is not None and next_current["mutation_report"] != prior_current["mutation_report"]:
            raise TransportError("recorded remediation mutation is immutable")
        if (
            prior_current["primary_verifier_reconciliation"] is not None
            and next_current["primary_verifier_reconciliation"]
            != prior_current["primary_verifier_reconciliation"]
        ):
            raise TransportError("recorded remediation reconciliation is immutable")
        if prior_current["mutation_report"] is None and next_current["mutation_report"] is None:
            if next_current != prior_current:
                raise TransportError("only a mutation report may complete the current cycle")
        elif (
            prior_current["mutation_report"] is not None
            and prior_current["primary_verifier_reconciliation"] is None
            and next_current["primary_verifier_reconciliation"] is None
            and next_current != prior_current
        ):
            raise TransportError("only reconciliation may complete the current cycle")
    elif len(new_cycles) == len(previous_cycles) + 1:
        if previous["state"] != "ACTIVE" or normalized["state"] != "ACTIVE":
            raise TransportError("only active remediation may append a cycle")
        if new_cycles[:-1] != previous_cycles:
            raise TransportError("earlier remediation cycles are immutable")
        if previous_cycles[-1]["primary_verifier_reconciliation"] is None:
            raise TransportError("a cycle must be reconciled before another cycle is appended")
    else:
        raise TransportError("remediation updates may only complete the current cycle or append one cycle")
    if previous["state"] == "SAFE_ABANDONED":
        raise TransportError("safe-abandoned remediation cannot change")
    _write_artifact(path, normalized, "remediation checkpoint")


def record_remediation_mutation(
    project_root: str | Path,
    ticket_path: str | Path,
    mutation_report: dict[str, Any],
) -> None:
    """Complete only the current authorized cycle's mutation-report field."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        _record_remediation_mutation_unlocked(project_root, ticket_path, mutation_report)


def _record_remediation_mutation_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    mutation_report: dict[str, Any],
) -> None:
    path, checkpoint, plan, approval = _read_remediation(
        project_root,
        ticket_path,
        require_current_pre_mutation_anchors=False,
    )
    _require_no_current_terminal(project_root, ticket_path, plan, approval)
    if checkpoint["state"] != "ACTIVE":
        raise TransportError("safe-abandoned remediation cannot mutate")
    if checkpoint["cycles"][-1]["mutation_report"] is not None:
        raise TransportError("current remediation cycle already has a mutation report")
    updated = copy.deepcopy(checkpoint)
    updated["cycles"][-1]["mutation_report"] = mutation_report
    _write_remediation_update(path, checkpoint, updated, plan, approval)


def record_remediation_reconciliation(
    project_root: str | Path,
    ticket_path: str | Path,
    reconciliation: dict[str, Any],
) -> None:
    """Complete only the current cycle's Primary Verifier reconciliation field."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        _record_remediation_reconciliation_unlocked(project_root, ticket_path, reconciliation)


def _record_remediation_reconciliation_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    reconciliation: dict[str, Any],
) -> None:
    path, checkpoint, plan, approval = _read_remediation(
        project_root,
        ticket_path,
        require_current_pre_mutation_anchors=False,
    )
    _require_no_current_terminal(project_root, ticket_path, plan, approval)
    if checkpoint["state"] != "ACTIVE":
        raise TransportError("safe-abandoned remediation cannot reconcile")
    current = checkpoint["cycles"][-1]
    if current["mutation_report"] is None:
        raise TransportError("current remediation cycle has no mutation report")
    if current["primary_verifier_reconciliation"] is not None:
        raise TransportError("current remediation cycle already has reconciliation")
    updated = copy.deepcopy(checkpoint)
    updated["cycles"][-1]["primary_verifier_reconciliation"] = reconciliation
    _write_remediation_update(path, checkpoint, updated, plan, approval)


def append_remediation_cycle(
    project_root: str | Path,
    ticket_path: str | Path,
    remediation_agent_proposal: dict[str, Any],
    lead_authorization: dict[str, Any],
    pre_mutation_anchor_digests: list[dict[str, str]],
) -> None:
    """Append the next authorized cycle, preserving every prior cycle byte-for-byte."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        _append_remediation_cycle_unlocked(
            project_root,
            ticket_path,
            remediation_agent_proposal,
            lead_authorization,
            pre_mutation_anchor_digests,
        )


def _append_remediation_cycle_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    remediation_agent_proposal: dict[str, Any],
    lead_authorization: dict[str, Any],
    pre_mutation_anchor_digests: list[dict[str, str]],
) -> None:
    path, checkpoint, plan, approval = _read_remediation(
        project_root,
        ticket_path,
        require_current_pre_mutation_anchors=False,
    )
    _require_no_current_terminal(project_root, ticket_path, plan, approval)
    if checkpoint["state"] != "ACTIVE":
        raise TransportError("safe-abandoned remediation cannot append a cycle")
    reconciliation = checkpoint["cycles"][-1]["primary_verifier_reconciliation"]
    if reconciliation is None:
        raise TransportError("current remediation cycle must be reconciled before appending")
    if reconciliation["result"] != "NOT_SATISFIED":
        raise TransportError("only fresh NOT_SATISFIED reconciliation may authorize another cycle")
    if len(checkpoint["cycles"]) >= 3:
        raise TransportError("remediation cycle budget is exhausted")
    project = Path(plan["binding"]["project_root"])
    ac_ids = set(_ac_root_ids(plan))
    next_cycle = {
        "cycle": len(checkpoint["cycles"]) + 1,
        "remediation_agent_proposal": _validate_remediation_proposal(
            remediation_agent_proposal, ac_ids, "remediation_agent_proposal"
        ),
        "lead_authorization": _validate_lead_authorization(
            lead_authorization, "lead_authorization"
        ),
        "pre_mutation_anchor_digests": _validate_anchors(
            pre_mutation_anchor_digests,
            project,
            "pre_mutation_anchor_digests",
            require_current_digest=True,
        ),
        "mutation_report": None,
        "primary_verifier_reconciliation": None,
    }
    updated = copy.deepcopy(checkpoint)
    updated["cycles"].append(next_cycle)
    _write_remediation_update(path, checkpoint, updated, plan, approval)


def abandon_remediation(
    project_root: str | Path,
    ticket_path: str | Path,
    safe_abandonment: dict[str, Any],
) -> None:
    """Explicitly establish mutation state without enabling an automatic retry."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        _abandon_remediation_unlocked(project_root, ticket_path, safe_abandonment)


def _abandon_remediation_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    safe_abandonment: dict[str, Any],
) -> None:
    path, checkpoint, plan, approval = _read_remediation(
        project_root,
        ticket_path,
        require_current_pre_mutation_anchors=False,
    )
    _require_no_current_terminal(project_root, ticket_path, plan, approval)
    if checkpoint["state"] != "ACTIVE":
        raise TransportError("remediation checkpoint is already safe-abandoned")
    updated = copy.deepcopy(checkpoint)
    updated["state"] = "SAFE_ABANDONED"
    updated["safe_abandonment"] = safe_abandonment
    _write_remediation_update(path, checkpoint, updated, plan, approval)


def read_remediation_current(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    """Read the one bounded remediation checkpoint; this is not general recovery."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        _path, checkpoint, _plan, _approval = _read_remediation(
            project_root,
            ticket_path,
            require_current_pre_mutation_anchors=False,
        )
        return checkpoint


def _validate_dependency_bindings(value: Any) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(_array(value, "declared_dependency_bindings", maximum=_MAX_ARRAY_ITEMS)):
        item = _object(raw, f"declared_dependency_bindings[{index}]")
        _require_keys(
            item,
            f"declared_dependency_bindings[{index}]",
            {"id", "kind", "identity", "sha256"},
        )
        binding_id = _identifier(item["id"], f"declared_dependency_bindings[{index}].id")
        kind = _text(item["kind"], f"declared_dependency_bindings[{index}].kind", maximum=64)
        if kind not in _DEPENDENCY_KINDS:
            raise TransportError("declared dependency binding kind is invalid")
        identity = _text(
            item["identity"], f"declared_dependency_bindings[{index}].identity", maximum=512
        )
        pair = (kind, identity)
        if pair in seen or any(binding["id"] == binding_id for binding in bindings):
            raise TransportError("declared dependency bindings contain duplicates")
        seen.add(pair)
        bindings.append(
            {
                "id": binding_id,
                "kind": kind,
                "identity": identity,
                "sha256": _sha256(
                    item["sha256"], f"declared_dependency_bindings[{index}].sha256"
                ),
            }
        )
    if not bindings:
        raise TransportError("declared dependency bindings must not be empty")
    if bindings != sorted(bindings, key=lambda item: item["id"]):
        raise TransportError("declared dependency bindings must be sorted by ID")
    return bindings


def _validate_evidence_record(
    value: Any,
    index: int,
    allowed_scenarios: set[tuple[str, str]],
    ac_ids: set[str],
    dependency_bindings: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    label = f"evidence_records[{index}]"
    record = _object(value, label)
    _require_keys(
        record,
        label,
        {
            "id",
            "type",
            "scenario_id",
            "scenario_revision",
            "source",
            "execution_surface",
            "decision_boundary",
            "ac_ids",
            "dependency_binding_refs",
            "recorded_at",
            "reference",
            "type_details",
        },
    )
    evidence_id = _identifier(record["id"], f"{label}.id")
    evidence_type = _text(record["type"], f"{label}.type", maximum=64)
    if evidence_type not in _EVIDENCE_TYPES:
        raise TransportError(f"{label}.type is invalid")
    scenario_id = _identifier(record["scenario_id"], f"{label}.scenario_id")
    scenario_revision = _identifier(record["scenario_revision"], f"{label}.scenario_revision")
    if (scenario_id, scenario_revision) not in allowed_scenarios:
        raise TransportError(f"{label} does not reference an approved Scenario revision")
    evidence_ac_ids = _string_ids(record["ac_ids"], f"{label}.ac_ids")
    if not set(evidence_ac_ids) <= ac_ids:
        raise TransportError(f"{label} references an AC outside the current plan")
    dependency_refs = _string_ids(
        record["dependency_binding_refs"], f"{label}.dependency_binding_refs"
    )
    if not set(dependency_refs) <= dependency_bindings.keys():
        raise TransportError(f"{label}.dependency_binding_refs are unknown")
    type_details = _object(record["type_details"], f"{label}.type_details")
    if evidence_type == "runner-raw":
        _require_keys(type_details, f"{label}.type_details", {"raw_material_ref"})
        normalized_details = {
            "raw_material_ref": _text(
                type_details["raw_material_ref"], f"{label}.type_details.raw_material_ref"
            )
        }
    elif evidence_type == "readiness-fact":
        _require_keys(type_details, f"{label}.type_details", {"runner_raw_refs"})
        normalized_details = {
            "runner_raw_refs": _string_ids(
                type_details["runner_raw_refs"], f"{label}.type_details.runner_raw_refs"
            )
        }
    elif evidence_type == "static-support":
        _require_keys(type_details, f"{label}.type_details", {"source_anchor_refs"})
        normalized_details = {
            "source_anchor_refs": _string_ids(
                type_details["source_anchor_refs"],
                f"{label}.type_details.source_anchor_refs",
            )
        }
    elif evidence_type == "source-conflict/canonical-authority":
        _require_keys(type_details, f"{label}.type_details", {"canonical_source_refs", "conflict_ref"})
        normalized_details = {
            "canonical_source_refs": _string_ids(
                type_details["canonical_source_refs"],
                f"{label}.type_details.canonical_source_refs",
            ),
            "conflict_ref": _text(
                type_details["conflict_ref"], f"{label}.type_details.conflict_ref"
            ),
        }
    elif evidence_type == "source-conflict/product-static":
        _require_keys(type_details, f"{label}.type_details", {"source_anchor_refs", "conflict_ref"})
        normalized_details = {
            "source_anchor_refs": _string_ids(
                type_details["source_anchor_refs"],
                f"{label}.type_details.source_anchor_refs",
            ),
            "conflict_ref": _text(
                type_details["conflict_ref"], f"{label}.type_details.conflict_ref"
            ),
        }
    else:
        _require_keys(
            type_details,
            f"{label}.type_details",
            {"post_approval_observation", "observed_at"},
        )
        if type_details["post_approval_observation"] != "NEW_AFTER_APPROVAL":
            raise TransportError(f"{label}.type_details must declare post-approval observation")
        _timestamp(type_details["observed_at"], f"{label}.type_details.observed_at")
        normalized_details = {
            "post_approval_observation": "NEW_AFTER_APPROVAL",
            "observed_at": type_details["observed_at"],
        }
    _timestamp(record["recorded_at"], f"{label}.recorded_at")
    return {
        "id": evidence_id,
        "type": evidence_type,
        "scenario_id": scenario_id,
        "scenario_revision": scenario_revision,
        "source": _text(record["source"], f"{label}.source", maximum=512),
        "execution_surface": _text(
            record["execution_surface"], f"{label}.execution_surface", maximum=512
        ),
        "decision_boundary": _text(
            record["decision_boundary"], f"{label}.decision_boundary", maximum=512
        ),
        "ac_ids": evidence_ac_ids,
        "dependency_binding_refs": dependency_refs,
        "recorded_at": record["recorded_at"],
        "reference": _text(record["reference"], f"{label}.reference", maximum=512),
        "type_details": normalized_details,
    }


def _validate_evidence_records(
    plan: dict[str, Any],
    dependency_bindings: list[dict[str, Any]],
    value: Any,
) -> list[dict[str, Any]]:
    ac_ids = set(_ac_root_ids(plan))
    allowed_scenarios = {
        (scenario["id"], scenario["revision"])
        for scenario in plan["coverage_gate_envelope"]["scenarios"]
    }
    raw_records = _array(value, "evidence_records", maximum=_MAX_EVIDENCE_RECORDS)
    dependency_by_id = {binding["id"]: binding for binding in dependency_bindings}
    records = [
        _validate_evidence_record(raw, index, allowed_scenarios, ac_ids, dependency_by_id)
        for index, raw in enumerate(
            raw_records
        )
    ]
    if not records:
        raise TransportError("final outcome must include bounded typed evidence records")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise TransportError("evidence records contain duplicate IDs")
    if ids != sorted(ids):
        raise TransportError("evidence records must be sorted by ID")
    records_by_id = {record["id"]: record for record in records}
    for record in records:
        details = record["type_details"]
        if record["type"] == "readiness-fact":
            refs = details["runner_raw_refs"]
            if not set(refs) <= records_by_id.keys() or any(
                records_by_id[ref]["type"] != "runner-raw" for ref in refs
            ):
                raise TransportError("readiness-fact must reference runner-raw evidence")
        elif record["type"] in {
            "static-support",
            "source-conflict/product-static",
        }:
            refs = details["source_anchor_refs"]
            if not set(refs) <= dependency_by_id.keys() or any(
                dependency_by_id[ref]["kind"] != "product-source-anchor" for ref in refs
            ):
                raise TransportError("static evidence must reference product-source anchors")
        elif record["type"] == "source-conflict/canonical-authority":
            refs = details["canonical_source_refs"]
            if not set(refs) <= dependency_by_id.keys() or any(
                dependency_by_id[ref]["kind"] != "canonical-source" for ref in refs
            ):
                raise TransportError("canonical conflict must reference canonical sources")
    return records


def _validate_ac_rows(
    plan: dict[str, Any],
    evidence_records: list[dict[str, Any]],
    value: Any,
) -> list[dict[str, Any]]:
    ac_ids = _ac_root_ids(plan)
    ac_set = set(ac_ids)
    units_by_id = {
        unit["id"]: unit for unit in plan["coverage_gate_envelope"]["units"]
    }
    edges_by_id = {
        edge["id"]: edge for edge in plan["coverage_gate_envelope"]["coverage_edges"]
    }
    scenario_keys = {
        (scenario["id"], scenario["revision"])
        for scenario in plan["coverage_gate_envelope"]["scenarios"]
    }
    evidence_by_id = {record["id"]: record for record in evidence_records}
    verification_root_ids = set(_verification_root_ids(plan))
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(_array(value, "ac_rows", maximum=_MAX_AC_ROWS)):
        label = f"ac_rows[{index}]"
        row = _object(raw, label)
        _require_keys(
            row,
            label,
            {
                "ac_id",
                "verdict",
                "obligation_ids",
                "verification_flow_ids",
                "scenario_revisions",
                "evidence_refs",
            },
        )
        ac_id = _identifier(row["ac_id"], f"{label}.ac_id")
        if ac_id not in ac_set:
            raise TransportError(f"{label}.ac_id is outside the current plan")
        verdict = _text(row["verdict"], f"{label}.verdict", maximum=32)
        if verdict not in _VERDICTS:
            raise TransportError(f"{label}.verdict is invalid")
        obligations = _string_ids(row["obligation_ids"], f"{label}.obligation_ids")
        expected_obligations = {
            unit_id
            for unit_id, unit in units_by_id.items()
            if ac_id in unit["root_ids"]
        }
        if set(obligations) != expected_obligations:
            raise TransportError(f"{label}.obligation_ids are not mapped to its AC")
        flow_ids = _string_ids(
            row["verification_flow_ids"],
            f"{label}.verification_flow_ids",
            allow_empty=True,
        )
        expected_flows = {
            root_id
            for unit_id in obligations
            for root_id in units_by_id[unit_id]["root_ids"]
            if root_id in verification_root_ids
        }
        if set(flow_ids) != expected_flows:
            raise TransportError(f"{label}.verification_flow_ids are not connected to its obligations")
        scenario_revisions: list[dict[str, str]] = []
        seen_scenarios: set[tuple[str, str]] = set()
        for scenario_index, raw_scenario in enumerate(
            _array(row["scenario_revisions"], f"{label}.scenario_revisions")
        ):
            scenario = _object(raw_scenario, f"{label}.scenario_revisions[{scenario_index}]")
            _require_keys(
                scenario,
                f"{label}.scenario_revisions[{scenario_index}]",
                {"scenario_id", "revision"},
            )
            key = (
                _identifier(
                    scenario["scenario_id"],
                    f"{label}.scenario_revisions[{scenario_index}].scenario_id",
                ),
                _identifier(
                    scenario["revision"],
                    f"{label}.scenario_revisions[{scenario_index}].revision",
                ),
            )
            if key not in scenario_keys or key in seen_scenarios:
                raise TransportError(f"{label}.scenario_revisions is invalid")
            seen_scenarios.add(key)
            scenario_revisions.append({"scenario_id": key[0], "revision": key[1]})
        if not scenario_revisions:
            raise TransportError(f"{label}.scenario_revisions must not be empty")
        if scenario_revisions != sorted(
            scenario_revisions, key=lambda item: (item["scenario_id"], item["revision"])
        ):
            raise TransportError(f"{label}.scenario_revisions must be sorted")
        expected_scenarios = {
            (edge["scenario_id"], edge["scenario_revision"])
            for edge in edges_by_id.values()
            if edge["unit_id"] in obligations
        }
        if {
            (scenario["scenario_id"], scenario["revision"])
            for scenario in scenario_revisions
        } != expected_scenarios:
            raise TransportError(f"{label}.scenario_revisions are not connected to its obligations")
        evidence_refs = _string_ids(row["evidence_refs"], f"{label}.evidence_refs")
        if not set(evidence_refs) <= evidence_by_id.keys():
            raise TransportError(f"{label}.evidence_refs reference unknown evidence")
        if any(ac_id not in evidence_by_id[evidence_id]["ac_ids"] for evidence_id in evidence_refs):
            raise TransportError(f"{label}.evidence_refs are not bound to its AC")
        scenario_set = {
            (scenario["scenario_id"], scenario["revision"])
            for scenario in scenario_revisions
        }
        if any(
            (
                evidence_by_id[evidence_id]["scenario_id"],
                evidence_by_id[evidence_id]["scenario_revision"],
            )
            not in scenario_set
            for evidence_id in evidence_refs
        ):
            raise TransportError(f"{label}.evidence_refs are not bound to its Scenario revisions")
        rows.append(
            {
                "ac_id": ac_id,
                "verdict": verdict,
                "obligation_ids": obligations,
                "verification_flow_ids": flow_ids,
                "scenario_revisions": scenario_revisions,
                "evidence_refs": evidence_refs,
            }
        )
    if [row["ac_id"] for row in rows] != ac_ids:
        raise TransportError("final outcome must contain exactly one ordered row per Markdown AC")
    return rows


def _validate_final_remediation_lineage(
    value: Any,
    plan: dict[str, Any],
    approval: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if value is None:
        return None
    checkpoint = _validate_remediation(
        value,
        plan,
        approval,
        require_current_pre_mutation_anchors=False,
    )
    if checkpoint["state"] != "ACTIVE":
        raise TransportError("final remediation lineage must be the active compact lineage")
    evidence_by_id = {record["id"]: record for record in evidence_records}
    target_ac_ids = set(checkpoint["failure_origin"]["target_ac_ids"])
    origin_refs = checkpoint["failure_origin"]["direct_evidence_refs"]
    if not set(origin_refs) <= evidence_by_id.keys() or any(
        evidence_by_id[reference]["type"] != "direct-evidence"
        or not target_ac_ids <= set(evidence_by_id[reference]["ac_ids"])
        for reference in origin_refs
    ):
        raise TransportError("remediation failure origin must close to matching direct evidence")
    for cycle in checkpoint["cycles"]:
        if cycle["mutation_report"] is None:
            raise TransportError("terminal remediation lineage has an incomplete mutation report")
        reconciliation = cycle["primary_verifier_reconciliation"]
        if reconciliation is None:
            raise TransportError("terminal remediation lineage has an incomplete reconciliation")
        references = reconciliation["direct_evidence_refs"]
        target_ids = set(reconciliation["target_ac_ids"])
        affected_ids = set(reconciliation["affected_ac_ids"])
        reported_at = _timestamp(
            cycle["mutation_report"]["reported_at"],
            f"remediation cycle {cycle['cycle']} mutation reported_at",
        )
        reconciled_at = _timestamp(
            reconciliation["reconciled_at"],
            f"remediation cycle {cycle['cycle']} reconciled_at",
        )
        if not set(references) <= evidence_by_id.keys() or any(
            evidence_by_id[reference]["type"] != "direct-evidence"
            or not target_ids <= set(evidence_by_id[reference]["ac_ids"])
            or not affected_ids <= set(evidence_by_id[reference]["ac_ids"])
            for reference in references
        ):
            raise TransportError("remediation reconciliation must close to matching direct evidence")
        if any(
            not reported_at
            < _timestamp(
                evidence_by_id[reference]["type_details"]["observed_at"],
                f"remediation reconciliation evidence {reference} observed_at",
            )
            <= reconciled_at
            for reference in references
        ):
            raise TransportError(
                "remediation reconciliation evidence must be observed after mutation and no later than reconciliation"
            )
    return checkpoint


def _validate_final_outcome(
    value: Any,
    expected_binding: dict[str, str],
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    outcome = _object(value, "final outcome")
    _require_keys(
        outcome,
        "final outcome",
        {
            "schema",
            "verification_execution_id",
            "binding",
            "plan_fp",
            "gate_approval_id",
            "approval_projection_sha256",
            "declared_dependency_bindings",
            "evidence_records",
            "ac_rows",
            "closure",
            "final_remediation_lineage",
            "published_at",
        },
    )
    if outcome["schema"] != FINAL_SCHEMA:
        raise TransportError("final outcome schema is invalid")
    if outcome["verification_execution_id"] != plan["verification_execution_id"]:
        raise TransportError("final outcome execution ID does not match the plan")
    binding = _validate_binding(outcome["binding"], expected_binding)
    expected_chain = _plan_and_approval_binding(plan, approval)
    if (
        outcome["plan_fp"] != expected_chain["plan_fp"]
        or outcome["gate_approval_id"] != expected_chain["gate_approval_id"]
        or outcome["approval_projection_sha256"]
        != expected_chain["approval_projection_sha256"]
    ):
        raise TransportError("final outcome does not match its plan and approval chain")
    dependency_bindings = _validate_dependency_bindings(
        outcome["declared_dependency_bindings"]
    )
    evidence_records = _validate_evidence_records(
        plan, dependency_bindings, outcome["evidence_records"]
    )
    approved_at = _timestamp(approval["approved_at"], "approved_at")
    published_at = _timestamp(outcome["published_at"], "published_at")
    for record in evidence_records:
        if record["type"] != "direct-evidence":
            continue
        observed_at = _timestamp(
            record["type_details"]["observed_at"],
            f"direct evidence {record['id']} observed_at",
        )
        if not approved_at < observed_at <= published_at:
            raise TransportError(
                "direct evidence must be observed after approval and no later than publication"
            )
    ac_rows = _validate_ac_rows(plan, evidence_records, outcome["ac_rows"])
    closure = _object(outcome["closure"], "closure")
    _require_keys(closure, "closure", {"result", "closed_at"})
    closure_result = _text(closure["result"], "closure.result", maximum=32)
    if closure_result not in {"COMPLETE", "BLOCKED"}:
        raise TransportError("closure.result is invalid")
    _timestamp(closure["closed_at"], "closure.closed_at")
    return {
        "schema": FINAL_SCHEMA,
        "verification_execution_id": plan["verification_execution_id"],
        "binding": binding,
        "plan_fp": expected_chain["plan_fp"],
        "gate_approval_id": expected_chain["gate_approval_id"],
        "approval_projection_sha256": expected_chain["approval_projection_sha256"],
        "declared_dependency_bindings": dependency_bindings,
        "evidence_records": evidence_records,
        "ac_rows": ac_rows,
        "closure": {"result": closure_result, "closed_at": closure["closed_at"]},
        "final_remediation_lineage": _validate_final_remediation_lineage(
            outcome["final_remediation_lineage"], plan, approval, evidence_records
        ),
        "published_at": outcome["published_at"],
    }


def _active_remediation_checkpoint(
    project_root: str | Path,
    ticket_path: str | Path,
    plan: dict[str, Any],
    approval: dict[str, Any],
) -> tuple[Path, dict[str, Any]] | None:
    path = _remediation_path(project_root, ticket_path, create=False)
    try:
        raw = _read_artifact(path, "remediation checkpoint")
    except ArtifactNotFound:
        return None
    if raw.get("verification_execution_id") != plan["verification_execution_id"]:
        return None
    checkpoint = _validate_remediation(
        raw,
        plan,
        approval,
        require_current_pre_mutation_anchors=False,
    )
    return path, checkpoint


def publish_final_outcome(
    project_root: str | Path,
    ticket_path: str | Path,
    final_outcome: dict[str, Any],
) -> None:
    """Publish one complete terminal package without interpreting its verdicts."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        published_at = _publish_final_outcome_unlocked(project_root, ticket_path, final_outcome)
    try:
        mark_route_navigation_terminal(project_root, ticket_path, published_at)
    except TransportError:
        # Route-sidecar absence, malformedness, or cleanup trouble is ambiguous
        # and never changes terminal verification authority.
        pass


def _publish_final_outcome_unlocked(
    project_root: str | Path,
    ticket_path: str | Path,
    final_outcome: dict[str, Any],
) -> str:
    plan, approval = _read_current_plan_and_approval(project_root, ticket_path)
    _require_no_current_terminal(project_root, ticket_path, plan, approval)
    binding = _binding(project_root, ticket_path)
    remediation = _active_remediation_checkpoint(
        project_root, ticket_path, plan, approval
    )
    normalized = _validate_final_outcome(final_outcome, binding, plan, approval)
    if remediation is not None:
        remediation_path, checkpoint = remediation
        if checkpoint["state"] == "ACTIVE":
            if normalized["final_remediation_lineage"] != checkpoint:
                raise TransportError(
                    "terminal outcome must incorporate the active remediation checkpoint"
                )
        elif normalized["final_remediation_lineage"] is not None:
            raise TransportError("safe-abandoned remediation is not terminal lineage")
    elif normalized["final_remediation_lineage"] is not None:
        raise TransportError("final remediation lineage has no current checkpoint")
    path = _final_path(project_root, ticket_path, create=True)
    _write_artifact(path, normalized, "final outcome")
    if remediation is not None:
        remediation_path, checkpoint = remediation
        if checkpoint["state"] == "ACTIVE":
            _remove_artifact(
                remediation_path,
                "remediation checkpoint",
            )
    return normalized["published_at"]


def read_final_outcome(
    project_root: str | Path,
    ticket_path: str | Path,
) -> dict[str, Any]:
    """Read the one complete terminal package after structural chain validation."""

    key = ticket_key(project_root, ticket_path)
    with _verification_write_lock(key, create=False):
        plan, approval = _read_current_plan_and_approval(project_root, ticket_path)
        binding = _binding(project_root, ticket_path)
        path = _final_path(project_root, ticket_path, create=False)
        return _validate_final_outcome(
            _read_artifact(path, "final outcome"), binding, plan, approval
        )
