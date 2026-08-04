# Phase 7 — 통합·runtime 검증

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

Phase 1~6의 단순화가 문서상 의미에 그치지 않고, 새 Implementation Verification Module의 실제 실행에서
정확한 구현, 사용자 변경 보존, fresh 독립 검증, source·AC·evidence 결속과 위험한 effect 안전성을
보존하는지 증명할 최소 runtime evidence를 정한다.

이번 단계의 단일 결정은 다음이다.

> 새 public `implement`, `verify`, `inspect` Interface를 주 test surface로 삼아 대표 정상·실패·중단·
> 동시성 flow를 실행한다. public outcome만으로 물리 보장을 증명할 수 없는 Worker confinement,
> Verifier/Runner isolation, Source Adoption과 Effect Observation Adapter에는 bounded conformance probe를
> 적용한다. 새 경로가 legacy command/store 없이 이 evidence를 모두 통과하기 전에는
> `RUNTIME_VERIFIED`나 legacy 삭제를 허용하지 않는다.

Phase 7은 제품 구현을 시작하지 않는다. 이 문서는 새 구현이 생긴 뒤 어떤 실행 증거가 통과해야 하는지와
그 증거가 무엇을 의미하는지만 정한다.

## 상속한 사용자 가치와 Interface

- caller가 아는 정상 Interface는 `implement(work, worker)`, `verify(candidate)`, `inspect(work)`뿐이다.
- Candidate는 exact planning/전체 AC, retained exact source와 보존된 user/external change에 결속된다.
- VerificationResult는 fresh 관점의 runner-owned direct evidence로 모든 AC를 판정한다.
- evidence 부족은 `UNDETERMINED`, direct contradiction만 `NOT_SATISFIED`다.
- implementation check는 final verification evidence가 아니다.
- dangerous effect는 exact non-self-grant authority, pre-dispatch may-have-run, non-reexecution,
  authoritative readback과 필요한 cleanup/final disposition을 만족한다.
- response loss와 crash 뒤에는 공개 완료 결과만 `inspect`에 보이며 unsafe work는 자동 반복하지 않는다.

테스트가 internal actor, capability, claim, run/flow/step ref, ledger row 또는 legacy status를 assertion
surface로 사용하면 새 Interface를 증명한 것이 아니다.

## 증명 구조

Phase 7은 새 production Module을 하나 더 만들지 않는다. test harness는 다음 두 층만 가진다.

1. **Public contract harness** — 실제 새 entrypoint를 통해 `implement`, `verify`, `inspect`를 호출하고
   Candidate, VerificationResult, currentness와 source/effect의 외부 관찰을 검증한다.
2. **Adapter conformance harness** — public result만으로 물리적 원자성·격리·dispatch ordering을 구분할 수
   없는 production Worker, Fresh Verifier/Evidence Runner, Source Adoption과 Effect Observation Adapter의
   실제 namespace·mount·transport path에 bounded behavior probe를 적용한다.

production Adapter와 deterministic test Adapter는 각 Seam에 적용되는 같은 의미의 conformance를 통과해야
한다. test 전용 Adapter만 통과하고 production Adapter의 실제 namespace/mount/transport path를 실행하지
않은 상태로 runtime verification을 선언하지 않는다.
다만 production effect Adapter의 conformance는 실제 production message/payment를 보내는 방식이 아니라,
그 Adapter가 공식 지원하는 sandbox/non-production target이나 provider test surface에서 수행한다. 안전한
conformance target이 없으면 해당 Adapter는 enable하지 않고 전체 Module의 다른 경로를 막지 않는다.

test-only failpoint와 scheduler hook은 허용하지만 public Interface나 production caller configuration으로
노출하지 않는다. 내부 schema, digest 문자열, table 수와 private method call을 contract assertion으로
고정하지 않는다.

## 증거의 네 종류

### 1. Public outcome evidence

실제 public Interface 반환값과 `inspect` readback, canonical/retained source 및 외부 target의 관찰이다.
정상 caller가 볼 수 없는 private state는 성공 증거를 대신하지 않는다.

### 2. Adapter-owned physical evidence

read-only source write 차단, conditional mutation linearization, external dispatch count, authoritative
readback과 cleanup final state처럼 물리적 surface에서 얻은 evidence다. fake가 작성한 성공 flag만으로
대체하지 않는다.

### 3. Fault-boundary evidence

의미가 바뀌는 최소 linearization boundary에서 process termination, response loss, competing write 또는
tool failure를 주입하고 재호출·`inspect` 결과를 관찰한다. 모든 instruction이나 임의 corruption 조합을
열거하지 않는다.

### 4. Legacy-independence evidence

새 path 실행 중 legacy CLI, legacy public command dispatcher, actor/capability issuance, authorization/
replay command와 legacy result publisher가 호출되면 test가 실패한다. 구 DB table이 우연히 존재하지
않는다는 사실만으로 독립성을 주장하지 않는다.

## 필수 public contract flow

다음 flow는 최종 구현 내부 구조와 무관하게 새 public Interface에서 실행돼야 한다.

### A. 구현과 사용자 변경 보존

1. **dirty-source success** — baseline에 이미 있던 user change와 Worker의 disjoint change가 모두 final
   source와 Candidate에 남고, Worker change와 external/unattributed change가 구별된다.
2. **same-path overlap stop** — Worker private result와 live user change가 같은 path에서 다르면 canonical
   user bytes를 한 번도 덮지 않고 Candidate 없이 stop한다.
3. **same-final-value non-attribution** — Worker와 user가 같은 final value를 만들면 canonical path를 다시
   쓰지 않고 Worker 공적으로 허위 귀속하지 않는다.
4. **zero-mutation Candidate** — 이미 Ticket obligation을 만족하는 source도 exact retention과 closure 뒤
   Candidate가 되며 final verdict로 가장하지 않는다.
5. **known gap/check failure** — mandatory implementation gap, check timeout 또는 unreadable result는
   Candidate를 만들지 않고 AC failure도 만들지 않는다.

### B. fresh verification과 결과 의미

6. **fresh full-AC positive** — implementation check를 전달하지 않은 fresh Verifier가 전체 AC를 새 plan에
   포함하고 direct source/runtime evidence로만 `VERIFIED`를 만든다.
7. **disconnected/missing observation** — component success가 있어도 required product flow가 없으면
   `UNDETERMINED`이고 `VERIFIED`가 아니다.
8. **direct contradiction** — complete exact evidence가 한 AC를 반박하면 `NOT_SATISFIED`; unrelated missing
   evidence나 later drift가 그 exact historical contradiction을 지우지 않는다.
9. **tool/evidence failure** — timeout, missing executable, source isolation 실패와 readback 판독 불능은
   `UNDETERMINED`이며 product contradiction으로 승격되지 않는다.
10. **source non-mutation** — Verifier/Runner의 Candidate 또는 canonical source write 시도는 물리적으로
    실패하고, writable scratch가 source namespace를 shadow하지 않는다.
11. **fresh namespace** — 새 Verifier가 Worker prose, implementation check, 이전 plan/verdict/raw artifact를
    읽을 수 없고 현재 transition Runner evidence만 받는다.

### C. 결과 복구와 currentness

12. **Candidate commit response loss** — commit 뒤 응답을 잃어도 `inspect(work)`가 exact retained Candidate를
    돌려주고 Worker/Candidate를 중복 생성하지 않는다. 이어서 `verify(candidate)`가 fresh verifier를
    정확히 한 번 시작하고, overlapping root의 다른 합법적 adoption도 진행돼 orphan transition/occupancy가
    없음을 public behavior로 확인한다.
13. **VerificationResult commit response loss** — result commit 뒤 응답을 잃어도 `inspect`가 exact result와
    복구 가능한 Candidate를 반환한다. `UNDETERMINED`이면 fresh verify, `NOT_SATISFIED`이면 별도 implement
    같은 result 의미상 다음 합법적 transition이 정확히 한 번 시작될 수 있어야 한다.
14. **retained Candidate plus canonical drift** — Candidate를 source A에서 publish한 뒤 verification 전에
    canonical source를 B로 변경하고 process를 재시작한다. `verify(candidate)`는 live B가 아니라 retained
    exact A를 실제 source input으로 사용해 historical VerificationResult를 만든다. 안정적으로 읽히는 B를
    둔 정상 fixture에서 `inspect`는 그 result와 반드시 `NOT_CURRENT`를 함께 반환하며, A의 historical
    evidence로 current-positive `SATISFIED`/`VERIFIED`를 만들지 않는다. `UNKNOWN`은 live currentness
    observation 자체를 의도적으로 실패시킨 별도 variant에서만 허용한다.
15. **no complete result** — partial transition, corrupt binding 또는 unreadable head에서 timestamp/파일
    순서로 결과를 추정하지 않고 `NoConclusiveResult`다.

### D. 위험한 effect

16. **no actual authority, no dispatch** — exact non-self-grant authority가 없거나 Candidate가 grant를
    자기 작성하면 external dispatch count는 0이고 결과는 `UNDETERMINED`/`ImplementationStopped`다.
17. **authenticated pure read** — consequence 없는 authenticated read는 fresh evidence를 만들되
    may-have-run/replay/cleanup lifecycle이나 external mutation을 만들지 않는다.
18. **timeout plus authoritative readback** — action response가 ambiguous해도 correlated/current readback이
    effect를 확인하면 action count 1로 complete evidence를 만든다.
19. **ambiguous non-reexecution** — readback도 불명확하면 same Candidate의 여러 `UNDETERMINED`와 새
    Candidate에서도 overlapping occurrence action count가 1을 넘지 않는다.
20. **completed implementation occurrence** — implementation check가 완료한 occurrence는 Candidate 뒤
    fresh verification에서 action을 반복하지 않고 new readback-only evidence로 판정한다.
21. **cleanup/final disposition** — temporary target은 pre-authorized cleanup과 final absence/restored-state
    readback이 complete해야 닫힌다. cleanup timeout은 success가 아니고 duplicate cleanup도 하지 않는다.
22. **contradiction/drift containment** — action may-have-run 뒤 contradiction/drift가 생기면 unrelated new
    action은 0회이고, safe pre-fixed readback/cleanup만 수행하며 current positive verdict는 만들지 않는다.

### E. remediation 재진입

23. **failed result to new Candidate** — exact `NOT_SATISFIED` 뒤 자동 source mutation 없이 별도
    `implement(work, worker)`가 current planning/source/preservation을 다시 읽고 새 Candidate를 만든다.
    새 Candidate는 이전 source와 구별되고, fresh Verifier가 이전 plan/evidence를 읽지 않은 채 전체 AC를
    다시 검증한다. 이전 effect safety fact는 duplicate consequence 방지에만 적용된다.
24. **authority delta stop** — 실패를 고치려면 새 product/planning 결정이 필요한 경우 Worker를 임의
    dispatch하지 않고 `ImplementationStopped`로 돌아가며 기존 source와 historical result를 보존한다.

## 필수 concurrency와 fault-boundary flow

아래는 Phase 3~6에서 의미를 바꾸는 최소 failure boundary다.

1. 같은 work의 concurrent implement/verify에서 외부 Worker/verifier/effect owner가 하나뿐이다.
2. 다른 work가 overlapping mutation domain을 채택하려 할 때 canonical mutation winner가 하나뿐이고,
   loser는 source를 변경하지 않는다.
3. occupancy 획득 뒤 source recheck 직전에 user write가 생기면 adoption은 user bytes를 보존하고 멈춘다.
4. Source Adoption의 expected-state observation과 mutation 사이 경쟁 write에서 intended bytes가 actual
   user bytes를 덮지 않는다.
5. Worker may-have-run 뒤 response loss는 private workspace를 재조정하고 duplicate Worker dispatch를
   하지 않는다.
6. canonical mutation may-have-started 뒤 process death는 current source를 보존하며 automatic
   continuation/rollback/write attribution을 하지 않는다.
7. result append atomic commit 직전 중단은 partial result를 보이지 않고 동일 요청을 safe re-enter하거나
   fail-closed한다. commit 직후 response loss는 exact result를 readback한 뒤 flow 12·13의 다음 합법적
   public transition과 overlapping adoption까지 진행한다.
8. effect may-have-run 직전/직후 중단에서 durable marker 없는 dispatch는 0회이고, marker 뒤 ambiguous
   dispatch는 새 action 없이 readback/UNDETERMINED로 복구한다.
9. live Worker/Runner owner가 있을 때 competing publication은 이를 crash로 재분류하거나 transition을
   닫지 않는다.

각 failure boundary는 “exception을 던졌다”가 아니라 source bytes, external dispatch counter, target final
state, public result와 재호출 결과로 판정한다.

## Adapter conformance

### Worker Adapter confinement

production Worker Adapter가 실제로 조립하는 process/container namespace에서 test Worker가 다음 쓰기를
시도한다.

- private candidate workspace 안의 허용된 source write는 성공한다.
- canonical product source, planning authority와 Module durable-state path write는 물리적으로 실패한다.
- 실패 뒤 외부 bytes와 identity는 그대로이며 private result만 recapture된다.

deterministic Worker의 약속이나 post-hoc reconciliation만으로 이 probe를 대신하지 않는다. Worker의
semantic 품질을 시험하는 것이 아니라 production confinement path를 시험한다.

### Fresh Verifier와 Evidence Runner isolation

production launcher가 만드는 실제 namespace/input projection에 이전 verdict·plan·raw artifact와
implementation check의 상반된 canary를 둔다. Fresh Verifier는 이를 읽지 못하고 exact Candidate/planning/
전체 AC 및 current Runner capability만 받는다. Candidate/canonical source write와 Runner 밖의 실행 결과
제출도 물리적으로 실패해야 한다.

모델의 자연어 출력을 snapshot 비교하지 않는다. launcher의 readable/writable namespace, 전달 input과
Evidence Runner ownership을 deterministic probe로 확인한다.

### Source Adoption Adapter

production과 temporary-filesystem Adapter 모두 다음을 만족해야 한다.

- immutable baseline/private result/live source의 physical identity를 안정적으로 관찰한다.
- expected-state 검증과 mutation의 linearization 사이 competing write를 덮지 않는다.
- multi-path atomicity를 가장하지 않고 may-have-started 뒤 automatic continuation/rollback을 하지 않는다.
- regular file bytes뿐 아니라 existence, mode, directory와 symlink identity를 보존·비교한다.
- final retained Candidate source가 canonical capture와 일치하고 result recoverability보다 먼저 사라지지
  않는다.

구체 CAS, rename, open-fd, mount와 fsync 방법은 Adapter Implementation 선택이다. conformance는 그 방법이
아니라 위 observable behavior를 검증한다.

### Effect Observation Adapter

각 enabled production Adapter와 deterministic target Adapter는 다음을 만족해야 한다.

- fixed Adapter가 canonical target와 occurrence를 기계적으로 구분한다.
- positive grant는 Candidate/effect writable namespace 밖에서만 읽고 Candidate restriction과 교차한다.
- external dispatch 전에 durable may-have-run이 관찰 가능하며 live owner가 중복 dispatch를 막는다.
- provider-enforced idempotency/correlation이 없으면 문자열/argv equality를 replay safety로 쓰지 않는다.
- action response를 persistent final state로 가장하지 않고 authoritative readback을 수행한다.
- started polling/action/readback/cleanup subattempt를 모두 bundle에 포함한다.
- terminal receipt로 인정한 provider fact가 submitted/accepted가 아니라 실제 authoritative final
  observable임을 sandbox/test surface에서 보인다.
- credential과 protected payload가 evidence에 노출되지 않고, 필요한 projection이 불가능하면
  nonconclusive result다.

## replace-don’t-layer 검증

새 tests는 current 12-command verification protocol과 transaction/claim/capability choreography 위에
추가하지 않는다. 새 public contract harness가 같은 사용자 가치를 증명하면 그 가치에 대응하던 old
shallow-command unit test는 Phase 8 삭제 대상이 된다.

Phase 7 중에는 old baseline suite를 보존해 회귀 reference로 사용할 수 있지만 다음을 금지한다.

- old handoff/result를 새 Candidate/VerificationResult로 변환해 test success를 만드는 compatibility path
- new path가 legacy CLI를 subprocess로 호출하는 facade
- effect를 old와 new에서 각각 실행해 outcome을 비교하는 dual-run
- legacy ledger row를 새 evidence로 읽는 shadow certification
- old test count 또는 Freeze 22 checklist 통과만으로 new Module을 `RUNTIME_VERIFIED`라 선언

read-only comparison이 필요하면 source/result의 외부 관찰만 비교하고 external effect를 두 번 실행하지
않는다.

대표 public harness는 추가로 한 번 **legacy-unavailable environment**에서 실행한다.

- retired legacy entry module의 import와 call을 시작 전부터 차단한다.
- legacy store root는 absent 또는 unreadable하게 둔다.
- conversion/fallback을 드러낼 필요가 있으면 valid-looking but current planning/source와 모순되는 poisoned
  old result를 별도 legacy surface에 둔다.
- 새 Module-owned state만으로 동일 public outcome과 recovery flow가 통과해야 한다.

모든 공용 utility symbol을 금지하거나 permanent dependency manifest를 만들지 않는다. retired entry
package, legacy store/result read와 conversion surface만 negative environment에서 차단한다.

## 정상 실행 비용 증명

단순화 목적은 correctness뿐 아니라 반복 비용 제거다. 새 정상 flow에서 다음을 관찰한다.

- caller는 Candidate를 위해 `implement` 한 번, verification을 위해 `verify` 한 번만 필요로 하며
  `inspect`는 recovery/read 용도다.
- caller가 actor/capability/claim/budget/authorization/run/flow/step/artifact/replay 값을 만들거나 전달하지
  않는다.
- source-only와 authenticated pure-read verification은 effect durable state를 만들지 않는다.
- single-attempt evidence는 generic event/attempt ledger를 만들지 않는다.
- 새 entrypoint를 삭제하면 planning/source/effect/recovery 지식이 harness나 callers에 다시 나타나므로
  Module이 단순 pass-through가 아니다.

wall-clock이나 저장 byte의 보편적 threshold는 근거 없이 고정하지 않는다. 대신 legacy public command
호출 0, caller orchestration 개념 0과 불필요한 effect state 0을 deterministic evidence로 삼는다.

## runtime verification 판정과 evidence 기록

다음이 모두 참일 때만 구현된 Phase 7을 `RUNTIME_VERIFIED`라고 판정할 수 있다.

1. Phase 1~6 계약을 구현한 새 entrypoint와 production Adapter가 존재한다.
2. 필수 public flow와 concurrency/fault flow가 새 path에서 통과한다.
3. Worker confinement, Fresh Verifier/Evidence Runner isolation, Source Adoption과 enabled Effect Adapter
   conformance가 각각 실제 production physical path에서 통과한다.
4. test 중 legacy call sentinel이 한 번도 작동하지 않고, 대표 public harness가
   legacy-unavailable environment에서도 통과한다.
5. exact tested source revision, test command와 결과를 다시 읽을 수 있다. Effect Adapter evidence는
   exact Adapter implementation revision, tested variant/mode와 target class, 실제 사용한 authority·dispatch·
   readback·cleanup branch 및 검증 당시 enabled Adapter set에 결속된다.
6. known failing/unsupported Adapter는 전체 성공으로 숨기지 않고 enable되지 않거나 명시적으로
   nonconclusive다.

sandbox가 production variant를 인증하려면 authority, transport, correlation, readback과 cleanup 처리의
동일한 production code path를 실행했다는 구조적 evidence가 있어야 한다. 그렇지 않으면 conformance는
sandbox variant에만 적용된다. Adapter enablement, mode 또는 해당 branch가 바뀌면 그 Adapter의 runtime
판정은 다시 보류되며 Module 전체의 이미 검증된 다른 Adapter까지 무효화하지 않는다.

evidence 기록은 test runner의 standard result와 exact tested source 및 위 Adapter scope에 대한 bounded
report면 충분하다.
새 product result schema, audit graph, capability 또는 permanent per-test ledger를 만들지 않는다.

## 허용한 실패 의미

- deterministic fake만 통과하면 production runtime proof가 아니다.
- legacy path가 호출되면 new Interface proof가 아니다.
- dangerous production Adapter에 safe conformance target이 없으면 그 Adapter를 enable하지 않는다.
- flaky/timeout/missing-tool test는 제품 failure가 아니라 verification incomplete이며
  `RUNTIME_VERIFIED`를 보류한다.
- 일부 Phase 계약만 통과한 상태를 전체 runtime success로 합성하지 않는다.
- test harness가 source/effect를 안전하게 격리하지 못하면 해당 destructive test를 실행하지 않는다.
- runtime proof가 없다는 이유로 Phase 1~6 계약을 약화하거나 legacy mechanism을 영구 보존하지 않는다.

## 현재 baseline에서 재사용할 evidence와 폐기할 mechanism

현재 source/test는 새 Implementation의 증거는 아니지만 실제 failure path와 기대 observable을 제공한다.

- Baseline Capsule stability/corruption tests: stable physical source와 immutable retained payload
- ownership/transaction tests: concurrent/unexpected change, overlap과 source closure
- workflow-store tests: single winner, atomic publication, response-loss retry
- verification-run tests: runner-owned evidence, complete polling, contradiction/drift precedence, live owner,
  ambiguous replay, cleanup과 retained readback
- pilots: direct positive, disconnected negative, delayed readback과 executable drift

새 harness는 위 behavior를 public Interface/Adapter conformance에서 다시 증명한다. actor rows, claim refs,
budget fields, table triggers, run/flow/step IDs, PROCESS version strings과 exact legacy reason code 자체는
보존 대상 evidence가 아니다.

## 명시적 범위 밖

- 새 Module/Adapter와 test code의 실제 구현
- CI product, runner framework, test file layout와 fixture library 선택
- exhaustive corruption, distributed partition, hostile kernel과 모든 scheduler interleaving
- performance SLO와 universal timeout/resource threshold
- 실제 production money/message/deployment를 사용하는 destructive verification
- legacy source/schema/command/test의 실제 삭제와 migration

## Oracle finding 판정 기록

### Initial — `slots-context-phase7in-744caf754a`

slot 1, DevSpace 무첨부 review가 authoritative readback과 함께 완료됐다. stored model evidence는
`requested=Pro`, `resolved=(unavailable)`, `strategy=current`, `verified=no`이므로 실제 model identity를
확정하지 않는다.

#### F1 — production Worker/Verifier/Runner 격리 proof 누락

```text
ORACLE_CLAIM: Source Adoption과 Effect Adapter만 production conformance 대상으로 두면 production Worker가
  canonical/planning/store를 쓰거나 production Verifier가 prior semantic artifact를 읽어도 fake public
  flow로 RUNTIME_VERIFIED가 가능하다.
STRONGEST_COUNTERARGUMENT: public flow 10·11이 source write와 fresh namespace를 이미 검사하고, 내부
  Adapter를 더 시험하면 interface-first 원칙을 약화할 수 있다. 그러나 deterministic Adapter path만
  실행하면 production namespace 조립의 물리적 차이를 증명하지 못한다.
PURPOSE_INVARIANT_AT_RISK: user-change preservation, fresh independent verification, runner-owned evidence.
CONCRETE_EVIDENCE: Phase 4/5는 production Worker confinement와 production Fresh Verifier/Runner namespace를
  명시한다. current overlap test는 canonical overwrite 뒤 사후 발견하는 한계를 보여준다.
CURRENT_PHASE_OWNERSHIP: production physical isolation을 어떤 runtime evidence로 증명할지는 Phase 7이다.
SMALLEST_CORRECTION: production Worker namespace의 forbidden-write probe와 production Verifier/Runner
  namespace의 canary/read-write/ownership probe만 추가한다. 모델 semantic output은 snapshot하지 않는다.
COMPLEXITY_DELTA: caller/normal path/durable/failure state +0, test-only physical probe +2; actor capability와
  path envelope protocol은 되살리지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F2 — sandbox effect conformance scope 과장

```text
ORACLE_CLAIM: sandbox branch만 통과하고 production branch가 다른 transport/readback을 써도 source revision만
  기록하면 enabled production Adapter까지 verified로 과장할 수 있다.
STRONGEST_COUNTERARGUMENT: 같은 Adapter implementation revision이면 sandbox가 production code를 대표한다고
  볼 수 있고 detailed mode metadata는 audit ceremony가 될 수 있다. 그러나 mode branch가 다른 실제
  sequence에서는 source revision만으로 실행된 semantics를 구분할 수 없다.
PURPOSE_INVARIANT_AT_RISK: actual authority, non-reexecution, authoritative readback과 cleanup.
CONCRETE_EVIDENCE: current effect tests는 local process/filesystem surface만 입증하며 provider production
  branch를 입증하지 않는다.
CURRENT_PHASE_OWNERSHIP: runtime verdict의 적용 범위를 과장하지 않는 evidence binding은 Phase 7이다.
SMALLEST_CORRECTION: bounded report를 Adapter revision, variant/mode, target class, 실제 branch와 enabled set에
  결속한다. 동일 production code path가 아니면 sandbox variant만 verified로 둔다.
COMPLEXITY_DELTA: caller/product state/failure state +0, test report scope metadata만 증가; destructive
  production action과 per-effect ledger는 추가하지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F3 — legacy call sentinel의 direct-read blind spot

```text
ORACLE_CLAIM: 새 path가 sqlite로 legacy store를 직접 읽고 copied converter로 old result를 변환하면 legacy
  public-call sentinel 없이도 facade가 통과한다.
STRONGEST_COUNTERARGUMENT: old conversion과 shadow certification을 이미 금지했고 sentinel 구현이 import/read도
  잡을 수 있다. 그러나 runtime gate는 sentinel 작동 여부만 요구해 direct data dependency의 negative
  proof가 명시되지 않았다.
PURPOSE_INVARIANT_AT_RISK: replace-don't-layer, 정상 비용 제거와 Phase 8 실제 삭제 가능성.
CONCRETE_EVIDENCE: current tests에는 transaction-free legacy root를 직접 읽어 admission하는 path가 있다.
CURRENT_PHASE_OWNERSHIP: 새 path가 legacy 없이 독립 실행된다는 runtime evidence는 Phase 7 소유다.
SMALLEST_CORRECTION: retired imports/calls 차단, legacy store absent/unreadable 및 필요시 poisoned old result인
  negative environment에서 대표 public harness를 재실행한다.
COMPLEXITY_DELTA: caller/normal/durable/failure +0, negative test environment +1; 모든 symbol audit나 permanent
  dependency manifest는 만들지 않는다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F4 — commit readback 뒤 orphan transition/occupancy 미검출

```text
ORACLE_CLAIM: result/head는 commit됐지만 active transition/occupancy release가 분리돼 orphan으로 남아도
  inspect readback과 duplicate-result 방지만으로 test가 통과한다.
STRONGEST_COUNTERARGUMENT: atomicity는 Phase 3 contract이고 internal transaction test가 구현 시 확인할 수
  있다. 그러나 Phase 7이 private row assertion을 최종 proof로 인정하지 않으므로 public liveness로 그
  semantic atomicity를 대체해야 한다.
PURPOSE_INVARIANT_AT_RISK: response-loss recovery, remediation 재진입, overlapping source의 이후 사용 가능성.
CONCRETE_EVIDENCE: Phase 3은 append/head/release/close의 single commit을 요구하며 current legacy tests는
  private claim/reservation row로 이를 확인한다.
CURRENT_PHASE_OWNERSHIP: restart 뒤 atomic closure를 실제 behavior로 증명하는 것은 Phase 7이다.
SMALLEST_CORRECTION: commit 후 inspect에 이어 verify/fresh verify/remediation implement와 overlapping-root
  adoption이 정확히 한 번 진행되는지 public sequence를 연장한다.
COMPLEXITY_DELTA: caller/state/protocol +0, 기존 fault test의 follow-on public call만 증가; private claim
  assertion과 orphan manual diagnosis를 대체한다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### F5 — Candidate 뒤 drift/restart에서 retained source 실제 사용 누락

```text
ORACLE_CLAIM: retained bytes 존재, response-loss inspect와 result-after-drift를 따로 시험해도 Candidate
  publication 후 verification 전 canonical drift/restart에서 verifier가 live source를 잘못 읽는 결함을
  놓칠 수 있다.
STRONGEST_COUNTERARGUMENT: fresh positive와 historical drift flow의 조합으로 의도가 충분히 드러날 수 있다.
  그러나 실제 순서가 다르면 두 test를 모두 통과하면서 retained Candidate를 검증 입력으로 쓰지 않을
  수 있다.
PURPOSE_INVARIANT_AT_RISK: exact Candidate source 결속과 user change 뒤 historical verification 가능성.
CONCRETE_EVIDENCE: Phase 4는 Candidate가 live path가 아닌 retained source라고 고정한다.
CURRENT_PHASE_OWNERSHIP: retained source가 실제 verifier input인지 실행으로 증명하는 것은 Phase 7이다.
SMALLEST_CORRECTION: 기존 flow 14를 Candidate A publish -> canonical B drift -> restart -> verify(A) ->
  historical result + NOT_CURRENT/UNKNOWN 순서로 명확히 한다.
COMPLEXITY_DELTA: caller/state/failure +0, 기존 public flow 순서 명확화만 추가한다.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

initial review는 24개 public flow/9개 fault boundary가 mechanism checklist 재포장이 아니라 사용자 가치별
proof이며, remediation flow와 deterministic 정상 비용 evidence도 충분하다고 판정했다. F1~F5 최소
correction을 같은 conversation follow-up으로 재공격한다.

### Follow-up 1 — `slots-followup-phase7fo-9166bfe6ba`

initial과 같은 slot 1·같은 conversation URL에 prompt가 실제 제출됐고 UI 답변을 완료해 회수했다. wrapper의
prompt commit probe는 timeout으로 stock status를 error로 남겼지만, 이는 delivery 상태일 뿐 설계 근거로
쓰지 않는다. stored browser evidence는 model identity를 확정하지 못하므로 실제 model을 단정하지 않는다.

- F2 effect Adapter scope binding과 F4 post-commit public liveness는 `CLOSED`.
- F1 production isolation과 F3 legacy-unavailable correction은 각각 본문에 존재하지만 최종
  `RUNTIME_VERIFIED` 판정 목록에 결속되지 않아 `STILL_OPEN`; 판정 조건 3·4에 직접 결속했다.
- F5는 stable readable B에서도 `UNKNOWN`을 허용하고 historical A evidence의 current-positive 오용을
  명시적으로 막지 않아 `STILL_OPEN`; stable B는 반드시 `NOT_CURRENT`, current-positive verdict 금지,
  observation-failure variant에서만 `UNKNOWN` 허용으로 좁혔다.
- 새 material finding, 사용자 결정과 ceremony 회귀는 없었다.

세 correction 모두 caller Interface, 정상 path, product durable state, public failure state와 permanent
ledger를 늘리지 않는다. 같은 conversation의 두 번째 follow-up에서 F1·F3·F5와 새 회귀만 재공격한다.

### Follow-up 2 — `slots-followup-phase7fo-09d45a724e`

follow-up 1과 같은 slot 1·같은 conversation URL에 prompt가 제출됐고 completed UI answer를 회수했다.
wrapper commit probe timeout과 stock error는 delivery 상태로만 기록한다. 실제 model identity는 검증되지
않았다.

- F1은 네 production physical conformance를 판정 조건 3에 결속해 `CLOSED`.
- F3는 sentinel 0과 legacy-unavailable public harness 통과를 판정 조건 4에 함께 결속해 `CLOSED`.
- F5는 stable readable B에서 `NOT_CURRENT`, historical A evidence의 current-positive 금지,
  observation-failure variant에서만 `UNKNOWN`을 허용해 `CLOSED`.
- 새 material finding, 사용자 결정, ceremony 회귀와 caller/정상 path/state/ledger 순증가는 없다.

Oracle 선언 자체가 아니라 위 세 sequence를 Phase 1~6 계약과 현재 contract에 다시 대조했다. failed
production isolation, direct legacy read/conversion, always-`UNKNOWN`과 historical-positive 오용은 각각
명시적 runtime gate에서 실패한다. 따라서 Phase 7 design을 `DESIGN_CONVERGED`로 판정한다.

## 완료 판단

Phase 7 design은 `DESIGN_CONVERGED`다. 새 Module이 아직 구현되지 않았으므로 `IMPLEMENTED` 또는
`RUNTIME_VERIFIED`는 아니다. 이 계약의 실제 runtime evidence가 exact 구현 revision에서 통과하기 전에는
Phase 8 제거 gate를 실행할 수 없다.
