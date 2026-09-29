---
title: NFS PVC Mount 실패 - ONTAP 측 확인 요청
date: 2026-07-03
status: review
case_status: investigating
tags:
  - review
  - kubesphere
  - nfs
  - pvc
  - trident
  - ontap
  - mount-fail
  - exit-status-32
  - multi-nic
  - vserver-root-policy
  - check-access
  - source-ip
  - scs
  - cluster-setup
aliases:
  - Trident NFS PVC Mount 실패
  - ONTAP Export Policy 확인 요청
  - NIC 분리 환경 NFS mount
  - SCS 환경 NFS 검토
related:
  - "[[30. 구축 및 전환/공통 구축/04. Install Storage Components|04. Install Storage Components]]"
  - "[[20. 환경 준비/환경 준비 및 의존성|환경 준비 및 의존성]]"
doc_type: guide
scope: "Xi'an 전환 운영 가이드"
updated: "2026-07-19"
---

# NFS PVC Mount 실패 - ONTAP 측 확인 요청

## 1. 현상 요약

Kubernetes 환경에서 NetApp Trident 기반 NFS PVC를 생성해 보면, **PVC Bound와 Trident backend volume 생성까지는 정상적으로 진행**됩니다.

문제는 해당 PVC를 사용하는 Pod가 기동될 때, NFS mount 단계에서 발생합니다.

현재 확인된 에러는 아래와 같습니다.

```text
error mounting NFS volume
<data-lif-address>:/<nfs-export-path> on mountpoint ...
exit status 32
```

현재는 **스토리지 볼륨/qtree 생성과 PVC 바인딩까지는 끝난 상태입니다. 다만 Pod가 스케줄된 노드에서 Data LIF의 NFS export path를 mount하지 못하고 있습니다.**

---

## 2. Kubernetes / Trident 측 확인 사항

지금까지 Kubernetes와 Trident 쪽에서 확인한 내용은 아래와 같습니다.

### 2.1 PVC 상태

PVC는 정상적으로 `Bound` 상태입니다.

```bash
kubectl get pvc -n <namespace>
```

확인 결과 대상 PVC는 정상 `Bound` 상태입니다.

### 2.2 Trident backend 상태

Trident backend를 조회해 보면, 대상 backend에 PVC volume이 생성된 것이 확인됩니다.

```bash
tridentctl get backend -n trident
```

backend의 `VOLUMES` 값도 늘어나 있어, **Trident가 ONTAP에 volume/qtree를 만드는 단계까지는 성공한 것**으로 보고 있습니다.

### 2.3 autoExportCIDRs 설정 확인

Trident backend YAML 기준으로 `autoExportCIDRs`에 대상 노드 IP가 정상적으로 들어가 있는 것도 확인했습니다.

```bash
tridentctl get backend <backend-name> -n trident -o yaml
```

### 2.4 Trident node IP 확인

`tridentctl get nodes -n trident -o yaml` 결과에 표시되는 노드 IP와 `autoExportCIDRs`에 등록된 IP도 서로 일치했습니다.

```bash
tridentctl get nodes -n trident -o yaml
```

여기까지 확인한 내용으로 보면 **Trident backend 설정에서 autoExportCIDRs 오입력이나 노드 IP 불일치 가능성은 낮습니다.**

---

## 3. 현재 의심 지점

> [!warning] 의심 흐름
> 현재 증상은 아래 흐름으로 보입니다.

```text
PVC 생성 요청
→ Trident backend에서 volume/qtree 생성 성공
→ PVC Bound 성공
→ Pod 스케줄링 성공
→ kubelet이 NFS mount 시도
→ ONTAP Data LIF:/export-path mount 실패
→ exit status 32 발생
```

Kubernetes PVC provisioning 단계에서 막힌 것으로 보이지는 않습니다. **ONTAP NFS export 접근 허용 정책이나 Data LIF 접근 경로 쪽 점검**이 필요해 보입니다.

특히 아래 가능성을 먼저 확인 부탁드립니다.

---

## 4. ONTAP 측 확인 요청 사항

### 4.1 Trident export policy rule 반영 여부 확인

Trident backend에는 `autoExportCIDRs`가 정상적으로 들어가 있습니다. 다만 실제 ONTAP export policy rule에 Pod가 올라간 Kubernetes node IP가 `clientmatch`로 반영됐는지는 별도로 확인이 필요합니다.

**확인 요청 항목**

```text
- 대상 SVM의 export policy rule 목록
- Trident가 생성한 export policy에 대상 node IP가 clientmatch로 존재하는지
- rorule / rwrule / superuser / protocol 값이 NFS mount 가능하게 설정되어 있는지
```

**예상 확인 명령**

```bash
vserver export-policy rule show -vserver <svm>
```

또는 Trident policy 기준:

```bash
vserver export-policy rule show -vserver <svm> -policyname <trident-policy-name>
```

특정 노드 IP 기준 확인:

```bash
vserver export-policy rule show -vserver <svm> | grep <node-ip>
```

### 4.2 qtree / parent FlexVol export policy 확인

현재 StorageClass는 qtree 기반 NFS backend로 보입니다. `ontap-nas-economy` 계열일 가능성이 있습니다.

실제 PVC가 qtree로 생성되는 구조라면, 아래 export policy 관계도 함께 봐야 합니다.

```text
- qtree export policy에 node IP가 허용되어 있는지
- parent FlexVol export policy에도 필요한 rule이 반영되어 있는지
- qtree path와 실제 export path가 일치하는지
```

**확인 요청 항목**

```bash
volume qtree show -vserver <svm>
volume show -vserver <svm> -fields policy,junction-path
vserver export-policy rule show -vserver <svm>
```

### 4.3 SVM root junction export policy 확인

NFS mount 시 실제 export path에 도달하기 전에 SVM root junction 또는 상위 junction path를 거치게 되므로, root junction export policy에서도 Kubernetes node IP가 허용되는지 확인 부탁드립니다.

> [!important] Oracle Browser 검수 보완
> Trident의 `autoExportPolicy: true`는 **Trident가 생성한 volume/qtree의 export policy만** 자동 관리합니다. SVM root junction의 export policy는 자동 관리 대상이 아닙니다. 따라서 `autoExportCIDRs`만 잘 잡아도 root junction policy가 `10.0.0.0/24`를 허용 안 하면 mount fail이 납니다. 이 부분이 mount fail의 은밀한 원인 중 하나입니다.

**확인 요청 항목**

```text
- SVM root volume의 junction-path가 `/`인지
- root volume에 적용된 export policy
- 해당 export policy에 Kubernetes node IP 또는 node subnet이 허용되어 있는지
```

**예상 확인 명령**

```bash
volume show -vserver <svm> -junction-path / -fields policy
vserver export-policy rule show -vserver <svm> -policyname <root-policy-name>
```

### 4.4 Data LIF 접근 및 source IP 확인

Trident가 인식한 node IP와 ONTAP이 실제 NFS client로 인식하는 source IP가 다르면, export policy rule이 맞아도 mount가 실패할 수 있습니다.

> [!note] NIC 2개 환경 (현재 구성)
> K8s 노드에 NIC가 2개 있는 경우, **NFS mount 트래픽은 data LIF와 통신하는 NIC(=storage NIC)로** 나갑니다. 이때 source IP는 kernel routing에 따라 storage NIC의 IP가 됩니다. management LIF와 통신하는 NIC의 IP는 NFS export policy 검사 대상이 아닙니다.

**확인 요청 항목**

```text
- 대상 node에서 Data LIF로 접근 시 ONTAP이 인식하는 client source IP
- NAT 또는 storage망 별도 source IP 변환 여부
- Data LIF 기준 NFS 2049 접근 가능 여부
```

Kubernetes node 측에서는 아래 명령으로 source IP를 확인할 예정입니다.

```bash
ip route get <data-lif-ip>
```

여기서 확인되는 `src` IP가 ONTAP export policy의 `clientmatch` IP와 일치해야 합니다.

> [!tip] 가장 빠른 1차 진단
> ONTAP은 `vserver export-policy check-access`로 client IP가 path에 접근 가능한지 직접 평가해볼 수 있습니다. ip route + check-access 조합이 가장 확실한 진단 경로입니다.
>
> ```bash
> vserver export-policy check-access \
>   -vserver <svm> \
>   -client-ip <NODE_NFS_SOURCE_IP> \
>   -volume <volume_or_parent_volume> \
>   -authentication-method sys \
>   -protocol nfs4 \
>   -access-type read-write
> ```

---

## 5. 요청 결론

> [!summary] 현재까지 확인된 정상 항목
> - PVC Bound 성공
> - Trident backend volume 생성 확인
> - backend YAML 내 `autoExportCIDRs` 설정 확인
> - `tridentctl get nodes` 기준 node IP와 `autoExportCIDRs` IP 일치 확인

ONTAP 측에서는 아래 항목을 중점적으로 확인해 주시면 됩니다.

1. Trident export policy에 대상 Kubernetes node IP가 실제 `clientmatch`로 반영되어 있는지
2. qtree 및 parent FlexVol export policy가 정상 구성되어 있는지
3. SVM root junction export policy에서 Kubernetes node IP/subnet 접근이 허용되어 있는지
4. ONTAP이 실제로 인식하는 NFS client source IP가 Trident/Kubernetes node IP와 같은지
5. Data LIF 기준 NFS 접근 또는 방화벽/라우팅 차단 여부가 없는지

> [!important] 결론
> 현재 증상만 보면 PVC provisioning 이슈라기보다는 **ONTAP export policy rule 반영 문제, NFS client 접근 허용 정책 문제 가능성이 높아 보입니다. ONTAP 측 확인을 요청드립니다.**

---

## 6. 추가 검토 사항 (Oracle Browser 검수 반영)

초기 검토 이후 진행한 진단과 Oracle Browser 검수에서 추가로 확인한 내용입니다.

### 6.1 NIC 2개 환경 — management LIF vs data LIF

현재 K8s 노드에는 NIC가 2개 있습니다.

| NIC | 대역 예시 | 통신 대상 LIF | 트래픽 종류 | export policy 검사 |
|---|---|---|---|---|
| NIC A | `192.168.1.x` | SVM management LIF | HTTPS 443 (Trident REST API) | ❌ 안 함 |
| NIC B | `10.0.0.x` | SVM data LIF | NFS TCP 2049 | ✅ 함 |

**결론**: NFS mount 트래픽은 **data LIF와 통신하는 NIC B**로 나갑니다. source IP는 kernel routing에 따라 storage NIC의 IP가 됩니다.

> [!warning] 흔한 오해
> "ONTAP에 트래픽이 가니까 management NIC IP도 등록해야 하지 않나?" — **아닙니다.** management LIF는 Trident의 ONTAP API 호출용(HTTPS 443)이며 export policy 검사 대상이 아닙니다. export policy는 NFS 접근에만 적용됩니다.

### 6.2 Trident `autoExportCIDRs` 등록 대상

여기에는 **storage NIC CIDR만** 등록합니다.

```yaml
spec:
  managementLIF: 192.168.1.<svm-mgmt>
  dataLIF: 10.0.0.<svm-data>
  autoExportPolicy: true
  autoExportCIDRs:
    - 10.0.0.0/24      # <- storage NIC 대역만
  svm: <svm-name>
```

management CIDR(`192.168.1.0/24`)을 `autoExportCIDRs`에 **넣지 말아야 하는** 이유는 다음과 같습니다.

1. NFS 접근면이 불필요하게 넓어져 storage network 분리가 약해짐
2. routing 오류가 있어도 mount가 성공해버려서 잘못된 경로가 고착될 수 있음
3. rule 관리/IP 재사용 리스크 영역이 불필요하게 늘어남

### 6.3 K8s node IP discovery 함정

Trident는 K8s Node object의 InternalIP를 보고 `autoExportCIDRs`로 필터링해 rule을 만듭니다. 이 때문에:

```bash
# 1) K8s가 storage NIC IP를 InternalIP로 광고하고 있는지
kubectl get nodes -o wide
kubectl get node <node-name> -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}'
```

storage NIC IP(`10.0.0.x`)가 InternalIP에 안 보이면, `autoExportCIDRs: ["10.0.0.0/24"]`을 넣어도 **rule이 비거나 잘못된 IP로 만들어집니다.** 이 경우 해결책은 두 가지:

- kubelet에 `--node-ip=<storage-nic-ip>` 플래그로 storage NIC IP를 InternalIP로 등록
- 또는 `autoExportPolicy: false`로 두고 ONTAP에서 export policy를 수동 생성

### 6.4 Trident node detection 갱신 (NIC 추가/변경 시)

`tridentctl get node`가 새 NIC를 잡지 못하면, 데몬셋을 rollout restart 해서 갱신합니다.

```bash
# 23.04+
kubectl -n trident rollout restart ds trident-csi-node
# 구버전
kubectl -n trident rollout restart ds trident-node-linux

# 완료 대기
kubectl -n trident rollout status ds trident-csi-node

# 확인
tridentctl get node -n trident -o yaml
```

여기에 storage NIC IP가 새로 보이면 정상입니다. 그 후 Trident가 backend reconcile을 한 번 돌면서 export policy rule을 갱신합니다.

### 6.5 SVM root junction export policy (가장 중요한 보완)

> [!important]
> Trident의 `autoExportPolicy: true`는 **Trident가 생성한 volume/qtree의 export policy만** 자동 관리합니다. **SVM root junction의 export policy는 자동 관리 대상이 아닙니다.** 따라서 `autoExportCIDRs`만 잘 잡아도 root junction policy가 `10.0.0.0/24`를 허용 안 하면 mount fail이 납니다. 이 부분이 mount fail의 은밀한 원인 중 하나입니다.

확인 명령 (§4.3에 이미 포함, 별도 강조):

```bash
volume show -vserver <svm> -junction-path / -fields policy
vserver export-policy rule show -vserver <svm> -policyname <root-policy-name>
```

> [!info] 관련 셋업 문서
> - [[30. 구축 및 전환/공통 구축/04. Install Storage Components|04. Install Storage Components]] — Trident 설치/구성 절차 (export policy 자동 설정 가정)
> - [[20. 환경 준비/환경 준비 및 의존성|SCS 환경 협의 및 요청 사항]] — SCS 환경의 `ontap-nas-economy` backend 및 vServer 정보 (QOS policy, storageClass 명은 요청중)
> - [[30. 구축 및 전환/구축 마스터 Runbook|00. DKS Cluster Setup Guide]] — SCS 환경은 HQ와 다를 수 있음 (Step 0~2)
>
> 이 검토의 결론이 위 셋업 문서의 export policy 사전 설정 가이드에 피드백으로 반영되어야 함.

### 6.6 엣지 케이스

- **NAT 비권장**: Trident 문서에서 dynamic export policy와 NAT는 같이 쓰지 말라고 명시. NAT 환경에서는 storage controller가 실제 host IP가 아니라 NAT frontend 주소를 봄
- **`dataLIF` 명시 권장**: 미명시 시 Trident가 SVM에서 자동 선택하는데, 의도와 다를 수 있음
- **routing source IP 선택 오류**: 어떤 이유로 kernel이 storage LIF로 갈 때도 management NIC IP를 source로 고르면 clientmatch 미스. 해결: routing 수정 (management CIDR 추가는 정답 아님)

### 6.7 Oracle 검수 종합

NetApp 공식 문서 기준으로 다음이 확인되었습니다:

1. `autoExportCIDRs`는 storage NIC CIDR만 등록이 맞음
2. management LIF 트래픽(HTTPS 443)은 NFS export policy 검사 대상이 아님
3. SVM root junction policy는 manual 사전 설정 필요 (Trident 자동 관리 X)
4. `vserver export-policy check-access`가 공식 1차 진단 명령어

### 6.8 4.1 vs 4.2 우선순위 — 환경별 차이

| 환경 | 우선 확인 |
|---|---|
| **초기 구축 / 첫 시도** (현재) | 4.1 — policy rule 자체 부재/오류 가능성 ↑ |
| 운영 중 특정 PVC만 fail | 4.2 — qtree 상속 문제 가능성 ↑ |
| 2 NIC + routing 분리 환경 | 4.4 — source IP가 잘못된 NIC에서 나가는지 |
| NAS-economy + qtree 사용 | 4.2 + 4.3 (root policy) 동시 확인 |

현재는 초기 구축 단계에서 첫 시도 중이므로, **4.1을 먼저 보고 그다음 4.4 (source IP), 이어서 4.3 (root policy), 마지막으로 4.2 (qtree)** 순서로 확인하는 것이 효율적입니다.

## 7. 진행 상태

> [!info] 액션 트래킹
> - **2026-07-03**: ONTAP 측에 `qtree / parent FlexVol / SVM root junction` 각각의 export policy `clientmatch` 적용 여부 점검 요청 보냄. 응답 대기 중.
> - 응답 수신 후 `vserver export-policy check-access`로 최종 검증 예정.
