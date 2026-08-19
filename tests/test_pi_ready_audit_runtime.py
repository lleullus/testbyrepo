from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
NODE_TEST = ROOT / "tests" / "pi_ready_audit_runtime.test.mjs"


class PiReadyAuditRuntimeTests(unittest.TestCase):
    def test_node_runtime_contract(self) -> None:
        completed = subprocess.run(
            ["node", "--test", str(NODE_TEST)],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)


if __name__ == "__main__":
    unittest.main()
