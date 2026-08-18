# 예시: 일반 non-UI 동작 한 가지 변경

Status: approved
Owner: 예시 planning owner
Source-Increment: None

이 문서의 `approved`는 확정된 shared understanding에 미해결 제품 결정이 없고 To Spec의 충실성·완전성·검증 가능성 자체검수를 통과했다는 계약 상태 예시일 뿐, 실제 제품 요구사항이나 실행 fixture가 아니다. 일반 non-UI 흐름에는 별도 initiative shaping이나 prototype이 필요하지 않다.

## Problem

가상의 일반 동작 하나를 현재 기준에 맞게 조정해야 한다.

## Desired Outcome

정의된 입력에서 조정된 동작을 관찰할 수 있다.

## Requirements

- 한 가지 non-UI 동작만 바꾼다.
- 기존에 명시되지 않은 제품 결정을 추가하지 않는다.
- 이 delivery는 정의된 대상 입력과 명시된 비대상 입력을 실행하고 각각의
  product result를 직접 읽을 ordinary product boundary와 readback을 만든다.

## Non-Goals

- UI 변경
- 큰 작업 탐색이나 prototype 작성
- 관련 없는 동작의 재설계

## Implementation Constraints

변경은 해당 동작과 직접 연결된 영역으로 제한한다.

## Verification Expectations

- Outcome: 정의된 입력에서 조정된 non-UI 동작을 관찰할 수 있다.
  Acceptance boundary: 정의된 입력을 받는 normal non-UI product boundary
  Trigger or inspection target: 정의된 입력을 normal product entry에 제공한다.
  Expected observable result: 조정된 동작의 product result가 반환된다.
  Authoritative readback: 같은 product entry가 반환한 product result
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 정의된 입력을 받는 ordinary product entry와 반환 결과
  External condition: None
- Outcome: 명시된 비대상 경로의 동작은 보존된다.
  Acceptance boundary: 비대상 입력을 받는 normal non-UI product boundary
  Trigger or inspection target: 명시된 비대상 입력을 normal product entry에 제공한다.
  Expected observable result: 비대상 경로의 기존 observable result가 유지된다.
  Authoritative readback: 같은 product entry가 반환한 product result
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 비대상 입력을 받는 ordinary product entry와 반환 결과
  External condition: None

## Behavior Authorities

- docs/planning/behavior/contexts/non-ui-operation.md | Scope: 정의된 입력에서 조정되는 non-UI 동작과 명시된 비대상 경로의 보존

## UI / UX

Not applicable

## Open Questions

None
