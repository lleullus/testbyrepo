from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "matt" / "examples"
ACTIVE = (
    EXAMPLES / "simple-non-ui",
    EXAMPLES / "ui-prototype",
    EXAMPLES / "large-scope-shaping",
)


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text)
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group(1).strip()


def authority_item(block: str) -> tuple[str, str]:
    match = re.fullmatch(r"- (.+(?:\.md|path)>)?([^ ]*\.md)? \| Scope: (.+)", block)
    if not match:
        raise AssertionError(f"invalid authority item: {block}")
    return (match.group(1) or match.group(2)), match.group(3)


class ActiveMattExampleTests(unittest.TestCase):
    def test_templates_have_behavior_authorities_in_contract_order(self) -> None:
        spec = (EXAMPLES / "SPEC.template.md").read_text(encoding="utf-8")
        ticket = (EXAMPLES / "TICKET.template.md").read_text(encoding="utf-8")
        self.assertLess(spec.index("## Verification Expectations"), spec.index("## Behavior Authorities"))
        self.assertLess(spec.index("## Behavior Authorities"), spec.index("## UI / UX"))
        self.assertLess(ticket.index("## Verification"), ticket.index("## Behavior Authorities"))
        self.assertLess(ticket.index("## Behavior Authorities"), ticket.index("## References"))
        authority_item(section(spec, "Behavior Authorities").split("\n\n", 1)[0])
        authority_item(section(ticket, "Behavior Authorities").split("\n\n", 1)[0])

    def test_active_specs_and_tickets_share_behavior_authorities(self) -> None:
        for example in ACTIVE:
            with self.subTest(example=example.name):
                spec_path = example / "SPEC.md"
                ticket_path = example / "tickets" / "TICKET-001.md"
                spec = spec_path.read_text(encoding="utf-8")
                ticket = ticket_path.read_text(encoding="utf-8")
                spec_ref, spec_scope = authority_item(section(spec, "Behavior Authorities"))
                ticket_ref, ticket_scope = authority_item(section(ticket, "Behavior Authorities"))
                self.assertEqual(spec_scope, ticket_scope)
                self.assertEqual(
                    (spec_path.parent / spec_ref).resolve(),
                    (ticket_path.parent / ticket_ref).resolve(),
                )
                authority = (spec_path.parent / spec_ref).resolve().read_text(encoding="utf-8")
                self.assertEqual(authority.count("Status: approved"), 1)
                self.assertRegex(authority, r"(?m)^Owner: .+$")
                self.assertRegex(authority, r"(?m)^Scope: .+$")

    def test_ui_example_references_same_complete_ui_authority(self) -> None:
        example = EXAMPLES / "ui-prototype"
        spec_path = example / "SPEC.md"
        ticket_path = example / "tickets" / "TICKET-001.md"
        spec = spec_path.read_text(encoding="utf-8")
        ticket = ticket_path.read_text(encoding="utf-8")
        ui_ref, _ = authority_item(section(spec, "UI / UX").split("\n\n", 1)[0])
        target = (spec_path.parent / ui_ref).resolve()
        references = {
            (ticket_path.parent / item[2:]).resolve()
            for item in section(ticket, "References").splitlines()
            if item.startswith("- ")
        }
        self.assertIn(target, references)
        authority = target.read_text(encoding="utf-8")
        self.assertIn("Scope:", authority)
        self.assertIn("narrow", authority)
        self.assertIn("wide", authority)
        self.assertIn("focus order", authority)
        self.assertIn("## Open Questions\n\nNone", authority)

    def test_non_ui_examples_do_not_require_ui_authority(self) -> None:
        for name in ("simple-non-ui", "large-scope-shaping"):
            spec = (EXAMPLES / name / "SPEC.md").read_text(encoding="utf-8")
            ticket = (EXAMPLES / name / "tickets" / "TICKET-001.md").read_text(encoding="utf-8")
            self.assertEqual(section(spec, "UI / UX"), "Not applicable")
            self.assertIn("UI: no", ticket)

    def test_active_examples_do_not_teach_wayfinder(self) -> None:
        for example in ACTIVE:
            for path in example.rglob("*.md"):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("WAYFINDER.md", text)
                self.assertNotIn("Wayfinder", text)
        self.assertFalse((EXAMPLES / "large-wayfinder").exists())


if __name__ == "__main__":
    unittest.main()
