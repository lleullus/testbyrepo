# `logtrim` v3 실무 사용법 가이드

`logtrim`은 시스템·인프라·쿠버네티스 로그의 대규모 반복 노이즈를 결정론적으로 압축하고, 고유 장애 패턴과 통계를 추출하는 고성능 오프라인 로그 분석 CLI 도구입니다.

---

## 1. 요구사항 및 설치

- **요구사항:** Python 3.10 이상 (외부 의존성 **0개**, 순수 표준 라이브러리 구동)
- **별도 pip 설치 불필요:** 단일 실행 스크립트(`trim.py`) 또는 모듈 실행(`python -m logtrim`)으로 즉시 동작합니다.

### 패키지 설치 (선택 사항)
CLI 명령어(`logtrim`)로 어디서든 바로 호출하려면:
```bash
pip install -e /path/to/logtrim-v3
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
| `text` (기본) | `COUNT    PATTERN` 형태의 고정폭 텍스트 | 터미널 빠른 훑기, 콘솔 모니터링 |
| `html` | 검색·정렬·필터링이 내장된 **단일 독립 HTML 대시보드** | 웹 브라우저 정밀 분석, 팀 공유용 리포트 |
| `markdown` | 표와 코드 블록으로 포맷팅된 마크다운 | 이슈 티켓(Jira, GitHub), 장애 보고서 첨부 |
| `json` | 메타데이터, 패턴 목록, 슬롯 통계가 포함된 JSON | 타 분석 도구 및 자동화 파이프라인 연계 |
| `jsonl` | 줄바꿈 구분 JSON (한 줄당 한 클러스터) | 대용량 클러스터 데이터 스트리밍 처리 |

### 실행 예시
```bash
# 1. 브라우저에서 바로 열어볼 수 있는 대화형 HTML 리포트 생성
python trim.py app.log report.html --format html --top 2000

# 2. 장애 공유용 Markdown 표 생성
python trim.py app.log incident.md --format markdown

# 3. 자동화용 JSON 출력
python trim.py app.log report.json --format json
```

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
| `--no-multiline` | 멀티라인 활성 | Exception 스택 트레이스 자동 조립 비활성화 |
| `--rules <FILE>` | - | 사용자 정의 정규화 규칙 JSON 파일 |
| `--decode-errors` | `strict` | 텍스트 디코딩 에러 처리 (`strict`, `replace`) |
| `--max-input-bytes N` | 0 (무제한) | 처리할 최대 바이트 수 제한 (리소스 보호) |
