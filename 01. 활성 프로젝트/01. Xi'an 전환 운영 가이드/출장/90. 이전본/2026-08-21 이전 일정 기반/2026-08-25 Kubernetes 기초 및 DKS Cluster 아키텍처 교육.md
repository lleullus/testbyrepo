---
title: "2026-08-25 Kubernetes 기초 및 DKS Cluster 아키텍처 교육"
status: current
doc_type: training-material
scope: "Kubernetes 사전 지식이 없는 Xi'an 현지 담당자를 위한 1일 기초 이론 및 DKS 아키텍처 교육"
created: "2026-08-21"
updated: "2026-08-21"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획(안)]]"
---

# 2026-08-25 Kubernetes 기초 및 DKS Cluster 아키텍처 교육

> [!summary] 교육의 핵심
> **Kubernetes는 여러 서버에서 Container 기반 애플리케이션을 배포·실행·유지하는 플랫폼이다. DKS는 Kubernetes를 역할별 Node, Network, Storage, Registry, Monitoring, KubeSphere 운영 구조로 표준화한 아키텍처다.**

> [!important] 교육 목적
> 이 문서는 Kubernetes를 처음 접하는 담당자가 이후 운영 Manual 교육과 실제 Cluster 구축 과정을 이해할 수 있도록 공통 구조를 설명한다. 세부 명령어와 환경값을 암기하는 것이 아니라, **구성요소가 왜 존재하고 서로 어떻게 연결되는지**를 이해하는 것이 목표다.

## 교육 완료 목표

교육 종료 후 다음 내용을 큰 수준에서 설명할 수 있어야 한다.

1. Kubernetes Cluster에서 Control Plane과 Worker Node의 역할
2. Image가 Pod로 실행되어 사용자에게 서비스되는 흐름
3. Network·Storage·Registry·Monitoring이 필요한 이유
4. DKS의 Bastion·Control Plane·ETCD·Router·Infra·Worker 역할
5. KubeSphere Host와 Member Cluster의 관계
6. Xi'an의 Host·Production Member·Development Member·Harbor 구성
7. Kubernetes 내부 영역과 Load Balancer·DNS·Storage·인증 등 외부 연계 영역의 경계

## 이번 교육에서 다루지 않는 범위

- Calico의 VXLAN·Typha·IPAM 내부 설정
- Kubespray 변수와 실행 명령
- Binary·Container Image 전체 목록
- 실제 IP·hostname·CIDR·방화벽 Rule
- 인증서·Secret·계정 원문
- Upgrade·Migration 절차
- 상세 VM 용량 계산

세부값과 실행 절차는 이후 운영 Manual과 실제 구축일에 대상 환경을 기준으로 다시 확인한다.

---

## 1. 교육 구성

| 구분 | 주요 내용 | 교육 후 이해해야 할 것 |
|---|---|---|
| 오전 1 | VM·Container·Kubernetes의 관계 | Kubernetes가 필요한 이유 |
| 오전 2 | Cluster·Control Plane·Worker·Pod | Kubernetes의 기본 구조 |
| 오전 3 | Image → Deployment → Pod → Service → Ingress | 애플리케이션 실행과 사용자 접근 흐름 |
| 오후 1 | Network·DNS·Storage·Harbor·Monitoring | 운영에 필요한 주변 기능 |
| 오후 2 | DKS Node 역할과 설계 이유 | DKS가 Kubernetes를 어떻게 표준화했는지 |
| 오후 3 | API·사용자·Image·Storage·Monitoring 경로 | 주요 요청과 데이터의 이동 경로 |
| 오후 4 | KubeSphere Host·Member와 Xi'an 실제 구성 | 운영 대상의 전체 구조 |

---

# 오전 — Kubernetes 기본 구조

## 2. VM과 Container에서 Kubernetes까지

### 2.1 여러 서버 운영에서 생기는 문제

애플리케이션이 늘어나면 서버 또는 VM 한 대씩 관리하는 방식만으로는 다음 문제를 일관되게 처리하기 어렵다.

- 어떤 서버에서 어떤 애플리케이션을 실행할지 결정해야 한다.
- 애플리케이션이 중단되면 다시 실행해야 한다.
- 사용량 증가에 따라 실행 개수를 늘려야 한다.
- 서버 장애 시 다른 서버에서 다시 실행해야 한다.
- 애플리케이션 간 Network와 외부 접속 경로를 관리해야 한다.
- 애플리케이션 데이터와 운영 상태를 별도로 관리해야 한다.

Kubernetes는 여러 서버를 하나의 Cluster로 묶고, Container 기반 애플리케이션의 배치·연결·상태 유지를 담당한다.

### 2.2 VM, Image, Container, Kubernetes

| 구분 | 의미 | Kubernetes와의 관계 |
|---|---|---|
| VM | OS를 포함한 독립 실행환경 | Kubernetes Node를 구성하는 기반이 될 수 있음 |
| Container Image | 애플리케이션과 실행에 필요한 파일을 묶은 원본 | Harbor 같은 Registry에 저장 |
| Container | Image를 실제로 실행한 프로세스 환경 | Kubernetes Node에서 실행 |
| Kubernetes | 여러 Node에서 Container를 배치·연결·유지하는 플랫폼 | Cluster 단위 운영 제공 |

Container는 실행환경을 일관되게 만든다. Kubernetes는 여러 서버에서 많은 Container를 **어디에 실행하고, 몇 개 유지하며, 어떻게 연결할지** 관리한다.

**[그림 삽입 위치: VM·Container·Kubernetes의 관계]**

### 2.3 Kubernetes가 담당하는 기능

- 애플리케이션 배포
- 원하는 실행 개수 유지
- 중단된 Pod의 재생성
- 적절한 Node로 배치
- Pod 간 Network 연결
- Service와 Ingress를 통한 접근
- 외부 Storage 연결
- 상태 조회와 운영 자동화의 기반 제공

---

## 3. Kubernetes Cluster 기본 구조

### 3.1 Cluster와 Node

- **Cluster**: 여러 Node와 Kubernetes 구성요소를 하나의 운영 단위로 묶은 것
- **Node**: Kubernetes가 사용하는 서버 또는 VM
- **Control Plane**: 요청을 받고 Cluster 상태를 판단·조정하는 영역
- **Worker Node**: 실제 애플리케이션 Pod가 실행되는 영역
- **Pod**: Kubernetes에서 Container가 실행되는 기본 단위

**[그림 삽입 위치: Kubernetes Cluster 기본 구조 — Control Plane, Worker Node, Pod]**

### 3.2 Control Plane 구성요소

| 구성요소 | 주요 역할 |
|---|---|
| API Server | Kubernetes 관리 요청의 진입점 |
| Scheduler | 새 Pod를 실행할 Node 선택 |
| Controller Manager | 원하는 상태와 실제 상태를 일치시키도록 조정 |
| ETCD | Kubernetes Cluster 상태 저장 |

Control Plane은 **API로 요청을 받고, Pod를 배치하며, 원하는 상태를 유지하고, Cluster 상태를 저장**한다.

### 3.3 Worker Node 구성요소

| 구성요소 | 주요 역할 |
|---|---|
| kubelet | 해당 Node의 Pod 상태 관리 |
| Container Runtime | Container 실행. DKS에서는 containerd 사용 |
| Pod | 실제 애플리케이션 Container 실행 |

### 3.4 원하는 상태와 실제 상태

Kubernetes의 핵심은 애플리케이션을 한 번 실행하는 것이 아니라 **원하는 상태를 계속 유지하는 것**이다.

```text
원하는 상태: Web Pod 3개
실제 상태: Web Pod 2개
→ Kubernetes가 부족한 Pod 1개를 새로 생성
```

Worker Node 한 대가 중단되어도 Workload가 여러 Node에 분산되어 있고 필요한 Network·Storage 조건이 갖춰져 있다면, Kubernetes는 다른 Node에서 Pod를 다시 실행할 수 있다.

---

## 4. 애플리케이션 실행과 사용자 접근 흐름

### 4.1 핵심 객체

| 객체 | 역할 |
|---|---|
| Image | 애플리케이션 실행 원본 |
| Pod | Container가 실행되는 Kubernetes 기본 단위 |
| Deployment | Pod의 배포 상태와 원하는 개수를 유지 |
| Service | 변경될 수 있는 Pod 앞에 안정적인 접근점 제공 |
| Ingress | HTTP/HTTPS 요청을 Service로 연결 |
| Namespace | Cluster 안에서 리소스를 논리적으로 분리 |

### 4.2 배포 흐름

```text
Container Image
→ Deployment 생성
→ Worker Node에 Pod 실행
→ Service가 Pod 연결
→ Ingress가 외부 요청 경로 제공
```

1. 애플리케이션 Image를 Registry에 저장한다.
2. Deployment가 사용할 Image와 Pod 개수를 정의한다.
3. Kubernetes가 Worker Node에 Pod를 배치한다.
4. Service가 여러 Pod에 안정적인 접근점을 제공한다.
5. 외부 HTTP/HTTPS 요청은 Ingress를 통해 Service로 전달된다.

### 4.3 사용자 요청 흐름

```text
사용자
→ External Load Balancer
→ Router / Ingress Controller
→ Service
→ Pod
```

> [!important] 상태 판정의 경계
> `Pod Running`은 Container가 실행 중이라는 증거다. 사용자가 실제 서비스를 이용할 수 있다는 최종 증거는 **Service·Ingress·Load Balancer를 포함한 전체 경로와 실제 응답**까지 확인해야 한다.

**[그림 삽입 위치: Image → Deployment → Pod → Service → Ingress → 사용자 전체 흐름]**

### 4.4 Namespace와 KubeSphere Project

Kubernetes의 Namespace는 하나의 Cluster 안에서 리소스를 분리하는 논리적 경계다. Xi'an DKS에서 **KubeSphere Project는 Kubernetes Namespace와 연결된다.**

이후 운영교육에서는 Namespace 위에 다음 관리 개념을 연결한다.

```text
Workspace
→ Project / Namespace
→ 사용자
→ Role
→ Quota
```

---

## 5. 애플리케이션 운영에 필요한 주변 기능

### 5.1 Network와 DNS

Kubernetes에서는 서로 다른 Node의 Pod가 통신하고, Service 이름으로 대상 애플리케이션을 찾을 수 있어야 한다.

- **Pod Network**: 서로 다른 Node의 Pod 간 통신 제공
- **Service Network**: Service에 안정적인 가상 접근점 제공
- **DNS**: Service 이름을 내부 주소로 해석
- **Ingress**: 외부 HTTP/HTTPS 요청을 Service로 연결

DKS에서는 Pod Network 구현에 **Calico**, Cluster 내부 DNS에 **CoreDNS**를 사용한다. 8/25에는 내부 설정이 아니라 각 구성요소의 역할만 이해한다.

### 5.2 Storage

Pod는 재생성될 수 있으므로 애플리케이션 데이터는 Pod 수명과 분리되어야 한다.

```text
Pod
→ PVC
→ StorageClass
→ Trident
→ NetApp Storage
```

| 용어 | 역할 |
|---|---|
| PVC | 애플리케이션이 Storage를 요청하는 객체 |
| StorageClass | 사용할 Storage 정책 정의 |
| Trident | Kubernetes와 NetApp Storage 연결 |
| PV | 실제로 제공된 Volume을 Kubernetes에서 표현 |

> [!important] Storage 판정의 경계
> `PVC Bound`는 Volume 공급이 진행됐다는 증거다. 실제 사용 가능 여부는 **Pod Mount와 Container Read/Write**까지 확인해야 한다.

**[그림 삽입 위치: PVC → StorageClass → Trident → NetApp Storage]**

### 5.3 Registry와 Harbor

Harbor는 DKS의 Private Container Registry다.

```text
Image Build
→ Harbor Project / Repository
→ Kubernetes Node에서 Image Pull
→ Pod 실행
```

Harbor가 제공하는 주요 기능은 다음과 같다.

- Container Image 저장
- Project와 Repository 관리
- 사용자와 권한 관리
- Image Push·Pull

> [!note] 객체 구분
> KubeSphere Project는 Kubernetes Namespace와 연결되는 운영 단위다. Harbor Project는 Image Repository와 접근 권한을 관리하는 Registry 단위다.

**[그림 삽입 위치: Harbor에서 Member Cluster로 Image가 공급되는 흐름]**

### 5.4 Monitoring

```text
Node / Kubernetes Component / Workload
→ Prometheus
→ Grafana / Alertmanager
```

| 구성요소 | 역할 |
|---|---|
| Prometheus | Metric 수집·저장 |
| Grafana | Metric 시각화 |
| Alertmanager | Alert 전달 |

Monitoring은 단순히 Dashboard를 보여주는 기능이 아니다. Cluster와 Workload 상태를 **증거로 확인하고 이상을 발견하는 운영 기반**이다.

**[그림 삽입 위치: Prometheus·Grafana·Alertmanager Monitoring 흐름]**

### 5.5 전체 서비스 흐름 정리

```text
Harbor에 Image 저장
→ Kubernetes가 Worker Node에 Pod 실행
→ Service가 Pod 연결
→ Ingress와 Load Balancer를 통해 사용자 접근
→ PVC와 Trident를 통해 Storage 사용
→ Prometheus와 Grafana가 상태 관측
```

---

# 오후 — DKS 및 Xi'an 실제 아키텍처

## 6. Kubernetes와 DKS의 관계

### 6.1 DKS의 위치

```text
Kubernetes
= Container Workload 실행·조정 기반

DKS
= Kubernetes를 정해진 Node 역할, Software 구성, 설치·운영 기준으로 배포하는 표준 아키텍처
```

DKS Installer는 Kubespray와 Ansible을 기반으로 Linux Node를 준비하고 Kubernetes Cluster를 자동화된 방식으로 구성한다.

| 도구·구성요소 | 역할 |
|---|---|
| Ansible | 여러 Linux Node의 설정 자동화 |
| Kubespray | Ansible Playbook 기반 Kubernetes Cluster 설치 |
| kubectl | Kubernetes API에 접근하는 CLI |
| Helm | Kubernetes 애플리케이션 Package 설치·관리 |
| containerd | Container 실행 Runtime |
| Calico | Pod Network |
| CoreDNS | Cluster 내부 DNS |
| Ingress Nginx | 외부 HTTP/HTTPS 요청 처리 |
| Trident | Kubernetes와 NetApp Storage 연결 |
| Prometheus / Grafana | Monitoring과 시각화 |
| KubeSphere | Kubernetes와 Multi-Cluster 운영 계층 |
| Harbor | Private Container Registry |

Bastion·External ETCD·Router·Infra를 별도 역할로 분리하는 방식은 모든 Kubernetes Cluster가 반드시 가져야 하는 구조가 아니라 **DKS의 표준 아키텍처 선택**이다.

---

## 7. DKS Node 역할

| DKS 역할 | 주요 목적 | 대표 구성요소·작업 |
|---|---|---|
| Bastion | 설치·관리 작업의 진입점 | Ansible, Kubespray, kubectl, Git, Helm |
| Control Plane | Kubernetes 제어와 API 제공 | API Server, Scheduler, Controller Manager |
| External ETCD | Cluster 상태 저장 | ETCD |
| Router | 외부 HTTP/HTTPS 요청 처리 | Ingress Controller |
| Infra | 플랫폼·관측 구성요소 배치 | Monitoring, Dashboard, KubeSphere 관련 Component |
| Worker | 사용자 애플리케이션 실행 | Deployment, Pod, 사용자 Workload |

Bastion은 사용자 Workload를 실행하는 일반 Worker Node가 아니라 설치와 운영을 위한 관리 진입점이다.

### 7.1 고가용성의 기본 구조

DKS는 중요 역할을 여러 Node에 분산해 단일 Node 장애가 전체 기능 중단으로 바로 이어지는 위험을 줄인다.

- Control Plane: 여러 Node와 API Load Balancer
- External ETCD: 여러 ETCD Member
- Router: 여러 Node와 Ingress Load Balancer
- Infra: 주요 플랫폼 구성요소의 분산 배치 기반
- Worker: 업무 용량과 가용성 요구에 따라 수량 조정

“모든 역할이 반드시 3대”라는 의미는 아니다. Xi'an 카탈로그에서 Bastion과 Worker 수량은 Cluster 역할과 용량에 따라 다르고, Control Plane·ETCD·Router·Infra는 역할별 다중 Node로 구성되어 있다.

**[그림 삽입 위치: DKS 역할별 Node 배치 — Bastion, Control Plane, ETCD, Router, Infra, Worker]**

---

## 8. DKS의 설계 선택과 이유

DKS의 구성은 단순히 제품을 나열한 것이 아니라, 장애 영향과 운영 경계를 분리하기 위한 설계다.

| 설계 선택 | 이유 | 잘못 이해하면 생기는 문제 |
|---|---|---|
| VM 기반 Node | 표준화된 배포·증설·교체와 인프라 관리 경계 확보 | Kubernetes가 물리 인프라까지 자동으로 관리한다고 오해 |
| 역할별 Node 분리 | 제어·트래픽·플랫폼·사용자 Workload의 장애와 용량 영향 분리 | 모든 Node를 동일한 Worker로 이해 |
| External ETCD | Cluster 상태 저장 계층을 Workload 실행 영역과 분리 | ETCD를 일반 애플리케이션 DB로 이해 |
| External Load Balancer | API와 사용자 트래픽을 여러 Node에 분산 | 특정 Node 주소를 Cluster의 고정 진입점으로 오해 |
| Host·Member 분리 | 중앙 관리와 실제 Workload 실행 영역 분리 | Member가 Host 안으로 합쳐진다고 오해 |
| External Storage | Pod 재생성과 데이터 수명을 분리 | Pod가 다시 생성되면 데이터도 자동으로 유지된다고 오해 |
| Harbor 분리 | Image 공급과 Kubernetes 리소스 운영 책임 분리 | KubeSphere Project와 Harbor Project를 동일하게 이해 |

---

## 9. 주요 요청·데이터 경로

### 9.1 Kubernetes 관리 요청

```text
운영자 / kubectl
→ API VIP
→ External Load Balancer
→ Control Plane
→ Kubernetes API
```

API 요청은 Kubernetes 관리 작업을 위한 경로다. Load Balancer는 사용 가능한 Control Plane으로 요청을 전달한다.

### 9.2 사용자 서비스 요청

```text
사용자
→ Ingress VIP / Service Domain
→ External Load Balancer
→ Router / Ingress Controller
→ Service
→ Pod
```

API 경로는 Control Plane으로 연결되고, 사용자 HTTP/HTTPS 경로는 Router와 Ingress를 통해 실제 Workload로 연결된다.

### 9.3 Image 공급

```text
Harbor
→ Container Runtime이 Image Pull
→ Pod 실행
```

### 9.4 영속 데이터

```text
Pod
→ PVC
→ StorageClass
→ Trident
→ NetApp Storage
```

### 9.5 Monitoring

```text
Node / Kubernetes Component / Workload
→ Prometheus
→ Grafana / Alertmanager
```

**[그림 삽입 위치: API·사용자·Image·Storage·Monitoring의 다섯 가지 경로]**

---

## 10. 접근·연계·책임 경계

Kubernetes Cluster는 Load Balancer, DNS, Storage, Registry, 인증 같은 외부 시스템과 연결되어 동작한다. 문제가 발생하면 먼저 어느 영역까지 정상인지 구분해야 한다.

| 목적 | 진입점·연계 대상 | 주요 확인 영역 | 경계에서 확인할 내용 |
|---|---|---|---|
| Cluster 설치·관리 | Bastion | DKS Installer, kubectl, 접근 권한 | 대상 Cluster·계정·Network 접근 |
| Kubernetes 관리 요청 | API VIP → Control Plane | Kubernetes API와 Control Plane 상태 | External LB와 API Server 중 첫 단절 위치 |
| 사용자 서비스 요청 | Ingress VIP → Router → Service → Pod | Ingress·Service·Workload | DNS·LB·방화벽과 Cluster 내부 경로 구분 |
| Web 기반 리소스 관리 | KubeSphere | Workspace·Project·Role·Quota | 사용자 인증과 Kubernetes 권한 연결 |
| Image Push·Pull | Harbor | Registry Project·Repository·사용자 권한 | 인증서 신뢰·로그인·Repository·권한 구분 |
| 영속 데이터 | Trident → NetApp | PVC·PV·Mount·Read/Write | Kubernetes Provisioning과 Storage·Network 경계 구분 |
| 이름·외부 트래픽 | DNS·External Load Balancer | Domain·VIP·Health Check | Cluster 밖 외부 의존성 확인 |
| 사용자 인증 | KubeSphere·Harbor 인증 연계 | 계정·그룹·Role | 실제 인증 방식과 현장 보안 정책 확인 |

실제 담당 조직과 승인 절차는 현장에서 확정한다. 8/25에는 **문제의 위치를 Kubernetes 내부와 외부 연계 영역으로 나누어 생각하는 방법**을 이해한다.

---

## 11. KubeSphere와 Multi-Cluster

### 11.1 KubeSphere의 역할

KubeSphere는 Kubernetes를 대체하지 않는다. Kubernetes 위에서 Cluster와 리소스를 관리하기 위한 Web 기반 운영 계층이다.

- Workspace·Project 관리
- 사용자·Role·권한 관리
- Quota 관리
- Workload·Service·Storage 조회·운영
- Multi-Cluster 관리 화면 제공

| KubeSphere에서 보는 객체 | Kubernetes에서 연결되는 객체·영역 |
|---|---|
| Project | Namespace |
| Workload | Deployment·StatefulSet·Pod 등 |
| Service | Kubernetes Service |
| Storage | PVC·PV·StorageClass |
| Role·권한 | Kubernetes 권한 모델과 연결 |

### 11.2 Host와 Member Cluster

| 구분 | 주요 역할 |
|---|---|
| Host Cluster | Multi-Cluster 중앙 관리와 사용자·Workspace·Project 운영 관점 제공 |
| Member Cluster | 실제 애플리케이션 Workload 실행, 자체 Kubernetes·Storage·Monitoring 운영 |

Member가 Host에 Join된다는 것은 중앙 관리·관측 대상에 편입된다는 의미다. Member의 Kubernetes가 Host 내부로 합쳐지는 것은 아니다.

### 11.3 Harbor의 위치

Harbor는 Host·Member와 별도로 Container Image를 공급하는 Registry 영역이다.

```text
KubeSphere
→ Kubernetes 리소스와 사용자 운영

Harbor
→ Container Image와 Registry Project·권한 운영
```

**[그림 삽입 위치: KubeSphere Host → Member Cluster, Harbor → Member Cluster 관계]**

---

## 12. Xi'an 실제 Cluster 구성

### 12.1 논리 구성

| 영역 | Cluster | 역할 |
|---|---|---|
| Host | `prd-host-pa01-xas` | KubeSphere Multi-Cluster 중앙 관리 |
| Production Member | `prd-apps-pa01-xas` | 운영 애플리케이션 Workload 실행 |
| Development Member | `dev-apps-pa01-xas` | 개발 애플리케이션 Workload 실행 |
| Harbor | `prd-harbor-xas` | Container Image 저장·Push·Pull |

### 12.2 역할별 Node 배치

| 영역 | Bastion | Control Plane | External ETCD | Router | Infra | Worker | 합계 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `prd-host-pa01-xas` | 1 | 3 | 3 | 3 | 3 | 0 | 13 |
| `prd-apps-pa01-xas` | 1 | 3 | 3 | 3 | 3 | 4 | 17 |
| `dev-apps-pa01-xas` | 1 | 3 | 3 | 3 | 3 | 2 | 15 |
| `prd-harbor-xas` | Harbor Server 1대 | — | — | — | — | — | 1 |

### 12.3 이 표에서 읽어야 할 것

- Host Cluster는 중앙 관리 역할이며 현재 카탈로그상 사용자 Workload용 Worker가 없다.
- Production·Development Member에는 실제 사용자 Workload를 실행하는 Worker가 있다.
- 각 Kubernetes Cluster는 API 접근 경로와 사용자 Ingress 경로를 별도로 가진다.
- 각 Cluster는 Pod·Service Network를 별도로 사용한다.
- Harbor는 Member Cluster에 Container Image를 공급한다.

> [!important] Node 수량과 Workload 수용량
> Node 수량은 역할 배치를 보여주는 값이다. 실제 Workload 수용량은 Worker의 CPU·Memory·Disk, 예약 자원, Replica 수, Storage·Network 요구사항과 운영 정책을 함께 확인해야 한다. Host의 Node 수가 많아도 사용자 Workload용 Worker가 없다면 일반 업무 Pod 실행 영역으로 판단하지 않는다.

### 12.4 이번 신규 Member 구축과의 관계

현재 표는 Xi'an의 기준 아키텍처를 설명한다. 이번 출장에서 신규 구축할 Member의 실제 identity, Node, IP, VIP, CIDR, StorageClass와 접근조건은 **8/31 실제 환경 확인 단계에서 다시 확정**한다.

**[그림 삽입 위치: Xi'an Host·Production Member·Development Member·Harbor 전체 구성도]**

상세값은 아래 Cluster 카탈로그에서 확인한다.

- [[10. 기준 및 설계/클러스터 카탈로그/01. prd-host-pa01-xas|prd-host-pa01-xas]]
- [[10. 기준 및 설계/클러스터 카탈로그/02. prd-harbor-xas|prd-harbor-xas]]
- [[10. 기준 및 설계/클러스터 카탈로그/03. prd-apps-pa01-xas|prd-apps-pa01-xas]]
- [[10. 기준 및 설계/클러스터 카탈로그/04. dev-apps-pa01-xas|dev-apps-pa01-xas]]

---

## 13. 이후 운영·구축 교육과 연결

| 일정 | 교육·작업 | 8/25 내용과의 연결 |
|---|---|---|
| 8/26 | KubeSphere Operation | Workspace·Project·사용자·Role·Quota 운영 |
| 8/27 오전 | Operations Manual | Worker·Node·API·인증서 등 운영 작업 |
| 8/27 오후 | Harbor Manual | Image Project·사용자·Push·Pull 관리 |
| 8/28 오전 | User Manual | DKS·Harbor·KubeSphere 사용자 흐름 |
| 8/28 오후 | Troubleshooting Guide | Image·Storage·권한·Dashboard 문제의 시작점 |
| 8/31 | 환경 확인과 Pre-setting | Bastion·VM·Node·Inventory 준비 |
| 9/1 | Kubernetes 구축 | Kubespray와 Kubernetes 기본 검증 |
| 9/2 | Storage 구축 | Trident·StorageClass·PVC·Mount·Read/Write |
| 9/3 | Monitoring·KubeSphere·Host Join | 플랫폼 완성과 Multi-Cluster 확인 |

```text
8/25: 구조와 설계 이유를 이해
→ 8/26~8/28: 운영 Manual에서 사용 방법 확인
→ 8/31~9/3: 실제 환경에서 그 구조를 구축
```

---

## 14. 핵심 정리

1. Kubernetes는 여러 Node에서 Container 기반 애플리케이션을 배치·연결·유지한다.
2. Control Plane은 Cluster를 제어하고 Worker Node는 실제 Pod를 실행한다.
3. 사용자 서비스는 `Load Balancer → Ingress → Service → Pod` 경로로 연결된다.
4. `Pod Running`만으로 사용자 서비스 정상까지 증명되지는 않는다.
5. Pod 데이터는 PVC·StorageClass·Trident를 통해 External Storage와 연결된다.
6. `PVC Bound`와 실제 Mount·Read/Write는 서로 다른 성공 단계다.
7. DKS는 Node 역할과 운영 구성요소를 분리해 장애 영향과 운영 경계를 관리한다.
8. KubeSphere Host는 중앙 관리, Member Cluster는 실제 Workload 실행 영역이다.
9. Harbor는 Image를 관리하며 KubeSphere Project와 Harbor Project는 서로 다른 객체다.
10. Node 수량은 역할 배치를 뜻하며 실제 Workload 수용량을 직접 의미하지 않는다.

### 학습 확인

- Control Plane과 Worker Node의 차이는 무엇인가?
- Image, Deployment, Pod의 관계는 무엇인가?
- Service와 Ingress는 각각 왜 필요한가?
- API VIP와 Ingress VIP의 목적은 어떻게 다른가?
- Storage에서 PVC Bound 이후 무엇을 추가로 확인해야 하는가?
- Bastion·Router·Infra 역할을 분리한 이유는 무엇인가?
- KubeSphere와 Harbor는 각각 무엇을 관리하는가?
- Host와 Member Cluster는 어떤 관계인가?
- Kubernetes 내부 문제와 Load Balancer·DNS·Storage 문제는 어떻게 구분할 수 있는가?
- Node 수량만으로 Workload 수용량을 판단할 수 없는 이유는 무엇인가?

---

## 15. 후속 교육으로 넘길 주제

아래 주제는 8/25에 개념과 위치만 확인하고 세부 내용은 후속 교육 또는 별도 Runbook에서 다룬다.

| 질문 | 8/25에서 확인할 범위 | 후속 확인 |
|---|---|---|
| 왜 VM을 사용하는가? | 표준 Node 배포·교체와 인프라 관리 경계 | VM Template·용량 설계 문서 |
| 사용자는 자원을 어떻게 할당받는가? | Workspace·Project·Role·Quota 사용 | 8/26 KubeSphere Operation |
| AD/LDAP는 어떻게 연계되는가? | 인증·그룹 정책이 외부 경계와 연결됨 | 현장 인증 정책과 운영 절차 |
| Upgrade·Migration은 어떻게 하는가? | 별도 영향도 높은 변경 작업 | 승인된 Upgrade Runbook |
| Harbor는 어떻게 복구하거나 이중화하는가? | Harbor가 Image 공급 영역임을 이해 | Xi'an Harbor 구성·복구 정책 |
| 실제 VM 사양은 무엇인가? | 역할과 수량만 확인 | Cluster 카탈로그·용량 산정 기준 |
| 실제 IP·VIP·CIDR은 무엇인가? | API와 Ingress 경로의 차이 이해 | Cluster 카탈로그·8/31 실제 환경 확인 |
| Calico·Trident·Kubespray의 세부 설정은 무엇인가? | 각 구성요소의 역할 이해 | 9/1~9/3 실제 구축 Manual |
| 방화벽 Rule과 접근 승인은 어떻게 처리하는가? | 외부 Network·보안 경계가 있음을 이해 | 현장 정책과 담당 영역 확인 |

---

## 16. 핵심 용어

| 용어 | 한 줄 정의 |
|---|---|
| Cluster | 여러 Node와 Kubernetes 구성요소를 하나로 관리하는 단위 |
| Control Plane | API와 Cluster 상태 조정을 담당하는 영역 |
| Worker Node | 실제 애플리케이션 Pod가 실행되는 Node |
| Pod | Kubernetes에서 Container가 실행되는 기본 단위 |
| Deployment | Pod의 배포와 원하는 개수를 유지하는 객체 |
| Service | Pod 앞에 안정적인 내부 접근점을 제공하는 객체 |
| Ingress | 외부 HTTP/HTTPS 요청을 Service로 연결하는 규칙 |
| Namespace | Cluster 안에서 리소스를 분리하는 논리적 경계 |
| Registry | Container Image를 저장·공급하는 시스템 |
| PVC | 애플리케이션이 Storage를 요청하는 객체 |
| StorageClass | Volume 공급 방식과 정책을 나타내는 객체 |
| Monitoring | Metric을 수집·시각화·알림하는 운영 기능 |
| Host Cluster | KubeSphere Multi-Cluster 중앙 관리 영역 |
| Member Cluster | 실제 애플리케이션 Workload가 실행되는 Cluster |
| Bastion | 설치·운영 도구와 접근 경로를 제공하는 관리 서버 |
| Harbor | DKS Private Container Registry |
| Trident | Kubernetes와 NetApp Storage를 연결하는 CSI 구성요소 |

---

## 관련 문서

- [[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획(안)]]
- [[10. 기준 및 설계/클러스터 카탈로그/클러스터 카탈로그|Xi'an 클러스터 카탈로그]]
- [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
- [[50. 운영/01. Operations Overview/운영 안내|운영 안내]]
- [[50. 운영/07. DKS User Guide/01. DS Kubernetes Service Overview|DS Kubernetes Service Overview]]
