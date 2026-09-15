from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from test_direct_scope import DirectScopeFixtures
from iis_observatory.discovery import discover_repositories, display_name, is_git_repository
from iis_observatory.render import render_overview, render_overview_markdown
from iis_observatory.scanner import scan_repository


class DiscoveryAndRenderTests(unittest.TestCase):
    def test_discovers_nested_direct_scope_repository(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "tax"
            DirectScopeFixtures(repo).scope()
            self.assertEqual(discover_repositories(root), [repo.resolve()])
            self.assertTrue(is_git_repository(repo))
            self.assertEqual(display_name(repo, root), "tax")

    def test_non_git_discovery_root_is_not_a_project(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs/planning").mkdir(parents=True)
            self.assertEqual(discover_repositories(root), [])

    def test_overview_exposes_current_scope_without_legacy_pointer(self) -> None:
        with TemporaryDirectory() as temp:
            repo = Path(temp) / "tax"
            DirectScopeFixtures(repo).scope()
            state = scan_repository(repo)
            output = render_overview([state], terminal_width=120)
            self.assertIn("Scope · member", output)
            self.assertNotIn("Ask Matt", output)

    def test_markdown_overview_preserves_direct_scope_state(self) -> None:
        with TemporaryDirectory() as temp:
            repo = Path(temp) / "tax"
            DirectScopeFixtures(repo).scope()
            output = render_overview_markdown([scan_repository(repo)])
            self.assertIn("| tax |", output)
            self.assertIn("PLANNING", output)


if __name__ == "__main__":
    unittest.main()
