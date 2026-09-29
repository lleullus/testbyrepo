---
title: "구축 마스터 Runbook"
created: "2026-07-03"
updated: "2026-07-21"
status: current
doc_type: runbook
scope: "Xi'an DKS 클러스터 구축 오케스트레이션"
parent: "[[00. 홈|Xi'an 전환 운영 가이드]]"
tags:
  - dks
  - cluster-setup
  - runbook
  - overview
aliases:
  - DKS Cluster Setup
  - 클러스터 구축 가이드
  - DKS Setup Guide
---

> [!warning] SCS 환경 주의
> SCS 환경은 HQ와 다를 수 있으므로 Node Pre-setting 단계(Step 1, 2)에서 예상치 못한 오류가 발생할 수 있습니다.

# 구축 마스터 Runbook

Xi'an DKS 클러스터 구축 실행의 유일한 시작점이다. Step 0의 환경 확인 원문을 보존하며, Step 1 이후에는 상세 절차 문서를 실행 기준으로 사용한다.

## 실행 오케스트레이션

| 단계 | 상세 절차 | 진입 조건 | 완료 조건 | 상태/주의 |
|---|---|---|---|---|
| Step 0 | 이 문서의 [[#0. 초기 VM 설정]] | VM/LB 요청 가능 | VIP, 디스크, Bastion 사용자 확인 | 환경 의존성은 [[20. 환경 준비/환경 준비 및 의존성]] 우선 확인 |
| Step 1 | [[30. 구축 및 전환/공통 구축/01. Bastion Node Pre-setting|Bastion Node Pre-setting]] | Step 0 완료 | 디스크, 사용자/권한, Bastion 설정, 사전 소프트웨어, Kubespray 준비 완료 | 상세 문서의 User and Permissions는 독립 단계(1-2) |
| Step 2 | [[30. 구축 및 전환/공통 구축/02. K8S Cluster Nodes Pre-setting|K8S Cluster Nodes Pre-setting]] | Bastion 및 inventory 준비 | 상세 문서에 명시된 실제 자동화 작업 검증 | NTP, Nameserver, SELinux, Firewall, Filesystem은 placeholder 또는 별도 확인 항목이며 완료로 가정하지 않음 |
| Step 3 | [[30. 구축 및 전환/공통 구축/03. Deploy DKS Cluster|Deploy DKS Cluster]] | 노드 사전 설정 검증 | Kubernetes 핵심 컴포넌트 및 API 연결 확인 | Inventory와 현장 설정값을 우선 |
| Step 4 | [[30. 구축 및 전환/공통 구축/04. Install Storage Components|Install Storage Components]] | Step 3 완료 | StorageClass 및 Test PVC 확인 | NFS mount 이슈는 [[60. 이슈 및 결정/문제/NFS PVC Mount 실패 - ONTAP 측 확인 요청]] 참조 |
| Step 5 | [[30. 구축 및 전환/Host 및 Member 구축 분기|Host 및 Member 구축 분기]] | Storage 검증 완료 | 대상 역할별 설치 및 Monitoring 확인 | Host/Member 절차를 혼용하지 않음 |

---

## 0. 초기 VM 설정

### 0-1. 사전 확인

- 모든 DKS Cluster 노드의 VM 설정(hostname, IP Address 등) 확인
- L4 Load-balancer 구성 테스트

| 확인 대상 | 확인 항목 | 확인 기준 |
|---|---|---|
| 전체 DKS Cluster 노드 | hostname, IP Address 등 VM 설정 | 현장 기준값과 일치 |
| ETCD 노드 | VM 템플릿의 파일시스템 용도 | `/var/lib/etcd` 사용을 위한 변경 필요 여부 확인 |
| Load Balancer | VIP-A/B의 Master Node 및 Router Node routing | backend HTTP 응답 확인 |
| Bastion 노드 | DATA Disk, `dspaas` 사용자 그룹 | `0-2-1`, `0-2-2` 상세 절차 완료 |

> [!note] ETCD 노드
> ETCD 노드는 VM 템플릿에서 적용된 파일 시스템을 변경해야 합니다 (`/var/lib/containerd → /var/lib/etcd`).

> [!note] dspaas 사용자
> 신규 클러스터 VM 요청 시 `dspaas` 사용자는 기본적으로 `wheel` 그룹에 추가되어야 합니다. 자동 추가가 안 됐으면 `usermod -G wheel dspaas`로 수동 추가.

### 0-1-1. Alert exception request against Load Balancer

Load Balancer에 대한 alert exception을 DS Cloud service desk에 요청합니다.

```text
=====================
To DS Cloud Service Desk
■ Cluster:
■ LB Virtual server name:
■ IP Address:
■ Period for exception
  Start date/time:
  End date/time:
=====================
```

> [!warning] DS Cloud Service Desk 사전 통보
> LB VS의 service down detection 제외를 위해 작업 정보는 DS Cloud Service Desk에 **사전 통보**해야 합니다. 사전 통보 없이 2회 이상 broadcast 발생 시 LB VS의 service down detection은 제외 처리됩니다.

### 0-1-2. Verify VIP-A/B

Load Balancer (VIP-A & VIP-B)가 Master Node와 Router Node로 traffic을 routing하는지 확인합니다.

각 노드에서 backend으로 simple HTTP server 실행 후 LB IP로 curl 호출:

```bash
# Backend HTTP server 실행 (각 노드에서)
python3 -m http.server <backend_port_number>

# LB 경유 확인
curl http://<load_balancer_IP>:<port_number>
```

### 0-2. 디스크 파티션 및 사용자 설정 (Bastion 노드)

> Bastion VM의 디스크/사용자 설정 절차는 [[30. 구축 및 전환/공통 구축/01. Bastion Node Pre-setting#0-2-x. Bastion VM 디스크 및 사용자 설정|01. Bastion Node Pre-setting §0-2-x]] 참조.

| 작업 | 실행자 | 상세 절차 |
|------|--------|----------|
| 0-2-1. DATA Disk 파티션 설정 | ROOT | [[30. 구축 및 전환/공통 구축/01. Bastion Node Pre-setting#0-2-1. Modifying DATA Disk partition|Bastion §0-2-1]] |
| 0-2-2. 'dspaas' 사용자 그룹 확인 | ROOT | [[30. 구축 및 전환/공통 구축/01. Bastion Node Pre-setting#0-2-2. Confirm 'dspaas' user group|Bastion §0-2-2]] |

### Step 0 완료 기준

- [ ] 모든 DKS Cluster 노드의 hostname 및 IP Address 확인
- [ ] ETCD 노드의 파일시스템 용도(`/var/lib/etcd`) 확인
- [ ] DS Cloud Service Desk에 Load Balancer alert exception 사전 요청
- [ ] VIP-A/B가 Master Node 및 Router Node로 routing하는지 HTTP 응답 확인
- [ ] Bastion DATA Disk 파티션 및 LVM 설정 완료
- [ ] Bastion `dspaas` 사용자의 `wheel` 그룹 소속 확인


## 다음 단계

Step 0의 VM, VIP, Bastion 디스크 및 사용자 확인이 끝나면 [[30. 구축 및 전환/공통 구축/01. Bastion Node Pre-setting|Step 1 Bastion Node Pre-setting]]을 수행한다. Step 1~5의 작업 내용과 완료 판단은 각 상세 문서 및 [[30. 구축 및 전환/Host 및 Member 구축 분기]]가 소유한다.
