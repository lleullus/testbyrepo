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

    def test_no_fixed_decomposition_early_navigation_and_boundary_scoped_unavailability(self) -> None:
        for phrase in ("AC-per-Runner", "flow-per-Runner", "outcome-per-Runner", "defect-per-Runner", "file-per-Runner"):
            self.assertIn(phrase, NORMALIZED)
        for phrase in (
            "required verification property, canonical observation surface, and semantic closure condition",
            "Investigate as deeply as materially necessary",
            "Do not expand into a new adjacent verification question",
            "report it as an adjacent observation for Lead routing without pursuing it",
            "no materially necessary unresolved path remains inside that assignment",
            "Failure of the assigned endpoint, representation, transport, tool, or readback establishes only that exact failed boundary",
            "never label the dependency or service as wholly unavailable from that observation alone",
            "another materially relevant contract-admitted representation/readback",
            "alternate may diagnose dependency reachability or candidate integration work",
            "does not satisfy an exact authored endpoint, representation, or readback obligation unless the approved contract permits that equivalence",
            "Otherwise report the exact failed boundary so the Lead can decide whether another bounded Runner observation is warranted",
            "report that observation to the calling Lead immediately",
            "Do not wait for unrelated Runner assignments or the Lead's final aggregate merely to batch findings",
            "navigation only",
        ):
            self.assertIn(phrase, NORMALIZED)

    def test_disposable_target_report_is_raw_and_attributable(self) -> None:
        for phrase in (
            "Before disposing or cleaning up a disposable target",
            "authoritative raw readback needed to attribute the assigned observation",
            "exact target or representation",
            "materially relevant non-secret identifiers or terminal fields",
            "cleanup state",
            "not an evidence cache, archive, or durable record",
            "narration about what the target previously showed cannot substitute for the missing raw observation",
        ):
            self.assertIn(phrase, NORMALIZED)

    def test_freshness_safety_and_no_control_plane(self) -> None:
        for phrase in (
            "cycle unusable for progression",
            "all overlapped Runner invocations must return or be host-confirmed stopped",
            "Goal Verification always uses new fresh Runner invocation(s)",
            "Do not solve effect risk by pretending verification was performed",
            "Ordinary read-only observation does not require a blocking parent/caller approval checkpoint",
            "do not wait for a reply before continuing other still-safe work already inside the same bounded assignment",
            "There is no generic IIS staging-to-parent-canonical promotion stage",
        ):
            self.assertIn(phrase, NORMALIZED)
        for phrase in ("Runner registry", "scheduler", "queue", "ledger", "persistent roster", "evidence cache", "controller"):
            self.assertIn(phrase, NORMALIZED)

if __name__ == "__main__":
    unittest.main()
