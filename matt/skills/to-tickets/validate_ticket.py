#!/usr/bin/env python3
"""Validate the structural contract of one IIS Ticket."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CORE_LABELS = (
    "Parent outcome ordinal",
    "AC ordinals",
    "Behavior authority ordinals",
    "Initial state",
    "Trigger or inspection target",
    "Acceptance boundary",
    "Expected observable result",
    "Authoritative readback",
    "Decision boundary",
    "Disposition",
    "Independent verification required",
    "Acceptance surface",
    "External condition",
)
SPEC_CORE_LABELS = (
    "Outcome",
    "Acceptance boundary",
    "Trigger or inspection target",
    "Expected observable result",
    "Authoritative readback",
    "Disposition",
    "Independent verification required",
    "Acceptance surface",
    "External condition",
)
OPTIONAL_LABELS = frozenset(
    {
        "Absence terminal condition",
        "Ordering event source and range",
        "Persistence storage identity and lifecycle boundary",
        "Interruption checkpoint",
        "External effect sandbox, authority, cleanup, and readback",
        "UI rendered state and interaction readback",
    }
)
DISPOSITIONS = {
    "Independent",
    "Operator-assisted",
    "Not independently verifiable",
}
SURFACE_PREFIXES = {
    "Existing",
    "Ticket Scope creates",
    "Delivery contract guarantees",
    "Operator-owned",
    "None",
}
STATUS_RE = re.compile(r"(?m)^Status: ([^\n]+)$")
PARENT_RE = re.compile(r"(?m)^Parent-Spec: ([^\n]+)$")
PROJECT_RE = re.compile(r"(?m)^Project-Root: ([^\n]+)$")
WORK_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TICKET_NAME_RE = re.compile(r"^TICKET-[0-9]{3}\.md$")


class TicketValidationError(RuntimeError):
    pass


def _single_match(pattern: re.Pattern[str], text: str, label: str) -> str:
    values = pattern.findall(text)
    if len(values) != 1:
        raise TicketValidationError(f"{label} must occur exactly once")
    return values[0].strip()


def _section(text: str, heading: str) -> str:
    matches = list(re.finditer(rf"(?m)^## {re.escape(heading)}\s*$", text))
    if len(matches) != 1:
        raise TicketValidationError(f"section must occur exactly once: {heading}")
    start = matches[0].end()
    next_heading = re.search(r"(?m)^## ", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def _top_level_items(body: str, label: str) -> list[str]:
    items: list[list[str]] = []
    for line in body.splitlines():
        if line.startswith("- "):
            items.append([line[2:]])
        elif line.startswith("  ") and items and line.strip():
            items[-1].append(line[2:])
        elif line.strip():
            raise TicketValidationError(f"{label} has non-item top-level content")
    if not items:
        raise TicketValidationError(f"{label} must contain at least one item")
    return ["\n".join(lines) for lines in items]


def _behavior_authority_identity(item: str, project: Path) -> tuple[Path, str]:
    marker = " | Scope: "
    if item.count(marker) != 1:
        raise TicketValidationError("Behavior Authority item must contain exactly one ' | Scope: '")
    raw_path, scope = item.split(marker, 1)
    raw_path = raw_path.strip()
    scope = scope.strip()
    if not raw_path or not scope:
        raise TicketValidationError("Behavior Authority path and Scope must be non-empty")
    relative = Path(raw_path)
    if relative.is_absolute():
        raise TicketValidationError("Behavior Authority path must be project-relative")
    target = (project / relative).resolve(strict=False)
    allowed_parents = {
        (project / "docs/planning/behavior/contexts").resolve(strict=False),
        (project / "docs/planning/behavior/lifecycles").resolve(strict=False),
        (project / "docs/planning/behavior/invariants").resolve(strict=False),
    }
    if target.parent not in allowed_parents:
        raise TicketValidationError(
            "Behavior Authority must resolve from Project-Root to a canonical behavior authority directory"
        )
    return target, scope


def _labeled_item(item: str, labels: tuple[str, ...], item_label: str) -> dict[str, str]:
    lines = item.splitlines()
    values: dict[str, str] = {}
    for index, line in enumerate(lines):
        if ": " not in line:
            raise TicketValidationError(f"{item_label} has an unlabeled line")
        label, value = line.split(": ", 1)
        if label in values:
            raise TicketValidationError(f"{item_label} repeats label: {label}")
        if label not in labels and label not in OPTIONAL_LABELS:
            raise TicketValidationError(f"{item_label} has unknown label: {label}")
        if not value.strip() or "<" in value or ">" in value:
            raise TicketValidationError(f"{item_label} has an unresolved value: {label}")
        if index < len(labels) and label != labels[index]:
            raise TicketValidationError(f"{item_label} core labels are out of order")
        values[label] = value.strip()
    if tuple(lines[index].split(": ", 1)[0] for index in range(min(len(lines), len(labels)))) != labels:
        raise TicketValidationError(f"{item_label} is missing a core label")
    if any(label not in values for label in labels):
        raise TicketValidationError(f"{item_label} is missing a core label")
    return values


def _surface(value: str) -> tuple[str, str]:
    if " | " not in value:
        raise TicketValidationError("Acceptance surface must use `<kind> | <detail>`")
    kind, detail = value.split(" | ", 1)
    if kind not in SURFACE_PREFIXES or not detail.strip():
        raise TicketValidationError("Acceptance surface kind or detail is invalid")
    return kind, detail.strip()


def _validate_combination(values: dict[str, str], label: str) -> None:
    disposition = values["Disposition"]
    required = values["Independent verification required"]
    surface_kind, _detail = _surface(values["Acceptance surface"])
    external = values["External condition"]
    if disposition not in DISPOSITIONS:
        raise TicketValidationError(f"{label} disposition is invalid")
    if required not in {"yes", "no"}:
        raise TicketValidationError(f"{label} independent requirement is invalid")
    if required == "yes" and disposition != "Independent":
        raise TicketValidationError(f"{label} requires independent verification but is non-independent")
    if disposition == "Independent" and surface_kind not in {
        "Existing",
        "Ticket Scope creates",
        "Delivery contract guarantees",
    }:
        raise TicketValidationError(f"{label} Independent surface is invalid")
    if disposition == "Independent" and any(
        values[field].startswith("Not available")
        for field in (
            "Acceptance boundary",
            "Trigger or inspection target",
            "Authoritative readback",
        )
    ):
        raise TicketValidationError(f"{label} Independent observation field is Not available")
    if disposition == "Operator-assisted":
        if surface_kind != "Operator-owned" or external == "None":
            raise TicketValidationError(f"{label} Operator-assisted path is incomplete")
    if disposition == "Not independently verifiable" and surface_kind != "None":
        raise TicketValidationError(f"{label} non-verifiable surface must be None")


def _resolve_parent(ticket: Path, raw: str, expected: Path) -> Path:
    candidates = [part.strip() for part in raw.split(" | ") if part.strip()]
    if not candidates or len(candidates) > 2:
        raise TicketValidationError("Parent-Spec must contain one path or matching relative and absolute paths")
    resolved_candidates: list[Path] = []
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = ticket.parent / path
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise TicketValidationError("Parent-Spec does not resolve to a readable file") from exc
        if path.is_symlink() or not resolved.is_file() or resolved != expected:
            raise TicketValidationError("Parent-Spec must resolve to the exact sibling work SPEC.md")
        resolved_candidates.append(resolved)
    if any(resolved != expected for resolved in resolved_candidates):
        raise TicketValidationError("Parent-Spec paths do not identify the same sibling work SPEC.md")
    return expected


def _validate_blockers(ticket: Path, body: str, ready: bool) -> None:
    if body == "None":
        return
    for item in _top_level_items(body, "Blockers"):
        if "\n" in item or not item.endswith(".md"):
            raise TicketValidationError("Blockers must contain path-only Markdown items")
        relative = Path(item)
        if relative.is_absolute():
            raise TicketValidationError("Blockers must contain local Markdown paths")
        raw_target = ticket.parent / relative
        try:
            target = raw_target.resolve(strict=True)
            mode = raw_target.lstat().st_mode
            work = ticket.parent.parent
            if raw_target.is_symlink() or target == work or work not in target.parents:
                raise TicketValidationError("blocker must remain a raw local path inside the Ticket work")
            if not target.is_file() or target.suffix != ".md" or mode == 0:
                raise TicketValidationError("blocker must be a regular Markdown file")
            text = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise TicketValidationError(f"blocker is unreadable: {item}") from exc
        status = _single_match(STATUS_RE, text, f"blocker Status ({item})")
        if ready and status not in {"resolved", "done"}:
            raise TicketValidationError(f"ready Ticket has unresolved blocker: {item}")


def validate(ticket_path: str | Path) -> None:
    raw_ticket = Path(ticket_path).expanduser()
    if not raw_ticket.is_absolute():
        raise TicketValidationError("Ticket path must be absolute and canonical")
    try:
        ticket = raw_ticket.resolve(strict=True)
        text = ticket.read_text(encoding="utf-8")
    except OSError as exc:
        raise TicketValidationError(f"Ticket is unreadable: {raw_ticket}") from exc
    if raw_ticket != ticket or raw_ticket.is_symlink() or not ticket.is_file():
        raise TicketValidationError("Ticket must be an absolute canonical raw regular file path")

    status = _single_match(STATUS_RE, text, "Ticket Status")
    if status not in {"draft", "ready", "blocked", "done"}:
        raise TicketValidationError("Ticket Status is invalid")
    project_raw = _single_match(PROJECT_RE, text, "Project-Root")
    try:
        project = Path(project_raw).resolve(strict=True)
    except OSError as exc:
        raise TicketValidationError("Project-Root is inaccessible") from exc
    if not project.is_dir() or project_raw != str(project):
        raise TicketValidationError("Project-Root must be an existing canonical directory")
    work_container = project / "docs" / "planning" / "work"
    work = ticket.parent.parent
    if (
        ticket.parent.name != "tickets"
        or work.parent != work_container
        or not WORK_SLUG_RE.fullmatch(work.name)
        or not TICKET_NAME_RE.fullmatch(ticket.name)
    ):
        raise TicketValidationError(
            "Ticket must be canonical Project-Root/docs/planning/work/<work-slug>/tickets/TICKET-NNN.md"
        )

    expected_parent = work / "SPEC.md"
    parent = _resolve_parent(
        ticket,
        _single_match(PARENT_RE, text, "Parent-Spec"),
        expected_parent.resolve(strict=True),
    )
    parent_text = parent.read_text(encoding="utf-8")
    if _single_match(STATUS_RE, parent_text, "Parent Spec Status") != "approved":
        raise TicketValidationError("Parent Spec must be approved")

    ac_items = _top_level_items(_section(text, "Acceptance Criteria"), "Acceptance Criteria")
    flow_items = _top_level_items(_section(text, "Verification"), "Verification")
    ticket_behavior_items = _top_level_items(
        _section(text, "Behavior Authorities"), "Behavior Authorities"
    )
    spec_items = _top_level_items(
        _section(parent_text, "Verification Expectations"), "Verification Expectations"
    )
    parent_behavior_items = _top_level_items(
        _section(parent_text, "Behavior Authorities"), "Behavior Authorities"
    )
    spec_values = [
        _labeled_item(item, SPEC_CORE_LABELS, f"Spec outcome {index}")
        for index, item in enumerate(spec_items, 1)
    ]
    for index, values in enumerate(spec_values, 1):
        _validate_combination(values, f"Spec outcome {index}")
    parent_behavior_identities = {
        _behavior_authority_identity(item, project) for item in parent_behavior_items
    }
    for item in ticket_behavior_items:
        if _behavior_authority_identity(item, project) not in parent_behavior_identities:
            raise TicketValidationError("Ticket Behavior Authority is absent from Parent Spec")

    scope = _section(text, "Scope")
    covered_ac: set[int] = set()
    covered_behavior: set[int] = set()
    for index, item in enumerate(flow_items, 1):
        values = _labeled_item(item, CORE_LABELS, f"Verification flow {index}")
        _validate_combination(values, f"Verification flow {index}")

        parent_raw = values["Parent outcome ordinal"]
        if not parent_raw.isdigit() or int(parent_raw) < 1:
            raise TicketValidationError(f"Verification flow {index} has invalid Parent outcome ordinal")
        parent_ordinal = int(parent_raw)
        if parent_ordinal > len(spec_values):
            raise TicketValidationError(f"Verification flow {index} references an unknown Parent outcome ordinal")
        parent_values = spec_values[parent_ordinal - 1]

        ordinal_parts = [part.strip() for part in values["AC ordinals"].split(",")]
        if any(not part.isdigit() or int(part) < 1 for part in ordinal_parts):
            raise TicketValidationError(f"Verification flow {index} has invalid AC ordinals")
        ordinals = [int(part) for part in ordinal_parts]
        if len(ordinals) != len(set(ordinals)) or ordinals != sorted(ordinals):
            raise TicketValidationError(f"Verification flow {index} AC ordinals must be unique and ordered")
        if any(ordinal > len(ac_items) for ordinal in ordinals):
            raise TicketValidationError(f"Verification flow {index} references an unknown AC ordinal")
        covered_ac.update(ordinals)

        behavior_raw = values["Behavior authority ordinals"]
        if behavior_raw == "None":
            behavior_ordinals: list[int] = []
        else:
            behavior_parts = [part.strip() for part in behavior_raw.split(",")]
            if any(not part.isdigit() or int(part) < 1 for part in behavior_parts):
                raise TicketValidationError(
                    f"Verification flow {index} has invalid Behavior authority ordinals"
                )
            behavior_ordinals = [int(part) for part in behavior_parts]
            if (
                len(behavior_ordinals) != len(set(behavior_ordinals))
                or behavior_ordinals != sorted(behavior_ordinals)
            ):
                raise TicketValidationError(
                    f"Verification flow {index} Behavior authority ordinals must be unique and ordered"
                )
            if any(ordinal > len(ticket_behavior_items) for ordinal in behavior_ordinals):
                raise TicketValidationError(
                    f"Verification flow {index} references an unknown Behavior authority ordinal"
                )
        covered_behavior.update(behavior_ordinals)

        combination = (
            values["Disposition"],
            values["Independent verification required"],
            values["Acceptance surface"],
            values["External condition"],
        )
        parent_combination = (
            parent_values["Disposition"],
            parent_values["Independent verification required"],
            parent_values["Acceptance surface"],
            parent_values["External condition"],
        )
        if combination != parent_combination:
            raise TicketValidationError(
                f"Verification flow {index} combination differs from mapped Parent Spec outcome"
            )
        surface_kind, surface_detail = _surface(values["Acceptance surface"])
        if surface_kind == "Ticket Scope creates" and surface_detail not in scope:
            raise TicketValidationError(f"Verification flow {index} Scope does not own its acceptance surface")
        flow_optional = {
            (label, values[label]) for label in OPTIONAL_LABELS if label in values
        }
        parent_optional = {
            (label, parent_values[label]) for label in OPTIONAL_LABELS if label in parent_values
        }
        if flow_optional != parent_optional:
            raise TicketValidationError(
                f"Verification flow {index} conditional boundary differs from mapped Parent Spec outcome"
            )

    if covered_ac != set(range(1, len(ac_items) + 1)):
        raise TicketValidationError("Acceptance Criteria and Verification flows do not close bidirectionally")
    if covered_behavior != set(range(1, len(ticket_behavior_items) + 1)):
        raise TicketValidationError(
            "Behavior Authorities and Verification flows do not close bidirectionally"
        )
    _validate_blockers(ticket, _section(text, "Blockers"), status == "ready")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticket")
    args = parser.parse_args(argv)
    try:
        validate(args.ticket)
    except TicketValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
