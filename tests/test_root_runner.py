from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNNER = ROOT / "run_tests.py"


class RootRunnerTests(unittest.TestCase):
    def test_all_required_suites_are_children(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('"discover", "-s", "tests"', source)
        self.assertIn('"-B", "implementation-lead/run_tests.py"', source)
        self.assertIn('"-B", "verification-lead/run_tests.py"', source)

    def test_missing_or_failing_child_cannot_be_hidden(self) -> None:
        for verification_child in (None, "raise SystemExit(7)\n"):
            with self.subTest(verification_child=verification_child):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    shutil.copyfile(RUNNER, root / "run_tests.py")
                    tests = root / "tests"
                    tests.mkdir()
                    (tests / "test_ok.py").write_text(
                        "import unittest\n\n"
                        "class Smoke(unittest.TestCase):\n"
                        "    def test_ok(self):\n"
                        "        self.assertTrue(True)\n",
                        encoding="utf-8",
                    )
                    implementation = root / "implementation-lead"
                    implementation.mkdir()
                    (implementation / "run_tests.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
                    if verification_child is not None:
                        verification = root / "verification-lead"
                        verification.mkdir()
                        (verification / "run_tests.py").write_text(verification_child, encoding="utf-8")

                    completed = subprocess.run(
                        [sys.executable, "-B", str(root / "run_tests.py")],
                        cwd=root,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                    )

                    self.assertNotEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                    self.assertIn("verification-lead/run_tests.py", completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
