---
title: "Xi'an 현지 기술 전수 강사 전체 확인"
status: current
doc_type: instructor-master-checklist
scope: "2026-08-24~09-04 최신 실행 일정, 최종 배포 Manual 1.1~6.5, 신규 Member 구축 5.0~5.5.2, 기존 Host Join 및 현장 인수 전체 강사 확인 기준"
created: "2026-08-15"
updated: "2026-08-28"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획]]"
---

# Xi'an 현지 기술 전수 강사 전체 확인

> [!important] 이 문서의 역할
> 이 문서는 Manual 이름만 체크하는 목록이 아니다. **강사가 8/24~9/4 전체 일정과 각 날짜 문서, 최종 배포 Manual, 실제 신규 Member 구축, 기존 Host Join, 교육생 Teach-back, 현장 증적과 철수까지 하나의 체계로 연결해서 준비·진행·판정하는 최상위 확인 문서**다.
>
> 상세 내용은 각 일자 문서와 원문 Manual을 줄이지 않고 그대로 사용한다. 이 문서는 그 내용을 요약해서 대체하는 것이 아니라 **어느 문서를 언제 쓰고, 무엇이 통과되어야 다음 단계로 넘어가는지, 무엇을 현장에서 다시 확인해야 하는지**를 연결한다.

> [!success] 최신 기준
> 출장 전체 Source of Truth는 [[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|2026-08-24~09-04 Xi'an 현지 교육 실행 일정]]이다. 기존 Xi'an **Host Cluster는 이미 구축 완료**되어 있으며 이번 출장에서 새로 구축하지 않는다. 신규 구축 대상은 **Member Cluster**이며 기술적 최종 완료 조건은 **9/3 신규 Member Monitoring·KubeSphere 구성 → 기존 Host Join → Multi-Cluster 정상 확인**이다.

> [!important] 작성·교육·판정 규율
> 교육·구축·Troubleshooting·검증·인수 문서를 작성하거나 현장에서 판정할 때는 [[출장/01. 출장 교육·구축 문서 작성 및 판정 핵심 규율|출장 교육·구축 문서 작성 및 판정 핵심 규율]]을 공통 규율로 사용한다. 일정·승인 실제값·원본 Runbook의 기술 사실은 그대로 우선하되, **한 독자 변화·최소 인과 줄기·증거 범위 제한·Gate·인계·최종 Teach-back**은 이 규율을 따른다.

> [!warning] 이전 문서 사용 금지
> `출장/90. 이전본/` 아래 문서는 일정 변경 전 사고·자료를 보존하기 위한 이전본이다. Frontmatter에 `status: current`가 남아 있더라도 **현재 현장 수행 기준으로 사용하지 않는다.** 최신 일정과 현재 카테고리 문서를 우선한다.

## 1. 강사가 기억해야 할 단 하나의 전체 흐름

```text
8/24 현장 준비
→ 8/25 Kubernetes 기초·DKS 아키텍처
→ 8/26 KubeSphere Operation 1.1~1.7
→ 8/27 Operations 2.1~2.5 + Harbor 3.1~3.3
→ 8/28 User 4.1~4.4 + Troubleshooting 6.1~6.5
→ 8/29~30 교육 보완·구축 준비
→ 8/31 신규 Member 실제 환경·Pre-setting·Inventory
→ 9/1 Kubespray·Kubernetes 검증
→ 9/2 Storage 구성·Mount·Write/Read 검증
→ 9/3 Member Monitoring·KubeSphere·기존 Host Join·Multi-Cluster 최종 인수
→ 9/4 문서·증적·잔여 항목·Credential·장비 정리 후 철수
```

### 반드시 함께 말할 네 원칙

1. 운영 Manual 교육을 먼저 하고 실제 Member 구축을 다음 주에 한다.
2. 기존 Host는 재설치 대상이 아니라 정상 비교와 Join 대상이다.
3. 각 단계는 `명령 성공`보다 **기능 증거와 다음 단계 Gate**로 완료를 판정한다.
4. 9/4는 기술 작업 Buffer가 아니다.

---

# Part 1. 현재 출장 문서 기준

## 2. 출장 홈과 일정

- [ ] [[출장/00. 출장 홈|00. 출장 홈]]을 열면 모든 현재 문서에 도달할 수 있다.
- [ ] [[출장/10. 일정 및 범위/2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|최신 실행 일정]]을 전체 Source of Truth로 사용한다.
- [ ] 일정표의 날짜·오전·오후·Manual 범위를 현지 총괄과 공유한다.
- [ ] 일자 문서가 일정표와 다르면 일정표를 우선하고 해당 문서를 교정한다.
- [ ] `90. 이전본`은 현재 실행 탐색 경로에서 분리한다.

## 3. 8/24 현장 준비

기준 문서: [[2026-08-24 현장 준비|2026-08-24 Xi'an 현장 준비]]

강사 확인:

- [ ] 출입·Laptop 반입·촬영·자료 반출 규칙을 안다.
- [ ] 교육장·화면·전원·Adapter·Network 상태를 확인한다.
- [ ] 통역 참여 시간과 기술 용어를 맞춘다.
- [ ] 교육생 수·역할·Kubernetes 경험을 확인한다.
- [ ] 8/25 한국어·중국어 최종 교육자료를 준비한다.
- [ ] 실제 UI 접근 실패 시 대체 진행 자료가 있다.
- [ ] 분야별 현지 담당자와 국내 지원 경로를 안다.
- [ ] 8/24에는 상태 변경 작업을 하지 않는다.
- [ ] 8/25 시작 상태를 READY / READY WITH CONSTRAINTS / BLOCKED로 판정한다.

## 4. 8/25 Kubernetes 및 DKS 아키텍처

현재 기준 자료:

- [ ] [[출장/20. 교육/2026-08-25 Kubernetes 및 DKS 아키텍처/01. 교육 교재 - 최종본|01. 교육 교재 - 최종본]]
- [ ] [[출장/20. 교육/2026-08-25 Kubernetes 및 DKS 아키텍처/02. 교육 교재 - 최종본 - 中文版|02. 교육 교재 - 최종본 - 中文版]]
- [ ] [[출장/20. 교육/2026-08-25 Kubernetes 및 DKS 아키텍처/03. 교육 교재 - 배포용|03. 교육 교재 - 배포용]]
- [ ] [[출장/20. 교육/2026-08-25 Kubernetes 및 DKS 아키텍처/04. 교육 교재 - 배포용 - 中文版|04. 교육 교재 - 배포용 - 中文版]]
- [ ] [[출장/20. 교육/2026-08-25 Kubernetes 및 DKS 아키텍처/05. 강사용 전체 대본|05. 강사용 전체 대본]]
- [ ] [[출장/20. 교육/2026-08-25 Kubernetes 및 DKS 아키텍처/06. 강사용 전체 메모|06. 강사용 전체 메모]]

강사가 설명할 전체 연결:

```text
Server / VM
→ Container / Image / Registry
→ Kubernetes Cluster
→ Control Plane / Worker
→ Pod / Deployment
→ Service / Ingress
→ Storage / PVC / CSI / Trident
→ Monitoring / Prometheus / Grafana
→ DKS Node Role
→ KubeSphere Host / Member
→ Xi'an 실제 구조
```

확인:

- [ ] 공개 Kubernetes 개념과 Xi'an 실제값을 구분한다.
- [ ] Host와 Member를 구분한다.
- [ ] VIP-A와 VIP-B를 구분한다.
- [ ] Harbor가 Image 공급 경로임을 설명한다.
- [ ] StorageClass→PVC→PV→Mount 관계를 설명한다.
- [ ] 8/26~28 운영 Manual이 어디에 연결되는지 설명한다.
- [ ] 8/31부터 신규 Member를 구축한다는 후속 일정을 설명한다.

## 5. 8/26 KubeSphere Operation

기준 문서: [[출장/20. 교육/2026-08-26 KubeSphere Operation 기술 전수|2026-08-26 KubeSphere Operation 기술 전수]]

오전:

- [ ] 별도 교육 참석을 일정에 반영한다.

오후 Manual:

- [ ] 1.1 Creating Workspaces&projects
- [ ] 1.2 Inviting a new member
- [ ] 1.3 Assigning project roles to users
- [ ] 1.4 Setting quotas
- [ ] 1.5 KubeSphere Role-Based Access Control
- [ ] 1.6 Enable users using kubectl CLI
- [ ] 1.7 KubeSphere SECDS-ROOT.crt(CA.crt) ConfigMap Mount

강사 완료 기준:

- [ ] 신청→Workspace→Project/Namespace→Member→Role→Quota를 연결한다.
- [ ] `Admin → project-operator`, `User → project-viewer`를 설명한다.
- [ ] `project-admin`은 별도 권한임을 설명한다.
- [ ] Workspace Member와 Project Member를 구분한다.
- [ ] Quota와 RBAC을 다른 경계로 설명한다.
- [ ] kubectl은 별도 Bastion·kubeconfig·context·VIP-A 경로임을 설명한다.
- [ ] x509에서 CA ConfigMap→ks-apiserver Mount→Rollout→기능 재확인을 설명한다.
- [ ] kubeconfig·Token·CA 원문·Private Key를 노출하지 않는다.

## 6. 8/27 Operations Manual 및 Harbor Manual

기준 문서: [[출장/20. 교육/2026-08-27 Operations Manual 및 Harbor Manual 기술 전수|2026-08-27 Operations Manual 및 Harbor Manual 기술 전수]]

### 오전 — Operations 2.1~2.5

- [ ] 2.1 Adding a worker node to cluster using kubespray
- [ ] 2.2 Add taint and node-label when adding node
- [ ] 2.3 DKS FAQ
- [ ] 2.4 Utilizing the Kubernetes Native API
- [ ] 2.5 Renewing API Server Certificates

강사 완료 기준:

- [ ] Worker 추가를 VM·Pre-setting→Inventory→scale→Workload·Storage 검증까지 설명한다.
- [ ] label·taint·nodeSelector·toleration 네 요소를 연결한다.
- [ ] FAQ를 상세 Runbook이 아니라 요청 라우터로 사용한다.
- [ ] Native API의 Service·Ingress·Source 제한·Authentication·RBAC을 함께 설명한다.
- [ ] API Certificate 갱신의 Backup과 Master one-by-one 원칙을 설명한다.
- [ ] 다음 Master로 넘어가기 전 `readyz`·`livez`·Static Pod·API Gate를 설명한다.
- [ ] Bastion kubeconfig와 KubeSphere 재연결까지 영향범위를 설명한다.
- [ ] 고위험 작업을 교육 목적으로 운영 환경에서 임의 실행하지 않는다.

### 오후 — Harbor 3.1~3.3

- [ ] 3.1 SCS Harbor Installation
- [ ] 3.2 Create a project
- [ ] 3.3 Managing Users

강사 완료 기준:

- [ ] Docker·offline installer·Certificate·harbor.yml·data_volume의 역할을 설명한다.
- [ ] Harbor Container Running과 기능 정상의 차이를 설명한다.
- [ ] Private Project와 승인 Quota를 설명한다.
- [ ] ProjectAdmin과 Developer를 구분한다.
- [ ] KubeSphere Project와 Harbor Project를 혼동하지 않는다.

## 7. 8/28 User Manual 및 Troubleshooting Guide

기준 문서: [[출장/20. 교육/2026-08-28 User Manual 및 Troubleshooting Guide 기술 전수|2026-08-28 User Manual 및 Troubleshooting Guide 기술 전수]]

### 오전 — User 4.1~4.4

- [ ] 4.1 DS Kubernetes Service Overview
- [ ] 4.2 Harbor User Guide
- [ ] 4.3 KubeSphere User Guide
- [ ] 4.4 GSAMS Application Guide for Accessing Domestic DKS URLs from SCS and SAS

강사 완료 기준:

- [ ] DKS 사용자 이용 흐름을 Account·Project·Harbor·Workload·HTTP까지 설명한다.
- [ ] Harbor CA→Login→Pull→Tag→Push→Artifact를 설명한다.
- [ ] PVC·Image Secret·Deployment·Service·Endpoint·Ingress·HTTP를 하나로 연결한다.
- [ ] GSAMS 해외 사업장 신청 적용 조건과 입력 형식을 설명한다.
- [ ] GSAMS 가이드가 URL 유효성·승인 여부·승인 후 통신을 정하지 않는다는 경계를 설명한다.

### 오후 — Troubleshooting 6.1~6.5

- [ ] 6.1 Harbor Access, Login, and Image Push/Pull Errors
- [ ] 6.2 Accessing Kubernetes Dashboard, Logging In, and Regenerating the Token
- [ ] 6.3 When a NetApp NFS PVC Is Bound but Pod Mount Fails
- [ ] 6.4 When a Project Is Not Visible or You Do Not Have Permission to Create Resources
- [ ] 6.5 KubeSphere ImagePullBackOff When Deploying a Private Image

강사 완료 기준:

- [ ] Harbor 문제를 Network·CA·Authentication·Repository/Tag·Role로 분리한다.
- [ ] Dashboard에서 대상 Cluster·ServiceAccount·Token Secret을 먼저 확인한다.
- [ ] 새 Dashboard Token을 검증하기 전에 기존 Token을 삭제하지 않는다.
- [ ] NFS에서 `PVC Bound ≠ Pod Mount`를 설명한다.
- [ ] Project 문제를 Namespace→Workspace Member→Project Member→Role→Quota 순서로 본다.
- [ ] ImagePullBackOff에서 Pod Event를 먼저 읽는다.
- [ ] 복구 후 동일 정상 경로의 최종 기능 결과를 확인한다.

## 8. 8/29~30 Buffer / 구축 준비

기준 문서: [[2026-08-29~30 운영 교육 보완 및 구축 준비|2026-08-29~30 운영 교육 보완 및 신규 Member 구축 준비]]

- [ ] 1.1~1.7 교육 결과를 확인한다.
- [ ] 2.1~2.5 교육 결과를 확인한다.
- [ ] 3.1~3.3 교육 결과를 확인한다.
- [ ] 4.1~4.4 교육 결과를 확인한다.
- [ ] 6.1~6.5 교육 결과를 확인한다.
- [ ] 질문을 개념·절차·실제값·정책·장애로 분류한다.
- [ ] 통역·용어 혼동을 보완한다.
- [ ] 시연 실패와 대체 자료를 기록한다.
- [ ] 교육생 Teach-back 결과를 기록한다.
- [ ] 신규 Member VM·Bastion·Cluster 전역값·Inventory 기준본 확보 상태를 확인한다.
- [ ] Network·Storage·Registry 외부 의존성과 담당자를 확인한다.
- [ ] 8/31을 GO / GO WITH CONSTRAINTS / BLOCKED로 판정한다.

## 9. 8/31 Member 구축 1일차

기준 문서: [[출장/30. 구축/2026-08-31 Member 구축 1일차 - 환경 확인 및 Pre-setting|2026-08-31 Member 구축 1일차 - 환경 확인 및 Pre-setting]]

수행 범위:

```text
신규 Member VM 실제값
→ Role·hostname·IP·Disk
→ VIP·Network
→ Bastion
→ Node Pre-setting
→ hosts.yaml·Inventory·Variables
→ SSH·sudo·Ansible 연결
→ 9/1 Kubespray Gate
```

확인:

- [ ] VM·Node Role과 승인 설계를 대조한다.
- [ ] 파괴적 Disk 작업 전에 `lsblk`·`findmnt`·fstab·LVM을 확인한다.
- [ ] Bastion에서 SSH·`sudo -n`이 된다.
- [ ] Repository·Package·CA·NFS·Swap 전제를 확인한다.
- [ ] VIP-A·VIP-B·CIDR·Domain·Registry·Version의 출처를 안다.
- [ ] 다른 Cluster Inventory 값이 섞이지 않았다.
- [ ] Ansible 연결 실패와 Kubespray 실패를 구분한다.
- [ ] 9/1 Playbook 실행 Gate를 통과한다.

## 10. 9/1 Member 구축 2일차

기준 문서: [[출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증|2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증]]

강사용 대본:
- [[출장/20. 교육/2026-09-01/오전/01. Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본|오전 - Kubespray 실행·로그 판독]]
- [[출장/20. 교육/2026-09-01/오후/01. Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본|오후 1 - Control Path]]
- [[출장/20. 교육/2026-09-01/오후/02. External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본|오후 2 - Application 경로·9/2 Gate]]

수행 범위:

```text
8/31 GO
→ cluster.yml 실행·최초 실패 판독
→ CONTROL PATH PASS
→ ETCD·Runtime·CNI·DNS·Ingress 실제 기능
→ KUBERNETES BASE PASS / BLOCKED
```

확인:

- [ ] 8/31 GO가 현재 Bastion·Bundle·Inventory에서도 유효한지 확인한다.
- [ ] 최초 FAILED / UNREACHABLE Host·Task를 고정한다.
- [ ] Playbook 실행 성공과 Kubernetes 기능 성공을 분리한다.
- [ ] Context·VIP-A·전역 CIDR·Domain·Version을 실제 Cluster와 대조한다.
- [ ] Node Identity·Role·Ready·Version·Internal IP를 확인한다.
- [ ] Control Plane을 Data Plane 성공으로 확대하지 않는다.
- [ ] External ETCD·Runtime·실제 Test Pod·DNS·Ingress 경로를 기능으로 검증한다.
- [ ] 임시 Test Resource 정리까지 확인한다.
- [ ] `KUBERNETES BASE PASS / BLOCKED`로 9/2 진입을 판정한다.

## 11. 9/2 Member 구축 3일차

기준 문서: [[출장/30. 구축/2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증|2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증]]

강사용 대본:
- [[출장/20. 교육/2026-09-02/오전/01. Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본|오전 - Storage 공급 경로]]
- [[출장/20. 교육/2026-09-02/오후/01. PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본|오후 - Storage 실제 사용·9/3 Gate]]

수행 범위:

```text
KUBERNETES BASE PASS
→ Snapshotter·Trident·Backend·StorageClass
→ STORAGE SUPPLY PASS
→ PVC·PV·Pod Mount·Write/Read·재읽기·Cleanup
→ STORAGE PASS / BLOCKED
```

확인:

- [ ] Snapshotter와 Trident 역할을 구분한다.
- [ ] Trident Controller 정상과 Node Plugin 전체 정상을 분리한다.
- [ ] Backend `online`의 증거 범위를 제한한다.
- [ ] StorageClass의 provisioner·reclaimPolicy·volumeBindingMode를 확인한다.
- [ ] `PVC Bound ≠ Pod Mount ≠ Write/Read`를 설명한다.
- [ ] 9/3 Monitoring 배치 Role의 실제 Mount 경로를 확인한다.
- [ ] Data LIF·Source IP·Route·TCP 2049·Export Policy를 첫 실패에 맞게 연결한다.
- [ ] Write·Read·재읽기와 Cleanup·reclaim 결과까지 확인한다.
- [ ] 9/3 Monitoring StorageClass·Namespace·용량을 확정한다.
- [ ] `STORAGE PASS / BLOCKED`로 다음날 진입을 판정한다.

## 12. 9/3 Member 구축 4일차 및 최종 인수

기준 문서: [[출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수|2026-09-03 Member 구축 4일차 - Monitoring·KubeSphere·기존 Host Join 및 최종 인수]]

강사용 대본:
- [[출장/20. 교육/2026-09-03/오전/01. Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본|오전 1 - Member Monitoring]]
- [[출장/20. 교육/2026-09-03/오전/02. Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본|오전 2 - Member KubeSphere·Pre-Join]]
- [[출장/20. 교육/2026-09-03/오후/01. 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본|오후 1 - Host Join·Multi-Cluster]]
- [[출장/20. 교육/2026-09-03/오후/02. 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본|오후 2 - 최종 인수]]

수행 범위:

```text
STORAGE PASS
→ MONITORING PASS
→ MEMBER SELF PASS
→ MULTI-CLUSTER PASS
→ 기존 Cluster 회귀 확인
→ 최종 PASS / PARTIAL / BLOCKED
```

확인:

- [ ] Monitoring PVC 실제 Mount와 현재 Member Identity를 확인한다.
- [ ] Prometheus CRD가 `Established`이고 핵심 Target·Query가 정상이다.
- [ ] External ETCD Target이 `UP`이며 현재 Member Endpoint다.
- [ ] Grafana Datasource·Query·Dashboard가 현재 Member Metric을 사용한다.
- [ ] Monitoring Ingress·VIP-B 실제 기능이 정상이다.
- [ ] KubeSphere installer 실행과 내부 Task 성공을 분리한다.
- [ ] Storage·Registry·ETCD·External Monitoring Endpoint가 현재 Member 값이다.
- [ ] `multicluster.clusterRole=member`와 실제 Platform Workload 배치를 확인한다.
- [ ] `MEMBER SELF PASS` 뒤에만 기존 Host Join을 수행한다.
- [ ] 기존 Host를 재설치하지 않고 Join 전 기준 상태를 기록한다.
- [ ] Host Console 이름뿐 아니라 Status·Resource·Monitoring을 실제 확인한다.
- [ ] 신규 Join 후 기존 Host·PRD·DEV Member 회귀가 없다.
- [ ] `MULTI-CLUSTER PASS` 뒤 최종 인수에서만 `PASS / PARTIAL / BLOCKED`를 사용한다.
- [ ] 보호된 값 원문이 증적에 없고 임시 복사본 정리가 확인된다.

## 13. 9/4 현장 정리 및 철수

기준 문서: [[2026-09-04 현장 정리 및 철수|2026-09-04 Xi'an 현장 정리 및 철수]]

- [ ] 9/3 기술 판정을 임의로 바꾸지 않는다.
- [ ] 9/4에 새로운 기술 변경을 시작하지 않는다.
- [ ] 기능별 증적 위치를 정리한다.
- [ ] 출장 홈·일정·교육·구축·Manual 위치를 인계한다.
- [ ] 이전본 사용 금지 기준을 인계한다.
- [ ] 질문 주차장과 잔여 기술 항목을 인계한다.
- [ ] Blocking·Non-blocking·External·Observation을 구분한다.
- [ ] 각 잔여 항목에 영향·재개조건·담당자·다음 확인을 붙인다.
- [ ] 임시 kubeconfig·Token·JWT·Secret·Private Key 사본을 정리한다.
- [ ] 계정·임시 권한 회수·만료 상태를 확인한다.
- [ ] Browser·Clipboard·Shell History·Screenshot을 확인한다.
- [ ] 장비·출입증·인쇄물·Storage Device를 정리한다.
- [ ] 현지 담당자가 문서와 잔여 항목을 직접 찾아보는 것을 확인한다.
- [ ] CLOSED / CLOSED WITH FOLLOW-UP / NOT READY TO CLOSE로 판정한다.

---

# Part 2. 최종 배포 Manual 목록

## 14. 1. KubeSphere Operation

- [ ] [[50. 운영/04. Kubesphere Operation/01. Creating Workspaces&projects|1.1 Creating Workspaces&projects]]
- [ ] [[50. 운영/04. Kubesphere Operation/02. Inviting a new member|1.2 Inviting a new member]]
- [ ] [[50. 운영/04. Kubesphere Operation/03. Assigning project roles to users|1.3 Assigning project roles to users]]
- [ ] [[50. 운영/04. Kubesphere Operation/04. Setting quotas|1.4 Setting quotas]]
- [ ] [[50. 운영/04. Kubesphere Operation/05. Kubesphere Role-Based Access Control|1.5 KubeSphere Role-Based Access Control]]
- [ ] [[50. 운영/04. Kubesphere Operation/06. Enable users using kubectl CLI|1.6 Enable users using kubectl CLI]]
- [ ] [[50. 운영/04. Kubesphere Operation/07. KubeSphere SECDS-ROOT.crt ConfigMap Mount|1.7 KubeSphere SECDS-ROOT.crt(CA.crt) ConfigMap Mount]]

번역본 위치 확인:

- CN: `50. 운영/중국어 번역/04. Kubesphere Operation/`
- EN: `50. 운영/영어 번역/04. Kubesphere Operation/`

## 15. 2. Operations Manual

최종 배포 목록에는 아래 5개만 포함한다.

- [ ] [[50. 운영/05. Operations Manual/01. Adding a worker node using kubespray|2.1 Adding a worker node to cluster using kubespray]]
- [ ] [[50. 운영/05. Operations Manual/02. Add taint and node-label when adding node|2.2 Add taint and node-label when adding node]]
- [ ] [[50. 운영/05. Operations Manual/03. DKS FAQ|2.3 DKS FAQ]]
- [ ] [[50. 운영/05. Operations Manual/05. Utilizing the Kubernetes Native API|2.4 Utilizing the Kubernetes Native API]]
- [ ] [[50. 운영/05. Operations Manual/06. Renewing API Server Certificates|2.5 Renewing API Server Certificates]]

현재 최종 배포 목록 제외:

- `Failure response training`
- `Kubernetes Dashboard Token 로그인 원복 및 사용 가이드`
- `Kubernetes Dashboard 복구`

제외는 문서 삭제를 의미하지 않는다. 내부 참고·복구 자료로 Obsidian에 남겨 둔다.

번역본 위치 확인:

- CN: `50. 운영/중국어 번역/05. Operations Manual/`
- EN: `50. 운영/영어 번역/05. Operations Manual/`

## 16. 3. Harbor Manual

- [ ] [[50. 운영/06. Harbor Manual/01. Harbor Installation|3.1 SCS Harbor Installation]]
- [ ] [[50. 운영/06. Harbor Manual/02. Create a project|3.2 Create a project]]
- [ ] [[50. 운영/06. Harbor Manual/03. Managing Users|3.3 Managing Users]]

번역본 위치 확인:

- CN: `50. 운영/중국어 번역/06. Harbor Manual/`
- EN: `50. 운영/영어 번역/06. Harbor Manual/`

## 17. 4. User Manual

- [ ] [[50. 운영/07. DKS User Guide/01. DS Kubernetes Service Overview|4.1 DS Kubernetes Service Overview]]
- [ ] [[50. 운영/07. DKS User Guide/02. Harbor User Guide|4.2 Harbor User Guide]]
- [ ] [[50. 운영/07. DKS User Guide/03. KubeSphere User Guide|4.3 KubeSphere User Guide]]
- [ ] [[50. 운영/07. DKS User Guide/04. 해외 사업장 관련 DKS URL GSAMS 신청 가이드|4.4 GSAMS Application Guide for Accessing Domestic DKS URLs from SCS and SAS]]

> [!warning] 4.4 번역본 확인
> Obsidian의 영어·중국어 `07. DKS User Guide`에 4.4 대응 파일이 없다면 배포본과 Vault 동기화 대상이다. 존재 여부를 현지 배포 전 확인하고, 없다는 사실을 다른 4.1~4.3의 번역 완료 여부와 혼동하지 않는다.

## 18. 5. Cluster Setup

최종 배포 Manual:

- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/00. Initial VM Setting|5.0 Initial VM setting]]
- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/01. Bastion Node Pre-setting|5.1 SCS Bastion node pre-setting]]
- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|5.2 SCS K8S Cluster nodes pre-settings]]
- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|5.3 SCS Deploy DKS Cluster using Kubespray]]
- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|5.4 SCS Install storage components]]
- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-1|5.5.1 Install kubesphere - host cluster]] — **Manual에는 존재하지만 이번 출장 수행 범위 제외**
- [ ] [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5.5.2 Install kubesphere - member cluster]]

이번 실제 수행 순서:

```text
5.0
→ 5.1
→ 5.2
→ 5.3
→ 5.4
→ 5.5.2
→ 기존 Host Join
→ Multi-Cluster 확인
```

번역본 위치:

- CN: `30. 구축 및 전환/공통 구축/Xi'an/中文/`
- EN: `30. 구축 및 전환/공통 구축/Xi'an/English/`

## 19. 6. Troubleshooting Guide

- [ ] [[50. 운영/08. 트러블슈팅/Harbor/01. Harbor 접속, 로그인 및 Image Push-Pull 오류|6.1 Harbor Access, Login, and Image Push/Pull Errors]]
- [ ] [[50. 운영/08. 트러블슈팅/Kubernetes/01. Kubernetes Dashboard 접속 및 Token 로그인 가이드|6.2 Accessing Kubernetes Dashboard, Logging In, and Regenerating the Token]]
- [ ] [[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|6.3 When a NetApp NFS PVC Is Bound but Pod Mount Fails]]
- [ ] [[50. 운영/08. 트러블슈팅/KubeSphere/01. Project가 보이지 않거나 리소스 생성 권한이 없는 경우|6.4 When a Project Is Not Visible or You Do Not Have Permission to Create Resources]]
- [ ] [[50. 운영/08. 트러블슈팅/KubeSphere/02. Private Image 배포 시 ImagePullBackOff가 발생하는 경우|6.5 KubeSphere ImagePullBackOff When Deploying a Private Image]]

최종 배포 목록 제외:

- `Ingress를 사용하는 여러 UI가 간헐적으로 504를 반환하는 경우`
- `Kubernetes Native API 접속 및 권한 오류`
- `트러블슈팅 작성 원칙`

위 문서는 내부 참고자료로는 사용할 수 있지만, 8/28 최종 배포 Troubleshooting 6.1~6.5 목차에 추가하지 않는다.

---

# Part 3. 교차 개념 확인

## 20. 환경·대상 구분

아래는 문서 없이 즉시 설명한다.

```text
기존 Host Cluster
≠ 신규 Member Cluster

KubeSphere Host
≠ Kubernetes Control Plane Node

PRD Member
≠ DEV Member

VIP-A
≠ VIP-B

KubeSphere Project
≠ Harbor Project

Workspace
≠ Project / Namespace
```

체크:

- [ ] 어떤 화면·명령을 보기 전에 Cluster·context를 확인한다.
- [ ] 기존 Xi'an 실제값과 신규 Member 실제값을 섞지 않는다.
- [ ] PRD·DEV Domain·VIP·ETCD·Node·Stage를 따로 확인한다.
- [ ] Host Manifest를 Member에 값 몇 개만 바꿔서 적용하지 않는다.

## 21. 성공 상태 과잉 판정 방지

```text
VM 존재
≠ Kubernetes 설치 준비 완료

SSH 성공
≠ sudo·Ansible 실행 준비 완료

Inventory Parse 성공
≠ 실제 설계값 정상

Playbook 성공
≠ Kubernetes 기능 정상

Node Ready
≠ CNI·DNS·Storage·Ingress 정상

StorageClass 존재
≠ Backend 정상

PVC Bound
≠ Pod Mount·Write/Read 정상

Pod Running
≠ Service·HTTP 정상

Service 존재
≠ Endpoint 존재

Secret 존재
≠ Workload가 Secret 사용

Prometheus Pod Running
≠ Target UP

Grafana UI 열림
≠ Datasource·Query 정상

KubeSphere Console 열림
≠ installer Task·Role·Monitoring 정상

Host Console에 Member 이름 표시
≠ Multi-Cluster 기능 정상
```

- [ ] 각 상태가 무엇을 증명하고 무엇을 증명하지 않는지 교육생에게 질문한다.

## 22. 민감정보 경계

문서·화면·메신저·증적에 남기지 않는다.

- [ ] Password
- [ ] Token
- [ ] JWT
- [ ] Private Key
- [ ] `client-key-data`
- [ ] kubeconfig 원문
- [ ] Secret Data
- [ ] ServiceAccount Token
- [ ] Join Credential 원문
- [ ] 인증서 Private Key

기록할 수 있는 것:

- Secret 이름·Type·Key 이름
- 존재 여부
- Masking된 상태
- 발급·확인 시각
- 승인된 보관·전달 체계
- 사용 성공·폐기·Rotation 필요 여부

## 23. 문제 판단 공통 순서

강사는 구축·운영·장애 모두에서 같은 사고 순서를 사용한다.

```text
대상과 문제 고정
→ 확인된 사실
→ 정상과 차이
→ 선후·변경·반응
→ 정보가 현재 대상의 것인지 검증
→ 결과에 따라 행동이 달라지는 다음 확인 하나
→ 승인된 조치 또는 담당 영역 에스컬레이션
→ 같은 정상 경로로 재검증
```

- [ ] 원인 이름을 먼저 맞히게 하지 않는다.
- [ ] 읽기 전용 확인을 먼저 고르게 한다.
- [ ] 변경 후 반응을 강한 증거로 사용한다.
- [ ] 현재 대상이 아닌 과거 로그를 사실로 사용하지 않는다.
- [ ] 다른 담당 영역이면 필요한 증거를 정리해서 넘긴다.

---

# Part 4. 교육생 Teach-back 평가

## 24. 교육생이 독립적으로 해야 할 것

### 구조

- [ ] Host·Member·Harbor·Storage·Monitoring 관계를 설명한다.
- [ ] VIP-A·VIP-B 경로를 설명한다.
- [ ] Workspace·Project·Role·Quota 관계를 설명한다.

### 정상 경로

- [ ] Harbor Image→Secret→Deployment→Pod를 설명한다.
- [ ] StorageClass→PVC→PV→Mount→Write/Read를 설명한다.
- [ ] Service→Endpoint→Ingress→VIP-B→HTTP를 설명한다.

### 운영

- [ ] 요청에 맞는 Manual을 찾는다.
- [ ] 실제값과 예시값을 구분한다.
- [ ] 권한·Quota·Storage·Network 문제를 섞지 않는다.

### 장애

- [ ] 증상 원문을 먼저 본다.
- [ ] 정상과 처음 달라진 지점을 찾는다.
- [ ] 다음 행동을 가르는 확인을 고른다.
- [ ] 승인 없는 재설치·삭제·권한 확대를 하지 않는다.

### 구축

- [ ] 5.0→5.5.2 선후를 설명한다.
- [ ] 각 단계의 완료 증거를 말한다.
- [ ] 기존 Host는 Join 대상임을 설명한다.

## 25. 평가 판정

### PASS

- 구조·대상·Manual·검증·경계를 연결할 수 있다.
- 실제값은 문서·화면에서 찾는다.
- 다음 확인과 담당 영역을 선택할 수 있다.

### PARTIAL

- 큰 구조는 맞지만 특정 Manual·증거·경계가 약하다.
- 약한 부분을 특정해서 보충할 수 있다.

### RETEACH

- Host·Member·Project·VIP·권한·Storage 경계를 반복적으로 잘못 구분한다.
- 정상 상태를 한 개의 `Running`·`Bound`로 과잉 판정한다.
- 위험 변경을 첫 행동으로 선택한다.

### BLOCKED

- 계정·자료·통역·환경 접근이 없어 평가 자체가 불가능하다.
- 이해 부족으로 오해하지 않고 환경 제약으로 기록한다.

---

# Part 5. 현장 기록과 인수

## 26. 현장 변경·확인사항

- [ ] [[현장 변경 및 확인사항|현장 변경 및 확인사항]]에 일정·범위·실제값·접근·결정 변경을 기록한다.
- [ ] 사실과 해석을 구분한다.
- [ ] 결정자·담당자·영향 날짜를 기록한다.
- [ ] 미확정 항목에는 다음 확인을 붙인다.
- [ ] 임시 대응이 영구 기준으로 오해되지 않게 표시한다.

## 27. 일별 증적

### 8/24

- 출입·교육장·통역·참석자·자료·접근 상태

### 8/25

- 교육 완료·질문·Teach-back·자료 배포 상태

### 8/26~28

- Manual별 진행 결과·시연·질문·환경 제약·Teach-back

### 8/31

- VM·Bastion·Node·Inventory·Ansible

### 9/1

- Playbook·API·Node·System Pod·CNI·DNS·ETCD·Runtime

### 9/2

- Snapshotter·Trident·Backend·StorageClass·PVC·Mount·Write/Read·정리

### 9/3

- Monitoring·ETCD Target·Grafana·KubeSphere·Join·Multi-Cluster·회귀

### 9/4

- 문서·증적·잔여 항목·Credential·접근·장비·출입 정리

## 28. 잔여 항목 분류

- [ ] Blocking
- [ ] Non-blocking
- [ ] External Dependency
- [ ] Observation

모든 잔여 항목에:

- 현재 통과 지점
- 최초 실패·미확인 지점
- 영향
- 재개조건
- 다음 확인
- 담당자
- 필요한 승인
- 증적 위치

를 기록한다.

## 29. 9/3 최종 기술 판정

- [ ] PASS
- [ ] PARTIAL
- [ ] BLOCKED

판정은 [[출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수|9/3 최종 인수 문서]]의 기능별 인수 매트릭스를 따른다.

## 30. 9/4 현장 종료 판정

- [ ] CLOSED
- [ ] CLOSED WITH FOLLOW-UP
- [ ] NOT READY TO CLOSE

종료 판정은 기술 성공 여부 하나만 보지 않고 문서·인수·보안·장비·출입·후속 담당까지 확인한다.

---

# Part 6. 출발 전 최종 체크

## 31. 문서

- [ ] 출장 홈 최신
- [ ] 일정표 최신
- [ ] 8/25 최종본·중국어본·배포본 최신
- [ ] 8/26 기술 전수 문서 최신
- [ ] 8/27 기술 전수 문서 최신
- [ ] 8/28 기술 전수 문서 최신
- [ ] 8/31 구축 문서 최신
- [ ] 9/1 구축 문서 최신
- [ ] 9/2 구축 문서 최신
- [ ] 9/3 구축·인수 문서 최신
- [ ] 9/4 철수 문서 최신
- [ ] 현장 변경·확인사항 준비
- [ ] 이전본이 분리되어 있음

## 32. 자료·번역

- [ ] 8/25 한국어 최종본
- [ ] 8/25 중국어 최종본
- [ ] 8/25 배포용 한국어
- [ ] 8/25 배포용 중국어
- [ ] 8/25 강사 대본
- [ ] 8/25 강사 메모
- [ ] 1.x CN/EN 위치 확인
- [ ] 2.x CN/EN 위치 확인
- [ ] 3.x CN/EN 위치 확인
- [ ] 4.1~4.3 CN/EN 위치 확인
- [ ] 4.4 CN/EN 존재 여부 확인
- [ ] 5.x CN/EN 위치 확인

## 33. 현장 운영

- [ ] 출입·Laptop 반입 규칙
- [ ] 교육장·화면·전원
- [ ] Network
- [ ] 통역
- [ ] 참석자
- [ ] 담당자 연락 경로
- [ ] Offline 자료
- [ ] Masking 방법
- [ ] 질문 기록 양식

## 34. 구축 외부 의존성

- [ ] 신규 Member VM 배정표
- [ ] VIP-A·VIP-B
- [ ] Pod·Service CIDR
- [ ] Domain·DNS
- [ ] Bastion
- [ ] Repository
- [ ] Kubespray Bundle
- [ ] Registry·Image
- [ ] Storage SVM·Data LIF·Export policy
- [ ] Host↔Member Join Network
- [ ] 승인자·작업 역할

## 35. 보안

- [ ] 교육자료에 Password 없음
- [ ] Token 없음
- [ ] kubeconfig 원문 없음
- [ ] Secret Data 없음
- [ ] Private Key 없음
- [ ] 임시 Credential 관리 계획 있음
- [ ] 9/4 회수·정리 계획 있음

---

# Part 7. 강사 최종 질문

## 36. 전체 구조

1. 이번 출장의 신규 구축 대상과 기존 완료 대상은 각각 무엇인가?
2. 왜 운영 Manual 교육을 실제 구축보다 먼저 하는가?
3. 8/31~9/3의 Member 구축은 무엇부터 무엇까지인가?
4. 9/3에 Host Join까지 포함해야 하는 이유는 무엇인가?
5. 9/4를 기술 Buffer로 쓰지 않는 이유는 무엇인가?

## 37. 운영

1. 사용자의 DKS 신청은 어떤 객체와 권한으로 변환되는가?
2. KubeSphere Project와 Harbor Project는 무엇이 다른가?
3. `project-operator`와 `project-admin`은 왜 구분하는가?
4. kubectl 접근은 KubeSphere UI 권한과 어떤 점에서 다른가?
5. CA ConfigMap이 필요한 증상과 완료 증거는 무엇인가?

## 38. 구축

1. VM을 받았다고 Kubespray를 바로 실행하면 안 되는 이유는?
2. Inventory Parse 성공과 실제 설계 일치는 왜 다른가?
3. Node Ready 이후 무엇을 더 확인해야 하는가?
4. PVC Bound 이후 어떤 증거가 더 필요한가?
5. Member Monitoring의 External ETCD Target `UP`은 왜 중요한가?
6. Host Join 전 Member 자체 Gate는 무엇인가?

## 39. 장애 판단

1. Harbor x509와 unauthorized는 어떻게 다른가?
2. Dashboard Token을 교체할 때 왜 기존 Secret을 먼저 지우지 않는가?
3. PVC Bound + FailedMount에서 좋은 다음 확인은 무엇인가?
4. Project가 안 보일 때 왜 바로 권한을 올리지 않는가?
5. ImagePullBackOff에서 왜 Event가 시작점인가?
6. Host Console에 Member 이름이 보인다는 것만으로 Join 완료라고 할 수 없는 이유는?

## 40. 인수·철수

1. PASS와 PARTIAL의 차이는 무엇인가?
2. Blocker를 9/4에 강행하지 않고 인계하려면 무엇을 기록해야 하는가?
3. 어떤 보호된 값이 현장 Laptop·Bastion·문서에 남지 않아야 하는가?
4. 현지 담당자가 어떤 문서를 직접 찾을 수 있어야 하는가?
5. CLOSED WITH FOLLOW-UP은 어떤 상태인가?

---

## 41. 강사 최종 준비 완료 기준

- [ ] 최신 일정을 문서 없이 설명한다.
- [ ] 8/25~8/28 교육 범위를 정확히 구분한다.
- [ ] 최종 배포 Manual 1.1~6.5의 위치를 찾는다.
- [ ] 5.0~5.5.2 중 5.5.1이 이번 수행 범위 제외임을 설명한다.
- [ ] 8/31~9/3 신규 Member 구축의 Gate를 설명한다.
- [ ] 기존 Host는 재설치하지 않고 Join 대상으로만 사용한다.
- [ ] 각 단계의 성공 증거와 과잉 판정 위험을 설명한다.
- [ ] 실제값·예시값·이전본을 구분한다.
- [ ] Secret·Token·Password·Private Key를 노출하지 않는다.
- [ ] 교육생 Teach-back을 PASS·PARTIAL·RETEACH·BLOCKED로 판정할 수 있다.
- [ ] 현장 변경과 잔여 항목을 증거·담당자·다음 확인으로 기록한다.
- [ ] 9/3 PASS·PARTIAL·BLOCKED 기술 판정을 할 수 있다.
- [ ] 9/4에 기술 작업을 추가하지 않고 인수·정리·철수한다.
- [ ] 현지 담당자가 출장 홈과 원문 Manual을 직접 찾을 수 있게 인계한다.
- [ ] CLOSED / CLOSED WITH FOLLOW-UP / NOT READY TO CLOSE를 근거로 판정한다.
