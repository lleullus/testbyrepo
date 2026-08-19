from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
MATT = (ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
GATE = (ROOT / "matt/skills/adversarial-consensus/SKILL.md").read_text(encoding="utf-8")
TO_SPEC = (ROOT / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def can_to_spec(
    *,
    active: bool,
    withdrawn: bool = False,
    challenger: bool = False,
    intent_anchor: bool = False,
    consensus: bool = False,
    post_consensus_final_approval: bool = False,
) -> bool:
    if not active or withdrawn:
        return True
    return challenger and intent_anchor and consensus and post_consensus_final_approval


def purpose_first_path(
    *,
    material_problem: bool,
    purpose_achieved: bool,
    purpose_undermined: bool,
) -> str:
    if not material_problem:
        return "NO PROBLEM"
    if not purpose_achieved:
        return "PURPOSE FAILURE"
    if purpose_undermined:
        return "PURPOSE UNDERMINING"
    return "TRADEOFF ELIGIBLE"


class AdversarialConsensusSemanticsFixtureTests(unittest.TestCase):
    def test_purpose_first_path_blocks_tradeoff_until_material_and_purpose_gates_pass(self) -> None:
        self.assertEqual(
            purpose_first_path(
                material_problem=False,
                purpose_achieved=False,
                purpose_undermined=True,
            ),
            "NO PROBLEM",
        )
        self.assertEqual(
            purpose_first_path(
                material_problem=True,
                purpose_achieved=False,
                purpose_undermined=False,
            ),
            "PURPOSE FAILURE",
        )
        self.assertEqual(
            purpose_first_path(
                material_problem=True,
                purpose_achieved=True,
                purpose_undermined=True,
            ),
            "PURPOSE UNDERMINING",
        )
        self.assertEqual(
            purpose_first_path(
                material_problem=True,
                purpose_achieved=True,
                purpose_undermined=False,
            ),
            "TRADEOFF ELIGIBLE",
        )

    def test_active_gate_cannot_be_bypassed_by_explicit_to_spec(self) -> None:
        self.assertTrue(can_to_spec(active=False))
        self.assertTrue(can_to_spec(active=True, withdrawn=True))
        self.assertFalse(can_to_spec(active=True))
        self.assertFalse(can_to_spec(active=True, challenger=True))
        self.assertFalse(can_to_spec(active=True, challenger=True, intent_anchor=True))
        self.assertFalse(
            can_to_spec(
                active=True,
                challenger=True,
                intent_anchor=True,
                consensus=True,
                post_consensus_final_approval=False,
            )
        )
        self.assertTrue(
            can_to_spec(
                active=True,
                challenger=True,
                intent_anchor=True,
                consensus=True,
                post_consensus_final_approval=True,
            )
        )

    def test_pre_consensus_approval_is_not_reused_as_final_approval(self) -> None:
        pre_consensus_approval = True
        self.assertTrue(pre_consensus_approval)
        self.assertFalse(
            can_to_spec(
                active=True,
                challenger=True,
                intent_anchor=True,
                consensus=True,
                post_consensus_final_approval=False,
            )
        )

    def test_material_candidate_delta_makes_prior_consensus_noncurrent(self) -> None:
        consensus = True
        material_candidate_delta = True
        if material_candidate_delta:
            consensus = False
        self.assertFalse(
            can_to_spec(
                active=True,
                challenger=True,
                intent_anchor=True,
                consensus=consensus,
                post_consensus_final_approval=True,
            )
        )

    def test_to_spec_owns_the_single_direct_admission_gate(self) -> None:
        router = normalized(ROUTER)
        to_spec = normalized(TO_SPEC)
        for required in (
            "An explicit To Spec request does not withdraw, satisfy, or bypass an active adversarial-consensus instruction",
            "pass the current adversarial-consensus activation or withdrawal fact to To Spec",
        ):
            self.assertIn(required, router)
        for required in (
            "Adversarial Consensus Admission",
            "active adversarial-consensus instruction",
            "exact `Adversarial Planning Challenger` binding",
            "user-confirmed Intent Anchor",
            "latest complete candidate",
            "post-consensus final integrated user approval",
            "A direct or explicit To Spec request is not withdrawal",
            "TO SPEC: BLOCKED",
        ):
            self.assertIn(required, to_spec)

    def test_optional_gate_cannot_be_model_auto_invoked(self) -> None:
        self.assertIn("disable-model-invocation: true", GATE)

    def test_ui_authority_approval_is_directly_deferred_while_gate_is_active(self) -> None:
        matt = normalized(MATT)
        self.assertIn(
            "When adversarial consensus is active, keep a new or changed `DESIGN.md` at `Status: draft` until the latest complete candidate reaches current adversarial consensus",
            matt,
        )
        self.assertIn(
            "The consensus-post final integrated approval may approve both the completed UI authority and shared understanding in one user response",
            matt,
        )


if __name__ == "__main__":
    unittest.main()
