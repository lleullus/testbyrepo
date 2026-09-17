# PLAN-001 — BLOCK-11 OpenCodex Draft Generation 및 One-Click Studio UX

## 1. 결속된 권위와 실행 경계

- Project Root: `/home/user01/project/comic_new`
- Scope: `/home/user01/project/comic_new/docs/planning/work/opencodex-draft-studio-ux/SCOPE.md` (sha256 `5666bc0440fde1edb0fa76f70d05cb963496e2dd322204b66645c78b6454990c`, `Schema: iis-scope/v1`, `Status: ready`)
- Normative Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md` (`THESIS-003`, sha256 `d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268`)
- Transition Authority: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md` (sha256 `59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51`, selected `BLOCK-11`)
- Repository investigation: 별도 불변 investigation artifact는 제공되지 않았다. 이 Plan은 위 원본과 현재 source/test bytes를 직접 조사한 결과에 결속한다.
- Scope validator: canonical `scope-shaper/tools/validate_scope.py --json`은 `iis-scope/v1`, `status: ready`, 위 Thesis/Transition path 및 digest의 정확한 일치를 반환했다.
- 선행 경계: `/home/user01/project/comic_new/docs/planning/work/live-model-sparse-baseline/SCOPE.md:1-27`은 `Status: done`으로 BLOCK-10을 기록한다. 다만 문서 상태만으로 runtime 성공을 추정하지 않으며, 구현자는 §8 CF-1의 bounded readback으로 sparse approval/단일 컷 경계를 확인한다.
- 허용 범위: BLOCK-11의 OpenCodex draft 제안, HTTP API, 편집 가능한 one-click UX와 관련 테스트만 구현한다. BLOCK-12 geometry/좌표와 BLOCK-13 저장 스키마·동적 membership/order는 시작하지 않는다.
- 증거 경계: `httpx.MockTransport`, 가짜 client 및 component fetch mock은 retry·DTO·UI 보존을 판별하는 보조 수단이다. 이들은 실제 `127.0.0.1:10100` OpenCodex 연결, 실제 모델 선택/응답 또는 사용자가 브라우저에서 경험하는 end-to-end 성공의 대체 증거가 아니다. 실제 draft 성공은 로컬 서비스 응답의 validated draft/provenance와 브라우저 편집·별도 승인 후 fresh Baseline snapshot을 연결해 판정한다.

### 1.1 모델 이름과 정책 결속

사용자 지시의 `gemini-3.8-flash-high` 및 `opencodex-gpt5.6-luna-high` 표기는 모델 계열/노력 수준을 합쳐 표현한 이름으로 이해하되, wire payload는 더 구체적인 제품 권위인 `THESIS-003 §3.3`과 `BASELINE-003 BLOCK-11 Scope Invariants`를 그대로 따른다.

1. Primary wire model: `google-antigravity/gemini-3.8-flash`, `reasoning_effort: high`, read timeout 45초.
2. Fallback wire model: `gpt-5.6-luna`, `reasoning_effort: max`, read timeout 90초.
3. endpoint: `http://127.0.0.1:10100/v1/chat/completions`.
4. 런타임에서 임의로 “사용 가능한 빠른 Gemini”를 탐색하거나 다른 alias로 silent substitution하지 않는다. 위 식별자가 실제 서비스에서 거절되면 §8 CF-2에 따라 제품 수단/권위 소유자에게 반환한다.

## 2. 달성할 관찰 결과와 보존 조건

최초 Baseline 화면의 주 작업은 `주제 또는 시놉시스` 한 줄과 `[AI 콘티 자동 생성]` 버튼이다. 사용자가 유효한 brief를 입력하면 서버는 권위 DB를 변경하지 않은 채 OpenCodex fallback chain을 실행하고, 요청한 `cut_count`(기본 5)에 정확히 대응하는 ordered draft를 반환한다. 각 cut은 stable draft identity, display order, non-empty `role`, `beat`, self-contained `prompt`, 문자열 `dialogue`와 전체 attempt provenance를 가진다. 현재 Studio 승인 경로는 fixed-five이므로 frontend는 `cut_count: 5`로 호출하고 결과를 기존 다섯 cut 편집 필드에 local draft로 채운다. API/client 내부의 `cut_count >= 1` 지원은 draft 제안 계약일 뿐 BLOCK-13의 authoritative N-cut persistence를 선행하지 않는다.

생성 결과는 편집 가능한 **무권위 제안**이다. 성공만으로 `POST /api/baselines`를 호출하거나 generation job을 enqueue하거나 authority revision/authorization/currentness를 바꾸지 않는다. 사용자가 결과를 검토·수정하고 별도 `[승인]`을 눌러 기존 Baseline 저장 응답이 성공한 뒤에만 dialog를 닫는다.

동시에 다음을 보존한다.

1. 원문 brief와 생성 전 local role/beat/prompt/dialogue는 요청 중 유지한다. 생성 실패·malformed output·502/503에서는 한 필드도 덮어쓰지 않는다.
2. 실패 후 즉시 동일 brief 재시도 또는 `[수동 입력]` 전환이 가능하다. loading latch가 반드시 해제된다.
3. OpenCodex가 반환한 부분 데이터나 추정 보정값을 성공 draft로 표시하지 않는다.
4. draft 호출은 store/DB/SSE authority mutation과 분리하며 INV-1 CAS, INV-2 STOP lockout, INV-3 approval revocation, INV-4 destination readback 경로를 건드리지 않는다.
5. Baseline save의 기존 400/409/422/5xx 보존 동작을 유지한다. 성공 응답 전에 dialog를 닫지 않고, 실패 시 local draft를 유지한다.
6. prompt는 각 cut에 필요한 인물·의상·배경·행동·구도·조명과 별도 조판용 negative space/no rendered text를 self-contained하게 표현한다. `same as previous`류 상대 참조는 schema 이후 의미 검증에서 거절한다.
7. dialogue `""`는 유효한 무대사 의도다. role, beat, prompt, draft identity는 empty/whitespace-only일 수 없다.

## 3. 현재 코드 Grounding

### 3.1 EXISTING — legacy OpenCodex 구현과 재사용 가능한 정책

- `/home/user01/project/comic/src/comic/llm/client.py:58-83`: legacy `OpenCodexClient`는 base URL, primary/fallback model·reasoning·timeout, connect timeout, 150초 budget과 주입 가능한 `httpx.AsyncClient`를 가진다.
- 같은 파일 `:85-153`: `/chat/completions`, `response_format: {"type":"json_object"}`, per-request timeout, Markdown fence 제거, JSON parsing과 attempt 기록 패턴이 있다.
- 같은 파일 `:155-239`: primary 최대 2회, fallback 최대 2회와 429/일부 5xx retry가 구현되어 있다. 새 구현은 이 구조를 포팅하되 **모든** 5xx, hard wall-clock budget, schema failure fallback을 정확히 보완한다.
- 같은 파일 `:241-266`: story script와 target cuts를 system/user message로 분리하고 Pydantic model validation 후에만 storyboard를 반환한다.
- `/home/user01/project/comic/src/comic/llm/prompts.py:3-32, 86-130`: vertical webtoon, cinematic continuity, self-contained cut, separate typesetting, negative space 및 no in-image text 원칙이 이미 있다.
- 같은 파일 `:132-184`: legacy schema는 ordered storyboard unit의 구조를 제공하지만 BLOCK-11의 `role/beat/dialogue/prompt`, stable draft identity/order 및 attempt provenance를 직접 표현하지 않는다. 그대로 복사하지 않고 제품 DTO에 맞춘 새 schema를 둔다.

이 근거는 transport/prompt 작성 원칙을 재사용할 수 있음을 확정하지만 legacy client가 현재 BLOCK-11 정책을 완전히 충족한다는 증거는 아니다. 특히 legacy는 501/505 등 모든 5xx를 retry하지 않고, JSON parse 이후 제품 schema validation 실패를 fallback 대상으로 처리하지 않는다.

### 3.2 EXISTING — backend API와 authority 경계

- `pyproject.toml:5-14`: runtime dependency에는 FastAPI/Uvicorn/Pillow만 있고 `httpx`가 없다.
- `src/comic_new/server.py:22-29, 79-154`: FastAPI/Pydantic wire model 패턴과 `extra="forbid"`가 있으며 Baseline DTO는 ordered cut 1..5를 검증한다.
- `src/comic_new/server.py:623-637, 802-891`: `ApiProblem` JSON envelope와 400/409/422/5xx exception mapping이 한 곳에 있다.
- `src/comic_new/server.py:664-800`: `create_app()`이 service를 한 번 구성하고 `app.state`에 소유시키며, `fresh_and_publish()`만 authoritative snapshot/SSE를 발행한다.
- `src/comic_new/server.py:893-908`: `POST /api/baselines`만 store approval을 호출해 authority를 변경한다. 새 draft route는 이 함수나 `fresh_and_publish()`를 호출하면 안 된다.
- `src/comic_new/server.py:933-972`: generation enqueue/STOP은 별도 명시 endpoint다. draft 생성에서 재사용하지 않는다.
- `tests/test_server.py:139-189` 및 `tests/test_baseline_dialogue_authority.py:95-166`: disposable project + `TestClient(create_app(...))`의 실제 route 통합 패턴이 있다.

### 3.3 EXISTING — frontend 입력·저장·오류 보존 경계

- `frontend/src/components/baseline/RebaselineDialog.vue:11-26, 88-123`: 현재 source brief와 5×4 fields를 dialog 진입 즉시 모두 펼치며 AI action/loading이 없다.
- 같은 파일 `:30-50`: open 시 browser draft를 authoritative Baseline보다 우선 복원하므로 local edits 보존 기반은 이미 있다.
- 같은 파일 `:57-81`: `updateDraft()`가 local fields를 store draft로 직렬화하고 `submit()`이 `saveBaselineDraft()` 결과를 기다려 success일 때만 닫는다.
- `frontend/src/api/client.ts:20-57`: 모든 same-origin API가 공통 `request<T>()`와 `ApiError` envelope를 사용하지만 success payload runtime validation은 snapshot 외에는 caller가 별도로 해야 한다.
- `frontend/src/api/contracts.ts:3-45`: 현재 `CutId`와 Baseline submit contract는 fixed-five이며 prompt origin을 구분한다. BLOCK-11 API의 draft identity/order/provenance DTO는 없다.
- `frontend/src/store/studio.ts:350-430, 540-574`: edit lane은 save failure 시 draft/toast를 보존하고 `saveBaselineDraft()`는 `Promise<boolean>`을 반환한다.
- 같은 파일 `:871-923`: dialog가 사용할 수 있는 draft-generation action은 아직 없다.
- `frontend/tests/store.test.ts:71-100`: controlled fetch와 request-body helper가 있어 pending/success/error를 순서 제어할 수 있다.
- `frontend/vitest.config.ts:4-11`, `frontend/package.json:14-20`: Vitest는 node 환경이고 Vue component mount/jsdom dependency가 없다. 실제 component interaction test를 위해 최소 test dependency/config 추가가 필요하다.

### 3.4 EXISTING — 선행 BLOCK-10과 고정 5컷 경계

- `src/comic_new/server.py:79-82, 120-128`: current authoritative API는 cut identity 1..5를 고정한다.
- `frontend/src/api/contracts.ts:5, 27-36`: frontend Baseline 역시 exact tuple 1..5다.
- `frontend/src/components/shell/StudioShell.vue:42-49`: Baseline이 없을 때 사용자는 `Baseline 설정`으로 dialog에 진입한다.
- 선행 BLOCK-10 Scope는 sparse approval과 single-cut generation 완료를 기록하지만, 현재 BLOCK-11 구현자는 §8 CF-1 readback 전 이를 runtime 사실로 가정하지 않는다.

따라서 BLOCK-11에서 `cut_count`를 API/LLM 제안 단계에 지원하되 frontend 승인 path는 5를 명시하고, authoritative DTO/DB/cardinality를 일반 N으로 바꾸지 않는다. 이는 BLOCK-13을 침범하지 않으면서 Thesis의 draft API 입력 계약을 보존한다.

### 3.5 PROPOSED / UNRESOLVED 요약

- **PROPOSED:** `src/comic_new/llm/`의 새 async client/prompt/schema, retry/fallback/budget와 sanitized provenance.
- **PROPOSED:** `POST /api/baselines/generate-draft`의 non-authoritative DTO와 400/502/503 mapping.
- **PROPOSED:** typed frontend client/store action, one-line-first dialog, success-only overwrite, failure preservation, 별도 승인.
- **PROPOSED:** backend client unit, HTTP integration, store/component interaction tests.
- **UNRESOLVED:** 현재 로컬 OpenCodex가 권위에 고정된 두 wire model identifier와 `reasoning_effort`/`response_format`을 실제 수용하는지 source만으로는 알 수 없다. §8 CF-2에서 실제 서비스 readback으로 판별한다.
- **UNRESOLVED:** 현재 target runtime에서 BLOCK-10 sparse approval/single-cut 경계가 실제로 유지되는지는 상태 문서만으로 증명되지 않는다. §8 CF-1로 판별한다.

## 4. Backend 구현 방법

### 4.1 `src/comic_new/llm/` 모듈과 DTO

새 package는 최소 세 파일로 둔다.

1. `src/comic_new/llm/__init__.py`: server가 필요한 `OpenCodexClient`, `DraftGenerationError`, request 결과 type만 명시 export한다.
2. `src/comic_new/llm/prompts.py`: 하나의 storyboard system prompt와 user-message builder를 둔다.
3. `src/comic_new/llm/client.py`: Pydantic draft model, attempt record, JSON extraction/validation, retry/fallback/budget 및 `generate_draft()`를 둔다. 별도 service/repository layer는 만들지 않는다.

검증된 내부/응답 shape는 다음 의미를 가진다.

```json
{
  "source_brief": "사용자 원문 그대로",
  "cut_count": 5,
  "cuts": [
    {
      "draft_id": "cut-1",
      "display_order": 1,
      "role": "establishing",
      "beat": "...",
      "dialogue": "... 또는 빈 문자열",
      "prompt": "self-contained production prompt"
    }
  ],
  "provenance": {
    "provider": "opencodex",
    "selected_model": "google-antigravity/gemini-3.8-flash",
    "attempts": [
      {
        "model": "google-antigravity/gemini-3.8-flash",
        "reasoning_effort": "high",
        "outcome": "succeeded",
        "status_code": 200,
        "elapsed_ms": 123
      }
    ]
  }
}
```

LLM가 생성할 JSON object는 `cuts`만 포함하며 각 row의 `draft_id`, `display_order`, `role`, `beat`, `dialogue`, `prompt`를 모두 required로 한다. 서버가 신뢰 가능한 원문 `source_brief`, requested `cut_count`와 attempt provenance를 envelope에 결합한다. 검증 규칙은 다음과 같다.

- `cut_count`는 strict integer, `>= 1`; bool과 문자열 숫자는 거절한다. operational abuse 방지를 위한 상한은 현재 제품 계약에 없으므로 Plan이 임의 상한을 만들지 않는다.
- `len(cuts) == cut_count`.
- `draft_id`는 trim 후 non-empty이며 response 안에서 unique다.
- `display_order`는 정확히 `[1, ..., cut_count]` 순서로 한 번씩 나타난다. 정렬해서 보정하지 않는다.
- role/beat/prompt는 trim 후 non-empty다. 원문 문자열을 보존하되 whitespace-only는 실패다.
- dialogue는 문자열이면 빈 값도 허용한다.
- prompt는 상대 참조(`same as previous`, `as above`, `이전 컷과 동일` 등)를 금지하고, 별도 조판을 위한 no rendered text/typography와 speech-balloon negative-space 지시를 포함해야 한다. 이 최소 의미 조건이 없으면 schema mismatch로 해당 attempt를 실패시킨다.
- extra field는 `forbid`하여 malformed/부분 출력을 정상 draft로 흡수하지 않는다.

`source_brief`는 request의 topic을 trim해 사용하되 사용자가 입력한 내부 줄바꿈/내용은 변경하지 않는다. 응답 provenance에는 stack trace, raw provider body, local path나 비밀을 넣지 않는다. 실패 attempt의 public summary는 model, effort, status/`timeout|connection|rate_limited|upstream_5xx|invalid_response|budget_exhausted` category만 포함한다.

### 4.2 prompt 구조

`prompts.py`의 system prompt는 legacy 지침을 BLOCK-11 DTO로 압축해 다음을 명시한다.

1. 입력 brief를 exact `cut_count` ordered vertical-scroll webtoon cuts로 변환한다.
2. 전체 arc는 hook/establish → buildup/turn → climax/reaction/resolution을 cut 수에 맞게 구성하고 인물/배경 연속성을 유지한다.
3. 각 cut은 unique stable `draft_id`, 1-indexed `display_order`, narrative `role`, 관찰 가능한 `beat`, dialogue intent, standalone image prompt를 갖는다.
4. prompt는 주체·외형·의상·행동·배경·camera/framing·lighting·mood를 매 cut 반복해 자립시키며 이전 cut 상대 참조를 쓰지 않는다.
5. lettering은 downstream separate-typesetting이다. prompt에 clean negative space를 지정하고 image 안 text/typography/speech bubble 렌더를 금지한다.
6. JSON object 외 prose/Markdown fence를 반환하지 않는다.

user message는 XML/도구 지시로 해석될 여지를 줄이도록 brief를 명확한 quoted data block에 넣고, `cut_count`와 required field 목록을 반복한다. 사용자 brief 속 명령은 이야기 재료일 뿐 system/schema를 변경할 수 없다고 명시한다. JSON repair 재호출이나 추측 기반 fill은 하지 않는다.

### 4.3 async OpenCodex fallback chain

`OpenCodexClient`는 legacy constructor seam을 유지하되 기본값을 §1.1에 고정한다. `httpx.AsyncClient` 또는 `MockTransport` 주입을 허용하고, production에서는 요청마다 client를 열고 닫아 app lifespan ownership을 늘리지 않는다. `pyproject.toml` runtime dependency에 현재 FastAPI/TestClient 계열과 호환되는 `httpx` 범위를 명시한다.

한 attempt의 순서는 다음과 같다.

1. `deadline = monotonic() + 150.0`을 `generate_draft()` 진입에서 한 번만 만든다.
2. dispatch 전 remaining budget을 계산한다. 0 이하이면 새 request를 보내지 않고 `budget_exhausted`로 종료한다.
3. payload는 `model`, `reasoning_effort`, `response_format: {"type":"json_object"}`, system/user messages를 포함한다.
4. `httpx.Timeout`의 connect/read/write/pool 값을 remaining budget 이내로 cap하고 전체 `client.post()`도 `asyncio.timeout(remaining)`으로 감싸 DNS/connect/write까지 hard budget 밖으로 나가지 못하게 한다.
5. HTTP 200이라도 content extraction, optional outer Markdown fence strip, `json.loads`, Pydantic/semantic validation까지 통과해야 attempt `succeeded`다.
6. 429 또는 `500 <= status < 600`만 같은 모델에서 최대 한 번 retry한다. retry backoff 0.5초도 remaining budget을 넘기지 않는다.
7. 4xx(429 제외), timeout/connection, malformed JSON/schema mismatch는 같은 모델을 재시도하지 않고 즉시 다음 모델로 이동한다.
8. primary 성공이면 fallback을 호출하지 않는다. primary 두 attempt 또는 non-retryable failure 뒤 fallback으로 이동한다. fallback도 같은 retry 규칙을 적용한다.
9. 두 모델이 실패하거나 budget이 소진되면 모든 sanitized attempts를 가진 `DraftGenerationError`를 던진다. `CancelledError`는 삼키지 않는다.

오류 category와 HTTP mapping:

- 모든 실제 dispatch가 connection/timeout/budget availability failure이고 유효한 upstream response를 한 번도 받지 못한 경우 `503`, code `draft_service_unavailable`.
- upstream 429/5xx, invalid JSON/content/schema 또는 정책 위반 response가 포함된 최종 실패는 `502`, code `draft_generation_failed`.
- 양쪽 category가 섞이면 “provider에 도달했으나 valid draft를 얻지 못함”인 502를 우선한다.

이 분류는 사용자에게 retry/manual 경로를 안내하기 위한 것이며 partial response를 성공시키지 않는다.

### 4.4 FastAPI endpoint

`src/comic_new/server.py`에 다음 wire model과 route를 추가한다.

- `DraftGenerationRequest`: `topic: StrictStr`, `cut_count: strict int = 5`.
- body가 object가 아니거나 type이 틀린 경우 기존 global request validation대로 422다.
- endpoint 진입에서 `topic.strip()`이 empty면 `ApiProblem(400, "validation_error", "topic must be a non-empty string")`을 반환한다. `cut_count < 1`도 400으로 mapping한다. 이 route-specific 400은 다른 endpoint의 422 계약을 바꾸지 않는다.
- `create_app(..., draft_client: OpenCodexClient | None = None)` test seam을 추가하고 production 기본 client를 한 번 선택해 `app.state.draft_client`에 둔다. 다른 service constructor/caller는 optional tail argument라 변경하지 않는다.
- `POST /api/baselines/generate-draft`는 shutdown 중 새 work를 시작하지 않도록 `_ensure_accepting(app)` 후 `await draft_client.generate_draft(...)`를 직접 호출한다. client 자체가 async이므로 `to_thread`를 사용하지 않는다.
- success는 validated response를 반환할 뿐 `store`, `fresh_and_publish`, broadcaster, generation service를 호출하지 않는다.
- `DraftGenerationError`만 502/503 `ApiProblem`으로 번역하고 sanitized attempt summary를 message/detail에 포함한다. raw body/trace는 숨긴다. 예기치 않은 bug는 기존 500 handler로 간다.

`ApiProblem` envelope는 현재 optional revision/snapshot 필드만 지원하므로 attempts를 표현할 optional `details: dict[str, Any] | None`을 추가하고 `_api_error()`가 있을 때만 `error.details`를 내보낸다. 기존 error fields와 callers는 그대로 유지한다. frontend `ApiErrorDTO`도 optional typed details를 수용한다.

## 5. Frontend 구현 방법

### 5.1 typed API 및 runtime validator

`frontend/src/api/contracts.ts`에 authority DTO와 분리된 `DraftCutDTO`, `DraftAttemptDTO`, `DraftGenerationResponseDTO`를 추가한다. draft cut identity는 `string`, display order는 positive integer이므로 fixed `CutId`로 거짓 typing하지 않는다. `isDraftGenerationResponseDTO()`/`validateDraftGenerationResponse()`는 backend와 동일하게 count, unique identity, exact order, required strings, selected-model/attempt consistency를 검사한다.

`frontend/src/api/client.ts`에 `postGenerateDraft({ topic, cut_count })`를 추가하고 success JSON을 runtime validator에 통과시킨다. 단순 `as Promise<T>` cast만으로 component에 전달하지 않는다. server 502/503은 기존 `ApiError` path를 사용한다.

### 5.2 store action과 local draft ownership

`frontend/src/store/studio.ts`에 `generateBaselineDraft(topic: string, cutCount = 5): Promise<DraftGenerationResponseDTO | null>` action을 추가한다.

1. 별도 authority edit lane에는 넣지 않는다. 이는 권위 mutation이 아니라 외부 draft 제안 요청이다.
2. component가 중복 요청을 막지만 store action도 one-call/one-response만 수행하고 자동 retry를 추가하지 않는다. retry/fallback은 server 정책 소유다.
3. 성공 시 응답이 정확히 5 cuts인지 확인하고 `BaselineStructureDTO`의 cut_id 1..5와 response display order 1..5를 명시적으로 매핑한다. role/beat를 structure로, prompt/dialogue를 intents로 옮기고 prompt origin은 승인 시 BLOCK-10 server가 판정하는 기존 contract를 따른다.
4. `setBaselineDraft(structure, intents, false)`로 browser local draft를 만들되 자동 save/enqueue하지 않는다. action은 response를 component에 반환한다.
5. 실패 시 기존 `drafts.baseline`, server snapshot 및 component local inputs를 변경하지 않는다. `ApiError`이면 server의 정직한 message를 포함한 alert toast, invalid success/network이면 일반 생성 실패 toast를 추가하고 `null`을 반환한다.
6. 성공 toast는 “초안이 생성되었습니다. 검토 후 승인하세요.”로 제안/승인을 구분한다.

생성 요청 중 사용자가 local field를 바꿀 가능성을 component loading disable로 줄이되, late response overwrite 정책은 request 시작 시 `sourceBrief`와 local edit version을 캡처해 판별한다. response 도착 전 source brief 또는 editor fields가 바뀌었다면 결과를 자동 적용하지 않고 “입력이 변경되어 생성 결과를 적용하지 않았습니다” toast를 표시하며 기존 입력을 보존한다. 요청 취소/새 요청을 암묵적으로 만들지 않는다.

### 5.3 `RebaselineDialog.vue` one-line-first UX

현재 21-field 기본 노출을 다음 상태로 바꾼다.

- dialog 상단 첫 control: label `주제 또는 시놉시스`, 현재 `sourceBrief` textarea/input.
- 그 바로 아래 primary action `[AI 콘티 자동 생성]`과 secondary `[수동 입력]`.
- 새 Baseline에서 기존 local draft가 없을 때 상세 cut editor는 접혀 있다. AI success 또는 `[수동 입력]` 후에만 5개 cut card를 펼친다.
- 기존 Baseline/rebaseline 또는 저장 전 browser draft가 있으면 그 값을 즉시 복원하고 editor를 펼쳐 데이터가 숨겨지거나 초기화되지 않게 한다.
- `isGenerating`과 `isSubmitting`은 분리한다. generating 동안 AI 버튼은 disable되고 `AI 콘티 생성 중…` 및 `aria-busy`/live status를 표시한다. 승인/취소 정책은 기존 draft 보존에 맞추되 동일 action의 중복 클릭은 막는다.
- AI click은 empty topic을 client에서 즉시 안내하되 server 400 계약도 유지한다. 호출은 항상 `cut_count: 5`다.
- 성공 response가 현재 request input과 일치할 때만 source brief/cuts/intents를 한 번에 교체하고 editor를 펼친다. DOM에 부분 apply하지 않는다.
- 실패/null이면 editor visibility와 sourceBrief/cuts/intents를 요청 전 그대로 둔다. toast는 store의 `ToastRegion`을 재사용하고 dialog 안에는 간단한 retry/manual 안내를 둔다.
- footer primary label은 `[승인]`/`승인 중…`으로 통일한다. `submit()`은 현재처럼 `updateDraft()` 후 `await saveBaselineDraft()`하고 true일 때만 close한다.
- 성공 draft를 사용자가 수정하면 `updateDraft()`가 수정값을 그대로 저장한다. 생성 결과를 재호출하거나 provenance를 승인 payload에 억지로 끼워 넣지 않는다. 현재 BLOCK-10은 저장 snapshot에서 `llm_draft` origin을 표현할 계약을 이미 갖지만, 그 origin을 정확히 전달할 request field가 현재 없다면 §8 CF-3 전까지 `user`로 오표기해서는 안 된다.

마지막 origin 항목은 load-bearing하다. current Baseline submit wire DTO에는 prompt origin field가 없으므로 AI prompt를 승인할 때 server가 `user`로 판정한다면 Thesis의 origin truth를 위반한다. 따라서 §8 CF-3에서 현 store/server behavior를 확인하고, 필요하면 이 Scope 안에서 `BaselineIntentDTO` request에 `prompt_origin: 'user' | 'llm_draft' | 'intelligent_default'`를 명시적으로 추가한다. AI mapping은 `llm_draft`, 수동 입력/AI 후 사용자 수정은 해당 cut prompt field가 바뀐 시점에 `user`로 전환한다. optional field/default/shim으로 과거 의미를 숨기지 않고 기존 manual caller를 함께 migrate한다.

## 6. 파일별 line-anchored 변경 목록

1. `pyproject.toml:5-14`
   - async OpenCodex transport용 `httpx` runtime dependency를 추가한다.
2. 새 `src/comic_new/llm/__init__.py`, `src/comic_new/llm/prompts.py`, `src/comic_new/llm/client.py`
   - §4.1~4.3의 DTO, prompt, async retry/fallback, budget, sanitized provenance를 구현한다.
3. `src/comic_new/server.py:18-29, 79-210`
   - LLM imports, `DraftGenerationRequest`, optional `ApiProblem.details`, route-specific validation DTO를 추가한다.
4. `src/comic_new/server.py:623-637, 664-800`
   - error details projection과 optional injected `draft_client`, `app.state` ownership을 연결한다.
5. `src/comic_new/server.py:893-933` 사이
   - `POST /api/baselines/generate-draft`를 Baseline approval route와 generation job route 사이에 추가한다. store/SSE mutation은 호출하지 않는다.
6. `frontend/src/api/contracts.ts:3-45, 217-239` 부근
   - draft response/provenance/error details type 및 독립 runtime validator를 추가한다.
7. `frontend/src/api/client.ts:3-18, 39-57, 78-114`
   - typed `postGenerateDraft()`와 success runtime validation을 추가한다.
8. `frontend/src/store/types.ts:3-30, 46-74`
   - 필요한 경우 baseline draft에 per-cut prompt origin/edit metadata를 포함하되 authority state와 혼합하지 않는다.
9. `frontend/src/store/studio.ts:15-29, 505-574, 871-923`
   - draft API import, `generateBaselineDraft()`, success mapping/failure toast/action export를 추가하고 origin cutover를 함께 반영한다.
10. `frontend/src/components/baseline/RebaselineDialog.vue:1-85, 88-220`
    - one-line-first state, AI/manual actions, loading/late-response guard, success-only atomic field apply, editor reveal와 `[승인]` label/style을 구현한다.
11. `frontend/package.json:14-20`, `frontend/vitest.config.ts:4-11`
    - component interaction에 필요한 `@vue/test-utils`, `jsdom`과 대상 test environment를 최소 추가한다.
12. 새 `tests/test_llm_client.py`
    - MockTransport 기반 client unit scenarios를 구현한다.
13. `tests/test_server.py:1-55`와 기존 TestClient 구간 뒤
    - injected client를 사용한 generate-draft HTTP integration scenarios를 추가한다.
14. `frontend/tests/store.test.ts:1-100` 및 baseline draft 관련 describe
    - generate success/failure/pending/late response와 origin mapping을 추가한다.
15. 새 `frontend/tests/rebaseline-dialog.test.ts`
    - 실제 component mount로 one-line-first, loading, success populate/edit/approve, failure preservation을 검증한다.

## 7. 구현 순서와 cutover 경계

1. §8 CF-1과 CF-3을 먼저 수행해 선행 sparse 경계와 origin 전달 결손을 확정한다.
2. LLM prompt/model/attempt DTO 및 client를 구현하고 `tests/test_llm_client.py`로 transport policy를 고정한다.
3. FastAPI request/response/error contract와 injected client route를 연결하고 HTTP integration을 추가한다. 이 단계까지 DB/SSE mutation은 없어야 한다.
4. frontend contract validator/client/store action을 한 번에 연결한다. backend response와 frontend validator의 required field를 optional alias 없이 동일하게 유지한다.
5. `RebaselineDialog.vue`를 one-line-first UX로 전환하고 component tests를 추가한다.
6. origin이 CF-3에서 결손이면 Baseline submit backend/frontend DTO와 모든 caller/test fixture를 clean cutover해 `llm_draft`/`user`를 정직하게 전달한다.
7. focused tests와 disposable actual-service/browser smoke를 수행하고 production frontend bundle을 재build한다. source와 stale `src/comic_new/static` bundle이 공존한 상태를 verifier handoff로 넘기지 않는다.

중간 상태를 배포 대상으로 취급하지 않는다. backend가 새 response를 내는데 frontend가 cast-only old contract를 소비하거나, UI가 AI 값을 보이는데 approval origin을 잘못 저장하는 부분 cutover는 금지한다.

## 8. Conditional First Work

### CF-1 — BLOCK-10 runtime entry 보존

- `plan_anchor`: `PLAN-001 §1, §3.4, §9.4`
- `permitted_initial_work`: 구현 전 disposable project에서 empty/sparse 5-cut Baseline을 기존 `POST /api/baselines`로 승인하고 fresh snapshot을 읽은 뒤, 준비된 cut 하나만 enqueue 가능한지 관찰한다. live image generation 자체는 시작하지 않아도 되며 DB/source를 수동 보정하지 않는다.
- `discriminating_observation`: sparse approval이 200이고 fresh snapshot에 ordered five structure/intents가 보존되며, single-cut enqueue가 다른 컷 준비 상태와 무관하게 target job만 만든다.
- `dependent_work_not_yet_permitted`: 이 결과가 refuted인 상태에서 BLOCK-11 UI를 “생성 후 한 번 승인으로 진행 가능”하다고 통합하거나 end-to-end acceptance를 주장하는 작업.
- `response_if_refuted`: BLOCK-11 mutation을 확대하지 않고 Main에게 BLOCK-10 regression evidence를 반환한다. 선행 Scope 복구/재검증이 끝나기 전 통합 handoff는 `BLOCKED`; 독립 LLM client/API 작업만 안전하게 계속할 수 있다.

### CF-2 — 실제 OpenCodex model/capability 경계

- `plan_anchor`: `PLAN-001 §1.1, §4.3, §9.3`
- `permitted_initial_work`: client unit/HTTP contract 구현 후 사용자 허용 local 환경에서 실제 `http://127.0.0.1:10100/v1`로 최소 1-cut brief를 요청한다. 먼저 primary payload를 관찰하고, fallback 검증은 primary를 파괴하거나 서비스 설정을 바꾸지 않는 허용된 controlled 방법이 있을 때만 수행한다.
- `discriminating_observation`: endpoint가 canonical primary model, `reasoning_effort: high`, JSON object response format을 수용하고 validated draft/provenance가 돌아온다. controlled primary failure가 가능하면 exact fallback `gpt-5.6-luna`, `max` 및 attempt 순서를 확인한다.
- `dependent_work_not_yet_permitted`: mock response만으로 실제 OpenCodex availability/모델 결속/one-line utility 성공을 선언하거나 다른 Gemini/Luna alias를 자동 탐색·대체하는 작업.
- `response_if_refuted`: transport payload shape 문제면 client method/Plan을 수정해 fresh review한다. canonical model identifier/effort가 실제 서비스에서 불가하면 임의 alias로 바꾸지 않고 Main에게 Thesis/Transition product means 결정을 반환한다.

### CF-3 — AI prompt origin 전달

- `plan_anchor`: `PLAN-001 §5.2~5.3, §7 step 6`
- `permitted_initial_work`: current `POST /api/baselines` request, `approve_structural_baseline()` origin resolver 및 fresh snapshot을 bounded source trace/기존 focused test로 확인한다. product DB를 변경하지 않는다.
- `discriminating_observation`: AI-generated prompt를 별도 request provenance 없이 저장해도 authoritative snapshot이 정직하게 `llm_draft`로 판정할 결정적 근거가 있으면 existing path를 사용한다. 현재처럼 모든 non-empty submit을 `user`로 판정하면 결손이다.
- `dependent_work_not_yet_permitted`: AI 값을 `user`로 저장한 채 Acceptance D/provenance truth를 충족했다고 주장하거나 origin을 optional/default로 숨기는 작업.
- `response_if_refuted`: 이 Scope 안에서 Baseline request의 per-cut origin을 required로 확장하고 manual/AI/edit caller 전부를 migrate한다. 이는 Thesis의 직접 요구를 완성하는 shared interface cutover다. origin 정책 자체를 바꾸어야 한다면 Main/Thesis owner에게 반환한다.

## 9. 집중 테스트 계획

### 9.1 `tests/test_llm_client.py` — OpenCodexClient unit

`httpx.MockTransport` 또는 injected AsyncClient로 실제 async method를 실행한다. source text assertion은 쓰지 않는다.

1. **primary success:** 한 primary request만 발생하고 exact model/effort/response_format/messages가 전달된다. valid 5-cut JSON이 typed draft로 반환되며 fallback request는 0건이다.
2. **retryable primary success:** primary 첫 429와 두 번째 200에서 exactly 2 primary attempts, fallback 0, provenance order/status가 일치한다.
3. **fallback success:** primary non-retryable connection/invalid-response 또는 retry exhausted 뒤 fallback이 호출되고 valid result의 `selected_model`과 attempts가 실제 순서와 일치한다.
4. **fallback retry:** fallback 첫 5xx, 두 번째 200만 허용한다. 429/모든 5xx 외 4xx는 same-model retry하지 않는다.
5. **both fail:** primary/fallback 최종 실패가 `DraftGenerationError`와 모든 sanitized attempts를 보존한다. raw body secret/trace는 public message에 없다.
6. **hard budget:** 작은 injected budget/clock으로 remaining budget 이후 request와 retry sleep이 추가되지 않고 wall-clock cap을 넘기지 않는지 검증한다.
7. **schema honesty:** malformed JSON, missing field, wrong count, duplicate draft_id/order, whitespace role/beat/prompt, relative-reference/non-typesetting prompt는 성공이 아니며 다음 model로 넘어간다. 양쪽 invalid면 partial cut을 반환하지 않는다.
8. **dialogue semantics:** empty dialogue는 valid, non-string은 invalid다.
9. **custom cut count:** `cut_count=1`과 다른 positive count에서 exact count/order가 통과한다. 0/bool/non-int는 request 전에 거절된다.
10. **cancellation:** task cancellation이 generic provider failure로 변환되지 않고 호출자에게 전파된다.

### 9.2 `tests/test_server.py` — HTTP integration

실제 `create_app()`/lifespan/TestClient와 injected deterministic draft client를 사용한다.

1. valid `{"topic":"..."}`는 200, default `cut_count=5`, exact ordered cuts/source brief/provenance를 반환한다.
2. explicit positive `cut_count`는 client에 그대로 전달되고 response count가 일치한다. 이는 draft API만 검사하며 DB active cut 수를 바꾸지 않는다.
3. empty/whitespace topic은 400 `validation_error`; missing/wrong-type body는 기존 422 contract다.
4. connection/timeout/budget-only final error는 503 `draft_service_unavailable`; upstream/schema final error는 502 `draft_generation_failed`; details는 sanitized attempts만 포함한다.
5. success와 failure 각각 전후 `store.snapshot()`/authority revision/baseline/jobs/authorization을 대조해 변경 0, SSE authoritative publish 0임을 확인한다.
6. client exception 후 같은 app의 snapshot/Baseline endpoint가 계속 응답하여 server crash가 없음을 확인한다.
7. shutdown-settling 상태에서 새 draft work가 503이고 client 호출이 시작되지 않는지 확인한다.

mock client는 HTTP route/error mapping의 ancillary dependency double이며 실제 OpenCodex 성공 증거로 사용하지 않는다.

### 9.3 `frontend/tests/store.test.ts`

1. `generateBaselineDraft(topic)`이 `POST /api/baselines/generate-draft`에 topic과 `cut_count: 5`를 보낸다.
2. pending 동안 기존 `drafts.baseline`은 그대로다. valid response 후에만 exact role/beat/prompt/dialogue local draft가 atomic하게 교체되고 자동 `POST /api/baselines`는 0건이다.
3. 400/502/503/network/invalid-success response에서 action은 `null`, 기존 draft byte-equivalent, server snapshot 불변, alert toast가 남는다.
4. response 전 새 local edit/version이 생기면 late response가 이를 덮어쓰지 않는다.
5. AI output의 initial origin은 `llm_draft`, 해당 prompt를 사용자가 수정하면 `user`, untouched cut은 `llm_draft`를 유지한다(CF-3 결과 반영).
6. AI success 뒤 `saveBaselineDraft()`를 명시 호출했을 때만 Baseline request가 발생하고 accepted response에서만 draft가 clear된다. 400/409/422/5xx에는 유지된다.

### 9.4 `frontend/tests/rebaseline-dialog.test.ts`

`@vue/test-utils` + jsdom에서 실제 component를 mount하고 Pinia/store API만 제어한다.

1. 신규 Baseline open 시 topic control과 AI/manual actions가 먼저 보이고 20개 cut fields는 접혀 있다.
2. empty click은 API를 호출하지 않고 명확한 안내를 보인다.
3. pending promise 동안 button text/disabled/aria-busy가 맞고 duplicate click은 request 하나만 만든다.
4. success 시 다섯 card가 한 번에 나타나 각 role/beat/dialogue/prompt가 response와 일치한다. 사용자가 한 field를 수정하고 `[승인]`하면 수정값이 submit된다.
5. AI success만으로 dialog가 닫히지 않는다. Baseline save pending/실패에는 열려 있고, accepted save true에서만 닫힌다.
6. AI failure에서는 사전 source/cut values와 editor visibility가 동일하며 toast/manual retry path가 보인다.
7. existing Baseline 또는 browser draft open은 editor를 즉시 보여 주고 값을 초기화하지 않는다.
8. request 중 local input 변경 뒤 late success는 fields를 덮어쓰지 않는다.

## 10. 구현자 Self-check와 최종 Acceptance Readback

### 10.1 정적/보조 경계

- focused backend: `tests/test_llm_client.py` 및 `tests/test_server.py`의 BLOCK-11 scenarios.
- focused frontend: `frontend/tests/store.test.ts`, `frontend/tests/rebaseline-dialog.test.ts`, TypeScript contract check.
- production frontend build 후 `src/comic_new/static/index.html`의 hashed assets가 실제 새 bundle을 가리키는지 preflight한다.
- 이 결과는 retry/DTO/component behavior의 증거이나 실제 OpenCodex/사용자 경로의 대체 증거가 아니다.

### 10.2 최소 실제 사용자 경로

1. disposable project와 production server/static bundle을 기동하고 browser에서 Baseline 없는 Studio를 연다.
2. dialog 첫 화면에서 one-line topic과 AI action이 우선 노출되고 상세 20 fields가 접혀 있는지 확인한다.
3. 실제 local OpenCodex로 topic을 제출한다. network에서 `/v1/chat/completions` payload의 canonical model/effort를 확인하고 UI의 5 cuts와 API response/provenance를 대조한다.
4. AI success 직후 fresh `GET /api/studio/snapshot`의 authority revision/baseline/jobs가 요청 전과 동일함을 확인한다.
5. cut prompt/dialogue 하나를 수정하고 `[승인]`한다. 응답 전 dialog가 열려 있고 성공 후만 닫히며 fresh snapshot의 structure/intents/origin이 최종 수정값과 일치하는지 확인한다.
6. OpenCodex를 허용된 방법으로 unavailable하게 한 별도 disposable run에서 502/503 toast, topic 및 기존 cut edits 보존, manual editor/retry 가능, DB snapshot 불변을 확인한다. 서비스 설정을 파괴하거나 shared process를 무단 중지하지 않는다.
7. Baseline save를 controlled 400/409/5xx로 실패시켜 dialog와 local edits가 남고 수정 후 재시도가 가능한지 확인한다.
8. draft generation 전후/실패 후 generation jobs/authorization/canonical assets가 변하지 않았고, 기존 CAS/STOP/release tests가 그대로 통과하는지 확인한다.

### 10.3 Acceptance 매핑

- **A. OpenCodex LLM 통합 및 자동 폴백 체인:** §4.1~4.3, §8 CF-2, §9.1, §10.2 step 3. 실제 model/attempt 순서와 validated schema가 판정 경계다.
- **B. POST `/api/baselines/generate-draft` 계약:** §4.4, §9.2, §10.2 step 3~4. HTTP 200 validated response와 authority side effect 0을 함께 확인한다.
- **C. 장애 시 정직한 실패 및 수동 입력 보존:** §4.3~4.4, §5.2~5.3, §9.2~9.4, §10.2 step 6~7. 502/503와 browser local values/DB 불변이 판정 경계다.
- **D. One-Click Studio UX:** §5, §9.3~9.4, §10.2 step 1~5. one-line-first → editable five-cut proposal → 별도 승인 → fresh Baseline snapshot을 실제 browser에서 연결한다.
- **E. 4대 인과 불변식 보존:** §2, §4.4, §9.2 step 5, §10.2 step 4/8. draft route가 authority writer를 호출하지 않는 것과 기존 CAS/STOP/revoke/readback 회귀를 함께 확인한다.

### 10.4 authoritative success와 한계

- Draft Generated 성공은 actual OpenCodex response가 schema/semantic validation을 통과하고 original brief + full attempt provenance와 함께 API/UI에 나타날 때다.
- Baseline Approved 성공은 AI draft 성공이 아니라 사용자의 별도 승인 후 fresh server snapshot에 최종 edited structure/intents/origin이 조회될 때다.
- 테스트 통과, HTTP acceptance, 화면 field populate만으로 OpenCodex 실제 availability나 Baseline authority 성공을 선언하지 않는다.
- fallback 실제 유도 권한이 없으면 primary real success + mocked fallback policy까지만 observed이고 fallback live behavior는 명시적 evidence limit로 verifier에게 넘긴다.

## 11. 실패·중단·재개·부분 효과

- topic validation 실패: OpenCodex 호출 0, local/authority state 변화 0.
- primary failure: retryable status만 한 번 재시도하고 fallback으로 진행한다. partial primary JSON은 버린다.
- fallback failure/budget exhaustion: 502/503, local UI fields 및 DB 불변, loading reset, manual/retry 가능.
- request cancellation/dialog close: client cancellation은 전파하고 response를 apply하지 않는다. 외부 OpenCodex 호출의 cancellation이 remote 계산 종료를 보장한다고 주장하지 않는다.
- late/duplicate UI response: request token + local edit version이 current일 때만 atomic apply한다. 오래된 response는 폐기하고 authority mutation을 만들지 않는다.
- Baseline save failure: dialog/local draft 유지, 자동 재승인 없음. 409는 fresh snapshot과 local draft를 기존 store contract대로 구분한다.
- server interruption: draft는 DB에 쓰지 않으므로 재시작 후 자동 복구/승인하지 않는다. browser local draft는 existing ownership에 따라 보존한다.
- unexpected schema response: 추측 repair 없이 attempt failure; 다음 canonical fallback 또는 최종 정직한 실패다.
- cleanup: disposable server/browser/mock transport를 종료하고 temp project를 제거한다. throwaway script나 raw provider response/secret log를 repository에 남기지 않는다.

## 12. 구현 재량과 재검토 반환 조건

구현자는 private helper 이름, Pydantic class 배치, equivalent CSS layout, test fixture 이름처럼 관찰 계약을 바꾸지 않는 내부 선택을 할 수 있다. 다음은 material method 변경이므로 해당 구현을 멈추고 이 Plan을 개정한 뒤 fresh independent Plan Review를 받아야 한다.

1. canonical OpenCodex endpoint/model/reasoning/retry/timeout/150초 budget 변경.
2. `cut_count`를 draft API가 아니라 authoritative DB/membership으로 확장하거나 fixed-five frontend approval을 부분 N-cut으로 바꾸는 것.
3. malformed/partial output repair, 추가 모델, 무한/추가 retry 또는 client-side retry 도입.
4. draft generation이 store/SSE/approval/enqueue authority를 직접 변경하도록 만드는 것.
5. late response overwrite, save-before-review 또는 AI success를 승인 성공으로 간주하는 것.
6. prompt provenance ownership/전달 전략을 §8 CF-3과 다르게 바꾸는 것.
7. 실제 OpenCodex/readback 대신 mocks를 final acceptance 증거로 대체하는 것.

제품 의미, 모델 수단 또는 BLOCK 전환 순서를 바꿔야 하면 Plan이 결정하지 않고 Main에게 Thesis/Transition/Scope owning source 수정으로 반환한다. 이 문서는 실행 방법이지 구현·검증·완료 판정이 아니다. exact Scope/Plan bytes에 대해 independent Plan Reviewer가 모든 Acceptance, conditional starts, model policy, origin truth, failure preservation과 authority side-effect 반례를 검토해 `ADMIT`한 뒤에만 구현을 시작한다. Scope `done`은 별도 semantic verification과 Coverage 후 Main만 기록한다.
