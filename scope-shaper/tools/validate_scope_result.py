#!/usr/bin/env python3
"""Validate one confirmed Scope Shaping result and its selected construction Increment.

The validator checks structural integrity, canonical paths, horizontal Work Package
boundary drift, and selected-Increment drift. It does not grade product judgment.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PRODUCT_THESIS_TOOLS = REPO_ROOT / "product-thesis" / "tools"
if str(PRODUCT_THESIS_TOOLS) not in sys.path:
    sys.path.insert(0, str(PRODUCT_THESIS_TOOLS))

from iis_path_contract import (  # noqa: E402
    PathContractError,
    canonical_project_root,
    require_canonical_owned_directory,
    require_canonical_regular_file,
    require_work_slug,
)
from product_meaning_binding import ProductMeaningBindingError, parse_binding  # noqa: E402


class ValidationError(Exception):
    pass


@dataclass(frozen=True)
class Package:
    package_id: str
    title: str
    outcome: str
    includes: tuple[str, ...]
    excludes: tuple[str, ...]
    dependencies: tuple[str, ...]
    decisions_reserved: tuple[str, ...]


@dataclass(frozen=True)
class ConstructionCandidate:
    candidate_id: str
    outcome_area: str | None
    current_state: str
    target_state: str
    actor_or_operator: str
    trigger_or_inspection_target: str
    observable_result: str
    authoritative_readback: str
    durable_foundation: str
    future_policy_avoided: str
    disposition: str
    reason: str


@dataclass(frozen=True)
class Increment:
    increment_id: str
    title: str
    work_package: str | None
    suggested_work_slug: str
    selected_candidate: str
    current_state: str
    target_state: str
    observable_outcome: str
    includes: tuple[str, ...]
    excludes: tuple[str, ...]
    required_dependencies: tuple[str, ...]
    preserved_foundations: tuple[str, ...]
    decisions_reserved: tuple[str, ...]
    deferred: tuple[str, ...]
    verification_boundary: str
    reentry_contract: str
    delivery_context: tuple[str, ...]
    artifact: str


@dataclass(frozen=True)
class SourceResult:
    path: Path
    project_root: str
    work_slug: str
    scope_revision: str
    shape: str
    increment: Increment
    packages: dict[str, Package]
    deferred_packages: frozenset[str]


def _metadata(text: str, key: str) -> str:
    matches = re.findall(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one {key} metadata line")
    return matches[0].strip()


def _field(block: str, label: str) -> str:
    matches = re.findall(rf"(?m)^{re.escape(label)}:\s*(.+?)\s*$", block)
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one {label} field")
    value = matches[0].strip()
    if not value:
        raise ValidationError(f"{label} must not be empty")
    return value


def _field_only_block(block: str, labels: tuple[str, ...], context: str) -> dict[str, str]:
    values = {label: _field(block, label) for label in labels}
    allowed_prefixes = tuple(f"{label}:" for label in labels)
    for line in block.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(allowed_prefixes):
            raise ValidationError(f"{context} contains unexpected content: {stripped}")
    return values


def _section(text: str, heading: str, level: int = 2) -> str:
    marker = "#" * level + " " + heading
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}\s*$", text))
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one section: {marker}")
    match = matches[0]
    start = match.end()
    next_heading = re.search(rf"(?m)^#{{1,{level}}}\s+", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _subsection(block: str, heading: str, level: int) -> str:
    marker = "#" * level + " " + heading
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}\s*$", block))
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one subsection: {marker}")
    match = matches[0]
    start = match.end()
    next_heading = re.search(rf"(?m)^#{{1,{level}}}\s+", block[start:])
    end = start + next_heading.start() if next_heading else len(block)
    return block[start:end].strip()


def _items(block: str) -> tuple[str, ...]:
    stripped = block.strip()
    if stripped == "None":
        return ()
    if not stripped:
        raise ValidationError("expected Markdown list items or exact None")
    if any(not line.startswith("- ") for line in stripped.splitlines()):
        raise ValidationError("expected Markdown list items or exact None")
    items = tuple(x.strip() for x in re.findall(r"(?m)^-\s+(.+?)\s*$", block))
    if not items:
        raise ValidationError("expected Markdown list items or exact None")
    return items


def _nonempty(block: str, label: str) -> str:
    value = block.strip()
    if not value:
        raise ValidationError(f"{label} must not be empty")
    return value


def _validate_product_meaning_binding(text: str) -> None:
    if "## Product Meaning Binding" not in text:
        return
    try:
        parse_binding(text)
    except ProductMeaningBindingError as exc:
        raise ValidationError(f"Product Meaning Binding: {exc}") from exc


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _normalize_lines(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_normalize(item) for item in items)


def _path_error(action) -> None:
    try:
        action()
    except PathContractError as exc:
        raise ValidationError(str(exc)) from exc


def _validate_scope_path(path: Path, project_root: str, work_slug: str) -> Path:
    try:
        root = canonical_project_root(project_root, writable=True)
        require_work_slug(work_slug)
    except PathContractError as exc:
        raise ValidationError(str(exc)) from exc

    current = root
    for component in ("docs", "planning", "scope-shaping", work_slug):
        current = current / component
        _path_error(lambda current=current: require_canonical_owned_directory(current, writable=True))
    expected = current / "SCOPE-SHAPING-RESULT.md"
    if path != expected:
        raise ValidationError(f"Scope result must be exactly {expected}")
    return root


def _shape_ordinal(value: str) -> int:
    match = re.fullmatch(r"SHAPE-(\d{3})", value)
    if match is None or int(match.group(1)) < 1:
        raise ValidationError("Scope-Revision must be SHAPE-NNN with an ordinal of at least 001")
    return int(match.group(1))


def _revision_path(source: Path, revision: str) -> Path:
    _shape_ordinal(revision)
    revision_root = source.parent / "revisions"
    _path_error(lambda: require_canonical_owned_directory(revision_root, writable=True))
    path = revision_root / f"{revision}.md"
    _path_error(lambda: require_canonical_regular_file(path))
    return path


def _validate_revision_identity(path: Path, text: str, *, project_root: str, work_slug: str) -> str:
    revision = _metadata(text, "Scope-Revision")
    _shape_ordinal(revision)
    if path.name != f"{revision}.md":
        raise ValidationError(f"{path}: Scope-Revision filename drift")
    if _metadata(text, "Status") != "confirmed":
        raise ValidationError(f"{path}: Status must be confirmed")
    if _metadata(text, "Project-Root") != project_root:
        raise ValidationError(f"{path}: Project-Root drift")
    if _metadata(text, "Work-Slug") != work_slug:
        raise ValidationError(f"{path}: Work-Slug drift")
    return revision


def _parse_packages(text: str) -> dict[str, Package]:
    proposal = _section(text, "Work Package Proposal")
    packages_block = _subsection(proposal, "Proposed Work Packages", 3)
    matches = list(re.finditer(r"(?m)^####\s+(WP-\d{3}):\s+(.+?)\s*$", packages_block))
    if not matches:
        raise ValidationError("initiative result has no proposed Work Packages")
    result: dict[str, Package] = {}
    for index, match in enumerate(matches):
        package_id, title = match.group(1), match.group(2).strip()
        if package_id in result:
            raise ValidationError(f"duplicate Work Package ID: {package_id}")
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(packages_block)
        body = packages_block[start:end]
        result[package_id] = Package(
            package_id=package_id,
            title=title,
            outcome=_nonempty(_subsection(body, "Outcome", 5), f"{package_id} Outcome"),
            includes=_items(_subsection(body, "Includes", 5)),
            excludes=_items(_subsection(body, "Excludes", 5)),
            dependencies=_items(_subsection(body, "Depends On", 5)),
            decisions_reserved=_items(_subsection(body, "Decisions Reserved For Matt", 5)),
        )
    return result


def _outcome_horizon(text: str) -> tuple[set[str], set[str], set[str]]:
    proposal = _section(text, "Work Package Proposal")
    horizon = _subsection(proposal, "Outcome Horizon", 3)
    groups = tuple(_items(_subsection(horizon, name, 4)) for name in ("Foundation", "Expansion", "Deferred"))
    if any(len(group) != len(set(group)) for group in groups):
        raise ValidationError("Outcome Horizon groups must not contain duplicate Work Packages")
    return tuple(set(group) for group in groups)  # type: ignore[return-value]


def _cycle(packages: dict[str, Package]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dependency in packages[node].dependencies:
            if visit(dependency):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in packages)


def _parse_construction_candidates(text: str) -> dict[str, ConstructionCandidate]:
    block = _section(text, "Construction Candidates")
    matches = list(re.finditer(r"(?m)^###\s+(Candidate\s+[^\n]+?)\s*$", block))
    if not matches:
        raise ValidationError("Construction Candidates must contain at least one Candidate")
    labels = (
        "Outcome Area",
        "Current Product State",
        "Target Product State",
        "Actor Or Operator",
        "Trigger Or Inspection Target",
        "Observable Result",
        "Authoritative Readback",
        "Durable Foundation",
        "Future Policy Avoided",
        "Lead Disposition",
        "Reason",
    )
    result: dict[str, ConstructionCandidate] = {}
    for index, match in enumerate(matches):
        candidate_id = " ".join(match.group(1).split())
        if candidate_id in result:
            raise ValidationError(f"duplicate construction candidate: {candidate_id}")
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        body = block[start:end].strip()
        values = _field_only_block(body, labels, candidate_id)
        outcome_raw = values["Outcome Area"]
        if outcome_raw == "None":
            outcome_area = None
        elif re.fullmatch(r"WP-\d{3}", outcome_raw):
            outcome_area = outcome_raw
        else:
            raise ValidationError(f"{candidate_id} Outcome Area must be None or WP-NNN")
        disposition = values["Lead Disposition"]
        if disposition not in {"SELECT", "REJECT"}:
            raise ValidationError(f"{candidate_id} Lead Disposition must be SELECT or REJECT")
        result[candidate_id] = ConstructionCandidate(
            candidate_id=candidate_id,
            outcome_area=outcome_area,
            current_state=values["Current Product State"],
            target_state=values["Target Product State"],
            actor_or_operator=values["Actor Or Operator"],
            trigger_or_inspection_target=values["Trigger Or Inspection Target"],
            observable_result=values["Observable Result"],
            authoritative_readback=values["Authoritative Readback"],
            durable_foundation=values["Durable Foundation"],
            future_policy_avoided=values["Future Policy Avoided"],
            disposition=disposition,
            reason=values["Reason"],
        )
    if sum(candidate.disposition == "SELECT" for candidate in result.values()) != 1:
        raise ValidationError("Construction Candidates must contain exactly one SELECT disposition")
    return result


def _observable_contract(block: str, context: str) -> dict[str, str]:
    return _field_only_block(
        block,
        (
            "Actor Or Operator",
            "Trigger Or Inspection Target",
            "Observable Result",
            "Authoritative Readback",
        ),
        context,
    )


def _parse_selected_increment(text: str) -> Increment:
    section = _section(text, "Selected Next Increment")
    matches = list(re.finditer(r"(?m)^###\s+(INC-\d{3}):\s+(.+?)\s*$", section))
    if len(matches) != 1:
        raise ValidationError("Selected Next Increment must contain exactly one INC-NNN")
    match = matches[0]
    increment_id, title = match.group(1), match.group(2).strip()
    body = section[match.end():]
    work_package_raw = _subsection(body, "Work Package", 4).strip()
    if work_package_raw == "None":
        work_package = None
    elif re.fullmatch(r"WP-\d{3}", work_package_raw):
        work_package = work_package_raw
    else:
        raise ValidationError("Selected Increment Work Package must be None or WP-NNN")
    suggested_work_slug = _nonempty(_subsection(body, "Suggested Work Slug", 4), "Increment Suggested Work Slug")
    try:
        require_work_slug(suggested_work_slug)
    except PathContractError as exc:
        raise ValidationError(f"invalid Increment Suggested Work Slug: {exc}") from exc
    selected_candidate = _nonempty(_subsection(body, "Selected Candidate", 4), "Increment Selected Candidate")
    if not selected_candidate.startswith("Candidate "):
        raise ValidationError("Increment Selected Candidate must name one Candidate <label>")
    observable_outcome = _nonempty(_subsection(body, "Observable Outcome", 4), "Increment Observable Outcome")
    _observable_contract(observable_outcome, "Increment Observable Outcome")
    artifact = _subsection(body, "Artifact", 4).strip()
    return Increment(
        increment_id=increment_id,
        title=title,
        work_package=work_package,
        suggested_work_slug=suggested_work_slug,
        selected_candidate=selected_candidate,
        current_state=_nonempty(_subsection(body, "Current Product State", 4), "Increment Current Product State"),
        target_state=_nonempty(_subsection(body, "Target Product State", 4), "Increment Target Product State"),
        observable_outcome=observable_outcome,
        includes=_items(_subsection(body, "Includes", 4)),
        excludes=_items(_subsection(body, "Excludes", 4)),
        required_dependencies=_items(_subsection(body, "Required Product Dependencies", 4)),
        preserved_foundations=_items(_subsection(body, "Preserved Foundations", 4)),
        decisions_reserved=_items(_subsection(body, "Decisions Reserved For Matt", 4)),
        deferred=_items(_subsection(body, "Deferred Until Re-entry", 4)),
        verification_boundary=_nonempty(_subsection(body, "Verification Boundary", 4), "Increment Verification Boundary"),
        reentry_contract=_nonempty(_subsection(body, "Re-entry Contract", 4), "Increment Re-entry Contract"),
        delivery_context=_items(_subsection(body, "Delivery Context", 4)),
        artifact=artifact,
    )


def _validate_package_file(source: Path, project_root: str, package: Package) -> None:
    package_root = source.parent / "work-packages"
    _path_error(lambda: require_canonical_owned_directory(package_root, writable=True))
    path = package_root / f"{package.package_id}.md"
    _path_error(lambda: require_canonical_regular_file(path))
    text = path.read_text(encoding="utf-8")
    if _metadata(text, "Status") != "scoped":
        raise ValidationError(f"{path}: Status must be scoped")
    if "ready-for-matt" in _metadata(text, "Status"):
        raise ValidationError(f"{path}: Work Package cannot be ready-for-matt")
    if _metadata(text, "Project-Root") != project_root:
        raise ValidationError(f"{path}: Project-Root drift")
    if _metadata(text, "Work-Package") != package.package_id:
        raise ValidationError(f"{path}: Work-Package drift")
    if _metadata(text, "Source-Scope-Result") != "../SCOPE-SHAPING-RESULT.md":
        raise ValidationError(f"{path}: Source-Scope-Result drift")
    if _normalize(_section(text, "Package Outcome")) != _normalize(package.outcome):
        raise ValidationError(f"{path}: Outcome drift")
    if _normalize_lines(_items(_section(text, "Included Product Scope"))) != _normalize_lines(package.includes):
        raise ValidationError(f"{path}: Includes drift")
    if _normalize_lines(_items(_section(text, "Excluded Sibling Scope"))) != _normalize_lines(package.excludes):
        raise ValidationError(f"{path}: Excludes drift")
    if _items(_section(text, "Dependencies")) != package.dependencies:
        raise ValidationError(f"{path}: Dependencies drift")
    if _normalize_lines(_items(_section(text, "Decisions Reserved For Matt"))) != _normalize_lines(package.decisions_reserved):
        raise ValidationError(f"{path}: Decisions Reserved For Matt drift")


def _validate_common_sections(text: str) -> Increment:
    _validate_product_meaning_binding(text)
    _nonempty(_section(text, "Intent Horizon"), "Intent Horizon")
    _items(_section(text, "Current Product State"))
    _items(_section(text, "Investigation Assignments"))
    _nonempty(_section(text, "Verified Material Claims"), "Verified Material Claims")
    boundary = _section(text, "Planning Boundary")
    _nonempty(_subsection(boundary, "Outcome", 3), "Planning Boundary Outcome")
    _items(_subsection(boundary, "Includes", 3))
    _items(_subsection(boundary, "Excludes", 3))
    for heading in (
        "Planning Constraints",
        "Candidate Outcome Areas",
        "Product Capability Dependencies",
        "Decisions Reserved For Matt",
        "Delivery Context",
        "Outside The Assessed Landscape",
        "Provisional Construction Horizon",
    ):
        _items(_section(text, heading))
    _parse_construction_candidates(text)
    increment = _parse_selected_increment(text)
    if _section(text, "Unresolved Material Questions").strip() != "None":
        raise ValidationError("Unresolved Material Questions must be None")
    _section(text, "Confirmation")
    _metadata(text, "Confirmed By")
    _metadata(text, "Confirmed Scope")
    return increment


def _validate_candidate_closure(
    text: str,
    increment: Increment,
    *,
    shape: str,
    package_ids: set[str],
) -> None:
    candidates = _parse_construction_candidates(text)
    selected = [candidate for candidate in candidates.values() if candidate.disposition == "SELECT"]
    assert len(selected) == 1
    candidate = selected[0]
    if increment.selected_candidate != candidate.candidate_id:
        raise ValidationError("Selected Next Increment must name the exactly one SELECT construction candidate")

    if shape == "bounded":
        if any(item.outcome_area is not None for item in candidates.values()):
            raise ValidationError("bounded construction candidates must use Outcome Area: None")
        if increment.work_package is not None:
            raise ValidationError("bounded Selected Increment Work Package must be None")
    elif shape == "initiative":
        for item in candidates.values():
            if item.outcome_area is None or item.outcome_area not in package_ids:
                raise ValidationError(f"{item.candidate_id} must reference one proposed Work Package")
        if candidate.outcome_area != increment.work_package:
            raise ValidationError("Selected construction candidate Outcome Area must match Selected Increment Work Package")
    else:
        raise ValidationError("Planning-Shape must be bounded or initiative")

    if _normalize(candidate.current_state) != _normalize(increment.current_state):
        raise ValidationError("Selected construction candidate Current Product State drift")
    if _normalize(candidate.target_state) != _normalize(increment.target_state):
        raise ValidationError("Selected construction candidate Target Product State drift")

    observable = _observable_contract(increment.observable_outcome, "Increment Observable Outcome")
    expected = {
        "Actor Or Operator": candidate.actor_or_operator,
        "Trigger Or Inspection Target": candidate.trigger_or_inspection_target,
        "Observable Result": candidate.observable_result,
        "Authoritative Readback": candidate.authoritative_readback,
    }
    for label, value in expected.items():
        if _normalize(observable[label]) != _normalize(value):
            raise ValidationError(f"Selected construction candidate {label} drift")


def _validate_increment_contract(path: Path, text: str, increment: Increment, *, project_root: str) -> str:
    if _metadata(text, "Project-Root") != project_root:
        raise ValidationError(f"{path}: Project-Root drift")
    if _metadata(text, "Increment") != increment.increment_id:
        raise ValidationError(f"{path}: Increment drift")
    expected_package = increment.work_package or "None"
    if _metadata(text, "Work-Package") != expected_package:
        raise ValidationError(f"{path}: Work-Package drift")
    work_slug = _metadata(text, "Suggested-Work-Slug")
    try:
        require_work_slug(work_slug)
    except PathContractError as exc:
        raise ValidationError(f"{path}: invalid Suggested-Work-Slug: {exc}") from exc
    if work_slug != increment.suggested_work_slug:
        raise ValidationError(f"{path}: Suggested-Work-Slug drift")

    scalar_sections = (
        ("Current Product State", increment.current_state),
        ("Target Product State", increment.target_state),
        ("Observable Outcome", increment.observable_outcome),
        ("Verification Boundary", increment.verification_boundary),
        ("Re-entry Contract", increment.reentry_contract),
    )
    for heading, source_value in scalar_sections:
        if _normalize(_section(text, heading)) != _normalize(source_value):
            raise ValidationError(f"{path}: {heading} drift")

    list_sections = (
        ("Includes", increment.includes),
        ("Excludes", increment.excludes),
        ("Required Product Dependencies", increment.required_dependencies),
        ("Preserved Foundations", increment.preserved_foundations),
        ("Decisions Reserved For Matt", increment.decisions_reserved),
        ("Deferred Until Re-entry", increment.deferred),
        ("Delivery Context", increment.delivery_context),
    )
    for heading, source_items in list_sections:
        if _normalize_lines(_items(_section(text, heading))) != _normalize_lines(source_items):
            raise ValidationError(f"{path}: {heading} drift")
    return work_slug


def _validate_unique_increment_work_slug(source: SourceResult, selected_path: Path, work_slug: str) -> None:
    scope_root = Path(source.project_root) / "docs" / "planning" / "scope-shaping"
    _path_error(lambda: require_canonical_owned_directory(scope_root, writable=True))
    for candidate in scope_root.glob("*/increments/INC-*.md"):
        if candidate == selected_path:
            continue
        _path_error(lambda candidate=candidate: require_canonical_regular_file(candidate))
        candidate_text = candidate.read_text(encoding="utf-8")
        if _metadata(candidate_text, "Suggested-Work-Slug") == work_slug:
            raise ValidationError(
                f"{selected_path}: Suggested-Work-Slug already belongs to another Scope Increment: {candidate}"
            )


def _validate_source(path: Path) -> SourceResult:
    raw_path = path.expanduser()
    _path_error(lambda: require_canonical_regular_file(raw_path))
    text = raw_path.read_text(encoding="utf-8")
    if _metadata(text, "Status") != "confirmed":
        raise ValidationError("Status must be confirmed")
    _metadata(text, "Owner")
    work_slug = _metadata(text, "Work-Slug")
    project_root = _metadata(text, "Project-Root")
    scope_revision = _metadata(text, "Scope-Revision")
    selected_revision_ordinal = _shape_ordinal(scope_revision)
    _validate_scope_path(raw_path, project_root, work_slug)

    revision = _revision_path(raw_path, scope_revision)
    revision_text = revision.read_text(encoding="utf-8")
    _validate_revision_identity(revision, revision_text, project_root=project_root, work_slug=work_slug)
    if revision.read_bytes() != raw_path.read_bytes():
        raise ValidationError("current Scope result must match its immutable Scope-Revision byte-for-byte")
    for candidate in revision.parent.glob("SHAPE-*.md"):
        if not re.fullmatch(r"SHAPE-\d{3}\.md", candidate.name):
            raise ValidationError(f"invalid Scope revision filename: {candidate.name}")
        if _shape_ordinal(candidate.stem) > selected_revision_ordinal:
            raise ValidationError("Scope-Revision must be the highest current SHAPE-NNN revision")

    increment = _validate_common_sections(text)
    if increment.artifact != f"./increments/{increment.increment_id}.md":
        raise ValidationError("Selected Increment Artifact must be ./increments/INC-NNN.md")

    shape = _metadata(text, "Planning-Shape")
    packages: dict[str, Package] = {}
    deferred_packages: frozenset[str] = frozenset()
    if shape == "bounded":
        if re.search(r"(?m)^## Work Package Proposal\s*$", text):
            raise ValidationError("bounded result must not contain Work Package Proposal")
        if increment.work_package is not None:
            raise ValidationError("bounded Selected Increment Work Package must be None")
    elif shape == "initiative":
        packages = _parse_packages(text)
        package_ids = set(packages)
        for package in packages.values():
            missing = set(package.dependencies) - package_ids
            if missing:
                raise ValidationError(f"{package.package_id}: missing dependencies {sorted(missing)}")
            if package.package_id in package.dependencies:
                raise ValidationError(f"{package.package_id}: self dependency")
        if _cycle(packages):
            raise ValidationError("dependency cycle detected")
        foundation, expansion, deferred = _outcome_horizon(text)
        if (foundation & expansion) or (foundation & deferred) or (expansion & deferred):
            raise ValidationError("Outcome Horizon groups overlap")
        if foundation | expansion | deferred != package_ids:
            raise ValidationError("every Work Package must appear exactly once in Foundation, Expansion, or Deferred")
        if increment.work_package is None or increment.work_package not in package_ids:
            raise ValidationError("initiative Selected Increment must reference one proposed Work Package")
        if increment.work_package in deferred:
            raise ValidationError("Selected Increment cannot reference a Deferred Work Package")
        deferred_packages = frozenset(deferred)
        for package in packages.values():
            _validate_package_file(raw_path, project_root, package)
    else:
        raise ValidationError("Planning-Shape must be bounded or initiative")

    _validate_candidate_closure(text, increment, shape=shape, package_ids=set(packages))

    return SourceResult(
        path=raw_path,
        project_root=project_root,
        work_slug=work_slug,
        scope_revision=scope_revision,
        shape=shape,
        increment=increment,
        packages=packages,
        deferred_packages=deferred_packages,
    )


def _validate_increment_file(source: SourceResult, selected_path: Path | None = None) -> Path:
    increment = source.increment
    increment_root = source.path.parent / "increments"
    _path_error(lambda: require_canonical_owned_directory(increment_root, writable=True))
    expected = increment_root / f"{increment.increment_id}.md"
    if selected_path is not None and selected_path != expected:
        raise ValidationError(f"selected Increment must be exactly {expected}")

    selected_ordinal = int(increment.increment_id.removeprefix("INC-"))
    for candidate in sorted(increment_root.glob("INC-*.md")):
        if not re.fullmatch(r"INC-\d{3}\.md", candidate.name):
            raise ValidationError(f"invalid Increment filename: {candidate.name}")
        _path_error(lambda candidate=candidate: require_canonical_regular_file(candidate))
        if candidate == expected:
            continue
        candidate_id = candidate.stem
        candidate_ordinal = int(candidate_id.removeprefix("INC-"))
        if candidate_ordinal >= selected_ordinal:
            raise ValidationError("Selected Next Increment must use the highest current INC-NNN ordinal")
        candidate_text = candidate.read_text(encoding="utf-8")
        if _metadata(candidate_text, "Status") != "superseded":
            raise ValidationError(f"{candidate}: prior Increment Status must be superseded")
        if _metadata(candidate_text, "Source-Scope-Result") != "../SCOPE-SHAPING-RESULT.md":
            raise ValidationError(f"{candidate}: Source-Scope-Result drift")
        revision_ref = _metadata(candidate_text, "Source-Scope-Revision")
        revision_match = re.fullmatch(r"\.\./revisions/(SHAPE-\d{3})\.md", revision_ref)
        if revision_match is None:
            raise ValidationError(f"{candidate}: invalid Source-Scope-Revision")
        historical_revision = _revision_path(source.path, revision_match.group(1))
        historical_text = historical_revision.read_text(encoding="utf-8")
        _validate_revision_identity(
            historical_revision,
            historical_text,
            project_root=source.project_root,
            work_slug=source.work_slug,
        )
        historical_increment = _validate_common_sections(historical_text)
        historical_shape = _metadata(historical_text, "Planning-Shape")
        historical_packages = _parse_packages(historical_text) if historical_shape == "initiative" else {}
        _validate_candidate_closure(
            historical_text,
            historical_increment,
            shape=historical_shape,
            package_ids=set(historical_packages),
        )
        if historical_increment.increment_id != candidate_id:
            raise ValidationError(f"{candidate}: historical Scope revision selects a different Increment")
        _validate_increment_contract(candidate, candidate_text, historical_increment, project_root=source.project_root)

    _path_error(lambda: require_canonical_regular_file(expected))
    text = expected.read_text(encoding="utf-8")
    if _metadata(text, "Status") != "ready-for-matt":
        raise ValidationError(f"{expected}: Status must be ready-for-matt")
    if _metadata(text, "Source-Scope-Result") != "../SCOPE-SHAPING-RESULT.md":
        raise ValidationError(f"{expected}: Source-Scope-Result drift")
    expected_revision_ref = f"../revisions/{source.scope_revision}.md"
    if _metadata(text, "Source-Scope-Revision") != expected_revision_ref:
        raise ValidationError(f"{expected}: Source-Scope-Revision drift")
    work_slug = _validate_increment_contract(expected, text, increment, project_root=source.project_root)
    _validate_unique_increment_work_slug(source, expected, work_slug)
    return expected


def validate(path: Path) -> None:
    source = _validate_source(path)
    _validate_increment_file(source)


def validate_selected_increment(path: Path) -> Path:
    raw_path = path.expanduser()
    _path_error(lambda: require_canonical_regular_file(raw_path))
    if raw_path.parent.name != "increments" or not re.fullmatch(r"INC-\d{3}\.md", raw_path.name):
        raise ValidationError("selected Increment path must end in increments/INC-NNN.md")
    source = raw_path.parent.parent / "SCOPE-SHAPING-RESULT.md"
    source_result = _validate_source(source)
    validated = _validate_increment_file(source_result, raw_path)
    if validated != raw_path:
        raise ValidationError("selected Increment is not the source's current Selected Next Increment")
    return source


def validate_selected_work_package(path: Path) -> Path:
    raise ValidationError(
        "Work Packages are not current Ask Matt handoffs; a legacy ready Work Package must return to Scope Shaper's Legacy Scope Artifact Compatibility flow, and current planning must select an increments/INC-NNN.md artifact"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("scope_result", type=Path)
    args = parser.parse_args()
    try:
        validate(args.scope_result)
    except (OSError, ValidationError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
