from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "product-thesis/SKILL.md"
CASES = ROOT / "evaluation/product-thesis/cases.json"


class ProductThesisContractTests(unittest.TestCase):
    def test_skill_closes_meaning_without_stealing_downstream_authority(self) -> None:
        body = " ".join(SKILL.read_text(encoding="utf-8").split())
        for required in (
            "Reason to Exist",
            "Core Utility",
            "Core Completion Loop",
            "Truth / Causal Invariants",
            "Required Outcomes / Means",
            "Candidate / Supporting Means",
            "Non-Core / Defer Candidates",
            "Success Observation",
            "CALIBRATED | USER_INPUT_REQUIRED",
            "The current planning owner directly performs this phase",
            "It has no separate agent, controller, queue, database, persistent state machine, retry ledger, or approval ceremony",
            "Current explicit user instruction and constraints",
            "Scope Shaper owns those decisions",
            "Ask Matt and Behavior/UI authorities own them",
            "Product Thesis never selects Scope Shaper versus Ask Matt by itself",
            "Do not add a separate required Product Thesis artifact",
            "Product Meaning Binding",
            "iis-product-meaning/v1",
            "not authentication, signing, tamper-proofing, or proof of semantic correctness",
            "Product Thesis -> first binding semantic fidelity",
            "binding -> actual Scope/Spec contract semantic fidelity",
        ):
            self.assertIn(required, body)

    def test_conditional_admission_preserves_existing_leaf_routes(self) -> None:
        body = " ".join(SKILL.read_text(encoding="utf-8").split())
        for required in (
            "Apply explicit planning-leaf and read-only classifications before broader inference",
            "status-only or planning-state inspection",
            "faithful To Spec or To Tickets projection of current approved authority",
            "exact existing Ready Ticket planning, implementation, or verification",
            "Do not rerun the phase merely because a new session or later leaf begins",
            "A projection leaf that discovers a material product-meaning defect returns to its existing product-planning owner",
        ):
            self.assertIn(required, body)

    def test_router_scope_matt_and_adaptive_preserve_one_authority_split(self) -> None:
        router = " ".join((ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8").split())
        scope = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        matt = " ".join((ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8").split())
        to_spec = " ".join((ROOT / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8").split())
        adaptive = " ".join((ROOT / "iis-adaptive-planning/SKILL.md").read_text(encoding="utf-8").split())
        run_contract = " ".join((ROOT / "iis-adaptive-planning/references/09-run-contract.md").read_text(encoding="utf-8").split())

        for required in (
            "Apply explicit leaf and read-only classifications first",
            "Product Thesis is complete before the existing next-increment admission",
            "it does not select Scope Shaper versus Ask Matt",
        ):
            self.assertIn(required, router)
        for required in (
            "This applies to an explicit Scope Shaper request",
            "The selected Increment may establish one durable product state",
            "it need not complete the whole loop",
            "The immutable `SHAPE-NNN` revision preserves those fields",
        ):
            self.assertIn(required, scope)
        for required in (
            "Apply Product Thesis admission before evaluating the direct request's next-increment readiness",
            "it does not make a broad request next-increment-ready",
            "exact `Product Meaning Binding` preserved in the exact immutable Scope revision",
            "five binding values needed for To Spec",
            "binding is product-level meaning and never widens the admitted Increment",
        ):
            self.assertIn(required, matt)
        for required in (
            "Source-Scope-Revision",
            "## Product Meaning Binding",
            "product_meaning_binding.py validate-spec",
            "SPEC.Source-Increment -> INC.Source-Scope-Revision -> revisions/SHAPE-NNN.md",
            "does not prove Product Thesis correctness",
        ):
            self.assertIn(required, to_spec)
        for required in (
            "conditional read-only Product Thesis calibration",
            "Mandate normalization or revalidation",
            "required /승인게이트 release when applicable",
            "Do not recalibrate on ordinary Ticket progress",
        ):
            self.assertIn(required, adaptive)
        self.assertNotIn("Sniper Principle at closure", run_contract)
        self.assertNotIn("feature-list substitution", run_contract)
        self.assertIn("Run Contract closure preserves product meaning", run_contract)
        self.assertIn("This fidelity check must not expand the invocation into the whole Core Completion Loop", run_contract)

    def test_fixed_semantic_cohort_covers_required_counterexamples(self) -> None:
        cohort = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(cohort["schema"], "iis-product-thesis-evaluation/v1")
        self.assertEqual(cohort["protocol"]["variants"], ["baseline", "candidate"])
        self.assertEqual(cohort["protocol"]["repetitions"], [1, 2])
        self.assertEqual(cohort["protocol"]["model"], "opencodex/gpt-5.6-luna")
        self.assertEqual(cohort["protocol"]["thinking"], "max")
        self.assertTrue(cohort["protocol"]["raw_evidence_required"])
        self.assertFalse(cohort["protocol"]["automatic_semantic_acceptance"])
        self.assertTrue(cohort["protocol"]["freeze_before_execution"])
        case_ids = [case["id"] for case in cohort["cases"]]
        self.assertEqual(
            case_ids,
            [
                "A-feature-list-to-utility",
                "B-broken-watch-loop",
                "C-fake-telemetry",
                "D-causal-identity",
                "E-non-core-clutter",
                "F-user-required-means",
                "G-explicit-narrow-stage",
                "H-approved-spec-projection",
                "I-status-only",
                "J-anti-overreach-control",
                "K-current-thesis-reuse",
            ],
        )
        for case in cohort["cases"]:
            self.assertTrue(case["prompt"])
            self.assertTrue(case["required_observations"])
            self.assertTrue(case["forbidden_observations"])


if __name__ == "__main__":
    unittest.main()
