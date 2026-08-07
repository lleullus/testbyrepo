#!/usr/bin/env python3
"""Validate Project Shaper maps and ready-for-Matt handoff briefs.

Dependency-free by design. This checks the artifact contracts shipped with the
skill; it does not judge product choices or implementation feasibility.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

MAP_META = ["Status", "Owner", "Project-Root", "Initiative-Slug"]
MAP_HEADINGS = [
    "Product Outcome",
    "Product Boundary",
    "Reference Interpretation",
    "MVP Cut",
    "Work Packages",
    "Dependency Map",
    "Deferred Capabilities",
    "Initiative-Level Open Questions",
    "Matt Handoff Queue",
]
PACKAGE_META = ["Package-Status", "Matt-Brief"]
PACKAGE_HEADINGS = [
    "Outcome",
    "Includes",
    "Excludes",
    "Depends On",
    "Why This Is One Package",
    "Why It Is Separate",
    "Decisions Reserved For Matt",
]
BRIEF_META = [
    "Status",
    "Parent-Project-Map",
    "Work-Package",
    "Project-Root",
    "Suggested-Work-Slug",
]
BRIEF_HEADINGS = [
    "Authority Notice",
    "Product Context",
    "Package Outcome",
    "Included Product Scope",
    "Excluded Sibling Scope",
    "Dependencies",
    "Adopted Initiative Decisions",
    "Decisions Reserved For Matt",
    "Reference Material",
    "Matt Start",
]
PACKAGE_STATUSES = {"proposed", "ready-for-matt", "blocked-shaping", "deferred"}
WP_RE = re.compile(r"WP-\d{3}")
SLUG_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str
    line: int | None = None


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, code: str, message: str, path: Path, line: int | None = None) -> None:
        self.findings.append(Finding("error", code, message, str(path), line))

    def warning(self, code: str, message: str, path: Path, line: int | None = None) -> None:
        self.findings.append(Finding("warning", code, message, str(path), line))

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.level == "warning"]


@dataclass
class Package:
    wp_id: str
    title: str
    status: str
    brief: str
    sections: dict[str, str]
    line: int

    @property
    def dependencies(self) -> list[str]:
        return package_dependency_ids(self.sections.get("Depends On", ""))


def read(path: Path, report: Report) -> str | None:
    try:
        if not path.is_file():
            report.error("file.missing", "Expected a readable regular file.", path)
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.error("file.read", f"Cannot read UTF-8 Markdown: {exc}", path)
        return None


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def title(text: str) -> str:
    for raw in text.splitlines():
        if raw.strip():
            return raw.strip()
    return ""


def metadata(text: str, stop_level: int = 2) -> tuple[dict[str, str], dict[str, int]]:
    stop = re.search(rf"^{'#' * stop_level} ", text, re.M)
    prefix = text[: stop.start()] if stop else text
    result: dict[str, str] = {}
    lines: dict[str, int] = {}
    for match in re.finditer(r"^([A-Za-z][A-Za-z0-9-]*):\s*(.*?)\s*$", prefix, re.M):
        key, value = match.groups()
        if key not in result:
            result[key] = value
            lines[key] = line_of(text, match.start())
    return result, lines


def duplicate_metadata_keys(text: str, stop_level: int = 2) -> list[str]:
    stop = re.search(rf"^{'#' * stop_level} ", text, re.M)
    prefix = text[: stop.start()] if stop else text
    keys = re.findall(r"^([A-Za-z][A-Za-z0-9-]*):\s*.*$", prefix, re.M)
    return sorted({key for key in keys if keys.count(key) > 1})


def heading_names(text: str, level: int) -> list[str]:
    return re.findall(rf"^{'#' * level} (.+?)\s*$", text, re.M)


def section(text: str, heading: str, level: int = 2) -> str | None:
    marks = "#" * level
    match = re.search(
        rf"^{marks} {re.escape(heading)}\s*\n(.*?)(?=^{marks} |\Z)",
        text,
        re.M | re.S,
    )
    return match.group(1).strip() if match else None


def bullets(body: str) -> list[str]:
    return [line.strip()[2:].strip() for line in body.splitlines() if line.strip().startswith("- ")]


def nonempty(body: str) -> bool:
    return any(raw.strip() and not raw.strip().startswith("```") for raw in body.splitlines())


def package_dependency_ids(body: str) -> list[str]:
    if body.strip() == "None":
        return []
    result: list[str] = []
    for line in body.splitlines():
        match = re.fullmatch(r"- (WP-\d{3})", line.strip())
        if match:
            result.append(match.group(1))
    return result


def brief_dependency_ids(body: str) -> list[str]:
    if body.strip() == "None":
        return []
    result: list[str] = []
    for line in body.splitlines():
        match = re.fullmatch(r"- (WP-\d{3}) — \S.*", line.strip())
        if match:
            result.append(match.group(1))
    return result


def valid_package_dependencies(body: str) -> bool:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return lines == ["None"] or bool(lines) and all(
        re.fullmatch(r"- WP-\d{3}", line) for line in lines
    )


def valid_brief_dependencies(body: str) -> bool:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return lines == ["None"] or bool(lines) and all(
        re.fullmatch(r"- WP-\d{3} — \S.*", line) for line in lines
    )


def expected_dependency_map(packages: Sequence[Package]) -> str:
    lines: list[str] = []
    for package in packages:
        dependencies = ", ".join(package.dependencies) if package.dependencies else "None"
        lines.append(f"- {package.wp_id}: {dependencies}")
    return "\n".join(lines)


def require_keys(
    actual: dict[str, str], expected: Sequence[str], report: Report, path: Path, context: str
) -> None:
    missing = [key for key in expected if key not in actual]
    extra = [key for key in actual if key not in expected]
    if missing:
        report.error(f"{context}.metadata.missing", "Missing: " + ", ".join(missing), path)
    if extra:
        report.error(f"{context}.metadata.extra", "Unexpected: " + ", ".join(extra), path)
    for key in expected:
        if key in actual and not actual[key]:
            report.error(f"{context}.metadata.empty", f"Empty value: {key}", path)


def require_headings(
    actual: Sequence[str], expected: Sequence[str], report: Report, path: Path, context: str
) -> None:
    if list(actual) == list(expected):
        return
    missing = [name for name in expected if name not in actual]
    extra = [name for name in actual if name not in expected]
    detail: list[str] = []
    if missing:
        detail.append("missing " + ", ".join(missing))
    if extra:
        detail.append("unexpected " + ", ".join(extra))
    if not detail:
        detail.append("wrong order")
    report.error(f"{context}.headings", "; ".join(detail), path)


def parse_packages(map_text: str, map_path: Path, report: Report) -> list[Package]:
    body = section(map_text, "Work Packages")
    if body is None:
        return []
    starts = list(re.finditer(r"^### (WP-\d{3}):\s*(.+?)\s*$", body, re.M))
    malformed = [
        match.group(0)
        for match in re.finditer(r"^### .+$", body, re.M)
        if not re.fullmatch(r"### WP-\d{3}:\s*.+", match.group(0))
    ]
    if malformed:
        report.error("package.heading", "Malformed package heading: " + malformed[0], map_path)
    packages: list[Package] = []
    seen: set[str] = set()
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        block = body[start.end() : end].strip()
        wp_id, package_title = start.groups()
        block_meta, _ = metadata(block, stop_level=4)
        require_keys(block_meta, PACKAGE_META, report, map_path, wp_id)
        duplicate_keys = duplicate_metadata_keys(block, stop_level=4)
        if duplicate_keys:
            report.error(
                "package.metadata.duplicate",
                f"{wp_id}: " + ", ".join(duplicate_keys),
                map_path,
            )
        names = heading_names(block, 4)
        require_headings(names, PACKAGE_HEADINGS, report, map_path, wp_id)
        sections = {name: section(block, name, 4) or "" for name in PACKAGE_HEADINGS}
        for name, value in sections.items():
            if not nonempty(value):
                report.error("package.section.empty", f"{wp_id}: {name}", map_path)
        if wp_id in seen:
            report.error("package.id.duplicate", wp_id, map_path)
        seen.add(wp_id)
        packages.append(
            Package(
                wp_id=wp_id,
                title=package_title,
                status=block_meta.get("Package-Status", ""),
                brief=block_meta.get("Matt-Brief", ""),
                sections=sections,
                line=line_of(map_text, map_text.find(start.group(0))),
            )
        )
    if not packages:
        report.error("package.none", "At least one Work Package is required.", map_path)
    return packages


def cycle(packages: dict[str, Package]) -> list[str] | None:
    state = {wp_id: 0 for wp_id in packages}
    stack: list[str] = []

    def visit(wp_id: str) -> list[str] | None:
        state[wp_id] = 1
        stack.append(wp_id)
        for dep in packages[wp_id].dependencies:
            if dep not in packages:
                continue
            if state[dep] == 0:
                found = visit(dep)
                if found:
                    return found
            elif state[dep] == 1:
                pos = stack.index(dep)
                return stack[pos:] + [dep]
        stack.pop()
        state[wp_id] = 2
        return None

    for wp_id in packages:
        if state[wp_id] == 0:
            found = visit(wp_id)
            if found:
                return found
    return None


def resolve_inside(base: Path, relative: str, report: Report, path: Path, code: str) -> Path | None:
    value = Path(relative)
    if value.is_absolute():
        report.error(code, "Expected a relative artifact path.", path)
        return None
    resolved = (base / value).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        report.error(code, "Artifact path escapes the initiative directory.", path)
        return None
    return resolved


def validate_brief(
    brief_path: Path,
    map_path: Path,
    map_meta: dict[str, str],
    package: Package,
    used_slugs: dict[str, Path],
    report: Report,
) -> None:
    text = read(brief_path, report)
    if text is None:
        return
    meta, meta_lines = metadata(text)
    require_keys(meta, BRIEF_META, report, brief_path, "brief")
    duplicate_keys = duplicate_metadata_keys(text)
    if duplicate_keys:
        report.error("brief.metadata.duplicate", ", ".join(duplicate_keys), brief_path)
    require_headings(heading_names(text, 2), BRIEF_HEADINGS, report, brief_path, "brief")
    if title(text) != f"# {package.wp_id}: {package.title}":
        report.error("brief.title", "Title must exactly match the parent package.", brief_path, 1)
    checks = {
        "Status": "ready-for-matt",
        "Work-Package": package.wp_id,
        "Project-Root": map_meta.get("Project-Root", ""),
    }
    for key, expected in checks.items():
        if meta.get(key) != expected:
            report.error("brief.metadata.mismatch", f"{key} must be `{expected}`.", brief_path, meta_lines.get(key))
    parent_value = Path(meta.get("Parent-Project-Map", ""))
    if parent_value.is_absolute():
        report.error("brief.parent.path", "Parent-Project-Map must be relative to the brief.", brief_path)
    else:
        parent = (brief_path.parent / parent_value).resolve()
        if parent != map_path.resolve():
            report.error("brief.parent.mismatch", "Parent-Project-Map does not resolve to this map.", brief_path)
    slug = meta.get("Suggested-Work-Slug", "")
    if slug and not SLUG_RE.fullmatch(slug):
        report.error("brief.slug", "Suggested-Work-Slug must be lowercase kebab-case.", brief_path, meta_lines.get("Suggested-Work-Slug"))
    if slug in used_slugs:
        report.error("brief.slug.duplicate", f"Also used by {used_slugs[slug]}", brief_path)
    elif slug:
        used_slugs[slug] = brief_path

    projections = {
        "Package Outcome": "Outcome",
        "Included Product Scope": "Includes",
        "Excluded Sibling Scope": "Excludes",
        "Decisions Reserved For Matt": "Decisions Reserved For Matt",
    }
    for brief_heading, map_heading in projections.items():
        brief_body = section(text, brief_heading) or ""
        if brief_body.strip() != package.sections[map_heading].strip():
            report.error(
                "brief.projection.drift",
                f"{brief_heading} must exactly project `{map_heading}` from {package.wp_id}.",
                brief_path,
            )
    brief_dependencies = section(text, "Dependencies") or ""
    if not valid_brief_dependencies(brief_dependencies):
        report.error(
            "brief.dependencies.format",
            "Dependencies must be `None` or `- WP-NNN — <user-visible reason>` items.",
            brief_path,
        )
    brief_deps = brief_dependency_ids(brief_dependencies)
    if brief_deps != package.dependencies:
        report.error("brief.dependencies.drift", "Dependency IDs or order differ from the parent package.", brief_path)
    for name in BRIEF_HEADINGS:
        value = section(text, name) or ""
        if not nonempty(value):
            report.error("brief.section.empty", name, brief_path)

    authority = (section(text, "Authority Notice") or "").lower()
    required_authority = [
        (r"승인된.*(?:프로젝트|이니셔티브).*(?:분해|투영)|approved initiative", "approved decomposition"),
        (r"승인된.*spec.*아니|not an approved.*spec", "not an approved Spec"),
        (r"사용자.*확인|user-confirmed", "user confirmation"),
        (r"to-spec", "to-spec gate"),
    ]
    for pattern, meaning in required_authority:
        if not re.search(pattern, authority, re.S):
            report.error("brief.authority", f"Missing authority meaning: {meaning}.", brief_path)
    start = (section(text, "Matt Start") or "").lower()
    for pattern, meaning in [
        (r"(?:이|현재) work package(?:만|만을)|only this work package", "only this package"),
        (r"확인|수정|confirm", "frame confirmation"),
        (r"ask-matt", "normal ask-matt continuation"),
    ]:
        if not re.search(pattern, start, re.S):
            report.error("brief.start", f"Missing Matt Start instruction: {meaning}.", brief_path)


def validate(project_map: Path) -> Report:
    report = Report()
    map_path = project_map.expanduser().resolve()
    text = read(map_path, report)
    if text is None:
        return report
    if not title(text).startswith("# ") or title(text).startswith("## "):
        report.error("map.title", "Map must start with one level-1 title.", map_path, 1)
    meta, meta_lines = metadata(text)
    require_keys(meta, MAP_META, report, map_path, "map")
    duplicate_keys = duplicate_metadata_keys(text)
    if duplicate_keys:
        report.error("map.metadata.duplicate", ", ".join(duplicate_keys), map_path)
    require_headings(heading_names(text, 2), MAP_HEADINGS, report, map_path, "map")
    if meta.get("Status") not in {"draft", "approved"}:
        report.error("map.status", "Status must be `draft` or `approved`.", map_path, meta_lines.get("Status"))
    root_value = meta.get("Project-Root", "")
    if root_value and not Path(root_value).is_absolute():
        report.error("map.project_root", "Project-Root must be absolute.", map_path, meta_lines.get("Project-Root"))
    elif root_value:
        project_root = Path(root_value).expanduser()
        try:
            canonical_root = project_root.resolve(strict=True)
        except OSError:
            report.error("map.project_root", "Project-Root must be an existing canonical directory.", map_path)
        else:
            if canonical_root != project_root or not canonical_root.is_dir():
                report.error("map.project_root", "Project-Root must be an existing canonical directory.", map_path)
            expected_parent = canonical_root / "docs" / "planning" / "initiatives" / meta.get("Initiative-Slug", "")
            if map_path.parent != expected_parent:
                report.error(
                    "map.location",
                    "PROJECT-MAP.md must be in <Project-Root>/docs/planning/initiatives/<Initiative-Slug>/.",
                    map_path,
                )
    slug = meta.get("Initiative-Slug", "")
    if slug and not SLUG_RE.fullmatch(slug):
        report.error("map.slug", "Initiative-Slug must be lowercase kebab-case.", map_path, meta_lines.get("Initiative-Slug"))
    if slug and map_path.parent.name != slug:
        report.warning("map.slug.path", "Initiative-Slug differs from the artifact directory name.", map_path)
    for name in MAP_HEADINGS:
        value = section(text, name)
        if value is None or not nonempty(value):
            report.error("map.section.empty", name, map_path)

    packages_list = parse_packages(text, map_path, report)
    packages = {item.wp_id: item for item in packages_list}
    numbers = [int(item.wp_id.split("-")[1]) for item in packages_list]
    if numbers != sorted(numbers):
        report.error("package.order", "Packages must appear in ascending WP-NNN order.", map_path)
    for package in packages_list:
        if package.status not in PACKAGE_STATUSES:
            report.error("package.status", f"{package.wp_id}: {package.status}", map_path, package.line)
        if meta.get("Status") == "approved" and package.status not in {"ready-for-matt", "deferred"}:
            report.error(
                "package.status.approved",
                f"{package.wp_id}: approved maps allow only ready-for-matt or deferred packages.",
                map_path,
                package.line,
            )
        if meta.get("Status") == "draft" and package.status == "ready-for-matt":
            report.error(
                "package.status.draft",
                f"{package.wp_id}: ready-for-matt requires an approved map.",
                map_path,
                package.line,
            )
        expected_brief = f"./matt-briefs/{package.wp_id}.md"
        if package.status == "ready-for-matt" and package.brief != expected_brief:
            report.error("package.brief", f"{package.wp_id} must point to {expected_brief}.", map_path, package.line)
        if package.status != "ready-for-matt" and package.brief != "None":
            report.error("package.brief.nonready", f"{package.wp_id} Matt-Brief must be None.", map_path, package.line)
        raw_deps = package.sections.get("Depends On", "")
        if not valid_package_dependencies(raw_deps):
            report.error(
                "package.dependencies.format",
                f"{package.wp_id} dependencies must be exact `- WP-NNN` items or `None`.",
                map_path,
            )
        if len(package.dependencies) != len(set(package.dependencies)):
            report.error("package.dependencies.duplicate", package.wp_id, map_path)
        for dep in package.dependencies:
            if dep == package.wp_id:
                report.error("package.dependencies.self", package.wp_id, map_path)
            elif dep not in packages:
                report.error("package.dependencies.unknown", f"{package.wp_id} -> {dep}", map_path)
    found_cycle = cycle(packages)
    if found_cycle:
        report.error("package.dependencies.cycle", " -> ".join(found_cycle), map_path)

    dependency_map = section(text, "Dependency Map") or ""
    expected_map = expected_dependency_map(packages_list)
    if dependency_map.strip() != expected_map:
        report.error(
            "map.dependencies.projection",
            "Dependency Map must exactly project every package's canonical Depends On list.",
            map_path,
        )

    mvp_body = section(text, "MVP Cut") or ""
    mvp = [item for item in bullets(mvp_body) if WP_RE.fullmatch(item)]
    if len(mvp) != len(bullets(mvp_body)) or not mvp:
        report.error("map.mvp.format", "MVP Cut must begin with one or more `- WP-NNN` items only.", map_path)
    if len(mvp) != len(set(mvp)):
        report.error("map.mvp.duplicate", "MVP Cut contains duplicate package IDs.", map_path)
    mvp_set = set(mvp)
    for wp_id in mvp:
        if wp_id not in packages:
            report.error("map.mvp.unknown", wp_id, map_path)
        elif meta.get("Status") == "approved" and packages[wp_id].status in {"deferred", "blocked-shaping"}:
            report.error("map.mvp.unavailable", f"{wp_id}: {packages[wp_id].status}", map_path)
        if wp_id in packages:
            for dependency in packages[wp_id].dependencies:
                if dependency not in mvp_set:
                    report.error(
                        "map.mvp.dependency",
                        f"{wp_id} requires {dependency}, which is missing from the MVP Cut.",
                        map_path,
                    )

    if meta.get("Status") == "approved" and (section(text, "Initiative-Level Open Questions") or "").strip() != "None":
        report.error("map.open_questions", "Approved maps require exact `None`.", map_path)

    queue_body = section(text, "Matt Handoff Queue") or ""
    queue = bullets(queue_body)
    if len(queue) != len(set(queue)):
        report.error("map.queue.duplicate", "Handoff queue paths must be unique.", map_path)
    ready = [item for item in packages_list if item.status == "ready-for-matt"]
    expected_queue = {item.brief for item in ready}
    if meta.get("Status") == "approved":
        nonempty_lines = [line.strip() for line in queue_body.splitlines() if line.strip()]
        if any(not line.startswith("- ") for line in nonempty_lines):
            report.error("map.queue.format", "Approved queue must contain path-only bullets.", map_path)
        if set(queue) != expected_queue:
            report.error("map.queue.mismatch", "Queue must contain every and only ready-for-matt brief.", map_path)
    queue_ids: list[str] = []
    for item in queue:
        match = re.fullmatch(r"\./matt-briefs/(WP-\d{3})\.md", item)
        if not match:
            report.error("map.queue.path", item, map_path)
        else:
            queue_ids.append(match.group(1))
    positions = {wp_id: index for index, wp_id in enumerate(queue_ids)}
    for wp_id in queue_ids:
        package = packages.get(wp_id)
        if not package:
            continue
        for dep in package.dependencies:
            if dep in positions and positions[dep] > positions[wp_id]:
                report.error("map.queue.order", f"{wp_id} appears before dependency {dep}.", map_path)

    used_slugs: dict[str, Path] = {}
    expected_files: set[Path] = set()
    if meta.get("Status") == "approved":
        for package in ready:
            brief_path = resolve_inside(map_path.parent, package.brief, report, map_path, "package.brief.path")
            if brief_path:
                expected_files.add(brief_path)
                validate_brief(brief_path, map_path, meta, package, used_slugs, report)
        brief_dir = map_path.parent / "matt-briefs"
        if brief_dir.is_dir():
            for candidate in brief_dir.glob("*.md"):
                if candidate.resolve() not in expected_files:
                    report.warning("brief.stale", "Unreferenced Matt brief.", candidate.resolve())
    return report


def emit(report: Report, project_map: Path, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "project_map": str(project_map.expanduser().resolve()),
                    "valid": not report.errors,
                    "error_count": len(report.errors),
                    "warning_count": len(report.warnings),
                    "findings": [asdict(item) for item in report.findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    for finding in report.findings:
        location = finding.path + (f":{finding.line}" if finding.line else "")
        print(f"{finding.level.upper():7} {finding.code:31} {location} — {finding.message}")
    if report.errors:
        print(f"INVALID: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    else:
        print(f"VALID: 0 errors, {len(report.warnings)} warning(s)")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Project Shaper artifacts.")
    parser.add_argument("project_map", type=Path, help="Exact PROJECT-MAP.md path")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict-warnings", action="store_true", help="Warnings return exit code 2")
    args = parser.parse_args(argv)
    report = validate(args.project_map)
    emit(report, args.project_map, args.json)
    if report.errors:
        return 1
    if args.strict_warnings and report.warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
