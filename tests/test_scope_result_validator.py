from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scope-shaper" / "tools" / "validate_scope_result.py"
INCREMENT_MODULE_PATH = ROOT / "scope-shaper" / "tools" / "validate_increment.py"
spec = importlib.util.spec_from_file_location("validator", MODULE_PATH)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
assert spec.loader is not None
spec.loader.exec_module(validator)

BINDING_MODULE_PATH = ROOT / "product-thesis" / "tools" / "product_meaning_binding.py"
binding_spec = importlib.util.spec_from_file_location("product_meaning_binding_for_scope_tests", BINDING_MODULE_PATH)
product_meaning_binding = importlib.util.module_from_spec(binding_spec)
sys.modules[binding_spec.name] = product_meaning_binding
assert binding_spec.loader is not None
binding_spec.loader.exec_module(product_meaning_binding)

WORKSPACE_MODULE_PATH = ROOT / "planning-workspace" / "planning_workspace.py"
workspace_spec = importlib.util.spec_from_file_location("planning_workspace_for_transition", WORKSPACE_MODULE_PATH)
planning_workspace = importlib.util.module_from_spec(workspace_spec)
assert workspace_spec.loader is not None
workspace_spec.loader.exec_module(planning_workspace)

TEMPLATES = ROOT / "scope-shaper" / "templates"


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_umask = os.umask(0o022)

    def tearDown(self) -> None:
        os.umask(self.original_umask)

    def _render(self, name: str, replacements: dict[str, str]) -> str:
        text = (TEMPLATES / name).read_text(encoding="utf-8")
        if "## Product Meaning Binding" in text:
            base = Path(replacements["<absolute project root>"])
            thesis = base / "THESIS-001.md"
            thesis.write_text("# Product Thesis\n\nConfirmed revisions determine the approved generation input.\n", encoding="utf-8")
            text = text.replace("<exact canonical absolute saved Thesis path>", str(thesis))
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = text.replace("Lead Disposition: SELECT | REJECT", "Lead Disposition: SELECT")
        text = re.sub(r"<[^>]+>", "Example", text)
        if "## Product Meaning Binding" in text:
            text = product_meaning_binding.stamp_fingerprint(text)
        return text

    def _write_current_scope(self, source: Path, text: str) -> Path:
        source.write_text(text, encoding="utf-8")
        revision = validator._metadata(text, "Scope-Revision")
        revision_root = source.parent / "revisions"
        revision_root.mkdir(exist_ok=True)
        revision_path = revision_root / f"{revision}.md"
        revision_path.write_text(text, encoding="utf-8")
        return revision_path

    def make_bounded(self) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        td = tempfile.TemporaryDirectory()
        base = Path(td.name).resolve()
        work = base / "docs" / "planning" / "scope-shaping" / "bounded"
        increments = work / "increments"
        increments.mkdir(parents=True)
        source = work / "SCOPE-SHAPING-RESULT.md"
        source_text = self._render(
            "SCOPE-SHAPING-RESULT.bounded.template.md",
            {
                "<absolute project root>": str(base),
                "<lowercase-kebab-slug>": "bounded",
                "<increment-work-slug>": "bounded-first",
            },
        )
        self._write_current_scope(source, source_text)
        increment = increments / "INC-001.md"
        increment.write_text(
            self._render(
                "INCREMENT.template.md",
                {
                    "<absolute project root>": str(base),
                    "<increment-work-slug>": "bounded-first",
                },
            ),
            encoding="utf-8",
        )
        return td, source, increment

    def make_initiative(self) -> tuple[tempfile.TemporaryDirectory, Path, Path, Path]:
        td = tempfile.TemporaryDirectory()
        base = Path(td.name).resolve()
        work = base / "docs" / "planning" / "scope-shaping" / "initiative"
        packages = work / "work-packages"
        increments = work / "increments"
        packages.mkdir(parents=True)
        increments.mkdir(parents=True)

        source = work / "SCOPE-SHAPING-RESULT.md"
        source_text = self._render(
            "SCOPE-SHAPING-RESULT.initiative.template.md",
            {
                "<absolute project root>": str(base),
                "<slug>": "initiative",
                "<increment-work-slug>": "initiative-first",
            },
        )
        self._write_current_scope(source, source_text)

        package = packages / "WP-001.md"
        package.write_text(
            self._render("WORK-PACKAGE.template.md", {"<absolute project root>": str(base)}),
            encoding="utf-8",
        )

        increment = increments / "INC-001.md"
        increment_text = self._render(
            "INCREMENT.template.md",
            {
                "<absolute project root>": str(base),
                "<increment-work-slug>": "initiative-first",
            },
        ).replace("Work-Package: None", "Work-Package: WP-001")
        increment.write_text(increment_text, encoding="utf-8")
        return td, source, package, increment

    def test_bounded_template_and_selected_increment_are_valid(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        validator.validate(source)
        self.assertEqual(validator.validate_selected_increment(increment), source)

    def test_scope_binding_stale_fingerprint_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        thesis = product_meaning_binding.parse_binding(source.read_text(encoding="utf-8")).source
        Path(thesis).write_text("Changed product meaning after Scope confirmation.\n", encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "stale Product Meaning Binding fingerprint"):
            validator.validate(source)

    def test_legacy_scope_without_binding_remains_valid(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8")
        start = text.index("## Product Meaning Binding")
        end = text.index("## Current Product State")
        self._write_current_scope(source, text[:start] + text[end:])
        validator.validate(source)

    def test_initiative_template_work_package_and_increment_are_valid(self) -> None:
        td, source, package, increment = self.make_initiative()
        self.addCleanup(td.cleanup)
        validator.validate(source)
        self.assertEqual(validator.validate_selected_increment(increment), source)
        self.assertIn("Status: scoped", package.read_text(encoding="utf-8"))

    def test_current_scope_must_match_immutable_revision_snapshot(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                "## Intent Horizon\n\nExample",
                "## Intent Horizon\n\nChanged after confirmation",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "byte-for-byte"):
            validator.validate(source)

    def test_increment_slug_can_prepare_workspace(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        validator.validate(source)
        work_slug = validator._metadata(increment.read_text(encoding="utf-8"), "Suggested-Work-Slug")
        result = planning_workspace.prepare(str(Path(td.name).resolve()), work_slug)
        self.assertEqual(result["workSlug"], work_slug)

    def test_work_package_cannot_be_ready_for_matt(self) -> None:
        td, source, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        package.write_text(package.read_text(encoding="utf-8").replace("Status: scoped", "Status: ready-for-matt"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_work_package_is_never_a_selected_handoff(self) -> None:
        td, _, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(validator.ValidationError, "not current Ask Matt handoffs"):
            validator.validate_selected_work_package(package)

    def test_increment_contract_drift_fails(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        increment.write_text(
            increment.read_text(encoding="utf-8").replace(
                "## Target Product State\n\nExample",
                "## Target Product State\n\nDifferent target",
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_increment_work_package_drift_fails(self) -> None:
        td, source, _, increment = self.make_initiative()
        self.addCleanup(td.cleanup)
        increment.write_text(increment.read_text(encoding="utf-8").replace("Work-Package: WP-001", "Work-Package: None"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_selected_increment_cannot_reference_deferred_package(self) -> None:
        td, source, _, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "#### Foundation\n\n- WP-001\n\n#### Expansion\n\nNone\n\n#### Deferred\n\nNone",
            "#### Foundation\n\nNone\n\n#### Expansion\n\nNone\n\n#### Deferred\n\n- WP-001",
        )
        self._write_current_scope(source, text)
        with self.assertRaisesRegex(validator.ValidationError, "Deferred Work Package"):
            validator.validate(source)

    def test_selected_increment_section_must_contain_exactly_one_increment(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8")
        selected = validator._section(text, "Selected Next Increment")
        duplicate = selected.replace("### INC-001: Example", "### INC-002: Other", 1)
        self._write_current_scope(source, text.replace(selected, selected + "\n\n" + duplicate))
        with self.assertRaisesRegex(validator.ValidationError, "exactly one INC-NNN"):
            validator.validate(source)

    def test_construction_candidates_require_exactly_one_select(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8")
        candidates = validator._section(text, "Construction Candidates")
        duplicate = candidates.replace("### Candidate A", "### Candidate B", 1)
        self._write_current_scope(source, text.replace(candidates, candidates + "\n\n" + duplicate))
        with self.assertRaisesRegex(validator.ValidationError, "exactly one SELECT"):
            validator.validate(source)

    def test_construction_candidate_required_field_missing_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8")
        candidates = validator._section(text, "Construction Candidates")
        changed = candidates.replace("Authoritative Readback: Example\n", "", 1)
        self._write_current_scope(source, text.replace(candidates, changed))
        with self.assertRaisesRegex(validator.ValidationError, "Authoritative Readback"):
            validator.validate(source)

    def test_selected_candidate_reference_must_match_select(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "#### Selected Candidate\n\nCandidate A",
            "#### Selected Candidate\n\nCandidate B",
        )
        self._write_current_scope(source, text)
        with self.assertRaisesRegex(validator.ValidationError, "exactly one SELECT construction candidate"):
            validator.validate(source)

    def test_selected_candidate_observable_contract_drift_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "#### Observable Outcome\n\nActor Or Operator: Example\nTrigger Or Inspection Target: Example\nObservable Result: Example",
            "#### Observable Outcome\n\nActor Or Operator: Example\nTrigger Or Inspection Target: Example\nObservable Result: Different",
        )
        self._write_current_scope(source, text)
        with self.assertRaisesRegex(validator.ValidationError, "Observable Result drift"):
            validator.validate(source)

    def test_initiative_candidate_must_reference_proposed_work_package(self) -> None:
        td, source, _, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace("Outcome Area: WP-001", "Outcome Area: WP-999", 1)
        self._write_current_scope(source, text)
        with self.assertRaisesRegex(validator.ValidationError, "must reference one proposed Work Package"):
            validator.validate(source)

    def test_candidate_validator_is_structural_not_a_scoring_engine(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8")
        candidates = validator._section(text, "Construction Candidates")
        changed = candidates.replace("Durable Foundation: Example", "Durable Foundation: debatable product judgment").replace(
            "Reason: Example", "Reason: Lead chose this after qualitative tradeoff judgment"
        )
        self._write_current_scope(source, text.replace(candidates, changed))
        validator.validate(source)

    def test_provisional_horizon_is_required_but_not_a_ready_artifact(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Provisional Construction Horizon\n\n- Example\n\n", ""
        )
        self._write_current_scope(source, text)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_unresolved_material_question_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                "## Unresolved Material Questions\n\nNone",
                "## Unresolved Material Questions\n\nNeed evidence",
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_source_work_slug_must_be_lowercase_kebab(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        source.write_text(source.read_text(encoding="utf-8").replace("Work-Slug: bounded", "Work-Slug: BAD"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_increment_suggested_work_slug_must_be_lowercase_kebab(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        increment.write_text(increment.read_text(encoding="utf-8").replace("Suggested-Work-Slug: bounded-first", "Suggested-Work-Slug: BAD"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_increment_suggested_work_slug_must_match_confirmed_scope(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        increment.write_text(
            increment.read_text(encoding="utf-8").replace(
                "Suggested-Work-Slug: bounded-first",
                "Suggested-Work-Slug: different-valid-slug",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "Suggested-Work-Slug drift"):
            validator.validate(source)

    def test_increment_work_slug_is_unique_across_scope_increments(self) -> None:
        td, _, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        base = Path(td.name).resolve()
        work = base / "docs" / "planning" / "scope-shaping" / "other"
        (work / "increments").mkdir(parents=True)
        source = work / "SCOPE-SHAPING-RESULT.md"
        source_text = self._render(
            "SCOPE-SHAPING-RESULT.bounded.template.md",
            {
                "<absolute project root>": str(base),
                "<lowercase-kebab-slug>": "other",
                "<increment-work-slug>": "bounded-first",
            },
        )
        self._write_current_scope(source, source_text)
        increment = work / "increments" / "INC-001.md"
        increment.write_text(
            self._render(
                "INCREMENT.template.md",
                {
                    "<absolute project root>": str(base),
                    "<increment-work-slug>": "bounded-first",
                },
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "already belongs to another Scope Increment"):
            validator.validate(source)

    def test_source_path_must_match_work_slug(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        source.write_text(source.read_text(encoding="utf-8").replace("Work-Slug: bounded", "Work-Slug: other"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_selected_increment_path_must_be_exact(self) -> None:
        td, _, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        renamed = increment.with_name("selected.md")
        increment.rename(renamed)
        with self.assertRaises(validator.ValidationError):
            validator.validate_selected_increment(renamed)

    def test_future_nonselected_increment_makes_source_invalid(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        other = increment.with_name("INC-002.md")
        other.write_text(increment.read_text(encoding="utf-8").replace("Increment: INC-001", "Increment: INC-002"), encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "highest current INC-NNN ordinal"):
            validator.validate(source)

    def test_reentry_requires_prior_increment_to_be_superseded(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        original_increment = increment.read_text(encoding="utf-8")
        next_source = (
            source.read_text(encoding="utf-8")
            .replace("Scope-Revision: SHAPE-001", "Scope-Revision: SHAPE-002")
            .replace("### INC-001: Example", "### INC-002: Example")
            .replace("#### Suggested Work Slug\n\nbounded-first", "#### Suggested Work Slug\n\nbounded-second")
            .replace("./increments/INC-001.md", "./increments/INC-002.md")
        )
        self._write_current_scope(source, next_source)
        current = increment.with_name("INC-002.md")
        current.write_text(
            original_increment
            .replace("Source-Scope-Revision: ../revisions/SHAPE-001.md", "Source-Scope-Revision: ../revisions/SHAPE-002.md")
            .replace("Increment: INC-001", "Increment: INC-002")
            .replace("Suggested-Work-Slug: bounded-first", "Suggested-Work-Slug: bounded-second"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "prior Increment Status must be superseded"):
            validator.validate(source)
        increment.write_text(original_increment.replace("Status: ready-for-matt", "Status: superseded"), encoding="utf-8")
        validator.validate(source)
        self.assertEqual(validator.validate_selected_increment(current), source)

        historical_revision = source.parent / "revisions" / "SHAPE-001.md"
        historical_revision.write_text(
            historical_revision.read_text(encoding="utf-8").replace(
                "#### Target Product State\n\nExample",
                "#### Target Product State\n\nChanged historical target",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "Target Product State drift"):
            validator.validate(source)

    def test_missing_confirmation_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").split("\n## Confirmation", 1)[0]
        self._write_current_scope(source, text)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_duplicate_required_heading_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Candidate Outcome Areas\n\n- Example",
            "## Candidate Outcome Areas\n\n- Example\n\n## Candidate Outcome Areas\n\n- Duplicate",
        )
        self._write_current_scope(source, text)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_planning_constraints_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Planning Constraints\n\n- Example\n\n", ""
        )
        self._write_current_scope(source, text)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_reserved_decisions_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Decisions Reserved For Matt\n\n- Example\n\n", ""
        )
        self._write_current_scope(source, text)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_list_section_rejects_mixed_prose(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Planning Constraints\n\n- Example",
            "## Planning Constraints\n\nprose\n- Example",
        )
        self._write_current_scope(source, text)
        with self.assertRaisesRegex(validator.ValidationError, "Markdown list items"):
            validator.validate(source)

    def test_missing_work_package_dependency_fails(self) -> None:
        td, source, _, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "##### Depends On\n\nNone",
            "##### Depends On\n\n- WP-999",
            1,
        )
        self._write_current_scope(source, text)
        with self.assertRaisesRegex(validator.ValidationError, "missing dependencies"):
            validator.validate(source)

    def test_two_package_dependency_cycle_fails(self) -> None:
        td, source, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "##### Depends On\n\nNone",
            "##### Depends On\n\n- WP-002",
            1,
        )
        second = """#### WP-002: Second

##### Outcome

Example

##### Includes

- Example

##### Excludes

- Example

##### Depends On

- WP-001

##### Why This Is One Package

Example

##### Why It Is Separate

Example

##### Decisions Reserved For Matt

- Example

"""
        text = text.replace("### Outcome Horizon", second + "### Outcome Horizon")
        text = text.replace("#### Foundation\n\n- WP-001", "#### Foundation\n\n- WP-001\n- WP-002")
        self._write_current_scope(source, text)

        package.write_text(
            package.read_text(encoding="utf-8").replace("## Dependencies\n\nNone", "## Dependencies\n\n- WP-002"),
            encoding="utf-8",
        )
        package2 = package.with_name("WP-002.md")
        package2.write_text(
            self._render("WORK-PACKAGE.template.md", {"<absolute project root>": str(Path(td.name).resolve())})
            .replace("WP-001", "WP-002")
            .replace("## Dependencies\n\nNone", "## Dependencies\n\n- WP-001"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "dependency cycle"):
            validator.validate(source)

    def test_work_package_boundary_drift_fails(self) -> None:
        td, source, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        package.write_text(
            package.read_text(encoding="utf-8").replace(
                "## Included Product Scope\n\n- Example",
                "## Included Product Scope\n\n- Different scope",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "Includes drift"):
            validator.validate(source)

    def test_missing_work_package_file_fails(self) -> None:
        td, source, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        package.unlink()
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_source_outside_project_planning_tree_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        outside = Path(td.name).resolve() / "outside" / "SCOPE-SHAPING-RESULT.md"
        outside.parent.mkdir()
        outside.write_bytes(source.read_bytes())
        with self.assertRaisesRegex(validator.ValidationError, "Scope result must be exactly"):
            validator.validate(outside)

    def test_source_filename_must_be_exact(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        renamed = source.with_name("RENAMED-RESULT.md")
        source.rename(renamed)
        with self.assertRaisesRegex(validator.ValidationError, "Scope result must be exactly"):
            validator.validate(renamed)

    def test_project_root_tilde_or_relative_form_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                f"Project-Root: {Path(td.name).resolve()}",
                "Project-Root: ~/project",
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_scope_revision_file_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        (source.parent / "revisions" / "SHAPE-001.md").unlink()
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_invalid_scope_revision_ordinal_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        source.write_text(
            source.read_text(encoding="utf-8").replace("Scope-Revision: SHAPE-001", "Scope-Revision: SHAPE-000"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(validator.ValidationError, "ordinal of at least 001"):
            validator.validate(source)

    def test_symlinked_work_packages_directory_fails(self) -> None:
        td, source, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        package_root = package.parent
        elsewhere = Path(td.name).resolve() / "packages-elsewhere"
        package_root.rename(elsewhere)
        package_root.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_work_package_file_fails(self) -> None:
        td, source, package, _ = self.make_initiative()
        self.addCleanup(td.cleanup)
        target = package.with_name("WP-target.md")
        package.rename(target)
        package.symlink_to(target)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_revisions_directory_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        revision_root = source.parent / "revisions"
        elsewhere = Path(td.name).resolve() / "revisions-elsewhere"
        revision_root.rename(elsewhere)
        revision_root.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_revision_file_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        revision = source.parent / "revisions" / "SHAPE-001.md"
        target = revision.with_name("SHAPE-target.md")
        revision.rename(target)
        revision.symlink_to(target)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_source_file_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        target = source.with_name("source-target.md")
        source.rename(target)
        source.symlink_to(target)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_increment_file_fails(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        target = increment.with_name("target.md")
        increment.rename(target)
        increment.symlink_to(target)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_increments_directory_fails(self) -> None:
        td, source, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        increment_root = increment.parent
        elsewhere = Path(td.name).resolve() / "increments-elsewhere"
        increment_root.rename(elsewhere)
        increment_root.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_noncanonical_project_root_fails(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        root = Path(td.name).resolve()
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                f"Project-Root: {root}", f"Project-Root: {root / 'docs' / '..'}"
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_scope_validator_cli_works_from_arbitrary_cwd(self) -> None:
        td, source, _ = self.make_bounded()
        self.addCleanup(td.cleanup)
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(source)],
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "VALID")

    def test_increment_validator_cli_works_from_arbitrary_cwd(self) -> None:
        td, _, increment = self.make_bounded()
        self.addCleanup(td.cleanup)
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                [sys.executable, str(INCREMENT_MODULE_PATH), str(increment)],
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "VALID")


if __name__ == "__main__":
    unittest.main()
