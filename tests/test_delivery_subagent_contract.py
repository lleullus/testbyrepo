from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENT = ROOT / "companion-skills" / "ready-ticket-implement"
PROBE = ROOT / "companion-skills" / "ready-ticket-heuristic-probe"
VERIFY = ROOT / "companion-skills" / "ready-ticket-verify"
ADAPTIVE_CONTINUATION = (
    ROOT / "iis-adaptive-planning" / "references" / "08-delivery-continuation.md"
)


class DeliverySubagentContractTests(unittest.TestCase):
    def test_retired_observer_contracts_are_removed(self) -> None:
        self.assertFalse((IMPLEMENT / "references" / "concurrent-auditors.md").exists())
        self.assertFalse((VERIFY / "references" / "ac-runtime-auditors.md").exists())
        self.assertEqual(
            {path.name for path in (IMPLEMENT / "references").iterdir()},
            {"implement.md"},
        )
        self.assertEqual(
            {path.name for path in (VERIFY / "references").iterdir()},
            {"verify.md"},
        )

    def test_delivery_surfaces_have_no_retired_observer_vocabulary(self) -> None:
        paths = (
            IMPLEMENT / "SKILL.md",
            IMPLEMENT / "references" / "implement.md",
            IMPLEMENT / "agents" / "openai.yaml",
            VERIFY / "SKILL.md",
            VERIFY / "references" / "verify.md",
            VERIFY / "agents" / "openai.yaml",
            ADAPTIVE_CONTINUATION,
        )
        forbidden = (
            "auditor",
            "Auditor",
            "AC Runtime Auditor",
            "Auditor Count",
            "동시감사",
            "감사자",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{token!r} remained in {path}")

    def test_implementation_is_direct_first_with_explicit_subagent_only(self) -> None:
        skill = (IMPLEMENT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        self.assertIn("Top-level 기본 실행 모드는 `DIRECT`", skill)
        self.assertIn("현재 사용자가 이 exact implementation stage에 명시한 경우에만", skill)
        self.assertIn("references/implement.md#2-direct-first-execution-topology", skill)
        self.assertNotIn("`Delegated Worker: yes`", skill)
        self.assertNotIn("실패를 `DIRECT`로 자동 대체하지 않는다", skill)
        self.assertIn("Top-level invocation은 `DIRECT`가 기본", workflow)
        self.assertIn("`Delegated Worker: yes`", workflow)
        self.assertIn("한 명의 implementation worker", workflow)
        self.assertIn("checkpoint return/continuation", workflow)
        self.assertIn("자동 전환이나 실패 후 fallback은 없다", workflow)

    def test_implementation_reports_are_checkpointed_and_event_driven(self) -> None:
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        handoff = workflow.index("IMPLEMENTATION HANDOFF REPORT")
        implementation = workflow.index("## 5. 구현")
        self.assertLess(handoff, implementation)
        self.assertIn("첫 source-file 변경 전에", workflow)
        self.assertIn("Checkpoint: PRE_ACTION", workflow)
        self.assertIn("Protected next phase: FIRST_SOURCE_FILE_CHANGE", workflow)
        self.assertIn("Parent decision 전에는 source 파일을 변경하지 않는다", workflow)
        self.assertIn("logical phase boundary", workflow)
        self.assertIn("required live-wait primitive, direct-user approval gate 또는 durable workflow state가 아니다", workflow)
        self.assertIn("CONTINUE", workflow)
        self.assertIn("STEER", workflow)
        self.assertIn("STOP", workflow)
        self.assertIn("IMPLEMENTATION TURN REPORT", workflow)
        self.assertIn("초기 handoff의 방향을 material하게 바꾸는 경우에만", workflow)
        self.assertIn("정상 진행, 단순 tool activity", workflow)
        self.assertIn("Work permitted before continuation: NONE", workflow)
        self.assertIn("periodic progress checkpoint로 사용하지 않는다", workflow)
        self.assertIn("Checkpoint: NOT_APPLICABLE", workflow)

    def test_implementation_resyncs_non_discretionarily_on_authority_or_readback_drift(self) -> None:
        skill = (IMPLEMENT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        self.assertIn("worker의 materiality threshold를 적용하지 않는다", skill)
        self.assertIn("### 비재량 재동기화", workflow)
        self.assertIn("exact authority artifact 자체에 scoped되고 content-sensitive", workflow)
        self.assertIn("canonical path + file/content SHA", workflow)
        self.assertIn("repository-wide working-tree 변화는 authority drift로 취급하지 않으며", workflow)
        self.assertIn("current `Parent-released anchor`", workflow)
        self.assertIn("Parent가 `CONTINUE`하면", workflow)
        self.assertIn("invocation-local 최신 `Parent-released anchor`", workflow)
        self.assertIn("currentness 비교는 최신 `Parent-released anchor`", workflow)
        self.assertIn("unavailable 또는 non-attributable", workflow)
        self.assertIn("다른 readback으로 substitution", workflow)
        self.assertIn("기존 `MATERIAL_TURN` checkpoint", workflow)
        self.assertIn("`Completion: BLOCKED`", workflow)
        self.assertIn("`SUBAGENT`에서는", workflow)
        self.assertIn("최신 `Parent-released anchor`와 대조", workflow)
        self.assertIn("`DIRECT`에서는 Parent checkpoint나 `Parent-released anchor`를 만들지 않는다", workflow)
        self.assertIn("현재 Main이 exact Ticket과 적용되는 canonical Parent Spec/Behavior/UI Authority 및 authoritative readback을 직접 다시 결합", workflow)
        self.assertIn("runtime의 persistent state는 실행 guard 내부에만 존재", workflow)
        self.assertIn("runtime의 internal state machine/authority snapshot은 이 enforcement에만 쓰며", workflow)
        self.assertNotIn("PRE_COMPLETION", skill + workflow)

    def test_implementation_preserves_delivery_authority_boundaries(self) -> None:
        skill = (IMPLEMENT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        self.assertIn("Separate heuristic-probe authority", skill)
        self.assertIn("Separate verification authority", skill)
        self.assertIn("이 스킬은 Ticket status를 `done`으로 바꾸지 않는다", skill)
        self.assertIn("Status: ready", workflow)
        self.assertIn("Heuristic probe status: NOT RUN BY THIS SKILL", workflow)
        self.assertIn("Verification status: NOT ADJUDICATED BY THIS SKILL", workflow)
        self.assertIn("Heuristic-probe / verification evidence handoff", workflow)
        self.assertIn("Completion: COMPLETE | BLOCKED | PARTIAL", workflow)

    def test_verification_is_direct_first_with_explicit_checkpointed_subagent(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        self.assertIn("Execution defaults to `DIRECT`", skill)
        self.assertIn("current user explicitly selects it for this exact verification stage", skill)
        self.assertIn("references/verify.md#1-direct-first-invocation", skill)
        self.assertNotIn("Delegated Verifier: yes", skill)
        self.assertNotIn("run parallel verifiers", skill)
        self.assertIn("references/verify.md#2-admission-and-current-authority", skill)
        self.assertIn("Execution defaults to `DIRECT`", workflow)
        self.assertIn("Delegated Verifier: yes", workflow)
        self.assertIn("Exactly one delegated verifier", workflow)
        self.assertIn("do not split ACs/flows", workflow)
        self.assertIn("verifier roster", workflow)
        self.assertIn("run parallel verifiers", workflow)
        self.assertIn("delegate again", workflow)
        self.assertIn("SUBAGENT CAPABILITY UNAVAILABLE", workflow)
        self.assertIn("never auto-fallback to `DIRECT`", workflow)

    def test_verification_requires_current_complete_heuristic_probe_gate(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        combined = skill + workflow
        self.assertIn("Heuristic Probe Result / Evidence", skill)
        self.assertIn("Probe Machine Binding", combined)
        self.assertIn("Probe Completion: COMPLETE", combined)
        self.assertIn("Authority Snapshot", combined)
        self.assertIn("ready_guard", combined)
        self.assertIn("begin_verify", combined)
        self.assertIn("ready_argv execute", combined)
        self.assertIn("TARGET_DRIFT", combined)
        self.assertIn("REQUIRED HEURISTIC PROBE RESULT MISSING", combined)
        self.assertIn("HEURISTIC PROBE GATE INCOMPLETE", combined)
        self.assertIn("HEURISTIC PROBE RESULT STALE", combined)
        self.assertIn("`Material Findings: None` is not", combined)
        self.assertIn("never satisfies an authored `Independent verification required: yes`", workflow)
        self.assertNotIn("first verification", combined)
        self.assertIn("normal delivery verification", combined)
        for disposition in (
            "REPRODUCED",
            "CURRENT_READBACK_CONFIRMED",
            "OUT_OF_SCOPE",
            "UNATTRIBUTABLE",
            "SUPERSEDED_BY_CURRENT_TARGET",
        ):
            self.assertIn(disposition, workflow)

    def test_adaptive_forwards_current_verifier_required_probe_handoffs_without_copying_runtime_mechanics(self) -> None:
        verify_skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        probe_skill = (PROBE / "SKILL.md").read_text(encoding="utf-8")
        continuation = ADAPTIVE_CONTINUATION.read_text(encoding="utf-8")
        artifact_contract = (
            ROOT / "iis-adaptive-planning" / "references" / "05-artifact-contract.md"
        ).read_text(encoding="utf-8")

        section = re.search(
            r"Required for normal delivery verification of `Status: ready`:\n\n(?P<body>(?:- .+\n)+)",
            verify_skill,
        )
        self.assertIsNotNone(section)
        required_handoffs = re.findall(r"^- ([^:]+):", section.group("body"), re.MULTILINE)
        self.assertGreaterEqual(len(required_handoffs), 1)
        for handoff in required_handoffs:
            self.assertIn(handoff, continuation)

        self.assertIn("Probe Machine Binding:", probe_skill)
        self.assertIn("Probe Machine Binding", artifact_contract)
        self.assertIn("canonical owner interface", continuation)
        self.assertIn("forward every current required handoff field", continuation)
        self.assertNotIn("ready_guard begin_verify", continuation)
        self.assertNotIn("ready_argv execute", continuation)

    def test_verification_requires_semantic_contract_check_and_claim_sufficient_evidence(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        self.assertIn("semantically compare every AC and mapped Verification flow", skill)
        self.assertIn("## 3. Semantic contract check", workflow)
        self.assertIn("false-positive or false-negative", workflow)
        self.assertIn("Nearest nonconforming state", workflow)
        self.assertIn("Discriminating observation", workflow)
        self.assertIn("Sensitivity activation", workflow)
        self.assertIn("Bounded active-surface universe", workflow)
        self.assertIn("Semantic and qualitative claims", workflow)
        self.assertIn("Process/history claims", workflow)
        self.assertIn("do not create a new run ledger", workflow)
        self.assertNotIn("ADEQUATE | INADEQUATE | UNRESOLVED", workflow)
        self.assertNotIn("Acceptance-contract adequacy gate", skill)

    def test_verification_scenario_report_and_material_turns_are_mode_specific(self) -> None:
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        report = workflow.index("## 8. Scenario report")
        runtime = workflow.index("## 9. Evidence sufficiency and execution")
        self.assertLess(report, runtime)
        self.assertIn("Before the first product/runtime action", workflow)
        self.assertIn("Checkpoint: NOT_APPLICABLE | PRE_RUNTIME", workflow)
        self.assertIn("In `DIRECT`, the report is informational and has no Parent continuation", workflow)
        self.assertIn("`PRE_RUNTIME` is mandatory", workflow)
        self.assertIn("FIRST_PRODUCT_OR_RUNTIME_ACTION", workflow)
        self.assertIn("VERIFICATION TURN REPORT", workflow)
        self.assertIn("only when direct evidence creates a material change", workflow)
        self.assertIn("Checkpoint: NOT_APPLICABLE | MATERIAL_TURN", workflow)
        self.assertIn("Work permitted before continuation: NONE when SUBAGENT", workflow)
        self.assertIn("not periodic progress", workflow)

    def test_verification_preserves_full_adjudication_and_done_guard(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        self.assertIn("every authored Verification flow", skill)
        self.assertIn("Independent verification required", workflow)
        self.assertIn("all ACs PASS          -> VERIFIED", workflow)
        self.assertIn("no unresolved material semantic-contract defect", skill)
        self.assertIn("Perform one guarded targeted replacement", workflow)
        self.assertIn("finalize_verification", workflow)
        self.assertIn("Ticket Progression: COMPLETED | NOT APPLICABLE | FAILED", workflow)
        self.assertIn("Do not automatically edit source", workflow)

    def test_verification_pre_progression_checkpoint_precedes_done_and_is_verified_only(self) -> None:
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        checkpoint = workflow.index("VERIFICATION PRE-PROGRESSION CHECKPOINT")
        guarded_write = workflow.index("Perform one guarded targeted replacement")
        self.assertLess(checkpoint, guarded_write)
        self.assertIn("Candidate whole-Ticket verdict: VERIFIED", workflow)
        self.assertIn("Checkpoint: PRE_PROGRESSION", workflow)
        self.assertIn("FINAL_VERIFIED_AND_GUARDED_READY_TO_DONE", workflow)
        self.assertIn("rechecks currentness and performs the existing guarded progression", workflow)
        self.assertIn("`FAILED` and `INCONCLUSIVE` candidates have no `PRE_PROGRESSION` checkpoint", workflow)
        self.assertIn("Parent does not rerun runtime verification or issue its own verdict", workflow)
        self.assertIn("Parent may use `STOP` at `PRE_PROGRESSION` only when", workflow)
        self.assertIn("emits the existing terminal `READY TICKET VERIFICATION RESULT`", workflow)
        self.assertIn("`Verification Verdict: INCONCLUSIVE`", workflow)
        self.assertIn("`Ticket Progression: NOT APPLICABLE`", workflow)
        self.assertIn("`Ticket status after verification: ready`", workflow)
        self.assertIn("it performs no `done` mutation", workflow)
        self.assertIn("Parent Main does not issue or substitute that verdict", workflow)

    def test_adaptive_routes_direct_first_delivery_without_auto_topology_switch(self) -> None:
        continuation = ADAPTIVE_CONTINUATION.read_text(encoding="utf-8")

        self.assertIn("Delivery defaults to `DIRECT`", continuation)
        self.assertIn("`ready-ticket-implement` uses `SUBAGENT` only when the current user explicitly selects SUBAGENT", continuation)
        self.assertIn("`ready-ticket-heuristic-probe` owns one exact Ready Ticket", continuation)
        self.assertIn("`ready-ticket-heuristic-probe` uses `SUBAGENT` only when the current user explicitly selects SUBAGENT", continuation)
        self.assertIn("`ready-ticket-verify` owns one exact Ready Ticket fresh verification", continuation)
        self.assertIn("`ready-ticket-verify` defaults to `DIRECT`", continuation)
        self.assertIn("uses `SUBAGENT` only when the current user explicitly selects SUBAGENT for that exact verification stage", continuation)
        self.assertIn("exactly one delegated verifier", continuation)
        self.assertIn("Outer Main does not issue a second verifier verdict", continuation)
        self.assertIn("PARENT CONTINUATION DECISION", continuation)
        self.assertIn("Decision: CONTINUE | STEER | STOP", continuation)
        self.assertIn("nonterminal invocation-local delivery message", continuation)
        self.assertIn("verification triage wait for the exact terminal owner result", continuation)
        self.assertIn("never falls back between topologies after a capability failure", continuation)
        self.assertIn("`Delegated Worker: yes`, `Delegated Probe Worker: yes`, or `Delegated Verifier: yes`", continuation)
        self.assertIn("Do not forward a checkpoint as a user approval prompt.", continuation)
        self.assertIn("Do not create a checkpoint ledger or persistent state.", continuation)
        self.assertIn("Select only a currently admissible Ticket", continuation)

        implementation = continuation.index("## Implementation handoff")
        probe = continuation.index("## Heuristic probe gate handoff")
        verification = continuation.index("## Verification terminal routing")
        self.assertLess(implementation, probe)
        self.assertLess(probe, verification)

    def test_openai_metadata_matches_current_delivery_contracts(self) -> None:
        implement_yaml = (IMPLEMENT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        probe_yaml = (PROBE / "agents" / "openai.yaml").read_text(encoding="utf-8")
        verify_yaml = (VERIFY / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("$ready-ticket-implement", implement_yaml)
        self.assertIn("directly implement", implement_yaml)
        self.assertIn("SUBAGENT only when I explicitly select it", implement_yaml)
        self.assertIn("$ready-ticket-heuristic-probe", probe_yaml)
        self.assertIn("run DIRECT by default", probe_yaml)
        self.assertIn("$ready-ticket-verify", verify_yaml)
        self.assertIn("default DIRECT mode", verify_yaml)
        self.assertIn("current COMPLETE ready-ticket heuristic-probe handoff", verify_yaml)
        self.assertIn("semantically check", verify_yaml)
        self.assertIn("explicitly select SUBAGENT", verify_yaml)
        self.assertIn("PRE_RUNTIME", verify_yaml)
        self.assertIn("PRE_PROGRESSION", verify_yaml)


if __name__ == "__main__":
    unittest.main()
