# Transition Baseline & Autonomous Continuation Protocol Specification

Status: approved
Owner: User
Source-Increment: docs/planning/scope-shaping/transition-baseline-autonomous-continuation/increments/INC-001.md

## Product Meaning Binding

Schema: iis-product-meaning/v1
Fingerprint: sha256:f94dd842beef044aceead9be675ee4867106baea1988937d7d839522d673f3c4

Core Utility:
운영자의 실시간 개입이나 턴별 승인이 불가능한 환경에서도, 사전 1회 승인된 전환 지형도(Transition Baseline)의 굵직한 이정표(Transition Block)별로 아우터 메인의 작업 문맥을 엄격히 격리(Context Slicing)하여 과부하를 차단하고, 각 Block의 실제 Exit 검증을 거쳐 사람 없이 다음 단계로 자동 연속 주행(Auto-continuation)함으로써 최종 전환을 안전하게 자율 완결하며, 장애 시 비상 안전 상태(Safe Abort)로 자율 복구하는 보장.

Core Completion Loop:
운영자의 1회 사전 지형도 승인 -> 아우터 메인의 단일 Active Block 문맥 격리(Envelope Projection) -> Block 내부 세부 시공 및 실측 검증 -> 실측 기반 Block Exit 판정 -> caller/host의 무인 자동 연속 주행(Auto-continuation) -> 비상 시 Safe Abort 복구 -> 최종 Transformation Outcome 실측 완결.

Required Outcomes / Means:
- 경량 Transition Baseline 아티팩트 규약 및 템플릿 (BASELINE-NNN.md)
- 아우터 메인 Active Block 엔벨로프 프로젝션 규약
- 무인 자동 연속 주행(Auto-continuation) 규약
- Goal 보존형 SAFE_INCOMPLETE_HANDOFF 규약
- 전환 경로 제약 carry-forward 규약

Truth / Causal Invariants:
- Transition Baseline은 일반 작업에 자동 생성되지 않으며 명시적 Opt-in과 1회 사전 승인으로만 활성화된다.
- 아우터 메인은 전체 거대 지형도를 작업 문맥에 올리지 않고 단일 Active Block Envelope만을 Scope Shaper에 격리 전달한다.
- 1회 사전 승인은 Block 간 자동 계속 실행 권위를 포함하며, Block Exit 실측 시 사람 개입 없이 후속 invocation이 자율 기동된다.
- 각 세션의 Run Contract는 Block 실행에 한정되지만 원래의 전체 Goal은 상위 위임으로 온전히 보존된다.
- 무인 환경일수록 중간 티켓/배치 완료는 전환 완료 증거가 될 수 없으며 최종 authoritative readback 실측만으로 완료를 판정한다.
- 중간 인계가 금지된 원자적 컷오버(HARD_ATOMIC)는 다중 Scope Increment로 쪼갤 수 없으며 단일 Increment 내부 실행 단위로 한정된다.

Success Observation:
운영자가 초기 경량 Baseline을 1회 승인하고 자리를 비웠을 때, 아우터 메인이 한 번에 1개 Block씩 문맥을 좁혀 스스로 쪼개고 실행하며, 컨텍스트 붕괴나 사람 호출 없이 수 차례의 후속 세션을 자율 연속 기동하여 전체 전환을 순차 완결하고, 최종 신규 권위 확립이 authoritative readback으로 증명되는 상태.

## Problem

대규모 전환 과제에서 운영자가 실시간 개입할 수 없을 때, 아우터 메인이 거대한 단일 목표를 한 번에 쪼개려다 컨텍스트가 과부하되거나, 중간에 인계할 안전 기준이 없어 시스템이 위험한 과도 상태에 방치되거나, 배치 성공을 전환 완료로 오인하는 결함이 발생한다.

## Desired Outcome

iis-skills 패키지 내에 경량 Transition Baseline 지형도 규약, 단일 Active Block 문맥 격리 프로젝션, 무인 자동 연속 주행 프로토콜, SAFE_INCOMPLETE_HANDOFF, 전환 제약 carry-forward가 canonical 규약과 템플릿으로 통합되어 무인 전환의 안전한 자율 완결을 보장한다.

## Requirements

1. `iis-adaptive-planning/templates/BASELINE-NNN.template.md` 신설: 전체 목표, 전역 불변식, 굵직한 Block 이정표, 진입/종료 조건, Safe Continuation, Safe Abort 정의.
2. `iis-adaptive-planning/SKILL.md`: Active Block 선택, 단일 Active Block Envelope 프로젝션 규약, post-delivery completion disposition에 `SAFE_INCOMPLETE_HANDOFF` 추가.
3. `iis-adaptive-planning/references/09-run-contract.md`: Completion discipline 내 Goal 보존형 `SAFE_INCOMPLETE_HANDOFF` 예외 조항 추가 및 후속 invocation 자동 재구성 규약 추가.
4. `scope-shaper/SKILL.md`: Planning Constraints 내 전환 경로 불변식(path invariants)의 carry-forward 강제 규칙 및 Re-entry Contract의 안전 인계 조건(Safe Continuation Predicate) 명시 규약 추가.
5. 기존 IIS 권위 체계 및 300+개 기존 테스트 스위트와의 100% 정합성 유지.

## Non-Goals

- 무거운 외부 상주 워크플로 DB, 오케스트레이터 데몬, 에이전트 레지스트리 구축
- Transition Block 전용 7종 완료 평가 평면 도입 (기존 4대 disposition에 통합)
- 임의 rollback SQL 처방

## Implementation Constraints

- Transition Baseline은 100% 명시적(Opt-in)으로만 활성화되어야 함.
- Run Contract는 끝까지 invocation-local이어야 함.
- HARD_ATOMIC 컷오버는 단일 Increment 내부 실행으로 엄격히 한정됨.

## Verification Expectations

- Outcome: Transition Baseline and Autonomous Continuation Protocol Integrated
  Acceptance boundary: Canonical file inspection and existing test suite execution
  Trigger or inspection target: iis-skills repository canonical files and pytest tests/
  Expected observable result: All 5 Required Named Items are fully integrated and all tests pass with zero regressions
  Authoritative readback: Direct file readback and pytest test results
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | /home/user01/project/iis-skills
  External condition: None

## Behavior Authorities

- docs/planning/behavior/contexts/transition-protocol.md | Scope: Transition Baseline and Autonomous Continuation Protocol Specification

## Open Decisions

None
