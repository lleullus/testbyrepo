# 예시: initiative에서 선택한 작은 구현 범위

Status: approved
Owner: 예시 planning owner
Source-Increment: docs/planning/scope-shaping/example-initiative/increments/INC-001.md

이 문서의 `approved`는 confirmed Scope revision과 selected ready Increment에서 시작한 Ask Matt 결과가 모든 미해결 제품 결정을 닫은 뒤 To Spec의 충실성·완전성·검증 가능성 자체검수를 통과한 계약 상태 예시다. Source Increment와 그 immutable Scope revision은 lineage와 planning context이며, 이 Spec과 adopted authorities가 실행 권위를 가진다. 이 예시는 실행 fixture나 실제 제품 요구사항이 아니다.

## Problem

가상의 큰 변경에서 실제로 구현할 첫 번째 작은 동작 경계를 정해야 한다.

## Desired Outcome

큰 변경 전체를 약속하지 않고, 선택한 한 동작의 완료 기준을 관찰할 수 있다.

## Requirements

- 탐색으로 좁힌 한 동작만 구현 범위로 확정한다.
- 확정한 범위는 selected Work Package 밖의 sibling outcome을 포함하지 않는다.
- 이 delivery는 확정한 입력을 실행하고 complete product result를 직접 읽을
  ordinary product boundary와 readback을 만든다.

## Non-Goals

- 큰 변경 전체의 구현
- 다른 Work Package의 추가 채택
- UI 변경

## Implementation Constraints

이 Spec에 적힌 작은 범위를 넘기지 않으며, Scope result와 selected Work Package는 lineage와 context로만 참조한다.

## Verification Expectations

- Outcome: 확정한 입력에서 selected Work Package의 작은 non-UI 동작 결과를 관찰할 수 있다.
  Acceptance boundary: 선택한 동작의 normal non-UI product boundary
  Trigger or inspection target: 확정한 입력을 선택한 동작의 normal product entry에 제공한다.
  Expected observable result: selected Work Package가 요구한 작은 동작의 product result가 반환된다.
  Authoritative readback: 같은 product entry가 반환한 product result
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 선택한 동작의 ordinary product entry와 complete 반환 결과
  External condition: None
- Outcome: complete product result는 selected Work Package 밖 sibling outcome을 포함하지 않는다.
  Acceptance boundary: 선택한 동작의 complete product result
  Trigger or inspection target: 확정한 입력을 선택한 동작의 ordinary product entry에 제공한다.
  Expected observable result: complete product result에는 selected Work Package의 작은 동작 결과만 있고 sibling outcome이 없다.
  Authoritative readback: 같은 product entry가 반환한 complete product result
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 선택한 동작의 ordinary product entry와 complete 반환 결과
  External condition: None
  Absence terminal condition: complete product result가 반환되면 이번 호출 결과에 추가 sibling outcome이 나타날 수 없다.

## Behavior Authorities

- docs/planning/behavior/contexts/selected-outcome.md | Scope: selected Work Package의 작은 non-UI 동작과 sibling outcome의 비대상 경계

## UI / UX

Not applicable

## Open Questions

None
