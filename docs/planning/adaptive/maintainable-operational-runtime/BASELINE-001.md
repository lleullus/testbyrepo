# Transition Baseline `BASELINE-001`

Status: DRAFT
Project-Root: `/home/user01/project/oracle`
Baseline-ID: `BASELINE-001`
Revision: `draft-2026-09-16.1` — this emitted revision is immutable; any textual change requires a new revision identifier
Applicability: Oracle Browser를 개인 환경·숙련자 운영 지식에 의존하는 현 런타임에서, `/home/user01/project/oracle/oracle-browser-slots/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md`가 정의한 **자기완결적 프로덕션 런타임**으로 전환하는 프로젝트 수준 Transition Baseline. Product meaning에 대해서는 해당 Thesis가 최상위 권위이며, 본 Baseline은 그 의미를 축소·재정의하지 않고 구현 전이의 측정 가능한 경계만 규정한다.

## Identity & Approval

Source Authority:

* Product meaning: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/product-thesis/maintainable-operational-runtime/THESIS-001.md`, SHA-256 `b532ad84c1e8529e8169f68e6673d279b6f3a6cf8018f7d0fd64b761cb9c69c6`. 이 문서의 `Result: CALIBRATED` 제품 의미, Required Outcomes / Means, Truth / Causal Invariants, Success Observation을 본 전이의 최상위 제품 권위로 사용한다.
* Baseline contract form: `/home/user01/project/iis-skills/iis-workflow/templates/BASELINE-NNN.template.md`, SHA-256 `3bc9b1bfaa7f28523e51029edb194435b90f2655d8586909dd74e7af6690a1c3`. 본 문서의 Identity, Outcome, Invariants, Transition Blocks, Safe Continuation, Safe Abort, Atomic Boundary 구조와 판정 의미의 형식 권위다.
* Current-state evidence: `/home/user01/project/oracle/package.json`, SHA-256 `9fdd86af8557bca025be71011aa8f5440b6c7e8b181c3570da978a2fc4f4ec44`.
* Current-state evidence: `/home/user01/project/oracle/oracle-browser-slots/oracle_browser_slots/runner.py`, SHA-256 `f993b1ed0e3e5359f34c5d6dd7d6abf079dcc5390e0a6f858adb99e3ece2a1be`.
* Current-state evidence: `/home/user01/project/oracle/oracle-browser-slots/oracle_browser_slots/attachments.py`, SHA-256 `2b802d2211360c749260a224c15ee42a88b83b6ef90fe5595f4e22e1346aa6f1`.
* Investigation: 별도의 Investigation 문서는 이번 Baseline의 직접 입력으로 승인되지 않았다. 위 세 current-state source와 THESIS-001에 이미 인계되어 있는 조사 결과만 적용한다. 특히 `reattach.ts`, `assistantResponse.ts`, `SKILL.md`는 이번 Baseline 작성에서 직접 재열람했다고 주장하지 않으며, 그 파일들에 관한 제품 사실은 THESIS-001에 확정되어 있는 Source Authority 범위 안에서만 사용한다.
* Current user authority: 2026-09-16 현재 요청. `/home/user01/project/oracle`을 Project-Root로 지정하고, THESIS-001을 제품적 의미의 최상위 Source Authority로 삼으며, 본 Baseline에 Block 1~4, Thesis의 5대 불변식, Safe Continuation / Safe Abort, HARD_ATOMIC 경계를 포함하도록 한 명시적 작성 지시다. 이 지시는 Baseline 초안 작성 권한이며 구현·배포·Block 자동 진행의 승인으로 해석하지 않는다.

Approval:

* Approved by: Pending — this revision is a draft and has not received explicit transition approval.
* Approved at / reference: Not approved. The 2026-09-16 user instruction authorizes preparation of this draft only.
* Approval scope: None until explicit approval. Approval 시에는 최소한 Transformation Goal, Required Named Items, Global/Path Invariants, 각 Block의 Entry/Exit/Abort, Safe Continuation ceiling 및 Atomic Boundary를 함께 승인해야 한다.
* Inter-Block auto-continuation authorized: `no`

Applicability requires this exact original revision and current authority. Finding an old file does not authorize the transition. This is a conditional transition contract, not an operating mode, request form, cursor, status log or workflow store.

## Transformation Outcome

Goal:

* THESIS-001이 정의한 Oracle Browser의 제품 의미를 변경하지 않은 채, 현재 개인 NVM 설치 경로·외부 패키지 내부 구현·에이전트 전용 운영 지침에 의존하는 실행 형태를 **지원되는 Linux/WSL2 환경에서 다른 사용자·HOME·설치 경로로 옮겨도 동일한 실행, 제출, 결과 귀속, 실패 폐쇄 계약을 스스로 유지하는 자기완결적 프로덕션 런타임**으로 전환한다.
* 전환 결과는 “패키지가 생성된다”, “한 번 실행된다”, “개발 checkout에서는 테스트가 통과한다”가 아니다. 정상 설치 → 사전 검증 → 슬롯 점유 → 제출 → 현재 턴 응답 확정 → 결과 보존 → 슬롯 종료/격리 → 기존 결과 재조회 및 recovery까지의 제품 수명주기가 THESIS-001의 의미로 닫혀야 한다.
* 제품이 직접 책임져야 하는 보호는 SKILL.md나 숙련자의 기억에 위임하지 않는다. 선언된 플랫폼 전제인 Node/Python/Chrome, 사용자 로그인 및 외부 ChatGPT 서비스 자체는 지원 환경의 명시적 전제로 남을 수 있으나, `/home/user01`, 특정 NVM 버전 디렉터리, 개발 checkout, 외부 패키지의 비공개 `dist/src/...` 경로는 제품 전제가 될 수 없다.
* 이 Baseline은 번들러, 패키지 관리자, 저장 라이브러리, 구체적 manifest 스키마와 같은 Candidate Means를 선제적으로 고정하지 않는다. 어느 구현을 선택하더라도 아래 Completion Predicate와 Invariants를 만족해야 한다.

Required Named Items:

* **Self-Contained Runtime Unit** — 실행 CLI, 파일 선택/첨부 정책, 브라우저 동작 코드가 하나의 선언된 호환 실행 단위로 해석되어야 한다. 개인 NVM 절대 경로나 개발 checkout 복제 없이 설치물 자체에서 정체성을 결정해야 한다.
* **Runtime Provenance / Build-Binary Integrity** — 실제 호출된 `oracle` 실행물과 파일 선택·첨부·브라우저 구현이 동일한 지원 릴리스/구성에 속한다는 사실을 실행 시점 또는 승인된 provenance readback으로 판정할 수 있어야 한다.
* **CLI-Owned Safety Contract** — `run`, `submit`, `followup` 및 지원하는 recovery 진입 경로가 동일한 사전 검증·라우팅·첨부·실패 계약을 내장한다.
* **Default Browser Response Timeout = 2h** — 사용자가 명시적으로 override하지 않는 정상 Browser 실행은 응답 대기 기본값 `2h`를 제품 자체가 적용하고 실제 적용값을 관찰 가능하게 해야 한다.
* **Automatic Pre-Submission Validation** — 버전/호환성, 인자, 라우팅, 첨부 준비, 선택 슬롯의 제출 직전 CDP/login 등 실제로 시점 의존적인 전제는 irreversible submission 이전에 자동 검증한다. 별도 수동 dry-run은 필수 선행조건이 될 수 없다.
* **Zero False Success in Recovery** — recovery의 성공은 반드시 동일 conversation, 현재 요청의 고유 사용자 턴, 그 턴에 귀속된 고유 어시스턴트 턴, 완결 응답의 결합 증거를 요구한다. 그 증거가 없으면 `uncertain`/failure로 닫으며 이전 또는 이후 턴을 성공으로 반환하지 않는다.
* **Durable Request/Turn Lineage** — 프로세스 메모리에만 존재하는 `identityScope`가 아니라 recovery 후에도 request/session/conversation/user-turn/assistant-turn/originating-slot 결합을 재구성할 수 있는 내구 증거를 갖는다.
* **Non-Submitting Recovery** — `reattach` 계열 복구는 결과 수거 경로이며 귀속이 불확실한 요청을 자동 재제출하지 않는다.
* **Exclusive Slot Ownership** — 동시에 하나의 관리 슬롯을 승인받은 활성 owner는 최대 하나이며, owner를 검증하지 않은 해제는 금지한다. owner 소실은 자동 AVAILABLE이 아니라 격리 경계로 이어진다.
* **Context Continuity** — followup은 원 conversation 및 originating slot/profile에 고정되고, 다른 빈 슬롯이나 대체 conversation으로 조용히 이동하지 않는다.
* **Submission-Evidence Separation** — 전송 시도, 원격 사용자 턴 commit, 어시스턴트 응답 완결은 서로 독립된 사실로 보존한다.
* **Single Compressed ZIP for File Requests** — 파일 요청은 사용자가 선택한 원본 집합을 정확히 한 개의 압축 ZIP으로 정규화하며 선택 실패, ZIP 실패, 업로드 실패를 성공으로 숨기지 않는다. 첨부가 없는 요청에는 인위적인 ZIP을 만들지 않는다.
* **Closed Failure Lifecycle** — 제출 전 거절, 제출 가능성이 발생한 미확정, 귀속 확정 응답, 후처리 실패, 슬롯 격리를 서로 다른 상태로 보존하고 위험한 자동 재진입을 차단한다.
* **CI Python Regression Gate** — `oracle-browser-slots`의 제품 보호를 검증하는 pytest suite가 CI의 승인된 필수 검증 경로에 포함되어야 하며, 로컬 개발자가 테스트를 기억해서 실행하는 것에만 의존하지 않는다.
* **Clean-Environment E2E Evidence** — 원 개발자의 HOME/NVM/check-out을 갖지 않는 신규 격리 지원 환경에서 설치 → 실행 → 첨부/비첨부 → multi-turn → recovery → 결과 readback → 정상 해제 또는 안전 격리까지 관찰해야 한다.

Candidate Named Items:

* 제품 소유 Python/Node adapter, package-relative resolution, 공개된 안정 모듈 경계, 독립 번들링 등 Self-Contained Runtime Unit을 만드는 구체적 방식.
* release manifest, SHA-256/fingerprint, package metadata 또는 다른 provenance record를 통한 실행물 정합성 증명.
* 별도 `doctor` 또는 health-check CLI. 단, 실제 `run`/`submit`/`followup`의 내장 검증을 대신할 수 없다.
* 현재 `fcntl.flock`, PID starttime, atomic replace/fsync 패턴 등 기존 안전 primitives의 재사용.
* `committedUserTurn`, `committedAssistantTurn`, `identityScope` 또는 동등한 identity evidence를 세션에 영속화하는 구체적 스키마.
* clean-environment E2E를 container, VM, throw-away Linux user, WSL2 instance 또는 동등한 격리 환경으로 수행하는 구체적 방법.
* packed artifact smoke, package install smoke 또는 release candidate staging을 통한 build/readback 방법.
* 이 Candidate들은 특정 구현의 선승인을 뜻하지 않으며 Required Named Item보다 낮은 권위다.

Completion Predicate:

* **다음의 결합 관찰이 한 승인된 release candidate에 대해 모두 참이어야 한다:** 개인 `/home/user01` NVM·개발 checkout·외부 비공개 `dist/src/...` 의존 없이 신규 지원 환경에 설치된 실행물이 자신의 실제 release identity를 증명하며 실행되고, CLI 내장 사전 검증과 기본 `2h` 응답 대기를 적용하고, 파일 요청은 정확한 단일 ZIP으로 제출되며, 슬롯/중복/followup 소유권 불변식을 지키고, 정상 실행과 기존-Chrome recovery 및 새-Chrome recovery 모두에서 `success ⇒ same conversation ∧ uniquely identified current user turn ∧ assistant owned by that turn ∧ completed response`를 만족하며, 제출 여부가 불확실하면 자동 재전송하지 않고, 급사/후처리 실패에서는 이미 확정된 결과를 보존하면서 위험 슬롯을 격리하고, 저장 결과를 재조회할 수 있으며, 해당 보호를 검증하는 필수 pytest/빌드 검증과 clean-environment E2E가 모두 승인된 readback으로 통과해야 한다.
* 위 conjunction 중 하나라도 unknown이거나 실패하면 전체 Transformation Completion은 성립하지 않는다.
* 패키지 생성, TypeScript compile 성공, Python unit test 성공, 하나의 정상 Browser 요청 성공, `exit 0`, `promptSubmitted=true`, attachment ZIP 생성, source checkout의 테스트 통과는 단독으로 Completion Predicate가 아니다.

Final Authoritative Readback:

* Surface / owner: 실제 설치된 Oracle Browser 제품 런타임, 해당 런타임이 만든 session/result artifacts와 slot state, clean-environment E2E 실행 결과. 최종 판정 owner는 이 Baseline과 THESIS-001의 승인권자이며 하위 구현 Scope가 자체적으로 제품 완성을 선언할 수 없다.
* Source / method: clean environment에 설치된 release candidate의 실제 `oracle` entrypoint와 runtime provenance, 요청별 CLI 종료 상태, session `meta.json` 및 transcript/answer surface, 필요한 경우 `artifacts/oracle-browser-slots-attachments.json`, request/turn lineage evidence, slot ownership/reprepare 상태, recovery 전후 원격 conversation/turn 관찰, 그리고 필수 CI pytest/build/packed-runtime 검증 결과를 서로 대조한다. source tree의 예상값이 아니라 **실제로 설치·실행된 artifact**를 기준으로 한다.
* Claim limits: 이 readback은 지원 Linux/WSL2 환경에서 런타임의 자기완결성·보호·귀속·폐쇄 수명주기를 입증한다. AI 답변 내용의 사실성, ChatGPT 서비스 무중단, 인증 자동화, 모든 OS 지원, 모든 요청의 성공 또는 외부 UI 변경에 대한 영구적 호환성을 보증하지 않는다.

## Global Invariants

* **GI-01 — Slot Exclusivity / 슬롯 배타:** 같은 관리 슬롯에는 동시에 최대 하나의 승인된 활성 owner만 존재한다. 해제는 현재 owner identity를 확인한 주체만 수행한다. PID 값 하나나 `occupancy=null`만으로 가용성을 선언하지 않는다. owner 소실 또는 identity mismatch는 재사용 허용이 아니라 `requires_reprepare`/동등한 격리 상태로 이어져야 한다.
* **GI-02 — Context Continuity / 컨텍스트 연속:** followup의 `conversationId`, originating slot 및 profile lineage는 부모와 동일해야 한다. 현재 턴의 모델/Power 및 UI 준비 상태는 새로 검증한다. 같은 URL, 비슷한 prompt 또는 다른 슬롯에 보이는 동일 UI는 lineage 대체 증거가 아니다.
* **GI-03 — Submission Proof / 제출 증명:** send action, `promptSubmitted`, remote user-turn commit, assistant completion을 동일 사실로 축약하지 않는다. 제출 가능성이 한번 발생했다면 미제출이 입증되지 않은 상태에서 자동 재전송하지 않는다.
* **GI-04 — Result Attribution / 결과 귀속:** 모든 성공은 `same conversation ∧ unique current user turn ∧ assistant owned by that turn ∧ completed response`를 만족해야 한다. turn index 증가, prompt prefix, 마지막 assistant message, copy/action button, 과거 completed 상태는 이 결합 증거를 대신하지 못한다. 정상, reattach, 새 Chrome recovery, 늦게 도착한 capture에 예외를 두지 않는다.
* **GI-05 — Build-Binary Integrity / 빌드-바이너리 일체성:** 실제 실행 CLI와 파일 선택·첨부·브라우저 코드가 동일하게 선언된 호환 release/configuration에 속해야 한다. 수정 source를 테스트해 놓고 개인 NVM에 남은 구형 `dist`를 실행한 결과를 현재 build의 증거로 사용하지 않는다.
* **GI-06 — Fail-Closed Product Semantics:** 모호한 실행물, 모호한 제출, 모호한 턴, 모호한 owner는 성공 또는 재사용 가능 상태로 승격하지 않는다. 보수적 거절은 허용되지만 false success는 허용하지 않는다.
* **GI-07 — Caller-Independent Safety:** 동일 제품 호출이라면 일반 사용자, ChatGPT agent, scheduler가 동일 보호를 받는다. 별도 SKILL.md 준수 여부가 안전 계약을 달리 만들지 않는다.
* **GI-08 — No Silent Product-Meaning Regression:** 기존 Product Thesis의 명시 Pro selection (`Latest`, `GPT-5.6 Sol`, `GPT-5.5` × Power=`Pro`)과 슬롯 `(1,2,10)` 계약을 본 전이 편의를 위해 약화하지 않는다. 자동 lower-model fallback, 다른 슬롯으로 followup 이동, timeout 후 무조건 재제출을 허용하지 않는다.
* **GI-09 — Evidence Preservation:** 이미 관찰한 request/session/turn/result/owner evidence는 migration이나 cleanup 편의를 위해 파괴하지 않는다. 특히 제출 가능성이 있었던 실패와 확인된 결과는 후속 디버깅 및 recovery를 위해 보존해야 한다.
* **GI-10 — Result vs Cleanup Separation:** 현재 턴의 답변이 귀속까지 확정된 후 ZIP cleanup, manifest write, slot release 같은 후처리가 실패해도 답변을 삭제하거나 자동 재제출하지 않는다. 답변 결과와 후처리 실패/격리를 각각 관찰 가능하게 유지한다.
* **GI-11 — Attachment Intent Preservation:** 파일 선택 입력은 제품이 정의한 선택 의미를 보존하고 정확한 선택 집합을 단일 ZIP으로 변환한다. 빈 선택, path collision, ZIP 생성 실패, 등록 실패를 정상 첨부로 간주하지 않는다.
* **GI-12 — No Unsupported Authority Expansion:** 각 Block은 해당 Exit까지의 전이만 승인할 수 있다. Baseline 존재만으로 외부 배포, registry publish, 인증 자동화, 다음 Block 시작 또는 별도 데이터 migration 권한이 생기지 않는다.

## Path Invariants

These constraints apply throughout the transition path, including Block boundaries and re-entry. Apply the relevant slice to the current measured Block and selected Scope; a different construction order must not silently weaken an invariant.

* **PI-01 — No “temporary” personal-path fallback:** 전이 중 새 resolver가 실패했을 때 `/home/user01/.nvm/versions/node/v24.18.0/bin/oracle`로 되돌아가는 fallback을 두어 green test를 만들지 않는다. 개인 절대 경로 제거는 실제 실행 경로에서 검증한다.
* **PI-02 — CLI와 selector를 함께 본다:** `runner.py`의 CLI resolver만 독립화하고 `attachments.py`가 기존 외부 NVM의 `files.js`/`options.js`를 계속 import하는 상태는 자기완결성 진전으로는 기록할 수 있어도 Block 1 Exit는 아니다.
* **PI-03 — No private-module roulette:** 특정 global package layout의 `lib/node_modules/@steipete/oracle/dist/src/...` 존재 여부를 런타임 계약으로 간주하지 않는다. 그러한 내부 경로가 계속 필요하다면 동일 제품 artifact가 소유·버전 관리하는 명시적 경계여야 한다.
* **PI-04 — Installed artifact over source assumption:** 각 Block에서 build/runtime 관련 사실은 가능한 한 설치 또는 packed artifact의 readback으로 확인한다. source import 성공을 installed runtime 성공으로 치환하지 않는다.
* **PI-05 — Identity evidence before permissive recovery:** recovery를 더 permissive하게 만드는 변경은 durable identity/turn binding의 write/read 경로와 성공 gate가 먼저 또는 동일 HARD_ATOMIC cutover에서 존재해야 한다.
* **PI-06 — No auto-resubmit on uncertainty:** 제출 후 프로세스 급사, `promptSubmitted` 기록 누락, prompt preview matching 실패, turn ambiguity가 발생하는 모든 중간 단계에서 재전송보다 evidence recovery를 우선한다.
* **PI-07 — Normal/recovery parity:** 정상 경로에만 강한 identity gate를 적용하고 recovery가 text matching 또는 “latest answer” fallback을 사용하는 중간 상태를 승인 가능한 최종 상태로 남기지 않는다.
* **PI-08 — Compatibility guard precedes irreversible effect:** 실행물 compatibility, file preparation, route/model/Power, slot ownership, 시점 의존 CDP/login 검증은 가능한 범위에서 prompt submission 이전에 끝나야 한다.
* **PI-09 — Preview is non-submitting:** dry-run/preview/preflight가 존재하더라도 remote prompt를 만들지 않는다. 반대로 실실행은 preview 선행을 요구하지 않고 자체적으로 같은 필수 검증을 수행한다.
* **PI-10 — 2h protection is intrinsic:** `--browser-timeout 2h` 또는 동등한 실제 timeout 값은 사용자의 명시 override가 없을 때 CLI 자체의 결정으로 적용되어야 한다. agent prompt나 SKILL.md의 인자 주입에 의존하지 않는다.
* **PI-11 — Preserve explicit user override:** 사용자가 지원되는 timeout을 명시했다면 그 값을 조용히 `2h`로 덮지 않고 실제 적용값을 노출한다. 큐 대기·준비·cleanup과 browser response wait를 같은 timeout 의미로 혼합하지 않는다.
* **PI-12 — Re-entry is measured, not assumed:** 중단된 Block을 재개할 때 이전 Scope의 “완료 보고”가 아니라 현재 installed/runtime/session state를 다시 읽는다. 특히 active owner, uncertain submission, dirty slot, partially installed artifact는 재측정한다.
* **PI-13 — CI cannot weaken runtime semantics:** 테스트를 통과시키기 위해 production fail-closed gate를 test-only bypass하거나 recovery identity 검증을 약화하지 않는다.
* **PI-14 — Clean environment must be genuinely independent:** Block 4 환경은 원 개발자의 HOME, 개인 NVM 경로, source checkout, symlink 및 미선언 global installation을 간접적으로 참조하지 않아야 한다.
* **PI-15 — Evidence from failed E2E is retained:** Block 4 실패가 remote submission 가능성 이후에 발생하면 환경을 즉시 재초기화하여 증거를 잃지 않는다. session/result/slot/remote conversation evidence를 먼저 보존한다.
* **PI-16 — Completion requires aggregation:** 각 Block Exit는 Transformation Completion과 동일하지 않다. Block 4가 모든 선행 Required Named Items를 실제 installed runtime에서 재검증한 뒤에만 최종 Completion Predicate를 평가한다.

## Transition Blocks

Define coarse transition milestones and measured predicates, not preapproved future Scopes or a queue of implementation tasks.

### Block `B1-RUNTIME-CLOSURE` — 런타임 자기완결성 및 의존성 봉합

* **ID:** `B1-RUNTIME-CLOSURE`
* **Name:** 런타임 자기완결성 및 의존성 봉합
* **Meaning Contribution:** 제품 실행의 정체성과 파일 선택/첨부 구현을 개인 HOME/NVM/global package layout에서 분리하여, 다른 지원 설치 경로에서도 동일 release가 스스로 필요한 executable과 제품 소유 모듈을 해석할 수 있는 기반을 만든다. 이 Block은 Zero False Success 자체를 완성하지 않지만 이후 Block에서 검증할 browser/recovery 코드가 “어느 build를 실제로 실행했는지”를 신뢰할 수 있게 한다.
* **Order / Dependencies:** 첫 번째 필수 Block. 결과 귀속 강화 전에 수행하는 것을 기본 transition geography로 한다. 이유는 Block 2의 소스 변경을 검증하더라도 Block 1이 닫히지 않으면 실제 wrapper가 개인 NVM의 구형 `dist`를 실행하여 검증과 production runtime이 분리될 수 있기 때문이다.
* **Entry:** 다음 current-state facts가 본 revision의 authoritative entry다.

  * `/home/user01/project/oracle/package.json`은 package version `0.16.1`, bin entry `oracle -> dist/bin/oracle-cli.js`, 배포 파일 `dist/**/*`, Node `>=24`, `prepare -> pnpm run build`를 선언한다.
  * `runner.py`는 `CANONICAL_ORACLE_CLI = "/home/user01/.nvm/versions/node/v24.18.0/bin/oracle"`를 기본 실행물로 사용하며 env/constructor override가 없으면 이 개인 경로를 채택한다.
  * `runner.py`의 command validation은 `argv[0]`가 resolved canonical executable과 정확히 일치할 것을 요구하므로, 현재 기본 경로 결합은 실제 실행 진입 계약에 직접 포함되어 있다.
  * `attachments.py`에도 독립적으로 동일 `CANONICAL_ORACLE_CLI`가 존재한다.
  * `select_stock_files()`는 해당 CLI의 sibling Node를 추론한 뒤 version root 아래 `lib/node_modules/@steipete/oracle/dist/src/oracle/files.js`와 `dist/src/cli/options.js`를 직접 찾아 `readFiles`, `mergePathLikeOptions`, `dedupePathInputs`를 import한다.
  * 따라서 현재는 “wrapper CLI 위치 override”와 “attachment selector dependency resolution”이 별도의 provenance 경계를 갖고 있으며, 하나만 변경하면 동일 release 일체성이 성립하지 않는다.
  * Entry readback owner/source는 본 Baseline에 fingerprint로 고정한 `package.json`, `runner.py`, `attachments.py`다.
* **Exit:** 다음이 모두 실제 artifact/readback으로 참이어야 한다.

  * 제품의 정상 실행에 필요한 CLI executable resolution에 개인 `/home/user01/...` 또는 특정 NVM version directory가 기본/비상 fallback으로 남아 있지 않다.
  * 파일 선택/첨부 경로가 외부 global install의 비공개 `dist/src/oracle/files.js`, `dist/src/cli/options.js` 위치를 추측해야만 동작하는 구조가 아니다.
  * CLI executable, file selection logic, attachment normalization 및 browser implementation의 compatibility identity가 동일 release unit에 귀속되며, 서로 다른 설치본을 조용히 조합할 수 없다.
  * 다른 `HOME` 및 다른 absolute install prefix에서 제품 entrypoint와 file selection component를 resolve할 수 있다.
  * Node `>=24` 등 선언된 platform precondition이 충족되지 않거나 필요한 product-owned component가 누락된 경우 prompt submission 이전에 구체적 원인으로 fail-closed한다.
  * file-bearing request의 선택 결과는 현재 제품 의미를 유지하고 하나의 ZIP으로 정규화되며, file-free request는 불필요한 ZIP을 생성하지 않는다.
  * source tree가 아니라 packed/installed artifact 또는 이에 준하는 실제 배포 단위에서 executable identity와 selector identity의 일치가 readback된다.
  * Exit readback은 최소한 resolved executable path, release/version 또는 동등한 provenance, selector/attachment component의 동일 release 귀속, alternate install prefix에서의 non-submitting smoke 결과를 포함한다.
* **Invariants:** `GI-05`, `GI-06`, `GI-07`, `GI-08`, `GI-11`, `GI-12`, `PI-01`~`PI-04`, `PI-08`, `PI-12`.
* **Continuation:** Block 2로 넘기려면 B1 Exit evidence의 exact release/artifact identity를 고정하고 successor가 동일 artifact/source revision을 대상으로 작업함을 확인해야 한다. 다음 Block은 “source에 수정이 존재한다”가 아니라 “B1에서 확립한 self-contained release path가 그 수정된 browser runtime을 실제로 실행할 수 있다”는 사실을 상속한다. active remote prompt나 uncertain submission을 B1 검증 과정에서 만들었다면 먼저 Safe Continuation Predicate를 만족해야 한다.
* **Abort:** 다음 중 하나면 B1 자동 진행을 중단한다: 동일 release unit을 구성하려면 Product Thesis에 없는 외부 runtime service가 새 필수 전제로 필요해지는 경우, selector semantics가 기존 사용자 file selection 의미와 달라지는 경우, 설치 artifact가 source와 다른 browser/file-selection build를 실행하는 경우, 개인 NVM fallback 없이는 테스트가 통과하지 않는 경우. 안전 목표는 **새 runtime artifact의 promotion/사용을 중지하고, 기존 증거와 마지막 확인된 실행물을 보존한 채 미완성 상태로 남기는 것**이다. 이미 remote submission 가능성이 발생했다면 해당 요청을 재실행하지 말고 session/slot evidence를 보존한다. owner는 현 Scope의 authorized implementer/operator이며 rollback 가능성을 가정하지 않는다. Abort readback은 어떤 dependency가 self-contained하지 않은지, 어떤 artifact가 실제 resolve되었는지, remote effect 발생 여부를 명시해야 한다.
* **Insufficient for Exit:**

  * `runner.py`에서 하드코딩 문자열 한 곳만 제거.
  * `ORACLE_BROWSER_SLOTS_ORACLE_CLI` 환경변수를 수동 설정하면 성공.
  * `/home/user01/...` 경로를 symlink로 재현.
  * `oracle --version`이 `0.16.1`을 출력하지만 attachment selector는 다른 global package에서 import.
  * source checkout에서 Python unit test만 통과.
  * `pnpm build` 성공 또는 `dist/` 생성.
  * 첨부 없는 요청 하나의 성공.
  * file selector를 새로 구현했지만 기존 selection semantics 동등성/compatibility가 검증되지 않음.
  * build fingerprint 없이 “같은 버전 문자열이므로 같은 실행물”이라고 추정.

### Block `B2-RESULT-ATTRIBUTION` — 결과 귀속성 원천 보장 / Zero False Success in Recovery

* **ID:** `B2-RESULT-ATTRIBUTION`
* **Name:** 결과 귀속성 원천 보장
* **Meaning Contribution:** 정상 실행에서 관찰되는 current-turn identity를 recovery에서도 동일하게 적용하고, 프로세스 급사·reattach·새 Chrome 복구·동일 prompt 반복·후속 턴 존재 상황에서도 현재 요청이 아닌 답변을 성공으로 반환할 수 없는 구조를 만든다.
* **Order / Dependencies:** `B1-RUNTIME-CLOSURE` Exit 후가 기본. Block 2 구현 자체를 먼저 개발하는 것은 가능하지만 product transition continuation으로 인정하려면 B1 release identity와 결합하여 검증되어야 한다. 이 Block의 identity persistence writer와 recovery reader/success gate는 중간 불일치 상태로 배포하지 않는 HARD_ATOMIC 경계를 갖는다.
* **Entry:** THESIS-001의 authoritative product/current-state finding을 사용한다.

  * 정상 browser 경로에는 `committedUserTurn`, `committedAssistantTurn`, `identityScope`를 사용하여 특정 사용자 턴과 어시스턴트 턴을 결합하는 로직이 존재한다고 Thesis가 확인했다.
  * Thesis가 확인한 recovery 결손은 기존 Chrome 및 새 Chrome reattach 경로가 prompt preview의 부분 문자열 matching에 의존하고, matching 실패 시 현재 요청 identity를 충분히 제한하지 않은 응답 대기로 내려갈 수 있으며 정상 경로의 `identityScope`가 동일하게 전달되지 않는다는 것이다.
  * `promptSubmitted=true`는 전송 동작 이후의 힌트일 뿐 remote user-turn commit의 충분조건이 아니며, 필드 부재 역시 미제출을 증명하지 않는다.
  * Block 2 Entry에서 `reattach.ts` 또는 `assistantResponse.ts`의 현재 line-level 상태를 본 Baseline 작성자가 직접 재확인했다고 간주하지 않는다. 실행 Scope는 변경 전에 해당 source revision을 직접 측정해야 하며, Thesis와 다른 사실이 발견되면 authority conflict를 보고하고 Baseline의 제품 의미를 임의로 낮추지 않는다.
* **Exit:** 다음 recovery contract가 정상 경로와 동일한 authoritative readback으로 증명되어야 한다.

  * `success`를 저장하거나 반환하는 모든 browser result path가 `same conversation ∧ uniquely identified current user turn ∧ assistant owned by that turn ∧ completed response`를 검증한다.
  * current request identity는 process-local memory만이 아니라 프로세스 재시작 뒤 recovery가 사용할 수 있는 durable session/result evidence로 보존된다.
  * existing-Chrome reattach와 new-Chrome reopen/recovery 모두 동일 identity/ownership gate를 사용한다.
  * prompt preview의 prefix/substring, turn ordering만, 마지막 assistant message, copy button, 기존 completed message를 unique request identity의 대체 증거로 사용하지 않는다.
  * 같은 prompt가 두 번 존재하거나 첫 120자 등 preview 범위가 같은 경우에도 B의 recovery가 A의 답변을 반환하지 않는다.
  * 요청 B 뒤에 요청 C가 존재하고 C가 더 최신이어도 B recovery가 C 답변을 반환하지 않는다.
  * B의 user-turn identity 또는 assistant ownership evidence를 복원할 수 없으면 `uncertain`/failure로 종료하고 기존 evidence를 보존한다.
  * 제출 여부가 불확실하면 recovery는 remote prompt count를 증가시키지 않는다.
  * remote user-turn commit 후 local persistence 전에 급사한 경우를 “미제출”로 오판해 자동 재제출하지 않는다.
  * 답변 귀속은 확정됐으나 cleanup/release가 실패한 경우 answer를 보존하면서 후처리 상태를 별도로 표시한다.
  * 동일 session에 동시 또는 늦은 recovery가 도착해도 이미 확정된 다른 request result를 덮어쓰거나 현재 slot owner를 잘못 해제하지 않는다.
  * Exit verification에는 최소한 정상 경로, existing-Chrome reattach, new-Chrome recovery 및 아래 adversarial cases가 포함되어야 한다: 동일 prompt, 동일 preview prefix, target turn 미렌더링, 과거 턴만 copy button 보유, target 이후 새로운 턴 존재, prompt submission 직후 local flag 기록 전 급사, completed result 저장 후 caller 출력 전 급사.
* **Invariants:** `GI-02`, `GI-03`, `GI-04`, `GI-06`, `GI-09`, `GI-10`, `PI-05`~`PI-07`, `PI-12`, `PI-13`.
* **Continuation:** B2 Exit에서 request/session/conversation/user-turn/assistant-turn/originating-slot의 실제 durable evidence schema 또는 동등한 readback 계약을 successor에게 넘긴다. Block 3는 이 identity contract를 CLI protection 아래에서 호출할 뿐 다시 축소할 수 없다. 성공/미확정/후처리 실패의 exit semantics와 관련 test corpus도 handoff fact다.
* **Abort:** identity evidence가 일부 path에서만 기록되어 recovery가 normal path보다 약한 성공 조건을 가지거나, 새 schema 도입 때문에 기존 session을 오래된 답변으로 성공 처리할 가능성이 생기거나, ambiguity 해결을 위해 자동 resubmit/latest-answer fallback을 요구하는 경우 중단한다. 안전 목표는 **false success보다 conservative uncertain/failure를 선택하고 기존 session 및 remote conversation evidence를 보존하는 것**이다. 이미 submission 가능성이 있는 request에는 새 자동 submission을 금지한다. readback은 target request의 submission certainty, durable identity availability, result attribution certainty 및 현재 slot ownership을 각각 기록한다.
* **Insufficient for Exit:**

  * `identityScope` parameter를 함수 signature에 추가했지만 recovery call graph 전체에 적용됐는지 검증하지 않음.
  * `answer.turn_index > prompt.turn_index`만 확인.
  * prompt text/prefix가 일치하므로 current turn이라고 판정.
  * 가장 최근 completed assistant response를 반환.
  * existing-Chrome reattach만 수정하고 new-Chrome path는 기존 fallback 유지.
  * new-Chrome path만 수정하고 정상/reattach가 서로 다른 gate 사용.
  * process memory에만 identity를 저장.
  * happy-path multi-turn test 하나만 통과.
  * ambiguity case에서 error 대신 timeout 후 자동 재제출.
  * user-turn binding은 검증하지만 assistant가 그 user turn의 응답인지 검증하지 않음.
  * correct assistant를 찾았지만 streaming/`Pro thinking`/placeholder 상태를 completed로 인정.

### Block `B3-CLI-PROTECTION` — CLI 내장 보호 및 파이프라인 무결성

* **ID:** `B3-CLI-PROTECTION`
* **Name:** CLI 내장 보호 및 파이프라인 무결성
* **Meaning Contribution:** 기존에 숙련자/agent가 SKILL.md를 읽고 수행해야 했던 보호를 제품 호출 경로 자체의 기본 계약으로 이동한다. 동일 runtime을 사람, agent, scheduler가 호출해도 version/provenance, timeout, routing, attachments, live pre-submit validation 및 recovery safety가 동일하게 적용되도록 한다.
* **Order / Dependencies:** B1과 B2의 Exit가 필요하다. B3가 guard를 내장하더라도 실제 runtime provenance가 불명확하거나 recovery result가 잘못 귀속된다면 제품 안전성이 성립하지 않기 때문이다.
* **Entry:** 다음 authority를 측정한다.

  * THESIS-001은 기존 운영 지침에 `0.16.1` 호환성 확인, `--browser-timeout 2h`, 관련 경로 dry-run 및 충분한 외부 실행 시간 확보가 존재했다고 기록하며, 이를 agent-only knowledge로 남겨서는 안 된다고 확정한다.
  * `runner.py`에는 현재 command normalization과 required `--engine browser`, model strategy/remote Chrome validation, incompatible transport flag rejection, model/reasoning → compatible slots mapping이 존재한다.
  * `runner.py`에는 claim 이후 irreversible child call 전 CDP/login을 다시 확인하도록 설계된 `pre_submit_check()`가 존재한다. 이 존재만으로 모든 public entrypoint가 반드시 이를 호출한다고 본 Baseline은 추정하지 않는다. Block Scope가 실제 call path를 측정해야 한다.
  * `attachments.py`는 file-bearing request를 single ZIP으로 정규화하고 `--wait`, attachment policy, cleanup/manifest 동작을 갖지만, 해당 구현의 안전성이 CLI의 모든 public entrypoint와 CI에서 자동 보장되는지는 별도 Exit 조건이다.
* **Exit:** 다음 호출자 독립 계약이 제품 CLI 자체에서 성립해야 한다.

  * `run`, `submit`, `followup` 및 제품이 공개하는 recovery 진입 경로가 동일한 release/provenance compatibility 검사와 fail-closed 원칙을 공유한다.
  * 사용자가 별도 timeout을 지정하지 않은 browser response wait에는 실제 기본값 `2h`가 적용된다.
  * 명시 timeout override가 있으면 유효성을 검증하고 값을 보존하며 실제 적용값을 CLI/session readback에서 식별할 수 있다.
  * queue wait, preparation, attachment packaging, response wait, cleanup을 의미상 하나의 “2h timeout”으로 오인시키지 않는다.
  * unsupported/mismatched runtime, invalid argument combination, invalid routing/model/Power, attachment selection/ZIP failure는 irreversible remote submission 전에 거절한다.
  * slot claim 뒤 실제 submission 직전에는 CDP/login, target conversation/URL, 모델/Power, attachment upload readiness 등 시간에 따라 바뀔 수 있는 조건을 해당 path에 필요한 수준으로 재검증한다.
  * preflight/dry-run/preview는 선택적 비제출 기능이며, 사용자가 먼저 호출하지 않아도 실실행이 같은 mandatory checks를 자체 수행한다.
  * file-bearing request는 정확히 한 개의 compressed ZIP을 사용하며 attachment-free request에는 artificial ZIP을 만들지 않는다.
  * SKILL.md를 읽지 않은 일반 shell 사용자도 동일한 default timeout과 보호를 받는다.
  * scheduler가 browser response가 끝나기 전에 자체 process timeout으로 child를 죽일 수 있는 경우에도 제품 state가 중복 submission 또는 false success로 전환되지 않는다. 제품은 가능한 경우 caller가 설정해야 하는 외부 execution ceiling과 실제 browser timeout을 명확히 구분해 노출한다.
  * B2의 identity/result attribution gate는 CLI 보호에 의해 우회되지 않는다. `exit 0`은 attribution이 확정된 success 또는 명시적으로 정의된 non-submitting operation에만 부여한다.
  * Python wrapper의 핵심 protection regression suite가 pytest로 자동 실행되며 CI의 필수 green condition에 들어간다.
  * package/build side의 필요한 TypeScript/build/packed runtime 검증과 Python pytest가 release candidate에 대해 동일 provenance를 대상으로 실행된다. 서로 다른 source/build를 테스트한 green 결과를 합성하지 않는다.
* **Invariants:** 모든 Global Invariant, 특히 `GI-03`~`GI-08`, `GI-11`; `PI-08`~`PI-13`.
* **Continuation:** Block 4로 넘기는 handoff에는 exact release candidate identity, 설치 artifact, default/override timeout readback, mandatory pre-submit guard matrix, supported public entrypoints, pytest/빌드 검증 결과가 포함되어야 한다. Block 4 환경은 이 artifact를 수정 없이 설치해야 하며 source checkout fallback을 허용하지 않는다.
* **Abort:** public entrypoint 사이에 guard 차이가 남아 있거나, default `2h`를 넣기 위해 caller script/agent prompt 수정이 필요하거나, pre-submit validation이 remote submission 후에야 실패를 발견하거나, CI가 pytest 실패를 무시할 수 있거나, packed artifact와 CI가 검증한 build identity가 다른 경우 중단한다. 안전 목표는 release promotion 및 다음 Block 진행을 막는 것이다. runtime 중 이미 uncertain submission이 생성됐다면 재시도하지 않고 B2 계약으로 수거/격리한다. readback에는 entrypoint별 guard 적용 여부, 실제 timeout 값, submission 가능성, artifact provenance 및 failing CI gate를 남긴다.
* **Insufficient for Exit:**

  * SKILL.md에 timeout/dry-run 지침을 더 명확히 작성.
  * agent wrapper가 매번 `--browser-timeout 2h`를 주입.
  * 별도 `doctor`가 성공하지만 `run` 자체는 검사하지 않음.
  * `run`만 보호하고 `submit`/`followup`/recovery는 다른 검증 사용.
  * unit test에서는 default가 2h이지만 실제 packed CLI에서 다른 default 사용.
  * `pre_submit_check()` 함수가 존재하지만 public execution path에서 호출됨을 증명하지 못함.
  * local pytest green이나 local Vitest/build green 중 하나만 존재.
  * CI job은 존재하지만 allowed-failure/optional이어서 merge/release를 차단하지 못함.
  * dry-run 성공을 실제 submission 순간의 login/model/attachment readiness로 간주.
  * child exit 0을 current-turn result attribution 검사 없이 wrapper success로 그대로 승격.

### Block `B4-CLEAN-E2E` — 종단간 클린 환경 구동 검증

* **ID:** `B4-CLEAN-E2E`
* **Name:** 종단간(E2E) 클린 환경 구동 검증
* **Meaning Contribution:** B1~B3가 개별 source/test 수준에서만 성립한 것이 아니라, 실제 사용자에게 전달되는 release candidate가 원 개발자 환경 없이 Product Thesis의 전체 효용을 닫는다는 최종 authoritative evidence를 만든다.
* **Order / Dependencies:** B1, B2, B3 Exit 후 수행하는 최종 transition Block. 이 Block은 새로운 product semantics를 발명하는 단계가 아니라 앞선 모든 Required Named Item의 installed-runtime readback 단계다.
* **Entry:** 다음이 모두 필요하다.

  * B3에서 고정한 exact release candidate/install artifact identity.
  * source checkout이 아닌 설치 artifact를 사용할 수 있는 상태.
  * 신규 격리 Linux/WSL2 환경 또는 동등한 clean environment.
  * 원 개발자의 `/home/user01`, 해당 NVM directory, 기존 global `@steipete/oracle`, 개발 source checkout, 임시 compatibility symlink가 환경에 존재하지 않거나 제품이 접근할 수 없는 상태.
  * 선언된 지원 platform precondition만 준비한다: Node `>=24` 또는 실제 release가 승인한 해당 platform runtime, Python runtime, 지원 Chrome/CDP, 필요한 사용자 로그인 및 외부 네트워크.
  * B1~B3의 CI/verification이 동일 candidate에 대해 green.
  * E2E 시작 전 slot/session state가 known-clean 또는 명시적으로 prepared되었다는 readback.
* **Exit:** 아래 E2E observations 전체가 동일 installed candidate에서 입증되어야 한다.

  * **Install/resolve:** 다른 HOME 및 다른 absolute install prefix에 설치되고 `oracle`/wrapper가 개인 NVM이나 source checkout 없이 self-contained compatible runtime을 resolve한다.
  * **Provenance:** 실행 전후 actual executable과 relevant selector/browser components가 같은 release identity임을 읽을 수 있다.
  * **No-file normal request:** agent-specific instruction 없이 정상 browser request가 실행되고 default `2h`가 적용되며 current model/Power/turn을 검증하고 정확한 response를 저장·조회한다.
  * **File-bearing normal request:** 여러 선택 원본이 정확한 selection semantics에 따라 단 하나의 compressed ZIP으로 생성되고 하나의 attachment로 등록된다. manifest/readback이 selected file set, ZIP identity와 request/session lineage를 연결한다.
  * **Attachment-free invariant:** 첨부 없는 요청에는 ZIP이 생성·업로드되지 않는다.
  * **Duplicate request:** 동일 request identity의 동시/반복 실행이 외부 prompt duplication을 만들지 않는다.
  * **Slot competition:** 서로 다른 requests가 같은 managed slot을 경쟁할 때 동시에 두 owner가 승인되지 않는다.
  * **Followup continuity:** followup은 originating slot/profile/conversation을 보존하고 해당 slot이 사용 불가하다는 이유로 다른 빈 slot 또는 새 conversation으로 이동하지 않는다.
  * **Recovery — existing Chrome:** 동일 conversation에 완료된 A와 target request B가 존재할 때 B 중단 후 reattach가 B의 durable identity를 통해 B assistant만 회수한다.
  * **Recovery — reopened/new Chrome:** 동일 조건에서 browser 재개방이 필요해도 같은 attribution gate를 통과한다.
  * **Ambiguous repeated text:** A/B prompt가 동일하거나 preview prefix가 동일해도 과거 A를 B success로 반환하지 않는다.
  * **Later-turn contamination:** B 뒤에 C가 존재해도 C assistant를 B result로 저장하지 않는다.
  * **Missing identity:** B 귀속 증거가 충분하지 않으면 false success가 아니라 uncertain/failure로 종료되고 remote prompt count가 증가하지 않는다.
  * **Crash after submission attempt:** send action과 local `promptSubmitted`/commit evidence persistence 사이 급사를 모사하거나 동등하게 검증했을 때 flag 부재를 자동 retry 허가로 사용하지 않는다.
  * **Crash after result persistence:** response가 authoritative storage에 저장된 뒤 caller output 전에 종료되어도 재조회로 동일 결과를 회수하고 새 prompt를 제출하지 않는다.
  * **Owner death:** SIGKILL/OOM 또는 owner identity disappearance 후 다음 status/claim이 slot을 자동 AVAILABLE로 사용하지 않고 격리한다. 명시적 prepare/reprepare 후에만 재사용된다.
  * **Post-result cleanup failure:** current-turn answer가 확정된 뒤 ZIP cleanup/manifest/slot release 일부가 실패하는 case에서 answer를 보존하고 cleanup failure/slot isolation을 별도 보고한다.
  * **Unsupported runtime:** incompatible/missing runtime component는 remote submission 전에 원인을 표시하며 종료한다.
  * **Result readback:** saved result를 caller process와 독립적으로 request/session identity로 다시 조회할 수 있다.
  * **CI correlation:** E2E artifact identity가 B3 CI가 검증한 artifact identity와 동일하거나 승인된 cryptographic/provenance relation으로 연결된다.
  * **Final aggregation:** 위 readback과 B1~B3 Exit facts를 함께 평가해 Transformation Completion Predicate의 모든 conjunct가 known true여야 한다.
* **Invariants:** 모든 Global Invariant 및 모든 Path Invariant. Block 4에서는 해당 불변식을 source-level expectation이 아니라 installed-runtime observation으로 다시 확인한다.
* **Continuation:** B4의 다음 단계는 자동 Block이 아니라 **Transformation Completion approval**이다. 본 draft는 배포/registry publish/production rollout 권한을 부여하지 않는다. B4 Exit 후에도 승인권자가 Final Authoritative Readback을 읽고 이 exact Baseline revision의 Completion Predicate 충족 여부를 명시적으로 판정해야 한다. 실패한 E2E에 unknown non-idempotent remote effect가 남았다면 approval로 진행하지 않는다.
* **Abort:** clean environment가 실제로 원 개발자의 global install/source를 참조하는 것이 발견되거나, candidate provenance가 B3와 다르거나, false-success/duplicate submission/slot dual ownership 가능성이 관찰되거나, E2E 중 target request의 remote effect가 unknown 상태가 된 경우 즉시 신규 submission sequence를 중단한다. 안전 목표는 evidence-preserving quarantine다: 현재 session/result/log/slot ownership 및 remote conversation을 보존하고, uncertain request를 재전송하지 않으며, dirty slot은 reprepare 전까지 재사용하지 않는다. clean environment를 지워 “다시 깨끗하게” 만드는 것은 evidence readback 이후에만 가능하다.
* **Insufficient for Exit:**

  * 개발 checkout에서 E2E 성공.
  * 같은 `/home/user01` HOME에서 PATH만 바꾸어 실행.
  * 개인 NVM/global package를 그대로 mount.
  * attachment-free happy path 하나만 성공.
  * fresh install은 성공하지만 recovery를 실행하지 않음.
  * normal recovery만 성공하고 repeated-prompt/next-turn contamination counterexample을 검증하지 않음.
  * E2E stdout에 `completed`가 출력됐지만 session/turn/result evidence를 대조하지 않음.
  * slot release가 성공했다는 이유로 answer attribution을 생략.
  * browser answer가 보인다는 이유로 설치 artifact provenance를 확인하지 않음.
  * source tests와 clean runtime이 서로 다른 build인데 version 문자열만 동일.
  * 실패 환경을 즉시 삭제하여 submission 여부/owner state를 더 이상 판정할 수 없음.
  * packed artifact 생성 또는 npm/pnpm install 성공만으로 제품 완료 선언.

## Safe Continuation

Safe Continuation Predicate:

* 현재 측정 대상 Block의 모든 Exit conjunct가 authoritative readback에서 known true이고, 그 Block이 만든 모든 비가역적 또는 비멱등적 효과가 **확정된 결과, 확정된 미제출, 또는 명시적으로 격리된 uncertain state** 중 하나로 분류되며, 다음 Block이 기존 request를 다시 제출하거나 active owner를 침범하지 않아도 시작할 수 있어야 한다.
* 특히 remote Browser interaction을 수행한 Block에서는 `unknown whether submitted` 상태 자체가 continuation 금지는 아니다. 다만 그 request가 보존되고 자동 재제출이 금지되며, 관련 slot/session이 다음 작업의 안전성을 침범하지 않도록 격리된 경우에만 handoff-safe하다.
* `tests passed`, `process exited`, `slot file disappeared`, `no error observed`만으로는 Safe Continuation을 증명하지 않는다.

Required handoff facts and readbacks:

* 현재 Block의 exact ID, Baseline revision, 구현/검증 source revision 및 실제 runtime/release candidate identity.
* 각 Exit conjunct의 measured result와 그 authoritative source.
* 실행물 provenance: 실제 launcher/CLI가 무엇이었고 attachment selector/browser implementation이 어떤 동일 release identity에 속했는지.
* remote effects를 만들었던 모든 request의 request/session/conversation/turn 상태: not-submitted, committed/owned/completed, uncertain 중 어느 것인지.
* active 또는 최근 사용 slot의 owner identity, release 여부, `requires_reprepare` 또는 동등한 quarantine 상태.
* attachment request가 있었다면 selected file set, generated ZIP identity, registration/cleanup/manifest readback.
* 이미 확정된 결과와 후처리 failure를 구별한 readback.
* 현재까지 만족된 Required Named Items와 아직 남은 Required Named Items.
* Global/Path Invariant 위반이 없다는 근거. 위반이 있었다가 containment된 경우 그 사실과 containment boundary.
* successor가 시작하기 전에 다시 검사해야 할 volatile facts: installed artifact identity, CDP/login, slot availability/owner, target conversation, current model/Power 및 외부 UI readiness.
* successor에게 전달할 exact Source Authority: THESIS-001 fingerprint, 이 BASELINE revision, current approved Scope/Mandate 및 predecessor Exit evidence.

Successor authority:

* 본 `DRAFT` revision에서는 caller/host가 다음 Block 자동 시작 권한을 갖지 않는다. `Inter-Block auto-continuation authorized: no`.
* 향후 승인 revision이 auto-continuation을 허용하더라도 그 권한은 승인된 continuation ceiling까지만 유효하며 Safe Continuation Predicate 실패 시 즉시 소멸한다.
* successor는 THESIS-001의 제품 의미와 이 Baseline의 불변식을 모두 입력으로 받아야 한다. predecessor가 남긴 구현 문서나 테스트 결과만 전달받아 제품 권위를 대체해서는 안 된다.
* successor Scope는 predecessor Exit readback을 재사용할 수 있으나 mutable/volatile 사실은 entry 시점에 다시 측정해야 한다.

Absence of an observed danger is not proof of Safe Continuation. If the predicate or any required readback is unknown, do not perform an automatic handoff.

## Safe Abort

Trigger:

* Global 또는 Path Invariant가 실제로 위반되었거나 위반 여부를 판정할 수 없는 상태가 발생한다.
* 실제 실행 artifact의 provenance가 source/CI가 검증한 artifact와 일치하지 않는다.
* remote prompt가 제출됐을 가능성이 있으나 현재 request의 user-turn commit 여부를 확인할 수 없다.
* current request의 assistant ownership/완결을 입증할 수 없는데 success로 처리하려는 경로가 발견된다.
* 동일 slot에 복수 owner가 승인됐거나 current owner identity를 검증할 수 없다.
* recovery가 다른 turn을 반환하거나 자동 재제출해야만 진행할 수 있는 구조가 드러난다.
* clean environment가 개인 NVM, source checkout 또는 미선언 global package를 참조한다.
* required CI/E2E gate가 실패하거나 provenance를 잃어 더 이상 유효한 검증 결과로 사용할 수 없다.
* Scope가 THESIS-001의 제품 의미를 변경해야만 진행할 수 있다고 판단된다. 이 경우 구현자는 Thesis를 임의 수정하지 않고 상위 authority로 되돌린다.

Authorized safe target state:

* 신규 remote submission이 더 발생하지 않는다.
* 이미 확정된 request result는 보존한다.
* submission 가능성이 있으나 귀속이 확정되지 않은 request는 `uncertain` 또는 동등한 fail-closed 상태로 보존하고 자동 retry하지 않는다.
* owner가 불명확하거나 crash-contaminated slot은 AVAILABLE로 재사용하지 않고 명시적 reprepare가 필요한 quarantine 상태로 둔다.
* partially generated ZIP/session/result artifacts 중 증거 가치가 있는 자료를 debugging 전에 파괴하지 않는다.
* 새 runtime artifact가 불완전하면 promotion/use를 중지한다. 이전 runtime으로 자동 rollback할 수 있다고 가정하지 않는다. 이전 runtime이 별도로 known-safe이고 rollback authority가 실제 존재하는 경우에만 그 별도 authority에 따라 전환할 수 있다.
* source repository가 중간 구현 상태에 있더라도 product traffic이나 후속 Block이 그 상태를 승인된 runtime으로 오인하지 않도록 release/provenance boundary를 닫는다.
* Abort는 “원래 상태로 완벽 복구”를 의미하지 않는다. 핵심은 추가 비가역 효과와 false success를 멈추고, 남아 있는 unknown을 정확히 격리하는 것이다.

Owner and action boundary:

* 현재 승인된 Scope의 implementer/operator는 신규 실행 정지, evidence 보존, 해당 Scope가 만든 임시 artifact 정리 중 안전성이 입증된 부분, unsafe candidate의 promotion 차단까지 수행할 수 있다.
* uncertain request의 재제출, slot state 수동 삭제, conversation 대체 생성, 다른 slot으로 followup 이동, lower model/Power fallback, production deployment, registry publish 또는 기존 사용자 데이터 파괴는 본 Abort 권한에 포함되지 않는다.
* `prepare --slot N` 또는 동등한 explicit reprepare는 해당 slot의 활성 owner가 없고 기존 상태를 침범하지 않는다는 readback 이후에만 허용되는 별도 복구 경계다.
* Abort 중에도 이미 확정된 response를 cleanup 편의를 위해 삭제하지 않는다.

Authoritative readback:

* exact runtime/build provenance와 마지막 실행 command identity.
* affected request들의 submission certainty 및 durable request/session/conversation/user-turn/assistant-turn evidence.
* persisted answer의 존재 및 attribution 상태.
* 각 affected slot의 owner identity, availability/quarantine/reprepare 상태.
* attachment ZIP/manifest/cleanup 상태.
* 어떤 Exit condition이 미충족 또는 unknown인지.
* 어떤 effect가 이미 되돌릴 수 없고, 어떤 effect가 단순히 실행되지 않았는지.
* 이 readback만으로 safe target을 입증할 수 없다면 Abort 상태 자체를 `contained but incomplete/unknown`으로 표시하며 정상 상태로 선언하지 않는다.

## Atomic Boundary

`HARD_ATOMIC` keeps an indivisible cutover inside one Scope. Internal technical units are not independently completed product Scopes and do not permit handoff in the middle. Split only where a safe, durable, independently observable state exists.

### HARD_ATOMIC boundaries

| Boundary                                          | Required indivisible cut                                                                                                   | Why it is atomic                                                                                                                                                                        |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `HA-01 Runtime identity closure`                  | production CLI resolution, selector/file-selection provenance, attachment execution boundary 및 같은-release compatibility 판정 | 새 CLI가 옛 global selector를 사용하거나 새 selector가 개인 NVM CLI를 실행하는 중간 cut은 GI-05를 깨뜨린다. 따라서 “한쪽만 새 runtime”인 상태를 product-complete Scope로 handoff할 수 없다.                                       |
| `HA-02 Durable identity writer ↔ recovery reader` | current request/turn identity를 durable state에 쓰는 경로와 recovery가 그 evidence를 읽어 identityScope/동등 gate를 구성하는 경로               | writer 없이 reader를 강화하면 recovery가 모든 요청을 거절할 수 있고, reader 없이 writer만 배포하면 false-success path가 계속 남는다. schema 변경이 필요한 경우 해당 compatibility contract까지 같은 atomic cut에 포함한다.                 |
| `HA-03 Recovery success gate parity`              | existing-Chrome reattach, new-Chrome recovery 및 최종 assistant completion/ownership 판정                                       | 한 recovery path라도 text/latest-message fallback을 유지하면 “recovery success”라는 제품 의미가 path에 따라 달라진다. B2 Exit까지는 세 경로를 독립 completed product scope로 취급하지 않는다.                                  |
| `HA-04 Uncertain-submission no-resubmit contract` | send-attempt/commit uncertainty 표현, retry suppression, recovery entry behavior                                             | uncertain 상태를 기록하지만 caller/recovery가 이를 failed-before-submit으로 읽어 자동 retry하면 duplicate prompt가 생긴다. producer와 consumer semantics를 같은 cut에서 맞춘다.                                         |
| `HA-05 Result persistence ↔ success publication`  | authoritative current-turn result 저장과 CLI/session success publication                                                      | stdout/exit success가 먼저 노출되고 durable result attribution write가 실패할 수 있는 cut은 caller에게 recoverable evidence 없는 성공을 줄 수 있다. success publication은 authoritative result condition과 함께 전환한다. |
| `HA-06 Slot owner mutation`                       | claim owner identity write, release owner comparison, owner-loss quarantine semantics                                      | claim/release의 일부만 바꾸면 stale owner가 새 owner를 해제하거나 crash slot이 자동 재사용될 수 있다. 변경이 필요할 경우 한 제품 cut으로 검증한다.                                                                                |
| `HA-07 Production default safety semantics`       | 기본 `2h`, mandatory pre-submit validation, unsupported-runtime fail-closed가 실제 public entrypoint에 적용되는 cut                  | 문서/agent wrapper에만 새 default가 있고 CLI production path는 옛 의미를 유지하는 상태는 제품 protection 전환이 아니다.                                                                                             |

### Splittable boundaries

* B1 내부의 구체적 resolver 구현, provenance formatting, diagnostics UI는 각각 durable compatibility contract를 보존한다면 별도 Scope로 나눌 수 있다. 단 `HA-01` 중간에서는 handoff하지 않는다.
* packed-runtime smoke와 clean alternate-prefix non-submitting smoke는 runtime cutover가 이미 안전하게 닫힌 뒤 별도 verification Scope로 분리할 수 있다.
* B2의 adversarial test case 추가는 production recovery gate가 이미 fail-closed이고 각 중간 상태가 false success를 만들지 않는다면 여러 Scope로 확대할 수 있다.
* `doctor`/diagnostic command는 optional Candidate Mean이므로 core CLI safety가 이미 존재한 뒤 독립적으로 추가할 수 있다.
* B3의 pytest test authoring, CI workflow wiring, packed artifact verification은 각 단계가 production runtime semantics를 약화하지 않는다면 기술적으로 분리 가능하다. 그러나 세 결과가 모두 존재하기 전에는 B3 Exit가 아니다.
* 문서 개선과 operator diagnostics는 runtime behavior와 독립적으로 관찰 가능하면 별도 Scope로 나눌 수 있다.
* Block 4의 정상 실행, attachment, concurrency, crash/recovery scenarios는 서로 다른 E2E execution Scope로 나눌 수 있다. 각각의 run은 자체 Safe Continuation/Abort readback을 가져야 하며, 전체 scenario matrix가 완료되기 전에는 B4 Exit 또는 Transformation Completion을 선언하지 않는다.
* Block 간 분할은 각 predecessor의 Safe Continuation Predicate가 참일 때만 가능하다. “다음 작업이 작다”거나 “테스트가 대부분 통과했다”는 분할 가능성의 근거가 아니다.

### Atomicity interpretation

* `HARD_ATOMIC`은 모든 관련 코드를 한 commit에 넣어야 한다는 의미가 아니다. 개발 commit은 여러 개일 수 있으나 **제품이 사용하거나 successor가 전제하는 runnable cut**에서는 atomic contract 전체가 닫혀 있어야 한다.
* source가 중간 commit을 갖는 것은 허용되지만 해당 commit을 production candidate, Block Exit, handoff-safe state로 선언해서는 안 된다.
* 기술적으로 rollback하기 어려운 browser remote submission은 atomic local transaction으로 만들 수 없으므로, atomicity를 “exactly-once send”라고 허위 선언하지 않는다. 대신 irreversible-send 경계 앞의 검증과 send 이후 uncertainty의 fail-closed handling을 atomic product contract로 취급한다.
* 서로 다른 파일의 durable state를 하나의 분산 트랜잭션인 것처럼 가정하지 않는다. 부분 write가 가능한 경우 reader가 incomplete/conflicting evidence를 성공으로 읽지 않는 것이 필수 atomic safety property다.

## Placement and Use

본 Baseline은 `/home/user01/project/oracle`의 Oracle Browser 자기완결적 프로덕션 런타임 전이에 대해서만 사용한다. 실제 저장 위치와 revision identity는 승인 과정에서 프로젝트 로컬의 승인된 planning path에 고정되어야 하며, 저장 후 내용 변경은 새로운 immutable revision으로 수행한다.

본 문서는 THESIS-001의 대체물이 아니다. Product meaning conflict가 발생하면 THESIS-001의 해당 의미를 우선하며, 구현 편의를 위해 Baseline에서 Required Outcome이나 Truth / Causal Invariant를 약화하지 않는다.

각 실행 Scope는 자신의 Transition Authority에 이 exact Baseline revision과 Thesis fingerprint를 원본으로 결합해야 한다. Scope는 현재 Block의 Entry → Exit에 필요한 최소 변경과 검증만 승인받으며 미래 Block의 구현을 작업 큐처럼 선승인받았다고 간주하지 않는다.

본 DRAFT는 코드 변경, release 생성, registry publish, external deployment, Browser request 실행 또는 다음 Block 시작 권한을 자체적으로 부여하지 않는다. 특히 `Inter-Block auto-continuation authorized: no`이므로 Block Exit를 달성했다는 구현자 판단만으로 successor Block을 자동 시작할 수 없다.

향후 APPROVED revision이 생성될 경우에도 그 승인 범위는 문서에 명시된 continuation ceiling까지만 유효하다. Safe Continuation Predicate가 false 또는 unknown이면 자동 handoff 권한은 사용하지 않는다.

최종 제품 완성 판정은 B4 종료 보고 하나가 아니라 Transformation Outcome의 Completion Predicate와 Final Authoritative Readback 전체를 다시 읽어 내린다. 패키지 생성, 개별 test suite green, 한 번의 Browser 성공 또는 하위 Block Exit는 전체 제품 완성의 대체 증거가 아니다.
