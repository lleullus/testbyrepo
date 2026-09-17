import re
from collections import defaultdict
from typing import Iterable, Sequence

_HASHISH_SEGMENT = re.compile(r"^[a-f0-9]{5,10}$", re.IGNORECASE)


def _rows(lines: Sequence[str]) -> list[list[str]]:
    return [line.split() for line in lines if line.strip()]


def _workload_from_name(name: str) -> str:
    parts = name.split("-")
    if len(parts) >= 3 and parts[-1].isdigit():
        return "-".join(parts[:-1]) or name
    if len(parts) >= 3 and _HASHISH_SEGMENT.match(parts[-2]) and _HASHISH_SEGMENT.match(parts[-1]):
        return "-".join(parts[:-2]) or name
    if len(parts) >= 3 and _HASHISH_SEGMENT.match(parts[-2]) and len(parts[-1]) <= 5:
        return "-".join(parts[:-2]) or name
    if len(parts) > 1:
        return name
    return name


def _format_state_block(state_counts: dict[str, int]) -> str:
    parts = []
    for state in sorted(state_counts):
        count = state_counts[state]
        label = "pods" if count != 1 else "pod"
        parts.append(f"{state} ({count} {label})")
    return ", ".join(parts)


def summarize_snapshot(lines: Iterable[str]) -> str:
    raw_lines = [line.rstrip("\n") for line in lines]
    parsed = _rows(raw_lines)
    if not parsed:
        return ""

    header, *rows = parsed
    header_map = {name.upper(): idx for idx, name in enumerate(header)}
    namespace_idx = header_map.get("NAMESPACE")
    name_idx = header_map.get("NAME", 0)
    status_idx = header_map.get("STATUS", 1)

    has_ready = "READY" in header_map
    has_restarts = "RESTARTS" in header_map
    is_pod_table = has_ready or has_restarts
    is_node_table = "ROLES" in header_map or "VERSION" in header_map

    if is_pod_table:
        workload_states: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for row in rows:
            if len(row) <= status_idx or len(row) <= name_idx:
                continue
            name = row[name_idx]
            state = row[status_idx]
            workload = _workload_from_name(name)
            if namespace_idx is not None and len(row) > namespace_idx:
                workload = f"{row[namespace_idx]}/{workload}"
            workload_states[workload][state] += 1

        if not workload_states:
            return ""

        if namespace_idx is not None:
            blocks = ["Pods by namespace/workload and state:"]
        else:
            blocks = ["Pods by workload and state:"]
        for workload in sorted(workload_states):
            blocks.append(f"- {workload}: {_format_state_block(workload_states[workload])}")
        return "\n".join(blocks)

    if is_node_table:
        blocks = ["Nodes:"]
        for row in rows:
            if len(row) <= status_idx or len(row) <= name_idx:
                continue
            blocks.append(f"- {row[name_idx]}: {row[status_idx]}")
        return "\n".join(blocks) if len(blocks) > 1 else ""

    return "\n".join(raw_lines)
