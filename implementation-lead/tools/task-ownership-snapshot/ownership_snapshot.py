#!/usr/bin/env python3
"""Physical task ownership snapshots and frozen-envelope scope comparison.

This tool deliberately knows nothing about language projects, commands, coverage, or technical
reports. Its artifacts do not identify mutation actors and must never be used as product verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "task-ownership-snapshot-v1"
DELTA_VERSION = "task-ownership-delta-v2"
_TOP_LEVEL_FIELDS = frozenset(
    {
        "schemaVersion",
        "ownershipOnly",
        "projectRoot",
        "capturedAt",
        "identity",
        "policy",
        "entries",
    }
)
_FIXED_POLICY = {
    "gitMetadata": "excluded",
    "ignoredAndUntracked": "included",
    "symlinks": "target-and-mode",
    "regularFiles": "sha256-size-and-mode",
    "directories": "mode",
    "stabilityPasses": 2,
}
_POLICY_FIELDS = frozenset({*_FIXED_POLICY, "exclusions"})
_SHA256_PATTERN = re.compile(r"[a-f0-9]{64}")
_IDENTITY_PATTERN = re.compile(r"sha256:[a-f0-9]{64}")


class SnapshotError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _is_excluded(relative_path: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        if _segment_glob_match(relative_path, pattern):
            return True
    return False


def _segment_glob_match(relative_path: str, pattern: str) -> bool:
    """Match POSIX paths without allowing `*` to cross `/`; `**` is recursive."""
    normalized = pattern.rstrip("/")
    if normalized.endswith("/**") and relative_path == normalized[:-3].rstrip("/"):
        return True
    expression: list[str] = ["^"]
    index = 0
    while index < len(normalized):
        character = normalized[index]
        if character == "*":
            if index + 1 < len(normalized) and normalized[index + 1] == "*":
                index += 2
                if index < len(normalized) and normalized[index] == "/":
                    expression.append("(?:.*/)?")
                    index += 1
                else:
                    expression.append(".*")
                continue
            expression.append("[^/]*")
        elif character == "?":
            expression.append("[^/]")
        else:
            expression.append(re.escape(character))
        index += 1
    expression.append("$")
    return re.match("".join(expression), relative_path) is not None


def _file_entry(path: Path, mode: int) -> dict[str, Any]:
    before = path.stat(follow_symlinks=False)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    after = path.stat(follow_symlinks=False)
    stable_fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
        raise SnapshotError("SOURCE_CHANGED_DURING_CAPTURE", f"file changed while hashing: {path}")
    return {
        "kind": "file",
        "mode": stat.S_IMODE(mode),
        "size": after.st_size,
        "sha256": digest.hexdigest(),
    }


def _scan_tree(project_root: Path, exclusions: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}

    def visit(directory: Path, relative_directory: str = "") -> None:
        try:
            children = sorted(os.scandir(directory), key=lambda item: os.fsencode(item.name))
        except OSError as exc:
            raise SnapshotError("SOURCE_CHANGED_DURING_CAPTURE", f"cannot scan {directory}: {exc}") from exc
        for child in children:
            relative = f"{relative_directory}/{child.name}" if relative_directory else child.name
            if relative == ".git" or relative.startswith(".git/") or _is_excluded(relative, exclusions):
                continue
            path = Path(child.path)
            try:
                metadata = child.stat(follow_symlinks=False)
            except OSError as exc:
                raise SnapshotError(
                    "SOURCE_CHANGED_DURING_CAPTURE", f"cannot stat {relative}: {exc}"
                ) from exc
            mode = metadata.st_mode
            if stat.S_ISLNK(mode):
                try:
                    target = os.readlink(path)
                except OSError as exc:
                    raise SnapshotError(
                        "SOURCE_CHANGED_DURING_CAPTURE", f"cannot read symlink {relative}: {exc}"
                    ) from exc
                entries[relative] = {
                    "kind": "symlink",
                    "mode": stat.S_IMODE(mode),
                    "target": target,
                }
            elif stat.S_ISDIR(mode):
                entries[relative] = {"kind": "directory", "mode": stat.S_IMODE(mode)}
                visit(path, relative)
            elif stat.S_ISREG(mode):
                entries[relative] = _file_entry(path, mode)
            else:
                entries[relative] = {"kind": "special", "mode": stat.S_IMODE(mode)}

    visit(project_root)
    return entries


def _workspace_identity(entries: Mapping[str, Mapping[str, Any]], exclusions: tuple[str, ...]) -> str:
    identity_input = {"entries": entries, "exclusions": list(exclusions)}
    return f"sha256:{hashlib.sha256(_canonical_json(identity_input)).hexdigest()}"


def _invalid_snapshot(message: str) -> SnapshotError:
    return SnapshotError("INVALID_SNAPSHOT", message)


def _canonical_root(value: Any) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise _invalid_snapshot("projectRoot must be a non-empty absolute path")
    path = Path(value)
    if not path.is_absolute():
        raise _invalid_snapshot("projectRoot must be absolute")
    try:
        resolved = str(path.resolve(strict=False))
    except (OSError, RuntimeError) as exc:
        raise _invalid_snapshot(f"projectRoot cannot be canonicalized: {exc}") from exc
    if resolved != value:
        raise _invalid_snapshot("projectRoot is not canonical")
    return value


def _expected_root(value: Path | str) -> str:
    if not isinstance(value, (Path, str)):
        raise SnapshotError("INVALID_PROJECT_ROOT", "expected_project_root must be a path")
    try:
        return str(Path(value).resolve(strict=False))
    except (OSError, RuntimeError) as exc:
        raise SnapshotError(
            "INVALID_PROJECT_ROOT", f"expected_project_root cannot be canonicalized: {exc}"
        ) from exc


def _validate_captured_at(value: Any) -> str:
    if not isinstance(value, str):
        raise _invalid_snapshot("capturedAt must be a UTC ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise _invalid_snapshot("capturedAt must be a UTC ISO-8601 timestamp") from exc
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timezone.utc.utcoffset(parsed)
        or parsed.isoformat() != value
    ):
        raise _invalid_snapshot("capturedAt must be a canonical UTC ISO-8601 timestamp")
    return value


def _validate_patterns(value: Any, *, normalized: bool) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise _invalid_snapshot("policy.exclusions must be an array")
    patterns: list[str] = []
    for index, pattern in enumerate(value):
        if not isinstance(pattern, str) or not pattern or "\x00" in pattern:
            raise _invalid_snapshot(f"policy.exclusions[{index}] is invalid")
        patterns.append(pattern)
    if normalized and patterns != sorted(set(patterns)):
        raise _invalid_snapshot("policy.exclusions must be sorted and unique")
    return tuple(patterns)


def _validate_policy(value: Any) -> tuple[dict[str, Any], tuple[str, ...]]:
    if not isinstance(value, Mapping) or set(value) != _POLICY_FIELDS:
        raise _invalid_snapshot("policy fields are invalid")
    for field, expected in _FIXED_POLICY.items():
        if value[field] != expected or type(value[field]) is not type(expected):
            raise _invalid_snapshot(f"policy.{field} is invalid")
    exclusions = _validate_patterns(value["exclusions"], normalized=True)
    return (
        {
            "gitMetadata": _FIXED_POLICY["gitMetadata"],
            "ignoredAndUntracked": _FIXED_POLICY["ignoredAndUntracked"],
            "symlinks": _FIXED_POLICY["symlinks"],
            "regularFiles": _FIXED_POLICY["regularFiles"],
            "directories": _FIXED_POLICY["directories"],
            "exclusions": list(exclusions),
            "stabilityPasses": _FIXED_POLICY["stabilityPasses"],
        },
        exclusions,
    )


def _validate_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise _invalid_snapshot("entry paths must be non-empty strings")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise _invalid_snapshot("entry paths must be valid UTF-8") from exc
    segments = value.split("/")
    if value.startswith("/") or any(segment in {"", ".", ".."} for segment in segments):
        raise _invalid_snapshot(f"entry path is not canonical: {value!r}")
    if value == ".git" or value.startswith(".git/"):
        raise _invalid_snapshot("entries cannot contain excluded .git metadata")
    return value


def _validate_mode(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0o7777:
        raise _invalid_snapshot(f"entry mode is invalid: {path}")
    return value


def _validate_entry(path: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise _invalid_snapshot(f"entry must be an object: {path}")
    kind = value.get("kind")
    if not isinstance(kind, str):
        raise _invalid_snapshot(f"entry kind is invalid: {path}")
    fields_by_kind = {
        "directory": {"kind", "mode"},
        "special": {"kind", "mode"},
        "symlink": {"kind", "mode", "target"},
        "file": {"kind", "mode", "size", "sha256"},
    }
    expected_fields = fields_by_kind.get(kind)
    if expected_fields is None or set(value) != expected_fields:
        raise _invalid_snapshot(f"entry fields are invalid: {path}")
    mode = _validate_mode(value["mode"], path)
    if kind in {"directory", "special"}:
        return {"kind": kind, "mode": mode}
    if kind == "symlink":
        target = value["target"]
        if not isinstance(target, str) or not target or "\x00" in target:
            raise _invalid_snapshot(f"symlink target is invalid: {path}")
        try:
            target.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise _invalid_snapshot(f"symlink target must be valid UTF-8: {path}") from exc
        return {"kind": "symlink", "mode": mode, "target": target}
    size = value["size"]
    digest = value["sha256"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise _invalid_snapshot(f"file size is invalid: {path}")
    if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
        raise _invalid_snapshot(f"file digest is invalid: {path}")
    return {"kind": "file", "mode": mode, "size": size, "sha256": digest}


def _validate_entries(value: Any, exclusions: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        raise _invalid_snapshot("entries must be an object")
    entries: dict[str, dict[str, Any]] = {}
    for raw_path, raw_entry in value.items():
        path = _validate_relative_path(raw_path)
        if _is_excluded(path, exclusions):
            raise _invalid_snapshot(f"entry violates the exclusion policy: {path}")
        entries[path] = _validate_entry(path, raw_entry)
    for path in entries:
        segments = path.split("/")
        for end in range(1, len(segments)):
            parent = "/".join(segments[:end])
            parent_entry = entries.get(parent)
            if parent_entry is None or parent_entry["kind"] != "directory":
                raise _invalid_snapshot(f"entry has no directory parent: {path}")
    return entries


def validate_snapshot(
    value: Any, expected_project_root: Path | str | None = None
) -> dict[str, Any]:
    """Validate and normalize one in-memory ownership snapshot.

    The identity authenticates the physical manifest and exclusion list. The remaining fixed
    fields are validated independently so a caller cannot extend or reinterpret the v1 schema.
    """
    if not isinstance(value, Mapping) or set(value) != _TOP_LEVEL_FIELDS:
        raise _invalid_snapshot("top-level fields are invalid")
    if value["schemaVersion"] != SCHEMA_VERSION or type(value["schemaVersion"]) is not str:
        raise _invalid_snapshot(f"schemaVersion must be {SCHEMA_VERSION}")
    if value["ownershipOnly"] is not True:
        raise _invalid_snapshot("ownershipOnly must be true")
    project_root = _canonical_root(value["projectRoot"])
    if expected_project_root is not None and project_root != _expected_root(expected_project_root):
        raise SnapshotError(
            "PROJECT_ROOT_MISMATCH", "snapshot projectRoot differs from expected_project_root"
        )
    captured_at = _validate_captured_at(value["capturedAt"])
    policy, exclusions = _validate_policy(value["policy"])
    entries = _validate_entries(value["entries"], exclusions)
    identity = value["identity"]
    if not isinstance(identity, str) or _IDENTITY_PATTERN.fullmatch(identity) is None:
        raise _invalid_snapshot("identity must be a lowercase SHA-256 identity")
    try:
        expected_identity = _workspace_identity(entries, exclusions)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise _invalid_snapshot(f"identity input is not canonical JSON: {exc}") from exc
    if identity != expected_identity:
        raise _invalid_snapshot("snapshot identity mismatch")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "ownershipOnly": True,
        "projectRoot": project_root,
        "capturedAt": captured_at,
        "identity": identity,
        "policy": policy,
        "entries": entries,
    }


def capture(project_root: Path | str, *, exclusions: Iterable[str] = ()) -> dict[str, Any]:
    root = Path(project_root).resolve(strict=True)
    if not root.is_dir():
        raise SnapshotError("INVALID_PROJECT_ROOT", f"not a directory: {root}")
    try:
        raw_exclusions = list(exclusions)
    except TypeError as exc:
        raise SnapshotError("INVALID_EXCLUSIONS", "exclusions must be iterable") from exc
    normalized_exclusions = tuple(
        sorted(set(_validate_patterns(raw_exclusions, normalized=False)))
    )
    first = _scan_tree(root, normalized_exclusions)
    second = _scan_tree(root, normalized_exclusions)
    if first != second:
        raise SnapshotError(
            "SOURCE_CHANGED_DURING_CAPTURE",
            "physical manifests differed across the two stability passes",
        )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "ownershipOnly": True,
        "projectRoot": str(root),
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "identity": _workspace_identity(second, normalized_exclusions),
        "policy": {
            "gitMetadata": "excluded",
            "ignoredAndUntracked": "included",
            "symlinks": "target-and-mode",
            "regularFiles": "sha256-size-and-mode",
            "directories": "mode",
            "exclusions": list(normalized_exclusions),
            "stabilityPasses": 2,
        },
        "entries": second,
    }


def write_immutable(snapshot: Mapping[str, Any], output: Path | str) -> Path:
    destination = Path(output).resolve()
    root = Path(str(snapshot["projectRoot"])).resolve()
    if destination == root or destination.is_relative_to(root):
        raise SnapshotError("SNAPSHOT_INSIDE_PROJECT", "snapshot artifacts must be outside projectRoot")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n"
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    except FileExistsError as exc:
        raise SnapshotError("IMMUTABLE_ARTIFACT_EXISTS", f"refusing to overwrite {destination}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination


def read_snapshot(
    path: Path | str, expected_project_root: Path | str | None = None
) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_snapshot(value, expected_project_root=expected_project_root)


def path_matches_any(relative_path: str, patterns: Iterable[str]) -> bool:
    """Return whether a canonical project-relative path matches any owner path pattern."""
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or "\x00" in relative_path
        or relative_path.startswith("/")
        or any(segment in {"", ".", ".."} for segment in relative_path.split("/"))
    ):
        raise SnapshotError("INVALID_PATH", "relative_path must be canonical and project-relative")
    if isinstance(patterns, (str, bytes)):
        raise SnapshotError("INVALID_PATH_PATTERN", "patterns must be an iterable of strings")
    try:
        normalized_patterns = tuple(patterns)
    except TypeError as exc:
        raise SnapshotError("INVALID_PATH_PATTERN", "patterns must be iterable") from exc
    for index, pattern in enumerate(normalized_patterns):
        if not isinstance(pattern, str) or not pattern or "\x00" in pattern:
            raise SnapshotError("INVALID_PATH_PATTERN", f"patterns[{index}] is invalid")
    return _is_excluded(relative_path, normalized_patterns)


def _allowed(relative_path: str, patterns: tuple[str, ...]) -> bool:
    """Compatibility shim; owner integrations must use :func:`path_matches_any`."""
    return path_matches_any(relative_path, patterns)


def compare(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    allowed_mutation_scopes: Iterable[str],
) -> dict[str, Any]:
    validated_before = validate_snapshot(before)
    validated_after = validate_snapshot(after)
    if validated_before["projectRoot"] != validated_after["projectRoot"]:
        raise SnapshotError("PROJECT_ROOT_MISMATCH", "before and after project roots differ")
    if validated_before["policy"] != validated_after["policy"]:
        raise SnapshotError("SNAPSHOT_POLICY_MISMATCH", "before and after snapshot policies differ")
    before_entries = validated_before["entries"]
    after_entries = validated_after["entries"]
    before_paths = set(before_entries)
    after_paths = set(after_entries)
    created = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    modified = sorted(
        path for path in before_paths & after_paths if before_entries[path] != after_entries[path]
    )
    changed_paths = sorted(set(created + deleted + modified))
    allowed_patterns = tuple(sorted(set(allowed_mutation_scopes)))
    in_scope = [path for path in changed_paths if path_matches_any(path, allowed_patterns)]
    out_of_scope = [
        path for path in changed_paths if not path_matches_any(path, allowed_patterns)
    ]
    rename_candidates: list[dict[str, str]] = []
    for old_path in deleted:
        old = before_entries[old_path]
        if old.get("kind") == "directory":
            continue
        for new_path in created:
            new = after_entries[new_path]
            comparable_fields = {"kind", "mode", "size", "sha256", "target"}
            if {key: old.get(key) for key in comparable_fields} == {
                key: new.get(key) for key in comparable_fields
            }:
                rename_candidates.append({"from": old_path, "to": new_path})
    return {
        "schemaVersion": DELTA_VERSION,
        "ownershipOnly": True,
        "projectRoot": validated_before["projectRoot"],
        "beforeIdentity": validated_before["identity"],
        "afterIdentity": validated_after["identity"],
        "allowedMutationScopes": list(allowed_patterns),
        "created": created,
        "modified": modified,
        "deleted": deleted,
        "changedPaths": changed_paths,
        "inScopePaths": in_scope,
        "renameCandidates": rename_candidates,
        "outOfScopePaths": out_of_scope,
        "scopeState": "WITHIN_ENVELOPE" if not out_of_scope else "OUTSIDE_ENVELOPE",
        "actorAttribution": "NOT_ESTABLISHED",
    }


def _load_patterns(values: list[str]) -> tuple[str, ...]:
    return tuple(pattern for value in values for pattern in value.split(",") if pattern)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture")
    capture_parser.add_argument("--project-root", required=True)
    capture_parser.add_argument("--output", required=True)
    capture_parser.add_argument("--exclude", action="append", default=[])
    compare_parser = commands.add_parser("compare")
    compare_parser.add_argument("--before", required=True)
    compare_parser.add_argument("--after", required=True)
    compare_parser.add_argument("--allow", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            snapshot = capture(args.project_root, exclusions=_load_patterns(args.exclude))
            path = write_immutable(snapshot, args.output)
            print(json.dumps({"snapshot": str(path), "identity": snapshot["identity"]}))
        else:
            delta = compare(
                read_snapshot(args.before),
                read_snapshot(args.after),
                allowed_mutation_scopes=_load_patterns(args.allow),
            )
            print(json.dumps(delta, ensure_ascii=False, indent=2, sort_keys=True))
            if delta["scopeState"] != "WITHIN_ENVELOPE":
                return 10
    except (OSError, ValueError, SnapshotError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
