---
title: "인증서 갱신 시 사용자 kubeconfig 처리 가이드"
created: 2026-08-30
status: draft
tags:
  - kubernetes
  - kubeconfig
  - certificate
  - kubesphere
scope: "Xi'an 전환 운영 가이드"
---

# 인증서 갱신 시 사용자 kubeconfig 처리 가이드

## 1. 대상 kubeconfig 확인

관리자, 일반 사용자, 자동화 계정, KubeSphere Member 연결용 kubeconfig를 구분한다.

## 2. 인증서 갱신 유형 판정

다음 세 경우를 구분한다.

- Control Plane 인증서만 갱신
- 사용자 Client Certificate 만료
- Kubernetes CA 교체

## 3. 사용자 Client Certificate 만료일 확인

사용자 ~/.kube/config 또는 kubesphere-controls-system/kubeconfig-<AD 계정>에 포함된 client-certificate-data의 만료일을 확인한다.

```bash
kubectl config view --raw -o jsonpath='{.users[0].user.client-certificate-data}' | base64 -d | openssl x509 -noout -subject -issuer -dates
```

## 4. Control Plane 인증서만 갱신한 경우

Kubernetes CA가 유지되고 사용자 Client Certificate가 유효하면 사용자 kubeconfig는 교체하지 않는다.

kubeadm certs renew all로 갱신되는 Control Plane 인증서와 일반 사용자의 kubeconfig-<AD> Client Certificate는 별도 관리 대상으로 본다.

## 5. 사용자 Client Certificate가 만료된 경우

만료된 사용자만 새 Client Certificate와 kubeconfig를 발급·배포한다.

일반 사용자 kubeconfig를 갱신하기 위해 /etc/kubernetes/admin.conf를 배포하지 않는다.

## 6. Kubernetes CA를 교체한 경우

기존 CA를 제거하기 전에 새 CA 기준 인증정보를 먼저 배포하고 검증한다.

대상은 다음과 같다.

- 사용자 kubeconfig
- 자동화 Client kubeconfig
- KubeSphere Member 연결 kubeconfig
- 기타 Kubernetes API Client kubeconfig

처리 항목:

- certificate-authority-data: 신규 CA로 교체
- client-certificate-data: 신규 CA 기준으로 재발급
- client-key-data: 신규 Client Certificate에 대응하는 Key로 교체

## 7. 사용자 kubeconfig 재생성 및 배포

현재 Xi'an 사용자 CLI 방식은 다음 ConfigMap을 기준으로 한다.

```text
kubesphere-controls-system
→ kubeconfig-<G-AD 계정>
→ 사용자 ~/.kube/config
```

갱신 대상 사용자의 새 kubeconfig를 생성·추출한 뒤 해당 사용자 계정의 ~/.kube/config에 반영한다.

파일 권한은 기존 기준과 동일하게 사용자 소유 및 600을 유지한다.

## 8. 자동화 계정 kubeconfig 처리

스크립트, 배치, 운영 자동화에서 사용하는 kubeconfig가 있으면 일반 사용자와 분리하여 Client Certificate 만료와 CA 변경 여부를 확인한다.

유효한 인증정보는 불필요하게 교체하지 않는다.

## 9. KubeSphere Member 연결 kubeconfig 처리

KubeSphere Member Unbind·Import는 일반 사용자 kubeconfig 갱신과 별도 작업이다.

기존 인증서 갱신 가이드의 Member Unbind·Import 절차는 Host가 Member Cluster에 접속하는 관리용 kubeconfig 갱신으로 처리한다.

## 10. admin.conf 사용자 배포 금지

admin.conf는 관리자용 kubeconfig이므로 일반 사용자의 인증서 갱신 수단으로 배포하지 않는다.

일반 사용자는 기존 kubeconfig-<AD 계정> 기반 인증정보와 기존 RBAC 권한을 유지한다.

## 11. kubectl 인증 및 권한 검증

갱신 대상 사용자 계정에서 다음을 확인한다.

```bash
kubectl config current-context
kubectl auth can-i --list
kubectl get all -n <허용된-namespace>
```

정상 기준:

- API Server 인증 성공
- 기존 허용 Namespace/Resource 접근 성공
- 기존에 허용되지 않은 권한이 새로 부여되지 않음

## 12. 실패 시 복구

새 kubeconfig 적용 후 인증이 실패하면 기존 유효한 kubeconfig 백업본으로 복구한다.

CA 교체 작업에서는 기존 CA를 제거하기 전에 신규 CA 기준 kubeconfig의 정상 동작을 먼저 확인한다.

## 13. 사용자별 처리 결과 기록

| 사용자/Client | 구분 | Client Certificate 만료일 | 처리 | 검증 결과 |
|---|---|---|---|---|
|  | 일반 사용자 / 자동화 / Member 연결 |  | 유지 / 재발급 / 교체 |  |

## 14. 완료 기준

- Control Plane 인증서만 갱신한 경우 불필요한 사용자 kubeconfig 교체가 수행되지 않았다.
- 만료된 사용자 Client Certificate만 필요한 범위에서 재발급됐다.
- CA 교체 시 대상 Client kubeconfig가 신규 CA 기준으로 이전됐다.
- 일반 사용자에게 admin.conf가 배포되지 않았다.
- 갱신 대상 사용자의 kubectl 인증과 기존 RBAC 권한이 정상이다.

## 근거

- 50. 운영/05. Operations Manual/06. Renewing API Server Certificates.md L16–39, L43–95, L392–470
- 50. 운영/04. Kubesphere Operation/06. Enable users using kubectl CLI.md L17–27, L52–178
