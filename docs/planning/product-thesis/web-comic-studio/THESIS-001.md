# Product Thesis: Web Comic Studio — 의도 실현과 조판 정본의 인과적 보존을 통한 5컷 만화 완결

Result: CALIBRATED  
Artifact-Type: product-thesis  
Thesis-Revision: THESIS-001  
Project-Root: /home/user01/project/comic_new  
Meaning-Slug: web-comic-studio  
Language: ko  
Authored-On: 2026-09-15  
Planning-Owner: Main  
Consultation: Oracle Browser Slot 3 (3-Round CodexPro Mode Calibration)  
Diagnostic-Evidence: /home/user01/project/comic (THESIS-008, INV-001, src/comic)  
UI-Architecture-Source: docs/planning/frontend-architecture/FRONTEND-ARCH-001.md (sha256:8eea9545d82b40e64791cd0d6b3340e848b72923d36373bae6425cc39badac9b)  
Invocation-Boundary: 본 문서는 comic_new의 유일한 제품 의미 규범 원본이다. 기술적 구현 세부(Plan/Implementation)를 침범하지 않으며 하위의 파편화된 Spec/Ticket 문서를 양산하지 않는다.
---

## 1. Source Authority & Anti-Bloat Governance

### 1.1 배경 및 작성 경위
본 문서는 과거 `~/project/comic`에서 누적된 심각한 난개발, 생성 엔진 이원화로 인한 덮어쓰기(Stale Overwrite), 1,800줄 스파게티 프론트엔드의 상태 불일치, WYSIWYG 파괴, 파일 락 난립, 그리고 8회에 걸친 테시즈 개정과 산더미 같은 SPEC/TICKET 문서 비대화(Bloat)의 교훈을 바탕으로 작성되었다.  
기존 `~/project/comic`의 코드와 문서는 결함 진단과 반례 도출을 위한 참고 증거(Diagnostic Evidence)일 뿐이며, `~/project/comic_new`에 대한 구현 호환성 권위를 갖지 않는다.  
UI 및 인터랙션 경계는 '디자인' 스킬 원칙(ZERO_FETCH, 5대 상호작용 축 분석, 안티-블로트)을 준수하여 작성된 `docs/planning/frontend-architecture/FRONTEND-ARCH-001.md`를 원천으로 하여 본 테시스에 정식 결속(Bound)되었다.
### 1.2 단일 규범 권위 (Sole Normative Authority)
- `THESIS-001`은 `comic_new`의 제품 의미, 사용자 효용, 인과적 루프, 불변식을 정의하는 **유일한 규범적 권위(Sole Normative Authority)**이다.
- 구현을 보조하는 하위 계획이나 실행 아티팩트가 필요할 경우 파생 투영(Derived Projection)으로 존재할 수 있으나, 본 문서의 제품 의미를 수정, 재정의, 우회할 수 없다.
- 기능의 개수, 화면의 수, 파일 락의 종류, 스케줄러 알고리즘과 같은 기술적 수단은 Thesis의 본질이 아니며, 오직 사용자가 약속된 핵심 결과를 실제로 획득하는 인과적 무결성만으로 제품의 완결성을 판단한다.

---

## 2. Reason to Exist & 5-Truth Failure

### 2.1 기존 시스템의 근본 실패: 5대 진실의 분열
과거 comic 시스템은 개별 기능 블록(LLM 콘티 기획, ima2 이미지 생성, 캔버스 식자 편집, 조판, 블로거 발행)이 모두 존재했음에도 불구하고, 다음 5가지 진실 차원이 서로 다른 파일, 메모리 변수, 렌더러, 비동기 경로로 파편화되어 상호 모순을 일으켰다:

1. **Intent Truth (의도 진실)**: 창작자가 원하는 대사/콘티가 storyboard JSON, lettering JSON, synopsis 텍스트로 삼원화되어 어떤 것이 진짜 최신 의도인지 분열됨.
2. **Realization Truth (실현 진실)**: 전체 생성(`/run`)과 컷별 재생성(`/regenerate`)의 커밋 권위가 분리되어, 재생성으로 먼저 완료된 최신 픽셀을 뒤늦게 끝난 전체 생성이 오래된 픽셀로 조용히 덮어씀(Stale Overwrite).
3. **Canonical Visual Truth (시각 진실)**: 브라우저 화면(CSS % 좌표), PNG 내보내기(PIL 24자 줄바꿈), 블로거 발행(별도 resize 후 재합성)이 각자 독립된 렌더러로 말풍선과 배치를 재해석하여 WYSIWYG가 완전히 파괴됨.
4. **Approval Truth (승인 진실)**: 1차 승인은 메모리 변수(`is_approved`)에만 있어 서버 재시작 시 풀려버리고, 2차 승인은 발행 승인일 뿐인데 도메인 상태를 즉시 `PUBLISHED`로 왜곡 기록함.
5. **Delivery Truth (전달 진실)**: 조판 과정에서 이미지가 깨져도 조용히 `continue`하여 4컷만 전달되거나, 외부 블로거 응답 성공 여부와 무관하게 로컬 상태만으로 발행 성공을 단정함.

### 2.2 comic_new의 존재 이유
`comic_new`는 단순한 "기능이 더 많은 만화 생성기"가 아니다.  
**Comic Studio는 창작자의 최신 승인 의도를 단 하나의 분열 없는 인과 사슬(5-Truth Chain)을 통해 정확히 5개의 정본 컷으로 실현하고, 창작자가 눈으로 확인·승인한 바로 그 조판 정본을 왜곡 없이 외부로 전달하는 완결 시스템으로 존재한다.**

---

## 3. Product Promise & Boundary

### 3.1 핵심 제품 약속 (Core Promise)
> **창작자의 승인된 5컷 구조적 Baseline 아래에서 현재 수용된 최신 Effective Intent를 정확히 5개의 정본 컷으로 실현하고, 창작자가 확인·승인한 동일한 조판 정본을 훼손·왜곡 없이 내보내거나 외부에 전달한다.**

### 3.2 제품 고정 경계 (Fixed Boundary: Exactly Five Stable Ordered Cuts)
- 본 제품은 **정확히 5개의 안정된 순서형 컷 식별자(Five Stable Ordered Cut Identities: 1..5)**를 소유한다.
- 임의 N컷 확장, 컷 추가, 컷 삭제, 컷 재색인(Reindexing) 등의 가변적 생애주기는 제품 경계에서 명시적으로 배제한다.
- 창작 과정에서의 수정(Revision)은 각 컷의 의도(Intent)나 실현본(Realization)을 변경하는 행위이며, 컷의 소속이나 슬롯 자체를 변경하는 생애주기를 만들지 않는다.

---

## 4. Core Causal Loop

전체 창작 흐름은 이전 단계의 대상 동일성을 다음 단계가 엄격히 보존하는 단 하나의 관통 인과 루프로 정의된다:

```text
Source Brief (시놉시스/기획 메모)
    ↓
Approved Structural Baseline (1차 승인: 5컷 서사 구조 동결)
    ↓
Five Effective Cut Intents (컷별 단일 최신 의도)
    ↓
Five Current Realizations (컷별 최신 실현 픽셀)
    ↓
Draft Composition (편집 캔버스 상의 인터랙티브 투영)
    ↓
Canonical Review Artifact (승인 대상이 되는 단일 조판 실체화 정본)
    ↓
Release Authorization (2차 공개 승인)
    ↓
External Delivery + Destination Readback (단일 정본의 외부화 및 실제 증거 확인)
```

1. **Source Brief → Baseline**: 원천 메모를 기반으로 5개 컷의 서사적 역할과 순서가 합의되고 동결됨.
2. **Baseline → Cut Intents**: 동결된 서사 틀 아래에서 각 컷은 정확히 하나의 실효 의도(Effective Intent)를 가짐.
3. **Intent → Realization**: 수용된 컷 의도가 단조 증가 revision 검증을 거쳐 정본 이미지 자산으로 실현됨.
4. **Realization → Composition**: 5개 실현 컷 위에 대사/말풍선이 배치된 인터랙티브 편집 모델이 형성됨.
5. **Composition → Review Artifact**: 편집 모델이 픽셀 수준의 단일 조판 정본으로 실체화(Materialized)되어 창작자에게 검토물로 제시됨.
6. **Review Artifact → Authorization**: 창작자는 추상 사양이 아니라 자신이 눈으로 확인한 바로 그 정본 실체(Review Artifact)를 승인함.
7. **Authorization → Delivery**: 승인된 바로 그 정본 실체가 재조판 없이 외부 파일(PNG) 또는 목적지(Blogger)로 전달됨.
8. **Delivery → Readback**: 외부 목적지의 권위 있는 실제 응답/게시 확인(Readback)을 통해서만 전달 성공이 최종 확정됨.

---

## 5. 8대 인과적 불변식 (Load-Bearing Invariants)

### INV-1 (Single Effective Intent & Structural Baseline)
1차 승인은 정확히 5개의 안정된 ordered cut identity와 그 서사적 관계를 `Structural Baseline`으로 동결한다. 각 컷에는 언제나 하나의 `Effective Current Intent`만 존재한다. 다른 컷의 의도나 5컷 구조 계약을 변경할 필요가 없는 국소 수정(대사 표현, 시각 프롬프트 등)은 해당 컷의 새 revision이 되며 Baseline은 유지된다. 컷의 역할이나 서사 의존성을 뒤흔드는 수정은 새 Structural Baseline과 새 1차 승인을 요구한다. Baseline, 과거 revision, 화면 투영, 복제 데이터는 현재 의도와 경쟁하는 별도의 mutable authority가 될 수 없다.

### INV-2 (Monotonic Intent Realization)
수용된 컷 intent revision은 엄격히 단조 증가한다. canonical realization은 현재 desired revision에 귀속된 결과만 수용할 수 있으며, 지연 완료된 이전 작업, 대체된(superseded) 작업, 취소된 작업은 연산상 성공하더라도 commit authority를 갖지 못하고 즉시 폐기된다. 과거 내용으로 되돌리는 행위 또한 revision의 감소가 아니라 이전 내용을 페이로드로 갖는 새로운 상위 revision의 수용이다. Stale Overwrite는 구조적으로 불가능하다.

### INV-3 (Truthful Currency & Completion)
Asset Completeness는 Intent Completion이 아니다. 오래된 이미지 파일이 디스크에 존재한다는 사실은 최신 의도 충족의 증거가 아니다. 한 컷은 `desired_revision == realized_revision`일 때만 `Current`이며, 정확히 5컷 모두가 Current일 때만 작품의 실현이 `Complete`이다. 실행 상태(Running/Idle/Interrupted), 실현 완료성(Current/Stale), 릴리즈 승인 여부(Authorized/Unauthorized), 전달 결과(Not Attempted/Unknown/Confirmed)는 서로 다른 진실 차원이며 절대 하나의 상태로 치환되거나 대리될 수 없다.

### INV-4 (Canonical Review Artifact)
편집 화면은 현재 composition의 인터랙티브 투영(Interactive Projection)이다. 2차 릴리즈 승인의 대상은 추상 데이터나 편집 투영 화면이 아니라, 창작자가 실제로 눈으로 확인한 실체화된 `Canonical Review Artifact`이다. 외부 전달(PNG 내보내기, Blogger 발행)은 인코딩 포맷 변환이나 목적지 규격에 맞춘 전체 균등 축소(Uniform Scaling)와 같은 composition-preserving transformation만 허용하며, 텍스트 재줄바꿈(reflow), 폰트 재계산, 말풍선 재배치, 내용 crop, 컷 재순서화 등 조판을 독자적으로 재해석하는 일체의 행위를 금지한다.

### INV-5 (Immediate Authorization Revocation by Release Closure)
Canonical Review Artifact의 픽셀, 기하 좌표, 텍스트, 타이포그래피, 컷 순서, 컷 간 간격(Gap) 등 수신자가 인지하는 최종 결과물에 영향을 줄 수 있는 어떠한 의도라도 시스템의 authoritative state에 정식 수용(accepted)되는 '그 즉시' 기존 Release Authorization은 무효화된다. 저장되지 않은 클라이언트 로컬 편집물은 authoritative intent가 아니며 과거 승인을 상속하지 않는다.

### INV-6 (Complete Release & Honest Delivery Outcome)
정확히 5개 컷 모두가 Current이고 승인된 Release Closure와 100% 일치하지 않으면 릴리즈 페이로드를 생성하거나 제출할 수 없다. 컷 누락이나 합성 실패가 발생했을 때 조용히 건너뛰는(continue) 부분 릴리즈는 엄격히 금지된다. 외부 전달 결과는 확정 성공(Confirmed Success), 확정 실패(Confirmed Failure), 미확인(Unresolved/Unknown)을 정직하게 구분하며, 통신 장애나 응답 누락으로 결과가 불명확할 때 로컬 추정만으로 성공이나 실패를 창조할 수 없다.

### INV-7 (Durable Intent Across Interruption)
STOP 조작, 시스템 충돌, 서버 재시작은 현재 실행 중인 물리적 연산(Subprocess)을 즉시 종료할 수 있으나, 이미 책임 있게 수용된 창작자의 desired intent를 조용히 철회하지 않는다. 이전 realization 픽셀은 보존될 수 있으나 최신 intent를 만족하지 못하면 반드시 `STALE`로 고지된다. 의도의 철회나 과거 상태로의 복귀는 사용자의 명시적인 새 intent 수용을 통해서만 이루어진다.

### INV-8 (Single Durable Local Authority & External Evidence Boundary)
제품이 소유하는 현재 의도, realization 귀속, composition identity, authorization 및 실행/시도 사실은 단 하나의 영속적 트랜잭션 권위(Single Durable Transactional Authority) 아래 원자적으로 기록된다. 프로세스 메모리 변수나 분산된 파일 락은 이에 경쟁하는 독립 권위가 될 수 없다. 외부 목적지의 실제 상태는 로컬 트랜잭션이 원자적으로 창조할 수 없으며, 오직 destination readback으로 관측된 사실만을 외부 전달 진실로 기록한다.

---

## 6. Core Behavior & UI Policy

### 6.1 Baseline Locality & Synopsis Boundary
- **1차 승인(Baseline)의 성격**: 5컷의 전체 서사 뼈대와 컷별 역할을 고정한다.
- **국소 수정의 범위**: 대사 변경, 시각 프롬프트 튜닝 등 단일 컷 내부에서 완결되는 수정은 1차 승인을 유지하며 해당 컷의 `desired_revision`만 증가시킨다.
- **구조적 재승인 요구**: 컷의 서사적 역할 전도, 컷 순서 변경 등 5컷 간 상호 의존성을 깨는 수정은 1차 승인을 무효화하고 새로운 Baseline 형성을 요구한다.
- **시놉시스(Source Brief)의 경계**: 1차 승인 전 시놉시스는 Baseline 형성의 입력이다. 1차 승인 후 UI에서 편집되는 시놉시스 텍스트는 단순 에피소드 기획 참고 메타데이터(Reference Metadata)이며, 현재 컷들의 의도를 암묵적으로 변소시키거나 2차 릴리즈 승인을 깨뜨리지 않는다. 시놉시스 수정을 작품 전체에 반영하려면 명시적인 `Re-baseline` 조작을 수행해야 한다.

### 6.2 Presence is Not Currency (STALE 상태 고지)
- 특정 컷에 대해 최신 intent $v_{new}$가 요청되었으나 생성이 진행 중이거나, 중단(STOP)되었거나, 실패하여 물리적으로 이전 이미지 $v_{old}$만 존재하는 경우:
  - 시스템은 유효한 기존 자산인 $v_{old}$ 픽셀을 임의로 삭제하거나 숨기지 않고 캔버스에 유지한다.
  - 동시에 UI는 이 컷이 최신 의도를 반영하지 못하고 있음을 명백하게 `[STALE: 최신 의도 미실현 / 재시도 필요]` 뱃지와 함께 표시한다.
  - 이 컷이 존재하는 한 작품 전체의 Realization 상태는 절대 `Complete`로 표시될 수 없으며 `UNRESOLVED` 상태를 유지한다.

### 6.3 정직한 편집 투영과 에러 가시화 (Unsaved State Transparency)
- 사용자가 캔버스에서 말풍선 좌표를 이동하거나 텍스트를 입력할 때 브라우저 화면은 즉각적인 편집 편의를 위한 투영(Interactive Projection)을 제공한다.
- 그러나 서버 영속화 요청이 네트워크 장애, 409 Conflict, 500 오류 등으로 실패한 경우:
  - UI는 에러를 콘솔에만 남기거나 저장된 척 위장하는 것을 엄격히 금지한다.
  - 즉각 사용자에게 "저장 실패" 토스트 및 경고 상태를 노출하고, 해당 변경분이 아직 정본 의도로 수용되지 않았음을 시각적으로 식별 가능하게 격리한다.

### 6.4 3열 스튜디오 레이아웃 & 5대 상호작용 축 경계 (`FRONTEND-ARCH-001`)
- **Header (`StudioHeader`)**: 상단 영구 고정. 프로젝트 상태 요약, 큐 상태 요약, 즉시 `STOP` 명령 버튼을 항상 노출하며 스크롤이나 선택 상태에 가려지지 않는다.
- **Left Rail (`CutRail`)**: 좌측 영구 고정(데스크톱). 정확히 5개 컷 슬롯의 썸네일, 의도/실현 revision, STALE 상태를 상시 표시한다.
- **Center Canvas (`CompositionCanvas`)**: 중앙 영구 고정. 5컷 전체 조판 투영 및 말풍선 시각 인터랙션을 담당한다.
- **Right Inspector (`InspectorPanel`)**: 우측 영구 고정(데스크톱, 비모달). 선택된 컷의 프롬프트/대사 상세 폼을 제공한다. 캔버스 작업 조작을 차단하는 모달 대화상자로 구현하는 것을 엄격히 금지한다.
- **작업 큐 상세 (`QueuePopover`)**: 비모달 트리거 팝오버. 헤더 큐 버튼에 앵커되어 세부 작업 목록과 개별 취소를 제공한다.
- **최종 검토 및 승인 (`ReviewModal`)**: **유일한 포커스 트랩 모달**. 백엔드에서 실체화된 `Canonical Review Artifact`를 검토하고 2차 승인을 내릴 때만 캔버스를 차단하는 전용 모달을 사용한다.

### 6.5 캔버스 식자 기하 모델 & 조작 규격
- 말풍선 위치와 크기는 브라우저 뷰포트나 개별 컷 이미지가 아닌 **Canonical Composition Surface 기준 백분율 좌표 (`x_pct`, `y_pct`, `w_pct`, `h_pct`)**로 엄격히 정규화된다. 뷰포트 줌, 리사이즈, 화면 해상도 변화에도 기하는 불변이다.
- 거대 서드파티 캔버스 라이브러리를 배제하고 네이티브 `PointerEvent` + SVG/DOM 오버레이로 구현하며, 포인터 캡처(`setPointerCapture`) 및 `pointercancel` 자동 복구, 키보드 미세 이동(Nudge: 0.5%, Shift: 2.0%)을 지원한다.

### 6.6 단일 서빙 배포 계약 (Single-Serving Deployment Boundary)
- 웹 프론트엔드는 빌드되어 백엔드 패키지 데이터(`src/comic_new/static/`)로 단일 배포된다.
- 프로덕션 런타임은 오직 `comic-new serve` 단일 Python 프로세스만 구동되며, 별도의 Node 데몬, SSR 서버, 외부 웹 서버를 요구하지 않는다.
---

## 7. Banned False Successes (영구 금지된 거짓 성공 반례)

다음 행위들은 테스트나 코드가 정상 종료를 보고하더라도 제품 수준에서 완전한 결함으로 규정된다:

1. **Stale Completion Fallacy**: 최신 컷 생성 요청이 실패하거나 중단되었음에도 이전 픽셀 파일이 존재한다는 이유로 작품을 완료(Complete)로 처리하는 행위.
2. **Silent Overwrite**: 오래된 요청의 비동기 실행 결과가 사용자의 더 최신 컷 수정 결과를 덮어쓰는 행위.
3. **Unpersisted State Illusion**: 영속화가 거절되었거나 진행되지 않은 클라이언트 메모리 상의 편집 내용을 정상 저장된 정본으로 위장하는 행위.
4. **Volatile Approval Trap**: 1차 콘티 승인이나 2차 릴리즈 승인이 서버 재시작 시 메모리에서 휘발되어 잠금이 풀려버리는 행위.
5. **Partial Silent Transport**: 5컷 중 일부가 누락되거나 조판 오류가 발생했음에도 조용히 `continue`하여 불완전한 만화를 발행/내보내는 행위.
6. **Authorization-As-Delivery Fallacy**: 2차 승인이 완료되었다는 사실을 외부 발행이 성공했다는 사실과 동일시하는 행위.
7. **Phantom Outcome Invention**: 외부 시스템 응답이 타임아웃되거나 불명확할 때 실제 확인 없이 성공 또는 영구 실패로 단정하는 행위.
8. **UI Event Inversion**: 시스템 내부의 성공 이벤트(예: 3/3 성공)를 클라이언트 해석 오류로 인해 실패(예: 실패 0컷)로 왜곡 전달하는 행위.

---

## 8. Observable Success & Acceptance Readback

제품이 스스로 특정 단계의 '성공'을 선언하기 위해서는 다음의 권위 있는 상태 또는 외부 증거를 반드시 읽어낼 수 있어야 한다:

| Causal Boundary | 성공 판정 기준 (Authoritative Readback) |
| :--- | :--- |
| **Intent Accepted** | 단일 트랜잭션 저장소에서 해당 컷의 단조 증가된 `desired_revision`이 영속적으로 재조회됨 |
| **Cut Realized** | canonical 컷 자산이 바로 그 `desired_revision`에 귀속되어 존재하며 무결한 이미지 바이트로 확인됨 |
| **Realization Complete** | 5개 컷 모두 `realized_revision == desired_revision`이며 어떠한 미해결 의도도 남지 않음 |
| **Composition Canonicalized** | 5컷 픽셀, 말풍선 좌표, 텍스트, 폰트 비율, Gap이 단일한 `Canonical Review Artifact`로 실체화되어 화면에 노출됨 |
| **Release Authorized** | 2차 승인 레코드가 바로 그 `Canonical Review Artifact`의 전체 identity에 불변으로 결속되어 영속화됨 |
| **Release Delivered** | 외부 전달 페이로드가 승인된 artifact와 100% 동일한 composition identity를 유지한 채 생성됨 |
| **Destination Confirmed** | 외부 서비스(Blogger 등)의 고유 게시물 식별자 및 실제 접근 가능한 URL이 authoritative response로 확인됨 |

**"하류의 어떠한 성공도 상류에서 깨진 인과적 진실을 대체하거나 복구할 수 없다 (No downstream success may repair or substitute for a broken upstream truth)."**

---

## 9. Counterexample Gates

본 Thesis를 검증하기 위한 4대 반례 차단 게이트:

- **Gate 1 (Currency Gate)**: 아무리 훌륭하고 정상적인 5개의 PNG 파일이 존재하더라도, 1개 컷이라도 최신 요청 의도가 실현되지 않은 상태라면 시스템이 '완료' 상태로 진입하는 것이 가능한가? → **불가능해야 함 (차단).**
- **Gate 2 (Identity Gate)**: 2차 승인 후 말풍선 텍스트 1글자나 컷 간격(Gap) 1px을 수정했을 때, 기존의 2차 승인 권한을 이용해 외부 발행을 진행하는 것이 가능한가? → **불가능해야 함 (수용 즉시 승인 자동 취소).**
- **Gate 3 (Interruption Gate)**: 생성 도중 STOP을 누르거나 서버를 강제 재부팅했을 때, 수용되었던 최신 의도가 사라져 이전 의도로 되돌아가거나 가짜 running 스피너가 도는가? → **불가능해야 함 (의도 영속 보존, 작업은 정직한 INTERRUPTED 정리, 기존 픽셀은 STALE 고지).**
- **Gate 4 (External Truth Gate)**: 인터넷 연결이 끊겨 Blogger 응답을 받지 못했을 때, 로컬에 저장된 데이터만으로 "발행 완료"를 표시할 수 있는가? → **불가능해야 함 (Unknown/Unresolved 유지).**

---

## 10. Open Product Meaning & Downstream Boundary

### 10.1 본 문서에서 의도적으로 결정하지 않은 기술 세부 (Plan / Implementation Scope)
- **저장 기술 구현체**: SQLite, JSON transactional store, PostgreSQL 등 구체적인 DB/라이브러리 선택.
- **웹 서버 및 통신 프레임워크**: FastAPI, Starlette, SSE 프로토콜 세부 필드명 및 엔드포인트 URL 네이밍.
- **이미지 생성기 연동 방식**: ima2 CLI subprocess 호출, HTTP 데몬 연동, 워커 풀 크기(concurrency limit) 및 프로세스 시그널(SIGTERM/SIGKILL).
- **조판 렌더러 구현 라이브러리**: Python PIL, Skia, Canvas 라이브러리 선택 및 픽셀 블렌딩 알고리즘.
- **프론트엔드 아키텍처 및 구현 스택**: Vue 3 + TypeScript + Vite 단일 SPA 및 번들링 배포로 확정 (`docs/planning/frontend-architecture/FRONTEND-ARCH-001.md`에 결속).

### 10.2 잔여 제품 제약 (Open Product Meaning)
- 본 문서에 명시된 5컷 만화 창작·수정·검토·발행의 닫힌 인과 루프에 대한 미결정 제품 의미는 **없음 (None)**.
- 본 Thesis는 완전하게 확정(CALIBRATED)되었으며, 후속 계획 및 구현은 본 문서의 8대 불변식과 5-Truth 체인을 구현하는 가장 간결하고 단단한 아키텍처를 수립한다.
