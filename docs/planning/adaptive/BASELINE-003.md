# Transition Baseline BASELINE-003 — Web Comic Studio 가변 N컷 전환

Status: APPROVED  
Baseline-ID: BASELINE-003  
Revision: 1  
Project-Root: /home/user01/project/comic_new  
Meaning-Slug: web-comic-studio  
Applicability: THESIS-003의 한 줄 초안, sparse 점진 생성, 동적 조판, 가변 N컷 정본 전달을 안전하게 도입하는 전환  
Authored-On: 2026-09-17  
Language: ko  

---

## 1. Identity & Approval

### 1.1 Baseline Identity

- **Baseline-ID:** `BASELINE-003`
- **Status:** `APPROVED`
- **Meaning-Slug:** `web-comic-studio`
- **Project-Root:** `/home/user01/project/comic_new`
- **전환 범위:** `BLOCK-10`부터 `BLOCK-13`까지
- **승인 의미:** 이 문서는 `THESIS-003`의 제품 의미를 구현 가능한 안전 전이 경계로 분해한 승인된 Transition Baseline이다. 파일의 존재만으로 특정 Scope의 구현·검증·완료가 승인되지는 않는다.

### 1.2 Source Authority

본 Baseline의 유일한 제품 의미 권위는 다음 문서의 정확한 revision과 bytes다.

- **Normative Product Thesis:** `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md`
- **Thesis-Revision:** `THESIS-003`
- **SHA-256:** `d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268`

`THESIS-003`이 제품 목적, 사용자 약속, 상태·실패·회복 의미, 네 가지 인과 불변식과 성공 판정의 최상위 권위다. 본 문서는 그 의미를 강화·약화하거나 대체하지 않고, 서로 다른 위험을 안전하게 분리하는 Block 경계만 고정한다. 구현 편의를 이유로 `THESIS-003`의 active-set 완결성, exact closure, readback 또는 실패 정직성을 축소할 수 없다.

선행 `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-002.md`는 기존 안전 하드닝의 역사적 전이 기록이다. `BASELINE-003`은 이를 덮어쓰지 않는다. 다만 fixed-five, 모든 prompt 선입력, 고정 `1024×7680`, 전역 `y_pct`처럼 `THESIS-003`이 폐기한 의미는 현재 전환의 권위가 아니며, 충돌 시 언제나 위에 고정한 `THESIS-003`이 우선한다.

### 1.3 승인된 전환 결과

전환 완료 후 사용자는 한 줄 topic 또는 synopsis에서 검토 가능한 N컷 초안을 얻고, sparse Baseline을 승인한 뒤 원하는 한 컷부터 실제 live 모델로 탐색 생성할 수 있어야 한다. 편집 화면과 정본은 동일한 동적 integer layout, `contain` fit, 컷 로컬 말풍선 좌표를 사용해야 한다. 최종적으로 시스템은 `N >= 1`의 ordered active cut set을 안정된 identity와 분리된 membership/order로 관리하며, 모든 활성 컷이 Current인 exact closure만 승인·전달해야 한다.

---

## 2. Current State & Deficit

### 2.1 전환 시작 상태

`THESIS-003`의 진단과 제품 의미 개정에 따라 현재 전환은 다음 결손을 해결해야 한다. 이 목록은 구현 완료를 추정하지 않으며, 각 Block Scope는 진입 전에 해당 결정 앵커를 실제 코드·상태에서 다시 측정해야 한다.

1. **생성 경로 결손:** 기본 이미지 모델이 live 연결 경로가 아닌 `nano-banana-pro`를 가리킬 수 있어 정상 생성이 시작부터 실패할 수 있다.
2. **sparse 승인 결손:** 빈 prompt를 전체 Baseline의 구조 오류로 취급하는 과거 경로가 있어, 다른 컷이 준비되지 않았다는 이유로 유효한 단일 컷 탐색까지 HTTP 400으로 막힐 수 있다.
3. **초안 효용 결손:** 사용자가 첫 결과를 보기 전에 synopsis와 고정 5컷의 role/beat/prompt/dialogue를 수동으로 채워야 하며, 한 줄 의도를 OpenCodex N컷 제안으로 바꾸는 제품 경로가 없다.
4. **조판 기하 결손:** backend cumulative division과 frontend `Math.floor`가 서로 다른 slot bounds를 만들고 마지막 경계에 4px drift가 발생할 수 있다. frontend `cover`와 backend `contain` 불일치도 WYSIWYG를 깨뜨린다.
5. **말풍선 소유 결손:** 전역 surface의 `y_pct`에 결속된 말풍선은 컷 추가·비활성화·재정렬 때 원래 장면을 떠날 수 있다.
6. **고정 5컷 결손:** DB·API·renderer·frontend·release에 숫자 5가 구조 제약으로 반복되어 `N=1,2,7…`과 동적 membership/order를 안전하게 표현하지 못한다.

### 2.2 목표 상태와 결손 폐쇄 원칙

- 빈 prompt는 Baseline 승인 실패가 아니라 아직 사용자 prompt가 없는 유효 상태다.
- non-empty 조건은 실제 enqueue 대상 컷의 effective prompt를 확정하는 시점에만 적용한다.
- 단일 컷 생성 성공은 해당 컷만 Current로 만들며 전체 작품 완료를 뜻하지 않는다.
- 캔버스 높이와 slot bounds는 하나의 resolved integer layout에서 파생한다.
- 말풍선은 stable `cut_id`와 cut-local coordinates를 소유한다.
- 숫자 5를 제거해도 네 가지 인과 불변식과 active-set all-or-nothing release는 약화되지 않는다.
- 각 Block의 성공은 코드 존재나 테스트 통과만이 아니라 fresh authoritative readback과 사용자 관찰 가능한 결과로 판정한다.

---

## 3. Transition-Wide Causal Invariants

모든 Block은 다음 네 불변식을 시작 상태와 종료 상태에서 모두 보존해야 한다. Block 구현 중간 상태가 사용자 또는 후속 작업에 노출될 수 있다면 그 상태도 동일한 불변식을 만족해야 한다.

### INV-1. Monotonic Sequence CAS

각 stable cut의 `desired_revision`과 `generation_request_seq`는 단조 증가한다. 생성 job은 `(cut_id, desired_revision, request_seq, model, effective_prompt identity)`에 결속하고, candidate commit은 동일 권위 transaction 안에서 현재 revision, 최신 sequence와 commit eligibility를 다시 확인한다. 늦은 과거 결과는 canonical asset을 변경할 수 없다.

### INV-2. STOP Pre-commit Lockout

STOP/Cancel 수용은 process 종료보다 먼저 job/attempt의 commit 자격을 권위 transaction에서 철회한다. STOP 이후 candidate는 commit할 수 없고, 이미 성공한 canonical result는 늦은 Cancel로 실패 상태가 되지 않는다.

### INV-3. Atomic Approval Revocation

release authorization은 immutable artifact hash와 current ordered active-set closure에 결속한다. intent, generation request, realization, membership/order, geometry, fit, bubble/text/style처럼 결과를 바꿀 수 있는 mutation을 수용하는 동일 transaction에서 기존 authorization을 철회한다. 저장되지 않은 결과 영향 draft가 있으면 release를 차단한다.

### INV-4. Destination Content Readback

승인 hash와 일치하는 바로 그 immutable bytes만 전달한다. local export는 destination bytes를 다시 읽어 identity를 확인하고, 외부 전달 성공은 목적지 본문에서 artifact ID와 content hash를 실제 readback한 후에만 확정한다. timeout·단절은 `Unknown`이며 자동 재게시가 아니다.

### 3.1 공통 전이 규칙

1. 숫자 5, 모든 prompt 선입력, 작성 순서, 기본 컷 수는 안전 불변식으로 취급하지 않는다.
2. 저장소 migration, API, renderer, frontend projection과 release closure가 서로 다른 cardinality·order·geometry 의미를 동시에 사용하도록 부분 컷오버하지 않는다.
3. 권위 mutation과 이에 따른 currentness/authorization 무효화는 하나의 원자 경계를 유지한다.
4. 과거 immutable artifact와 retired cut history는 새 구조 도입을 이유로 재작성하거나 삭제하지 않는다.
5. Block 실패 시 이미 승인된 intent와 canonical bytes를 보존하고, 성공하지 않은 새 상태를 current 또는 complete로 표시하지 않는다.

---

## 4. Transition Blocks

```text
BLOCK-10  Live Model Repair & Sparse Baseline Approval
    ↓
BLOCK-11  OpenCodex Draft Generation & One-Click Studio UX
    ↓
BLOCK-12  Canvas Geometry Unification & Cut-Local Coordinates
    ↓
BLOCK-13A Creation-Time N-Cut
    ↓
BLOCK-13B Dynamic Membership / Display Order & Release Parity
    ↓
Clean Cutover
```

`BLOCK-13A`와 `BLOCK-13B`는 하나의 `BLOCK-13` 안에 있는 의무적 두 단계다. Phase 1을 안전하게 제공하더라도 Phase 2 완료 전에는 작업 중 add/retire/reorder가 가능하다고 주장하지 않는다.

### BLOCK-10 — Live Model Repair & Sparse Baseline Approval

- **Block-ID:** `BLOCK-10`
- **의존성:** `THESIS-003`에 결속된 현재 상태 측정

#### Goal

새 generation job의 기본 모델을 실제 연결된 `oauth/gpt-image-2.5-flare`에 결속하고, 빈 prompt를 허용하는 sparse Baseline 승인과 컷별 generation eligibility를 분리한다. 다른 컷의 준비 여부와 무관하게 한 컷을 탐색 생성할 수 있게 한다.

#### Bound Findings

- 연결되지 않은 `nano-banana-pro`를 기본값이나 무언의 fallback으로 사용하는 경로는 정상 제품 경로가 아니다.
- Baseline 승인 시 non-empty prompt를 일괄 강제하면 sparse 승인과 단일 컷 탐색을 모두 막는다.
- effective prompt가 비어 있는 상태로 provider에 보내는 것은 허용되지 않는다.
- 실제 생성 job은 사용된 model, effective prompt identity와 origin을 추적해야 한다.

#### Scope Invariants

1. Baseline 승인에서는 빈 prompt, 일부 컷만 작성된 prompt와 빈 dialogue를 허용한다.
2. 선택한 컷의 enqueue 직전에만 non-empty effective prompt를 resolve하고 검증한다.
3. origin 우선순위는 사용자 non-empty prompt 보존을 최우선으로 하고 `user`, `llm_draft`, `intelligent_default`를 숨기지 않는다.
4. 다른 컷의 prompt·dialogue·realization 상태는 단일 컷 enqueue eligibility에 영향을 주지 않는다.
5. enqueue는 기존 INV-1 tuple에 `oauth/gpt-image-2.5-flare`와 실제 effective prompt identity를 결속한다.
6. 부분 생성은 전체 completion이나 release readiness를 만들지 않는다.

#### Non-Goals

- OpenCodex를 이용한 전체 storyboard draft 생성 UI.
- canvas geometry 또는 말풍선 좌표 migration.
- creation-time N 및 dynamic membership/order.
- 사용자용 고급 provider/model 선택 UI.
- provider 실패를 다른 모델의 무언 fallback으로 숨기는 동작.

#### Observable Success

1. prompt가 모두 비어 있거나 일부만 채워진 `N >= 1` Baseline이 HTTP 400 없이 승인되고, fresh snapshot에서 동일 ordered structure와 prompt 상태가 조회된다.
2. Cut 1의 prompt가 유효하거나 intelligent default로 resolve 가능한 상태에서 Cut 2…N이 비어 있어도 Cut 1만 enqueue된다.
3. enqueue된 job readback에 non-empty effective prompt, origin, `oauth/gpt-image-2.5-flare`, current desired revision과 신규 request sequence가 함께 나타난다.
4. resolve 후에도 대상 컷 prompt가 유효하지 않으면 그 컷만 거절되고, Baseline과 다른 컷 작업은 유지된다.
5. provider 경계에서 empty string이 관찰되지 않으며, 단일 컷 성공 후에도 미실현 active cut이 있으면 전체 상태는 `UNRESOLVED`다.

#### Counterexample Blockers

- 빈 prompt 하나 때문에 Baseline 전체가 400으로 실패한다.
- 다른 컷의 빈 prompt 때문에 준비된 한 컷 enqueue가 실패한다.
- empty prompt가 provider로 전달되거나 실제 사용 prompt/origin을 readback할 수 없다.
- 기본 enqueue model이 `nano-banana-pro`이거나 live 모델 실패를 그 값으로 무언 대체한다.
- 한 컷 생성 후 전체 작품을 Complete 또는 Release Ready로 표시한다.

#### Entry, Atomic Boundary, Readback & Continuation

- **Entry:** 현재 model default, Baseline validation 경계, effective prompt resolution과 enqueue tuple을 실제 상태에서 측정한다.
- **Atomic Boundary:** Baseline 승인 mutation과 컷별 enqueue mutation을 분리한다. enqueue mutation은 effective prompt/model/revision/sequence/job identity를 함께 확정한다.
- **Authoritative Readback:** 승인 snapshot과 생성 job/attempt의 저장된 identity를 fresh 조회하고 실제 provider 요청 경계와 대조한다.
- **Abort:** 승인 실패 시 local draft를 보존한다. 생성 실패는 대상 job에만 기록하고 기존 canonical realization을 보존한다.
- **Safe Continuation:** Observable Success 전항과 Counterexample Blocker 부재가 증명된 뒤 `BLOCK-11`로 이동한다.

---

### BLOCK-11 — OpenCodex Draft Generation & One-Click Studio UX

- **Block-ID:** `BLOCK-11`
- **의존성:** `BLOCK-10`

#### Goal

`POST /api/baselines/generate-draft`와 OpenCodex fallback chain을 제공하고, 최초 Studio의 주 작업을 한 줄 topic/synopsis와 한 번의 초안 생성으로 바꾼다. 생성 결과는 편집 가능한 제안이며 자동 승인이나 자동 이미지 생성이 아니다.

#### Bound Findings

- API는 topic 또는 synopsis와 선택적 목표 컷 수를 받아 `N >= 1`의 ordered draft cuts를 반환해야 한다.
- endpoint는 `http://127.0.0.1:10100/v1`이며 fallback 정책은 `THESIS-003`에 고정되어 있다.
- 최초 UI에서 N개 컷의 role/beat/prompt/dialogue를 모두 펼치는 방식은 한 줄 효용 약속을 충족하지 못한다.
- malformed 또는 부분 LLM 출력은 정상 draft로 보정할 수 없다.

#### Scope Invariants

1. Primary는 `google-antigravity/gemini-3.8-flash`, reasoning `high`, 45초 read timeout이다.
2. Primary의 `429` 또는 `5xx`만 최대 1회 재시도하고, 실패하면 `gpt-5.6-luna`, reasoning `max`, 90초 read timeout으로 이동한다.
3. fallback의 `429` 또는 `5xx`도 최대 1회 재시도하며 전체 wall-clock budget은 150초다.
4. 검증된 JSON object만 draft가 되며 ordered cuts의 stable draft identity, display order, role, beat, dialogue intent, self-contained prompt와 attempt provenance를 포함한다.
5. 원문 brief와 기존 draft는 성공·실패 모두에서 보존한다.
6. draft generation은 Baseline approval, generation enqueue 또는 기존 authority mutation을 암묵적으로 수행하지 않는다.
7. 수동 Baseline 작성은 동등한 회복·진입 경로로 남는다.

#### Non-Goals

- AI 제안을 자동 승인하거나 즉시 이미지 생성하는 흐름.
- malformed JSON의 추측 기반 자동 수선.
- 무한 retry 또는 명시되지 않은 모델 fallback.
- dynamic membership/order 편집.
- draft 생성 성공만으로 작품 completion을 선언하는 동작.

#### Observable Success

1. 최초 화면에서 한 줄 topic/synopsis와 선택적 컷 수만으로 `스토리보드 초안 만들기`를 실행할 수 있다.
2. 성공 응답은 `N >= 1` ordered cuts와 필수 필드·provenance를 포함하고, 각 필드를 사용자가 편집한 뒤 별도로 승인할 수 있다.
3. primary 성공, primary retry 후 성공, fallback 성공과 양 모델 최종 실패 경로에서 실제 attempt 순서·timeout·budget이 정책과 일치한다.
4. malformed JSON, 누락 필드, 중복 identity/order는 성공 draft가 되지 않는다.
5. LLM 실패 후에도 원문과 기존 편집값이 남고 즉시 재시도 또는 수동 작성이 가능하다.
6. 저장 요청은 서버 응답 전 dialog를 닫지 않으며 400/409/422/5xx 후 수정·재시도가 가능하다.

#### Counterexample Blockers

- 한 줄 입력 뒤에도 초안을 보기 전에 모든 컷 필드를 수동 입력해야 한다.
- 실패한 LLM 출력 일부가 정상 draft 또는 승인 상태로 표시된다.
- fallback chain, retry 횟수 또는 150초 budget이 무시된다.
- draft 생성이 기존 Baseline을 변경하거나 generation을 시작한다.
- 실패 후 원문/local draft가 사라지거나 UI가 영구적으로 저장 불가 상태가 된다.

#### Entry, Atomic Boundary, Readback & Continuation

- **Entry:** `BLOCK-10`의 sparse approval과 단일 컷 generation이 독립적으로 동작함을 readback한다.
- **Atomic Boundary:** draft는 authority 밖의 제안 상태다. 사용자의 별도 Baseline 승인 mutation만 ordered active structure를 권위 상태로 만든다.
- **Authoritative Readback:** draft schema/provenance를 API 응답에서 확인하고, 승인 후에는 server의 fresh Baseline snapshot으로만 저장 성공을 판정한다.
- **Abort:** timeout, 연결 실패, rate limit, 5xx, malformed/schema mismatch는 정직한 `Draft Generation Failed`이며 기존 권위 상태를 변경하지 않는다.
- **Safe Continuation:** one-line utility와 실패 회복 전항을 만족한 뒤 `BLOCK-12`로 이동한다.

---

### BLOCK-12 — Canvas Geometry Unification & Cut-Local Coordinates

- **Block-ID:** `BLOCK-12`
- **의존성:** `BLOCK-11`

#### Goal

canonical width 1024px과 동적 높이 `H = Σ slot_height(i) + (N - 1) × gap_px`를 사용하는 하나의 resolved integer layout을 backend와 frontend가 공유하게 한다. 4px rounding drift와 fit 불일치를 제거하고 말풍선 권위를 stable cut의 로컬 좌표로 전환한다.

#### Bound Findings

- 이미 확정된 integer slot height를 다시 N등분하면 frontend/backend 경계가 달라질 수 있다.
- 마지막 slot bottom은 항상 정확히 `H`여야 한다.
- 기본 image fit은 양쪽 모두 `contain`이며 stretch는 금지된다.
- global `y_pct`는 membership/order 변화에서 말풍선 소유를 보존하지 못한다.
- legacy global bubble은 과거 slot bounds를 복원할 수 있을 때만 안전하게 변환할 수 있다.

#### Scope Invariants

1. `W = 1024px`, `N >= 1`, 각 `slot_height(i)`는 양의 정수다.
2. 기본 slot height는 source aspect ratio를 1024px 폭에 맞춰 half-up rounding하고, 사용자가 수용한 높이는 새 composition revision이다.
3. ordered active set을 따라 integer bounds를 누적하며 마지막 bottom은 정확히 `H`다.
4. backend와 frontend는 같은 resolved bounds를 소비하고 서로 다른 division 공식을 재구현하지 않는다.
5. 기본 fit은 `contain`이다. `cover`는 명시적으로 수용된 per-cut fit/crop 정책으로 양쪽에 동일하게 결속된 경우만 가능하다.
6. 말풍선 권위는 `(cut_id, local_x_pct, local_y_pct, local_w_pct, local_h_pct)`이며 각 값은 해당 slot의 0…100 범위다.
7. geometry, fit, bubble/text/style mutation은 INV-3에 따라 기존 release authorization을 원자적으로 철회한다.

#### Non-Goals

- 컷 경계를 넘는 별도 연출 primitive.
- 과거 immutable artifact의 자동 재렌더링.
- 안전하게 귀속할 수 없는 legacy bubble의 임의 clamp.
- 운영 환경별 최대 canvas pixel budget 결정.
- dynamic membership/order 자체의 사용자 동작.

#### Observable Success

1. `N=1,2,5,7`과 비균등 slot heights에서 backend/frontend가 동일한 각 slot `(top,bottom,height)`를 사용하고 마지막 bottom이 `H`와 일치한다.
2. 과거 4px bottom drift가 재현되지 않는다.
3. 같은 source와 accepted layout에서 preview와 materialized artifact의 crop/letterbox 결과가 동일한 `contain` 의미를 보인다.
4. stretch 또는 한쪽만의 `cover`가 발생하면 materialization/release가 차단된다.
5. 컷 재배치를 모사해도 변환된 말풍선은 stable `cut_id`와 local coordinates를 유지한다.
6. 안전한 legacy 좌표는 복원된 과거 slot bounds를 통해 local 좌표로 변환되고, gap/다른 컷을 침범하는 항목은 `REANCHOR_REQUIRED`가 되어 임의 이동되지 않는다.
7. geometry closure가 artifact의 size, bounds, fit, bubble geometry와 함께 fresh readback된다.

#### Counterexample Blockers

- backend bottom은 `H`인데 frontend가 4px 위에서 끝난다.
- preview는 `cover`, 정본은 `contain`인데 WYSIWYG로 표시한다.
- 이미지가 slot을 채우기 위해 stretch된다.
- 말풍선의 권위 위치가 global surface percentage로 남는다.
- 안전하지 않은 legacy bubble을 임의 clamp하거나 다른 컷에 귀속한다.
- geometry 변경 후 이전 release authorization이 active로 남는다.

#### Entry, Atomic Boundary, Readback & Continuation

- **Entry:** 현재 backend/frontend bounds, fit, legacy bubble 저장 형태와 artifact closure를 실측한다.
- **Atomic Boundary:** accepted layout revision은 ordered slot bounds, gap, fit과 cut-local bubble geometry를 하나의 composition closure로 갱신하고 이전 authorization을 같은 transaction에서 철회한다.
- **Authoritative Readback:** frontend DOM 위치가 아니라 accepted resolved layout과 immutable artifact bytes/hash/closure를 대조한다.
- **Abort:** invalid height, out-of-bounds bubble, source/hash/font/geometry 불일치는 전체 materialization 실패다. 누락 컷 skip, crop, stretch, ellipsis로 성공을 꾸미지 않는다.
- **Safe Continuation:** geometry/fit parity와 legacy coordinate 분류가 증명된 뒤 `BLOCK-13`으로 이동한다.

---

### BLOCK-13 — N-Cut Dynamic Architecture & Cutover

- **Block-ID:** `BLOCK-13`
- **의존성:** `BLOCK-12`
- **내부 단계:** Phase 1 `BLOCK-13A` → Phase 2 `BLOCK-13B`

#### Goal

Phase 1에서 프로젝트 생성 시 `N >= 1`을 허용하도록 fixed-five schema와 전 계층 가정을 제거하고, Phase 2에서 stable cut identity와 active membership/display order를 분리해 add/retire/reorder를 안전하게 제공한다. 두 단계 모두 active-set completion, exact artifact closure와 release parity를 유지한다.

#### Bound Findings

- `CHECK(cut_id BETWEEN 1 AND 5)`와 DB·API·renderer·frontend·release의 숫자 5 반복은 제품 안전 조건이 아니다.
- stable identity와 display order를 같은 값으로 취급하면 재정렬이 intent history와 generation ownership을 훼손한다.
- active set/order 변경은 composition closure를 바꾸므로 기존 review artifact currentness와 release authorization을 무효화한다.
- retired cut은 물리 삭제나 ID 재사용 없이 history 귀속을 보존해야 한다.

#### Scope Invariants

1. **Phase 1:** 프로젝트 생성 시 `N >= 1`; `cut_id >= 1`; 기존 5컷 프로젝트는 정상 `N=5` 사례로 보존한다.
2. **Phase 1:** 생성 후 membership/order는 고정이지만 숫자 5는 DB/API/UI/renderer/release 제한이 아니다.
3. **Phase 2:** stable `cut_id`, active membership와 `display_order`를 분리한다. display order 변경은 cut identity, desired revision, job와 artifact history ownership을 변경하지 않는다.
4. 제외된 컷은 inactive membership으로 남고 physical identity를 재사용하지 않는다.
5. active set은 항상 비어 있지 않으며 order와 membership 참조는 유일하고 유효해야 한다.
6. active membership/order mutation은 같은 transaction에서 기존 review artifact currentness와 release authorization을 철회한다.
7. 새 active cut은 Current가 되기 전까지 전체를 `UNRESOLVED`로 만든다.
8. `RealizationComplete(S)`와 `ReleaseReady(A,S)`는 `|S|=5`가 아니라 정확한 current ordered active set `S`를 사용한다.
9. release는 active set 전체에 대해 all-or-nothing이며 retired/inactive cut을 조용히 포함하거나 미실현 active cut을 제외하지 않는다.

#### Non-Goals

- multiple active story branches.
- cut identity 재번호화 또는 retired ID 재사용.
- historical intent/job/artifact 삭제.
- partial active-set release.
- Phase 2 완료 전 add/retire/reorder 가능하다는 UI 또는 문서 주장.
- 협업 편집이나 범용 version control.

#### Observable Success

**Phase 1 — Creation-Time N**

1. `N=1,2,5,7` 프로젝트가 생성되고 동일한 Baseline 승인, sparse generation, dynamic geometry, completion 및 release 규칙을 사용한다.
2. 기존 `N=5` 프로젝트의 stable identity, intent/job/artifact history와 currentness가 migration 전후 보존된다.
3. DB/API/UI/renderer/release의 사용자 도달 경로에 정확히 5컷을 요구하는 제약이 남지 않는다.
4. 일부 active cuts만 Current면 전체는 `UNRESOLVED`이며 release가 차단된다.

**Phase 2 — Dynamic Membership & Display Order**

5. cut 추가, inactive 전환, reorder 후에도 기존 cut의 stable identity, revisions, request sequences, job와 historical artifact 귀속이 보존된다.
6. reorder 뒤 frontend, renderer와 release closure가 하나의 `display_order`를 사용하고 cut-local bubble이 원래 cut을 따라 이동한다.
7. membership/order 변경과 동시에 이전 review artifact/authorization이 current가 아니게 되며, old authorization으로 전달할 수 없다.
8. 새 active cut이 미실현이면 전체가 `UNRESOLVED`이고, inactive cut은 current active closure에서 제외되지만 history에는 남는다.
9. 모든 active cuts가 Current인 뒤 새 exact closure로 materialize·review·authorize한 artifact만 PNG/Blogger 전달이 가능하고 destination identity readback까지 유지된다.

#### Counterexample Blockers

- `N=1,2,7`이 schema, API, UI, renderer 또는 release에서 5컷 가정 때문에 실패한다.
- reorder가 `cut_id`를 바꾸거나 intent/job/history를 다른 장면에 귀속한다.
- retired cut을 삭제하거나 ID를 새 cut에 재사용한다.
- active membership/order 변경 뒤 old artifact 또는 authorization으로 release할 수 있다.
- 일부 active cuts만 Current인데 이를 제외하고 전체 작품을 Complete로 표시한다.
- Phase 2 미완료 상태에서 동적 편집을 지원한다고 표시한다.
- release closure와 화면 order 또는 renderer order가 다르다.

#### Entry, Atomic Boundary, Readback & Continuation

- **Entry:** 숫자 5가 존재하는 schema, API validation, iteration, UI rendering, geometry, completion, artifact closure와 release 경계를 모두 식별한다. 단순 소스 문자열이 아니라 도달 가능한 동작을 기준으로 한다.
- **Phase 1 Atomic Boundary:** project creation에서 N개의 stable cuts와 초기 ordered membership을 하나의 authority mutation으로 만든다. 실패 시 부분 프로젝트/부분 cut set을 current로 남기지 않는다.
- **Phase 1 Handoff:** creation-time N의 전 계층 parity가 증명된 뒤에만 Phase 2 schema와 사용자 동작을 노출한다.
- **Phase 2 Atomic Boundary:** add/retire/reorder, closure currentness 변경과 authorization 철회를 하나의 transaction에서 수행한다.
- **Authoritative Readback:** fresh active membership/order, per-cut identity/revision/sequence, currentness, artifact closure와 release authorization을 함께 조회한다.
- **Abort:** migration 또는 mutation 불일치 시 기존 authoritative project와 immutable history를 보존한다. 부분 변환 상태를 current로 승격하지 않는다.
- **Safe Continuation:** Phase 1과 Phase 2 Observable Success 전항, Counterexample Blocker 부재, §6 Clean Cutover를 모두 충족한 뒤 전환 완료를 판정한다.

---

## 5. Block Dependency Matrix

| Block | 필수 선행 상태 | 생성하는 권위 경계 | 후속 Block에 넘기는 증거 | 단독 롤백/중단 경계 |
| :--- | :--- | :--- | :--- | :--- |
| `BLOCK-10` | THESIS-003 결속 및 현재 model/validation/enqueue 측정 | sparse Baseline 승인과 컷별 effective prompt/model-bound enqueue 분리 | sparse 승인 snapshot, single-cut job tuple, live model provider observation | 기존 Baseline과 canonical bytes 보존; 실패 job만 격리 |
| `BLOCK-11` | `BLOCK-10` exit 충족 | draft 제안과 Baseline authority mutation의 명시적 분리 | 검증된 N컷 draft/provenance, 실패 보존, 승인 후 fresh snapshot | 기존 authority 무변경; 원문/local draft 보존 |
| `BLOCK-12` | `BLOCK-11` exit 및 active cuts 투영 가능 | shared integer layout, fit, cut-local bubble closure | backend/frontend bounds parity, artifact geometry readback, legacy 변환 분류 | 과거 artifact 보존; invalid composition 전체 거절 |
| `BLOCK-13A` | `BLOCK-12` exit | creation-time `N >= 1`과 전 계층 cardinality parity | N=1/2/5/7 authoritative projects와 exact active-set completion evidence | 기존 N=5 projects와 history 보존; 부분 생성 거절 |
| `BLOCK-13B` | `BLOCK-13A` exit | stable identity와 active membership/display order 분리 | add/retire/reorder identity 보존, authorization 철회, release closure parity | 부분 membership mutation 거절; old closure current 승격 금지 |

### 5.1 의존성 해석

- 의존성은 단순 구현 순서가 아니라 후속 Block이 소비하는 의미 경계다.
- 후속 Block은 선행 Block의 파일 존재나 테스트 라벨이 아니라 Exit evidence와 fresh authoritative readback을 소비한다.
- 선행 Block 결과가 drift했거나 네 불변식 중 하나를 위반하면 후속 Block을 진행하지 않고 영향을 받은 Block 경계로 돌아가 다시 측정한다.
- Block을 묶어 한 번에 구현할 수 있더라도 acceptance와 readback은 각 Block 경계별로 구분해 남긴다.

---

## 6. Measurement & Acceptance

### 6.1 공통 측정 원칙

1. **권위 상태를 직접 읽는다:** 브라우저 draft, DOM 위치, queue empty, 파일 존재, provider exit code만으로 성공을 판정하지 않는다.
2. **행동과 readback을 함께 측정한다:** mutation 응답뿐 아니라 fresh server snapshot, job tuple, artifact bytes/hash, destination content identity를 해당 경계에서 확인한다.
3. **반례를 실제로 차단한다:** 정상 경로만 통과한 결과는 충분하지 않다. 각 Block의 Counterexample Blocker를 도달 가능한 사용자·API·worker·renderer·release 경계에서 판별한다.
4. **부분 성공을 전체 성공으로 올리지 않는다:** 한 컷, 한 레이어, 한 renderer 또는 한 delivery adapter의 성공은 전체 Block exit가 아니다.
5. **기존 안전을 재검증한다:** 모든 Block에서 INV-1~INV-4가 그대로 작동함을 영향을 받은 경계에 대해 판별한다.

### 6.2 필수 Acceptance Matrix

| 측정 경계 | 필수 관찰 | 실패 판정 |
| :--- | :--- | :--- |
| Live Model | 새 default job의 model identity와 실제 provider 요청이 `oauth/gpt-image-2.5-flare`로 일치 | 연결되지 않은 기본값, 무언 fallback, identity 불일치 |
| Sparse Baseline | empty/partial prompt Baseline 승인 후 fresh ordered snapshot | empty prompt로 400 또는 저장 성공 전 UI 종료 |
| Per-Cut Eligibility | 다른 컷이 비어 있어도 선택 컷의 non-empty effective prompt/origin/revision/sequence job 조회 | 전체 컷 선입력 요구, empty provider prompt, 타 컷 연쇄 차단 |
| Draft Generated | OpenCodex 응답이 검증된 N컷 schema와 brief/attempt provenance로 반환 | malformed/partial output 성공 처리, 권위 상태 자동 변경 |
| Draft Failure Recovery | 원문과 기존 draft가 보존되고 수동 경로·재시도가 가능 | 입력 유실, 무한 retry, UI 영구 잠금 |
| Layout Parity | 동일 accepted integer bounds와 `last.bottom = H`를 backend/frontend에서 확인 | 4px drift, 분리 계산, non-positive slot |
| Fit Parity | preview와 artifact가 동일 accepted fit, 기본 `contain` | silent crop, stretch, 한쪽만 `cover` |
| Bubble Ownership | stable `cut_id`와 local coordinates 보존, unsafe legacy는 `REANCHOR_REQUIRED` | global 위치 잔존, 타 컷 이동, 임의 clamp |
| Creation-Time N | N=1/2/5/7의 schema/API/UI/renderer/release parity | fixed-five 제약 또는 기존 N=5 history 훼손 |
| Membership/Order | add/retire/reorder 후 stable identity/history와 display order readback | 재번호화, ID 재사용, closure/order 불일치 |
| Completion | `S ≠ ∅ ∧ ∀i∈S Current(i)`일 때만 complete | partial active set을 전체 완료로 표시 |
| Approval Revocation | 결과 영향 mutation과 같은 transaction에서 old authorization 비활성 | old authorization과 new content 동시 active |
| Release Closure | exact ordered active-set closure와 immutable artifact bytes/hash 일치 | inactive 포함, 미실현 active 누락, stale artifact 전달 |
| Destination Truth | PNG destination byte readback 및 Blogger marker/hash readback | HTTP 200/URL/파일 존재만으로 성공 확정 |
| STOP/Currency Regression | stale 또는 post-STOP candidate commit 0건 | 늦은 결과가 canonical pixels 변경 |

### 6.3 Block Acceptance Rule

각 Block은 다음 조건을 모두 만족할 때만 `Accepted for Safe Continuation`이다.

- 해당 Block의 Goal이 사용자 관찰 가능한 결과로 충족된다.
- Bound Findings 각각이 구현 경계 또는 명시적 실패 상태로 처리된다.
- Scope Invariants와 전역 INV-1~INV-4 위반이 없다.
- Observable Success 전항의 fresh evidence가 있다.
- Counterexample Blocker가 하나도 재현되지 않는다.
- atomic boundary, abort와 authoritative readback이 실제 경로에서 판별된다.
- 후속 Block이 소비할 handoff evidence가 정확한 current revision에 결속되어 있다.

테스트 스위트 통과, endpoint 존재, schema column 존재 또는 UI 표시만으로 위 조건을 대체할 수 없다.

### 6.4 Clean Cutover Criteria

`BASELINE-003` 전환 완료는 다음이 모두 충족될 때만 선언한다.

1. `BLOCK-10`~`BLOCK-13`이 순서대로 Accepted for Safe Continuation이며 `BLOCK-13A`와 `BLOCK-13B`가 모두 완료됐다.
2. 새 권위 경로의 모든 caller가 sparse intent, live model, shared layout, cut-local bubble, active membership/order 의미를 사용한다.
3. Baseline 승인 경계의 non-empty 일괄 강제, `nano-banana-pro` 기본값, fixed-five validation/iteration, 독립적인 frontend/backend slot 계산과 global bubble authority가 사용자 도달 경로에서 제거됐다.
4. 호환 alias, 이중 쓰기, 숨은 fallback 또는 legacy/new 동시 권위 경로가 남아 있지 않다. legacy data는 명시적 migration/read-only history로만 존재한다.
5. 기존 N=5 projects와 immutable artifacts는 identity와 history를 보존하며, 새 renderer 의미로 조용히 재작성되지 않는다.
6. active membership/order 또는 composition 변화 후 과거 artifact/authorization이 release에 재사용되지 않는다.
7. 모든 active cuts가 Current인 exact ordered closure만 새 canonical review artifact와 release authorization을 얻는다.
8. PNG와 Blogger 전달이 승인 artifact의 exact bytes/content identity readback으로 끝난다.
9. stale request, post-STOP candidate, partial active set, geometry/fit mismatch와 destination phantom success가 모두 차단된다.
10. 최종 fresh authoritative readback이 brief → Baseline → per-cut intent/job/realization → composition closure → artifact → authorization → destination observation의 동일 identity chain을 보인다.

하나라도 충족되지 않으면 결과는 전환 완료가 아니라 해당 Block의 미완료 또는 차단 상태다. 더 작은 성공을 전체 제품 성공으로 선언하지 않는다.

---

## 7. Open Decisions

### 7.1 현재 전환을 막는 미결정 사항

- **없음 (None).**

`THESIS-003`이 다음을 이미 고정했다: 한 줄 OpenCodex draft, fallback chain, sparse Baseline, 컷별 generation, 기본 이미지 모델 `oauth/gpt-image-2.5-flare`, width 1024px과 동적 height, shared integer layout, 기본 `contain`, cut-local bubbles, Phase 1 creation-time N, Phase 2 dynamic membership/order, active-set completion과 네 가지 인과 불변식.

### 7.2 비차단 미래 선택

다음은 본 전환의 완료를 막지 않으며, 현재 Block에서 임의로 결정하지 않는다.

- provider/model을 사용자가 선택하는 고급 UI 범위.
- 컷 경계를 넘는 별도 연출 primitive의 좌표 타입.
- 여러 활성 서사 branch 및 협업 편집.
- 운영 환경별 최대 canvas pixel budget과 명시적 작품 크기 상한.

이 항목들은 live 기본 모델, exact fallback chain, `contain` parity, active-set all-or-nothing release 또는 destination readback을 우회하는 근거가 아니다.

---

## 8. Final Transition Declaration

`BASELINE-003`은 `THESIS-003`에 엄격히 결속된 승인된 전이 계약이다. 즉시 선택 가능한 다음 경계는 `BLOCK-10`의 현재 상태 측정과 Scope 확정이다. 이 문서의 `APPROVED` 상태는 네 Block의 구현 완료나 제품 검증 완료를 뜻하지 않는다. 완료 선언은 §6.4의 Clean Cutover Criteria를 실제 권위 상태와 관찰 가능한 사용자 경로에서 모두 충족한 뒤에만 가능하다.
