# Scope — P0-1: Contract Freeze & Golden Test Fixtures

**Schema:** iis-scope/v1
**Status:** done
**Created:** 2026-09-17

---

## Product Authority

- **Thesis:** `docs/planning/product-thesis/logtrim/THESIS-001.md`

---

## Goal

logtrim의 단일 정본 제품 계약을 확정하고, 모든 후속 리팩터링과 기능 변경의 regression guard 역할을 하는 골든 테스트 스위트를 구축한다.

현재 가장 큰 제품 결함은 "무엇이 정답 출력인지에 대한 단일 Product Contract가 없다"는 점이다. 4/7 설계와 4/13 설계가 병존하고, README의 testing 섹션이 존재하지 않는 `tests/` 디렉터리를 참조하며, 어떤 입력에 대해 어떤 출력이 정답인지를 검증할 방법이 없다.

---

## Outcome

이 Scope가 완료되면 다음이 달성된다:

1. **정본 계약 확정:** 4/7 모델(통계 보존형)이 정본임을 코드·문서·테스트에서 일관되게 반영한다. 4/13 설계 문서에는 `SUPERSEDED` 표기를 추가한다.

2. **README 정합성:** README의 예제 출력이 실제 `logtrim` 실행 결과와 byte-for-byte 일치한다. README의 Testing 섹션이 실제로 실행 가능한 test 명령을 참조한다.

3. **Golden Test Fixtures:** 각 소스 패밀리(event, JSON, snapshot, describe, generic)에 대해 최소 1개의 골든 입력/출력 fixture pair가 존재하고, 테스트가 byte-for-byte 일치를 검증한다.

4. **Must-Merge / Must-Not-Merge Adversarial Corpus:**
   - **Must-Merge:** 동일 사건이 timestamp/PID/UUID만 다른 입력 pair → 같은 그룹으로 합쳐지는지 검증.
   - **Must-Not-Merge:** 서로 다른 component(nginx vs postgres), 서로 다른 에러(timeout vs connection refused, permission denied vs disk full) → 절대 합쳐지지 않는지 검증.

5. **Mixed-source Integration Fixture:** event + JSON + snapshot + describe + generic이 혼합된 단일 입력에서 패밀리 분리가 올바르게 동작하는지 검증하는 통합 테스트 fixture.

6. **`tests/` 디렉터리 복원:** `tests/` 디렉터리와 테스트 파일이 프로젝트에 존재하고, `python -m unittest discover -s tests -p "test_*.py" -v` 명령으로 실행 가능하다.

---

## Acceptance

### AC-1: 정본 계약 가시성

- `docs/superpowers/specs/2026-04-13-aggressive-trim-design.md` 파일이 존재하는 경우, 파일 상단에 `SUPERSEDED` 표기가 추가되어 있다.
  - 해당 파일이 존재하지 않는 경우 이 AC는 자동 충족된다. (현재 프로젝트에 포함되어 있지 않음.)
- `THESIS-001.md`의 Section 2에서 4/7 모델이 정본임을 명시하고, 근거를 제시한다.

### AC-2: README 예제 검증

- README의 "Examples" 섹션에 있는 event log 예제 입력을 `logtrim`에 실제 실행하면 README에 기재된 예제 출력과 동일한 결과가 나온다.
- README의 snapshot 예제도 동일하게 일치한다.
- 이 검증이 자동화된 테스트 케이스로 존재한다.

### AC-3: 패밀리별 Golden Fixture

- `tests/fixtures/` 하위에 최소 다음 fixture pair가 존재한다:
  - `event_input.txt` / `event_expected.txt`
  - `json_input.txt` / `json_expected.txt`
  - `snapshot_input.txt` / `snapshot_expected.txt`
  - `describe_input.txt` / `describe_expected.txt`
  - `generic_input.txt` / `generic_expected.txt`
  - `mixed_input.txt` / `mixed_expected.txt`
- 각 pair에 대해 `logtrim --input <input> --output <actual>` 실행 후 `<actual>`과 `<expected>`의 byte-for-byte 일치를 검증하는 테스트가 있다.

### AC-4: Must-Merge Corpus

- `tests/fixtures/` 하위에 Must-Merge 테스트 입력이 존재한다:
  - timestamp만 다른 동일 event 2건 이상 → 단일 그룹 (count >= 2)
  - PID만 다른 동일 event 2건 이상 → 단일 그룹
  - UUID만 다른 동일 JSON 2건 이상 → 단일 그룹
- 각 케이스에 대해 출력에서 해당 패턴의 count가 입력 건수와 일치함을 검증하는 테스트가 있다.

### AC-5: Must-Not-Merge Corpus

- `tests/fixtures/` 하위에 Must-Not-Merge 테스트 입력이 존재한다:
  - `nginx[1]: Failed to start` + `postgres[2]: Failed to start` → 2개 별도 그룹
  - `timeout` + `connection refused` → 2개 별도 그룹
  - `permission denied` + `disk full` → 2개 별도 그룹
- 각 케이스에 대해 출력에서 해당 패턴들이 서로 다른 그룹으로 존재함을 검증하는 테스트가 있다.
- **현재 코드의 `_PROC_PATTERN` 결함으로 인해 일부 Must-Not-Merge 케이스(nginx vs postgres)가 실패할 수 있다.** 이 경우 `_PROC_PATTERN`의 수정이 이 Scope에 포함된다. 수정 범위는 `normalize.py`의 `_PROC_PATTERN` regex만 변경하여 component name을 보존하도록 하는 것이며, 정규화 정책의 전면 재설계는 P0-3의 범위이다.

### AC-6: 테스트 실행 가능성

- 프로젝트 루트에서 `python -m unittest discover -s tests -p "test_*.py" -v` 실행 시 0 이상의 테스트가 발견되고, 모두 통과한다.
- 테스트 실행 시 ImportError나 ModuleNotFoundError가 발생하지 않는다.

---

## Open Decisions

- golden fixture의 구체적인 입력 데이터 내용은 구현 시 결정한다. 이 Scope는 fixture의 존재와 검증 메커니즘을 요구하되, 특정 로그 내용을 지정하지는 않는다.
- `_PROC_PATTERN` 수정의 구체적 regex는 구현 시 결정한다. 핵심 계약은 "component name 보존 + PID만 치환"이다.

---

## Non-Goals

- 정규화 정책의 전면 재설계 (P0-3 범위).
- Bounded-memory streaming 구현 (P0-2 범위).
- Snapshot의 readiness/restart 보존 확장 (P0-4 범위).
- CLI stdin/stdout 지원 (P1-1 범위).
- 4/13 aggressive mode의 구현.
- 배포 스크립트 수정.
- 성능 최적화.
