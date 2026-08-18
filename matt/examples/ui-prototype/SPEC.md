# 예시: 채택된 UI 제시 순서 반영

Status: approved
Owner: 예시 planning owner
Source-Increment: None

이 문서의 `approved`는 사용자가 `UI-UX.md`의 결정을 상위 planning authority로 채택하고 Open Questions를 해소한 뒤 To Spec 자체검수를 통과한 계약 상태 예시다. `PROTOTYPE-NOTE.md`의 결과 자체는 권위가 아니며, 이 예시는 실행 fixture나 실제 제품 요구사항이 아니다.

## Problem

가상의 대상 화면에서 필요한 정보와 주요 행동의 제시 순서를 명확히 해야 한다.

## Desired Outcome

사용자는 필요한 정보를 먼저 보고, 그 다음 하나의 주요 행동을 확인할 수 있다.

## Requirements

- `UI-UX.md`에 승인된 정보 우선, 주요 행동 후속 순서를 따른다.
- 채택되지 않은 prototype 선택지는 반영하지 않는다.

## Non-Goals

- 화면 전반의 재설계
- 추가 상호작용이나 문구 결정
- prototype 결과의 자동 채택

## Implementation Constraints

승인된 UI/UX 참조의 제시 순서만 구현 범위로 삼는다.

## Verification Expectations

- Outcome: 넓은 화면과 좁은 화면에서 승인된 정보와 주요 행동의 제시 순서가 보인다.
  Acceptance boundary: 대상 화면의 rendered UI
  Trigger or inspection target: 지원되는 넓은 viewport와 좁은 viewport에서 대상 화면을 연다.
  Expected observable result: 두 viewport 모두에서 필요한 정보가 하나의 주요 행동보다 먼저 보인다.
  Authoritative readback: 각 viewport의 현재 rendered state와 보이는 정보·행동 순서
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 승인된 순서를 표현하는 대상 화면의 rendered state
  External condition: None
  UI rendered state and interaction readback: 넓은 viewport와 좁은 viewport에서 필요한 정보 및 하나의 주요 행동이 실제로 보이는 순서를 직접 관찰한다.

## Behavior Authorities

- docs/planning/behavior/contexts/ui-information-action-order.md | Scope: 대상 화면에서 정보가 단일 주요 행동보다 먼저 제공되는 의미적 순서

## UI / UX

- ./UI-UX.md | Scope: 대상 화면의 정보와 단일 주요 행동의 rendered ordering 및 narrow/wide viewport 보존

`PROTOTYPE-NOTE.md`는 검토 배경일 뿐 권위가 아니다.

## Open Questions

None
