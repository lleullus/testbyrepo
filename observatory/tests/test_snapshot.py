from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
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


if __name__ == "__main__":
    unittest.main()
