from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json
import re
from urllib.parse import unquote

from .markdown import extract_sections, parse_artifact
from .model import (
    Artifact,
    ArtifactKind,
    Health,
    Issue,
    ProjectState,
    Stage,
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
    direct_scopes = [item for item in scopes if _is_direct_scope(item, planning_root)]

    if direct_scopes:
        _scan_direct_scope(
            state,
            artifacts,
            by_kind,
            direct_scopes,
            planning_root,
            check_links=options.check_links,
        )
    else:
        # Legacy Scope/Increment/Spec/Ticket artifacts are retained as history.
        # They never establish current authority or an automatic Matt/Ticket
        # pointer after the Thesis → Scope cutover.
        state.legacy_history = [item for item in artifacts if item.kind != ArtifactKind.UNKNOWN]
        state.transition_required = _legacy_transition_candidates(state.legacy_history)
        if options.check_links:
            _validate_planning_links(state.legacy_history, planning_root, state)
        state.evidence.update(
            {
                "authority_mode": "legacy-history" if state.legacy_history else "none",
                "artifact_counts": {kind.value: len(items) for kind, items in by_kind.items()},
                "transition_required": [item.relative_path for item in state.transition_required],
            }
        )

    evaluate_next_work(state)
    return state


def _is_direct_scope(artifact: Artifact, planning_root: Path) -> bool:
    """Recognize only docs/planning/work/<slug>/SCOPE.md as direct Scope."""
    if artifact.kind != ArtifactKind.SCOPE or artifact.path.name.upper() != "SCOPE.MD":
        return False
    try:
        relative = artifact.path.relative_to(planning_root.parent.parent)
    except ValueError:
        return False
    return len(relative.parts) == 5 and relative.parts[:3] == ("docs", "planning", "work")


def _scan_direct_scope(
    state: ProjectState,
    artifacts: list[Artifact],
    by_kind: dict[ArtifactKind, list[Artifact]],
    direct_scopes: list[Artifact],
    planning_root: Path,
    *,
    check_links: bool,
) -> None:
    state.direct_scope_mode = True
    state.active_scopes = sorted(
        [item for item in direct_scopes if item.status in {"draft", "ready"}],
        key=lambda item: (item.modified_at or utc_now(), item.relative_path),
    )
    state.scope_history = sorted(
        [item for item in direct_scopes if item.status not in {"draft", "ready"}],
        key=lambda item: (item.modified_at or utc_now(), item.relative_path),
        reverse=True,
    )
    state.legacy_history = [item for item in artifacts if item not in direct_scopes and item.kind != ArtifactKind.UNKNOWN]
    state.transition_required = _legacy_transition_candidates(state.legacy_history)

    if len(state.active_scopes) > 1:
        state.issues.append(
            Issue(
                "IIS502",
                "More than one active direct Scope exists: "
                + ", ".join(item.relative_path for item in state.active_scopes),
                "error",
            )
        )

    candidates = state.active_scopes or [item for item in state.scope_history if item.status == "done"]
    if not candidates:
        candidates = [item for item in state.scope_history if item.status != "superseded"]
    state.current_scope = _newest(candidates) if candidates else None
    if state.current_scope is None and state.scope_history:
        state.issues.append(
            Issue(
                "IIS503",
                "Only superseded direct Scope history is present; a new current Scope is required.",
                "warning",
                state.scope_history[0].relative_path,
            )
        )

    if state.current_scope is not None:
        state.current_work_slug = state.current_scope.work_slug
        state.scope_authority, state.transition_authority = _validate_direct_scope(
            state, state.current_scope
        )
        state.required_outcomes, state.remaining_required_outcomes = _required_outcomes(
            state.scope_authority,
        )

    if check_links:
        _validate_planning_links(artifacts, planning_root, state)
    state.evidence.update(
        {
            "authority_mode": "direct-scope",
            "artifact_counts": {kind.value: len(items) for kind, items in by_kind.items()},
            "active_scopes": [item.relative_path for item in state.active_scopes],
            "scope_history": [item.relative_path for item in state.scope_history],
            "transition_required": [item.relative_path for item in state.transition_required],
            "current_work_slug": state.current_work_slug,
        }
    )


def _source_refs(body: str, label: str, state: ProjectState, scope: Artifact, *, product: bool) -> list[dict[str, str]]:
    match = re.findall(r"^```iis-sources\s*\n(.*?)^```\s*$", body, re.M | re.S)
    if len(match) != 1:
        state.issues.append(Issue("IIS510" if product else "IIS515", f"{label} requires one iis-sources JSON block.", "error", scope.relative_path))
        return []
    try:
        raw = json.loads(match[0])
    except json.JSONDecodeError:
        state.issues.append(Issue("IIS510" if product else "IIS515", f"{label} JSON is invalid.", "error", scope.relative_path))
        return []
    if not isinstance(raw, list) or not raw:
        state.issues.append(Issue("IIS514" if product else "IIS519", f"{label} needs at least one fixed source reference.", "error", scope.relative_path))
        return []
    values: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"snapshot", "path"}:
            state.issues.append(Issue("IIS510" if product else "IIS515", f"{label} source ref must contain snapshot and path.", "error", scope.relative_path))
            continue
        snapshot, path = item.get("snapshot"), item.get("path")
        if not isinstance(snapshot, str) or re.fullmatch(r"snap-[0-9a-f]{32}", snapshot) is None:
            state.issues.append(Issue("IIS510" if product else "IIS515", f"{label} snapshot id is invalid.", "error", scope.relative_path))
            continue
        if not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts:
            state.issues.append(Issue("IIS511" if product else "IIS516", f"{label} path must stay project-relative.", "error", scope.relative_path))
            continue
        if product and not path.startswith("docs/planning/product-thesis/"):
            state.issues.append(Issue("IIS511", f"Product Authority is not a Product Thesis path: {path}", "error", scope.relative_path))
            continue
        key = (snapshot, path)
        if key in seen:
            state.issues.append(Issue("IIS512" if product else "IIS517", f"{label} source is duplicated.", "error", scope.relative_path))
            continue
        seen.add(key)
        live = state.repository_path / path
        values.append({
            "snapshot": snapshot,
            "path": path,
            "live_path": str(live),
            "current": "admission-required",
        })
    return values


def _validate_direct_scope(
    state: ProjectState,
    scope: Artifact,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Validate observable iis-scope/v2 structure without pretending to perform admission."""
    allowed_statuses = {"draft", "ready", "done", "superseded"}
    if scope.status not in allowed_statuses:
        state.issues.append(
            Issue(
                "IIS504",
                f"Direct Scope status '{scope.status or 'missing'}' is not draft, ready, done, or superseded.",
                "error",
                scope.relative_path,
            )
        )
    if scope.metadata.get("schema") != "iis-scope/v2":
        state.issues.append(
            Issue("IIS505", "Direct Scope does not declare Schema: iis-scope/v2.", "error", scope.relative_path)
        )

    project_root = scope.metadata.get("project_root")
    if not project_root:
        state.issues.append(Issue("IIS506", "Direct Scope has no Project-Root metadata.", "error", scope.relative_path))
    else:
        try:
            declared_root = Path(project_root).expanduser().resolve()
        except (OSError, RuntimeError, ValueError):
            declared_root = None
        if declared_root != state.repository_path:
            state.issues.append(
                Issue(
                    "IIS507",
                    f"Direct Scope Project-Root does not match the scanned repository: {project_root}",
                    "error",
                    scope.relative_path,
                )
            )

    for key, label in (
        ("section_product_authority", "Product Authority"),
        ("section_outcome", "Outcome"),
        ("section_acceptance", "Acceptance"),
    ):
        if not scope.metadata.get(key, "").strip():
            state.issues.append(Issue("IIS508", f"Direct Scope has no nonempty {label} section.", "error", scope.relative_path))

    open_decisions = scope.metadata.get("section_open_decisions", "").strip()
    if scope.status in {"ready", "done"} and open_decisions and open_decisions.lower() != "none":
        state.issues.append(
            Issue(
                "IIS509",
                "Ready/done direct Scope has unresolved Open Decisions.",
                "error",
                scope.relative_path,
            )
        )

    authorities = _source_refs(
        scope.metadata.get("section_product_authority", ""),
        "Product Authority",
        state,
        scope,
        product=True,
    )
    transition = _parse_transition_authority(state, scope)
    return authorities, transition


def _parse_transition_authority(state: ProjectState, scope: Artifact) -> list[dict[str, str]]:
    body = scope.metadata.get("section_transition_authority")
    if body is None:
        return []
    return _source_refs(body, "Transition Authority", state, scope, product=False)


def _required_outcomes(
    authorities: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    all_outcomes: list[dict[str, str]] = []
    for authority in authorities:
        source = Path(authority.get("live_path", ""))
        if not source.is_file():
            continue
        try:
            thesis = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        sections = extract_sections(thesis)
        body = next(
            (value for heading, value in sections.items() if _normalize_match_text(heading) in {"required outcomes means", "required outcomes"}),
            "",
        )
        if not body or body.strip().lower() == "none":
            continue
        bullets = [
            re.sub(r"^\s*[-*+]\s+", "", line).strip()
            for line in body.splitlines()
            if re.match(r"^\s*[-*+]\s+", line)
        ]
        values = bullets or [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()]
        for value in values:
            if value.lower() == "none":
                continue
            entry = {
                "text": value,
                "source": f"{authority['snapshot']}:{authority['path']}",
                "status": "unassessed",
            }
            all_outcomes.append(entry)
    return all_outcomes, list(all_outcomes)

def _normalize_match_text(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", value.lower()).strip()


def _legacy_transition_candidates(artifacts: list[Artifact]) -> list[Artifact]:
    candidates: list[Artifact] = []
    for artifact in artifacts:
        status = artifact.status
        if artifact.kind == ArtifactKind.TICKET:
            needed = status != "done"
        elif artifact.kind == ArtifactKind.SPEC:
            needed = status not in {"approved", "done", "superseded"}
        elif artifact.kind == ArtifactKind.INCREMENT:
            needed = status not in {"done", "superseded", "complete", "closed", "verified"}
        elif artifact.kind == ArtifactKind.WORK_PACKAGE:
            needed = status not in {"done", "complete", "closed", "verified", "deferred", "rejected"}
        elif artifact.kind == ArtifactKind.SCOPE:
            needed = status not in {"confirmed", "approved", "done", "superseded", "complete", "closed", "verified"}
        else:
            needed = False
        if needed:
            candidates.append(artifact)
    return sorted(candidates, key=lambda item: (item.relative_path, item.status or ""))


def _load_artifacts(planning_root: Path, options: ScanOptions, state: ProjectState) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for path in sorted(planning_root.rglob("*.md")):
        try:
            relative = path.relative_to(planning_root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0].lower() in {"observatory", "adaptive"}:
            # Derived Observatory files and Adaptive provenance never become
            # canonical Scope/Increment/Spec/Ticket authority.
            continue
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


