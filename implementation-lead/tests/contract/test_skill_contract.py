from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_SKILL = (ROOT / "implementation-lead/SKILL.md").read_text(encoding="utf-8")
VERIFICATION_SKILL = (ROOT / "verification-lead/SKILL.md").read_text(encoding="utf-8")
PRIMARY_SKILL = (ROOT / "primary-verifier/SKILL.md").read_text(encoding="utf-8")
TO_TICKETS_SKILL = (ROOT / "matt/skills/to-tickets/SKILL.md").read_text(encoding="utf-8")
EXAMPLES = ROOT / "matt/examples"
COVERAGE_GATE_PATH = ROOT / "verification-lead/coverage_gate.py"
COVERAGE_GATE_SPEC = importlib.util.spec_from_file_location("coverage_gate", COVERAGE_GATE_PATH)
assert COVERAGE_GATE_SPEC and COVERAGE_GATE_SPEC.loader
coverage_gate = importlib.util.module_from_spec(COVERAGE_GATE_SPEC)
COVERAGE_GATE_SPEC.loader.exec_module(coverage_gate)


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text)
    if not match:
        raise AssertionError(f"missing section: {heading}")
    return match.group(1).strip()


class ActiveSkillContractTests(unittest.TestCase):
    def test_ticket_verification_is_compatible_with_coverage_gate_roots(self) -> None:
        self.assertIn(
            "Serialize each materially distinct Verification product flow as one exact\n"
            "top-level `- ` list item",
            TO_TICKETS_SKILL,
        )

        tickets = [EXAMPLES / "TICKET.template.md"]
        tickets.extend(
            EXAMPLES / name / "tickets/TICKET-001.md"
            for name in ("simple-non-ui", "ui-prototype", "large-scope-shaping")
        )
        for ticket_path in tickets:
            with self.subTest(ticket=ticket_path):
                self.assertTrue(
                    coverage_gate._top_level_items(
                        section(ticket_path.read_text(encoding="utf-8"), "Verification"),
                        "Verification",
                    )
                )

    def test_implementation_skill_names_direct_subagent_and_review_contract(self) -> None:
        implementation_skill = " ".join(IMPLEMENTATION_SKILL.split())
        implementation_skill_lower = implementation_skill.lower()
        self.assertIn("exact ready local Markdown Ticket", IMPLEMENTATION_SKILL)
        self.assertIn("Implementation Subagent", IMPLEMENTATION_SKILL)
        self.assertIn("Host Subagent Invocation Mechanism", IMPLEMENTATION_SKILL)
        self.assertIn("current project directly", IMPLEMENTATION_SKILL)
        self.assertIn("actual project diff", IMPLEMENTATION_SKILL)
        self.assertIn("every Markdown acceptance criterion (AC)", IMPLEMENTATION_SKILL)
        self.assertIn("known remaining implementation work", implementation_skill)
        self.assertIn("same user-designated Implementation Subagent", implementation_skill)
        self.assertIn("no known correctable in-scope due-now implementation work remains", implementation_skill)
        self.assertIn("requires direct runtime evidence", implementation_skill)
        self.assertIn("must not report", implementation_skill)

        self.assertIn(
            "If the user explicitly designates one or more implementation research models, invoke "
            "`Implementation Research Agent` roles using only those designated models",
            implementation_skill,
        )
        self.assertIn(
            "using only those designated models through the host's `Host Subagent Invocation Mechanism`",
            implementation_skill,
        )
        self.assertIn(
            "If the user does not designate an implementation research model, the Implementation Lead performs "
            "the needed research directly and must not assign a separate research agent",
            implementation_skill,
        )
        self.assertIn(
            "Parallel research is allowed only when the user designates multiple research models and explicitly "
            "chooses parallel execution",
            implementation_skill,
        )
        self.assertIn(
            "without such a model designation, do not create additional delegation cost",
            implementation_skill,
        )
        for research_surface in (
            "implementation and integration surfaces",
            "pre-existing or concurrent changes",
            "required files, executables, dependencies, and focused-check availability",
            "scope, dependency, authority, or contract conflicts",
        ):
            self.assertIn(research_surface, implementation_skill)
        self.assertIn(
            "Its findings are advisory and do not bind the Implementation Subagent's internal design, exact file "
            "list, implementation sequence, or technical steps",
            implementation_skill,
        )
        self.assertIn("do not assign an AC or whole-Ticket verdict", implementation_skill)
        self.assertIn(
            "The Implementation Lead directly confirms the material current-project facts used for the assignment "
            "decision",
            implementation_skill,
        )
        self.assertIn(
            "Any further delegated research is limited to research models already designated by the user",
            implementation_skill,
        )
        self.assertIn(
            "only then invoke the user-designated `Implementation Subagent`",
            implementation_skill,
        )
        for role_only_research_bypass in (
            "models or roles",
            "model or role",
            "multiple research models or roles",
            "models or roles already designated",
        ):
            self.assertNotIn(role_only_research_bypass, implementation_skill_lower)

    def test_implementation_skill_gates_actual_product_handoff_before_verification(self) -> None:
        implementation_skill = " ".join(IMPLEMENTATION_SKILL.split())
        for required in (
            "concrete post-implementation actual-product handoff-check plan",
            "Ticket-created first executable",
            "current absence of that Ticket-owned artifact is not a feasibility failure",
            "unavailable focused-check capability",
            "pre-mutation blocker",
            "gross handoff-liveness",
            "Ticket-required nominal success class",
            "Ticket-unowned debug hook or seam",
            "leave residual causal uncertainty for Verification",
            "actual execution context and direct raw product-boundary result",
            "same-Ticket due-now implementation work",
            "classify it neither as verification-only work nor as a new feature or Ticket",
            "every materially distinct required route has current gross actual-product handoff-liveness evidence",
            "~/.iis/route-navigation/<ticket-key>.json",
            "publish_route_navigation",
            "read_primary_navigation_view",
            "read_lead_producer_provenance_view",
            "neither evidence of producer omission nor a verification blocker",
        ):
            self.assertIn(required, implementation_skill)

        ordered_contract = (
            "concrete post-implementation actual-product handoff-check plan",
            "After implementation, for each materially distinct route",
            "same-Ticket due-now implementation work",
            "Begin independent verification only after",
            "sole serialized handoff exception",
        )
        positions = [implementation_skill.index(text) for text in ordered_contract]
        self.assertEqual(positions, sorted(positions))

    def test_verification_roles_split_workflow_and_semantic_ownership(self) -> None:
        verification_skill = " ".join(VERIFICATION_SKILL.split())
        for required in (
            "same exact ready local Markdown Ticket",
            "user-facing workflow authority",
            "Primary Verifier is the sole product-verification semantic owner",
            "no fallback or direct product-verification path",
            "exactly one internal `Primary Verifier`",
            "Host Subagent Invocation Mechanism",
            "read_primary_navigation_view",
            "read_lead_producer_provenance_view",
            "publish_plan_envelope",
            "publish_user_approval",
            "read_final_outcome",
            "coverage_gate.py",
            "COVERAGE_GATE_UNSUPPORTED",
            "PRE_APPROVAL_COVERAGE_GATE_FAILURE",
            "Ask the user to explicitly approve that exact plan",
            "maximum-three-cycle lineage",
            "must not rewrite evidence, AC mappings, verdicts",
        ):
            self.assertIn(required, verification_skill)

        for required in (
            "sole product-verification semantic owner",
            "exactly four parts",
            "Independently decompose every Markdown AC",
            "Primary alone interprets and adopts Runner",
            "Primary alone designs Scenario Records",
            "Execute only current approved `READY` Scenario revisions",
            "Derive exactly one ordered result row per Markdown AC",
            "Remediation Agent owns read-only causal proposal",
            "publish_final_outcome",
            "Lead may accept or reject the package only",
        ):
            self.assertIn(required, PRIMARY_SKILL)

        self.assertIn(
            "After structural validation, invoke one Coverage Challenger in a fresh isolated context",
            verification_skill,
        )
        self.assertIn("Lead must not self-sign or edit the model", verification_skill)
        approval_request = "Ask the user to explicitly approve that exact plan."
        self.assertEqual(VERIFICATION_SKILL.count(approval_request), 1)
        self.assertNotIn("Ask the user to approve that exact plan.", VERIFICATION_SKILL)
        self.assertNotIn(
            "Ask the user to explicitly approve the disclosed scenario plan.",
            VERIFICATION_SKILL,
        )

        self.assertNotIn("LEAD_FAILURE", VERIFICATION_SKILL)

    def test_behavior_hierarchy_change_invalidates_prior_coverage_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            project_root = Path(raw_root).resolve()
            planning = project_root / "docs/planning"
            behavior_dir = planning / "behavior/contexts"
            ticket_dir = planning / "tickets"
            behavior_dir.mkdir(parents=True)
            ticket_dir.mkdir()

            behavior_path = behavior_dir / "checkout.md"
            spec_path = planning / "SPEC.md"
            ticket_path = ticket_dir / "TICKET-001.md"
            model_path = project_root / "coverage-model.json"
            behavior_relative = "docs/planning/behavior/contexts/checkout.md"

            behavior_path.write_text(
                "# Checkout Behavior\n"
                "Status: approved\n\n"
                "## Rules\n\n"
                "- Trigger A\n"
                "  - Result X\n"
                "- Trigger B\n"
                "  - Result Y\n",
                encoding="utf-8",
            )
            spec_path.write_text(
                "# Checkout Spec\n"
                "Status: approved\n\n"
                "## Desired Outcome\n\nCheckout is observable.\n\n"
                "## Requirements\n\nPreserve behavior.\n\n"
                "## Non-Goals\n\nNone.\n\n"
                "## Implementation Constraints\n\nNone.\n\n"
                "## Verification Expectations\n\nObserve the checkout boundary.\n\n"
                "## Behavior Authorities\n\n"
                f"- {behavior_relative} | Scope: checkout\n\n"
                "## UI / UX\n\nNot applicable\n\n"
                "## Open Questions\n\nNone\n",
                encoding="utf-8",
            )
            ticket_path.write_text(
                "# TICKET-001\n"
                "Status: ready\n"
                "Parent-Spec: docs/planning/SPEC.md\n"
                f"Project-Root: {project_root}\n"
                "UI: no\n\n"
                "## Acceptance Criteria\n\n"
                "- Checkout produces the adopted result.\n\n"
                "## Verification\n\n"
                "- Trigger checkout and observe the result.\n\n"
                "## Behavior Authorities\n\n"
                f"- {behavior_relative} | Scope: checkout\n",
                encoding="utf-8",
            )
            model_path.write_text(
                json.dumps(
                    {
                        "units": [
                            {
                                "id": "U1",
                                "root_ids": ["AC:01", "V:01"],
                                "predicate": "Checkout produces the adopted result.",
                                "qualifier_binding_ids": ["Q1"],
                                "disposition": "PLANNED",
                            }
                        ],
                        "qualifier_bindings": [
                            {
                                "id": "Q1",
                                "source": behavior_relative,
                                "source_text": "- Trigger A - Result X",
                                "unit_ids": ["U1"],
                                "meaning": "Trigger A requires Result X.",
                            }
                        ],
                        "coverage_edges": [
                            {
                                "id": "E1",
                                "unit_id": "U1",
                                "scenario_id": "VS1",
                                "scenario_revision": "r1",
                                "trigger": "Trigger A",
                                "product_boundary": "Checkout boundary",
                                "expected_result": "Result X",
                                "forbidden_result": "Any other result",
                                "observation_readback": "Checkout result readback",
                                "identity_correlation": "Single checkout identity",
                                "decision_predicate": "Observed result is Result X",
                            }
                        ],
                        "scenarios": [
                            {
                                "id": "VS1",
                                "revision": "r1",
                                "procedure": ["Trigger A and read the checkout result."],
                                "readiness": "READY",
                                "readiness_record_ids": ["F1"],
                                "preparation_scope": "None",
                            }
                        ],
                        "partial": None,
                    }
                ),
                encoding="utf-8",
            )

            envelope = coverage_gate.build(ticket_path, model_path)
            root_checks = [
                {
                    "root_id": root["id"],
                    "checks": [
                        {
                            "predicate": "Checkout result is independently accounted.",
                            "unit_ids": ["U1"],
                            "edge_ids": ["E1"],
                        }
                    ],
                }
                for root in envelope["canonical"]["roots"]
            ]
            receipt = coverage_gate.check_attestation(
                envelope,
                {
                    "schema": "coverage-challenge/v1",
                    "result": "PASS",
                    "challenge_fp": envelope["fingerprints"]["challenge_fp"],
                    "roots": root_checks,
                    "qualifier_binding_ids_checked": ["Q1"],
                },
                None,
            )
            self.assertEqual(coverage_gate.approve(envelope, receipt)["mode"], "TOTAL")

            behavior_path.write_text(
                "# Checkout Behavior\n"
                "Status: approved\n\n"
                "## Rules\n\n"
                "- Trigger A\n"
                "  - Result X\n"
                "  - Trigger B\n"
                "    - Result Y\n",
                encoding="utf-8",
            )
            rebuilt = coverage_gate.build(ticket_path, model_path)

            self.assertNotEqual(
                rebuilt["fingerprints"]["challenge_fp"],
                envelope["fingerprints"]["challenge_fp"],
            )
            with self.assertRaises(coverage_gate.GateError):
                coverage_gate.approve(rebuilt, receipt)

    def test_verification_skill_removes_retired_verification_role_names(self) -> None:
        combined = VERIFICATION_SKILL + PRIMARY_SKILL
        self.assertNotIn("Readiness Research Agent", combined)
        self.assertNotIn("Fresh Verification Lead", combined)
        self.assertNotIn("Fresh Verification Subagent", combined)

    def test_active_skills_exclude_retired_mechanism_terms(self) -> None:
        combined = (
            IMPLEMENTATION_SKILL + "\n" + VERIFICATION_SKILL + "\n" + PRIMARY_SKILL
        ).lower()
        for term in (
            "implementation verification module",
            "module.implement",
            "module.verify",
            "module.inspect",
            "opencode worker",
            "opencode verifier",
            "terraworker",
            "fresh luna",
            "implementation-handoff",
            "verification-result",
            "verification-run",
            "workflow-store",
            "baseline capsule",
        ):
            self.assertNotIn(term, combined)

    def test_bounded_transport_excludes_rejected_architecture(self) -> None:
        transport = (ROOT / "iis_ephemeral_transport.py").read_text(encoding="utf-8")
        public_match = re.search(r"(?ms)^__all__ = \((.*?)^\)", transport)
        self.assertIsNotNone(public_match)
        public = public_match.group(1).lower()
        for forbidden in (
            "active",
            "latest",
            "predecessor",
            "history",
            "inspect",
            "list",
            "takeover",
            "retry",
            "replay",
            "verification-result",
            "workflow-store",
        ):
            self.assertNotIn(forbidden, public)
        for forbidden_path in ("active.json", "outcome-", "evidence/"):
            self.assertNotIn(forbidden_path, transport)
        for retired_path in (
            ROOT / "verification-lead" / "tools" / "verification-run",
            ROOT / "implementation-lead" / "tools" / "workflow-store",
        ):
            self.assertFalse(retired_path.exists())


if __name__ == "__main__":
    unittest.main()
