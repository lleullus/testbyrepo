---
title: "Kubernetes Dashboard 恢复"
status: current
aliases:
  - Dashboard Namespace 恢复
doc_type: guide
scope: "Xi'an 切换运营指南"
updated: "2026-07-19"
---

# Kubernetes Dashboard 恢复

删除 `kubernetes-dashboard` Namespace 时，不要重新部署整个集群。确认现场 inventory 中的 `dashboard_enabled` 和 `dashboard_namespace` 后，仅执行 Kubespray Dashboard tag。

```bash
ansible-playbook \
  -e @inventory/dks/dks_vars.yml \
  -i inventory/dks/hosts.yaml \
  --become --become-user=root \
  --tags dashboard \
  cluster.yml
```

确认 Namespace、Pod、Service/Endpoint、Ingress 及事件。关于 Ingress 的 SSL passthrough 和 backend HTTPS 设置、Token 登录以及 RBAC 注意事项，以事件原文为准。

详细原文和按环境的验证结果：[[60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구|Kubernetes Dashboard Namespace 删除恢复]]
