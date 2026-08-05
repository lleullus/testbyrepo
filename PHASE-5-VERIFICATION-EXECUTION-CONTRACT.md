# Phase 5 — Verification 실행

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

Phase 2의 `verify(candidate)`가 exact Candidate를 수정하지 않고, 구현과 분리된 fresh 관점에서
모든 Acceptance Criterion을 계획하고, 직접 source/evidence를 얻어 독립적인
`VerificationResult`를 만드는 방법을 정한다.

이번 단계의 단일 결정은 다음이다.

> Module은 fresh Verifier에게 exact planning/전체 AC와 immutable Candidate source만 제공해 모든
> AC의 필요한 관찰을 실행 전에 한 번 계획하게 한다. Evidence Runner는 그 고정된 관찰을 read-only
> source 또는 격리된 실행 환경에서 직접 수행하고 immutable evidence를 만든다. Verifier는 그
> evidence만으로 각 AC를 `SATISFIED`, `NOT_SATISFIED`, `UNDETERMINED` 중 하나로 판정한다.

이 결정은 현재 sealed plan/flow/step/actor/capability/ledger command를 caller에게 다시 제공하지
않는다. 계획 고정, runner-owned evidence, 완전한 AC coverage와 source currentness만 깊은 Module
안에 남긴다.

## 상속한 사용자 가치와 Interface

- caller Interface는 Phase 2의 `verify(candidate)` 하나이며 verifier, runner, plan, flow, step,
  capability 또는 evidence payload를 입력하지 않는다.
- Candidate는 exact planning/전체 AC와 다시 읽을 수 있는 immutable exact source에 결속된다.
- 검증은 구현 Worker, Implementation Lead의 check와 이전 verifier 결론을 상속하지 않는 fresh
  관점이어야 한다.
- 모든 AC가 정확히 한 번 결과에 나타나며, 각 결론적 판정은 planning이 요구한 관찰 수준의 직접
  evidence에 결속된다.
- runtime 결과·외부효과·readback이 필요한 AC는 source review, 구현 check나 Worker 서술로 대체하지
  않는다.
- evidence 부족·tool failure·identity/currentness 불명·authority 부족은 AC 불충족이 아니라
  `UNDETERMINED`다.
- 충분한 direct evidence가 AC 불충족을 보일 때만 `NOT_SATISFIED`다.
- verification은 canonical source와 retained Candidate source를 수정하지 않는다.
- source 수정이 필요하면 현재 verification이 Worker를 호출하지 않고 별도 `implement(work, worker)`가
  새 Candidate를 만든다.
- Phase 3의 한 active VERIFY transition과 atomic VerificationResult publication을 그대로 사용한다.

## user-facing Verification Lead session

Verification Lead itself is the user-facing lead session. It directly owns
scenario design, user-facing commentary, direct evidence acquisition, and AC
verdicts; it must not execute the Verification Lead role through a delegated
subagent. If a user-facing commentary channel is unavailable, Verification Lead
stops as `unsupported` before any direct evidence acquisition. This does not
prohibit the separate Remediation Agent delegation for directly evidenced
`NOT_SATISFIED` ACs. `unsupported` before acquisition is not a fourth AC result.

## 깊은 Module과 실제 Seam

Phase 2의 Implementation Verification Module 안에 **Verification Execution Module**을 둔다. 정상
caller는 이 Module을 직접 호출하지 않는다. 이 Module이 없어지면 fresh context 생성, 전체 AC
coverage, observation suitability, runner request 고정, evidence ownership, currentness와 aggregate
판정이 caller와 각 verifier에게 다시 퍼진다.

내부 seam은 두 곳이다.

1. **Fresh Verifier Adapter seam** — production에서는 이전 구현/검증 context를 받지 않는 새
   verifier를 만들고, test에서는 동일 입력만 받는 deterministic verifier를 사용한다. Verifier는
   observation plan과 evidence 해석을 소유하지만 실행 결과를 작성하거나 source를 수정하지 않는다.
2. **Evidence Runner Adapter seam** — fixed observation request를 실행하고 source slice, process result,
   rendered observation 또는 Phase 6 effect observation 같은 runner-owned evidence를 반환한다.
   production Adapter와 local test Adapter는 같은 read-only/evidence ownership 계약을 만족한다.

Phase 6이 정할 위험한 외부효과 Adapter는 Evidence Runner 내부의 제한된 후속 seam이다. Phase 5는
authorization, idempotency, correlation, retry/readback protocol을 정하지 않는다. 필요한 effect
observation을 Phase 6 Adapter가 안전하게 제공하지 못하면 해당 AC는 `UNDETERMINED`다.

## fresh 독립 검증 context

각 새 VERIFY transition은 fresh Verifier context를 한 번 만든다. 그 context에 제공할 수 있는 것은
다음뿐이다.

```text
exact Candidate와 retained Candidate source
Candidate에 결속된 exact planning과 전체 AC
현재 적용되는 repository/product authority
Evidence Runner가 지원하는 관찰 종류와 안전 한계
```

다음은 입력으로 제공하지 않는다.

- Worker/Implementation Lead의 성공 서술과 reasoning
- implementation check 결과와 provisional smoke
- 이전 VerificationResult의 verdict, rationale, observation plan과 evidence selection
- remediation 제안, patch 또는 구현 task accounting
- caller가 제안한 aggregate status나 유리한 evidence subset

Verifier는 source에 포함된 product test를 읽을 수 있지만, 그것이 구현자가 작성한 test라는 이유만으로
독립 evidence가 되지는 않는다. AC가 source-level observation만 요구하는 경우에는 direct source
evidence가 충분할 수 있다. 제품 동작을 요구하는 경우에는 public product surface를 fresh하게 실행해
관찰해야 한다.

`UNDETERMINED` 뒤 같은 Candidate를 다시 검증하면 새 transition과 새 Verifier context를 만들고 plan과
evidence를 처음부터 다시 얻는다. 이전 result, plan, rationale, artifact와 implementation check의
semantic content는 Module과 Phase 6 safety gate만 읽을 수 있고 fresh Verifier의 readable namespace에는
들어오지 않는다. safety gate는 이전 내용을 넘기지 않고 현재 observation이 `SUPPORTED`, `UNSAFE`,
`UNDETERMINED` 중 무엇인지라는 capability fact만 제공한다. 이전 result는 새 AC verdict의 evidence로
carry forward하지 않으며, Phase 6이 이전 ambiguous effect를 안전하지 않다고 판정하면 새 effect를
실행하지 않는다. 이 제한은 caller-visible actor/capability token이 아니라 내부 Adapter boundary다.

## immutable observation plan

Verification Lead itself, as the user-facing lead session, reads exact planning,
the full AC set, Candidate source, and the actual product entrypoint before
evidence-producing execution to make one bounded observation plan. This planning
inspection is permitted only to design scenarios. Its observations are not direct
AC evidence, must not be preserved or reused as direct AC evidence, and require a
new evidence observation after commentary emission even when the target is the
same. The plan is a Module-internal fact, not caller-visible `seal-run`, plan
digest, or flow/step ID.

After designing scenarios for every AC and before any direct evidence
acquisition, Verification Lead emits a user-facing commentary table headed
`Verification Scenarios`. Each scenario row contains a stable scenario ID, AC,
observation target, procedure and verification surface, expected result, direct
evidence to collect, and decision criteria. Completed commentary emission is a
precondition for evidence acquisition, not an approval gate. The table is a
human-readable projection of the internal immutable observation plan; it does not
elevate that plan into user-owned input, approval token, durable artifact, or
state machine. Verification Lead continues without waiting for confirmation unless
an existing authority, ambiguity, or effect-safety rule requires a user decision.

If a scenario changes before or during execution, Verification Lead stops using
the old scenario. Before any replacement direct evidence acquisition, it emits
user-facing commentary with a new stable replacement scenario ID and its
`replaces <old scenario ID>` relationship. Evidence acquired for the old scenario
remains bound to that scenario and must not be relabeled as replacement evidence.

plan은 최소한 다음 의미를 가진다.

```text
exact Candidate/planning/전체 AC binding
각 scenario의 stable scenario ID와 AC binding
각 AC가 요구하는 관찰 수준
ordered fixed observations
각 observation이 대상으로 하는 AC 집합
expected observable과 결론에 충분한 조건
source-only | isolated local execution | Phase-6-owned effect observation 구분
```

Module은 다음 조건을 만족할 때만 plan을 고정한다.

- 모든 exact AC가 정확히 한 번 coverage 계산에 포함된다.
- 각 AC에 적어도 하나의 direct observation obligation이 있다.
- 각 observation이 대상으로 하는 AC와 역방향 coverage가 일치한다.
- component check의 조합을 planning이 요구한 end-to-end product observation으로 가장하지 않는다.
- source-only AC에 불필요한 runtime action을 추가하지 않고, runtime AC를 source review로 축소하지 않는다.
- 각 scenario의 request, target, order와 expected observable이 첫 evidence acquisition 뒤 바뀌지
  않는다. 변경이 필요하면 기존 scenario 사용을 중단하고 새 replacement scenario로만 진행하며,
  replacement direct evidence acquisition 전에 user-facing commentary를 먼저 출력한다.
- 위험한 effect, cleanup, retention 또는 authoritative readback이 필요한 observation은 Phase 6 소유임을
  명시하고 임의 local command로 대체하지 않는다.

plan 고정 뒤 의미 누락이나 실행 중 변경이 발견되면 기존 scenario를 수정해 성공시키지 않는다. 기존
scenario 사용을 중단하고, 새 stable ID와 대체 관계를 가진 replacement scenario를 user-facing
commentary로 먼저 공개한 뒤에만 새 direct evidence observation을 수행한다. 기존 scenario에서 얻은
evidence는 해당 scenario에만 남으며 replacement evidence로 재표기하지 않는다. replacement를
공개하거나 실행할 수 없으면 영향받은 AC는 필요한 admissible direct evidence가 없으므로
`UNDETERMINED`다.

## Candidate read-only와 격리된 실행

Evidence Runner는 Phase 4가 retained한 exact Candidate source를 immutable input으로 사용한다.
canonical product source와 retained Candidate source 모두 Runner와 Verifier에게 write 불가여야 한다.

실행이 temporary file, build output, cache 또는 materialization을 필요로 하면 Candidate에서 만든 fresh
verification environment와 별도 writable scratch/output만 사용한다. Candidate source view는 그
environment 안에서도 read-only이며, writable overlay가 source path를 shadow하거나 바꾸어 보이게
해서는 안 된다. exact 구현은 read-only mount, read-only validated copy 또는 동등한 Adapter 선택이며
Interface가 아니다. 다음 의미는 고정한다.

- Candidate source bytes와 identity는 실행 전후 동일하다.
- verification environment는 이전 implementation check와 이전 verification run의 writable state를
  상속하지 않는다.
- writable output은 Candidate source namespace와 겹치지 않고, Candidate source로 자동 편입되지 않으며
  evidence artifact로만 취급한다.
- observation이 generated state에 의존하면 plan이 그 생성과 관찰을 하나의 direct product flow로
  고정해야 한다. 임의의 사후 component 결과를 합성하지 않는다.
- Runner 또는 도구가 canonical/retained source 쓰기를 시도하거나 격리를 입증하지 못하면 해당
  observation은 `UNDETERMINED`이고 source를 수정된 Candidate로 재분류하지 않는다.

Verifier는 source를 직접 수정할 권한이 없고 Evidence Runner 외의 process/browser/MCP 결과를
evidence로 제출할 수 없다.

## runner-owned evidence

Evidence Runner는 plan에 고정된 exact observation request만 받으며, 그 scenario의 user-facing
commentary emission이 완료된 뒤에만 direct evidence observation을 수행한다. planning inspection은
이 precondition을 충족하는 direct evidence가 아니며, 같은 target도 표 출력 뒤 새로 관찰해야 한다.
caller나 Verifier가 execution 시점에 request, target 또는 outcome을 바꾸지 못한다. Runner는 각
observation에 대해 다음을 하나의 immutable evidence item으로 만든다.

```text
exact Candidate/planning binding
stable scenario ID, fixed observation identity와 대상 AC
실제로 관찰한 source/target/request
시작 전 currentness observation
완전한 bounded result 또는 observation을 얻지 못한 tool fact
artifact와 direct observation의 integrity binding
완료 후 currentness observation
```

source review도 Verifier가 자유 서술로 증거를 만드는 것이 아니다. plan이 요구한 exact Candidate의
path/range/semantic surface를 Runner가 읽고 immutable source evidence를 반환한다. concrete hash,
anchor와 artifact serialization은 숨긴 Implementation이다.

local execution은 한 observation에 대해 한 bounded runner operation을 기본으로 한다. timeout,
missing executable, nonzero exit, empty output와 tool error는 자동 AC verdict가 아니다. Verifier는
완전한 direct observation이 expected observable을 충족하거나 반박하는지 판단한다. 실행 결과가
없거나 tool failure와 product failure를 구분할 수 없으면 `UNDETERMINED`다.

한 fixed observation 안에서 retry, poll, action/readback 또는 다른 subattempt를 둘 이상 시작했다면
complete evidence item은 시작된 모든 subattempt를 순서대로 포함한다. 각 subattempt는 같은 fixed
observation plan 안에서 **그 subattempt에 미리 고정된 request**와의 결속, tool status,
source/currentness, artifact 또는 artifact 부재를 보존한다. 동일-request retry/poll은 같은 request
binding을 공유하고, action/readback처럼 서로 다른 subattempt는 각자의 pre-fixed request binding을
유지한다. Runner와 Verifier는 성공·실패 어느 쪽에도 유리한 subset만 선택할 수 없다. 이는 completed
evidence bundle의 완전성 조건이지 generic audit/event ledger나 caller-visible attempt protocol이 아니다.

retry/poll/action/readback/cleanup이 의미의 일부인 외부효과 observation은 Phase 6이 하나의 complete
effect evidence bundle로 제공해야 한다. Phase 5는 per-attempt ledger, replay scope 또는 polling DSL을
만들지 않는다.

## evidence 충분성과 AC 판정

Verifier는 fixed plan과 Runner가 반환한 complete evidence item만 읽고 모든 AC를 정확히 한 번씩
판정한다.

### `SATISFIED`

- 해당 AC의 모든 필요한 observation이 exact Candidate/planning에서 완료됐다.
- evidence가 planning이 요구한 observation level에서 expected observable을 직접 보인다.
- evidence가 user-facing commentary로 먼저 공개되고 실제 실행된 모든 applicable stable scenario IDs에
  각각 결속된다.
- implementation check, Worker prose, previous verification 또는 unmapped component result에 의존하지
  않는다.
- candidate/planning currentness와 evidence integrity가 결론을 허용한다.

### `NOT_SATISFIED`

- 적어도 하나의 complete direct observation이 exact Candidate가 AC의 required observable과 모순됨을
  보인다.
- tool/environment/authority failure나 evidence 부재를 product contradiction으로 바꾸지 않는다.
- source drift 전에 exact Candidate에 결속되어 완성된 contradiction evidence는 그 Candidate에 대한
  결론으로 보존할 수 있다.

### `UNDETERMINED`

- 필요한 observation이 누락·중단·판독 불능이거나 observation level이 부족하다.
- tool, environment, authority, isolation, currentness 또는 evidence integrity를 확보하지 못했다.
- 결과가 모호해 product failure와 observation failure를 구분할 수 없다.
- 안전한 Phase 6 effect observation을 실행할 수 없다.

Verifier rationale은 evidence와 AC의 관계를 설명할 뿐 evidence를 대신하지 않는다. Module은 각
판정이 plan의 exact AC와 complete evidence에 결속되는지 검증하고, unsupported conclusive verdict는
항상 `UNDETERMINED`로 낮춘다. `SATISFIED`와 `NOT_SATISFIED`라는 내부 Verifier claim을 그대로
신뢰하거나 malformed assessment 때문에 complete nonconclusive result publication까지 버리지 않는다.

## contradiction short-circuit

한 AC의 `NOT_SATISFIED`에 충분한 complete direct evidence가 생기면 Module은 이후 아직 시작하지 않은
위험한 effect observation을 실행하지 않는다. 필요한 safe readback/cleanup은 Phase 6 규칙대로
마쳐야 한다. 나머지 AC는 evidence가 이미 충분한 경우에만 결론적 판정을 유지하고, 그렇지 않으면
`UNDETERMINED`다.

별도 `declare-contradiction` command, contradiction capability와 post-hoc event는 만들지 않는다.
contradiction은 immutable evidence item과 그 evidence를 읽은 AC assessment의 결속이다.

## currentness와 drift

retained Candidate source는 immutable하지만 live planning과 canonical source는 달라질 수 있다.
Module은 최소한 plan 고정 전, 각 effectful observation 직전, result publication 직전에 stable live
currentness를 다시 확인한다.

- live planning/source가 Candidate와 일치하는 동안 얻은 complete evidence만 현재 work의 긍정
  conclusion에 사용할 수 있다.
- drift 뒤 새 observation을 기존 Candidate의 `SATISFIED` 근거로 사용하지 않는다.
- drift 전에 exact Candidate에 결속된 sufficient contradiction은 그 exact Candidate의
  `NOT_SATISFIED`로 보존한다.
- 나머지 영향받은 AC는 `UNDETERMINED`다.
- live currentness를 안정적으로 읽지 못하면 historical Candidate/result binding은 보존하지만
  current positive conclusion은 만들지 않는다.
- source가 예전 bytes로 돌아와도 current verification을 자동 resume하지 않는다.

VerificationResult는 exact Candidate에 대한 historical result이며 `inspect`가 live currentness를
별도로 관찰한다. result를 새로운 live source에 맞게 고쳐 쓰지 않는다.

## durable progress와 재시작

Phase 3의 active VERIFY transition private progress에는 다음 의미만 남긴다.

```text
fresh verification context identity
immutable observation plan
현재 최대 한 observation의 fixed request와 may-have-run state
완료된 runner-owned evidence bundle
완료되지 않은 effect observation이 있다면 그 하나의 unresolved observation item
```

generic event ledger, caller-visible run/flow/step graph, actor/capability rows와 budget vector는 남기지
않는다. completed evidence는 final result 근거이므로 보존하지만, 모든 내부 호출·poll·attempt를 audit
history로 보존하지 않는다.

observation이 시작됐을 수 있는데 complete evidence가 없으면 동일 request를 자동 반복하지 않는다.
Runner Adapter가 canonical/retained source와 외부 state를 바꾸지 않았음을 입증한 isolated local
observation만 fresh environment에서 한 번 다시 수행할 수 있다. 입증하지 못하면 해당 observation과
그에 의존하는 AC는 `UNDETERMINED`다. 위험한 effect의 continuation/replay는 Phase 6만 결정한다.

effect observation이 `may-have-run`인데 complete evidence가 없으면 Module은 먼저 live execution
owner가 더는 없음을 확인한다. 그 뒤 exact Candidate, fixed request/target과 `may-have-run`을 Runner가
확인한 하나의 unresolved observation item으로 만들어 result의 private safety binding에 보존한
경우에만 active transition을 `UNDETERMINED` publication으로 종료할 수 있다. 이를 보존할 수 없거나
live owner 부재를 확정할 수 없으면 transition을 fail-closed로 유지한다. 이 item은 다음 verification의
Phase 6 safety gate만 읽으며 fresh Verifier의 semantic evidence가 아니다. Phase 6이 continuation,
authoritative readback, exact idempotency 또는 correlation 중 어떤 mechanism을 사용할지는 Phase 6에
남긴다.

exact Candidate에 결속된 unresolved observation item은 Phase 6 safety gate가 authoritative하게
`RESOLVED` 또는 `SAFE`라고 판정할 때까지 이후 모든 same-Candidate verification에 계속 적용된다. 중간
verification이 새 effect를 시작하지 않고 `UNDETERMINED`로 끝나도 이 applicability를 지우지 않는다.
Module은 immutable result history에서 item을 읽거나 private safety binding으로 carry forward할 수 있으며
representation과 탐색 방식은 숨긴 Implementation이다.

process death나 elapsed time만으로 active transition을 버리지 않는다. Module은 private progress와
Candidate/currentness/effect safety를 읽어 evidence completion, nonconclusive result publication,
safe no-result close 또는 fail-closed 유지 중 하나를 선택한다. Phase 3의 atomic publication 전에는
partial VerificationResult가 외부에 보이지 않는다.

## VerificationResult publication

publication 전에 Module은 다음을 한 번 다시 계산한다.

- exact Candidate/planning/전체 AC와 immutable plan의 일치
- 모든 AC가 결과에 정확히 한 번 존재하는지
- 각 AC 결과 행이 사용자에게 실제로 공개되고 실행된 모든 applicable stable scenario IDs와 각
  scenario의 admissible direct evidence를 연결하는지
- 각 conclusion이 mapped runner-owned direct evidence에 의해 허용되는지
- evidence integrity와 Candidate binding
- currentness 및 drift 전 contradiction precedence
- Phase 6이 요구한 effect safety/readback/cleanup completeness
- unresolved effect가 있으면 live owner 부재와 private safety binding 보존

criterion 결과는 Phase 2 의미만 사용한다.

```text
모든 AC가 SATISFIED                         -> VERIFIED
하나 이상의 AC가 NOT_SATISFIED             -> NOT_SATISFIED
그 외 하나 이상의 AC가 UNDETERMINED         -> UNDETERMINED
```

authority prohibition, tool failure와 evidence incompleteness를 별도 `BLOCKED`/`INCOMPLETE` public status로
나누지 않는다. 그것들은 `UNDETERMINED` reason으로 설명한다. result의 AC별 정확히 한 행은 exact
Candidate와 verdict를, 실제 사용자에게 공개되고 실행된 모든 applicable stable scenario IDs를, 그리고
각 scenario의 admissible direct evidence를 대조 가능하게 연결한다. 공개되지 않은 scenario 실행은
`SATISFIED`의 근거가 될 수 없다. plan digest, flow/step ref, capability, raw ledger와 budget을 caller에게
요구하지 않는다. 실행 전에 공유하지 않은 replacement scenario를 이전에 공유한 scenario인 것처럼
publication하지 않으며, 기존 scenario evidence를 replacement evidence로 재표기하지 않는다.

Phase 3의 한 atomic commit으로 VerificationResult append, predecessor/head 이동과 active transition
종료를 수행하고 exact committed result를 readback한다. 응답 유실 뒤 `inspect(work)`는 complete result와
그 result에서 복구 가능한 exact Candidate를 반환한다.

## 허용한 실패·복구 의미

- fresh Verifier를 만들지 못하면 evidence를 실행하지 않고 `UNDETERMINED` 또는 safe no-result close다.
- user-facing commentary channel이 없으면 direct evidence acquisition 전에 `unsupported`로 중단한다.
- planning inspection은 scenario 설계용일 뿐이며, 표 출력 뒤 새 evidence observation 없이는 direct
  AC evidence가 아니다.
- 모든 AC를 적절한 observation으로 계획하지 못하면 약한 plan으로 성공시키지 않는다.
- source/runner isolation이 없으면 Candidate source를 수정하지 않고 `UNDETERMINED`다.
- implementation check나 Worker prose만 있으면 결론적 AC verdict를 만들지 않는다.
- observation request/result가 바뀌거나 evidence binding을 읽지 못하면 해당 AC는 `UNDETERMINED`다.
- missing tool, timeout과 absent evidence는 `NOT_SATISFIED`가 아니다.
- complete direct contradiction은 다른 AC의 missing evidence와 무관하게 exact Candidate의
  `NOT_SATISFIED`를 만들 수 있다.
- drift 뒤 positive observation을 만들지 않으며, drift 전 contradiction만 exact historical result로
  보존한다.
- response loss는 duplicate verifier/effect를 자동 시작하지 않고 committed result를 readback한다.
- 시작된 모든 subattempt는 complete evidence에서 생략하지 않으며, unresolved effect fact는 result 종료
  뒤에도 다음 Phase 6 safety gate까지 보존한다.

## 근거가 있는 최소 시나리오

1. source-only AC를 fresh Verifier가 계획하고 Runner가 retained Candidate의 exact source evidence를
   읽는다. 충분한 evidence면 `SATISFIED`다.
2. public CLI/API behavior AC를 isolated local Runner가 fresh하게 실행해 expected output을 직접 얻는다.
   implementation test 성공을 재사용하지 않고 `SATISFIED`다.
3. implementation check는 통과했지만 required end-to-end observation을 얻지 못했다. AC는
   `UNDETERMINED`다.
4. component별 성공은 있지만 planning이 요구한 하나의 product flow가 연결되지 않는다. AC는
   `UNDETERMINED`다.
5. complete direct evidence가 expected behavior와 모순된다. 해당 AC는 `NOT_SATISFIED`이고 아직
   시작하지 않은 위험한 effect는 중단한다.
6. process timeout, missing executable 또는 source 격리 실패로 observation을 얻지 못한다. 이는
   `UNDETERMINED`이며 product failure가 아니다.
7. verification tool이 Candidate source에 쓰기를 시도한다. write는 차단되고 해당 observation은
   `UNDETERMINED`다.
8. Candidate 이후 planning/canonical source가 바뀐다. drift 전 contradiction은 보존하되 positive와
   영향받은 AC는 `UNDETERMINED`다.
9. evidence acquisition 중 process가 죽는다. unsafe duplicate execution 없이 complete evidence가
   없는 AC를 `UNDETERMINED`로 닫는다.
10. result commit 뒤 response가 유실된다. `inspect`가 exact Candidate에 결속된 complete
    VerificationResult를 반환한다.
11. `UNDETERMINED` 뒤 조건이 해결된다. 새 fresh Verifier가 이전 plan/evidence를 carry forward하지
    않고 같은 exact Candidate를 처음부터 다시 검증한다.
12. effect가 발생했을 수 있으나 응답이 유실된다. live owner가 없고 unresolved observation item을
    보존한 뒤에만 `UNDETERMINED`로 닫으며, 다음 verification은 Phase 6 safety gate가 허용하기 전 같은
    effect를 실행하지 않는다.

## 현재 mechanism에서 삭제·숨길 것

새 Verification Execution Module은 다음 current 보장을 흡수한다.

- fresh read-only Assessor 관점
- 모든 exact AC의 pre-execution observation coverage
- component success의 post-hoc composition 거부
- fixed request와 runner-owned artifacts
- source/planning currentness와 drift precedence
- missing evidence와 direct contradiction의 구분
- result status의 criterion-derived aggregation

다음 current mechanism은 정상 caller와 새 public protocol에 남기지 않는다.

- Coordinator/Assessor/Remediator actor row와 role capability token
- outer invocation, budget vector, reservation과 claim command
- `open-verification`, `seal-run`, `execute-step`, `declare-contradiction`, `read-artifact` 호출 순서
- caller-authored verification draft JSON
- public-shaped run/flow/step ID와 bidirectional mapping payload
- `process-v3`, environment-policy와 executable digest를 caller가 알아야 하는 계약
- append-only attempt/event ledger와 per-step OS lock protocol
- separate `BLOCKED`/`INCOMPLETE` public statuses
- verification command 안의 remediation open과 Worker lifecycle

fixed observation plan, exact runner request, evidence integrity와 any necessary execution exclusion은
Module 내부 Implementation으로 남는다. 새 tests는 `verify(candidate)` Interface에서 observable
criterion/result/currentness 의미를 검증하고, legacy shallow-command unit tests를 layering하지 않는다.

## 명시적 범위 밖

- final CLI/function 이름과 serialized Candidate/VerificationResult schema
- plan/evidence identity digest, artifact serialization, storage와 retention 형식
- concrete process/browser/MCP/HTTP runner와 sandbox implementation
- dangerous external-effect authorization, retry, correlation, readback과 cleanup mechanism
- runtime fault injection, performance budget와 resource quota
- remediation implementation, migration과 legacy command/schema/test 제거

## Oracle finding 판정 기록

### Initial — `slots-context-phase5in-b767c5fbf2`

slot 1, DevSpace 무첨부 review가 완료됐다. stored model evidence는
`requested=Pro`, `resolved=(unavailable)`, `strategy=current`, `verified=no`이므로 실제 model identity를
확정하지 않는다.

#### F1 — publication 뒤 ambiguous effect fact 유실

```text
ORACLE_CLAIM: transition-local may-have-run만 남기고 UNDETERMINED result를 publish하면 다음
  verification의 Phase 6 safety gate가 prior exact effect를 판별할 입력을 잃는다.
STRONGEST_COUNTERARGUMENT: active transition을 fail-closed로 계속 유지하면 유실은 없고, Phase 6이
  모든 effect recovery를 소유하므로 Phase 5 result에 새 상태를 넣을 필요가 없을 수 있다.
PURPOSE_INVARIANT_AT_RISK: response loss 뒤 duplicate effect를 만들지 않으면서 같은 exact Candidate를
  다시 검증할 수 있어야 한다.
CONCRETE_EVIDENCE: current Verification Lead는 same-handoff ancestor의 ambiguous ACTION/CLEANUP을
  검사하고 authority 없이는 새 effect를 막는다. test_ambiguous_cross_run_effect_is_blocked_until_
  exact_idempotency_authority가 그 실패 경로를 고정한다.
CURRENT_PHASE_OWNERSHIP: Phase 6은 safety 판단 mechanism을 소유하지만 Phase 5 publication이 그 판단의
  최소 입력을 버릴 수 있는지는 Phase 5 durable closure 문제다.
SMALLEST_CORRECTION: live owner 부재 확인 뒤 exact Candidate/request/target/may-have-run 하나를 private
  unresolved observation item으로 result에 결속한다. 불가능하면 transition을 fail-closed로 유지한다.
COMPLEXITY_DELTA: caller Interface/status/정상 경로 +0, ambiguous effect일 때 private item 최대 +1;
  ancestor attempt ledger와 replay command는 되살리지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F2 — complete bundle의 favorable subattempt selection

```text
ORACLE_CLAIM: 한 observation이 여러 poll/retry/subattempt를 시작했는데 성공 subset만 complete evidence로
  제출할 수 있으면 direct evidence 결속이 무너진다.
STRONGEST_COUNTERARGUMENT: plan은 한 bounded runner operation을 고정하고 effect bundle의 내부는 Phase 6
  소유이므로 Phase 5가 attempt 의미를 다시 도입하면 ledger ceremony가 돌아올 수 있다.
PURPOSE_INVARIANT_AT_RISK: missing/tool failure와 product result를 구분하고 유리한 evidence 선택을 막는다.
CONCRETE_EVIDENCE: current runner는 모든 READBACK poll을 보존하며 timeout 뒤 exact readback 유무에 따라
  결과가 달라진다. process pilot도 miss와 success poll을 함께 보존한다.
CURRENT_PHASE_OWNERSHIP: retry algorithm과 serialization은 Phase 6/Implementation이지만 conclusive verdict를
  허용하는 complete direct evidence의 의미는 Phase 5 소유다.
SMALLEST_CORRECTION: 실제 시작된 subattempt만 순서대로 complete evidence item에 포함하고 subset 선택을
  금지한다. 공개 attempt ID, ledger, polling DSL은 추가하지 않는다.
COMPLEXITY_DELTA: caller/public state/단일-attempt 정상 경로 +0; multi-attempt evidence만 실제 실행 수만큼
  늘고 generic ledger는 계속 삭제한다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F3 — historical context와 fresh namespace 충돌

```text
ORACLE_CLAIM: 이전 result를 historical context로 허용한 문구가 fresh Verifier의 이전 semantic artifact
  비접근 조건과 충돌한다.
STRONGEST_COUNTERARGUMENT: 문맥상 historical context는 Module/Phase 6 진단용이고 이전 verdict를 새
  evidence로 쓰지 말라는 금지만으로 충분하다고 읽을 수 있다.
PURPOSE_INVARIANT_AT_RISK: 이전 plan/verdict/evidence selection에 편향되지 않은 독립 검증이다.
CONCRETE_EVIDENCE: current test는 fresh Assessor의 ancestor raw artifact read를 거부하고, 현재 초안 63~79행은
  입력 금지를 선언하면서 86~89행은 독자를 특정하지 않은 historical context를 허용했다.
CURRENT_PHASE_OWNERSHIP: fresh Verifier Adapter의 readable semantic namespace는 Phase 5 내부 seam 계약이다.
SMALLEST_CORRECTION: Module/Phase 6 safety gate만 과거 내용을 읽고 Verifier에는 현재 capability fact만
  전달한다고 명시한다. actor/capability protocol은 추가하지 않는다.
COMPLEXITY_DELTA: caller/정상 경로/durable state/failure state +0, 내부 namespace boundary 문구 +1;
  per-Assessor token과 artifact-read command는 계속 삭제한다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

초기 review의 Candidate read-only, immutable plan/AC coverage, three-result collapse와 contradiction command
삭제에는 추가 correction이 필요하지 않다는 판정은 current 계약/source/test와 일치한다. F1~F3의 최소
수정에 대해 같은 conversation follow-up으로 재공격한다.

### Follow-up 1 — `slots-followup-phase5fo-85fcd5a93e`

같은 conversation URL과 slot 1에서 prompt submission 및 completed UI answer를 확인했다. wrapper의
prompt commit probe timeout 때문에 stock session status와 authoritative readback은 `error`지만, 이 운영
상태를 설계 finding 근거로 사용하지 않고 실제 follow-up answer를 harvest했다. stored model evidence는
`requested=Pro`, `resolved=(unavailable)`, `strategy=current`, `verified=no`다.

#### F1 — `STILL_OPEN`, unresolved fact의 다중 retry lifetime

```text
ORACLE_CLAIM: R1이 unresolved item을 보존해도 effect를 실행하지 않은 R2가 UNDETERMINED로 끝난 뒤
  current head R2만 보는 R3가 R1의 fact를 잃을 수 있다.
STRONGEST_COUNTERARGUMENT: immutable result history에 R1이 남고 Module/Phase 6은 private content를 읽을
  수 있으므로 구현이 ancestor를 탐색하면 이미 안전하다.
PURPOSE_INVARIANT_AT_RISK: 같은 exact Candidate의 반복 재검증에서도 unresolved effect를 authoritative
  resolution 전 재실행하지 않는다.
CONCRETE_EVIDENCE: current _replay_preflight는 same-handoff predecessor run들을 lineage 전체에서 탐색한다.
  기존 correction은 “다음 safety gate까지”만 명시해 그 이후 applicability를 Implementation 선택으로
  남겼다.
CURRENT_PHASE_OWNERSHIP: effect resolution mechanism은 Phase 6, unresolved durable fact의 lifetime은 Phase 5
  publication/recovery 의미다.
SMALLEST_CORRECTION: exact Candidate의 unresolved item은 Phase 6이 RESOLVED/SAFE라고 판정할 때까지 모든
  same-Candidate verification에 적용한다. history scan/carry-forward representation은 고정하지 않는다.
COMPLEXITY_DELTA: caller/정상 경로/public state/new item +0; 이미 존재하는 private item의 applicability만
  연장하며 ancestor attempt ledger는 되살리지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F2 — `OVERCORRECTED`, heterogeneous action/readback request

```text
ORACLE_CLAIM: 모든 subattempt를 “같은 fixed request”에 결속한 문구는 서로 다른 ACTION과 READBACK
  request까지 동일해야 한다고 읽혀 정상 product flow를 막거나 개별 request substitution을 놓친다.
STRONGEST_COUNTERARGUMENT: “same”은 observation마다 plan에 고정된 요청과 같다는 뜻으로 읽을 수 있고
  실제로 identical bytes를 요구하려는 문구가 아니었다.
PURPOSE_INVARIANT_AT_RISK: 필요한 action/readback 검증을 실행하면서 각 실제 실행을 계획된 request에
  정확히 결속한다.
CONCRETE_EVIDENCE: current source는 step마다 canonicalRequestDigest를 가지며 동일-request 반복은 READBACK
  poll에만 적용한다. ACTION timeout 뒤 별도 READBACK request가 effect를 확인하는 test도 있다.
CURRENT_PHASE_OWNERSHIP: concrete digest/DSL은 후속 Implementation이지만 complete evidence의 request
  binding 의미는 Phase 5다.
SMALLEST_CORRECTION: 각 subattempt를 그 subattempt에 pre-fixed된 request에 결속하고, 동일 poll과
  heterogeneous action/readback을 구분한다.
COMPLEXITY_DELTA: caller/정상 경로/durable/public state +0; 문구 범위만 좁히고 공개 step/attempt protocol은
  만들지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

F3는 `CLOSED`, 새 별도 material finding과 사용자 결정은 없음으로 판정됐다. F1/F2 correction을 같은
conversation에서 다시 재공격한다.

### Follow-up 2 — `slots-followup-phase5fo-485d0a30a4`

같은 conversation URL과 slot 1에서 prompt submission과 completed UI answer를 확인했다. follow-up 1과
같은 wrapper prompt commit probe timeout으로 stock status와 authoritative readback은 `error`지만 답변은
child session에서 harvest했다. 이 delivery 이상은 설계 근거로 사용하지 않는다. stored model evidence는
`requested=Pro`, `resolved=(unavailable)`, `strategy=current`, `verified=no`다.

```text
F1: CLOSED — unresolved item은 authoritative RESOLVED/SAFE까지 모든 same-Candidate verification에
  계속 적용되며, history scan/carry-forward는 숨긴 Implementation이다.
F2: CLOSED — 각 subattempt는 자기 pre-fixed request에 결속되고, identical poll과 heterogeneous
  action/readback을 구분하면서 started subattempt 전체를 보존한다.
F3: CLOSED 유지
새 material finding: 없음
사용자 결정: 없음
caller Interface / 정상 경로 / durable state 종류 / failure state 순증가: 없음
제거 대상 ceremony 재도입: 없음
```

Oracle의 closure 선언과 별개로 Phase 1~4 불변 조건과 current source/test를 다시 대조했다. F1은 current
ancestor replay scan이 지키는 사용자 가치를 private unresolved-item lifetime 하나로 축소하며 Phase 6
mechanism을 끌어오지 않는다. F2는 current per-step request와 READBACK polling의 의미만 completed evidence
안에 흡수하고 공개 step/attempt protocol을 되살리지 않는다. F3는 actor/capability 대신 Adapter readable
namespace로 독립성을 지킨다. 세 correction 모두 외부 `verify(candidate)`와 3상태 결과를 바꾸지 않는다.

## 완료 판단

`DESIGN_CONVERGED`다.

- exact Candidate를 수정하지 않는 fresh verification과 전체 AC pre-evidence plan이 정해졌다.
- Runner-owned direct evidence, 모든 started subattempt의 비선택적 포함과 request binding이 정해졌다.
- evidence 부족과 product contradiction은 `UNDETERMINED`/`NOT_SATISFIED`로 분리된다.
- ambiguous effect의 durable fact는 authoritative resolution 전 재실행되지 않지만 effect safety mechanism은
  Phase 6에 남는다.
- caller-visible actor/capability/run/flow/step/ledger/replay ceremony는 재도입하지 않았다.
- 열린 material finding과 사용자 결정은 없다. Phase 6과 제품 구현은 시작하지 않았다.
