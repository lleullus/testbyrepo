# 개요
Metric Server, Log Server, Addon 영역의 인증서 갱신 기간 설정 및 현재 현황(만료 임박일 포함)을 정리한 현황 보고서.

## 핵심 내용
### 인증서 갱신 주기 패턴
- **365일 인증서** (root-ca 계열): Renew window **3일(72h)**
- **90일 인증서**: Renew window는 용도별 상이
  - Log Server / OpenSearch 클러스터 노드 간 통신: **15일(360h)**
  - Metric Server 서버 인증서 / Addon 에이전트: **10일(240h)**
- **오퍼레이터 자체 생성 인증서**: Duration 매우 김 (1908~2658일), Renew 기본 30일

### 오퍼레이터 자체 생성 인증서 (독립 관리)
| Name | Namespace | Secret | Issuer | Duration | Renew | Created | Renewal |
|---|---|---|---|---|---|---|---|
| vm-operator-root-ca | victoria-metrics-operator | vm-operator-root-ca | vm-operator-root | **2658일**(63800h) | - | 2026-03-18 | **2031-01-23** |
| vm-operator-validation | victoria-metrics-operator | vm-operator-validation | vm-operator-issuer | **1908일**(45800h) | - | 2026-03-18 | **2029-09-10** |

### Metric Server (metric-hub)
| Name | Secret | Issuer | Duration | Renew | Created | Renewal |
|---|---|---|---|---|---|---|
| root-ca | root-ca-secret | selfsigned-root | 365일(8760h) | **3일** | 2026-03-19 | **2027-03-16** |
| vmauth-server-cert | vmauth-server-tls | monitoring-hub-issuer | 90일(2160h) | **10일** | 2026-03-19 | **2026-08-26** |

### Log Server (logs-hub)
- **root-ca**: 365일, Renew **3일**, Renewal **2027-03-16**
- **OpenSearch admin**: opensearch-admin-cert, Renew **15일**, Renewal **2026-08-16**
- **OpenSearch API**: opensearch-cert, Renew **15일**, Renewal **2026-08-16**
- **OpenSearch 노드 간 통신** (모두 logs-issuer, 90일/15일):

| Name | Secret | Renewal |
|---|---|---|
| cluster-coordinator-cert-0 | opensearch-cluster-coordinator-tls-0 | 2026-08-16 |
| cluster-coordinator-cert-1 | opensearch-cluster-coordinator-tls-1 | 2026-08-16 |
| cluster-hot-data-cert-0 | opensearch-cluster-hot-data-tls-0 | 2026-08-16 |
| cluster-hot-data-cert-1 | opensearch-cluster-hot-data-tls-1 | 2026-08-16 |
| cluster-master-cert-0 | opensearch-cluster-master-tls-0 | 2026-08-16 |
| cluster-master-cert-1 | opensearch-cluster-master-tls-1 | 2026-08-16 |
| cluster-master-cert-2 | opensearch-cluster-master-tls-2 | 2026-08-16 |
| cluster-warm-data-cert-0 | opensearch-cluster-warm-data-tls-0 | 2026-08-16 |

- **OpenTelemetry**: otel-gateway-cert, 90일/Renew 15일, Renewal **2026-08-16**

### Addon (에이전트 인증서, 모두 90일/Renew 10일)
| Name | Namespace | Secret | Issuer | Renewal |
|---|---|---|---|---|
| dks-logs-agent-cert | dks-log | dks-logs-agent-tls | dks-logs-agent-issuer | (Created 기준 2026-03-19 + 90일 → **2026-06-17**, RenewWindow 시작: 2026-06-07) |
| dks-metric-agent | dks-metrics | dks-metric-agent-tls | dks-metric-issuer | 위와 동일 |
| dks-events-agent-cert | dks-event | dks-events-agent-tls | dks-events-agent-issuer | 위와 동일 |

> Addon 에이전트 인증서는 원문에 Created/Renewal Time 컬럼이 없으므로, Duration(90일)과 Renew(10일)만으로 계산 가능.

## 세부 정보
### Issuer 매핑 정리
- **Metric Server root**: `selfsigned-root` → `selfsigned-root`
- **Metric Server 서버**: `monitoring-hub-issuer`
- **Log Server root**: `logs-selfsigned-issuer`
- **Log Server 전체** (OpenSearch + otel): `logs-issuer`
- **Addon 에이전트**: 각 영역별 독립 issuer (dks-logs-agent-issuer / dks-metric-issuer / dks-events-agent-issuer)

### OpenSearch 클러스터 노드 구성 (노드 간 통신 인증서)
- **Coordinator**: 2개 (cert-0, cert-1)
- **Master**: 3개 (cert-0, cert-1, cert-2)
- **Hot Data**: 2개 (cert-0, cert-1)
- **Warm Data**: 1개 (cert-0)
- 총 **8개 노드** 인증서, 모두 동일 설정(90일/Renew 15일/2026-03-19 생성)

### 생성일 기준
- 대부분 인증서: **2026-03-19** 생성
- 오퍼레이터 자체 인증서: **2026-03-18** 생성 (하루 차이)

## 주의사항 / 예외 / 확인 필요
- **오퍼레이터 인증서**(vm-operator-root-ca, vm-operator-validation)는 기본 Renew 설정이 `-` (비활성)이며, Duration이 5~7년으로 길어 별도 수동 관리 필요. 기본 Renew가 30일로 표기됨.
- **Addon 에이전트 인증서**의 Created/Renewal Time이 원문에 빠져있음. 90일 Duration + 2026-03-19 생성 가정 시 **2026-08-16 경 만료 임박** → RenewWindow 시작 **2026-08-06** (계산값, 원문 미기재).
- Log Server 노드 간 통신 인증서가 **8개**로 많아 RenewWindow 시작(2026-08-01) 시 동시 갱신 부하 발생 가능.