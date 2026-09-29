# KubeSphere Tower 리더 선출 롤링 업데이트 교착 상태(Deadlock) 정리 및 현장 회신 가이드

## 1. 개요 및 인과 요약 (국문 정제본)

Tower는 Host와 Member 클러스터 간의 **관리 및 제어 통신을 중계하는 프록시 컴포넌트**입니다.

정상 상태의 기대값은 1개가 맞으나 현재 2개의 Pod가 공존하고 있는 상태입니다.  
원인은 초기 구축 또는 재설치 과정에서 설정 변경/재배포가 시도되면서, Deployment의 기본 배포 방식인 **롤링 업데이트(RollingUpdate: 새 Pod를 먼저 띄우고 정상 확인 후 기존 Pod를 삭제하는 방식)**가 트리거되었기 때문입니다.

하지만 배포가 완료되지 못한 이유는 Tower의 동작 메커니즘 때문입니다:

1. **단일 분산 락(Leader Lease) 필수**: Tower는 중복 실행 방지를 위해 쿠버네티스 분산 락(`coordination.k8s.io/v1 Lease`)을 쥐어야만 기동을 완료합니다.
2. **신규 Pod의 대기**: 기존 Pod가 여전히 살아있어 락을 계속 갱신(Renew)하고 있으므로, **새로 생성된 Pod는 락을 가져오지 못해 Readiness Probe를 통과하지 못하고 `0/1 Ready` 상태로 대기**하게 됩니다.
3. **상호 교착(Deadlock)**: Deployment Controller 입장에서는 신규 Pod가 `1/1 Ready`가 되지 않았으므로 기존 Pod를 종료할 수 없어, **서로 상대방의 상태 변화를 선행 조건으로 요구하는 교착 상태**에 빠져 2개가 유지된 것입니다.

### 조치 방안
이를 해결하려면 Deployment의 scale을 일시적으로 `0`으로 내려 기존 Pod와 락을 완전히 정리한 뒤, 다시 `1`로 올려주시면 됩니다.

```bash
kubectl scale deployment tower -n kubesphere-system --replicas=0
kubectl scale deployment tower -n kubesphere-system --replicas=1
```

> **영향도 안내**:  
> 이 과정에서 약 5~10초간 Host-Member 간 KubeSphere 웹 콘솔 관리 통신이 잠시 끊길 수 있으나, **Member 클러스터에서 실제로 실행 중인 비즈니스 애플리케이션의 서비스 트래픽에는 아무런 영향이 없습니다.**

---

## 2. 중국 담당자 전달용 가이드 (现场技术回复指南 - 中文版)

> Tower 是负责 Host 与 Member 集群之间**管理及控制面通信的反向代理组件**。
>
> 正如您所查到的，期望副本数是 1 个，但目前存在 2 个 Pod。
> 原因推测是 7 月份在初期搭建或重新部署过程中触发了更新，Deployment 按照默认的**滚动更新（RollingUpdate）机制执行了“先启动新 Pod，确认就绪后再销毁旧 Pod”的流程**。
>
> 之所以卡住未能完成更新，是因为 Tower 自身的工作机制：
> 
> 1. Tower 具备单实例保护机制，必须获取到 Kubernetes 的 Leader 锁（Lease）才能完成启动。
> 2. 由于旧 Pod 仍在运行并持续持有该锁，**新 Pod 无法夺取锁，导致其探针（Readiness Probe）无法通过，一直保持在 `0/1 Ready` 状态**。
> 3. Deployment 控制器检测到新 Pod 迟迟没有变为 `1/1 Ready`，因此不敢终止旧 Pod，从而形成了**相互等待的死锁（Deadlock）状态**，导致 2 个 Pod 一直并存。
>
> **【处理建议】**  
> 处理该问题时，请不要单独强杀 Pod，建议将 Deployment 缩容至 0 彻底释放锁资源后，再扩容恢复为 1 即可：
>
> ```bash
> kubectl scale deployment tower -n kubesphere-system --replicas=0
> kubectl scale deployment tower -n kubesphere-system --replicas=1
> ```
>
> 执行过程中会有大约 5~10 秒的时间导致 Host 与 Member 集群之间的 KubeSphere 控制台管理通信短暂中断，但**绝不会影响 Member 集群上正在运行的实际业务应用与服务流量**，请放心操作。
