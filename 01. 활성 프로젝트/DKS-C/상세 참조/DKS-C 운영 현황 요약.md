# DKS-C 운영 현황 요약

> [!warning] 민감정보 포함
> 이 문서에는 내부 서비스 URL, 계정 및 비밀번호 등 운영 민감정보가 포함되어 있음.

## 개요

DS Cloud Kubernetes Service(DKS-C)의 인프라 아키텍처와 운영 정보를 정리한 문서.

---

## 시스템 아키텍처

### VCF Overview

- **운영 WLD01**: `kh-prd-ia-wld01` — 기흥화성 / 운영 / 3 Zone
- **운영 WLD02**: `kh-prd-ia-wld02` — 기흥화성 / 운영·개발 / 2 Zone
- Organization
  - 운영 WLD: `dks-org`
  - 개발 WLD: `dks-dev-org`
- 개발계: 5월 말 구축 예정

### 사용자 클러스터

- DKS-C 포털(콘솔)로 관리
- 외부 접근은 `dksg-ic01-khm` APISIX를 통해 통제
- 외부 직접 접근 불가
- 기본 External-IP 3개
  - kube-apiserver
  - Application Ingress
  - SNAT

### Network

- 관리 클러스터 전체: `dkssol-project` 단일 Transit G/W 공유
- 관리 클러스터: `prod-dks-vpc` 사용
- 사용자 클러스터: VPC와 1:1 관계
- VPC별 SNAT External IP 부여

### Storage

| PV | 용도 | 비고 |
|---|---|---|
| `vks-pf-storage-policy-admin` | Supervisor VM OS, Platform 클러스터 PV | |
| `vks-pf-storage-policy` | 사용자 클러스터 VM OS PV | |
| `vks-pf-storage-policy-data` | 사용자 제공 PV | |

- **개발계 Storage**: 5월 말 구축 예정

### 클러스터 프로비저닝

- VCF Cluster-API + ArgoCD 기반
- ArgoCD 2개 인스턴스
  - Platform 관리
  - 클러스터 프로비저닝
- VCF 개발계
  - Platform + Harbor는 DKS-N
  - 클러스터 프로비저닝 ArgoCD 1개

---

## Platform 클러스터

### 운영 WLD01 — `kh-prd-ai-wld01` (기흥화성/운영)

| Name | 용도 | CP | WK | VIP (6443) | VIP (80,443) | SNAT |
|---|---|---|---|---|---|---|
| `prd-dksc-ic01-khm` | 사용자 콘솔 | 3×4C/8G | 5×16C/32G | 12.201.18.9 | 12.201.18.15 | 12.201.18.6 |
| `prd-dksg-ic01-khm` | API 게이트웨이 | 3×4C/8G | 5×16C/32G | 12.201.18.10 | 12.201.18.7 | 12.201.18.14 |
| `prd-dksm-ic01-khm` | 모니터링 | 3×4C/8G | 5×16C/32G | 12.201.18.12 | 12.201.18.18 | — |
| `prd-dksl-ic01-khm` | 로깅 | 3×4C/8G | 5×16C/64G | 12.201.18.11 | 12.201.18.16 | — |
| `prd-dkso-ic01-khm` | DevOps | 3×4C/8G | 10×8C/16G | 12.201.18.13 | 12.201.18.17 | — |

- LB Services: `12.201.18.(19,20,23)`, `12.201.18.(34,36,35)`

### 운영 WLD02 — `kh-prd-ai-wld02` (기흥화성/운영/개발)

| Name | 용도 | CP | WK | VIP (6443) | VIP (80,443) | SNAT |
|---|---|---|---|---|---|---|
| `dev-dksc-ic01-khm` | 사용자 콘솔 | 3×4C/8G | 3×8C/16G | 12.201.35.10 | 12.201.35.20 | 12.201.35.3 |
| `dev-dksg-ic01-khm` | API 게이트웨이 | 3×4C/8G | 3×8C/16G | 12.201.35.8 | 12.201.35.21 | 12.201.35.27 |
| `dev-dksl-ic01-khm` | 로깅 | 3×4C/8G | 3×8C/16G | 12.201.35.14 | 12.201.35.23 | — |
| `dev-dksm-ic01-khm` | 모니터링 | 3×4C/8G | 3×8C/16G | 12.201.35.13 | 12.201.35.22 | — |
| `dev-dkso-ic01-khm` | DevOps | 3×4C/8G | 3×8C/16G | 12.201.35.12 | 12.201.35.24 | — |

### Block Storage policy (운영 WLD01)

| PV | DataStore | 용도 | 용량 | 비고 |
|---|---|---|---|---|
| `vks-pf-storage-policy-admin` | DS001 | Supervisor VM + Platform 클러스터 | 50 TB | |
| `vks-pf-storage-policy` | DS002 | 사용자 클러스터 VM OS | 60 TB | kyverno block |
| `vks-pf-storage-policy-data` | DS003 | 사용자 제공 | 15 TB | |
| (추가 예정) | DS003 | 사용자 제공 | 60 TB | |

### NetApp Storage

| Endpoint | 용도 | Endpoint IP | 용량 | Backend |
|---|---|---|---|---|
| `vks-1az-a-prd` | 사용자 제공 (운영) | 10.172.149.11 | 60 TB | 10.172.201.51-54 |
| `vks-1az-a-dev` | 사용자 제공 (개발) | 10.172.149.11 | 60 TB | 10.172.201.55-58 |
| `vks-1az-a-stg` | 사용자 제공 (스테이징) | 10.172.149.11 | 60 TB | 10.172.201.59-62 |

---

## 관리자 계정

### VCF 운영계

#### 운영 WLD01 — `kh-prd-ai-wld01` (기흥화성/운영/운영WLD)

| Product | URL | User | Password |
|---|---|---|---|
| VCFA | https://kh-prd-vcf-vcfa.samsungds.net/ | `dks-org / dks-org-admin` | `Dks123!Dks123!!` |
| vCenter | https://kh-prd-ia-wld01-vct.samsungds.net/ | `dks-sup-admin@vsphere.local` | `Dks123!Dks123!!` |
| AVI | https://kh-prd-ia-wld01-avi.samsungds.net/ | `dks-org-admin` | `Dks123!Dks123!!` |
| NSX | https://kh-prd-ia-wld01-nsx.samsungds.net | `dks-org-admin` | `Dks123!Dks123!!` |

#### 운영 WLD02 — `kh-prd-ai-wld02` (기흥화성/운영/개발WLD)

| Product | URL | User | Password |
|---|---|---|---|
| VCFA | https://kh-prd-vcf-vcfa.samsungds.net/ | `dks-dev-org / dks-dev-admin` | `Dks123!Dks123!!` |
| vCenter | http://kh-dev-ia-wld02-vct.samsungds.net/ | `dks-sup-admin@vsphere.local` | `Dks123!Dks123!!` |
| AVI | http://kh-dev-ia-wld02-avi.samsungds.net | `dks-org-admin` | `Dks123!Dks123!!` |
| NSX | http://kh-dev-ia-wld02-nsx.samsungds.net/ | `dks-org-admin` | `Dks123!Dks123!!` |

#### VCF 9.1 검증계 — `kh-dev-wda` (기흥화성/개발)

| Product | URL | User | Password |
|---|---|---|---|
| VCFA | https://kh-dev-mgd-vra.samsungds.net/ | `KH-DEV-WDA-VKS / dks-org-admin` | `Dks123!Dks123!!` |
| vCenter | https://kh-dev-wda-vc01.samsungds.net/ | `dks-sup-admin@vsphere.local` | `Dks123!Dks123!!` |
| AVI | https://10.169.61.81 | `dks-org-admin` | `Dks123!Dks123!!` |
| NSX | https://10.169.61.140 | `dks-org-admin` | `Dks123!Dks123!!` |

> 운영 WLD01/WLD02는 동일한 VCFA URL을 사용하고 계정만 다름.

### DKS Platform

#### 운영 WLD01

| Name | URL | User | Password | 비고 |
|---|---|---|---|---|
| 사용자 콘솔 | https://console.dks.samsungds.net/ | — | — | OIDC 연동 |
| KeyCloak | https://keycloak.dks.samsungds.net/ | `dkskeycloakadmin` | `Dks123tka!tjd` | OIDC 연동 |
| 운영자 모니터링 (Grafana) | https://grafana.dks.samsungds.net/ | `superuser` | `Dks123!Dks123!!` | OIDC 연동 가능 |
| 모니터링 (Grafana) | https://grafana-dksm.dks.samsungds.net | `superuser` | `Dks123!Dks123!!` | 동일 서비스 |
| 운영자 로깅 (OpenSearch) | https://opensearch-dashboard.dks.samsungds.net/ | `dashboard-admin` | `Dks123!Dks123!!` | OIDC 연동 가능 |
| Run Book | https://runbooks.dks.samsungds.net/ | — | — | 콘솔 알림 링크 |
| VM UI | https://vmui-dksm.dks.samsungds.net/select/0/vmui/ | `admin` | `Dks123!Dks123!!` | VictoriaMetrics Query Browser |
| VM Alert | http://vmalert-dksm.dks.samsungds.net/vmalert | `admin` | `Dks123!Dks123!!` | VictoriaMetrics Alert |
| Alert Manager | http://alert-dksm.dks.samsungds.net/ | `admin` | `Dks123!Dks123!!` | VictoriaMetrics Alert Manager |
| Argo CD (admin) | https://argocd-admin.dks.samsungds.net | — | — | Admin 플랫폼, 클러스터, 애드온 |
| Argo CD (user) | https://argocd-user.dks.samsungds.net | — | — | 사용자 클러스터, 애드온 |

#### 운영 WLD02

| Name | URL | User | Password | 비고 |
|---|---|---|---|---|
| 사용자 콘솔 | https://console-dev.dks.samsungds.net/ | `dksconsole` | `1q2w3e4r!!` | OIDC 연동 |
| KeyCloak | https://keycloak-dev.dks.samsungds.net/ | `dkskeycloakadmindev` | `tka!tjdDks123` | OIDC 연동 |
| 운영자 모니터링 (Grafana) | https://grafana-dev.dks.samsungds.net/ | `superuser` | `Dks123!Dks123!!` | OIDC 연동 가능 |
| 운영자 로깅 (OpenSearch) | https://opensearch-dashboard-dev.dks.samsungds.net/ | `dashboard-admin` | `Dks123!Dks123!!` | OIDC 연동 가능 |
| Run Book | https://runbooks-dev.dks.samsungds.net/ | — | — | 콘솔 알림 링크 |
| VM UI | http://vmui-dev-dksm.dks.samsungds.net/select/0/vmui | `admin` | `Dks123!Dks123!!` | VictoriaMetrics Query Browser |
| VM Alert | http://vmalert-dev-dksm.dks.samsungds.net/vmalert | `admin` | `Dks123!Dks123!!` | VictoriaMetrics Alert |
| Alert Manager | http://alert-dev-dksm.dks.samsungds.net | `admin` | `Dks123!Dks123!!` | VictoriaMetrics Alert Manager |
| Argo CD (admin) | https://argocd-admin-dev.dks.samsungds.net | — | — | Admin 플랫폼, 클러스터, 애드온 |
| Argo CD (user) | https://argocd-user-dev.dks.samsungds.net | — | — | 사용자 클러스터, 애드온 |

### Image Registry

| 인프라 | Name | URL | User | Password | 비고 |
|---|---|---|---|---|---|
| 운영 WLD01 | 관리 패키지 | https://packages.dks.samsungds.net/ | `admin` | `Dks123!Dks123!!` | |
| 운영 WLD01 | 사용자용 Harbor | https://harbor.dks.samsungds.net/ | `admin` | `Dks123!Dks123!!` | DevOps 및 사용자 제공 |
| 운영 WLD01 | Supervisor | http://kh-prd-ia-mgd-harbor.samsungds.net/ | `admin` | `.dU:17@SK=zJ` | Supervisor Management Only |
| 운영 WLD02 | 관리 패키지 | https://packages-dev.dks.samsungds.net/ | `admin` | `Dks123!Dks123!!` | |
| 운영 WLD02 | 사용자용 Harbor | https://harbor-dev.dks.samsungds.net/ | `admin` | `Dks123!Dks123!!` | DevOps 및 사용자 제공 |
| 운영 WLD02 | Supervisor | http://kh-prd-ia-mgd-harbor.samsungds.net/ | `admin` | `.dU:17@SK=zJ` | Supervisor Management Only (공통) |

### Bastion

| 인프라 | SSH | Password | 비고 |
|---|---|---|---|
| `kh-prd-ai-wld01` (운영 WLD01) | `dks-user@12.201.42.47` | `Dks123!Dks123!!` | |
| `kh-prd-ai-wld02` (운영 WLD02) | `dks-user@12.201.42.48` | `Dks123!Dks123!!` | |
| `kh-dev-wda` (VCF 9.1 검증계) | `dks-user@10.169.61.25` | `Dks123!Dks123!!` | |

---

## 확인 필요 사항

- 상단 VCF Overview에서는 WLD 명칭이 `kh-prd-ia-wld01`, `kh-prd-ia-wld02`로 기재되어 있으나 Platform 클러스터 및 Bastion 영역에서는 `kh-prd-ai-wld01`, `kh-prd-ai-wld02`로 기재되어 있음. 실제 공식 명칭 확인 필요.
- 개발계 및 개발계 Storage의 "5월 말 구축 예정"은 기준 연도가 명시되어 있지 않으므로 추후 일정 기준일 확인 필요.
