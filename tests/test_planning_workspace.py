from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "planning-workspace" / "planning_workspace.py"
SPEC = importlib.util.spec_from_file_location("planning_workspace", MODULE_PATH)
assert SPEC and SPEC.loader
planning_workspace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(planning_workspace)


class PlanningWorkspaceTests(unittest.TestCase):
    def test_prepares_project_local_work_root_and_reuses_it(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as raw:
            project = Path(raw).resolve()
            first = planning_workspace.prepare(str(project), "reservation-flow")
            second = planning_workspace.prepare(str(project), "reservation-flow")

            expected_root = project / "docs" / "planning"
            self.assertEqual(first, second)
            self.assertEqual(first["planningRoot"], str(expected_root))
            self.assertEqual(first["behaviorRoot"], str(expected_root / "behavior"))
            self.assertEqual(first["artifactWorkspace"], str(expected_root / "work" / "reservation-flow"))

    def test_prepares_initiative_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as raw:
            project = Path(raw).resolve()
            result = planning_workspace.prepare(str(project), "booking-platform", "initiative")
            self.assertEqual(
                result["artifactWorkspace"],
                str(project / "docs" / "planning" / "initiatives" / "booking-platform"),
            )

    def test_rejects_absent_project_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as raw:
            missing = Path(raw) / "missing"
            with self.assertRaises(planning_workspace.WorkspaceError):
                planning_workspace.prepare(str(missing), "reservation-flow")
            self.assertFalse(missing.exists())

    def test_rejects_symlinked_planning_component(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as raw:
            project = Path(raw).resolve()
            elsewhere = project / "elsewhere"
            elsewhere.mkdir()
            (project / "docs").symlink_to(elsewhere, target_is_directory=True)
            with self.assertRaises(planning_workspace.WorkspaceError):
                planning_workspace.prepare(str(project), "reservation-flow")


if __name__ == "__main__":
    unittest.main()
