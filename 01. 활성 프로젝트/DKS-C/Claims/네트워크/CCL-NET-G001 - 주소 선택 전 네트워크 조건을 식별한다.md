---
type: conditional-claim
claim_id: CCL-NET-G001
claim_kind: guard
domain: network

decision_question: "DKS 연동 주소를 선택하기 전에 무엇을 확인해야 하는가?"
derivation: contrastive

evidence_status: supported
currentness: historical
operational_use: advisory

service_models: [DKS-N, DKS-C, unknown]
network_profiles: [unknown]
directions: [inbound, outbound]
purposes: [dns-registration, firewall-source, alb-backend]
protocols: [unknown]

evidence_ids:
  - "2026011610005492048"
  - "2026011510483584284"
  - "2026051912595354289"
  - "2026071317114898244"
evidence_first_seen: 2026-01-15
evidence_last_seen: 2026-07-14

source_fidelity_min: redacted-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

DKS 연동 주소를 선택하기 전에 **서비스 모델 또는 네트워크 프로파일, 통신 방향, 연동 목적**을 식별해야 하며, 이 중 핵심 조건이 미확인이면 특정 주소 규칙을 일반화하지 않는다.

## 판단 질문

> DNS·방화벽·ALB 구성에 어떤 IP를 사용해야 하는가?

## 적용 조건

- DKS와 외부 시스템 사이의 주소 또는 노출 지점을 선택하려는 상황
- `Cluster IP`, `VIP`, `Node IP`, `Egress IP` 중 어느 것을 사용할지 결정해야 하는 상황

## 적용 전 확인할 미지수

- 서비스가 DKS-N인지 DKS-C인지
- 문서에 서비스 모델이 없을 경우 실제 네트워크 프로파일이 무엇인지
- 트래픽 방향이 인바운드인지 아웃바운드인지
- 목적이 DNS 등록, 방화벽 Source/Destination, ALB backend 중 무엇인지
- 프로토콜과 포트가 HTTP·HTTPS인지 기타 TCP인지

## 근거 사슬

1. 외부 → 기존 DKS 인바운드에서는 내부 Ingress IP가 아니라 Cluster LB VIP를 사용하도록 답했다.
2. 기존 DKS → 외부에서는 Worker Node IP 대역을 방화벽 Source로 사용하도록 답한 사례가 있다.
3. DKS-C → 외부에서는 전용 Egress IP로 SNAT된다고 답했다.
4. 외부 ALB → DKS-C에서는 Worker Node NodePort 직접 접근이 불가하고 LB VIP를 사용하도록 답했다.
5. 같은 “어느 IP인가” 질문에 서로 다른 답이 성립하므로 조건 확인 없이 하나의 주소 규칙으로 합칠 수 없다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026011610005492048 | full-dialogue | 외부 인바운드는 내부 Ingress IP가 아닌 Cluster LB VIP를 사용했다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 161-178행 |
| scope-boundary | 2026011510483584284 | full-dialogue | 외부로 나가는 특정 기존 클러스터는 Worker Node IP 대역을 Source로 사용했다. | 같은 파일 252-264행 |
| scope-boundary | 2026051912595354289 | redacted-dialogue | DKS-C 외부 아웃바운드는 Egress IP로 SNAT된다. | `VOC/2026-05-17 ~ 2026-05-23 DKS VOC 목록 (8건).md` 134-141행 |
| scope-boundary | 2026071317114898244 | full-dialogue | DKS-C ALB 연동은 Worker Node NodePort가 아니라 LB VIP를 사용한다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 191-196행 |

## 이 Claim이 말하지 않는 것

- 확인해야 할 조건이 이 다섯 가지뿐이라는 뜻이 아니다.
- 실제 주소값을 제공하지 않는다.
- 특정 하위 Claim이 현재 정책임을 보장하지 않는다.

## 반례·경쟁 설명

- 서비스 모델이 아니라 구축 세대·망·클러스터별 프로파일이 실제 분기 조건일 수 있다.
- 일부 과거 VOC에는 DKS-N/C가 명시되지 않아 서비스 모델만으로 모든 차이를 설명할 수 없다.

## 무효화 조건

- 서비스 모델·방향·목적과 무관하게 모든 DKS 연동이 하나의 주소 규칙으로 통합됐다는 최신 공식 정책이 확인되는 경우 수정한다.

## 다음 검증

- DKS-N/C별 최신 네트워크 아키텍처와 주소 선택표를 공식 자료에서 확인한다.

## 하위 문서 사용 조건

- 이 Claim은 주소값을 주는 절차가 아니라 오판을 막는 Guard로 사용할 수 있다.
- 구체값은 현재성이 검증된 하위 Claim 또는 최신 공식 자료에서 확인해야 한다.
