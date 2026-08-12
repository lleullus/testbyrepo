from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
CLOSURE = (ROOT / "ARCHITECTURE-CLOSURE.md").read_text(encoding="utf-8")


class ArchitectureClosureTests(unittest.TestCase):
    def test_finite_failure_surface_has_exactly_nine_numbered_classes(self) -> None:
        headings = re.findall(r"(?m)^### (\d+)\. (.+)$", CLOSURE)
        self.assertEqual([int(number) for number, _ in headings], list(range(1, 10)))

    def test_each_failure_class_has_a_terminal_classification(self) -> None:
        headings = [line for line in CLOSURE.splitlines() if line.startswith("### ")]
        allowed = ("PROVED", "ACCEPTED TRADE-OFF", "OUT OF SUPPORTED RANGE")
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertTrue(any(token in heading for token in allowed), heading)

    def test_ticket_projection_closure_explicitly_preserves_semantic_decomposition(self) -> None:
        required = (
            "Ralph independently revalidates current Spec-to-Ticket semantic compatibility before mutation",
            "An unchanged `Status: ready` is not sufficient",
            "The validator does **not** decide semantic equivalence",
            "Exact string equality would reject valid solution-independent decomposition",
            "agent-quality/evaluation issue unless the authored contract itself permits stale mutation",
        )
        for text in required:
            self.assertIn(text, CLOSURE)

    def test_freeze_reopening_requires_all_five_admission_conditions(self) -> None:
        section = CLOSURE.split("## Core Freeze Admission", 1)[1].split("## Explicit Non-Reasons", 1)[0]
        for label in (
            "Faithful-contract counterexample",
            "Architecture-general",
            "Material failure class",
            "Invariant repair",
            "Complexity test",
        ):
            self.assertIn(label, section)
        self.assertIn("when **all** of the following are true", section)

    def test_freeze_rejects_agent_quality_and_project_specific_patch_pressure(self) -> None:
        for text in (
            "an agent missed a useful field, endpoint, helper, source location, or root cause",
            "a different technical correction would have been better",
            "an iteration was inefficient",
            "parser, retry, fallback, storage, or deployment-specific rule",
            "agent-quality variance without a faithful-contract architecture counterexample",
        ):
            self.assertIn(text, CLOSURE)

    def test_state_tradeoff_stays_explicitly_state_free(self) -> None:
        section = CLOSURE.split("### 9. State, Restart, And Historical Efficiency — ACCEPTED TRADE-OFF", 1)[1]
        for text in (
            "No durable attempt history",
            "Positional ordinals",
            "Complete ready Ticket-set planning",
            "does not persist a Goal-achieved marker",
            "semantic hashes",
            "controller databases",
        ):
            self.assertIn(text, section)


if __name__ == "__main__":
    unittest.main()
