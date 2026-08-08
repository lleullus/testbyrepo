from __future__ import annotations

import importlib.util
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
Suggested-Work-Slug: {package_id}

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
    def make_tree(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        td = tempfile.TemporaryDirectory()
        base = Path(td.name)
        work = base / "docs" / "planning" / "scope-shaping" / "example"
        (work / "work-packages").mkdir(parents=True)
        source = work / "SCOPE-SHAPING-RESULT.md"
        source.write_text(SOURCE.format(project_root=base), encoding="utf-8")
        (work / "work-packages" / "WP-001.md").write_text(
            WP.format(package_id="WP-001", title="First", project_root=base,
                      outcome="First outcome.", include="First include", exclude="Second scope",
                      dependencies="None"), encoding="utf-8")
        (work / "work-packages" / "WP-002.md").write_text(
            WP.format(package_id="WP-002", title="Second", project_root=base,
                      outcome="Second outcome.", include="Second include", exclude="First scope",
                      dependencies="- WP-001"), encoding="utf-8")
        return td, source

    def test_valid(self) -> None:
        td, source = self.make_tree()
        self.addCleanup(td.cleanup)
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
                "Suggested-Work-Slug: WP-002", "Suggested-Work-Slug: WP-001"
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

## Planning Constraints

None

## Decisions Reserved For Matt

None

## Unresolved Material Questions

None

## Confirmation

Confirmed By: user
Confirmed Scope: bounded scope
""".format(root=base), encoding="utf-8")
        validator.validate(source)


if __name__ == "__main__":
    unittest.main()
