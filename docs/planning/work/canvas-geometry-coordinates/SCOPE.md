# Scope: Canvas Geometry Unification and Cut-Local Coordinates

Schema: iis-scope/v1
Project-Root: /home/user01/project/comic_new
Status: done

## Product Authority

- /home/user01/project/comic_new/docs/planning/product-thesis/web-comic-studio/THESIS-003.md sha256:d239e9c1c125d4d47aafcf7727901b836f4133ca3406df4ee8351ddacb60e268

## Transition Authority

- /home/user01/project/comic_new/docs/planning/adaptive/BASELINE-003.md sha256:59d815b2025e810373381dc1033923289a1c1d6c962338825c2ddd115f934d51

## Outcome

현재 조판 렌더러와 프론트엔드 캔버스 사이에는 심각한 기하학적 불일치가 존재한다.
1. 백엔드 Python(`composition.py:compute_cut_slots`)은 정수 나눗셈 누적 방식으로 슬롯을 계산하여 바닥이 7680px에 정확히 닿는 반면, 프론트엔드 Vue(`CompositionCanvas.vue`)는 `Math.floor(usable/N)`을 단순 곱하여 계산함으로써 마지막 슬롯 바닥이 7676px로 끝나 최대 4px의 렌더링 오차(drift)가 발생한다.
2. 백엔드는 원본 이미지를 여백 보존 방식으로 축소하는 `contain` 방식인데, 프론트엔드 CSS는 상하를 잘라먹는 `object-fit: cover`를 사용하여 화면에서 보는 구도와 실제 생성되는 정본 웹툰의 구도가 서로 어긋난다.
3. 말풍선 좌표가 전체 7680px 캔버스 기준의 전역 백분율(`y_pct`)로 관리되어, 컷 높이나 컷 수가 변동될 때 말풍선이 엉뚱한 컷으로 밀려나는 결손이 있다.

이 Scope는 `BASELINE-003`의 `BLOCK-12`를 선택한다.
백엔드와 프론트엔드의 슬롯 경계 계산 알고리즘을 단일 정수 기하학(Single Resolved Integer Layout)으로 완전 일치시켜 4px drift를 원천 제거한다.
프론트엔드 캔버스의 이미지 렌더링을 백엔드 조판 엔진과 동일한 `contain` 정책으로 일치시켜 WYSIWYG(보는 대로 조판됨)를 보장한다.
말풍선 좌표 스키마를 전역 `y_pct`에서 **`컷 로컬 백분율 (cut_id, local_x_pct, local_y_pct)`**로 전환하여, 향후 N컷 추가/삭제나 간격 변경 시에도 말풍선이 자신의 소유 컷 안에 안정적으로 고정되도록 한다.
기존 데이터에 대한 마이그레이션 및 정본 조판 계산(`compute_bubble_geometry`)을 업데이트하여 일관성을 확보한다.

포함: `composition.py` 및 `geometry.ts`의 슬롯 정수 계산 단일화, `CompositionCanvas.vue`의 `contain` 렌더링 통일, `store.py` 및 프론트엔드 말풍선 데이터 모델의 컷 로컬 좌표계 전환, 4대 인과 불변식 보존.

제외: 임의 N컷 추가/삭제/재정렬 스키마 및 DDL 변경(`BLOCK-13`), OpenCodex LLM 기획 추가 변경.

## Acceptance

### A. 슬롯 정수 계산 알고리즘 단일화 (4px Drift 제거)
백엔드 `composition.py`와 프론트엔드 `geometry.ts`가 동일한 정수 슬롯 분할 알고리즘을 사용한다. N=5, gap=24, height=7680 기준 모든 컷의 top/bottom 좌표가 1px의 오차도 없이 백/프론트 간에 100% 동일하게 산출되며, 마지막 슬롯의 바닥이 캔버스 높이 끝(7680)과 정확히 일치한다.

### B. 백엔드-프론트엔드 렌더링 Fit Parity (Contain 일치)
프론트엔드 `CompositionCanvas.vue`의 컷 이미지 렌더링 스타일이 백엔드 PIL 합성 엔진과 동일하게 `contain` 방식으로 정렬된다. 브라우저에서 보이는 이미지 비율과 여백이 실제 조판된 Canonical Review Artifact PNG와 완벽히 일치하여 visual WYSIWYG가 성립한다.

### C. 컷 로컬 말풍선 좌표계 전환 (Cut-Local Coordinates)
말풍선의 위치가 소유 컷 기준 백분율 `(cut_id, local_x_pct, local_y_pct)`로 저장 및 조작된다. 컷 간격(gap)이나 타 컷의 높이가 변경되어도 해당 컷 내부의 말풍선 상대 위치는 완벽히 보존된다. 백엔드 PIL 텍스트 렌더러는 컷 로컬 좌표를 슬롯 절대 픽셀 좌표로 정확히 투영하여 렌더링한다.

### D. 기존 데이터 호환 및 마이그레이션
기존 전역 `y_pct`로 저장된 말풍선 데이터가 존재할 경우, 각 말풍선의 중심 Y좌표가 속한 컷의 슬롯을 찾아 컷 로컬 백분율로 무손실 변환되어 정상 표시 및 조판된다.

### E. 4대 인과 불변식 보존
조판 상태 변경 시 기존 릴리즈 승인은 원자적으로 즉시 철회되며(INV-3), Monotonic Sequence CAS, STOP 사전 커밋 차단, 릴리즈 목적지 검증은 손상 없이 완벽히 유지된다.

## Non-Goals

- 임의 N컷 추가/삭제 DDL 및 컷오버 (`BLOCK-13`)
- 새로운 폰트 엔진 도입

## Open Decisions

None
