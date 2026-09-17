Schema: iis-scope/v1
Project-Root: /home/user01/project/oracle
Status: done

## Product Authority
- /home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md sha256:b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6

## Transition Authority
- /home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md sha256:6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9

## Outcome
현재 Oracle Browser 슬롯 래퍼는 에이전트 운영 지침(`skills/oracle-browser/SKILL.md`)에 의존하여 `--browser-timeout 2h` 플래그 주입, 수동 사전 dry-run 검증, 그리고 특정 환경에서만 동작하는 검증 규칙들을 외부 호출자의 지식으로 요구하고 있다. 이로 인해 일반 터미널 사용자나 스케줄러가 CLI를 호출할 때 타임아웃이 2분(기본값)으로 짧게 설정되어 Pro 모델 응답 수거 도중 프로세스가 조기 종료되거나, 인자 및 환경 불일치를 원격 제출 시도 전에 걸러내지 못하는 문제가 존재한다. 또한 핵심 보호 계층인 파이썬 슬롯 래퍼 테스트가 GitHub CI 파이프라인에 연동되어 있지 않아 소스 변경 시 회귀가 자동으로 감지되지 않는다.

본 Scope(Block 3: `B3-CLI-PROTECTION`)는 다음의 상태 변화를 달성한다:
1. **기본 브라우저 응답 타임아웃 2시간 내재화 (PI-10, PI-11)**:
   외부 호출자가 `--browser-timeout`을 명시하지 않은 모든 정상 브라우저 실행(`run`, `submit`, `followup`)에 대해 CLI 래퍼가 기본값으로 `2h`(7200초)를 자동으로 적용한다. 호출자가 명시한 유효한 override 값은 그대로 존중하며 조용히 덮어쓰지 않는다.
2. **원격 제출 전 사전 검증(Pre-submission Guard)의 완전 자동 내재화 (PI-08, PI-09)**:
   별도의 수동 dry-run이나 preview 선행 없이도, 실제 실행 명령이 브라우저 원격 전송을 시도하기 전에 버전/호환성, 슬롯/인자 유효성, 첨부 파일 준비, 선택 슬롯의 실시간 CDP/로그인 상태를 자동으로 검증하여 미충족 시 exit code 2로 fail-closed 거절한다.
3. **공개 진입점 전반의 일관된 보호 계약 적용**:
   `run`, `submit`, `followup` 등 래퍼의 모든 공개 실행 경로가 동일한 타임아웃 기본값과 사전 검증 파이프라인을 통과하도록 보장한다.
4. **CI 파이프라인에 파이썬 래퍼 회귀 테스트 연동**:
   `.github/workflows/ci.yml`에 파이썬 슬롯 래퍼의 핵심 보호 회귀 테스트(`pytest tests/test_slots.py tests/test_followup.py`)를 필수 점검 단계로 통합하여 배포 및 머지 시 자동 검증 체계를 완성한다.

### Includes
- `runner.py`의 명령 정규화 및 validation 로직에 기본 `--browser-timeout 2h` 자동 주입 구현 (명시적 override 보존).
- `run`, `submit`, `followup` 진입점에서 실시간 pre-submit 검증 보장.
- `.github/workflows/ci.yml`에 Python 테스트 실행 스텝 추가.
- 관련 단위 테스트 및 CLI 호출 단위 테스트 추가.

### Excludes
- Block 4의 외부 클린 격리 컨테이너 환경에서의 종단간(E2E) 라이브 실행 검증 (Block 4 범위).

## Acceptance

### Scenario 1: Default 2h Timeout Injection Without Caller Flag
- **Initial State**: 호출자가 `--browser-timeout` 플래그를 전달하지 않고 실행한 `run` 또는 `submit` 명령.
- **Action**: 명령 정규화 및 실행 파이프라인을 구동한다.
- **Expected Result**: 생성된 child command 및 session options에 `--browser-timeout 2h`가 자동으로 주입되어 실행되며, 사용자가 명시적으로 `--browser-timeout 30m`을 넘긴 경우에는 `30m`이 보존된다.

### Scenario 2: Automatic Pre-Submission Guard Enforcement
- **Initial State**: 슬롯의 CDP가 미응답이거나 로그인되지 않은 상태, 또는 인자 조합이 유효하지 않은 상태.
- **Action**: 사용자가 사전 dry-run 없이 직접 `run` 또는 `submit` 명령을 실행한다.
- **Expected Result**: 원격 브라우저 세션에 요청을 제출하기 전 검증 단계에서 실패를 감지하고, 즉각 0이 아닌 종료 코드로 안전하게 거절(Fail-Closed)한다.

### Scenario 3: CI Python Test Suite Enforcement
- **Initial State**: 저장소의 GitHub Actions 워크플로 설정(`.github/workflows/ci.yml`).
- **Action**: CI 워크플로를 트리거하거나 로컬에서 정의된 테스트 파이프라인을 점검한다.
- **Expected Result**: Node 빌드/테스트뿐만 아니라 Python 래퍼 테스트(`pytest`)가 실행 단계에 포함되어 통과해야만 워크플로가 최종 성공으로 완료된다.
