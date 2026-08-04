# Phase 2 — 외부 Interface와 복구 의미

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

정상 caller가 정확한 구현 candidate를 만들고, 그 candidate를 독립 검증하고, 중단 뒤 현재
결과를 다시 확인하기 위해 알아야 할 최소 Interface와 복구 의미를 정한다.

이 단계는 저장소·schema·digest 형식·lock·claim·transaction·runner·evidence 수집 방식 또는
외부효과 replay를 설계하지 않는다. 그것들은 작은 Interface 뒤의 Implementation이거나 Phase
3~6의 결정이다.

## Phase 1에서 상속한 사용자 가치

1. 구현 결과는 알려진 due-now 구현·통합 미완료가 없는 독립 검증 대기 candidate일 뿐 final
   verdict가 아니다.
2. candidate는 정확한 planning/AC, 실제 source, 구현 범위 변경과 보존한 기존·동시 변경을
   대조할 수 있어야 한다.
3. 검증은 구현 주체와 분리된 fresh 관점에서 모든 AC를 다루고, planning이 요구한 관찰 수준의
   직접 source/evidence로 판정한다.
4. 성공, evidence로 입증된 불충족, 아직 판정할 수 없음을 구분한다. evidence 부족 자체는 AC
   불충족이 아니다.
5. 검증 중 source를 수정하지 않는다. 수정이 필요하면 새 candidate와 새 독립 검증을 거친다.

## 현재 caller 부담

현재 구현 publication은 command 하나지만 caller가 workflow root/guard, Capsule store,
transaction request를 조립해야 한다. 검증은 12개 command와 capability, claim, invocation budget,
run/flow/step ref, sealed draft, contradiction, artifact read, replay scope, remediation open 순서를
caller에게 노출한다.

이 표면은 Phase 1의 결과 의미보다 훨씬 크다. 특히 actor capability, claim, reservation,
step execution, ledger와 replay는 caller가 목적을 표현하는 개념이 아니라 현재 Implementation을
운영하기 위한 개념이다.

## 실제 Seam

한 개의 깊은 **Implementation Verification Module**을 planning과 product source가 만나는
seam에 둔다. Implementation Lead와 Verification Lead의 책임 분리는 Module 내부에서 유지한다.
외부 Interface가 하나라는 사실은 동일 actor가 구현과 검증을 수행한다는 뜻이 아니다.

의존성은 다음처럼 분류한다.

- planning/source identity와 local durable state: local-substitutable dependency. 외부 Interface에
  store adapter를 노출하지 않는다.
- selected implementation Worker: 실행마다 실제로 달라지는 injected dependency. `implement`의
  명시적 입력으로 남긴다.
- fresh verifier와 evidence runner: 독립성 보장을 소유하는 Module 내부 seam. 정상 caller가
  actor/capability/runner를 조립하지 않는다.
- 실제 제품 runtime과 위험한 외부효과: 후속 Phase가 정할 internal Adapter. Phase 2 Interface에
  executor 종류나 replay protocol을 노출하지 않는다.

## 작은 외부 Interface

Interface는 세 가지 의미 호출만 제공한다. 아래 이름은 의미를 고정하기 위한 설계 이름이며,
최종 CLI 함수명이나 payload serialization은 아니다.

### 1. `implement(work, worker)`

`work`는 caller가 이미 아는 exact canonical ready Ticket이다. Module은 Ticket에 기록된
authoritative `Project-Root`를 직접 해석하고 currentness를 확인한다. caller는 같은 root를 별도
값으로 다시 제공하거나 두 authority의 일치를 책임지지 않는다. `worker`는 실제 실행 가능한
선택된 구현 Worker다.

Module은 현재 planning과 source를 직접 읽고, 초기 구현인지 evidence로 입증된 실패 뒤의
재구현인지 내부에서 판별한다. caller는 baseline, snapshot, envelope, transaction, claim,
capability, task accounting 또는 handoff payload를 조립하지 않는다.

반환은 둘 중 하나다.

- `Candidate`: 독립 검증에 넘길 수 있는 구현 candidate
- `ImplementationStopped`: candidate를 정직하게 만들 수 없다는 비긍정 결과

`Candidate`가 외부에 제공해야 할 관찰은 다음뿐이다.

```text
정확한 planning 입력과 전체 AC
검증자가 다시 읽을 exact candidate source
구현 범위 변경과 보존된 기존·동시 변경의 구별 가능성
독립 검증이 아직 남았다는 사실
```

`ImplementationStopped`는 알려진 미완료, planning/source 불일치, 사용자 변경 보존 불확실성처럼
candidate를 만들지 못한 이유와 현재 source를 보존해 보고한다. 이를 candidate나 final failure로
승격하지 않는다.

### 2. `verify(candidate)`

Module은 전달받은 exact `Candidate`에 대해 fresh read-only verifier를 만들고 모든 AC를 검증한다.
caller는 verifier identity, capability, plan seal, flow/step, executor, artifact selection,
contradiction declaration 또는 aggregate status를 제출하지 않는다.

반환 `VerificationResult`는 candidate와 동일한 planning/AC/source를 다시 나타내고, 모든 AC를
정확히 한 번씩 다음 중 하나로 판정한다.

모든 `VerificationResult`는 자신이 판정한 exact `Candidate`에 결속된다. caller는 result를
읽은 뒤 그 exact candidate를 다시 검증 입력으로 복구할 수 있어야 한다. candidate handle,
field 또는 serialization 형식은 이 단계에서 정하지 않는다.

```text
SATISFIED       충분한 independent evidence가 AC 충족을 보임
NOT_SATISFIED   충분한 independent evidence가 AC 불충족을 보임
UNDETERMINED    결론에 필요한 evidence·identity·authority를 확보하지 못함
```

각 결론에는 verifier가 직접 읽거나 실행해 얻은 evidence 관찰을 대조할 수 있어야 한다. 구체적인
evidence ref/schema와 수집 방식은 Phase 5가 소유한다.

전체 의미는 criterion 결과에서만 도출한다.

```text
모든 AC가 SATISFIED                         -> VERIFIED
하나 이상의 AC가 NOT_SATISFIED             -> NOT_SATISFIED
그 외 하나 이상의 AC가 UNDETERMINED         -> UNDETERMINED
```

`verify`는 source를 수정하거나 자동 재구현하지 않는다. `NOT_SATISFIED` 뒤의 수정은 별도
`implement(work, worker)` 호출이 새 candidate를 만들 때만 가능하다.

### 3. `inspect(work)`

중단·재시작 또는 담당자 교체 뒤 사용하는 read-only 호출이다. caller가 이미 아는 exact
canonical ready Ticket만 받으며, 별도 product root, capability, claim, run ref, store path 또는
schema version을 요구하지 않는다.

반환은 Module이 확인할 수 있는 최신 완전한 공개 결과 하나와, 그 결과가 현재 `work`에 그대로
적용되는지에 관한 currentness 관찰이다.

```text
Candidate
VerificationResult
NoConclusiveResult
```

완전한 결과 자체의 exact planning/source/evidence 결속과 무결성을 확인할 수 있다면, live
planning/source가 나중에 달라져도 그 exact historical result를 반환한다. 다만 currentness
관찰은 그 결과를 현재 work의 판정으로 사용할 수 없음을 나타내야 한다. 특정 boolean, digest,
status 이름 또는 serialization은 정하지 않는다.

`NoConclusiveResult`는 아직 완전하게 publication된 결과가 없거나, 기존 결과 자체의 exact
planning/source/evidence 결속 또는 무결성을 확인할 수 없음을 뜻한다. 단순한 live drift만으로
이미 완전하게 결속된 결과를 숨기지 않는다. 내부 state가 존재한다는 사실만으로 candidate,
failure 또는 verified를 추론하지 않는다.

## 복구 의미

- `Candidate`와 `VerificationResult`는 완전한 결과로 publication된 뒤에만 관찰된다. 부분 기록,
  Worker 서술, check 통과 또는 실행 중 state는 긍정 결과가 아니다.
- caller가 응답을 받기 전 호출이 끊겨도 `inspect(work)`는 확인 가능한 최신 공개 결과만 돌려준다.
- 같은 의미의 `implement` 재호출을 받으면 Module은 이미 공개된 exact candidate를 반환하거나,
  안전한 continuation을 내부에서 입증한 경우에만 계속한다.
- exact candidate에 대한 `VERIFIED`와 `NOT_SATISFIED`는 결론적 결과다. `UNDETERMINED`는 성공이나
  불충족의 terminal 결론이 아니다. 조건이 해결된 뒤 같은 `verify(candidate)`가 호출되면,
  Module은 candidate currentness와 이전 외부효과의 비재실행 또는 safe continuation을 입증한
  경우에만 fresh independent verification을 시작한다. 입증하지 못하면 effect를 실행하지 않고
  다시 `UNDETERMINED`를 반환한다.
- 재시작한 caller가 `inspect(work)`에서 `UNDETERMINED`를 읽은 경우에도, 그 결과에 결속된 exact
  candidate를 복구해 위 fresh verification 입력으로 사용할 수 있어야 한다.
- 안전한 continuation, 사용자 변경 보존, source/planning currentness 또는 외부효과 비재실행을
  입증하지 못하면 자동 replay·새 Worker dispatch·source 채택을 하지 않고 비긍정 결과를 반환한다.
- candidate 뒤 source나 planning이 달라지면 기존 candidate를 새 source에 맞춰 고쳐 쓰지 않는다.
  drift는 `SATISFIED`·`VERIFIED`와 drift 이후 관찰에 의존하는 결론을 금지한다. 다만 drift 전에
  exact candidate·planning·AC에 결속된 충분한 independent evidence로 확정된
  `NOT_SATISFIED`는 그 exact candidate에 대한 결론으로 보존할 수 있다. 나머지 영향받은 AC는
  `UNDETERMINED`다. 현재 authority에서 새 candidate가 필요하면 별도 구현 호출로 만든다.
- `NOT_SATISFIED`는 자동 수정 권한이 아니다. 같은 planning 안에서 수정 가능한지 Module이 다시
  읽고 판단하며, 새 제품 결정이 필요하면 `ImplementationStopped`로 planning authority에 돌려보낸다.
- restart 뒤 어떤 internal operation을 resume·abort·reconcile할지는 caller 계약이 아니다.
  Phase 3~6 Implementation이 위 fail-closed 결과 의미를 만족해야 한다.

## 오류와 caller가 알아야 할 구분

caller는 내부 실패 상태가 아니라 다음 행동을 결정하는 최소 구분만 받는다.

| 결과 | caller 의미 |
| --- | --- |
| `Candidate` | exact candidate를 `verify`할 수 있음 |
| `ImplementationStopped` | candidate 없음; 이유와 보존된 현재 source를 보고 planning/authority 또는 구현 조건을 해결해야 함 |
| `VERIFIED` | 모든 AC가 충분한 independent evidence로 충족됨 |
| `NOT_SATISFIED` | 충분한 independent evidence가 적어도 한 AC의 불충족을 보임; 자동 수정 없이 새 구현 판단 필요 |
| `UNDETERMINED` | 성공도 불충족도 결론 낼 수 없음; 누락된 evidence/authority/currentness를 해결해야 함 |
| `NoConclusiveResult` | 재시작 뒤 신뢰할 공개 결과를 찾지 못함; 내부 진행을 추론하거나 성공으로 간주하지 않음 |

완전한 historical result와 live work가 달라졌다는 currentness 관찰은 새 verdict가 아니다. 이는
exact 과거 결과를 보존하면서 현재 source/planning에 대한 성공·불충족으로 오용하지 않게 한다.

reason은 caller가 해결할 authority/evidence/currentness/preservation 문제를 설명할 수 있어야 하지만,
내부 state enum, claim/lease/lock 또는 runner fault code를 그대로 공개할 필요는 없다.

## Module이 숨길 Implementation

- source identity digest, retained baseline과 delta partition
- planning seal, raw AC parser와 criterion accounting
- durable store, schema, graph, unique tip, atomic publication과 lineage
- actor capability, claim, reservation, budget와 ownership token
- transaction/envelope, before/after snapshot과 reconciliation
- verification draft, flow/step ordering, executor, ledger와 artifact retention
- effect classification, authorization, correlation, replay와 readback
- restart 시 resume/abort/reconcile 및 remediation admission
- status derivation과 내부 오류를 작은 외부 결과로 변환하는 방식

## 근거가 있는 최소 시나리오

1. 기존 사용자 변경이 있는 source에서 `implement`가 그 변경을 보존하고 exact Ticket/AC에 대한
   `Candidate`를 반환한다. caller는 ownership snapshot이나 delta partition을 조립하지 않는다.
2. `verify(candidate)`가 모든 AC를 fresh source review와/또는 필요한 제품 흐름으로 직접 확인하고
   `VERIFIED`를 반환한다. implementation check만으로는 이 결과를 만들 수 없다.
3. 구현 호출이 응답 전에 끊긴다. 재시작한 caller는 exact ready Ticket으로 `inspect(work)`를
   호출해 공개된 candidate가 있는지
   확인한다. 없으면 성공을 추론하지 않으며 Module은 안전성을 입증하지 못한 작업을 자동 반복하지
   않는다.
4. verification ACTION의 결과를 읽기 전에 호출이 끊기고 외부효과 발생 여부가 모호하다.
   재호출은 effect를 조용히 반복하지 않으며, 충분한 readback/authority가 없으면
   `UNDETERMINED`를 반환한다.
5. 한 AC의 직접 evidence가 불충족을 보이면 `NOT_SATISFIED`다. 같은 AC의 evidence가 단지 없으면
   `UNDETERMINED`다.
6. candidate 이후 source 또는 planning이 바뀌면 기존 candidate의 긍정 검증 결과를 만들지 않는다.
7. `NOT_SATISFIED` 뒤 새 Worker가 수정하면 새 `Candidate`가 생기며, 이전 evidence를 재사용하지
   않고 모든 AC를 fresh verifier가 다시 검증한다.
8. 첫 검증이 `UNDETERMINED`로 끝난 뒤 누락 조건이 해결된다. 같은 exact candidate의 재검증은
   이전 ambiguous effect의 비재실행 또는 safe continuation을 입증한 경우에만 fresh하게 진행된다.
9. exact candidate의 AC 불충족이 충분한 evidence로 먼저 확정된 뒤 unrelated drift가 생겨도,
   그 candidate에 대한 `NOT_SATISFIED`는 보존된다. drift에 영향받은 긍정·미완료 관찰은
   `UNDETERMINED`다.
10. `NOT_SATISFIED`가 완전히 publication된 뒤 live work가 달라지고 caller가 재시작한다.
    `inspect(work)`는 exact historical result를 currentness 관찰과 함께 반환하며 이를 현재 work의
    verdict로 가장하지 않는다.
11. `UNDETERMINED` 뒤 caller가 원래 candidate 값을 잃어도 `inspect(work)`의 result에서 exact
    candidate를 복구해, 조건이 해결된 뒤 안전한 fresh verification 입력으로 사용할 수 있다.

## 명시적 범위 밖

- 최종 함수·CLI 이름, argument와 serialized payload schema
- work/result identity의 digest·handle 형식과 저장 위치·retention
- atomic publication, lineage, concurrency, lock/lease와 recovery algorithm
- Worker dispatch, task decomposition, ownership reconciliation과 implementation checks
- verification plan, evidence taxonomy, runner와 artifact/redaction 방식
- 위험한 외부효과 authorization·replay·readback mechanism
- runtime 통합 검증, migration과 legacy command/schema 제거

## 대안 Interface 판정

### 대안 A — 현재 command를 얇게 묶음

12개 verification command와 capability/claim/run ref를 보존한 facade는 caller 지식이 거의 줄지
않고 Interface가 Implementation만큼 얕다. 목적에 맞지 않아 거부한다.

### 대안 B — 구현과 검증을 하나의 `run-all` 호출로 합침

정상 경로는 짧지만 exact candidate를 독립 검증 전에 관찰·전달할 수 없고, 구현 중단과 검증
미확정을 한 결과로 뭉개기 쉽다. Phase 1의 두 결과 의미를 약화하므로 거부한다.

### 선택 — 두 책임 호출과 한 read-only 복구 호출

`implement`, `verify`, `inspect`는 구현/검증의 의미 분리를 유지하면서 proof machinery를 숨긴다.
Module을 삭제하면 currentness, preservation, restart, evidence 결속 복잡성이 다시 caller마다
퍼지므로 깊이와 locality가 있다.

## Oracle finding 판정 기록

### F1 — drift 전에 확정된 불충족 보존

```text
ORACLE_CLAIM
초안은 candidate 뒤 source 또는 planning이 바뀌면 검증 전체를 UNDETERMINED로 만들어, exact
candidate에서 drift 전에 충분한 independent evidence로 확정된 불충족까지 지운다.

STRONGEST_COUNTERARGUMENT
publication 시점의 authority가 바뀌었다면 과거 관찰을 현재 판정으로 노출하지 않는 것이 가장
단순하고 안전하다. 그러나 NOT_SATISFIED는 현재 source의 포괄적 상태가 아니라 식별된 candidate가
식별된 planning/AC를 만족하지 못했다는 exact 결론이다. 이를 보존해도 새 source의 remediation
권한이나 현재 판정을 자동 부여하지 않는다.

PURPOSE_INVARIANT_AT_RISK
독립 검증의 정확성 및 source·AC·evidence 결속. 이미 직접 입증한 결함을 미확정으로 되돌리면
검증 결과가 실제 evidence보다 부정확해진다.

CONCRETE_EVIDENCE
Phase 1은 drift 뒤 관찰의 긍정 evidence 사용을 금지하고 충분한 independent evidence가 보인
불충족은 실패로 허용한다. verification-lead/SKILL.md의 Identity drift와
test_v3_contradiction_precedes_later_executable_drift는 complete exact contradiction이 later drift보다
우선해 VERIFICATION_FAILED가 됨을 확인한다.

CURRENT_PHASE_OWNERSHIP
NOT_SATISFIED와 UNDETERMINED의 외부 의미와 precedence는 Phase 2 소유다. evidence chronology와
identity binding mechanism은 Phase 5, 실행 증명은 Phase 7 소유다.

SMALLEST_CORRECTION
drift는 긍정 및 drift에 영향받은 결론만 UNDETERMINED로 만들고, drift 전에 exact 결속과 충분한
evidence로 확정된 NOT_SATISFIED는 해당 candidate 결과로 보존한다고 좁혔다.

COMPLEXITY_DELTA
caller 호출·개념·상태·durable protocol 증가 0. 기존 evidence precedence를 Module 안에 숨긴다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — 외부 결과 의미만 수정. mechanism은 Phase 5/7로 위임.
```

### F2 — `UNDETERMINED` 뒤 안전한 fresh verification

```text
ORACLE_CLAIM
초안은 공개된 UNDETERMINED를 영구 반환할지, 조건 해결 뒤 fresh verification을 허용할지 정하지
않아 영구 정체 또는 ambiguous effect의 unsafe replay를 모두 허용한다.

STRONGEST_COUNTERARGUMENT
Module이 내부 reason과 state를 보고 판단하면 caller 계약에 재검증 의미를 추가할 필요가 없다.
그러나 terminal 여부는 caller가 같은 candidate를 다시 검증할 수 있는지 결정하는 외부 복구
의미다. 이를 숨기면 conforming Implementation끼리 관찰 가능한 동작이 달라진다.

PURPOSE_INVARIANT_AT_RISK
중단 뒤 복구 가능성과 외부효과 비재실행, fresh independent verification.

CONCRETE_EVIDENCE
현재 Verification Lead는 INCOMPLETE/BLOCKED 뒤 같은 handoff/source의 fresh result를 허용하면서,
ancestor의 ambiguous effect는 authoritative readback 또는 명시적 safety 없이는 replay하지 않는다.

CURRENT_PHASE_OWNERSHIP
UNDETERMINED의 비종결성과 재호출 의미는 Phase 2 소유다. durable lineage는 Phase 3,
effect safety mechanism은 Phase 6 소유다.

SMALLEST_CORRECTION
새 retry 호출·identifier 없이 같은 verify(candidate)가 currentness와 effect safety를 입증한 경우에만
fresh verification을 시작하고, 그렇지 않으면 effect 없이 UNDETERMINED를 반환한다고 고정했다.

COMPLEXITY_DELTA
caller Interface·정상 성공 경로·상태 증가 0. 기존 open-verification/replay 의식을 숨긴다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — retry 결과 의미만 수정. lineage/replay mechanism은 Phase 3/6으로 위임.
```

### F3 — ready Ticket과 별도 product root의 중복 authority

```text
ORACLE_CLAIM
work 입력에 ready Ticket과 product root를 함께 요구하면 정상 caller가 중복 authority를 조립하고
stale mismatch를 만들 수 있다.

STRONGEST_COUNTERARGUMENT
root를 별도 명시하면 legacy Ticket이나 불완전 planning에도 적용하기 쉽다. 그러나 이 Interface는
exact canonical ready Ticket만 받으며, legacy admission은 확인된 정상 consumer가 아니다.

PURPOSE_INVARIANT_AT_RISK
작은 caller Interface와 정확한 source 선택. 두 authority가 어긋나면 정상 요청 중단 또는 잘못된
source 선택이 가능하다.

CONCRETE_EVIDENCE
matt/skills/to-tickets/SKILL.md는 ready Ticket에 유일하고 canonical인 existing Project-Root를
필수화한다. implementation-lead/SKILL.md도 Ticket이 root를 결정하지 못할 때만 별도 root를 요구한다.

CURRENT_PHASE_OWNERSHIP
정상 caller의 최소 입력은 Phase 2 소유다. root parsing/currentness algorithm은 후속 Implementation
소유다.

SMALLEST_CORRECTION
work를 exact canonical ready Ticket 하나로 줄이고 Module이 Ticket의 Project-Root를 직접 해석한다.

COMPLEXITY_DELTA
caller 개념 -1, 중복 authority -1, mismatch 실패 경로 -1. 새 state/protocol 없음.

DISPOSITION
ACCEPT — 정상 Interface에서 별도 product root 제거.
```

### Follow-up F1 — `inspect`가 보존된 exact 결과를 숨김

```text
ORACLE_CLAIM
drift 전에 완전히 publication된 NOT_SATISFIED를 보존한다고 했지만 inspect(work)가 live drift를
이유로 NoConclusiveResult만 반환하면 재시작 caller에게 그 결과가 사라진다.

STRONGEST_COUNTERARGUMENT
inspect는 현재 exact work만 보여주고 과거 결과는 숨기는 편이 Interface가 작고 stale 결과 오용을
막는다. 그러나 완전한 historical result와 currentness는 서로 다른 관찰이다. 결과를 숨기면 이미
입증된 결함과 복구 가능성을 잃고, currentness를 함께 반환하면 현재 verdict로의 오용을 막을 수 있다.

PURPOSE_INVARIANT_AT_RISK
독립 evidence로 확정된 exact 결과 보존과 중단 뒤 결과 복구.

CONCRETE_EVIDENCE
Phase 1은 결과가 어떤 planning/source/AC/evidence에 관한 것인지 대조 가능해야 한다고 요구한다.
F1 correction과 current verification source는 complete exact contradiction을 later drift 뒤에도
그 candidate의 결과로 보존한다.

CURRENT_PHASE_OWNERSHIP
inspect가 어떤 결과 의미를 돌려주는지는 Phase 2 소유다. historical lookup과 currentness 계산
mechanism은 Phase 3/5 소유다.

SMALLEST_CORRECTION
NoConclusiveResult를 unpublished 또는 결과 자체 결속/무결성 불명으로 좁히고, valid historical
result는 현재 work에 적용 가능한지에 관한 currentness 관찰과 함께 반환한다.

COMPLEXITY_DELTA
호출·verdict·durable state 증가 0, 외부 currentness 관찰 +1. 새 handle/schema는 정하지 않는다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — result/currentness 의미만 수정; mechanism은 Phase 3/5로 위임.
```

### Follow-up F2 — `UNDETERMINED`에서 exact candidate를 복구할 수 없음

```text
ORACLE_CLAIM
verify는 Candidate를 요구하지만 inspect가 최신 UNDETERMINED VerificationResult만 반환하면 담당자
교체 뒤 exact Candidate를 다시 얻어 fresh verification할 보장이 없다.

STRONGEST_COUNTERARGUMENT
VerificationResult가 이미 같은 planning/source를 나타내므로 Module이 내부적으로 candidate를 찾으면
된다. 그러나 caller Interface가 verify(candidate)를 요구하는 이상 caller가 그 입력을 복구할 수
있다는 의미가 없으면 약속된 재검증 호출을 구성할 수 없다.

PURPOSE_INVARIANT_AT_RISK
중단·담당자 교체 뒤 same candidate의 fresh independent verification 복구.

CONCRETE_EVIDENCE
현재 verification-result-v1은 exact implementationHandoffRef를 공개하고, INCOMPLETE/BLOCKED 뒤
fresh verification은 같은 handoff/source를 기반으로 열린다.

CURRENT_PHASE_OWNERSHIP
결과에서 exact candidate를 복구할 수 있다는 의미는 Phase 2 소유다. handle/field/serialization과
lineage 저장은 Phase 3 소유다.

SMALLEST_CORRECTION
모든 VerificationResult가 exact Candidate에 결속되고 caller가 그 candidate를 재검증 입력으로
복구할 수 있다고 명시한다. 새 호출이나 구체 field는 추가하지 않는다.

COMPLEXITY_DELTA
호출·상태·정상 경로 증가 0, 결과 결속 관찰 +1. 기존 handoff ref ceremony를 Candidate 의미로 숨긴다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — semantic recoverability만 수정; representation은 Phase 3로 위임.
```

### F4 — `ImplementationStopped`의 durable restart publication

```text
ORACLE_CLAIM
ImplementationStopped 응답이 유실되면 inspect로 복구할 수 없으므로 완전한 stop도 durable public
result로 추가해야 한다.

STRONGEST_COUNTERARGUMENT
Phase 1이 보존하라고 한 구현 외부 결과는 독립 검증 가능한 Candidate 하나다. ImplementationStopped는
긍정 completion이 아닌 invocation-local 설명이며, 조건과 source가 바뀌면 stale해진다. 응답 유실
뒤 NoConclusiveResult는 “candidate 없음”을 정직하게 나타내고, fail-closed implement 재호출이 현재
planning/source/preservation을 다시 읽는다. durable stop kind를 만들면 새 stale failure와 retention,
currentness, replacement 의미를 추가한다.

PURPOSE_INVARIANT_AT_RISK
Oracle 주장을 거부해도 정확한 구현·사용자 변경 보존·독립 검증·source/AC/evidence 결속은 깨지지
않는다. 오히려 정상 caller와 durable state 단순화 목적이 durable stop 추가로 약해진다.

CONCRETE_EVIDENCE
Phase 1 최소 결과 계약 A는 Candidate 의미만 고정하고, 알려진 미완료나 보존 불확실성이 있으면
candidate를 내지 못하게 한다. 현재 Implementation Lead Terminal return도 stop을 보고하지만 이를
새 immutable public protocol로 만들지 않는다.

CURRENT_PHASE_OWNERSHIP
Phase 2는 restart 결과 의미를 정할 수 있으나, 보존 가치가 없는 새 durable result kind를 만들
의무는 없다. implement 재평가 방식은 Phase 4, crash 검증은 Phase 7 소유다.

SMALLEST_CORRECTION
문서 correction 없음. ImplementationStopped는 호출 응답일 수 있으나 inspect가 보장하는 durable
public result가 아니며, 유실 시 NoConclusiveResult와 fail-closed implement 재평가를 사용한다는
기존 의미를 유지한다.

COMPLEXITY_DELTA
제안을 수용하면 inspect 대안 +1, durable publication kind 최대 +1, stale stop currentness/replacement
상태가 새로 생긴다. 거부하면 증가 0이며 candidate/result recovery만 남는다.

DISPOSITION
REJECT_AS_MECHANISM_PRESERVATION — positive candidate/independent verdict 보존에 필요 없는 durable
stop ceremony를 추가한다.
```

## 완료 판단

같은 DevSpace Oracle conversation의 두 번째 follow-up에서 다음을 다시 공격했다.

- valid historical result와 live currentness의 분리는 complete exact result를 보존하면서 현재
  work의 verdict로 오용되는 경로를 닫았다.
- 모든 VerificationResult에서 exact Candidate를 복구할 수 있어 `UNDETERMINED` 뒤 담당자 교체가
  있어도 같은 candidate의 safe fresh verification을 구성할 수 있다.
- `ImplementationStopped`의 durable publication 거부는 Phase 1이 보존하지 않은 새 failure
  lifecycle을 만들지 않으면서, `NoConclusiveResult`와 fail-closed implement 재평가로 response-loss
  경로를 정직하게 처리한다.
- 위 correction은 새 caller 호출·verdict·identity 입력·durable state를 추가하지 않았다.
- 새 material finding과 사용자 결정은 없다.

Oracle의 수렴 선언 자체가 아니라, 위 주장들을 Phase 1 계약과 current Implementation Lead,
Verification Lead source에 대조해 다음처럼 판정한다.

- Interface는 `implement`, `verify`, `inspect` 세 의미 호출로 현재 proof machinery보다 작다.
- Module을 삭제하면 planning/source currentness, user-change preservation, result recovery,
  candidate/evidence 결속 복잡성이 caller로 다시 퍼진다.
- durable state·concurrency·execution·evidence·effect mechanism을 후속 Phase에 남겼다.
- 수용한 finding은 모두 caller Interface나 상태를 늘리지 않는 최소 correction이다.
- F4는 실제 보존 가치 없이 durable publication kind와 stale-stop lifecycle을 늘려 명시적으로
  거부했다.

**판정: `DESIGN_CONVERGED`.**
