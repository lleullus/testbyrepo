from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import unittest

from iis_observatory.history import collect_history


@unittest.skipUnless(shutil.which("git"), "git is required")
class HistoryTests(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_detects_status_transition(self) -> None:
        with TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_git(repo, "init", "-q")
            ticket = repo / "docs/planning/work/demo/tickets/TICKET-001.md"
            ticket.parent.mkdir(parents=True)
            ticket.write_text("# TKT-001\nStatus: draft\n", encoding="utf-8")
            self.run_git(repo, "add", ".")
            self.run_git(repo, "commit", "-qm", "add draft ticket")
            ticket.write_text("# TKT-001\nStatus: ready\n", encoding="utf-8")
            self.run_git(repo, "add", ".")
            self.run_git(repo, "commit", "-qm", "ready ticket")

            events = collect_history(repo, limit=5)
            self.assertGreaterEqual(len(events), 2)
            latest = events[0]
            self.assertEqual(latest.subject, "ready ticket")
            self.assertEqual(len(latest.transitions), 1)
            self.assertEqual(latest.transitions[0].before, "draft")
            self.assertEqual(latest.transitions[0].after, "ready")
            self.assertEqual(latest.transitions[0].category, "canonical")

    def test_separates_adaptive_and_observatory_files(self) -> None:
        with TemporaryDirectory() as temp:
            repo = Path(temp)
            self.run_git(repo, "init", "-q")
            adaptive = repo / "docs/planning/adaptive/current/ADAPTIVE-PLANNING-MANDATE.md"
            observatory = repo / "docs/planning/observatory/PROJECT-OVERVIEW.md"
            adaptive.parent.mkdir(parents=True)
            observatory.parent.mkdir(parents=True)
            adaptive.write_text("# Mandate\nStatus: active\n", encoding="utf-8")
            observatory.write_text(
                "# Overview\nSnapshot-Freshness: current-at-generation\n",
                encoding="utf-8",
            )
            self.run_git(repo, "add", ".")
            self.run_git(repo, "commit", "-qm", "add derived planning records")

            events = collect_history(repo, limit=1)
            self.assertEqual(len(events), 1)
            event = events[0]
            self.assertEqual(event.transitions[0].category, "adaptive")
            self.assertIn(
                "docs/planning/observatory/PROJECT-OVERVIEW.md",
                event.to_dict()["files_by_category"]["observatory"],
            )


if __name__ == "__main__":
    unittest.main()
