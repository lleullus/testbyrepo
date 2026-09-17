from __future__ import annotations

import json
import re

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")
_SYSLOG_RE = re.compile(r"^<\d+>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}")
_JOURNAL_RE = re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\S+\s+\S+")
_SEVERITY_RE = re.compile(r"^(?:TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b")
_KLOG_RE = re.compile(r"^[IWEF]\d{4}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+")
_COMPONENT_RE = re.compile(
    r"^(?:kubelet|kube-apiserver|kube-scheduler|kube-controller-manager|etcd|containerd|dockerd|cri-o|systemd|kernel)(?:\[\d+\])?:"
)
_JSON_START_RE = re.compile(r"^\s*\{")
_JSON_NUMBER_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$")

_DESCRIBE_ANCHORS = (
    "Name:",
    "Namespace:",
    "Labels:",
    "Annotations:",
    "Events:",
    "Conditions:",
)


def starts_new_event(line: str) -> bool:
    line = line.rstrip("\n")
    if not line.strip():
        return False
    if _JSON_START_RE.match(line):
        return True
    if _TIMESTAMP_RE.match(line):
        return True
    if _SYSLOG_RE.match(line):
        return True
    if _JOURNAL_RE.match(line):
        return True
    if _SEVERITY_RE.match(line):
        return True
    if _KLOG_RE.match(line):
        return True
    if _COMPONENT_RE.match(line.lstrip()):
        return True
    return False


def detect_family(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return "generic"
    if _contains_describe_anchor(stripped):
        return "describe"
    if _looks_like_snapshot(stripped):
        return "snapshot"
    if _looks_like_json(stripped):
        return "json"
    first_line = stripped.splitlines()[0]
    if starts_new_event(first_line):
        return "event"
    return "generic"


def looks_like_json_array_start(line: str) -> bool:
    stripped = line.lstrip()
    if not stripped.startswith("["):
        return False

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return True

    remainder = stripped[1:].lstrip()
    if not remainder:
        return True

    first = remainder[0]
    if first in "{[\"":
        return stripped.rstrip().endswith(",")
    if first == "]":
        return remainder[1:].strip() == ""
    if first in "tfn":
        token_chars: list[str] = []
        index = 0
        while index < len(remainder):
            char = remainder[index]
            if char.isspace() or char in ",]":
                break
            token_chars.append(char)
            index += 1
        token = "".join(token_chars)
        next_sig = remainder[index:].lstrip()[:1] if index < len(remainder) else ""
        return token in {"true", "false", "null"} and next_sig in {",", "]", ""}
    if first == "-" or first.isdigit():
        token_chars: list[str] = []
        index = 0
        while index < len(remainder):
            char = remainder[index]
            if char.isspace() or char in ",]":
                break
            token_chars.append(char)
            index += 1
        token = "".join(token_chars)
        next_sig = remainder[index:].lstrip()[:1] if index < len(remainder) else ""
        return bool(token and _JSON_NUMBER_RE.fullmatch(token) and next_sig in {",", "]", ""})

    return False


def _contains_describe_anchor(text: str) -> bool:
    for line in text.splitlines():
        for anchor in _DESCRIBE_ANCHORS:
            if line.startswith(anchor):
                return True
    return False


def _looks_like_snapshot(text: str) -> bool:
    for line in text.splitlines():
        upper = line.upper()
        if re.match(r"^NAMESPACE\s+NAME\s+READY\s+STATUS\b", upper):
            return True
        if re.match(r"^NAMESPACE\s+NAME\s+STATUS\b", upper):
            return True
        if re.match(r"^NAME\s+READY\s+STATUS\b", upper):
            return True
        if re.match(r"^NAME\s+STATUS\b", upper):
            return True
    return False


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped.startswith(("{", "[")) or not text.rstrip().endswith(("}", "]")):
        return False
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, (dict, list))
