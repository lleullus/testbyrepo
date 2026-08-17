from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import re

from .model import Artifact, ArtifactKind

ID_PATTERN = re.compile(r"(?i)\b(?:WP|INC|TKT|TICKET|SPEC)[-_]\d{1,6}\b")
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
STATUS_ALIASES = {
    "complete": "done",
    "completed": "done",
    "verified": "done",
    "closed": "done",
    "ready for matt": "ready-for-matt",
    "ready_for_matt": "ready-for-matt",
    "readyformatt": "ready-for-matt",
    "ready-for-matt": "ready-for-matt",
    "in progress": "active",
    "in-progress": "active",
    "current": "active",
    "selected": "active",
    "confirmed": "confirmed",
    "approved": "approved",
    "scoped": "scoped",
    "superseded": "superseded",
    "blocked": "blocked",
    "draft": "draft",
    "ready": "ready",
    "done": "done",
    "active": "active",
    "provisional": "provisional",
    "deferred": "deferred",
    "rejected": "rejected",
}
KNOWN_KEYS = {
    "status",
    "id",
    "identifier",
    "scope",
    "scope_id",
    "work_package",
    "work_package_id",
    "parent_work_package",
    "source_work_package",
    "increment",
    "increment_id",
    "selected_increment",
    "current_increment",
    "source_increment",
    "parent_increment",
    "suggested_work_slug",
    "work_slug",
    "title",
    "name",
    "revision",
}


def normalize_key(value: str) -> str:
    value = value.strip().lower().replace("`", "")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    clean = value.strip().strip("`*_[]()\"").lower()
    clean = re.sub(r"\s+", " ", clean)
    if clean in STATUS_ALIASES:
        return STATUS_ALIASES[clean]
    hyphenated = clean.replace("_", "-").replace(" ", "-")
    return STATUS_ALIASES.get(hyphenated, hyphenated or None)


def canonical_id(value: str | None) -> str | None:
    if not value:
        return None
    match = ID_PATTERN.search(value)
    if not match:
        return None
    result = match.group(0).upper().replace("_", "-")
    if result.startswith("TICKET-"):
        return "TKT-" + result.split("-", 1)[1]
    return result


def _extract_metadata(text: str) -> dict[str, str]:
    lines = text.splitlines()
    metadata: dict[str, str] = {}

    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            _consume_metadata_line(line, metadata, front_matter=True)

    for line in lines[:240]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) >= 2 and not all(re.fullmatch(r":?-{3,}:?", cell or "-") for cell in cells[:2]):
                key = normalize_key(cells[0])
                if key in KNOWN_KEYS or any(token in key for token in ("status", "increment", "work_package", "slug")):
                    metadata.setdefault(key, cells[1].strip())
            continue
        _consume_metadata_line(stripped, metadata, front_matter=False)

    return metadata


def _consume_metadata_line(line: str, metadata: dict[str, str], front_matter: bool) -> None:
    stripped = line.strip()
    if stripped.startswith(("- ", "* ")):
        stripped = stripped[2:].strip()
    match = re.match(r"^([A-Za-z][A-Za-z0-9 _/-]{0,48})\s*:\s*(.+?)\s*$", stripped)
    if not match:
        return
    key = normalize_key(match.group(1))
    if front_matter or key in KNOWN_KEYS or any(token in key for token in ("status", "increment", "work_package", "slug")):
        metadata.setdefault(key, match.group(2).strip())


def _classify(path: Path, text: str) -> ArtifactKind:
    upper_name = path.name.upper()
    upper_parts = "/".join(part.upper() for part in path.parts)
    if "SCOPE-SHAPING-RESULT" in upper_name or re.fullmatch(r"SHAPE-\d+\.MD", upper_name):
        return ArtifactKind.SCOPE
    if "WORK-PACKAGE" in upper_name or re.search(r"\bWP-\d+", upper_name):
        return ArtifactKind.WORK_PACKAGE
    if "INCREMENT" in upper_name or re.search(r"\bINC-\d+", upper_name):
        return ArtifactKind.INCREMENT
    if "TICKET" in upper_name or re.search(r"\bTKT-\d+", upper_name) or "/TICKETS/" in upper_parts:
        return ArtifactKind.TICKET
    if upper_name.startswith("SPEC") or "/SPEC" in upper_parts:
        return ArtifactKind.SPEC

    heading = "\n".join(text.splitlines()[:20]).upper()
    if "SCOPE SHAPING RESULT" in heading:
        return ArtifactKind.SCOPE
    if re.search(r"#\s+.*WORK PACKAGE", heading):
        return ArtifactKind.WORK_PACKAGE
    if re.search(r"#\s+.*INCREMENT", heading):
        return ArtifactKind.INCREMENT
    if re.search(r"#\s+.*TICKET", heading):
        return ArtifactKind.TICKET
    if re.search(r"#\s+.*SPEC", heading):
        return ArtifactKind.SPEC
    return ArtifactKind.UNKNOWN


def _identifier_for(kind: ArtifactKind, path: Path, metadata: dict[str, str], text: str) -> str | None:
    keys_by_kind = {
        ArtifactKind.WORK_PACKAGE: ("work_package_id", "work_package", "id", "identifier"),
        ArtifactKind.INCREMENT: ("increment_id", "increment", "id", "identifier"),
        ArtifactKind.TICKET: ("ticket_id", "ticket", "id", "identifier"),
        ArtifactKind.SCOPE: ("scope_id", "scope", "revision", "id", "identifier"),
        ArtifactKind.SPEC: ("spec_id", "spec", "id", "identifier"),
    }
    for key in keys_by_kind.get(kind, ("id", "identifier")):
        value = canonical_id(metadata.get(key))
        if value:
            return value

    value = canonical_id(path.name)
    if value:
        return value

    # A Scope result commonly mentions WP/INC identifiers without having its own
    # identifier. Never borrow a referenced child ID as the Scope ID.
    if kind == ArtifactKind.SCOPE:
        return None

    expected = {
        ArtifactKind.WORK_PACKAGE: "WP-",
        ArtifactKind.INCREMENT: "INC-",
        ArtifactKind.TICKET: "TKT-",
        ArtifactKind.SPEC: "SPEC-",
    }.get(kind)
    for found in ID_PATTERN.findall("\n".join(text.splitlines()[:80])):
        value = canonical_id(found)
        if value and (expected is None or value.startswith(expected)):
            return value
    return None


def _title(text: str, metadata: dict[str, str]) -> str | None:
    for key in ("title", "name"):
        if metadata.get(key):
            return metadata[key].strip().strip("`*")
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line.strip())
        if match:
            return match.group(1).strip()
    return None


def _status(metadata: dict[str, str], text: str) -> str | None:
    for key in ("status", "ticket_status", "increment_status", "work_package_status", "spec_status"):
        if metadata.get(key):
            return normalize_status(metadata[key])
    match = re.search(r"(?im)^\s*(?:[-*]\s*)?Status\s*:\s*([^\n|]+)", text)
    return normalize_status(match.group(1)) if match else None


def _work_slug(path: Path, planning_root: Path, metadata: dict[str, str]) -> str | None:
    for key in ("suggested_work_slug", "work_slug"):
        value = metadata.get(key)
        if value and value.strip().lower() not in {"none", "n/a", "-"}:
            return value.strip().strip("`/ ")
    try:
        relative = path.relative_to(planning_root)
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) >= 2 and parts[0].lower() == "work":
        return parts[1]
    return None


def parse_artifact(path: Path, planning_root: Path, max_bytes: int = 2_000_000) -> Artifact:
    raw = path.read_bytes()
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
    text = raw.decode("utf-8", errors="replace").lstrip("\ufeff")
    metadata = _extract_metadata(text)
    kind = _classify(path, text)
    references = tuple(dict.fromkeys(canonical_id(value) for value in ID_PATTERN.findall(text) if canonical_id(value)))
    link_targets = tuple(dict.fromkeys(match.strip() for match in LINK_PATTERN.findall(text)))
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return Artifact(
        path=path,
        relative_path=path.relative_to(planning_root.parent.parent).as_posix(),
        kind=kind,
        identifier=_identifier_for(kind, path, metadata, text),
        status=_status(metadata, text),
        title=_title(text, metadata),
        metadata=metadata,
        references=references,
        link_targets=link_targets,
        work_slug=_work_slug(path, planning_root, metadata),
        modified_at=modified_at,
        raw_text=text,
    )


def metadata_id(artifact: Artifact, *keys: str) -> str | None:
    for key in keys:
        value = canonical_id(artifact.metadata.get(key))
        if value:
            return value
    return None


def metadata_value(artifact: Artifact, *keys: str) -> str | None:
    for key in keys:
        value = artifact.metadata.get(key)
        if value and value.strip().lower() not in {"none", "n/a", "-", "null"}:
            return value.strip().strip("`")
    return None
