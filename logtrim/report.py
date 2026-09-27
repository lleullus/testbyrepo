"""Streaming reports; no list of clusters or whole-report string is required."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import math


def safe_text(value) -> str:
    text = str(value)
    return "".join(f"\\u{ord(c):04x}" if ord(c) < 32 or 127 <= ord(c) <= 159
                   or 0x202a <= ord(c) <= 0x202e or 0x2066 <= ord(c) <= 0x2069
                   else c for c in text)

def _variant_delta(pattern: str, variant: str, limit: int = 120) -> str:
    """Show only the changed middle span, with bounded work and output."""
    prefix = 0
    common = min(len(pattern), len(variant))
    while prefix < common and pattern[prefix] == variant[prefix]:
        prefix += 1
    suffix = 0
    remaining = min(len(pattern) - prefix, len(variant) - prefix)
    while suffix < remaining and pattern[len(pattern) - suffix - 1] == variant[len(variant) - suffix - 1]:
        suffix += 1
    old = pattern[prefix:len(pattern) - suffix if suffix else len(pattern)]
    new = variant[prefix:len(variant) - suffix if suffix else len(variant)]
    pieces = []
    if old:
        pieces.append("−" + old[:limit])
    if new:
        pieces.append("+" + new[:limit])
    delta = " ".join(pieces) or "(same representation)"
    return delta if len(delta) <= limit else delta[:limit - 1] + "…"


def _variant_lines(row: dict):
    states = row.get("family_states", {})
    if states:
        counts = ", ".join(f"{state}={value['count']}" for state, value in states.items())
        yield "states: " + counts
    variants = row.get("variants", {})
    for index, (variant, counts) in enumerate(variants.items()):
        branch = "└─" if index == len(variants) - 1 and not row.get("variant_other_count") else "├─"
        detail = _variant_delta(row["pattern"], variant)
        yield (f"{branch} {counts['count']} {detail} "
               f"[baseline={counts['baseline']} current={counts['current']}]")
    overflow = row.get("variant_other_count", 0)
    if overflow:
        yield f"└─ other: {overflow} observations; {row.get('variant_unique_count', 0)} unique total"


def diff_rows(analyzer, min_ratio: float = 2.0):
    if not math.isfinite(min_ratio) or min_ratio <= 1:
        raise ValueError("min_ratio must be finite and greater than one")
    nb, nc = analyzer.phase_events["baseline"], analyzer.phase_events["current"]
    for row in analyzer.rows():
        b, c = row["baseline"], row["current"]
        rb, rc = (b + 0.5) / (nb + 1), (c + 0.5) / (nc + 1)
        ratio = rc / rb
        change = ("NEW" if b == 0 else "RESOLVED" if c == 0 else
                  "SURGED" if ratio >= min_ratio else
                  "DROPPED" if ratio <= 1 / min_ratio else "STABLE")
        row.update(change=change, baseline_rate=rb, current_rate=rc,
                   rate_ratio=ratio, log2_ratio=math.log2(ratio))
        yield row


def render(summary: dict, rows, fmt: str = "text"):
    dump = lambda value: json.dumps(value, ensure_ascii=True, allow_nan=False)
    if fmt == "json":
        yield '{"summary":' + dump(summary) + ',"patterns":['
        separator = ""
        for row in rows:
            yield separator + dump(row)
            separator = ","
        yield "]}\n"
    elif fmt == "jsonl":
        yield dump({"type": "summary", **summary}) + "\n"
        for row in rows:
            yield dump({"type": "pattern", **row}) + "\n"
    elif fmt in {"text", "markdown"}:
        yield (f"# logtrim {summary['tool_version']}\n"
               f"# lines={summary['original_count']} events={summary['logical_events']} "
               f"exact={summary['exact_patterns']} clusters={summary['trimmed_count']}\n")
        if fmt == "markdown":
            yield "\n| Count | Change | Pattern and semantic variants |\n| ---: | --- | --- |\n"
        for row in rows:
            text = safe_text(row["pattern"])
            change = row.get("change", "")
            if fmt == "markdown":
                text = html.escape(text).replace("|", "&#124;").replace("`", "&#96;")
                variants = "<br>".join(
                    html.escape(safe_text(line)).replace("|", "&#124;")
                    for line in _variant_lines(row))
                detail = f"<br><small>{variants}</small>" if variants else ""
                yield (f"| {row['count']} | {html.escape(str(change))} | "
                       f"{text}{detail} |\n")
            else:
                yield f"{row['count']:>9} {change:8} {text}\n"
                for line in _variant_lines(row):
                    yield f"          {safe_text(line)}\n"
    elif fmt == "html":
        script = ("document.getElementById('q').addEventListener('input',function(){"
                  "const q=this.value.toLowerCase();"
                  "document.querySelectorAll('tbody tr').forEach(r=>{"
                  "r.hidden=!r.textContent.toLowerCase().includes(q);});});")
        digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
        yield ("<!doctype html><html lang='en'><meta charset='utf-8'>"
               f"<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
               f"script-src 'sha256-{digest}'\"><title>logtrim</title><body>"
               "<h1>logtrim report</h1><label>Filter <input id='q'></label>"
               "<table><thead><tr><th>Count</th><th>Change</th><th>Pattern</th></tr></thead><tbody>")
        for row in rows:
            text = html.escape(safe_text(row["pattern"]))
            change = html.escape(row.get("change", ""))
            variants = "".join(
                f"<li>{html.escape(safe_text(line))}</li>" for line in _variant_lines(row))
            details = (f"<details><summary>Variants</summary><ul>{variants}</ul></details>"
                       if variants else "")
            yield (f"<tr><td>{row['count']}</td><td>{change}</td><td><pre>{text}</pre>"
                   f"{details}</td></tr>")
        yield f"</tbody></table><script>{script}</script></body></html>\n"
    else:
        raise ValueError(f"unsupported format: {fmt}")


def format_output(summary: dict, patterns, fmt: str = "text") -> str:
    """Small-result compatibility helper; CLI uses render() instead."""
    return "".join(render(summary, patterns, fmt))