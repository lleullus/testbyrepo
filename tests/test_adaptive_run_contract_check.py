from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "iis-adaptive-planning" / "tools" / "check_run_contract.py"
TEMPLATE_PATH = (
    ROOT / "iis-adaptive-planning" / "templates" / "ADAPTIVE-RUN-CONTRACT.template.md"
)
SPEC = importlib.util.spec_from_file_location("adaptive_run_contract_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def contract(**changes: str) -> str:
    values = {
        "status": "CLOSED",
        "project_root": "Not established yet",
        "mandate": "current-conversation authority",
        "gate": "not_required",
        "goal": "Produce the assigned current planning result.",
        "required": "None required",
        "candidate": "None named",
        "policy": "NONE_REQUIRED",
        "implementation": "no",
        "verification": "no",
        "implementation_mode": "disabled",
        "implementation_selection": "Not applicable",
        "implementation_basis": "Not applicable",
        "verification_mode": "disabled",
        "verification_selection": "Not applicable",
        "verification_basis": "Not applicable",
        "boundary": "READY_TICKET_SET",
        "predicate": "The current validated Ready Ticket Set exists.",
        "readback": "Not yet established",
        "source": "Current user instruction in this conversation.",
        "unresolved": "None",
        "notes": "",
    }
    values.update(changes)
    return f"""# IIS Adaptive Run Contract

Status: {values['status']}
Project-Root: {values['project_root']}
Mandate: {values['mandate']}
Run Contract Approval Gate: {values['gate']}

## Goal Outcome

{values['goal']}

## Required Named Items

{values['required']}

## Candidate Named Items

{values['candidate']}

## Required Item Policy

{values['policy']}

## Delivery Stages

Implementation: {values['implementation']}
Verification: {values['verification']}

## Delivery Model Selection

| Stage | Execution mode | Selected model / effort | User-selection basis |
| --- | --- | --- | --- |
| Implementation | {values['implementation_mode']} | {values['implementation_selection']} | {values['implementation_basis']} |
| Verification | {values['verification_mode']} | {values['verification_selection']} | {values['verification_basis']} |

## Run Completion Boundary

{values['boundary']}

## Completion Predicate

{values['predicate']}

## Authoritative Readback

{values['readback']}

## Source Authority

{values['source']}

## Unresolved Field

{values['unresolved']}
{values['notes']}"""


def messages(text: str) -> list[str]:
    return [diagnostic.message for diagnostic in CHECKER.check_run_contract(text)]


class AdaptiveRunContractStructureTests(unittest.TestCase):
    def test_planning_only_and_required_approval_are_valid_structures(self) -> None:
        self.assertEqual(CHECKER.check_run_contract(contract()), [])
        self.assertEqual(CHECKER.check_run_contract(contract(gate="required")), [])

    def test_closed_delivered_contract_with_selected_models_is_valid(self) -> None:
        text = contract(
            implementation="yes",
            verification="yes",
            implementation_mode="SUBAGENT",
            implementation_selection="implementation-model / high",
            implementation_basis="current user selection",
            verification_mode="SUBAGENT",
            verification_selection="verification-model / high",
            verification_basis="current user selection",
            boundary="CURRENT_INCREMENT_DELIVERED",
        )
        self.assertEqual(CHECKER.check_run_contract(text), [])

    def test_user_input_required_allows_actual_unresolved_model_selection(self) -> None:
        text = contract(
            status="USER_INPUT_REQUIRED",
            implementation="yes",
            verification="yes",
            implementation_mode="SUBAGENT",
            implementation_selection="Not selected",
            implementation_basis="unresolved",
            verification_mode="SUBAGENT",
            verification_selection="Not selected",
            verification_basis="unresolved",
            boundary="CURRENT_INCREMENT_DELIVERED",
            unresolved="Implementation and Verification model / effort",
        )
        self.assertEqual(CHECKER.check_run_contract(text), [])

    def test_delivered_boundaries_reject_disabled_verification(self) -> None:
        for boundary in (
            "CURRENT_INCREMENT_DELIVERED",
            "NAMED_REQUIRED_ITEMS_DELIVERED",
        ):
            with self.subTest(boundary=boundary):
                text = contract(
                    required="- Required result",
                    policy="EXACT_REQUIRED_SET",
                    implementation="yes",
                    implementation_mode="DIRECT",
                    boundary=boundary,
                )
                self.assertTrue(
                    any("requires Verification yes" in message for message in messages(text))
                )

    def test_stage_modes_follow_enabled_switches(self) -> None:
        direct = contract(
            implementation="yes",
            implementation_mode="DIRECT",
            boundary="CURRENT_INCREMENT_IMPLEMENTED",
        )
        self.assertEqual(CHECKER.check_run_contract(direct), [])

        invalid = contract(
            implementation="yes",
            verification="yes",
            implementation_mode="SUBAGENT",
            implementation_selection="model-a / high",
            implementation_basis="user selected model-a",
            verification_mode="DIRECT",
            verification_selection="model-b / high",
            verification_basis="user selected model-b",
            boundary="CURRENT_INCREMENT_DELIVERED",
        )
        result = CHECKER.check_run_contract(invalid)
        self.assertTrue(any(item.field == "Verification" for item in result))
        self.assertTrue(all(item.line > 0 for item in result))

    def test_closed_subagent_requires_selection_and_basis(self) -> None:
        text = contract(
            implementation="yes",
            implementation_mode="SUBAGENT",
            implementation_selection="Not selected",
            implementation_basis="unresolved",
            boundary="CURRENT_INCREMENT_IMPLEMENTED",
        )
        result = CHECKER.check_run_contract(text)
        self.assertEqual(sum(item.field == "Implementation" for item in result), 2)

    def test_closed_subagent_rejects_empty_selection_and_basis(self) -> None:
        text = contract(
            implementation="yes",
            implementation_mode="SUBAGENT",
            implementation_selection="",
            implementation_basis="",
            boundary="CURRENT_INCREMENT_IMPLEMENTED",
        )
        result = CHECKER.check_run_contract(text)
        self.assertEqual(sum(item.field == "Implementation" for item in result), 2)

    def test_required_policy_and_cross_list_duplication_are_checked(self) -> None:
        missing = contract(policy="EXACT_REQUIRED_SET")
        self.assertIn(
            "EXACT_REQUIRED_SET requires Required Named Items", messages(missing)
        )

        unexpected = contract(required="- Must ship", policy="NONE_REQUIRED")
        self.assertIn("NONE_REQUIRED requires exact 'None required'", messages(unexpected))

        duplicate = contract(
            required="- Must   ship",
            candidate="- Must ship",
            policy="EXACT_REQUIRED_SET",
        )
        self.assertTrue(any("also appears" in message for message in messages(duplicate)))

    def test_source_sets_preserve_policy_and_execution_restrictions(self):
        reference = "From source: /project/THESIS-001.md#Required Outcomes / Means"
        text = contract(required=reference, policy="EXACT_REQUIRED_SET")
        self.assertEqual(CHECKER.check_run_contract(text), [])
        self.assertTrue(messages(contract(required=reference, policy="NONE_REQUIRED")))
        self.assertTrue(messages(contract(required=reference, candidate=reference, policy="EXACT_REQUIRED_SET")))
        self.assertTrue(messages(contract(required=reference, policy="EXACT_REQUIRED_SET", boundary="NAMED_REQUIRED_ITEMS_DELIVERED")))

    def test_source_set_requires_exact_path_and_section(self):
        for value in ("From source: latest", "From source: /project/thesis.md", "From source: <source>#Required"):
            with self.subTest(value=value):
                self.assertTrue(messages(contract(required=value, policy="EXACT_REQUIRED_SET")))

    def test_duplicate_fields_sections_and_unknown_enums_are_rejected(self) -> None:
        duplicate_field = contract().replace(
            "Status: CLOSED", "Status: CLOSED\nStatus: CLOSED", 1
        )
        self.assertTrue(
            any(item.field == "Status" and item.line > 0 for item in CHECKER.check_run_contract(duplicate_field))
        )

        duplicate_section = contract() + "\n\n## Goal Outcome\n\nAnother goal.\n"
        self.assertTrue(
            any(
                item.field == "Goal Outcome" and item.line > 0
                for item in CHECKER.check_run_contract(duplicate_section)
            )
        )

        self.assertTrue(
            any("unknown value" in message for message in messages(contract(policy="BEST_EFFORT")))
        )

    def test_notes_and_fenced_examples_do_not_shadow_real_fields(self) -> None:
        notes = """

## Notes

Status: BROKEN

```text
## Required Named Items
- Shadow item
Verification: yes
```
"""
        self.assertEqual(CHECKER.check_run_contract(contract(notes=notes)), [])

    def test_broad_already_satisfied_boundary_is_not_forced_to_yes_yes(self) -> None:
        self.assertEqual(
            CHECKER.check_run_contract(
                contract(
                    boundary="BOUNDED_OUTCOME_SATISFIED",
                    predicate="The assigned outcome is present in fresh actual state.",
                    readback="The actual product surface already exposes the outcome.",
                )
            ),
            [],
        )

    def test_reshape_does_not_create_digest_or_staleness_requirement(self) -> None:
        first = contract(required="- Ticket A", policy="EXACT_REQUIRED_SET")
        reshaped = contract(required="- Ticket B", policy="EXACT_REQUIRED_SET")
        self.assertEqual(CHECKER.check_run_contract(first), [])
        self.assertEqual(CHECKER.check_run_contract(reshaped), [])

    def test_semantic_weakness_is_outside_the_structure_verdict(self) -> None:
        weak = contract(
            goal="A",
            predicate="A",
            readback="some output",
            source="uncorroborated summary",
        )
        self.assertEqual(CHECKER.check_run_contract(weak), [])

    def test_template_and_checker_share_current_structural_vocabulary(self) -> None:
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        for section in CHECKER.REQUIRED_SECTIONS:
            self.assertIn(f"## {section}\n", template)
        for value in (
            *CHECKER.STATUSES,
            *CHECKER.REQUIRED_ITEM_POLICIES,
            *CHECKER.RUN_COMPLETION_BOUNDARIES,
            *CHECKER.APPROVAL_GATES,
        ):
            self.assertIn(value, template)


class AdaptiveRunContractCliTests(unittest.TestCase):
    def run_checker(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(CHECKER_PATH), *args],
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_exit_codes_and_diagnostics(self) -> None:
        valid = self.run_checker(stdin=contract())
        self.assertEqual(valid.returncode, 0)
        self.assertEqual(valid.stdout, "STRUCTURE_VALID\n")

        invalid = self.run_checker(
            stdin=contract(boundary="CURRENT_INCREMENT_DELIVERED")
        )
        self.assertEqual(invalid.returncode, 1)
        self.assertTrue(invalid.stdout.startswith("STRUCTURE_INVALID\n"))
        self.assertIn("field=Run Completion Boundary line=", invalid.stdout)

        missing = self.run_checker("--file", "/does/not/exist")
        self.assertEqual(missing.returncode, 2)
        self.assertTrue(missing.stderr.startswith("INPUT_ERROR:"))

    def test_file_mode_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "run-contract.md"
            original = contract()
            source.write_text(original, encoding="utf-8")

            result = self.run_checker("--file", str(source))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertEqual(list(root.iterdir()), [source])


if __name__ == "__main__":
    unittest.main()
