# Scope: Canonical Composition & Review Artifact Stitcher

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: ready

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md sha256:74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md sha256:5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c

## Outcome

`BLOCK-01`은 SQLite 단일 트랜잭션 권위, exact-five cut identity, monotonic intent, composition revision, review artifact identity/registration, release authorization binding/revocation, delivery attempt/outcome recording을 완료 검증했다. `BLOCK-02`는 동일 queue/worker pool, ima2 subprocess lifecycle, commit-time currency gate, global STOP/restart recovery를 완료 검증했다.

현재 `comic_new`에는 정확히 다섯 컷의 canonical realization을 받아 normalized percentage geometry, bubble text, typography, cut gap을 하나의 composition schema로 해석하고, 서버 측 PIL renderer가 immutable Canonical Review Artifact를 실체화하는 compositor가 없다. `review_artifacts`/`artifact_cuts` 등록 API와 five-current gate, composition revision binding, authorization identity 결속은 이미 `BLOCK-01` store에 존재하지만, 실제 composition 입력 정규화와 PIL 픽셀 materialization은 아직 구현되지 않았다.

이 Scope는 `BASELINE-001`의 `BLOCK-03 — Canonical Composition & Review Artifact Stitcher`를 선택한다.

완료 후 canonical compositor는 정확히 5개의 Current realization asset, 고정된 컷 순서, canonical composition surface 기준 normalized percentage 좌표(`x_pct`, `y_pct`, `w_pct`, `h_pct`)의 bubble geometry, bubble text, typography/style, cut gap을 하나의 composition schema로 받아들인다. 서버 측 단일 PIL renderer가 이 정규화된 입력으로부터 하나의 immutable Canonical Review Artifact 이미지를 실체화한다. 생성된 artifact는 안정된 `artifact_id`, content hash, composition revision, five desired/realized revision identities를 결속한 identity로 기존 `register_review_artifact` API를 통해 SQLite authority에 등록된다. artifact bytes를 다시 읽으면 hash가 일치하고, 생성 후 editor state가 바뀌어도 기존 artifact bytes 자체는 변하지 않는다. text wrapping과 typography의 final truth는 PIL canonical renderer가 소유하며, browser DOM reconstruction이나 PNG/Blogger downstream의 독립적 text reflow/bubble relayout이 필요 없는 artifact boundary가 확립된다. 동일 accepted composition에서 review path와 export source가 동일 canonical artifact identity를 사용할 수 있다.

포함: composition 입력 정규화 schema 해석, canonical composition surface 위의 five-cut asset stitching과 gap 처리, normalized percentage bubble geometry positioning, bubble text rendering과 PIL typography, 서버 측 단일 PIL canonical renderer, immutable artifact bytes 생성과 content hash 계산, 기존 `register_review_artifact` transaction API를 통한 artifact identity/cut closure 등록, exact-five Current realization gate 적용, 후속 review/export/release가 동일 artifact identity를 참조할 수 있는 materialization service API.

제외: 실제 LLM/ima2 이미지 생성(`BLOCK-02`에서 완료), Vue/Vite 프론트엔드 interactive projection/canvas editor/ReviewModal(`BLOCK-04`), PNG file export/Blogger delivery 실행(`BLOCK-05`), release authorization 생성/revocation 실행(이미 `BLOCK-01` store에 존재, `BLOCK-05`에서 end-to-end 검증), 브라우저 화면에 artifact를 표시하는 UI, 과거 `comic` 데이터 호환, 임의 N-cut, 범용 rendering framework.

## Acceptance

### A. Normalized percentage geometry의 viewport 독립성

canonical composition surface 크기를 고정한 상태에서 동일한 `x_pct`, `y_pct`, `w_pct`, `h_pct` 좌표로 bubble을 배치하면 surface 크기와 무관하게 bubble의 상대 위치와 상대 크기가 동일하다. 실제 artifact pixel 좌표를 readback했을 때 percentage 좌표에서 계산한 기대 pixel 좌표와 일치한다.

### B. 정확히 다섯 cut asset 필수

canonical compositor에 정확히 5개의 cut asset을 제공하면 materialization이 성공한다. 4개 이하의 cut asset을 제공하면 compositor가 materialization을 거부한다.

### C. 개별 cut decode/render 실패 시 전체 실패

5개 cut 중 하나의 이미지 파일을 읽을 수 없거나(missing/corrupt) decode할 수 없게 만들면 전체 materialization이 실패한다. 4컷만으로 부분 artifact를 생성하는 silent skip/continue 경로가 존재하지 않는다.

### D. Five Current 조건 미충족 시 materialization 거절

5개 컷 중 하나 이상에서 `desired_revision != realized_revision`이면 review artifact materialization이 거절된다. 이는 기존 `register_review_artifact`의 `RealizationIncompleteError`와 일관된다.

### E. Authoritative composition으로 immutable artifact 생성

authoritative composition state(composition revision, geometry, text, typography, gap)를 입력으로 PIL renderer가 immutable artifact image를 생성하고, 생성된 bytes의 content hash가 계산된다.

### F. Artifact identity 결속

생성된 artifact가 등록되면 최소 다음 identity가 결속된다: `artifact_id`, content hash, composition revision, five cuts 각각의 desired/realized revision과 asset_id. 이는 기존 `review_artifacts`/`artifact_cuts` schema와 `register_review_artifact` API가 강제하는 구조이며, compositor의 cut closure 출력이 이 요구를 만족한다.

### G. Artifact bytes readback hash 일치

동일 artifact bytes를 생성 직후와 별도 파일 읽기로 재확인했을 때 content hash가 일치한다.

### H. Editor 변경 후 기존 artifact bytes 불변

artifact 생성 후 composition state(bubble text, geometry, gap 등)를 `accept_composition`으로 변경하더라도 이미 생성된 artifact 이미지 파일의 bytes와 hash가 변하지 않는다. 새 composition은 새 artifact materialization을 요구한다.

### I. PIL renderer가 text wrap/typography의 final truth를 소유

artifact 이미지 내의 text rendering(줄바꿈, 폰트 크기, 배치)은 PIL canonical renderer가 결정하며, browser DOM이 text를 재구성할 필요 없이 artifact bytes가 최종 시각 진실이다.

### J. Downstream이 독립적 text reflow/bubble layout을 수행하지 않아도 되는 artifact boundary

materialized artifact는 자체 완결적인 pixel image이므로 PNG export source나 review display가 text reflow, font recalculation, bubble relocation을 재수행할 필요가 없다. Downstream은 이 artifact의 identity를 참조하여 composition-preserving transformation(encoding 변환, uniform scaling)만 수행하면 된다.

### K. Review path와 export source의 동일 artifact identity 공유

동일 accepted composition에서 materialized된 artifact의 `artifact_id`를 review path와 export/release source가 동일하게 참조할 수 있다. 서로 다른 composition reconstruction을 사용하지 않는다.

## External Conditions

실제 PIL rendering은 Pillow 라이브러리 가용성과 서버 환경의 font 파일 접근에 의존한다. 검증 시점에 Pillow가 설치되어 있고 최소 하나의 사용 가능한 font가 있으면 compositor의 전체 경계를 검증할 수 있다. Font가 없는 환경에서는 text rendering 세부가 `INCONCLUSIVE`일 수 있으나, geometry positioning과 cut stitching은 font 없이도 검증 가능하다.

## Non-Goals

- Vue/Vite 프론트엔드 UI 또는 ReviewModal 구현
- PNG file export 실행 또는 Blogger delivery 실행
- Release authorization 생성/revocation 실행 (store API는 이미 존재)
- 브라우저 interactive projection/canvas editor
- LLM/ima2 이미지 생성
- 범용 rendering framework 또는 canvas 라이브러리 도입
- 과거 `comic` 데이터 호환/마이그레이션
- 임의 N-cut 지원

## Open Decisions

None
