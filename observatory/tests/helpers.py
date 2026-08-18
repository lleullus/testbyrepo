from __future__ import annotations

from pathlib import Path


class RepoBuilder:
    def __init__(self, root: Path, name: str = "repo", *, git: bool = True) -> None:
        self.repo = root / name
        self.planning = self.repo / "docs" / "planning"
        self.planning.mkdir(parents=True, exist_ok=True)
        if git:
            (self.repo / ".git").mkdir(exist_ok=True)

    def write(self, relative: str, text: str) -> Path:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return path

    def scope(
        self,
        increment: str | None = "INC-001",
        slug: str | None = "demo-work",
        work_package: str = "WP-001",
        status: str = "confirmed",
        *,
        increment_title: str | None = None,
    ) -> None:
        selected = f"Selected-Increment: {increment}\n" if increment else ""
        suggested = f"Suggested-Work-Slug: {slug}\n" if slug else ""
        self.write(
            "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
            f"""
# Scope Shaping Result
Status: {status}
Work-Package: {work_package}
{selected}{suggested}
""",
        )
        self.work_package(work_package)
        if increment:
            self.increment(
                increment,
                slug=slug,
                work_package=work_package,
                title=increment_title,
            )

    def work_package(
        self,
        identifier: str = "WP-001",
        status: str = "scoped",
        *,
        title: str | None = None,
    ) -> None:
        number = identifier.split("-")[-1]
        heading = title or f"{identifier} Work package"
        self.write(
            f"docs/planning/scope-shaping/current/WORK-PACKAGE-{number}.md",
            f"""
# {heading}
Status: {status}
Work-Package: {identifier}
""",
        )

    def increment(
        self,
        identifier: str = "INC-001",
        *,
        status: str = "ready-for-matt",
        slug: str | None = "demo-work",
        work_package: str = "WP-001",
        title: str | None = None,
    ) -> None:
        number = identifier.split("-")[-1]
        suggested = f"Suggested-Work-Slug: {slug}\n" if slug else ""
        heading = title or f"{identifier} Increment"
        self.write(
            f"docs/planning/scope-shaping/current/INCREMENT-{number}.md",
            f"""
# {heading}
Status: {status}
Parent-Work-Package: {work_package}
{suggested}
""",
        )

    def spec(
        self,
        slug: str = "demo-work",
        *,
        status: str = "approved",
        source_increment: str | None = "INC-001",
        title: str = "Demo Spec",
    ) -> None:
        source = (
            f"Source-Increment: {source_increment}\n"
            if source_increment is not None
            else "Source-Increment: None\n"
        )
        self.write(
            f"docs/planning/work/{slug}/SPEC.md",
            f"""
# {title}
Status: {status}
{source}
""",
        )

    def ticket(
        self,
        number: int,
        status: str,
        *,
        slug: str = "demo-work",
        source_increment: str | None = "INC-001",
        include_status: bool = True,
        identifier: str | None = None,
    ) -> None:
        ticket_id = identifier or f"TKT-{number:03d}"
        status_line = f"Status: {status}\n" if include_status else ""
        source = (
            f"Source-Increment: {source_increment}\n"
            if source_increment is not None
            else "Source-Increment: None\n"
        )
        self.write(
            f"docs/planning/work/{slug}/tickets/TICKET-{number:03d}.md",
            f"""
# {ticket_id} Ticket
{status_line}{source}
""",
        )
