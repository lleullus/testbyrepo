---
title: "Xi'an 현지 교육 1주 상세 커리큘럼"
status: draft
doc_type: curriculum
scope: "CKA·CKS 보유 운영자를 위한 Xi'an DKS 6일 집중 인수 교육"
updated: "2026-08-06"
parent: "[[Xi'an 현지 교육 1주 2주 커리큘럼 시안|Xi'an 현지 교육 1주·2주 커리큘럼 시안]]"
---

# Xi'an 현지 교육 1주 상세 커리큘럼

## 1. 과정 정의

| 항목 | 내용 |
|---|---|
| 전체 기간 | **P0 환경 준비 1일 + 기술 교육 5일**, 총 6일 |
| 일일 시간 | 통역 포함 6시간, `09:00~16:00` |
| 수강생 | 2명. 주 수강생은 실제 운영자이며 CKA·CKS 보유. 보조 수강생은 증적 감사와 인시던트 기록 담당 |
| 과정 목표 | Xi'an 고유 구조와 실제 환경값을 기준으로 현재 구축 결과, 반복 운영, 정상 경로와 장애 초동 판단을 안전하게 수행한다. |
| 완료 의미 | 핵심 운영 인수와 안전한 초동 판단 교육 완료다. 전체 설치 수행 자격이나 장기 독립 운영을 보증하지 않는다. |

이 과정은 Kubernetes 개론이 아니다. Container, Pod, Deployment, Service, Endpoint, Ingress, PVC, RBAC의 일반 정의와 Kubespray 일반 설치 원리는 독립 강의로 편성하지 않는다. 아래 Xi'an 판단에 직접 필요할 때만 짧게 재호출한다.

- `Project ↔ Namespace`의 Xi'an 운영 관계
- `VIP-A/API ↔ VIP-B/Ingress` 구분
- `Service 존재 ≠ Endpoint 연결`
- `PVC Bound ≠ Pod Mount 성공`
- `Pod Running ≠ 사용자 HTTP 성공`
- Host·Member KubeSphere Multi-Cluster 관리 경계
- Xi'an 실제 Role, Quota, StorageClass, Ingress, Monitoring 값

## 2. 고정 역할과 판단 루프

| 역할 | 고정 책임 |
|---|---|
| 강사 | Xi'an 기준·시나리오·반증 질문 제공, 안전 중단, 승인 경계 통제, 최종 평가 |
| 주 수강생 | 실제 운영 대상 선택, 문서 탐색, 조회 순서 결정, 정상·이상 판단, teach-back과 에스컬레이션 주도 |
| 보조 수강생 | 증적의 대상·출처·시각 감사, 실제값 교차검증, 누락 확인, 인시던트 타임라인과 교대 인계 기록 |

```text
대상 Cluster·context·Namespace 확인
→ 정상 경로와 기대 결과 확인
→ 증거로 확인된 첫 단절 식별
→ 읽기 전용 반증 확인
→ 승인된 조치 또는 담당 영역으로 에스컬레이션
```

## 3. P0 - 환경 준비일

P0는 기술 교육과 분리된 최소 1일이다. 접속 문제가 남으면 시간을 추가하며, D1을 접근 설정일로 전환하지 않는다.

| 시간 | 주제 | 강사 | 주 수강생 | 보조 수강생 | 산출물·완료 기준 |
|---|---|---|---|---|---|
| 09:00~09:20 | 역할·범위 확정 | 역할, 교육 목표, 안전 경계 설명 | 실제 운영 범위와 계정 확인 | 역할·질문 기록 | 역할표와 질문 목록 |
| 09:20~10:30 | 접속 시험 1 | Host·PRD·DEV·Harbor 접근 경로 제공 | 운영 계정으로 KubeSphere·Harbor·Monitoring 접속 | 성공·실패·권한 범위 기록 | 필수 UI 접속 확인표 |
| 10:45~12:00 | 접속 시험 2 | Bastion·MFA·방화벽·조회용 kubectl 경로 점검 | `current-context`, Cluster, Namespace 조회 | context·권한 교차검증 | CLI·Bastion 접근 확인표 |
| 13:00~14:20 | 실제값 기준선 | 카탈로그와 화면의 확인 방법 제시 | Domain, VIP-A/B, StorageClass, Monitoring URL, Harbor Project 확인 | 값·출처·시각·현재성 기록 | Xi'an 실제값 기준표 |
| 14:35~15:40 | 실습·증적 게이트 | 조건부 변경 실습의 승인 기준 판정 | 정상 애플리케이션·조회 화면·실습 가능 범위 확인 | 자료·증적·Blocker 정리 | 실습 판정표와 Blocker 목록 |
| 15:40~16:00 | P0 종료 | 미확정 항목을 기술 교육과 분리 | 미확정 값을 담당자·기한과 함께 확인 | Blocker 교차 확인 | P0 완료 또는 추가 준비 결정 |

### P0 완료 기준

- Host, PRD Member, DEV Member, Harbor, Monitoring과 허용된 kubectl 조회가 실제로 동작한다.
- Cluster·context·Namespace, Domain, VIP-A/B, StorageClass, Monitoring URL 값마다 확인 출처와 시각이 있다.
- 미확정 값은 `미확인`으로 두고 담당자와 확인 시점을 기록한다.
- 아래 6개 조건으로 변경 실습을 `허용` 또는 `불허`로 명시한다.

### 조건부 변경 실습의 6개 승인 조건

1. 격리 Cluster 또는 명시적으로 승인된 실습 Namespace가 있다.
2. 교육생용 최소 권한 계정이 준비돼 있다.
3. 변경 승인자와 승인 상태가 확인됐다.
4. 허용 변경 대상과 범위가 구체적으로 정해졌다.
5. 정리·원복 절차와 정리 완료 확인 방법이 있다.
6. 성공 기준과 즉시 중단 기준이 합의됐다.

하나라도 충족하지 못하면 변경하지 않고 현재 상태 조회, 마스킹 출력, 화면 워크스루, Runbook·정상 증적 대조 또는 탁상훈련으로 대체한다.

## 4. D1 - Xi'an 실제 토폴로지와 운영 경계

**목표:** 일반 아키텍처 설명 대신 Xi'an의 Host·PRD/DEV Member·Harbor·Bastion·LB·Storage·Monitoring과 담당 조직 경계를 실제값으로 확인한다.

| 시간 | 주제 | 강사 | 주 수강생 | 보조 수강생 | 산출물·완료 기준 |
|---|---|---|---|---|---|
| 09:00~09:20 | P0 회상 | P0 Blocker와 사용 가능한 조회 범위 확인 | 대상과 context 재확인 | 기준표 최신성 확인 | 당일 대상표 |
| 09:20~10:30 | 실제 토폴로지 | Xi'an 구성과 Taylor 예시 혼입 함정 제시 | 카탈로그·화면으로 Host/Member/Harbor 역할 설명 | 값 출처를 `사용/금지/재확인` 분류 | 토폴로지·책임 경계도 |
| 10:45~12:00 | 두 요청 경로 | VIP-A/API와 VIP-B/Ingress 비교 질문 | API 관리 경로와 User HTTP 경로를 실제 Domain·VIP로 그리기 | 경로·대상값 교차검증 | API·사용자 요청 경로도 |
| 13:00~14:20 | Multi-Cluster 역할 | Host 중앙 관리와 Member Workload 실행 경계 제시 | Host Console에서 Member와 실제 Workload 위치 확인 | Host/Member 값 혼용 감사 | Multi-Cluster 역할표 |
| 14:35~15:40 | 외부 책임 경계 | AD·CyberArk·DNS·LB·ONTAP 담당 영역 질문 | 각 의존성이 어느 경로에 개입하는지 분류 | 담당 조직·인계 정보 기록 | 외부 의존성 맵 |
| 15:40~16:00 | Teach-back | 반증 질문만 수행 | 10분 구조·경계 설명 | 근거 누락 감사 | 구조 teach-back 기록 |

**완료 기준:** Host·Member, VIP-A·VIP-B, Xi'an 실제값과 Taylor 예시를 혼동하지 않고 각 외부 의존성의 담당 영역을 설명한다.

## 5. D2 - 구축 결과 인수와 KubeSphere Multi-Cluster 검증

**목표:** Step 0~5의 설치법을 설명하지 않고, 현재 구축 결과가 운영 가능한지를 복수 증거로 판정한다.

| 시간 | 주제 | 강사 | 주 수강생 | 보조 수강생 | 산출물·완료 기준 |
|---|---|---|---|---|---|
| 09:00~09:20 | 대상 확인 | 당일 Cluster·context 확인 질문 | 대상 환경 확정 | context 기록 | 대상 확인 기록 |
| 09:20~10:30 | 공통 구축 인수 | VM·LB·Bastion·Inventory 결과의 증거·중단조건 제시 | Step 0~3 결과를 Runbook·증적으로 판정 | 단일 상태값 결론 감사 | 공통 구축 인수표 |
| 10:45~12:00 | Storage 인수 | StorageClass, Test PVC, Pod Mount와 ONTAP 경계 질문 | Provisioning과 Mount를 분리해 현재 상태 확인 | `Bound` 과잉 판정 감사 | Storage 검증표 |
| 13:00~14:20 | Host·Member 인수 | Host Role, Member Monitoring 선행, Join 증거 제시 | Host·Member 완료 증거와 Join 상태 확인 | 클러스터별 값 혼용 감사 | Multi-Cluster 검증표 |
| 14:35~15:40 | Monitoring 인수 | Target·Grafana·ETCD 값의 반증 질문 | Prometheus·Grafana·ETCD Target 증거 확인 | Namespace·Endpoint·시간 기록 | Monitoring 인수표 |
| 15:40~16:00 | 중단·에스컬레이션 | 설치 재실행 금지와 경계 확인 | 증거 부족 시 다음 조회·협업 요청 설명 | 누락 증거 기록 | 인수 보류·에스컬레이션 목록 |

**완료 기준:** `Ready`, `Bound`, `Running` 하나만으로 완료를 선언하지 않고 API·System Pod·Mount·Monitoring·Host Join의 증거와 중단조건을 제시한다.

## 6. D3 - 반복 운영과 외부 의존성

**목표:** 사용자 신청을 Xi'an 정책의 Project·Role·Quota·Harbor 설정과 외부 요청으로 변환한다.

| 시간 | 주제 | 강사 | 주 수강생 | 보조 수강생 | 산출물·완료 기준 |
|---|---|---|---|---|---|
| 09:00~09:20 | 전일 회상 | 인수 증거의 반증 질문 | D2 보류 항목 설명 | 누락 증거 확인 | 보류 항목 갱신 |
| 09:20~10:30 | 신청→Project | 신청 사례와 PRD/DEV 조건 제시 | Workspace·Project·Namespace와 필요한 선행 확인 판단 | 신청값·대상 일치 감사 | 온보딩 흐름도 |
| 10:45~12:00 | Role·Quota | 모호한 권한 요청·Quota 사례 제공 | 최소 권한 Role과 CPU·Memory·Storage Quota 결정 | `project-admin`, StorageClass, 신청값 감사 | Role·Quota 결정표 |
| 13:00~14:20 | Harbor·Image 경계 | Harbor Project와 KubeSphere Project 혼동 사례 제시 | Private Project·사용자 역할·Image Secret 흐름 판단 | Harbor 권한·CA 의존성 감사 | Harbor 요청 처리표 |
| 14:35~15:40 | 외부 의존성 요청 | AD·CyberArk·방화벽·DNS·CA 단서 제공 | 내부 처리와 외부 티켓 요청을 분리 | 담당자·필수 정보·인계 기준 기록 | 외부 요청 맵 |
| 15:40~16:00 | 처리 결과 확인 | 승인 경계 질문 | 신청 사례를 처음부터 완료 통보까지 설명 | 누락·과잉 권한 감사 | 온보딩 체크리스트 |

P0 게이트가 통과한 경우에만 Workspace·Project·Role·Quota·Harbor Project/User를 생성·검증·정리한다. 그 외에는 UI·신청서·증적 판정으로 진행한다.

**완료 기준:** 신청에서 권한·Quota·Harbor·외부 의존성까지 누락 없이 연결하고, 임의 권한 상승이나 실제값 추측을 하지 않는다.

## 7. D4 - 정상 운영 경로와 Daily Monitoring

**목표:** 주 수강생이 기존 정상 Workload를 기준으로 Image·PVC·Pod·Endpoint·Ingress·HTTP·Monitoring을 정순·역순으로 판정한다.

| 시간 | 주제 | 강사 | 주 수강생 | 보조 수강생 | 산출물·완료 기준 |
|---|---|---|---|---|---|
| 09:00~09:20 | 기준선 확인 | 정상 사례와 대상 확인 질문 | 정상 Workload·Namespace·context 확인 | 기준선 시각 기록 | 정상 기준선 |
| 09:20~10:30 | Image·Storage 경로 | Image Secret·PVC·Mount의 반증 질문 | Image→Pod, PVC→Mount 증거 수집 | `Bound`와 Mount 증거 분리 | 배포·저장소 증적표 |
| 10:45~12:00 | 요청 경로 | Service·Endpoint·Ingress·VIP-B·HTTP 질문 | User 경로를 정순·역순으로 조회 | Endpoint·HTTP 증거 감사 | 요청 경로 증적표 |
| 13:00~14:20 | Monitoring | Target·Dashboard와 Workload 상태 차이 질문 | Prometheus·Grafana와 Cluster 상태 확인 | 대상·시각·값 기록 | Daily Monitoring 기준선 |
| 14:35~15:40 | 운영 시나리오 | 부분 실패 단서만 제공 | 대상 확인부터 정상/이상 판정까지 지휘 | 누락 확인·반증 질문 기록 | 정상 운영 수행표 |
| 15:40~16:00 | Teach-back | 정답 대신 판정 기준 평가 | 3분 안에 첫 확인 지점과 최종 정상 기준 설명 | 증적 완전성 감사 | 운영 teach-back 기록 |

P0 게이트가 통과한 경우에만 샘플 Workload를 생성·확인·정리한다. 기본은 기존 정상 Workload 조회다.

**완료 기준:** `Pod Running ≠ HTTP 성공`, `PVC Bound ≠ Mount 성공`, `Service 존재 ≠ Endpoint 연결`을 실제 증거와 함께 설명하고 최종 HTTP·Monitoring까지 판정한다.

## 8. D5 - 통합 운영과 장애 초동 판단

**목표:** 주 수강생이 장애 시나리오를 지휘하고 보조 수강생이 증거·타임라인을 감사하며, 안전한 에스컬레이션 패키지를 완성한다.

| 시간 | 주제 | 강사 | 주 수강생 | 보조 수강생 | 산출물·완료 기준 |
|---|---|---|---|---|---|
| 09:00~09:20 | 역할·대상 확인 | 시나리오 규칙과 안전 중단 조건 공지 | 인시던트 리드 역할 수락 | 기록 형식 준비 | 인시던트 역할표 |
| 09:20~10:30 | 사례 1: NFS Mount | 증상·단서를 순차 투입 | 첫 조회와 Kubernetes/ONTAP 경계 결정 | 시각·증적·가설 기록 | NFS 판정표 |
| 10:45~12:00 | 사례 2: Monitoring 오적용 | 잘못 복사된 Endpoint·Namespace 단서 제공 | 현재값 대조·반증 순서 결정 | 사용 금지 값·증거 감사 | Monitoring 판정표 |
| 13:00~14:20 | 사례 3: Host UI 504 | Router·Ingress 단서 제공 | 공유 경로와 Router별 분기 판단 | 조회 순서·금지 변경 기록 | 504 판정표 |
| 14:35~15:40 | 최종 통합 teach-back | 위험 변경 시에만 개입 | 사례 하나를 `대상→정상 경로→첫 단절→반증→에스컬레이션`으로 발표 | 독립 평가·타임라인 완성 | 에스컬레이션 패키지 |
| 15:40~16:00 | 종료·후속 | 통과·보류를 분리 | 실제 운영에서 추가 확인할 항목 인계 | 미확정·담당자·기한 기록 | 교대 인계서 |

**완료 기준:** 관찰과 가설을 분리하고, 첫 단절·다음 읽기 전용 확인·금지 변경·담당 영역을 근거로 제시한다. 장애 생성, 재시작, 재배포, LB·Storage 정책 변경은 수행하지 않는다.

## 9. 최종 산출물과 공통 금지 범위

| 산출물 | 판정 기준 |
|---|---|
| 접근 확인표·Blocker 목록 | 시스템별 접속 결과, 권한 범위와 미확정 담당자가 있다. |
| Xi'an 실제값 기준표 | 값, 확인 출처, 시각, 사용 가능 여부가 있다. |
| 토폴로지·책임 경계도 | Host·Member, VIP-A/B, 외부 담당 조직을 구분한다. |
| 구축·Multi-Cluster 인수표 | Step 0~5 결과의 증거, 중단·에스컬레이션이 있다. |
| 온보딩·정상 운영 증적표 | Role·Quota·Harbor·Image·Mount·HTTP·Monitoring을 연결한다. |
| 인시던트 타임라인·교대 인계서 | 첫 단절, 반증, 금지 변경, 담당자와 다음 확인이 있다. |

다음은 실제 수행 대상으로 잡지 않는다: 전체 Cluster 재설치·Playbook 실행, Worker 변경, taint·label, Member Unbind·Import, Native API 외부 노출, 인증서 갱신, Namespace 삭제·복구, Monitoring 설정 재적용, RBAC·Network·LB·ONTAP 정책 변경, Secret·Token·개인키·kubeconfig 원문 출력.

## 관련 문서

- [[Xi'an 현지 교육 1주 2주 커리큘럼 시안|Xi'an 현지 교육 1주·2주 커리큘럼 시안]]
- [[Xi'an 현지 교육 준비 계획|Xi'an 현지 교육 준비 계획]]
- [[Taylor 4주 교육 수행 분석|Taylor 4주 교육 수행 분석]]
- [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
- [[50. 운영/01. Operations Overview/운영 안내|운영 안내]]
