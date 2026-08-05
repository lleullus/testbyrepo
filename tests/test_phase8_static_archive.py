from __future__ import annotations

import hashlib
import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "phase8_static_archive.py"
SPEC = importlib.util.spec_from_file_location("phase8_static_archive", ARCHIVE)
assert SPEC and SPEC.loader
phase8_static_archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(phase8_static_archive)


def tree_identity(root: Path) -> str:
    entries: list[tuple[str, str, str, int]] = []
    for path in sorted([root, *root.rglob("*")], key=lambda item: item.relative_to(root).as_posix() if item != root else ""):
        relative = "" if path == root else path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            entries.append((relative, "file", hashlib.sha256(path.read_bytes()).hexdigest(), stat.S_IMODE(mode)))
        elif stat.S_ISDIR(mode):
            entries.append((relative, "directory", "", stat.S_IMODE(mode)))
        else:
            entries.append((relative, "other", "", stat.S_IMODE(mode)))
    return hashlib.sha256(json.dumps(entries, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


class Phase8StaticArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.active = self.root / "active"
        self.results = self.active / "implementation-results"
        self.capsule_store = self.active / "baseline-capsules"
        self.capsules = self.capsule_store / "capsules"
        self.results.mkdir(parents=True)
        self.capsules.mkdir(parents=True)
        self.capsule_id = "a" * 32
        capsule = self.capsules / self.capsule_id
        (capsule / "root" / "nested").mkdir(parents=True)
        (capsule / "root" / "nested" / "source.txt").write_text("retained", encoding="utf-8")
        (capsule / "descriptor.json").write_text("descriptor", encoding="utf-8")
        result = {"protocolVersion": "implementation-result-v3", "capsuleRef": f"capsule:v1:{self.capsule_id}"}
        (self.results / "result.json").write_text(json.dumps(result), encoding="utf-8")
        for path in (self.results / "result.json", capsule / "descriptor.json", capsule / "root" / "nested" / "source.txt"):
            path.chmod(0o400)
        self.container = self.root / "archives"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_create_and_general_file_read_verify_every_item_without_source_mutation(self) -> None:
        before = tree_identity(self.active)

        result = phase8_static_archive.create_archive(self.results, self.capsule_store, self.container)

        after = tree_identity(self.active)
        archive = Path(result["archivePath"])
        verified = phase8_static_archive.verify_archive(archive)
        self.assertEqual(before, after)
        self.assertEqual(result, verified)
        self.assertEqual("STATIC_ARCHIVE", json.loads((archive / "manifest.json").read_text())["disposition"])
        self.assertFalse(json.loads((archive / "manifest.json").read_text())["retentionDisposalAuthorized"])
        self.assertEqual(3, result["counts"]["files"])
        self.assertEqual(1, result["counts"]["historicalResults"])
        self.assertEqual(1, result["counts"]["referencedCapsules"])
        self.assertEqual(0o700, stat.S_IMODE(self.container.stat().st_mode))
        self.assertEqual(0o500, stat.S_IMODE(archive.stat().st_mode))
        self.assertEqual(0o400, stat.S_IMODE((archive / "manifest.json").stat().st_mode))
        self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o400 for path in archive.rglob("*") if path.is_file()))

    def test_collision_fails_without_reusing_existing_archive(self) -> None:
        result = phase8_static_archive.create_archive(self.results, self.capsule_store, self.container)
        before = tree_identity(self.container)

        with self.assertRaisesRegex(phase8_static_archive.ArchiveError, "already exists"):
            phase8_static_archive.create_archive(self.results, self.capsule_store, self.container)

        self.assertEqual(before, tree_identity(self.container))
        self.assertTrue(Path(result["archivePath"]).is_dir())

    def test_symlink_source_is_rejected_before_archive_publication(self) -> None:
        (self.results / "unexpected-link").symlink_to(self.results / "result.json")

        with self.assertRaisesRegex(phase8_static_archive.ArchiveError, "non-regular"):
            phase8_static_archive.create_archive(self.results, self.capsule_store, self.container)

        self.assertFalse(self.container.exists())

    def test_verifier_rejects_unexpected_file_and_mode_change(self) -> None:
        result = phase8_static_archive.create_archive(self.results, self.capsule_store, self.container)
        archive = Path(result["archivePath"])
        archive.chmod(0o700)
        extra = archive / "unexpected.txt"
        extra.write_text("unexpected", encoding="utf-8")
        extra.chmod(0o400)
        archive.chmod(0o500)

        with self.assertRaisesRegex(phase8_static_archive.ArchiveError, "unexpected or missing"):
            phase8_static_archive.verify_archive(archive)

    def test_verifier_rejects_manifest_traversal_and_duplicate_paths(self) -> None:
        result = phase8_static_archive.create_archive(self.results, self.capsule_store, self.container)
        archive = Path(result["archivePath"])
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        manifest["items"][0]["relativePath"] = "../outside"
        identity = dict(manifest)
        identity.pop("manifestSha256")
        manifest["manifestSha256"] = phase8_static_archive._sha256(
            phase8_static_archive._canonical_json(identity)
        )

        with self.assertRaisesRegex(phase8_static_archive.ArchiveError, "escapes archive"):
            phase8_static_archive._verify_manifest(
                archive,
                manifest,
                expected_archive_name=f"phase8-static-archive-v1-{manifest['manifestSha256']}",
            )

        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        manifest["items"].append(dict(manifest["items"][0]))
        identity = dict(manifest)
        identity.pop("manifestSha256")
        manifest["manifestSha256"] = phase8_static_archive._sha256(
            phase8_static_archive._canonical_json(identity)
        )
        with self.assertRaisesRegex(phase8_static_archive.ArchiveError, "duplicate paths"):
            phase8_static_archive._verify_manifest(
                archive,
                manifest,
                expected_archive_name=f"phase8-static-archive-v1-{manifest['manifestSha256']}",
            )


if __name__ == "__main__":
    unittest.main()
