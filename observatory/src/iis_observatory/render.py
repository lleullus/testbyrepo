from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from shutil import get_terminal_size
from typing import Iterable
import re
import unicodedata

from .model import Health, NextWorkKind, ProjectState

ANSI = re.compile(r"\x1b\[[0-9;]*m")
HEALTH_COLORS = {
    Health.READY: "\033[32m",
    Health.PLANNING: "\033[36m",
    Health.NEEDS_SCOPE: "\033[34m",
    Health.BLOCKED: "\033[31m",
    Health.INCONSISTENT: "\033[35m",
    Health.COMPLETE: "\033[32m",
    Health.STALE: "\033[33m",
    Health.NO_IIS: "\033[90m",
}
RESET = "\033[0m"

STAGE_LABELS = {
    "ko": {
        "delivery": "Delivery",
        "tickets": "Tickets",
        "planning": "Planning",
        "shaping": "Shaping",
        "complete": "Complete",
        "unknown": "Unknown",
    },
    "en": {
        "delivery": "Delivery",
        "tickets": "Tickets",
        "planning": "Planning",
        "shaping": "Shaping",
        "complete": "Complete",
        "unknown": "Unknown",
    },
}


def _health_label(health: Health) -> str:
    return health.value.replace("_", " ")


def _paint(value: str, health: Health, color: bool) -> str:
    if not color:
        return value
    return f"{HEALTH_COLORS.get(health, '')}{value}{RESET}"


def _char_width(character: str) -> int:
    if unicodedata.combining(character):
        return 0
    return 2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1


def _visible_len(value: str) -> int:
    return sum(_char_width(character) for character in ANSI.sub("", value))


def _truncate(value: str, width: int) -> str:
    if width <= 0:
        return ""
    plain = ANSI.sub("", value)
    if _visible_len(plain) <= width:
        return value
    if width == 1:
        return "…"
    result: list[str] = []
    used = 0
    target = width - 1
    for character in plain:
        char_width = _char_width(character)
        if used + char_width > target:
            break
        result.append(character)
        used += char_width
    return "".join(result) + "…"


def _pad(value: str, width: int) -> str:
    return value + " " * max(0, width - _visible_len(value))


def _current_position(state: ProjectState, lang: str) -> str:
    stage = STAGE_LABELS.get(lang, STAGE_LABELS["ko"])[state.stage.value]
    if state.current_increment and state.current_increment.identifier:
        return f"{state.current_increment.identifier} / {stage}"
    if state.current_work_package and state.current_work_package.identifier:
        return f"{state.current_work_package.identifier} / {stage}"
    if state.current_work_slug:
        return f"{state.current_work_slug} / {stage}"
    if state.current_scope:
        return f"Scope / {stage}"
    return stage


def _current_unit(state: ProjectState) -> str:
    if state.current_increment and state.current_increment.identifier:
        return _authored_unit_label(state.current_increment.identifier, state.current_increment.title)
    if state.current_work_package and state.current_work_package.identifier:
        return _authored_unit_label(state.current_work_package.identifier, state.current_work_package.title)
    if state.current_spec is not None:
        title = (state.current_spec.title or state.current_work_slug or "").strip()
        return f"work · {title}" if title else "work"
    if state.current_work_slug:
        return f"work · {state.current_work_slug}"
    if state.current_scope:
        title = (state.current_scope.title or "").strip()
        return f"Scope · {title}" if title else "Scope"
    return "—"


def _authored_unit_label(identifier: str, title: str | None) -> str:
    """Combine a stable planning ID with its authored heading without inventing a summary."""
    clean = (title or "").strip()
    if not clean:
        return identifier
    clean = re.sub(rf"(?i)^\s*{re.escape(identifier)}\s*[:\-]?\s*", "", clean).strip()
    if not clean or clean.lower() in {"increment", "work package", "work-package"}:
        return identifier
    return f"{identifier} · {clean}"


def _tickets_label(state: ProjectState, lang: str) -> str:
    counts = state.ticket_counts
    if counts["total"] == 0:
        return "—"
    return f"{counts['done']}/{counts['total']}"


def _next_label(state: ProjectState, lang: str) -> str:
    work = state.next_work
    target = work.target_id or ""
    if work.kind == NextWorkKind.SCOPE_SHAPER and state.health == Health.COMPLETE and state.next_candidate_work_packages:
        return "Select next Increment" if lang == "en" else "다음 Increment 선택"
    if lang == "en":
        labels = {
            NextWorkKind.TICKET_IMPLEMENT: f"Implement {target}",
            NextWorkKind.TICKET_UNBLOCK: f"Unblock {target}",
            NextWorkKind.TICKET_REVIEW: f"Ready review {target}",
            NextWorkKind.TO_TICKETS: "To Tickets",
            NextWorkKind.TO_SPEC: "To Spec",
            NextWorkKind.ASK_MATT: "Ask Matt",
            NextWorkKind.SCOPE_SHAPER: "Scope Shaper",
            NextWorkKind.CONSISTENCY_CHECK: "Check consistency",
            NextWorkKind.NONE: "No next unit",
        }
    else:
        labels = {
            NextWorkKind.TICKET_IMPLEMENT: f"{target} 구현",
            NextWorkKind.TICKET_UNBLOCK: f"{target} blocker 해소",
            NextWorkKind.TICKET_REVIEW: f"{target} Ready 전환",
            NextWorkKind.TO_TICKETS: "To Tickets",
            NextWorkKind.TO_SPEC: "To Spec",
            NextWorkKind.ASK_MATT: "Ask Matt",
            NextWorkKind.SCOPE_SHAPER: "Scope Shaper",
            NextWorkKind.CONSISTENCY_CHECK: "정합성 확인",
            NextWorkKind.NONE: "다음 단위 없음",
        }
    return labels[work.kind].strip()


def _overview_next_label(state: ProjectState, lang: str) -> str:
    if state.health == Health.COMPLETE and state.next_candidate_work_packages:
        identifiers = ", ".join(
            item.identifier or Path(item.relative_path).stem
            for item in state.next_candidate_work_packages
        )
        return f"Scope Shaper [{identifiers}]"
    if state.next_work.kind == NextWorkKind.NONE:
        return "—"
    return _next_label(state, lang)


def render_overview(
    states: Iterable[ProjectState],
    *,
    lang: str = "ko",
    color: bool = False,
    terminal_width: int | None = None,
) -> str:
    states = list(states)
    title = "IIS PROJECT OVERVIEW"
    if not states:
        empty = "IIS planning artifacts를 가진 저장소를 찾지 못했습니다." if lang == "ko" else "No repositories with IIS planning artifacts were found."
        return f"{title}\n{'─' * len(title)}\n{empty}\n"

    rows = [
        [
            state.repository,
            _current_unit(state),
            _tickets_label(state, lang),
            _paint(_health_label(state.health), state.health, color),
            _overview_next_label(state, lang),
        ]
        for state in states
    ]
    headers = ["Repository", "Unit", "Tkts", "State", "Next"]
    natural_widths = [
        max(_visible_len(headers[index]), max(_visible_len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    max_width = terminal_width or get_terminal_size((120, 30)).columns
    max_width = max(80, min(max_width, 180))
    separators = 3 * (len(headers) - 1)
    available = max_width - separators
    caps = [30, 42, 7, 12, 36]
    mins = [14, 13, 4, 12, 29]
    widths = [min(natural_widths[index], caps[index]) for index in range(len(headers))]
    while sum(widths) > available:
        changed = False
        for index in (0, 1, 4, 2):
            if widths[index] > mins[index] and sum(widths) > available:
                widths[index] -= 1
                changed = True
        if not changed:
            break

    rule = "─" * min(max_width, sum(widths) + separators)
    output = [title, rule]
    output.append("   ".join(_pad(_truncate(headers[index], widths[index]), widths[index]) for index in range(len(headers))))
    output.append(rule)
    for row in rows:
        output.append("   ".join(_pad(_truncate(row[index], widths[index]), widths[index]) for index in range(len(headers))))
    output.append(rule)

    counts = Counter(state.health for state in states)
    summary_items = [
        ("Ready", counts[Health.READY]),
        ("Blocked", counts[Health.BLOCKED]),
        ("Planning", counts[Health.PLANNING] + counts[Health.NEEDS_SCOPE]),
        ("Inconsistent", counts[Health.INCONSISTENT]),
        ("Complete", counts[Health.COMPLETE]),
    ]
    output.append("   ".join(f"{label} {count}" for label, count in summary_items))
    return "\n".join(output) + "\n"


def render_overview_markdown(states: Iterable[ProjectState], *, lang: str = "ko") -> str:
    states = list(states)
    lines = [
        "# IIS Project Overview",
        "",
        "| Repository | Unit | Tickets | State | Next |",
        "|---|---|---:|---|---|",
    ]
    for state in states:
        values = (
            state.repository,
            _current_unit(state),
            _tickets_label(state, lang),
            _health_label(state.health),
            _overview_next_label(state, lang),
        )
        escaped = [value.replace("|", "\\|") for value in values]
        lines.append("| " + " | ".join(escaped) + " |")
    lines.append("")
    counts = Counter(state.health for state in states)
    lines.append(
        f"Ready for delivery **{counts[Health.READY]}** · "
        f"Blocked **{counts[Health.BLOCKED]}** · "
        f"Needs planning **{counts[Health.PLANNING] + counts[Health.NEEDS_SCOPE]}** · "
        f"Inconsistent **{counts[Health.INCONSISTENT]}** · "
        f"Complete **{counts[Health.COMPLETE]}**"
    )
    lines.append("")
    return "\n".join(lines)


def render_state(state: ProjectState, *, lang: str = "ko", color: bool = False) -> str:
    completed = ", ".join(ticket.identifier or ticket.relative_path for ticket in state.completed_tickets) or "None"
    remaining = ", ".join(
        f"{ticket.identifier or ticket.relative_path} ({ticket.status or 'missing'})"
        for ticket in state.remaining_tickets
    ) or "None"
    health = _paint(_health_label(state.health), state.health, color)
    lines = [
        "IIS CURRENT PLANNING STATE",
        f"Repository: {state.repository} ({state.repository_path})",
        f"Current Scope: {_artifact_label(state.current_scope)}",
        f"Current Work Package: {_artifact_label(state.current_work_package)}",
        f"Current Increment: {_artifact_label(state.current_increment)}",
        f"Current Spec: {_artifact_label(state.current_spec)}",
    ]
    if state.health in {Health.READY, Health.BLOCKED, Health.COMPLETE} and state.tickets:
        lines.append(f"Derived Delivery State: {_paint(_health_label(state.health), state.health, color)}")
    lines.extend(
        [
            f"Completed: {completed}",
            f"Remaining: {remaining}",
        ]
    )
    if state.health == Health.COMPLETE and (state.next_candidate_work_packages or state.deferred_work_packages):
        if state.next_candidate_work_packages:
            lines.append("Next candidate Work Packages:")
            lines.extend(f"- {_work_package_horizon_label(item)}" for item in state.next_candidate_work_packages)
        if state.deferred_work_packages:
            lines.append("Deferred:")
            lines.extend(f"- {_work_package_horizon_label(item)}" for item in state.deferred_work_packages)
        if state.next_candidate_work_packages:
            lines.append("Next Increment: not yet shaped")
    lines.extend(
        [
            f"Next Work: {_next_label(state, lang)}",
            f"Next leaf: {state.next_work.leaf}",
            f"Health: {health}",
            f"Reason: {state.next_work.reason}",
        ]
    )
    if state.last_activity:
        lines.append(f"Last activity: {state.last_activity.isoformat(timespec='seconds')}")
    if state.issues:
        lines.append("Issues:")
        for issue in state.issues:
            suffix = f" [{issue.path}]" if issue.path else ""
            lines.append(f"- {issue.severity.upper()} {issue.code}: {issue.message}{suffix}")
    else:
        lines.append("Issues: None")
    lines.append("STOP")
    return "\n".join(lines) + "\n"


def render_doctor(states: Iterable[ProjectState]) -> str:
    states = list(states)
    lines = ["IIS OBSERVATORY DOCTOR", "────────────────────────"]
    issue_count = 0
    for state in states:
        if not state.issues:
            continue
        lines.append(f"{state.repository} [{_health_label(state.health)}]")
        for issue in state.issues:
            issue_count += 1
            suffix = f" ({issue.path})" if issue.path else ""
            lines.append(f"  {issue.severity.upper():7} {issue.code}  {issue.message}{suffix}")
    if issue_count == 0:
        lines.append("PASS: no planning-artifact issues detected.")
    else:
        lines.append(f"\n{issue_count} issue(s) detected across {len(states)} repository scan(s).")
    return "\n".join(lines) + "\n"


def _artifact_label(artifact) -> str:
    if artifact is None:
        return "None"
    name = artifact.identifier or artifact.title or Path(artifact.relative_path).name
    status = f" / {artifact.status}" if artifact.status else ""
    return f"{name}{status} [{artifact.relative_path}]"


def _work_package_horizon_label(artifact) -> str:
    identifier = artifact.identifier or Path(artifact.relative_path).stem
    title = (artifact.title or "").strip()
    if not title:
        return identifier
    clean = re.sub(rf"(?i)^\s*{re.escape(identifier)}\s*[:\-]?\s*", "", title).strip()
    if not clean or clean == identifier:
        return identifier
    return f"{identifier}: {clean}"
