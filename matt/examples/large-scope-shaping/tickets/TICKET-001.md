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

승인된 Spec의 작은 동작과 다음 Scope-owned acceptance surface를 만드는
변경으로 한정한다: 선택한 동작의 ordinary product entry와 complete 반환 결과.

## Non-Goals

- 큰 변경 전체 구현
- sibling Work Package의 추가 채택
- UI 변경

## Blockers

None

## Verification

- AC ordinals: 1, 2
  Initial state: 선택한 동작의 ordinary product boundary와 complete result readback이 구현되어 있다.
  Trigger or inspection target: 확정한 입력을 선택한 동작의 ordinary product entry에 제공한다.
  Acceptance boundary: 선택한 동작의 complete product result
  Expected observable result: 작은 동작 결과가 반환되고 selected Work Package 밖 sibling outcome은 포함되지 않는다.
  Authoritative readback: 같은 product entry가 반환한 complete product result
  Decision boundary: complete result가 작은 동작 결과만 포함하면 충족하고 결과가 다르거나 sibling outcome을 포함하면 모순이다.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 선택한 동작의 ordinary product entry와 complete 반환 결과
  External condition: None
  Absence terminal condition: complete product result가 반환되면 이번 호출 결과에 추가 sibling outcome이 나타날 수 없다.

## Behavior Authorities

- ../docs/planning/behavior/contexts/selected-outcome.md | Scope: selected Work Package의 작은 non-UI 동작과 sibling outcome의 비대상 경계

## References

- ../SPEC.md
- ../docs/planning/scope-shaping/example-initiative/SCOPE-SHAPING-RESULT.md
- ../docs/planning/scope-shaping/example-initiative/work-packages/WP-001.md

Scope result와 Work Package는 lineage와 planning context이며 Spec 또는 Behavior authority를 대체하지 않는다.
