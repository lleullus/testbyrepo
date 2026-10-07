# DKS 일일 모니터링 보고서 (New Daily Report)

## 금주 작업 현황 (PRD)

| 09/14 (월) | 09/15 (화) | 09/16 (수) | 09/17 (목) | 09/18 (금) |
|---|---|---|---|---|
| - | - | [작업][DKS-N] 2026/09/16 클러스터 Velero 설치 작업<br>오정석 / Cloud Solution그룹(AI센터) | [작업][DKS-N] 2026/09/17 prd-dkso-pa01-khm 클러스터 new-opensearch hot data PVC 용량 증설 작업<br>오정석 / Cloud Solution그룹(AI센터) | - |

---

## 주요 보고사항

### DKS-N
1. **Opensearch 특이사항 보고**
   - `opensearch-cluster-hot-data-opensearch-cluster-hot-data-0` PVC Max Used 82.1% / 09.17 증설 예정
   - `opensearch-cluster-hot-data-opensearch-cluster-hot-data-1` PVC Max Used 82.1% / 09.17 증설 예정
2. **System Pod Restart Count**
   - `prd-ctzs-pb01-khs` 클러스터 / `calico-kube-controller` 3개 HA 파드 중 1개 재시작 / 원인: OOM Killed로 인한 Container restart / 서비스 영향: 3중화 HA 구성된 component로 서비스 영향 없음
   - `prd-ctzs-pb01-khs` 클러스터 / `trident-node-linux-gn8ns` 파드 1개 재시작 / 원인: Go map 동시 접근 (concurrent map writes) 오류로 인한 Container restart / 서비스 영향: 해당 컨테이너 재시작 후 정상 동작 확인, 서비스 영향 없음
3. **PVC Usage**
   - `prd-ctzs-pb01-khs` 클러스터 / `prometheus-k8s-db-prometheus-k8s-1` PVC Max Used 82.2% / 모니터링 중
4. **'dspaas' Password 만료일**
   - DKS-N / 전체 클러스터 / 'dspaas' Password 만료일 14일, 'dspaas' Password 변경 필요

### DKS-C
1. `kh-prd-ia-wld01-region01` / `vks-pf-storage-policy` Provisioned 87% / 실사용량: 22.75 / 60 TB (37%)

---

## 1. Console, Opensearch, Thanos, VictoriaMetrics Component Check New Daily Report - 상세 항목 설명

### ※ Console, Opensearch, Thanos 특이사항 보고
| 항목 | 구분 | 내용 | 비고 |
|---|---|---|---|
| PVC Usage | `prd-dkso-pa01-khm` | `opensearch-cluster-hot-data-opensearch-cluster-hot-data-0` PVC Used 82.1%<br>`opensearch-cluster-hot-data-opensearch-cluster-hot-data-1` PVC Used 82.1% | 09.17 증설 예정 |
| PVC Usage | `prd-dksc-pa01-khm` | `airflow/logs-airflow-worker-0` pvc metric 값 확인 불가<br>`airflow/logs-airflow-worker-1` pvc metric 값 확인 불가 | airflow 사용 중지 상태 |

### ※ Pod Restart Count & Pod Status & PVC Usage & Balancing & Compactor Status Check
| System | Cluster | Pod Restart Count | Pod Status | PVC Usage | Balancing | Compactor Status |
|---|---|---|---|---|---|---|
| DKS-C | `prd-dksc-ic01-khm` | 0 | Good | Good | - | - |
| DKS-C | `prd-dksl-ic01-khm` | 0 | Good | Good | Good | - |
| DKS-C | `prd-dksm-ic01-khm` | 0 | Good | Good | Good | - |
| DKS-N | `prd-dksc-pa01-khm` | 0 | Good | Good | - | - |
| DKS-N | `prd-dkso-pa01-khm` | 0 | Good | Check | Good | - |
| DKS-N | `prd-dkst-pa01-khm` | 0 | Good | Good | Good | Good |

---

## 2. Cluster Check New Daily Report - 상세 항목 설명

### ※ Cluster Check 특이사항 보고
| 환경 | 항목 | 대상 클러스터 | 내용 | 비고 |
|---|---|---|---|---|
| DKS-N | System Pod Restart Count | `prd-ctzs-pb01-khs` | OOM Killed 로 인한 calico-kube-controller 3개 HA 파드 중 1개 Container restart | 3중화 HA 구성된 component로 서비스 영향 없음 |
| DKS-N | System Pod Restart Count | `prd-ctzs-pb01-khs` | Go map 동시 접근 (concurrent map writes) 오류로 인한 trident-node-linux-gn8ns 파드 Container restart | 해당 컨테이너 재시작 후 정상 동작 확인, 서비스 영향 없음 |
| DKS-N | PVC Usage | `prd-ctzs-pb01-khs` | prometheus-k8s-db-prometheus-k8s-1 PVC Max Used 82.1% | 모니터링 중 |
| DKS-N | 'dspaas' Password | 전체 클러스터 | 'dspaas' Password 만료일 14일 | 관련 이슈 확인 및 조치 사항은 별도 보고 예정 |

### ※ Cluster Check
| No | Cluster | 총 노드수 | 가용 Node 수 | Node 가용률 (%) | System Pod Restart Count | Cluster Status | Core Namespace Balancing (CPU) | Core Namespace Balancing (MEM) | API | ETCD | PVC Usage | Core Node Usage (API) | Core Node Usage (ETCD) | Certificate Expiry | 'dspaas' Password |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `prd-dksc-ic01-khm` | 8 | 8 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Good |
| 2 | `prd-dksg-ic01-khm` | 8 | 8 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Good |
| 3 | `prd-dksl-ic01-khm` | 8 | 8 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Good |
| 4 | `prd-dksm-ic01-khm` | 8 | 8 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Good |
| 5 | `prd-dkso-ic01-khm` | 13 | 13 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Good |
| 6 | `prod-ds-buildfarm-vm` | 189 | 189 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 7 | `prod-ds-dbaas` | 29 | 29 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 8 | `prod-ds-member` | 48 | 48 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 9 | `prod-ds-member-dev` | 31 | 31 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 10 | `prod-ds-citizen` | 42 | 42 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 11 | `prd-dksc-pa01-khm` | 16 | 16 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 12 | `prd-dkso-pa01-khm` | 15 | 15 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 13 | `prd-dkst-pa01-khm` | 15 | 15 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 14 | `prd-apps-pa01-cad` | 17 | 17 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 15 | `prd-ctzn-pa01-cad` | 21 | 21 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 16 | `prd-apps-pb01-khm (v1.26)` | 77 | 77 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 17 | `dev-apps-pb01-khs (v1.26)` | 43 | 43 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 18 | `prd-ctzj-pb01-khs` | 42 | 42 | 100% | 0 | Good | Good | Good | Good | Good | Good | Good | Good | Good | Check |
| 19 | `prd-ctzs-pb01-khs` | 57 | 57 | 100% | 0 | Good | Good | Good | Good | Good | Check | Good | Good | Good | Check |

---

## 3. DKS 동보 현황

### ※ DKS-N 동보 상태
**전일 동보 현황 (18:00 ~ 08:00)**
| Total | Sensor C | Sensor D | Sensor I | Sensor 참조 대시보드 |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | - |

**동보 Sensor 현황**
- 동보 상세 (C등급 이상)

| Cluster | 등급 | 동보 상세 내용 | 확인 사항 | 중복 동보건 제외 |
|---|---|---|---|---|
| - | - | - | - | - |

- 관련 이슈 확인 및 조치 사항: N/A

### ※ DKS-N/C 잔존 알림 확인
| 구분 | ClusterName | 잔존 알림 여부 | 알림 내용 | 비고 |
|---|---|---|---|---|
| DKS-N | - | 없음 | - | - |
| DKS-C | `gsre-servicemap-dev` | 있음 | Guest Cluster CPU Request 점유율 80% 이상 | - |

---

## 4. DKS-C Region/Zone Quota New Daily Report - 상세 항목 설명

### ※ Platform Region/Zone Quota 특이사항 보고
| REGION | Zone / StorageClass | Resource | 특이사항 |
|---|---|---|---|
| kh-prd-ia-wld01-region01 | - | - | - |

### ※ Region Resource Summary
| REGION | Namespaces | CPU | Memory | Storage |
|---|---|---|---|
| kh-prd-ia-wld01-region01 | 51 | 11,202 / 14,515.2 GHz | 34.05 / 52.11 TB | 79.32 / 125 TB |

### ※ Zone / StorageClass Resource Usage(%)
| REGION | Resource | ZONE / STORAGECLASS / IPBLOCK | Provisioned (%) | Used (%) |
|---|---|---|---|---|
| kh-prd-ia-wld01-region01 | CPU | `kh-prd-ia-wld01-az01` | 77% | - |
| kh-prd-ia-wld01-region01 | CPU | `kh-prd-ia-wld01-az02` | 77% | - |
| kh-prd-ia-wld01-region01 | CPU | `kh-prd-ia-wld01-az03` | 77% | - |
| kh-prd-ia-wld01-region01 | Memory | `kh-prd-ia-wld01-az01` | 65% | - |
| kh-prd-ia-wld01-region01 | Memory | `kh-prd-ia-wld01-az02` | 65% | - |
| kh-prd-ia-wld01-region01 | Memory | `kh-prd-ia-wld01-az03` | 65% | - |
| kh-prd-ia-wld01-region01 | Storage | `vks-pf-storage-policy` | 88% | 23.46 / 60 TB |
| kh-prd-ia-wld01-region01 | Storage | `vks-pf-storage-policy-admin` | 37% | 13.26 / 50 TB |
| kh-prd-ia-wld01-region01 | Storage | `vks-pf-storage-policy-data` | 54% | 0.55 / 15 TB |
| kh-prd-ia-wld01-region01 | External-IP | `external-ipblock-12-201-18-x-dhnlf` | 64% | - |

---

## 5. DKS-C Platform 자원 현황 New Daily Report - 상세 항목 설명

### ※ DKS-C Platform 자원 현황 특이사항 보고
| 항목 | 내용 | 비고 |
|---|---|---|
| VictoriaMetrics Storage | N/A | - |
| Opensearch Storage | N/A | - |
| Object Storage | N/A | - |
| harbor | N/A | - |
* 관련 이슈 확인 및 조치 사항은 별도 보고 예정

### ※ VictoriaMetrics Storage 사용 현황
- VictoriaMetrics Storage

### ※ OpenSearch Storage 사용 현황
- OpenSearch Storage

### ※ Object Storage 사용 현황
- Object Storage

### ※ harbor 사용 현황
| 항목 | 값 |
|---|---|
| 프로젝트 | 39개 |
| 사용된 할당량 | 197.89 GiB |

### ※ argocd-vks-instance Memory 모니터링 클러스터
| 클러스터 컴포넌트 | 전일 | 현재 | 비고 |
|---|---|---|---|
| `argocd-application-controller-0` | 1.36GB | 1.02GB | - |
| `argocd-application-controller-1` | 0.78GB | 0.78GB | - |
| `vks-argocd-application-controller-0` | 6.5GB | 8.29GB | - |
| `vks-argocd-application-controller-1` | 4.39GB | 4.06GB | - |

---

## 6. DKS-C 사용자 Cluster 현황 New Daily Report - 상세 항목 설명

- **전일 사용자 Cluster 수**: 38 / **금일 사용자 Cluster 수**: 39 / **증감**: +1 (생성 1, 삭제 0)

| ClusterName | 생성 / 삭제 |
|---|---|
| `claude-cowork` | 생성 |

### ※ 사용자 Cluster Worker Node 자원 사용량 현황
| Cluster | Node (전일 / 현재) | CPU 보유량(Core) / 하루 최대 사용률 (전일 / 현재) | Mem 보유량(GiB) / 하루 최대 사용률 (전일 / 현재) | Block Storage 보유량(GiB) / 하루 최대 사용률 (전일 / 현재) | NAS 보유량(GiB) / 하루 최대 사용률 (전일 / 현재) | 비고 |
|---|---|---|---|---|---|---|
| `amhs-sim-analysis-pr` | 6개 / 3개 | 24 / 1.0% / 24 / 1.2% | 96 / 3.6% / 96 / 3.7% | 0 / 0.0% / 0 / 0.0% | 0 / 0.0% / 0 / 0.0% | - |
| `appdevops` | 3개 / 3개 | 96 / 0.9% / 96 / 0.9% | 384 / 3.8% / 384 / 3.8% | 29 / 42.2% / 29 / 41.3% | 321 / 2.8% / 321 / 2.8% | - |
| `artds2dprov` | 6개 / 6개 | 96 / 0.9% / 96 / 0.9% | 384 / 4.9% / 384 / 5.1% | 0 / 0.0% / 0 / 0.0% | 490 / 0.9% / 490 / 0.6% | - |
| `bia-dev` | 4개 / 4개 | 32 / 15.4% / 32 / 23.0% | 128 / 25.7% / 128 / 30.3% | 381 / 4.6% / 381 / 4.7% | 332 / 2.7% / 352 / 3.5% | - |
| `bia-prd` | 6개 / 6개 | 48 / 3.0% / 48 / 15.1% | 192 / 14.6% / 192 / 16.8% | 402 / 2.1% / 402 / 2.1% | 274 / 0.8% / 274 / 0.8% | - |
| `bia-stg` | 4개 / 4개 | 32 / 4.1% / 32 / 8.0% | 128 / 14.7% / 128 / 16.8% | 402 / 1.9% / 402 / 1.9% | 264 / 1.0% / 264 / 1.1% | - |
| `cae-pcloud-prod` | 3개 / 3개 | 12 / 2.5% / 12 / 2.5% | 24 / 17.7% / 24 / 17.8% | 0 / 0.0% / 0 / 0.0% | 0 / 0.0% / 0 / 0.0% | - |
| `canvas` | 3개 / 3개 | 24 / 1.3% / 24 / 1.4% | 192 / 3.1% / 192 / 3.1% | 0 / 0.0% / 0 / 0.0% | 15 / 64.2% / 15 / 64.2% | - |
| `cdep0` | 4개 / 3개 | 48 / 0.7% / 48 / 0.7% | 384 / 1.4% / 384 / 1.4% | 0 / 0.0% / 0 / 0.0% | 223 / 1.8% / 223 / 1.8% | - |
| `claude-cowork` | - / 3개 | - / 48 / 0.6% | - / 96 / 3.6% | - / 0 / 0.0% | - / 0 / 0.0% | 신규 생성 |
| `dbrgdev01` | 3개 / 3개 | 24 / 1.6% / 24 / 1.6% | 96 / 6.5% / 96 / 6.5% | 365 / 7.7% / 365 / 8.0% | 0 / 0.0% / 0 / 0.0% | - |
| `diff-application-01` | 4개 / 4개 | 16 / 3.9% / 16 / 4.2% | 32 / 23.1% / 32 / 23.0% | 0 / 0.0% / 0 / 0.0% | 25 / 40.0% / 25 / 40.0% | - |
| `dks-c-aisw-art-ace` | 4개 / 4개 | 16 / 3.6% / 16 / 5.7% | 32 / 29.8% / 32 / 32.4% | 0 / 0.0% / 0 / 0.0% | 30 / 9.3% / 35 / 8.4% | - |
| `dks-magician-ax` | 3개 / 3개 | 24 / 4.1% / 24 / 4.1% | 48 / 12.4% / 48 / 13.2% | 422 / 4.1% / 422 / 4.7% | 5 / 0.0% / 5 / 0.0% | - |
| `dsportal-dev` | 12개 / 12개 | 72 / 2.1% / 72 / 8.7% | 192 / 15.0% / 192 / 17.8% | 0 / 0.0% / 0 / 0.0% | 191 / 6.6% / 191 / 7.0% | - |
| `dsportal-prd` | 15개 / 15개 | 96 / 2.9% / 96 / 7.3% | 336 / 11.3% / 336 / 13.4% | 0 / 0.0% / 0 / 0.0% | 360 / 4.8% / 360 / 5.3% | - |
| `dsportal-stg` | 15개 / 15개 | 96 / 1.5% / 96 / 5.3% | 288 / 10.4% / 288 / 11.9% | 0 / 0.0% / 0 / 0.0% | 193 / 2.7% / 193 / 3.0% | - |
| `ears-tsp` | 4개 / 4개 | 32 / 1.2% / 32 / 1.3% | 64 / 19.8% / 64 / 19.8% | 90 / 0.1% / 90 / 0.2% | 0 / 0.0% / 0 / 0.0% | - |
| `espec-devops` | 3개 / 3개 | 24 / 1.0% / 24 / 1.0% | 48 / 7.3% / 48 / 7.3% | 10 / 0.0% / 10 / 0.0% | 10 / 0.0% / 10 / 0.0% | - |
| `fmcs-datapipeline` | 3개 / 3개 | 12 / 2.8% / 12 / 2.8% | 48 / 12.5% / 48 / 12.5% | 0 / 0.0% / 0 / 0.0% | 600 / 0.1% / 600 / 0.1% | - |
| `gsre-servicemap-dev` | 4개 / 4개 | 16 / 7.5% / 16 / 12.4% | 64 / 18.3% / 64 / 20.6% | 5 / 0.7% / 5 / 1.2% | 43 / 24.1% / 35 / 29.9% | - |
| `gsre-servicemap-prd` | 3개 / 3개 | 96 / 0.4% / 96 / 0.4% | 192 / 2.6% / 192 / 2.6% | 0 / 0.0% / 0 / 0.0% | 0 / 0.0% / 0 / 0.0% | - |
| `incluster-0722-dev` | 4개 / 4개 | 32 / 1.0% / 32 / 1.0% | 64 / 7.0% / 64 / 7.1% | 2 / 1.1% / 2 / 1.2% | 0 / 0.0% / 0 / 0.0% | - |
| `oafbrx` | 12개 / 12개 | 304 / 1.0% / 304 / 1.0% | 1.19 TiB / 9.6% / 1.19 TiB / 9.7% | 0 / 0.0% / 0 / 0.0% | 784 / 1.2% / 784 / 1.2% | - |
| `pems` | 3개 / 3개 | 24 / 1.9% / 24 / 10.8% | 48 / 26.8% / 48 / 31.1% | 0 / 0.0% / 0 / 0.0% | 0 / 10.0% / 0 / 10.0% | - |
| `peoplein360-dev` | 15개 / 15개 | 60 / 2.8% / 60 / 9.9% | 168 / 23.2% / 168 / 27.5% | 16 / 0.0% / 16 / 0.0% | 283 / 8.3% / 283 / 8.3% | - |
| `peoplein360-prd` | 21개 / 21개 | 132 / 1.3% / 132 / 1.3% | 528 / 5.4% / 528 / 5.3% | 12 / 0.0% / 12 / 0.0% | 143 / 6.2% / 143 / 6.2% | - |
| `peoplein360-stg` | 15개 / 15개 | 60 / 1.8% / 60 / 2.0% | 168 / 13.5% / 168 / 13.6% | 12 / 0.0% / 12 / 0.0% | 88 / 12.5% / 88 / 12.6% | - |
| `ra-server-monitoring` | 8개 / 5개 | 20 / 1.7% / 20 / 1.8% | 40 / 10.8% / 40 / 10.8% | 8 / 0.0% / 8 / 0.0% | 2 / 0.1% / 2 / 0.1% | - |
| `rsip-cluster` | 9개 / 6개 | 96 / 0.6% / 96 / 0.6% | 192 / 3.9% / 192 / 3.9% | 0 / 0.0% / 0 / 0.0% | 11 / 25.0% / 11 / 33.5% | - |
| `sense-cluster` | 3개 / 3개 | 24 / 1.1% / 24 / 1.2% | 48 / 10.4% / 48 / 10.5% | 0 / 0.0% / 0 / 0.0% | 59 / 0.0% / 59 / 0.0% | - |
| `smap-dev-cluster` | 5개 / 5개 | 160 / 0.9% / 160 / 1.5% | 640 / 5.7% / 640 / 5.7% | 410 / 8.5% / 410 / 8.6% | 334 / 3.9% / 334 / 3.8% | - |
| `smap-mgmt-cluster` | 3개 / 3개 | 48 / 1.0% / 48 / 1.2% | 192 / 4.5% / 192 / 4.6% | 0 / 0.0% / 0 / 0.0% | 32 / 25.2% / 32 / 25.1% | - |
| `smap-prod-cluster` | 5개 / 5개 | 160 / 0.6% / 160 / 1.9% | 640 / 3.9% / 640 / 3.9% | 360 / 3.8% / 360 / 3.9% | 303 / 5.7% / 303 / 5.1% | - |
| `smap-stg-cluster` | 3개 / 3개 | 48 / 1.4% / 48 / 1.6% | 192 / 7.4% / 192 / 7.3% | 315 / 11.6% / 315 / 11.7% | 264 / 2.9% / 264 / 2.5% | - |
| `ssafe-platform` | 6개 / 3개 | 24 / 1.0% / 24 / 1.1% | 96 / 3.8% / 96 / 3.8% | 0 / 0.0% / 0 / 0.0% | 0 / 0.0% / 0 / 0.0% | - |
| `util-analysis` | 3개 / 3개 | 12 / 2.3% / 12 / 2.2% | 24 / 15.7% / 24 / 15.7% | 0 / 0.0% / 0 / 0.0% | 0 / 0.0% / 0 / 0.0% | - |
| `ymsdb-dksc` | 3개 / 3개 | 96 / 0.4% / 96 / 0.4% | 192 / 3.0% / 192 / 3.0% | 0 / 0.0% / 0 / 0.0% | 1 / 0.0% / 1 / 0.0% | - |
| `ymsui-cluster` | 3개 / 3개 | 48 / 0.7% / 48 / 0.8% | 96 / 4.4% / 96 / 4.6% | 10 / 12.2% / 10 / 18.5% | 0 / 0.0% / 0 / 0.0% | - |

---

## 7. DKS-C Platform VCFA Supervisor 컴포넌트 상태 모니터링 New Daily Report - 상세 항목 설명

### ※ Supervisor HEALTH FAIL 컴포넌트 특이사항 보고
| Service Name | Health | Component Group | Cluster | 특이사항 |
|---|---|---|---|---|
| - | - | - | - | - |
* 관련 이슈 확인 및 조치 사항: N/A

### ※ 인증서 만료일 확인
| 항목 | 만료일 | 비고 |
|---|---|---|
| `cns-storage-quota-extension-cert` | 2026-10-24 16:10:25 | |
| `storage-quota-serving-cert` | 2026-10-24 16:10:22 | |
| `storage-quota-webhook-internal-serving-cert` | 2026-10-24 16:10:24 | |
| `storage-quota-selfsigned-issuer-cert` | 2026-10-24 16:10:22 | |
| `runtime-extension-serving-cert` | 2026-10-24 16:35:40 | |
| `console-token` | 2026-09-21 10:31:04 | 만료 약 2주일 전 (remaining < 15) 경우 해당 만료일에 인증서 업데이트에 따른 후속조치 수행할 수 있도록 담당자에게 전파 |

---

## 8. DKS-C Backup 프로세스 모니터링 New Daily Report - 상세 항목 설명

| 구분 | Status | 비고 |
|---|---|---|
| `logs-hub` | 정상 | 스냅샷 생성 시간 (1일 1회) 09/15/26 10:59 am |
| `metric-hub` | 정상 | 1일 내 Cron Job Fail Count 0 |
| `Console-db` | 정상 | 1일 내 Fail Process 0건 (시간당 1회) |
| `Keycloak-db` | 정상 | 1일 내 Fail Process 0건 (시간당 1회) |
| `Apisix-etcd` | 정상 | 1일 내 스냅샷 카운트 24건 (시간당 1건) |

---

## 9. DKS-N Platform 자원 현황 New Daily Report - 상세 항목 설명

- **제외 클러스터**: 6개 (argocd 1개, staging 3개, host 2개)
- **제외 노드**: bastion node
- *`dev-ppoc-pc01-khs` 신규 클러스터 포함*

### ※ DKS-N Platform 자원 현황 특이사항 보고
| 스토리지 구분 | 항목 | 내용 | 비고 |
|---|---|---|---|
| Powerflex | SP04 | Provisioned 93% | Max Used 80% 미만 |
| NAS (NetApp) | `dks-common` | Provisioned 400%, Max Used 76.1% | Max Used 80% 미만 |
| NAS (NetApp) | `dks` | Provisioned 96% | Max Used 80% 미만 |
* 관련 이슈 확인 및 조치 사항은 별도 보고 예정

### ※ Harbor 사용 현황
| Harbor 항목 | 값 |
|---|---|
| 스토리지 사용량 | 1571 GB / 2000 GB (78.5%) |
| 프로젝트 수 | 595 |

### ※ DKS-N Storage 전체 리소스
- Kubernetes Resource
- ALL Node Resource

### ※ DKS-N Storage 사용 현황
- Block Storage (Powerflex)
- NAS (NetApp)
- Object Storage (Prod)

---

## 10. DKS-N Cluster 자원 사용 현황 New Daily Report - 상세 항목 설명

- **제외 클러스터**: 6개 (argocd 1개, staging 3개, host 2개)
- **제외 노드**: bastion node
- *`dev-ppoc-pc01-khs` 신규 클러스터 포함*

### ※ Cluster Storage Summary - SP04 / SP205 / NetApp
| 대상 클러스터 | 스토리지 구분 | 항목 | 내용 | 비고 |
|---|---|---|---|---|
| `prod-ds-buildfarm-vm` | Powerflex | SP04 | Max Provisioned 97% | Max Used 80% 미만 |
| `prod-ds-member` | Powerflex | SP04 | Max Provisioned 81% | Max Used 80% 미만 |
| `prod-ds-buildfarm-vm` | NetApp | `dks-common` | Max Provisioned 95% | Max Used 80% 미만 |
| `prd-ctzs-pb01-khs` | NetApp | `dks-1AZ-A` | Max Provisioned 90% | Max Used 80% 미만 |
| `prd-ctzj-pb01-khs` | NetApp | `dks-1AZ-A` | Max Provisioned 94% | Max Used 80% 미만 |

- Cluster Block Storage Usage - SP04
- Cluster Block Storage Usage - SP205
- Cluster NFS Usage - NetApp - `dks-common`
- Cluster NFS Usage - NetApp - `dks-1AZ-A`
- Cluster NFS Usage - NetApp - `dks`
- Cluster NFS Usage - NetApp - `dks_E`

### ※ User Resource Summary
| 대상 클러스터 | 내용 | 비고 |
|---|---|---|
| - | - | - |

- CPU Info
- Mem Info
