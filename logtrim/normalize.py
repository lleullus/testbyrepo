import json
import re
from typing import Any


_UNSTABLE_JSON_FIELDS = {"request_id", "ts"}
_TIMESTAMP_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\b")
_PROC_PATTERN = re.compile(r"\b([\w.-]+)\[(\d+)\](?=[^\w]|$)")
_PID_KV_PATTERN = re.compile(r"\bpid=\d+\b", re.IGNORECASE)
_TID_KV_PATTERN = re.compile(r"\btid=\d+\b", re.IGNORECASE)
_UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\b"
)
_IP_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_ADDR_PATTERN = re.compile(r"\b0x[0-9a-fA-F]+\b")
_PORT_KV_PATTERN = re.compile(r"\bport=\d+\b", re.IGNORECASE)
_COLON_PORT_PATTERN = re.compile(r"(?<!\d):\d{2,5}\b")
_POD_SUFFIX_PATTERN = re.compile(
    r"\b(?P<prefix>[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)-[a-f0-9]{8,10}-[a-z0-9]{5}\b",
    re.IGNORECASE,
)
_HASH_PATTERN = re.compile(r"\b(?=[a-fA-F0-9]*[A-Fa-f])(?=[a-fA-F0-9]*\d)[a-fA-F0-9]{8,}\b")
_LONG_NUMBER_PATTERN = re.compile(r"\b\d{6,}\b")
_ID_PATTERN = re.compile(r"\bid=([a-fA-F0-9]+)\b")


def normalize_event_text(text: str) -> str:
    """Normalize observable chunks in free-form log text."""
    normalized = text
    normalized = _TIMESTAMP_PATTERN.sub("<TS>", normalized)
    normalized = _PID_KV_PATTERN.sub("pid=<PID>", normalized)
    normalized = _TID_KV_PATTERN.sub("tid=<TID>", normalized)
    normalized = _PROC_PATTERN.sub(r"\1[<PID>]", normalized)
    normalized = _UUID_PATTERN.sub("<UUID>", normalized)
    normalized = _ADDR_PATTERN.sub("<ADDR>", normalized)
    normalized = _IP_PATTERN.sub("<IP>", normalized)
    normalized = _PORT_KV_PATTERN.sub("port=<PORT>", normalized)
    normalized = _COLON_PORT_PATTERN.sub(":<PORT>", normalized)
    normalized = _POD_SUFFIX_PATTERN.sub(_replace_pod_name, normalized)
    normalized = _HASH_PATTERN.sub("<HASH>", normalized)
    normalized = _LONG_NUMBER_PATTERN.sub("<NUM>", normalized)
    normalized = _ID_PATTERN.sub("id=<HEX>", normalized)
    return normalized


def normalize_json_text(text: str) -> str:
    """Build a deterministic text key for JSON payloads."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return normalize_event_text(text)

    canon = _canonicalize_json(parsed)
    return json.dumps(canon, separators=(",", ":"), sort_keys=True)


def _canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        filtered = {
            key: _canonicalize_json(val)
            for key, val in value.items()
            if key not in _UNSTABLE_JSON_FIELDS
        }
        return filtered
    if isinstance(value, list):
        return [_canonicalize_json(entry) for entry in value]
    return value


def _replace_pod_name(match: re.Match[str]) -> str:
    return f"{match.group('prefix')}-<POD>"
