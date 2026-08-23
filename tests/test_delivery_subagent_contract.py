from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENT = ROOT / "companion-skills" / "ready-ticket-implement"
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

    def test_implementation_is_subagent_first_with_explicit_direct_only(self) -> None:
        skill = (IMPLEMENT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        self.assertIn("Top-level 기본 실행 모드는 `SUBAGENT`", skill)
        self.assertIn("사용자가 현재 요청에서 명시한 경우에만", skill)
        self.assertIn("`Delegated Worker: yes`", skill)
        self.assertIn("다시 위임하지 않고", skill)
        self.assertIn("실패를 `DIRECT`로 자동 대체하지 않는다", skill)
        self.assertIn("정확히 한 명의 implementation worker", skill)
        self.assertIn("Top-level invocation에서 사용자가 `DIRECT`를 명시하지 않았으면", workflow)
        self.assertIn("한 명의 non-blocking implementation worker", workflow)

    def test_implementation_reports_are_early_non_blocking_and_event_driven(self) -> None:
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        handoff = workflow.index("IMPLEMENTATION HANDOFF REPORT")
        implementation = workflow.index("## 5. 구현")
        self.assertLess(handoff, implementation)
        self.assertIn("첫 source-file 변경 전에", workflow)
        self.assertIn("approval gate가 아니다", workflow)
        self.assertIn("acknowledgement나 approval을 기다리지 않고", workflow)
        self.assertIn("IMPLEMENTATION TURN REPORT", workflow)
        self.assertIn("초기 handoff의 방향을 material하게 바꾸는 경우에만", workflow)
        self.assertIn("정상 진행, 단순 tool activity", workflow)
        self.assertIn("live wait를 만들지 말고", workflow)

    def test_implementation_preserves_delivery_authority_boundaries(self) -> None:
        skill = (IMPLEMENT / "SKILL.md").read_text(encoding="utf-8")
        workflow = (IMPLEMENT / "references" / "implement.md").read_text(encoding="utf-8")

        self.assertIn("Separate verification authority", skill)
        self.assertIn("이 스킬은 Ticket status를 `done`으로 바꾸지 않는다", skill)
        self.assertIn("Status: ready", workflow)
        self.assertIn("Verification status: NOT ADJUDICATED BY THIS SKILL", workflow)
        self.assertIn("Completion: COMPLETE | BLOCKED | PARTIAL", workflow)

    def test_verification_is_direct_and_main_owns_verdict(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        self.assertIn("Execution mode is `DIRECT` only", skill)
        self.assertIn("The current Main is the sole verifier", skill)
        self.assertIn("does not delegate this verification authority", skill)
        self.assertIn("DIRECT VERIFIER REQUIRED", skill)
        self.assertNotIn("Top-level default execution mode is `SUBAGENT`", skill)
        self.assertIn("This skill is `DIRECT` only", workflow)
        self.assertIn("does not delegate verification", workflow)

    def test_verification_requires_semantic_contract_check_and_claim_sufficient_evidence(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        self.assertIn("semantically compare every AC and mapped Verification flow", skill)
        self.assertIn("## 3. Semantic contract check", workflow)
        self.assertIn("false-positive or false-negative", workflow)
        self.assertIn("Bounded active-surface universe", workflow)
        self.assertIn("Semantic and qualitative claims", workflow)
        self.assertIn("Process/history claims", workflow)
        self.assertIn("do not create a new run ledger", workflow)
        self.assertNotIn("ADEQUATE | INADEQUATE | UNRESOLVED", workflow)
        self.assertNotIn("Acceptance-contract adequacy gate", skill)

    def test_verification_scenario_report_and_material_turns_are_direct(self) -> None:
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        report = workflow.index("## 8. Scenario report")
        runtime = workflow.index("## 9. Evidence sufficiency and execution")
        self.assertLess(report, runtime)
        self.assertIn("Before the first product/runtime action", workflow)
        self.assertIn("informational, not an approval gate", workflow)
        self.assertIn("VERIFICATION TURN REPORT", workflow)
        self.assertIn("only when direct evidence creates a material change", workflow)
        self.assertIn("waiting in a live suspended state", workflow)

    def test_verification_preserves_full_adjudication_and_done_guard(self) -> None:
        skill = (VERIFY / "SKILL.md").read_text(encoding="utf-8")
        workflow = (VERIFY / "references" / "verify.md").read_text(encoding="utf-8")

        self.assertIn("every authored Verification flow", skill)
        self.assertIn("Independent verification required", workflow)
        self.assertIn("all ACs PASS          -> VERIFIED", workflow)
        self.assertIn("no unresolved material semantic-contract defect", skill)
        self.assertIn("Perform one guarded targeted replacement", workflow)
        self.assertIn("Ticket Progression: COMPLETED | NOT APPLICABLE | FAILED", workflow)
        self.assertIn("Do not automatically edit source", workflow)

    def test_adaptive_routes_implementation_and_direct_verification(self) -> None:
        continuation = ADAPTIVE_CONTINUATION.read_text(encoding="utf-8")

        self.assertIn("`ready-ticket-implement` retains its normal `SUBAGENT` default", continuation)
        self.assertIn("`ready-ticket-verify` owns one exact Ready Ticket fresh verification", continuation)
        self.assertIn("For verification, use DIRECT-only `ready-ticket-verify`", continuation)
        self.assertIn("without issuing a second verdict", continuation)
        self.assertIn("Do not pass `Delegated Worker: yes` from Adaptive", continuation)
        self.assertIn("Select only a currently admissible Ticket", continuation)

    def test_openai_metadata_matches_current_delivery_contracts(self) -> None:
        implement_yaml = (IMPLEMENT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        verify_yaml = (VERIFY / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("$ready-ticket-implement", implement_yaml)
        self.assertIn("one implementation worker", implement_yaml)
        self.assertIn("$ready-ticket-verify", verify_yaml)
        self.assertIn("directly verify", verify_yaml)
        self.assertIn("semantically check", verify_yaml)


if __name__ == "__main__":
    unittest.main()
