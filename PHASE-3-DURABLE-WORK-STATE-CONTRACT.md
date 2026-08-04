# Phase 3 — durable work state와 동시성

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

Phase 2의 `implement(work, worker)`, `verify(candidate)`, `inspect(work)`가 process 중단과 동시
호출 뒤에도 정직한 결과 의미를 유지하도록, 어떤 최소 durable state와 원자 전이를 한 깊은
Module 안에 숨길지 정한다.

이번 단계의 단일 결정은 다음이다.

> 한 exact work의 완전한 결과 history와 한 개의 active transition을 Module-owned durable state로
> 직렬화하고, 결과 append·current head 이동·active transition 종료를 한 atomic commit으로 묶는다.

schema, database 제품, lock/lease 구현, digest 문자열, migration, Worker 실행, verification runner,
evidence 수집과 외부효과 replay 방식은 정하지 않는다.

## 상속한 사용자 가치와 Interface

- 구현 결과는 알려진 due-now 구현·통합 미완료가 없는 exact `Candidate`이며 final verdict가 아니다.
- `VerificationResult`는 exact Candidate/planning/source/모든 AC/direct evidence에 결속된 독립 판정이다.
- 사용자 기존·동시 변경을 지우거나 구현자 변경으로 허위 귀속하지 않는다.
- evidence 부족은 불충족이 아니며 `UNDETERMINED`다.
- 외부 Interface는 `implement`, `verify`, `inspect` 세 호출뿐이다.
- `inspect`는 완전한 historical result를 currentness 관찰과 함께 반환하고, result에서 exact
  Candidate를 복구할 수 있다.
- `ImplementationStopped`는 invocation 결과일 수 있지만 새 durable public result는 아니다.

## 깊은 Module과 Seam

Phase 2의 Implementation Verification Module 내부에 **Durable Work Module**을 둔다. 이 Module의
seam은 planning/source를 읽고 Worker/verifier를 실행하는 코드와, durable 결과·동시성 state를
소유하는 코드 사이에 있다.

정상 caller는 이 seam을 직접 호출하지 않는다. caller가 아는 것은 Phase 2의 work, Candidate,
VerificationResult와 currentness뿐이다. Durable Work Module은 다음 내부 책임을 한곳에 숨긴다.

- exact ready Ticket을 한 durable work stream에 대응시키기
- Module-owned opaque Candidate/VerificationResult identity 할당
- work별 active transition 단일성
- immutable complete result append와 internal predecessor lineage
- unique current head 선택
- atomic publication과 retry readback
- crash 뒤 active transition re-entry와 safe closure
- result 자체의 결속/무결성과 live work currentness 분리

concrete persistence는 local-substitutable dependency다. production과 test가 다른 public Adapter를
필요로 한다는 근거가 없으므로 storage port를 외부 Interface로 만들지 않는다. 같은 Durable Work
Module Interface를 real temporary store에서도 테스트한다.

## 최소 durable state

### 1. Work stream

하나의 exact canonical ready Ticket locator에 대응하는 내부 stream이다. 이 설계에서 locator는
work identity authority이며 정확한 저장·정규화 형식은 숨긴다. Ticket bytes, planning identity와
source identity는 각 result와 transition에 별도로 결속되므로 같은 locator의 planning이 바뀌어도
과거 결과를 덮어쓰지 않는다.

Ticket rename, move 또는 copy는 새 canonical locator이므로 새 work다. Module은 같은 bytes,
Project-Root 또는 filename이라는 이유로 stream을 병합하지 않는다. rename continuity를 보장하려면
planning-owned stable identity가 먼저 별도 승인되어 Phase 2의 work 의미가 바뀌어야 하며, Phase 3은
임의 UUID·content digest·alias/redirect graph를 발명하지 않는다. 따라서 old locator가 더 이상 exact
ready Ticket으로 존재하지 않는 경우 `inspect(newWork)`가 old stream을 복구한다는 보장은 없다.

Work stream은 다음 의미만 durable하게 가진다.

```text
work identity
current result head 또는 아직 결과 없음
active transition 또는 없음
```

current head는 timestamp나 디렉터리 scan으로 추정하지 않는다. successful atomic append가 정한
유일한 head다.

### 2. Complete result record

`Candidate`와 `VerificationResult`만 durable public result record다. 각 record는 immutable하며
최소한 다음에 결속된다.

```text
Module-owned opaque result identity
work identity
exact planning/AC identity
exact candidate source identity
result kind와 Phase 1/2 의미 payload
internal predecessor result identity 또는 첫 result
```

`VerificationResult`는 자신이 판정한 opaque Candidate identity를 별도로 결속한다. 따라서 current
head가 `UNDETERMINED` result여도 `inspect`가 exact Candidate를 복구할 수 있다.

internal predecessor와 head는 caller가 lineage protocol을 조립하기 위한 Interface가 아니다.
Module이 latest result와 historical exact result를 결정하기 위한 Implementation이다.

### 3. Active transition

한 work stream에는 durable active transition이 최대 하나만 존재한다. transition은 최소한 다음
의미에 결속된다.

```text
Module-owned opaque transition identity
work identity
kind = IMPLEMENT | VERIFY
시작 시의 expected result head
exact semantic input identity
진행 소유 Phase가 재조정에 필요한 private progress reference
```

semantic input identity는 caller가 제공하는 idempotency key가 아니다. Module이 exact ready Ticket,
selected Worker 또는 exact Candidate 같은 이미 필요한 입력에서 내부적으로 만든다. 구체 형식과
비교 알고리즘은 Phase 4/5가 정한다.

active transition은 actor capability, claim, lease, budget reservation 또는 audit session이 아니다.
그 의미는 **이 work에서 새 외부 작업을 시작하기 전에 먼저 재조정해야 하는 하나의 미완료
transition이 있다**는 것뿐이다.

### 4. Physical mutation-domain occupancy

서로 다른 work라도 canonical `Project-Root`가 같은 physical product tree를 가리키거나 서로
포함되어 writable tree가 겹치면 같은 mutation domain에서 충돌한다. source를 변경할 수 있는
active IMPLEMENT transition은 한 overlapping mutation domain에서 최대 하나다.

occupancy는 public claim/token이 아니라 active transition에 결속된 hidden durable fact다. no-op
implementation은 장시간 occupancy를 만들 필요가 없다. **canonical product source mutation이 처음
가능해지기 직전**, Module은 mutation domain을 atomic하게 점유한다. winner는 occupancy를 유지한
상태에서 current source를 다시 읽고 expected source와 일치할 때만 canonical mutation을 시작한다.
occupancy 전의 source observation은 canonical mutation authority가 아니다. mismatch면 product
mutation 없이 Phase 4가 stop, safe close 또는 re-entry를 판정한다. 점유는 Candidate publication
또는 입증된 safe no-result close와 함께 해제한다.

Phase 4의 private candidate workspace처럼 canonical product source와 분리되고 그 밖의 product,
planning, durable-state write가 runtime에서 차단된 Worker 실행은 이 mutation-domain occupancy를
요구하지 않는다. 같은 work의 active transition 단일성은 여전히 duplicate Worker dispatch를 막고,
occupancy는 private result를 canonical source에 채택하기 직전에만 필요하다.

구체적인 canonicalization, containment 비교, index와 lock 방식은 Implementation 선택이다. repository
전체 global lock, path별 lock graph, TTL, renew 또는 steal protocol은 도입하지 않는다.

## 내부 전이 계약

아래 이름은 의미 설명용이며 final 함수명이나 schema가 아니다.

### Begin or re-enter

한 atomic decision에서 current head와 active transition을 읽고 다음 중 하나만 수행한다.

1. active transition이 없고 요청이 current head에서 허용되면 expected head와 semantic input에
   결속된 transition을 만든다.
2. 같은 semantic input의 active transition이 있으면 새 transition이나 새 Worker/verifier 실행을
   만들지 않고 기존 transition에 re-enter한다.
3. 다른 active transition이 있으면 경쟁 호출은 외부 작업을 시작하지 않는다. 기존 transition이
   결과를 내거나 안전하게 닫힌 뒤 current state를 다시 읽는다.

어떤 호출도 “process가 사라졌다”, “오래됐다” 또는 “lease 시간이 지났다”는 이유만으로 active
transition을 빼앗거나 지우지 않는다.

IMPLEMENT transition이 canonical product mutation을 시작하려면 위 work 단일성에 더해 overlapping
physical mutation domain occupancy를 얻어야 한다. 반드시 occupancy 획득 뒤 이를 유지한 채 source
currentness를 다시 확인하고, 일치한 winner만 canonical mutation을 시작한다. 실패한 경쟁
transition과 source mismatch transition은 product source를 변경하지 않는다. private workspace
Worker dispatch는 canonical product mutation이 아니므로 이 ordering의 mutation 시점이 아니다.

### Publish complete result

다음을 한 atomic commit으로 수행한다.

```text
active transition이 여전히 exact work와 expected head를 소유함을 확인
완전한 Candidate 또는 VerificationResult record append
record의 internal predecessor를 expected head에 결속
work의 current head를 새 result로 이동
transition이 보유한 physical mutation-domain occupancy 해제
active transition 종료
commit된 exact result readback
```

occupancy 해제 항목은 transition이 이를 보유한 경우에만 적용된다. Candidate result append,
predecessor/head 이동, occupancy 해제와 active transition 종료는 같은 atomic commit에 모두 남거나
모두 남지 않는다. publication 전 별도 해제나 commit 뒤 별도 해제를 허용하지 않는다.

하나라도 실패하면 새 result, head 이동, transition 종료 중 어느 것도 외부에서 성공으로 보이지
않는다. 재호출은 이미 commit된 exact result를 읽거나 같은 active transition을 재조정한다.

### Close without public result

Phase 4~6의 진행 소유 코드가 source·user change·effect state에 대해 더 이상 복구할 미완료가
없음을 입증한 경우에만 active transition을 atomic하게 닫을 수 있다. 그 뒤 `inspect`는 기존
complete head 또는 `NoConclusiveResult`를 반환한다.

transition이 mutation domain을 점유했다면 safe close와 occupancy 해제도 같은 atomic decision이다.
process death, timestamp 또는 TTL만으로 occupancy를 해제하지 않는다.

`ImplementationStopped`를 저장하기 위해 새 public node를 추가하지 않는다. invocation 응답이
유실되면 다음 `implement`가 current planning/source/preservation을 다시 읽는다.

안전한 closure를 입증하지 못하면 transition을 남긴다. active transition이 남아 있다는 이유로
partial Candidate, failure 또는 verdict를 만들지 않는다.

## 동시성 의미

- 같은 work의 concurrent `implement`/`verify` 호출 중 최대 한 transition만 Worker, verifier 또는
  effectful step을 시작할 수 있다.
- 같은 semantic request는 기존 transition/result에 합류하며 duplicate dispatch를 만들지 않는다.
- 다른 request는 winner의 결과나 safe closure 전까지 외부 작업을 시작하지 않고 이후 current
  state에서 다시 판정한다.
- 서로 다른 work stream은 공유 global lock을 요구하지 않는다. storage Implementation이 필요한
  짧은 commit serialization은 허용하지만 장시간 Worker/verifier 실행 동안 global transaction을
  잡지 않는다.
- 서로 다른 work라도 physical mutation domain이 겹치는 canonical source adoption은 직렬화한다.
  다른 mutation domain의 IMPLEMENT와 read-only VERIFY/inspect는 이 규칙만으로 직렬화하지 않는다.
- result publish는 expected-head compare와 append/head/transition closure를 한 commit으로 묶어
  두 successor나 timestamp-based latest를 허용하지 않는다.
- transition 단일성은 내부 invariant다. caller에게 claim 획득·release·renew 순서를 요구하지 않는다.

## 재시작과 `inspect`

`inspect(work)`는 read-only이며 store를 생성하거나 active transition을 변경하지 않는다.

1. consistent durable read로 unique complete head와 result integrity를 확인한다.
2. active transition이나 partial private progress는 public result로 반환하지 않는다.
3. complete result가 없거나 result 자체의 결속/무결성을 확인할 수 없으면
   `NoConclusiveResult`를 반환한다.
4. complete historical result가 있으면 live planning/source가 바뀌어도 그 exact result를 반환한다.
5. currentness는 다음 세 의미 중 하나로 관찰한다.

```text
CURRENT      stable live planning/source observation이 result와 일치
NOT_CURRENT  stable live observation이 result와 불일치
UNKNOWN      stable live observation 또는 비교를 완료하지 못함
```

currentness는 result verdict가 아니며 durable head를 바꾸지 않는다. `CURRENT`도 호출 뒤 source가
계속 고정된다는 lease가 아니다. 이후 `implement`/`verify`는 effect나 publication 전에 currentness를
다시 확인한다.

active transition이 남은 재시작 호출은 Durable Work Module을 통해 그 transition에 re-enter한다.
Phase 4~6이 private progress와 current source/effect를 읽어 resume, complete-result publication,
safe close 또는 fail-closed 유지 중 하나를 결정한다. 이를 입증하기 전 새 transition을 시작하지
않는다.

## 허용한 실패 의미

- store가 없고 complete result도 없으면 `inspect`는 state를 만들지 않고 `NoConclusiveResult`다.
- result record나 internal lineage/head의 결속·무결성을 확인할 수 없으면 긍정 result를 선택하지
  않고 `NoConclusiveResult`다.
- live planning/source를 안정적으로 읽지 못해도 valid historical result 자체는 반환하며
  currentness는 `UNKNOWN`이다.
- active transition recovery가 불가능하면 그 transition을 자동 삭제하거나 duplicate work를
  시작하지 않는다. caller에게는 기존 complete result 또는 비긍정 invocation 결과만 보인다.
- mutation-domain occupancy recovery가 불가능하면 이를 자동 해제하지 않는다. 다른 work의 Worker도
  같은 physical source를 변경하지 못한다.
- storage가 atomic commit과 durable readback을 제공할 수 없으면 Module은 positive Candidate나
  VerificationResult를 publish하지 않는다.

corruption repair, backup, retention, store relocation과 schema migration은 이번 단계가 보장하지
않는다. 배포가 이 Module의 최소 atomicity를 제공하지 못하면 callable implementation으로 인정하지
않는다는 fail-closed 의미만 고정한다.

## 현재 mechanism에서 삭제·숨길 것

현재 owner store가 입증한 실제 failure path는 concurrent claim의 single winner, stale tip publication
거부, node/edge/tip/claim closure의 atomicity와 restart readback이다. 새 Module은 이 보장을
work stream, active transition, atomic result append로 흡수한다.

정상 caller와 Phase 3 state model에는 다음을 보존하지 않는다.

- Coordinator/Assessor/Remediator/Worker actor row와 capability digest
- invocation과 multi-dimensional budget reservation/consumption
- public claim acquire/release/closure protocol
- separate node/edge graph API와 caller-provided predecessor/tip ref
- audit event, generic authorization, migration fingerprint와 preopen ceremony
- timestamp-based recovery, lease renewal과 process ownership protocol
- global repository lock, path별 lock graph와 caller-visible mutation claim/token

Phase 4~6에서 실제 실행 evidence나 effect safety에 필요한 private fact가 확인되면 각 소유 Phase가
추가할 수 있다. 그것을 Phase 3의 generic workflow ledger로 미리 승격하지 않는다.

## 근거가 있는 최소 시나리오

1. 같은 work에 두 `implement` 호출이 동시에 들어온다. 하나만 transition을 만들고 Worker를
   시작한다. 다른 호출은 duplicate dispatch 없이 같은 결과를 읽는다.
2. 서로 다른 Ticket이 같은 또는 overlapping canonical Project-Root를 가리킨다. private workspace
   Worker는 병행할 수 있지만, mutation domain을 점유한 하나의 IMPLEMENT만 canonical source
   adoption을 시작하며 패자는 source를 변경하지 않는다.
3. Candidate publication commit 전에 process가 죽는다. `inspect`는 partial candidate를 반환하지
   않는다. 재호출은 남은 active transition을 재조정하며 새 Worker를 자동 시작하지 않는다.
4. Candidate append는 성공했지만 응답 전에 process가 죽는다. `inspect`는 complete Candidate를
   반환하고 재호출은 새 Candidate를 중복 append하지 않는다.
5. 같은 Candidate의 두 `verify`가 경쟁한다. 하나만 verifier/effectful execution을 시작하고,
   completion은 한 VerificationResult successor만 만든다.
6. `UNDETERMINED` 뒤 fresh verification은 새 transition이지만 같은 Candidate identity에 결속된다.
   이전 ambiguous effect의 safety를 입증하지 못하면 Phase 6이 effect를 시작하지 못하게 한다.
7. `NOT_SATISFIED` publication 뒤 new implementation이 새 Candidate를 append한다. 과거 result는
   immutable하며 currentness만 달라진다.
8. historical result 뒤 planning/source가 바뀐다. `inspect`는 result를 숨기지 않고
   `NOT_CURRENT`를 함께 반환한다.
9. live identity read가 실패한다. valid historical result는 유지되고 currentness는 `UNKNOWN`이다.
10. Ticket을 rename/move/copy하면 새 work로 취급하고 path·bytes·root heuristic으로 과거 stream을
    합치지 않는다. 두 새 work가 같은 source를 변경하려 하면 mutation-domain 단일성이 적용된다.
11. store의 head/lineage 결속이 읽히지 않는다. timestamp나 파일 순서로 result를 선택하지 않고
   `NoConclusiveResult`로 fail-closed한다.

## 명시적 범위 밖

- concrete database, table, index, transaction mode와 filesystem layout
- ref/digest/version/schema serialization
- schema migration, backup, corruption repair와 retention policy
- Worker task/envelope, source snapshot/delta와 reconciliation algorithm
- verifier plan, evidence taxonomy, runner step와 artifact storage
- authorization, external-effect idempotency/correlation/replay/readback
- timeout, budget accounting, process/OS lock와 distributed deployment
- runtime fault injection, legacy store/command migration과 제거

## Oracle finding 판정 기록

### F1 — 서로 다른 work의 overlapping physical source mutation

```text
ORACLE_CLAIM
work별 active transition만으로는 서로 다른 Ticket이 같은 Project-Root를 가리킬 때 두 Worker가
동시에 source를 변경해 사용자 변경 손실과 허위 attribution을 만들 수 있다.

STRONGEST_COUNTERARGUMENT
Phase 4의 dispatch 직전 source identity 재확인과 after snapshot reconciliation이 drift를 발견할 수
있으므로 Phase 3에 cross-work state를 추가하지 않아도 된다. 그러나 두 호출이 모두 같은 source를
확인한 뒤 동시에 dispatch하면 drift detection은 physical overwrite 뒤에야 작동한다. 이미 잃은 변경을
정확히 복구·귀속할 수 없으므로 사후 검출은 보존 보장이 아니다.

PURPOSE_INVARIANT_AT_RISK
사용자 기존·동시 변경 보존, Worker 변경의 정확한 귀속과 Candidate source identity.

CONCRETE_EVIDENCE
ready Ticket은 각자 canonical Project-Root를 가지지만 서로 다른 Ticket의 root 중복을 금지하지 않는다.
Implementation Lead는 dispatch 전 identity 확인과 Worker 후 changed-path reconciliation을 요구하나,
current race tests는 같은 workflow root claim만 직렬화하고 다른 work의 same-source dispatch는 다루지
않는다.

CURRENT_PHASE_OWNERSHIP
어떤 source-changing transition이 동시에 실행될 수 있는지는 Phase 3 concurrency invariant다.
mutation domain key/index/lock 구현은 Phase 4와 구현 단계가 소유한다.

SMALLEST_CORRECTION
product mutation 직전 overlapping canonical Project-Root domain을 hidden durable occupancy로 하나만
점유하게 한다. no-op 구현, 다른 domain, VERIFY/inspect는 불필요하게 직렬화하지 않는다.

COMPLEXITY_DELTA
caller 호출·token·verdict +0, hidden occupancy 결속 +1, IMPLEMENT mutation 경로 atomic conflict check
+1. global lock/path graph/TTL/renew/steal은 추가하지 않는다. 대신 cross-work ad hoc coordination과
사후 attribution 추측을 숨긴다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — physical source mutation 단일성만 수용; concrete lock과 effectful VERIFY는
Phase 4/6으로 위임.
```

### F2 — Ticket locator rename/copy continuity

```text
ORACLE_CLAIM
canonical Ticket locator가 work identity와 lookup을 겸하면 rename/move/copy 뒤 historical result를
찾지 못하거나 logical work가 여러 stream으로 갈라진다. locator와 별도 planning-owned stable work
identity가 필요하다.

STRONGEST_COUNTERARGUMENT
Phase 2가 승인한 work는 exact canonical ready Ticket 자체다. canonical path는 current planning seal의
authority이며 rename/move/copy를 동일 logical work로 본다는 사용자 가치나 consumer 근거는 없다.
별도 stable identity를 만들면 caller-visible ID 또는 alias/redirect lifecycle이 생기고, path·bytes·
Project-Root heuristic은 잘못된 stream 병합을 허용한다.

PURPOSE_INVARIANT_AT_RISK
rename continuity를 보장하지 않아도 exact Ticket에서의 Candidate, independent verification,
user-change preservation과 same-locator restart 의미는 깨지지 않는다. 반대로 근거 없는 병합은
planning/source 결속을 약화한다.

CONCRETE_EVIDENCE
Phase 2는 work를 exact canonical ready Ticket으로 확정했고, implementation_result planning seal은
canonical absolute Ticket path와 bytes를 함께 검증한다. 지정 source에는 rename continuity를
승인하는 stable planning identity나 실제 consumer가 없다.

CURRENT_PHASE_OWNERSHIP
Phase 3은 work identity를 정할 수 있지만 Phase 2 work 의미를 조용히 넓힐 수 없다. rename continuity가
필요해지면 user-confirmed Phase 2/planning delta가 먼저다.

SMALLEST_CORRECTION
locator가 현재 work identity authority임을 명시하고 rename/move/copy는 새 work로 처리한다. heuristic
병합을 금지하고, old locator 삭제 뒤 new work에서 old result 복구는 보장하지 않는다고 경계를 적었다.

COMPLEXITY_DELTA
새 caller input·stable ID·alias state·redirect protocol 0. 제안 수용 시 최소 durable identity +1과
locator mapping lifecycle이 필요하지만 삭제되는 current complexity의 근거가 없다.

DISPOSITION
REJECT_AS_SCOPE_EXPANSION — 확인되지 않은 rename continuity를 위해 Phase 2 work authority를 넓히지
않는다. 새 work 경계만 명시한다.
```

### Follow-up F1 — occupancy ordering과 Candidate publication closure

```text
ORACLE_CLAIM
mutation-domain occupancy와 source recheck가 모두 dispatch 전이라는 문구만으로는 recheck가 먼저
일어나는 TOCTOU를 허용한다. 또한 Candidate publication atomic commit에 occupancy 해제가 없으면
publication 전 해제로 source 결속이 깨지거나 publication 뒤 orphan occupancy가 남는다.

STRONGEST_COUNTERARGUMENT
source capture와 Worker dispatch, Candidate 생성은 Phase 4 소유이므로 구체 순서와 cleanup을 그
단계에 맡길 수 있다. 그러나 occupancy 전 recheck와 occupancy 후 recheck는 overwrite 가능성이
다르고, publication과 release 분리는 crash 뒤 영구 write block을 만든다. 이는 algorithm 선택이
아니라 Phase 3 concurrency/atomicity 결과 의미다.

PURPOSE_INVARIANT_AT_RISK
사용자 변경 보존, Worker attribution, exact Candidate source 결속과 restart 뒤 구현 복구 가능성.

CONCRETE_EVIDENCE
Implementation Lead는 dispatch 직전 current source와 baseline의 exact 일치를 요구한다. current
store tests는 successor append, head advance와 claim closure의 한-transaction atomicity를 실제
검증하며, mutation occupancy는 새 Module에서 같은 failure boundary를 닫아야 한다.

CURRENT_PHASE_OWNERSHIP
occupancy와 recheck의 ordering 및 publication atomic membership은 Phase 3 소유다. source identity
capture 방식과 mismatch 처리 algorithm은 Phase 4, failpoint 실행 증명은 Phase 7 소유다.

SMALLEST_CORRECTION
occupancy winner만 이를 유지한 채 source를 재확인하고 일치할 때 dispatch하도록 순서를 고정했다.
Candidate publication commit에는 result/head/active close와 함께 occupancy release를 조건부 포함했다.

COMPLEXITY_DELTA
caller Interface·state kind·public failure +0. 새 ordering invariant +1, 기존 atomic commit member +1.
추가 lock/lease/release command 없이 overwrite 추측과 orphan occupancy 수동 복구를 제거한다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — ordering과 atomic closure만 수용; capture/mismatch/fault-injection은 Phase 4/7.
```

## 완료 판단

같은 DevSpace Oracle conversation의 두 번째 follow-up에서 다음을 다시 공격했다.

- occupancy를 먼저 획득한 winner만 이를 유지한 채 source를 재확인하므로 stale pre-occupancy
  observation으로 canonical source mutation을 시작하는 TOCTOU가 닫혔다. Phase 4에서 도입한
  isolated private Worker dispatch는 canonical mutation이 아니므로 이 occupancy를 요구하지 않는다.
- Candidate append, predecessor/head 이동, occupancy release와 active transition close가 한 atomic
  commit에 묶여 publication 전 source 노출과 publication 뒤 orphan occupancy를 모두 막는다.
- mismatch 처리와 source capture algorithm은 Phase 4, kill/failpoint 실행 증명은 Phase 7에 남겨도
  Phase 3의 관찰 의미가 달라지지 않는다.
- exact canonical Ticket locator를 work authority로 유지하고 rename/move/copy를 새 work로 둔 경계는
  Phase 2와 모순되지 않으며, 근거 없는 stable ID·alias lifecycle을 만들지 않는다.
- mutation occupancy는 caller token·capability·TTL·renew·release command가 없는 하나의 hidden
  physical-source exclusion invariant이며 legacy claim ceremony를 재도입하지 않는다.
- 새 material finding과 사용자 결정은 없다.

Oracle의 수렴 선언 자체가 아니라 Phase 1/2 계약, current source와 test baseline에 대조해 다음처럼
판정한다.

- Durable Work Module은 work stream, immutable complete-result chain, unique head, active transition과
  필요한 mutation occupancy만 소유한다.
- caller Interface는 Phase 2의 세 호출 그대로이며 durable state를 조립하지 않는다.
- concurrent publication과 response loss는 atomic append/readback으로, unsafe stale recovery는
  fail-closed active transition 유지로 닫힌다.
- 수용한 correction은 actual cross-work overwrite와 orphan occupancy만 닫고 global/path lock graph,
  actor/claim/budget/audit protocol을 추가하지 않는다.
- rename continuity 제안은 실제 consumer와 planning authority가 없어 명시적으로 거부했다.

**판정: `DESIGN_CONVERGED`.**
