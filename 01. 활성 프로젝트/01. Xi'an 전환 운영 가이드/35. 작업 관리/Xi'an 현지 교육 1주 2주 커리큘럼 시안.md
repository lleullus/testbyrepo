---
title: "Xi'an 현지 교육 1주·2주 커리큘럼 시안"
status: draft
doc_type: plan
scope: "현재 Xi'an 가이드와 Taylor 교육 이력을 기반으로 한 현지 교육 기간별 시안"
updated: "2026-08-06"
parent: "[[Xi'an 현지 교육 준비 계획|Xi'an 현지 교육 준비 계획]]"
---

# Xi'an 현지 교육 1주·2주 커리큘럼 시안

## 1. 목적

현재 준비된 Xi'an 구축·운영 가이드와 [[Taylor 4주 교육 수행 분석|Taylor 4주 교육 수행 분석]]을 기준으로, 현지 교육 기간이 1주 또는 2주일 때 사용할 수 있는 커리큘럼 시안을 제시한다.

두 안은 같은 교육을 빠르게 또는 느리게 진행하는 관계가 아니다.

- **1주안**은 핵심 구조, 반복 운영과 안전한 초동 판단을 인계하는 집중 과정이다.
- **2주안**은 첫 주에 플랫폼 구축과 검증 기반을 만들고, 둘째 주에 교육생 주도 관리·운영과 축소 Shadowing으로 독립성을 확인하는 과정이다.

> [!important] 시안의 시간 가정
> 두 안 모두 기술 교육 전에 별도 환경 준비일 `P0` 최소 1일을 둔다. 따라서 1주안은 `P0 1일 + 기술 교육 5일` 총 6일, 2주안은 `P0 1일 + 기술 교육 10일` 총 11일이며, 기술 교육은 하루 6시간을 기준으로 작성했다. 실제 날짜, 교육 일수, 일별 시간과 통역 참여 여부는 아직 미확정이므로 확정 후 시간표를 다시 조정해야 한다.

## 2. 설계 원칙

### 2.1 세 축을 모두 연결한다

```text
구축축: VM·LB·Bastion → Kubernetes → Storage → Host·Member
관리축: 신청 → Workspace·Project → Role → Quota → kubectl 접근
운영축: Harbor Image·PVC → Deployment·Pod → Service·Endpoint → Ingress·VIP-B → User
```

구축축이 애플리케이션 실행 기반을 만들고, 관리축이 사람의 권한과 자원 경계를 만들며, 운영축이 그 경계 안에서 실제 사용자 응답을 만든다는 하나의 이야기로 설명한다.

### 2.2 모든 교육에 같은 판단 순서를 적용한다

```text
대상 Cluster·context·Namespace 확인
→ 정상 경로와 기대 결과 확인
→ 증거로 확인된 첫 단절 식별
→ 읽기 전용 반증 확인
→ 승인된 조치 또는 담당 영역으로 에스컬레이션
```

### 2.3 현재 자료가 지원하는 깊이까지만 가르친다

| 깊이 | 교육 대상 | 기본 방식 |
|---|---|---|
| 반드시 체화 | Xi'an 구조, Host·Member, VIP-A/B, 정상 애플리케이션 경로, 상태와 실제 성공의 차이 | 설명, 구조도, 교육생 재설명 |
| 조건부 직접 실습 | Workspace·Project·Role·Quota, Harbor Project·User, 샘플 Workload, 기본 상태 확인 | 격리 환경·계정·승인·정리 절차 확보 시에만 실습 |
| 문서 기반 워크스루 | Step 0~5 전체 설치, Worker 작업, taint·label, Native API, 인증서 갱신, 복구 | Runbook, 마스킹 출력, 탁상훈련 |
| 실제 실행 금지 | 전체 재설치, 장애 생성, 임의 RBAC·Network·Storage 변경, Namespace 삭제 | 사례 설명과 작업 경계 확인 |

## 3. 1주 과정 시안

### 3.1 과정 목표

전체 설치를 직접 반복하는 대신, 교육생이 다음을 수행할 수 있게 한다.

1. Xi'an DKS 전체를 구축·관리·운영 세 축으로 설명한다.
2. 설치 Step 0~5의 선후관계와 완료·중단 기준을 판정한다.
3. 반복적인 사용자·권한·Quota·Harbor 운영을 문서에 따라 수행하거나 결과를 확인한다.
4. 하나의 애플리케이션을 Image와 PVC에서 사용자 HTTP 응답까지 추적한다.
5. 장애에서 첫 단절을 찾고 위험한 변경 전에 중단·에스컬레이션한다.

### 3.2 일자별 커리큘럼

| 일자 | 목표 | 주요 주제 | 교육 방식 | 산출물·완료 기준 |
|---|---|---|---|---|
| Day 1<br>Xi'an DKS 전체 구조 | 세 축과 작업 대상을 구분한다. | Host·PRD Member·DEV Member·Harbor 역할, VM·LB·Bastion·Storage·Monitoring 책임 경계, VIP-A/API와 VIP-B/Ingress, 신청→권한→Quota, Image/PVC와 사용자 요청 경로 | 설명, 구조도 워크스루, 조회 화면 시연, 교육생 재설명 | 10분 안에 세 축을 설명한다. Host·Member, VIP-A·B, Project·Namespace를 혼동하지 않는다. 대상과 미확정 값을 구분한 구조도 1장을 작성한다. |
| Day 2<br>구축과 검증 | 설치 명령보다 Step 0~5의 선후관계와 검증 기준을 이해한다. | VM·LB 확인, Bastion·Node Pre-Setting, Inventory, Kubespray, API·Node·System Pod 검증, StorageClass·PVC·Mount, Host·Member 설치 순서, Monitoring과 Host Join | 설명, [[30. 구축 및 전환/구축 마스터 Runbook|Runbook]] 워크스루, 마스킹 출력 시연, 단계 판정 실습 | 단계별 `목적·진입조건·변경 대상·성공 증거·중단조건` 카드를 작성한다. `Ready` 하나로 완료를 선언하지 않고 Storage·Monitoring·Join까지 검증 범위를 설명한다. |
| Day 3<br>사용자와 자원 관리 | 신청을 권한과 자원 경계로 변환하는 표준 절차를 익힌다. | Workspace·Project, Member 초대, Project Role과 RBAC, CPU·Memory·Storage Quota, kubectl 접근 경계, Harbor Private Project와 사용자 역할 | 설명, 화면 시연, 조건부 실습, 권한 사례 워크스루 | 신청 사례 1건을 Workspace·Project·Role·Quota·Harbor 설정 체크리스트로 변환한다. 조건 충족 시 생성·검증·정리하고, 미충족 시 화면 증적으로 설정과 완료 상태를 판정한다. |
| Day 4<br>애플리케이션 정상 경로 | 배포부터 사용자 응답까지의 모든 연결을 확인한다. | Harbor Image·Image Secret, Deployment·Pod, PVC `Bound`와 Mount, Service·Endpoint, Ingress·VIP-B, HTTP 응답, Prometheus·Grafana 기본 상태 | 설명, 시연, 조회 전용 실습, 정상 경로 워크스루 | 정상 경로 지도와 증적표를 작성한다. `Pod Running ≠ HTTP 성공`, `PVC Bound ≠ Mount 성공`을 설명하고 각 연결의 확인 근거를 제시한다. 조건 충족 시 샘플 Workload를 배포·검증·정리한다. |
| Day 5<br>통합 인수와 초동 판단 | 세 축을 연결하고 독립 판단 가능성을 확인한다. | 설치 결과 인수, 사용자 온보딩, 정상 경로, Daily Monitoring, 사용자 요청, NFS Mount·Monitoring 오적용·Host UI 504 사례 중 2~3건 | 통합 워크스루, 탁상훈련, teach-back, 질의응답 | `대상→정상 경로→첫 단절→읽기 전용 증적→변경·에스컬레이션 경계`로 사례를 판정한다. 15분 teach-back, 질문·미확정 목록과 인수 체크리스트를 제출한다. |

### 3.3 1주안의 Taylor 과정 축약

| Taylor 4주 요소 | 1주안 처리 |
|---|---|
| 별도 VM Full Installation | 전체 재설치 대신 Step 0~5 증적 기반 워크스루와 완료 상태 판정으로 대체한다. 격리 환경이 있어도 안전한 부분 실습만 수행한다. |
| 설치 오류 대응과 대기 | 사전 준비한 정상·실패 출력으로 진입조건, 첫 실패 지점과 중단조건을 판정한다. |
| Week 4 Shadowing | Day 1~4 말미의 일일 teach-back과 Day 5 통합 탁상훈련으로 대체한다. |
| 독립 운영 확인 | 장기 관찰 대신 문서 탐색, 조회 증적 수집, 첫 단절 판단과 위험 작업 중단 능력으로 판정한다. |

### 3.4 1주안의 한계

- 교육생이 별도 환경에서 DKS 전체를 직접 설치하는 경험은 제공하지 않는다.
- 반복 수행을 장기간 관찰하는 Shadowing이 없으므로 실제 독립 운영 능력을 완전히 검증할 수 없다.
- 따라서 1주안의 완료는 **핵심 운영 인수와 안전한 초동 판단 교육 완료**를 의미하며, 전체 구축 수행 자격을 증명하지 않는다.

## 4. 2주 과정 시안

### 4.1 과정 목표

첫째 주에는 구축 결과를 읽고 검증하는 기반을 만들고, 둘째 주에는 교육생이 관리·운영 시나리오를 주도하도록 한다.

```text
Week 1: 강사 설명·시연 중심 → 구축 인수 teach-back
Week 2: 교육생 주도 수행 → 정상 운영·장애 판단 → 통합 인수 평가
```

### 4.2 Week 1 - 플랫폼 기반과 구축 인수

| 일자 | 목표 | 주요 주제 | 교육 방식 | 산출물·완료 기준 |
|---|---|---|---|---|
| Day 1<br>구조와 수준 정렬 | 세 축의 시작점과 끝점을 공통 언어로 정리한다. | Host·PRD/DEV Member·Harbor, Bastion·LB·Storage·Monitoring, VIP-A/B, 신청·권한·Quota, 정상 애플리케이션 경로 | 설명, 구조도 워크스루, 조회 시연, 기초 수준 확인 | 세 축 구조도와 용어 혼동 목록을 작성한다. 교육생이 각 축의 시작점과 끝점을 설명한다. |
| Day 2<br>설치 전 조건과 Inventory | 선행조건과 Inventory가 설치 결과에 미치는 영향을 이해한다. | Step 0, VM hostname·IP, ETCD 파일시스템, VIP-A/B 라우팅, Bastion 권한, Node Pre-Setting, 노드 역할·IP·CIDR | 설명, 문서 워크스루, 마스킹 출력, 판정 실습 | 사전조건 체크리스트와 Inventory 검토표를 작성한다. Xi'an 실제값, Taylor 예시와 미확정 값을 출처별로 구분한다. |
| Day 3<br>Kubernetes와 Storage 검증 | 설치 결과를 연결된 증적으로 판정한다. | Kubespray 흐름, API 연결, Node·System Pod, Storage Backend·StorageClass, Test PVC, Pod Mount, ONTAP/NFS 경계 | 설명, 실행 로그 워크스루, 조회 실습, 증적 판정 | Node Ready, System Pod, API, PVC Bound와 Pod Mount를 분리한 설치 검증표를 완성하고 첫 실패 지점을 지목한다. |
| Day 4<br>Host·Member와 Monitoring | 역할별 설치 순서와 차이를 설명한다. | Host KubeSphere·Monitoring·RBAC·`cluster-configure`, Member 선행 컴포넌트·CRD·Prometheus·Ingress·ETCD Monitoring·Grafana·KubeSphere·Host Join | 설명, 구성 시연, Runbook 워크스루, 순서 배열 실습 | Host·Member 비교표와 역할별 완료 증거를 작성한다. Host 설정을 Member에 복사하면 안 되는 이유와 Member의 Monitoring 선행 순서를 설명한다. |
| Day 5<br>구축 인수 Teach-back | 전체 구축을 인수 관점에서 연결하고 중단 기준을 적용한다. | Step 0~5 전체, 공통·역할별 검증, 실제값 확인, 현재 상태와 과거 사례 구분 | 교육생 주도 워크스루, 검증 실습, teach-back | 교육생이 20분 동안 Step 0~5를 설명하고 단계별 성공 증거와 중단조건을 제시한다. 전체 설치 실행 없이 구축 인수 체크리스트를 완성한다. |

### 4.3 Week 2 - 관리·운영 주도 수행과 인수 확인

| 일자 | 목표 | 주요 주제 | 교육 방식 | 산출물·완료 기준 |
|---|---|---|---|---|
| Day 6<br>사용자 온보딩 | 교육생이 권한과 자원 설정을 주도한다. | 신청, Workspace·Project, Workspace Member, Project Role, RBAC, CPU·Memory·Storage Quota, kubectl 접근 경계 | 짧은 설명, 교육생 주도 시연·조건부 실습, 역할 사례 | 신청 사례 2건을 PRD/DEV, Role과 Quota로 변환한다. 조건 충족 시 생성·검증·정리하고 미충족 시 화면 증적을 판정한다. |
| Day 7<br>Harbor와 Image 공급 | Harbor에서 Workload까지의 공급 경로를 연결한다. | Private Project, ProjectAdmin·Developer, Image Tag·Push·Pull, Image Secret, CA 신뢰 오류와 인증 오류 | 설명, 시연, 조건부 실습, teach-back | Harbor 권한표와 Image→Deployment 증적을 작성한다. 조건 충족 시 Project·User와 샘플 Image 사용 후 정리 결과를 확인한다. |
| Day 8<br>정상 운영 주도 수행 | 정상 애플리케이션 경로와 일상 점검을 직접 수행한다. | Deployment·Pod, PVC·Mount, Service·Endpoint, Ingress·VIP-B·HTTP, Cluster 상태, Prometheus·Grafana, 사용자 요청 | 교육생 주도 조회 실습, 관찰·교정 | 정상 경로 증적표와 Daily Monitoring 기록을 작성한다. 3분 안에 대상과 첫 확인 지점을 제시하고 최종 HTTP 응답까지 판정한다. |
| Day 9<br>장애 초동 판단 | 여러 축에 걸친 장애에서 첫 단절과 협업 경계를 판단한다. | Host UI 504, NFS PVC Mount, Monitoring 복붙 오적용, Dashboard Namespace 삭제 사례 중 3~4건 | 탁상훈련, 역할 분담, 증적 워크스루, teach-back | 사례별 `증상·확인 사실·첫 단절/분기·다음 조회·금지 변경·에스컬레이션`을 작성한다. 근거 없는 재설치·재부팅·정책 변경을 제안하지 않는다. |
| Day 10<br>통합 인수 평가 | 교육생 주도로 전체 시나리오를 완주한다. | 구축 결과 검증, 사용자 온보딩, Harbor·Workload·Ingress, Monitoring, 사용자 요청, 승인·중단·복구 경계 | 교육생 주도 통합 수행, teach-back, 탁상훈련, 최종 Q&A | 팀별 20~30분 teach-back, 통합 체크리스트와 미확정·에스컬레이션 목록을 제출한다. 문서를 찾아 증거로 판단하고 실제값을 추측하지 않으며 위험 작업에서 멈추면 완료다. |

### 4.4 2주안의 Taylor 과정 축약

| Taylor 4주 요소 | 2주안 처리 |
|---|---|
| 별도 VM Full Installation | Week 1에 설치 전 조건, Kubespray 로그, Storage, Host·Member·Monitoring·Join을 단계별로 분석하고 Day 5에 교육생이 전체 구축 인수 워크스루를 주도한다. |
| 별도 환경 전체 설치 반복 | 기본 과정에는 넣지 않는다. 격리 환경, 설치파일, 복구 가능 시간과 승인자가 확보된 경우에만 별도 선택 과정으로 분리한다. |
| Week 4 Shadowing | Day 8 정상 경로·Daily Monitoring, Day 9 사례 대응, Day 10 통합 업무를 교육생이 주도하는 3일 축소 Shadowing으로 대체한다. |
| 독립 운영 확인 | Day 5 구축 teach-back, Day 8 정상 운영, Day 9 장애 판단과 Day 10 통합 평가의 누적 결과로 판정한다. |

## 5. 두 시안 비교

| 비교 항목 | 1주안 | 2주안 |
|---|---|---|
| 핵심 목적 | 핵심 운영 인수와 안전한 초동 판단 | 구축 인수와 교육생 주도 운영 독립성 확인 |
| 교육 주도권 | 강사 설명·시연 중심, 마지막 날 통합 확인 | Week 1 강사 중심, Week 2 교육생 중심 |
| 구축 교육 | Step 0~5 집중 워크스루 1일 | 사전조건, Kubernetes·Storage, Host·Member를 4일에 걸쳐 학습하고 인수 teach-back |
| 관리·운영 실습 | 핵심 절차를 각 1일에 압축 | 사용자 온보딩, Harbor, 정상 운영을 역할별로 분리해 반복 |
| 장애 사례 | 2~3건 통합 탁상훈련 | 3~4건 역할 분담 탁상훈련 |
| Shadowing 대체 | 일일 teach-back과 마지막 날 통합 평가 | 마지막 3일 교육생 주도 축소 Shadowing |
| 완료 의미 | 핵심 내용을 이해하고 안전하게 초동 대응 가능 | 문서를 이용한 반복 관리·운영과 인수 판단을 주도 가능 |
| 공통 제외 | 전체 재설치, 장애 생성, 고위험 운영 변경의 실제 실행 | 전체 재설치, 장애 생성, 고위험 운영 변경의 실제 실행 |

## 6. 현재 자료 지원 범위

| 구분 | 현재 자료로 지원되는 내용 | 교육 전 확정할 내용 |
|---|---|---|
| 교육 목적 | 설치와 운영을 포함한 종합 인수인계, 기존 설치·운영 가이드 전달 | 공식 교육 완료 기준과 제출 형식 |
| 구축축 | Step 0~5, VM·LB·Bastion·Node, Kubespray, Storage, Host·Member, Monitoring, Host Join과 검증 기준 | 전체 설치용 별도 VM, 설치파일 접근, 실행·복구 시간 |
| 관리축 | Workspace·Project·Member·Role·RBAC·Quota, kubectl, Harbor Project·User | 실습 계정과 권한, AD·CyberArk·방화벽 조건, 승인자 |
| 운영축 | Harbor→Workload, PVC·Mount, Service·Endpoint, Ingress·VIP-B·HTTP, Monitoring, 장애 초동 판단 | 샘플 애플리케이션, 실습 Namespace, 정리 절차와 허용 변경 범위 |
| 교육생 | 현지 인프라 담당자를 대상으로 한다는 가정 | 인원, Kubernetes 경험, 역할, CLI 숙련도 |
| 언어 | 한국어 진행과 통역 참여 가능성을 고려한 준비 문서 | 통역 참여, 용어 사전 공유와 기술 통역 수준 |
| 시스템 상태 | 사용자 확인 기준으로 현재 운영상 문제 없음 | 교육 직전 실제 상태와 조회 증적 |
| 추적 사례 | NFS, 504, Monitoring, Dashboard 사건 기록을 사례로 활용 가능 | [[60. 이슈 및 결정/열린 항목|열린 항목]]의 `review`가 현재도 유효한지는 재확인 필요하며 기록만으로 현재 장애라고 단정하지 않음 |

## 7. 공통 안전 기준

- 운영 Cluster에서는 기본적으로 조회만 수행한다.
- 대상 Cluster, context, Namespace와 실제 환경값을 먼저 확인한다.
- Secret, Token, 개인키와 kubeconfig 원문을 화면·자료·로그에 남기지 않는다.
- `apply`, `delete`, `patch`, `taint`, `scale`, 재시작, 인증서 갱신, Worker 변경과 전체 Playbook 실행은 현장 실습의 기본 범위에서 제외한다.
- 위험 작업은 `목적→선행조건→영향→백업→실행 순서→성공 기준→중단 기준→복구·에스컬레이션` 순서의 워크스루 또는 탁상훈련으로 다룬다.
- 교육 완료는 명령어 암기가 아니라 문서를 찾아 대상을 확인하고, 증적으로 상태를 판정하며, 위험 작업에서 중단·에스컬레이션할 수 있는지로 평가한다.

## 8. 시안 확정 전 결정 사항

1. 실제 교육 기간, 날짜와 일별 교육시간
2. 교육생 인원, Kubernetes 경험과 담당 역할
3. 통역 참여와 통역을 포함한 실제 진행 가능 시간
4. 실습용 Cluster·Namespace·계정·권한·네트워크 접근
5. 변경 승인자, 허용 작업과 실습 후 정리 절차
6. 사용할 샘플 애플리케이션과 정상 증적
7. 최종 교육 완료 기준과 제출할 산출물
8. 2주안 선택 시 전체 설치 Hands-on을 별도 선택 과정으로 추가할지 여부

## 9. 상세 커리큘럼

- [[Xi'an 현지 교육 1주 상세 커리큘럼|1주 상세 커리큘럼]]
- [[Xi'an 현지 교육 2주 상세 커리큘럼|2주 상세 커리큘럼]]

## 관련 문서

- [[Xi'an 현지 교육 준비 기준|Xi'an 현지 교육 준비 기준]]
- [[Xi'an 현지 교육 준비 계획|Xi'an 현지 교육 준비 계획]]
- [[Taylor 4주 교육 수행 분석|Taylor 4주 교육 수행 분석]]
- [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
- [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
- [[50. 운영/01. Operations Overview/운영 안내|운영 안내]]
- [[60. 이슈 및 결정/열린 항목|열린 항목]]
