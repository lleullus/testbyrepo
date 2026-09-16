# Product Thesis: Web Comic Studio — 의도 실현과 조판 정본의 인과적 보존을 통한 5컷 만화 완결

Result: CALIBRATED  
Artifact-Type: product-thesis  
Thesis-Revision: THESIS-002  
Project-Root: /home/user01/project/comic_new  
Meaning-Slug: web-comic-studio  
Language: ko  
Authored-On: 2026-09-16  
Planning-Owner: Main  
Prior-Sources: THESIS-001.md (sha256:74561c6874bbb5a0bb7b15b8b39e0f75b8a8f426f4085b951b467ceef3fb2d63)  
Diagnostic-Evidence: Oracle Browser Slot 3 Product Completion Brief (comic-product-completion-brief-20260916)  
UI-Architecture-Source: docs/planning/frontend-architecture/FRONTEND-ARCH-001.md (sha256:8eea9545d82b40e64791cd0d6b3340e848b72923d36373bae6425cc39badac9b)  
Invocation-Boundary: 본 문서는 comic_new의 유일한 제품 규범 원본(Sole Normative Authority)이다. 본 문서는 구현 세부를 서술하지 않으며, 제품의 존재 이유, 사용자 약속, 인과적 루프, 불변식 및 검증 기준을 정의한다.

---

## 1. Source Authority & Anti-Bloat Governance

### 1.1 배경 및 개정 경위
본 개정본(THESIS-002)은 `THESIS-001`의 기본 철학과 블록 전이 성과를 계승하되, Oracle Browser Slot 3(GPT-5.6 Sol)을 통해 수행된 **Product Completion Brief**의 정밀 진단 결과를 전면 수용하여 수립되었다.  
진단 결과, 초기 아키텍처는 SQLite 단일 트랜잭션 권위, 5컷 고정 스키마, 단일 큐, 단일 PIL 합성기, Pinia 드래프트 분리 등 핵심 뼈대를 성공적으로 수립했으나, 프로덕션 완결성 관점에서 다음 5대 중대 결함(P0 Gaps)이 확인되었다:

1. **동일 Revision 내 생성 요청 Supersession 부재**: 프롬프트 수정 없이 재성성을 연속 요청할 경우, 늦게 끝난 이전 요청이 먼저 끝난 새 결과를 덮어쓰는 경쟁(Race) 존재.
2. **STOP / Cancel과 커밋 간 비원자적 경계**: 프로세스 종료 전 candidate가 canonical로 승격되거나, 취소 요청이 이미 성공한 픽셀의 이력을 `cancelled`로 왜곡 기록하는 경계 결함 존재.
3. **Structural Baseline 백엔드 강제 부재 및 대사 Authority 분열**: 콘티 승인 없이 API로 바로 생성을 진입할 수 있는 백엔드 우회로와, `CutIntent.dialogue`와 `composition.bubbles[].text` 간 권위 분열 존재.
4. **승인 아티팩트 TOCTOU (Time-of-Check to Time-of-Use)**: 검증된 인메모리 바이트가 아닌 디스크 경로를 다시 읽어 Blogger로 전송하는 파일 변조 위험 창 존재.
5. **목적지 Readback의 아티팩트 동일성 미검증**: 단순 HTTP GET 200 여부만 확인할 뿐, 실제 목적지에 승인된 만화 아티팩트와 해시가 존재하는지 검증하지 않음.

본 문서는 이러한 병리를 제품 규범 차원에서 영구 차단하기 위해 인과적 불변식과 제품 행동을 강화한다.

### 1.2 단일 규범 권위 (Sole Normative Authority)
- `THESIS-002`는 `comic_new`의 제품 의미, 사용자 효용, 인과적 루프, 불변식을 정의하는 **유일한 규범적 권위**다.
- 기술적 수단(DB 테이블 구조, 내부 함수, 프로세스 시그널 방식 등)은 본 문서의 인과적 보장을 달성하기 위한 도구일 뿐이며, 규범 그 자체가 아니다.
- 제품의 성패는 기능의 나열이나 UI의 미려함이 아니라, **사용자가 약속된 5컷 만화 정본을 왜곡·유실·거짓 피드백 없이 획득하는 인과적 무결성**으로만 판정한다.

---

## 2. Reason to Exist & 5-Truth Chain

### 2.1 5대 진실 사슬 (5-Truth Chain)
Comic Studio는 창작자의 머릿속 기획부터 외부 독자 전달까지 단 하나의 단절 없는 5대 진실 사슬로 연결되어야 한다:

1. **Intent Truth (의도 진실)**: 창작자가 승인한 서사 구조(Baseline)와 각 컷의 최신 연출 의도가 모호함이나 이원화 없이 단일하게 정의된다.
2. **Realization Truth (실현 진실)**: 단조 증가하는 의도 및 생성 요청 순서에 결속된 최신 결과만이 정본 픽셀이 되며, 어떠한 과거·취소·중단된 결과도 최신 픽셀을 덮어쓸 수 없다.
3. **Canonical Visual Truth (시각 진실)**: 창작자가 확인하는 편집 캔버스 투영과 최종 합성되는 조판 정본은 0.0~100.0% 정규화 좌표계 아래에서 완전히 동일한 시각적 배치와 대사를 보장한다 (WYSIWYG).
4. **Approval Truth (승인 진실)**: 릴리즈 승인은 추상 데이터가 아닌 물리적으로 실체화된 조판 정본(Canonical Review Artifact)의 바이트 해시에 결속되며, 단 1px이나 1글자의 변경이라도 수용되는 즉시 승인은 원자적으로 무효화된다.
5. **Delivery Truth (전달 진실)**: 외부 전달(PNG/Blogger)은 승인된 바로 그 아티팩트 바이트를 변형 없이 전송하며, 목적지에서 실제 내용 식별자(Content Identity)가 Readback으로 확인될 때만 성공으로 확정한다.

---

## 3. Product Promise & Boundary

### 3.1 핵심 제품 약속 (Core Promise)
> **창작자의 승인된 5컷 구조적 Baseline 아래에서 현재 수용된 최신 Effective Intent를 단조 순서가 보장된 정본 컷으로 실현하고, 창작자가 최종 검토·승인한 동일한 단일 조판 정본을 바이트 수준의 동일성 검증과 목적지 Readback을 거쳐 안전하게 외부로 전달한다.**

### 3.2 제품 고정 경계 (Fixed Boundary)
- **Exactly Five Stable Ordered Cuts**: 제품은 항상 정확히 5개의 고정 순서 컷 식별자 `1..5`만 소유한다. 임의 N컷 추가/삭제/순서 섞기는 제품 경계에서 제외한다.
- **Single Active Narrative Stream**: 하나의 프로젝트는 단 하나의 활성 서사 상태를 가지며, 복수의 서사 브랜치나 버전 관리를 제공하지 않는다.
- **Single Serving Runtime**: 별도의 복잡한 마이크로서비스나 외부 태스크 브로커 없이, 단일 프로세스 서버 아래에서 동작한다.

---

## 4. Core Causal Loop

```text
Source Brief (시놉시스 / 기획 의도)
    ↓ [1차 승인: 서사 뼈대 및 5컷 배정 동결]
Approved Structural Baseline
    ↓ [컷별 연출·대사 의도 수용]
Five Effective Cut Intents (Desired Revision Monotonicity)
    ↓ [단일 큐 비동기 생성 + 커밋 시점 Currency/Sequence 검증]
Five Current Realizations
    ↓ [정규화 백분율 좌표계 기반 인터랙티브 편집 투영]
Draft Composition
    ↓ [단일 PIL 합성기를 통한 물리 픽셀 결속 및 Content Hash 생성]
Canonical Review Artifact (Closure Materialization)
    ↓ [창작자의 실체화 정본 전수 검토 및 2차 공개 승인]
Release Authorization (Artifact Hash Bound)
    ↓ [승인 바이트 직접 전달 + Destination Content Readback]
External Delivery Truth (Confirmed Success / Failure / Unknown)
```

---

## 5. 8대 인과적 불변식 (Load-Bearing Invariants)

### INV-1. Single Effective Intent & Strict Baseline Precondition
1. **Baseline 선행 필수성**: 시스템은 유효하게 승인된 `Structural Baseline`이 존재하지 않는 한 어떠한 컷의 의도(Cut Intent) 수용이나 생성(Generation) 요청도 백엔드 수준에서 거절한다. UI 비활성화에 의존하지 않고 서버 트랜잭션 경계에서 이를 강제한다.
2. **단일 컷 의도**: 각 컷에는 언제나 단 하나의 `Effective Current Intent`만 존재한다.
3. **대사 진실의 일원화**: 컷의 서사적 대사 의도는 `CutIntent`가 유일한 권위를 갖는다. 조판 편집(`Composition`)에서의 말풍선 텍스트 수정은 시각적 타이포그래피 배치의 조정이거나 새로운 Cut Intent revision 수용을 수반하며, 하나의 컷에 대해 서로 다른 대사가 독립 영속되는 상태를 금지한다.

### INV-2. Monotonic Realization & Generation Request Supersession
1. **Desired Revision 단조 증가**: 수용된 컷의 `desired_revision`은 엄격히 증가한다.
2. **동일 Revision 내 요청 Supersession**: 동일한 컷에 대해 `desired_revision`이 동일하더라도 새로운 생성 요청이 수용되면, 해당 컷의 단조 증가하는 `generation_request_seq`가 발행된다.
3. **커밋 자격 단일성**: `commit_candidate()`는 해당 컷의 `desired_revision`과 `generation_request_seq`가 모두 최신 활성 요청과 일치할 때만 픽셀 승격을 허용한다. 지연 완료된 이전 요청은 물리적 연산이 성공했더라도 커밋 자격을 박탈당하고 즉시 폐기된다. Stale Overwrite는 100% 원천 차단된다.

### INV-3. Truthful Currency & Honest Completion
1. **Presence Is Not Currency**: 오래된 이미지 파일이 디스크에 존재한다는 사실은 최신 의도 충족의 증거가 아니다.
2. **컷 단위 Currency**: `desired_revision == realized_revision`이고 해당 컷에 미완료된 상위 생성 요청이 없을 때만 그 컷은 `Current`이다.
3. **작품 전체 Completion**: 정확히 5개 컷 모두가 `Current`일 때만 작품의 실현은 `Complete`이며, 단 1개 컷이라도 미실현이거나 STALE이면 작품 상태는 `UNRESOLVED`이다.

### INV-4. Canonical Review Artifact & In-Memory Transport
1. **실체화 정본의 유일성**: 승인의 대상은 편집 화면의 DOM/CSS 투영이 아니라, 단일 PIL 합성 엔진이 5컷 픽셀, 정규화 백분율 좌표, 폰트, 마진, 갭을 물리적으로 구워낸 단일 PNG 바이트 실체(`Canonical Review Artifact`)이다.
2. **In-Memory Verified Passing (Anti-TOCTOU)**: 릴리즈 사전 검증에서 승인 해시와 일치함이 확인된 바로 그 immutable 바이트 객체를 외부 전달 전송기(Blogger/PNG)로 직접 전달한다. 검증 후 디스크 파일을 다시 읽는 2차 I/O를 배제하여 검증-전송 간 파일 변조 위험을 제거한다.

### INV-5. Immediate Authorization Revocation by Release Closure
1. **즉각적 무효화**: 픽셀, 말풍선 좌표, 대사 텍스트, 컷 간 간격(Gap), 스타일 등 최종 결과물에 영향을 미치는 어떠한 의도라도 수용(accepted)되는 '그 즉시' 기존의 `Release Authorization`은 동일 트랜잭션 내에서 원자적으로 철회(revoked)된다.
2. **클라이언트 드래프트의 무권위**: 브라우저 로컬의 미저장 드래프트는 권위가 없으며 승인을 파괴하지 않지만, 승인 상태에서 외부 전달을 시도할 때 미저장 드래프트가 남아있다면 릴리즈는 차단된다.

### INV-6. Complete Release & Destination Content Readback
1. **All-or-Nothing 릴리즈**: 5개 컷 모두 Current이고 유효한 Release Authorization이 존재하지 않으면 어떠한 외부 페이로드도 생성할 수 없다. 1개 컷 결측이나 조판 실패 시 작업을 건너뛰는 부분 릴리즈는 엄격히 금지된다.
2. **Byte-Identical PNG Export**: PNG 내보내기는 승인된 아티팩트 바이트를 1바이트의 오차도 없이 그대로 출력 파일에 복사한다.
3. **Content-Identity Readback**: 외부 전달(Blogger)의 성공은 단순 HTTP GET 200 응답이 아니라, 원격 게시물 본문에서 승인된 아티팩트 식별자(Artifact ID / SHA-256 Content Hash)가 온전히 Readback될 때만 `Confirmed Success`로 확정한다.
4. **정직한 Unknown 보존**: 응답 타임아웃, 네트워크 단절, 5xx 에러는 성공이나 실패로 날조하지 않고 `Unknown` 상태로 영속화하며, 임의 재시도로 인한 중복 게시를 방지하기 위해 원격 재대조(Reconciliation) 경로를 제공한다.

### INV-7. Atomic Interruption Closure Across STOP & Cancel
1. **커밋 자격의 원자적 박탈**: 전역 STOP이나 개별 Cancel 요청이 수용되면, 물리적 프로세스를 종료하기에 앞서 DB 트랜잭션 내에서 대상 작업들을 즉시 `commit-ineligible`(취소/중단) 상태로 전환한다.
2. **사후 커밋 차단**: STOP 수용 시점 이후에 도착하는 워커의 `commit_candidate()`는 트랜잭션 경계에서 즉각 거절되며, 결코 canonical 픽셀로 승격될 수 없다.
3. **실행 진실 왜곡 방지**: 이미 성공하여 canonical로 승격된 작업은 뒤늦은 Cancel 요청에 의해 `cancelled`로 덮어씌워지지 않는다. 상태 전이는 오직 합법적인 유한 상태 기계(FSM) 가드를 통해서만 일어난다.
4. **의도 보존**: 프로세스 종료는 연산의 중단일 뿐이며, 창작자가 수용한 desired intent는 영속 보존된다. 미실현 픽셀은 정직하게 `STALE`로 고지된다.

### INV-8. Single Durable Transactional Authority
1. **단일 SQLite 권위**: 제품의 모든 의도, 실현 상태, 조판 기하, 승인 레코드, 큐 작업 및 전달 이력은 단 하나의 로컬 SQLite 데이터베이스(`comic-new.sqlite3`) 트랜잭션 아래에서 원자적으로 기록된다.
2. **분산 락 배제**: 파일 락(`.lock`), 메모리 플래그, 사이드카 파일은 상태 권위가 될 수 없다. 동시성 제어는 SQLite의 원자적 트랜잭션(`BEGIN IMMEDIATE`)과 monotonic revision CAS로만 해결한다.

---

## 6. Core Behavior & UI Policy

### 6.1 Baseline 선행 및 콘티 생애주기
- 프로젝트 생성 직후 상태는 `INIT`이다.
- 콘티 기획이 수용되고 창작자가 이를 확정할 때 `Structural Baseline`이 생성되고 1차 승인된다.
- 1차 승인 전에는 개별 컷 의도 수용이나 이미지 생성이 전면 차단된다.
- 서사 뼈대를 뒤흔드는 대규모 수정은 명시적인 `Re-baseline` 조작을 통해서만 수행되며, 이는 기존의 모든 컷 intent와 realization의 currency를 재검토 상태로 전환한다.

### 6.2 Presence Is Not Currency (STALE 고지)
- 새로운 intent나 재생성이 요청되었으나 아직 생성 중이거나 실패/중단된 경우, 기존 유효 픽셀을 임의로 삭제하지 않고 캔버스에 유지한다.
- UI는 해당 컷에 `[STALE: 최신 의도 미실현]` 뱃지를 상시 표시하며, 전체 진행률은 100% 완료로 표시될 수 없다.

### 6.3 클라이언트 드래프트 격리 및 스트림 복구 (Anti-Illusory UI)
- 프론트엔드 스토어는 `server`, `drafts`, `saves`를 완전히 분리한다.
- 409 Conflict 또는 500 오류 시 사용자 입력을 조용히 증발시키거나 저장된 척 위장하지 않고, "저장 실패" 경고와 함께 로컬 드래프트를 보존한다.
- **Degraded Resync State**: SSE 스트림 단절이나 revision gap 발생 시 snapshot 재조회가 성공할 때까지 UI는 `DEGRADED / RESYNC_REQUIRED` 상태를 유지하며, 생성·승인·릴리즈 등 중대한 상태 전이 액션을 차단한다.

### 6.4 캔버스 기하 정규화 및 WYSIWYG
- 말풍선과 텍스트의 위치·크기는 Canonical Surface 대비 0.0~100.0%의 백분율 좌표(`x_pct`, `y_pct`, `w_pct`, `h_pct`)로만 다룬다.
- 백엔드 PIL 렌더러와 프론트엔드 SVG/DOM 오버레이는 동일한 상대 기하 계약을 공유하며, 뷰포트 크기 변화에 의해 텍스트 위치나 배치가 왜곡되지 않는다.

---

## 7. Banned False Successes (영구 금지된 거짓 성공 반례)

1. **Stale Overwrite**: 늦게 끝난 이전 요청이 사용자의 더 최신 생성 의도나 재생성 요청 결과를 덮어쓰는 행위.
2. **Post-STOP Ghost Commit**: 전역 STOP이나 취소가 수용된 이후 백그라운드 워커가 픽셀을 커밋하여 화면을 바꿔버리는 행위.
3. **Unapproved Baseline Bypass**: 1차 서사 구조 승인 없이 개별 컷 생성으로 직행하여 만화를 완성했다고 주장하는 행위.
4. **Dialogue Double-Truth**: 시각 편집기의 말풍선 대사와 컷 의도의 대사가 서로 다른 텍스트를 가진 채 둘 다 정본 행세를 하는 행위.
5. **Partial Silent Release**: 5컷 중 결측이 있거나 조판 에러가 발생했음에도 조용히 4컷만 묶어 내보내는 행위.
6. **Phantom Delivery Confirmation**: 외부 서비스 응답이 없거나 단순 URL 접근만 가능한 상태에서 실제 아티팩트 존재 확인 없이 성공으로 확정하는 행위.
7. **Stale Recovery Reversion**: SSE 스트림 갭 복구가 실패했음에도 오래된 스냅샷을 최신으로 간주하여 사용자에게 승인 버튼을 열어주는 행위.

---

## 8. Observable Success & Acceptance Readback

| 경계 | 권위 있는 성공 판정 기준 (Authoritative Readback) |
| :--- | :--- |
| **Baseline Established** | 단일 SQLite 트랜잭션에서 5컷 구조가 바인딩된 `structural_baselines` 레코드가 활성 상태로 조회됨 |
| **Intent Accepted** | 활성 Baseline 아래에서 컷의 단조 증가된 `desired_revision`이 기록됨 |
| **Generation Enqueued** | `desired_revision`과 신규 `generation_request_seq`에 결속된 job이 `generation_jobs`에 대기 등록됨 |
| **Cut Realized** | 해당 `desired_revision` 및 `request_seq`와 일치하는 candidate 픽셀만 무결한 PNG로 검증되어 canonical 자산으로 원자적 승격됨 |
| **Realization Complete** | 5개 컷 모두 `realized_revision == desired_revision`이며 미완료 작업이 없음 |
| **Review Materialized** | 5컷 정본 픽셀과 정규화 조판이 단일 PIL 합성기에 의해 불변 `review_artifacts`로 실체화되고 고유 SHA-256 해시가 부여됨 |
| **Release Authorized** | 바로 그 실체화 아티팩트의 해시와 composition revision에 결속된 `release_authorizations` 레코드가 활성 상태로 영속화됨 |
| **Release Delivered** | 승인 검증을 통과한 바로 그 불변 바이트 메모리 객체가 외부 전송기로 직접 전달되어 전송됨 |
| **Destination Confirmed** | 외부 목적지에서 발행된 게시물 식별자 및 본문 내 아티팩트 식별 마커(Artifact ID/Hash)가 실제 Readback으로 확인됨 |

---

## 9. 4대 반례 차단 게이트 (Counterexample Gates)

- **Gate 1 (Currency Gate)**: 5개의 PNG 파일이 디스크에 존재하더라도, 1개 컷이라도 최신 요청 의도와 불일치하거나 활성 작업이 남아있다면 완료 상태 진입이 가능한가? → **불가능 (차단)**
- **Gate 2 (Identity Gate)**: 2차 승인 후 말풍선 텍스트 1글자나 컷 간격 1px을 수정했을 때, 기존 승인으로 릴리즈를 진행할 수 있는가? → **불가능 (수용 즉시 원자적 승인 철회)**
- **Gate 3 (Interruption Gate)**: STOP을 누른 직후 워커가 생성을 마쳤을 때 픽셀이 커밋되거나, 취소된 작업이 성공 픽셀의 이력을 왜곡할 수 있는가? → **불가능 (트랜잭션 내 커밋 자격 즉시 박탈 및 FSM 가드)**
- **Gate 4 (External Truth Gate)**: Blogger 응답이 없거나 단순 200 페이지만 반환될 때 승인 아티팩트 해시 확인 없이 성공을 확정할 수 있는가? → **불가능 (Content-Identity Readback 전까지 Unknown 유지)**

---

## 10. Open Product Meaning

- 본 제품 의미에 대한 미해결 영역: **없음 (None)**.
- 본 문서는 완전하게 캘리브레이션(`CALIBRATED`)되었으며, 구현 및 검증은 본 문서의 8대 불변식과 5-Truth 체인을 단 하나의 누수 없이 만족해야 한다.
