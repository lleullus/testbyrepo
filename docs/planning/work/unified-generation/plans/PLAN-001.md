# PLAN-001 — BLOCK-02 Unified Generation Engine 실행 방법

Plan-Type: Scope execution method  
Project-Root: `/home/user01/project/comic_new`  
Scope: `/home/user01/project/comic_new/docs/planning/work/unified-generation/SCOPE.md`  
Scope-SHA256: `710a2afe3c4c72eaa674911005d0a185664c9e222aacfd09cc809f053c47acb3`  
Selected-Transition: `BASELINE-001 / BLOCK-02`  
Planner-Mode: `SUBAGENT`  
Planner-Model: `Sol High`

## 1. 권위, 현재성, 획득할 결과

### 1.1 결속 원본과 입장 조건

- **[EXISTING] Product Authority** — `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md`, revision `THESIS-001`, SHA-256 `74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63`. 전체 원문에서 제품 약속, Intent → Realization 인과 경계, INV-1/2/3/7/8, Interruption/Currency Gate, 성공 readback을 직접 확인했다.
- **[EXISTING] Scope** — 위 exact Scope는 `Schema: iis-scope/v1`, `Status: ready`, `Open Decisions: None`이다. canonical validator `/home/user01/.omp/agent/skills/scope-shaper/tools/validate_scope.py --json <exact-scope>`의 실제 결과는 exact Project Root, 위 Product Authority, 아래 Transition Authority 및 `status: ready`를 반환했다.
- **[EXISTING] Transition Authority** — `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md`, SHA-256 `5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c`, `Status: APPROVED`. 적용 범위는 `BLOCK-02`와 그 Entry/Exit 1–16, INV-1/2/3/7/8, PATH-3/4/5/9/10, Safe Continuation/Safe Abort 및 Realization Commit atomic boundary뿐이다. 이후 Block을 이 Plan으로 시작하지 않는다.
- **[EXISTING] 완료 선행 Scope** — `/home/user01/project/comic_new/docs/planning/work/transactional-core/SCOPE.md`, 현재 `Status: done`, SHA-256 `2ea75fa8ab21733b0baaf5f84d3505a2eec197e0d74dbd98cabfe9ad564f7a02`.
- **[EXISTING] 선행 실행 증거** — verifier report `/home/user01/tmp/comic-new-block01-verification-r3.md` SHA-256 `28d7051d59df56ed2ecba2ea13ef15ef28517f7d7577398b5bc89734d75309b2`, Coverage `/home/user01/tmp/comic-new-block01-coverage.md` SHA-256 `607a111653a4d5d4cbd22ef6ca1a896cee02adfd3bb10e325e4b37cffe89b671`. 실제 on-disk SQLite, 새 connection/process readback, CAS, stale commit rejection, intent 보존과 queue/currency 분리를 증명했으며 provider/process-tree 실행은 명시적으로 증명하지 않았다.
- **[EXISTING] 입장 판단에 쓰는 선행 사실** — BLOCK-01 Exit 1–12와 Coverage `Findings: None`, `Completion: COMPLETE`가 제공되었다. 이 Plan은 그 완료 판정을 재발행하지 않고, 현재 코드에 있는 SQLite authority만 후속 owner로 사용한다.

### 1.2 획득할 정확한 결과

하나의 SQLite-backed `generation_jobs` queue, 하나의 job type, 전역 동시성 2인 단일 runner owner를 만든다. 전체 생성은 cut `1..5`를 같은 enqueue transaction에 넣는 상위 조작이고, 개별 생성은 같은 서비스에 cut 하나를 주는 조작이다. 각 worker는 job이 가리키는 `(cut_id, target_desired_revision)`의 역사적 intent prompt를 stdin으로 실제 ima2 CLI에 전달하고 job별 staging PNG만 쓰게 한다. decode 가능한 PNG만 commit gate에 도달하며, gate가 같은 SQLite write transaction에서 job/attempt 상태와 현재 `cuts.desired_revision`을 다시 읽은 뒤에만 immutable canonical asset을 승격한다.

STOP/cancel/timeout/crash는 실행 process group/tree와 실행 truth만 종료한다. accepted intent와 기존 canonical bytes는 건드리지 않는다. Queue drain, terminal job 수 또는 파일 존재는 currency를 만들지 않으며, 기존 `snapshot()`의 정확히 다섯 `desired_revision == realized_revision`만 `COMPLETE`를 만든다.

### 1.3 보존 및 비범위

- 기존 exact-five identity, monotonic intent, composition/release closure, delivery truth와 `authority_revision` transaction ordering을 보존한다.
- full-run queue/engine, JSON queue, queue sidecar, app lock/lock registry, broker, generic task framework, provider retry/fallback, 임의 N-cut 경로를 만들지 않는다.
- compositor/review artifact bytes, Vue/FastAPI/SSE UI, production `serve`, PNG/Blogger release는 건드리지 않는다.
- 실패 시 기존 realization을 삭제하지 않는다. explicit retry는 같은 job 재시도가 아니라 사용자가 다시 enqueue한 새 job이다.
- legacy `comic`의 handoff/file-lock/commit 구조는 가져오지 않는다.

## 2. Grounding ledger

### 2.1 EXISTING

1. `pyproject.toml:5-16`은 `comic-new = comic_new.cli:main`, Python `>=3.10`, runtime dependency 없음, package data `schema.sql`만 선언한다. SHA-256은 `053be1f99847a23c6b3b3cc94c7e514f1c08938ba94c2e5a0cbc07bb93a8be2d`이다.
2. `src/comic_new/schema.sql:55-74`에는 이미 `generation_jobs(job_id, cut_id, target_desired_revision, status, terminal_detail, timestamps)`와 `generation_attempts(attempt_id, job_id, ordinal, status, timestamps, detail)`가 같은 SQLite authority에 있다. 별도 queue 파일은 없다. Schema SHA-256은 `a563cc9794b0dff1596ed1ec3ee1dabf9454676184bad5ea0401ed73024bf6fb`이다.
3. 현재 `src/comic_new/store.py:249-464`의 `snapshot()`은 한 DEFERRED read transaction에서 cut currency를 오직 non-null revision equality로 계산하고 jobs와 attempts를 별도 projection으로 읽는다. 이것이 queue/currency 분리의 재사용 기준이다.
4. 현재 `store.py:617-828`의 generation primitives는 BLOCK-01 metadata boundary다. enqueue가 caller-supplied target을 그대로 저장하고, start/finish/job-terminal이 물리 process identity 없이 개별 transaction이며, `commit_realization`은 desired revision을 commit 때 다시 읽어 stale job을 superseded로 만든다. 그러나 decode/staging/file promotion, attempt closure, single runner, cancellation liveness, startup reconciliation은 없다.
5. 현재 generation primitive는 `tests/test_transactional_core.py`에서만 호출된다. `cli.py:20-69`의 공식 CLI는 `init`과 `snapshot`뿐이다. 즉 product callsite migration 범위는 store tests, CLI 및 새 generation service로 한정된다.
6. 현재 production hashes는 `store.py` `5477e5f834879585f464c84cf3558bb2eafce9d62c1762e005250d22158768f7`, `cli.py` `d1fe9679bf5fda25e390c1233fab4667b01ec1f4e533b22c1bee0416801765f3`, `__init__.py` `41376d7817758b97cf8f009d90ddf59b15a2d45e67b4d0c5c9436d0c1920b247`, `__main__.py` `1308842bda05bab19982aac09a229d1e8bf4600dea78b9b49bcd537132abd318`이다. BLOCK-01 verifier가 기록한 `store.py` digest `c1052d...`와 현재 bytes는 다르다. 현재 소스에는 temp-DB atomic initialization과 stricter schema verification이 추가되어 있으므로 Plan은 verifier의 예전 store bytes를 현재 구현 증거로 오인하지 않고 직접 읽은 현재 bytes를 기준으로 한다.
7. 현재 Project Root 안에는 `*.sqlite3`가 없다. 이는 저장소 내부에서 migration 대상 DB를 발견하지 못했다는 사실만 뜻하며, 외부 사용자 project에 v1 DB가 없다는 뜻은 아니다.
8. 실제 설치된 `/home/user01/.nvm/versions/node/v24.18.0/bin/ima2 gen --help`를 provider 호출 없이 실행해 `gen`, `--stdin`, `--mode`, `--no-size-nudge`, `--model`, `--size`, `--quality`, `--timeout`, `-o/--out`, `--json`이 현재 CLI surface임을 확인했다. 이 help readback은 provider/model 가용성이나 생성 성공을 증명하지 않는다.
9. 진단 전용 legacy `/home/user01/project/comic/src/comic/generator/ima2_client.py` SHA-256은 `e7485836e501a76e6f2ce427510f2c1a8d3ecd0ec83a3585cb47fe34648d9956`이다. 관련 관찰은 `:64-85`의 argv와 `:124-220`의 stdin/timeout/staging뿐이다. 그 코드는 child 하나만 kill하고 non-empty output만 검사하며 legacy handoff/file-lock을 사용하므로 compatibility authority나 복사 대상이 아니다.

### 2.2 PROPOSED

1. 기존 두 generation table을 확장하고 SQLite singleton `generation_control`을 추가한다. 이것만이 queue, runner ownership, stop epoch 및 attempt/process identity의 durable authority다.
2. `GenerationService.enqueue(cut_id: int | None, expected_authority_revision: int)` 하나가 single/all 요청을 수용한다. `None`은 exact `1..5`, 정수는 정확히 한 cut이며 다른 subset API는 없다.
3. `GenerationRunner` 하나가 DB에서 queue를 claim하고 정확히 worker 2개를 운용한다. 별도 daemon/broker가 아니며 향후 server도 이 동일 class를 호출한다.
4. ima2 child는 new process session/group에서 실행되고, runner는 PID/PGID/Linux process start token과 staging path를 attempt에 기록한다. live process handle은 신호 전달 수단일 뿐 authority가 아니다.
5. Pillow 한 dependency로 실제 PNG decode를 확인한다. header/non-empty 검사만으로 성공시키지 않는다.
6. canonical path는 project 내부 `assets/realizations/cut-<cut_id>/rev-<revision>-<job_id>.png`처럼 job마다 immutable/unique하게 만든다. staging은 project 내부 `.generation-staging/<job_id>/candidate.png`여서 promotion과 canonical path가 같은 filesystem에 있다.
7. store의 느슨한 generation primitives는 새 state-specific transaction methods로 clean cutover하고 기존 모든 caller를 이관한다. direct-to-canonical public writer와 deprecated alias는 남기지 않는다.

### 2.3 UNRESOLVED

- **실제 ima2 provider 성공** — CLI syntax와 binary presence만 관찰했다. 현재 model credential, provider availability, quota/cost permission, 네트워크 결과 및 실제 생성 품질은 관찰하지 않았다. Main의 별도 현재 권한 없이는 실제 provider command를 실행하지 않으며 local helper 결과를 ima2 성공으로 주장하지 않는다. §11.2의 conditional-first-work bundle만 이 경계를 열 수 있다.
- **Project Root 밖 v1 DB의 실제 존재/내용** — 공급된 target에는 실제 사용자 DB가 없다. 구현은 이를 없다고 가정하지 않고 exact v1→v2 migration을 제공한다. 알 수 없는 version 또는 검증되지 않는 partial schema는 자동 보정하지 않고 정직하게 거절한다.

## 3. 최소 파일/인터페이스 구조

### 3.1 변경 대상

- `pyproject.toml` — `Pillow` runtime dependency와 `migrations/*.sql` package data만 추가한다.
- `src/comic_new/schema.sql` — 신규 project용 schema v2: 기존 authority를 유지하면서 generation control/process identity/index를 포함한다.
- `src/comic_new/migrations/v1_to_v2.sql` — 한 번뿐인 exact v1→v2 transaction SQL. 범용 migration framework를 만들지 않는다.
- `src/comic_new/store.py` — migration, generation-specific transaction/state transition, authoritative snapshot 확장, candidate commit gate를 소유한다.
- `src/comic_new/generation.py` — `GenerationService`, fixed-two `GenerationRunner`, ima2 argv, PNG validation, process tree termination 및 staging lifecycle을 소유한다.
- `src/comic_new/_generation_exec.py` — provider exec 전 parent-death 보호와 시작 gate만 수행하는 작은 POSIX/Linux launcher. generic worker framework가 아니다.
- `src/comic_new/cli.py` — `generate`, `run-generation`, `cancel-generation`, `stop-generation`을 기존 parser에 직접 추가한다.
- `src/comic_new/__init__.py` — 후속 server가 직접 사용할 service/runner와 material error/receipt type만 export한다.
- `tests/test_transactional_core.py` — 제거되는 primitive callsite를 새 공식 path 또는 명시적 test-only DB fixture로 이관하되 provider 성공 증거로 사용하지 않는다.
- `tests/test_generation.py` — 실제 local subprocess/process tree와 on-disk SQLite를 사용하는 load-bearing lifecycle regression만 둔다.

### 3.2 공식 service/CLI surface와 반환 조건

- `GenerationService.enqueue(cut_id=None|1..5, expected_authority_revision=R) -> EnqueueReceipt` — 한 `BEGIN IMMEDIATE`에서 authority CAS, 대상 cut과 exact target intent row 및 non-empty prompt를 읽고 ordered jobs를 insert한다. all은 정확히 5개 전부 성공하거나 전부 rollback한다. receipt는 `authority_revision`과 ordered `(job_id, cut_id, target_desired_revision)`를 반환한다. missing intent/prompt, 잘못된 cut, stale `R`은 job을 일부 만들지 않고 명시 오류다.
- `GenerationRunner.run_until_idle() -> RunReceipt` — single-owner acquisition과 orphan recovery가 성공한 뒤 worker 2개만 시작한다. 반환은 이 runner가 더 이상 claim할 queued/running work가 없고 자신이 시작한 child를 모두 reap한 뒤에만 가능하다. terminal status counts/job IDs와 별도 `realization_complete` readback을 함께 반환하되 전자를 후자로 합성하지 않는다. 어떤 대상 job이 `failed/cancelled/interrupted/superseded`면 CLI는 nonzero다.
- `GenerationService.cancel(job_id) -> CancelReceipt` — queued이면 spawn 전 DB `cancelled`; running이면 전체 process tree가 사라지고 attempt/job terminal readback이 확인된 뒤 반환한다. succeeded/failed/superseded 같은 이미 settled job을 성공적으로 취소했다고 위장하지 않고 current terminal disposition을 반환한다.
- `GenerationService.stop_all() -> StopReceipt` — stop epoch 증가와 queued cancellation을 같은 DB transaction에 기록해 새 claim을 닫고, 당시 running process trees를 TERM→bounded wait→KILL로 종료/reap한 뒤 attempt/job을 `interrupted`로 terminalize한다. 반환 조건은 targeted process/group의 non-zombie liveness 0과 새 DB connection terminal readback 둘 다다. kill 권한/settlement 실패 시 nonzero/exception이며 살아 있는 row를 terminal 성공으로 위장하지 않는다.
- `comic-new generate PROJECT [--cut {1,2,3,4,5}]` — 생략 시 exactly five enqueue 후 동일 runner를 drain한다. enqueue receipt와 run receipt를 JSON으로 출력한다.
- `comic-new run-generation PROJECT` — 기존 durable queue의 공식 startup/recovery+drain entry다. interrupted job을 자동 retry하지 않는다.
- `comic-new cancel-generation PROJECT JOB_ID`, `comic-new stop-generation PROJECT` — 위 service와 동일한 반환 조건을 JSON/exit code로 투영한다.
- `comic-new snapshot PROJECT` — generation control, process identity, jobs/attempts와 기존 currency를 한 read transaction에서 계속 출력한다.

## 4. SQLite schema, migration, 단일 runner ownership

### 4.1 v2 generation schema

기존 `generation_jobs` status vocabulary는 그대로 유지한다. `target_desired_revision`은 service가 같은 transaction에서 현재 cut로부터 읽으며 `(cut_id, revision)` 역사 row 존재도 검사한다. 최소 index는 queued claim용 `(status, created_at, job_id)` 하나다.

`generation_attempts`에는 다음을 더한다.

- `runner_id`: claim owner identity
- `process_pid`, `process_group_id`, `process_start_token`: 셋 모두 NULL(아직 spawn 전) 또는 셋 모두 non-NULL
- `staging_path`: job별 candidate path
- `provider_request_id`: stdout JSON에 실제 값이 있을 때만 기록

`generation_control(singleton_id=1)`에는 `stop_epoch >= 0`, nullable all-or-none `runner_id/runner_pid/runner_start_token`, `runner_started_at`을 둔다. worker pool count나 queue truth를 memory singleton에 복제하지 않는다. 두 번째 live runner acquisition은 `RunnerAlreadyActiveError`; dead/mismatched process token owner만 startup recovery 대상이다. 이 row가 전역 concurrency 2를 모든 CLI/server caller에 대해 하나로 만든다.

### 4.2 exact v1→v2 cutover

1. 구현 시작 전 현재 v1 source로 isolated scratch project를 하나 만들고 representative intents, old realization, queued/running/terminal jobs를 기록한다. source 변경 후 migration discrimination에만 쓰고 외부/provider 효과는 만들지 않는다.
2. 신규 DB는 updated `schema.sql`로 v2를 atomic temp DB에 생성한다.
3. 기존 v1은 exact migration SQL 하나를 `BEGIN IMMEDIATE`에서 적용해 generation columns/control/index를 추가하고 마지막에 `user_version=2`를 기록한다. 기존 cuts/intents/realizations/jobs/attempts를 삭제하거나 재작성하지 않는다.
4. v1에서 이미 `running`인데 process identity가 없는 row는 migration 성공을 Running 정상화로 오인하지 않는다. 첫 official runner startup이 §8 recovery로 `interrupted` 처리한다.
5. 현재 strict `verify_schema()`에 v2 table/column/index/singleton 검사를 추가한다. version 0/unknown, partial v1/v2 또는 migration 실패는 rollback/`StoreCorruptionError`; JSON/lock fallback은 없다.
6. migrated scratch DB를 새 process에서 열어 모든 preexisting BLOCK-01 truth가 동일하고 새 generation control만 추가됐는지 읽은 후 scratch를 제거한다.

## 5. 하나의 enqueue와 queue claim path

### 5.1 Intent → job binding

`enqueue`는 target을 caller에게 받지 않는다. transaction 안에서 각 cut의 `desired_revision`과 바로 그 `cut_intents(cut_id, revision).payload_json`을 읽는다. string payload는 그 값, object payload는 non-empty string `prompt` field를 generation prompt로 사용한다. 다른 payload shape은 accepted intent 자체를 변경하지 않고 generation acceptance만 정직하게 거절한다.

all/single은 대상 목록 결정만 다르다.

```text
GenerationService.enqueue(cut_id)
  -> cut_id is None ? (1,2,3,4,5) : (cut_id,)
  -> one store enqueue transaction
  -> same generation_jobs table/status
  -> same runner claim/execute/commit path
```

새 enqueue는 이전 STOP epoch를 되돌리거나 intent를 변경하지 않는다. 새 runner invocation은 acquisition 당시 epoch를 own start epoch로 읽는다. global STOP 당시 queued jobs는 `cancelled`이므로 나중에 묵시 재실행되지 않는다.

### 5.2 Claim

각 worker는 독립 connection의 `BEGIN IMMEDIATE`에서 다음을 한 번에 수행한다.

1. runner owner/start token 및 captured stop epoch가 여전히 일치하는지 확인한다.
2. oldest queued job 하나를 `(created_at, job_id)`로 선택한다.
3. 이미 target revision이 current desired가 아니면 process를 만들지 않고 job을 `superseded`로 terminalize한다.
4. current면 job `queued -> running`, ordinal 1 attempt `running`, runner/staging identity를 쓰고 authority revision을 1 증가시킨다.
5. exact historical intent prompt를 반환하고 commit한다.

동시 worker 또는 외부 STOP/cancel의 winner는 SQLite transaction 상태가 결정한다. DB busy/conflict의 bounded transaction 재-read는 provider retry가 아니지만, semantic state conflict를 이전 base에 자동 재적용하지 않는다.

## 6. ima2 subprocess, fixed pool, PNG candidate

### 6.1 argv/stdin/staging

production argv는 shell string이 아니라 list로 직접 exec한다.

```text
<ima2-binary> gen --stdin --mode direct --no-size-nudge
  --model <selected-model> --size 1024x1536 --quality high
  --timeout <provider-timeout> -o <job-staging-path> --json
```

prompt bytes는 UTF-8 stdin으로만 보내고 EOF를 닫는다. stdout/stderr는 bounded capture하여 request ID와 failure detail만 DB에 기록하고 prompt나 binary image를 detail에 복제하지 않는다. `shell=True`는 사용하지 않는다. provider timeout보다 약간 큰 runner watchdog이 전체 process tree termination을 시작한다.

`_generation_exec.py`는 `start_new_session=True`로 생성된 group leader이며 Linux parent-death signal을 설정하고 parent가 process identity를 DB에 attach했다는 one-byte start gate를 받을 때까지 ima2를 exec하지 않는다. attach 실패/STOP race에서는 gate를 열지 않고 group을 종료한다. exec 뒤 PID/PGID는 ima2 leader에 유지된다. 이 작은 launcher는 spawn→durable identity 사이 crash window에서 무기록 provider 실행을 막기 위한 exact process boundary다.

### 6.2 fixed concurrency

single durable runner acquisition 뒤 정확히 2개의 long-lived async worker task를 만든다. job별 task나 arbitrary executor size 설정을 공개하지 않는다. 두 worker가 서로 다른 jobs를 실제 동시에 실행할 수 있지만 live generation root는 2를 넘지 않는다. child와 descendants는 pool slot을 반환하기 전에 반드시 reap/settle한다.

### 6.3 candidate validation

exit code 0만으로 성공하지 않는다. child 종료/reap 뒤 staging path가 regular file인지, size > 0인지, Pillow가 format `PNG`로 열고 `verify()`한 뒤 재-open/`load()`하여 실제 pixel decode와 positive dimensions를 완료하는지 확인한다. 그 후 bytes SHA-256을 계산한다. nonzero, watchdog, missing file, empty file, non-PNG, truncated/corrupt decode는 distinct terminal detail로 attempt/job `failed`; staging을 지우고 기존 canonical attribution/bytes를 그대로 둔다.

stdout JSON request ID는 진단 metadata일 뿐 candidate success나 provider success의 대리 판정이 아니다.

## 7. commit-time revision gate와 파일 경계

validated candidate마다 store의 단일 `commit_candidate` transaction이 다음 순서를 소유한다.

1. `BEGIN IMMEDIATE`; current job과 active attempt를 다시 읽는다.
2. job/attempt가 이 exact runner의 `running`이 아니면 commit authority가 없다. `cancelled/interrupted/superseded` late candidate는 staging만 폐기하고 기존 cut을 쓰지 않는다.
3. `cuts.desired_revision == generation_jobs.target_desired_revision`을 **바로 이 transaction에서** 검사한다.
4. mismatch면 attempt는 실제 subprocess 결과를 정직하게 `succeeded`로 닫고 job은 `superseded`; cut과 active authorization은 변경하지 않고 commit한 뒤 staging을 삭제한다.
5. match면 unique immutable canonical path로 candidate를 같은 filesystem에서 atomic rename하고, `cuts.realized_revision/asset_id/path/content_hash`, attempt `succeeded`, job `succeeded`, provider request ID, authority revision 및 active Release Authorization revocation을 같은 DB transaction에 기록한다.
6. DB commit 전 오류면 transaction rollback하고 새 canonical path가 이 transaction에서 생겼을 때만 제거한다. crash가 rename 뒤 DB commit 전에 나면 그 file은 권위가 없는 orphan presence일 뿐이고 currency를 만들지 않는다. 기존/historical canonical 파일을 broad scan/delete하지 않는다.
7. DB commit 뒤 fresh connection으로 exact cut/job/attempt를 읽고 canonical path bytes를 다시 hash/decode할 수 있어야 committed receipt를 반환한다.

기존 canonical path를 덮어쓰지 않으므로 rev 3/B가 먼저 commit된 뒤 rev 2/A가 끝나도 A는 B의 path, identity 또는 bytes를 바꿀 수 없다.

## 8. cancel, STOP, timeout, restart recovery

### 8.1 공통 process-tree termination

termination helper는 recorded PID의 `/proc/<pid>/stat` start token을 확인해 PID reuse를 거부하고, PGID에 SIGTERM을 보낸다. 동시에 `/proc` parent chain으로 root descendants를 수집하여 group을 벗어난 descendants에도 신호를 보낸다. bounded grace 뒤 동일 identity가 살아 있으면 SIGKILL하고, runner-owned child를 `wait()`로 reap한다. 종료 중 새 descendant를 놓치지 않도록 deadline 안에서 group/descendant set을 다시 읽는다. 성공은 non-zombie live member 0이며 단순 signal syscall 성공이 아니다.

### 8.2 cancel 및 global STOP ordering

- pending cancel transaction이 먼저 이기면 job을 `cancelled`로 하고 worker claim이 0 rows가 되어 spawn하지 않는다.
- claim이 먼저 이기면 cancel은 recorded attempt/process identity를 대상으로 termination하고 liveness 0 후 attempt/job `cancelled`를 commit한다.
- STOP은 먼저 `stop_epoch += 1`하고 아직 queued인 모든 job을 `cancelled(global_stop)`로 terminalize한다. captured old epoch worker는 이후 claim/launch gate를 통과하지 못한다.
- 당시 running jobs는 termination 후 `interrupted(global_stop)`로 닫는다. intent/cuts realization columns는 STOP transaction의 update 대상이 아니다.
- process를 죽이지 못했으면 STOP은 성공 반환하지 않고 해당 row를 가짜 terminal로 바꾸지 않는다. 다음 readback은 stop epoch와 여전히 unsettled running identity를 보여야 한다.

### 8.3 startup orphan reconciliation

공식 `run-generation`/future server runner 시작은 worker 생성보다 먼저 다음을 실행한다.

1. `generation_control`의 previous owner PID/start token을 새 process에서 확인한다. 동일 live owner면 두 번째 runner를 거절한다.
2. stale/dead owner면 provisional new owner를 SQLite transaction으로 획득하되 아직 provider work를 claim하지 않는다.
3. DB의 모든 `running` attempt process identity를 termination helper로 정리하고 OS liveness 0을 확인한다. PID가 이미 없으면 그 사실을 기록한다.
4. 같은 transaction에서 남은 `running` attempts/jobs를 `interrupted(startup_recovery)`로 바꾸고 owner/authority revision을 갱신한다. accepted intent, queued가 아닌 terminal history 및 existing realization은 그대로다.
5. recorded staging만 삭제한다. interrupted job을 queued로 되돌리거나 새 attempt/provider call로 자동 재실행하지 않는다.
6. recovery가 완전히 read back된 뒤에만 기존 **queued** jobs를 worker가 claim할 수 있다. 종료 때 owner row는 자신의 exact identity일 때만 clear한다.

recovery 중 orphan termination 실패는 runner startup 실패다. 이후 Block/UI가 이를 Running 정상 상태나 성공으로 가리지 못한다.

## 9. authoritative readback과 상태 전이

### 9.1 lifecycle

```text
job: queued
  -> running
     -> succeeded       (valid PNG + current commit gate)
     -> failed          (exit/timeout/missing/invalid/runner failure)
     -> cancelled       (individual cancel)
     -> interrupted     (global STOP/startup recovery)
     -> superseded      (pre-run or commit-time revision mismatch)
  -> cancelled          (pending cancel/global STOP; no subprocess)
  -> superseded         (claim-time stale; no subprocess)

attempt: running
  -> succeeded | failed | cancelled | interrupted
```

한 job을 재실행하지 않는다. ordinal 1 이후 attempt 생성은 product runner에서 금지하고 explicit user retry는 새로운 job identity다. job이 superseded일 때 process execution 자체가 성공했으면 attempt는 `succeeded`, pre-run stale이면 attempt를 만들지 않는다.

### 9.2 write/read ownership trace

| State/effect | Create/update owner | Deciding read | Reset/removal |
|---|---|---|---|
| desired intent/revision | 기존 `approve_structural_baseline` / `accept_cut_intent` | enqueue와 commit gate의 SQLite row | generation은 변경/철회하지 않음 |
| queue job | `GenerationService.enqueue` 한 transaction | worker claim, snapshot, cancel/STOP | row 삭제 없음; terminal history 보존 |
| attempt/process identity | runner claim + gated launcher attach | cancel/STOP/recovery 및 snapshot | terminal 때 identity/history 보존; OS process만 제거 |
| staging candidate | exact child의 `-o` | PNG validator와 commit gate | success promotion 또는 모든 non-commit terminal에서 unlink |
| canonical realization | current commit gate만 | fresh snapshot + file hash/decode | 기존 bytes 삭제/overwrite 없음 |
| runner owner/stop epoch | runner acquisition / STOP | claim/launch gate와 startup | own clean exit에서 owner clear; epoch 단조 증가 |
| currency/complete | writer 없음; snapshot projection | desired/realized equality | queue/job/file로 보정하지 않음 |

### 9.3 queue와 currency 분리

`snapshot()`은 `generation` 아래 control/queue counts를 추가할 수 있지만 기존 `cuts[*].currency`와 `realization_complete` 계산식을 바꾸지 않는다. 다음 네 상태가 모두 표현 가능해야 한다: queue nonempty+STALE, queue drained+STALE, queue drained+COMPLETE, terminal failed/interrupted jobs+old bytes+STALE. SSE/UI event는 이 Scope에서 만들지 않으며 향후 caller는 snapshot equality를 다시 읽어야 한다.

## 10. 구현 순서와 partial-failure 경계

1. current v1 scratch DB를 만들고 §4.2 migration discriminator를 보존한다.
2. v2 schema/migration/strict verification과 snapshot 확장을 구현하고 v1/v2 fresh-process readback을 확인한다.
3. generation store primitives를 state-specific transactions로 교체한다. 기존 tests/callers를 모두 이관하고 obsolete public writers를 제거한다.
4. one enqueue path와 single runner acquisition/claim을 구현한다. 이 단계에서는 provider success를 주장하지 않는다.
5. gated launcher, exact argv/stdin/staging, pool 2, timeout/tree termination을 연결한다.
6. Pillow decode/hash와 commit-time atomic gate/file promotion을 연결한다.
7. pending/running cancel, global STOP, startup orphan recovery를 연결한다.
8. CLI를 service에 얇게 연결하고 material receipts/exit conditions를 노출한다.
9. §11의 controlled local subprocess scenarios를 실행해 local lifecycle/SQLite boundary를 판별한다.
10. Main이 별도 현재 외부 권한을 준 경우에만 §11.2 actual provider boundary를 한 번 실행한다. 권한/환경이 없으면 `INCONCLUSIVE`를 보존하고 구현 결과나 helper 성공으로 메우지 않는다.

어느 단계에서도 DB 오류를 queue JSON/lock으로 우회하지 않는다. source/schema/interface/process ownership 또는 acceptance readback이 이 Plan과 달라져야 하면 §12 반환 규칙을 적용한다.

## 11. 가장 싼 판별력 있는 self-check와 Acceptance/Exit trace

모든 local check는 isolated temporary project의 실제 on-disk SQLite, 새 DB connection/process, 실제 OS subprocess를 사용하고 종료/cleanup까지 기록한다. helper executable은 production argv를 받고 stdin을 실제 읽어 prompt-derived PNG를 쓰며 필요 시 descendant를 띄우는 ancillary controlled subprocess다. 이는 queue, scheduling, process, staging, decode, race, STOP 경계를 검증하지만 실제 ima2/provider 성공 증거가 아니다.

### 11.1 Local discriminating scenarios

1. **A / Exit 1,3** — exact five prompts를 승인하고 `enqueue(None, R)` 한 번을 호출한다. fresh raw SQLite에서 같은 `generation_jobs` table에 정확히 5개, stable cut `1..5`, 각 acceptance-time target revision이 있는지 확인한다. 이후 single cut enqueue가 같은 method/table/status를 쓰는지 확인한다. project tree에 queue JSON/lock/full-run store가 없어야 한다.
2. **B-success / Exit 2** — 3개 이상 helper jobs를 pool 2로 실행한다. DB process identities와 `/proc` sample로 서로 다른 둘의 live interval overlap과 maximum live roots `2`를 확인한다. helper가 받은 stdin bytes와 job historical prompt가 같고 output은 job staging에만 있었는지 확인한다.
3. **B-failure / D / Exit 7–9** — actual local subprocess 각각을 nonzero, timeout+descendant, missing output, corrupt/truncated PNG로 종료한다. fresh DB에서 job/attempt exact failure detail, process tree liveness 0, staging cleanup, old canonical identity/hash/bytes 불변, latest mismatch `STALE/UNRESOLVED`를 확인한다.
4. **C stale race / Exit 4–7** — 같은 cut rev 2 job A helper를 gate에서 실제 실행 중으로 유지한다. rev 3 intent와 job B를 받아 B의 prompt-derived valid PNG를 먼저 commit한다. A를 늦게 success시킨 뒤 새 connection에서 A job `superseded`, A attempt 실제 `succeeded`, cut desired/realized rev 3, asset identity B를 읽고 B canonical bytes/hash가 A 전후 byte-identical인지 확인한다. process-local completion order나 mock return은 판정에 쓰지 않는다.
5. **pending/running cancel / Exit 7** — pending job cancel 뒤 그 job PID/attempt가 전혀 생기지 않는지 확인한다. descendant를 가진 running helper cancel 뒤 root/group/descendant non-zombie liveness 0, attempt/job `cancelled`, late staging output의 no-commit을 새 DB에서 확인한다.
6. **global STOP / E / Exit 10–12** — 서로 다른 두 long-running helpers가 각각 descendant를 가진 상태를 DB와 OS에서 먼저 관찰한다. 별도 official STOP invocation 한 번 후 모든 recorded group/tree liveness 0, affected running attempts/jobs `interrupted`, queued jobs `cancelled`, accepted desired revisions와 preexisting realization hashes/bytes 불변을 새 process에서 확인한다. API return/stop epoch만으로 통과시키지 않는다.
7. **restart / F / Exit 13–14** — long-running helpers와 process identities가 DB에 기록된 후 runner owner를 SIGKILL한다. 새 official `run-generation` process를 시작해 orphan group/tree가 없어지고 old running rows가 `interrupted(startup_recovery)`가 되는지 확인한다. provider invocation count가 증가하지 않아 interrupted job 자동 재실행이 없고 accepted intents/old realization이 보존되며 mismatch가 STALE인지 확인한다.
8. **queue vs completion / G / Exit 15–16** — empty/terminal-only queue지만 한 cut mismatch인 상태를 만들어 `UNRESOLVED`를 확인한다. 반대로 정확히 다섯 current commits 뒤에만 `COMPLETE`를 확인한다. job success count, file count, staging presence를 바꿔도 equality projection이 바뀌지 않아야 한다.
9. 각 scenario 뒤 child/descendant가 없고 temp directory가 삭제됐는지 확인한다. preexisting path absence를 cleanup 성공으로 대신하지 않고 생성 path 목록과 settlement를 대응시킨다.

### 11.2 실제 provider conditional-first-work

- `plan_anchor`: `§6.1 ima2 argv/stdin/staging` 및 본 절.
- `permitted_initial_work`: Main이 현재 네트워크/provider/quota·비용 권한과 usable model을 명시적으로 확인한 뒤, isolated five-cut project의 한 current cut에 official `comic-new generate --cut`을 정확히 한 번 실행한다.
- `discriminating_observation`: 실제 ima2 process argv/stdin, exit 0, stdout request identity(있는 경우), staging에서 생성된 non-empty decodable PNG, immutable canonical bytes/hash, fresh DB의 same target revision realization 및 `CURRENT`를 함께 관찰한다. DB readback이나 output file 하나만으로 충분하지 않다.
- `dependent_work_not_yet_permitted`: 실제 ima2 성공 주장, provider/model 확정 주장, quota/cost를 수반하는 추가 호출, fallback/retry 추가, BLOCK-03 진입.
- `response_if_refuted`: CLI syntax drift면 영향 argv method와 Plan을 Planner/Main에게 반환한다. credential/provider/quota/network 부재면 구현을 provider 실패로 개조하지 않고 이 boundary를 `INCONCLUSIVE`로 남겨 환경/권한 owner인 Main에게 반환한다. 유효 PNG 없이 exit 0이면 provider success가 아니라 honest job failure로 기록하고 generation method를 재검토한다.

### 11.3 Acceptance A–G 및 BLOCK-02 Exit 1–16 대응

| Scope | Local proof | BLOCK-02 Exit |
|---|---|---|
| A unified all/single acceptance | §11.1.1 | 1, 3 |
| B bounded real subprocess + stdin/staging/PNG/failures | §11.1.2–3; provider 부분은 §11.2 | 2, 3, 8, 9 |
| C late old result structural discard | §11.1.4 | 4, 5, 6, 7 |
| D cancel/failure/timeout preservation | §11.1.3,5 | 7, 8, 9 |
| E STOP physical + durable effects | §11.1.6 | 10, 11, 12 |
| F restart recovery | §11.1.7 | 13, 14 |
| G queue/currency separation | §11.1.8 | 15, 16 |

Self-check는 semantic verification, Exit 충족 판정 또는 Scope 완료 선언이 아니다. verifier handoff target은 current source/schema hashes, scenario commands, exact temp/effect paths, PIDs/PGIDs/start tokens, before/after DB rows, asset hashes/bytes, subprocess exit/stdout/stderr, cleanup 결과 및 실제 provider boundary의 `OBSERVED` 또는 `INCONCLUSIVE` 구분이다.

## 12. 구현 재량, material return, 다음 단계

### 12.1 구현자 재량

동등한 private helper/dataclass 이름, receipt JSON field의 비권위적 표기, SQL index 이름, TERM grace의 작은 bounded 값, request-ID parsing detail은 구현자 재량이다. 다음은 재량이 아니다: one queue/job/commit path, pool 2, SQLite runner/stop/process authority, commit-time revision check, real PNG decode, immutable old bytes, process-tree liveness+DB terminal STOP return, no automatic retry, restart orphan reconciliation, queue/currency 분리.

### 12.2 Plan/Scope/Thesis로 반환하는 변화

- queue/runner owner를 SQLite 밖 sidecar/lock/broker로 옮겨야 함
- full/single이 다른 schema, worker 또는 commit path를 필요로 함
- accepted intent payload에서 generation prompt를 정직하게 결정할 수 없어 product meaning 변경이 필요함
- process tree를 종료·식별할 수 없는 target OS로 effect strategy를 바꿔야 함
- canonical promotion을 current revision transaction gate와 결속할 수 없음
- provider retry/fallback 또는 interrupted auto-resume가 필요하다는 새 정책
- helper/local lifecycle evidence를 real provider success로 취급해야만 acceptance가 가능함
- Scope A–G, Exit 1–16, authoritative readback 또는 Non-Goal을 바꾸어야 함

앞의 interface/ownership/effect/readback 변화는 이 Plan 개정과 새 independent Plan Review가 필요하다. 제품 의미 변화는 THESIS-001 owner, current outcome/Scope 경계 변화는 Scope shaping owner에게 반환한다.

## 13. Plan 완료 경계

이 문서는 exact ready BLOCK-02의 실행 방법만 준비한다. product source/data/schema, Thesis, Scope, Baseline, status 또는 external provider를 변경하지 않았고 구현·검증·Exit verdict를 발행하지 않는다. 다음 단계는 Main이 별도 invocation으로 수행하는 이 exact Plan bytes의 independent Plan Review다. Review `ADMIT`과 currentness 확인은 구현 시작 범위를 열 수 있지만 실제 provider permission을 공급하지 않는다.
