from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "iis-adaptive-planning"
INTAKE = ADAPTIVE / "references" / "10-repository-evidence-intake.md"


class AdaptiveRepositoryEvidenceIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        self.intake = INTAKE.read_text(encoding="utf-8")
        self.run_contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )

    def test_intake_is_optional_and_requires_one_exact_artifact(self) -> None:
        self.assertIn("one exact repository-investigation artifact", self.skill)
        self.assertIn("one exact repository-investigation artifact path", self.intake)
        self.assertIn("Do not search `docs/investigation/**`", self.intake)
        self.assertIn("When no exact artifact is supplied, Adaptive behavior is unchanged", self.skill)
        self.assertIn("require exact `VALID`", self.intake)
        self.assertIn("exact `Project-Root` to match", self.intake)

    def test_intake_revalidates_load_bearing_evidence_not_whole_head(self) -> None:
        for token in (
            "CURRENT",
            "PARTIALLY_STALE",
            "STALE",
            "ANCHOR_LOCAL",
            "SEARCH_UNIVERSE",
            "RUNTIME_STATE",
            "EXTERNAL_VERSION",
            "Do not declare the whole artifact stale merely because Git HEAD changed",
        ):
            self.assertIn(token, self.intake)
        self.assertIn("Re-establish currentness at the load-bearing evidence boundary", self.intake)

    def test_investigation_is_not_promoted_to_planning_or_readback_authority(self) -> None:
        for token in (
            "does not authorize or decide",
            "Planning Boundary",
            "Selected Increment",
            "Run Completion Boundary",
            "planning-relevance hints into IIS product authority",
            "artifact itself is not a new Source Authority",
            "must not become the Run Contract's product `Authoritative Readback`",
        ):
            self.assertIn(token, self.intake)
        self.assertIn("artifact itself as a product authoritative readback", self.skill)

    def test_scope_uses_current_complete_evidence_without_repeating_broad_research(self) -> None:
        self.assertIn("A current `COMPLETE` investigation", self.intake)
        self.assertIn("directly reopens every investigation anchor", self.intake)
        self.assertIn("Do not repeat a broad repository investigation solely for confidence", self.intake)
        self.assertIn("A `PARTIAL` investigation may contribute current individual facts", self.intake)

    def test_intake_adds_no_run_contract_field_or_baseline_gate(self) -> None:
        self.assertNotIn("Repository Investigation:", self.run_contract)
        self.assertIn("Do not create:", self.intake)
        self.assertIn("a new Run Contract field for investigation status", self.intake)
        self.assertIn("a mandatory Baseline IIS investigation gate", self.intake)
        self.assertIn("automatic investigation invocation from Adaptive", self.intake)

        for path in (
            ROOT / "iis-workflow" / "SKILL.md",
            ROOT / "scope-shaper" / "SKILL.md",
            ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md",
            ROOT / "matt" / "skills" / "to-spec" / "SKILL.md",
            ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md",
        ):
            self.assertNotIn("repository-investigation", path.read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
