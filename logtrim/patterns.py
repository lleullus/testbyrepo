"""Parser-first normalization with non-overlapping spans and semantic anchors."""
from __future__ import annotations

import ipaddress
import json
import math
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from .models import Config, NormalizedEvent, ResourceLimit
from .similarity import tokenize

ISO = re.compile(r"\b\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:?\d\d)?")
SYSLOG = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+(\d\d):(\d\d):(\d\d)")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
KLOG = re.compile(r"^([IWEF])(\d{2})(\d{2})\s+(\d\d:\d\d:\d\d(?:\.\d+)?)\s+(\d+)\s+([^: ]+):(\d+)\]\s*(.*)$", re.S)
EXCEPTION = re.compile(r"\b(?:[A-Za-z_$][\w$]*\.)*(?:[A-Za-z_$][\w$]*)?(?:Error|Exception|Failure|Fault|KeyboardInterrupt|SystemExit|StopIteration)\b")
ERROR_CODE = re.compile(r"\b(?:ORA-\d{5}|SQLSTATE\[[0-9A-Z]{5}\]|[A-Z][A-Z_]{1,15}-\d{3,8})\b")
PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9_]*>")
URL = re.compile(r'''\bhttps?://[^\s<>"']+''')
PATH = re.compile(r'''(?<![\w/\\])(?:/[\w.~@+%-][^\s<>"',;)\]}]*|[A-Za-z]:\\[^\s<>"'|]+|\\\\[^\s<>"'|]+)''')
IP = re.compile(r"(?<![\w:.])(?:[0-9A-Fa-f]*:[0-9A-Fa-f:.]+(?:%[\w.-]+)?|(?:\d{1,3}\.){3}\d{1,3})(?![\w.])")
UUID = re.compile(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b")
MAC = re.compile(r"(?<![\w:])(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}(?![\w:])")
OPAQUE = re.compile(r"\b(?:0x[0-9a-fA-F]{8,}|[A-Za-z0-9]{20,})\b")
SECRET_KEY = re.compile(r"(?i)(?:^|[_-])(?:password|passwd|secret|token|authorization|cookie|api[_-]?key)$")
SECRET = re.compile(r'''(?i)\b(password|passwd|secret|token|authorization|cookie|api[_-]?key)\s*[:=]\s*(?:Bearer\s+|Basic\s+)?(?:"(?:\\.|[^"\\])*"|'[^']*'|[^\s,;]+)''')
LOGFMT = re.compile(r'''([A-Za-z_][\w.-]*)=("(?:\\.|[^"\\])*"|[^\s"]*)''')
DURATION = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)\s*(ns|us|ms|s)\b")
CONTEXT_NUMBER = re.compile(r"(?i)\b(pid|port|line|retries|retry|attempt|count|bytes|latency_ms|duration_ms)\s*[:=]?\s*(-?\d+(?:\.\d+)?)\b")
PRESERVE = {"service", "component", "logger", "level", "severity", "error.type",
            "exception.type", "exception.class", "error.code", "event.code",
            "status", "status_code", "http.status_code", "method", "http.method", "route"}
NUMERIC = {"pid": "PID", "port": "PORT", "line": "LINE", "count": "NUMBER",
           "retries": "RETRY_COUNT", "retry": "RETRY_COUNT", "attempt": "NUMBER",
           "bytes": "BYTES", "latency_ms": "DURATION_MS", "duration_ms": "DURATION_MS"}
IDENTIFIERS = {"request_id", "trace_id", "span_id", "session_id", "user_id", "id"}


def parse_timestamp(text: str, year: int | None = None,
                    offset_minutes: int = 0) -> datetime | None:
    assumed = timezone(timedelta(minutes=offset_minutes))
    match = ISO.search(text)
    try:
        if match:
            iso = match.group().replace("Z", "+00:00")
            if re.search(r"[+-]\d{4}$", iso):
                iso = iso[:-2] + ":" + iso[-2:]
            value = datetime.fromisoformat(iso)
            if value.tzinfo is None:
                value = value.replace(tzinfo=assumed)
            return value.astimezone(timezone.utc)
        match = SYSLOG.search(text)
        if match and year is not None:
            month, day, hour, minute, second = match.groups()
            return datetime(year, MONTHS.index(month) + 1, int(day), int(hour),
                            int(minute), int(second), tzinfo=assumed).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        pass
    return None


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite JSON number")
    return number


def reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def parse_logfmt(text: str) -> dict | None:
    result, pos = {}, 0
    for match in LOGFMT.finditer(text):
        if text[pos:match.start()].strip() or (result and match.start() == pos):
            return None
        key, value = match.groups()
        if key in result:
            return None
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                return None
        result[key], pos = value, match.end()
    return result if result and not text[pos:].strip() else None


class Normalizer:
    def __init__(self, config: Config | None = None, rules: list[dict] | None = None,
                 stats: Counter | None = None):
        self.config = config or Config()
        self.stats = stats if stats is not None else Counter()
        self.rule_specs = [] if rules is None else rules
        if not isinstance(self.rule_specs, list) or len(self.rule_specs) > 64:
            raise ValueError("rules must be a list with at most 64 entries")
        self.rules, ids = [], set()
        for spec in self.rule_specs:
            if not isinstance(spec, dict) or set(spec) - {"id", "pattern", "action", "placeholder"}:
                raise ValueError("invalid custom rule fields")
            rid, pattern = spec.get("id", ""), spec.get("pattern", "")
            action, slot = spec.get("action", "replace"), spec.get("placeholder", "CUSTOM")
            if not isinstance(rid, str) or not rid or rid in ids:
                raise ValueError("rule id must be nonempty and unique")
            if not isinstance(pattern, str) or not pattern or len(pattern) > 4096:
                raise ValueError("invalid regex length")
            if action not in {"preserve", "replace", "redact"}:
                raise ValueError("invalid rule action")
            if not isinstance(slot, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", slot):
                raise ValueError("invalid placeholder")
            try:
                regex = re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"invalid regex in rule {rid}") from exc
            if regex.search(""):
                raise ValueError("a rule must not match an empty string")
            ids.add(rid)
            self.rules.append((rid, regex, action, slot))

    def text(self, text: str, field: str = "message") -> tuple[str, list]:
        spans = []

        def add(start, end, replacement, priority, kind, value=None):
            if start == end:
                raise ValueError("a normalization rule matched an empty span")
            spans.append((priority, start, end, replacement, kind, value))
            if len(spans) > self.config.max_tokens * 8:
                raise ResourceLimit("too many normalization spans")

        for regex, priority in ((PLACEHOLDER, 2000), (EXCEPTION, 900), (ERROR_CODE, 900)):
            for m in regex.finditer(text):
                add(m.start(), m.end(), m.group(), priority, "protected")
        for m in re.finditer(r"\b(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(/[^?\s<>\"']*)", text):
            add(m.start(1), m.end(1), m.group(1), 900, "protected")
        for m in SECRET.finditer(text):
            add(m.start(), m.end(), m.group(1).lower() + "=<REDACTED>", 1000, "redacted")
        for rid, regex, action, slot in self.rules:
            for m in regex.finditer(text):
                out = m.group() if action == "preserve" else f"<{slot}>"
                if action == "redact":
                    out = "<REDACTED>"
                add(m.start(), m.end(), out, 950 if action == "preserve" else 850,
                    "rule." + rid)
        for regex in (ISO, SYSLOG):
            for m in regex.finditer(text):
                add(m.start(), m.end(), "<TIMESTAMP>", 800, "TIMESTAMP")
        for m in URL.finditer(text):
            value = m.group().rstrip(".,;!?)]}")
            try:
                valid = bool(urlsplit(value).hostname)
            except ValueError:
                valid = False
            if valid:
                add(m.start(), m.start() + len(value), "<URL>", 1100, "URL")
        for regex, kind in ((UUID, "UUID"), (MAC, "MAC")):
            for m in regex.finditer(text):
                add(m.start(), m.end(), f"<{kind}>", 750, kind)
        for m in IP.finditer(text):
            candidate = m.group()
            if candidate == "::" and text[max(0, m.start() - 1):m.start()] != "[":
                continue
            try:
                addr = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            kind = "IPV4" if addr.version == 4 else "IPV6"
            add(m.start(), m.end(), f"<{kind}>", 700, kind)
        for m in PATH.finditer(text):
            add(m.start(), m.end(), "<PATH>", 650, "PATH")
        for m in OPAQUE.finditer(text):
            value = m.group()
            if any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
                add(m.start(), m.end(), "<ID>", 600, "ID")
        for m in CONTEXT_NUMBER.finditer(text):
            kind = NUMERIC[m.group(1).lower()]
            value = float(m.group(2))
            add(m.start(2), m.end(2), f"<{kind}>", 550, kind,
                value if math.isfinite(value) else None)
        for m in re.finditer(r"(?<=\.java:)\d+\b", text):
            add(m.start(), m.end(), "<LINE>", 550, "LINE")
        for m in DURATION.finditer(text):
            kind, value = "DURATION_" + m.group(2).upper(), float(m.group(1))
            add(m.start(), m.end(), f"<{kind}>", 500, kind,
                value if math.isfinite(value) else None)
        occupied, chosen = bytearray(len(text)), []
        for item in sorted(spans, key=lambda s: (-s[0], s[1], -(s[2] - s[1]))):
            _, start, end, _, _, _ = item
            if not any(occupied[start:end]):
                occupied[start:end] = b"\x01" * (end - start)
                chosen.append(item)
        pieces, captures, pos, ordinal = [], [], 0, Counter()
        for _, start, end, out, kind, value in sorted(chosen, key=lambda s: s[1]):
            pieces.extend((text[pos:start], out))
            pos = end
            self.stats["normalize." + kind] += 1
            if value is not None:
                ordinal[kind] += 1
                captures.append((f"{field}.{kind}[{ordinal[kind]}]", value))
        pieces.append(text[pos:])
        return " ".join("".join(pieces).split()), captures

    def normalize(self, raw: str) -> NormalizedEvent:
        if len(raw.encode("utf-8")) > self.config.max_event_bytes:
            raise ResourceLimit("event exceeds max_event_bytes")
        parser, obj = "text", None
        if raw.lstrip().startswith("{"):
            try:
                obj = json.loads(raw, object_pairs_hook=unique_object,
                                 parse_constant=reject_constant, parse_float=finite_float)
                parser = "json"
            except (ValueError, RecursionError):
                self.stats["parser.json_failure"] += 1
        elif KLOG.match(raw):
            level, month, day, clock, pid, source, line, message = KLOG.match(raw).groups()
            stamp = (f"{self.config.syslog_year:04d}-{month}-{day}T{clock}"
                     if self.config.syslog_year else f"{month}{day} {clock}")
            obj = {"level": {"I": "INFO", "W": "WARN", "E": "ERROR", "F": "FATAL"}[level],
                   "timestamp": stamp, "pid": int(pid), "source": source,
                   "line": int(line), "message": message}
            parser = "klog"
        elif "=" in raw:
            obj = parse_logfmt(raw)
            if obj is not None:
                parser = "logfmt"
        anchors, captures, stamps = [], [], []
        time_present = False

        def walk(value, path="", depth=0):
            nonlocal time_present
            if depth > 32:
                raise ResourceLimit("structured event exceeds depth 32")
            key = path.rsplit(".", 1)[-1].lower()
            if SECRET_KEY.search(key):
                self.stats["fields.redacted"] += 1
                return "<REDACTED>"
            if isinstance(value, dict):
                return {k: walk(v, f"{path}.{k}" if path else k, depth + 1)
                        for k, v in sorted(value.items())}
            if isinstance(value, list):
                return [walk(v, f"{path}[{i}]", depth + 1) for i, v in enumerate(value)]
            if path.lower() in PRESERVE or key in PRESERVE:
                anchors.append(path + "=" + json.dumps(value, ensure_ascii=True))
                return value
            if key in {"ts", "time", "timestamp", "@timestamp"}:
                time_present = True
                stamp = parse_timestamp(str(value), self.config.syslog_year,
                                        self.config.timezone_minutes)
                if stamp is not None:
                    priority = {"@timestamp": 0, "timestamp": 1, "ts": 2, "time": 3}[key]
                    stamps.append((path.count(".") + path.count("["), priority, stamp))
                return "<TIMESTAMP>"
            if key in IDENTIFIERS:
                return "<ID>"
            if key in {"host", "hostname", "peer", "ip", "address"}:
                return "<HOST>"
            if key in NUMERIC:
                try:
                    number = float(value) if not isinstance(value, bool) else math.nan
                except (ValueError, TypeError, OverflowError):
                    number = math.nan
                if math.isfinite(number):
                    captures.append((path, number))
                    return f"<{NUMERIC[key]}>"
            if isinstance(value, str):
                text, found = self.text(value, path)
                captures.extend(found)
                return text
            return value

        if obj is not None:
            pattern = json.dumps(walk(obj), ensure_ascii=True, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False)
        else:
            pattern, captures = self.text(raw)
        for regex in (EXCEPTION, ERROR_CODE):
            anchors.extend(m.group() for m in regex.finditer(pattern))
        tokens = tokenize(pattern)
        if len(tokens) > self.config.max_tokens:
            raise ResourceLimit("event exceeds max_tokens")
        self.stats["parser." + parser] += 1
        stamp = min(stamps)[2] if stamps else (None if time_present else parse_timestamp(
            raw, self.config.syslog_year, self.config.timezone_minutes))
        return NormalizedEvent(pattern, tokens, tuple(sorted(set(anchors))), parser,
                               stamp, tuple(captures))


def extract_pattern(raw_line: str) -> str:
    return Normalizer().normalize(raw_line).pattern