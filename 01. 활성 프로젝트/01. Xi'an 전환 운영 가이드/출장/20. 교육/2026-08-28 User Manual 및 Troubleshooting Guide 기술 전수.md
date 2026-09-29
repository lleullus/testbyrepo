---
title: "2026-08-28 User Manual 및 Troubleshooting Guide 기술 전수"
status: current
doc_type: training-note
scope: "2026-08-28 User Manual 4.1~4.4와 Troubleshooting Guide 6.1~6.5 기술 전수, 사용자 정상 흐름·초동 판단·강사 판정 기준"
created: "2026-08-15"
updated: "2026-08-21"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획]]"
---

# 2026-08-28 User Manual 및 Troubleshooting Guide 기술 전수

> [!important] 이 문서의 역할
> 8/28 오전에는 최종 배포 Manual의 `4.1~4.4 User Manual`, 오후에는 `6.1~6.5 Troubleshooting Guide`를 기술 전수한다. 이 문서는 사용자 절차와 장애 사례를 짧게 요약하는 문서가 아니라, **사용자가 DKS에 접근하고 Harbor Image·PVC·Deployment·Service·Ingress를 이용해 실제 서비스를 만드는 정상 경로와, 그 경로가 끊겼을 때 증거로 첫 단절을 찾는 방법을 충분한 밀도로 가르치기 위한 강사 학습·진행·판정 기준**이다.

> [!success] 교육 범위의 경계
> 오전에는 사용자 관점의 신청·접속·Image·Workload·Storage·Network 흐름을 연결한다. 오후에는 최종 배포 Troubleshooting 6.1~6.5만 다룬다. `Ingress 여러 UI 간헐 504`, `Native API 접속 및 권한 오류`, 내부 작성 원칙 문서는 이번 최종 배포 목록 밖이므로 교육 목차에 섞지 않는다.

> [!warning] 민감정보와 실제값
> AD 비밀번호, Docker Credential, Image Registry Secret, kubeconfig, Dashboard Token, ServiceAccount Token, 인증서 Private Key는 교육 자료와 기록에 남기지 않는다. URL·IP·StorageClass·계정·Project·Tag는 현재 Xi'an 카탈로그·Manual·현장 화면에서 다시 확인하며, 참조 출력의 동적 Pod 이름·IP·시간을 현재 사실처럼 사용하지 않는다.

## 1. 8/28 확정 범위

### 오전 — 4. User Manual

| Manual | 주제 | 교육 후 교육생이 판단할 것 |
|---|---|---|
| 4.1 | DS Kubernetes Service Overview | Host·Member·Harbor·Project·접속 경계와 이용 순서 |
| 4.2 | Harbor User Guide | CA trust·Login·Pull·Tag·Push·Artifact 확인 |
| 4.3 | KubeSphere User Guide | PVC·Image Secret·Deployment·Service·Ingress·HTTP 정상 경로 |
| 4.4 | GSAMS Application Guide | 해외 사업장에서 국내 DKS URL 접근을 위한 신청서 입력 방식 |

### 오후 — 6. Troubleshooting Guide

| Guide | 증상 | 첫 판단 축 |
|---|---|---|
| 6.1 | Harbor Access, Login, Image Push/Pull Errors | Network·CA·Auth·Repository/Tag·Role 분리 |
| 6.2 | Kubernetes Dashboard Access and Token Login | 대상 Cluster·URL·ServiceAccount·Token Secret 분리 |
| 6.3 | NetApp NFS PVC Bound but Pod Mount Fails | Provisioning과 Node Mount 분리 |
| 6.4 | Project Not Visible or Permission Missing | Namespace·Workspace Member·Project Member·Role 순서 |
| 6.5 | KubeSphere ImagePullBackOff with Private Image | Pod Event·Image·Secret·imagePullSecrets·Harbor Tag/권한 순서 |

이날의 핵심 질문은 다음이다.

> **정상 사용 흐름에서 어떤 연결이 성공해야 사용자 결과가 나오며, 문제가 발생했을 때 확인된 증거로 처음 끊긴 연결을 어떻게 찾는가?**

## 2. 하루 전체 이야기

```text
DKS 사용 준비
→ 사용자 계정·방화벽·Project·Role·Quota 확인
→ Harbor CA trust와 로그인
→ 승인된 Project의 Image Pull / Tag / Push
→ KubeSphere Project에서 Image Secret 생성
→ PVC 생성·Mount
→ Deployment·Pod 실행
→ Service·Endpoint 연결
→ Ingress·VIP-B·DNS
→ 사용자 HTTP 응답

문제 발생
→ 대상 Cluster·Project·시각·증상 고정
→ 정상 경로와 비교
→ 확인된 첫 단절 선택
→ 오류 문자열과 실제 객체 대조
→ 다음 행동을 갈라놓는 읽기 전용 확인
→ 승인된 수정 또는 담당 영역 에스컬레이션
→ 동일 정상 경로로 재검증
```

### 반복해서 구분할 것

```text
Harbor 웹 접속 성공
≠ Docker Login 성공

Docker Login 성공
≠ 특정 Private Project Image Pull·Push 권한

PVC Bound
≠ Pod Mount·Write/Read 성공

Image Registry Secret 존재
≠ Deployment가 그 Secret을 사용

Pod Running
≠ Service·Endpoint·Ingress·HTTP 정상

Workspace가 보임
≠ Project Member·Create 권한이 있음

Dashboard URL이 열림
≠ 올바른 Cluster Token과 권한으로 로그인됨
```

## 3. 권장 진행 블록

| 블록 | 범위 | 방식 | 통과 기준 |
|---|---|---|---|
| A | 4.1 | 구조도·접속·이용 흐름 | Host·Member·Harbor·Project 관계 설명 |
| B | 4.2 | Harbor User 워크스루 | CA→Login→Pull→Tag→Push→Artifact 연결 |
| C | 4.3 | KubeSphere 정상 시나리오 | PVC·Secret·Deployment·Service·Ingress·HTTP 연결 |
| D | 4.4 | GSAMS 신청서 사례 | 적용 조건과 필수 입력값 구분 |
| E | 6.1~6.2 | Access·인증 사례 | Network·CA·Account·Token 분리 |
| F | 6.3~6.5 | Storage·권한·Image 사례 | 첫 단절과 다음 확인 선택 |
| G | 통합 | 교육생 역할 기반 Teach-back | 정상 경로와 장애 초동을 연결 |

## 4. 기준 Manual

### User Manual

1. [[50. 운영/07. DKS User Guide/01. DS Kubernetes Service Overview|4.1 DS Kubernetes Service Overview]]
2. [[50. 운영/07. DKS User Guide/02. Harbor User Guide|4.2 Harbor User Guide]]
3. [[50. 운영/07. DKS User Guide/03. KubeSphere User Guide|4.3 KubeSphere User Guide]]
4. [[50. 운영/07. DKS User Guide/04. 해외 사업장 관련 DKS URL GSAMS 신청 가이드|4.4 GSAMS Application Guide for Accessing Domestic DKS URLs from SCS and SAS]]

### Troubleshooting Guide

1. [[50. 운영/08. 트러블슈팅/Harbor/01. Harbor 접속, 로그인 및 Image Push-Pull 오류|6.1 Harbor Access, Login, and Image Push/Pull Errors]]
2. [[50. 운영/08. 트러블슈팅/Kubernetes/01. Kubernetes Dashboard 접속 및 Token 로그인 가이드|6.2 Accessing Kubernetes Dashboard, Logging In, and Regenerating the Token]]
3. [[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|6.3 When a NetApp NFS PVC Is Bound but Pod Mount Fails]]
4. [[50. 운영/08. 트러블슈팅/KubeSphere/01. Project가 보이지 않거나 리소스 생성 권한이 없는 경우|6.4 When a Project Is Not Visible or You Do Not Have Permission to Create Resources]]
5. [[50. 운영/08. 트러블슈팅/KubeSphere/02. Private Image 배포 시 ImagePullBackOff가 발생하는 경우|6.5 KubeSphere ImagePullBackOff When Deploying a Private Image]]

---

# Part 1. User Manual

## 5. 4.1 DS Kubernetes Service Overview

### 5.1 Xi'an DKS를 사용자 관점으로 설명한다

| 구성 | 사용자 관점 역할 |
|---|---|
| KubeSphere Host | 로그인·Workspace·Project·권한을 중앙 관리 |
| PRD Member | 운영 Workload 실행 |
| DEV Member | 개발 Workload 실행 |
| Harbor | Private Container Image 저장·Pull·Push |
| NetApp Trident | PVC를 실제 Volume으로 Provision·Mount |
| Ingress·VIP-B | 사용자의 HTTP/HTTPS 요청을 Workload로 전달 |
| Bastion·VIP-A | 승인된 운영자·kubectl의 Kubernetes API 접근 |
| Prometheus·Grafana | Cluster와 Workload 상태 관측 |

사용자는 Host Console에서 Project를 선택할 수 있지만 실제 Pod는 대상 Member Cluster에서 실행된다.

```text
KubeSphere Host
→ 중앙 관리

PRD / DEV Member
→ 사용자 Workload 실행
```

Host를 사용자 HTTP 경로의 중간에 넣지 않는다.

### 5.2 접속 경계를 구분한다

```text
관리·API 경로
사용자 또는 운영자 → Bastion / kubeconfig → VIP-A → Kubernetes API

사용자 애플리케이션 경로
사용자 → DNS → VIP-B → Router / Ingress Controller → Ingress → Service → Endpoint → Pod

Image 경로
사용자 시스템 또는 Node → Harbor FQDN → Private Project / Repository → Image
```

### 5.3 Workspace·Project·Namespace

```text
Workspace
→ 상위 관리 범위

Project
= Kubernetes Namespace
→ Workload·PVC·Secret·Service·Ingress 작업 범위
```

DKS 1:1 운영 정책이 있더라도 Workspace와 Project의 기능은 다르다.

### 5.4 이용 시작 순서

1. 사용자 계정과 로그인 방식을 확인한다.
2. KubeSphere Dashboard·Harbor·Member Ingress 접근 방화벽을 확인한다.
3. 대상 PRD 또는 DEV와 Project 이름을 확정한다.
4. Workspace·Project·Role·Quota 신청을 완료한다.
5. Harbor Project와 Role을 확인한다.
6. Harbor CA trust·Login·Image 사용을 확인한다.
7. KubeSphere에서 PVC·Secret·Deployment·Service·Ingress를 구성한다.
8. 최종 HTTP 응답과 Resource 상태를 확인한다.

### 5.5 완료 증거

- 대상 Project가 올바른 Member Cluster에 있다.
- 사용자 Role이 신청 내용과 일치한다.
- Quota가 승인값과 일치한다.
- Harbor에 필요한 Project·Role이 있다.
- 사용자가 대상 UI·FQDN에 접근한다.
- Workload가 Member에 실행된다.
- 최종 애플리케이션 HTTP 응답을 확인한다.

## 6. 4.2 Harbor User Guide

### 6.1 전체 사용자 흐름

```text
AD·사용 권한 확인
→ 사용자 Source에서 Harbor 80/443 접근
→ 승인된 2-Tier Root CA 설치
→ Docker daemon에 CA trust 반영
→ docker login
→ Image Pull
→ 로컬 Image 확인
→ 대상 Repository로 Tag
→ Image Push
→ Harbor Artifact·Tag·Digest 확인
```

### 6.2 Network와 계정 전제

- 사용자 Source IP에서 Xi'an Harbor의 TCP 80/443 연결
- Harbor FQDN과 DNS 해석
- 승인된 AD 계정
- Harbor Project Member Role
- Docker 또는 승인된 Container Client
- OS CA trust 변경 권한
- 승인된 `SECDS-2TROOTCA.crt`

과거 Global AD Group·DS Pass·GSAMS 경로가 Xi'an에서 그대로 유효한지는 현지 운영팀에 확인한다.

### 6.3 CA trust

```text
Root CA 파일 확인
→ OS trust anchor에 배치
→ CA trust 갱신
→ Docker daemon 재시작
→ docker login 재시도
```

반드시 구분한다.

```text
브라우저가 Harbor HTTPS를 신뢰
≠ Docker daemon이 같은 CA를 신뢰
```

Docker가 x509를 반환하면 Harbor 서비스 Down보다 사용자 시스템의 CA trust를 먼저 본다.

### 6.4 Login

```text
sudo docker login xa.dcr.dks.samsungds.net
Username: <approved-account>
Password: <not-recorded>
```

정상 증거:

```text
Login Succeeded
```

Docker Credential이 파일에 저장될 수 있으므로 승인된 Credential Helper 정책을 확인하고 Password를 로그·교육 노트에 남기지 않는다.

### 6.5 Pull

Image 주소는 다음 요소로 읽는다.

```text
<registry>/<project>/<repository>:<tag>
```

확인할 것:

- Registry FQDN
- Harbor Project
- Repository
- Tag
- 계정의 Pull 권한
- 실제 Digest

`manifest unknown`이면 인증부터 다시 만들지 않고 Repository·Tag 존재 여부를 확인한다.

### 6.6 Tag와 Push

```text
로컬 Image:Tag
→ Harbor 대상 주소로 Tag
→ Push
→ Harbor UI에서 Artifact·Tag·Digest 확인
```

Push 실패에서 구분할 것:

- 로컬 Source Image 없음
- Tag 주소 오타
- 다른 Harbor Project
- Developer 또는 ProjectAdmin Role 없음
- Project Quota 초과
- Harbor Disk 문제

### 6.7 완료 증거

```text
DNS·443 연결
+ HTTPS 응답
+ Docker CA trust
+ Login Succeeded
+ Pull 성공
+ 로컬 Image 확인
+ Tag 생성
+ Push 성공
+ Harbor Artifact·Tag·Digest 일치
```

## 7. 4.3 KubeSphere User Guide

### 7.1 정상 애플리케이션 경로

```text
Harbor Image
+ Image Registry Secret
→ Deployment
→ Pod

StorageClass
→ PVC
→ PV
→ Pod Mount
→ Container Write/Read

User
→ DNS / VIP-B
→ Ingress
→ Service
→ Endpoint
→ Pod
→ HTTP 응답
```

### 7.2 사용자 권한과 대상

- Project = Namespace
- 신청서 Admin = 기본 `project-operator`
- 신청서 User = 기본 `project-viewer`
- `project-admin`은 별도 정책
- Workload는 PRD 또는 DEV Member에서 실행
- KubeSphere Host는 중앙 관리

### 7.3 PVC 생성

확인할 값:

| 항목 | 의미 |
|---|---|
| Name | Project 내 PVC 식별자 |
| StorageClass | 실제 Xi'an Member의 승인된 Storage 정책 |
| Access Mode | 애플리케이션 요구와 Driver 지원 일치 |
| Capacity | 승인 Quota 내 요청량 |
| Namespace | 현재 Project |

완료는 `Bound`에서 끝나지 않는다.

```text
PVC Bound
→ Pod에 연결
→ Node Mount
→ Container에서 사용
```

### 7.4 Image Registry Secret

- Deployment와 같은 Project에 생성한다.
- Type은 Image Registry 정보다.
- Registry 주소는 실제 Harbor FQDN이다.
- 계정은 해당 Private Project 접근 권한이 있어야 한다.
- Secret Data를 출력하지 않는다.
- Deployment `imagePullSecrets`에 명시적으로 연결한다.

```text
Secret 존재
≠ Deployment가 Secret을 참조
```

### 7.5 Deployment

확인할 값:

- Name·Namespace
- Replicas
- 실제 Harbor Image·Tag
- Pod label
- Deployment selector
- CPU·Memory Requests·Limits
- Image Pull Secret
- PVC Volume·Mount path
- Node selector·toleration이 필요한지
- Rollout Strategy

완료 증거:

- Deployment Available
- 원하는 Replica 수
- 새 Pod Ready
- Image Pull 성공 Event
- PVC Mount 성공
- Application Listen Port 정상

### 7.6 Service와 Endpoint

```text
Service selector
↔ Pod label
→ Endpoint 생성
```

Service가 존재해도 Endpoint가 비어 있으면 요청이 Pod에 전달되지 않는다.

확인할 값:

- Service Name·Namespace
- Selector
- Port·TargetPort
- Protocol
- Endpoint Address·Port
- 대상 Pod Ready

### 7.7 Ingress / Route

```text
승인된 FQDN
→ 대상 환경의 Domain
→ VIP-B
→ Ingress Controller
→ Ingress Rule
→ Service·Port
```

PRD와 DEV Domain을 혼용하지 않는다. Ingress 생성 후 다음을 본다.

- Host·Path
- Backend Service·Port
- Address
- Event
- DNS 해석
- VIP-B 연결
- 실제 HTTP 상태 코드와 내용

### 7.8 YAML과 UI의 관계

UI에서 만든 객체도 Kubernetes Resource다. 교육생이 다음 필드를 읽을 수 있어야 한다.

```text
metadata.namespace
spec.selector
spec.template.metadata.labels
spec.imagePullSecrets
spec.containers[].image
spec.volumes
spec.volumeMounts
Service port / targetPort
Ingress backend.service
```

### 7.9 Autoscaling

- Metrics API가 정상인지 확인한다.
- CPU Target은 Request 대비 사용률이다.
- Memory Target의 단위와 의미를 확인한다.
- Minimum·Maximum Replicas를 구분한다.
- Requests가 없으면 CPU 기반 판단이 성립하지 않을 수 있다.
- 부하 생성·Scale 변경은 승인된 실습에서만 수행한다.

### 7.10 최종 정상 증거

```text
Image Pull 성공
+ Pod Ready
+ PVC Mount·Write/Read 성공
+ Service Endpoint 존재
+ Ingress Backend 일치
+ DNS·VIP-B 경로 정상
+ 사용자 HTTP 응답 정상
```

## 8. 4.4 GSAMS Application Guide

### 8.1 발동 조건

SCS·SAS 등 해외 사업장에서 국내 GH/HS의 DKS 서비스 URL에 접속해야 할 때 적용한다. 보안그룹 안내상 GSAMS FQDN 메뉴가 국내 출발지 신청에 한정된다면, 해외 출발지는 **GSAMS 방화벽 신청서** 형식으로 상신한다.

### 8.2 신청서 입력 기준

| 항목 | 입력 |
|---|---|
| 신청 제목 | `[FQDN]` 포함 |
| 목적지 IP | `1.1.1.1` |
| Port | `80/443` |
| 상신 의견 | 실제 접속할 개별 DKS 서비스 URL |

`1.1.1.1`은 해당 신청 방식에서 목적지 IP 필드에 입력하도록 안내된 값이다. 실제 대상은 상신 의견의 URL로 식별한다.

### 8.3 작성 예시 구조

```text
신청 제목: [FQDN] <신청 목적>
목적지 IP: 1.1.1.1
Port: 80/443
상신 의견:
접속이 필요한 URL: <실제 DKS 서비스 URL>
```

### 8.4 제출 전 확인

- 해외 사업장 출발지에 해당하는가
- FQDN 메뉴가 아니라 방화벽 신청서 대상인가
- 제목에 `[FQDN]`이 있는가
- 목적지 IP와 Port 입력값이 안내와 일치하는가
- Wildcard나 예시 URL이 아니라 실제 개별 URL인가
- 신청 목적이 명확한가
- URL의 유효성은 별도 기준에서 확인했는가

### 8.5 이 가이드가 정하지 않는 것

- 개별 URL의 실제 유효성
- 신청 승인 여부
- 승인 담당자
- 승인 후 통신 테스트 방법
- DNS 생성·LB·Ingress 구성

이 항목을 가이드 밖에서 추측해 추가하지 않는다.

---

# Part 2. Troubleshooting Guide

## 9. 공통 초동 판단 순서

모든 사례에서 같은 순서를 사용한다.

```text
1. 대상 고정
Cluster·context·Project·사용자·시각·URL·Pod

2. 증상 원문
오류 문자열·상태 코드·Event·실제 화면

3. 정상 경로와 비교
어디까지 성공했고 어디서 처음 달라졌는가

4. 정보 신뢰성
현재 대상의 출력인가, 과거·다른 Cluster 예시인가

5. 다음 분기 확인
결과 A/B에 따라 조사 방향이 달라지는 읽기 전용 확인

6. 조치 경계
직접 수정, 승인 필요, 다른 담당자 에스컬레이션

7. 동일 경로 재검증
최종 사용자 결과까지 확인
```

### 좋은 첫 확인의 조건

- 결과에 따라 다음 행동이 실제로 달라진다.
- 상태를 바꾸지 않는다.
- 대상과 실패 단계를 좁힌다.
- 한 번에 여러 가설을 섞지 않는다.
- 현재 증거로 답할 수 있다.

## 10. 6.1 Harbor Access, Login, and Image Push/Pull Errors

### 10.1 정상 경로

```text
DNS
→ Harbor IP:443
→ HTTPS
→ Server Certificate
→ Client CA trust
→ /v2/ Registry API
→ Account Authentication
→ Private Project Role
→ Repository / Tag
→ Pull / Push
→ Artifact / Digest
```

### 10.2 웹은 열리는데 Docker x509

확인된 사실:

- Browser HTTPS는 열림
- Docker Login은 `x509: certificate signed by unknown authority`

첫 판단:

```text
Harbor Network와 HTTPS 응답
≠ Docker daemon의 CA trust
```

확인 순서:

1. 승인된 Root CA 파일이 있는가
2. OS trust anchor 경로에 배치됐는가
3. CA trust 갱신을 했는가
4. Docker daemon을 재시작했는가
5. FQDN이 Certificate와 일치하는가
6. `docker login`을 재시도했는가

### 10.3 웹·Docker 모두 인증 실패

```text
HTTPS /는 200
/v2/는 인증 없이 401
docker login은 unauthorized
```

이 경우 Registry가 응답하는지와 계정 인증을 분리한다.

- 계정 문자열
- 비밀번호
- AD 로그인 가능 여부
- Harbor 사용 권한
- Project Member 여부

### 10.4 Login 성공, Pull 실패

오류 문자열에 따라 분기한다.

| 메시지 | 우선 확인 |
|---|---|
| `manifest unknown` | Repository·Tag·Artifact 존재 |
| `pull access denied` | Project Role·Secret Account |
| `repository does not exist` | Project·Repository 이름 |
| `x509` | CA trust |
| timeout | DNS·Network·443 |

### 10.5 Push 실패

```text
로컬 Image 존재
→ 대상 주소로 Tag
→ Login 상태
→ Project Role
→ Quota
→ Push
→ Harbor Artifact·Digest
```

Developer와 ProjectAdmin은 읽기·쓰기가 가능하지만 Viewer 성격의 권한은 Push할 수 없다.

### 10.6 웹 자체가 열리지 않음

```text
DNS 해석
→ Harbor IP
→ TCP 443
→ HTTPS Header
```

DNS·443·HTTPS가 모두 실패하면 Application Layer보다 Source IP·방화벽·Network 경로부터 확인한다.

### 10.7 정상 복구 증거

- 웹 HTTPS 정상
- `/v2/` 기대 상태 코드
- `docker login` 성공
- 승인 Image Pull 성공
- 승인 Image Push 성공
- Harbor UI의 Artifact·Tag·Digest 일치

## 11. 6.2 Kubernetes Dashboard Access and Token Login

### 11.1 대상 Cluster가 먼저다

Dashboard URL은 Cluster별로 다르다.

| Cluster | Dashboard URL |
|---|---|
| `prd-host-pa01-xas` | `https://dashboard.apps.xaprdpa01.mgmt.dks.samsungds.net` |
| `prd-apps-pa01-xas` | `https://dashboard.apps.xaprdpa01.apps.dks.samsungds.net` |
| `dev-apps-pa01-xas` | `https://dashboard.apps.xadevpa01.apps.dks.samsungds.net` |

URL을 열기 전에 대상 Cluster와 목적을 고정한다. Host Dashboard Token을 Member에 사용하거나 반대로 사용하지 않는다.

### 11.2 정상 Token 로그인 구조

```text
대상 Cluster context
→ kubernetes-dashboard Namespace
→ admin-user ServiceAccount
→ service-account-token Secret
→ Token 존재 확인
→ 대상 Dashboard URL
→ Token 로그인
→ Namespace·Node·Workload 조회
```

Token 원문은 교육 자료·로그·스크린샷에 남기지 않는다.

### 11.3 ServiceAccount와 Secret 확인

확인할 것:

- `admin-user` ServiceAccount 존재
- 연결된 Secret Type이 `kubernetes.io/service-account-token`
- Secret Data가 기대 필드를 갖는가
- Token 값 자체가 아니라 존재·연결 상태
- RBAC Binding이 유지되는가

### 11.4 새 Token Secret 생성

기존 Secret을 먼저 삭제하지 않는다.

```text
새 service-account-token Secret 생성
→ Controller가 Token Data를 채움
→ 새 Token으로 로그인 확인
→ 정상일 때 기존 Secret 삭제
```

기존 Token을 먼저 삭제하면 새 Token 생성·로그인이 실패할 때 즉시 접근을 잃을 수 있다.

### 11.5 실패 분기

```text
Dashboard URL 자체가 안 열림
→ DNS·VIP-B·Ingress·Service·Pod

로그인 화면은 열림, Token 거부
→ 대상 Cluster·Token Secret·RBAC·Token 복사 상태

admin-user 없음
→ ServiceAccount·RBAC 복구 여부 확인

새 Secret DATA 미생성
→ Annotation·ServiceAccount 이름·Controller 상태

로그인 성공, 일부 Resource 조회 거부
→ RBAC 범위
```

### 11.6 완료 증거

- 올바른 Cluster URL
- `admin-user`와 Token Secret 정상
- 새 Token 사용 시 로그인 성공
- 승인 범위 Resource 조회
- 기존 Token 교체가 필요하면 새 Token 검증 후 구 Token 삭제
- Token 원문 미노출

## 12. 6.3 NetApp NFS PVC Bound but Pod Mount Fails

### 12.1 문제 구조

```text
PVC = Bound
Trident Backend = online
Pod = ContainerCreating
Event = FailedMount / exit status 32
```

이 상태는 모순이 아니다.

```text
PVC Bound
→ Provisioning 성공

Pod FailedMount
→ Node에서 실제 NFS Mount 실패
```

### 12.2 먼저 하지 않을 것

- PVC·StorageClass 즉시 삭제·재생성
- Trident 전체 재설치
- Pod 반복 삭제
- 모든 Node Route 일괄 변경
- Export policy를 근거 없이 전체 허용

### 12.3 확인 순서

1. PVC·PV·StorageClass 상태
2. Pod가 배치된 Node
3. Pod Event의 Data LIF와 export path
4. Trident Backend `online`
5. 해당 Node에서 Data LIF로 가는 Route와 Source IP
6. TCP 2049
7. 같은 export path의 Node direct mount
8. Mount 성공 시 kubelet·CSI·Trident Node 상태
9. Mount 실패 시 오류 문자열로 Network·Export policy·Path 분기

### 12.4 좋은 분기 확인

```text
Node에서 같은 NFS export를 직접 mount할 수 있는가?

성공
→ Node→Data LIF→export→read/write 통과
→ kubelet / CSI / Pod 쪽으로 좁힘

실패
→ Route / Network / 2049 / Export policy / Path로 좁힘
```

### 12.5 오류별 담당 영역

| 오류 | 우선 영역 |
|---|---|
| No route to host | Node Routing·Network |
| Connection timed out | 방화벽·Data LIF·Network |
| access denied by server | Export policy·실제 Source IP |
| No such file or directory | export path·qtree |
| Direct mount 성공, Pod 실패 | kubelet·CSI·Trident Node |

### 12.6 정상 복구 증거

```text
Pod Running·Ready
+ 새 FailedMount Event 없음
+ Container에서 df / mount 확인
+ Write·Read 성공
```

## 13. 6.4 Project Not Visible or Permission Missing

### 13.1 확인 순서

```text
Project / Namespace 존재
→ Workspace Member
→ Project Member
→ Project Role
→ Quota·정책
→ 실제 UI·API 권한
```

### 13.2 Project 자체가 없는 경우

```text
kubectl get namespace <project>
→ NotFound
```

Project 생성 미완료 또는 이름 불일치다. 멤버십을 수정하기 전에 1.1 생성 절차로 돌아간다.

### 13.3 Namespace는 Active, 사용자 화면에 없음

Project 생성보다 멤버십을 본다.

- Workspace Members에 사용자가 있는가
- Project Members에 사용자가 있는가
- 계정 문자열이 맞는가
- 사용자 재로그인이 필요한가

### 13.4 Project는 보이지만 Create 메뉴 없음

```text
신청 Permission = User
Project Role = project-viewer
→ 조회 전용이 정상
```

장애로 보고 권한을 올리지 않는다.

```text
신청 Permission = Admin
Project Role = project-viewer
→ 잘못된 매핑 가능
→ project-operator 검토
```

`project-operator`에게 Member 관리 메뉴가 없는 것은 정상이다.

### 13.5 Role 수정 후 검증

- 사용자 재로그인
- 대상 Project 진입
- Workload·PVC·Secret 조회
- 승인된 작은 리소스 생성 또는 읽기 전용 권한 확인
- Member 관리 권한은 없는지 확인
- Quota 초과 오류와 RBAC 오류를 분리

### 13.6 완료 증거

- Project/Namespace 존재
- Workspace·Project Member 등록
- Role이 신청 Permission과 일치
- viewer는 조회만 가능
- operator는 승인 리소스 생성 가능
- 불필요한 project-admin 부여 없음

## 14. 6.5 KubeSphere ImagePullBackOff with Private Image

### 14.1 확인 순서

```text
Pod Event
→ Deployment Image 경로·Tag
→ 같은 Namespace의 Image Registry Secret
→ Secret Type
→ Deployment imagePullSecrets 연결
→ Harbor 계정·Project Role
→ 새 Pod Pull Event
```

### 14.2 Event가 시작점인 이유

`ImagePullBackOff`는 최종 상태 이름이다. 실제 원인은 Event Message에 나온다.

| Event 문자열 | 우선 확인 |
|---|---|
| `manifest unknown` | Repository·Tag |
| `pull access denied` | Secret·Harbor Role |
| `repository does not exist` | Project·Repository 이름 |
| `x509` | Node 또는 KubeSphere CA trust |
| timeout | DNS·Network·443 |

### 14.3 Image 경로

```text
xa.dcr.dks.samsungds.net/<project>/<repository>:<tag>
```

다음 중 하나라도 틀리면 Secret을 다시 만들어도 해결되지 않는다.

- Registry FQDN
- Harbor Project
- Repository
- Tag

### 14.4 Secret

- Deployment와 같은 Namespace
- Type = `kubernetes.io/dockerconfigjson`
- 실제 Harbor 계정 사용
- Secret Data 원문 미출력
- 계정의 Project Pull 권한

### 14.5 Deployment 연결

```yaml
spec:
  template:
    spec:
      imagePullSecrets:
        - name: <approved-secret>
```

Secret이 존재해도 이 연결이 없으면 사용되지 않는다.

### 14.6 수정 후 검증

```text
Deployment 저장
→ 새 ReplicaSet / Pod
→ Pod Event: Pulling
→ Pulled
→ Created
→ Started
→ Pod Ready
```

기존 실패 Pod의 상태만 보지 않고 새 Pod와 새 Event를 확인한다.

### 14.7 완료 증거

- 실제 Image·Tag가 Harbor에 존재
- 같은 Namespace에 올바른 Secret
- `imagePullSecrets` 연결
- Harbor 계정에 Pull 권한
- 새 Pod Event에서 `Successfully pulled`
- Pod Ready

---

# Part 3. 통합 훈련과 판정

## 15. 정상 시나리오 한 건을 끝까지 따라간다

```text
사용자 계정·방화벽
→ Workspace·Project·Role·Quota
→ Harbor Project·Role
→ CA trust·docker login
→ Image Pull / Tag / Push
→ Harbor Artifact 확인
→ KubeSphere Image Secret
→ PVC
→ Deployment / Pod
→ Service / Endpoint
→ Ingress / VIP-B
→ HTTP 응답
```

교육생은 각 화살표마다 다음을 적는다.

- 어떤 객체인가
- 어디에서 확인하는가
- 성공 증거는 무엇인가
- 실패하면 어느 Troubleshooting Guide를 보는가
- 실제값은 어디서 다시 확인하는가

## 16. 증상에서 Guide 선택 훈련

| 증상 | Guide | 첫 확인 |
|---|---|---|
| Harbor 웹·Docker 접속 실패 | 6.1 | DNS·443·HTTPS |
| Docker만 x509 | 6.1 | Client CA trust |
| Dashboard Token 거부 | 6.2 | Cluster·ServiceAccount·Token Secret |
| PVC Bound, Pod ContainerCreating | 6.3 | Pod Event·Node Mount |
| Project 안 보임 | 6.4 | Namespace·Workspace·Project Member |
| Project 보임, Create 없음 | 6.4 | 신청 Permission·Project Role |
| Private Image Pod가 ImagePullBackOff | 6.5 | Pod Event |

## 17. 강사 진행 순서

1. 4.1 구조로 Host·Member·Harbor·접속 경계를 설명한다.
2. 4.2에서 실제 Harbor 사용자 흐름을 CA부터 Artifact까지 연결한다.
3. 4.3에서 PVC·Secret·Deployment·Service·Ingress를 하나의 정상 앱으로 연결한다.
4. 4.4의 해외 GSAMS 적용 조건과 입력값을 사례로 작성한다.
5. 오후에는 정상 경로 지도를 다시 놓고 다섯 증상을 하나씩 추가한다.
6. 교육생이 Guide를 선택하고 첫 읽기 전용 확인을 말하게 한다.
7. 강사는 다음 확인 결과를 단계적으로 제공한다.
8. 교육생이 정상과 차이, 첫 단절, 조치 경계를 설명한다.
9. 마지막에 같은 정상 경로로 복구 결과를 확인한다.

## 18. 교육 중 피할 방식

- Harbor 웹 성공을 Docker·Project 권한 성공으로 확대
- PVC Bound를 Storage 사용 완료로 설명
- Secret 존재를 Deployment 연결 완료로 설명
- Pod Running을 사용자 서비스 정상으로 설명
- Project가 안 보인다는 이유로 무조건 project-admin 부여
- ImagePullBackOff에서 Event를 보지 않고 Secret부터 재생성
- Dashboard Token을 화면에 노출
- GSAMS 예시 URL을 실제 URL로 제출
- 다른 Cluster의 URL·VIP·StorageClass·Token을 현재값으로 사용
- 증상 설명 직후 원인 정답과 변경 명령을 먼저 제공

## 19. 숙지 수준 분류

### A. 문서 없이 설명할 것

- [ ] Host·Member·Harbor·Project 관계
- [ ] VIP-A 관리 경로와 VIP-B 사용자 경로
- [ ] Harbor CA→Login→Pull→Tag→Push 흐름
- [ ] Image Secret→Deployment→Pod 흐름
- [ ] PVC Bound→Mount→Write/Read 흐름
- [ ] Service selector→Endpoint 관계
- [ ] Ingress→VIP-B→HTTP 경로
- [ ] GSAMS 해외 사업장 적용 조건과 핵심 입력
- [ ] Harbor 오류의 Network·CA·Auth·Tag·Role 분리
- [ ] Dashboard Token 교체 시 새 Secret 우선 원칙
- [ ] NFS Provisioning과 Mount 차이
- [ ] Project Member와 Role 분리
- [ ] ImagePullBackOff의 Event 우선 원칙

### B. Manual을 보며 수행·설명할 것

- [ ] Harbor CA trust·Login·Pull·Push 명령 위치
- [ ] Harbor Artifact 확인 위치
- [ ] KubeSphere PVC·Secret·Deployment·Service·Ingress UI 경로
- [ ] GSAMS 신청서 입력값
- [ ] Dashboard ServiceAccount·Token Secret 확인 경로
- [ ] NFS Route·2049·direct mount 절차
- [ ] Workspace·Project Member·Role 확인 화면
- [ ] Pod Event·Secret Type·imagePullSecrets 확인 명령

### C. 현장에서 다시 확인할 것

- 실제 사용자·교육 계정
- 실제 Project·Role·Quota
- 실제 Harbor Project·Repository·Tag
- 실제 승인 Root CA
- 실제 KubeSphere Dashboard URL
- 실제 Dashboard Token Secret 이름
- 실제 StorageClass·PVC·Pod Node·Data LIF
- 실제 GSAMS 대상 URL
- 실제 Ingress Host·VIP-B·HTTP 결과
- 실제 담당자와 에스컬레이션 경계

## 20. 자가점검

| 질문 | 상태 | 막힌 부분 | 돌아갈 문서 |
|---|---|---|---|
| DKS 사용자 이용 흐름을 처음부터 끝까지 설명하는가? | 미평가 |  | 4.1 |
| Harbor Login과 Project Pull 권한을 분리하는가? | 미평가 |  | 4.2·6.1 |
| PVC·Secret·Deployment·Service·Ingress를 연결하는가? | 미평가 |  | 4.3 |
| GSAMS 적용 조건과 입력값을 설명하는가? | 미평가 |  | 4.4 |
| Dashboard 대상 Cluster와 Token을 구분하는가? | 미평가 |  | 6.2 |
| PVC Bound와 Node Mount를 구분하는가? | 미평가 |  | 6.3 |
| Project 존재·멤버·Role을 순서대로 확인하는가? | 미평가 |  | 6.4 |
| ImagePullBackOff에서 Event를 먼저 읽는가? | 미평가 |  | 6.5 |
| 복구 후 최종 HTTP 또는 기능 결과까지 확인하는가? | 미평가 |  | 전체 |

## 21. 직접 연습

### 연습 1 — 정상 경로 지도

```text
Account / Firewall
→ Workspace / Project / Role / Quota
→ Harbor Project / Role
→ CA / Login / Pull / Tag / Push
→ Image Secret
→ PVC / Mount
→ Deployment / Pod
→ Service / Endpoint
→ Ingress / VIP-B
→ HTTP
```

각 화살표에 확인 화면·객체·상태를 하나씩 붙인다.

### 연습 2 — Harbor 오류 문자열 카드

```text
x509
unauthorized
manifest unknown
pull access denied
timeout
```

각 문자열에서 다음 확인이 어떻게 달라지는지 말한다.

### 연습 3 — Dashboard Token 교체 순서

```text
기존 admin-user 확인
→ 새 Token Secret 생성
→ DATA 생성 확인
→ 새 Token 로그인
→ 정상 확인
→ 기존 Secret 삭제
```

삭제를 먼저 했을 때 위험을 설명한다.

### 연습 4 — NFS 분기 카드

```text
PVC Bound
Pod FailedMount
Backend online
Route 정상
TCP 2049 정상
Direct mount 결과 = 성공 / 실패
```

두 결과에서 다음 조사 방향을 각각 작성한다.

### 연습 5 — Project 권한 카드

```text
A. Namespace 없음
B. Namespace Active, Workspace Member 없음
C. Workspace Member O, Project Member 없음
D. Project viewer, 신청 User
E. Project viewer, 신청 Admin
F. project-operator, Create 실패 + Quota 초과
```

각 사례에서 정상·오류와 다음 확인을 구분한다.

### 연습 6 — ImagePullBackOff 카드

```text
Event: manifest unknown
Event: pull access denied
Event: x509
Event: timeout
```

Secret을 재생성하기 전에 확인할 것을 말한다.

### 연습 7 — GSAMS 신청 작성

실제값을 넣지 않은 템플릿으로 다음을 작성한다.

```text
신청 제목
목적지 IP
Port
상신 의견의 실제 URL 위치
적용 조건
이 가이드가 정하지 않는 항목
```

## 22. 예상 질문

| 예상 질문 | 답변 핵심 | 현재 답변 가능 여부 |
|---|---|---|
| KubeSphere Host에서 사용자 Pod가 실행되나요? | 중앙 관리와 Member Workload 실행 분리 | 미평가 |
| Harbor 웹에 로그인되면 Docker도 되나요? | Docker CA trust·Credential 별도 | 미평가 |
| Pull이 되는데 Push가 안 되는 이유는? | Project Write Role·Quota·Tag 확인 | 미평가 |
| PVC Bound면 데이터 사용 가능한 것 아닌가요? | Node Mount·Write/Read 별도 | 미평가 |
| Secret을 만들었는데 왜 Image Pull이 실패하나요? | Namespace·Type·imagePullSecrets·Tag·Role 확인 | 미평가 |
| Service가 있는데 왜 접속이 안 되나요? | Endpoint·Ingress·VIP-B·HTTP 구간 확인 | 미평가 |
| Dashboard Token을 그냥 새로 만들면 되나요? | 대상 Cluster와 기존 접근 보존 후 새 Token 검증 | 미평가 |
| Project가 안 보이면 권한을 높이면 되나요? | Namespace→Workspace Member→Project Member→Role 순서 | 미평가 |
| ImagePullBackOff면 Secret 문제인가요? | Event 문자열에 따라 Tag·권한·CA·Network 분기 | 미평가 |
| GSAMS에 실제 DKS IP를 넣는 것 아닌가요? | 안내된 해외 FQDN 신청 형식의 `1.1.1.1`과 상신 의견 URL 구분 | 미평가 |

## 23. 현장 기록 양식

```text
교육일: 2026-08-28
오전 User Manual
4.1 Service Overview 이해 결과: ______________________
4.2 Harbor User 흐름 결과: __________________________
4.3 KubeSphere 정상 시나리오 결과: __________________
4.4 GSAMS 신청 작성 결과: ___________________________

오후 Troubleshooting
6.1 Harbor 분기 결과: _______________________________
6.2 Dashboard Token 분기 결과: ______________________
6.3 NFS Mount 분기 결과: ____________________________
6.4 Project·권한 분기 결과: _________________________
6.5 ImagePullBackOff 분기 결과: ______________________

실제 환경에서 확인할 값: ____________________________
미해결 질문: ________________________________________
다른 담당 영역으로 넘길 항목: ________________________
민감정보 노출 없음: __________________________________
```

## 24. 8/28 완료 기준

- [ ] 교육생이 DKS의 Host·Member·Harbor·Project 관계를 설명한다.
- [ ] Harbor 사용자 흐름을 CA trust부터 Artifact 확인까지 설명한다.
- [ ] Harbor 웹·Docker Login·Project Pull/Push 권한을 분리한다.
- [ ] KubeSphere에서 PVC·Image Secret·Deployment·Service·Endpoint·Ingress·HTTP를 연결한다.
- [ ] `PVC Bound ≠ Mount`, `Secret 존재 ≠ 사용`, `Pod Running ≠ HTTP 성공`을 설명한다.
- [ ] GSAMS 해외 사업장 신청의 적용 조건과 입력값을 설명한다.
- [ ] Harbor 오류를 Network·CA·Auth·Tag·Role로 분리한다.
- [ ] Dashboard Token을 대상 Cluster와 ServiceAccount·Secret 구조로 설명한다.
- [ ] 새 Dashboard Token 검증 전에 기존 Token을 삭제하지 않는다.
- [ ] NFS 사례에서 direct mount 결과로 다음 조사 방향을 나눈다.
- [ ] Project 권한 사례에서 Namespace·Workspace Member·Project Member·Role·Quota를 순서대로 본다.
- [ ] ImagePullBackOff에서 Pod Event를 먼저 읽고 Image·Secret·Role을 대조한다.
- [ ] Token·Password·Secret·Private Key를 노출하지 않는다.
- [ ] 교육생이 다섯 증상에서 올바른 Troubleshooting Guide를 60초 안에 선택한다.
- [ ] 복구 후 동일 정상 경로의 최종 기능 결과를 확인한다.

## 25. 8/29~30과 연결

주말에는 8/26~8/28의 운영 교육을 축약하지 않고 다음 기준으로 보완한다.

```text
Manual별 미완료 설명
→ 교육생 질문 주차장
→ 실제 환경값 확인 필요 목록
→ 시연 실패·접근 제한 기록
→ 8/31 신규 Member 구축에서 다시 확인할 개념 연결
→ 구축 자료·계정·VM·Bastion·Inventory·Storage 준비
```

관련 문서: [[2026-08-29~30 운영 교육 보완 및 구축 준비|2026-08-29~30 운영 교육 보완 및 구축 준비]]

---

## 26. 제한된 준비시간을 반영한 현장 실행 전략

> [!important] 적용 원칙
> 8/28 오전은 사용자가 DKS를 이용하는 정상 경로를 한 번 연결하고, 오후는 증상별로 올바른 Troubleshooting Guide와 첫 확인을 선택하게 하는 날이다. **교육용 Application이나 장애 환경을 새로 만들지 않고, 기존 정상 환경의 읽기 전용 조회와 현재 Guide 안의 절차·출력만 사용한다.**

### 26.1 오전 기준 대상 — 기존 사용자 경로 한 세트

가능하면 다음 두 대상을 미리 정한다.

```text
기존 Harbor Private Project·Repository·Tag 1개
+
기존 KubeSphere Project·Application 1개
```

두 대상이 실제로 연결된 Application이면 가장 좋지만, 교육을 위해 새로 맞추지 않는다. 다음 정상 경로를 같은 대상 기준으로 따라간다.

```text
계정·방화벽
→ Harbor Project·Repository·Image
→ KubeSphere Workspace·Project
→ Image Secret 존재 여부
→ PVC
→ Deployment·Pod
→ Service·Endpoint
→ Ingress·VIP-B
→ 사용자 HTTP
```

적합한 기존 Application이 없거나 조회 권한이 없으면 `4.1~4.4` User Manual의 화면·명령·정상 결과를 순서대로 사용한다.

### 26.2 오전 User Manual 진행 수준

| 범위 | 현장 우선 방식 | 이번 교육에서 하지 않을 것 |
|---|---|---|
| `4.1` Service Overview | 전체 이용 흐름과 Host·Member·Harbor 관계 설명 | 별도 시연 환경 구성 |
| `4.2` Harbor User Guide | 기존 Project·Repository·Artifact·Tag를 읽기 전용으로 조회하고 CLI는 Manual 출력으로 설명 | CA 설치·`docker login`·Pull·Tag·Push 실제 실행 |
| `4.3` KubeSphere User Guide | 기존 Project의 PVC·Deployment·Pod·Service·Endpoint·Ingress를 한 경로로 조회 | 신규 Secret·PVC·Deployment·Service·Route 생성 |
| `4.4` GSAMS Guide | 신청 조건과 입력 필드를 템플릿으로 작성 | 실제 신청 상신·승인·통신 변경 |

`4.3`에서 Secret은 이름·Type·연결 여부까지만 확인하고 값은 열지 않는다. 기존 Application을 조회할 때에도 Resource를 각각 독립적으로 소개하기보다 `Image → Pod → Service → Ingress → HTTP`, `PVC → Mount` 연결을 유지한다.

### 26.3 오후 Troubleshooting의 범위 조절

먼저 `6.1~6.5` 다섯 Guide를 증상과 연결한다.

| 증상 | 선택할 Guide | 첫 확인 |
|---|---|---|
| Harbor 접속·로그인·Push/Pull 오류 | `6.1` | 웹·Docker·Pull·Push 중 어느 단계인지와 오류 원문 |
| Dashboard 접속·Token 로그인 문제 | `6.2` | 대상 Cluster와 현재 ServiceAccount·Token Secret |
| PVC Bound 후 Pod Mount 실패 | `6.3` | Pod Event의 `FailedMount`와 Pod가 배치된 Node |
| Project가 안 보이거나 Create 권한 없음 | `6.4` | Namespace 존재 여부 |
| Private Image `ImagePullBackOff` | `6.5` | Pod Event의 실제 Pull 오류 문자열 |

다섯 사례를 모두 같은 깊이로 설명하지 않는다. 제한된 준비시간에서는 다음 두 사례를 상세 진행 대상으로 삼는다.

```text
6.4 Project·권한 문제
→ 8/26 Workspace·Project·Member·Role과 직접 연결

6.5 ImagePullBackOff
→ 8/27 Harbor Project·Role과 오전 4.3 Image Secret·Deployment를 연결
```

`6.1`, `6.2`, `6.3`은 Guide 선택과 첫 분기, 완료 또는 에스컬레이션 위치까지만 확인한다. 현장 질문이나 실제 증상이 있는 경우에만 해당 Guide를 더 깊게 따라간다.

### 26.4 별도 장애 자료 없이 사례를 진행하는 방법

Troubleshooting Guide 안에 이미 포함된 상태와 Console 출력을 순서대로 사용한다. 별도의 장애 캡처나 로그 묶음을 만들 필요가 없다.

```text
1. 제목과 최초 증상만 제시
2. 교육생이 사용할 Guide를 선택
3. 대상 Cluster·Project·사용자·Pod를 고정
4. Guide의 첫 번째 읽기 전용 결과를 확인
5. 결과에 따라 다음 절로 이동
6. 정상 완료 증거 또는 담당 영역 전환을 말함
```

Guide의 아래쪽 정답을 처음부터 모두 읽지 않는다. 현재 확인 결과에 해당하는 다음 절만 열어 진행한다. 문서 자체를 단계별 시뮬레이션 자료로 사용한다.

### 26.5 준비 우선순위

#### 반드시 준비할 것

- User Manual `4.1~4.4`와 Troubleshooting Guide `6.1~6.5` 링크를 바로 열 수 있게 한다.
- 가능하면 기존 Harbor Project 하나와 KubeSphere Project·Application 하나를 조회 대상으로 정한다.
- Secret·Token·Password·Private Key가 노출되지 않는 화면 경로를 확인한다.
- 기존 Application을 사용할 수 없을 때 Manual 워크스루로 즉시 전환할 수 있게 한다.
- 오후 상세 진행 대상인 `6.4`, `6.5`의 첫 확인과 주요 분기 위치를 확인한다.

#### 있으면 사용하되 별도로 만들지 않을 것

- 기존 Artifact·Tag와 정상 Harbor Repository 화면
- 기존 Project의 Deployment·Pod·Service·Endpoint·Ingress
- 기존 PVC와 정상 Mount 상태
- 현재 정상 HTTP 응답
- 이미 마스킹된 Console 출력

#### 이번 교육을 위해 준비하지 않을 것

- 신규 Harbor Image와 Push/Pull 계정
- 교육용 Image Secret·PVC·Deployment·Service·Ingress
- Dashboard Token 신규 발급·교체
- NFS Mount 실패 재현과 직접 Mount 환경
- 권한 오류용 사용자·Role 변경
- `ImagePullBackOff` 재현용 잘못된 Tag·Secret
- 별도 장애 캡처·로그·슬라이드

### 26.6 현장 진행 순서

#### 오전

```text
4.1 전체 이용 흐름
→ 4.2 Harbor에서 Image가 준비되는 위치
→ 4.3 KubeSphere에서 Image·Storage·Workload·Service·Ingress가 연결되는 위치
→ 4.4 접속 전 GSAMS 신청 조건
→ 정상 사용자 HTTP까지 정리
```

#### 오후

```text
다섯 증상과 Guide 매핑
→ 6.4 Project·권한 사례 상세
→ 6.5 ImagePullBackOff 사례 상세
→ 6.1·6.2·6.3의 첫 분기와 에스컬레이션 위치 확인
→ 운영 교육 전체 Q&A
```

오전과 오후를 모두 라이브 시연으로 채우지 않는다. 오전은 정상 경로 조회, 오후는 문서 기반 분기 판단으로 역할을 분리한다.

### 26.7 현장 전환 기준

```text
Mode 1. 기존 정상 환경 읽기 전용 조회 + Guide
→ Harbor·KubeSphere 접근이 가능한 경우

Mode 2. Guide의 기존 출력·화면 워크스루
→ 실제 환경 접근이 제한된 경우

Mode 3. 증상 카드·Guide 선택·첫 확인 설명
→ 계정·환경·통역 시간까지 제한된 경우
```

Mode 3에서도 교육생이 올바른 Guide와 첫 확인을 선택하면 핵심 목적은 달성된다.

### 26.8 실행과 정보 노출 경계

다음은 승인된 별도 실습이 아니면 수행하지 않는다.

- Password를 입력하는 Harbor Login·Push·Pull
- Secret 값과 Docker Credential 확인
- Dashboard Token 출력·신규 발급·기존 Token 삭제
- Node 직접 NFS Mount와 Route 변경
- Workspace·Project Member·Role 수정
- 잘못된 Image·Secret을 사용한 장애 재현
- 실제 GSAMS 신청 제출

화면 공유 중 민감정보가 나타나면 해당 화면을 닫고 Manual의 마스킹된 예시로 전환한다.

### 26.9 이번 전략의 완료 판정

다음이 가능하면 8/28 기술 전수는 목적을 달성한 것으로 본다.

- 사용자가 계정·Harbor·KubeSphere·Ingress까지의 정상 이용 흐름을 설명한다.
- 기존 환경 또는 Manual에서 PVC·Secret·Deployment·Service·Endpoint·Ingress의 연결을 찾는다.
- 다섯 증상을 올바른 Troubleshooting Guide와 연결한다.
- `6.4`, `6.5`에서 첫 확인 결과에 따라 다음 분기를 선택한다.
- 장애를 재현하지 않아도 정상 완료 증거와 에스컬레이션 경계를 말한다.
- 실제값이 미확정이거나 접근이 제한되면 추측하지 않고 필요한 확인과 문서 위치를 기록한다.

