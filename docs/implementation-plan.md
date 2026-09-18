# Log Trimmer CLI Implementation Plan (v2)

> **For agentic workers:** REQUIRED IMPLEMENTATION ENTRY: Use superpowers:subagent-driven-development to implement this plan task-by-task with TDD. superpowers:executing-plans is invalid unless the user explicitly overrides this default; the override cannot weaken the frozen lock or TDD obligations. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 시스템 로그를 패턴 기반으로 유사도 트리밍하는 Python CLI 도구 개발. K8s, 노드, 파드 등 전체 시스템 로그를 입력받아 중복 패턴을 제거하고 발생 횟수를 카운트하여 압축된 로그 파일 출력.

**Architecture:**小包 구조로 모듈을 분리하되, 외부에서는 `trim.py` 단일 스크립트로 접근. 변수 감지(정규식+히어리스틱) → 패턴 정규화 → 유사도 비교(80~90% 임계값) → 그룹화 및 카운트 파이프라인.

**Tech Stack:** Python >= 3.10, stdlib + python-dateutil + rapidfuzz(선택), pytest

---

## 파일 구조

```
log-trimmer/
├─ trim.py                         # CLI 진입점: python trim.py input.txt output.txt
├─ logtrim/
│  ├─ __init__.py
│  ├─ cli.py                       # argparse, 메인 흐름 오케스트레이션
│  ├─ models.py                    # LogLine, LogPattern, TrimmedLog dataclass
│  ├─ patterns.py                  # 변수 감지 + 패턴 추출 (정규식 + 히어리스틱)
│  ├─ similarity.py                # 유사도 계산 (rapidfuzz / difflib fallback)
│  ├─ grouping.py                  # 그룹화 로직 (버킷 최적화)
│  ├─ io_utils.py                  # 파일/stdin 읽기, stdout/파일 쓰기
│  └─ report.py                    # 출력 포맷 (텍스트/JSON) + 요약 메타데이터
├─ tests/
│  ├─ __init__.py
│  ├─ test_models.py
│  ├─ test_patterns.py
│  ├─ test_similarity.py
│  ├─ test_grouping.py
│  └─ test_cli.py
├─ requirements.txt
└─ README.md
```

---

## Plan Contract Lock

**Approved Authority:** Seed v1.0.0 (`/home/user01/project/work/log/seed.yaml`, 2026-04-24)
**Governed Downstream Entry:** `superpowers:subagent-driven-development`
**Controlling Objective:** 로그 패턴 추출 + 유사도 그룹화 CLI 도구 구현
**Scope Boundary:**
- 포함: 로그 파일 읽기, 변수 자동 감지, 패턴 추출/정규화, 80~90% 유사도 그룹화, 트리밍 결과 출력, 단위 테스트
- 제외: 실시간 스트리밍, 외부 DB/서버 연동, GB 이상 배치, 웹 UI/API
**Explicit Prohibitions / Non-Goals:**
- pandas, numpy 등 무거운 의존성 금지
- asyncio 또는 멀티스레딩 불필요 (동기 처리)
- 커스텀 파서 작성 금지 (정규식 기반 패턴 추출 사용)
**Required Downstream Obligations:** TDD per task, task-by-task execution, spec compliance review, code quality review
**Ordering / Acceptance Constraints:** 각 태스크 완료 시 테스트 통과 필요. 최종: `python trim.py input.txt output.txt` 정상 실행, 압축률 50% 이상 목표.
**Invalidation Rule:** Seed 변경, scope 확장/축소, architecture 변경 시 재승인 필요.
**Branch Entry Constraint:** `log-trimmer` 브랜치, `.worktrees/log-trimmer` 워크트리에서 구현.

---

## Task 1: 프로젝트 초기화 및 models.py (seed ontology_schema 직접 참조)

**Files:**
- Create: `logtrim/__init__.py`
- Create: `logtrim/models.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`
- Create: `requirements.txt`

**Seed ontology_schema 매핑 (evidence — seed.yaml 직접 인용):**

```yaml
# seed.yaml ontology_schema (source: /home/user01/project/work/log/seed.yaml)
ontology_schema:
  - name: LogLine
    fields:
      - name: raw       (type: string)  → models.py LogLine.raw: str
      - name: pattern   (type: string)  → models.py LogLine.pattern: str
      - name: timestamp (type: datetime) → models.py LogLine.timestamp: datetime | None

  - name: LogPattern
    fields:
      - name: pattern    (type: string)  → models.py LogPattern.pattern: str
      - name: count      (type: int)     → models.py LogPattern.count: int
      - name: sample     (type: string)  → models.py LogPattern.sample: str
      - name: first_seen (type: datetime) → models.py LogPattern.first_seen: datetime | None
      - name: last_seen  (type: datetime) → models.py LogPattern.last_seen: datetime | None

  - name: TrimmedLog
    fields:
      - name: original_count    (type: int)      → models.py TrimmedLog.original_count: int
      - name: trimmed_count     (type: int)      → models.py TrimmedLog.trimmed_count: int
      - name: compression_ratio (type: float)    → models.py TrimmedLog.compression_ratio: float
      - name: patterns          (type: array)    → models.py TrimmedLog.patterns: list[LogPattern]
```

**Steps:**
- [ ] `logtrim/` 패키지 디렉토리 및 `__init__.py` 생성
- [ ] `tests/` 디렉토리 및 `__init__.py` 생성
- [ ] `requirements.txt`에 `python-dateutil`, `rapidfuzz`(선택) 명시
- [ ] `models.py`에 `LogLine`, `LogPattern`, `TrimmedLog` dataclass 정의 (seed.yaml ontology_schema 직접 참조)
- [ ] `test_models.py`에 dataclass 인스턴스화 테스트 작성
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 2: io_utils.py — 파일/stdin 읽기 및 출력

**Files:**
- Create: `logtrim/io_utils.py`
- Create: `tests/test_io_utils.py`

**Steps:**
- [ ] `io_utils.py`에 `iter_lines(path_or_stdin)` 제너레이터 함수 작성
- [ ] `io_utils.py`에 `write_output(lines, path)` 함수 작성
- [ ] stdin(`-`)과 파일 경로 모두 지원
- [ ] `test_io_utils.py`에 임시 파일 읽기/쓰기 테스트 작성
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 3: patterns.py — 변수 감지 및 패턴 추출 (기초, IPv6+URL 포함)

**Files:**
- Create: `logtrim/patterns.py`
- Create: `tests/test_patterns.py`

**Regex 순서 (IPv6, URL 포함):**
1. URL (http/https)
2. TIMESTAMP
3. UUID
4. MAC
5. IPV4
6. IPV6
7. PATH
8. DOMAIN
9. HEX
10. NUMBER
11. WHITESPACE CLEANUP

**Steps:**
- [ ] `patterns.py`에 변수 타입 정의 (TIMESTAMP, IPV4, IPV6, UUID, MAC, PORT, NUM, PATH, DOMAIN, HEX, HASH, ID, IDENT, URL)
- [ ] 각 타입별 정규식 패턴 정의 (IPv6, URL 포함)
- [ ] `extract_pattern(raw_line)` 함수: 변수를 `<TYPE>` 플레이스홀더로 교체
- [ ] 규칙 적용 순서 보장 (URL → TIMESTAMP → UUID → MAC → IPV4 → IPV6 → PATH → DOMAIN → HEX → NUMBER)
- [ ] `test_patterns.py`에 기본 변수 감지 테스트 (숫자, IP, UUID, IPv6, URL)
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 4: patterns.py — 히어리스틱 확장 및 timestamp 파싱

**Files:**
- Modify: `logtrim/patterns.py`
- Modify: `tests/test_patterns.py`

**Steps:**
- [ ] `dateutil.parser.parse` 통합하여 timestamp 파싱
- [ ] 히어리스틱 패턴 추가 (긴 숫자열, 혼합 식별자, 랜덤 문자열)
- [ ] timestamp 파싱 실패 시 `None` 반환 (에러 안 냄)
- [ ] `test_patterns.py`에 timestamp 파싱, 히어리스틱 테스트 추가
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 5: similarity.py — 유사도 계산

**Files:**
- Create: `logtrim/similarity.py`
- Create: `tests/test_similarity.py`

**Steps:**
- [ ] `similarity.py`에 `compute_similarity(a, b)` 함수 작성
- [ ] `rapidfuzz.fuzz.ratio` 우선, 미설치 시 `difflib.SequenceMatcher` fallback
- [ ] token-level 유사도 옵션 (공백 기준 분词 후 비교)
- [ ] `test_similarity.py`에 고Similar/중Similar/低Similar 테스트
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 6: grouping.py — 로그 그룹화

**Files:**
- Create: `logtrim/grouping.py`
- Create: `tests/test_grouping.py`

**Steps:**
- [ ] `grouping.py`에 `group_logs(lines, threshold=0.85)` 함수 작성
- [ ] 버킷 최적화: exact match 우선, 그 다음 유사도 비교
- [ ] `LogPattern` 인스턴스 생성 및 count 증가
- [ ] first_seen / last_seen 추적
- [ ] `test_grouping.py`에 완전 중복, 변수 다른 동일 패턴, 유사하지만 다른 패턴, 명확히 다른 패턴 테스트
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 7: report.py — 출력 포맷 (grouping 이후)

**Files:**
- Create: `logtrim/report.py`
- Create: `tests/test_report.py`

**Steps:**
- [ ] `report.py`에 `format_text(summary, patterns)` 함수 작성 (텍스트 포맷)
- [ ] `report.py`에 `format_json(summary, patterns)` 함수 작성 (JSON 포맷)
- [ ] 요약 메타데이터 포함: original_count, trimmed_count, compression_ratio
- [ ] **grouping.py 구현 이후에 배치** (이전 fail 해결)
- [ ] `test_report.py`에 출력 포맷 테스트
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 8: cli.py — CLI 오케스트레이션

**Files:**
- Create: `logtrim/cli.py`
- Create: `tests/test_cli.py`

**Steps:**
- [ ] `cli.py`에 argparse 기반 CLI 작성
- [ ] 인자: `input` (path or `-`), `output` (path or `-`), `--threshold`, `--format` (text/json)
- [ ] 흐름: read → extract_pattern → group → format → write
- [ ] 에러 처리: 파일 없음, 잘못된 threshold
- [ ] `test_cli.py`에 subprocess 기반 E2E 테스트
- [ ] 테스트 실행 및 통과 확인
- [ ] 커밋

---

## Task 9: trim.py — 진입점 스크립트

**Files:**
- Create: `trim.py`

**Steps:**
- [ ] `trim.py` 작성: `logtrim.cli.main()` 호출
- [ ] `if __name__ == "__main__":` 진입점
- [ ] PowerShell에서 `python trim.py input.txt output.txt` 실행 테스트
- [ ] 커밋

---

## Task 10: 통합 테스트 및 README

**Files:**
- Create: `README.md`
- Modify: `tests/test_cli.py`

**Steps:**
- [ ] K8s 시스템 로그 샘플 3종 준비 (kubelet, container runtime, pod scheduling)
- [ ] `test_cli.py`에 통합 테스트 추가 (샘플 로그 → 압축률 검증)
- [ ] README.md 작성: 설치, 사용법, 옵션, 예시
- [ ] 전체 테스트 스위트 실행
- [ ] 압축률 50% 이상 목표 검증
- [ ] 커밋

---

## Self-Review

- [x] Seed ontology_schema와 models.py 매핑 직접 참조 (seed.yaml 경로 명시, 매핑 evidence 기재)
- [x] acceptance_criteria 모든 항목 커버 (파일 읽기, 변수 감지, 유사도 그룹화, 출력, CLI 실행)
- [x] 타스크 분할 적정성 (각 2-5분, TDD 가능)
- [x] 의존성 순서 확인 (models → patterns → similarity → grouping → report → cli → trim)
- [x] 제약사항 준수 (stdlib + python-dateutil + rapidfuzz, 단일 스크립트 진입점)
- [x] 테스트 전략: 단위 테스트 + E2E + 샘플 데이터
- [x] regex 순서: URL → TIMESTAMP → UUID → MAC → IPV4 → IPV6 → PATH → DOMAIN → HEX → NUMBER → WHITESPACE (IPv6, URL 포함)
- [x] output writer(report.py)가 grouping(grouping.py) 이후로 배치됨
