from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "delivery-runtime/ready-ticket-implement"
SYNC = ROOT / "scripts/sync_installed_iis.py"


class ReadyTicketRuntimeContractTests(unittest.TestCase):
    def test_runtime_unit_and_omp_integration_suite(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Ready runtime tests require node")
        tests = sorted(str(path) for path in (RUNTIME / "tests").glob("*.test.js"))
        self.assertTrue(tests)
        result = subprocess.run([node, "--test", *tests], cwd=ROOT,
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class BundleInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("iis_bundle_test", SYNC)
        cls.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.installer)

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="iis-bundle-install-")
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
        self.router.write_text(f"Read {self.source}/matt/skills/to-tickets/validate_ticket.py\n"
                               f"Guide {self.source}/model-selection-guide.md\n")
        self.runtime_data = self.root / "runtime-data/uncertain.json"
        self.runtime_data.parent.mkdir()
        self.runtime_data.write_text('{"effect":"unresolved"}')

    def prepare(self) -> dict:
        return self.installer.prepare(self.source, self.store)

    def activate(self, manifest: dict, **kwargs) -> dict:
        return self.installer.activate(self.store, manifest["bundle_id"], {"omp": self.host},
                                       quiescent=True, **kwargs)

    def test_prepare_never_activates_and_rebases_only_internal_references(self) -> None:
        manifest = self.prepare()
        self.assertFalse((self.store / "current").exists())
        self.assertFalse(self.host.exists())
        release = self.store / "releases" / manifest["bundle_id"]
        router = (release / "iis-workflow/SKILL.md").read_text()
        self.assertIn(str(release / "matt/skills/to-tickets/validate_ticket.py"), router)
        self.assertIn(str(self.source / "model-selection-guide.md"), router)
        self.router.write_text("new candidate\n")
        self.assertEqual((release / "iis-workflow/SKILL.md").read_text(), router)
        self.assertNotEqual(self.prepare()["bundle_id"], manifest["bundle_id"])

    def test_explicit_migration_and_remove_restore_user_entries_and_preserve_data(self) -> None:
        original = self.host / "skills/iis-workflow"
        original.mkdir(parents=True)
        (original / "SKILL.md").write_text("user's existing install\n")
        retired = self.host / "skills/ready-ticket-heuristic-probe"
        retired.symlink_to(self.source / "unavailable-original")
        manifest = self.prepare()
        with self.assertRaises(ValueError):
            self.activate(manifest)
        self.assertEqual((original / "SKILL.md").read_text(), "user's existing install\n")
        state = self.activate(manifest, migrate=True)
        self.assertEqual(state["loaded_identity"], "NOT_CHECKED")
        self.assertTrue(original.is_symlink())
        self.assertFalse(retired.is_symlink())
        self.installer.remove(self.store, quiescent=True)
        self.assertFalse(original.is_symlink())
        self.assertEqual((original / "SKILL.md").read_text(), "user's existing install\n")
        self.assertEqual(os.readlink(retired), str(self.source / "unavailable-original"))
        self.assertEqual(self.runtime_data.read_text(), '{"effect":"unresolved"}')
        self.assertTrue((self.store / "releases" / manifest["bundle_id"]).is_dir())

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

    def test_modified_release_and_unsettled_install_cannot_activate(self) -> None:
        manifest = self.prepare()
        with self.assertRaises(ValueError):
            self.installer.activate(self.store, manifest["bundle_id"], {"omp": self.host}, quiescent=False)
        path = self.store / "releases" / manifest["bundle_id"] / "iis-workflow/SKILL.md"
        path.chmod(0o644)
        path.write_text("tampered\n")
        with self.assertRaises(ValueError):
            self.activate(manifest)
        self.assertFalse(self.host.exists())

    def test_cli_check_reports_drift_without_loading_or_mutating_host(self) -> None:
        manifest = self.prepare()
        result = subprocess.run([sys.executable, str(SYNC), "check", "--store", str(self.store),
                                 "--bundle", manifest["bundle_id"]], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["loaded_identity"], "NOT_CHECKED")
        self.assertFalse(self.host.exists())


if __name__ == "__main__":
    unittest.main()
