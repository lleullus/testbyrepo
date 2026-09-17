Schema: iis-scope/v1
Project-Root: /home/user01/project/oracle
Status: ready

## Product Authority
- /home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md sha256:b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6

## Transition Authority
- /home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md sha256:6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9

## Outcome
B1(런타임 자기완결성), B2(결과 귀속성/Zero False Success), B3(CLI 내장 보호 및 CI)의 개별 구현과 단위 검증이 완료되었으나, 실제 패키징된 배포 후보물(Release Candidate)이 원 개발자의 환경(`/home/user01`, 개인 NVM, 소스 체크아웃)이 전혀 없는 깨끗한 격리 지원 환경에서도 스스로 정체성을 입증하며 전체 제품 수명주기를 완결할 수 있는지에 대한 종단간(E2E) 증거가 필요하다.

본 Scope(Block 4: `B4-CLEAN-E2E`)는 다음의 상태 변화를 달성한다:
1. **클린 격리 환경에서의 패키징 및 설치 런타임 수명주기 검증 (PI-14)**:
   원 개발자의 개인 NVM 및 개발 디렉터리가 격리된 임시 클린 디렉터리/환경에서 실제 빌드·패키징된 실행물을 설치하고, 제품이 자신의 릴리스 정체성을 스스로 증명하며 CLI 명령을 정상 구동함을 입증한다.
2. **무첨부 및 첨부 파일 요청의 정상 실행과 결과 보존**:
   첨부 없는 일반 브라우저 요청과 다중 파일이 첨부된 요청이 단일 압축 ZIP 생성 규칙을 준수하며 정상 실행되고, 사전 검증과 기본 2시간 타임아웃 하에 정확한 응답을 수거·보존함을 확인한다.
3. **슬롯 배타 점유 및 수명주기 안전성 확인**:
   요청 실행 중 슬롯 배타 점유, 비정상 종료 시 안전한 상태 격리 및 복구 수명주기가 닫힘을 확인한다.

### Includes
- 패키징된 배포 아티팩트(`dist` 및 wheel 패키지) 기반 격리 설치 및 실행 스모크 스크립트.
- 첨부/무첨부 브라우저 실행 명령 정규화 및 슬롯 점유-해제 수명주기 E2E 검증.
- 개발자 홈 환경 격리 하에서의 CLI 정상 구동 확인.

### Excludes
- 상용 npm 레지스트리 공개 배포(Publish) 실행.
- 비지원 OS(Windows Native, macOS 등) 전용 인스톨러 생성.

## Acceptance

### Scenario 1: Clean Environment Installation & Provenance Readback
- **Initial State**: `/home/user01` 및 개인 NVM 경로가 `PATH`에서 배제된 독립된 임시 설치 접두사(Clean Prefix).
- **Action**: 패키징된 바이너리를 설치하고 `status`, `prepare`, `run --dry-run`을 호출한다.
- **Expected Result**: 개인 경로 의존 없이 제품 자체 런타임에서 실행물과 선택기가 정상 해석되며, 동일한 릴리스 버전(`0.16.1`) 및 스키마를 증명하고 0으로 종료된다.

### Scenario 2: End-to-End File Attachment Normalization & Single ZIP Preservation
- **Initial State**: 격리된 클린 환경에서 복수의 파일 인자를 포함한 실행 요청.
- **Action**: 슬롯 래퍼를 통해 파일 첨부 준비 및 실행 정규화를 수행한다.
- **Expected Result**: 정확히 하나의 압축 ZIP 파일이 생성되고 상대 경로가 보존되며, 첨부 없는 요청에는 인위적인 ZIP이 생성되지 않고 깨끗하게 처리된다.

### Scenario 3: Closed Slot Lifecycle & Precondition Rejection Under Clean Runtime
- **Initial State**: 슬롯의 CDP 엔드포인트가 준비되지 않았거나 유효하지 않은 인자가 전달된 격리 환경.
- **Action**: 실행 명령(`run` 또는 `submit`)을 호출한다.
- **Expected Result**: 원격 브라우저 세션에 요청을 제출하기 전에 실패를 감지하고, 슬롯을 오염시키지 않은 채 exit code 2로 즉각 안전하게 거절(Fail-Closed)한다.
