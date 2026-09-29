---
type: conditional-claim
claim_id: CCL-NET-001
claim_kind: boundary
domain: network

decision_question: "DKS-N 콘솔의 Cluster IP를 외부 DNS·방화벽 주소로 사용해도 되는가?"
derivation: direct

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-N]
network_profiles: [shared-namespace]
directions: [inbound]
purposes: [dns-registration, firewall-destination]
protocols: [http, https]

evidence_ids:
  - "2026071617520129033"
  - "2026011610005492048"
evidence_first_seen: 2026-01-16
evidence_last_seen: 2026-07-20

source_fidelity_min: full-dialogue
depends_on: [CCL-NET-G001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS-N 콘솔에 표시되는 내부 Cluster IP·Ingress Service IP를 외부 DNS 등록 주소나 외부 인바운드 방화벽 목적지로 간주하지 않는다.

## 판단 질문

> 콘솔의 Service/Ingress 화면에 보이는 IP를 외부 등록에 그대로 사용해도 되는가?

## 적용 조건

- 서비스 모델이 DKS-N으로 확인됨
- 외부에서 DKS-N 서비스로 들어오는 연결임
- DNS 등록 또는 인바운드 방화벽 목적지를 결정하는 상황임

## 적용 전 확인할 미지수

- 대상 IP가 내부 Service IP인지 외부 LB VIP인지
- 대상 클러스터의 대표 도메인과 외부 노출 지점
- 현재 DKS-N 네트워크 제공 방식이 VOC 당시와 동일한지

## 근거 사슬

1. 2026-07 사례는 DKS-N 콘솔의 Cluster IP를 내부 Ingress Controller Service IP라고 직접 규정했다.
2. 같은 답변은 DNS 등록용 Cluster VIP를 별도로 확인하도록 했다.
3. 2026-01 사례도 사용자가 제시한 LB IP를 내부 Ingress IP라고 구분하고 외부에는 Cluster LB VIP가 필요하다고 답했다.
4. 따라서 내부 표시 IP와 외부 등록 주소는 동일한 객체로 취급할 수 없다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026071617520129033 | full-dialogue | DKS-N Cluster IP는 내부 Ingress Controller Service IP다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 40-47행 |
| corroboration | 2026011610005492048 | full-dialogue | 문의자가 제시한 IP는 내부 Ingress IP이며 외부에는 Cluster LB VIP가 필요하다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 161-178행 |

## 이 Claim이 말하지 않는 것

- 외부 등록에 사용할 실제 VIP 값을 제공하지 않는다.
- DKS-C의 LB·Gateway 구조를 규정하지 않는다.
- HTTP·HTTPS 외 TCP 서비스 노출 방식을 규정하지 않는다.

## 반례·경쟁 설명

- 2026-01 사례의 서비스 모델은 본문에서 직접 명시되지 않아 DKS-N 범위를 넓히는 직접 증거로 사용하지 않는다.
- 콘솔 UI가 향후 외부 VIP를 별도 표시하도록 변경될 가능성이 있다.

## 무효화 조건

- 최신 공식 자료에서 DKS-N 콘솔의 해당 Cluster IP가 외부 등록용 주소로 변경됐다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS-N 콘솔에서 내부 Service IP와 외부 VIP가 각각 어떻게 노출되는지 확인한다.

## 하위 문서 사용 조건

- 잘못된 IP 선택을 막는 경계 설명에는 사용할 수 있다.
- 실제 신청 주소는 현재 공식 가이드로 재확인해야 한다.
