---
title: "2026-09-03 Member 구축 4일차 - Monitoring·KubeSphere·기존 Host Join 및 최종 인수"
status: current
doc_type: build-note
scope: "2026-09-03 신규 Member Monitoring 구성, Member KubeSphere 설치·검증, 기존 Host Join, Multi-Cluster 확인 및 전체 구축 최종 인수"
created: "2026-08-15"
updated: "2026-08-28"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획]]"
---

# 2026-09-03 Member 구축 4일차 - Monitoring·KubeSphere·기존 Host Join 및 최종 인수

> [!important] 이 문서의 역할
> 이 문서는 9/3 신규 Member Monitoring·KubeSphere·Host Join·최종 인수의 **현장 수행·판정 Source of Truth**이다. 정확한 Manifest·Join 절차·증적 기준과 환경 의존값을 보존한다. 강의의 설명 순서와 Teach-back은 아래 네 개의 강사용 대본으로 분리해 사용하며, 실제 변경은 이 문서와 해당 원본 Runbook을 따른다.

### 9/3 강사용 대본

- [[출장/20. 교육/2026-09-03/오전/01. Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본|오전 1 - Member Monitoring]]
- [[출장/20. 교육/2026-09-03/오전/02. Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본|오전 2 - Member KubeSphere·Pre-Join Gate]]
- [[출장/20. 교육/2026-09-03/오후/01. 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본|오후 1 - 기존 Host Join·Multi-Cluster 검증]]
- [[출장/20. 교육/2026-09-03/오후/02. 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본|오후 2 - 최종 인수]]

> [!success] 9/3 Gate 체계
> 오전에는 `MONITORING PASS / BLOCKED`, `MEMBER SELF PASS / BLOCKED`, 오후 Join은 `MULTI-CLUSTER PASS / BLOCKED`를 사용한다. `PASS / PARTIAL / BLOCKED`는 모든 핵심 기능 검증이 끝난 **최종 인수에서만** 사용한다.

> [!success] Host 전제
> 기존 Xi'an Host Cluster는 이미 구축 완료되어 있다. 9/3에는 Host KubeSphere를 새로 설치하거나 재구성하지 않는다. 기존 Host는 **접근·상태·Join 대상·Multi-Cluster 관리면**만 확인한다. 이번 출장의 신규 구축 대상은 Member Cluster이며, 최종 완료 조건은 신규 Member 자체 정상과 기존 Host Join 후 Multi-Cluster 정상 상태다.

> [!warning] 보호된 값
> ETCD Certificate Secret, kubeconfig, JWT, Host Join용 Secret, Token, Private Key, Password는 화면·문서·로그에 원문을 남기지 않는다. 존재·이름·Type·Key 구조·전달 경로만 승인된 방식으로 확인한다.

## 1. 9/3 확정 범위

### 오전 — Member Monitoring과 Member KubeSphere

- 9/2 Storage Gate 재확인
- 대상 Member context·Node·StorageClass·Registry·Domain·ETCD 실제값 확인
- `monitoring` Namespace와 Preliminary Components 확인
- ETCD Certificate Secret 확인
- Grafana·Prometheus·Alertmanager PVC 선행조건 확인
- Prometheus Operator CRD 적용·`Established` 검증
- DKS custom `kube-prometheus-stack` 적용
- Prometheus·Alertmanager·Grafana Pod·PVC·배치 검증
- Monitoring Ingress 적용·VIP-B 경로 확인
- External ETCD Service·Endpoints·ServiceMonitor 구성
- Prometheus ETCD Target `UP` 확인
- Grafana datasource·Dashboard 확인
- Member KubeSphere installer·ClusterConfiguration 적용
- Member 외부 Monitoring Endpoint·Storage·Registry·ETCD·Role 검증
- KubeSphere Platform Workload 배치와 installer 완료 확인

### 오후 — 기존 Host Join과 최종 인수

- 신규 Member 자체 최종 Pre-Join 검증
- 기존 Host 접근·상태·Join 대상 확인
- 승인된 방식으로 Host Join 수행
- Member Agent·연결 Component 상태 확인
- Host Console에서 신규 Member 등록·상태 확인
- Host에서 Member Resource·Monitoring 관리·관측 확인
- Multi-Cluster 경로·권한·통신 확인
- 8/31~9/3 전체 구축 증적 통합
- 미완료·Blocker·현장 확인사항·Q&A 정리
- 9/4 철수 전 인계할 문서·증적·접근 상태 확정

이날의 핵심 질문은 다음이다.

> **신규 Member의 Monitoring·KubeSphere·기존 Host Join은 각각 무엇을 완성하며, 어떤 증거가 있어야 신규 Member가 Xi'an Multi-Cluster의 운영 가능한 구성원으로 최종 인수됐다고 말할 수 있는가?**

## 2. 전체 선후관계

```text
9/2 Storage Gate 통과
→ 대상 Member context·identity·actual values 재확인
→ monitoring Namespace
→ ETCD Certificate Secret
→ Grafana / Prometheus / Alertmanager Storage 선행조건
→ Prometheus Operator CRD
→ DKS custom kube-prometheus-stack
→ Monitoring Pod·PVC·Node 배치
→ Monitoring Ingress·VIP-B
→ External ETCD Endpoints·Service·ServiceMonitor
→ Prometheus ETCD Target UP
→ Grafana datasource·Dashboard
→ Member kubesphere-installer
→ Member ClusterConfiguration
→ external Monitoring 연결
→ KubeSphere Platform Workload·Console·API 검증
→ multicluster.clusterRole = member
→ 기존 Host 접근·Join 대상 확인
→ 보호된 Join 정보 전달
→ Host Join
→ Member Agent·Host-Member 연결 확인
→ Host Console에서 신규 Member 정상
→ Multi-Cluster 관리·관측 확인
→ 전체 구축 최종 인수
```

### 반드시 분리할 성공

```text
Monitoring Pod Running
≠ Prometheus Target 정상

PVC Bound
≠ Monitoring Pod Mount·데이터 사용 정상

Ingress 존재
≠ Monitoring UI·VIP-B·HTTP 정상

Grafana UI 접속
≠ Datasource·Query·Dashboard 정상

ETCD Service·Endpoints 존재
≠ Prometheus ETCD Target UP

ks-installer Pod Running
≠ KubeSphere 내부 설치 Task 성공

KubeSphere Console 열림
≠ Member Role·external Monitoring·Storage·Platform Workload 정상

Host Console에 Cluster 이름 보임
≠ Host-Member 연결과 Multi-Cluster 관리·관측 정상
```

## 3. 기준 문서

1. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5.5.2 Install kubesphere - member cluster]]
2. [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
3. [[30. 구축 및 전환/Member 클러스터/05.2.1.1 Deploy preliminary components|Preliminary Components]]
4. [[30. 구축 및 전환/Member 클러스터/05.2.1.2 Deploy CRDs|Prometheus Operator CRD]]
5. [[30. 구축 및 전환/Member 클러스터/05.2.1.3 Deploy DKS kube-prometheus-stack components|DKS kube-prometheus-stack]]
6. [[30. 구축 및 전환/Member 클러스터/05.2.1.4 Deploy Ingresses and External ETCD Monitoring|Monitoring Ingress·External ETCD Monitoring]]
7. [[30. 구축 및 전환/Member 클러스터/05.2.1.5 Grafana Custom Dashboard Addition|Grafana Custom Dashboard]]
8. [[30. 구축 및 전환/Member 클러스터/05.2.2 Install KubeSphere on Member Cluster|Member KubeSphere 설치]]
9. [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
10. [[60. 이슈 및 결정/장애/dev-apps-pa01-xas Monitoring 복붙 오적용|Monitoring 복붙 오적용 사례]]
11. [[10. 기준 및 설계/클러스터 카탈로그/클러스터 카탈로그|Xi'an Cluster 카탈로그]]

기존 Host 설치 문서는 비교·정상 기준일 뿐 9/3 적용 대상이 아니다.

---

# Part 1. Preflight와 Preliminary Components

## 4. 9/2 Storage Gate 재확인

Monitoring과 KubeSphere는 PVC와 StorageClass를 사용한다. 9/2 검증이 불완전하면 9/3 설치 실패를 KubeSphere 문제로 잘못 해석할 수 있다.

### 4.1 재확인 항목

- Kubernetes API·Node·CNI·DNS 기본 기능 정상
- Trident Operator·Controller·Node Component 정상
- Backend `online`
- 승인된 StorageClass 존재
- Test PVC Bound
- Test Pod Mount 성공
- Container Write·Read·재읽기 성공
- 테스트 리소스 정리 결과 확인
- Monitoring PVC에 사용할 StorageClass·용량·Namespace 확정
- 역할별 Node에서 Storage 접근 차이 없음

### 4.2 진행 금지 상태

- Backend `offline`
- StorageClass 실제값 미확정
- PVC Pending
- Pod `FailedMount`
- 특정 Infra Node에서만 Mount 실패
- Write·Read 실패
- Reclaim·정리 동작 미확인으로 데이터 삭제 위험 존재

이 상태에서는 Monitoring Stack을 적용해 실패 원인을 더 복잡하게 만들지 않는다.

## 5. 대상 Member Identity 고정

### 5.1 가장 먼저 확인할 값

```text
current-context
Cluster name
Stage
Node hostname·role·IP
VIP-A / VIP-B
Domain
StorageClass
Registry
External ETCD Endpoint
Monitoring Namespace
```

### 5.2 Cluster별 값 혼입 방지

Host·PRD Member·DEV Member는 다음 값이 다를 수 있다.

- ETCD Endpoint
- Certificate Secret과 Key 이름
- VIP-A·VIP-B
- Ingress Domain
- Cluster·Stage External Label
- StorageClass
- Registry Repository·Tag
- Node Selector·Taint
- Grafana Datasource
- KubeSphere external Monitoring Endpoint

Manifest가 적용됐다는 사실보다 **각 값이 현재 신규 Member Identity와 일치하는가**가 더 중요하다.

### 5.3 기록 양식

```text
대상 Member Cluster: __________________________
current-context: ______________________________
Stage: _______________________________________
VIP-A / VIP-B: _______________________________
Domain: ______________________________________
StorageClass: _________________________________
Registry: ____________________________________
External ETCD: ________________________________
확인 근거: ___________________________________
```

민감한 Endpoint 인증정보는 기록하지 않는다.

## 6. Preliminary Components

### 6.1 `monitoring` Namespace

Member custom Monitoring의 작업 경계다.

완료 증거:

- Namespace가 `Active`
- 과거 `kubesphere-monitoring-system`과 혼동하지 않음
- 이후 CR·PVC·Secret·Service·Ingress가 올바른 Namespace에 생성됨

### 6.2 ETCD Certificate Secret

External ETCD HTTPS Metric 접근에 필요한 인증 재료를 Prometheus에 제공한다.

확인할 것:

- Secret 존재
- Namespace = `monitoring`
- Type
- 필요한 Key 이름 존재
- 실제 ETCD Certificate와 대응
- Secret 원문 미출력
- 파일·Key 권한과 전달 경로 승인

```text
Secret 이름이 같음
≠ 올바른 Cluster Certificate
```

### 6.3 Grafana·Prometheus·Alertmanager PVC

- StorageClass가 9/2 검증값과 일치한다.
- 요청 용량이 승인값과 Quota 안에 있다.
- PVC가 Bound된다.
- Pod가 실제 Mount한다.
- Node 배치와 NFS 접근이 정상이다.

Grafana PVC 하나만 보고 Prometheus·Alertmanager Storage를 자동 통과시키지 않는다.

### 6.4 Preliminary 완료 Gate

```text
monitoring Namespace Active
+ Secret 구조 정상
+ StorageClass 확정
+ 필요한 PVC 생성 가능
+ Registry 접근 가능
+ Infra Node 배치 조건 확인
=
CRD와 Monitoring Stack 적용 가능
```

---

# Part 2. Prometheus Operator와 DKS Monitoring

## 7. Prometheus Operator CRD

### 7.1 CRD가 먼저인 이유

DKS custom Stack은 다음 API Kind를 사용한다.

- Prometheus
- Alertmanager
- ServiceMonitor
- PodMonitor
- PrometheusRule
- ThanosRuler 등 Bundle에 포함된 Kind

CRD가 없으면 Kubernetes API가 객체 종류를 해석할 수 없다.

```text
CRD Applied
→ Names Accepted
→ Established
→ API Discovery 가능
→ Custom Resource 적용 가능
```

### 7.2 검증

- CRD 이름
- `Established=True`
- Version과 Served·Storage 상태
- 다른 Bundle Version과 충돌하지 않음
- Operator가 해당 CRD를 Watch할 준비가 됨

```bash
kubectl get crd | grep monitoring.coreos.com
kubectl describe crd <crd-name>
```

### 7.3 흔한 실패

```text
CRD Apply 명령 성공
≠ Established 완료

과거 CRD Version 잔존
→ 새 Manifest Schema와 불일치 가능

Operator 먼저 기동
→ 필요한 CRD가 없어 반복 실패
```

## 8. DKS custom kube-prometheus-stack

### 8.1 핵심 구성요소

- Prometheus Operator
- Prometheus
- Alertmanager
- Grafana
- kube-state-metrics
- Node Exporter
- Kubernetes Component ServiceMonitor
- PrometheusRule
- 필요한 Adapter·Exporter

정확한 목록은 현재 Bundle과 Manifest를 기준으로 확인한다.

### 8.2 Cluster Identity

```yaml
externalLabels:
  cluster: <current-member-cluster>
  stage: <current-stage>
```

이 Label은 Multi-Cluster Metric에서 출처를 구분한다. 다른 Cluster 이름을 복사하면 Pod는 Running이어도 Dashboard·Alert·Query가 잘못된 Identity를 표시한다.

### 8.3 Storage

확인할 것:

- Prometheus Retention과 PVC 용량
- StorageClass
- Alertmanager PVC
- Grafana PVC
- Volume Mount
- PVC·PV·Node·NFS 경로

```text
PVC Bound
≠ Prometheus가 정상 기동·데이터 기록
```

### 8.4 Node 배치

- `nodeSelector`
- `tolerations`
- `affinity` 또는 anti-affinity
- Replica 수
- 실제 Pod `NODE`
- Infra Node의 Taint

```text
Manifest에 nodeSelector 존재
+ Toleration 존재
+ 실제 Pod가 대상 Infra Node
=
배치 정책 적용 확인
```

### 8.5 Registry와 Image

- Registry FQDN
- Project·Repository
- Image Tag
- CA Trust
- Image Pull Secret 필요 여부
- Node에서 Pull 가능 여부

Image가 Pull되지 않으면 Monitoring 설정값을 먼저 바꾸지 않고 Pod Event를 확인한다.

### 8.6 Stack 적용 후 검증

#### Kubernetes 객체

- Deployment·StatefulSet·DaemonSet
- Pod Ready·Restart
- Service·Endpoint
- PVC·PV
- CR 상태
- Event

#### 기능

- Prometheus Web/API
- Active Target
- Rule Load
- Alertmanager Cluster·Config
- Grafana Login·Datasource·Query
- Node·Kubernetes Metric 수집

### 8.7 과잉 판정 방지

```text
Operator Running
≠ Prometheus CR Ready

Prometheus Pod Running
≠ Target UP

Grafana Pod Running
≠ Datasource 정상

Rule Object 존재
≠ Prometheus가 Rule Load

Alertmanager Pod Running
≠ Route·Receiver·알림 전달 정상
```

## 9. Monitoring Ingress와 VIP-B

### 9.1 외부 요청 경로

```text
사용자 또는 운영자
→ DNS / Monitoring FQDN
→ Member VIP-B
→ Router
→ ingress-nginx-controller
→ Monitoring Ingress
→ Service
→ Pod
```

### 9.2 확인할 값

- Hostname
- PRD/DEV·현재 Member Domain
- Path
- Service Name·Port
- Ingress Class
- TLS 방식
- Address
- DNS 해석
- VIP-B Backend
- Source 접근 조건

Host Cluster Domain이나 다른 Member VIP를 넣지 않는다.

### 9.3 기능 검증

- DNS가 올바른 VIP-B로 해석된다.
- TCP 80/443 연결이 된다.
- Ingress Address가 Router와 일치한다.
- Backend Service·Endpoint가 존재한다.
- Prometheus·Grafana·Alertmanager UI 또는 API가 기대 상태를 반환한다.
- 인증·권한 정책이 의도와 일치한다.

## 10. External ETCD Monitoring

### 10.1 구조

Member의 Kubernetes ETCD가 External Node에서 실행되는 경우 Kubernetes Pod Selector로 직접 발견되지 않는다. Kubernetes 객체로 Endpoint를 표현하고 ServiceMonitor가 이를 Scrape하도록 연결한다.

```text
실제 ETCD Node IP:Port
→ Kubernetes Endpoints / EndpointSlice
→ Headless Service
→ ServiceMonitor
→ Prometheus
→ /metrics HTTPS
→ Target UP
```

### 10.2 Endpoints

확인할 것:

- 현재 Member의 실제 ETCD Node IP
- Port·Name
- Address 개수
- 다른 Cluster IP 혼입 여부
- TLS Server Name 또는 Metric Path 요구

### 10.3 Service

- Selector 없는 Headless 또는 승인된 구조
- Port Name이 ServiceMonitor와 일치
- Endpoint 연결
- Namespace 일치

### 10.4 ServiceMonitor

- Namespace Selector
- Service Label Selector
- Port Name
- Scheme = HTTPS 등 실제값
- TLS Config
- Secret Key 참조
- Scrape Interval

### 10.5 최종 Target

```text
Service·Endpoints 존재
≠ Scrape 성공
```

Prometheus Target에서 확인한다.

- Health = `UP`
- Last Scrape
- Scrape Duration
- Error 없음
- Endpoint가 현재 Member ETCD
- Metric이 실제로 Query됨

### 10.6 Target Down 분기

| 증상 | 첫 확인 |
|---|---|
| No Endpoint | Endpoints·Service Label |
| Connection refused | ETCD Metric Listen·Port |
| Timeout | Network·Route·Firewall |
| x509 | CA·Client Certificate·Server Name |
| 403/401 | ETCD Auth·Certificate |
| Wrong Cluster Metric | Endpoints IP·External Label |

## 11. Monitoring 복붙 오적용 방지

### 11.1 실제 학습 사례

과거 DEV Member에서 다음과 같은 값 혼입이 발생했다.

- Host ETCD Endpoint를 Member에 적용
- Grafana Datasource Namespace를 잘못 적용
- 일부 Pod·PVC·Ingress는 정상
- ETCD Target과 Grafana Data는 실패

### 11.2 핵심 교훈

```text
리소스 개수가 많이 Running
보다
각 Endpoint·Datasource·Label이 현재 Cluster Identity와 일치
가 더 강한 정상 판정
```

### 11.3 Manifest 검토표

| 값 | 현재 Member 근거 | 다른 Cluster 값 혼입 여부 |
|---|---|---|
| externalLabels.cluster | Cluster 카탈로그·context |  |
| externalLabels.stage | 승인 Stage |  |
| ETCD Endpoints | 실제 Member ETCD |  |
| StorageClass | 9/2 검증 |  |
| Ingress Host | 현재 Member Domain |  |
| Grafana Datasource | `monitoring` Service |  |
| Registry·Tag | 현재 Bundle |  |
| Node Selector | 현재 Node Role |  |

---

# Part 3. Grafana와 Monitoring 인수

## 12. Grafana Datasource

### 12.1 용도

Grafana가 Metric Query를 보낼 Prometheus Service를 지정한다.

기존 구조 예:

```text
Grafana Datasource
→ http://prometheus-k8s.monitoring.svc:9090
```

실제 Service 이름·Namespace는 현재 Manifest에서 확인한다.

### 12.2 KubeSphere external Monitoring Endpoint와 구분

```text
Grafana Datasource
→ Grafana가 Query할 Prometheus Service

KubeSphere external Monitoring Endpoint
→ KubeSphere가 외부 Monitoring으로 사용할 Prometheus Service
```

기존 문서 구조에서는 다음처럼 서로 다른 Service를 사용할 수 있다.

```text
prometheus-k8s.monitoring.svc
vs
prometheus-operated.monitoring.svc
```

이름을 암기해 서로 바꾸지 않고 실제 Service·Port·목적을 확인한다.

### 12.3 검증

- Datasource URL
- Access Mode
- Save & Test 성공
- 간단 Query 결과
- Cluster Label
- Dashboard Data 시간 범위
- 다른 Cluster Metric 혼입 없음

## 13. Dashboard

### 13.1 Dashboard 추가

- 승인된 JSON 또는 ConfigMap
- UID·Title 중복
- Datasource 참조
- Variable·Cluster Label
- Version
- Import 결과

### 13.2 기능 검증

- Node·Pod·Cluster Metric 표시
- 현재 Member 이름 표시
- 최근 Data 존재
- Panel Error 없음
- Datasource Query 성공
- 실제 Kubernetes 상태와 대략 일치

### 13.3 과잉 판정 방지

```text
Dashboard 화면 열림
≠ Panel Query 정상

일부 Panel 값 있음
≠ 현재 Member Metric

Datasource Save & Test 성공
≠ 모든 Dashboard Variable 정상
```

## 14. Monitoring 최종 Gate

다음이 모두 충족되어야 Member KubeSphere 설치로 진행한다.

1. Monitoring Namespace·Secret·PVC 정상
2. Prometheus CRD Established
3. Operator·Prometheus·Alertmanager·Grafana 정상
4. PVC Mount·Storage 사용 정상
5. Node 배치 정책 정상
6. Prometheus 주요 Target 정상
7. External ETCD Target `UP`
8. Rule Load 정상
9. Grafana Datasource·Query 정상
10. Monitoring Ingress·VIP-B 정상
11. Cluster·Stage Label 현재 Member와 일치
12. 민감정보 노출 없음

### 14.1 중단 기준

- ETCD Target Down 원인 미확정
- Grafana가 다른 Cluster Prometheus를 참조
- PVC Mount 실패
- Registry Image Pull 실패
- CRD Version 충돌
- 주요 Monitoring Pod 반복 재시작
- Ingress가 다른 Member Domain/VIP 사용
- External Label 잘못 적용

---

# Part 4. Member KubeSphere

## 15. Member installer와 ClusterConfiguration

### 15.1 두 파일의 역할

```text
kubesphere-installer.yaml
→ Installer CRD·RBAC·Deployment와 실행기

cluster-configure.yaml / ClusterConfiguration
→ 실제 KubeSphere 기능·환경·Role·Monitoring·Storage·Registry 설정
```

### 15.2 Member 핵심값

- 대상 Member context
- StorageClass
- Registry·Image
- External ETCD
- Monitoring Type = external 등 승인값
- External Prometheus Endpoint
- `multicluster.clusterRole = member`
- Console·Ingress
- Node Selector·Toleration
- Module Enable·Disable
- Host 연결에 필요한 보호된 값

### 15.3 Host와 Member 차이

| 항목 | Host | 신규 Member |
|---|---|---|
| 역할 | 중앙 Multi-Cluster 관리 | 사용자 Workload·Member 실행 |
| clusterRole | `host` | `member` |
| Monitoring | Host 기준 구성 | DKS custom external Monitoring 사용 |
| Join | Member를 받음 | 기존 Host에 Join |
| 이번 출장 | 재설치 없음 | 신규 설치 대상 |

Host Manifest를 복사해 `clusterRole`만 바꾸는 방식으로 적용하지 않는다.

## 16. Installer 로그

### 16.1 먼저 구분할 것

```text
ks-installer Pod 자체가 Pending·Crash인가?
vs
Installer는 Running이지만 내부 Task가 실패하는가?
```

### 16.2 Task 범주

- common
- monitoring
- multicluster
- network
- openpitrix
- devops
- logging·events·alerting 등 Bundle 구성

정확한 Task는 현재 로그를 기준으로 본다.

### 16.3 실패 시 확인

| 실패 범주 | 먼저 확인 |
|---|---|
| Pod Pending | Node Selector·Taint·PVC·Image |
| ImagePullBackOff | Registry·Tag·CA·Secret |
| CRD not found | CRD 적용·Established |
| Monitoring Task | External Endpoint·Service·CRD·PVC |
| Multicluster Task | Role·Join 설정·보호된 값 |
| Timeout | API·Network·Webhook·Resource |

### 16.4 완료 증거

- Installer Task 성공
- KubeSphere 주요 Deployment·StatefulSet Ready
- Console/API 접근
- `clusterRole=member`
- External Monitoring Endpoint 정상
- Storage PVC 정상
- Platform Workload 배치 정상
- Installer 종료·Replica 정책이 Manual과 일치

## 17. Platform Workload 배치

### 17.1 확인 요소

- Node Label
- Node Taint
- Workload Node Selector
- Toleration
- Replica 수
- 실제 Pod `NODE`
- Pod Disruption·Anti-affinity

### 17.2 완료 판단

```text
Manifest에 배치 조건 있음
+ Scheduler Event 정상
+ 실제 새 Pod가 Infra Node에 배치
+ Replica가 역할별 Node에 분산
=
DKS 배치 정책 반영
```

### 17.3 Pending 분기

```text
원인을 KubeSphere 자체 오류로 단정하지 않음
→ nodeSelector와 실제 Label
→ Taint와 Toleration
→ PVC Binding
→ Resource Request
→ Scheduler Event
```

## 18. Member 자체 Pre-Join 검증

Host Join 전에 Member가 자체적으로 정상이어야 한다.

### 18.1 Kubernetes

- API·Node·Control Plane·CNI·DNS
- Ingress Controller
- Event에 미해결 Critical Error 없음

### 18.2 Storage

- Trident·Backend·StorageClass
- Monitoring·KubeSphere PVC Mount
- Write·Read

### 18.3 Monitoring

- Prometheus·Alertmanager·Grafana
- External ETCD Target `UP`
- Datasource·Dashboard
- Ingress·HTTP

### 18.4 KubeSphere

- Installer Task
- Console·API
- 주요 Platform Workload
- `clusterRole=member`
- External Monitoring 연결
- Infra 배치

### 18.5 Network·Identity

- Member VIP-A·VIP-B
- Domain
- Existing Host와 필요한 통신
- DNS·Firewall
- Cluster Name·Stage·External Label

### 18.6 Pre-Join Gate

위 항목 중 하나라도 Member 자체 장애가 남아 있으면 Join으로 문제를 덮지 않는다.

---

# Part 5. 기존 Host Join

## 19. Join의 의미

Host Join은 Console 목록에 이름을 추가하는 UI 작업이 아니다.

```text
Member KubeSphere = member로 준비
+ 기존 Host = host로 정상
+ 필요한 인증정보를 안전하게 공유
+ Host↔Member Network·DNS·API 통신
+ Member Agent·연결 Component 정상
=
Host가 신규 Member를 관리·관측할 수 있는 Multi-Cluster 연결
```

## 20. Join 전 기존 Host 확인

기존 Host에는 변경을 최소화하고 다음을 조회한다.

- Host Console·API 접근
- Host `clusterRole=host`
- 기존 PRD·DEV Member 상태
- 신규 Member 이름 중복 여부
- Join 대상 Workspace·Cluster 관리 권한
- Host Resource 상태
- Multi-Cluster Component 상태
- Host↔신규 Member DNS·Network·Firewall
- Join 승인자와 보호된 값 전달 방법

기존 Host에 문제가 있으면 신규 Member Join 실패와 분리한다.

## 21. 보호된 Join 정보

### 21.1 원칙

- Secret·JWT·kubeconfig 원문을 문서에 복사하지 않는다.
- 화면 공유 시 Masking한다.
- 승인된 전달 경로를 사용한다.
- 전달 대상과 유효시간을 확인한다.
- 사용 후 임시 파일·Clipboard·Shell History를 정리한다.
- 파일 권한은 최소화한다.

### 21.2 기록할 수 있는 정보

- 값의 종류
- 발급·확인 시각
- 전달자·수신자 역할
- 저장 위치가 아닌 승인된 관리체계
- 사용 성공 여부
- Rotation·폐기 필요 여부

## 22. Join 실행 흐름

실제 UI·명령·Manifest는 현재 Manual과 Host Console을 따른다.

```text
신규 Member Name·Role 확인
→ 기존 Host의 Add / Import / Join 경로 확인
→ 보호된 연결정보 준비
→ Join 적용
→ Member Agent·연결 Workload 생성
→ Host Console에서 Cluster 등록
→ 상태 전환 관찰
→ API·Resource·Monitoring 관리·관측 확인
```

### 22.1 이름과 Identity

- Cluster Name이 현재 Member와 일치
- PRD·DEV·Stage Tag 일치
- 기존 Cluster와 중복 없음
- 잘못된 과거 이름 사용 금지

### 22.2 Network

- Host에서 Member API 접근
- Member에서 Host 연결 Endpoint 접근
- DNS 해석
- TLS 인증
- 필요한 Port
- Proxy·Firewall 영향

### 22.3 Agent·Component

- Member Agent Pod
- Host 측 Multi-Cluster Component
- Registration 상태
- Log·Event
- Restart·Error

## 23. Join 완료 증거

```text
Host Console에 신규 Member 표시
+ Status 정상
+ Cluster Name·Stage 정확
+ Member Node·Namespace·Workload 조회 가능
+ Member KubeSphere 자체 Console·API 정상
+ Host에서 Member Monitoring 정보 확인 가능
+ Host-Member 연결 Component 정상
+ 기존 Member 영향 없음
+ 권한 경계 정상
```

### 23.1 단순 목록 표시를 넘어 확인할 것

- Node 수와 Role이 Member 실제 상태와 일치
- Namespace·Project 조회
- Workload 상태
- Monitoring Metric의 Cluster Label
- Host에서 선택한 Cluster가 올바름
- Member의 API·Network Error 없음
- 기존 PRD·DEV Member 상태 변화 없음

## 24. Join 실패 분기

### 24.1 Host Console에 Cluster가 안 보임

- Join 요청이 생성됐는가
- Cluster Name·Identity 중복
- Host 권한
- 보호된 값 유효성
- Host API·Component Log

### 24.2 Cluster는 보이지만 상태 이상

```text
Member 자체 정상인가?
→ Member Agent 정상인가?
→ Host→Member API 통신이 되는가?
→ DNS·TLS·Firewall은 정상인가?
→ 인증정보가 현재 Member 것인가?
```

### 24.3 Resource는 보이지만 Monitoring 없음

- Member external Monitoring 정상
- Cluster External Label
- Host가 참조하는 Metric Source
- Datasource·Endpoint
- Multi-Cluster Monitoring Component

### 24.4 기존 Member까지 영향

즉시 신규 Join 작업과 영향 관계를 확인하고, 추가 변경을 멈춘다. Host 공통 Component·Config 변경이 있었는지 비교한다.

---

# Part 6. 전체 구축 최종 인수

## 25. 8/31~9/3 구축 흐름 복원

```text
8/31
신규 Member VM·LB·Bastion·Node 실제값 확인
→ Pre-setting
→ Inventory·변수
→ Ansible 연결

9/1
Kubespray
→ API·Node·System Pod·CNI·DNS·ETCD·Runtime 검증

9/2
Snapshotter·Trident·Backend·StorageClass
→ PVC·PV
→ Pod Mount
→ Write·Read

9/3
Member Monitoring
→ Member KubeSphere
→ 기존 Host Join
→ Multi-Cluster 최종 인수
```

## 26. 기능별 인수 매트릭스

| 영역 | 확인 대상 | 최소 증거 | 판정 |
|---|---|---|---|
| VM·Node | 역할·CPU·Memory·Disk·NIC | 승인 설계·현재 출력 |  |
| Bastion | SSH·sudo·Bundle·Repo | 연결·Version |  |
| Inventory | Host·Group·VIP·CIDR·Domain | 기준본·대조표 |  |
| Kubespray | Task·Recap | 미해결 실패 없음 |  |
| Kubernetes API | VIP-A·readyz | API 응답 |  |
| Node | Ready·Role·Version | Node 출력 |  |
| CNI·DNS | Calico·CoreDNS | Pod·기능 테스트 |  |
| Storage | Backend·SC·PVC·Mount·RW | 단계별 증적 |  |
| Monitoring | Pod·Target·Rule·Datasource | ETCD UP·Query |  |
| Monitoring Ingress | DNS·VIP-B·HTTP | 응답·Backend |  |
| Member KubeSphere | Task·Console·API·Role | Member 기능 |  |
| 배치 | Infra Node·Toleration | 실제 Pod NODE |  |
| Host Join | Cluster 상태·Agent | Multi-Cluster 상태 |  |
| 회귀 | 기존 Host·Member | 영향 없음 |  |
| 보안 | Secret·Token·Key | 미노출·정리 |  |

## 27. 최종 완료 조건

### 27.1 신규 Member 자체

- Kubernetes API·Node·CNI·DNS 정상
- Storage Mount·Write/Read 정상
- Monitoring 주요 Component 정상
- External ETCD Target `UP`
- Grafana Datasource·Dashboard 정상
- Member KubeSphere Console·API 정상
- `clusterRole=member`
- Platform Workload 배치 정상
- 주요 Ingress·VIP-B 정상

### 27.2 기존 Host Join

- Host 접근·Role 정상
- 신규 Member Join 성공
- Host Console Status 정상
- Member Resource 조회·관리 가능
- Member Monitoring 관측 가능
- 기존 Member 영향 없음

### 27.3 인수·기록

- 환경 실제값과 기준본 차이 기록
- 실행 로그·검증 증적 위치 기록
- 미완료·Blocker 구분
- 보호된 값 정리
- 현지 담당자에게 문서 위치와 정상 기준 전달
- 9/4 철수 문서에 인계 항목 반영

## 28. 부분 완료·보류 판정

### Pass

모든 핵심 완료 조건을 통과하고 잔여 항목이 비차단적이다.

### Partial Pass

핵심 기능은 정상이나 문서 정리·부가 Dashboard·비차단 Q&A 등이 남았다. 남은 항목의 영향·담당자·기한이 명확해야 한다.

### Blocked

다음 중 하나라도 남으면 최종 완료로 선언하지 않는다.

- Kubernetes 기본 기능 비정상
- Storage Mount·Write/Read 실패
- External ETCD Target Down
- Member KubeSphere 핵심 Task 실패
- `clusterRole` 또는 Cluster Identity 오류
- Host Join 실패
- Host Console Member 상태 이상
- 기존 Cluster 영향 발생
- 보호된 값 노출·통제 미확정

## 29. 잔여 항목 기록

| 항목 | 현재 통과 지점 | 최초 실패·미확인 지점 | 영향 | 다음 확인 | 담당 영역 | 상태 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

`완료`, `비차단 잔여`, `차단`, `외부 확인`을 구분한다. 실패를 질문 목록으로만 남기고 완료 처리하지 않는다.

## 30. 최종 증적 패킷

### 30.1 포함할 것

- 대상 Member Identity·context 확인
- Node·System Pod·API 검증
- Storage Backend·SC·PVC·Mount·RW
- Monitoring Component·Target·Datasource
- KubeSphere Task·Workload·Console
- Host Join·Cluster 상태
- 기존 Cluster 회귀 확인
- 질문·결정·잔여 항목

### 30.2 포함하지 않을 것

- Secret Data
- Token
- Password
- Private Key
- kubeconfig 원문
- JWT
- 보호된 Join 값
- 인증서 원문

### 30.3 증적 파일 규칙

- 날짜·대상 Cluster·영역을 파일명에 표시
- Dynamic Pod 이름·시간이 현재 실행임을 명시
- Screenshot은 민감정보 Masking
- 참조 출력과 실제 실행 증적 구분
- 원본 로그와 요약 판단을 분리

---

# Part 7. 강사·교육생 학습과 훈련

## 31. 숙지 수준 분류

### A. 문서 없이 설명할 것

- [ ] Member Monitoring을 KubeSphere보다 먼저 구성하는 이유
- [ ] Namespace·Secret·PVC·CRD의 선후관계
- [ ] Prometheus CRD `Established`의 의미
- [ ] External Label이 Cluster별이어야 하는 이유
- [ ] Monitoring Ingress와 VIP-B 경로
- [ ] ETCD Endpoint→Service→ServiceMonitor→Target 관계
- [ ] Target `UP`이 최종 증거인 이유
- [ ] Grafana Datasource와 KubeSphere external Monitoring Endpoint 차이
- [ ] installer와 ClusterConfiguration 차이
- [ ] Member `clusterRole=member` 의미
- [ ] 기존 Host를 재설치하지 않는 이유
- [ ] Host Join이 Multi-Cluster에서 완성하는 것
- [ ] 목록 표시와 실제 Multi-Cluster 정상의 차이
- [ ] 8/31~9/3 전체 구축의 Gate

### B. 문서를 보며 정확히 수행·설명할 것

- [ ] Preliminary Components 적용·확인
- [ ] Secret Key 존재를 원문 노출 없이 확인
- [ ] CRD 적용·Established 확인
- [ ] custom Stack Manifest 핵심값 검토
- [ ] PVC·Pod·Node 배치 확인
- [ ] Monitoring Ingress·Service·Endpoint 확인
- [ ] ETCD Service·Endpoints·ServiceMonitor 확인
- [ ] Prometheus Target 확인
- [ ] Grafana Datasource·Dashboard 확인
- [ ] Member installer·ClusterConfiguration 검토
- [ ] Installer Task·Workload·Role 검증
- [ ] 기존 Host Join 절차와 상태 확인
- [ ] 최종 인수 매트릭스 작성

### C. 현장에서 반드시 다시 확인할 것

- 신규 Member Cluster Name·Stage·context
- Node·VIP·Domain
- StorageClass
- ETCD IP·Port·Certificate Key 이름
- Registry·Image Tag
- Monitoring PVC 용량
- Ingress FQDN
- Grafana·KubeSphere Prometheus Endpoint
- Join 대상 Host와 Cluster Name
- 보호된 값 전달 방식
- 기존 Host·Member 현재 상태
- 승인자·담당자·인계 대상

## 32. 자가점검

| 질문 | 상태 | 막힌 부분 | 돌아갈 문서 |
|---|---|---|---|
| Monitoring 전체 순서를 10분 안에 설명하는가? | 미평가 |  | 05-2 |
| CRD와 Custom Resource 선후를 설명하는가? | 미평가 |  | 05.2.1.2 |
| Cluster별 Identity 혼입 위험을 설명하는가? | 미평가 |  | Monitoring 사례 |
| ETCD Target Down 분기를 설명하는가? | 미평가 |  | 05.2.1.4 |
| 두 Prometheus Endpoint를 구분하는가? | 미평가 |  | 05-2 |
| Member installer Task를 읽는가? | 미평가 |  | 05.2.2 |
| `clusterRole=member`를 확인하는가? | 미평가 |  | 05.2.2 |
| Join 전 Member 자체 Gate를 설명하는가? | 미평가 |  | 이 문서 §18 |
| 기존 Host Join의 보호된 값 경계를 설명하는가? | 미평가 |  | 이 문서 §21 |
| Host Console 목록 이상으로 검증하는가? | 미평가 |  | 이 문서 §23 |
| 전체 구축 Pass·Partial·Blocked를 구분하는가? | 미평가 |  | 이 문서 §28 |

## 33. 직접 연습

### 연습 1 — Member 전체 순서 15분 설명

```text
Storage Gate
→ Preliminary Components
→ CRD
→ custom Monitoring
→ Ingress
→ ETCD Target
→ Grafana
→ Member KubeSphere
→ Pre-Join
→ Existing Host Join
→ Multi-Cluster
→ Final Acceptance
```

각 단계에서 다음을 말한다.

```text
왜 필요한가?
무엇을 입력하는가?
성공 증거는 무엇인가?
어디서 멈추는가?
```

### 연습 2 — Cluster 값 혼입 찾기

Host·PRD Member·DEV Member 자료에서 다음 값을 섞은 Manifest를 만들고 잘못된 항목을 찾는다.

```text
externalLabels.cluster
ETCD Endpoints
StorageClass
Ingress Host
Grafana Datasource
KubeSphere Monitoring Endpoint
clusterRole
```

### 연습 3 — ETCD Monitoring 그림

```text
ETCD Node
→ Endpoints
→ Service
→ ServiceMonitor
→ Prometheus
→ Target UP
→ Query
```

각 객체가 존재하지만 Target이 Down일 수 있는 이유를 설명한다.

### 연습 4 — Monitoring 실패 카드

```text
A. CRD 없음
B. Prometheus Pod Pending + PVC Pending
C. Pod Running + ETCD Target Down
D. Grafana 열림 + Datasource Error
E. Ingress 존재 + DNS 다른 VIP
```

첫 단절과 다음 확인을 고른다.

### 연습 5 — Installer 로그 카드

다음 실패를 분류한다.

```text
ImagePullBackOff
CRD not found
Monitoring endpoint timeout
clusterRole mismatch
Pod Pending on tainted Infra Node
```

### 연습 6 — Join Preflight

```text
Member Kubernetes:
Member Storage:
Member Monitoring:
Member KubeSphere:
Member Identity:
Existing Host:
Network/DNS/TLS:
Protected Join Data:
```

하나라도 미확정이면 어떤 영향이 있는지 말한다.

### 연습 7 — Multi-Cluster 판정

Host Console에서 Cluster 이름만 보이는 화면과 다음 증적을 비교한다.

- Status
- Node·Namespace·Workload
- Monitoring Metric
- Agent Pod
- API Connectivity
- 기존 Member 상태

목록 표시만으로 완료할 수 없는 이유를 설명한다.

### 연습 8 — 최종 인수 매트릭스

8/31~9/3의 실제 또는 가상 증적을 기능별 인수 표에 넣고 Pass·Partial·Blocked를 판정한다.

## 34. 대표 문제 상황

### 사례 1 — Monitoring Pod 정상, ETCD Target Down

```text
확인된 사실
→ Stack은 기동
→ ETCD Scrape만 실패

다음 확인
→ Endpoints가 현재 Member ETCD IP인가?
```

### 사례 2 — Grafana 열림, Data 없음

```text
UI 접속과 Datasource 성공 분리
→ Datasource URL
→ Prometheus Service·Endpoint
→ Save & Test
→ Query
→ Cluster Label
```

### 사례 3 — KubeSphere Monitoring Task 실패

```text
Storage PVC 실패인가?
→ CRD·Endpoint·Service 실패인가?
→ Installer 내부 Task인가?
```

### 사례 4 — KubeSphere Pod Pending

```text
Node Selector
→ Node Label
→ Taint·Toleration
→ PVC
→ Resource Request
→ Scheduler Event
```

### 사례 5 — Host Join 후 Cluster 상태 Error

```text
Member 자체 정상
→ Member Agent
→ Host→Member API
→ DNS·Firewall·TLS
→ Join Credential
→ Host Component
```

### 사례 6 — Host Join 후 Monitoring만 안 보임

```text
Member external Monitoring 정상
→ Cluster Label
→ Prometheus Endpoint
→ Host Multi-Cluster Monitoring 경로
```

### 사례 7 — 신규 Join 후 기존 Member 상태도 이상

추가 변경을 중단한다. Host 공통 Component·Config가 바뀌었는지 확인하고 영향 범위를 우선 고정한다.

## 35. 예상 질문

| 예상 질문 | 답변 핵심 | 현재 답변 가능 여부 |
|---|---|---|
| Member Monitoring을 왜 KubeSphere 전에 설치하나요? | DKS external Monitoring 선행 설계 | 미평가 |
| PVC Bound면 Monitoring Storage는 정상 아닌가요? | Pod Mount·데이터 사용 별도 | 미평가 |
| CRD가 왜 먼저 필요한가요? | API가 Custom Resource Kind를 알아야 함 | 미평가 |
| ETCD Service가 있는데 Target은 왜 Down인가요? | Service 존재와 TLS Scrape 성공은 별도 | 미평가 |
| Grafana와 KubeSphere가 같은 Prometheus URL을 쓰지 않나요? | 소비 목적과 Service가 다를 수 있음 | 미평가 |
| Host Manifest를 Member에 복사하면 안 되나요? | Role·ETCD·Domain·Monitoring·Identity가 다름 | 미평가 |
| Console이 열리면 Member 설치가 끝난 건가요? | Task·Monitoring·Storage·Role·배치 별도 | 미평가 |
| 기존 Host도 다시 설치해야 Join되나요? | 기존 Host는 완료 상태, Join 대상만 확인 | 미평가 |
| Host Console에 보이면 Join 성공 아닌가요? | Resource·Monitoring·Agent·API까지 확인 | 미평가 |
| Join Secret을 교육 자료에 적어두면 안 되나요? | 보호된 값은 승인된 관리체계로만 전달 | 미평가 |
| 9/3에 완료하지 못하면 9/4에 이어서 하면 되나요? | 9/4는 철수일, 기술 Buffer가 아님 | 미평가 |

## 36. 현장 기록 양식

```text
작업일: 2026-09-03
신규 Member Cluster/context: __________________________
기존 Host Cluster: ___________________________________

Storage Gate 재확인: _________________________________
Preliminary Components: ______________________________
CRD Established: _____________________________________
Prometheus Stack: ____________________________________
Monitoring PVC·Mount: ________________________________
Monitoring Ingress: __________________________________
External ETCD Target: ________________________________
Grafana Datasource·Dashboard: _________________________
Member KubeSphere Task: ______________________________
clusterRole=member: __________________________________
Platform Workload 배치: ______________________________
Pre-Join Gate: ________________________________________
Existing Host Join: __________________________________
Host Console Status: _________________________________
Multi-Cluster 관리·관측: _____________________________
기존 Cluster 회귀 확인: ______________________________

최종 판정: PASS / PARTIAL / BLOCKED
잔여 항목: ___________________________________________
담당 영역·다음 조치: _________________________________
보호된 값 정리 완료: _________________________________
증적 위치: ___________________________________________
```

## 37. 9/3 완료 기준

- [ ] 9/2 Storage Gate를 다시 확인했다.
- [ ] 대상 Member Identity와 실제값을 다른 Cluster와 구분했다.
- [ ] Monitoring Namespace·Secret·PVC 선행조건이 정상이다.
- [ ] Prometheus Operator CRD가 `Established`다.
- [ ] DKS custom Monitoring Component가 정상이다.
- [ ] Monitoring PVC가 실제 Mount되고 사용된다.
- [ ] Prometheus 주요 Target과 External ETCD Target이 `UP`이다.
- [ ] Cluster·Stage External Label이 현재 Member와 일치한다.
- [ ] Grafana Datasource·Query·Dashboard가 정상이다.
- [ ] Monitoring Ingress·VIP-B·HTTP가 정상이다.
- [ ] Member KubeSphere Installer Task가 성공했다.
- [ ] Member ClusterConfiguration의 Storage·Registry·ETCD·Monitoring 값이 정확하다.
- [ ] `multicluster.clusterRole=member`다.
- [ ] KubeSphere Platform Workload가 DKS Infra 배치 정책을 따른다.
- [ ] Member 자체 Pre-Join Gate를 통과했다.
- [ ] 기존 Host를 재설치·재구성하지 않았다.
- [ ] 승인된 방식으로 기존 Host Join을 완료했다.
- [ ] Host Console에서 신규 Member Status가 정상이다.
- [ ] Host에서 Member Resource·Monitoring 관리·관측이 가능하다.
- [ ] 기존 Host·PRD·DEV Member에 회귀 영향이 없다.
- [ ] Secret·Token·JWT·kubeconfig·Private Key 원문을 노출하지 않았다.
- [ ] 8/31~9/3 기능별 인수 매트릭스를 완성했다.
- [ ] Pass·Partial·Blocked를 증거로 판정했다.
- [ ] 잔여 항목의 영향·담당자·다음 조치를 기록했다.
- [ ] 9/4 철수 전 인계·증적·접근 정리 항목을 확정했다.

## 38. 9/4와 연결

9/4는 기술 작업 Buffer가 아니다. 9/3 종료 시점에 기술 판정을 확정하고, 9/4에는 다음만 수행한다.

```text
현장 일정 정리
→ 증적·문서·잔여 항목 인계
→ 보호된 값·임시 파일·접근 정리
→ 현지 담당자 확인
→ 철수 준비와 이동
```

관련 문서: [[2026-09-04 현장 정리 및 철수|2026-09-04 현장 정리 및 철수]]
