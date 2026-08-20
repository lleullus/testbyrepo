from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
MATT = (ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
GATE = (ROOT / "matt/skills/adversarial-consensus/SKILL.md").read_text(encoding="utf-8")
TO_SPEC = (ROOT / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8")
ADAPTIVE = ROOT / "iis-adaptive-planning"
ADAPTIVE_DELEGATED = (ADAPTIVE / "references" / "02-delegated-decision-policy.md").read_text(
    encoding="utf-8"
)
ADAPTIVE_ROUTING = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
    encoding="utf-8"
)


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


def can_adaptive_to_spec(
    *,
    active: bool,
    challenger: bool,
    intent_anchor: bool,
    consensus: bool,
    finalization_provenance: str,
    standing_authority_valid: bool,
    material_authority_delta: str,
    candidate_changed_after_final_review: bool = False,
) -> bool:
    if not active or not challenger or not intent_anchor or not consensus:
        return False
    if candidate_changed_after_final_review:
        return False
    if finalization_provenance == "USER_EXPLICIT":
        return True
    if finalization_provenance == "DELEGATED_RECOMMENDATION":
        return standing_authority_valid and material_authority_delta == "NONE"
    return False


def adaptive_intent_anchor_finalization(
    *,
    active: bool,
    challenger: bool,
    standing_authority_valid: bool,
    anchor_faithful: bool,
    correction_determinable: bool = False,
    unresolved_material_interpretation: bool = False,
    disclosure_expansion: bool = False,
    direct_review_required: bool = False,
) -> str:
    if not active or not challenger:
        return "BLOCKED"
    if direct_review_required:
        return "USER_EXPLICIT_REQUIRED"
    if disclosure_expansion or unresolved_material_interpretation or not standing_authority_valid:
        return "USER_DECISION_REQUIRED"
    if not anchor_faithful and not correction_determinable:
        return "USER_DECISION_REQUIRED"
    return "DELEGATED_RECOMMENDATION"


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


def adversarial_next_step(
    *,
    challenger_opened_material_objection: bool,
    matt_disposition: str,
    challenger_followup: str = "NONE",
    unreviewed_material_candidate_delta: bool = False,
) -> str:
    if matt_disposition == "USER DECISION REQUIRED" or challenger_followup == "USER DECISION":
        return "USER DECISION"
    if matt_disposition == "RETURN TO SCOPE SHAPER":
        return "RETURN TO SCOPE SHAPER"
    if challenger_followup == "MAINTAIN":
        return "CONTINUE"
    if unreviewed_material_candidate_delta:
        return "CONTINUE"
    if challenger_opened_material_objection and challenger_followup != "CONCEDE":
        return "CONTINUE"
    return "COMPLETE ELIGIBLE"


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

    def test_no_material_objection_and_unchanged_candidate_need_no_extra_round(self) -> None:
        self.assertEqual(
            adversarial_next_step(
                challenger_opened_material_objection=False,
                matt_disposition="NO PROBLEM",
            ),
            "COMPLETE ELIGIBLE",
        )

    def test_matt_adjudication_does_not_close_a_challenger_material_objection(self) -> None:
        for disposition in ("NO PROBLEM", "DEFENDED", "ADOPTED", "RECONSTRUCTED"):
            with self.subTest(disposition=disposition):
                self.assertEqual(
                    adversarial_next_step(
                        challenger_opened_material_objection=True,
                        matt_disposition=disposition,
                    ),
                    "CONTINUE",
                )

    def test_challenger_closure_and_unreviewed_candidate_delta_control_continuation(self) -> None:
        self.assertEqual(
            adversarial_next_step(
                challenger_opened_material_objection=True,
                matt_disposition="DEFENDED",
                challenger_followup="CONCEDE",
            ),
            "COMPLETE ELIGIBLE",
        )
        self.assertEqual(
            adversarial_next_step(
                challenger_opened_material_objection=True,
                matt_disposition="DEFENDED",
                challenger_followup="MAINTAIN",
            ),
            "CONTINUE",
        )
        self.assertEqual(
            adversarial_next_step(
                challenger_opened_material_objection=False,
                matt_disposition="ADOPTED",
                challenger_followup="CONCEDE",
                unreviewed_material_candidate_delta=True,
            ),
            "CONTINUE",
        )
        self.assertEqual(
            adversarial_next_step(
                challenger_opened_material_objection=True,
                matt_disposition="DEFENDED",
                challenger_followup="USER DECISION",
            ),
            "USER DECISION",
        )
        for disposition, expected in (
            ("USER DECISION REQUIRED", "USER DECISION"),
            ("RETURN TO SCOPE SHAPER", "RETURN TO SCOPE SHAPER"),
        ):
            with self.subTest(disposition=disposition):
                self.assertEqual(
                    adversarial_next_step(
                        challenger_opened_material_objection=True,
                        matt_disposition=disposition,
                    ),
                    expected,
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

    def test_adaptive_pre_consensus_intent_anchor_finalization_is_bounded_and_automatic(self) -> None:
        base = {
            "active": True,
            "challenger": True,
            "standing_authority_valid": True,
            "anchor_faithful": True,
        }

        self.assertEqual(
            adaptive_intent_anchor_finalization(**base),
            "DELEGATED_RECOMMENDATION",
        )
        self.assertEqual(
            adaptive_intent_anchor_finalization(
                **(base | {"anchor_faithful": False, "correction_determinable": True})
            ),
            "DELEGATED_RECOMMENDATION",
        )
        for override in (
            {"standing_authority_valid": False},
            {"anchor_faithful": False},
            {"unresolved_material_interpretation": True},
            {"disclosure_expansion": True},
        ):
            self.assertEqual(
                adaptive_intent_anchor_finalization(**(base | override)),
                "USER_DECISION_REQUIRED",
            )
        self.assertEqual(
            adaptive_intent_anchor_finalization(**(base | {"direct_review_required": True})),
            "USER_EXPLICIT_REQUIRED",
        )
        self.assertEqual(
            adaptive_intent_anchor_finalization(**(base | {"active": False})),
            "BLOCKED",
        )
        self.assertEqual(
            adaptive_intent_anchor_finalization(**(base | {"challenger": False})),
            "BLOCKED",
        )

        delegated = normalized(ADAPTIVE_DELEGATED)
        routing = normalized(ADAPTIVE_ROUTING)
        self.assertIn("Pre-consensus delegated Intent Anchor finalization", delegated)
        self.assertIn("finalize the exact current Intent Anchor as `DELEGATED_RECOMMENDATION`", delegated)
        self.assertIn("invoke the exact designated Challenger without another user approval", delegated)
        self.assertIn("finalize the Anchor as `DELEGATED_RECOMMENDATION`", routing)
        self.assertIn("explicit current request for direct Anchor review", routing)

    def test_adaptive_post_consensus_finalization_accepts_only_valid_current_authority(self) -> None:
        base = {
            "active": True,
            "challenger": True,
            "intent_anchor": True,
            "consensus": True,
            "standing_authority_valid": True,
            "material_authority_delta": "NONE",
        }

        self.assertTrue(
            can_adaptive_to_spec(
                **base,
                finalization_provenance="USER_EXPLICIT",
            )
        )
        self.assertTrue(
            can_adaptive_to_spec(
                **base,
                finalization_provenance="DELEGATED_RECOMMENDATION",
            )
        )
        self.assertFalse(
            can_adaptive_to_spec(
                **(base | {"standing_authority_valid": False}),
                finalization_provenance="DELEGATED_RECOMMENDATION",
            )
        )
        for delta in ("MATERIAL", "UNCERTAIN"):
            self.assertFalse(
                can_adaptive_to_spec(
                    **(base | {"material_authority_delta": delta}),
                    finalization_provenance="DELEGATED_RECOMMENDATION",
                )
            )
        self.assertFalse(
            can_adaptive_to_spec(
                **base,
                finalization_provenance="NONE",
            )
        )
        for missing_gate in ("active", "challenger", "intent_anchor", "consensus"):
            self.assertFalse(
                can_adaptive_to_spec(
                    **(base | {missing_gate: False}),
                    finalization_provenance="DELEGATED_RECOMMENDATION",
                )
            )
        self.assertFalse(
            can_adaptive_to_spec(
                **base,
                finalization_provenance="DELEGATED_RECOMMENDATION",
                candidate_changed_after_final_review=True,
            )
        )

    def test_adaptive_overlay_assigns_delta_to_ask_matt_without_rewriting_baseline_gate(self) -> None:
        delegated = normalized(ADAPTIVE_DELEGATED)
        routing = normalized(ADAPTIVE_ROUTING)
        baseline_to_spec = normalized(TO_SPEC)

        self.assertIn("Ask Matt alone owns the authority-delta review", delegated)
        self.assertIn("The Challenger owns review and objection closure", delegated)
        self.assertIn("To Spec owns admission/projection after finalization", delegated)
        self.assertIn("authority delta is exactly `NONE`", delegated)
        self.assertIn("ordinary non-Adaptive To Spec still requires", routing)
        self.assertIn("do not reinterpret the Mandate or Run Contract", routing)
        self.assertIn("post-consensus final integrated user approval", baseline_to_spec)

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
