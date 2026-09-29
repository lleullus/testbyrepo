---
title: "Native API Ingress Source CIDR 통제 검토"
created: 2026-08-30
status: draft
tags:
  - kubernetes
  - native-api
  - ingress
  - cidr
scope: "Xi'an 전환 운영 가이드"
---

# Native API Ingress Source CIDR 통제 검토

## 1. 현재 Native API 구성

- PRD Native API는 nativeapi.xaprdpa01.apps.dks.samsungds.net을 사용한다.
- 경로는 VIP-B 109.156.25.60:443 → Router 109.156.22.61~63:30443 → ingress-nginx → kube-system/kube-apiserver Service :443 → Master 109.156.22.58~60:6443이다.
- PRD에는 FQDN, Ingress Address, Service Endpoint, 무인증 403, Token 호출 성공, RBAC 허용/비허용 결과가 기록돼 있다.
- Host와 DEV는 Native API FQDN과 대상 구성이 정의돼 있으나 PRD 수준의 실제 적용 증적은 부족하다.

## 2. 현재 CIDR 통제 가능 여부

현재 PRD Native API는 일반 Ingress 서비스와 동일한 VIP-B:443을 공유한다.

따라서 VIP-B 자체에 Source CIDR 제한을 적용하면 Native API뿐 아니라 동일 VIP-B:443을 사용하는 다른 HTTPS 서비스에도 영향을 줄 수 있다.

현재 구조 그대로는 Native API만 대상으로 한 L4 Source CIDR 제한을 적용하기 어렵다.

## 3. ssl-passthrough 적용 상태

Xi'an ingress-nginx Controller는 --enable-ssl-passthrough로 실행된다.

Native API Ingress에도 다음 설정이 적용돼 있다.

```yaml
nginx.ingress.kubernetes.io/ssl-passthrough: "true"
```

이 구조에서는 ingress-nginx가 Native API TLS를 종료하지 않고 kube-apiserver까지 전달한다.

## 4. whitelist-source-range 적용 한계

Operations Manual에는 다음 예시가 있다.

```yaml
nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/24,10.10.0.0/24"
```

이 값은 Xi'an 승인 CIDR이 아니다.

또한 ingress-nginx 공식 문서 기준으로 SSL Passthrough는 일반 NGINX HTTP 처리 경로를 우회하므로, 해당 Ingress의 HTTP 계층 Annotation을 Source CIDR 통제 수단으로 사용할 수 없다.

따라서 현재 Native API 구조에서 whitelist-source-range를 실제 차단 수단으로 적용하는 방안은 사용하지 않는다.

## 5. 공유 VIP-B 구조의 제약

현재 구조:

```text
Native API / 일반 HTTPS 서비스
→ 공용 VIP-B:443
→ Router
→ ingress-nginx
```

L4 LB에서는 동일한 VIP-B:443으로 들어오는 여러 FQDN을 개별 Source CIDR 정책으로 분리하기 어렵다.

따라서 Native API에만 별도 CIDR 정책을 적용하려면 현재 공유 경로의 변경이 필요하다.

## 6. 가능한 구조 변경안

### 6-1. SSL Passthrough 유지

Native API만 별도로 식별 가능한 L4 VIP/Virtual Server 또는 별도 Listener를 구성하고 해당 경계에서 Source CIDR을 제한한다.

### 6-2. Ingress TLS Termination으로 변경

현재 확인된 Native API 인증 방식은 ServiceAccount Bearer Token이다.

Bearer Token 방식만을 전제로 한다면 ingress-nginx에서 TLS를 종료하고 일반 HTTP/HTTPS 처리 경로를 사용하도록 변경한 뒤 Ingress Source CIDR Allowlist를 적용하는 방안을 검토할 수 있다.

현재 문서에는 왜 Native API에 SSL Passthrough를 선택했는지에 대한 설계 근거가 기록돼 있지 않으므로, 기존 구조 변경 여부는 별도 판단이 필요하다.

## 7. PRD / Host / DEV별 확인 상태

| Cluster | 현재 상태 |
|---|---|
| PRD Apps | Native API 경로 및 Token/RBAC 호출 증적 있음. Source CIDR 차단 증적 없음 |
| Host | Native API FQDN·대상 구성 정의. 실제 적용 증적 부족 |
| DEV Apps | Native API FQDN·대상 구성 정의. 실제 적용 증적 부족 |

## 8. 최종 판정

- 현재 Xi'an Native API의 Source CIDR 통제는 완료된 상태로 볼 수 없다.
- Operations Manual의 whitelist-source-range 값은 예시이며 실제 Xi'an 승인 CIDR이 아니다.
- 현재 ssl-passthrough + 공용 VIP-B:443 구조에서는 Native API만 대상으로 한 CIDR 제한을 기존 Ingress Annotation 또는 공용 L4 VIP 정책으로 적용하기 어렵다.
- 실제 CIDR 통제를 위해서는 Native API 전용 L4 제어 지점을 만들거나, SSL Passthrough를 제거하고 Ingress TLS Termination 구조로 변경하는 설계 판단이 필요하다.

## 근거

- 50. 운영/08. 트러블슈팅/Kubernetes/04. Kubernetes Native API 접속 및 권한 오류.md L18–168, L288–376
- 50. 운영/05. Operations Manual/05. Utilizing the Kubernetes Native API.md L125–175
- 60. 이슈 및 결정/ADR/Native API Xi'an 클러스터 구성 초안.md L179–272
- 30. 구축 및 전환/공통 구축/Xi'an/한국어/03.md L2664–2701
- 10. 기준 및 설계/클러스터 카탈로그/03. prd-apps-pa01-xas.md L50–90
