# PLAN-001 — BLOCK-13 N-Cut Dynamic Architecture & Cutover

## 1. 결속된 권위와 실행 경계

- Project Root: `/home/user01/project/comic_new`
- Scope: `/home/user01/project/comic_new/docs/planning/work/n-cut-dynamic-architecture/SCOPE.md` (sha256 `370fdcbde89f45e76f517179cf909c752536434d090850a7d3a4c5ceff3c5a25`, `Schema: iis-scope/v1`, `Status: ready`)
- Normative Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md` (`THESIS-003`, sha256 `d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268`)
- Transition Authority: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md` (sha256 `59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51`, selected `BLOCK-13`)
- Repository investigation: 별도 불변 investigation artifact는 제공되지 않았다. 이 Plan은 위 원본과 현재 source/test bytes 및 read-only workspace DB 관찰을 직접 조사한 결과에 결속한다.
- Scope validator: canonical `scope-shaper/tools/validate_scope.py --json`은 `iis-scope/v1`, `status: ready`, 위 Thesis/Transition path 및 digest의 정확한 일치를 반환했다.
- 선행 경계: BLOCK-10, BLOCK-11, BLOCK-12 Scope는 각각 `Status: done`이다. 현재 코드에서도 sparse intent/job identity(`store.py:126-186, 1447-1538`), 검증된 N-cut draft 입력(`llm/client.py:294 이후`, `server.py:147-157,965-974`), 동적 integer layout·cut-local bubble(`composition.py:30-35`, `CompositionCanvas.vue:20-65`)이 존재한다. 문서 상태만으로 runtime 성공을 추정하지 않으며 §10 CF-1에서 fresh readback한다.
- 증거 경계: synthetic PNG, controlled provider/Blogger adapter, unit/component test는 cardinality·CAS·closure·UI projection을 판별하는 보조 증거다. 실제 제품 성공은 fresh authoritative snapshot, 실제 materialized artifact bytes/embedded closure, PNG destination bytes readback 및 허용된 경우의 Blogger destination marker/hash readback을 연결해 판정한다. 외부 유료 Blogger 계정 실발행은 이 Scope 밖이다.

`BASELINE-003:300-373`은 BLOCK-13을 Phase 1 `BLOCK-13A`와 Phase 2 `BLOCK-13B`의 의무적 연속 경계로 고정한다. 따라서 사용자 지시의 schema v7, creation/baseline-time `cut_count`, N-cut backend/frontend/release 전환은 Phase 1에서 먼저 완료하고, 같은 Scope 안에서 stable identity와 active membership/display order 분리 및 add/retire/reorder까지 Phase 2로 완료한다. Phase 1 성공만으로 BLOCK-13 완료를 주장하지 않는다.

## 2. 달성할 관찰 결과와 보존 조건

### 2.1 Phase 1 — creation-time N

1. `comic-new init --cut-count N`, 최초 수동 Baseline, 또는 draft의 `cut_count` 채택을 통해 `N >= 1`의 ordered cut set을 하나의 원자 mutation으로 만든다.
2. `cut_id`는 양의 정수이고 새 프로젝트의 최초 identity는 `1..N`이다. 기존 v6 프로젝트는 동일한 다섯 identity와 모든 intent/job/artifact/delivery history를 보존한 정상 `N=5` 프로젝트가 된다.
3. Baseline 승인, sparse per-cut intent, single/all enqueue, composition acceptance/materialization, authorization, export/Blogger preflight는 고정 5가 아니라 fresh ordered active set `S`를 사용한다.
4. `S`가 비어 있지 않고 모든 `i ∈ S`가 Current일 때만 `RealizationComplete(S)`가 true다. 한 컷이라도 Unrealized/Stale/최신 job 미성공이면 review materialization과 release가 차단된다.
5. Rebaseline dialog는 양의 정수 `cut_count`를 직접 지정하거나 validated draft의 `cut_count`를 원자적으로 채택한다. 성공 응답 전에 닫지 않고 실패 시 brief/count/cut fields를 보존한다.

### 2.2 Phase 2 — stable identity와 active membership/order

1. `cut_id`는 영구 identity다. add는 `MAX(cut_id)+1`만 발급하고 retire는 row를 삭제하지 않으며 reorder는 `cut_id`, desired/realized revision, request sequence, job와 historical artifact ownership을 바꾸지 않는다.
2. active membership은 항상 한 개 이상이고 각 active cut은 유일한 양의 `display_order`를 가지며 order는 정확히 `1..N`이다.
3. add/retire/reorder는 새 structural baseline snapshot과 ordered active set, composition slot order, artifact currentness 및 authorization 철회를 같은 SQLite transaction에서 확정한다. 실패하면 전부 rollback한다.
4. 새 active cut은 intent를 가질 수 있으나 realization 전에는 전체가 `UNRESOLVED`다. inactive cut은 current snapshot/render/release closure에서 제외되지만 cut/intent/job/artifact history에는 남는다.
5. reorder 뒤 CutRail, CompositionCanvas, renderer, artifact metadata, DB `artifact_cuts`, authorization/release preflight가 동일 `display_order`를 사용한다. cut-local bubble은 `cut_id`를 따라 이동한다.
6. drag-and-drop 애니메이션 프레임워크는 만들지 않는다. Phase 2 UI는 최소한의 추가/비활성화 및 위/아래 이동 controls로 완전한 동작을 제공한다.

### 2.3 반드시 보존할 4대 인과 불변식

- **INV-1 Monotonic Sequence CAS:** active 여부나 order와 무관하게 `(cut_id, desired_revision, request_seq, model, effective_prompt identity)` 결속 및 commit-time 최신성 검사를 유지한다.
- **INV-2 STOP Pre-commit Lockout:** retire/reorder 중인 cut의 queued/running job을 성공으로 가장하지 않는다. STOP은 기존대로 commit eligibility를 먼저 철회하고 늦은 candidate는 canonical asset을 바꾸지 못한다.
- **INV-3 Atomic Approval Revocation:** Baseline, intent, generation, accepted realization, membership/order, composition mutation과 동일 transaction에서 active authorization을 철회한다.
- **INV-4 Destination Content Readback:** 승인 artifact의 검증된 bytes만 전달하고 PNG destination bytes 또는 Blogger destination marker/hash의 실제 readback 전에는 성공으로 확정하지 않는다.

## 3. 현재 코드 Grounding

### 3.1 EXISTING — v6 fixed-five DB와 migration authority

- `src/comic_new/schema.sql:16-47,56-69,115-121`은 `cut_intents`, `cuts`, `baseline_intents`, `generation_jobs`, `artifact_cuts`의 `cut_id`를 `BETWEEN 1 AND 5`로 제한한다.
- `src/comic_new/schema.sql:159-185`는 다섯 cut row를 고정 seed하고 insert/delete/cut_id update를 모두 막는 trigger를 설치한다.
- `src/comic_new/store.py:75-107`은 schema version 6 및 fixed trigger set을 요구한다. `:275-483`은 순차 migration을 `BEGIN IMMEDIATE`와 rollback으로 수행하고 `:750-865`는 version/table/trigger/index/row/content를 검증한다.
- `src/comic_new/store.py:199-262`의 `create_project()`는 임시 DB에서 전체 schema를 만든 뒤 `verify_schema()` 후 `os.replace`하므로 실패한 project가 current path에 부분 노출되지 않는 기반이 있다. 현재 cut count 입력은 없다.
- read-only workspace 관찰에서 `workspace/comic-new.sqlite3`은 `user_version=4`, cut `1..5`, composition revision 0/`{}`, job/artifact/authorization/delivery 0건이다. 이 파일은 v6→v7 단독 migration 증거가 아니라 실제 open 시 v4→v5→v6→v7 연쇄 migration을 판별할 추가 fixture다.

이 근거는 원자 migration/프로젝트 생성 틀을 재사용할 수 있음을 확정하지만, v7의 positive IDs, membership/order, historical closure 보존을 충족한다는 증거는 아니다.

### 3.2 EXISTING — store/service의 fixed-five 결정 지점

- `store.py:146-186`의 intelligent-default resolver가 structure를 정확히 `1..5`로 요구하고 list index로 cut을 찾는다.
- `store.py:779-782`, `888-912`, `948-1013`은 schema verification, current closure, snapshot/completion을 다섯 physical rows와 `ORDER BY cut_id`에 결속한다.
- `store.py:1174-1260`의 Baseline approval은 intent key/iteration을 `1..5`로 고정한다. `:1264-1275`, `:1447-1465`는 per-cut intent/enqueue ID를 같은 고정 집합으로 검증하고 enqueue-all도 `[1..5]`를 만든다.
- `store.py:1334-1439`의 composition acceptance는 slot count와 dialogue synchronization을 다섯 cut에 고정한다.
- `store.py:2080-2203`의 artifact registration/authorization은 closure 길이 5를 요구하고 `:2211-2280`의 delivery-attempt 시작은 모든 physical cuts를 current closure로 해석한다.
- `generation.py:321-341`과 `cli.py:30-57,114-133`은 service/CLI cut validation 및 init/generate UX를 5에 고정한다.
- `delivery.py:756-872`는 snapshot complete를 확인한 뒤 다시 `len(cuts)==5`를 요구한다. bytes/hash/physical source readback 자체는 이미 올바른 경계이므로 cardinality만 active set으로 전환한다.

### 3.3 EXISTING — BLOCK-12 geometry와 remaining identity mismatch

- `composition.py:17-35`에는 dynamic height와 `ResolvedSlot.cut_id`가 있지만 `TOTAL_CUTS=5`, fixed default heights가 남아 있다.
- `composition.py:424-499`는 state/cut 길이를 5로 강제하고 `expected_cut_id=idx+1`로 renderer order를 identity와 동일시한다.
- `composition_service.py:81-187,258-337,358-443`은 materialize, duplicate convergence, currentness/readback을 `TOTAL_CUTS`와 ordered `1..5`에 결속한다.
- BLOCK-12가 만든 `slot_heights_px`는 ordered array이고 bubble은 stable `cut_id`를 가진다. 따라서 Phase 2 reorder에서 height ownership을 보존하려면 resolver가 실제 ordered active cut IDs를 함께 받아야 한다. index+1을 새 identity로 추정하면 안 된다.
- `server.py:502-523`의 default composition과 render contract는 5-height default를 사용한다. `:538-628`은 store snapshot cuts 순서를 그대로 투영하는 재사용 가능한 경계다.

### 3.4 EXISTING — API/frontend fixed-five와 이미 동적인 render loop

- `server.py:80-84,116-172,200-203`은 `CutId=Literal[1..5]`, path max 5, Baseline structure/intents exact-five를 강제한다. `:885-887`의 오류 메시지도 “Exactly five”다.
- `frontend/src/api/contracts.ts:3-6,70-79,140-195,246-265`는 `CutId` union, five-tuple Baseline/Snapshot, artifact/job cut IDs를 고정한다. runtime validator `:395-397,485-533,640-690`도 length 5와 index+1 identity를 요구한다.
- `frontend/src/components/baseline/RebaselineDialog.vue:16-29,90-123`은 local arrays와 draft request를 5로 고정한다.
- `frontend/src/store/studio.ts:485-505,542-612`은 intent lane을 `[1..5]`로 순회하고 draft response가 정확히 5인지 재검사한다.
- 반면 `CutRail.vue:9-20`은 이미 snapshot array를 `v-for`하고, `CompositionCanvas.vue:20-65,86-133`은 resolved slot array와 cut-local bubble을 순회한다. 고정 type/assertion과 upstream slot identity만 제거하면 N rendering 구조는 재사용 가능하다.
- `domain/currency.ts:15-18`만 `cuts.length===5`를 completion으로 재강제한다.

### 3.5 Grounding 분류 요약

- **EXISTING:** BLOCK-10의 sparse intent/frozen job identity와 INV-1/2 경계, BLOCK-11의 arbitrary positive draft `cut_count`, BLOCK-12의 integer heights/contain/cut-local bubble은 현재 source에 존재한다.
- **EXISTING:** fixed-five는 DB DDL, store writers/readers, renderer/service, server DTO, frontend runtime validator, completion/release에 중복되어 도달 가능하다.
- **PROPOSED:** schema v7, active/display order columns, positive cut constraints, ordered artifact closure, v6→v7 atomic rebuild migration.
- **PROPOSED:** creation-time N 및 first-Baseline cut count adoption, Phase 2 add/retire/reorder mutation, active-set snapshot/completion/materialization/release clean cutover.
- **PROPOSED:** positive integer `CutId`, array DTO/runtime invariants, Rebaseline cut count UI, N-cut rail/canvas and membership controls.
- **UNRESOLVED:** 현재 실제 운영 대상 DB들의 version/history 분포는 repository source와 단일 workspace DB만으로 확정할 수 없다. §10 CF-2의 read-only inventory가 v6→v7 방법의 전제와 다르면 migration mutation을 중단한다.
- **UNRESOLVED:** BLOCK-12의 실제 browser/artifact parity와 선행 Scope currentness는 source 및 `Status: done`만으로 runtime 사실이 아니다. §10 CF-1이 refute되면 BLOCK-13 mutation을 시작하지 않는다.

## 4. Schema v7과 active-set 권위 모델

### 4.1 v7 current schema

`cuts`가 stable identity와 current membership/order를 함께 소유한다.

```sql
cut_id        INTEGER PRIMARY KEY CHECK (cut_id >= 1)
is_active     INTEGER NOT NULL CHECK (is_active IN (0, 1))
display_order INTEGER NULL CHECK (display_order IS NULL OR display_order >= 1)
CHECK (
  (is_active = 1 AND display_order IS NOT NULL) OR
  (is_active = 0 AND display_order IS NULL)
)
```

- partial unique index `UNIQUE(display_order) WHERE is_active=1`을 둔다.
- active rows를 `ORDER BY display_order`로 읽은 결과가 exact ordered active set `S`다. `verify_schema()`와 모든 membership mutation은 `S != []`, unique positive IDs, order `1..N`을 검사한다.
- `cut_id`는 수정/재사용하지 않는다. 새 row는 transaction 안에서 `COALESCE(MAX(cut_id),0)+1`을 할당한다.
- `cut_intents`, `baseline_intents`, `generation_jobs`, `artifact_cuts`의 fixed range check를 모두 `cut_id >= 1`로 전환한다. 사용자 지시에 열거되지 않았어도 `baseline_intents`의 동일 check(`schema.sql:41-47`)를 남기면 N>5 Baseline이 실패하므로 함께 바꾼다.
- `artifact_cuts`에 positive `display_order`를 추가하고 `(artifact_id, display_order)`를 unique하게 한다. 과거/현재 artifact closure는 `ORDER BY display_order`로 읽으며, reorder 이후에도 과거 artifact의 당시 order가 보존된다.

### 4.2 trigger/index cutover

- `trg_cuts_no_insert`를 제거한다. creation/first Baseline/Phase 2 add가 positive stable cut을 삽입할 수 있어야 한다.
- `trg_cuts_no_delete`와 `trg_cuts_no_update_cut_id`는 fixed-five 문구를 제거하고 각각 historical ownership 보존과 identity 불변을 이유로 유지한다.
- 마지막 active cut을 inactive로 바꾸는 UPDATE를 거절하는 `trg_cuts_keep_one_active`를 추가한다. 이것은 `N>=1`을 보장하는 좁은 DB 경계다.
- display order uniqueness는 partial unique index가 담당한다. reorder transaction은 먼저 대상 rows의 order를 현재 max보다 큰 임시 positive range로 이동한 뒤 최종 `1..N`을 배정해 SQLite의 immediate uniqueness 충돌을 피한다.
- `trg_cut_intents_active_baseline`은 새 intent가 현재 active Baseline에 귀속되어야 한다는 기존 의미를 유지한다. 기존 intent revision을 새 structural baseline에서 재사용할 때는 `baseline_intents`가 binding authority이며 `cut_intents.baseline_id == current_baseline_id`를 요구하지 않는다.

### 4.3 fresh project와 first Baseline

- `TransactionalStore.create_project(project_dir, cut_count=5)`는 bool이 아닌 strict integer `N>=1`을 먼저 검증한다.
- `schema.sql`의 fixed five seed를 제거한다. 현재 임시 DB `BEGIN IMMEDIATE … COMMIT` script에 검증된 `1..N` row insert와 `is_active=1, display_order=1..N`을 포함해 schema/singletons/cuts를 한 번에 만든 뒤 verify하고 `os.replace`한다. 실패한 임시 DB는 삭제한다.
- CLI `init`에 `--cut-count`를 추가하고 default 5를 유지한다. `generate --cut`은 arbitrary positive integer를 parse하되 실제 active membership은 store가 판정한다.
- 최초 Baseline 전 pristine project는 Rebaseline/draft의 requested `N`을 승인 transaction에서 채택할 수 있다. 기존 cut rows에 history/intent/job/artifact가 전혀 없을 때만 부족한 IDs를 insert하거나 여분을 inactive로 바꾸고 order를 `1..N`으로 확정한다. 이미 Baseline/history가 있으면 implicit cardinality 교체를 하지 않고 Phase 2의 명시적 membership mutation을 사용한다.

### 4.4 v6→v7 atomic migration

SQLite는 table CHECK를 직접 변경하지 못하므로 `src/comic_new/migrations/v6_to_v7.sql` marker와 `_migrate_v6_to_v7()`의 명시적 table rebuild를 사용한다.

1. connection에서 `PRAGMA foreign_keys=OFF`를 **transaction 시작 전** 적용하고 `BEGIN IMMEDIATE`를 시작한다.
2. affected tables `cuts`, `cut_intents`, `baseline_intents`, `generation_jobs`, `artifact_cuts`를 새 v7 definition으로 rebuild한다. parent/child copy 순서를 고정하고 모든 columns를 명시해 copy한다.
3. 기존 다섯 `cuts`는 `is_active=1`, `display_order=cut_id`; 기존 `artifact_cuts.display_order=cut_id`로 backfill한다. 다른 identity/revision/path/hash/status/timestamp bytes는 변경하지 않는다.
4. old fixed triggers/indexes를 제거하고 §4.2 trigger/index를 설치한다. job queue index와 authorization unique index를 재생성/검증한다.
5. row counts, primary/foreign key targets, active order `1..5`, prompt hashes, artifact closure order를 old/new 사이에서 대조한다. `PRAGMA foreign_key_check`가 한 건이라도 반환하면 rollback한다.
6. `PRAGMA user_version=7`을 같은 transaction에서 설정하고 commit한 뒤 `foreign_keys=ON`을 복원한다. 재open `verify_schema()`까지 성공해야 migration 완료다.

schema-only migration은 current active set/content를 바꾸지 않으므로 composition/authority revision 또는 authorization을 철회하지 않는다. migration 중 bytes/row mapping이 달라지거나 실패하면 v6 전체가 남고 server preflight가 열리지 않는다. v4 workspace copy는 기존 v4→v5→v6 후 동일 v6→v7 경로를 연속 수행해 검증한다.

## 5. Backend 구현 방법

### 5.1 active-set reader를 단일 권위로 만들기

`store.py`에 작은 private query helper 하나를 둔다.

```text
_active_cuts(con, require_nonempty=True)
  -> SELECT ... FROM cuts WHERE is_active=1 ORDER BY display_order
```

이 helper는 positive/unique/contiguous order와 nonempty를 검사하고 다음 모든 writer/reader가 같은 결과를 사용한다.

- Baseline structure/intents set validation 및 intelligent default lookup
- per-cut intent membership validation
- enqueue-all target selection; single enqueue의 active membership 검사
- composition slot/bubble owner validation
- snapshot `cuts` ordering 및 `realization_complete`
- current closure validation, artifact registration/authorization/delivery start

physical `cuts` 전체 조회는 migration/ID allocation/history integrity에만 사용한다. inactive cut을 completion/render/release에 포함하거나 active cut을 빠뜨리는 별도 query를 두지 않는다.

### 5.2 Baseline approval과 Phase 2 membership mutation

기존 `approve_structural_baseline()`은 requested ordered IDs와 active set이 정확히 같아야 한다. 예외는 §4.3의 pristine first-Baseline count adoption뿐이다. structure와 intents는 같은 nonempty ordered unique positive IDs를 가져야 하며 list index가 아니라 `cut_id` map으로 resolve한다.

Phase 2에는 다음 store/API mutations를 추가한다. 구체 route 이름은 아래 계약을 유지하는 범위에서 구현자 재량이나, 세 동작을 하나의 모호한 partial patch endpoint로 숨기지 않는다.

1. **add cut:** current active set과 baseline structure/mappings를 읽고 `MAX(cut_id)+1` identity를 만든다. 요청의 role/beat/sparse intent를 새 intent revision 1로 저장하고 기존 active cuts의 current intent revision을 새 Baseline의 `baseline_intents`에 그대로 결속한다. requested insertion position으로 order를 재작성한다.
2. **retire cut:** target이 active이고 `N>1`인지 확인한다. row는 `is_active=0, display_order=NULL`로 바꾸고 남은 order를 압축한다. intent/job/artifact rows와 asset files를 삭제하지 않는다.
3. **reorder cuts:** 요청 배열이 현재 active ID 집합과 정확히 같고 중복이 없는지 검사한 뒤 §4.2의 임시 range→최종 order 방식으로 갱신한다.

세 mutation 모두 immutable한 새 structural baseline row를 만든다. 기존 cut은 current desired revision을 그대로 새 `baseline_intents`에 연결하고, add된 cut만 새 intent를 만든다. 따라서 reorder/retire가 기존 cut의 desired revision/request sequence를 증가시키지 않는다. enqueue/composition reader는 current binding을 `baseline_intents(baseline_id,cut_id,intent_revision)`로 확인하며 origin baseline ID가 다르다는 이유로 정당한 cloned binding을 거절하지 않는다.

각 mutation은 composition state도 같은 transaction에서 변환한다.

- mutation 전 active order와 `slot_heights_px`를 zip해 `cut_id -> height`로 만든다.
- reorder는 height를 동일 cut identity와 함께 재배열한다.
- retire는 current state에서 해당 cut height와 bubbles를 제거한다. 이전 immutable artifacts가 과거 geometry/history를 보존한다.
- add는 양의 기본 slot height를 한 개 넣고 bubble 없이 시작한다. 기본값은 기존 default composition factory가 소유하는 단일 per-cut constant를 재사용하며 새 정책 계층을 만들지 않는다.
- composition이 revision 0/`{}`이면 새 active order 길이에 맞는 default를 projection할 뿐 불필요한 accepted composition revision을 만들지 않는다. accepted state가 있으면 composition revision을 한 번 증가시킨다.

마지막에 authority revision을 한 번 증가시키고 active authorization을 같은 transaction에서 철회한다. 새 cut은 desired revision은 있어도 realized revision이 없으므로 fresh snapshot은 `UNRESOLVED`다.

### 5.3 generation/CAS/STOP

- `accept_cut_intent()`와 `GenerationService.enqueue()`는 arbitrary positive ID를 wire에서 받은 뒤 store transaction의 active membership을 판정한다. inactive/nonexistent ID는 400이고 job/sequence/authorization side effect가 0건이어야 한다.
- enqueue-all은 `_active_cuts()`의 ordered IDs를 사전 검증하고 한 컷이라도 invalid effective prompt면 하나도 enqueue하지 않는다. silent skip은 없다.
- claim/commit/cancel/STOP은 job의 stable `cut_id`를 계속 사용한다. membership mutation과 race 시 authority transaction serialization 후 inactive가 된 cut의 queued/running candidate는 commit-time active membership도 검사해 canonical current result로 승격하지 않는다. 기존 bytes/history는 보존하고 job을 superseded/interrupted의 정직한 terminal 상태로 둔다.
- reorder는 job identity나 sequence에 영향을 주지 않는다. add만 새 cut sequence 0에서 시작한다.

### 5.4 composition/renderer/materialization

`compute_cut_slots()`를 `(ordered_cut_ids, slot_heights_px, gap_px)` 계약으로 clean cutover하고 Python/TypeScript 모든 caller를 함께 이동한다. 길이는 같고 nonempty이며 cut IDs는 unique positive여야 한다. 반환 `ResolvedSlot.cut_id`는 `index+1`이 아니라 전달된 stable ID다.

- `composition.py:424-499`에서 `TOTAL_CUTS`, exact-five, `expected_cut_id=idx+1`을 제거한다. cuts payload 순서가 ordered active IDs와 exact-equal인지 검사하고 N cuts를 렌더한다.
- `composition_service.py:81-187`은 fresh active snapshot의 N, composition slots, currentness를 대조한다. duplicate convergence/readback도 기대 closure의 길이/ordered IDs를 사용하며 상수와 `1..N` 추정을 제거한다.
- embedded PNG closure와 store `artifact_cuts.display_order`에 동일 ordered IDs, revisions, asset IDs/hash, slots/fit/composition revision을 기록한다.
- materialization 전후 membership/order/intent/sequence/composition이 바뀌면 registration CAS 또는 fresh readback이 실패하고 staging/current artifact로 승격하지 않는다.

### 5.5 release/delivery

- `register_review_artifact()`는 입력 closure가 fresh active IDs와 exact ordered-equal이고 각 current identity/revision/asset과 일치할 때만 `artifact_cuts.display_order=1..N`으로 저장한다.
- `authorize_release()`와 `start_delivery_attempt()`은 artifact closure order/set을 fresh active closure와 대조한다. 길이만 같거나 map subset인 것은 충분하지 않다.
- `delivery.py:789-863`은 `len(cuts)==5`를 제거하고 nonempty active set 전체의 Current 및 physical asset hash를 검사한다. CompositionService가 읽은 immutable artifact bytes를 그대로 export/Blogger payload로 사용한다.
- membership/order mutation은 old authorization을 철회하므로 preflight와 mutation race에서 old bytes가 전달되지 않는다. INV-4의 destination readback/Unknown reconciliation 코드는 cardinality와 무관하므로 유지하고 N-cut regression만 추가한다.

### 5.6 server DTO/routes

- `CutId`/`CutPathId`를 strict positive integer로 바꾸고 bool/0/negative/string 숫자를 거절한다.
- Baseline DTO는 `cuts: list[...]`, intents list를 받되 nonempty, unique positive IDs, 두 ordered ID 배열 exact-equal을 검증한다.
- snapshot cut DTO에 `display_order`를 required로 추가하고 `cuts`는 active ordered array만 반환한다. job/artifact history의 `cut_id`도 positive integer이며 inactive historical ID를 type 오류로 만들지 않는다.
- `_default_composition(font_hash, ordered_cut_ids)`가 N개의 default heights를 만들고 `_render_contract()`는 stable IDs와 heights를 resolver에 전달한다.
- Phase 2 add/retire/reorder routes는 expected authority revision, nonempty mutation/baseline identity, exact payload를 받고 accepted mutation ID와 fresh snapshot을 반환한다. 409 conflict는 기존 current snapshot envelope를 재사용한다.
- `RealizationIncompleteError` 메시지를 “모든 active cuts의 current realization이 필요”로 바꾼다.

## 6. Frontend contract와 Studio UI

### 6.1 DTO/runtime validator clean cutover

`frontend/src/api/contracts.ts`에서:

- `CutId`를 branded alias 없이 `number`로 단순화하되 runtime에서는 positive safe integer를 강제한다.
- `BaselineStructureDTO.cuts`, `StudioSnapshotDTO.cuts`를 nonempty arrays로 바꾼다. five-tuple/length 5 validation을 삭제한다.
- snapshot active cuts는 `display_order`가 정확히 `1..N`, `cut_id`가 unique positive이며 Baseline structure/intents와 ordered IDs가 일치해야 한다.
- render contract slots의 ordered cut IDs가 snapshot cuts와 exact-equal이고 state heights 길이, gap 연속성, 마지막 bottom=`H`가 일치해야 한다.
- review artifact closure는 positive unique IDs 및 `display_order=1..N`을 검증한다. historical job cut ID가 current active set 밖이라는 이유만으로 snapshot을 거절하지 않는다.
- schema version은 7로 올리고 old six-shape를 optional alias/default로 수용하지 않는다.

### 6.2 RebaselineDialog cut_count와 draft adoption

`RebaselineDialog.vue:16-29,43-67,90-140`을 다음처럼 전환한다.

1. `cutCount` positive integer control을 source brief 옆에 둔다. 새 project/default draft는 server active N 또는 5를 초기값으로 사용한다.
2. 수동 count 변경은 `1..N` local rows를 한 번에 resize한다. 유지되는 rows의 편집값은 보존하고, 제거 예정 rows가 non-empty면 명시적 확인 없이 버리지 않는다.
3. AI request는 선택한 `cutCount`를 그대로 보낸다. validated response의 `result.cut_count`와 cuts length/order가 일치하면 count와 전체 cut/intents를 한 번에 채택한다. 일부 apply는 없다.
4. first Baseline에서는 display order를 최초 stable IDs `1..N`으로 매핑한다. 기존 project에서는 draft count가 active N과 다르면 자동 membership 변경으로 숨기지 않고 add/retire 변화 요약을 보여 준 뒤 명시적 승인 시 Phase 2 mutation을 사용한다.
5. failure/late response는 기존 `localEditVersion` guard를 유지해 brief, count, cut rows와 existing server snapshot을 보존한다. 성공 전에 dialog를 닫지 않는다.

### 6.3 CutRail, CompositionCanvas와 membership UI

- `CutRail.vue:9-20`은 fresh active `cuts`의 `display_order`를 그대로 순회한다. N cards를 scroll 가능한 rail로 렌더하고 key는 stable `cut_id`다. 각 card의 preview aspect/height는 대응 render slot height를 사용해 canonical proportion을 보존한다.
- `CompositionCanvas.vue:20-65,86-133`은 server `render_contract.slots` 또는 local resolver에 active ordered cut IDs를 함께 전달한다. slot top/height는 integer bounds에서만 파생하고 마지막 bottom은 H다. bubble slot lookup은 stable ID다.
- `studio.ts:485-505`는 fixed array 대신 `server.cuts` order로 intent draft queue를 순회한다. selection의 cut이 retire되면 fresh snapshot의 인접/첫 active cut으로 한 번 이동시키고 retired ID를 current selection으로 남기지 않는다.
- Phase 2 UI는 add, retire, 위/아래 이동을 제공한다. reorder는 전체 ordered ID array를 한 mutation으로 보내고, optimistic authority state를 만들지 않는다. pending 중 중복 submit을 막고 400/409/5xx에서 local proposal을 보존한다.
- `domain/currency.ts:15-18`은 `cuts.length>=1 && cuts.every(isCutCurrent)`로 바꾸되 authoritative release control은 server snapshot과 authorization readback을 계속 사용한다.

## 7. 파일별 line-anchored 변경 목록

1. `src/comic_new/schema.sql:16-47,56-69,115-121,159-197`
   - positive cut checks, active/display order, ordered artifact closure, dynamic seed/trigger/index schema로 전환한다.
2. 새 `src/comic_new/migrations/v6_to_v7.sql`
   - reviewed v7 rebuild marker/DDL을 둔다. copy 검증과 transaction orchestration은 store가 소유한다.
3. `src/comic_new/store.py:75-107,199-483,750-865`
   - schema 7, dynamic create, v6→v7 rebuild/verification 및 trigger/index contract를 구현한다.
4. `src/comic_new/store.py:146-186,876-1172`
   - cut map resolver, 단일 active-set query, active ordered snapshot/completion/artifact projection을 구현한다.
5. `src/comic_new/store.py:1174-1544`
   - N Baseline/intents/composition/enqueue와 first-Baseline count adoption을 구현한다.
6. `src/comic_new/store.py:2080-2280`
   - N ordered artifact registration/authorization/delivery closure 및 Phase 2 membership mutation을 구현한다.
7. `src/comic_new/generation.py:321-341` 및 commit eligibility path `:1675 이후`의 store 호출 경계
   - positive active ID validation과 inactive-race commit 차단을 연결한다.
8. `src/comic_new/composition.py:17-35,424-499, PNG closure 생성 구간`
   - `TOTAL_CUTS` 제거, stable ordered IDs resolver/renderer/metadata로 전환한다.
9. `src/comic_new/composition_service.py:81-187,258-443,499-532`
   - N active-set preflight, duplicate convergence, DB/PNG closure readback을 구현한다.
10. `src/comic_new/delivery.py:756-872`
    - fixed-five preflight를 exact active-set all-or-nothing gate로 바꾼다.
11. `src/comic_new/server.py:80-203,502-628,885-1023`
    - positive ID/N DTO, dynamic default/render contract, membership routes, N-cut 오류/response를 구현한다.
12. `src/comic_new/cli.py:30-57,114-133`
    - `init --cut-count N`, arbitrary positive `generate --cut`을 추가한다.
13. `frontend/src/api/contracts.ts:3-265,395-533,640-725`
    - positive integer IDs, N arrays, display order/schema 7/runtime cross-field validation을 구현한다.
14. `frontend/src/store/types.ts:1-60`, `frontend/src/store/studio.ts:485-612,614 이후 save actions`
    - dynamic draft maps/queue, draft count adoption, membership mutation actions와 conflict preservation을 구현한다.
15. `frontend/src/components/baseline/RebaselineDialog.vue:1-157,162-235`
    - cut count/manual resize/draft adoption/explicit membership summary를 구현한다.
16. `frontend/src/components/cuts/CutRail.vue:1-31` 및 `CutCard.vue`
    - ordered N cards, canonical proportions, add/retire/reorder controls를 구현한다.
17. `frontend/src/components/canvas/CompositionCanvas.vue:1-153`, `frontend/src/domain/geometry.ts`
    - stable ordered IDs를 사용하는 N slots/local bubble projection으로 전환한다.
18. `frontend/src/domain/currency.ts:3-18`, inspector/queue/review callers
    - N completion과 positive IDs를 clean cutover한다.
19. `tests/test_transactional_core.py`, `tests/test_generation.py`, `tests/test_composition.py`, `tests/test_release.py`, `tests/test_server.py`
    - §9 backend/migration/invariant 시나리오를 추가하고 fixed-five 목적 테스트는 새 제품 계약으로 교체한다.
20. `frontend/tests/store.test.ts`, `frontend/tests/geometry.test.ts` 및 Rebaseline/CutRail/Canvas component tests
    - §9 frontend contract/interaction/parity 시나리오를 추가한다.
21. `src/comic_new/static/`
    - 모든 source/contract 검증 후 production frontend를 한 번 rebuild하여 stale schema-6 bundle을 남기지 않는다.

## 8. 구현 순서와 원자적 cutover

1. **Conditional entry:** §10 CF-1/CF-2를 먼저 수행한다. BLOCK-12 parity 또는 migration 전제가 refute되면 dependent mutation을 시작하지 않는다.
2. **Phase 1 DB:** v7 current schema, dynamic create, v6→v7 migration, active-set reader와 schema verification을 구현한다.
3. **Phase 1 backend:** Baseline/intent/enqueue/snapshot/composition/renderer/materialize/release를 creation-time N으로 한 change set에서 전환한다. DB v7에 backend fixed-five reader가 남은 중간 상태를 배포하지 않는다.
4. **Phase 1 frontend:** schema-7 contracts, count/draft adoption, N CutRail/Canvas/store를 전환한다. backend N response를 five-tuple cast로 소비하는 bundle을 배포하지 않는다.
5. **Phase 1 handoff:** §10 CF-3에서 N=1/2/5/7 및 사용자 지정 3/4/6의 schema/API/UI/renderer/release parity를 판별한다. 성공 전 Phase 2 controls를 노출하지 않는다.
6. **Phase 2 authority:** add/retire/reorder, immutable structural baseline clone binding, composition transform, authorization revocation을 한 store transaction으로 구현한다.
7. **Phase 2 UI:** explicit controls와 failure-preserving store actions를 연결한다. drag animation/framework는 추가하지 않는다.
8. **Invariant/readback:** 3/4/6 end-to-end 및 add/retire/reorder 후 exact closure, INV-1~4, old authorization block을 실행한다.
9. **Bundle/cleanup:** focused proof 후 production static을 rebuild하고 disposable DB/server/provider/output/staging을 정리한다.

schema/API/frontend를 old/new dual authority로 운영하지 않는다. compatibility alias, optional fixed-five tuple, retired ID 재번호화, partial active-set release를 남기지 않는다.

## 9. 테스트 및 검증 계획

### 9.1 v6→v7 migration

`tests/test_transactional_core.py`에 실제 v6 schema fixture를 만들고 다음을 판별한다.

1. empty/history-rich v6 DB 각각이 v7로 열리고 `cut_id 1..5`, intent revisions, frozen job prompt/model/hash/status, realization paths/hashes, artifacts, authorizations, delivery attempts의 row/value가 보존된다.
2. migrated cuts는 active/order `[(1,1)…(5,5)]`; artifact cuts의 historical order도 1..5다. 모든 relevant table SQL에서 `BETWEEN 1 AND 5`가 사라지고 positive constraint가 실제로 6을 수용하며 0/negative를 거절한다.
3. `foreign_key_check` 0건, required triggers/indexes 존재, old no-insert trigger 부재, delete/id-update/last-active guards 동작을 확인한다.
4. copy 중 duplicate/order/FK/hash mismatch를 주입하면 user_version/data/authorization이 v6 그대로 rollback된다.
5. migration 재open은 no-op이고 authority/composition revision과 active authorization을 불필요하게 바꾸지 않는다.
6. repository `workspace` DB copy를 open해 v4→v5→v6→v7 연쇄가 동일하게 성공하고 원본 file은 변경하지 않는다.

### 9.2 creation-time 3/4/6 end-to-end

각 N=3,4,6에 대해 disposable project에서 실제 store/service/server/renderer를 연결한다.

1. `create_project(N)` 또는 first Baseline draft count adoption 후 fresh snapshot의 IDs/order/schema 7을 확인한다.
2. empty/partial prompt Baseline을 승인하고 ordered structure/intents/origin을 fresh snapshot에서 확인한다.
3. 한 cut만 enqueue/realize하면 그 cut만 Current, aggregate `UNRESOLVED`; materialize/authorize/export/Blogger는 차단된다.
4. enqueue-all 또는 개별 실행으로 N cuts를 모두 Current로 만들고 nonuniform heights/gap, cut-local bubbles로 실제 PNG를 materialize한다.
5. PNG dimensions는 `1024 × [Σ heights+(N-1)gap]`, embedded closure와 DB artifact closure의 ordered N IDs/revisions/assets/hash가 exact-equal이어야 한다.
6. authorization 후 PNG export destination bytes를 다시 읽어 artifact bytes/hash와 byte-identical인지 확인한다. controlled Blogger adapter는 N과 무관한 marker/hash readback 경계를 실행하되 실제 유료 게시를 대체했다고 주장하지 않는다.

전이 권위의 명시 matrix인 N=1/2/5/7도 store/API/geometry/release 경계에서 추가 실행한다. 3/4/6은 사용자 요구의 주요 end-to-end matrix이고 1/2/5/7은 minimum/legacy/odd-N 반례 matrix다.

### 9.3 Phase 2 membership/order

1. 4-cut complete project에서 cut 5/6을 add한다. 기존 cut 1..4 revisions/sequences/jobs/assets는 byte/value 동일, 새 IDs는 5/6이고 전체는 즉시 `UNRESOLVED`다.
2. active order를 `[6,2,1,4,5,3]`으로 바꾼다. cut IDs와 history는 그대로이고 snapshot, render slots, Canvas, artifact closure가 같은 order다. local bubble values는 cut identity별로 불변이다.
3. cut 4를 retire한다. physical row와 intent/job/old artifact는 남고 current snapshot/render/release closure에서는 제외된다. retired ID를 새 cut에 재사용하지 않는다.
4. 마지막 active cut retire, duplicate/missing/unknown reorder ID, inactive intent/enqueue는 400/ValidationError이고 authority/composition/authorization/job에 side effect가 0건이다.
5. membership/order 변경 직전 active authorization은 같은 authority revision에서 revoked되고 old authorization의 materialize/export/Blogger 시작은 실패한다.
6. 새 active set 전부를 Current로 만든 뒤 새 artifact를 materialize/authorize해야만 delivery preflight가 통과한다.

### 9.4 4대 인과 불변식과 All-or-Nothing

N=3,4,6 각각에서 다음 회귀를 실행한다.

- **INV-1:** 같은 cut의 동일 revision request_seq 경쟁과 reorder 동시 발생에서 오래된 candidate commit 0건, 최신 tuple만 canonical.
- **INV-2:** provider pre-commit에서 single cancel/global STOP 후 late candidate가 canonical bytes를 바꾸지 않는다. membership retire race도 commit eligibility를 우회하지 않는다.
- **INV-3:** intent, enqueue, accepted realization, composition 1px, add/retire/reorder 각각에서 old authorization이 mutation과 같은 transaction에서 revoked된다. 실패/no-op mutation은 근거 없이 revoke하지 않는다.
- **INV-4:** export destination tamper는 confirmed failure, Blogger missing/duplicate/mismatched marker는 실패, timeout은 Unknown이며 reconciliation은 readback-only다.
- **All-or-Nothing:** 각 N에서 첫/중간/마지막 한 cut을 Stale/Unrealized로 만든 matrix 모두 materialization와 release를 차단하고, generated subset을 complete로 표시하지 않는다.

### 9.5 frontend contract와 UI

- contracts validator: N=1/3/4/6/7 valid snapshot, nonempty/unique/order exactness, zero/negative/duplicate/gap/order/slot mismatch reject, inactive historical job 허용.
- Rebaseline: manual count 3/4/6 row 생성, 값 보존 resize, validated draft count adoption, late response ignore, 실패 draft/count 보존, first Baseline success-only close.
- store: `server.cuts` 순서의 dynamic save lane, add/retire/reorder 409 resync, local proposal preservation, retired selection recovery.
- CutRail: N cards의 stable key/order와 slot-proportional preview; fixed viewport에서 scroll 가능하고 card 누락/중복이 없다.
- Canvas/geometry: shared case fixture로 stable IDs `[6,2,1,4,5,3]`, nonuniform heights, exact top/bottom/gap, last bottom=H, bubble owner/projected rect를 Python과 TypeScript에서 동일하게 확인한다.
- 실제 browser smoke에서 3/4/6 전환, rail/card 수, canvas slot bounds를 `getBoundingClientRect()` pixel readback으로 확인하고 materialized PNG closure와 비교한다. CSS screenshot만으로 authority 성공을 판정하지 않는다.

## 10. Conditional First Work

### CF-1 — BLOCK-12 exit/currentness

- `plan_anchor`: `PLAN-001 §1, §3.3, §9.5`
- `permitted_initial_work`: 제품 source mutation 전에 disposable current-v6 project에서 accepted composition의 backend/frontend slots, contain fit, cut-local bubble, materialized PNG closure를 fresh snapshot/browser/artifact에서 읽는다.
- `discriminating_observation`: server render slots와 browser slot bounds가 exact integer projection으로 일치하고 last bottom=H이며, PNG size/fit/bubble owner가 동일 accepted composition closure와 일치한다.
- `dependent_work_not_yet_permitted`: 이 결과가 refuted인 상태에서 v7 membership/order 또는 N renderer cutover를 시작하는 작업.
- `response_if_refuted`: BLOCK-13 mutation을 중단하고 Main에게 BLOCK-12 regression evidence를 반환한다. 선행 Scope 복구/재검증 뒤 Plan currentness를 다시 검토한다.

### CF-2 — 실제 DB migration inventory

- `plan_anchor`: `PLAN-001 §3.1, §4.4, §9.1`
- `permitted_initial_work`: 권한 있는 실제 대상 DB를 read-only 또는 disposable copy로 열어 `user_version`, affected table SQL, triggers/indexes, row counts, foreign-key check, max cut ID, active baseline, job/artifact/authorization/delivery history를 조회한다. 원본 DB를 변경하지 않는다.
- `discriminating_observation`: 모든 DB가 canonical v6이거나 기존 supported migration chain으로 v6에 결정적으로 도달하며, v7 rebuild의 각 old column/history row를 손실 없이 명시 mapping할 수 있다.
- `dependent_work_not_yet_permitted`: 관찰 전에 실제 DB에 table rebuild를 실행하거나 unmapped column/history를 drop/default backfill하여 user_version 7로 올리는 작업.
- `response_if_refuted`: migration을 추측하지 않는다. 새로운 legacy shape/무귀속 history면 source와 exact mismatch를 Main에게 반환하고 migration method를 revise한 뒤 fresh independent review를 받는다.

### CF-3 — Phase 1 → Phase 2 handoff

- `plan_anchor`: `PLAN-001 §2.1, §8 step 5, §9.2`
- `permitted_initial_work`: Phase 1 implementation 후 disposable N=1/2/5/7 및 3/4/6 projects에서 schema/API/UI/renderer/release active-set parity와 existing N=5 migration 보존을 실행한다.
- `discriminating_observation`: 모든 N에서 nonempty ordered snapshot, exact slots/closure, partial release block, all-current materialize/authorize/export readback이 성립하고 N=5 history가 보존된다.
- `dependent_work_not_yet_permitted`: Phase 2 add/retire/reorder controls를 사용자 도달 surface에 노출하거나 BLOCK-13 completion을 주장하는 작업.
- `response_if_refuted`: Phase 2 노출을 중단하고 Phase 1의 해당 owner/schema/interface/readback method를 수정한다. owner/interface가 Plan과 달라지면 Plan revision과 fresh review를 받는다.

## 11. 구현자 Self-check와 최종 Acceptance Readback

### 11.1 최소 실제 경로

1. v6 history-rich fixture 및 실제 workspace copy를 별도 경로에서 v7로 open하고 migration 전후 row/value/FK/order/hash를 대조한다.
2. 실제 server를 production frontend bundle과 함께 disposable 4-cut project로 기동한다.
3. Rebaseline에서 수동 count 4 및 AI draft count 4를 각각 실행하고, 성공 전 dialog 유지/실패 보존/승인 후 fresh snapshot을 확인한다.
4. cut 1만 생성하여 partial completion 및 materialize/release block을 확인한 뒤 4 cuts를 모두 실제 generation boundary 또는 승인된 controlled provider로 실현한다. double이 대체한 provider availability는 관찰 한계로 분리한다.
5. nonuniform layout과 bubbles를 저장하고 browser slots와 materialized PNG size/embedded closure를 비교한다.
6. authorization 후 PNG export를 수행하고 destination bytes/hash를 readback한다.
7. cut add, reorder, retire를 수행해 stable IDs/revisions/sequences/history, local bubbles/order, immediate authorization revocation, new cut `UNRESOLVED`를 fresh snapshot에서 확인한다.
8. 새 active set을 모두 Current로 만든 뒤 새 artifact만 authorize/export 가능함을 확인한다.
9. generation candidate를 pre-commit STOP하여 late commit 0건을 확인하고, destination mismatch/Unknown recovery를 실행한다.

### 11.2 Scope Acceptance 매핑

- **A. SQLite Schema v7 및 N>=1:** §4, §7 items 1-6, §9.1-9.2, §11.1 steps 1-3.
- **B. Backend service/API N generalization:** §5.1-5.4, §7 items 4-11, §9.2-9.3.
- **C. Frontend N-cut 및 Studio UI:** §6, §7 items 13-18, §9.5, §11.1 steps 2-5/7.
- **D. All-or-Nothing release:** §2.1/2.2, §5.4-5.5, §9.2-9.4, §11.1 steps 4/6/8.
- **E. 4대 인과 불변식/cutover:** §2.3, §5.3/5.5, §9.3-9.4, §11.1 steps 7-9.
- **BASELINE-003 Phase 2 obligations:** §2.2, §4.1-4.2, §5.2, §6.3, §9.3.

### 11.3 최종 명령/관찰과 cleanup

- focused backend: migration/store/generation/composition/release/server의 위 시나리오만 먼저 실행한다.
- focused frontend: contract/store/geometry/component tests, type check, production Vite build를 실행한다.
- main integration owner가 stable target에서 전체 backend/frontend suite를 한 번 실행한다.
- actual browser에서 3/4/6 및 Phase 2 order를 확인하고 artifact/destination readback evidence를 보존한다.
- disposable server/runner/provider를 종료하고 process tree, 임시 DB/export, `.generation-staging`, `.composition-staging`을 정리한다. throwaway script를 repository에 남기지 않는다.
- Scope/Thesis/Baseline/Plan 및 stable implementation target bytes를 다시 hash해 verifier handoff currentness를 고정한다.

테스트 통과, DOM card 수, queue empty 또는 파일 존재만으로 BLOCK-13 성공을 선언하지 않는다. authoritative success는 fresh active membership/order, per-cut tuple, immutable N-cut closure, authorization state와 destination identity readback을 연결한 관찰이다.

## 12. 실패·중단·재개 경계

- **project create 실패:** temp DB를 삭제하고 destination에 partial project를 남기지 않는다.
- **migration 실패:** transaction rollback, original version/data/history/authorization 보존, preflight fail. 자동 schema retry로 partial table을 current로 열지 않는다.
- **Baseline/count 실패:** authority/cuts/intents/composition 무변경, browser count/brief/cut draft 보존.
- **membership/order 실패:** active set/order/composition/baseline/authorization 모두 rollback. 임시 display order가 commit되지 않는다.
- **add 후 generation 실패:** 새 cut은 active/Stale로 남고 전체 `UNRESOLVED`; 기존 canonical assets/history를 삭제하지 않는다.
- **retire/reorder와 worker race:** serialized authority 상태에서 inactive/stale candidate commit을 차단한다. process 성공/파일 생성만으로 canonical 승격하지 않는다.
- **materialization interruption:** staging만 정리하고 artifact row/authorization을 만들지 않는다. publish 후 registration ambiguity는 exact DB/file/closure convergence로만 수용한다.
- **frontend 400/409/422/5xx/stream gap:** local proposal을 보존하고 fresh snapshot을 재조회한다. authority 복구 전 release controls를 차단한다.
- **delivery timeout:** outcome은 Unknown이며 기존 destination readback만 수행한다. 자동 재게시하지 않는다.

## 13. 구현 재량과 재검토 반환 조건

구현자는 helper/route 이름, SQL rebuild table 임시 이름, equivalent query ordering, UI button placement와 CSS 세부처럼 관찰 계약을 바꾸지 않는 내부 선택을 할 수 있다. 다음은 material method 변경이므로 영향을 받은 구현을 멈추고 이 Plan을 revise한 뒤 fresh independent Plan Review를 받아야 한다.

- `cuts`가 아닌 sidecar를 active membership/order의 경쟁 권위로 도입하는 설계;
- stable `cut_id`를 display order로 재번호화하거나 retired ID를 재사용하는 설계;
- current active set을 통하지 않는 별도 completion/materialize/release query;
- `artifact_cuts.display_order` 또는 동등한 immutable ordered closure 없이 과거 artifact order를 추정하는 설계;
- membership mutation과 composition/authorization revocation을 서로 다른 transaction으로 나누는 설계;
- reorder/retire만으로 기존 cut desired revision/request sequence를 증가시키는 설계;
- schema 6/7 또는 fixed-five/N DTO를 optional alias/dual-write로 동시에 권위화하는 설계;
- partial active cuts를 skip해 materialize/release하거나 destination readback을 내부 success로 대체하는 설계.

제품 의미, BLOCK-13A→13B 전환 지리, `N>=1`, identity/history/partial-release 의미를 바꿔야 하면 Plan이 결정하지 않고 Main에게 Thesis/Baseline/Scope owning source 수정으로 반환한다.

이 문서는 실행 방법이며 구현·검증·완료 판정이 아니다. exact Scope/Plan bytes에 대해 독립 Plan Reviewer가 모든 Acceptance, v7 migration, 13A→13B handoff, active-set closure, 네 불변식 및 failure/readback 반례를 검토해 `ADMIT`한 후에만 구현을 시작한다. 현재 할당은 독립 Reviewer invocation을 허용하지 않으므로 이 Plan 작성 자체는 ADMIT이 아니다. Scope `done`은 별도 semantic verification과 Coverage 후 Main만 기록한다.
