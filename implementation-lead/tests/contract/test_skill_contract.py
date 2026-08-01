from __future__ import annotations

import re
import unittest
from pathlib import Path


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[2]
SKILL = (IMPLEMENTATION_ROOT / "SKILL.md").read_text(encoding="utf-8")


class ImplementationSkillContractTests(unittest.TestCase):
    def test_adapter_native_mechanics_are_absent(self) -> None:
        forbidden = [
            r"\bNode\b",
            r"\bPython\b",
            r"\bGo\b",
            r"nativeReport",
            r"contextDigest",
            r"adapterVersion",
            r"references/adapters",
            r"adapters/node",
            r"adapters/python",
            r"adapters/go",
            r"per-task Fast",
            r"Full entry",
        ]
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, SKILL), pattern)

    def test_run_state_is_implementation_only(self) -> None:
        for state in (
            "PREFLIGHT",
            "IMPLEMENTING",
            "FINAL_REVIEW",
            "IMPLEMENTATION_COMPLETE",
            "INCOMPLETE",
            "BLOCKED",
            "PENDING",
            "WORKER_RUNNING",
            "REVIEWING",
            "IMPLEMENTED",
        ):
            self.assertIn(state, SKILL)
        for removed in (
            "READY_FOR_VERIFICATION",
            "verificationSessionId",
            "verificationResultId",
            "verificationVerdict",
            "currentnessResult",
            "checkpointHistoryRefs",
            "ImplementationHandoff",
            "assertCurrent",
        ):
            self.assertNotIn(removed, SKILL)

    def test_first_worker_requires_baseline_capsule_not_verification_lead(self) -> None:
        self.assertIn("../baseline-capsule/baseline_capsule.py create", SKILL)
        self.assertIn("Immediately before dispatching the first\nWorker", SKILL)
        self.assertIn("require exact equality with\n`baselineSourceIdentity`", SKILL)
        self.assertIn("Do not invoke Verification Lead from this skill", SKILL)

    def test_capsule_failure_prevents_worker_dispatch(self) -> None:
        self.assertIn("no Worker may run after either result", SKILL)
        self.assertIn("missing or expired Capsules are never silently replaced", SKILL)
        self.assertIn("For a genuine zero-mutation Ticket path, create the Capsule", SKILL)

    def test_implemented_is_source_review_not_verification(self) -> None:
        self.assertIn("task_implementation_review_complete", SKILL)
        self.assertIn("does not claim a separate\ntechnical verification verdict", SKILL)

    def test_final_review_binds_two_equal_source_identities(self) -> None:
        self.assertIn("finalReviewStartIdentity", SKILL)
        self.assertIn("finalSourceIdentity", SKILL)
        self.assertIn("Require exact equality between both final-review identities", SKILL)

    def test_completion_publishes_independent_result(self) -> None:
        self.assertIn("implementation-result-v2", SKILL)
        self.assertIn("implementation_result.py publish", SKILL)
        self.assertIn("immutable ImplementationResult publication succeeded", SKILL)
        self.assertIn("It does not mean `VERIFIED`", SKILL)

    def test_later_verification_cannot_reopen_implementation(self) -> None:
        self.assertIn("starts\na new Implementation Lead invocation; it never reopens this one", SKILL)
        self.assertIn("cannot retroactively alter this\ninvocation's immutable result", SKILL)


if __name__ == "__main__":
    unittest.main()
