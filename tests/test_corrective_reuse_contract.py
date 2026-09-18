from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "evaluation" / "ready-verification" / "corrective-reuse-scenarios.md"


class CorrectiveReuseContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_existing_roles_own_the_corrective_reuse_rules(self) -> None:
        expected = {
            "iis-workflow/SKILL.md": (
                "usable reproducer or evidence limit",
                "still-running independent verifier",
                "admission-controlling premises stay unchanged",
                "faithfully realizes the reviewed method",
                "not alone a Plan revision",
            ),
            "companion-skills/scope-plan/references/plan.md": (
                "executable disposition",
                "existing project test/build/CI path",
                "Classify the boundary by the reviewed premise",
            ),
            "companion-skills/scope-plan/references/review.md": (
                "proposed executable disposition",
                "retrievable from the next-role environment",
                "same-assumption sibling",
            ),
            "companion-skills/scope-implement/references/implement.md": (
                "### Correction reproducer and regression disposition",
                "### Execution handoff",
                "same reviewed state/effect owner",
            ),
            "companion-skills/scope-verify/references/verify.md": (
                "For corrective re-entry, plan evidence acquisition",
                "An invocation-local argument, selector, route or command-usage error",
                "original target/invocation attribution",
            ),
            "companion-skills/production-heuristic-probing/SKILL.md": (
                "### Durable reproducer handoff",
                "bounded same-assumption sibling sweep",
                "targeted probing is the first acquisition path",
            ),
        }
        for path, phrases in expected.items():
            text = self.read(path)
            for phrase in phrases:
                with self.subTest(path=path, phrase=phrase):
                    self.assertIn(phrase, text)

    def test_review_schema_and_workflow_topology_are_unchanged(self) -> None:
        files = [
            "iis-workflow/SKILL.md",
            "companion-skills/scope-plan/SKILL.md",
            "companion-skills/scope-plan/references/review.md",
            "companion-skills/scope-implement/SKILL.md",
            "companion-skills/scope-verify/SKILL.md",
            "companion-skills/production-heuristic-probing/SKILL.md",
        ]
        combined = "\n".join(self.read(path) for path in files)
        self.assertIn("iis-scope-plan-review/v2", combined)
        self.assertNotIn("iis-scope-plan-review/v3", combined)
        self.assertNotIn("Correction Bundle", combined)
        self.assertNotIn("corrective reuse stage", combined.lower())
        self.assertIn("Production Heuristic Probe", combined)
        self.assertIn("fresh whole-Scope verdict", combined)

    def test_adapter_prompts_surface_the_load_bearing_rules(self) -> None:
        expected = {
            "companion-skills/scope-plan/agents/openai.yaml": "existing project check",
            "companion-skills/scope-implement/agents/openai.yaml": "promote it to the existing project regression path",
            "companion-skills/scope-verify/agents/openai.yaml": "still-running verifier",
            "companion-skills/production-heuristic-probing/agents/openai.yaml": "preserve exact reusable content",
        }
        for path, phrase in expected.items():
            with self.subTest(path=path):
                self.assertIn(phrase, self.read(path))

    def test_scenario_inventory_is_explicit_and_not_executed(self) -> None:
        scenarios = SCENARIOS.read_text(encoding="utf-8")
        self.assertIn("Status: NOT_RUN", scenarios)
        for number in range(1, 17):
            with self.subTest(case=number):
                self.assertIn(f"## E{number} —", scenarios)
        self.assertIn(
            "A contract phrase, fixture label or passing unit test is not semantic agent acceptance",
            scenarios,
        )

    def test_product_thesis_frontier_contract_is_not_rewritten_by_this_change(self) -> None:
        product = self.read("product-thesis/SKILL.md")
        exploration = self.read("product-thesis/references/exploration.md")
        self.assertIn("## Minimum semantic sufficiency", product)
        self.assertIn("## Semantic frontier calibration", exploration)


if __name__ == "__main__":
    unittest.main()
