# 단일 서비스 계정 JSON 내보내기의 공통 요청 연결

Status: approved
Owner: 테스트 사용자

## Problem

계정 내보내기 기능이 여러 서비스에 흩어져 있어 장기 통합의 시작점이 필요하다.

## Desired Outcome

기존 단일 서비스의 JSON 내보내기 한 경로가 새 공통 요청 형식으로도 연결되고, 이전 요청과 새 요청은 동일 결과를 낸다.

## Requirements

- 기존 단일 서비스의 JSON 내보내기 한 경로만 새 공통 요청 형식에 연결한다.
- 기존 이전 요청 경로는 유지한다.
- 이전 요청과 새 공통 요청의 동일 결과를 기존 통합 테스트로 검증한다.

## Non-Goals

- 다른 서비스 통합
- CSV 내보내기
- UI 변경
- 데이터 삭제

## Implementation Constraints

- 첫 구현 범위는 기존 단일 서비스의 JSON 내보내기 한 경로로 한정한다.
- 공통 요청 연결은 기존 경로의 결과를 바꾸지 않는다.
- 기존 통합 테스트를 검증 근거로 사용한다.

## Verification Expectations

- 기존 통합 테스트에서 이전 요청과 새 공통 요청의 동일 결과를 확인한다.
- 기존 단일 서비스 JSON 내보내기 경로가 이전 요청으로 유지되는지 확인한다.

## UI / UX

Not applicable

## Open Questions

None
