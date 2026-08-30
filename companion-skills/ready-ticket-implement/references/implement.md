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

1. 한 명의 implementation worker를 시작할 capability, 같은 Project Root 접근, checkpoint return/continuation과 terminal result capability를 확인한다.
2. exact Ticket, Project Root, 추가 사용자 지시와 `Delegated Worker: yes`를 하나의 완전한 assignment에 담는다.
3. worker assignment에 exact targets, Scope/Non-Goals, 요구되는 observable evidence와 다음 communication contract를 포함한다.
4. worker의 checkpoint report를 수신하고 `CONTINUE | STEER | STOP` 중 하나의 bounded continuation decision을 반환한다.
5. terminal `IMPLEMENT RESULT`를 수신해 exact Ticket identity와 필수 terminal fields를 확인한 뒤 caller-facing 결과를 작성한다.

```text
# Communication

- Contract preflight가 닫힌 뒤 첫 source-file 변경 전에 direct parent에게 IMPLEMENTATION HANDOFF REPORT를 PRE_ACTION checkpoint로 반환한다.
- Parent continuation decision 전에는 Protected next phase인 FIRST_SOURCE_FILE_CHANGE를 넘지 않는다.
- Initial interpretation, authority mapping, change surface 또는 evidence strategy가 material하게 바뀌는 경우에만 IMPLEMENTATION TURN REPORT를 보낸다.
- 정상 진행, 단순 tool activity, 일시적 test failure, 스타일 또는 내부 리팩터링은 보고하지 않는다.
- Material-turn report 뒤에는 새 방향에 의존하는 작업을 Parent continuation decision 전에 진행하지 않는다.
- Parent/user authority가 필요한 unresolved decision이 bounded continuation으로 해결될 수 없으면 evidence와 exact blocker를 포함한 terminal BLOCKED result를 반환한다.
- 성공 또는 blocker는 반드시 terminal IMPLEMENT RESULT로 끝낸다.
```

필요 capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 보고한다. `DIRECT`로 자동 전환하지 않는다.

`Delegated Worker: yes`를 받은 worker는 아래 implementation core를 직접 수행하며 다시 위임하지 않는다.

### SUBAGENT checkpoint continuation

`SUBAGENT` checkpoint는 logical phase boundary다. required live-wait primitive, direct-user approval gate 또는 durable workflow state가 아니다.

Checkpoint에서는 다음을 지킨다.

1. delegated owner는 완전한 checkpoint report를 Parent Main에게 반환한다.
2. report에 적힌 `Protected next phase`를 Parent decision 전에 넘어가지 않는다.
3. Parent Main은 정확히 하나를 반환한다.
   - `CONTINUE`: 현재 방향으로 보호된 다음 phase 진입을 허용한다.
   - `STEER`: exact authority/evidence anchor를 가진 bounded correction을 전달한다. decision-critical 내용이 바뀌면 worker는 같은 checkpoint를 갱신해 다시 반환한다.
   - `STOP`: 보호된 다음 phase로 진입하지 않고 기존 `BLOCKED | PARTIAL` owner terminal 형식으로 pass를 닫는다.
4. 동일 Ticket과 implementation stage에는 한 시점에 정확히 하나의 delegated owner lane만 존재한다.
5. 동일한 checkpoint를 material delta 없이 반복하거나 periodic progress checkpoint로 사용하지 않는다.
6. checkpoint continuation capability가 없으면 `SUBAGENT CAPABILITY UNAVAILABLE`을 반환한다.
7. `DIRECT`로 자동 fallback하지 않는다.

Continuation은 특정 harness API를 제품 계약으로 요구하지 않는다. 다만 runtime assignment는 exact Ticket/Project Root와 정확히 한 child session에 one-use로 bind되고 parent는 checkpoint와 terminal result를 회수하는 joined lifecycle을 유지한다. detached child, background delivery queue, polling controller 또는 persistent execution scheduler로 continuation을 넘기지 않는다. 핵심 규칙은 `Parent decision 전에는 protected next phase로 넘어가지 않는다`이다.

### Ready runtime binding

`ready-ticket-implement`를 읽으면 current session은 runtime에서 ARMED된다. 외부 invocation 입력은 바꾸지 않는다.

- `DIRECT`: contract preflight 전에 exact Ticket과 Project Root로 `ready_guard begin_direct`를 호출한다.
- `SUBAGENT`: Outer Main이 `ready_guard assign_subagent`로 exact assignment를 만들고, 지정된 한 worker가 그 `assignment_id`로 `ready_guard begin_delegated`를 호출한다.
- runtime이 current `iis-workflow`의 To Tickets route와 exact validator, Ticket status, Parent Spec, applicable Behavior/UI Authority, Git/worktree identity를 직접 bind한다. worker가 digest를 제출해 runtime에 신뢰시키지 않는다.
- runtime은 Project Root confinement, protected authority mutation, observation ledger, broad inventory, mutation revision/current evidence, retry classification, operation lock과 managed local service를 소유한다. 이 내부 state는 product authority나 caller-facing Ready result가 아니다.
- native Bash가 구조적으로 read-only임을 확인할 수 없으면 자유 shell string을 추측하지 않는다. 필요한 write-capable command는 explicit `ready_argv mutate`의 argv와 target paths로 실행한다.
- terminal owner는 기존 `IMPLEMENT RESULT`를 내기 전에 runtime을 `complete` 또는 `block`으로 닫는다. runtime debug/state는 기존 result의 새 필수 field가 아니다.

### Zero-Mock Delivery runtime invariant

`ready-ticket-implement`의 implementation/self-check evidence는 mock-free여야 한다. basename이나 본문의 이름 언급을 provenance로 보지 않고, Python/JS/TS structural import closure와 JS/TS global/member/destructuring/alias flow를 따르는 mocking/interception API 정적 검사 및 actual execution provenance를 함께 사용한다.

금지 대상:

- mock/fake/stub implementation과 `unittest.mock`, pytest `monkeypatch`/`mocker`, Jest/Vitest mock/spy API, Sinon 등 dependency patching
- HTTP/provider interception (`responses`, `requests_mock`, `respx`, `nock`, `msw`, MockAgent 등)
- fake/in-memory repository/database/provider와 mock mode 환경변수
- fake response, intercepted response 또는 mock-tainted test 결과를 authoritative evidence로 승격하는 행위

허용 대상은 실제 production entrypoint, 실제 dependency/config/schema/persistence, 임시 디렉터리, 격리된 실제 DB/container와 단순 seed data다.

Runtime enforcement:

1. native/edit/write 및 structured mutation 전 prospective input에서 명시적 mock 도입/활성화를 차단한다.
2. mutation result 후 실제 target의 Python/JS/TS structural local import closure를 재스캔하며 JS/TS runtime global·static member·destructuring·alias flow나 import/require alias/wrapper가 이름을 바꿔 mock API를 감싸도 taint를 기록한다. basename 또는 text mention만으로 dependency/provenance를 인정하지 않는다.
3. acceptance test는 오직 `ready_argv acceptance`로 실행하고 `provenance_kind`를 정확히 `LOCAL_PATH`, `LOCAL_SQLITE`, `EXTERNAL_HTTP_PROVIDER` 중 하나로 지정한다. 지원되는 standard Python/JS test runner 또는 shell-control 없는 package script만 허용하며, resolved argv에서 계산한 selected test roots와 `evidence_paths`가 exact canonical set으로 일치하지 않거나 selector가 ambiguous/unsupported이면 fail-closed한다. package runner는 original/resolved argv와 `package.json`을 fingerprint하고 exact adjacent `pre<name>`/`post<name>` lifecycle hook이 configured이면 실행 전에 차단한다. unknown custom runner/MCP execution은 verifiable provenance가 없으면 fail-closed한다.
4. clean local PASS provenance는 original/resolved 실행 argv, production/evidence structural import closure, actual dependency/config, authoritative readback, runner config와 current mutation revision의 전체 fingerprint 및 `mock_taint: false`를 기록한다.
5. 현재 runtime은 `EXTERNAL_HTTP_PROVIDER` 실행과 readback correlation을 지원하지 않는다. 이 kind에서는 command/readback argv를 실행하지 않고 acceptance를 `INCONCLUSIVE`로 기록하며 implementation은 기존 `Completion: BLOCKED`로 닫는다.
6. `ready_guard complete`는 non-empty acceptance provenance denominator의 모든 entry가 clean인지 요구하고 각각의 전체 fingerprint를 current selected-test-root/`evidence_paths` binding, production/evidence import closures, dependency/config, authoritative readback, runner config와 mutation revision에서 재계산한다. 일반 read-only observation은 이 denominator를 대체하지 않으며 mismatch·persistent violation·non-passing provenance가 있으면 COMPLETE를 차단한다.

## 3. Contract preflight

첫 source-file 변경 전에:

1. Ticket 전체와 연결된 Parent Spec, Behavior/UI Authority, constraints와 references를 읽고 의미를 결합한다. runtime binding이 exact Ticket과 적용되는 canonical Parent Spec/Behavior/UI Authority의 bounded identity를 계산하며, 각 identity는 exact authority artifact 자체에 scoped되고 content-sensitive하다. runtime은 canonical path + file/content SHA를 사용한다. repository-wide working-tree 변화는 authority drift로 취급하지 않으며 exact authority artifact currentness만 비교한다.
2. 한 문장으로 observable product outcome을 적는다.
3. 각 authored Verification flow의 initial state, trigger, acceptance boundary, expected result, authoritative readback, decision boundary와 disposition을 정리한다.
4. Scope와 Non-Goals에서 생겨야 하는 것과 생기면 안 되는 것을 분리한다.
5. Authored independent-verification requirement가 있으면 그 존재와 원문 의미를 기록하고, separate verification authority에 넘길 implementation/self-check evidence를 식별한다. 이 단계에서 충족 여부를 판정하지 않는다.
6. Repository/runtime에서 현재 behavior, entry point, test surface와 직접 readback을 확인한다.
7. Pre-existing working-tree change가 있으면 이번 Ticket delta와 분리 가능한 baseline을 기록한다.
8. 첫 source change가 observable product outcome 또는 승인된 invariant와 직접 연결되는지 확인한다.

실질적 authority 충돌이나 canonical source 부재로 faithful implementation direction을 확정할 수 없으면 임의 선택하지 않고 `Completion: BLOCKED`로 종료한다.

## 4. Implementation handoff report

Delegated worker는 contract preflight 직후, 첫 source-file 변경 전에 다음 보고를 direct parent에게 `PRE_ACTION` checkpoint로 반환한다.

```text
IMPLEMENTATION HANDOFF REPORT

Ticket:
Execution Mode: SUBAGENT
Worker identity:
Baseline:
Observable product outcome:
Authority / Verification-flow anchors:
Expected change surface:
Authoritative readback / self-check target:
Scope / Non-Goals boundary:
Material uncertainty: None | <exact uncertainty>

Checkpoint: PRE_ACTION
Protected next phase: FIRST_SOURCE_FILE_CHANGE
Checkpoint state: PARENT_CONTINUATION_REQUIRED
```

`Authority / Verification-flow anchors`에는 runtime이 bind한 exact Ticket과 적용되는 canonical parent authority의 bounded identity를 함께 보존한다. `Authoritative readback / self-check target`에는 completion evidence를 결정할 exact acceptance/readback target을 적는다. runtime의 persistent state는 실행 guard 내부에만 존재하며 이 report에 새 caller-facing snapshot, registry 또는 workflow contract를 추가하지 않는다.

이 checkpoint를 반환한 worker는 Parent decision 전에는 source 파일을 변경하지 않는다. Outer Main은 exact Ticket/assignment identity, observable outcome의 의미 보존, Scope/Non-Goals와 change surface, authoritative readback의 결정력, 명백한 authority mismatch나 unresolved blocker만 bounded하게 검토한다. Outer Main이 구현 방법을 다시 설계하거나 코드를 직접 구현하지 않는다.

`DIRECT`에서는 같은 내용을 implementation preflight record로 유지하되 `Checkpoint: NOT_APPLICABLE`이고 Parent continuation은 없다.

### 비재량 재동기화

`SUBAGENT`에서 `PRE_ACTION` 이후 아래 사실 중 하나가 확인되면 delegated worker는 자신의 materiality threshold를 적용하지 않는다. `PRE_ACTION`에서 Parent가 처음 release한 authority/readback anchor가 initial `Parent-released anchor`다.

1. exact Ticket 또는 적용되는 canonical Parent Spec/Behavior/UI Authority의 bounded identity가 current `Parent-released anchor`에서 달라졌다.
2. current `Parent-released anchor`에 선언된 authoritative readback이 completion evidence에 대해 unavailable 또는 non-attributable해졌거나, 계속하려면 다른 readback으로 substitution해야 한다.

해당 변화에 의존하는 작업은 즉시 멈춘다. 현재 canonical authority 안에서 faithful implementation direction과 결정력 있는 readback을 다시 확정할 수 있으면 기존 `MATERIAL_TURN` checkpoint를 반환하고 Parent `CONTINUE | STEER | STOP` 전에는 보호된 다음 phase로 넘어가지 않는다. Parent가 `CONTINUE`하면 그 checkpoint에서 재확정된 authority/readback identity가 invocation-local 최신 `Parent-released anchor`가 된다. `STEER`가 decision-critical 내용을 바꾸면 worker는 갱신된 같은 checkpoint를 다시 반환하고, 이후 Parent `CONTINUE`된 내용만 최신 anchor가 된다. `STOP` 또는 `Completion: BLOCKED`에서는 anchor를 갱신하지 않는다. 현재 authority 안에서 faithful direction 또는 결정력 있는 readback을 확정할 수 없으면 새 제품 의미나 약한 대체 readback을 Parent checkpoint로 승인받으려 하지 말고 `Completion: BLOCKED`로 닫는다.

이 규칙은 최초 `PRE_ACTION`을 provenance로 보존하되 currentness 비교는 최신 `Parent-released anchor`와 runtime authority binding을 사용한다. 새 checkpoint 종류나 caller-facing checkpoint ledger를 만들지 않고 periodic polling도 하지 않는다. runtime의 internal state machine/authority snapshot은 이 enforcement에만 쓰며 delivery contract나 제품 state로 노출하지 않는다. 같은 사실을 material delta 없이 반복 보고하지 않는다.

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
Current working-tree state:
Proposed new direction:

Checkpoint: MATERIAL_TURN
Protected next phase:
Checkpoint state: PARENT_CONTINUATION_REQUIRED
Work permitted before continuation: NONE
```

보고를 반환한 뒤에는 새 방향에 의존하는 작업을 계속하지 않는다. Parent가 `CONTINUE`하면 제안 방향으로 진행한다. `STEER`로 decision-critical 내용이 바뀌면 같은 `MATERIAL_TURN` checkpoint를 갱신해 다시 반환한다. `STOP` 또는 bounded continuation으로 해결할 수 없는 authority blocker면 terminal `Completion: BLOCKED` 또는 해당 owner terminal 형식으로 닫는다.

## 7. Completion self-check

Completion candidate 전에:

- `SUBAGENT`에서는 exact Ticket과 적용되는 canonical Parent Spec/Behavior/UI Authority의 현재 bounded identity를 다시 확인하고 최신 `Parent-released anchor`와 대조한다. drift가 있으면 `Completion: COMPLETE`를 내지 않고 위 비재량 재동기화 규칙을 적용한다. intended product outcome과 최신 anchor의 authoritative readback도 다시 확인하고, 그 readback이 unavailable/non-attributable하거나 substitution이 필요하면 같은 규칙을 적용한다.
- `DIRECT`에서는 Parent checkpoint나 `Parent-released anchor`를 만들지 않는다. 현재 Main이 exact Ticket과 적용되는 canonical Parent Spec/Behavior/UI Authority 및 authoritative readback을 직접 다시 결합한다. 현재 authority 안에서 faithful implementation direction과 결정력 있는 readback이 유지되면 기존 DIRECT self-check를 계속하고, 확정할 수 없으면 `Completion: BLOCKED`로 닫는다.
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
- separate heuristic-probe authority와 separate verification authority가 사용할 exact implementation target/checkpoint와 self-check/runtime evidence를 navigation handoff로 보존한다.
- 이후 heuristic probing, verification이나 planning continuation을 자동 실행하지 않는다.

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
Separate heuristic-probe authority required before normal verification: yes when verification is requested
Heuristic probe status: NOT RUN BY THIS SKILL
Separate verification authority required:
Verification status: NOT ADJUDICATED BY THIS SKILL
Heuristic-probe / verification evidence handoff:
Tests/runtime evidence:
Implementation handoff report: SENT | NOT APPLICABLE
Material turn reports: None | <concise list>
Checkpoint decisions:
- PRE_ACTION: CONTINUE | STEERED_THEN_CONTINUE | STOP | NOT_APPLICABLE
- MATERIAL_TURN: None | <turn -> decision>
External conditions / limitations:
Working-tree scope:
Completion: COMPLETE | BLOCKED | PARTIAL
```
