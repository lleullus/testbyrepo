from __future__ import annotations

from collections.abc import Iterable, Iterator

from logtrim.detect import detect_family, looks_like_json_array_start, starts_new_event
from logtrim.models import LogicalRecord


def eventize_lines(lines: Iterable[str]) -> Iterator[LogicalRecord]:
    buffer: list[str] = []
    start_line = 0
    json_mode = False
    json_depth = 0
    json_in_string = False
    json_escaped = False
    last_line = 0

    for line_number, raw_line in enumerate(lines, start=1):
        last_line = line_number
        line = raw_line.rstrip("\n")

        if not buffer and not line.strip():
            continue

        if not buffer:
            buffer = [line]
            start_line = line_number
            if _is_json_start(line):
                json_mode = True
                json_depth, json_in_string, json_escaped = _scan_json_state(
                    line, json_depth, json_in_string, json_escaped
                )
                if _json_complete(json_depth, json_in_string):
                    yield _finalize_record(buffer, start_line, line_number, json_mode=True)
                    buffer = []
                    json_mode = False
                    json_depth = 0
                    json_in_string = False
                    json_escaped = False
            continue

        if json_mode:
            buffer.append(line)
            json_depth, json_in_string, json_escaped = _scan_json_state(
                line, json_depth, json_in_string, json_escaped
            )
            if _json_complete(json_depth, json_in_string):
                yield _finalize_record(buffer, start_line, line_number, json_mode=True)
                buffer = []
                json_mode = False
                json_depth = 0
                json_in_string = False
                json_escaped = False
            continue

        if _is_json_start(line):
            yield _finalize_record(buffer, start_line, line_number - 1, json_mode=False)
            buffer = [line]
            start_line = line_number
            json_mode = True
            json_depth, json_in_string, json_escaped = _scan_json_state(
                line, json_depth, json_in_string, json_escaped
            )
            if _json_complete(json_depth, json_in_string):
                yield _finalize_record(buffer, start_line, line_number, json_mode=True)
                buffer = []
                json_mode = False
                json_depth = 0
                json_in_string = False
                json_escaped = False
            continue

        if starts_new_event(line):
            yield _finalize_record(buffer, start_line, line_number - 1, json_mode=False)
            buffer = [line]
            start_line = line_number
            continue

        buffer.append(line)

    if buffer:
        yield _finalize_record(buffer, start_line, last_line, json_mode=json_mode)


def _finalize_record(
    lines: list[str],
    start_line: int,
    end_line: int,
    *,
    json_mode: bool,
) -> LogicalRecord:
    text = "\n".join(lines)
    family = "json" if json_mode else detect_family(text)
    return LogicalRecord(
        text=text,
        family=family,
        start_line=start_line,
        end_line=end_line,
    )


def _is_json_start(line: str) -> bool:
    return line.lstrip().startswith("{") or looks_like_json_array_start(line)


def _scan_json_state(
    line: str, depth: int, in_string: bool, escaped: bool
) -> tuple[int, bool, bool]:
    for char in line:
        if in_string:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1

    return depth, in_string, escaped


def _json_complete(depth: int, in_string: bool) -> bool:
    return depth <= 0 and not in_string
