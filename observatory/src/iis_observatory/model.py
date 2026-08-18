from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable
import re

__version__ = "0.2.1"
SCHEMA_VERSION = "1.0"
SNAPSHOT_SCHEMA_VERSION = "1.0"


class ArtifactKind(str, Enum):
    SCOPE = "scope"
    WORK_PACKAGE = "work_package"
    INCREMENT = "increment"
    SPEC = "spec"
    TICKET = "ticket"
    UNKNOWN = "unknown"


class Health(str, Enum):
    READY = "READY"
    PLANNING = "PLANNING"
    NEEDS_SCOPE = "NEEDS_SCOPE"
    BLOCKED = "BLOCKED"
    INCONSISTENT = "INCONSISTENT"
    COMPLETE = "COMPLETE"
    STALE = "STALE"
    NO_IIS = "NO_IIS"


class Stage(str, Enum):
    DELIVERY = "delivery"
    TICKETS = "tickets"
    PLANNING = "planning"
    SHAPING = "shaping"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class NextWorkKind(str, Enum):
    TICKET_IMPLEMENT = "ticket_implement"
    TICKET_UNBLOCK = "ticket_unblock"
    TICKET_REVIEW = "ticket_review"
    TO_TICKETS = "to_tickets"
    TO_SPEC = "to_spec"
    ASK_MATT = "ask_matt"
    SCOPE_SHAPER = "scope_shaper"
    CONSISTENCY_CHECK = "consistency_check"
    NONE = "none"


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    severity: str = "warning"
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.path:
            data["path"] = self.path
        return data


@dataclass
class Artifact:
    path: Path
    relative_path: str
    kind: ArtifactKind
    identifier: str | None
    status: str | None
    title: str | None
    metadata: dict[str, str]
    references: tuple[str, ...] = ()
    link_targets: tuple[str, ...] = ()
    work_slug: str | None = None
    modified_at: datetime | None = None
    raw_text: str = field(default="", repr=False)

    def ref(self) -> dict[str, Any]:
        return {
            "id": self.identifier,
            "kind": self.kind.value,
            "status": self.status,
            "title": self.title,
            "path": self.relative_path,
            "work_slug": self.work_slug,
            "modified_at": isoformat(self.modified_at),
        }


@dataclass(frozen=True)
class NextWork:
    kind: NextWorkKind
    target_id: str | None
    target_path: str | None
    leaf: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "target_id": self.target_id,
            "target_path": self.target_path,
            "leaf": self.leaf,
            "reason": self.reason,
        }


@dataclass
class ProjectState:
    repository: str
    repository_path: Path
    planning_root: Path | None
    scanned_at: datetime
    stage: Stage
    health: Health
    current_scope: Artifact | None = None
    current_work_package: Artifact | None = None
    current_increment: Artifact | None = None
    current_spec: Artifact | None = None
    current_work_slug: str | None = None
    tickets: list[Artifact] = field(default_factory=list)
    next_candidate_work_packages: list[Artifact] = field(default_factory=list)
    deferred_work_packages: list[Artifact] = field(default_factory=list)
    next_work: NextWork = field(
        default_factory=lambda: NextWork(
            NextWorkKind.NONE, None, None, "none", "No next planning unit is established."
        )
    )
    issues: list[Issue] = field(default_factory=list)
    last_activity: datetime | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def ticket_counts(self) -> dict[str, int]:
        counts = {"total": len(self.tickets), "done": 0, "ready": 0, "blocked": 0, "draft": 0, "other": 0}
        for ticket in self.tickets:
            status = ticket.status or "other"
            if status in counts:
                counts[status] += 1
            else:
                counts["other"] += 1
        return counts

    @property
    def completed_tickets(self) -> list[Artifact]:
        return [ticket for ticket in self.tickets if ticket.status == "done"]

    @property
    def remaining_tickets(self) -> list[Artifact]:
        return [ticket for ticket in self.tickets if ticket.status != "done"]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "repository": self.repository,
            "repository_path": str(self.repository_path),
            "planning_root": str(self.planning_root) if self.planning_root else None,
            "scanned_at": isoformat(self.scanned_at),
            "last_activity": isoformat(self.last_activity),
            "stage": self.stage.value,
            "health": self.health.value,
            "current": {
                "scope": self.current_scope.ref() if self.current_scope else None,
                "work_package": self.current_work_package.ref() if self.current_work_package else None,
                "increment": self.current_increment.ref() if self.current_increment else None,
                "spec": self.current_spec.ref() if self.current_spec else None,
                "work_slug": self.current_work_slug,
            },
            "tickets": {
                "counts": self.ticket_counts,
                "items": [ticket.ref() for ticket in self.tickets],
                "completed": [ticket.identifier or ticket.relative_path for ticket in self.completed_tickets],
                "remaining": [ticket.identifier or ticket.relative_path for ticket in self.remaining_tickets],
            },
            "follow_up": {
                "next_candidate_work_packages": [item.ref() for item in self.next_candidate_work_packages],
                "deferred_work_packages": [item.ref() for item in self.deferred_work_packages],
                "next_increment": None,
                "next_increment_status": "not_yet_shaped" if self.next_candidate_work_packages else None,
            },
            "next_work": self.next_work.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "evidence": self.evidence,
        }


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat(timespec="seconds")


def natural_id_key(value: str | None) -> tuple[str, int, str]:
    if not value:
        return ("~", 10**9, "")
    match = re.search(r"(?i)\b(WP|INC|TKT|TICKET|SPEC)[-_]?(\d+)\b", value)
    if not match:
        return (value.upper(), 10**9, value)
    prefix = match.group(1).upper().replace("TICKET", "TKT")
    return (prefix, int(match.group(2)), value)


def newest_timestamp(artifacts: Iterable[Artifact]) -> datetime | None:
    values = [artifact.modified_at for artifact in artifacts if artifact.modified_at is not None]
    return max(values) if values else None
