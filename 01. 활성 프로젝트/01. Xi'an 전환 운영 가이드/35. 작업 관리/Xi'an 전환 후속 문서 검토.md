# [DKS-N] Xi'an 전환 후속 문서·설치파일·실사용 검토

작성자: 미기재  
마지막 업데이트: 2026-07-21  
읽기 시간: 8분

## 1. 개요

Xi'an 전환 운영 가이드에는 구축, 검증, 운영, 사용자 안내 문서가 이미 존재한다. 그러나 사용자가 제시한 `03. Cluster Setup`, `04. Kubesphere Operation`, `05. Operations Manual`, `06. Harbor Manual`, `07. DKS User Guide`의 전달 단위와 현재 Obsidian의 파일 위치가 일대일로 정리되어 있지는 않다.

이번 검토의 목적은 다음 네 가지 작업을 하나의 기준으로 연결하는 것이다.

1. 설치문서를 `03. Cluster Setup`의 실행 순서로 재정리한다.
2. KubeSphere·Operations·Harbor·DKS User Guide 문서를 영문화 관점에서 검수한다.
3. SCS 설치파일의 기준본·환경값·보안정보·적용 단계를 확인한다.
4. 문서와 설치파일을 실제 설치·운영·사용자 시나리오로 확인할 수 있는 기준을 만든다.

현재 Obsidian에는 독립 작업관리 영역이 없었으므로 `35. 작업 관리`를 별도 카테고리로 두고, 요약 상태는 [[35. 작업 관리/작업 목록|작업 목록]]에서, 상세 판단과 실행 기준은 이 문서에서 관리하는 방안이 적절하다. 원문 절차는 기존 `30. 구축 및 전환`과 `50. 운영`의 위치를 유지한다.

## 2. 확인사항

### 2.1 현재 문서 구조와 기준

| 구분 | Obsidian에서 확인된 내용 | 판단 근거 |
|---|---|---|
| 전체 허브 | [[00. 홈|Xi'an 전환 운영 가이드 홈]]이 기준·준비·구축·검증·운영·이슈를 연결함 | 새 작업관리 영역은 홈에서 접근 가능해야 함 |
| 구축 순서 | [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]이 초기 VM 설정부터 Host·Member 분기까지 연결함 | 설치문서 재정리의 기준 흐름으로 사용 가능함 |
| 구축 사전조건 | `20. 환경 준비`에 환경 의존성이 별도로 존재함 | 환경값과 선행조건을 설치 완료로 추정하면 안 됨 |
| Host·Member 분기 | 공통 구축과 Storage 구성 후 Host·Member 절차로 나뉨 | 두 클러스터 역할의 설치문서를 분리해서 검수해야 함 |
| 검증 기준 | [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]이 Kubespray, StorageClass·Test PVC, Host·Member 절차를 연결함 | 문서 존재가 아니라 검증 증적 연결 여부를 확인해야 함 |
| 운영 문서 | [[50. 운영/01. Operations Overview/운영 안내|운영 안내]] 아래에 04~07 매뉴얼이 존재함 | 영문화 대상의 현재 원문 위치로 사용함 |
| 미해결 항목 | [[60. 이슈 및 결정/열린 항목|열린 항목]]에 NFS, Host UI, Native API, Storage 의존성이 기록됨 | 문서 검수 중 발견한 이슈와 기존 운영 이슈를 분리해야 함 |
| 작업관리 | `35. 작업 관리/작업 목록.md`에 네 작업군과 상태가 정리됨 | 요약 상태와 상세 검토를 분리하는 구조가 가능함 |

#### 설치문서와 현재 원문 매핑

| 순서 | 요청된 설치문서 | 현재 Obsidian 원문 | 확인할 기준 |
|---:|---|---|---|
| 0 | `Initial VM setting` | [[업로드용/0. Initial VM setting]] 및 [[30. 구축 및 전환/구축 마스터 Runbook#0. 초기 VM 설정|구축 마스터 Runbook §0]] | VM hostname·IP, ETCD 파일시스템, Load Balancer VIP-A/B, Bastion 조건 |
| 1 | `SCS Bastion node pre-setting` | [[30. 구축 및 전환/공통 구축/01. Bastion Node Pre-setting]] | Bastion 디스크, 사용자·권한, 사전 소프트웨어, Kubespray 준비 |
| 2 | `SCS K8S Cluster nodes pre-settings` | [[30. 구축 및 전환/공통 구축/02. K8S Cluster Nodes Pre-setting]] | 노드 사전 설정의 실제 적용 범위, placeholder, 확인 필요 항목 |
| 3 | `SCS Deploy DKS Cluster using Kubespray` | [[30. 구축 및 전환/공통 구축/03. Deploy DKS Cluster]] | Inventory, 현장 설정값, Kubernetes 핵심 컴포넌트, API 연결 검증 |
| 4 | `SCS Install storage components` | [[30. 구축 및 전환/공통 구축/04. Install Storage Components]] | StorageClass·Test PVC와 NFS·ONTAP 의존성 |
| 5.1 | `Install kubesphere - host cluster` | [[30. 구축 및 전환/Host 클러스터/개요|Host 클러스터 개요]] 및 [[30. 구축 및 전환/Host 클러스터/05.1.1 Apply kubesphere-installer]] | Host KubeSphere, Host 전용 Monitoring, cluster-configure |
| 5.2 | `Install kubesphere - member cluster` | [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]] 및 [[30. 구축 및 전환/Member 클러스터/05.2.2 Install KubeSphere on Member Cluster]] | Member 선행 구성, KubeSphere 설치, Host join |

#### 매뉴얼 영문화 대상

| 분류 | 대상 문서 | 현재 원문 |
|---|---|---|
| `04. Kubesphere Operation` | `Creating Workspaces&projects` | [[50. 운영/04. Kubesphere Operation/01. Creating Workspaces&projects]] |
| `04. Kubesphere Operation` | `Inviting a new member` | [[50. 운영/04. Kubesphere Operation/02. Inviting a new member]] |
| `04. Kubesphere Operation` | `Assigning project roles to users` | [[50. 운영/04. Kubesphere Operation/03. Assigning project roles to users]] |
| `04. Kubesphere Operation` | `Setting quotas` | [[50. 운영/04. Kubesphere Operation/04. Setting quotas]] |
| `04. Kubesphere Operation` | `Kubesphere Role-Based Access Control` | [[50. 운영/04. Kubesphere Operation/05. Kubesphere Role-Based Access Control]] |
| `04. Kubesphere Operation` | `Enable users using kubectl CLI` | [[50. 운영/04. Kubesphere Operation/06. Enable users using kubectl CLI]] |
| `04. Kubesphere Operation` | `Kubesphere SECDS-ROOT.crt(CA.crt) ConfigMap Mount` | [[50. 운영/04. Kubesphere Operation/07. KubeSphere SECDS-ROOT.crt ConfigMap Mount]] |
| `05. Operations Manual` | `Adding a worker node to cluster using kubespray` | [[50. 운영/05. Operations Manual/01. Adding a worker node using kubespray]] |
| `05. Operations Manual` | `Add taint and node-label when adding node` | [[50. 운영/05. Operations Manual/02. Add taint and node-label when adding node]] |
| `05. Operations Manual` | `DKS FAQ` | [[50. 운영/05. Operations Manual/03. DKS FAQ]] |
| `05. Operations Manual` | `Failure response training` | [[50. 운영/05. Operations Manual/04. Failure response training]] |
| `05. Operations Manual` | `Utilizing the Kubernetes Native API` | [[50. 운영/05. Operations Manual/05. Utilizing the Kubernetes Native API]] |
| `05. Operations Manual` | `Renewing API Server Certificates` | [[50. 운영/05. Operations Manual/06. Renewing API Server Certificates]] |
| `06. Harbor Manual` | `Harbor Installation` | [[50. 운영/06. Harbor Manual/01. Harbor Installation]] |
| `06. Harbor Manual` | `Create a project` | [[50. 운영/06. Harbor Manual/02. Create a project]] |
| `06. Harbor Manual` | `Managing Users` | [[50. 운영/06. Harbor Manual/03. Managing Users]] |
| `07. DKS User Guide` | `DS Kubernetes Service Overview` | [[50. 운영/07. DKS User Guide/01. DS Kubernetes Service Overview]] |
| `07. DKS User Guide` | `Harbor user Guide` | [[50. 운영/07. DKS User Guide/02. Harbor User Guide]] |
| `07. DKS User Guide` | `KubeSphere User Guide` | [[50. 운영/07. DKS User Guide/03. KubeSphere User Guide]] |

파일명이 영문이라는 사실만으로 본문 영문화가 완료되었다고 판단할 수 없다. 본문 설명, 화면 경로, 제품명·컴포넌트명, Namespace·클러스터명, 명령어 전제조건을 문서별로 확인해야 한다.

### 2.2 제약사항과 영향 범위

| 항목 | 확인된 제약 | 영향 |
|---|---|---|
| SCS 설치파일 | 파일명·버전·수정일·실제 내용이 현재 Obsidian 자료에 없음 | 설치파일 검수와 기준본 확정을 완료할 수 없음 |
| 실제 사용 확인 | 대상자·수행 방식·테스트 환경·일정·승인자가 미기재 | 사용 가능 여부를 판단할 수 없음 |
| 환경값 | Xi'an의 최신 hostname, IP, 클러스터명, 경로, 버전이 이 작업목록에 모두 확정되어 있지 않음 | 문서의 placeholder와 실제값을 대조해야 함 |
| 복구 절차 | 문서 이동·설치파일 기준본 변경에 대한 구체적인 복구 절차가 원문에 없음 | 담당자 확인 전 대량 이동·삭제·덮어쓰기를 수행하면 안 됨 |
| 기존 이슈 | NFS PVC Mount, Host UI 504, Native API, Storage 의존성이 열린 항목에 존재함 | 문서 정리와 운영 문제 해결을 완료로 혼동하면 안 됨 |
| 보안정보 | 인증서·CA·Secret·토큰·비밀번호·개인키의 게시 가능 범위가 미기재 | 설치파일 확보 후 공유본 마스킹 검토가 필요함 |
| 서비스 영향 | 문서 검수 자체와 실제 클러스터 실행의 영향이 구분되어야 함 | 실제 실행은 별도 승인·영향도·중단 조건 확인이 필요함 |

`Failure response training`은 현재 `90. 참고 및 폐기/교육 및 훈련`에 있으므로 `05. Operations Manual` 최종 전달본에 포함할지는 별도 결정이 필요하다. 또한 사용자가 입력한 `Kubesphere`와 기존 문서의 `KubeSphere` 표기를 하나의 기준으로 통일해야 한다.

### 2.3 대안별 예상 결과

| 대안 | 구성 | 예상 결과 | 위험 또는 한계 |
|---|---|---|---|
| A. 기존 문서만 유지 | `60. 이슈 및 결정/열린 항목`과 마일스톤에 작업을 계속 추가 | 새 폴더를 만들지 않아 즉시 유지 가능 | 문서 정리·영문화·파일 검수·실사용 확인이 다시 분산됨 |
| B. `35. 작업 관리` 유지 | 요약 상태는 `작업 목록`, 상세 판단은 이 DKS-N 문서에서 관리하고 원문 위치는 유지 | 작업관리와 원문 절차가 분리되고, 기존 링크·역할 구조를 보존할 수 있음 | 기준본 확정 전에는 실제 문서 이동을 하지 않아야 함 |
| C. 설치·운영 원문을 `03~07` 폴더로 즉시 이동 | 사용자 전달 구조에 맞춰 모든 원문을 재배치 | 최종 전달본은 단순해질 수 있음 | 내부 링크 파손, 이전본·기준본 혼선, 원문 손실 위험이 있음 |

대안 B를 기본안으로 제안한다. 현재는 작업관리 카테고리와 원문 절차의 역할이 다르므로, 먼저 매핑·검수·기준본 확정을 완료하고 실제 이동은 별도 결정으로 남기는 것이 안전하다.

## 3. 조치방안

기존 `35. 작업 관리` 카테고리를 유지하고, `작업 목록`은 상태판으로 사용하며, 이 문서에서 설치문서·매뉴얼·설치파일·실사용 확인의 판단 기준과 다음 조치를 관리한다. SCS 파일과 실제 사용 결과가 확보되기 전에는 어떤 작업도 완료로 선언하지 않는다.

### 진행 절차

1. `00. 홈`, `30. 구축 및 전환/구축 마스터 Runbook`, `40. 검증 및 인수/구축 검증 기준`, `50. 운영/01. Operations Overview/운영 안내`, `60. 이슈 및 결정/열린 항목`을 기준 문서로 확정한다.
2. 사용자가 제시한 `03. Cluster Setup` 0~5.2 순서와 현재 Obsidian 원문을 매핑하고, 각 단계의 선행조건·입력값·완료조건·중단 조건·복구 기준을 기록한다.
3. `04. Kubesphere Operation`, `05. Operations Manual`, `06. Harbor Manual`, `07. DKS User Guide`의 모든 대상 문서를 본문·용어·화면 경로·명령어 전제조건 기준으로 검수한다.
4. SCS 설치파일을 확보한 뒤 파일 목록·버전·환경값·의존성·재실행성·민감정보·기준본 여부를 문서와 대조한다.
5. 설치 담당자·운영 담당자·사용자 중 실제 사용 확인 대상을 정하고, 전체 리허설·단계별 워크스루·실제 운영 시나리오 중 방식을 결정한다.
6. 신규 설치, 공통 구축, Storage, Host, Member, KubeSphere 운영, Harbor 운영, 기술 운영 시나리오를 확인하고 막힘·누락·오류·재현조건을 기록한다.
7. 결과를 `작업 목록`, `전환 현황 및 마일스톤`, `열린 항목`, `구축 검증 기준`에 반영하고, 실제 증적이 있는 항목만 완료로 갱신한다.

### `03. Cluster Setup` 설치문서 검수

| 단계 | 확인할 결과 | 완료 판단 |
|---|---|---|
| 0. Initial VM setting | VM hostname·IP, ETCD 파일시스템, Load Balancer VIP-A/B, Bastion 디스크·사용자 조건을 찾을 수 있음 | 다음 단계의 대상과 선행조건이 명확함 |
| 1. Bastion node pre-setting | Bastion 디스크·사용자·권한·사전 소프트웨어·Kubespray 준비가 연결됨 | Step 2에 필요한 입력과 확인 방법이 명확함 |
| 2. K8S Cluster nodes pre-settings | 실제 자동화 범위와 placeholder·확인 필요 항목이 구분됨 | 노드 사전 설정 완료를 추정하지 않음 |
| 3. Deploy DKS Cluster using Kubespray | Inventory·현장 설정값·Kubernetes 핵심 컴포넌트·API 연결 기준이 연결됨 | Kubespray 배포 검증 증적을 남길 수 있음 |
| 4. Install storage components | StorageClass·Test PVC와 NFS·ONTAP 의존성이 연결됨 | Storage 검증 기준과 열린 항목이 구분됨 |
| 5.1. Install KubeSphere - Host | Host 설치, Monitoring, `cluster-configure` 흐름이 연결됨 | Host 전용 완료조건이 Member와 섞이지 않음 |
| 5.2. Install KubeSphere - Member | Member 선행 구성, KubeSphere 설치, Host join 흐름이 연결됨 | Member 완료조건과 Host 연계가 확인됨 |

### 매뉴얼 영문화 검수

각 문서에 대해 다음 순서로 검수한다.

1. 제목과 파일 위치가 최종 전달 구조의 분류와 일치하는지 확인한다.
2. 본문 설명과 화면 메뉴가 영문 기준으로 일관되는지 확인한다.
3. 제품명, 컴포넌트명, Namespace, 클러스터명, 명령어를 임의로 번역하거나 변경하지 않았는지 확인한다.
4. 단계별 선행조건, 예상 결과, 실패 시 다음 조치가 있는지 확인한다.
5. 실제 사용 확인에서 이해하지 못한 표현과 누락된 화면 경로를 수정 후보로 기록한다.
6. 인증서·CA·Secret·토큰·비밀번호·개인키 값이 공유 문서와 게시본에 노출되지 않았는지 확인한다.

### SCS 설치파일 검수

| 검수 영역 | 확인 내용 | 결과 기록 |
|---|---|---|
| 파일 식별 | 파일명·경로·확장자·수정일·버전·디렉터리 구조 | SCS 파일 목록 필요 |
| 단계 매핑 | `03. Cluster Setup` 0~5.2 중 어느 단계에 적용되는지 | 단계별 매핑표 필요 |
| 환경값 | hostname·IP·클러스터명·Namespace·경로·StorageClass·레지스트리 | Xi'an 기준 대조 필요 |
| 플랫폼 버전 | Kubernetes·Kubespray·KubeSphere·Storage·Harbor 버전과 호환성 | 실제 버전 필요 |
| 실행 전제 | 권한·환경변수·선행 파일·외부 의존성 | 실행 전제조건 필요 |
| 재실행성 | 중복 생성·덮어쓰기·상태 불일치 가능성 | 재실행 검토 필요 |
| 보안정보 | 인증서·CA·Secret·토큰·비밀번호·개인키 포함 여부 | 게시 전 마스킹 필요 |
| 기준본 | 기준본·수정본·폐기본과 최종 전달 묶음 | 담당자 확정 필요 |

SCS 설치파일이 확보되기 전까지 설치파일 검수 상태는 `미착수`로 유지한다. 파일 본문이나 민감정보는 Blogger 게시본에 포함하지 않는다.

### 실제 사용 확인 시나리오

| 시나리오 | 확인 문서 | 확인할 질문 | 증적 |
|---|---|---|---|
| 신규 환경 준비 | `Initial VM setting`, 환경 준비 문서 | VM·LB·Bastion 선행조건을 담당자가 찾을 수 있는가? | 워크스루 또는 실행 기록 |
| 공통 클러스터 구축 | Bastion, K8S nodes, Kubespray 문서 | 순서·입력값·완료조건·다음 단계가 명확한가? | 단계별 확인표 |
| Storage 구성 | Storage 문서, 구축 검증 기준 | StorageClass·Test PVC와 NFS 의존성을 확인할 수 있는가? | 검증 증적 또는 이슈 |
| Host 구축 | Host 개요·KubeSphere 설치 문서 | Host Monitoring·`cluster-configure`까지 흐름이 이어지는가? | 시나리오 결과 |
| Member 구축 | Member 개요·KubeSphere 설치 문서 | Member 선행 구성·설치·Host join이 구분되는가? | 시나리오 결과 |
| KubeSphere 운영 | Workspace·Project·Member·Role·quota·CLI·ConfigMap 문서 | 구두 설명 없이 사용자·프로젝트 운영이 가능한가? | 화면 경로·결과 |
| Harbor 운영 | Harbor 설치·Project·Users·User Guide | 설치와 프로젝트·사용자 관리가 연결되는가? | 화면 경로·결과 |
| 기술 운영 | Worker·taint/label·Native API·Certificate·Failure response 문서 | 운영자가 변경·장애 대응 절차와 확인 방법을 찾는가? | 워크스루·이슈 |

### 완료 판단과 보류 기준

| 작업군 | 완료 기준 | 현재 판단 |
|---|---|---|
| 설치문서 재정리 | `03. Cluster Setup` 순서·원문·선행조건·완료조건·검증 링크가 확정됨 | 미착수 |
| 매뉴얼 영문화 | `04~07` 대상 문서별 본문·용어·화면 경로 검수가 끝남 | 미착수 |
| 설치파일 검수 | SCS 파일 기준본과 문서 단계 매핑이 확정됨 | 미착수 |
| 실제 사용 확인 | 참여자·방식·환경·결과·잔여 이슈가 기록됨 | 보류 |

다음 결정이 필요한 항목은 SCS 설치파일 목록 확보, `Failure response training`의 최종 분류, 실제 사용 확인 참여자·방식·일정, 문서 이동 여부다. 이 값이 확인되기 전에는 문서 구조를 대규모로 변경하거나 운영 환경에서 실행하지 않는다.
