# 예시: 큰 변경에서 확정한 작은 구현 범위

Status: approved
Owner: 예시 planning owner

이 문서의 `approved`는 사용자가 확인하고 Open Questions가 해소된 계약 상태 예시다. `WAYFINDER.md`는 탐색 배경일 뿐 구현 권위가 아니며, 이 Spec에 기록된 범위만 권위가 있다. 이 예시는 실행 fixture나 실제 제품 요구사항이 아니다.

## Problem

가상의 큰 변경에서 실제로 구현할 첫 번째 작은 동작 경계를 정해야 한다.

## Desired Outcome

큰 변경 전체를 약속하지 않고, 선택한 한 동작의 완료 기준을 관찰할 수 있다.

## Requirements

- 탐색으로 좁힌 한 동작만 구현 범위로 확정한다.
- 확정한 범위는 Wayfinder의 다른 후보에 의존하지 않는다.

## Non-Goals

- 큰 변경 전체의 구현
- Wayfinder의 모든 후보 채택
- UI 변경

## Implementation Constraints

이 Spec에 적힌 작은 범위를 넘기지 않으며, Wayfinder는 배경 정보로만 참조한다.

## Verification Expectations

선택한 동작의 결과와 큰 변경의 비대상 영역이 바뀌지 않았음을 기존 프로젝트 검증으로 확인한다.

## UI / UX

Not applicable

## Open Questions

None
