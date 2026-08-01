from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


planning_workspace = load_module(
    "planning_workspace",
    REPOSITORY_ROOT / "planning-workspace/planning_workspace.py",
)
project_map_validator = load_module(
    "project_map_validator",
    REPOSITORY_ROOT / "project-shaper/skills/project-shaper/tools/validate_project_map.py",
)


class PlanningWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.product = self.root / "product"
        self.product.mkdir()
        self.default_root = self.root / "managed" / "opencode" / "planning"
        self.default_root.parent.parent.mkdir()
        self.original_default = planning_workspace.DEFAULT_PLANNING_ROOT
        planning_workspace.DEFAULT_PLANNING_ROOT = self.default_root

    def tearDown(self) -> None:
        planning_workspace.DEFAULT_PLANNING_ROOT = self.original_default
        self.temporary.cleanup()

    def test_default_workspace_is_exclusive_external_owner_only_and_reusable(self) -> None:
        first = planning_workspace.prepare(str(self.product), "external-planning")
        second = planning_workspace.prepare(str(self.product), "external-planning")
        first_path = Path(first["planningWorkspace"])
        second_path = Path(second["planningWorkspace"])
        self.assertNotEqual(first_path, second_path)
        self.assertTrue(first_path.is_dir())
        self.assertEqual(0o700, first_path.stat().st_mode & 0o777)
        self.assertEqual(os.geteuid(), first_path.stat().st_uid)
        self.assertFalse(first_path.is_relative_to(self.product))
        self.assertFalse(self.product.is_relative_to(first_path))
        self.assertFalse((self.product / ".scratch").exists())

        reused = planning_workspace.prepare(str(self.product), "external-planning", str(first_path))
        self.assertEqual(str(first_path), reused["planningWorkspace"])
        self.assertFalse(reused["created"])
        self.assertTrue(reused["defaultWorkspace"])
        self.assertEqual(first["taskId"], reused["taskId"])

    def test_supplied_workspace_can_be_created_only_under_safe_canonical_parent(self) -> None:
        durable_parent = self.root / "durable"
        durable_parent.mkdir(mode=0o700)
        workspace = durable_parent / "work"
        result = planning_workspace.prepare(str(self.product), "work", str(workspace))
        self.assertTrue(result["created"])
        self.assertEqual(workspace, Path(result["planningWorkspace"]))
        self.assertEqual(0o700, workspace.stat().st_mode & 0o777)

        unsafe_parent = self.root / "unsafe"
        unsafe_parent.mkdir()
        os.chmod(unsafe_parent, 0o777)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_WORKSPACE_PARENT"):
            planning_workspace.prepare(str(self.product), "work", str(unsafe_parent / "work"))

    def test_slug_and_product_overlap_fail_closed(self) -> None:
        for slug in ("", ".", "..", "Bad", "bad/name", "bad\\name", "bad--", "valid--slug"):
            with self.subTest(slug=slug), self.assertRaisesRegex(
                planning_workspace.WorkspaceError, "INVALID_WORK_SLUG"
            ):
                planning_workspace.prepare(str(self.product), slug)

        for workspace in (self.product, self.product / "planning", self.root):
            with self.subTest(workspace=workspace), self.assertRaisesRegex(
                planning_workspace.WorkspaceError, "WORKSPACE_PROJECT_OVERLAP"
            ):
                planning_workspace.prepare(str(self.product), "work", str(workspace))

    def test_future_root_prepares_without_provisioning_then_revalidates_strictly(self) -> None:
        future_product = self.root / "future-product"
        result = planning_workspace.prepare_future_root(str(future_product), "future-work")
        workspace = Path(result["planningWorkspace"])
        self.assertFalse(future_product.exists())
        self.assertIsNone(result["projectRoot"])
        self.assertEqual(str(future_product), result["futureProjectRoot"])
        self.assertFalse(result["rootReady"])

        future_product.mkdir()
        strict = planning_workspace.prepare(str(future_product), "future-work", str(workspace))
        self.assertEqual(str(future_product), strict["projectRoot"])
        self.assertEqual(str(workspace), strict["planningWorkspace"])
        self.assertFalse(strict["created"])

    def test_future_root_lexical_identity_and_disjointness_fail_closed(self) -> None:
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "INVALID_FUTURE_PROJECT_ROOT"):
            planning_workspace.prepare_future_root(str(self.root / "future" / ".." / "product"), "work")
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "FUTURE_PROJECT_ROOT_EXISTS"):
            planning_workspace.prepare_future_root(str(self.product), "work")

        durable = self.root / "durable"
        durable.mkdir(mode=0o700)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "WORKSPACE_PROJECT_OVERLAP"):
            planning_workspace.prepare_future_root(
                str(durable / "future-product"),
                "work",
                str(durable),
            )

        unsafe = self.root / "unsafe-future-parent"
        unsafe.mkdir()
        os.chmod(unsafe, 0o777)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_FUTURE_PROJECT_ANCESTOR"):
            planning_workspace.prepare_future_root(str(unsafe / "product"), "work")

    def test_reused_default_workspace_revalidates_task_and_workspace_modes(self) -> None:
        first = planning_workspace.prepare(str(self.product), "mode-check")
        workspace = Path(first["planningWorkspace"])
        task_directory = workspace.parent

        os.chmod(task_directory, 0o777)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_TASK_DIRECTORY"):
            planning_workspace.prepare(str(self.product), "mode-check", str(workspace))
        os.chmod(task_directory, 0o700)

        os.chmod(workspace, 0o770)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_WORKSPACE"):
            planning_workspace.prepare(str(self.product), "mode-check", str(workspace))

    def test_reused_default_workspace_requires_owner_only_task_and_workspace_modes(self) -> None:
        first = planning_workspace.prepare(str(self.product), "owner-only")
        workspace = Path(first["planningWorkspace"])
        task_directory = workspace.parent

        os.chmod(task_directory, 0o755)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_TASK_DIRECTORY"):
            planning_workspace.prepare(str(self.product), "owner-only", str(workspace))
        os.chmod(task_directory, 0o700)

        os.chmod(workspace, 0o755)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_WORKSPACE"):
            planning_workspace.prepare(str(self.product), "owner-only", str(workspace))

    def test_default_root_paths_cannot_be_reclassified_as_durable_workspaces(self) -> None:
        first = planning_workspace.prepare(str(self.product), "original-slug")
        workspace = Path(first["planningWorkspace"])
        os.chmod(self.default_root.parent, 0o777)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "INVALID_DEFAULT_WORKSPACE"):
            planning_workspace.prepare(str(self.product), "different-slug", str(workspace))
        os.chmod(self.default_root.parent, 0o700)

        malformed = workspace / "deeper"
        malformed.mkdir(mode=0o700)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "INVALID_DEFAULT_WORKSPACE"):
            planning_workspace.prepare(str(self.product), "deeper", str(malformed))

    def test_reused_default_workspace_rejects_task_directory_retarget(self) -> None:
        first = planning_workspace.prepare(str(self.product), "retarget-check")
        workspace = Path(first["planningWorkspace"])
        task_directory = workspace.parent
        original_workspace = workspace
        moved = task_directory.with_name(task_directory.name + "-moved")
        task_directory.rename(moved)
        task_directory.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_WORKSPACE"):
            planning_workspace.prepare(str(self.product), "retarget-check", str(original_workspace))

    def test_unsafe_default_managed_ancestor_and_symlink_are_not_adopted(self) -> None:
        opencode = self.default_root.parent
        opencode.mkdir()
        os.chmod(opencode, 0o777)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_MANAGED_ANCESTOR"):
            planning_workspace.prepare(str(self.product), "work")

        os.chmod(opencode, 0o700)
        target = self.root / "target"
        target.mkdir()
        self.default_root.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(planning_workspace.WorkspaceError, "UNSAFE_MANAGED_ANCESTOR"):
            planning_workspace.prepare(str(self.product), "work")

    def test_external_project_map_and_relative_brief_validate_without_product_pollution(self) -> None:
        workspace = Path(planning_workspace.prepare(str(self.product), "initiative")["planningWorkspace"])
        briefs = workspace / "matt-briefs"
        briefs.mkdir()
        project_map = workspace / "PROJECT-MAP.md"
        brief = briefs / "WP-001.md"
        project_map.write_text(
            "# Initiative\n"
            "Status: approved\nOwner: user\n"
            f"Project-Root: {self.product}\nInitiative-Slug: initiative\n\n"
            "## Product Outcome\nA user can complete the core job.\n\n"
            "## Product Boundary\nOnly the core job.\n\n"
            "## Reference Interpretation\nNo reference product.\n\n"
            "## MVP Cut\n- WP-001\n\n"
            "## Work Packages\n"
            "### WP-001: Core job\n\n"
            "Package-Status: ready-for-matt\nMatt-Brief: ./matt-briefs/WP-001.md\n\n"
            "#### Outcome\nA user can complete the core job.\n\n"
            "#### Includes\n- Core job\n\n"
            "#### Excludes\n- Expansion\n\n"
            "#### Depends On\nNone\n\n"
            "#### Why This Is One Package\nOne acceptance moment.\n\n"
            "#### Why It Is Separate\nExpansion is independently acceptable.\n\n"
            "#### Decisions Reserved For Matt\nNone\n\n"
            "## Dependency Map\n- WP-001: None\n\n"
            "## Deferred Capabilities\n- Expansion\n\n"
            "## Initiative-Level Open Questions\nNone\n\n"
            "## Matt Handoff Queue\n- ./matt-briefs/WP-001.md\n",
            encoding="utf-8",
        )
        brief.write_text(
            "# WP-001: Core job\n"
            "Status: ready-for-matt\nParent-Project-Map: ../PROJECT-MAP.md\n"
            "Work-Package: WP-001\n"
            f"Project-Root: {self.product}\nSuggested-Work-Slug: core-job\n\n"
            "## Authority Notice\nThis projects an approved initiative decomposition. It is not an approved package Spec. Matt requires user-confirmed understanding before to-spec.\n\n"
            "## Product Context\nThe core job starts the initiative.\n\n"
            "## Package Outcome\nA user can complete the core job.\n\n"
            "## Included Product Scope\n- Core job\n\n"
            "## Excluded Sibling Scope\n- Expansion\n\n"
            "## Dependencies\nNone\n\n"
            "## Adopted Initiative Decisions\n- Core job is MVP.\n\n"
            "## Decisions Reserved For Matt\nNone\n\n"
            "## Reference Material\nNone\n\n"
            "## Matt Start\nPlan only this work package, confirm the frame, then continue with ask-matt.\n",
            encoding="utf-8",
        )
        report = project_map_validator.validate(project_map)
        self.assertEqual([], [(item.code, item.message) for item in report.errors])
        self.assertFalse((self.product / ".scratch").exists())


if __name__ == "__main__":
    unittest.main()
