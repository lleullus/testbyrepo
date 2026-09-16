from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from test_direct_scope import DirectScopeFixtures
from iis_observatory.snapshot import (
    SnapshotFreshness,
    build_snapshot,
    check_snapshot,
    write_snapshot,
)


class SnapshotTests(unittest.TestCase):

    def test_write_then_check_is_current(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            result = write_snapshot(fixture.root)
            self.assertEqual(result.action, "WRITTEN")
            self.assertEqual(result.check.freshness, SnapshotFreshness.CURRENT)
            checked = check_snapshot(fixture.root)
            self.assertEqual(checked.freshness, SnapshotFreshness.CURRENT)


    def test_scope_content_change_is_stale(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            scope = fixture.scope()
            write_snapshot(fixture.root)
            scope.write_text(
                scope.read_text(encoding="utf-8").replace(
                    "Preserve member identity.", "Preserve changed member identity."
                ),
                encoding="utf-8",
            )
            checked = check_snapshot(fixture.root)
            self.assertEqual(checked.freshness, SnapshotFreshness.STALE)
            self.assertTrue(checked.changes)

    def test_changed_bound_thesis_is_inconsistent_not_latest_source(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            write_snapshot(fixture.root)
            fixture.thesis.write_text("# Changed Thesis\n", encoding="utf-8")
            checked = check_snapshot(fixture.root)
            self.assertEqual(checked.freshness, SnapshotFreshness.INCONSISTENT)
            self.assertIn("IIS513", checked.reason + " " + " ".join(checked.changes))

    def test_history_add_edit_delete_refreshes_stored_projection(self) -> None:
        for kind in ("scope", "legacy"):
            with self.subTest(kind=kind), TemporaryDirectory() as temp:
                fixture = DirectScopeFixtures(Path(temp))
                current = fixture.scope()
                write_snapshot(fixture.root)
                history = (
                    fixture.scope("previous", "done")
                    if kind == "scope" else fixture.legacy_ticket()
                )
                relative = history.relative_to(fixture.root).as_posix()
                stored = fixture.root / "docs/planning/observatory/project-state.json"
                for change in ("added", "edited", "deleted"):
                    with self.subTest(change=change):
                        if change == "edited":
                            history.write_text(
                                history.read_text(encoding="utf-8").replace(
                                    "# previous" if kind == "scope" else "# TKT-001",
                                    "# Revised history",
                                ),
                                encoding="utf-8",
                            )
                        elif change == "deleted":
                            history.unlink()
                        self.assertEqual(
                            check_snapshot(fixture.root).freshness,
                            SnapshotFreshness.STALE,
                        )
                        self.assertEqual(write_snapshot(fixture.root).action, "WRITTEN")
                        planning = json.loads(stored.read_text(encoding="utf-8"))["planning"]
                        items = planning["scope" if kind == "scope" else "legacy"]["history"]
                        self.assertEqual(
                            [item["path"] for item in items],
                            [] if change == "deleted" else [relative],
                        )
                        if change == "edited":
                            self.assertEqual(items[0]["title"], "Revised history")
                        self.assertEqual(
                            planning["current"]["scope"]["path"],
                            current.relative_to(fixture.root).as_posix(),
                        )
                        self.assertEqual(planning["scope"]["status"], "ready")
                        self.assertEqual(planning["tickets"]["items"], [])
                        self.assertEqual(
                            check_snapshot(fixture.root).freshness,
                            SnapshotFreshness.CURRENT,
                        )

    def test_legacy_only_history_change_is_stale(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            history = fixture.legacy_ticket()
            write_snapshot(fixture.root)
            history.write_text("# Renamed ticket\nStatus: done\n", encoding="utf-8")
            self.assertEqual(check_snapshot(fixture.root).freshness, SnapshotFreshness.STALE)
            self.assertEqual(write_snapshot(fixture.root).action, "WRITTEN")
            payload = build_snapshot(fixture.root).payload
            self.assertIsNone(payload["planning"]["current"]["scope"])
            self.assertEqual(payload["planning"]["legacy"]["history"][0]["title"], "Renamed ticket")

    def test_unrelated_code_does_not_rewrite_history_snapshot(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            fixture.scope("previous", "done")
            fixture.legacy_ticket()
            write_snapshot(fixture.root)
            directory = fixture.root / "docs/planning/observatory"
            before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in directory.iterdir()}
            (fixture.root / "product.py").write_text("print('changed')\n", encoding="utf-8")
            self.assertEqual(check_snapshot(fixture.root).freshness, SnapshotFreshness.CURRENT)
            self.assertEqual(write_snapshot(fixture.root).action, "UNCHANGED")
            after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in directory.iterdir()}
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
