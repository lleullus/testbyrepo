from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

ACTIVE_HASHLESS = [
    ROOT / "iis_artifacts" / "refs.py",
    ROOT / "iis_artifacts" / "store.py",
    ROOT / "iis_artifacts" / "publication.py",
    ROOT / "iis_artifacts" / "admission.py",
    ROOT / "product-thesis" / "tools" / "lifecycle.py",
    ROOT / "product-thesis" / "tools" / "thesis.py",
    ROOT / "scope-shaper" / "tools" / "validate_scope.py",
    ROOT / "iis-workflow" / "tools" / "assurance.py",
    ROOT / "scripts" / "sync_installed_iis.py",
    ROOT / "observatory" / "src" / "iis_observatory" / "scanner.py",
    ROOT / "observatory" / "src" / "iis_observatory" / "snapshot.py",
    ROOT / "evaluation" / "product-thesis" / "run.py",
    ROOT / "evaluation" / "ready-verification" / "fixture_catalog.py",
    ROOT / "evaluation" / "ready-verification" / "implementation_fixtures.py",
    ROOT / "evaluation" / "ready-verification" / "corrective_reuse_fixtures.py",
    ROOT / "evaluation" / "ready-verification" / "score_assurance.py",
]


class HashlessRuntimeContractTests(unittest.TestCase):
    def test_active_producers_and_consumers_do_not_reintroduce_content_identity(self) -> None:
        forbidden = ("hashlib", "sha256", "sourceFingerprint", "source_fingerprint", "compute_source_fingerprint")
        for path in ACTIVE_HASHLESS:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=path.relative_to(ROOT).as_posix(), token=token):
                    self.assertNotIn(token, text)

    def test_scope_and_assurance_current_schemas_are_v2(self) -> None:
        scope = (ROOT / "scope-shaper" / "tools" / "validate_scope.py").read_text(encoding="utf-8")
        assurance = (ROOT / "iis-workflow" / "tools" / "assurance.py").read_text(encoding="utf-8")
        self.assertIn("iis-scope/v2", scope)
        self.assertIn("iis-assurance/v2", assurance)
        self.assertIn("iis-assurance-binding/v2", assurance)
        self.assertIn("iis-assurance-result/v2", assurance)

    def test_installer_is_protocol_five_with_allocated_release_ids(self) -> None:
        installer = (ROOT / "scripts" / "sync_installed_iis.py").read_text(encoding="utf-8")
        self.assertIn('SCHEMA = "iis-bundle/v5"', installer)
        self.assertIn('INSTALL_SCHEMA = "iis-install/v5"', installer)
        self.assertIn("PROTOCOL = 5", installer)
        self.assertIn('"rel-" + uuid.uuid4().hex', installer)


if __name__ == "__main__":
    unittest.main()
