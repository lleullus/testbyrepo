# TICKET-001: 빈 설정 화면 안내문 우선 정보 계층

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/matt/verification/smoke-workspaces/flow-3
Worker:
UI: yes

## Goal

빈 설정 화면에서 안내문을 먼저 보이고, 그 뒤에 단일 주요 설정 버튼을 보이게 한다.

## Acceptance Criteria

- 좁은 화면의 빈 설정 화면에서 안내문이 단일 주요 설정 버튼보다 먼저 보인다.
- 넓은 화면의 빈 설정 화면에서 안내문이 단일 주요 설정 버튼보다 먼저 보인다.
- 두 화면 크기 모두에서 안내문 뒤에 단일 주요 설정 버튼이 보인다.
- 변경 검토에서 다른 화면은 이 Ticket 범위에 포함되지 않은 것이 확인된다.

## Scope

- 빈 설정 화면의 안내문과 주요 설정 버튼 정보 계층
- 좁은 화면과 넓은 화면의 해당 빈 상태 표현

## Non-Goals

- 다른 화면 변경
- 빈 설정 화면 외 상태의 UI 변경
- prototype code 또는 variant switcher의 제품 구현

## Blockers

None

## Verification

- 좁은 390x844와 넓은 1440x1000에서 빈 설정 화면을 수동 검토한다.
- 승인된 UI/UX 참조와 렌더링 순서를 대조한다.
- 변경 검토로 다른 화면이 범위에 포함되지 않았는지 확인한다.

## References

- ../UX-REFERENCE.md
- ../SPEC.md
