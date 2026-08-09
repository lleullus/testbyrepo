# 예시 initiative - Scope Shaping Result

Status: confirmed
Owner: 예시 planning owner
Project-Root: /home/user01/project/iis-skills/matt/examples/large-scope-shaping
Work-Slug: example-initiative
Planning-Shape: initiative

## Original Request

여러 독립 outcome을 포함할 수 있는 큰 변경을 계획한다.

## Investigation Assignments

- 연결된 outcome과 dependency 확인

## Verified Material Claims

### Claim 1

Classification: FACT
Primary Evidence: example planning record
Counterexample Tested: outcomes must ship together
Lead Finding: 첫 outcome은 독립적으로 수용할 수 있다.
Planning Relevance: DECOMPOSITION

첫 outcome과 sibling outcome은 독립적으로 수용 또는 연기할 수 있다.

## Planning Boundary

### Outcome

독립 outcome을 Work Package로 나누고 첫 package를 다음 planning unit으로 선택한다.

### Includes

- selected outcome과 sibling outcome의 경계

### Excludes

- 내부 구현 순서와 메커니즘

## Planning Constraints

- selected package는 sibling outcome을 변경하지 않는다.

## Candidate Outcome Areas

- selected outcome
- sibling outcome

## Decisions Reserved For Matt

- selected outcome의 정확한 observable contract

## Delivery Context

- 이 예시는 실행 fixture가 아닌 planning lineage 예시다.

## Outside The Assessed Landscape

None

## Unresolved Material Questions

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

### Release Cut

#### MVP

- WP-001

#### Next

None

#### Deferred

- WP-002

### Next Planning Units

- ./work-packages/WP-001.md

## Confirmation

Confirmed By: 예시 planning owner
Confirmed Scope: Planning Boundary, Planning Constraints, and Work Package proposal
