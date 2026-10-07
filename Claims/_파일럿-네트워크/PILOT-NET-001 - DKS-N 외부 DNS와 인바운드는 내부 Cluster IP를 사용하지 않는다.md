---
type: conditional-claim
claim_id: PILOT-NET-001
claim_kind: rule
status: supported
domain: network
service_model: DKS-N
direction: inbound
purpose:
  - dns-registration
  - http-https-exposure
observed_from: 2026-01-16
observed_to: 2026-07-20
current_policy_verified: false
last_reviewed: 2026-09-25
---

# Claim

DKS-N 서비스를 외부 DNS 또는 HTTP·HTTPS 인바운드에 연결할 때, 콘솔에 보이는 내부 Cluster IP·Ingress Service IP를 외부 등록 주소로 사용하지 않고 클러스터 대표 도메인 조회로 확인한 Cluster LB VIP를 사용한다.

## 적용 조건

- 서비스 모델이 DKS-N으로 확인됨
- 방향이 외부 → DKS임
- 목적이 DNS 등록 또는 HTTP·HTTPS 인바운드 방화벽 신청임

## 근거 사슬

1. 2026-07-16 사례는 DKS-N 콘솔의 Cluster IP를 내부 Ingress Controller Service IP라고 명시했다.
2. 같은 답변은 DNS 등록 주소로 클러스터 대표 도메인의 `nslookup` 결과를 사용하도록 했다.
3. 2026-01-16 사례도 내부 Ingress IP와 외부 Cluster LB VIP를 구분하고 `nslookup`으로 VIP를 확인하도록 했다.
4. 2026-03-06 사례도 DNS 등록 시 클러스터 domain을 조회해 주소를 확인하도록 했다.
5. 따라서 명시된 적용 조건에서는 내부 Cluster IP와 외부 등록용 VIP가 구별된다는 주장이 지지된다.

## 근거표

| 관계 | 사실 주장 | 근거 파일·행 |
|---|---|---|
| direct support | DKS-N Cluster IP는 내부 Ingress Controller Service IP이며 DNS용 VIP는 대표 도메인의 `nslookup` 결과다. | `VOC/2026-07-12 ~ 2026-07-18 DKS VOC 목록 (12건).md` 40-47행 |
| corroboration | 내부 Ingress IP가 아닌 Cluster LB VIP로 외부 방화벽을 열고, 도메인을 조회해 VIP를 확인한다. | `VOC/2026-01-11 ~ 2026-01-17 DKS VOC 목록 (17건).md` 161-178행 |
| corroboration | DNS 등록 주소는 클러스터 domain을 조회해 확인한다. | `VOC/2026-03-01 ~ 2026-03-07 DKS VOC 목록 (3건).md` 31-50행 |

## 이 Claim이 말하지 않는 것

- DKS-C의 인바운드 주소 선택을 규정하지 않는다.
- DKS-C 또는 DKS-N의 아웃바운드 방화벽 출발지 주소를 규정하지 않는다.
- HTTP·HTTPS 이외의 TCP 서비스 노출 방식을 규정하지 않는다.
- 특정 도메인이나 실제 VIP 값을 제공하지 않는다.

## 반례·경쟁 설명

- 1월과 3월 사례에는 서비스 모델이 본문에 명시되지 않았다. 이들은 DKS-N 범위를 직접 입증하기보다 주소 구분 패턴을 보강하는 근거다.
- DKS-C ALB 연동에서도 LB VIP를 사용하지만, 네트워크 경계와 제공 방식은 별도 Claim으로 관리해야 한다.

## 검증 상태

- 2026-07-20 공식 답변 기준으로 적용 조건 안의 Claim은 지지된다.
- 2026-09-25 현재 정책의 재확인은 수행하지 않았다.
