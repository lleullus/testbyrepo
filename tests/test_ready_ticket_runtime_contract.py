from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "delivery-runtime" / "ready-ticket-implement"
SYNC = ROOT / "scripts" / "sync_installed_ready_runtime.py"


class ReadyTicketRuntimeContractTests(unittest.TestCase):
    def test_runtime_unit_and_omp_integration_suite(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Ready runtime tests require node")
        tests = sorted(str(path) for path in (RUNTIME / "tests").glob("*.test.js"))
        self.assertTrue(tests)
        result = subprocess.run(
            [node, "--test", *tests],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_runtime_package_has_selected_provenance_without_click_contract(self) -> None:
        provenance = (RUNTIME / "CLICK-PROVENANCE.md").read_text(encoding="utf-8")
        readme = (RUNTIME / "README.md").read_text(encoding="utf-8")
        self.assertIn("0.17.0", provenance)
        self.assertIn("behavior-level reimplementation", provenance)
        self.assertIn("copied Click source files: none", provenance)
        self.assertIn("does not decide product meaning", readme)
        self.assertIn("does not", readme)

    def test_install_sync_is_explicit_checkable_and_removable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="iis-ready-runtime-install-") as directory:
            target = Path(directory) / "ready-ticket-implement-runtime"
            env = os.environ.copy()
            env["IIS_READY_RUNTIME_INSTALL_DIR"] = str(target)
            env["IIS_READY_SKILL_INSTALL_DIR"] = str(ROOT / "companion-skills" / "ready-ticket-implement")
            env["IIS_READY_VERIFY_SKILL_INSTALL_DIR"] = str(ROOT / "companion-skills" / "ready-ticket-verify")
            env["IIS_READY_PROBE_SKILL_INSTALL_DIR"] = str(ROOT / "companion-skills" / "ready-ticket-heuristic-probe")

            preflight = subprocess.run(
                [os.fspath(SYNC), "--preflight"], cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(preflight.returncode, 0, preflight.stdout + preflight.stderr)
            self.assertEqual(preflight.stdout.strip(), "READY")

            install = subprocess.run(
                [os.fspath(SYNC)], cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assertTrue((target / "index.js").is_file())
            self.assertFalse((target / "tests").exists())

            check = subprocess.run(
                [os.fspath(SYNC), "--check"], cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertEqual(check.stdout.strip(), "SYNCED")

            remove = subprocess.run(
                [os.fspath(SYNC), "--remove"], cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(remove.returncode, 0, remove.stdout + remove.stderr)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
