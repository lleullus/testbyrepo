from __future__ import annotations
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
NORMALIZED = " ".join(SKILL.split())

class VerificationRunnerContractTests(unittest.TestCase):
    def test_authority_and_role_binding(self) -> None:
        for phrase in (
            "calling Lead owns the authored denominator, grouping, evidence admission, verdicts, aggregate",
            "Runner reports only raw current observation",
            "explicit current-conversation user designation of a `Verification Runner` role",
            "Model identity alone is not a role",
            "separately designated that same configured model/agent for that other role",
        ):
            self.assertIn(phrase, NORMALIZED)

    def test_no_fixed_decomposition_and_early_navigation(self) -> None:
        for phrase in ("AC-per-Runner", "flow-per-Runner", "outcome-per-Runner", "defect-per-Runner", "file-per-Runner"):
            self.assertIn(phrase, NORMALIZED)
        for phrase in (
            "report that observation to the calling Lead immediately",
            "Do not wait for unrelated Runner assignments or the Lead's final aggregate merely to batch findings",
            "navigation only",
        ):
            self.assertIn(phrase, NORMALIZED)

    def test_freshness_safety_and_no_control_plane(self) -> None:
        for phrase in (
            "cycle unusable for progression",
            "all overlapped Runner invocations must return or be host-confirmed stopped",
            "Goal Verification always uses new fresh Runner invocation(s)",
            "Do not solve effect risk by pretending verification was performed",
            "There is no generic IIS staging-to-parent-canonical promotion stage",
        ):
            self.assertIn(phrase, NORMALIZED)
        for phrase in ("Runner registry", "scheduler", "queue", "ledger", "persistent roster", "evidence cache", "controller"):
            self.assertIn(phrase, NORMALIZED)

if __name__ == "__main__":
    unittest.main()
