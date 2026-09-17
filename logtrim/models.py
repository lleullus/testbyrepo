from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogicalRecord:
    text: str
    family: str
    start_line: int
    end_line: int


@dataclass
class Group:
    pattern: str
    sample: str
    count: int
    first_seen: str
    last_seen: str
