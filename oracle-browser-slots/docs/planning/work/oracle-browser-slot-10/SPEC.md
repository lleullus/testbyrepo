# Oracle Browser Managed Slot 10

Status: approved
Owner: user

## Problem

Oracle Browser의 관리 슬롯 계약은 새로 승인된 슬롯 10의 운영 경계와 실행 적격성을 제품 전반에서 일관되게 제공해야 한다. 이 계약이 완결되지 않으면 슬롯 10이 일부 흐름에서만 보이거나 기존 슬롯과 다른 의미로 동작할 수 있다.

## Desired Outcome

슬롯 10이 기존 슬롯 1~5를 보존하는 추가 관리 슬롯으로 제공되고, 준비와 상태 조회부터 초기 managed 실행, 자동 배정 및 원 세션 followup까지 승인된 관리 슬롯 behavior가 일관되게 적용된다.

## Requirements

- Oracle Browser의 관리 슬롯 동작은 채택된 Behavior authority의 적용 범위 전체에서 슬롯 10을 지원해야 한다.
- 슬롯 10 추가로 영향을 받는 관찰 가능한 제품 흐름은 동일한 승인 Behavior authority를 일관되게 따라야 한다.
- 슬롯 10의 계정 운영 적합성에 관한 책임 경계는 승인 Behavior authority를 따라야 한다.

## Non-Goals

- 슬롯 6~9 또는 그 밖의 새 관리 슬롯 ID 추가
- 슬롯별 계정 신원 식별 또는 비교
- 계정 구독, 모델 권한 또는 workspace 권한 자동 검증
- managed followup의 다른 슬롯 fallback
- 기존 슬롯 1~5의 capability 또는 호환 후보 내 상대 순서 변경
- UI 변경

## Implementation Constraints

- 관리 슬롯의 사용자 관찰 가능 의미는 채택된 Behavior authority와 일치해야 한다.
- 승인된 제품 계약을 만족하는 내부 구조, 구현 경로 및 작업 순서는 Implementation Lead에 위임한다.

## Verification Expectations

- 슬롯 10의 준비 및 상태 조회 흐름에서 채택된 관리 슬롯 scope의 결과를 관찰할 수 있어야 한다.
- 슬롯 10이 호환되는 각 capability의 초기 managed 실행 및 자동 배정 흐름에서 채택된 관리 슬롯 scope의 결과를 관찰할 수 있어야 한다.
- 슬롯 10에서 시작된 managed session의 followup을 슬롯 가용, 점유 및 unavailable 조건에서 관찰해 채택된 원 슬롯 연속성 scope를 확인할 수 있어야 한다.
- 지원되지 않는 슬롯 ID, 동시 점유 및 중복 요청 조건에서 채택된 관리 슬롯 경계를 관찰할 수 있어야 한다.
- 슬롯 10 추가 전후로 기존 슬롯 1~5의 관찰 가능한 capability와 상대 순서가 보존됨을 확인할 수 있어야 한다.
- 로그인 성공과 운영자 책임 범위가 구분됨을 관찰 가능한 준비 및 실행 결과로 확인할 수 있어야 한다.

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성

## UI / UX

Not applicable

## Open Questions

None
