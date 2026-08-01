# TICKET-001: 단일 서비스 JSON 내보내기 공통 요청 연결

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/matt/verification/smoke-workspaces/flow-2
Worker:
UI: no

## Goal

기존 단일 서비스의 JSON 계정 내보내기 한 경로를 새 공통 요청 형식으로도 사용할 수 있게 한다.

## Acceptance Criteria

- 새 공통 요청이 기존 단일 서비스의 JSON 내보내기 한 경로로 연결된다.
- 기존 통합 테스트에서 이전 요청과 새 공통 요청이 동일 결과를 반환하는 것이 관찰된다.
- 이전 요청을 통한 기존 단일 서비스 JSON 내보내기 경로가 유지되는 것이 기존 통합 테스트에서 관찰된다.

## Scope

- 기존 단일 서비스의 JSON 내보내기 한 경로
- 그 경로의 새 공통 요청 형식 연결
- 이전 요청과 새 공통 요청을 비교하는 기존 통합 테스트

## Non-Goals

- 다른 서비스 통합
- CSV 내보내기
- UI 변경
- 데이터 삭제

## Blockers

None

## Verification

- 기존 통합 테스트로 이전 요청과 새 공통 요청의 동일 결과를 확인한다.
- 기존 통합 테스트로 이전 요청의 JSON 내보내기 경로가 유지되는지 확인한다.

## References

- ../SPEC.md
- ../WAYFINDER.md

`../WAYFINDER.md`는 비권위 planning context다.
