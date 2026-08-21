# Concurrent Auditor Contract

## 목적

이 reference는 하나의 Ready Ticket `IMPLEMENT` lifecycle 안에서 선택적으로 동작하는 `0~3`개의 concurrent read-only implementation auditor 계약을 정의한다.

- Count `0`: auditor를 생성하지 않는다.
- Count `1~3`: 구현 시작 baseline부터 completion candidate의 마지막 delta까지 활성 auditor를 유지한다.

Auditor는 구현자도 아니고 separate verification authority도 아니다. 구현 중 contract drift와 material regression을 조기에 탐지하는 역할이며, 제품 코드를 수정하거나 verification 완료 또는 사용자-visible 완료를 선언하지 않는다.

## 입력

- Ticket: `<TICKET_PATH>`
- Project Root: `<PROJECT_ROOT>`
- Baseline Revision: `<BASELINE_REVISION>`
- Baseline Working Tree State: `<CLEAN | PREEXISTING_DIFF_OR_SNAPSHOT_REFERENCE>`
- Shared Workspace: `<SHARED_WORKSPACE>`
- Direct Parent: `<PARENT_HANDLE>`
- 추가 사용자 지시: `<ADDITIONAL_USER_INSTRUCTIONS>`

Auditor Configuration:

```text
Auditor Count: 1 | 2 | 3

Auditor 1:
  Role: PRIMARY_CONTRACT_IMPLEMENTATION
  Model: <exact caller/user-designated model>
  Reasoning Depth: <exact caller/user-designated depth>

Auditor 2 when active:
  Role when Count=2: BEHAVIOR_AUTHORITY | VERIFICATION_REGRESSION
  Role when Count=3: BEHAVIOR_AUTHORITY
  Model: <exact caller/user-designated model>
  Reasoning Depth: <exact caller/user-designated depth>

Auditor 3 when Count=3:
  Role: VERIFICATION_REGRESSION
  Model: <exact caller/user-designated model>
  Reasoning Depth: <exact caller/user-designated depth>
```

Count `2`에서 Auditor 2 role은 caller/user가 명시하거나 caller/user가 명시한 `AUTO_BY_MATERIAL_RISK`를 Main이 dispatch 전에 해석한 결과여야 한다. 값이 없으면 실행하지 않는다.

## Roster와 binding 계약

- Primary auditor는 Count `1~3`에서 항상 활성이다.
- Count `2`는 Primary와 정확히 한 specialist다.
- Count `3`은 Primary, Behavior/Authority, Verification/Regression 세 역할이다.
- 역할을 중복 배치하지 않는다.
- Auditor가 스스로 count나 role을 바꾸지 않는다.
- 각 active slot은 exact Model과 exact Reasoning Depth가 모두 있어야 한다.
- Host는 첫 source change 전에 exact requested slot configuration으로 execution context를 성공적으로 시작해야 한다. Host default나 대체 binding을 사용하지 않는다. 성공적으로 시작된 뒤 self-reported model/depth/runtime metadata/display label은 diagnostic only다.
- Active slot을 실행할 capability가 없으면 다른 slot, 다른 model/depth 또는 순차 review로 대체하지 않는다.

`VERIFICATION_REGRESSION`이라는 role 이름은 구현 중 verification surface와 regression risk를 감사한다는 뜻이다. Separate verification authority를 수행하거나 verification verdict를 내린다는 뜻이 아니다.

## Host capability requirements

Count `1~3`을 실제 concurrent audit로 실행하려면 현재 host가 다음 capability를 제공해야 한다.

1. **Concurrent execution**: 구현자가 계속 작업하는 동안 auditor가 별도 execution context에서 진행된다.
2. **Shared observation**: 같은 implementation workspace 또는 그 최신 delta를 관찰할 수 있다.
3. **Spawn admission fidelity**: 각 active slot의 requested model과 reasoning depth를 실제 start/spawn configuration에 적용할 수 있고 exact requested slot의 시작 성공을 확인할 수 있다. 시작 성공 뒤에는 auditor self-report metadata로 binding을 재판정하지 않는다.
4. **Non-blocking intermediate communication**: material finding이나 dependency status를 전달한 뒤 안전한 감사를 계속할 수 있다.
5. **Authority decision escalation**: parent 권한이 필요한 material decision을 구분해 요청할 수 있다.
6. **Lifecycle continuity**: initial pass 뒤 종료하지 않고 implementation completion candidate까지 attached 상태를 유지할 수 있다.
7. **Distinct terminal result**: 중간 notice나 progress와 구별되는 final audit result를 반환할 수 있다.
8. **Fan-in and cancellation**: parent가 active slot 상태를 분류하고 필요한 경우 취소하며 terminal result를 fan-in할 수 있다.

Capability가 부족하거나 exact requested slot을 start/spawn할 수 없으면 `AUDIT CAPABILITY UNAVAILABLE` 또는 해당 binding blocker를 첫 source change 전에 보고한다. 일단 exact requested slot이 성공적으로 시작된 뒤에는 self-reported binding metadata 차이만으로 blocker나 re-audit를 만들지 않는다. Count를 줄이거나 순차 사후 review를 concurrent audit로 가장하지 않는다.

현재 host의 native concurrency, communication, lifecycle, terminal-result mechanisms와 standing governance를 사용하되, 이 스킬에서 host-specific transport 계약을 복제하거나 재정의하지 않는다.

## 공통 authority와 read-only 경계

감사자는 필요한 범위에서 다음을 할 수 있다.

- Ticket, Parent Spec, Behavior/UI Authority와 references 읽기
- baseline과 current implementation delta 비교
- 관련 코드, 테스특, 설정, 문서, 로그, runtime과 browser 상태 조사
- read-only 또는 비파괴적 test/build/probe 실행
- 지정된 audit evidence 위치에 보고서 기록
- material finding, decision request와 terminal result를 direct parent에게 전달

감사자는 다음을 하지 않는다.

- tracked source/config/test 수정
- 제품 persisted runtime/external state 수정
- Git index/history/HEAD 또는 branch/tag 수정
- finding 직접 패치
- 다른 auditor 결과의 최종 수용
- scope, 사용자 선호, 정책 또는 risk acceptance 결정
- separate verification authority의 verdict 선언
- parent fan-in이나 사용자-visible completion 선언

테스트가 cache, compiler output, coverage 같은 재생성 가능한 ephemeral artifact를 만들 수는 있지만 product change나 audit authority로 취급하지 않는다. Tracked file, durable product state 또는 external state를 바꿀 가능성이 있으면 실행하지 않는다.

Host가 tool-level read-only를 강제하지 못하면 `Enforcement level`을 final result에 명시한다. 지침만으로 제한된 상태를 hard read-only로 과장하지 않는다.

Baseline이 clean이 아니면 pre-existing change를 고정한다. 이번 Ticket delta와 신뢰성 있게 분리할 수 없으면 `AUDIT BLOCKED: BASELINE AMBIGUOUS`를 보고한다.

## 감사 lifecycle

활성 auditor는 one-shot review가 아니다.

1. Baseline과 authority를 읽는다.
2. 역할에 맞는 invariant와 watchpoint뉼 정한다.
3. 초기 watchpoint와 material risk가 있으면 `AUDIT PRECHECK NOTICE`로 알린다.
4. 구현과 동시에 current delta 감사를 계속한다.
5. 초기 pass가 끝나도 implementation lifecycle이 열려 있으면 terminal result를 반환하지 않는다.
6. 새 material delta, finding resolution, relevant test/runtime evidence 또는 scope change가 생기면 역할 범위에서 다시 검사한다.
7. Material finding은 가능한 이른 안전한 실행 경계에서 알리고, unrelated safe audit work는 계속한다.
8. 실제 parent authority가 필요한 material decision일 때만 `AUDIT DECISION REQUEST`를 연다.
9. Completion candidate가 나오면 같은 활성 auditor가 그 candidate의 final delta와 relevant evidence를 마지막으로 검사한다.
10. Final delta sweep이 끝나면 식별 가능한 exact candidate 또는 checkpoint에 귀속된 `AUDIT FINAL RESULT`를 반환한다.
11. Final result 뒤 implementation delta가 생기면 기존 result를 `STALE`로 처리하고 같은 logical slot, role, exact binding, baseline과 prior findings를 보존해 변경분 coverage를 다시 수행한다.

Host가 같은 long-lived context를 유지할 수 없더라도 logical continuity를 보존해야 한다. 같은 slot, role, exact binding, baseline, prior findings와 최신 delta를 이어받을 수 없다면 완료된 lifecycle 감사로 꾸미지 않는다.

## 중간 보고와 decision

### `AUDIT PRECHECK NOTICE`

```text
AUDIT PRECHECK NOTICE

Auditor:
Role:
Exact model/depth requested:
Watchpoint:
Authority:
Affected Verification flow / AC:
Baseline evidence:
Failure mode to watch:
Minimal counterexample:
```

### `AUDIT FINDING NOTICE`

계속 진행하면 계약 위반, 회귀 또는 큰 수정 비용으로 이어질 material risk만 보낸다.

```text
AUDIT FINDING NOTICE

Auditor:
Finding:
Authority:
Diff/runtime anchor:
Affected Verification flow / AC:
Confirmed or likely failure mode:
Minimal falsification or reproduction:
Impact if implementation continues:
Required parent action: NONE | REVIEW | DECISION
```

정상 WIP, 일시적 compile failure, 스타일, 명명 취향, 더 예쁜 구조는 보고하지 않는다.

### `AUDIT DECISION REQUEST`

Material scope divergence, shared interface/contract 변경, unresolved authority conflict, required dependency failure, external/destructive/irreversible/costly/security-sensitive action, unresolved sibling ownership conflict, 최신 사용자 지시 충돌 또는 containment가 크게 어려워지는 경우에만 연다.

```text
AUDIT DECISION REQUEST

Correlation:
Auditor:
Decision required:
Authority and evidence:
Safe work that can continue:
Work blocked by this decision:
Consequence of each known option:
```

고정 시간이나 tool-call 수를 이유로 decision request를 만들지 않는다. 하나의 auditor-parent 관계에는 unresolved authority decision을 한 번에 하나만 유지한다.

## `AUDIT FINAL RESULT`

Final delta sweep 이후 반환하는 terminal audit result다.

```text
AUDIT FINAL RESULT

Auditor:
Role:
Exact model/depth requested:
Spawn admission: SATISFIED | FAILED
Enforcement level: TOOL_ENFORCED | POLICY_ENFORCED_WITH_PROBE_RISK | INSTRUCTION_ONLY
Baseline:
Reviewed candidate/checkpoint:
Final implementation delta reviewed:
Test/runtime evidence reviewed:
Material findings and disposition:
Open blockers:
Coverage limitations:
Classification: COMPLETE | BLOCKED | FAILED | CANCELLED | STALE
Separate verification authority verdict: Not performed by auditor
Implementation completion: Not declared by auditor
```

Intermediate notice나 progress는 terminal audit result를 대체하지 않는다.

## Auditor 1 — Primary Contract and Implementation

모든 roster의 기본 auditor다.

- Ticket/Spec/Behavior/UI authority 의미 보존
- observable result와 authoritative readback 연결
- Scope/Non-Goals 침범
- cross-AC와 cross-component regression
- identity, ownership, ordering, terminal, interruption, persistence
- uncertainty를 success/failure로 추정하는 구현
- 외부 authority 복제와 암묵적 session/resource/history
- tests가 실제 decision boundary를 판정하는지
- 구현 구조가 Ticket 계약 만족을 불필요하게 막는지

일반 코드 리뷰나 스타일 개선을 하지 않는다. Finding은 authority, anchor, failure mode와 최소 반증에 연결한다.

## Behavior and Authority specialist

- 복수 상태와 terminal 보호
- concurrency, retry, replay, duplicate, late/out-of-order event
- long-running work와 interruption
- identity, membership, ownership, reconciliation
- refresh/reopen/process lifecycle
- 외부 provider 결과의 잘못된 귀속
- stale result 부활과 uncertainty 손실
- UI 표현과 Behavior meaning의 모순

각 finding에 실행 가능한 counterexample을 붙인다.

## Verification Surface and Regression specialist

- authored Verification flow와 AC coverage 누락
- acceptance surface와 disposition 불일치
- 내부 로그/mock이 authoritative readback을 대체
- trigger를 실행하지 않고 코드 존재만 확인
- partial, timeout, identity 누락, terminal, duplicate 경계 누락
- UI focus, keyboard, scroll, refresh와 rendered-state 누락
- provider/runtime 실제 shape와 fake 차이
- Scope 밖 route, control, 저장, effect, session/resource
- 한 AC 수정이 다른 AC readback을 깨는 변화

Finding을 `Coverage gap`, `Readback gap`, `Runtime-shape mismatch`, `UI interaction gap`, `External-condition gap`, `Cross-AC regression`, `Scope/Non-Goal side effect` 중 하나로 분류한다.

## Sibling coordination

감사자끼리 중복 조사 방지, file/symbol/test ownership, parent가 정한 interface clarification, dependency readiness, shared-file conflict 경고와 짧은 evidence pointer를 조정할 수 있다.

Scope를 확장하거나 shared contract, 사용자 정책, risk acceptance를 결정하지 않는다. 다수결로 finding을 무효화하지 않는다.

## 종료 경계

개별 slot의 `AUDIT FINAL RESULT`는 다음을 모두 충족해야 한다.

- Baseline과 authority를 읽었다.
- Lifecycle 중 relevant delta를 감사했다.
- 같은 활성 auditor가 식별 가능한 completion candidate/checkpoint의 final delta를 검사했다.
- Material finding, limitation과 enforcement level을 terminal result에 기록했다.
- Result가 어떤 candidate/checkpoint에 귀속되는지 명확하다.

감사자 terminal result는 구현 완료나 separate verification authority의 verdict를 의미하지 않는다. Main이 모든 active slot을 fan-in하고 직접 evidence를 확인한 뒤 `IMPLEMENT` 종료를 판단한다.
