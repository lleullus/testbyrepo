# Transition Baseline & Autonomous Continuation Protocol - Scope Shaping Result

Status: confirmed
Owner: User
Project-Root: /home/user01/project/iis-skills
Work-Slug: transition-baseline-autonomous-continuation
Scope-Revision: SHAPE-001
Planning-Shape: bounded

## Original Request

운영자 실시간 개입이 불가한 무인/최소 터치 환경에서 대규모 시스템 전환(저장소 교체, authoritative source 이전, 레거시 청산)을 안전하게 자율 완결하기 위해, 사전 1회 승인 기반 '경량 Transition Baseline 아티팩트 규약(BASELINE-NNN.md)', 아우터 메인의 '단일 Active Block 엔벨로프 프로젝션(Context Slicing)', 블록 종료 후 무인 '자동 연속 주행(Auto-continuation)', Safe Continuation / Safe Abort 경계, 그리고 Goal 보존형 'SAFE_INCOMPLETE_HANDOFF'를 iis-skills 규약에 모순 없이 완전하고 정밀하게 반영한다.

## Intent Horizon

운영자가 장시간 자리를 비우거나 턴마다 개입하지 못하더라도, 에이전트가 사전 승인된 불변 전환 지형도(Transition Baseline)를 따라 각 단계(호환 레이어 -> 수렴 -> 컷오버 -> 정리)를 스스로 쪼개고 실행하며, 컨텍스트 과부하나 권위 분열 없이 대규모 전환을 안전하게 자율 완결하는 시스템 보장.

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

## Current Product State

- iis-adaptive-planning 및 references/09-run-contract.md는 단일 invocation 단위의 Run Contract 체결, coverage invariant, standing delegation을 소유하고 있으나, 목표 미완료 상태에서 세션을 안전하게 분리하는 SAFE_INCOMPLETE_HANDOFF 규약이 없음.
- Scope Shaper는 단일 next Increment를 선택하고 Atomic Exception을 지원하지만, 다중 invocation에 걸친 전환 경로 불변식(path invariants)의 carry-forward 규칙과 대단위 이정표 지형도(Transition Baseline) 프로젝션 규약이 없음.
- 굵직한 이정표(Transition Block) 단위의 사전 승인 템플릿(BASELINE-NNN.md) 및 caller 레벨의 무인 자동 연속 주행(Auto-continuation) 프로토콜 부재.

## Investigation Assignments

None

## Verified Material Claims

### Claim 1

Classification: FACT
Primary Evidence: /home/user01/project/iis-skills/iis-adaptive-planning/references/09-run-contract.md:342-344
Counterexample Tested: Goal이 미완료이지만 시스템이 안전한 중간 상태일 때 세션을 끊을 수 있는가?
Lead Finding: 현행 규율은 valid next action이 있으면 같은 invocation에서 계속하도록 강제하므로 safe incomplete handoff를 위한 명시적 예외가 필요함.
Planning Relevance: PLANNING_CONSTRAINT

### Claim 2

Classification: FACT
Primary Evidence: /home/user01/project/iis-skills/scope-shaper/SKILL.md:329-331
Counterexample Tested: HARD_ATOMIC을 여러 Scope Increment로 쪼갤 수 있는가?
Lead Finding: 중간 상태가 독립적이고 안전하지 않다면 Atomic Exception에 의해 단일 넓은 Increment로 묶여야 하므로, HARD_ATOMIC은 다중 Increment를 가질 수 없음.
Planning Relevance: BOUNDARY

## Planning Boundary

### Outcome

iis-skills 패키지 내에 경량 Transition Baseline 지형도 규약, 단일 Active Block 엔벨로프 격리 투영 규약, 무인 자동 연속 주행 프로토콜, Safe Incomplete Handoff 및 전환 제약 carry-forward 규약의 완전한 반영.

### Includes

- 경량 Transition Baseline 아티팩트 규약 및 표준 템플릿 (BASELINE-NNN.md)
- iis-adaptive-planning/SKILL.md 내 Active Block 선택, 엔벨로프 프로젝션, post-delivery disposition 확장 (SAFE_INCOMPLETE_HANDOFF)
- references/09-run-contract.md 내 Goal 보존형 SAFE_INCOMPLETE_HANDOFF 예외 및 후속 invocation 재구성 규칙
- scope-shaper/SKILL.md 내 전환 경로 불변식 carry-forward 및 Re-entry Contract의 안전 인계 조건 명시 규칙
- 기존 테스트 스위트의 정합성 유지 및 신규 규약 회귀 검증

### Excludes

- 무거운 외부 상주 워크플로 DB, 오케스트레이션 데몬, 에이전트 레지스트리 구축
- Transition Block 전용 7종 완료 평가 평면 (기존 4대 disposition에 흡수)
- rollback SQL 등 구현 종속적 메커니즘을 Baseline에 강제하는 행위

## Planning Constraints

- Baseline은 100% 명시적(Opt-in)이어야 하며 일반 IIS/Adaptive 요청에 자동 활성화되어서는 안 된다.
- Run Contract는 끝까지 invocation-local이어야 하며 durable resume state가 되지 않는다.
- HARD_ATOMIC 컷오버는 결코 여러 Scope Increment로 분할될 수 없다.

## Candidate Outcome Areas

None

## Product Capability Dependencies

None

## Decisions Reserved For Matt

- BASELINE-NNN.md의 마크다운 템플릿 헤더 및 필드 상세 표기법
- 09-run-contract.md 및 SKILL.md에 삽입될 조항의 구체적 문장 배치 및 섹션 명칭

## Delivery Context

- Python 3.12 환경, pytest 스위트 준수
- iis-skills 저장소 내 canonical skill 파일 직접 수정

## Outside The Assessed Landscape

- 타사 CI/CD 오케스트레이터(GitHub Actions, Temporal 등)와의 직접 연동 플러그인

## Construction Candidates

### Candidate A

Outcome Area: None
Current Product State: 전환 지형도 부재 및 무인 자율 인계 규약 부재
Target Product State: 경량 Transition Baseline 규약, 엔벨로프 격리 투영, 자동 연속 주행 프로토콜, SAFE_INCOMPLETE_HANDOFF, 전환 제약 carry-forward가 통합된 iis-skills 완성
Actor Or Operator: 시스템 운영자 및 Outer Main
Trigger Or Inspection Target: 대규모 전환 지시 및 canonical skill 파일들
Observable Result: 운영자가 1회 Baseline을 승인하면 아우터 메인이 컨텍스트 과부하 없이 1개 Block씩 자율 주행 및 무인 연속 실행을 완결할 수 있는 규약 체계 확립
Authoritative Readback: iis-skills 내 4개 핵심 파일 및 템플릿 검사, 테스트 통과
Durable Foundation: 이후 모든 대규모 전환 작업이 이 지형도와 자율 주행 규약을 표준으로 채택 가능
Future Policy Avoided: 복잡한 GUI 대시보드나 외부 워크플로 엔진 결합 배제
Lead Disposition: SELECT
Reason: 사용자의 핵심 요구사항을 100% 충족하는 가장 간결하고 직접적인 최소 충분 구현임

## Provisional Construction Horizon

None

## Selected Next Increment

### INC-001: Transition Baseline and Autonomous Continuation Protocol Specification

#### Work Package

None

#### Suggested Work Slug

transition-baseline-protocol

#### Selected Candidate

Candidate A

#### Current Product State

전환 지형도 부재 및 무인 자율 인계 규약 부재

#### Target Product State

경량 Transition Baseline 규약, 엔벨로프 격리 투영, 자동 연속 주행 프로토콜, SAFE_INCOMPLETE_HANDOFF, 전환 제약 carry-forward가 통합된 iis-skills 완성

#### Observable Outcome

Actor Or Operator: 시스템 운영자 및 Outer Main
Trigger Or Inspection Target: 대규모 전환 지시 및 canonical skill 파일들
Observable Result: 운영자가 1회 Baseline을 승인하면 아우터 메인이 컨텍스트 과부하 없이 1개 Block씩 자율 주행 및 무인 연속 실행을 완결할 수 있는 규약 체계 확립
Authoritative Readback: iis-skills 내 4개 핵심 파일 및 템플릿 검사, 테스트 통과

#### Includes

- 경량 Transition Baseline 아티팩트 규약 및 템플릿 (`BASELINE-NNN.md`)
- `iis-adaptive-planning/SKILL.md` 내 Active Block Envelope Projection 및 `SAFE_INCOMPLETE_HANDOFF` 반영
- `references/09-run-contract.md` 내 Goal 보존형 handoff 예외 및 successor 계약 재구성 규약 반영
- `scope-shaper/SKILL.md` 내 전환 경로 제약 carry-forward 및 Re-entry Contract 안전 조건 반영
- 5개 Required Named Items의 완전한 통합 및 테스트 통과

#### Excludes

- 외부 workflow DB, persistent controller, progress dashboard 구축
- 독립 7종 Block 완료 평가 평면 도입

#### Required Product Dependencies

None

#### Preserved Foundations

- 기존 IIS 권위 구조 (Product Thesis, Mandate, Scope Shaper, Run Contract) 및 coverage invariant 100% 보존

#### Decisions Reserved For Matt

- 정확한 섹션 배치 및 템플릿 텍스트 문구 세부 조율
#### Deferred Until Re-entry

None

#### Verification Boundary

iis-skills 내 canonical 파일 직접 검사, run_contract_check 도구 검증, pytest 테스트 스위트 검증

#### Re-entry Contract

INC-001 완료 후 5개 Required Named Items가 모두 반영되었는지 실측 검사

#### Delivery Context

- /home/user01/project/iis-skills 저장소 내 canonical 파일 수정
#### Artifact

./increments/INC-001.md

## Unresolved Material Questions

None

## Confirmation

Confirmed By: User
Confirmed Scope: Planning landscape, Planning Constraints, and exactly one Selected Next Increment; Decisions Reserved For Matt remain open and Provisional Construction Horizon remains non-normative
