# IMPLEMENT 실행 계약

## 1. 입력과 configuration 고정

다음을 확보한다.

- Ticket path와 Project root
- exact Ticket top metadata `Status:`가 `ready`인지 확인; `done`이면 이미 terminal delivery marker가 있으므로 재구현하지 않고, `draft`/`blocked`이면 시작하지 않는다.
- 현재 추가 사용자 지시
- Auditor Count
- Count `2`의 명시적 specialist 값
- 각 활성 slot의 exact Model과 exact Reasoning Depth
- baseline revision과 baseline working-tree 상태

감사를 요청하지 않았고 Count도 제공하지 않은 경우에만 Count `0`을 사용한다. 감사를 요청했지만 Count, Count 2 role 또는 active-slot binding이 부족하면 해당 configuration gap을 정확히 보고한다.

## 2. Concurrent audit capability preflight

Count `1~3`이면 첫 source change 전에 다음을 확인한다.

- 요청된 수만큼 별도 execution context를 동시에 시작할 수 있는가
- 각 execution context가 같은 workspace의 최신 delta를 관찰하는가
- 각 active slot의 exact model/depth를 제공할 수 있는가
- non-blocking notice, correlated decision request, steering, lifecycle hold, terminal result와 cancellation이 가능한가
- 현재 host의 native mechanisms와 standing governance가 위 capability를 실제로 제공하는가

충족되지 않으면 count를 줄이거나 순차 사후 review로 바꾸지 않는다. 새로운 명시적 사용자/caller 지시 없이 reduced coverage로 source change를 시작하지 않는다.

## 3. Contract preflight

첫 source-file 변경 전에:

1. Ticket 전체와 연결된 Parent Spec, Behavior/UI Authority, constraints와 references를 읽는다.
2. 한 문장으로 observable product outcome을 적는다.
3. 각 authored Verification flow의 initial state, trigger, acceptance boundary, expected result, authoritative readback과 disposition을 정리한다.
4. Scope와 Non-Goals에서 생겨야 하는 것과 생기면 안 되는 것을 분리한다.
5. Authored independent-verification requirement가 있으면 그 존재와 원문 의미를 기록하고, separate verification authority에 넘길 implementation/self-check evidence를 식별한다. 이 단계에서 충족 여부를 판정하지 않는다.
6. Repository/runtime에서 현재 behavior, entry point, test surface와 직접 readback을 확인한다.
7. Pre-existing working-tree change가 있으면 이번 Ticket delta와 분리 가능한 baseline을 기록한다.
8. Count `1~3`이면 같은 스킬의 [concurrent-auditors.md](concurrent-auditors.md)를 적용하고 현재 host가 필요한 concurrent audit capability를 제공하는지 확인한 뒤 활성 roster를 동시에 시작한다.

첫 source change가 observable product outcome 또는 승인된 invariant와 직접 연결되지 않으면 방향을 다시 검토한다.

## 4. Auditor roster 시작

Count `1~3`일 때:

- 모든 auditor에게 같은 baseline, Ticket, authority paths, Scope/Non-Goals, Verification flows, shared workspace와 추가 사용자 지시를 제공한다.
- 역할별 exact target, non-goals, acceptance evidence와 read-only 경계를 제공한다.
- exact Model과 exact Reasoning Depth를 requested slot configuration으로 적용해 start/spawn한다. 그 exact requested slot의 start/spawn 성공이 binding admission을 닫는다. 이후 auditor self-report의 model/depth/runtime metadata/display label은 diagnostic only이며 binding을 다시 열거나 re-audit 또는 completion blocker를 만들지 않는다.
- Count `2`의 `AUTO_BY_MATERIAL_RISK`는 caller/user가 그 값을 명시한 경우에만 해석한다.
- 활성 auditor를 구현자의 첫 source change 전에 시작한다.
- 각 auditor assignment에는 역할, scope, non-goals, required evidence, read-only 경계, lifecycle 지속과 communication 기대를 명시하되 host-specific transport 문법을 이 스킬에서 재정의하지 않는다.

Count `0`이면 auditor context를 만들거나 빈 auditor task를 생성하지 않는다.

## 5. 구현

### 제품 결과 중심

- 내부 구조보다 observable outcome을 먼저 고정한다.
- Ticket이 고정하지 않은 구현 세부는 repository의 기존 product vocabulary와 architecture를 따른다.
- 스킬 메타 용어를 제품 도메인에 투사하지 않는다.
- 최소 변경, 단순성, 속도, 가역성은 사용자 결과에 미치는 실제 영향 안에서만 비교한다.

### 구현 필요성·충분성 관문

Ticket의 observable product outcome, Scope/Non-Goals, 적용되는 product invariant와 모든 authored Verification-flow obligation을 필수 구현 분모로 먼저 고정한다. 이 관문은 필수 결과, 경계, authoritative readback, self-check 또는 evidence를 생략·약화하거나 Ticket 의미를 재해석하는 데 사용할 수 없다.

각 재량적 코드 변경, 추상화, 리팩터링, 방어장치, 상태 저장, 추가 interface 또는 observability surface는 현재 canonical product contract에 대한 직접적인 anchor가 있거나, 추가하지 않을 경우 계약 달성을 방해하는 구체적이고 현실적인 실패 경로가 있어야 한다. 기존 동작이 이미 해당 의무를 충족하면 그 동작을 보존하고 직접 evidence로 확인하며, diff를 만들기 위한 재작성이나 일반적 개선을 추가하지 않는다.

이론적 가능성, 미래 확장, 더 깔끔한 구조, 완전해 보이려는 목적, 일반적인 hardening 또는 test 편의만으로 제품 변경을 추가하지 않는다. 필수 계약을 충분히 보존하는 구현안들 사이에서만 tradeoff를 비교하고 가장 작고 명확한 충분한 delta를 선택한다. 필수 구현, self-check, evidence와 요청된 audit lifecycle이 닫히면 Ticket과 무관한 개선을 계속하지 않는다.

### Flow 단위 작업

각 change와 self-check를 authored Verification flow에 연결한다.

- 어떤 change가 어떤 flow와 invariant를 만족시키는가
- 어떤 readback으로 관찰할 수 있는가
- 어떤 모순 결과를 막아야 하는가
- external condition이 없을 때 disposition은 무엇인가
- ordering, interruption, persistence, UI interaction 의미가 어디에서 보존되는가

### Test와 runtime evidence

- 적절한 unit/integration/E2E/build/type/lint 검증을 사용한다.
- Acceptance surface가 runtime, browser, provider, CLI 또는 canonical storage라면 가능한 직접 관찰을 우선한다.
- Mock, 로그, 내부 변수만으로 authoritative readback을 대체하지 않는다.
- 외부 효과는 Ticket이 허용한 sandbox, authority, cleanup과 readback 경계 안에서만 실행한다.

## 6. Event-driven auditor synchronization

Count `1~3`이면 Main은 고정 시간 polling 대신 material event를 기준으로 auditor를 갱신한다.

- 의미 있는 implementation delta
- Auditor finding에 대한 수정
- 관련 test/runtime evidence 변화
- Scope 또는 shared-contract revision
- completion candidate 생성 또는 무효화

각 material event에는 auditor가 오래된 delta나 completion candidate를 최신으로 오인하지 않도록 충분한 delta/candidate identity를 포함한다.

## 7. Finding과 decision 처리

Auditor notice를 받으면 authority와 diff/runtime anchor를 확인하고 material finding, 정상 WIP, 중복 또는 stale로 분류한다.

유효한 finding은 구현 방향과 영향받은 flow를 교정한다. 반박할 때는 구체적인 authority와 직접 evidence를 반환한다. Auditor report를 자동 수용하지도, 구현 편의를 위해 축소하지도 않는다.

Decision request는 material scope divergence, shared interface/contract 변경, unresolved authority conflict, required dependency failure, external/destructive/irreversible/costly/security-sensitive action, 최신 사용자 지시 충돌 또는 containment가 크게 어려워지는 경계에서만 연다.

## 8. Completion candidate와 final audit

Completion candidate 전에:

- intended product outcome과 authoritative readback을 확인한다.
- Scope/Non-Goals를 다시 읽는다.
- 관련 tests/runtime evidence를 실행한다.
- pre-existing diff와 Ticket delta를 분리한다.
- limitation, external condition, inconclusive evidence, open finding과 decision request를 기록한다.

Count `0`이면 self-check와 Main direct evidence 확인 뒤 종료 판단으로 간다.

Count `1~3`이면:

1. 식별 가능한 exact candidate 또는 checkpoint와 self-check evidence를 모든 활성 auditor가 확인할 수 있게 한다.
2. 같은 활성 auditor가 final delta sweep을 수행하고 그 candidate/checkpoint에 귀속된 terminal audit result를 반환한다.
3. Finding 때문에 구현이 바뀌면 새 candidate를 만들고 이전 audit result를 stale로 처리한 뒤 변경 delta를 다시 감사한다.
4. Terminal audit result에는 reviewed candidate, relevant evidence, material finding과 limitation을 명시한다.
5. Terminal result 뒤 코드가 바뀌면 해당 result를 stale로 분류하고 같은 logical slot, role, exact binding, baseline과 prior findings를 보존해 변경분 coverage를 다시 수행한다.

이 단계는 implementation-time audit의 종료이며 separate verification authority를 수행하거나 대체하지 않는다.

## 9. Final fan-in

Main은:

1. 모든 활성 slot의 terminal result 또는 runtime terminal failure를 수집한다.
2. `COMPLETE | BLOCKED | FAILED | CANCELLED | STALE`을 구분한다.
3. Intermediate notice나 진행 status를 terminal audit result로 대체하지 않는다.
4. Finding 간 충돌을 authority와 직접 evidence로 해소한다.
5. Decision-critical source claim, diff, artifact, command와 runtime behavior를 직접 확인한다.
6. Final result 이후 새 delta가 없는지 확인한다.
7. 선택된 slot unavailable을 조용한 count 감소로 처리하지 않는다.

## 10. Ticket status handoff

이 스킬은 exact Ticket의 top metadata `Status:`를 변경하지 않는다. 정상 구현 입력인 `ready`는 `IMPLEMENT COMPLETE` 뒤에도 `ready`로 유지한다.

- `done`은 separate verification authority가 최종 verification verdict에 따라 소유하는 terminal delivery marker다.
- 구현 완료, passing tests, Main self-check 또는 implementation auditor result만으로 `done`을 쓰지 않는다.
- Spec, Scope, Increment, AC, Verification flow, Behavior/UI authority 또는 다른 Ticket planning source를 수정하지 않는다.
- 구현 결과에는 separate verification authority가 사용할 exact implementation target/checkpoint와 self-check/runtime evidence를 handoff한다.
- 이 스킬은 이후 verification이나 planning continuation을 자동 실행하지 않는다.

## 11. 종료 보고

```text
IMPLEMENT RESULT

Ticket:
Ticket Status: ready (unchanged; separate verification authority owns terminal done) | unchanged because implementation did not run
Planning continuation: invoke `iis-workflow` explicitly when the user wants the next planning cycle
Observable product outcome:
Implemented scope:
Non-Goals preserved:
Verification flows used for implementation/self-check:
Authoritative readback:
Separate verification authority required:
Verification status: NOT ADJUDICATED BY THIS SKILL
Verification evidence handoff:
Tests/runtime evidence:
Auditor Count:
Auditor roles:
Requested exact model/depth bindings:
Spawn admission: SATISFIED | FAILED
Auditor terminal classifications:
Material findings and disposition:
External conditions / limitations:
Working-tree scope:
Completion: COMPLETE | BLOCKED | PARTIAL
```

Count `0`이면:

```text
Auditor Count: 0
Concurrent audit coverage: Not requested and not performed
```

Count `1~3`인데 일부 slot이 terminal classification을 반환하지 못하면 configured audit coverage를 완료로 보고하지 않는다.
