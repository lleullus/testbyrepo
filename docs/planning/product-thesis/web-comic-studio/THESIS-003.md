# Product Thesis: Web Comic Studio — 한 줄 의도에서 가변 N컷 정본 전달까지

Result: CALIBRATED  
Artifact-Type: product-thesis  
Thesis-Revision: THESIS-003  
Project-Root: /home/user01/project/comic_new  
Meaning-Slug: web-comic-studio  
Language: ko  
Authored-On: 2026-09-17  
Planning-Owner: Main  
Prior-Source: THESIS-002.md (sha256:1fe716cd3afc2e179a2acb7b22bd3fd5c62eddeefcc65596febfa0e48e6c511f)  
Diagnostic-Evidence: 8-agent deep dive — fixed-five architecture, baseline UX/code, invariant discipline/code, canvas geometry/rendering  
Legacy-LLM-Source: /home/user01/project/comic/src/comic/llm/client.py  
Invocation-Boundary: 본 문서는 `comic_new`의 제품 의미, 사용자 약속, 상태·행동·실패·회복, 진실 경계와 수용 반례를 정의하는 유일한 규범 원본이다. 구현 순서나 현재 Scope를 선택하지 않으며, 명시된 API·provider·모델은 사용자가 채택한 필수 제품 수단인 경우에만 규범으로 고정한다.

---

## 1. Source Authority

### 1.1 개정 권위와 승계

`THESIS-003`은 `THESIS-002`를 덮어쓰지 않고 새 제품 계약으로 개정한다. 다음 의미는 그대로 승계한다.

- 사용자가 수용한 의도와 실제 생성 결과는 동일한 컷 정체성 및 최신 revision에 귀속되어야 한다.
- 늦은 생성 결과, STOP 이후 결과, 오래된 승인, 목적지에서 확인되지 않은 전달은 성공으로 위장될 수 없다.
- 편집 화면과 최종 조판 정본은 같은 기하·fit·대사 의미를 가져야 한다.
- 최종 전달은 승인된 불변 아티팩트와 그 목적지 readback에 근거해야 한다.

다음 `THESIS-002` 의미는 본 개정으로 폐기된다.

- 정확히 5컷만 유효하다는 고정 cardinality.
- 5개 컷의 모든 prompt를 채워야 첫 컷을 생성할 수 있다는 선입력 조건.
- 고정 `1024×7680` surface와 전역 `y_pct`가 모든 작품의 영구 좌표계라는 가정.
- Baseline 작성이 사용자의 21개 수동 입력으로 시작해야 한다는 흐름.

이 폐기는 안전성 약화가 아니다. 숫자와 작업 순서를 실제 인과 안전 조건에서 분리하고, 안전은 §7의 네 가지 불변식으로 더 좁고 명확하게 유지한다.

### 1.2 직접 채택된 제품 결정

본 개정은 다음을 현재 제품 의미로 채택한다.

1. OpenCodex를 통한 자동 스토리보드·생성 prompt 초안 경로를 복원한다.
2. 한 줄 topic 또는 synopsis로 전체 초안을 제안하는 `POST /api/baselines/generate-draft`를 제공한다.
3. Baseline 승인은 sparse 또는 empty prompt를 허용하며, 빈 prompt 때문에 HTTP 400이 발생해서는 안 된다.
4. 실제 생성 대상 컷의 non-empty effective prompt는 그 컷의 generation enqueue 시점에만 엄격히 요구한다.
5. 다른 컷의 준비 여부와 무관하게 한 컷을 탐색 생성할 수 있다.
6. Phase 1에서 프로젝트 생성 시 `N >= 1`의 컷 수를 허용하고, Phase 2에서 stable identity와 분리된 active membership 및 display order로 컷 추가·비활성화·재정렬을 허용한다.
7. canonical width는 1024px이고, height는 컷 슬롯 높이와 gap에서 동적으로 파생한다.
8. 말풍선 위치는 전역 surface percentage가 아니라 컷 로컬 좌표로 소유한다.
9. 이미지 생성 기본 모델은 실제 연결된 `oauth/gpt-image-2.5-flare`다.

### 1.3 수단과 결과의 구분

- OpenCodex endpoint, draft API, 기본 이미지 모델은 현재 사용자 결정에 의해 제품 계약에 포함되는 필수 수단이다.
- SQLite, PIL, Vue, Pinia, 내부 테이블·함수·migration 절차는 제품 약속을 실현하는 교체 가능한 구현 수단이다.
- 단, 제품 성공은 “API가 존재한다”, “파일이 생겼다”, “큐가 비었다”가 아니라 사용자가 한 줄 의도에서 출발해 검토 가능한 컷을 점진적으로 만들고, 모든 활성 컷이 실현된 동일 정본을 승인·전달했는지로 판정한다.

---

## 2. Product Purpose

### 2.1 존재 이유

Web Comic Studio는 창작자가 머릿속 소재를 이미지 생성 시스템이 소비할 수 있는 구조로 수동 번역하게 만드는 폼이 아니다. 제품은 **짧은 창작 의도를 서사적으로 일관된 가변 N컷 제안으로 변환하고, 사용자가 필요한 컷부터 탐색·수정·실현한 뒤, 최종 활성 컷 전체를 하나의 검증된 웹툰 정본으로 전달하게 하는 창작 도구**다.

현재의 핵심 결손은 다음과 같다.

- 사용자가 첫 이미지를 보기 전에 synopsis 1개와 5컷 × role/beat/prompt/dialogue의 20개 필드, 총 21개 입력을 마주한다.
- 한 컷의 빈 prompt가 전체 Baseline 승인을 400으로 실패시키고, 다른 컷의 유효한 작업까지 막는다.
- 컷 수 5가 안전 불변식인 것처럼 DB·API·renderer·frontend·release에 반복된다.
- backend와 frontend의 슬롯 반올림 및 image fit이 달라 편집 투영과 정본 결과가 어긋난다.
- 전역 `y_pct`는 컷 추가·삭제·재정렬 시 말풍선을 다른 장면으로 이동시킨다.
- 기본 이미지 모델이 연결되지 않은 `nano-banana-pro`를 가리켜 정상 생성 경로가 처음부터 실패할 수 있다.

### 2.2 핵심 제품 약속

> 창작자는 topic 또는 synopsis 한 줄만으로도 편집 가능한 N컷 스토리보드 초안을 즉시 얻고, 승인된 구조 아래 원하는 한 컷부터 생성·비교·수정할 수 있다. 시스템은 각 결과를 정확한 최신 의도와 요청 순서에 귀속하고, 모든 활성 컷이 Current가 된 뒤 사용자가 본 것과 같은 동적 조판 정본만 승인·전달하며, 목적지에서 그 정본의 내용 정체성이 확인될 때만 성공이라 말한다.

### 2.3 제품 경계

제품은 다음을 제공한다.

- 단일 활성 작품 흐름과 그 안의 ordered active cut set.
- AI 초안 생성과 수동 편집의 동등한 진입 경로.
- 컷별 독립 생성, 재생성, 실패 복구와 전체 완결 상태.
- 동적 세로 캔버스, 컷 로컬 말풍선, 단일 canonical review artifact.
- PNG 내보내기와 Blogger 전달의 내용 동일성 확인.

다음은 본 제품 약속이 아니다.

- 복수 사용자의 동시 공동 편집.
- 여러 활성 서사 branch 및 범용 버전 관리.
- 미완성 활성 컷을 조용히 제외한 “전체 작품” 릴리즈.
- provider 실패를 다른 내용의 임의 결과로 숨기는 무한 retry.
- frontend와 backend가 서로 다른 renderer 의미를 갖는 근사 WYSIWYG.

---

## 3. Complete Utility Loop

### 3.1 완전한 사용자 효용 루프

```text
Topic / Synopsis / Brief
    ↓ [한 번의 초안 생성 요청]
AI Storyboard Draft Proposal
    - ordered cuts (N >= 1)
    - cut role / beat / dialogue / generation prompt
    - prompt origin과 제안 상태
    ↓ [사용자 검토·수정·구조 승인]
Approved Structural Baseline + Ordered Active Cut Set
    ↓ [필요한 컷부터 intent 수용 또는 intelligent default 사용]
Per-Cut Effective Intent
    ↓ [선택한 컷만 generation enqueue]
Exploratory Realization / Compare / Revise
    ↓ [활성 컷 전체가 Current가 될 때까지 점진 반복]
Complete Active-Set Realization
    ↓ [동일 layout resolver와 fit policy로 실체화]
Canonical Review Artifact
    ↓ [사용자의 최종 정본 검토·승인]
Artifact-Bound Release Authorization
    ↓ [검증된 동일 bytes 전송]
PNG Export / Blogger Delivery
    ↓ [목적지 content identity readback]
Confirmed Delivery Truth
```

### 3.2 한 번의 초안 생성

`POST /api/baselines/generate-draft`는 topic 또는 synopsis와 선택적 목표 컷 수를 받아 다음의 **제안(draft)** 을 반환한다.

- `N >= 1`인 ordered cuts.
- 각 컷의 stable draft identity, display order, narrative role, beat.
- 대사 또는 무대사 의도.
- 이미지 생성을 위한 self-contained generation prompt.
- 자동 생성 provenance와 provider/model attempt 결과.

이 응답은 자동 승인이나 자동 생성이 아니다. 사용자는 제안을 그대로 승인하거나, 일부만 수정하거나, 수동 Baseline으로 대체할 수 있다. 초안 실패는 기존 작업을 변경하지 않는다.

### 3.3 OpenCodex LLM 경계

자동 초안은 OpenAI-compatible OpenCodex endpoint `http://127.0.0.1:10100/v1`을 사용한다. 기본 fallback chain은 다음과 같다.

1. Primary: `google-antigravity/gemini-3.8-flash`, reasoning `high`, 45초 read timeout.
2. Primary가 `429` 또는 `5xx`이면 최대 1회 재시도한다.
3. Primary가 실패하면 fallback: `gpt-5.6-luna`, reasoning `max`, 90초 read timeout.
4. Fallback도 `429` 또는 `5xx`이면 최대 1회 재시도한다.
5. 전체 wall-clock budget은 150초이며, 두 모델이 모두 실패하면 정직한 초안 생성 실패로 끝난다.

구조화 응답은 JSON object여야 하며 제품 계약에 맞게 검증된 뒤에만 draft로 표시한다. malformed JSON, 누락된 컷 필드, 중복 identity/order는 성공으로 보정하지 않는다. 사용자의 원문 brief는 보존되고, 실패 후 수동 작성과 재시도가 가능하다.

### 3.4 점진 생성과 완결

- Baseline 승인은 모든 컷의 수동 prompt 작성을 요구하지 않는다.
- 사용자는 Cut 1만 준비된 상태에서 Cut 1을 생성할 수 있다. Cut 2…N의 빈 prompt나 미실현 상태는 Cut 1의 enqueue를 막지 않는다.
- 단일 컷의 성공은 그 컷만 `Current`로 만든다. 작품 전체는 나머지 활성 컷이 미실현이면 `UNRESOLVED`다.
- 최종 review artifact와 release는 ordered active cut set `S`가 비어 있지 않고 모든 `i ∈ S`가 Current일 때만 가능하다.
- 탐색용 부분 결과를 preview·비교·저장할 수 있지만, 이를 전체 작품 완료나 릴리즈 성공으로 표시하지 않는다.

---

## 4. UI & Behavioral Semantics

### 4.1 빠른 시작과 21-box 제거

최초 화면의 주 작업은 하나의 `주제 또는 시놉시스` 입력과 `스토리보드 초안 만들기` 버튼이다. 처음부터 N개 컷의 role/beat/prompt/dialogue를 모두 펼치지 않는다.

```text
┌ 새 웹툰 ─────────────────────────────────────┐
│ 주제 또는 시놉시스                           │
│ [ 비 오는 밤, 길 잃은 로봇이 고양이를 만난다 ] │
│ 컷 수 [자동 추천 ▾]     [스토리보드 초안 만들기] │
└──────────────────────────────────────────────┘
```

초안 결과는 카드 또는 rail 형태로 역할·beat·대사·prompt를 보여주며, 각 필드는 수정 가능하다. 자동 값과 사용자 작성 값의 provenance를 구분하되 자동 값이라는 이유만으로 열등하거나 미승인 상태로 간주하지 않는다. 사용자가 구조를 승인하는 행위가 Baseline authority를 만든다.

수동 작성은 동등한 경로다. LLM 사용이 불가능해도 사용자는 `N >= 1`을 선택하고 role/beat만, 또는 sparse prompt만으로 Baseline을 승인할 수 있다.

### 4.2 Baseline 승인과 sparse intent

Baseline 승인은 다음을 허용한다.

- 빈 prompt.
- 일부 컷에만 작성된 prompt.
- 빈 dialogue(무대사라는 유효한 의미).
- AI가 생성한 role/beat/prompt와 사용자가 수정한 값의 혼합.

빈 prompt는 승인 실패가 아니라 “사용자 원문 prompt가 아직 없음”이다. 시스템은 source brief, 컷 role, beat, 인접 맥락과 컷 위치를 사용해 intelligent default를 제안 또는 resolve한다. default는 다음 원칙을 따른다.

1. 사용자가 작성한 non-empty prompt를 최우선으로 보존한다.
2. source brief + 해당 컷 role/beat가 있으면 이를 조합한다.
3. 다른 컷의 seed만 있으면 복사하지 않고 해당 컷 역할에 맞게 self-contained prompt를 만든다.
4. 맥락이 거의 없어도 컷 identity와 구조 정보에 기반한 명시적 generic default를 제공할 수 있다.
5. dialogue는 임의로 합성하지 않는다. 빈 dialogue는 그대로 무대사다.
6. resolved prompt의 origin(`user`, `llm_draft`, `intelligent_default`)을 표시한다.

Baseline 승인 경계에서 빈 prompt 때문에 `400 Bad Request`를 반환하는 것은 금지된다. `store.py`의 과거 “Intent prompt must be a non-empty string” 의미는 이 경계에서 폐기된다.

### 4.3 Generation eligibility

`Generate Cut`은 선택 컷 `i`에 대해서만 다음을 확인한다.

- 활성 Baseline과 active membership에 속하는 stable cut identity.
- 그 컷의 현재 desired revision.
- 사용자 prompt 또는 intelligent default를 resolve한 non-empty effective generation prompt.
- enqueue를 결속할 신규 monotonic request sequence.

다른 컷의 prompt·dialogue·realization 상태는 검사하지 않는다. resolve 이후에도 대상 컷의 prompt가 비어 있거나 구조적으로 유효하지 않다면 **그 컷의 enqueue만** 거절하고, 어떤 정보가 필요한지 컷 카드에 표시한다. Baseline 전체를 무효화하거나 다른 컷 작업을 잠그지 않는다.

`Generate All`은 현재 active set 전체에 대한 명시적 bulk action이다. 각 컷이 enqueue 가능한지 사전 표시하고, 한 컷의 invalid prompt를 조용히 skip하여 “전체 생성”을 시작하지 않는다. 사용자는 문제 컷을 수정하거나 생성 대상을 단일 컷으로 좁힐 수 있다.

### 4.4 저장·실패·재시도 UX

- Baseline 저장 버튼은 서버 응답을 기다린다. 성공 전에 dialog를 닫지 않는다.
- 400/409/422/5xx가 발생하면 사용자 입력은 브라우저 draft로 보존되고, 실패 원인을 해당 필드 또는 작업 영역에서 보여준다.
- 한 번 실패한 save state가 이후 수정·재시도를 영구 차단해서는 안 된다.
- 서버 snapshot과 local draft를 구분한다. 저장되지 않은 값은 저장되었다고 표시하지 않는다.
- stream gap이나 stale snapshot이 감지되면 서버의 authoritative snapshot을 재조회하고, local draft는 폐기하지 않은 채 충돌을 명시한다. 릴리즈는 권위 상태가 복구되기 전까지 차단한다.

### 4.5 N-cut 전환의 사용자 의미

#### Phase 1 — creation-time N

- 프로젝트 생성 시 컷 수 `N >= 1`을 정한다.
- 기존 5컷 프로젝트는 `N=5`인 정상 사례로 보존한다.
- Phase 1에서는 생성 이후 membership과 order가 고정되지만, 숫자 5는 더 이상 제한이 아니다.
- 물리 식별 범위는 `cut_id >= 1`이며, `CHECK(cut_id BETWEEN 1 AND 5)`는 폐기된다.

#### Phase 2 — dynamic membership and order

- 컷의 stable identity와 `display_order`를 분리한다.
- 사용자는 컷을 추가하고, active set에서 제외하고, 재정렬할 수 있다.
- 재정렬은 cut identity, intent history, generation job ownership을 바꾸지 않는다.
- 제외된 컷은 물리 삭제나 ID 재사용 대신 비활성 membership으로 남아 과거 intent/job/artifact 귀속을 보존한다.
- active set/order 변경은 작품 closure를 바꾸므로 기존 review artifact의 currentness와 release authorization을 무효화한다.
- 추가된 active cut은 실현 전까지 작품 전체를 `UNRESOLVED`로 만든다.

### 4.6 캔버스·기하·fit 정책

Canonical surface는 다음 규칙을 따른다.

```text
W = 1024px
H = Σ slot_height(i) + (N - 1) × gap_px,  N >= 1
```

- `slot_height(i)`는 승인된 layout의 양의 정수 pixel 값이다. 기본값은 source aspect ratio를 폭 1024px에 맞춰 half-up rounding한 높이이며, 사용자가 명시적으로 조정한 높이는 새 composition revision으로 수용한다.
- slot은 ordered active set을 따라 위에서 아래로 누적한다. 이미 정수로 확정된 높이를 다시 N등분하지 않는다.
- backend와 frontend는 같은 resolved slot bounds를 사용한다. 각자 다른 나눗셈 공식을 재구현하지 않는다.
- 과거 backend cumulative division과 frontend `Math.floor`의 4px bottom drift는 허용되지 않는다. 마지막 slot bottom은 항상 정확히 `H`다.
- 기본 image fit은 backend와 frontend 모두 `contain`이다. `cover`는 명시적으로 수용된 per-cut fit/crop 정책일 때만 허용하며, 한쪽에서만 적용할 수 없다.
- 이미지 stretch는 금지한다.

### 4.7 컷 로컬 말풍선

말풍선의 권위 좌표는 다음과 같다.

```text
(cut_id, local_x_pct, local_y_pct, local_w_pct, local_h_pct)
```

각 percentage는 해당 컷 slot의 0…100 범위다. global pixel 좌표는 layout resolver가 파생하며 별도 권위로 저장하지 않는다.

- 컷 추가·삭제·재정렬 시 말풍선은 stable `cut_id`를 따라 이동하고 local 좌표를 보존한다.
- 일반 말풍선은 자기 컷 경계를 넘을 수 없다. 경계를 넘는 별도 연출 primitive가 미래에 필요하면 명시적인 다른 타입으로 정의한다.
- legacy global coordinates는 과거 slot의 pixel bounds를 먼저 복원한 뒤 local 좌표로 변환한다. gap 또는 다른 컷을 침범하는 legacy bubble을 임의 clamp하지 않고 수동 재배치 필요 상태로 남긴다.
- 기존 immutable artifact는 새 layout으로 자동 재렌더링하지 않는다.

### 4.8 이미지 생성 기본 모델

새 generation job의 기본 모델은 연결된 `oauth/gpt-image-2.5-flare`다. 연결되지 않은 `nano-banana-pro`는 기본값, 무언의 fallback 또는 성공 경로로 사용할 수 없다. 사용자가 명시적으로 다른 사용 가능한 모델을 선택한 경우에만 그 모델을 job identity에 결속한다.

---

## 5. Truth Architecture

### 5.1 다섯 진실

1. **Brief Truth**: 사용자의 원문 topic/synopsis와 AI draft가 구분되어 보존된다. AI 제안은 사용자 원문을 대체하거나 승인된 사실로 위장하지 않는다.
2. **Intent Truth**: 각 active cut에는 stable identity와 단 하나의 current desired revision이 있다. 사용자 prompt, LLM draft, intelligent default의 origin과 실제 generation에 사용된 effective prompt가 추적 가능하다.
3. **Realization Truth**: 최신 desired revision 및 최신 generation request sequence와 일치하는 결과만 canonical realization이 된다.
4. **Composition Truth**: ordered active set, slot heights, gap, fit, 컷 로컬 말풍선, 대사, 각 source asset identity가 하나의 canonical artifact closure로 실체화된다.
5. **Delivery Truth**: 승인된 artifact bytes와 목적지에서 readback된 content identity가 같을 때만 전달 성공이다.

### 5.2 권위 상태와 파생 상태

- **권위**: active Baseline, stable cuts, active membership/order, current desired revisions, request sequences, canonical realizations, accepted composition, immutable review artifact, release authorization, delivery observations.
- **파생**: UI progress, `Current/STALE`, aggregate completion, global canvas coordinates, preview thumbnails.
- **무권위**: 브라우저의 저장 전 draft, DOM 위치, 파일 존재만으로 추정한 currentness, queue empty, provider exit code만으로 추정한 성공.

클라이언트는 권위 상태를 투영하며 대체하지 않는다. 하나의 SQLite transaction authority를 유지할 수 있으나, 제품 계약은 특정 저장 엔진이 아니라 동일 원자성과 readback을 요구한다.

### 5.3 컷 currentness와 전체 completion

활성 ordered cut set을 `S = [i₁, …, iₙ]`, `n >= 1`이라 한다.

```text
Current(i) iff
    realized_revision(i) = desired_revision(i)
    AND realized_request_seq(i) = latest_generation_request_seq(i)
    AND latest request is successfully committed
    AND canonical asset identity/hash/readback is valid

RealizationComplete(S) iff
    S ≠ ∅
    AND ∀ i ∈ S: Current(i)
```

- prompt가 존재한다는 사실은 Current의 증거가 아니다.
- PNG 파일이 존재한다는 사실은 Current의 증거가 아니다.
- queue가 비었다는 사실은 Current의 증거가 아니다.
- 일부 컷만 Current면 해당 컷은 사용할 수 있지만 작품 전체는 Complete가 아니다.

### 5.4 Artifact closure와 release

Canonical Review Artifact는 최소한 다음 ordered closure에 결속한다.

- active set identity 및 display order.
- 각 cut의 desired/realized revision, request sequence, asset identity와 content hash.
- slot height, gap, fit과 전체 `(1024, H)`.
- 컷 로컬 bubble geometry, dialogue/text/style.
- composition revision과 renderer contract version.

```text
ReleaseReady(A, S) iff
    RealizationComplete(S)
    AND Closure(A) = CurrentClosure(S)
    AND A의 실제 bytes/hash/readback이 등록 identity와 일치
    AND A에 결속된 active Release Authorization이 존재
    AND 저장되지 않은 결과 영향 draft가 없음
```

release는 항상 active set 전체에 대해 all-or-nothing이다. 사용자가 탐색 중 일부 컷만 preview하는 것과 전체 작품을 release하는 것은 서로 다른 상태다.

### 5.5 성공의 권위 있는 readback

| 경계 | 성공 판정 |
| :--- | :--- |
| Draft Generated | OpenCodex 응답이 검증된 N컷 draft schema로 파싱되고 원문 brief 및 attempt provenance와 함께 반환됨 |
| Baseline Approved | ordered active set과 sparse/authored/default intent 상태가 하나의 authority mutation으로 fresh snapshot에서 조회됨 |
| Cut Enqueued | 대상 cut의 current desired revision과 새 request sequence에 결속된 job 및 실제 effective prompt/model identity가 조회됨 |
| Cut Realized | 동일 cut/revision/sequence candidate만 canonical asset으로 승격되고 실제 bytes/hash가 fresh readback과 일치함 |
| Realization Complete | 비어 있지 않은 active set 전부가 `Current(i)`이고 미완료 최신 요청이 없음 |
| Review Materialized | current ordered closure와 동일한 geometry/fit/text를 가진 immutable artifact bytes 및 hash가 조회됨 |
| Release Authorized | 사용자가 본 exact artifact hash와 closure에 결속된 active authorization이 조회됨 |
| PNG Exported | 목적지 파일을 다시 읽은 bytes/hash가 승인 artifact와 byte-identical함 |
| Blogger Confirmed | 원격 목적지의 실제 본문에서 artifact ID와 SHA-256 content identity가 readback됨 |

---

## 6. Failure & Recovery

### 6.1 Draft generation failure

- OpenCodex 연결 실패, timeout, rate limit, 5xx, malformed JSON 또는 schema mismatch는 `Draft Generation Failed`다.
- 시도한 model, 실패 종류와 retry/fallback 진행을 사용자에게 요약한다. 내부 stack trace나 비밀은 노출하지 않는다.
- 사용자의 원문 brief와 기존 draft는 보존한다.
- 사용자는 재시도하거나 수동 Baseline 작성으로 즉시 전환할 수 있다.
- 실패한 LLM 출력의 일부를 정상 draft로 자동 수용하지 않는다.

### 6.2 Baseline validation failure

- 빈 prompt는 실패가 아니다.
- 중복 cut identity/order, `N < 1`, 잘못된 타입, 불가능한 membership 참조는 구조 오류로 해당 필드에 표시한다.
- 서버 저장이 실패하면 dialog를 닫지 않고 local draft를 보존한다.
- conflict면 fresh authoritative snapshot과 local 변경을 함께 보여 주고 사용자가 재적용할 수 있게 한다.
- 예상 가능한 입력 부족을 일반 500이나 opaque toast로 축약하지 않는다.

### 6.3 Generation failure와 STOP

- provider 실패는 해당 job의 실패이며, 기존 canonical realization을 삭제하지 않는다.
- 새 intent 또는 재생성 요청으로 기존 픽셀이 stale이 된 경우 기존 이미지는 비교용으로 보존하되 `[STALE: 최신 의도 미실현]`을 표시한다.
- STOP/Cancel은 먼저 commit 자격을 철회하고 그 후 process를 종료한다.
- STOP 이후 늦게 도착한 candidate는 폐기한다.
- 이미 성공한 canonical result를 사후 Cancel이 `cancelled`로 왜곡하지 않는다.
- 재시도는 새 generation request sequence를 발급하는 명시적 사용자 행위다.

### 6.4 Composition·geometry failure

- slot height가 양수가 아니거나, bubble이 컷 경계를 벗어나거나, source/hash/font/geometry가 유효하지 않으면 전체 artifact materialization은 실패한다.
- 누락 컷을 skip하거나 stretch/crop/ellipsis로 성공을 꾸미지 않는다.
- backend/frontend layout 불일치가 감지되면 review/release를 차단하고 authoritative layout을 다시 불러온다.
- legacy global bubble을 안전하게 cut-local로 변환할 수 없으면 `REANCHOR_REQUIRED`로 표시하고 기존 artifact는 보존한다.

### 6.5 Delivery failure와 Unknown

- PNG export는 쓰기 후 목적지 bytes를 다시 읽어 hash를 확인하며, mismatch면 실패다.
- Blogger의 HTTP 200, URL 존재 또는 POST 응답만으로 성공을 확정하지 않는다.
- timeout·연결 단절·5xx처럼 원격 반영 여부를 알 수 없는 경우 `Unknown`으로 보존한다.
- `Unknown` reconciliation은 새 게시를 만들지 않고 기존 목적지를 readback한다.
- 잘못되거나 누락된 artifact marker는 confirmed success가 아니다.

### 6.6 재시작과 복구

- 재시작 후 authoritative state와 immutable assets에서 현재성을 재구성한다.
- 실행 중이던 job을 근거 없이 성공 또는 자동 재개로 만들지 않는다.
- local draft는 서버 truth와 분리해 보존한다.
- historical artifact와 retired cut history를 삭제해 현재 상태를 단순화하지 않는다.

---

## 7. Invariants

본 제품의 load-bearing causal invariant는 다음 네 가지다. “정확히 5컷”과 “모든 prompt 선입력”은 이 목록에 포함되지 않는다.

### INV-1. Monotonic Sequence CAS

- 각 stable cut의 accepted `desired_revision`과 `generation_request_seq`는 단조 증가한다.
- enqueue된 job은 `(cut_id, desired_revision, request_seq, model, effective_prompt identity)`에 결속한다.
- candidate commit은 동일한 권위 transaction에서 cut identity, current desired revision, latest request sequence, job/attempt의 commit eligibility를 모두 다시 검사한다.
- 하나라도 불일치하면 candidate를 폐기하고 기존 canonical asset과 history를 변경하지 않는다.
- 동일 revision의 재생성도 request sequence로 구분하므로 늦은 과거 결과가 최신 결과를 덮어쓸 수 없다.

### INV-2. STOP Pre-commit Lockout

- STOP/Cancel 수용은 process 종료보다 먼저 대상 job/attempt의 commit eligibility를 권위 transaction에서 철회한다.
- STOP 이후 도착한 candidate는 process가 실제로 종료되었는지와 무관하게 commit할 수 없다.
- 이미 성공한 job은 뒤늦은 Cancel로 실패 상태가 되지 않는다.
- STOP은 사용자의 accepted intent와 이전 canonical bytes를 삭제하지 않는다.

### INV-3. Atomic Approval Revocation

- release authorization은 immutable artifact hash 및 current ordered active-set closure에 결속한다.
- intent, generation request, accepted realization, active membership/order, slot height/gap/fit, bubble geometry/text/style 등 결과를 바꿀 수 있는 authoritative mutation이 수용되는 동일 transaction에서 기존 active authorization을 철회한다.
- 저장 전 draft와 의미가 동일한 no-op은 authorization을 철회하지 않지만, 저장되지 않은 결과 영향 draft가 존재하면 release를 차단한다.
- old authorization과 new authoritative content가 동시에 active인 관찰 가능한 상태는 존재할 수 없다.

### INV-4. Destination Content Readback

- 승인 hash와 일치한다고 검증한 바로 그 immutable bytes를 전달 payload로 사용한다.
- local export는 destination file readback으로 byte identity를 확인한다.
- 외부 전달의 `Confirmed Success`는 destination identity와 본문에 있는 artifact ID/content hash를 실제 readback했을 때만 기록한다.
- timeout·단절은 `Unknown`, 명백한 identity mismatch는 실패다.
- `Unknown`의 회복은 readback-only reconciliation이며 자동 재게시가 아니다.

### 7.5 불변식이 아닌 정책

다음은 중요한 제품 행동일 수 있으나 인과 안전 불변식으로 위장하지 않는다.

- 기본 컷 수.
- UI에서 한 번에 펼치는 필드 수.
- 컷 작성 순서.
- 먼저 생성하는 컷 번호.
- 고정 worker 수.
- 5컷이라는 전통적 포맷.

안전은 active set `S`와 각 구성원의 identity/currentness/closure에 의해 보장되며, `|S| = 5`에 의해 보장되지 않는다.

---

## 8. Counterexample Gates

각 Gate의 질문에 “가능”이라 답하는 구현은 제품 약속을 충족하지 못한다.

### Gate 1 — One-line Utility

**질문:** 사용자가 topic 또는 synopsis 한 줄을 입력했는데도 첫 스토리보드 초안을 얻기 전에 N개 컷의 role/beat/prompt/dialogue를 모두 수동 작성해야 하는가?  
**판정:** 불가능. 한 번의 draft generation으로 ordered cuts와 role/beat/dialogue/prompt 제안을 얻어야 한다. LLM 실패 시에도 원문 보존과 수동 경로가 있다.

### Gate 2 — Sparse Baseline

**질문:** Cut 1 prompt가 유효하거나 intelligent default로 resolve될 수 있는데 Cut 2…N의 prompt가 비어 있다는 이유로 Baseline 승인 또는 Cut 1 generation이 400으로 실패하는가?  
**판정:** 불가능. 빈 prompt는 Baseline에서 허용하며 non-empty 강제는 실제 enqueue 대상 컷에만 적용한다.

### Gate 3 — Empty Prompt Honesty

**질문:** 시스템이 빈 문자열을 provider에 보내거나, 어떤 prompt가 실제 사용되었는지 숨긴 채 default를 사용하고 성공이라 말할 수 있는가?  
**판정:** 불가능. enqueue 전에 대상 컷의 non-empty effective prompt와 origin을 확정하고 job identity에 결속한다.

### Gate 4 — N-cut Integrity

**질문:** N이 1, 2, 7이거나 Phase 2에서 컷이 재정렬되면 stale overwrite, job 오귀속 또는 artifact closure 혼동을 피하기 위해 5컷으로 되돌려야 하는가?  
**판정:** 불가능. stable cut identity, 별도 membership/order, per-cut CAS와 exact active-set closure로 동일한 무결성을 유지한다.

### Gate 5 — Honest Completion

**질문:** active set 중 일부만 생성되었는데 생성된 컷만 조용히 묶어 작품 전체를 Complete 또는 Release Ready로 표시할 수 있는가?  
**판정:** 불가능. `S ≠ ∅ ∧ ∀i∈S Current(i)`가 아니면 전체는 `UNRESOLVED`다.

### Gate 6 — Rounding Parity

**질문:** backend의 마지막 slot bottom은 `H`인데 frontend가 4px 위에서 끝나거나, 같은 accepted layout에 서로 다른 slot bounds를 사용할 수 있는가?  
**판정:** 불가능. 하나의 resolved integer layout을 양쪽이 공유하고 마지막 bottom은 정확히 `H`다.

### Gate 7 — Fit Parity

**질문:** frontend는 `cover`로 crop된 이미지를 보여주고 backend artifact는 `contain`으로 letterbox한 뒤 WYSIWYG라고 주장할 수 있는가?  
**판정:** 불가능. accepted fit policy는 양쪽에서 동일하며 기본은 `contain`이다.

### Gate 8 — Bubble Ownership

**질문:** 앞 컷 추가 또는 재정렬 후 말풍선이 global `y_pct` 위치에 남아 다른 컷 위에 놓일 수 있는가?  
**판정:** 불가능. 말풍선은 stable `cut_id`와 local coordinates를 소유한다.

### Gate 9 — Stale / Post-STOP Commit

**질문:** 더 최신 request가 수용되었거나 STOP이 수용된 뒤 늦은 candidate가 canonical pixels를 변경할 수 있는가?  
**판정:** 불가능. commit-time sequence CAS와 pre-commit lockout이 차단한다.

### Gate 10 — Approval Reuse

**질문:** 승인 후 대사 한 글자, slot height 1px, fit, cut order 또는 active membership을 바꾸고도 이전 authorization으로 전달할 수 있는가?  
**판정:** 불가능. 수용 mutation과 같은 transaction에서 authorization이 철회된다.

### Gate 11 — Phantom Delivery

**질문:** Blogger가 HTTP 200 또는 URL만 반환했는데 승인 artifact marker/hash를 목적지에서 읽지 못해도 성공으로 확정할 수 있는가?  
**판정:** 불가능. content-identity readback 전에는 실패 또는 Unknown이다.

### Gate 12 — Model Availability

**질문:** 기본 모델이 연결되지 않은 `nano-banana-pro`인 상태에서 생성 UI를 정상 경로라고 제시할 수 있는가?  
**판정:** 불가능. 기본은 live `oauth/gpt-image-2.5-flare`이며 실제 enqueue identity에도 그 값이 결속된다.

---

## 9. Open Product Meaning

### 9.1 현재 제품 의미의 완결성

현재 핵심 제품 의미에 대한 미해결 선택은 없다.

- 첫 유효 가치: 한 줄 brief에서 N컷 draft 제안.
- 작성 경계: sparse Baseline과 컷별 점진 생성.
- 완결 경계: 모든 active cuts Current.
- 조판 경계: width 1024px, dynamic height, 동일 integer layout/fit, cut-local bubbles.
- 안전 경계: 네 가지 causal invariant.
- 전달 경계: exact approved bytes와 destination content readback.
- 기본 provider/model: OpenCodex fallback chain과 `oauth/gpt-image-2.5-flare`.

따라서 결과는 `CALIBRATED`다. 이는 제품이 구현되었거나 검증되었다는 뜻이 아니라, 구현과 검증이 따라야 할 제품 의미가 현재 요청 범위에서 결정되었다는 뜻이다.

### 9.2 단계적 전환에서 고정된 의미

Phase 1과 Phase 2는 제품 약속의 축소·확대가 아니라 위험을 분리한 전환 단계다.

- Phase 1은 creation-time N을 제공하며 stable contiguous identity와 고정 membership/order를 유지한다.
- Phase 2는 stable identity를 유지한 채 membership/order를 분리하여 add/retire/reorder를 제공한다.
- 두 단계 모두 sparse generation, active-set completion, 네 불변식, dynamic canvas와 cut-local geometry를 동일하게 따른다.
- Phase 2가 완료되기 전 Phase 1 제품은 “작업 중 컷 추가·삭제·재정렬 가능”이라고 주장해서는 안 된다.

### 9.3 미래에만 열려 있는 비핵심 선택

다음은 현재 약속을 막지 않는 미래 확장 사항이다.

- provider/model을 사용자가 선택하는 고급 UI의 범위.
- 컷 경계를 넘는 연출 primitive의 별도 좌표 타입.
- 여러 활성 서사 branch 또는 협업 편집.
- 운영 환경별 최대 canvas pixel budget과 그에 따른 명시적 작품 크기 상한.

이 미래 항목은 임의 fallback, silent crop, partial release 또는 fixed-five 회귀를 정당화하지 않는다.
