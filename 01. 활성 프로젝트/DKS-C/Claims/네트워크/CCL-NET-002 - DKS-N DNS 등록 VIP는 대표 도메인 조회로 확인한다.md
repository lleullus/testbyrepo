---
type: conditional-claim
claim_id: CCL-NET-002
claim_kind: procedure
domain: network

decision_question: "DKS-N 외부 DNS 등록용 VIP를 어떻게 확인하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [DKS-N]
network_profiles: [shared-namespace]
directions: [inbound]
purposes: [dns-registration]
protocols: [http, https]

evidence_ids:
  - "2026071617520129033"
  - "2026030612551576849"
  - "2026011610005492048"
evidence_first_seen: 2026-01-16
evidence_last_seen: 2026-07-20

source_fidelity_min: full-dialogue
depends_on: [CCL-NET-G001, CCL-NET-001]
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

관측된 DKS-N 외부 DNS 등록 절차에서는 클러스터별 대표 도메인을 조회해 얻은 Cluster LB VIP를 등록 주소로 사용했다.

## 판단 질문

> 외부 DNS에 등록할 DKS-N Cluster VIP를 어디에서 확인하는가?

## 적용 조건

- 서비스 모델이 DKS-N으로 확인됨
- 목적이 외부 DNS 등록임
- 대상 서비스가 클러스터 Ingress를 통해 노출됨

## 적용 전 확인할 미지수

- 대상 클러스터의 대표 도메인
- 현재 대표 도메인 조회 방식이 유지되는지
- DNS 등록 외에 GSAMS URL Filtering 등 추가 절차가 필요한지

## 근거 사슬

1. 2026-07 공식 답변은 DKS-N DNS 등록용 VIP를 클러스터 대표 도메인의 `nslookup` 결과로 확인하도록 했다.
2. 2026-03 공식 답변도 클러스터별 domain을 `nslookup`해 주소를 확인하도록 했다.
3. 2026-01 공식 답변도 기본 hostname 또는 Cluster Domain을 조회해 Cluster별 VIP를 확인하도록 했다.
4. 반복된 공식 답변이 동일한 확인 방법을 제시하므로, 관측된 절차로서 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026071617520129033 | full-dialogue | DKS-N 대표 도메인을 `nslookup`해 DNS 등록용 VIP를 확인한다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 40-47행 |
| corroboration | 2026030612551576849 | full-dialogue | 클러스터별 domain을 조회해 DNS 등록 주소를 확인한다. | `VOC/2026-03-01 ~ 2026-03-07 DKS VOC 목록 (3건).md` 31-50행 |
| corroboration | 2026011610005492048 | full-dialogue | Cluster Domain 또는 기본 hostname을 조회해 VIP를 확인한다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 161-178행 |

## 이 Claim이 말하지 않는 것

- 현재 대표 도메인 목록이나 실제 VIP 값을 제공하지 않는다.
- DKS-C Gateway·Two-Arm LB의 주소 확인 절차를 규정하지 않는다.
- DNS 등록 승인 절차 전체를 규정하지 않는다.

## 반례·경쟁 설명

- 향후 콘솔에서 외부 VIP를 직접 제공하면 `nslookup`은 유일한 확인 방법이 아닐 수 있다.
- 1월과 3월 사례는 서비스 모델이 본문에 명시되지 않아 반복 패턴 보강에만 사용한다.

## 무효화 조건

- 최신 공식 가이드에서 대표 도메인 조회가 폐기되거나 다른 authoritative source를 사용하도록 변경되면 대체한다.

## 다음 검증

- 현재 DKS-N Ingress 배포 가이드의 VIP 확인 절차와 GSAMS 요구사항을 확인한다.

## 하위 문서 사용 조건

- 현재성이 검증되기 전에는 과거 관측 절차로만 기술한다.
- 실제 DNS 신청 전에는 최신 공식 가이드에서 주소와 절차를 재확인한다.
