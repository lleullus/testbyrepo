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


if __name__ == "__main__":
    unittest.main()
