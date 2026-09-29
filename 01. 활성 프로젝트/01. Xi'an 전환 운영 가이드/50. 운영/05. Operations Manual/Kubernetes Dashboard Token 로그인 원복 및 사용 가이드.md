---
title: "Kubernetes Dashboard Token 로그인 원복 및 사용 가이드"
created: "2026-08-11"
updated: "2026-08-13"
status: review
doc_type: guide
scope: "Xi'an Host Cluster Kubernetes Dashboard 인증 원복"
parent: "[[50. 운영/01. Operations Overview/운영 안내|운영 안내]]"
aliases:
  - Dashboard Skip 로그인 원복
  - Dashboard Token 로그인 복구
  - Kubernetes Dashboard 인증 원복
---

# Kubernetes Dashboard Token 로그인 원복 및 사용 가이드

> [!summary] 문서 역할
> 이 문서는 현재 `Skip` 버튼으로 인증 없이 진입하도록 임시 구성한 Xi'an Kubernetes Dashboard를, 기존 Xi'an 구축 기록에 남아 있는 **Token 로그인 방식**으로 되돌리고 실제 운영자가 Token을 확인해 로그인하는 절차를 정리한 새 동반 가이드다. 기존 [[50. 운영/05. Operations Manual/Kubernetes Dashboard 복구|Kubernetes Dashboard 복구]] 및 [[60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구|Dashboard Namespace 삭제 복구 사건 기록]]을 수정하거나 대체하지 않는다.

**행위자:** Xi'an Host Cluster에서 `kubectl`로 `kubernetes-dashboard` Namespace와 Dashboard Deployment를 조회·변경할 수 있는 운영 담당자가 수행한다.

**독자:** Kubernetes Dashboard의 인증 우회 상태를 원복하고 Token 방식으로 접속해야 하는 Xi'an 운영 담당자가 사용한다.

**발동 조건:** Dashboard 로그인 화면에 `Skip` 버튼을 활성화해 Token 없이 진입하는 현재 임시 구성을 종료하고, 원래 Xi'an 문서에 기록된 Token 로그인 방식으로 복구해야 할 때 이 절차를 사용한다.

> [!important] 이번 작업의 핵심
> - Dashboard Namespace 자체를 재구축하는 작업이 아니다.
> - Ingress·TLS·KubeSphere·Monitoring 구성을 새로 설계하는 작업이 아니다.
> - `cluster-admin`이나 새 RBAC을 임의로 만드는 작업이 아니다.
> - **Skip 로그인 활성화 원인을 확인해 그 설정만 제거하고, 기존 `admin-user`의 Token을 확인해 로그인하는 작업**이다.

---

## 1. 확인된 기준과 이번 원복 방향

Xi'an 원본 구축 문서에는 Kubernetes Dashboard UI 접속 시 `admin-user` ServiceAccount를 확인하고, 연결된 `admin-user-token-*` Secret의 Token을 디코드해 로그인한 기록이 남아 있다.

반면 Dashboard Namespace 삭제 복구 사건 문서에는 Token 조회 예시가 고정 이름 `admin-token`으로 기록되어 있다. 두 기록의 Secret 이름이 일치하지 않으므로, 이번 가이드에서는 `admin-token`이라는 이름을 전제로 하지 않고 **`admin-user` ServiceAccount에 실제 연결된 Token Secret을 조회하는 방식**을 기준으로 한다.

현재 작업 요청에서 확인된 상태는 Dashboard 로그인 화면에 `Skip` 버튼을 활성화해 Token 입력 없이 진입하도록 임시 구성했다는 것이다. 따라서 원복 목표는 다음과 같다.

| 항목 | 원복 후 기준 |
|---|---|
| Dashboard Namespace | `kubernetes-dashboard` 유지 |
| Dashboard 배포 | 현재 정상 동작 리소스 유지 |
| Skip 로그인 | 비활성화 |
| 로그인 방식 | `Token` 선택 후 인증 |
| 로그인 주체 | 기존 `admin-user` ServiceAccount 기준 |
| Token 획득 | 기존 `admin-user-token-*` Secret 사용 |
| RBAC | 현재 승인된 기존 정책 확인 후 그대로 사용. 새 `cluster-admin` 부여 금지 |
| Ingress/TLS | 이번 작업에서 임의 변경하지 않음 |

---

## 2. 변경 전 현재 상태 확인

### 2-1. 대상 Cluster와 Dashboard 리소스 확인

먼저 현재 `kubectl` 대상과 Dashboard 리소스가 맞는지 확인한다.

```bash
kubectl config current-context
kubectl get ns kubernetes-dashboard
kubectl -n kubernetes-dashboard get deploy,pod,svc,endpoints,ingress
```

정상적으로 확인해야 할 대상은 다음과 같다.

- Namespace: `kubernetes-dashboard`
- Dashboard Deployment 및 Pod
- Dashboard Service와 Endpoint
- `kubernetes-dashboard-ingress`

Dashboard Namespace가 없거나 Pod가 정상 상태가 아니면 이 문서의 인증 원복을 먼저 진행하지 않는다. 그 경우에는 [[50. 운영/05. Operations Manual/Kubernetes Dashboard 복구|Kubernetes Dashboard 복구]] 절차로 범위를 분리한다.

### 2-2. 실제 Dashboard Deployment 이름과 실행 인자 확인

```bash
kubectl -n kubernetes-dashboard get deploy
```

현재 Xi'an 원본 기록의 Pod 이름은 `kubernetes-dashboard-*` 패턴이므로, Deployment 이름도 실제 조회 결과로 확인한 뒤 아래 명령의 `kubernetes-dashboard` 부분을 사용한다.

```bash
kubectl -n kubernetes-dashboard get deploy kubernetes-dashboard -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\t"}{.args}{"\n"}{end}'
```

출력에서 `enable-skip-login`이 포함되어 있는지 확인한다.

예상되는 확인 대상:

```text
--enable-skip-login
```

또는

```text
--enable-skip-login=true
```

> [!warning] 조건부 변경
> 위 인자가 실제 Deployment에 확인될 때만 제거한다. `Skip` 버튼은 보이지만 Deployment args에 해당 설정이 없다면 추정으로 다른 인자를 삭제하지 않는다. 이 경우 현재 Pod args와 Kubespray 원본/override 위치를 추가 확인한 뒤 작업을 분리한다.

### 2-3. Kubespray 원본 또는 현장 override에도 Skip 설정이 남아 있는지 확인

Dashboard Namespace 삭제 복구 기록에 남은 Xi'an Kubespray 작업 경로는 다음과 같다.

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19
```

현장 inventory와 Dashboard role에서 Skip 설정을 검색한다.

```bash
grep -Rni -- 'enable-skip-login' inventory/dks roles/kubernetes-apps/ansible
```

Dashboard 관련 원본 확인 위치:

```text
roles/kubernetes-apps/ansible/tasks/dashboard.yml
roles/kubernetes-apps/ansible/templates/dashboard.yml.j2
inventory/dks/group_vars/k8s_cluster/addons.yml
```

판정:

- **검색 결과 있음:** 현재 live Deployment뿐 아니라 Kubespray 기준 파일 또는 현장 override에도 Skip 설정이 남아 있을 수 있으므로, 검색된 실제 파일에서 `enable-skip-login` 인자만 제거 대상으로 잡는다.
- **검색 결과 없음 + live Deployment에는 있음:** live Deployment에만 임시 변경이 들어간 것으로 보고 Deployment 쪽 인자만 제거한다.
- **검색 결과 없음 + live Deployment에도 없음:** 이 문서로 변경하지 않고 원인을 추가 확인한다.

> [!important] 기준본 유지
> Kubespray 쪽에 `enable-skip-login`이 남아 있으면 live Deployment만 수정해도 향후 Dashboard tag 재적용 시 다시 들어올 수 있다. 따라서 실제 검색 결과가 있는 경우에는 **기준 파일의 해당 인자와 live Deployment의 해당 인자를 둘 다 제거 대상으로 관리**한다.

---

## 3. 기존 `admin-user`와 RBAC 확인

Skip 로그인을 끄기 전에 Token으로 로그인할 기존 주체가 실제로 있는지 확인한다.

```bash
kubectl -n kubernetes-dashboard get sa admin-user
```

원본 Xi'an 구축 기록에서는 다음 상태가 확인되어 있었다.

```text
NAME         SECRETS   AGE
admin-user   1         ...
```

현재도 `admin-user`가 존재하면 다음으로 진행한다.

### 3-1. 현재 권한 확인

가능한 환경에서는 기존 `admin-user`가 실제로 어떤 권한을 가지는지 확인한다.

```bash
kubectl auth can-i --as=system:serviceaccount:kubernetes-dashboard:admin-user --list
```

위 조회가 현재 운영 계정의 impersonation 권한 때문에 실패하면 RBAC 리소스에서 `admin-user` subject를 확인한다.

```bash
kubectl -n kubernetes-dashboard get rolebinding -o yaml
kubectl get clusterrolebinding -o yaml
```

확인 목적은 **기존 운영 RBAC을 식별하는 것**이다. 이 단계에서 `admin-user`가 없거나 기존 binding을 확인할 수 없다고 해서 새 `cluster-admin` binding을 만들지 않는다.

> [!danger] 중단 조건
> `admin-user` ServiceAccount가 없거나, 기존 운영 RBAC이 무엇인지 확인되지 않으면 Skip 로그인부터 제거하지 않는다. 원본 문서에는 `admin-user` 생성 및 새 ClusterRoleBinding을 만드는 절차가 확인되지 않으므로, 임의 생성 대신 기존 Kubespray/운영 RBAC 기준을 먼저 확인해야 한다.

### 3-2. Skip 제거 전 Token 로그인 사전 검증

**이 단계가 성공하기 전에는 4장의 Skip 로그인 제거를 수행하지 않는다.** 현재 Skip 진입이 가능한 상태를 유지한 채, 별도 Private/Incognito 창에서 Token 로그인이 실제로 되는지 먼저 검증한다.

Xi'an Kubernetes `v1.22.10`에서는 원본 Xi'an 방식으로 기존 연결 Secret을 찾는다.

```bash
kubectl -n kubernetes-dashboard get sa admin-user -o jsonpath='{.secrets[*].name}{"\n"}'
```

출력된 `admin-user-token-*` Secret의 Token을 확인한다.

```bash
kubectl -n kubernetes-dashboard get secret <ADMIN_USER_TOKEN_SECRET> -o jsonpath='{.data.token}' | base64 --decode; printf '\n'
```

Token을 얻었으면 현재 Skip 버튼을 아직 제거하지 않은 상태에서 새 Private/Incognito 창으로 Dashboard에 접속하고, `Skip`을 누르지 말고 `Token` 방식을 선택해 로그인한다.

사전 검증 완료 조건:

- 기존 `admin-user`로 Token을 획득할 수 있음
- Token 입력으로 Dashboard 로그인에 성공함
- Token 원문을 문서·메신저·화면 캡처에 남기지 않음

> [!danger] 사전 검증 실패
> Token을 얻지 못하거나 Token 로그인에 실패하면 여기서 중단한다. 현재 Skip 설정은 그대로 두고 원인을 확인하며, Token 로그인 경로가 확보되기 전에 인증 우회 설정부터 제거하지 않는다.

---

## 4. Skip 로그인 설정 원복

### 4-1. Kubespray 기준 파일에 설정이 있으면 먼저 제거

2-3 검색에서 `enable-skip-login`이 Kubespray template 또는 inventory override에서 확인된 경우, **검색된 실제 파일에서 해당 인자 한 줄만 제거**한다.

예:

```text
- --enable-skip-login
```

또는

```text
- --enable-skip-login=true
```

이 작업만을 위해 전체 `cluster.yml`을 다시 실행하지 않는다. Dashboard Namespace 삭제 복구 때 사용한 `--tags dashboard`는 삭제된 Dashboard 리소스를 재생성하는 절차이며, 이번 작업은 인증 인자 하나를 원복하는 범위다.

### 4-2. Live Deployment에서 Skip 인자 제거

현재 Deployment를 편집한다.

```bash
kubectl -n kubernetes-dashboard edit deployment kubernetes-dashboard
```

Dashboard container의 `args:`에서 확인된 다음 인자만 삭제한다.

```text
--enable-skip-login
```

또는

```text
--enable-skip-login=true
```

다른 인자는 이번 작업에서 변경하지 않는다.

저장 후 rollout을 확인한다.

```bash
kubectl -n kubernetes-dashboard rollout status deployment/kubernetes-dashboard
kubectl -n kubernetes-dashboard get pod -o wide
```

그리고 인자가 실제로 제거되었는지 재확인한다.

```bash
kubectl -n kubernetes-dashboard get deploy kubernetes-dashboard -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\t"}{.args}{"\n"}{end}'
```

`enable-skip-login`이 더 이상 출력되지 않아야 한다.

### 4-3. Ingress가 기존 상태를 유지하는지 확인

이번 작업은 Deployment args만 변경하므로 Ingress를 임의 수정하지 않는다. 다만 기존 Dashboard 복구 사건에서 확정한 Ingress 상태가 유지되는지는 확인한다.

```bash
kubectl -n kubernetes-dashboard get ingress kubernetes-dashboard-ingress -o yaml
```

기존 사건 기록 기준:

- `nginx.ingress.kubernetes.io/ssl-passthrough`는 제거된 상태
- `nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"`

이 두 값이 이번 작업 전후로 바뀌지 않아야 한다.

---

## 5. Dashboard 로그인 Token 획득

### 5-1. 기존 연결 Token Secret 사용

Xi'an Kubernetes `v1.22.10`에서는 원본 Xi'an 구축 기록과 동일하게 ServiceAccount에 연결된 Secret 이름을 조회한다.

```bash
kubectl -n kubernetes-dashboard get sa admin-user -o jsonpath='{.secrets[*].name}{"\n"}'
```

원본 Xi'an 구축 기록에서는 다음과 같은 동적 이름이 확인되었다.

```text
admin-user-token-jsjxf
```

Secret 이름은 고정값으로 보지 않고 현재 출력값을 사용한다.

예를 들어 출력값이 `<ADMIN_USER_TOKEN_SECRET>`이라면 Token을 다음처럼 확인한다.

```bash
kubectl -n kubernetes-dashboard get secret <ADMIN_USER_TOKEN_SECRET> -o jsonpath='{.data.token}' | base64 --decode; printf '\n'
```

출력된 한 줄 전체가 Dashboard 로그인에 사용할 Token이다.

> [!warning] Token 취급
> Token 원문은 Obsidian, 작업보고서, 메신저, 화면 캡처, 게시 산출물에 기록하지 않는다. 필요한 로그인 시점에 터미널에서 확인해 사용하고, 문서에는 Secret 이름과 Token 값을 복사하지 않는다.

> [!note] 원본 절차와의 관계
> Xi'an 구축 원문과 동일하게 `admin-user-token-*` Secret을 직접 디코드한다. 로그인 주체와 기존 RBAC은 원본의 `admin-user`를 유지하며, 새 장기 Token Secret은 이 문서에서 만들지 않는다.

### 5-2. Token을 얻지 못하면

다음 중 하나면 작업을 중단한다.

- `admin-user`가 없음
- 기존 RBAC을 확인할 수 없음
- ServiceAccount에 연결된 Token Secret이 없음
- Token은 발급되지만 Dashboard 로그인 시 `Unauthorized` 또는 권한 오류가 발생함

이 경우 Token 문제를 이유로 다시 `Skip` 로그인을 기본 운영 방식으로 되돌리지 않는다. 먼저 `admin-user`의 기존 RBAC과 현재 Kubernetes/Dashboard 버전에 맞는 Token 발급 경로를 별도 확인한다.

---

## 6. 브라우저에서 Token 로그인

Xi'an Dashboard 사건 기록에 확인된 접속 URL:

```text
https://dashboard.apps.xaprdpa01.mgmt.dks.samsungds.net
```

접속 후 로그인 화면에서 다음 순서로 수행한다.

1. 브라우저에서 Dashboard URL을 연다.
2. 로그인 방식에서 `Token`을 선택한다.
3. 5장에서 확인한 Token 한 줄 전체를 입력한다.
4. 로그인한다.

기존 Xi'an 기록에서는 `kubeconfig`가 아니라 `Token` 로그인을 사용했다.

Skip 로그인 제거 확인은 기존 브라우저 세션의 영향을 피하기 위해 새 Private/Incognito 창에서도 다시 확인한다.

정상 기준:

- 로그인 화면에 `Skip` 버튼이 더 이상 제공되지 않음
- Token 입력 화면이 표시됨
- 유효한 `admin-user` Token으로 로그인 가능
- Token 없이 Dashboard 내부 화면으로 진입할 수 없음

---

## 7. 완료 확인

### 7-1. Kubernetes 리소스

```bash
kubectl -n kubernetes-dashboard get deploy,pod,svc,endpoints,ingress
```

확인:

- Dashboard Deployment 정상
- Pod `Running`
- Service 및 Endpoint 존재
- Ingress 존재

### 7-2. Skip 인자 제거

```bash
kubectl -n kubernetes-dashboard get deploy kubernetes-dashboard -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{"\t"}{.args}{"\n"}{end}'
```

`enable-skip-login`이 없어야 한다.

### 7-3. Kubespray 기준 파일

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19

grep -Rni -- 'enable-skip-login' inventory/dks roles/kubernetes-apps/ansible
```

이번 현장 커스텀으로 추가했던 Skip 설정이 기준 파일에 더 이상 남아 있지 않아야 한다. 검색 결과가 Kubespray 원본의 다른 설명이나 사용하지 않는 파일에서 나오는 경우에는 실제 적용 파일인지 구분해 기록한다.

### 7-4. 브라우저

- 새 브라우저 세션에서 Dashboard 접속
- Skip 버튼 없음 확인
- Token 로그인 성공 확인
- Token 없이 내부 화면 진입 불가 확인

---

## 8. 실패 시 분기

| 증상 | 판단 | 다음 조치 |
|---|---|---|
| `admin-user`가 없음 | 원본 Xi'an 로그인 주체가 현재 없음 | 새 `cluster-admin`을 만들지 말고 기존 운영 RBAC/Kubespray 기준 확인 |
| `admin-user`는 있으나 연결된 Token Secret이 없음 | 사용 가능한 Token 발급 경로가 현재 확인되지 않음 | Skip 제거를 진행하지 말고 현재 Kubernetes/Dashboard Token 발급 경로 확인 |
| Token 발급은 되지만 로그인 실패 | 인증 주체 또는 RBAC 문제 가능 | 기존 `admin-user` binding과 Dashboard 로그 확인. 권한 임의 확대 금지 |
| Deployment args에 Skip 설정이 없음 | 다른 위치에서 Skip 동작을 만들었을 가능성 | 현재 Pod args와 Kubespray template/override 재확인 |
| live에서는 제거했는데 재배포 후 Skip이 다시 생김 | Kubespray 기준 파일/override에 설정이 남아 있음 | `enable-skip-login` 검색 결과의 실제 적용 파일에서 제거 |
| Dashboard Pod가 비정상 | 인증 원복 범위를 벗어남 | [[50. 운영/05. Operations Manual/Kubernetes Dashboard 복구|Kubernetes Dashboard 복구]]로 분리 |

---

## 9. 이번 문서에서 정하지 않는 사항

자료에서 확인되지 않은 다음 항목은 이 문서에서 새 기준으로 만들지 않는다.

- `admin-user`에 새 `cluster-admin`을 부여하는 방법
- 새로운 Dashboard 전용 Role/ClusterRole 설계
- 새로운 ServiceAccount 생성
- 새로운 장기 Token Secret 생성
- Dashboard Ingress FQDN 변경
- 새로운 TLS Secret 또는 인증서 정책
- Source CIDR 또는 방화벽 정책 변경
- Dashboard 버전 업그레이드 또는 다른 Web UI로의 전환
- KubeSphere 인증과 Dashboard 인증 통합

---

## 10. 근거 추적

| 사실 주장 | 근거 파일·섹션/행 |
|---|---|
| Xi'an 원본 Dashboard 로그인은 `admin-user` ServiceAccount의 Token을 사용함 | `30. 구축 및 전환/공통 구축/Xi'an/한국어/03.md` § `Ingress token으로 Kubernetes Dashboard UI login 테스트` |
| 원본 기록의 실제 Token Secret은 `admin-user-token-*` 형태이며 `kubernetes.io/service-account-token` 타입임 | `30. 구축 및 전환/공통 구축/Xi'an/한국어/03.md` § `Ingress token으로 Kubernetes Dashboard UI login 테스트` |
| 원본 기록은 Secret의 Token 값을 base64 decode 후 Dashboard Token 입력란에 붙여넣음 | `30. 구축 및 전환/공통 구축/Xi'an/한국어/03.md` § `Token value decode` |
| Dashboard Namespace는 `kubernetes-dashboard`이며 현장 inventory에서 `dashboard_enabled: true`, `dashboard_namespace: kubernetes-dashboard`가 확인됨 | `60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구.md` § `6-2. 복구 전 확인` |
| Xi'an Kubespray Dashboard 확인 파일은 `roles/kubernetes-apps/ansible/tasks/dashboard.yml`, `roles/kubernetes-apps/ansible/templates/dashboard.yml.j2`임 | `60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구.md` § `6-2. 복구 전 확인` |
| 기존 복구 사건에서 Dashboard 로그인은 `Token` 방식을 사용하고 `kubeconfig`는 사용하지 않음 | `60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구.md` § `6-6. 브라우저 접속 및 Token 로그인` |
| 기존 복구 사건은 `admin-token`이 없을 때 임의로 `cluster-admin`을 추가하지 말고 기존 운영 RBAC 정책을 확인하도록 함 | `60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구.md` § `6-6. 브라우저 접속 및 Token 로그인` |
| Dashboard Ingress는 SSL passthrough를 제거하고 backend protocol을 `HTTPS`로 둔 상태가 사건 최종 결과임 | `60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구.md` § `6-5. SSL Passthrough 및 Backend Protocol 처리`, § `6-7. 최종 장애 처리 결과` |
| Token과 kubeconfig 등 민감정보를 문서에 기록하지 않음 | `60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구.md` § `6-8. 재발 방지 체크리스트`; `70. 실제 업로드 산출물/00. 업로드 산출물 목록.md` § `사용 원칙` |
| 현재 Dashboard에 Skip 버튼을 활성화해 Token 없이 진입하도록 임시 구성함 | 현재 작업 요청, 2026-08-11 |
| Dashboard의 Skip 로그인 기능은 `enable-skip-login` 설정으로 활성화되는 기능임 | Kubernetes Dashboard 공식 저장소의 Skip login 관련 기록 |

---

## 관련 문서

- [[50. 운영/05. Operations Manual/Kubernetes Dashboard 복구|Kubernetes Dashboard 복구]]
- [[60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구|Kubernetes Dashboard Namespace 삭제 복구]]
- [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|Xi'an 공통 구축 03]]
- [[50. 운영/05. Operations Manual/05. Utilizing the Kubernetes Native API|Utilizing the Kubernetes Native API]]
