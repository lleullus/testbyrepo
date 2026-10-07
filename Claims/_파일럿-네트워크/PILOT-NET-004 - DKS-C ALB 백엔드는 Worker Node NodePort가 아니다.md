---
type: conditional-claim
claim_id: PILOT-NET-004
claim_kind: rule
status: supported
domain: network
service_model: DKS-C
direction: inbound
purpose: alb-backend
observed_from: 2026-07-13
observed_to: 2026-07-14
current_policy_verified: false
last_reviewed: 2026-09-25
---

# Claim

외부 ALB에서 DKS-C 서비스를 백엔드로 연결할 때 Worker Node의 NodePort를 직접 타깃으로 사용하지 않고, 클러스터에 제공되는 Two-Arm LB VIP를 백엔드 타깃으로 사용한다.

## 적용 조건

- 서비스 모델이 DKS-C임
- 방향이 외부 ALB → DKS-C임
- 목적이 ALB backend pool 구성임

## 근거 사슬

1. 문의자는 Contour IP와 Worker Node + NodePort 중 어느 방식을 사용할지 물었다.
2. 운영팀은 DKS-C가 독립 전용 VPC에 격리돼 외부에서 Worker Node NodePort로 직접 접근할 수 없다고 답했다.
3. 운영팀은 대안으로 클러스터별 Two-Arm LB VIP를 ALB backend target으로 지정하도록 답했다.
4. 따라서 명시된 적용 조건에서는 Worker Node NodePort 방식이 배제되고 LB VIP 방식이 지지된다.

## 근거표

| 관계 | 사실 주장 | 근거 파일·행 |
|---|---|---|
| direct support | DKS-C는 전용 VPC에 격리되어 외부 Worker Node NodePort 직접 접근이 불가하고 Two-Arm LB VIP를 ALB backend로 사용한다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 191-196행 |

## 이 Claim이 말하지 않는 것

- ALB Health Check 경로와 HTTPRoute 설정을 규정하지 않는다.
- Two-Arm LB VIP의 실제 수량, 생성 절차 또는 현재 제공 한도를 규정하지 않는다.
- DKS-N의 NodePort 노출 정책을 규정하지 않는다.

## 반례·경쟁 설명

- 기존 DKS의 일부 비 HTTP TCP 사례에서는 Worker Node + NodePort가 안내됐다. 이는 DKS-C ALB 연동 Claim의 반례가 아니라 서비스 모델·목적이 다른 범위 경계다.
- 전용 VPC 외부에 별도 프록시가 배치되는 특수 구성이 가능한지는 현재 자료로 판단할 수 없다.

## 검증 상태

- 공식 답변이 DKS-C 구조에 대한 일반 문장으로 제시되어 Claim을 직접 지지한다.
- 단일 VOC 근거이므로 별도 공식 아키텍처 자료와의 교차 검증은 남아 있다.
