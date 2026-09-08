---
name: ready-ticket-implement
description: "Implement one existing IIS Ready Ticket and perform implementer self-check. Use for exact Ready Ticket delivery. Top-level execution defaults to SUBAGENT with one checkpointed implementation worker; use DIRECT only when the current user explicitly selects it for this stage. This skill never performs or adjudicates the separate verification authority."
---

# Ready Ticket Implement

## 목적과 권위

이 스킬은 IIS Planning이 만든 하나의 Ready Ticket을 그 Ticket이 승인한 제품 자체에 구현한다. IIS Planning을 재개하거나 Ticket 의미를 다시 계획하지 않는다.

구현 worker는 구현과 구현자 self-check를 소유한다. 준비 reviewer의 독립 착수 판단과 final verifier의 탐색·AC verdict·whole-Ticket verdict·terminal `done` 전이는 소유하지 않는다.

실제 작업 전에 [references/implement.md](references/implement.md)를 전부 읽는다.

## 입력

- Ticket: `<TICKET_PATH>`
- Project Root: `<PROJECT_ROOT>`
- 추가 사용자 지시: `<ADDITIONAL_USER_INSTRUCTIONS>`
- Plan Review: `<exact outside-Project-Root iis-plan-review/v1 path>`; 없거나 stale이면 source mutation/assignment 전에 [ready-ticket-plan](../ready-ticket-plan/SKILL.md)으로 필요한 준비부터 수행/요청한다. 실제 독립 reviewer의 current ADMIT 없이 착수하지 않는다.

## 실행 topology

Top-level 기본 실행 모드는 `SUBAGENT`다. 현재 사용자가 이 exact implementation stage에 `DIRECT`를 명시한 경우에만 `DIRECT`를 사용한다. 기본 모드 사용을 위한 별도 SUBAGENT 승인을 요구하지 않는다.

Exact assignment, 단일 owner lane, checkpoint continuation, capability failure, no-fallback 규칙의 canonical 상세는 [references/implement.md#2-subagent-first-execution-topology](references/implement.md#2-subagent-first-execution-topology)에 있다. 실제 작업 전에 그 계약을 적용한다.
`SUBAGENT CAPABILITY UNAVAILABLE`은 기존 [Non-continuation provenance](references/implement.md#non-continuation-provenance) schema로 반환한다.

이 entry contract는 implementation worker가 구현과 self-check만 소유하고 독립 준비 검토나 final verification authority를 흡수하지 않는다는 경계를 유지한다.

## Ready Ticket 상태 게이트

- 시작 정상 상태는 exact `ready`다.
- `done`이면 재구현하지 않는다.
- `draft` 또는 `blocked`이면 구현을 시작하지 않는다.
- 이 스킬은 Ticket status를 `done`으로 바꾸지 않는다. 정상 구현 입력인 `ready`는 구현 완료 후에도 그대로 유지한다.

## Ready runtime guard

Skill/reference 조회와 준비 artifact 작성만으로 실행을 arm하거나 만들지 않는다. 실제 current review가 있는 exact Ticket의 명시적 begin/assignment가 경계다.

- `DIRECT`: exact Ticket/Project Root와 `plan_review_path`로 `ready_guard begin_direct`를 완료한다.
- `SUBAGENT`: Outer Main이 같은 입력으로 `ready_guard assign_subagent`를 완료한 뒤 한 child를 할당하고, 지정 worker가 `assignment_id`와 같은 review로 `begin_delegated`를 완료한다. 공통 검사는 현재 bytes를 다시 확인하며 성공 시 `ACTIVE`다.
- runtime은 pinned canonical validator와 exact Ticket/Parent Spec/Behavior/UI authority, 현재 plan/review를 직접 bind한다. 누락은 `PLAN_REVIEW_REQUIRED`, stale은 `PLAN_REVIEW_STALE`, 미허가는 `PLAN_NOT_ADMITTED`다. 대화의 통과나 worker 합성 JSON으로 대신하지 않는다.
- exact owner, Project Root/보호된 authority/plan/review/output 경계와 active effect를 유지한다. 일반 read ledger, inventory quota, 일률 retry latch 또는 read 한 번으로 self-check를 증명하는 gate는 없다.
- command는 지원된 structured `ready_argv`, ephemeral service는 host-native `hub`를 사용한다. 서비스 생성/timeout/cancel receipt가 실제 정착이나 외부 effect 종료를 증명하지 않는다.
- terminal 전에 owned activity/service/effect를 실제로 닫고 `complete` 또는 `block`을 호출한다. 불확실한 효과는 `EFFECT_UNCERTAIN`과 점유를 보존하며 file hash 불변만으로 미적용 처리하지 않는다.

## 제품 의미 해석

구현 시작 전 한 문장으로 `이번 Ticket이 실제 제품에 추가하거나 변경하는 observable product outcome`을 고정한다. 제품 의미는 다음 authority에 계속 속한다.

1. 현재의 명시적 사용자 지시
2. Ticket 전체
3. Parent Spec
4. Behavior Authorities
5. 승인된 Design/UI Authority
6. Implementation Constraints와 References
7. 현재 repository/runtime의 직접 관찰 사실

Ticket은 이번 구현 경계, Parent Spec은 상위 결과, Behavior Authority는 identity·ownership·ordering·lifecycle 의미, Design/UI Authority는 사용자-visible 구조와 상호작용을 소유한다. References와 repository/runtime는 evidence/context이지 새 제품 권위가 아니다.

구현 편의, 기존 구조, 최소 변경 또는 test 편의를 이유로 승인된 결과를 축소·대체하지 않는다. Scope/Non-Goals 밖 제품 surface나 lifecycle guarantee를 만들지 않는다. 실질적 authority 충돌로 faithful direction을 확정할 수 없으면 `Completion: BLOCKED`로 닫는다.

## Verification-flow 해석과 self-check

각 authored Verification flow의 Parent outcome/AC/Behavior authority mapping, initial state, trigger, acceptance boundary, expected observable result, authoritative readback, decision boundary, disposition, authored independent-verification requirement, acceptance surface, external condition과 적용되는 ordering/interruption/persistence/external-effect/UI 경계를 그대로 사용한다.

Verification flow를 임의의 1:1 파일 작업으로 바꾸지 않는다. 구현 change와 self-check evidence를 각 flow에 연결하고, acceptance boundary와 authoritative readback으로 current product 결과를 확인한다. Authored independent-verification requirement가 있으면 원문 의미와 관련 implementation/self-check evidence를 final handoff에 보존하되 충족 여부는 판정하지 않는다.

## Checkpoint와 종료

current ADMIT 후 정상 첫 source 변경과 무변경 재개/교체에는 PRE_ACTION 재심사가 없다. worker는 load-bearing anchor/search universe/runtime 전제와 current user/Scope를 첫 의존 변경 전에 확인하며, 검토된 조건부 첫 작업의 지지/반증/불충분 분기를 따른다.

구현 방향, authority 해석, change surface 또는 evidence 전략이 material하게 바뀌는 경우에만 `IMPLEMENTATION TURN REPORT`를 `MATERIAL_TURN` checkpoint로 반환한다. 정상 진행, 일시적 test failure, 스타일 또는 단순 리팩터링은 periodic progress checkpoint 사유가 아니다.

중요 owner/interface/persistence/readback/원인 변경은 영향 Planner → Heuristic → independent review로 반환한다. `checkpoint`의 `kind: MATERIAL_TURN`과 `release_checkpoint`를 사용하며, plan drift 해제에는 새 `plan_review_path`의 공통 검사가 필요하다. Parent CONTINUE만으로 우회하지 않는다. DIRECT owner도 currentness와 pause fence를 준수한다. `PAUSED`에서는 안전한 read/분석만 허용하며 mutation은 금지한다.

`IMPLEMENT` 완료에는 Ticket Scope/Non-Goals 보존, 모든 authored Verification-flow obligation에 연결된 current self-check evidence, unresolved authority conflict/material blocker 부재, authored independent-verification requirement evidence 보존, decision-critical source/diff/artifact/command/runtime behavior의 직접 확인이 필요하다.

`Completion: COMPLETE`여도 exact Ticket의 `Status: ready`는 유지한다. actual implementation target/checkpoint와 current self-check evidence를 final verifier의 navigation handoff로 보존한다. 이후 verification 또는 IIS planning continuation을 자동 실행하지 않는다.

`Completion: BLOCKED | PARTIAL`이 admission, authority/readback, target currentness, 또는 checkpoint `STOP` 때문에 현재 구현 owner가 계속할 수 없음을 뜻할 때는 [references/implement.md](references/implement.md)의 **Non-continuation provenance**를 terminal caller-facing report에 포함한다. 정상 `Completion: COMPLETE`에는 이 설명 블록을 추가하지 않는다.
