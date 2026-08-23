from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "iis-adaptive-planning"
INSTALLED = Path.home() / ".codex" / "skills" / "iis-adaptive-planning"


class IISAdaptivePlanningTests(unittest.TestCase):
    def test_skill_payload_is_lean_and_self_contained(self) -> None:
        self.assertTrue((ADAPTIVE / "SKILL.md").is_file())
        self.assertTrue((ADAPTIVE / "agents" / "openai.yaml").is_file())

        top_level = {p.name for p in ADAPTIVE.iterdir()}
        self.assertEqual(top_level, {"SKILL.md", "agents", "references", "templates"})

        for forbidden in ("README.md", "INSTALL.md", "CHANGELOG.md", "MANIFEST.json"):
            self.assertFalse((ADAPTIVE / forbidden).exists(), forbidden)

    def test_adaptive_is_explicit_opt_in_and_baseline_remains_default(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        coexistence = (ADAPTIVE / "references" / "00-baseline-coexistence.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Use only when the user explicitly requests IIS Adaptive Planning", skill)
        self.assertIn("If Adaptive activation is absent", skill)
        self.assertIn("Leave the request to Baseline IIS", skill)
        self.assertIn("Baseline IIS remains independently complete", coexistence)
        self.assertIn("Do not edit `iis-workflow`", coexistence)

    def test_baseline_leaf_files_are_not_modified_to_route_adaptive(self) -> None:
        baseline_files = (
            ROOT / "iis-workflow" / "SKILL.md",
            ROOT / "scope-shaper" / "SKILL.md",
            ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md",
            ROOT / "matt" / "skills" / "to-spec" / "SKILL.md",
            ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md",
        )
        for path in baseline_files:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("iis-adaptive-planning", text, path)

    def test_baseline_projection_uses_self_review_with_optional_approval(self) -> None:
        scope = (ROOT / "scope-shaper" / "SKILL.md").read_text(encoding="utf-8")
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("one user confirmation", scope)
        self.assertIn("Require explicit user approval", matt)
        self.assertIn("Self-review is a leaf-local transition guard", spec)
        self.assertIn("If the current user explicitly requires separate user or planning-owner", spec)
        self.assertIn("Self-review is a leaf-local transition guard", tickets)
        self.assertIn("If the current user explicitly requires separate user or planning-owner", tickets)
        for text in (spec, tickets):
            self.assertNotIn("self-reviewing", text)
            self.assertNotIn("review-failed", text)

        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Baseline To Spec self-review/adoption guard", routing)
        self.assertIn("Baseline To Tickets whole-Set self-review/readiness guard", routing)

    def test_adaptive_delta_preserves_hard_boundaries(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        delegated = (ADAPTIVE / "references" / "02-delegated-decision-policy.md").read_text(
            encoding="utf-8"
        )
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("does not implement or verify Tickets", skill)
        self.assertIn("Ready Ticket Set", routing)
        self.assertIn("hard STOP", routing)
        self.assertIn("auto-enable adversarial consensus", skill)
        self.assertIn("Special gates not covered by standing delegation", delegated)
        self.assertIn("Adversarial Planning Challenger", delegated)

    def test_adaptive_intent_anchor_can_finalize_by_delegation_without_changing_baseline(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        coexistence = (ADAPTIVE / "references" / "00-baseline-coexistence.md").read_text(
            encoding="utf-8"
        )
        delegated = (ADAPTIVE / "references" / "02-delegated-decision-policy.md").read_text(
            encoding="utf-8"
        )
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )
        baseline_gate = (ROOT / "matt" / "skills" / "adversarial-consensus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        baseline_to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        baseline_gate_normalized = " ".join(baseline_gate.split())

        self.assertIn("Pre-consensus delegated Intent Anchor finalization", delegated)
        self.assertIn("finalize the exact current Intent Anchor as `DELEGATED_RECOMMENDATION`", delegated)
        self.assertIn("invoke the exact designated Challenger without another user approval", delegated)
        self.assertIn("Ordinary non-Adaptive Intent Anchor confirmation remains direct-user-only", delegated)
        self.assertIn("ordinary Baseline adversarial consensus still requires direct user confirmation", coexistence)
        self.assertIn("explicit current request for direct Anchor review", routing)
        self.assertIn("satisfies the Baseline `user-confirmed Intent Anchor` admission condition", routing)
        self.assertIn("a user-confirmed Intent Anchor for the current candidate", baseline_to_spec)
        self.assertNotIn(
            "activation, exact Challenger designation, and the Intent Anchor remain direct-user-only",
            skill,
        )
        self.assertNotIn(
            "activation, exact Challenger binding, and user-confirmed Intent Anchor remain direct-user-only",
            coexistence,
        )

        # Baseline adversarial consensus remains unchanged and still owns direct confirmation.
        self.assertIn("Ask the user only to confirm", baseline_gate_normalized)
        self.assertIn(
            "Challenger invocation is not allowed before that confirmation",
            baseline_gate_normalized,
        )

    def test_post_consensus_delegated_finalization_is_adaptive_only_and_scope_safe(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        coexistence = (ADAPTIVE / "references" / "00-baseline-coexistence.md").read_text(
            encoding="utf-8"
        )
        delegated = (ADAPTIVE / "references" / "02-delegated-decision-policy.md").read_text(
            encoding="utf-8"
        )
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Ask Matt alone performs the post-consensus authority-delta review", skill)
        self.assertIn("Post-consensus delegated finalization", delegated)
        self.assertIn("Ask Matt alone owns the authority-delta review", delegated)
        self.assertIn("authority delta is exactly `NONE`", delegated)
        self.assertIn("For `MATERIAL` or `UNCERTAIN`", delegated)
        self.assertIn("does not revise the outer Run Contract", delegated)
        self.assertIn("ordinary non-Adaptive To Spec still requires", routing)
        self.assertIn("do not reinterpret the Mandate or Run Contract", routing)
        self.assertIn("finalization is `USER_EXPLICIT` or `DELEGATED_RECOMMENDATION`", routing)

        # The earlier whole-run scope closure remains authoritative across finalization.
        self.assertIn("Required-item coverage invariant", contract)
        self.assertIn("`LEAF_APPROVAL_ONLY`", contract)
        self.assertIn("`REQUIRED_REMAINS_AFTER_DELIVERY`", contract)
        self.assertIn("do not revise the Run Contract Goal Outcome", routing)

        # Baseline remains directly user-approved and unchanged by the Adaptive overlay.
        self.assertIn("Require explicit user approval", matt)
        self.assertIn("post-consensus final integrated user approval", to_spec)
        self.assertIn("or change ordinary Baseline finalization", coexistence)

    def test_adaptive_activation_defaults_current_increment_delivery_with_stop_override(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        terminal = (ADAPTIVE / "references" / "07-terminal-report.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Under explicit Adaptive activation", skill)
        self.assertIn("Explicit Adaptive activation", continuation)
        self.assertIn("CURRENT_INCREMENT_DELIVERED", contract)
        self.assertIn("default current-Increment terminal", contract)
        self.assertIn("planning only", continuation)
        self.assertIn("ready-ticket-implement", continuation)
        self.assertIn("ready-ticket-verify", continuation)
        self.assertIn("continues the current Increment", terminal)
        self.assertIn("`ready-ticket-implement` retains its normal `SUBAGENT` default", continuation)
        self.assertIn("`ready-ticket-verify` owns one exact Ready Ticket fresh verification", continuation)
        self.assertIn("For verification, use DIRECT-only `ready-ticket-verify`", continuation)
        self.assertIn("Do not pass `Delegated Worker: yes` from Adaptive", continuation)
        self.assertNotIn("Auditor Count", continuation)
        self.assertNotIn("AC Runtime Auditor", continuation)

    def test_single_entry_outer_main_and_owner_stop_are_explicit(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )
        terminal = (ADAPTIVE / "references" / "07-terminal-report.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("There is no separately invokable Adaptive Run skill", skill)
        self.assertIn("Outer Main", skill)
        self.assertIn("current explicit Adaptive invocation", skill)
        self.assertIn("does not become a second planning, implementation, or verification authority", skill)
        self.assertIn("Planning owner result: STOP", terminal)
        self.assertIn("Returned to: Outer Main", terminal)
        self.assertIn("owner STOP is not an invocation STOP", routing)
        self.assertIn("thin invocation-local handoff owner", continuation)

        payload = "\n".join(
            path.read_text(encoding="utf-8")
            for path in ADAPTIVE.rglob("*")
            if path.is_file() and path.suffix in {".md", ".yaml"}
        )
        self.assertNotIn("outer caller", payload.lower())

    def test_end_to_end_delivery_can_reenter_adaptive_for_planning_failures(self) -> None:
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        for classification in (
            "CONTRACT_OVERREACH",
            "CURRENT_INCREMENT_MISMATCH",
            "IMPLEMENTATION_DEFECT",
            "VERIFICATION_MECHANISM_DEFECT",
            "INCONCLUSIVE",
        ):
            self.assertIn(classification, continuation)
        self.assertIn("Completion: COMPLETE", continuation)
        self.assertIn("Status: ready", continuation)
        self.assertIn("Corrective routing is the Adaptive default", continuation)
        self.assertIn("no re-entry", continuation)
        self.assertIn("Verification Verdict: VERIFIED", continuation)
        self.assertIn("Ticket Progression: COMPLETED", continuation)
        self.assertIn("Ticket status after verification: done", continuation)

    def test_delivery_uses_invocation_local_evidence_economy_without_state_machine(self) -> None:
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Invocation-local evidence economy", continuation)
        self.assertIn("stop confidence-only duplicate evidence collection", continuation)
        self.assertIn("Do not create evidence budgets, counters, modality quotas", continuation)
        self.assertIn("Progress guard without retry machinery", continuation)
        self.assertIn("Do not add a numeric retry policy", continuation)

    def test_success_continuation_reassesses_outcome_from_actual_state(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        mandate = (ADAPTIVE / "references" / "01-mandate-contract.md").read_text(
            encoding="utf-8"
        )
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )
        template = (ADAPTIVE / "templates" / "ADAPTIVE-PLANNING-MANDATE.template.md").read_text(
            encoding="utf-8"
        )

        for value in ("CURRENT_INCREMENT", "BOUNDED_OUTCOME", "MANDATE_OUTCOME"):
            self.assertIn(value, mandate)
            self.assertIn(value, template)

        self.assertIn("default when the user did not explicitly authorize", mandate)
        self.assertIn("Post-delivery completion assessment and success re-entry", skill)
        self.assertIn("RUN_CONTRACT_SATISFIED", skill)
        self.assertIn("NEXT_INCREMENT_REQUIRED", skill)
        self.assertIn("USER_DECISION_REQUIRED", skill)
        self.assertIn("EVIDENCE_REQUIRED", skill)
        self.assertIn("fresh actual product state", continuation)
        self.assertIn("never consumes a pre-authored Work Package/Increment list as a queue", continuation)
        self.assertIn("not a continuation through the Ready Ticket STOP", routing)

    def test_success_continuation_does_not_turn_horizon_into_queue(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        mandate = (ADAPTIVE / "references" / "01-mandate-contract.md").read_text(
            encoding="utf-8"
        )
        terminal = (ADAPTIVE / "references" / "07-terminal-report.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("do not consume the existing Work Package list", skill)
        self.assertIn("never means consuming a pre-authored WP list", mandate)
        self.assertIn("not a completion blocker", terminal)
        self.assertIn("Completion requires fresh actual outcome evidence", terminal)

    def test_increment_reshaping_and_delivered_history_contract(self) -> None:
        reshape = (ADAPTIVE / "references" / "04-increment-reshaping.md").read_text(
            encoding="utf-8"
        )
        for operation in ("split", "merge", "reorder", "replace", "defer", "drop"):
            self.assertIn(operation, reshape)
        self.assertIn("Status: done", reshape)
        self.assertIn("Do not rewrite delivered history", reshape)
        self.assertIn("SHAPE-NNN", reshape)
        self.assertIn("INC-NNN", reshape)

    def test_verification_triage_is_authority_based(self) -> None:
        triage = (ADAPTIVE / "references" / "06-verification-triage.md").read_text(
            encoding="utf-8"
        )
        for classification in (
            "IMPLEMENTATION_DEFECT",
            "VERIFICATION_MECHANISM_DEFECT",
            "CONTRACT_OVERREACH",
            "CURRENT_INCREMENT_MISMATCH",
            "INCONCLUSIVE",
        ):
            self.assertIn(classification, triage)

        self.assertIn('Does the disputed requirement have current product authority', triage)
        self.assertIn("A hard or expensive requirement is **not** overreach", triage)
        self.assertIn("No retroactive PASS", triage)

    def test_companion_artifacts_do_not_replace_canonical_artifacts(self) -> None:
        artifact = (ADAPTIVE / "references" / "05-artifact-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("same canonical IIS artifacts", artifact)
        self.assertIn("ADAPTIVE-PLANNING-MANDATE.md", artifact)
        self.assertIn("ADAPTIVE-PLANNING-TRACE.md", artifact)
        self.assertIn("Do not add persistent decision IDs", artifact)
        self.assertIn("never add a fake direct-user approval quote", artifact)

    def test_live_installed_skill_matches_canonical_source(self) -> None:
        self.assertTrue(INSTALLED.is_dir(), INSTALLED)

        canonical_files = sorted(
            p.relative_to(ADAPTIVE)
            for p in ADAPTIVE.rglob("*")
            if p.is_file()
        )
        installed_files = sorted(
            p.relative_to(INSTALLED)
            for p in INSTALLED.rglob("*")
            if p.is_file()
        )
        self.assertEqual(canonical_files, installed_files)

        for relative in canonical_files:
            self.assertEqual(
                (ADAPTIVE / relative).read_bytes(),
                (INSTALLED / relative).read_bytes(),
                relative,
            )

    def test_sync_script_is_scoped_only_to_adaptive_skill(self) -> None:
        sync = (ROOT / "scripts" / "sync_installed_adaptive.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('ROOT / "iis-adaptive-planning"', sync)
        self.assertIn('/ "skills" / "iis-adaptive-planning"', sync)
        self.assertNotIn('ROOT / "iis-workflow"', sync)
        self.assertNotIn('/ "skills" / "iis-workflow"', sync)


if __name__ == "__main__":
    unittest.main()
