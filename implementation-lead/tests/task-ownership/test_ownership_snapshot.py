from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "task-ownership-snapshot"
    / "ownership_snapshot.py"
)
SPEC = importlib.util.spec_from_file_location("ownership_snapshot", MODULE_PATH)
assert SPEC and SPEC.loader
ownership_snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ownership_snapshot)


class OwnershipSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.artifacts = Path(self.temporary.name) / "artifacts"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        (self.root / ".git" / "index").write_text("ignored metadata", encoding="utf-8")
        (self.root / ".gitignore").write_text("*.cache\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def capture(self) -> dict[str, object]:
        return ownership_snapshot.capture(self.root)

    def test_preexisting_dirty_and_ignored_files_are_not_worker_delta(self) -> None:
        (self.root / "user.txt").write_text("dirty before", encoding="utf-8")
        (self.root / "state.cache").write_text("ignored by git, not by snapshot", encoding="utf-8")
        before = self.capture()
        (self.root / "worker.txt").write_text("worker", encoding="utf-8")
        after = self.capture()
        delta = ownership_snapshot.compare(before, after, allowed_mutation_scopes=["worker.txt"])
        self.assertEqual(["worker.txt"], delta["changedPaths"])
        self.assertEqual(["worker.txt"], delta["inScopePaths"])
        self.assertEqual("WITHIN_ENVELOPE", delta["scopeState"])
        self.assertEqual("NOT_ESTABLISHED", delta["actorAttribution"])
        self.assertIn("state.cache", before["entries"])
        self.assertNotIn(".git/index", before["entries"])

    def test_out_of_scope_change_requires_reconciliation_without_claiming_actor(self) -> None:
        (self.root / "src").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "src" / "app.py").write_text("before", encoding="utf-8")
        (self.root / "docs" / "note.md").write_text("before", encoding="utf-8")
        before = self.capture()
        (self.root / "src" / "app.py").write_text("after", encoding="utf-8")
        (self.root / "docs" / "note.md").write_text("external", encoding="utf-8")
        after = self.capture()
        delta = ownership_snapshot.compare(before, after, allowed_mutation_scopes=["src/**"])
        self.assertEqual(["src/app.py"], delta["inScopePaths"])
        self.assertEqual(["docs/note.md"], delta["outOfScopePaths"])
        self.assertEqual("OUTSIDE_ENVELOPE", delta["scopeState"])
        self.assertEqual("NOT_ESTABLISHED", delta["actorAttribution"])

    def test_concurrent_scratch_work_is_reported_for_reconciliation(self) -> None:
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("before", encoding="utf-8")
        before = self.capture()
        (self.root / "src" / "app.py").write_text("after", encoding="utf-8")
        ticket = self.root / ".scratch" / "other-work" / "tickets" / "TICKET-001.md"
        ticket.parent.mkdir(parents=True)
        ticket.write_text("planning", encoding="utf-8")
        after = self.capture()
        delta = ownership_snapshot.compare(before, after, allowed_mutation_scopes=["src/**"])
        self.assertEqual(["src/app.py"], delta["inScopePaths"])
        self.assertEqual(
            [
                ".scratch",
                ".scratch/other-work",
                ".scratch/other-work/tickets",
                ".scratch/other-work/tickets/TICKET-001.md",
            ],
            delta["outOfScopePaths"],
        )
        self.assertEqual("OUTSIDE_ENVELOPE", delta["scopeState"])

    def test_compare_cli_returns_reconciliation_signal_for_concurrent_scratch_work(self) -> None:
        (self.root / "src").mkdir()
        app = self.root / "src" / "app.py"
        app.write_text("before", encoding="utf-8")
        before_path = self.artifacts / "before.json"
        after_path = self.artifacts / "after.json"
        ownership_snapshot.write_immutable(self.capture(), before_path)
        app.write_text("after", encoding="utf-8")
        spec = self.root / ".scratch" / "wp-002" / "SPEC.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("planning", encoding="utf-8")
        ownership_snapshot.write_immutable(self.capture(), after_path)

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "compare",
                "--before",
                str(before_path),
                "--after",
                str(after_path),
                "--allow",
                "src/**",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(10, completed.returncode)
        delta = json.loads(completed.stdout)
        self.assertEqual("OUTSIDE_ENVELOPE", delta["scopeState"])
        self.assertEqual("NOT_ESTABLISHED", delta["actorAttribution"])
        self.assertEqual(["src/app.py"], delta["inScopePaths"])
        self.assertIn(".scratch/wp-002/SPEC.md", delta["outOfScopePaths"])

    def test_single_star_does_not_cross_path_segments_for_python_glob(self) -> None:
        self.assertFalse(ownership_snapshot._allowed("src/deep/x.py", ("src/*.py",)))

    def test_single_star_does_not_cross_path_segments_for_generic_glob(self) -> None:
        self.assertFalse(ownership_snapshot._allowed("src/a/b.txt", ("src/*",)))

    def test_double_star_matches_recursively(self) -> None:
        self.assertTrue(ownership_snapshot._allowed("src/deep/x.py", ("src/**/*.py",)))
        self.assertTrue(ownership_snapshot._allowed("src", ("src/**",)))

    def test_mode_symlink_and_rename_are_visible(self) -> None:
        (self.root / "bin").mkdir()
        source = self.root / "bin" / "old"
        source.write_text("same", encoding="utf-8")
        os.symlink("old", self.root / "bin" / "current")
        before = self.capture()
        source.rename(self.root / "bin" / "new")
        os.chmod(self.root / "bin" / "new", 0o755)
        (self.root / "bin" / "current").unlink()
        os.symlink("new", self.root / "bin" / "current")
        after = self.capture()
        delta = ownership_snapshot.compare(before, after, allowed_mutation_scopes=["bin/**"])
        self.assertIn("bin/current", delta["modified"])
        self.assertIn("bin/old", delta["deleted"])
        self.assertIn("bin/new", delta["created"])
        # Mode changed, so the physical rename candidate intentionally does not claim equivalence.
        self.assertEqual([], delta["renameCandidates"])

    def test_rename_candidate_preserves_both_endpoints(self) -> None:
        old = self.root / "old.txt"
        old.write_text("same", encoding="utf-8")
        before = self.capture()
        old.rename(self.root / "new.txt")
        after = self.capture()
        delta = ownership_snapshot.compare(
            before, after, allowed_mutation_scopes=["old.txt", "new.txt"]
        )
        self.assertEqual([{"from": "old.txt", "to": "new.txt"}], delta["renameCandidates"])
        self.assertEqual(["new.txt", "old.txt"], delta["changedPaths"])

    def test_immutable_artifact_cannot_be_overwritten(self) -> None:
        snapshot = self.capture()
        output = self.artifacts / "before.json"
        ownership_snapshot.write_immutable(snapshot, output)
        with self.assertRaisesRegex(ownership_snapshot.SnapshotError, "IMMUTABLE_ARTIFACT_EXISTS"):
            ownership_snapshot.write_immutable(snapshot, output)

    def test_artifact_inside_project_is_rejected(self) -> None:
        with self.assertRaisesRegex(ownership_snapshot.SnapshotError, "SNAPSHOT_INSIDE_PROJECT"):
            ownership_snapshot.write_immutable(self.capture(), self.root / "snapshot.json")

    def test_concurrent_mutation_between_stability_passes_is_rejected(self) -> None:
        first = {"file": {"kind": "file", "mode": 0o644, "size": 1, "sha256": "a" * 64}}
        second = {"file": {"kind": "file", "mode": 0o644, "size": 1, "sha256": "b" * 64}}
        with mock.patch.object(ownership_snapshot, "_scan_tree", side_effect=[first, second]):
            with self.assertRaisesRegex(
                ownership_snapshot.SnapshotError, "SOURCE_CHANGED_DURING_CAPTURE"
            ):
                ownership_snapshot.capture(self.root)

    def test_exclusion_policy_must_match(self) -> None:
        before = ownership_snapshot.capture(self.root, exclusions=["cache/**"])
        after = ownership_snapshot.capture(self.root)
        with self.assertRaisesRegex(ownership_snapshot.SnapshotError, "SNAPSHOT_POLICY_MISMATCH"):
            ownership_snapshot.compare(before, after, allowed_mutation_scopes=[])

    def test_bounded_performance_for_one_thousand_files(self) -> None:
        bulk = self.root / "bulk"
        bulk.mkdir()
        for index in range(1000):
            (bulk / f"{index:04d}.txt").write_text(str(index), encoding="utf-8")
        started = time.monotonic()
        snapshot = self.capture()
        self.assertLess(time.monotonic() - started, 5.0)
        self.assertEqual(1002, len(snapshot["entries"]))  # .gitignore, bulk, and 1000 files


if __name__ == "__main__":
    unittest.main()
