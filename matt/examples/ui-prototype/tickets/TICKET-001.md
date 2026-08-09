# TICKET-001: 채택된 UI 제시 순서 적용

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/iis-skills/matt/examples/ui-prototype
Worker:
UI: yes

이 문서의 `ready`는 승인된 Spec과 UI/UX 참조, 사용자 검토, 해결된 blocker를 나타내는 계약 상태 예시다. 실행 fixture나 실제 제품 요구사항이 아니며 구현 실행을 시작하지 않는다.

## Goal

승인된 UI/UX 결정에 맞춰 가상의 대상 화면의 제시 순서를 적용한다.

## Acceptance Criteria

- 대상 화면에서 필요한 정보가 하나의 주요 행동보다 먼저 보이는 것을 관찰할 수 있다.
- 좁은 화면과 넓은 화면에서 승인된 제시 순서가 유지되는 것을 확인할 수 있다.

## Scope

승인된 UI/UX 제시 순서와 그에 직접 연결된 기존 UI 검증으로 한정한다.

## Non-Goals

- 추가 화면 구성이나 상호작용 결정
- 채택되지 않은 prototype 선택지 반영
- Parent Spec 밖의 UI 변경

## Blockers

None

## Verification

실제 사용 시 좁은 화면과 넓은 화면에서 렌더링을 확인하고, `../UI-UX.md`의 승인된 결정과 대조한다.

## Behavior Authorities

- ../docs/planning/behavior/contexts/ui-information-action-order.md | Scope: 대상 화면에서 정보가 단일 주요 행동보다 먼저 제공되는 의미적 순서

## References

- ../UI-UX.md
- ../SPEC.md
- ../PROTOTYPE-NOTE.md

`../PROTOTYPE-NOTE.md`는 검토 배경이며 구현 권위가 아니다.
