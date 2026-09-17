from __future__ import annotations

from typing import Iterable

from logtrim.models import Group


def render_groups(groups: Iterable[Group]) -> str:
    """Render grouped events into deterministic human-readable blocks."""

    blocks: list[str] = []
    for group in sorted(groups, key=lambda group: (-group.count, group.pattern)):
        blocks.append(f"[{group.count}] {group.pattern}")
        blocks.append(f"count: {group.count}")
        blocks.append(f"sample: {group.sample}")
        blocks.append(f"first_seen: {group.first_seen}")
        blocks.append(f"last_seen: {group.last_seen}")
        blocks.append("")  # blank line between groups

    return "\n".join(blocks).rstrip()
