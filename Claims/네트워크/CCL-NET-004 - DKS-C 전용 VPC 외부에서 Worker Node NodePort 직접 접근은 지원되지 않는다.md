---
type: conditional-claim
claim_id: CCL-NET-004
claim_kind: prohibition
domain: network

decision_question: "외부 시스템이 DKS-C Worker Node의 NodePort를 직접 백엔드로 사용할 수 있는가?"
derivation: direct

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-C]
network_profiles: [dedicated-vpc]
directions: [inbound]
purposes: [direct-nodeport-access, alb-backend]
protocols: [unknown]

evidence_ids:
  - "2026071317114898244"
evidence_first_seen: 2026-07-13
evidence_last_seen: 2026-07-14

source_fidelity_min: full-dialogue
depends_on: [CCL-NET-G001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS-C가 독립 전용 VPC에 격리된 조건에서는 외부 시스템이 Worker Node의 NodePort를 직접 접근 지점이나 ALB backend로 사용하는 구성이 지원되지 않는다.

## 판단 질문

> DKS-C Worker Node IP와 NodePort를 외부 연동 대상으로 직접 등록할 수 있는가?

## 적용 조건

- 서비스 모델이 DKS-C임
- 클러스터가 독립 전용 VPC에 위치함
- 접근 주체가 해당 VPC 외부에 있음

## 적용 전 확인할 미지수

- 실제 접근 주체가 동일 VPC 내부인지 외부인지
- 별도 프록시·피어링·라우팅 예외가 있는지
- 현재 DKS-C 네트워크 경계가 VOC 당시와 동일한지

## 근거 사슬

1. 문의자는 외부 ALB backend로 Worker Node + NodePort를 사용할 수 있는지 물었다.
2. 운영팀은 DKS-C가 독립 전용 VPC에 격리되어 외부에서 Worker Node NodePort로 직접 접근할 수 없다고 답했다.
3. 따라서 전용 VPC 외부라는 조건에서는 직접 NodePort 접근이 지원되지 않는다는 Claim이 직접 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026071317114898244 | full-dialogue | DKS-C 전용 VPC 외부에서는 Worker Node NodePort 직접 접근이 불가하다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 191-196행 |

## 이 Claim이 말하지 않는 것

- 동일 VPC 내부 접근 가능 여부를 규정하지 않는다.
- DKS-N의 NodePort 노출 정책을 규정하지 않는다.
- 외부 노출의 대체 방식 전체를 규정하지 않는다.

## 반례·경쟁 설명

- 기존 DKS의 일부 TCP 서비스 사례에서는 Worker Node NodePort가 안내됐다. 이는 서비스 모델과 네트워크 경계가 다른 범위 경계다.
- 특수 네트워크 연결이나 운영팀 승인 예외가 존재할 가능성은 현재 자료로 배제할 수 없다.

## 무효화 조건

- 최신 공식 자료에서 DKS-C Worker Node NodePort의 외부 직접 접근을 지원한다고 확인되면 수정한다.

## 다음 검증

- 현재 DKS-C VPC 라우팅·보안 경계와 지원되는 외부 노출 방식 목록을 공식 자료에서 확인한다.

## 하위 문서 사용 조건

- 아키텍처 경계와 지원하지 않는 구성 설명에는 사용할 수 있다.
- 현재 설계 승인 판단에는 최신 공식 네트워크 정책을 추가 확인해야 한다.
