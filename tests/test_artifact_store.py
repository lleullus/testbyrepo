from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from iis_artifacts.publication import RevisionConflict, publish_ref
from iis_artifacts.store import ArtifactStore, ArtifactStoreError


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="iis-artifact-store-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.store = ArtifactStore(self.root / "store", "project")

    def test_capture_preserves_actual_bytes_without_content_identity(self) -> None:
        source = self.project / "docs/source.txt"
        source.parent.mkdir()
        source.write_bytes(b"alpha\n")
        snapshot = self.store.capture_files(self.project, [source], kind="source")
        ref = {"snapshot": snapshot, "path": "docs/source.txt"}
        self.assertRegex(snapshot, r"^snap-[0-9a-f]{32}$")
        self.assertEqual(self.store.read_bytes(ref), b"alpha\n")

    def test_capture_rejects_intermediate_final_and_broken_symlinks(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        real = outside / "real.txt"
        real.write_text("outside\n", encoding="utf-8")

        intermediate = self.project / "linked"
        intermediate.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ArtifactStoreError, "symlink"):
            self.store.capture_files(self.project, [intermediate / "real.txt"], kind="source")

        final = self.project / "final.txt"
        final.symlink_to(real)
        with self.assertRaisesRegex(ArtifactStoreError, "symlink"):
            self.store.capture_files(self.project, [final], kind="source")

        broken = self.project / "broken.txt"
        broken.symlink_to(outside / "missing.txt")
        with self.assertRaisesRegex(ArtifactStoreError, "symlink"):
            self.store.capture_files(self.project, [broken], kind="source")

    def test_publication_rejects_intervening_live_change(self) -> None:
        logical = "docs/planning/product-thesis/demo/THESIS-001.md"
        target = self.project / logical
        target.parent.mkdir(parents=True)
        target.write_bytes(b"first\n")
        first_snapshot = self.store.capture_mapping({logical: b"first\n"}, kind="candidate")
        first = {"snapshot": first_snapshot, "path": logical}
        publish_ref(self.store, first, self.project, logical, expected_prior=None)

        target.write_bytes(b"user-change\n")
        second_snapshot = self.store.capture_mapping({logical: b"second\n"}, kind="candidate")
        second = {"snapshot": second_snapshot, "path": logical}
        with self.assertRaisesRegex(RevisionConflict, "changed outside"):
            publish_ref(self.store, second, self.project, logical, expected_prior=first)
        self.assertEqual(target.read_bytes(), b"user-change\n")


if __name__ == "__main__":
    unittest.main()
