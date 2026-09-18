"""Output formatting for trimmed log results.

Provides text and JSON output formatters for grouped/trimmed log patterns.
"""

from __future__ import annotations

import json
from typing import Any


def format_text(summary: dict, patterns: list) -> str:
    """Format trimmed log results as human-readable text.

    Args:
        summary: Dict with original_count, trimmed_count, compression_ratio, threshold.
        patterns: List of pattern dicts with pattern, count, sample, first_seen, last_seen.

    Returns:
        Formatted text string.
    """
    lines: list[str] = []

    # Header metadata
    lines.append("# Log Trimmer Output")
    lines.append(f"# input_lines={summary['original_count']}")
    lines.append(f"# exact_patterns={summary['original_count']}")
    lines.append(f"# grouped_patterns={summary['trimmed_count']}")
    lines.append(f"# compression_ratio={summary['compression_ratio']}%")
    lines.append(f"# threshold={summary['threshold']}")
    lines.append("")

    # Pattern table
    if patterns:
        max_count = max(p["count"] for p in patterns)
        count_width = len(str(max_count))

        lines.append(f"{'COUNT':>{count_width}}    PATTERN")
        for p in patterns:
            lines.append(f"{p['count']:>{count_width}}    {p['pattern']}")

    return "\n".join(lines)


def format_json(summary: dict, patterns: list) -> str:
    """Format trimmed log results as JSON.

    Args:
        summary: Dict with original_count, trimmed_count, compression_ratio, threshold.
        patterns: List of pattern dicts with pattern, count, sample, first_seen, last_seen.

    Returns:
        JSON string.
    """
    output: dict[str, Any] = {
        "original_count": summary["original_count"],
        "trimmed_count": summary["trimmed_count"],
        "compression_ratio": summary["compression_ratio"],
        "patterns": [],
    }

    for p in patterns:
        output["patterns"].append({
            "pattern": p["pattern"],
            "count": p["count"],
            "sample": p["sample"],
            "first_seen": p.get("first_seen"),
            "last_seen": p.get("last_seen"),
        })

    return json.dumps(output, ensure_ascii=False, indent=2)


def format_output(summary: dict, patterns: list, fmt: str = "text") -> str:
    """Select formatter based on format string.

    Args:
        summary: Summary dict.
        patterns: Patterns list.
        fmt: Format selector — "text" or "json". Defaults to "text".

    Returns:
        Formatted output string.

    Raises:
        ValueError: If fmt is not "text" or "json".
    """
    if fmt == "text":
        return format_text(summary, patterns)
    elif fmt == "json":
        return format_json(summary, patterns)
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Use 'text' or 'json'.")
