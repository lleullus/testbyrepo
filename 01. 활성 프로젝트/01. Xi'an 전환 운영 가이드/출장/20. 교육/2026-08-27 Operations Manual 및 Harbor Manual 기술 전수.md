---
title: "2026-08-27 Operations Manual 및 Harbor Manual 기술 전수"
status: current
doc_type: training-note
scope: "2026-08-27 Operations Manual 2.1~2.5와 Harbor Manual 3.1~3.3 기술 전수, 강사 시연·판정·안전 경계"
created: "2026-08-15"
updated: "2026-08-21"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획]]"
---

# 2026-08-27 Operations Manual 및 Harbor Manual 기술 전수

> [!important] 이 문서의 역할
> 8/27 오전에는 최종 배포 Manual의 `2.1~2.5 Operations Manual`, 오후에는 `3.1~3.3 Harbor Manual`을 기술 전수한다. 이 문서는 각 절차를 짧게 소개하는 요약본이 아니라, **반복 운영과 고위험 변경의 목적·선행조건·입력·영향·검증·중단·복구 경계를 강사가 충분한 깊이로 설명하고, 교육생이 해당 요청에서 어느 Manual을 찾아야 하는지 판정하도록 만드는 고밀도 학습·진행 기준**이다.

> [!warning] 실제 실행 경계
> Worker 추가, taint·label 변경, Native API 노출, API Server 인증서 갱신, Harbor 재설치는 서비스 영향이 있는 변경이다. 교육 당일 기본 방식은 기존 정상 환경 조회, Manual 워크스루, 마스킹된 출력, 승인된 격리 실습이다. 대상·승인·백업·복구·중단 기준이 확인되지 않은 상태에서는 운영 환경에 적용하지 않는다.

## 1. 8/27 확정 범위

### 오전 — 2. Operations Manual

| Manual | 주제 | 교육 후 교육생이 판단할 것 |
|---|---|---|
| 2.1 | Adding a worker node to cluster using kubespray | VM·Pre-setting·Inventory·scale.yml·검증·정리의 연결 |
| 2.2 | Add taint and node-label when adding node | Node 배치 경계와 Pod의 nodeSelector·toleration 관계 |
| 2.3 | DKS FAQ | 반복 요청의 시작 문서와 담당 영역 경계 |
| 2.4 | Utilizing the Kubernetes Native API | Service·Ingress·API Server·RBAC·인증·Source 제한의 연결 |
| 2.5 | Renewing API Server Certificates | 백업·Master one-by-one·Static Pod·kubeconfig·KubeSphere 재연결 |

### 오후 — 3. Harbor Manual

| Manual | 주제 | 교육 후 교육생이 판단할 것 |
|---|---|---|
| 3.1 | SCS Harbor Installation | Docker·offline installer·인증서·harbor.yml·설치·검증 흐름 |
| 3.2 | Create a project | 신청·Private Project·Quota·완료 증거 |
| 3.3 | Managing Users | ProjectAdmin·Developer 권한과 멤버 변경 |

이날의 핵심 질문은 다음이다.

> **운영 요청을 받았을 때 무엇을 변경하고, 어떤 전제와 증거가 있어야 하며, 어디에서 멈추거나 다른 담당자에게 넘겨야 하는가?**

## 2. 하루 전체 이야기

```text
운영 요청 접수
→ 요청 유형과 대상 Cluster·Node·서비스 확인
→ 적절한 Operations Manual 선택
→ 변경 전 현재 상태·Inventory·백업·영향 확인
→ 승인된 절차를 단계별 실행 또는 워크스루
→ Node·Pod·API·인증서·권한 등 기능 검증
→ 운영 경계와 복구 위치 기록

오후
→ Harbor가 설치되는 기반 이해
→ Private Registry의 인증서·데이터·서비스 검증
→ Project 생성
→ 사용자와 Role 관리
→ 이후 User Manual의 Image Push/Pull 흐름으로 연결
```

### 반복해서 구분할 것

```text
Playbook 성공
≠ 새 Node의 Workload·Storage 사용 검증 완료

Node에 label이 있다
≠ 원하는 Pod가 그 Node에 배치된다

Service와 Ingress가 있다
≠ Native API가 안전하고 필요한 권한으로 동작한다

인증서 파일이 갱신됐다
≠ 실행 중인 Control Plane과 모든 kubeconfig가 새 인증서를 사용한다

Harbor Container가 Running이다
≠ HTTPS·Registry API·로그인·Push/Pull·데이터 영속성이 정상이다

Harbor Project가 존재한다
≠ 사용자가 올바른 Role로 실제 Push/Pull할 수 있다
```

## 3. 권장 진행 블록

| 블록 | 범위 | 방식 | 완료 기준 |
|---|---|---|---|
| A | 2.1 Worker 추가 | Runbook 워크스루 + Inventory 판독 | 새 Node 추가의 시작·끝·검증을 설명 |
| B | 2.2 taint·label | 개념 + YAML 비교 + 배치 판정 | Node와 Pod 양쪽 조건을 연결 |
| C | 2.3 FAQ | 요청 카드 분류 | 올바른 Manual·담당 영역 선택 |
| D | 2.4 Native API | 구조도 + RBAC·접근통제 워크스루 | 경로·인증·권한·노출 경계 설명 |
| E | 2.5 인증서 갱신 | one-by-one 시나리오·중단 Gate | Master별 검증 후 다음 Node 진행 원칙 설명 |
| F | 3.1 Harbor 설치 | 구성·파일·서비스·검증 워크스루 | 설치 전제와 실제 정상 증거 설명 |
| G | 3.2~3.3 Project·User | UI 시연·역할 비교 | Private·Quota·Role을 신청과 연결 |
| H | 통합 | 교육생 Teach-back | 요청→Manual→선행조건→검증→경계 연결 |

## 4. 기준 Manual

### Operations Manual

1. [[50. 운영/05. Operations Manual/01. Adding a worker node using kubespray|2.1 Adding a worker node to cluster using kubespray]]
2. [[50. 운영/05. Operations Manual/02. Add taint and node-label when adding node|2.2 Add taint and node-label when adding node]]
3. [[50. 운영/05. Operations Manual/03. DKS FAQ|2.3 DKS FAQ]]
4. [[50. 운영/05. Operations Manual/05. Utilizing the Kubernetes Native API|2.4 Utilizing the Kubernetes Native API]]
5. [[50. 운영/05. Operations Manual/06. Renewing API Server Certificates|2.5 Renewing API Server Certificates]]

### Harbor Manual

1. [[50. 운영/06. Harbor Manual/01. Harbor Installation|3.1 SCS Harbor Installation]]
2. [[50. 운영/06. Harbor Manual/02. Create a project|3.2 Create a project]]
3. [[50. 운영/06. Harbor Manual/03. Managing Users|3.3 Managing Users]]

`Failure response training`과 Dashboard 복구 문서는 Obsidian에 남아 있지만 이번 최종 Operations Manual 2.1~2.5에는 포함하지 않는다. 기술 배경이 필요할 때 참고할 수 있으나 교육 목차를 임의로 늘리지 않는다.

---

# Part 1. Operations Manual

## 5. 2.1 Adding a worker node to cluster using kubespray

### 5.1 이 절차의 목적

기존 Kubernetes Cluster에 승인된 Worker Node를 추가하고, Kubernetes 등록뿐 아니라 역할·Runtime·System Pod·Workload·Storage 사용까지 확인하여 운영 가능한 Node로 인수한다.

```text
신규 VM 확보
→ Node Pre-setting
→ Kubespray Inventory 추가
→ scale.yml 실행
→ Node Ready·Version·Runtime 확인
→ System Pod 확인
→ Workload 배치 테스트
→ PVC Mount 테스트
→ Inventory 기준본 정리
```

### 5.2 시작 전에 확정할 것

- 대상 Cluster와 Bastion
- 신규 VM hostname·IP·역할
- OS·CPU·Memory·Disk·Mount
- 관리 NIC와 Storage NIC
- 승인된 Node label·taint 정책
- Bastion `/etc/hosts`
- `dspaas` 계정·SSH·passwordless sudo
- OS Repository와 필수 Package
- Swap 비활성화
- NFS·Storage Client 도구
- Root CA 신뢰
- Kubespray bundle 경로와 Version
- Inventory 기준본과 백업
- NetApp Storage ACL·Export policy 필요 여부
- 변경 승인·작업 시간·중단·복구 기준

### 5.3 Node Pre-setting 범주

| 범주 | 확인할 것 | 완료 증거 |
|---|---|---|
| 계정 | `dspaas`, group, sudo | `sudo -n` 성공 |
| SSH | Bastion 공개키·Host key | passwordless 연결 |
| Repository | 실제 승인 URL | Package 조회·설치 가능 |
| Package | Kubernetes·NFS 전제 | Package 목록·Version |
| Swap | 비활성화 | 현재 상태와 fstab 일치 |
| CA | 승인된 Root CA | Registry·Repository TLS 정상 |
| Hostname/DNS | Inventory와 일치 | `hostname`, 이름 해석 |
| Disk/Mount | 역할별 경로 | `lsblk`, `findmnt`, fstab |
| Kernel/Network | Kubespray 전제 | sysctl·module·Route 확인 |

### 5.4 Inventory를 설계 변경으로 본다

`hosts.yaml`에 한 줄을 더하는 작업이 아니라 다음을 결정한다.

- Node의 관리 IP
- Kubernetes가 사용할 Internal IP
- 어느 Group에 속하는가
- Worker 역할 label
- 추가 team label
- taint 여부
- `kube_node` 포함 여부
- scale 대상

```text
all.hosts
→ Node identity와 IP

children.worker_node 또는 별도 group
→ 역할·label·taint

kube_node
→ Kubernetes Worker 집합
```

기존 Xi'an Inventory 예시는 구조 참고용이다. 신규 Node의 IP·hostname·Group을 그대로 복사하지 않는다.

### 5.5 scale.yml 실행 전 Gate

- Inventory YAML 문법이 정상이다.
- 새 Node가 기존 Group에 중복 등록되지 않았다.
- `ansible_host`, `ip`, `access_ip`가 실제 VM과 일치한다.
- Bastion에서 대상 Node에 SSH·sudo가 된다.
- 기존 Node가 의도치 않게 `--limit`에 포함되지 않는다.
- Inventory와 변수 파일 백업이 있다.
- Node Pre-setting의 미완료 항목이 없다.

### 5.6 실행과 로그 판독

실제 명령은 Manual에서 확인한다. 교육에서는 명령 문자열보다 다음을 먼저 본다.

```text
어느 Inventory인가?
어느 Cluster인가?
--limit 대상은 무엇인가?
어느 Host·Task에서 FAILED 또는 UNREACHABLE인가?
recap에서 failed·unreachable은 몇 개인가?
```

실패 시 전체 Cluster를 재설치하지 않는다. 최초 실패 Host·Task와 정상 Node의 차이를 확인한다.

### 5.7 Node 등록 후 검증

#### Kubernetes 등록

- Node 이름
- `Ready`
- Role·label
- Internal IP
- Kubernetes Version
- OS·Kernel
- Container Runtime

#### System Pod

- `calico-node`
- `kube-proxy`
- CSI Node Plugin
- Node별 DaemonSet
- Restart와 Event

#### Workload 배치

- 승인된 테스트 Deployment가 새 Node에 배치되는가
- Node selector가 실제 label과 일치하는가
- taint가 있으면 toleration이 있는가
- Pod가 `Running`과 `Ready`인가

#### Storage

- 대상 StorageClass 확인
- Test PVC가 Bound되는가
- 새 Node에서 Pod가 실제 Mount되는가
- Container Write·Read가 되는가

### 5.8 완료 판단

```text
scale.yml 성공
+ 새 Node Ready
+ label·taint 정상
+ Runtime·System Pod 정상
+ 테스트 Workload 배치 성공
+ PVC Mount·Write/Read 성공
+ Inventory 기준본 정리
=
운영 가능한 Worker Node 추가 완료
```

### 5.9 중단·복구 기준

- 잘못된 Cluster Inventory를 열었음
- 실제 VM IP·hostname과 Inventory 불일치
- 디스크 역할이 승인 설계와 다름
- SSH·sudo·Repository 미완료
- 기존 Node가 의도치 않게 변경 대상에 포함
- Node는 Ready지만 CNI·CSI·kube-proxy가 비정상
- 특정 Node에서만 NFS Mount 실패

복구는 임의 Node 삭제가 아니라 실패 단계에 따라 Inventory 원복, Pre-setting 수정, 제한 재실행, Node 상태 정리 절차를 선택한다.

## 6. 2.2 Add taint and node-label when adding node

### 6.1 목적

특정 팀 또는 Workload를 지정된 Worker Node에만 배치하고 일반 Pod의 우발적 스케줄링을 막는다.

### 6.2 네 요소를 함께 본다

```text
Node label
→ 어떤 속성의 Node인가

Node taint
→ 어떤 Pod를 기본적으로 거부하는가

Pod nodeSelector / affinity
→ 어느 Node를 선택하는가

Pod toleration
→ 해당 taint를 허용하는가
```

### 6.3 label과 taint의 차이

| 항목 | 위치 | 역할 | 단독으로 보장하지 않는 것 |
|---|---|---|---|
| label | Node | Node 분류·선택 | 다른 Pod의 접근 거부 |
| taint | Node | 허용되지 않은 Pod 배제 | 원하는 Node 선택 |
| nodeSelector | Pod | label이 맞는 Node 선택 | taint 통과 |
| toleration | Pod | taint 허용 | 특정 Node 선택 |

### 6.4 Effect

| Effect | 동작 | 교육 포인트 |
|---|---|---|
| PreferNoSchedule | 가능하면 피함 | 강제 격리 아님 |
| NoSchedule | 새 Pod 배치 거부 | 기존 Pod는 유지 가능 |
| NoExecute | 배치 거부와 기존 Pod Eviction | 운영 영향이 가장 큼 |

### 6.5 Inventory Group 방식

Kubespray Inventory의 별도 Worker Group에 label과 taint를 선언하면 scale 단계에서 일관되게 적용할 수 있다.

```text
worker1_node
→ hosts
→ node_labels
→ node_taints
→ kube_node children에 포함
```

그룹 이름과 `--limit` 대상이 일치하는지 확인한다.

### 6.6 Pod 배치 검증

```text
Node에 label 존재
+ Node에 taint 존재
+ Pod nodeSelector 일치
+ Pod toleration 일치
+ 실제 Pod NODE가 대상 Node
=
의도한 배치 경계 성립
```

확인할 정보:

- `kubectl get nodes --show-labels`
- `kubectl describe node`의 Taints
- Pod spec의 `nodeSelector`
- Pod spec의 `tolerations`
- Scheduler Event
- 실제 Pod `NODE`

### 6.7 대표 실패

```text
label만 있음
→ 일반 Pod도 배치될 수 있음

taint만 있음
→ toleration 있는 Pod가 어느 tainted Node로 갈지 선택하지 못함

nodeSelector만 있음
→ taint 때문에 Pending

toleration만 있음
→ 다른 허용 Node에도 배치 가능

NoExecute를 잘못 적용
→ 기존 Pod가 Eviction될 수 있음
```

### 6.8 변경 전 질문

1. 새 Node는 일반 Worker인가 전용 Worker인가?
2. 기존 Pod가 이미 있는 Node인가?
3. 적용할 Effect는 무엇인가?
4. 기존 Workload에 toleration이 있는가?
5. 배치 실패 시 원복할 label·taint 값은 기록했는가?
6. Inventory 기준본과 실제 Node 상태가 일치하는가?

## 7. 2.3 DKS FAQ

### 7.1 FAQ의 역할

FAQ는 모든 문제의 상세 Runbook이 아니라 **반복 문의를 올바른 신청·Manual·담당 영역으로 연결하는 시작점**이다.

### 7.2 주요 질문과 라우팅

| 요청 | 먼저 확인할 것 | 연결 문서·담당 영역 |
|---|---|---|
| DKS Project 사용 | 신청·대상 Cluster·Quota·사용자 | KubeSphere Operation 1.1~1.5 |
| Harbor 권한 | AD·Project·Role | Harbor 3.2~3.3 |
| Namespace 축소·삭제 | 영향·데이터·Project 관계 | 승인된 변경 절차 |
| kubectl 사용 | Bastion·CyberArk·kubeconfig | KubeSphere Operation 1.6 |
| 외부 애플리케이션 접근 | Ingress Domain·VIP-B·방화벽 | User Manual·GSAMS |
| DevOps·Image Build | 지원 범위·대체 시스템 | 사용자 책임·P-DEP 등 운영 기준 확인 |
| 로그인 오류 | AD·보안그룹·비밀번호 | 인증 담당과 운영팀 |

### 7.3 FAQ에서 단정하지 않을 값

- 현재 유효한 AD Group
- 현지 SCS의 최종 신청 시스템 경로
- 실제 방화벽 승인 상태
- 현재 Cluster의 StorageClass
- 사용자별 Project·Role
- 특정 URL의 실제 유효성

FAQ의 과거 예시를 현재 운영 사실로 사용하지 않고, 해당 Manual과 현재 화면에서 다시 확인한다.

### 7.4 삭제 요청 경계

Namespace·Workspace 삭제는 단순 UI 정리가 아니다.

- Workload·PVC·Secret·ConfigMap 삭제 영향
- PV Reclaim Policy
- Harbor Image와 별도 관계
- 사용자 접근 제거
- 백업·복구 가능성
- 승인자

위 항목이 확인되지 않으면 FAQ만 보고 실행하지 않는다.

## 8. 2.4 Utilizing the Kubernetes Native API

### 8.1 목적과 경계

Kubernetes API를 승인된 외부 소비 시스템에 제공할 때 `Service → Ingress → kube-apiserver → 인증 → RBAC` 구조를 사용한다. 이는 단순 URL 생성이 아니라 **Control Plane API 노출과 권한 제공**이므로 네트워크·인증·권한·감사 경계를 함께 설계한다.

### 8.2 전체 구조

```text
승인된 Client Source
→ DNS / FQDN
→ VIP-B / Ingress Controller
→ kube-apiserver Ingress
→ kube-apiserver Service :443
→ kube-apiserver Endpoint :6443
→ ServiceAccount 또는 승인된 인증 주체
→ Role / ClusterRole
→ RoleBinding / ClusterRoleBinding
→ 허용된 Kubernetes Resource
```

### 8.3 Service 검증

- Selector가 kube-apiserver Static Pod label과 일치한다.
- Service Port와 TargetPort가 의도와 일치한다.
- Endpoints가 올바른 Control Plane Node를 가리킨다.
- 다른 Cluster의 Master IP가 들어가지 않았다.

```text
Service 존재
≠ Endpoints 정상
```

### 8.4 Ingress 검증

- 승인된 FQDN
- TLS passthrough 또는 승인된 TLS 방식
- Backend Service·Port
- Ingress Controller Address
- Source IP/CIDR 제한
- DNS와 VIP-B

Source 제한이 미확정이면 외부 노출 완료로 간주하지 않는다.

### 8.5 인증과 RBAC

```text
인증 없음
→ system:anonymous
→ 401 또는 403이 정상 경계일 수 있음

인증 있음
→ 인증 주체 확인
→ RBAC으로 Resource·Verb·Namespace 제한
```

RBAC은 현재 눈에 보이는 API 호출 하나만 통과시키는 방식으로 성급히 정하지 않는다. 소비 시스템이 실제로 대체해야 하는 기능 범위를 먼저 확인하고, 필요한 Resource·Verb·Namespace를 식별한 뒤 최소 권한으로 줄인다.

### 8.6 Token·Credential 경계

- Token 원문을 문서에 붙이지 않는다.
- `echo $TOKEN` 출력이나 화면 공유를 교육 증적으로 남기지 않는다.
- 장기 Token 사용 여부는 Kubernetes Version과 보안 정책을 확인한다.
- ServiceAccount를 `default` Namespace에 임의 생성하지 않는다.
- ClusterRoleBinding으로 불필요하게 범위를 확대하지 않는다.
- Credential 전달·회수·만료·Rotation 책임을 정한다.

### 8.7 완료 증거

```text
승인된 Source만 연결 가능
+ DNS·VIP·Ingress·Service·Endpoint 정상
+ 인증 없는 요청은 거부
+ 인증된 요청은 허용 Resource만 성공
+ 허용되지 않은 Verb·Namespace는 거부
+ Audit·로그 위치 확인
+ Token 원문 미노출
```

### 8.8 중단 기준

- 호출 주체 Source CIDR 미확정
- API 범위와 필요한 Resource·Verb 미확정
- Ingress가 전체 네트워크에 열림
- 과도한 Cluster Admin 권한이 필요하다고 가정
- Token 보관·Rotation 책임 미확정
- 대상 Cluster·FQDN·Endpoint 불일치

## 9. 2.5 Renewing API Server Certificates

### 9.1 목적

kubeadm이 관리하는 Control Plane 인증서와 kubeconfig Client Certificate를 갱신하고, 실행 중인 Static Pod와 Bastion·KubeSphere 연결이 새 인증서를 사용하도록 순차 반영한다.

### 9.2 절대 원칙

```text
Master 01
→ 인증서 갱신
→ Static Pod 재생성
→ API Ready/Live와 Cluster 기능 확인
→ 정상일 때만 Master 02
→ 동일 검증
→ 정상일 때만 Master 03
```

여러 Master를 동시에 갱신하거나 재시작하지 않는다.

### 9.3 변경 전 백업

모든 Master에서 다음을 백업한다.

- `/etc/kubernetes/ssl`
- `/etc/kubernetes/admin.conf`
- `/etc/kubernetes/scheduler.conf`
- `/etc/kubernetes/controller-manager.conf`
- 현재 인증서 만료 정보
- 현재 Static Pod 상태
- Bastion kubeconfig
- KubeSphere Member 연결 식별정보

백업 경로·소유자·복구 명령과 실제 파일 존재를 확인한다.

### 9.4 Node별 갱신 흐름

1. 대상 Master 한 대를 고정한다.
2. 현재 API와 Static Pod 상태를 확인한다.
3. `kubeadm certs check-expiration` 결과를 기록한다.
4. 승인된 명령으로 인증서를 갱신한다.
5. 디스크의 새 만료일을 확인한다.
6. API Server·Scheduler·Controller Manager Static Pod Sandbox를 해당 Node에서만 재생성한다.
7. 새 Pod가 Running·Ready인지 확인한다.
8. `/readyz`, `/livez`와 Cluster API를 확인한다.
9. 해당 Node의 kubeconfig를 새 `admin.conf`로 갱신한다.
10. 정상 복구 후 다음 Master로 이동한다.

### 9.5 Static Pod가 필요한 이유

```text
인증서 파일 갱신
≠ 실행 중인 프로세스가 새 파일을 읽음

Static Pod 재생성
→ kubelet이 Control Plane Container를 다시 시작
→ 새 인증서 파일 로드
```

### 9.6 Bastion kubeconfig

모든 Master 작업 후 정상 Master의 새 `admin.conf`를 승인된 방식으로 Bastion root와 `dspaas` kubeconfig에 반영한다.

확인할 것:

- API endpoint
- Client Certificate 만료일
- 파일 소유자·권한
- `current-context`
- `kubectl get nodes`
- 기존 자동화가 사용하는 경로

### 9.7 KubeSphere 재연결

인증서 갱신으로 Member 연결 정보가 바뀌는 환경에서는 다음을 수행할 수 있다.

```text
기존 Member Cluster 식별정보 기록
→ Unbind
→ 새 kubeconfig로 Import
→ KubeSphere System Workload 재시작
→ Host Console에서 Member 상태 확인
```

Unbind 전에 Cluster Name·Tag·현재 상태·복구 방법을 기록한다. kubeconfig 원문은 교육 자료에 남기지 않는다.

### 9.8 Node별 다음 단계 Gate

다음이 모두 정상이어야 다음 Master로 이동한다.

- 갱신된 인증서 만료일
- API Server Static Pod Running·Ready
- Scheduler·Controller Manager 정상
- `/readyz` 성공
- `/livez` 성공
- VIP-A 경유 API 정상
- Node와 System Pod에 새로운 이상 없음
- 현재 Master에서 kubectl 정상

### 9.9 중단·복구

- Static Pod가 재생성되지 않음
- API Ready/Live 실패
- VIP-A는 실패하고 로컬 API만 정상
- 새 kubeconfig 인증 실패
- ETCD 연결 오류
- 인증서 SAN·CA 불일치

이 경우 다음 Master로 이동하지 않는다. 백업 파일과 현재 실패 지점을 기준으로 해당 Node를 먼저 복구한다.

---

# Part 2. Harbor Manual

## 10. 3.1 SCS Harbor Installation

### 10.1 이 교육에서의 위치

이번 출장의 Xi'an Harbor는 이미 구축되어 있다. 8/27에는 Harbor를 재설치하지 않고 **왜 Docker·offline installer·인증서·hostname·data volume이 필요하며, 설치가 정상이라는 것을 무엇으로 확인하는지**를 Manual로 전수한다.

### 10.2 설치 전제

Manual의 기준 예시는 다음 Version을 사용한다.

| 구성 | Manual 예시 Version |
|---|---|
| Docker | 20.10.16 |
| docker-compose | 1.27.4 |
| Harbor offline installer | v2.2.2 |

실제 재설치 작업에서는 현재 승인 Version과 호환성을 다시 확인한다. 문서 Version을 최신 환경에 무조건 적용하지 않는다.

### 10.3 설치 흐름

```text
Harbor VM·Disk·DNS·FQDN·방화벽 확인
→ Docker Repository 준비
→ Docker·docker-compose 설치·서비스 기동
→ offline installer 확보·검증·압축 해제
→ Server Certificate·Private Key·Root CA 준비
→ OS·Docker CA trust 반영
→ harbor.yml 작성
→ data_volume 확인
→ install.sh 실행
→ Container·HTTPS·Registry API·로그인·데이터 검증
```

### 10.4 harbor.yml 핵심값

| 항목 | 의미 | 반드시 확인할 것 |
|---|---|---|
| hostname | Harbor FQDN | `xa.dcr.dks.samsungds.net` 등 승인값 |
| http.port | HTTP Port | HTTPS Redirect 정책 |
| https.port | HTTPS Port | 방화벽·Certificate |
| certificate | Server Certificate | FQDN·Chain·만료 |
| private_key | Private Key | 파일 권한·일치 여부 |
| data_volume | Registry 영속 데이터 | Disk 용량·Mount·Backup |
| admin password | 초기 관리자 Credential | 문서·로그 미노출 |
| database password | 내부 DB Credential | Secret 관리 |

### 10.5 인증서 세 종류를 구분한다

```text
Harbor Server Certificate
→ Client가 접속하는 FQDN의 서버 인증서

Private Key
→ Server Certificate와 쌍을 이루는 비밀키

Root / Intermediate CA
→ Client가 Server Certificate를 신뢰하도록 하는 체인
```

Root CA와 Server Certificate를 같은 파일로 설명하지 않는다. Private Key는 화면과 문서에 절대 노출하지 않는다.

### 10.6 설치 완료 증거

```text
Docker active
+ docker-compose Version 확인
+ Harbor Container 정상
+ HTTPS FQDN 응답
+ /v2/ Registry API가 기대 상태 코드 반환
+ 관리자 또는 승인 계정 로그인
+ Project 생성 가능
+ Test Image Push·Pull 성공
+ data_volume에 데이터 영속
+ 재시작 후 Repository 유지
```

### 10.7 설치 실패 분기

| 증상 | 먼저 볼 것 |
|---|---|
| Docker 미기동 | Package·daemon log·Disk |
| Container 반복 재시작 | `harbor.yml`, Port, Certificate, Data permission |
| HTTPS x509 | Server Chain·Client CA trust·FQDN |
| `/v2/` 연결 실패 | nginx·Port·방화벽·DNS |
| 로그인 실패 | Account·AD·Password·Harbor auth |
| Push 실패 | Project Role·Quota·Tag·Disk |
| 재시작 후 데이터 없음 | data_volume·Mount·권한 |

## 11. 3.2 Create a project

### 11.1 신청에서 Project로

Harbor Project는 KubeSphere Project와 다른 객체다.

```text
KubeSphere Project
= Kubernetes Namespace와 Workload 작업 경계

Harbor Project
= Container Image Repository와 접근 권한 경계
```

### 11.2 생성 기준

| 항목 | 기준 |
|---|---|
| Project Name | 승인된 신청 이름 |
| Access Level | Private |
| Storage Quota | 승인값, Manual 예시는 10 GB |
| 관리자 | 승인된 ProjectAdmin |
| 일반 사용자 | Developer |

Manual 예시의 10 GB를 모든 신청의 고정값으로 단정하지 않고 현재 정책과 신청 승인량을 확인한다.

### 11.3 Private와 Public

| 구분 | Private | Public |
|---|---|---|
| Pull | Member·인증 필요 | 인증 없이 가능할 수 있음 |
| Push | 권한 필요 | 권한 필요 |
| 사용 | 조직·서비스 전용 | 공개 Image |
| 기본 | 승인된 내부 Project | 별도 근거 필요 |

내부 Image Project를 편의상 Public으로 만들지 않는다.

### 11.4 완료 증거

- 승인 이름의 Project가 하나만 존재한다.
- Access Level이 Private다.
- Quota가 승인값과 일치한다.
- ProjectAdmin이 지정되어 있다.
- 다른 Project와 이름·권한을 혼동하지 않았다.
- 사용자 계정으로 허용된 Repository만 보인다.

## 12. 3.3 Managing Users

### 12.1 역할 비교

| Role | Pull | Push | Artifact 관리 | Member 관리 | 기본 대상 |
|---|---:|---:|---:|---:|---|
| ProjectAdmin | O | O | O | O | Project 관리자 |
| Developer | O | O | O | X | 일반 개발·사용자 |

ProjectAdmin을 여러 명 지정할지, 신청서 Admin과 어떤 관계인지 현재 운영 정책을 확인한다. KubeSphere `project-operator`와 Harbor `ProjectAdmin`은 이름과 범위가 다른 별도 Role이다.

### 12.2 멤버 추가

```text
Harbor 로그인
→ Projects
→ 대상 Project
→ Members
→ +User
→ 실제 AD 계정 선택·입력
→ ProjectAdmin 또는 Developer
→ 저장
```

### 12.3 역할 변경·제거

- 신청 또는 승인 근거를 확인한다.
- 현재 Repository 사용자를 확인한다.
- 마지막 ProjectAdmin 제거 여부를 확인한다.
- 자동화 계정·Robot Account 사용 여부를 확인한다.
- 제거 후 필요한 Image Pull이 중단되지 않는지 영향 확인한다.
- 변경 전후 멤버 목록을 증적으로 남긴다.

### 12.4 실제 권한 검증

```text
Developer
→ docker login 성공
→ 승인 Project Image Pull 성공
→ 승인 Project Image Push 성공
→ Members 관리 불가

ProjectAdmin
→ 위 기능
+ Members·Project 설정 관리
```

웹 UI에 이름이 보이는 것만으로 완료하지 않고 승인된 테스트 Repository·Tag로 실제 접근 범위를 확인한다.

### 12.5 흔한 실패

```text
KubeSphere Role을 Harbor Role로 그대로 사용
→ 서로 다른 권한 체계 혼동

사용자가 Harbor에 로그인됨
→ 특정 Private Project 권한까지 있다고 과잉 판정

Developer인데 Push 거부
→ Project·Repository·Tag·계정·Quota를 분리 확인

ProjectAdmin 제거
→ 남은 관리자·자동화 영향 미확인
```

---

# Part 3. 통합 시나리오와 판정

## 13. 요청 유형별 Manual 선택 훈련

| 요청 | 선택할 Manual | 첫 확인 |
|---|---|---|
| Worker VM을 Cluster에 추가 | 2.1 | 대상 Cluster·VM·Inventory·Pre-setting |
| 특정 팀 전용 Node 구성 | 2.2 | label·taint·Pod 배치 요구 |
| 사용 방법·지원 범위 문의 | 2.3 | 요청 유형과 담당 영역 |
| 외부 시스템에서 Kubernetes API 호출 | 2.4 | 기능 범위·Source·인증·RBAC |
| API 인증서 만료 예정 | 2.5 | 만료일·백업·HA·작업 승인 |
| Harbor 신규 설치·복구 | 3.1 | VM·Disk·FQDN·Certificate·Version |
| Image 저장 공간 요청 | 3.2 | Project Name·Private·Quota |
| Harbor 사용자 추가 | 3.3 | 계정·Project·Role |

## 14. 강사 시연·워크스루 순서

1. Worker 추가 요청 카드를 읽고 2.1의 시작점과 완료 증거를 설명한다.
2. Inventory에서 새 Node Group·label·taint를 읽는다.
3. Pod YAML의 nodeSelector·toleration을 비교한다.
4. FAQ 질문을 해당 Manual과 담당 영역으로 분류한다.
5. Native API 경로를 Service·Ingress·RBAC까지 그린다.
6. 인증서 갱신을 Master별 Gate로 탁상훈련한다.
7. Harbor 설치의 FQDN·Certificate·data_volume을 읽는다.
8. Private Project와 Quota를 생성 사례로 설명한다.
9. ProjectAdmin과 Developer를 실제 권한으로 비교한다.
10. 교육생이 임의 요청을 받아 Manual·선행조건·검증·중단 기준을 Teach-back한다.

## 15. 운영 변경 공통 프레임

모든 절차를 아래 순서로 읽는다.

```text
목적
→ 대상과 현재 상태
→ 선행조건
→ 입력값·기준본
→ 변경 영향
→ 백업·복구
→ 실행 순서
→ 단계별 성공 증거
→ 중단 조건
→ 최종 기능 검증
→ 증적·인계
```

어떤 Manual에 이 항목이 부족하면 강사가 구두로 값을 만들어 채우지 않고 현장 확인사항으로 기록한다.

## 16. 대표 사고 연습

### 사례 1 — 새 Worker가 Ready지만 PVC Pod만 Pending

```text
Node 등록 성공을 전체 성공으로 보지 않음
→ CSI Node Pod
→ Node NFS Route·2049
→ StorageClass·PVC Event
→ taint·toleration과 Scheduling
```

### 사례 2 — 전용 Node에 일반 Pod가 배치됨

```text
label만 있는가?
→ taint가 있는가?
→ Effect가 무엇인가?
→ 일반 Pod에 예상치 못한 toleration이 있는가?
```

### 사례 3 — Native API URL은 열리지만 모든 요청이 Forbidden

```text
네트워크 성공과 권한 성공 분리
→ 인증 주체
→ Namespace
→ Role·Binding
→ Resource·Verb
```

### 사례 4 — Master 01 인증서 갱신 후 API Ready 실패

```text
Master 02로 진행 금지
→ Static Pod 상태
→ readyz/livez
→ 인증서·CA·SAN
→ kubeconfig
→ 백업 복구 여부
```

### 사례 5 — Harbor 웹은 열리지만 docker login x509

```text
Harbor Down으로 단정하지 않음
→ 사용자 시스템 CA trust
→ FQDN과 Server Chain
→ Docker daemon 재시작
→ /v2/ 응답
```

### 사례 6 — Harbor Login 성공, Push denied

```text
로그인과 Project 쓰기 권한 분리
→ 대상 Project
→ Role
→ Repository·Tag
→ Quota
```

## 17. 숙지 수준 분류

### A. 문서 없이 설명할 것

- [ ] Worker 추가의 Pre-setting→Inventory→scale→기능 검증 흐름
- [ ] Node Ready와 Workload·Storage 성공의 차이
- [ ] label·taint·nodeSelector·toleration 네 요소
- [ ] FAQ가 상세 Runbook이 아니라 라우터인 이유
- [ ] Native API의 Service·Ingress·인증·RBAC·Source 제한
- [ ] 인증서 갱신 one-by-one 원칙과 Static Pod 재생성 이유
- [ ] Harbor Server Certificate·Private Key·Root CA 차이
- [ ] Harbor Project와 KubeSphere Project 차이
- [ ] ProjectAdmin과 Developer 차이
- [ ] Harbor Running과 Push/Pull·영속성 성공의 차이

### B. Manual을 보며 정확히 찾을 것

- [ ] Worker Node Pre-setting 항목과 Inventory 경로
- [ ] `scale.yml --limit` 대상과 로그 판독
- [ ] Node label·taint Group 선언
- [ ] Pod nodeSelector·toleration YAML
- [ ] FAQ별 관련 문서
- [ ] kube-apiserver Service·Ingress·RBAC 위치
- [ ] Master별 인증서 백업·갱신·Health 명령
- [ ] Bastion kubeconfig와 KubeSphere 재연결 절차
- [ ] Harbor 설치 Version·파일·`harbor.yml`
- [ ] Harbor Project·Quota·Member 메뉴

### C. 실제 환경에서 다시 확인할 것

- 실제 Cluster·Bastion·Inventory 기준본
- 실제 신규 Node hostname·IP·Disk·Route
- 실제 label·taint 정책
- Native API 소비 시스템의 기능 범위·Source CIDR
- 실제 인증서 만료일·Master 상태·백업 경로
- 실제 Harbor Version·Disk·FQDN·Certificate Chain
- 실제 Project Quota 정책
- 실제 사용자 계정과 Role
- 승인자·변경 시간·복구 담당자

## 18. 자가점검

| 질문 | 상태 | 막힌 부분 | Manual |
|---|---|---|---|
| Worker 추가의 완료를 Ready 이상으로 설명하는가? | 미평가 |  | 2.1 |
| taint와 toleration을 Node·Pod 양쪽에서 설명하는가? | 미평가 |  | 2.2 |
| FAQ 질문을 올바른 문서로 보낼 수 있는가? | 미평가 |  | 2.3 |
| Native API의 Source·Auth·RBAC을 함께 설명하는가? | 미평가 |  | 2.4 |
| 인증서 갱신 중 다음 Master Gate를 설명하는가? | 미평가 |  | 2.5 |
| Harbor 설치의 FQDN·Certificate·data_volume을 설명하는가? | 미평가 |  | 3.1 |
| Private Project와 Quota를 설명하는가? | 미평가 |  | 3.2 |
| ProjectAdmin과 Developer를 실제 권한으로 구분하는가? | 미평가 |  | 3.3 |
| 운영 변경에서 백업·중단·복구를 함께 말하는가? | 미평가 |  | 전체 |

## 19. 직접 연습

### 연습 1 — Worker 추가 Gate 카드

```text
대상 Cluster:
신규 Node:
Pre-setting 완료 증거:
Inventory 변경:
scale 대상:
Node 검증:
Workload 검증:
Storage 검증:
중단 기준:
Inventory 정리:
```

### 연습 2 — 배치 조합 판정

다음 조합에서 Pod가 어디에 배치될 수 있는지 설명한다.

```text
A. label O / taint X / nodeSelector O / toleration X
B. label O / taint NoSchedule / nodeSelector O / toleration X
C. label O / taint NoSchedule / nodeSelector X / toleration O
D. label O / taint NoSchedule / nodeSelector O / toleration O
```

### 연습 3 — Native API 권한 카드

```text
Client Source:
FQDN:
Service·Endpoint:
Authentication:
Namespace:
Resource:
Verb:
허용 테스트:
거부 테스트:
Credential Rotation:
```

### 연습 4 — 인증서 갱신 탁상훈련

Master 01에서 `readyz`가 실패한 상황을 주고 다음 Master로 이동하지 않은 채 필요한 확인과 복구 순서를 작성한다.

### 연습 5 — Harbor 설치 파일 판독

`harbor.yml`에서 다음을 찾아 의미와 검증 방법을 말한다.

```text
hostname
https.certificate
https.private_key
data_volume
admin password 취급
```

### 연습 6 — Project·Role 변환

신청 사례를 다음으로 변환한다.

```text
Harbor Project Name
Private/Public
Quota
ProjectAdmin
Developer
완료 검증
```

## 20. 예상 질문

| 예상 질문 | 답변 핵심 | 현재 답변 가능 여부 |
|---|---|---|
| Node가 Ready면 추가가 끝난 건가요? | System Pod·Workload·Storage 사용 검증까지 필요 | 미평가 |
| label과 taint 중 하나만 쓰면 안 되나요? | 선택과 배제 역할이 다름 | 미평가 |
| NoExecute는 왜 위험한가요? | 기존 Pod Eviction 가능 | 미평가 |
| Native API를 Ingress로 열면 보안상 괜찮나요? | Source 제한·Auth·RBAC·Credential 관리가 함께 필요 | 미평가 |
| ServiceAccount에 cluster-admin을 주면 간단하지 않나요? | 기능 범위 확인 후 최소 권한으로 제한 | 미평가 |
| 인증서 파일만 바꾸면 왜 Pod를 재시작하나요? | 실행 프로세스가 새 파일을 읽어야 함 | 미평가 |
| Master 세 대를 같이 갱신하면 더 빠르지 않나요? | Control Plane 가용성과 복구 Gate 상실 | 미평가 |
| Harbor Container가 모두 Running이면 정상 아닌가요? | HTTPS·API·로그인·Push/Pull·영속성 별도 | 미평가 |
| Harbor Project를 Public으로 만들면 Secret이 필요 없나요? | 내부 보안정책과 접근통제 훼손, 기본은 Private | 미평가 |
| Developer와 ProjectAdmin의 차이는? | Image read/write는 같고 Member 관리 권한이 다름 | 미평가 |

## 21. 현장 기록 양식

```text
교육일: 2026-08-27
오전 Operations Manual
2.1 Worker 추가 이해·시연 결과: ______________________
2.2 taint·label 이해·시연 결과: _____________________
2.3 FAQ 라우팅 결과: ________________________________
2.4 Native API 워크스루 결과: _______________________
2.5 인증서 갱신 탁상훈련 결과: ______________________

오후 Harbor Manual
3.1 설치 구조·검증 결과: ____________________________
3.2 Project 생성·Quota 결과: _________________________
3.3 User·Role 결과: _________________________________

실제 환경에서 확인할 값: ____________________________
변경 실행 없이 워크스루로 대체한 항목: ______________
질문 주차장: ________________________________________
민감정보 노출 없음: __________________________________
```

## 22. 8/27 완료 기준

- [ ] 교육생이 Worker 추가의 시작과 끝을 VM부터 Workload·Storage 검증까지 설명한다.
- [ ] Inventory 변경과 `--limit` 대상의 위험을 설명한다.
- [ ] label·taint·nodeSelector·toleration을 함께 설명한다.
- [ ] DKS FAQ 요청을 적절한 Manual과 담당 영역으로 보낸다.
- [ ] Native API의 Service·Ingress·Source 제한·Auth·RBAC을 연결한다.
- [ ] Token·Private Key·kubeconfig 원문을 노출하지 않는다.
- [ ] 인증서 갱신을 Master one-by-one과 Node별 Health Gate로 설명한다.
- [ ] 백업과 Bastion kubeconfig·KubeSphere 재연결까지 범위를 설명한다.
- [ ] Harbor 설치에서 FQDN·Certificate·data_volume과 기능 검증을 설명한다.
- [ ] Harbor Project를 Private와 승인 Quota로 생성하는 이유를 설명한다.
- [ ] ProjectAdmin과 Developer 권한을 구분한다.
- [ ] 고위험 절차를 승인 없이 운영 환경에서 실행하지 않는다.
- [ ] 각 요청에서 사용할 Manual을 60초 안에 찾는다.

## 23. 다음 일정과 연결

8/28에는 운영자 절차에서 사용자 관점으로 이동한다.

```text
DKS 서비스 구조·접근
→ Harbor 사용자 로그인·Pull·Tag·Push
→ KubeSphere PVC·Secret·Deployment·Service·Ingress
→ GSAMS 신청
→ Harbor·Dashboard·NFS·Project 권한·ImagePullBackOff 문제의 첫 확인
```

관련 문서: [[2026-08-28 User Manual 및 Troubleshooting Guide 기술 전수|2026-08-28 User Manual 및 Troubleshooting Guide 기술 전수]]

---

## 24. 제한된 준비시간과 운영 위험을 반영한 현장 실행 전략

> [!important] 적용 원칙
> 8/27은 Worker 추가·Native API 노출·인증서 갱신·Harbor 설치를 현장에서 실제로 수행해 보이는 날이 아니다. **운영 요청을 받았을 때 올바른 Manual을 선택하고, 선행조건·핵심 절차 위치·완료 증거·중단 및 복구 경계를 인계하는 것**이 목적이다. 라이브 실행의 양보다 작업 경계를 정확히 설명하는 것을 우선한다.

### 24.1 모든 Manual에 적용할 고정 진행 단위

각 절차는 다음 여섯 항목으로만 진행한다.

```text
어떤 요청에서 여는 Manual인가
→ 실제 대상은 무엇인가
→ 시작 전에 무엇이 준비되어야 하는가
→ 핵심 절차는 문서 어디에 있는가
→ 어디까지 확인해야 완료인가
→ 어느 조건에서 중단·복구·에스컬레이션하는가
```

명령을 처음부터 끝까지 읽거나 실행하지 않는다. 교육생이 이 여섯 항목을 해당 Manual에서 찾을 수 있으면 기술 전수의 목적을 달성한 것으로 본다.

### 24.2 범위별 시연 수준

| 범위 | 현장 우선 방식 | 실행하지 않을 것 |
|---|---|---|
| `2.1` Worker 추가 | 기존 Worker와 Node 상태를 읽기 전용으로 확인하고, Pre-setting→Inventory→scale→기능 검증 흐름을 Manual에서 추적 | Inventory 수정·`scale.yml` 실행·Node 추가/삭제 |
| `2.2` taint·label | 기존 Node의 label·taint와 Workload YAML의 selector·toleration을 비교 | `kubectl label`·`kubectl taint`·Workload 변경 |
| `2.3` DKS FAQ | 요청 카드를 보고 올바른 Manual·담당 영역을 선택 | FAQ 항목을 별도 실습으로 확장 |
| `2.4` Native API | 구조도와 기존 Service·Ingress·RBAC을 읽기 전용으로 확인하거나 Manual 워크스루 | 신규 노출·Source 허용·Credential 발급·권한 확대 |
| `2.5` 인증서 갱신 | Master one-by-one 탁상훈련과 중단 Gate 설명 | 인증서 파일 교체·Static Pod 재기동·kubeconfig 갱신 |
| `3.1` Harbor 설치 | `harbor.yml`의 구조와 설치 후 검증 항목을 Manual에서 확인 | Harbor 설치·재설치·서비스 재시작 |
| `3.2~3.3` Project·User | 기존 Private Project·Quota·Member·Role을 읽기 전용으로 조회 | Project 생성·공개 전환·Quota·Role 변경 |

### 24.3 기준 대상은 두 개만 사용한다

가능하면 다음 두 대상을 정해 하루 전체의 기준으로 사용한다.

```text
기존 Worker Node 1대
→ label·taint·System Pod·Runtime 확인 기준

기존 Harbor Private Project 1개
→ Repository·Artifact·Quota·Member·Role 확인 기준
```

절마다 새로운 Node나 Project를 찾지 않는다. 기준 대상이 준비되지 않았으면 교육용 대상을 새로 만들지 않고 Manual 예시와 마스킹된 정상 결과로 전환한다.

### 24.4 준비 우선순위

#### 반드시 준비할 것

- 기준 Manual `2.1~2.5`, `3.1~3.3`의 링크와 절차 시작 위치를 확인한다.
- 대상 Cluster·Bastion·context를 혼동하지 않도록 읽기 전용 조회 대상 하나를 정한다.
- 기존 Worker의 Node 상세, label·taint, 주요 DaemonSet을 어디서 확인하는지 한 번만 확인한다.
- 기존 Harbor Project 하나에서 Private 여부, Quota, Member, Role, Artifact 위치를 확인한다.
- `harbor.yml`, Token, Private Key, kubeconfig, Password가 화면에 노출되지 않도록 표시 범위를 정한다.

#### 있으면 사용하되 별도로 만들지 않을 것

- 기존 Inventory의 마스킹된 구조
- 정상 `scale.yml` recap 또는 Node 검증 결과
- 기존 Native API Service·Ingress·RBAC
- 과거 인증서 갱신의 정상 Health 결과
- 기존 Harbor 설치 상태와 HTTPS·Registry API 결과

#### 이번 교육을 위해 준비하지 않을 것

- 신규 VM·Worker Node
- 별도 Kubespray Inventory와 실습 Cluster
- 교육용 label·taint 조합
- Native API 신규 Endpoint와 ServiceAccount
- 만료 임박 인증서 또는 인증서 교체 환경
- Harbor 재설치 환경과 교육용 Project·사용자
- 별도 캡처·로그 묶음

### 24.5 오전 Operations Manual 진행

#### `2.1` Worker 추가

Manual에서 시작과 끝을 한 번 연결한다.

```text
VM·Pre-setting
→ Inventory
→ scale 대상
→ Node Ready
→ CNI·CSI·kube-proxy
→ Workload 배치
→ PVC Mount·Read/Write
→ Inventory 기준본 정리
```

강조점은 `scale.yml` 성공이나 `Node Ready`만으로 완료하지 않는 것이다. 실제 명령 실행보다 완료 증거와 중단 기준을 설명한다.

#### `2.2` taint·label

기존 Node와 YAML을 비교하여 다음 네 요소의 역할만 확정한다.

```text
label = 선택할 Node의 속성
taint = 기본 배치 거부 조건
nodeSelector / affinity = Pod가 선택할 Node
toleration = Pod가 허용할 taint
```

#### `2.3~2.5`

- FAQ는 요청을 적절한 문서로 보내는 라우터로 사용한다.
- Native API는 Network 진입점보다 Authentication·RBAC·Source 제한을 함께 본다.
- 인증서 갱신은 Master 한 대의 Health가 회복되기 전에는 다음 Master로 이동하지 않는 원칙을 탁상훈련으로 확인한다.

### 24.6 오후 Harbor Manual 진행

`3.1` 설치는 구성 파일과 검증 흐름을 Manual에서 찾는 방식으로 진행한다.

```text
설치 전제
→ FQDN·Certificate·Private Key·data_volume
→ 설치
→ HTTPS
→ Registry API
→ Login
→ Push/Pull
→ Artifact·Data 영속성
```

`3.2~3.3`은 기존 Harbor Project 화면을 사용할 수 있을 때만 조회한다. Project 생성과 Role 변경이 준비되지 않았더라도 다음 차이를 설명하면 된다.

```text
Project 존재
≠ 올바른 Private·Quota 정책

Login 성공
≠ 대상 Project Push 권한

Developer
≠ Project Member 관리 권한
```

### 24.7 현장 전환 기준

```text
Mode 1. 기존 환경 읽기 전용 조회 + Manual
→ Node·Harbor 접근이 가능한 경우

Mode 2. 마스킹된 정상 결과 + Manual
→ 일부 접근이나 권한이 제한된 경우

Mode 3. 요청 카드 + Manual 탐색
→ 실제 대상·승인·접근이 준비되지 않은 경우
```

어떤 Mode에서도 운영 변경을 교육 성과로 요구하지 않는다. 실제 실행이 없더라도 올바른 Manual, 선행조건, 완료 증거와 중단 Gate를 찾으면 된다.

### 24.8 즉시 중단할 조건

다음 중 하나라도 해당하면 라이브 변경으로 전환하지 않는다.

- 대상 Cluster·Inventory·Node identity가 확정되지 않았다.
- 변경 승인·백업·복구 담당자·작업 시간이 없다.
- `--limit`, Source CIDR, Role, 인증서 대상이 미확정이다.
- 화면 공유 중 Credential·Private Key·Password 노출 가능성이 있다.
- Harbor 또는 Control Plane의 서비스 영향 범위를 확인하지 못했다.

이 경우에는 현재 확인 가능한 상태와 돌아갈 Manual 위치만 기록한다.

### 24.9 이번 전략의 완료 판정

다음이 가능하면 8/27 기술 전수는 목적을 달성한 것으로 본다.

- 운영 요청을 `2.1~2.5`, `3.1~3.3` 중 올바른 Manual로 보낸다.
- 각 작업의 시작 전제와 최종 완료 증거를 연결한다.
- 조회 가능한 정상 환경과 실제 변경 작업을 구분한다.
- 고위험 변경에서 중단·백업·복구 Gate를 설명한다.
- 라이브 실행이 없어도 Manual에서 핵심 절차와 검증 위치를 찾는다.

