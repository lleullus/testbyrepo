# Prometheus의 시계열이 Thanos Block으로 합쳐지는 과정 — Working Space와 ENOSPC의 이해

## 문서의 목적

Prometheus가 수집한 시계열이 어떤 파일로 저장되고, Thanos가 그 파일들을 어떤 기준으로 합치는지 설명합니다. Block을 만드는 과정부터 따라가며, 병합 범위와 동시 작업 수가 달라질 때 로컬 작업 공간이 왜 달라지는지, 작업 실패 뒤에는 왜 사용량이 낮게 보일 수 있는지 이해합니다.

이 문서는 Prometheus Block을 Sidecar로 Object Storage에 업로드하는 구성을 다룹니다. 기본적인 시간 범위 병합을 먼저 설명하고, 다른 구성이 결과를 바꾸는 조건은 해당 설명에 붙입니다. 일반 구조는 공식 문서로 확인했으며, 구체적인 실행 경로는 Thanos v0.40.1과 Prometheus TSDB v3.5.0을 **각각의 참고 구현**으로 확인했습니다. 이 둘을 대상 환경에 함께 배포된 조합이라고 확인한 것은 아닙니다. 기존 `thanos-compact-2` 관측은 본문과 구분해 부록에 보존합니다.

## 전체 인과 지도

이 지도는 Prometheus가 만든 Block이 Sidecar를 통해 Object Storage에 저장되고, Thanos Compactor가 이를 더 큰 Block으로 병합하는 과정에서 **왜 로컬 Working Space가 필요하고, 어떻게 ENOSPC가 발생할 수 있으며, 실패 뒤에는 왜 낮은 사용량이 관측될 수 있는지**까지 연결한다.

비유는 문서 전체에서 하나의 **도서관 시스템**을 사용한다. Prometheus는 자료를 만드는 지점, Object Storage는 중앙보존서고, Compactor의 로컬 `data-dir`은 보존 자료를 꺼내 다시 묶는 제본 작업실에 대응한다.

```text
시계열 데이터를 저장 가능한 단위로 조직
  sample → 시계열 식별 → TSDB Block → Object Storage
                                     │
                                     ▼
병합 대상을 정하고 병합이 만드는 결과 이해
  출처·해상도 → Compaction Group → plan의 Source
  Source ──새 데이터·index로 재구성──> 더 넓은 시간 범위의 Output
                                      │
                                      └─ 이후 더 큰 병합의 Source 후보

실제 Thanos의 로컬 병합 구현
  선택된 Source 다운로드 완료 → Source를 읽으며 Output 작성
                              → 같은 로컬 filesystem의 사용량 증가
                              → 공간 부족 시 쓰기·할당 실패 가능
                              → 성공·오류 경로에 따라 파일 상태 변화

독립적인 관측 경로
  실제 파일 상태 ──주기적 측정·수집──> 모니터링 화면
```

### 블록 1 — sample을 시계열에 귀속한다

#### 기술적 목표

수집된 sample을 **어느 시계열의 어느 시점 값인지 다시 식별할 수 있는 형태로 조직하여**, 이후 저장·색인·조회가 가능하게 한다.

#### 비유

도서관에서 낱장 자료의 내용만 보관하고 어느 기록물에 속하는지 표시하지 않으면 나중에 원하는 기록을 다시 찾기 어렵다. sample이 낱장 기록이라면 metric 이름과 label은 **그 기록이 어느 연속 기록물에 속하는지 알려주는 분류번호**에 해당한다.

#### 본문

측정된 `(시각, 값)`만 떼어 놓으면 그 값이 무엇을 측정한 것인지 구별할 수 없다. 따라서 Prometheus는 먼저 측정 대상을 식별할 기준이 필요하고, **metric 이름과 label의 조합**을 하나의 시계열을 구별하는 기준으로 사용한다. 같은 조합에서 수집된 sample은 같은 시계열에 귀속되고, label이 달라지면 metric 이름이 같더라도 다른 시계열이 된다. 이렇게 **시계열의 식별자와 그 시계열에 속한 sample의 관계가 보존되어야** 나중에 특정 시계열의 값을 다시 찾아 읽을 수 있다.[^data]

#### ASCII

```text
측정값
(12:00, 22.1)
      │
      │ 어느 시계열의 값인가?
      ▼
metric + labels
temperature_celsius{sensor="a"}
      │
      │ 같은 식별자를 가진 sample을 귀속
      ▼
시계열 A
├─ (12:00, 22.1)
├─ (12:01, 22.3)
└─ ...
```

### 블록 2 — 시계열을 시간 범위별 TSDB Block으로 영속화한다

#### 기술적 목표

계속 들어오는 시계열 데이터를 **일정한 시간 범위 단위로 영속 저장하여**, 이후 해당 기간의 데이터와 색인을 하나의 단위로 읽을 수 있게 한다.

#### 비유

도서관의 최근 기록은 작업대에서 계속 추가되고 있지만, 일정 기간이 지나면 그 기간의 기록을 하나의 보존 상자로 묶는다. 상자 안에는 실제 기록뿐 아니라 **어떤 자료가 어디 들어 있는지 알려주는 색인과 상자의 기간 정보**도 같이 넣는다.

#### 본문

새 sample이 계속 유입되는 최근 데이터는 아직 완성된 영속 파일 묶음으로 확정되지 않는다. Prometheus는 최근 데이터를 Head에서 다루고 WAL을 복구 기록으로 사용하다가, 오래된 구간을 일정 시간 범위의 **TSDB Block**으로 작성한다. Block의 `chunks/`에는 sample 데이터가 들어가고, `index`는 시계열과 chunk 위치를 연결하며, `meta.json`은 Block이 어느 시간 범위를 담는지 등의 정보를 가진다. 따라서 Block이 완성되면 앞 블록에서 만든 **시계열 식별 관계와 실제 sample을 일정 기간 단위로 다시 읽을 수 있는 영속 저장 단위**가 생긴다.[^storage]

#### ASCII

```text
계속 들어오는 sample
        │
        ▼
      Head
        │
        ├── WAL : 재시작 복구 기록
        │
        └── 오래된 시간 구간을 확정
                    ▼
               TSDB Block
               ├─ chunks/   sample
               ├─ index     시계열 → chunk
               └─ meta.json 시간 범위·통계
```

### 블록 3 — 완성된 Block을 출처 정보와 함께 중앙 저장소에 보관한다

#### 기술적 목표

Prometheus 로컬에서 완성된 Block을 **장기 보관과 이후 Thanos 처리가 가능한 공용 저장소로 전달하면서**, 어느 수집 지점에서 만들어진 Block인지 구별할 수 있게 한다.

#### 비유

각 지점 도서관에서 완성한 보존 상자를 중앙보존서고로 보내되, 상자에는 반드시 **어느 지점에서 만든 자료인지 표시하는 지점표**를 붙인다. 중앙서고는 같은 종류의 상자가 많아져도 그 표식을 보고 출처를 구별할 수 있다.

#### 본문

Prometheus 로컬에만 Block이 존재하면 Thanos가 여러 수집 지점의 Block을 장기간 보관하고 후속 병합 대상으로 다루기 어렵다. Sidecar는 완성된 Block을 **Object Storage에 복사·업로드**하고, Block metadata에는 `external labels`를 붙여 어느 수집기에서 나온 Block인지 구별할 수 있게 한다. 그 결과 Object Storage에는 데이터 자체뿐 아니라 **Block의 출처를 판단할 수 있는 정보**가 함께 모이고, Compactor는 이를 이용해 뒤에서 서로 병합 가능한 Block을 구분할 수 있다. 이 문서의 대표 구성은 Prometheus의 최소·최대 Block duration을 모두 2h로 두어 로컬 Block 병합을 맡기지 않고 Sidecar가 완성된 2h Block을 업로드하는 경우다. 업로드는 복사이며 즉시 Prometheus 로컬 원본을 이동·삭제한다는 뜻은 아니다.[^sidecar]

#### ASCII

```text
Prometheus 로컬
완성된 TSDB Block
        │
        │ Sidecar 복사·업로드
        ▼
Object Storage
├─ Block 데이터
└─ external labels
   └─ cluster / replica 등 출처 정보
```

### 블록 4 — 병합 가능한 Block을 구분하고 이번 작업의 Source를 선택한다

#### 기술적 목표

Object Storage에 있는 여러 Block 중 **서로 함께 병합할 수 있는 후보를 구분하고**, 그중 이번 한 번의 병합 작업에 사용할 입력 Block을 결정한다.

#### 비유

중앙보존서고에서는 먼저 같은 지점에서 왔고 같은 형식으로 보존된 상자끼리 분류한다. 그 분류 전체가 작업 후보군이고, 그중 이번 제본 작업에서 실제로 꺼낼 몇 상자만 별도의 **작업 목록**으로 선정한다.

#### 본문

Object Storage에는 서로 다른 출처와 서로 다른 **데이터 해상도**의 Block이 함께 존재할 수 있으므로 모든 Block을 한꺼번에 병합할 수는 없다. 여기서 해상도는 원본 sample을 보관하는 raw Block인지, 5분·1시간처럼 일정 구간으로 집계한 downsampled Block인지 구별하는 metadata 기준이다. Compactor는 먼저 **출처 정보와 데이터 해상도**가 같은 Block들을 Compaction Group으로 묶는다. 그다음 해당 Group 안에서 시간 범위와 현재 Block 상태를 기준으로 이번 병합에 실제로 사용할 Block 목록을 선택한다. 이 선택 결과가 **plan**이고, plan에 들어간 Block들이 이번 작업의 **Source**가 된다. 따라서 Group은 병합 가능한 후보의 범위이고, Source는 그중 이번 작업에서 실제로 처리할 입력이다.[^group]

#### ASCII

```text
Object Storage의 Block들
        │
        ├─ 출처가 같은가?
        └─ 해상도가 같은가?
                 │
                 ▼
         Compaction Group
                 │
          시간 범위 등으로 선택
                 ▼
               plan
                 │
                 ▼
        이번 작업의 Source
```

### 블록 5 — Source를 더 큰 시간 범위의 Block으로 재구성한다

#### 기술적 목표

여러 시간 구간에 나뉜 Source Block을 **더 적고 더 넓은 시간 범위의 Output Block으로 재구성하여**, 이후 더 큰 범위의 병합도 가능하게 한다.

#### 비유

여러 개의 작은 보존 상자에 나뉘어 있던 연속 기록을 꺼내 하나의 더 큰 보존 상자로 다시 정리한다. 내용물을 요약해서 버리는 것이 아니라 **기존 기록은 유지하면서 새로운 통합 색인을 만든다**. 이렇게 만든 큰 상자도 나중에는 더 큰 보존 묶음을 만드는 재료가 될 수 있다.

#### 본문

각 Source Block은 자기 시간 구간의 sample과 index를 따로 가지고 있다. Compactor는 선택된 Source를 읽어 데이터를 시간 순서에 맞게 모으고, 그 전체를 가리키는 새로운 index와 함께 **새 Output Block을 작성한다**. 기존 Source 뒤에 데이터를 단순 추가하는 것이 아니라 새로운 Block을 만드는 작업이다. 완성된 Output은 이후 다시 Source 후보가 될 수 있으므로 병합은 더 넓은 시간 범위로 단계적으로 진행될 수 있다. 예를 들어 참고 구현의 범위에서는 2시간 Block들이 8시간 Block으로, 그 결과가 다시 2일과 14일 범위의 입력으로 이어질 수 있다. **시계열 수·수집 밀도·압축 특성이 비슷하다는 조건에서는 더 긴 시간 범위를 처리하는 Source가 보통 더 많은 byte를 담지만, 시간 범위 하나만으로 정확한 입력량을 결정할 수는 없다.** 이 병합은 sample을 평균값 등으로 줄이는 downsampling과도 다른 작업이며, 시간 범위가 커졌다고 sample 자체가 같은 비율로 줄어드는 것은 아니다.[^compact][^cmd][^planner]

#### ASCII

```text
2h Source ─┐
2h Source ─┼─ 읽어서 새 데이터·index 구성 ──> 8h Output
2h Source ─┤                                  │
2h Source ─┘                                  ▼
                                        다음 병합의 Source
                                              │
                                              ▼
                                      더 넓은 시간 범위

예: 2h → 8h → 2d → 14d

Block 병합 ≠ downsampling
```

### 블록 6 — Source를 로컬 작업 공간에 유지한 채 Output을 작성한다

#### 기술적 목표

Object Storage의 Source를 **로컬에서 실제로 읽고 새 Output을 작성할 수 있는 작업 상태로 준비하면서**, Output이 완성될 때까지 필요한 입력을 보존한다.

#### 비유

중앙서고에서 가져온 원본 상자를 제본 작업실 선반에 놓고 새 통합 상자를 만든다. 새 상자가 완성되기 전까지는 원본 자료를 계속 확인해야 하므로 원본 상자를 치울 수 없다. 따라서 작업실에는 한동안 **원본 상자와 새로 커지는 상자가 동시에 존재**한다.

#### 본문

앞 블록은 compaction이 만드는 변환을 설명했고, 실제 Thanos 병합은 로컬 `data-dir`에서 수행된다. Compactor는 선택된 Source의 다운로드가 끝난 뒤 그 Source를 읽으면서 같은 로컬 작업 공간에 새로운 Output을 작성한다. Kubernetes 구성에서는 이 `data-dir`을 PVC가 연결한 영속 볼륨에 둘 수 있으며, PVC는 Object Storage bucket 자체가 아니라 Pod가 사용할 저장 공간을 요청·연결하는 수단이다. Output 작성이 끝나기 전에는 Source를 계속 읽어야 하므로 Source를 먼저 없앨 수 없다. 그 결과 **다운로드된 Source가 남아 있는 상태에서 Output의 크기가 점점 증가하는 시간 구간**이 생긴다. 즉 로컬 공간이 커지는 직접적인 이유는 다운로드와 쓰기가 독립적으로 동시에 시작해서가 아니라, **Source의 보존 기간과 Output의 작성 기간이 겹치기 때문**이다.[^group][^pvc]

#### ASCII

```text
Object Storage
      │
      │ Source 다운로드
      ▼
로컬 data-dir
├─ Source A ─┐
├─ Source B ─┼── 읽음 ──> 새 Output 작성 중
└─ Source C ─┘

시간 ───────────────────────>
Source  [===================]
Output          [+++++++++++]

          ↑ 두 파일 집합의 수명이 겹침
```

### 블록 7 — 동시에 존재하는 파일 전체를 Working Space가 감당한다

#### 기술적 목표

병합 중 같은 로컬 저장 공간에 실제로 존재하는 모든 작업 파일을 **수용하여 Output 작성을 계속할 수 있는 Working Space를 제공한다**.

#### 비유

제본 작업실에는 원본 상자, 새로 만드는 상자, 포장재와 다른 작업의 상자가 동시에 놓일 수 있다. 작업실의 필요한 크기는 완성품 하나의 크기가 아니라 **그 순간 실제로 작업실을 점유한 모든 물건의 합계**다. 여러 작업팀이 동시에 같은 방을 쓰면 실제로 겹친 물건만 합산해야 하고, 새 상자를 놓을 자리가 더 이상 없으면 그 작업을 계속할 수 없다.

#### 본문

병합 중 필요한 공간은 최종 Output 크기만으로 결정되지 않는다. 한 시점의 로컬 사용량에는 아직 남아 있는 Source, 작성 중인 Output, 별도 임시 파일과 기존 로컬 파일이 함께 포함된다. 여러 Group의 병합이 같은 PVC가 제공하는 filesystem에서 실제로 겹친다면 각 작업이 그 시점에 가지고 있는 파일도 함께 공간을 차지한다. 따라서 Working Space는 **같은 시점에 실제로 존재하는 서로 겹치지 않는 파일들의 합계**로 판단해야 하며, 그 값이 시간에 따라 변할 때 가장 큰 지점이 피크다. 프로그램이 Output을 더 쓰거나 파일 영역을 확보하려는데 filesystem에 필요한 여유 공간이 없다면 그 할당·쓰기에서 `ENOSPC`가 발생할 수 있다. ENOSPC는 Working Space의 기술적 목표가 아니라 **공간이 부족할 때 나타나는 실패 결과**다. 반대로 공간이 충분하다는 사실만으로 다른 종류의 오류까지 없어진다는 뜻은 아니다.[^compact][^cmd][^write]

#### ASCII

```text
시각 t의 로컬 저장 공간

[Source]
+ [작성 중 Output]
+ [임시 파일]
+ [기존 파일]
+ [실제로 겹친 다른 Group 작업]
              │
              ▼
        현재 사용량
              │
         시간에 따라 변화
              ▼
            Peak

다음 쓰기에 필요한 여유 공간
├─ 있음  → 쓰기 계속
└─ 없음  → ENOSPC
```

### 블록 8 — 작업 결과에 따라 로컬 파일 상태를 정리한다

#### 기술적 목표

병합 작업이 끝난 뒤 **성공 또는 실패 결과에 맞게 Output과 Source의 후속 상태를 처리하고**, 더 이상 필요하지 않은 로컬 작업 파일을 제거한다.

#### 비유

제본이 성공하면 완성된 새 보존 상자를 중앙서고로 보내고 작업실을 치운다. 작업 중 문제가 발생하면 만들던 미완성 상자를 폐기해서 자리를 확보할 수 있지만, 원본 상자는 아직 작업실에 남을 수 있다. 갑자기 작업실 운영이 중단되면 예정된 정리 절차 자체가 실행되지 않을 수도 있다.

#### 본문

Output 작성과 후속 처리가 성공하면 완성된 Block은 Object Storage에 업로드되고, 대체된 Source에는 삭제 처리를 위한 상태가 반영되며, 성공한 Group의 로컬 작업 디렉터리도 정리할 수 있다. 반면 Output 작성 도중 오류가 반환되면 완성되지 않은 임시 Output을 정리하는 경로가 실행될 수 있지만, 다운로드된 Source가 들어 있는 Group 디렉터리는 남을 수 있다. 따라서 오류 순간에는 Output 때문에 사용량이 크게 증가했더라도 **임시 Output 정리가 성공한 뒤에는 사용량이 다시 낮아질 수 있다**. 다만 강제 종료처럼 정상적인 오류 처리 경로 자체가 실행되지 않았거나 파일 삭제가 실패한 경우에는 같은 결과를 보장할 수 없으며, 다음 작업이 자동으로 재실행되는지도 별도의 실행·운영 정책에 달려 있다.[^writer][^group][^cmd][^signal]

#### ASCII

```text
Output 작성
   │
   ├─ 성공
   │    → Output 완성
   │    → Object Storage 업로드
   │    → Source 후속 처리
   │    → 로컬 작업 파일 정리
   │
   └─ 작성 오류 반환
        → 임시 Output 정리 시도
        ├─ 정리 성공 → 사용량 감소 가능
        └─ Source / Group 파일은 남을 수 있음

강제 종료
→ 위 정리 경로가 실행됐다고 단정할 수 없음
```

### 블록 9 — 실제 파일 상태를 주기적으로 관측해 모니터링 값으로 만든다

#### 기술적 목표

시간에 따라 변하는 실제 로컬 저장 공간 상태를 **주기적으로 측정 가능한 지표로 변환하여 모니터링 시스템에 제공한다**.

#### 비유

도서관 관리자가 제본 작업실을 계속 지켜보는 것이 아니라 일정한 간격으로 들어가 **그 순간 방 안에 있는 물건의 양만 기록한다**고 생각하면 된다. 두 점검 사이에 작업실이 가득 찼다가 정리되었다면 기록에는 처음과 마지막의 낮은 사용량만 남을 수 있다.

#### 본문

디스크의 실제 파일 상태는 Output이 커지고 정리되는 동안 계속 변하지만, 모니터링 시스템이 그 모든 변화를 파일 쓰기마다 기록하는 것은 아니다. Kubernetes 측에서 볼륨 통계를 계산하고 Prometheus가 이를 주기적으로 수집하면 Grafana는 저장된 측정값을 화면에 표시한다. 이 측정은 compaction 성공·실패 뒤에만 시작되는 실행 단계가 아니라 **실제 파일 상태와 독립적으로 주기 수행되는 관측 경로**다. 따라서 두 측정 사이에서 Output이 크게 증가했다가 오류 뒤 정리되면 **실제 피크가 존재했어도 측정값에는 남지 않을 수 있다**. 반대로 피크 시점에 측정이 이루어졌다면 높은 값이 기록될 수 있다. 그러므로 실패 뒤 화면에 보이는 낮은 사용량은 그 시점의 상태를 보여줄 뿐이며, 그것만으로 과거에 높은 피크가 없었다거나 ENOSPC가 발생했다고 또는 발생하지 않았다고 확정할 수 없다.[^stats]

#### ASCII

```text
실제 파일 상태
낮음 ── Output 증가 ── Peak / 오류 ── 정리 ── 낮음
  │                                      │
  ● 측정                              측정 ●
  │                                      │
  ▼                                      ▼
낮은 값                                낮은 값

        측정 사이의 Peak는 기록되지 않을 수 있음

실제 상태 변화 ≠ 모니터링 샘플의 연속 기록
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
