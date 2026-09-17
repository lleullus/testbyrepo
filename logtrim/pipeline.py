from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Literal

from logtrim.describe import summarize_describe
from logtrim.detect import looks_like_json_array_start, starts_new_event
from logtrim.eventize import eventize_lines
from logtrim.grouping import group_json_records, group_records
from logtrim.render import render_groups
from logtrim.snapshot import summarize_snapshot

Family = Literal["event", "json", "snapshot", "describe", "generic"]

_SECTION_TITLES: dict[Family, str] = {
    "event": "Event Logs",
    "json": "JSON Logs",
    "snapshot": "Snapshot Output",
    "describe": "Describe Output",
    "generic": "Generic Text",
}

_DESCRIBE_ANCHORS = (
    "Name:",
    "Namespace:",
    "Labels:",
    "Annotations:",
    "Events:",
    "Conditions:",
)


def process_stream(lines: Iterable[str]) -> Iterator[str]:
    current_family: Family | None = None
    current_lines: list[str] = []
    snapshot_width: int | None = None
    pending_generic_sections: list[list[str]] = []
    seen_non_generic = False

    def emit_section(family: Family, section_lines: list[str]) -> Iterator[str]:
        nonlocal seen_non_generic
        if family == "generic":
            if seen_non_generic:
                yield _render_section(family, section_lines)
            else:
                pending_generic_sections.append(section_lines)
            return

        if not seen_non_generic:
            for generic_lines in pending_generic_sections:
                yield _render_section("generic", generic_lines)
            pending_generic_sections.clear()
            seen_non_generic = True

        yield _render_section(family, section_lines)

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        family = _classify_line(line, current_family, snapshot_width, current_lines)
        if current_family is None:
            current_family = family
            current_lines.append(raw_line)
            if family == "snapshot":
                snapshot_width = len(line.split())
            continue

        if family != current_family:
            yield from emit_section(current_family, current_lines)
            current_family = family
            current_lines = [raw_line]
            snapshot_width = len(line.split()) if family == "snapshot" else None
            continue

        current_lines.append(raw_line)

    if current_family is not None:
        yield from emit_section(current_family, current_lines)

    if not seen_non_generic:
        for generic_lines in pending_generic_sections:
            yield _render_section("generic", generic_lines)


def _classify_line(
    line: str,
    current_family: Family | None,
    snapshot_width: int | None,
    current_lines: list[str],
) -> Family:
    stripped = line.strip()
    if not stripped:
        if current_family in {"event", "json", "describe"}:
            return current_family
        return "generic"

    if _starts_describe(line):
        return "describe"
    if _starts_snapshot(line):
        return "snapshot"
    if current_family == "describe" and (
        line.startswith(" ") or line.startswith("\t") or stripped.endswith(":")
    ):
        return "describe"
    if line.lstrip().startswith("{") or looks_like_json_array_start(line):
        return "json"
    if starts_new_event(line):
        return "event"

    if current_family == "snapshot" and snapshot_width is not None and len(line.split()) == snapshot_width:
        return "snapshot"
    if current_family == "json" and _looks_like_json_continuation(line):
        return "json"
    if current_family == "event" and _looks_like_event_continuation(line):
        return "event"
    if current_family == "event" and _event_tail_context(current_lines):
        return "event"
    return "generic"


def _starts_describe(line: str) -> bool:
    for anchor in _DESCRIBE_ANCHORS:
        if line.startswith(anchor):
            return True
    return False


def _starts_snapshot(line: str) -> bool:
    upper = line.upper()
    return (
        upper.startswith("NAMESPACE NAME READY STATUS")
        or upper.startswith("NAMESPACE NAME STATUS")
        or upper.startswith("NAME READY STATUS")
        or upper.startswith("NAME STATUS")
    )


def _looks_like_json_continuation(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(("\"", "{", "[", "}", "]", ",")) or line.startswith((" ", "\t"))


def _looks_like_event_continuation(line: str) -> bool:
    stripped = line.lstrip()
    return line.startswith((" ", "\t")) or stripped.startswith(
        (
            "Traceback",
            "File ",
            "Caused by:",
            "at ",
            "...",
            "Previous message:",
            "During handling of the above exception, another exception occurred:",
            "The above exception was the direct cause of the following exception:",
        )
    )


def _event_tail_context(current_lines: list[str]) -> bool:
    for line in reversed(current_lines):
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith(
            ("Traceback", "File ", "Caused by:", "at ", "...", "Exception in thread")
        )
    return False


def _render_section(family: Family, lines: list[str]) -> str:
    title = _SECTION_TITLES[family]
    if family == "event":
        records = list(eventize_lines(lines))
        summary = render_groups(group_records(record.text for record in records))
    elif family == "json":
        records = list(eventize_lines(lines))
        summary = render_groups(group_json_records(record.text for record in records))
    elif family == "snapshot":
        summary = summarize_snapshot(lines)
    elif family == "describe":
        summary = summarize_describe(lines)
    else:
        summary = "".join(lines).rstrip("\n")

    if summary:
        return f"{title}\n{summary}\n"
    return f"{title}\n"
