"""Public data models and resource limits."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime


class ResourceLimit(RuntimeError):
    """Processing stopped without silently dropping input."""


@dataclass(frozen=True, slots=True)
class Config:
    threshold: float = 0.85
    min_margin: float = 0.02
    max_candidates: int = 64
    depth: int = 4
    cache_size: int = 256
    sqlite_cache_kib: int = 8192
    max_event_bytes: int = 65536
    max_event_lines: int = 256
    max_tokens: int = 2048
    max_input_bytes: int = 0
    max_clusters: int = 0
    multiline: bool = True
    sample_mode: str = "none"
    sample_chars: int = 512
    syslog_year: int | None = None
    timezone_minutes: int = 0

    def __post_init__(self):
        for name in ("threshold", "min_margin"):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if self.threshold == 0:
            raise ValueError("threshold must be greater than zero")
        for name in ("max_candidates", "depth", "cache_size", "sqlite_cache_kib",
                     "max_event_bytes", "max_event_lines", "max_tokens", "sample_chars"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if self.depth > 16:
            raise ValueError("depth must not exceed 16")
        if (type(self.max_input_bytes) is not int or type(self.max_clusters) is not int
                or self.max_input_bytes < 0 or self.max_clusters < 0):
            raise ValueError("optional limits must be nonnegative")
        if self.sample_mode not in {"none", "redacted", "raw"}:
            raise ValueError("invalid sample mode")
        if self.syslog_year is not None and not 1 <= self.syslog_year <= 9999:
            raise ValueError("invalid syslog year")
        if not -1439 <= self.timezone_minutes <= 1439:
            raise ValueError("invalid timezone offset")

    def digest(self, rules: list[dict]) -> str:
        data = json.dumps([asdict(self), rules], sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class Event:
    text: str
    physical_lines: int


@dataclass(frozen=True, slots=True)
class NormalizedEvent:
    pattern: str
    tokens: tuple[str, ...]
    anchors: tuple[str, ...]
    parser: str
    timestamp: datetime | None
    captures: tuple[tuple[str, float], ...] = ()

    def key(self) -> str:
        return json.dumps([self.parser, self.anchors, self.pattern], ensure_ascii=True)


@dataclass(slots=True)
class LogPattern:
    pattern: str
    count: int
    sample: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None


@dataclass(slots=True)
class Cluster:
    id: int
    pattern: str
    leader: list[str]
    template: list[str]
    parser: str
    anchors: list[str]
    count: int = 0
    baseline: int = 0
    current: int = 0
    first_seen: str | None = None
    last_seen: str | None = None
    sample: str | None = None
    slots: dict[str, dict] = field(default_factory=dict)

    def observe(self, event: NormalizedEvent, phase: str, sample: str | None):
        self.count += 1
        if phase in {"baseline", "current"}:
            setattr(self, phase, getattr(self, phase) + 1)
        if self.sample is None:
            self.sample = sample
        if event.timestamp is not None:
            stamp = event.timestamp.isoformat(timespec="microseconds")
            self.first_seen = min(self.first_seen or stamp, stamp)
            self.last_seen = max(self.last_seen or stamp, stamp)
        for name, value in event.captures:
            s = self.slots.setdefault(name, {"count": 0, "min": value,
                                            "max": value, "mean": 0.0})
            s["count"] += 1
            s["min"], s["max"] = min(s["min"], value), max(s["max"], value)
            n = s["count"]
            s["mean"] = s["mean"] * ((n - 1) / n) + value / n