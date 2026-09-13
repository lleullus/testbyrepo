---
name: ready-ticket-implement
description: "Implement one existing IIS Ready Ticket and perform implementer self-check. Use for exact Ready Ticket delivery. Top-level execution defaults to SUBAGENT with one implementation worker; use DIRECT only when the current user explicitly selects it for this stage. The actual implementing actor must pass current plan admission before mutation and again before COMPLETE. This skill never performs or adjudicates the separate verification authority."
---

# Ready Ticket Implement

## Caller: include in every delegated assignment

Adaptive 호출자는 실제 shared context에서 역할별 Target/Change 지시 **앞에** 값이 채워진 Common original sources 블록을 넣는다. child에게 이 스킬이나 템플릿을 읽으라고 지시하는 것으로 실제 블록 전달을 대신하지 않는다.

- Project Root: 정확한 절대 경로.
- Thesis: 승인된 source-set 전체의 복구 가능한 정확한 경로, bound revision/identity와 기존 binding 참조. 승계 원본을 포함한 모든 bound source를 보존한다.
- Repository investigation: 제공된 immutable artifact의 정확한 경로와 recorded identity, 또는 None supplied.
- Transition Baseline: 적용되는 승인 원본의 정확한 경로, revision과 approval/applicability 참조, 또는 Not activated.

child에게 **역할별 판단·편집 전에 바인딩된 원본을 직접 읽고 Thesis의 목적·핵심 완료 루프·거짓 성공 구분을 확인하라**고 명시한다. 요약으로 대신하거나 원본 선택·최신 파일 검색을 child에게 떠넘기지 않는다.
받은 공통 블록은 변경 없이 전달하고 정확한 역할 문서·대상·출력·권한 경계는 그 뒤에 넣는다. 원본 접근은 Ticket 범위 확대 권한이 아니다.
원본 변경과 허용되는 부재·사유는 기존 [shared source assignment](../../iis-adaptive-planning/templates/SHARED-SOURCE-ASSIGNMENT.template.md)를 따른다. standalone 구현의 기존 authority 입력은 유지하며 Adaptive 활성화나 새 Thesis 생성을 요구하지 않는다.

### Evidence boundary — copy into the assignment

standalone 구현을 포함한 모든 실제 위임에서 아래 블록 원문을 실제 shared context에 넣는다. 적용되는 Common original sources 뒤, 역할별 Target/Change 지시 앞에 배치한다. 이미 전달받은 동일 블록은 변경 없이 한 번만 유지한다. 스킬·템플릿 링크나 이 규칙을 읽으라는 지시로 실제 블록 전달을 대신하지 않는다.

> **Evidence boundary — apply before role-specific work**
> - Do not use mocks, stubs, canned responses, seeded success states or surrogate readbacks as completion or verification evidence for the actual acceptance boundary they replace.
> - When the approved outcome requires real execution, state transitions or external effects, evidence must exercise the required real path and authoritative readback. Internal success or HTTP acceptance alone cannot prove the required external effect.
> - A double for an ancillary dependency does not invalidate observation of an unrelated real boundary. Distinguish boundaries actually observed from those replaced by doubles and therefore not verified.
> - If required evidence is unavailable, preserve the gap under your role's existing limitation/return rules. Do not infer success or obtain evidence through unauthorized actions. This instruction does not expand your role's execution authority.

## 목적과 권위

이 스킬은 IIS Planning이 만든 하나의 Ready Ticket을 그 Ticket이 승인한 제품 자체에 구현한다. IIS Planning을 재개하거나 Ticket 의미를 다시 계획하지 않는다.

구현 worker는 구현과 구현자 self-check를 소유한다. 준비 reviewer의 독립 착수 판단과 final verifier의 탐색·AC verdict·whole-Ticket verdict·terminal `done` 전이는 소유하지 않는다.

호출자는 이 entry의 입력·dispatch·결과 소비 계약을 읽는다. 실제 구현자(위임 worker 또는 명시적 DIRECT의 Main)는 [references/implement.md](references/implement.md) 전체를 읽고 적용한다. SUBAGENT 호출자는 worker core를 재서술하거나 수행하지 않는다.

## 입력

- Ticket: `<TICKET_PATH>`
- Project Root: `<PROJECT_ROOT>`
- 추가 사용자 지시: `<ADDITIONAL_USER_INSTRUCTIONS>`
- Plan Review: `<exact outside-Project-Root iis-plan-review/v1 path>`; 없거나 stale이면 source mutation/assignment 전에 [ready-ticket-plan](../ready-ticket-plan/SKILL.md)으로 필요한 준비부터 수행/요청한다. 실제 독립 reviewer의 current ADMIT 없이 착수하지 않는다.

## 실행 topology

Top-level 기본 실행 모드는 `SUBAGENT`다. 현재 사용자가 이 exact implementation stage에 `DIRECT`를 명시한 경우에만 `DIRECT`를 사용한다. 기본 모드 사용을 위한 별도 SUBAGENT 승인을 요구하지 않는다.

현재 pinned bundle의 이 SKILL.md와 references/implement.md의 정확한 읽기 가능한 경로를 resolve하여 작업 전 직접 읽고 적용하라는 지시와 함께 전달한다. 한 worker에게 exact Ticket/Project Root/`plan_review_path`, 검토된 범위와 conditional first work, 현재 사용자 지시·모드·모델, 원본 authority, source ownership, 알려진 finding/변경 증거와 허용된 효과·출력 경로를 바인딩한다. `Delegated Worker: yes` 및 현재 host Communication 계약을 포함하고, 구현/self-check만 수행한 뒤 terminal `IMPLEMENT RESULT`로 종료하도록 한다. worker는 재위임·계획 재설계·독립 판정·후속 Ticket을 수행하지 않는다.

공통 원본 전달은 이 스킬 상단의 caller 블록을 따른다. 필요한 worker 실행·동일 Project Root 접근·terminal 회수 capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`과 실제 한계를 반환하며 DIRECT로 대체하지 않는다.

한 mutable worktree에는 하나의 구현 owner를 두고 정확한 terminal만 소비한다. 정상 실행 중 progress polling·status DM·중복 repository 검사를 하지 않는다. 사용자 status/stop 요청, host 실패, 누락/잘못된 terminal 또는 실제 replacement/settlement 진단에만 bounded snapshot을 사용한다. 취소 receipt만으로 종료를 추정하지 않으며 실제 settlement 뒤에만 fresh actor를 시작한다.

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

## 수행 절차의 소유권

제품 의미 해석, authored Verification-flow 연결, load-bearing 전제 확인, 구현 및 current self-check 절차는 [references/implement.md](references/implement.md)의 실제 구현자 계약이 소유한다. 호출자는 원본과 검토된 방법·입출력을 전달하고, 반환된 exact target, 수행한 self-check, admission 결과와 한계를 소비한다. 테스트 통과나 구현 COMPLETE를 독립 verification으로 승격하지 않는다.

## Material method change와 종료

current ADMIT 후 정상 첫 source 변경에는 PRE_ACTION 재심사가 없다. worker는 load-bearing anchor/search universe/runtime 전제와 current user/Scope를 첫 의존 변경 전에 확인하며, 검토된 조건부 첫 작업의 지지/반증/불충분 분기를 따른다.

구현 중 다른 root cause, owner, shared interface, persistence 의미, authoritative readback 또는 non-idempotent effect strategy가 직접 evidence로 드러나 reviewed Plan의 중요한 방법이 바뀌면 새 방향에 의존하는 mutation을 즉시 멈춘다. 정상 진행, 일시적 test failure, 스타일 또는 동등한 국소 리팩터링은 material method change가 아니다.

material method change는 runtime pause/resume이 아니라 current implementation invocation의 terminal 경계다. worker는 `Completion: PARTIAL | BLOCKED`, reviewed direction, 새 직접 evidence, affected Plan scope, current working-tree state, `Next allowed action: revise affected Plan -> independent review`를 반환하고 invocation을 끝낸다. Outer Main은 실제 affected Plan revision과 current independent review를 얻은 뒤 fresh implementation actor를 시작한다. old worker를 CONTINUE로 release하지 않는다.

`IMPLEMENT` 완료에는 Ticket Scope/Non-Goals 보존, 모든 authored Verification-flow obligation에 연결된 current self-check evidence, unresolved authority conflict/material blocker 부재, authored independent-verification requirement evidence 보존, decision-critical source/diff/artifact/command/runtime behavior의 직접 확인, 그리고 terminal 직전 current `check_plan_admission` 재확인이 필요하다.

`Completion: COMPLETE`여도 exact Ticket의 `Status: ready`는 유지한다. actual implementation target과 current self-check evidence를 final verifier의 navigation handoff로 보존한다. 이후 verification 또는 IIS planning continuation을 자동 실행하지 않는다.

`Completion: BLOCKED | PARTIAL` 또는 capability failure로 계속할 수 없으면 반환된 `Decision`, `Governing authority`, `Observed condition`, `Effect`, `Next allowed action`을 보존한다. 호출자 자신이 발견한 capability/transport 한계도 같은 필드로 실제 관찰과 허용된 다음 행동만 보고한다. 정상 COMPLETE에는 이 블록을 추가하지 않으며 제품 원인을 추측하지 않는다.
