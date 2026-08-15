from __future__ import annotations

import importlib.util
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scope-shaper" / "tools" / "prepare_scope_workspace.py"
spec = importlib.util.spec_from_file_location("scope_workspace", MODULE_PATH)
scope_workspace = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scope_workspace
assert spec.loader is not None
spec.loader.exec_module(scope_workspace)


class ScopeWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_umask = os.umask(0o002)

    def tearDown(self) -> None:
        os.umask(self.original_umask)

    def test_prepare_creates_safe_scope_artifact_directories(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            result = scope_workspace.prepare(str(root), "example-scope")
            for key in (
                "scopeRoot",
                "scopeWorkspace",
                "workPackages",
                "revisions",
                "increments",
                "legacyImport",
                "legacyWorkPackages",
            ):
                path = Path(result[key])
                mode = stat.S_IMODE(path.stat().st_mode)
                self.assertEqual(mode & (stat.S_IWGRP | stat.S_IWOTH), 0, (key, oct(mode)))

    def test_unsafe_existing_scope_directory_blocks_without_explicit_repair(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            result = scope_workspace.prepare(str(root), "example-scope")
            increments = Path(result["increments"])
            increments.chmod(0o775)
            with self.assertRaisesRegex(scope_workspace.ScopeWorkspaceError, "unsafe group/other write"):
                scope_workspace.prepare(str(root), "example-scope")
            repaired = scope_workspace.prepare(str(root), "example-scope", repair_owned_permissions=True)
            self.assertEqual(stat.S_IMODE(Path(repaired["increments"]).stat().st_mode), 0o755)

    def test_repair_option_never_changes_shared_docs_or_planning_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            docs = root / "docs"
            docs.mkdir(mode=0o755)
            docs.chmod(0o775)
            with self.assertRaisesRegex(scope_workspace.ScopeWorkspaceError, "unsafe group/other write"):
                scope_workspace.prepare(str(root), "example-scope", repair_owned_permissions=True)
            self.assertEqual(stat.S_IMODE(docs.stat().st_mode), 0o775)

    def test_symlinked_scope_component_is_rejected_even_with_repair(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw).resolve()
            docs = root / "docs"
            docs.mkdir(mode=0o755)
            elsewhere = root / "elsewhere"
            elsewhere.mkdir(mode=0o755)
            (docs / "planning").symlink_to(elsewhere, target_is_directory=True)
            with self.assertRaisesRegex(scope_workspace.ScopeWorkspaceError, "non-symlink directory"):
                scope_workspace.prepare(str(root), "example-scope", repair_owned_permissions=True)

    def test_invalid_scope_work_slug_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(scope_workspace.ScopeWorkspaceError):
                scope_workspace.prepare(str(Path(raw).resolve()), "BAD/slug")


if __name__ == "__main__":
    unittest.main()
