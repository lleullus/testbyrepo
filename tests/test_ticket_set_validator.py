from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATOR_DIR = ROOT / "matt/skills/to-tickets"
sys.path.insert(0, str(VALIDATOR_DIR))
try:
    import validate_ticket_set
finally:
    sys.path.pop(0)


def spec_outcome(name: str) -> str:
    return f"""- Outcome: {name}
  Acceptance boundary: local CLI output
  Trigger or inspection target: run product CLI
  Expected observable result: {name}
  Authoritative readback: CLI stdout
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | local CLI output
  External condition: None"""


def flow(parent: int, behavior: int, ac: int = 1) -> str:
    return f"""- Parent outcome ordinal: {parent}
  AC ordinals: {ac}
  Behavior authority ordinals: {behavior}
  Initial state: product is runnable
  Trigger or inspection target: run product CLI
  Acceptance boundary: local CLI output
  Expected observable result: expected output
  Authoritative readback: CLI stdout
  Decision boundary: stdout matches expected output
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | local CLI output
  External condition: None"""


class TicketSetFixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.work = self.root / "docs/planning/work/example"
        self.tickets = self.work / "tickets"
        self.tickets.mkdir(parents=True)
        self.spec = self.work / "SPEC.md"

    def close(self) -> None:
        self.temporary.cleanup()

    def write_spec(self, outcomes: int = 2, behaviors: int = 2) -> None:
        outcome_text = "\n".join(spec_outcome(f"outcome {index}") for index in range(1, outcomes + 1))
        behavior_text = "\n".join(
            f"- docs/planning/behavior/contexts/b{index}.md | Scope: behavior {index}"
            for index in range(1, behaviors + 1)
        )
        self.spec.write_text(
            f"""# Spec

Status: approved
Owner: test

## Verification Expectations

{outcome_text}

## Behavior Authorities

{behavior_text}

## Open Questions

None
""",
            encoding="utf-8",
        )

    def write_ticket(
        self,
        number: int,
        *,
        parent_outcome: int,
        behavior: int,
        status: str = "ready",
    ) -> Path:
        path = self.tickets / f"TICKET-{number:03d}.md"
        path.write_text(
            f"""# Ticket {number}

Status: {status}
Parent-Spec: ../SPEC.md
Project-Root: {self.root}
Worker:
UI: no

## Acceptance Criteria

- observable result {number}

## Scope

local CLI output

## Non-Goals

- unrelated behavior

## Blockers

None

## Verification

{flow(parent_outcome, 1)}

## Behavior Authorities

- docs/planning/behavior/contexts/b{behavior}.md | Scope: behavior {behavior}

## References

- ../SPEC.md
""",
            encoding="utf-8",
        )
        return path


class TicketSetValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = TicketSetFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_accepts_complete_ready_parent_outcome_coverage(self) -> None:
        self.fixture.write_spec(outcomes=2, behaviors=2)
        self.fixture.write_ticket(1, parent_outcome=1, behavior=1)
        self.fixture.write_ticket(2, parent_outcome=2, behavior=2)
        tickets = validate_ticket_set.validate_set(self.fixture.spec)
        self.assertEqual([path.name for path in tickets], ["TICKET-001.md", "TICKET-002.md"])

    def test_rejects_missing_parent_outcome_coverage(self) -> None:
        self.fixture.write_spec(outcomes=2, behaviors=1)
        self.fixture.write_ticket(1, parent_outcome=1, behavior=1)
        with self.assertRaisesRegex(
            validate_ticket_set.TicketSetValidationError,
            "does not cover every Parent Spec outcome",
        ):
            validate_ticket_set.validate_set(self.fixture.spec)

    def test_accepts_global_parent_behavior_without_ticket_acceptance_ownership(self) -> None:
        self.fixture.write_spec(outcomes=1, behaviors=2)
        self.fixture.write_ticket(1, parent_outcome=1, behavior=1)
        tickets = validate_ticket_set.validate_set(self.fixture.spec)
        self.assertEqual([path.name for path in tickets], ["TICKET-001.md"])

    def test_ralph_completable_rejects_nonverifiable_parent_outcome_before_ticket_use(self) -> None:
        self.fixture.write_spec(outcomes=1, behaviors=1)
        self.fixture.write_ticket(1, parent_outcome=1, behavior=1)
        text = self.fixture.spec.read_text(encoding="utf-8")
        self.fixture.spec.write_text(
            text.replace("Disposition: Independent", "Disposition: Not independently verifiable")
            .replace("Independent verification required: yes", "Independent verification required: no")
            .replace(
                "Acceptance surface: Existing | local CLI output",
                "Acceptance surface: None | approved contract exposes no completion evidence path",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            validate_ticket_set.TicketSetValidationError,
            "Ralph completion is not admitted: Spec outcome 1 has no approved completion evidence path",
        ):
            validate_ticket_set.validate_set(self.fixture.spec, require_completable=True)

    def test_rejects_non_ready_member(self) -> None:
        self.fixture.write_spec(outcomes=1, behaviors=1)
        self.fixture.write_ticket(1, parent_outcome=1, behavior=1, status="draft")
        with self.assertRaisesRegex(
            validate_ticket_set.TicketSetValidationError,
            "Ticket set is not ready",
        ):
            validate_ticket_set.validate_set(self.fixture.spec)


if __name__ == "__main__":
    unittest.main()
