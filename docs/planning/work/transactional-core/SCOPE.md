# Scope: Transactional Core Authority

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md sha256:74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md sha256:5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c

## Outcome

현재 `comic_new`에는 승인된 제품 문서만 있고 실행 가능한 제품 소스나 영속 상태 권위가 없다. 이 Scope는 `BASELINE-001`의 `BLOCK-01 — Core Domain & Single Transactional Authority`를 선택한다.

완료 후 신규 프로젝트는 단 하나의 SQLite transactional authority 안에 정확히 다섯 개의 안정된 ordered cut identity `1..5`, 승인된 Structural Baseline, 각 컷의 단일 Effective Intent와 단조 증가 `desired_revision`, 현재 realization 귀속, composition revision/state, generation job/attempt 사실, Canonical Review Artifact identity, Release Authorization, delivery attempt/outcome을 표현하고 재조회할 수 있다. `Current`와 전체 realization completion은 자산 존재나 실행 상태가 아니라 revision equality로만 판정한다. 프로세스 재시작과 concurrent write 후에도 같은 DB readback이 권위이며 애플리케이션 관리 lock file이나 JSON sidecar는 경쟁 authority가 되지 않는다.

포함: Python 패키지/CLI의 최소 실행 골격, 프로젝트 생성과 authoritative snapshot readback, Structural Baseline 승인, cut intent 수용, receiver-visible composition 변경 수용, realization/job/artifact/authorization/delivery truth를 후속 Block이 같은 authority에서 소유할 수 있는 영속 모델과 transaction API.

제외: 실제 LLM/ima2 실행과 worker pool(`BLOCK-02`), 픽셀 조판(`BLOCK-03`), 웹 UI(`BLOCK-04`), PNG/Blogger 외부 전달 실행(`BLOCK-05`), 과거 `comic` 데이터/파일 형식 호환 또는 마이그레이션, 임의 N-cut 생애주기.

## Acceptance

### A. 정확히 다섯 컷인 신규 권위

빈 프로젝트 경로에서 공식 제품 진입점으로 프로젝트를 생성하고 새 프로세스/새 DB connection에서 authoritative snapshot을 읽으면 cut identity는 정확히 `[1, 2, 3, 4, 5]`이고 추가·삭제·재색인 명령이나 저장 API는 존재하지 않는다. 별도 JSON authority 또는 애플리케이션 `.lock` 파일은 생성되지 않는다.

### B. 승인된 Baseline과 단조 Intent

서로 구분되는 정확히 다섯 컷 intent를 포함한 Structural Baseline을 승인하면 한 transaction 뒤 새 connection에서 승인 identity와 다섯 intent가 재조회된다. 같은 컷에 두 변경을 순서대로 수용하면 `desired_revision`이 매번 엄격히 증가하고 마지막 payload만 Effective Intent이다. 과거 payload로 되돌리는 조작도 revision 감소가 아니라 더 높은 새 revision으로 기록된다.

### C. Composition과 승인 폐기 원자성

receiver-visible composition 변경을 현재 composition revision에 대해 수용하면 revision이 정확히 한 단계 증가하고 변경 상태가 재조회된다. 특정 Canonical Review Artifact에 결속된 Release Authorization이 존재하는 상태에서 receiver-visible 변경이 수용되면 변경과 authorization 폐기가 같은 transaction의 readback으로 관찰되어, 새 composition과 오래된 authorization이 동시에 authoritative한 중간 상태가 없다. stale base revision을 사용한 concurrent writer는 정직한 conflict를 받고 기존 accepted state를 덮어쓰지 않는다.

### D. Currency와 Complete의 정직성

realization이 없는 신규 프로젝트, 또는 다섯 개의 유효한 과거 이미지 경로/asset identity가 저장되어 있어도 하나 이상의 컷에서 `desired_revision != realized_revision`이면 해당 컷은 `STALE`이고 전체 realization은 `UNRESOLVED`이다. 오직 정확히 다섯 컷 모두의 `desired_revision == realized_revision`일 때만 `Complete` readback이 참이다. job 상태, 파일 존재, approval 또는 delivery 상태는 이 판정을 바꾸지 못한다.

### E. Restart와 동시성 보존

Baseline, intent, composition, realization 귀속, job/attempt, artifact, authorization, delivery truth를 기록한 뒤 모든 connection을 닫고 새 프로세스에서 열어도 동일한 authoritative truth가 복구된다. 동일 base revision을 가진 두 독립 writer가 경쟁하면 하나만 수용되고 다른 하나는 conflict가 되며 split-brain Effective Intent나 composition state가 생기지 않는다.

### F. 후속 Block의 단일 권위 경계

후속 generation/composition/release 계층이 사용할 public transaction API와 authoritative snapshot은 위 truth dimensions를 서로 대체하지 않고 별도 필드/레코드로 재조회한다. execution terminal state는 accepted desired intent를 철회하지 않고, authorization은 delivery success를 창조하지 않으며, 외부 delivery 결과는 `confirmed_success`, `confirmed_failure`, `unknown/unresolved`를 구분해 기록할 수 있다.

## Non-Goals

- 실제 generation subprocess, queue worker 또는 STOP 구현
- Canonical Review Artifact 이미지 생성
- Vue/Vite 정적 자산 또는 FastAPI 스튜디오 서버
- 실제 파일 export, Blogger 요청 또는 외부 destination readback
- 과거 `comic` 저장소와의 호환 계층
- 범용 ORM/저장소 추상화, 플러그인 DB, audit/event-sourcing 프레임워크

## Open Decisions

None
