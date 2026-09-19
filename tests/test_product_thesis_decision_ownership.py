from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PRODUCT = ROOT / "product-thesis" / "SKILL.md"
TEMPLATE = ROOT / "product-thesis" / "templates" / "PRODUCT-THESIS.template.md"
EXPLORATION = ROOT / "product-thesis" / "references" / "exploration.md"
WORKFLOW = ROOT / "iis-workflow" / "SKILL.md"
SCOPE = ROOT / "scope-shaper" / "SKILL.md"
PLAN = ROOT / "companion-skills" / "scope-plan" / "SKILL.md"
PLAN_REF = ROOT / "companion-skills" / "scope-plan" / "references" / "plan.md"
IMPLEMENT = ROOT / "companion-skills" / "scope-implement" / "SKILL.md"
PROBE = ROOT / "companion-skills" / "production-heuristic-probing" / "SKILL.md"


class ProductThesisDecisionOwnershipContractTests(unittest.TestCase):
    def test_product_thesis_can_own_grounded_construction_without_blanket_plan_transfer(self) -> None:
        product = PRODUCT.read_text(encoding="utf-8")
        exploration = EXPLORATION.read_text(encoding="utf-8")
        combined = product + "\n" + exploration

        self.assertNotIn(
            "Technical architecture, files, internal APIs, libraries and scheduling belong to Plan, not Thesis.",
            combined,
        )
        for phrase in (
            "Technical vocabulary does not determine decision ownership.",
            "observed current fact",
            "adopted construction decision",
            "unresolved premise",
            "System grounding and construction decisions",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

    def test_scope_and_plan_preserve_thesis_bound_decisions(self) -> None:
        scope = SCOPE.read_text(encoding="utf-8")
        plan = PLAN.read_text(encoding="utf-8")
        plan_ref = PLAN_REF.read_text(encoding="utf-8")
        self.assertIn("Thesis-bound construction decision", scope)
        self.assertIn("EXISTING authority", plan)
        self.assertIn("EXISTING authority", plan_ref)
        self.assertIn("only methods the Thesis/Transition/Scope leave open", plan)

    def test_reentry_routes_by_bound_decision_owner(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        implement = IMPLEMENT.read_text(encoding="utf-8")
        probe = PROBE.read_text(encoding="utf-8")
        self.assertIn("Thesis-bound factual premise or adopted construction decision", workflow)
        self.assertIn("Small diff, private code or technical vocabulary does not make a decision implementation-local.", implement)
        self.assertIn("earliest decision that must change", probe)
        self.assertIn("Multiple no-finding lanes never cancel one material finding", probe)

    def test_readme_and_template_match_binding_revision_model(self) -> None:
        readme = README.read_text(encoding="utf-8")
        template = TEMPLATE.read_text(encoding="utf-8")
        for phrase in (
            "downstream-binding adopted construction decision",
            "load-bearing factual premise",
            "returns to Product-Thesis",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)
        for phrase in (
            "product obligation",
            "observed current fact",
            "adopted construction decision",
            "unresolved premise",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, template)

    def test_no_reviewer_verifier_or_semantic_final_judge_is_reintroduced(self) -> None:
        texts = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (PRODUCT, EXPLORATION, WORKFLOW, SCOPE, PLAN, PLAN_REF, IMPLEMENT, PROBE)
        )
        self.assertNotIn("independent Product Thesis reviewer", texts)
        self.assertNotIn("scope-verify/SKILL.md", texts)
        self.assertIn(
            "No new Aggregator, Reviewer, Verifier or final judge is introduced.",
            WORKFLOW.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
