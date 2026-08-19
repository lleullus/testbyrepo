
# Ready Ticket Implement

## 목적과 단일 모드

이 스킬은 IIS Planning이 만든 하나의 Ready Ticket을 그 Ticket이 승인한 제품 자체에 구현한다. IIS Planning을 재개하거나 Ticket 의미를 다시 계획하지 않는다.

실행 모드는 정확히 하나다.

- `IMPLEMENT`: Ticket을 구현하고 구현자 self-check를 수행하며, 선택된 감사자가 있으면 구현과 동시에 지속 감사를 수행한 뒤 같은 lifecycle 안에서 final fan-in까지 닫는다.

이 스킬은 구현과 구현자 self-check만 소유한다. 동시감사자는 구현 중 계약 이탈 탐지 역할이며, 별도 verification authority를 흡수·대체·재정의하거나 그 완료 여부를 판정하지 않는다.

## 실행 절차 로드 — 필수

실제 작업 전에 [references/implement.md](references/implement.md)를 전부 읽는다.

`Auditor Count`가 `1`, `2`, `3`이면 [references/concurrent-auditors.md](references/concurrent-auditors.md)를 전부 읽고, 활성 slot을 baseline부터 completion candidate의 final delta까지 유지한다.

필수 reference를 읽을 수 없거나 요청된 concurrent audit capability를 현재 host가 제공하지 못하면 정확한 unavailable item을 보고한다. 기억, 순차 사후 review 또는 임의 기본값으로 대체하지 않는다.

## 공통 입력

- Ticket: `<TICKET_PATH>`
- Project Root: `<PROJECT_ROOT>`
- 추가 사용자 지시: `<ADDITIONAL_USER_INSTRUCTIONS>`

Audit Configuration:

```text
Auditor Count: 0 | 1 | 2 | 3
Default: 0 only when no audit was requested and no count was supplied

Second Auditor Role when Count=2:
  BEHAVIOR_AUTHORITY | VERIFICATION_REGRESSION | AUTO_BY_MATERIAL_RISK

Auditor 1:
  Model: <explicit exact model, otherwise opencodex/gpt-5.6-luna>
  Reasoning Depth: <explicit exact depth, otherwise xhigh>

Auditor 2 when active:
  Role when Count=2: <resolved Second Auditor Role>
  Role when Count=3: BEHAVIOR_AUTHORITY
  Model: <explicit exact model, otherwise opencodex/gpt-5.6-luna>
  Reasoning Depth: <explicit exact depth, otherwise xhigh>

Auditor 3 when Count=3:
  Role: VERIFICATION_REGRESSION
  Model: <explicit exact model, otherwise opencodex/gpt-5.6-luna>
  Reasoning Depth: <explicit exact depth, otherwise xhigh>
```

## Ready Ticket 상태 게이트

- IMPLEMENT 시작 시 exact Ticket의 top metadata `Status:`를 직접 확인한다. 정상 입력은 exact `ready`뿐이다.
- `done`이면 이미 terminal delivery marker가 있는 Ticket이므로 다시 구현하지 않고 현재 상태를 보고한다.
- `draft` 또는 `blocked`이면 Ready Ticket delivery를 시작하지 않는다. 상태를 임의로 승격하거나 planning 결정을 대신하지 않는다.
- 이 스킬은 Ticket status를 `done`으로 바꾸지 않는다. 정상 구현 입력인 `ready`는 구현 완료 후에도 그대로 유지하며, separate verification authority가 최종 verification verdict에 따라 terminal `done` 전이를 소유한다.

## Audit Configuration 권위

- `Auditor Count`는 caller/user가 소유한다. Main이나 auditor가 임의로 증감하지 않는다.
- 사용자가 감사를 요청하지 않았고 count도 제공하지 않은 경우에만 Count `0`을 사용한다.
- 감사를 요청했지만 count가 불명확하면 `AUDIT CONFIGURATION REQUIRED: COUNT`를 보고한다.
- Count `0`은 정상 구성이다. Auditor를 생성하거나 audit coverage를 암시하지 않는다.
- Count `1`은 Primary auditor다.
- Count `2`는 Primary와 specialist 한 명이다. `Second Auditor Role`이 없으면 `AUDIT CONFIGURATION REQUIRED: SECOND ROLE`이다.
- `AUTO_BY_MATERIAL_RISK`가 caller/user에 의해 명시된 경우에만 Main이 specialist를 선택하고 첫 source change 전에 authority와 material risk 근거를 기록한다.
- Count `3`은 Primary, Behavior/Authority, Verification/Regression 세 역할을 모두 사용한다.
- Count `1~3`의 각 활성 slot에는 dispatch 전에 exact `Model`과 exact `Reasoning Depth`가 모두 해석되어 있어야 한다. 명시값이 없으면 Pi runner의 pinned default인 `opencodex/gpt-5.6-luna`와 `xhigh`를 사용한다.
- 첫 source change 전에 host가 명시적으로 요청되었거나 pinned default로 해석된 exact auditor binding으로 해당 slot을 실제 시작할 수 있어야 한다. 그 exact binding의 start/spawn 자체가 실패하면 해당 slot을 `AUDITOR BLOCKED: EXACT BINDING UNAVAILABLE`로 보고한다. Exact requested slot이 성공적으로 시작된 뒤에는 auditor의 self-reported model name, reasoning depth, runtime metadata 또는 display label은 diagnostic only이며 slot validity, re-audit 필요 여부, `IMPLEMENT` completion을 바꾸지 않는다.
- Count `1~3`인데 실제 concurrent/shared-observation capability가 없으면 순차 사후 review로 바꾸지 않고 `AUDIT CAPABILITY UNAVAILABLE`을 보고한다.

## 메타 용어와 제품 도메인 분리 — 필수

이 스킬에서 쓰는 `Ready Ticket`, `implement`, `auditor`, `handoff`, `checkpoint`, `completion candidate`, `fan-in`은 에이전트 작업 절차를 설명하는 메타 용어다. Ticket, Parent Spec, Behavior Authority 또는 승인된 UI Authority가 제품 개념으로 직접 정의하지 않은 한 제품 파일명, 모듈, 클래스, 함수, DB schema, API, CLI, route, command, engine, queue, lease, manager, orchestration layer 또는 제품 상태로 만들지 않는다.

구현 시작 전 한 문장으로 `이번 Ticket이 실제 제품에 추가하거나 변경하는 observable product outcome`을 적는다. 첫 source-file 변경은 그 outcome 또는 승인된 product invariant에 직접 연결되어야 한다.

구현 구조를 정할 때 “이 스킬을 실행하려면 무엇이 필요한가?”가 아니라 “Ticket의 제품 계약을 만족시키려면 무엇이 필요한가?”만 묻는다.

## 공통 권위와 해석 원칙

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

문서 일부를 고립해 임의로 우선시하지 않는다. 전체가 가장 강하게 뒷받침하는 승인된 결과를 보존한다. 구현 편의, 기존 코드 구조, 익숙한 설계, 최소 변경, 테스트 편의 또는 현재 구현을 이유로 사용자 결과를 축소·대체·재정의하지 않는다.

코드, 테스트, runtime과 구현자·감사자 보고는 사실을 보여줄 수 있지만 승인된 product meaning을 추가·축소·변경하지 않는다.

실질적 authority 충돌이 있으면 한쪽을 임의 선택하지 않는다. 충돌, 관련 authority와 영향을 정확히 보고하고 해결되지 않은 충돌을 숨긴 채 완료를 선언하지 않는다.

## Verification-flow 해석

파일 작업이나 검증 실험을 나누기 전에 Ticket의 각 authored Verification flow를 그대로 읽는다.

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
- Ticket에 실제 존재하는 경우에만 ordering, interruption, persistence, external-effect, UI interaction 경계

`Independent verification required` 같은 authored requirement가 있으면 그 존재와 원문 의미를 보존한다. 이 스킬은 그 요구의 충족 여부를 판정하지 않는다.

- Concurrent auditor와 Main self-check는 구현 중 evidence를 만들 수 있지만 separate verification authority를 충족하거나 대체했다고 선언하지 않는다.
- 구현 결과에는 해당 requirement와 관련 implementation/self-check evidence를 handoff 정보로 남긴다.
- Separate verification authority의 실행 여부와 판정은 이 스킬의 책임 밖이며, verification이 아직 실행되지 않았다는 사실만으로 implementation status를 자동 `BLOCKED`로 바꾸지 않는다.

Verification flow가 1차 제품 관찰 단위다. 한 flow가 여러 AC를 판정하거나 한 AC가 여러 flow에 걸릴 수 있으므로 AC 문장을 임의의 1:1 파일 작업으로 바꾸지 않는다.

각 flow에서 반드시 존재해야 하는 결과, 존재하면 모순인 결과, 확인 불가능할 때의 처리, external condition 불충족 시의 처리와 적용되는 ordering/interruption/persistence/UI 의미를 분리한다.

## 공통 결과·상태 원칙

### Observable result 우선

파일, 클래스, 함수, 테스트 이름이 아니라 Ticket이 요구하는 관찰 가능한 결과가 기준이다.

### 불변식과 uncertainty 보존

Identity, ownership, membership, ordering, duplicate 방지, terminal 보호, interruption 이후 상태와 persistence lifecycle을 정확히 보존한다. 확인할 수 없는 상태를 success 또는 failure로 추정하지 않는다.

### 책임 시작점 보존

Interruption checkpoint가 있으면 그 지점부터 제품이 소유하는 책임을 기준으로 구현한다. 제품이 작업 시작을 인정한 뒤 client timeout, 호출자 종료, 화면 이탈 또는 관찰 실패만으로 인정된 작업이 조용히 사라져서는 안 된다.

### Authority 복제 금지

외부 provider, canonical storage, 기존 runtime 또는 다른 authority가 권위일 때 편의용 독립 사본, 암묵적 history/ledger, 자동 session/resource 생성, 느슨한 전역 추정 또는 authority 의미를 바꾸는 내부 모델을 만들지 않는다.

### Authoritative readback

완료 여부는 Ticket이 지정한 acceptance boundary와 authoritative readback에서 확인할 수 있어야 한다. 내부 변수, 로그, 코드 존재 또는 테스트 이름은 승인된 acceptance boundary가 아닌 한 readback을 대체하지 않는다.

### Scope와 Non-Goals

범위 밖 UI control, API, route, command, 저장, external effect, session/resource 또는 lifecycle guarantee가 생기지 않았는지 확인한다. 편의를 위해 product authority나 ownership을 바꾸지 않는다.

### External condition

외부 조건과 제품 책임을 분리한다. 외부 조건 불충족을 제품 성공이나 제품 결함으로 꾸미지 않는다.

## 동시 감사 통합

- Count `0`: 구현과 self-check를 수행하되 auditor lifecycle, final audit sweep과 auditor fan-in이 없다.
- Count `1~3`: capability와 exact binding을 먼저 확인하고 첫 source change 전에 활성 auditor를 동시에 시작한다.
- 감사자는 shared workspace를 read-only로 지속 관찰한다.
- 중요한 finding은 구현을 불필요하게 멈추지 않는 notification으로 전달한다.
- Scope, shared contract, authority conflict, external/destructive action처럼 Main 판단이 필요한 경우에만 decision request를 연다.
- Completion candidate가 나오면 같은 활성 auditor가 final delta sweep을 수행한다.
- Auditor는 식별 가능한 exact candidate 또는 checkpoint에 귀속된 terminal audit result를 반환한다.
- Final result 뒤 새 delta가 생기면 그 result를 stale로 처리하고 해당 logical slot의 coverage를 다시 수행한다.
- Main은 모든 활성 result를 분류하고 decision-critical evidence를 직접 확인한 뒤 종료한다.

현재 host의 native concurrency, communication, lifecycle, terminal-result mechanisms와 standing governance를 사용하되, 이 스킬에서 host-specific transport 계약을 복제하거나 재정의하지 않는다.

## 종료 경계

`IMPLEMENT` 완료에는 다음이 필요하다.

1. Ticket Scope와 Non-Goals가 보존되었다.
2. Authored Verification flow에 연결된 self-check와 runtime/readback evidence가 있다.
3. Unresolved authority conflict나 material finding이 없다.
4. Authored independent-verification requirement가 있다면 그 requirement와 관련 implementation/self-check evidence가 handoff 정보로 보존되었고, 이 스킬이 충족 여부를 판정하지 않았다.
5. Count `0`이면 audit coverage를 주장하지 않는다.
6. Count `1~3`이면 모든 요청 auditor slot이 첫 source change 전에 성공적으로 시작되었고 final delta를 포함한 terminal classification을 반환했다.
7. 활성 auditor 실패·차단·소실을 조용한 count 감소로 처리하지 않았다.
8. Main이 decision-critical source claim, diff, artifact, command와 runtime behavior를 직접 확인했다.

`IMPLEMENT`가 `COMPLETE`여도 exact Ticket의 `Status: ready`는 변경하지 않는다. 구현 결과와 self-check evidence를 separate verification authority에 넘기고, terminal `done` 전이는 그 authority가 최종 verification verdict에 따라 소유한다. Spec, Scope, Increment, Acceptance Criteria, Verification flow 또는 다른 Ticket planning source도 이 스킬이 수정하지 않는다.

이 종료 절차는 같은 `IMPLEMENT` lifecycle의 fan-in이며 별도 검증 모드가 아니다. 이후 planning continuation도 자동 실행하지 않는다. Separate verification authority가 Ticket을 terminal `done`으로 닫은 뒤 사용자가 다음 IIS planning cycle을 원할 때만 `iis-workflow`를 명시적으로 호출한다.
