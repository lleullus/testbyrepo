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
    category: str = "canonical"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "path": self.path,
            "before": self.before,
            "after": self.after,
            "category": self.category,
        }


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
            "files_by_category": _files_by_category(self.files),
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
            transitions.append(
                StatusTransition(path, before, after, _history_category(path))
            )
    return transitions


def render_history(events: list[HistoryEvent]) -> str:
    lines = ["IIS PLANNING HISTORY", "────────────────────"]
    if not events:
        lines.append("No Git history exists for docs/planning.")
        return "\n".join(lines) + "\n"
    for event in events:
        lines.append(f"{event.timestamp}  {event.commit[:8]}  {event.subject}")
        by_transition: dict[str, list[StatusTransition]] = {
            "canonical": [],
            "adaptive": [],
            "observatory": [],
        }
        for transition in event.transitions:
            by_transition.setdefault(transition.category, []).append(transition)
        labels = {
            "canonical": "Canonical planning transitions",
            "adaptive": "Adaptive provenance transitions",
            "observatory": "Observatory projection transitions",
        }
        for category in ("canonical", "adaptive", "observatory"):
            transitions = by_transition.get(category, [])
            if not transitions:
                continue
            lines.append(f"  {labels[category]}:")
            for transition in transitions:
                before = transition.before or "∅"
                after = transition.after or "∅"
                lines.append(f"    {transition.path}: {before} → {after}")

        grouped_files = _files_by_category(event.files)
        transitioned_paths = {transition.path for transition in event.transitions}
        for category, label in (
            ("adaptive", "Adaptive provenance files"),
            ("observatory", "Observatory projection files"),
            ("canonical", "Canonical planning files"),
        ):
            files = [
                path
                for path in grouped_files.get(category, [])
                if path not in transitioned_paths
            ]
            if files:
                lines.append(f"  {label}: {_preview(files)}")
        if not event.transitions and not event.files:
            lines.append("  planning files: none")
    return "\n".join(lines) + "\n"


def _history_category(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("docs/planning/adaptive/"):
        return "adaptive"
    if normalized.startswith("docs/planning/observatory/"):
        return "observatory"
    return "canonical"


def _files_by_category(files: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {
        "canonical": [],
        "adaptive": [],
        "observatory": [],
    }
    for path in files:
        grouped[_history_category(path)].append(path)
    return grouped


def _preview(files: list[str], limit: int = 3) -> str:
    preview = ", ".join(files[:limit])
    if len(files) > limit:
        preview += f" (+{len(files) - limit})"
    return preview or "none"
