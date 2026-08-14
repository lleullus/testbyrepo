from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
RUNNER = (ROOT / "run_tests.py").read_text(encoding="utf-8")


class RootRunnerTests(unittest.TestCase):
    def test_root_runner_runs_only_planning_tests(self) -> None:
        self.assertIn('"unittest", "discover", "-s", "tests", "-v"', RUNNER)
        for forbidden in (
            "implementation-lead/run_tests.py",
            "verification-lead/run_tests.py",
            "verification-runner/run_tests.py",
            "goal-verification-lead",
            "iis-goal-loop",
        ):
            self.assertNotIn(forbidden, RUNNER)


if __name__ == "__main__":
    unittest.main()
