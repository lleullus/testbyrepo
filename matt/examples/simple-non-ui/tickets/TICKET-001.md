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

대상 동작을 처리하는 영역과 다음 Scope-owned acceptance surface를 만드는
변경으로 한정한다: 정의된 입력을 받는 ordinary product entry와 반환 결과;
비대상 입력을 받는 ordinary product entry와 반환 결과.

## Non-Goals

- UI 변경
- initiative Scope result 또는 prototype 작성
- Parent Spec 밖의 제품 동작 변경

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1
  Behavior authority ordinals: 1
  Initial state: 정의된 대상 입력을 받을 ordinary product boundary가 구현되어 있다.
  Trigger or inspection target: 정의된 대상 입력을 ordinary product entry에 제공한다.
  Acceptance boundary: 정의된 대상 입력을 받는 ordinary non-UI product boundary
  Expected observable result: 조정된 동작의 product result가 반환된다.
  Authoritative readback: 같은 product entry가 반환한 product result
  Decision boundary: 반환 결과가 조정된 동작이면 충족하고 다른 동작이면 모순이다.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 정의된 입력을 받는 ordinary product entry와 반환 결과
  External condition: None
- Parent outcome ordinal: 2
  AC ordinals: 2
  Behavior authority ordinals: 1
  Initial state: 명시된 비대상 입력을 받을 ordinary product boundary가 구현되어 있다.
  Trigger or inspection target: 명시된 비대상 입력을 ordinary product entry에 제공한다.
  Acceptance boundary: 비대상 입력을 받는 ordinary non-UI product boundary
  Expected observable result: 비대상 경로의 기존 observable result가 유지된다.
  Authoritative readback: 같은 product entry가 반환한 product result
  Decision boundary: 반환 결과가 기존 observable result와 같으면 충족하고 다르면 모순이다.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | 비대상 입력을 받는 ordinary product entry와 반환 결과
  External condition: None

## Behavior Authorities

- docs/planning/behavior/contexts/non-ui-operation.md | Scope: 정의된 입력에서 조정되는 non-UI 동작과 명시된 비대상 경로의 보존

## References

- ../SPEC.md
