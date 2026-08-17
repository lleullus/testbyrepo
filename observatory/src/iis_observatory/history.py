from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import subprocess

from .markdown import normalize_status


class HistoryError(RuntimeError):
    pass


@dataclass
class StatusTransition:
    path: str
    before: str | None
    after: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {"path": self.path, "before": self.before, "after": self.after}


@dataclass
class HistoryEvent:
    commit: str
    timestamp: str
    author: str
    subject: str
    files: list[str] = field(default_factory=list)
    transitions: list[StatusTransition] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "commit": self.commit,
            "timestamp": self.timestamp,
            "author": self.author,
            "subject": self.subject,
            "files": self.files,
            "status_transitions": [item.to_dict() for item in self.transitions],
        }


def collect_history(repository: Path, limit: int = 20) -> list[HistoryEvent]:
    repository = repository.expanduser().resolve()
    _run_git(repository, ["rev-parse", "--show-toplevel"])
    format_string = "%H%x1f%cI%x1f%an%x1f%s"
    output = _run_git(
        repository,
        ["log", f"--max-count={limit}", f"--format={format_string}", "--", "docs/planning"],
    )
    events: list[HistoryEvent] = []
    for line in output.splitlines():
        fields = line.split("\x1f", 3)
        if len(fields) != 4:
            continue
        commit, timestamp, author, subject = fields
        names = _run_git(
            repository,
            ["show", "--format=", "--name-only", commit, "--", "docs/planning"],
        )
        files = [name.strip() for name in names.splitlines() if name.strip()]
        patch = _run_git(
            repository,
            ["show", "--format=", "--unified=0", commit, "--", "docs/planning"],
        )
        transitions = _parse_transitions(patch)
        events.append(HistoryEvent(commit, timestamp, author, subject, files, transitions))
    return events


def _run_git(repository: Path, args: list[str]) -> str:
    command = ["git", "-C", str(repository), *args]
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise HistoryError("git executable was not found") from exc
    if completed.returncode != 0:
        message = completed.stderr.strip() or "git command failed"
        raise HistoryError(message)
    return completed.stdout


def _parse_transitions(patch: str) -> list[StatusTransition]:
    current_path: str | None = None
    removed: dict[str, list[str]] = {}
    added: dict[str, list[str]] = {}
    status_pattern = re.compile(r"(?i)(?:^|[-*]\s*)Status\s*:\s*(.+?)\s*$")

    for line in patch.splitlines():
        if line.startswith("diff --git "):
            match = re.match(r"diff --git a/(.+?) b/(.+)$", line)
            current_path = match.group(2) if match else None
            continue
        if current_path is None or line.startswith(("+++", "---")):
            continue
        if not line.startswith(("+", "-")):
            continue
        match = status_pattern.search(line[1:].strip())
        if not match:
            continue
        value = normalize_status(match.group(1)) or match.group(1).strip()
        target = added if line.startswith("+") else removed
        target.setdefault(current_path, []).append(value)

    transitions: list[StatusTransition] = []
    for path in sorted(set(removed) | set(added)):
        before = removed.get(path, [None])[-1]
        after = added.get(path, [None])[-1]
        if before != after:
            transitions.append(StatusTransition(path, before, after))
    return transitions


def render_history(events: list[HistoryEvent]) -> str:
    lines = ["IIS PLANNING HISTORY", "────────────────────"]
    if not events:
        lines.append("No Git history exists for docs/planning.")
        return "\n".join(lines) + "\n"
    for event in events:
        lines.append(f"{event.timestamp}  {event.commit[:8]}  {event.subject}")
        for transition in event.transitions:
            before = transition.before or "∅"
            after = transition.after or "∅"
            lines.append(f"  {transition.path}: {before} → {after}")
        if not event.transitions:
            preview = ", ".join(event.files[:3])
            if len(event.files) > 3:
                preview += f" (+{len(event.files) - 3})"
            lines.append(f"  planning files: {preview or 'none'}")
    return "\n".join(lines) + "\n"
