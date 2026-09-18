# Plan Brief: Log Trimmer

## Goal
시스템 로그를 패턴 기반으로 유사도 트리밍하는 Python CLI 도구 개발

## Scope Boundaries
- **포함:** Python CLI 도구, 패턴 추출, 유사도 비교, 그룹화, 출력 파일 생성
- **제외:** 실시간 모니터링, 웹 UI, 데이터베이스, 네트워크 기능

## Repo-Local Constraints
- Python >= 3.10
- 표준 라이브러리 + python-dateutil, rapidfuzz(선택)만 사용
- 단일 스크립트 또는 소규모 패키지 구조
- 파워셸에서 `python trim.py input.txt output.txt` 로 실행 가능

## Required Files and Tests
- `trim.py` - 메인 CLI 스크립트
- `tests/test_pattern_extraction.py` - 패턴 추출 테스트
- `tests/test_similarity.py` - 유사도 계산 테스트
- `tests/test_grouping.py` - 그룹화 테스트
- `tests/test_cli.py` - CLI 인터페이스 테스트

## Explicit Prohibitions
- 외부 서버 또는 데이터베이스 사용 금지
- GUI 또는 웹 인터페이스 개발 금지
- 대용량 배치 처리 (수십 GB) 구현 금지
