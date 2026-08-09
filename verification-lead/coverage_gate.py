#!/usr/bin/env python3
"""Build and validate the Verification Lead pre-approval coverage gate.

The gate is deliberately structural. Semantic completeness remains the bounded
responsibility of an independent Coverage Challenger whose non-vacuous JSON
attestation is validated here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


SCHEMA = "verification-coverage-gate/v1"
ATTESTATION_SCHEMA = "coverage-challenge/v1"
RECEIPT_SCHEMA = "coverage-challenge-receipt/v1"
APPROVAL_SCHEMA = "coverage-gate-approval/v1"
ROOT_HEADINGS = (("AC", "Acceptance Criteria"), ("V", "Verification"))
SPEC_QUALIFIER_SECTIONS = (
    "Desired Outcome",
    "Requirements",
    "Non-Goals",
    "Implementation Constraints",
    "Verification Expectations",
    "Behavior Authorities",
    "UI / UX",
    "Open Questions",
)
DISPOSITIONS = {"PLANNED", "NOT_READY", "UNSAFE", "UNSUPPORTED"}
SCENARIO_READINESS = {"READY", "PREPARABLE"}
DEFECT_CLASSES = {
    "MISSING_UNIT",
    "MISSING_QUALIFIER",
    "MISBOUND_EDGE",
    "ILLEGAL_COLLAPSE",
}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@-]*$")


class GateError(RuntimeError):
    pass


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Any, length: int | None = None) -> str:
    result = hashlib.sha256(_json_bytes(value)).hexdigest()
    return result[:length] if length else result


def _normalize_inline_prose(value: str) -> str:
    result: list[str] = []
    prose: list[str] = []

    def flush_prose() -> None:
        if prose:
            result.append(re.sub(r"\s+", " ", "".join(prose)))
            prose.clear()

    index = 0
    while index < len(value):
        if value[index] != "`":
            prose.append(value[index])
            index += 1
            continue
        end_of_ticks = index
        while end_of_ticks < len(value) and value[end_of_ticks] == "`":
            end_of_ticks += 1
        ticks = value[index:end_of_ticks]
        closing = value.find(ticks, end_of_ticks)
        if closing < 0:
            prose.append(ticks)
            index = end_of_ticks
            continue
        flush_prose()
        result.append(value[index : closing + len(ticks)])
        index = closing + len(ticks)
    flush_prose()
    return "".join(result).strip()


def _normalize_markdown(value: str) -> str:
    text = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    chunks: list[str] = []
    prose_lines: list[str] = []
    fenced_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    def flush_prose() -> None:
        if prose_lines:
            normalized = _normalize_inline_prose("\n".join(prose_lines))
            if normalized:
                chunks.append(normalized)
            prose_lines.clear()

    for line in text.split("\n"):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence_character is None:
            if marker is None:
                prose_lines.append(line)
                continue
            flush_prose()
            token = marker.group(1)
            fence_character = token[0]
            fence_length = len(token)
            fenced_lines = [line]
            continue
        fenced_lines.append(line)
        closing = re.match(
            rf"^\s*{re.escape(fence_character)}{{{fence_length},}}\s*$", line
        )
        if closing:
            chunks.append("\n".join(fenced_lines))
            fenced_lines = []
            fence_character = None
            fence_length = 0
    flush_prose()
    if fenced_lines:
        chunks.append("\n".join(fenced_lines))
    return "\n".join(chunks).strip()


def _expect_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GateError(f"{label} must be an object")
    return value


def _expect_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GateError(f"{label} must be an array")
    return value


def _expect_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty string")
    return value.strip()


def _expect_string_list(
    value: Any, label: str, *, allow_empty: bool = False
) -> list[str]:
    items = _expect_list(value, label)
    if not allow_empty and not items:
        raise GateError(f"{label} must not be empty")
    result = [_expect_string(item, f"{label} item") for item in items]
    if len(result) != len(set(result)):
        raise GateError(f"{label} must not contain duplicates")
    return result


def _expect_keys(
    value: dict[str, Any], label: str, required: set[str], optional: set[str] = set()
) -> None:
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing:
        raise GateError(f"{label} is missing fields: {sorted(missing)}")
    if extra:
        raise GateError(f"{label} has unsupported fields: {sorted(extra)}")


def _require_id(value: Any, label: str) -> str:
    result = _expect_string(value, label)
    if not ID_PATTERN.fullmatch(result):
        raise GateError(f"{label} has an invalid stable ID: {result}")
    return result


def _require_file(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise GateError(f"{label} must be an absolute path")
    try:
        details = path.lstat()
    except OSError as exc:
        raise GateError(f"cannot inspect {label} {path}: {exc}") from exc
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
        raise GateError(f"{label} must be a non-symlink regular file: {path}")
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise GateError(f"{label} must be canonical: {path}")
    return path


def _read_json(path: Path, label: str) -> dict[str, Any]:
    _require_file(path, label)
    try:
        return _expect_dict(json.loads(path.read_text(encoding="utf-8")), label)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read {label} {path}: {exc}") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _write_json(
    path: Path | None, value: Any, project_root: Path | None = None
) -> None:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path is None:
        print(rendered, end="")
        return
    if not path.is_absolute():
        raise GateError("output path must be absolute")
    parent = path.parent.resolve(strict=True)
    canonical_output = parent / path.name
    if project_root is not None and (
        _is_within(canonical_output, project_root) or canonical_output == project_root
    ):
        raise GateError("coverage-gate output must remain outside the Project Root")
    if path.exists() and path.is_symlink():
        raise GateError(f"output path must not be a symlink: {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _metadata(text: str, key: str) -> str:
    matches = re.findall(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if len(matches) != 1:
        raise GateError(f"expected exactly one {key} metadata line")
    return matches[0].strip()


def _top_metadata(text: str, key: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or not lines[0].startswith("# "):
        raise GateError("authority must start with one Markdown title")
    metadata: list[str] = []
    started = False
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z /_-]*:\s*.+", stripped):
            started = True
            metadata.append(stripped)
            continue
        break
    matches = [
        match.group(1).strip()
        for line in metadata
        if (match := re.fullmatch(rf"{re.escape(key)}:\s*(.+)", line))
    ]
    if len(matches) != 1:
        raise GateError(f"expected exactly one top-metadata {key} entry")
    return matches[0]


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}\s*$", text))
    if len(matches) != 1:
        raise GateError(f"expected exactly one section: {marker}")
    start = matches[0].end()
    next_heading = re.search(r"(?m)^#{1,2}\s+", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _top_level_items(block: str, label: str) -> list[str]:
    items: list[list[str]] = []
    for raw_line in block.splitlines():
        line = raw_line
        if not line.strip():
            if items:
                items[-1].append(line)
            continue
        match = re.match(r"^-\s+(.+)$", line)
        if match:
            items.append([match.group(1)])
            continue
        if not items:
            raise GateError(
                f"{label} must contain only top-level '-' Markdown list items"
            )
        if re.match(r"^(?:\*|\+|\d+[.)])\s+", line):
            raise GateError(f"{label} contains an unsupported top-level list marker")
        items[-1].append(line)
    if not items:
        raise GateError(f"{label} must contain at least one top-level '-' item")
    return [_normalize_markdown("\n".join(parts)) for parts in items]


def _canonical_file(raw: str, *, base: Path, project_root: Path, label: str) -> Path:
    token = raw.strip().strip("`")
    candidate = Path(token)
    if not candidate.is_absolute():
        candidate = (
            project_root / candidate if token.startswith("docs/") else base / candidate
        )
    candidate = candidate.resolve(strict=True)
    _require_file(candidate, label)
    if not _is_within(candidate, project_root):
        raise GateError(f"{label} must be inside the Project Root: {candidate}")
    return candidate


def _declared_path(value: str, *, base: Path, project_root: Path, label: str) -> Path:
    candidates = [part.strip() for part in value.split("|") if part.strip()]
    if not candidates:
        raise GateError(f"{label} has no path")
    resolved = [
        _canonical_file(part, base=base, project_root=project_root, label=label)
        for part in candidates
    ]
    if any(path != resolved[0] for path in resolved[1:]):
        raise GateError(f"{label} path declarations do not resolve to one file")
    return resolved[0]


def _list_path(item: str) -> str:
    return item.split("|", 1)[0].strip().strip("`")


def _single_external_authority_path(section: str) -> str | None:
    try:
        items = _top_level_items(section, "Spec UI / UX")
    except GateError:
        return None
    if len(items) != 1:
        return None
    authored = items[0].strip()
    path_part, separator, suffix = authored.partition("|")
    if separator and not suffix.strip().startswith("Scope:"):
        return None
    path_text = path_part.strip().strip("`")
    if not re.fullmatch(r"(?:\.{1,2}/|/|docs/)[^\s]+\.md", path_text):
        return None
    return path_text


def _source_id(kind: str, relative_path: str, content: str) -> str:
    return f"Q:{kind}:{_digest([relative_path, content], 12)}"


def _selected_source(
    kind: str, path: Path, project_root: Path, content: str
) -> dict[str, str]:
    relative = path.relative_to(project_root).as_posix()
    normalized = _normalize_markdown(content)
    return {
        "id": _source_id(kind, relative, normalized),
        "kind": kind,
        "path": relative,
        "content": normalized,
    }


def _canonical_package(ticket_path: Path) -> dict[str, Any]:
    ticket_path = _require_file(ticket_path, "Ticket")
    ticket_text = ticket_path.read_text(encoding="utf-8")
    if _metadata(ticket_text, "Status") != "ready":
        raise GateError("Ticket Status must be ready")
    project_root = Path(_metadata(ticket_text, "Project-Root"))
    if (
        not project_root.is_absolute()
        or project_root.resolve(strict=True) != project_root
    ):
        raise GateError("Project-Root must be an absolute canonical directory")
    expected_planning = project_root / "docs" / "planning"
    if not _is_within(ticket_path, expected_planning):
        raise GateError("Ticket must be under the Project Root's docs/planning tree")

    roots: list[dict[str, Any]] = []
    for kind, heading in ROOT_HEADINGS:
        for ordinal, text in enumerate(
            _top_level_items(_section(ticket_text, heading), heading), start=1
        ):
            roots.append(
                {
                    "id": f"{kind}:{ordinal:02d}:{_digest(text, 12)}",
                    "kind": kind,
                    "ordinal": ordinal,
                    "text": text,
                }
            )

    spec_path = _declared_path(
        _metadata(ticket_text, "Parent-Spec"),
        base=ticket_path.parent,
        project_root=project_root,
        label="Parent-Spec",
    )
    spec_text = spec_path.read_text(encoding="utf-8")
    if _metadata(spec_text, "Status") != "approved":
        raise GateError("Parent Spec Status must be approved")
    spec_content = "\n".join(
        f"## {heading}\n{_section(spec_text, heading)}"
        for heading in SPEC_QUALIFIER_SECTIONS
    )

    binding_content = "\n".join(
        (
            f"Status: {_metadata(ticket_text, 'Status')}",
            f"Parent-Spec: {spec_path.relative_to(project_root).as_posix()}",
            f"Project-Root: {project_root}",
            f"UI: {_metadata(ticket_text, 'UI')}",
            f"Behavior Authorities:\n{_section(ticket_text, 'Behavior Authorities')}",
        )
    )
    sources = [
        _selected_source("ticket_binding", ticket_path, project_root, binding_content),
        _selected_source("parent_spec", spec_path, project_root, spec_content),
    ]

    ticket_behavior_items = _top_level_items(
        _section(ticket_text, "Behavior Authorities"), "Behavior Authorities"
    )
    spec_behavior_items = _top_level_items(
        _section(spec_text, "Behavior Authorities"), "Spec Behavior Authorities"
    )
    ticket_behaviors = {
        _canonical_file(
            _list_path(item),
            base=ticket_path.parent,
            project_root=project_root,
            label="Behavior authority",
        )
        for item in ticket_behavior_items
    }
    spec_behaviors = {
        _canonical_file(
            _list_path(item),
            base=spec_path.parent,
            project_root=project_root,
            label="Spec Behavior authority",
        )
        for item in spec_behavior_items
    }
    if not ticket_behaviors or not ticket_behaviors <= spec_behaviors:
        raise GateError(
            "Ticket Behavior authorities must be adopted by the parent Spec"
        )
    for path in sorted(ticket_behaviors):
        allowed_parents = {
            project_root / "docs" / "planning" / "behavior" / category
            for category in ("contexts", "lifecycles", "invariants")
        }
        if path.parent not in allowed_parents:
            raise GateError(
                f"Behavior authority is outside a canonical authority directory: {path}"
            )
        content = path.read_text(encoding="utf-8")
        if _metadata(content, "Status") != "approved":
            raise GateError(f"Behavior authority must be approved: {path}")
        sources.append(_selected_source("behavior", path, project_root, content))

    ui_value = _metadata(ticket_text, "UI")
    if ui_value not in {"yes", "no"}:
        raise GateError("Ticket UI must be exactly yes or no")
    spec_ui = _section(spec_text, "UI / UX")
    ui_path: Path | None = None
    if ui_value == "yes":
        external_authority = _single_external_authority_path(spec_ui)
        if external_authority is not None:
            ui_path = _canonical_file(
                external_authority,
                base=spec_path.parent,
                project_root=project_root,
                label="UI authority",
            )
        else:
            ui_path = spec_path
        reference_paths: set[Path] = set()
        for item in _top_level_items(_section(ticket_text, "References"), "References"):
            if item != _list_path(item) or "`" in item:
                continue
            try:
                reference_paths.add(
                    _canonical_file(
                        _list_path(item),
                        base=ticket_path.parent,
                        project_root=project_root,
                        label="Reference",
                    )
                )
            except (GateError, OSError):
                continue
        if ui_path not in reference_paths:
            raise GateError(
                "Ticket References must contain the Spec-selected UI authority"
            )
        if ui_path != spec_path:
            ui_content = ui_path.read_text(encoding="utf-8")
            if _top_metadata(ui_content, "Status") != "approved":
                raise GateError("UI authority must be approved")
            _top_metadata(ui_content, "Owner")
            _top_metadata(ui_content, "Scope")
            if ui_path.name == "DESIGN.md":
                open_question_lines = [
                    line.strip()
                    for line in _section(ui_content, "Open Questions").splitlines()
                    if line.strip()
                ]
                if (
                    not open_question_lines
                    or open_question_lines[0] != "None"
                    or any(
                        not (
                            re.fullmatch(r"Approved (?:By|On):\s*.+", line)
                            or re.fullmatch(
                                r"Final approval render:\s*(?:reviewed|declined|not applicable\s*[—-]\s*unchanged approved authority adopted)",
                                line,
                                re.IGNORECASE,
                            )
                        )
                        for line in open_question_lines[1:]
                    )
                ):
                    raise GateError(
                        "DESIGN.md UI authority must have Open Questions: None"
                    )
            sources.append(_selected_source("ui", ui_path, project_root, ui_content))
    elif spec_ui.strip() != "Not applicable":
        raise GateError("UI: no requires exact parent-Spec UI / UX: Not applicable")

    package = {
        "ticket": ticket_path.relative_to(project_root).as_posix(),
        "project_root": str(project_root),
        "parent_spec": spec_path.relative_to(project_root).as_posix(),
        "ui_authority": ui_path.relative_to(project_root).as_posix()
        if ui_path
        else None,
        "roots": roots,
        "qualifier_sources": sorted(sources, key=lambda item: item["id"]),
    }
    package["raw_fingerprint"] = _digest(package)
    return package


def _resolve_root_ref(raw: str, roots: list[dict[str, Any]]) -> str:
    matches = [
        root["id"]
        for root in roots
        if root["id"] == raw or root["id"].startswith(raw + ":")
    ]
    if len(matches) != 1:
        raise GateError(f"root reference must resolve exactly once: {raw}")
    return matches[0]


def _normalize_model(
    model: dict[str, Any], canonical: dict[str, Any]
) -> dict[str, Any]:
    _expect_keys(
        model,
        "model",
        {"units", "qualifier_bindings", "coverage_edges", "scenarios", "partial"},
        {"schema"},
    )
    roots = canonical["roots"]
    root_ids = {root["id"] for root in roots}
    ac_root_ids = {root["id"] for root in roots if root["kind"] == "AC"}
    source_by_id = {source["id"]: source for source in canonical["qualifier_sources"]}
    source_by_path = {
        source["path"]: source for source in canonical["qualifier_sources"]
    }

    raw_units = _expect_list(model["units"], "units")
    units: list[dict[str, Any]] = []
    unit_ids: set[str] = set()
    for index, raw in enumerate(raw_units):
        item = _expect_dict(raw, f"units[{index}]")
        _expect_keys(
            item,
            f"units[{index}]",
            {"id", "root_ids", "predicate", "qualifier_binding_ids", "disposition"},
            {"readiness_support"},
        )
        unit_id = _require_id(item["id"], f"units[{index}].id")
        if unit_id in unit_ids:
            raise GateError(f"duplicate Unit ID: {unit_id}")
        unit_ids.add(unit_id)
        resolved_roots = sorted(
            {
                _resolve_root_ref(ref, roots)
                for ref in _expect_string_list(item["root_ids"], f"{unit_id}.root_ids")
            }
        )
        if not set(resolved_roots) & ac_root_ids:
            raise GateError(f"Unit {unit_id} must link to at least one AC root")
        disposition = _expect_string(item["disposition"], f"{unit_id}.disposition")
        if disposition not in DISPOSITIONS:
            raise GateError(f"Unit {unit_id} has invalid disposition: {disposition}")
        support = item.get("readiness_support")
        normalized_support: dict[str, Any] | None = None
        if disposition == "PLANNED":
            if support is not None and support != {}:
                raise GateError(
                    f"planned Unit {unit_id} must not carry unsuccessful readiness support"
                )
        else:
            support_obj = _expect_dict(support, f"{unit_id}.readiness_support")
            _expect_keys(
                support_obj,
                f"{unit_id}.readiness_support",
                {
                    "candidate_ids",
                    "adopted_fact_ids",
                    "runner_raw_ids",
                    "alternative_search_closure",
                    "stopping_predicate",
                },
            )
            normalized_support = {
                "candidate_ids": sorted(
                    _expect_string_list(
                        support_obj["candidate_ids"], f"{unit_id}.candidate_ids"
                    )
                ),
                "adopted_fact_ids": sorted(
                    _expect_string_list(
                        support_obj["adopted_fact_ids"], f"{unit_id}.adopted_fact_ids"
                    )
                ),
                "runner_raw_ids": sorted(
                    _expect_string_list(
                        support_obj["runner_raw_ids"],
                        f"{unit_id}.runner_raw_ids",
                        allow_empty=True,
                    )
                ),
                "alternative_search_closure": _expect_string(
                    support_obj["alternative_search_closure"],
                    f"{unit_id}.alternative_search_closure",
                ),
                "stopping_predicate": _expect_string(
                    support_obj["stopping_predicate"], f"{unit_id}.stopping_predicate"
                ),
            }
        units.append(
            {
                "id": unit_id,
                "root_ids": resolved_roots,
                "predicate": _expect_string(item["predicate"], f"{unit_id}.predicate"),
                "qualifier_binding_ids": sorted(
                    _expect_string_list(
                        item["qualifier_binding_ids"],
                        f"{unit_id}.qualifier_binding_ids",
                        allow_empty=True,
                    )
                ),
                "disposition": disposition,
                "readiness_support": normalized_support,
            }
        )
    if not units:
        raise GateError("model must contain at least one Unit")

    bindings: list[dict[str, Any]] = []
    binding_ids: set[str] = set()
    for index, raw in enumerate(
        _expect_list(model["qualifier_bindings"], "qualifier_bindings")
    ):
        item = _expect_dict(raw, f"qualifier_bindings[{index}]")
        _expect_keys(
            item,
            f"qualifier_bindings[{index}]",
            {"id", "source", "source_text", "unit_ids", "meaning"},
        )
        binding_id = _require_id(item["id"], f"qualifier_bindings[{index}].id")
        if binding_id in binding_ids:
            raise GateError(f"duplicate qualifier binding ID: {binding_id}")
        binding_ids.add(binding_id)
        source_ref = _expect_string(item["source"], f"{binding_id}.source")
        source = source_by_id.get(source_ref) or source_by_path.get(source_ref)
        if source is None:
            raise GateError(
                f"qualifier binding {binding_id} cites an unselected source: {source_ref}"
            )
        source_text = _normalize_markdown(
            _expect_string(item["source_text"], f"{binding_id}.source_text")
        )
        if source_text not in source["content"]:
            raise GateError(
                f"qualifier binding {binding_id} source_text is not present in its selected source"
            )
        linked_units = sorted(
            _expect_string_list(item["unit_ids"], f"{binding_id}.unit_ids")
        )
        if not set(linked_units) <= unit_ids:
            raise GateError(f"qualifier binding {binding_id} references unknown Units")
        bindings.append(
            {
                "id": binding_id,
                "source_id": source["id"],
                "source_text": source_text,
                "unit_ids": linked_units,
                "meaning": _expect_string(item["meaning"], f"{binding_id}.meaning"),
            }
        )

    for unit in units:
        if not set(unit["qualifier_binding_ids"]) <= binding_ids:
            raise GateError(f"Unit {unit['id']} references unknown qualifier bindings")
    for binding in bindings:
        for unit_id in binding["unit_ids"]:
            unit = next(candidate for candidate in units if candidate["id"] == unit_id)
            if binding["id"] not in unit["qualifier_binding_ids"]:
                raise GateError(
                    f"qualifier binding {binding['id']} and Unit {unit_id} must reference each other"
                )

    scenarios: list[dict[str, Any]] = []
    scenario_keys: set[str] = set()
    for index, raw in enumerate(_expect_list(model["scenarios"], "scenarios")):
        item = _expect_dict(raw, f"scenarios[{index}]")
        _expect_keys(
            item,
            f"scenarios[{index}]",
            {
                "id",
                "revision",
                "procedure",
                "readiness",
                "readiness_record_ids",
                "preparation_scope",
            },
        )
        scenario_id = _require_id(item["id"], f"scenarios[{index}].id")
        revision = _require_id(item["revision"], f"scenarios[{index}].revision")
        key = f"{scenario_id}@{revision}"
        if key in scenario_keys:
            raise GateError(f"duplicate Scenario revision: {key}")
        scenario_keys.add(key)
        readiness = _expect_string(item["readiness"], f"{key}.readiness")
        if readiness not in SCENARIO_READINESS:
            raise GateError(f"Scenario {key} must be READY or PREPARABLE")
        scenarios.append(
            {
                "id": scenario_id,
                "revision": revision,
                "procedure": _expect_string_list(item["procedure"], f"{key}.procedure"),
                "readiness": readiness,
                "readiness_record_ids": sorted(
                    _expect_string_list(
                        item["readiness_record_ids"], f"{key}.readiness_record_ids"
                    )
                ),
                "preparation_scope": _expect_string(
                    item["preparation_scope"], f"{key}.preparation_scope"
                ),
            }
        )

    edges: list[dict[str, Any]] = []
    edge_ids: set[str] = set()
    for index, raw in enumerate(
        _expect_list(model["coverage_edges"], "coverage_edges")
    ):
        item = _expect_dict(raw, f"coverage_edges[{index}]")
        required = {
            "id",
            "unit_id",
            "scenario_id",
            "scenario_revision",
            "trigger",
            "product_boundary",
            "expected_result",
            "forbidden_result",
            "observation_readback",
            "identity_correlation",
            "decision_predicate",
        }
        _expect_keys(item, f"coverage_edges[{index}]", required)
        edge_id = _require_id(item["id"], f"coverage_edges[{index}].id")
        if edge_id in edge_ids:
            raise GateError(f"duplicate Coverage Edge ID: {edge_id}")
        edge_ids.add(edge_id)
        unit_id = _require_id(item["unit_id"], f"{edge_id}.unit_id")
        if unit_id not in unit_ids:
            raise GateError(f"Coverage Edge {edge_id} references an unknown Unit")
        scenario_id = _require_id(item["scenario_id"], f"{edge_id}.scenario_id")
        revision = _require_id(
            item["scenario_revision"], f"{edge_id}.scenario_revision"
        )
        if f"{scenario_id}@{revision}" not in scenario_keys:
            raise GateError(
                f"Coverage Edge {edge_id} references an unknown Scenario revision"
            )
        normalized = {
            "id": edge_id,
            "unit_id": unit_id,
            "scenario_id": scenario_id,
            "scenario_revision": revision,
        }
        for field in sorted(required - normalized.keys()):
            normalized[field] = _expect_string(item[field], f"{edge_id}.{field}")
        edges.append(normalized)

    planned_units = {unit["id"] for unit in units if unit["disposition"] == "PLANNED"}
    edged_units = {edge["unit_id"] for edge in edges}
    if planned_units != edged_units:
        raise GateError(
            f"planned Units and edged Units must match exactly; missing={sorted(planned_units - edged_units)}, "
            f"unexpected={sorted(edged_units - planned_units)}"
        )
    referenced_scenarios = {
        f"{edge['scenario_id']}@{edge['scenario_revision']}" for edge in edges
    }
    if scenario_keys != referenced_scenarios:
        raise GateError(
            "every Scenario revision must be referenced by at least one Coverage Edge"
        )
    covered_roots = {root_id for unit in units for root_id in unit["root_ids"]}
    if covered_roots != root_ids:
        raise GateError(
            f"every Ticket root must have a Unit; missing={sorted(root_ids - covered_roots)}"
        )

    partial_raw = model["partial"]
    partial: dict[str, Any] | None
    if partial_raw is None:
        partial = None
    else:
        item = _expect_dict(partial_raw, "partial")
        _expect_keys(
            item,
            "partial",
            {"decision_value", "decision_unit_ids", "contradiction_unit_ids"},
        )
        decision_units = sorted(
            _expect_string_list(
                item["decision_unit_ids"], "partial.decision_unit_ids", allow_empty=True
            )
        )
        contradiction_units = sorted(
            _expect_string_list(
                item["contradiction_unit_ids"],
                "partial.contradiction_unit_ids",
                allow_empty=True,
            )
        )
        referenced_units = set(decision_units) | set(contradiction_units)
        if not referenced_units:
            raise GateError("partial value decision must reference at least one Unit")
        if not referenced_units <= planned_units:
            raise GateError("partial value decision may reference only planned Units")
        partial = {
            "decision_value": _expect_string(
                item["decision_value"], "partial.decision_value"
            ),
            "decision_unit_ids": decision_units,
            "contradiction_unit_ids": contradiction_units,
        }
    blocked_units = {unit["id"] for unit in units if unit["disposition"] != "PLANNED"}
    if partial is not None and not blocked_units:
        raise GateError("partial value decision is invalid when every Unit is planned")

    return {
        "units": sorted(units, key=lambda item: item["id"]),
        "qualifier_bindings": sorted(bindings, key=lambda item: item["id"]),
        "coverage_edges": sorted(edges, key=lambda item: item["id"]),
        "scenarios": sorted(scenarios, key=lambda item: (item["id"], item["revision"])),
        "partial": partial,
    }


def _fingerprints(canonical: dict[str, Any], model: dict[str, Any]) -> dict[str, str]:
    scenario_by_key = {
        f"{item['id']}@{item['revision']}": item for item in model["scenarios"]
    }
    referenced_keys = {
        f"{edge['scenario_id']}@{edge['scenario_revision']}"
        for edge in model["coverage_edges"]
    }
    challenge_scenarios = [
        {
            "id": scenario_by_key[key]["id"],
            "revision": scenario_by_key[key]["revision"],
            "procedure": scenario_by_key[key]["procedure"],
        }
        for key in sorted(referenced_keys)
    ]
    challenge_view = {
        "canonical": canonical,
        "units": [
            {
                "id": unit["id"],
                "root_ids": unit["root_ids"],
                "predicate": unit["predicate"],
                "qualifier_binding_ids": unit["qualifier_binding_ids"],
            }
            for unit in model["units"]
        ],
        "qualifier_bindings": model["qualifier_bindings"],
        "coverage_edges": model["coverage_edges"],
        "scenario_semantics": challenge_scenarios,
    }
    challenge_fp = _digest(challenge_view)
    plan_fp = _digest({"challenge_fp": challenge_fp, "model": model})
    return {"challenge_fp": challenge_fp, "plan_fp": plan_fp}


def build(ticket: Path, model_path: Path) -> dict[str, Any]:
    canonical = _canonical_package(ticket)
    model = _normalize_model(_read_json(model_path, "coverage model"), canonical)
    return {
        "schema": SCHEMA,
        "canonical": canonical,
        **model,
        "fingerprints": _fingerprints(canonical, model),
        "structural_status": "PASS",
    }


def _validate_envelope(
    envelope: dict[str, Any], *, require_current_sources: bool = True
) -> None:
    _expect_keys(
        envelope,
        "envelope",
        {
            "schema",
            "canonical",
            "units",
            "qualifier_bindings",
            "coverage_edges",
            "scenarios",
            "partial",
            "fingerprints",
            "structural_status",
        },
    )
    if envelope["schema"] != SCHEMA or envelope["structural_status"] != "PASS":
        raise GateError("envelope schema or structural status is invalid")
    canonical = _expect_dict(envelope["canonical"], "envelope.canonical")
    project_root = Path(
        _expect_string(canonical.get("project_root"), "canonical.project_root")
    )
    ticket_relative = Path(_expect_string(canonical.get("ticket"), "canonical.ticket"))
    if ticket_relative.is_absolute() or ".." in ticket_relative.parts:
        raise GateError("canonical.ticket must be a safe Project-Root-relative path")
    if require_current_sources:
        regenerated_canonical = _canonical_package(project_root / ticket_relative)
        if regenerated_canonical != canonical:
            raise GateError(
                "envelope canonical package is stale or does not match current sources"
            )
    raw_model = {
        "units": envelope["units"],
        "qualifier_bindings": [
            {
                "id": binding["id"],
                "source": binding["source_id"],
                "source_text": binding["source_text"],
                "unit_ids": binding["unit_ids"],
                "meaning": binding["meaning"],
            }
            for binding in _expect_list(
                envelope["qualifier_bindings"], "envelope.qualifier_bindings"
            )
        ],
        "coverage_edges": envelope["coverage_edges"],
        "scenarios": envelope["scenarios"],
        "partial": envelope["partial"],
    }
    normalized_model = _normalize_model(raw_model, canonical)
    for field, value in normalized_model.items():
        if value != envelope[field]:
            raise GateError(f"envelope {field} is not a valid normalized projection")
    fingerprints = _fingerprints(canonical, normalized_model)
    if fingerprints != envelope["fingerprints"]:
        raise GateError("envelope fingerprints do not match its contents")


def _root_accounting(attestation: dict[str, Any], envelope: dict[str, Any]) -> None:
    root_ids = {root["id"] for root in envelope["canonical"]["roots"]}
    unit_by_id = {unit["id"]: unit for unit in envelope["units"]}
    edge_by_id = {edge["id"]: edge for edge in envelope["coverage_edges"]}
    seen_roots: set[str] = set()
    seen_units: set[str] = set()
    seen_edges: set[str] = set()
    seen_unit_root_pairs: set[tuple[str, str]] = set()
    seen_edge_root_pairs: set[tuple[str, str]] = set()
    for index, raw_root in enumerate(
        _expect_list(attestation["roots"], "attestation.roots")
    ):
        root = _expect_dict(raw_root, f"attestation.roots[{index}]")
        _expect_keys(root, f"attestation.roots[{index}]", {"root_id", "checks"})
        root_id = _expect_string(root["root_id"], "attestation root_id")
        if root_id not in root_ids or root_id in seen_roots:
            raise GateError(f"attestation has an unknown or duplicate root: {root_id}")
        seen_roots.add(root_id)
        checks = _expect_list(root["checks"], f"{root_id}.checks")
        if not checks:
            raise GateError(f"attestation root {root_id} has no semantic checks")
        for check_index, raw_check in enumerate(checks):
            check = _expect_dict(raw_check, f"{root_id}.checks[{check_index}]")
            _expect_keys(
                check,
                f"{root_id}.checks[{check_index}]",
                {"predicate", "unit_ids", "edge_ids"},
            )
            _expect_string(
                check["predicate"], f"{root_id}.checks[{check_index}].predicate"
            )
            unit_ids = _expect_string_list(
                check["unit_ids"], f"{root_id}.check.unit_ids"
            )
            edge_ids = _expect_string_list(
                check["edge_ids"], f"{root_id}.check.edge_ids", allow_empty=True
            )
            if (
                not set(unit_ids) <= unit_by_id.keys()
                or not set(edge_ids) <= edge_by_id.keys()
            ):
                raise GateError(
                    f"attestation check for {root_id} references unknown Units or Edges"
                )
            if any(
                root_id not in unit_by_id[unit_id]["root_ids"] for unit_id in unit_ids
            ):
                raise GateError(
                    f"attestation check maps root {root_id} to an unrelated Unit"
                )
            if any(
                edge_by_id[edge_id]["unit_id"] not in unit_ids for edge_id in edge_ids
            ):
                raise GateError(
                    f"attestation check for {root_id} cites an Edge without its Unit"
                )
            seen_units.update(unit_ids)
            seen_edges.update(edge_ids)
            seen_unit_root_pairs.update((unit_id, root_id) for unit_id in unit_ids)
            seen_edge_root_pairs.update((edge_id, root_id) for edge_id in edge_ids)
    if seen_roots != root_ids:
        raise GateError(
            f"attestation root accounting is incomplete: {sorted(root_ids - seen_roots)}"
        )
    if seen_units != unit_by_id.keys():
        raise GateError(
            f"attestation Unit accounting is incomplete: {sorted(unit_by_id.keys() - seen_units)}"
        )
    if seen_edges != edge_by_id.keys():
        raise GateError(
            f"attestation Edge accounting is incomplete: {sorted(edge_by_id.keys() - seen_edges)}"
        )
    expected_unit_root_pairs = {
        (unit_id, root_id)
        for unit_id, unit in unit_by_id.items()
        for root_id in unit["root_ids"]
    }
    if seen_unit_root_pairs != expected_unit_root_pairs:
        raise GateError(
            "attestation Unit-to-root accounting is incomplete: "
            f"{sorted(expected_unit_root_pairs - seen_unit_root_pairs)}"
        )
    expected_edge_root_pairs = {
        (edge_id, root_id)
        for edge_id, edge in edge_by_id.items()
        for root_id in unit_by_id[edge["unit_id"]]["root_ids"]
    }
    if seen_edge_root_pairs != expected_edge_root_pairs:
        raise GateError(
            "attestation Edge-to-root accounting is incomplete: "
            f"{sorted(expected_edge_root_pairs - seen_edge_root_pairs)}"
        )
    checked_bindings = set(
        _expect_string_list(
            attestation["qualifier_binding_ids_checked"],
            "attestation.qualifier_binding_ids_checked",
            allow_empty=True,
        )
    )
    binding_ids = {binding["id"] for binding in envelope["qualifier_bindings"]}
    if checked_bindings != binding_ids:
        raise GateError("attestation qualifier-binding accounting must match exactly")


def _validate_defects(attestation: dict[str, Any], envelope: dict[str, Any]) -> None:
    expected_sets = {
        "reviewed_root_ids": {root["id"] for root in envelope["canonical"]["roots"]},
        "reviewed_unit_ids": {unit["id"] for unit in envelope["units"]},
        "reviewed_edge_ids": {edge["id"] for edge in envelope["coverage_edges"]},
        "reviewed_qualifier_binding_ids": {
            binding["id"] for binding in envelope["qualifier_bindings"]
        },
    }
    for field, expected in expected_sets.items():
        actual = set(
            _expect_string_list(
                attestation[field], f"attestation.{field}", allow_empty=True
            )
        )
        if actual != expected:
            raise GateError(
                f"DEFECT response {field} must account for the complete challenged scope"
            )
    source_ids = {source["id"] for source in envelope["canonical"]["qualifier_sources"]}
    units_by_id = {unit["id"]: unit for unit in envelope["units"]}
    edges_by_id = {edge["id"]: edge for edge in envelope["coverage_edges"]}
    defect_ids: set[str] = set()
    defects = _expect_list(attestation["defects"], "attestation.defects")
    if not defects:
        raise GateError("DEFECT response must contain at least one certificate")
    for index, raw in enumerate(defects):
        defect = _expect_dict(raw, f"defects[{index}]")
        _expect_keys(
            defect,
            f"defects[{index}]",
            {
                "id",
                "class",
                "root_id",
                "qualifier_source_ids",
                "unit_ids",
                "edge_ids",
                "plan_can_pass_when",
                "still_unverified",
            },
        )
        defect_id = _require_id(defect["id"], f"defects[{index}].id")
        if defect_id in defect_ids:
            raise GateError(f"duplicate defect ID: {defect_id}")
        defect_ids.add(defect_id)
        defect_class = _expect_string(defect["class"], f"{defect_id}.class")
        if defect_class not in DEFECT_CLASSES:
            raise GateError(f"invalid defect class: {defect_class}")
        root_id = _expect_string(defect["root_id"], f"{defect_id}.root_id")
        if root_id not in expected_sets["reviewed_root_ids"]:
            raise GateError(f"defect {defect_id} cites an unknown Ticket root")
        qualifier_sources = set(
            _expect_string_list(
                defect["qualifier_source_ids"],
                f"{defect_id}.qualifier_source_ids",
                allow_empty=True,
            )
        )
        if not qualifier_sources <= source_ids:
            raise GateError(f"defect {defect_id} cites an unknown qualifier source")
        units = set(
            _expect_string_list(
                defect["unit_ids"], f"{defect_id}.unit_ids", allow_empty=True
            )
        )
        edges = set(
            _expect_string_list(
                defect["edge_ids"], f"{defect_id}.edge_ids", allow_empty=True
            )
        )
        if (
            not units <= expected_sets["reviewed_unit_ids"]
            or not edges <= expected_sets["reviewed_edge_ids"]
        ):
            raise GateError(f"defect {defect_id} cites an unknown Unit or Edge")
        if defect_class in {"MISBOUND_EDGE", "ILLEGAL_COLLAPSE"} and not edges:
            raise GateError(f"defect {defect_id} requires at least one affected Edge")
        if defect_class == "MISSING_QUALIFIER" and (not units or not qualifier_sources):
            raise GateError(
                f"defect {defect_id} requires an affected Unit and qualifier source"
            )
        if any(root_id not in units_by_id[unit_id]["root_ids"] for unit_id in units):
            raise GateError(
                f"defect {defect_id} cites a Unit unrelated to its Ticket root"
            )
        if any(edges_by_id[edge_id]["unit_id"] not in units for edge_id in edges):
            raise GateError(
                f"defect {defect_id} cites an Edge without its affected Unit"
            )
        _expect_string(defect["plan_can_pass_when"], f"{defect_id}.plan_can_pass_when")
        _expect_string(defect["still_unverified"], f"{defect_id}.still_unverified")


def _validated_initial_attestation(
    attestation: dict[str, Any], envelope: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    result = _expect_string(attestation.get("result"), "attestation.result")
    if result == "PASS":
        _expect_keys(
            attestation,
            "PASS attestation",
            {
                "schema",
                "result",
                "challenge_fp",
                "roots",
                "qualifier_binding_ids_checked",
            },
        )
        _root_accounting(attestation, envelope)
    elif result == "DEFECT":
        _expect_keys(
            attestation,
            "DEFECT attestation",
            {
                "schema",
                "result",
                "challenge_fp",
                "reviewed_root_ids",
                "reviewed_unit_ids",
                "reviewed_edge_ids",
                "reviewed_qualifier_binding_ids",
                "defects",
            },
        )
        _validate_defects(attestation, envelope)
    else:
        raise GateError("initial attestation result must be PASS or DEFECT")
    return result, attestation


def _validated_rebuttal(
    attestation: dict[str, Any], envelope: dict[str, Any], prior_receipt: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    _expect_keys(
        attestation,
        "REBUTTAL attestation",
        {"schema", "result", "challenge_fp", "prior_attestation_digest", "outcomes"},
        {"pass_accounting"},
    )
    if attestation.get("result") != "REBUTTAL":
        raise GateError("a prior receipt accepts only a REBUTTAL attestation")
    if prior_receipt.get("effective_result") != "DEFECT":
        raise GateError("rebuttal requires a prior DEFECT receipt")
    if (
        "prior_receipt" in prior_receipt
        or prior_receipt.get("attestation", {}).get("result") != "DEFECT"
    ):
        raise GateError(
            "the gate permits exactly one rebuttal to an initial DEFECT response"
        )
    if attestation.get("prior_attestation_digest") != prior_receipt.get(
        "attestation_digest"
    ):
        raise GateError("rebuttal does not bind the exact prior defect attestation")
    prior_defects = {
        item["id"]: item for item in prior_receipt["attestation"]["defects"]
    }
    outcomes: dict[str, str] = {}
    for index, raw in enumerate(
        _expect_list(attestation["outcomes"], "rebuttal.outcomes")
    ):
        item = _expect_dict(raw, f"rebuttal.outcomes[{index}]")
        _expect_keys(item, f"rebuttal.outcomes[{index}]", {"defect_id", "decision"})
        defect_id = _expect_string(item["defect_id"], "rebuttal defect_id")
        decision = _expect_string(item["decision"], f"{defect_id}.decision")
        if defect_id not in prior_defects or defect_id in outcomes:
            raise GateError(
                f"rebuttal cites an unknown or duplicate defect: {defect_id}"
            )
        if decision not in {"WITHDRAW", "SUSTAIN"}:
            raise GateError(
                f"rebuttal decision must be WITHDRAW or SUSTAIN: {defect_id}"
            )
        outcomes[defect_id] = decision
    if outcomes.keys() != prior_defects.keys():
        raise GateError("rebuttal must decide every prior defect exactly once")
    sustained = [
        prior_defects[defect_id]
        for defect_id, decision in outcomes.items()
        if decision == "SUSTAIN"
    ]
    if sustained:
        if "pass_accounting" in attestation:
            raise GateError("a sustained rebuttal must not include PASS accounting")
        return "DEFECT", attestation
    pass_accounting = _expect_dict(
        attestation.get("pass_accounting"), "rebuttal.pass_accounting"
    )
    _expect_keys(
        pass_accounting,
        "rebuttal.pass_accounting",
        {"roots", "qualifier_binding_ids_checked"},
    )
    _root_accounting(pass_accounting, envelope)
    return "PASS", attestation


def _pass_accounting(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("effective_result") != "PASS":
        raise GateError("changed-scope reuse requires a prior PASS receipt")
    attestation = _expect_dict(receipt.get("attestation"), "prior PASS attestation")
    if attestation.get("result") == "PASS":
        return {
            "roots": attestation["roots"],
            "qualifier_binding_ids_checked": attestation[
                "qualifier_binding_ids_checked"
            ],
        }
    if attestation.get("result") == "REBUTTAL":
        return _expect_dict(
            attestation.get("pass_accounting"),
            "prior rebuttal PASS accounting",
        )
    raise GateError("prior PASS receipt has no reusable full accounting")


def _scoped_envelope(
    envelope: dict[str, Any], changed: dict[str, Any]
) -> dict[str, Any]:
    root_ids = set(changed["root_ids"])
    unit_ids = {
        unit["id"] for unit in envelope["units"] if set(unit["root_ids"]) & root_ids
    }
    edge_ids = {
        edge["id"] for edge in envelope["coverage_edges"] if edge["unit_id"] in unit_ids
    }
    binding_ids = {
        binding["id"]
        for binding in envelope["qualifier_bindings"]
        if set(binding["unit_ids"]) & unit_ids
    }
    return {
        "canonical": {
            "roots": [
                root
                for root in envelope["canonical"]["roots"]
                if root["id"] in root_ids
            ],
            "qualifier_sources": envelope["canonical"]["qualifier_sources"],
        },
        "units": [
            {
                **unit,
                "root_ids": [
                    root_id for root_id in unit["root_ids"] if root_id in root_ids
                ],
            }
            for unit in envelope["units"]
            if unit["id"] in unit_ids
        ],
        "coverage_edges": [
            edge for edge in envelope["coverage_edges"] if edge["id"] in edge_ids
        ],
        "qualifier_bindings": [
            binding
            for binding in envelope["qualifier_bindings"]
            if binding["id"] in binding_ids
        ],
    }


def _scoped_scope(
    envelope: dict[str, Any],
    prior_receipt: dict[str, Any],
    old_envelope: dict[str, Any],
    prior_challenge_fp: Any,
    prior_attestation_digest: Any,
    *,
    historical_replay: bool = False,
) -> dict[str, Any]:
    _validate_envelope(old_envelope, require_current_sources=False)
    _validate_receipt(old_envelope, prior_receipt)
    if prior_challenge_fp != old_envelope["fingerprints"]["challenge_fp"]:
        raise GateError("scoped challenge does not bind the old envelope")
    if prior_attestation_digest != prior_receipt["attestation_digest"]:
        raise GateError(
            "scoped challenge does not bind the exact prior PASS attestation"
        )
    change = diff(
        old_envelope,
        envelope,
        require_new_current_sources=not historical_replay,
    )
    if not change["rechallenge_required"]:
        raise GateError("scoped challenge is invalid when challenge_fp did not change")
    changed = change["changed_or_dependent"]
    if not changed["root_ids"]:
        raise GateError(
            "changed semantic input did not resolve to an affected Ticket root"
        )
    return _scoped_envelope(envelope, changed)


def _validated_scoped_pass(
    attestation: dict[str, Any],
    envelope: dict[str, Any],
    prior_receipt: dict[str, Any],
    old_envelope: dict[str, Any],
    *,
    historical_replay: bool = False,
) -> dict[str, Any]:
    _expect_keys(
        attestation,
        "SCOPED_PASS attestation",
        {
            "schema",
            "result",
            "challenge_fp",
            "prior_challenge_fp",
            "prior_attestation_digest",
            "roots",
            "qualifier_binding_ids_checked",
        },
    )
    if attestation.get("result") != "SCOPED_PASS":
        raise GateError(
            "a prior PASS receipt accepts only SCOPED_PASS or SCOPED_DEFECT"
        )
    scope = _scoped_scope(
        envelope,
        prior_receipt,
        old_envelope,
        attestation["prior_challenge_fp"],
        attestation["prior_attestation_digest"],
        historical_replay=historical_replay,
    )
    _root_accounting(attestation, scope)

    old_accounting = _pass_accounting(prior_receipt)
    scoped_root_ids = {root["id"] for root in scope["canonical"]["roots"]}
    current_root_ids = [root["id"] for root in envelope["canonical"]["roots"]]
    old_roots = {root["root_id"]: root for root in old_accounting["roots"]}
    fresh_roots = {root["root_id"]: root for root in attestation["roots"]}
    merged_roots: list[dict[str, Any]] = []
    for root_id in current_root_ids:
        source = fresh_roots if root_id in scoped_root_ids else old_roots
        if root_id not in source:
            raise GateError(f"prior PASS cannot carry forward current root: {root_id}")
        merged_roots.append(source[root_id])

    current_binding_ids = {binding["id"] for binding in envelope["qualifier_bindings"]}
    scoped_binding_ids = {binding["id"] for binding in scope["qualifier_bindings"]}
    old_binding_ids = set(old_accounting["qualifier_binding_ids_checked"])
    merged_binding_ids = (old_binding_ids & current_binding_ids) - scoped_binding_ids
    merged_binding_ids.update(attestation["qualifier_binding_ids_checked"])
    merged = {
        "schema": ATTESTATION_SCHEMA,
        "result": "PASS",
        "challenge_fp": envelope["fingerprints"]["challenge_fp"],
        "roots": merged_roots,
        "qualifier_binding_ids_checked": sorted(merged_binding_ids),
    }
    _root_accounting(merged, envelope)
    return merged


def _validated_scoped_defect(
    attestation: dict[str, Any],
    envelope: dict[str, Any],
    prior_receipt: dict[str, Any],
    old_envelope: dict[str, Any],
    *,
    historical_replay: bool = False,
) -> dict[str, Any]:
    _expect_keys(
        attestation,
        "SCOPED_DEFECT attestation",
        {
            "schema",
            "result",
            "challenge_fp",
            "prior_challenge_fp",
            "prior_attestation_digest",
            "reviewed_root_ids",
            "reviewed_unit_ids",
            "reviewed_edge_ids",
            "reviewed_qualifier_binding_ids",
            "defects",
        },
    )
    if attestation.get("result") != "SCOPED_DEFECT":
        raise GateError("expected SCOPED_DEFECT")
    scope = _scoped_scope(
        envelope,
        prior_receipt,
        old_envelope,
        attestation["prior_challenge_fp"],
        attestation["prior_attestation_digest"],
        historical_replay=historical_replay,
    )
    _validate_defects(attestation, scope)
    return attestation


def _validated_scoped_rebuttal(
    attestation: dict[str, Any],
    envelope: dict[str, Any],
    scoped_defect_receipt: dict[str, Any],
    old_envelope: dict[str, Any],
    *,
    historical_replay: bool = False,
) -> tuple[str, dict[str, Any]]:
    _expect_keys(
        attestation,
        "SCOPED_REBUTTAL attestation",
        {
            "schema",
            "result",
            "challenge_fp",
            "prior_attestation_digest",
            "outcomes",
        },
        {"pass_accounting"},
    )
    if attestation.get("result") != "SCOPED_REBUTTAL":
        raise GateError("a scoped defect permits only one SCOPED_REBUTTAL")
    if scoped_defect_receipt.get("effective_result") != "DEFECT":
        raise GateError("SCOPED_REBUTTAL requires a scoped DEFECT receipt")
    defect_attestation = _expect_dict(
        scoped_defect_receipt.get("attestation"), "scoped defect attestation"
    )
    if defect_attestation.get("result") != "SCOPED_DEFECT":
        raise GateError("SCOPED_REBUTTAL requires an initial SCOPED_DEFECT")
    _validate_receipt(envelope, scoped_defect_receipt)
    if (
        attestation["prior_attestation_digest"]
        != scoped_defect_receipt["attestation_digest"]
    ):
        raise GateError("SCOPED_REBUTTAL does not bind the exact scoped defect")
    reuse = _expect_dict(
        scoped_defect_receipt.get("scoped_reuse"), "scoped defect reuse"
    )
    prior_receipt = _expect_dict(
        scoped_defect_receipt.get("prior_receipt"), "scoped defect prior PASS"
    )
    embedded_old = _expect_dict(reuse.get("old_envelope"), "scoped defect old envelope")
    if embedded_old != old_envelope:
        raise GateError("SCOPED_REBUTTAL old envelope does not match scoped defect")
    scope = _scoped_scope(
        envelope,
        prior_receipt,
        old_envelope,
        defect_attestation["prior_challenge_fp"],
        defect_attestation["prior_attestation_digest"],
        historical_replay=historical_replay,
    )
    prior_defects = {item["id"]: item for item in defect_attestation["defects"]}
    outcomes: dict[str, str] = {}
    for index, raw in enumerate(
        _expect_list(attestation["outcomes"], "scoped rebuttal outcomes")
    ):
        item = _expect_dict(raw, f"scoped rebuttal outcomes[{index}]")
        _expect_keys(
            item, f"scoped rebuttal outcomes[{index}]", {"defect_id", "decision"}
        )
        defect_id = _expect_string(item["defect_id"], "scoped rebuttal defect_id")
        decision = _expect_string(item["decision"], f"{defect_id}.decision")
        if defect_id not in prior_defects or defect_id in outcomes:
            raise GateError(
                f"scoped rebuttal cites an unknown or duplicate defect: {defect_id}"
            )
        if decision not in {"WITHDRAW", "SUSTAIN"}:
            raise GateError(
                f"scoped rebuttal decision must be WITHDRAW or SUSTAIN: {defect_id}"
            )
        outcomes[defect_id] = decision
    if outcomes.keys() != prior_defects.keys():
        raise GateError("scoped rebuttal must decide every scoped defect exactly once")
    if any(decision == "SUSTAIN" for decision in outcomes.values()):
        if "pass_accounting" in attestation:
            raise GateError(
                "a sustained scoped rebuttal must not include PASS accounting"
            )
        return "DEFECT", attestation
    pass_accounting = _expect_dict(
        attestation.get("pass_accounting"), "scoped rebuttal pass_accounting"
    )
    _expect_keys(
        pass_accounting,
        "scoped rebuttal pass_accounting",
        {"roots", "qualifier_binding_ids_checked"},
    )
    scoped_pass = {
        "schema": ATTESTATION_SCHEMA,
        "result": "SCOPED_PASS",
        "challenge_fp": envelope["fingerprints"]["challenge_fp"],
        "prior_challenge_fp": defect_attestation["prior_challenge_fp"],
        "prior_attestation_digest": prior_receipt["attestation_digest"],
        "roots": pass_accounting["roots"],
        "qualifier_binding_ids_checked": pass_accounting[
            "qualifier_binding_ids_checked"
        ],
    }
    _root_accounting(scoped_pass, scope)
    merged = _validated_scoped_pass(
        scoped_pass,
        envelope,
        prior_receipt,
        old_envelope,
        historical_replay=historical_replay,
    )
    return "PASS", merged


def check_attestation(
    envelope: dict[str, Any],
    attestation: dict[str, Any],
    prior_receipt: dict[str, Any] | None,
    old_envelope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_envelope(envelope)
    if attestation.get("schema") != ATTESTATION_SCHEMA:
        raise GateError("attestation schema is invalid")
    if attestation.get("challenge_fp") != envelope["fingerprints"]["challenge_fp"]:
        raise GateError("attestation challenge_fp does not match the envelope")
    if prior_receipt is None:
        if old_envelope is not None:
            raise GateError("old envelope requires a prior PASS receipt")
        effective_result, normalized = _validated_initial_attestation(
            attestation, envelope
        )
    elif prior_receipt.get("effective_result") == "PASS":
        if old_envelope is None:
            raise GateError("changed-scope reuse requires the old envelope")
        if attestation.get("result") == "SCOPED_PASS":
            normalized = _validated_scoped_pass(
                attestation, envelope, prior_receipt, old_envelope
            )
            effective_result = "PASS"
        elif attestation.get("result") == "SCOPED_DEFECT":
            normalized = _validated_scoped_defect(
                attestation, envelope, prior_receipt, old_envelope
            )
            effective_result = "DEFECT"
        else:
            raise GateError("a prior PASS accepts only SCOPED_PASS or SCOPED_DEFECT")
    else:
        if prior_receipt.get("attestation", {}).get("result") == "SCOPED_DEFECT":
            if old_envelope is None:
                raise GateError("SCOPED_REBUTTAL requires the old envelope")
            _validate_receipt(envelope, prior_receipt)
            effective_result, normalized = _validated_scoped_rebuttal(
                attestation, envelope, prior_receipt, old_envelope
            )
        else:
            if old_envelope is not None:
                raise GateError("ordinary rebuttal must not supply an old envelope")
            _validate_receipt(envelope, prior_receipt)
            effective_result, normalized = _validated_rebuttal(
                attestation, envelope, prior_receipt
            )
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "effective_result": effective_result,
        "challenge_fp": envelope["fingerprints"]["challenge_fp"],
        "attestation_digest": _digest(normalized),
        "attestation": normalized,
    }
    if prior_receipt is not None:
        receipt["prior_receipt"] = prior_receipt
    if old_envelope is not None:
        receipt["scoped_reuse"] = {
            "old_envelope": old_envelope,
            "scoped_attestation": attestation,
        }
    return receipt


def _validate_receipt(envelope: dict[str, Any], receipt: dict[str, Any]) -> None:
    _expect_keys(
        receipt,
        "attestation receipt",
        {
            "schema",
            "effective_result",
            "challenge_fp",
            "attestation_digest",
            "attestation",
        },
        {"prior_receipt", "scoped_reuse"},
    )
    if receipt["schema"] != RECEIPT_SCHEMA:
        raise GateError("attestation receipt schema is invalid")
    if receipt["challenge_fp"] != envelope["fingerprints"]["challenge_fp"]:
        raise GateError("attestation receipt is stale")
    attestation = _expect_dict(receipt["attestation"], "receipt.attestation")
    if receipt["attestation_digest"] != _digest(attestation):
        raise GateError("attestation receipt digest is invalid")
    if attestation.get("schema") != ATTESTATION_SCHEMA:
        raise GateError("receipt attestation schema is invalid")
    if attestation.get("challenge_fp") != envelope["fingerprints"]["challenge_fp"]:
        raise GateError("receipt attestation challenge_fp is stale")
    prior = receipt.get("prior_receipt")
    scoped_reuse = receipt.get("scoped_reuse")
    if scoped_reuse is not None:
        if prior is None:
            raise GateError("scoped reuse receipt is missing its prior receipt")
        reuse = _expect_dict(scoped_reuse, "receipt.scoped_reuse")
        _expect_keys(
            reuse,
            "receipt.scoped_reuse",
            {"old_envelope", "scoped_attestation"},
        )
        prior_receipt = _expect_dict(prior, "receipt.prior_receipt")
        old_envelope = _expect_dict(reuse["old_envelope"], "receipt old envelope")
        scoped_attestation = _expect_dict(
            reuse["scoped_attestation"], "receipt scoped attestation"
        )
        scoped_result = scoped_attestation.get("result")
        if scoped_result == "SCOPED_PASS":
            expected = _validated_scoped_pass(
                scoped_attestation,
                envelope,
                prior_receipt,
                old_envelope,
                historical_replay=True,
            )
            effective_result = "PASS"
        elif scoped_result == "SCOPED_DEFECT":
            expected = _validated_scoped_defect(
                scoped_attestation,
                envelope,
                prior_receipt,
                old_envelope,
                historical_replay=True,
            )
            effective_result = "DEFECT"
        elif scoped_result == "SCOPED_REBUTTAL":
            effective_result, expected = _validated_scoped_rebuttal(
                scoped_attestation,
                envelope,
                prior_receipt,
                old_envelope,
                historical_replay=True,
            )
        else:
            raise GateError("scoped receipt has an unsupported attestation result")
        if expected != attestation:
            raise GateError(
                "scoped receipt does not contain its validated effective attestation"
            )
    elif prior is None:
        effective_result, _ = _validated_initial_attestation(attestation, envelope)
    else:
        prior_receipt = _expect_dict(prior, "receipt.prior_receipt")
        _validate_receipt(envelope, prior_receipt)
        effective_result, _ = _validated_rebuttal(attestation, envelope, prior_receipt)
    if effective_result != receipt["effective_result"]:
        raise GateError(
            "attestation receipt effective_result does not match its validated chain"
        )


def approve(envelope: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    _validate_envelope(envelope)
    _validate_receipt(envelope, receipt)
    mode = "OPEN"
    reason = "independent semantic coverage challenge has unresolved defects"
    if receipt["effective_result"] == "PASS":
        dispositions = {unit["disposition"] for unit in envelope["units"]}
        if dispositions == {"PLANNED"}:
            mode = "TOTAL"
            reason = "every required Unit is planned under a current independent PASS"
        elif dispositions <= DISPOSITIONS and dispositions - {"PLANNED"}:
            if envelope["partial"] is not None:
                mode = "PARTIAL"
                reason = "the complete denominator is independently accounted and blocked Units are evidence-bound"
            else:
                reason = "blocked Units require a positive partial value decision"
    elif receipt["effective_result"] != "DEFECT":
        raise GateError("attestation receipt effective_result is invalid")
    approval_id = None
    if mode != "OPEN":
        approval_id = f"A:{_digest([envelope['fingerprints']['plan_fp'], receipt['attestation_digest']], 12)}"
    return {
        "schema": APPROVAL_SCHEMA,
        "mode": mode,
        "reason": reason,
        "challenge_fp": envelope["fingerprints"]["challenge_fp"],
        "plan_fp": envelope["fingerprints"]["plan_fp"],
        "attestation_digest": receipt["attestation_digest"],
        "approval_id": approval_id,
    }


def _changed_ids(
    old_items: list[dict[str, Any]], new_items: list[dict[str, Any]], key
) -> set[str]:
    old = {key(item): item for item in old_items}
    new = {key(item): item for item in new_items}
    return {
        item_id
        for item_id in old.keys() | new.keys()
        if old.get(item_id) != new.get(item_id)
    }


def diff(
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    require_new_current_sources: bool = True,
) -> dict[str, Any]:
    _validate_envelope(old, require_current_sources=False)
    _validate_envelope(new, require_current_sources=require_new_current_sources)
    changed_roots = _changed_ids(
        old["canonical"]["roots"], new["canonical"]["roots"], lambda item: item["id"]
    )
    changed_sources = _changed_ids(
        old["canonical"]["qualifier_sources"],
        new["canonical"]["qualifier_sources"],
        lambda item: item["id"],
    )
    changed_bindings = _changed_ids(
        old["qualifier_bindings"], new["qualifier_bindings"], lambda item: item["id"]
    )
    changed_units = _changed_ids(
        [
            {
                "id": item["id"],
                "root_ids": item["root_ids"],
                "predicate": item["predicate"],
                "qualifier_binding_ids": item["qualifier_binding_ids"],
            }
            for item in old["units"]
        ],
        [
            {
                "id": item["id"],
                "root_ids": item["root_ids"],
                "predicate": item["predicate"],
                "qualifier_binding_ids": item["qualifier_binding_ids"],
            }
            for item in new["units"]
        ],
        lambda item: item["id"],
    )
    if changed_sources:
        changed_roots.update(
            root["id"]
            for envelope in (old, new)
            for root in envelope["canonical"]["roots"]
        )
    for envelope in (old, new):
        changed_units.update(
            unit["id"]
            for unit in envelope["units"]
            if set(unit["root_ids"]) & changed_roots
        )
        changed_units.update(
            unit_id
            for binding in envelope["qualifier_bindings"]
            if binding["id"] in changed_bindings
            or binding["source_id"] in changed_sources
            for unit_id in binding["unit_ids"]
        )
    changed_scenario_semantics = _changed_ids(
        [
            {
                "id": item["id"],
                "revision": item["revision"],
                "procedure": item["procedure"],
            }
            for item in old["scenarios"]
        ],
        [
            {
                "id": item["id"],
                "revision": item["revision"],
                "procedure": item["procedure"],
            }
            for item in new["scenarios"]
        ],
        lambda item: f"{item['id']}@{item['revision']}",
    )
    changed_edges = _changed_ids(
        old["coverage_edges"], new["coverage_edges"], lambda item: item["id"]
    )
    for envelope in (old, new):
        changed_edges.update(
            edge["id"]
            for edge in envelope["coverage_edges"]
            if edge["unit_id"] in changed_units
            or f"{edge['scenario_id']}@{edge['scenario_revision']}"
            in changed_scenario_semantics
        )
        changed_units.update(
            edge["unit_id"]
            for edge in envelope["coverage_edges"]
            if edge["id"] in changed_edges
        )
    for envelope in (old, new):
        changed_roots.update(
            root_id
            for unit in envelope["units"]
            if unit["id"] in changed_units
            for root_id in unit["root_ids"]
        )
    changed_scenarios = _changed_ids(
        old["scenarios"],
        new["scenarios"],
        lambda item: f"{item['id']}@{item['revision']}",
    )
    return {
        "challenge_changed": old["fingerprints"]["challenge_fp"]
        != new["fingerprints"]["challenge_fp"],
        "plan_changed": old["fingerprints"]["plan_fp"]
        != new["fingerprints"]["plan_fp"],
        "rechallenge_required": old["fingerprints"]["challenge_fp"]
        != new["fingerprints"]["challenge_fp"],
        "reapproval_required": old["fingerprints"]["plan_fp"]
        != new["fingerprints"]["plan_fp"],
        "changed_or_dependent": {
            "root_ids": sorted(changed_roots),
            "qualifier_source_ids": sorted(changed_sources),
            "qualifier_binding_ids": sorted(changed_bindings),
            "unit_ids": sorted(changed_units),
            "edge_ids": sorted(changed_edges),
            "scenario_revisions": sorted(changed_scenarios),
        },
    }


def _output_path(raw: str | None) -> Path | None:
    return Path(raw) if raw is not None else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--ticket", type=Path, required=True)
    build_parser.add_argument("--model", type=Path, required=True)
    build_parser.add_argument("--output", required=True)

    check_parser = subparsers.add_parser("check-attestation")
    check_parser.add_argument("--envelope", type=Path, required=True)
    check_parser.add_argument("--attestation", type=Path, required=True)
    check_parser.add_argument("--prior-receipt", type=Path)
    check_parser.add_argument("--old-envelope", type=Path)
    check_parser.add_argument("--output", required=True)

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("--envelope", type=Path, required=True)
    approve_parser.add_argument("--receipt", type=Path, required=True)
    approve_parser.add_argument("--output", required=True)

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("--old", type=Path, required=True)
    diff_parser.add_argument("--new", type=Path, required=True)
    diff_parser.add_argument("--output")

    args = parser.parse_args()
    try:
        if args.operation == "build":
            envelope = build(args.ticket, args.model)
            _write_json(
                _output_path(args.output),
                envelope,
                Path(envelope["canonical"]["project_root"]),
            )
        elif args.operation == "check-attestation":
            envelope = _read_json(args.envelope, "coverage envelope")
            attestation = _read_json(args.attestation, "challenge attestation")
            prior = (
                _read_json(args.prior_receipt, "prior attestation receipt")
                if args.prior_receipt
                else None
            )
            old_envelope = (
                _read_json(args.old_envelope, "old coverage envelope")
                if args.old_envelope
                else None
            )
            receipt = check_attestation(envelope, attestation, prior, old_envelope)
            _write_json(
                _output_path(args.output),
                receipt,
                Path(envelope["canonical"]["project_root"]),
            )
        elif args.operation == "approve":
            envelope = _read_json(args.envelope, "coverage envelope")
            receipt = _read_json(args.receipt, "attestation receipt")
            approval = approve(envelope, receipt)
            _write_json(
                _output_path(args.output),
                approval,
                Path(envelope["canonical"]["project_root"]),
            )
            if approval["mode"] == "OPEN":
                return 2
        else:
            old = _read_json(args.old, "old coverage envelope")
            new = _read_json(args.new, "new coverage envelope")
            result = diff(old, new)
            project_root = Path(new["canonical"]["project_root"])
            _write_json(_output_path(args.output), result, project_root)
    except (GateError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
