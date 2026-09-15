# PLAN-001 — BLOCK-01 Transactional Core 실행 방법

Plan-Type: Scope execution method  
Project-Root: `/home/user01/project/comic_new`  
Scope: `/home/user01/project/comic_new/docs/planning/work/transactional-core/SCOPE.md`  
Scope-SHA256: `bef0ca00ac08007e8bd716787c57559e3eca3a587c5c960a1e371b4a78e3b3dd`  
Selected-Transition-Block: `BASELINE-001 / BLOCK-01`  
Execution-Mode: `SUBAGENT`  
Planner-Model: `Sol High`

## 1. 권위, 현재성, 범위

### 1.1 결속 원본

- **[EXISTING] Product Authority** — `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md`, revision `THESIS-001`, SHA-256 `74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63`. 제품 목적, 5-Truth Chain, 정확히 다섯 컷, 단조 intent revision, currency, 승인 폐기, 중단 내구성 및 단일 영속 권위의 의미를 정한다.
- **[EXISTING] Scope** — 위 Scope는 `Schema: iis-scope/v1`, `Status: ready`, `Open Decisions: None`이다. 2026-09-15에 canonical validator `skill://scope-shaper/tools/validate_scope.py --json`으로 직접 검사했으며 `status: ready`, 결속 Thesis/Transition 경로와 digest가 모두 일치했다.
- **[EXISTING] Transition Authority** — `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md`, SHA-256 `5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c`; `Status: APPROVED`. 이 Plan이 적용하는 것은 `BLOCK-01 — Core Domain & Single Transactional Authority`뿐이다. 해당 Block의 Entry, Required Construction Boundary, Exit 1–12, Abort/Insufficient-for-Exit, Global/Path Invariants와 Safe Continuation 조건을 보존한다.
- **[EXISTING] Repository investigation** — 별도 immutable investigation artifact는 공급되지 않았다. 대신 현재 프로젝트를 직접 열어 확인한 파일은 결속 Thesis, Scope, Baseline 및 `docs/planning/frontend-architecture/FRONTEND-ARCH-001.md`의 네 planning 문서뿐이며, 제품 소스·패키지 메타데이터·테스트·런타임 DB는 존재하지 않는다. 과거 `/home/user01/project/comic`은 이 구현의 호환 권위가 아니다.
- **[EXISTING] 실행 기반** — 현재 호스트의 `python3`은 `3.12.3`, 표준 `sqlite3`가 보고한 SQLite는 `3.45.1`이다. 이 관찰은 현재 계획 환경의 기능 가용성만 세우며 배포 환경이나 아직 없는 제품 동작을 증명하지 않는다.

### 1.2 획득할 결과

하나의 실제 SQLite DB를 공식 Python/CLI 진입점으로 만들고, 새 connection 및 새 process의 한 read transaction에서 다음을 서로 대체하지 않는 별도 truth dimension으로 재조회한다: Structural Baseline, 정확히 `1..5`인 cut identity, Effective Intent와 `desired_revision`, current realization 귀속, composition revision/state, generation job/attempt, immutable review artifact identity, artifact-bound Release Authorization, delivery attempt/outcome. `Current`와 전체 `Complete`는 오직 revision equality로 계산한다.

### 1.3 보존 및 비범위

- 컷 추가·삭제·재색인 경로, arbitrary-N 중간 모델, JSON authority/sidecar, 애플리케이션 `.lock`/lock registry는 만들지 않는다. SQLite가 자체 동시성 구현을 위해 만드는 journal/locking 동작은 별도 애플리케이션 권위가 아니다.
- ORM, repository/unit-of-work 계층, event sourcing/audit 프레임워크, DB plugin/adapter 프레임워크를 만들지 않는다.
- LLM/ima2 실행, worker pool/STOP process control, 픽셀 조판, Vue/FastAPI UI, PNG/Blogger 실행, 외부 destination readback은 구현하지 않는다. 다만 후속 Block이 같은 DB 권위에 그 사실을 기록할 수 있는 좁은 transaction API와 schema는 제공한다.
- `comic-new serve`, 실 generation/release 성공, 외부 효과는 이 Block의 성공으로 주장하지 않는다. 이후 Block의 세부 구현을 미리 넣지 않는다.

## 2. Grounding ledger

### 2.1 EXISTING

1. 결속 원본과 digest, ready Scope, 승인된 `BLOCK-01`은 §1.1의 직접 원본 및 validator 결과로 확인되었다.
2. 현 저장소에는 재사용하거나 이관할 제품 코드/DB가 없다. 따라서 기존 writer/reader, schema migration, 호환 caller는 없다.
3. 이 Scope의 실제 acceptance boundary는 로컬 filesystem의 실제 DB, 실제 SQLite transaction, 독립 connection/process 및 공식 CLI snapshot이다. mock, in-memory DB 또는 소스 존재만으로 대체할 수 없다.

### 2.2 PROPOSED

1. 제품 패키지는 `src/comic_new`, 공식 console entry는 `comic-new = comic_new.cli:main`, 프로젝트 DB는 사용자가 지정한 빈 project directory의 `comic-new.sqlite3` 한 개로 고정한다.
2. `src/comic_new/store.py`의 하나의 concrete `TransactionalStore`가 connection 설정, transaction 시작/commit/rollback, schema mutation 및 snapshot query를 소유한다. 별도 repository interface나 transaction abstraction stack은 두지 않는다.
3. 모든 public mutation은 caller가 마지막 authoritative snapshot에서 얻은 `expected_authority_revision`을 요구한다. `BEGIN IMMEDIATE` 뒤 현재 revision을 비교하고, 일치할 때에만 한 domain mutation과 `authority_revision + 1`을 같은 transaction에서 commit한다. stale caller는 `ConflictError(expected, actual)`을 받고 어떤 상태도 덮어쓰지 않는다. 자동 재시도는 하지 않는다.
4. cut currency는 `desired_revision IS NOT NULL AND realized_revision = desired_revision`, 작품 completion은 고정 다섯 row 모두가 이 조건을 만족하는 경우에만 참이다. asset path/hash 존재, job terminal state, baseline/artifact/authorization/delivery 상태는 이 식의 입력이 아니다.
5. receiver-visible accepted change와 active authorization revocation은 동일 transaction에 묶는다. 외부 delivery 확인은 로컬 attempt와 분리된 후속 observation으로만 기록한다.

### 2.3 UNRESOLVED

- **구현 시작 범위에 필요한 미해결 premise: 없음.** 저장 기술, 패키지 구조, DB identity, transaction 소유자, concurrency/currency 규칙과 verifier readback을 이 Plan에서 제안하고 독립 Plan Review 대상으로 넘긴다.
- 실제 ima2 process 수명, 이미지 byte 유효성 판정, canonical compositor bytes, UI projection, Blogger 응답 및 destination 접근성은 관찰되지 않았다. 이는 `BLOCK-02`~`BLOCK-05`의 명시적 비범위이지, 이 Plan이 surrogate data로 성공을 추정할 수 있는 공백이 아니다.
- 구현 전 target 파일이 새로 생기거나 결속 원본/해시가 바뀌면 §9의 currentness/return 규칙을 적용한다.

## 3. 가장 작은 코드 구조와 진입 경로

### 3.1 제안 파일

- `pyproject.toml` — 최소 build metadata, `src` package discovery, console script `comic-new`만 선언한다. 런타임 의존성은 Python 표준 라이브러리뿐이다.
- `src/comic_new/__init__.py` — package marker와 필요한 public domain types만 export한다.
- `src/comic_new/__main__.py` — `python -m comic_new`를 `cli.main()`으로 직접 연결한다.
- `src/comic_new/cli.py` — stdlib `argparse`로 `init PROJECT_DIR`, `snapshot PROJECT_DIR` 두 명령을 제공한다. add/delete/reindex 명령은 없다.
- `src/comic_new/schema.sql` — v1 DDL, constraints, indexes, exactly-five 보호 trigger를 한 장소에 둔다.
- `src/comic_new/store.py` — DB 경로, schema 생성, concrete transaction methods, conflict/domain errors, authoritative snapshot query와 JSON 직렬화 가능한 반환 타입을 소유한다.
- `tests/test_transactional_core.py` — Scope A–F 및 `BLOCK-01` Exit의 transaction/concurrency/restart 회귀만 둔다. future Block의 generator/compositor/server/delivery를 흉내 내는 테스트는 두지 않는다.

다른 계층은 첫 실제 필요가 생기기 전 만들지 않는다. schema와 store 사이에 ORM/model/repository adapter를 추가하지 않는다.

### 3.2 공식 CLI

- `comic-new init <empty-project-dir>`: directory를 생성하거나 비어 있음을 확인하고 `<dir>/comic-new.sqlite3`를 연다. `PRAGMA application_id`와 `user_version = 1`을 설정하고, 한 schema transaction에서 singleton rows와 cut `1..5`를 seed한 후 commit한다. DB가 이미 정상 초기화되어 있으면 정직하게 already-exists 오류를 내고 덮어쓰지 않는다. crash 뒤 `user_version=0`이며 product table이 없는 빈 SQLite 파일만 재초기화할 수 있고, 식별 불가능하거나 부분적인 비빈 schema는 자동 수리하지 않는다.
- `comic-new snapshot <project-dir>`: read-only 의미의 새 connection과 명시적 read transaction으로 §6 snapshot을 읽어 stdout에 JSON으로 출력한다. 파일/메모리 cache를 섞지 않는다.
- mutation CLI는 이 Scope에 필요하지 않다. 이후 package caller는 §5의 public transaction API를 직접 사용한다.

## 4. SQLite schema와 소유권

모든 connection은 `foreign_keys=ON`, bounded `busy_timeout`, 명시적 transaction mode를 설정한다. schema version은 `PRAGMA user_version`; migration framework는 두지 않고 v1만 생성한다. JSON payload column은 canonical UTF-8 JSON text로 저장하고 현재 SQLite의 `json_valid` CHECK로 형식만 보호한다. domain identity/revision/status는 JSON 안에 숨기지 않고 typed column/constraint로 둔다.

### 4.1 테이블

1. **`authority` singleton**
   - `singleton_id = 1` CHECK/PK, `authority_revision >= 0`, nullable `current_baseline_id`.
   - 모든 accepted write의 compare-and-swap 기준이자 commit 순서다. 한 domain mutation당 정확히 1 증가한다.

2. **`cuts` — 정확히 다섯 stable row**
   - `cut_id INTEGER PRIMARY KEY CHECK (cut_id BETWEEN 1 AND 5)`.
   - nullable `desired_revision`, nullable `realized_revision`, `realized_asset_id/path/content_hash`.
   - init transaction이 `1..5`를 한 번 seed한 뒤 `BEFORE INSERT`, `BEFORE DELETE`, `BEFORE UPDATE OF cut_id` trigger가 `RAISE(ABORT, 'exactly five cuts are immutable')` 한다. public API에는 row lifecycle method가 없다.
   - nullable desired/realized는 신규 프로젝트를 Current로 오판하지 않게 한다. realized metadata는 all-null 또는 all-non-null CHECK, revision은 양수 CHECK를 둔다.

3. **`structural_baselines` 및 `baseline_intents`**
   - baseline은 caller 제공 immutable `baseline_id`, canonical `structure_json`, 승인 시 authority revision을 기록한다.
   - `baseline_intents(baseline_id, cut_id, intent_revision)`은 승인 당시 정확한 다섯 intent revision을 결속한다. approval API가 입력 key set이 정확히 `{1,2,3,4,5}`인지 검사하고 한 transaction에서 다섯 row를 모두 기록한다.

4. **`cut_intents`**
   - PK `(cut_id, revision)`, `revision > 0`, 당시 baseline identity, canonical payload, accepted authority revision.
   - `cuts.(cut_id, desired_revision)`은 현재 Effective Intent를 이 history row에 결속한다(처음의 NULL만 예외). rollback은 과거 payload를 복사한 새 `revision = old + 1` row이지 UPDATE/감소가 아니다. intent history row는 UPDATE/DELETE하지 않는다.

5. **`composition` singleton**
   - `singleton_id = 1`, `revision >= 0`, canonical `state_json`.
   - receiver-visible full state replacement만 수용한다. merge/patch 해석은 만들지 않는다. accepted mutation은 `expected_composition_revision`도 확인하고 정확히 `+1` 한다.

6. **`generation_jobs`, `generation_attempts`**
   - job: immutable `job_id`, `cut_id`, `target_desired_revision`, status (`queued`, `running`, `succeeded`, `failed`, `cancelled`, `interrupted`, `superseded`)와 terminal detail.
   - attempt: immutable `attempt_id`, `job_id`, ordinal/status 및 시작/종료 사실. 물리 subprocess나 scheduler는 없다.
   - terminal job/attempt mutation은 cut intent를 변경하지 않는다. canonical realization commit은 job target과 commit 시점의 current desired revision이 일치할 때만 가능하다. 불일치 결과는 `superseded`로 기록할 수 있으나 `cuts.realized_*`는 변경하지 않는다.

7. **`review_artifacts`, `artifact_cuts`**
   - artifact는 immutable `artifact_id`, unique `content_hash`, 귀속 `composition_revision`을 기록한다.
   - `artifact_cuts`는 정확히 `{1..5}`의 `(cut_id, realized_revision, asset_id)` closure를 기록한다. registration API는 transaction 안에서 다섯 cut 모두 Current인지와 전달받은 set이 현 snapshot과 같은지 확인한다.
   - 이 Block은 이미지 bytes를 생성하거나 artifact를 표시하지 않는다. 이 metadata는 후속 compositor가 생성한 실제 bytes의 identity를 기록할 권위 경계일 뿐이다.

8. **`release_authorizations`**
   - immutable authorization id, artifact id/hash, authorized/revoked authority revision. `revoked_authority_revision IS NULL`인 active row는 partial unique index로 최대 하나다.
   - authorization 생성은 artifact의 composition revision과 five-cut closure가 현재 authority와 일치하고 다섯 cut이 Current일 때만 된다. boolean approval을 두지 않는다.

9. **`delivery_attempts`**
   - attempt id, kind (`png` 또는 `blogger`), authorization/artifact identity, request identity, outcome (`unknown`, `confirmed_success`, `confirmed_failure`), nullable destination id/URL/evidence와 관찰 revision.
   - row 생성 시 outcome은 반드시 `unknown`; no-row는 snapshot에서 `not_attempted`로 계산한다. `confirmed_success`는 destination id, URL 및 evidence가 모두 있을 때만 기록한다. authorization row를 만들거나 가진 사실은 이 outcome을 바꾸지 않는다.

### 4.2 불변식 보호 범위

DB CHECK/FK/UNIQUE/trigger가 identity와 상태 조합의 저비용 위반을 거부하고, exact-five input, current closure, state transition 및 cross-table 동시 변경은 하나의 store transaction이 책임진다. raw SQL로 schema/trigger 자체를 파괴하는 행위는 제품 API가 아니지만, 정상 SQL로 insert/delete/reindex를 시도해도 trigger가 차단되는지 self-check한다. schema 오류를 lock file, JSON 복제본 또는 in-memory override로 우회하지 않는다.

## 5. Public transaction API와 원자 경계

`TransactionalStore`는 아래 concrete methods만 제공한다. 명명·private helper·반환 dataclass의 동등한 세부는 구현자 재량이지만 의미와 transaction boundary는 고정한다.

- `create_project(project_dir)` / `open_project(project_dir)` / `snapshot()`.
- `approve_structural_baseline(expected_authority_revision, baseline_id, structure, intents_by_cut)` — 새 baseline, 다섯 새 intent revision, five `cuts.desired_revision`, current baseline pointer, active authorization revocation, authority revision 증가를 한 transaction으로 commit한다.
- `accept_cut_intent(expected_authority_revision, cut_id, intent_payload)` — 해당 cut의 `desired_revision + 1`, immutable intent row, authorization revocation을 함께 commit한다.
- `accept_composition(expected_authority_revision, expected_composition_revision, state)` — composition `+1`, state replacement, authorization revocation을 함께 commit한다.
- `enqueue_generation_job`, `start_generation_attempt`, `finish_generation_attempt`, `set_job_terminal` — job/attempt 사실만 바꾸며 accepted intent/realization을 대리하지 않는다.
- `commit_realization(expected_authority_revision, job_id, asset_id, asset_path, content_hash)` — 같은 commit 안에서 job target revision과 현 cut desired revision 및 허용 job 상태를 재확인한다. 일치할 때만 realized attribution을 교체하고 job을 `succeeded`로 만든 뒤 receiver-visible pixel change이므로 active authorization도 revoke한다. stale/cancelled/interrupted 결과는 canonical state에 쓰지 않는다.
- `register_review_artifact(expected_authority_revision, artifact_id, content_hash, composition_revision, cut_closure)` — 정확히 다섯 Current realization과 composition identity를 검사한 immutable metadata 등록이다. bytes 생성/검증 성공을 스스로 주장하지 않는다.
- `authorize_release(expected_authority_revision, authorization_id, artifact_id, content_hash)` — 바로 그 current artifact closure에 결속하고 기존 active authorization이 있다면 같은 transaction에서 revoke 후 새 row를 만든다.
- `start_delivery_attempt(expected_authority_revision, attempt_id, kind, authorization_id, request_id)` — active/current closure를 다시 검사하고 `unknown` attempt만 만든다.
- `record_delivery_observation(expected_authority_revision, attempt_id, outcome, evidence, destination_id=None, destination_url=None)` — local attempt와 분리된 관찰을 기록한다. 실제 외부 readback을 호출하지 않으며 confirmed 상태의 evidence 요건만 강제한다.

모든 mutation은 성공 return 자체를 최종 readback으로 삼지 않는다. commit 뒤 caller/verifier는 새 connection의 `snapshot()`으로 권위 상태를 재조회한다. validation error, stale expected revision, SQLite busy/storage error를 구별하며 어느 것도 성공으로 변환하거나 자동 replay하지 않는다.

## 6. Authoritative snapshot, restart, concurrency

### 6.1 한 read transaction의 snapshot

`snapshot()`은 한 명시적 SQLite read transaction에서 다음 JSON-compatible 구조를 만든다.

- `schema_version`, `authority_revision`.
- `baseline`: current identity/structure 및 승인 당시 다섯 intent identity, 또는 `null`.
- `cuts`: 항상 `cut_id` 오름차순의 다섯 항목. 각 항목은 current intent payload/revision, realized revision/asset identity, 계산된 `currency: CURRENT|STALE`를 분리한다.
- `realization_complete`: boolean과 `COMPLETE|UNRESOLVED`; 오직 다섯 currency의 conjunction이다.
- `composition`: revision/state.
- `jobs`와 `attempts`: execution facts.
- `review_artifacts`: artifact/composition/five-realization closure.
- `release_authorization`: active exact artifact-bound row 또는 `null`, 그리고 revoked history.
- `delivery_attempts`: `not_attempted`/`unknown`/`confirmed_success`/`confirmed_failure`를 authorization과 별도 dimension으로 표시한다.

snapshot reader는 filesystem asset 존재, process memory, job success, approval 또는 delivery를 이용해 currency를 보정하지 않는다. DB 내부 불변식(예: cut count가 5가 아님)을 만나면 정상 snapshot을 꾸미지 말고 corruption error로 실패한다.

### 6.2 restart

DB connection을 모두 닫은 뒤 별도 Python process가 동일 `comic-new.sqlite3`를 열어 같은 snapshot을 얻는 것이 권위 있는 restart readback이다. accepted intent, baseline, composition, job/attempt, realization attribution, artifact, authorization, delivery truth는 process-local 변수로 복구하지 않는다. 이 Block의 job API는 `interrupted` terminal truth를 영속화할 수 있고 그 transition이 desired intent를 건드리지 않음을 증명한다. 실제 worker process crash 감지와 startup reconciliation의 소유자는 `BLOCK-02`이며, 이 Plan은 실행하지 않았던 subprocess를 가짜로 복구했다고 주장하지 않는다.

### 6.3 concurrent writers

각 writer는 독립 connection/process에서 같은 snapshot의 `authority_revision = R`을 잡는다. write는 `BEGIN IMMEDIATE`로 SQLite writer를 직렬화한 뒤 `authority.revision == R`을 검사한다. 첫 writer만 domain write와 `R+1`을 commit한다. 기다린 둘째 writer는 실제 `R+1`을 보고 `ConflictError`로 rollback한다. 둘째 request를 새 base에 자동 재적용하지 않는다. reader는 transaction isolation상 old-state/old-authorization 또는 new-state/revoked-authorization만 보며 중간 조합을 볼 수 없다.

## 7. 구현 순서와 partial-failure 경계

1. `pyproject.toml`과 package/CLI entry를 만들되 아직 제품 성공을 주장하지 않는다.
2. `schema.sql`과 DB create/open identity 검사를 구현하고, 단일 schema transaction으로 singleton + cut `1..5`를 seed한다. 이 단계에서 direct SQL insert/delete/reindex와 재초기화 실패를 먼저 확인한다.
3. store의 connection/transaction 소유, global compare-and-swap, `ConflictError`, one-transaction snapshot을 구현한다.
4. baseline/intent와 currency readback을 먼저 연결하고 monotonic rollback-as-new-revision을 확인한다.
5. composition acceptance + authorization revocation closure를 한 mutation으로 구현한다. 이를 분리된 두 commit으로 임시 제공하지 않는다.
6. job/attempt와 realization commit-time currency gate를 구현한다. job terminal mutation은 desired intent에 쓰지 않는다.
7. artifact/authorization/delivery metadata API를 같은 authority에 연결한다. external effect를 호출하지 않는다.
8. CLI init/snapshot을 실제 store에 연결한다. in-memory fallback, sample JSON snapshot 또는 seeded success state를 두지 않는다.
9. §8의 실제 SQLite/connection/process self-check를 수행한다. 실패 시 후속 Block으로 우회하지 않고 해당 atomic boundary를 수정한다.

예외가 나면 transaction context가 전부 rollback한다. artifact bytes나 외부 효과는 이 Block에서 만들지 않으므로 DB와 외부 사이 partial effect는 없다. 후속 Block은 filesystem/external effect를 transaction 안에 포함한 척하지 말고 candidate 생성 → 검증 → commit-time DB gate와 local attempt → external readback 경계를 각각 사용한다.

## 8. Focused self-check와 verifier readback

모든 확인은 격리된 임시 project directory의 실제 on-disk SQLite DB를 사용한다. in-memory SQLite, mocked store, canned snapshot은 acceptance 증거가 아니다. synthetic intent/composition 문자열과 asset/artifact identity는 이 Scope의 로컬 transaction 입력이며 실제 generator/compositor/external 성공의 대체 증거로 해석하지 않는다.

| Scope / Exit | 최소 실행 | 권위 있는 readback 및 가장 싼 판별 |
|---|---|---|
| **A / Exit 1,2,9** | 설치된 공식 `comic-new init` 실행 후 별도 process에서 `comic-new snapshot`; CLI help와 public store surface 검사; 정상 DB에 raw insert/delete/reindex 각각 시도 | 새 connection snapshot의 cut ids가 정확히 `[1,2,3,4,5]`; 세 SQL이 trigger 오류로 rollback; project dir에는 DB 및 명시적으로 만든 asset fixture 외 `.json`/`.lock` authority가 없음. SQLite 자체 journal/lock은 app sidecar로 오분류하지 않음 |
| **B / Exit 3,4,5** | 서로 다른 다섯 payload로 baseline 승인, close/open; 한 cut을 두 번 수정; 과거 payload를 다시 수용 | baseline identity와 다섯 승인 intent를 새 connection에서 조회; selected cut revision이 매 commit 정확히 1씩 증가하고 마지막 payload만 Effective Intent; 복원 payload도 더 높은 revision |
| **C / Exit 6,10** | current five-cut closure와 artifact/authorization metadata를 실제 DB에 기록; 같은 composition base를 가진 독립 writer 둘을 barrier 후 경쟁; accepted composition change도 수행 | 한 writer만 commit, 하나는 `ConflictError`; composition은 정확히 한 단계만 증가; change와 authorization `revoked_authority_revision`이 같은 snapshot에 함께 나타나며 new-composition/old-active-auth 조합은 어떤 reader에서도 없음 |
| **D / Exit 11,12** | baseline rev1을 다섯 realization metadata에 commit하고 실제 임시 asset files도 둔 뒤 cut 3 intent를 rev2로 수용; job/authorization/delivery row 상태도 바꿔 snapshot; 마지막에 cut 3 rev2 realization을 valid job target으로 commit | cut 3은 기존 file이 있어도 `STALE`, whole은 `UNRESOLVED`; 다른 truth dimension 변화가 판정을 바꾸지 않음; 오직 다섯 equality 후 `COMPLETE=true` |
| **E / Exit 7,8,10** | 모든 local truth dimension을 기록하고 모든 connection 종료; 별도 Python process snapshot. 같은 `R`로 동일 cut intent 또는 composition을 두 independent process에서 경쟁 | 재시작 snapshot이 baseline/intent/composition/realization/job/attempt/artifact/auth/delivery identity를 보존; 경쟁 결과 accepted 1/conflict 1; Effective Intent/composition은 하나뿐이고 authority revision은 한 번만 증가 |
| **F / Exit 8 및 continuation boundary** | public APIs로 queued→running→`interrupted` job/attempt, artifact-bound authorization, `unknown` delivery attempt를 기록하고 새 process snapshot | job terminal 전이가 desired intent를 철회하지 않음; authorization과 delivery outcome은 별도; unknown은 confirmed로 보이지 않음; 모든 기록이 동일 SQLite snapshot에 있고 별도 queue/approval/delivery file 없음 |

추가로 stale job의 `commit_realization`을 최신 intent 변경 뒤 실행하여 job을 superseded/거절 상태로 남기되 canonical realization이 바뀌지 않는지 확인한다. 이는 `PATH-4`의 후속 Block용 commit gate를 가장 싸게 판별하며 실제 image generation 성공을 주장하지 않는다.

### BLOCK-01 Exit 및 Safe Continuation 판정 자료

위 A–F 결과로 `BLOCK-01` Exit 1–12 각각을 직접 매핑한다. 구현자 self-check 통과는 semantic verification이나 Block 완료 선언이 아니다. verifier는 다음을 받아 독립적으로 재실행한다.

1. 결속 Thesis/Scope/Baseline의 위 exact path/digest와 validator JSON.
2. 독립 review가 admit한 이 Plan의 exact path/digest.
3. 검증 대상 source byte identity(변경 파일 목록과 SHA-256) 및 `python3`/SQLite version.
4. repo 밖 새 임시 directory에서 공식 CLI로 생성한 fresh DB; 기존 DB나 구현자 fixture를 성공 상태로 재사용하지 않는다.
5. A–F 각 실행, authoritative CLI snapshot/필요한 진단 SQL, 두 process의 accepted/conflict 결과, filesystem no-sidecar 관찰.
6. 관찰한 unresolved/corruption/stale/orphan state와 invariant violation 유무. 하나라도 Unknown이면 `BLOCK-02` handoff를 금지한다.

DB row나 내부 method return만으로 외부 image/delivery 성공을 주장하지 않는다. 이 Scope의 real boundary는 실제 on-disk SQLite commit과 새 connection/process readback이며, 후속 external boundary는 해당 Block의 실제 실행/readback이 별도로 필요하다.

## 9. 구현 재량, 조건부 시작, 반환 조건

### 9.1 구현자 재량

동등한 private helper 이름, dataclass/TypedDict 선택, SQL index 이름, 오류 메시지 문구, canonical JSON serializer의 작은 배치는 재량이다. public truth dimensions, exactly-five constraint, CAS conflict, transaction closure, snapshot 의미는 재량이 아니다.

### 9.2 Conditional first work

현재 권한으로 값싸게 확인 가능한 시작 premise는 모두 §1–2에서 확인되었으므로 미해결 premise에 묶인 conditional-first-work bundle은 없다. 허용된 최초 작업은 §3의 최소 package/CLI와 §4의 v1 schema를 만드는 것이며, `BLOCK-02` 이후 실행은 허용되지 않는다. 구현 시작 시 결속 digest나 저장소 inventory가 달라지면 이를 지지로 간주하지 말고 아래 반환 규칙을 적용한다.

### 9.3 Plan/Scope/Thesis로 반환하는 material change

다음 변화가 필요해지면 영향 작업을 중단하고 이 Plan을 개정한 뒤 새 독립 Plan Review를 받아야 한다.

- SQLite 이외 권위, 둘 이상의 DB/JSON/queue authority, app-managed lock, ORM/repository/event framework가 필요하다는 결론.
- exactly-five identity, DB path, transaction owner, public transaction boundary 또는 authoritative snapshot shape의 의미 변경.
- global expected revision/CAS 대신 silent merge, 자동 replay 또는 last-write-wins가 필요하다는 결론.
- intent monotonicity, commit-time currency, Complete 식, receiver-visible mutation+authorization revocation closure, artifact/release/delivery identity 전략의 변경.
- restart/readback 또는 verifier의 실제 acceptance 경로를 mock/surrogate로 바꾸는 제안.
- implementation-time evidence가 현재 cause/owner/interface/persistence/effect strategy를 반박하는 경우.

제품 의미(정확히 다섯 컷, 승인/전달/currency 의미)를 바꿔야 하면 `THESIS-001` owner에게 반환한다. 현재 Outcome/Acceptance/Non-Goals 또는 `BLOCK-01` 경계를 바꿔야 하면 Scope shaping owner에게 반환한다. 단순 파일명/private helper/index 조정은 재검토 사유가 아니다.

## 10. Plan 완료 경계

이 문서는 구현 방법만 준비한다. product source, DB, Thesis, Scope, Baseline 또는 status를 변경하지 않으며 `BLOCK-01` 구현·검증·Exit를 선언하지 않는다. 정확한 다음 단계는 이 Plan bytes에 대한 독립 Plan Review이다. `ADMIT`과 현재성 확인 전에는 구현을 시작하지 않으며, `REVISE`/`EVIDENCE_NEEDED` 또는 material finding이 있으면 지정 owner에게 돌아간다.
