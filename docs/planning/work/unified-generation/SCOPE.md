# Scope: Unified Generation Engine

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md sha256:74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md sha256:5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c

## Outcome

`BASELINE-001`의 `BLOCK-01`은 exact-five SQLite authority, monotonic intent, commit-time currency, restart readback과 honest conflict를 실제 검증하고 완료 기록했다. 현재 `comic_new`에는 generation job/attempt/realization 메타데이터 transaction API만 있으며, accepted intent를 ima2 subprocess로 실행하는 queue owner, worker pool, 전역 STOP, restart recovery가 없다. 이 Scope는 `BLOCK-02 — Single Unified Generation Engine & Runner`를 선택한다.

완료 후 전체 생성과 개별 컷 생성은 동일한 SQLite-backed durable queue와 동일한 job type으로 수용된다. 전체 생성은 현재 다섯 컷에 대해 그 job을 다섯 번 enqueue하는 상위 조작일 뿐 별도 실행·커밋 경로가 아니다. 제한된 비동기 worker pool은 각 job의 `cut_id`와 enqueue 시점 `target_desired_revision`에 결속된 ima2 subprocess를 실행해 staging candidate를 만들고, 바로 commit 직전에 BLOCK-01 authority를 다시 읽어 현재 revision 결과만 canonical realization으로 승격한다. 오래되거나 superseded/cancelled/interrupted 된 결과는 늦게 성공해도 canonical asset을 바꾸지 않는다.

backend global STOP은 실행 중인 generation subprocess와 그 process tree 모두에 즉시 종료를 요청하고, accepted desired intent와 기존 realization bytes는 보존하면서 실행 truth만 정직한 terminal 상태로 영속화한다. 서버/runner 재시작은 이전 프로세스의 `running` 사실을 계속 실행 중인 것처럼 가장하지 않고 orphan work를 `interrupted` 등 정직한 상태로 정리한다. Queue drain과 job success는 currency를 대리하지 않으며 정확히 다섯 revision equality만 Complete를 만든다.

포함: 하나의 queue/runner/worker pool, ima2 CLI argv/stdin/staging integration, 전체/개별 enqueue, 제한 동시성, cancel/global STOP/process-tree termination, timeout/failure, staging cleanup, restart reconciliation, canonical realization commit gate, 공식 로컬 CLI 또는 후속 서버가 직접 사용할 좁은 service API와 상태 readback.

제외: LLM 콘티 작성, canonical composition/lettering/review artifact bytes(`BLOCK-03`), Vue/FastAPI studio UI와 SSE projection(`BLOCK-04`), PNG/Blogger release(`BLOCK-05`), cloud broker, queue sidecar/lock registry, automatic provider fallback, arbitrary N-cut.

## Acceptance

### A. 전체와 개별 생성의 단일 수용 경로

승인된 five-cut baseline과 current intents가 있는 프로젝트에서 전체 생성 조작을 수용하면 동일한 durable `generation_jobs` schema에 정확히 다섯 job이 생기고 각 row가 안정된 `cut_id 1..5`와 수용 당시 `target_desired_revision`을 가진다. 이후 한 컷의 개별 생성 조작을 수용해도 같은 enqueue service, 같은 table/status model, 같은 worker execution/commit path를 사용한다. 별도 full-run queue, JSON queue, lock file, direct-to-canonical writer는 존재하지 않는다.

### B. 제한 동시성과 실제 subprocess 경계

worker pool concurrency를 2로 두고 둘 이상의 서로 다른 cut job을 실행하면 실제 child subprocess 실행 구간이 겹치되 동시에 살아 있는 generation process 수는 2를 넘지 않는다. 각 process는 해당 intent prompt를 stdin으로 받고 job별 staging output만 쓴다. 성공 candidate는 비어 있지 않은 해독 가능한 PNG로 확인된 뒤에만 commit gate로 이동하고, provider nonzero exit·timeout·missing/invalid output은 job/attempt 실패로 영속화되며 canonical realization을 변경하지 않는다. 실제 ima2 provider 성공의 검증에는 현재의 별도 외부 실행 권한과 사용 가능한 provider 환경이 필요하며, 그 권한이 없을 때 로컬 대역 성공을 ima2 성공으로 주장하지 않는다.

### C. 늦은 과거 결과의 구조적 폐기

같은 cut의 rev 2 job A를 실제 subprocess 실행 중에 둔 뒤 rev 3 intent와 job B를 수용하고 B의 valid candidate를 먼저 완료시키면 canonical realization은 rev 3과 B asset identity를 가진다. 그 후 A가 성공 종료하고 valid PNG를 남겨도 commit-time authoritative readback이 이를 stale/superseded로 판정하며 rev 3 canonical asset bytes/identity를 바꾸지 않는다. 이 결과는 process-local 순서 추정이 아니라 새 DB connection의 job/cut readback과 canonical asset identity/bytes로 판별한다.

### D. 취소·실패·타임아웃의 보존

pending job을 취소하면 subprocess가 시작되지 않고 terminal cancellation이 영속화된다. running job을 취소하거나 timeout/failure가 발생하면 해당 process tree가 종료·수거되고 terminal job/attempt truth와 원인이 재조회된다. superseded/cancelled/interrupted job의 late output은 canonical commit을 얻지 못한다. 어떤 실패도 기존 canonical realization bytes를 삭제하지 않으며 최신 desired revision이 미실현이면 기존 realization은 `STALE`, 전체 작품은 `UNRESOLVED`이다.

### E. 전역 STOP의 물리적·영속적 효과

둘 이상의 장시간 generation job이 실제 parent/child process tree를 실행 중일 때 backend global STOP을 한 번 호출하면 모든 실행 중 generation process tree에 즉시 termination이 요청되고 bounded escalation 뒤 살아 있는 generation descendant가 남지 않는다. STOP API/명령의 반환이나 `stop_requested` flag만으로 성공을 판정하지 않고 OS process liveness와 DB terminal readback을 함께 확인한다. 이미 accepted 된 desired revisions와 기존 realization은 보존되며 affected job/attempt는 `interrupted` 또는 실제 종료 원인을 나타내는 terminal 상태가 된다.

### F. 강제 종료 뒤 restart recovery

runner process를 generation 도중 강제 종료하여 DB에 이전 `running` job/attempt가 남은 상태에서 공식 runner/server startup recovery를 수행하면 존재하지 않는 process를 계속 Running으로 표시하지 않고 orphan rows를 transactionally `interrupted`로 정리한다. 새 process snapshot은 accepted desired intent를 그대로 보존하고, 기존 realization이 새 desired revision보다 오래되면 `STALE`로 표시한다. recovery는 provider call을 자동 재실행하거나 intent를 철회하지 않는다.

### G. Queue 상태와 realization completion 분리

queue가 비었거나 모든 job이 terminal이어도 하나 이상의 cut에서 `desired_revision != realized_revision`이면 전체 realization은 `UNRESOLVED`이다. 반대로 exactly five cuts가 모두 revision equality를 만족할 때만 `COMPLETE`이며 이 판정은 queue length, job success count, staging/canonical 파일 존재 여부로 보정되지 않는다.

## External Conditions

실제 ima2 provider 호출은 네트워크·provider quota/비용을 수반할 수 있는 외부 효과다. 구현과 로컬 process-lifecycle/commit-gate 검증은 외부 호출 없이 수행할 수 있으나, 실제 ima2 성공 경계를 검증해야 하는 시점에는 Main이 별도의 현재 권한과 provider 가용성을 확인한다. 권한이나 환경이 없으면 해당 경계는 `INCONCLUSIVE`이며 mock/helper 결과로 대체하지 않는다.

## Non-Goals

- 별도의 전체 생성 엔진 또는 direct canonical writer
- generation queue JSON/lock file, 외부 broker, cloud worker
- worker pool 외의 범용 task framework
- provider fallback chain, 자동 retry 정책, history/audit UI
- 조판, 브라우저 UI/SSE, release 또는 destination readback
- accepted intent 자동 철회, 실패 시 기존 realization 삭제

## Open Decisions

None
