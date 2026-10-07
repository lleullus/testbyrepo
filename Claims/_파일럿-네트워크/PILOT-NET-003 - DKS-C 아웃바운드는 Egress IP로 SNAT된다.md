---
type: conditional-claim
claim_id: PILOT-NET-003
claim_kind: rule
status: supported
domain: network
service_model: DKS-C
direction: outbound
purpose: firewall-source
observed_from: 2026-05-19
observed_to: 2026-07-01
current_policy_verified: false
last_reviewed: 2026-09-25
---

# Claim

DKS-C Pod가 클러스터 외부의 사내 서비스 또는 DB로 통신할 때, 트래픽은 클러스터 전용 Egress IP로 SNAT되므로 방화벽 출발지에는 해당 Egress IP를 사용한다.

## 적용 조건

- 서비스 모델이 DKS-C임
- 방향이 DKS-C Pod → 클러스터 외부임
- 목적이 외부 사내 서비스 또는 DB 접근을 위한 방화벽 출발지 지정임

## 근거 사슬

1. 2026-05-19 사례에서 운영팀은 DKS-C 외부 아웃바운드가 Egress IP로 SNAT된다고 답했다.
2. 2026-06-30 사례에서도 DKS-C 전용 VPC의 외부 통신은 전용 Egress IP로 SNAT된다고 재확인했다.
3. 서로 다른 클러스터와 문의자가 동일한 구조를 확인했다.
4. 따라서 명시된 적용 조건 안에서는 Egress IP를 방화벽 Source로 사용하는 주장이 지지된다.

## 근거표

| 관계 | 사실 주장 | 근거 파일·행 |
|---|---|---|
| direct support | DKS-C 외부 아웃바운드는 Egress IP로 SNAT되고 별도 outbound Kubernetes 리소스는 필요하지 않다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 134-141행 |
| direct support | DKS-C 전용 VPC의 외부 통신은 전용 Egress IP로 SNAT되며 방화벽 Source에 그 IP를 입력한다. | `VOC/2026-06-28 ~ 2026-07-04 DKS VOC 목록 (17건).md` 297-305행 |

## 이 Claim이 말하지 않는 것

- 인터넷 직접 접근 허용 여부를 규정하지 않는다.
- 목적지 측 추가 ACL이나 URL Filtering 필요 여부를 규정하지 않는다.
- DKS-N의 아웃바운드 주소를 규정하지 않는다.
- 실제 Egress IP 값을 제공하지 않는다.

## 반례·경쟁 설명

- 기존 DKS 사례에서는 Worker Node IP 대역을 출발지로 안내했다. 이는 서비스 모델 또는 구축 구조가 달라 답이 달라지는 범위 경계다.
- 특정 망에서 별도 NAT 또는 보안 장비가 추가될 가능성은 현재 자료로 배제할 수 없다.

## 검증 상태

- 두 개의 독립적인 공식 답변에서 지지됨.
- 2026-09-25 현재 정책 재확인은 수행하지 않음.
