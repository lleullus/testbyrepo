# [DKS-N] KubeSphere Tower 롤링 업데이트 교착 상태 원인 분석 및 조치 방안

작성자: 클라우드 인프라팀  
마지막 업데이트: 2026-09-17  
읽기 시간: 3분

## 1. 개요

KubeSphere 콘솔에서 kubesphere-system 네임스페이스의 host tower pod에 lock is held by tower-xxx and has not yet expired 경고가 발생하고, deployment의 replica 기대값은 1개이나 2개의 pod가 동시에 실행되어 1개가 Ready(0/1) 상태로 정체되는 현상이 접수되었다. 현장에서는 7월 9일 기동된 기존 pod를 비정상 인스턴스로 판단하여 삭제를 계획하였다.

본 문서는 tower pod가 2개로 유지되며 신규 pod 기동이 차단된 기술적 인과관계를 검증하고, 개별 pod 삭제 시의 통신 단절 위험을 분석하여, 서비스 영향 없이 교착 상태를 해소하고 재발을 방지하는 표준 조치 절차를 확정하기 위해 작성한다. 검토 범위는 Host 클러스터의 tower 배포 구성과 Member 클러스터 간 터널 연결성이다.

## 2. 확인사항

### Tower 컴포넌트의 역할 및 통신 분리 구조

Tower는 Host 클러스터와 사설망 또는 NAT 환경의 Member 클러스터 간에 SSH-over-HTTP(Chisel) 리버스 터널을 중계하는 관리 및 제어면 프록시 컴포넌트다.

Host 콘솔의 Member 클러스터 상태 조회, 리소스 생성 및 제어 요청만 Tower 터널을 경유한다. 외부 사용자의 서비스 인그레스 트래픽, Calico CNI를 통한 파드 간 통신, NetApp Trident를 통한 PV 데이터 I/O는 Tower를 거치지 않고 독자 경로로 처리된다. 따라서 Tower 인스턴스 정지 시에도 Member 클러스터에서 실행 중인 비즈니스 애플리케이션 트래픽은 단절되지 않는다.

### 2개 Pod 공존 및 교착 상태 형성 원인

Tower deployment의 배포 전략과 분산 락 메커니즘 간의 상호 의존성으로 인해 교착 상태가 형성되었다.

tower deployment의 spec.strategy.type은 RollingUpdate이며 maxSurge는 25퍼센트다. replicas가 1일 때 maxSurge 계산은 올림 처리되어 1이 되므로, 업데이트 시 구 pod를 유지한 채 신규 pod가 먼저 생성되어 2개의 pod가 공존한다.

Tower는 다중 인스턴스의 터널 세션 충돌을 방지하기 위해 coordination.k8s.io/v1 Lease 리소스(kubesphere-system/tower)를 통한 분산 락(Leader Election)을 사용한다. 신규 pod는 리더 락을 획득해야만 프로세스를 초기화하고 Readiness Probe를 통과하여 1/1 Ready 상태가 된다.

그러나 7월 9일 기동된 구 pod는 정상 작동 중이며 15초 유효 기간의 Lease를 2초 주기로 지속 갱신(Renew)하고 있다. 신규 pod는 구 pod가 락을 유지하고 있어 lock is held by... and has not yet expired 경고를 출력하며 0/1 Ready 상태로 대기한다.

Deployment Controller는 maxUnavailable 제약(replicas 1일 때 0)으로 인해 신규 pod가 1/1 Ready가 되지 않으면 구 pod를 종료하지 않는다. 결과적으로 구 pod 종료 조건과 신규 pod Ready 조건이 서로를 선행 조건으로 요구하여 무한 대치 상태가 유지된다.

### 개별 Pod 조치 시의 운영 리스크

현장 계획과 같이 특정 pod만을 단독 삭제할 경우 다음과 같은 문제가 발생한다.

- 구 pod 강제 삭제 시 위험: 7월 9일 기동된 구 pod는 비정상이 아니라 실시간 터널 세션을 유지하고 있는 유일한 활성 리더다. SIGKILL 등으로 강제 삭제되면 Lease 락이 즉시 해제되지 못하고 leaseDurationSeconds(15초) 만료 시까지 유지되어, 최대 수십 초 동안 Host-Member 간 모든 제어 통신이 단절되고 웹 콘솔 상에서 Member 클러스터가 오프라인으로 전환된다.
- 신규 pod 단독 삭제 시 문제: Deployment Controller가 즉시 동일한 대체 pod를 재생성하여 동일한 락 경합과 경고가 영구 반복된다.

## 3. 조치방안

기본안으로 maintenance window를 별도 지정하지 않고 저부하 시간대에 deployment replica를 일시적으로 0으로 축소하여 잔여 프로세스와 Lease 락을 완전히 정리한 후, 1로 복구하여 신규 pod를 단독 기동시키는 방안을 확정한다. 아울러 향후 재발을 원천 차단하기 위해 배포 전략을 Recreate로 영구 패치한다.

### 실행 절차

사전 확인: Host 클러스터에서 현재 실행 중인 tower pod 2개의 상태와 Lease 소유자를 확인한다.
```bash
kubectl get pods -n kubesphere-system -l app=tower
kubectl get lease tower -n kubesphere-system -o yaml
```

Scale 0 축소: replica를 0으로 설정하여 구 pod를 정상 종료(Graceful Termination)시키고 Lease 락을 반환하도록 유도한다.
```bash
kubectl scale deployment tower -n kubesphere-system --replicas=0
```

완전 종료 검증: 모든 tower pod가 Terminated 완료되었는지 확인한다. 노드 장애 등으로 찌꺼기 pod가 남지 않고 0개가 되었음을 확인한다.
```bash
kubectl get pods -n kubesphere-system -l app=tower
```

잔여 Lease 정리: 만약 pod가 0개인데도 Lease holderIdentity가 남아있다면 Lease를 수동 삭제한다.
```bash
kubectl delete lease tower -n kubesphere-system --ignore-not-found
```

Scale 1 복구: replica를 1로 증가시켜 신규 pod가 경합 없이 단독으로 Lease를 취득하고 1/1 Ready 상태에 도달하도록 한다.
```bash
kubectl scale deployment tower -n kubesphere-system --replicas=1
```

배포 전략 Recreate 영구 전환: 향후 설정 변경이나 버전 업그레이드 시 롤링 업데이트 교착이 발생하지 않도록 deployment spec.strategy를 Recreate로 패치한다.
```bash
kubectl patch deployment tower -n kubesphere-system -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}'
```

### 판정 및 검증 기준

- 정상 기동 확인: tower pod 1개가 단독 생성되어 수 초 이내에 Ready(1/1), Status(Running)으로 전이되는지 확인한다.
- 리더 락 취득 확인: describe lease tower 실행 결과 Holder Identity가 신규 pod명과 일치하고 Renew Time이 지속 갱신되는지 확인한다.
- Member 클러스터 터널 복구 확인: Member 클러스터의 tower-agent pod 로그를 확인하여 Host와의 WebSocket 터널이 재연결되었는지 검증한다. Member 클러스터 tower-agent는 지수 백오프 로직에 따라 별도 수동 작업 없이 30초 이내에 자동 재연결된다.
- 콘솔 상태 검증: KubeSphere 웹 콘솔의 클러스터 관리 메뉴에서 Member 클러스터 상태가 정상 초록색으로 표출되는지 확인한다.

### 중단 및 복구 조건

- 중단 조건: scale 0 실행 후 기존 pod가 Terminating 상태에서 60초 이상 정체되거나, scale 1 실행 후 신규 pod가 ImagePullBackOff, CrashLoopBackOff 등 락 외의 런타임 오류로 기동 실패하는 경우 작업을 일시 중단한다.
- 복구 절차: 신규 pod 장애 발생 시 직전 정상 이미지 태그 및 환경 변수 상태를 확인하고, 이전 ReplicaSet으로 롤백을 수행한다.
```bash
kubectl rollout undo deployment tower -n kubesphere-system
```
