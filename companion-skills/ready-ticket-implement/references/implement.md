# IMPLEMENT 실행 계약

## 1. Invocation과 입력 고정

다음을 확보한다.

- Ticket path와 Project Root
- 현재 추가 사용자 지시
- exact Ticket top metadata `Status:`
- baseline revision과 baseline working-tree 상태
- top-level invocation인지, direct parent가 `Delegated Worker: yes`로 할당한 worker invocation인지

정상 Ticket 상태는 exact `ready`다. `done`이면 재구현하지 않고 현재 terminal marker를 보고한다. `draft` 또는 `blocked`이면 delivery를 시작하지 않는다.

## 2. Direct-first execution topology

Top-level invocation은 `DIRECT`가 기본이다. 현재 사용자가 이 exact implementation stage에 `SUBAGENT`를 명시한 경우에만 `SUBAGENT`를 사용한다. 모델 capability, 작업 난도, 비용 또는 worker availability만으로 mode를 바꾸지 않으며 `DIRECT`와 `SUBAGENT` 사이의 자동 전환이나 실패 후 fallback은 없다.

`DIRECT`에서는 현재 Main이 아래 implementation core를 직접 수행하고 다시 위임하지 않는다.

`SUBAGENT`에서 Outer Main은:

1. 한 명의 non-blocking implementation worker를 시작할 capability, 같은 Project Root 접근, parent-directed message와 terminal result capability를 확인한다.
2. exact Ticket, Project Root, 추가 사용자 지시와 `Delegated Worker: yes`를 하나의 완전한 assignment에 담는다.
3. worker assignment에 exact targets, Scope/Non-Goals, 요구되는 observable evidence와 다음 communication contract를 포함한다.
4. worker의 handoff/turn report를 수신하고, 새로운 사용자 지시나 decision-critical evidence가 있을 때만 steering한다.
5. terminal `IMPLEMENT RESULT`를 수신해 exact Ticket identity와 필수 terminal fields를 확인한 뒤 caller-facing 결과를 작성한다.

```text
# Communication

- Contract preflight가 닫힌 뒤 첫 source-file 변경 전에 direct parent에게 IMPLEMENTATION HANDOFF REPORT를 non-blocking으로 보낸다.
- 보고 후 acknowledgement나 approval을 기다리지 않고 안전한 구현을 계속한다.
- Initial interpretation, authority mapping, change surface 또는 evidence strategy가 material하게 바뀌는 경우에만 IMPLEMENTATION TURN REPORT를 보낸다.
- 정상 진행, 단순 tool activity, 일시적 test failure, 스타일 또는 내부 리팩터링은 보고하지 않는다.
- Parent/user authority가 필요한 unresolved decision에서는 live wait를 만들지 말고 evidence와 exact blocker를 포함한 terminal BLOCKED result를 반환한다.
- 성공 또는 blocker는 반드시 terminal IMPLEMENT RESULT로 끝낸다.
```

필요 capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 보고한다. `DIRECT`로 자동 전환하지 않는다.

`Delegated Worker: yes`를 받은 worker는 아래 implementation core를 직접 수행하며 다시 위임하지 않는다.

## 3. Contract preflight

첫 source-file 변경 전에:

1. Ticket 전체와 연결된 Parent Spec, Behavior/UI Authority, constraints와 references를 읽는다.
2. 한 문장으로 observable product outcome을 적는다.
3. 각 authored Verification flow의 initial state, trigger, acceptance boundary, expected result, authoritative readback, decision boundary와 disposition을 정리한다.
4. Scope와 Non-Goals에서 생겨야 하는 것과 생기면 안 되는 것을 분리한다.
5. Authored independent-verification requirement가 있으면 그 존재와 원문 의미를 기록하고, separate verification authority에 넘길 implementation/self-check evidence를 식별한다. 이 단계에서 충족 여부를 판정하지 않는다.
6. Repository/runtime에서 현재 behavior, entry point, test surface와 직접 readback을 확인한다.
7. Pre-existing working-tree change가 있으면 이번 Ticket delta와 분리 가능한 baseline을 기록한다.
8. 첫 source change가 observable product outcome 또는 승인된 invariant와 직접 연결되는지 확인한다.

실질적 authority 충돌이나 canonical source 부재로 faithful implementation direction을 확정할 수 없으면 임의 선택하지 않고 `Completion: BLOCKED`로 종료한다.

## 4. Implementation handoff report

Delegated worker는 contract preflight 직후, 첫 source-file 변경 전에 다음 보고를 direct parent에게 non-blocking으로 보낸다.

```text
IMPLEMENTATION HANDOFF REPORT

Ticket:
Baseline:
Observable product outcome:
Authority / Verification-flow anchors:
Expected change surface:
Authoritative readback / self-check target:
Material uncertainty: None | <exact uncertainty>
```

이 보고는 approval gate가 아니다. Outer Main이 실제 material contradiction이나 최신 사용자 지시를 발견하면 running worker에게 steering할 수 있지만, routine acknowledgement는 필요하지 않다.

`DIRECT`에서는 같은 내용을 implementation preflight record로 유지하되 parent message는 `NOT APPLICABLE`이다.

## 5. 구현

### 제품 결과 중심

- 내부 구조보다 observable outcome을 먼저 고정한다.
- Ticket이 고정하지 않은 구현 세부는 repository의 기존 product vocabulary와 architecture를 따른다.
- 스킬 메타 용어를 제품 도메인에 투사하지 않는다.
- 최소 변경, 단순성, 속도, 가역성은 사용자 결과에 미치는 실제 영향 안에서만 비교한다.

### 구현 필요성·충분성 관문

Ticket의 observable product outcome, Scope/Non-Goals, 적용되는 product invariant와 모든 authored Verification-flow obligation을 필수 구현 분모로 고정한다. 이 관문은 필수 결과, 경계, authoritative readback, self-check 또는 evidence를 생략·약화하거나 Ticket 의미를 재해석하는 데 사용할 수 없다.

각 재량적 코드 변경, 추상화, 리팩터링, 방어장치, 상태 저장, 추가 interface 또는 observability surface는 현재 canonical product contract에 대한 직접적인 anchor가 있거나, 추가하지 않을 경우 계약 달성을 방해하는 구체적이고 현실적인 실패 경로가 있어야 한다.

기존 동작이 이미 의무를 충족하면 그 동작을 보존하고 직접 evidence로 확인한다. 이론적 가능성, 미래 확장, 더 깔끔한 구조, 일반적인 hardening 또는 test 편의만으로 제품 변경을 추가하지 않는다.

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

## 6. Material turn report

Delegated worker는 다음 중 하나가 실제로 발생해 초기 handoff의 방향을 material하게 바꾸는 경우에만 보고한다.

- repository/runtime 직접 evidence가 initial product interpretation 또는 authority mapping을 뒤집는다.
- expected change surface가 다른 component, interface, persistence boundary 또는 user-visible surface로 material하게 이동한다.
- self-check 결과가 단순 결함 수정이 아니라 구현 strategy 또는 cross-flow/cross-AC meaning 변경을 요구한다.
- target identity, external condition 또는 authoritative readback strategy가 더 이상 attributable하지 않다.
- 최신 사용자 지시가 현재 implementation direction을 변경·축소·취소한다.

```text
IMPLEMENTATION TURN REPORT

Ticket:
Turn:
Previous direction:
New direct evidence:
Material change:
Affected flow / authority / scope:
Safe work continuing:
Parent action needed: NONE | STEERING | USER/AUTHORITY DECISION
```

`Parent action needed: NONE | STEERING`이면 safe work를 계속한다. 사용자나 parent authority가 없이는 진행할 수 없으면 추가 대기를 만들지 않고 terminal `Completion: BLOCKED`로 닫는다.

## 7. Completion self-check

Completion candidate 전에:

- intended product outcome과 authoritative readback을 확인한다.
- Scope/Non-Goals를 다시 읽는다.
- 모든 authored Verification-flow obligation에 연결된 tests/runtime evidence를 실행한다.
- pre-existing diff와 Ticket delta를 분리한다.
- limitation, external condition, inconclusive evidence와 unresolved authority conflict를 기록한다.
- decision-critical source claim, diff, artifact, command와 runtime behavior를 worker가 직접 확인한다.

Required implementation, self-check와 evidence가 닫히면 Ticket과 무관한 개선을 계속하지 않는다.

## 8. Ticket status handoff

이 스킬은 exact Ticket의 top metadata `Status:`를 변경하지 않는다. 정상 구현 입력인 `ready`는 `Completion: COMPLETE` 뒤에도 `ready`로 유지한다.

- `done`은 separate verification authority가 최종 verdict에 따라 소유하는 terminal delivery marker다.
- 구현 완료, passing tests 또는 implementer self-check만으로 `done`을 쓰지 않는다.
- Spec, Scope, Increment, AC, Verification flow, Behavior/UI Authority 또는 다른 planning source를 수정하지 않는다.
- separate verification authority가 사용할 exact implementation target/checkpoint와 self-check/runtime evidence를 handoff한다.
- 이후 verification이나 planning continuation을 자동 실행하지 않는다.

## 9. 종료 보고

```text
IMPLEMENT RESULT

Ticket:
Execution Mode: SUBAGENT | DIRECT
Worker identity: <delegated worker identity> | DIRECT
Ticket Status: ready (unchanged; separate verification authority owns terminal done) | unchanged because implementation did not run
Observable product outcome:
Implemented scope:
Non-Goals preserved:
Verification flows used for implementation/self-check:
Authoritative readback:
Separate verification authority required:
Verification status: NOT ADJUDICATED BY THIS SKILL
Verification evidence handoff:
Tests/runtime evidence:
Implementation handoff report: SENT | NOT APPLICABLE
Material turn reports: None | <concise list>
External conditions / limitations:
Working-tree scope:
Completion: COMPLETE | BLOCKED | PARTIAL
```
