from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scope-shaper" / "tools" / "validate_scope.py"
SPEC = importlib.util.spec_from_file_location("validate_scope", MODULE_PATH)
assert SPEC and SPEC.loader
validate_scope = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validate_scope)


class ScopeValidatorFilesystemTests(unittest.TestCase):
    def _fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, Path]:
        temporary = tempfile.TemporaryDirectory(dir=Path.home())
        project = Path(temporary.name).resolve()
        thesis = project / "docs" / "planning" / "product-thesis" / "reservation-flow" / "THESIS-001.md"
        scope = project / "docs" / "planning" / "work" / "reservation-flow" / "SCOPE.md"
        thesis.parent.mkdir(parents=True)
        scope.parent.mkdir(parents=True)
        thesis.write_text("# Thesis\n\nCore utility.\n", encoding="utf-8")
        digest = hashlib.sha256(thesis.read_bytes()).hexdigest()
        scope.write_text(
            f"""# Reservation flow
Schema: iis-scope/v1
Project-Root: {project}
Status: ready

## Product Authority
- {thesis} sha256:{digest}

## Outcome
A durable reservation result.

## Acceptance
Read the canonical reservation state.

## Open Decisions
None
""",
            encoding="utf-8",
        )
        return temporary, scope, thesis

    def test_accepts_canonical_scope_and_binds_thesis_bytes(self) -> None:
        temporary, scope, thesis = self._fixture()
        self.addCleanup(temporary.cleanup)

        result = validate_scope.validate(scope)

        self.assertEqual(result["schema"], "iis-scope/v1")
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["scope_path"], str(scope))
        self.assertEqual(result["product_authorities"], [{
            "path": str(thesis),
            "sha256": hashlib.sha256(thesis.read_bytes()).hexdigest(),
        }])

    def test_rejects_changed_thesis_bytes(self) -> None:
        temporary, scope, thesis = self._fixture()
        self.addCleanup(temporary.cleanup)
        thesis.write_text("# Thesis\n\nChanged utility.\n", encoding="utf-8")

        with self.assertRaisesRegex(validate_scope.ScopeValidationError, "authority changed"):
            validate_scope.validate(scope)

    def test_rejects_scope_outside_canonical_work_path(self) -> None:
        temporary, scope, _thesis = self._fixture()
        self.addCleanup(temporary.cleanup)
        outside = scope.parents[3] / "SCOPE.md"
        outside.write_text(scope.read_text(encoding="utf-8"), encoding="utf-8")

        with self.assertRaisesRegex(validate_scope.ScopeValidationError, "docs/planning/work/<slug>/SCOPE.md"):
            validate_scope.validate(outside)


if __name__ == "__main__":
    unittest.main()
