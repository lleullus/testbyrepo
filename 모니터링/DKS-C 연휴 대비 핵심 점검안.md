# [DKS-C] 연휴 대비 핵심 점검안 (실무 개정판)
작성자: 미기재  
마지막 업데이트: 2026-09-16  
읽기 시간: 7분

## 1. 개요

DKS-C Daily 보고서는 이미 다음 기본 항목을 매일 점검하고 있다.

- 5대 인프라 클러스터와 39개 사용자 클러스터의 Status, Node 가용률, System/Core Pod Restart
- **노드 자원(Node CPU/Memory/Block/NAS)** 및 클러스터별 기본 PVC 사용률
- API Server, ETCD 기본 헬스, Alert 수신 상태
- VCFA Region/Zone 및 Storage Policy 현재 사용량/할당률
- Platform 인증서 및 `console-token` 만료 D-day
- `logs-hub`, `metric-hub`, `Console-db`, `Keycloak-db`, `Apisix-etcd` 백업 실행 결과

연휴 점검에서는 기본 항목을 요약해서 뭉뚱그리지 않고, **5대 인프라 클러스터와 39개 사용자 게스트 클러스터 전체(총 44개 클러스터)의 노드 자원 상태를 전수 표기**하여 일일 모니터링 기준선을 명확히 계승한다.

연휴 점검에서 추가해야 할 핵심은 이론적인 etcd 쿼터 분석이 아니라, **"운영 컨플루언스에서 실제로 발생했던 VCF/Supervisor 제어 평면 결함(Storage Quota 부족으로 인한 노드 프로비저닝 Reject)이 무인 연휴 기간에 재발하여 클러스터 복구를 전면 락(Lock)시키는 치명적 지점"**을 사전에 차단하는 것이다.

---

## 2. 확인사항

### 2.1 1순위: Storage Policy Quota 및 복구 락(Lock) 검증의 당위성

운영 컨플루언스에 실제 기록된 장애 사례와 결함 메커니즘은 다음과 같다.

#### 1) 실제 발생 장애 이력 (컨플루언스 발췌)
- **컨트롤 플레인 프로비저닝 거부**:
  ```text
  failed to create or update VirtualMachine: admission webhook 
  "quota-create.validating.virtualmachine.v1alpha4.vmoperator.vmware.com" denied the request: 
  Operation denied, failed to validate against storage quota for resource getting-started-cluster-9cwz8-gmbvn, 
  namespace getting-started-ns-vdlrp with err Operation denied due to insufficient storage quota 
  for storage policy resource getting-started-cluster-9cwz8-gmbvn
  ```
- **머신 디플로이먼트 워커 노드 생성 거부**:
  ```text
  VirtualMachineProvisioned: failed to create or update VirtualMachine: admission webhook 
  "quota-create.validating.virtualmachine.v1alpha4.vmoperator.vmware.com" denied the request: 
  Operation denied due to insufficient storage quota for storage policy resource 
  kubernetes-cluster-5v4p-kubernetes-cluster-5v4p-np-qqcx-rmj7q48
  ```
- **원인 및 영향**:
  - Storage Quota가 소진되거나 vCenter/CCI 간 Quota 집계에 불일치가 발생하면, VM Operator 웹훅이 VirtualMachine 리소스 생성을 강제 Reject함.
  - 연휴 동안 단 1대의 Worker Node 또는 Control Plane Node에 하드웨어/OS 장애가 발생해도, **CAPI가 대체할 신규 VM(OS 디스크)을 띄우지 못해 노드 자동 복구가 영구 정체(Waiting for Cluster control plane to be initialized)**됨.

#### 2) 연휴 검증 산식
`vks-pf-storage-policy`의 Daily 표기 `87~88%`는 가상 Provisioned 비율이며, 실제 사용량은 `23.46 / 60 TB (약 39%)`이다. 연휴 점검에서는 다음 산식으로 **노드 장애 복구 여유(Reserve)**를 반드시 확보해야 한다.

```text
예상 종료 quota 사용량 = 현재 quota 사용량 + 일평균 증가량 × (연휴 일수 + 2일 buffer)
복구 후 안전 마진 = Quota Limit - 예상 종료 사용량 - (가장 큰 노드 N+1 복구 OS 디스크 용량)
```

---

### 2.2 연휴 진입 차단 Gate (No-Go Gate) 실무 근거

1. **`console-token` 만료 (현재 기준 D-5)**:
   - 만료 시 콘솔 API 및 VictoriaMetrics/OpenSearch 헬스체크가 401로 실패하여 무인 관제 마비 &rarr; 연휴 전 신규 토큰 발급 및 Secret 교체, 실제 헬스체크 2xx 응답 확인 필수.
2. **Supervisor CA 및 Runtime Extension 웹훅 인증서 만료 차단**:
   - 컨플루언스 실장애 이력: `CA 인증서가 만료되어 슈퍼바이저 클러스터에서 PVC 또는 VolumeSnapshot 작업이 실패함 (tls x509: certificate signed by unknown authority)`
   - 만료일이 `연휴 종료 + 30일` 이상 잔여하는지 사전 확인.
3. **VKS RWX Retain 볼륨으로 인한 Unbound PVC 누수 확인**:
   - 컨플루언스 실장애 이력: VKS에서 볼륨 삭제 시 Supervisor Retain 정책으로 인해 `WARNING: Unbound PVC(s) detected!` 상태로 스토리지 쿼터를 잠식하는 현상 사전 정리.

---

## 3. 최종 점검 틀 (전수 클러스터 표기 완성형)

# [DKS-C] `<연휴명>` 연휴 대비 사전 점검 결과

| 항목 | 값 |
|---|---|
| 연휴 기간 | `<시작일>` ~ `<종료일>` |
| 점검 기준 시각 | `<YYYY-MM-DD HH:mm KST>` |
| 차용한 Daily 보고서 | `<Daily 보고서 링크 / 일자>` |
| 점검자 / 검토자 | `<담당자 성명>` / `<파트장 성명>` |
| 최종 판정 | `[ ] Go    [ ] Conditional Go    [ ] No-Go` |

---

### 1) Daily 기본 항목 차용: 5대 인프라 클러스터 전수 점검표

| No | Cluster Name | 역할 | Node 가용률 | System Pod Restart | Core Node CPU 사용률 | Core Node Mem 사용률 | API Server | ETCD | Alert | 연휴 판정 |
|---|---|---|---|---|---|---|---|---|---|:---:|
| 1 | `prd-dksc-ic01-khm` | 콘솔 (Portal) | 8/8 (100%) | 0 | Good | Good | Good | Good | Good | **Pass** |
| 2 | `prd-dksg-ic01-khm` | API 게이트웨이 (APISIX) | 8/8 (100%) | 0 | Good | Good | Good | Good | Good | **Pass** |
| 3 | `prd-dksl-ic01-khm` | 로깅 (OpenSearch) | 8/8 (100%) | 0 | Good | Good | Good | Good | Good | **Pass** |
| 4 | `prd-dksm-ic01-khm` | 모니터링 (VictoriaMetrics) | 8/8 (100%) | 0 | Good | Good | Good | Good | Good | **Pass** |
| 5 | `prd-dkso-ic01-khm` | DevOps (CI/CD) | 13/13 (100%) | 0 | Good | Good | Good | Good | Good | **Pass** |

---

### 2) Daily 기본 항목 차용: 39개 사용자 게스트 클러스터 전수 점검표 (노드 자원 및 스토리지)

| No | Cluster Name | Worker Node (보유/정상) | Node CPU (보유 Core / 최대 사용률) | Node Memory (보유 GiB / 최대 사용률) | Node Block Storage (보유 GiB / 최대 사용률) | Node NAS (보유 GiB / 최대 사용률) | 연휴 판정 | 비고 |
|---|---|---|---|---|---|---|:---:|---|
| 1 | `amhs-sim-analysis-pr` | 3개 / 3개 | 24 / 1.2% | 96 / 3.7% | 0 / 0.0% | 0 / 0.0% | **Pass** | 정상 |
| 2 | `appdevops` | 3개 / 3개 | 96 / 0.9% | 384 / 3.8% | 29 / 41.3% | 321 / 2.8% | **Pass** | 정상 |
| 3 | `artds2dprov` | 6개 / 6개 | 96 / 0.9% | 384 / 5.1% | 0 / 0.0% | 490 / 0.6% | **Pass** | 정상 |
| 4 | `bia-dev` | 4개 / 4개 | 32 / 23.0% | 128 / 30.3% | 381 / 4.7% | 352 / 3.5% | **Pass** | 정상 |
| 5 | `bia-prd` | 6개 / 6개 | 48 / 15.1% | 192 / 16.8% | 402 / 2.1% | 274 / 0.8% | **Pass** | 정상 |
| 6 | `bia-stg` | 4개 / 4개 | 32 / 8.0% | 128 / 16.8% | 402 / 1.9% | 264 / 1.1% | **Pass** | 정상 |
| 7 | `cae-pcloud-prod` | 3개 / 3개 | 12 / 2.5% | 24 / 17.8% | 0 / 0.0% | 0 / 0.0% | **Pass** | 정상 |
| 8 | `canvas` | 3개 / 3개 | 24 / 1.4% | 192 / 3.1% | 0 / 0.0% | 15 / 64.2% | **Pass** | NAS 주의 관찰 |
| 9 | `cdep0` | 3개 / 3개 | 48 / 0.7% | 384 / 1.4% | 0 / 0.0% | 223 / 1.8% | **Pass** | 정상 |
| 10 | `claude-cowork` | 3개 / 3개 | 48 / 0.6% | 96 / 3.6% | 0 / 0.0% | 0 / 0.0% | **Pass** | 신규 생성 클러스터 |
| 11 | `dbrgdev01` | 3개 / 3개 | 24 / 1.6% | 96 / 6.5% | 365 / 8.0% | 0 / 0.0% | **Pass** | 정상 |
| 12 | `diff-application-01` | 4개 / 4개 | 16 / 4.2% | 32 / 23.0% | 0 / 0.0% | 25 / 40.0% | **Pass** | 정상 |
| 13 | `dks-c-aisw-art-ace` | 4개 / 4개 | 16 / 5.7% | 32 / 32.4% | 0 / 0.0% | 35 / 8.4% | **Pass** | 정상 |
| 14 | `dks-magician-ax` | 3개 / 3개 | 24 / 4.1% | 48 / 13.2% | 422 / 4.7% | 5 / 0.0% | **Pass** | 정상 |
| 15 | `dsportal-dev` | 12개 / 12개 | 72 / 8.7% | 192 / 17.8% | 0 / 0.0% | 191 / 7.0% | **Pass** | 정상 |
| 16 | `dsportal-prd` | 15개 / 15개 | 96 / 7.3% | 336 / 13.4% | 0 / 0.0% | 360 / 5.3% | **Pass** | 정상 |
| 17 | `dsportal-stg` | 15개 / 15개 | 96 / 5.3% | 288 / 11.9% | 0 / 0.0% | 193 / 3.0% | **Pass** | 정상 |
| 18 | `ears-tsp` | 4개 / 4개 | 32 / 1.3% | 64 / 19.8% | 90 / 0.2% | 0 / 0.0% | **Pass** | 정상 |
| 19 | `espec-devops` | 3개 / 3개 | 24 / 1.0% | 48 / 7.3% | 10 / 0.0% | 10 / 0.0% | **Pass** | 정상 |
| 20 | `fmcs-datapipeline` | 3개 / 3개 | 12 / 2.8% | 48 / 12.5% | 0 / 0.0% | 600 / 0.1% | **Pass** | 정상 |
| 21 | `gsre-servicemap-dev` | 4개 / 4개 | 16 / 12.4% | 64 / 20.6% | 5 / 1.2% | 35 / 29.9% | **Pass** | 정상 |
| 22 | `gsre-servicemap-prd` | 3개 / 3개 | 96 / 0.4% | 192 / 2.6% | 0 / 0.0% | 0 / 0.0% | **Pass** | 정상 |
| 23 | `incluster-0722-dev` | 4개 / 4개 | 32 / 1.0% | 64 / 7.1% | 2 / 1.2% | 0 / 0.0% | **Pass** | 정상 |
| 24 | `oafbrx` | 12개 / 12개 | 304 / 1.0% | 1.19 TiB / 9.7% | 0 / 0.0% | 784 / 1.2% | **Pass** | 정상 |
| 25 | `pems` | 3개 / 3개 | 24 / 10.8% | 48 / 31.1% | 0 / 0.0% | 0 / 10.0% | **Pass** | 정상 |
| 26 | `peoplein360-dev` | 15개 / 15개 | 60 / 9.9% | 168 / 27.5% | 16 / 0.0% | 283 / 8.3% | **Pass** | 정상 |
| 27 | `peoplein360-prd` | 21개 / 21개 | 132 / 1.3% | 528 / 5.3% | 12 / 0.0% | 143 / 6.2% | **Pass** | 정상 |
| 28 | `peoplein360-stg` | 15개 / 15개 | 60 / 2.0% | 168 / 13.6% | 12 / 0.0% | 88 / 12.6% | **Pass** | 정상 |
| 29 | `ra-server-monitoring` | 5개 / 5개 | 20 / 1.8% | 40 / 10.8% | 8 / 0.0% | 2 / 0.1% | **Pass** | 노드 스케일 조정 확인 |
| 30 | `rsip-cluster` | 6개 / 6개 | 96 / 0.6% | 192 / 3.9% | 0 / 0.0% | 11 / 33.5% | **Pass** | 정상 |
| 31 | `sense-cluster` | 3개 / 3개 | 24 / 1.2% | 48 / 10.5% | 0 / 0.0% | 59 / 0.0% | **Pass** | 정상 |
| 32 | `smap-dev-cluster` | 5개 / 5개 | 160 / 1.5% | 640 / 5.7% | 410 / 8.6% | 334 / 3.8% | **Pass** | 정상 |
| 33 | `smap-mgmt-cluster` | 3개 / 3개 | 48 / 1.2% | 192 / 4.6% | 0 / 0.0% | 32 / 25.1% | **Pass** | 정상 |
| 34 | `smap-prod-cluster` | 5개 / 5개 | 160 / 1.9% | 640 / 3.9% | 360 / 3.9% | 303 / 5.1% | **Pass** | 정상 |
| 35 | `smap-stg-cluster` | 3개 / 3개 | 48 / 1.6% | 192 / 7.3% | 315 / 11.7% | 264 / 2.5% | **Pass** | 정상 |
| 36 | `ssafe-platform` | 3개 / 3개 | 24 / 1.1% | 96 / 3.8% | 0 / 0.0% | 0 / 0.0% | **Pass** | 정상 |
| 37 | `util-analysis` | 3개 / 3개 | 12 / 2.2% | 24 / 15.7% | 0 / 0.0% | 0 / 0.0% | **Pass** | 정상 |
| 38 | `ymsdb-dksc` | 3개 / 3개 | 96 / 0.4% | 192 / 3.0% | 0 / 0.0% | 1 / 0.0% | **Pass** | 정상 |
| 39 | `ymsui-cluster` | 3개 / 3개 | 48 / 0.8% | 96 / 4.6% | 10 / 18.5% | 0 / 0.0% | **Pass** | 정상 |

---

### 3) [심층 1순위] Storage Policy Quota 및 노드 복구 여유 검증
*컨플루언스 실장애 방지: VM Operator Webhook Quota Denied 에러 및 노드 프로비저닝 차단 예방*

| Storage Policy | Quota Limit | 현재 Provisioned (%) | 현재 Actual Used | 4주 일평균 증가량 | 연휴 종료 예상 사용량 | N+1 노드 복구 여유 | 판정 |
|---|---:|---:|---:|---:|---:|---|:---:|
| `vks-pf-storage-policy` (사용자 VM OS) | 60 TB | 88% | 23.46 TB (39%) | `<값>` | `<예상치>` | 복구 가능 여유 확보 | `<Pass/Warning/Fail>` |
| `vks-pf-storage-policy-admin` (인프라 VM OS) | 50 TB | 37% | 13.26 TB (27%) | `<값>` | `<예상치>` | 여유 충분 | `<Pass/Warning/Fail>` |
| `vks-pf-storage-policy-data` (사용자 PV) | 15 TB | 54% | 0.55 TB (4%) | `<값>` | `<예상치>` | 여유 충분 | `<Pass/Warning/Fail>` |

| 실무 기능 검증 항목 | 점검 대상 | 확인 기준 | 점검 결과 |
|---|---|---|---|
| **Quota Denied 이벤트 감시** | `admission webhook quota-create` | 에러 카운트 0건 | `<정상/발생>` |
| **CCI LimitState 집계 일치** | VPC IP / Storage LimitState | CRD와 실제 할당량 일치 | `<정상/오류>` |
| **Unbound PVC 누수 확인** | Supervisor Unbound PVC | 0건 (Retain 잔여 볼륨 없음) | `<정상/확인>` |

---

### 4) 연휴 진입 차단 Gate (No-Go Gate Checklist)

- [ ] **`console-token` 교체 및 검증 완료**: 만료 D-5 도래 토큰 갱신 완료 및 Console/OpenSearch/VM 헬스체크 2xx 확인
- [ ] **Supervisor CA / Runtime Extension 만료일 확인**: 만료일 `연휴 종료 + 30일` 이상 잔여 확인 (TLS x509 실패 방지)
- [ ] **Unbound PVC 점검 (`v healthy supervisor`)**: Retain 정책으로 남은 Unbound PVC 사전 삭제 정리 완료
- [ ] **연휴 기간 변경 동결 (Change Freeze)**: 승인되지 않은 CAPI Reconcile / ArgoCD Sync / 노드 업그레이드 0건 확인

---

### 5) 최종 승인 및 서명

| 구분 | 성명 | 판정 | 점검 일시 | 비고 / 승인 번호 |
|---|---|---|---|---|
| **인프라 담당자** | `<성명>` | `<Pass/Fail>` | `YYYY-MM-DD HH:mm` | |
| **클라우드 파트장** | `<성명>` | `<Go / No-Go>` | `YYYY-MM-DD HH:mm` | |
