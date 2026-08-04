---
title: Implementation Lead / Verification Lead Simplification Plan
status: design-reset-skeleton
branch: refactor/simplify-implementation-verification
---

> [!CAUTION]
> **주 설계자 실행 강제 규칙 — 모든 단계와 모든 Oracle 라운드에 최우선 적용**
>
> - 한 단계를 시작하면 초안 작성이나 첫 Oracle 답변에서 멈추지 않는다. 그 단계의 단일 결정이
>   충분한 근거로 닫히고 모든 finding이 수용·거부·위임·사용자 결정 필요로 명시적으로 판정되어
>   `DESIGN_CONVERGED`가 될 때까지 같은 단계 안에서 설계 수정과 Oracle follow-up을 계속한다.
>   `USER_DECISION_REQUIRED`가 남으면 다음 단계로 넘어가지 않고 사용자에게 결정 근거와 선택지를
>   제시한다.
> - Oracle의 finding, severity, 표현상의 확신 또는 `CONVERGED` 선언을 절대 그대로 수용하지 않는다.
>   **모든 finding은 수용 여부를 검토하기 전에 주 설계자가 기각할 수 있는 가장 강한 반론부터
>   작성한다.** 그 뒤에만 사용자 가치 훼손, source·test·runtime 근거, 현재 단계 소유권,
>   더 작은 correction의 가능성, 복잡성 순증가를 확인해 판정한다.
> - 모든 initial prompt와 follow-up에는 이 문서의 취지 방어문을 의미 축소 없이 넣는다. Oracle과의
>   합의, Critical/High 0건 또는 문서의 완전무결성을 사용자 목적보다 우선하지 않는다.
> - 실제 근거가 입증된 정확성·사용자 변경 보존·독립 검증·source·AC·evidence 결속 문제는
>   가장 작은 correction으로 수용한다. 근거 없는 복잡성, 범위 확장, 가상 위협 과적합, 구
>   메커니즘의 이름만 바꾼 재도입은 거부한다.
> - 사용자 취지를 약화하거나 정상 실행 비용과 caller Interface를 불필요하게 키워 얻은
>   `DESIGN_CONVERGED`는 무효이며 실패다. 주 설계자는 이를 수렴으로 보고하거나 다음 단계로
>   진행해서는 안 된다.
> - 채팅 기억, 대화 요약 또는 주 설계자의 자기 보고는 실행 상태의 authority가 아니다. 컨텍스트
>   압축·중단·새 세션·담당자 교체 뒤에는 작업 전에 반드시 이 문서를 처음부터 다시 읽고,
>   아래 `실행 체크포인트`, 현재 단계 설계, Oracle 원문과 finding 판정 기록, 로컬 diff를 서로
>   대조한다. 기억에 의존해 생략된 절차를 완료한 것으로 간주하지 않는다.
> - 주 설계자는 source 조사, 초안 수정, Oracle initial/follow-up, finding 판정처럼 상태가 바뀌는
>   작업 직후 아래 `실행 체크포인트`를 갱신한다. 최소한 현재 단계와 상태, 마지막 완료 작업,
>   Oracle session, 열린 finding·사용자 결정, 바로 다음 행동을 기록한다. 체크포인트가 실제 파일·
>   transcript·diff와 다르면 더 진척됐다고 가정하지 말고 확인 가능한 마지막 상태로 되돌린다.
> - **Oracle 자기참조·재위임 금지:** Oracle은 지정된 local source·test·runtime 근거를 읽는
>   reviewer일 뿐, Oracle 운영자가 아니다. Oracle은 `oracle`·`oracle-browser-slots`를 실행하거나,
>   Oracle session·slot·browser·metadata·transcript를 조회·대기·관리하거나, 자기 자신·다른
>   Oracle·다른 모델·agent에게 검토를 재위임하거나, 그런 활동의 결과를 finding 근거로 사용해서는
>   안 된다. Oracle의 저장 transcript는 주 설계자가 이미 완료된 답변을 회수할 때만 읽을 수 있는
>   delivery artifact이며, session 상태·모델 상태·slot 상태는 설계 근거가 아니다.
> - Oracle 답변이 위 금지를 어기면, 주 설계자는 해당 session-operation 주장과 거기에 의존한
>   결론을 `REJECT_AS_SCOPE_EXPANSION`으로 판정하고 설계 근거에서 제외한다. 그 답변의 나머지도
>   지정 source·test·runtime으로 독립 재구성할 수 있을 때만 검토한다. 새 Oracle follow-up은
>   사용자에게 이 사실을 알리고, self-operation을 금지한 새 prompt가 필요한지 명시적으로
>   판단한 뒤에만 시작한다.

## 실행 체크포인트 — 컨텍스트 복구 authority

```text
현재 단계: Phase 1 — 목적 보존 테스트 구현
단계 상태: IMPLEMENTED (목적 보존 직접 검증 통과)
마지막 완료 작업:
- 전용 worktree와 refactor/simplify-implementation-verification branch 확인
- Implementation Lead, Verification Lead, Baseline Capsule의 source·test·CLI·실제 in-repo 소비자 조사
- baseline-capsule, implementation-lead, verification-lead 전체 테스트 통과 확인
- `PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md`에 Phase 1 목적 보존 계약 초안 작성
- Oracle initial review `slots-context-phase1pu-db7cf3504d` 완료; F1과 F2를
  `ACCEPT_WITH_BOUNDARY`로 판정하고 초안에 반영
- same-session follow-up `slots-followup-phase1pu-3a57580625` 완료; F1·F2는 닫혔고
  F3를 `ACCEPT_WITH_BOUNDARY`로 판정해 초안에 반영
- 세 번째 follow-up `slots-followup-phase1pu-3452bd7664`에서 Oracle이 자기 Oracle session
  readback을 시도한 사실을 확인; 그 session-operation 주장과 거기에 의존한 결론은 채택하지 않음
- 문서 최상단에 Oracle 자기참조·재위임 금지와 위반 답변 처리 규칙을 추가
- F1~F3 correction을 이 문서·Implementation Lead·Verification Lead·Ticket authority와
  runtime baseline에만 대조해 재공격; 새 Phase 1 finding 없이 `DESIGN_CONVERGED`로 판정
- 2026-08-04 전용 worktree·branch·untracked 설계 문서 두 개를 다시 대조
- 2026-08-04 `baseline-capsule/run_tests.py`, `implementation-lead/run_tests.py`,
  `verification-lead/run_tests.py`를 다시 실행해 모두 통과 확인
- 현재 외부 command surface와 restart/recovery 의미를 Phase 2 시작 근거로 목록화
- `PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md` 초기 초안 작성
- `implement(work, worker)`, `verify(candidate)`, `inspect(work)`의 세 의미 호출과
  fail-closed restart 의미를 Phase 2 공격 대상 Interface로 선정
- Oracle session `slots-context-phase2in-dfd8b94afb`를 슬롯 3 ZIP 첨부 방식으로 잘못 시작;
  계획의 DevSpace 모드와 사용자 슬롯 지시를 어긴 실행이므로 답변·finding 전체를 설계 근거에서 제외
- DevSpace `devspace-http.service` active, PID와 local `/healthz` 성공, 모든 review 대상이
  허용 root `/home/user01/project` 아래임을 확인
- 사용자 지시에 따라 managed slot 1과 2를 각각 `prepare`했으나, 둘 다 CDP 응답과 달리
  `/proc`에서 port/profile Chrome 소유 증거를 확립하지 못해 wrapper가 `사용 불가`로 거부
- slot 1 stale Chrome top PID를 정상 종료한 뒤 wrapper `prepare --slot 1`로 새 Chrome를 준비;
  slot 1 `사용 가능`, login과 CDP `127.0.0.1:19222` 확인
- DevSpace 모드·무첨부 Oracle initial `slots-context-phase2de-ffc3ec047b` 완료
- F1 drift 전 exact contradiction 보존, F2 UNDETERMINED 뒤 safe fresh verification,
  F3 ready Ticket의 별도 product-root 중복 authority 제거를 모두 source와 test에 대조해 반영
- same-session follow-up `slots-followup-phase2de-06b3dae245` 완료; F3 CLOSED, F1/F2 STILL_OPEN,
  F4 durable ImplementationStopped 제안 확인
- follow-up F1은 valid historical result와 currentness 관찰을 분리해 반영, F2는 VerificationResult에서
  exact Candidate를 복구 가능하게 보강, F4는 Phase 1 비보존 결과를 durable protocol로 늘려 거부
- second same-session follow-up `slots-followup-phase2de-5c4baa3a43` 완료; F1/F2 CLOSED,
  F4 REJECTION_JUSTIFIED, correction regression·새 material finding·사용자 결정 없음 확인
- Oracle 선언이 아니라 Phase 1과 current source에 correction/거부를 재대조해 Phase 2
  `DESIGN_CONVERGED` 판정
- current workflow store의 nodes/edges/claims/actors/invocations/budget/run/transaction schema,
  unique active claim, atomic successor publication과 관련 race/restart test 조사
- Phase 3 보존 대상을 work별 unique head, 최대 한 active transition, atomic complete-result append로 축소
- `PHASE-3-DURABLE-WORK-STATE-CONTRACT.md` 초기 초안 작성
- 2026-08-04 workflow-store 53개, implementation-result 20개, verification-run 64개 test를
  현재 worktree에서 다시 실행해 모두 통과 확인
- Phase 3 DevSpace Oracle initial `slots-context-phase3de-87291b0486` 완료
- F1 cross-work overlapping source mutation은 hidden mutation-domain occupancy로 최소 반영
- F2 Ticket rename/copy stable identity는 Phase 2 exact Ticket authority와 실제 consumer 근거가 없어
  `REJECT_AS_SCOPE_EXPANSION`; rename/move/copy를 새 work로 명시
- same-session follow-up `slots-followup-phase3de-6b237afa3b` 완료; F2 REJECTION_JUSTIFIED,
  F1은 occupancy 후 source recheck ordering과 Candidate publication atomic release 누락으로 STILL_OPEN
- follow-up F1의 두 잔여 경로를 새 state 없이 ordering invariant와 atomic commit membership으로 반영
- second same-session follow-up `slots-followup-phase3de-279e3c87b2` 완료; F1 CLOSED,
  F2 REJECTION_JUSTIFIED, 새 material finding·사용자 결정·legacy ceremony 회귀 없음 확인
- Oracle 선언이 아니라 Phase 1/2와 current source/test에 correction/거부를 재대조해 Phase 3
  `DESIGN_CONVERGED` 판정
- Phase 4 시작 전 Phase 1~3 계약과 plan checkpoint 전체 재대조
- current Implementation Lead의 Baseline Capsule, ownership snapshot, sequential Worker loop,
  implementation check, handoff publication source·test 조사
- same-path 선행 external change 뒤 Worker가 canonical source를 덮어쓴 다음 publication만 fail-closed하는
  현재 test/runtime 경로를 사용자 변경 보존의 실제 결함으로 식별
- `PHASE-4-IMPLEMENTATION-EXECUTION-CONTRACT.md` 초기 초안 작성
- Worker를 private candidate workspace에 격리하고 B/W/L three-source adoption으로 사용자 동시 변경을
  canonical mutation 전에 분리하는 단일 실행 결정을 선정
- 2026-08-04 `baseline-capsule/run_tests.py`, `implementation-lead/run_tests.py`,
  `verification-lead/run_tests.py`를 다시 실행해 모두 통과 확인
- Phase 4 DevSpace Oracle initial `slots-context-phase4in-d28c668059` 완료
- F1 check-then-write race는 source-preserving linearized conditional mutation으로 최소 반영
- F2 crash recovery ABA는 per-path ledger 없이 may-have-started 뒤 automatic write resume 금지로 반영
- F3 Phase 3 occupancy-before-Worker 문구를 first canonical mutation으로 좁혀 private Worker 장기
  직렬화를 제거
- same-conversation follow-up child `slots-followup-phase4fo-1cdf1df7c0`은 prompt가 실제 같은 URL에
  제출되고 UI 답변이 완료되어 F1~F3 CLOSED, 새 material finding·사용자 결정 없음으로 회수했으나,
  wrapper commit probe timeout 때문에 stock session status는 error로 남음; 이 delivery 상태를 설계
  근거로 과장하지 않고 clean authoritative follow-up readback을 한 번 더 요구
- second same-conversation follow-up child `slots-followup-phase4fo-a3a9f3b480`도 같은 URL에 실제
  제출·완료되어 F1~F3 CLOSED, 새 material finding·사용자 결정·ceremony 회귀 없음 재확인; 같은
  commit probe timeout으로 stock status는 error이나 completed UI answer를 harvest함
- Oracle session-operation status가 아니라 Phase 1~3 계약과 current source/test에 correction을
  독립 재대조해 Phase 4 `DESIGN_CONVERGED` 판정
- Phase 5 시작 전 Phase 1~4 계약과 plan checkpoint 전체 재대조
- current Verification Lead의 preflight, sealed draft, AC/flow mapping, PROCESS runner,
  runner-owned artifact, drift/contradiction precedence, result aggregation source·test 조사
- `PHASE-5-VERIFICATION-EXECUTION-CONTRACT.md` 초기 초안 작성
- fresh Verifier가 모든 AC observation을 먼저 고정하고 Evidence Runner만 exact Candidate의 direct
  evidence를 얻는 단일 검증 실행 결정을 선정
- current 12-command/actor/capability/plan/flow/step/ledger와 four-status ceremony를 Phase 2의
  `verify(candidate)` 및 three-result semantics 뒤로 축소
- 2026-08-04 `baseline-capsule/run_tests.py`, `implementation-lead/run_tests.py`,
  `verification-lead/run_tests.py`를 다시 실행해 모두 통과 확인
- Phase 5 DevSpace Oracle initial `slots-context-phase5in-b767c5fbf2` 완료
- initial F1 ambiguous effect fact 보존, F2 started subattempt completeness, F3 fresh readable namespace를
  source/test에 대조해 최소 반영
- same-conversation follow-up 1 `slots-followup-phase5fo-85fcd5a93e`의 F1 lifetime과 F2 heterogeneous
  request 지적을 재반영
- same-conversation follow-up 2 `slots-followup-phase5fo-485d0a30a4`에서 F1/F2/F3 CLOSED,
  새 material finding·사용자 결정·ceremony 회귀 없음 확인
- Oracle 선언이 아니라 Phase 1~4와 current source/test에 correction을 독립 재대조해 Phase 5
  `DESIGN_CONVERGED` 판정
- Phase 6 시작 전 Phase 1~5 계약과 plan checkpoint 전체 재대조
- current authorization ref, ACTION/READBACK/CLEANUP, correlation, retained target, ambiguous replay와
  관련 source/test 조사
- `PHASE-6-DANGEROUS-EFFECT-CONTRACT.md` 초기 초안 작성
- generic authorization/replay command 대신 internal fixed Effect Observation Adapter가 actual authority,
  non-reexecution, authoritative readback과 cleanup/final disposition을 소유하는 단일 결정을 선정
- 2026-08-04 Phase 6 baseline으로 `baseline-capsule/run_tests.py`,
  `implementation-lead/run_tests.py`, `verification-lead/run_tests.py`를 다시 실행해 모두 통과 확인
- Phase 6 DevSpace Oracle initial `slots-context-phase6in-338da18bbd` 완료
- initial F1 completed effect safety/readback-only, F2 authenticated read 과분류, F3 non-self-grant
  provenance를 source/test에 대조해 최소 반영
- same-conversation follow-up `slots-followup-phase6fo-3f6fe9cd52`에서 F1/F2/F3 CLOSED,
  새 material finding·사용자 결정·ceremony 회귀 없음 확인
- Oracle 선언이 아니라 Phase 1~5와 current source/test에 correction을 재대조해 Phase 6
  `DESIGN_CONVERGED` 판정
- Phase 7 시작 전 Phase 1~6 계약과 plan checkpoint 전체 재대조
- current baseline 3개 runner, 254개 test surface와 대표 concurrency/recovery/effect test 조사
- `PHASE-7-INTEGRATION-RUNTIME-VERIFICATION-CONTRACT.md` 초기 초안 작성
- 새 public Interface를 주 test surface로 하고 Source Adoption/Effect Observation만 physical Adapter
  conformance를 요구하며 legacy call sentinel로 새 경로 독립성을 증명하는 단일 결정을 선정
- 2026-08-04 Phase 7 baseline으로 `baseline-capsule/run_tests.py`,
  `implementation-lead/run_tests.py`, `verification-lead/run_tests.py`를 다시 실행해 모두 통과 확인
- 2026-08-04 현재 설계 산출물 28개를 전용 branch commit `3e10c81`로 보존
- 구현 후보 결과의 exact planning/source/AC 결속과 final verdict 비포함을 runtime assertion으로 고정
- 검증 성공·실패 결과의 exact candidate 결속과 criterion evidence 결속을 runtime assertion으로 고정
- evidence 부족은 `INCOMPLETE`, 충분한 exact contradiction은 `VERIFICATION_FAILED`라는 결과 의미를
  runtime assertion으로 고정
- 변경한 목적 보존 테스트 4개를 직접 실행해 모두 통과 확인
Oracle session: Phase 1 구현에는 새 Oracle session을 사용하지 않음; Phase 1 설계 finding F1~F3은 닫힘
열린 finding: 없음 — Phase 1 F1/F2/F3 CLOSED
사용자 결정 필요: 없음
현재 blocker: 없음
바로 다음 행동:
1. Phase 2 시작 시 전체 계획과 `PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md`를 순서대로 읽는다.
2. Phase 2 Interface 구현 전에는 Phase 3 이후 계약을 구현 근거로 사용하지 않는다.
금지: Phase 2 Interface 선행 구현, 제품 source 변경, legacy 제거
```

> [!IMPORTANT]
> **이 작업을 하는 이유**
>
> 구현리드와 검증리드를 없애려는 것이 아니다. 두 리드의 핵심 가치인 정확한 구현,
> 사용자 변경 보존, 독립 검증, source·AC·evidence 결속은 그대로 두고, 실제 보장을
> 제공하지 않으면서 매 실행마다 토큰·시간·실패 가능성을 소비하는 capability, claim,
> authorization, audit, replay 의식을 제거하려는 것이다.
>
> 지금 큰 비용을 한 번 들이는 이유는 본질과 의식을 먼저 분리하고 본질이 사라지지 않는
> 실행 가능한 증명 장치를 만든 뒤, 앞으로 모든 구현·검증 실행의 Interface와 운영 비용을
> 지속적으로 낮추기 위해서다. 설계 합의는 최종 목적이 아니라 안전한 단순화를 위한 선행
> 투자다. 목적 보존의 실제 구현과 검증, 구 메커니즘 제거까지 이어지지 않으면 이 작업의
> 본래 취지는 달성된 것이 아니다.
>
> **가장 중요한 규칙:** Oracle과 적대적으로 토의할 때 주 설계자는 위 작업 이유를 절대
> 방어한다. 정확성·안전성 지적은 근거를 확인해 수용하되, 합의를 얻기 위해 핵심 가치를
> 약화하거나 근거 없는 새 복잡성 또는 불필요한 구 메커니즘을 보존해서는 안 된다. 취지를
> 양보해 얻은 `CONVERGED`는 실패다.

이 작업의 목적은 모든 crash·corruption·공격자·미래 버전 조합을 문서에서 봉쇄하거나,
Oracle의 Critical/High를 0으로 만들거나, 구현리드·검증리드를 새 workflow engine·보안
protocol·감사 체계로 바꾸는 것이 아니다. 실제 사용자 가치에 필요한 보장을 더 작은
Interface와 더 싼 정상 경로로 제공하고, 그 보장을 실행 evidence로 확인한 뒤 구 의식을
삭제하는 것이 목적이다.

## Oracle 적대 검토에서 취지를 방어하는 강제 규칙

Oracle은 설계 authority가 아니라 공격 검토자다. Oracle의 severity와 `CONVERGED` 선언은
그 자체로 근거가 아니다. 주 설계자는 Oracle 의견을 곧바로 문서에 반영하지 않고, **각
finding을 수용하기 전에 그 의견을 기각할 수 있는 가장 강한 반론부터 작성한다.** 여기서
공격한다는 것은 무조건 반대한다는 뜻이 아니라, 새 복잡성을 제안한 쪽에 입증 책임을 두고
사용자 취지보다 reviewer의 불안을 우선하지 않는다는 뜻이다.

### 모든 initial prompt와 follow-up에 넣을 취지 방어문

아래 내용은 단계별 Oracle prompt에서 생략하거나 의미를 약화하지 않는다.

```text
[취지 방어 — 생략 금지]
이 작업의 목적은 구현리드·검증리드의 정확한 구현, 사용자 변경 보존, 독립 검증,
source·AC·evidence 결속을 보존하면서 capability·claim·authorization·audit·replay
의식과 정상 실행 비용을 제거하는 것이다. C/H=0, 문서의 완전무결성, Oracle과의
합의 자체는 목적이 아니다.

너는 설계 authority가 아니라 적대적 reviewer다. 현재 설계의 목적 손실과 실제 실패
경로를 공격하되, 네가 제안하는 correction 역시 과설계·범위 확장·가상 위협 과적합·
구 메커니즘의 이름 바꾼 재도입인지 스스로 공격하라. 더 작은 correction이 있으면 그것을
우선하라. 현재 단계가 소유하지 않는 Implementation 세부를 현재 Interface 계약으로
끌어올리지 마라.

finding을 쓰기 전에 먼저 다음을 재진술하라.
1. 이 작업을 애초에 하는 이유
2. 반드시 보존할 사용자 가치
3. 제거하려는 비용과 의식
4. 이번 단계가 결정할 단 하나의 질문
5. 이번 단계의 명시적 범위 밖

각 finding에는 반드시 다음을 적어라.
- 위 사용자 가치 중 정확히 무엇이 깨지는가
- source·test·runtime 사실 또는 이미 승인된 불변 조건 중 무엇이 근거인가
- 왜 이 finding을 현재 단계에서 닫아야 하는가
- 메커니즘을 추가하지 않거나 더 작게 고치는 대안은 무엇인가
- 제안이 caller Interface, 정상 경로, durable state, 실패 상태를 얼마나 늘리는가
- 새 복잡성이 대신 삭제하거나 한곳에 숨기는 기존 복잡성은 무엇인가

근거 없는 가능성, 아직 존재하지 않는 consumer, 모든 corruption을 막아야 한다는 요구,
후속 단계의 fault injection 세부, reviewer를 만족시키기 위한 식별자·상태·protocol 추가는
Critical/High finding으로 취급하지 마라. 실제 위험이면 질문이나 후속 단계 검증 항목으로
분류하라. 목적을 약화하거나 복잡성만 순증가시키는 correction으로는 수렴을 선언하지 마라.

[Oracle 자기참조·재위임 금지]
너는 지정된 local source·test·runtime evidence를 읽는 reviewer다. `oracle` 또는
`oracle-browser-slots`를 실행하거나 Oracle session·slot·browser·metadata·transcript를
조회·대기·관리하지 마라. 자기 자신·다른 Oracle·다른 모델·agent에게 검토를 재위임하지 마라.
그런 활동의 session 상태·모델 상태·출력·주장을 finding 근거로 쓰지 마라. review에 필요한
근거가 지정 경로에 없으면 이를 missing evidence로 적고, 운영 도구를 호출해 보완하지 마라.
```

### finding 수용 기준

주 설계자는 Oracle 답변을 받은 뒤 finding마다 아래 기록을 먼저 만든다.

```text
ORACLE_CLAIM
STRONGEST_COUNTERARGUMENT
PURPOSE_INVARIANT_AT_RISK
CONCRETE_EVIDENCE
CURRENT_PHASE_OWNERSHIP
SMALLEST_CORRECTION
COMPLEXITY_DELTA
DISPOSITION
```

`ACCEPT` 또는 `ACCEPT_WITH_BOUNDARY`는 다음 조건을 모두 만족할 때만 가능하다.

- 깨지는 사용자 가치나 승인된 불변 조건을 정확히 가리킨다.
- source·test·runtime 사실 또는 재현 가능한 실패 경로가 있다.
- 지금 단계에서 결정하지 않으면 현재 단계의 Interface가 실제로 잘못된다.
- 더 작은 correction이나 후속 단계 검증으로는 닫을 수 없다.
- 추가되는 복잡성이 기존에 삭제하거나 Module 안에 숨기는 복잡성보다 정당하다.

하나라도 충족하지 않으면 자동 수용하지 않고 다음 중 하나로 분류한다.

```text
DEFER_TO_PHASE_<N>
DOWNGRADE_TO_IMPLEMENTATION_CHECK
REJECT_AS_UNSUPPORTED
REJECT_AS_SCOPE_EXPANSION
REJECT_AS_MECHANISM_PRESERVATION
USER_DECISION_REQUIRED
```

### 과설계·과적합 판별

새 메커니즘을 수용하려면 최소한 다음 순증가를 적는다.

- caller가 새로 알아야 할 개념과 호출 단계
- 새 durable state·식별자·protocol
- 정상 경로의 추가 I/O·coordination·토큰 비용
- 새로 생기는 실패·복구 상태
- 그 대가로 삭제되거나 한 Module 안에 숨는 기존 복잡성

구체적 consumer나 관찰된 실패 없이 미래의 다중 process·다중 version·악의적 내부자·임의
corruption을 가정하거나, 문서만으로 완전한 증명을 만들거나, 제거 대상과 같은 역할을 하는
새 이름의 ceremony를 추가하면 원칙적으로 거부한다. 단, 이미 확인된 데이터 손실·사용자 변경
훼손·독립 검증 붕괴·복구 불능을 이 규칙으로 축소해서는 안 된다.

### follow-up 라운드 통제

- 같은 단계의 follow-up은 승인된 목적과 불변 조건에서 나온 finding을 닫는 데만 쓴다.
- 새 threat model, 새 consumer 또는 새 운영 범위를 조용히 추가하지 않는다.
- 후속 단계가 소유할 Implementation·fault injection은 해당 단계로 넘기고 현재 설계의 blocker로
  만들지 않는다.
- 라운드 종료 조건은 C/H=0이 아니라 현재 단계의 단일 결정이 충분한 근거로 닫히고, 남은 finding이
  거부·위임·사용자 결정 필요로 정직하게 분류된 상태다.
- 문서와 Interface는 계속 커지는데 제거되는 메커니즘이 없거나, Oracle finding을 한 건도 반박하지
  못했거나, 합의한 threat model 밖의 지적이 등장하면 다음 follow-up 전에 취지 감사를 강제한다.

취지 감사에서는 `이 변경이 없으면 어떤 실제 사용자 가치가 깨지는가?`, `왜 지금 단계인가?`,
`더 작은 방법은 없는가?`, `무엇이 삭제되는가?`에 답하지 못하는 변경을 되돌린다.

## 현재 구체화 작업 방식

1. 전체 개편을 한 번에 설계하지 않고 한 번에 한 단계만 설계한다.
2. 전용 Git worktree와 branch에서 작업하며 원본 `main`은 건드리지 않는다.
3. 각 단계는 먼저 작은 Interface, 숨길 Implementation, 목적 불변 조건과 명시적 범위 밖을 정한다.
4. 새로운 메커니즘은 구체적인 위협·실패 경로·실제 소비자가 확인될 때만 도입한다.
5. Oracle Browser는 DevSpace 모드로 사용한다. 첨부 대신 worktree 문서와 필요한 소스의 절대
   경로를 제공하고, 최상단 취지와 이전에 확정된 사용자 결정을 직접 읽게 한다.
6. 재설계하는 1단계는 과거 Oracle conversation을 재사용하지 않고 새 conversation에서 시작한다.
   2~8단계도 단계마다 새로운 Oracle session/conversation에서 공격 검토를 시작한다.
7. 한 단계의 수정안 재공격은 그 단계의 같은 conversation에서 follow-up으로 이어간다. 다음 단계로
   넘어갈 때는 이전 conversation을 재사용하지 않는다.
8. Oracle에는 동의를 구하지 않고 목적 손실, 복구 불능, 자기증명 테스트, 구 메커니즘 재유입과
   근거 없는 새 복잡성을 공격하게 하며, 위 취지 방어문과 출력 요구를 매번 포함한다.
9. 주 설계자는 Oracle 결론을 자동 수용하지 않는다. 먼저 가장 강한 반론을 작성하고 로컬
   source·test·runtime 사실과 사용자 취지에 대조해 다음 중 하나로 판정하고 이유를 남긴다.

   ```text
   ACCEPT
   ACCEPT_WITH_BOUNDARY
   DEFER_TO_PHASE_<N>
   DOWNGRADE_TO_IMPLEMENTATION_CHECK
   REJECT_AS_UNSUPPORTED
   REJECT_AS_SCOPE_EXPANSION
   REJECT_AS_MECHANISM_PRESERVATION
   USER_DECISION_REQUIRED
   ```

10. 열린 Critical/High 숫자를 줄이는 것이 목표가 아니다. 해당 지적이 이 단계에서 닫아야 할 실제
    목적 결함인지 먼저 판정하며, 후속 단계의 Implementation 세부를 앞 단계 계약으로 끌어오지 않는다.
11. 단계 상태를 다음처럼 구분한다.

    ```text
    NOT_DESIGNED
    -> DESIGN_DRAFT
    -> DESIGN_CONVERGED
    -> IMPLEMENTED
    -> RUNTIME_VERIFIED
    -> LEGACY_MECHANISM_REMOVED
    ```

## 0. 리셋 상태

- 이전 Phase 1~3 상세 설계와 Oracle 수렴 판정은 폐기했다.
- 이전 문서의 Interface, 상태 모델, schema, lock, permit, migration, recovery protocol과 테스트
  매트릭스는 어떤 후속 설계의 authority도 아니다.
- 모든 단계는 `NOT_DESIGNED`에서 다시 시작한다.
- 제품 코드는 아직 변경하지 않았다.
- 과거 Oracle transcript는 실행 이력일 뿐 설계 근거로 자동 재사용하지 않는다.

## 1. 사용자 목적

- Implementation Lead는 정확한 요구를 구현하고 사용자 변경을 보존한다.
- Verification Lead는 구현과 분리된 fresh 검증을 수행한다.
- 성공 결과는 정확한 planning, source, Acceptance Criteria와 evidence에 결속된다.
- 호출자가 알아야 하는 Interface와 정상 실행 비용을 크게 줄인다.
- 실제 보장을 제공하지 않는 권한·인증·감사·replay 의식을 제거한다.
- 단순화 때문에 정확성, 복구 가능성 또는 독립 검증을 잃지 않는다.

## 2. 재설계 원칙

- Module은 작은 Interface 뒤에 복잡한 Implementation을 숨긴다.
- caller와 test는 같은 Seam을 사용한다.
- 내부 구현 선택을 목적 계약으로 승격하지 않는다.
- 현재 코드에 있다는 이유만으로 메커니즘을 보존하지 않는다.
- 가상의 위협과 모든 가능한 fault를 문서 단계에서 봉쇄하려 하지 않는다.
- 단계별 결정은 그 단계의 소비자가 반드시 알아야 하는 사실로 제한한다.
- 상세 Implementation과 fault injection은 해당 구현 단계와 runtime 검증 단계에서 닫는다.
- 제거 대상과 이름만 다른 새 ceremony를 만들지 않는다.

## 3. 8단계 뼈대

| 단계 | 상태 | 설계 질문 |
| --- | --- | --- |
| 1. 목적 보존 계약 | `DESIGN_CONVERGED` | 구현·검증의 어떤 결과를 반드시 보존해야 하며, 최소한 어떤 외부 관찰로 증명할 것인가? |
| 2. 외부 Interface와 복구 의미 | `DESIGN_CONVERGED` | 정상 caller가 알아야 할 최소 호출과 결과는 무엇이며, 재시작 후 어떤 의미만 보장할 것인가? |
| 3. durable workflow state와 동시성 | `DESIGN_CONVERGED` | 원자 publication·lineage·단일 활성 전이를 어떤 깊은 Module이 숨길 것인가? |
| 4. Implementation 실행 | `DESIGN_CONVERGED` | 선택된 Worker 결과와 사용자 변경을 보존하면서 candidate를 어떻게 만들고 채택할 것인가? |
| 5. Verification 실행 | `DESIGN_CONVERGED` | source를 수정하지 않고 fresh plan과 runner-owned evidence로 어떻게 독립 판정할 것인가? |
| 6. 위험한 외부효과 | `DESIGN_CONVERGED` | 실제 동의·비재실행·readback이 필요한 효과만 어떤 고정 Seam으로 분리할 것인가? |
| 7. 통합·runtime 검증 | `DESIGN_CONVERGED` | 대표 flow, restart, failure와 remediation에서 목적 보존을 어떻게 실행 증명할 것인가? |
| 8. 구 메커니즘 제거 | `DESIGN_CONVERGED` | 대체 증거가 통과한 뒤 어떤 구 경로·명령·schema·protocol을 안전하게 삭제할 것인가? |

## 4. 단계별 설계 템플릿

각 단계는 아래 항목만 채운다. 후속 단계의 Implementation을 미리 설계하지 않는다.

```text
상태
목적과 이번 단계의 단일 결정
보존해야 할 사용자 가치
작은 Interface
Module이 숨길 Implementation
실제 Seam과 필요한 Adapter
허용한 실패·복구 의미
근거가 있는 최소 시나리오
명시적 범위 밖
Oracle finding별 반론·근거·최소 correction·복잡성 delta·판정 기록
완료 판단
```

완료 판단은 다음 질문에 모두 답해야 한다.

- Interface가 Implementation보다 작고 caller에게 leverage를 주는가?
- 이 단계가 없어지면 복잡성이 여러 caller로 다시 퍼지는가?
- 다음 단계의 세부를 현재 Interface로 노출하지 않았는가?
- 새 복잡성마다 실제 위협·실패 경로·소비자가 있는가?
- Oracle 지적을 거부해야 할 때 실제로 거부했는가?
- 수용한 Oracle 지적마다 더 작은 대안을 먼저 검토했는가?
- 새 Interface·state·protocol보다 삭제하거나 숨긴 복잡성이 분명한가?
- 최초 사용자 목적보다 약해지거나 더 비싸지지 않았는가?

## 5. Phase 2 시작 및 수렴 기록

이 절은 Phase 2를 시작할 때 사용한 진입 근거와 최종 수렴 상태를 기록한다. normative 결과
계약은 `PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md`다.

### Phase 1에서 그대로 상속할 불변 조건

- 구현 결과는 final verdict가 아니라, 알려진 due-now 구현·통합 미완료가 없는 검증 대기
  candidate를 뜻한다.
- candidate와 독립 검증 결과는 같은 exact planning/AC와 실제 검토 source에 결속된다.
- 독립 검증은 모든 AC를 빠짐없이 다루고, 각 결론적 판정에 planning이 요구한 관찰 수준의
  직접 source/evidence를 사용한다.
- 사용자 기존·동시 변경을 구현자 변경으로 허위 귀속하거나 조용히 삭제하지 않는다.
- evidence 부족·identity 불일치·판독 불능은 성공도 AC 불충족도 아니며 미확정이다.
- 검증 중 source를 수정하지 않는다. 수정이 필요하면 새 candidate와 새 독립 검증으로 간다.

### 현재 외부 표면 기준선

- 구현 결과 command는 `implementation_result.py publish --request ...` 하나이며,
  `implementation-handoff-v1`을 반환한다. 전역 workflow guard/store와 Capsule 경로는 caller가
  알아야 한다.
- 검증 command는 `start-invocation`, `issue-authorization`, `open-verification`, `seal-run`,
  `execute-step`, `declare-contradiction`, `publish-result`, `read-run`, `read-artifact`,
  `preview-process-step`, `replay-authorization-scope`, `open-remediation`의 12개다. capability,
  claim, budget, run/flow/step ref와 replay scope가 정상 caller 표면에 노출된다.
- 현재 공개 결과는 `implementation-handoff-v1`과 `verification-result-v1`로 분리되어 있다.
  구현 handoff는 planning/source/criterion accounting을, 검증 결과는 같은 handoff와 source,
  criterion별 판정과 reason을 공개한다.
- restart/recovery는 현재 immutable graph, unique tip, exclusive claim, reservation/closure budget,
  sealed run, per-step lock, append-only ledger, replay authorization과 remediation continuation에
  걸쳐 분산돼 있다. Phase 2는 caller가 알아야 할 최소 의미만 정하고, durable state·원자성·
  동시성은 Phase 3, 실행·evidence 세부는 Phase 4~6에 남겨야 한다.

### Phase 2 시작 시 반드시 다시 읽을 근거

1. 이 문서의 목적·강제 규칙·실행 체크포인트와
   `PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md` 전체
2. `implementation-lead/SKILL.md`의 Invocation contract, State model, Handoff publication,
   Failure routing, Terminal return과 `references/implementation-handoff-v1.md`
3. `verification-lead/SKILL.md`의 Required input, Callable tool, Owner-store workflow, Opening,
   Cardinality/recovery, Identity drift, Result publication, Cross-run replay, Terminal return
4. 두 CLI의 parser/help와 해당 interface test·representative pilot
5. `baseline-capsule/PROTOCOL.md`, `matt/skills/to-tickets/SKILL.md`, `README.md`의 실제 consumer 계약

### Phase 2의 단일 설계 질문과 진입 순서

단일 질문은 **정상 caller가 candidate 제출·독립 검증·결과 확인을 위해 알아야 할 최소 호출과
결과는 무엇이며, 중단 또는 재시작 뒤에는 어떤 결과 의미까지만 정직하게 보장할 것인가**다.

시작 뒤에는 다음 순서만 따른다.

1. 기존 caller가 조립하는 개념·호출·ordering/error/restart 지식을 표로 만든다.
2. 삭제하면 그 복잡성이 caller로 다시 퍼지는 한 개의 깊은 Module seam 후보를 정한다.
3. 정상 완료, 중단 뒤 결과 확인, identity/planning/evidence 불일치의 최소 caller 시나리오로
   Interface와 복구 의미를 공격한다.
4. digest·schema·store·lock·lease·transaction·ledger·runner·replay 형식은 Interface에 꼭 필요한
   구체적 consumer 근거가 없는 한 숨기거나 소유 Phase로 위임한다.
5. 새 Phase 2 Oracle conversation에서 공격 검토하고, 모든 finding을 강제 판정 형식으로 닫는다.

### 시작 가능 판정

- Phase 1: `DESIGN_CONVERGED`, 열린 finding 없음, 사용자 결정 없음
- 현재 source/runtime baseline: 세 필수 test runner 모두 통과
- worktree: 전용 branch가 맞고 제품 코드 변경 없음; 두 설계 문서만 untracked
- Phase 2 blocker: 없음
- Phase 2 상태: `DESIGN_CONVERGED` — DevSpace Oracle initial과 두 same-session follow-up의
  finding을 모두 판정하고 source 대조 완료

## 6. 전체 상태

```text
Phase 1  IMPLEMENTED
Phase 2  DESIGN_CONVERGED
Phase 3  DESIGN_CONVERGED
Phase 4  DESIGN_CONVERGED
Phase 5  DESIGN_CONVERGED
Phase 6  DESIGN_CONVERGED
Phase 7  DESIGN_CONVERGED
Phase 8  DESIGN_CONVERGED

Product implementation       NOT_STARTED
Runtime verification         NOT_STARTED
Legacy mechanism removal     NOT_STARTED
```

## 7. 폐기한 자료

다음 항목은 이 문서에서 의도적으로 제거했으며 다시 도입하려면 현재 단계의 근거로 처음부터
정당화해야 한다.

- 이전 Phase 1~3 상세 설계
- 이전 목적 계약 Interface와 대규모 scenario/crash matrix
- 이전 recovery state와 response protocol
- 이전 Workflow Store schema·lock·marker·migration 설계
- 이전 Effect permit/replay 설계
- 이전 Oracle Round 1~12 판정과 `CONVERGED` 선언
