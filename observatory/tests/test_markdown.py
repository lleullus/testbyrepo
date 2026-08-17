from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from helpers import RepoBuilder
from iis_observatory.markdown import canonical_id, normalize_status, parse_artifact
from iis_observatory.model import ArtifactKind


class MarkdownParserTests(unittest.TestCase):
    def test_normalizes_identifiers_and_statuses(self) -> None:
        self.assertEqual(canonical_id("TICKET-005"), "TKT-005")
        self.assertEqual(canonical_id("inc_12"), "INC-12")
        self.assertEqual(normalize_status("ready for matt"), "ready-for-matt")
        self.assertEqual(normalize_status("Completed"), "done")

    def test_reads_front_matter(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            path = builder.write(
                "docs/planning/work/demo/tickets/TICKET-001.md",
                """
---
status: ready
source_increment: INC-003
---
# TKT-001 Example
""",
            )
            artifact = parse_artifact(path, builder.planning)
            self.assertEqual(artifact.kind, ArtifactKind.TICKET)
            self.assertEqual(artifact.identifier, "TKT-001")
            self.assertEqual(artifact.status, "ready")
            self.assertEqual(artifact.metadata["source_increment"], "INC-003")
            self.assertEqual(artifact.work_slug, "demo")

    def test_reads_markdown_table_metadata(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            path = builder.write(
                "docs/planning/work/demo/SPEC.md",
                """
# Spec
| Field | Value |
|---|---|
| Status | approved |
| Source-Increment | INC-008 |
""",
            )
            artifact = parse_artifact(path, builder.planning)
            self.assertEqual(artifact.kind, ArtifactKind.SPEC)
            self.assertEqual(artifact.status, "approved")
            self.assertEqual(artifact.metadata["source_increment"], "INC-008")

    def test_skips_non_status_colon_content(self) -> None:
        with TemporaryDirectory() as temp:
            builder = RepoBuilder(Path(temp))
            path = builder.write(
                "docs/planning/work/demo/tickets/TICKET-001.md",
                """
# TKT-001
Status: ready
Notes: this should not alter status
""",
            )
            artifact = parse_artifact(path, builder.planning)
            self.assertEqual(artifact.status, "ready")


if __name__ == "__main__":
    unittest.main()
