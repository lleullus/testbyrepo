---
title: "2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증"
status: current
doc_type: build-note
scope: "2026-09-01 신규 Member Cluster Kubespray 실행, Kubernetes API·Node·System Pod·CNI·DNS 검증 및 실패 범위 판정"
created: "2026-08-15"
updated: "2026-08-28"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거]]"
---

# 2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증

> [!important] 이 문서의 역할
> 이 문서는 9/1 신규 Member Kubernetes 구축일의 **현장 수행·판정 Source of Truth**이다. 8/31에 확정한 Inventory·환경값·Ansible 연결을 입력으로 Kubespray를 실행하고, 로그의 최초 실패 지점을 좁히며, 설치 후 API·Node·Control Plane·DNS·CNI·ETCD·Runtime이 실제로 성립했는지 여러 독립 증거로 판정한다. 강의의 설명 순서와 Teach-back은 아래 강사용 대본을 사용하고, 정확한 실행·검증 명령과 현장값은 이 문서와 원본 Runbook을 따른다.
>
> 날짜와 수행 범위는 [[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|8/21 최신 실행 일정]]을 최우선으로 하며, Playbook 종료 자체가 다음날 Storage 단계로 넘어가는 완료 조건은 아니다.

### 9/1 강사용 대본

- [[출장/20. 교육/2026-09-01/오전/01. Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본|오전 - Kubespray 실행·로그 판독]]
- [[출장/20. 교육/2026-09-01/오후/01. Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본|오후 1 - Control Path 검증]]
- [[출장/20. 교육/2026-09-01/오후/02. External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본|오후 2 - Application 경로·9/2 Gate]]

> [!success] 9/1 종료 Gate
> 다음날 Storage로 넘어가는 판정은 강사용 대본의 `KUBERNETES BASE PASS / BLOCKED`를 사용한다. 핵심 Kubernetes 기반 오류가 남으면 `BLOCKED`로 판정하고 다음 단계로 넘기지 않는다.

## 1. 9/1 확정 범위

- Kubespray Playbook 실행
- 진행 로그 확인
- 실패 지점 확인과 필요한 재실행
- Kubernetes API 확인
- Node 상태 확인
- System Pod 상태 확인
- 기본 네트워크 상태 검증
- 설치 과정의 오류와 설정값 리뷰
- 교육생이 직접 구축·검증

이날의 핵심 질문은 다음이다.

> **Playbook이 끝났다는 것과 Kubernetes Cluster가 정상적으로 구축됐다는 것은 어떻게 다른가?**

## 2. 머릿속에 있어야 할 흐름

```text
8/31에 검증한 Inventory·변수·Ansible 연결
→ Kubespray cluster.yml 실행
→ Ansible task / recap 확인
→ 실패가 있으면 최초 실패 범위 확인
→ API 접근 확인
→ Node 등록·Role·Version 확인
→ Control Plane / System Pod 확인
→ CNI / CoreDNS / Ingress 기본 구성 확인
→ 전역 변수와 실제 Cluster 상태 대조
→ 9/2 Storage 설치로 이동
```

### 반드시 분리할 성공

```text
ansible-playbook 종료 코드 0
≠ 모든 설정값이 맞다

Node Ready
≠ Kubernetes 핵심 컴포넌트 전체 검증 완료

System Pod Running
≠ Storage·KubeSphere까지 DKS 구축 완료
```

## 3. Playbook 실행에서 이해해야 할 것

근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]

### 실행 명령보다 먼저 설명할 것

- `cluster.yml`은 `hosts.yaml`과 변수 파일을 입력으로 사용한다.
- 같은 Playbook이라도 Inventory·CIDR·VIP·Registry가 다르면 다른 Cluster를 만든다.
- `--become`은 대상 노드에서 root 권한이 필요한 task를 수행하기 위한 것이다.
- 실패 시 명령을 무조건 처음부터 반복하는 것이 아니라 **어느 host의 어느 task에서 처음 실패했는지** 본다.

### 로그에서 먼저 볼 것

```text
어느 Host인가?
어느 Task인가?
FAILED / UNREACHABLE인가?
모든 노드 공통인가, 특정 노드만인가?
Ansible recap에서 failed/unreachable이 몇 개인가?
```

원인을 바로 추정하기보다 **실패 위치를 먼저 고정**한다.

## 4. 설치 후 전역 설정 대조

`03.md`의 배포 후 검증은 단순 Pod 조회보다 먼저 Cluster 전역 설정을 확인한다.

내가 설명할 수 있어야 할 항목:

- Control Plane Endpoint = VIP-A
- Kubernetes version
- Cluster DNS domain
- Pod subnet
- Service subnet
- Node CIDR block size 등 설치 설계 관련 설정

여기서 중요한 것은 숫자를 암기하는 것이 아니다.

> **8/31에 넣은 설계값이 9/1 만들어진 Cluster에 실제로 반영됐는지 확인하는 단계**라는 점을 설명할 수 있어야 한다.

## 5. Kubernetes 핵심 컴포넌트 검증 구조

### Control Plane

- kube-apiserver
- kube-controller-manager
- kube-scheduler

### Node 공통

- kube-proxy
- kubelet 상태

### DNS

- CoreDNS

### CNI

- calico-node
- calico-controller
- 환경에 따른 Typha 등

### Ingress / Add-on

- ingress-nginx-controller
- metrics-server
- 기타 bundle이 설치하는 기본 addon

정확한 Pod suffix를 외우지 않는다. **어떤 컴포넌트가 어느 역할 노드에 몇 개쯤 배치되어야 하는지**를 이해한다.

## 6. Node 상태를 볼 때 알아야 할 것

`kubectl get nodes -o wide`에서 최소 다음을 읽을 수 있어야 한다.

```text
NAME
STATUS
ROLES
VERSION
INTERNAL-IP
OS
CONTAINER-RUNTIME
```

그리고 다음을 구분한다.

```text
Node Ready
→ kubelet과 Control Plane의 기본 Node 상태 보고가 성립

하지만
→ CNI, DNS, 특정 addon, Storage, Ingress까지 모두 정상이라는 뜻은 아님
```

## 7. ETCD·CRI·CNI를 큰 구조로 설명하기

### External ETCD

- Kubernetes 상태 저장소
- API Server가 external ETCD endpoint를 사용
- `etcdctl`로 member와 endpoint status를 확인할 수 있음
- 인증서·endpoint 값은 대상 Cluster 기준으로 확인

### CRI / containerd

- Kubernetes가 Container를 실행할 런타임
- Registry 설정과 image pull 경로가 이후 workload 실행에 영향을 줌

### CNI / Calico

- Pod Network를 구성
- Pod CIDR과 실제 network plugin 설정이 연결됨
- `calico-node`가 Running이라는 사실과 실제 통신 성공을 구분

9/1에는 세부 설정을 모두 외우기보다 **ETCD=상태, CRI=Container 실행, CNI=Pod Network**라는 관계를 명확히 한다.

## 8. 숙지 수준 분류

### A. 문서 없이 바로 설명할 것

- [ ] Kubespray가 어떤 입력으로 Cluster를 만드는지
- [ ] Ansible task 실패와 Kubernetes runtime 문제의 차이
- [ ] Ansible recap에서 무엇을 보는지
- [ ] API·Node·Control Plane·CNI·DNS를 왜 따로 검증하는지
- [ ] `Ready` 하나로 설치 완료를 선언하면 안 되는 이유
- [ ] External ETCD·containerd·Calico의 역할
- [ ] VIP-A가 API 검증에서 왜 중요한지
- [ ] 9/2 Storage가 별도 단계인 이유

### B. 문서를 보며 정확히 수행·설명할 것

- [ ] `ansible-playbook` 실행 명령 찾기
- [ ] Node 상태 확인 명령 찾기
- [ ] `kubeadm-config`에서 전역 변수 확인 방법 찾기
- [ ] Control Plane Pod 조회 방법 찾기
- [ ] CoreDNS·Calico·Ingress Controller 확인 방법 찾기
- [ ] ETCD member/endpoint status 확인 절차 찾기
- [ ] containerd / crictl 버전·설정 확인 위치 찾기
- [ ] kube-proxy mode와 node label/taint 확인 위치 찾기

### C. 실제 실행 때 새로 확인할 것

- Playbook task 결과와 실행 시간
- 실제 실패 host/task
- 실제 Node 이름·Role·IP·Version
- 실제 Pod 이름·IP·재시작 횟수
- 실제 API health
- 실제 ETCD member/leader 상태
- 실제 CNI/DNS/Ingress 상태

## 9. 내가 지금 부족한 곳을 찾는 자가점검

| 질문 | 현재 상태 | 막히는 부분 | 학습 문서 |
|---|---|---|---|
| `cluster.yml`이 무엇을 입력으로 사용하는지 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Kubespray]] |
| Ansible recap을 보고 실패 범위를 말할 수 있는가? | 미평가 |  | 3. Kubespray |
| API 정상과 Node Ready를 별도로 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
| Control Plane 세 컴포넌트의 역할을 말할 수 있는가? | 미평가 |  | 3. Kubespray |
| CoreDNS가 왜 별도 검증 대상인지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
| Calico가 무엇을 담당하는지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
| External ETCD 검증이 왜 필요한지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
| containerd Registry 설정이 이후 어떤 문제와 연결되는지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
| Node Ready인데 다음 날 Storage로 넘어가면 안 되는 사례를 말할 수 있는가? | 미평가 |  | [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]] |

## 10. 읽을 문서와 목적

1. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
   - 실행과 배포 후 검증의 전체 뼈대
2. [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
   - Step 3이 전체에서 차지하는 위치
3. [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
   - 설치 완료를 어떤 증적으로 봐야 하는지
4. [[2026-08-31 Member 구축 1일차 - 환경 확인 및 Pre-setting]]
   - Playbook 입력이 어디서 왔는지 연결

## 11. 반드시 답할 수 있어야 할 질문

1. `cluster.yml` 실행 전 마지막으로 무엇을 확인해야 하는가?
2. Playbook이 특정 한 노드에서만 실패했다면 무엇을 먼저 비교하는가?
3. `UNREACHABLE`과 task `FAILED`는 조사 시작점이 어떻게 다른가?
4. `kubectl get nodes`가 성공한다는 것은 무엇을 증명하는가?
5. API health와 Node Ready를 왜 모두 보는가?
6. Control Plane Pod가 모두 Running이어도 CoreDNS를 별도로 보는 이유는?
7. Calico가 비정상이면 어떤 종류의 증상이 생길 수 있는가?
8. External ETCD endpoint를 다른 Cluster 값으로 잘못 넣으면 무엇이 문제인가?
9. Ingress Controller의 NodePort와 VIP-B는 어떤 관계인가?
10. 9/2 Storage로 넘어가기 위한 최소 Kubernetes 기준은 무엇인가?

## 12. 직접 연습할 것

### 연습 1 — 설치 로그 판독

과거/참조 Playbook 로그에서 다음만 먼저 찾는 연습을 한다.

```text
첫 FAILED task
대상 host
공통 실패인가 특정 host인가
recap의 failed/unreachable
```

그 뒤에만 원인 후보를 생각한다.

### 연습 2 — 배포 후 검증 순서 복원

문서 없이 다음 순서를 적는다.

```text
설계값 대조
→ API
→ Node
→ Control Plane
→ DNS
→ CNI
→ Ingress/Add-on
→ ETCD/Runtime 추가 확인
```

### 연습 3 — 명령의 질문을 말하기

아래 명령을 보기 전에 “무엇을 확인하기 위한 것인지”를 먼저 말한다.

```bash
kubectl get nodes -o wide
kubectl -n kube-system describe cm kubeadm-config
kubectl get pod -A -o wide
kubectl get crd
kubectl get svc -n ingress-nginx
```

## 13. 정상 상태를 내가 설명할 수 있는가

```text
Playbook 실행 완료
+ Ansible recap에 미해결 실패 없음
+ API 접근 정상
+ 설계한 VIP/CIDR/Domain/Version 반영 확인
+ Node Role/Ready 상태 정상
+ Control Plane 핵심 Pod 정상
+ CoreDNS/CNI/Ingress 기본 구성 정상
+ ETCD/Runtime에 명백한 이상 없음
=
Storage 구축으로 넘어갈 Kubernetes 기반이 마련됨
```

## 14. 문제 상황 사고 연습

### 사례 1 — Playbook은 성공했는데 API 접속 실패

```text
확인된 사실
→ Ansible task는 완료됐다.
차이
→ API VIP/TLS endpoint는 응답하지 않는다.
다음 판단을 가를 확인
→ Master 자체 API와 VIP-A 경로 중 어디가 먼저 실패하는가?
```

### 사례 2 — 한 Node만 NotReady

```text
전체 Cluster 재설치로 가지 않는다.
→ 해당 Node가 다른 Node와 무엇이 다른지 확인
→ kubelet / network / role / pre-setting 차이를 좁힘
```

### 사례 3 — Node는 Ready인데 DNS가 안 됨

```text
Node Ready라는 정보의 범위를 과대해석하지 않는다.
→ CoreDNS Pod와 Service
→ Pod Network
→ 실제 DNS 질의
순서로 별도 기능을 확인한다.
```

## 15. 예상 질문

| 예상 질문 | 핵심 답변 방향 | 현재 답변 가능 여부 |
|---|---|---|
| Playbook 성공이면 설치 성공 아닌가요? | 실행 성공과 기능 검증은 별도 | 미평가 |
| 왜 `Ready` 외에 System Pod까지 보나요? | Node 상태와 Cluster 기능은 다른 증거 | 미평가 |
| ETCD는 왜 Kubernetes 밖에 따로 있나요? | external ETCD 설계와 상태 저장 역할 | 미평가 |
| Calico가 하는 일이 정확히 뭔가요? | Pod Network/CNI | 미평가 |
| 설치가 실패하면 그냥 다시 돌리면 안 되나요? | 최초 실패 위치와 영향 범위를 먼저 고정 | 미평가 |

## 16. 학습 기록

### 새로 이해한 것
-

### 로그를 읽다가 막힌 것
-

### 직접 조회가 더 필요한 것
-

### 9/2로 넘길 것
-

## 17. 9/1 준비 완료 기준

- [ ] Kubespray 입력과 실행의 관계를 설명할 수 있다.
- [ ] Ansible 실패를 host/task/recap으로 좁힐 수 있다.
- [ ] API·Node·Control Plane·DNS·CNI를 별도 증거로 설명할 수 있다.
- [ ] ETCD·CRI·CNI의 큰 역할을 설명할 수 있다.
- [ ] `Node Ready ≠ DKS 전체 구축 완료`를 설명할 수 있다.
- [ ] 배포 후 검증 명령을 문서에서 바로 찾을 수 있다.
- [ ] 대표 실패 사례에서 다음 판단을 가를 확인 하나를 고를 수 있다.
- [ ] 9/2 Storage가 시작될 수 있는 Kubernetes 기준을 말할 수 있다.
