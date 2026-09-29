---
title: "dev-apps-pa01-xas Monitoring 복붙 오적용"
doc_type: incident
status: current
case_status: resolved
scope: "dev-apps-pa01-xas custom monitoring stack"
updated: "2026-07-19"
parent: "[[60. 이슈 및 결정/이슈 및 결정 안내|이슈 및 결정 안내]]"
---

# dev-apps-pa01-xas Monitoring 복붙 오적용

## 타임라인과 영향

2026-07-14, Taylor/Host 절차를 Member Apps에 복사하면서 External ETCD Endpoints와 Grafana datasource Namespace가 잘못 적용되었다. Pod, PVC, Ingress는 정상이었지만 ETCD target과 Grafana 데이터 조회가 실패했다.

| 항목 | 잘못된 값 | 정상 값 | 조치 |
|---|---|---|---|
| ETCD Endpoints | `109.156.22.41~43` | `109.156.22.70~72` | `etcd-k8s` Endpoints 또는 manifest 수정 후 apply |
| Grafana datasource | `prometheus-k8s.kubesphere-monitoring-system.svc:9090` | `prometheus-k8s.monitoring.svc:9090` | datasource manifest 적용 후 Grafana rollout restart |

## 완료 기준

- Prometheus Targets에서 `etcd-k8s`가 `UP`
- Grafana Data source Save & Test 성공 및 대시보드 값 표시

현재 적용해야 할 기준값과 복붙 방지 표는 [[30. 구축 및 전환/Member 클러스터/개요#복붙 방지 기준|Member 클러스터 복붙 방지 기준]]에서 관리한다. 클러스터의 현재 사실값은 [[10. 기준 및 설계/클러스터 카탈로그/04. dev-apps-pa01-xas|dev-apps-pa01-xas 카탈로그]]에서 관리한다.
