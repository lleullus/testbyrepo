---
title: "DDD-lite 도메인 안전 계층"
status: oracle-reviewed
date: 2026-06-16
tags:
  - llm
  - ddd
  - domain-driven-design
  - domain-safety
  - bounded-context
  - oracle-review
---
> [!oracle] Oracle Browser 3턴 토의 최종 결론
> **이 프로젝트는 DDD를 전면 도입할 필요가 없습니다.**
> 대신 DDD에서 **LLM의 추측을 줄이고, 변경 범위를 제한하고, 도메인 오류를 자동 검출하는 부분만 흡수**해야 합니다.
>
> DDD를 아키텍처 방법론으로 도입하지 말고, **LLM-safe domain boundary system**으로 재해석해서 도입하라.
>
> 핵심 원칙: **No DDD artifact without executable consequence.**
> 실행 가능한 결과가 없는 DDD 산출물은 만들지 않는다.

---

## 1. 이 프로젝트에 필수인 DDD 원칙

### 1.1 공통 언어: 필수

LLM 바이브 코딩 환경에서 공통 언어는 선택이 아니라 필수입니다.

LLM은 용어를 보고 의미를 추론합니다. 따라서 `cancel`, `delete`, `refund`, `void`, `rollback`, `reverse`, `expire` 같은 단어가 뒤섞이면 높은 확률로 잘못된 코드를 만듭니다.

공통 언어는 단순 용어집이 아니라 **LLM용 의미 타입 시스템**입니다.

필수로 정리해야 할 것:

```text
- 도메인 핵심 용어
- 금지어
- 혼동하기 쉬운 용어 쌍
- 코드 네이밍 규칙
- 이벤트/상태/행위 이름의 의미
- 이 용어가 의미하지 않는 것
```

예:

```md
## Refund

Meaning:
이미 capture된 금액의 일부 또는 전부를 고객에게 반환하는 행위.

Must not mean:
- 결제 승인 취소
- 주문 취소
- DB row 삭제
- 정산 취소

Forbidden:
- Authorization 취소를 refund라고 부르지 않는다.
- captured payment에 void라는 용어를 사용하지 않는다.
```

---

### 1.2 도메인 불변식과 소유권: 필수

현재 프로젝트가 이미 가장 잘 잡고 있는 부분입니다. 다만 DDD 관점에서 보완해야 할 점은 **불변식의 소유자**입니다.

현재 방향:

```text
환불 금액은 원 결제 금액을 초과할 수 없다.
취소된 주문은 배송 생성이 불가능하다.
```

여기에 추가해야 할 것:

```text
이 불변식은 어느 컨텍스트가 소유하는가?
어느 코드 경로에서만 변경 가능한가?
어느 테스트가 이 규칙을 고정하는가?
다른 모듈이 이 규칙을 재구현해도 되는가?
```

예:

```md
## Invariant: Refund amount must not exceed captured amount

Owner:
Billing Context

Allowed mutation point:
Payment.refund()
RefundPolicy.calculateRefundableAmount()

Forbidden:
Order module must not calculate refundable amount directly.
Shipping module must not infer payment refundability.

Executable checks:
tests/domain-invariants/billing/refund-amount.test.ts
tests/contracts/order-billing/refund-request.contract.test.ts
```

이게 DDD의 실질적 가치입니다.
단순히 "규칙이 있다"가 아니라 **규칙의 책임 위치를 고정**합니다.

---

### 1.3 바운디드 컨텍스트 / 의미적 모듈 경계: 필수

현재의 `module-boundaries.md`는 매우 중요합니다. 여기에 DDD를 더한다면 방향은 "폴더 구조 설명"이 아니라 **의미적 소유권 지도**가 되어야 합니다.

모듈 경계는 이렇게만 쓰면 부족합니다.

```text
Order는 BillingRepository를 import하면 안 된다.
Shipping은 OrderEntity를 import하면 안 된다.
```

DDD적으로는 이렇게 확장해야 합니다.

```text
Order owns:
- 주문 상태
- 주문 취소 가능 여부
- 주문 총액 계산

Billing owns:
- 결제 승인
- 매입
- 환불 가능 금액
- 정산 상태

Shipping owns:
- 배송 생성
- 배송 취소
- 배송 완료
```

LLM에게 중요한 것은 "어디를 import할 수 있는가"뿐 아니라 **어디서 판단해야 하는가**입니다.

---

### 1.4 컨텍스트 맵: 필수에 가깝다

10만 줄 이상 코드베이스에서 LLM이 가장 자주 실패하는 지점은 "무엇을 읽고 무엇을 무시해야 하는가"입니다.

컨텍스트 맵은 DDD 문서라기보다 **retrieval routing 문서**로 봐야 합니다.

예:

```md
## Order → Billing

Relationship:
Order requests payment operations from Billing.

Allowed communication:
- BillingPort.authorizePayment()
- BillingPort.requestRefund()
- PaymentAuthorized event
- PaymentFailed event

Forbidden:
- Order must not import BillingPaymentEntity.
- Order must not read billing database tables.
- Order must not calculate refundable amount.

Relevant checks:
- boundary:order-billing
- tests/contracts/order-billing/*
- tests/domain-invariants/billing/*
```

이 문서가 있으면 LLM은 작업 전에 읽어야 할 범위를 좁힐 수 있습니다.

---

### 1.5 고위험 변경 분류: 필수

DDD를 LLM 환경에 맞게 흡수하려면 "어떤 변경은 바로 맡기면 안 된다"는 기준이 있어야 합니다.

필수로 분류해야 할 고위험 변경:

```text
- aggregate boundary 변경
- 도메인 상태 전이 변경
- 결제/환불/정산/권한/재고 규칙 변경
- 기존 도메인 이벤트 의미 변경
- repository contract 변경
- context 간 의존 방향 변경
- 금지 import 예외 추가
- migration이 도메인 핵심 테이블을 건드리는 경우
```

이건 DDD라기보다 **LLM 작업 안전 프로토콜**입니다.

---

## 2. 선택적이거나 불필요한 DDD 요소

### 2.1 전역 Aggregate Catalog: 선택적

전역 문서로 만들지 않는 편이 낫습니다.

이유:

```text
- 문서가 빨리 낡을 수 있음
- 모든 객체를 aggregate처럼 모델링하려는 유혹이 생김
- LLM이 패턴 이름을 보고 과도한 구조를 생성할 수 있음
- 실제 트랜잭션 경계와 문서상 aggregate가 어긋나면 더 위험함
```

대신 고위험 컨텍스트에만 국소적으로 둡니다.

예:

```text
docs/domain/billing/aggregates.md
docs/domain/order/aggregates.md
```

적용 조건:

```text
- 상태 전이가 중요하다
- 금전/권한/재고/정산처럼 오류 비용이 크다
- 한 트랜잭션 안에서 지켜야 하는 불변식이 있다
- 외부 직접 변경을 반드시 막아야 한다
```

---

### 2.2 모든 모델의 Entity / Value Object화: 불필요

값 객체는 유용하지만, 모든 primitive를 클래스로 감싸는 것은 오히려 해롭습니다.

도입할 만한 값 객체:

```text
- Money
- Email
- OrderId
- PaymentId
- DateRange
- Quantity
- Percentage
- Currency
```

도입하지 않아도 되는 것:

```text
- 단순 표시용 문자열
- 내부 UI 상태값
- 일회성 DTO 필드
- 도메인 불변식과 무관한 값
```

기준은 이것입니다.

> 값 객체가 잘못된 값을 만들지 못하게 막는다면 도입한다.
> 단지 DDD스럽게 보이기 위한 wrapper라면 도입하지 않는다.

---

### 2.3 Repository 패턴 일괄 적용: 불필요

Repository는 도메인과 영속성을 분리할 때 유용합니다. 하지만 모든 테이블마다 repository interface를 만들면 보일러플레이트가 늘고 LLM이 수정해야 할 파일 수가 증가합니다.

도입 기준:

```text
Repository를 둘 만한 경우:
- 도메인 로직이 ORM에 오염되고 있다
- 테스트에서 영속성 의존을 끊어야 한다
- aggregate 저장/복원이 명확한 의미를 갖는다
- 여러 storage 구현이 실제로 필요하다

Repository가 과한 경우:
- 단순 CRUD
- admin/backoffice 조회
- 도메인 규칙 없는 read model
- ORM query wrapper에 불과한 경우
```

---

### 2.4 Domain Service 남발: 불필요

`DomainService`는 LLM이 가장 쉽게 잡동사니 유틸 클래스로 만드는 패턴입니다.

도입 기준:

```text
도입할 만한 경우:
- 특정 Entity나 Value Object에 넣기 어려운 순수 도메인 판단
- 여러 aggregate를 읽지만 하나의 도메인 결정을 내리는 경우
- 정책 이름이 코드에 드러나야 하는 경우

피해야 할 경우:
- application orchestration
- repository 호출 묶음
- 외부 API 호출
- 단순 util 함수 모음
```

가능하면 이름을 `DomainService`보다 구체적으로 붙이는 편이 낫습니다.

```text
RefundEligibilityPolicy
ShipmentCreationPolicy
OrderCancellationPolicy
```

---

### 2.5 도메인 이벤트 남발: 선택적

도메인 이벤트는 사이드이펙트 누락을 줄일 수 있지만, 남발하면 LLM이 실행 경로를 추적하기 어려워집니다.

도입할 만한 경우:

```text
- 여러 컨텍스트가 같은 도메인 사실에 반응해야 한다
- producer/consumer가 명확하다
- 이벤트 계약 테스트가 가능하다
- 이벤트가 의미하는 것과 의미하지 않는 것을 문서화할 수 있다
```

피해야 할 경우:

```text
- 단순 함수 호출을 이벤트로 바꾸는 경우
- 같은 컨텍스트 내부 흐름을 불필요하게 비동기화하는 경우
- 이벤트 이름만 있고 계약 테스트가 없는 경우
- 이벤트 순서와 실패 처리가 불명확한 경우
```

---

### 2.6 패턴 중심 폴더 구조: 불필요하거나 위험

다음 구조는 겉보기에는 DDD스럽지만 LLM 환경에서는 위험할 수 있습니다.

```text
domain/
  entities/
  value-objects/
  services/
  repositories/
  events/
```

이 구조는 도메인 의미보다 패턴을 먼저 보게 만듭니다.

더 나은 구조는 컨텍스트 중심입니다.

```text
modules/
  billing/
    domain/
    application/
    infrastructure/
    tests/
  order/
    domain/
    application/
    infrastructure/
    tests/
```

LLM에게 중요한 것은 "이게 Entity인가?"보다 "이게 Billing의 무엇인가?"입니다.

---

## 3. 현재 문서 구조 수정/보완안

### 3.1 `01. 실행 가능한 명세` 보완

현재:

```text
1. 실행 가능한 명세
- 테스트, 타입, 린트, 빌드, 계약 테스트, 도메인 불변식
```

추가 문서:

```text
docs/01-executable-specs/
  immune-system.md
  domain-invariant-tests.md
  contract-tests.md
  boundary-checks.md
  invariant-index.md
```

#### 추가: `invariant-index.md`

역할:

```text
도메인 불변식 ↔ 소유 컨텍스트 ↔ 테스트 파일 ↔ 관련 모듈 ↔ 위험도 연결
```

템플릿:

```md
# Domain Invariant Index

## INV-BILLING-001: Refund amount must not exceed captured amount

Owner:
Billing

Rule:
Refund amount must be less than or equal to captured amount.

Allowed mutation points:
- modules/billing/domain/payment.ts
- modules/billing/domain/refund-policy.ts

Forbidden:
- modules/order/** must not calculate refundable amount.
- modules/shipping/** must not infer refundability.

Executable checks:
- tests/domain-invariants/billing/refund-amount.test.ts
- tests/contracts/order-billing/refund-request.contract.test.ts

Risk:
High

Related docs:
- docs/domain/billing/rules.md
- docs/architecture/context-map.md#order-billing
```

---

### 3.2 `02. AI용 헌법 AGENTS.md` 보완

추가 문서:

```text
docs/02-ai-constitution/
  AGENTS.md
  change-risk.md
  ddd-lite-rules.md
```

#### 추가: `change-risk.md`

역할:

```text
LLM에게 바로 맡겨도 되는 변경과 인간 리뷰가 필요한 변경을 분류
```

핵심 내용:

```md
# LLM Change Risk

## Low risk
- Local refactor inside one function
- Add test for existing invariant
- Rename private helper
- Add adapter behind existing port

## Medium risk
- Add new use case
- Add new value object
- Add new policy method
- Add new contract test

## High risk
- Change domain invariant
- Change state transition
- Change aggregate boundary
- Change context dependency direction
- Change existing domain event meaning
- Change repository contract
- Modify migration for domain-critical table

## Requires human review
- Payment/refund/settlement rule change
- Authorization/security policy change
- Inventory consistency rule change
- Cross-context data ownership change
```

#### 추가: `ddd-lite-rules.md`

역할:

```text
DDD를 어떻게 제한적으로 쓸지 LLM에게 알려주는 문서
```

핵심 문구:

```md
# DDD Lite Rules for LLM Agents

Do:
- Use domain language consistently.
- Preserve invariant ownership.
- Respect context boundaries.
- Prefer named policies over duplicated conditionals.
- Add executable checks when adding domain rules.

Do not:
- Introduce Entity/ValueObject/Repository/DomainService just for style.
- Add event-driven flow without contract tests.
- Create new aggregate boundaries without human review.
- Restructure folders into pattern-first DDD layout.
- Duplicate another context's business rule.
```

---

### 3.3 `03. 코드 맵과 모듈 경계`를 DDD 전략 설계로 확장

추가 문서:

```text
docs/03-architecture/
  architecture.md
  module-boundaries.md
  context-map.md
  ownership-map.md
  dependency-rules.md
```

#### 추가: `context-map.md`

역할:

```text
컨텍스트 간 허용된 통신 방식과 금지된 결합을 명시
```

#### 추가: `ownership-map.md`

역할:

```text
어떤 도메인 판단이 어느 컨텍스트에 속하는지 명시
```

예:

```md
# Ownership Map

| Decision | Owner | Other contexts may | Other contexts must not |
|---|---|---|---|
| Can an order be cancelled? | Order | Request cancellation | Reimplement cancellation rules |
| Is payment refundable? | Billing | Request refund | Calculate refundable amount |
| Can shipment be created? | Shipping | Request shipment | Directly create shipment record |
| Is stock reservable? | Inventory | Request reservation | Read inventory tables directly |
```

---

### 3.4 `04. 작업 프로토콜` 보완

추가 문서:

```text
docs/04-work-protocol/
  research-plan-small-diff.md
  domain-change-protocol.md
  review-checklist.md
  high-risk-change-protocol.md
```

#### 추가: `domain-change-protocol.md`

역할:

```text
도메인 변경 작업에서 LLM이 따라야 할 절차
```

템플릿:

```md
# Domain Change Protocol

Before changing code:

1. Identify touched context.
2. Identify invariant owner.
3. Read relevant domain rules.
4. Read context-map relationship.
5. Locate executable checks.
6. Plan the smallest safe diff.

Plan must include:
- Context touched
- Invariant affected
- Allowed mutation points
- Tests to run
- Boundary checks to run
- Whether human review is required

Do not proceed automatically if:
- Invariant meaning changes
- Context ownership changes
- Event meaning changes
- Aggregate boundary changes
```

---

### 3.5 `05. LLM 친화적 코드베이스 기준` 보완

추가 문서:

```text
docs/05-llm-friendly-codebase/
  criteria.md
  tactical-pattern-guidelines.md
  naming-and-language-rules.md
  when-not-to-use-ddd.md
```

#### 추가: `when-not-to-use-ddd.md`

핵심 내용:

```md
# When Not to Use DDD

Do not introduce DDD artifacts when:
- The code is simple CRUD.
- The rule is not domain-critical.
- There is no invariant to protect.
- The abstraction is not connected to tests or boundary checks.
- The change would increase files touched for common tasks.
- The pattern name is clearer than the actual business meaning.

Default:
Prefer simple code with strong tests over complex DDD structure.
```

---

### 3.6 `06. lumin-repo-lens 도입` 보완

추가 문서:

```text
docs/06-tooling/
  lumin-repo-lens.md
  evidence-provider.md
  domain-safety-gates.md
  protocol-hooks.md
```

#### 추가: `domain-safety-gates.md`

역할:

```text
DDD 문서를 실제 자동 검증으로 연결
```

내용:

```md
# Domain Safety Gates

## Boundary gate
Input:
- docs/03-architecture/context-map.md
- docs/03-architecture/dependency-rules.md

Checks:
- forbidden imports
- dependency direction violations
- internal model leakage

## Invariant gate
Input:
- docs/01-executable-specs/invariant-index.md

Checks:
- changed domain files have related invariant tests
- high-risk invariant changes are flagged
- missing test mapping is reported

## Language gate
Input:
- docs/domain/*/language.md

Checks:
- forbidden terminology
- inconsistent naming
- deprecated domain terms

## Change risk gate
Input:
- docs/02-ai-constitution/change-risk.md

Checks:
- high-risk touched areas
- aggregate boundary changes
- event contract changes
- migration on critical tables
```

---

## 4. 실행 순서와 우선순위

### Phase 1: DDD 용어가 아니라 안전장치부터 만든다

우선순위 1입니다.

만들 문서:

```text
docs/01-executable-specs/invariant-index.md
docs/03-architecture/ownership-map.md
docs/02-ai-constitution/change-risk.md
```

목표:

```text
- 핵심 불변식 10~20개 식별
- 각 불변식의 owner 지정
- 관련 테스트 파일 연결
- 고위험 변경 유형 정의
```

이 단계에서는 Aggregate, Repository, Domain Event 같은 용어를 거의 쓰지 않아도 됩니다.

가장 먼저 해야 할 일은 다음입니다.

```text
1. 핵심 도메인 불변식 목록화
2. 각 불변식의 소유 컨텍스트 지정
3. 테스트 파일 또는 테스트 필요 여부 연결
4. LLM 변경 위험도 분류
```

---

### Phase 2: 모듈 경계를 의미 경계로 승격한다

우선순위 2입니다.

만들 문서:

```text
docs/03-architecture/context-map.md
docs/03-architecture/dependency-rules.md
docs/01-executable-specs/boundary-checks.md
```

목표:

```text
- 컨텍스트별 owns / does not own 정의
- 허용 통신 방식 정의
- 금지 import 정의
- boundary check와 연결
```

여기서 중요한 것은 "문서화"가 아니라 "검출 가능성"입니다.

---

### Phase 3: 공통 언어를 LLM 입력으로 만든다

우선순위 3입니다.

만들 문서:

```text
docs/domain/billing/language.md
docs/domain/order/language.md
docs/domain/shipping/language.md
docs/05-llm-friendly-codebase/naming-and-language-rules.md
```

목표:

```text
- 혼동어 제거
- 금지어 정의
- 코드 네이밍 규칙 정의
- 이벤트/상태/행위 이름의 의미 고정
```

이 단계는 LLM 품질에 직접적인 영향을 줍니다.
특히 결제, 환불, 취소, 배송, 정산처럼 용어 혼동 비용이 큰 곳부터 합니다.

---

### Phase 4: 작업 프로토콜에 도메인 변경 절차를 연결한다

우선순위 4입니다.

만들 문서:

```text
docs/04-work-protocol/domain-change-protocol.md
docs/04-work-protocol/high-risk-change-protocol.md
```

목표:

```text
LLM이 도메인 변경을 하기 전에 반드시 다음을 식별하게 한다.

- touched context
- invariant owner
- related rules
- allowed mutation points
- required tests
- boundary checks
- human review 필요 여부
```

---

### Phase 5: lumin-repo-lens와 연결한다

우선순위 5입니다.

만들 문서:

```text
docs/06-tooling/domain-safety-gates.md
```

목표:

```text
lumin-repo-lens가 DDD-inspired 문서를 실제 evidence provider로 사용하게 한다.
```

구체적 역할:

```text
- diff가 어떤 context를 건드렸는지 탐지
- 관련 invariant-index 항목 제안
- 금지 import 탐지
- 관련 테스트 누락 탐지
- high-risk change 여부 표시
- LLM에게 읽어야 할 문서 목록 제공
```

---

### Phase 6: 전술적 DDD 패턴은 필요한 곳에만 국소 도입한다

우선순위 6입니다. 가장 나중입니다.

만들 문서:

```text
docs/domain/billing/aggregates.md
docs/domain/billing/events.md
docs/05-llm-friendly-codebase/tactical-pattern-guidelines.md
docs/05-llm-friendly-codebase/when-not-to-use-ddd.md
```

도입 기준:

```text
Aggregate:
- 상태 전이가 복잡하고 오류 비용이 클 때만

Value Object:
- 잘못된 값을 막을 수 있을 때만

Repository:
- ORM 오염을 끊거나 aggregate persistence가 의미 있을 때만

Domain Event:
- 여러 컨텍스트가 같은 도메인 사실에 반응하고 계약 테스트가 있을 때만

Domain Service / Policy:
- 복잡한 조건을 이름 있는 도메인 규칙으로 고정할 때만
```

---

## 5. DDD 도입 판단 기준

### 도입할 조건

| 질문                           | Yes면 도입 | No면 보류 |
| ---------------------------- | ------- | ------ |
| 이 요소가 특정 버그를 자동으로 잡는가?       | 도입      | 보류     |
| 이 요소가 변경 가능한 위치를 줄이는가?       | 도입      | 보류     |
| 이 요소가 import/의존성 규칙으로 검증되는가? | 도입      | 보류     |
| 이 요소가 테스트 선택을 돕는가?           | 도입      | 보류     |
| 이 요소가 도메인 용어 혼동을 줄이는가?       | 도입      | 보류     |

### 보류할 조건

| 질문                           | 결과   |
| ---------------------------- | ----- |
| 이 요소 때문에 수정 파일 수가 늘어나는가?     | 신중    |
| 이 요소가 boilerplate를 늘리는가?     | 보류    |
| 이 요소가 문서만 늘리고 검증은 못 하는가?     | 도입 금지  |

---

## 6. Turn 2에서 지적된 핵심 위험

### 패턴 이름이 의미를 대체하는 문제

LLM은 `Entity`, `ValueObject`, `Repository`, `DomainService`, `Aggregate` 같은 이름을 보면 그럴듯한 구조를 생성합니다. 하지만 이게 실제 도메인 안전성을 보장하지는 않습니다.

DDD 패턴 이름을 먼저 도입하지 말고, 다음 질문에 답할 때만 패턴명을 붙여야 합니다.

```text
이 객체가 어떤 불변식을 닫고 있는가?
이 경계 밖에서 직접 변경하면 무엇이 깨지는가?
이 추상화가 테스트나 경계 검증에 연결되는가?
LLM이 이 구조 덕분에 덜 추측하게 되는가?
```

---

### 과도한 계층화가 LLM의 변경 경로를 흐린다

LLM 친화적 설계에서는 "정교한 계층"보다 "정확한 수정 지점"이 더 중요합니다.

계층을 늘리기 전에 다음 기준을 적용해야 합니다.

```text
이 분리가 변경 diff를 줄이는가?
아니면 변경 시 만져야 할 파일 수를 늘리는가?
```

---

### 문서와 코드가 불일치할 때 LLM이 문서를 과신한다

DDD 문서는 반드시 다음 중 하나와 연결되어야 합니다.

```text
- 테스트 파일
- import boundary rule
- schema contract
- event contract
- repo-lens evidence
- CI check
- review checklist
```

연결되지 않는 문서는 "설계 설명"이 아니라 "LLM 오염원"이 될 수 있습니다.

---

## 7. 최종 결론

> **경량 DDD는 필수다. 중량 DDD는 위험하다. 실행 가능한 결과 없는 DDD는 금지한다.**

이 프로젝트에 필요한 것은 "DDD 도입"이 아닙니다.

필요한 것은:

> **DDD-inspired, executable domain safety layer**

즉, DDD에서 다음만 필수로 흡수합니다.

```text
1. 공통 언어
2. 도메인 불변식의 소유권
3. 의미적 모듈 경계
4. 컨텍스트 맵
5. 고위험 변경 분류
6. 자동 검증과 연결되는 문서 구조
```

반대로 다음은 기본적으로 선택적이거나 보류해야 합니다.

```text
1. 전역 aggregate catalog
2. 모든 모델의 Entity/ValueObject화
3. Repository 패턴 일괄 적용
4. DomainService 남발
5. 이벤트 기반 아키텍처 남발
6. 패턴 중심 폴더 구조
7. 실행 결과 없는 DDD 문서
```

최종 판단 기준은 이것입니다.

> 이 DDD 요소가 LLM이 덜 추측하게 만드는가?
> 변경 가능한 위치를 줄이는가?
> 도메인 오류를 자동으로 검출하게 만드는가?
> 관련 테스트와 boundary check에 연결되는가?

그렇다면 도입합니다.
아니라면 보류합니다.

---

### References

Oracle Browser 3턴 토의 결과 (/tmp/oracle_ddd_final.md)
