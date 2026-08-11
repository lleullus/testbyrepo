from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
TO_TICKETS_SKILL = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
EXAMPLES = ROOT / "matt/examples"


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text)
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group(1).strip()


def top_level_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        if line.startswith("- "):
            items.append(line[2:])
        elif line.strip() and not line.startswith("  "):
            raise AssertionError(f"non-item top-level content: {line}")
    return items


class ActiveSkillContractTests(unittest.TestCase):
    def test_ticket_verification_flows_remain_exact_product_authority(self) -> None:
        normalized = " ".join(TO_TICKETS_SKILL.split())
        for required in (
            "states how the Ticket's Acceptance Criteria can be observed",
            "observable product flow, expected effect, and readback",
            "one exact top-level `- ` list item in authored order",
            "Preserve its count, order, product trigger, expected effect, readback, grouping, and meaning",
            "do not merge materially distinct flows",
            "split one flow into implementation seams",
            "weaken it into optional guidance",
        ):
            self.assertIn(required, normalized)

        tickets = [EXAMPLES / "TICKET.template.md"]
        tickets.extend(
            EXAMPLES / name / "tickets/TICKET-001.md"
            for name in ("simple-non-ui", "ui-prototype", "large-scope-shaping")
        )
        for ticket_path in tickets:
            with self.subTest(ticket=ticket_path):
                items = top_level_items(
                    section(ticket_path.read_text(encoding="utf-8"), "Verification")
                )
                self.assertTrue(items)

    def test_implementation_skill_preserves_direct_assignment_and_review(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "exact ready local Markdown Ticket",
            "Implementation Subagent",
            "Host Subagent Invocation Mechanism",
            "current project directly",
            "actual project diff",
            "every Markdown acceptance criterion (AC)",
            "same user-designated Implementation Subagent",
            "no known correctable in-scope due-now implementation work remains",
            "Gross actual-product liveness",
            "actual execution context and direct raw product-boundary result",
            "same-Ticket due-now implementation work",
            "checks actually performed",
            "exact unresolved limitations",
        ):
            self.assertIn(required, normalized)

    def test_research_remains_user_bounded_and_advisory(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "using only those designated models",
            "must not assign a separate research agent",
            "explicitly chooses parallel execution",
            "do not create additional delegation cost",
            "Its findings are advisory",
            "The Implementation Lead directly confirms",
            "limited to research models already designated by the user",
        ):
            self.assertIn(required, normalized)

    def test_result_cannot_become_independent_verification_or_ac_verdict(self) -> None:
        normalized = " ".join(IMPLEMENTATION_SKILL.split())
        for forbidden_claim in (
            "Do not assign independent verification readiness",
            "claim independent or direct AC evidence",
            "issue an AC verdict",
            "report final `VERIFIED` or any equivalent whole-Ticket success status",
        ):
            self.assertIn(forbidden_claim, normalized)
        self.assertIn(
            "implementation-result limitation",
            normalized,
        )
        self.assertIn(
            "outside the supported IIS lifecycle; do not claim it was established",
            normalized,
        )

    def test_no_verification_handoff_or_replacement_artifact_remains(self) -> None:
        for forbidden in (
            "Verification Lead",
            "Primary Verifier",
            "Runtime Runner",
            "route-navigation",
            "iis_ephemeral_transport",
            "publish_route_navigation",
            "serialized handoff exception",
            "verification-only",
        ):
            self.assertNotIn(forbidden, IMPLEMENTATION_SKILL)
        self.assertIn(
            "Do not create a serialized handoff, sidecar, replacement verification artifact, or approval workflow",
            " ".join(IMPLEMENTATION_SKILL.split()),
        )

    def test_active_contracts_exclude_removed_roles_and_runtime(self) -> None:
        combined = IMPLEMENTATION_SKILL + "\n" + TO_TICKETS_SKILL
        for forbidden in (
            "Verification Lead",
            "Primary Verifier",
            "Runtime Runner",
            "coverage_gate.py",
            "route-navigation",
            "iis_ephemeral_transport",
            "iis-verify",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
