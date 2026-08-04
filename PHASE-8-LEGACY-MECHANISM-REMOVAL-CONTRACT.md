# Phase 8 — 구 메커니즘 제거

상태: `DESIGN_CONVERGED`

## 목적과 단일 결정

Phase 1~7의 사용자 가치를 새 Implementation Verification Module이 실제로 증명한 뒤, 그 가치를 더는
소유하지 않는 구 command, protocol, schema, code와 mechanism-coupled test를 어떤 순서와 증거로 삭제할지
정한다.

이번 단계의 단일 결정은 다음이다.

> 삭제는 새 경로의 exact revision·enabled Adapter set에 대한 Phase 7 `RUNTIME_VERIFIED` 뒤에만 시작한다.
> durable user data와 active mechanism을 먼저 분리하고, 실제 consumer를 새 Interface로 한 번만 cut over한
> 뒤 compatibility read/write, dual-run과 fallback 없이 dependency 바깥에서 안쪽 순서로 구 mechanism을
> 제거한다. 삭제가 반영된 새 revision에서 Phase 7 proof와 legacy-absence proof를 다시 통과해야만
> `LEGACY_MECHANISM_REMOVED`라고 판정한다.

Phase 8은 이 삭제 gate와 순서를 설계한다. 현재 새 Module은 구현되지 않았고 Phase 7 runtime evidence도
없으므로 이 문서는 어떤 제품 code, user state 또는 legacy file의 현재 삭제를 허가하지 않는다.

## 삭제 실행의 hard precondition

다음이 모두 참이 아니면 removal executor는 아무것도 삭제하거나 이동하지 않는다.

1. Phase 1~7 design이 모두 `DESIGN_CONVERGED`다.
2. Phase 1~6을 구현한 새 `implement`, `verify`, `inspect`와 production Adapter가 존재한다.
3. Phase 7의 public/fault/conformance/legacy-unavailable evidence가 exact source revision, Adapter revision,
   mode·branch와 enabled set에 결속돼 `RUNTIME_VERIFIED`다.
4. active caller/skill/automation과 durable legacy root를 다시 census한 bounded removal manifest가 있다.
5. legacy workflow의 live owner, active transition, unresolved may-have-run effect나 미완료 cleanup이 0이다.
   하나라도 있으면 자동 변환·재실행·폐기하지 않고 removal을 멈춘다.
6. durable historical data 각각에 `IMPORT`, `STATIC_ARCHIVE`, `DISCARD_AS_TEST_DATA` 중 근거 있는 disposition이
   정해졌고, user data를 test data로 추정하지 않는다.

Phase 7의 현재 `DESIGN_CONVERGED`나 기존 254-test baseline은 2·3을 만족하지 않는다.

## 현재 source와 local durable surface의 관찰

2026-08-04 read-only census에서 확인한 legacy mechanism은 다음이다.

- `verification-lead/tools/verification-run/verification_run.py`: 12-command orchestration,
  actor/capability, authorization, claim/budget, run/flow/step, artifact와 replay scope.
- `implementation-lead/tools/implementation-result/implementation_result.py`: handoff publication과
  historical `implementation-result-v3` reader.
- `implementation-lead/tools/implementation-transaction/implementation_transaction.py`: ownership envelope,
  selected Worker capability, transaction/event와 reconciliation.
- `implementation-lead/tools/workflow-store/{workflow_store.py,workflow_store_preopen.py}`: old nodes/edges,
  claims, actors, invocations, budgets, transactions, verification runs/attempts/artifacts와 migrations.
- `implementation-lead/tools/task-ownership-snapshot/ownership_snapshot.py`: capture/compare command.
- `baseline-capsule/`: five-command capsule store, identity/read leases와 cleanup.
- 두 Lead의 `SKILL.md`, protocol/reference 문서와 위 mechanism의 private row·reason·token을 직접 assertion하는
  tests.

현재 default local state에는 약 184 KiB의 historical result JSON 19개가 실제로 존재하며, observed
`protocolVersion`은 v3 11개와 v2 8개다. 현재 runtime의 `HistoricalV3Store`는 v3만 읽고 repository에는
v2 reader가 없다. 약 670 MiB의 baseline capsule store도 존재한다. default `implementation-workflows`
root의 file은 이 census에서 발견되지 않았지만 삭제 시점에는 다시 확인해야 한다. 이 관찰은 data 삭제
허가가 아니며, 특히 unsupported v2 bytes와 historical result 및 그 source capsule을 test fixture로
간주하지 않는다.

Matt planning 문서, Ticket/SPEC authority, repo-snapshot, 중립적인 source hashing/file observation utility는
이름이 함께 검색된다는 이유만으로 삭제 대상이 아니다. 새 Module이 실제로 소비하는 deep primitive는
legacy public mechanism과 분리된 뒤 유지할 수 있다.

## data와 mechanism의 분리

구 schema나 reader를 계속 실행하는 것은 compatibility layer지만, 검증된 immutable bytes를 active runtime
밖에 보존하는 것은 legacy mechanism이 아니다.

### IMPORT

새 `inspect`가 기존 historical result를 계속 공개해야 하는 명시적 consumer가 있을 때만 사용한다.

- removal 중 실행하는 bounded one-shot importer 하나가 old bytes를 읽는다.
- exact planning/source/result binding과 referenced retained source를 새 canonical model에 완전하게 표현할 수
  있는 record만 import한다.
- import 전후 semantic fields, raw-source identity, cardinality와 digest manifest를 대조한다.
- 검증된 import가 끝나면 importer와 old read path를 함께 삭제한다. runtime fallback이나 dual read는 없다.
- 불완전 record를 긍정 Candidate/VerificationResult로 합성하지 않는다.

### STATIC_ARCHIVE

계속되는 runtime consumer는 없지만 실제 user history 또는 source recoverability를 보존해야 할 때 사용한다.

- original immutable bytes, referenced capsule bytes, relative-path manifest, size와 cryptographic digest를
  active state root 밖의 read-only archive에 보존한다.
- archive는 새 result를 publish하거나 currentness를 계산하거나 effect를 재실행하지 않는다.
- old CLI/library/schema를 archive reader로 남기지 않는다. 일반 file access와 manifest verification이면
  충분하다.
- retention authority가 archive 폐기를 승인하기 전에는 bytes를 삭제하지 않는다. archive가 남아 있어도
  active legacy mechanism removal과 구분해 보고한다.

### DISCARD_AS_TEST_DATA

repository-owned disposable fixture/temp root라는 positive evidence가 있을 때만 허용한다. 위치나 오래된
timestamp만으로 user data를 폐기하지 않는다.

baseline capsule은 참조 reachability를 계산한다. imported 또는 archived historical result가 가리키는
capsule과 아직 recoverable Candidate source는 먼저 보존하고, unreferenced임이 증명된 것만 별도 retention
정책에 따라 처리한다. 670 MiB라는 크기는 삭제 근거가 아니다.

## one-way cutover와 삭제 순서

### 0. freeze와 census

- exact removal revision, enabled Adapter set, legacy entrypoint·store root·consumer 목록을 고정한다.
- legacy workflow에 새 write를 시작하지 않으며 active owner/effect/cleanup이 0인지 공개·물리 evidence로
  확인한다.
- durable data disposition과 archive/import manifest를 만들고 복구 readback을 표본이 아니라 전 항목에
  대해 검증한다.

old write quiescence/fence는 이 최초 zero census부터 installed caller cutover, 이미 시작된 old process의
종료 확인과 retired entrypoint unavailable 완료까지 계속 유지한다. old store의 내부 lock만으로 별도
checkout/custom-root의 old writer가 참여한다고 가정하지 않는다. 이 window 중 새 old owner, transition,
effect 또는 cleanup이 나타나면 다음 삭제 단계로 진행하지 않는다. 새 lock/audit protocol은 만들지 않고
bounded removal window의 시작·종료 evidence만 남긴다.

### 1. active caller cutover

- installed/local Lead entry routing과 실제 automation을 새 `implement`, `verify`, `inspect`로 한 번에 바꾼다.
- 같은 work를 old/new 양쪽에 쓰거나 읽지 않는다. shadow publish, dual effect, fallback converter를 금지한다.
- old command는 새 command를 부르는 facade가 되지 않고 명시적으로 unavailable이어야 한다.
- cutover 직후 대표 production path와 legacy-unavailable Phase 7 harness를 실행한다.

### 2. top-level consumer부터 outside-in 제거

consumer root인 Verification Run과 shared public entrypoint/intermediate dependency인 Implementation Result,
두 Lead의 old orchestration 문서·참조, old handoff/result publication과 historical runtime reader를
outside-in으로 제거한다. user history는 앞서 검증한 import 또는 static archive에만 남는다.

### 3. coordination mechanism 제거

더는 consumer가 없음을 확인한 뒤 Implementation Transaction, ownership snapshot command, actor/capability,
claim/budget/authorization/replay, run/flow/step/artifact coordination과 그 schema/migration을 제거한다.
old reason code나 table을 새 Module state에 그대로 복제하지 않는다.

### 4. shared legacy storage와 capsule mechanism 제거

old workflow-store open/audit/migration과 schema fixture를 제거한다. Baseline Capsule은 새 Source
Adoption/retained-source implementation이 필요한 identity·retention behavior를 직접 소유하고 Phase 7
conformance가 통과하며 historical reachability disposition이 끝난 뒤에만 CLI, lease/cleanup store와
protocol을 제거한다. 중립적인 hash/read primitive가 실제 새 consumer를 가지면 deep internal utility로
남길 수 있지만 old public capsule protocol을 유지하지 않는다.

### 5. mechanism-coupled test 교체

actor row, claim ref, capability token, budget vector, exact old schema/trigger, command count와 legacy reason을
보장하는 test는 해당 implementation과 함께 제거한다. 각 삭제 범주를 지우기 전에 그 tests가 보존하던
사용자 가치를 Phase 7 public/conformance proof 또는 Phase 8 import/archive readback·legacy-absence proof에
한 줄로 매핑한다. 매핑 없는 가치 test는 삭제하지 않는다. per-test permanent ledger는 만들지 않으며 동일
behavior를 old/new 두 suite에서 영구 실행하지 않는다.

historical-reader 범주는 모든 disposition item의 digest/readback, imported record의 semantic/cardinality,
archive 일반 file read가 old state root를 만들지 않음, retired reader/import/conversion surface의 부재와
old result가 positive Candidate/VerificationResult로 변환되지 않음을 replacement evidence로 삼는다. 그
evidence가 통과한 deletion change에서 old reader와 mechanism-coupled tests를 함께 제거한다.

### 6. documentation과 package closure

active `SKILL.md`, README, help, examples와 installer/package export에서 old command와 protocol을 제거한다.
historical design/removal record는 `historical`로 명확히 표시해 남길 수 있지만 실행 지침이나 supported
Interface로 노출하지 않는다.

### 7. deletion-revision 재검증

삭제로 source revision이 바뀌므로 pre-removal `RUNTIME_VERIFIED`를 그대로 승계하지 않는다.

- Phase 7 전체 public/fault/conformance suite를 deletion revision과 exact enabled Adapter set에서 재실행한다.
- legacy entry imports/calls, command help와 old state roots가 unavailable인 환경에서 대표 flow를 재실행한다.
- repository와 installed/exported runtime에서 retired entrypoint·schema creator·fallback/converter reference가
0인지 bounded inventory로 확인한다.
- pure read가 state를 만들지 않고 old default roots가 재생성되지 않는지 확인한다.
- archive/import manifest의 bytes와 digest가 그대로 recoverable한지 재확인한다.

모두 통과해야만 `LEGACY_MECHANISM_REMOVED`다. 실패하면 새 path를 old facade로 우회하지 않고 removal
revision을 고쳐 다시 검증한다.

## 삭제 완료 evidence

완료 report는 다음 bounded evidence만 가진다.

- before/after exact source revision과 enabled Adapter set
- 삭제한 entrypoint/package/schema/test 범주와 남긴 deep primitive의 실제 consumer
- active caller/installed copy가 새 Interface를 가리킨다는 확인
- legacy unavailable/import-blocked/store-absent harness 결과
- deletion revision의 Phase 7 result와 Adapter scope report
- user data disposition별 item count·bytes·manifest digest와 archive/import readback 결과
- 삭제 범주별 old-test user value와 replacement proof의 bounded mapping
- unresolved active transition/effect/cleanup 0 또는 실행 중단 사실

per-file approval workflow, permanent dependency graph, tombstone DB, compatibility telemetry와 delete ledger는
만들지 않는다. source control diff, bounded manifest와 standard test report면 충분하다.

## 실패와 중단 의미

- Phase 7 runtime proof가 없거나 revision/Adapter scope가 다르면 삭제하지 않는다.
- active legacy work/effect가 하나라도 있으면 강제 close, replay, 자동 migration 없이 중단한다.
- record의 semantic/source binding을 새 model에 완전히 표현할 수 없으면 긍정 result로 import하지 않고
  static archive로 보존한다.
- actual consumer가 남아 있으면 compatibility facade를 추가하지 않고 cutover 작업을 완료할 때까지 해당
  dependency의 삭제를 보류한다.
- deletion 뒤 Phase 7이나 legacy-absence proof가 실패하면 `LEGACY_MECHANISM_REMOVED`를 선언하지 않는다.
- archive retention과 active mechanism removal을 같은 상태로 합성하지 않는다.

## 명시적 범위 밖

- 새 Module, Adapter, importer나 archive tooling의 실제 구현
- 현재 local user data의 이동·삭제·압축
- provider별 production effect migration
- organization-wide consumer discovery와 보편 retention 기간
- git history나 과거 설계 기록의 삭제
- unrelated Matt planning/repo-snapshot 기능의 정리

## Oracle finding 판정 기록

### Initial — `slots-context-phase8in-91583584f3`

slot 1의 새 conversation에서 DevSpace 무첨부 review를 완료했다. wrapper commit probe의 stock error와
completed UI answer delivery는 구분하며, stored model evidence로 실제 model identity를 확정하지 않는다.

#### H1 — zero census 뒤 old writer 재진입

```text
ORACLE_CLAIM: point-in-time zero census 뒤 별도 checkout/installed caller가 old process를 시작하면 code/store
  삭제 중 may-have-run effect와 cleanup/result recovery를 잃는다.
STRONGEST_COUNTERARGUMENT: freeze라는 제목과 "새 write를 시작하지 않는다"가 지속 fence를 뜻할 수 있다.
  그러나 current store lock은 old writer deployment를 강제 참여시키지 않고 실제 installed skill은 별도
  checkout을 가리키므로 window 종료점이 없으면 point check로 오해 가능하다.
PURPOSE_INVARIANT_AT_RISK: user work preservation, effect non-reexecution/readback/cleanup, recovery.
CONCRETE_EVIDENCE: workflow_store.py는 separate deployment quiesce가 필요함을 명시하고 installed Lead가
  /home/user01/project/iis-skills를 가리킨다.
CURRENT_PHASE_OWNERSHIP: deletion authorization이 유효한 시간 구간은 Phase 8 소유다.
SMALLEST_CORRECTION: first zero census부터 caller cutover, old process 종료와 entrypoint unavailable까지 기존
  quiescence를 지속한다. 새 old owner가 보이면 stop한다.
COMPLEXITY_DELTA: caller/normal path/durable +0, 기존 removal-stop 범위만 명확화; 새 lock/ledger 없음.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### H2 — old test replacement를 Phase 7에만 한정

```text
ORACLE_CLAIM: archive recoverability/no-state-creation 가치는 Phase 7 legacy-unavailable flow가 증명하지 않아,
  mapping 규칙상 old historical reader/test를 영구 보존하거나 가치 proof 없이 삭제해야 한다.
STRONGEST_COUNTERARGUMENT: Phase 8 completion evidence에 archive readback이 이미 있다. 그러나 test deletion 절은
  명시적으로 Phase 7 mapping만 허용해 상충한다.
PURPOSE_INVARIANT_AT_RISK: historical result/source recoverability와 replace-don't-layer.
CONCRETE_EVIDENCE: old tests는 byte-preserving read, no adaptation, no workflow-root creation을 검사한다.
CURRENT_PHASE_OWNERSHIP: removal-specific replacement evidence와 code/test ordering은 Phase 8 소유다.
SMALLEST_CORRECTION: 삭제 범주별로 Phase 7 또는 Phase 8 import/archive/absence proof에 먼저 매핑하고 같은
  change에서 reader와 tests를 제거한다. per-test ledger는 금지한다.
COMPLEXITY_DELTA: caller/normal/durable/failure +0, bounded report mapping 한 줄/범주; old reader 제거 가능.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### M1 — dependency leaf 용어 역전

```text
ORACLE_CLAIM: Verification Run은 consumer root이고 Implementation Result는 intermediate dependency인데 leaf라
  부르면 store/capsule부터 지우는 반대 순서로 해석된다.
STRONGEST_COUNTERARGUMENT: 번호 순서는 이미 대체로 outside-in이다. 따라서 새 ordering mechanism은 필요 없다.
SMALLEST_CORRECTION: leaf를 top-level consumer/outside-in으로 바로잡고 direct import edge만 bounded manifest에 둔다.
COMPLEXITY_DELTA: 모두 +0.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

#### M2 — historical inventory 오기

```text
ORACLE_CLAIM: 실제 19개 중 v3 11/v2 8인데 20개 v3라 쓰면 v3-only importer가 v2를 누락할 수 있다.
STRONGEST_COUNTERARGUMENT: 실행 전 item별 census가 오기를 잡는다. 그래도 현재 concrete baseline은 바로잡는
  편이 unsupported bytes를 test data로 오인하지 않는 목적에 부합한다.
CONCRETE_EVIDENCE: local jq 재검산도 JSON 19, v3 11, v2 8이며 runtime reader는 v3-only다.
SMALLEST_CORRECTION: 문구를 바로잡고 unsupported protocol은 STATIC_ARCHIVE 또는 stop으로 둔다.
COMPLEXITY_DELTA: 모두 +0, 새 v2 compatibility reader 없음.
DISPOSITION: ACCEPT_WITH_BOUNDARY
```

initial은 pre-removal verdict를 deletion revision에 승계하지 않는 점, dual-read/fallback 금지, positive
evidence 없는 user data discard 금지와 bounded report 범위는 충분하다고 판정했다. 새 material finding과
현재 사용자 결정은 없다. H1/H2/M1/M2 correction을 같은 conversation follow-up으로 재공격한다.

### Follow-up 1 — `slots-followup-phase8fo-fefabdec5c`

initial과 같은 slot 1·같은 conversation URL에서 DevSpace 무첨부 follow-up을 완료했다. wrapper prompt commit
probe의 stock error와 completed UI answer delivery를 구분하며 실제 model identity는 검증되지 않았다.

- H1은 zero census부터 caller cutover, old process 종료와 entrypoint unavailable까지 fence를 유지해
  `CLOSED`; 새 deployment lock이나 ledger는 없다.
- H2는 category-level Phase 7/8 replacement proof 뒤 같은 change에서 reader/test를 제거해 `CLOSED`;
  per-test ceremony는 없다.
- M1은 actual direct import 방향과 맞는 consumer-root outside-in 순서로 `CLOSED`; dependency solver/graph는
  없다.
- M2는 JSON 19(v3 11/v2 8)과 v3-only reader를 정확히 기록하고 unsupported bytes를 archive/stop으로 두어
  `CLOSED`; v2 compatibility reader/converter는 없다.
- 새 material finding, 현재 사용자 결정, ceremony 회귀와 caller/normal path/durable/public failure state의
  순증가는 없다.

Oracle 선언 자체가 아니라 current import graph, installed skill target과 local durable census에 correction을
재대조했다. initial failure sequence는 각각 bounded removal window, category replacement gate, outside-in
order와 item-level disposition에서 실패한다. 따라서 Phase 8 design을 `DESIGN_CONVERGED`로 판정한다.

## 완료 판단

Phase 8 design은 `DESIGN_CONVERGED`다. 현재 product implementation, Phase 7 runtime verification, data
disposition과 legacy removal은 시작되지 않았다. hard precondition과 deletion-revision 재검증이 실제로
통과하기 전에는 `LEGACY_MECHANISM_REMOVED`라고 부르지 않는다.
