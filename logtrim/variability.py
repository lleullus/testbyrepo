"""Disk-friendly signatures for learning stable, high-cardinality values."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .similarity import TOKEN


@dataclass(frozen=True, slots=True)
class Candidate:
    location: str
    lexical_type: str
    value: str
    start: int | None = None
    end: int | None = None


_PROTECTED_KEYS = {
    "status", "status_code", "http_status", "http_status_code", "response_code",
    "responsecode", "code", "error", "error_type", "error_code", "errortype",
    "errorcode", "exception", "exception_type", "exception_class", "exceptiontype",
    "exceptionclass", "service", "component", "logger", "level", "severity",
    "namespace", "workload", "method", "http_method", "route", "result", "outcome",
    "state", "phase", "reason", "condition", "conditions", "ready", "success", "type",
}
_PROTECTED_VALUES = {
    "failed", "failure", "succeeded", "success", "successful", "ok", "timeout",
    "timedout", "running", "pending", "error", "exception", "ready", "notready",
    "crashloopbackoff", "completed", "normal", "warning", "info", "debug", "fatal",
    "critical", "refused", "established", "connected", "disconnected", "started",
    "stopped", "true", "false", "unknown", "available", "unavailable", "healthy",
    "unhealthy", "open", "closed", "new", "resolved", "surged", "dropped",
}
_ERROR_CODE = re.compile(r"^(?:ORA-\d{5}|SQLSTATE\[[0-9A-Z]{5}\]|[A-Z][A-Z_]{1,15}-\d{3,8})$")
_EXCEPTION = re.compile(r"(?:Error|Exception|Failure|Fault)$", re.I)
_UUID = re.compile(r"^[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
_FLOAT = re.compile(r"^-?\d+\.\d+(?:[eE][+-]?\d+)?$")
_INTEGER = re.compile(r"^-?\d{3,}$")
_HEX = re.compile(r"^(?:0x)?[0-9a-fA-F]{6,}$")
_OPAQUE = re.compile(r"^[A-Za-z0-9_.-]{4,}$")
_WORD = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{2,}$")
_FIELD = re.compile(r"([A-Za-z_][\w.-]*)=([A-Za-z0-9_./:+-]+)")
_ROUTE_METHOD = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
_PREFIX = "\x00logtrim-adaptive:"
_SUFFIX = "\x00"


def _kind(value, key: str = "", allow_word: bool = False) -> str | None:
    text = str(value)
    if not text or text.startswith("<") and text.endswith(">"):
        return None
    lower = text.lower()
    key = key.lower().replace("-", "_").replace(".", "_")
    if key in _PROTECTED_KEYS or lower in _PROTECTED_VALUES:
        return None
    if _ERROR_CODE.fullmatch(text) or _EXCEPTION.search(text):
        return None
    if lower.isdigit() and 100 <= int(lower) <= 599 and "status" in key:
        return None
    if _UUID.fullmatch(text):
        return "uuid"
    if _FLOAT.fullmatch(text):
        return "float"
    if _INTEGER.fullmatch(text):
        return "integer"
    if _HEX.fullmatch(text) and any(ch.isalpha() for ch in text) and any(ch.isdigit() for ch in text):
        return "hexadecimal"
    if _OPAQUE.fullmatch(text) and any(ch.isalpha() for ch in text) and any(ch.isdigit() for ch in text):
        return "opaque_alphanumeric"
    if allow_word and _WORD.fullmatch(text):
        return "word"
    return None


def _marker(kind: str) -> str:
    return f"{_PREFIX}{kind}{_SUFFIX}"


def _walk_json(value, path: str, parent: str,
               promoted: set[tuple[str, str]] | None,
               candidates: list[Candidate] | None):
    if isinstance(value, dict):
        return {key: _walk_json(item, f"{path}/{key}", key, promoted, candidates)
                for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_walk_json(item, f"{path}/{index}", parent, promoted, candidates)
                for index, item in enumerate(value)]
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        kind = _kind(value, parent, allow_word=True)
        location = path or "/"
        if kind:
            if candidates is not None:
                candidates.append(Candidate(location, kind, str(value)))
            if promoted is None:
                return _marker(kind)
            if (location, kind) in promoted:
                return "<ID>"
    return value


def _text_candidates(pattern: str) -> tuple[str, list[Candidate]]:
    matches = list(TOKEN.finditer(pattern))
    replacements: list[tuple[int, int, str]] = []
    candidates: list[Candidate] = []
    previous = [match.group() for match in matches]
    for index, match in enumerate(matches):
        token = match.group()
        field = _FIELD.search(token)
        if field:
            key, value = field.groups()
            kind = _kind(value, key, allow_word=True)
            if kind:
                # Field values can have trailing punctuation; keep it in the structure.
                absolute_start = match.start() + field.start(2)
                absolute_end = match.start() + field.end(2)
                location = f"token[{index}].field:{key.lower()}"
                candidates.append(Candidate(location, kind, value, absolute_start, absolute_end))
                replacements.append((absolute_start, absolute_end, _marker(kind)))
                continue

        route = token.startswith("/") and index > 0 and previous[index - 1].upper() in _ROUTE_METHOD
        if route:
            offset = 0
            for segment_index, segment in enumerate(token.split("/")):
                if not segment:
                    offset += 1
                    continue
                kind = _kind(segment, allow_word=True)
                if kind:
                    start = match.start() + offset
                    end = start + len(segment)
                    location = f"token[{index}].path_segment[{segment_index}]"
                    candidates.append(Candidate(location, kind, segment, start, end))
                    replacements.append((start, end, _marker(kind)))
                offset += len(segment) + 1
            continue

        context = previous[index - 1].lower().rstrip(":=") if index else ""
        if context == "http" or context.startswith("http/"):
            continue
        allow_context_word = context in {"to", "from", "node", "host", "peer"}
        kind = _kind(token, allow_word=allow_context_word)
        if kind:
            location = f"token[{index}]"
            candidates.append(Candidate(location, kind, token, match.start(), match.end()))
            replacements.append((match.start(), match.end(), _marker(kind)))

    skeleton = pattern
    for start, end, marker in reversed(replacements):
        skeleton = skeleton[:start] + marker + skeleton[end:]
    return skeleton, candidates


def signature(parser: str, pattern: str) -> tuple[str, list[Candidate]]:
    """Return a structural signature and value candidates for one unique pattern."""
    if pattern.startswith("{"):
        try:
            value = json.loads(pattern)
        except (ValueError, RecursionError):
            pass
        else:
            candidates: list[Candidate] = []
            shape = _walk_json(value, "", "", None, candidates)
            skeleton = json.dumps(shape, ensure_ascii=True, sort_keys=True,
                                  separators=(",", ":"), allow_nan=False)
            return skeleton, candidates
    return _text_candidates(pattern)


def generalized_pattern(parser: str, pattern: str,
                        promoted: set[tuple[str, str]]) -> str:
    """Replace only promoted positions; all other literals remain protected."""
    if pattern.startswith("{"):
        try:
            value = json.loads(pattern)
        except (ValueError, RecursionError):
            pass
        else:
            result = _walk_json(value, "", "", promoted, None)
            return json.dumps(result, ensure_ascii=True, sort_keys=True,
                              separators=(",", ":"), allow_nan=False)
    _, candidates = _text_candidates(pattern)
    replacements = [(item.start, item.end, "<ID>") for item in candidates
                    if (item.location, item.lexical_type) in promoted
                    and item.start is not None and item.end is not None]
    result = pattern
    for start, end, replacement in sorted(replacements, reverse=True):
        result = result[:start] + replacement + result[end:]
    return result
