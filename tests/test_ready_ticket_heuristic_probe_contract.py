from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "companion-skills" / "ready-ticket-heuristic-probe"


class ReadyTicketHeuristicProbeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (PROBE / "SKILL.md").read_text(encoding="utf-8")
        self.workflow = (PROBE / "references" / "probe.md").read_text(encoding="utf-8")
        self.openai = (PROBE / "agents" / "openai.yaml").read_text(encoding="utf-8")

    def test_skill_surface_is_minimal_and_discoverable(self) -> None:
        self.assertTrue(PROBE.is_dir())
        self.assertEqual(
            {path.name for path in PROBE.iterdir()},
            {"SKILL.md", "agents", "references"},
        )
        self.assertEqual(
            {path.name for path in (PROBE / "agents").iterdir()},
            {"openai.yaml"},
        )
        self.assertEqual(
            {path.name for path in (PROBE / "references").iterdir()},
            {"probe.md"},
        )
        self.assertIn("name: ready-ticket-heuristic-probe", self.skill)
        self.assertIn("$ready-ticket-heuristic-probe", self.openai)

    def test_probe_uses_current_ticket_authority_and_existing_methods(self) -> None:
        for token in (
            "validate_ticket.py",
            "exact `VALID`",
            "production-heuristic-probing",
            "purpose-first-review",
            "Parent Spec",
            "Behavior/UI",
            "Status: ready",
        ):
            self.assertIn(token, self.skill + self.workflow)

        self.assertIn("Implementation reports, test output, logs", self.workflow)
        self.assertIn("navigation/support", self.workflow)
        self.assertIn("do not create product authority", self.workflow)

    def test_execution_is_direct_first_and_subagent_is_explicit_only(self) -> None:
        self.assertIn("Top-level execution defaults to `DIRECT`", self.skill)
        self.assertIn(
            "only when the current user explicitly selects SUBAGENT for this exact probe stage",
            self.skill,
        )
        self.assertIn("Never auto-switch or fall back", self.skill)
        self.assertIn("SUBAGENT CAPABILITY UNAVAILABLE", self.skill)
        self.assertIn("Do not silently run DIRECT instead", self.skill)
        self.assertIn("Delegated Probe Worker: yes", self.skill)
        self.assertIn("does not delegate again", self.workflow)

    def test_frontier_is_ticket_derived_not_generic_chaos(self) -> None:
        combined = self.skill + self.workflow
        for token in (
            "Review every authored Verification flow",
            "ADMIT_LANE",
            "NO_DISTINCT_HEURISTIC_LANE",
            "exact current product-contract anchor",
            "concrete plausible failure or false-attribution path",
            "material observable/canonical consequence",
            "generic fuzzing or chaos testing",
        ):
            self.assertIn(token, combined)

        self.assertIn("Do not split one material path merely to create more workers", self.workflow)
        self.assertIn("no runtime perturbation or worker dispatch is required", self.workflow)

    def test_subagent_topology_is_dynamic_and_parallel_only_when_isolated(self) -> None:
        combined = self.skill + self.workflow
        self.assertIn("dynamic worker set", self.skill)
        self.assertIn("no fixed worker count or fixed role roster", self.skill)
        self.assertIn("There is no minimum, maximum-by-contract", self.workflow)
        self.assertIn("Parallelize only when each lane has an isolated read/effect/cleanup surface", self.workflow)
        self.assertIn("Serialize when lanes share or can interfere", self.workflow)
        self.assertIn("same mutable database record or canonical file", self.workflow)
        self.assertIn("scheduler, queue, lease system or persistent worker registry", self.workflow)

        for retired_role in (
            "CONTRACT_INTERPRETER",
            "ORACLE_CHALLENGER",
            "EVIDENCE_ARCHITECT",
            "SEMANTIC_MATERIALITY_REVIEWER",
        ):
            self.assertNotIn(retired_role, combined)

    def test_probe_is_exploration_not_verdict_or_remediation_authority(self) -> None:
        self.assertIn("exploration authority", self.skill)
        self.assertIn("NOT ADJUDICATED BY THIS SKILL", self.skill)
        self.assertIn("A separate verifier decides", self.workflow)
        self.assertIn("do not automatically remediate implementation", self.workflow.lower())
        self.assertNotIn("Ticket Progression:", self.skill + self.workflow)

        terminal = self.workflow.split("## 10. Completion and final result", 1)[1]
        self.assertRegex(
            terminal,
            re.compile(r"Probe Completion: COMPLETE \| PARTIAL \| BLOCKED"),
        )
        self.assertIn("Do not use `PROBE_CLEAR`, `PASS`, `FAIL`", terminal)

    def test_complete_does_not_mean_no_findings_or_verification_pass(self) -> None:
        combined = self.skill + self.workflow
        self.assertIn("A finding does not make the probe itself fail", self.workflow)
        self.assertIn("`COMPLETE` with one or more findings is normal", self.workflow)
        self.assertIn("does **not** mean the Ticket passes verification", self.skill)
        self.assertIn("Material Findings: None | <findings>", self.skill)

    def test_target_drift_and_mutation_ambiguity_are_bounded(self) -> None:
        self.assertIn("Authority Snapshot", self.skill)
        self.assertIn("Authority Snapshot", self.workflow)
        self.assertIn("source/config/build/artifact/runtime checkpoint", self.workflow)
        self.assertIn("invalidate supportive evidence", self.workflow)
        self.assertIn("does not prove the action happened or did not happen", self.workflow)
        self.assertIn("Do not immediately repeat it", self.workflow)
        self.assertIn("access-control bypass", self.workflow)
        self.assertIn("rate/protection bypass", self.workflow)


if __name__ == "__main__":
    unittest.main()
