---
type: conditional-claim
claim_id: CCL-NET-007
claim_kind: responsibility
domain: network

decision_question: "DKS-C가 Contour·Envoy를 자동 배포하면 사용자 라우팅도 자동 생성되는가?"
derivation: direct

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-C]
network_profiles: [dedicated-vpc]
directions: [inbound]
purposes: [gateway-routing]
protocols: [http, https]

evidence_ids:
  - "2026070211275719321"
evidence_first_seen: 2026-07-02
evidence_last_seen: 2026-07-02

source_fidelity_min: full-dialogue
depends_on: [CCL-NET-006]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 DKS-C 제공 모델에서는 Envoy·Contour Controller는 클러스터 프로비저닝 시 자동 배포되지만, 서비스별 라우팅을 정의하는 `Gateway`와 `HTTPRoute` 리소스는 사용자가 작성한다.

## 판단 질문

> DKS-C를 생성하면 Application Routing도 자동 구성되는가?

## 적용 조건

- 서비스 모델이 DKS-C임
- HTTP·HTTPS 서비스를 Gateway API로 외부 노출하려는 상황
- 플랫폼 Controller 설치와 사용자 Routing 설정의 책임을 구분하려는 상황

## 적용 전 확인할 미지수

- 플랫폼이 기본 `Gateway` 객체까지 제공하는지
- 사용자에게 허용된 GatewayClass·Listener·Namespace 범위
- TLS Secret·Certificate와 Route Attachment 책임
- P-DEP 또는 Catalog가 Resource를 대신 생성하는지

## 근거 사슬

1. 2026-07 공식 답변은 DKS-C 프로비저닝 시 Envoy·Contour Controller가 자동 배포된다고 했다.
2. 같은 답변은 `Gateway`와 `HTTPRoute`를 사용자가 직접 작성해야 한다고 명시했다.
3. 따라서 Controller 운영 책임과 Application Routing Resource 작성 책임은 분리된다는 Claim이 직접 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026070211275719321 | full-dialogue | Envoy·Contour는 자동 배포되지만 `Gateway`·`HTTPRoute`는 사용자가 작성한다. | `VOC/2026-06-28 ~ 2026-07-04 DKS VOC 목록 (17건).md` 146-155행 |

## 이 Claim이 말하지 않는 것

- 사용자가 Envoy·Contour Controller 자체를 운영·업그레이드한다는 뜻이 아니다.
- 모든 GatewayClass·Listener 설정이 허용된다는 뜻이 아니다.
- P-DEP·Catalog가 라우팅 Resource 생성을 지원하지 않는다는 뜻이 아니다.

## 반례·경쟁 설명

- 서비스 Catalog나 배포 Template를 사용하면 `Gateway`·`HTTPRoute`가 자동 생성될 수 있다.
- Shared Gateway와 Namespace별 Gateway 모델에 따라 사용자 책임 범위가 달라질 수 있다.

## 무효화 조건

- 최신 DKS-C가 Application Routing Resource를 완전 관리형으로 자동 생성하거나 사용자가 Controller까지 직접 관리하도록 변경되면 수정한다.

## 다음 검증

- 현재 DKS-C GatewayClass·Shared Gateway 제공 방식과 P-DEP 연동 범위를 확인한다.

## 하위 문서 사용 조건

- 역할·책임 구분과 Migration 작업 항목 도출에 사용할 수 있다.
- 실제 Manifest 작성은 현재 Gateway API Version과 DKS-C 가이드로 검증한다.
