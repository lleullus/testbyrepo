---
type: conditional-claim
claim_id: PILOT-NET-G001
claim_kind: guard
status: supported
domain: network
service_model: any
direction: any
purpose: address-selection
observed_from: 2026-01-15
observed_to: 2026-07-14
current_policy_verified: false
last_reviewed: 2026-09-25
---

# Claim

DKS 연동에 사용할 주소를 결정하기 전에 최소한 **서비스 모델, 통신 방향, 연동 목적**을 식별해야 한다.

## 적용 조건

- DNS 등록, 방화벽 신청 또는 외부 LB 백엔드 구성을 위해 주소를 선택하는 상황
- 질문에 `DKS IP`, `클러스터 IP`, `노드 IP`, `VIP`처럼 여러 의미가 가능한 표현이 포함된 상황

## 근거 사슬

1. 외부에서 기존 DKS의 HTTP·HTTPS 서비스로 들어가는 사례에서는 내부 Ingress IP가 아니라 Cluster LB VIP를 사용하도록 안내됐다.
2. 기존 DKS에서 외부 서비스로 나가는 사례에서는 Worker Node IP 대역을 방화벽 출발지로 사용하도록 안내됐다.
3. DKS-C에서 외부 서비스로 나가는 사례에서는 전용 Egress IP로 SNAT되므로 Egress IP를 출발지로 사용하도록 안내됐다.
4. DKS-C를 외부 ALB와 연동하는 사례에서는 Worker Node의 NodePort 직접 접근이 불가하고 Two-Arm LB VIP를 백엔드로 사용하도록 안내됐다.
5. 따라서 질문의 표면적 주제가 모두 “어느 IP인가”로 같아도, 서비스 모델·방향·목적이 다르면 정답이 달라진다.
6. 그러므로 세 조건을 확인하지 않은 채 특정 주소 유형을 답하는 것은 현재 근거로 정당화되지 않는다.

## 근거표

| 관계 | 사실 주장 | 근거 파일·행 |
|---|---|---|
| support | 외부 → 기존 DKS 인바운드는 Cluster LB VIP를 사용하도록 안내됐다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 161-178행 |
| support | 기존 DKS → 외부 통신은 Worker Node IP 대역을 사용하도록 안내됐다. | 같은 파일 252-264행 |
| support | DKS-C → 외부 통신은 Egress IP로 SNAT된다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 134-141행 |
| support | DKS-C 외부 ALB 연동은 Worker Node NodePort가 아니라 Two-Arm LB VIP를 사용한다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 191-196행 |

## 이 Claim이 말하지 않는 것

- 세 조건만 알면 실제 IP 값을 계산할 수 있다는 뜻이 아니다.
- 모든 네트워크 판단에 이 세 조건만으로 충분하다는 뜻이 아니다. 프로토콜, 포트, 망 구분 등이 추가로 필요할 수 있다.
- 각 하위 Claim이 2026-09-25 현재도 동일한 정책임을 보장하지 않는다.

## 반례·경쟁 설명

- 실제 차이를 만든 요인이 서비스 모델이 아니라 구축 세대나 특정 망 정책일 가능성이 있다.
- 일부 VOC에는 서비스 모델이 명시돼 있지 않으므로, `기존 DKS = DKS-N`으로 자동 치환하면 안 된다.

## 검증 상태

- 서로 다른 공식 답변을 설명하는 **판단 전제**로는 지지된다.
- 현재 운영 정책의 필수 확인 항목으로 공식 승인된 것은 아니다.
