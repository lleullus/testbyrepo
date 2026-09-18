from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "iis-workflow/SKILL.md"
CENTRAL = ROOT / "iis-workflow/references/delegated-role-dispatch.md"
SCENARIOS = ROOT / "evaluation/ready-verification/delegated-dispatch-scenarios.md"
SYNC = ROOT / "scripts/sync_installed_iis.py"

PROJECTIONS = {
    "product_thesis": "product-thesis/dispatch/product-thesis.md",
    "investigator": "companion-skills/repository-investigation/dispatch/investigator.md",
    "planner": "companion-skills/scope-plan/dispatch/planner.md",
    "plan_reviewer": "companion-skills/scope-plan/dispatch/reviewer.md",
    "implementer": "companion-skills/scope-implement/dispatch/implementer.md",
    "verifier": "companion-skills/scope-verify/dispatch/verifier.md",
    "probe": "companion-skills/production-heuristic-probing/dispatch/probe.md",
    "purpose_review": "companion-skills/purpose-first-review/dispatch/reviewer.md",
}


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_installed_iis_dispatch_test", SYNC)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load sync_installed_iis")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DelegatedRoleDispatchContractTests(unittest.TestCase):
    def test_workflow_uses_transient_dispatch_contract(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("references/delegated-role-dispatch.md", workflow)
        self.assertIn("Build one transient envelope", workflow)
        self.assertIn("Keep the assignment short and outcome-neutral", workflow)
        self.assertIn("without repeating semantic judgment", workflow)

    def test_common_contract_is_lossless_but_not_new_authority(self) -> None:
        central = CENTRAL.read_text(encoding="utf-8")
        for phrase in (
            "not a workflow stage",
            "transient invocation input",
            "Scope authoring remains Main work",
            "RESULT HANDOFF CHECK",
            "conclusion seeding",
            "Do not introduce a universal `INPUT_CONTRACT_INCOMPLETE` verdict",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, central)
        self.assertNotIn("scope-shaper/dispatch", central)

    def test_each_projection_stays_compact_and_role_specific(self) -> None:
        headings = (
            "## Required",
            "## Optional",
            "## Forbidden framing",
            "## Assignment pattern",
            "## Independence guard",
            "## Result",
        )
        for name, relative in PROJECTIONS.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for heading in headings:
                with self.subTest(role=name, heading=heading):
                    self.assertIn(heading, text)
            self.assertNotIn("FF-01", text)

    def test_independent_roles_reject_caller_framing(self) -> None:
        reviewer = (ROOT / PROJECTIONS["plan_reviewer"]).read_text(encoding="utf-8")
        verifier = (ROOT / PROJECTIONS["verifier"]).read_text(encoding="utf-8")
        probe = (ROOT / PROJECTIONS["probe"]).read_text(encoding="utf-8")

        self.assertIn("not presumed complete, correct or admission-controlling", reviewer)
        self.assertIn("bounded as-built failure frontier independently", verifier)
        self.assertIn("Do not ask the Probe to repeat the verifier", probe)

    def test_direct_owner_boundaries_are_preserved(self) -> None:
        thesis = (ROOT / PROJECTIONS["product_thesis"]).read_text(encoding="utf-8")
        investigation = (ROOT / PROJECTIONS["investigator"]).read_text(encoding="utf-8")
        central = CENTRAL.read_text(encoding="utf-8")

        self.assertIn("Direct Product Thesis work remains the normal arrangement", thesis)
        self.assertIn("current user explicitly selected `SUBAGENT`", investigation)
        self.assertIn("Scope authoring remains Main work", central)

    def test_dispatch_files_are_in_the_skills_payload(self) -> None:
        sync = load_sync_module()
        packaged = {path.relative_to(ROOT).as_posix() for path in sync.payload_files(ROOT)}
        expected = {CENTRAL.relative_to(ROOT).as_posix(), *PROJECTIONS.values()}
        self.assertTrue(expected.issubset(packaged), sorted(expected - packaged))

    def test_behavior_scenarios_are_recorded_not_claimed(self) -> None:
        scenarios = SCENARIOS.read_text(encoding="utf-8")
        self.assertIn("Status: NOT_RUN", scenarios)
        for number in range(1, 8):
            self.assertIn(f"### D{number:02d} —", scenarios)
        self.assertIn("Do not expose the expected observation", scenarios)


if __name__ == "__main__":
    unittest.main()
