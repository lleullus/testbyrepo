---
title: "Xi'an 현지 교육 준비 계획"
status: draft
doc_type: plan
scope: "Xi'an DKS 설치·운영 종합 인수인계 교육 준비"
updated: "2026-07-26"
target_date: "2026-08-24"
parent: "[[00. 홈|Xi'an 전환 운영 가이드]]"
---

# Xi'an 현지 교육 준비 계획

> [!important] 문서 상태
> 이 문서는 2026-08-24 출국 전 교육 준비를 위한 **초안**이다. 기존 작업 상태판의 미착수·보류 표기를 현재 구현 상태로 사용하지 않는다. 사용자가 확인한 최신 사실인 **구현 완료, 현재 운영상 문제 없음**을 준비 기준으로 사용한다.

## 0. 처음 시작하는 페이지

> [!tip] 오늘은 20분만 한다
> 이 문서 전체와 링크된 매뉴얼을 먼저 읽지 않는다. 아래 `첫 20분`을 수행해 **한 애플리케이션의 정상 경로 지도 1장**을 만드는 것이 첫 작업이다. 빈칸이 생기면 추측하지 않고 `미확인`이라고 쓴다.

바로 시작:

1. 20분 타이머를 켠다.
2. `Image, Deployment, Pod, PVC, Service/Endpoint, Ingress, VIP-B, User` 여덟 칸을 쓴다.
3. 문서를 보지 않고 화살표와 각 역할을 적는다.
4. 연결을 증명할 상태나 화면을 적고, 모르는 곳은 `미확인`으로 남긴다.
5. 아래 기준 경로와 비교해 고친 뒤 90초 동안 설명한다.

### 0.1 먼저 버릴 부담

출국 전까지 모든 명령어와 환경값을 외울 필요는 없다. 머리에 넣을 것과 문서에서 찾을 것을 분리한다.

| 머리에서 바로 꺼낼 것                                       | 실행 전에 문서·화면에서 찾을 것                         |
| -------------------------------------------------- | ------------------------------------------ |
| Host와 Member의 역할 차이                                | IP, 도메인, hostname, Namespace의 실제값          |
| VIP-A는 API, VIP-B는 Ingress라는 차이                    | 현재 `context`, StorageClass, 인증서와 Secret 이름 |
| Image → Pod, User → Ingress → Service → Pod의 정상 경로 | 정확한 명령어, 파일 경로, 버전, manifest 값             |
| `Running`과 실제 서비스 성공, `Bound`와 실제 Mount 성공의 차이     | 현재 상태 출력과 작업 승인·복구 절차                      |
| 대상 확인 → 정상 경로 → 첫 단절 → 증적 → 안전 조치의 판단 순서           | 담당자, 연락망, 현장별 예외값                          |

### 0.2 첫 판단 장면

초보자가 처음 익힐 판단은 “컴포넌트 정의를 얼마나 많이 아는가”가 아니다.

> 사용자는 애플리케이션 URL이 정상이라고 말하거나 접속이 안 된다고 말한다. 강사는 이 요청이 어느 Member Cluster의 어떤 Pod까지 가야 하는지 설명하고, 각 연결을 실제 상태로 확인하며, 처음 끊긴 지점에서 멈춰야 한다.

정상 경로는 두 방향으로 본다.

```text
[배포 경로]
Deployment → Pod
               ├─ Image Secret으로 인증해 Harbor Image Pull
               └─ PVC/Volume Mount

[사용자 요청 경로]
User → DNS/VIP-B/LB → Ingress → Service → Endpoint → Pod

[관리·관측 경로]
Host KubeSphere → Member 상태 관리
Prometheus/Grafana → Cluster와 Workload 상태 관측
```

Host Cluster와 VIP-A는 위 사용자 HTTP 요청의 중간 경로가 아니다. Host는 중앙 관리 역할이고, VIP-A는 Kubernetes API 접근 경로다.

### 0.3 판단 루프

정상 상태를 설명할 때도, 장애 질문을 받을 때도 항상 같은 순서로 판단한다.

1. **관찰**: 대상 Cluster, context, Namespace와 실제 상태는 무엇인가?
2. **비교**: 정상 경로의 어느 연결과 일치하거나 어긋나는가?
3. **판단**: 증거로 확인된 첫 단절 지점은 어디인가?
4. **확인**: 다음 읽기 전용 확인으로 이 판단을 반증할 수 있는가?
5. **경계**: 직접 확인할 것인가, 승인받아 변경할 것인가, 다른 담당자에게 넘길 것인가?

반복 질문은 하나다.

> **사용자 응답까지 이어지는 경로에서 처음 끊긴 연결은 어디인가?**

### 0.4 시작 패킷

#### 첫 20분

| 시간     | 할 일                                                                                  | 남길 결과            |
| ------ | ------------------------------------------------------------------------------------ | ---------------- |
| 0~3분   | 종이나 빈 화면에 `Image, Deployment, Pod, PVC, Service/Endpoint, Ingress, VIP-B, User`를 쓴다. | 빈 경로 지도          |
| 3~8분   | 화살표를 연결하고 각 항목의 역할을 한 문장으로 쓴다. 문서를 보지 않는다.                                           | 첫 회상본            |
| 8~13분  | 각 화살표가 연결됐다고 증명할 화면·상태·출력을 하나씩 적는다. 모르면 `미확인`이라고 쓴다.                                 | 증적 칸이 있는 지도      |
| 13~17분 | 위 `첫 판단 장면`의 정상 경로와 비교해 틀린 화살표와 빠진 연결만 다른 색으로 고친다.                                   | 교정본              |
| 17~20분 | 지도를 보며 90초 동안 소리 내어 설명하고, 막힌 지점 세 개를 적는다.                                            | 90초 설명 1회와 보완 목록 |

완료 조건은 완벽한 설명이 아니다. **교정 전 첫 회상본, 교정본, 막힌 지점 세 개**가 남으면 첫 20분은 완료다.

#### 필요한 것

- 이 문서와 빈 종이 또는 빈 노트 1장
- 20분 타이머
- 실제 환경을 볼 수 있다면 조회 전용 KubeSphere 화면이나 마스킹된 정상 출력
- 실제 애플리케이션을 아직 정하지 못했다면 첫날에는 이름을 모두 `<미확인>`으로 두고 구조만 그린다.
- 실습 환경과 변경 승인이 확정되기 전까지 운영 Cluster에서는 조회만 한다.

#### 막힐 때만 읽을 곳

- 화살표 자체를 모르겠으면 `0.2 첫 판단 장면`만 다시 본다.
- 용어 때문에 문장을 못 만들겠으면 아래 `로컬 용어`만 본다.
- 첫 회상본을 만든 뒤 틀린 이유를 모르겠으면 `0.8 개념 패치`에서 해당 항목 하나만 본다.
- 처음부터 `4. A부터 Z까지의 교육 지도`를 정독하지 않는다.

#### 로컬 용어

| 용어 | 여기서의 쉬운 뜻 | 이 판단에서 중요한 이유 |
|---|---|---|
| Image·Image Secret | 실행할 프로그램 묶음과 Private Harbor에서 그것을 가져올 자격증명 | Image 주소 오류와 인증 오류를 구분해야 한다. |
| Deployment·Pod | Deployment는 원하는 실행 상태를 선언하고, Pod는 실제로 실행되는 단위 | Deployment가 있어도 Pod가 정상이라는 뜻은 아니다. |
| Service·Endpoint | Service는 고정된 내부 연결점이고, Endpoint는 실제로 연결할 Pod 주소 | Service가 있어도 Endpoint가 비면 요청은 Pod에 도달하지 않는다. |
| Ingress·VIP-B | Ingress는 Host·경로를 Service로 보내고, VIP-B는 외부 요청을 Router로 전달 | 외부 접속 실패를 Kubernetes API용 VIP-A와 혼동하지 않게 한다. |
| PVC `Bound`·Mount | `Bound`는 저장공간 할당 완료이고 Mount는 Pod가 실제로 붙여 쓸 수 있는 상태 | PVC 성공과 애플리케이션의 저장소 사용 성공을 따로 판정해야 한다. |

### 0.5 첫 산출물 양식

첫날에는 실제값을 억지로 채우지 않는다. 확인한 값에는 근거를 적고, 확인하지 못한 값에는 `미확인`이라고 쓴다.

```text
대상 Cluster/context: ____________________  근거: ____________________
Namespace/Project:     ____________________  근거: ____________________
사용자 URL:            ____________________  기대 HTTP: ______________

Harbor Image:          ____________________
Image Secret:          ____________________  확인 상태: _______________
Deployment → Pod:      ____________________  확인 상태: _______________
PVC → Pod Mount:       ____________________  확인 상태: _______________
Service → Endpoint:    ____________________  확인 상태: _______________
Ingress → Service:     ____________________  Host/Port: _______________
DNS/VIP-B → Ingress:   ____________________  확인 상태: _______________
User HTTP 응답:        ____________________  상태 코드/본문: __________

처음 끊긴 연결 또는 아직 확인하지 못한 연결: __________________________
다음 읽기 전용 확인 한 가지: _________________________________________
직접 변경하지 않고 넘겨야 할 경우의 담당 영역: ________________________
```

### 0.6 초보자 함정

가장 흔한 실패는 매뉴얼을 처음부터 끝까지 읽고 “대충 알겠다”고 느낀 뒤 다음 문서로 넘어가는 것이다. 그러면 화면 앞에서 지식이 나오지 않는다.

| 약한 행동 | 왜 실패하는가 | 바꿀 행동 |
|---|---|---|
| 개념 정의와 명령어부터 암기 | 실제 요청의 어느 구간에 쓰는 지식인지 연결되지 않는다. | 한 애플리케이션 경로에 개념과 증적을 붙인다. |
| `Pod Running`을 서비스 정상으로 판단 | Service·Endpoint·Ingress·HTTP 구간은 여전히 실패할 수 있다. | 마지막 HTTP 응답까지 확인한다. |
| `PVC Bound`를 Mount 성공으로 판단 | Node에서 NFS Mount가 실패해도 PVC는 Bound일 수 있다. | Pod 상태와 Event, 실제 Mount 사용을 별도로 본다. |
| 기억나는 IP와 StorageClass를 말함 | Taylor 값이나 다른 Cluster 값을 재사용할 수 있다. | 실제값은 외우지 않고 카탈로그와 현재 화면에서 확인한다. |
| 질문을 받자마자 원인과 해결책을 말함 | 관측과 가설이 섞여 위험한 변경으로 이어진다. | 첫 단절과 반증 확인을 먼저 말한다. |

### 0.7 첫 아크 통과 기준

산출물이 다음 기준을 충족하는지 확인한다.

1. 대상 Cluster·context·Namespace를 먼저 적었고, 모르는 실제값을 추측하지 않았다.
2. Host·Member, VIP-A·VIP-B를 구분하고 사용자 요청 경로를 올바르게 그렸다.
3. 각 화살표에 연결을 증명할 화면·상태·출력을 하나 이상 붙였다.
4. `Pod Running ≠ HTTP 성공`, `PVC Bound ≠ Pod Mount 성공`을 말할 수 있다.
5. 첫 단절, 다음 읽기 전용 확인, 변경·에스컬레이션 경계를 구분했다.

실패 신호:

- Taylor 주소나 다른 Cluster 값을 Xi'an 실제값으로 추측해 적음
- `Running`, `Bound`, `Ready` 하나만 보고 전체 성공으로 판정함
- Service는 있지만 Endpoint를 확인하지 않음
- 사용자 HTTP 경로에 Host Cluster나 VIP-A를 넣음
- 확인 전에 재배포, 재시작, 설정 변경을 해결책으로 제안함

피드백 강도:

- 실제 조회 전용 화면·출력과 HTTP 응답 비교: **객관적 확인, 신뢰도 높음**
- 현재 카탈로그·정상 증적과 비교: **기준 비교, 신뢰도 중간**
- AI가 설명문만 검토: **모의 검토, 신뢰도 낮음**. 실제값 검증을 대신하지 않는다.

### 0.8 틀린 뒤에만 보는 개념 패치

| 개념 패치 | 고치는 실패 | 사용할 때 | 다시 연습할 시점 |
|---|---|---|---|
| 대상 경계: Host·Member·context·VIP | 다른 Cluster 값이나 VIP-A/B를 섞음 | 첫 통과 기준 1~2 실패 | 대상과 요청 경로를 지도 맨 위에 정확히 적은 뒤 같은 산출물을 다시 그림 |
| 선언과 실행: Deployment·Pod | Deployment 존재를 실행 성공으로 판단 | 통과 기준 3~4 실패 | Deployment 상태와 실제 Pod 상태를 별도로 지목할 수 있을 때 |
| 선택과 연결: Service·Endpoint | Service 존재를 Pod 연결 성공으로 판단 | 통과 기준 3 실패 | Service selector, Pod label, Endpoint를 한 줄로 비교할 수 있을 때 |
| 할당과 사용: PVC Bound·Mount | PVC Bound를 파일시스템 사용 성공으로 판단 | 통과 기준 4 실패 | PVC 상태와 Pod Event·Mount 상태를 따로 설명할 수 있을 때 |
| 외부 경로: Ingress·VIP-B·HTTP | Pod 정상만 보고 외부 접속도 정상으로 판단 | 통과 기준 2~4 실패 | Ingress Host·Service·Port와 최종 HTTP 결과를 연결할 수 있을 때 |

### 0.9 첫 7일 연습 사다리

첫 7일의 중심 판단은 하나다. **정상 경로에서 처음 끊긴 연결을 증거로 찾는다.** 매 연습은 조건 하나만 바꾼다.

#### Rep 0 - 정상 경로 복원, 1~2일차

- **판단 초점:** 관찰 - 대상과 실제 객체·상태를 추측 없이 적는다.
- **변경 조건:** clean case - 정상인 기존 애플리케이션 또는 마스킹된 정상 증적 한 건을 사용한다.
- **학습자 산출물:** `0.5 첫 산출물 양식` 1장과 90초 설명.
- **충돌 게이트:** 통과 기준 1~3. 대상과 요청 경로, 연결 증적이 실제값과 일치해야 한다.
- **AI 역할:** 학습자가 첫 회상본을 먼저 제출한다. AI는 제출 뒤 틀린 화살표와 빠진 증적을 표시할 수 있지만 첫 회상본을 대신 만들지 않는다.

#### Rep 1 - 오래된 값 구분, 3~4일차

- **판단 초점:** 비교 - Xi'an 현재값과 Taylor·다른 Cluster 예시를 출처로 구분한다.
- **변경 조건:** misleading cue - `tas`, `dcr.cloud...`, Taylor StorageClass 같은 오래된 예시 하나를 섞는다.
- **학습자 산출물:** `사용 / 사용 금지 / 현장 재확인` 세 칸 비교표.
- **충돌 게이트:** 통과 기준 1~2와 실패 신호 1. 문서에 먼저 나온 값이 아니라 현재 카탈로그와 화면값을 선택해야 한다.
- **AI 역할:** 학습자가 표를 만든 뒤에만 AI가 출처 확인 힌트 하나를 줄 수 있다. AI가 사용할 값을 먼저 골라주지 않는다.

#### Rep 2 - 첫 단절 판단, 5~6일차

- **판단 초점:** 판단 - 정상인 객체 목록이 아니라 처음 실패한 연결을 고른다.
- **변경 조건:** missing information - Pod는 Running이지만 Service Endpoint가 비어 있는 사례처럼 핵심 증적 하나가 빠진 사례를 사용한다.
- **학습자 산출물:** `첫 단절 / 근거 / 다음 읽기 전용 확인 / 지금 하지 않을 변경` 네 줄.
- **충돌 게이트:** 통과 기준 3~5와 실패 신호 2~5. Ingress·LB부터 바꾸지 않고 Service selector·Endpoint를 먼저 확인해야 한다.
- **AI 역할:** 학습자 판단 뒤 AI는 반증 질문 하나만 한다. 원인과 해결책을 대신 말하지 않는다.

#### Rep 3 - 다른 사례에 전이, 7일차

- **판단 초점:** 확인 - 같은 판단법이 다른 애플리케이션이나 PVC Mount 사례에서도 유지되는지 확인한다.
- **변경 조건:** transfer - 표면이 다른 읽기 전용 사례 한 건을 사용한다.
- **학습자 산출물:** 새 경로 지도, 2분 설명, 자신의 판단을 틀렸다고 만들 수 있는 반증 한 가지.
- **충돌 게이트:** 통과 기준 1~5 전체. 3분 안에 첫 단절과 다음 확인을 제시하고 상태 변경을 제안하지 않아야 한다.
- **AI 역할:** 제출 전 도움을 받지 않는다. AI는 제출 후 통과 기준만 적용해 감사한다.

### 0.10 연습 결과에 따른 다음 행동

| 결과 | 적용 기준 | 다음 행동 |
|---|---|---|
| Pass | 해당 Rep의 충돌 게이트 충족 | 다음 Rep로 이동하고 AI 도움을 한 단계 줄인다. |
| Partial pass | 경로는 맞지만 증적이나 경계 하나가 빠짐 | 빠진 칸 하나만 수정하고 같은 Rep를 다시 제출한다. 관련 `0.8 개념 패치` 하나만 본다. |
| Fail | 실패 신호가 발생하거나 첫 단절을 잘못 고름 | 다음 Rep로 가지 않는다. 잘못 고른 화살표를 지우고 같은 사례로 교정 재시도한다. |
| Blocked | 실제 화면·정상 증적·용어가 없어 판정 불가 | 추측하지 않는다. 필요한 조회 권한, 마스킹 출력 또는 기준 문서를 확보한 뒤 같은 Rep로 돌아온다. |
| Unsafe or unverifiable | 운영 변경, Secret·Token 노출, 대상 미확정이 필요함 | 실제 실행을 중단하고 조회 전용 자료나 격리 실습으로 바꾼다. 불확실한 결과를 Pass로 처리하지 않는다. |

같은 통과 기준을 두 번 연속 실패하면 범위를 늘리지 않는다. 해당 개념 패치 하나만 골라 3개의 짧은 사례에서 같은 화살표를 반복 판정한 뒤 원래 Rep로 돌아온다.

### 0.11 첫 주 안전 경계

실습 환경과 승인자가 확정되기 전 첫 주는 **관측 전용**이다.

관측에 사용할 수 있는 예:

- KubeSphere와 Harbor의 현재 설정·상태 조회
- `kubectl config current-context`, `kubectl cluster-info`
- `kubectl get`, `kubectl describe`, 민감정보가 없는 `kubectl logs --since=...`
- Node, Pod, PVC, Service, Endpoint, Ingress, Event, Monitoring Target 확인
- 브라우저 또는 승인된 URL의 HTTP 상태 확인

첫 주 금지:

- `apply`, `create`, `edit`, `patch`, `delete`, `label`, `taint`, `scale`, `rollout restart`
- `ansible-playbook`, `kubeadm certs renew`, `crictl rmp`, Node 재부팅
- Namespace·Pod·Secret·ConfigMap 삭제, KubeSphere Unbind·Import
- Route·방화벽·LB·ONTAP export policy·RBAC·Quota 변경
- Secret, Token, 개인키, kubeconfig 원문 출력 또는 기록
- 다른 Cluster의 manifest와 환경값을 복사해 적용

대상, 승인자, 변경 영향, 백업, 복구, 성공·중단 기준 중 하나라도 미확정이면 실제 변경 시연을 하지 않는다.

### 0.12 진척 기록

각 시도 후 한 줄만 기록한다.

| case | first-ranked cue | decision | collision result | patch used | next change | AI support level |
|---|---|---|---|---|---|---|
| Rep 0 - 정상 경로 |  |  |  |  |  | 첫 제출 후 교정 허용 |
| Rep 1 - 오래된 값 |  |  |  |  |  | 제출 후 힌트 1개 |
| Rep 2 - 첫 단절 |  |  |  |  |  | 제출 후 반증 질문 1개 |
| Rep 3 - 전이 |  |  |  |  |  | 제출 후 감사만 |

첫 아크 완료 조건:

- 다른 애플리케이션 또는 다른 장애 표면의 Rep 3를 통과한다.
- 마지막 시도는 제출 전 AI 힌트 없이 수행한다.
- 통과 기준 5개 중 4개 이상을 두 번 연속 충족한다.
- 두 번 모두 대상 미확정·추측값·상태 변경 제안이 없다.

**다음 행동:** 지금 20분 타이머를 켜고 `0.4 첫 20분`의 교정 전 경로 지도 1장을 만든다.

## 1. 확인된 조건과 가정

### 확인된 조건

- 2026-08-24는 교육일이 아니라 출국일이다.
- 교육은 설치와 운영을 포함하는 종합 인수인계 성격이다.
- 기존 설치 매뉴얼과 교육·운영 가이드는 기본 전달 대상이다.
- 강사는 전달 문서를 설명하고 필요한 절차를 시연할 수 있어야 한다.
- 교육은 한국어로 진행하고 통역이 참여할 가능성이 높다.
- 현재 시스템은 정상이며 운영상 남은 문제는 없다.
- 공식 목적은 교육 이수이며, 설치 매뉴얼과 기존 교육 매뉴얼을 전달할 예정이다.

### 미확정 가정

- 교육생은 현지 인프라 담당자이나 Kubernetes 경험과 실제 담당 범위는 미확정이다.
- 별도 실습 환경은 확인되지 않았으므로 제한된 직접 조작이 가능하다고 가정한다.
- 교육 기간, 일별 시간, 인원, 계정·네트워크 접근 조건은 미확정이다.
- 고위험 절차는 운영 환경에서 실제 실행하지 않고 설명·워크스루·탁상훈련으로 대체한다.

## 2. 준비 목표

출국 전 강사는 다음 네 단계의 역량을 갖춘다.

1. **무자료 설명**: Xi'an DKS의 구성, Host·Member 역할, 정상 요청 경로를 10분 안에 설명한다.
2. **Runbook 시연**: 반복 운영 절차는 문서를 보며 안전하게 시연하고 결과를 판정한다.
3. **장애 초동 판단**: 증상에서 첫 확인 지점, 분기 기준, 안전한 다음 조치를 설명한다.
4. **작업 경계 판단**: 직접 수행, 협업 요청, 승인 필요, 운영 환경 실행 금지를 구분한다.

명령어 자체를 암기하는 것이 아니라 아래 판단 경로를 회상할 수 있어야 한다.

```text
대상 클러스터와 작업 목적 확인
→ 정상 경로와 기대 결과 확인
→ 처음 끊긴 지점 확인
→ 읽기 전용 증적 확보
→ 안전한 조치 또는 에스컬레이션
```

## 3. 교육 깊이 구분

모든 문서를 전달하더라도 모든 절차를 같은 깊이로 실습하지 않는다.

| 구분 | 출국 전 강사 기준 | 교육 방식 | 대상 |
|---|---|---|---|
| A. 반드시 체화 | 문서 없이 구조와 판단 기준 설명 | 설명, 그림, 질의응답 | Kubernetes 기초, Xi'an 구조, Host·Member, VIP-A/B, Harbor, Storage, Monitoring, 정상 요청 경로 |
| B. 직접 시연 | Runbook을 보며 안전하게 수행하고 성공 여부 판정 | 강사 시연 후 교육생 실습 | 사용자·Project·Role·Quota, Harbor Project·User, PVC·Deployment·Service·Ingress, 기본 상태 확인 |
| C. 문서 기반 워크스루 | 목적·선행조건·실행 순서·완료조건·중단조건 설명 | 화면·명령 출력 예시, 탁상훈련 | 전체 설치 흐름, Worker 추가, taint·label, Native API, 인증서 갱신, 복구 절차 |
| D. 운영 환경 실행 금지 | 위험과 승인·복구 경계 설명 | 사례 설명만 수행 | 디스크 Full 생성, 로그 삭제, Namespace 삭제, 전체 재설치, 임의 인증서·RBAC·네트워크·Storage 정책 변경 |

## 4. A부터 Z까지의 교육 지도

### 4.1 기초 질문 대비

다음 개념은 정의만 외우지 않고 하나의 애플리케이션이 배포되어 사용자 요청을 받는 흐름으로 설명한다.

```text
Deployment가 Pod를 생성함
├─ Pod는 Image Secret으로 인증해 Harbor Image를 가져옴
└─ Pod는 PVC를 통해 필요한 저장소를 Mount함

사용자 요청은 VIP-B/LB → Ingress → Service → Endpoint → Pod로 이동함
Prometheus와 Grafana는 Cluster와 Workload 상태를 관측함
```

필수 개념:

- Container, Image, Pod, Deployment
- Namespace와 KubeSphere Project
- Service, Endpoint, Ingress, VIP-A, VIP-B
- Node 역할과 taint·label
- StorageClass, PV, PVC, NFS Mount
- ConfigMap, Secret, 인증서
- RBAC, Workspace, Project Role
- Host Cluster, Member Cluster, Host Join
- Harbor, Prometheus, Grafana, Alertmanager

### 4.2 환경과 구조

- [[10. 기준 및 설계/클러스터 카탈로그/클러스터 카탈로그|클러스터 카탈로그]]를 기준으로 Host, PRD Member, DEV Member, Harbor의 역할을 설명한다.
- VIP-A는 Kubernetes API, VIP-B는 Ingress 경로라는 차이를 설명한다.
- Bastion, Load Balancer, Kubernetes, Storage, Harbor, Monitoring의 책임 경계를 설명한다.
- 대상 클러스터의 context, cluster name, domain, VIP, StorageClass를 작업 전에 확인하는 이유를 설명한다.

### 4.3 설치 문서 내용 지도

설치 문서는 `VM 준비 → 공통 노드 준비 → Kubernetes → Storage → Host·Member 역할 구성`의 한 흐름이다. 교육 현장에서 전체 설치를 다시 실행하기보다 각 단계의 입력, 변경 내용, 완료 확인, 다음 단계와 중단 지점을 설명한다.

| 단계와 문서 | 문서 안에 있는 실제 내용 | 강사가 설명해야 할 핵심 | 교육 깊이 |
|---|---|---|---|
| `0. Initial VM setting` 및 [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook Step 0]] | 노드 hostname·IP 확인, ETCD용 `/var/lib/etcd` 파일시스템, LB alert exception 요청, VIP-A/B 라우팅 테스트, Bastion DATA Disk와 `dspaas` 권한 확인 | Kubernetes 설치 전에 VM·디스크·계정·LB가 왜 먼저 준비되어야 하는지, VIP-A는 API이고 VIP-B는 Ingress라는 차이 | A: 구조 설명, C: 절차 워크스루 |
| `1. Bastion Node Pre-setting` | Bastion 디스크 파티션과 LVM, 사용자·wheel 권한, `/etc/hosts`, SSH key, 설치 디렉터리와 Kubespray 실행 준비 | Bastion은 설치 명령을 실행하는 관리 거점이며, 대상 노드 접근과 설치 파일의 기준점이라는 역할 | A: 역할 설명, C: 절차 워크스루 |
| `2. K8S Cluster Nodes Pre-setting` | `dspaas` sudo 권한, SSH key 배포, YUM repository, 필수 패키지, SWAP 비활성화, logrotate, 사내 CA, sysctl, VM 리소스 확인 | 어떤 설정이 자동화되고 어떤 값은 현장에서 별도 확인해야 하는지, 노드 준비 완료를 무엇으로 판정하는지 | C: 문서 기반 설명 |
| `3. Deploy DKS Cluster using Kubespray` | `hosts.yaml` inventory와 환경 변수 확인, Kubespray playbook 실행, Master·ETCD·Router·Infra·Worker 구성, Node·System Pod·API 연결 검증 | Inventory가 실제 환경 설계도라는 점, 잘못된 IP·그룹·CIDR이 전체 클러스터에 미치는 영향, `Ready`만으로 검증을 끝내면 안 되는 이유 | A: 역할 구조, C: 전체 실행 워크스루 |
| `4. Install Storage Components` | Trident와 Storage backend 구성, StorageClass 생성, Test PVC와 Pod Mount 확인, ONTAP·NFS 의존성 확인 | `PVC Bound`는 볼륨 생성 성공이고 실제 Pod Mount 성공과는 다르다는 점, Kubernetes와 ONTAP의 책임 경계 | A: 개념 체화, B: 안전한 테스트 시연 |
| [[30. 구축 및 전환/Host 및 Member 구축 분기|5.1 Host Cluster]] | KubeSphere installer 적용, 설치 로그 확인, Host 전용 Monitoring·Prometheus 설정, Alert·Record Rule, retention·external label, RBAC와 `cluster-configure` 적용 | Host는 중앙 KubeSphere 관리 클러스터이고 Member를 관리한다는 점, Host 전용 설정을 Member에 복사하면 안 되는 이유 | A: 차이 체화, C: 설치 워크스루 |
| [[30. 구축 및 전환/Host 및 Member 구축 분기|5.2 Member Cluster]] | 선행 컴포넌트와 CRD, DKS custom Prometheus stack, Ingress·External ETCD Monitoring, Grafana Dashboard, KubeSphere 설치, Host Import·Join | Member에서는 Monitoring을 먼저 구성한 뒤 KubeSphere와 Host Join으로 이어진다는 순서, 클러스터별 ETCD·Namespace·Storage 값을 확인해야 하는 이유 | A: 순서 체화, C: 설치 워크스루 |
| [[50. 운영/06. Harbor Manual/01. Harbor Installation|Harbor Installation]] | Docker 20.10.16과 docker-compose 1.27.4, offline installer, 사내 CA와 Harbor 인증서, `harbor.yml`, `/harbordata`, ChartMuseum·Trivy 포함 설치 | Harbor가 이미지 공급 경계라는 점, hostname·인증서·데이터 경로가 맞아야 하는 이유, 개인키를 교육자료에 노출하면 안 되는 이유 | C: 설치 워크스루 |

### 4.4 KubeSphere 운영 문서 내용 지도

KubeSphere 운영 문서는 `신청 접수 → Workspace·Project → 사용자·권한 → CPU·Memory·Storage Quota → CLI 접근` 순서로 연결된다.

| 문서 | 문서 안에 있는 실제 내용 | 시연하거나 답해야 할 내용 |
|---|---|---|
| [[50. 운영/04. Kubesphere Operation/01. Creating Workspaces&projects|Creating Workspaces & Projects]] | 신청서 접수, Dashboard·Harbor·PRD/DEV 방화벽 대상, 사용자 로그인 이력 확인, Workspace 생성, PRD·DEV 클러스터 할당, Project 생성 | Project는 Kubernetes Namespace이고 DKS는 Workspace와 Project를 1:1로 운영한다. 사용자가 한 번 로그인해야 계정을 확인할 수 있으며 이름의 `prd/dev`에 따라 대상 Member가 갈린다. |
| [[50. 운영/04. Kubesphere Operation/02. Inviting a new member|Inviting a New Member]] | Workspace Settings에서 사용자 초대, 최초 `viewer` 부여, 기존 멤버 역할 변경·제거 | Workspace 초대는 Project 권한 부여 전 단계이고 `viewer`는 조회만 가능하다. |
| [[50. 운영/04. Kubesphere Operation/03. Assigning project roles to users|Assigning Project Roles]] | Project Member 초대, `project-admin`, `project-operator`, `project-viewer` 역할 배정 | 신청서의 Admin은 실제 `project-admin`이 아니라 `project-operator`, User는 `project-viewer`로 매핑된다는 DKS 정책을 구분한다. |
| [[10. 기준 및 설계/KubeSphere RBAC|KubeSphere RBAC]] | Platform·Workspace·Project 3계층, 각 계층의 Admin·Operator·Viewer 권한, Workload·Storage·ConfigMap·Secret·Monitoring·멤버 관리 권한표 | “누가 무엇을 볼 수 있고, 변경할 수 있고, 다른 사용자를 관리할 수 있는가”를 계층별로 설명한다. 최소 권한 원칙과 임의 `project-admin` 부여 금지를 강조한다. |
| [[50. 운영/04. Kubesphere Operation/04. Setting quotas|Setting Quotas]] | Workspace CPU·Memory Requests/Limits, Project CPU·Memory Requests/Limits, StorageClass별·전체 Storage ResourceQuota YAML | Request는 예약·보장값이고 Limit은 상한이라는 차이, Workspace와 Project를 같은 신청값으로 설정하는 이유, 실제 StorageClass 이름 확인 후 적용해야 하는 이유를 설명하고 기본 Quota 설정을 시연한다. |
| [[50. 운영/04. Kubesphere Operation/06. Enable users using kubectl CLI|Enable Users Using kubectl CLI]] | Bastion 계정과 CyberArk 요청, 사용자 kubeconfig ConfigMap 추출, VIP-A·cluster·context 수정, `.kube/config` 권한 설정, `current-context`와 Namespace 접근 확인 | CLI가 웹 UI의 우회 접근이며 대상 클러스터와 사용자 권한을 kubeconfig가 결정한다는 점을 설명한다. 교육본에서는 초기 비밀번호, kubeconfig·Token 출력과 명령 이력 노출을 제거하거나 마스킹한다. |

### 4.5 Harbor 운영 문서 내용 지도

Harbor 운영 문서는 `프로젝트 생성 → 멤버 역할 → 이미지 Push → Private 이미지 Pull` 흐름이다.

| 문서 | 문서 안에 있는 실제 내용 | 시연하거나 답해야 할 내용 |
|---|---|---|
| [[50. 운영/06. Harbor Manual/02. Create a project|Create a Harbor Project]] | 신청서를 기준으로 프로젝트 생성, Access Level `Private`, 기본 Storage Quota 10GB | Public은 인증 없이 Pull할 수 있으므로 금지하고, 프로젝트 이름·Quota·관리자를 신청서와 맞춘다. |
| [[50. 운영/06. Harbor Manual/03. Managing Users|Managing Harbor Users]] | `ProjectAdmin`과 `Developer` 권한 비교, 멤버 추가·제거·역할 변경 | ProjectAdmin은 멤버 관리까지 가능하고 Developer는 이미지 읽기·쓰기와 스캔은 가능하지만 멤버 관리는 못 한다. |
| [[50. 운영/07. DKS User Guide/02. Harbor User Guide|Harbor User Guide]] | Docker·Podman으로 이미지 tag·Push, Deployment에서 이미지 사용, Private 프로젝트용 Image Secret 생성·연결 | `xa.dcr.dks.samsungds.net/<project>/<image>:<tag>`의 각 부분을 설명하고 Push된 이미지가 KubeSphere Deployment로 이어지는 흐름을 시연한다. 현재 문서의 일반 예시 주소 `dcr.cloud.samsungds.net`은 Xi'an 주소로 교체해야 한다. |
| [[50. 운영/04. Kubesphere Operation/07. KubeSphere SECDS-ROOT.crt ConfigMap Mount|Harbor CA 오류 처리]] | Image Secret 생성 시 `x509: certificate signed by unknown authority`가 발생하면 Member의 `kubesphere-system`에 사내 CA ConfigMap을 만들고 `ks-apiserver`에 Mount | 계정·Secret 오류와 CA 신뢰 오류를 구분하고, 승인된 Xi'an CA인지 확인한 뒤 적용해야 한다. CA 원문과 개인키는 교육자료에 포함하지 않는다. |

### 4.6 사용자 가이드 내용 지도

사용자 가이드는 운영자가 플랫폼을 만드는 절차가 아니라, 최종 사용자가 권한을 받아 애플리케이션을 올리고 접근하는 흐름을 설명한다.

| 문서 | 문서 안에 있는 실제 내용 | 교육 전 정리할 사항 |
|---|---|---|
| [[50. 운영/07. DKS User Guide/01. DS Kubernetes Service Overview|DKS Overview]] | KubeSphere Web Console 기반 서비스, 도메인·접속 정보, AD 인증, Workspace·Project·Namespace와 Resource Quota 개요 | 현재 Taylor 클러스터명·도메인·IP가 남아 있으므로 Xi'an Host Dashboard, PRD·DEV Ingress, Harbor 주소로 교체한다. |
| [[50. 운영/07. DKS User Guide/03. KubeSphere User Guide|KubeSphere User Guide]] | AD 그룹 등록, 방화벽, Project 권한, PVC, Image Secret, Deployment, Service, Route·Ingress, Autoscaling까지의 UI 작업 | 하나의 샘플 애플리케이션으로 처음부터 끝까지 시연한다. Taylor IP·클러스터명·StorageClass 예시를 Xi'an 기준으로 교체하고, 각 단계의 성공 상태와 정리 절차를 추가한다. |
| [[50. 운영/05. Operations Manual/03. DKS FAQ|DKS FAQ]] | Project 신청, Harbor 권한, Namespace 축소·삭제, kubectl, 외부 접근, DevOps 미지원, 이미지 생성 책임, 로그인 오류 | “누가 처리하는가”를 중심으로 답한다. 방화벽·AD·CyberArk는 협업 요청, Image 빌드는 사용자 책임, DKS는 ContainerD 기반 실행·Pull을 지원한다는 경계를 설명한다. |

### 4.7 기술 운영 Runbook 내용 지도

기술 Runbook은 반복 사용자 작업보다 영향도가 크다. 교육에서는 실행 명령보다 변경 전 확인, 완료 판정, 중단조건과 복구 책임을 먼저 설명한다.

| 문서 | 문서 안에 있는 실제 내용 | 교육에서 강조할 판단 |
|---|---|---|
| [[50. 운영/05. Operations Manual/01. Adding a worker node using kubespray|Worker Node 추가]] | VM·NetApp ACL 확인, Node Pre-setting, Kubespray inventory에 신규 노드 추가, `scale.yml --limit`, Node Ready·버전·System Pod·Deployment·PVC 검증, 별도 inventory 정리 | `Ready`만 확인하지 않고 시스템 Pod와 실제 Workload·Storage까지 검증한다. 실패 시 전체 playbook을 반복하지 않고 SSH·inventory·Ansible recap에서 처음 실패한 지점을 찾는다. |
| [[50. 운영/05. Operations Manual/02. Add taint and node-label when adding node|Taint·Label 적용]] | taint의 Key·Value·Effect, `PreferNoSchedule`·`NoSchedule`·`NoExecute`, inventory node group, node label, Pod nodeSelector와 toleration | taint는 Pod를 끌어오는 기능이 아니라 맞지 않는 Pod를 밀어내는 조건이다. 기존 Workload 영향과 잘못 적용했을 때의 스케줄 불능을 먼저 확인한다. |
| [[50. 운영/05. Operations Manual/05. Utilizing the Kubernetes Native API|Kubernetes Native API]] | kube-apiserver를 Service로 묶고 Ingress TLS passthrough로 노출, Source CIDR 제한, 인증 없는 403 확인, ServiceAccount·Role·RoleBinding·Token으로 접근 | 외부 노출은 CIDR과 RBAC 범위가 확정된 뒤에만 진행한다. `403`은 경로가 살아 있고 인증·권한이 거부된 것일 수 있으며, Token을 화면·문서·로그에 남기지 않는다. |
| [[50. 운영/05. Operations Manual/06. Renewing API Server Certificates|API Server 인증서 갱신]] | 모든 Master 인증서·conf 백업, ma01→ma02→ma03 순차 갱신, static Pod 재시작, 만료일·Running·`readyz/livez` 확인, Bastion kubeconfig 갱신, Member Unbind·Import | 한 Master가 완전히 정상화된 뒤 다음 Master로 간다. 백업·health check·중단 기준 없이 실행하지 않으며 교육에서는 실제 갱신 대신 순서와 판정만 설명한다. |
| [[50. 운영/05. Operations Manual/Kubernetes Dashboard 복구|Kubernetes Dashboard 복구]] | 현장 inventory 확인, Kubespray dashboard tag로 제한 재배포, Namespace·Pod·Service·Endpoint·Ingress 검증 | 전체 `cluster.yml` 재실행이 아니라 삭제된 범위만 복구한다. Token·RBAC·TLS는 임의 생성하지 않고 별도 승인 범위로 분리한다. |

### 4.8 장애 초동 대응

실제 사건을 읽기 전용 또는 탁상훈련 사례로 사용한다.

| 사례 | 관측되는 증상 | 첫 확인 지점 | 안전한 다음 조치와 금지사항 |
|---|---|---|---|
| [[60. 이슈 및 결정/장애/prd-host-pa01-xas Host UI 간헐 504 진단 핸드오프|Host UI 간헐 504]] | Console·Prometheus·Grafana·Alertmanager가 함께 간헐적 504를 반환하지만 Pod와 Endpoint는 정상 | 어느 ingress-controller가 504를 만들었는지 로그와 Router 노드를 고정 | 정상 Router와 문제 Router의 backend 경로를 비교한다. 근거 없이 timeout 상향, 전체 재설치, LB 변경, 노드 재부팅을 하지 않는다. |
| [[60. 이슈 및 결정/문제/NFS PVC Mount 실패 - ONTAP 측 확인 요청|NFS PVC Mount 실패]] | PVC는 `Bound`이고 Trident volume도 생성되지만 Pod에서 NFS Mount `exit status 32` 발생 | PVC Provisioning이 아니라 Node→Data LIF Mount 단계인지 확인 | Node의 실제 Source IP, route, NFS 2049, ONTAP export policy를 증적으로 묶어 Storage 담당자에게 전달한다. 원인 확인 전 export policy를 넓히지 않는다. |
| [[60. 이슈 및 결정/장애/dev-apps-pa01-xas Monitoring 복붙 오적용|Monitoring 복붙 오적용]] | Pod·PVC·Ingress는 정상이나 ETCD target은 Down이고 Grafana 조회가 실패 | 대상 클러스터의 ETCD Endpoint와 Grafana datasource Namespace·URL을 카탈로그와 대조 | 수정 후 Prometheus target `UP`, Grafana `Save & Test`, Dashboard 값 표시를 모두 확인한다. 다른 클러스터 manifest를 그대로 재적용하지 않는다. |
| [[60. 이슈 및 결정/장애/Kubernetes Dashboard Namespace 삭제 복구|Dashboard Namespace 삭제]] | `kubernetes-dashboard` Namespace와 하위 리소스가 삭제되어 Dashboard 접속 불가 | 실제 삭제 Namespace와 inventory의 `dashboard_enabled`, `dashboard_namespace` 확인 | Kubespray `dashboard` tag로 제한 복구하고 Namespace·Pod·Service·Endpoint·Ingress를 확인한다. 전체 클러스터 재배포나 임의 `cluster-admin` 부여를 하지 않는다. |

## 5. 출국 전 일정

### 1주차: 7/27~8/2 - 구조를 머리에서 꺼내기

- 이 문서의 `0. 처음 시작하는 페이지`만 먼저 사용한다.
- 1~2일차에는 Rep 0으로 정상 애플리케이션 경로를 복원한다.
- 3~4일차에는 Rep 1로 Xi'an 현재값과 Taylor·다른 Cluster 예시를 구분한다.
- 5~6일차에는 Rep 2로 처음 끊긴 연결과 다음 읽기 전용 확인을 판단한다.
- 7일차에는 Rep 3으로 다른 사례를 2분 안에 설명한다.
- Rep 0 첫 회상본을 만들기 전에는 전체 설치·운영 문서를 정독하지 않는다.

통과 기준:

- `0.12 진척 기록`의 첫 아크 완료 조건을 모두 충족한다.
- Host·Member, VIP-A/B, Service·Endpoint, PVC Bound·Mount를 혼동하지 않는다.
- 실제값을 추측하지 않고 `미확인`과 확인할 출처를 말한다.
- 읽기 전용 확인과 상태 변경 작업을 구분한다.

### 2주차: 8/3~8/9 - 설치 문서 Teach-through

설치 명령을 외우거나 실행하지 않는다. 매일 해당 단계의 `목적 / 진입조건 / 바꾸는 것 / 성공 증거 / 중단조건` 다섯 칸짜리 강의 카드를 만든다.

| 날짜 | 다룰 흐름 | 그날 산출물 |
|---|---|---|
| 8/3 | Step 0 VM·LB·Bastion 사전 확인 | VIP-A/B, ETCD Disk, Bastion 권한을 포함한 카드 |
| 8/4 | Step 1 Bastion과 Step 2 Node Pre-setting | Bastion 수동 작업과 Ansible 자동화 범위를 나눈 카드 |
| 8/5 | Step 3 Kubespray Cluster 배포 | Inventory가 정하는 노드 역할·IP·CIDR과 완료 증거 카드 |
| 8/6 | Step 4 Storage | StorageClass → PVC Bound → Pod Mount를 구분한 카드 |
| 8/7 | Step 5.1 Host | KubeSphere 중앙 관리, Host Monitoring, `cluster-configure` 카드 |
| 8/8 | Step 5.2 Member | Monitoring 선행 → KubeSphere → Host Join 순서 카드 |
| 8/9 | 전체 연결 | Step 0~5를 15분 안에 설명하고 막힌 단계만 재연습 |

통과 기준:

- Step마다 다섯 칸을 빠짐없이 말한다.
- Step마다 최소 하나의 관측 가능한 완료값과 하나의 중단조건을 제시한다.
- Host와 Member 설치 순서 차이를 그림 없이 설명한다.
- 15분 전체 설명 중 기억나지 않는 실제값을 추측하지 않는다.
- 상태 변경 명령은 실행하지 않고 위험과 승인조건을 먼저 말한다.

### 3주차: 8/10~8/16 - 운영 시연과 기초 질문

실제 조작은 격리된 실습 범위와 승인이 확인된 경우에만 한다. 그 전에는 조회 전용 화면, 마스킹 출력, 사전 녹화로 시연한다.

| 날짜 | 다룰 운영 | 그날 산출물 |
|---|---|---|
| 8/10 | 신청 → Workspace → Project | 신청값, 로그인 이력, PRD·DEV 배정, Project 생성의 5문장 설명 |
| 8/11 | Workspace Member → Project Role → RBAC | `viewer`, `project-operator`, `project-viewer`, `project-admin` 비교표 |
| 8/12 | CPU·Memory·Storage Quota와 kubectl 접근 | Request/Limit 차이, 실제 StorageClass 확인, context 확인 카드 |
| 8/13 | Harbor 설치 개요 → Private Project → Member → Push/Pull | Harbor와 KubeSphere Project 차이, Image 주소 구조 설명 |
| 8/14 | PVC → Deployment → Service → Ingress | 한 애플리케이션의 화면·상태·HTTP 증적을 연결한 시연안 |
| 8/15 | Worker, taint·label, Native API, 인증서 | 실제 실행하지 않을 고위험 Runbook의 목적·승인·중단 카드 |
| 8/16 | 운영 통합 리허설 | 120분 모듈 1회와 질문 주차장 |

통과 기준:

- `신청 → 권한 → Quota → Harbor Image → Workload → 외부 응답`을 하나의 이야기로 설명한다.
- 화면과 CLI에서 확인할 대상·기대 상태를 각각 하나 이상 말한다.
- 실습 가능 시 같은 시나리오를 2회 연속 성공하고 정리 결과까지 확인한다.
- 실습 불가 시 마스킹 증적을 보고 첫 실패 지점을 3분 안에 판정한다.
- 고위험 Runbook은 실제 시연하지 않고 승인·백업·중단·복구 경계를 말한다.

### 4주차: 8/17~8/20 - 장애 판단과 전체 리허설

| 날짜 | 다룰 사례와 리허설 | 그날 산출물 |
|---|---|---|
| 8/17 | Host UI 간헐 504 + 60분 모듈 | 공유 경로와 특정 Router 분기 카드, 60분 리허설 결과 |
| 8/18 | NFS PVC Mount 실패 + 120분 모듈 | Bound·Mount·ONTAP 경계 카드, 120분 리허설 결과 |
| 8/19 | Monitoring 복붙 오적용 + Dashboard 삭제 | 실제값 대조와 제한 복구 카드, 질문 주차장 정리 |
| 8/20 | 종합 리허설 | 강의·시연·통역·질문을 포함한 최대 240분 리허설과 재시험 목록 |

통과 기준:

- 네 사례 모두 `증상 → 첫 게이트 → 분기 → 안전 조치 → 에스컬레이션` 다섯 칸으로 설명한다.
- 원인을 바로 단정하지 않고 관측된 사실과 가설을 구분한다.
- 읽기 전용 확인과 상태 변경 작업을 구분한다.
- 막혔을 때 확인할 증적, 협업 대상, 지금 하지 않을 조치를 제시한다.
- 제3자가 통과 기준으로 검토하거나, 불가능하면 녹화본을 다음 날 스스로 같은 기준으로 재검토한다.

### 동결 기간: 8/21~8/23 - 교육 패키지 확정

- 신규 범위를 추가하지 않는다.
- 깨진 링크, 잘못된 환경값, 민감정보를 최종 확인한다.
- 통역을 고려해 문장을 짧게 하고 제품명과 명령어는 원문 표기를 유지한다.
- 오프라인에서도 확인할 수 있는 문서와 필요한 파일을 준비한다.
- 실습 불가 상황에 대비해 화면 캡처 또는 정상 실행 결과를 준비한다.

### 8/24 - 출국

- 교육 자료, 설치 매뉴얼, 실습 계정·접속 조건, 담당자 연락망을 최종 확인한다.
- 현지에서 바뀔 수 있는 교육 시간과 실습 환경에 맞춰 A~D 깊이를 조정한다.

## 6. 매일 60분 실행 루틴

| 시간 | 행동 | 완료 증거 |
|---|---|---|
| 0~10분 | 전날 지도를 보지 않고 다시 그린다. | 교정 전 회상본 |
| 10~25분 | 오늘 Rep의 화면·출력·문서에서 연결 하나만 확인한다. | 관측값과 출처 |
| 25~40분 | 90초 설명을 두 번 한다. 두 번째에는 첫 번째 막힘 하나를 고친다. | 설명 2회와 수정 문장 |
| 40~50분 | 해당 Rep의 충돌 게이트로 Pass·Partial·Fail·Blocked·Unsafe 중 하나를 판정한다. | 판정과 사용 기준 |
| 50~60분 | `0.12 진척 기록` 한 줄을 채우고 다음에 바꿀 행동 하나만 정한다. | 다음 연습 행동 1개 |

한 세션에서 여러 문서를 읽거나 여러 약점을 동시에 고치지 않는다. 같은 기준을 두 번 실패했을 때만 `0.8 개념 패치` 하나를 골라 보완한다.

매주 한 번은 2~3시간을 확보해 여러 모듈을 연결한 전체 리허설을 진행한다. 리허설 후에는 `중단 항목`, `문서 수정 항목`, `재시험 항목`을 각각 한 줄 이상 남긴다.

## 7. 초보 강사를 위한 전달 장치

### 7.1 모든 주제를 설명하는 90초 구조

한 문장에는 동작 하나만 넣고 각 문장 뒤에 통역 시간을 둔다.

| 순서 | 말할 내용 | 애플리케이션 경로 예시 |
|---|---|---|
| 1. 목적 | 지금 무엇을 이해시키는가? | “사용자 요청이 Pod까지 가는 경로를 설명합니다.” |
| 2. 정상 경로 | 어떤 순서로 흘러가야 하는가? | “User 요청은 VIP-B, Ingress, Service, Endpoint를 거쳐 Pod로 갑니다.” |
| 3. 성공 증거 | 무엇을 보면 정상이라고 하는가? | “Pod뿐 아니라 Endpoint, Ingress와 최종 HTTP 응답을 확인합니다.” |
| 4. 혼동 분리 | 무엇을 같은 것으로 보면 안 되는가? | “Pod Running은 HTTP 성공과 같지 않습니다.” |
| 5. 작업 경계 | 누가 무엇을 확인하거나 변경하는가? | “조회는 여기서 하고, LB 변경은 승인 후 네트워크 담당자와 진행합니다.” |
| 6. 되묻기 | 교육생이 경로를 재현할 수 있는가? | “이 요청 경로를 역순으로 말해 주시겠습니까?” |

### 7.2 모르는 질문에 답하는 절차

즉시 정답을 만들어내지 않는다. 다음 다섯 단계를 고정해서 사용한다.

1. **확인**: 질문을 한 문장으로 다시 말한다.
2. **분류**: 개념, 절차, 환경값, 권한, 장애 중 어디에 속하는지 말한다.
3. **근거**: 지금 확인된 사실과 판단 기준까지만 답한다.
4. **보류**: 실제값·정책·원인이 미확정이면 추측하지 않는다.
5. **후속**: 확인할 화면·문서·담당자와 답변할 시점을 기록한다.

사용할 고정 문장:

- “일반 원칙과 Xi'an의 실제 설정은 구분해서 확인하겠습니다.”
- “현재 화면에서 실제값을 확인한 뒤 답하겠습니다.”
- “지금 확인된 것은 증상이고 원인은 아직 가설입니다.”
- “운영 환경에서 실행해서 확인할 질문은 아니므로 읽기 전용 증적을 보겠습니다.”
- “지금 단정하지 않고 질문 목록에 남겨 확인 후 답하겠습니다.”

질문 기록 형식:

| 질문 | 분류 | 지금 답한 사실 | 추가 확인 | 담당자·답변 상태 |
|---|---|---|---|---|
|  |  |  |  |  |

### 7.3 통역을 고려한 말하기 규칙

- 제품명, 리소스명, 상태값, 명령어, IP, 도메인은 원문 표기를 유지한다.
- 처음 등장할 때만 짧은 한국어 뜻을 붙인다. 예: “PVC, 즉 저장소 사용 요청입니다.”
- `Ready`, `Bound`, `UP`, `403`, `504`를 임의로 번역하지 않고 화면값과 함께 설명한다.
- `Project/Namespace`, `VIP-A/VIP-B`, `Admin/Operator`, `Bound/Mount`는 반드시 쌍으로 대비한다.
- “올린다”, “물린다”, “죽었다”, “터졌다” 대신 생성, 연결, 응답 실패, 프로세스 중단처럼 관측 가능한 말을 쓴다.
- 명령어보다 목적과 기대 결과를 먼저 말한다.
- 통역사에게 용어표와 화면을 사전에 전달하고, 의미가 불명확하면 문장을 중간에 끊어 확인하도록 합의한다.

### 7.4 교육 시간 미확정에 대비한 모듈

아래 시간은 통역을 포함한 총 교육시간이다. 시간이 줄어들면 뒤 모듈을 압축하지 않고 하위 범위를 통째로 제외한다.

| 총 시간 | 반드시 포함 | 추가 포함 | 제외 |
|---|---|---|---|
| 60분 | 안전 경계, Host·Member, VIP-A/B, 정상 애플리케이션 경로, 읽기 전용 상태 판정, 교육생 90초 재설명 | 없음 | 전체 설치, 고급 운영, 실제 변경 |
| 120분 | 60분 범위 | Workspace·Project·Role·Quota, Harbor, 샘플 애플리케이션 조회 시연, 장애 사례 1건 | 인증서, Native API, Worker 추가 실행 |
| 240분 | 120분 범위 | 설치 Step 0~5 워크스루, kubectl 접근 개념, 기술 Runbook 경계, 장애 사례 4건 탁상훈련 | 전체 재설치, 장애 생성, 인증서·RBAC·네트워크·Storage 실제 변경 |

## 8. 최소 추가 산출물

기존 설치·운영 문서를 다시 복제하지 않고 다음 두 개만 추가한다.

### 8.1 강사용 교육 진행서

이 문서를 확장해 다음을 포함한다.

- 시간대별 교육 순서
- 모듈별 핵심 메시지와 시연 절차
- 예상 기초 질문과 짧은 답변
- 통역 시 전달할 제품명·용어 목록
- 실습 불가 시 사용할 대체 화면과 설명
- 90초 설명 구조, 질문 주차장, 60·120·240분 모듈표

### 8.2 교육생 실습·확인표

- 대상 클러스터와 context 확인
- Workspace·Project·Role·Quota 수행 결과
- Harbor Project·이미지 사용 결과
- PVC·Pod·Service·Ingress 확인 결과
- Monitoring 기본 상태 확인
- 장애 사례에서 첫 확인 지점과 에스컬레이션 대상

교육 완료는 모든 명령을 암기했는지가 아니라, 교육생이 문서를 찾아 안전하게 수행하고 위험한 작업에서 멈출 수 있는지로 확인한다.

## 9. 아직 확인할 정보

- 실제 교육 날짜, 일수, 일별 시간
- 교육생 인원, Kubernetes 경험, 실제 담당 업무
- 통역 참여 여부와 사전 용어 공유 가능 여부
- 실습 환경, 계정, 권한, 네트워크 접근 가능 여부
- 운영 환경에서 허용되는 시연 범위와 변경 승인자
- 설치파일과 교육자료의 최종 제출 형식 및 제출 기한

이 정보가 확인되면 교육 시간표와 실습 범위를 확정한다.

## 관련 문서

- [[00. 홈|Xi'an 전환 운영 가이드]]
- [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
- [[50. 운영/01. Operations Overview/운영 안내|운영 안내]]
- [[50. 운영/05. Operations Manual/04. Failure response training|Failure response training]]
- [[35. 작업 관리/작업 목록|기존 작업 목록]]
