from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scope-shaper" / "tools" / "validate_scope_result.py"
spec = importlib.util.spec_from_file_location("validator", MODULE_PATH)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
assert spec.loader is not None
spec.loader.exec_module(validator)

WORKSPACE_MODULE_PATH = Path(__file__).parents[1] / "planning-workspace" / "planning_workspace.py"
workspace_spec = importlib.util.spec_from_file_location("planning_workspace_for_transition", WORKSPACE_MODULE_PATH)
planning_workspace = importlib.util.module_from_spec(workspace_spec)
assert workspace_spec.loader is not None
workspace_spec.loader.exec_module(planning_workspace)


SOURCE = """# Example — Scope Shaping Result

Status: confirmed
Owner: user
Project-Root: {project_root}
Work-Slug: example
Planning-Shape: initiative

## Original Request

Example

## Investigation Assignments

- complete

## Verified Material Claims

### Claim 1

Classification: FACT
Primary Evidence: source
Counterexample Tested: alternate
Lead Finding: supported
Planning Relevance: DECOMPOSITION

Claim.

## Planning Boundary

### Outcome

Outcome.

### Includes

- Included

### Excludes

- Excluded

## Planning Constraints

- External contract

## Candidate Outcome Areas

- A
- B

## Decisions Reserved For Matt

- Product policy

## Delivery Context

- None

## Outside The Assessed Landscape

- None

## Unresolved Material Questions

None

## Work Package Proposal

### Split / Merge Decisions

#### A / B

Decision: SPLIT
Independent Acceptance Test: independent
Counterexample Tested: merge
Lead Finding: split
Supporting Material Claims: Claim 1

### Proposed Work Packages

#### WP-001: First

##### Outcome

First outcome.

##### Includes

- First include

##### Excludes

- Second scope

##### Depends On

None

##### Why This Is One Package

One acceptance.

##### Why It Is Separate

Independent.

##### Decisions Reserved For Matt

- None

#### WP-002: Second

##### Outcome

Second outcome.

##### Includes

- Second include

##### Excludes

- First scope

##### Depends On

- WP-001

##### Why This Is One Package

One acceptance.

##### Why It Is Separate

Independent.

##### Decisions Reserved For Matt

- None

### Release Cut

#### MVP

- WP-001
- WP-002

#### Next

None

#### Deferred

None

### Next Planning Units

- ./work-packages/WP-001.md
- ./work-packages/WP-002.md

## Confirmation

Confirmed By: user
Confirmed Scope: all
"""

WP = """# {package_id}: {title}

Status: ready-for-matt
Project-Root: {project_root}
Source-Scope-Result: ../SCOPE-SHAPING-RESULT.md
Work-Package: {package_id}
Suggested-Work-Slug: {work_slug}

## Authority Notice

Thin handoff.

## Package Outcome

{outcome}

## Included Product Scope

- {include}

## Excluded Sibling Scope

- {exclude}

## Dependencies

{dependencies}

## Decisions Reserved For Matt

- None

## Matt Start

Start.
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_umask = os.umask(0o022)

    def tearDown(self) -> None:
        os.umask(self.original_umask)

    def make_tree(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        td = tempfile.TemporaryDirectory()
        base = Path(td.name)
        work = base / "docs" / "planning" / "scope-shaping" / "example"
        (work / "work-packages").mkdir(parents=True)
        source = work / "SCOPE-SHAPING-RESULT.md"
        source.write_text(SOURCE.format(project_root=base), encoding="utf-8")
        (work / "work-packages" / "WP-001.md").write_text(
            WP.format(package_id="WP-001", title="First", project_root=base,
                      work_slug="first-outcome",
                      outcome="First outcome.", include="First include", exclude="Second scope",
                      dependencies="None"), encoding="utf-8")
        (work / "work-packages" / "WP-002.md").write_text(
            WP.format(package_id="WP-002", title="Second", project_root=base,
                      work_slug="second-outcome",
                      outcome="Second outcome.", include="Second include", exclude="First scope",
                      dependencies="- WP-001"), encoding="utf-8")
        return td, source

    def test_valid(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        validator.validate(source)

    def test_validated_package_slug_can_prepare_workspace(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        validator.validate(source)
        wp = source.parent / "work-packages" / "WP-001.md"
        work_slug = validator._metadata(wp.read_text(encoding="utf-8"), "Suggested-Work-Slug")
        result = planning_workspace.prepare(str(Path(td.name)), work_slug)
        self.assertEqual(result["workSlug"], work_slug)

    def test_canonical_bounded_template_instance_passes(self) -> None:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        base = Path(td.name).resolve()
        source = base / "docs" / "planning" / "scope-shaping" / "bounded" / "SCOPE-SHAPING-RESULT.md"
        source.parent.mkdir(parents=True)
        template = (
            Path(__file__).parents[1]
            / "scope-shaper"
            / "templates"
            / "SCOPE-SHAPING-RESULT.bounded.template.md"
        ).read_text(encoding="utf-8")
        rendered = template.replace("<absolute project root>", str(base)).replace(
            "<lowercase-kebab-slug>", "bounded"
        )
        rendered = re.sub(r"<[^>]+>", "Example", rendered)
        source.write_text(rendered, encoding="utf-8")
        validator.validate(source)

    def test_canonical_initiative_template_and_wp_instance_pass(self) -> None:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        base = Path(td.name).resolve()
        work = base / "docs" / "planning" / "scope-shaping" / "initiative"
        package_root = work / "work-packages"
        package_root.mkdir(parents=True)
        templates = Path(__file__).parents[1] / "scope-shaper" / "templates"
        source_template = (templates / "SCOPE-SHAPING-RESULT.initiative.template.md").read_text(
            encoding="utf-8"
        )
        package_template = (templates / "WORK-PACKAGE.template.md").read_text(encoding="utf-8")
        source_text = source_template.replace("<absolute project root>", str(base)).replace(
            "<slug>", "initiative"
        )
        source_text = re.sub(r"<[^>]+>", "Example", source_text)
        package_text = package_template.replace("<absolute project root>", str(base)).replace(
            "<slug>", "example-outcome"
        )
        package_text = re.sub(r"<[^>]+>", "Example", package_text)
        source = work / "SCOPE-SHAPING-RESULT.md"
        source.write_text(source_text, encoding="utf-8")
        (package_root / "WP-001.md").write_text(package_text, encoding="utf-8")
        validator.validate(source)

    def test_list_section_rejects_mixed_prose(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Planning Constraints\n\n- External contract",
            "## Planning Constraints\n\nprose\n- External contract",
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_dependency_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace("- WP-001\n\n##### Why This Is One Package", "- WP-999\n\n##### Why This Is One Package")
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_cycle_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace("##### Depends On\n\nNone\n\n##### Why This Is One Package", "##### Depends On\n\n- WP-002\n\n##### Why This Is One Package", 1)
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_mvp_closure_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace("#### MVP\n\n- WP-001\n- WP-002\n\n#### Next\n\nNone", "#### MVP\n\n- WP-002\n\n#### Next\n\n- WP-001")
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_boundary_drift_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        wp = source.parent / "work-packages" / "WP-001.md"
        wp.write_text(wp.read_text(encoding="utf-8").replace("First include", "Changed include"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_package_file_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        (source.parent / "work-packages" / "WP-002.md").unlink()
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_confirmation_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").split("\n## Confirmation", 1)[0]
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_duplicate_required_heading_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Candidate Outcome Areas\n\n- A\n- B",
            "## Candidate Outcome Areas\n\n- A\n- B\n\n## Candidate Outcome Areas\n\n- C",
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_planning_constraints_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Planning Constraints\n\n- External contract\n\n", ""
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_missing_reserved_decisions_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Decisions Reserved For Matt\n\n- Product policy\n\n", "", 1
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_source_outside_project_planning_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        outside = Path(td.name) / "outside" / "SCOPE-SHAPING-RESULT.md"
        outside.parent.mkdir()
        outside.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(outside)

    def test_empty_mvp_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "#### MVP\n\n- WP-001\n- WP-002\n\n#### Next\n\nNone",
            "#### MVP\n\nNone\n\n#### Next\n\n- WP-001\n- WP-002",
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_duplicate_release_cut_entry_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "#### MVP\n\n- WP-001\n- WP-002",
            "#### MVP\n\n- WP-001\n- WP-001\n- WP-002",
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_duplicate_next_planning_unit_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "- ./work-packages/WP-001.md\n- ./work-packages/WP-002.md",
            "- ./work-packages/WP-001.md\n- ./work-packages/WP-001.md\n- ./work-packages/WP-002.md",
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_reserved_decision_drift_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        wp = source.parent / "work-packages" / "WP-001.md"
        wp.write_text(
            wp.read_text(encoding="utf-8").replace(
                "## Decisions Reserved For Matt\n\n- None",
                "## Decisions Reserved For Matt\n\n- Different decision",
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_duplicate_work_slug_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        wp2 = source.parent / "work-packages" / "WP-002.md"
        wp2.write_text(
            wp2.read_text(encoding="utf-8").replace(
                "Suggested-Work-Slug: second-outcome", "Suggested-Work-Slug: first-outcome"
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_bounded_result_is_valid_without_packages(self) -> None:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        base = Path(td.name)
        source = base / "docs" / "planning" / "scope-shaping" / "bounded" / "SCOPE-SHAPING-RESULT.md"
        source.parent.mkdir(parents=True)
        source.write_text("""# Bounded

Status: confirmed
Owner: user
Project-Root: {root}
Work-Slug: bounded
Planning-Shape: bounded

## Verified Material Claims

### Claim 1

Confirmed fact.

## Planning Boundary

### Outcome

Bounded outcome.

### Includes

- Included scope

### Excludes

None

## Planning Constraints

None

## Candidate Outcome Areas

None

## Decisions Reserved For Matt

None

## Delivery Context

None

## Unresolved Material Questions

None

## Confirmation

Confirmed By: user
Confirmed Scope: bounded scope
""".format(root=base), encoding="utf-8")
        validator.validate(source)

    def test_bounded_requires_planning_boundary(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8")
        start = text.index("## Planning Boundary")
        end = text.index("## Planning Constraints")
        source.write_text(text[:start] + text[end:], encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_requires_candidate_outcome_areas(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Candidate Outcome Areas\n\n- A\n- B\n\n", ""
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_requires_delivery_context(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "## Delivery Context\n\n- None\n\n", ""
        )
        source.write_text(text, encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_source_work_slug_must_be_lowercase_kebab(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        source.write_text(
            source.read_text(encoding="utf-8").replace("Work-Slug: example", "Work-Slug: WP-001"),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_suggested_work_slug_must_be_lowercase_kebab(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        wp = source.parent / "work-packages" / "WP-001.md"
        wp.write_text(
            wp.read_text(encoding="utf-8").replace("first-outcome", "WP-001"),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_source_path_must_match_work_slug(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        source.write_text(
            source.read_text(encoding="utf-8").replace("Work-Slug: example", "Work-Slug: other"),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_source_filename_must_be_exact(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        renamed = source.with_name("RENAMED-RESULT.md")
        source.rename(renamed)
        with self.assertRaises(validator.ValidationError):
            validator.validate(renamed)

    def test_symlinked_docs_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            elsewhere = base / "elsewhere"
            work = elsewhere / "planning" / "scope-shaping" / "example"
            work.mkdir(parents=True)
            (base / "docs").symlink_to(elsewhere, target_is_directory=True)
            source = work / "SCOPE-SHAPING-RESULT.md"
            source.write_text(SOURCE.format(project_root=base), encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate(source)

    def test_symlinked_planning_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            docs = base / "docs"
            elsewhere = base / "elsewhere"
            work = elsewhere / "scope-shaping" / "example"
            docs.mkdir()
            work.mkdir(parents=True)
            (docs / "planning").symlink_to(elsewhere, target_is_directory=True)
            source = work / "SCOPE-SHAPING-RESULT.md"
            source.write_text(SOURCE.format(project_root=base), encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate(source)

    def test_symlinked_work_packages_directory_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        package_root = source.parent / "work-packages"
        elsewhere = Path(td.name) / "packages"
        package_root.rename(elsewhere)
        package_root.symlink_to(elsewhere, target_is_directory=True)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_work_package_file_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        wp = source.parent / "work-packages" / "WP-001.md"
        target = Path(td.name) / "WP-001.md"
        wp.rename(target)
        wp.symlink_to(target)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_selected_wp_path_must_be_exact(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        wp = source.parent / "work-packages" / "WP-001.md"
        validator.validate_selected_work_package(wp)
        renamed = wp.with_name("selected.md")
        wp.rename(renamed)
        with self.assertRaises(validator.ValidationError):
            validator.validate_selected_work_package(renamed)

    def test_selected_deferred_work_package_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        text = source.read_text(encoding="utf-8").replace(
            "#### MVP\n\n- WP-001\n- WP-002\n\n#### Next\n\nNone\n\n#### Deferred\n\nNone",
            "#### MVP\n\n- WP-001\n\n#### Next\n\nNone\n\n#### Deferred\n\n- WP-002",
        ).replace("- ./work-packages/WP-002.md\n", "")
        source.write_text(text, encoding="utf-8")
        validator.validate(source)
        deferred = source.parent / "work-packages" / "WP-002.md"
        with self.assertRaises(validator.ValidationError):
            validator.validate_selected_work_package(deferred)

    def test_noncanonical_project_root_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        noncanonical = root / "docs" / ".."
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                f"Project-Root: {root}", f"Project-Root: {noncanonical}"
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_project_root_input_must_be_absolute_without_tilde_expansion(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        source.write_text(
            source.read_text(encoding="utf-8").replace(
                f"Project-Root: {root}", "Project-Root: ~/project"
            ),
            encoding="utf-8",
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_symlinked_source_file_fails(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
        target = source.with_name("source-target.md")
        source.rename(target)
        source.symlink_to(target)
        with self.assertRaises(validator.ValidationError):
            validator.validate(source)

    def test_scope_validator_cli_works_from_arbitrary_cwd(self) -> None:
        td, source = self.make_tree()
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


if __name__ == "__main__":
    unittest.main()
