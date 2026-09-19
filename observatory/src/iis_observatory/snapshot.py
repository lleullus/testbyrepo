from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable
import base64
import json
import os
import re
import subprocess
import tempfile

from .model import Artifact, Health, ProjectState, SNAPSHOT_SCHEMA_VERSION, __version__
from .scanner import ScanOptions, scan_repository

SNAPSHOT_DIRECTORY = Path("docs/planning/observatory")
SNAPSHOT_MARKDOWN = "PROJECT-OVERVIEW.md"
SNAPSHOT_JSON = "project-state.json"
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
    content_b64: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "path": self.path,
            "content": self.content_b64,
            "size": self.size,
        }


@dataclass(frozen=True)
class SnapshotBundle:
    repository: Path
    state: ProjectState
    payload: dict[str, Any]
    markdown: str


@dataclass(frozen=True)
class SnapshotCheck:
    freshness: SnapshotFreshness
    repository: Path
    snapshot_json: Path
    snapshot_markdown: Path
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
            "snapshot": {
                "markdown": str(self.bundle.repository / SNAPSHOT_DIRECTORY / SNAPSHOT_MARKDOWN),
                "json": str(self.bundle.repository / SNAPSHOT_DIRECTORY / SNAPSHOT_JSON),
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
        raise SnapshotError("Current planning artifacts are inconsistent; snapshot write is refused.")
    adaptive = collect_adaptive_provenance(repository)
    inputs = collect_snapshot_inputs(repository, state, adaptive)
    generated = generated_at or datetime.now(timezone.utc)
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    payload = _snapshot_payload(repository, state, inputs, adaptive, generated)
    markdown = render_project_overview(payload)
    payload["projection"]["files"] = {
        "projectOverview": SNAPSHOT_MARKDOWN,
        "projectState": SNAPSHOT_JSON,
    }
    return SnapshotBundle(repository, state, payload, markdown)


def collect_snapshot_inputs(
    repository: Path,
    state: ProjectState,
    adaptive: dict[str, Any] | None = None,
) -> list[SnapshotInput]:
    repository = repository.expanduser().resolve()
    paths: dict[Path, str] = {}

    def add_file(path: Path, category: str) -> None:
        if not path.exists() or not path.is_file() or path.is_symlink():
            return
        try:
            relative = path.relative_to(repository)
        except ValueError as exc:
            raise SnapshotError(f"Snapshot input escapes repository: {path}") from exc
        if relative.parts[:3] == ("docs", "planning", "observatory"):
            return
        paths[path] = category

    if state.current_scope is not None:
        for path in sorted(state.current_scope.path.parent.rglob("*.md")):
            add_file(path, "canonical-scope-work")

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

    for authority in [*state.scope_authority, *state.transition_authority]:
        path_value = authority.get("path")
        if path_value:
            add_file(repository / path_value, "scope-authority-live-projection")

    for artifact in (*state.scope_history, *state.legacy_history):
        if artifact.path not in paths:
            add_file(artifact.path, "displayed-history")

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
                content_b64=base64.b64encode(data).decode("ascii"),
                size=len(data),
            )
        )
    return result


def collect_adaptive_provenance(repository: Path) -> dict[str, Any]:
    repository = repository.expanduser().resolve()
    root = repository / "docs" / "planning" / "adaptive"
    mandates: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(root.rglob("*.md")):
            name = path.name.upper()
            if name not in {"ADAPTIVE-PLANNING-MANDATE.MD", "ADAPTIVE-PLANNING-TRACE.MD"}:
                continue
            metadata = _read_simple_metadata(path)
            relative = path.relative_to(repository).as_posix()
            if name == "ADAPTIVE-PLANNING-MANDATE.MD":
                mandates.append({
                    "path": relative,
                    "recordedStatus": metadata.get("status"),
                    "revision": _parse_revision(metadata.get("revision")),
                    "mode": metadata.get("mode"),
                    "appliesTo": metadata.get("applies_to"),
                })
            else:
                traces.append({
                    "path": relative,
                    "mandate": metadata.get("mandate"),
                    "currentMandateRevision": _parse_revision(metadata.get("current_mandate_revision")),
                })
    recorded = None
    if mandates:
        recorded = max(
            mandates,
            key=lambda item: (
                item.get("revision") if isinstance(item.get("revision"), int) else -1,
                item["path"],
            ),
        )
    return {
        "present": bool(mandates or traces),
        "mandates": mandates,
        "traces": traces,
        "recordedMandate": recorded,
        "activationInference": "not-performed",
        "note": "Companion provenance presence does not activate IIS Adaptive Planning for the current request.",
    }


def check_snapshot(
    repository: Path,
    *,
    state: ProjectState | None = None,
) -> SnapshotCheck:
    repository = repository.expanduser().resolve()
    json_path = repository / SNAPSHOT_DIRECTORY / SNAPSHOT_JSON
    markdown_path = repository / SNAPSHOT_DIRECTORY / SNAPSHOT_MARKDOWN
    if not json_path.exists() and not markdown_path.exists():
        return SnapshotCheck(SnapshotFreshness.MISSING, repository, json_path, markdown_path, "No stored Observatory snapshot exists.")
    if not json_path.is_file() or not markdown_path.is_file():
        return SnapshotCheck(SnapshotFreshness.INCONSISTENT, repository, json_path, markdown_path, "The snapshot pair is incomplete.")

    try:
        stored = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        return SnapshotCheck(SnapshotFreshness.INCONSISTENT, repository, json_path, markdown_path, f"Cannot read stored project-state.json: {exc}")
    if stored.get("schemaVersion") != SNAPSHOT_SCHEMA_VERSION:
        return SnapshotCheck(SnapshotFreshness.INCONSISTENT, repository, json_path, markdown_path, "Stored snapshot schema is not current.")

    projection = stored.get("projection")
    if not isinstance(projection, dict) or projection.get("files") != {
        "projectOverview": SNAPSHOT_MARKDOWN,
        "projectState": SNAPSHOT_JSON,
    }:
        return SnapshotCheck(SnapshotFreshness.INCONSISTENT, repository, json_path, markdown_path, "Stored snapshot file declaration is invalid.")

    try:
        expected_markdown = render_project_overview(stored)
        actual_markdown = markdown_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, KeyError, TypeError) as exc:
        return SnapshotCheck(SnapshotFreshness.INCONSISTENT, repository, json_path, markdown_path, f"Cannot validate snapshot pair: {exc}")
    if actual_markdown != expected_markdown:
        return SnapshotCheck(SnapshotFreshness.INCONSISTENT, repository, json_path, markdown_path, "PROJECT-OVERVIEW.md does not match the stored project-state projection.")

    state = state or scan_repository(repository, options=ScanOptions(check_links=True))
    if state.health == Health.INCONSISTENT or state.has_errors:
        return SnapshotCheck(
            SnapshotFreshness.INCONSISTENT,
            repository,
            json_path,
            markdown_path,
            "Current planning artifacts are inconsistent.",
            tuple(f"{issue.code}: {issue.message}" for issue in state.issues if issue.severity == "error"),
        )
    adaptive = collect_adaptive_provenance(repository)
    current_inputs = collect_snapshot_inputs(repository, state, adaptive)
    changes = _compare_inputs(projection.get("inputs"), current_inputs)
    if changes:
        return SnapshotCheck(
            SnapshotFreshness.STALE,
            repository,
            json_path,
            markdown_path,
            "Planning inputs or displayed history changed after snapshot generation.",
            tuple(changes),
        )
    return SnapshotCheck(
        SnapshotFreshness.CURRENT,
        repository,
        json_path,
        markdown_path,
        "Stored snapshot inputs match the current observed planning inputs.",
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
    json_text = json.dumps(bundle.payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    _atomic_replace_pair(directory, markdown_path, bundle.markdown, json_path, json_text)
    after = check_snapshot(repository, state=state)
    if after.freshness != SnapshotFreshness.CURRENT:
        raise SnapshotError(f"Snapshot write did not verify as CURRENT: {after.reason}")
    return SnapshotWriteResult("WRITTEN", bundle, after)


def render_snapshot_check(check: SnapshotCheck) -> str:
    lines = [
        "IIS OBSERVATORY SNAPSHOT",
        f"Repository: {check.repository}",
        f"Snapshot-Freshness: {check.freshness.value}",
        f"Snapshot JSON: {check.snapshot_json}",
        f"Project Overview: {check.snapshot_markdown}",
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

    direct_scope = planning.get("scope") if planning.get("authorityMode") == "direct-scope" else None
    if direct_scope:
        current_scope = direct_scope.get("current") or {}
        position = [
            f"- Stage: {planning['stage']}",
            f"- Health: {planning['health']}",
            f"- Current Scope: `{current_scope.get('path') or 'None'}`",
            f"- Scope Status: {current_scope.get('status') or 'None'}",
            f"- Work Slug: {current_scope.get('workSlug') or 'None'}",
            f"- Next Work: {next_work.get('kind')}" + (f" / {next_work.get('targetId')}" if next_work.get("targetId") else ""),
            f"- Next Leaf: {next_work.get('leaf')}",
            f"- Reason: {next_work.get('reason')}",
        ]
    else:
        position = [
            f"- Stage: {planning['stage']}",
            f"- Health: {planning['health']}",
            f"- Current Scope: {_snapshot_artifact_label(current.get('scope'))}",
            f"- Current Work Package: {_snapshot_artifact_label(current.get('workPackage'))}",
            f"- Current Increment: {_snapshot_artifact_label(current.get('increment'))}",
            f"- Current Spec: {_snapshot_artifact_label(current.get('spec'))}",
            f"- Work Slug: {current.get('workSlug') or 'None'}",
            f"- Next Work: {next_work.get('kind')}" + (f" / {next_work.get('targetId')}" if next_work.get("targetId") else ""),
            f"- Next Leaf: {next_work.get('leaf')}",
            f"- Reason: {next_work.get('reason')}",
        ]

    lines = [
        "# IIS Project Overview",
        "",
        "Projection-Authority: derived-read-only",
        f"Generated-By: iis-observatory {projection['generatedBy']['version']}",
        f"Generated-At: {projection['generatedAt']}",
        "Snapshot-Freshness: current-at-generation",
        f"Projection-Consistency: {projection['consistency']}",
        f"Git-Revision-At-Generation: {git.get('head') or 'unavailable'}",
        f"Git-Dirty-At-Generation: {_yes_no(git.get('dirty')) if git.get('available') else 'unavailable'}",
        "",
        "This file is a generated read-only projection. It does not establish downstream admission.",
        "",
        "## Project",
        "",
        f"- Name: {project['name']}",
        "- Root: .",
        "",
        "## Current Position",
        "",
        *position,
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

    if direct_scope:
        lines.extend(["", "## Scope", ""])
        current_scope = direct_scope.get("current") or {}
        lines.append(f"- Status: {current_scope.get('status') or 'None'}")
        lines.append(f"- Path: `{current_scope.get('path') or 'None'}`")
        lines.append("- Bound Thesis refs — admission not checked:")
        for item in direct_scope.get("boundThesis", []):
            lines.append(f"  - {item.get('snapshot')}:{item.get('path')}")
        transition = direct_scope.get("transitionAuthority", [])
        if transition:
            lines.append("- Transition Authority refs:")
            for item in transition:
                lines.append(f"  - {item.get('snapshot')}:{item.get('path')}")
        lines.append("- Required Outcomes — fulfillment not established:")
        remaining_outcomes = direct_scope.get("remainingRequiredOutcomes", [])
        if remaining_outcomes:
            lines.extend(f"  - {item.get('text')} ({item.get('source')})" for item in remaining_outcomes)
        else:
            lines.append("  - None observed")

    lines.extend(["", "## Tickets", ""])
    if tickets["items"]:
        lines.extend(["| Ticket | Artifact status | Path |", "|---|---|---|"])
        for ticket in tickets["items"]:
            lines.append(f"| {ticket.get('id') or 'Unknown'} | {ticket.get('status') or 'missing'} | `{ticket['path']}` |")
    else:
        lines.append("No current Tickets are associated with this planning unit.")

    lines.extend(["", "## Follow-up Horizon", ""])
    candidates = follow_up["nextCandidateWorkPackages"]
    deferred = follow_up["deferredWorkPackages"]
    if candidates:
        lines.append("### Authored next candidates")
        lines.append("")
        lines.extend(f"- {_snapshot_artifact_label(item)}" for item in candidates)
        lines.extend(["", "Next Increment: not yet shaped"])
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
        lines.append(f"- Recorded mandate revision: {recorded.get('revision') if recorded.get('revision') is not None else 'unknown'}")
        lines.append(f"- Recorded mandate artifact status: {recorded.get('recordedStatus') or 'unknown'}")
    lines.append("- Current Adaptive mode inference: not performed")
    lines.append(f"- Boundary: {adaptive['note']}")

    lines.extend(["", "## Consistency", ""])
    if planning["issues"]:
        for issue in planning["issues"]:
            suffix = f" (`{issue['path']}`)" if issue.get("path") else ""
            lines.append(f"- {issue['severity'].upper()} {issue['code']}: {issue['message']}{suffix}")
    else:
        lines.append("No planning-artifact issues were reported by this projection.")

    lines.extend([
        "",
        "## Projection Boundaries",
        "",
        "- This snapshot does not change canonical planning, verification, release, or runtime state.",
        "- It does not establish Product Thesis closure or role admission.",
        "- Runtime correctness remains an independently observed property.",
        "",
    ])
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
    return f"- {measurement.get('label') or 'Progress'}: {_progress_bar(percent)} {numerator:g} / {denominator:g} ({percent:.1f}%) — exact ratio"


def _progress_bar(percent: float, width: int = 10) -> str:
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
    generated_at: datetime,
) -> dict[str, Any]:
    ticket_counts = state.ticket_counts
    progress: list[dict[str, Any]] = []
    if ticket_counts["total"]:
        percent = round(ticket_counts["done"] / ticket_counts["total"] * 100.0, 6)
        progress.append({
            "id": "current-ticket-delivery",
            "label": "Current Ticket delivery",
            "measurement": "exact-ratio",
            "numerator": ticket_counts["done"],
            "denominator": ticket_counts["total"],
            "percent": percent,
            "evidence": [ticket.relative_path for ticket in state.tickets],
        })
    return {
        "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
        "projection": {
            "authority": PROJECTION_AUTHORITY,
            "generatedBy": {"name": "iis-observatory", "version": __version__},
            "generatedAt": generated_at.astimezone(timezone.utc).isoformat(timespec="seconds"),
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
            "authorityMode": "direct-scope" if state.direct_scope_mode else ("legacy-history" if state.legacy_history else "none"),
            "scope": _stable_scope_details(state),
            "legacy": {
                "history": [_stable_artifact_ref(item) for item in state.legacy_history],
                "transitionRequired": [_stable_artifact_ref(item) for item in state.transition_required],
                "automaticMigration": False,
            },
            "tickets": {
                "counts": ticket_counts,
                "items": [_stable_artifact_ref(item) for item in state.tickets],
                "completed": [item.identifier or item.relative_path for item in state.completed_tickets],
                "remaining": [item.identifier or item.relative_path for item in state.remaining_tickets],
            },
            "followUp": {
                "nextCandidateWorkPackages": [_stable_artifact_ref(item) for item in state.next_candidate_work_packages],
                "deferredWorkPackages": [_stable_artifact_ref(item) for item in state.deferred_work_packages],
                "nextIncrement": None,
                "nextIncrementState": "not-yet-shaped" if state.next_candidate_work_packages else None,
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


def _stable_scope_details(state: ProjectState) -> dict[str, Any] | None:
    scope = state.current_scope
    if not state.direct_scope_mode or scope is None:
        return None
    return {
        "current": {
            "path": scope.relative_path,
            "status": scope.status,
            "workSlug": scope.work_slug,
            "title": scope.title,
            "outcome": scope.metadata.get("section_outcome"),
            "acceptance": scope.metadata.get("section_acceptance"),
            "openDecisions": scope.metadata.get("section_open_decisions"),
        },
        "status": scope.status,
        "active": [_stable_artifact_ref(item) for item in state.active_scopes],
        "history": [_stable_artifact_ref(item) for item in state.scope_history],
        "boundThesis": [
            {key: value for key, value in item.items() if key in {"snapshot", "path"}}
            for item in state.scope_authority
        ],
        "transitionAuthority": [
            {key: value for key, value in item.items() if key in {"snapshot", "path"}}
            for item in state.transition_authority
        ],
        "requiredOutcomes": list(state.required_outcomes),
        "remainingRequiredOutcomes": list(state.remaining_required_outcomes),
    }


def _git_metadata(repository: Path) -> dict[str, Any]:
    top = _run_git_optional(repository, ["rev-parse", "--show-toplevel"])
    if top is None:
        return {"available": False, "head": None, "branch": None, "dirty": None}
    head = _run_git_optional(repository, ["rev-parse", "HEAD"])
    branch = _run_git_optional(repository, ["branch", "--show-current"])
    status = _run_git_optional(repository, ["status", "--porcelain", "--untracked-files=normal"])
    dirty_lines = []
    if status:
        for line in status.splitlines():
            if "docs/planning/observatory/" not in line.replace("\\", "/"):
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
            path.unlink(missing_ok=True)


def _write_temp(directory: Path, name: str, content: str) -> Path:
    descriptor, raw_path = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=directory)
    path = Path(raw_path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, 0o644)
        return path
    except Exception:
        path.unlink(missing_ok=True)
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


def _compare_inputs(stored_inputs: Any, current_inputs: list[SnapshotInput]) -> list[str]:
    stored_map: dict[str, tuple[str, str, int]] = {}
    if isinstance(stored_inputs, list):
        for item in stored_inputs:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            category = item.get("category")
            content = item.get("content")
            size = item.get("size")
            if isinstance(path, str) and isinstance(category, str) and isinstance(content, str) and isinstance(size, int):
                stored_map[path] = (category, content, size)
    current_map = {item.path: (item.category, item.content_b64, item.size) for item in current_inputs}
    changes: list[str] = []
    for path in sorted(set(current_map) - set(stored_map)):
        changes.append(f"added input: {path}")
    for path in sorted(set(stored_map) - set(current_map)):
        changes.append(f"removed input: {path}")
    for path in sorted(set(stored_map) & set(current_map)):
        if stored_map[path] != current_map[path]:
            changes.append(f"changed input: {path}")
    return changes


def _snapshot_artifact_label(item: dict[str, Any] | None) -> str:
    if item is None:
        return "None"
    identifier = item.get("id")
    title = item.get("title")
    path = item.get("path")
    status = item.get("status")
    label = identifier or title or path or "Unknown"
    if identifier and title:
        clean = re.sub(rf"(?i)^\s*{re.escape(identifier)}\s*[:\-]?\s*", "", title).strip()
        if clean and clean.lower() not in {"increment", "work package"}:
            label = f"{identifier} · {clean}"
    if status:
        label += f" / {status}"
    if path:
        label += f" (`{path}`)"
    return label


def _yes_no(value: Any) -> str:
    return "yes" if value else "no"
