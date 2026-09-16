# PLAN-001 — BLOCK-05 Release Authorization & Destination Readback 실행 방법

- Plan role: exact ready Scope의 구현·자기점검 방법. 제품 의미나 Acceptance를 임의로 추가하거나 축소하지 않는다.
- Project Root: `/home/user01/project/comic_new`
- Scope: `/home/user01/project/comic_new/docs/planning/work/release-destination-readback/SCOPE.md`
- Selected transition: `BASELINE-001`의 `BLOCK-05 — Release Authorization & Destination Readback`만
- Prepared against commit: `512c78d152f5ebdacf406176dd6348ca1fab2c1f`
- Prepared working tree: 이 revision 전 `git status --short` 상 `?? docs/planning/work/release-destination-readback/` 외 변경 없음. 제품 source/config/DB 상태를 임의 수정하지 않았다.
- Repository investigation: None supplied; 아래 current source 직접 판독 및 선행 블록 검증 기록을 근거로 사용했다.
- Remote retrieval: 0회
- Visual concept/image generation: 생략. 본 Scope는 백엔드 영속 승인 생명주기, All-or-Nothing 게이트, 정본 조판 보존 PNG Export 파이프라인, Blogger 전달 어댑터 및 목적지 Readback을 완결하는 작업이며 concept image는 부적절하다.

---

## 1. 결속 권위, 현재 바이트와 진입 조건

### 1.1 원본과 해시

| 분류 | 원본 | 실제 SHA-256 | 적용 범위 |
|---|---|---|---|
| Product Authority | `docs/planning/product-thesis/web-comic-studio/THESIS-001.md` (`THESIS-001`) | `74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63` | 유일한 제품 의미, 5-Truth Chain, INV-1~8, §6.6 서빙 배포, §7 거짓 성공(Banned False Successes 1-12), §8 readback |
| Scope | `docs/planning/work/release-destination-readback/SCOPE.md` | `36ed6b7823d25163a8ac42843b25cd636808c2979c8e550590181470febd6961` | ready BLOCK-05 Outcome, Acceptance A-G, External Conditions/Non-Goals |
| Transition Authority | `docs/planning/adaptive/BASELINE-001.md` | `5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c` | selected `BLOCK-05`, Exit 1-33, 모든 적용 INV/PATH, Gate 1~4 실측 차단 조건 |

Canonical validator 사전 실행:

```text
python3 /home/user01/.omp/agent/skills/scope-shaper/tools/validate_scope.py --json /home/user01/project/comic_new/docs/planning/work/release-destination-readback/SCOPE.md
=> schema iis-scope/v1, status ready,
   product_authorities = THESIS-001 위 해시,
   transition_authorities = BASELINE-001 위 해시
```

독립 Plan Review 시작 전과 구현 handoff 직전에 세 원본 해시와 Scope `Status: ready`를 다시 비교한다. 해시 변화는 자동 승인/거절이 아니라 이 방법의 currentness를 중단하고 해당 변경 소유자에게 재검토시키는 신호다.

### 1.2 이 Plan이 얻어야 할 결과와 넘지 않을 경계

창작자가 눈으로 확인·승인한 단일 Canonical Review Artifact를 All-or-Nothing 방식으로 외부화하고, 로컬 권위와 외부 목적지 진실의 경계를 끝까지 보존하여 5-Truth Chain을 완결한다.
2차 릴리즈 승인은 화면에 표시된 exact `artifact_id`와 full content SHA-256 hash에 결속되어 SQLite에 영속화되며, 서버 재시작 후에도 보존된다.
승인 이후 말풍선 텍스트 한 글자, 기하 좌표, 컷 간 간격(Gap), 스타일, 시각 프롬프트/대사 intent, Structural Baseline, 새로운 realization commit 등 수신자가 인지할 수 있는 어떠한 변경이라도 시스템에 수용되는 즉시 기존 Release Authorization은 원자적으로 취소(Revoke)된다.
수정된 내용을 과거 승인으로 발행하거나, 승인되지 않은 조판을 외부화하는 우회로는 존재하지 않는다.

릴리즈는 정확히 5개 컷 모두가 Current이고 승인된 Review Artifact와 일치할 때만 허용된다. 1개 컷이라도 STALE이거나, 컷 자산 중 하나라도 읽을 수 없거나 결측되면 4컷짜리 불완전한 부분 릴리즈를 생성하지 않고 전체 릴리즈가 명시적 실패로 종료된다.
PNG Export는 승인된 artifact를 소스로 사용하여 텍스트 재줄바꿈, 폰트 재계산, 말풍선 이동, 컷 재배치 없이 composition identity를 보존하며 출력 바이트를 생성한다.
Blogger 전달 역시 승인된 artifact를 소스로 사용하며, 로컬 DB에 전달 시도를 기록(`unknown`)한 뒤 외부 서비스의 권위 있는 응답을 통해 고유 게시물 ID와 실제 접근 가능한 목적지 URL을 확인(Readback)했을 때만 `confirmed_success`로 전이한다.
통신 장애, 타임아웃, 응답 누락 발생 시에는 로컬 요청 성공만으로 발행 성공을 날조하지 않고 `unknown` 상태를 유지하며 UI에 '발행 결과 미확인'을 정직하게 고지한다.

**비범위 (Non-Goals)**:
- Blogger 이외의 추가 외부 배포처(Twitter, Instagram, Webtoon 등)
- 상세 generation/delivery audit log 전용 뷰어
- 멀티유저 협업, 원격/클라우드 데이터베이스, 분산 큐, SSR
- 임의 N-cut 지원(제품 경계 밖, exactly 5 cuts 유지)
- 하류 단계에서의 독자적 레이아웃 보정이나 WYSIWYG 위반 재조판
- 본 Scope 수준에서의 전체 프로젝트 Transformation Outcome 최종 완료 선언(Main 호출자 소유)

---

## 2. Grounding Ledger

### 2.1 EXISTING — 현재 실제 권위와 인터페이스

1. **SQLite 스키마 및 권위 테이블** — `src/comic_new/schema.sql:117-151`
   - `release_authorizations` 테이블: `authorization_id` (PK), `artifact_id` (FK), `artifact_content_hash`, `authorized_authority_revision`, `revoked_authority_revision`, `created_at`, `revoked_at`.
   - 부분 고유 인덱스 `idx_active_release_authorization` on `((1)) WHERE revoked_authority_revision IS NULL`을 통해 활성 승인은 시스템 전체에서 단 1건만 존재함을 DB 레벨에서 강제한다.
   - `delivery_attempts` 테이블: `attempt_id` (PK), `kind` CHECK IN (`'png'`, `'blogger'`), `authorization_id` (FK), `artifact_id` (FK), `request_id`, `outcome` CHECK IN (`'unknown'`, `'confirmed_success'`, `'confirmed_failure'`), `destination_id`, `destination_url`, `evidence_json`, `observed_authority_revision`, `created_at`, `updated_at`.
   - `CHECK (outcome != 'confirmed_success' OR (destination_id IS NOT NULL AND destination_url IS NOT NULL AND evidence_json IS NOT NULL))` 제약 조건을 통해 목적지 정보와 증거 없는 거짓 성공을 DB 레벨에서 거부한다.

2. **단일 트랜잭션 권위 및 릴리즈 승인/취소 메서드** — `src/comic_new/store.py`
   - `_revoke_active_authorization(con, new_rev, now_iso)` (`:298-311`): 활성 승인의 `revoked_authority_revision`과 `revoked_at`을 원자적으로 갱신한다.
   - 모든 수신자 인지 가능 mutation에서 `_revoke_active_authorization`이 단일 트랜잭션 내에 강제됨:
     - `approve_structural_baseline` (`:600`)
     - `accept_cut_intent` (`:643`)
     - `accept_composition` (`:686`)
     - `commit_candidate` (`:1061`)
   - `authorize_release(...)` (`:1321-1391`): `expected_authority_revision`, `authorization_id`, `artifact_id`, `content_hash`를 검증하고, artifact 등록 여부, hash 일치, 현재 composition revision 일치, 5컷 Current 여부, artifact cut closure 일치를 단일 트랜잭션에서 전수 확인 후 `release_authorizations`에 등록하고 `authority_revision`을 증가시킨다.
   - `start_delivery_attempt(...)` (`:1393-1457`): 활성(미취소) 승인 확인, 5컷 Current 및 artifact closure 일치를 재검증하고 초기 `outcome='unknown'`으로 `delivery_attempts` 레코드를 생성한다.
   - `record_delivery_observation(...)` (`:1459-1504`): 전달 관찰 결과를 기록하며, `confirmed_success` 시 `destination_id`, `destination_url`, `evidence`를 필수 검증하고 DB에 갱신한다.
   - `snapshot()` (`:466-544`): 활성 승인(`release_authorization.active`), 취소 이력(`release_authorization.history`), 전체 전달 시도(`delivery_attempts`)를 정직하게 분리하여 반환한다.

3. **Canonical Review Artifact 조판 및 무결성 검증** — `src/comic_new/composition_service.py:53-485`, `src/comic_new/composition.py:345-613`
   - `CompositionService.materialize(...)`: 5컷 Current 검증, PIL 기반 고정 `1024×7680` 캔버스 조판, 불변 PNG 저장 및 `review_artifacts` / `artifact_cuts` 원자적 등록.
   - `CompositionService.read_artifact(artifact_id)` (`:345-485`): DB 등록 검증, 디스크 파일 존재 검증, SHA-256 해시 검증, PIL 디코드(1024×7680, RGB, PNG), PNG 텍스트 청크 메타데이터 검증을 수행하는 단일 정본 판독기.

4. **FastAPI 서버 및 현재 엔드포인트** — `src/comic_new/server.py`
   - `POST /api/review-artifacts/{artifact_id}/authorize` (`:1008-1038`): 검토 화면에서 호출되는 승인 handoff 엔드포인트. artifact 조회, hash 일치 검증, `store.authorize_release` 호출 및 fresh snapshot 반환.
   - `GET /api/studio/snapshot` (`:847-849`): 도메인 스냅샷 DTO 제공.
   - `GET /api/events` (`:1040-1069`): SSE 스냅샷 브로드캐스트.
   - 현재 누락: PNG Export API 및 Blogger Delivery API.

5. **CLI 진입점** — `src/comic_new/cli.py`
   - 현재 `init`, `snapshot`, `generate`, `run-generation`, `cancel-generation`, `stop-generation`, `serve` 명령 존재.
   - 현재 누락: `export-png`, `release-blogger` 명령.

6. **Studio Vue 3 프론트엔드** — `frontend/src/`
   - `CanonicalReviewDialog.vue` (`:1-259`): 창작자가 화면에 표시된 exact `artifact_id`와 `displayedByteHash`를 눈으로 확인하고 승인 버튼(`store.authorizeReview()`)을 클릭.
   - `TruthSummary.vue` (`:17-31`): `authLabel` (`승인됨` / `미승인`), `deliveryLabel` (`미시도`, `전달 성공`, `전달 실패`, `결과 미확인`)을 독립 차원으로 분리 표시.
   - `studio.ts` (`:630-654`): `authorizeReview` 액션 구현 완료.
   - 현재 누락: 내보내기/발행 트리거 액션 및 목적지 URL/결과 미확인 상세 고지 연동.

### 2.2 PROPOSED — 최소 신규 경계

1. **통합 릴리즈 서비스 모듈 (`src/comic_new/delivery.py`)**
   - 불필요한 계층 분립 없이, 단일 모듈 안에 릴리즈 권위 검증, All-or-Nothing 물리 자산 무결성 preflight, 정본 조판 보존 PNG Export, Blogger 전달 어댑터 인터페이스, 통제된 테스트 하네스(`ControlledBloggerAdapter`), 그리고 Destination Readback 판정 로직을 응집하여 구현한다.
   - `DeliveryService`:
     - `export_png(expected_authority_revision: int, output_path: Path, authorization_id: str | None = None) -> DeliveryResult`
     - `deliver_blogger(expected_authority_revision: int, blog_id: str, title: str, adapter: BloggerAdapter, authorization_id: str | None = None) -> DeliveryResult`
     - `preflight_release(authorization_id: str | None = None) -> tuple[dict, MaterializedArtifact]`

2. **Blogger 전달 어댑터 계약 및 결정론적 테스트 하네스 (`src/comic_new/delivery.py`)**
   - `BloggerAdapter` (Protocol):
     - `publish(blog_id: str, title: str, artifact_png_bytes: bytes, filename: str) -> BloggerPublishResult`
   - `ControlledBloggerAdapter`:
     - 외부 네트워크나 자격 증명 없이 결정론적 모드(`success`, `timeout`, `disconnect`, `auth_failure`, `bad_request`)를 주입할 수 있는 표준 하네스.
     - `success` 모드: 고유 `post_id` ("post-blogger-XXXX")와 정규 `destination_url` ("https://comic.blogspot.com/2026/09/episode-1.html"), 원시 응답 JSON을 반환하고 실제 HTTP GET 또는 자체 목적지 접근 검증을 수행.
     - `timeout` / `disconnect` 모드: `BloggerTransportTimeoutError`를 발생시켜 로컬 결과가 정직한 `unknown`으로 유지되도록 유도.
     - `auth_failure` / `bad_request` 모드: `BloggerAuthoritativeError`를 발생시켜 로컬 결과가 `confirmed_failure`와 오류 증거로 전이되도록 유도.

3. **FastAPI 서버 신규 릴리즈 엔드포인트 (`src/comic_new/server.py`)**
   - `POST /api/release/export-png`:
     - Request: `{ "expected_authority_revision": int, "output_path": str | null }`
     - 권위 검증 -> All-or-Nothing 검증 -> 정본 PNG 파일 생성 -> 목적지 readback -> delivery_attempts 기록 -> fresh snapshot 반환.
   - `POST /api/release/blogger`:
     - Request: `{ "expected_authority_revision": int, "blog_id": str | null, "title": str | null }`
     - 권위 검증 -> All-or-Nothing 검증 -> start_delivery_attempt (`outcome='unknown'`) -> 어댑터 호출 -> 성공 시 `confirmed_success` + 목적지 URL/ID 기록, 통신 두절 시 `unknown` 유지, 거절 시 `confirmed_failure` 기록 -> fresh snapshot 반환.

4. **CLI 신규 릴리즈 명령어 (`src/comic_new/cli.py`)**
   - `comic-new export-png <project_dir> <output_file>`
   - `comic-new release-blogger <project_dir> [--blog-id <id>] [--title <title>]`

5. **프론트엔드 릴리즈 인터랙션 및 결과 고지 (`frontend/`)**
   - `contracts.ts` & `client.ts`: `postExportPng`, `postBloggerRelease` API 함수 추가.
   - `studio.ts`: `exportPng`, `releaseBlogger` 액션 추가. 미저장 로컬 드래프트 존재 시 릴리즈 요청 원천 차단(`canRelease` 가드).
   - `StudioHeader.vue` / `CanonicalReviewDialog.vue`: 활성 승인 존재 시 'PNG 내보내기' 및 'Blogger 발행' 액션 제공.
   - `TruthSummary.vue` / 전용 상태 모달: 전달 성공 시 실제 목적지 URL로 이동 가능한 링크 노출, 미확인 시 경고 스타일과 함께 '발행 결과 미확인 (Unknown)' 고지.

### 2.3 UNRESOLVED — 구현/검증에서 확인할 실제 사실

1. **CFW-1: Blogger Adapter 어댑터 시그니처 및 예외 계층과 SQLite 트랜잭션 분리 검증**
   - 외부 네트워크 I/O(블로거 호출 및 타임아웃 대기)는 SQLite write lock 트랜잭션 외부에서 수행되어야 한다. `start_delivery_attempt`로 `unknown` 상태를 커밋한 뒤, 외부 I/O를 수행하고, 그 결과에 따라 `record_delivery_observation` 트랜잭션을 새로 열어야 DB 락 기아 현상이나 프로세스 블로킹이 발생하지 않는다. 이 비동기/스레드 I/O 분리 경계를 구현 첫 단계에서 실측한다.
2. **CFW-2: PNG Export 시 조판 불변 바이트 동일성(Byte Identity) 검증**
   - 승인된 Review Artifact PNG 파일을 Export할 때 Pillow로 다시 열어 저장하면 메타데이터나 압축 레벨 차이로 바이트 해시가 달라질 위험이 있다. 따라서 Export는 `shutil.copyfile` 또는 원자적 바이트 복사(`read_bytes` -> `atomic_write`)를 사용하여 바이트 단위 해시 일치(`hashlib.sha256(export_bytes) == artifact_content_hash`)를 100% 보장해야 한다. 이 무손실 파이프라인을 첫 단위 테스트로 실측 검증한다.

---

## 3. 고정 Wire Contract 및 인터페이스 규격

### 3.1 API 엔드포인트 규격

```ts
// POST /api/release/export-png
export interface ExportPngRequest {
  expected_authority_revision: number
  output_path?: string // 생략 시 project_dir / exports / comic-<artifact_id>.png
}

export interface ExportPngResponse {
  attempt_id: string
  kind: 'png'
  authorization_id: string
  artifact_id: string
  output_path: string
  content_hash: string
  bytes_written: number
  snapshot: StudioSnapshotDTO
}

// POST /api/release/blogger
export interface BloggerReleaseRequest {
  expected_authority_revision: number
  blog_id?: string
  title?: string
}

export interface BloggerReleaseResponse {
  attempt_id: string
  kind: 'blogger'
  authorization_id: string
  artifact_id: string
  outcome: 'confirmed_success' | 'unknown' | 'confirmed_failure'
  destination_id: string | null
  destination_url: string | null
  error_message?: string
  snapshot: StudioSnapshotDTO
}
```

에러 응답은 기존 표준 `ApiErrorDTO` 형식을 그대로 사용한다:
- `409 authorization_revoked`: 활성 승인이 없거나 취소됨.
- `409 realization_stale`: 1개 이상의 컷이 STALE임.
- `409 invalid_closure`: 컷 realization이 승인된 아티팩트 closure와 불일치.
- `409 draft_conflict`: 클라이언트에 미저장 드래프트가 존재함.
- `500 asset_missing`: 컷 canonical 자산 파일 결측 또는 손상.

### 3.2 CLI 규격

1. `comic-new export-png <project_dir> <output_file>`
   - 성공 시 stdout (JSON):
     ```json
     {
       "status": "success",
       "attempt_id": "delivery-...",
       "authorization_id": "authorization-...",
       "artifact_id": "artifact-...",
       "output_file": "/absolute/path/to/output.png",
       "content_hash": "...",
       "bytes_written": 1234567,
       "dimensions": [1024, 7680]
     }
     ```
   - 승인 부재, STALE, 파일 결측 시 stderr에 명시적 원인 출력 후 exit code `1`.

2. `comic-new release-blogger <project_dir> [--blog-id <id>] [--title <title>]`
   - 성공 시 stdout (JSON):
     ```json
     {
       "status": "confirmed_success",
       "attempt_id": "delivery-...",
       "authorization_id": "authorization-...",
       "post_id": "post-12345",
       "destination_url": "https://comic.blogspot.com/2026/09/episode-1.html"
     }
     ```
   - 결과 미확인(타임아웃 등) 시 stdout (JSON, exit code `1`):
     ```json
     {
       "status": "unknown",
       "attempt_id": "delivery-...",
       "message": "발행 결과 미확인: 외부 서비스 응답 타임아웃"
     }
     ```
   - 실패 시 stderr 출력 후 exit code `1`.

### 3.3 Blogger Adapter 및 결과 인터페이스

```python
from typing import Protocol, Any
from dataclasses import dataclass

@dataclass(frozen=True)
class BloggerPublishResult:
    post_id: str
    destination_url: str
    raw_response: dict[str, Any]

class BloggerTransportTimeoutError(Exception):
    """외부 네트워크 연결 단절, 타임아웃, 불완전 응답 발생 시."""
    pass

class BloggerAuthoritativeError(Exception):
    """외부 서비스에서 명시적으로 오류(401, 400 등)를 반환했을 때."""
    def __init__(self, status_code: int, message: str, details: Any = None) -> None:
        super().__init__(f"Blogger rejected request ({status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.details = details

class BloggerAdapter(Protocol):
    def publish(
        self,
        blog_id: str,
        title: str,
        artifact_png_bytes: bytes,
        filename: str,
    ) -> BloggerPublishResult: ...
```

---

## 4. 핵심 아키텍처 및 실행 흐름

### 4.1 릴리즈 승인 결속 및 재시작 영속성 (Acceptance A, Exit 1-4)

```text
[Browser ReviewModal]
  │  1. 화면에 표시된 exact artifact_id 및 displayedByteHash 확인
  ▼
[POST /api/review-artifacts/{id}/authorize]
  │  2. body.content_hash == artifact_row.content_hash 검증
  │  3. store.authorize_release(...) 단일 트랜잭션 진입
  ▼
[SQLite: release_authorizations]
  │  4. 기존 활성 승인 revoke (revoked_authority_revision = new_rev)
  │  5. 신규 승인 INSERT (revoked_authority_revision = NULL)
  │  6. authority_revision 단조 증가
  ▼
[Server Process Termination & Restart]
  │  7. comic-new serve 프로세스 SIGTERM 종료 후 재기동
  ▼
[Fresh Readback]
  │  8. GET /api/studio/snapshot 및 SQLite 직접 SELECT
  │  => active authorization 레코드 보존, delivery_attempts는 빈 목록 (Exit 1-4)
```

- **All-or-Nothing 승인 원칙**: 승인 시점에 5컷 중 1개라도 STALE이거나, artifact의 cut closure와 DB의 realization 상태가 단 1개라도 다르면 `RealizationIncompleteError` 또는 `InvalidArtifactClosureError`가 발생하여 롤백된다.
- **분리 원칙**: 승인 레코드가 생성되어도 `delivery_attempts` 테이블에는 어떠한 행도 추가되지 않으며, `published=true`와 같은 단순화 플래그를 두지 않는다.

### 4.2 수신자 인지 가능 변경 시 즉시 승인 취소 (Acceptance B, Exit 5-9, Gate 2)

```text
[활성 승인(ACTIVE AUTH) 존재]
  │
  ├─ 1. 말풍선 텍스트 1글자 수정 / 저장 ────► accept_composition(...) ────┐
  ├─ 2. 말풍선 좌표 (x, y, w, h) 수정 / 저장 ─► accept_composition(...) ────┤
  ├─ 3. 컷 간격 (gap_px) 수정 / 저장 ───────► accept_composition(...) ────┤
  ├─ 4. 말풍선 스타일 / 폰트 수정 / 저장 ────► accept_composition(...) ────┤ 원자적 트랜잭션 내
  ├─ 5. 단일 컷 대사/프롬프트 intent 수정 ───► accept_cut_intent(...) ──────┤ _revoke_active_authorization
  ├─ 6. 구조적 Baseline 승인 / 변경 ────────► approve_structural_baseline ┤
  └─ 7. 신규 realization 생성 커밋 ────────► commit_candidate(...) ──────┘
                                                                           │
  ▼                                                                        ▼
[SQLite: release_authorizations] ◄─────────────────────────────────────────┘
  UPDATE release_authorizations
  SET revoked_authority_revision = new_rev, revoked_at = now_iso
  WHERE revoked_authority_revision IS NULL;
  authority_revision = new_rev;
  COMMIT;
```

- **단일 트랜잭션 완결**: 위 7개 mutation은 각자의 데이터 갱신과 활성 승인 취소(`_revoke_active_authorization`)를 동일한 SQLite `BEGIN IMMEDIATE ... COMMIT` 트랜잭션 안에서 원자적으로 수행한다.
- **Bypass 불가능**: 승인이 취소되면 `snapshot()` 조회 시 `release_authorization.active`는 `None`이 되고, `history`에 취소 revision과 함께 보존된다.
- **클라이언트 미저장 드래프트 격리**: 브라우저 메모리의 미저장 편집은 서버의 활성 승인을 취소하지 않지만, 클라이언트에 미저장 드래프트가 남아있는 상태에서 릴리즈(PNG/Blogger)를 요청하면 서버 및 클라이언트 가드에 의해 즉시 거절된다.
- **재승인 강제**: 취소된 후 이전 artifact로 릴리즈를 시도하면 `AuthorizationRevokedError`로 차단되며, 반드시 새로운 Review Artifact 실체화와 새로운 2차 승인을 거쳐야만 릴리즈가 가능하다.

### 4.3 All-or-Nothing 릴리즈 무결성 게이트 (Acceptance C, Exit 10-14, Gate 1)

릴리즈(PNG Export 또는 Blogger Delivery) 수행 직전, `preflight_release`는 다음 5단계 무결성 검증을 엄격히 통과해야만 진입을 허용한다:

1. **Active Authorization 존재 검증**: 활성 승인이 존재하지 않거나 이미 취소되었으면 즉각 차단.
2. **5컷 전원 Current 검증**: 5개 컷 모두 `desired_revision != null`이고 `realized_revision == desired_revision`이어야 함. 단 1개라도 STALE이면 즉각 차단 (Gate 1).
3. **Artifact Cut Closure 100% 일치 검증**: 현재 5컷의 realization asset_id 및 revision이 승인된 Review Artifact의 closure와 완전히 동일해야 함.
4. **물리적 자산 파일 실체 검증**: 5개 컷의 canonical 이미지 자산 파일(`assets/realizations/cut-<id>/...png`)과 Canonical Review Artifact 파일(`assets/review-artifacts/<artifact_id>.png`)이 디스크에 실제 존재하고, 0바이트가 아니며, 정상적인 PNG 바이트여야 함. 단 1개 파일이라도 결측되거나 손상된 경우 전체 릴리즈 즉각 중단.
5. **무결성 실패 시 무조건 Abort**: 4컷짜리 불완전한 부분 PNG 파일이나 부분 Blogger 페이로드를 임시 디렉터리나 출력물로 생성하지 않고 예외 발생과 함께 종료.

### 4.4 정본 조판 보존 PNG Export 파이프라인 (Acceptance D, Exit 15-18)

1. **소스 정본 불변 원칙**:
   - 승인된 `Canonical Review Artifact` 파일 바이트를 그대로 읽어 들여 출력 파일로 안전하게 기록한다(`atomic_write` 또는 `shutil.copyfile`).
   - 텍스트 재줄바꿈(reflow), 폰트 재계산, 말풍선 좌표 재연산, 컷 재정렬을 수행하는 조판 라이브러리/코드를 Export 단계에서 일절 호출하지 않는다.
2. **원자적 파일 생성**:
   - 임시 파일(`.tmp-export-...`)에 기록 후 대상 경로로 원자적 이름 변경(`os.replace`)을 수행하여 불완전한 파일 노출을 방지한다.
3. **사후 Readback 검증**:
   - 생성된 출력 파일의 바이트를 다시 읽어 SHA-256 해시를 계산하고, 이것이 승인된 `artifact_content_hash`와 정확히 일치하는지 검증한다.
   - Pillow로 출력 파일을 열어 규격이 `(1024, 7680)`, 모드가 `RGB`, 포맷이 `PNG`임을 실측 확인한다.
4. **전달 시도 기록**:
   - `store.start_delivery_attempt(rev, attempt_id, kind='png', ...)`로 시작 (`outcome='unknown'`).
   - 파일 무결성 확인 완료 즉시 `store.record_delivery_observation(new_rev, attempt_id, outcome='confirmed_success', destination_id=filename, destination_url=file_uri, evidence={sha256, bytes})` 기록.

### 4.5 Blogger 전달 및 목적지 Readback (Acceptance E, Exit 19-23)

1. **페이로드 정본 불변 원칙**:
   - 승인된 `Canonical Review Artifact` 바이트를 직접 멀티파트 이미지 페이로드로 패키징한다. 브라우저 DOM 캡처나 HTML 재조판 렌더링을 거치지 않는다.
2. **트랜잭션 순서 및 락 격리**:
   - Step 1: `store.start_delivery_attempt(rev, attempt_id, kind='blogger', auth_id, req_id)`를 호출하여 DB에 `outcome='unknown'` 상태를 먼저 원자적으로 커밋한다.
   - Step 2: DB 커밋 완료 후 트랜잭션 락이 없는 상태에서 `BloggerAdapter.publish(...)`를 호출하여 외부 HTTP 통신을 수행한다.
   - Step 3: 어댑터 응답에 따라 별도의 트랜잭션으로 `store.record_delivery_observation(...)`을 호출한다.
3. **목적지 Readback (Destination Readback)**:
   - 어댑터로부터 반환된 `post_id` (고유 게시물 번호)와 `destination_url` (실제 접근 가능한 퍼블릭 URL)을 확인한다.
   - `ControlledBloggerAdapter` 또는 실제 어댑터는 해당 URL에 대해 Readback(HTTP GET 등 접근성 검증)을 수행하여 목적지가 실제로 존재함을 증명한다.
   - 확인 성공 시 `store.record_delivery_observation`에 `outcome='confirmed_success'`, `destination_id=post_id`, `destination_url=destination_url`, `evidence=raw_response`를 기록한다.
4. **독립 진실 보존**:
   - 로컬 릴리즈 승인 필드(`release_authorizations`)와 외부 전달 결과(`delivery_attempts.outcome`)는 엄격히 분리되며, 하나의 boolean 필드로 축약되지 않는다.

### 4.6 응답 불명확 시 정직한 Unknown 유지 (Acceptance F, Exit 24-29, Gate 4)

1. **통신 장애 및 타임아웃 주입 시험**:
   - 외부 Blogger 요청 전송 후 응답 수신 단계에서 네트워크 단절(`socket.error`), 타임아웃(`TimeoutError`), 또는 HTTP 504/불완전 응답을 강제 주입한다.
2. **로컬 상태 불변**:
   - 전달 시도 결과는 Step 1에서 기록된 `unknown` 상태를 그대로 유지하며, 절대 `confirmed_success`나 `confirmed_failure`로 멋대로 단정하지 않는다.
3. **UI 및 스냅샷 정직 고지**:
   - 스냅샷 조회 시 최신 전달 시도의 outcome은 `'unknown'`으로 반환된다.
   - Studio Shell 헤더 및 상태 요약(`TruthSummary.vue`)은 '전달 성공'으로 속이지 않고 '발행 결과 미확인 (Unknown)'으로 정직하게 사용자에게 고지한다 (Gate 4).
4. **명시적 거절 시 Confirmed Failure**:
   - 외부 서비스가 401 Unauthorized, 400 Invalid Payload 등 권위 있는 오류 응답을 확정 반환한 경우에만 `confirmed_failure`로 전이하고 오류 증거를 기록한다.

### 4.7 4대 Counterexample Gate 종단 실측 차단 구조 (Acceptance G, Exit 30-33)

- **Gate 1 (Currency Gate)**: 5컷의 이전 완성 픽셀이 디스크에 모두 존재하더라도, 1개 컷의 intent가 수정되어 `desired_revision != realized_revision` (STALE)인 경우 `preflight_release`가 릴리즈를 즉각 차단한다.
- **Gate 2 (Identity Gate)**: 2차 승인이 완료된 후 말풍선 텍스트 1글자 또는 Gap 1px이 수정되는 즉시 기존 승인은 원자적으로 취소(`revoked_authority_revision IS NOT NULL`)되며, 과거 승인 ID로 릴리즈 요청 시 `AuthorizationRevokedError`로 차단된다.
- **Gate 3 (Interruption Gate)**: 생성 도중 STOP 명령이 내려지거나 서버가 강제 재시작되어도 SQLite에 영속화된 최신 desired intent는 절대 롤백되지 않고 보존되며, 미완성 컷은 정직하게 STALE로 표시된다.
- **Gate 4 (External Truth Gate)**: 외부 서비스 응답이 타임아웃되거나 유실되었을 때, 로컬 요청 사실만으로 성공을 꾸며내지 않고 Destination Readback 완료 전까지 `Unknown` 상태를 유지한다.

---

## 5. 구현 순서 및 세부 변경점

### Step 1: 코어 릴리즈 & 전달 엔진 모듈 (`src/comic_new/delivery.py`)

1. `BloggerAdapter` 프로토콜 및 `BloggerPublishResult`, 예외 클래스(`BloggerTransportTimeoutError`, `BloggerAuthoritativeError`) 정의.
2. `ControlledBloggerAdapter` 구현: 결정론적 모드(`success`, `timeout`, `disconnect`, `auth_failure`, `bad_request`) 지원 및 destination readback 검증 기능 내장.
3. `DeliveryService` 구현:
   - `preflight_release(...)`: Active auth 검증, 5컷 Current 검증, artifact cut closure 검증, 디스크 내 5컷 canonical asset 파일 및 review artifact 파일 실체/규격 검증.
   - `export_png(...)`: preflight -> start_delivery_attempt (`kind='png'`) -> atomic file export -> output file hash & dimension readback -> record_delivery_observation (`confirmed_success`).
   - `deliver_blogger(...)`: preflight -> start_delivery_attempt (`kind='blogger'`, `outcome='unknown'`) -> try adapter.publish -> 성공 시 record_delivery_observation (`confirmed_success`), 타임아웃/단절 시 `unknown` 유지, 거절 시 record_delivery_observation (`confirmed_failure`).

### Step 2: Store 불변식 보강 (`src/comic_new/store.py`)

1. `start_delivery_attempt`에 composition revision 일치 확인 추가:
   - `art = con.execute("SELECT composition_revision FROM review_artifacts WHERE artifact_id = ?", (art_id,)).fetchone()`
   - `comp = con.execute("SELECT revision FROM composition WHERE singleton_id = 1").fetchone()`
   - `comp["revision"] != art["composition_revision"]`인 경우 `InvalidArtifactClosureError` 발생.
2. `start_delivery_attempt` 및 `record_delivery_observation`의 입력 검증 및 에러 메시지 명확화.

### Step 3: FastAPI 서버 릴리즈 라우트 추가 (`src/comic_new/server.py`)

1. Request DTO 정의: `ExportPngRequest`, `BloggerReleaseRequest`.
2. 엔드포인트 구현:
   - `POST /api/release/export-png`: `DeliveryService.export_png` 호출 및 결과 반환.
   - `POST /api/release/blogger`: `DeliveryService.deliver_blogger` 호출 및 결과 반환.
3. 에러 핸들러 매핑: `AuthorizationRevokedError`, `RealizationIncompleteError`, `InvalidArtifactClosureError`를 적절한 409 ApiProblem으로 변환.

### Step 4: CLI 릴리즈 서브커맨드 추가 (`src/comic_new/cli.py`)

1. `argparse` 서브파서 등록:
   - `export-png`: `project_dir`, `output_file`.
   - `release-blogger`: `project_dir`, `--blog-id`, `--title`.
2. 실행 핸들러 구현:
   - `TransactionalStore.open_project` -> `DeliveryService` 인스턴스 생성 -> 명령 실행 -> JSON 영수증 출력.

### Step 5: 프론트엔드 API, 스토어 및 UI 연동 (`frontend/`)

1. `api/contracts.ts` & `api/client.ts`:
   - `postExportPng(...)` 및 `postBloggerRelease(...)` 함수 추가.
2. `store/studio.ts`:
   - `hasUnsavedDrafts` 계산 프로퍼티를 활용한 `canRelease` 가드 정의.
   - `exportPng(...)`, `releaseBlogger(...)` 액션 추가 및 성공/미확인/실패 토스트 처리.
3. `components/shell/StudioHeader.vue`:
   - 활성 승인이 존재할 때 헤더 작업 영역에 '내보내기(Export)' 및 '발행(Blogger)' 버튼 노출.
   - 미저장 드래프트가 있을 경우 버튼 비활성화 및 안내 툴팁 제공.
4. `components/shell/TruthSummary.vue`:
   - `deliveryLabel`에 더해, `confirmed_success` 시 `destination_url`로 연결되는 외부 링크 버튼 노출.
   - `unknown` 시 경고 색상(`var(--color-stale)` / amber)과 함께 툴팁 고지.
5. `bun run build` 실행으로 `src/comic_new/static/` 정적 번들 갱신.

### Step 6: 종합 자동화 검증 스위트 작성 (`tests/test_release.py`)

1. Acceptance A ~ G 및 Baseline Exit 1-33 전 항목을 커버하는 격리된 통합 테스트 스위트 작성.
2. 실제 disposable SQLite DB, 실제 PIL 이미지 자산, 실제 `comic-new serve` 프로세스, 통제된 Blogger 어댑터를 사용하여 종단 실측.

---

## 6. Scope Acceptance 및 Baseline Exit 1:1 매핑 표

| Scope Acceptance 항목 | Baseline Exit | 핵심 검증 시나리오 및 실측 판정 조건 |
|---|---|---|
| **A. 승인 결속 및 재시작 영속성** | Exit 1-4 | 1. ReviewModal에서 화면 표시된 `artifact_id`와 byte SHA-256 해시를 제출하여 승인 생성.<br>2. snapshot 및 SQLite 직접 SELECT 시 활성 승인으로 조회됨.<br>3. `comic-new serve` 프로세스를 SIGTERM 종료 후 재기동했을 때 활성 승인이 그대로 보존됨.<br>4. 승인 직후 `delivery_attempts`는 비어 있으며 `published` 플래그로 조기 승격되지 않음. |
| **B. 수신자 인지 가능 변경 시 즉시 승인 취소** | Exit 5-9, Gate 2 | 1. 활성 승인 상태에서 말풍선 텍스트 1글자 수정 저장 시 동일 트랜잭션에서 기존 승인이 원자적 취소됨.<br>2. 말풍선 좌표(x, y, w, h), 컷 간격(gap_px), 스타일, intent, Baseline 변경 시에도 즉시 승인 취소.<br>3. 취소 후 이전 artifact로 릴리즈 요청 시 `AuthorizationRevokedError` 발생.<br>4. 수정된 조판의 릴리즈는 새 artifact 실체화와 새 승인을 거쳐야만 가능함을 실측 검증. |
| **C. All-or-Nothing 릴리즈 무결성** | Exit 10-14, Gate 1 | 1. 5개 컷 중 1개라도 STALE이면 릴리즈 요청이 즉각 거부됨.<br>2. 5개 컷 자산 중 1개를 강제 삭제/손상시킨 후 릴리즈 시 4컷 부분 파일 생성 없이 전체 실패.<br>3. 조판 합성기 오류 발생 시 조용히 넘기지 않고 전체 릴리즈 실패 및 롤백 확인. |
| **D. 정본 조판 보존 PNG Export** | Exit 15-18 | 1. 활성 승인 존재 시 승인된 Canonical Review Artifact 바이트를 직접 사용하여 PNG 파일 생성.<br>2. 텍스트 재줄바꿈, 폰트 재계산, 말풍선 이동 없이 정본 조판 그대로 출력됨.<br>3. 출력된 PNG 파일의 SHA-256 해시 및 (1024, 7680) 규격이 승인된 artifact와 100% 일치함을 판독 검증.<br>4. 승인이 없거나 취소된 상태에서는 Export가 차단됨. |
| **E. Blogger 전달 및 목적지 Readback** | Exit 19-23 | 1. 승인된 artifact가 전달 페이로드 소스로 사용됨.<br>2. 요청 시작 시 로컬 DB에 `kind='blogger'`, 초기 `outcome='unknown'` 기록.<br>3. 정상 응답 시 고유 `post_id`와 `destination_url`을 기록하고 `confirmed_success`로 전이.<br>4. snapshot 및 SQLite에서 post ID와 목적지 URL이 정상 재조회됨.<br>5. 승인 필드와 전달 결과 필드가 독립적으로 분리 보존됨. |
| **F. 응답 불명확 시 정직한 Unknown 유지** | Exit 24-29, Gate 4 | 1. Blogger 요청 후 네트워크 절단/타임아웃 주입 시 `confirmed_success`로 승격되지 않고 `unknown` 유지.<br>2. UI와 snapshot이 '발행 결과 미확인 (Unknown)'으로 정직하게 고지.<br>3. 권위 있는 오류 반환 시에만 `confirmed_failure`로 전이됨을 확인. |
| **G. 4대 Counterexample Gate 종단 차단** | Exit 30-33 | 1. Gate 1: 완성 픽셀이 있어도 1개 컷 intent 미실현 시 릴리즈 차단.<br>2. Gate 2: 2차 승인 후 텍스트 1글자/Gap 1px 변경 시 이전 승인으로 릴리즈 차단.<br>3. Gate 3: STOP/재시작 후에도 accepted intent 보존, 미완성 컷 STALE 표시.<br>4. Gate 4: Blogger 타임아웃 시 목적지 Readback 전까지 publication success 선언 차단. |

---

## 7. 구현자 자기점검 및 검증 프로토콜

구현 완료 후 구현자는 다음 점검을 반드시 격리된 일회용 디렉터리(`tmp_path`)에서 실행하고 결과를 확인해야 한다:

1. **단위 및 도메인 불변식 테스트 실행**:
   ```bash
   pytest -v tests/test_release.py
   pytest -v tests/test_transactional_core.py
   ```
2. **프론트엔드 타입 검사 및 빌드 검증**:
   ```bash
   cd frontend && bun run build
   ```
3. **실제 `comic-new` CLI 및 서버 통합 종단 검증**:
   - `comic-new init <test-project>`
   - Baseline 승인 -> 5컷 생성 및 Current 완료 -> Review Artifact 실체화 -> exact hash로 릴리즈 승인.
   - `comic-new export-png <test-project> /tmp/test-export.png` 실행 후 `sha256sum` 대조 검증.
   - `comic-new release-blogger <test-project>` 실행 후 stdout의 `confirmed_success` 및 destination URL 검증.
   - 텍스트 1글자 수정 후 `comic-new export-png` 재호출 시 exit code 1 및 승인 취소 에러 확인 (Gate 2).
   - 타임아웃 주입 모드에서 `release-blogger` 호출 시 exit code 1 및 `unknown` 결과 확인 (Gate 4).
   - 서버 기동(`comic-new serve`) -> 승인 획득 -> 프로세스 종료(SIGTERM) -> 재기동 후 승인 유지 확인 (Acceptance A).

---

## 8. 조건부 선행 작업 (Conditional First Work) 번들

### CFW-1: Blogger 어댑터 I/O 및 트랜잭션 분리 실측

- **plan_anchor**: §4.5, §5 Step 1
- **permitted_initial_work**: `src/comic_new/delivery.py`에 어댑터 프로토콜 및 `ControlledBloggerAdapter`를 작성하고, `start_delivery_attempt` (트랜잭션 1) -> 어댑터 I/O -> `record_delivery_observation` (트랜잭션 2) 분리 호출 구조의 단위 테스트 작성.
- **discriminating_observation**: 어댑터 I/O 도중 지연(예: 2초 sleep)이 발생하더라도 SQLite DB 파일에 write lock이 걸려있지 않아 다른 읽기 쿼리(`store.snapshot()`)가 블로킹 없이 즉시 반환되는지 확인.
- **dependent_work_not_yet_permitted**: FastAPI 라우트 연결 및 프론트엔드 연동.
- **response_if_refuted**: 단일 트랜잭션 내에서 외부 I/O를 수행하도록 잘못 설계된 경우 즉시 중단하고 비동기/별도 트랜잭션 구조로 수정.

### CFW-2: PNG Export 시 조판 바이트 동일성 (Zero-Reflow) 실측

- **plan_anchor**: §4.4, §5 Step 1
- **permitted_initial_work**: `DeliveryService.export_png`의 파일 복사 및 readback 해시 검증 로직 구현.
- **discriminating_observation**: 원본 Canonical Review Artifact의 SHA-256 해시와 내보내진 파일의 SHA-256 해시가 100% 비트 단위로 동일함을 `hashlib.sha256`으로 확인.
- **dependent_work_not_yet_permitted**: CLI 서브커맨드 및 프론트엔드 Export 버튼 연동.
- **response_if_refuted**: 바이트 해시 불일치 시 Pillow 재인코딩 경로를 완전 배제하고 원자적 파일 스트림 복사로 즉시 수정.

---

## 9. 개정 소유권 및 거버넌스

- 사설 헬퍼 함수 명명, 세부 변수명, 내부 로직의 세부 리팩터링은 구현자의 재량에 속한다.
- 그러나 다음 사항은 중대한 방법 변경이므로 발생 즉시 구현을 중단하고 본 Plan을 개정하여 독립 Plan Review의 재승인을 받아야 한다:
  1. 승인 취소의 원자적 트랜잭션 경계 수정
  2. All-or-Nothing 게이트 검증 조건 완화
  3. PNG Export 파이프라인에서 정본 바이트 직접 복사 대신 재조판/재렌더링 도입
  4. Blogger 목적지 Readback 없이 로컬 요청 완료만으로 성공을 단정하는 설계 변경
  5. 4대 Counterexample Gate 중 어느 하나의 실측 조건 우회
- 제품 의미(Thesis)의 변경이 필요한 경우 `THESIS-001` 소유자에게 반환하고, Scope 범위의 조정이 필요한 경우 `Scope Shaper`에게 반환한다.
- 본 Plan의 승인 여부는 독립 Gemini Plan Reviewer가 소유하며, 본 문서는 독립 검토를 위한 입력으로 제출된다.
