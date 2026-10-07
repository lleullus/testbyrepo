---
type: conditional-claim
claim_id: PILOT-NET-002
claim_kind: case-bounded
status: candidate
domain: network
service_model: unknown
direction: outbound
purpose: firewall-source
observed_from: 2026-01-15
observed_to: 2026-06-04
current_policy_verified: false
last_reviewed: 2026-09-25
---

# Claim

확인된 일부 기존 DKS 클러스터 사례에서는 Pod가 외부 서비스로 통신할 때 Cluster별 Worker Node IP 대역을 방화벽 출발지로 사용했다.

## 적용 조건

- 방향이 DKS → 외부임
- 해당 클러스터가 DKS-C의 전용 Egress SNAT 구조가 아님이 별도로 확인됨
- 운영팀이 그 클러스터의 방화벽 출발지로 Worker Node IP 대역을 지정함

## 근거 사슬

1. `prod-ds-member` 사례에서 운영팀은 외부 서비스 통신 시 Worker Node IP 대역으로 방화벽을 열도록 답했다.
2. 2026-06-04의 일반 DKS 문의에서도 내부 → 외부 통신 시 Cluster별 Node IP 대역을 Source로 사용하도록 답했다.
3. 그러나 두 사례 모두 본문에서 서비스 모델을 DKS-N이라고 직접 명시하지 않는다.
4. DKS-C 사례에서는 Egress IP를 출발지로 사용하므로, 이 답변을 모든 DKS에 일반화할 수 없다.
5. 따라서 현재 정당화되는 범위는 “관측된 기존 DKS 사례”이며, 정확한 서비스 모델 범위는 미확정이다.

## 근거표

| 관계 | 사실 주장 | 근거 파일·행 |
|---|---|---|
| direct support | `prod-ds-member`의 외부 통신은 Worker Node IP 대역으로 방화벽을 연다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 252-264행 |
| corroboration | DKS 내부 → 외부 통신은 Cluster별 Node IP 대역을 Source로 안내했다. | `VOC/2026-05-31 ~ 2026-06-06 DKS VOC 목록 (9건).md` 115-121행 |
| scope boundary | DKS-C 외부 통신은 전용 Egress IP로 SNAT된다. | `VOC/2026-06-28 ~ 2026-07-04 DKS VOC 목록 (17건).md` 297-305행 |

## 이 Claim이 말하지 않는 것

- `기존 DKS`가 곧 DKS-N이라는 뜻이 아니다.
- 모든 DKS-N 클러스터가 현재도 Worker Node IP 대역을 출발지로 사용한다는 뜻이 아니다.
- 개별 Node IP를 고정 등록하라는 뜻이 아니다.

## 반례·경쟁 설명

- DKS-C의 Egress SNAT 사례는 전체 DKS 일반화에 대한 명확한 범위 경계다.
- 구축 세대, 망 또는 클러스터별 구성 차이가 실제 분기 조건일 수 있다.

## 다음 검증

- `prod-ds-member`와 2026-06-04 문의 대상의 서비스 모델을 공식 자료에서 확인한다.
- DKS-N의 현재 아웃바운드 SNAT 구조를 공식 가이드에서 확인한다.

## 검증 상태

- 사례 사실은 확인됨.
- 재사용 가능한 DKS-N 일반 규칙으로의 승격은 보류함.
