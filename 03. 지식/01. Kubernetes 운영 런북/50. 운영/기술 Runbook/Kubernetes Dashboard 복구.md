---
title: "Kubernetes Dashboard 복구"
status: current
aliases:
  - Dashboard Namespace 복구
doc_type: guide
scope: "Xi'an 전환 운영 가이드"
updated: "2026-07-19"
---

# Kubernetes Dashboard 복구

`kubernetes-dashboard` Namespace 또는 그 안의 Dashboard 리소스가 삭제되어 접속할 수 없을 때, 전체 클러스터를 재배포하지 않고 Kubespray Dashboard 범위만 복구하는 절차다.

> [!warning] 적용 범위와 중단 조건
> 이 절차는 Xi'an Host Cluster의 `kubernetes-dashboard` 복구에만 적용한다. 대상 context, 현장 inventory의 `dashboard_enabled` 또는 `dashboard_namespace`, 기존 Ingress 정책을 확인할 수 없으면 실행하지 않는다. KubeSphere Namespace 삭제, 관리자 RBAC 재설계, TLS 정책 변경은 이 절차의 범위 밖이다.

## 완료 기준

- `kubernetes-dashboard` Namespace가 `Active`다.
- Dashboard Deployment가 존재하고 Pod가 `Running`이며, 관련 Service와 Endpoint가 존재한다.
- Dashboard Ingress가 존재하며 이벤트에 ImagePull, Scheduling, TLS handshake 오류가 없다.
- 환경의 기존 Ingress 정책과 일치하는 접속 경로를 확인했다.
- 기존 운영 RBAC 정책에 따른 Token 로그인까지 확인했거나, Token/RBAC 복구를 별도 작업으로 분리했다.

## 1. 실행 전 확인

실행 대상이 의도한 Cluster인지 먼저 확인하고, 복구 전 상태를 남긴다. `kubernetes-dashboard`와 `kubesphere-system`은 서로 다른 Namespace이므로 삭제·복구 대상을 혼동하지 않는다.

```bash
kubectl config current-context
kubectl get ns kubernetes-dashboard
kubectl get ing -A
```

Kubespray 작업 디렉터리에서 Dashboard 역할과 현장 inventory 값을 확인한다.

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19

find roles/kubernetes-apps/ansible -type f \( -iname "*dashboard*" \) -print

grep -RniE "dashboard_enabled|dashboard_namespace" \
  inventory/dks roles/kubernetes-apps/ansible
```

Xi'an에서 확인된 적용값은 다음과 같다. Kubespray role 기본값에 `dashboard_namespace: kube-system`이 있을 수 있으므로, 기본값이 아니라 현장 inventory override를 실행 기준으로 사용한다.

```yaml
# inventory/dks/group_vars/k8s_cluster/addons.yml
dashboard_enabled: true
dashboard_namespace: kubernetes-dashboard
```

> [!danger] 실행 금지
> `dashboard_enabled: true`와 `dashboard_namespace: kubernetes-dashboard`를 현장 inventory에서 확인하기 전에는 playbook을 실행하지 않는다. 전체 `cluster.yml` 재배포나 KubeSphere installer 재실행으로 대체하지 않는다.

## 2. Dashboard 범위 복구

확인한 동일 작업 디렉터리에서 `dashboard` tag만 실행한다.

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19

ansible-playbook \
  -e @inventory/dks/dks_vars.yml \
  -i inventory/dks/hosts.yaml \
  --become --become-user=root \
  --tags dashboard \
  cluster.yml
```

이번 환경에서는 해당 tag가 Namespace, Dashboard 리소스 및 기존 Ingress를 재생성했다. 다른 Kubespray 버전이나 bundle에서는 Ingress가 template에 없을 수 있으므로, 별도 Ingress YAML을 만들기 전에 `roles/kubernetes-apps/ansible/templates/dashboard.yml.j2`와 실제 실행 결과를 확인한다.

## 3. 복구 직후 검증

```bash
kubectl get ns kubernetes-dashboard
kubectl get all -n kubernetes-dashboard
kubectl get endpoints -n kubernetes-dashboard
kubectl get sa,secret -n kubernetes-dashboard
kubectl get ingress -n kubernetes-dashboard
kubectl get events -n kubernetes-dashboard --sort-by=.lastTimestamp
```

Namespace가 `Active`인지, `kubectl get all` 출력에서 Dashboard Deployment가 존재하고 Pod가 `Running`인지, `kubectl get endpoints` 출력에서 `kubernetes-dashboard` Service의 Endpoint가 존재하는지, Dashboard Ingress가 존재하는지 확인한다. ImagePull, Scheduling, TLS handshake 관련 오류가 있으면 다음 단계로 진행하지 않고 해당 오류를 먼저 분리한다.

## 4. Ingress 경로 확인 및 조건부 조정

이번 폐쇄망 환경의 목표 상태는 브라우저와 Ingress Controller 사이에는 기본 Fake Certificate를 사용하고, Ingress Controller와 Dashboard Service 사이에는 HTTPS로 연결하는 구조다. 이 환경에서 Ingress에 별도 TLS Secret을 추가하지 않는다. 외부 공개 환경에는 이 정책을 적용하지 않는다.

현재 Ingress와 annotation을 확인한다.

```bash
kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress -o yaml

dashboard_host=$(kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress \
  -o jsonpath='{.spec.rules[0].host}')
printf '%s\n' "$dashboard_host"

kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress \
  -o jsonpath='{.metadata.annotations.nginx\.ingress\.kubernetes\.io/ssl-passthrough}{"\n"}'

kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress \
  -o jsonpath='{.metadata.annotations.nginx\.ingress\.kubernetes\.io/backend-protocol}{"\n"}'
```

현장 정책이 위 목표 상태와 같고 SSL passthrough가 설정되어 있을 때만 제거한다. Dashboard Service는 `443 -> 8443` HTTPS backend이므로 backend protocol은 `HTTPS`여야 한다.

```bash
kubectl -n kubernetes-dashboard annotate ingress kubernetes-dashboard-ingress \
  nginx.ingress.kubernetes.io/ssl-passthrough-

kubectl -n kubernetes-dashboard annotate ingress kubernetes-dashboard-ingress \
  nginx.ingress.kubernetes.io/backend-protocol="HTTPS" \
  --overwrite
```

변경 후 `ssl-passthrough` 출력은 비어 있고 `backend-protocol` 출력은 `HTTPS`여야 한다. 현장 TLS/Ingress 정책이 확인되지 않았거나 다른 정책이 적용돼 있으면 annotation을 변경하지 않고 승인된 별도 작업으로 분리한다.

Ingress에서 조회한 host로 브라우저 접속을 확인한다. 이번 폐쇄망 정책에서는 브라우저 경고를 승인했을 때 Ingress Controller의 기본 self-signed Fake Certificate가 표시되는 경로가 정상이다. 인증서 경로가 다르거나 접속이 실패하면 Token 로그인 단계로 진행하지 않는다.

```bash
openssl s_client \
  -connect "${dashboard_host}:443" \
  -servername "$dashboard_host" \
  </dev/null 2>&1 | \
  grep -E 'subject=|issuer=|Verify return code'
```

정상 경로에서는 `subject`와 `issuer`가 모두 `Kubernetes Ingress Controller Fake Certificate`이고 `Verify return code`가 `18 (self signed certificate)`로 표시된다. 외부 공개 환경에는 이 기준을 적용하지 않는다.

## 5. Token 로그인 확인

로그인 화면에서는 `Token` 방식을 사용하고 `kubeconfig`를 사용하지 않는다. 기존 `admin-token`이 있을 때만 Token을 조회해 브라우저에서 로그인 확인을 수행한다. Token 값은 문서, 티켓, 채팅에 기록하지 않는다.

```bash
kubectl -n kubernetes-dashboard get secret admin-token \
  -o jsonpath='{.data.token}' | base64 --decode
```

`admin-token`이 없으면 Namespace 삭제로 함께 삭제되었을 수 있다. 이 경우 관리자 Token/RBAC 복구를 별도 작업으로 분리하고, 기존 운영 RBAC 정책을 확인하기 전에는 임의로 `cluster-admin` 권한을 추가하지 않는다.

```bash
kubectl -n kubernetes-dashboard get secret admin-token
```

## 기록할 증거

- 실행 전 context와 Namespace/Ingress 조회 결과
- 현장 inventory의 `dashboard_enabled`, `dashboard_namespace` 확인 결과
- `--tags dashboard` 실행 결과
- Namespace, Deployment, Pod, Service, Endpoint, Ingress, 이벤트 검증 결과
- 적용한 Ingress annotation과 그 확인 결과
- Token 로그인 확인 결과 또는 Token/RBAC 복구를 분리한 사유

상세 사건 원문과 환경별 검증 결과: [[60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구]]
