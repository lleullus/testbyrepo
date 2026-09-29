# [DKS-N] thanos-compact-2 PVC 증설 용량 산정

작성자: 미기재  
마지막 업데이트: 2026-09-28  
읽기 시간: 4분

## 1. 개요

prd-dkst-pa01-khm의 thanos-compact-2-0이 2026-09-25 이후 11회 재시작했다. 11회 모두 compaction 도중 no space left on device로 실패했다. 현재 PVC는 2000Gi다.

**실패 원인:** thanos-compact-2는 prd-apps-pb01-khm의 2일 블록 7개를 14일 블록 하나로 합치는 compaction을 수행한다. 이 작업 동안 원본(약 1,039Gi)과 결과 블록(약 1,039Gi)이 PVC에 동시에 있어야 하므로 약 2,077Gi가 필요하다. 이 클러스터의 데이터가 2주마다 약 6%씩 늘어, 이번 14일 구간(09-10~09-24)에서 필요량이 처음으로 PVC 2000Gi를 넘었다. 그래서 compaction이 끝나기 전에 디스크가 가득 차 실패하고, 재시작 후에도 같은 작업을 다시 시도하다 매번 같은 지점에서 실패하고 있다.

thanos-compact-2는 cluster label의 hashmod 3 값이 2인 클러스터를 담당한다. 해당 클러스터는 prd-apps-pb01-khm, prd-ctzj-pb01-khs, prod-ds-buildfarm-osp다. 이 중 현재 bucket에 블록이 있는 클러스터는 prd-apps-pb01-khm과 prd-ctzj-pb01-khs 두 개다. 이번 산정은 prd-apps-pb01-khm만 대상으로 한다. 지금까지 prd-ctzj-pb01-khs의 compaction은 prd-apps-pb01-khm의 compaction과 디스크 사용 최고점이 겹치지 않은 것으로 보인다. 따라서 PVC 필요 용량은 가장 큰 작업인 prd-apps-pb01-khm raw 14일 compaction 하나로 정해진다. 이 문서는 그 크기로 필요 용량을 산정하고, 증설 크기를 3Ti와 4Ti 중에서 고른다. 두 작업이 겹칠 경우의 영향은 3절 끝의 참고에 적었다.

## 2. 확인사항

### 2.1 compact-2의 담당 범위와 설정

```bash
$ kubectl -n $NS get sts thanos-compact-2 -o yaml | grep -E 'compact.concurrency|modulus|regex|storage:'
        - --compact.concurrency=2
          modulus: 3
          regex: 2
          storage: 150Gi

$ kubectl -n $NS get pvc data-thanos-compact-2-0 -o jsonpath='{.status.capacity.storage}{"\n"}'
2000Gi
```

- compact-2가 담당하는 클러스터 중 현재 bucket에 블록이 있는 것은 prd-apps-pb01-khm과 prd-ctzj-pb01-khs 두 개다. compact-2의 샤드 조건은 cluster label의 hashmod 3 값이 2인 것이다. 가장 큰 compaction 작업은 prd-apps-pb01-khm의 raw 14일 compaction이다.
- StatefulSet 템플릿은 150Gi, 실제 PVC는 2000Gi다. 과거에 PVC만 직접 늘렸기 때문이다. PVC를 다시 생성하면 150Gi로 돌아간다.

### 2.2 prd-apps-pb01-khm raw 14일 데이터 크기

compaction의 가장 큰 단계는 2일 블록 7개를 14일 블록 하나로 합치는 작업이다. 이 작업 중에는 Source 블록을 내려받아 둔 상태에서 결과 블록을 같은 디스크에 새로 쓴다. 따라서 필요한 디스크는 14일 raw 데이터 크기의 약 2배다(Thanos 문서 기준).

```bash
$ kubectl -n $NS exec thanos-compact-2-0 -- sh -c 'thanos tools bucket inspect --objstore.config="$OBJSTORE_CONFIG" -l cluster=\"prd-apps-pb01-khm\" --output=tsv' | cut -f2,4,7,12 | grep -E '336h|48h' | grep -P '\t0s$'
2026-08-13T00:00:00Z  336h0m0s  359,759,042,389  0s
2026-08-27T00:00:00Z  336h0m0s  379,160,126,799  0s
2026-09-12T00:00:00Z  48h0m0s   56,456,571,112   0s
2026-09-14T00:00:00Z  48h0m0s   56,786,507,203   0s
2026-09-16T00:00:00Z  48h0m0s   58,006,705,944   0s
2026-09-20T00:00:00Z  48h0m0s   58,714,307,640   0s
2026-09-22T00:00:00Z  48h0m0s   58,147,421,251   0s
2026-09-24T00:00:00Z  48h0m0s   58,384,452,071   0s
```

(열 순서: FROM, RANGE, #SAMPLES, RESOLUTION)

블록 크기는 meta.json의 files.size_bytes 합계로 확인했다.

```bash
$ kubectl -n $NS exec thanos-compact-2-0 -- sh -c 'thanos tools bucket ls --objstore.config="$OBJSTORE_CONFIG" -o json' | grep 01M3EFNTGKT4WJTNV86X0SCHYR | grep -o '"size_bytes":[0-9]*' | awk -F: '{s+=$2} END {printf "%.1f GiB\n", s/2^30}'
150.3 GiB
```

이 2일 raw 블록은 58,384,452,071 sample이고 크기는 150.3GiB다. sample 1개당 약 2.765 byte다. 이 값을 각 14일 구간의 sample 수에 곱해 크기를 구했다.

| Cluster | Time | Samples | Data Size (Raw) | 필요 디스크 (x2) | 2000Gi 결과 |
|---|---|---|---|---|---|
| prd-apps-pb01-khm | Start Time: August 13, 2026 9:00 AM<br>End Time: August 27, 2026 9:00 AM<br>Duration: 14 days | 359,759,042,389 | 926.4 Gi | 1,853 Gi | 성공 |
| prd-apps-pb01-khm | Start Time: August 27, 2026 9:00 AM<br>End Time: September 10, 2026 9:00 AM<br>Duration: 14 days | 379,160,126,799 | 976.4 Gi | 1,953 Gi | 성공 |
| prd-apps-pb01-khm | Start Time: September 10, 2026 9:00 AM<br>End Time: September 24, 2026 9:00 AM<br>Duration: 14 days | 약 403,356,000,000 (2일 블록 평균 × 7) | 1,038.7 Gi | **2,077 Gi** | **실패 (ENOSPC)** |

09-10 구간은 compaction이 실패해 아직 14일 블록이 없다. 그래서 2일 블록의 평균에 7을 곱해 계산했다.

prd-apps-pb01-khm raw는 2주마다 약 5.9%(약 56Gi)씩 꾸준히 늘었다. 필요 디스크는 08-27 구간에서 2000Gi에 약 50Gi 남긴 수준까지 올라왔고, 09-10 구간에서 처음으로 2000Gi를 넘었다. 데이터가 갑자기 늘어난 것이 아니라, 꾸준한 증가가 2000Gi 한계에 도달한 것이다.

실패 로그도 이 계산과 맞는다. 입력 raw 약 1,039Gi를 받아 둔 상태에서 결과 블록 chunk segment 1,844개(약 922Gi)를 쓴 시점에 ENOSPC가 났다.

```text
level=error ... msg="critical error detected" err="compaction: group 0@3175624986547008247: compact blocks [...]: 3 errors:
populate block: write chunks: preallocate: no space left on device;
sync /var/thanos/compact/compact/0@3175624986547008247/01M3BN84F2H0QV8THJPFDC1J86.tmp-for-creation/chunks/001844: file already closed;
write /var/thanos/compact/compact/0@3175624986547008247/01M3BN84F2H0QV8THJPFDC1J86.tmp-for-creation/index_tmp_p: no space left on device"
```

### 2.3 3Ti와 4Ti 비교

다시 부족해지는 시점은 필요 디스크(prd-apps-pb01-khm raw 14일 × 2)가 PVC를 처음 넘는 14일 구간이 끝나는 날로 잡았다. 그날부터 해당 구간의 compaction이 시작되기 때문이다. 증가 가정은 두 가지다.
- 복리: 2주마다 5.9%
- 선형: 2주마다 56Gi

| 항목 | 3Ti (3,072Gi) | 4Ti (4,096Gi) |
|---|---|---|
| 현재 필요량 2,077Gi 대비 여유 | 약 995Gi (48%) | 약 2,019Gi (97%) |
| 다시 부족해지는 시점 (복리) | 2026-12-31 | 2027-03-11 |
| 다시 부족해지는 시점 (선형) | 2027-01-28 | 2027-06-03 |
| 운영 가능 기간 | 약 3~4개월 | 약 5.5~8개월 |

## 3. 조치방안

thanos-compact-2의 PVC를 4Ti(4,096Gi)로 증설한다. 3Ti는 2026년 12월 말~2027년 1월 말에 다시 부족해져 연말에 재증설이 필요하다. 4Ti는 현재 증가 추세 기준으로 2027년 3월~6월까지 운영할 수 있다(2.3). 스토리지 여유가 4Ti에 미치지 못하면 3Ti로 증설하고, 12월 재산정에서 추가 증설 여부를 판단한다.

진행 조건:
- StorageClass의 allowVolumeExpansion이 true여야 한다.
- PowerFlex storage pool(SP04)에 증설분만큼 여유가 있어야 한다. 4Ti로 늘리면 2,096GiB, 3Ti로 늘리면 1,072GiB가 추가로 필요하다. 여유량은 아래 스토리지 풀 여유 검토를 따른다.
- PVC는 한번 늘리면 줄일 수 없다. Compactor PVC는 작업 공간이고 원본은 Object Storage에 있으므로, 증설이 실패해도 데이터는 유실되지 않는다.

실행 절차:

1. PVC를 증설한다.
   ```bash
   kubectl -n $NS patch pvc data-thanos-compact-2-0 -p '{"spec":{"resources":{"requests":{"storage":"4096Gi"}}}}'
   ```
2. 확장 상태를 확인한다. conditions에 FileSystemResizePending이 남아 있으면 thanos-compact-2-0 Pod를 삭제해 재기동한다.
   ```bash
   kubectl -n $NS get pvc data-thanos-compact-2-0 -o jsonpath='{.status.capacity.storage}{"\n"}{.status.conditions}{"\n"}'
   ```
3. Pod 안에서 파일시스템 크기가 4.0T인지 확인한다.
   ```bash
   kubectl -n $NS exec thanos-compact-2-0 -- df -h /var/thanos/compact
   ```
4. StatefulSet 템플릿의 storage를 150Gi에서 4096Gi로 맞춘다. 배포 도구(Helm/ArgoCD)를 쓰면 values를 수정한다. 템플릿을 직접 바꿔야 하면 StatefulSet을 --cascade=orphan으로 삭제한 뒤 다시 생성한다.

검증 기준:
- bucket inspect에 prd-apps-pb01-khm의 2026-09-10 구간 14일 raw 블록이 나타난다.
- 원래 2일 블록들에 삭제 표시가 된다.
- ENOSPC 로그와 Pod 재시작이 더 이상 발생하지 않는다.

중단 및 추가 조사 조건:
- 증설 뒤에도 같은 chunk 위치 부근에서 ENOSPC가 나면, PVC 크기가 아니라 PowerFlex pool의 실제 할당을 확인한다.
- ENOSPC 없이 compaction이 진행되지 않으면, 조회 결과에 없었던 09-10과 09-18 2일 raw 블록의 partial 상태부터 확인한다.

재산정: 2026년 12월에 2.2의 조회를 다시 실행해 증가율을 갱신한다.

참고 — 두 클러스터의 compaction이 겹칠 경우: compact.concurrency가 2이므로 prd-apps-pb01-khm과 prd-ctzj-pb01-khs의 raw 14일 compaction이 동시에 실행될 수는 있다. 그러나 지금까지 두 작업의 디스크 사용 최고점이 겹친 적은 없다. 08-27 구간은 prd-apps-pb01-khm 단독 필요량 1,953Gi로 2000Gi 안에서 성공했다. 두 작업이 동시에 최고점에 이르면 필요량은 약 2,950Gi(prd-ctzj-pb01-khs raw 약 438Gi 포함)가 되고, 4Ti는 2026년 12월 말에 부족해진다. 증설 후 ENOSPC가 다시 나고 로그상 두 그룹이 동시에 진행 중이었다면, compact.concurrency를 1로 낮춰 동시 실행을 막는다.

스토리지 풀(SP04) 여유 검토: compact-2 PVC의 StorageClass가 사용하는 SP04의 현재 상태는 다음과 같다. 기준 시각은 [DKS 배포 관리] 2026-09-28 17:18이다.

| 항목 | 값 | 비율 |
|---|---|---|
| Total | 386,071 GiB | |
| Required | 372,393 GiB | 96.5% |
| Provisioned | 359,992 GiB | 93.2% (Max 93.2%) |
| Used | 155,578 GiB | 40.3% (Max 41.0%) |
| 남은 할당 여유 (Total - Provisioned) | 26,079 GiB | 6.8% |
| 실 여유량 (Total - Used) | 230,493 GiB | 59.7% |
| Session | 721개 | |

증설하면 SP04 상태가 다음과 같이 바뀐다. 현재 PVC 2000Gi를 기준으로 증가분만 더했다.

| 항목 | 3Ti (+1,072 GiB) | 4Ti (+2,096 GiB) |
|---|---|---|
| Provisioned | 361,064 GiB (93.5%) | 362,088 GiB (93.8%) |
| Total - Provisioned | 25,007 GiB | 23,983 GiB |
| Required | 373,465 GiB (96.7%) | 374,489 GiB (97.0%) |
| Total - Required | 12,606 GiB | 11,582 GiB |
| 남은 할당 여유 중 이번 증설이 차지하는 비율 | 4.1% | 8.0% |

할당 기준(Total - Provisioned)으로는 4Ti로 늘려도 약 24TiB가 남는다. 증설 자체는 가능하다. 실제 사용률은 40%대이므로 물리 용량도 부족하지 않다. 다만 Provisioned 93.2%와 Required 96.5%는 이미 높은 수준이다. 아래 항목은 증설 전에 스토리지 담당과 확인한다.

- Required 값의 의미: Required(372,393 GiB)가 Provisioned보다 12,401 GiB 크다. 이 차이가 이미 요청됐지만 아직 할당되지 않은 볼륨인지 확인해야 한다. 그런 볼륨이라면 실제 여유는 Total - Required 기준인 13,678 GiB다. 4Ti로 증설하면 11,582 GiB가 남는다.
- 할당 상한 정책: SP04에 Provisioned 또는 Required 비율의 상한(예: 95%)이 있는지 확인해야 한다. Required 기준으로는 이미 96.5%다. 상한이 있다면 3Ti 증설도 승인 대상이 될 수 있다.
- Thin/Thick 여부: SP04가 thin provisioning이면 Provisioned가 커져도 실제 사용량(Used)은 compaction 중에만 일시적으로 약 2.1Ti 늘었다가 작업이 끝나면 다시 줄어든다. thick이면 증설분 전체가 즉시 물리 용량을 차지한다.
- 풀 전체 증설 계획: 남은 할당 여유 약 26TiB는 다른 PVC 증설이나 신규 볼륨과 함께 나눠 쓰는 공간이다. 이번 증설분(1~2TiB)을 넣었을 때 SP04 확장 계획이 필요한지 판단한다.

위 항목을 확인한 결과 할당 여유나 정책상 4Ti가 어렵다면 3Ti로 증설한다. 이 경우 2.3의 시점(2026-12 말~2027-01 말) 전에 재산정과 재증설을 계획한다.
