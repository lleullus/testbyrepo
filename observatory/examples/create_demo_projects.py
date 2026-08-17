from __future__ import annotations

from pathlib import Path
import shutil
import sys


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def scope(repo: Path, inc: str | None, slug: str | None, wp: str = "WP-001") -> None:
    selected = f"Selected-Increment: {inc}\n" if inc else ""
    suggested = f"Suggested-Work-Slug: {slug}\n" if slug else ""
    write(
        repo / "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
        f"""
# Scope Shaping Result
Status: confirmed
Work-Package: {wp}
{selected}{suggested}
""",
    )
    write(
        repo / f"docs/planning/scope-shaping/current/WORK-PACKAGE-{wp.split('-')[-1]}.md",
        f"""
# {wp} Demo outcome
Status: scoped
""",
    )
    if inc:
        write(
            repo / f"docs/planning/scope-shaping/current/INCREMENT-{inc.split('-')[-1]}.md",
            f"""
# {inc} Demo increment
Status: ready-for-matt
Parent-Work-Package: {wp}
Suggested-Work-Slug: {slug}
""",
        )


def spec(repo: Path, slug: str, inc: str, status: str = "approved") -> None:
    write(
        repo / f"docs/planning/work/{slug}/SPEC.md",
        f"""
# Demo Spec
Status: {status}
Source-Increment: {inc}
""",
    )


def ticket(repo: Path, slug: str, number: int, status: str, inc: str) -> None:
    write(
        repo / f"docs/planning/work/{slug}/tickets/TICKET-{number:03d}.md",
        f"""
# TKT-{number:03d} Demo ticket
Status: {status}
Source-Increment: {inc}
""",
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".demo-projects").resolve()
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    tax = root / "tax"
    scope(tax, "INC-004", "vat-readback", "WP-002")
    spec(tax, "vat-readback", "INC-004")
    for number in (1, 2, 3):
        ticket(tax, "vat-readback", number, "done", "INC-004")
    ticket(tax, "vat-readback", 4, "ready", "INC-004")
    ticket(tax, "vat-readback", 5, "ready", "INC-004")

    ima2 = root / "ima2"
    scope(ima2, "INC-012", "job-inspection", "WP-003")

    oracle = root / "oracle"
    scope(oracle, None, None, "WP-003")

    watcher = root / "watcher"
    scope(watcher, "INC-007", "release-alert", "WP-002")
    spec(watcher, "release-alert", "INC-007")
    ticket(watcher, "release-alert", 1, "done", "INC-007")
    ticket(watcher, "release-alert", 2, "done", "INC-007")
    ticket(watcher, "release-alert", 3, "blocked", "INC-007")
    ticket(watcher, "release-alert", 4, "ready", "INC-007")

    legacy = root / "legacy-api"
    scope(legacy, "INC-002", "legacy-cleanup", "WP-001")
    spec(legacy, "legacy-cleanup", "INC-002")
    for number in range(1, 5):
        ticket(legacy, "legacy-cleanup", number, "done", "INC-002")

    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
