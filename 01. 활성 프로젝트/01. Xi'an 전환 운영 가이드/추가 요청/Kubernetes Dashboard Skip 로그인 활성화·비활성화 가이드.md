---
title: "Kubernetes Dashboard Skip 로그인 활성화·비활성화 가이드"
created: 2026-08-30
status: draft
tags:
  - kubernetes
  - dashboard
  - skip-login
scope: "Xi'an 전환 운영 가이드"
---

# Kubernetes Dashboard Skip 로그인 활성화·비활성화 가이드

## 1. 현재 인자 확인

```bash
kubectl -n kubernetes-dashboard get deploy kubernetes-dashboard -o jsonpath='{.spec.template.spec.containers[0].args}'
```

확인할 인자:

```text
--enable-skip-login
--disable-settings-authorizer
```

## 2. Skip 로그인 활성화

Live Deployment를 편집한다.

```bash
kubectl -n kubernetes-dashboard edit deployment kubernetes-dashboard
```

Dashboard container의 args:에 아래 두 인자를 추가한다.

```yaml
- --enable-skip-login
- --disable-settings-authorizer
```

저장 후 rollout 상태를 확인한다.

```bash
kubectl -n kubernetes-dashboard rollout status deployment/kubernetes-dashboard
```

활성화 확인:

```bash
kubectl -n kubernetes-dashboard get deploy kubernetes-dashboard -o jsonpath='{.spec.template.spec.containers[0].args}'
```

두 인자가 모두 출력되어야 한다.

새 브라우저 세션에서 Dashboard 로그인 화면에 Skip 버튼이 표시되는지 확인한다.

## 3. Skip 로그인 비활성화

Live Deployment를 편집한다.

```bash
kubectl -n kubernetes-dashboard edit deployment kubernetes-dashboard
```

Dashboard container의 args:에서 아래 두 인자를 모두 제거한다.

```yaml
- --enable-skip-login
- --disable-settings-authorizer
```

저장 후 rollout 상태를 확인한다.

```bash
kubectl -n kubernetes-dashboard rollout status deployment/kubernetes-dashboard
```

비활성화 확인:

```bash
kubectl -n kubernetes-dashboard get deploy kubernetes-dashboard -o jsonpath='{.spec.template.spec.containers[0].args}'
```

두 인자가 모두 없어야 한다.

새 브라우저 세션에서 Dashboard 로그인 화면에 Skip 버튼이 표시되지 않는지 확인한다.

## 4. Kubespray 기준본 확인

```bash
cd /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/DKS-Kubespray-v2.19

grep -RniE -- 'enable-skip-login|disable-settings-authorizer' inventory/dks roles/kubernetes-apps/ansible
```

활성화할 때:

- 실제 적용되는 template 또는 inventory override에 두 인자가 모두 있어야 한다.
- Live Deployment에도 두 인자가 모두 있어야 한다.

비활성화할 때:

- 실제 적용되는 template 또는 inventory override에서 두 인자를 모두 제거한다.
- Live Deployment에서도 두 인자를 모두 제거한다.

## 5. 완료 확인

| 상태 | 확인 기준 |
|---|---|
| Skip 활성화 | Deployment args에 두 인자 존재 + 새 브라우저에 Skip 버튼 표시 |
| Skip 비활성화 | Deployment args에 두 인자 없음 + 새 브라우저에 Skip 버튼 없음 |
| 재배포 기준 | Kubespray 실제 적용 파일과 Live Deployment의 두 인자 상태가 동일 |

## 근거

| 사실 주장 | 근거 |
|---|---|
| Xi'an Dashboard Namespace와 Deployment는 kubernetes-dashboard 기준으로 운영한다. | 50. 운영/05. Operations Manual/Kubernetes Dashboard Token 로그인 원복 및 사용 가이드.md L55–85 |
| 기존 원복 가이드는 --enable-skip-login을 Live Deployment와 Kubespray 기준본에서 확인·제거하도록 작성돼 있다. | 같은 문서 L76–134, L204–259 |
| Skip 로그인 구성 시 --enable-skip-login과 --disable-settings-authorizer 두 인자를 함께 사용한다. | Kubernetes Dashboard v2.x 공식 argument 문서 및 배포 예시 |
