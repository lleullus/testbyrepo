# Phase 4 — Implementation 실행

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

Phase 2의 `implement(work, worker)`가 선택된 Worker를 실행해 exact ready Ticket의 구현 책임을
닫고, 사용자 기존·동시 변경을 잃거나 구현 변경으로 허위 귀속하지 않은 exact `Candidate`를
만드는 방법을 정한다.

이번 단계의 단일 결정은 다음이다.

> Worker는 canonical product source를 직접 변경하지 않고 Module-owned private candidate
> workspace만 변경한다. Implementation Lead는 baseline, Worker 결과와 채택 시점의 live source를
> 대조해 충돌 없는 구현 delta만 canonical source에 채택하고, final source를 다시 닫은 뒤
> immutable Candidate source를 publication한다.

이 분리는 정상 caller가 알아야 할 새 호출·capability·claim을 만들기 위한 것이 아니다. 현재
before/after snapshot이 겹친 변경을 사후 검출하면서도 이미 덮어쓴 사용자 bytes는 보존하지 못하는
실제 실패 경로를 닫기 위한 Module 내부 실행 방식이다.

## 상속한 사용자 가치와 Interface

- caller Interface는 Phase 2의 `implement(work, worker)`, `verify(candidate)`, `inspect(work)` 그대로다.
- `work`는 exact canonical ready Ticket 하나이고 Project-Root는 Module이 Ticket에서 해석한다.
- `Candidate`는 알려진 due-now 구현·통합 미완료가 없는 독립 검증 대기 결과이지 final verdict가
  아니다.
- Candidate는 exact planning/전체 AC, 독립 검증자가 다시 읽을 exact source, 구현 change와 보존한
  기존·동시 change의 구별을 제공한다.
- 사용자 변경을 지우거나 Worker 변경으로 허위 귀속하지 않는다.
- Worker 서술과 implementation check는 구현 폐쇄의 보조 근거일 뿐 최종 AC 판정 evidence가 아니다.
- Phase 3의 work별 active transition, overlapping mutation-domain occupancy, atomic Candidate
  publication과 fail-closed re-entry를 그대로 사용한다.
- `ImplementationStopped`는 invocation-local 비긍정 결과이며 새 durable public result가 아니다.

## 깊은 Module과 실제 Seam

Phase 2의 Implementation Verification Module 안에 **Implementation Execution Module**을 둔다.
정상 caller는 이 Module을 직접 호출하지 않는다. 이 Module이 사라지면 Worker 격리, baseline과
live source의 합성, 충돌 판정, 중단 복구, source/integration closure와 Candidate source 보존이
각 caller와 Worker 지침으로 다시 퍼진다.

실제 내부 seam은 두 곳뿐이다.

1. **Worker Adapter seam** — 선택된 Worker가 writable root 하나에서 bounded implementation
   assignment를 수행한다. production Adapter는 private candidate workspace 밖의 product source를
   Worker가 쓸 수 없게 해야 하고, test Adapter는 같은 제한과 중단 결과를 재현한다.
2. **Source Adoption seam** — immutable baseline, private Worker result와 current canonical source를
   대조하고 충돌 없는 delta만 **현재 exact state를 잃지 않는 선형화된 조건부 mutation**으로
   적용한다. production Adapter는 physical filesystem을, test Adapter는 temporary source tree를
   사용한다.

이 두 seam은 Module 내부다. caller에게 workspace path, snapshot ref, merge plan, assignment ID,
adoption cursor 또는 Adapter 선택을 요구하지 않는다.

## 실행 기준선과 private candidate workspace

Implementation transition을 시작할 때 Module은 current planning/AC와 stable physical source를 읽고,
다음 두 가지를 같은 baseline에 결속한다.

```text
exact planning과 전체 AC identity
canonical Project-Root의 immutable baseline source와 identity
```

baseline retained source에서 transition 전용 private candidate workspace를 만든다. exact materialize
방식은 copy, copy-on-write 또는 동등한 local 방식일 수 있으며 Interface가 아니다. 중요한 조건은
다음뿐이다.

- Worker의 writable product root는 이 workspace 하나다.
- canonical product source는 Worker에게 read-only이거나 아예 writable namespace에 나타나지 않는다.
- planning authority와 Module durable state는 Worker의 mutation scope 밖이다.
- 격리를 실제 runtime이 강제할 수 없으면 Worker를 dispatch하지 않고 `ImplementationStopped`다.
- workspace 생성·검증 실패는 canonical source를 변경하지 않는다.

이 때문에 Worker 실행 중 사용자가 canonical source를 바꾸어도 Worker가 그 bytes를 덮어쓸 수 없다.
또한 workspace의 baseline-to-result delta는 canonical source의 동시 변경과 섞이지 않으므로 누가
canonical source를 바꿨는지 추측하지 않고도 구현 change 후보를 분리할 수 있다.

## 순차 Worker loop

Implementation Lead는 exact Ticket과 current candidate workspace를 직접 읽어 다음 due-now source 또는
integration gap 하나를 선택한다. 한 transition에서 Worker call은 한 번에 하나만 active할 수 있다.

각 call은 다음 순서를 따른다.

1. 현재 planning/AC가 baseline과 동일하고 assignment가 이미 승인된 Ticket 의미 안인지 다시 읽는다.
2. current workspace의 stable identity와 bounded assignment 내용을 private progress에 결속한다.
3. Worker가 실행됐을 수도 있다는 사실을 dispatch 전에 durable하게 남긴다.
4. 선택된 Worker를 workspace에서 한 번 호출한다.
5. Worker 성공 서술과 무관하게 workspace를 stable recapture하고 실제 delta와 source/integration을
   Implementation Lead가 직접 검토한다.
6. 이전 call을 완전히 재조정한 뒤에만 다음 call을 선택한다.

completed task ledger, task ID, criterion-to-task accounting, Worker capability row, per-call event log와
budget accounting은 Candidate 의미에 필요하지 않으므로 보존하지 않는다. 재시작에 필요한 private
progress는 **현재 한 call**의 assignment identity, before workspace identity, Worker가 실행됐을 수
있는지, reconciled workspace identity뿐이다.

Worker가 실행됐을 수 있다는 marker 뒤 process가 중단되면 새 Worker를 자동 dispatch하지 않는다.
재진입은 private workspace를 먼저 recapture한다.

- before identity와 같으면 product source에는 영향이 없으며, Lead가 같은 assignment를 새로 실행할지
  현재 source에서 다시 계획할지 결정할 수 있다.
- workspace가 달라졌으면 그 source를 incomplete Worker result로 직접 검토·재조정한다. Worker의
  성공 response를 복원하지 못해도 delta를 버리거나 성공으로 간주하지 않는다.
- workspace identity나 격리 여부를 확인하지 못하면 canonical source를 채택하거나 Worker를 반복하지
  않고 active transition을 fail-closed로 남긴다.

## Implementation change와 사용자 change의 구별

채택 전 세 source를 비교한다.

```text
B = transition의 immutable baseline source
W = 재조정과 implementation checks가 끝난 private Worker result
L = mutation-domain occupancy를 얻은 뒤 stable recapture한 live canonical source
```

`B -> W`만 implementation change 후보이고, `B -> L`은 Module이 구현 change라고 주장하지 않는
live external change다. Phase 4는 actor causation을 filesystem timestamp나 Worker prose로
발명하지 않는다.

최소 채택 규칙은 path 단위로 보수적으로 정한다.

| B/W/L 관계 | 처리 |
| --- | --- |
| W만 B와 다름 | implementation change로 채택 가능 |
| L만 B와 다름 | external change로 그대로 보존 |
| W와 L이 B에서 같은 최종 값으로 바뀜 | canonical source를 쓰지 않고 external/unattributed change로 보존; Worker 공적으로 세지 않음 |
| W와 L이 같은 path에서 서로 다른 값으로 바뀜 | overlap conflict; 자동 merge·overwrite·Candidate publication 금지 |

여기서 값은 regular-file bytes뿐 아니라 존재 여부, mode, directory와 symlink의 physical identity를
포함한다. 서로 다른 path의 change는 merged target에 함께 남긴다. 같은 file의 서로 다른 hunk를
자동 merge하는 것은 이 단계의 필수 보장이 아니며, 보존을 증명할 수 있는 별도 implementation이
없으면 conflict로 처리한다.

overlap conflict가 나면 live canonical source는 아직 변경하지 않았으므로 사용자 change가 그대로
남는다. Lead는 current authority 안에서 새 baseline과 workspace로 다시 구현할 수 있거나,
결정·보존 조건이 부족하면 `ImplementationStopped`로 돌아간다.

## canonical source 채택과 중단 복구

private result의 source/integration review와 applicable implementation checks가 통과한 뒤에만 canonical
source 채택을 시도한다.

1. Phase 3의 overlapping physical mutation-domain occupancy를 얻는다.
2. occupancy를 유지한 채 live source를 stable recapture한다.
3. 위 B/W/L 규칙으로 merged target을 계산한다. conflict면 product mutation 없이 stop 또는 재계획한다.
4. 첫 canonical mutation 전에 immutable private adoption plan을 durable하게 남긴다. plan은 expected
   live state, 적용할 implementation change와 각 affected path의 intended after state만 가진다.
5. 각 path의 expected-state 검증과 mutation을 Source Adoption Adapter의 한 선형화된 조건부
   operation으로 수행한다. mutation 시점의 actual state가 expected와 다르면 그 state의 bytes와
   physical identity를 잃지 않은 채 아무 intended bytes도 canonical path에 남기지 않는다. Adapter가
   이 의미를 강제할 수 없으면 첫 canonical mutation을 시작하지 않는다.
6. 적용 뒤 canonical source 전체를 stable recapture하고 planning/AC, implementation change,
   preserved external change와 source/integration closure를 다시 확인한다.

filesystem 다중-file write를 atomic이라고 가장하지 않는다. 첫 canonical mutation 전에 transition은
`canonical mutation may have started`라는 한 private fact를 durable하게 남긴다. 그 뒤 process death가
확인되면 source equality만으로 적용 여부나 actor attribution을 추론하지 않는다. `expected`,
`intended`, 그 밖의 current state 모두 보존·분류를 위한 관찰일 뿐 **새 canonical write의 resume
authority가 아니다.** 이는 intended 뒤 user revert가 expected와 같아지는 ABA와, user가 intended와
같은 값을 독립적으로 만든 경우를 구별할 수 없기 때문이다.

따라서 crash 재진입은 canonical adoption write를 자동으로 계속하거나 rollback하지 않는다. current
source의 모든 bytes를 그대로 retain하고, stable source·planning·user preservation을 확인할 수 있으면
추가 write 없이 `ImplementationStopped`와 no-result safe close로 끝낸다. 그 뒤 새 `implement`는 그
preserved current source에서 새 baseline을 만든다. source를 안정적으로 분류·retain할 수 없으면
transition과 occupancy를 fail-closed로 남긴다. 자동 multi-path continuation을 위해 per-path ledger,
generation 또는 mutation witness를 추가하지 않는다.

## implementation checks와 source/integration closure

Worker prose, Worker가 실행한 test와 smoke는 모두 provisional claim이다. Module이 선택한 bounded
implementation check만 구현 폐쇄의 보조 근거로 사용하며 다음을 만족해야 한다.

- exact executable/arguments/working root와 bounded output을 Module이 소유한다.
- check가 source에 쓰지 않는 것이 기본이다. 실제로 필요한 source mutation 또는 위험한 외부효과가
  있으면 Phase 6의 effect seam 없이는 실행하지 않는다.
- mandatory check 실패, timeout, missing tool 또는 unreadable result는 Candidate publication을 막지만
  AC 불충족이나 final verification verdict를 만들지 않는다.
- Candidate publication에 사용한 check는 최종 canonical source identity에 결속된다. 채택 뒤
  preserved external change나 source drift로 identity가 달라지면 필요한 check와 closure를 다시 한다.

Candidate 준비 직전 Implementation Lead는 current exact planning의 모든 AC를 구현 관점에서 다시
읽고 다음만 확인한다.

- 모든 due-now source·test·config·caller·export·compatibility·persistence·migration·UI·integration
  responsibility가 실제 final source에 존재한다.
- 알려진 구현 미완료와 unresolved overlap/preservation 문제가 없다.
- implementation change와 preserved external change partition이 final source와 완전하게 일치한다.
- applicable implementation checks가 exact final source에서 통과했다.

이는 최종 제품 동작 또는 AC 만족 verdict가 아니다. per-AC task accounting과
`unresolvedImplementationItems = []` payload 대신, Module이 final source 전체를 다시 닫지 못하면
Candidate를 publish하지 않는 결과 규칙을 사용한다.

## Candidate source 보존과 publication

closure가 끝나면 final canonical source의 stable physical projection을 immutable하게 retain한다.
Candidate가 가리키는 source는 이 retained exact source이며 live worktree path만이 아니다. 그래야
응답 유실이나 이후 user change 뒤에도 `inspect`와 `verify`가 exact Candidate를 다시 읽을 수 있다.
retained source의 lifetime은 complete Candidate 또는 그 Candidate에 결속된 VerificationResult를
복구할 수 있는 lifetime보다 짧아서는 안 된다. 현재 Baseline Capsule의 독립적인 7일 expiry를 final
Candidate source에 그대로 적용해 historical result만 남기지 않는다.

Candidate record는 Phase 1/2가 요구한 다음 의미에 결속된다.

```text
exact planning과 전체 AC
retained exact candidate source와 identity
채택된 implementation change
candidate에 함께 보존된 external/unattributed change
independent verification pending
```

snapshot handle, digest, manifest와 retention 형식은 caller Interface가 아니다. final retained source가
canonical source capture와 같고 planning이 여전히 current임을 확인한 뒤, Phase 3의 한 atomic
commit으로 Candidate append, predecessor/head 이동, occupancy 해제와 active transition 종료를
수행한다. publication 뒤 live source가 바뀌어도 Candidate를 고쳐 쓰지 않으며 `inspect` currentness가
이를 `NOT_CURRENT` 또는 `UNKNOWN`으로 나타낸다.

zero-mutation implementation도 같은 closure와 immutable final-source retention을 거친다. 장시간
occupancy는 필요 없지만 final live capture와 Candidate publication 사이에는 다른 Module-owned
mutation이 들어오지 않도록 짧게 mutation-domain occupancy를 얻고 같은 publication commit에서
해제한다.

## 허용한 실패·복구 의미

- planning/AC가 바뀌면 old planning을 조용히 채택하지 않고 canonical source mutation 전 stop한다.
- private workspace 생성·격리·stable capture가 실패하면 Worker를 시작하거나 canonical source를
  변경하지 않는다.
- Worker response가 유실돼도 canonical source에는 영향이 없다. private workspace를 먼저 읽어
  continuation 가능성을 판단하고 duplicate dispatch를 금지한다.
- B/W/L overlap은 user change를 덮어쓰기 전에 stop한다.
- conditional mutation의 선형화점에서 source가 expected state가 아니면 실제 current state를
  보존하고 intended bytes를 남기지 않는다.
- canonical mutation may-have-started 뒤 crash가 나면 source equality로 자동 continuation이나
  attribution을 승인하지 않고, 추가 write 없는 safe close 또는 fail-closed 유지로 간다.
- check 실패와 알려진 implementation gap은 Candidate가 아니며 final AC failure도 아니다.
- complete Candidate publication 전 중단은 `inspect`에서 partial Candidate로 보이지 않는다.
- Candidate commit 뒤 response 유실은 `inspect`가 exact retained Candidate를 반환한다.
- source, workspace, adoption plan 또는 preservation state를 재구성하지 못하면 자동 Worker replay,
  overwrite, rollback, occupancy steal을 하지 않는다.

## 근거가 있는 최소 시나리오

1. dirty baseline에서 Worker가 private workspace의 한 path만 바꾼다. baseline에 이미 있던 사용자
   change는 Candidate에 남지만 implementation change로 세지 않는다.
2. Worker 실행 중 사용자가 canonical source의 다른 path를 바꾼다. 채택은 두 delta를 합치고 user
   path를 preserved external change로 기록한다.
3. Worker와 사용자가 baseline 뒤 같은 path를 서로 다르게 바꾼다. canonical user path는 손대지 않고
   overlap conflict로 stop 또는 새 baseline 재계획한다.
4. Worker와 사용자가 같은 path를 동일한 값으로 바꾼다. canonical source를 다시 쓰지 않고 그 path를
   external/unattributed로 보존한다.
5. Worker response 전에 process가 죽는다. 재진입은 private workspace를 읽고 새 Worker를 자동 호출하지
   않는다.
6. canonical adoption 도중 process가 죽는다. 재진입은 exact path equality를 resume authority로 쓰지
   않고 current source를 retain한 채 추가 write 없는 safe close 또는 fail-closed 유지로 간다.
7. path condition 확인 직후 사용자가 그 path를 바꾼다. 선형화된 conditional mutation은 그 actual
   state를 잃지 않고 intended write를 거부한다.
8. Worker implementation check가 통과했지만 final canonical identity에서 mandatory check가 실패한다.
   Candidate와 verification verdict를 publish하지 않는다.
9. 현재 source가 이미 Ticket의 due-now implementation obligation을 충족한다. 짧은 final occupancy와
   exact retention 뒤 zero-mutation Candidate를 publish한다.
10. Candidate commit 뒤 응답이 유실된다. `inspect(work)`가 exact retained source와 결속된 Candidate를
   반환하며 duplicate Worker나 Candidate를 만들지 않는다.
11. planning 또는 source가 final retention/publication 전에 바뀐다. stale Candidate를 publish하지
    않고 사용자 source를 보존한다.

## 현재 mechanism에서 삭제·숨길 것

새 Implementation Execution Module은 다음 current 보장을 흡수한다.

- stable full-source capture와 retained physical source identity
- Worker 전후 실제 delta 관찰
- unexpected/concurrent change의 비귀속과 preservation review
- sequential Worker execution과 final source/integration closure
- implementation check의 provisional 성격
- final Candidate의 planning/source 결속

다음 current mechanism은 Phase 4의 정상 caller나 새 durable public protocol에 남기지 않는다.

- task ID와 criterion-to-task accounting
- allowed/forbidden path envelope를 caller가 조립하는 절차
- Worker capability mint/digest와 actor row
- `FROZEN -> DISPATCHED -> CAPTURED -> RECONCILED` public-shaped state machine
- per-call immutable event log와 reconciliation payload 제출
- implementation transaction capability와 budget accounting
- caller-provided handoff request, baseline/delta ref와 status field
- Worker prose를 attribution이나 completion proof로 쓰는 경로

대신 Module 내부에는 현재 한 Worker call의 최소 recovery fact, immutable baseline/private workspace,
한 adoption plan과 retained final Candidate source만 남는다. normal caller의 호출 수와 입력 개념은
Phase 2보다 증가하지 않는다.

## 명시적 범위 밖

- final CLI/function 이름과 serialized payload/schema
- concrete copy/COW/container/sandbox 기술과 filesystem layout
- source identity digest, manifest, retention 기간과 quota
- path adoption primitive, fsync와 concrete crash failpoint
- independent verifier plan, evidence taxonomy, runner와 final verdict
- 위험한 외부효과 authorization·correlation·replay·readback
- runtime fault-injection 증명, migration과 legacy source/schema/command 제거

## Oracle finding 판정 기록

### F1 — path precheck 뒤 user write overwrite

```text
ORACLE_CLAIM
초안의 expected-state precheck와 실제 path mutation 사이에 사용자가 같은 path를 바꾸면 adoption이
그 bytes를 덮어쓰며, final recapture로는 잃은 bytes를 복구할 수 없다.

STRONGEST_COUNTERARGUMENT
Phase 3 occupancy와 final recapture가 source drift를 막거나 발견할 수 있고 concrete CAS/rename은
Phase 7 구현·fault-injection 소유라고 볼 수 있다. 그러나 occupancy는 Module-owned mutation만
직렬화하고 일반 사용자 write는 막지 않는다. final recapture는 overwrite 뒤 검출일 뿐 보존이
아니므로, concrete primitive가 아니라 Source Adoption seam의 조건부 mutation 의미는 Phase 4가
고정해야 한다.

PURPOSE_INVARIANT_AT_RISK
사용자 동시 변경 보존과 canonical mutation 전 conflict 차단.

CONCRETE_EVIDENCE
current `test_same_task_replacement_overlap_stays_captured_and_fails_closed`는 external app.txt 뒤 Worker가
같은 canonical path를 덮고 reconciliation만 실패한다. current transaction source도 after capture 뒤
overlap을 거부할 뿐 overwritten bytes를 복원하지 않는다. 초안의 check-then-write는 같은 race를
adoption 시점에 남겼다.

CURRENT_PHASE_OWNERSHIP
Source Adoption seam이 어떤 mutation을 허용하는지는 Phase 4 소유다. CAS/atomic exchange/mount 같은
concrete Adapter와 kill failpoint는 구현/Phase 7 소유다.

SMALLEST_CORRECTION
expected-state 검증과 mutation을 한 선형화된 conditional operation으로 묶고, mismatch면 actual state를
잃지 않은 채 intended write를 남기지 못하게 한다. Adapter가 이를 보장하지 못하면 mutation을 시작하지
않는다.

COMPLEXITY_DELTA
caller 호출·public state·durable state +0. internal Adoption seam 의미 +1. overwrite 뒤 rollback·복구
추측을 제거한다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — preservation 의미만 수용하고 concrete filesystem primitive는 구현/Phase 7로
위임한다.
```

### F2 — crash recovery source-state ABA

```text
ORACLE_CLAIM
crash 뒤 current path가 expected이면 미적용, intended이면 적용 완료라고 판단하면, 적용 뒤 사용자가
expected로 되돌린 ABA를 다시 덮거나 사용자가 intended를 만든 경우 Worker change로 허위 귀속한다.

STRONGEST_COUNTERARGUMENT
exact content/mode identity가 같으면 최종 source 관점에서는 같은 상태이므로 자동 continuation도
무해하다고 볼 수 있다. 그러나 사용자가 명시적으로 intended에서 expected로 되돌린 행위 자체가
보존 대상이며, 동일 bytes는 actor나 mutation generation을 증명하지 않는다. source-only 판정으로
다시 쓰는 것은 Phase 1의 비허위 귀속과 user change preservation을 깨뜨린다.

PURPOSE_INVARIANT_AT_RISK
crash 중 사용자 변경 보존, Worker attribution의 정직성, duplicate mutation 금지.

CONCRETE_EVIDENCE
Baseline/ownership identity는 bytes·mode·size·existence를 비교할 뿐 mutation generation을 갖지 않는다.
초안의 expected/intended recovery table은 이 정보만으로 application 여부를 단정했다.

CURRENT_PHASE_OWNERSHIP
canonical adoption crash 뒤 resume authority는 Phase 4 소유다. concrete crash injection은 Phase 7이다.

SMALLEST_CORRECTION
canonical mutation may-have-started marker 뒤 crash가 나면 source equality로 새 write나 attribution을
승인하지 않는다. current source를 보존·retain할 수 있으면 추가 write 없는 ImplementationStopped와
safe close, 아니면 fail-closed 유지로 간다. per-path ledger나 mutation witness는 추가하지 않는다.

COMPLEXITY_DELTA
caller Interface·public failure·per-path durable state +0. private may-have-started fact +1은 Phase 3의
기존 private progress reference 안에 들어간다. 자동 resume와 ABA 추측을 삭제한다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — 보수적 no-write recovery를 수용하고 자동 continuation용 ledger는
REJECT_AS_MECHANISM_PRESERVATION.
```

### F3 — Phase 3 occupancy와 private Worker dispatch의 문구 충돌

```text
ORACLE_CLAIM
Phase 3은 occupancy winner만 Worker를 dispatch한다고 하지만 Phase 4는 private Worker를 occupancy 전에
실행하므로 두 계약을 동시에 만족할 수 없다.

STRONGEST_COUNTERARGUMENT
Phase 3 문맥의 Worker dispatch는 product mutation이 가능한 canonical Worker를 뜻하므로 private
workspace Worker에는 이미 적용되지 않는다고 해석할 수 있다. 그러나 normative 문장이 literal
Worker dispatch를 반복해 conforming Implementation이 긴 private Worker loop 동안 occupancy를 잡는
구 claim 비용을 재도입할 수 있다.

PURPOSE_INVARIANT_AT_RISK
작은 정상 경로, 불필요한 장시간 직렬화 제거와 Phase 간 계약 일관성.

CONCRETE_EVIDENCE
Phase 3 occupancy 절은 first Worker dispatch와 winner-only dispatch를 명시하고, Phase 4는 adoption
직전에 occupancy를 얻는다. private workspace는 canonical source를 변경하지 않는다.

CURRENT_PHASE_OWNERSHIP
private execution 도입으로 canonical mutation 시점이 바뀐 사실은 Phase 4가 발견했지만, 문구
correction은 Phase 3 concurrency invariant에 반영해야 한다.

SMALLEST_CORRECTION
Phase 3의 occupancy gate를 first canonical product mutation으로 좁히고, private workspace Worker는
같은-work transition 단일성만 적용받으며 occupancy는 adoption 직전에 얻는다고 명시했다.

COMPLEXITY_DELTA
caller Interface·state·protocol +0, occupancy 보유 시간 감소. 새 mechanism 없음.

DISPOSITION
ACCEPT — 기존 invariant의 의도를 private-workspace model에 맞게 좁힌다.
```

## 완료 판단

같은 DevSpace conversation의 두 follow-up에서 correction을 다시 공격했다.

- F1은 Source Adoption seam이 precheck와 write를 분리하지 않고, 선형화 시 actual state mismatch면
  actual bytes/physical identity를 잃지 않으며 intended bytes를 남기지 못하게 해 닫혔다.
- F2는 canonical mutation may-have-started 뒤 equality를 resume/attribution authority로 쓰지 않고
  no-write safe close 또는 fail-closed 유지로만 가므로 ABA와 duplicate write가 닫혔다.
- F3은 occupancy가 canonical adoption만 직렬화하고 isolated private Worker는 같은-work transition
  단일성만 적용받으므로 cross-work loss와 장시간 claim 회귀를 함께 막는다.
- final Candidate source는 result recoverability lifetime에 결속되어 baseline payload의 독립 expiry와
  혼동되지 않는다.
- task/envelope/event/criterion accounting/budget를 삭제해도 final exact planning/전체 AC와 actual
  source/integration closure가 알려진 due-now gap 부재를 다시 확인한다.
- caller Interface, public result kind, per-path durable ledger, rollback/replay protocol은 늘지 않았다.
- 새 material finding과 사용자 결정은 없다.

첫 follow-up `slots-followup-phase4fo-1cdf1df7c0`과 두 번째 follow-up
`slots-followup-phase4fo-a3a9f3b480`은 모두 같은 slot 1 conversation URL에 prompt가 실제 제출되고
완성 답변이 UI harvest로 확인됐다. 다만 wrapper prompt-commit probe timeout이 먼저 발생해 두 stock
child session status와 authoritative readback verification은 error로 남았다. 이 delivery-state 오류나
Oracle의 `CLOSED` 선언 자체를 설계 근거로 사용하지 않았다.

주 설계자는 Phase 1~3 계약, current ownership snapshot/transaction source와 overlap test에 각
correction을 독립 재대조했다. private workspace는 current same-path overwrite를 canonical mutation
전에 차단하고, conditional adoption은 adoption 자체의 race를 막으며, crash 뒤 no-write recovery는
source-only ABA 추측을 제거한다. 추가된 private fact는 current Worker call과 canonical mutation
may-have-started 두 개뿐이고 Phase 3의 private progress reference 안에 숨는다. 대가로 current
task/envelope/capability/event/accounting과 unsafe automatic recovery가 삭제된다.

concrete Worker isolation, conditional filesystem mutation, marker/write durability ordering,
kill-point recovery, overlapping-root adoption과 retained-source lifecycle은 아직 구현·runtime으로
증명되지 않았다. 이는 Phase 4 semantic contract의 열린 설계 finding이 아니라 Phase 7의 필수 실행
검증 대상이다.

**판정: `DESIGN_CONVERGED`.**
