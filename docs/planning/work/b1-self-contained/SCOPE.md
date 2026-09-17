Schema: iis-scope/v1
Project-Root: /home/user01/project/oracle
Status: done

## Product Authority
- /home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md sha256:b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6

## Transition Authority
- /home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md sha256:6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9

## Outcome
현재 Oracle Browser 슬롯 래퍼는 `runner.py`와 `attachments.py` 내부에 `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`이라는 개인 NVM 절대 경로를 하드코딩하고 있으며, 파일 선택 및 첨부 시 해당 개인 NVM의 비공개 모듈(`lib/node_modules/@steipete/oracle/dist/src/oracle/files.js`, `dist/src/cli/options.js`)을 파일시스템 경로 추론으로 동적 import하고 있다. 이로 인해 다른 사용자 계정, 다른 디렉터리, 또는 NVM이 없는 환경에서는 실행 자체가 불가능하거나 의존성이 깨지는 문제가 발생한다.

본 Scope(Block 1: `B1-RUNTIME-CLOSURE`)는 다음의 상태 변화를 달성한다:
1. **개인 NVM 및 사용자 홈 절대 경로 완전 제거**: `runner.py`, `attachments.py` 및 CLI 전반에서 `/home/user01/...` 및 고정 NVM 경로를 제거하고, 패키지 자체/설치 단위 상대 경로 또는 표준 환경변수/PATH 탐색을 통한 자기완결적 런타임 해석 메커니즘을 구축한다. (PI-01 준수: 실패 시 개인 경로로 돌아가는 비상 fallback 금지)
2. **외부 비공개 모듈 동적 import 차단 및 파일 선택기 내재화/표준화**: 상위 Node 디렉터리를 거슬러 올라가 비공개 `files.js`를 기웃거리던 방식을 제거하고, 동일 배포 단위 내부의 안정적 인터페이스 또는 자체 구현을 통해 기존 파일 선택 및 정규화 시맨틱을 보존한다. (PI-02, PI-03 준수)
3. **바이너리-선택기 릴리스 일체성 보장 (GI-05, HA-01)**: 호출된 `oracle` 실행물과 파일 선택/첨부 컴포넌트가 동일한 릴리스 단위/버전에 속함을 검증하며, 서로 다른 빌드가 임의로 조합되는 것을 차단한다.
4. **전제조건 미충족 시 사전 거절 (Fail-Closed)**: 지원 런타임(Node >= 24 등) 또는 필수 모듈이 누락되었거나 버전이 불일치할 경우, 원격 브라우저 제출 전에 구체적인 실패 원인과 함께 즉각 안전하게 거절한다.

### Includes
- `runner.py` 및 `attachments.py`의 `CANONICAL_ORACLE_CLI` 하드코딩 제거 및 자기완결적 resolver 구현.
- 외부 비공개 `dist/src/oracle/files.js` 동적 import 제거 및 제품 소유의 일체화된 파일 선택/압축 메커니즘 제공.
- 동일 릴리스/호환성 검증 로직 추가.
- 대체 설치 경로 / NVM 배제 환경에서의 비제출 스모크 및 단위 테스트 검증.

### Excludes
- Block 2의 `reattach.ts` 복구 경로 `identityScope` 필수화 및 Zero False Success 로직 (Block 2 범위).
- Block 3의 CLI 기본 2h 타임아웃 주입 및 CI 파이프라인 연동 (Block 3 범위).
- Block 4의 외부 클린 컨테이너/격리 환경 E2E 라이브 브라우저 제출 테스트 (Block 4 범위).

## Acceptance

### Scenario 1: Self-Contained CLI & Selector Resolution Without Personal Paths
- **Initial State**: `PATH` 및 환경변수에 `/home/user01`이나 특정 NVM 버전 경로가 노출되지 않은 상태.
- **Action**: 슬롯 래퍼 CLI(`prepare`, `status`, `run --dry-run`)를 실행한다.
- **Expected Result**: 개인 NVM 경로로의 폴백 없이 제품 자체 런타임 단위에서 `oracle` 실행물과 파일 선택기를 정확히 찾아내며, 버전 및 호환성 메타데이터가 동일 릴리스 단위로 일치하여 정상 실행된다.

### Scenario 2: Preservation of File-Bearing Selection & Single Compressed ZIP
- **Initial State**: 다중 파일 및 디렉터리 경로 인자가 포함된 파일 첨부 실행 요청.
- **Action**: 파일 선택 및 압축 전처리(`prepare_attachments`)를 수행한다.
- **Expected Result**: 외부 비공개 `files.js` import 없이도 기존 선택 시맨틱(중복 제거, 상대경로 보존)에 따라 정확히 하나의 압축 ZIP 파일이 생성되고, 첨부가 없는 요청에는 불필요한 ZIP이 생성되지 않는다.

### Scenario 3: Fail-Closed on Missing Preconditions or Mismatched Runtime
- **Initial State**: 지원되지 않는 Node 런타임 환경 또는 `oracle` 바이너리/모듈의 버전이 일치하지 않는 조작된 환경.
- **Action**: `run` 또는 `submit` 명령을 호출한다.
- **Expected Result**: 원격 브라우저 세션에 요청을 전송하기 전에 불일치 사실을 감지하고, 구체적인 진단 메시지와 함께 0이 아닌 종료 코드로 즉시 실패(Fail-closed)한다.
