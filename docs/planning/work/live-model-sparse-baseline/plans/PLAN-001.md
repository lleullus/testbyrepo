# PLAN-001 — BLOCK-10 Live Model Repair 및 Sparse Baseline 승인

## 1. 결속된 권위와 실행 경계

- Project Root: `/home/user01/project/comic_new`
- Scope: `/home/user01/project/comic_new/docs/planning/work/live-model-sparse-baseline/SCOPE.md` (sha256 `b142d37d605c1e9c6532a49d23743a24733548560ae8cfc2537077a5e4907462`, `Status: ready`)
- Normative Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md` (`THESIS-003`, sha256 `d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268`)
- Transition Authority: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md` (sha256 `59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51`, selected `BLOCK-10`)
- Repository investigation: 별도 불변 artifact는 제공되지 않았다. 이 Plan은 위 세 원본과 현재 source/test bytes를 직접 조사한 결과에 결속한다.
- Scope validator: canonical `validate_scope.py --json` 결과는 `iis-scope/v1`, `status: ready`, 위 Thesis/Transition path와 digest의 정확한 일치를 반환했다.
- 허용 범위: 구현자는 BLOCK-10만 구현한다. BLOCK-11의 OpenCodex draft API, BLOCK-12의 geometry/좌표, BLOCK-13의 N-cut schema/membership은 시작하지 않는다.
- 증거 경계: mock provider는 subprocess·stdin·job commit 같은 로컬 generation 경계를 판별하는 보조 수단일 뿐 live 모델 연결 성공의 대체 증거가 아니다. 실제 모델 수용은 default ima2 command와 실제 provider 요청/결과 및 authoritative job readback을 대조해야 한다. 외부 Blogger 실발행은 하지 않는다.

## 2. 달성할 관찰 결과와 보존 조건

사용자는 다섯 컷의 prompt가 모두 비었거나 일부만 작성된 Baseline을 승인할 수 있고, 서버가 각 빈 prompt를 해당 컷의 `source_brief`, `cut_id`, `role`, `beat`에 결속된 non-empty intelligent default로 확정하여 fresh snapshot에 반환해야 한다. 이후 다른 컷의 준비·실현 여부와 관계없이 선택한 한 컷만 enqueue할 수 있어야 한다. 새 job은 실제 사용한 model, effective prompt, prompt identity 및 origin과 현재 desired revision/new request sequence를 enqueue transaction 안에서 고정하며, worker는 intent를 뒤늦게 재해석하지 않고 이 고정값만 provider에 전달한다.

다음은 동시에 유지한다.

1. **INV-1 Monotonic Sequence CAS:** `(cut_id, desired_revision, request_seq, model, effective_prompt identity)`가 job에 고정되고 commit 시 최신 revision/sequence/eligibility 검사는 그대로 유지된다.
2. **INV-2 STOP Pre-commit Lockout:** enqueue 이후 cancel/STOP이 commit 자격을 먼저 철회하고 process를 정리하는 기존 경계는 변경하지 않는다.
3. **INV-3 Atomic Approval Revocation:** Baseline 승인, intent 변경, generation enqueue가 결과를 바꾸면 같은 transaction에서 active authorization을 철회한다.
4. **INV-4 Destination Content Readback:** export/Blogger readback 경로는 변경하지 않으며 부분 generation을 release 성공으로 승격하지 않는다.
5. 단일 컷 성공은 그 컷만 `CURRENT`로 만들고 나머지 active cut이 `STALE`/미실현이면 aggregate는 `UNRESOLVED`다. review materialize/authorize/export/Blogger는 기존 exact five-current closure에서 계속 차단된다.
6. provider 실패를 `nano-banana-pro` 또는 다른 모델로 묵시적으로 재시도하지 않는다. 실패는 해당 job의 정직한 실패이고 기존 canonical realization을 보존한다.

## 3. 현재 코드 Grounding

### 3.1 EXISTING — 모델 및 provider 실행 경로

- `src/comic_new/generation.py:318-338`: `GenerationService.enqueue()`는 single/all 선택을 `TransactionalStore.enqueue_generation_jobs()`에 위임한다.
- `src/comic_new/generation.py:429-474`: `GenerationRunner.default_provider_cmd()`가 ima2 `gen --stdin --mode direct` command를 만들며, 현재 `--model nano-banana-pro`를 하드코딩한다.
- `src/comic_new/generation.py:595-638, 713-718`: worker는 store claim의 `prompt`를 stdin bytes로 provider에 전달한다. custom `provider_cmd_factory`는 테스트 경계이고 production default command는 위 method다.
- `tests/test_generation.py:153-228`: 실제 mock-provider subprocess의 stdin과 candidate commit을 검증하지만 production default command의 model 값은 고정하지 않는다.

이 증거는 production default model 결손과 prompt의 실제 provider 입력 경로를 확정한다. live provider 자체의 가용성은 source inspection만으로 확정하지 않는다.

### 3.2 EXISTING — Baseline validation과 fallback 재료

- `src/comic_new/store.py:120-130`: `_parse_structured_intent()`가 모든 caller에 대해 prompt `None`, 비문자열, 빈 문자열, whitespace-only를 동일하게 거절한다.
- `src/comic_new/store.py:758-840`: `approve_structural_baseline()`은 transaction 전 `intents_by_cut` 1..5를 공통 parser로 검사하므로 빈 prompt 하나가 전체 승인을 막는다. 승인 성공 시 다섯 intent revision, active baseline, composition dialogue synchronization, authorization revoke가 하나의 mutation에 있다.
- `src/comic_new/server.py:114-154, 893-904`: HTTP request에는 `structure.source_brief`, ordered cut별 `role`/`beat`, prompt/dialogue가 모두 도달한다. 즉 fallback에 필요한 재료는 승인 요청 안에 이미 있다.
- `src/comic_new/store.py:504-601`: fresh snapshot은 각 cut의 stored `effective_intent`와 aggregate currentness를 권위 readback으로 제공한다.
- `tests/test_transactional_core.py:233-299`: 승인 snapshot 및 monotonic intent revision의 기존 보존 시험이 있다.

### 3.3 EXISTING — enqueue와 job identity 결손

- `src/comic_new/store.py:1022-1085`: enqueue는 `BEGIN IMMEDIATE` 아래 대상 컷만 선택할 수 있고 active baseline, desired revision을 확인한 뒤 request sequence 증가, job insert, authorization revoke, authority revision 증가를 원자적으로 commit한다. 그러나 공통 parser가 먼저 empty를 거절하므로 lines 1055-1058의 명시적 non-empty guard는 사실상 중복이다.
- `src/comic_new/schema.sql:56-65`: `generation_jobs`에는 `cut_id`, `target_desired_revision`, `request_seq`, status만 있고 model/effective prompt/origin/identity가 없다.
- `src/comic_new/store.py:1219-1293`: claim 시 job에 고정된 prompt가 아니라 `cut_intents.payload_json`을 다시 조회한다. 따라서 enqueue 때 사용한 prompt/model identity를 authoritative readback하거나 immutable job input으로 보장할 수 없다.
- `src/comic_new/store.py:614-649` 및 `frontend/src/api/contracts.ts:90-100`: backend snapshot과 frontend `JobDTO`에도 model/effective prompt/origin/identity가 없다.
- `tests/test_generation.py:1019-1078`: revision/request sequence stale overwrite CAS는 이미 강하게 시험한다. 새 필드 추가는 이 검사를 대체하지 않고 tuple을 확장한다.
- `tests/test_transactional_core.py:727-762`: enqueue와 authorization revoke가 같은 transaction이고 pending latest sequence가 review/authorize를 막는 기존 시험이 있다.

따라서 job identity/readback 요구는 단순 model 상수 교체만으로 충족되지 않는다. schema version 증가와 migration, enqueue/claim/snapshot/DTO의 일관된 cutover가 필요하다.

### 3.4 EXISTING — frontend 저장 실패/대화상자 경계

- `frontend/src/components/baseline/RebaselineDialog.vue:56-75`: submit은 draft를 만든 직후 비동기 save 결과를 기다리지 않고 dialog를 즉시 닫는다.
- `frontend/src/store/studio.ts:350-427`: `dispatchEdit()`는 성공 시 authoritative snapshot을 적용하고 draft를 지우며, 실패/409에서는 draft와 save failure를 보존한다.
- `frontend/src/store/studio.ts:537-570`: `saveBaselineDraft()`는 위 dispatch를 호출하지만 결과를 반환하지 않는다.
- `frontend/tests/store.test.ts:193-245`: Baseline 성공 후 draft/composition 직렬화를 검증한다. 실패 보존은 store 수준에 존재하지만 dialog가 성공 전에 닫히지 않는 제품 의미는 아직 충족하지 않는다.

## 4. 구현 방법

### 4.1 Intent parser를 구조 검증과 generation eligibility로 분리

`src/comic_new/store.py:120-130`의 `_parse_structured_intent()`는 JSON object, `prompt`의 문자열 타입, `dialogue`의 문자열 타입만 검증하도록 바꾼다. `prompt`는 `""`와 whitespace-only를 허용하되 입력 문자열 자체를 반환한다. dialogue는 빈 문자열을 유효한 무대사로 그대로 보존한다.

빈 값 허용은 Baseline 승인에만 필요한 정책이지만 parser는 migration/snapshot/intent 변경에서도 사용되므로, non-empty generation 조건을 이 공통 parser에 남기지 않는다. `accept_cut_intent()`도 sparse intent를 저장할 수 있게 되어 “저장 가능한 intent”와 “생성 가능한 effective prompt”가 일관되게 분리된다.

`approve_structural_baseline()` 진입부에 작은 private resolver를 추가한다. 각 cut에 대해:

1. 입력 prompt가 `strip()` 후 non-empty이면 원문을 보존하고 origin은 request가 제공하는 기존 provenance가 없으므로 현재 BLOCK-10 수동 경로에서는 `user`로 둔다.
2. empty/whitespace-only이면 structure를 검증해 해당 `cut_id`의 row를 정확히 하나 찾고 `source_brief`, `role`, `beat`를 문자열로 읽는다.
3. intelligent default를 정확히 `f"{source_brief} - 컷 {cut_id} ({role}: {beat})"`로 만든다. 각 성분은 leading/trailing whitespace를 정규화하되 컷 identity 표시는 유지한다.
4. 결과를 `strip()` 후 검사한다. 위 형식은 cut identity를 포함하므로 source/role/beat가 비어도 `컷 {cut_id}` 기반 non-empty generic default가 된다. origin은 `intelligent_default`다.
5. dialogue는 합성하지 않고 입력값을 그대로 둔다.

저장 payload는 최소 `{prompt, dialogue, prompt_origin}`으로 확장한다. `_parse_structured_intent()`는 `prompt_origin`이 있으면 `user | llm_draft | intelligent_default`만 허용하고, legacy/current input처럼 없으면 명시적 caller 정책으로 origin을 공급한다. BLOCK-10은 LLM draft 생성 자체를 도입하지 않지만 향후 origin 값을 훼손하지 않는 schema를 사용한다. Snapshot의 `effective_intent`에 origin이 포함되어 fallback의 정직한 readback이 가능해야 한다.

구조 자체의 ordered cut 검사는 server DTO가 수행하지만 store 직접 caller도 있으므로 resolver는 `structure`가 dict이고 `source_brief`가 string이며 `cuts`가 ordered 1..5, 각 role/beat가 string인지 확인한다. 이 검증은 BLOCK-13 cardinality 변경이 아니라 현재 다섯 컷 계약의 방어다.

### 4.2 Generation job input을 enqueue transaction에서 동결

새 schema version은 **v5**로 올리고 다음 작업을 한 cutover로 적용한다.

- `src/comic_new/schema.sql:56-65`의 `generation_jobs`에 non-null `model`, `effective_prompt`, `effective_prompt_origin`, `effective_prompt_sha256`를 추가한다.
- `src/comic_new/migrations/v4_to_v5.sql`을 추가하고 `store.py:219-381` migration dispatcher에 v4→v5를 연결한다. 기존 job은 연결된 desired intent payload에서 prompt/origin을 결정적으로 backfill하고 SHA-256을 계산해야 한다. SQL만으로 hash를 계산하지 말고 migration transaction에서 Python `hashlib.sha256(prompt.encode("utf-8"))`를 사용한다. 기존 job의 historical production model을 증명할 수 없으므로 `legacy/unknown`처럼 거짓 model을 쓰지 않는다. **조건부 시작:** 기존 DB에 generation job이 있으면 schema mutation 전에 해당 model attribution 가능성을 판별한다(§7). attribution 불가능하면 migration을 추측으로 완료하지 않고 Plan 재검토로 돌린다. 새 프로젝트 schema에는 네 필드를 처음부터 NOT NULL로 둔다.
- `verify_schema()`는 새 column 존재, allowed origin, non-empty model/prompt, prompt hash 형식 및 실제 SHA-256 일치를 검사한다.
- `enqueue_generation_jobs()`는 대상 컷별 current intent에서 prompt/origin을 resolve한 뒤 여기서만 strict non-empty를 수행한다. single-cut 요청은 오직 해당 cut만 검사한다. bulk `cut_id=None`는 현재의 all-or-nothing prevalidation을 유지하여 invalid 컷을 조용히 skip하지 않는다.
- model은 production 기본 상수 `oauth/gpt-image-2.5-flare`로 고정한다. 사용자 model 선택 UI는 Non-Goal이므로 새 선택 파라미터를 API에 만들지 않는다.
- effective prompt SHA-256은 UTF-8 prompt bytes에 대해 계산한다. job insert와 `latest_generation_request_seq` 증가, authorization revoke, authority revision update는 기존 하나의 `BEGIN IMMEDIATE` 안에 둔다. validation 실패는 rollback되어 sequence/job/authorization에 부분 효과가 없어야 한다.
- `claim_next_generation_job()`은 intent table을 다시 읽어 prompt를 재결정하지 않는다. job row의 frozen model/prompt/origin/hash를 읽고 hash를 재확인한 후 claim에 반환한다. current desired revision/latest sequence CAS는 그대로 먼저 적용한다.
- `GenerationRunner`는 claim model을 `default_provider_cmd()`에 전달하고, command의 `--model` 값으로 사용한다. production default는 반드시 `oauth/gpt-image-2.5-flare`; `nano-banana-pro` fallback branch는 만들지 않는다. custom test factory의 기존 signature는 필요하면 model/prompt identity를 명시적으로 받도록 한 번에 migrate하며 호환 shim은 남기지 않는다.

이 구조는 worker가 enqueue 후 수정된 intent를 소비하는 TOCTOU를 제거하고 INV-1 tuple을 실제 durable job identity로 만든다.

### 4.3 Snapshot/API/frontend readback 확장

`src/comic_new/store.py:614-649` job projection에 `model`, `effective_prompt`, `effective_prompt_origin`, `effective_prompt_sha256`를 포함한다. `GenerationService.enqueue()` receipt와 `POST /api/generation/jobs` response는 fresh snapshot에서 같은 값을 반환한다.

`frontend/src/api/contracts.ts:37-40, 68-100, 154-173`를 함께 갱신한다.

- `PromptOrigin = 'user' | 'llm_draft' | 'intelligent_default'`를 정의한다.
- `CutIntentDTO`의 readback에는 origin을 포함하되 Baseline submit DTO는 origin을 서버가 판단할 수 있도록 별도 request type으로 분리한다. 하나의 interface에 optional을 붙여 권위/입력 의미를 흐리지 않는다.
- `JobDTO`에 model, effective prompt, origin, SHA-256을 required field로 추가한다.
- runtime `isStudioSnapshotDTO()`는 새 schema version 5, intent origin 및 job identity/hash의 구조를 검증한다. hash가 prompt bytes와 일치하는 cryptographic 검사는 backend authoritative readback이 담당하고 frontend는 wire shape를 검사한다.
- `server.py`의 DTO projection은 store 값을 그대로 내보내되 model/prompt identity를 재계산하지 않는다.

### 4.4 기본 model command 교체

`src/comic_new/generation.py:455-474`에서 `nano-banana-pro`를 완전히 제거하고 job에 고정된 `oauth/gpt-image-2.5-flare`를 `--model` 인자로 전달한다. `ima2 gen --stdin --mode direct --no-size-nudge`, size/quality/timeout/output/json 설정은 Scope 밖이므로 유지한다.

production 경로 어디에도 `nano-banana-pro` 문자열 또는 failure fallback이 남지 않아야 한다. 테스트 fixture에서 과거 값을 검증 목적으로 언급하는 경우 외에는 source에서 제거한다.

### 4.5 Baseline dialog는 승인 응답 후에만 닫기

`frontend/src/store/studio.ts:350-427`의 `dispatchEdit()`와 `saveBaselineDraft()`가 해당 mutation의 성공 여부를 `Promise<boolean>`로 반환하게 한다. 성공은 accepted mutation id가 요청 id와 일치하고 authoritative snapshot이 적용된 경우만 true다. conflict, validation, network failure, stale/mismatched response는 false이며 현재 draft/save error를 보존한다. background lane caller는 반환값을 무시할 수 있으나 dialog submit은 직접 await한다.

`frontend/src/components/baseline/RebaselineDialog.vue:71-75`는 `async submit()`으로 바꾸고:

1. draft를 update한다.
2. `await store.saveBaselineDraft()`한다.
3. true일 때만 `close()`한다.
4. pending 동안 confirm button을 disable하고 중복 submit을 막는다.
5. false이면 dialog, source brief, role/beat/prompt/dialogue 입력을 그대로 유지한다. 기존 store toast/save error를 재사용하고 별도 오류 상태 계층을 만들지 않는다.

빈 prompt를 frontend에서 막는 validation은 추가하지 않는다. server가 intelligent default를 확정한 성공 snapshot을 적용하므로 다음 open/readback에는 실제 저장된 prompt/origin이 보인다.

## 5. 파일별 line-anchored 변경 목록

1. `src/comic_new/generation.py:429-474, 619-638`
   - frozen job model을 command builder로 전달한다.
   - default/live model을 `oauth/gpt-image-2.5-flare`로 고정하고 `nano-banana-pro`를 제거한다.
2. `src/comic_new/store.py:73-75, 120-130, 219-381, 382-454`
   - schema v5, sparse parser/origin validation, v4→v5 migration, schema verification을 추가한다.
3. `src/comic_new/store.py:758-840`
   - Baseline structure에서 per-cut intelligent default를 resolve하고 origin과 함께 저장한다. 기존 revision/authorization/composition transaction 경계는 유지한다.
4. `src/comic_new/store.py:1022-1091, 1197-1293`
   - target-only strict enqueue validation, frozen model/prompt/origin/hash insert 및 frozen claim 소비로 바꾼다.
5. `src/comic_new/store.py:504-649`
   - intent origin과 job identity를 authoritative snapshot에 투영한다.
6. `src/comic_new/schema.sql:56-65` 및 새 `src/comic_new/migrations/v4_to_v5.sql`
   - generation job identity columns와 migration을 추가한다. cuts cardinality/DDL은 변경하지 않는다.
7. `src/comic_new/server.py:110-154, 790-904, 929-953`
   - submit/readback DTO 의미를 분리하고 sparse Baseline 및 job identity를 wire에 보존한다. 기존 400/409 mapping은 유지한다.
8. `frontend/src/api/contracts.ts:26-40, 68-100, 154-173, 428-478`
   - prompt origin/job identity/schema v5 runtime contract를 반영한다.
9. `frontend/src/store/studio.ts:350-427, 537-570`
   - Baseline save가 실제 accepted response 여부를 반환하게 한다.
10. `frontend/src/components/baseline/RebaselineDialog.vue:56-75, 111-116`
    - save 완료 전 dialog 유지, pending 중복 방지, 실패 시 draft 유지.
11. `tests/test_generation.py:100-228` 및 BLOCK-06 CAS/STOP 구간
    - default command model, frozen stdin/job identity, single-cut isolation, CAS/STOP 회귀를 확장한다.
12. `tests/test_transactional_core.py:233-299, 447-516, 727-762`
    - sparse approval/default/origin, atomic revoke, partial completion/release block을 확장한다.
13. `tests/test_server.py:139-189`
    - 실제 HTTP sparse Baseline 200/fresh snapshot과 single generation response identity를 검증한다.
14. `frontend/tests/store.test.ts:193-245`
    - pending/failed save가 dialog-compatible false를 반환하고 draft를 유지하며 성공만 true/clear하는 동작을 검증한다.

## 6. 구현 순서와 원자적 cutover

1. §7의 legacy job attribution 조건을 먼저 판별한다.
2. schema v5/migration/verification과 store job identity를 먼저 구현한다. 이 시점의 branch는 아직 실행 가능한 중간 배포로 취급하지 않는다.
3. parser/resolver/Baseline approval을 변경하고 snapshot projection을 연결한다.
4. runner command와 provider stdin이 frozen job input만 소비하도록 전환한다.
5. server/frontend contracts를 schema v5에 맞춰 같은 change set에서 갱신한다. v4/v5 이중 wire contract나 compatibility alias는 두지 않는다.
6. dialog await 동작을 연결한다.
7. focused tests와 disposable smoke를 실행한 뒤 production static을 재build한다. source와 stale static bundle이 공존한 상태를 검증 대상으로 넘기지 않는다.

어느 단계에서도 부분 schema가 실제 server에 노출되어서는 안 된다. migration/verification 실패 시 기존 DB transaction은 rollback하고 server preflight가 열리지 않아야 한다. 이미 승인된 Baseline, intent history, canonical assets와 authorization history를 삭제하거나 재작성하지 않는다.

## 7. Conditional First Work

### CF-1 — legacy generation job의 model attribution

- `plan_anchor`: `PLAN-001 §4.2`
- `permitted_initial_work`: 구현 시작 전 disposable copy 또는 read-only SQL로 실제 대상 v4 DB의 `generation_jobs` 수, status, 관련 intent payload와 기존 provider provenance column/attempt detail 존재 여부를 조회한다. source DB를 변경하지 않는다.
- `discriminating_observation`: (a) 기존 job이 0건이면 v4→v5 migration은 column 추가 후 제약 검증으로 진행 가능하다. (b) 모든 기존 job의 model/effective prompt/origin을 권위 자료에서 결정적으로 복원할 수 있으면 그 source와 mapping을 migration test에 고정한다. (c) 하나라도 model을 추측해야 하면 refuted다.
- `dependent_work_not_yet_permitted`: 관찰 전 migration에 임의 default model을 historical job에 backfill하거나 schema version을 5로 올리는 작업.
- `response_if_refuted`: historical identity 의미를 Plan이 임의 결정하지 않는다. 해당 migration 방법을 중단하고 Main에게 current Scope/transition 호환성 결정을 반환한 뒤 Plan revision 및 fresh independent review를 받는다. 새 프로젝트 경로의 독립적 source edit은 하되 v5 배포/검증 대상으로 넘기지 않는다.

### CF-2 — 실제 live provider 경계

- `plan_anchor`: `PLAN-001 §4.4, §9.1`
- `permitted_initial_work`: 구현 후 사용자가 허용한 로컬 환경에서 default runner로 한 컷을 enqueue하여 ima2 child argv/stdin과 job/attempt readback을 관찰한다. 외부 게시나 unrelated model 호출은 하지 않는다.
- `discriminating_observation`: argv model과 stored job model이 모두 `oauth/gpt-image-2.5-flare`, stdin SHA-256이 job `effective_prompt_sha256`과 일치하며 provider가 empty stdin을 받지 않는다. 성공 시 candidate가 동일 revision/sequence에 commit되거나, provider 실패 시 해당 job만 failed이고 identity는 그대로 남는다.
- `dependent_work_not_yet_permitted`: source constant 또는 mock subprocess 통과만으로 Acceptance A/실제 live 연결 성공을 주장하는 것.
- `response_if_refuted`: fallback하지 말고 runner/provider integration의 실제 mismatch를 기록한다. command shape 문제면 Plan method revision 대상으로, 모델 availability/product 수단 문제면 Main/Thesis authority로 반환한다.

## 8. 집중 테스트 계획

### 8.1 `tests/test_transactional_core.py`

1. **Sparse approval matrix:** prompts가 all `""`, all whitespace, one authored/rest empty인 세 요청을 승인한다. fresh store를 다시 열어 ordered 1..5, 각 desired revision, authored prompt 보존, default exact string, `user`/`intelligent_default` origin, empty dialogue 보존을 검사한다.
2. **구조 오류 분리:** prompt empty는 성공하지만 prompt non-string, dialogue non-string, missing/duplicate cut structure는 rollback되는지 검사한다.
3. **target-only enqueue:** cut 1 authored/default prompt가 유효하고 다른 cut payload를 controlled direct fixture로 invalid empty로 만들었을 때 `cut_id=1`만 성공한다. 다른 컷 sequence/job은 변하지 않는다. 해당 invalid 컷 직접 enqueue는 `ValidationError`, job 0건, sequence/authority/authorization 변화 0건이어야 한다.
4. **bulk honesty:** 같은 상태에서 enqueue-all은 한 컷도 만들지 않는 all-or-nothing failure다.
5. **atomic revocation:** 성공한 single enqueue는 sequence/job insert와 같은 revision에서 prior active authorization을 revoke한다. 실패한 enqueue는 authorization을 유지한다.
6. **partial completion/release:** cut 1만 Current여도 aggregate `UNRESOLVED`; materialize/register/authorize 경계는 다른 컷 미실현 때문에 계속 실패한다.
7. **migration:** empty-job v4와 attribution 가능한 fixture가 v5로 원자 전환되고 재open/verify가 통과한다. attribution 불가능 fixture는 원본 user_version/data를 유지한 채 명확히 실패한다.

### 8.2 `tests/test_generation.py`

1. `default_provider_cmd()` argv의 정확한 `--model oauth/gpt-image-2.5-flare` 및 `nano-banana-pro` 부재를 검사한다.
2. single-cut sparse Baseline에서 cut 1만 enqueue/run한다. mock provider stdin은 job의 effective prompt와 byte-equal, SHA-256 equal이어야 하며 cut 2..5 job/attempt가 없어야 한다.
3. enqueue 후 same cut intent가 바뀌거나 DB current intent가 달라져도 이미 queued job은 stale CAS로 provider spawn 전에 superseded되며 frozen prompt가 새 intent로 바뀌지 않는다.
4. 같은 revision 두 요청의 request sequence 경쟁, cancel, global STOP, post-STOP candidate를 기존 BLOCK-06 tests로 재실행하여 새 identity columns가 commit eligibility를 우회하지 않음을 확인한다.
5. provider failure에서 다른 model command가 실행되지 않고 해당 job만 failed, 기존 canonical realization/다른 컷 상태가 유지된다.

### 8.3 HTTP/frontend 집중 검증

- `tests/test_server.py`: 실제 `POST /api/baselines`에 empty/whitespace prompts를 보내 200, accepted mutation id, default/origin이 포함된 fresh snapshot을 확인한다. 이어 `POST /api/generation/jobs` cut 1만 요청해 model/effective prompt/origin/hash/revision/sequence를 response와 fresh GET에서 대조한다. invalid target은 400이며 runner wake/provider attempt가 없어야 한다.
- `frontend/tests/store.test.ts`: pending save 동안 Promise가 settle되지 않고 draft가 유지되는지, 400/409/5xx/network failure에서 false와 draft/error 보존, 성공에서 true와 accepted snapshot/draft clear를 검사한다. component test harness가 없으면 RebaselineDialog를 mount하는 최소 기존 Vitest 방식으로 “pending/실패에는 open, 성공에만 close”라는 사용자 관찰 계약을 추가한다.
- 기존 frontend snapshot fixture를 schema v5 및 required origin/job fields로 일괄 갱신한다. optional/default로 validator를 우회하지 않는다.

## 9. 구현자 Self-check와 최종 Acceptance Readback

### 9.1 최소 실제 경로

1. disposable project를 생성하고 실제 server를 production static과 함께 기동한다.
2. browser 또는 HTTP+실제 UI에서 source brief/role/beat를 두고 모든 prompt를 비워 Baseline 승인한다.
3. 응답 전 dialog가 열려 있고, 성공 후 닫히며, fresh `GET /api/studio/snapshot`의 다섯 prompt/default/origin이 요청 구조와 일치하는지 확인한다.
4. cut 1만 generation 요청한다. DB/fresh snapshot에서 오직 한 job이 있고 model, effective prompt, origin, hash, desired revision, 신규 request sequence가 일치하는지 확인한다.
5. 허용된 live ima2 경계에서 child argv/stdin을 대조한다. mock 결과를 live availability 증거로 대체하지 않는다.
6. cut 1 성공 시 cut 1만 Current, cut 2..5 Stale, aggregate `UNRESOLVED`인지 확인한다.
7. review materialize/authorize/export/Blogger API가 partial active set에서 차단되는지 확인한다. 실 Blogger 게시를 시도하지 않는다.
8. 한 job을 provider pre-commit 경계에서 STOP하여 late candidate가 canonical asset을 바꾸지 못하는지 확인한다.

### 9.2 Acceptance 매핑

- **A. Live Image Model Default 결속:** §4.2, §4.4, §8.2, §9.1 step 4–5. Source string만이 아니라 stored job identity와 실제 ima2 argv를 대조한다.
- **B. Sparse Baseline Approval 허용:** §4.1, §4.3, §4.5, §8.1/8.3, §9.1 step 2–3. HTTP 200과 fresh snapshot이 판정 경계다.
- **C. 단일 컷 탐색 생성 및 미준비 컷 격리:** §4.2, §8.1/8.2, §9.1 step 4–6. 다른 컷 job 0건과 aggregate `UNRESOLVED`를 함께 읽는다.
- **D. Enqueue strict validation:** §4.1–4.2, §8.1/8.3. 해당 cut만 400/ValidationError, transaction side effect 0건, provider attempt 0건을 확인한다.
- **E. 4대 인과 불변식 및 release 보존:** §2, §6, §8.1/8.2, §9.1 step 6–8. 기존 CAS/STOP/revoke/readback tests와 실제 partial-release block을 모두 요구한다.

### 9.3 최종 검증 및 cleanup

- focused backend: 관련 `tests/test_transactional_core.py`, `tests/test_generation.py`, `tests/test_server.py` 시나리오.
- focused frontend: `frontend/tests/store.test.ts`, type contract check, production Vite build.
- main integration owner가 최종 stable target에서 전체 backend/frontend suite를 한 번 실행한다.
- disposable server/browser/provider를 종료하고 process tree, `.generation-staging`, 임시 DB/static output을 정리한다. repository에 throwaway script를 남기지 않는다.
- Scope/Thesis/Baseline/Plan 및 stable implementation target의 bytes를 다시 hash하여 verifier handoff currentness를 고정한다.

테스트 통과만으로 BLOCK-10 성공을 선언하지 않는다. authoritative success는 fresh Baseline snapshot, stored generation job identity, 실제 provider request 경계, cut currency/aggregate completion, release block을 연결한 readback이다.

## 10. 실패·중단·재개 경계

- Baseline validation/DB 실패: transaction rollback, 기존 active Baseline/intent/canonical bytes 보존, frontend dialog/draft 유지.
- enqueue validation 실패: job/attempt/sequence/authority revision/authorization에 변화가 없어야 하며 다른 컷 작업은 계속 가능하다.
- provider 실패: 대상 job만 failed; model fallback 없음; 기존 canonical realization과 다른 컷은 불변이다.
- interruption/restart: frozen job input은 DB에 남고 running orphan은 기존 recovery대로 interrupted/commit-ineligible가 된다. 자동 성공/자동 재생성하지 않는다.
- late/duplicate result: current desired revision와 latest sequence가 다르면 기존 supersede/commit CAS가 차단한다.
- schema migration 실패: transaction rollback 후 preflight 실패; 부분 v5를 current로 열지 않는다.
- UI save 실패: local draft를 보존하고 명시적 수정/재시도만 허용한다. 성공 전 dialog close나 자동 재전송을 하지 않는다.

## 11. 구현 재량과 재검토 반환 조건

구현자는 helper 이름, 상수 위치, equivalent SQL statement ordering처럼 관찰 계약을 바꾸지 않는 내부 선택을 할 수 있다. 다음은 material method 변경이므로 영향을 받은 작업을 멈추고 Plan revision 및 fresh independent Plan Review를 받아야 한다.

- job input을 enqueue가 아닌 claim/run 시점에 resolve하는 설계;
- job model/prompt/origin/hash를 durable authority 밖에 두는 설계;
- historical jobs에 근거 없는 model을 backfill하는 migration;
- Baseline empty prompt를 그대로 저장하면서 fallback을 UI에서만 꾸미는 설계;
- single enqueue에서 다른 컷 eligibility를 검사하거나 bulk invalid cut을 silent skip하는 설계;
- schema v4/v5 또는 old/new job identity를 동시에 권위로 유지하는 compatibility shim;
- 실패 model을 `nano-banana-pro` 또는 다른 model로 묵시 fallback하는 설계.

제품 의미, BLOCK-10 geography, fallback/origin 정책, Scope Acceptance 자체를 바꿔야 한다면 Plan이 아니라 Main이 Thesis/Baseline/Scope 소유 경계로 돌아간다.

## 12. 독립 검토 및 시작 경계

이 문서는 실행 방법이며 구현·검증·완료 판정이 아니다. exact Scope/Plan bytes에 대해 독립 Plan Reviewer가 모든 Acceptance, migration 조건, identity/readback, 네 불변식과 partial-release 반례를 검토해 `ADMIT`한 후에만 §6의 구현을 시작한다. `REVISE` 또는 `EVIDENCE_NEEDED`이면 그 finding의 owner가 해결하기 전 dependent mutation을 시작하지 않는다. 최종 Scope `done`은 구현자 self-check가 아니라 별도 semantic verification과 Coverage 후 Main만 기록한다.
