# KubeSphere Tower의 리더 선출 롤링 업데이트 교착 상태 분석 및 장애 대응 가이드 — replicas: 1 환경에서 발생하는 두 Pod의 무한 대치 인과와 Recreate 전략 전환

## 문서의 목적
- **대상 독자**: KubeSphere 및 쿠버네티스 인프라 운영 엔지니어, 클라우드 플랫폼 아키텍트, 중국 현장 유지보수 지원팀.
- **중심 질문**:
  1. Deployment 설정상 `replicas: 1`인데 왜 2개의 Tower Pod가 동시에 기동되어 서로 대치하는가?
  2. 신규 생성된 Pod는 왜 `lock is held by tower-xxx and has not yet expired` 경고를 출력하며 `0/1 Ready` 상태로 멈추는가?
  3. 현장에서 '오래된 비정상 인스턴스'로 의심하는 7월 9일 기동 Pod의 실제 상태와 역할은 무엇인가?
  4. 구 Pod를 임의로 강제 삭제할 경우 어떤 2차 장애가 발생하는가?
  5. 서비스 영향을 최소화하며 교착 상태를 해소하고 재발을 방지하는 표준 절차는 무엇인가?
- **이해할 범위**: KubeSphere Tower의 멀티클러스터 터널링 프록시 아키텍처, Kubernetes `coordination.k8s.io/v1` Lease 분산 락 메커니즘, `RollingUpdate` 배포 전략과 리더 선출(Leader Election) 간의 순환 교착(Deadlock) 인과 사슬, 현장 오판에 따른 위험성, Recreate 전략 패치를 통한 영구 해결책.

---

## 전체 이해 지도

**핵심 명제: 쿠버네티스의 기본 `RollingUpdate` 전략은 신규 Pod가 `Ready`가 된 후에 구 Pod를 종료하려 하지만, Tower는 단일 분산 락(`Lease`)을 획득해야만 `Ready`가 될 수 있으므로, 구 Pod가 락을 유지하고 갱신하는 한 신규 Pod는 영원히 `Ready`에 도달하지 못해 두 Pod가 무한히 대치하는 순환 교착(Deadlock)이 발생한다.**

```text
[전체 인과 및 구조 지도]

[서브 흐름 1: 정상 운영 상태]
7월 9일 구 Pod (tower-old) 기동 중
→ Kubernetes Lease (kubesphere-system/tower) 리더 락 점유
→ 주기적 갱신(Renew, 기본 2~5초 간격) 수행
→ 서비스 포트 정상 오픈 (1/1 Ready)
→ 멀티클러스터 에이전트 터널 트래픽 정상 중계 중 (유일한 정상 활성 리더)

[서브 흐름 2: 배포 트리거 및 교착 형성]
설정 변경 또는 업그레이드로 인한 새 ReplicaSet 생성
→ Deployment 전략: RollingUpdate (maxSurge: 25%, maxUnavailable: 25%)
→ replicas: 1 계산 시 maxSurge 올림(+1) 허용
→ 신규 Pod (tower-new) 동시 생성 허용 (시스템에 2개 Pod 공존)
   │
   ├─► 신규 Pod 기동 시도
   │   → leaderelection.go 실행하여 Lease 획득 시도
   │   → 조건 확인: 구 Pod가 락 점유 중이며 만료되지 않음 (not yet expired)
   │   → 결과: 락 획득 실패 및 "lock is held by..." 경고 무한 반복
   │   → 메인 프로세스 대기 및 Readiness Probe 실패 (0/1 Ready 고착)
   │
   └─► Deployment Controller 상태 감시
       → 조건 확인: maxUnavailable(0) 제약으로 인해 신규 Pod가 Ready(1/1)가 되어야 구 Pod 종료 가능
       → 판단: 신규 Pod가 Ready(0/1)가 아니므로 구 Pod를 종료하지 않음
       → 결과: 구 Pod 생존 유지 → 구 Pod는 계속 Lease 갱신 → 신규 Pod 영구 락 획득 불가
       └──► [순환 교착(Deadlock) 확정: 두 Pod의 무한 대치]

[서브 흐름 3: 현장의 오판과 2차 장애 리스크]
현장 엔지니어: "7월 9일 구 Pod가 오래되었으니 비정상이다. 강제 삭제(kill)하자!"
   │
   ├─► [시나리오 A] 7월 9일 구 Pod 강제 삭제 시:
   │   → 정상 리더 급작스러운 중단 (SIGKILL 시 Lease 반환 실패)
   │   → Lease 잔여 만료 시간(기본 15초) 동안 신규 Pod 기동 지연
   │   → Host-Member 간 모든 네트워크 터널 즉시 단절 및 콘솔 장애 발생
   │
   └─► [시나리오 B] 0/1 대기 중인 신규 Pod만 삭제 시:
       → Deployment Controller가 즉시 동일한 새 Pod를 다시 생성
       → 동일한 락 경합 및 교착 상태 무한 반복 (근본 해결 불가)

[서브 흐름 4: 검증된 단계별 조치 및 영구 방지]
[단기 즉각 조치] 유지보수 시간(약 10초) 확보
→ replicas 0으로 축소 (구 Pod 정상 종료 및 Lease 완전 해제)
→ replicas 1로 복구 (신규 Pod 단독 기동 → Lease 즉시 획득 → 1/1 Ready 달성)

[영구 방지책] Deployment 전략 패치
→ strategy.type을 'RollingUpdate'에서 'Recreate'로 변경
→ 인과 보장: 구 Pod의 '완전 종료'가 확인된 후에만 신규 Pod를 생성하므로 락 경합 원천 차단
```

---

## 1. KubeSphere Tower의 역할과 분산 락: 멀티클러스터 터널 단일 진입점 보장

### 멀티클러스터 아키텍처 내 Tower의 위치
KubeSphere의 멀티클러스터 제어 평면은 호스트 클러스터(Host Cluster)가 여러 멤버 클러스터(Member Cluster)를 중앙 집중식으로 관리하는 구조다. 사설망이나 NAT 뒤에 위치한 멤버 클러스터는 호스트 클러스터의 API 서버로 직접 인바운드 접근이 불가능한 경우가 많다. 
이를 해결하기 위해 KubeSphere는 **Tower** 컴포넌트를 사용한다.
- **역할**: 멤버 클러스터에 배포된 `tower-agent`가 호스트 클러스터의 `tower` 서비스로 아웃바운드 TCP/WebSocket 터널을 개설하면, 호스트 제어 평면은 이 확립된 터널을 통해 멤버 클러스터의 쿠버네티스 리소스에 접근한다.
- **구조적 특성**: 제어 평면의 게이트웨이이자 단일 통신 관문으로 작동한다.

### 단일 리더(Active-Standby) 보장과 Kubernetes Lease 메커니즘
Tower 서비스는 다중 인스턴스가 동시에 동일한 터널 세션을 중복 제어하거나 포트 충돌을 일으키는 것을 방지하기 위해 단일 활성 인스턴스(Active-Standby) 원칙을 채택한다.
- **분산 락의 대상**: 쿠버네티스 표준 API인 `coordination.k8s.io/v1` 그룹의 `Lease` 리소스를 사용하며, 네임스페이스와 이름은 `kubesphere-system/tower`이다.
- **Lease의 핵심 필드**:
  - `spec.holderIdentity`: 현재 리더 권한을 소유한 Pod 이름 (예: `tower-8645f8b7bf-8lssd`).
  - `spec.leaseDurationSeconds`: 락 유지 유효 시간 (일반적으로 15초).
  - `spec.renewTime`: 현재 리더가 마지막으로 생존 신호를 갱신한 마이크로초 단위 타임스탬프.
- **작동 원리**:
  1. 기동된 Tower 프로세스는 `leaderelection.go`를 실행하여 해당 Lease의 획득을 시도한다.
  2. 이미 다른 Pod가 락을 점유하고 있고 `renewTime + leaseDurationSeconds > 현재 시간`이라면, 락을 획득하지 못하고 대기(Retry) 상태로 유지된다.
  3. 락을 성공적으로 획득한 인스턴스만이 내부 메인 루프를 기동하고, 프록시 포트를 열며, 쿠버네티스 Readiness Probe에 성공 응답을 반환한다.

---

## 2. 순환 교착(Deadlock) 형성 인과: RollingUpdate와 Leader Election의 충돌

### replicas: 1인데 2개의 Pod가 공존하는 이유
쿠버네티스 `Deployment`의 기본 배포 전략(Strategy)은 무중단 배포를 위한 `RollingUpdate`이다.
- 기본 파라미터는 `maxSurge: 25%`, `maxUnavailable: 25%`로 설정된다.
- `replicas: 1` 환경에서 `maxSurge`를 계산할 때 쿠버네티스는 정수 올림(ceil) 처리를 수행한다.
  $$\text{Surge 허용 Pod 수} = \lceil 1 \times 0.25 \rceil = 1$$
- 따라서 롤링 업데이트가 트리거(이미지 변경, 라벨 수정, 환경변수 변경 또는 업그레이드 등)되면, 쿠버네티스는 서비스를 단절시키지 않기 위해 구 Pod(`tower-old`)를 먼저 죽이지 않고 **신규 Pod(`tower-new`)를 먼저 생성하여 총 2개의 Pod가 공존**하게 된다.

### 순환 교착의 4단계 메커니즘
업스트림 이슈(KubeSphere GitHub Issue #5855)에서 보고된 바와 같이, 이 구조는 근본적인 인과적 모순을 내포하고 있다.

```text
[단계 1: 구 Pod의 락 유지]
7월 9일 기동된 구 Pod가 여전히 Running 상태로 존재하며,
15초 유효 기간의 Lease를 2초마다 갱신(Renew)하여 락을 독점 유지한다.
         │
         ▼
[단계 2: 신규 Pod의 락 획득 실패 및 Readiness 미달]
신규 Pod가 스케줄링되어 기동을 시작하지만, 구 Pod가 락을 쥐고 있으므로
Lease 획득 루프에서 다음 로그를 반복하며 대기한다.
"leaderelection.go:341] lock is held by tower-old and has not yet expired"
Tower는 리더 락을 획득하기 전까지 Readiness Probe를 통과시키지 않으므로 상태는 0/1 Ready로 멈춘다.
         │
         ▼
[단계 3: Deployment Controller의 구 Pod 종료 차단]
Deployment Controller는 maxUnavailable: 0(replicas 1 기준 25% 버림 처리) 규칙에 따라,
신규 Pod가 '1/1 Ready' 상태에 도달한 것이 확인된 후에만 구 Pod에 종료(SIGTERM) 신호를 보낸다.
신규 Pod가 0/1이므로 구 Pod 종료 절차를 절대 진행하지 않는다.
         │
         ▼
[단계 4: 폐쇄 루프(Deadlock) 완성]
신규 Pod가 Ready가 되려면 구 Pod가 죽어야 하고(락 반환),
구 Pod가 죽으려면 신규 Pod가 Ready가 되어야 한다.
서로가 상대방의 상태 변화를 선행 조건으로 요구하면서 영구히 대치한다.
```

---

## 3. 현장 운영자의 치명적 오판과 2차 장애 리스크

현장 운영자(중국 현장 엔지니어)는 웹 콘솔의 경고 로그와 장기 기동된 타임스탬프만 보고 다음과 같이 잘못 판단하기 쉽다.

### 치명적 오판: "7월 9일 구 Pod가 비정상이므로 강제 삭제해야 한다"
- **오판의 배경**: 신규 Pod에서 `lock is held by tower-xxx`라는 에러 로그가 계속 발생하고, 7월 9일에 생성된 Pod가 비정상적으로 락을 쥐고 놓아주지 않아 신규 Pod의 시작을 방해하고 있다고 인식함.
- **실제 사실**: **7월 9일 생성된 구 Pod는 비정상이 아니라, 현재 호스트 클러스터와 모든 멤버 클러스터 간의 실제 네트워크 트래픽을 처리하고 있는 유일한 정상 활성 리더(Active Leader)**이다.

### 2차 장애 위험 분석

#### 위험 시나리오 A: 7월 9일 구 Pod를 임의로 강제 삭제(`kubectl delete pod`)할 경우
1. **터널 세션 급작스런 파괴**: 구 Pod가 처리 중이던 모든 멤버 클러스터와의 TCP/WebSocket 터널이 일시에 강제 종료된다.
2. **Lease 만료 대기 지연**: 쿠버네티스 클라이언트 리더 선출 라이브러리는 강제 종료(SIGKILL) 시 Lease 객체를 즉시 정리하지 못한다. 
3. **통신 블랙아웃(Blackout)**: Lease의 `leaseDurationSeconds`(기본 15초)가 지나 락이 완전히 만료될 때까지 신규 Pod는 리더십을 가져오지 못한다. 결과적으로 수십 초 동안 멀티클러스터 통신이 전면 마비되고, KubeSphere 웹 콘솔에서 모든 멤버 클러스터가 오프라인으로 표시되며 운영 장애로 비화된다.

#### 위험 시나리오 B: 0/1 상태로 대기 중인 신규 Pod만 삭제할 경우
1. Deployment Controller는 여전히 최신 배포 명세(ReplicaSet)를 충족하지 못했다고 판단한다.
2. 삭제 즉시 새로운 신규 Pod(`tower-new-2`)를 다시 생성한다.
3. 새 Pod 역시 동일하게 `lock is held by tower-old` 경고를 출력하며 0/1 Ready로 멈춘다. 즉, **문제가 전혀 해결되지 않고 무한 루프**가 이어진다.

---

## 4. 검증된 복구 절차 및 영구 방지책

### 1단계: 즉각 복구 절차 (단기 조치)
이 조치는 멀티클러스터 터널의 일시적인 재연결(약 5~10초)을 수반하므로, 업무 영향도가 낮은 작업 시간대에 신속하게 진행한다.

#### 1. Deployment를 0으로 축소하여 구 Pod 및 락 완전 정리
구 Pod를 정상 종료시켜 네트워크 연결을 안전하게 닫고 리더 락을 완전히 해제한다.
```bash
kubectl scale deployment tower -n kubesphere-system --replicas=0
```

#### 2. Pod 종료 및 Lease 잔여 여부 확인
구 Pod가 완전히 소멸되었는지 확인하고, 필요 시 잔여 Lease 리소스를 확인한다.
```bash
# Pod가 완전히 종료(Terminated)되었는지 확인
kubectl get pods -n kubesphere-system -l app=tower

# Lease 리소스 상태 확인 (holderIdentity 확인)
kubectl get lease tower -n kubesphere-system
```
*참고: 만약 구 Pod가 비정상 노드 장애로 인해 잔류 락을 남긴 채 내려갔다면, 아래 명령어로 Lease를 수동 정리할 수 있다.*
```bash
kubectl delete lease tower -n kubesphere-system --ignore-not-found
```

#### 3. Deployment를 1로 복구하여 신규 Pod 단독 기동
경합 대상이 없는 상태에서 신규 Pod가 단독 기동되도록 한다.
```bash
kubectl scale deployment tower -n kubesphere-system --replicas=1
```
- **결과**: 신규 Pod가 기동 즉시 Lease를 단독으로 획득하여 `1/1 Running` 및 `Ready` 상태에 도달한다.

---

### 2단계: 영구 방지책 (배포 전략 Recreate 전환)
Deployment의 배포 전략을 `RollingUpdate`에서 `Recreate`로 패치한다. 이는 향후 설정 변경, 인증서 갱신, KubeSphere 업그레이드 시 동일한 데드락이 발생하는 것을 원천 차단한다.

#### 배포 전략 패치 명령
```bash
kubectl patch deployment tower -n kubesphere-system -p '{
  "spec": {
    "strategy": {
      "type": "Recreate",
      "rollingUpdate": null
    }
  }
}'
```

#### 전략 전환의 인과적 보장 이유
- `Recreate` 전략은 신규 Pod를 띄우기 전에 **반드시 기존 Pod를 완전히 종료(Terminate)**시킨다.
- 구 Pod가 먼저 종료되므로 Lease 락이 자연스럽게 반환/만료된다.
- 이어서 기동되는 신규 Pod는 아무런 락 경합 없이 즉시 리더십을 확보하고 정상 시작된다.
- 따라서 `RollingUpdate`가 야기하는 순환 대치 조건이 성립하지 않는다.

---

## 현장 엔지니어 및 고객사 대응 가이드라인

### 국문 회신 요약 (내부 및 국내 엔지니어 공유용)
> **[현상 분석 및 답변 요약]**
> 1. **2개 Pod 공존 원인**: Deployment의 기본 무중단 배포 전략(`RollingUpdate`)에 의해 신규 Pod가 먼저 생성되었으나, Tower의 리더 선출 락(Lease) 구조상 신규 Pod가 락을 얻지 못해 `Ready(1/1)`가 되지 않아 구 Pod를 종료하지 못하고 대치 상태가 유지된 것입니다.
> 2. **7월 9일 Pod의 상태**: 해당 Pod는 비정상이 아니며, 현재 호스트-멤버 클러스터 간 터널 트래픽을 처리하고 있는 유일한 '정상 활성 리더'입니다.
> 3. **주의 사항**: 구 Pod를 임의 강제 삭제하면 멀티클러스터 통신 단절이 발생하며, 신규 Pod만 삭제하면 즉시 재기동되어 동일 현상이 반복됩니다.
> 4. **해결 방안**: 사전 승인된 유지보수 시점에 `replicas 0 -> 1` 수동 재기동으로 교착을 해소하고, Deployment 전략을 `Recreate`로 영구 패치하여 재발을 방지합니다.

---

### 중문 회신 가이드라인 (현장 중국 엔지니어 전달용 / 现场技术回复指南)

```markdown
各位工程师，您好：

针对 KubeSphere 页面中 Host Tower Pod 出现的提示及异常现象，技术分析与解决方案如下：

### 一、 现象原因分析（为何 replicas 为 1 却同时存在 2 个 Pod）
1. **7月9日运行的旧 Pod 是正常活跃实例**：
   - 7月9日创建的旧 Pod 并不是异常或僵死实例，它当前持有分布式锁（Kubernetes Lease: `kubesphere-system/tower`），是正在负责 Host 与 Member 多集群网络隧道通信的**唯一正常 Leader**。
2. **为何产生死锁（Deadlock）**：
   - Tower 默认的发布策略为 `RollingUpdate`（滚动更新），其机制是“先启动新 Pod，待新 Pod 处于 Ready 状态后再销毁旧 Pod”。
   - 但 Tower 具备 Leader Election（领导者选举）机制，新 Pod 必须抢占到 Lease 锁才能通过健康检查（Ready）。
   - 由于旧 Pod 一直正常运行并持续续租（Renew），新 Pod 无法获取锁，因此一直打印警告 `lock is held by tower-xxx and has not yet expired`，状态卡在 `0/1 Running`。
   - Kubernetes 调度器检测到新 Pod 未 Ready，便不会关闭旧 Pod，从而导致**两个 Pod 无限对峙，死锁无法自动解开**。

### 二、 风险提示（严禁随意强杀旧 Pod）
- 如果直接强制删除 7月9日的旧 Pod，会导致当前所有的多集群网络隧道瞬间中断，控制台将短暂无法访问成员集群。
- 如果仅删除 0/1 的新 Pod，Deployment 会立即再次新建 Pod，继续陷入相同的死锁循环，无法根本解决。

### 三、 标准处置与修复方案（请选择低峰期执行，影响时间约 10 秒）

#### 步骤 1：安全重置 Pod（解除当前死锁）
```bash
# 1. 缩容到 0，让旧 Pod 正常终止并释放分布式锁
kubectl scale deployment tower -n kubesphere-system --replicas=0

# 2. 确认 Pod 完全退出后，恢复为 1（新 Pod 将独占启动并立即获取锁）
kubectl scale deployment tower -n kubesphere-system --replicas=1
```

#### 步骤 2：永久防范策略（将更新策略修改为 Recreate）
为避免日后升级或配置变更时再次出现滚动更新死锁，请将 Tower 的部署策略永久修改为 `Recreate`：
```bash
kubectl patch deployment tower -n kubesphere-system -p '{
  "spec": {
    "strategy": {
      "type": "Recreate",
      "rollingUpdate": null
    }
  }
}'
```

修改为 `Recreate` 后，未来任何更新都将先终止旧 Pod、释放锁，再启动新 Pod，从根本上杜绝死锁。
```

---

## 남아 있는 제약과 질문

### 확인된 기술적 범위
- **KubeSphere 및 쿠버네티스 버전 적용성**: 해당 현상은 KubeSphere v3.3.x 및 v3.4.0 초기 버전, KubeKey 업그레이드 과정에서 공통으로 확인된 공식 이슈(GitHub #5855)와 100% 일치한다.
- **Recreate 전략의 수반 영향**: `Recreate` 전략 적용 시 업데이트 과정에서 구 Pod 종료부터 신규 Pod 기동 완료까지 약 5~15초 내외의 멀티클러스터 프록시 일시 단절이 수반된다. 그러나 이는 무한 데드락 상태로 방치되는 것보다 통제 가능한 정상적인 계획 작업 범위에 해당한다.

### 필요한 운영 및 후속 확인 사항
1. **멤버 클러스터 에이전트의 자동 재연결 여부**: Tower가 재기동된 후 멤버 클러스터의 `tower-agent`가 지수 백오프(Exponential Backoff) 알고리즘을 통해 30초 이내에 호스트로 터널을 정상 재수립하는지 모니터링해야 한다.
2. **KubeSphere 업스트림 패치 릴리즈 확인**: 최신 KubeSphere v3.4.1+ 또는 KSE 버전에서는 KubeKey 배포 템플릿 단계에서 `Recreate`가 기본 적용되어 있으므로 플랫폼 버전 업그레이드 계획 수립 시 반영 여부를 확인한다.

---

## 상세 자료 색인

| 지금 풀어야 할 질문 | 확인할 자료 | 확인할 내용 |
|---|---|---|
| 7월 9일 구 Pod가 실제 락을 쥐고 있는지 확인하려면? | `kubectl describe lease tower -n kubesphere-system` | `Holder Identity` 필드가 구 Pod의 이름과 일치하는지, `Renew Time`이 수 초 이내로 계속 갱신되는지 확인 |
| 신규 Pod가 왜 시작되지 못하는지 로그로 직접 확인하려면? | `kubectl logs deployment/tower -n kubesphere-system -c tower --tail=50` | `leaderelection.go`에서 출력하는 `lock is held by ... and has not yet expired` 로그 확인 |
| Tower Deployment의 현재 롤링 업데이트 전략을 확인하려면? | `kubectl get deployment tower -n kubesphere-system -o yaml` | `spec.strategy.type`이 `RollingUpdate`인지 확인 |
| 업스트림 커뮤니티의 동일 증상 논의 및 공인 해결책은? | GitHub Issue `kubesphere/kubesphere#5855` | KubeSphere 공식 메인테이너의 Recreate 전략 제안 및 scale 0->1 복구 권고 내용 확인 |
| Recreate 패치 적용 후 상태 변화를 검증하려면? | `kubectl rollout status deployment/tower -n kubesphere-system` | 구 Pod가 먼저 완전히 종료(Terminated)된 후 새 Pod가 `1/1 Ready`로 정상 전환되는지 확인 |
