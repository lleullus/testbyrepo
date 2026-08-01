# TICKET-NNN: <제목>

Status: draft
Parent-Spec: ../SPEC.md
Project-Root: <유일하게 결정되는 절대 프로젝트 경로>
Worker:
UI: no

한 파일에는 독립적으로 관찰 가능한 하나의 desired-state Ticket만 적는다. 사용자의 검토가 끝나고 parent Spec이 `approved`이며, 모든 blocker가 해소되고, Acceptance Criteria가 관찰 가능하고, 프로젝트 경로가 유일하게 결정된 경우에만 `Status: ready`로 바꾼다. Ticket은 parent Spec의 범위를 확대하거나 뒤집지 않는다. Goal은 비규범적 요약이며 구현 의무의 유일한 위치가 될 수 없다. Blockers는 정확한 `None` 또는 경로-only 목록이어야 한다. `UI: yes`이면 승인된 UI/UX 문서를 레이블이나 backtick 없는 경로-only 목록 항목으로 References에 추가한다.

## Goal

Acceptance Criteria, Scope, Non-Goals, Blockers, Verification에 완전히
표현된 desired outcome을 비규범적으로 요약한다.

## Acceptance Criteria

완료 여부를 관찰할 수 있는 결과와 보존 invariant를 적는다.
예상 원인, 파일, endpoint, abstraction 또는 구현 순서를 조건으로
만들지 않는다.

## Scope

변경을 허용하는 제품·subsystem·integration·문서 또는 운영 경계를
적는다. 아직 관찰하지 않은 정확한 미래 파일 목록을 요구하지 않는다.

## Non-Goals

이 Ticket에서 하지 않을 일을 명시한다.

## Blockers

None

## Verification

Acceptance Criteria를 관찰할 안정적인 결과 또는 검증 경계를 적는다.
실제 focused test seam은 Implementation Lead가 현재 저장소를 보고 선택한다.

## References

- ../SPEC.md
