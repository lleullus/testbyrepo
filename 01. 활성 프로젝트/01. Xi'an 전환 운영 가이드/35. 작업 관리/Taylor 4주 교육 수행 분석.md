---
title: "Taylor 4주 교육 수행 분석"
status: draft
doc_type: analysis
scope: "Taylor T-DKS 4주 Training Plan의 수행 내용과 진행 방식"
updated: "2026-08-06"
parent: "[[00. 홈|Xi'an 전환 운영 가이드]]"
---

# Taylor 4주 교육 수행 분석

## 1. 문서 목적

Taylor에서 진행했던 4주 T-DKS Training Plan을 기준으로, 당시 무엇을 교육했고 어떤 방식으로 기술 이전을 진행했는지 정리한다.

이 문서는 Xi'an 교육 일정을 바로 설계하기 위한 문서가 아니다. 먼저 Taylor의 기존 4주 과정을 사실 기준으로 복원하여, 이후 Xi'an에서 유지하거나 축약할 범위를 판단할 수 있게 하는 것이 목적이다.

> [!note] 근거 범위
> 이 분석은 사용자가 제공한 Taylor Training Plan의 일정, Task, Detailed Task, 참석자, 진행 상태와 Remarks의 질의사항을 바탕으로 작성했다. 세부 강의자료, 실제 작업 로그와 완료 증적은 별도로 확인하지 않았다.

## 2. 전체 진행 구조

Taylor의 4주 과정은 단순 강의가 아니라 다음 단계로 이어지는 기술 이전 프로젝트였다.

```text
환경 접근 준비
→ DKS 아키텍처와 설계 배경 이해
→ 강사 주도의 클러스터 구축
→ 별도 환경에서 전체 구축 Hands-on
→ 운영자·관리자·사용자 교육
→ 실제 운영 Shadowing
```

| 기간 | 단계 | 핵심 목적 | 진행 방식 |
|---|---|---|---|
| Week 1 | Pre-Setting 및 Architecture | 접근 환경 확보와 DKS 전체 구조 이해 | 환경 설정, 설명, 질의응답 |
| Week 2 | DKS Cluster Setup | 표준 클러스터 구축 절차 전수 | 단계별 구축 시연과 공동 수행 |
| Week 2~3 | T-DKS Hands-on | 교육생의 전체 설치 수행 능력 확인 | 별도 VM에서 직접 구축 및 검증 |
| Week 3 | DKS Operation | 플랫폼 운영, 권한 관리와 사용자 이용 방법 전수 | 운영 절차 시연, 실습, 사용자 교육 |
| Week 4 | Operation Shadowing | 실제 업무 적용과 독립 운영 가능 여부 확인 | Taylor 수행, Dell 관찰·지원 |

## 3. Week 1 - Pre-Setting과 DKS Architecture

### 3.1 환경 접근 준비

- T-PJT 환경에 접근할 PC를 설정했다.
- HQ 환경 접근에 필요한 방화벽을 개방했다.
- 이후 설치와 운영 교육에 필요한 기본 접근 경로를 먼저 확보했다.

이 단계는 기술 강의 이전의 선행 작업이었다. 환경 접근이 확보된 뒤 아키텍처 교육과 클러스터 구축으로 넘어갔다.

### 3.2 DKS 아키텍처 소개

다음 내용을 중심으로 DKS의 기술 기반과 설계 배경을 설명했다.

- DKS Hardware 구성
- DKS Software 구성
- Component와 VM의 구체적인 배치 관계
- DKS VM 용량 산정
- External Storage 설계 고려사항
- VM Template
- Kubespray와 Kubernetes 버전
- NetApp Trident
- 운영 관리 계획
- 가용성 보장 계획
- Multi-Cluster 관리
- Private Image Registry 관리

### 3.3 당시 확인한 주요 질문

- HQ는 사용자에게 자원을 어떻게 할당하는가?
- 왜 Physical Machine이 아니라 Virtual Machine을 사용하는가?
- HQ는 AD와 연계된 LDAP 및 Security Group을 어떻게 관리하는가?
- Kubernetes Upgrade 또는 Migration은 어떻게 수행하는가?
- 사용자는 HQ Harbor를 어떻게 사용하는가?
- 사용자는 KubeSphere 접근 권한을 어떻게 얻는가?
- Harbor를 이중화할 수 있는가?

### 3.4 진행 방식 분석

Week 1은 설치 명령을 배우는 시간이 아니라 DKS가 어떤 인프라와 운영 정책 위에 구성되는지를 이해하는 단계였다. 단순한 구성요소 정의보다 자원 할당, VM 채택 이유, 인증·권한, Storage, Registry, 가용성과 같은 설계 판단이 주요 질의로 다뤄졌다.

## 4. Week 2 - DKS Cluster Setup

### 4.1 클러스터 설치 전 준비

- Bastion Node Pre-Setting
- Cluster Node Pre-Setting
- Ansible Playbook 실행 환경 구성

설치 자동화를 실행하기 전에 Bastion과 대상 Node를 준비하고, Inventory와 Ansible 실행 기반을 구성했다.

### 4.2 Kubernetes 및 DKS 배포

- Kubespray 기반 DKS Cluster 배포
- Ansible Playbook 실행
- Post-Cluster 상태 검증
- Storage Component 설치

### 4.3 Host·Member와 Monitoring 구성

- Host Cluster에 KubeSphere 설치
- Grafana 및 PV Exporter 설치
- Prometheus Monitoring Stack 설치
- Member Cluster에 KubeSphere 설치
- Member Cluster를 Host Cluster에 Join

전체 설치 흐름은 다음과 같다.

```text
Bastion 준비
→ Cluster Node 준비
→ Ansible/Kubespray 실행 환경 구성
→ Kubernetes 배포
→ 배포 후 상태 검증
→ Storage 설치
→ Host KubeSphere 설치
→ Monitoring 구성
→ Member KubeSphere 설치
→ Host Join
```

### 4.4 당시 확인한 주요 질문

- Cluster Naming Convention에서 `PA01`은 무엇을 의미하는가?
- Kubernetes Cluster가 올바르게 설치됐는지 어떻게 확인하는가?
- 클러스터 설치를 완전히 자동화할 수 있는가?
- 사용자가 특정 Port 사용을 요청하면 어떻게 대응하는가?
- DKS에 Service Mesh를 추가할 계획이 있는가?
- 사용자가 PV Snapshot을 요청하면 어떻게 처리하는가?
- PV 생성에 제한이 있는가?
- DKS의 Monitoring 항목은 무엇인가?
- Alert 등급은 어떻게 구성되는가?

### 4.5 진행 방식 분석

Week 2는 Kubernetes 설치만 다룬 것이 아니다. Storage, Host·Member 역할, Monitoring과 Multi-Cluster Join까지 포함하여 DKS 플랫폼이 운영 가능한 상태가 되는 전체 구축 과정을 전수했다.

## 5. Week 2~3 - T-DKS Full Installation Hands-on

강사 주도의 구축 교육과 별도로 Taylor 담당자가 Test 환경에서 전체 설치를 직접 반복했다.

### 5.1 수행 내용

- T-DKS 설치용 신규 VM 요청
- DKS Cluster 설치를 위한 사전 설정
- Test 환경에서 Kubespray를 이용한 T-DKS 설치
- 설치 후 Cluster 상태 검증

### 5.2 진행 방식

```text
강사의 설명과 구축 시연
→ Taylor 담당자의 별도 VM 확보
→ 동일한 설치 절차 직접 수행
→ 설치 결과와 Cluster 상태 검증
```

이 Hands-on은 독립된 하루짜리 실습이 아니라 Week 2의 구축 교육과 Week 3의 운영 교육 사이에 병행된 장기 작업이었다. VM 준비, 설치 실행, 오류 대응과 검증에 필요한 대기 시간이 전체 일정에 포함됐다.

## 6. Week 3 - DKS Operation

Week 3에는 플랫폼 운영자, 서비스 관리 담당자와 최종 사용자를 위한 내용이 함께 포함됐다.

### 6.1 일상 운영과 상태 점검

- Daily Monitoring Task
- Cluster 상태 점검
- 사용자별 요구사항 대응

### 6.2 KubeSphere 운영과 권한 관리

- Workspace와 Project 생성
- 신규 Member 초대
- Project Role 할당
- KubeSphere와 CLI를 통한 Quota 설정
- 사용자의 kubectl CLI 접근 활성화

관리 흐름은 다음 순서로 교육했다.

```text
Workspace·Project 생성
→ 사용자 초대
→ Project Role 부여
→ Quota 설정
→ 필요 시 kubectl CLI 접근 제공
```

### 6.3 Harbor 운영

- Harbor 설치
- Harbor Project 생성
- Harbor 사용자 관리

### 6.4 Cluster 변경 작업

- Worker Node 추가
- Worker Node 제거
- Taint와 Toleration 설정

### 6.5 Taylor 및 SAS 사용자 교육

- DS Kubernetes Service 개요
- Harbor User Guide
- KubeSphere User Guide

### 6.6 당시 확인한 주요 질문

- Workspace와 Project를 한 번에 생성할 수 있는가?
- 관리자가 사용자 초대와 권한 설정 이력을 확인할 수 있는가?
- Workspace에만 Quota를 설정하고 Project에는 설정하지 않으면 어떻게 되는가?
- HQ DKS에 Critical Application이 실행되고 있는가?
- T-DKS가 `SG1599`와 다른 Security Group을 사용하면 문제가 있는가?
- 사용자는 kubectl을 어떻게 사용하는가?
- 배포한 Pod에서 외부 Database에 연결할 수 있는가?
- 사용자는 자신의 Storage를 어떻게 사용할 수 있는가?
- DKS에 Ingress Service가 있는가?

### 6.7 진행 방식 분석

Week 3의 `DKS Operation`은 하나의 역할만을 위한 교육이 아니었다.

- 플랫폼 운영자는 Monitoring, Cluster 상태와 Node 변경 작업을 배웠다.
- 서비스 관리 담당자는 Workspace, Project, Role과 Quota를 배웠다.
- 최종 사용자는 Harbor, KubeSphere와 kubectl을 이용하는 방법을 배웠다.

따라서 Week 3는 운영 절차뿐 아니라 사용자 권한 관리와 서비스 이용 교육까지 함께 인계한 단계였다.

## 7. Week 4 - T-DKS Operation Shadowing

### 7.1 수행 내용

- T-DKS Daily Monitoring
- KubeSphere 운영
- Cluster 상태 점검
- 사용자별 요구사항 대응

### 7.2 진행 방식

Week 4에는 새로운 설치 또는 운영 주제를 추가로 강의하기보다, Taylor 담당자가 실제 업무를 수행하고 Dell 담당자가 옆에서 관찰·지원하는 Shadowing을 진행했다.

```text
Taylor 담당자가 실제 운영 업무 수행
→ Dell 담당자가 수행 과정 관찰
→ 필요한 경우 질의응답과 교정
→ 독립 운영 가능 여부 확인
```

Training Plan에는 Week 3까지 모든 교육이 완료된 것으로 표시돼 있다. Week 4는 교육 내용을 추가하는 단계라기보다, 앞서 배운 내용을 실제 운영에 적용할 수 있는지 확인하는 인수 단계로 볼 수 있다.

## 8. Taylor에서 사용한 교육 방식

Taylor 과정에서는 하나의 교육 방식만 사용하지 않았다.

| 방식 | 적용 영역 | 목적 |
|---|---|---|
| 설명과 질의응답 | Architecture, 자원, AD, Storage, 가용성 | 구성과 설계 이유 이해 |
| 강사 시연 및 공동 수행 | Bastion, Kubespray, Storage, Host·Member, Monitoring | 표준 구축 절차 전달 |
| Full Installation Hands-on | 별도 T-DKS Test 환경 | 교육생의 전체 구축 수행 확인 |
| 운영 절차 실습 | KubeSphere, Harbor, Quota, kubectl, Node 작업 | 반복 운영 업무 전수 |
| 사용자 교육 | DKS Overview, Harbor, KubeSphere | 서비스 이용 방법 전달 |
| Shadowing | Daily Monitoring, Cluster 상태, 사용자 요청 | 실제 운영 적용과 독립성 확인 |

## 9. 4주가 사용된 이유

Taylor 일정에서 4주 전체가 강의로 채워진 것은 아니다.

1. Week 1에는 환경 접근 준비와 아키텍처 교육을 먼저 수행했다.
2. Week 2에는 Host·Member와 Monitoring을 포함한 전체 DKS 구축을 진행했다.
3. Week 2~3에는 별도 VM에서 Full Installation Hands-on을 병행했다.
4. Week 3에는 운영자 교육과 사용자 교육을 함께 진행했다.
5. Week 4에는 새로운 교육 대신 실제 운영 Shadowing을 수행했다.

따라서 긴 기간의 주요 원인은 전체 설치 내용을 설명하는 시간만이 아니었다. 별도 환경 준비, 전체 설치 반복, 설치 결과 검증, 역할별 운영 교육과 실제 운영 관찰까지 하나의 기술 이전 범위에 포함했기 때문이다.

## 10. 분석 결론

Taylor에서 수행한 일은 다음 네 덩어리로 요약된다.

1. DKS가 어떤 환경과 설계 판단 위에 구성됐는지 설명했다.
2. DKS Cluster의 전체 구축 절차를 시연하고 공동 수행했다.
3. Taylor 담당자가 별도 Test 환경에서 전체 구축을 직접 반복했다.
4. 운영·관리·사용자 교육 후 실제 운영을 Shadowing으로 확인했다.

명목상 4주 과정이지만 새로운 교육 내용은 주로 Week 1~3에 배치됐다. Week 4는 추가 강의보다 실제 운영 적용과 독립 운영 가능성 확인에 목적이 있었다. 또한 Week 2~3의 Full Installation Hands-on이 다른 교육과 병행됐기 때문에 전체 기간이 길어졌다.

이 구조는 이후 Xi'an 교육 기간을 정할 때 `설명`, `구축 시연`, `전체 설치 Hands-on`, `운영 실습`, `Shadowing`을 각각 유지할지 축약할지 판단하는 기준으로 사용할 수 있다.
