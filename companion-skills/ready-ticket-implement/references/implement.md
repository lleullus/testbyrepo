# IMPLEMENT 실행 계약

## 1. Invocation과 입력 고정

다음을 확보한다.

- Ticket path와 Project Root
- 현재 추가 사용자 지시
- exact Ticket top metadata `Status:`
- baseline revision과 baseline working-tree 상태
- top-level invocation인지, direct parent가 `Delegated Worker: yes`로 할당한 worker invocation인지
- exact outside-root `Plan Review` (`plan_review_path`)와 실제 독립 reviewer invocation/evidence. 없으면 제품 mutation/assignment 전에 `ready-ticket-plan` 준비를 수행/요청한다.

정상 Ticket 상태는 exact `ready`다. `done`이면 재구현하지 않고 현재 terminal marker를 보고한다. `draft` 또는 `blocked`이면 delivery를 시작하지 않는다.

## 2. Subagent-first execution topology

Top-level invocation은 `SUBAGENT`가 기본이다. 현재 사용자가 이 exact implementation stage에 `DIRECT`를 명시한 경우에만 `DIRECT`를 사용하며, 기본 모드 사용을 위한 별도 SUBAGENT 승인을 요구하지 않는다. 모델 capability, 작업 난도, 비용 또는 worker availability만으로 mode를 바꾸지 않으며 `DIRECT`와 `SUBAGENT` 사이의 자동 전환이나 실패 후 fallback은 없다. 이 기본값은 top-level invocation에만 적용한다. `Delegated Worker: yes`를 받은 worker는 이미 할당된 implementation core를 직접 수행하고 다시 위임하지 않는다.

`DIRECT`에서는 현재 Main이 아래 implementation core를 직접 수행하고 다시 위임하지 않는다.

`SUBAGENT`에서 Outer Main은:

1. 한 명의 implementation worker를 시작할 capability와 같은 Project Root 접근, terminal result 회수 capability를 확인한다.
2. exact Ticket, Project Root, current `plan_review_path`, 추가 사용자 지시와 `Delegated Worker: yes`를 하나의 완전한 assignment에 담는다.
3. worker assignment에 exact targets, Scope/Non-Goals, 요구되는 observable evidence와 다음 communication contract를 포함한다.
4. material method change terminal을 받으면 old worker를 resume하지 않고 affected Plan revision → Heuristic → independent review를 실제로 수행한 뒤 fresh worker invocation으로만 재개한다.
5. terminal `IMPLEMENT RESULT`를 수신해 exact Ticket identity와 필수 terminal fields를 확인한 뒤 caller-facing 결과를 작성한다.

```text
# Communication

- actual implementing actor가 첫 source mutation 전에 ready_contract check_plan_admission으로 현재 ADMIT을 직접 확인한다.
- 현재 ADMIT과 load-bearing 전제 확인 뒤 검토된 범위에서 바로 시작한다. 정상 첫 source 변경의 PRE_ACTION 재심사는 없다.
- 중요한 원인, owner, interface, persistence, authoritative readback 또는 non-idempotent effect strategy가 바뀌면 새 방향에 의존한 mutation을 멈추고 terminal PARTIAL/BLOCKED material-method result를 반환한다.
- 정상 진행, 단순 tool activity, settled test failure, 스타일 또는 동등한 내부 리팩터링은 별도 checkpoint 사유가 아니다.
- actual external effect의 response loss는 blind replay하지 않고 approved authoritative readback/cleanup/evidence로만 정착 여부를 판단한다.
- 성공 또는 blocker는 반드시 terminal IMPLEMENT RESULT로 끝내며 COMPLETE 직전 같은 review로 admission을 재확인한다.
```

필요 capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 보고한다. `DIRECT`로 자동 전환하지 않는다.

`Delegated Worker: yes`를 받은 worker는 아래 implementation core를 직접 수행하며 다시 위임하지 않는다.

### SUBAGENT ownership and settlement

`SUBAGENT`는 exact Ticket과 같은 mutable worktree에 한 시점에 하나의 implementation owner만 둔다. 이 규칙은 IIS execution DB나 lease가 아니라 caller/host process contract가 소유한다.

1. delegated owner는 assignment에 전달된 exact Ticket/Project Root/`plan_review_path`로 첫 mutation 전 admission을 직접 확인한다.
2. 정상 local failure/fix/retry는 worker가 같은 invocation 안에서 host-native tools로 수행한다.
3. material method change는 continuation checkpoint가 아니라 terminal `PARTIAL | BLOCKED`로 current invocation을 끝낸다.
4. old worker가 사라지거나 교체가 필요하면 host가 실제 process/session/work settlement를 확인하기 전에는 같은 mutable worktree에 replacement를 시작하지 않는다.
5. cancel/stop request의 receipt, job/session ID 또는 단순 응답 유실만으로 old worker 종료를 추정하지 않는다.
6. settlement를 증명할 수 없으면 current owner/caller가 `PARTIAL | BLOCKED`로 반환한다. 병렬 작업이 필요하면 caller가 별도 isolated worktree를 사용한다.
7. fresh replacement는 current `plan_review_path`로 admission부터 다시 수행한다. `DIRECT`와 `SUBAGENT` 사이의 자동 fallback은 없다.

### Passive terminal fan-in

After one background implementation owner is successfully dispatched, Outer Main does not poll normal progress or completion. It does not call `hub wait`, `hub jobs`, `hub list` or `hub inbox`, send a status request, or duplicate repository inspection solely to observe that owner. It yields/stands by once and lets the host-delivered async terminal result wake the parent; only then does it validate and route the exact `IMPLEMENT RESULT`.

A single bounded diagnostic snapshot is allowed only for an explicit current user status request, cancellation/stop request, host-reported timeout/failure, malformed or missing expected terminal delivery, or a real need to establish worker replacement/settlement. If the snapshot shows normal execution, do not start periodic monitoring; return to passive terminal fan-in. This changes no worker ownership: local test failure/fix/retry and ordinary progress remain inside the implementation invocation.

Detached child, background delivery queue, polling controller 또는 persistent IIS execution scheduler로 ownership을 넘기지 않는다. IIS boundary tools는 worker/session/assignment state를 생성하거나 소비하지 않는다.

### Ready contract admission과 host-native execution

Skill/reference 조회, read-only `ready_contract inspect_authority`, 준비 artifact 작성은 implementation admission이 아니다. actual implementing actor의 `ready_contract check_plan_admission` 성공이 첫 source mutation 전 경계다. 이 check는 pinned canonical validator를 사용해 current Ticket/authority/Plan/Review bytes를 다시 묶고 제품/실행 상태를 쓰지 않는다.

- `DIRECT`와 `SUBAGENT` 모두 actual implementing actor가 exact Ticket/Project Root/`plan_review_path`로 `check_plan_admission`을 직접 호출한다. Parent가 execution/assignment/reservation을 만들지 않는다.
- 누락 `PLAN_REVIEW_REQUIRED`, stale `PLAN_REVIEW_STALE`, 미허가 `PLAN_NOT_ADMITTED`를 실제 결과 그대로 보존한다. field 존재나 fixture JSON은 독립 검토의 의미 증거가 아니며 worker는 결과를 합성/승격하지 않는다.
- admission 뒤에는 host-native read/search/edit/write/test/build/lint/CLI를 사용한다. IIS가 shell/argv grammar나 일반 tool dispatch를 재구현하지 않는다. settled nonzero는 command failure일 뿐 generic effect uncertainty가 아니며, worker는 결과를 읽고 Plan 범위 안에서 수정·재실행할 수 있다.
- ephemeral service가 필요하면 host-native service/process surface를 사용하고 실제 handle/generation/readiness/settlement를 직접 확인한다. shared/pre-existing service를 임의로 adoption/stop하지 않으며 start timeout이나 cancel receipt를 settlement로 과대해석하지 않는다.
- actual non-idempotent/external effect가 timeout/abort/response loss로 불명확하면 같은 effect를 blind replay하지 않는다. Ticket/Plan이 승인한 authoritative readback을 수행하고 cleanup/log/evidence 작성은 막지 않는다. readback으로 applied/not-applied가 확인되면 그 사실에 맞춰 계속한다. 확인 불가이면 그 effect에 의존하는 후속 mutation을 멈추고 exact evidence gap과 함께 `PARTIAL | BLOCKED`로 반환한다.
- generic execution-uncertainty phase, mutation-resolution API, operation reservation, recovery JSON, active-ticket/session/assignment lifecycle은 만들지 않는다. 필요한 evidence는 원래 제품/Plan/Verifier evidence surface에 남긴다.
- worker replacement는 host/caller 책임이다. old worker/process가 실제 종료됐다는 host evidence가 없으면 같은 mutable worktree에 fresh worker를 시작하지 않는다. settlement가 증명된 뒤 fresh worker는 current admission부터 다시 수행한다.
- `Completion: COMPLETE` 직전에 같은 `plan_review_path`로 `check_plan_admission`을 다시 호출하고 load-bearing source/runtime assumptions와 self-check evidence를 현재 상태로 재확인한다. Plan/authority stale이면 COMPLETE를 금지하고 `PARTIAL | BLOCKED`로 반환한다.

## 3. Contract preflight

첫 source-file 변경 전에:

1. Ticket 전체와 연결된 Parent Spec, Behavior/UI Authority, constraints와 references를 읽고 의미를 결합한다. `ready_contract check_plan_admission`이 exact Ticket과 적용되는 canonical Parent Spec/Behavior/UI Authority의 bounded identity를 current Plan Review와 함께 계산하며, 각 identity는 exact authority artifact 자체에 scoped되고 content-sensitive하다. repository-wide working-tree 변화 자체는 authority drift가 아니며 exact authority/Plan/Review artifact currentness를 구분한다.
2. 한 문장으로 observable product outcome을 적는다.
3. 각 authored Verification flow의 initial state, trigger, acceptance boundary, expected result, authoritative readback, decision boundary와 disposition을 정리한다.
4. Scope와 Non-Goals에서 생겨야 하는 것과 생기면 안 되는 것을 분리한다.
5. Authored independent-verification requirement가 있으면 그 존재와 원문 의미를 기록하고, separate verification authority에 넘길 implementation/self-check evidence를 식별한다. 이 단계에서 충족 여부를 판정하지 않는다.
6. 현재 제품 진입점부터 필요한 결과까지 경로를 추적해 이번 구현 소유 부분, 이미 존재하는 부분, 외부 소유 부분과 authoritative readback을 구분한다. 뒤늦게 틀리면 뒤따르는 구현을 무효화하는 전제는 그 전제에 의존한 확장 전에 가능한 가장 작은 실제 정상 경로로 확인한다. 확인 순서는 현재 제품 상태와 비용·권한·부작용에 따른다. 아직 없는 소유 경로는 먼저 만들 수 있으며, 모든 작업에 외부 호출을 선행시키지 않는다.
7. Pre-existing working-tree change가 있으면 이번 Ticket delta와 분리 가능한 baseline을 기록한다.
8. 첫 source change가 observable product outcome 또는 승인된 invariant와 직접 연결되는지 확인한다.

실질적 authority 충돌이나 canonical source 부재로 faithful implementation direction을 확정할 수 없으면 임의 선택하지 않고 `Completion: BLOCKED`로 종료한다.

자격증명·운영자 동작은 승인된 기존 경로만 사용한다. 필수 외부 조건이 없으면 정확한 미확인 경계와 허용된 다음 행동을 기존 preflight record에 남긴다. 그 조건에 의존하지 않는 안전한 내부 구현은 계속할 수 있지만, Mock·권한 우회·내부 성공으로 미확인을 닫거나 최종 제품 성공을 주장하지 않는다.

## 4. Current plan, conditional start and resynchronization

검토된 계획을 다시 설계하거나 최초 source 변경 앞에 정상 PRE_ACTION 재심사를 만들지 않는다. current ADMIT은 제품 성공이 아니며 plan/authority hash 일치만으로 source/search/runtime 전제가 현재라고 단정하지 않는다. 첫 의존 변경 전에 계획의 load-bearing anchors, 검색 범위, 동적 전제와 현재 user/Scope를 직접 확인한다. 기존 증거가 현재면 재사용한다.

조건부 ADMIT의 `permitted_initial_work`만 먼저 수행하고 `discriminating_observation`을 얻는다. 지지하면 이미 검토된 의존 방향으로 새 Parent 승인 없이 진행한다. 반증이면 `response_if_refuted`에 따라 영향 작업을 멈추고 Planner로 반환한다. 불충분이면 `dependent_work_not_yet_permitted`로 확장하지 않는다. 안전한 비의존 작업은 shared state/interface/effect 독립성이 실제로 설명되는 경우에만 계속한다.

명명, private helper, 동등한 국소 수정은 worker 재량이다. 중요한 원인/owner/interface/persistence/readback/effect 변경은 current invocation에서 새 방향에 의존한 mutation을 중단하고 terminal `PARTIAL | BLOCKED`로 반환한 뒤 Planner 수정 → 영향 Heuristic → independent review → fresh actor admission을 요구한다. 제품 의미 변경은 원 planning authority로 반환한다. worker가 bound Plan을 직접 고쳐 gate를 맞추지 않는다.

material method change를 보고받은 caller는 old review가 byte-current하다는 이유만으로 그대로 재사용해 fresh worker를 시작하지 않는다. affected Plan을 실제로 수정하고 Heuristic/Independent Review를 다시 거친 후 새 `plan_review_path`로 fresh implementation invocation을 시작한다.

exact Ticket/Parent Spec/Behavior/UI authority drift, authoritative readback의 unavailable/non-attributable 상태 또는 대체 필요가 확인되면 영향 작업을 즉시 멈춘다. 원 권위 안에서 faithful direction/readback을 재확정하고 필요한 review를 갱신할 수 없으면 BLOCKED다. readback 약화나 새 제품 의미를 caller 승인으로 만들지 않는다. 일반 repository 변경과 제품 authority drift는 구분한다.

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

## 6. Material method change terminal

Worker는 다음 중 하나가 실제로 발생해 current reviewed 방향의 load-bearing method를 바꾸는 경우에만 새 방향에 의존한 mutation을 멈추고 current invocation을 terminal로 반환한다.

- repository/runtime 직접 evidence가 initial root cause 또는 authority mapping을 뒤집는다.
- expected owner/change surface가 다른 component, shared interface, persistence boundary 또는 user-visible surface로 material하게 이동한다.
- self-check 결과가 단순 결함 수정이 아니라 구현 strategy 또는 cross-flow/cross-AC meaning 변경을 요구한다.
- target identity, external condition 또는 authoritative readback strategy가 더 이상 attributable하지 않다.
- non-idempotent/external effect strategy가 reviewed Plan과 달라져야 한다.
- 최신 사용자 지시가 현재 implementation direction을 변경·축소·취소한다.

```text
IMPLEMENTATION TURN / PARTIAL

Ticket:
Completion: PARTIAL | BLOCKED
Material method change: yes
Reviewed direction:
New direct evidence:
Affected plan scope:
Current working-tree state:
Next allowed action: revise affected Plan -> Heuristic -> independent review
```

이 result로 current invocation은 끝난다. Parent `CONTINUE`나 runtime release로 same child를 살려두지 않는다. caller는 affected Plan을 실제로 수정하고 Heuristic/Independent Review를 다시 수행한 뒤 fresh worker를 시작한다. 해결 불가 authority/readback blocker이거나 external effect 정착 여부를 확인할 수 없으면 exact evidence gap을 포함해 `BLOCKED | PARTIAL`로 닫고 성공을 추측하지 않는다.

## 7. Completion self-check

Completion candidate 전에:

- mode와 관계없이 현재 exact Ticket/Parent Spec/Behavior/UI, current review, actual target 및 authoritative readback을 다시 확인한다. 같은 `plan_review_path`로 `ready_contract check_plan_admission`을 재호출하며 drift, unavailable/non-attributable readback 또는 substitution은 위 current plan/resynchronization 경계를 따른다. DIRECT와 SUBAGENT 모두 이 end admission을 건너뛰지 않는다.
- Scope/Non-Goals를 다시 읽는다.
- 모든 authored Verification-flow obligation에 연결된 tests/runtime evidence를 실행한다.
- pre-existing diff와 Ticket delta를 분리한다.
- limitation, external condition, inconclusive evidence와 unresolved authority conflict를 기록한다.
- decision-critical source claim, diff, artifact, command와 runtime behavior를 worker가 직접 확인한다.

Required implementation, self-check와 evidence가 닫히면 Ticket과 무관한 개선을 계속하지 않는다.

## 8. Ticket status handoff

이 스킬은 exact Ticket의 top metadata `Status:`를 변경하지 않는다. 정상 구현 입력인 `ready`는 `Completion: COMPLETE` 뒤에도 `ready`로 유지한다.

- `done`은 separate verifier의 semantic verdict를 받은 뒤 caller가 `ready_finalize`로 수행하는 terminal delivery progression이다. implementation worker는 직접 쓰지 않는다.
- 구현 완료, passing tests 또는 implementer self-check만으로 `done`을 쓰지 않는다.
- Spec, Scope, Increment, AC, Verification flow, Behavior/UI Authority 또는 다른 planning source를 수정하지 않는다.
- final verifier가 사용할 exact actual implementation target/checkpoint, self-check/runtime evidence, 해당하는 plan/review navigation을 보존한다.
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
Material method change: no | yes
Plan admission at completion: CURRENT | <actual failure>
External conditions / limitations:
Working-tree scope:
Completion: COMPLETE | BLOCKED | PARTIAL
```

### Non-continuation provenance

`Completion: BLOCKED | PARTIAL`이 현재 owner가 admission·권위·readback·target currentness·external-effect uncertainty·material method change 때문에 계속할 수 없음을 나타낼 때, 또는 `SUBAGENT CAPABILITY UNAVAILABLE`로 반환할 때 기존 결과 뒤에 다음 다섯 필드를 붙인다. 기존 owner 결과를 유지하며 이 블록은 새 상태가 아니다. 실행 전 반환에 아직 얻지 않은 Completion/runtime evidence를 채워 넣지 않는다.

```text
Decision: <exact existing Completion result or SUBAGENT CAPABILITY UNAVAILABLE>
Governing authority: ready-ticket-implement / <stable section or rule>
Observed condition: <직접 확인된 blocker, capability boundary, unavailable/non-attributable readback, authority drift, or checkpoint STOP condition>
Effect: <COMPLETE를 주장할 수 없는 이유와 보호되는 다음 mutation/phase>
Next allowed action: <exact caller/owner action needed to resume, or None>
```

도구·transport·protocol 실패만 관찰된 경우 그 실패 자체만 `Observed condition`으로 기록하고 product/repository 상태 원인을 추측하지 않는다. 정상 `COMPLETE` 또는 단순 implementation finding에는 provenance 블록을 추가하지 않는다.
