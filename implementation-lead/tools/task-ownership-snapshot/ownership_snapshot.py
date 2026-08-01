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


def capture(project_root: Path | str, *, exclusions: Iterable[str] = ()) -> dict[str, Any]:
    root = Path(project_root).resolve(strict=True)
    if not root.is_dir():
        raise SnapshotError("INVALID_PROJECT_ROOT", f"not a directory: {root}")
    normalized_exclusions = tuple(sorted(set(exclusions)))
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


def read_snapshot(path: Path | str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("schemaVersion") != SCHEMA_VERSION or value.get("ownershipOnly") is not True:
        raise SnapshotError("INVALID_SNAPSHOT", f"not an ownership-only v1 snapshot: {path}")
    expected = _workspace_identity(value.get("entries", {}), tuple(value["policy"]["exclusions"]))
    if value.get("identity") != expected:
        raise SnapshotError("INVALID_SNAPSHOT", f"snapshot identity mismatch: {path}")
    return value


def _allowed(relative_path: str, patterns: tuple[str, ...]) -> bool:
    return any(_is_excluded(relative_path, (pattern,)) for pattern in patterns)


def compare(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    allowed_mutation_scopes: Iterable[str],
) -> dict[str, Any]:
    if before.get("schemaVersion") != SCHEMA_VERSION or after.get("schemaVersion") != SCHEMA_VERSION:
        raise SnapshotError("INVALID_SNAPSHOT", "both inputs must be v1 ownership snapshots")
    if before.get("ownershipOnly") is not True or after.get("ownershipOnly") is not True:
        raise SnapshotError("INVALID_SNAPSHOT", "ownershipOnly must be true")
    if before.get("projectRoot") != after.get("projectRoot"):
        raise SnapshotError("PROJECT_ROOT_MISMATCH", "before and after project roots differ")
    if before.get("policy") != after.get("policy"):
        raise SnapshotError("SNAPSHOT_POLICY_MISMATCH", "before and after snapshot policies differ")
    before_entries = _mapping_entries(before.get("entries"))
    after_entries = _mapping_entries(after.get("entries"))
    before_paths = set(before_entries)
    after_paths = set(after_entries)
    created = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    modified = sorted(
        path for path in before_paths & after_paths if before_entries[path] != after_entries[path]
    )
    changed_paths = sorted(set(created + deleted + modified))
    allowed_patterns = tuple(sorted(set(allowed_mutation_scopes)))
    in_scope = [path for path in changed_paths if _allowed(path, allowed_patterns)]
    out_of_scope = [path for path in changed_paths if not _allowed(path, allowed_patterns)]
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
        "projectRoot": before["projectRoot"],
        "beforeIdentity": before["identity"],
        "afterIdentity": after["identity"],
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


def _mapping_entries(value: Any) -> Mapping[str, Mapping[str, Any]]:
    if not isinstance(value, Mapping):
        raise SnapshotError("INVALID_SNAPSHOT", "entries must be an object")
    return value


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
