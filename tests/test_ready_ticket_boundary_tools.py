from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "delivery-tools/ready-ticket"
SYNC = ROOT / "scripts/sync_installed_iis.py"


class ReadyTicketBoundaryContractTests(unittest.TestCase):
    def test_boundary_unit_and_omp_integration_suite(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Ready boundary-tool tests require node")
        tests = sorted(str(path) for path in (BOUNDARY / "tests").glob("*.test.js"))
        self.assertTrue(tests)
        result = subprocess.run([node, "--test", *tests], cwd=ROOT,
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_retired_runtime_surface_is_absent_from_active_boundary_package(self) -> None:
        self.assertFalse((ROOT / "delivery-runtime/ready-ticket-implement").exists())
        text = "\n".join(path.read_text(encoding="utf-8", errors="ignore")
                         for path in BOUNDARY.rglob("*") if path.is_file())
        self.assertNotIn("IIS_READY_RUNTIME_DATA", text)
        self.assertNotIn("ready_argv", text)
        self.assertNotIn("ready_guard", text)


class BundleInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("iis_bundle_test", SYNC)
        cls.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.installer)

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory(prefix="iis-boundary-install-")
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

    def prepare(self) -> dict:
        return self.installer.prepare(self.source, self.store)

    def activate(self, manifest: dict, **kwargs) -> dict:
        return self.installer.activate(self.store, manifest["bundle_id"], {"omp": self.host},
                                       quiescent=True, **kwargs)

    def _legacy_release(self) -> tuple[str, Path]:
        bundle_id = hashlib.sha256(b"legacy-ready-runtime-v2").hexdigest()
        release = self.store / "releases" / bundle_id
        files = {
            "iis-workflow/SKILL.md": b"# legacy router\n",
            "delivery-runtime/ready-ticket-implement/index.js": b"export default function legacy() {}\n",
            "delivery-runtime/ready-ticket-implement/src/core.js": b"export const legacy = true;\n",
        }
        entries = {}
        for relative, data in files.items():
            path = release / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o444)
            entries[relative] = {"sha256": hashlib.sha256(data).hexdigest(), "mode": 0o444}
        release.mkdir(parents=True, exist_ok=True)
        manifest = {"schema": self.installer.SCHEMA, "protocol": 2,
                    "bundle_id": bundle_id, "files": entries}
        (release / "bundle.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (release / "bundle.json").chmod(0o444)
        self.store.mkdir(parents=True, exist_ok=True)
        (self.store / "current").symlink_to(release, target_is_directory=True)
        skill = self.host / "skills/iis-workflow"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.symlink_to(self.store / "current/iis-workflow", target_is_directory=True)
        old_extension = self.host / "extensions" / self.installer.OLD_EXTENSION_NAME
        old_extension.parent.mkdir(parents=True, exist_ok=True)
        old_extension.symlink_to(self.store / "current/delivery-runtime/ready-ticket-implement", target_is_directory=True)
        state = {
            "schema": "iis-install/v2", "bundle_id": bundle_id,
            "hosts": {"omp": str(self.host)},
            "links": {str(skill): str(self.store / "current/iis-workflow"),
                      str(old_extension): str(self.store / "current/delivery-runtime/ready-ticket-implement")},
            "originals": {}, "snapshot": str(self.root / "legacy-snapshot.json"),
            "loaded_identity": "NOT_CHECKED",
        }
        self.installer.atomic_json(self.store / "installed.json", state)
        return bundle_id, old_extension

    def _runtime_record(self, phase: str = "ACTIVE") -> tuple[Path, Path, dict]:
        runtime_root = (self.root / "retired-runtime").resolve()
        record = runtime_root / "executions/execution-1.json"
        record.parent.mkdir(parents=True, exist_ok=True)
        value = {
            "schema_version": 2, "kind": "execution", "execution_id": "execution-1",
            "session_id": "worker-1", "reservation_id": "reservation-1", "phase": phase,
            "active_operation": None, "owned_service": None, "uncertainty": None,
        }
        record.write_text(json.dumps(value, indent=2) + "\n")
        return runtime_root, record, value

    def _retirement_evidence(self, runtime_root: Path, record: Path, *, live_work: str = "absent",
                             effect: str = "none") -> Path:
        evidence = (self.root / "retirement-evidence.json").resolve()
        relative = record.relative_to(runtime_root).as_posix()
        data = {
            "schema": self.installer.RETIREMENT_EVIDENCE_SCHEMA,
            "runtime_root": str(runtime_root),
            "records": {
                relative: {
                    "record_sha256": hashlib.sha256(record.read_bytes()).hexdigest(),
                    "record_kind": "execution", "owner_session": "worker-1",
                    "live_work": live_work, "live_service": "absent",
                    "ownership_disposition": "terminated_or_withdrawn",
                    "effect_disposition": effect,
                    "live_work_absence_evidence": "host process/service inventory: none",
                    "readback_reference": "operator readback: no unresolved product effect",
                }
            },
        }
        evidence.write_text(json.dumps(data, indent=2) + "\n")
        return evidence

    def test_prepare_never_activates_and_rebases_only_internal_references(self) -> None:
        manifest = self.prepare()
        self.assertEqual(manifest["family"], self.installer.NEW_FAMILY)
        self.assertFalse((self.store / "current").exists())
        self.assertFalse(self.host.exists())
        release = self.store / "releases" / manifest["bundle_id"]
        router = (release / "iis-workflow/SKILL.md").read_text()
        self.assertIn(str(release / "matt/skills/to-tickets/validate_ticket.py"), router)
        self.assertIn(str(self.source / "model-selection-guide.md"), router)
        self.router.write_text("new candidate\n")
        self.assertEqual((release / "iis-workflow/SKILL.md").read_text(), router)
        self.assertNotEqual(self.prepare()["bundle_id"], manifest["bundle_id"])

    def test_candidate_rejects_retired_runtime_payload(self) -> None:
        retired = self.source / "delivery-runtime/ready-ticket-implement/index.js"
        retired.parent.mkdir(parents=True, exist_ok=True)
        retired.write_text("legacy\n")
        with self.assertRaisesRegex(ValueError, "retired payload"):
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
        new_extension = self.host / "extensions" / self.installer.NEW_EXTENSION_NAME
        old_extension = self.host / "extensions" / self.installer.OLD_EXTENSION_NAME
        self.assertTrue(new_extension.is_symlink())
        self.assertEqual(os.readlink(new_extension), str(self.store / "current/delivery-tools/ready-ticket"))
        self.assertFalse(old_extension.exists() or old_extension.is_symlink())
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

    def test_rollback_restores_previous_boundary_release_and_rejects_intervening_user_changes(self) -> None:
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

    def test_cli_check_reports_candidate_family_without_loading_host(self) -> None:
        manifest = self.prepare()
        result = subprocess.run([sys.executable, str(SYNC), "check", "--store", str(self.store),
                                 "--bundle", manifest["bundle_id"]], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        parsed = json.loads(result.stdout)
        self.assertEqual(parsed["family"], self.installer.NEW_FAMILY)
        self.assertEqual(parsed["loaded_identity"], "NOT_CHECKED")
        self.assertFalse(self.host.exists())

    def test_old_release_is_checked_by_its_own_manifest_and_cutover_rolls_back_exact_old_identity(self) -> None:
        old_bundle, old_extension = self._legacy_release()
        checked = self.installer.check_install(self.store)
        self.assertEqual(checked["family"], self.installer.OLD_FAMILY)
        self.assertEqual(checked["bundle_id"], old_bundle)
        runtime_root, record, _ = self._runtime_record("COMPLETE")
        before_runtime = record.read_bytes()
        candidate = self.prepare()
        state = self.activate(candidate, retired_ready_runtime_root=runtime_root)
        self.assertEqual(state["family"], self.installer.NEW_FAMILY)
        self.assertFalse(old_extension.exists() or old_extension.is_symlink())
        new_extension = self.host / "extensions" / self.installer.NEW_EXTENSION_NAME
        self.assertTrue(new_extension.is_symlink())
        retirement = state["retired_ready_runtime"]
        self.assertEqual(retirement["summary"]["blockers"], 0)
        self.assertEqual(retirement["summary"]["terminal_history"], 1)
        self.assertTrue(Path(retirement["archive"]["path"]).is_dir())
        self.assertEqual(record.read_bytes(), before_runtime)
        self.installer.rollback(self.store, quiescent=True)
        restored = self.installer.check_install(self.store)
        self.assertEqual(restored["bundle_id"], old_bundle)
        self.assertEqual(restored["family"], self.installer.OLD_FAMILY)
        self.assertTrue(old_extension.is_symlink())
        self.assertFalse(new_extension.exists() or new_extension.is_symlink())
        self.assertEqual(record.read_bytes(), before_runtime)

    def test_old_runtime_cutover_requires_exact_root_and_blocks_unattributed_nonterminal_record(self) -> None:
        self._legacy_release()
        candidate = self.prepare()
        with self.assertRaisesRegex(ValueError, "retired Ready runtime root is required"):
            self.activate(candidate)
        runtime_root, _, _ = self._runtime_record("ACTIVE")
        with self.assertRaisesRegex(ValueError, "live/unsettled/unattributed"):
            self.activate(candidate, retired_ready_runtime_root=runtime_root)
        self.assertEqual(self.installer.check_install(self.store)["family"], self.installer.OLD_FAMILY)

    def test_retirement_evidence_distinguishes_live_blocker_from_settled_stale_record(self) -> None:
        self._legacy_release()
        candidate = self.prepare()
        runtime_root, record, _ = self._runtime_record("PAUSED")
        live = self._retirement_evidence(runtime_root, record, live_work="present")
        with self.assertRaisesRegex(ValueError, "live/unsettled/unattributed"):
            self.activate(candidate, retired_ready_runtime_root=runtime_root,
                          retired_ready_runtime_evidence=live)
        settled = self._retirement_evidence(runtime_root, record, live_work="absent", effect="none")
        state = self.activate(candidate, retired_ready_runtime_root=runtime_root,
                              retired_ready_runtime_evidence=settled)
        records = state["retired_ready_runtime"]["records"]
        self.assertEqual(records[0]["disposition"], "retired_stale_record")
        self.assertEqual(records[0]["owner_session"], "worker-1")
        self.assertEqual(state["retired_ready_runtime"]["summary"]["retired_stale_record"], 1)
        self.assertEqual(state["retired_ready_runtime"]["summary"]["blockers"], 0)


if __name__ == "__main__":
    unittest.main()
