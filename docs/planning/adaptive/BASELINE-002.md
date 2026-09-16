# Transition Baseline BASELINE-002 — Web Comic Studio Product Completion & Hardening

Status: APPROVED  
Baseline-ID: BASELINE-002  
Revision: 1  
Project-Root: /home/user01/project/comic_new  
Meaning-Slug: web-comic-studio  
Applicability: Product Completion & Production Cutover Hardening of Web Comic Studio adhering to THESIS-002 and Oracle Product Completion Brief  
Authored-On: 2026-09-16  
Language: ko  

---

## 1. Identity & Approval

### 1.1 Baseline Identity
* **Baseline-ID:** `BASELINE-002`
* **Status:** `APPROVED`
* **Project-Root:** `/home/user01/project/comic_new`
* **Meaning-Slug:** `web-comic-studio`
* **Applicability:** `THESIS-002` 및 오라클 Product Completion Brief 진단에 기반한 Web Comic Studio의 완결성 하드닝 및 프로덕션 컷오버
* **Request Reference:** `comic-new-baseline-002-20260916`

### 1.2 Source Authority
1. **현재 사용자 지시**: `THESIS-002` 기반의 전이 베이스라인 작성 및 완결성 검증
2. **Product Thesis**:
   * `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-002.md`
   * SHA-256: `1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f`
3. **진단 원천 (Diagnostic Baseline Source)**:
   * Oracle Browser Slot 3 (GPT-5.6 Sol) Product Completion Brief (`comic-product-completion-brief-20260916`)
4. **선행 전이 원천 (Prior Foundation)**:
   * `BASELINE-001.md` (BLOCK-01 ~ BLOCK-05 완료 기반)
5. **프론트엔드 아키텍처 원천**:
   * `docs/planning/frontend-architecture/FRONTEND-ARCH-001.md`

`THESIS-002`는 본 베이스라인의 최상위 제품 규범 권위이다. 본 문서는 `comic_new`가 초기 기초 블록(BLOCK-01~05)을 넘어 실제 프로덕션 상용 환경에서 단 하나의 데이터 꼬임이나 거짓 피드백 없이 안정적으로 동작하도록 만드는 **전이 권위 지도(Transition Authority Map)**이다.

---

## 2. Transformation Outcome

### 2.1 Goal
`BASELINE-002`의 목표는 오라클의 Product Completion Brief를 통해 식별된 **5대 P0 결함 및 잔여 운영 리스크를 완전히 봉합**하고, 4대 Counterexample Gate의 실측 증거를 확보하여 **프로덕션 컷오버(Production Cutover)를 최종 완결**하는 것이다.

### 2.2 해결해야 할 5대 핵심 P0 갭
1. **P0-1 (Realization Truth)**: 동일 컷·동일 revision 재생성 요청 간 supersession 부재로 인한 Stale Overwrite 가능성 제거.
2. **P0-2 (Interruption Truth)**: STOP/Cancel 수용과 백그라운드 커밋 간의 비원자적 경계 레이스로 인한 사후 유령 픽셀 커밋 및 FSM 이력 왜곡 원천 차단.
3. **P0-3 (Intent Truth)**: Structural Baseline 없는 컷 의도 수용 및 생성 직행 백엔드 우회로 차단, 대사(Dialogue)의 단일 원천 권위 일원화.
4. **P0-4 (Delivery Truth)**: 승인 아티팩트 검증 후 디스크 파일을 다시 읽는 2차 I/O 구조를 배제하고, 검증된 인메모리 바이트를 직접 전송하는 Anti-TOCTOU 체계 구축.
5. **P0-5 (Delivery Truth)**: 단순 HTTP 200 확인이 아닌, 원격 게시물 본문의 아티팩트 식별자(ID 및 해시 마커)를 검증하는 Content-Identity Readback 확증.

### 2.3 Required Named Items
1. **Monotonic Generation Request Sequence**: 컷별 단조 증가 시퀀스(`generation_request_seq`) 및 최신 요청만 커밋 가능한 원자적 자격 통제.
2. **Atomic Interruption FSM & Commit Lockout**: STOP/Cancel 수용 즉시 동일 트랜잭션에서 커밋 자격을 박탈하는 원자적 경계 및 유한 상태 기계(FSM) 전이 가드.
3. **Strict Structural Baseline Precondition Guard**: 활성 Baseline이 없을 때 컷 의도 수용 및 생성 요청을 백엔드 트랜잭션 수준에서 거절하는 인과 통제.
4. **Unified Narrative Dialogue Authority**: `CutIntent.dialogue`를 단일 권위로 확립하고 조판 말풍선과의 인과적 동기화 보장.
5. **In-Memory Verified Artifact Transport**: 사전 검증된 불변 바이트 메모리 객체를 외부 전송기(Blogger/PNG)로 직결하는 무결성 전송 파이프라인.
6. **Content-Identity Destination Readback**: Blogger HTML 내 아티팩트 메타 마커 삽입 및 원격 Readback 시 본문 내 해시 실측 검증.
7. **Frontend Degraded Resync State**: SSE 스트림 갭 복구 실패 시 stale 스냅샷을 current로 오인하지 않고 `DEGRADED` 상태를 유지하여 위험 액션을 잠그는 UI 보호.
8. **Empirical Gate Verification**: 4대 Counterexample Gate 전항목의 실제 경쟁·중단·단절 시나리오 실측 통과.

---

## 3. Global Invariants & Transition Rules

`THESIS-002`의 8대 불변식(INV-1 ~ INV-8)을 그대로 준수하며, 본 전이 과정에서 다음 하드닝 규칙을 추가로 구속한다:

1. **RULE-01 (Atomic Commit Revocation)**: STOP/Cancel 조작은 프로세스 종료 시그널 발송 전에 반드시 대상 job들의 상태를 `commit-ineligible`로 변경하는 DB 트랜잭션을 완료해야 한다.
2. **RULE-02 (Sequence-Bound Currency)**: 픽셀 커밋 권한은 `(cut_id, desired_revision, generation_request_seq)`의 정확한 3중 튜플 일치에만 부여된다.
3. **RULE-03 (No Baseline Bypass)**: 어떠한 컷도 활성 `structural_baselines` 레코드 없이는 `cut_intents` row를 가질 수 없으며 큐에 등록될 수 없다.
4. **RULE-04 (Zero Second-Read on Delivery)**: 릴리즈 사전 검증에서 읽어 SHA-256을 검증한 바로 그 바이트 메모리 객체만 외부로 전송한다. 디스크 재조회는 금지된다.
5. **RULE-05 (Artifact-Bound Confirmation)**: Blogger 외부 전달 성공은 원격 응답 HTML 본문에서 정확한 `artifact_id`와 SHA-256이 확인되기 전에는 절대 선언될 수 없다.

---

## 4. Transition Blocks

```text
[BASELINE-001 완료 기반: BLOCK-01 ~ BLOCK-05]
    ↓
BLOCK-06: Monotonic Generation Currency & Atomic Interruption Closure (P0-1, P0-2 해소)
    ↓
BLOCK-07: Strict Structural Baseline Precondition & Dialogue Authority (P0-3 해소)
    ↓
BLOCK-08: In-Memory Verified Transport & Content-Identity Readback (P0-4, P0-5 해소)
    ↓
BLOCK-09: Client Resync Safety & Empirical Gate Cutover Finalization (P1 해소 및 최종 완결)
```

---

### BLOCK-06 — Monotonic Generation Currency & Atomic Interruption Closure

* **Block-ID:** `BLOCK-06`
* **Name:** Monotonic Generation Currency & Atomic Interruption Closure
* **Target P0s:** P0-1 (동일 리비전 덮어쓰기 레이스), P0-2 (STOP/Cancel 커밋 레이스)
* **Meaning Contribution:** 의도 수정 없는 재생성 연타 시 최신 요청 결과만 안착되도록 보장하고, STOP/Cancel 수용 즉시 커밋 자격을 박탈하여 사후 유령 커밋과 상태 왜곡을 원천 차단.
* **Dependencies:** BLOCK-01, BLOCK-02 (선행 완료)
* **Envelope / Scope Boundary:**
  - `store.py`: `cuts` 테이블에 `latest_generation_request_seq INTEGER DEFAULT 0` 추가. `generation_jobs` 테이블에 `request_seq INTEGER` 추가.
  - `generation.py`: 
    - 컷 생성 요청 시 컷별 `generation_request_seq` 증가 및 job에 결속.
    - `commit_candidate()` 시 `desired_revision`과 함께 `request_seq == cuts.latest_generation_request_seq` 검증. 이전 요청 결과는 연산 성공 여부와 무관하게 폐기.
    - `stop_all_and_cancel_queued()` 및 `cancel_job_in_store()`에서 프로세스 킬 전에 `BEGIN IMMEDIATE` 트랜잭션 내에서 실행 중인 attempt/job을 즉시 취소/중단 상태로 전환하여 커밋 불가 처리.
    - `mark_job_and_attempt_cancelled()`에 FSM 전이 가드(`WHERE status = 'running'`) 추가하여 이미 성공한 작업이 cancelled로 역전되는 현상 차단.
* **Exit Predicate (실측 조건):**
  1. 동일 컷에 대해 프롬프트 수정 없이 Job A 요청 후 즉시 Job B 요청 시, Job B의 `request_seq`가 더 크며 지연 완료된 Job A가 결코 픽셀을 커밋할 수 없음을 경쟁 테스트로 증명.
  2. 워커가 PNG 생성을 마치고 커밋 직전인 시점에 STOP을 수용하면, 수용 직후 워커의 커밋 시도가 트랜잭션 경계에서 즉각 거절되고 픽셀이 바뀌지 않음을 증명.
  3. 이미 커밋 성공한 작업에 뒤늦은 cancel 요청이 도착해도 상태가 `cancelled`로 왜곡되지 않고 `succeeded`를 유지함을 증명.
* **Safe Continuation:** Exit 1~3 실측 통과 시 BLOCK-07 진입.

---

### BLOCK-07 — Strict Structural Baseline Precondition & Dialogue Authority

* **Block-ID:** `BLOCK-07`
* **Name:** Strict Structural Baseline Precondition & Dialogue Authority
* **Target P0s:** P0-3 (베이스라인 백엔드 강제 부재, 대사 권위 이원화)
* **Meaning Contribution:** 1차 서사 승인(콘티 확정) 없이 개별 컷 생성으로 직행하는 인과 붕괴를 백엔드 수준에서 원천 차단하고, 대사의 유일한 권위를 `CutIntent`로 일원화.
* **Dependencies:** BLOCK-06
* **Envelope / Scope Boundary:**
  - `store.py`: 
    - `accept_cut_intent()`, `enqueue_generation_jobs()`, `set_desired_intent()` 등에서 `current_baseline_id`가 `None`이면 `BaselineRequiredError`(HTTP 409/412)를 발생시키는 트랜잭션 가드 추가.
    - DDL 수준의 외래키 또는 트리거 방어 검증.
  - `server.py`:
    - `/api/cuts/{cut_id}/intent` 및 `/api/generation/jobs` 엔드포인트에서 활성 베이스라인 존재 여부를 엄격히 선행 검증.
  - 대사 진실 일원화:
    - 컷의 서사적 대사는 `CutIntent.dialogue`를 유일한 단일 권위(Sole Authority)로 확립.
    - 조판 편집(`composition.py` 및 프론트엔드)에서 말풍선 텍스트 수정 시, 해당 텍스트를 `CutIntent.dialogue`의 갱신과 인과적으로 연동하거나, 조판 단계의 말풍선 텍스트 수정이 명시적인 intent 동기화 트랜잭션을 거치도록 통제.
* **Exit Predicate (실측 조건):**
  1. 프로젝트 초기화 후 Structural Baseline 승인 없이 컷 의도 수용 또는 생성 API 호출 시, 백엔드가 100% 거절함을 증명.
  2. Baseline 승인 후에만 컷 의도 등록 및 큐 등록이 허용됨을 증명.
  3. 컷의 대사 조회 시 `CutIntent.dialogue`와 조판 말풍선 텍스트 간 모순이 존재하지 않음을 증명.
* **Safe Continuation:** Exit 1~3 실측 통과 시 BLOCK-08 진입.

---

### BLOCK-08 — In-Memory Verified Transport & Content-Identity Readback

* **Block-ID:** `BLOCK-08`
* **Name:** In-Memory Verified Transport & Content-Identity Readback
* **Target P0s:** P0-4 (승인 아티팩트 TOCTOU), P0-5 (목적지 Readback 아티팩트 미검증)
* **Meaning Contribution:** 승인 검증된 바이트 메모리 객체를 외부 전송기로 직접 전달하여 파일 변조 위험을 제거하고, 블로그 발행 후 원격 본문에서 실제 아티팩트 해시를 Readback하여 가짜 성공을 원천 차단.
* **Dependencies:** BLOCK-07
* **Envelope / Scope Boundary:**
  - `delivery.py`:
    - `preflight_release()`에서 검증 완료된 `verified_bytes` 객체를 반환하고, `GoogleBloggerAdapter.publish()` 및 `export_png()`가 디스크 경로를 다시 열지 않고 이 `verified_bytes`를 직접 전달받도록 시그니처 및 호출 체인 리팩터링 (Anti-TOCTOU).
    - Blogger HTML 생성 시 보이지 않는 식별 주석 삽입: `<!-- comic-new:artifact-id={id}:sha256={hash} -->`.
    - `_readback_destination()`을 단순 HTTP GET 200 검사에서 **HTML 본문 내 아티팩트 식별 마커(Artifact ID 및 SHA-256) 파싱 검증**으로 강화.
    - 마커가 없거나 해시가 불일치할 경우 200 응답이라도 `confirmed_success`로 처리하지 않고 `delivery_failed` 또는 `content_corrupted`로 판정.
    - `Unknown` 상태 시 원격 게시물을 재대조(Reconcile)할 수 있는 안전한 검증 엔드포인트 마련.
* **Exit Predicate (실측 조건):**
  1. 사전 검증 통과 후 디스크 파일이 임의 변조되더라도, 기 검증된 메모리 바이트 객체만 온전히 전송됨을 단위/통합 테스트로 증명.
  2. Blogger 목적지 URL이 200을 반환하더라도 본문에 아티팩트 식별 마커가 누락되었거나 해시가 다르면 `confirmed_success`를 선언하지 않음을 실측 증명.
  3. 올바른 마커가 포함된 본문이 Readback될 때만 비로소 `confirmed_success`가 영속화됨을 증명.
* **Safe Continuation:** Exit 1~3 실측 통과 시 BLOCK-09 진입.

---

### BLOCK-09 — Client Resync Safety & Empirical Gate Cutover Finalization

* **Block-ID:** `BLOCK-09`
* **Name:** Client Resync Safety & Empirical Gate Cutover Finalization
* **Target:** P1 갭 해소(스트림 단절 복구 안전성), 4대 Gate 전수 실측, 프로덕션 컷오버 최종 판정
* **Meaning Contribution:** 프론트엔드가 일시적 동기화 실패 시 오래된 데이터를 최신으로 위장하지 못하게 막고, 전 시스템에 걸쳐 4대 반례 게이트를 실측 검증하여 최종 프로덕션 완료 선언.
* **Dependencies:** BLOCK-08
* **Envelope / Scope Boundary:**
  - `frontend/src/store/studio.ts`:
    - SSE gap 복구 실패 시 `gapFetchPending = false`로 풀려 stale 데이터를 current로 오인하는 결함 수정.
    - 명시적인 `stream.status = 'DEGRADED'` 상태를 도입하고, 스냅샷 재동기화 성공 전까지 Generate, Authorize, Release 등 위험한 상태 전이 액션을 비활성화.
  - 전역 통합 하드닝 검증:
    - Gate 1 (Currency): 동일 revision 재생성 연타 경쟁 실측 통과.
    - Gate 2 (Identity): 승인 후 텍스트/간격 미세 수정 시 즉각적인 원자적 승인 철회 실측 통과.
    - Gate 3 (Interruption): 커밋 직전 STOP 수용 시 유령 픽셀 커밋 100% 차단 실측 통과.
    - Gate 4 (External Truth): 타임아웃 Unknown 유지 및 아티팩트 해시 기반 Destination Readback 실측 통과.
  - Final Authoritative Readback 수행 및 프로덕션 컷오버 승인.
* **Exit Predicate (실측 조건):**
  1. SSE 갭 복구 실패 시 프론트엔드가 DEGRADED 상태를 유지하며 consequential action을 안전하게 차단함을 브라우저/유닛 레벨에서 증명.
  2. Gate 1 ~ Gate 4 전 항목이 실제 프로세스·네트워크 결함 주입 테스트에서 차단 통과됨을 증명.
  3. 전체 테스트 스위트 100% 통과 및 최종 권위 재조회(Final Authoritative Readback) 무결성 확인.
* **Safe Continuation:** 전이 완료 선언 (`COMPLETE`).

---

## 5. Completion Predicate

본 Transition Baseline `BASELINE-002`는 다음 조건이 **모두 실측**되었을 때만 최종 완료를 선언한다:

1. **P0-1 실측**: 동일 컷·동일 revision 생성 요청 시 최신 `generation_request_seq`를 가진 요청만 커밋되고 이전 지연 요청은 폐기된다.
2. **P0-2 실측**: STOP 수용 후 백그라운드 워커의 커밋 시도가 트랜잭션에서 거절되어 유령 픽셀 커밋이 0건이다.
3. **P0-3 실측**: Structural Baseline 미승인 상태에서의 컷 의도 수용 및 생성 요청이 백엔드에서 100% 거절된다.
4. **P0-4 실측**: 릴리즈 전달 시 디스크 2차 I/O 없이 사전 검증된 단일 인메모리 바이트 객체만 전송된다.
5. **P0-5 실측**: Blogger destination readback이 원격 본문 내 아티팩트 식별 마커 및 SHA-256 해시 일치를 확인한 뒤에만 성공을 선언한다.
6. **P1 실측**: 프론트엔드 동기화 갭 복구 실패 시 `DEGRADED` 상태가 유지되어 위험한 조작이 차단된다.
7. **Gate 1~4 실측**: Currency, Identity, Interruption, External Truth 게이트가 모두 실측 차단된다.
8. **단일 프로세스 무결성**: 모든 기능이 `comic-new serve` 단일 프로세스 아래에서 완결된다.

---

## 6. Final Authoritative Readback Matrix

| Causal Boundary | Authoritative Readback 성공 기준 |
| :--- | :--- |
| **Baseline Enforced** | Baseline 미승인 시 `BaselineRequiredError` 발생, 승인 후 정상 의도 수용 확인 |
| **Generation Monotonicity** | 동일 컷 다중 요청 시 `latest_generation_request_seq`와 일치하는 candidate만 커밋 확인 |
| **Atomic Interruption** | STOP 수용 트랜잭션 후 도착한 candidate의 커밋 실패 및 STALE 상태 고지 확인 |
| **In-Memory Transport** | 릴리즈 전송 시 전달된 payload의 SHA-256이 승인 레코드 해시와 메모리 상에서 100% 일치 |
| **Destination Content Verified** | Blogger 본문 Readback에서 `artifact_id` 및 SHA-256 마커가 원격 본문에서 실제 파싱 확인 |
| **Client Degraded Safety** | 동기화 실패 시 `hasCurrentSnapshot = false` 및 핵심 버튼 비활성화 확인 |

---

## 7. Open Decisions

- 미결정 사항: **없음 (None)**.
- 본 Baseline은 `THESIS-002`를 완전히 실현하기 위한 구체적인 4단계 전이 블록(BLOCK-06 ~ BLOCK-09)을 수립했으며, 승인 즉시 BLOCK-06 Scoping으로 진입할 수 있다.
