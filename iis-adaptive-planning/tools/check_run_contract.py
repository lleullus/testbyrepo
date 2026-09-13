#!/usr/bin/env python3
"""Check deterministic structural consistency of one Adaptive Run Contract."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


STATUSES = frozenset({"CLOSED", "USER_INPUT_REQUIRED"})
REQUIRED_ITEM_POLICIES = frozenset({"EXACT_REQUIRED_SET", "REQUIRED_FLOOR", "NONE_REQUIRED"})
RUN_COMPLETION_BOUNDARIES = frozenset(
    {
        "READY_TICKET_SET",
        "READY_EXECUTION_PLANS",
        "CURRENT_INCREMENT_IMPLEMENTED",
        "CURRENT_INCREMENT_DELIVERED",
        "NAMED_REQUIRED_ITEMS_DELIVERED",
        "BOUNDED_OUTCOME_SATISFIED",
        "MANDATE_OUTCOME_SATISFIED",
    }
)
APPROVAL_GATES = frozenset({"required", "not_required"})
TOP_FIELDS = ("Status", "Project-Root", "Mandate", "Run Contract Approval Gate")
REQUIRED_SECTIONS = (
    "Goal Outcome",
    "Required Named Items",
    "Candidate Named Items",
    "Required Item Policy",
    "Delivery Stages",
    "Delivery Model Selection",
    "Run Completion Boundary",
    "Completion Predicate",
    "Authoritative Readback",
    "Source Authority",
    "Unresolved Field",
)
IMPLEMENTATION_MODES = frozenset({"SUBAGENT", "DIRECT", "disabled"})
VERIFICATION_MODES = frozenset({"SUBAGENT", "disabled"})

Line = tuple[int, str]
Section = tuple[int, list[Line]]
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_ITEM = re.compile(r"^\s*-\s+(.+?)\s*$")


@dataclass(frozen=True)
class Diagnostic:
    field: str
    line: int
    message: str


@dataclass(frozen=True)
class _ModelRow:
    line: int
    mode: str
    selection: str
    basis: str


def _unresolved(value: str) -> bool:
    return value.startswith("<") or value.lower() in {"unresolved", "not selected"}


class _Checker:
    def __init__(self, text: str) -> None:
        self.diagnostics: list[Diagnostic] = []
        self.top, raw_sections = self._document(text)
        self.sections = {
            name: self._one_section(raw_sections, name) for name in REQUIRED_SECTIONS
        }

    def add(self, field: str, line: int, message: str) -> None:
        self.diagnostics.append(Diagnostic(field, line, message))

    def _document(self, text: str) -> tuple[list[Line], dict[str, list[Section]]]:
        visible: list[Line] = []
        fence: tuple[str, int, int] | None = None
        for number, line in enumerate(text.splitlines(), 1):
            marker_match = _FENCE.match(line)
            if fence:
                if marker_match:
                    marker = marker_match.group(1)
                    if marker[0] == fence[0] and len(marker) >= fence[1]:
                        fence = None
                continue
            if marker_match:
                marker = marker_match.group(1)
                fence = (marker[0], len(marker), number)
            else:
                visible.append((number, line))
        if fence:
            self.add("Markdown", fence[2], "fenced block is not closed")

        top: list[Line] = []
        sections: dict[str, list[Section]] = {}
        current: Section | None = None
        for number, line in visible:
            heading = _HEADING.match(line)
            if heading and len(heading.group(1)) == 2:
                name = heading.group(2).strip().rstrip("#").rstrip()
                current = (number, [])
                sections.setdefault(name, []).append(current)
            elif current:
                current[1].append((number, line))
            else:
                top.append((number, line))
        sections.pop("Notes", None)
        return top, sections

    def _one_section(
        self, sections: dict[str, list[Section]], name: str
    ) -> Section | None:
        found = sections.get(name, [])
        if not found:
            self.add(name, 0, "required section is missing")
            return None
        if len(found) > 1:
            for number, _ in found[1:]:
                self.add(name, number, "section appears more than once")
            return None
        return found[0]

    def field(self, lines: list[Line], name: str) -> Line | None:
        pattern = re.compile(rf"^\s*{re.escape(name)}:\s*(.*?)\s*$")
        found = [
            (number, match.group(1))
            for number, line in lines
            if (match := pattern.match(line))
        ]
        if not found:
            self.add(name, 0, "required field is missing")
            return None
        if len(found) > 1:
            for number, _ in found[1:]:
                self.add(name, number, "field appears more than once")
            return None
        if not found[0][1]:
            self.add(name, found[0][0], "field value is empty")
            return None
        return found[0]

    def scalar(self, name: str) -> Line | None:
        section = self.sections[name]
        if not section:
            return None
        values = [(number, line.strip()) for number, line in section[1] if line.strip()]
        if not values:
            self.add(name, section[0], "section value is empty")
            return None
        if len(values) > 1:
            for number, _ in values[1:]:
                self.add(name, number, "section must contain one value")
            return None
        return values[0]

    def enum(
        self,
        entry: Line | None,
        name: str,
        allowed: frozenset[str],
        status: str | None,
    ) -> str | None:
        if not entry:
            return None
        number, value = entry
        if value in allowed:
            return value
        if status == "USER_INPUT_REQUIRED" and _unresolved(value):
            return None
        self.add(name, number, f"unknown value '{value}'")
        return None

    def items(
        self, name: str, sentinel: str, status: str | None
    ) -> list[Line] | None:
        section = self.sections[name]
        if not section:
            return None
        content = [(number, line.strip()) for number, line in section[1] if line.strip()]
        if len(content) == 1 and content[0][1].startswith("From source:"):
            number, reference = content[0]
            if not re.fullmatch(r"From source: /[^\n#<>]+#[^\n<>]+", reference):
                self.add(name, number, "source reference requires an absolute path and exact section")
                return None
            return content
        if status == "USER_INPUT_REQUIRED" and len(content) == 1 and _unresolved(content[0][1]):
            return None
        sentinels = [number for number, line in content if line == sentinel]
        items: list[Line] = []
        invalid: list[int] = []
        for number, line in content:
            match = _ITEM.match(line)
            if match:
                items.append((number, re.sub(r"\s+", " ", match.group(1).strip())))
            elif line != sentinel:
                invalid.append(number)
        for number in invalid:
            self.add(name, number, f"expected list item or exact '{sentinel}'")
        for number in sentinels[1:]:
            self.add(name, number, "sentinel appears more than once")
        if sentinels and items:
            self.add(name, sentinels[0], "sentinel cannot accompany list items")
        if not content:
            self.add(name, section[0], "named-item selection is empty")
        if invalid or len(sentinels) > 1 or (sentinels and items) or not content:
            return None
        return items

    def model_rows(self) -> dict[str, _ModelRow]:
        found: dict[str, list[_ModelRow]] = {"Implementation": [], "Verification": []}
        section = self.sections["Delivery Model Selection"]
        for number, line in section[1] if section else []:
            stripped = line.strip()
            if not (stripped.startswith("|") and stripped.endswith("|")):
                continue
            cells = [cell.strip() for cell in stripped[1:-1].split("|")]
            if len(cells) == 4 and cells[0] in found:
                found[cells[0]].append(_ModelRow(number, cells[1], cells[2], cells[3]))
        rows: dict[str, _ModelRow] = {}
        for stage, candidates in found.items():
            if not candidates:
                self.add("Delivery Model Selection", 0, f"{stage} row is missing")
            elif len(candidates) > 1:
                for row in candidates[1:]:
                    self.add(stage, row.line, "model row appears more than once")
            else:
                rows[stage] = candidates[0]
        return rows

    def check(self) -> list[Diagnostic]:
        top = {name: self.field(self.top, name) for name in TOP_FIELDS}
        status = self.enum(top["Status"], "Status", STATUSES, None)
        self.enum(
            top["Run Contract Approval Gate"],
            "Run Contract Approval Gate",
            APPROVAL_GATES,
            status,
        )
        for name in ("Project-Root", "Mandate"):
            if top[name] and _unresolved(top[name][1]) and status != "USER_INPUT_REQUIRED":
                self.add(name, top[name][0], "field is unresolved")

        policy_entry = self.scalar("Required Item Policy")
        policy = self.enum(
            policy_entry, "Required Item Policy", REQUIRED_ITEM_POLICIES, status
        )
        boundary_entry = self.scalar("Run Completion Boundary")
        boundary = self.enum(
            boundary_entry,
            "Run Completion Boundary",
            RUN_COMPLETION_BOUNDARIES,
            status,
        )
        required = self.items("Required Named Items", "None required", status)
        candidate = self.items("Candidate Named Items", "None named", status)
        if policy in {"EXACT_REQUIRED_SET", "REQUIRED_FLOOR"} and required == []:
            self.add(
                "Required Item Policy",
                policy_entry[0],
                f"{policy} requires Required Named Items",
            )
        if policy == "NONE_REQUIRED" and required not in (None, []):
            self.add(
                "Required Item Policy",
                policy_entry[0],
                "NONE_REQUIRED requires exact 'None required'",
            )
        if required is not None and candidate is not None:
            candidate_values = {value for _, value in candidate}
            for number, value in required:
                if value in candidate_values:
                    self.add(
                        "Required Named Items",
                        number,
                        f"item also appears in Candidate Named Items: {value}",
                    )

        stage_section = self.sections["Delivery Stages"]
        stages = {
            name: self.field(stage_section[1], name) if stage_section else None
            for name in ("Implementation", "Verification")
        }
        switches = {
            name: self.enum(stages[name], name, frozenset({"yes", "no"}), status)
            for name in stages
        }
        implementation, verification = switches["Implementation"], switches["Verification"]
        model_rows = self.model_rows()

        for stage, allowed in (
            ("Implementation", IMPLEMENTATION_MODES),
            ("Verification", VERIFICATION_MODES),
        ):
            row = model_rows.get(stage)
            if not row:
                continue
            if row.mode not in allowed and not (
                status == "USER_INPUT_REQUIRED" and _unresolved(row.mode)
            ):
                self.add(stage, row.line, f"unknown execution mode '{row.mode}'")
            switch = switches[stage]
            expected = (
                {"SUBAGENT", "DIRECT"}
                if stage == "Implementation" and switch == "yes"
                else {"SUBAGENT"}
                if stage == "Verification" and switch == "yes"
                else {"disabled"}
                if switch == "no"
                else set()
            )
            if expected and row.mode not in expected:
                self.add(
                    stage,
                    row.line,
                    f"stage switch '{switch}' conflicts with mode '{row.mode}'",
                )
            if status == "CLOSED" and row.mode == "SUBAGENT":
                if (
                    not row.selection.strip()
                    or _unresolved(row.selection)
                    or row.selection.lower() == "not applicable"
                ):
                    self.add(stage, row.line, "CLOSED SUBAGENT stage requires selected model/effort")
                if (
                    not row.basis.strip()
                    or _unresolved(row.basis)
                    or row.basis.lower() == "not applicable"
                ):
                    self.add(stage, row.line, "CLOSED SUBAGENT stage requires user-selection basis")

        if boundary in {"READY_TICKET_SET", "READY_EXECUTION_PLANS"}:
            if None not in (implementation, verification) and (implementation, verification) != ("no", "no"):
                self.add("Run Completion Boundary", boundary_entry[0], f"{boundary} requires no/no stages")
        elif boundary == "CURRENT_INCREMENT_IMPLEMENTED":
            if None not in (implementation, verification) and (implementation, verification) != ("yes", "no"):
                self.add(
                    "Run Completion Boundary",
                    boundary_entry[0],
                    "CURRENT_INCREMENT_IMPLEMENTED requires yes/no stages",
                )
        elif boundary in {"CURRENT_INCREMENT_DELIVERED", "NAMED_REQUIRED_ITEMS_DELIVERED"}:
            if verification is not None and verification != "yes":
                self.add("Run Completion Boundary", boundary_entry[0], f"{boundary} requires Verification yes")
            if boundary == "NAMED_REQUIRED_ITEMS_DELIVERED" and required == []:
                self.add("Run Completion Boundary", boundary_entry[0], f"{boundary} requires Required Named Items")

        unresolved = self.scalar("Unresolved Field")
        if status == "CLOSED" and unresolved and unresolved[1] != "None":
            self.add("Unresolved Field", unresolved[0], "CLOSED requires exact 'None'")
        if status == "USER_INPUT_REQUIRED" and unresolved and unresolved[1] == "None":
            self.add("Unresolved Field", unresolved[0], "USER_INPUT_REQUIRED requires an unresolved field")
        if status == "CLOSED":
            for name in ("Goal Outcome", "Completion Predicate", "Authoritative Readback", "Source Authority"):
                section = self.sections[name]
                content = [] if not section else [line.strip() for _, line in section[1] if line.strip()]
                if not content or all(_unresolved(value) for value in content):
                    self.add(name, section[0] if section else 0, "CLOSED requires a resolved value")

        return sorted(
            self.diagnostics,
            key=lambda item: (item.line == 0, item.line, item.field, item.message),
        )



def check_run_contract(text: str) -> list[Diagnostic]:
    """Return structure diagnostics without reading or writing external state."""

    return _Checker(text).check()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check one Adaptive Run Contract's deterministic structure."
    )
    parser.add_argument("--file", type=Path, help="read this exact path instead of stdin")
    args = parser.parse_args(argv)
    try:
        text = args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()
    except (OSError, UnicodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    if not text.strip():
        print("INPUT_ERROR: Run Contract input is empty", file=sys.stderr)
        return 2

    diagnostics = check_run_contract(text)
    if not diagnostics:
        print("STRUCTURE_VALID")
        return 0
    print("STRUCTURE_INVALID")
    for diagnostic in diagnostics:
        print(f"field={diagnostic.field} line={diagnostic.line} message={diagnostic.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
