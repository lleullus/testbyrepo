# Product Thesis — logtrim

**Schema:** product-thesis/v1
**Status:** CALIBRATED
**Created:** 2026-09-17

---

## 1. Product Promise

logtrim은 인프라 로그 캡처 원본을 입력받아, 반복 노이즈를 결정론적으로 압축하고, 운영상 구별해야 하는 사건은 보존하여, 사람이 빠르게 훑을 수 있는 요약본을 생성하는 오프라인 CLI 유틸리티다.

### 핵심 약속

1. **보수적 압축:** 같은 사건이 변수(timestamp, PID, UUID 등)만 다를 때만 하나로 합친다. 서로 다른 사건(nginx 실패 vs postgres 실패, timeout vs connection refused)은 절대 합치지 않는다.
2. **소스 패밀리 분리:** event stream, JSON log, kubectl snapshot, kubectl describe, generic text를 별도 파이프라인으로 처리한다. 서로 다른 패밀리를 하나의 그룹에 합치지 않는다.
3. **결정론적 출력:** 동일 입력 + 동일 버전 → byte-identical 출력. 비결정적 요소(정렬, 순서)가 없다.
4. **안전한 결과 커밋:** 처리 완료 후에만 output 파일이 생성된다. 중간 실패 시 기존 output을 손상시키지 않는다.
5. **표준 라이브러리 전용:** 런타임 의존성 0개. 오프라인 환경에서 설치·실행 가능.

### 이 약속이 제공하는 사용자 가치

인프라 장애 캡처를 받은 사람이 수천~수만 줄의 원본 대신 수십~수백 줄의 구조화된 요약을 읽고, 어떤 종류의 사건이 얼마나 발생했는지, 어떤 pod/node가 어떤 상태인지를 빠르게 파악할 수 있다.

---

## 2. 설계 계약 충돌 해결: 4/7 vs 4/13

### 문제

두 설계 문서가 서로 다른 제품을 정의하고 있다:

- **4/7 설계** (`2026-04-07-log-trimming-design.md`): `[count] pattern + sample + first_seen + last_seen` 형태의 **보수적 통계 그룹화** 도구.
- **4/13 설계** (`2026-04-13-aggressive-trim-design.md`): unique normalized pattern만 출력하고 count/sample/metadata를 제거하는 **공격적 패턴 추출기**.

현재 코드와 README는 4/7 모델을 구현하고 있으나, 4/13 문서가 유효한 것처럼 병존한다.

### 정본 결정

**4/7 모델이 정본이다.**

근거:

1. logtrim의 핵심 약속은 "보수적 압축"이다. `count`와 `sample`은 사용자가 압축 결과를 신뢰하기 위한 필수 정보다. count가 없으면 "이 패턴이 1번 나왔는지 10만번 나왔는지"를 구분할 수 없다.
2. 현재 코드, README, pyproject 모두 4/7 모델을 일관되게 구현한다.
3. 4/13의 aggressive 추출은 로그 탐색의 특정 사용 시나리오(패턴 목록만 빠르게 보기)에 유용하나, 이는 기본 동작이 아닌 선택적 모드로 제공되어야 한다.

**후속 조치:**

- 4/13 설계 문서는 `docs/superpowers/specs/` 하위에서 `SUPERSEDED` 또는 `DEFERRED` 상태로 명시적 표기한다.
- 향후 `--mode compact` 또는 유사 플래그로 4/13 스타일 출력을 선택적 모드로 도입할 수 있다. 이는 현재 Scope의 범위가 아니다.

---

## 3. 출력 형식 계약 (정본)

### Event / JSON 패밀리

```text
[count] <normalized_pattern>
count: <N>
sample: <representative_raw_record>
first_seen: <first_raw_record>
last_seen: <last_raw_record>
```

- 그룹 간 빈 줄로 분리
- count 내림차순, pattern 사전순 보조 정렬
- `first_seen`과 `last_seen`이 `sample`과 동일한 경우에도 표시한다 (명시적 일관성 우선)

### Snapshot 패밀리

```text
Pods by workload and state:
- <workload>: <STATUS> (<N> pod[s])
```

state signature에는 최소 STATUS를 포함한다. READY와 RESTARTS 보존은 P0-4에서 확장한다.

### Describe 패밀리

section anchor 기반 요약. 알려진 anchor와 그 continuation(들여쓰기/탭)을 보존한다.

### Generic 패밀리

원본 텍스트 그대로 출력. 다른 패밀리에 분류되지 않은 내용.

### 섹션 타이틀

| 패밀리     | 타이틀            |
|----------|----------------|
| event    | Event Logs     |
| json     | JSON Logs      |
| snapshot | Snapshot Output|
| describe | Describe Output|
| generic  | Generic Text   |

- 단일 generic-only 입력인 경우 `Generic Text` 헤더 제거 (현 동작 유지).
- mixed 입력에서는 모든 섹션에 타이틀 표시.

---

## 4. 정규화 계약: Semantic Identity vs Volatile Value

### 핵심 원칙

정규화는 **volatile value만 제거**하고 **semantic identity는 보존**해야 한다.

| 분류            | 예시                             | 정규화 정책                     |
|---------------|--------------------------------|-----------------------------|
| Volatile value | timestamp, PID, UUID, hash, IP, port, pod suffix | placeholder로 치환 (`<TS>`, `<PID>`, `<UUID>` 등) |
| Semantic identity | component name (nginx, postgres), error type (timeout, connection refused), field name | **절대 제거하지 않음**          |

### 현재 위반 사항 (P0 결함)

**A. Component identity 소실 (false merge):**

`normalize.py:8`의 `_PROC_PATTERN`이 `nginx[1]` 전체를 `<PID>`로 치환한다.
올바른 동작: `nginx[<PID>]`처럼 component name을 보존하고 PID 숫자만 치환.

**B. Timestamp under-normalization (false split):**

`normalize.py:7`의 `_TIMESTAMP_PATTERN`이 `YYYY-MM-DDTHH:MM:SSZ`만 매칭한다.
누락: fractional seconds (`...000Z`), timezone offset (`+09:00`), syslog 형식 (`Mon DD HH:MM:SS`), klog 형식 (`I0407 12:00:00.000000`).

**C. JSON volatile field 부족:**

`_UNSTABLE_JSON_FIELDS`가 `{"request_id", "ts"}`뿐이다. `trace_id`, `timestamp`, `time`, UUID 값이 포함된 string 등이 처리되지 않는다.

### 입력 소스 패밀리별 보존 불변식 (Invariants)

**INV-1 (Event):** 동일 component의 동일 메시지는 variable token만 다를 때 합쳐진다. 서로 다른 component 이름 또는 서로 다른 에러 유형은 절대 같은 그룹에 들어가지 않는다.

**INV-2 (JSON):** `json.loads` 성공 시 field-order independent canonicalization을 사용한다. 지정된 volatile field를 제거한 뒤의 구조가 동일한 레코드만 합친다. string value 안의 variable token(UUID, timestamp 등)도 정규화한다.

**INV-3 (Snapshot):** 같은 workload에 속하는 pod들은 state signature가 동일한 경우에만 하나의 count로 합산한다. readiness, status, restart 차이가 있으면 별도 엔트리로 보존한다.

**INV-4 (Describe):** section 구조를 먼저 인식하고, 인식된 section 안의 subsection을 보존한다. 하나의 describe 출력이 여러 generic 조각으로 분절되어서는 안 된다.

**INV-5 (Generic):** 다른 패밀리에 분류되지 않은 텍스트는 원본 그대로 통과한다. 정규화·그룹화를 적용하지 않는다.

**INV-6 (Cross-family):** 서로 다른 패밀리 사이에서 그룹이 합쳐지는 일은 없다.

---

## 5. False Success 방지 기준

다음 상황은 logtrim이 "성공적으로 처리했다"고 보고하더라도 제품 약속을 위반한 것이다:

### 5.1 False Merge (과잉 합침)

- `nginx[1]: Failed to start`와 `postgres[2]: Failed to start`가 하나의 그룹으로 합쳐진 경우.
- `timeout`과 `connection refused`가 하나의 그룹으로 합쳐진 경우.
- `permission denied`와 `disk full`이 하나의 그룹으로 합쳐진 경우.
- 서로 다른 deployment의 pod가 하나의 snapshot 라인으로 합쳐진 경우.

### 5.2 False Split (과잉 분리)

- 동일 사건이 timestamp나 PID만 다른데 2개 이상의 그룹으로 분리된 경우.
- fractional seconds만 다른 동일 JSON 로그가 별도 그룹이 된 경우.

### 5.3 Semantic Information Loss (의미 정보 소실)

- snapshot에서 Running 1/1 restart 0과 Running 0/1 restart 99가 구분 불가능한 경우.
- describe 출력이 여러 Generic Text 조각으로 분절된 경우.
- component identity (nginx, postgres 등)가 정규화 과정에서 사라진 경우.

### 5.4 Error Propagation (오류 전파)

- 하나의 malformed JSON record가 이후 정상 JSON record들을 흡수하여 하나의 group으로 만든 경우.
- 하나의 parse 실패가 이후 section 전체의 해석을 오염시킨 경우.

### 5.5 Silent Degradation (무음 품질 저하)

- parse fallback, malformed row skip 등이 발생했으나 사용자에게 아무런 표시가 없는 경우.
- 결과가 생성되었으나 실제로는 대부분의 레코드가 generic fallback으로 처리된 경우.

---

## 6. 제품 완성 Gate (최소 기준)

logtrim을 "완성된 오프라인 로그 트리머"라고 부르기 위한 최소 조건:

1. 정본 spec이 하나다 (4/7 모델).
2. README의 예제가 그대로 executable test다.
3. Must-Merge / Must-Not-Merge corpus를 모두 통과한다.
4. 하나의 malformed record가 뒤 record를 오염시키지 않는다.
5. snapshot에서 readiness/restart 등의 약속된 상태를 잃지 않는다.
6. 정상 describe가 generic 조각으로 분해되지 않는다.
7. 큰 event file을 section 전체 메모리 적재 없이 처리한다.
8. stdin/stdout pipeline이 파일 입력과 동일한 결과를 낸다.
9. 실패·fallback·interrupt의 exit/stderr/output-file 결과가 명확하다.
10. 같은 input과 같은 version에서 byte-identical output이 보장된다.

---

## 7. 유지해야 할 현재 결정

다음은 보존 가치가 높은 현재 구현의 설계 결정이다:

- **Atomic output commit:** `NamedTemporaryFile` + `os.replace()` 구조.
- **Standard-library-only runtime:** 런타임 의존성 0개.
- **Exact-key grouping 철학:** 보수적 deterministic normalization + exact key. Fuzzy clustering 배제.
- **Source-family separation:** event/snapshot/describe를 별도 알고리즘으로 처리하는 구조.
- **Group 정렬:** count 내림차순, pattern 사전순.

---

## 8. 실행 범위 로드맵 (Scope 시퀀스)

| 우선순위   | Scope                                       | 목적                                        |
|---------|---------------------------------------------|-------------------------------------------|
| P0-1    | Contract Freeze + Golden Test Fixtures      | 정본 계약 확정, golden/adversarial 테스트 스위트 구축    |
| P0-2    | Bounded-Memory Streaming                    | section 전체 메모리 적재 제거, 실제 streaming pipeline |
| P0-3    | Normalization Safety Contract               | component identity 보존, timestamp 범위 확장, JSON volatile 정책 |
| P0-4    | Snapshot / Describe Semantic Preservation   | readiness/restart 보존, describe section 분절 방지 |
| P1-1    | CLI Stream Interface + Failure Contract     | stdin/stdout, exit code, encoding, interrupt |
| P1-2    | Parser Degradation Observability            | stderr diagnostic summary                 |
| P1-3    | Offline Distribution Cleanup                | setup script 안전화, tests 포함 정책 일치         |

P0-1이 모든 후속 작업의 선행 조건이다. P0-1이 확립한 golden fixture가 이후 모든 리팩터링의 regression guard 역할을 한다.
