# `logtrim` 4.0.0 (0.4 아키텍처 세대) 실무 사용법 가이드

`logtrim`은 시스템·인프라·쿠버네티스 로그를 스트리밍 분석하는 오프라인 로그 압축 도구입니다. Python 표준 라이브러리만 사용하며, SQLite disk-backed 집계와 bounded-memory 상태를 유지합니다.

---

## 1. 요구사항 및 설치

- **요구사항:** Python 3.10 이상 (외부 의존성 **0개**, 순수 표준 라이브러리 구동)
- **별도 pip 설치 불필요:** 단일 실행 스크립트(`trim.py`) 또는 모듈 실행(`python -m logtrim`)으로 즉시 동작합니다.

### 패키지 설치 (선택 사항)
CLI 명령어(`logtrim`)로 어디서든 바로 호출하려면:
```bash
python -m pip install .
```

---

## 2. 기본 사용법 (단일 로그 분석)

### (1) 가장 빠른 기본 실행
입력 로그를 분석하여 터미널(stdout)로 빈도순 패턴 요약을 출력합니다.
```bash
# trim.py 직접 실행
python trim.py app.log

# 또는 모듈 호출
python -m logtrim app.log
```

### (2) 파일로 결과 저장
두 번째 인자로 출력 파일 경로를 지정합니다. (중도 실패 시 기존 파일 손상 없음 — 원자적 쓰기)
```bash
python trim.py app.log summary.txt
```

### (3) 파이프라인 연동 (`-` 지원)
`stdin`과 `stdout`을 완전 지원하므로 `journalctl`, `kubectl`, `cat` 파이프와 자연스럽게 연결됩니다.
```bash
# 실시간 저널 로그 요약
journalctl -u nginx -n 10000 | python trim.py - -

# 쿠버네티스 파드 로그 압축
kubectl logs my-pod --tail=50000 | python trim.py - -
```

### (4) 압축 파일 직접 입력
`logtrim`은 파일 매직 바이트를 자동 인식하므로 별도 압축 해제 없이 바로 읽을 수 있습니다.
- 지원 형식: `.gz` (gzip), `.bz2` (bzip2), `.xz`
```bash
python trim.py /var/log/syslog.2.gz syslog_summary.txt
```

---

## 3. 출력 포맷 (`--format`)

상황에 맞는 5가지 출력 형식을 지원합니다.

| 포맷 | 설명 | 추천 사용 시나리오 |
| :--- | :--- | :--- |
| `text` (기본) | pattern과 bounded variant 차이를 빈도순으로 출력 | 터미널 확인 |
| `html` | 검색 가능한 **단일 독립 HTML 리포트**. variant는 접힌 상세로 표시 | 브라우저 검토 |
| `markdown` | pattern 아래 variant 차이를 함께 표시 | 이슈·장애 보고 |
| `json` | 요약, schema version, pattern 및 top-N variant 통계 | 자동화·후처리 |
| `jsonl` | summary 한 줄 뒤에 pattern별 JSON 한 줄 | 대용량 스트리밍 처리 |

### 실행 예시
```bash
# 1. 브라우저에서 바로 열어볼 수 있는 대화형 HTML 리포트 생성
python trim.py app.log report.html --format html --top 2000

# 2. 장애 공유용 Markdown 표 생성
python trim.py app.log incident.md --format markdown

# 3. 자동화용 JSON 출력
python trim.py app.log report.json --format json
```

### pattern 아래의 semantic variants

기본 text/Markdown 출력은 coarse pattern의 하위에 top-N variant를 간결한 차이로 표시합니다. HTML은 `<details>`로 접어 전체 문자열 반복을 피합니다. JSON/JSONL은 전체 variant signature를 반환하며, 각 항목에 `count`, `baseline`, `current`를 담습니다.

```text
12542 GET /users/<NUM> HTTP/1.1 200
          ├─ 11891 −<NUM> +123 [baseline=0 current=0]
          ├─   491 −<NUM> +457 [baseline=0 current=0]
          └─   160 −<NUM> +789 [baseline=0 current=0]
```

`--max-variants N`은 pattern당 보여줄 variant 수를 제한합니다. SQLite는 모든 signature의 정확한 빈도를 유지하고, 보고 시 빈도순 상위 N개를 선택합니다. `variant_other_count`는 출력되지 않은 관측 건수, `variant_unique_count`는 전체 고유 signature 수입니다.

### JSON schema와 압축 지표

요약 객체의 `schema_version`은 `"4.0"`, variant 구조의 `variant_schema_version`은 `"1.0"`입니다. 도구 버전과 schema 버전은 별도 계약입니다.

| 필드 | 정의 |
| --- | --- |
| `pattern` | adaptive/final grouping 후 보고하는 압축 representation |
| `representative` | 해당 group에서 처음 보존한 관측 representation |
| `variants` | 빈도 상위 N개 semantic signature와 전체/baseline/current count |
| `family_states` | snapshot 상태별 정확한 count 및 baseline/current count |
| `physical_lines` / `original_count` | 입력의 실제 줄 수 |
| `logical_events` | multiline assembly 및 family reduction 이후 이벤트 수 |
| `coarse_patterns` | exact normalized signature 수, adaptive merge 전 |
| `final_patterns` / `trimmed_count` | 최종 report group 수 |
| `compression_ratio` | `100 × (1 - final_patterns / logical_events)` |
| `physical_compression_ratio` | `100 × (1 - final_patterns / physical_lines)` |

kubectl snapshot/describe는 family별로 먼저 축약됩니다. Pod는 namespace/workload로 group한 뒤 `family_states`에 `Running=2`, `CrashLoopBackOff=1`처럼 상태별 정확한 횟수를 유지합니다. Node는 상태별로 요약합니다. Describe는 Name, Namespace, Labels, Annotations, Conditions, Events를 보존하며 Events는 type/reason별 횟수로 요약합니다.

자동 variability inference는 unique coarse signature를 disk-backed로 집계합니다. 안정된 주변 구조에서 서로 다른 값이 3개 이상이고 entropy가 1 bit 이상이며 최빈값 비율이 80% 이하일 때만 후보 위치를 승격합니다. `status`, result, service/component, exception, error code 같은 의미 필드는 후보에서 제외합니다. inference는 compatible group만 합치고, 의미가 다른 상태를 일반 `<WORD>` 하나로 합치지 않습니다.

---

## 4. 핵심 분석 기능

### ① 장애 전후 비교 분석 (`diff`) — 가장 강력한 실무 기능
정상 시점(Baseline)과 장애 시점(Incident) 두 로그를 비교하여, 장애 시점에 **새로 출현한 에러(`NEW`)**와 **발생 빈도가 급증한 에러(`SURGED`)**만 정확히 분리합니다.

```bash
python -m logtrim diff normal.log incident.log --changes-only
```
- `--changes-only`: 변동 없는 일반 패턴은 제외하고 새로 생기거나 급증한 에러만 출력.
- HTML/Markdown 출력 가능:
  ```bash
  python -m logtrim diff normal.log incident.log -o diff_report.html --format html --changes-only
  ```

### ② 단일 라인 정규화 디버깅 (`explain`)
특정 에러 로그가 어떤 파서(JSON/Text)로 읽히고 어떻게 변수 치환(토큰화)되는지 진단합니다.
```bash
python -m logtrim explain --line '2026-09-18T10:20:30+09:00 ERROR java.lang.NullPointerException at Service.run(Service.java:42)'
```
**출력 예시:**
```json
{
  "pattern": "<TIMESTAMP> ERROR java.lang.NullPointerException at Service.run(Service.java:<LINE>)",
  "anchors": ["java.lang.NullPointerException"],
  "parser": "text"
}
```

### ③ 희귀 이상치(Outlier) 패턴 필터링
수천 번 반복되는 일반 노이즈를 거르고, 딱 1~2번 찍힌 고위험 잠재 장애 징후만 뽑아냅니다.
```bash
# 2회 이하로 발생한 희귀 패턴만 추출
python trim.py app.log rare_events.txt --rare-max-count 2
```

---

## 5. 커스텀 정규화 규칙 (`--rules`)

사내 시스템 고유 ID, 특정 주문 번호, 고객 번호 등을 인식시키려면 JSON 규칙 파일을 지정합니다.

**`rules.json` 예시:**
```json
{
  "version": 1,
  "rules": [
    {
      "id": "order-id",
      "pattern": "\\bord_[A-Z0-9]{10}\\b",
      "placeholder": "ORDER_ID"
    },
    {
      "id": "acme-error-code",
      "pattern": "\\bACME-\\d{6}\\b",
      "action": "preserve"
    }
  ]
}
```
**실행:**
```bash
python trim.py app.log output.txt --rules rules.json
```

---

## 6. 주요 CLI 옵션 레퍼런스

| 옵션 | 기본값 | 설명 |
| :--- | :--- | :--- |
| `input` | `-` (stdin) | 입력 파일 경로 또는 `-` |
| `output` | `-` (stdout) | 출력 파일 경로 또는 `-` |
| `--format` | `text` | 출력 포맷 (`text`, `json`, `jsonl`, `markdown`, `html`) |
| `--threshold` | `0.85` | 유사도 병합 임계값 (0.01 ~ 1.00) |
| `--top N` | 전체 | 출력할 상위 패턴 개수 제한 |
| `--rare-max-count N` | - | 발생 횟수 N회 이하인 희귀 패턴만 필터링 |
| `--sample-mode` | `none` | 원본 샘플 보존 정책 (`none`, `redacted`, `raw`) |
| `--multiline` | `auto` | 멀티라인 조립 (`auto`, `off`) |
| `--max-variants N` | `16` | pattern당 표시할 빈도 상위 variant 수; 전체 집계는 SQLite에서 정확히 유지 |
| `--max-candidates N` | `64` | 새 exact signature당 비교 후보 상한 |
| `--cache-size N` | `256` | bounded exact/adaptive lookup cache 상한 |
| `--sqlite-cache-kib N` | `8192` | SQLite page cache 용량 |
| `--max-event-bytes N` | `65536` | logical event 및 describe block 최대 크기 |
| `--max-event-lines N` | `256` | multiline event/describe block 최대 줄 수 |
| `--max-input-bytes N` | `0` (무제한) | 입력 바이트 상한 |
| `--max-clusters N` | `0` (무제한) | 허용할 최대 cluster 수 |
| `--rules <FILE>` | - | 사용자 정의 정규화 규칙 JSON 파일 |
| `--decode-errors` | `strict` | 텍스트 디코딩 에러 처리 (`strict`, `replace`) |
