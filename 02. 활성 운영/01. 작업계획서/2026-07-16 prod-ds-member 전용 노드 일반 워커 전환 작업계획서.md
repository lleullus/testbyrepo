---
title: "prod-ds-member 전용 노드 일반 Worker 전환"
created: "2026-07-16"
updated: "2026-07-16"
status: draft
document_type: plan-note
schema_version: 1
project: "prod-ds-member 운영"
owner: "이준호"
reviewer: "신유진"
plan_type: operation-workplan
priority: "원문 미기재"
tags:
  - workplan
  - operations
  - 운영
  - Kubernetes
  - node-conversion
  - prod-ds-member
  - 작업계획서
related: []
version: 0.1
source: "JIRA #0001/#0003 원문 기반 재구성"
doc_status: "계획 초안 (실행 증적 미포함)"
---

# prod-ds-member 전용 노드 일반 Worker 전환

> [!warning] 문서 상태
> 본 문서는 JIRA 원문과 현재 확인된 CPU Request 이슈를 바탕으로 작성한 **실행 전 작업계획서 초안**이다. `실제값`은 실행 전 공란으로 두며, 작업 완료를 의미하지 않는다.

## [ 작업 개요 ]

| 항목 | 내용 |
|------|------|
| 작업 일정 | **원문 일정:** 2026.04.10 (금) 10:30 ~ 11:00 (KST) — 현재 과거 일정이므로 실제 작업 일정 재조정 필요 |
| 작업 담당자 | 작업자: 이준호 / 검증자: 신유진 |
| 작업 내용 | prod-ds-member 전용 노드 6대 중 `khdkswkmpdta18`, `khdkswkmpdta19` 2대를 일반 Worker로 전환 |
| 작업 목적 | 일반 Worker로 스케줄링 가능한 자원을 늘리고, 공용 Worker의 가용성을 확보 |
| 작업 대상 | `prod-ds-member` / `khdkswkmpdta18`, `khdkswkmpdta19` |
| 작업 범위 | 전용 노드 6대 중 2대만 전환. 나머지 전용 노드 4대는 본 작업 범위에서 유지 |
| 작업 영향도 | JIRA 원문은 영향도 없음으로 기재했으나, 공용 Worker CPU 여유와 대상 Pod 확인 전에는 무영향으로 확정하지 않음 |
| 작업 방식 | 대상 노드의 전용 label 및 `NoSchedule` taint를 삭제하여 일반 Worker 스케줄링 허용 |

### 작업 배경 및 이슈 정리

#### 1. 현재 관측된 상황

| 구분 | 확인된 내용 | 해석 |
|------|------------|------|
| 경보 상태 | 2026-04-08 생성된 `CPU Request 80% 초과` 경보 Silence가 2026-07-29까지 활성 예정. 코멘트는 다음 저활용 회수까지였으나 회수 후 복원 이력은 확인되지 않음 | 자원 증가를 감시해야 할 경보가 장기간 억제되어 대응 시점이 늦어졌을 가능성 |
| 공용 Worker 추이 | 2026-07-08 이후 CPU Request가 80% 전후에서 유지되다가 2026-07-15 00시 이후 기준 점유량이 약 10% 상승, 순간 최고 95% 기록 | 일시적 spike만이 아니라 공용 Pool의 예약량이 한 단계 상승한 상태 |
| Pool별 편중 | 동일 산식의 PromQL 결과가 공용 Worker 약 `90.343%`, 전용 Worker 약 `9.402%` | 자원 압박은 클러스터 전체보다 공용 Worker Pool에 집중된 것으로 보임 |
| 서비스 영향 | 제공 자료에는 Pending, FailedScheduling, 오류율, CPU throttling, 실제 CPU Usage 증적이 없음 | 현재는 서비스 장애가 확정된 것이 아니라 스케줄링 여유가 줄어든 용량 위험 상태 |

#### 2. 이번 작업에서 해결하려는 문제

현재 문제는 단순히 노드 2대가 부족하다는 것이 아니다. **공용 Worker의 CPU Request 여유가 줄어든 상태에서 경보까지 장기간 억제되어, 어떤 workload가 증가를 만들었는지와 실제 서비스 영향이 분리되지 않은 것**이 핵심이다.

따라서 본 작업은 다음 두 목적을 함께 가진다.

1. 전용 노드 중 2대를 일반 Worker로 전환해 공용 Pool의 스케줄링 가능한 CPU 자원을 늘린다.
2. 전환 전후의 namespace별 Request 대비 실제 Usage, CPU throttling, Pending을 비교해 공용 Pool 압박이 완화되는지 확인한다.

#### 3. 작업 판단의 한계

전용 노드 2대의 일반 Worker 전환은 공용 Pool의 여유를 확보하기 위한 **조건부 완화 조치**다. 이것만으로 7월 15일 이후 증가한 CPU Request의 원인이 제거되지는 않는다. 증가 원인은 별도로 namespace·workload별 Request delta, replica 변화, 최근 배포·HPA·VPA 변경 이력으로 확인해야 한다.

또한 CPU Request는 실제 CPU 사용량이 아니므로 `90.343%` 또는 `95%`만으로 CPU 포화나 고객 장애를 단정하지 않는다. 반대로 Request 여유가 작으면 신규 Pod 배치와 장애 시 재스케줄링 여유가 줄어들기 때문에, 실제 Usage가 낮더라도 사전 확인 없이 전환을 진행하지 않는다.

#### 4. 작업 전 확인해야 할 핵심 질문

- 7월 15일 이후 증가분은 특정 namespace/workload의 Pod 수 증가인가, Pod당 CPU Request 변경인가?
- 공용 Worker의 높은 Request가 실제 CPU Usage·throttling·Pending으로 이어지고 있는가?
- 대상 노드에 현재 실행 중인 중요 Pod나 PDB 보호 대상이 있는가?
- label/taint 삭제 후 유입될 일반 workload를 공용 Pool이 감당할 수 있는가?
- 기존 Silence와 P-DEP/Alertfunction을 작업 종료 후 누가 어떤 시각에 복원할 것인가?

위 질문에 대한 답이 기록되기 전에는 본 작업을 서비스 영향 없음으로 확정하지 않는다.

### 작업 전 필수 판단

다음 조건을 확인하기 전에는 label/taint를 삭제하지 않는다.

1. 대상 노드의 기존 Pod와 중요 workload가 확인됨.
2. PDB, Pending, FailedScheduling, Ready 감소가 없음.
3. 공용 Worker의 CPU Request와 실제 Usage 여유가 전환 후에도 확인됨.
4. 현재 Alertmanager Silence와 P-DEP/Alertfunction 억제 상태 및 복원 담당자가 확인됨.
5. 대상 노드의 label/taint 원본을 백업했고 rollback 담당자가 지정됨.

### 소개: 작업 전 참고 확인 기준

아래 항목은 JIRA 작업 순서에 별도 Task로 추가하지 않는다. 작업 배경과 판단을 위한 참고 기준이며, 실제 확인 결과는 기존 순서의 해당 확인 항목 또는 작업 기록에 기재한다.

| 참고 확인 항목 | 확인 기준 |
|---------------|----------|
| 공용 Worker 자원 | CPU Request, 실제 CPU Usage, namespace별 `Usage/Request`, CPU throttling 추이 확인 |
| 서비스 상태 | 대상 Pod, Pending, FailedScheduling, Ready 상태, PDB 확인 |
| 대상 노드 원본 | 현재 Pod·label·taint·Node 상태를 작업 전 기록하여 변경 전후 비교에 사용 |
| 경보 복원 | 기존 Silence의 범위·종료 시각·담당자와 P-DEP/Alertfunction 복원 담당자 확인 |
| 원인 확인 | 7월 15일 이후 증가분을 namespace/workload별 Request delta와 replica 변화로 별도 추적 |

이 참고 확인은 전용 노드 전환이 CPU Request 상승의 원인을 해결한다고 오해하지 않기 위한 것이다. 전환은 공용 Worker Pool 여유를 확보하는 완화 조치이며, 증가 workload와 실제 서비스 영향은 별도 확인이 필요하다.

## [ 작업 순서 요약 ]

| 번호 | 항목 | 세부항목 | 작업 내용 | 서비스 영향도 |
|-----|------|---------|----------|------------|
| 0 | 사전 작업 | 0-1. 작업 공지 | DKS 운영 작업공지방에 일정·대상·담당자·검증자·영향도 공유 | 없음 |
| 0 | 사전 작업 | 0-2-1. P-DEP Web Health Check 동보 해제 | 작업 클러스터 P-DEP Web Health Check Turn Off | 없음 |
| 0 | 사전 작업 | 0-2-2. Alertfunction Replica Scale (1→0) | `alertfunction-deployment` replicas 1→0 | 없음 |
| 0 | 사전 작업 | 0-3-1. 대상 노드 현재 Pod 확인 | 작업 대상 노드의 현재 Pod 확인 | 없음 |
| 0 | 사전 작업 | 0-3-2. 대상 노드 현재 label/taint 확인 | 작업 대상 노드의 현재 label/taint 확인 | 없음 |
| 1 | 본 작업 | 1-1-1. 전용 노드 label 삭제 | `khdkswkmpdta18`, `khdkswkmpdta19` 전용 label 삭제 | 없음 |
| 1 | 본 작업 | 1-1-2. 전용 노드 taint 삭제 | 두 대상 노드의 `team=dscmp:NoSchedule` 삭제 | 없음 |
| 2 | 사후 작업 | 2-1-1. 대상 노드 현재 Pod 확인 | 전환 후 대상 노드 Pod 확인 | 없음 |
| 2 | 사후 작업 | 2-2-1. Alertfunction Replica Scale (0→1) | `alertfunction-deployment` replicas 0→1 | 없음 |
| 2 | 사후 작업 | 2-2-2. P-DEP Web Health Check 활성화 | 작업 클러스터 P-DEP Web Health Check Turn On | 없음 |
| 2 | 사후 작업 | 2-2-3. Alertfunction 로그 확인 | Alertfunction 로그 확인 | 없음 |

## [ 작업 순서 ]

## 0. 사전 작업

### Task 0-1. 작업 대화창 개설 및 작업 내용 공지

| 작업대상 | 세부항목 | 작업 내용 | 확인항목 | 담당자 |
|---------|---------|----------|---------|-------|
| DKS 운영 작업공지방 | Task 0-1-1. 작업 내용 공유 | 작업 일정 재확정, 대상 클러스터, 대상 노드 2대, 전환 목적, 현재 CPU Request 이슈, 작업자·검증자, 중단·복구 조건 공유 | 공지 완료 | 이준호 |

```text
작업 공지 내용:
- 작업 일정: 2026-07-16 (목) / 시간은 운영 승인 후 확정
- 작업자: 이준호
- 검증자: 신유진
- 대상 클러스터: prod-ds-member
- 대상 노드: khdkswkmpdta18, khdkswkmpdta19
- 작업 내용: 전용 Worker 2대를 일반 Worker로 전환
- 작업 목적: 일반 Worker로 스케줄링 가능한 자원 확대 및 가용성 확보
- 배경 이슈: 7월 15일 이후 공용 Worker CPU Request가 80%에서 최대 95%까지 상승
- 사전 조건: 대상 Pod/PDB/노드 상태, 공용 CPU Request·Usage, Silence 상태 확인
- 중단 조건: Pending/FailedScheduling 증가, Ready 감소, 고객 영향, 공용 CPU 압박 확대
```

### Task 0-2. 동보 해제

| 작업대상 | 세부항목 | 작업 내용 | 확인항목 | 담당자 |
|---------|---------|----------|---------|-------|
| P-DEP | Task 0-2-1. P-DEP Web Health Check 동보 해제 | P-DEP Health Check → Setting Web → Turn Off Status (작업 클러스터만 진행) | 작업 클러스터 OFF | 이준호 |
| monitoring | Task 0-2-2. Alertfunction Replica Scale (1→0) | `kubectl scale deployment -n monitoring alertfunction-deployment --replicas=0` | Alertfunction Pod 미기동 | 이준호 |

#### Task 0-2-1. P-DEP Web Health Check 동보 해제

- P-DEP Health Check → Setting Web → Turn Off Status
- 작업 클러스터만 진행

#### Task 0-2-2. Alertfunction Replica Scale (1→0)

```bash
kubectl scale deployment -n monitoring alertfunction-deployment --replicas=0
kubectl get pod -n monitoring | grep alertfunction
```

### Task 0-3. 작업 대상 확인

| 작업대상 | 세부항목 | 작업 내용 | 확인항목 | 담당자 |
|---------|---------|----------|---------|-------|
| `khdkswkmpdta18`, `khdkswkmpdta19` | Task 0-3-1. 작업 대상 노드 현재 Pod 확인 | 작업 대상 노드의 현재 Pod 확인 | 현재 Pod 목록 확인 | 이준호 |
| `khdkswkmpdta18`, `khdkswkmpdta19` | Task 0-3-2. 작업 대상 노드 현재 label/taint 확인 | 작업 대상 노드의 현재 label/taint 확인 | 전용 label 및 taint 원본 확인 | 이준호 |

#### Task 0-3-1. 작업 대상 노드 현재 Pod 확인

```bash
kubectl get pod -A -o wide | grep khdkswkmpdta1[89]
```

#### Task 0-3-2. 작업 대상 노드 현재 label/taint 확인

```bash
kubectl get nodes --show-labels | grep khdkswkmpdta1[89]
kubectl describe node khdkswkmpdta18 | grep -i taint
kubectl describe node khdkswkmpdta19 | grep -i taint
```

## 1. 본 작업

### 본 작업 요약

| No. | 세부항목 | 작업대상 | 작업 내용 | 작업 검증 방법 | 예상값 | 실제값 | 작업자 | 검증자 |
|----:|---------|---------|----------|--------------|-------|-------|-------|-------|
| 1 | Task 1-1-1. 전용 label 삭제 | `khdkswkmpdta18` | JIRA 원문 명령 실행 | `kubectl get nodes --show-labels` | 전용 label 삭제 |  | 이준호 | 신유진 |
| 2 | Task 1-1-2. 전용 label 삭제 | `khdkswkmpdta19` | JIRA 원문 명령 실행 | `kubectl get nodes --show-labels` | 전용 label 삭제 |  | 이준호 | 신유진 |
| 3 | Task 1-2-1. 전용 taint 삭제 | `khdkswkmpdta18` | JIRA 원문 명령 실행 | `kubectl describe node` | `Taints: <none>` |  | 이준호 | 신유진 |
| 4 | Task 1-2-2. 전용 taint 삭제 | `khdkswkmpdta19` | JIRA 원문 명령 실행 | `kubectl describe node` | `Taints: <none>` |  | 이준호 | 신유진 |

### Task 1-1. 전용 노드 label 삭제

> [!warning] 원문 명령 유지
> 아래 명령은 제공된 JIRA 원문을 기준으로 기록한다. 실행 전 `Task 0-3`에서 실제 label key가 일치하는지 검증한다.

```bash
kubectl label node khdkswkmpdta18 node-role.kubernetes.io/dscmp- team-
kubectl label node khdkswkmpdta19 node-role.kubernetes.io/dscmp- team-
```

검증:

```bash
kubectl get nodes khdkswkmpdta18 khdkswkmpdta19 --show-labels
```

예상값: `node-role.kubernetes.io/dscmp` 및 `team=dscmp` 전용 label이 삭제되고, 다른 label은 변경되지 않음.

### Task 1-2. 전용 노드 taint 삭제

```bash
kubectl taint node khdkswkmpdta18 team=dscmp:NoSchedule-
kubectl taint node khdkswkmpdta19 team=dscmp:NoSchedule-
```

검증:

```bash
kubectl describe node khdkswkmpdta18 | grep -i taint
kubectl describe node khdkswkmpdta19 | grep -i taint
```

예상값: `Taints: <none>` 또는 기존 taint 중 `team=dscmp:NoSchedule`만 삭제되고 다른 taint는 유지됨.

## 2. 사후 작업

### Task 2-1. 작업 대상 노드 현재 Pod 확인

| 작업대상 | 세부항목 | 작업 내용 | 확인항목 | 담당자 |
|---------|---------|----------|---------|-------|
| `khdkswkmpdta18`, `khdkswkmpdta19` | Task 2-1-1. 작업 대상 노드 현재 Pod 확인 | 전환 후 작업 대상 노드의 현재 Pod 확인 | Pod 상태 확인 | 이준호 |

```bash
kubectl get pod -A -o wide | grep khdkswkmpdta1[89]
```

### Task 2-2. 동보 활성화

| 작업대상 | 세부항목 | 작업 내용 | 확인항목 | 담당자 |
|---------|---------|----------|---------|-------|
| monitoring | Task 2-2-1. Alertfunction Replica Scale (0→1) | `kubectl scale deployment -n monitoring alertfunction-deployment --replicas=1` | Alertfunction Pod Running 확인 | 이준호 |
| P-DEP | Task 2-2-2. P-DEP Web Health Check 활성화 | P-DEP Health Check → Setting Web → Turn On Status (작업 클러스터만 진행) | 작업 클러스터 ON | 이준호 |
| monitoring | Task 2-2-3. Alertfunction 로그 확인 | `kubectl logs -n monitoring -l k8s-app=alertfunction-k8s` | 로그 이상 유무 확인 | 이준호 |

#### Task 2-2-1. Alertfunction Replica Scale (0→1)

```bash
kubectl scale deployment -n monitoring alertfunction-deployment --replicas=1
kubectl get pod -n monitoring | grep alertfunction
```

#### Task 2-2-2. P-DEP Web Health Check 활성화

- P-DEP Health Check → Setting Web → Turn On Status
- 작업 클러스터만 진행

#### Task 2-2-3. Alertfunction 로그 확인

```bash
kubectl logs -n monitoring -l k8s-app=alertfunction-k8s
```

## [ 복구 방안 ]

### R-1. 복구 조건

다음 중 하나가 발생하면 추가 스케줄링을 중단하고 rollback 여부를 작업자·검증자가 협의한다.

- 대상 Node가 `NotReady` 또는 Pressure 상태가 됨.
- 기존 중요 Pod가 Ready에서 이탈함.
- Pending 또는 FailedScheduling이 증가함.
- 공용 Worker CPU Request/Usage가 작업 전보다 악화되고 실제 서비스 영향이 발생함.
- Alertfunction 또는 P-DEP Health Check를 예정대로 복원하지 못함.

### R-2. label/taint bounded rollback

rollback은 작업 순서 밖의 소개용 참고 확인에서 저장한 원본 YAML과 label/taint 값만을 근거로 수행한다.

```bash
# 실제 원본 값 확인 후 실행. 아래 값은 JIRA 원문 기준 예시.
kubectl label node khdkswkmpdta18 node-role.kubernetes.io/dscmp=<original-value> team=dscmp
kubectl label node khdkswkmpdta19 node-role.kubernetes.io/dscmp=<original-value> team=dscmp

kubectl taint node khdkswkmpdta18 team=dscmp:NoSchedule
kubectl taint node khdkswkmpdta19 team=dscmp:NoSchedule

kubectl get nodes khdkswkmpdta18 khdkswkmpdta19 --show-labels
kubectl describe node khdkswkmpdta18 | grep -i taint
kubectl describe node khdkswkmpdta19 | grep -i taint
```

`NoSchedule` taint 복원은 기존 Pod를 자동으로 Evict하지 않는다. 전환 후 새 일반 workload가 대상 노드에 배치된 경우에는 무단 삭제·drain하지 말고, 해당 workload owner와 재배치 방안을 협의한다. 실제 원본 label 값이 확인되지 않으면 임의의 값을 넣지 않고 에스컬레이션한다.

### R-3. 동보 복구

```bash
kubectl scale deployment -n monitoring alertfunction-deployment --replicas=1
kubectl get pod -n monitoring | grep alertfunction
```

Alertfunction과 P-DEP 복구 실패 시 작업 대화창에 즉시 공유하고, 모니터링 담당자와 서비스 오너에게 연락한다.

## 작업 종료 확인

| 확인항목 | 결과 |
|---------|------|
| 작업 일정 재승인 |  |
| 사전 CPU/서비스 영향 게이트 완료 |  |
| 대상 Node label/taint 원본 백업 |  |
| 전용 label 삭제 완료 |  |
| 전용 taint 삭제 완료 |  |
| 대상 Node Ready |  |
| 대상 Pod 및 중요 workload 정상 |  |
| Pending/FailedScheduling 없음 |  |
| namespace Request 대비 Usage 재확인 |  |
| Alertfunction 1 replica 복구 |  |
| P-DEP Web Health Check 복구 |  |
| Alertmanager/Thanos 상태 확인 |  |
| 복구 방안 확인 |  |
| 최종 검증자 | 신유진 |

## 문서 한계

> - 본 문서는 JIRA #0001/#0003와 기존 작업계획서 형식을 바탕으로 작성한 계획 초안이다.
> - JIRA 원문 일정인 2026.04.10은 현재 과거이므로 실제 작업 일정과 승인 상태를 재확인해야 한다.
> - 본 문서는 실행 완료를 주장하지 않으며 모든 실제값은 실행 시 작업자와 검증자가 기재한다.
> - CPU Request 80%→95% 상승은 배경 이슈로 기록했으며, 실제 증가 workload와 서비스 영향은 Prometheus/Grafana 및 Kubernetes 상태 확인으로 확정해야 한다.
> - 제공된 전환 명령은 원문 JIRA를 기준으로 기록했으며, 실제 label/taint key가 다르면 실행 전에 중단하고 원본 상태를 확인한다.
> - `kubectl scale`, label 삭제, taint 삭제는 변경 작업이므로 작업 승인과 검증자 확인 없이 실행하지 않는다.
> - 노드 drain, Pod 삭제, 강제 eviction은 본 작업 범위에 포함하지 않는다.
