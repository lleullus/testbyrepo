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
