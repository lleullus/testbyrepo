---
type: conditional-claim
claim_id: CCL-NET-005
claim_kind: procedure
domain: network

decision_question: "외부 ALB의 DKS-C backend target으로 무엇을 사용해야 하는가?"
derivation: direct

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-C]
network_profiles: [dedicated-vpc]
directions: [inbound]
purposes: [alb-backend]
protocols: [unknown]

evidence_ids:
  - "2026071317114898244"
evidence_first_seen: 2026-07-13
evidence_last_seen: 2026-07-14

source_fidelity_min: full-dialogue
depends_on: [CCL-NET-G001, CCL-NET-004]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 DKS-C 외부 ALB 연동 방식에서는 클러스터에 제공되는 Two-Arm LB VIP를 ALB backend target으로 사용했다.

## 판단 질문

> DKS-C 서비스를 외부 ALB의 backend pool에 어떤 주소로 등록하는가?

## 적용 조건

- 서비스 모델이 DKS-C임
- 외부 ALB가 DKS-C 서비스를 backend로 연결함
- Worker Node NodePort 직접 접근이 지원되지 않는 전용 VPC 구조임

## 적용 전 확인할 미지수

- 대상 클러스터에 현재 제공되는 LB 유형과 VIP
- ALB와 DKS-C 사이의 실제 라우팅·방화벽 조건
- Health Check 경로와 Gateway/HTTPRoute 설정

## 근거 사슬

1. 운영팀은 DKS-C Worker Node NodePort 직접 접근이 불가하다고 답했다.
2. 동일 답변에서 클러스터별 Two-Arm LB VIP를 ALB backend target으로 등록하도록 안내했다.
3. 따라서 해당 관측 시점의 DKS-C ALB 연동 대안은 Two-Arm LB VIP였다는 Claim이 직접 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026071317114898244 | full-dialogue | 클러스터별 Two-Arm LB VIP를 ALB backend target으로 사용하도록 안내했다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 191-196행 |

## 이 Claim이 말하지 않는 것

- 현재 클러스터당 제공 VIP 수량을 규정하지 않는다.
- LB VIP의 생성·변경 절차를 규정하지 않는다.
- Health Check 및 세션 전환 설계를 보장하지 않는다.

## 반례·경쟁 설명

- 향후 DKS-C의 공식 외부 노출 방식이 다른 Gateway 또는 LB 서비스로 바뀔 수 있다.
- 특정 망이나 프로젝트에서 별도 연동 지점이 제공될 가능성은 현재 자료로 배제할 수 없다.

## 무효화 조건

- 최신 공식 자료에서 ALB backend target으로 다른 endpoint를 사용하도록 변경됐다고 확인되면 supersede한다.

## 다음 검증

- 현재 DKS-C 외부 트래픽 가이드에서 Two-Arm LB 제공 방식, 확인 경로, 제한을 확인한다.

## 하위 문서 사용 조건

- 현재성이 검증되기 전에는 “2026-07 관측 방식”으로만 기술한다.
- 실제 ALB 구성은 최신 공식 네트워크 설계와 클러스터 제공 정보를 확인해야 한다.
