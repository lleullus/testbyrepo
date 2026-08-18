from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import shutil
import subprocess
import time
import unittest

from helpers import RepoBuilder
from iis_observatory.snapshot import (
    SNAPSHOT_DIRECTORY,
    SNAPSHOT_JSON,
    SNAPSHOT_MARKDOWN,
    SnapshotError,
    SnapshotFreshness,
    _progress_bar,
    build_snapshot,
    check_snapshot,
    write_snapshot,
)


class SnapshotTests(unittest.TestCase):
    def make_complete_repo(self, root: Path, name: str = "repo") -> RepoBuilder:
        builder = RepoBuilder(root, name)
        builder.scope(
            "INC-004",
            "current-work",
            "WP-001",
            increment_title="INC-004: Durable Current Outcome",
        )
        builder.spec(
            "current-work",
            source_increment="INC-004",
            title="Durable Current Outcome",
        )
        builder.ticket(1, "done", slug="current-work", source_increment="INC-004")
        return builder

    def test_write_creates_stable_relative_snapshot_schema(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            result = write_snapshot(builder.repo)
            self.assertEqual(result.action, "WRITTEN")
            directory = builder.repo / SNAPSHOT_DIRECTORY
            markdown = directory / SNAPSHOT_MARKDOWN
            state_json = directory / SNAPSHOT_JSON
            self.assertTrue(markdown.is_file())
            self.assertTrue(state_json.is_file())

            payload = json.loads(state_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["schemaVersion"], "1.0")
            self.assertEqual(payload["projection"]["authority"], "derived-read-only")
            self.assertEqual(payload["project"]["root"], ".")
            serialized = state_json.read_text(encoding="utf-8")
            self.assertNotIn(str(builder.repo), serialized)
            self.assertEqual(payload["planning"]["health"], "COMPLETE")
            self.assertEqual(payload["progress"][0]["measurement"], "exact-ratio")
            self.assertEqual(payload["progress"][0]["numerator"], 1)
            self.assertEqual(payload["progress"][0]["denominator"], 1)

    def test_exact_ticket_progress_renders_bar_with_numeric_basis(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope("INC-004", "current-work", "WP-001")
            builder.spec("current-work", source_increment="INC-004")
            for number in (1, 2, 3):
                builder.ticket(number, "done", slug="current-work", source_increment="INC-004")
            for number in (4, 5):
                builder.ticket(number, "ready", slug="current-work", source_increment="INC-004")
            result = write_snapshot(builder.repo)
            self.assertIn(
                "Current Ticket delivery: ██████░░░░ 3 / 5 (60.0%) — exact ratio",
                result.bundle.markdown,
            )

    def test_progress_bar_preserves_tiny_nonzero_ratio(self) -> None:
        self.assertEqual(_progress_bar(1.2), "▏░░░░░░░░░")
        self.assertEqual(_progress_bar(60.0), "██████░░░░")
        self.assertEqual(_progress_bar(100.0), "██████████")

    def test_write_then_check_is_current(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            write_snapshot(builder.repo)
            check = check_snapshot(builder.repo)
            self.assertEqual(check.freshness, SnapshotFreshness.CURRENT)
            self.assertEqual(check.current_fingerprint, check.stored_fingerprint)

    def test_changed_ticket_makes_snapshot_stale_with_reason(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "repo")
            builder.scope()
            builder.spec()
            builder.ticket(1, "ready")
            write_snapshot(builder.repo)
            builder.ticket(1, "done")
            check = check_snapshot(builder.repo)
            self.assertEqual(check.freshness, SnapshotFreshness.STALE)
            self.assertTrue(any("TICKET-001.md" in change for change in check.changes))

    def test_same_fingerprint_write_is_true_no_op(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            first = write_snapshot(builder.repo)
            directory = builder.repo / SNAPSHOT_DIRECTORY
            markdown = directory / SNAPSHOT_MARKDOWN
            state_json = directory / SNAPSHOT_JSON
            before = (
                markdown.read_bytes(),
                state_json.read_bytes(),
                markdown.stat().st_mtime_ns,
                state_json.stat().st_mtime_ns,
            )
            time.sleep(0.01)
            second = write_snapshot(builder.repo)
            after = (
                markdown.read_bytes(),
                state_json.read_bytes(),
                markdown.stat().st_mtime_ns,
                state_json.stat().st_mtime_ns,
            )
            self.assertEqual(first.action, "WRITTEN")
            self.assertEqual(second.action, "UNCHANGED")
            self.assertEqual(before, after)

    def test_generated_files_are_excluded_from_source_fingerprint(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            first = build_snapshot(
                builder.repo,
                generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
            write_snapshot(builder.repo)
            second = build_snapshot(
                builder.repo,
                generated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
            self.assertEqual(first.source_fingerprint, second.source_fingerprint)
            input_paths = [item["path"] for item in second.payload["projection"]["inputs"]]
            self.assertFalse(
                any(path.startswith("docs/planning/observatory/") for path in input_paths)
            )

    def test_markdown_tampering_is_inconsistent_not_current(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            write_snapshot(builder.repo)
            markdown = builder.repo / SNAPSHOT_DIRECTORY / SNAPSHOT_MARKDOWN
            markdown.write_text(
                markdown.read_text(encoding="utf-8") + "manual edit\n",
                encoding="utf-8",
            )
            check = check_snapshot(builder.repo)
            self.assertEqual(check.freshness, SnapshotFreshness.INCONSISTENT)
            self.assertIn("checksum", check.reason)

    def test_incomplete_snapshot_pair_is_inconsistent(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            directory = builder.repo / SNAPSHOT_DIRECTORY
            directory.mkdir(parents=True)
            (directory / SNAPSHOT_MARKDOWN).write_text("# orphan\n", encoding="utf-8")
            check = check_snapshot(builder.repo)
            self.assertEqual(check.freshness, SnapshotFreshness.INCONSISTENT)
            self.assertIn("pair is incomplete", check.reason)

    def test_inconsistent_canonical_state_refuses_write(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp), "bad")
            builder.write(
                "docs/planning/scope-shaping/current/SCOPE-SHAPING-RESULT.md",
                "# Scope\nStatus: confirmed\nSelected-Increment: INC-999",
            )
            with self.assertRaises(SnapshotError):
                write_snapshot(builder.repo)
            self.assertFalse((builder.repo / SNAPSHOT_DIRECTORY).exists())

    def test_adaptive_provenance_is_displayed_without_activation_inference(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            builder.write(
                "docs/planning/adaptive/current/ADAPTIVE-PLANNING-MANDATE.md",
                """
# Adaptive Planning Mandate
Mode: IIS Adaptive Planning
Status: active
Revision: 2
Project-Root: /tmp/example
Applies-To: current initiative
""",
            )
            builder.write(
                "docs/planning/adaptive/current/ADAPTIVE-PLANNING-TRACE.md",
                """
# Adaptive Planning Trace
Mandate: docs/planning/adaptive/current/ADAPTIVE-PLANNING-MANDATE.md
Current Mandate Revision: 2
""",
            )
            result = write_snapshot(builder.repo)
            adaptive = result.bundle.payload["adaptiveProvenance"]
            self.assertTrue(adaptive["present"])
            self.assertEqual(adaptive["recordedMandate"]["recordedStatus"], "active")
            self.assertEqual(adaptive["activationInference"], "not-performed")
            self.assertIn("does not activate", adaptive["note"])
            self.assertIn(
                "Current Adaptive mode inference: not performed", result.bundle.markdown
            )
            self.assertNotIn("Adaptive Mode: ACTIVE", result.bundle.markdown)

    def test_adding_adaptive_provenance_makes_snapshot_stale(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            write_snapshot(builder.repo)
            builder.write(
                "docs/planning/adaptive/current/ADAPTIVE-PLANNING-MANDATE.md",
                "# Adaptive Planning Mandate\nMode: IIS Adaptive Planning\nStatus: active\nRevision: 1",
            )
            check = check_snapshot(builder.repo)
            self.assertEqual(check.freshness, SnapshotFreshness.STALE)
            self.assertTrue(any("ADAPTIVE-PLANNING-MANDATE" in item for item in check.changes))

    def test_project_overview_avoids_top_level_status_field(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            result = write_snapshot(builder.repo)
            for line in result.bundle.markdown.splitlines():
                self.assertIsNone(re.match(r"^\s*(?:[-*]\s*)?Status\s*:", line, re.I))
            self.assertIn("Snapshot-Freshness: current-at-generation", result.bundle.markdown)
            self.assertIn("Projection-Consistency: consistent", result.bundle.markdown)

    def test_scope_horizon_is_preserved_without_selecting_a_candidate(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
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
### Deferred
- WP-004
""",
            )
            for identifier, title in (
                ("WP-002", "Explorer"),
                ("WP-003", "Automation"),
                ("WP-004", "Reconciliation"),
            ):
                builder.write(
                    f"docs/planning/scope-shaping/current/work-packages/{identifier}.md",
                    f"# {identifier}: {title}\nStatus: scoped\nWork-Package: {identifier}",
                )
            result = write_snapshot(builder.repo)
            follow_up = result.bundle.payload["planning"]["followUp"]
            self.assertEqual(
                [item["id"] for item in follow_up["nextCandidateWorkPackages"]],
                ["WP-002", "WP-003"],
            )
            self.assertEqual(
                [item["id"] for item in follow_up["deferredWorkPackages"]],
                ["WP-004"],
            )
            self.assertIsNone(follow_up["nextIncrement"])
            self.assertEqual(
                result.bundle.payload["planning"]["nextWork"]["leaf"],
                "Scope Shaper",
            )

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_committing_snapshot_does_not_make_it_stale(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            # RepoBuilder creates a marker directory for portfolio discovery; replace
            # it with a real Git repository for this integration test.
            (builder.repo / ".git").rmdir()
            subprocess.run(["git", "-C", str(builder.repo), "init", "-q"], check=True)
            git = [
                "git",
                "-C",
                str(builder.repo),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
            ]
            subprocess.run([*git, "add", "."], check=True)
            subprocess.run([*git, "commit", "-qm", "canonical planning"], check=True)
            write_snapshot(builder.repo)
            subprocess.run([*git, "add", "docs/planning/observatory"], check=True)
            subprocess.run([*git, "commit", "-qm", "record observatory snapshot"], check=True)
            check = check_snapshot(builder.repo)
            self.assertEqual(check.freshness, SnapshotFreshness.CURRENT)

            # An unrelated Git commit also must not change source freshness.
            (builder.repo / "README.md").write_text("unrelated\n", encoding="utf-8")
            subprocess.run([*git, "add", "README.md"], check=True)
            subprocess.run([*git, "commit", "-qm", "unrelated repository change"], check=True)
            self.assertEqual(
                check_snapshot(builder.repo).freshness, SnapshotFreshness.CURRENT
            )

    def test_snapshot_file_permissions_are_regular_readable_files(self) -> None:
        with TemporaryDirectory() as temp:
            builder = self.make_complete_repo(Path(temp))
            write_snapshot(builder.repo)
            directory = builder.repo / SNAPSHOT_DIRECTORY
            for name in (SNAPSHOT_MARKDOWN, SNAPSHOT_JSON):
                path = directory / name
                self.assertTrue(path.is_file())
                self.assertEqual(path.stat().st_mode & 0o777, 0o644)


if __name__ == "__main__":
    unittest.main()
