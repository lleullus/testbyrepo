from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "implementation_verification.py"
SPEC = importlib.util.spec_from_file_location("implementation_verification", MODULE)
assert SPEC and SPEC.loader
interface = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = interface
SPEC.loader.exec_module(interface)


class FakeBackend:
    def __init__(self) -> None:
        self.implementation_result = None
        self.verification_result = None
        self.inspection = None
        self.calls = []

    def implement(self, work, worker):
        self.calls.append(("implement", work, worker))
        return self.implementation_result

    def verify(self, candidate):
        self.calls.append(("verify", candidate))
        return self.verification_result

    def inspect(self, work):
        self.calls.append(("inspect", work))
        return self.inspection


class InterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.ticket = root / "TICKET.md"
        self.ticket.write_text("# Ticket\nStatus: ready\n", encoding="utf-8")
        self.work = self.ticket.resolve()
        self.worker = object()
        self.candidate = interface.Candidate(
            work=self.work,
            planning={"ticket": self.work},
            acceptance_criteria=("AC-1", "AC-2"),
            source="source-1",
            implementation_changes=("app.py",),
            preserved_changes=("notes.txt",),
        )
        self.backend = FakeBackend()
        self.module = interface.ImplementationVerificationModule(self.backend)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_implement_exposes_candidate_without_a_final_verdict(self) -> None:
        self.backend.implementation_result = self.candidate

        result = self.module.implement(self.ticket, self.worker)

        self.assertIs(self.candidate, result)
        self.assertTrue(result.independent_verification_pending)
        self.assertFalse(hasattr(result, "verification_status"))
        self.assertEqual([("implement", self.work, self.worker)], self.backend.calls)

    def test_implement_can_stop_without_manufacturing_a_candidate(self) -> None:
        stopped = interface.ImplementationStopped(
            work=self.work,
            reason="implementation remains incomplete",
            current_source="source-unchanged",
        )
        self.backend.implementation_result = stopped

        result = self.module.implement(self.ticket, self.worker)

        self.assertIs(stopped, result)
        self.assertNotIsInstance(result, interface.Candidate)

    def test_verify_derives_status_and_preserves_the_exact_candidate(self) -> None:
        self.backend.verification_result = interface.VerificationResult(
            self.candidate,
            (
                interface.CriterionResult(
                    "AC-1", interface.CriterionOutcome.SATISFIED, ("evidence-1",)
                ),
                interface.CriterionResult(
                    "AC-2", interface.CriterionOutcome.UNDETERMINED
                ),
            ),
        )

        result = self.module.verify(self.candidate)

        self.assertIs(self.candidate, result.candidate)
        self.assertEqual(interface.VerificationStatus.UNDETERMINED, result.status)
        self.assertEqual(("AC-1", "AC-2"), tuple(item.criterion for item in result.criterion_results))
        self.assertEqual([("verify", self.candidate)], self.backend.calls)

        self.backend.verification_result = interface.VerificationResult(
            self.candidate,
            (
                interface.CriterionResult(
                    "AC-1", interface.CriterionOutcome.SATISFIED, ("evidence-1",)
                ),
                interface.CriterionResult(
                    "AC-2", interface.CriterionOutcome.NOT_SATISFIED, ("evidence-2",)
                ),
            ),
        )
        failed = self.module.verify(self.candidate)
        self.assertEqual(interface.VerificationStatus.NOT_SATISFIED, failed.status)

    def test_verify_rejects_missing_or_reordered_acceptance_criteria(self) -> None:
        with self.assertRaisesRegex(ValueError, "every exact acceptance criterion once"):
            self.backend.verification_result = interface.VerificationResult(
                self.candidate,
                (
                    interface.CriterionResult(
                        "AC-2", interface.CriterionOutcome.SATISFIED, ("evidence-2",)
                    ),
                ),
            )

        self.assertEqual([], self.backend.calls)

    def test_inspect_returns_historical_result_with_currentness_and_candidate_recovery(self) -> None:
        verified = interface.VerificationResult(
            self.candidate,
            (
                interface.CriterionResult(
                    "AC-1", interface.CriterionOutcome.SATISFIED, ("evidence-1",)
                ),
                interface.CriterionResult(
                    "AC-2", interface.CriterionOutcome.SATISFIED, ("evidence-2",)
                ),
            ),
        )
        self.backend.inspection = interface.Inspection(
            result=verified,
            currentness=interface.Currentness.NOT_CURRENT,
        )

        inspection = self.module.inspect(self.ticket)

        self.assertIs(verified, inspection.result)
        self.assertIs(self.candidate, inspection.result.candidate)
        self.assertEqual(interface.Currentness.NOT_CURRENT, inspection.currentness)
        self.assertEqual([("inspect", self.work)], self.backend.calls)


if __name__ == "__main__":
    unittest.main()
