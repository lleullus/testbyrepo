# 개요
DKS-C 콘솔의 SW 아키텍처, 기술 스택, 기본 Addons, vSphere Supervisor Service, DevOps 이미지 저장소를 정리한 문서.

## 핵심 내용
### DKS Portal 아키텍처
![](https://confluence.samsungds.net/download/attachments/3557913088/image-2026-5-15_13-59-47.png?version=1&modificationDate=1778821188000&api=v2)

### 콘솔 Applications & 기술 Stack
#### Console 클러스터 — DKS-C Console 전반 기능 제공 (자원관리, 권한관리, 서비스 요청, CI/CD)
| Component | 설명 | 기술 Stack | 소스 |
|---|---|---|---|
| DKS Console | Front 요청 인증/로깅, K8/모니터링/외부 시스템 연동, API routing | React, Golang | console |
| Portal API | DB 연동 (프로젝트, 클러스터, 권한), Knox API, SSG API, GraphQL (VCFA MGMT) | Java, Spring Boot | console-portal |
| DKS Batch | CUP Batch 데이터 DB I/F, 결재 자원 상태 체크/처리 | — | console-batch |
| DevOps API | CI/CD 파이프라인, workflow-runner 연동, Nats CI/CD 로그 저장 | — | console-devops |
| VCFA MGMT | Cluster 관리, 자원 CRUD (ArgoCD → VKS) | Golang | vcfa-mgmt |
| Backup Agent | Velero Backup 외부 저장소 연동 | — | backup-service |
| DKS DB | Portal, DevOps, CUP, Knox 데이터 저장 | PostgresSql | — |
| Nats | CI/CD 로그 스트리밍, CI/CD 이벤트 | — | — |

#### Gateway Cluster — Backend Gateway API 및 인증 처리
| Component | 설명 | 기술 Stack |
|---|---|---|
| APISIX | DKS-C Backend Gateway, K8S NativeAPI RestAPI 서비스, Control/Data Plane 분리, AutoScaling | nginx, lua |
| KeyCloack | DS ADFS SSO 연동 OIDC 중앙 집중 인증 | OIDC, JWT |

#### DevOps 클러스터 — DevOps Task API 및 빌드/배포 처리
| Component | 설명 | 기술 Stack | 소스 |
|---|---|---|---|
| workflow-runner | DevOps API 통신, 빌드 목록 가져와 빌드 서버 생성 후 workflow-engine 실행 | Golang | workflow-runner |
| workflow-engine | 정의된 CI/CD Task 정보 가져와 빌드 서버 실행 | Golang | workflow-engine |
| tenant | CI/CD Task 실행 Docker in Docker 빌드 서버 | Docker in Docker, Shell Script, Golang | dind |
| ci-git-clone | CI/CD 소스 다운로드 | shell script | ci-git-clone |
| builder | Dockerfile 빌드 및 이미지 Push | Golang | builder |
| deploy-k8s | Kubernetes 리소스 배포 | Golang | deploy-k8s |
| container-logger | Dind 서버 Task 로그 실시간 Nats 전송 | Golang | container-logger |

#### Monitoring 클러스터 — 클러스터 메트릭 중앙 관리, 알람/동보 제어
| Component | 설명 | 기술 Stack | 소스 |
|---|---|---|---|
| vm-alert | 알람 Rule 관리, 전파 프로세스 제어, Runbook 서비스 | VictoriaMetrics, AlertManager | vm-alert |
| vm-cluster-main | 메트릭 중앙 저장소 (Active-Active HA) | VictoriaMetrics | — |
| vm-cluster-archive | 메트릭 장기 저장 Archive | VictoriaMetrics | — |
| vm-read | 중앙/Archive 저장소 메트릭 조회 | VictoriaMetrics | vm-read |
| vm-write | 메트릭 수집 게이트웨이 | VictoriaMetrics | vm-write |
| vm-record | 집계/장기 저장 메트릭 관리, Archive 이전 | VictoriaMetrics | vm-record |
| grafana | 메트릭 실시간 모니터링 시각화 | Grafana | grafana |
| alert-dispatcher | 알람 P-DEP 연동 동보 전송 | Golang | alert-dispatcher |
| monitoring-runbooks | 메트릭 알람 운영 가이드 | Hugo Framework | monitoring-runbooks |

#### Logging 클러스터 — 로그 수집 및 시각화
| Component | 설명 | 기술 Stack | 소스 |
|---|---|---|---|
| opensearch | 로그 데이터 저장, 검색/분석 | Java, Apache Lucene | dks-logs-hub |
| opensearch-dashboards | 데이터 검색/분석/시각화 웹 UI | Node.js, React | — |
| opentelemetry-collector | 로그 수집 에이전트 데이터 수집/가공/전송 | golang | — |
| spoditor | Statefulset Pod 제어, 오픈서치 노드별 인증서 적용 | golang | dks-spoditor |

### DKS-C VKS 설치 기본 Addons (13개)
| 애드온 | Version | 제공 | 설명 | 비고 |
|---|---|---|---|---|
| cert-manager | 1.18.2 | VCF Default | Certificate management | |
| contour | 1.33.0 | VCF Default | Ingress controller | |
| velero | 1.17.0 | VCF Default | Backup/restore, disaster recovery | |
| victoria-metrics-operator | 0.61.0 | Custom | 메트릭 수집 에이전트 오퍼레이터 | Carvel 기반 |
| dks-metrics-agent | 0.1.6 | Custom | 메트릭 수집 에이전트 | Helm Deploy |
| dks-logs-agent | 0.1.0 | Custom | 로그 수집 에이전트 | Carvel 기반 |
| dks-events-agent | 0.1.0 | Custom | k8s 이벤트 수집 에이전트 | Carvel 기반 |
| kyverno | 3.7.0 | Custom | 정책 관리 컨트롤러 | Helm Deploy |
| kyverno-policies | 3.7.0 | Custom | DKS 정책 설정 | Helm Deploy |
| policy-reporter | 3.7.1 | Custom | 정책 리포트 | Helm Deploy |
| trident-operator | 25.06.2 | Custom | NetApp Storage Driver | Helm Deploy |
| vertical-pod-autoscaler | 1.10.1 | Custom | Pod 리소스 조정 | Helm Deploy |
| velero-tz | 1.17.0 | Custom | velero cron timezone 적용 | Helm Deploy |

### vSphere Supervisor Service (VCF 9.0)
| Supervisor Service | Version | 인스턴스 명 | 설명 |
|---|---|---|---|
| Argo CD | v3.0.19+d67e6eb-vcf | argocd-admin-instance | 관리용 클러스터, Custom Cluster Class, 애드온 배포/관리 |
| Argo CD | v3.0.19+d67e6eb-vcf | argocd-vks-instance | 사용자 클러스터, Custom Cluster Class, 애드온 배포/관리 |
| Harbor | v2.14.2+vmware.2-3a2df66d | dksharbor01 | DKS-C 관리자 이미지, 애드온 이미지/차트 |

### DevOps 이미지 저장소 (Harbor)
| Component | 설명 | 기술 Stack |
|---|---|---|
| Harbor | DevOps 이미지 저장 (v2.14.3) | docker-compose |
| Harbor 동보 알림 메트릭 | 별도 VM, 알림 Rule 관리, 동보 현황, VMAgent 설치 | docker-compose |
| Harbor 시스템 서비스 등록 | 노드 재시작 시 Harbor Services 끊김 방지 | system service |

## 세부 정보
### VKS 배포 구성도
![](https://confluence.samsungds.net/download/attachments/3557913088/image-2026-5-14_18-19-43.png?version=1&modificationDate=1778750384000&api=v2)

### CI/CD DevOps 구성도
![](https://confluence.samsungds.net/download/attachments/3557913088/image-2026-5-15_14-18-39.png?version=1&modificationDate=1778822320000&api=v2)

### Alert 구성도
![](https://confluence.samsungds.net/download/attachments/3633283301/dks-c-alert-arch.png?version=11&modificationDate=1787201317000&api=v2)

## 주의사항 / 예외 / 확인 필요
- **사용자 알람 전송 파이프라인 설계 필요** (미정)
- **사용자(고객) 알람 대상 결정 필요** (미정)