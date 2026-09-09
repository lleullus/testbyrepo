---
name: ready-ticket-implement
description: "Implement one existing IIS Ready Ticket and perform implementer self-check. Use for exact Ready Ticket delivery. Top-level execution defaults to SUBAGENT with one implementation worker; use DIRECT only when the current user explicitly selects it for this stage. The actual implementing actor must pass current plan admission before mutation and again before COMPLETE. This skill never performs or adjudicates the separate verification authority."
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

## Ready boundary admission과 host-native 실행

Skill/reference 조회와 준비 artifact 작성은 implementation admission이 아니다. 실제 implementing actor가 첫 source mutation 전에 exact Ticket/Project Root/`plan_review_path`로 `ready_contract check_plan_admission`을 직접 호출한다.

- `DIRECT`: 현재 Main이 actual implementing actor이며 첫 mutation 전 current `ADMIT`을 확인한다.
- `SUBAGENT`: Outer Main은 exact Ticket/Project Root/`plan_review_path`와 scope를 한 child에게 전달하고, 그 child가 actual implementing actor로서 같은 admission을 직접 확인한다. 별도 execution/assignment/session/reservation ID는 만들지 않는다.
- boundary check는 pinned canonical validator와 exact Ticket/Parent Spec/Behavior/UI authority, 현재 Plan/Review bytes를 다시 묶는다. 누락은 `PLAN_REVIEW_REQUIRED`, stale은 `PLAN_REVIEW_STALE`, 미허가는 `PLAN_NOT_ADMITTED`다. 대화의 통과나 worker 합성 JSON으로 대신하지 않는다.
- admission 뒤 read/search/edit/write/unit/integration/build/lint/CLI는 host-native tools를 그대로 사용한다. settled process의 nonzero exit는 그 command의 정상 실패 결과일 수 있으며 global execution lock으로 승격하지 않는다. 실패를 읽고 Plan 범위 안에서 수정한 뒤 재실행할 수 있다.
- actual non-idempotent/external effect가 timeout/abort/response loss로 정착 여부가 불명확하면 같은 effect를 blind replay하지 않는다. Ticket/Plan이 승인한 authoritative readback, cleanup, log/evidence 작성은 계속 수행할 수 있다. applied/not-applied가 확인되면 그 사실에 맞춰 계속하고, 확인 불가이면 그 effect에 의존하는 작업을 멈추고 `PARTIAL | BLOCKED`로 반환한다.
- worker 교체는 caller/host 책임이다. old worker/process가 실제 종료됐다는 host evidence가 없으면 같은 mutable worktree에 replacement를 시작하지 않는다. cancel receipt만으로 settlement를 주장하지 않는다.
- `Completion: COMPLETE` 직전에 같은 review로 `ready_contract check_plan_admission`을 다시 호출하고 load-bearing runtime/source assumptions를 직접 확인한다. current가 아니면 COMPLETE를 주장하지 않는다.

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

## Material method change와 종료

current ADMIT 후 정상 첫 source 변경에는 PRE_ACTION 재심사가 없다. worker는 load-bearing anchor/search universe/runtime 전제와 current user/Scope를 첫 의존 변경 전에 확인하며, 검토된 조건부 첫 작업의 지지/반증/불충분 분기를 따른다.

구현 중 다른 root cause, owner, shared interface, persistence 의미, authoritative readback 또는 non-idempotent effect strategy가 직접 evidence로 드러나 reviewed Plan의 중요한 방법이 바뀌면 새 방향에 의존하는 mutation을 즉시 멈춘다. 정상 진행, 일시적 test failure, 스타일 또는 동등한 국소 리팩터링은 material method change가 아니다.

material method change는 runtime pause/resume이 아니라 current implementation invocation의 terminal 경계다. worker는 `Completion: PARTIAL | BLOCKED`, reviewed direction, 새 직접 evidence, affected Plan scope, current working-tree state, `Next allowed action: revise affected Plan -> Heuristic -> independent review`를 반환하고 invocation을 끝낸다. Outer Main은 실제 Plan revision과 새 independent review를 얻은 뒤 fresh implementation actor를 시작한다. old worker를 CONTINUE로 release하지 않는다.

`IMPLEMENT` 완료에는 Ticket Scope/Non-Goals 보존, 모든 authored Verification-flow obligation에 연결된 current self-check evidence, unresolved authority conflict/material blocker 부재, authored independent-verification requirement evidence 보존, decision-critical source/diff/artifact/command/runtime behavior의 직접 확인, 그리고 terminal 직전 current `check_plan_admission` 재확인이 필요하다.

`Completion: COMPLETE`여도 exact Ticket의 `Status: ready`는 유지한다. actual implementation target과 current self-check evidence를 final verifier의 navigation handoff로 보존한다. 이후 verification 또는 IIS planning continuation을 자동 실행하지 않는다.

`Completion: BLOCKED | PARTIAL`이 admission, authority/readback, target currentness, external-effect uncertainty 또는 material method change 때문에 현재 구현 owner가 계속할 수 없음을 뜻할 때는 [references/implement.md](references/implement.md)의 **Non-continuation provenance**를 terminal caller-facing report에 포함한다. 정상 `Completion: COMPLETE`에는 이 설명 블록을 추가하지 않는다.
