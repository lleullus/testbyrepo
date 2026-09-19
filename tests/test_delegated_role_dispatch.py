from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DispatchPayloadTests(unittest.TestCase):
    def test_callable_projections_and_assurance_tools_ship_without_retired_roles(self):
        spec = importlib.util.spec_from_file_location("iis_dispatch_payload", ROOT / "scripts/sync_installed_iis.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        packaged = {path.relative_to(ROOT).as_posix() for path in installer.payload_files(ROOT)}
        expected = {
            "product-thesis/dispatch/product-thesis.md",
            "companion-skills/repository-investigation/dispatch/investigator.md",
            "companion-skills/purpose-first-review/dispatch/reviewer.md",
            "companion-skills/scope-plan/dispatch/planner.md",
            "companion-skills/scope-implement/dispatch/implementer.md",
            "companion-skills/production-heuristic-probing/dispatch/probe.md",
            "iis-workflow/references/delegated-role-dispatch.md",
            "iis-workflow/references/assurance.md",
            "iis-workflow/tools/assurance.py",
        }
        self.assertTrue(expected.issubset(packaged), sorted(expected - packaged))
        self.assertFalse(any(path.startswith("companion-skills/scope-verify/") for path in packaged))
        self.assertNotIn("companion-skills/scope-plan/dispatch/reviewer.md", packaged)
        self.assertNotIn("companion-skills/scope-plan/references/review.md", packaged)
