# Plan — P0-1: Contract Freeze & Golden Test Fixtures

**Schema:** iis-scope-plan/v1
**Scope:** `docs/planning/work/p0-contract-freeze/SCOPE.md`
**Thesis:** `docs/planning/product-thesis/logtrim/THESIS-001.md`
**Created:** 2026-09-17

---

## 개요

이 Plan은 P0-1 Scope의 6개 Acceptance Criteria를 달성하기 위한 구체적인 실행 방법을 정의한다.

작업은 3개 Phase로 나뉜다:

1. **Phase A: 계약 확정 및 정규화 수정** — 문서 정비와 `_PROC_PATTERN` 수정
2. **Phase B: Golden Fixture 생성** — 각 패밀리별 입출력 fixture pair 작성
3. **Phase C: 테스트 스위트 구축** — fixture 기반 자동화 테스트 작성 및 검증

---

## Phase A: 계약 확정 및 정규화 수정

### A-1: 4/13 설계 문서 SUPERSEDED 표기

**대상 파일:** `docs/superpowers/specs/2026-04-13-aggressive-trim-design.md`

- 해당 파일이 프로젝트에 존재하는 경우, 파일 최상단에 다음을 추가한다:

```markdown
> **SUPERSEDED:** 이 문서의 설계는 4/7 설계(2026-04-07-log-trimming-design.md)로 대체되었습니다.
> 향후 선택적 `--mode compact` 플래그로 일부 동작을 재도입할 수 있으나, 기본 동작은 4/7 모델을 따릅니다.
```

- 현재 프로젝트에 이 파일이 포함되어 있지 않으므로 (Oracle 트랜스크립트 참조 문서이며 코드와 함께 배포되지 않음), 이 단계는 **skip** 가능하다.
- **확인:** 파일 존재 여부를 `glob`으로 확인 후 결정.

### A-2: `_PROC_PATTERN` 수정 (Must-Not-Merge 선행 조건)

**대상 파일:** `logtrim/normalize.py`

**현재 문제:**

```python
# 현재 (line 8)
_PROC_PATTERN = re.compile(r"\b[\w.-]+\[\d+\](?=[^\w]|$)")
# 현재 치환 (line 37)
normalized = _PROC_PATTERN.sub("<PID>", normalized)
```

`nginx[1]` 전체를 `<PID>`로 치환하여 component identity를 소실시킨다.

**수정:**

```python
# 수정: PID 숫자만 치환하고 component name 보존
_PROC_PATTERN = re.compile(r"(\b[\w.-]+)\[(\d+)\]")

# 치환 함수 또는 치환 문자열
normalized = _PROC_PATTERN.sub(r"\1[<PID>]", normalized)
```

이 변경으로:
- `nginx[1]` → `nginx[<PID>]` (component name 보존)
- `postgres[2]` → `postgres[<PID>]` (component name 보존)
- `nginx[<PID>]`와 `postgres[<PID>]`는 서로 다른 normalized key → 별도 그룹

**영향 범위:**
- `normalize.py`만 변경. `_PROC_PATTERN`과 그 `sub()` 호출만 수정.
- 나머지 정규화 regex, grouping, render 로직은 변경 없음.
- 이 변경은 golden fixture의 기대 출력에 반영된다.

### A-3: README 예제 출력 검증 및 정합

**대상 파일:** `README.md`

- 현재 README의 Examples 섹션 (line 141-190)의 예제 입력을 실제 `logtrim`에 실행하여 출력을 확인한다.
- A-2의 `_PROC_PATTERN` 수정 후, 예제의 `<PID>`가 `app[<PID>]`로 변경되므로 README 예제 출력을 실제 출력에 맞춰 갱신한다.

**예상 변경:**

README line 156의 `<TS> <PID>: Failed to start`가 A-2 수정 후 `<TS> app[<PID>]: Failed to start`로 변경될 것이므로 README를 이에 맞춰 업데이트한다.

---

## Phase B: Golden Fixture 생성

### 디렉터리 구조

```
tests/
  __init__.py               (빈 파일)
  fixtures/
    event_input.txt
    event_expected.txt
    json_input.txt
    json_expected.txt
    snapshot_input.txt
    snapshot_expected.txt
    describe_input.txt
    describe_expected.txt
    generic_input.txt
    generic_expected.txt
    mixed_input.txt
    mixed_expected.txt
    must_merge_input.txt
    must_merge_expected.txt
    must_not_merge_input.txt
    must_not_merge_expected.txt
  test_golden.py            (AC-3 검증)
  test_merge_contract.py    (AC-4, AC-5 검증)
  test_readme_examples.py   (AC-2 검증)
```

### B-1: Event Fixture

**`event_input.txt`:**

다음을 포함하는 event stream 입력:
- timestamp-prefixed 이벤트 2건 이상 (동일 메시지, 다른 timestamp)
- multiline stack trace 포함 이벤트 1건 이상
- 서로 다른 component의 이벤트

**`event_expected.txt`:**

`logtrim`의 실제 출력. A-2 수정 적용 후의 정규화 결과.

### B-2: JSON Fixture

**`json_input.txt`:**

- 동일 구조의 JSON 로그 2건 이상 (`request_id`, `ts` 만 다름)
- 서로 다른 메시지의 JSON 로그 1건 이상

**`json_expected.txt`:**

field-order independent canonicalization이 적용된 grouping 결과.

### B-3: Snapshot Fixture

**`snapshot_input.txt`:**

```text
NAME                          READY   STATUS    RESTARTS   AGE
api-7c9d8f6b7c-abc12         1/1     Running   0          2d
api-7c9d8f6b7c-def34         0/1     CrashLoopBackOff   4   2d
web-5f4d3c2b1a-ghi56         1/1     Running   0          1d
```

**`snapshot_expected.txt`:**

현재 코드의 실제 출력 (STATUS 기준 grouping, P0-4에서 readiness/restart 확장).

### B-4: Describe Fixture

**`describe_input.txt`:**

`kubectl describe pod` 스타일의 대표적인 sectioned 출력. `Name:`, `Namespace:`, `Labels:`, `Events:` 등의 anchor를 포함.

**`describe_expected.txt`:**

현재 `summarize_describe()`의 실제 출력.

### B-5: Generic Fixture

**`generic_input.txt`:**

어떤 패밀리에도 분류되지 않는 일반 텍스트.

**`generic_expected.txt`:**

`Generic Text` 헤더 없이 원본 텍스트 그대로 (단일 generic-only 입력이므로 헤더 제거 정책 적용).

### B-6: Mixed Fixture

**`mixed_input.txt`:**

event + JSON + snapshot + describe + generic이 순서대로 포함된 단일 파일.

**`mixed_expected.txt`:**

각 패밀리 섹션이 올바르게 분리되어 해당 타이틀과 함께 출력된 결과.

### B-7: Must-Merge Fixture

**`must_merge_input.txt`:**

```text
2026-04-07T11:00:00Z app[1]: Connection timeout to db-host
2026-04-07T11:00:05Z app[2]: Connection timeout to db-host
2026-04-07T11:00:10Z app[3]: Connection timeout to db-host
```

**검증:** 출력에서 `count: 3`인 단일 그룹이 존재.

### B-8: Must-Not-Merge Fixture

**`must_not_merge_input.txt`:**

```text
2026-04-07T11:00:00Z nginx[1]: Failed to start
2026-04-07T11:00:01Z postgres[2]: Failed to start
2026-04-07T11:00:02Z app[3]: Connection timeout
2026-04-07T11:00:03Z app[4]: Connection refused
```

**검증:** 출력에서 4개의 별도 그룹 (또는 최소 nginx와 postgres가 별도, timeout과 refused가 별도).

### Fixture 생성 방법

모든 expected 파일은 **실제 `logtrim` 실행 결과를 캡처**하여 생성한다. 수동 작성이 아니라, A-2 수정 적용 후의 실제 프로그램 출력을 기록한다.

단, Must-Not-Merge fixture의 expected는 프로그램 출력 캡처 후 별도 그룹 존재를 수작업으로 확인한다.

---

## Phase C: 테스트 스위트 구축

### C-1: `test_golden.py` (AC-3, AC-6)

```python
class TestGoldenFixtures(unittest.TestCase):
    """각 패밀리별 golden fixture의 byte-for-byte 일치 검증."""

    # 파라미터화: event, json, snapshot, describe, generic, mixed
    # 각 케이스:
    #   1. fixture input을 임시 파일로 복사
    #   2. logtrim.cli.main(["--input", input_path, "--output", output_path]) 실행
    #   3. output_path 내용과 expected fixture byte-for-byte 비교
```

### C-2: `test_merge_contract.py` (AC-4, AC-5)

```python
class TestMustMerge(unittest.TestCase):
    """동일 사건의 variable-only 차이가 올바르게 합쳐지는지 검증."""
    # must_merge fixture 실행 후 출력에서 count >= 2 그룹 존재 확인

class TestMustNotMerge(unittest.TestCase):
    """서로 다른 사건이 절대 합쳐지지 않는지 검증."""
    # must_not_merge fixture 실행 후 출력에서 별도 그룹 존재 확인
    # nginx와 postgres가 각각 별도 패턴으로 존재하는지 text 검증
```

### C-3: `test_readme_examples.py` (AC-2)

```python
class TestReadmeExamples(unittest.TestCase):
    """README의 예제 입출력이 실제 logtrim 실행과 일치하는지 검증."""
    # README에서 추출한 예제 입력으로 logtrim 실행
    # 실제 출력과 README 예제 출력 비교
```

---

## Self-Check

구현 완료 후 다음을 확인:

1. `python -m unittest discover -s tests -p "test_*.py" -v` — 모든 테스트 통과, 0 failures.
2. `logtrim --input tests/fixtures/must_not_merge_input.txt --output /tmp/mnm_out.txt && cat /tmp/mnm_out.txt` — nginx와 postgres가 별도 그룹.
3. `logtrim --input tests/fixtures/must_merge_input.txt --output /tmp/mm_out.txt && cat /tmp/mm_out.txt` — count: 3인 단일 그룹.
4. `logtrim --input tests/fixtures/mixed_input.txt --output /tmp/mixed_out.txt && cat /tmp/mixed_out.txt` — 5개 패밀리 섹션이 올바르게 분리.

---

## 후속 Scope 연결

이 Scope가 완료되면:

- **P0-2 (Bounded-Memory Streaming):** golden fixture가 regression guard 역할. `pipeline.py`의 `current_lines` 배치 버퍼를 incremental aggregator로 교체해도 golden output이 유지됨을 검증할 수 있다.
- **P0-3 (Normalization Safety):** must-merge/must-not-merge corpus가 정규화 regex 변경 시의 양방향 regression guard 역할. 새 regex를 추가하거나 변경할 때마다 양쪽 스위트를 모두 통과해야 한다.
- **P0-4 (Snapshot/Describe Semantic Preservation):** snapshot/describe golden fixture가 기준선 역할. readiness/restart 보존 확장 시 golden output이 업데이트되지만, 기존 정보가 손실되지 않음을 검증.
