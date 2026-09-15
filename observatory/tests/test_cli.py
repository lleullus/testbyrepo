from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from test_direct_scope import DirectScopeFixtures
from iis_observatory.cli import main


class CliTests(unittest.TestCase):
    def test_overview_json_uses_direct_scope_schema(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = DirectScopeFixtures(root / "tax")
            fixture.scope()
            output = StringIO()
            with redirect_stdout(output):
                code = main(["overview", str(root), "--format", "json"])
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["schema_version"], "2.0")
            self.assertEqual(payload["projects"][0]["authority_mode"], "direct-scope")
            self.assertEqual(payload["projects"][0]["next_work"]["kind"], "none")

    def test_path_without_subcommand_defaults_to_overview(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp) / "tax")
            fixture.scope()
            output = StringIO()
            with redirect_stdout(output):
                code = main([str(Path(temp))])
            self.assertEqual(code, 0)
            self.assertIn("IIS PROJECT OVERVIEW", output.getvalue())

    def test_scan_without_planning_keeps_distinct_exit_code(self) -> None:
        with TemporaryDirectory() as temp:
            output = StringIO()
            with redirect_stdout(output):
                code = main(["scan", str(Path(temp))])
            self.assertEqual(code, 4)
            self.assertIn("NO IIS", output.getvalue())

    def test_fail_on_inconsistent_direct_source(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            fixture.thesis.write_text("# Changed Thesis\n", encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                code = main(["scan", str(fixture.root), "--fail-on-inconsistent"])
            self.assertEqual(code, 3)
            self.assertIn("IIS513", output.getvalue())

    def test_duplicate_active_scope_is_doctor_error(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope("one", "ready")
            fixture.scope("two", "draft")
            output = StringIO()
            with redirect_stdout(output):
                code = main(["doctor", str(fixture.root)])
            self.assertEqual(code, 3)
            self.assertIn("IIS502", output.getvalue())

    def test_snapshot_write_and_check_use_direct_scope_inputs(self) -> None:
        with TemporaryDirectory() as temp:
            fixture = DirectScopeFixtures(Path(temp))
            fixture.scope()
            written = StringIO()
            with redirect_stdout(written):
                code = main(["snapshot", str(fixture.root), "--write"])
            self.assertEqual(code, 0)
            self.assertIn("Snapshot-Freshness: CURRENT", written.getvalue())
            checked = StringIO()
            with redirect_stdout(checked):
                code = main(["snapshot", str(fixture.root), "--check"])
            self.assertEqual(code, 0)
            self.assertIn("Snapshot-Freshness: CURRENT", checked.getvalue())


if __name__ == "__main__":
    unittest.main()
