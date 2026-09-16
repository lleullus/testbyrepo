# Scope: Generation Currency and Atomic Interruption Closure

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md sha256:1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md sha256:629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55

## Outcome

현재 생성 작업은 `target_desired_revision`만으로 커밋 자격을 판정한다. 같은 컷·같은 revision의 재생성 요청에는 순서 권위가 없어 늦게 끝난 과거 요청이 더 최신 요청의 픽셀을 덮어쓸 수 있다. 또한 개별 Cancel과 전역 STOP은 실행 프로세스를 종료하기 전에 running job/attempt의 커밋 자격을 원자적으로 박탈하지 않으며, 종료 후 별도 상태 갱신은 이미 성공한 상태를 `cancelled`로 역전시킬 수 있다.

이 Scope는 `BASELINE-002`의 `BLOCK-06`을 선택한다. 각 컷은 단조 증가하는 최신 generation request sequence를 SQLite 권위로 소유하고, 모든 job은 수용 시점의 `(cut_id, target_desired_revision, request_seq)`에 결속된다. claim과 commit은 revision 및 request sequence가 모두 최신인 job만 허용한다. 같은 revision의 새 요청이 수용된 순간부터 그 최신 sequence가 커밋될 때까지 기존 픽셀은 존재하더라도 `STALE`이고 작품 전체는 `UNRESOLVED`이다. 개별 Cancel과 전역 STOP은 물리적 프로세스 종료보다 먼저 하나의 `BEGIN IMMEDIATE` 트랜잭션에서 대상 running job/attempt를 terminal commit-ineligible 상태로 전환한다. 후속 commit은 거절되고, 뒤늦은 cancellation/interruption 마킹은 합법적인 running 상태만 변경하여 이미 성공한 실행 진실을 보존한다.

포함: 신규 프로젝트 schema와 기존 v2 프로젝트의 무손실 migration, snapshot/readback의 request sequence 노출, enqueue/claim/commit currency gate, 개별 Cancel 및 전역 STOP의 선박탈-후종료 순서, FSM 조건부 상태 전이, 기존 canonical realization과 accepted desired intent 보존.

제외: Structural Baseline precondition과 dialogue authority(`BLOCK-07`), release transport/readback(`BLOCK-08`), frontend degraded resync와 전체 cutover 판정(`BLOCK-09`), provider retry/fallback, worker 수 변경, 외부 broker.

## Acceptance

### A. 동일 revision 재생성의 단조 순서와 최신 요청 단일 커밋

활성 baseline과 current intent가 있는 같은 컷에 프롬프트 수정 없이 Job A를 수용한 뒤 Job B를 수용하면, 두 job의 `target_desired_revision`은 같고 Job B의 `request_seq`는 Job A보다 정확히 1 크다. 새 DB connection에서 컷의 `latest_generation_request_seq`가 Job B와 일치하고 두 job의 sequence가 영속 조회된다. Job B의 유효 PNG candidate가 먼저 커밋된 뒤 Job A가 늦게 유효 candidate를 제출해도 Job A는 superseded/discarded가 되고, canonical asset identity·hash·bytes는 Job B 결과 그대로 유지된다.

### B. claim 이전 supersession

같은 컷·같은 revision의 Job A와 Job B가 queued 상태일 때 runner가 큐를 처리하면, 최신 sequence가 아닌 Job A는 provider subprocess를 시작하지 않고 superseded terminal 상태가 된다. Job B만 실행 자격을 얻으며 snapshot의 job/cut sequence readback이 그 판정을 설명한다.

### C. 개별 Cancel 수용 시 원자적 커밋 자격 박탈

running job이 valid candidate 생성을 끝내고 commit 직전인 상태에서 개별 Cancel을 수용하면, Cancel 반환 및 프로세스 종료 시도보다 먼저 같은 DB 트랜잭션에서 해당 running job과 attempt가 `cancelled`로 전환된다. 그 뒤 동일 attempt의 `commit_candidate()`를 호출해도 canonical 픽셀은 바뀌지 않고 candidate는 폐기된다. accepted desired intent와 Cancel 전 canonical realization은 보존되어 해당 컷은 필요 시 정직하게 `STALE`이다.

### D. 전역 STOP 수용 시 원자적 커밋 자격 박탈

둘 이상의 running job이 commit 직전에 있을 때 전역 STOP을 수용하면, `stop_epoch` 증가, queued job 취소, 모든 대상 running job/attempt의 `interrupted` 전환이 하나의 `BEGIN IMMEDIATE` 트랜잭션에서 완료된 뒤에만 process-tree termination이 시작된다. STOP 수용 후 도착하는 모든 candidate commit은 거절되고 canonical 픽셀은 바뀌지 않는다. 새 DB connection의 job/attempt/stop epoch와 OS process settlement가 이 순서를 구분한다.

### E. 성공 상태의 비가역 보존

job과 attempt가 이미 `succeeded`이고 canonical realization이 커밋된 뒤 동일 job에 늦은 Cancel 또는 STOP 후속 마킹이 도착해도 상태는 `succeeded`를 유지하고 canonical asset identity·hash·bytes가 보존된다. 상태 갱신 쿼리는 `running`인 row만 바꾸며 terminal 상태를 다른 terminal 상태로 역전시키지 않는다.

### F. migration 및 기존 상태 보존

실제 v2 schema의 프로젝트에 migration을 적용하면 모든 기존 cut intent, desired/realized revision, canonical asset identity, job/attempt terminal 상태와 release 자료가 보존된다. 각 컷의 `latest_generation_request_seq`와 각 기존 job의 `request_seq`는 기존 생성 순서를 결정적으로 반영하는 양의 값으로 backfill되고, 이후 신규 enqueue가 그 최댓값 다음 sequence를 사용한다. migration 후 schema 검증과 snapshot readback이 새 권위를 확인한다.

### G. 실패와 종료 정직성 보존

process-tree 종료가 실패해도 이미 수용된 Cancel/STOP의 commit-ineligible 상태를 running으로 되돌리지 않으며, API/service 결과는 물리적 settlement 실패를 성공으로 위장하지 않는다. 반대로 이미 성공한 job을 settlement 실패 처리로 취소/중단 상태로 덮어쓰지 않는다. 어떤 경로도 accepted desired intent나 기존 canonical realization을 삭제하지 않는다.

### H. sequence-bound currency의 정직한 투영

현재 realized revision과 desired revision이 같더라도 더 큰 최신 request sequence의 job이 수용되어 아직 성공 커밋되지 않았다면 해당 컷은 `STALE`이고 작품 전체는 `UNRESOLVED`이다. 최신 request sequence가 canonical로 성공 커밋된 뒤에만 컷이 다시 `CURRENT`가 되며, 이 판정은 파일 존재나 과거 job 성공 수로 보정되지 않는다.

## Non-Goals

- Structural Baseline 없는 intent/generation 차단 또는 dialogue 동기화
- Blogger/PNG 전달 시그니처, 인메모리 전송, 목적지 마커 검증
- SSE gap recovery와 frontend consequential-action 잠금
- generation provider retry, fallback, 작업 우선순위 또는 worker concurrency 변경
- 과거 job history 삭제 또는 별도 audit/sidecar 권위 추가

## Open Decisions

None
