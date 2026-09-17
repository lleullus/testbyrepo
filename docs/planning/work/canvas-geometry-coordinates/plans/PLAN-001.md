# PLAN-001 — BLOCK-12 Canvas Geometry Unification 및 Cut-Local Coordinates

## 1. 결속된 권위와 실행 경계

- Project Root: `/home/user01/project/comic_new`
- Scope: `/home/user01/project/comic_new/docs/planning/work/canvas-geometry-coordinates/SCOPE.md` (sha256 `007b9ee982569cec6be911e3306f6c74b7584bee9fbeea4a61637dd86880704e`, `Schema: iis-scope/v1`, `Status: ready`)
- Normative Thesis: `/home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md` (`THESIS-003`, sha256 `d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268`)
- Transition Authority: `/home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md` (sha256 `59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51`, selected `BLOCK-12`)
- Repository investigation: 별도 불변 investigation artifact는 제공되지 않았다. 이 Plan은 위 원본과 현재 source/test bytes를 직접 조사한 결과에 결속한다.
- Scope validator: canonical `scope-shaper/tools/validate_scope.py --json`은 `iis-scope/v1`, `status: ready`, 위 Thesis/Transition path 및 digest의 정확한 일치를 반환했다.
- 허용 범위: 현재 조판의 정수 slot resolver, `contain` fit, composition JSON/API/frontend의 cut-local bubble 좌표, 기존 v1 composition migration, artifact closure/readback 및 이에 직접 관련된 테스트만 변경한다.
- 제외 범위: BLOCK-13의 creation-time N 저장 구조, active membership/add/retire/reorder DDL과 UI, 새 폰트 엔진, 과거 immutable artifact 재렌더링, 컷 경계를 넘는 연출 primitive는 시작하지 않는다.
- 증거 경계: Python/TypeScript unit test와 synthetic PNG는 수식·직렬화·PIL pixel 결과를 판별하는 보조 증거다. 실제 WYSIWYG 성공은 동일 accepted composition snapshot에서 나온 frontend preview와 materialized PNG의 slot/letterbox/bubble 위치를 실제 브라우저 및 artifact bytes에서 함께 관찰해야 한다. DOM 위치만, 파일 존재만, 테스트 통과만으로 acceptance를 대체하지 않는다.

## 2. 달성할 관찰 결과와 보존 조건

동일한 accepted composition은 backend와 frontend에서 하나의 정수 layout으로 해석된다. 각 slot은 `(cut_id, top_px, bottom_px, height_px)`를 가지며, `top_px`/`bottom_px`는 정수이고 `height_px > 0`이다. gap을 포함한 전체 높이는 `H = Σ slot_height_px + (N - 1) × gap_px`이며 마지막 slot의 `bottom_px`는 정확히 `H`다. frontend는 서버가 fresh snapshot에 투영한 resolved bounds를 우선 소비하고, 저장 전 draft를 미리보기할 때만 같은 정수 누적 resolver를 사용한다. 이미 확정된 slot heights를 다시 N등분하지 않는다.

기본 fit은 양쪽 모두 `contain`이다. 현재 Scope에서는 명시적 crop 계약이 없으므로 composition schema가 `contain`만 허용한다. frontend `cover`, PIL stretch/crop 또는 한쪽에만 존재하는 fit은 허용하지 않는다.

말풍선 권위는 `(cut_id, local_x_pct, local_y_pct, local_w_pct, local_h_pct)`다. local percentage는 해당 cut slot의 `0…100`이며 global canvas pixel/percentage는 resolver가 파생한다. gap이나 다른 slot 높이가 바뀌어도 같은 `cut_id`의 local rect는 변하지 않는다. backend는 local rect를 해당 slot의 절대 pixel rect로 half-up 투영하고, frontend는 동일 local rect를 해당 slot 안에서 조작한 뒤 저장한다.

동시에 다음을 보존한다.

1. composition 변화는 기존처럼 composition revision과 authority revision을 한 번씩 전진시키고 같은 SQLite transaction에서 active release authorization을 철회한다.
2. geometry/style-only 변경은 cut intent revision이나 generation request sequence를 증가시키지 않는다.
3. INV-1 generation sequence CAS, INV-2 STOP pre-commit lockout, INV-4 destination readback 코드는 수정하지 않으며 영향 회귀를 확인한다.
4. 기존 immutable artifact bytes와 history는 migration으로 덮어쓰거나 삭제하지 않는다.
5. 안전하게 변환할 수 없는 legacy bubble은 clamp하거나 다른 cut으로 이동하지 않는다. 원 좌표를 보존한 `REANCHOR_REQUIRED` 상태로 남기고 새 materialization/release를 차단한다.
6. source/hash/font/slot/bubble 불일치는 전체 materialization 실패다. 누락 layer skip, crop, stretch, ellipsis로 성공을 꾸미지 않는다.

## 3. 현재 코드 Grounding

### 3.1 EXISTING — backend 정수 layout과 PIL renderer

- `src/comic_new/composition.py:17-21`은 width `1024`, height `7680`, cut count `5`, composition schema `1`, renderer contract v1을 상수로 고정한다.
- `src/comic_new/composition.py:105-220`의 `normalize_state()`는 top-level `schema_version/gap_px/font_sha256/bubbles`만 허용하고 bubble을 `x_pct/y_pct/w_pct/h_pct` 전역 percentage로 정규화한다. `cut_id`는 이미 각 bubble에 존재한다.
- `src/comic_new/composition.py:228-240`의 `compute_cut_slots(surface_height, gap_px)`는 cumulative integer division으로 다섯 slot을 계산한다. `7680,24`에서 마지막 bottom은 7680이지만 API가 exact-five와 fixed height에 묶여 있고 resolved heights를 state/DTO로 전달하지 않는다.
- `src/comic_new/composition.py:243-268`의 `compute_bubble_geometry()`는 bubble Y를 전체 surface height에 곱하므로 `cut_id`를 geometry 소유권에 사용하지 않는다.
- `src/comic_new/composition.py:429-457`은 PIL canvas를 `1024×7680`으로 만들고 각 source image에 `scale=min(scale_w, scale_h)`를 적용해 중앙 `contain`한다.
- `src/comic_new/composition.py:474-478`은 모든 bubble을 global surface로 투영한다. `:576-612`의 PNG metadata에는 normalized state가 들어가지만 별도 resolved slot bounds/fit closure는 없다.
- `src/comic_new/composition_service.py:80-184`는 authoritative snapshot을 잡고 source bytes/hash를 검증한 뒤 renderer를 호출한다. `:196-234`는 staging/final PNG의 bytes, dimensions, metadata를 다시 읽는다. 이 경로가 artifact geometry의 권위 readback이다.

이 근거는 현재 backend의 cumulative formula와 `contain`이 실제 정본 경로에 있음을 확정한다. 동적/non-uniform resolved layout, cut-local bubble 및 closure 표현까지 충족한다는 증거는 아니다.

### 3.2 EXISTING — frontend preview와 조작 경로

- `frontend/src/components/canvas/CompositionCanvas.vue:29-49`는 `1024×7680`, 5 cuts를 재선언하고 `Math.floor(availableHeight / 5)`를 각 slot에 반복한다. 나머지 4px이 마지막 bottom에 반영되지 않는 직접 원인이다.
- `frontend/src/components/canvas/CompositionCanvas.vue:90-128`은 cut slots와 bubbles를 모두 surface 직계 absolute layer로 렌더한다. `:164-170`은 cut image에 `object-fit: cover`를 적용한다.
- `frontend/src/components/canvas/BubbleOverlay.vue:24-43,69-113`은 global `x_pct/y_pct/w_pct/h_pct`를 move/resize 입력으로 사용하고 `:120-130`은 이를 surface CSS percentage로 직접 출력한다.
- `frontend/src/composables/useBubblePointer.ts:22-67`은 전달받은 `surfaceRef`의 bounding rect로 pointer delta를 percentage로 바꾼다. 현재 canvas 전체를 기준으로 하므로 Y delta도 global이다.
- `frontend/src/components/inspector/InspectorPanel.vue:87-139`은 global percentage 필드를 편집하고 새 bubble의 Y를 `(cutId-1)*20+5`로 배치한다. 이는 `cut_id`가 있어도 global Y가 실제 소유권임을 보여 준다.
- `frontend/src/api/contracts.ts:93-117,378-408`은 v1 Bubble/Composition DTO와 runtime validator를 global percentage로 고정한다.
- `frontend/src/api/contracts.ts:209-223,566-627`은 snapshot schema 5 및 render contract `1024×7680`을 검증하지만 resolved slots/fit은 검증하지 않는다.

### 3.3 EXISTING — 저장, migration, API, authorization 경계

- `src/comic_new/schema.sql:49-54`는 composition을 singleton `state_json`으로 저장한다. 별도 bubble table/DDL 없이 JSON schema migration이 가능하다.
- `src/comic_new/store.py:75-107`은 DB schema version 5를 고정한다. `:275-461`은 순차 migration을 `BEGIN IMMEDIATE` transaction으로 수행한다.
- `src/comic_new/store.py:1180-1289`의 `accept_composition()`은 normalize → composition CAS → dialogue synchronization → composition/authority revision 증가 → active authorization 철회를 한 transaction에서 수행한다. geometry-only mutation은 intent revision을 바꾸지 않는다.
- `src/comic_new/server.py:187-197,970-980`은 arbitrary `state`를 `normalize_state()`로 검사한 뒤 store에 전달하고 fresh snapshot을 발행한다.
- `src/comic_new/server.py:502-508,523-604`는 default composition과 snapshot composition을 v1로 만들고 render contract에 fixed height만 보낸다.
- `tests/test_transactional_core.py:326-393`, `tests/test_release.py:121-151`은 composition mutation과 authorization 철회가 fresh snapshot에서 함께 보이는 회귀 경계를 이미 가진다.
- `tests/test_baseline_dialogue_authority.py:301-326`은 geometry/style-only 변경이 intent/sequence를 보존함을 검사하고, `:334-466`은 실제 SQLite migration 및 무귀속 데이터 거절 패턴을 제공한다.

### 3.4 EXISTING — 현재 테스트 결손

- `tests/test_composition.py:129-172`는 backend bubble/global geometry와 `last.bottom == 7680`만 검사한다. frontend와 같은 case table을 소비하지 않고 non-uniform heights, N=1/2/7, contain pixels, cut-local projection을 판별하지 않는다.
- `frontend/tests/geometry.test.ts:1-127`은 percentage clamp/move/resize만 검사하며 slot resolver가 없다.
- backend/frontend가 같은 expected bounds fixture를 소비하는 parity test, v1→v2 safe/unsafe bubble migration, API의 legacy field 거절, browser preview와 artifact의 실제 fit 비교가 없다.

### 3.5 Grounding 분류 요약

- **EXISTING:** backend cumulative division은 fixed-five legacy canvas의 마지막 bottom을 7680에 맞춘다.
- **EXISTING:** frontend repeated floored height와 `cover`가 각각 drift와 fit mismatch를 만든다.
- **EXISTING:** composition JSON mutation은 CAS와 authorization revocation transaction을 이미 제공한다.
- **PROPOSED:** composition schema v2, renderer contract v2, resolved integer slot DTO, `contain`-only fit, cut-local bubble union, v5→v6 data migration.
- **PROPOSED:** backend/frontend 공통 case fixture 및 실제 PIL/browser readback을 통한 parity 검증.
- **UNRESOLVED:** 실제 사용자 project DB에 v1 bubble이 있는지, 있다면 safe/unsafe 분포는 repository source만으로 알 수 없다. 구현 시작 시 §10 CF-1의 read-only inventory로 분기하되 어떤 분포도 migration 정책을 바꾸지 않는다.
- **UNRESOLVED:** 선행 BLOCK-11의 실제 exit/readback currentness는 이 source inspection만으로 증명되지 않는다. §10 CF-2가 실패하면 BLOCK-12 mutation을 시작하지 않는다.

## 4. 단일 geometry 및 composition contract

### 4.1 Composition schema v2

`normalize_state()`가 수용하고 store/API/artifact metadata/frontend가 사용하는 단 하나의 current shape를 다음 의미로 전환한다.

```json
{
  "schema_version": 2,
  "canvas_width_px": 1024,
  "gap_px": 24,
  "slot_heights_px": [1516, 1517, 1517, 1517, 1517],
  "fit": "contain",
  "font_sha256": "...",
  "bubbles": [
    {
      "anchor_status": "ANCHORED",
      "bubble_id": "bubble-1",
      "cut_id": 1,
      "shape": "rounded_rectangle",
      "local_x_pct": 25.0,
      "local_y_pct": 5.0,
      "local_w_pct": 50.0,
      "local_h_pct": 20.0,
      "text": "...",
      "font_size_pct": 2.0,
      "line_spacing_pct": 20.0,
      "text_align": "center",
      "text_rgba": "#000000FF",
      "fill_rgba": "#FFFFFFFF",
      "outline_rgba": "#17191DFF",
      "outline_width_pct": 0.2,
      "padding_pct": 5.0
    }
  ]
}
```

- `canvas_width_px`는 정확히 `1024`, `gap_px`는 non-negative integer, `slot_heights_px`는 현재 ordered cuts와 길이가 같고 모든 원소가 positive integer다.
- 현재 Scope에서는 `fit`의 유일한 허용값이 `contain`이다. 미래의 per-cut crop 계약을 미리 만들지 않는다.
- authoritative canvas height는 별도 자유 입력이 아니라 `sum(slot_heights_px) + gap_px*(N-1)`에서 파생한다.
- `ANCHORED` bubble은 global `x_pct/y_pct/w_pct/h_pct`를 허용하지 않는다. local rect의 각 edge가 `0…100` 안에 있어야 한다.
- 안전하게 변환되지 않은 legacy bubble은 같은 배열의 discriminated `anchor_status: "REANCHOR_REQUIRED"` record로 보존한다. 이 record는 원 `legacy_global_rect`, 원 `cut_id`, 원 style/text를 손실 없이 가지며 local fields를 가장하지 않는다. frontend는 재배치 필요 상태를 표시하고 renderer/materializer는 하나라도 존재하면 전체를 거절한다.
- API는 migration을 거치지 않은 v1/global payload를 받지 않는다. compatibility alias나 dual-write를 두지 않는다.

`slot_heights_px`의 예시는 기존 `7680, gap=24, N=5` backend bounds를 보존한 값이다. 새 resolver는 non-uniform heights도 동일하게 처리한다. 이 Scope는 BLOCK-13의 cut membership 저장을 도입하지 않지만 함수와 DTO는 배열 길이 `N >= 1`을 가정해 N=1/2/5/7에서 정확해야 한다.

### 4.2 Canonical integer resolver

backend `compute_cut_slots(slot_heights_px, gap_px)`와 frontend `computeCutSlots(slotHeightsPx, gapPx)`의 계약은 다음 하나다.

```text
cursor = 0
for i in 0..N-1:
    height = slot_heights_px[i]          # positive integer
    top = cursor
    bottom = top + height
    emit(cut_id=i+1, top_px=top, bottom_px=bottom, height_px=height)
    cursor = bottom + (i < N-1 ? gap_px : 0)
H = cursor
```

- float 계산과 percentage 반올림을 slot 권위에 사용하지 않는다.
- `top/height` CSS percentage는 마지막 화면 투영에서만 `top_px/H*100`, `height_px/H*100`으로 계산한다. 권위 및 parity assertion은 integer px다.
- legacy v1 migration에만 별도 private helper가 과거 `(surface_height, gap_px, N)` cumulative division을 복원한다. 결과 slot heights를 v2에 저장한 뒤 runtime에서는 다시 나누지 않는다.
- backend snapshot의 `render_contract`는 `{width_px,height_px,gap_px,fit,slots:[...]}`를 current composition에서 계산해 제공한다. frontend server state는 이 exact array를 소비한다. local draft preview는 v2 `slot_heights_px`로 같은 resolver를 실행하고 저장 성공 후 server bounds와 교체한다.

### 4.3 Cut-local bubble projection

backend `compute_bubble_geometry(bubble, slot, canvas_width)`는 `ANCHORED` bubble만 받는다.

```text
left   = half_up(local_x_pct * canvas_width / 100)
right  = half_up((local_x_pct + local_w_pct) * canvas_width / 100)
top    = slot.top_px + half_up(local_y_pct * slot.height_px / 100)
bottom = slot.top_px + half_up((local_y_pct + local_h_pct) * slot.height_px / 100)
```

`right > left`, `bottom > top`, `left/right`가 width 안, `top/bottom`이 소유 slot 안인지 재확인한다. bubble의 `cut_id`로 slot을 lookup하며 list index를 암묵적 소유권으로 쓰지 않는다.

frontend `geometry.ts`에는 다음 pure functions를 둔다.

1. `computeCutSlots(slotHeightsPx, gapPx): ResolvedSlot[]`
2. `canvasHeight(slots, gapPx)` 또는 resolver result의 `heightPx`
3. `projectLocalRectToCanvas(localRect, slot, widthPx, heightPx): CanvasPercentageRect`
4. 기존 move/nudge/resize는 `LocalPercentageRect`를 받고 해당 cut의 `0…100`에서 clamp한다.

`CompositionCanvas.vue`는 bubble의 `cut_id`로 resolved slot을 선택하고 canvas CSS 위치만 projection한다. `BubbleOverlay.vue`는 local rect를 편집하되 화면 style은 부모가 준 projected rect를 사용한다. `useBubblePointer()`에는 해당 cut slot element/ref의 bounding rect를 전달해 pointer Y delta가 slot-local percentage가 되게 한다. bubble을 다른 slot으로 drag해 소유권을 바꾸는 동작은 Non-Goal이며 경계에서 clamp한다.

## 5. Backend 구현 방법

### 5.1 `composition.py` clean cutover

1. `SCHEMA_VERSION=2`, `RENDERER_CONTRACT="canonical-composition/v2"`로 올리고 fixed `CANONICAL_HEIGHT`/`TOTAL_CUTS`를 runtime geometry authority로 사용하지 않는다. width 1024만 canonical constant로 유지한다.
2. `ResolvedSlot` frozen dataclass와 §4.2 `compute_cut_slots()`를 추가한다. bool, 빈 배열, non-integer/non-positive height, negative gap을 명시적으로 거절한다.
3. `normalize_state()`를 v2-only schema로 바꾸고 anchored/reanchor-required bubble union을 strict하게 정규화한다. unknown/global fields는 거절한다.
4. `compute_bubble_geometry()`를 slot-aware local projection으로 교체한다. 소유 slot 부재, reanchor-required, edge overflow와 non-positive pixel area를 `CompositionRenderError`로 거절한다.
5. `render_canonical()`은 normalized state에서 slots/H를 한 번 resolve해 `(1024,H)` canvas를 만들고 ordered cuts와 slot count/cut identity를 대조한다. cut image는 현재 PIL `contain` 계산을 유지하되 slot마다 적용한다.
6. closure metadata에 `width_px`, `height_px`, ordered exact slot bounds, `gap_px`, `fit: contain`, local bubble state, composition revision과 renderer contract v2를 포함한다. metadata에서 global bubble authority를 만들지 않는다.
7. artifact size/readback은 더 이상 fixed 7680과 비교하지 않고 rendered resolved height와 metadata layout이 일치하는지 비교한다.

### 5.2 `composition_service.py`와 API projection

- `CompositionService.materialize()`는 current composition v2를 normalize한 뒤 resolved slot count와 current cut payload count/order가 일치해야만 renderer를 호출한다. `REANCHOR_REQUIRED`, fit mismatch, invalid slot은 staging 생성 전에 실패시킨다.
- staging/final readback은 PNG size가 closure `(1024,H)`와 일치하고 closure의 slots/fit/state가 요청 snapshot과 byte-for-byte canonical JSON 의미로 일치하는지 확인한다.
- `server._snapshot_dto()`는 current composition에서 resolved layout을 계산해 `render_contract`에 투영한다. composition이 아직 null이면 v2 default와 그 resolved bounds를 반환한다.
- `server._default_composition()`은 기존 N=5 product의 legacy 7680 geometry를 정확히 보존한 v2 heights와 `fit: contain`을 생성한다. BLOCK-13이 authoritative N을 도입할 때 이 factory의 cut count 입력을 확장할 수 있지만, 여기서 DB/cardinality를 변경하지 않는다.
- `PUT /api/composition`은 v2만 수용하며 global fields/v1/reanchor-required를 저장할 수는 있어도 reanchor-required가 있는 state의 materialization은 불가하다. 새 anchored bubble 생성/편집은 local fields만 사용한다.

### 5.3 Store migration v5→v6

새 `src/comic_new/migrations/v5_to_v6.sql` marker와 `TransactionalStore._migrate_v5_to_v6()`를 추가하고 `SCHEMA_VERSION=6`으로 올린다. migration은 `BEGIN IMMEDIATE` 안에서 다음 순서를 지킨다.

1. composition singleton의 revision/state JSON, current authority revision 및 active authorization을 읽는다. `{}`인 revision 0 state는 v2 default를 꾸며 저장하지 않고 그대로 둔다.
2. v1 state이면 `gap_px`, old fixed surface `7680`, current five cuts로 과거 backend cumulative slots를 복원한다. 그 각 height를 v2 `slot_heights_px`로 고정한다.
3. 각 legacy bubble의 global percentage를 기존 Decimal half-up으로 `(left,top,right,bottom)` pixel edge로 복원한다. center Y가 정확히 한 slot 안에 있고 전체 rect도 같은 slot 안에 있으며 그 slot의 cut id가 저장 `cut_id`와 같을 때만 local percentage로 변환한다.
4. 변환 local percentage를 canonical precision으로 만든 뒤 새 `compute_bubble_geometry()`로 재투영한다. 네 pixel edge가 원 edge와 정확히 같을 때만 `ANCHORED`로 확정한다. 하나라도 다르거나 center가 gap/다른 cut, rect가 slot을 넘으면 원 record를 `REANCHOR_REQUIRED`로 보존한다. clamp, owner 재지정, silent drop은 금지한다.
5. v2 state를 canonical JSON으로 저장하고 composition revision 및 authority revision을 각각 한 번 증가시키며, 같은 transaction에서 active authorization을 철회한다. 이는 renderer contract/closure가 바뀌었기 때문이다. intent revision, request sequence, canonical realization, artifact/delivery history는 변경하지 않는다.
6. `PRAGMA user_version=6`까지 같은 transaction에서 commit한다. parse/validation/round-trip 검증 실패는 전체 rollback 후 `StoreCorruptionError`다.

이미 v2인 state를 다시 변환하지 않으며 migration 재실행으로 revision이 중복 증가하지 않아야 한다. 기존 immutable artifact는 이전 renderer metadata와 bytes로 그대로 남고 current authorization만 비활성화된다.

## 6. Frontend 구현 방법

### 6.1 DTO/runtime validator

`frontend/src/api/contracts.ts`에서 snapshot schema를 6으로 전환하고 다음을 clean cutover한다.

- `BubbleDTO`는 `AnchoredBubbleDTO | ReanchorRequiredBubbleDTO` discriminated union이다.
- normal edit path는 `AnchoredBubbleDTO`의 `local_x_pct/local_y_pct/local_w_pct/local_h_pct`만 사용한다.
- `CompositionStateDTO`는 schema v2, width, slot heights, fit, bubbles를 검증한다.
- `ResolvedSlotDTO`와 `RenderContractDTO`는 exact integer bounds, derived height, gap, fit을 검증한다. slots가 ordered/contiguous이고 gaps 및 total height가 state에서 재계산한 값과 일치하지 않으면 snapshot 전체를 거절한다.
- v1/global field를 optional alias로 받지 않는다.

### 6.2 `geometry.ts`, pointer와 overlay

- §4.2/4.3 pure functions 및 types를 `geometry.ts`에 둔다. slot resolver는 배열을 한 번 순회하며 추가 allocation은 반환 배열 외에 만들지 않는다.
- 기존 `PercentageRect`를 `LocalPercentageRect`로 이름/필드를 clean cutover하고 `applyMoveDelta/applyNudge/applyResizeDelta`의 모든 caller/test를 함께 이동한다.
- `useBubblePointer.ts`는 local rect를 사용하며 gesture 시작 때 소유 slot DOMRect를 freeze한다. canvas 전체 rect를 전달하는 caller를 남기지 않는다.
- `BubbleOverlay.vue`는 anchored bubble만 interactive하게 렌더하고 local rect를 commit한다. projected canvas rect는 별도 prop으로 받아 CSS에만 쓴다. `REANCHOR_REQUIRED`는 drag 가능한 정상 bubble로 가장하지 않는다.

### 6.3 Canvas/Inspector/store

- `CompositionCanvas.vue`의 상수 `SURFACE_H`, local cut division 코드를 제거한다. accepted state에서는 `server.render_contract.slots/height_px`를 사용하고 draft가 있으면 `geometry.ts` resolver 결과를 사용한다.
- cut layer는 exact slot `top_px/H`, `height_px/H`로 배치하고 `.cut-image { object-fit: contain; }`으로 바꾼다. slot/background가 letterbox를 그대로 보여야 하며 stretch/crop CSS를 추가하지 않는다.
- bubble은 `cut_id` slot을 찾은 뒤 local→canvas projection하여 표시한다. slot을 찾을 수 없으면 정상 표시하지 않고 composition-invalid 상태로 저장/materialization을 막는다.
- `InspectorPanel.vue`는 local field만 편집하고 새 bubble을 선택 cut의 `(25,5,50,20)` 등 local default로 만든다. cut index를 global Y에 곱하는 식을 삭제한다. `REANCHOR_REQUIRED`는 원 좌표 요약과 “수동 재배치 필요”를 표시하고 사용자가 현재 선택 cut 안에 명시적으로 새 위치를 지정할 때만 anchored record로 교체한다.
- `studio.ts`의 draft/save lane과 CAS는 유지한다. v2 full state를 원자 저장하며 성공 snapshot 전 local draft를 제거하지 않는다. geometry draft가 존재하면 기존 release UI 차단을 유지한다.

## 7. 파일별 line-anchored 변경 목록

1. `src/comic_new/composition.py:17-21,105-268,345-478,572-612`
   - schema/renderer contract v2, resolved slot type/resolver, strict local bubble normalization/projection, dynamic H render와 geometry closure를 구현한다.
2. `src/comic_new/composition_service.py:16-30,80-184,196-234`
   - fixed height/count import·검사를 resolved layout 검증으로 바꾸고 staging/final PNG size와 closure readback을 dynamic H에 결속한다.
3. `src/comic_new/store.py:75-107,275-461`
   - DB schema 6, v5→v6 migration dispatch와 Python data migration을 추가한다.
4. 새 `src/comic_new/migrations/v5_to_v6.sql`
   - composition JSON migration의 reviewed marker를 둔다. 실제 Decimal/JSON round-trip은 store Python transaction에서 수행한다.
5. `src/comic_new/store.py:1180-1289`
   - v2 normalize/CAS/dialogue sync/authorization revocation을 유지하고 bubble union을 안전하게 순회한다.
6. `src/comic_new/server.py:502-508,523-604,970-980`
   - v2 default, resolved render contract projection, v2-only composition API를 연결한다.
7. `frontend/src/api/contracts.ts:93-117,209-223,378-408,566-627`
   - local/reanchor bubble union, composition v2, snapshot schema 6, resolved layout runtime validation을 구현한다.
8. `frontend/src/domain/geometry.ts:1-105`
   - integer slot resolver, local rect reducer, local→canvas projection으로 교체한다.
9. `frontend/src/composables/useBubblePointer.ts:1-112`
   - local rect와 owner slot DOMRect 기준 gesture로 전환한다.
10. `frontend/src/components/canvas/CompositionCanvas.vue:29-49,61-75,82-128,147-170`
    - fixed division/height 제거, server/draft resolved slots 소비, local bubble projection 및 `contain`을 적용한다.
11. `frontend/src/components/canvas/BubbleOverlay.vue:1-131`
    - local interaction rect와 projected display rect를 분리하고 commit payload를 local fields로 바꾼다.
12. `frontend/src/components/inspector/InspectorPanel.vue:16-20,55-64,87-145`
    - anchored union narrowing, local field editor/default, explicit reanchor UX를 구현한다.
13. `frontend/src/store/studio.ts:351-434,527-665`
    - composition v2 draft/CAS save가 unchanged semantics로 동작하도록 type/callers를 갱신한다.
14. `tests/test_composition.py:129-220` 및 renderer scenarios
    - backend slot/local bubble/contain/dynamic closure tests로 교체·확장한다.
15. `tests/test_baseline_dialogue_authority.py:301-466`
    - geometry-only preservation과 v5→v6 safe/unsafe/idempotent migration/authorization tests를 추가한다.
16. `tests/test_server.py`의 composition endpoint/snapshot scenarios
    - v2 request/fresh readback, v1/global reject, render contract exact bounds를 검증한다.
17. `frontend/tests/geometry.test.ts:1-127`
    - local reducers, N=1/2/5/7 slots, non-uniform heights, local projection을 검증한다.
18. `frontend/tests/store.test.ts:15-58,221-271,287 이후`
    - schema 6 snapshot, v2 default save와 resolved contract, composition failure draft preservation을 갱신한다.
19. 새 `tests/fixtures/composition_geometry_cases.json`
    - Python과 Vitest가 함께 읽는 N/gap/heights/expected exact bounds case table을 둔다. 이는 runtime authority가 아니라 두 구현의 parity fixture다.

## 8. 구현 순서와 부분 실패 경계

1. **Shared contract first:** fixture와 backend v2 resolver/normalizer/projection을 구현하고 pure scoped tests로 exact bounds와 migration round-trip 기준을 고정한다.
2. **Durable migration:** DB v6 migration과 store atomicity tests를 구현한다. 이 단계가 검증되기 전 frontend v2만 배포하면 기존 project snapshot을 읽을 수 없으므로 다음 단계와 같은 change set으로 완료한다.
3. **Renderer/readback:** dynamic H, contain, local bubble projection, closure metadata와 CompositionService readback을 연결한다.
4. **API cutover:** server default/snapshot/PUT contract를 v2로 전환한다. v1 input alias를 남기지 않는다.
5. **Frontend cutover:** DTO→geometry→pointer/overlay→canvas/inspector/store 순으로 모든 global field caller를 이동한다. backend v2와 frontend v1 또는 반대 조합을 release하지 않는다.
6. **Scoped integration/smoke:** store/API tests, Python/TS shared fixture, actual browser preview와 materialized PNG 비교를 수행한다.

migration 또는 renderer가 실패하면 SQLite transaction과 기존 composition/artifacts가 보존되어야 한다. staging PNG가 생긴 뒤 registration/readback이 실패하면 current artifact로 등록하거나 authorization하지 않는다. frontend save 실패/409/422/5xx는 local v2 draft를 유지하고 server accepted layout으로 성공 표시하지 않는다.

## 9. 테스트 및 검증 계획

### 9.1 Pure geometry parity

공유 fixture에 최소 다음 case를 고정하고 Python `compute_cut_slots()`와 TypeScript `computeCutSlots()`가 같은 exact integer array를 반환하게 한다.

- N=1, heights `[7680]`, gap 24 → `(0,7680)`.
- N=2, 균등/비균등 heights와 gap 0/24.
- N=5, legacy `H=7680`, gap 24, heights `[1516,1517,1517,1517,1517]` → 마지막 bottom 7680; 과거 frontend 7676 반례가 불가능함.
- N=7, odd/non-uniform positive heights와 gap.
- invalid: N=0, zero/negative/non-integer height, negative gap.

각 case에서 `top[0]=0`, `bottom-top=height`, `next.top=previous.bottom+gap`, `last.bottom=sum(heights)+(N-1)gap`을 assertion한다. source text 비교가 아니라 실제 함수를 실행한다.

### 9.2 Bubble schema/projection/migration

- 각 cut에서 local `(x,y,w,h)`가 half-up 후 해당 slot 안 exact pixel rect가 되는지 검사한다.
- 다른 slot 높이/gap만 바꿔도 `cut_id`와 local values가 동일하고 global Y만 올바르게 재투영되는지 검사한다.
- API가 global `y_pct`/schema v1/unknown mixed fields를 422로 거절하고 local v2를 fresh snapshot에서 동일하게 반환하는지 검사한다.
- v5 fixture DB의 safe legacy bubble이 migration 전 old pixel rect와 migration 후 projected rect가 exact edge-equal인지 검사한다.
- center가 gap, declared `cut_id` 불일치, rect가 slot 경계를 넘는 각각을 `REANCHOR_REQUIRED`로 분류하고 원 global record가 그대로 남는지 검사한다.
- migration이 composition/authority revision을 한 번만 올리고 active authorization을 같은 transaction에서 철회하며 intent revision/request sequence/artifact bytes/history를 보존하는지 검사한다.
- migrated DB 재open이 추가 mutation 없이 schema 6 snapshot을 반환하는지 검사한다.

### 9.3 Rendering fit/closure

- wide source와 tall source를 명확한 border/color pattern으로 만들고 non-square slots에 PIL materialize한다. `contain` scale, centered offsets, letterbox pixels, source 전체 corner 보존을 pixel readback으로 검사한다. 단순 이미지 크기 assertion으로 대체하지 않는다.
- bubble pixel rect와 text/shape가 owner slot을 벗어나지 않는지 검사한다.
- PNG metadata를 다시 열어 width/H, exact slots, fit, local bubble state, renderer contract v2 및 composition revision이 request snapshot과 같은지 검사한다.
- `REANCHOR_REQUIRED`, invalid fit, non-positive slot, count/order mismatch에서 artifact row/authorization이 생기지 않는지 검사한다.

### 9.4 Store/API/불변식 회귀

- geometry/fit/bubble mutation 수용 후 fresh snapshot에서 new composition과 revoked authorization이 동시에 보이고 old authorization+new content 중간 상태가 없음을 확인한다(INV-3).
- geometry-only edit가 desired revision과 generation request sequence를 바꾸지 않음을 확인한다(INV-1 영향 보존).
- 기존 STOP/post-STOP commit 및 destination readback의 영향 범위 test를 targeted 실행해 INV-2/INV-4 경로가 손상되지 않았음을 확인한다.
- save conflict와 invalid state에서 DB revision/authorization이 전혀 바뀌지 않고 frontend draft가 유지되는지 확인한다.

### 9.5 Frontend 및 실제 surface smoke

- Vitest에서 local move/nudge/resize가 owner slot `0…100`에 clamp되고 pointer delta가 slot DOMRect를 기준으로 계산됨을 확인한다.
- `CompositionCanvas`가 server accepted bounds를 쓰고 draft 때만 local resolver를 쓰며 `.cut-image` computed style이 `contain`인지 확인한다.
- 실제 앱을 disposable project로 실행하고 browser에서 wide/tall patterned cuts와 각 cut bubble을 연다. screenshot에서 letterbox와 slot 경계를 기록하고 bubble을 move/resize/save한다.
- 같은 accepted composition revision으로 review artifact를 materialize하고 PNG bytes를 열어 preview와 동일한 source 전체/여백 방향, slot bounds, bubble owner/local 위치를 대조한다.
- gap을 변경·저장한 뒤 bubble의 local values/cut_id가 fresh snapshot에서 그대로이고 global 위치만 새 slot으로 이동했으며 active release authorization이 사라졌음을 확인한다.

## 10. Conditional first work

### CF-1 — legacy composition inventory

- `plan_anchor`: `PLAN-001 §5.3 Store migration v5→v6`
- `permitted_initial_work`: 구현자가 사용자가 지정한 실제 project DB를 변경하지 않는 read-only query 또는 복사본에서 schema version, composition state version, bubble 수, 각 legacy rect의 safe/unsafe 분류를 계산한다. 원본 DB/asset은 쓰지 않는다.
- `discriminating_observation`: 모든 legacy bubble이 exact pixel round-trip 가능한지, gap/다른 cut/edge crossing 또는 cut_id mismatch가 존재하는지의 bubble-id별 분류와 원 state hash.
- `dependent_work_not_yet_permitted`: 관찰 전 실제 project migration 실행, unsafe bubble clamp/drop/owner 변경, 기존 artifact 재렌더링은 금지한다.
- `response_if_refuted`: 예상하지 못한 legacy shape/field가 있으면 해당 DB mutation을 중단하고 migration method를 이 Plan 소유자에게 반환해 fresh independent review를 받는다. 제품 의미를 바꿔야 하면 Main이 Scope/Thesis owning source로 re-entry한다.

### CF-2 — BLOCK-11 handoff currentness

- `plan_anchor`: `PLAN-001 §1 결속된 권위와 실행 경계`
- `permitted_initial_work`: disposable project에서 한 줄 draft → 별도 Baseline approval → fresh snapshot까지 read-only/isolated smoke하여 active five cuts와 composition default 생성 진입을 확인한다.
- `discriminating_observation`: accepted Baseline snapshot이 ordered cuts와 current schema 5 composition/default contract를 반환하고, draft success 자체는 authority를 바꾸지 않는다.
- `dependent_work_not_yet_permitted`: 선행 경계가 깨졌다면 BLOCK-12 source/data migration 및 frontend cutover를 시작하지 않는다.
- `response_if_refuted`: BLOCK-11 결과 owner/Main에게 현재 readback을 반환한다. BLOCK-12 Plan에서 draft/Baseline 의미를 고치지 않는다.

## 11. 구현자 self-check 및 verifier handoff

구현자는 다음 evidence bundle을 남긴다.

1. 변경 후 exact Scope/Thesis/Baseline hash와 implementation target revision.
2. shared fixture를 소비한 Python/TypeScript exact result 및 N=1/2/5/7/non-uniform case 출력.
3. safe/unsafe migration fixture의 pre-state hash, 분류, post-state, revision/authorization/artifact 보존 readback.
4. API v2 accepted snapshot과 v1/global rejection response.
5. patterned source의 browser screenshot, 동일 composition revision의 artifact path/hash/PNG closure 및 pixel 비교 결과.
6. geometry mutation 전 active authorization과 mutation 후 fresh snapshot의 revoked record.
7. 실행한 targeted command와 종료 결과. project-wide validation은 Main이 모든 동시 변경 landing 후 한 번 수행한다.

Verifier handoff의 minimum real path는 다음이다.

```text
schema-5 legacy project copy open
→ atomic v6 migration
→ fresh v2 composition/render_contract readback
→ browser contain/local bubble preview 및 편집 저장
→ fresh accepted snapshot과 authorization revocation
→ same revision materialization
→ PNG bytes/hash/closure 및 preview geometry 대조
```

unit test나 DOM만으로 이 path를 대체하지 않는다. unsafe fixture는 `REANCHOR_REQUIRED`와 materialization 차단까지 별도로 관찰한다.

## 12. 재검토가 필요한 변경과 구현자 재량

다음은 outcome/contract를 바꾸지 않는 구현자 재량이다: private helper 이름, dataclass/interface 배치, 동일한 strict validation error wording, test fixture helper 구성, Vue ref 관리 방식.

다음은 material method 변경이므로 해당 구현을 중단하고 이 Plan 수정 및 fresh independent Plan Review가 필요하다.

- slot authority를 stored integer heights가 아닌 새 division/float/CSS 계산으로 변경.
- frontend가 server resolved bounds를 소비하지 않고 별도 accepted formula를 권위로 삼음.
- v1/v2 dual-write, global field compatibility alias 또는 unsafe legacy 자동 clamp를 도입.
- migration의 revision/authorization atomic boundary를 변경.
- `contain` 이외 fit/crop policy를 추가하거나 renderer/readback closure 전략을 변경.
- bubble owner를 stable `cut_id`가 아닌 list position/display order로 변경.

제품 의미, BLOCK-12/13 경계, unsafe legacy 처리 의미 또는 acceptance를 바꿔야 하면 Plan이 결정하지 않고 Main에게 Thesis/Transition/Scope owning source 수정으로 반환한다. 이 문서는 실행 방법이지 구현·검증·완료 판정이 아니다. exact Scope/Plan bytes에 대해 independent Plan Reviewer가 모든 Acceptance와 conditional start를 검토해 `ADMIT`한 뒤에만 구현을 시작한다. Scope `done`은 별도 semantic verification과 Coverage 후 Main만 기록한다.
