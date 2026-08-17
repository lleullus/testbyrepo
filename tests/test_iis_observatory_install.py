from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = ROOT / "iis-observatory"
INSTALLED_SKILL = Path.home() / ".codex" / "skills" / "iis-observatory"
CANONICAL_CLI = ROOT / "observatory" / "bin" / "iis-observatory"
INSTALLED_CLI = Path.home() / ".local" / "bin" / "iis-observatory"


class IISObservatoryInstallTests(unittest.TestCase):
    def test_live_installed_skill_matches_canonical_source(self) -> None:
        for relative in (Path("SKILL.md"), Path("agents/openai.yaml")):
            canonical = CANONICAL_SKILL / relative
            installed = INSTALLED_SKILL / relative
            self.assertTrue(canonical.is_file(), canonical)
            self.assertTrue(installed.is_file(), installed)
            self.assertEqual(canonical.read_bytes(), installed.read_bytes(), relative)

    def test_global_cli_link_targets_canonical_observatory(self) -> None:
        self.assertTrue(INSTALLED_CLI.is_symlink(), INSTALLED_CLI)
        self.assertEqual(INSTALLED_CLI.resolve(), CANONICAL_CLI.resolve())

    def test_global_cli_executes_same_version_as_canonical_cli(self) -> None:
        global_result = subprocess.run(
            [str(INSTALLED_CLI), "version"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        canonical_result = subprocess.run(
            [str(CANONICAL_CLI), "version"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertEqual(global_result.stdout.strip(), canonical_result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
