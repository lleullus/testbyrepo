from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "product-thesis" / "tools" / "product_meaning_binding.py"
spec = importlib.util.spec_from_file_location("product_meaning_binding_tests", MODULE_PATH)
binding = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = binding
assert spec.loader is not None
spec.loader.exec_module(binding)


ZERO_FINGERPRINT = "sha256:" + "0" * 64


def binding_document(
    *,
    core_utility: str = "User obtains the durable result.",
    completion_loop: str = "intent -> durable state -> authoritative result",
    required: str = "- durable append-only event log",
    invariants: str = "- authoritative readback reflects the original record",
    success: str = "User can retrieve the persisted original record after restart.",
) -> str:
    text = f"""## Product Meaning Binding

Schema: iis-product-meaning/v1
Fingerprint: {ZERO_FINGERPRINT}

Core Utility:
{core_utility}

Core Completion Loop:
{completion_loop}

Required Outcomes / Means:
{required}

Truth / Causal Invariants:
{invariants}

Success Observation:
{success}
"""
    return binding.stamp_fingerprint(text)


class ProductMeaningBindingTests(unittest.TestCase):
    def test_valid_binding_stamps_and_parses(self) -> None:
        text = binding_document()
        parsed = binding.parse_binding(text)
        self.assertEqual(parsed.schema, "iis-product-meaning/v1")
        self.assertEqual(parsed.fingerprint, parsed.computed_fingerprint())
        self.assertEqual(parsed.required_outcomes_means, ("durable append-only event log",))

    def test_fingerprint_cli_calculates_without_accepting_placeholder_as_valid(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "artifact.md"
            stamped = binding_document()
            recorded = binding.parse_binding(stamped).fingerprint
            path.write_text(stamped.replace(recorded, ZERO_FINGERPRINT), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = binding.main(["fingerprint", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(output.getvalue().strip(), recorded)
            with self.assertRaises(binding.ProductMeaningBindingError):
                binding.parse_binding(path.read_text(encoding="utf-8"))

    def test_formatting_only_newline_and_trailing_space_differences_are_absorbed(self) -> None:
        text = binding_document()
        formatted = text.replace("User obtains the durable result.", "User obtains the durable result.   ")
        formatted = formatted.replace("\n", "\r\n")
        parsed = binding.parse_binding(formatted)
        self.assertEqual(parsed.fingerprint, binding.parse_binding(text).fingerprint)

    def test_none_is_the_only_empty_collection_representation(self) -> None:
        text = binding_document(required="None", invariants="None")
        parsed = binding.parse_binding(text)
        self.assertEqual(parsed.required_outcomes_means, ())
        self.assertEqual(parsed.truth_causal_invariants, ())

        invalid = text.replace("Required Outcomes / Means:\nNone", "Required Outcomes / Means:\n")
        with self.assertRaises(binding.ProductMeaningBindingError):
            binding.parse_binding(invalid, verify_fingerprint=False)

    def test_stale_fingerprint_fails(self) -> None:
        text = binding_document().replace(
            "User obtains the durable result.",
            "User obtains a different durable result.",
        )
        with self.assertRaisesRegex(binding.ProductMeaningBindingError, "stale"):
            binding.parse_binding(text)

    def test_semantic_or_internal_text_change_is_not_normalized_away(self) -> None:
        source = binding_document()
        target = binding_document(core_utility="User receives the durable result.")
        with self.assertRaisesRegex(binding.ProductMeaningBindingError, "Core Utility"):
            binding.compare_binding_texts(source, target)

    def test_list_order_is_preserved(self) -> None:
        source = binding_document(required="- first\n- second")
        target = binding_document(required="- second\n- first")
        with self.assertRaisesRegex(binding.ProductMeaningBindingError, "Required Outcomes / Means"):
            binding.compare_binding_texts(source, target)

    def test_duplicate_binding_section_fails(self) -> None:
        text = binding_document()
        with self.assertRaisesRegex(binding.ProductMeaningBindingError, "exactly one section"):
            binding.parse_binding(text + "\n" + text)

    def _make_project(self, *, spec_binding: str | None = None, direct: bool = False) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name).resolve()
        scope_root = root / "docs" / "planning" / "scope-shaping" / "example"
        revisions = scope_root / "revisions"
        increments = scope_root / "increments"
        revisions.mkdir(parents=True)
        increments.mkdir(parents=True)

        source_binding = binding_document()
        revision = revisions / "SHAPE-001.md"
        revision.write_text(
            f"""# Scope
Status: confirmed
Project-Root: {root}
Work-Slug: example
Scope-Revision: SHAPE-001

{source_binding}
""",
            encoding="utf-8",
        )
        increment = increments / "INC-001.md"
        increment.write_text(
            f"""# Increment
Status: ready-for-matt
Project-Root: {root}
Increment: INC-001
Source-Scope-Revision: ../revisions/SHAPE-001.md

## Target Product State
Only durable persistence for this Increment.
""",
            encoding="utf-8",
        )

        spec_path = root / "docs" / "planning" / "work" / "example-work" / "SPEC.md"
        spec_path.parent.mkdir(parents=True)
        source_increment = "None" if direct else "docs/planning/scope-shaping/example/increments/INC-001.md"
        spec_path.write_text(
            f"""# Spec
Status: draft
Owner: planner
Source-Increment: {source_increment}

{spec_binding or source_binding}

## Problem
Example

## Requirements
- Example

## Verification Expectations
- Example
""",
            encoding="utf-8",
        )
        return td, spec_path, revision

    def test_direct_spec_requires_only_internal_binding_consistency(self) -> None:
        td, spec_path, _ = self._make_project(direct=True)
        self.addCleanup(td.cleanup)
        result = binding.validate_spec_binding(spec_path)
        self.assertEqual(result.mode, "direct")
        self.assertIsNone(result.source_revision)

    def test_scope_spec_resolves_increment_then_exact_immutable_revision(self) -> None:
        td, spec_path, revision = self._make_project()
        self.addCleanup(td.cleanup)
        result = binding.validate_spec_binding(spec_path)
        self.assertEqual(result.mode, "scope")
        self.assertEqual(result.source_revision, revision)

    def test_scope_spec_binding_drift_reports_field(self) -> None:
        changed = binding_document(success="A different observable success condition.")
        td, spec_path, _ = self._make_project(spec_binding=changed)
        self.addCleanup(td.cleanup)
        with self.assertRaisesRegex(binding.ProductMeaningBindingError, "Success Observation"):
            binding.validate_spec_binding(spec_path)

    def test_wrong_source_scope_revision_is_rejected(self) -> None:
        td, spec_path, _ = self._make_project()
        self.addCleanup(td.cleanup)
        increment = Path(td.name).resolve() / "docs/planning/scope-shaping/example/increments/INC-001.md"
        increment.write_text(
            increment.read_text(encoding="utf-8").replace(
                "Source-Scope-Revision: ../revisions/SHAPE-001.md",
                "Source-Scope-Revision: ../revisions/SHAPE-999.md",
            ),
            encoding="utf-8",
        )
        with self.assertRaises(binding.ProductMeaningBindingError):
            binding.validate_spec_binding(spec_path)

    def test_binding_equality_does_not_claim_requirements_semantic_fidelity(self) -> None:
        td, spec_path, _ = self._make_project()
        self.addCleanup(td.cleanup)
        text = spec_path.read_text(encoding="utf-8").replace(
            "## Requirements\n- Example",
            "## Requirements\n- An append-only log may be considered later.",
        )
        spec_path.write_text(text, encoding="utf-8")
        result = binding.validate_spec_binding(spec_path)
        self.assertEqual(result.mode, "scope")

    def test_product_level_binding_does_not_expand_increment_delivery_scope(self) -> None:
        td, spec_path, _ = self._make_project()
        self.addCleanup(td.cleanup)
        increment = Path(td.name).resolve() / "docs/planning/scope-shaping/example/increments/INC-001.md"
        self.assertIn("Only durable persistence for this Increment", increment.read_text(encoding="utf-8"))
        result = binding.validate_spec_binding(spec_path)
        self.assertEqual(result.mode, "scope")


if __name__ == "__main__":
    unittest.main()
