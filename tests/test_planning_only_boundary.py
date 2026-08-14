from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class PlanningOnlyBoundaryTests(unittest.TestCase):
    def test_retired_delivery_directories_are_absent(self) -> None:
        for name in (
            "iis-goal-loop",
            "implementation-lead",
            "verification-lead",
            "verification-runner",
            "goal-verification-lead",
        ):
            self.assertFalse((ROOT / name).exists(), name)

    def test_active_router_and_readme_do_not_route_retired_delivery(self) -> None:
        body = (
            (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
            + "\n"
            + (ROOT / "README.md").read_text(encoding="utf-8")
        )
        for forbidden in (
            "iis-goal-loop/SKILL.md",
            "implementation-lead/SKILL.md",
            "verification-lead/SKILL.md",
            "verification-runner/SKILL.md",
            "goal-verification-lead/SKILL.md",
            "GOAL ACHIEVED",
        ):
            self.assertNotIn(forbidden, body)

    def test_to_tickets_is_terminal_planning_output(self) -> None:
        body = " ".join((ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Planning ends when the reviewed Tickets are `ready`", body)
        self.assertIn("terminal IIS planning output", body)
        self.assertIn("Any later implementation or verification is outside IIS Planning", body)


if __name__ == "__main__":
    unittest.main()
