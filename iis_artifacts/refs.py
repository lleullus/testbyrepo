"""Opaque, non-content-derived references to executor-owned fixed snapshots."""
from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

SNAPSHOT_ID = re.compile(r"^snap-[0-9a-f]{32}$")


class RefError(ValueError):
    pass


def validate_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise RefError("reference path must be a nonempty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RefError("reference path must stay inside its snapshot")
    return path.as_posix()


def validate_ref(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise RefError("snapshot reference must be an object")
    if set(value) != {"snapshot", "path"}:
        raise RefError("snapshot reference needs exactly snapshot and path")
    snapshot = value.get("snapshot")
    path = value.get("path")
    if not isinstance(snapshot, str) or SNAPSHOT_ID.fullmatch(snapshot) is None:
        raise RefError("invalid snapshot id")
    if not isinstance(path, str):
        raise RefError("reference path must be a string")
    return {"snapshot": snapshot, "path": validate_relative_path(path)}


def ref(snapshot: str, path: str) -> dict[str, str]:
    return validate_ref({"snapshot": snapshot, "path": path})


def source_refs_from_section(body: str, label: str) -> list[dict[str, str]]:
    blocks = re.findall(r"^\x60\x60\x60iis-sources\s*\n(.*?)^\x60\x60\x60\s*$", body, re.M | re.S)
    if len(blocks) != 1:
        raise RefError(f"{label} requires one iis-sources JSON block")
    try:
        value = json.loads(blocks[0])
    except json.JSONDecodeError as exc:
        raise RefError(f"invalid {label} JSON") from exc
    if not isinstance(value, list) or not value:
        raise RefError(f"{label} needs at least one source reference")
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in value:
        ref_value = validate_ref(item)
        key = (ref_value["snapshot"], ref_value["path"])
        if key in seen:
            raise RefError(f"duplicate {label} source reference")
        seen.add(key)
        result.append(ref_value)
    return result
