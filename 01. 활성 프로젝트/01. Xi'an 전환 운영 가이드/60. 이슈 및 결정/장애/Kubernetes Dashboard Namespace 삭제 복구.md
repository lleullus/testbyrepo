---
title: "Kubernetes Dashboard Namespace 삭제 복구"
created: "2026-07-03"
updated: "2026-07-19"
status: current
case_status: resolved
doc_type: incident
scope: "Host Cluster Kubernetes Dashboard Namespace 삭제 사건"
parent: "[[60. 이슈 및 결정/이슈 및 결정 안내|이슈 및 결정 안내]]"
tags:
  - dks
  - cluster-setup
  - monitoring
  - kubesphere
  - prometheus
  - grafana
aliases:
  - Dashboard Namespace 삭제 사건
---

# Kubernetes Dashboard Namespace 삭제 복구

재사용 가능한 실행 절차는 [[50. 운영/05. Operations Manual/Kubernetes Dashboard 복구]]에서 관리한다. 아래는 사건 원문과 환경별 확인 기록이다.

## 사건 기록: Kubernetes Dashboard Namespace 및 Ingress 복구

### 6-1. 발생 상황

Host Cluster에 Kubespray와 KubeSphere 구성을 완료한 뒤, 운영자가 실수로 `kubernetes-dashboard` Namespace를 삭제했습니다.

이번 장애에서 구분해야 할 Namespace는 다음과 같습니다.

| Namespace | 역할 | 이번 장애와의 관계 |
|---|---|---|
| `kubernetes-dashboard` | Kubespray가 배포한 Kubernetes Dashboard | 삭제된 대상 |
| `kubesphere-system` | KubeSphere Console/API/Controller | 삭제하지 않음 |
| `kubesphere-monitoring-system` | KubeSphere Monitoring | 삭제하지 않음 |

`kubernetes-dashboard` Namespace를 삭제하면 해당 Namespace 안의 Dashboard Deployment, Service, ServiceAccount, Secret, RBAC Role/RoleBinding 및 Ingress가 함께 삭제될 수 있습니다. 따라서 KubeSphere installer를 다시 실행하는 것이 아니라 Kubespray Dashboard 배포 절차로 복구해야 합니다.

### 6-2. 복구 전 확인

Kubespray 작업 디렉터리는 원격 Bastion에 있으며, 현재 환경의 실제 경로는 다음과 같습니다.

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19
```

Dashboard 관련 Kubespray 파일 위치를 확인합니다.

```bash
find roles/kubernetes-apps/ansible -type f \( -iname "*dashboard*" \) -print
```

확인된 주요 파일:

```text
roles/kubernetes-apps/ansible/tasks/dashboard.yml
roles/kubernetes-apps/ansible/templates/dashboard.yml.j2
```

Dashboard 활성화 여부와 Namespace 값을 확인합니다.

```bash
grep -RniE "dashboard_enabled|dashboard_namespace" \
  inventory/dks roles/kubernetes-apps/ansible
```

이번 Xi'an Host Cluster의 실제 설정은 다음과 같았습니다.

```yaml
# inventory/dks/group_vars/k8s_cluster/addons.yml
dashboard_enabled: true
dashboard_namespace: kubernetes-dashboard
```

Kubespray role 기본값에는 `dashboard_namespace: kube-system`이 있을 수 있으므로, 실행 전 현장 inventory의 override 값을 반드시 확인해야 합니다. 이번 환경에서는 `inventory/dks/group_vars/k8s_cluster/addons.yml`의 `kubernetes-dashboard` 설정이 실제 적용값입니다.

### 6-3. Dashboard Namespace 및 리소스 복구

전체 클러스터를 재배포하지 않고 Kubespray의 `dashboard` tag만 실행합니다.

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19

ansible-playbook \
  -e @inventory/dks/dks_vars.yml \
  -i inventory/dks/hosts.yaml \
  --become --become-user=root \
  --tags dashboard \
  cluster.yml
```

이번 환경에서는 위 명령으로 `kubernetes-dashboard` Namespace와 Dashboard 리소스가 복구되었고, 기존 Dashboard Ingress도 재생성되었습니다. 따라서 해당 환경에서는 Ingress를 별도 YAML로 새로 만들기 전에 먼저 동일한 Kubespray `dashboard` tag 실행 결과를 확인합니다.

복구 직후 확인합니다.

```bash
kubectl get ns kubernetes-dashboard
kubectl get all -n kubernetes-dashboard
kubectl get sa,secret -n kubernetes-dashboard
kubectl get ingress -n kubernetes-dashboard
kubectl get events -n kubernetes-dashboard --sort-by=.lastTimestamp
```

정상 기준:

- `kubernetes-dashboard` Namespace가 `Active`
- Dashboard Deployment/Pod가 `Running`
- `kubernetes-dashboard` Service와 Endpoint가 존재
- Dashboard Ingress가 존재
- ImagePull, Scheduling, TLS handshake 관련 오류가 없음

> [!warning] Ingress 재생성 범위
> 이번 환경에서 `--tags dashboard` 실행 후 Ingress가 다시 생성되었지만, 이는 현장 Kubespray bundle 또는 후속 task의 실제 동작을 기준으로 기록한 것입니다. 다른 Kubespray 버전이나 수정되지 않은 원본에서는 Dashboard template에 Ingress가 없을 수 있으므로, 실행 전 `roles/kubernetes-apps/ansible/templates/dashboard.yml.j2`와 실제 playbook 결과를 확인합니다.

### 6-4. Dashboard Ingress 및 Fake Certificate 확인

이번 환경의 Alertmanager, Prometheus, KubeSphere Console, Grafana, Kubernetes Dashboard Ingress는 다음과 같은 공통 구조를 사용했습니다.

- 외부 Load Balancer 주소: `109.156.22.47`, `109.156.22.48`, `109.156.22.49`
- Kubernetes Ingress 출력의 PORTS: `80`
- Kubernetes Ingress의 `spec.tls` Secret: 없음
- HTTPS 요청 시 Ingress Controller의 기본 self-signed Fake Certificate 사용

전체 Ingress 상태 확인:

```bash
kubectl get ing -A
```

특정 Ingress 원문 확인:

```bash
kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress -o yaml
kubectl -n kubesphere-monitoring-system get ingress alertmanager-main-ingress -o yaml
```

실제 외부에서 전달되는 인증서 확인:

```bash
openssl s_client \
  -connect dashboard.apps.xaprdpa01.mgmt.dks.samsungds.net:443 \
  -servername dashboard.apps.xaprdpa01.mgmt.dks.samsungds.net \
  </dev/null 2>&1 | \
  grep -E 'subject=|issuer=|Verify return code'

openssl s_client \
  -connect alertmanager.xaprdpa01.mgmt.dks.samsungds.net:443 \
  -servername alertmanager.xaprdpa01.mgmt.dks.samsungds.net \
  </dev/null 2>&1 | \
  grep -E 'subject=|issuer=|Verify return code'
```

Alertmanager에서 확인된 결과:

```text
subject=O = Acme Co, CN = Kubernetes Ingress Controller Fake Certificate
issuer=O = Acme Co, CN = Kubernetes Ingress Controller Fake Certificate
Verify return code: 18 (self signed certificate)
```

이 환경에서 KubeSphere Console 및 Alertmanager가 같은 Fake Certificate 구조로 동작하므로, 폐쇄망 운영 정책상 Dashboard도 별도 2-tier 인증서나 TLS Secret을 추가하지 않고 동일한 Fake Certificate 구조를 유지합니다.

> [!important] Fake Certificate와 TLS Secret
> Fake Certificate를 동일하게 사용한다는 것은 별도의 `dashboard-tls` Secret을 생성한다는 의미가 아닙니다. Ingress에 `spec.tls`를 추가하지 않고 Ingress Controller의 기본 인증서를 사용하는 현재 구조를 유지한다는 의미입니다. 브라우저의 인증서 경고는 폐쇄망 운영 정책에 따라 승인하되, 외부 공개 환경에는 적용하지 않습니다.

### 6-5. SSL Passthrough 및 Backend Protocol 처리

처음에는 Dashboard Ingress가 Dashboard Pod의 자체 인증서를 직접 전달하는 SSL passthrough 경로로 동작할 수 있습니다. 이 경우 Dashboard 도메인으로 접속했을 때 Dashboard Pod가 자동 생성한 self-signed 인증서가 노출되어 Alertmanager의 Ingress Controller Fake Certificate와 결과가 다르게 보일 수 있습니다.

Dashboard를 Alertmanager와 같은 Ingress Controller Fake Certificate 경로로 전환할 때는 기존 Ingress의 SSL passthrough annotation을 제거합니다.

```bash
kubectl -n kubernetes-dashboard annotate ingress kubernetes-dashboard-ingress \
  nginx.ingress.kubernetes.io/ssl-passthrough-
```

Dashboard Service 자체는 `443 -> 8443` HTTPS backend이므로, Frontend 인증서와 별개로 Ingress Controller와 Dashboard Service 사이 연결은 HTTPS로 지정합니다.

```bash
kubectl -n kubernetes-dashboard annotate ingress kubernetes-dashboard-ingress \
  nginx.ingress.kubernetes.io/backend-protocol="HTTPS" \
  --overwrite
```

두 설정의 의미는 서로 다릅니다.

```text
브라우저 -- HTTPS / Ingress Controller 기본 Fake Certificate --> Ingress
Ingress Controller -- HTTPS / Service 443 --> Dashboard Pod 8443
```

- `ssl-passthrough-`: Dashboard Pod의 자체 인증서를 외부에 직접 노출하지 않음
- `backend-protocol: HTTPS`: Ingress Controller가 Dashboard Service backend에 HTTPS로 연결
- Fake Certificate: 브라우저와 Ingress Controller 사이에서 사용되는 인증서

Annotation 적용 여부 확인:

```bash
kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress \
  -o jsonpath='{.metadata.annotations.nginx\.ingress\.kubernetes\.io/ssl-passthrough}{"\n"}'

kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress \
  -o jsonpath='{.metadata.annotations.nginx\.ingress\.kubernetes\.io/backend-protocol}{"\n"}'
```

첫 번째 출력은 비어 있어야 하고, 두 번째 출력은 `HTTPS`여야 합니다. Annotation 변경 후 Ingress Controller 전체 재시작은 기본적으로 필요하지 않습니다.

### 6-6. 브라우저 접속 및 Token 로그인

Dashboard 접속 URL:

```text
https://dashboard.apps.xaprdpa01.mgmt.dks.samsungds.net
```

로그인 화면에서는 `Token`을 선택합니다. `kubeconfig`는 선택하지 않습니다.

```bash
kubectl -n kubernetes-dashboard get secret admin-token \
  -o jsonpath='{.data.token}' | base64 --decode
```

출력된 Token 한 줄 전체를 Dashboard Token 입력란에 붙여넣습니다.

`admin-token`이 없는 경우:

```bash
kubectl -n kubernetes-dashboard get secret admin-token
```

`NotFound`이면 Namespace 삭제 때 해당 Secret도 함께 삭제된 것입니다. 이 경우 Dashboard Namespace/Service 복구와 관리자 Token 복구를 별도 작업으로 구분해야 하며, 임의로 `cluster-admin` 권한을 추가하지 말고 기존 운영 RBAC 정책을 확인합니다.

### 6-7. 최종 장애 처리 결과

이번 장애의 실제 복구 순서는 다음과 같습니다.

1. `kubernetes-dashboard` Namespace 삭제 사실 확인
2. 원격 Bastion의 Kubespray role 및 inventory 확인
3. `dashboard_enabled: true`, `dashboard_namespace: kubernetes-dashboard` 확인
4. `--tags dashboard`로 Kubespray Dashboard 리소스 및 현장 Ingress 복구
5. Dashboard Ingress에서 SSL passthrough 제거
6. Dashboard backend 연결에 `backend-protocol: HTTPS` 적용
7. Alertmanager와 동일한 Ingress Controller Fake Certificate 경로 확인
8. Dashboard Service/Endpoint/Pod 상태 확인
9. Dashboard Token 조회 후 Token 방식으로 로그인

최종적으로 KubeSphere Console 및 Alertmanager와 동일하게 폐쇄망의 Fake Certificate를 사용하면서, Dashboard backend는 HTTPS로 연결하는 구조로 접속을 복구했습니다.

### 6-8. 재발 방지 체크리스트

- [ ] 운영 작업 전 `kubectl get ns`, `kubectl get ing -A` 상태 저장
- [ ] `kubernetes-dashboard`와 `kubesphere-system` Namespace 구분
- [ ] Kubespray 실행 전 `dashboard_enabled`, `dashboard_namespace` 확인
- [ ] Dashboard 복구 시 전체 `cluster.yml`이 아닌 `--tags dashboard` 사용
- [ ] Dashboard Ingress 삭제 시 먼저 동일 Kubespray tag로 재생성 여부 확인
- [ ] Fake Certificate 사용 환경에서 불필요한 TLS Secret 생성 금지
- [ ] `ssl-passthrough`와 `backend-protocol`의 역할을 구분
- [ ] `ssl-passthrough`는 제거하고 backend protocol은 Dashboard Service에 맞게 `HTTPS`로 확인
- [ ] Dashboard 로그인은 Token 방식 사용
- [ ] Token, kubeconfig, 인증서 private key 등 민감정보를 문서에 기록하지 않음
