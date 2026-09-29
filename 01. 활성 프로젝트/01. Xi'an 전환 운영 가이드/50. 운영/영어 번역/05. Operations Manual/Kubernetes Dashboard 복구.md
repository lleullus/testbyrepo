---
title: "Kubernetes Dashboard Recovery"
status: current
aliases:
  - Dashboard Namespace Recovery
doc_type: guide
scope: "Xi'an Transition Operations Guide"
updated: "2026-07-19"
---

# Kubernetes Dashboard Recovery

When the `kubernetes-dashboard` Namespace is deleted, do not redeploy the entire cluster. Check `dashboard_enabled` and `dashboard_namespace` in the environment inventory, then run only the Kubespray `dashboard` tag.

```bash
ansible-playbook \
  -e @inventory/dks/dks_vars.yml \
  -i inventory/dks/hosts.yaml \
  --become --become-user=root \
  --tags dashboard \
  cluster.yml
```

Check the Namespace, Pod, Service/Endpoint, Ingress, and events. Refer to the original incident record for the Ingress SSL passthrough and backend HTTPS settings, Token login, and RBAC considerations.

Detailed source material and environment-specific verification results: [[60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구|Kubernetes Dashboard Namespace Deletion Recovery]]
