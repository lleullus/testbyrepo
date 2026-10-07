---
type: conditional-claim
claim_id: CCL-NET-006
claim_kind: boundary
domain: network

decision_question: "DKS-N의 Nginx Ingress Manifest를 DKS-C에 그대로 사용할 수 있는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-N, DKS-C]
network_profiles: [shared-ingress, dedicated-vpc]
directions: [inbound]
purposes: [service-routing, migration]
protocols: [http, https]

evidence_ids:
  - "2026062312395352000"
  - "2026070211275719321"
evidence_first_seen: 2026-06-23
evidence_last_seen: 2026-07-02

source_fidelity_min: full-dialogue
depends_on: [CCL-NET-G001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS-N의 Nginx Ingress Resource·Annotation은 DKS-C의 Contour·Envoy Gateway API와 직접 호환된다고 가정할 수 없으므로, DKS-C 전환 시 `Gateway`·`HTTPRoute` 중심으로 라우팅 Manifest를 재구성해야 한다.

## 판단 질문

> DKS-N에서 사용하던 `Ingress` YAML과 Nginx Annotation을 DKS-C에 그대로 배포해도 되는가?

## 적용 조건

- 기존 환경이 DKS-N Nginx Ingress 기반임
- 대상 환경이 DKS-C Contour·Envoy Gateway API 기반임
- HTTP·HTTPS Routing 설정을 이전하려는 상황

## 적용 전 확인할 미지수

- 기존 Ingress Rule·TLS·Rewrite·Timeout·Body Size·Header Annotation 목록
- 각 Nginx 기능에 대응하는 Gateway API·Contour 기능
- 지원되지 않는 Annotation과 대체 구현
- Gateway·Listener·HTTPRoute의 소유·Namespace 관계

## 근거 사슬

1. 2026-06 공식 답변은 DKS-N이 Nginx Ingress, DKS-C가 Contour·Envoy Gateway API를 사용한다고 구분했다.
2. 같은 답변은 Annotation과 Resource Spec 차이 때문에 Migration 시 Manifest 수정이 필요하다고 했다.
3. 2026-07 사례는 기존 Nginx Annotation·Option이 Contour와 호환되지 않아 Gateway API 규격으로 재구성하도록 권장했다.
4. 따라서 Controller 제품 차이뿐 아니라 사용자 Routing API와 Manifest가 달라 직접 재사용할 수 없다는 Claim이 반복 근거로 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026062312395352000 | full-dialogue | DKS-N은 Nginx Ingress, DKS-C는 Contour·Gateway API이며 Manifest 수정이 필요하다. | `VOC/2026-06-21 ~ 2026-06-27 DKS VOC 목록 (27건).md` 419-425행 |
| direct-support | 2026070211275719321 | full-dialogue | Nginx Annotation·Option이 Contour와 호환되지 않아 Gateway API로 재구성한다. | `VOC/2026-06-28 ~ 2026-07-04 DKS VOC 목록 (17건).md` 146-155행 |

## 이 Claim이 말하지 않는 것

- 모든 Nginx 기능에 Gateway API 대체 기능이 있다는 뜻이 아니다.
- 기존 Ingress Object를 배포하면 반드시 실패한다는 뜻이 아니다. 플랫폼 지원·Controller 설치 여부에 따라 다르다.
- 자동 변환 Tool이 없다는 뜻이 아니다.
- L4 TCP·UDP Routing까지 같은 변환 규칙을 쓴다는 뜻이 아니다.

## 반례·경쟁 설명

- 단순 Host·Path Routing은 의미상 유사하게 변환될 수 있지만 API 객체와 세부 동작은 검증해야 한다.
- DKS-C에 별도 Nginx Controller를 사용자가 설치할 수 있다면 다른 경로가 가능할 수 있으나 권한·정책 검증이 필요하다.

## 무효화 조건

- DKS-C가 Nginx Ingress Compatibility Layer 또는 공식 자동 변환을 제공하면 Migration 절차를 갱신한다.

## 다음 검증

- Nginx Annotation별 Gateway API·Contour Mapping 표와 미지원 기능 목록을 확인한다.

## 하위 문서 사용 조건

- Migration Scope 산정과 사전 호환성 검토에 사용할 수 있다.
- 실제 변환 Manifest는 현재 Gateway API Version과 DKS-C 배포 가이드로 검증해야 한다.
