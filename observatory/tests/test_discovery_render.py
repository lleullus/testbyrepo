from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from helpers import RepoBuilder
from iis_observatory.discovery import (
    discover_repositories,
    display_name,
    is_git_repository,
    is_git_worktree,
)
from iis_observatory.render import render_overview, render_overview_markdown
from iis_observatory.scanner import scan_repository


class DiscoveryAndRenderTests(unittest.TestCase):
    def test_discovers_nested_repositories(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            first = RepoBuilder(root, "tax")
            first.scope()
            second = RepoBuilder(root / "happy", "ima2")
            second.scope()
            (root / "not-a-project").mkdir()

            repos = discover_repositories(root, max_depth=4)
            self.assertEqual(repos, sorted([first.repo.resolve(), second.repo.resolve()]))
            self.assertEqual(display_name(second.repo, root), "happy/ima2")

    def test_excludes_non_git_discovery_root_even_when_it_has_planning(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs" / "planning").mkdir(parents=True)
            child = RepoBuilder(root, "tax")
            child.scope()

            self.assertFalse(is_git_repository(root))
            self.assertEqual(discover_repositories(root), [child.repo.resolve()])

    def test_includes_git_discovery_root_when_it_has_planning(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs" / "planning").mkdir(parents=True)
            (root / ".git").mkdir()

            self.assertTrue(is_git_repository(root))
            self.assertEqual(discover_repositories(root), [root.resolve()])

    def test_excludes_linked_worktrees_by_default_and_can_include_them(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            main = RepoBuilder(root, "x.com")
            main.scope()
            worktree = RepoBuilder(main.repo / "worktrees", "feature", git=False)
            worktree.scope()
            worktree.write(
                ".git",
                f"gitdir: {main.repo / '.git' / 'worktrees' / 'feature'}\n",
            )

            self.assertTrue(is_git_worktree(worktree.repo))
            self.assertEqual(discover_repositories(root), [main.repo.resolve()])
            self.assertEqual(
                discover_repositories(root, include_worktrees=True),
                sorted([main.repo.resolve(), worktree.repo.resolve()]),
            )

    def test_does_not_treat_submodule_gitfile_as_worktree(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            submodule = RepoBuilder(root, "submodule", git=False)
            submodule.scope()
            submodule.write(".git", "gitdir: ../.git/modules/submodule\n")

            self.assertFalse(is_git_worktree(submodule.repo))
            self.assertEqual(discover_repositories(root), [submodule.repo.resolve()])

    def test_overview_contains_required_columns_and_summary(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ready = RepoBuilder(root, "tax")
            ready.scope()
            ready.spec()
            ready.ticket(1, "ready")
            planning = RepoBuilder(root, "ima2")
            planning.scope("INC-012", "job")
            states = [
                scan_repository(ready.repo, repository_name="tax"),
                scan_repository(planning.repo, repository_name="ima2"),
            ]

            output = render_overview(states, color=False, terminal_width=120)
            self.assertIn("IIS PROJECT OVERVIEW", output)
            self.assertIn("Unit", output)
            self.assertIn("State", output)
            self.assertIn("Next", output)
            self.assertIn("TKT-001 구현", output)
            self.assertIn("Ready 1", output)

    def test_overview_unit_uses_authored_increment_title(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "x.com")
            builder.scope("INC-003", "highlights", "WP-001")
            builder.write(
                "docs/planning/scope-shaping/current/INCREMENT-003.md",
                """
# INC-003: Trader Jesse Highlights Decision Evidence Full Coverage
Status: ready-for-matt
Parent-Work-Package: WP-001
Suggested-Work-Slug: highlights
""",
            )
            builder.spec("highlights", source_increment="INC-003")
            builder.ticket(1, "ready", slug="highlights", source_increment="INC-003")

            state = scan_repository(builder.repo)
            output = render_overview_markdown([state])
            self.assertIn("INC-003 · Trader Jesse Highlights Decision Evidence Full Coverage", output)
            self.assertNotIn("INC-003 · INC-003", output)

    def test_overview_direct_work_uses_authored_spec_title(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "ima2_http")
            builder.write(
                "docs/planning/work/live-image-gallery/SPEC.md",
                """
# ima2-http 연속 이미지 작업 뷰
Status: approved
Source-Increment: None
""",
            )
            builder.ticket(1, "done", slug="live-image-gallery", source_increment=None)

            state = scan_repository(builder.repo)
            output = render_overview_markdown([state])
            self.assertIn("work · ima2-http 연속 이미지 작업 뷰", output)
            self.assertNotIn("work · live-image-gallery", output)

    def test_narrow_overview_preserves_follow_up_candidates(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "dc-ai-tier")
            builder.scope("INC-004", "current-work", "WP-001")
            builder.write(
                "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
                """
# Scope Shaping Result
Status: confirmed
Work-Package: WP-001
Selected-Increment: INC-004
Suggested-Work-Slug: current-work

## Outcome Horizon

### Foundation
- WP-001

### Expansion
- WP-002
- WP-003
""",
            )
            for identifier, title in (("WP-002", "Explorer"), ("WP-003", "Automation")):
                builder.write(
                    f"docs/planning/scope-shaping/current/work-packages/{identifier}.md",
                    f"# {identifier}: {title}\nStatus: scoped\nWork-Package: {identifier}",
                )
            builder.spec("current-work", source_increment="INC-004")
            builder.ticket(1, "done", slug="current-work", source_increment="INC-004")

            state = scan_repository(builder.repo)
            output = render_overview([state], color=False, terminal_width=80)
            self.assertIn("Repository", output)
            self.assertIn("Unit", output)
            self.assertIn("Tkts", output)
            self.assertIn("State", output)
            self.assertIn("Scope Shaper [WP-002, WP-003]", output)
            self.assertIn("dc-ai-tier", output)
            self.assertIn("INC-004", output)
            self.assertIn("1/1", output)
            self.assertIn("COMPLETE", output)

    def test_markdown_overview_is_valid_table(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope()
            state = scan_repository(builder.repo)
            output = render_overview_markdown([state])
            self.assertIn("| Repository | Unit | Tickets | State | Next |", output)
            self.assertIn("| repo |", output)


if __name__ == "__main__":
    unittest.main()
