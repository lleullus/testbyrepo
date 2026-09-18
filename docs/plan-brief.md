# Plan Brief: Log Trimmer CLI

## Goal
시스템 로그를 패턴 기반으로 유사도 트리밍하는 Python CLI 도구 (`trim.py`) 개발.
K8s, 노드, 파드 등 전체 시스템 로그를 입력받아 중복 패턴을 제거하고 발생 횟수를 카운트하여 압축된 로그 파일 출력.

## Scope Boundaries
- **포함:**
  - 로그 파일 읽기 (path 또는 stdin)
  - 변수 부분 자동 감지 (숫자, IP, UUID, MAC, 경로, 도메인, 타임스탬프 등)
  - 패턴 추출 및 정규화
  - 유사도 80~90% 기준으로 로그 그룹화
  - 트리밍 결과 출력 (패턴 + 발생 횟수 + 요약 메타데이터)
  - 단위 테스트
- **제외:**
  - 실시간 스트리밍 처리
  - 외부 저장소 (DB, S3 등) 연동
  - 대용량 배치 (GB 이상) 처리
  - 웹 UI 또는 API

## Repo-Local Constraints
- Python >= 3.10
- 표준 라이브러리 + `python-dateutil`, `rapidfuzz`(선택)만 사용
- 단일 스크립트 또는 소규모 패키지 구조
- 실행 명령: `python trim.py input.txt output.txt`
- 소규모 배치 처리 대상 (수 MB ~ 수백 MB)

## Required Files
- `trim.py` - 메인 CLI 스크립트
- `tests/test_trim.py` - 단위 테스트
- (선택) `README.md` - 사용법 문서

## Explicit Prohibitions
- 외부 DB 또는 서버 사용 금지
- pandas, numpy 등 무거운 의존성 금지
- asyncio 또는 멀티스레딩 불필요 (동기 처리)
- 커스텀 파서 작성 금지 (정규식 기반 패턴 추출 사용)

## Acceptance Criteria
- `python trim.py input.txt output.txt` 실행 시 정상 출력 생성
- 출력 파일에 카운트 포함 패턴 로그 기록
- 유사도 임계값 80~90%에서 논리적 그룹화 검증 완료
- 로컬 테스트 통과
- 압축률 50% 이상 목표
