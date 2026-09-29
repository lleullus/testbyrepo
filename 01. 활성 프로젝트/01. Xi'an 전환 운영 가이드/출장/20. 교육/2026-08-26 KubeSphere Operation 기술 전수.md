---
title: "2026-08-26 KubeSphere Operation 기술 전수"
status: current
doc_type: training-note
scope: "2026-08-26 오후 KubeSphere Operation 1.1~1.7 기술 전수와 강사 사전 숙지·시연·판정 기준"
created: "2026-08-15"
updated: "2026-08-21"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획]]"
---

# 2026-08-26 KubeSphere Operation 기술 전수

> [!important] 이 문서의 역할
> 8/26 오전에는 별도 교육에 참석하고, 오후에는 최종 배포 Manual의 `1.1~1.7 KubeSphere Operation`을 기술 전수한다. 이 문서는 화면을 빠르게 훑기 위한 요약본이 아니라, **사용자 신청이 Workspace·Project·Role·Quota·kubectl 접근·CA ConfigMap으로 변환되는 전체 관리 흐름을 강사가 밀도 있게 설명하고 교육생의 이해와 실제 결과를 판정하기 위한 학습·진행 기준**이다.

> [!success] 현재 환경 전제
> 기존 Xi'an Host·PRD Member·DEV Member와 Multi-Cluster 구성은 이미 완료되어 있다. 8/26에는 기존 환경에서 승인된 범위의 조회와 시연을 사용한다. Workspace·Project·Role·Quota·ConfigMap 변경이 필요한 경우 대상 Cluster·계정·승인·정리 방법을 먼저 확인하며, Secret·Token·kubeconfig·인증서 원문은 교육 자료나 기록에 남기지 않는다.

## 1. 8/26 확정 범위

### 오전

- 별도 교육 참석
- 오후 기술 전수에 사용할 계정·화면·Manual·통역 용어 최종 확인
- 실습 계정과 조회 대상이 준비되지 않았으면 시연을 마스킹된 화면·기존 정상 결과 워크스루로 전환

### 오후

| Manual | 주제 | 교육 후 교육생이 판단할 것 |
|---|---|---|
| 1.1 | Creating Workspaces&projects | 신청 대상 Cluster와 Workspace·Project 생성 순서 |
| 1.2 | Inviting a new member | Workspace 멤버 등록과 Project 권한의 차이 |
| 1.3 | Assigning project roles to users | 신청서 Permission과 Project Role 매핑 |
| 1.4 | Setting quotas | CPU·Memory·Storage 요청을 자원 경계로 변환하는 방법 |
| 1.5 | KubeSphere Role-Based Access Control | Platform·Workspace·Project 권한 계층과 최소 권한 |
| 1.6 | Enable users using kubectl CLI | Bastion·kubeconfig·VIP-A·context·Project 권한의 연결 |
| 1.7 | KubeSphere SECDS-ROOT.crt ConfigMap Mount | Harbor CA 신뢰 오류와 KubeSphere `ks-apiserver` CA Mount 흐름 |

이날의 핵심 질문은 다음이다.

> **사용자의 신청과 접근 요청은 KubeSphere의 어떤 객체·권한·Quota·접속 경계로 변환되며, 각각의 완료를 무엇으로 확인하는가?**

## 2. 전체 관리 흐름을 하나의 이야기로 설명한다

```text
사용자 또는 서비스 신청
→ 신청자·사용자·Permission·PRD/DEV·CPU·Memory·Storage 확인
→ 대상 Member Cluster 결정
→ Workspace 생성
→ Project 생성 = Kubernetes Namespace 생성
→ Workspace Member 초대
→ Project Member 초대
→ 신청 Permission을 Project Role로 매핑
→ Workspace·Project CPU/Memory Quota 적용
→ Namespace 전체·StorageClass별 Storage Quota 적용
→ 필요 시 승인된 kubectl 접근 제공
→ Harbor CA 신뢰가 필요한 경우 Member별 CA ConfigMap과 ks-apiserver Mount 확인
→ 사용자 재로그인·화면·권한·Quota·접속 결과 검증
```

### 반드시 구분할 것

```text
Workspace가 존재한다
≠ Project가 존재한다

Workspace에 사용자가 있다
≠ Project 안에서 리소스를 생성할 권한이 있다

신청서에 Admin이라고 적혀 있다
≠ project-admin을 자동 부여한다

Quota가 화면에 보인다
≠ 실제 Namespace와 StorageClass별 ResourceQuota가 모두 맞다

kubeconfig 파일이 있다
≠ 올바른 Cluster·사용자·context·권한을 사용한다

CA ConfigMap이 있다
≠ ks-apiserver가 해당 ConfigMap을 Mount하고 새 CA를 읽었다
```

## 3. 권장 진행 순서와 시간 배분

오후 시간이 실제 통역·질의·시연 상황에 따라 달라질 수 있으므로 분 단위 시간보다 교육 블록과 완료 기준을 우선한다.

| 블록 | 권장 범위 | 핵심 활동 | 통과 기준 |
|---|---|---|---|
| A | 1.1~1.3 | 신청 → Workspace/Project → Member → Role | 신청 사례를 객체와 권한으로 변환 |
| B | 1.4~1.5 | Quota와 RBAC 계층 | 자원 경계와 권한 경계를 분리 설명 |
| C | 1.6 | kubectl 접근 | VIP-A·context·kubeconfig·Project 권한 연결 |
| D | 1.7 | CA ConfigMap Mount | x509 증상과 CA 적용 경로 설명 |
| E | 통합 | 하나의 신청 사례 Teach-back | 대상·객체·권한·Quota·접속·검증을 연결 |

## 4. 기준 Manual

> [!important] 현장 실습용 가이드
> 6명 운영자 실습에서는 [[00. KubeSphere Operation 운영자 실습 가이드 안내|2026-08-26 KubeSphere Operation 운영자 실습 가이드]]를 우선 사용하고, 아래 `50. 운영` 문서는 원본 기준 Manual로 참조한다.

1. [[50. 운영/04. Kubesphere Operation/01. Creating Workspaces&projects|1.1 Creating Workspaces&projects]]
2. [[50. 운영/04. Kubesphere Operation/02. Inviting a new member|1.2 Inviting a new member]]
3. [[50. 운영/04. Kubesphere Operation/03. Assigning project roles to users|1.3 Assigning project roles to users]]
4. [[50. 운영/04. Kubesphere Operation/04. Setting quotas|1.4 Setting quotas]]
5. [[50. 운영/04. Kubesphere Operation/05. Kubesphere Role-Based Access Control|1.5 KubeSphere Role-Based Access Control]]
6. [[50. 운영/04. Kubesphere Operation/06. Enable users using kubectl CLI|1.6 Enable users using kubectl CLI]]
7. [[50. 운영/04. Kubesphere Operation/07. KubeSphere SECDS-ROOT.crt ConfigMap Mount|1.7 KubeSphere SECDS-ROOT.crt(CA.crt) ConfigMap Mount]]

화면 명칭이나 실제값이 문서와 다르면 현재 Xi'an Console과 승인된 신청·운영 기준을 우선한다. 문서 예시의 Cluster 이름·StorageClass·계정·경로를 기억으로 재사용하지 않는다.

---

# Part 1. Workspace·Project·Member·Role

## 5. 1.1 Creating Workspaces&projects

### 5.1 Workspace와 Project의 역할

| 객체 | 의미 | 운영상 확인할 것 |
|---|---|---|
| Workspace | Project와 Workspace Member를 묶는 상위 관리 범위 | 이름, 관리자, 멤버, 연결된 Project |
| Project | Kubernetes Namespace와 연결되는 실제 Workload 작업 경계 | 대상 Cluster, Namespace, 상태, Quota |
| Namespace | Kubernetes Resource 격리 단위 | `Active` 여부, 실제 이름, ResourceQuota |

DKS 운영 정책에서 Workspace와 Project를 1:1로 구성하더라도 두 객체의 역할이 같아지는 것은 아니다.

```text
Workspace
→ 멤버와 Project를 관리하는 상위 범위

Project
→ 특정 Member Cluster의 Namespace와 연결되는 실행 범위
```

### 5.2 신청에서 먼저 읽을 항목

- 신청자와 실제 사용자
- Department 또는 서비스 담당 조직
- 대상 환경: PRD 또는 DEV
- Project 이름과 명명 규칙
- 신청 Permission: Admin 또는 User
- CPU Request·Limit 또는 승인량
- Memory Request·Limit 또는 승인량
- Storage 총량과 사용할 StorageClass
- Harbor 사용 여부
- kubectl 사용 필요 여부
- 추가 CA 신뢰 필요 여부

신청서에 항목이 없거나 실제값이 미확정이면 임의 값을 채우지 않는다. 특히 Project 접미사만 보고 대상 Cluster를 결정하지 말고 신청서·카탈로그·현재 Console을 함께 확인한다.

### 5.3 생성 선후관계

```text
대상 Member Cluster 확인
→ Workspace 생성
→ 대상 Cluster에서 Project 생성
→ Project가 Namespace로 생성됐는지 확인
→ Workspace·Project 명칭과 신청서 대조
→ Member·Role·Quota 단계로 이동
```

### 5.4 완료 증거

- KubeSphere에서 Workspace가 조회된다.
- Workspace에 대상 Project가 연결된다.
- Project가 올바른 PRD 또는 DEV Member에 생성되어 있다.
- Kubernetes에서 동일한 Namespace가 `Active`다.
- 과거 Cluster나 다른 환경에 동명 Project가 생성되지 않았다.
- 생성자·관리자·명칭이 신청 내용과 일치한다.

조회 예시의 목적은 화면과 Kubernetes 객체가 같은 대상을 가리키는지 확인하는 것이다.

```bash
kubectl config current-context
kubectl get namespace <project-name>
kubectl get resourcequota -n <project-name>
```

### 5.5 흔한 실패

```text
Workspace만 생성
→ Project·Namespace 미생성

Project를 잘못된 Member에 생성
→ 같은 이름이 보여도 실제 Workload 대상이 다름

과거 예시 Project 이름 재사용
→ 신청서와 실제 대상 불일치

Project 생성 직후 완료 선언
→ Member·Role·Quota 미적용
```

## 6. 1.2 Inviting a new member

### 6.1 Workspace Member가 먼저인 이유

사용자를 Project에 추가하려면 Workspace 범위에서 사용자를 먼저 식별하고 초대해야 한다.

```text
사용자 계정 존재·로그인 가능
→ Workspace Member 초대
→ Project Member 초대
→ Project Role 부여
```

### 6.2 Workspace Role

기본 초대에서는 상위 Workspace를 볼 수 있도록 `viewer` 성격의 역할을 사용하고, 실제 Workload 권한은 Project Role에서 별도로 부여한다.

```text
Workspace viewer
= Workspace 접근·조회 기반
≠ Project의 Deployment/PVC/Secret 생성 권한
```

### 6.3 화면 경로를 설명할 때

```text
Workbench
→ Workspaces
→ 대상 Workspace
→ Workspace Settings
→ Workspace Members
→ Invite Member
→ 대상 사용자 선택
→ Workspace Role 확인
→ OK
```

화면 위치를 외우게 하는 것보다 **어느 범위의 멤버십을 만드는 절차인지** 먼저 설명한다.

### 6.4 완료 증거

- 신청된 사용자 계정이 Workspace Members에 모두 보인다.
- 계정 문자열이 신청서의 실제 AD 계정과 일치한다.
- 동명이인·다른 도메인 계정을 선택하지 않았다.
- 사용자 재로그인 후 Workspace가 보인다.
- 아직 Project 권한이 없으면 Project가 보이지 않거나 작업할 수 없다는 점을 설명할 수 있다.

## 7. 1.3 Assigning project roles to users

### 7.1 DKS 기본 매핑

```text
신청서 Permission = Admin
→ project-operator

신청서 Permission = User
→ project-viewer
```

`Admin`이라는 단어만 보고 `project-admin`을 주지 않는다. `project-admin`은 멤버와 역할까지 관리할 수 있어 별도 운영 정책과 승인이 필요한 더 강한 권한이다.

### 7.2 역할 비교

| Project Role | 조회 | Workload·PVC·Secret 생성/변경 | Project Member 관리 | 기본 매핑 |
|---|---:|---:|---:|---|
| project-viewer | O | X | X | 신청서 User |
| project-operator | O | O | X | 신청서 Admin |
| project-admin | O | O | O | 별도 정책·승인 |

### 7.3 화면 경로

```text
Projects
→ 대상 Project
→ Project Settings
→ Project Members
→ Invite
→ Workspace에 등록된 사용자 선택
→ 신청 Permission과 매핑되는 Project Role 선택
→ OK
```

### 7.4 실제 권한 확인

역할 이름만 보고 완료하지 않는다. 승인된 조회 또는 작은 테스트로 실제 권한 범위를 확인한다.

```text
project-viewer
→ 기존 Workload·PVC·Secret 조회 가능
→ Create/Edit/Delete 메뉴 없음

project-operator
→ Workload·PVC·Secret 생성·수정 가능
→ Project Member 관리 메뉴 없음
```

CLI 권한 확인이 승인된 경우에는 실제 Namespace를 지정하고 읽기 전용으로 확인한다.

```bash
kubectl auth can-i get pods -n <project-name> --as=<user>
kubectl auth can-i create deployments.apps -n <project-name> --as=<user>
```

실제 환경의 사용자 인증 방식과 권한에 따라 `--as` 사용이 적합하지 않을 수 있으므로, 기본 검증은 해당 사용자 로그인 화면과 승인된 kubeconfig 결과를 우선한다.

### 7.5 권한 문제의 첫 분기

```text
Project 자체가 존재하는가?
→ Workspace Member인가?
→ Project Member인가?
→ 실제 Project Role은 무엇인가?
→ Role은 신청 Permission과 일치하는가?
→ Quota나 Admission 정책이 생성 실패 원인은 아닌가?
```

---

# Part 2. Quota와 RBAC

## 8. 1.4 Setting quotas

### 8.1 Quota의 목적

Quota는 사용자의 편의를 위한 표시값이 아니라 **Workspace·Project·Namespace가 사용할 수 있는 자원의 경계**다.

### 8.2 CPU와 Memory

| 항목 | 의미 | 판정 시 주의점 |
|---|---|---|
| Requests | 스케줄링과 예약의 기준이 되는 요구량 | 실제 Pod Request 합계와 비교 |
| Limits | 사용할 수 있는 상한 | Request보다 작지 않은지 확인 |
| Workspace Quota | 상위 관리 범위의 자원 경계 | 1:1 정책일 때 Project와 일관성 확인 |
| Project Quota | 실제 Namespace의 자원 경계 | ResourceQuota 객체와 화면 대조 |

### 8.3 Storage Quota

Storage는 한 숫자로만 보지 않는다.

```text
Namespace 전체 Storage Request 총량
+
특정 StorageClass별 Storage Request 총량
```

대상 Cluster의 실제 StorageClass를 먼저 확인한 뒤 ResourceQuota의 resource key에 반영한다.

```bash
kubectl config current-context
kubectl get storageclass
kubectl get resourcequota -n <project-name> -o yaml
```

### 8.4 완료 증거

- Workspace Quota와 Project Quota가 신청값과 일치한다.
- CPU·Memory Request/Limit의 단위와 숫자가 바뀌지 않았다.
- Namespace ResourceQuota가 실제로 존재한다.
- StorageClass 이름이 대상 Cluster의 현재 값이다.
- StorageClass별 Quota가 잘못된 과거 예시를 참조하지 않는다.
- 사용자가 승인량을 넘는 요청을 했을 때 거부될 경계가 설명 가능하다.

### 8.5 과잉 판정 방지

```text
Quota 화면 저장 성공
≠ Kubernetes ResourceQuota 반영 확인

Storage 총량 설정
≠ StorageClass별 Quota 설정

숫자가 같음
≠ 단위와 Request/Limit 의미가 같음
```

## 9. 1.5 KubeSphere Role-Based Access Control

### 9.1 세 계층

```text
Platform
→ Workspace
→ Project / Namespace
```

| 계층 | 관리 대상 | 대표 판단 |
|---|---|---|
| Platform | Cluster와 전체 플랫폼 | 누가 플랫폼 설정·Cluster를 관리하는가 |
| Workspace | Workspace·Project·멤버 | 누가 상위 관리 범위를 볼 수 있는가 |
| Project | Namespace 내부 리소스 | 누가 Workload·Storage·Secret을 조회·변경하는가 |

### 9.2 최소 권한으로 설명한다

- 사용자가 서비스를 조회만 해야 하면 `project-viewer` 범위가 기본이다.
- Workload와 PVC를 관리해야 하면 `project-operator`를 검토한다.
- 멤버·역할 관리가 필요하다는 근거가 없으면 `project-admin`을 부여하지 않는다.
- Platform 또는 Workspace 관리자 권한으로 Project 권한 부족을 우회하지 않는다.
- 장애 해결을 이유로 영구 권한을 확대하지 않는다.

### 9.3 권한과 Quota를 분리한다

```text
권한 있음 + Quota 부족
→ 생성 명령은 허용돼도 Admission 단계에서 거부될 수 있음

Quota 충분 + 권한 없음
→ Create/Edit 메뉴나 API 요청 자체가 거부됨
```

따라서 리소스 생성 실패를 모두 RBAC 문제로 보지 않는다.

### 9.4 교육생에게 묻는 질문

1. Workspace Member인데 Project가 안 보이면 어디를 확인하는가?
2. Project는 보이는데 Create 메뉴가 없으면 어떤 Role이 정상일 수 있는가?
3. 신청서 Admin을 `project-admin`으로 주지 않는 이유는 무엇인가?
4. Role이 맞는데 Pod 생성이 거부되면 Quota를 어떻게 분리해서 보는가?
5. 멤버 관리 권한이 없는 것이 오류인지 정상 최소 권한인지 어떻게 판단하는가?

---

# Part 3. kubectl 접근과 CA ConfigMap

## 10. 1.6 Enable users using kubectl CLI

### 10.1 kubectl은 별도 승인 경로다

KubeSphere Web UI 사용 권한이 있다고 자동으로 Bastion과 kubectl 접근이 허용되는 것은 아니다.

```text
Bastion OS 계정
→ 접근 승인·CyberArk·방화벽
→ 사용자별 kubeconfig
→ 대상 Cluster VIP-A
→ cluster / user / context
→ Project RBAC
→ 승인된 Namespace 범위에서 kubectl 사용
```

### 10.2 kubeconfig에서 구분할 것

| 항목 | 결정하는 것 | 잘못됐을 때 영향 |
|---|---|---|
| cluster | API Server와 CA | 다른 Cluster 또는 접속 실패 |
| user | 인증 주체 | 인증 실패 또는 다른 권한 |
| context | cluster·user·Namespace 조합 | 명령은 성공하지만 잘못된 대상 조회 가능 |
| current-context | 현재 실제 대상 | 가장 먼저 확인해야 할 값 |

### 10.3 사용 전 확인

```bash
kubectl config current-context
kubectl config get-contexts
kubectl cluster-info
kubectl auth can-i get pods -n <project-name>
```

첫 명령이 성공했다는 이유만으로 올바른 대상이라고 판단하지 않는다. Node 이름·Cluster 카탈로그·VIP-A와 대조한다.

### 10.4 민감정보 경계

다음 값은 화면 공유·학습 기록·문서·채팅에 남기지 않는다.

- kubeconfig 전체 원문
- `client-certificate-data`
- `client-key-data`
- Bearer Token
- JWT Secret
- 비밀번호
- 개인키
- ServiceAccount Token

사용자별 kubeconfig 파일은 승인된 경로에 두고 파일 권한을 제한한다.

```bash
chmod 600 ~/.kube/config
```

### 10.5 완료 증거

- 승인된 사용자 계정으로 Bastion 접근이 가능하다.
- kubeconfig 파일 권한이 적절하다.
- `current-context`가 대상 PRD 또는 DEV Member를 가리킨다.
- VIP-A와 Kubernetes API 연결이 성립한다.
- 승인된 Project에서 읽기 권한이 정상이다.
- 권한 밖 Namespace의 변경이 허용되지 않는다.
- 인증정보 원문을 기록하지 않았다.

## 11. 1.7 KubeSphere SECDS-ROOT.crt ConfigMap Mount

### 11.1 발동 조건

KubeSphere에서 Harbor Image Registry Secret을 생성하거나 Registry를 확인할 때 다음 오류가 발생할 수 있다.

```text
x509: certificate signed by unknown authority
```

이 오류는 계정 비밀번호 실패와 동일하지 않다. KubeSphere의 `ks-apiserver`가 Xi'an Harbor의 인증서 체인을 신뢰하지 못하는지 확인한다.

### 11.2 적용 대상

- Harbor를 사용하는 각 Member Cluster
- `kubesphere-system` Namespace
- `ks-apiserver` Workload
- 승인된 Xi'an Root CA 파일

Host나 다른 Member에서 사용한 ConfigMap 이름·인증서 내용을 그대로 복사하지 않는다. 실제 인증서 파일과 명칭은 현장에서 확인한다.

### 11.3 ConfigMap 생성 흐름

```text
Platform
→ Cluster Management
→ 대상 Member Cluster
→ Configuration
→ ConfigMaps
→ Create
```

기준 예:

| 항목 | 값 |
|---|---|
| Name | `secds-rootca` 또는 승인된 실제 이름 |
| Project / Namespace | `kubesphere-system` |
| Key | `ca.crt` |
| Value | 승인된 SECDS Root CA 내용 |

CA 원문은 이 문서에 넣지 않는다. 시연 시 화면에 전체 인증서 내용을 노출하지 않고, 파일의 발급자·만료·fingerprint 등 승인된 식별 정보로 대상이 맞는지 확인한다.

### 11.4 ks-apiserver Mount

```text
Platform
→ Cluster Management
→ 대상 Member Cluster
→ Application Workloads
→ Workloads
→ ks-apiserver
→ More
→ Edit Settings
→ Volumes
→ Mount ConfigMap or Secret
→ 대상 ConfigMap 선택
→ Mount path·key 확인
→ 저장
```

설정 저장 후 `ks-apiserver`가 새 Pod로 재생성되거나 Rollout되는지 본다.

### 11.5 완료 증거

```text
ConfigMap 존재
+ Namespace = kubesphere-system
+ Key = ca.crt
+ ks-apiserver Pod spec에 ConfigMap volume 존재
+ container volumeMount 존재
+ 새 Pod Ready
+ x509 오류 재현 안 됨
+ Harbor Image Registry Secret 생성 또는 검증 성공
```

### 11.6 실패 분기

```text
ConfigMap 없음
→ 생성 단계 확인

ConfigMap은 있음, Volume 없음
→ Workload 설정 저장 여부 확인

Volume 있음, volumeMount 없음
→ Container Mount 설정 확인

Pod 재기동 실패
→ Event·Mount path·key·권한 확인

Pod 정상, x509 지속
→ 실제 CA가 Harbor 인증서 체인과 맞는지 확인
→ 다른 Cluster CA 또는 서버 인증서 파일을 넣지 않았는지 확인

x509는 해결, unauthorized 발생
→ CA 문제가 아니라 Harbor 계정·Project 권한으로 분리
```

### 11.7 변경 경계

- 운영 Member의 `ks-apiserver` 변경은 영향이 있을 수 있으므로 승인된 대상과 시간에만 수행한다.
- CA 파일 원문을 메신저·교육 노트·로그에 복사하지 않는다.
- ConfigMap 이름만 같다고 올바른 인증서라고 판단하지 않는다.
- Host·PRD Member·DEV Member의 대상과 context를 먼저 고정한다.
- Rollout 후 KubeSphere 로그인·API·Registry Secret 기능을 함께 확인한다.

---

# Part 4. 통합 교육과 판정

## 12. 하나의 신청 사례를 끝까지 변환한다

아래와 같은 가상 신청을 사용한다. 실제 이름·계정·Quota는 현장 승인값으로 교체한다.

```text
환경: DEV
Project: <approved-project-name>
사용자 A: Admin
사용자 B: User
CPU / Memory / Storage: <approved-values>
kubectl: 사용자 A만 요청
Harbor Private Image: 사용
```

교육생이 다음 표를 완성하게 한다.

| 신청 항목 | KubeSphere·Kubernetes 반영 | 완료 증거 |
|---|---|---|
| DEV | 대상 DEV Member Cluster | context·Cluster name |
| Project | Workspace + Project/Namespace | UI + Namespace Active |
| 사용자 A Admin | Workspace Member + project-operator | 실제 Create 가능·멤버 관리 불가 |
| 사용자 B User | Workspace Member + project-viewer | 조회 가능·Create 불가 |
| CPU/Memory | Workspace·Project Quota | 화면 + ResourceQuota |
| Storage | Namespace 전체·StorageClass별 Quota | 실제 StorageClass + ResourceQuota |
| kubectl | Bastion·kubeconfig·VIP-A·context | 읽기 권한과 대상 확인 |
| Harbor CA | 필요 시 ConfigMap + ks-apiserver Mount | x509 해소·Registry Secret 성공 |

## 13. 강사 시연 순서

1. 최신 실행 일정에서 8/26 범위를 확인한다.
2. 실제 대상 Cluster와 계정이 무엇인지 보여준다.
3. 신청 사례를 읽고 설정값으로 변환한다.
4. Workspace와 Project를 화면에서 구분한다.
5. Workspace Member와 Project Member를 별도 화면에서 확인한다.
6. Project Role을 신청 Permission과 대조한다.
7. Workspace·Project·Storage Quota를 차례로 확인한다.
8. RBAC 계층과 최소 권한을 설명한다.
9. kubectl 접근의 별도 승인·context·VIP-A 경계를 설명한다.
10. x509 사례를 제시하고 CA ConfigMap → ks-apiserver Mount → 기능 재확인 흐름을 설명한다.
11. 교육생이 같은 신청을 문서 위치와 함께 Teach-back한다.

## 14. 교육 중 피할 진행 방식

- 화면 메뉴를 클릭하는 순서만 읽어주고 객체 관계를 설명하지 않음
- 신청서 `Admin`을 `project-admin`으로 단순 치환
- Workspace Member 등록을 Project 권한 부여 완료로 설명
- Quota 숫자만 읽고 Request·Limit·StorageClass별 경계를 생략
- kubeconfig 전체를 화면에 띄움
- 올바른 context를 확인하지 않고 kubectl 명령 시연
- CA 인증서 원문을 교재에 붙여넣음
- ConfigMap 생성만 보고 x509 해결 완료 선언
- 교육생이 실제 Manual 위치를 찾지 못한 상태에서 다음 주제로 이동

## 15. 대표 문제 상황 사고 연습

### 사례 1 — 사용자가 로그인했지만 Project가 보이지 않는다

```text
Project/Namespace가 실제 존재하는가?
→ Workspace Member인가?
→ Project Member인가?
→ 재로그인이 필요한가?
```

### 사례 2 — Project는 보이지만 Create 메뉴가 없다

```text
신청 Permission이 User인가 Admin인가?
→ 실제 Project Role은 viewer인가 operator인가?
→ viewer라면 조회 전용이 정상인가?
→ operator인데 실패하면 Quota·정책을 별도 확인
```

### 사례 3 — CPU Quota는 맞는데 PVC 생성이 거부된다

```text
CPU·Memory Quota와 Storage Quota를 분리
→ Namespace 전체 Storage Request
→ StorageClass별 ResourceQuota
→ 실제 StorageClass 이름
→ PVC 요청 용량
```

### 사례 4 — kubectl 명령은 성공하지만 다른 Node가 보인다

```text
명령 성공 여부보다 대상 확인
→ current-context
→ API endpoint / VIP-A
→ Node 이름과 Cluster 카탈로그
→ 다른 Cluster라면 결과 해석 중단
```

### 사례 5 — Registry Secret 생성에서 x509

```text
계정 오류로 단정하지 않음
→ 대상 Member
→ Harbor 인증서 체인
→ CA ConfigMap
→ ks-apiserver volume·mount
→ Rollout
→ 기능 재확인
```

## 16. 숙지 수준 분류

### A. 문서 없이 설명할 것

- [ ] Workspace와 Project/Namespace의 차이
- [ ] Workspace Member와 Project Member의 차이
- [ ] 신청서 Admin→project-operator, User→project-viewer 매핑
- [ ] project-admin이 별도 권한인 이유
- [ ] Platform→Workspace→Project RBAC 계층
- [ ] Requests와 Limits의 차이
- [ ] Workspace·Project·StorageClass별 Quota 관계
- [ ] kubectl의 Bastion·kubeconfig·VIP-A·context 관계
- [ ] ConfigMap 존재와 실제 Mount·기능 성공의 차이
- [ ] x509와 unauthorized 오류의 차이

### B. Manual을 보며 정확히 수행·설명할 것

- [ ] Workspace·Project 생성 화면 경로
- [ ] Workspace Member 초대 경로
- [ ] Project Member·Role 설정 경로
- [ ] Workspace·Project Quota 입력 위치
- [ ] Storage ResourceQuota 확인 위치
- [ ] RBAC 역할표와 신청 매핑 확인
- [ ] kubectl 사용자 접근 절차
- [ ] CA ConfigMap 생성과 ks-apiserver Mount 절차
- [ ] 변경 후 Rollout·기능 검증 위치

### C. 현장에서 반드시 다시 확인할 것

- 실제 대상 PRD/DEV Cluster와 context
- 실제 Workspace·Project 이름
- 실제 사용자 계정과 Permission
- 실제 CPU·Memory·Storage 승인량
- 실제 StorageClass
- 실제 Bastion·CyberArk·방화벽 조건
- 실제 kubeconfig 전달·보관 절차
- 실제 Root CA 파일과 승인된 식별정보
- 실제 ConfigMap 이름·Mount path
- 실제 `ks-apiserver` Rollout과 Registry Secret 결과

## 17. 자가점검

| 질문 | 상태 | 막히는 부분 | 돌아갈 Manual |
|---|---|---|---|
| 신청을 Workspace·Project로 변환할 수 있는가? | 미평가 |  | 1.1 |
| Workspace Member와 Project Member를 구분하는가? | 미평가 |  | 1.2~1.3 |
| Admin→project-operator 정책을 설명하는가? | 미평가 |  | 1.3·1.5 |
| Request·Limit·StorageClass별 Quota를 구분하는가? | 미평가 |  | 1.4 |
| RBAC 세 계층을 설명하는가? | 미평가 |  | 1.5 |
| kubeconfig의 cluster·user·context를 구분하는가? | 미평가 |  | 1.6 |
| VIP-A와 VIP-B를 혼동하지 않는가? | 미평가 |  | 1.6·8/25 최종본 |
| CA ConfigMap과 ks-apiserver Mount를 연결하는가? | 미평가 |  | 1.7 |
| x509와 인증 실패를 분리하는가? | 미평가 |  | 1.7·Harbor Troubleshooting |
| 완료 증거를 UI 한 화면 이상으로 제시하는가? | 미평가 |  | 전체 |

## 18. 직접 연습

### 연습 1 — 신청서 변환

임의 신청서 한 건을 다음 12개 값으로 변환한다.

```text
대상 Cluster
Workspace
Project / Namespace
Workspace Member
Project Member
Project Role
Workspace CPU·Memory Quota
Project CPU·Memory Quota
Namespace Storage 총량
StorageClass별 Quota
kubectl 필요 여부와 접속 경계
CA ConfigMap 필요 여부와 검증 방법
```

### 연습 2 — 권한 충돌 카드

다음 네 사례에서 정상과 오류를 판정한다.

```text
A. User 신청 + project-viewer + Create 메뉴 없음
B. Admin 신청 + project-viewer
C. Admin 신청 + project-operator + Member 관리 메뉴 없음
D. 승인 근거 없음 + project-admin
```

### 연습 3 — 대상 확인

실제 또는 마스킹된 화면에서 다음을 60초 안에 찾는다.

```text
Cluster
Workspace
Project
Project Member
Role
Quota
StorageClass
```

### 연습 4 — kubectl 경계 설명

문서를 닫고 2분 안에 다음을 설명한다.

```text
사용자 → Bastion → kubeconfig → context → VIP-A → Kubernetes API → Project RBAC
```

### 연습 5 — x509 분기

```text
증상: Registry Secret 생성에서 x509
확인 1: 대상 Member
확인 2: 승인된 Root CA
확인 3: ConfigMap Namespace·key
확인 4: ks-apiserver volume·mount
확인 5: 새 Pod Ready
확인 6: Registry Secret 재검증
```

## 19. 예상 질문

| 예상 질문 | 답변 핵심 | 현재 답변 가능 여부 |
|---|---|---|
| Workspace와 Project는 왜 둘 다 있나요? | 상위 관리 범위와 실제 Namespace 작업 경계 분리 | 미평가 |
| Workspace에 초대됐는데 Project가 안 보이는 이유는? | Project Member·Role이 별도 | 미평가 |
| Admin인데 왜 project-admin이 아닌가요? | DKS 최소 권한 매핑과 멤버 관리 권한 분리 | 미평가 |
| CPU·Memory Quota를 Workspace와 Project에 둘 다 넣는 이유는? | 1:1 운영 정책에서 상위·실제 경계를 일관되게 유지 | 미평가 |
| StorageClass별 Quota는 왜 필요한가요? | Storage 정책별 요청 총량 제어 | 미평가 |
| KubeSphere 로그인만 되면 kubectl도 가능한가요? | 별도 Bastion·승인·kubeconfig 필요 | 미평가 |
| current-context가 왜 중요한가요? | 명령 성공보다 올바른 대상이 우선 | 미평가 |
| ConfigMap을 만들었는데 왜 x509가 계속 나나요? | 실제 ks-apiserver Mount·Rollout·CA 일치 확인 | 미평가 |
| CA를 Secret으로 만들면 안 되나요? | 승인된 Manual의 ConfigMap·Mount 구조를 따르고 목적·민감성 구분 | 미평가 |
| x509가 없어졌는데 unauthorized가 나옵니다 | TLS 신뢰와 Harbor 인증·권한은 별도 | 미평가 |

## 20. 현장 기록 양식

```text
교육일: 2026-08-26
대상 Cluster/context: __________________________
사용한 계정 유형: ______________________________
신청 사례 또는 대상 Project: ____________________

1.1 Workspace·Project 결과: ____________________
1.2 Workspace Member 결과: _____________________
1.3 Project Role 결과: _________________________
1.4 Quota 결과: ________________________________
1.5 RBAC 확인 결과: ____________________________
1.6 kubectl 접근 결과: _________________________
1.7 CA ConfigMap·Mount 결과: ___________________

미확정 실제값: _________________________________
질문 주차장: ___________________________________
다음 Manual에서 이어갈 항목: ___________________
민감정보 노출 없음 확인: _______________________
```

## 21. 8/26 완료 기준

- [ ] 교육생이 Workspace·Project·Namespace를 구분한다.
- [ ] Workspace Member와 Project Member가 별도임을 설명한다.
- [ ] 신청서 Admin→project-operator, User→project-viewer 매핑을 설명한다.
- [ ] project-admin이 별도 승인 대상임을 설명한다.
- [ ] CPU·Memory Request/Limit과 StorageClass별 Quota를 구분한다.
- [ ] Platform·Workspace·Project RBAC 계층을 설명한다.
- [ ] kubectl 접근에서 Bastion·kubeconfig·VIP-A·context·Project 권한을 연결한다.
- [ ] Secret·Token·kubeconfig·CA 원문을 노출하지 않는다.
- [ ] x509 오류에서 CA ConfigMap→ks-apiserver Mount→Rollout→기능 재확인 순서를 설명한다.
- [ ] 하나의 신청 사례를 Workspace·Project·Member·Role·Quota·접속 경계로 변환한다.
- [ ] 각 Manual의 사용 시점과 위치를 스스로 찾는다.
- [ ] 완료하지 못한 항목은 원인 추측이 아니라 미확정 값·필요 권한·다음 확인으로 기록한다.

## 22. 다음 일정과 연결

8/27에는 KubeSphere 내부 사용자·권한 관리에서 범위를 넓혀 다음을 다룬다.

```text
반복 운영 작업
→ Worker Node 추가
→ taint·label과 배치 경계
→ DKS FAQ
→ Kubernetes Native API
→ API Server 인증서 갱신
→ Harbor 설치·Project·사용자 관리
```

관련 문서: [[2026-08-27 Operations Manual 및 Harbor Manual 기술 전수|2026-08-27 Operations Manual 및 Harbor Manual 기술 전수]]

---

## 23. 제한된 준비시간을 반영한 현장 실행 전략

> [!important] 적용 원칙
> 8/26의 목적은 새 Workspace·Project·사용자·Quota를 현장에서 만들어 보이는 것이 아니다. **하나의 사용자 신청이 KubeSphere와 Kubernetes의 어떤 객체·권한·자원 경계로 변환되는지, 그리고 각 단계의 완료를 무엇으로 확인하는지 인계하는 것**이 목적이다. 별도 전체 대본은 만들지 않고 이 문서와 기준 Manual을 진행 자료로 사용한다.

### 23.1 기준 진행 단위 — 기존 대상 한 세트

가능하면 교육 전에 다음이 연결된 기존 정상 대상 한 세트를 고른다.

```text
대상 Member Cluster
→ Workspace
→ Project / Namespace
→ Workspace Member
→ Project Member / Role
→ Workspace·Project·Storage Quota
```

이 한 세트를 `1.1~1.5` 전체의 기준 대상으로 사용한다. 절마다 다른 Project나 계정을 사용하면 대상 전환 자체가 설명을 방해하므로, 실제 정책상 문제가 없는 범위에서 같은 대상을 계속 따라간다.

적합한 기존 대상이 없다고 해서 교육용 Workspace·Project를 새로 만들지 않는다. 이 경우에는 기준 Manual의 화면 순서, 마스킹된 정상 결과, 기존 문서의 예시를 사용한다.

### 23.2 범위별 현장 방식

| 범위 | 우선 방식 | 현장에서 하지 않을 것 |
|---|---|---|
| `1.1~1.3` Workspace·Project·Member·Role | 기존 객체를 조회하며 신청값과 객체 관계를 대조 | 교육만을 위한 생성·초대·Role 변경 |
| `1.4~1.5` Quota·RBAC | 기존 Quota와 Role을 조회하고 Request·Limit·StorageClass별 경계를 설명 | 승인 없는 Quota 수정·권한 확대 |
| `1.6` kubectl | 승인된 경우 `current-context`와 읽기 권한만 확인 | kubeconfig 원문 표시·신규 Credential 발급 |
| `1.7` CA ConfigMap | 기존 설정을 읽기 전용으로 확인하거나 Manual 워크스루 | `ks-apiserver` 설정 변경·Rollout 실행 |

### 23.3 준비 우선순위

#### 반드시 준비할 것

- KubeSphere Console과 기준 Manual `1.1~1.7`을 열 수 있는지 확인한다.
- 설명에 사용할 대상 Member Cluster와 기존 Workspace·Project 한 세트를 정한다.
- 해당 대상의 Member·Role·Quota 화면을 어디에서 여는지 한 번만 확인한다.
- 계정·Token·Secret·kubeconfig·CA 원문이 화면에 노출되지 않는 경로를 확인한다.
- 실제 대상이 준비되지 않았을 때 즉시 Manual 워크스루로 전환할 수 있도록 각 Manual 위치를 북마크한다.

#### 있으면 사용하되 별도로 만들지 않을 것

- `project-viewer`와 `project-operator`가 각각 적용된 기존 사용자
- 기존 ResourceQuota와 StorageClass별 Quota
- 승인된 읽기 전용 `current-context` 결과
- 기존 CA ConfigMap과 `ks-apiserver` Mount 상태

#### 이번 교육을 위해 준비하지 않을 것

- 신규 Workspace·Project·사용자 계정
- 교육용 Role·Quota 변경
- 사용자별 kubeconfig와 Bastion 접근
- 새 CA ConfigMap 또는 `ks-apiserver` 변경
- 별도 데모 Cluster와 추가 캡처 자료

### 23.4 현장 진행 순서

오후 전체를 다음 한 흐름으로 유지한다.

```text
신청 사례 확인
→ 대상 PRD/DEV Member 결정
→ Workspace와 Project/Namespace 구분
→ Workspace Member와 Project Member 구분
→ 신청 Permission과 Project Role 대조
→ CPU·Memory·Storage Quota 위치와 의미 확인
→ kubectl은 별도 승인 경로임을 확인
→ x509는 CA Trust·Mount 경로로 분리
→ 각 단계의 완료 증거 정리
```

`1.1~1.5`는 기존 대상 화면을 따라가며 연속해서 설명한다. `1.6~1.7`은 실제 접근과 변경 전제가 다르므로 같은 수준의 라이브 시연을 억지로 만들지 않고, 승인된 읽기 전용 확인 또는 Manual 워크스루로 분리한다.

### 23.5 현장 전환 기준

```text
Mode 1. 기존 환경 읽기 전용 조회
→ 대상과 계정이 준비된 경우

Mode 2. 기존 정상 결과·마스킹 화면 워크스루
→ 로그인이나 권한이 일부 제한된 경우

Mode 3. 기준 Manual 워크스루
→ 실제 대상·계정·승인이 준비되지 않은 경우
```

Mode가 낮아져도 교육 실패로 보지 않는다. 실제 변경을 억지로 실행하는 것보다 객체 관계·완료 증거·변경 경계를 정확히 인계하는 것이 우선이다.

### 23.6 중단과 기록 기준

다음 상황에서는 값을 추측하거나 즉석에서 생성·변경하지 않는다.

- 화면의 Cluster·Workspace·Project가 신청 사례와 일치하지 않는다.
- 실제 계정·Quota·StorageClass·CA가 미확정이다.
- 조회 과정에서 민감정보가 노출될 가능성이 있다.
- Role·Quota·ConfigMap 변경 승인이 없다.
- `current-context` 또는 실제 대상 Cluster를 확정할 수 없다.

이 경우 현장 기록에는 다음만 남긴다.

```text
확인된 현재 상태
미확정 실제값
필요한 권한 또는 담당자
돌아갈 Manual 위치
다음 읽기 전용 확인
```

### 23.7 이번 전략의 완료 판정

다음이 가능하면 8/26 기술 전수는 목적을 달성한 것으로 본다.

- 하나의 신청 사례를 대상 Cluster·Workspace·Project·Member·Role·Quota로 변환한다.
- 기존 화면 또는 Manual에서 각 객체의 위치를 찾는다.
- 객체가 존재하는 것과 실제 권한·Quota·Mount가 적용된 것을 구분한다.
- kubectl과 CA ConfigMap을 별도 승인·변경 경계로 설명한다.
- 실제 환경이 준비되지 않아도 올바른 Manual과 완료 증거를 제시한다.

