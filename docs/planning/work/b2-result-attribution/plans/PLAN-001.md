# PLAN-001 — B2 Result Attribution 실행 방법

Plan 역할: 이 문서는 `B2-RESULT-ATTRIBUTION` Scope를 구현하고 구현자 자체 점검으로 넘기기 위한 방법이다. 제품 의미, Acceptance 또는 검증 판정을 새로 정의하지 않는다.

## 1. 결합된 권위와 현재성

- Product Thesis: `/home/user01/project/oracle/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md`, SHA-256 `b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6`.
  - 목적/완전한 루프: 사용자는 정상 실행과 중단 복구 모두에서 의도한 conversation과 현재 요청 턴의 완결 결과를 믿고 회수해야 한다(Reason to Exist, Core Completion Loop 4~8).
  - false-success 경계: `success ⇒ same conversation ∧ uniquely identified current user turn ∧ assistant owned by that turn ∧ completed response`; 턴 순서, prompt 유사성, 마지막 답변, 과거 copy button은 대체 증거가 아니다(Behavior §5, Truth/Causal Invariant 4).
  - 실패/복구 의미: 제출 가능성이 생겼으나 commit/귀속을 증명하지 못하면 자동 재제출하지 않고 `uncertain`/failure로 닫으며 기존 자료를 보존한다. 완결 답변과 후처리 실패도 분리한다.
  - authoritative success readback: 실제 원격 conversation/turn 관찰, 저장된 session `meta.json`/답변, 호출자 결과를 함께 대조해야 하며 내부 반환값이나 단위 테스트만으로 실제 외부 결과를 증명하지 않는다(Success Observation B/C/F).
- Scope: `/home/user01/project/oracle/docs/planning/work/b2-result-attribution/SCOPE.md`, SHA-256 `ecb71fde29ed90f96f9c752d3cfd82524f61e1276d6f90733bd58c065eafb487`, `Schema: iis-scope/v1`, `Status: ready`.
  - canonical validator 실행 결과: `VALID`/JSON status `ready`; Product/Transition Authority의 실제 바이트 digest가 Scope 기록과 일치했다.
- Transition Authority: `/home/user01/project/oracle/docs/planning/adaptive/maintainable-operational-runtime/BASELINE-001.md`, SHA-256 `6e4d81d83c18d21ec8f1d3e60f671bd2d3db07e0a8699507009e91e953b5d1a9`.
  - 적용 범위는 Block `B2-RESULT-ATTRIBUTION`, `GI-02`~`GI-04`, `GI-06`, `GI-09`~`GI-10`, `PI-05`~`PI-07`, `PI-12`~`PI-13`, `HA-02`~`HA-04`다.
  - identity writer/recovery reader와 existing-/new-Chrome success gate는 한 runnable cut에서 닫혀야 한다. 중간 commit은 가능하지만 writer-only 또는 한 recovery path만 강화한 상태를 production candidate/Exit로 발표하지 않는다.
  - 원문 자체는 `Status: DRAFT`, `Approved by: Pending`, `Inter-Block auto-continuation authorized: no`다. Scope가 결합한 불변식과 HARD_ATOMIC 제약은 이 Plan에서 보존하지만, 이 문서나 Plan은 B1 Exit, B2 transition Exit, 외부 실행 또는 다음 Block 진행 권한을 만들지 않는다.
- Repository investigation: supplied artifact 없음. 아래 현재 소스를 직접 읽어 method grounding으로 사용했다.

## 2. 달성할 관찰과 보존 경계

### Scope 결과

1. 정상 제출이 확정한 현재 user-turn identity와 이후 결합된 assistant-turn identity를 세션 `BrowserRuntimeMetadata`에 내구 저장한다.
2. 기존 Chrome reattach와 새 Chrome recovery가 동일한 저장 identity와 동일 conversation을 `waitForAssistantResponse`/Deep Research 완료 판정에 전달한다.
3. 복구 성공은 오직 저장된 current user turn에 유일하게 소유된 assistant turn의 완결 증거에서만 나온다. identity가 없거나, malformed/conflicting하거나, 원격 DOM에 유일하게 match되지 않거나, completion을 입증하지 못하면 명시적 attribution error/timeout으로 닫는다.
4. 복구는 prompt를 제출하지 않는다. `promptSubmitted`의 true/false/부재, prompt preview, turn index는 재제출 허가 또는 성공 증거가 아니다.

### 보존 및 Non-Goals

- 정상 제출의 모델/Power, 첨부, follow-up, Deep Research 동작은 결과 귀속 gate를 약화하지 않는 범위에서 보존한다.
- 이미 귀속 확정된 답변은 후처리/slot release 실패 때문에 삭제하거나 재제출하지 않는다.
- Block 3의 CLI 기본 `2h`/CI 연결과 Block 4의 clean-environment E2E는 구현 범위가 아니다.
- 새 DB, telemetry, latest-answer fallback, legacy 성공 shim, prompt-text 기반 호환 fallback을 추가하지 않는다.

## 3. Code Grounding

### EXISTING

1. **정상 제출 identity 생성과 메모리 gate**
   - `src/browser/actions/promptComposer.ts:241-275, 906-984`는 send-attempt callback 뒤 원격 user turn commit을 별도 검증하고 `committedUserTurn`을 반환한다.
   - `src/browser/providers/chatgptDomProvider.ts:46-87`는 그 값을 provider state에 두고, 응답 대기 시 `{ committedUserTurn, committedAssistantTurn }`을 구성한다.
   - `src/browser/index.ts:741-762, 1773-1867, 3453-3517`는 submission 결과로 process-local `identityScope`를 만들며 정상 응답 경로에 전달한다.
   - `src/browser/actions/assistantResponse.ts:246-366`는 저장 user identity의 유일 match와 그 다음 owned assistant identity를 찾는다. assistant identity가 이미 있으면 그것을 우선한다.
   - `assistantResponse.ts:369-563, 954-1049, 1117-1250, 1437-1545`는 identityScope가 있을 때 snapshot/observer/completion/extractor를 같은 scoped resolver로 제한하며 불완전 응답을 완료로 발표하지 않는다.
2. **현재 내구 writer 경로**
   - `src/browser/index.ts:1040-1094, 3086-3125`의 runtime hint에는 Chrome/conversation와 `promptSubmitted`만 있고 turn identity가 없다.
   - `markPromptSubmitted`는 send-attempt 직후 hint를 쓰지만 commit 검증 후 다시 호출하면 이미 true라 no-op이다. 즉 commit identity가 확정돼도 그 시점의 내구 write가 없다.
   - `src/browser/sessionRunner.ts:149-244` → `src/cli/sessionRunner.ts:120-160` → `src/sessionManager.ts:692-702`가 runtime hint를 세션 `meta.json`의 `browser.runtime`으로 저장하는 실제 writer/readback 경로다.
3. **현재 저장 schema와 수명**
   - `src/sessionManager.ts:125-140`의 `BrowserRuntimeMetadata`에는 conversation/Chrome/`promptSubmitted`만 있고 turn identity가 없다.
   - `src/sessionManager.ts:109-123, 656-702, 710-727`는 browser metadata를 JSON으로 저장하고 다시 읽는다. identity를 제거하는 sanitizer는 없으므로 schema와 writer를 연결하면 동일 `meta.json` 수명 동안 유지할 수 있다.
4. **현재 recovery read/decision path**
   - entry readers는 `src/cli/sessionDisplay.ts:277-370`의 명시 reattach와 `src/cli/sessionRunner.ts:1178-1345`의 auto-reattach다. 둘 다 저장 `browser.runtime`을 `resumeBrowserSession`에 넘기고 반환값만으로 session을 `completed`로 갱신한다.
   - `src/browser/reattach.ts:62-227`의 existing-Chrome path와 `267-413`의 new-Chrome path는 모두 prompt preview/turn index를 계산하고 `waitForAssistantResponse(Runtime, ..., minTurnIndex)`를 호출한다. `expectedConversationId`와 `identityScope`를 넘기지 않는다.
   - existing-Chrome path의 모든 오류는 new-Chrome recovery로 이어지므로 두 경로의 gate가 동일하지 않으면 fallback에서 의미가 약해질 수 있다.
   - `reattach.ts:416-444`는 prompt 첫 120자의 부분/포함 일치로 마지막 user turn index를 고른다. 동일 prompt/preview prefix를 유일 identity로 구분하지 못한다.
   - `src/browser/reattachHelpers.ts:373-412`의 `recoverPromptEcho`는 이미 받은 answer가 prompt와 닮으면 `readAssistantSnapshot`을 identity 없이 다시 호출한다. strict wait 뒤에도 latest assistant로 빠질 수 있는 우회 경로다.
   - `src/browser/actions/assistantResponse.ts:596-617, 1687-1740`의 markdown copy는 supplied message/turn hint를 못 찾으면 마지막 assistant/copy button으로 fallback한다. strict answer text 뒤 markdown이 과거 턴으로 바뀔 수 있는 별도 우회 경로다.
5. **Deep Research 별도 success path**
   - `reattach.ts:180-195, 379-396`은 `waitForAssistantResponse`를 건너뛰고 `waitForDeepResearchCompletion`을 호출한다.
   - `src/browser/actions/deepResearch.ts:205-324, 516-670, 1052-1114`는 target baseline과 DOM index/owner index로 오래된 report를 줄이지만 durable stable user/assistant identity를 받지 않는다. 따라서 B2의 결합 귀속 gate와 동등하지 않다.
6. **현재 테스트가 보장하는 것과 빈자리**
   - `tests/browser/assistantResponseStatus.test.ts:495-848`은 user anchor 부재, stale/latest assistant, DOM prefix 제거, assistant ownership, completion action correlation을 검사한다. 이는 scoped resolver의 로컬 의미를 보장하지만 recovery call graph가 scope를 전달하는지는 보장하지 않는다.
   - `tests/browser/reattach.test.ts:22-335`는 prompt preview index 전달과 기존/new recovery fallback을 현재 동작으로 고정하지만 identityScope/conversation gate parity는 검사하지 않는다.
   - `tests/sessionManager.test.ts:62-188`은 metadata JSON 왕복과 cookie sanitizer를 검사하지만 turn identity round-trip은 없다.
   - `tests/browser/reattach.e2e.test.ts`는 `resumeBrowserSession` 자체를 mock한다. session completion wiring에는 유용하지만 실제 원격 귀속 증거가 아니다.

현재성 fingerprint(계획 시 읽은 바이트):

- `src/browser/reattach.ts` `983211db620bae973f97ae09c21615660180121e49e979a3d233b44260b625e0`
- `src/browser/actions/assistantResponse.ts` `623228258156e396fcbdc5693c64635219762fee8d1708682dba7036dfcc352e`
- `src/browser/index.ts` `52001f6702bd7643b4aafe53e4aab893b8f9b840d4a52be5d71326d049229d96`
- `src/sessionManager.ts` `195234101f007131c3dc685593c33caf5bfe6c3852fae376660ccc65be774b4b`

### PROPOSED

1. `BrowserRuntimeMetadata`의 canonical durable attribution contract를 다음처럼 둔다.
   - `committedUserTurn?: ConversationTurnIdentity | null`: remote user-turn commit의 내구 증거.
   - `identityScope?: AssistantResponseIdentityScope | null`: 같은 `committedUserTurn`과, 결합된 뒤에는 `committedAssistantTurn`을 포함하는 recovery success gate snapshot.
   - 공유 데이터 type은 `conversationTurns.ts` 같은 dependency-neutral 위치에 한 번만 정의하고 `assistantResponse.ts`와 `sessionManager.ts`가 같은 type을 import한다. 중복 shape/별도 recovery identity type은 만들지 않는다.
   - 두 user identity가 함께 존재하면 normalized identity가 일치해야 한다. absent, malformed, 상충은 합성/부분 필드 추측 없이 fail-closed한다. `committedAssistantTurn`은 아직 렌더링 전에는 `null`일 수 있으나, 성공 반환 시에는 유일한 owned assistant와 completion 증거가 필요하다.
2. commit writer와 assistant-binding writer를 기존 runtime hint → session `meta.json` 경로에 연결한다.
3. recovery 시작 시 저장 metadata를 한 번 normalize/validate해 `{ expectedConversationId, identityScope }`를 만든 뒤 existing/new Chrome 양쪽이 같은 객체와 같은 capture helper를 사용한다.
4. strict identity recovery에서는 `minTurnIndex`, prompt preview, prompt echo recovery, latest markdown/copy fallback을 성공 gate에서 제거한다. 이 값들은 진단/navigation hint로도 성공을 승인하지 못한다.
5. standard response와 Deep Research 모두 동일 conversation/current-user/owned-assistant/completed conjunction을 만족한 뒤에만 `ReattachResult`를 만든다.

### UNRESOLVED

1. **B1 handoff/provenance evidence 없음**: B1 Exit release identity가 공급되지 않았다. 이 Plan의 source 구현과 targeted self-check는 진행할 수 있으나 B2 transition continuation/Exit 또는 installed-runtime 효과의 증거로 승격할 수 없다. 최소 판별 관찰은 B1 handoff가 지정한 exact runtime/release candidate identity와 이 source revision의 browser implementation이 동일 artifact에 속한다는 readback이다. owner는 preparation lead/transition authority owner다.
2. **실제 ChatGPT DOM의 stable identity 가용성**: 소스는 stable turn attributes를 읽도록 구현되어 있지만 현재 live conversation에서 normal/Deep Research가 어떤 stable field를 제공하는지는 이번 read-only Plan에서 외부 실행하지 않았다. 최소 판별 관찰은 승인된 기존 session에서 target user와 owned assistant의 normalized identity, conversation id, completion state를 비제출 방식으로 읽는 것이다. field가 없거나 모호하면 fallback을 추가하지 말고 recovery를 `uncertain`/failure로 닫는다.
3. **외부 실제 acceptance evidence 미수집**: 단위 fixture/mocks는 실제 remote turn, 새 Chrome, 중복 prompt count를 대체하지 않는다. 권한 있는 verifier의 actual browser/session readback이 없으면 구현 자체 점검은 완료할 수 있어도 Scope Acceptance 판정은 evidence gap으로 남는다.
4. **Transition approval**: bound Baseline 원문은 DRAFT다. current Scope 구현 요청 외의 Block 진행/Exit 승인으로 해석하지 않는다.

## 4. Entry/read paths, deciding writers/readers, lifetime

### Entry/read paths

1. CLI session run은 `performSessionRun`에서 `runBrowserSessionExecution`을 호출하고 `runtimeHintCb`를 `persistRuntimeHint`/`sessionStore.updateSession`에 연결한다.
2. 정상 local Chrome 및 remote Chrome 제출은 `chatgptDomProvider.submitPrompt`가 `submitPrompt`의 commit identity를 받는다.
3. 프로세스 중단 뒤 `sessionDisplay` 또는 `autoReattachUntilComplete`가 `meta.json → metadata.browser.runtime`을 읽어 `resumeBrowserSession`에 전달한다.
4. `resumeBrowserSession`은 저장 conversation/identity를 검증한 뒤 existing target에 붙거나 같은 runtime을 new-Chrome path로 전달한다.
5. 두 recovery path는 동일 attributed capture helper를 호출하고, 그 helper만 `waitForAssistantResponse` 또는 identity-aware Deep Research gate를 호출한다.

### Deciding writers

- send-attempt writer: 기존 `markPromptSubmitted`; `promptSubmitted=true`만 기록하며 commit identity를 대신하지 않는다.
- user-commit writer: provider가 `submitPrompt` 반환을 받은 직후 `onPromptCommitted(committedUserTurn)`을 await한다. 이 write가 실패하면 이미 submission 가능성이 있으므로 답변 대기/성공 발표/재제출로 진행하지 않고 uncertain error를 보존한다.
- assistant-binding writer: `waitForAssistantResponse`가 current user에 owned assistant를 최초 유일 결합한 직후, observer/poller 성공을 기다리기 전에 `onIdentityScopeResolved(scope)`를 await한다. write 실패는 성공으로 무시하지 않는다.
- recovery binding writer: recovery 중 metadata에 assistant가 아직 null이었다가 결합되면 caller-provided awaited persistence hook으로 같은 session runtime을 갱신한 뒤 capture를 계속한다.
- completed result writer: 기존 session completion writer가 identity-bearing runtime을 보존한 채 answer/artifacts와 completion을 기록한다. 기존 `browser: { ... }` 재구성으로 identity가 떨어지지 않게 spread/central builder를 사용한다.

### Deciding readers

- `requireRecoveryAttribution(runtime)`(private helper)은 conversation id, top-level committed user, nested identity scope를 normalize하고 conflict/absence를 거절하는 유일 recovery entry validator다.
- `waitForAssistantResponse`의 scoped resolver는 current user/assistant ownership과 completion을 결정한다.
- Deep Research owner resolver는 동일 identity scope로 top-level owned assistant를 먼저 확정하고, report iframe/OOPIF가 그 assistant에 속함을 확인한다. ordinal은 현재 DOM에서 이미 identity로 찾은 owner node를 iframe에 연결하는 내부 locator로만 쓸 수 있고 persisted identity/성공 증거를 대신하지 않는다.
- `sessionDisplay`/`autoReattachUntilComplete`는 reattach return이 strict attributed capture를 통과한 경우에만 session을 completed로 기록한다.

### State/effect lifetime

- creation: send action 이전에는 identity fields 없음. send attempt 후 `promptSubmitted`만 true일 수 있다.
- update 1: remote user turn commit 검증 직후 `committedUserTurn`과 `identityScope={ committedUserTurn, committedAssistantTurn:null }`를 한 metadata write에 기록한다.
- update 2: owned assistant가 유일 결합되면 같은 scope의 assistant field를 채워 다시 기록한다.
- reads: 동일 process의 정상 wait, process restart 뒤 existing-Chrome reattach, new-Chrome recovery, completion/markdown capture가 같은 scope를 읽는다.
- reset: 새 follow-up을 제출해 새 current request가 commit된 때에만 새 user scope로 교체한다. send attempt만으로 이전 committed scope를 지우지 않는다. 다른 session/request가 이 값을 갱신하지 않는다.
- success: same conversation + unique user + owned assistant + completed response를 확인하고 identity-bearing runtime과 answer를 저장한 뒤 success를 발표한다.
- failure/interruption: 부분/상충 identity는 유지하되 success로 읽지 않는다. 자동 resend하지 않는다. timeout/DOM ambiguity/persistence failure는 explicit attribution/uncertain failure다.

## 5. 구현 순서 — HA-02/HA-03/HA-04 atomic cut

### Step 1 — canonical durable identity schema

1. `ConversationTurnIdentity`와 identity-scope type을 공유 source에 둔다. `assistantResponse.ts`, provider/index, `sessionManager.ts`, tests가 그 한 type을 사용하도록 clean cutover한다.
2. `BrowserRuntimeMetadata`에 `committedUserTurn`와 `identityScope`를 추가한다. `BrowserRunResult`에도 같은 최종 runtime fields를 추가해 정상 completion/error 객체가 identity를 떨어뜨리지 않게 한다.
3. local/remote browser mode 각각에 흩어진 runtime object literal을 mode-local `buildRuntimeMetadata()` 하나로 모아 Chrome/conversation/`promptSubmitted`/identity를 항상 함께 만든다. success return, timeout, disconnect, challenge, runtime hint의 모든 caller를 이 builder로 이동하고 obsolete literal duplication을 제거한다.
4. sanitizer는 identity를 그대로 보존하되 JSON read 후 recovery entry에서 normalize한다. 저장 파일에 function/DOM index/node를 넣지 않고 stable scalar identity만 저장한다.
5. `tests/sessionManager.test.ts`에 initialize/update/read/원시 `meta.json` round-trip을 추가한다. user와 assistant identity가 모두 보존되고 inline cookie sanitizer가 계속 적용됨을 관찰한다.

### Step 2 — commit 직후 strict durable write

1. `ChatgptDomProviderState`/`ChatGptProviderSubmissionState`에 awaited `onPromptCommitted(identity)` hook을 추가한다.
2. `chatgptDomProvider.submitPromptViaAdapter`가 `submitPrompt` 반환을 받은 뒤 state를 설정하고 즉시 hook을 await한다. `onPromptSubmitted`(send attempt)보다 뒤, response wait보다 앞이다.
3. local/remote `index.ts`에서 hook은 normalized committed user를 process state에 두고 `identityScope`를 생성한 뒤 authoritative runtime persistence callback을 await한다.
4. 일반 Chrome 위치/URL hint의 기존 best-effort catch와 identity persistence를 분리한다. user commit 또는 assistant binding write failure를 log-only로 삼지 않는다. 이미 send 가능성이 있으므로 typed uncertain error에 full runtime evidence를 싣고 자동 submission/retry를 금지한다.
5. follow-up마다 commit된 새 scope만 current recovery target으로 교체한다. fallback submission이 실제 새 send를 수행한 경우에도 commit된 실제 turn만 기록한다.

### Step 3 — assistant binding을 저장하고 normal gate 유지

1. `waitForAssistantResponse`의 현재 positional identity 관련 인자를 하나의 options object(`minTurnIndex`, `expectedConversationId`, `identityScope`, awaited `onIdentityScopeResolved`)로 정리하고 모든 caller를 한 번에 migration한다. overload/legacy alias는 남기지 않는다.
2. `resolveAssistantResponseIdentityScope`가 user를 normalize하고 owned assistant를 유일하게 bind한 직후 callback을 await한다. callback은 scope의 defensive copy를 받아 durable writer를 호출한다.
3. normal local/remote path의 wait/reload/final snapshot/settle 경로가 같은 mutable current scope를 사용한다. assistant identity가 변경되면 runtime metadata를 갱신하고, error result에도 마지막 durable scope를 보존한다.
4. `captureAssistantMarkdown`/copy expression에 identityScope를 전달한다. scoped mode에서는 exact scoped assistant container의 copy action만 허용하며 hint miss 시 latest assistant/global copy button으로 fallback하지 않고 `null`/error를 반환한다. plain text를 authoritative scoped snapshot에서 보존할 수는 있지만 다른 턴의 markdown으로 교체하지 않는다.
5. `assistantResponseStatus.test.ts`에 malformed persisted identity, duplicate user match, missing owned assistant, later C assistant, old A-only copy button, scoped copy hint miss를 추가한다. 실제 DOM을 대체하는 완료 증거로 주장하지 않고 resolver contract 회귀로만 사용한다.

### Step 4 — recovery entry에서 attribution을 필수화

1. `reattach.ts` 시작부에서 `requireRecoveryAttribution(runtime)`을 호출한다.
   - canonical conversation id는 저장 `conversationId` 또는 유효한 `/c/<id>` URL에서 얻되 둘 다 있으면 일치해야 한다.
   - committed user와 identityScope user는 normalized identity가 일치해야 한다.
   - assistant identity가 있으면 normalize되어야 한다.
   - 어느 필수 증거든 absent/malformed/conflicting하면 Chrome attach/open 전에 `recovery-attribution-unavailable` 오류로 종료한다.
2. `ensureConversationOpen`과 new-Chrome navigation 후 `location.href`의 conversation id를 canonical id와 정확히 비교한다. mismatch/unknown은 sidebar preview 검색이나 현재 탭 수용으로 우회하지 않는다.
3. `readPromptPreviewTurnIndex`와 `readConversationTurnIndex`를 response selection에서 제거한다. 더 이상 사용되지 않으면 helper/test/export도 삭제한다. prompt preview는 UI 안내에 남더라도 conversation/turn identity 또는 success를 승인하지 못한다.
4. existing-/new-Chrome branch가 중복 구현하지 않도록 private `captureAttributedRecoveryResponse`를 만든다. 입력은 `Runtime`, expected conversation id, validated identityScope, timeout/logger와 필요한 Page/client뿐이다.
5. standard response는 `waitForAssistantResponse(Runtime, timeout, logger, { expectedConversationId, identityScope, onIdentityScopeResolved })`만 사용한다. `minTurnIndex`는 전달하지 않는다.
6. strict recovery path에서 `recoverPromptEcho`, `buildPromptEchoMatcher`, `alignPromptEchoMarkdown`을 제거한다. scoped resolver가 user echo를 assistant로 반환했다면 그것은 보정 대상이 아니라 gate failure다.
7. markdown capture에도 동일 scope를 전달한다. scoped markdown이 없으면 latest copy button을 쓰지 않는다.
8. existing attach 실패 뒤 new Chrome fallback은 validated attribution 객체를 그대로 전달한다. missing identity 오류는 새 Chrome을 열어도 회복되지 않으므로 fallback 전에 닫는다. infrastructure/target failure만 동일 strict new-Chrome path로 이동한다.

### Step 5 — Deep Research parity

1. `waitForDeepResearchCompletion` options에 validated `identityScope`와 expected conversation id를 추가한다.
2. poll 시작 전 common scoped resolver로 target user와 owned assistant를 유일하게 찾고, 현재 location conversation도 검증한다. iframe/OOPIF owner index는 그 exact assistant DOM node에서 계산한 locator일 때만 사용한다.
3. target baseline, latest report, `requireScopedTargetOwner`, copy/action state는 보조 completion/effect evidence다. stable owner identity를 match하지 못하면 completed-looking 과거 report를 반환하지 않는다.
4. normal, existing reattach, new-Chrome branch가 같은 Deep Research ownership/completion contract를 호출하도록 migration한다. 현 UI에서 stable owner mapping이 불가능하면 Deep Research recovery만 명시적 attribution error로 닫고 normal-response/latest-report fallback을 추가하지 않는다.
5. `tests/browser/deepResearch.test.ts`에 이전 completed report만 존재, target B 미렌더링, B 뒤 C 존재, owner mismatch를 추가하고 모두 success가 아님을 확인한다.

### Step 6 — completion writers와 readback 보존

1. `ReattachResult`에 resolved identityScope를 포함한다. `sessionDisplay`와 auto-reattach는 callback으로 assistant binding을 먼저 runtime에 저장하고, 최종 completion update에서도 returned scope를 포함한 runtime을 보존한다.
2. recovery persistence callback이 실패하면 answer를 `completed`로 발표하지 않는다. 이미 scoped answer를 관찰했다면 evidence/answer를 버리지 말고 incomplete/uncertain 상태와 persistence error를 구별해 보존한다. 이 Scope 밖의 새 상태 체계를 만들지 말고 기존 error/response metadata 표현을 사용한다.
3. late/duplicate recovery는 다른 request identity와 상충하면 덮어쓰지 않는다. update 직전 최신 session runtime identity를 다시 읽어 expected scope와 일치할 때만 completion을 기록한다. mismatch는 현재 owner/result를 변경하지 않고 fail-closed한다.
4. 어떤 recovery path도 composer 입력, send button, `submitPrompt`, fallback submission을 호출하지 않음을 source call graph와 spy로 확인한다.

## 6. Partial failure, interruption, late response 처리

| 경계 | 관찰 | 처리 |
| --- | --- | --- |
| send action 후 commit write 전 급사 | `promptSubmitted`만 있고 committed user 없음 | 미제출로 추정하지 않는다. recovery는 attribution unavailable/uncertain, 자동 resend 없음. |
| user commit 확인 후 identity write 실패 | remote effect 가능/확정, durable user 없음 | normal success 대기/발표 중단; full runtime error evidence 보존; 재제출 없음. |
| user identity 저장 후 assistant 미렌더링 | assistant null | 같은 user-owned assistant만 대기; timeout/failure. A 또는 C 반환 금지. |
| assistant bind 후 persistence 실패 | remote assistant 존재, durable lineage 갱신 실패 | completed 발표 금지; 관찰 answer/evidence 보존, persistence failure 표시. |
| identity fields 상충/복수 match | attribution ambiguous | attach/open 또는 capture 단계에서 explicit failure; text/ordinal fallback 없음. |
| existing Chrome 연결 실패 | infrastructure failure | 같은 validated conversation/scope로 new Chrome 시도 가능. identity failure라면 new Chrome fallback 금지. |
| completion은 보이나 owned turn이 아님 | old A/later C action bar 또는 report | 무시하고 target B를 기다리거나 timeout. |
| scoped text 성공, markdown copy 실패 | 정확한 text는 있음, copy scope 없음 | 다른 턴 markdown 사용 금지. 현재 scoped text 보존 또는 명시적 markdown 후처리 실패. |
| answer 저장 뒤 caller 출력 실패 | durable current-turn answer 있음 | 같은 stored result 조회; 새 prompt 없음. |
| 늦은 recovery가 newer scope 발견 | stored expected scope mismatch | newer request/result/slot을 덮어쓰지 않고 stale recovery 실패. |

## 7. 테스트 및 구현자 자체 점검

### Targeted automated checks

1. `pnpm exec vitest run tests/sessionManager.test.ts`
   - 실제 temp `meta.json` write/read에서 committed user/assistant/identityScope가 보존되는지 확인한다.
2. `pnpm exec vitest run tests/browser/assistantResponseStatus.test.ts tests/browser/deepResearch.test.ts`
   - local DOM fixtures로 unique ownership, missing/duplicate/conflicting identity, incomplete response, old A/later C/copy-button contamination을 구분한다.
3. `pnpm exec vitest run tests/browser/reattach.test.ts`
   - 모든 success fixture에 canonical conversation + durable scope를 제공한다.
   - existing-Chrome waiter가 expected conversation/scope를 받는지, missing scope에서 waiter/capture/new-Chrome launch가 호출되지 않는지, strict markdown/echo bypass가 없는지 확인한다.
   - existing attach 실패 후 new-Chrome path도 동일 scope를 받는 parity case를 둔다.
4. `pnpm exec vitest run tests/browser/reattach.e2e.test.ts tests/cli/sessionRunner.test.ts`
   - 이 테스트의 mocks는 실제 attribution proof가 아니라 caller state transition만 검사한다. recovered identity가 completion update에 유지되고 stale scope가 completed를 덮어쓰지 않으며 retry loop가 prompt 제출을 호출하지 않는지를 확인한다.
5. 변경된 source에 대한 좁은 compile check가 가능한 경우 `pnpm exec tsc --noEmit`을 구현자 self-check 마지막에 실행한다. project-wide formatter/lint/test suite는 caller 통합 단계 소유다.

### Minimum real acceptance path (독립 verifier 소유)

승인된 로그인/브라우저/외부 effect 권한과 stable current artifact가 있을 때만 수행한다. 각 run에서 실제 remote prompt count, conversation id, user/assistant stable identity, completion, session `meta.json`, answer readback을 함께 보존한다.

1. 같은 conversation에서 A 완료 후 B를 제출하고 B 대기 중 기존 Chrome 연결을 끊는다. metadata의 B scope를 읽고 reattach한다.
2. 동일 조건에서 Chrome 프로세스를 종료하고 새 Chrome recovery를 수행한다.
3. 각각에 대해 (a) A/B 동일 prompt, (b) 첫 120자 동일, (c) B assistant 미렌더링, (d) A만 copy button 보유, (e) B 뒤 C 존재를 구분한다.
4. success인 경우 remote B user identity = stored committed user, returned assistant = B owner, B completion=true, conversation id 일치, stored answer/runtime identity 일치를 대조한다.
5. B가 없거나 identity가 모호한 경우 explicit failure/timeout, session evidence 보존, remote prompt count 불변을 확인한다.
6. 실제 external readback 없이 위 단위 테스트를 이 acceptance의 대체 증거로 사용하지 않는다. Block 4 clean-environment 요건까지 이 Scope가 주장하지 않는다.

### Verifier handoff current-target condition

- Scope/Thesis/Transition hashes가 위 값과 동일하다.
- Plan에 적은 load-bearing source가 구현 도중 materially 바뀌었으면 해당 premise와 method를 재검토한다.
- HA-02 writer/readers, HA-03 both recovery gates, HA-04 no-resubmit가 같은 runnable source/artifact cut에 모두 존재한다.
- 실제 검증 artifact provenance가 구현 source와 연결되고, unfinished/uncertain external requests가 격리되어 있다.

## 8. Conditional first-work bundles

### Bundle C1 — B1 provenance handoff

- `plan_anchor`: §3 UNRESOLVED 1, §7 Verifier handoff.
- `permitted_initial_work`: source-only B2 구현과 targeted unit/self-check. supplied B1 evidence가 있다면 exact release/artifact identity를 읽는 비제출 readback.
- `discriminating_observation`: B1 handoff의 runtime/release identity가 이 B2 browser source를 실제 실행할 candidate와 cryptographically/provenance상 연결됨.
- `dependent_work_not_yet_permitted`: B2 transition Exit, installed-runtime claim, 다음 Block 자동 진행.
- `response_if_refuted`: candidate promotion/외부 실행을 중지하고 B1 owner 및 Plan owner에게 반환한다. B2 source tests를 installed product evidence로 재분류하지 않는다.

### Bundle C2 — stable turn identity availability

- `plan_anchor`: §3 UNRESOLVED 2, §5 Step 5.
- `permitted_initial_work`: 승인된 기존 conversation에서 prompt를 제출하지 않고 target user/assistant의 DOM identity와 Deep Research owner mapping을 읽는다.
- `discriminating_observation`: stored normalized user가 exactly one remote user를 match하고 exactly one owned assistant 및 completion/Deep Research owner를 결합할 수 있음.
- `dependent_work_not_yet_permitted`: identity가 없는 DOM에서 ordinal/latest/prompt-text fallback 구현, 해당 path의 success publication.
- `response_if_refuted`: 해당 recovery path를 fail-closed 상태로 유지하고 Plan owner에게 method 재검토를 요청한다. 제품 의미를 바꿔 old/latest answer를 허용해야 한다면 Scope/Thesis owner로 반환한다.

### Bundle C3 — actual recovery acceptance

- `plan_anchor`: §7 Minimum real acceptance path.
- `permitted_initial_work`: 현재 사용자/환경 권한이 명시된 뒤 하나의 isolated, evidence-preserving B request로 existing-Chrome recovery를 먼저 실행한다.
- `discriminating_observation`: remote B identity/owner/completion, stored scope, returned answer가 일치하고 prompt count가 증가하지 않음.
- `dependent_work_not_yet_permitted`: new-Chrome/adversarial external matrix, Scope PASS/Block Exit 주장.
- `response_if_refuted`: 추가 submission/retry를 중단하고 session/conversation/runtime/slot evidence를 보존한다. implementation defect면 Plan/implementer로, product meaning gap이면 exact Scope/Thesis owner로 반환한다.

### Bundle C4 — stale/duplicate completion write

- `plan_anchor`: §5 Step 6, §6 late recovery row.
- `permitted_initial_work`: temp session store에서 recovery 시작 scope와 completion write 직전 scope를 다르게 만드는 local state-transition test.
- `discriminating_observation`: compare-before-complete가 mismatch를 거절하고 newer runtime/result를 그대로 보존함.
- `dependent_work_not_yet_permitted`: late recovery가 unconditional `status=completed`를 쓰는 구현, live concurrent recovery.
- `response_if_refuted`: completion writer mutation을 중단하고 Plan owner에게 persistence/ownership method 재검토를 요청한다.

## 9. 구현 재량과 재검토 경계

- private helper 이름, options object의 정확한 이름, test fixture 구성은 implementer 재량이다.
- 다음은 material method 변경이므로 affected work를 중지하고 이 Plan을 개정한 뒤 새 independent Plan Review가 필요하다: identity schema/ownership 의미, durable writer 시점, recovery success gate, conversation authority, Deep Research attribution strategy, success publication/readback, 자동 retry 정책.
- current result/Acceptance를 줄이려면 Scope owner로, old/latest answer 허용이나 제출 의미를 바꾸려면 Thesis owner로 반환한다.
- 이 Plan은 구현, 검증 판정, Scope `done`, B2 Exit 또는 다음 Block 시작을 선언하지 않는다.
