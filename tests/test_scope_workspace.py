from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scope-shaper" / "tools" / "validate_scope.py"
SPEC = importlib.util.spec_from_file_location("validate_scope", MODULE_PATH)
assert SPEC and SPEC.loader
validate_scope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_scope)


class ScopeValidatorFilesystemTests(unittest.TestCase):
    def _fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, Path, dict]:
        temporary = tempfile.TemporaryDirectory(dir=Path.home())
        project = Path(temporary.name).resolve()
        thesis = project / "docs/planning/product-thesis/reservation-flow/THESIS-001.md"
        scope = project / "docs/planning/work/reservation-flow/SCOPE.md"
        thesis.parent.mkdir(parents=True)
        scope.parent.mkdir(parents=True)
        thesis.write_text("# Thesis\n\nCore utility.\n", encoding="utf-8")
        source = {
            "snapshot": "snap-" + "1" * 32,
            "path": "docs/planning/product-thesis/reservation-flow/THESIS-001.md",
        }
        scope.write_text(
            f"""# Reservation flow
Schema: iis-scope/v2
Project-Root: {project}
Status: ready

## Product Authority
```iis-sources
{json.dumps([source], indent=2)}
```

## Outcome
A durable reservation result.

## Acceptance
Read the canonical reservation state.

## Open Decisions
None
""",
            encoding="utf-8",
        )
        return temporary, scope, thesis, source

    def test_accepts_canonical_scope_and_fixed_source_ref(self) -> None:
        temporary, scope, _thesis, source = self._fixture()
        self.addCleanup(temporary.cleanup)
        result = validate_scope.validate(scope)
        self.assertEqual(result["schema"], "iis-scope/v2")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["scope_path"], str(scope))
        self.assertEqual(result["product_authorities"], [source])

    def test_structure_validation_does_not_recheck_live_thesis_bytes(self) -> None:
        temporary, scope, thesis, source = self._fixture()
        self.addCleanup(temporary.cleanup)
        thesis.write_text("# Thesis\n\nChanged live publication.\n", encoding="utf-8")
        result = validate_scope.validate(scope)
        self.assertEqual(result["product_authorities"], [source])

    def test_rejects_scope_outside_canonical_work_path(self) -> None:
        temporary, scope, _thesis, _source = self._fixture()
        self.addCleanup(temporary.cleanup)
        outside = scope.parents[3] / "SCOPE.md"
        outside.write_text(scope.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaisesRegex(validate_scope.ScopeValidationError, "docs/planning/work/<slug>/SCOPE.md"):
            validate_scope.validate(outside)

    def test_rejects_content_derived_or_path_only_authority_shape(self) -> None:
        temporary, scope, _thesis, _source = self._fixture()
        self.addCleanup(temporary.cleanup)
        text = scope.read_text(encoding="utf-8")
        text = text.replace(
            '"snapshot": "snap-' + "1" * 32 + '",\n    "path": "docs/planning/product-thesis/reservation-flow/THESIS-001.md"',
            '"path": "docs/planning/product-thesis/reservation-flow/THESIS-001.md"',
        )
        scope.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(validate_scope.ScopeValidationError, "source reference"):
            validate_scope.validate(scope)


if __name__ == "__main__":
    unittest.main()
