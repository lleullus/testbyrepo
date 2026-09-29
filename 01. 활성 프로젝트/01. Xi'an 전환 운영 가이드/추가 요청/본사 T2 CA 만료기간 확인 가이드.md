---
title: "본사 T2 CA 만료기간 확인 가이드"
created: 2026-08-30
status: draft
tags:
  - certificate
  - ca
  - harbor
scope: "Xi'an 전환 운영 가이드"
---

# 본사 T2 CA 만료기간 확인 가이드

## 1. 확인 대상 인증서

문서에 기록된 확인 대상 경로는 다음과 같다.

```text
/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2IssuingCA.crt
/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2ROOTCA.crt
```

Harbor 서버 인증서는 다음 FQDN에서 별도로 확인한다.

```text
xa.dcr.dks.samsungds.net:443
```

## 2. T2 Issuing CA·Root CA 정보 조회

Bastion에서 다음 명령을 실행한다.

```bash
for CERT in /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2IssuingCA.crt /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2ROOTCA.crt; do echo "===== $CERT ====="; openssl x509 -in "$CERT" -noout -subject -issuer -serial -startdate -enddate -fingerprint -sha256; done
```

확인 항목:

- Subject
- Issuer
- Serial
- Not Before
- Not After
- SHA-256 Fingerprint

## 3. Harbor 서버 인증서 정보 조회

```bash
openssl s_client -connect xa.dcr.dks.samsungds.net:443 -servername xa.dcr.dks.samsungds.net </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -serial -startdate -enddate -fingerprint -sha256
```

## 4. 조회 결과 기록

| 구분 | Subject | Issuer | Serial | Not Before | Not After | SHA-256 Fingerprint |
|---|---|---|---|---|---|---|
| T2 Issuing CA |  |  |  |  |  |  |
| T2 Root CA |  |  |  |  |  |  |
| Harbor 서버 인증서 |  |  |  |  |  |  |

## 5. 만료 임박 여부 판정

| 확인 결과 | 판정 |
|---|---|
| 인증서가 현재 유효하고 운영 기준보다 충분한 잔여기간이 있음 | 정상 |
| Not Before 이전이거나 Not After를 초과함 | 사용 불가 |
| 운영 기준 이내로 만료가 임박함 | 갱신 계획 수립 필요 |
| 파일을 읽을 수 없거나 Subject가 예상 CA와 다름 | 확인 중단 및 파일 출처 재확인 |

완료 조건:

- T2 Issuing CA와 T2 Root CA의 실제 유효기간과 식별값이 기록돼 있다.
- Harbor 서버 인증서의 유효기간이 CA와 별도로 기록돼 있다.
- 각 인증서의 만료 임박 여부가 판정돼 있다.

## 근거

- 35. 작업 관리/2026-08-19 DEV PRD Member ks-apiserver SECDS T2 CA Bundle 적용 작업계획서.md L159–186, L431–433
