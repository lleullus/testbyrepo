---
title: "2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증"
status: current
doc_type: build-note
scope: "2026-09-02 신규 Member Cluster Storage Component 구성, Test PVC·Pod Mount·Write/Read 검증 및 9/3 Member 설치 선행조건 확정"
created: "2026-08-15"
updated: "2026-08-28"
parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거]]"
---

# 2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증

> [!important] 이 문서의 역할
> 이 문서는 9/2 신규 Member Storage 구축의 **현장 수행·판정 Source of Truth**이다. Snapshotter·Trident·Backend·StorageClass의 실제 구성과 Test PVC·Pod Mount·Write/Read·Cleanup의 정확한 수행 기준을 보존한다. 강의의 설명 순서와 Teach-back은 아래 강사용 대본을 사용하며, 상세 Manifest·명령·환경값은 이 문서와 원본 Storage Runbook을 따른다.

### 9/2 강사용 대본

- [[출장/20. 교육/2026-09-02/오전/01. Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본|오전 - Storage 공급 경로]]
- [[출장/20. 교육/2026-09-02/오후/01. PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본|오후 - Storage 실제 사용·9/3 Gate]]

> [!success] 9/2 종료 Gate
> 9/3 Monitoring으로 넘어가는 판정은 `STORAGE PASS / BLOCKED`를 사용한다. `PVC Bound`만으로 통과시키지 않고 실제 Pod Mount·Write/Read·Cleanup까지 닫는다.

> [!success] 현재 일정의 경계
> 기존 Xi'an Host Cluster는 이미 구축 완료되어 있으며 9/2에 Host KubeSphere를 새로 설치하지 않는다. 이 문서에 남아 있는 Host installer·`cluster-configure` 설명은 **Storage가 KubeSphere와 Monitoring에 어떻게 의존되는지 이해하고, 다음날 Member 구성을 준비하기 위한 비교·배경 지식**이다. 실제 9/2 변경 범위는 신규 Member Cluster의 Storage Component 구성과 사용 검증까지다.

## 1. 9/2 확정 범위

- External Snapshotter CRD·Controller 설치와 상태 확인
- NetApp Trident Operator·Controller·Node 구성요소 설치와 상태 확인
- Trident Backend 생성·연결 및 `online` 상태 확인
- 승인된 StorageClass 생성·기본값·reclaim policy·provisioner 확인
- Test PVC 생성과 PVC/PV 동적 Provisioning 검증
- Test Pod의 Node 배치, CSI Attach·Mount, NFS 경로와 Event 확인
- Container 내부 Mount·Write·Read·재읽기 검증
- 테스트 산출물과 임시 리소스 정리 기준 확인
- 9/3 Member Monitoring·KubeSphere가 사용할 StorageClass와 PVC 선행조건 확인
- 핵심 구간은 교육생이 직접 조회·설명·실습하고, 환경 의존 변경은 강사와 현지 담당자가 공동 확인

이날 가장 중요한 문장은 다음이다.

> **StorageClass가 보이고 PVC가 Bound여도 Storage 교육은 끝난 것이 아니다. Pod가 실제로 Mount하고 Write/Read까지 되어야 한다.**

## 2. 머릿속에 있어야 할 전체 흐름

```text
9/1 Kubernetes 기반 정상
→ External Snapshotter CRD·Controller
→ Trident Operator / Controller / Node CSI
→ Trident Backend 연결 및 online 확인
→ 승인된 StorageClass 생성·속성 확인
→ PVC 동적 Provisioning
→ PV·VolumeHandle·NFS export 경로 확인
→ Test Pod Scheduling
→ Node에서 실제 NFS Mount
→ Container Write / Read / 재읽기
→ 테스트 리소스와 증적 정리
→ 9/3 Member Monitoring PVC 선행조건 확인
→ Member KubeSphere 설치·기존 Host Join 준비
```

### 서로 다른 성공 단계

```text
StorageClass 존재
≠ Backend 정상

PVC Bound
≠ Pod Mount

Pod Ready
≠ Volume 실제 Write/Read 확인

Test PVC·Mount·Write/Read 성공
≠ 9/3 Member Monitoring·KubeSphere·Host Join 완료
```

## 3. Storage 구성요소 관계를 설명하기

근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Kubernetes 스토리지 컴포넌트 구축 및 설치 검증]]

### External Snapshotter

- CSI Snapshot API/Controller 선행 구성
- Snapshot CRD와 Controller가 준비됨
- Trident와 동일한 것은 아님

### NetApp Trident

- Kubernetes CSI와 NetApp Storage를 연결
- Operator / Controller / Node 구성요소
- Backend를 통해 SVM·Data LIF·Storage 정책과 연결

### Backend

- Kubernetes 바깥의 실제 NetApp Storage 정보를 Trident와 연결
- `online` 여부가 중요
- management LIF·Data LIF·SVM·export policy 등은 실제 환경값 확인 필요

### StorageClass

- 사용자가 PVC에서 선택할 Storage 공급 정책
- Xi'an의 현재 기준은 `scs-netapp-qtree-nfs-sc-delete`
- provisioner는 Trident CSI와 연결

### PVC / PV / Pod

```text
PVC
→ StorageClass 요청
→ Trident가 volume provision
→ PV 연결
→ kubelet/CSI가 Node에 Mount
→ Container가 filesystem 사용
```

이 연결을 그림 없이 설명할 수 있어야 한다.

## 4. `Bound`와 `Mount`를 분리해서 이해하기

9/2와 9/3 모두에서 반복해서 사용할 핵심이다.

```text
PVC Bound
→ Kubernetes/CSI가 volume을 할당하는 단계까지 성공

Pod Mount 성공
→ 해당 Node에서 실제 NFS export를 붙이는 단계까지 성공

Write/Read 성공
→ Container에서 실제 filesystem을 사용할 수 있음
```

따라서 `Bound` 후 `ContainerCreating + FailedMount`는 모순이 아니다.

관련 사례:
[[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우]]

## 5. Kubernetes와 ONTAP의 책임 경계를 이해하기

Storage 문제를 모두 Kubernetes 문제로 보거나 모두 Storage 문제로 넘기지 않는다.

### Kubernetes/Trident 측에서 볼 수 있는 것

- StorageClass
- PVC/PV
- CSI driver
- Trident backend state
- Pod Event
- kubelet Mount 오류
- Node가 선택한 NFS source path

### Storage/Network 측과 연결되는 것

- Data LIF
- Node Source IP
- Route
- TCP 2049
- Export policy
- 실제 NFS export path

문제가 생기면 “Trident 문제”라고 바로 부르지 않고 **Provisioning이 실패한 것인지 Mount가 실패한 것인지 먼저 구분**한다.

## 6. 9/3 Member 구성과 연결되는 Storage 의존성

근거:
- [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
- [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]

9/2의 Storage 검증은 독립된 기능 점검으로 끝나지 않는다. 다음날 구성할 Member Monitoring과 KubeSphere가 PVC를 실제로 사용할 수 있어야 하므로, **테스트 PVC 한 건의 성공을 다음 구성요소의 선행조건으로 해석하는 연결**이 필요하다.

```text
StorageClass 사용 가능
→ Monitoring PVC 동적 Provisioning 가능
→ Prometheus·Grafana Pod가 Volume Mount 가능
→ Member Monitoring 데이터 보존 가능
→ Member KubeSphere 설치의 Storage 의존성 충족
→ 기존 Host Join 전 Member 자체 상태 검증 가능
```

### 9/3 전에 확정할 Storage 항목

- Member Monitoring이 사용할 StorageClass 이름
- StorageClass의 provisioner, reclaim policy, volumeBindingMode
- Trident Backend `online` 상태와 실제 SVM·Data LIF 연결
- Router·Infra·Worker를 포함한 대상 Node에서 NFS Data LIF 접근 가능 여부
- Test PVC가 생성한 PV의 VolumeHandle과 실제 export path
- Pod가 스케줄된 Node와 Mount source의 일치 여부
- Container에서 Write한 데이터가 재읽기되는지
- 테스트 리소스 삭제 시 PV와 Backend Volume의 정리 동작
- 9/3에 사용할 PVC 용량과 Namespace
- 실패 시 9/3 작업을 시작하지 않을 중단 기준

### 기존 Host KubeSphere 문서를 남겨 두는 이유

기존 Xi'an Host Cluster는 이미 구축 완료되어 있고 이번 출장에서는 재설치하지 않는다. 다만 Host의 KubeSphere·Monitoring도 StorageClass, Registry, External ETCD, Node 배치 정책에 의존하므로 다음 두 파일의 역할을 **비교 지식**으로 이해할 필요가 있다.

#### `kubesphere-installer.yaml`

- KubeSphere installer 실행을 위한 CRD·RBAC·Deployment 생성
- installer Pod의 Image와 Registry 의존성
- Infra Node 배치 정책
- 설치 실행기 자체의 기동 조건

#### `cluster-configure.yaml`

- KubeSphere 기능과 환경 설정
- StorageClass와 Monitoring Storage
- Registry와 External ETCD
- Console·Ingress
- Multi-Cluster Role
- 기능 Module별 구성

> `kubesphere-installer.yaml`은 설치 실행기를 올리고, `cluster-configure.yaml`은 그 실행기가 어떤 KubeSphere 구성을 만들지 정의한다. 이번 9/2에는 이 두 파일을 Host에 적용하지 않고, **Storage가 다음날 Member 설치와 Monitoring에 어떻게 연결되는지 설명하는 비교 근거**로만 사용한다.

## 7. Storage 검증 증적을 단계별로 남기는 법

한 장의 `kubectl get pvc` 출력으로 완료를 선언하지 않는다. 각 단계에서 서로 다른 질문에 답하는 증적을 남긴다.

| 단계 | 핵심 질문 | 최소 증적 | 실패 시 첫 분기 |
|---|---|---|---|
| Snapshotter | Snapshot API·Controller가 준비됐는가? | CRD와 Controller 상태 | CRD 누락 / Controller 비정상 |
| Trident | CSI Controller·Node가 준비됐는가? | Trident Pod·DaemonSet 상태 | 특정 Node 누락 / Image·권한 오류 |
| Backend | NetApp 연결이 성립했는가? | `tridentctl get backend`의 `online` | SVM·LIF·Credential·Network |
| StorageClass | 승인된 정책이 노출됐는가? | YAML의 provisioner·parameter·reclaim policy | 오타 / 잘못된 Backend·정책 |
| Provisioning | PVC 요청이 PV로 연결됐는가? | PVC·PV·Event·VolumeHandle | Pending / Provisioner Event |
| Mount | 선택된 Node가 NFS export를 붙였는가? | Pod Event·Mount source·Node | Route·2049·Export policy |
| 사용 | Container가 실제 파일시스템을 쓰는가? | `df`, write, read, 재읽기 | 권한·filesystem·mount option |
| 정리 | 테스트 자원이 기대대로 정리되는가? | PVC/PV/Backend Volume 상태 | reclaim policy·잔여 Volume |

### 증적 기록 양식

```text
Cluster/context: ______________________________
Namespace: ___________________________________
StorageClass: _________________________________
Backend/state: ________________________________
PVC/PV: ______________________________________
Pod/Node: ____________________________________
NFS source/export path: _______________________
Write test: __________________________________
Read-back test: _______________________________
Cleanup result: ______________________________
첫 실패 단계 또는 미확인 단계: ________________
다음 읽기 전용 확인: __________________________
```

실제 IP, SVM, Credential, Secret 원문은 교육 문서에 복사하지 않는다. 필요한 경우 화면을 마스킹하고, 값 자체보다 **어느 단계가 어떤 근거로 통과했는지**를 남긴다.

## 8. 9/3 진행 여부를 가르는 Gate

다음 항목이 모두 충족되어야 Member Monitoring·KubeSphere 단계로 이동한다.

1. Kubernetes API·Node·CNI·DNS 기본 검증이 9/1 기준으로 통과했다.
2. Snapshotter와 Trident의 필수 구성요소가 대상 Node 전체에서 정상이다.
3. Backend가 `online`이며 승인된 SVM·Data LIF를 참조한다.
4. StorageClass가 승인된 값과 일치하고 잘못된 예시값을 사용하지 않는다.
5. Test PVC가 Bound되고 대응 PV·VolumeHandle을 확인했다.
6. Test Pod가 실제 Node에 배치되어 NFS Volume을 Mount했다.
7. Container에서 Write와 Read-back을 성공했다.
8. 테스트 리소스 정리 동작과 잔여 Volume 여부를 확인했다.
9. Monitoring에서 사용할 StorageClass·Namespace·용량을 확정했다.
10. 9/3 Monitoring의 실제 Storage 사용을 막는 미해결 Storage 오류가 없다. 비차단 기록 항목이 남으면 영향·담당자·기한을 별도로 기록하되 `STORAGE PASS` 자체를 흐리지 않는다.

### 중단 기준

- Backend가 `offline`이거나 실제 연결 대상이 미확정
- StorageClass가 과거 Cluster의 값인지 현재 신규 Member 값인지 구분되지 않음
- PVC가 Pending 상태로 원인이 해소되지 않음
- PVC는 Bound지만 Pod가 `FailedMount`에서 멈춤
- Mount는 됐지만 Write/Read 검증 실패
- Node별 NFS 접근 조건이 서로 달라 특정 역할 Node에서만 실패
- 테스트 정리 과정에서 의도하지 않은 PV·Backend Volume 삭제 위험이 확인됨

이 경우 9/3 KubeSphere 설치를 강행하지 않는다. 먼저 실패 단계를 확정하고, Kubernetes·Network·ONTAP 중 어느 담당 영역의 확인이 필요한지 분리한다.

### 다음날 installer 로그와 연결되는 판단

9/3에는 다음 두 실패를 구분해야 한다.

```text
Monitoring PVC 자체가 Pending 또는 FailedMount인가?
vs
Storage는 정상인데 installer 내부 monitoring task가 실패하는가?
```

첫 번째는 9/2 Storage Gate의 미통과 가능성이 높고, 두 번째는 CRD·설치 순서·설정값·Image·권한 같은 KubeSphere 설치 영역을 확인해야 한다. Pod가 `Running`이라는 한 상태만으로 어느 쪽도 성공이라고 판정하지 않는다.

## 9. 숙지 수준 분류

### A. 문서 없이 바로 설명할 것

- [ ] Snapshotter·Trident·Backend·StorageClass·PVC·PV의 관계
- [ ] `PVC Bound ≠ Pod Mount ≠ Write/Read`인 이유
- [ ] Provisioning 실패와 Node Mount 실패의 조사 시작점 차이
- [ ] NFS Mount에서 Kubernetes·Network·ONTAP의 책임 경계
- [ ] Backend `online`이 의미하는 범위와 의미하지 않는 범위
- [ ] StorageClass의 provisioner·reclaim policy·volumeBindingMode가 영향을 주는 지점
- [ ] 9/2 Storage 검증이 9/3 Monitoring·KubeSphere의 선행조건인 이유
- [ ] 기존 Host를 재설치하지 않지만 Host 문서를 비교 지식으로 남기는 이유
- [ ] Monitoring PVC 문제와 installer task 문제를 구분하는 기준
- [ ] 테스트 리소스 정리 결과까지 확인해야 하는 이유

### B. 문서를 보며 수행·설명할 것

- [ ] Snapshot CRD·Controller 확인
- [ ] Trident Operator·Controller·Node Pod 확인
- [ ] `tridentctl` Backend 조회와 상태 해석
- [ ] StorageClass YAML의 핵심값 확인
- [ ] Test PVC·PV·Event·VolumeHandle 확인
- [ ] Test Pod의 Node·Event·Mount source 확인
- [ ] Container 내부 `df`·mount·Write·Read·재읽기 확인
- [ ] Node에서 Data LIF Route와 TCP 2049 확인 위치 찾기
- [ ] Export policy 확인 요청에 필요한 Source IP와 export path 정리
- [ ] 테스트 PVC 삭제 후 PV·Backend Volume 정리 상태 확인
- [ ] 9/3 Member Monitoring PVC의 StorageClass·용량·Namespace 확인
- [ ] 기존 Host installer·cluster-configure에서 Storage 의존값을 비교해 찾기

### C. 실제 환경에서 확인할 것

- 실제 Backend name·state·SVM·Data LIF
- 실제 StorageClass 이름과 승인 근거
- 실제 PV·VolumeHandle·NFS export path
- 실제 Test Pod 이름·Node·Mount source
- 역할별 Node의 Data LIF 접근 차이
- 실제 Write 내용과 Read-back 결과
- 테스트 리소스 정리 결과와 잔여 Volume
- 9/3 Monitoring용 StorageClass·PVC 용량·Namespace
- Storage 미해결 항목의 담당자·영향·다음 조치
- Secret·Credential 원문을 노출하지 않은 증적 기록 방식

## 10. 내가 지금 부족한 곳을 찾는 자가점검

| 질문 | 현재 상태 | 막히는 부분 | 학습 문서 |
|---|---|---|---|
| Snapshotter와 Trident의 차이를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Storage]] |
| Trident Backend가 무엇이며 `online`은 어디까지 증명하는가? | 미평가 |  | 4. Storage |
| PVC→PV→CSI→Node Mount→Write/Read 흐름을 그릴 수 있는가? | 미평가 |  | 4. Storage |
| `Bound`인데 Mount가 실패할 수 있는 이유를 설명할 수 있는가? | 미평가 |  | Storage 트러블슈팅 |
| Node→Data LIF 경로와 Export policy가 왜 함께 중요한지 설명할 수 있는가? | 미평가 |  | Storage 트러블슈팅 |
| StorageClass의 provisioner·reclaim policy·volumeBindingMode를 읽을 수 있는가? | 미평가 |  | 4. Storage |
| Test Pod의 Event에서 Provisioning과 Mount 실패를 구분할 수 있는가? | 미평가 |  | 4. Storage |
| Write/Read 검증과 테스트 리소스 정리 결과를 기록할 수 있는가? | 미평가 |  | 4. Storage |
| 9/3 Monitoring PVC가 사용할 StorageClass·용량·Namespace를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2 Member]] |
| Monitoring PVC 실패와 installer task 실패를 구분할 기준이 있는가? | 미평가 |  | 5-2 Member |
| 기존 Host 문서가 이번 9/2 실제 수행 범위가 아니라 비교 근거라는 점을 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-1|5-1 Host]] |

## 11. 읽을 문서와 목적

1. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Kubernetes 스토리지 컴포넌트 구축 및 설치 검증]]
   - Snapshotter→Trident→Backend→StorageClass→PVC→Mount→Write/Read의 전체 선후관계와 실제 명령·검증 기준
2. [[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|NFS PVC Mount 실패]]
   - Provisioning 성공과 Node Mount 실패를 분리하고, Data LIF·Source IP·Route·TCP 2049·Export policy로 확장하는 실제 사례
3. [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
   - StorageClass 존재가 아니라 Test PVC·Pod Mount·Write/Read까지 완료 증적으로 보는 기준
4. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
   - 9/3 Monitoring PVC·Member KubeSphere·기존 Host Join에 필요한 Storage 의존성
5. [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
   - Member Monitoring 선행 구성과 KubeSphere 설치 순서
6. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-1|5-1. KubeSphere Host 클러스터 설치 및 운영 구성]]
   - 기존 Host가 이미 구축되어 있다는 전제에서 installer·cluster-configure·Storage 의존성을 비교하는 참고
7. [[30. 구축 및 전환/Host 클러스터/05.1.1 Apply kubesphere-installer|KubeSphere Installer 적용]]
   - 실행기와 배치·Registry 의존성을 비교할 때만 사용하며 이번 9/2 적용 대상은 아님
8. [[30. 구축 및 전환/Host 클러스터/05.1.2 Apply cluster-configure|Host cluster-configure 적용]]
   - KubeSphere가 StorageClass·Monitoring Storage를 소비하는 구조를 확인하는 비교 자료

## 12. 반드시 답할 수 있어야 할 질문

1. 왜 External Snapshotter CRD·Controller를 Trident와 분리해 확인하는가?
2. Trident Backend와 StorageClass는 어떤 관계이고, `online`은 어디까지 증명하는가?
3. PVC가 Bound라는 것은 정확히 어느 단계까지 성공했다는 뜻인가?
4. Pod Mount는 어떤 Event·Node·NFS source 증적으로 확인하는가?
5. Container Write·Read·재읽기 검증은 왜 별도로 필요한가?
6. NFS Mount 실패 시 Node Route·TCP 2049·Export policy·Source IP는 어떻게 연결되는가?
7. StorageClass의 provisioner·reclaim policy·volumeBindingMode는 각각 어떤 동작에 영향을 주는가?
8. 테스트 PVC 삭제 후 PV와 Backend Volume 정리를 왜 확인해야 하는가?
9. 9/3 Monitoring PVC가 Storage Gate를 통과했다고 판단하려면 무엇이 필요한가?
10. Monitoring PVC가 Pending인 상황과 installer 내부 monitoring task가 실패한 상황은 어떻게 구분하는가?
11. 기존 Host installer 문서가 이번 9/2 실제 적용 대상이 아닌데도 참고하는 이유는 무엇인가?
12. 어떤 Storage 실패가 남아 있으면 9/3 Member KubeSphere 작업을 중단해야 하는가?

## 13. 직접 연습할 것

### 연습 1 — Storage 전체 흐름 5분 설명

```text
Snapshotter
→ Trident
→ Backend
→ StorageClass
→ PVC
→ PV
→ Pod Mount
→ Write/Read
```

각 화살표에서 “무엇이 다음 단계의 조건인가?”를 말한다.

### 연습 2 — 정상 출력과 실패 출력 구분

다음 세 장면을 비교해서 현재 실패 위치를 말한다.

```text
A. PVC Pending
B. PVC Bound + Pod ContainerCreating + FailedMount
C. PVC Bound + Pod Running + df/write/read 성공
```

### 연습 3 — Storage 증적표 완성

정상 또는 실패 출력 한 세트를 사용해 다음 표를 실제 값으로 채운다. Secret·Credential 원문은 쓰지 않는다.

```text
Backend / state:
StorageClass / provisioner / reclaim policy:
PVC / phase / Event:
PV / VolumeHandle:
Pod / Node:
NFS source / export path:
Mount 확인:
Write / Read-back:
Cleanup 결과:
첫 실패 단계:
다음 읽기 전용 확인:
```

출력에 없는 값은 추측하지 않고 `미확인`으로 둔다. 한 단계의 성공으로 뒤 단계를 자동 통과시키지 않는다.

### 연습 4 — 9/3 Member 선행조건 점검

`05-2.md`와 Member 클러스터 개요에서 다음 항목을 찾고, 각각 9/2 Storage 결과와 어떻게 연결되는지 한 문장씩 설명한다.

```text
Monitoring StorageClass
Prometheus PVC
Grafana PVC 또는 datasource 의존성
Infra nodeSelector / taint·toleration
Member clusterRole
Registry
External ETCD Monitoring 대상
기존 Host Join 전 Member 정상 조건
```

### 연습 5 — 기존 Host 문서를 비교 근거로 읽기

`05-1.md`에서 다음 값을 찾되, **9/2에 Host에 적용하지 않는다.** 같은 항목이 Member 구성에서는 어떤 값과 역할로 나타나는지 비교한다.

```text
StorageClass
local_registry
External ETCD
multicluster.clusterRole
infra nodeSelector
```

### 연습 6 — 실행기와 구성의 역할 설명

문서를 닫고 90초 안에 다음 관계를 설명한다. 목적은 Host 설치 실행이 아니라 다음날 Member installer 로그를 읽을 준비다.

```text
kubesphere-installer.yaml
vs
cluster-configure.yaml
vs
Monitoring PVC의 Storage 선행조건
```

## 14. 정상 상태를 내가 설명할 수 있는가

### Storage

```text
Trident 구성요소 정상
→ backend online
→ StorageClass 정상
→ PVC Bound
→ PV/CSI 연결 확인
→ Pod Ready
→ 실제 Mount
→ Write/Read
```

### 9/3 Member 구성 진입 준비

```text
Storage Gate 통과
→ Monitoring에서 사용할 StorageClass·PVC 조건 확정
→ Member installer·cluster-configure의 Storage/Registry/ETCD/Role 값 사전 대조
→ 기존 Host는 재설치하지 않고 접근·Join 대상만 확인
→ 9/3 Member Monitoring·KubeSphere 설치와 Host Join을 시작할 수 있음
```

### 완료를 선언하지 않는 상태

```text
PVC Bound만 확인
또는
한 Node에서만 Mount 성공
또는
Write/Read 없이 Pod Running만 확인
또는
테스트 정리 결과 미확인
=
Storage 완료 아님, 9/3 진행 Gate 미통과
```

## 15. 문제 상황 사고 연습

### 사례 1 — PVC Bound, Pod Mount 실패

```text
확인된 사실
→ Provisioning은 통과했다.
차이
→ Pod가 Node에서 NFS를 Mount하지 못한다.
다음 분기
→ Pod Event의 NFS path와 해당 Node의 Data LIF route/TCP 2049를 본다.
```

### 사례 2 — Backend offline

```text
Pod 문제로 바로 가지 않는다.
→ Backend 자체 연결이 성립하지 않았으므로 Storage 연결 정보를 먼저 확인한다.
```

### 사례 3 — Test Storage는 정상인데 9/3 Monitoring PVC가 Pending

```text
9/2 Test PVC 성공을 자동으로 모든 Monitoring PVC 성공으로 확대하지 않는다.
→ Monitoring PVC가 같은 StorageClass를 사용하는가?
→ 요청 용량과 Namespace Quota가 맞는가?
→ volumeBindingMode와 실제 Pod Scheduling 조건은 무엇인가?
→ 해당 Infra Node에서 Data LIF 접근이 되는가?
→ PVC Event의 최초 실패 원문은 무엇인가?
```

Test PVC와 Monitoring PVC는 같은 Storage 기반을 사용하더라도 요청 용량·Namespace·Node 배치·Quota가 다를 수 있다. 9/3에는 Storage 자체 실패와 KubeSphere installer 내부 task 실패를 먼저 분리한다.

## 16. 예상 질문

| 예상 질문 | 핵심 답변 방향 | 현재 답변 가능 여부 |
|---|---|---|
| PVC가 Bound면 왜 Pod가 못 뜰 수 있나요? | Provisioning과 Node Mount 단계 분리 | 미평가 |
| Trident는 StorageClass인가요? | CSI/Backend와 정책 객체의 역할 구분 | 미평가 |
| Backend가 online이면 Storage는 끝난 건가요? | Backend 연결과 PVC·Node Mount·Write/Read는 별도 | 미평가 |
| Test PVC가 성공하면 Monitoring PVC도 무조건 되나요? | Namespace·Quota·용량·Node 배치 조건을 별도 검증 | 미평가 |
| 왜 테스트 리소스 삭제 결과까지 보나요? | reclaim policy와 잔여 Volume 동작도 운영 기준 | 미평가 |
| 9/3 installer의 monitoring task가 실패하면 Storage를 다시 설치해야 하나요? | Monitoring PVC 상태와 CRD·Endpoint·installer task를 먼저 분리 | 미평가 |
| 기존 Host KubeSphere 문서는 왜 읽나요? | 이번 적용 대상이 아니라 Storage 의존성을 비교하는 배경 근거 | 미평가 |

## 17. 학습 기록

### 새로 이해한 것
-

### 설명하다 막힌 것
-

### 직접 해봐야 할 것
-

### 9/3에 이어서 볼 Member Monitoring·KubeSphere 영역
-

### Storage Gate에서 아직 미확정인 실제값
-

### 9/3 시작 전에 담당자 확인이 필요한 항목
-

## 18. 9/2 준비 완료 기준

- [ ] Storage 전체 흐름을 문서 없이 설명할 수 있다.
- [ ] `PVC Bound ≠ Mount ≠ Write/Read`를 명확히 설명할 수 있다.
- [ ] Kubernetes·Network·ONTAP의 책임 경계를 나눌 수 있다.
- [ ] Snapshotter·Trident Backend·StorageClass·PVC·PV의 관계를 설명할 수 있다.
- [ ] Backend `online`이 PVC·Mount·Write/Read 전체 성공을 뜻하지 않는다고 설명할 수 있다.
- [ ] StorageClass의 provisioner·reclaim policy·volumeBindingMode를 읽을 수 있다.
- [ ] Test PVC의 PV·VolumeHandle·Pod Node·NFS source를 증적으로 연결할 수 있다.
- [ ] Container Write·Read·재읽기와 테스트 리소스 정리 결과를 확인할 수 있다.
- [ ] 대표 Storage 실패에서 다음 판단을 가를 읽기 전용 확인 하나를 고를 수 있다.
- [ ] 9/3 Member Monitoring이 사용할 StorageClass·Namespace·용량을 확정할 수 있다.
- [ ] Monitoring PVC 실패와 KubeSphere installer 내부 monitoring task 실패를 구분할 수 있다.
- [ ] 기존 Host installer 문서는 비교 근거이며 9/2 실제 적용 대상이 아님을 설명할 수 있다.
- [ ] 9/3 Member Monitoring·KubeSphere·기존 Host Join으로 넘어갈 Storage Gate를 판정할 수 있다.
