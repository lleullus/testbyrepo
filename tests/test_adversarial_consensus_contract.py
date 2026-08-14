from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
GATE = (ROOT / "matt/skills/adversarial-consensus/SKILL.md").read_text(encoding="utf-8")
MATT = (ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8")
BEHAVIOR = (ROOT / "behavior-design-lead/SKILL.md").read_text(encoding="utf-8")
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class AdversarialConsensusContractTests(unittest.TestCase):
    def test_gate_is_explicit_only_and_requires_exact_counterpart(self) -> None:
        body = normalized(GATE + "\n" + MATT + "\n" + ROUTER)
        for required in (
            "user explicitly instructs Ask Matt to run adversarial consensus",
            "user explicitly designates one exact Challenger counterpart",
            "A Challenger designation without an explicit instruction to run the gate does not activate it",
            "instruction to run the gate without one exact counterpart does not authorize Matt to choose",
            "ADVERSARIAL CONSENSUS: CHALLENGER BINDING REQUIRED",
            "Do not proactively suggest, default to, infer, or auto-enable this gate",
            "do not substitute another counterpart without a new user instruction",
            "A designation alone does not activate the gate",
            "do not silently fall back to ordinary finalization",
            "do not approve or enter `to-spec`",
            "Pass an explicit user instruction to run adversarial consensus",
            "even when its Challenger binding is still missing",
            "only when both the activation instruction and exact binding are current",
        ):
            self.assertIn(required, body)

    def test_intent_anchor_precedes_challenger_and_does_not_replace_user_authority(self) -> None:
        body = normalized(GATE)
        for required in (
            "the complete current user conversation context, including the original words",
            "a later user change supersedes only the intent it actually changes",
            "current user-confirmed Intent Anchor as a derivative representation",
            "Only the user may change the product intent",
            "Intent Anchor Confirmation",
            "Challenger invocation is not allowed before that confirmation",
            "Intent Anchor confirmation is not final product-contract approval",
            "permission to replace the user's original words with Matt's summary",
            "bounded material or exact local sources that the Challenger may receive or inspect",
        ):
            self.assertIn(required, body)
        self.assertLess(body.index("Intent Anchor Confirmation"), body.index("Challenger Boundary"))

    def test_challenger_is_read_only_advisory_and_cannot_cross_consume_roles(self) -> None:
        body = normalized(GATE + "\n" + BEHAVIOR + "\n" + ROUTER)
        for required in (
            "The Challenger is read-only and advisory",
            "may not: - mutate product source",
            "Implementation Subagent, Implementation Research Agent, Verification Runner",
            "Challenger findings are advisory",
            "never becomes a Behavior execution role",
            "pass the binding to implementation or verification roles",
            "Host Subagent Invocation Mechanism",
            "configured authorized Oracle mechanism",
            "Do not reinterpret one mechanism or counterpart as the other",
            "use the `BLOCKED` boundary rather than inventing another transport, agent, or fallback",
        ):
            self.assertIn(required, body)

    def test_main_must_defend_counterattack_expand_and_adjudicate_tradeoffs(self) -> None:
        body = normalized(GATE)
        for required in (
            "Main Defense And Counterattack",
            "Passive acceptance",
            "Intent defense",
            "Candidate defense or honest abandonment",
            "Counterattack",
            "Alternative expansion",
            "Tradeoff adjudication",
            "direction and magnitude of user impact",
            "likelihood, uncertainty, evidence strength",
            "ADOPTED",
            "DEFENDED",
            "RECONSTRUCTED",
            "USER DECISION REQUIRED",
            "RETURN TO SCOPE SHAPER",
        ):
            self.assertIn(required, body)

    def test_debate_requires_substantive_progress_without_fixed_round_limit_or_vote(self) -> None:
        body = normalized(GATE)
        for required in (
            "There is no fixed round count",
            "Repeating a closed objection without new support is not progress",
            "CONCEDE",
            "MAINTAIN",
            "Prefer the same Challenger conversation or resumable context",
            "do not let Matt unilaterally declare victory",
            "ADVERSARIAL CONSENSUS: BLOCKED",
            "not a workflow database, roster, queue, ledger",
        ):
            self.assertIn(required, body)
        self.assertIn("vote, majority rule", body)

    def test_consensus_is_latest_candidate_closure_not_final_user_approval(self) -> None:
        body = normalized(GATE + "\n" + MATT)
        for required in (
            "ADVERSARIAL CONSENSUS REACHED",
            "Challenger reviewed the latest complete candidate",
            "every material objection has an explicit closure",
            "no unresolved user-owned product decision remains",
            "no material candidate change occurred after the Challenger's final review",
            "Consensus is advisory planning closure, not final product authority",
            "final approval",
            "both required before `to-spec`",
            "invalidate the affected consensus",
        ):
            self.assertIn(required, body)

    def test_ask_matt_runs_gate_after_direct_analysis_and_verification_closure_before_to_spec(self) -> None:
        body = normalized(MATT)
        self.assertIn("Optional Adversarial Planning Consensus", body)
        self.assertIn("complete Matt's ordinary first-hand investigation", body)
        self.assertIn("verification-feasibility closure before invoking the Challenger", body)
        self.assertIn("Hold new or changed Behavior/UI authority at draft/approval-ready state", body)
        self.assertIn("and no adversarial-consensus gate is active", body)
        self.assertIn("defer this joint approval until its latest candidate reaches current consensus", body)
        self.assertIn("current `ADVERSARIAL CONSENSUS REACHED`", body)
        self.assertLess(body.index("close the verification-feasibility decisions"), body.index("execute `../adversarial-consensus/SKILL.md`"))
        self.assertLess(body.index("execute `../adversarial-consensus/SKILL.md`"), body.index("Use `to-spec` when"))

    def test_behavior_design_remains_matt_owned_and_ordinary_path_is_unchanged(self) -> None:
        body = normalized(BEHAVIOR)
        for required in (
            "mandatory direct Behavior Design procedure above is never delegated or replaced",
            "after Matt has performed Existing Authority First",
            "Counterexample Stress Test",
            "Matt must directly confirm every load-bearing fact",
            "Ordinary Ask Matt work without that explicit activation keeps the existing approval path unchanged",
        ):
            self.assertIn(required, body)


if __name__ == "__main__":
    unittest.main()
