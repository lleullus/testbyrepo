# Reset Plan: Log Trimmer CLI Implementation Plan (v2)

## Target Artifact
docs/implementation-plan.md

## Artifact Type
Implementation plan (TDD task plan)

## Revision Number
v2

## Next Draft Owner
main agent

## Goal
Seed ontology_schema를 직접 참조하여 models.py 매핑을 검증하고, regex 순서(IPv6, URL 포함)에 dedicated 태스크를 배정하며, output writer를 grouping 이후로 재배치한 fresh 구현 계획 작성.

## Rewrite Map
```
# Log Trimmer CLI Implementation Plan (v2)
> For agentic workers header
Goal / Architecture / Tech Stack
파일 구조
Plan Contract Lock
Task 1: 프로젝트 초기화 및 models.py (seed ontology_schema 직접 참조)
Task 2: io_utils.py
Task 3-4: patterns.py 기초 (TIMESTAMP, UUID, MAC, IPV4, IPV6, PATH, DOMAIN, HEX, NUMBER)
Task 5: patterns.py URL + 히어리스틱
Task 6: similarity.py
Task 7: grouping.py
Task 8: report.py (output writer — grouping 이후)
Task 9: cli.py
Task 10: trim.py 진입점
Task 11: 통합 테스트 및 README
Self-Review
```

## Per-Section Instructions

### Goal / Architecture / Tech Stack
- Goal: Seed goal과 완전히 일치 (시스템 로그 패턴 기반 유사도 트리밍 CLI)
- Architecture:小包 구조 (logtrim 패키지 + trim.py 진입점)
- Tech Stack: Python >= 3.10, stdlib + python-dateutil + rapidfuzz(선택)

### 파일 구조
- logtrim/__init__.py, cli.py, models.py, patterns.py, similarity.py, grouping.py, io_utils.py, report.py
- tests/__init__.py, test_models.py, test_patterns.py, test_similarity.py, test_grouping.py, test_cli.py, test_report.py
- trim.py, requirements.txt, README.md

### Plan Contract Lock
- Approved Authority: Seed v1.0.0 (seed.yaml, 2026-04-24) — **seed.yaml 파일 경로 명시**
- Governed Downstream Entry: superpowers:subagent-driven-development
- Controlling Objective: 로그 패턴 추출 + 유사도 그룹화 CLI 도구 구현
- Scope Boundary: 포함/제외 항목 명시
- Explicit Prohibitions / Non-Goals: pandas/numpy/asyncio/DB client 금지 명시
- Required Downstream Obligations: TDD per task, task-by-task execution
- Ordering / Acceptance Constraints: 각 태스크 완료 시 테스트 통과
- Invalidation Rule: Seed 변경, scope 확장/축소 시 재승인
- Branch Entry Constraint: log-trimmer 브랜치, .worktrees/log-trimmer 워크트리

### Task 1: 프로젝트 초기화 및 models.py (seed ontology_schema 직접 참조)
- **seed.yaml ontology_schema 직접 참조하여 매핑 기재:**
  - LogLine (raw, pattern, timestamp) → models.py LogLine dataclass
  - LogPattern (pattern, count, sample, first_seen, last_seen) → models.py LogPattern dataclass
  - TrimmedLog (patterns, original_count, trimmed_count, compression_ratio) → models.py TrimmedLog dataclass
- Files: logtrim/__init__.py, logtrim/models.py, tests/__init__.py, tests/test_models.py, requirements.txt
- Steps: 패키지 생성 → dataclass 정의 (seed ontology_schema 참조) → 테스트 작성 → 통과 확인 → 커밋

### Task 2: io_utils.py — 파일/stdin 읽기 및 출력
- Files: logtrim/io_utils.py, tests/test_io_utils.py
- Steps: iter_lines(path_or_stdin) 제너레이터 → write_output(lines, path) → stdin("-") 지원 → 테스트 → 통과 → 커밋

### Task 3: patterns.py — 변수 감지 및 패턴 추출 (기초)
- regex 순서: TIMESTAMP → UUID → MAC → IPV4 → IPV6 → PATH → DOMAIN → HEX → NUMBER
- **IPv6 및 URL 포함** (이전 fail 해결)
- Files: logtrim/patterns.py, tests/test_patterns.py
- Steps: 변수 타입 정의 → 각 타입별 regex → extract_pattern(raw_line) → 순서 보장 → 테스트 → 통과 → 커밋

### Task 4: patterns.py — URL + 히어리스틱 확장
- URL 정규화 (http/https URL → <URL>)
- 히어리스틱: 긴 숫자열 → <NUM>, 혼합 식별자 → <IDENT>, 랜덤 문자열 → <ID>
- timestamp 파싱 (dateutil.parser.parse)
- Files: logtrim/patterns.py, tests/test_patterns.py
- Steps: URL regex → 히어리스틱 → timestamp 파싱 → 테스트 → 통과 → 커밋

### Task 5: similarity.py — 유사도 계산
- Files: logtrim/similarity.py, tests/test_similarity.py
- Steps: compute_similarity(a, b) → rapidfuzz.fuzz.ratio 우선, difflib fallback → token-level 유사도 옵션 → 테스트 → 통과 → 커밋

### Task 6: grouping.py — 로그 그룹화
- Files: logtrim/grouping.py, tests/test_grouping.py
- Steps: group_logs(lines, threshold=0.85) → 버킷 최적화 (exact match 우선) → LogPattern 인스턴스 생성 및 count 증가 → first_seen/last_seen 추적 → 테스트 → 통과 → 커밋

### Task 7: report.py — 출력 포맷 (grouping 이후)
- **grouping.py 이후에 위치** (이전 fail 해결)
- Files: logtrim/report.py, tests/test_report.py
- Steps: format_text(summary, patterns) → format_json(summary, patterns) → 요약 메타데이터 포함 → 테스트 → 통과 → 커밋

### Task 8: cli.py — CLI 오케스트레이션
- Files: logtrim/cli.py, tests/test_cli.py
- Steps: argparse 기반 CLI → 인자: input, output, --threshold, --format → 흐름: read → extract_pattern → group → format → write → 에러 처리 → 테스트 → 통과 → 커밋

### Task 9: trim.py — 진입점 스크립트
- Files: trim.py
- Steps: logtrim.cli.main() 호출 → if __name__ == "__main__:" 진입점 → PowerShell 실행 테스트 → 커밋

### Task 10: 통합 테스트 및 README
- Files: README.md, tests/test_cli.py
- Steps: K8s 샘플 로그 3종 → 통합 테스트 → README 작성 → 전체 테스트 스위트 실행 → 압축률 50% 이상 검증 → 커밋

### Self-Review
- [x] Seed ontology_schema와 models.py 매핑 직접 참조 (evidence 명시)
- [x] acceptance_criteria 모든 항목 커버
- [x] 타스크 분할 적정성 (각 2-5분, TDD 가능)
- [x] 의존성 순서 확인 (models → patterns → similarity → grouping → report → cli → trim)
- [x] 제약사항 준수
- [x] 테스트 전략
- [x] regex 순서: URL → TIMESTAMP → UUID → MAC → IPV4 → IPV6 → PATH → DOMAIN → HEX → NUMBER → WHITESPACE (IPv6, URL 포함)

## Explicit Prohibitions
- evidence 없는 seed ontology_schema 주장 금지 (Task 1에서 직접 참조)
- IPv6/URL 미포함 regex 순서 금지 (Task 3-4에서 포함)
- output writer → grouping 이전 ordering 금지 (Task 7에서 grouping 이후로 배치)

## Drafting Checks
- Task 1에서 seed.yaml ontology_schema를 직접 참조하여 models.py 매핑이 명시적으로 기재되었는가?
- regex 순서에 IPv6와 URL이 포함되었는가?
- output writer(report.py)가 grouping(grouping.py) 이후에 배치되었는가?
- 각 태스크가 2-5 분 분량인가?
- Self-Review에서 모든 fail anchor가 해결되었는가?
