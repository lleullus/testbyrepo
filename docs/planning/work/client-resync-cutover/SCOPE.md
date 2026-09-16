# Scope: Client Resync Safety and Empirical Cutover

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md sha256:1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md sha256:629ac544e3a08a14d986f53ff895bac26988bdab8034988e5c1df17d1a11fc55

## Outcome

`BLOCK-06`, `BLOCK-07`, `BLOCK-08`은 순서대로 완료되었다. 현재 프론트엔드는 SSE revision gap에서 snapshot 재조회에 실패해도 `gapFetchPending=false`로 되돌려 기존 `server` 스냅샷을 다시 current처럼 취급한다. 단순 SSE `onerror`도 `reconnecting` 표시만 바꾸고 생성·승인·릴리즈 권한을 유지한다. 따라서 연결 단절이나 gap 복구 실패 동안 오래된 브라우저 상태로 중대한 상태 전이를 요청할 수 있다.

이 Scope는 `BASELINE-002`의 최종 `BLOCK-09`를 선택한다. 프론트엔드는 스트림 연결과 권위 snapshot freshness를 하나의 명시적 상태 기계로 관리한다. 최초 snapshot과 정상 SSE 연결이 확인된 상태만 `OPEN`이며, SSE 단절·revision gap·boot change·replay miss·복구 fetch 실패는 즉시 `DEGRADED / RESYNC_REQUIRED`로 전이한다. `DEGRADED`는 snapshot 재조회 또는 그와 동등한 최신 authoritative snapshot event를 성공적으로 수용하기 전까지 유지한다. 이 동안 로컬 드래프트는 보존하지만 생성, baseline/intent/composition 저장, review materialize, 승인, PNG export, Blogger 발행 같은 중대한 mutation은 차단한다. 실행 중 작업의 STOP/Cancel은 안전 조치이므로 허용한다. 복구 성공 뒤에만 current 권한을 되살리며 오래되거나 모순된 복구 응답은 권한을 되살리지 않는다.

같은 안정된 최종 target에서 4대 Counterexample Gate를 실제 프로세스·SQLite·HTTP·브라우저·통제 네트워크 결함 주입으로 다시 실측한다. Gate 1은 최신 generation request sequence만 Current/완료를 만들 수 있음을, Gate 2는 승인 뒤 1글자/1px 변경이 즉시 승인을 철회함을, Gate 3은 STOP 수용 뒤 늦은 provider 결과가 canonical pixel을 커밋하지 못함을, Gate 4는 destination content marker 검증 전까지 성공을 만들지 못함을 증명한다. 전체 backend/frontend suite, production build/static asset preflight, 실제 `comic-new serve` 브라우저 smoke, 최종 SQLite/HTTP/UI readback이 모두 같은 target에서 통과할 때만 프로덕션 컷오버 완료가 가능하다.

포함: Pinia stream 상태·resync 로직, EventSource 상태 계약, consequential-action 가드 및 degraded UI 표시, focused 브라우저/스토어 회귀, 4대 Gate 전수 fresh 검증, 전체 suite/build/production smoke, final authoritative readback.

제외: 새 제품 기능, 새 provider/destination, 배포·실계정 Blogger 발행, 멀티유저/분산화, 완료 판정을 위한 요구 약화나 mock-only 대체.

## Acceptance

### A. 단절 즉시 DEGRADED 전이

정상 `OPEN`에서 SSE `onerror` 또는 연결 단절이 관찰되면 기존 server snapshot이 남아 있어도 즉시 `DEGRADED / RESYNC_REQUIRED`로 전이한다. `hasCurrentSnapshot`은 false가 되고 생성·저장·조판 실체화·승인·PNG export·Blogger 발행은 모두 비활성화된다. 로컬 draft, 선택 상태와 표시 중인 마지막 snapshot은 진단/복구를 위해 보존된다. 실행 중 job의 STOP/Cancel은 계속 사용할 수 있다.

### B. gap 복구 실패의 fail-closed 유지

`revision-gap`, `boot-changed`, `replay-miss` 이벤트는 중복 fetch를 하나로 합치면서 즉시 DEGRADED로 전이한다. snapshot fetch가 네트워크 오류, 5xx, invalid payload로 실패하면 pending 플래그만 풀고 stale snapshot을 current로 복원하지 않는다. 상태는 DEGRADED로 남고 모든 중대한 액션이 계속 차단된다. 반복 gap/open 신호는 안전한 새 복구 시도를 시작할 수 있지만 병렬 fetch나 권한 깜박임을 만들지 않는다.

### C. 식별 가능한 최신 snapshot에서만 복구

복구 fetch 또는 `studio.snapshot` 이벤트가 현재보다 같거나 높은 authority revision의 내부 일관된 snapshot을 제공하고 이벤트 revision과 payload revision이 일치할 때만 `OPEN`으로 복구한다. pending fetch보다 최신 SSE snapshot이 먼저 오면 최신 것을 유지하며 늦은 오래된 fetch가 rollback하지 않는다. 낮은 revision, 이벤트/payload revision 불일치, malformed event는 DEGRADED를 해제하지 않는다. 복구 후에만 consequential action 가드가 다시 true가 될 수 있다.

### D. 실제 UI fail-closed와 draft 보존

production build를 실제 `comic-new serve`로 열고 EventSource gap/단절 및 snapshot fetch 실패를 주입하면 헤더에 DEGRADED/재동기화 필요 상태가 접근 가능하게 표시되고 생성·승인·내보내기·발행 버튼이 disabled이다. 저장 전 로컬 composition/intent draft는 그대로 보존된다. 차단된 버튼/액션은 HTTP mutation을 보내지 않는다. fresh snapshot 복구 후 표시와 권한이 정상화되고 draft base-change 규칙은 기존대로 정직하게 적용된다.

### E. Gate 1 — Currency

동일 desired revision에 대한 다중 generation 요청과 완료 순서를 실제 runner/provider 제어점에서 뒤집어도 최신 request sequence와 일치하는 성공만 canonical realization을 커밋한다. 이전 요청의 성공·디스크 PNG 존재·취소/실패 이력은 Current 또는 전체 완료를 만들지 못한다.

### F. Gate 2 — Identity

5컷 Current artifact를 2차 승인한 뒤 실제 HTTP/UI 경로로 말풍선 텍스트 1글자 또는 gap 1px을 수용하면 동일 SQLite 트랜잭션에서 활성 Release Authorization이 철회된다. 이전 artifact/authorization으로 export·Blogger 발행은 차단되고 새 materialize/승인 전까지 릴리즈 권한이 돌아오지 않는다.

### G. Gate 3 — Interruption

실제 generation subprocess가 candidate staging을 완료하고 canonical commit 직전 제어점에 있을 때 STOP을 수용한다. STOP 트랜잭션 뒤 늦게 도착한 provider 결과와 subprocess 종료가 canonical cut pixel/realization을 바꾸지 않으며 job/attempt는 interrupted/cancelled 사실과 STALE/UNRESOLVED 상태를 정직하게 유지한다. 프로세스·staging·SSE effect가 정리된다.

### H. Gate 4 — External Truth

통제 Blogger HTTP 목적지가 timeout, truncated/invalid body, 200 missing/wrong marker를 반환하면 attempt는 각각 unknown 또는 confirmed_failure로 남고 성공 UI/SQLite 상태가 생성되지 않는다. exact artifact ID와 SHA-256 marker가 원격 본문에서 유일하게 readback된 경우에만 confirmed_success가 된다. unknown reconcile은 새 publish 없이 같은 attempt를 검증한다.

### I. Final Authoritative Readback and Cutover

동일한 stable target에서 전체 backend suite, frontend Vitest/typecheck, production frontend build가 통과한다. 새 build의 hashed JS/CSS를 단일 `comic-new serve`가 strict preflight 후 제공하고 실제 Chromium에서 초기 load, OPEN, DEGRADED 차단, 복구, 핵심 5-cut workflow 상태를 읽는다. 최종 SQLite·HTTP snapshot·UI가 baseline, exactly five cuts, currentness, active jobs, canonical artifact, authorization, delivery attempt, stream freshness를 모순 없이 나타내며 잔류 subprocess/임시 staging/열린 서버가 없다. A-H가 모두 통과한 이 증거에 한해서만 Main이 `BASELINE-002` 전환과 요청 전체를 완료 기록한다.

## Non-Goals

- 실제 외부 Blogger 게시 또는 production 배포
- 새 기능·새 배포처·임의 N-cut
- DEGRADED 중 생성/승인/릴리즈를 허용하는 optimistic fallback
- STOP/Cancel 안전 조치 차단
- 과거 블록의 verified 결과만 재인용하고 현재 통합 target을 실행하지 않는 최종 판정

## Open Decisions

None
