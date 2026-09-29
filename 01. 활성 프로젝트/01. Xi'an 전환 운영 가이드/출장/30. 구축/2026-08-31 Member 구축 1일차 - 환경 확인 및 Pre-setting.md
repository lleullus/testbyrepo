---
title: "2026-08-31 Member 구축 1일차 - 환경 확인 및 Pre-setting"
status: current
doc_type: build-note
scope: "2026-08-31 신규 Member VM 실제 환경 확인, Initial VM·Bastion·Node Pre-setting, Inventory 작성 및 Kubespray 실행 준비"
created: "2026-08-15"
updated: "2026-08-21"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거]]"
---

# 2026-08-31 Member 구축 1일차 - 환경 확인 및 Pre-setting

> [!important] 이 문서의 역할
> 이 문서는 8/31 신규 Member 구축 착수일의 **강사 학습·현장 수행·판정 기준**이다. VM·Bastion·Node Pre-setting·Inventory의 상세 관계와 기존 학습·연습 내용을 유지하면서, 교육생과 실제 환경을 확인하고 9/1 Kubespray 실행 가능 여부까지 증거로 판단하는 데 사용한다.
>
> 날짜와 수행 범위는 [[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|8/21 최신 실행 일정]]을 최우선으로 한다. 기존 문서·기존 Xi'an 값은 구조와 정상 비교에 사용하며 신규 Member의 실제값을 대신하지 않는다.

> [!success] 현재 상태 전제
> 기존 Xi'an 환경의 구축은 완료되어 있다. 8/31부터는 **신규 Member VM**을 대상으로 교육생과 처음부터 구축 Hands-on을 진행한다. 기존 Xi'an 값은 구조와 정상 상태 비교에 쓰고, 신규 Member VM의 hostname·IP·VIP·CIDR 등은 새로 확인한다.

## 1. 8/31 확정 범위

확정 일정에서 8/31의 범위는 다음과 같다.

- Xi'an DKS 전체 구축 흐름 설명
- 신규 Member VM·VIP·Bastion 상태 확인
- Bastion 사용자·디스크·bundle·필수 도구 확인
- Kubernetes Node 사전 설정 확인
- `hosts.yaml` 작성·검토
- LB·CIDR·Domain·Registry·Kubernetes version 등 Inventory/변수 작성·검토
- Ansible 연결 점검
- 교육생이 핵심 설정을 직접 준비

이날의 학습 목표는 명령어를 외우는 것이 아니라 다음 질문에 답할 수 있게 되는 것이다.

> **Kubespray를 실행하기 전에 무엇이 사실로 확인되어 있어야 하며, 그 사실이 Inventory와 변수에 어떻게 들어가는가?**

## 2. 머릿속에 있어야 할 선후관계

```text
신규 Member VM 실제 상태
→ 역할·hostname·IP·디스크 확인
→ VIP-A/VIP-B와 네트워크 조건 확인
→ Bastion을 설치 실행점으로 준비
→ 각 Kubernetes Node의 OS·계정·repo·패키지·swap·filesystem 준비
→ 신규 Member VM 실제값으로 Inventory와 변수 작성
→ Ansible 연결 확인
→ 9/1 Kubespray 실행
```

### 반드시 구분할 것

```text
VM이 존재한다
≠ Kubernetes 설치 준비가 끝났다

SSH가 된다
≠ Ansible이 sudo 포함 정상 실행된다

Inventory 문법이 맞다
≠ Inventory 값이 실제 VM 설계와 맞다

기존 Xi'an 값이 정상이다
≠ 신규 실습 VM에 같은 값을 사용한다
```

## 3. Step 0~3에서 오늘이 차지하는 위치

근거: [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]

| 단계        | 의미                  | 8/31에서 이해해야 할 것                                     |
| --------- | ------------------- | --------------------------------------------------- |
| Step 0    | VM·LB·Bastion 초기 조건 | 자동화 전에 실제 인프라가 설계와 맞는지 확인하는 단계                      |
| Step 1    | Bastion Pre-setting | 설치·관리 실행점에 필요한 DNS·hosts·권한·도구를 준비하는 단계             |
| Step 2    | Node Pre-setting    | Kubespray가 기대하는 OS·계정·패키지·filesystem 조건을 노드에 만드는 단계 |
| Step 3 준비 | Inventory·변수 작성     | 실제 VM 설계를 Kubespray가 읽을 입력으로 표현하는 단계                |
| Step 3 실행 | Kubespray Playbook  | **9/1 중심 범위**                                      |

8/31에는 Step 3의 실행보다 **잘못된 입력을 만들지 않는 능력**이 중요하다.

## 4. VM과 역할을 이해하기

근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/00. Initial VM Setting|0. 초기 VM 설정]]

### 역할별로 왜 구성이 다른가

| 역할 | 내가 설명해야 할 핵심 |
|---|---|
| Bastion | 구축과 관리 명령을 실행하는 거점 |
| Master | Kubernetes Control Plane/API 역할 |
| ETCD | Kubernetes 상태 저장. `/var/lib/etcd` 설계가 중요 |
| Router | Ingress Controller와 VIP-B Backend 역할 |
| Infra | KubeSphere·Monitoring 등 플랫폼 workload 배치 |
| Worker | 사용자 workload 실행 |

정확한 CPU·Memory 값을 모두 외우는 것보다 **왜 역할별 디스크·배치·네트워크 조건이 다른지** 설명할 수 있어야 한다.

### 디스크에서 반드시 이해할 것

- ETCD의 데이터 경로는 일반 `containerd` 경로와 다르다.
- `lsblk`, `findmnt`, `/etc/fstab`, PV/VG/LV 상태를 보지 않고 장치 이름만 보고 파티션을 바꾸면 안 된다.
- 기존 Xi'an 문서에는 과거 카탈로그 불일치 흔적도 있으므로 신규 Member VM에서는 실제 승인된 설계와 현재 출력이 우선이다.
- 파괴적 디스크 작업은 **대상과 역할을 먼저 고정하는 사고 훈련**의 대표 사례다.

## 5. Bastion에서 내가 이해해야 할 것

근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/01. Bastion Node Pre-setting|1. Bastion 노드 사전 설정]]

### 문서 없이 설명할 것

```text
Bastion은 단순 점프 서버가 아니라
클러스터별 설치·관리·운영 실행의 기준점이다.
```

Bastion 준비에는 다음 범주가 있다.

1. DNS / `/etc/hosts`
2. `dspaas` 계정과 sudo
3. 설치에 필요한 repository와 Python/Ansible 의존성
4. SSH key와 대상 노드 접근
5. 설치 bundle과 Kubespray 실행 환경

### 특히 기억할 원칙

- 한 Bastion의 `/etc/hosts`에 다른 Cluster 목록을 합쳐 쓰지 않는다.
- `sudoers`는 설정 존재가 아니라 실제 `sudo -n` 성공까지 확인한다.
- repository URL·package 경로는 과거 예시를 추측해서 채우지 않는다.
- 설치 bundle의 **경로와 버전은 실제 파일로 확인**한다.

## 6. Kubernetes Node Pre-setting에서 알아야 할 것

근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|2. K8S 클러스터 노드 사전 설정]]

### 설명할 수 있어야 하는 범주

- 계정 및 passwordless sudo
- Bastion SSH 공개키 배포
- OS repository
- 필수 패키지
- swap 비활성화
- NFS/Storage 관련 도구
- CA 및 인증서 신뢰
- hostname·hosts·DNS
- filesystem과 VM resource
- Kubespray가 요구하는 kernel/network 전제

모든 세부 명령을 외우는 것이 아니라 다음을 판단해야 한다.

> **이 설정이 Kubespray 전에 왜 필요한가? 적용됐다는 것을 무엇으로 확인하는가?**

## 7. Inventory를 설치 설계도로 이해하기

근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]

### `hosts.yaml`에서 이해할 것

- 어떤 hostname이 어떤 IP를 가지는가
- 어떤 노드가 Control Plane인가
- 어떤 노드가 ETCD인가
- Router·Infra·Worker 그룹은 어떻게 나뉘는가
- 역할별 label·taint는 어떻게 반영되는가

### 환경 변수에서 이해할 것

```text
VIP-A / API endpoint
Cluster name
Pod CIDR
Service CIDR
Service domain
Registry
Kubernetes version
```

이 값들은 독립된 설정 항목이 아니라 **신규 Member VM 설계를 Kubernetes Cluster의 실제 동작으로 바꾸는 입력값**이다.

## 8. 숙지 수준 분류

### A. 문서 없이 바로 설명할 것

- [ ] Bastion·Master·ETCD·Router·Infra·Worker의 역할
- [ ] 왜 VM 실제값 확인이 Inventory 작성보다 먼저인지
- [ ] VIP-A와 VIP-B의 차이
- [ ] ETCD 파일시스템을 별도로 확인하는 이유
- [ ] Bastion이 설치 기준점인 이유
- [ ] passwordless sudo와 SSH key가 Ansible에 왜 필요한지
- [ ] Inventory가 어떤 설계 정보를 담는지
- [ ] Pod CIDR과 Service CIDR의 역할 차이
- [ ] Registry가 offline 구축에서 왜 필요한지
- [ ] 신규 Member VM 값과 기존 Xi'an 값을 섞으면 안 되는 이유

### B. 문서를 보며 정확히 수행·설명할 것

- [ ] VM CPU·Memory·Disk·Mount 확인 명령 찾기
- [ ] Bastion `/etc/hosts` 구성 위치 찾기
- [ ] sudo 권한 검증 방법 찾기
- [ ] SSH key 배포 절차 찾기
- [ ] Node package·swap·repository 확인 절차 찾기
- [ ] `hosts.yaml`의 host/group 구조 읽기
- [ ] `dks_vars.yml`의 VIP·CIDR·Domain 항목 찾기
- [ ] `offline.yml`의 Registry 항목 찾기
- [ ] Kubernetes version 확인 위치 찾기
- [ ] Ansible 연결 확인 명령과 결과 읽기

### C. 신규 Member VM에서 반드시 실제 확인할 것

- hostname / IP / Role
- CPU / Memory / Disk / Mount
- 승인된 DATA disk
- ETCD filesystem
- VIP-A / VIP-B
- Pod / Service CIDR
- Domain
- Registry와 bundle 실제 접근
- repository URL
- 실제 SSH/sudo 권한
- 실제 Kubernetes version과 package version

## 9. 내가 지금 부족한 곳을 찾는 자가점검

| 질문 | 현재 상태 | 막히는 부분 | 학습 문서 |
|---|---|---|---|
| 노드 역할 6개를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/00. Initial VM Setting|0. 초기 VM 설정]] |
| ETCD와 다른 노드의 filesystem 차이를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/00. Initial VM Setting|0. 초기 VM 설정]] |
| Bastion에서 무엇을 준비해야 하는지 5개 범주로 말할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/01. Bastion Node Pre-setting|1. Bastion]] |
| Ansible을 위해 sudo와 SSH가 왜 모두 필요한지 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/01. Bastion Node Pre-setting|1. Bastion]], [[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|2. Node Pre-setting]] |
| Node Pre-setting의 주요 범주를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|2. Node Pre-setting]] |
| `hosts.yaml`의 group 구조를 읽을 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Kubespray]] |
| VIP·CIDR·Domain이 어느 변수 파일에 들어가는지 찾을 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Kubespray]] |
| Inventory 값이 잘못됐을 때 영향 범위를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Kubespray]] |
| Ansible 연결 실패와 Kubespray 실패를 구분할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|2. Node Pre-setting]], [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Kubespray]] |
| 파괴적 디스크 작업 전에 무엇을 확인해야 하는지 말할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/00. Initial VM Setting|0. 초기 VM 설정]] |

## 10. 읽을 문서와 읽는 목적

1. [[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|8/21 최신 실행 일정]]
   - 8/31 범위 고정
2. [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
   - Step 0~3의 위치와 선후관계
3. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/00. Initial VM Setting|0. 초기 VM 설정]]
   - VM·역할·disk·LB를 무엇으로 확인하는지
4. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/01. Bastion Node Pre-setting|1. Bastion 노드 사전 설정]]
   - 설치 실행점을 만드는 조건
5. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|2. K8S 클러스터 노드 사전 설정]]
   - Kubespray 이전 Node 조건
6. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
   - Inventory와 변수의 의미
7. [[10. 기준 및 설계/클러스터 카탈로그/클러스터 카탈로그|클러스터 카탈로그]]
   - 기존 완성환경을 정상 비교 기준으로 보는 연습

## 11. 반드시 답할 수 있어야 할 질문

1. 왜 VM을 받았다고 바로 Kubespray를 실행하면 안 되는가?
2. Bastion은 무엇을 기준화하는 노드인가?
3. Master·ETCD·Router·Infra·Worker는 왜 별도 그룹인가?
4. ETCD 노드에서 `/var/lib/etcd`를 따로 보는 이유는 무엇인가?
5. VIP-A와 VIP-B의 backend 역할은 어떻게 다른가?
6. `dspaas` sudo가 대화형으로만 되고 `sudo -n`이 안 되면 왜 문제인가?
7. `hosts.yaml`의 잘못된 IP 하나가 어떤 결과를 만들 수 있는가?
8. Pod CIDR과 Service CIDR은 어떻게 다르며 왜 중복 여부를 확인해야 하는가?
9. Registry 주소와 Kubernetes version은 왜 설치 전에 고정해야 하는가?
10. Ansible ping 성공 후에도 무엇을 더 확인해야 9/1로 넘어갈 수 있는가?

## 12. 직접 연습할 것

### 연습 1 — VM 역할표 복원

문서를 보지 않고 다음 표를 그린다.

```text
Role | 하는 일 | 설치 전 꼭 확인할 것 | 이후 영향
Bastion
Master
ETCD
Router
Infra
Worker
```

### 연습 2 — Inventory 읽기

`03.md`의 `hosts.yaml` 예시를 열고 각 host가 왜 해당 group에 있는지 한 줄씩 설명한다. **예시 IP 자체를 외우지 않는다.**

### 연습 3 — 변수에서 의미 찾기

다음 값을 문서에서 찾아 각각 한 문장으로 의미를 설명한다.

```text
loadbalancer_apiserver
cluster_name
kube_service_addresses
kube_pods_subnet
service_domain
registry_host
kube_version
```

### 연습 4 — Preflight를 말로 설명

빈 화면에서 다음 순서를 5분 안에 설명한다.

```text
대상 확인
→ VM / disk
→ LB
→ Bastion
→ Node
→ Inventory
→ Ansible 연결
```

## 13. 정상 상태를 내가 설명할 수 있는가

8/31 종료 상태를 다음처럼 이해한다.

```text
신규 Member VM 실제값이 확정됨
+ 역할별 filesystem/권한 조건을 확인함
+ Bastion에서 대상 노드 접근 가능
+ Node Pre-setting 핵심 조건 확인
+ Inventory·변수가 신규 Member VM 설계와 일치
+ Ansible 연결과 sudo 가능
=
9/1 Kubespray 실행에 들어갈 준비가 됨
```

## 14. 문제 상황 사고 연습

### 사례 1 — Ansible이 특정 노드만 실패

```text
문제 이해
→ Kubernetes 원인이 아니라 설치 전 연결 조건 문제인지 먼저 판단한다.
확인된 사실
→ 어느 노드에서 어떤 단계가 실패했는가?
차이
→ 정상 노드와 실패 노드의 SSH·sudo·repo·hostname·IP 차이는?
다음 판단을 가를 확인 하나
→ 같은 Bastion에서 해당 노드로 passwordless SSH와 sudo가 실제 되는가?
```

### 사례 2 — Inventory IP와 실제 VM IP가 다름

```text
원인을 생각하기 전에
→ 실제 VM 출력과 승인된 신규 Member VM 목록 중 어느 값이 기준인지 확인한다.
→ 기존 Xi'an 카탈로그 값을 복사한 흔적이 있는지 본다.
→ Inventory를 실행하지 않고 먼저 수정 근거를 확정한다.
```

### 사례 3 — `/dev/sdb`가 예상과 다름

```text
파티션 명령을 치지 않는다.
→ hostname/role 확인
→ lsblk/findmnt/PV·VG·LV 확인
→ 승인된 DATA disk 식별과 비교
→ 결과가 맞을 때만 다음 판단
```

## 15. 예상 질문

| 예상 질문 | 핵심 답변 방향 | 현재 답변 가능 여부 |
|---|---|---|
| 왜 Bastion이 클러스터마다 하나씩 필요한가요? | 설치·관리 실행점과 환경 기준 분리 | 미평가 |
| ETCD 노드는 왜 disk가 다른가요? | Kubernetes 상태 저장 경로 분리 | 미평가 |
| VIP-A와 VIP-B를 하나로 쓰면 안 되나요? | API와 Ingress backend 역할이 다름 | 미평가 |
| Inventory는 자동으로 만들 수 없나요? | 자동화 가능 여부보다 실제 설계값 검증이 선행 | 미평가 |
| Node가 모두 SSH 되면 준비 끝인가요? | sudo·repo·package·filesystem 등 추가 조건 필요 | 미평가 |
| 기존 Xi'an `hosts.yaml`을 복사해 IP만 바꾸면 되나요? | group·역할·CIDR·domain·registry까지 신규 설계와 대조 필요 | 미평가 |

## 16. 학습 기록

### 새로 이해한 것

-

### 설명하다 막힌 것

-

### 실제로 한번 더 해봐야 할 것

-

### 9/1 공부로 넘길 것

-

## 17. 8/31 준비 완료 기준

- [ ] Step 0~3 준비의 선후관계를 설명할 수 있다.
- [ ] 노드 역할 6개를 구분해 설명할 수 있다.
- [ ] Bastion 준비의 목적과 주요 범주를 말할 수 있다.
- [ ] Node Pre-setting의 주요 범주와 이유를 말할 수 있다.
- [ ] Inventory의 host/group 구조를 읽을 수 있다.
- [ ] VIP·CIDR·Domain·Registry·version의 의미와 위치를 찾을 수 있다.
- [ ] 신규 Member VM 값과 기존 Xi'an 값을 섞지 않는다.
- [ ] 파괴적 disk 작업 전 확인할 기준을 설명할 수 있다.
- [ ] Ansible 연결 실패 시 Kubernetes 원인으로 뛰어가지 않고 연결 조건부터 구분할 수 있다.
- [ ] 9/1 Playbook 실행 전에 무엇이 완료되어야 하는지 2분 안에 설명할 수 있다.


---
