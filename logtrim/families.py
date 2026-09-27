"""Streaming reducers for kubectl snapshots and describe records."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass

from .io_utils import Event
from .models import Config, ResourceLimit


@dataclass(frozen=True, slots=True)
class FamilyRecord:
    """One reduced family item; ``text`` retains detail, ``pattern`` is its floor."""

    text: str
    pattern: str
    parser: str
    physical_lines: int
    family_state: str | None = None


@dataclass(frozen=True, slots=True)
class SnapshotSpec:
    columns: tuple[str, ...]
    kind: str


_FIELD = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /_.-]*):\s*(.*)$")
_NAME_START = re.compile(r"^\s*Name:\s*(.+?)\s*$", re.I)
_REPLICA_POD = re.compile(r"^(.*)-[a-z0-9]{8,10}-[a-z0-9]{5}$", re.I)
_STATEFUL_POD = re.compile(r"^(.*)-\d+$")
_RANDOM_POD = re.compile(r"^(.*)-[a-z0-9]{5}$", re.I)
_SECTION_KEYS = {"labels", "annotations", "conditions", "events"}
_DESCRIBE_KEYS = {
    "name": "name", "namespace": "namespace", "labels": "labels",
    "annotations": "annotations", "conditions": "conditions", "events": "events",
    "status": "status", "phase": "phase", "ready": "ready", "state": "state",
    "reason": "reason", "node": "node", "ip": "ip", "ips": "ips",
    "restart count": "restart_count", "restartcount": "restart_count",
    "qos class": "qos_class", "qosclass": "qos_class", "roles": "roles",
    "internal ip": "internal_ip", "internalip": "internal_ip",
    "operating system": "operating_system", "operatingsystem": "operating_system",
    "kubelet version": "kubelet_version", "kubeletversion": "kubelet_version",
    "container runtime version": "container_runtime_version",
    "containerruntimeversion": "container_runtime_version",
}
_VOLATILE_COLUMNS = {
    "NAME", "AGE", "RESTARTS", "IP", "IPS", "NODE", "NOMINATED NODE",
    "READINESS GATES", "CONTAINER ID",
}


def _split_columns(line: str) -> list[str]:
    parts = re.split(r"\s{2,}", line.strip())
    if len(parts) == 1:
        parts = line.split()
    return [re.sub(r"\s+", " ", part.strip()) for part in parts if part.strip()]


def _snapshot_spec(line: str) -> SnapshotSpec | None:
    columns = tuple(part.upper() for part in _split_columns(line))
    if len(columns) < 3 or len(set(columns)) != len(columns) or "NAME" not in columns:
        return None
    state_columns = {"STATUS", "PHASE", "READY", "AVAILABLE", "CONDITION", "STATE"}
    if not state_columns.intersection(columns):
        return None
    if "STATUS" in columns and "READY" in columns and "RESTARTS" in columns:
        kind = "pods"
    elif "STATUS" in columns and "ROLES" in columns:
        kind = "nodes"
    else:
        kind = "table"
    return SnapshotSpec(columns, kind)


def _workload(name: str) -> str:
    for expression in (_REPLICA_POD, _STATEFUL_POD, _RANDOM_POD):
        match = expression.fullmatch(name)
        if match and match.group(1):
            return match.group(1)
    return name


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def _family_record(text: str, pattern: str, parser: str, physical_lines: int,
                   family_state: str | None = None) -> FamilyRecord:
    return FamilyRecord(text=text, pattern=pattern, parser=parser,
                        physical_lines=physical_lines, family_state=family_state)


def _snapshot_record(line: str, spec: SnapshotSpec, physical_lines: int) -> FamilyRecord | None:
    values = re.split(r"\s{2,}", line.strip())
    if len(values) != len(spec.columns):
        values = line.split()
    if len(values) < len(spec.columns) or values[0].upper() in spec.columns:
        return None
    row = dict(zip(spec.columns, values))
    if not row.get("NAME"):
        return None
    status_key = next((key for key in ("STATUS", "PHASE", "CONDITION", "STATE", "AVAILABLE", "READY")
                       if row.get(key)), None)
    if status_key is None or not re.fullmatch(r"[\w./:+-]+", row[status_key]):
        return None

    name = row["NAME"]
    namespace = row.get("NAMESPACE", "")
    if "/" in name and not namespace:
        namespace, name = name.split("/", 1)
    status = row.get("STATUS") or row.get("PHASE") or row.get("CONDITION") or row.get("STATE") or row.get("AVAILABLE") or row.get("READY", "unknown")
    ready = row.get("READY", "")

    if spec.kind == "pods":
        kind = "pods"
        selected = [("namespace", namespace or "default"), ("workload", _workload(name))]
    elif spec.kind == "nodes":
        kind = "nodes"
        selected = [("status", status), ("roles", row.get("ROLES", "<none>"))]
        if row.get("VERSION"):
            selected.append(("version", row["VERSION"]))
    else:
        kind = "table"
        selected = [(re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_"), value)
                    for column, value in row.items()
                    if column not in _VOLATILE_COLUMNS and value]
        if not selected:
            selected = [("status", status)]

    pattern = f"k8s snapshot {kind} " + " ".join(f"{key}={_quote(value)}" for key, value in selected)
    used = {key for key, _ in selected}
    detail_fields = [(re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_"), value)
                     for column, value in row.items() if value]
    ordered_details = selected + [(key, value) for key, value in detail_fields
                                  if key not in used or key in {"name", "age", "restarts", "ip", "node"}]
    text = f"k8s snapshot {kind} " + " ".join(f"{key}={_quote(value)}" for key, value in ordered_details)
    return _family_record(text, pattern, "k8s_snapshot_" + kind, physical_lines, status)


def _condition_summary(lines: list[str]) -> str:
    conditions = set()
    for line in lines:
        value = line.strip()
        if not value or value.startswith(("<none>", "---")) or value.lower().startswith("type status"):
            continue
        match = re.match(r"^([A-Za-z][\w./-]*)\s*:\s*(True|False|Unknown)\b", value, re.I)
        if match:
            conditions.add(f"{match.group(1)}={match.group(2)}")
            continue
        columns = value.split()
        if len(columns) >= 2 and columns[1] in {"True", "False", "Unknown"}:
            conditions.add(f"{columns[0]}={columns[1]}")
    return ",".join(sorted(conditions)) or "none"


def _event_summary(lines: list[str]) -> str:
    counts = Counter()
    for line in lines:
        columns = line.split()
        if len(columns) < 2 or columns[0] not in {"Normal", "Warning"}:
            continue
        if columns[1].lower() == "reason":
            continue
        counts[(columns[0], columns[1])] += 1
    if not counts:
        return "none"
    return ",".join(f"{kind}:{reason}={count}" for (kind, reason), count in sorted(counts.items()))


def _describe_record(records: list[Event]) -> FamilyRecord | None:
    fields: dict[str, str] = {}
    sections = {key: [] for key in _SECTION_KEYS}
    extras: dict[str, list[str]] = {}
    current_section: str | None = None
    for record in records:
        for line in record.text.splitlines():
            match = _FIELD.match(line)
            if match:
                key = " ".join(match.group(1).lower().split())
                target = _DESCRIBE_KEYS.get(key)
                value = match.group(2).strip()
                if target in _SECTION_KEYS:
                    current_section = target
                    if value:
                        sections[target].append(value)
                elif target:
                    current_section = None
                    fields[target] = value
                elif current_section:
                    sections[current_section].append(line.strip())
                else:
                    current_section = None
                    if value:
                        extras.setdefault(key.replace(" ", "_"), []).append(value)
                continue
            value = line.strip()
            if value and current_section:
                sections[current_section].append(value)

    name = fields.get("name", "")
    namespace = fields.get("namespace", "")
    if not name or not any(sections[key] or key in fields
                           for key in ("labels", "annotations", "conditions", "events")):
        return None

    condition_summary = _condition_summary(sections["conditions"])
    event_summary = _event_summary(sections["events"])
    status = fields.get("status") or fields.get("phase") or fields.get("state") or condition_summary
    if not status:
        status = "unknown"
    if fields.get("roles") or fields.get("operating_system") or fields.get("kubelet_version"):
        kind = "node"
        workload = name
    elif any(key in fields for key in ("node", "restart_count", "qos_class")):
        kind = "pod"
        workload = _workload(name.rsplit("/", 1)[-1])
    else:
        kind = "resource"
        workload = name
    if kind == "pod" and not namespace:
        namespace = "default"

    pattern_fields = [("namespace", namespace), ("workload", workload), ("status", status),
                      ("conditions", condition_summary), ("events", event_summary)]
    prefix = f"k8s describe {kind} "
    pattern = prefix + " ".join(f"{key}={_quote(value)}" for key, value in pattern_fields)
    details: list[tuple[str, str]] = [("name", name), ("labels", " | ".join(sections["labels"])),
                                      ("annotations", " | ".join(sections["annotations"])),
                                      ("conditions_detail", " | ".join(sections["conditions"])),
                                      ("events_detail", " | ".join(sections["events"]))]
    for key in ("node", "ip", "ips", "ready", "state", "reason", "restart_count", "qos_class",
                "roles", "internal_ip", "operating_system", "kubelet_version", "container_runtime_version"):
        if fields.get(key):
            details.append((key, fields[key]))
    for key, values in sorted(extras.items()):
        details.append((key, " | ".join(values)))
    text = prefix + " ".join(f"{key}={_quote(value)}" for key, value in pattern_fields + details)
    return _family_record(text, pattern, "k8s_describe_" + kind,
                          sum(record.physical_lines for record in records), status)


def _describe_start(text: str) -> bool:
    return bool(_NAME_START.match(text))


def _describe_continuation(text: str) -> bool:
    if text[:1].isspace():
        return True
    first_line = text.splitlines()[0] if text else ""
    return bool(_FIELD.match(first_line))


def _flush_describe(records: list[Event], config: Config) -> FamilyRecord | list[Event]:
    line_count = sum(record.physical_lines for record in records)
    byte_count = sum(len(record.text.encode("utf-8")) for record in records)
    if line_count > config.max_event_lines:
        raise ResourceLimit("kubectl describe block exceeds max_event_lines")
    if byte_count > config.max_event_bytes:
        raise ResourceLimit("kubectl describe block exceeds max_event_bytes")
    reduced = _describe_record(records)
    return reduced if reduced is not None else records


def reduce_records(records, config: Config, stats):
    """Detect tabular snapshots and bounded describe blocks while preserving order."""
    snapshot: SnapshotSpec | None = None
    describe: list[Event] = []
    for record in records:
        stats["assembled_records"] += 1
        if describe:
            if _describe_start(record.text):
                flushed = _flush_describe(describe, config)
                if isinstance(flushed, FamilyRecord):
                    stats["family.describe_records"] += 1
                    yield flushed
                else:
                    yield from flushed
                describe = [record]
                snapshot = None
                continue
            if _describe_continuation(record.text):
                describe.append(record)
                if (sum(item.physical_lines for item in describe) > config.max_event_lines
                        or sum(len(item.text.encode("utf-8")) for item in describe) > config.max_event_bytes):
                    raise ResourceLimit("kubectl describe block exceeds configured event limits")
                continue
            flushed = _flush_describe(describe, config)
            if isinstance(flushed, FamilyRecord):
                stats["family.describe_records"] += 1
                yield flushed
            else:
                yield from flushed
            describe = []
            snapshot = None

        if snapshot is not None:
            reduced = _snapshot_record(record.text, snapshot, record.physical_lines)
            if reduced is not None:
                stats["family.snapshot_rows"] += 1
                yield reduced
                continue
            snapshot = None

        detected = _snapshot_spec(record.text)
        if detected is not None:
            snapshot = detected
            stats["family.snapshot_headers"] += 1
            continue
        if _describe_start(record.text):
            describe = [record]
            snapshot = None
            continue
        yield record

    if describe:
        flushed = _flush_describe(describe, config)
        if isinstance(flushed, FamilyRecord):
            stats["family.describe_records"] += 1
            yield flushed
        else:
            yield from flushed
