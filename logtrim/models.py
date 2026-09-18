"""Log trimmer domain models.

Mappings from seed.yaml ontology_schema:
  - LogLine: raw, pattern, timestamp
  - LogPattern: pattern, count, sample, first_seen, last_seen
  - TrimmedLog: original_count, trimmed_count, compression_ratio, patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogLine:
    """Parsed representation of a single log line.

    Fields (seed.yaml ontology_schema):
        raw     (string)  : Original raw log line
        pattern (string)  : Extracted pattern identifier
        timestamp (datetime): Parsed timestamp
    """

    raw: str
    pattern: str
    timestamp: datetime


@dataclass
class LogPattern:
    """Aggregated pattern statistics.

    Fields (seed.yaml ontology_schema):
        pattern   (string)  : Pattern template string
        count     (int)     : Occurrence count
        sample    (string)  : Representative sample log line
        first_seen (datetime): First occurrence timestamp
        last_seen  (datetime): Last occurrence timestamp
    """

    pattern: str
    count: int
    sample: str
    first_seen: datetime
    last_seen: datetime


@dataclass
class TrimmedLog:
    """Result of log trimming / compression.

    Fields (seed.yaml ontology_schema):
        original_count    (int)      : Total raw log lines
        trimmed_count     (int)      : Number of unique patterns
        compression_ratio (float)    : (1 - trimmed_count / original_count) * 100 (%)
        patterns          (list)     : List of LogPattern instances
    """

    original_count: int
    trimmed_count: int
    compression_ratio: float
    patterns: list[LogPattern] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        original_count: int,
        trimmed_count: int,
        patterns: list[LogPattern],
    ) -> TrimmedLog:
        """Factory method that computes compression_ratio."""
        if original_count == 0:
            compression_ratio = 0.0
        else:
            compression_ratio = (1 - trimmed_count / original_count) * 100
        return cls(
            original_count=original_count,
            trimmed_count=trimmed_count,
            compression_ratio=compression_ratio,
            patterns=patterns,
        )
