from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVESTIGATION = ROOT / "companion-skills" / "repository-investigation"


class RepositoryInvestigationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (INVESTIGATION / "SKILL.md").read_text(encoding="utf-8")
        self.workflow = (INVESTIGATION / "references" / "investigation.md").read_text(
            encoding="utf-8"
        )
        self.template = (INVESTIGATION / "templates" / "REPOSITORY-INVESTIGATION.template.md").read_text(
            encoding="utf-8"
        )
        self.openai = (INVESTIGATION / "agents" / "openai.yaml").read_text(encoding="utf-8")

    def test_skill_surface_is_bounded_and_discoverable(self) -> None:
        self.assertEqual(
            {path.name for path in INVESTIGATION.iterdir()},
            {"SKILL.md", "agents", "references", "templates", "tools"},
        )
        self.assertEqual({p.name for p in (INVESTIGATION / "agents").iterdir()}, {"openai.yaml"})
        self.assertEqual(
            {p.name for p in (INVESTIGATION / "references").iterdir()}, {"investigation.md"}
        )
        self.assertEqual(
            {p.name for p in (INVESTIGATION / "templates").iterdir()},
            {"REPOSITORY-INVESTIGATION.template.md"},
        )
        self.assertEqual(
            {p.name for p in (INVESTIGATION / "tools").iterdir()},
            {"prepare_investigation_workspace.py", "validate_investigation.py"},
        )
        self.assertIn("name: repository-investigation", self.skill)
        self.assertIn("$repository-investigation", self.openai)

    def test_live_skill_link_targets_canonical_companion(self) -> None:
        installed = Path.home() / ".codex" / "skills" / "repository-investigation"
        self.assertTrue(installed.is_symlink())
        self.assertEqual(installed.resolve(), INVESTIGATION.resolve())
        self.assertEqual(
            (installed / "SKILL.md").read_bytes(),
            (INVESTIGATION / "SKILL.md").read_bytes(),
        )

    def test_investigation_is_evidence_authority_not_iis_authority(self) -> None:
        combined = self.skill + self.workflow
        for token in (
            "repository evidence baseline",
            "does **not** own",
            "Planning Boundary",
            "Adaptive Mandate",
            "Spec or Ticket authority",
            "implementation design or mutation",
            "verification verdicts",
            "not IIS authority",
        ):
            self.assertIn(token, combined)
        self.assertIn("not IIS planning authority", self.template)

    def test_frontier_has_four_required_evidence_concerns(self) -> None:
        combined = self.skill + self.workflow
        for token in (
            "FLOW_AND_READBACK",
            "STATE_AND_AUTHORITY",
            "ALTERNATE_PATHS",
            "EVIDENCE_ALIGNMENT",
            "INVESTIGATE | COVERED_BY_OTHER_LANE | NOT_APPLICABLE",
        ):
            self.assertIn(token, combined)
        self.assertIn("deliberate counterpath challenge", self.skill)
        self.assertIn("Plausible Alternative", self.workflow)
        self.assertIn("Search Universe", self.workflow)

    def test_execution_is_direct_first_and_parallelism_is_not_a_quality_proxy(self) -> None:
        combined = self.skill + self.workflow
        self.assertIn("Top-level execution defaults to `DIRECT`", self.skill)
        self.assertIn("only when the current user explicitly selects", self.skill)
        self.assertIn("dynamic worker set", self.skill)
        self.assertIn("There is no fixed worker count", self.skill)
        self.assertIn("Worker agreement is never evidence", self.skill)
        self.assertIn("do not duplicate the same question solely to fill all slots", self.workflow)
        self.assertIn("resolves or preserves worker disagreement from primary evidence rather than voting", self.workflow)

    def test_durable_artifact_is_one_immutable_project_local_handoff(self) -> None:
        combined = self.skill + self.workflow
        self.assertIn("docs/investigation/**", self.skill)
        self.assertIn("never overwrite a prior `INV-NNN.md`", self.skill)
        self.assertIn("Do not create `LATEST.md`", self.workflow)
        self.assertIn("prepare_investigation_workspace.py", combined)
        self.assertIn("validate_investigation.py", combined)
        self.assertIn("require exact `VALID`", self.skill)
        self.assertIn("Evidence Handoff", self.template)
        self.assertIn("Load-Bearing Anchors", self.template)

    def test_completion_is_bounded_not_repo_exhaustiveness(self) -> None:
        combined = self.skill + self.workflow
        self.assertIn("COMPLETE | PARTIAL | BLOCKED", self.skill)
        self.assertIn("does not mean the repository has no defects", self.skill)
        self.assertIn("not an exhaustive-file-count threshold", self.workflow)
        self.assertIn("Decision-Critical Unknowns: None", self.workflow)
        self.assertIn("Do not inventory the whole repository", self.skill)


if __name__ == "__main__":
    unittest.main()
