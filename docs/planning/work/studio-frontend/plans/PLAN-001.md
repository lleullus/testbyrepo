# PLAN-001 — BLOCK-04 Studio Shell & Vue 3 Frontend 실행 방법

- Plan role: exact ready Scope의 구현·자기점검 방법. 제품 의미나 Acceptance를 추가하지 않는다.
- Project Root: `/home/user01/project/comic_new`
- Scope: `/home/user01/project/comic_new/docs/planning/work/studio-frontend/SCOPE.md`
- Selected transition: `BASELINE-001`의 `BLOCK-04`만
- Prepared against commit: `91f3fa7d968855bd87a5ee3d9953cbd6c928b738`
- Prepared working tree: 이 revision 전 `git status --short` 출력 없음. Main의 CFW scratch는 repository 밖 `/home/user01/tmp/comic-new-block04-cfw/`에만 있으며 이 Plan 외 제품/source/config 상태를 바꾸지 않았다.
- Repository investigation: None supplied; 아래 current source 직접 판독을 사용했다.
- Remote retrieval: 0회
- Visual concept/image generation: 생략. 이 표면은 새 마케팅/브랜드 페이지가 아니라 기존에 방향이 확정된 D4 반복 작업용 creative workstation이며, 사용자 지시와 `디자인` 스킬의 `IMAGE_GEN_TRIGGER = EXPLICIT_ONLY`에 따라 concept image는 부적절하다.

## 1. 결속 권위, 현재 바이트와 진입 조건

### 1.1 원본과 해시

| 분류 | 원본 | 실제 SHA-256 | 적용 범위 |
|---|---|---|---|
| Product Authority | `docs/planning/product-thesis/web-comic-studio/THESIS-001.md` (`THESIS-001`) | `74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63` | 유일한 제품 의미, 5-Truth Chain, INV-1~8, §6 UI 정책, §7 거짓 성공, §8 readback |
| Scope | `docs/planning/work/studio-frontend/SCOPE.md` | `ccc4764cbd8f1df949dd16572853e325016536614af8d6c2eb43cd02ffdc9635` | ready BLOCK-04 Outcome, Acceptance A-J, External Conditions/Non-Goals |
| Transition Authority | `docs/planning/adaptive/BASELINE-001.md` | `5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c` | selected `BLOCK-04`, Exit 1-44, 모든 적용 INV/PATH, Safe Continuation |
| Derived frontend projection | `docs/planning/frontend-architecture/FRONTEND-ARCH-001.md` | `8eea9545d82b40e64791cd0d6b3340e848b72923d36373bae6425cc39badac9b` | 구현 구조만. Thesis와 충돌하면 Thesis 우선; nudge는 `0.5%`, Shift `2.0%` |

Canonical validator 실행:

```text
python3 skill://scope-shaper/tools/validate_scope.py --json /home/user01/project/comic_new/docs/planning/work/studio-frontend/SCOPE.md
=> schema iis-scope/v1, status ready,
   product_authorities = THESIS-001 위 해시,
   transition_authorities = BASELINE-001 위 해시
```

독립 Plan Review 시작 전과 구현 handoff 직전에 네 원본 해시와 Scope `Status: ready`를 다시 비교한다. 해시 변화는 자동 승인/거절이 아니라 이 방법의 currentness를 중단하고 해당 변경 소유자에게 재검토시키는 신호다.

### 1.2 이 Plan이 얻어야 할 결과와 넘지 않을 경계

한 disposable 실제 프로젝트 SQLite를 여는 `comic-new serve` 한 Python 프로세스가 generated production Vue studio와 같은-origin API/SSE를 제공한다. 사용자는 exactly-five baseline/intent/realization/composition/job/artifact truth를 보고, local draft와 authoritative state를 혼동하지 않으며, 저장·생성·취소·STOP·canonical artifact 검토와 화면에 표시된 exact artifact identity/hash의 실제 승인 요청을 수행한다.

이 결과는 BLOCK-04일 뿐이다. `TransactionalStore.authorize_release(...)`를 실제 호출하는 승인 endpoint는 만들지만, authorization row의 restart 보존, receiver-visible 변경과 동시인 revocation closure, export/PNG, Blogger, destination readback 및 delivery 판정은 이 Plan의 성공 증거가 아니다. 그 판정은 BLOCK-05에 남긴다. 승인 HTTP 2xx나 screenshot을 delivery/제품 완료로 부르지 않는다.

## 2. Grounding ledger

### 2.1 EXISTING — 현재 실제 권위와 인터페이스

1. **단일 DB 권위와 snapshot** — `src/comic_new/store.py:67-117,288-545`
   - `TransactionalStore`는 `comic-new.sqlite3`, schema v2, exactly-five trigger/index를 검증한다.
   - `_begin_mutation`은 `authority_revision` CAS를 수행한다.
   - `snapshot()`은 한 deferred transaction에서 `authority_revision`, baseline, ordered cuts, revision-equality 기반 currency/realization completeness, composition, jobs/attempts/process identity, review artifacts/closures, active/revoked authorization, delivery attempts, generation control을 읽는다.
   - 이것이 API와 SSE의 유일한 domain source다. 서버의 메모리나 브라우저 상태를 snapshot 대신 읽는 경로를 만들지 않는다.

2. **프로젝트 생성/재개** — `src/comic_new/store.py:117-287`, `src/comic_new/schema.sql:1-179`, `src/comic_new/migrations/v1_to_v2.sql:1-28`
   - `create_project`는 temp DB를 원자 승격하고 cuts 1..5를 seed한다. `open_project`는 migration/schema 검증 후 연다.
   - 현 schema에는 별도 source-brief mutable table이나 event log가 없다. 이 Scope에서는 추가하지 않는다.

3. **baseline/intent/composition의 기존 결정 writer** — `src/comic_new/store.py:546-698`
   - `approve_structural_baseline(expected_authority_revision, baseline_id, structure, intents_by_cut)`은 exact 1..5 intent를 한 transaction으로 새 baseline에 결속한다.
   - `accept_cut_intent(...)`는 현재 baseline을 유지하며 해당 cut의 desired revision만 증가시킨다.
   - `accept_composition(expected_authority_revision, expected_composition_revision, state)`은 `normalize_state` 후 composition revision을 증가시킨다.
   - 세 writer 모두 기존 active authorization을 같은 transaction에서 revoke한다. BLOCK-04는 이를 우회하거나 복제하지 않는다.

4. **canonical composition schema** — `src/comic_new/composition.py:17-23,105-220`
   - surface는 `1024×7680`, exactly five, schema v1이다.
   - state의 유일한 top-level key는 `schema_version`, `gap_px`, `font_sha256`, `bubbles`다.
   - bubble wire field는 `bubble_id`, `cut_id`, `shape`, `x_pct/y_pct/w_pct/h_pct`, `text`, `font_size_pct`, `line_spacing_pct`, `text_align`, `text_rgba/fill_rgba/outline_rgba`, `outline_width_pct`, `padding_pct`다. 범위/shape/color/unknown-key 검증은 이 existing normalizer가 최종 소유한다.

5. **통합 queue/runner/실제 process-tree STOP** — `src/comic_new/store.py:699-1247`, `src/comic_new/generation.py:318-436,440-831`
   - `GenerationService.enqueue/cancel/stop_all`은 기존 queue와 process identity를 사용한다.
   - `GenerationRunner.run_until_idle`은 runner ownership과 orphan reconciliation 후 fixed concurrency 2 worker를 구동한다.
   - child는 `start_new_session=True`; PID/start token/process group 기반 TERM→KILL settlement 후에만 cancelled/interrupted row를 기록한다.
   - job success만으로 Current가 되지 않으며 `commit_candidate`의 commit-time desired revision gate가 realization을 결정한다.

6. **canonical review artifact** — `src/comic_new/composition_service.py:53-485`, `src/comic_new/composition.py:345-613`, `src/comic_new/store.py:1248-1319`
   - `CompositionService.materialize(expected_authority_revision, expected_composition_revision)`은 exactly-five Current와 source byte/hash를 preflight하고 PIL로 immutable PNG를 생성·등록·fresh-readback한다.
   - `read_artifact`는 DB registration을 먼저 읽고 file hash, PNG decode/size/mode/embedded closure를 재검증한다.

7. **실제 승인 writer** — `src/comic_new/store.py:1321-1391`
   - `authorize_release(expected_authority_revision, authorization_id, artifact_id, content_hash)`은 hash, current composition revision, exact-five Current와 artifact cut closure를 다시 검증하고 실제 authorization row를 기록한다.
   - BLOCK-04 approval endpoint가 호출할 유일한 writer다. 별도 boolean/no-op/“요청 받음” shadow를 두지 않는다.

8. **현재 CLI/package** — `src/comic_new/cli.py:22-161`, `pyproject.toml:1-21`
   - CLI에는 `init`, `snapshot`, `generate`, `run-generation`, `cancel-generation`, `stop-generation`만 있고 `serve`는 없다.
   - runtime dependency는 `Pillow>=10.0.0`, package data는 schema/migrations뿐이다.
   - 현재 `frontend/`, `src/comic_new/static/`, FastAPI app/static serve 구현은 실제로 없다.

9. **현재 환경과 CFW-1 frontend 조합 관찰**
   - Python `3.12.3`, Bun `1.3.14`, Node `v24.18.0`, npm `12.0.2`, Pillow `12.2.0`.
   - Main이 repository 밖 `/home/user01/tmp/comic-new-block04-cfw/frontend`에서 unbounded `latest`를 해석했을 때 Vue `3.5.42`, Pinia `4.0.3`, Vite `8.3.0`, `@vitejs/plugin-vue 6.0.9`, `vue-tsc 3.3.11`, TypeScript `7.0.2`가 설치됐지만 `vue-tsc --noEmit`은 `ERR_PACKAGE_PATH_NOT_EXPORTED`, TypeScript subpath `./lib/tsc`로 실패했다. 따라서 `latest` 호환성 premise는 refuted다.
   - 같은 scratch에서 TypeScript만 `5.9.3`으로 포함한 exact six-package pin(Vue `3.5.42`, Pinia `4.0.3`, Vite `8.3.0`, `@vitejs/plugin-vue 6.0.9`, `vue-tsc 3.3.11`, TypeScript `5.9.3`)은 `vue-tsc --noEmit`과 Vite production build exit `0`, 21 modules, hashed JS+CSS를 관찰했다. 두 번째 `bun install --frozen-lockfile`도 변경 없이 성공했다.
   - evidence bytes: `package.json` `cda5badd0671ac66b5751a0cf685245257b234aadae4591297a3ce9a73150914`; `bun.lock` `b117914b5ad612aac5ed7a56fc89ed19750477fba1fd0727638f5c93666d94db`; `dist/index.html` `aa2fa1592054fbec3712bb102b4239e5b99e428b763af9b9dede5a0db3d3cfbd`; `dist/assets/index-BwUgsyUe.css` `7726cec509bcd47f9b96f3b184700bdccd481e5adfd86259161f4f3f501a1f3b`; `dist/assets/index-6xL9AdZ1.js` `4c0274c73e777a3d727aca5bf3de3f6b04e4c7d1c83f7046c9856dde37554fcf`.

10. **CFW-2 Python resolver/import 관찰**
   - Main이 repository 밖 isolated venv `/home/user01/tmp/comic-new-block04-cfw/venv`에 `fastapi==0.136.3`와 `uvicorn==0.48.0`을 exact install했고 resolver/install과 import가 성공했다. import readback은 FastAPI `0.136.3`, uvicorn `0.48.0`; observed transitive versions는 Starlette `1.6.0`, Pydantic `2.13.5`다.
   - 이는 exact direct pins의 Python 3.12 resolver/import support만 세운다. 현재 제품에는 app factory/lifespan/static serve가 없으므로 실제 app startup, missing-static refusal, stream response, graceful shutdown을 증명하지 않는다.
   - 현재 interpreter에서 `wheel` Python distribution은 발견되지 않았다. 이는 wheel 생성 불가능의 단정이 아니라 CFW-3 대상이다.

### 2.2 PROPOSED — 최소 새 경계

- `src/comic_new/server.py` 하나가 FastAPI app factory, DTO 변환/route, lifespan, static/artifact byte serving, one runner supervisor와 SSE snapshot broadcaster를 직접 소유한다. repository/service/controller 계층을 추가하지 않는다.
- API mutation은 위 existing store/service를 호출하고 곧바로 fresh `store.snapshot()`을 반환한다. DTO projection은 filesystem path를 same-origin URL로 바꾸는 read-only 변환이며 mutable truth가 아니다.
- SSE는 full authoritative `StudioSnapshotDTO`만 전송한다. bounded in-memory replay ring은 전송 편의일 뿐 domain event store가 아니며, GET snapshot·currency·queue·approval 판정에 사용하지 않는다.
- Vue는 `useStudioStore` 하나만 domain transition을 소유한다. pointer gesture의 transient rect만 component-local이다.
- `frontend/**`는 source, `src/comic_new/static/**`는 reproducible Vite output이자 Python package data다.

### 2.3 UNRESOLVED — 구현/통합에서 남은 실제 관찰

1. CFW-3: setuptools wheel 조립이 generated nested static assets와 frontend source/lock을 의도대로 포함·제외하고 installed package가 이를 실제 serve하는지는 아직 증명되지 않았다.
2. CFW-4: canonical materialization proof에 쓸 font file의 exact bytes/path/hash는 disposable verification project를 만들 때 선택해야 한다. 임의 fallback font로 성공을 추정하지 않는다.
3. CFW-1은 exact dependency 조합의 빈 strict app support를 세웠지만 제품 `frontend/**` 전체의 fresh `bun install --frozen-lockfile`, `vue-tsc --noEmit`, production build와 `src/comic_new/static/**` 출력은 아직 없다. scratch output은 product build/Acceptance 증거가 아니다.
4. CFW-2는 exact resolver/import support를 세웠지만 아직 존재하지 않는 실제 product app의 startup/lifespan, missing-static negative, SSE/stream response, runner shutdown settlement은 구현 자기점검에서 관찰해야 한다.

CFW-1/2의 지원 관찰과 CFW-3/4의 완전한 bundle은 §11에 있다. 그 밖의 endpoint/state/interaction 의미는 Scope와 existing interface로 결정되어 있어 구현자 재협상 대상이 아니다.

## 3. 고정 wire contract

### 3.1 공통 규칙

- JSON UTF-8, same origin, `/api` prefix. CORS, GraphQL, WebSocket, Axios, query cache를 추가하지 않는다.
- success는 endpoint별 DTO를 직접 반환한다. error만 아래 한 shape를 사용한다.
- baseline/rebaseline, 모든 cut-intent save, composition save는 모두 관찰한 SQLite global `expected_authority_revision`을 보내고 §5의 client authoritative edit lane 하나를 공유한다. composition은 `expected_composition_revision`도 보낸다.
- 이 edit mutation들의 `mutation_id`는 client save correlation이지 DB authority가 아니다. 서버가 그대로 echo하되 snapshot/readback 대신 사용하지 않는다.
- integer cut identity는 `1|2|3|4|5`; add/delete/reindex DTO는 존재하지 않는다.

```ts
type Sha256 = string // wire validator: lowercase 64-hex
type CutId = 1 | 2 | 3 | 4 | 5
type JobStatus = 'queued'|'running'|'succeeded'|'failed'|'cancelled'|'interrupted'|'superseded'
type DeliveryOutcome = 'unknown'|'confirmed_success'|'confirmed_failure'

interface ApiErrorDTO {
  error: {
    code: 'validation_error'|'conflict'|'not_found'|'realization_incomplete'|
          'artifact_not_current'|'runner_busy'|'process_settlement_failed'|'internal_error'
    message: string
    expected_revision?: number
    actual_revision?: number
    current_snapshot?: StudioSnapshotDTO
  }
}
```

Status mapping: malformed/schema validation `422 validation_error`; domain validation `400 validation_error`; missing artifact/job `404`; CAS conflict `409 conflict` plus fresh snapshot; stale closure/artifact `409 artifact_not_current` plus fresh snapshot; incomplete review precondition `409 realization_incomplete`; runner ownership conflict `409 runner_busy`; STOP/cancel process settlement failure `503 process_settlement_failed`; uncaught I/O/SQLite/internal error `500 internal_error` with no traceback/path leakage. Client logic branches on `code`, never localized `message`.

### 3.2 Snapshot DTO

`GET /api/studio/snapshot -> StudioSnapshotDTO` is initial load, conflict and gap recovery readback.

```ts
interface StudioSnapshotDTO {
  schema_version: 2
  authority_revision: number
  baseline: null | {
    baseline_id: string
    structure: BaselineStructureDTO
    authority_revision: number
    created_at: string
    intents: Array<{cut_id: CutId; intent_revision: number}>
  }
  cuts: [CutDTO, CutDTO, CutDTO, CutDTO, CutDTO]
  realization_complete: {complete: boolean; status: 'COMPLETE'|'UNRESOLVED'}
  composition: {revision: number; state: CompositionStateDTO|null; updated_at: string}
  render_contract: {width:1024; height:7680; default_composition:CompositionStateDTO}
  jobs: JobDTO[]
  review_artifacts: ReviewArtifactSummaryDTO[]
  release_authorization: {active: AuthorizationDTO|null; history: AuthorizationDTO[]}
  delivery_attempts: Array<{attempt_id:string; kind:'png'|'blogger'; authorization_id:string;
    artifact_id:string; request_id:string; outcome:DeliveryOutcome; destination_id:string|null;
    destination_url:string|null; evidence:unknown|null; observed_authority_revision:number|null;
    created_at:string; updated_at:string}>
  generation_control: {stop_epoch:number; runner_id:string|null; runner_pid:number|null;
    runner_start_token:string|null; runner_started_at:string|null}
}

interface CutDTO {
  cut_id: CutId
  desired_revision: number|null
  effective_intent: CutIntentDTO|null
  realized_revision: number|null
  realized_asset_id: string|null
  realized_content_hash: Sha256|null
  realized_asset_url: string|null
  currency: 'CURRENT'|'STALE'
}
interface JobDTO {
  job_id:string; cut_id:CutId; target_desired_revision:number; status:JobStatus;
  terminal_detail:string|null; created_at:string; updated_at:string
  attempts:Array<{attempt_id:string; ordinal:number; status:string; started_at:string;
    finished_at:string|null; detail:string|null; provider_request_id:string|null}>
}
interface ReviewArtifactSummaryDTO {
  artifact_id:string; content_hash:Sha256; composition_revision:number; created_at:string
  cuts:[{cut_id:CutId; realized_revision:number; asset_id:string}, ...]
  asset_url:string
}
interface ReviewArtifactDTO extends ReviewArtifactSummaryDTO {
  cuts:[{cut_id:CutId; desired_revision:number; realized_revision:number;
    asset_id:string; source_content_hash:Sha256}, ...]
}
```

Transport DTO omits `realized_asset_path`, process PID/group/start token, staging path and runner internals from browser payload except the summary generation-control fields shown above. Server still uses complete existing snapshot internally; omission is not a second truth. `realized_asset_url` and artifact `asset_url` are deterministic projections of existing identities.

Existing 새 프로젝트의 `composition.state`는 revision 0에서 `{}` sentinel이다. DTO projection은 이 exact 경우만 `state:null`로 표현하고, 다른 비정상 state는 숨기지 않고 internal error로 실패시킨다. `render_contract.default_composition`은 configured font bytes의 hash, `schema_version:1`, `gap_px:24`, empty bubbles를 담는 초기 입력 제안일 뿐 authority가 아니다. 사용자가 첫 composition을 저장해 PUT이 수용된 뒤에만 snapshot `state`가 authoritative `CompositionStateDTO`가 된다.

```ts
interface BaselineStructureDTO {
  source_brief: string
  cuts: [
    {cut_id:1; role:string; beat:string}, {cut_id:2; role:string; beat:string},
    {cut_id:3; role:string; beat:string}, {cut_id:4; role:string; beat:string},
    {cut_id:5; role:string; beat:string}
  ]
}
interface CutIntentDTO { prompt:string; dialogue:string }
interface CompositionStateDTO {
  schema_version:1; gap_px:number; font_sha256:Sha256; bubbles:BubbleDTO[]
}
```

`BubbleDTO`는 §2.1.4의 existing exact schema와 동일하다. API가 별도 relaxed schema를 만들지 않고 `normalize_state`에서 최종 검증한다.

Materialization/read response의 richer `ReviewArtifactDTO.cuts`는 `CompositionService.read_artifact`가 이미 검증한 PNG embedded closure에서 읽는다. Snapshot의 summary나 현재 cut으로 과거 artifact의 desired/source identity를 재구성하지 않는다.

### 3.3 Mutation/read endpoints와 의미

1. `POST /api/baselines`
   - request: `{expected_authority_revision, mutation_id, baseline_id, structure:BaselineStructureDTO, intents:[{cut_id, intent:CutIntentDTO} × exact 5]}`.
   - 새 프로젝트에서는 explicit 1차 승인, 기존 baseline에서는 ReviewModal과 별도인 consequential `RebaselineDialog` 확인 뒤 호출한다.
   - server는 array를 exact key 1..5 dict로 바꾸고 기존 `approve_structural_baseline` 한 번만 호출한다. success는 `{accepted_mutation_id, snapshot}`.
   - approved baseline 뒤 Source Brief 편집은 store의 `baselineDraft.structure.source_brief`에 “현재 작품에 반영 안 됨”으로 남고 current intent/composition/release를 바꾸지 않는다. 반영 action은 이 endpoint의 explicit Re-baseline뿐이다. 별도 source-brief authority/table/localStorage를 만들지 않는다.
   - baseline 수용은 composition을 암묵 초기화하지 않는다. `composition.state:null`이면 UI가 `render_contract.default_composition`으로 같은 `PUT /api/composition`을 명시적으로 실행하고, 그 실제 acceptance 전에는 Canvas를 saved/ready로 표시하지 않는다.
2. `POST /api/cuts/{cut_id}/intent`
   - request: `{expected_authority_revision, mutation_id, intent:CutIntentDTO}`.
   - 기존 `accept_cut_intent` 호출; baseline은 유지되고 해당 desired revision만 증가한다. old realization URL/bytes는 남고 snapshot equality가 STALE를 결정한다.
   - response: `{accepted_mutation_id, snapshot}`. Browser draft clear는 id가 현재 draft와 같을 때만 한다.

3. `PUT /api/composition`
   - request: `{expected_authority_revision, expected_composition_revision, mutation_id, state:CompositionStateDTO}`.
   - full-state serializer 출력만 받고 `accept_composition`을 호출한다. response `{accepted_mutation_id, snapshot}`.
   - 서버는 client patch merge를 하지 않는다. 한 full normalized state와 existing CAS가 결정한다.

4. `POST /api/generation/jobs`
   - request: `{expected_authority_revision, cut_id:CutId|null}`; null은 exact five jobs, 값은 one job.
   - `GenerationService.enqueue` 후 one server runner supervisor를 wake한다. response `{jobs, snapshot}`.

5. `POST /api/generation/jobs/{job_id}/stop`
   - confirmation 없이 `GenerationService.cancel` 실행. response `{receipt, snapshot}`은 실제 termination/DB update 후에만 온다.
   - 브라우저는 request start 때 해당 job에 ephemeral `stopRequested=true`만 두고 response/SSE snapshot의 terminal status 전에는 terminal을 만들지 않는다.

6. `POST /api/generation/stop`
   - body 없음. `GenerationService.stop_all`; 실제 process tree settlement 실패는 503, 성공은 `{receipt, snapshot}`.
   - accepted desired intent/currency/release/delivery를 수정하지 않는다.

7. `POST /api/review-artifacts`
   - request: `{expected_authority_revision, expected_composition_revision}`.
   - `CompositionService.materialize` 호출 후 `{artifact:ReviewArtifactDTO, snapshot}`. unsaved gate는 client convenience이며 server의 exactly-five/current/CAS가 최종 gate다.

8. `GET /api/review-artifacts/{artifact_id}`
   - `CompositionService.read_artifact` 결과의 identity/closure metadata. bytes는 보내지 않는다.

9. `GET /api/review-artifacts/{artifact_id}/content`
   - 매 요청 `read_artifact`로 DB-first hash/decode를 검증한 exact PNG bytes를 `Content-Type: image/png`, strong `ETag: "<sha256>"`, `Cache-Control: public, max-age=31536000, immutable`로 보낸다. browser에서 bubble DOM을 합성하지 않는다.

10. `GET /api/cuts/{cut_id}/realization?asset_id=...&revision=...`
    - fresh snapshot의 cut tuple `(cut_id, realized_revision, realized_asset_id, realized_content_hash/path)`과 query identity가 모두 같은 경우에만 실제 bytes/hash/decode 후 PNG를 보낸다. path 입력을 받지 않는다.

11. `POST /api/review-artifacts/{artifact_id}/authorize`
    - request: `{expected_authority_revision, content_hash}`. URL artifact id, body full hash와 modal이 표시 중인 identity/hash가 같아야 한다.
    - server가 `authorization_id`를 생성하고 기존 `authorize_release(...)`를 실제 호출한 뒤 `{authorization_id, submitted_artifact_id, submitted_content_hash, snapshot}`을 반환한다.
    - 이 endpoint는 no-op handoff가 아니다. 그러나 BLOCK-04 proof는 captured request의 pre/effect identity와 exact displayed byte hash, 기존 call 실행까지만 기록한다. row durability/restart/revocation/release/delivery 판정은 하지 않는다.

Baseline/rebaseline·cut intent·composition만 §5의 edit draft/lane semantics를 가진다. Generation, review materialization, approval은 lane에 enqueue하거나 edit draft/mutation clear로 취급하지 않되, client는 fresh current snapshot과 `hasBlockingEdit == false`일 때만 호출한다. Global/per-job STOP은 이 gate와 lane을 우회해 pending edit가 있어도 즉시 요청한다.

### 3.4 SSE wire와 gap 규칙

`GET /api/events` 하나만 연다. response는 `text/event-stream`, buffering/cache를 끄고 heartbeat는 comment뿐이다.

```text
id: <boot_id>:<authority_revision>
event: studio.snapshot
data: {"schema":"studio-event/v1","boot_id":"...","authority_revision":17,"snapshot":{...}}

id: <boot_id>:<current_authority_revision>
event: snapshot-required
data: {"schema":"studio-event/v1","reason":"boot-changed|replay-miss|revision-gap","authority_revision":17}
```

- `authority_revision`이 유일한 domain monotonic key다. `boot_id`는 process-local replay identity일 뿐 domain truth가 아니다.
- server는 mutation route의 fresh snapshot과 runner 변화 감시에서 얻은 fresh snapshot을 publish한다. 같은 revision은 전송 ring에서 dedupe한다. 관찰 rev가 1보다 크게 뛰면 full snapshot을 ring에 넣되 subscriber에게 먼저 `snapshot-required`를 보내 client GET 1회를 강제한다.
- bounded replay ring 64개는 response replay만 위한 process-local cache다. SQLite writer/event log/query authority가 아니다. `Last-Event-ID`의 boot가 다르거나 ID가 ring에 없으면 `snapshot-required`다.
- client는 `studio.snapshot`을 `incoming.authority_revision > server.authority_revision`일 때만 server layer에 적용한다. equal/older는 무시한다. drafts/saves/gesture를 event로 clear하지 않는다.
- HTTP mutation response가 먼저 적용된 뒤 같은/older SSE가 도착하는 것이 natural duplicate/late case다. superseded/cancelled job의 late terminal snapshot은 job history만 갱신하고 cut realization tuple이 unchanged이면 Current를 만들지 않는다.
- `snapshot-required`는 concurrent duplicate 호출을 collapse하여 exactly one in-flight GET을 실행하고 server layer만 교체한다. EventSource `error`는 persistent reconnecting indicator만 만들며 queue/currency/terminal truth를 추정하지 않는다.

## 4. Python server, lifespan, runner와 single-serving

### 4.1 파일과 app 구조

Backend owner는 `src/comic_new/server.py`의 직접적인 `create_app(project_dir, font_path)`와 `serve(...)`만 만든다. FastAPI dependency-injection/repository/controller/event-bus 계층은 만들지 않는다. App state에는 opened `TransactionalStore`, existing three services, one `RunnerSupervisor`, one `SnapshotBroadcaster`만 둔다.

`comic-new serve <project_dir> --font <absolute-font-file> [--host 127.0.0.1] [--port 8000]`를 `cli.py`에 추가한다. CLI는 uvicorn 호출 전 다음을 순서대로 실패시킨다.

1. project open/schema 검증 실패;
2. font regular file/read 실패;
3. package-relative `src/comic_new/static/index.html` 부재;
4. index가 참조하는 `/assets/...` JS/CSS 파일 부재.

이 preflight 실패는 stderr 원인과 non-zero exit를 내며 socket을 열거나 empty HTML을 반환하지 않는다.

FastAPI는 `/assets`를 generated static directory에 mount하고 `GET /`만 `index.html`로 보낸다. client router/catch-all은 없으며 unknown non-API path는 404다. API, realization, artifact content도 같은 app/process/origin이다.

### 4.2 startup/run/shutdown settlement

Lifespan startup의 exact 순서:

1. preflight를 통과한 existing store/services를 app state에 결속;
2. initial fresh snapshot을 broadcaster ring에 넣음;
3. broadcaster SQLite revision monitor를 시작;
4. one runner supervisor thread를 시작한다. Startup 전 snapshot의 `running` job ID가 있으면 supervisor의 existing `GenerationRunner.run_until_idle()`이 그 orphan을 실제 terminate하고 authoritative terminal row로 바꿀 때까지 그 ID들에 한해 readiness를 보류한다. failure/timeout은 startup failure이고 old Running을 제공하지 않는다. Queued work drain은 readiness 뒤 background에서 계속할 수 있다;
5. orphan settlement의 fresh snapshot을 publish한 뒤 readiness를 허용.

Runner supervisor는 동시에 하나의 `GenerationRunner.run_until_idle()`만 호출한다. enqueue는 condition을 wake할 뿐 client-only queue나 두 번째 runner truth를 만들지 않는다. runner의 provider child process는 생성 중에만 허용되는 ancillary process이며 frontend production daemon이 아니다. queue UI에는 existing statuses만 표시하고 fake percent/ETA를 만들지 않는다.

Graceful shutdown의 exact 순서:

1. HTTP 신규 mutation을 거부하고 EventSource에 마지막 authoritative snapshot을 flush;
2. queued/running이 있을 때만 `GenerationService.stop_all()`을 worker thread에서 호출하여 stop epoch, queued cancellation, actual child process-tree termination과 terminal row를 완료;
3. runner supervisor에 close를 보내고 bounded join; 대상 child PID/process group이 남거나 runner가 settle하지 않으면 shutdown error/non-zero process 결과로 남기며 “종료됨”을 만들지 않음;
4. final fresh SQLite snapshot을 publish/기록한 후 SSE subscribers와 monitor를 닫음;
5. uvicorn process 종료.

강제 SIGKILL은 app이 cleanup을 주장할 수 없는 외부 interruption이다. 다음 start의 existing runner orphan reconciliation과 fresh snapshot이 authoritative recovery를 수행한다.

## 5. Frontend state machine과 authoritative edit lane

### 5.1 정확히 하나인 domain store

`frontend/src/store/studio.ts`의 `useStudioStore`만 아래 mutable domain/application state를 갖는다.

```ts
type EditKind = 'baseline'|'intent'|'composition'
interface EditDraft<T> {
  mutationId:string
  baseAuthorityRevision:number
  localVersion:number
  value:T
}
interface StudioClientState {
  server: StudioSnapshotDTO|null
  drafts: {
    composition: null|(EditDraft<CompositionDraftPatch> & {baseCompositionRevision:number})
    intents: Partial<Record<CutId,EditDraft<CutIntentDTO>>>
    baseline: null|EditDraft<BaselineDraft>
  }
  saves: Record<string,{state:'idle'|'pending'|'failed'|'conflict'|'base-changed';
    mutationId?:string; message?:string}>
  authoritativeEditLane: {
    inFlight:null|{kind:EditKind; draftKey:string; mutationId:string}
  }
  jobsUi: Record<string,{stopRequested:boolean}>
  selection: {cutId:CutId; bubbleId?:string}
  stream: {state:'connecting'|'open'|'reconnecting'; lastEventId?:string;
    gapFetchPending:boolean}
  ui: {leftOpen:boolean; rightOpen:boolean; queueOpen:boolean;
    review:null|{artifact:ReviewArtifactDTO; displayedByteHash:Sha256; zoom:number}}
  toasts: ToastMessage[]
}
```

`realizationComplete`, Current/STALE, projected composition, `hasCurrentSnapshot`, `hasBlockingEdit`, active/stoppable count, canGenerate, canMaterialize, canAuthorize는 computed selectors다. `hasCurrentSnapshot`은 initial/fresh GET 또는 newer accepted HTTP/SSE snapshot이 있고 gap recovery가 pending이 아닌 상태다. `hasBlockingEdit`는 baseline/intent/composition draft나 pending/failed/conflict/base-changed save 또는 edit lane in-flight가 있으면 true다. Components는 store actions/selectors만 사용한다. Mutable duplicate fields로 저장하지 않는다. pointer capture rect/delta/active handle과 local focus만 해당 component에 둔다.

### 5.2 한 authoritative edit mutation lane

- SQLite의 `authority_revision`이 baseline/rebaseline, 모든 cut-intent 수용, composition 수용 사이의 global CAS이므로 client도 이 세 edit type 전체에 exactly one authoritative edit lane을 둔다. cut별/composition별 별도 동시 lane은 금지하며 self-originated 두 accepted edit가 같은 base revision으로 race하지 않게 한다.
- lane은 현재 draft에서 request를 한 번 serialize할 때 body, `mutation_id`, `expected_authority_revision`과 composition의 `expected_composition_revision`을 immutable capture한다. request 중 새 edit는 해당 draft의 새 `localVersion/mutationId`로 남지만 이미 전송한 capture를 바꾸지 않는다.
- `serializeCompositionSave()`는 captured base의 latest authoritative `server.composition.state`에 해당 composition draft를 deterministic하게 적용하고 existing `CompositionStateDTO` full object만 만든다. derived/currency/job/auth/delivery/UI field를 넣지 않는다. Baseline/rebaseline은 exact-five full payload, intent는 one-cut full intent를 같은 lane에서 capture한다.
- 2xx: response snapshot을 server에 먼저 적용한다. `accepted_mutation_id`가 해당 draft의 **현재** mutation id와 같을 때만 그 draft/save를 clear한다. 더 최신 draft이면 유지하고, fresh response snapshot을 base로 lane의 다음 request를 serialize한다.
- network/500: captured payload와 local input을 보존하고 `failed`; alert toast `저장 실패 — 변경 내용은 이 브라우저에만 남아 있습니다.` 후에도 affected baseline/cut/bubble/field와 Canvas에 `저장 안 됨` marker를 남긴다. 사용자가 retry/reconcile하기 전 다른 authoritative edit는 같은 lane에서 진행하지 않는다.
- 409: `current_snapshot`을 server layer에 적용하고 해당 draft를 `conflict`로 보존한다. `서버 값 보기`는 authoritative 값을 read-only로 비교하고 `최신본에 다시 적용`만 same local content를 new mutation id와 current authority/composition base로 명시 재직렬화한다. 자동 overwrite/last-write-wins/implicit rebase를 하지 않는다.
- dirty 중 newer SSE는 server만 갱신하고 affected draft save state를 `base-changed`; edit/review/generation/approval gating은 유지한다. retry/reconcile success도 exact accepted current mutation만 clear하고 fresh HTTP/SQLite readback과 saved marker를 맞춘다.
- Baseline draft는 explicit approve/rebaseline 전 authority가 아니다. Accepted baseline 뒤 default composition save가 필요하면 baseline response의 fresh snapshot을 base로 **다음 lane item**으로만 실행한다.

### 5.3 edit가 아닌 command 경계

- Generation, review materialization, approval은 `hasCurrentSnapshot == true`, `hasBlockingEdit == false`이며 각 endpoint의 canonical precondition이 성립할 때만 enabled다. 이들은 authoritative edit lane에 넣지 않고 local edit draft나 mutation clear semantics를 공유하지 않는다; response의 fresh snapshot만 monotonic하게 적용한다.
- Global/per-job STOP은 safety/control command다. current snapshot 여부, `hasBlockingEdit`, lane in-flight, save failure/conflict와 무관하게 즉시 fetch하며 lane의 순서를 기다리지 않는다. STOP response/SSE terminal readback은 edit draft를 clear하지 않고 accepted intent를 바꾸지 않는다.

## 6. Canvas interaction, shell과 접근성

### 6.1 geometry/pointer/keyboard

한 `position:relative` canonical surface(1024:7680 aspect)가 base realization layer와 bubble overlay의 공통 좌표계다. CSS zoom/pan은 display transform이고 저장 geometry는 percentage다.

Pointerdown: primary button만, `setPointerCapture(pointerId)`, `preventDefault`, `touch-action:none`; surface `getBoundingClientRect()`와 starting geometry/pointer를 한 번 freeze한다. Pointermove는 `dxPct=(clientX-startX)/frozenRect.width*100`, y 동일; move/resize 모두 same clamp를 사용하고 DOM update는 `requestAnimationFrame` 한 element에만 한다. 매 frame store/full composition allocation/API 호출을 금지한다.

Pointerup: capture release, four-decimal round, local draft mutation 하나, save enqueue 하나. Pointercancel/lost capture: transient geometry만 last local draft로 되돌리고 store/API/revision을 건드리지 않는다. Focused bubble/handle Arrow는 exact `0.5%`, Shift+Arrow는 exact `2.0%`; 같은 edge/clamp 함수와 four-decimal serializer를 쓴다. viewport pixel을 저장하지 않는다.

### 6.2 layout와 responsive

- Desktop `>=1100px`: fixed Header + Left Rail + permanent Center + non-modal Right Inspector의 3열. 각 rail 독립 scroll, center min-size/overflow 격리, Header STOP은 항상 접근 가능.
- `<1100px`: Center는 permanent; left/right만 독립 toggle의 viewport-edge non-modal panel. 한 번에 열린 edge panel 하나, backdrop/focus trap 없음, Canvas/STOP은 계속 조작 가능. 닫아도 selection/draft 유지.
- verify widths: 1440, 1024, 768, 390, 320; browser zoom 200%. fixed controls는 safe-area inset, 44×44 conservative touch target, CSS logical properties를 사용한다. narrow에서 panel이 header STOP을 덮지 않는다.
- QueuePopover는 header trigger에 anchor, non-modal, Escape/outside click으로 닫고 trigger focus restore; keyboard Arrow/Tab/Enter/Space 경로를 제공한다.
- ReviewModal만 native `<dialog>.showModal()`로 focus trap, background inert, Escape는 승인 없이 닫고 trigger로 복귀한다. Rebaseline consequential confirmation은 별도 단기 dialog지만 ordinary editing modal은 아니다.
- semantic `header/nav/main/aside`, skip link, visible `:focus-visible`, sticky chrome에 가리지 않는 focus, icon-only accessible name, status `aria-live=polite`, save failure `role=alert`. Color alone으로 Current/STALE/error를 구분하지 않는다.
- `prefers-reduced-motion`에서는 feedback transition을 제거한다. 이 tool surface의 scroll-driven/expressive motion은 0개다.

## 7. Design Read와 구현 token

```yaml
---
name: comic-new-studio
colors:
  primary: "#16181D"
  accent: "#2563EB"
  background: "#EEF1F5"
typography:
  heading: { fontFamily: "Pretendard Variable, Pretendard, SUIT, Noto Sans KR, system-ui, sans-serif", fontSize: "20px" }
  body: { fontFamily: "Pretendard Variable, Pretendard, SUIT, Noto Sans KR, system-ui, sans-serif", fontSize: "14px" }
---
```

Reading this as: 한국어를 우선하는 반복 작업용 만화 creative workstation. 밝은 neutral chrome 안에 어두운 canonical canvas stage를 두어 “편집 projection”과 상태/명령의 층을 빠르게 구분한다. landing hero/card gallery가 아니라 CutRail→Canvas→Inspector의 촘촘하고 안정적인 작업 리듬이다.

- Do: revision pair와 persistent 상태를 compact text+shape로 노출; canvas가 시각 중심; 한 accent는 selection/primary action에만 사용.
- Don't: gradient/glass/oversized heading/3-equal-card/emoji/mascot/generated decoration/fake progress/영문 all-caps micro-label.
- `DESIGN_VARIANCE: 3/10`, `MOTION_INTENSITY: 1/10`, `VISUAL_DENSITY: 8/10`, product density `D4 Productivity`. 반복 편집의 정보량은 높이되 surprise와 motion은 낮춘다.

CSS custom properties는 최소 세 층만 둔다: neutral surfaces/text/border, one blue accent/focus, semantic current/stale/error. 제안 시작값: surface `#FFFFFF/#F7F8FA/#EEF1F5`, canvas `#16181D`, text `#17191D/#5E6572`, border `#D7DCE3`, accent `#2563EB`, current `#18794E`, stale `#A15C00`, error `#B42318`; 4/8/12/16/24 spacing; inner radius 4/6, panel radius 8; 1px border, shadow는 edge overlay에만. 실제 contrast가 AA를 못 넘으면 같은 역할 안에서 값만 조정하는 것은 implementer discretion이다. Korean button은 한 줄, body line-height 약 1.6, 숫자는 tabular. UI copy는 `현재`, `최신 의도 미실현`, `저장 안 됨`, `다시 시도`, `서버 값 보기`, `최신본에 다시 적용`, `발행 결과 미확인`처럼 짧고 행동 지향적으로 쓴다.

## 8. Build, package와 wheel 규칙

Frontend owner가 다음 source를 단독 소유한다.

```text
frontend/package.json, bun.lock, vite.config.ts, tsconfig*.json, index.html
frontend/src/**
src/comic_new/static/**   # generated, owner는 frontend 한 명뿐
```

- Vue 3 Composition API `<script setup>`, TS strict, Pinia one store, native fetch/EventSource, plain scoped CSS.
- CFW-1에서 support가 관찰된 여섯 package를 range/caret/tilde 없이 exact pin한다: runtime `vue: "3.5.42"`, `pinia: "4.0.3"`; build `vite: "8.3.0"`, `typescript: "5.9.3"`, `vue-tsc: "3.3.11"`, `@vitejs/plugin-vue: "6.0.9"`. router/component/canvas/DnD/state/query/test-browser package를 추가하지 않는다.
- `bun run build`는 `vue-tsc --noEmit && vite build`이며 Vite `base:'/'`, `outDir:'../src/comic_new/static'`, `emptyOutDir:true`.
- generated `index.html`이 content-hashed JS와 imported CSS를 `/assets/...`로 참조해야 한다. source map은 production package에 넣지 않는다.

Backend owner는 `pyproject.toml` runtime dependency를 range 없이 exact `fastapi==0.136.3`, `uvicorn==0.48.0`으로 선언하고 `static/**` package data를 선언한다. Starlette/Pydantic의 scratch transitive 관찰값을 direct dependency로 승격하거나 pin하지 않는다. wheel assembly의 canonical sequence는 repository root에서 다음 하나다.

```text
(cd frontend && bun install --frozen-lockfile && bun run build)
python3 -m pip wheel . --no-deps --wheel-dir <disposable-wheel-dir>
```

wheel은 clean temp venv에 설치하고 source tree 밖에서 `comic-new serve`를 실행해 package resource index/hashed assets를 검증한다. wheel 안에 `comic_new/static/index.html`, referenced hashed assets, schema/migrations가 있어야 한다. frontend source/`node_modules`는 wheel에 넣지 않는다. Static missing wheel은 serve startup failure여야 한다. 별도 magical setuptools hook이나 Node production daemon은 추가하지 않는다; release/integration runner가 위 명시적 pre-build를 수행한다.

## 9. 두 구현 owner와 exact 시작 범위

이 revision 전 review `/home/user01/tmp/comic-new-block04-plan-review.json`(SHA-256 `4ec4d1c025b82145f3d00bafd9cab26f184425d28fc9cb73565c8b8c914eac15`)의 `ADMIT`은 old Plan SHA-256 `fe658f2ac72209068a3704c423d1787d9f1b44a43da769bb5f6d20fa0f416d0d`만 대상으로 하므로 stale이며 구현을 승인하지 않는다. 이 exact revised Plan hash에 대한 fresh independent Plan Review가 `ADMIT`한 뒤 아래 두 owner를 동시에 시작할 수 있다. shared-file edit는 금지한다.

### Backend owner

소유: `pyproject.toml`, `src/comic_new/server.py` 및 필요한 새 Python web module(가급적 추가 없음), `src/comic_new/cli.py`, Python package-data/build config, backend-focused test file. `frontend/**`와 `src/comic_new/static/**`는 수정하지 않는다. Existing `store.py`, `generation.py`, `composition*.py`, schema/migrations는 본 방법에서 수정하지 않는다; route는 existing service를 호출한다.

첫 결과: exact `fastapi==0.136.3`/`uvicorn==0.48.0` 선언, §3 DTO/error/endpoint와 global authority CAS echo, §4 lifespan/static/supervisor/SSE 구현. Scratch resolver/import를 app proof로 대체하지 말고 empty static 때문에 product serve acceptance를 가짜로 통과시키지 않으며 route/app의 scoped lifecycle·missing-static checks 후 Main integration에 넘긴다.

### Frontend owner

소유: `frontend/**`, `src/comic_new/static/**`, frontend reducer/geometry tests와 lockfile. Python/pyproject/tests Python 파일은 수정하지 않는다.

첫 결과: §8 exact six pins/lock과 full app frozen install/typecheck/build, §3 contract를 그대로 소비하는 types/client/EventSource decoder, §5 one authoritative edit lane, shell/canvas/inspector/queue/review UI, production static. Backend가 아직 없을 때 fixture는 reducer/component 개발에만 쓸 수 있으며 Acceptance/real boundary 증거로 제출하지 않는다.

영구 test는 plausible regression을 직접 잡는 것만 둔다. Frontend: (a) older/equal SSE가 server/draft를 역전하지 않음, (b) cross-type edit lane의 immutable capture와 accepted mutation id가 newer draft를 clear하지 않음, (c) gap signal이 one in-flight snapshot recovery로 collapse됨, (d) pointer/keyboard percentage clamp·0.5/2.0·cancel reducer, (e) pending edit 중 STOP은 즉시 lane을 우회함. Backend: lifespan shutdown이 disposable SQLite의 real controlled child process tree를 settle하고 intent를 보존하는 경계, missing-static startup refusal. Route 존재/status/field copy/mock echo/snapshot markup test는 추가하지 않고 §12 actual smoke로 증명한다.

### 변경 재분배 규칙

DTO field, endpoint, persistence/effect owner, artifact identity, approval semantics가 바뀌면 둘 다 affected이므로 구현을 멈추고 Main이 이 Plan revision과 fresh independent Review를 소유한다. 이름/private helper/CSS 값/동등한 component 분리는 각 owner discretion이다. same-file 필요가 발견되면 임의 edit하지 않고 Main이 한 integration owner와 순서를 지정한다.

## 10. Integration 순서와 실패 경계

1. Main이 두 branch/result의 exact owned files를 fan-in하고 DTO가 §3과 byte-level로 맞는지 확인한다.
2. frontend frozen install/typecheck/production build로 generated static을 새로 만든다.
3. backend dependency install 후 source-tree `comic-new serve` static-missing negative와 generated positive를 실행한다.
4. wheel 생성→clean temp install→source tree 밖 serve로 package boundary를 확인한다.
5. 한 disposable project/font/control provider executable로 §12 implementer self-check를 순서대로 실행한다.
6. 실패 시 authoritative intent/old realization/artifact bytes를 삭제해 테스트를 맞추지 않는다. 서버/process를 settle하고 disposable root만 제거한다.
7. current source/Plan/Scope 해시와 clean working-tree expectation을 기록해 semantic verifier에게 넘긴다. Main만 commit/Block completion/다음 Block 진입을 결정한다.

Partial failure: build 실패면 serve proof로 진행하지 않는다; startup 실패면 browser proof로 진행하지 않는다; process termination 미확인이면 STOP proof를 실패로 남긴다; artifact identity/hash 불일치면 승인 endpoint를 호출하지 않는다. Safe unrelated checks만 계속한다.

## 11. Conditional-first-work와 남은 support 경계

CFW scratch는 repository 밖 `/home/user01/tmp/comic-new-block04-cfw/`에 fresh Review가 끝날 때까지 보존한다. 이는 dependency 선택의 primary local evidence이지 product source/build/runtime/Acceptance evidence가 아니다.

### CFW-1 — frontend dependency/lock: support 관찰 완료

- `plan_anchor`: `§8 Build, package와 wheel 규칙`
- `premise/outcome`: unbounded `latest`는 Vue `3.5.42`, Pinia `4.0.3`, Vite `8.3.0`, plugin-vue `6.0.9`, vue-tsc `3.3.11`, TypeScript `7.0.2`를 resolve했지만 `vue-tsc --noEmit`의 TypeScript `./lib/tsc` export error로 refuted됐다. TypeScript `5.9.3`을 포함한 §8 exact six pins는 같은 Bun/Node 환경의 empty strict app에서 supported로 관찰됐다.
- `executed_commands`: cwd `/home/user01/tmp/comic-new-block04-cfw/frontend`에서 먼저 six package 값을 `latest`로 쓴 `package.json`에 `bun install && bun run build && sha256sum bun.lock && bun install --frozen-lockfile && sha256sum bun.lock && bun pm ls`를 실행해 TypeScript `7.0.2`/vue-tsc failure를 관찰했다. 그 뒤 `package.json`을 §8 exact pins로 교체하고 같은 command를 재실행해 21 modules, typecheck/build exit `0`, unchanged frozen lock과 hashed JS+CSS를 관찰했다. `build` script의 exact command는 `vue-tsc --noEmit && vite build`다.
- `evidence`: `/home/user01/tmp/comic-new-block04-cfw/frontend`; manifest/lock/index/CSS/JS hashes는 §2.1.9 exact 값.
- `remaining_limit`: product의 full `frontend/**`가 생긴 뒤 동일 pins/lock으로 fresh `bun install --frozen-lockfile && bun run build`를 실행해 strict typecheck와 production static을 다시 관찰해야 한다. scratch output을 복사하거나 Acceptance A로 세지 않는다.
- `response_if_full_app_refutes`: frontend dependent mutation을 중단하고 actual full-app error와 manifest/lock bytes를 Main/Plan owner에게 반환한다. 대체 bundler/SSR/Tailwind/component suite를 추가하지 않는다; pin/stack 변경은 fresh Plan Review 대상이다.

### CFW-2 — Python runtime dependency: resolver/import support 관찰 완료

- `plan_anchor`: `§4 Python server, lifespan, runner와 single-serving`, `§8 Build, package와 wheel 규칙`
- `premise/outcome`: isolated Python 3.12 venv에서 exact `fastapi==0.136.3`, `uvicorn==0.48.0` resolver/install/import가 supported로 관찰됐다. transitive readback은 Starlette `1.6.0`, Pydantic `2.13.5`였다.
- `executed_commands`: cwd `/home/user01/tmp`에서 `python3 -m venv /home/user01/tmp/comic-new-block04-cfw/venv && /home/user01/tmp/comic-new-block04-cfw/venv/bin/pip install fastapi==0.136.3 uvicorn==0.48.0 && /home/user01/tmp/comic-new-block04-cfw/venv/bin/python -c "import fastapi,uvicorn; print(fastapi.__version__, uvicorn.__version__)"`; final stdout `0.136.3 0.48.0`.
- `remaining_limit`: product app/lifespan/static implementation이 아직 없으므로 `create_app` import/startup, missing-static refusal, SSE/stream response, actual runner settlement/graceful shutdown은 §12 product path에서 증명한다.
- `response_if_product_app_refutes`: framework-dependent 구현을 중단하고 actual import/lifespan/static/shutdown error를 Plan owner에게 반환한다. framework boundary 변경은 fresh Plan Review 대상이다.

### CFW-3 — wheel의 generated static 포함: UNRESOLVED

- `plan_anchor`: `§8 Build, package와 wheel 규칙`
- `premise`: 현재 setuptools package-data 규칙으로 nested hashed assets가 wheel에 들어가고 installed resource path에서 serve된다.
- `permitted_initial_work`: Main integration이 real production build 후 disposable wheel을 만들고 archive member를 inspect, clean venv install 후 repo 밖에서 serve한다.
- `discriminating_observation`: wheel에 index와 index가 참조한 exact hashed JS/CSS가 있고 HTTP `/`, `/assets/...`가 동일 bytes/hash로 200; Node/Bun/Vite process 없음.
- `dependent_work_not_yet_permitted`: release artifact/Block 완료 선언, empty-shell fallback, wheel 안에 frontend source/node_modules 포함.
- `response_if_refuted`: packaging fan-in을 중단하고 Backend owner가 package-data/MANIFEST 범위만 고친 뒤 같은 observation을 반복한다. custom build hook/packager가 필요해지면 Plan owner에게 재검토한다.

### CFW-4 — canonical font identity: UNRESOLVED

- `plan_anchor`: `§3.3 Mutation/read endpoints와 의미`의 review materialization, `§12.9 H`
- `premise`: verifier가 허가된 local font file을 갖고 그 SHA-256을 composition `font_sha256`과 동일하게 설정할 수 있다.
- `permitted_initial_work`: disposable project 전용 font path를 regular-file read하고 hash를 계산한 뒤 initial composition save에 exact hash를 사용한다.
- `discriminating_observation`: server가 same font bytes로 materialize하고 artifact embedded `font_sha256`, composition state, file hash가 일치한다. mismatch control은 409/validation failure이며 artifact를 만들지 않는다.
- `dependent_work_not_yet_permitted`: review/approval H proof, fallback font나 다른 hash로 success 주장.
- `response_if_refuted`: H와 dependent approval proof를 `BLOCKED`로 남기고 typography environment owner/Main에 exact missing/mismatch를 반환한다. 제품 compositor를 바꾸지 않는다.

## 12. Implementer self-check — actual production path

모든 test data/process는 disposable root와 ephemeral ports를 사용한다. provider subprocess는 image semantics를 증명하지 않는 ancillary controlled local executable일 수 있지만, 실제 child process spawn/PID group/termination/valid PNG handoff는 real이어야 한다. mock snapshot, seeded success state, in-memory store, Vite dev server, screenshot-only를 Acceptance 증거로 사용하지 않는다.

### 12.1 준비, pre/post identity와 cleanup ledger

- pre-source identity: commit, Scope/Thesis/Baseline/Arch/Plan hashes, production build manifest/index hash, wheel hash, installed package versions.
- pre-effect identity: disposable root absence, chosen DB path, font path/hash, ephemeral port, server PID, provider executable hash/PID logging location.
- 실제 `comic-new init`; API baseline 승인; controlled provider를 통한 exactly-five generation; valid composition save를 순서대로 수행한다. 각 단계 browser/HTTP 표시 값은 별도 Python process가 `TransactionalStore.open_project(...).snapshot()`한 fresh SQLite readback과 비교한다.
- post-effect identity: final authority/composition/cut/job/artifact tuples, DB hash는 실행 중 비교 기준이 아니므로 final shutdown 후에만 기록, artifact/source byte hashes, terminated PID/process-group observations, no leftover staging.
- cleanup: 먼저 EventSource/browser 닫기→graceful server termination→server/provider PID settlement 확인→temp venv/wheel/disposable project 삭제. 삭제 후 absence는 pre-existing artifact 제거 증거로 쓰지 않는다.

### 12.2 A — Exit 1-6 single production serve

- real frozen build에서 index + hashed JS/CSS 확인.
- generated static을 일시적으로 별도 보관한 negative copy에서 `serve` startup non-zero/명시 원인/no socket; 복구 후 one installed `comic-new serve` PID로 `/`, referenced assets, `/api/studio/snapshot`, `/api/events` 200.
- OS process tree에서 별도 Node/Bun/Vite/SSR frontend daemon이 없음을 확인한다. active generation 때의 controlled provider child는 별도 기록하여 frontend daemon과 구분한다.
- browser snapshot과 fresh SQLite의 authority revision/exact five/composition/jobs/artifacts identity 비교.

### 12.3 B — Exit 7-10 exactly-five와 truth dimensions

- five old valid realization bytes가 Current인 시작점에서 cut 하나의 새 intent를 실제 API로 수용한다.
- old pixel URL은 계속 표시되나 CutRail `STALE`, Header `UNRESOLVED`, review disabled; succeeded/empty queue를 별도 표시해도 currency가 바뀌지 않음.
- execution/currency/authorization/delivery 네 label/value가 generic success/published로 합쳐지지 않음을 DOM text와 snapshot readback으로 확인.

### 12.4 C — Exit 11-20 save isolation/failure/conflict

- Baseline/rebaseline, two different cut-intent saves와 composition save를 연속 발생시켜 browser request log에서 **cross-type max authoritative edit in-flight = 1**을 확인한다. 첫 response를 hold한 동안 다른 type을 편집해도 이미 captured URL/body/mutation/base revisions는 불변이고, 첫 accepted response가 더 최신 draft를 clear하지 않으며 fresh response snapshot으로 다음 item만 serialize한다.
- Inspector text와 Canvas pointer commit에서 draft 즉시 표시, acceptance 전 HTTP snapshot과 별도 SQLite unchanged, persistent unsaved marker.
- 첫 composition PUT response를 browser network에서 hold한 동안 두 번째 composition edit를 만든다. 첫 accepted mutation 뒤 두 번째 draft/value가 남고 global lane의 다음 save로 진행함을 확인한다.
- real network failure는 browser request abort로 만들고 local draft retention/UI만 증명하며 server effect 성공을 주장하지 않는다.
- real FastAPI 500은 별도 SQLite connection/process가 `BEGIN EXCLUSIVE`를 busy timeout보다 오래 유지한 동안 save하여 실제 server I/O failure를 발생시킨다. lock release 후 fresh readback unchanged, toast 후 persistent marker와 retry를 확인한다.
- 두 browser client가 same base에서 baseline/intent/composition 중 각각 충돌 가능한 edit를 수행한다. A 실제 수용 후 B가 409/current snapshot을 받고 B의 exact local draft가 남으며, read-only server compare 뒤 explicit `최신본에 다시 적용`만 new mutation/current base로 요청함을 확인한다. implicit rebase/overwrite는 없어야 한다.
- dirty B에 A change SSE를 보내 server revision만 update하고 draft/base-changed 유지. reconcile success 뒤 exact matching current mutation만 clear하고 fresh SQLite와 match한다.
- lane pending/failed/conflict/base-changed 동안 generation/review/approval이 disabled이고 lane item이나 edit draft로 생성되지 않음을 확인한다. Fresh current snapshot과 no blocking edit 뒤에만 각 canonical precondition대로 enabled된다.

### 12.5 D — Exit 21-27 SSE

- native EventSource 한 개와 connection indicator/last event identity를 browser에서 관찰한다.
- HTTP response가 먼저 반영된 뒤 같은 revision SSE를 받는 natural duplicate, reconnect replay로 older event를 받는 natural late path에서 server layer가 역행하지 않고 draft가 남는다.
- job terminal success snapshot에서 cut realization tuple이 unchanged인 통제(실패/late superseded)를 관찰해 Current 불변; 실제 commit-accepted snapshot에서만 revision equality 변화를 확인.
- stream을 끊고 replay capacity를 초과하는 실제 API mutations를 disposable DB에 수행한 뒤 reconnect한다. `snapshot-required` 후 exactly one GET, server layer only replacement, fresh SQLite convergence.
- disconnect 동안 persistent reconnecting이고 jobs/currency가 조작되지 않음.

### 12.6 E — Exit 28-33 actual STOP

- controlled local provider가 descendant child를 포함해 오래 실행하도록 하고 running + queued jobs를 만든다. Header/QueuePopover에 cut/revision/status와 STOP 접근성을 확인한다; fake %는 없어야 한다.
- authoritative edit lane request를 실제 hold한 상태에서도 global/per-job STOP 클릭은 confirmation 없이 즉시 별도 HTTP 요청으로 나가며 lane completion을 기다리지 않는다. `stopRequested`만 표시하고 HTTP/SSE terminal 전 상태는 running이다. STOP response가 held edit draft를 clear하거나 captured payload를 바꾸지 않음을 확인한다.
- server existing STOP path가 PID/start-token/process-group을 종료한 후에만 terminal snapshot/UI. `/proc`/OS process observation에서 root와 descendant 부재.
- fresh SQLite에서 desired intent unchanged, old pixel preserved, mismatch STALE/UNRESOLVED, release/delivery truth unchanged.

### 12.7 F — Exit 34-39 canonical interaction

- 1440과 narrow에서 actual pointer move/resize 저장, resize와 200% browser zoom 후 fresh SQLite percentages와 surface-relative geometry 동일.
- pointer capture 보유 확인; move frames 중 snapshot/DB revision unchanged. actual `pointercancel` 후 last draft로 복귀, network save 0, revision unchanged.
- pointerup은 draft/save one each; response 전 unsaved, 후 DB/display match.
- bubble과 resize handle Arrow `0.5%`, Shift `2.0%`, boundary clamp를 fresh SQLite에서 exact four-decimal 값으로 확인.

### 12.8 G — Exit 43-44 shell/responsive/focus

- 1440 desktop에서 Header/Left/Center/Right 동시, 독립 scroll/selection 중 Canvas와 STOP reachable, inspector non-modal.
- 1024/768/390/320 및 200% zoom에서 Center permanent, left/right edge toggles non-modal, draft/selection 보존, header/STOP no overlap.
- QueuePopover anchor/Canvas non-block/focus return, ReviewModal 외 ordinary path에 focus trap 없음.
- keyboard-only task, focus-visible, long Korean label/no clipping, 44px target, reduced-motion, no scroll-driven motion을 확인.

### 12.9 H — Exit 40-42 canonical review와 real approval call

- exactly five Current/no blocking draft에서 actual materialize. response/SQLite artifact identity, ordered closure, content file SHA-256/embedded metadata를 직접 비교.
- browser network response의 exact PNG bytes를 별도 hash하고 modal 표시 hash와 비교. DOM에서 bubble/text reconstruction layer가 없고 `<img>` contain/zoom만 있음을 확인.
- modal focus trap/Escape no approval/no canvas mutation/reopen same bytes.
- modal open 뒤 unrelated revision과 receiver identity-changing mutation을 각각 발생시킨다. unrelated 변화는 latest CAS로 endpoint가 재검증하고, identity change는 stale display approve를 disable/409한다.
- 승인 클릭 request URL/body의 artifact id/hash가 displayed byte hash와 같음을 capture하고 실제 FastAPI가 existing `authorize_release`를 호출하게 한다. **여기서 proof를 종료한다.** authorization restart/revocation/delivery는 H 성공에 포함하지 않는다.

### 12.10 I/J — 종합, restart, source→baseline→generation

- 같은 run에서 매 saved/current/job/artifact 표시를 fresh HTTP + 별도 SQLite로 교차 확인. screenshot은 visual/layout 증거일 뿐 state/effect 증거가 아님을 report에 분리한다.
- old-pixel STALE, network/500, 409, duplicate/older/gap SSE, late superseded, STOP-before-terminal, artifact identity mismatch를 차례로 주입해 relevant controls 차단과 input/old bytes/SQLite preservation을 확인.
- graceful restart proof는 §12.9의 실제 approval call **전에** 수행하거나 authorization이 없는 별도 disposable project에서 수행한다. accepted baseline/intent/composition/job terminal/artifact identity가 snapshot에 돌아오고 local browser draft가 authority로 복구되지 않으며 fake running/Complete/delivered/published가 생기지 않음을 확인하되, authorization row의 restart 보존/소실에 관한 BLOCK-05 verdict는 수집하지 않는다.
- 새 init 프로젝트의 no-baseline UI→Source Brief+exact five role/beat/intent→explicit baseline approval. fresh snapshot/SQLite exact baseline/five monotonic intents 일치.
- local cut intent save는 baseline 유지/one desired rev increase/STALE. structural role/order change는 ordinary intent/composition serializer에 field 자체가 없고 RebaselineDialog+exact-five baseline endpoint로만 가능.
- approved 뒤 Source Brief baseline draft edit만으로 server snapshot/cut/composition/release revision 불변; explicit Re-baseline 때만 새 baseline/exact five intents atomically accepted.
- generate all/one이 same endpoint/service/queue로 exact five/one job을 current desired revisions에 등록하고 UI/SQLite tuple 일치.

## 13. Later semantic verification handoff와 A-J/Exit trace

Implementer self-check가 통과해도 implementer는 `VERIFIED`나 BLOCK completion을 선언하지 않는다. 정확한 current implementation target(commit/tree identity), Plan hash, production manifest/wheel hash, disposable scenario ledger, browser screenshots와 network capture, HTTP/SSE raw capture, fresh SQLite readbacks, artifact/provider/process observations, cleanup 결과를 한 verifier에게 넘긴다.

| Scope Acceptance | Baseline Exit | 최소 real proof |
|---|---:|---|
| A | 1-6 | production build/wheel/one serve/static/API/process tree/missing-static negative |
| B | 7-10 | exact five, old-pixel STALE, UNRESOLVED, four truth dimensions |
| C | 11-20 | sole store, draft-before-accept, serialized saves, real network/500/409, reconcile |
| D | 21-27 | native SSE IDs, duplicate/older/accepted-only realization, replay gap GET, reconnect truth |
| E | 28-33 | running+queued controlled subprocess, immediate request, OS settlement, intent preservation |
| F | 34-39 | percentage persistence, capture/cancel, pointerup acceptance, 0.5/2.0 keyboard |
| G | 43-44 | desktop/non-modal narrow shell, QueuePopover/focus/modal boundary |
| H | 40-42 | real materialized bytes/hash/modal and exact displayed approval input to real store call |
| I | A-H 종합 | fresh HTTP+SQLite+artifact/process readback, false-success injection, restart |
| J | INV-1/7/8 + BLOCK-04 entry | no-baseline→baseline/exact intents→local edit/rebaseline→unified queue |

Verifier는 production Vite build/generated hashed assets, installed or source production `comic-new serve`, real Chromium desktop/narrow/zoom interactions, real FastAPI/SSE, disposable SQLite, controlled ancillary provider executable, OS PID observation, restart/readback을 새로 실행한다. Screenshot은 visual composition/focus/clipping의 증거로만 분류하고 SQLite state, process termination, artifact byte identity, approval/store effect를 대신하지 않는다.

Acceptance A-J와 Exit 1-44 전부에 fresh discriminating evidence가 있고 unresolved proof가 없을 때만 caller-owned Coverage로 넘어갈 수 있다. BLOCK-05 predicate, Baseline 전체 Completion Predicate, Blogger/destination은 검증하지도 완료로 기록하지도 않는다.

## 14. Revision/abort 기준과 남는 한계

다음은 affected 구현을 즉시 중단하고 Plan fresh Review가 필요한 material change다: endpoint/DTO identity, SQLite 외 mutable owner, event persistence/replay 의미, runner lifecycle/process-settlement strategy, save conflict/clear semantics, canonical geometry, review byte source, approval writer/effect 경계, build/wheel/static ownership. Product meaning 변경은 Thesis owner, current Outcome/Acceptance 변경은 Scope shaper에게 돌린다.

Abort 상태에서는 accepted intent와 valid old pixels를 보존하고 mismatch는 STALE, running process는 실제 settle, authorization/delivery를 승격하지 않는다. lock file, JSON sidecar, local approval boolean, fake event progress, client polling으로 결함을 봉합하지 않는다.

현재 unresolved evidence는 CFW-3 wheel, CFW-4 font와 §2.3에 명시한 full-app production build/runtime 관찰뿐이다. CFW-1 exact pins와 CFW-2 resolver/import support는 scratch에서 관찰됐지만 제품 Acceptance를 세우지 않는다. 이 revision은 제품 frontend/server/wheel/runtime/browser/SQLite/provider path를 구현하거나 실행하지 않았고, BLOCK-04 semantic verdict·Coverage·completion·BLOCK-05 진입을 주장하지 않는다. 이전 review `/home/user01/tmp/comic-new-block04-plan-review.json`의 old-hash `ADMIT`은 stale하며, exact revised Plan hash에 대한 fresh independent Gemini Flash Plan Review와 ADMIT은 Main 소유다.
