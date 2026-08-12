from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATOR_PATH = ROOT / "matt/skills/to-tickets/validate_ticket.py"
SPEC = importlib.util.spec_from_file_location("validate_ticket", VALIDATOR_PATH)
assert SPEC and SPEC.loader
validate_ticket = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_ticket)


def spec_item(
    *,
    disposition: str = "Independent",
    required: str = "yes",
    surface: str = "Existing | local CLI output",
    external: str = "None",
    optional: str = "",
) -> str:
    return f"""- Outcome: observable result
  Acceptance boundary: local CLI output
  Trigger or inspection target: run the product CLI with nominal input
  Expected observable result: expected product output
  Authoritative readback: CLI stdout
  Disposition: {disposition}
  Independent verification required: {required}
  Acceptance surface: {surface}
  External condition: {external}{optional}"""


def flow_item(
    *,
    parent_outcome: str = "1",
    ordinals: str = "1",
    behavior_ordinals: str = "1",
    disposition: str = "Independent",
    required: str = "yes",
    surface: str = "Existing | local CLI output",
    external: str = "None",
    optional: str = "",
) -> str:
    return f"""- Parent outcome ordinal: {parent_outcome}
  AC ordinals: {ordinals}
  Behavior authority ordinals: {behavior_ordinals}
  Initial state: clean local input
  Trigger or inspection target: run the product CLI with nominal input
  Acceptance boundary: local CLI output
  Expected observable result: expected product output
  Authoritative readback: CLI stdout
  Decision boundary: stdout equals the expected product output
  Disposition: {disposition}
  Independent verification required: {required}
  Acceptance surface: {surface}
  External condition: {external}{optional}"""


class TicketFixture:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.work = self.root / "docs/planning/work/example"
        self.tickets = self.work / "tickets"
        self.tickets.mkdir(parents=True)
        self.spec_path = self.work / "SPEC.md"
        self.ticket_path = self.tickets / "TICKET-001.md"

    def close(self) -> None:
        self.temporary.cleanup()

    def write(
        self,
        *,
        spec_verification: str | None = None,
        ticket_verification: str | None = None,
        acceptance: str = "- first observable result",
        scope: str = "local CLI output",
        blockers: str = "None",
        ticket_status: str = "ready",
    ) -> None:
        self.spec_path.write_text(
            f"""# Spec

Status: approved
Owner: test

## Verification Expectations

{spec_verification or spec_item()}

## Behavior Authorities

- docs/planning/behavior/contexts/example.md | Scope: example behavior

## Open Questions

None
""",
            encoding="utf-8",
        )
        self.ticket_path.write_text(
            f"""# Ticket

Status: {ticket_status}
Parent-Spec: ../SPEC.md
Project-Root: {self.root}
Worker:
UI: no

## Acceptance Criteria

{acceptance}

## Scope

{scope}

## Blockers

{blockers}

## Verification

{ticket_verification or flow_item()}

## Behavior Authorities

- docs/planning/behavior/contexts/example.md | Scope: example behavior
""",
            encoding="utf-8",
        )


class TicketValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = TicketFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def assert_valid(self) -> None:
        validate_ticket.validate(self.fixture.ticket_path)

    def assert_invalid(self, fragment: str) -> None:
        with self.assertRaisesRegex(validate_ticket.TicketValidationError, fragment):
            validate_ticket.validate(self.fixture.ticket_path)

    def test_accepts_ready_independent_existing_surface(self) -> None:
        self.fixture.write()
        self.assert_valid()

    def test_accepts_greenfield_ticket_scope_owned_surface(self) -> None:
        surface = "Ticket Scope creates | disposable local CLI and stdout readback"
        self.fixture.write(
            spec_verification=spec_item(surface=surface),
            ticket_verification=flow_item(surface=surface),
            scope="Create the disposable local CLI and stdout readback.",
        )
        self.assert_valid()

    def test_accepts_confirmed_disposable_target_delivery_guarantee(self) -> None:
        surface = (
            "Delivery contract guarantees | disposable local workspace available "
            "for every verification session"
        )
        self.fixture.write(
            spec_verification=spec_item(surface=surface),
            ticket_verification=flow_item(surface=surface),
        )
        self.assert_valid()

    def test_accepts_operator_assisted_without_treating_normal_credential_need_as_blocker(self) -> None:
        kwargs = {
            "disposition": "Operator-assisted",
            "required": "no",
            "surface": "Operator-owned | production account readback",
            "external": "named operator uses the production credential",
        }
        self.fixture.write(
            spec_verification=spec_item(**kwargs),
            ticket_verification=flow_item(**kwargs),
        )
        self.assert_valid()

    def test_accepts_not_independently_verifiable_without_a_blocker(self) -> None:
        kwargs = {
            "disposition": "Not independently verifiable",
            "required": "no",
            "surface": "None | approved contract exposes no independent boundary",
            "external": "None",
        }
        self.fixture.write(
            spec_verification=spec_item(**kwargs),
            ticket_verification=flow_item(**kwargs),
        )
        self.assert_valid()

    def test_rejects_missing_and_out_of_range_bidirectional_ac_closure(self) -> None:
        self.fixture.write(
            acceptance="- first observable result\n- second observable result",
            ticket_verification=flow_item(ordinals="1"),
        )
        self.assert_invalid("close bidirectionally")
        self.fixture.write(ticket_verification=flow_item(ordinals="2"))
        self.assert_invalid("unknown AC ordinal")

    def test_rejects_duplicate_unordered_or_persistent_ac_references(self) -> None:
        for ordinals in ("1, 1", "2, 1", "AC-001"):
            with self.subTest(ordinals=ordinals):
                self.fixture.write(
                    acceptance="- first observable result\n- second observable result",
                    ticket_verification=flow_item(ordinals=ordinals),
                )
                self.assert_invalid("AC ordinals")

    def test_rejects_missing_duplicate_unknown_or_out_of_order_labels(self) -> None:
        valid = flow_item()
        cases = (
            valid.replace("  Initial state: clean local input\n", ""),
            valid.replace(
                "  Initial state: clean local input\n",
                "  Initial state: clean local input\n  Initial state: duplicate\n",
            ),
            valid.replace("  Initial state:", "  Runtime command:"),
            valid.replace(
                "  Initial state: clean local input\n  Trigger or inspection target: run the product CLI with nominal input",
                "  Trigger or inspection target: run the product CLI with nominal input\n  Initial state: clean local input",
            ),
        )
        for item in cases:
            with self.subTest(item=item):
                self.fixture.write(ticket_verification=item)
                self.assert_invalid("label|core")

    def test_rejects_invalid_or_unknown_parent_outcome_ordinal(self) -> None:
        for parent_outcome, fragment in (
            ("Outcome-1", "invalid Parent outcome ordinal"),
            ("2", "unknown Parent outcome ordinal"),
        ):
            with self.subTest(parent_outcome=parent_outcome):
                self.fixture.write(ticket_verification=flow_item(parent_outcome=parent_outcome))
                self.assert_invalid(fragment)

    def test_rejects_missing_invalid_or_unknown_behavior_authority_mapping(self) -> None:
        for behavior_ordinals, fragment in (
            ("None", "Behavior Authorities and Verification flows do not close"),
            ("B-1", "invalid Behavior authority ordinals"),
            ("2", "unknown Behavior authority ordinal"),
        ):
            with self.subTest(behavior_ordinals=behavior_ordinals):
                self.fixture.write(
                    ticket_verification=flow_item(behavior_ordinals=behavior_ordinals)
                )
                self.assert_invalid(fragment)

    def test_behavior_authority_paths_resolve_from_project_root_not_document_directory(self) -> None:
        self.fixture.write()
        text = self.fixture.ticket_path.read_text(encoding="utf-8")
        self.fixture.ticket_path.write_text(
            text.replace(
                "docs/planning/behavior/contexts/example.md | Scope: example behavior",
                "../../../behavior/contexts/example.md | Scope: example behavior",
            ),
            encoding="utf-8",
        )
        self.assert_invalid("canonical behavior authority directory")

    def test_rejects_ticket_behavior_authority_absent_from_parent_spec(self) -> None:
        self.fixture.write()
        text = self.fixture.ticket_path.read_text(encoding="utf-8")
        self.fixture.ticket_path.write_text(
            text.replace(
                "docs/planning/behavior/contexts/example.md | Scope: example behavior",
                "docs/planning/behavior/contexts/other.md | Scope: other behavior",
            ),
            encoding="utf-8",
        )
        self.assert_invalid("Behavior Authority is absent from Parent Spec")

    def test_rejects_parent_independent_required_non_independent(self) -> None:
        kwargs = {
            "disposition": "Operator-assisted",
            "required": "yes",
            "surface": "Operator-owned | production readback",
            "external": "operator credential required",
        }
        self.fixture.write(
            spec_verification=spec_item(**kwargs),
            ticket_verification=flow_item(**kwargs),
        )
        self.assert_invalid("requires independent verification")

    def test_rejects_independent_operator_owned_or_none_surface(self) -> None:
        for surface in (
            "Operator-owned | production readback",
            "None | no observable boundary",
        ):
            with self.subTest(surface=surface):
                self.fixture.write(
                    spec_verification=spec_item(surface=surface),
                    ticket_verification=flow_item(surface=surface),
                )
                self.assert_invalid("Independent surface")

    def test_rejects_not_available_independent_observation_fields(self) -> None:
        for field, current in (
            ("Acceptance boundary", "local CLI output"),
            ("Trigger or inspection target", "run the product CLI with nominal input"),
            ("Authoritative readback", "CLI stdout"),
        ):
            with self.subTest(field=field):
                spec = spec_item().replace(f"{field}: {current}", f"{field}: Not available | missing")
                flow = flow_item().replace(f"{field}: {current}", f"{field}: Not available | missing")
                self.fixture.write(spec_verification=spec, ticket_verification=flow)
                self.assert_invalid("Independent observation field is Not available")

    def test_rejects_scope_created_surface_not_owned_by_scope(self) -> None:
        surface = "Ticket Scope creates | disposable CLI and stdout readback"
        self.fixture.write(
            spec_verification=spec_item(surface=surface),
            ticket_verification=flow_item(surface=surface),
            scope="Only unrelated product behavior.",
        )
        self.assert_invalid("Scope does not own")

    def test_rejects_ticket_combination_absent_from_parent_spec(self) -> None:
        self.fixture.write(
            ticket_verification=flow_item(
                surface="Delivery contract guarantees | disposable workspace always available"
            )
        )
        self.assert_invalid("differs from mapped Parent Spec outcome")

    def test_parent_outcome_mapping_is_exact_not_any_compatible_parent_combination(self) -> None:
        operator = spec_item(
            disposition="Operator-assisted",
            required="no",
            surface="Operator-owned | production readback",
            external="named operator uses production access",
        ).replace("Outcome: observable result", "Outcome: second observable result")
        self.fixture.write(
            spec_verification=f"{spec_item()}\n{operator}",
            ticket_verification=flow_item(parent_outcome="2"),
        )
        self.assert_invalid("differs from mapped Parent Spec outcome")

    def test_rejects_unresolved_blocker_for_ready_but_not_normal_operator_condition(self) -> None:
        blocker = self.fixture.work / "BLOCKER.md"
        blocker.write_text("# Blocker\n\nStatus: open\n", encoding="utf-8")
        self.fixture.write(blockers="- ../BLOCKER.md")
        self.assert_invalid("unresolved blocker")

    def test_rejects_inaccessible_assumed_existing_surface_when_declared_blocker_is_unresolved(self) -> None:
        blocker = self.fixture.work / "BLOCKER.md"
        blocker.write_text("# Blocker\n\nStatus: open\n", encoding="utf-8")
        self.fixture.write(
            scope="Ticket Scope does not create the assumed existing CLI.",
            blockers="- ../BLOCKER.md",
        )
        self.assert_invalid("unresolved blocker")

    def test_rejects_condition_that_blocks_the_declared_operator_path(self) -> None:
        blocker = self.fixture.work / "BLOCKER.md"
        blocker.write_text("# Blocker\n\nStatus: open\n", encoding="utf-8")
        kwargs = {
            "disposition": "Operator-assisted",
            "required": "no",
            "surface": "Operator-owned | production account readback",
            "external": "named operator uses the production credential",
        }
        self.fixture.write(
            spec_verification=spec_item(**kwargs),
            ticket_verification=flow_item(**kwargs),
            blockers="- ../BLOCKER.md",
        )
        self.assert_invalid("unresolved blocker")

    def test_rejects_legacy_ready_ticket_without_structured_flow(self) -> None:
        self.fixture.write(ticket_verification="- run existing tests")
        self.assert_invalid("unlabeled|core")

    def test_rejects_cross_project_or_cross_work_parent_spec(self) -> None:
        self.fixture.write()
        foreign_root = self.fixture.root / "foreign"
        foreign_spec = foreign_root / "docs/planning/work/example/SPEC.md"
        foreign_spec.parent.mkdir(parents=True)
        foreign_spec.write_text(self.fixture.spec_path.read_text(encoding="utf-8"), encoding="utf-8")
        ticket = self.fixture.ticket_path.read_text(encoding="utf-8")
        self.fixture.ticket_path.write_text(
            ticket.replace("Parent-Spec: ../SPEC.md", f"Parent-Spec: {foreign_spec}"),
            encoding="utf-8",
        )
        self.assert_invalid("exact sibling work SPEC.md")

        other_work = self.fixture.root / "docs/planning/work/other"
        other_work.mkdir(parents=True)
        other_spec = other_work / "SPEC.md"
        other_spec.write_text(self.fixture.spec_path.read_text(encoding="utf-8"), encoding="utf-8")
        self.fixture.ticket_path.write_text(
            ticket.replace("Parent-Spec: ../SPEC.md", f"Parent-Spec: {other_spec}"),
            encoding="utf-8",
        )
        self.assert_invalid("exact sibling work SPEC.md")

    def test_rejects_noncanonical_ticket_path_name_and_parent_symlink(self) -> None:
        self.fixture.write()
        wrong_name = self.fixture.tickets / "ticket-001.md"
        wrong_name.write_text(self.fixture.ticket_path.read_text(encoding="utf-8"), encoding="utf-8")
        with self.assertRaisesRegex(validate_ticket.TicketValidationError, "TICKET-NNN"):
            validate_ticket.validate(wrong_name)

        link = self.fixture.work / "SPEC-LINK.md"
        link.symlink_to(self.fixture.spec_path)
        ticket = self.fixture.ticket_path.read_text(encoding="utf-8")
        self.fixture.ticket_path.write_text(
            ticket.replace("Parent-Spec: ../SPEC.md", "Parent-Spec: ../SPEC-LINK.md"),
            encoding="utf-8",
        )
        self.assert_invalid("exact sibling work SPEC.md")

    def test_rejects_absolute_symlink_or_work_escaping_blocker(self) -> None:
        blocker = self.fixture.work / "BLOCKER.md"
        blocker.write_text("# Blocker\n\nStatus: resolved\n", encoding="utf-8")
        self.fixture.write(blockers=f"- {blocker}")
        self.assert_invalid("local Markdown paths")

        link = self.fixture.work / "BLOCKER-LINK.md"
        link.symlink_to(blocker)
        self.fixture.write(blockers="- ../BLOCKER-LINK.md")
        self.assert_invalid("raw local path")

        outside = self.fixture.root / "OUTSIDE.md"
        outside.write_text("# Blocker\n\nStatus: resolved\n", encoding="utf-8")
        self.fixture.write(blockers="- ../../../../../OUTSIDE.md")
        self.assert_invalid("inside the Ticket work")

    def test_structural_validator_does_not_judge_flow_semantics_or_runtime(self) -> None:
        semantic_nonsense = flow_item().replace(
            "run the product CLI with nominal input", "run an internal mock test command"
        )
        self.fixture.write(
            spec_verification=spec_item().replace(
                "run the product CLI with nominal input", "run an internal mock test command"
            ),
            ticket_verification=semantic_nonsense,
        )
        self.assert_valid()

    def test_validator_source_contains_no_persistent_ac_identity_or_verdict_engine(self) -> None:
        source = VALIDATOR_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "criterionRawSha256",
            "AC-001",
            "coverage gate",
            "VERIFIED",
            "INCONCLUSIVE",
            "PASS",
            "FAIL",
        ):
            self.assertNotIn(forbidden, source)

    def test_active_examples_pass_the_same_structural_validator(self) -> None:
        for name in ("simple-non-ui", "ui-prototype", "large-scope-shaping"):
            with self.subTest(name=name):
                example = ROOT / "matt/examples" / name
                self.fixture.spec_path.write_text(
                    (example / "SPEC.md").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                ticket = (example / "tickets/TICKET-001.md").read_text(encoding="utf-8")
                ticket = re.sub(
                    r"(?m)^Project-Root: .+$",
                    f"Project-Root: {self.fixture.root}",
                    ticket,
                )
                self.fixture.ticket_path.write_text(ticket, encoding="utf-8")
                validate_ticket.validate(self.fixture.ticket_path)


if __name__ == "__main__":
    unittest.main()
