from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from iis_artifacts.publication import (
    RevisionConflict,
    pending_publications,
    publish_ref,
    published_ref,
    recover_pending,
)
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
        self.assertEqual(self.store.ref_record(ref)["kind"], "source")

    def test_unregistered_filesystem_snapshot_is_not_a_valid_ref(self) -> None:
        snapshot = "snap-" + "f" * 32
        path = self.store.root / "snapshots" / snapshot / "forged.txt"
        path.parent.mkdir()
        path.write_text("forged\n", encoding="utf-8")
        with self.assertRaisesRegex(ArtifactStoreError, "not registered|unknown snapshot"):
            self.store.resolve({"snapshot": snapshot, "path": "forged.txt"})

    def test_capture_rejects_intermediate_final_and_broken_symlinks(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        real = outside / "real.txt"
        real.write_text("outside\n", encoding="utf-8")
        intermediate = self.project / "linked"
        intermediate.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ArtifactStoreError, "unsafe|symlink"):
            self.store.capture_files(self.project, [intermediate / "real.txt"], kind="source")
        final = self.project / "final.txt"
        final.symlink_to(real)
        with self.assertRaisesRegex(ArtifactStoreError, "unsafe|symlink"):
            self.store.capture_files(self.project, [final], kind="source")
        broken = self.project / "broken.txt"
        broken.symlink_to(outside / "missing.txt")
        with self.assertRaisesRegex(ArtifactStoreError, "unsafe|symlink"):
            self.store.capture_files(self.project, [broken], kind="source")

    def test_capture_tree_rejects_source_changed_during_capture(self) -> None:
        source = self.project / "source.txt"
        source.write_text("first\n", encoding="utf-8")
        original = self.store._read_regular_beneath
        calls = {"count": 0}

        def changing(root: Path, relative: str):
            value = original(root, relative)
            calls["count"] += 1
            if calls["count"] == 1:
                source.write_text("second\n", encoding="utf-8")
            return value

        with mock.patch.object(self.store, "_read_regular_beneath", side_effect=changing):
            with self.assertRaisesRegex(ArtifactStoreError, "INPUT_CAPTURE_UNAVAILABLE"):
                self.store.capture_tree(self.project, kind="source")

    def test_materialized_snapshot_is_independent_of_live_tree(self) -> None:
        source = self.project / "app.py"
        source.write_text("print('fixed')\n", encoding="utf-8")
        snapshot = self.store.capture_tree(self.project, kind="source")
        execution = self.root / "execution"
        self.store.materialize_snapshot(snapshot, execution)
        source.write_text("print('mutated')\n", encoding="utf-8")
        self.assertEqual((execution / "app.py").read_text(encoding="utf-8"), "print('fixed')\n")

    def test_publication_rejects_intervening_live_change(self) -> None:
        logical = "docs/planning/product-thesis/demo/THESIS-001.md"
        target = self.project / logical
        target.parent.mkdir(parents=True)
        target.write_bytes(b"first\n")
        first_snapshot = self.store.capture_mapping({logical: b"first\n"}, kind="candidate")
        first = {"snapshot": first_snapshot, "path": logical}
        publish_ref(self.store, first, self.project, logical, expected_prior=None)
        target.chmod(0o644)
        target.write_bytes(b"user-change\n")
        second_snapshot = self.store.capture_mapping({logical: b"first\n"}, kind="candidate")
        second = {"snapshot": second_snapshot, "path": logical}
        with self.assertRaisesRegex(RevisionConflict, "changed outside"):
            publish_ref(self.store, second, self.project, logical, expected_prior=first)
        self.assertEqual(target.read_bytes(), b"user-change\n")

    def test_thesis_revision_cannot_be_republished_with_different_bytes(self) -> None:
        logical = "docs/planning/product-thesis/demo/THESIS-001.md"
        target = self.project / logical
        target.parent.mkdir(parents=True)
        target.write_bytes(b"first\n")
        first_snapshot = self.store.capture_mapping({logical: b"first\n"}, kind="candidate")
        first = {"snapshot": first_snapshot, "path": logical}
        publish_ref(self.store, first, self.project, logical, expected_prior=None)
        second_snapshot = self.store.capture_mapping({logical: b"second\n"}, kind="candidate")
        second = {"snapshot": second_snapshot, "path": logical}
        with self.assertRaisesRegex(RevisionConflict, "IMMUTABLE_THESIS_REVISION"):
            publish_ref(self.store, second, self.project, logical, expected_prior=first)
        self.assertEqual(target.read_bytes(), b"first\n")
        self.assertEqual(published_ref(self.store, logical), first)

    def test_pending_publication_recovers_after_replace_before_db_finalize(self) -> None:
        logical = "docs/planning/product-thesis/demo/THESIS-001.md"
        target = self.project / logical
        target.parent.mkdir(parents=True)
        target.write_bytes(b"new\n")
        snapshot = self.store.capture_mapping({logical: b"new\n"}, kind="candidate")
        ref = {"snapshot": snapshot, "path": logical}
        with self.assertRaisesRegex(OSError, "injected publication failure"):
            publish_ref(
                self.store,
                ref,
                self.project,
                logical,
                expected_prior=None,
                fault_after_replace=True,
            )
        self.assertEqual(len(pending_publications(self.store)), 1)
        self.assertEqual(target.read_bytes(), b"new\n")
        recover_pending(self.store, self.project)
        self.assertEqual(pending_publications(self.store), [])
        self.assertEqual(published_ref(self.store, logical), ref)


if __name__ == "__main__":
    unittest.main()
