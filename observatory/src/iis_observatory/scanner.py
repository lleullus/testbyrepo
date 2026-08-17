from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import re
from urllib.parse import unquote

from .markdown import canonical_id, metadata_id, metadata_value, parse_artifact
from .model import (
    Artifact,
    ArtifactKind,
    Health,
    Issue,
    ProjectState,
    Stage,
    natural_id_key,
    newest_timestamp,
    utc_now,
)
from .next_work import evaluate_next_work


@dataclass(frozen=True)
class ScanOptions:
    check_links: bool = True
    max_file_bytes: int = 2_000_000


def scan_repository(
    repository: Path,
    *,
    repository_name: str | None = None,
    options: ScanOptions | None = None,
) -> ProjectState:
    options = options or ScanOptions()
    repository = repository.expanduser().resolve()
    planning_root = repository / "docs" / "planning"
    state = ProjectState(
        repository=repository_name or repository.name,
        repository_path=repository,
        planning_root=planning_root if planning_root.is_dir() else None,
        scanned_at=utc_now(),
        stage=Stage.UNKNOWN,
        health=Health.NO_IIS,
    )
    if not repository.exists():
        state.issues.append(Issue("IIS000", f"Repository does not exist: {repository}", "error"))
        evaluate_next_work(state)
        return state
    if not planning_root.is_dir():
        evaluate_next_work(state)
        return state

    artifacts = _load_artifacts(planning_root, options, state)
    state.last_activity = newest_timestamp(artifacts)
    by_kind = _group_by_kind(artifacts)

    scopes = by_kind[ArtifactKind.SCOPE]
    work_packages = by_kind[ArtifactKind.WORK_PACKAGE]
    increments = by_kind[ArtifactKind.INCREMENT]
    specs = by_kind[ArtifactKind.SPEC]
    tickets = by_kind[ArtifactKind.TICKET]

    state.current_scope = _select_scope(scopes)
    lineage_increments = _scope_lineage_items(increments, state.current_scope)
    lineage_work_packages = _scope_lineage_items(work_packages, state.current_scope)
    current_increment_id, selection_source = _selected_increment_id(
        state.current_scope, lineage_increments, specs
    )
    state.evidence["increment_selection"] = selection_source
    if state.current_scope is not None:
        state.evidence["scope_lineage"] = state.current_scope.path.parent.relative_to(planning_root).as_posix()

    ready_increments = [item for item in lineage_increments if item.status == "ready-for-matt"]
    if len(ready_increments) > 1:
        state.issues.append(
            Issue(
                "IIS102",
                "More than one Increment is marked ready-for-matt: "
                + ", ".join(item.identifier or item.relative_path for item in ready_increments),
                "error",
            )
        )

    if current_increment_id:
        state.current_increment = _find_by_id(lineage_increments, current_increment_id)
        if state.current_increment is None:
            state.issues.append(
                Issue(
                    "IIS101",
                    f"The current Scope selects {current_increment_id}, but no matching Increment artifact exists.",
                    "error",
                    state.current_scope.relative_path if state.current_scope else None,
                )
            )
    elif ready_increments:
        state.current_increment = _newest(ready_increments)
        state.evidence["increment_selection"] = "unique ready-for-matt Increment"
    else:
        active_increments = [
            item
            for item in lineage_increments
            if item.status in {"active", "confirmed", "approved"}
        ]
        if len(active_increments) == 1:
            state.current_increment = active_increments[0]
            state.evidence["increment_selection"] = "unique active Increment"

    if state.current_increment and state.current_increment.status == "superseded":
        state.issues.append(
            Issue(
                "IIS103",
                f"The selected current Increment {state.current_increment.identifier or state.current_increment.relative_path} is superseded.",
                "error",
                state.current_increment.relative_path,
            )
        )

    state.current_work_package = _select_work_package(
        lineage_work_packages, state.current_scope, state.current_increment
    )
    expansion_ids, deferred_ids = _scope_horizon_ids(state.current_scope)
    state.next_candidate_work_packages = _resolve_work_packages(lineage_work_packages, expansion_ids)
    state.deferred_work_packages = _resolve_work_packages(lineage_work_packages, deferred_ids)
    state.evidence["outcome_horizon"] = {
        "expansion": expansion_ids,
        "deferred": deferred_ids,
    }
    state.current_work_slug = _select_work_slug(
        state.current_scope, state.current_increment, specs, tickets
    )
    state.current_spec = _select_spec(
        specs, state.current_increment, state.current_work_slug
    )
    if state.current_work_slug is None and state.current_spec is not None:
        state.current_work_slug = state.current_spec.work_slug

    state.tickets = _select_tickets(
        tickets,
        current_increment=state.current_increment,
        current_work_slug=state.current_work_slug,
        current_spec=state.current_spec,
    )
    state.tickets.sort(key=lambda item: (natural_id_key(item.identifier), item.relative_path))

    _validate_tickets(state)
    if options.check_links:
        _validate_planning_links(artifacts, planning_root, state)
    _validate_association(state, specs, tickets)

    state.evidence.update(
        {
            "artifact_counts": {
                kind.value: len(items) for kind, items in by_kind.items()
            },
            "current_work_slug": state.current_work_slug,
        }
    )
    evaluate_next_work(state)
    return state


def _load_artifacts(planning_root: Path, options: ScanOptions, state: ProjectState) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for path in sorted(planning_root.rglob("*.md")):
        lowered = path.name.lower()
        if ".template." in lowered or lowered.endswith(".template.md"):
            continue
        if any(part in {"node_modules", ".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            artifact = parse_artifact(path, planning_root, options.max_file_bytes)
        except (OSError, UnicodeError) as exc:
            state.issues.append(
                Issue("IIS010", f"Cannot read planning artifact: {exc}", "error", path.as_posix())
            )
            continue
        if artifact.kind != ArtifactKind.UNKNOWN:
            artifacts.append(artifact)
    return artifacts


def _group_by_kind(artifacts: Iterable[Artifact]) -> dict[ArtifactKind, list[Artifact]]:
    grouped = {kind: [] for kind in ArtifactKind}
    for artifact in artifacts:
        grouped[artifact.kind].append(artifact)
    return grouped


def _newest(items: list[Artifact]) -> Artifact | None:
    if not items:
        return None
    return max(items, key=lambda item: (item.modified_at or utc_now(), item.relative_path))


def _scope_lineage_items(items: list[Artifact], scope: Artifact | None) -> list[Artifact]:
    """Limit Scope-owned artifacts to the currently selected Scope lineage.

    Increment and Work Package identifiers are local to a shaping lineage and
    may repeat in sibling or historical Scope trees. Repository-wide uniqueness
    would therefore turn valid parallel/history lineages into false failures.
    """
    if scope is None:
        return items
    lineage_root = scope.path.parent
    selected: list[Artifact] = []
    for item in items:
        try:
            item.path.relative_to(lineage_root)
        except ValueError:
            continue
        selected.append(item)
    return selected


def _scope_horizon_ids(scope: Artifact | None) -> tuple[list[str], list[str]]:
    """Read explicit Expansion and Deferred WP bullets from `## Outcome Horizon`.

    The authored section classification is planning authority. WP numbers are
    identifiers only and are never used to infer ordering or promotion.
    """
    if scope is None:
        return [], []

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    bullet_pattern = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
    wp_pattern = re.compile(r"(?i)\bWP[-_]\d{1,6}\b")
    lines = scope.raw_text.splitlines()
    horizon_level: int | None = None
    category: str | None = None
    expansion: list[str] = []
    deferred: list[str] = []

    for line in lines:
        heading = heading_pattern.match(line.strip())
        if heading:
            level = len(heading.group(1))
            title = re.sub(r"[`*_]", "", heading.group(2)).strip().lower()
            if horizon_level is None:
                if title == "outcome horizon":
                    horizon_level = level
                continue
            if level <= horizon_level:
                break
            if title == "expansion":
                category = "expansion"
            elif title == "deferred":
                category = "deferred"
            elif title == "foundation":
                category = "foundation"
            else:
                category = None
            continue

        if horizon_level is None or category not in {"expansion", "deferred"}:
            continue
        bullet = bullet_pattern.match(line)
        if not bullet:
            continue
        match = wp_pattern.search(bullet.group(1))
        identifier = canonical_id(match.group(0)) if match else None
        if not identifier:
            continue
        target = expansion if category == "expansion" else deferred
        if identifier not in target:
            target.append(identifier)

    return expansion, deferred


def _resolve_work_packages(work_packages: list[Artifact], identifiers: list[str]) -> list[Artifact]:
    resolved: list[Artifact] = []
    for identifier in identifiers:
        found = _find_by_id(work_packages, identifier)
        if found is not None:
            resolved.append(found)
    return resolved


def _select_scope(scopes: list[Artifact]) -> Artifact | None:
    if not scopes:
        return None
    canonical = [item for item in scopes if item.path.name.upper() == "SCOPE-SHAPING-RESULT.MD"]
    candidates = canonical or scopes
    status_rank = {"confirmed": 4, "approved": 3, "active": 2, "draft": 1, None: 0}
    return max(
        candidates,
        key=lambda item: (
            status_rank.get(item.status, 0),
            item.modified_at or utc_now(),
            item.relative_path,
        ),
    )


def _selected_increment_id(
    scope: Artifact | None,
    increments: list[Artifact],
    specs: list[Artifact],
) -> tuple[str | None, str]:
    if scope is not None:
        direct = metadata_id(
            scope,
            "selected_increment",
            "selected_increment_id",
            "current_increment",
            "increment_id",
        )
        if direct:
            return direct, f"{scope.relative_path} metadata"

        label_match = re.search(
            r"(?im)^\s*(?:[-*]\s*)?(?:Selected[- ]Increment|Current[- ]Increment)\s*:\s*.*?\b(INC[-_]\d+)\b",
            scope.raw_text,
        )
        if label_match:
            return canonical_id(label_match.group(1)), f"{scope.relative_path} selected-increment field"

        referenced = [item for item in increments if item.identifier in scope.references]
        ready_referenced = [item for item in referenced if item.status == "ready-for-matt"]
        if len(ready_referenced) == 1:
            return ready_referenced[0].identifier, f"{scope.relative_path} ready-for-matt reference"
        if len(referenced) == 1:
            return referenced[0].identifier, f"{scope.relative_path} unique Increment reference"

    ready = [item for item in increments if item.status == "ready-for-matt"]
    if len(ready) == 1:
        return ready[0].identifier, "unique ready-for-matt Increment"

    sourced_ids = {
        metadata_id(spec, "source_increment", "parent_increment")
        for spec in specs
        if metadata_id(spec, "source_increment", "parent_increment")
    }
    if len(sourced_ids) == 1:
        return next(iter(sourced_ids)), "unique Spec Source-Increment"
    return None, "none"


def _find_by_id(items: list[Artifact], identifier: str | None) -> Artifact | None:
    if not identifier:
        return None
    normalized = canonical_id(identifier)
    matches = [item for item in items if item.identifier == normalized]
    return _newest(matches)


def _select_work_package(
    work_packages: list[Artifact],
    scope: Artifact | None,
    increment: Artifact | None,
) -> Artifact | None:
    explicit: str | None = None
    if increment is not None:
        explicit = metadata_id(
            increment,
            "parent_work_package",
            "source_work_package",
            "work_package",
            "work_package_id",
        )
        if explicit is None:
            referenced = [item for item in work_packages if item.identifier in increment.references]
            if len(referenced) == 1:
                return referenced[0]
    if explicit is None and scope is not None:
        explicit = metadata_id(
            scope,
            "selected_work_package",
            "current_work_package",
            "work_package",
            "work_package_id",
        )
    if explicit:
        found = _find_by_id(work_packages, explicit)
        if found:
            return found
    active = [item for item in work_packages if item.status in {"scoped", "active", "confirmed"}]
    if len(active) == 1:
        return active[0]
    if scope is not None:
        referenced = [item for item in work_packages if item.identifier in scope.references]
        if referenced:
            return sorted(referenced, key=lambda item: natural_id_key(item.identifier))[0]
    return _newest(active) if active else None


def _clean_slug(value: str | None) -> str | None:
    if not value:
        return None
    clean = value.strip().strip("`/ ")
    clean = clean.replace("\\", "/")
    if clean.startswith("docs/planning/work/"):
        clean = clean[len("docs/planning/work/") :]
    return clean.split("/", 1)[0] or None


def _select_work_slug(
    scope: Artifact | None,
    increment: Artifact | None,
    specs: list[Artifact],
    tickets: list[Artifact],
) -> str | None:
    for artifact in (increment, scope):
        if artifact is None:
            continue
        value = metadata_value(artifact, "suggested_work_slug", "work_slug")
        if value:
            return _clean_slug(value)

    if increment is not None and increment.identifier:
        matching_specs = [
            spec
            for spec in specs
            if metadata_id(spec, "source_increment", "parent_increment") == increment.identifier
        ]
        if matching_specs:
            selected = _newest(matching_specs)
            return selected.work_slug if selected else None

    slugs = {item.work_slug for item in [*specs, *tickets] if item.work_slug}
    if len(slugs) == 1:
        return next(iter(slugs))
    if slugs:
        newest = _newest([item for item in [*specs, *tickets] if item.work_slug])
        return newest.work_slug if newest else None
    return None


def _select_spec(
    specs: list[Artifact],
    increment: Artifact | None,
    work_slug: str | None,
) -> Artifact | None:
    candidates: list[Artifact] = []
    if increment is not None and increment.identifier:
        source_matches = [
            spec
            for spec in specs
            if metadata_id(spec, "source_increment", "parent_increment") == increment.identifier
        ]
        if work_slug:
            candidates = [spec for spec in source_matches if spec.work_slug == work_slug]
        else:
            candidates = source_matches
    if not candidates and work_slug:
        candidates = [spec for spec in specs if spec.work_slug == work_slug]
    if not candidates and increment is None and len({spec.work_slug for spec in specs if spec.work_slug}) <= 1:
        candidates = specs
    if not candidates:
        return None
    rank = {"approved": 3, "confirmed": 2, "draft": 1, None: 0}
    return max(
        candidates,
        key=lambda item: (rank.get(item.status, 0), item.modified_at or utc_now(), item.relative_path),
    )


def _select_tickets(
    tickets: list[Artifact],
    *,
    current_increment: Artifact | None,
    current_work_slug: str | None,
    current_spec: Artifact | None,
) -> list[Artifact]:
    selected: list[Artifact] = []
    if current_increment is not None and current_increment.identifier:
        source_matches = [
            ticket
            for ticket in tickets
            if metadata_id(ticket, "source_increment", "parent_increment") == current_increment.identifier
        ]
        if current_work_slug:
            selected = [ticket for ticket in source_matches if ticket.work_slug == current_work_slug]
        else:
            selected = source_matches
    if not selected and current_work_slug:
        selected = [ticket for ticket in tickets if ticket.work_slug == current_work_slug]
    if not selected and current_spec is not None and current_spec.work_slug:
        selected = [ticket for ticket in tickets if ticket.work_slug == current_spec.work_slug]
    if not selected and current_increment is None:
        slugs = {ticket.work_slug for ticket in tickets if ticket.work_slug}
        if len(slugs) <= 1:
            selected = tickets
    return selected


def _validate_tickets(state: ProjectState) -> None:
    seen: dict[str, Artifact] = {}
    allowed = {"done", "ready", "blocked", "draft"}
    for ticket in state.tickets:
        if ticket.identifier is None:
            state.issues.append(
                Issue("IIS200", "A current Ticket has no recognizable TKT/TICKET identifier.", "error", ticket.relative_path)
            )
        elif ticket.identifier in seen:
            state.issues.append(
                Issue(
                    "IIS202",
                    f"Duplicate current Ticket identifier {ticket.identifier}.",
                    "error",
                    ticket.relative_path,
                )
            )
        else:
            seen[ticket.identifier] = ticket
        if ticket.status is None:
            state.issues.append(
                Issue("IIS201", "A current Ticket has no Status field.", "error", ticket.relative_path)
            )
        elif ticket.status not in allowed:
            state.issues.append(
                Issue(
                    "IIS203",
                    f"Current Ticket status '{ticket.status}' is not one of done, ready, blocked, or draft.",
                    "error",
                    ticket.relative_path,
                )
            )


def _validate_planning_links(
    artifacts: list[Artifact], planning_root: Path, state: ProjectState
) -> None:
    repo = planning_root.parent.parent
    emitted: set[tuple[str, str]] = set()
    for artifact in artifacts:
        for raw_target in artifact.link_targets:
            target = unquote(raw_target.split("#", 1)[0].split("?", 1)[0]).strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if not target.lower().endswith(".md"):
                continue
            candidate = (repo / target.lstrip("/")) if target.startswith("docs/") else (artifact.path.parent / target)
            try:
                candidate.relative_to(repo)
            except ValueError:
                continue
            if not candidate.exists():
                key = (artifact.relative_path, target)
                if key not in emitted:
                    emitted.add(key)
                    state.issues.append(
                        Issue(
                            "IIS301",
                            f"Planning link target does not exist: {target}",
                            "warning",
                            artifact.relative_path,
                        )
                    )


def _validate_association(
    state: ProjectState,
    specs: list[Artifact],
    tickets: list[Artifact],
) -> None:
    if state.current_increment is not None and state.current_spec is not None:
        source = metadata_id(state.current_spec, "source_increment", "parent_increment")
        if source and source != state.current_increment.identifier:
            state.issues.append(
                Issue(
                    "IIS401",
                    f"Current Spec Source-Increment {source} does not match selected {state.current_increment.identifier}.",
                    "error",
                    state.current_spec.relative_path,
                )
            )
    if state.current_work_slug and not state.current_spec and any(
        spec.work_slug == state.current_work_slug for spec in specs
    ):
        state.issues.append(
            Issue(
                "IIS402",
                f"Specs exist under work slug '{state.current_work_slug}' but none could be associated with the current unit.",
                "warning",
            )
        )
    if not state.tickets and state.current_work_slug and any(
        ticket.work_slug == state.current_work_slug for ticket in tickets
    ):
        state.issues.append(
            Issue(
                "IIS403",
                f"Tickets exist under work slug '{state.current_work_slug}' but none could be associated with the current unit.",
                "warning",
            )
        )
