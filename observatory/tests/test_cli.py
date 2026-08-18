from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from helpers import RepoBuilder
from iis_observatory.cli import main


class CliTests(unittest.TestCase):
    def test_overview_json(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            builder = RepoBuilder(root, "tax")
            builder.scope()
            stream = StringIO()
            with redirect_stdout(stream):
                code = main(["overview", str(root), "--format", "json"])
            self.assertEqual(code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(payload["projects"][0]["repository"], "tax")

    def test_doctor_treats_non_git_root_with_planning_as_discovery_container(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs" / "planning").mkdir(parents=True)
            child = RepoBuilder(root, "tax")
            child.scope()
            stream = StringIO()
            with redirect_stdout(stream):
                code = main(["doctor", str(root), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(stream.getvalue())
            self.assertEqual([item["repository"] for item in payload["projects"]], ["tax"])

    def test_path_without_subcommand_defaults_to_overview(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            builder = RepoBuilder(root, "tax")
            builder.scope()
            stream = StringIO()
            with redirect_stdout(stream):
                code = main([str(root), "--no-color"])
            self.assertEqual(code, 0)
            self.assertIn("IIS PROJECT OVERVIEW", stream.getvalue())

    def test_overview_hides_worktrees_unless_requested(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            main_repo = RepoBuilder(root, "x.com")
            main_repo.scope()
            worktree = RepoBuilder(main_repo.repo / "worktrees", "feature", git=False)
            worktree.scope()
            worktree.write(
                ".git",
                f"gitdir: {main_repo.repo / '.git' / 'worktrees' / 'feature'}\n",
            )

            default_stream = StringIO()
            with redirect_stdout(default_stream):
                default_code = main(["overview", str(root), "--format", "json"])
            self.assertEqual(default_code, 0)
            default_payload = json.loads(default_stream.getvalue())
            self.assertEqual([item["repository"] for item in default_payload["projects"]], ["x.com"])

            included_stream = StringIO()
            with redirect_stdout(included_stream):
                included_code = main(
                    ["overview", str(root), "--format", "json", "--include-worktrees"]
                )
            self.assertEqual(included_code, 0)
            included_payload = json.loads(included_stream.getvalue())
            self.assertEqual(
                sorted(item["repository"] for item in included_payload["projects"]),
                ["x.com", "x.com/worktrees/feature"],
            )

    def test_scan_without_planning_returns_distinct_exit_code(self) -> None:
        with TemporaryDirectory() as temp:
            stream = StringIO()
            with redirect_stdout(stream):
                code = main(["scan", temp, "--no-color"])
            self.assertEqual(code, 4)
            self.assertIn("NO IIS", stream.getvalue())

    def test_fail_on_inconsistent(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "bad")
            builder.write(
                "docs/planning/scope-shaping/SCOPE-SHAPING-RESULT.md",
                "# Scope\nSelected-Increment: INC-999",
            )
            stream = StringIO()
            with redirect_stdout(stream):
                code = main(["scan", str(builder.repo), "--fail-on-inconsistent", "--no-color"])
            self.assertEqual(code, 3)

    def test_missing_discovery_root_is_error(self) -> None:
        stream_out, stream_err = StringIO(), StringIO()
        with redirect_stdout(stream_out), redirect_stderr(stream_err):
            code = main(["overview", "/definitely/missing/iis-root"])
        self.assertEqual(code, 2)
        self.assertIn("does not exist", stream_err.getvalue())

    def test_snapshot_cli_missing_write_then_current(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope()
            builder.spec()
            builder.ticket(1, "done")

            missing = StringIO()
            with redirect_stdout(missing):
                missing_code = main(["snapshot", str(builder.repo), "--check"])
            self.assertEqual(missing_code, 7)
            self.assertIn("Snapshot-Freshness: MISSING", missing.getvalue())

            written = StringIO()
            with redirect_stdout(written):
                write_code = main(["snapshot", str(builder.repo), "--write"])
            self.assertEqual(write_code, 0)
            self.assertIn("Action: WRITTEN", written.getvalue())

            current = StringIO()
            with redirect_stdout(current):
                current_code = main(["snapshot", str(builder.repo), "--check"])
            self.assertEqual(current_code, 0)
            self.assertIn("Snapshot-Freshness: CURRENT", current.getvalue())

    def test_snapshot_cli_json_output(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope()
            builder.spec()
            builder.ticket(1, "done")
            write_stream = StringIO()
            with redirect_stdout(write_stream):
                code = main([
                    "snapshot",
                    str(builder.repo),
                    "--write",
                    "--format",
                    "json",
                ])
            self.assertEqual(code, 0)
            payload = json.loads(write_stream.getvalue())
            self.assertEqual(payload["action"], "WRITTEN")
            self.assertEqual(payload["freshness"], "CURRENT")

    def test_snapshot_cli_stale_exit_code(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope()
            builder.spec()
            builder.ticket(1, "ready")
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["snapshot", str(builder.repo), "--write"]), 0)
            builder.ticket(1, "done")
            stale = StringIO()
            with redirect_stdout(stale):
                code = main(["snapshot", str(builder.repo), "--check"])
            self.assertEqual(code, 6)
            self.assertIn("Snapshot-Freshness: STALE", stale.getvalue())


if __name__ == "__main__":
    unittest.main()
