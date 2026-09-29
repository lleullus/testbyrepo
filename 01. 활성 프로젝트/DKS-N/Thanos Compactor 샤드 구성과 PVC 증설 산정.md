# Thanos Compactor 샤드 구성과 PVC 증설 산정

관련 문서: [[thanos-compact-2 ENOSPC와 PVC Working Space 분석]]

## 1. Compactor 샤드별 담당 클러스터

Sidecar는 Compactor에 직접 데이터를 보내지 않는다. 각 클러스터의 Sidecar가 2h 블록을 Object Storage에 올리고, Compactor는 `--selector.relabel-config`로 자기 샤드에 해당하는 external label(`cluster`)의 블록만 가져가 처리한다.

출처: 사내 산정 스레드(2025.05.30, 2025.11.21). 14일 합계는 raw, 5m, 1h 블록을 모두 더한 값이다.

| Compactor | 담당 클러스터 | 14일 합계 | 필요 용량(×2) | PVC |
|---|---|---|---|---|
| compact-0 | prod-ds-citizen 1496.2, prod-ds-member 249.8, prd-ctzn-pa01-cad 576.5, prd-dkso-pa01-khm 77.2, dev-apps-pb01-khs 227.3, prd-dkst-pa01-khm 79.4, prd-ctzs-pb01-khs 82.3 | 2,788.7Gi (25.05) | 5,577.4Gi | 5,600Gi |
| compact-1 | prod-ds-member-dev 168.5, prod-ds-buildfarm-vm 536, prd-dksc-pa01-khm 106.5, prd-apps-pa01-cad 56.5, prod-ds-dbaas 124.9 | 992.4Gi (25.05) | 1,984.8Gi | 2,000Gi |
| compact-2 | prd-ctzj-pb01-khs 163.2, prd-gslb-pb02-khm 59.7, prd-gslb-pb01-khm 56.5, prd-apps-pb01-khm 464.5 | 743.9Gi (25.11) | 1,487.8Gi | 2,000Gi (현행, 25.05 산정 시 1,000Gi) |

compact-2의 14일 합계는 2025.05에 529Gi, 2025.11에 743.9Gi였다. 반년 사이 약 40% 늘었고, 증가분은 대부분 prd-apps-pb01-khm(294.1 → 464.5)과 prd-ctzj-pb01-khs(80.3 → 163.2)에서 나왔다.

실측 설정 (2026-09-28, prd-dkst-pa01-khm의 thanos-compact-2 StatefulSet):
- 샤드 규칙: `hashmod(cluster) % 3`, compact-2는 `shard == 2`만 유지한다. 위 표의 16개 클러스터에 hashmod(md5 하위 8바이트 % 3)를 적용해 보면 표의 샤드 배정과 모두 일치한다.
- prod-ds-buildfarm-osp도 hash 결과가 2이므로, 클러스터가 살아 있다면 **compact-2 담당**이다. 2025년 산정표에는 빠져 있었다(2024.10 기준 14일 177.2Gi).
- `--compact.concurrency=2`: 최대 2개 그룹을 동시에 compaction한다.
- `--compact.enable-vertical-compaction`, `--deduplication.replica-label=prometheus_replica`: dedup이 켜져 있다. 측정한 블록 크기에 replica 배수가 들어가 있지 않다.
- StatefulSet의 `volumeClaimTemplates`는 `data=150Gi`로 남아 있고 실제 PVC는 2,000Gi다. PVC만 직접 늘렸기 때문이다. PVC를 다시 만들면 150Gi로 돌아가므로 템플릿도 함께 맞춰야 한다(3.3의 4단계).
- compact-0과 compact-1의 목록과 수치는 2025.05 기준이다. 두 샤드 모두 필요 용량과 PVC 사이 여유가 1% 미만이므로 함께 다시 측정해야 한다.

## 2. compact-2가 지금 부족한 이유

2026-09 장애 분석에 따르면 2,000Gi PVC에서 한 그룹(`0@3175624986547008247`, raw)의 14d compaction이 반복적으로 ENOSPC로 실패했다.

- 입력: 2d 블록 7개. 실측한 1개가 약 126.3GiB이므로 7개는 약 884GiB로 추정한다.
- 출력: chunk segment `001844`(512MiB 단위) 시점, 약 920GiB에서 실패했다.
- 합계: 입력과 출력만 1.8TiB를 넘고, 여기에 index와 다른 그룹의 동시 작업분이 더해지면 2,000Gi를 넘는다.

2025.11 산정은 샤드 전체 14일치를 743.9Gi로 잡았다. 하지만 2026-09 기준으로는 **한 클러스터의 raw 14일치만 약 884GiB**다. 그 사이 데이터가 크게 늘어 2025.11의 필요량 1,487.8Gi는 더 이상 유효하지 않다.

### 2.1 bucket inspect 실측 (2026-09-28)

`bucket inspect`는 크기를 직접 보여주지 않으므로 sample 수로 환산했다. 환산 계수는 로컬에 남은 Source 블록으로 구했다. 이 블록은 126.3GiB이고, 같은 시기 prd-apps-pb01-khm의 2d raw 블록은 평균 576억 sample이다. 둘을 나누면 **약 2.35 B/sample**이다. 스레드의 과거 실측치 2.7~3.1보다 낮은데, dedup이 켜진 뒤 측정한 값이라 그런 것으로 보인다.

| 클러스터 | raw 14d (08-13) | raw 14d (08-27) | raw 14d (09-10 구간) | 5m 14d | 1h 14d |
|---|---|---|---|---|---|
| prd-apps-pb01-khm | 3,598억 → 789GiB | 3,792억 → 831GiB | 2d 블록 5개 평균 × 7 ≈ 884GiB (**미완료, 이번 실패 그룹**) | 약 30GiB | 약 2.7GiB |
| prd-ctzj-pb01-khs | 1,585억 → 347GiB | 1,668억 → 366GiB | 1,702억 → 373GiB (완료) | 약 13GiB | 약 1.2GiB |
| prd-gslb-pb01/pb02-khm, prod-ds-buildfarm-osp | 14d·2d 블록 없음 | | | | |

- **실패 그룹은 prd-apps-pb01-khm의 raw다.** 09-10 구간의 14d raw 블록이 ctzj에는 있지만 apps에는 없고, apps는 2d 블록으로만 남아 있다. 884GiB는 로컬 Source 1개로 추정한 입력 크기와 같다.
- apps raw 14d는 2주마다 약 5~6%씩 늘고 있다(789 → 831 → 884). ctzj는 2~5%다.
- apps의 09-10 구간 2d raw 블록 중 09-10과 09-18이 목록에 없다. inspect 결과에 `partial=2`가 있으므로 이 두 블록이 meta.json 없는 partial 블록일 가능성이 있다(`[추정]`). 증설 후에도 compaction이 진행되지 않으면 이 부분부터 확인한다.
- gslb 두 클러스터와 buildfarm-osp는 bucket에 블록이 없다. 폐기되었거나 업로드가 중단된 것으로 보이며, 산정에서는 제외한다.

## 3. compact-2 PVC 증설 방법

### 3.1 목표 용량 정하기

필요 용량 = 2 × (동시에 처리되는 상위 2개 raw 그룹, `--compact.concurrency=2`) × 1.1(index와 downsample 여유분). 아래는 2주마다 늘어나는 양이 최근과 같다고 보고 선형으로 외삽한 값이다.

| 시점 | apps raw 14d | ctzj raw 14d | concurrency=2 필요 | concurrency=1 필요 |
|---|---|---|---|---|
| 현재 | 884GiB | 373GiB | **약 2,770GiB** | 약 1,950GiB |
| +3개월 | 약 1,190GiB | 약 460GiB | 약 3,620GiB | 약 2,620GiB |
| +6개월 | 약 1,500GiB | 약 540GiB | 약 4,480GiB | 약 3,300GiB |

- 현재 2,000Gi는 concurrency=1로 낮추더라도 여유분이 없다. 실패 지점 기준으로 입력 884GiB에 출력 약 922GiB가 이미 쌓여 있었다.
- **권고: 4,096Gi(4Ti)로 증설하고 concurrency=2는 유지한다.** 이 크기로 약 3~4개월을 버틴다. 그 전에 4.5의 재측정을 한다.
- 6개월 이상 버티려면 5,000Gi가 필요하다. 또는 4Ti로 증설하면서 concurrency=1로 낮추는 방법도 있다. 이 경우 compaction은 느려지지만 6개월 치 수요(약 3,300GiB)를 감당한다.

### 3.2 사전 확인

```bash
# PVC와 StorageClass
kubectl -n <ns> get pvc data-thanos-compact-2-0 -o wide
kubectl get sc <storageclass> -o jsonpath='{.allowVolumeExpansion}{"\n"}'

# 배포 주체 확인 (Helm/Operator/ArgoCD가 관리하는지)
kubectl -n <ns> get sts thanos-compact-2 -o jsonpath='{.metadata.labels}{"\n"}{.metadata.annotations}{"\n"}'

# 백엔드 여유 공간 (PowerFlex storage pool 여유량은 스토리지 콘솔에서 확인)
```

- `allowVolumeExpansion`이 `true`가 아니면 PVC 패치가 거부된다. StorageClass 변경은 별도 승인을 받는다.
- PVC 용량은 늘리기만 할 수 있고 줄일 수 없다.
- Object Storage의 블록이 원본이므로 Compactor PVC는 작업 공간일 뿐이다. 증설이 실패해 PVC를 새로 만들어도 데이터가 유실되지 않는다. 다만 진행 중인 compaction은 처음부터 다시 한다.

### 3.3 실행

1. **PVC 확장**

   ```bash
   kubectl -n <ns> patch pvc data-thanos-compact-2-0 \
     -p '{"spec":{"resources":{"requests":{"storage":"4096Gi"}}}}'
   ```

2. **확장 상태 확인**

   ```bash
   kubectl -n <ns> get pvc data-thanos-compact-2-0 \
     -o jsonpath='{.status.capacity.storage}{"\n"}{.status.conditions}{"\n"}'
   kubectl -n <ns> describe pvc data-thanos-compact-2-0   # Events 확인
   ```

   - CSI 드라이버가 온라인 확장을 지원하면 Pod가 실행 중일 때 파일시스템까지 확장된다.
   - `FileSystemResizePending` 조건이 남아 있으면 Pod를 재시작한다(`kubectl -n <ns> delete pod thanos-compact-2-0`).

3. **Pod에서 실제 용량 확인**

   ```bash
   kubectl -n <ns> exec thanos-compact-2-0 -- df -h /var/thanos/compact
   ```

4. **StatefulSet 템플릿 맞추기**

   `volumeClaimTemplates`는 기존 StatefulSet에서 변경할 수 없다. 이 단계를 하지 않으면 다음 재배포 때 템플릿 불일치로 동기화가 실패하거나, PVC를 새로 만들 때 작은 용량으로 돌아간다.

   - Helm/ArgoCD로 관리한다면 values의 compactor 2 persistence size를 새 용량으로 수정한다.
   - StatefulSet을 `--cascade=orphan`으로 삭제한 뒤 새 템플릿으로 다시 만든다(Pod와 PVC는 유지된다).

   ```bash
   kubectl -n <ns> delete sts thanos-compact-2 --cascade=orphan
   # 수정된 매니페스트/차트로 재생성
   ```

### 3.4 완료 판정

- `df` 기준 파일시스템 크기가 목표 용량과 같다.
- 실패하던 그룹의 14d 블록이 생성되어 업로드되었다(`thanos tools bucket inspect`로 해당 cluster의 14d raw 블록 확인).
- 원래 2d 블록 7개에 `deletion-mark.json`이 붙었다.
- ENOSPC 로그와 Pod 재시작이 멈췄다.
- `thanos_compact_halted` = 0이고, `thanos_compact_group_compactions_failures_total`이 더 이상 증가하지 않는다.

증설 후에도 같은 지점에서 실패하면 PVC가 아니라 백엔드(PowerFlex pool) 용량이나 할당 문제를 조사한다.

## 4. 증설 용량 산정 절차 (일반)

### 4.1 입력값 측정: 클러스터별 14일 블록

```bash
thanos tools bucket inspect --objstore.config-file=<cfg> \
  --selector='cluster="<name>"'
```

클러스터별로 Duration이 14d인 블록의 해상도별 크기를 기록한다.

- R_raw: raw(0) 블록 크기
- R_5m: 5m(300000) 블록 크기
- R_1h: 1h(3600000) 블록 크기
- B14 = R_raw + R_5m + R_1h

14d 블록이 없는 클러스터는 다음 중 하나로 추정한다.

- 가장 최근 2d 블록 7개의 합계
- sample 수로 추정: 블록 크기 ≈ sample 수 × 약 3 byte. 스레드 실측값은 2.7~3.1 B/sample이었다.

  ```
  B14 ≈ rate(prometheus_tsdb_head_samples_appended_total[1d]) × 86400 × 14 × 3 B
  ```

**측정 시점의 vertical compaction(dedup) 설정을 함께 기록한다.** dedup을 끄면 HA 복제본 수만큼 크기가 늘어난다. 스레드 예상치는 약 3배였다.

### 4.2 동시에 실행되는 작업 파악

- 14d compaction은 한 그룹(클러스터 × 해상도) 단위로 실행되며, 입력 블록 다운로드와 출력 블록 쓰기가 동시에 디스크에 있어야 한다. 따라서 필요 공간은 그룹 크기의 약 2배다.
- 14일 구간은 모든 클러스터에서 같은 시각에 끝나므로, 같은 샤드의 클러스터들이 거의 동시에 14d compaction 대상이 된다.
- 동시에 처리되는 그룹 수 = min(`--compact.concurrency`, 샤드 내 그룹 수)

### 4.3 샤드별 PVC 산정식

```
PVC_shard = 2 × Σ(동시에 처리되는 상위 그룹들의 크기) × (1 + g) + 여유분
```

- concurrency ≥ 샤드 내 클러스터 수(DKS 기존 설정은 8)이면 **샤드 내 모든 클러스터의 B14 합계 × 2**가 된다. 2025년 산정 방식이 이것이다.
- concurrency = 1이면 **샤드 내 가장 큰 클러스터의 R_raw × 2**가 하한이다.
- g는 다음 점검 시점까지의 증가율이다. 이전 측정과 비교해 산출한다(compact-2는 반년 약 40%).
- 여유분에는 index와 downsample 작업 공간을 넣는다. 산정값의 10% 이상을 잡는다.

예시 (compact-2, 2025.11 수치, concurrency ≥ 4):

```
2 × 743.9 × 1.4 × 1.1 ≈ 2,291Gi
```

2026-09 실측(단일 raw 그룹만 약 884GiB)에서 보듯 이 값도 이미 부족할 수 있다. 수치는 반드시 새로 측정한 값을 넣는다.

### 4.4 사용하지 않는 방식

2024.09의 `8 × 426 × 2 / 3 = 2,272Gi`는 쓰지 않는다. 모든 동시 작업 슬롯이 가장 큰 클러스터를 처리하고, 그 부하를 샤드 3개가 균등하게 나눈다고 가정했기 때문이다. 실제로는 한 클러스터가 한 샤드의 한 그룹에서만 처리되므로 샤드별로 따로 계산해야 한다.

### 4.5 점검 주기

1. 반기마다(또는 클러스터를 추가하거나 dedup 설정을 바꿀 때) 4.1~4.3을 다시 측정한다.
2. 샤드마다 `필요 용량 / PVC` 비율을 기록하고, 0.8을 넘으면 증설한다.
3. Grafana의 PVC 사용률은 kubelet이 1분 주기로 수집하므로 compaction 최고점을 놓친다. 용량 판단은 사용률 그래프가 아니라 이 산정값으로 한다.

## 5. 참고: Object Storage 용량 산정

retention: raw와 5m는 30일, 1h는 180일.

```
S_cluster = (R_raw + R_5m) / 14 × 30 + R_1h / 14 × 180
S_total   = Σ S_cluster × D × H + margin
```

- D: dedup 계수. dedup이 켜져 있으면 1, 꺼져 있으면 복제본 수(스레드 기준 3). B14를 dedup을 끈 뒤 측정했다면 이미 반영되어 있으므로 1로 둔다.
- H: retention 지연 버퍼(1.1~1.2). retention은 compaction과 downsampling이 끝난 뒤에 적용되므로 그 전까지 사용량이 계속 늘어난다.
- margin: 스레드에서는 100Gi를 잡았다.

## 참고 자료

- Thanos Compactor Disk: https://thanos.io/tip/components/compact.md/#disk
- Cortex Compactor disk utilization: https://cortexmetrics.io/docs/blocks-storage/compactor/#compactor-disk-utilization
- thanos-io/thanos#1767: https://github.com/thanos-io/thanos/issues/1767#issuecomment-660849337
- Kubernetes PVC 확장: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#expanding-persistent-volumes-claims
