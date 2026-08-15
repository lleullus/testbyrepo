# 예시 initiative - Scope Shaping Result

Status: confirmed
Owner: 예시 planning owner
Project-Root: /home/user01/project/iis-skills/matt/examples/large-scope-shaping
Work-Slug: example-initiative
Scope-Revision: SHAPE-001
Planning-Shape: initiative

## Original Request

여러 독립 outcome을 포함할 수 있는 큰 변경을 계획하되 실제 구축은 첫 durable product state 하나부터 진행한다.

## Intent Horizon

selected outcome과 sibling outcome을 장기적으로 모두 지원하되 각 구축 단계는 실제 제품 상태를 다시 확인하며 선택한다.

## Current Product State

- selected outcome과 sibling outcome의 새 동작은 아직 존재하지 않는 예시 baseline이다.

## Investigation Assignments

None

## Verified Material Claims

### Claim 1

Classification: FACT
Primary Evidence: example planning record
Counterexample Tested: outcomes must ship together
Lead Finding: selected outcome은 sibling outcome 없이도 독립적으로 수용할 수 있다.
Planning Relevance: DECOMPOSITION

selected outcome과 sibling outcome은 독립적으로 수용 또는 연기할 수 있다.

### Claim 2

Classification: INFERENCE
Primary Evidence: example planning record
Counterexample Tested: 첫 단계가 기술 준비 작업뿐인 경우
Lead Finding: selected outcome의 observable result를 첫 durable Increment로 만들 수 있다.
Planning Relevance: CONSTRUCTION

첫 구축 단계는 기술 scaffold가 아니라 selected outcome의 완결된 observable product result여야 한다.

## Planning Boundary

### Outcome

독립 outcome의 전체 지형을 보존하면서 selected outcome의 첫 durable product state만 현재 구축 대상으로 선택한다.

### Includes

- selected outcome과 sibling outcome의 독립 경계
- selected outcome의 첫 observable construction state

### Excludes

- sibling outcome의 현재 구현
- 내부 구현 순서와 메커니즘

## Planning Constraints

- selected outcome은 sibling outcome을 변경하지 않는다.

## Candidate Outcome Areas

- selected outcome
- sibling outcome

## Product Capability Dependencies

None

## Decisions Reserved For Matt

- selected outcome의 정확한 observable contract

## Delivery Context

- 이 예시는 실행 fixture가 아닌 planning lineage 예시다.

## Outside The Assessed Landscape

None

## Work Package Proposal

### Split / Merge Decisions

#### selected / sibling

Decision: SPLIT
Independent Acceptance Test: selected outcome을 sibling 없이 수용할 수 있다.
Counterexample Tested: 두 outcome이 반드시 함께 필요하다.
Lead Finding: 독립 package가 적절하다.
Supporting Material Claims: Claim 1

### Proposed Work Packages

#### WP-001: Selected outcome

##### Outcome

선택한 작은 non-UI 동작의 결과를 관찰할 수 있다.

##### Includes

- selected outcome

##### Excludes

- sibling outcome

##### Depends On

None

##### Why This Is One Package

하나의 독립 acceptance boundary다.

##### Why It Is Separate

sibling outcome 없이 수용할 수 있다.

##### Decisions Reserved For Matt

- 정확한 observable contract

#### WP-002: Sibling outcome

##### Outcome

sibling outcome을 별도로 계획할 수 있다.

##### Includes

- sibling outcome

##### Excludes

- selected outcome

##### Depends On

None

##### Why This Is One Package

별도 acceptance boundary다.

##### Why It Is Separate

selected outcome과 독립적으로 연기할 수 있다.

##### Decisions Reserved For Matt

None

### Outcome Horizon

#### Foundation

- WP-001

#### Expansion

None

#### Deferred

- WP-002

## Construction Candidates

### Candidate A

Outcome Area: WP-001
Current Product State: selected outcome의 새 동작이 아직 없다.
Target Product State: selected outcome의 작은 non-UI 동작을 실제 제품 경계에서 완료하고 결과를 다시 확인할 수 있다.
Actor Or Operator: 사용자
Trigger Or Inspection Target: selected outcome의 ordinary product flow를 실행한다.
Observable Result: 완전한 selected outcome product result가 생성된다.
Authoritative Readback: ordinary product boundary에서 complete product result를 다시 확인한다.
Durable Foundation: 이후 sibling이나 확장 기능이 추가되어도 selected outcome의 observable contract는 유지된다.
Future Policy Avoided: sibling outcome과 이후 확장 정책은 현재 결정하지 않는다.
Lead Disposition: SELECT
Reason: 현재 상태에서 가장 작은 durable observable product result다.

## Provisional Construction Horizon

- selected outcome이 실제로 전달된 뒤 sibling outcome 또는 다음 확장을 다시 Scope Shaping한다.

## Selected Next Increment

### INC-001: Selected outcome first durable state

#### Work Package

WP-001

#### Suggested Work Slug

selected-outcome

#### Selected Candidate

Candidate A

#### Current Product State

selected outcome의 새 동작이 아직 없다.

#### Target Product State

selected outcome의 작은 non-UI 동작을 실제 제품 경계에서 완료하고 결과를 다시 확인할 수 있다.

#### Observable Outcome

Actor Or Operator: 사용자
Trigger Or Inspection Target: selected outcome의 ordinary product flow를 실행한다.
Observable Result: 완전한 selected outcome product result가 생성된다.
Authoritative Readback: ordinary product boundary에서 complete product result를 다시 확인한다.

#### Includes

- selected outcome

#### Excludes

- sibling outcome

#### Required Product Dependencies

None

#### Preserved Foundations

- selected outcome의 observable contract

#### Decisions Reserved For Matt

- 정확한 observable contract

#### Deferred Until Re-entry

- sibling outcome과 이후 확장 정책

#### Verification Boundary

selected outcome의 ordinary product boundary에서 실행 결과와 authoritative readback을 관찰한다.

#### Re-entry Contract

INC-001 delivery 이후 실제 selected outcome이 존재하고 readback 가능한지 직접 확인한 다음 다음 Increment를 선택한다.

#### Delivery Context

- 이 예시는 실행 fixture가 아닌 planning lineage 예시다.

#### Artifact

./increments/INC-001.md

## Unresolved Material Questions

None

## Confirmation

Confirmed By: 예시 planning owner
Confirmed Scope: Planning landscape, Work Package decomposition, Planning Constraints, and exactly one Selected Next Increment; Decisions Reserved For Matt remain open and Provisional Construction Horizon remains non-normative
