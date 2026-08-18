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

    def test_current_baseline_approval_gates_still_exist(self) -> None:
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
        self.assertIn("Never infer approval", spec)
        self.assertIn("obtain the user's confirmation", tickets)

        routing = (ADAPTIVE / "references" / "03-adaptive-routing.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("standing delegated", routing)
        self.assertIn("alternate execution contract", routing)

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

    def test_planning_terminal_does_not_erase_broader_user_delivery_authority(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        terminal = (ADAPTIVE / "references" / "07-terminal-report.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("outer caller may immediately continue", skill)
        self.assertIn("IIS Adaptive Planning ownership", continuation)
        self.assertIn("user's current execution envelope", continuation)
        self.assertIn("ready-ticket-implement", continuation)
        self.assertIn("ready-ticket-verify", continuation)
        self.assertIn("without asking for another approval", terminal)
        self.assertIn("Auditor Count 0", continuation)
        self.assertIn("AC Runtime Auditor Count 0", continuation)

    def test_end_to_end_delivery_can_reenter_adaptive_for_planning_failures(self) -> None:
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CONTRACT_OVERREACH", continuation)
        self.assertIn("CURRENT_INCREMENT_MISMATCH", continuation)
        self.assertIn("re-enters IIS Adaptive Planning", continuation)
        self.assertIn("IMPLEMENTATION_DEFECT", continuation)
        self.assertIn("VERIFICATION_MECHANISM_DEFECT", continuation)
        self.assertIn("INCONCLUSIVE", continuation)
        self.assertIn("all current Tickets VERIFIED -> done", continuation)

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
        self.assertIn("Success re-entry after delivery", skill)
        self.assertIn("MANDATE_SATISFIED", skill)
        self.assertIn("NEXT_INCREMENT_REQUIRED", skill)
        self.assertIn("USER_DECISION_REQUIRED", skill)
        self.assertIn("fresh actual product state", continuation)
        self.assertIn("does not automatically admit the next previously listed WP/INC", continuation)
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
