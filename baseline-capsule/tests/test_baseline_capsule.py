from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import baseline_capsule
from baseline_capsule import CapsuleError, CapsuleStore, capture_identity


class BaselineCapsuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.store_root = self.root / "store"
        self.project.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, value: str = "value\n") -> Path:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        return path

    def store(self, **overrides: int) -> CapsuleStore:
        values = {
            "retention_seconds": 100,
            "max_file_bytes": 1024 * 1024,
            "max_total_bytes": 4 * 1024 * 1024,
            "lease_seconds": 50,
        }
        values.update(overrides)
        return CapsuleStore(self.store_root, **values)

    def test_create_acquire_and_release_preserve_projected_payload(self) -> None:
        self.write("src/app.py", "print('ok')\n")
        self.write("ignored/local.txt", "local\n")
        os.symlink("app.py", self.project / "src/link.py")
        store = self.store()

        handle = store.create(self.project)
        view = store.acquire_read(handle["capsuleRef"])

        self.assertEqual(handle["formatVersion"], "baseline-capsule-v1")
        self.assertEqual(handle["projectionPolicyId"], "source-evidence-v1")
        self.assertEqual(view["baselineSourceIdentity"], handle["baselineSourceIdentity"])
        sealed = Path(view["sealedRoot"])
        self.assertEqual((sealed / "src/app.py").read_text(), "print('ok')\n")
        self.assertEqual((sealed / "ignored/local.txt").read_text(), "local\n")
        self.assertTrue((sealed / "src/link.py").is_symlink())
        store.release_read(view["readLeaseId"])

    def test_projection_excludes_only_closed_vcs_dependency_and_cache_rules(self) -> None:
        for excluded in (
            ".git/config",
            ".hg/store/data",
            ".svn/entries",
            "node_modules/pkg/index.js",
            ".mypy_cache/state",
            ".cache/go-build/item",
            ".next/cache/item",
            "src/__pycache__/app.pyc",
            "src/project.tsbuildinfo",
        ):
            self.write(excluded)
        for included in (
            "build/output.bin",
            "dist/package.js",
            "out/result.txt",
            ".cache/product-state",
            "coverage/report.json",
            "tmp/input.txt",
            "vendor/module.go",
            "ignored/source.py",
            ".scratch/other-work/SPEC.md",
        ):
            self.write(included)

        manifest = capture_identity(self.project)

        for excluded in (
            ".git/config",
            ".hg/store/data",
            ".svn/entries",
            "node_modules/pkg/index.js",
            ".mypy_cache/state",
            ".cache/go-build/item",
            ".next/cache/item",
            "src/__pycache__/app.pyc",
            "src/project.tsbuildinfo",
        ):
            self.assertNotIn(excluded, manifest["entries"])
        for included in (
            "build/output.bin",
            "dist/package.js",
            "out/result.txt",
            ".cache/product-state",
            "coverage/report.json",
            "tmp/input.txt",
            "vendor/module.go",
            "ignored/source.py",
            ".scratch/other-work/SPEC.md",
        ):
            self.assertIn(included, manifest["entries"])

    def test_python_environment_is_excluded_by_marker_not_name(self) -> None:
        self.write("runtime/pyvenv.cfg", "home = /python\n")
        self.write("runtime/lib/site.py")
        self.write("venv/source.py")

        manifest = capture_identity(self.project)

        self.assertNotIn("runtime", manifest["entries"])
        self.assertNotIn("runtime/lib/site.py", manifest["entries"])
        self.assertIn("venv/source.py", manifest["entries"])

    def test_identity_is_stable_and_changed_paths_ignore_directory_only_changes(self) -> None:
        self.write("src/app.py", "one\n")
        first = capture_identity(self.project)
        self.write("src/app.py", "two\n")
        self.write("new/value.txt", "new\n")
        second = capture_identity(self.project)

        self.assertNotEqual(first["sourceIdentity"], second["sourceIdentity"])
        self.assertEqual(baseline_capsule.changed_paths(first, second), ["new/value.txt", "src/app.py"])

    def test_source_change_between_stability_passes_is_rejected(self) -> None:
        path = self.write("app.py", "one\n")
        original = baseline_capsule._scan
        calls = 0

        def changing_scan(*args: object, **kwargs: object) -> object:
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            if calls == 1:
                path.write_text("two\n", encoding="utf-8")
            return result

        with mock.patch.object(baseline_capsule, "_scan", side_effect=changing_scan):
            with self.assertRaisesRegex(CapsuleError, "SOURCE_CHANGED_DURING_CAPTURE"):
                capture_identity(self.project)

    def test_file_and_total_quota_fail_before_publication(self) -> None:
        self.write("large.bin", "12345")
        with self.assertRaisesRegex(CapsuleError, "FILE_QUOTA_EXCEEDED"):
            self.store(max_file_bytes=4).create(self.project)
        self.assertEqual(list((self.store_root / "capsules").iterdir()), [])

        self.write("second.bin", "67890")
        with self.assertRaisesRegex(CapsuleError, "CAPSULE_QUOTA_EXCEEDED"):
            self.store(max_file_bytes=10, max_total_bytes=9).create(self.project)
        self.assertEqual(list((self.store_root / "capsules").iterdir()), [])

    def test_external_and_absolute_symlinks_are_rejected(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        os.symlink("../../outside.txt", self.project / "escape")
        with self.assertRaisesRegex(CapsuleError, "SYMLINK_ESCAPE"):
            self.store().create(self.project)

        (self.project / "escape").unlink()
        os.symlink(str(outside), self.project / "absolute")
        with self.assertRaisesRegex(CapsuleError, "SYMLINK_ESCAPE"):
            self.store().create(self.project)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO requires POSIX")
    def test_special_entry_is_rejected(self) -> None:
        os.mkfifo(self.project / "pipe")
        with self.assertRaisesRegex(CapsuleError, "UNSUPPORTED_ENTRY"):
            self.store().create(self.project)

    def test_store_must_be_external_to_project(self) -> None:
        inside = CapsuleStore(self.project / "capsules")
        with self.assertRaisesRegex(CapsuleError, "STORE_INSIDE_PROJECT"):
            inside.create(self.project)

        project_in_store = self.store_root / "project"
        project_in_store.mkdir(parents=True)
        with self.assertRaisesRegex(CapsuleError, "PROJECT_INSIDE_STORE"):
            self.store().create(project_in_store)

    def test_read_detects_payload_and_descriptor_corruption(self) -> None:
        self.write("app.py", "clean\n")
        store = self.store()
        handle = store.create(self.project)
        capsule_id = handle["capsuleRef"].split(":")[-1]
        capsule_path = self.store_root / "capsules" / capsule_id
        (capsule_path / "root/app.py").write_text("corrupt\n", encoding="utf-8")
        with self.assertRaisesRegex(CapsuleError, "CAPSULE_CORRUPT"):
            store.acquire_read(handle["capsuleRef"])

        second = store.create(self.project)
        second_id = second["capsuleRef"].split(":")[-1]
        descriptor_path = self.store_root / "capsules" / second_id / "descriptor.json"
        descriptor = json.loads(descriptor_path.read_text())
        descriptor["formatVersion"] = "future"
        descriptor_path.chmod(0o600)
        descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")
        with self.assertRaisesRegex(CapsuleError, "UNSUPPORTED_FORMAT"):
            store.acquire_read(second["capsuleRef"])

    def test_cleanup_waits_for_active_lease(self) -> None:
        self.write("app.py")
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store = self.store(retention_seconds=10, lease_seconds=100)
        handle = store.create(self.project, now=start)
        view = store.acquire_read(handle["capsuleRef"], now=start)

        self.assertEqual(store.cleanup_expired(now=start + timedelta(seconds=20)), [])
        store.release_read(view["readLeaseId"])
        self.assertEqual(store.cleanup_expired(now=start + timedelta(seconds=20)), [handle["capsuleRef"]])
        with self.assertRaisesRegex(CapsuleError, "CAPSULE_NOT_FOUND"):
            store.acquire_read(handle["capsuleRef"], now=start + timedelta(seconds=20))

    def test_expired_capsule_cannot_be_acquired_or_resealed(self) -> None:
        self.write("app.py")
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        store = self.store(retention_seconds=1)
        handle = store.create(self.project, now=start)
        with self.assertRaisesRegex(CapsuleError, "CAPSULE_EXPIRED"):
            store.acquire_read(handle["capsuleRef"], now=start + timedelta(seconds=2))
        self.assertEqual(len(list((self.store_root / "capsules").iterdir())), 1)

    def test_store_permissions_are_owner_only(self) -> None:
        store = self.store()
        self.assertEqual(stat.S_IMODE(store.store_root.stat().st_mode), 0o700)
        for name in ("capsules", "staging", "leases", "locks"):
            self.assertEqual(stat.S_IMODE((store.store_root / name).stat().st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
