from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ScopeToMattHandoffTests(unittest.TestCase):
    def test_only_selected_increment_is_scope_handoff(self) -> None:
        matt = " ".join((ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8").split())
        shaper = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        for required in (
            "scope-shaper/tools/validate_increment.py",
            "increments/INC-NNN.md",
            "Status: ready-for-matt",
            "Suggested-Work-Slug",
            "exact revision/Increment contract content",
            "Source-Scope-Revision",
            "current navigation only",
            "Plan only the selected Increment",
            "Work Packages are horizontal Scope records with `Status: scoped`",
            "only the source-selected `increments/INC-NNN.md` may admit Scope-shaped work",
        ):
            self.assertIn(required, matt)
        self.assertIn("Work Package files are durable decomposition records with `Status: scoped`", shaper)
        self.assertIn("They are never `ready-for-matt`", shaper)

    def test_future_horizon_cannot_leak_into_current_spec(self) -> None:
        matt = " ".join((ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8").split())
        spec = " ".join((ROOT / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Intent Horizon", matt)
        self.assertIn("Provisional Construction Horizon", matt)
        self.assertIn("are not current Spec authority", matt)
        self.assertIn("future shaping, not authority for this Spec", spec)
        self.assertIn("return to Scope Shaper rather than importing it", spec)

    def test_to_spec_revalidates_and_serializes_source_increment_trace(self) -> None:
        spec_raw = (ROOT / "matt/skills/to-spec/SKILL.md").read_text(encoding="utf-8")
        spec = " ".join(spec_raw.split())
        self.assertIn("## Source Increment Admission", spec_raw)
        self.assertIn("scope-shaper/tools/validate_increment.py", spec)
        self.assertIn("Suggested-Work-Slug` exactly equal to this Spec's work slug", spec)
        self.assertIn("Never convert a known Scope-shaped source to `None`", spec)
        self.assertIn("Source-Increment: None | <project-relative", spec_raw)
        self.assertIn("traceability only", spec)

    def test_direct_ask_matt_has_defensive_increment_admission(self) -> None:
        matt = " ".join((ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("next-increment-ready", matt)
        self.assertIn("multiple product maturity stages", matt)
        self.assertIn("product-capability ordering", matt)
        self.assertIn("ASK MATT: SCOPE SHAPING REQUIRED", matt)
        self.assertIn("before any Grill, Behavior, or UI work", matt)

    def test_scope_confirmation_requires_complete_artifact_chain(self) -> None:
        shaper = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        for required in (
            "complete artifact chain exists and validates",
            "write the new immutable `revisions/SHAPE-NNN.md`",
            "new selected `increments/INC-NNN.md`",
            "before replacing current navigation",
            "run both canonical Scope and selected-Increment validators",
        ):
            self.assertIn(required, shaper)

    def test_scope_selection_is_smallest_durable_product_state_not_smallest_task(self) -> None:
        shaper = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        rules = " ".join((ROOT / "scope-shaper/references/initiative-decomposition-rules.md").read_text(encoding="utf-8").split())
        for required in (
            "Observable Completeness",
            "Durable Foundation",
            "Product-Dependency Closure",
            "Future-Policy Deferral",
            "Smallest Durable Choice",
            "Atomic Exception",
            "Do not generate technical preparation candidates",
            "prior passes remain only as `Status: superseded` records",
        ):
            self.assertIn(required, shaper)
        self.assertIn("This is not “choose the smallest task.”", rules)
        self.assertIn("rather than absorbing a sibling Work Package into the Increment", rules)

    def test_legacy_ready_work_packages_require_semantic_scope_migration(self) -> None:
        shaper = " ".join((ROOT / "scope-shaper/SKILL.md").read_text(encoding="utf-8").split())
        matt = " ".join((ROOT / "matt/skills/ask-matt/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Legacy Scope Artifact Compatibility", shaper)
        self.assertIn("legacy planning context", shaper)
        self.assertIn("Do not restore direct legacy Work Package admission", shaper)
        self.assertIn("preserve the legacy source byte-for-byte", shaper)
        self.assertIn("preserve every referenced legacy Work Package byte-for-byte", shaper)
        self.assertIn("block rather than overwrite history", shaper)
        self.assertIn("semantic migration, not a mechanical file-format conversion", shaper)
        self.assertIn("No converter may automatically turn every legacy ready Work Package into an Increment", shaper)
        self.assertIn("return it to Scope Shaper's `Legacy Scope Artifact Compatibility` flow", matt)


if __name__ == "__main__":
    unittest.main()
