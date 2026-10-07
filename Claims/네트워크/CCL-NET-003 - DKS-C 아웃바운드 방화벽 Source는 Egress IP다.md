---
type: conditional-claim
claim_id: CCL-NET-003
claim_kind: rule
domain: network

decision_question: "DKS-C Pod에서 외부 서비스로 나갈 때 방화벽 Source IP는 무엇인가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-C]
network_profiles: [dedicated-vpc]
directions: [outbound]
purposes: [firewall-source]
protocols: [unknown]

evidence_ids:
  - "2026051912595354289"
  - "2026063016483603852"
evidence_first_seen: 2026-05-19
evidence_last_seen: 2026-07-01

source_fidelity_min: redacted-dialogue
depends_on: [CCL-NET-G001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS-C Pod가 클러스터 외부의 사내 서비스나 DB로 통신할 때 트래픽은 클러스터 전용 Egress IP로 SNAT되므로, 방화벽 출발지에는 해당 Egress IP를 사용한다.

## 판단 질문

> DKS-C Pod의 아웃바운드 통신을 허용할 때 어느 주소를 Source로 등록해야 하는가?

## 적용 조건

- 서비스 모델이 DKS-C임
- 클러스터가 전용 VPC 구조임
- 방향이 Pod → 클러스터 외부임
- 목적이 방화벽 Source IP 지정임

## 적용 전 확인할 미지수

- 대상 클러스터에 실제 할당된 Egress IP
- 목적지 서비스의 IP·포트와 추가 ACL
- 현재 DKS-C Egress 설계가 VOC 당시와 동일한지

## 근거 사슬

1. 2026-05 공식 답변은 DKS-C 외부 아웃바운드가 Egress IP로 SNAT된다고 명시했다.
2. 2026-06 공식 답변은 전용 VPC 외부 통신이 전용 Egress IP로 SNAT된다고 다시 명시했다.
3. 서로 다른 클러스터·문의에서 동일한 구조가 반복됐다.
4. 따라서 명시한 범위에서 방화벽 Source는 Egress IP라는 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026051912595354289 | redacted-dialogue | DKS-C 외부 아웃바운드는 Egress IP로 SNAT되며 별도 outbound Kubernetes 리소스는 필요하지 않다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 134-141행 |
| direct-support | 2026063016483603852 | full-dialogue | DKS-C 전용 VPC의 외부 통신은 전용 Egress IP로 SNAT되며 방화벽 Source에 해당 IP를 입력한다. | `VOC/2026-06-28 ~ 2026-07-04 DKS VOC 목록 (17건).md` 297-305행 |

## 이 Claim이 말하지 않는 것

- 인터넷 직접 통신이 허용된다는 뜻이 아니다.
- 목적지 측 방화벽·ACL이 불필요하다는 뜻이 아니다.
- DKS-N 또는 서비스 모델 미확인 클러스터의 출발지 주소를 규정하지 않는다.
- 실제 Egress IP 값을 제공하지 않는다.

## 반례·경쟁 설명

- 일부 기존 DKS 사례에서는 Worker Node IP 대역이 Source로 안내됐다. 이는 전체 DKS 일반화의 범위 경계다.
- 망별 별도 NAT·Proxy가 존재하는 특수 프로파일은 현재 자료로 배제할 수 없다.

## 무효화 조건

- 최신 공식 자료에서 DKS-C 아웃바운드 SNAT 지점이 변경됐거나 Pod/Node 주소가 직접 노출된다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS-C 콘솔 또는 공식 네트워크 가이드에서 Egress IP 확인 경로와 망별 예외를 검증한다.

## 하위 문서 사용 조건

- 구조 설명에는 사용할 수 있다.
- 실제 방화벽 신청에는 현재 클러스터 Egress IP와 최신 정책을 재확인해야 한다.
