from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import tarfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts/sync_installed_iis.py"




class BundleInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("iis_bundle_test", SYNC)
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
        return self.installer.activate(self.store, manifest["bundle_id"], {"omp": self.host},
                                       quiescent=True, **kwargs)

    def _legacy_release(self) -> tuple[str, Path]:
        family = "scope-boundary-tools"
        bundle_id = hashlib.sha256(family.encode()).hexdigest()
        release = self.store / "releases" / bundle_id
        files = {
            "iis-workflow/SKILL.md": b"# legacy router\n",
            "repo-snapshot/SKILL.md": b"# legacy repo snapshot\n",
            "delivery-tools/scope/index.js": b"export default function legacy() {}\n",
        }
        entries = {}
        for relative, data in files.items():
            path = release / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o444)
            entries[relative] = {"sha256": hashlib.sha256(data).hexdigest(), "mode": 0o444}
        manifest = {"schema": "iis-bundle/v3", "protocol": 3,
                    "family": family, "bundle_id": bundle_id, "files": entries,
                    "boundary_protocol": "iis-scope-boundary/v1",
                    "host_profile": "iis-scope-verifier/v1",
                    "terminal_schema": "iis-scope-verifier-terminal/v1"}
        self.installer.atomic_json(release / "bundle.json", manifest)
        (self.store / "current").symlink_to(release, target_is_directory=True)
        links = {}
        originals = {}
        for index, (name, relative) in enumerate((
            ("skills/iis-workflow", "iis-workflow"),
            ("skills/repo-snapshot", "repo-snapshot"),
            ("extensions/scope-boundary-tools", "delivery-tools/scope"),
        )):
            path = self.host / name
            target = str(self.store / "current" / relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(target, target_is_directory=True)
            links[str(path)] = target
            originals[str(path)] = {"path": str(path), "before": {"kind": "absent"},
                                    "after": {"kind": "symlink", "target": target},
                                    "backup": str(self.store / "snapshots/legacy" / str(index))}
        state = {
            "schema": "iis-install/v3", "bundle_id": bundle_id,
            "family": family, "hosts": {"omp": str(self.host)}, "originals": originals,
            "links": links, "snapshot": str(self.store / "snapshots/legacy/snapshot.json"),
            "boundary_protocol": "iis-scope-boundary/v1", "host_profile": "iis-scope-verifier/v1",
            "terminal_schema": "iis-scope-verifier-terminal/v1",
        }
        self.installer.atomic_json(self.store / "installed.json", state)
        return bundle_id, self.host / "extensions/scope-boundary-tools"

    def test_prepare_never_activates_and_rebases_only_internal_references(self) -> None:
        manifest = self.prepare()
        self.assertEqual(manifest["family"], self.installer.NEW_FAMILY)
        self.assertFalse((self.store / "current").exists())
        self.assertFalse(self.host.exists())
        release = self.store / "releases" / manifest["bundle_id"]
        router = (release / "iis-workflow/SKILL.md").read_text()
        self.assertIn(str(release / "scope-shaper/tools/validate_scope.py"), router)
        self.router.write_text("new candidate\n")
        self.assertEqual((release / "iis-workflow/SKILL.md").read_text(), router)
        self.assertNotEqual(self.prepare()["bundle_id"], manifest["bundle_id"])

    def test_candidate_rejects_retired_runtime_payload(self) -> None:
        retired = self.source / "delivery-runtime/ready-ticket-implement/index.js"
        retired.parent.mkdir(parents=True, exist_ok=True)
        retired.write_text("legacy\n")
        with self.assertRaises(ValueError):
            self.prepare()

    def test_explicit_migration_and_remove_restore_user_entries(self) -> None:
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
        self.assertEqual(state["family"], self.installer.NEW_FAMILY)
        self.assertFalse((self.host / "extensions").exists())
        self.installer.remove(self.store, quiescent=True)
        self.assertFalse(original.is_symlink())
        self.assertEqual((original / "SKILL.md").read_text(), "user's existing install\n")
        self.assertEqual(os.readlink(retired), str(self.source / "unavailable-original"))
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

    def test_installed_release_uses_its_own_manifest_during_upgrade(self) -> None:
        manifest = self.prepare()
        self.activate(manifest)
        future_required = self.installer.REQUIRED + ("companion-skills/future-role/SKILL.md",)
        with mock.patch.object(self.installer, "REQUIRED", future_required):
            state = self.installer.check_install(self.store)
        self.assertEqual(state["bundle_id"], manifest["bundle_id"])

    def test_frozen_v4_upgrade_retirement_rollback_inspect_and_remove(self) -> None:
        frozen = self.root / "frozen-v4"
        frozen.mkdir()
        with tarfile.open(ROOT / "tests/fixtures/iis-v4-c856dd7.tar") as archive:
            archive.extractall(frozen, filter="data")
        spec = importlib.util.spec_from_file_location("frozen_iis_installer", frozen / "scripts/sync_installed_iis.py")
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
        previous = old.prepare(frozen, self.store)
        old.activate(self.store, previous["bundle_id"], {"omp": self.host}, quiescent=True)
        retired = self.host / "skills/scope-verify"
        self.assertTrue(retired.is_symlink())
        user = self.host / "skills/user-owned"
        user.mkdir()
        (user / "SKILL.md").write_text("preserve me")
        self.assertEqual(self.installer.inspect(self.store)["bundle_id"], previous["bundle_id"])
        with self.assertRaises(ValueError):
            self.installer.inspect(self.store, previous["bundle_id"])
        candidate = self.prepare()
        self.activate(candidate)
        self.assertFalse(retired.exists() or retired.is_symlink())
        self.assertEqual(self.installer.inspect(self.store)["bundle_id"], candidate["bundle_id"])
        self.installer.rollback(self.store, quiescent=True)
        self.assertTrue(retired.is_symlink())
        self.assertEqual(self.installer.inspect(self.store)["bundle_id"], previous["bundle_id"])
        self.installer.remove(self.store, quiescent=True)
        self.assertFalse(retired.exists() or retired.is_symlink())
        self.assertEqual((user / "SKILL.md").read_text(), "preserve me")
        self.assertTrue((self.store / "releases" / previous["bundle_id"]).exists())

    def test_cli_inspect_reports_candidate_contract_without_loading_host(self) -> None:
        manifest = self.prepare()
        result = subprocess.run([sys.executable, str(SYNC), "inspect", "--store", str(self.store),
                                 "--bundle", manifest["bundle_id"]], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["family"], self.installer.NEW_FAMILY)
        self.assertEqual(parsed["protocol"], 4)
        self.assertTrue({"boundary_protocol", "host_profile", "terminal_schema"}.isdisjoint(parsed))
        self.assertEqual(parsed["loaded_identity"], "NOT_CHECKED")
        self.assertFalse(self.host.exists())

    def test_v3_cutover_preserves_history_and_unrelated_entries_and_can_rollback(self) -> None:
        old_bundle, old_extension = self._legacy_release()
        old_state = (self.store / "installed.json").read_bytes()
        history = self.store / "snapshots/legacy/observation.json"
        history.parent.mkdir(parents=True)
        history.write_bytes(b"historical observation\n")
        private = self.store / "private-verifier-state/terminal.json"
        private.parent.mkdir()
        private.write_bytes(b"historical private state\n")
        user_extension = self.host / "extensions/user-extension"
        user_extension.symlink_to(self.root / "user-extension-source")
        user_skill = self.host / "skills/user-skill"
        user_skill.mkdir()
        (user_skill / "SKILL.md").write_bytes(b"user skill\n")
        preserved = [history, private, user_extension, user_skill, self.store / "releases" / old_bundle]
        identities = {path: self.installer.entry_identity(path) for path in preserved}
        with self.assertRaises(ValueError):
            self.installer.inspect(self.store, old_bundle)
        candidate = self.prepare()
        state = self.activate(candidate)
        self.assertEqual(state["schema"], "iis-install/v4")
        self.assertFalse(old_extension.is_symlink() or old_extension.exists())
        self.assertEqual((self.host / "skills/iis-workflow/SKILL.md").read_text(),
                         (self.store / "releases" / candidate["bundle_id"] / "iis-workflow/SKILL.md").read_text())
        self.assertEqual({path: self.installer.entry_identity(path) for path in preserved}, identities)
        self.installer.rollback(self.store, quiescent=True)
        self.assertEqual((self.store / "installed.json").read_bytes(), old_state)
        self.assertEqual(os.readlink(old_extension), str(self.store / "current/delivery-tools/scope"))
        self.assertEqual((self.store / "current").resolve(), self.store / "releases" / old_bundle)
        self.assertEqual({path: self.installer.entry_identity(path) for path in preserved}, identities)

    def test_v3_cutover_refuses_user_modified_managed_extension(self) -> None:
        old_bundle, extension = self._legacy_release()
        extension.unlink()
        extension.mkdir()
        (extension / "user.js").write_bytes(b"user modification\n")
        with self.assertRaisesRegex(ValueError, "drift"):
            self.activate(self.prepare())
        self.assertEqual((extension / "user.js").read_bytes(), b"user modification\n")
        self.assertEqual((self.store / "current").resolve(), self.store / "releases" / old_bundle)

    def test_remove_after_v3_cutover_keeps_extension_retired_and_history_intact(self) -> None:
        old_bundle, extension = self._legacy_release()
        candidate = self.prepare()
        self.activate(candidate)
        self.installer.remove(self.store, quiescent=True)
        self.assertFalse(extension.is_symlink() or extension.exists())
        self.assertFalse((self.host / "skills/iis-workflow").is_symlink())
        self.assertTrue((self.store / "releases" / old_bundle / "bundle.json").is_file())
        self.assertTrue((self.store / "releases" / candidate["bundle_id"] / "bundle.json").is_file())


if __name__ == "__main__":
    unittest.main()
