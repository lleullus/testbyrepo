# Scope: Release Authorization & Destination Readback

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md sha256:74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md sha256:5ffa28c31d867e9c23233b0023b3215978ade3291e9254b70c9ccef5e61cce6c

## Outcome

`BLOCK-01`부터 `BLOCK-04`까지는 SQLite 단일 트랜잭션 권위, exactly-five cut identity, monotonic intent/currency, 통합 generation queue/runner와 실제 process-tree STOP, PIL 기반 canonical review artifact 실체화, 그리고 단일 프로세스 `comic-new serve`로 제공되는 Vue 3 Studio Shell을 순차적으로 완료 검증했다. `BLOCK-04`는 독립 검증 `VERIFIED`, Coverage `COMPLETE / Findings: None`으로 완료 기록되었으며, 선행 블록들의 Exit와 Safe Continuation 조건이 모두 실측 충족되었다. 따라서 `BASELINE-001`의 전환 권위 아래 현재 선택된 유일한 결과는 `BLOCK-05 — Release Authorization & Destination Readback`이다.

현재 실제 제품에는 SQLite 스키마에 `release_authorizations` 및 `delivery_attempts` 테이블이 정의되어 있고, `TransactionalStore`에 기초적인 authorization/delivery 메서드가 존재하며, FastAPI 서버에 검토물 승인 handoff 엔드포인트(`/api/review-artifacts/{artifact_id}/authorize`)가 연결되어 있다. 그러나 창작자가 눈으로 확인한 `Canonical Review Artifact`의 identity/hash에 결속되는 영속 승인 생명주기, 수신자 인지 가능 변경 시 즉시 승인 취소되는 Release Closure, STALE 컷이나 부분 합성 실패 시 외부화를 원천 차단하는 All-or-Nothing 검증, 승인 정본을 재조판 없이 그대로 내보내는 PNG Export 파이프라인, Blogger 전달 어댑터 및 목적지 Readback, 응답 불명확 시의 정직한 `Unknown` 처리, 그리고 4대 Counterexample Gate는 아직 하나의 통합된 완결 릴리즈 체계로 완성되거나 검증되지 않았다.

본 Scope의 선택된 결과는 창작자가 눈으로 검토·승인한 단일 Canonical Review Artifact를 All-or-Nothing 방식으로 외부화하고, 로컬 권위와 외부 목적지 진실의 경계를 끝까지 보존하여 5-Truth Chain을 닫는 것이다. 2차 승인은 화면에 표시된 exact `artifact_id`와 content hash에 결속되어 SQLite에 영속화되며, 서버 재시작 후에도 보존된다. 승인 이후 말풍선 텍스트 한 글자, 기하 좌표, 컷 간격(Gap), 시각 프롬프트/픽셀, 구조적 Baseline 등 수신자가 인지할 수 있는 어떠한 변경이라도 시스템에 수용되는 즉시 기존 Release Authorization은 원자적으로 취소된다. 수정된 내용을 과거 승인으로 발행하는 우회로는 존재하지 않는다.

릴리즈는 정확히 5개 컷 모두가 Current이고 승인된 Review Artifact와 일치할 때만 허용된다. 1개 컷이라도 STALE이거나, 컷 자산 중 하나라도 읽을 수 없거나, 조판/패키징 오류가 발생하면 4컷 부분 릴리즈를 생성하지 않고 전체 릴리즈가 실패한다. PNG Export는 승인된 artifact를 소스로 사용하여 텍스트 재줄바꿈, 폰트 재계산, 말풍선 이동, 컷 재배치 없이 composition identity를 보존하며 출력 바이트를 생성한다. Blogger 전달 역시 승인된 artifact를 소스로 사용하며, 로컬 DB에 전달 시도를 기록한 뒤 외부 서비스의 권위 있는 응답을 통해 고유 게시물 ID와 실제 접근 가능한 목적지 URL을 확인(Readback)했을 때만 `confirmed_success`로 전이한다. 통신 장애, 타임아웃, 응답 누락 발생 시에는 로컬 요청 성공만으로 발행 성공을 날조하지 않고 `unknown`/`unresolved` 상태를 유지하며 UI에 '발행 결과 미확인'을 정직하게 고지한다.

본 Scope의 완료 판정은 BLOCK-05의 실측 Exit Predicate 및 4대 Counterexample Gate 통과에 한정되며, 전체 전환의 최종 완성(Transformation Outcome Complete) 선언은 본 Scope 완료 후 Main 에이전트가 BASELINE-001의 Completion Predicate 전항목과 Final Authoritative Readback을 검증하여 수행한다.

포함:
- 검토 화면에 표시된 exact `artifact_id` 및 content SHA-256 hash에 결속되는 영속 Release Authorization 생성 및 서버 재시작 보존
- 수신자 인지 가능 mutation(말풍선 텍스트, 좌표, 스타일, Gap, 컷 intent/realization, Baseline) 수용 즉시 기존 활성 승인의 원자적 자동 취소(Revocation)
- 5컷 전원 Current 검증 및 결측/합성 실패 시 릴리즈 전체를 차단하는 All-or-Nothing 게이트
- 승인된 Review Artifact의 composition identity를 재조판 없이 보존하는 PNG Export 기능(CLI 및 API)
- 승인된 Review Artifact 기반 Blogger 전달 어댑터 및 시도/결과 상태 머신
- 외부 목적지(Blogger)의 고유 게시물 식별자 및 실제 접근 가능한 URL을 검증하는 Destination Readback
- 네트워크 단절, 타임아웃, 응답 누락 주입 시 발행 완료로 위장하지 않고 정직하게 `unknown`을 유지하는 오류 처리
- Studio UI 및 CLI에서 승인 상태, 전달 시도, 확정 성공, 확정 실패, 미확인(Unknown) 상태를 독립 차원으로 정직하게 노출
- 4대 Counterexample Gate(Gate 1 Currency, Gate 2 Identity, Gate 3 Interruption, Gate 4 External Truth)의 종단 실측 차단 검증

제외:
- Blogger 이외의 추가 외부 배포처(Twitter, Instagram, Webtoon 등 후보 항목)
- 상세 generation/delivery audit log 전용 뷰어
- 멀티유저 협업, 원격/클라우드 데이터베이스, 분산 큐, SSR
- 임의 N-cut 지원(제품 경계 밖)
- 하류 단계에서의 독자적 레이아웃 보정이나 WYSIWYG 위반 재조판
- 본 Scope 수준에서의 전체 프로젝트 Transformation Outcome 최종 완료 선언(Main 호출자 소유)

## Acceptance

아래 시나리오는 실제 disposable project SQLite, 실제 `comic-new serve` 프로세스, 실제 브라우저/HTTP API 호출, 실제 CLI 명령어, 그리고 외부 통신을 격리 검증할 수 있는 통제된 네트워크/응답 시험 환경을 사용하여 실측한다. stubbed store, in-memory mock 플래그, 단순 소스 검사, 또는 성공 가정만으로는 어떤 시나리오도 충족할 수 없다.

### A. 릴리즈 승인 결속 및 재시작 영속성 (Baseline Exit 1-4)

1. 정확히 5컷이 Current인 프로젝트에서 실체화된 Canonical Review Artifact를 브라우저 ReviewModal로 열고 승인을 요청하면, 요청 페이로드의 `artifact_id`와 full content hash가 모달에 표시된 바이트 해시와 정확히 일치한다.
2. 서버는 해당 artifact identity에 영속 결속된 `release_authorizations` 레코드를 생성하며, snapshot 및 SQLite 직접 조회 시 활성 승인(active authorization)으로 재조회된다.
3. 활성 승인이 존재하는 상태에서 `comic-new serve` 서버 프로세스를 완전히 종료했다가 다시 시작한 후 fresh snapshot 및 별도 SQLite readback을 수행하면, 활성 승인 레코드가 그대로 보존되어 있고 UI에도 승인됨 상태가 유지된다.
4. 활성 승인이 생성된 직후 snapshot과 SQLite를 조회했을 때 delivery attempts는 비어 있으며, 승인 행위 자체가 `published`나 전달 성공으로 자동 승격되지 않는다.

### B. 수신자 인지 가능 변경에 따른 즉시 승인 취소 (Baseline Exit 5-9, Gate 2)

1. 활성 릴리즈 승인이 존재하는 상태에서, Inspector를 통해 임의의 한 컷 말풍선 텍스트에 1글자를 추가/변경하고 저장한다. 변경이 authoritative state로 수용되는 단일 트랜잭션 안에서 기존 활성 승인은 즉시 revoked 처리된다.
2. snapshot 및 별도 SQLite readback 시 active authorization은 `None`이 되고, history에 해당 승인이 취소 권위 revision과 함께 남으며, UI의 승인 상태는 즉시 '미승인'으로 갱신된다.
3. 말풍선 기하 좌표(x, y, w, h), 컷 간 간격(`gap_px`), 스타일, 컷 대사/프롬프트 intent, Structural Baseline 변경, 새로운 realization commit 어느 것이 수용되더라도 활성 승인은 즉각 취소된다.
4. 브라우저의 저장되지 않은 로컬 draft 편집은 서버의 활성 승인을 취소하지 않지만, 미저장 draft가 존재하는 상태에서는 릴리즈 요청이 거부된다.
5. 승인이 취소된 후 이전 artifact identity로 릴리즈(PNG 내보내기 또는 Blogger 발행)를 시도하면 거절 에러가 발생하며, 수정된 조판에 대한 릴리즈는 반드시 새 review artifact 실체화와 새 2차 승인을 거쳐야만 가능하다.

### C. All-or-Nothing 릴리즈 무결성 (Baseline Exit 10-14, Gate 1)

1. 5개 컷 중 1개 컷이라도 `desired_revision != realized_revision`인 STALE 상태인 경우, 릴리즈 요청(PNG/Blogger)은 즉시 거절되며 릴리즈 시도가 시작되지 않는다.
2. 5개 컷 중 1개 컷의 canonical 이미지 자산 파일을 강제로 삭제하거나 읽을 수 없게 손상시킨 뒤 릴리즈를 요청하면, 4컷짜리 불완전한 부분 PNG나 Blogger 페이로드가 절대 생성되지 않고 전체 릴리즈가 명시적 실패로 종료된다.
3. 조판 합성기 또는 아티팩트 패키징 단계에서 예외가 발생하면 전체 릴리즈 트랜잭션이 실패하며, 결측을 무시하고 계속 진행(silent continue/omission)하는 경로가 존재하지 않는다.
4. 정확히 5개의 유효한 Current realization이 승인된 아티팩트의 cut closure와 100% 일치할 때만 릴리즈 진입이 허용된다.

### D. 정본 조판 보존 PNG Export (Baseline Exit 15-18)

1. 활성 승인이 존재하는 상태에서 PNG Export를 실행하면, 승인된 Canonical Review Artifact를 소스로 사용하여 완성된 단일 PNG 파일이 생성된다.
2. Export 과정에서 텍스트 재줄바꿈(reflow), 폰트 재계산, 말풍선 재배치, 컷 재정렬이 발생하지 않으며, 승인된 artifact의 픽셀 조판 정본이 그대로 보존된다.
3. 생성된 PNG 파일의 바이트 해시 및 이미지 규격이 승인된 Review Artifact와 일치함을 검증한다.
4. 활성 승인이 없거나 승인이 취소된 상태에서 PNG Export를 호출하면 명시적 승인 필요 오류와 함께 파일 생성이 차단된다.

### E. Blogger 전달 및 목적지 Readback (Baseline Exit 19-23)

1. Blogger 발행 요청 시 승인된 Canonical Review Artifact가 전달 페이로드 소스로 사용되며, 임의의 브라우저 DOM 캡처나 별도 재조판 렌더링을 거치지 않는다.
2. 발행 요청 시작 시 로컬 SQLite에 `kind='blogger'`, 참조된 `authorization_id`, 초기 상태 `unknown`을 가진 `delivery_attempts` 레코드가 원자적으로 기록된다.
3. 외부 Blogger 서비스가 정상 응답을 반환하고 게시 성공을 증명하면, 권위 있는 응답으로부터 추출한 고유 게시물 ID(post ID)와 접근 가능한 목적지 URL이 로컬 DB에 기록되며 상태는 `confirmed_success`로 전이된다.
4. snapshot 및 별도 SQLite readback에서 기록된 post ID와 destination URL을 읽어낼 수 있으며, UI에도 해당 링크와 함께 확정 성공 상태가 표시된다.
5. 로컬 릴리즈 승인 여부와 외부 전달 성공 여부는 서로 다른 필드로 엄격히 분리되며, 하나의 단순 불리언 `published=true`로 합쳐지지 않는다.

### F. 응답 불명확 시 정직한 Unknown 유지 (Baseline Exit 24-29, Gate 4)

1. Blogger 발행 요청 후 외부 응답 수신 단계에서 네트워크 단절, 연결 타임아웃, 또는 불완전 응답을 강제 주입한다.
2. 전달 시도 결과는 절대 `confirmed_success`로 승격되지 않고 `unknown` 상태로 유지된다.
3. Studio UI와 snapshot readback은 이를 '발행 완료'나 '성공'으로 속이지 않고 '발행 결과 미확인(Unknown)'으로 정직하게 고지한다.
4. 로컬에서 HTTP 요청을 전송했다는 사실만으로 성공을 창조하지 않으며, 목적지 Readback을 통해 실제 원격 게시물이 확인된 경우에만 Confirmed Success로 전이한다.
5. 외부 서비스가 명백한 오류(인증 실패, 규격 거부 등)를 확정 반환한 경우에는 `confirmed_failure`와 오류 증거를 정직하게 기록한다.

### G. 4대 Counterexample Gate 종단 실측 차단 (Baseline Exit 30-33)

1. Gate 1 (Currency Gate): 디스크에 온전한 이전 5컷 PNG가 모두 존재하더라도, 1개 컷의 최신 intent가 미실현(STALE)이면 릴리즈 권한이 차단되고 작품은 완료 상태로 진입할 수 없다.
2. Gate 2 (Identity Gate): 2차 릴리즈 승인을 획득한 후 말풍선 텍스트 1글자 또는 Gap 1px을 수정한 경우, 이전 승인을 재사용하여 릴리즈를 수행하는 것이 차단된다.
3. Gate 3 (Interruption Gate): 생성 도중 STOP을 누르거나 서버를 재시작해도 이미 수용된 최신 intent는 영속 보존되고 실행만 INTERRUPTED로 정리되며, 미완성 컷은 STALE로 표시된다.
4. Gate 4 (External Truth Gate): Blogger 응답이 타임아웃되거나 유실되었을 때, 로컬 데이터만으로 "발행 성공"을 표시할 수 없으며 목적지 Readback 전까지 Unknown 상태를 유지한다.

## External Conditions

검증 환경에는 FastAPI를 포함한 Python 3.11+ 런타임, SQLite 3, Pillow 및 유효한 조판용 폰트, 실제 Chromium 계열 브라우저가 갖추어져 있어야 한다. Blogger 전달 검증은 자동화 검증 시 불필요한 외부 자격 증명 유출이나 예측 불가능한 외부 부작용을 방지하기 위해 확정 성공(post ID 및 URL 반환), 타임아웃/네트워크 절단(Unknown 유발), 그리고 확정 실패(오류 반환)를 결정론적으로 주입하고 검증할 수 있는 통제된 테스트 하네스 또는 모의 서비스 어댑터를 지원해야 한다. 실환경 자격 증명이 제공되는 경우 실제 Blogger API에 대한 종단 Readback 검증을 수행할 수 있어야 한다.

## Open Decisions

None
