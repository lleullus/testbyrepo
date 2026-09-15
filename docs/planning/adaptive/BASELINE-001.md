# Transition Baseline BASELINE-001 — Web Comic Studio Clean Rebuild

Status: APPROVED
Baseline-ID: BASELINE-001
Revision: 1
Project-Root: /home/user01/project/comic_new
Meaning-Slug: web-comic-studio
Applicability: Clean rebuild of Web Comic Studio adhering to THESIS-001 and FRONTEND-ARCH-001
Authored-On: 2026-09-15
Language: ko

---

## 1. Identity & Approval

### 1.1 Baseline Identity

* **Baseline-ID:** `BASELINE-001`
* **Status:** `APPROVED`
* **Project-Root:** `/home/user01/project/comic_new`
* **Meaning-Slug:** `web-comic-studio`
* **Applicability:** Clean rebuild of Web Comic Studio adhering to `THESIS-001` and `FRONTEND-ARCH-001`
* **Request Reference:** `comic-new-baseline-session-20260915-0711`

### 1.2 Source Authority

본 Transition Baseline의 규범 권위는 다음 순서로 고정한다.

1. **현재 사용자 지시**
2. **Product Thesis**

   * `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-001.md`
   * SHA-256: `74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63`
3. **Frontend Architecture**

   * `/home/user01/project/comic_new/docs/planning/frontend-architecture/FRONTEND-ARCH-001.md`
   * SHA-256: `8eea9545d82b40e64791cd0d6b3340e848b72923d36373bae6425cc39badac9b`
4. **과거 참고 증거**

   * `/home/user01/project/comic/docs/planning/adaptive/BASELINE-001.md`
   * 형식, 실패 교훈, Transition Baseline 운용 원칙을 참고할 수 있으나 `comic_new`의 제품 의미나 구현 호환성 권위를 갖지 않는다.

`THESIS-001`은 제품 의미, 사용자 효용, 5-Truth Chain 및 인과적 불변식의 최상위 제품 권위이다. `FRONTEND-ARCH-001`은 그 제품 의미를 변경하지 않는 범위에서 프론트엔드 구현 아키텍처의 승인된 파생 권위이다.

문서 사이에 구현 세부 충돌이 존재할 경우 제품 의미와 인과적 진실은 `THESIS-001`을 우선하며, 하위 구현은 그 의미를 만족하는 방향으로 해석한다.

### 1.3 Approval

* **Approved by:** User
* **Approval reference:** `comic-new-baseline-session-20260915-0711`
* **Approval scope:** 본 문서의 Transformation Outcome, Global/Path Invariants, Counterexample Gates, BLOCK-01 ~ BLOCK-05
* **Inter-Block auto-continuation:** 각 선행 Block의 Exit Predicate와 Safe Continuation Predicate가 실측된 경우에 한해 허용
* **Unmeasured continuation:** 금지

### 1.4 Baseline Role

본 문서는 `comic_new`를 완결 상태로 이동시키는 **Transition Authority Map**이다.

본 문서는 다음 역할을 하지 않는다.

* 런타임 상태 저장소
* 작업 큐
* 재시도 장부
* 구현 진행률 로그
* Git 상태 기록
* 개별 Ticket 목록
* 구현 세부의 무제한 사전 승인
* Thesis를 대체하는 새로운 제품 의미 문서

각 Transition Block은 거친 원자적 마일스톤과 실측 가능한 Exit Predicate만 정의한다. 후속 Work Package, Increment, Ticket 또는 구현 작업은 필요한 시점에 본 Baseline의 해당 Block Envelope 안에서 파생되어야 한다.

---

## 2. Transformation Outcome

### 2.1 Goal

`comic_new`의 목표는 과거 `comic`에서 발생한 다음 **5대 진실 분열**을 구조적으로 제거하는 것이다.

1. **Intent Truth 분열**

   * storyboard, lettering, synopsis 등의 복제 상태가 현재 창작 의도를 서로 다르게 주장하는 문제
2. **Realization Truth 분열**

   * 전체 생성과 개별 재생성이 별도 권위를 가지며 늦게 끝난 구 작업이 최신 픽셀을 덮어쓰는 Stale Overwrite
3. **Canonical Visual Truth 분열**

   * 편집 화면, PNG 내보내기, Blogger 발행이 서로 다른 렌더러와 레이아웃 규칙을 사용하여 WYSIWYG가 파괴되는 문제
4. **Approval Truth 분열**

   * 승인 상태가 휘발성 메모리와 다른 생명주기 상태에 섞여 실제 승인 대상을 증명하지 못하는 문제
5. **Delivery Truth 분열**

   * 일부 컷 누락이나 외부 응답 불명확에도 성공을 추정하거나 조용히 부분 결과를 전달하는 문제

최종 Transformation Outcome은 다음과 같다.

> **창작자의 최신 승인 의도를 단 하나의 영속적 인과 사슬을 통해 정확히 5개의 현재 정본 컷으로 실현하고, 창작자가 실제로 확인하여 승인한 단일 조판 정본을 재해석 없이 PNG 또는 Blogger로 전달하며, 외부 전달의 성공 여부를 목적지 Readback으로 확인할 수 있는 단일 프로덕션 Web Comic Studio를 구축한다.**

### 2.2 Target 5-Truth Chain

```text
Source Brief
    ↓
Approved Structural Baseline
    ↓
Five Effective Cut Intents
    ↓
Five Current Realizations
    ↓
Draft Composition / Interactive Projection
    ↓
Canonical Review Artifact
    ↓
Release Authorization
    ↓
External Delivery
    ↓
Destination Readback
```

전이 과정에서 어느 Block도 이 Chain의 중간 단계를 생략하거나 하류 성공으로 상류 진실을 대체할 수 없다.

> **No downstream success may repair or substitute for a broken upstream truth.**

---

## 3. Required Named Items

### 3.1 단일 트랜잭션 저장소 및 5컷 고정 스키마

반드시 다음 특성을 갖는다.

* SQLite 기반 **Single Durable Transactional Authority**
* 제품이 소유하는 authoritative mutable state는 SQLite 트랜잭션을 통해서만 변경
* 정확히 `cut_id = 1..5`의 안정된 ordered cut identity
* 컷 추가, 삭제, 재색인 없음
* 각 컷에 `desired_revision`과 `realized_revision`을 구분
* intent revision은 엄격한 단조 증가
* composition identity/revision 영속화
* Structural Baseline 및 1차 승인 영속화
* 작업 및 실행 사실 영속화
* Canonical Review Artifact identity 영속화
* Release Authorization 영속화
* Delivery attempt/outcome 영속화
* 프로세스 메모리나 JSON 복제 파일이 경쟁 authority가 되는 구조 금지
* 애플리케이션이 생성·관리하는 `.lock` 파일 및 별도 파일 락: **0개**
* 동시성 및 원자성은 DB transaction/constraint/compare-and-swap 성격의 commit condition으로 해결

SQLite 자체가 내부적으로 사용하는 파일 시스템 수준의 동시성 기법은 별도 애플리케이션 lock authority로 간주하지 않는다. 금지 대상은 제품이 별도로 관리하여 진실을 분산시키는 lock file/lock registry이다.

### 3.2 단일 통합 생성 엔진 및 워커 풀

전체 생성과 개별 컷 재생성을 별도 실행 체계로 나누지 않는다.

반드시 다음을 만족한다.

* 전체 생성과 개별 생성 모두 **동일한 하나의 durable queue**
* 동일한 generation job model
* ima2 호출을 수행하는 제한된 worker pool
* 각 job은 대상 `cut_id`와 수용 당시의 `desired_revision`을 소유
* canonical realization commit 직전 현재 authoritative `desired_revision`을 재검증
* superseded/cancelled/interrupted/old-revision job은 연산 성공 여부와 무관하게 canonical commit 금지
* stale result는 폐기하거나 비정본 실행 기록으로만 보존
* `STOP`은 물리적 생성 subprocess/process tree를 즉시 종료 대상으로 삼음
* STOP은 accepted desired intent를 철회하지 않음
* 종료 후에도 revision mismatch가 있으면 기존 픽셀은 `STALE`

### 3.3 조판 정본 엔진

반드시 다음을 만족한다.

* Canonical Composition Surface 하나
* 말풍선 geometry는 `x_pct`, `y_pct`, `w_pct`, `h_pct` 정규화 백분율 좌표
* 좌표의 기준은 browser viewport나 개별 source image가 아니라 canonical composition surface
* 5개 cut geometry, gap, text, typography를 하나의 composition model로 해석
* 서버 측 **단일 PIL 기반 canonical renderer**
* 브라우저 projection, PNG export, Blogger path에 서로 독립적인 조판 알고리즘 금지
* 최종 검토 대상은 브라우저 DOM 재구성이 아니라 실제 렌더링된 immutable `Canonical Review Artifact`
* artifact는 안정된 `artifact_id`와 content hash를 가짐
* 승인 후 export/publish는 해당 artifact identity를 참조
* downstream에서 text reflow, font recalculation, bubble relocation, crop, cut reorder 금지
* destination 규격에 필요한 composition-preserving encoding 또는 전체 균등 축소만 허용

### 3.4 웹 스튜디오 프론트엔드

승인된 프론트엔드 경계는 다음과 같다.

* Vue 3 Composition API
* TypeScript `strict`
* Vite
* Pinia
* domain store는 정확히 하나: `useStudioStore`
* native `fetch`
* native `EventSource`
* DOM/SVG + native `PointerEvent`
* FastAPI 단일 프로덕션 서빙

`useStudioStore`는 최소한 다음 3개 진실 계층을 분리한다.

1. **server**

   * 마지막 authoritative server readback
2. **drafts**

   * 아직 서버에 수용되지 않은 브라우저 로컬 편집
3. **saves**

   * pending / failed / conflict 등 저장 시도 상태

로컬 draft는 authority가 아니다.

필수 UI 표면:

* `StudioHeader`
* `CutRail`
* `CompositionCanvas`
* `InspectorPanel`
* `QueuePopover`
* `ReviewModal` / canonical review dialog
* persistent STALE 표시
* persistent unsaved/save-failure 표시
* 3열 desktop layout
* narrow viewport에서 center permanent + non-modal edge panels

프로덕션 배포는 다음을 따른다.

* Vite build 결과 → `src/comic_new/static/`
* `comic-new serve` → 유일한 프로덕션 서버 프로세스
* 별도 Node/Bun daemon, SSR server, 별도 frontend production server 없음
* 정적 빌드가 누락된 상태에서 empty shell을 성공적으로 제공하는 행위 금지

### 3.5 공개 승인 결속 및 목적지 Readback

반드시 다음을 만족한다.

* Release Authorization은 **특정 Canonical Review Artifact identity**에 결속
* receiver-visible authoritative change가 수용되는 즉시 기존 authorization 폐기
* 로컬 unsaved draft만으로는 서버 authorization을 임의 폐기하거나 승계하지 않음
* 정확히 5개 컷이 모두 Current가 아니면 release 금지
* 부분 PNG, 부분 Blogger release 경로 없음
* PNG export는 승인된 artifact에서 생성
* Blogger 발행도 승인된 artifact에서 생성
* Blogger 성공은 local request 완료가 아니라 destination evidence를 통해 확인
* timeout/응답 불명확은 `Unknown` 또는 `Unresolved`
* 성공, 실패, 미확인을 서로 다른 상태로 유지

---

## 4. Candidate Named Items

다음 항목은 Transformation Outcome 달성에 필요하지 않으며 본 Baseline에 의해 사전 승인된 구현 의무가 아니다.

* Blogger 이외의 추가 외부 delivery adapter
* 상세 generation/history audit viewer
* 별도 desktop packaging
* multi-user collaboration
* remote/cloud database
* cloud queue
* SSR
* WebSocket
* general-purpose canvas/DnD framework
* arbitrary N-cut 지원

특히 **arbitrary N-cut 지원은 단순 Candidate가 아니라 현재 Product Boundary 밖**이다. 이를 도입하려면 새로운 제품 의미 결정이 필요하다.

Candidate 항목은 BLOCK-01 ~ BLOCK-05의 Exit를 앞당기거나 대체하는 근거로 사용할 수 없으며, 첫 번째 실제 실패 증거가 요구하지 않는 추상화나 dependency를 선제적으로 추가하지 않는다.

---

## 5. Completion Predicate

본 Transition Baseline은 다음 조건이 **모두 실측**되었을 때만 완료된다.

1. 정확히 5개의 stable cut identity와 모든 authoritative state가 단일 SQLite transactional authority에서 재조회된다.
2. 각 컷의 accepted intent revision이 단조 증가하며 이전 revision의 지연 결과가 최신 realization을 덮어쓸 수 없음을 경쟁 실행으로 증명한다.
3. 정확히 5컷 모두에 대해:

```text
desired_revision == realized_revision
```

이 성립해야만 Realization Complete가 된다.

4. revision mismatch가 있는 기존 이미지가 존재해도 해당 컷은 `STALE`이며 작품은 Complete가 아님을 UI와 서버 readback에서 확인한다.
5. STOP 또는 프로세스 중단 후 accepted desired intent가 보존되고 실행만 `INTERRUPTED` 등 정직한 terminal truth로 정리됨을 확인한다.
6. 저장 실패/409/500 시 브라우저 draft가 authoritative state로 위장되지 않으며 지속적인 unsaved/error 표시가 남는다.
7. 정확히 5개의 Current realization으로부터 하나의 immutable Canonical Review Artifact가 생성된다.
8. Review UI가 브라우저에서 조판을 재구성하지 않고 바로 그 artifact bytes를 표시한다.
9. 2차 승인은 표시 중인 정확한 artifact identity/hash에 결속된다.
10. 승인 후 receiver-visible authoritative 변경을 수용하면 기존 승인이 즉시 무효화된다.
11. 승인되지 않은 artifact나 5컷 미완성 상태에서는 PNG/Blogger release가 불가능하다.
12. PNG와 Blogger delivery가 승인된 artifact composition을 재조판 없이 보존한다.
13. 컷 누락이나 compositor 실패 시 부분 전달하지 않고 전체 release가 실패한다.
14. Blogger timeout 또는 응답 불명확을 성공으로 표시하지 않는다.
15. 실제 destination readback을 통해 Blogger의 권위 있는 게시물 식별자와 접근 가능한 목적지 정보를 확인할 수 있다.
16. 프로덕션 UI가 `comic-new serve` 단일 Python 프로세스로 제공된다.
17. 아래 4대 Counterexample Gate가 모두 실측 차단된다.

Block 자체의 완료는 전체 Product Completion을 의미하지 않는다. `BLOCK-05` 종료 후에도 본 Completion Predicate와 Final Authoritative Readback을 통과해야 최종 완료를 선언할 수 있다.

---

## 6. Final Authoritative Readback

| Causal Boundary              | Authoritative Readback                                                            |
| ---------------------------- | --------------------------------------------------------------------------------- |
| Structural Baseline accepted | SQLite에서 정확히 5개의 stable ordered cut identity와 승인된 Structural Baseline을 재조회        |
| Intent accepted              | 해당 cut의 증가된 `desired_revision`을 새 DB read transaction으로 재조회                       |
| Cut realized                 | canonical asset가 현재 `desired_revision`에 귀속되고 무결한 이미지 bytes로 확인                    |
| Realization complete         | 정확히 5개 cut 모두 `desired_revision == realized_revision`                             |
| Composition accepted         | authoritative composition revision과 정규화 geometry/text/style/gap 상태 재조회            |
| Review canonicalized         | immutable `artifact_id`, hash, composition revision 및 5개 realization revision이 일치 |
| Release authorized           | authorization record가 표시·승인된 정확한 artifact identity/hash에 결속                       |
| Release payload valid        | payload가 authorized artifact에서만 생성되고 정확히 5컷 composition을 보존                       |
| PNG delivered                | 승인 artifact에서 생성된 완전한 PNG bytes가 정상 검증됨                                           |
| Blogger attempted            | local DB에는 시도 사실과 request identity만 정직하게 기록                                       |
| Blogger confirmed            | destination readback에서 권위 있는 외부 게시물 식별자와 실제 목적지 확인                                |
| Ambiguous delivery           | local state가 `Unknown/Unresolved`를 유지하며 성공/실패를 창조하지 않음                            |

---

## 7. Global Invariants

다음 8개 불변식은 `THESIS-001`의 load-bearing invariants이며, BLOCK-01부터 최종 완료까지 약화·대체·일시 정지할 수 없다.

### INV-1 — Single Effective Intent & Structural Baseline

* 정확히 5개의 stable ordered cut identities `1..5`를 유지한다.
* 1차 승인으로 5컷 서사 구조를 `Structural Baseline`으로 동결한다.
* 각 컷에는 현재 authority가 되는 `Effective Current Intent`가 하나만 존재한다.
* 국소적인 대사/시각 prompt 수정은 해당 컷의 새 revision이다.
* 구조적 역할/순서/상호의존성을 바꾸는 수정은 명시적 Re-baseline과 새 1차 승인을 요구한다.
* 과거 revision, 브라우저 projection, 캐시 또는 복제 파일은 현재 intent와 경쟁하지 않는다.

### INV-2 — Monotonic Intent Realization

* accepted `desired_revision`은 엄격히 증가한다.
* rollback도 revision 감소가 아니라 과거 내용을 payload로 한 새로운 상위 revision이다.
* canonical realization은 현재 desired revision에 귀속된 결과만 commit할 수 있다.
* stale, superseded, cancelled, interrupted job은 계산 성공 여부와 무관하게 canonical commit 권한이 없다.
* Stale Overwrite는 구조적으로 불가능해야 한다.

### INV-3 — Truthful Currency & Completion

* asset presence는 Current의 증거가 아니다.
* job completion은 Current의 증거가 아니다.
* 다음 equality만이 cut currency를 판정한다.

```text
cut_current = desired_revision == realized_revision
```

* 정확히 5컷 모두 Current일 때만 Realization Complete이다.
* execution / currency / authorization / delivery는 별도 truth dimension이다.

### INV-4 — Canonical Review Artifact

* 편집 캔버스는 `Interactive Projection`이다.
* 승인 대상은 materialized immutable `Canonical Review Artifact`이다.
* release path는 승인된 artifact를 다시 조판해서는 안 된다.
* 허용되는 downstream transformation4
[…319ln elided…]
료
* SQLite authority 재시작 readback 검증 완료

### Required Construction Boundary

반드시 다음 하나의 generation model을 사용한다.

```text
Accepted Cut Intent
    ↓
Unified Durable Queue
    ↓
ima2 Worker Pool
    ↓
Generated Candidate Result
    ↓
Commit-Time Intent Version Gate
    ↓
Canonical Realization or Discard
```

전체 5컷 생성도 5개의 동일 유형 job을 enqueue하는 상위 명령일 뿐 별도 commit engine이 아니다.

### Exit — Measured Predicate

다음을 모두 실측한다.

1. 전체 생성과 개별 cut 생성이 동일 queue/job schema를 사용한다.
2. ima2 worker pool에서 둘 이상의 cut 작업이 제한된 동시성으로 수행된다.
3. 각 job은 target cut와 target desired revision을 명시적으로 소유한다.
4. job A가 rev 2에서 시작된 뒤 동일 cut에 rev 3 job B가 수용되고 B가 먼저 완료되는 경쟁 시나리오를 만든다.
5. B의 rev 3 결과가 canonical realization으로 commit된다.
6. 뒤늦게 성공한 A의 rev 2 결과는 canonical realization을 변경하지 못한다.
7. superseded/cancelled job의 late result 역시 canonical commit되지 않는다.
8. generation failure가 과거 realization을 삭제하지 않는다.
9. 최신 desired revision이 미실현이면 이전 realization은 STALE로 판정된다.
10. Header/global STOP에 해당하는 backend operation이 실행 중 generation subprocess/process tree의 종료를 즉시 요청한다.
11. STOP 후 accepted desired revision이 그대로 남는다.
12. STOP 후 job terminal truth가 authoritative readback으로 `interrupted` 또는 적절한 종료 상태가 된다.
13. 서버 강제 종료 후 재시작 시 이전 프로세스를 계속 Running으로 가장하지 않는다.
14. restart recovery가 accepted intent를 철회하지 않는다.
15. queue가 drain되었다는 사실만으로 realization Complete를 선언하지 않는다.
16. exactly 5 revision equality로만 Complete를 선언한다.

### Invariants

* INV-1
* INV-2
* INV-3
* INV-7
* INV-8
* PATH-3
* PATH-4
* PATH-5
* PATH-9
* PATH-10

### Continuation

Exit Predicate가 모두 성립하면 `BLOCK-03`으로 진행한다.

Canonical compositor는 `BLOCK-02`가 확립한 **Current realization만** 정본 입력으로 받아야 한다.

### Abort

다음 경우 즉시 전이를 중단한다.

* 전체 생성과 cut 재생성이 서로 다른 commit 경로를 가짐
* late old job이 canonical asset을 덮을 수 있음
* STOP이 accepted intent를 제거함
* STOP이 단순 UI flag에 그치고 실제 generation process가 계속됨
* restart 후 orphan job이 가짜 Running으로 남음
* queue 완료 여부가 cut currency와 결합됨

### Insufficient for Exit

다음은 Exit에 불충분하다.

* worker가 병렬 실행되기만 함
* 정상 순서 완료만 시험함
* stale race를 mock으로만 검증함
* STOP 버튼 API가 200을 반환함
* process 종료 증거 없이 `stopRequested=true`만 기록됨
* old job 결과를 “대부분” 무시함
* 5개의 파일이 결과 디렉터리에 존재함

---

## BLOCK-03 — Canonical Composition & Review Artifact Stitcher

* **ID:** `BLOCK-03`
* **Name:** Canonical Composition & Review Artifact Stitcher

### Meaning Contribution

5개의 Current realization과 authoritative lettering/composition을 사용하여, 사용자가 실제로 보고 승인할 수 있는 단 하나의 canonical visual truth를 생성한다.

이 Block에서 WYSIWYG의 최종 authority가 브라우저 projection에서 immutable materialized artifact로 이동한다.

### Order / Dependencies

* `BLOCK-01` 완료
* `BLOCK-02` 완료

### Entry

* exactly five current-realization model 존재
* stale realization이 canonical input으로 오인되지 않음
* generation stale commit gate 검증 완료

### Required Construction Boundary

Canonical compositor는 다음 입력을 하나의 schema로 해석한다.

* exactly 5 canonical cut assets
* fixed cut order
* normalized bubble geometry
* bubble text
* typography/style
* cut gap
* composition revision

geometry는 canonical composition surface 기준으로 다음 형태를 사용한다.

```text
x_pct
y_pct
w_pct
h_pct
```

서버의 PIL renderer가 canonical pixel artifact를 실체화한다.

### Exit — Measured Predicate

다음을 모두 실측한다.

1. normalized percentage geometry가 viewport 크기와 무관하게 동일 canonical 위치를 표현한다.
2. canonical compositor가 정확히 5개 cut asset을 요구한다.
3. cut 하나를 읽거나 decode/render하지 못하면 전체 materialization이 실패한다.
4. silent skip/continue로 4컷 artifact를 생성할 수 없다.
5. 5개 Current 조건이 만족되지 않으면 review artifact materialization이 거절된다.
6. authoritative composition으로 immutable artifact가 생성된다.
7. artifact에 최소 다음 identity가 결속된다.

   * `artifact_id`
   * content hash
   * composition revision
   * five desired/realized revision identities
8. 동일 artifact bytes를 다시 읽었을 때 hash가 일치한다.
9. artifact 생성 후 현재 editor state가 바뀌더라도 기존 artifact bytes 자체는 변하지 않는다.
10. browser가 최종 승인 이미지를 DOM text/bubble reconstruction으로 다시 만들 필요가 없다.
11. text wrap/typography의 final truth를 PIL canonical renderer가 소유한다.
12. PNG/Blogger downstream이 독립적으로 text reflow 또는 bubble layout을 다시 수행하지 않아도 되는 artifact boundary가 확립된다.
13. 동일 accepted composition에서 review path와 export source가 동일 canonical artifact identity를 사용할 수 있다.

### Invariants

* INV-3
* INV-4
* INV-5
* INV-6
* INV-8
* PATH-5
* PATH-7
* PATH-11
* PATH-13

### Continuation

Exit Predicate가 모두 성립하면 `BLOCK-04`로 진행한다.

Frontend는 compositor를 복제하지 않고 interactive projection과 immutable review artifact를 구분해 표시해야 한다.

### Abort

다음 경우 중단한다.

* browser와 server가 서로 다른 final layout truth를 소유함
* PNG export용 별도 lettering compositor가 생김
* Blogger용 별도 line wrapping이 생김
* artifact identity 없이 “현재 composition”을 승인 대상으로 사용함
* 일부 cut render failure를 무시함
* materialized artifact가 생성 후 mutable하게 덮어써짐

### Insufficient for Exit

다음은 Exit가 아니다.

* 브라우저 canvas가 보기 좋게 보임
* PIL로 이미지 한 장을 만들 수 있음
* screenshot 비교만 통과함
* artifact hash/identity가 없음
* 4컷만 성공해도 preview를 보여줌
* export 시 다시 조판할 예정임
* exact Current 검증 없이 artifact 생성 가능

---

## BLOCK-04 — Studio Shell & Vue 3 Frontend

* **ID:** `BLOCK-04`
* **Name:** Studio Shell & Vue 3 Frontend

### Meaning Contribution

창작자가 5-Truth Chain의 현재 상태를 왜곡 없이 관찰·수정·중단·검토할 수 있는 단일 Web Studio 사용자 표면을 완성한다.

Frontend의 역할은 새로운 truth를 창조하는 것이 아니라 authoritative state와 local unsaved projection의 차이를 정직하게 보여주는 것이다.

### Order / Dependencies

* `BLOCK-01` 완료
* `BLOCK-02` 완료
* `BLOCK-03` 완료

### Entry

* snapshot으로 읽을 authoritative server state 존재
* unified queue/STOP backend 존재
* canonical review artifact materialization 존재

### Required Construction Boundary

#### Stack

* Vue 3
* Composition API
* `<script setup>`
* TypeScript strict
* Vite
* Pinia
* native fetch
* native EventSource
* plain scoped CSS / CSS custom properties / Grid/Flex
* DOM/SVG + native PointerEvent
* one domain store: `useStudioStore`

#### Single-Serving Contract

```text
frontend/                  # source
    ↓ Vite build
src/comic_new/static/      # generated package data
    ↓
comic-new serve            # only production process
```

#### Store Truth Layers

```text
server  = last authoritative readback
drafts  = local unaccepted projection
saves   = persistence attempt status
```

gesture-only pointer state는 component local state로 유지한다.

#### Required Shell

* Header permanent
* Left 5-cut rail
* Center composition canvas
* Right non-modal inspector
* Queue popover
* STALE badges
* unsaved/conflict markers
* canonical ReviewModal

### Exit — Measured Predicate

다음을 모두 실측한다.

#### A. Single Serving

1. frontend build가 `src/comic_new/static/`에 생성된다.
2. `comic-new serve` 하나만 실행한 상태에서 `/`가 generated studio를 제공한다.
3. hashed JS/CSS assets를 FastAPI가 정상 제공한다.
4. `/api`가 같은 process boundary에서 제공된다.
5. 별도 Node/Bun production daemon 없이 동작한다.
6. `static/index.html` 누락 시 empty success shell 대신 명확히 startup failure가 발생한다.

#### B. Exactly-Five Truth UI

7. `CutRail`에 정확히 5개의 stable cut이 나타난다.
8. 각 cut의 desired/realized revision을 확인할 수 있다.
9. mismatch cut은 명백한 `STALE` 표시를 가진다.
10. 하나라도 STALE이면 전체 Complete UI를 표시하지 않는다.

#### C. One-Store / Draft Isolation

11. domain mutable store는 `useStudioStore` 하나이다.
12. local draft가 `server` snapshot을 직접 덮어쓰지 않는다.
13. save request는 base composition revision 또는 동등한 concurrency identity를 보낸다.
14. composition save는 동시에 여러 response가 draft를 역전시키지 않도록 직렬화된다.
15. save 500/network failure를 강제로 만들면 draft가 보존된다.
16. 사용자에게 save failure toast가 표시된다.
17. toast 종료 후에도 affected object/field에 persistent `저장 안 됨` 성격의 표시가 남는다.
18. 409 conflict에서도 local draft가 조용히 삭제되지 않는다.
19. dirty 상태에서 새로운 SSE snapshot이 와도 server layer만 갱신되고 draft는 보존된다.
20. unsaved/failed/conflict가 존재하면 review materialization UI가 비활성화된다.

#### D. SSE Truth Preservation

21. app은 native `EventSource`를 통해 authoritative events를 수신한다.
22. duplicate/older revision event가 새 server truth를 역전시키지 않는다.
23. job completed event 자체로 cut Current를 설정하지 않는다.
24. realization accepted authoritative payload에서만 realized revision을 갱신한다.
25. superseded result event가 이전 pixels를 보존하더라도 cut currency를 거짓으로 Current로 바꾸지 않는다.
26. event gap/reconnect 상황에서 authoritative studio snapshot을 다시 읽는다.
27. SSE 연결 장애가 job/interruption truth를 임의로 창조하지 않는다.

#### E. Immediate STOP UX

28. active/stoppable job이 있으면 Header에서 STOP에 접근할 수 있다.
29. STOP은 confirmation dialog 없이 즉시 요청된다.
30. local UI는 우선 `stopRequested`만 표현하며 authoritative terminal readback 전에 job을 임의 종료 처리하지 않는다.
31. terminal readback 후에도 desired intent는 보존된다.
32. revision mismatch가 남으면 해당 cut은 STALE이다.
33. QueuePopover에서 queued/running job과 대상 cut/revision을 확인할 수 있다.

#### F. Composition Interaction

34. geometry가 canonical surface percentage coordinates를 사용한다.
35. zoom/resize 후에도 저장된 geometry의 canonical 의미가 변하지 않는다.
36. native PointerEvent capture/cancel 경로가 존재한다.
37. `pointercancel` 시 transient gesture만 취소되고 authoritative save가 발생하지 않는다.
38. pointerup/commit 이후에도 server acceptance 전에는 saved로 위장하지 않는다.
39. keyboard interaction이 pointer interaction과 같은 normalized geometry model을 사용한다.

세부 nudge 수치 등 implementation-level 차이는 승인된 product meaning과 `FRONTEND-ARCH-001`의 최종 정합성을 깨지 않는 방향으로 후속 implementation proof에서 고정하며, 이 Baseline의 Exit를 별도 숫자 하나에 종속시키지 않는다.

#### G. Canonical Review

40. ReviewModal은 server-materialized immutable artifact bytes를 표시한다.
41. browser DOM/SVG가 approval artifact를 재조판하지 않는다.
42. 사용자가 보고 있는 정확한 artifact identity/hash가 승인 요청에 사용된다.
43. ordinary inspector와 queue UI는 non-modal이며 canvas editing을 불필요하게 차단하지 않는다.
44. consequential authority decision을 제외한 일상 편집에 focus-trap modal을 남용하지 않는다.

### Invariants

* INV-1 ~ INV-8 전부
* 모든 Path Invariants
* 특히 PATH-5, PATH-8, PATH-9, PATH-10, PATH-12

### Continuation

Exit Predicate가 모두 성립하면 `BLOCK-05`로 진행한다.

이 시점에도 UI에서 “승인 가능”하다는 사실은 외부 전달 성공을 의미하지 않는다.

### Abort

다음 경우 전이를 중단한다.

* multiple domain stores가 동일 truth를 독립적으로 소유
* draft가 authoritative snapshot을 덮어씀
* save 실패를 console에만 기록
* STALE cut을 Current로 렌더
* job complete를 cut complete로 간주
* STOP 클릭 즉시 backend readback 없이 Interrupted로 위장
* browser가 final artifact를 자체 재조판
* 별도 frontend production server가 필수
* inspector가 일반 편집을 focus-trap modal로 강제

### Insufficient for Exit

다음은 Exit가 아니다.

* Vue 화면이 렌더됨
* mock snapshot만 사용함
* desktop screenshot 한 장이 정상임
* save happy path만 동작함
* SSE happy path만 동작함
* toast가 있지만 persistent failure marker가 없음
* STALE badge가 디자인상 존재하지만 revision mismatch와 연결되지 않음
* ReviewModal이 current editor DOM을 캡처해 승인함
* Vite dev server를 함께 실행해야만 제품이 동작함

---

## BLOCK-05 — Release Authorization & Destination Readback

* **ID:** `BLOCK-05`
* **Name:** Release Authorization & Destination Readback

### Meaning Contribution

창작자가 눈으로 승인한 정확한 Canonical Review Artifact를 All-or-Nothing 방식으로 외부화하고, 로컬 권위와 외부 목적지 진실의 경계를 끝까지 보존하여 5-Truth Chain을 닫는다.

### Order / Dependencies

* `BLOCK-01` 완료
* `BLOCK-02` 완료
* `BLOCK-03` 완료
* `BLOCK-04` 완료

### Entry

* exactly five Current verification 가능
* immutable review artifact 존재
* frontend에서 정확한 artifact를 검토 가능
* authorization state를 durable authority에 기록 가능

### Required Construction Boundary

Release flow는 다음 순서를 강제한다.

```text
Exactly Five Current
    ↓
Materialize Canonical Review Artifact
    ↓
User visually reviews exact artifact
    ↓
Authorize exact artifact identity/hash
    ↓
No accepted receiver-visible mutation since authorization
    ↓
All-or-Nothing Release
       ├─ PNG Export
       └─ Blogger Delivery
    ↓
Destination Readback
```

### Exit — Measured Predicate

다음을 모두 실측한다.

#### A. Authorization Binding

1. 승인 요청은 사용자가 실제로 보고 있는 exact `artifact_id`와 hash를 제출한다.
2. authorization record는 해당 artifact identity에 영속 결속된다.
3. authorization이 server restart 후에도 보존된다.
4. authorization 자체가 `Published` 또는 delivery success를 의미하지 않는다.

#### B. Release Closure Revocation

5. 승인 이후 bubble text 한 글자를 authoritative mutation으로 수용하는 시험을 수행한다.
6. 해당 mutation acceptance 즉시 기존 authorization을 사용할 수 없게 된다.
7. gap/geometry/style/pixel 등 다른 receiver-visible change에도 동일하다.
8. 기존 authorized artifact로 current modified composition을 발행하는 우회 경로가 없다.
9. 새 composition은 새 review artifact 및 새 authorization을 요구한다.

#### C. All-or-Nothing Release

10. 하나라도 STALE이면 release request가 차단된다.
11. 다섯 cut 중 한 asset을 읽을 수 없게 만들어 release를 시험한다.
12. 4컷 partial PNG/Blogger payload가 생성되지 않는다.
13. compositor 또는 packaging failure가 발생하면 전체 release가 실패한다.
14. silent omission/continue 경로가 없다.

#### D. PNG Export

15. PNG export가 authorized canonical artifact를 source로 사용한다.
16. export 과정에서 text reflow/font recalculation/bubble relocation/cut reorder를 수행하지 않는다.
17. format 변환 또는 필요한 composition-preserving scaling만 허용한다.
18. 출력 PNG가 승인 artifact의 composition identity를 보존함을 image/hash/geometry readback으로 검증한다.

#### E. Blogger Delivery

19. Blogger payload 역시 authorized canonical artifact를 source로 사용한다.
20. delivery attempt 자체는 local transaction에 기록된다.
21. authoritative remote response가 성공을 명확히 증명하면 destination identity를 기록한다.
22. 외부 게시물 ID와 실제 접근 가능한 목적지 정보를 readback한다.
23. local authorization과 remote delivery status를 하나의 `PUBLISHED` boolean로 합치지 않는다.

#### F. Unknown Outcome

24. Blogger request 이후 response를 의도적으로 차단/timeout시키는 시험을 수행한다.
25. local result가 `Unknown`/`Unresolved`가 된다.
26. UI가 `발행 결과 미확인`에 해당하는 truth를 표시한다.
27. local request 기록만으로 success를 창조하지 않는다.
28. destination readback으로 실제 성공이 확인된 경우에만 Confirmed Success로 이동한다.
29. 실제 실패가 authoritative하게 확인된 경우에만 Confirmed Failure로 이동한다.

#### G. Four Counterexample Gates

30. Gate 1 Currency 실측 통과
31. Gate 2 Identity 실측 통과
32. Gate 3 Interruption 실측 통과
33. Gate 4 External Truth 실측 통과

### Invariants

* INV-1 ~ INV-8 전부
* 모든 Path Invariants
* 특히 INV-4, INV-5, INV-6, INV-8

### Continuation

`BLOCK-05` 자체의 Exit와 별도로 다음을 모두 재확인한 경우에만 Transformation Outcome 완료를 선언한다.

* BLOCK-01 ~ BLOCK-05 Exit evidence 존재
* Completion Predicate 전항목 충족
* Gate 1 ~ Gate 4 실측 통과
* Final Authoritative Readback 가능
* unresolved upstream truth 없음

이를 만족하면 본 Baseline의 Transition Outcome은 **COMPLETE**로 판정할 수 있다.

### Abort

다음 경우 release 전이를 즉시 중단한다.

* authorization이 artifact identity가 아닌 boolean 하나로 존재
* accepted change 후 old approval을 계속 사용할 수 있음
* 일부 cut failure에도 release 계속
* export/Blogger가 current editor를 독자 재조판
* timeout을 성공으로 간주
* local state만으로 external publication을 확정
* destination identity/readback 없이 최종 성공 선언

### Insufficient for Exit

다음은 Exit가 아니다.

* 승인 버튼이 동작함
* PNG 파일이 생성됨
* Blogger API가 HTTP 2xx를 한 번 반환함
* local state가 `published=true`임
* happy-path만 검증함
* partial failure test가 없음
* authorization revocation race test가 없음
* timeout/Unknown test가 없음
* destination readback이 없음

---

## 11. Safe Continuation

### Safe Continuation Predicate

Block `N`에서 `N+1`로 이동하려면 다음을 모두 만족해야 한다.

1. 현재 Block의 Exit Predicate가 실제 실행/상태 readback으로 검증됨
2. 관련 authoritative state가 SQLite에서 재조회 가능함
3. 적용되는 Global/Path Invariant 위반이 없음
4. known stale/orphan state가 다음 Block에서 정상으로 오인되지 않음
5. 실패한 proof 또는 미확인 predicate가 없음
6. 다음 Block이 선행 Block의 authority를 우회하는 별도 임시 진실을 필요로 하지 않음

### Required Handoff Facts

각 Block handoff는 최소 다음 사실을 보유해야 한다.

* 어떤 Exit Predicate를 어떤 실행으로 검증했는지
* authoritative readback 결과
* 관련 regression test 결과
* 알려진 unresolved state 유무
* invariant violation 유무

**위험이 관찰되지 않았다는 사실은 Safe Continuation의 증거가 아니다.**

predicate 또는 readback이 Unknown이면 자동 handoff를 수행하지 않는다.

---

## 12. Safe Abort

### Trigger

다음 중 하나라도 발생하면 현재 Transition Block을 안전 중단한다.

* Single Durable Authority 붕괴
* Stale Overwrite 가능성 발견
* accepted intent 유실
* 5컷 contract 파괴
* review artifact identity 불명확
* release authorization이 수정 후 살아 있음
* partial silent transport 발견
* 외부 결과를 local inference로 조작
* 후행 Block이 상류 truth 결함을 가리기 위해 필요해짐

### Authorized Safe Target State

Safe Abort 후 상태는 다음을 만족해야 한다.

* 이미 accepted 된 authoritative intent는 가능한 한 보존
* 성공한 과거 realization bytes는 손상시키지 않음
* 최신 intent 미충족이면 STALE로 남김
* 실행 중 process는 필요 시 종료
* 실행 truth는 Running으로 위장하지 않음
* authorization/delivery truth를 임의 승격하지 않음
* 실패 원인과 재진입에 필요한 authoritative readback을 확보

### Forbidden Abort Behavior

* DB truth를 맞추기 위해 사용자의 최신 intent를 삭제
* stale asset을 Current로 승격
* failed delivery를 Published로 마킹
* lock file을 추가하여 구조적 동시성 문제를 임시 봉합
* 후행 UI에서 상태를 숨김으로써 상류 결함을 해결한 것처럼 보이게 함

---

## 13. Atomic Boundaries

본 Baseline이 모든 구현 작업을 하나의 거대 atomic change로 요구하는 것은 아니다. 그러나 다음 의미 경계는 안전한 중간 상태를 깨뜨리면서 분할해서는 안 된다.

### 13.1 Intent Acceptance

새 desired intent의 authoritative acceptance와 그 revision identity 부여는 하나의 DB transaction boundary이다.

### 13.2 Realization Commit

candidate generation result를 canonical realization으로 승격하는 행위와 current desired revision 검증은 같은 commit boundary 안에서 결속되어야 한다.

### 13.3 Receiver-Visible Mutation Closure

receiver-visible authoritative composition change의 acceptance와 기존 Release Authorization 무효화는 승인 재사용이 가능한 중간 상태를 남겨서는 안 된다.

### 13.4 Review Artifact Registration

materialized bytes의 immutable identity/hash와 그것이 귀속되는 composition/revision set의 등록은 서로 모순될 수 없는 하나의 authority boundary를 형성해야 한다.

### 13.5 Delivery Outcome Recording

local delivery attempt 기록과 external confirmation은 구분한다. 외부 시스템을 local DB transaction에 포함시킬 수 없으므로:

```text
local attempt
    ≠
external confirmed outcome
```

외부 결과는 반드시 readback 이후 별도 authoritative observation으로 기록한다.

---

## 14. Banned False Successes

아래 상태는 구현 또는 테스트가 성공 종료하더라도 제품 성공으로 인정하지 않는다.

1. **Stale Completion Fallacy**

   * 오래된 pixel이 존재한다는 이유로 최신 intent를 Complete 처리
2. **Silent Overwrite**

   * 늦게 끝난 old revision job이 최신 realization을 덮음
3. **Unpersisted State Illusion**

   * save 실패한 browser draft를 저장된 상태처럼 표시
4. **Volatile Approval Trap**

   * restart 시 Structural Baseline 또는 Release Authorization이 소실
5. **Partial Silent Transport**

   * 5컷 중 일부를 생략하고 PNG/Blogger 성공 처리
6. **Authorization-As-Delivery Fallacy**

   * 2차 승인을 publication success와 동일시
7. **Phantom Outcome Invention**

   * timeout/불명확한 external response를 success/failure로 추정
8. **UI Event Inversion**

   * authoritative 성공/실패/currency event를 client interpretation 오류로 반대로 표시
9. **Queue-Equals-Completion Fallacy**

   * queue drain을 realization completeness로 간주
10. **Projection-Equals-Canonical Fallacy**

    * browser DOM projection을 승인/전달 정본으로 간주
11. **Lock-As-Authority Recovery**

    * concurrency 결함을 별도 file lock authority 추가로 봉합
12. **Downstream Repair Fallacy**

    * upstream truth가 깨진 상태를 export/publish 성공으로 덮어 완결 선언

---

## 15. Final Transition Acceptance Matrix

| Truth Dimension  | Final Required State                                                       | Forbidden Substitute                  |
| ---------------- | -------------------------------------------------------------------------- | ------------------------------------- |
| Intent           | exactly five accepted effective intents under approved Structural Baseline | synopsis copy, client draft, old JSON |
| Realization      | five revision-current canonical assets                                     | file presence, job success            |
| Composition      | authoritative normalized composition                                       | browser-only geometry                 |
| Visual Truth     | immutable Canonical Review Artifact                                        | DOM reconstruction, export rerender   |
| Approval         | exact artifact-bound durable authorization                                 | memory boolean, generic approved flag |
| Release          | all-or-nothing payload from authorized artifact                            | partial payload                       |
| PNG              | composition-preserving artifact export                                     | fresh re-layout                       |
| Blogger          | authorized artifact delivery                                               | current editor rerender               |
| Delivery Truth   | confirmed success/failure/unknown separated                                | generic published boolean             |
| External Success | destination readback evidence                                              | local request completion              |
| Runtime          | one `comic-new serve` production process                                   | mandatory frontend daemon             |
| Client State     | server/draft/save isolation                                                | local state masquerading as authority |
| Interruption     | intent durable, execution terminal, stale visible                          | intent rollback, fake spinner         |
| Concurrency      | DB transaction + revision commit gate                                      | application lock files                |

---

## 16. Final Completion Declaration Rule

`comic_new`는 다음 명제가 실제 시스템에서 참일 때만 본 Transition Baseline을 완료한 것으로 선언한다.

> **정확히 5개의 안정된 컷에 대한 창작자의 최신 accepted intent가 단일 transactional authority 아래 단조 revision으로 보존되고, 각 최신 intent에 귀속된 realization만 canonical state로 승격되며, 5컷 모두 Current일 때 하나의 immutable Canonical Review Artifact가 생성되고, 창작자가 승인한 바로 그 artifact만 All-or-Nothing 방식으로 PNG 또는 Blogger에 전달되며, 외부 전달 성공은 destination readback으로만 확정된다. STOP·실패·재시작·경쟁 완료·저장 충돌·네트워크 불명확성 어느 경우에도 이 인과 사슬의 진실이 조용히 왜곡되지 않아야 한다.**

다음 네 문장이 동시에 실측 참이어야 한다.

1. **Gate 1:** 오래된 5개 PNG가 있어도 최신 intent 하나가 미실현이면 Complete가 될 수 없다.
2. **Gate 2:** 승인 후 receiver-visible 한 글자라도 accepted 변경되면 기존 authorization으로 release할 수 없다.
3. **Gate 3:** STOP/restart 후 accepted latest intent는 남고 실행만 정직하게 종료되며 이전 pixel은 필요 시 STALE로 표시된다.
4. **Gate 4:** Blogger 결과가 불명확하면 destination readback 전까지 publication success를 선언할 수 없다.

이 네 Gate 중 하나라도 실패하면 BLOCK-05의 정상 기능 수와 관계없이 Transformation Outcome은 미완료이다.

---

## 17. Placement and Use

권장 저장 경로:

`/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-001.md`

본 Baseline은 승인된 `THESIS-001`과 `FRONTEND-ARCH-001`을 구현 단계로 투영하는 상위 Transition 문서이다.

후속 계획은 반드시 현재 Active Block의 Entry/Exit/Invariants 범위 안에서 파생되어야 하며, 아직 진입하지 않은 후행 Block의 세부 구현을 이유 없이 선제적으로 확대하지 않는다.

**Block progress is not product truth.
Code presence is not completion.
Asset presence is not currency.
Authorization is not delivery.
Local delivery intent is not external success.**
