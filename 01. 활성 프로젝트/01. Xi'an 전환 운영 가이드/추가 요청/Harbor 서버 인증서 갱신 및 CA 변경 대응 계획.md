---
title: "Harbor 서버 인증서 갱신 및 CA 변경 대응 계획"
created: 2026-08-30
status: draft
tags:
  - harbor
  - certificate
  - ca
scope: "Xi'an 전환 운영 가이드"
---

# Harbor 서버 인증서 갱신 및 CA 변경 대응 계획

## 1. 현재 확인된 구성

| 항목 | 값 |
|---|---|
| Harbor 서버 | xadksharbor01 |
| Harbor FQDN | xa.dcr.dks.samsungds.net |
| Harbor 버전 | 2.2.2 |
| 서버 인증서 | xa.dcr.dks.samsungds.net.crt |
| Private Key | xa.dcr.dks.samsungds.net.key |
| 인증서 설정 | harbor.yml의 certificate, private_key |
| 확인된 체인 | xa.dcr.dks.samsungds.net → SECDS-T2IssuingCA → SECDS-T2ROOTCA |

현재 문서에는 Harbor 최초 설치 시 서버 인증서와 Key를 배치하는 절차가 있으나, 운영 중 서버 인증서 갱신 절차는 없다.

## 2. 관리 기준

Harbor 서버 인증서 갱신과 조직 CA 변경은 별도 작업으로 구분한다.

### 2-1. 서버 인증서만 갱신되는 경우

CA 체인이 기존 SECDS-T2IssuingCA → SECDS-T2ROOTCA로 유지되고 Harbor 서버 인증서만 만료·재발급되는 경우이다.

```text
신규 Harbor 서버 인증서 발급
→ xadksharbor01의 서버 인증서/Key 교체
→ Harbor 설정 재반영 및 재기동
→ HTTPS / Registry / 로그인 / Push-Pull 검증
```

이 경우 CA가 변경되지 않았으므로 Worker, ks-apiserver, 사용자 PC의 CA Trust는 별도로 갱신하지 않는다.

신규 서버 인증서의 실제 신청·발급 담당 조직과 신청 절차는 현재 문서에 미기재되어 있으므로 별도 확인한다.

### 2-2. 조직 CA가 변경되는 경우

Harbor 서버 인증서의 Issuing CA 또는 Root CA가 변경되는 경우이다.

```text
신규 CA 체계로 Harbor 서버 인증서 발급
→ Harbor 서버 인증서/Key 교체
→ 신규 CA Bundle 배포
→ 전체 접근 경로 검증
```

신규 CA Trust 확인 대상:

- Member Cluster ks-apiserver
- Worker Node containerd/Docker
- 사용자 PC 및 Docker CLI 환경

구 CA와 신 CA의 전환 기간이 필요한 경우에는 신 CA 신뢰를 먼저 배포하고 검증한 뒤 서버 인증서를 전환한다.

## 3. 서버 인증서 교체 시 최소 확인 항목

1. 현재 인증서의 Issuer, Not After 확인
2. 신규 인증서의 SAN에 xa.dcr.dks.samsungds.net 포함 여부 확인
3. 신규 인증서와 Private Key 일치 확인
4. 기존 인증서, Key, harbor.yml, Compose 설정 백업
5. 신규 인증서와 Key 반영
6. Harbor 설정 재반영 및 재기동
7. openssl s_client로 실제 제공 인증서와 체인 확인
8. HTTPS /v2/, G-AD 로그인, Image Push/Pull 확인
9. 실패 시 기존 인증서와 설정으로 복구

## 4. 문서 범위

포함:

- Harbor 서버 인증서 만료·재발급 시 교체 기준
- 조직 CA 변경 시 Harbor 및 Client Trust 영향 범위

제외:

- Kubernetes API Server 인증서 갱신
- External ETCD 인증서 관리
- ks-apiserver CA Bundle의 상세 적용 명령
- Worker Runtime CA Trust의 상세 적용 명령

각 Client CA Trust의 상세 절차는 기존 KubeSphere/Worker/User Guide와 분리하여 관리한다.

## 근거

| 사실 주장 | 근거 |
|---|---|
| Harbor는 xa.dcr.dks.samsungds.net을 사용하며 xadksharbor01에서 운영된다. | 10. 기준 및 설계/클러스터 카탈로그/02. prd-harbor-xas.md L24–40 |
| Harbor 설치 문서에는 서버 인증서/Key 경로와 harbor.yml의 certificate, private_key 설정이 있다. | 50. 운영/06. Harbor Manual/01. Harbor Installation.md L76–112 |
| 현재 확인 기록의 체인은 xa.dcr.dks.samsungds.net → SECDS-T2IssuingCA → SECDS-T2ROOTCA이다. | 35. 작업 관리/2026-08-19 DEV PRD Member ks-apiserver SECDS T2 CA Bundle 적용 작업계획서.md L48–54 |
| Member ks-apiserver의 CA Trust 작업은 Harbor/LB 인증서와 Worker Runtime Trust를 범위에서 제외한다. | 같은 문서 L42–46 |
