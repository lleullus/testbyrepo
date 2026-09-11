# TICKET-001: Transition Baseline and Autonomous Continuation Protocol Integration

Status: done
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/iis-skills
Worker:
UI: no

## Goal

운영자 부재 시 대규모 전환의 자율 완결을 위해, 경량 Transition Baseline 아티팩트 규약(BASELINE-NNN.template.md), Active Block 엔벨로프 프로젝션, 무인 자동 연속 주행 프로토콜, Goal 보존형 SAFE_INCOMPLETE_HANDOFF 예외, 전환 경로 제약 carry-forward를 iis-skills canonical 파일들에 통합한다.

## Acceptance Criteria

- iis-adaptive-planning/templates/BASELINE-NNN.template.md가 추가되고 전체 목표, 전역 불변식, 굵직한 Block 이정표, 진입/종료 조건, Safe Continuation, Safe Abort 필드를 완전하게 정의한다.
- iis-adaptive-planning/SKILL.md에 Transition Baseline 인입, 단일 Active Block Envelope Projection, 그리고 post-delivery completion disposition에 SAFE_INCOMPLETE_HANDOFF가 추가된다.
- references/09-run-contract.md의 Completion discipline에 Goal 보존형 SAFE_INCOMPLETE_HANDOFF 예외 조항 및 후속 invocation 자동 재구성 규약이 추가된다.
- scope-shaper/SKILL.md의 Planning Constraints에 전환 경로 불변식(path invariants)의 carry-forward 강제 규칙과 Re-entry Contract의 안전 인계 조건 명시 규약이 추가된다.
- 기존 pytest tests/ 및 check_run_contract.py가 결함 없이 100% 정상 통과하고 정합성이 유지된다.

## Scope

- /home/user01/project/iis-skills/iis-adaptive-planning/templates/BASELINE-NNN.template.md
- /home/user01/project/iis-skills/iis-adaptive-planning/SKILL.md
- /home/user01/project/iis-skills/iis-adaptive-planning/references/09-run-contract.md
- /home/user01/project/iis-skills/scope-shaper/SKILL.md

## Non-Goals

- 외부 workflow DB, persistent controller, progress dashboard 구축
- 독립 7종 Block 완료 평가 평면 도입

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1, 2, 3, 4, 5
  Behavior authority ordinals: 1
  Initial state: Transition Baseline 규약 및 SAFE_INCOMPLETE_HANDOFF 미반영 상태
  Trigger or inspection target: iis-skills 내 canonical 파일들 및 pytest tests/
  Acceptance boundary: Canonical file contents and pytest test execution
  Expected observable result: All 5 acceptance criteria are met, new template and skill sections exist, and pytest passes
  Authoritative readback: Direct canonical file inspection and pytest output
  Decision boundary: All required clauses and template are present with zero test regressions
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | /home/user01/project/iis-skills
  External condition: None

## Behavior Authorities

- docs/planning/behavior/contexts/transition-protocol.md | Scope: Transition Baseline and Autonomous Continuation Protocol Specification

## References

- ../SPEC.md
