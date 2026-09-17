Schema: iis-scope/v1
Project-Root: /home/user01/project/oracle
Status: done

## Product Authority
- /home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md sha256:b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6

## Transition Authority
- /home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md sha256:6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9

## Outcome
현재 Oracle Browser의 세션 복구 경로(`reattach.ts`의 `resumeBrowserSession` 및 `resumeBrowserSessionViaNewChrome`)는 프롬프트 프리뷰 텍스트의 부분 일치 및 대화 턴 인덱스 추정에 의존하고 있다. 이로 인해 다중 턴 대화 도중 네트워크 단절이나 프로세스 중단이 발생한 후 재연결 시, 현재 요청에 귀속된 답변이 아직 완성되지 않았거나 렌더링 중임에도 과거 턴의 이미 완료된 이전 답변을 현재 요청의 성공 결과로 오인하여 반환하는 치명적인 버그(False Success)가 발생할 수 있다.

본 Scope(Block 2: `B2-RESULT-ATTRIBUTION`)는 다음의 상태 변화를 달성한다:
1. **결과 귀속성 원천 보장 (Zero False Success in Recovery, GI-04, PI-05~PI-07)**:
   정상 브라우저 실행 경로뿐만 아니라 기존 Chrome reattach 및 새 Chrome recovery를 포함한 모든 복구 경로에서 성공 판정은 반드시 `same conversation ∧ uniquely identified current user turn ∧ assistant owned by that turn ∧ completed response` 결합 조건을 검증하도록 단일화한다.
2. **턴 식별자 영속화 및 전달 (HA-02, HA-03)**:
   정상 제출 시 확정되는 사용자 턴 및 어시스턴트 턴 식별자(`committedUserTurn`, `committedAssistantTurn`, `identityScope`)를 프로세스 메모리뿐만 아니라 세션 메타데이터(`BrowserRuntimeMetadata`)에 내구성 있게 기록하여, 프로세스 재시작 후 복구 시에도 동일한 식별자를 복원해 `waitForAssistantResponse`에 전달한다.
3. **과거 턴 오인 회수 및 텍스트 휴리스틱 의존 차단**:
   단순 텍스트 프리뷰 접두사 일치, 턴 번호 증가, 과거 완료 버튼/복사 버튼 존재 여부를 현재 요청 완료의 대체 증거로 인정하지 않는다. 대상 턴의 귀속 증거를 확인할 수 없는 경우 이전 턴을 성공으로 반환하지 않고 안전하게 `uncertain`/실패로 처리한다 (Fail-Closed).
4. **미확정 요청 재제출 억제 (HA-04)**:
   제출 가능성이 발생한 요청에 대해 복구 경로가 임의로 프롬프트를 재전송하지 않으며, 전송 시도와 커밋 확인, 답변 완료를 엄격히 분리하여 다중 과금 및 중복 질문을 방지한다.

### Includes
- `src/sessionManager.ts`의 `BrowserRuntimeMetadata`에 `identityScope` / `committedUserTurn` 영속화 필드 지원.
- `src/browser/reattach.ts`의 `resumeBrowserSession` 및 `resumeBrowserSessionViaNewChrome`에 `identityScope` 전달 및 `waitForAssistantResponse` 정합.
- `src/browser/actions/assistantResponse.ts`의 귀속 검증 강화.
- 다중 턴 환경에서 이전 턴 답변 오인 수거 차단 단위/회귀 테스트 추가.

### Excludes
- Block 3의 CLI 기본 2h 타임아웃 주입 및 CI pytest 파이프라인 연동.
- Block 4의 외부 격리 클린 환경 라이브 E2E 검증.

## Acceptance

### Scenario 1: Strict IdentityScope Verification in Existing-Chrome Reattach
- **Initial State**: 다중 턴 대화 세션에서 이전 턴(A)이 완료되고 새 요청(B)이 제출된 후 연결이 끊어진 상태. 세션 메타데이터에 B의 `identityScope`가 기록되어 있음.
- **Action**: `resumeBrowserSession`을 호출하여 복구를 시도한다.
- **Expected Result**: 복구 로직이 B의 고유 `identityScope`에 바인딩된 어시스턴트 응답만을 대기하며, A의 완료된 답변을 B의 성공으로 반환하지 않는다. B의 응답이 아직 없거나 완료되지 않은 경우 타임아웃 또는 실패로 닫힌다.

### Scenario 2: Parity in New-Chrome Session Recovery
- **Initial State**: 브라우저 프로세스가 종료되어 새 Chrome을 실행하여 복구해야 하는 다중 턴 세션.
- **Action**: `resumeBrowserSessionViaNewChrome`을 통해 복구를 수행한다.
- **Expected Result**: 기존 Chrome reattach와 완전히 동일한 `identityScope` 및 대화 식별자 검증 게이트를 통과해야만 성공하며, 텍스트 프리뷰 휴리스틱만으로 과거 턴을 성공 반환하지 않는다.

### Scenario 3: Fail-Closed on Ambiguous or Missing Attribution Evidence
- **Initial State**: 원격 대화에 동일한 텍스트의 이전 프롬프트가 존재하거나, 현재 요청 턴의 어시스턴트 소유권을 증명할 수 없는 상태.
- **Action**: 복구 프로세스를 실행한다.
- **Expected Result**: 과거 턴을 성공으로 취급하거나 프롬프트를 자동 재전송하지 않고, `uncertain` 또는 명시적 에러로 안전하게 종료(Fail-Closed)한다.
