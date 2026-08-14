from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
ROUTER = (ROOT / "iis-workflow/SKILL.md").read_text(encoding="utf-8")
LOOP = (ROOT / "iis-goal-loop/SKILL.md").read_text(encoding="utf-8")
IMPLEMENTATION = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
RUNNER = (ROOT / "verification-runner/SKILL.md").read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


class VerificationRunnerTopologyContractTests(unittest.TestCase):
    def test_role_binding_and_consumption_timing(self) -> None:
        body = normalized(ROUTER + LOOP + IMPLEMENTATION + RUNNER)
        for phrase in (
            "Model identity alone is not a role",
            "separate user designation",
            "reservation",
            "consumption timing",
            "pre-consume a role the user reserved for a later correction",
            "Never select an assignee first and reinterpret its role",
            "assignment/authority mismatch",
        ):
            self.assertIn(phrase, body)

    def test_related_finding_prefers_existing_implementation(self) -> None:
        body = normalized(LOOP + IMPLEMENTATION)
        for phrase in (
            "give the observation to that existing invocation first",
            "consume another user-reserved implementation role",
            "feed it to the existing admitted role first",
            "recheck current source",
            "not defect/AC/file ownership",
        ):
            self.assertIn(phrase, body)

    def test_runner_is_observation_role(self) -> None:
        body = normalized(RUNNER)
        for phrase in (
            "calling Lead owns the authored denominator",
            "Runner reports only raw current observation",
            "choose an implementation worker",
            "Do not invoke otherwise-unused Runner slots merely to consume a roster",
        ):
            self.assertIn(phrase, body)


if __name__ == "__main__":
    unittest.main()
