---
name: ready-ticket-implement
description: "Implement one existing IIS Ready Ticket and perform implementer self-check. Use for exact Ready Ticket delivery. Execution defaults to DIRECT; SUBAGENT execution is supported only when the current user explicitly selects it and is mandatory checkpointed execution. This skill never performs or adjudicates the separate verification authority."
---

# Ready Ticket Implement

## 목적과 권위

이 스킬은 IIS Planning이 만든 하나의 Ready Ticket을 그 Ticket이 승인한 제품 자체에 구현한다. IIS Planning을 재개하거나 Ticket 의미를 다시 계획하지 않는다.

구현 worker는 구현과 구현자 self-check를 소유한다. Separate heuristic-probe authority의 finding/exploration과 Separate verification authority의 실행 여부, AC verdict, whole-Ticket verdict와 terminal `done` 전이는 소유하지 않는다.

실제 작업 전에 [references/implement.md](references/implement.md)를 전부 읽는다.

## 입력

- Ticket: `<TICKET_PATH>`
- Project Root: `<PROJECT_ROOT>`
- 추가 사용자 지시: `<ADDITIONAL_USER_INSTRUCTIONS>`

## 실행 topology

Top-level 기본 실행 모드는 `DIRECT`다.

- `DIRECT`: 현재 Main이 implementation worker 역할을 직접 수행한다.
- `SUBAGENT`: 현재 사용자가 이 exact implementation stage에 `SUBAGENT`를 명시한 경우에만 Outer Main이 exact Ticket 하나를 정확히 한 명의 implementation worker에게 할당한다.
- 모델 capability, 작업 난도, 비용 또는 worker availability만으로 execution mode를 바꾸지 않는다. `DIRECT`와 `SUBAGENT` 사이의 자동 전환이나 실패 후 fallback은 없다.

`SUBAGENT`에서는 다음을 지킨다.

1. 현재 host가 한 명의 delegated child worker, 같은 Project Root 접근, checkpoint return/continuation과 terminal result를 제공할 수 있는지 확인한다.
2. exact Ticket, Project Root, 추가 사용자 지시와 `Delegated Worker: yes`를 worker assignment에 포함한다.
3. `Delegated Worker: yes`를 받은 worker는 이 스킬을 다시 위임하지 않고 implementation core를 직접 수행한다.
4. worker를 시작할 수 없거나 필요한 checkpoint return/continuation/terminal-result capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 보고한다.
5. 실패를 `DIRECT`로 자동 대체하지 않는다.
6. 한 Ticket을 여러 implementation worker에게 나누거나 worker roster, queue, retry ledger 또는 별도 review lifecycle을 만들지 않는다.

`DIRECT`에서는 현재 Main이 아래 implementation core를 직접 수행한다. `SUBAGENT`에서는 Outer Main이 assignment, current user instruction 전달, worker의 checkpoint report 수신, `CONTINUE | STEER | STOP` continuation decision, terminal result 수신과 caller-facing fan-in을 소유한다. 구현 의미와 self-check는 delegated worker가 소유하며, Outer Main은 별도의 구현자로 중복 행동하지 않는다.

## Ready Ticket 상태 게이트

- 시작 시 exact Ticket의 top metadata `Status:`를 직접 확인한다. 정상 입력은 exact `ready`뿐이다.
- `done`이면 이미 terminal delivery marker가 있는 Ticket이므로 다시 구현하지 않고 현재 상태를 보고한다.
- `draft` 또는 `blocked`이면 delivery를 시작하지 않는다. 상태를 임의로 승격하거나 planning 결정을 대신하지 않는다.
- 이 스킬은 Ticket status를 `done`으로 바꾸지 않는다. 정상 구현 입력인 `ready`는 구현 완료 후에도 그대로 유지한다.

## 메타 용어와 제품 도메인 분리

이 스킬의 `Ready Ticket`, `implementation worker`, `handoff report`, `turn report`, `checkpoint`와 `terminal result`는 에이전트 작업 절차를 설명하는 메타 용어다. Ticket, Parent Spec, Behavior Authority 또는 승인된 UI Authority가 제품 개념으로 직접 정의하지 않은 한 제품 파일명, 모듈, 클래스, 함수, DB schema, API, CLI, route, command, engine, queue, lease, manager, orchestration layer 또는 제품 상태로 만들지 않는다.

구현 시작 전 한 문장으로 `이번 Ticket이 실제 제품에 추가하거나 변경하는 observable product outcome`을 적는다. 첫 source-file 변경은 그 outcome 또는 승인된 product invariant에 직접 연결되어야 한다.

## 권위와 해석

다음 자료를 모두 읽되 각 항목의 정확한 authority/evidence 역할만 적용한다.

1. 현재의 명시적 사용자 지시
2. Ticket 전체
3. Parent Spec
4. Behavior Authorities
5. 승인된 Design/UI Authority
6. Implementation Constraints와 References
7. 현재 repository/runtime의 직접 관찰 사실

- Ticket: 이번 구현의 완료·변경 경계
- Parent Spec: 상위 제품 결과와 승인된 제품 계약
- Behavior Authority: 상태, 관계, identity, ownership, lifecycle, ordering과 semantic meaning
- Design/UI Authority: 사용자-visible 구조, 상태 표현과 상호작용
- Implementation Constraints: 승인되었거나 외부적으로 강제된 기술 선택 경계
- References와 repository/runtime: 해석과 실행을 위한 evidence/context이며 새 제품 권위가 아님

구현 편의, 기존 구조, 익숙한 설계, 최소 변경 또는 테스트 편의를 이유로 승인된 사용자 결과를 축소·대체·재정의하지 않는다. 실질적 authority 충돌이 있으면 한쪽을 임의 선택하지 않고 정확한 충돌과 영향을 보고한다.

## Verification-flow 해석

파일 작업이나 self-check를 나누기 전에 Ticket의 각 authored Verification flow를 그대로 읽는다.

- Parent outcome ordinal
- AC ordinals
- Behavior authority ordinals
- Initial state
- Trigger or inspection target
- Acceptance boundary
- Expected observable result
- Authoritative readback
- Decision boundary
- Disposition
- Independent verification requirement, 실제로 authored된 경우
- Acceptance surface
- External condition
- Ticket에 실제 존재하는 ordering, interruption, persistence, external-effect, UI interaction 경계

Authored independent-verification requirement가 있으면 원문 의미와 관련 implementation/self-check evidence를 final handoff에 보존한다. 이 스킬은 그 요구의 충족 여부를 판정하지 않는다.

Verification flow가 1차 제품 관찰 단위다. 한 flow가 여러 AC를 판정하거나 한 AC가 여러 flow에 걸릴 수 있으므로 AC 문장을 임의의 1:1 파일 작업으로 바꾸지 않는다.

## 결과 원칙

- 파일, 클래스, 함수 또는 테스트 이름보다 Ticket의 observable result를 우선한다.
- Identity, ownership, membership, ordering, duplicate 방지, terminal 보호, interruption 이후 상태와 persistence lifecycle을 보존한다.
- 외부 provider, canonical storage 또는 기존 runtime이 권위일 때 편의용 독립 사본이나 암묵적 history/ledger를 만들지 않는다.
- Ticket이 지정한 acceptance boundary와 authoritative readback으로 완료 여부를 확인한다.
- Scope/Non-Goals 밖 UI, API, route, 저장, external effect, session/resource 또는 lifecycle guarantee를 만들지 않는다.
- 외부 조건 불충족을 제품 성공이나 제품 결함으로 꾸미지 않는다.

## 보고와 종료

Delegated worker는 contract preflight 뒤 첫 source-file 변경 전에 `IMPLEMENTATION HANDOFF REPORT`를 `PRE_ACTION` checkpoint로 direct parent에게 반환한다. Parent decision 전에는 `FIRST_SOURCE_FILE_CHANGE` 보호 구간으로 넘어가지 않는다.

구현 방향, authority 해석, change surface 또는 evidence 전략이 material하게 바뀌는 경우에만 `IMPLEMENTATION TURN REPORT`를 `MATERIAL_TURN` checkpoint로 반환한다. 정상 진행, 일시적 test failure, 스타일 또는 단순한 내부 리팩터링은 중간 보고 사유가 아니며 periodic progress checkpoint를 만들지 않는다.

Checkpoint는 logical phase boundary이며 required live-wait primitive, direct-user approval gate 또는 durable workflow state가 아니다. Parent는 `CONTINUE | STEER | STOP` 중 정확히 하나를 반환한다. checkpoint continuation capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 반환하고 `DIRECT`로 자동 fallback하지 않는다. Parent/user authority가 실제로 필요한 unresolved decision에 도달해 bounded continuation으로 해결할 수 없으면 확보한 evidence와 정확한 blocker를 포함해 `Completion: BLOCKED` terminal result를 반환한다.

`IMPLEMENT` 완료에는 다음이 필요하다.

1. Ticket Scope와 Non-Goals가 보존되었다.
2. 모든 authored Verification-flow obligation에 연결된 self-check와 runtime/readback evidence가 있다.
3. Unresolved authority conflict나 material blocker가 없다.
4. Authored independent-verification requirement와 관련 implementation/self-check evidence가 final handoff에 보존되었다.
5. Worker가 decision-critical source claim, diff, artifact, command와 runtime behavior를 직접 확인했다.

`Completion: COMPLETE`여도 exact Ticket의 `Status: ready`는 변경하지 않는다. 구현 target/checkpoint와 self-check evidence를 separate heuristic-probe authority와 separate verification authority에 넘길 수 있는 navigation handoff로 보존한다. 이후 heuristic probing, verification 또는 IIS planning continuation을 자동 실행하지 않는다.
