from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIRECT = ROOT / "companion-skills" / "ready-ticket-verify"
ENSEMBLE = ROOT / "companion-skills" / "ready-ticket-verify-ensemble"
ADAPTIVE = ROOT / "iis-adaptive-planning"


class ReadyTicketVerificationModeTests(unittest.TestCase):
    def test_two_explicitly_distinct_verification_surfaces_exist(self) -> None:
        self.assertTrue((DIRECT / "SKILL.md").is_file())
        self.assertTrue((ENSEMBLE / "SKILL.md").is_file())
        self.assertEqual(
            {path.name for path in (ENSEMBLE / "references").iterdir()},
            {"orchestration.md", "role-contracts.md"},
        )
        self.assertTrue((ENSEMBLE / "agents" / "openai.yaml").is_file())

        direct = (DIRECT / "SKILL.md").read_text(encoding="utf-8")
        ensemble = (ENSEMBLE / "SKILL.md").read_text(encoding="utf-8")
        metadata = (ENSEMBLE / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("Execution mode is `DIRECT` only", direct)
        self.assertIn("This skill is explicit-only", ensemble)
        self.assertIn("never infer this mode from model capability", ensemble)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("$ready-ticket-verify-ensemble", metadata)

    def test_ensemble_keeps_main_as_sole_verifier(self) -> None:
        skill = (ENSEMBLE / "SKILL.md").read_text(encoding="utf-8")
        roles = (ENSEMBLE / "references" / "role-contracts.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("The current Main is the sole verifier", skill)
        self.assertIn("No child role issues `SATISFIED`, `CONTRADICTED`", skill)
        self.assertIn("Workers never edit Ticket status", skill)
        self.assertIn("Flow/AC/Ticket verdict | None | None", roles)
        self.assertIn("`ready -> done` | None | None", roles)
        self.assertIn("Runner is not a fifth analyst and not a verifier", roles)

    def test_fixed_four_analysts_and_one_runner_are_complete(self) -> None:
        skill = (ENSEMBLE / "SKILL.md").read_text(encoding="utf-8")
        roles = (ENSEMBLE / "references" / "role-contracts.md").read_text(
            encoding="utf-8"
        )

        role_names = (
            "CONTRACT_INTERPRETER",
            "ORACLE_CHALLENGER",
            "EVIDENCE_ARCHITECT",
            "SEMANTIC_MATERIALITY_REVIEWER",
            "FLOW_RUNNER",
        )
        for role in role_names:
            self.assertIn(role, skill)
            self.assertIn(role, roles)

        self.assertIn("Use all four analyst roles for every ensemble verification", skill)
        self.assertIn("one runner alone performs product/runtime actions", skill)
        self.assertIn("Assign exactly one `FLOW_RUNNER`", (
            ENSEMBLE / "references" / "orchestration.md"
        ).read_text(encoding="utf-8"))

    def test_parallelizes_only_independent_read_only_reasoning(self) -> None:
        skill = (ENSEMBLE / "SKILL.md").read_text(encoding="utf-8")
        orchestration = (ENSEMBLE / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("at least two independent child contexts", skill)
        self.assertIn("four concurrent analyst contexts preferred", skill)
        self.assertIn("run two roles and then the other two", skill)
        self.assertIn("without disclosing first-batch conclusions", skill)
        self.assertIn("Parallelize only read-only work", skill)
        self.assertIn("Serialize target binding", skill)
        self.assertIn("Do not use one continuing context for several roles", orchestration)
        self.assertIn("No analyst executes the trigger", orchestration)

    def test_role_design_targets_contract_to_proof_and_evidence_to_meaning(self) -> None:
        orchestration = (ENSEMBLE / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )
        roles = (ENSEMBLE / "references" / "role-contracts.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("approved contract -> material proof obligations", orchestration)
        self.assertIn("raw evidence -> supported product meaning", orchestration)
        self.assertIn("contract -> proof", roles)
        self.assertIn("Could this exact evidence exist while the approved claim is still materially false?", roles)
        self.assertIn("bounded active-surface universe", roles)
        self.assertIn("causal reasoning is connected to source evidence", roles)
        self.assertIn("ALLOWED VARIATION", roles)

    def test_ensemble_uses_objection_closure_not_voting(self) -> None:
        skill = (ENSEMBLE / "SKILL.md").read_text(encoding="utf-8")
        orchestration = (ENSEMBLE / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Do not vote, average confidence or count supporting workers", skill)
        self.assertIn("Other workers' disagreement, confidence, majority or silence is not closure", orchestration)
        self.assertIn("Allow at most one targeted rebuttal round per objection", orchestration)
        self.assertIn("Exact contract anchor:", orchestration)
        self.assertIn("concrete plausible state", orchestration)
        self.assertIn("material impact", orchestration)
        self.assertIn("Do not manufacture objections", orchestration)

    def test_target_identity_and_error_boundaries_fail_closed(self) -> None:
        orchestration = (ENSEMBLE / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )
        roles = (ENSEMBLE / "references" / "role-contracts.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("A successful report from another target is not partial evidence", orchestration)
        self.assertIn("Do not immediately re-dispatch the same runner action", orchestration)
        self.assertIn("same exact read-only assignment", orchestration)
        self.assertIn("up to three times", orchestration)
        self.assertIn("expired/unknown child session or workspace identity", orchestration)
        self.assertIn("EXECUTION STATE UNKNOWN", roles)
        self.assertIn("do not repeat; report unknown execution state", roles)

    def test_direct_and_ensemble_share_terminal_meaning(self) -> None:
        direct = (DIRECT / "references" / "verify.md").read_text(encoding="utf-8")
        skill = (ENSEMBLE / "SKILL.md").read_text(encoding="utf-8")
        orchestration = (ENSEMBLE / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )

        shared_tokens = (
            "SATISFIED | CONTRADICTED | INCONCLUSIVE",
            "PASS | FAIL | INCONCLUSIVE",
            "VERIFIED | FAILED | INCONCLUSIVE",
            "Ticket Progression: COMPLETED | NOT APPLICABLE | FAILED",
        )
        for token in shared_tokens:
            self.assertIn(token, direct)
            self.assertTrue(token in skill or token in orchestration, token)

        self.assertIn("guarded `ready -> done`", skill)
        self.assertIn("Do not automatically remediate", skill)
        self.assertIn("no automatic remediation", orchestration)

    def test_ensemble_does_not_restore_retired_auditor_topology(self) -> None:
        payload = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                ENSEMBLE / "SKILL.md",
                ENSEMBLE / "references" / "orchestration.md",
                ENSEMBLE / "references" / "role-contracts.md",
                ENSEMBLE / "agents" / "openai.yaml",
            )
        )

        for forbidden in (
            "AC Runtime Auditor",
            "Auditor Count",
            "ac-runtime-auditors.md",
            "concurrent-auditors.md",
        ):
            self.assertNotIn(forbidden, payload)

        self.assertIn("do not split final AC ownership across workers", (
            ENSEMBLE / "SKILL.md"
        ).read_text(encoding="utf-8"))
        self.assertIn("one `FLOW_RUNNER`", (
            ENSEMBLE / "references" / "orchestration.md"
        ).read_text(encoding="utf-8"))

    def test_adaptive_uses_explicit_ensemble_selection_without_fallback(self) -> None:
        skill = (ADAPTIVE / "SKILL.md").read_text(encoding="utf-8")
        continuation = (ADAPTIVE / "references" / "08-delivery-continuation.md").read_text(
            encoding="utf-8"
        )
        contract = (ADAPTIVE / "references" / "09-run-contract.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("explicit-only `ready-ticket-verify-ensemble`", skill)
        self.assertIn("use `ready-ticket-verify-ensemble` only when the current user explicitly selects", continuation)
        self.assertIn("otherwise use DIRECT-only `ready-ticket-verify`", continuation)
        self.assertIn("do not fall back from one verification mode to the other", continuation)
        self.assertIn("They are never both invoked for one verification lifecycle", continuation)
        self.assertIn("currently selected one-Ticket verifier", contract)


if __name__ == "__main__":
    unittest.main()
