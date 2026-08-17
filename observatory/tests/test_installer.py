from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import subprocess
import unittest

from iis_observatory.model import __version__


class InstallerTests(unittest.TestCase):
    def test_installs_to_custom_target_without_network(self) -> None:
        source = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as temp:
            target = Path(temp) / "installed-observatory"
            bin_dir = Path(temp) / "bin"
            completed = subprocess.run(
                [
                    "bash",
                    str(source / "install.sh"),
                    "--target",
                    str(target),
                    "--bin-dir",
                    str(bin_dir),
                ],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "HOME": temp},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            command = bin_dir / "iis-observatory"
            self.assertTrue(command.is_symlink())
            version = subprocess.run(
                [str(command), "version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(version.stdout.strip(), __version__)


if __name__ == "__main__":
    unittest.main()
