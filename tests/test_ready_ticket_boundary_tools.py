from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts/sync_installed_iis.py"


class BundleInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("iis_bundle_test", SYNC)
        assert spec is not None and spec.loader is not None
        cls.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.installer)

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="iis-skills-install-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source"
        self.store = self.root / "store"
        self.host = self.root / "omp"
        for relative in self.installer.PAYLOAD_ROOTS:
            target = self.source / relative
            if target.suffix:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# helper\n")
            else:
                target.mkdir(parents=True, exist_ok=True)
        for relative in self.installer.REQUIRED:
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# candidate payload\n")
        self.router = self.source / "iis-workflow/SKILL.md"
        self.router.write_text(f"Read {self.source}/scope-shaper/tools/validate_scope.py\n")

    def prepare(self) -> dict:
        return self.installer.prepare(self.source, self.store)

    def activate(self, manifest: dict, **kwargs) -> dict:
        return self.installer.activate(
            self.store,
            manifest["bundle_id"],
            {"omp": self.host},
            quiescent=True,
            **kwargs,
        )

    def _legacy_release(self) -> tuple[str, Path]:
        bundle_id = "legacy-v4-fixture"
        release = self.store / "releases" / bundle_id
        skill = release / "iis-workflow/SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("# legacy router\n")
        current = self.store / "current"
        current.parent.mkdir(parents=True, exist_ok=True)
        current.symlink_to(release, target_is_directory=True)
        managed = self.host / "skills/iis-workflow"
        managed.parent.mkdir(parents=True, exist_ok=True)
        target = str(self.store / "current/iis-workflow")
        managed.symlink_to(target, target_is_directory=True)
        originals = {
            str(managed): {
                "path": str(managed),
                "before": {"kind": "absent"},
                "after": {"kind": "symlink", "target": target},
                "backup": str(self.store / "snapshots/legacy/0"),
            }
        }
        state = {
            "schema": "iis-install/v4",
            "bundle_id": bundle_id,
            "family": "iis-skills",
            "hosts": {"omp": str(self.host)},
            "originals": originals,
            "links": {str(managed): target},
            "snapshot": str(self.store / "snapshots/legacy/snapshot.json"),
        }
        self.installer.atomic_json(self.store / "installed.json", state)
        return bundle_id, managed

    def test_prepare_never_activates_and_release_id_is_not_content_derived(self) -> None:
        first = self.prepare()
        second = self.prepare()
        self.assertRegex(first["bundle_id"], r"^rel-[0-9a-f]{32}$")
        self.assertRegex(second["bundle_id"], r"^rel-[0-9a-f]{32}$")
        self.assertNotEqual(first["bundle_id"], second["bundle_id"])
        self.assertFalse((self.store / "current").exists())
        release = self.store / "releases" / first["bundle_id"]
        protected = self.store / "records" / first["bundle_id"] / "payload"
        self.assertEqual(
            (release / "iis-workflow/SKILL.md").read_bytes(),
            (protected / "iis-workflow/SKILL.md").read_bytes(),
        )

    def test_candidate_rejects_retired_runtime_payload(self) -> None:
        retired = self.source / "delivery-runtime/ready-ticket-implement/index.js"
        retired.parent.mkdir(parents=True, exist_ok=True)
        retired.write_text("legacy\n")
        with self.assertRaises(ValueError):
            self.prepare()

    def test_release_tamper_is_detected_by_direct_original_comparison(self) -> None:
        manifest = self.prepare()
        path = self.store / "releases" / manifest["bundle_id"] / "iis-workflow/SKILL.md"
        path.chmod(0o644)
        path.write_text("tampered\n")
        with self.assertRaisesRegex(ValueError, "release file changed|release mode changed"):
            self.activate(manifest)

    def test_explicit_migration_and_remove_restore_user_entries(self) -> None:
        original = self.host / "skills/iis-workflow"
        original.mkdir(parents=True)
        (original / "SKILL.md").write_text("user's existing install\n")
        manifest = self.prepare()
        with self.assertRaises(ValueError):
            self.activate(manifest)
        state = self.activate(manifest, migrate=True)
        self.assertEqual(state["schema"], "iis-install/v5")
        self.installer.remove(self.store, quiescent=True)
        self.assertFalse(original.is_symlink())
        self.assertEqual((original / "SKILL.md").read_text(), "user's existing install\n")

    def test_activation_failure_restores_entries_before_reporting_failure(self) -> None:
        manifest = self.prepare()
        original = self.host / "skills/iis-workflow"
        original.mkdir(parents=True)
        (original / "SKILL.md").write_text("original\n")
        real_pointer = self.installer.set_pointer

        def fail_new_pointer(store, target):
            if target is not None:
                raise OSError("injected activation failure")
            return real_pointer(store, target)

        with mock.patch.object(self.installer, "set_pointer", side_effect=fail_new_pointer):
            with self.assertRaisesRegex(OSError, "injected"):
                self.activate(manifest, migrate=True)
        self.assertFalse(original.is_symlink())
        self.assertEqual((original / "SKILL.md").read_text(), "original\n")
        self.assertFalse((self.store / "current").exists())
        self.assertFalse((self.store / "pending.json").exists())

    def test_rollback_restores_previous_release_and_rejects_intervening_user_changes(self) -> None:
        first = self.prepare()
        self.activate(first)
        self.router.write_text("second revision\n")
        second = self.prepare()
        self.activate(second)
        self.installer.rollback(self.store, quiescent=True)
        self.assertEqual((self.store / "current").resolve(), self.store / "releases" / first["bundle_id"])
        self.activate(second)
        entry = self.host / "skills/iis-workflow"
        entry.unlink()
        entry.mkdir()
        (entry / "SKILL.md").write_text("intervening user work\n")
        with self.assertRaises(ValueError):
            self.installer.remove(self.store, quiescent=True)
        self.assertEqual((entry / "SKILL.md").read_text(), "intervening user work\n")

    def test_cli_inspect_reports_protocol_five_without_loading_host(self) -> None:
        manifest = self.prepare()
        result = subprocess.run(
            [
                sys.executable,
                str(SYNC),
                "inspect",
                "--store",
                str(self.store),
                "--bundle",
                manifest["bundle_id"],
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["protocol"], 5)
        self.assertEqual(parsed["loaded_identity"], "NOT_CHECKED")
        self.assertFalse(self.host.exists())

    def test_legacy_v4_is_read_only_then_explicitly_cut_over_and_rollback(self) -> None:
        legacy_id, managed = self._legacy_release()
        inspected = self.installer.inspect(self.store)
        self.assertTrue(inspected["legacy_read_only"])
        self.assertEqual(inspected["bundle_id"], legacy_id)
        candidate = self.prepare()
        state = self.activate(candidate)
        self.assertEqual(state["schema"], "iis-install/v5")
        self.assertTrue(managed.is_symlink())
        self.installer.rollback(self.store, quiescent=True)
        self.assertEqual((self.store / "current").resolve(), self.store / "releases" / legacy_id)
        self.assertEqual(self.installer.inspect(self.store)["bundle_id"], legacy_id)


if __name__ == "__main__":
    unittest.main()
