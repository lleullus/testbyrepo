from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "companion-skills" / "production-heuristic-probing" / "SKILL.md"
CURRENT_SOURCES = (
    ROOT / "product-thesis" / "references" / "exploration.md",
    ROOT / "evaluation" / "product-thesis" / "refinement-scenarios.md",
    ROOT / "evaluation" / "ready-verification" / "README.md",
    ROOT / "docs" / "engineering" / "ready-runtime" / "dependency-map.md",
    ROOT / "docs" / "engineering" / "ready-runtime" / "verification.md",
    ROOT / "docs" / "engineering" / "host-integration-reintroduction.md",
)


class ProductionHeuristicProbeContractTests(unittest.TestCase):
    def test_probe_result_records_actions_effects_currentness_and_settlement(self) -> None:
        text = PROBE.read_text(encoding="utf-8")
        required_fields = (
            "Independent Probe invocation:",
            "Probe actions and primary evidence:",
            "Probe effect paths:",
            "Currentness before / after:",
            "Cleanup and settlement:",
            "Scope-material limitations:",
            "Out-of-scope limitations:",
        )
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, text)

    def test_current_sources_route_to_probe_not_retired_coverage(self) -> None:
        retired_phrases = (
            "companion-skills/scope-coverage",
            "Coverage owns its later read-only search",
            "independent read-only Coverage",
            "separate read-only Coverage",
            "real verifier, Coverage, deployment",
        )
        for path in CURRENT_SOURCES:
            text = path.read_text(encoding="utf-8")
            if path == ROOT / "evaluation" / "ready-verification" / "README.md":
                text = text.split("## Historical observations (old releases only)", 1)[0]
            with self.subTest(path=path):
                self.assertIn("Production Heuristic Probe", text)
                for phrase in retired_phrases:
                    self.assertNotIn(phrase, text)

    def test_installer_requires_probe_and_retires_scope_coverage(self) -> None:
        text = (ROOT / "scripts" / "sync_installed_iis.py").read_text(encoding="utf-8")
        self.assertIn('"companion-skills/production-heuristic-probing"', text)
        self.assertIn('"companion-skills/production-heuristic-probing/SKILL.md"', text)
        self.assertIn('"companion-skills/scope-coverage"', text)


if __name__ == "__main__":
    unittest.main()
