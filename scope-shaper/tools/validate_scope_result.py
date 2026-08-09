#!/usr/bin/env python3
"""Validate one confirmed Scope Shaping result and its thin Work Package files.

This validator checks structural integrity and boundary drift. It does not grade
product judgment or explanatory prose.
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

from iis_path_contract import (  # noqa: E402
    PathContractError,
    canonical_project_root,
    require_canonical_owned_directory,
    require_canonical_regular_file,
    require_work_slug,
)


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


def _metadata(text: str, key: str) -> str:
    matches = re.findall(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one {key} metadata line")
    return matches[0].strip()


def _section(text: str, heading: str, level: int = 2) -> str:
    marker = "#" * level + " " + heading
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}\s*$", text))
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one section: {marker}")
    m = matches[0]
    start = m.end()
    next_heading = re.search(rf"(?m)^#{{1,{level}}}\s+", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _subsection(block: str, heading: str, level: int) -> str:
    marker = "#" * level + " " + heading
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}\s*$", block))
    if len(matches) != 1:
        raise ValidationError(f"expected exactly one subsection: {marker}")
    m = matches[0]
    start = m.end()
    next_heading = re.search(rf"(?m)^#{{1,{level}}}\s+", block[start:])
    end = start + next_heading.start() if next_heading else len(block)
    return block[start:end].strip()


def _items(block: str) -> tuple[str, ...]:
    stripped = block.strip()
    if stripped == "None":
        return ()
    if any(not line.startswith("- ") for line in stripped.splitlines()):
        raise ValidationError("expected Markdown list items or exact None")
    items = tuple(x.strip() for x in re.findall(r"(?m)^-\s+(.+?)\s*$", block))
    if not items:
        raise ValidationError("expected Markdown list items or exact None")
    return items


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
        outcome = _subsection(body, "Outcome", 5).strip()
        includes = _items(_subsection(body, "Includes", 5))
        excludes = _items(_subsection(body, "Excludes", 5))
        dependencies = _items(_subsection(body, "Depends On", 5))
        decisions_reserved = _items(_subsection(body, "Decisions Reserved For Matt", 5))
        result[package_id] = Package(
            package_id,
            title,
            outcome,
            includes,
            excludes,
            dependencies,
            decisions_reserved,
        )
    return result


def _release_cut(text: str) -> tuple[set[str], set[str], set[str]]:
    proposal = _section(text, "Work Package Proposal")
    cut = _subsection(proposal, "Release Cut", 3)
    groups = tuple(
        _items(_subsection(cut, heading, 4))
        for heading in ("MVP", "Next", "Deferred")
    )
    if any(len(items) != len(set(items)) for items in groups):
        raise ValidationError("release-cut groups must not contain duplicate Work Packages")
    return tuple(set(items) for items in groups)  # type: ignore[return-value]


def _cycle(packages: dict[str, Package]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in packages[node].dependencies:
            if visit(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in packages)


def _normalize_lines(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(" ".join(x.split()) for x in items)


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


def _validate_package_file(source: Path, project_root: str, package: Package) -> str:
    package_root = source.parent / "work-packages"
    _path_error(lambda: require_canonical_owned_directory(package_root, writable=True))
    path = source.parent / "work-packages" / f"{package.package_id}.md"
    _path_error(lambda: require_canonical_regular_file(path))
    if path.parent != package_root or path.name != f"{package.package_id}.md":
        raise ValidationError(f"invalid Work Package path: {path}")
    text = path.read_text(encoding="utf-8")
    if _metadata(text, "Status") != "ready-for-matt":
        raise ValidationError(f"{path}: Status must be ready-for-matt")
    if _metadata(text, "Project-Root") != project_root:
        raise ValidationError(f"{path}: Project-Root drift")
    if _metadata(text, "Work-Package") != package.package_id:
        raise ValidationError(f"{path}: Work-Package drift")
    work_slug = _metadata(text, "Suggested-Work-Slug")
    try:
        require_work_slug(work_slug)
    except PathContractError as exc:
        raise ValidationError(f"{path}: invalid Suggested-Work-Slug: {exc}") from exc
    source_ref = _metadata(text, "Source-Scope-Result")
    if (path.parent / source_ref).resolve() != source.resolve():
        raise ValidationError(f"{path}: Source-Scope-Result drift")
    outcome = _section(text, "Package Outcome").strip()
    includes = _items(_section(text, "Included Product Scope"))
    excludes = _items(_section(text, "Excluded Sibling Scope"))
    deps = _items(_section(text, "Dependencies"))
    decisions_reserved = _items(_section(text, "Decisions Reserved For Matt"))
    if " ".join(outcome.split()) != " ".join(package.outcome.split()):
        raise ValidationError(f"{path}: Outcome drift")
    if _normalize_lines(includes) != _normalize_lines(package.includes):
        raise ValidationError(f"{path}: Includes drift")
    if _normalize_lines(excludes) != _normalize_lines(package.excludes):
        raise ValidationError(f"{path}: Excludes drift")
    if deps != package.dependencies:
        raise ValidationError(f"{path}: Dependencies drift")
    if _normalize_lines(decisions_reserved) != _normalize_lines(package.decisions_reserved):
        raise ValidationError(f"{path}: Decisions Reserved For Matt drift")
    return work_slug


def _validate_common_sections(text: str) -> None:
    claims = _section(text, "Verified Material Claims")
    if not claims:
        raise ValidationError("Verified Material Claims must not be empty")
    boundary = _section(text, "Planning Boundary")
    outcome = _subsection(boundary, "Outcome", 3)
    if not outcome:
        raise ValidationError("Planning Boundary Outcome must not be empty")
    _items(_subsection(boundary, "Includes", 3))
    _items(_subsection(boundary, "Excludes", 3))
    for heading in (
        "Planning Constraints",
        "Candidate Outcome Areas",
        "Decisions Reserved For Matt",
        "Delivery Context",
    ):
        _items(_section(text, heading))
    if _section(text, "Unresolved Material Questions").strip() != "None":
        raise ValidationError("Unresolved Material Questions must be None")
    _section(text, "Confirmation")
    _metadata(text, "Confirmed By")
    _metadata(text, "Confirmed Scope")


def validate(path: Path) -> None:
    raw_path = path.expanduser()
    _path_error(lambda: require_canonical_regular_file(raw_path))
    path = raw_path
    text = path.read_text(encoding="utf-8")
    if _metadata(text, "Status") != "confirmed":
        raise ValidationError("Status must be confirmed")
    _metadata(text, "Owner")
    work_slug = _metadata(text, "Work-Slug")
    project_root = _metadata(text, "Project-Root")
    _validate_scope_path(path, project_root, work_slug)
    _validate_common_sections(text)
    shape = _metadata(text, "Planning-Shape")
    if shape == "bounded":
        if re.search(r"(?m)^## Work Package Proposal\s*$", text):
            raise ValidationError("bounded result must not contain Work Package Proposal")
        return
    if shape != "initiative":
        raise ValidationError("Planning-Shape must be bounded or initiative")

    packages = _parse_packages(text)
    ids = set(packages)
    for package in packages.values():
        missing = set(package.dependencies) - ids
        if missing:
            raise ValidationError(f"{package.package_id}: missing dependencies {sorted(missing)}")
        if package.package_id in package.dependencies:
            raise ValidationError(f"{package.package_id}: self dependency")
    if _cycle(packages):
        raise ValidationError("dependency cycle detected")

    mvp, next_set, deferred = _release_cut(text)
    if not mvp:
        raise ValidationError("MVP must contain at least one Work Package")
    if (mvp & next_set) or (mvp & deferred) or (next_set & deferred):
        raise ValidationError("release-cut groups overlap")
    if mvp | next_set | deferred != ids:
        raise ValidationError("every Work Package must appear exactly once in MVP, Next, or Deferred")
    for package_id in mvp:
        if not set(packages[package_id].dependencies) <= mvp:
            raise ValidationError(f"MVP is not dependency-closed at {package_id}")

    units = _items(_subsection(_section(text, "Work Package Proposal"), "Next Planning Units", 3))
    if len(units) != len(set(units)):
        raise ValidationError("Next Planning Units must not contain duplicates")
    expected_paths = {f"./work-packages/{pid}.md" for pid in sorted(mvp | next_set)}
    if set(units) != expected_paths:
        raise ValidationError("Next Planning Units must list every non-deferred package exactly once")
    work_slugs: set[str] = set()
    for package_id in sorted(mvp | next_set):
        work_slug = _validate_package_file(path, project_root, packages[package_id])
        if work_slug in work_slugs:
            raise ValidationError(f"duplicate Suggested-Work-Slug: {work_slug}")
        work_slugs.add(work_slug)


def validate_selected_work_package(path: Path) -> Path:
    raw_path = path.expanduser()
    _path_error(lambda: require_canonical_regular_file(raw_path))
    if raw_path.parent.name != "work-packages" or not re.fullmatch(r"WP-\d{3}\.md", raw_path.name):
        raise ValidationError("selected Work Package path must end in work-packages/WP-NNN.md")
    _path_error(lambda: require_canonical_owned_directory(raw_path.parent, writable=True))
    text = raw_path.read_text(encoding="utf-8")
    package_id = _metadata(text, "Work-Package")
    if raw_path.name != f"{package_id}.md":
        raise ValidationError("selected Work Package filename does not match Work-Package metadata")
    source_ref = _metadata(text, "Source-Scope-Result")
    if source_ref != "../SCOPE-SHAPING-RESULT.md":
        raise ValidationError("selected Work Package must reference its sibling Scope result")
    source = raw_path.parent.parent / "SCOPE-SHAPING-RESULT.md"
    validate(source)
    source_text = source.read_text(encoding="utf-8")
    if _metadata(source_text, "Planning-Shape") != "initiative":
        raise ValidationError("selected Work Package source must be an initiative")
    units = _items(
        _subsection(_section(source_text, "Work Package Proposal"), "Next Planning Units", 3)
    )
    if f"./work-packages/{package_id}.md" not in units:
        raise ValidationError("selected Work Package must be a non-deferred Next Planning Unit")
    return source


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
