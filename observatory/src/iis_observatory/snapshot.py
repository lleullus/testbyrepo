from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import os
import re
import subprocess
import tempfile

from .model import (
    Artifact,
    Health,
    ProjectState,
    SNAPSHOT_SCHEMA_VERSION,
    __version__,
)
from .scanner import ScanOptions, scan_repository

SNAPSHOT_DIRECTORY = Path("docs/planning/observatory")
SNAPSHOT_MARKDOWN = "PROJECT-OVERVIEW.md"
SNAPSHOT_JSON = "project-state.json"
SOURCE_FINGERPRINT_ALGORITHM = "iis-observatory-source-v1"
PROJECTION_AUTHORITY = "derived-read-only"


class SnapshotError(RuntimeError):
    pass


class SnapshotFreshness(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    MISSING = "MISSING"
    INCONSISTENT = "INCONSISTENT"


@dataclass(frozen=True)
class SnapshotInput:
    category: str
    path: str
    sha256: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
        }


@dataclass(frozen=True)
class SnapshotBundle:
    repository: Path
    state: ProjectState
    payload: dict[str, Any]
    markdown: str
    source_fingerprint: str


@dataclass(frozen=True)
class SnapshotCheck:
    freshness: SnapshotFreshness
    repository: Path
    snapshot_json: Path
    snapshot_markdown: Path
    current_fingerprint: str | None
    stored_fingerprint: str | None
    reason: str
    changes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "freshness": self.freshness.value,
            "repository": str(self.repository),
            "snapshot": {
                "json": str(self.snapshot_json),
                "markdown": str(self.snapshot_markdown),
            },
            "current_source_fingerprint": self.current_fingerprint,
            "stored_source_fingerprint": self.stored_fingerprint,
            "reason": self.reason,
            "changes": list(self.changes),
        }


@dataclass(frozen=True)
class SnapshotWriteResult:
    action: str
    bundle: SnapshotBundle
    check: SnapshotCheck

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "source_fingerprint": self.bundle.source_fingerprint,
            "snapshot": {
                "markdown": str(
                    self.bundle.repository / SNAPSHOT_DIRECTORY / SNAPSHOT_MARKDOWN
                ),
                "json": str(
                    self.bundle.repository / SNAPSHOT_DIRECTORY / SNAPSHOT_JSON
                ),
            },
            "freshness": self.check.freshness.value,
        }


def build_snapshot(
    repository: Path,
    *,
    state: ProjectState | None = None,
    generated_at: datetime | None = None,
) -> SnapshotBundle:
    repository = repository.expanduser().resolve()
    state = state or scan_repository(repository, options=ScanOptions(check_links=True))
    if state.planning_root is None:
        raise SnapshotError("The repository has no docs/planning directory.")
    if state.health == Health.INCONSISTENT or state.has_errors:
        raise SnapshotError(
            "Current planning artifacts are inconsistent; snapshot write is refused."
        )

    adaptive = collect_adaptive_provenance(repository)
    inputs = collect_snapshot_inputs(repository, state, adaptive)
    source_fingerprint = compute_source_fingerprint(inputs)
    generated = generated_at or datetime.now(timezone.utc)
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)

    payload = _snapshot_payload(
        repository,
        state,
        inputs,
        adaptive,
        source_fingerprint,
        generated,
    )
    markdown = render_project_overview(payload)
    markdown_sha = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    payload["projection"]["files"] = {
        "projectOverview": SNAPSHOT_MARKDOWN,
        "projectOverviewSha256": markdown_sha,
        "projectState": SNAPSHOT_JSON,
    }
    return SnapshotBundle(repository, state, payload, markdown, source_fingerprint)


def collect_snapshot_inputs(
    repository: Path,
    state: ProjectState,
    adaptive: dict[str, Any] | None = None,
) -> list[SnapshotInput]:
    repository = repository.expanduser().resolve()
    paths: dict[Path, str] = {}

    def add_file(path: Path, category: str) -> None:
        if not path.exists() or not path.is_file():
            return
        try:
            relative = path.relative_to(repository)
        except ValueError as exc:
            raise SnapshotError(f"Snapshot input escapes repository: {path}") from exc
        if relative.parts[:3] == ("docs", "planning", "observatory"):
            return
        resolved = path.resolve()
        try:
            resolved.relative_to(repository)
        except ValueError as exc:
            raise SnapshotError(f"Snapshot input symlink escapes repository: {path}") from exc
        paths[path] = category

    # Scope lineage is the authored navigation and horizon authority. Include the
    # full current lineage so immutable revisions and reshaping relationships are
    # part of freshness without treating unrelated historical lineages as current.
    if state.current_scope is not None:
        lineage_root = state.current_scope.path.parent
        for path in sorted(lineage_root.rglob("*.md")):
            add_file(path, "canonical-scope-lineage")

    # Include the complete current work area rather than only SPEC/Ticket files so
    # current Behavior/UI and adjacent projection authorities can invalidate a
    # durable read model when they change.
    if state.current_work_slug:
        work_root = repository / "docs" / "planning" / "work" / state.current_work_slug
        if work_root.is_dir():
            for path in sorted(work_root.rglob("*.md")):
                add_file(path, "canonical-current-work")

    direct_artifacts: Iterable[Artifact | None] = (
        state.current_scope,
        state.current_work_package,
        state.current_increment,
        state.current_spec,
        *state.tickets,
        *state.next_candidate_work_packages,
        *state.deferred_work_packages,
    )
    for artifact in direct_artifacts:
        if artifact is not None:
            add_file(artifact.path, "canonical-state-input")

    adaptive = adaptive or collect_adaptive_provenance(repository)
    for item in [*adaptive.get("mandates", []), *adaptive.get("traces", [])]:
        path_value = item.get("path")
        if path_value:
            add_file(repository / path_value, "adaptive-provenance")

    result: list[SnapshotInput] = []
    for path, category in sorted(paths.items(), key=lambda item: item[0].as_posix()):
        data = path.read_bytes()
        result.append(
            SnapshotInput(
                category=category,
                path=path.relative_to(repository).as_posix(),
                sha256=hashlib.sha256(data).hexdigest(),
                size=len(data),
            )
        )
    return result


def compute_source_fingerprint(inputs: Iterable[SnapshotInput]) -> str:
    canonical = {
        "algorithm": SOURCE_FINGERPRINT_ALGORITHM,
        "inputs": [
            {
                "category": item.category,
                "path": item.path,
                "sha256": item.sha256,
            }
            for item in sorted(inputs, key=lambda value: (value.path, value.category))
        ],
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def collect_adaptive_provenance(repository: Path) -> dict[str, Any]:
    repository = repository.expanduser().resolve()
    root = repository / "docs" / "planning" / "adaptive"
    mandates: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.rglob("*.md")):
            name = path.name.upper()
            if name not in {
                "ADAPTIVE-PLANNING-MANDATE.MD",
                "ADAPTIVE-PLANNING-TRACE.MD",
            }:
                continue
            metadata = _read_simple_metadata(path)
            relative = path.relative_to(repository).as_posix()
            if name == "ADAPTIVE-PLANNING-MANDATE.MD":
                mandates.append(
                    {
                        "path": relative,
                        "recordedStatus": metadata.get("status"),
                        "revision": _parse_revision(metadata.get("revision")),
                        "mode": metadata.get("mode"),
                        "appliesTo": metadata.get("applies_to"),
                    }
                )
            else:
                traces.append(
                    {
                        "path": relative,
                        "mandate": metadata.get("mandate"),
                        "currentMandateRevision": _parse_revision(
                            metadata.get("current_mandate_revision")
                        ),
                    }
                )

    recorded: dict[str, Any] | None = None
    if mandates:
        recorded = max(
            mandates,
            key=lambda item: (
                item.get("revision")
                if isinstance(item.get("revision"), int)
                else -1,
                item["path"],
            ),
        )
    return {
        "present": bool(mandates or traces),
        "mandates": mandates,
        "traces": traces,
        "recordedMandate": recorded,
        "activationInference": "not-performed",
        "note": (
            "Companion provenance presence or a recorded active status does not "
            "activate IIS Adaptive Planning for the current request."
        ),
    }


def check_snapshot(
    repository: Path,
    *,
    state: ProjectState | None = None,
) -> SnapshotCheck:
    repository = repository.expanduser().resolve()
    directory = repository / SNAPSHOT_DIRECTORY
    json_path = directory / SNAPSHOT_JSON
    markdown_path = directory / SNAPSHOT_MARKDOWN

    state = state or scan_repository(repository, options=ScanOptions(check_links=True))
    if state.planning_root is None:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            None,
            None,
            "The repository has no docs/planning directory.",
        )
    if state.health == Health.INCONSISTENT or state.has_errors:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            None,
            None,
            "Current canonical planning artifacts are inconsistent.",
            tuple(f"{issue.code}: {issue.message}" for issue in state.issues),
        )

    adaptive = collect_adaptive_provenance(repository)
    current_inputs = collect_snapshot_inputs(repository, state, adaptive)
    current_fingerprint = compute_source_fingerprint(current_inputs)

    if not json_path.exists() and not markdown_path.exists():
        return SnapshotCheck(
            SnapshotFreshness.MISSING,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            None,
            "No durable Observatory snapshot exists.",
        )
    if not json_path.is_file() or not markdown_path.is_file():
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            None,
            "Snapshot pair is incomplete; both project-state.json and PROJECT-OVERVIEW.md are required.",
        )

    try:
        stored = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            None,
            f"Snapshot JSON is unreadable or invalid: {exc}",
        )

    if stored.get("schemaVersion") != SNAPSHOT_SCHEMA_VERSION:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            _stored_fingerprint(stored),
            "Snapshot schema version is unsupported or missing.",
        )
    projection = stored.get("projection")
    if not isinstance(projection, dict) or projection.get("authority") != PROJECTION_AUTHORITY:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            _stored_fingerprint(stored),
            "Snapshot projection authority is missing or invalid.",
        )

    stored_fingerprint = _stored_fingerprint(stored)
    files = projection.get("files") if isinstance(projection, dict) else None
    expected_markdown_sha = (
        files.get("projectOverviewSha256") if isinstance(files, dict) else None
    )
    actual_markdown_sha = hashlib.sha256(markdown_path.read_bytes()).hexdigest()
    if not expected_markdown_sha or expected_markdown_sha != actual_markdown_sha:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            stored_fingerprint,
            "PROJECT-OVERVIEW.md does not match the checksum recorded in project-state.json.",
        )

    if stored_fingerprint == current_fingerprint:
        return SnapshotCheck(
            SnapshotFreshness.CURRENT,
            repository,
            json_path,
            markdown_path,
            current_fingerprint,
            stored_fingerprint,
            "Stored snapshot matches the current source fingerprint.",
        )

    stored_inputs = projection.get("inputs") if isinstance(projection, dict) else []
    changes = _compare_inputs(stored_inputs, current_inputs)
    return SnapshotCheck(
        SnapshotFreshness.STALE,
        repository,
        json_path,
        markdown_path,
        current_fingerprint,
        stored_fingerprint,
        "Canonical planning or displayed Adaptive provenance changed after snapshot generation.",
        tuple(changes),
    )


def write_snapshot(repository: Path) -> SnapshotWriteResult:
    repository = repository.expanduser().resolve()
    state = scan_repository(repository, options=ScanOptions(check_links=True))
    bundle = build_snapshot(repository, state=state)
    before = check_snapshot(repository, state=state)
    if before.freshness == SnapshotFreshness.CURRENT:
        return SnapshotWriteResult("UNCHANGED", bundle, before)

    directory = repository / SNAPSHOT_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    markdown_path = directory / SNAPSHOT_MARKDOWN
    json_path = directory / SNAPSHOT_JSON
    json_text = json.dumps(
        bundle.payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"
    _atomic_replace_pair(
        directory,
        markdown_path,
        bundle.markdown,
        json_path,
        json_text,
    )
    after = check_snapshot(repository, state=state)
    if after.freshness != SnapshotFreshness.CURRENT:
        raise SnapshotError(
            f"Snapshot write did not verify as CURRENT: {after.reason}"
        )
    return SnapshotWriteResult("WRITTEN", bundle, after)


def render_snapshot_check(check: SnapshotCheck) -> str:
    lines = [
        "IIS OBSERVATORY SNAPSHOT",
        f"Repository: {check.repository}",
        f"Snapshot-Freshness: {check.freshness.value}",
        f"Snapshot JSON: {check.snapshot_json}",
        f"Project Overview: {check.snapshot_markdown}",
        f"Current Source Fingerprint: {check.current_fingerprint or 'None'}",
        f"Stored Source Fingerprint: {check.stored_fingerprint or 'None'}",
        f"Reason: {check.reason}",
    ]
    if check.changes:
        lines.append("Changes:")
        lines.extend(f"- {change}" for change in check.changes)
    return "\n".join(lines) + "\n"


def render_snapshot_write(result: SnapshotWriteResult) -> str:
    directory = result.bundle.repository / SNAPSHOT_DIRECTORY
    return (
        "IIS OBSERVATORY SNAPSHOT\n"
        f"Repository: {result.bundle.repository}\n"
        f"Action: {result.action}\n"
        f"Snapshot-Freshness: {result.check.freshness.value}\n"
        f"Source-Fingerprint: {result.bundle.source_fingerprint}\n"
        f"Project Overview: {directory / SNAPSHOT_MARKDOWN}\n"
        f"Project State: {directory / SNAPSHOT_JSON}\n"
    )


def render_project_overview(payload: dict[str, Any]) -> str:
    projection = payload["projection"]
    project = payload["project"]
    planning = payload["planning"]
    progress = payload["progress"]
    adaptive = payload["adaptiveProvenance"]
    current = planning["current"]
    tickets = planning["tickets"]
    follow_up = planning["followUp"]
    next_work = planning["nextWork"]
    git = projection["git"]

    lines = [
        "# IIS Project Overview",
        "",
        "Projection-Authority: derived-read-only",
        f"Generated-By: iis-observatory {projection['generatedBy']['version']}",
        f"Generated-At: {projection['generatedAt']}",
        f"Source-Fingerprint: {projection['sourceFingerprint']}",
        "Snapshot-Freshness: current-at-generation",
        f"Projection-Consistency: {projection['consistency']}",
        f"Git-Revision-At-Generation: {git.get('head') or 'unavailable'}",
        f"Git-Dirty-At-Generation: {_yes_no(git.get('dirty')) if git.get('available') else 'unavailable'}",
        "",
        "This file is a generated read-only projection. Canonical IIS artifacts and exact runtime evidence remain authoritative in their own domains.",
        "",
        "## Project",
        "",
        f"- Name: {project['name']}",
        "- Root: .",
        "",
        "## Current Position",
        "",
        f"- Stage: {planning['stage']}",
        f"- Health: {planning['health']}",
        f"- Current Scope: {_snapshot_artifact_label(current.get('scope'))}",
        f"- Current Work Package: {_snapshot_artifact_label(current.get('workPackage'))}",
        f"- Current Increment: {_snapshot_artifact_label(current.get('increment'))}",
        f"- Current Spec: {_snapshot_artifact_label(current.get('spec'))}",
        f"- Work Slug: {current.get('workSlug') or 'None'}",
        f"- Next Work: {next_work.get('kind')}"
        + (f" / {next_work.get('targetId')}" if next_work.get("targetId") else ""),
        f"- Next Leaf: {next_work.get('leaf')}",
        f"- Reason: {next_work.get('reason')}",
        "",
        "## Delivery Progress",
        "",
    ]

    if progress:
        for measurement in progress:
            rendered = _render_progress_measurement(measurement)
            if rendered:
                lines.append(rendered)
    else:
        lines.append("- No exact Ticket denominator is available for the current unit.")

    lines.extend(["", "## Tickets", ""])
    if tickets["items"]:
        lines.extend(
            [
                "| Ticket | Artifact status | Path |",
                "|---|---|---|",
            ]
        )
        for ticket in tickets["items"]:
            lines.append(
                f"| {ticket.get('id') or 'Unknown'} | {ticket.get('status') or 'missing'} | `{ticket['path']}` |"
            )
    else:
        lines.append("No current Tickets are associated with this planning unit.")

    lines.extend(["", "## Follow-up Horizon", ""])
    candidates = follow_up["nextCandidateWorkPackages"]
    deferred = follow_up["deferredWorkPackages"]
    if candidates:
        lines.append("### Authored next candidates")
        lines.append("")
        lines.extend(f"- {_snapshot_artifact_label(item)}" for item in candidates)
        lines.append("")
        lines.append("Next Increment: not yet shaped")
    else:
        lines.append("Authored next candidates: None")
    if deferred:
        lines.extend(["", "### Deferred", ""])
        lines.extend(f"- {_snapshot_artifact_label(item)}" for item in deferred)

    lines.extend(["", "## Adaptive Planning Provenance", ""])
    lines.append(f"- Companion artifacts present: {_yes_no(adaptive['present'])}")
    recorded = adaptive.get("recordedMandate")
    if recorded:
        lines.append(f"- Recorded mandate: `{recorded['path']}`")
        lines.append(
            f"- Recorded mandate revision: {recorded.get('revision') if recorded.get('revision') is not None else 'unknown'}"
        )
        lines.append(
            f"- Recorded mandate artifact status: {recorded.get('recordedStatus') or 'unknown'}"
        )
    lines.append("- Current Adaptive mode inference: not performed")
    lines.append(f"- Boundary: {adaptive['note']}")

    lines.extend(["", "## Consistency", ""])
    if planning["issues"]:
        for issue in planning["issues"]:
            suffix = f" (`{issue['path']}`)" if issue.get("path") else ""
            lines.append(
                f"- {issue['severity'].upper()} {issue['code']}: {issue['message']}{suffix}"
            )
    else:
        lines.append("No planning-artifact issues were reported by this projection.")

    lines.extend(
        [
            "",
            "## Projection Boundaries",
            "",
            "- This snapshot does not change Scope, Work Package, Increment, Spec, Ticket, verification, release, or runtime state.",
            "- It does not select among authored follow-up candidates or execute the reported next leaf.",
            "- Overall product estimates and project-specific runtime coverage are intentionally absent until supplied by an explicit measurement provider.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_progress_measurement(measurement: dict[str, Any]) -> str | None:
    if measurement.get("measurement") != "exact-ratio":
        return None
    numerator = measurement.get("numerator")
    denominator = measurement.get("denominator")
    percent = measurement.get("percent")
    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        return None
    if not isinstance(percent, (int, float)):
        percent = (numerator / denominator * 100.0) if denominator else 0.0
    bar = _progress_bar(percent)
    return (
        f"- {measurement.get('label') or 'Progress'}: {bar} "
        f"{numerator:g} / {denominator:g} ({percent:.1f}%) — exact ratio"
    )


def _progress_bar(percent: float, width: int = 10) -> str:
    """Render a deterministic percentage bar without overstating tiny ratios."""
    if width <= 0:
        return ""
    bounded = max(0.0, min(100.0, float(percent)))
    eighths_total = int(bounded / 100.0 * width * 8)
    if bounded > 0.0 and eighths_total == 0:
        eighths_total = 1
    if bounded < 100.0 and eighths_total >= width * 8:
        eighths_total = width * 8 - 1
    full_cells, partial = divmod(eighths_total, 8)
    full_cells = min(full_cells, width)
    partial_chars = "▏▎▍▌▋▊▉"
    pieces = ["█" * full_cells]
    used = full_cells
    if partial and used < width:
        pieces.append(partial_chars[partial - 1])
        used += 1
    pieces.append("░" * max(0, width - used))
    return "".join(pieces)


def _snapshot_payload(
    repository: Path,
    state: ProjectState,
    inputs: list[SnapshotInput],
    adaptive: dict[str, Any],
    source_fingerprint: str,
    generated_at: datetime,
) -> dict[str, Any]:
    ticket_counts = state.ticket_counts
    progress: list[dict[str, Any]] = []
    if ticket_counts["total"]:
        percent = round(
            ticket_counts["done"] / ticket_counts["total"] * 100.0, 6
        )
        progress.append(
            {
                "id": "current-ticket-delivery",
                "label": "Current Ticket delivery",
                "measurement": "exact-ratio",
                "numerator": ticket_counts["done"],
                "denominator": ticket_counts["total"],
                "percent": percent,
                "evidence": [ticket.relative_path for ticket in state.tickets],
            }
        )

    return {
        "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
        "projection": {
            "authority": PROJECTION_AUTHORITY,
            "generatedBy": {"name": "iis-observatory", "version": __version__},
            "generatedAt": generated_at.astimezone(timezone.utc).isoformat(
                timespec="seconds"
            ),
            "sourceFingerprint": source_fingerprint,
            "sourceFingerprintAlgorithm": SOURCE_FINGERPRINT_ALGORITHM,
            "freshness": "current-at-generation",
            "consistency": "consistent",
            "inputs": [item.to_dict() for item in inputs],
            "git": _git_metadata(repository),
        },
        "project": {"name": state.repository, "root": "."},
        "planning": {
            "stage": state.stage.value,
            "health": state.health.value,
            "current": {
                "scope": _stable_artifact_ref(state.current_scope),
                "workPackage": _stable_artifact_ref(state.current_work_package),
                "increment": _stable_artifact_ref(state.current_increment),
                "spec": _stable_artifact_ref(state.current_spec),
                "workSlug": state.current_work_slug,
            },
            "tickets": {
                "counts": ticket_counts,
                "items": [_stable_artifact_ref(item) for item in state.tickets],
                "completed": [
                    item.identifier or item.relative_path
                    for item in state.completed_tickets
                ],
                "remaining": [
                    item.identifier or item.relative_path
                    for item in state.remaining_tickets
                ],
            },
            "followUp": {
                "nextCandidateWorkPackages": [
                    _stable_artifact_ref(item)
                    for item in state.next_candidate_work_packages
                ],
                "deferredWorkPackages": [
                    _stable_artifact_ref(item) for item in state.deferred_work_packages
                ],
                "nextIncrement": None,
                "nextIncrementState": (
                    "not-yet-shaped"
                    if state.next_candidate_work_packages
                    else None
                ),
            },
            "nextWork": {
                "kind": state.next_work.kind.value,
                "targetId": state.next_work.target_id,
                "targetPath": state.next_work.target_path,
                "leaf": state.next_work.leaf,
                "reason": state.next_work.reason,
            },
            "issues": [issue.to_dict() for issue in state.issues],
        },
        "progress": progress,
        "adaptiveProvenance": adaptive,
    }


def _stable_artifact_ref(artifact: Artifact | None) -> dict[str, Any] | None:
    if artifact is None:
        return None
    return {
        "id": artifact.identifier,
        "kind": artifact.kind.value,
        "status": artifact.status,
        "title": artifact.title,
        "path": artifact.relative_path,
        "workSlug": artifact.work_slug,
    }


def _git_metadata(repository: Path) -> dict[str, Any]:
    top = _run_git_optional(repository, ["rev-parse", "--show-toplevel"])
    if top is None:
        return {
            "available": False,
            "head": None,
            "branch": None,
            "dirty": None,
        }
    head = _run_git_optional(repository, ["rev-parse", "HEAD"])
    branch = _run_git_optional(repository, ["branch", "--show-current"])
    status = _run_git_optional(
        repository, ["status", "--porcelain", "--untracked-files=normal"]
    )
    dirty_lines = []
    if status:
        for line in status.splitlines():
            normalized = line.replace("\\", "/")
            if "docs/planning/observatory/" in normalized:
                continue
            dirty_lines.append(line)
    return {
        "available": True,
        "head": head.strip() if head else None,
        "branch": branch.strip() if branch else None,
        "dirty": bool(dirty_lines),
    }


def _run_git_optional(repository: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _atomic_replace_pair(
    directory: Path,
    markdown_path: Path,
    markdown_text: str,
    json_path: Path,
    json_text: str,
) -> None:
    temp_paths: list[Path] = []
    try:
        md_temp = _write_temp(directory, markdown_path.name, markdown_text)
        temp_paths.append(md_temp)
        json_temp = _write_temp(directory, json_path.name, json_text)
        temp_paths.append(json_temp)
        # JSON is the check anchor and is replaced last. A crash between the two
        # replacements yields an explicit checksum inconsistency rather than a
        # falsely CURRENT pair.
        os.replace(md_temp, markdown_path)
        temp_paths.remove(md_temp)
        os.replace(json_temp, json_path)
        temp_paths.remove(json_temp)
        try:
            directory_fd = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        for path in temp_paths:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def _write_temp(directory: Path, name: str, content: str) -> Path:
    descriptor, raw_path = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".tmp", dir=directory
    )
    path = Path(raw_path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, 0o644)
        return path
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _read_simple_metadata(path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    pattern = re.compile(r"^([A-Za-z][A-Za-z0-9 _/-]{0,64})\s*:\s*(.*?)\s*$")
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return metadata
    for line in lines[:120]:
        match = pattern.match(line.strip())
        if not match:
            continue
        key = re.sub(r"[^a-z0-9]+", "_", match.group(1).lower()).strip("_")
        metadata.setdefault(key, match.group(2).strip().strip("`"))
    return metadata


def _parse_revision(value: str | None) -> int | str | None:
    if value is None:
        return None
    clean = value.strip()
    if clean.isdigit():
        return int(clean)
    return clean or None


def _stored_fingerprint(payload: dict[str, Any]) -> str | None:
    projection = payload.get("projection")
    if not isinstance(projection, dict):
        return None
    value = projection.get("sourceFingerprint")
    return value if isinstance(value, str) else None


def _compare_inputs(
    stored_inputs: Any, current_inputs: list[SnapshotInput]
) -> list[str]:
    stored_map: dict[str, str] = {}
    if isinstance(stored_inputs, list):
        for item in stored_inputs:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            digest = item.get("sha256")
            if isinstance(path, str) and isinstance(digest, str):
                stored_map[path] = digest
    current_map = {item.path: item.sha256 for item in current_inputs}
    changes: list[str] = []
    for path in sorted(set(current_map) - set(stored_map)):
        changes.append(f"added input: {path}")
    for path in sorted(set(stored_map) - set(current_map)):
        changes.append(f"removed input: {path}")
    for path in sorted(set(stored_map) & set(current_map)):
        if stored_map[path] != current_map[path]:
            changes.append(f"changed input: {path}")
    return changes or ["source fingerprint changed"]


def _snapshot_artifact_label(item: dict[str, Any] | None) -> str:
    if item is None:
        return "None"
    identifier = item.get("id")
    title = item.get("title")
    path = item.get("path")
    status = item.get("status")
    label = identifier or title or path or "Unknown"
    if identifier and title:
        clean = re.sub(
            rf"(?i)^\s*{re.escape(identifier)}\s*[:\-]?\s*", "", title
        ).strip()
        if clean and clean.lower() not in {"increment", "work package"}:
            label = f"{identifier} · {clean}"
    if status:
        label += f" / {status}"
    if path:
        label += f" (`{path}`)"
    return label


def _yes_no(value: Any) -> str:
    return "yes" if value else "no"
