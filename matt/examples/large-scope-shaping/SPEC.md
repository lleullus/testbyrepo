# 예시: initiative에서 선택한 작은 구현 범위

Status: approved
Owner: 예시 planning owner

이 문서의 `approved`는 confirmed Scope result와 selected ready Work Package에서 시작한 Ask Matt 결과를 사용자가 확인하고 Open Questions를 해소한 계약 상태 예시다. Scope result와 Work Package는 lineage와 planning context이며, 이 Spec과 adopted authorities가 실행 권위를 가진다. 이 예시는 실행 fixture나 실제 제품 요구사항이 아니다.

## Problem

가상의 큰 변경에서 실제로 구현할 첫 번째 작은 동작 경계를 정해야 한다.

## Desired Outcome

큰 변경 전체를 약속하지 않고, 선택한 한 동작의 완료 기준을 관찰할 수 있다.

## Requirements

- 탐색으로 좁힌 한 동작만 구현 범위로 확정한다.
- 확정한 범위는 selected Work Package 밖의 sibling outcome을 포함하지 않는다.

## Non-Goals

- 큰 변경 전체의 구현
- 다른 Work Package의 추가 채택
- UI 변경

## Implementation Constraints

이 Spec에 적힌 작은 범위를 넘기지 않으며, Scope result와 selected Work Package는 lineage와 context로만 참조한다.

## Verification Expectations

선택한 동작의 결과와 큰 변경의 비대상 영역이 바뀌지 않았음을 기존 프로젝트 검증으로 확인한다.

## Behavior Authorities

- ./docs/planning/behavior/contexts/selected-outcome.md | Scope: selected Work Package의 작은 non-UI 동작과 sibling outcome의 비대상 경계

## UI / UX

Not applicable

## Open Questions

None
