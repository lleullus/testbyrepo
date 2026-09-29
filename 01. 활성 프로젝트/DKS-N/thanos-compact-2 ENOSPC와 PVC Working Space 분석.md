# Prometheus의 시계열이 Thanos Block으로 합쳐지는 과정 — Working Space와 ENOSPC의 이해

## 문서의 목적

Prometheus가 수집한 시계열이 어떤 파일로 저장되고, Thanos가 그 파일들을 어떤 기준으로 합치는지 설명합니다. Block을 만드는 과정부터 따라가며, 병합 범위와 동시 작업 수가 달라질 때 로컬 작업 공간이 왜 달라지는지, 작업 실패 뒤에는 왜 사용량이 낮게 보일 수 있는지 이해합니다.

이 문서는 Prometheus Block을 Sidecar로 Object Storage에 업로드하는 구성을 다룹니다. 기본적인 시간 범위 병합을 먼저 설명하고, 다른 구성이 결과를 바꾸는 조건은 해당 설명에 붙입니다. 일반 구조는 공식 문서로 확인했으며, 구체적인 실행 경로는 Thanos v0.40.1과 Prometheus TSDB v3.5.0을 **각각의 참고 구현**으로 확인했습니다. 이 둘을 대상 환경에 함께 배포된 조합이라고 확인한 것은 아닙니다. 기존 `thanos-compact-2` 관측은 본문과 구분해 부록에 보존합니다.

## 전체 이해 지도

```text
데이터 생성과 보관
  Prometheus: 시계열 sample → Head/WAL → TSDB Block
  Sidecar: 완성된 Block ──복사·업로드──> Object Storage

병합 대상과 범위
  출처 labels + 데이터 해상도 → Compaction Group
  Group 안에서 시간 범위에 맞는 Block 선택 → 이번 작업의 Source
  작은 범위 병합 결과 → 다음의 더 큰 범위를 병합할 입력

Compactor의 로컬 작업
  Source 다운로드 완료 → Source를 읽으며 새 Output 작성
                         [같은 디스크에 입력과 출력이 함께 존재]
  여러 Group의 작업이 실제로 겹침 → 같은 시점의 사용량을 합산

작업 이후와 관측
  전체 작업 성공 → 업로드·삭제 표시·로컬 정리
  작성 오류 반환 → 임시 Output 정리 시도; 재실행 여부는 별도 조건
  파일 사용량의 변화 ──독립적인 주기 측정──> 모니터링 화면
```

- **Prometheus가 수집하는 시계열은 이름과 label로 구별되며, 그 안에는 시각별로 측정한 sample이 쌓입니다.** 예를 들어 `temperature_celsius{sensor="a"}`는 센서 a의 온도 시계열을 가리키고, `12:00에 22.1`, `12:01에 22.3`은 그 시계열의 sample입니다. 같은 측정 이름이라도 `sensor="b"`라면 다른 시계열입니다. 이처럼 시계열을 구별하는 이름·label과 실제 시각·값을 함께 저장해야 나중에 특정 대상의 변화를 찾을 수 있습니다. 뒤에서 Block의 데이터와 색인을 구분하는 이유도 여기에 있습니다.[^data]

```text
temperature_celsius
├─ {sensor="a"} → (12:00, 22.1), (12:01, 22.3), ...
└─ {sensor="b"} → (12:00, 24.0), (12:01, 23.9), ...
     시계열의 구별                 그 시계열의 sample
```

- **Prometheus는 최근 sample을 다루는 Head와 복구 기록인 WAL을 사용하고, 오래된 시간 구간을 TSDB Block으로 묶어 저장합니다.** TSDB는 시계열 데이터베이스를 뜻합니다. Head는 아직 영속 Block으로 정리하지 않은 최근 데이터를 처리하는 영역이고, WAL은 재시작 때 데이터를 복구하는 데 사용하는 디스크 기록입니다. 기본 구성에서는 오래된 데이터를 약 2시간 범위의 Block으로 만듭니다. 한 Block 안의 `chunks/`에는 압축된 sample이, `index`에는 어떤 이름·label의 시계열을 어느 chunk에서 찾을지 알려 주는 색인이, `meta.json`에는 데이터의 시작·끝 시각과 통계 등이 들어갑니다. 따라서 Block은 단순한 파일 한 개가 아니라 **일정 시간 범위의 시계열을 읽는 데 필요한 데이터와 색인의 묶음**입니다.[^storage]

```text
수집한 sample ──> Head ──오래된 구간을 작성──> TSDB Block
         └─────> WAL: 재시작 복구에 사용하는 기록

TSDB Block의 파일 묶음
  <Block ID>/
  ├─ chunks/    : sample 데이터
  ├─ index      : 시계열 → chunk 위치
  └─ meta.json  : 데이터 시간 범위·통계
```

- **Thanos Sidecar는 완성된 Block을 Object Storage에 복사해, Prometheus의 로컬 보관과 별도로 장기 보관할 수 있게 합니다.** 여기서 Object Storage는 Block의 파일들을 객체로 보관하는 저장소이고, bucket은 그 객체들이 모이는 저장 공간입니다. Sidecar는 Prometheus와 함께 동작하며 업로드하는 Block metadata에 `external labels`를 덧붙입니다. 이는 앞의 센서별 label과 달리, 예를 들어 `cluster="a"`, `replica="0"`처럼 **어느 수집기에서 나온 Block인지** 구별하는 출처 표식입니다. Thanos Compactor에 이후의 병합을 맡기는 구성에서는, 같은 데이터의 서로 다른 병합본을 함께 업로드하는 문제를 피하도록 Prometheus의 로컬 Block 병합을 끕니다. 두 Block-duration 설정을 모두 `2h`로 둔 구성이라면 Sidecar의 출발 입력은 2h Block입니다. 업로드는 복사이며, 업로드 즉시 Prometheus의 원본을 이동·삭제한다는 뜻은 아닙니다.[^sidecar]

```text
Prometheus 로컬                         Object Storage의 bucket
완성된 2h Block ── Sidecar 복사 ──>      Block 파일들
                                         + 출처 labels
                                         {cluster="a", replica="0"}

시계열 label: 어떤 측정 대상인가?
출처 external labels: 어느 수집기에서 나온 Block인가?
```

- **Compactor는 같은 출처와 같은 데이터 해상도의 Block을 Group으로 묶고, 그중 이번에 합칠 입력만 선택합니다.** 데이터 해상도는 Block이 원래 sample을 보관하는지, 일정 시간 구간의 집계값을 보관하는지를 구별합니다. 원본은 raw이며 metadata의 resolution 값은 `0`입니다. Downsampling은 원본에서 5분·1시간 구간 등의 집계 데이터를 별도로 만드는 작업입니다. 같은 출처라도 원본과 집계 데이터는 병합할 Group이 다릅니다. 여기서는 출처 labels를 그대로 사용하는 기본 grouping을 설명합니다. **Compaction Group은 합칠 수 있는 후보들의 묶음이고, plan은 그 안에서 한 번의 작업에 선택한 Block 목록**입니다. 선택된 입력을 Source Block, 병합해서 만들 결과를 Output Block이라고 부릅니다. 같은 Group이라고 모든 과거 Block을 한꺼번에 내려받는 것은 아닙니다.[^group]

```text
출처 labels A
├─ raw Block들       → Group A/raw
│                       ├─ 이번 plan: B1, B2, B3, B4 = Source
│                       └─ 아직 선택하지 않은 다른 Block들
└─ 5분 집계 Block들  → Group A/5m

이번 plan의 Source들 ──병합──> 새 Output Block
```

- **Compaction이 필요한 이유는 여러 작은 Block에 나뉜 데이터를 더 적은 Block과 색인으로 정리하기 위해서입니다.** 앞에서 각 Block에는 sample뿐 아니라 시계열을 찾는 index도 있다고 보았습니다. 같은 시계열이 계속 수집되면 이 시계열의 정보는 여러 시간대 Block의 index에 반복해서 등장합니다. Compactor는 선택한 Source들의 데이터를 읽어 하나의 새 데이터·색인 묶음을 만듭니다. 기존 Source 파일 끝에 계속 덧붙이는 것이 아니라 새 Output을 작성하는 방식입니다. 삭제나 중복 제거가 없는 일반적인 시간 범위 병합에서는 sample의 시간 순서를 이어 담는 것이지, 오래된 sample을 일정 간격의 값으로 줄이는 것이 아닙니다. 그 점에서 **Block 병합과 앞에서 설명한 downsampling은 다른 작업**입니다. Block 수가 줄어도 저장해야 할 sample이 그만큼 줄어드는 것은 아닙니다.[^compact]

```text
Source B1: [sample 구간 1] + [그 구간의 index]
Source B2: [sample 구간 2] + [그 구간의 index]
                         │ 읽어서 새로 구성
                         ▼
Output C : [sample 구간 1과 2] + [새로 만든 index]

Block 수 감소 ≠ sample을 시간 구간별로 집계
```

- **병합 결과는 다음 병합의 입력이 될 수 있으므로, 더 넓은 시간 범위를 한 번에 처리하는 작업이 생깁니다.** 참고한 Thanos 구현의 range 집합은 `1h, 2h, 8h, 2d, 14d`입니다. 이것은 실행 대기 단계의 목록이 아니라 planner가 사용하는 시간 범위들입니다. Source가 이미 2h인 구성에서는 더 큰 범위로 가는 예를 `2h → 8h → 2d → 14d`로 볼 수 있습니다. 경계에 맞는 연속 Block들이 각 범위를 채운 단순한 예라면 2h Block 4개가 8h, 8h Block 6개가 2d, 2d Block 7개가 14d를 채웁니다. 실제 plan은 빈 시간 구간, 이미 병합된 Block, 겹침과 설정에 따라 달라지므로 이 개수를 필수 규칙으로 외우면 안 됩니다. **시계열 수·수집 밀도·압축 특성이 비슷할 때**, 더 긴 구간의 Source는 보통 더 많은 byte를 담습니다. 따라서 시간 범위를 알아야 작업 규모를 이해할 수 있지만, 시간만으로 정확한 디스크 용량을 결정할 수는 없습니다.[^cmd][^planner]

```text
연속되고 경계가 맞는 Block이라는 예
  2h × 4  ──병합──> 8h
  8h × 6  ──병합──> 2d
  2d × 7  ──병합──> 14d

더 긴 처리 구간
  + 비슷한 수집 밀도·시계열 구성
  → 더 많은 Source 데이터

처리 구간의 길이와 데이터 밀도는 별개의 입력값
```

- **Thanos Compactor의 로컬 작업 공간이 커지는 직접적인 이유는 Source를 내려받은 뒤, 그 Source를 읽으면서 같은 작업 디스크에 Output을 쓰기 때문입니다.** Object Storage가 장기 보관 장소라면 `data-dir`은 Compactor가 파일을 읽고 쓰는 로컬 작업 장소입니다. Kubernetes에서는 PVC로 저장 공간을 요청하고, Compactor 컨테이너를 실행하는 Pod에 볼륨을 연결(마운트)해 그 경로를 작업 디렉터리로 사용할 수 있습니다. PVC는 저장 공간에 대한 요청이며 Object Storage bucket 자체가 아닙니다. 참고한 Thanos 실행 경로는 선택된 Source의 다운로드가 끝나기를 기다린 다음 로컬 TSDB 병합을 호출합니다. Output 작성 중에도 Source를 계속 읽으므로 입력은 남아 있어야 합니다. **다운로드와 Output 작성을 독립 병렬로 실행해서가 아니라, 다운로드가 끝난 파일의 수명이 Output 작성과 겹쳐서** 두 데이터가 동시에 공간을 차지합니다. Block이 새로 만들어진다는 성질만으로 모든 시스템이 같은 로컬 사용량을 갖는 것은 아니며, 여기에는 Thanos의 이 로컬 재작성 방식이 전제됩니다.[^group][^pvc]

```text
실행 순서
Object Storage → Source 다운로드 완료 → 로컬 병합 → Output 작성 완료
                                              │
                                              ▼
병합 중 같은 작업 디스크의 파일 상태
├─ Source: 계속 읽는 입력 파일들
└─ Output: 새로 쓰는 결과 파일들

동시에 존재하는 파일 ≠ 독립적으로 동시에 시작한 작업
```

- **Working Space는 이처럼 작업을 끝내기 위해 필요해지는 로컬 공간이며, 판단해야 할 것은 같은 시점에 존재하는 파일들의 합계입니다.** 한 작업의 Source와 생성 중인 Output에 더해, 그 둘에 포함되지 않은 작업용 임시 파일과 다른 로컬 파일도 공간을 차지합니다. Source와 Output에는 각자의 chunks와 index가 이미 들어 있으므로 index를 다시 더하지 않습니다. 이전 시도에서 남은 Source를 이번 작업이 재사용한다면 그 파일도 한 번만 셉니다. 관측 구간에서 이 합계가 가장 큰 순간의 값이 피크(peak)입니다. 프로그램이 다음 파일 영역을 확보하거나 데이터를 쓸 때, 파일과 저장 공간을 관리하는 filesystem에 필요한 공간이 없으면 ENOSPC가 반환될 수 있습니다. 즉 이미 보관된 최종 결과의 크기뿐 아니라 **작성 중간에 더 확보해야 하는 공간**을 봐야 합니다. 반대로 공간이 충분해도 데이터 오류나 업로드 실패 등 다른 이유로 전체 작업은 실패할 수 있습니다.[^storage][^write]

```text
시각 t의 서로 겹치지 않는 항목
[이번 작업의 Source] + [생성 중 Output] + [별도 임시 파일] + [나머지 파일]
                                  │
                                  ▼
                         그 시각의 로컬 사용량

다음 할당·쓰기에 필요한 공간
├─ 할당 가능 → 작업 계속; 전체 성공 여부는 아직 별도
└─ 공간 부족으로 거절 → 해당 할당·쓰기 실패
```

- **여러 Group의 병합이 실제로 겹치면 같은 디스크에서 각 작업의 파일을 함께 감당해야 합니다.** `--compact.concurrency`는 한 Compactor에서 Group 병합을 얼마나 동시에 진행할 수 있는지를 제한합니다. 제한값이 2라고 언제나 두 작업이 최대 크기로 실행된다는 뜻은 아닙니다. 같은 시점에 실제로 존재하는 파일을 합해야 합니다. 서로 다른 Compactor에 다른 출처의 Group을 맡기는 sharding과도 다릅니다. 이 경우 별도 PVC라면 각 PVC의 사용량을 따로 봅니다. 앞서 설명한 downsampling 역시 로컬 파일을 만들지만, 참고한 Thanos v0.40.1 실행 경로는 병합 처리를 마친 뒤 downsampling 단계로 넘어갑니다. **같은 PVC를 사용한다는 이유만으로 두 단계의 최대 사용량을 동시 피크처럼 더하지 않습니다.** 앞 단계의 잔여 파일이나 다른 프로세스의 작업이 실제로 남아 있다면 그 파일만 해당 시점의 사용량에 포함합니다.[^cmd][^compact]

```text
동일 Compactor / 동일 PVC
시간 ─────────────────────────────>
Group A   [Source + Output 증가 ........]
Group B          [Source + Output 증가 ........]
                  ↑ 이 시각에 겹친 양을 합산

참고한 실행 경로의 작업 단계
Group 병합 처리 완료 → downsampling 수행
  각각의 최대값이 같은 시각에 발생한다고 가정하지 않음
```

- **Output이 완성됐을 때와 작성 중 오류가 반환됐을 때는 남는 파일이 달라집니다.** 참고한 TSDB writer는 새 Block을 임시 디렉터리에 쓰고, 쓰기·마무리 작업이 성공하면 최종 이름으로 바꿉니다. Thanos는 완성된 Block을 Object Storage에 업로드한 뒤 대체된 Source에 삭제 표시를 하고, 성공한 Group의 로컬 작업 디렉터리를 정리합니다. Object Storage의 Source 삭제와 로컬 복사본 정리는 서로 다른 저장 장소의 일입니다. Output 작성 중 함수가 오류를 반환하는 경로에서는 TSDB가 임시 디렉터리 정리를 시도하고, Thanos는 오류가 난 Group 디렉터리를 남깁니다. 정리까지 성공하면 작업 중 커졌던 Output이 없어져 로컬 사용량이 줄 수 있습니다. 다만 강제 종료처럼 정리 코드가 실행되지 않거나 삭제 자체가 실패한 경우는 다릅니다. 다음 시도가 실행되는지도 오류 종류, 멈춰 조사 대기하는 halt 설정, 재시작 정책에 달려 있으므로 ENOSPC 다음에 자동 재시도가 반드시 온다고 그리지 않습니다.[^writer][^group][^cmd][^signal]

```text
새 Output 작성
├─ 작성·마무리 성공
│    → 최종 Block 이름 → 업로드 성공 → Source 삭제 표시
│    → 성공 경로에서 로컬 Group 정리 시도
└─ 작성 중 오류 반환
     → 임시 Output 정리 시도
     → 정리 성공 시 사용량 감소; Group 입력은 남을 수 있음

강제 종료: 위 함수 종료 처리가 실행됐다고 볼 수 없음
재실행: 오류 처리·운영 정책에 따라 별도로 결정
```

- **모니터링 화면은 이러한 파일 변화를 주기적으로 관측한 결과이므로, 실패 뒤의 낮은 값이 실패 순간의 값과 같지는 않습니다.** Kubernetes의 kubelet은 노드에서 볼륨 통계를 계산·보관하고, Prometheus 같은 수집기가 지표를 받아 저장하면 Grafana가 그 값을 표시합니다. 지표가 파일 쓰기마다 만들어지는 기록은 아니므로, 한 번의 측정과 다음 측정 사이에 Output이 커졌다가 정리되면 중간 피크를 놓칠 수 있습니다. 반대로 그 시간에 측정했다면 높은 값이 남을 수 있습니다. 측정 주기는 compaction의 오류나 정리를 기다리는 실행 단계가 아니라 독립적인 관측 주기입니다. 따라서 사후 사용량만으로 과거 peak를 복원하거나, 낮은 사후 값만으로 용량 부족을 확정·배제할 수 없습니다.[^stats]

```text
실제 파일 상태: 낮음 ── Output 증가 / 오류 ── 정리 성공 ── 낮음
관측 시각:        ●                  (측정 없음)             ●
저장된 지표:     낮은 값                                    낮은 값

위는 peak를 놓치는 한 가지 예
오류 시점에도 관측했다면 높은 값이 기록될 수 있음
```

## 1. Block의 파일과 시간 정보를 실제로 읽는 방법

지도에서 Block을 데이터와 색인의 묶음으로 보았습니다. 실제 디렉터리 이름에는 ULID라는 고유 식별자가 쓰입니다. 이름은 어느 Block인지 구별하는 데 사용하고, 저장한 데이터의 시간 범위는 `meta.json`의 `minTime`, `maxTime`으로 읽습니다. 식별자의 생성 시각이나 현재 파일 생성 시각을 데이터 범위와 동일시하지 않습니다.

| 확인 대상 | 의미와 사용 범위 |
|---|---|
| `chunks/` | 압축된 sample을 담은 segment 파일들입니다. 파일 개수는 데이터량의 직접 측정값이 아닙니다. |
| `index` | 시계열과 chunk 위치를 연결합니다. Source 전체 byte나 Output 전체 byte에 이미 포함되는 파일입니다. |
| `meta.json`의 `minTime`, `maxTime` | Block에 저장한 데이터의 시간 범위를 판단합니다. |
| `compaction.level`, `sources`, `parents` 등 | 병합의 이력·계보를 나타냅니다. level 숫자를 모든 환경에서 고정된 시간 길이로 해석하지 않습니다. 현재 입력 plan 목록과 여러 세대의 계보도 구분합니다. |
| `tombstones` | 삭제 표시된 sample 구간을 기록합니다. 삭제 표시가 있는 작업은 단순한 sample 수 보존 예와 다릅니다. |

참고한 `CompactBlockMetas` 구현은 새 level을 입력의 최대 level에서 증가시키고, 시간 범위와 입력 계보를 별도로 구성합니다. 그러므로 “level이 몇이니 반드시 2d다”보다 실제 시간 필드를 보는 것이 직접적입니다.[^planner]

Head 역시 전부가 단순한 메모리 배열인 것은 아닙니다. 이 문서에서 Head/WAL을 소개한 목적은 최근 데이터와 완성된 Block의 역할을 구분하는 것입니다. 메모리 매핑된 Head chunk나 WAL 복구의 내부 구현은 별도의 메모리·복구 문제를 다룰 때 확대할 수 있습니다.[^storage]

## 2. 업로드 설정, Group, plan을 구분하는 방법

Sidecar 업로드 구성에서 `--storage.tsdb.min-block-duration`과 `--storage.tsdb.max-block-duration`을 같게 설정하는 것은 Prometheus의 로컬 Block 병합을 끄는 조건입니다. 둘을 같게 했다는 사실만으로 그 값이 2h라고 결정되는 것은 아닙니다. **둘 다 2h로 설정된 경우**를 지도의 대표 구성으로 사용했습니다.[^sidecar]

출처 labels는 업로드된 metadata의 Thanos 영역에서 확인합니다. 기본 Grouper는 labels와 downsampling resolution을 함께 사용합니다. 복제본 중복 제거를 위해 특정 replica label을 제거하는 설정 등이 적용됐다면 grouping에 쓰이는 유효 labels도 달라질 수 있습니다. 따라서 원래 Prometheus 설정의 문자열과 Compactor가 실제 grouping에 사용한 값을 구별해야 합니다.[^cmd][^group]

Group의 구성원 전체와 이번 plan은 다른 목록입니다. plan은 그 Group 안에서 planner가 선택한 이번 입력입니다. 같은 Group에 속한다는 사실이나 Group의 Block 개수만으로 이번에 내려받을 전체 byte를 계산하지 않습니다. 마찬가지로 `2d × 7 → 14d`는 **경계에 맞는 2d 입력 7개를 선택한 경우의 예**이지 Source 개수 7에서 역으로 시간 범위를 결정하는 규칙이 아닙니다.

## 3. 병합 범위, 데이터 밀도, Output 크기는 서로 다른 변수다

한 plan이 더 긴 구간을 담을수록 Source 합계가 커지는 경향은 입력 데이터의 밀도가 비슷할 때 성립합니다. 이를 단순한 계산 모델로 나타내면 다음과 같습니다. 이 식은 실측을 대신하는 제품의 공식이 아니라 관계를 드러내는 근사입니다.

```text
Source byte ≈ 처리 시간 범위 × 그 구간의 저장 데이터 밀도

저장 데이터 밀도에 영향을 주는 것
  시계열 수 / 수집 주기 / 값과 chunk의 압축 특성 / index 크기
```

예를 들어 단위 시간당 저장량이 같은 두 구간이라면 2d보다 14d 구간을 처리하는 쪽이 더 많은 입력을 가질 수 있습니다. 그러나 희박한 14d 데이터가 밀집한 2d 데이터보다 작을 수도 있습니다. 그러므로 range를 지웠을 때도 안 되지만, range 하나로 모든 용량을 결정해도 안 됩니다.

Output도 Source byte의 합과 정확히 같다는 보장은 없습니다. 색인 재구성, 압축, 삭제·겹침·중복 제거 여부가 크기를 바꿉니다. `Source와 비슷한 Output이 추가된다`는 관점은 병합 중 두 세대가 겹친다는 구조를 설명합니다. 모든 작업에서 정확히 두 배가 된다는 수치 법칙은 아닙니다.

Thanos 문서의 최대 2주 범위에 대한 Source와 Output 공간 예시는 이 동시 보관 구조를 설명하는 capacity-planning 출발점입니다. 그것만으로 cache·잔여 파일·모든 변형을 포함한 엄밀한 전체 디스크 상한을 증명하는 것은 아닙니다.[^compact]

## 4. 로컬 재작성과 오류 처리의 구현 경계

참고한 Thanos `Group.Compact` 경로는 plan의 Source들을 내려받는 작업이 완료되기를 기다린 뒤 `CompactWithBlockPopulator`를 호출합니다. 개별 Source 다운로드끼리는 병렬일 수 있지만, 그것이 선택된 Source를 아직 받는 중에 같은 plan의 Output 병합을 독립적으로 시작한다는 뜻은 아닙니다.[^group]

참고한 Prometheus TSDB writer는 `.tmp-for-creation` 경로 아래에 Output을 작성합니다. chunk segment를 열 때 공간을 미리 확보하는 `preallocate`를 수행하고, 기본 segment 크기는 `512 × 1024 × 1024` byte, 즉 512MiB입니다. 파일에 데이터를 쓰기 전 공간 확보부터 실패할 수 있다는 것이 중요합니다. 이전 segment의 사용하지 않은 선할당 꼬리는 마무리 과정에서 잘릴 수 있으므로 `segment 번호 × 기본 크기`를 그 순간의 정확한 할당 byte로 바꾸지 않습니다.[^chunks]

`defer`에 놓인 정리 코드는 함수가 그 종료 경로를 실제로 실행할 때 작동합니다. 참고한 writer는 정리를 시도하고 실패하면 로그를 남깁니다. 따라서 다음 상태들을 구분합니다.[^writer][^signal]

| 상태 | 이 설명에서 결론낼 수 있는 것 |
|---|---|
| Output 작성 중 오류 반환, 정리 성공 | 생성 중이던 임시 Output은 제거될 수 있습니다. |
| Output 작성 중 오류 반환, 정리 실패 | 오류 반환만으로 공간이 회수됐다고 선언하지 않습니다. |
| 최종 이름 변경 뒤 업로드 실패 | 완성된 로컬 Output과 bucket의 부분 업로드를 별도로 봐야 합니다. 단순한 임시 Output 삭제 경로와 같지 않습니다. |
| SIGKILL 등 강제 종료 | 종료 직전의 정리 코드 실행을 가정하지 않습니다. |
| halt 오류를 받은 실행 루프 | 설정에 따라 멈춰 조사 대기할 수 있습니다. 다음 plan 재실행을 자동으로 전제하지 않습니다. |

Thanos v0.40.1의 `--wait` 경로는 halt 오류와 재시도 가능한 오류를 구별합니다. 이 조건을 실제 배포 인자와 대조하기 전에는 ENOSPC가 몇 번의 재시작이나 재시도를 만들지 일반 원리만으로 결정할 수 없습니다.[^cmd]

## 5. 중복 없이 같은 시각의 사용량을 계산한다

디스크 공간의 계산 대상은 메모리 Working Set이 아니라 **로컬 파일이 점유하는 저장 공간**입니다. 아래에서는 동일 filesystem의 같은 시각에 관측하는 파일들을 서로 겹치지 않게 분류합니다.

```text
S_g(t): 작업 g의 로컬 Source 파일들
O_g(t): 작업 g의 Output 파일들; 그 안의 chunks/index/임시 파일 포함
X_g(t): S_g나 O_g에 포함되지 않은 별도 작업용 파일들
B(t)  : 위 작업 파일들에 포함되지 않는 나머지 파일들

U(t) = B(t) + Σ_g [ S_g(t) + O_g(t) + X_g(t) ]
Peak = max_t U(t)
```

단위는 각 항목에서 일관된 byte로 맞춥니다. 파일 내용의 논리적 크기와 filesystem에 실제 할당된 크기도 구분합니다. 위 식은 파일 항목의 회계이며, filesystem metadata·예약 공간 등 때문에 이 합계와 `df`의 사용량이 완전히 같다고 단정하지 않습니다. 공간 확보 가능 여부는 같은 filesystem에서 실제 사용 가능한 공간과 대조해야 합니다.

**같은 파일은 한 항목에만 들어갑니다.** 예를 들어 이전 실패에서 남은 Source를 이번 작업이 재사용하면 이번의 `S_g(t)`에 포함하고 `B(t)`에 다시 포함하지 않습니다. cache를 `B(t)`에 넣었다면 별도의 cache 항목으로 재차 더하지 않습니다. Output 전체 크기를 쟀다면 그 안의 index를 별도로 추가하지 않습니다.

가상의 한 시점에 Source 400GiB(재사용한 Source 60GiB 포함), Output 450GiB, 별도 작업 파일 10GiB, cache 30GiB만 있다면 합계는 **890GiB**입니다. 재사용 Source 60GiB와 cache 30GiB를 추가로 더해 980GiB로 만들면 중복 계산입니다. 이 숫자는 실제 DKS-N 관측값이 아니라 회계 경계를 설명하는 예입니다.

또 **각 작업의 최대값을 합한 것과 실제 전체 최대값은 다릅니다.** 다음 역시 설명용 가상 수치입니다.

| 시각 | 작업 A | 작업 B | 두 작업 합계 |
|---|---:|---:|---:|
| t1 | 100GiB | 700GiB | 800GiB |
| t2 | 800GiB | 50GiB | 850GiB |
| t3 | 100GiB | 200GiB | 300GiB |

A의 최대 800GiB와 B의 최대 700GiB를 합한 1500GiB는 이 표의 실제 피크가 아닙니다. 두 작업이 함께 만든 피크는 850GiB이며, 별도의 `B(t)`가 30GiB로 일정하다면 전체는 880GiB입니다. 상한을 보수적으로 잡는 계산과 관측된 피크를 보고하는 계산을 같은 것으로 쓰지 않습니다.

참고한 Compactor는 일반 병합 처리 뒤 downsampling을 수행합니다. 이 실행 경로의 각 단계가 어느 시점에 어떤 파일을 남기는지를 위 `U(t)`에 반영하면 됩니다. 동일 PVC에 다른 프로세스가 동시에 쓰거나 이전 단계 잔여 파일이 실제 남아 있는 경우에는 그 파일을 추가하되, 단순히 기능 이름이 둘이라는 이유로 각각의 최대치를 동시에 더하지 않습니다.[^cmd]

## 6. ENOSPC와 사용률 지표가 말해 주는 범위

쓰기 중 `ENOSPC`가 기록되면 어느 파일·filesystem의 어느 요청이 실패했는지부터 식별합니다. Linux `write(2)`는 디스크 블록 quota 소진을 `EDQUOT`, 파일이 있는 장치의 공간 부족을 `ENOSPC`로 구별합니다. inode 소진은 파일 생성 같은 다른 단계에서도 문제를 만들 수 있습니다. 따라서 quota·inode·backend 문제를 모두 무조건 같은 errno라고 쓰지 않고, 실제 실패한 호출과 filesystem 상태를 대조합니다.[^write]

PVC의 요청 용량은 명목상 크기이며, 프로세스가 그 순간 추가 할당할 수 있는 공간과 같지 않을 수 있습니다. 다른 파일, filesystem 예약 공간과 이미 확보된 영역 때문에 남은 여유가 달라집니다. 예를 들어 새 segment를 위해 512MiB를 확보해야 하는데 실제 할당 가능한 공간이 256MiB라면 공간 확보는 실패할 수 있습니다. 이 예는 화면의 반올림된 사용률이 반드시 100%여야 실패하는 것은 아니라는 점을 설명합니다. 특정 사건의 실제 가용량을 대신 측정한 것은 아닙니다.

kubelet의 `volumeStatsAggPeriod`는 통계를 계산·캐시하는 주기이며 문서상 기본값은 1분입니다. 실제 설정과 지표 수집·표시 주기는 대상 환경에서 확인해야 합니다. 화면이 사용하는 지표, 집계 구간, sampling 시각이 다르면 실패 직전 화면과 filesystem의 순간 상태를 일대일로 비교할 수 없습니다.[^stats]

## 부록. 기존 `thanos-compact-2` 기록과 아직 확인하지 않은 사실

다음 표는 정련 전 대상 문서의 349~374행에 있던 기록을 보존한 것입니다. **이번 작업에서 원본 로그·클러스터·Object Storage를 다시 조회하지 않았습니다.** 기록의 존재와 현재 운영 상태의 독립 검증은 구분합니다. 기록의 출처 파일과 SHA-256은 함께 제공한 감사 보고서와 source manifest에 있습니다.

| 항목 | 기존 문서의 기록 |
|---|---|
| Pod / PVC | `thanos-compact-2-0` / `data-thanos-compact-2-0`, 2000Gi, `/var/thanos/compact` |
| 반복 실패 | 2026-09-25 이후 11회 재시작, compaction 중 ENOSPC |
| Group / Source | 표본 로그에 `0@3175624986547008247`, 동일 Source 7개 |
| 실패 위치 | `chunks/001839`·`001844`의 preallocate, `index_tmp_p` write에서 ENOSPC |
| Grafana | 재시작 시점 2회는 약 90% 이상, 나머지는 약 4~80% |
| 사후 파일 상태 | `df` 표시 2.0T 중 약 121.3G 사용, Group 아래 Source 하나 약 126.3G, tmp 없음 |

Source 7개라는 기록은 각 Source의 시간 범위가 2d라는 증거가 아닙니다. 같은 크기·시간 범위라는 가정을 추가해야 특정 plan으로 이어집니다. 실제 `minTime`·`maxTime`과 입력 plan을 확인하기 전에는 14d 작업이라고 확정하지 않습니다.

원문에는 `126.3 × 7 ≈ 884G`라는 조건부 계산도 있었습니다. 이것은 나머지 6개가 모두 비슷한 크기라는 가정에 따른 값이지 실측 합계가 아닙니다. 특히 `G`가 어떤 명령·옵션에서 나온 표기인지, 두 측정이 같은 시각·경계를 가리키는지 확인하지 못했습니다. `2000Gi`와 다른 단위의 숫자를 그대로 더하거나, `2000Gi`를 정확한 `2Ti`와 같은 값으로 처리하지 않습니다.

높은 chunk segment 번호는 많은 파일을 작성한 정황이지만 번호만으로 그 순간의 실제 할당 byte를 복원할 수 없습니다. 임시 파일이 없다는 사후 기록도 바로 그 오류의 정상 정리 경로가 실행됐다는 독립 증거는 아닙니다. 일반 구현은 가능한 작동을 설명하고, 실제 사건의 경로는 그 시각의 로그와 파일 상태가 결정합니다.

이 기록으로 유지할 수 있는 판단은 **로컬 Output 작성 중의 공간 부족이 반복됐다는 기록과 Source·Output 공존 모델이 부합한다**는 것입니다. 정확한 부족량, 실제 14d plan, 모든 재시작의 원인, 모니터링 peak 누락 원인까지 확인됐다고 확대하지 않습니다. 이를 더 좁히는 직접 자료는 입력 Block의 시간 범위·byte, 배포 이미지와 인자, 같은 시각의 파일·filesystem 사용량입니다. 다른 조건을 함께 바꾸지 않고 같은 plan이 증설 뒤 성공한다면 용량 가설의 증거가 강해지지만 과거의 정확한 피크까지 복원되는 것은 아닙니다.

## 질문별 자료 안내

| 질문 | 직접 확인한 자료 |
|---|---|
| 시계열·sample·Block은 무엇인가? | Prometheus Data Model / Storage |
| Sidecar가 무엇을 업로드하고 어떤 설정으로 병합을 나누는가? | Thanos Sidecar 공식 문서 |
| Group·plan·로컬 다운로드 순서는 무엇인가? | Thanos v0.40.1 `pkg/compact/compact.go` |
| range·동시성·downsampling 실행 단계·halt 처리는? | Thanos v0.40.1 `cmd/thanos/compact.go` |
| 임시 Output·index·segment·정리 경로는? | 별도로 확인한 Prometheus v3.5.0 TSDB writer와 chunk writer |
| kubelet 통계 주기와 syscall의 오류 구별은? | Kubernetes KubeletConfiguration / Linux write(2) |

여기서 확인한 참고 버전의 구현은 대상 환경 배포 버전의 증거가 아닙니다. Thanos v0.40.1의 `go.mod`에 지정된 정확한 Prometheus 의존 리비전 본문은 이번 웹 도구에서 확보하지 못했으므로, TSDB v3.5.0 검토를 그 의존 리비전의 직접 검증으로 보고하지 않습니다.

[^data]: Prometheus, [Data model](https://prometheus.io/docs/concepts/data_model/). metric name·labels와 sample의 관계.
[^storage]: Prometheus, [Storage](https://prometheus.io/docs/prometheus/latest/storage/). on-disk layout, WAL, compaction, Source와 새 Block의 일시적 공존. 열람일 2026-09-29.
[^sidecar]: Thanos, [Sidecar](https://thanos.io/tip/components/sidecar.md/). Block 업로드, min/max block duration, external labels. 열람일 2026-09-29.
[^compact]: Thanos, [Compactor](https://thanos.io/tip/components/compact.md/). compaction의 목적, Stream, Resources/Disk. 열람일 2026-09-29.
[^group]: Thanos v0.40.1, [`pkg/compact/compact.go`](https://github.com/thanos-io/thanos/blob/v0.40.1/pkg/compact/compact.go). `DefaultGrouper`, `AppendMeta`, `Group.Compact`, 다운로드 완료 대기 뒤 `CompactWithBlockPopulator` 호출.
[^cmd]: Thanos v0.40.1, [`cmd/thanos/compact.go`](https://github.com/thanos-io/thanos/blob/v0.40.1/cmd/thanos/compact.go). `compactions`, `runCompact`, `compactMainFn`, 오류 분기. [go.mod](https://github.com/thanos-io/thanos/blob/v0.40.1/go.mod)의 의존성도 별도 확인.
[^planner]: Prometheus v3.5.0, [`tsdb/compact.go`](https://github.com/prometheus/prometheus/blob/v3.5.0/tsdb/compact.go). plan/range 처리 및 `CompactBlockMetas`; 실제 배포 조합의 확인이 아닌 참고 구현.
[^writer]: Prometheus v3.5.0, [`tsdb/compact.go`](https://github.com/prometheus/prometheus/blob/v3.5.0/tsdb/compact.go). `LeveledCompactor.write`의 임시 디렉터리·정리·이름 변경.
[^chunks]: Prometheus v3.5.0, [`tsdb/chunks/chunks.go`](https://github.com/prometheus/prometheus/blob/v3.5.0/tsdb/chunks/chunks.go). `DefaultChunkSegmentSize`, `finalizeTail`, `cut` 및 선할당.
[^pvc]: Kubernetes, [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/). PVC는 사용자의 저장 공간 요청이며 Pod가 볼륨을 사용함.
[^stats]: Kubernetes, [KubeletConfiguration](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/), `volumeStatsAggPeriod`.
[^write]: Linux man-pages, [write(2)](https://man7.org/linux/man-pages/man2/write.2.html), `EDQUOT`·`ENOSPC` 오류 구분.
[^signal]: Go 표준 라이브러리, [os/signal](https://pkg.go.dev/os/signal). SIGKILL은 포착할 수 없음. 강제 종료를 정상 함수 반환 경로와 구분하는 근거.
