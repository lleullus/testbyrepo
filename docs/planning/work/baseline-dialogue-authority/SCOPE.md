# Scope: Structural Baseline and Dialogue Authority

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md sha256:1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md sha256:629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55

## Outcome

`BASELINE-002`의 `BLOCK-06`은 완료되었다. 현재 새 프로젝트의 `authority.current_baseline_id`가 `NULL`이어도 `accept_cut_intent()`가 `baseline_id=NULL`인 intent row를 만들 수 있고, 의도만 존재하면 생성 enqueue도 수용된다. 또한 서사적 대사는 `cut_intents.payload_json.dialogue`와 `composition.state_json.bubbles[].text`에 독립 저장되어 서로 다른 값이 동시에 정본처럼 조회·렌더링될 수 있다.

이 Scope는 `BLOCK-07`을 선택한다. 활성 Structural Baseline은 컷 의도 수용과 생성 enqueue의 서버/SQLite 트랜잭션 선행조건이다. `CutIntent.dialogue`가 컷별 서사 대사의 유일한 권위다. intent 또는 re-baseline으로 대사가 바뀌면 해당 컷의 모든 기존 말풍선 텍스트가 같은 트랜잭션에서 새 dialogue로 동기화된다. 조판 저장에서 한 컷의 말풍선 텍스트가 현재 dialogue와 다르게 제출되면, 그 컷의 모든 말풍선이 동일한 단일 텍스트를 가질 때만 해당 텍스트를 새 Cut Intent revision으로 원자 수용하고 조판과 intent를 함께 저장한다. 같은 컷에 서로 다른 말풍선 텍스트를 제출하는 이중 권위는 거절한다. 기하·스타일만 바뀌고 텍스트가 현재 dialogue와 같으면 intent revision은 증가하지 않는다.

포함: schema migration과 무손실 기존 데이터 동기화, DB trigger 및 store transaction guard, HTTP 오류 투영, baseline/intent/composition/generation production paths, snapshot·renderer·frontend readback, 승인 철회와 currency 보존.

제외: BLOCK-08 전달 바이트/목적지 readback, BLOCK-09 degraded resync와 cutover, 다중 서사 branch, 컷별 복수 독립 대사, provider retry/fallback.

## Acceptance

### A. baseline 없는 의도 수용 차단

초기화 직후 `current_baseline_id=NULL`인 프로젝트에서 store 및 `POST /api/cuts/{cut_id}/intent`로 의도를 수용하면 `BaselineRequiredError`와 정직한 409/412 응답으로 거절되고 authority revision, cuts, cut_intents, composition과 파일이 바뀌지 않는다. 직접 SQL로 `baseline_id=NULL` intent를 삽입하려 해도 DB trigger가 거절한다.

### B. baseline 없는 생성 차단

같은 초기 상태에서 단일 컷 및 전체 생성 enqueue를 store/API로 요청하면 모두 거절되고 generation request sequence와 job row가 생기지 않는다. 활성 baseline 승인 후 동일 요청은 기존 sequence-bound enqueue 경로로 수용된다.

### C. baseline 결속과 re-baseline

baseline 승인 트랜잭션은 정확히 5개 intent를 새 활성 baseline에 결속하고 `current_baseline_id`를 설정한 뒤에만 성공한다. 이후 intent 수용과 job enqueue는 그 활성 baseline의 current intent만 사용한다. Re-baseline은 새 baseline과 정확히 5개 새 intent를 원자 수용하고 모든 컷을 STALE/UNRESOLVED로 만들며 기존 활성 release authorization을 철회한다.

### D. intent 대사 변경의 조판 동기화

기존 composition에 한 컷의 말풍선이 하나 이상 있을 때 `accept_cut_intent()` 또는 intent API로 그 컷의 dialogue를 변경하면 새 desired revision과 dialogue가 기록되고, 같은 트랜잭션에서 해당 컷의 모든 `bubbles[].text`가 새 dialogue로 바뀌며 composition revision이 실제 변경 시 정확히 1 증가한다. 다른 컷의 말풍선·기하·스타일은 보존되고 authorization은 철회된다.

### E. 조판 대사 편집의 intent 원자 수용

활성 baseline 아래에서 한 컷의 모든 말풍선 text를 동일한 새 값으로 제출하는 composition 저장은 해당 컷에 정확히 하나의 새 Cut Intent revision을 생성하고 desired revision, bubble text, composition revision, authority revision과 authorization 철회를 하나의 트랜잭션에서 확정한다. prompt와 baseline 결속은 보존된다. 새 dialogue 때문에 그 컷은 STALE/UNRESOLVED가 되고 최신 generation sequence/currency 규칙은 유지된다.

### F. 대사 이중 권위 거절

같은 컷의 여러 말풍선에 서로 다른 text를 제출하거나, 유효한 CutIntent dialogue로 결정할 수 없는 composition을 제출하면 전체 저장이 거절된다. intent/composition/authority revision, authorization, canonical realization과 draft 원본은 부분 변경되지 않는다.

### G. 기하·스타일 전용 편집 보존

모든 bubble text가 해당 컷의 current dialogue와 같고 좌표·크기·색·폰트·gap만 바뀐 composition 저장은 composition revision만 증가시키며 Cut Intent desired revision과 generation request sequence는 증가시키지 않는다. authorization은 최종 조판 변경 규칙대로 철회된다.

### H. migration과 전 경로 단일 대사 readback

기존 schema 프로젝트를 새 revision으로 열면 모든 기존 intent, realization, job, artifact와 delivery history가 보존된다. 기존 composition bubble text는 활성 current CutIntent dialogue로 결정적으로 동기화되고, 실제 텍스트 변경이 있으면 composition/authority revision과 authorization 철회가 일관되게 반영된다. 이후 store snapshot, HTTP snapshot, 편집 캔버스, PIL materialization metadata/픽셀에서 한 컷의 dialogue와 bubble text가 모순되지 않는다.

## Non-Goals

- 한 컷의 여러 독립 서사 대사 또는 bubble별 별도 narrative authority
- Structural Baseline 자동 생성이나 UI 우회 fallback
- generation request sequence, STOP/Cancel FSM의 재설계
- Blogger/PNG 전달 및 destination content identity
- SSE degraded resync 정책과 production cutover 판정

## Open Decisions

None
