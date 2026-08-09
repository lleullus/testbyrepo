# TICKET-001: 일반 non-UI 동작 한 가지 변경

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/iis-skills/matt/examples/simple-non-ui
Worker:
UI: no

이 문서의 `ready`는 승인된 Spec, 사용자 검토, 해결된 blocker를 나타내는 계약 상태 예시다. 실행 fixture나 실제 제품 요구사항이 아니며 구현 실행을 시작하지 않는다.

## Goal

Parent Spec에 정의된 가상의 non-UI 동작 한 가지를 변경한다.

## Acceptance Criteria

- 정의된 입력 조건에서 변경된 동작을 관찰할 수 있다.
- 명시된 비대상 경로의 동작이 바뀌지 않았음을 확인할 수 있다.

## Scope

대상 동작을 처리하는 영역과 그에 직접 연결된 기존 검증만 변경할 수 있다.

## Non-Goals

- UI 변경
- initiative Scope result 또는 prototype 작성
- Parent Spec 밖의 제품 동작 변경

## Blockers

None

## Verification

- 실제 사용 시 대상 프로젝트의 기존 검증 방법으로 두 Acceptance Criteria를 확인한다.

## Behavior Authorities

- ../docs/planning/behavior/contexts/non-ui-operation.md | Scope: 정의된 입력에서 조정되는 non-UI 동작과 명시된 비대상 경로의 보존

## References

- ../SPEC.md
