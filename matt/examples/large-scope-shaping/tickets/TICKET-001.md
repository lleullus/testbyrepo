# TICKET-001: initiative에서 선택한 작은 동작 구현

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/iis-skills/matt/examples/large-scope-shaping
Worker:
UI: no

이 문서의 `ready`는 승인된 Spec과 사용자 검토 후의 계약 상태 예시다. 실행 fixture나 실제 제품 요구사항이 아니며 구현 실행을 시작하지 않는다.

## Goal

Parent Spec에서 확정한 작은 non-UI 동작 하나를 완료한다.

## Acceptance Criteria

- 확정한 입력 조건에서 작은 동작의 결과를 관찰할 수 있다.
- 큰 변경의 다른 후보 영역이 이번 변경으로 수정되지 않았음을 확인할 수 있다.

## Scope

승인된 Spec의 작은 동작과 그에 직접 연결된 기존 검증으로 한정한다.

## Non-Goals

- 큰 변경 전체 구현
- sibling Work Package의 추가 채택
- UI 변경

## Blockers

None

## Verification

- 실제 사용 시 대상 프로젝트의 기존 검증으로 Acceptance Criteria와 비대상 영역을 확인한다.

## Behavior Authorities

- ../docs/planning/behavior/contexts/selected-outcome.md | Scope: selected Work Package의 작은 non-UI 동작과 sibling outcome의 비대상 경계

## References

- ../SPEC.md
- ../docs/planning/scope-shaping/example-initiative/SCOPE-SHAPING-RESULT.md
- ../docs/planning/scope-shaping/example-initiative/work-packages/WP-001.md

Scope result와 Work Package는 lineage와 planning context이며 Spec 또는 Behavior authority를 대체하지 않는다.
