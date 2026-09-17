"""Simple describe summarizer helpers."""

from __future__ import annotations

from typing import Iterable

_DESCRIBE_ANCHORS = (
    "Name:",
    "Namespace:",
    "Labels:",
    "Annotations:",
    "Events:",
    "Conditions:",
)


def summarize_describe(lines: Iterable[str]) -> str:
    """Return a compact subset of the describe output."""

    cleaned_lines: list[str] = []
    keep_continuations = False

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if not stripped:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        if _starts_anchor(line):
            cleaned_lines.append(line)
            keep_continuations = True
            continue

        if keep_continuations and (line.startswith(" ") or line.startswith("\t")):
            cleaned_lines.append(line)
            continue

        keep_continuations = False

    return "\n".join(cleaned_lines)


def _starts_anchor(line: str) -> bool:
    for anchor in _DESCRIBE_ANCHORS:
        if line.startswith(anchor):
            return True
    return False
