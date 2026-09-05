from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DecisionProvenanceContractTests(unittest.TestCase):
    def test_router_defines_minimal_non_continuation_provenance_without_new_lifecycle(self) -> None:
        router = (ROOT / "iis-workflow" / "SKILL.md").read_text(encoding="utf-8")

        for field in (
            "Decision:",
            "Governing authority:",
            "Observed condition:",
            "Effect:",
            "Next allowed action:",
        ):
            self.assertIn(field, router)

        for guardrail in (
            "not a new lifecycle state",
            "ordinary successful continuation",
            "tool, transport, or protocol failure",
            "not evidence by itself",
            "do not present a model preference, guessed cause, or hidden reasoning as IIS authority",
        ):
            self.assertIn(guardrail, router)

    def test_planning_leaves_preserve_existing_result_and_explain_non_continuation(self) -> None:
        shaper = (ROOT / "scope-shaper" / "SKILL.md").read_text(encoding="utf-8")
        matt = (ROOT / "matt" / "skills" / "ask-matt" / "SKILL.md").read_text(encoding="utf-8")
        to_spec = (ROOT / "matt" / "skills" / "to-spec" / "SKILL.md").read_text(encoding="utf-8")
        to_tickets = (ROOT / "matt" / "skills" / "to-tickets" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Non-Continuation Decision Provenance", shaper)
        self.assertIn("Decision: ASK MATT: SCOPE SHAPING REQUIRED", matt)
        self.assertIn(
            "Governing authority: ask-matt / Entry Routing And Scope Handoff Preflight",
            matt,
        )
        self.assertIn("Decision: TO SPEC: BLOCKED", to_spec)
        self.assertIn("Governing authority: to-spec / Source Increment Admission", to_spec)
        self.assertIn("Non-Continuation Decision Provenance", to_tickets)
        self.assertIn("must not invent a new Ticket status", to_tickets)

    def test_adaptive_distinguishes_owner_stop_from_whole_run_state(self) -> None:
        terminal = (
            ROOT / "iis-adaptive-planning" / "references" / "07-terminal-report.md"
        ).read_text(encoding="utf-8")

        for required in (
            "## Decision provenance",
            "Owner status:",
            "Invocation status:",
            "Returned to:",
            "Planning owner result: STOP",
            "Governing authority: iis-adaptive-planning / Terminal boundary + active Run Contract",
        ):
            self.assertIn(required, terminal)

    def test_delivery_owners_explain_only_non_continuation_boundaries(self) -> None:
        implement_skill = (
            ROOT / "companion-skills" / "ready-ticket-implement" / "SKILL.md"
        ).read_text(encoding="utf-8")
        implement_ref = (
            ROOT
            / "companion-skills"
            / "ready-ticket-implement"
            / "references"
            / "implement.md"
        ).read_text(encoding="utf-8")
        probe = (
            ROOT / "companion-skills" / "ready-ticket-heuristic-probe" / "SKILL.md"
        ).read_text(encoding="utf-8")
        verify_skill = (
            ROOT / "companion-skills" / "ready-ticket-verify" / "SKILL.md"
        ).read_text(encoding="utf-8")
        verify_ref = (
            ROOT
            / "companion-skills"
            / "ready-ticket-verify"
            / "references"
            / "verify.md"
        ).read_text(encoding="utf-8")

        self.assertIn("`Completion: BLOCKED | PARTIAL`", implement_skill)
        self.assertIn("### Non-continuation provenance", implement_ref)
        self.assertIn("정상 `COMPLETE`", implement_ref)
        self.assertIn("For `Probe Completion: PARTIAL | BLOCKED` or `SUBAGENT CAPABILITY UNAVAILABLE`", probe)
        self.assertIn("normal `Probe Completion: COMPLETE`", probe)
        self.assertIn("Every caller-facing `VERIFICATION NOT STARTED` result", verify_skill)
        self.assertIn("Decision: VERIFICATION NOT STARTED", verify_ref)
        self.assertIn(
            "Do not append them to a normal evidence-complete `FAILED` verdict",
            verify_ref,
        )


# Static authoring checks: these validate real reference/template structure, not
# whether a model follows the skill correctly in an executed conversation.
PROVENANCE_FIELDS = (
    "Decision",
    "Governing authority",
    "Observed condition",
    "Effect",
    "Next allowed action",
)


def text_blocks(path: Path) -> list[str]:
    return re.findall(r"```text\n(.*?)\n```", path.read_text(encoding="utf-8"), re.DOTALL)


def field_counts(block: str) -> Counter[str]:
    return Counter(re.findall(r"^([A-Z][A-Za-z /-]*):", block, re.MULTILINE))


class DecisionProvenanceStructureTests(unittest.TestCase):
    def test_shared_template_has_only_the_five_provenance_fields(self) -> None:
        router = ROOT / "iis-workflow" / "SKILL.md"
        block = next(block for block in text_blocks(router) if block.startswith("Decision:"))
        self.assertEqual(field_counts(block), Counter(PROVENANCE_FIELDS))

    def test_direct_planning_leaves_resolve_the_shared_contract(self) -> None:
        target = ROOT / "iis-workflow" / "SKILL.md"
        fragment = "non-continuation-decision-provenance"
        for relative in (
            "scope-shaper/SKILL.md",
            "matt/skills/ask-matt/SKILL.md",
            "matt/skills/to-spec/SKILL.md",
            "matt/skills/to-tickets/SKILL.md",
        ):
            with self.subTest(skill=relative):
                skill = ROOT / relative
                links = re.findall(
                    rf"\[[^\]]+\]\(([^)\s]+#{fragment})\)",
                    skill.read_text(encoding="utf-8"),
                )
                self.assertTrue(links, "Direct entry needs a resolvable shared-contract reference")
                for link in links:
                    resolved = (skill.parent / link.split("#", 1)[0]).resolve()
                    self.assertEqual(resolved, target.resolve())
                    self.assertTrue(resolved.is_file())
                    self.assertIn(
                        "## Non-Continuation Decision Provenance\n",
                        resolved.read_text(encoding="utf-8"),
                    )

    def test_planning_failure_templates_preserve_results_and_resolve_rule_sections(self) -> None:
        for relative in (
            "matt/skills/ask-matt/SKILL.md",
            "matt/skills/to-spec/SKILL.md",
        ):
            skill = ROOT / relative
            source = skill.read_text(encoding="utf-8")
            reports = [block for block in text_blocks(skill) if "Governing authority:" in block]
            self.assertTrue(reports)
            for block in reports:
                header = block.splitlines()[0]
                with self.subTest(skill=relative, result=header):
                    counts = field_counts(block)
                    for key in PROVENANCE_FIELDS:
                        self.assertEqual(counts[key], 1, f"Missing or duplicate {key}")
                    fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
                    self.assertEqual(fields["Decision"], header)
                    owner, section = fields["Governing authority"].split(" / ", 1)
                    self.assertEqual(owner, skill.parent.name)
                    self.assertIn(f"\n## {section}\n", source)

    def test_delivery_capability_returns_link_to_provenance_fields(self) -> None:
        for owner, reference, heading in (
            ("ready-ticket-implement", "references/implement.md", "Non-continuation provenance"),
            ("ready-ticket-heuristic-probe", "SKILL.md", "Result boundary"),
            ("ready-ticket-verify", "references/verify.md", "2. Admission and current authority"),
        ):
            with self.subTest(owner=owner):
                skill = ROOT / "companion-skills" / owner / "SKILL.md"
                returns = [
                    line for line in skill.read_text(encoding="utf-8").splitlines()
                    if "`SUBAGENT CAPABILITY UNAVAILABLE`" in line
                ]
                links = [
                    link for line in returns
                    for link in re.findall(r"\[[^\]]+\]\(([^)\s]*#[^)\s]+)\)", line)
                ]
                self.assertTrue(links, "Capability return must route to the existing provenance schema")
                expected = skill.parent / reference
                fragment = re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
                for link in links:
                    filename, anchor = link.split("#", 1)
                    target = (skill.parent / filename) if filename else skill
                    self.assertEqual(target.resolve(), expected.resolve())
                    self.assertEqual(anchor, fragment)
                    source = target.read_text(encoding="utf-8")
                    self.assertRegex(source, rf"(?m)^##?#+ {re.escape(heading)}$")
                    self.assertTrue(any(
                        all(field_counts(block)[key] == 1 for key in PROVENANCE_FIELDS)
                        for block in text_blocks(target)
                    ))

    def test_adaptive_return_templates_do_not_shadow_provenance_fields(self) -> None:
        terminal = ROOT / "iis-adaptive-planning" / "references" / "07-terminal-report.md"
        blocks = text_blocks(terminal)
        common = next(block for block in blocks if block.startswith("Decision:"))
        for header in (
            "IIS ADAPTIVE RUN CONTRACT: USER INPUT REQUIRED",
            "IIS ADAPTIVE PLANNING: USER DECISION REQUIRED",
            "IIS ADAPTIVE COMPLETION EVIDENCE REQUIRED",
            "IIS ADAPTIVE RUN CONTRACT: AUTHORITY GAP",
        ):
            with self.subTest(result=header):
                reports = [block for block in blocks if block.startswith(header + "\n")]
                self.assertEqual(len(reports), 1)
                counts = field_counts(common + "\n" + reports[0])
                for key in PROVENANCE_FIELDS:
                    self.assertEqual(counts[key], 1, f"Template shadows provenance field {key}")


if __name__ == "__main__":
    unittest.main()
