# Phase 7 Oracle follow-up 1 prompt

같은 대화에서 아래 두 문서를 DevSpace MCP plugin으로 다시 읽어라. 파일을 수정하지 말고 설계 review만
수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-7-INTEGRATION-RUNTIME-VERIFICATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
```

initial F1~F5를 strongest counterargument와 source/test에 대조해 모두 `ACCEPT_WITH_BOUNDARY`로 최소
반영했다.

1. production Worker의 실제 namespace에서 private write 성공과 canonical/planning/durable-state write
   실패를 probe한다. production Fresh Verifier/Evidence Runner launcher에서도 prior semantic canary 접근,
   source write와 Runner 밖 evidence 제출을 물리적으로 차단한다. 모델 출력 snapshot은 하지 않는다.
2. effect conformance report를 exact Adapter revision, tested variant/mode·target class, 실제 authority/
   dispatch/readback/cleanup branch와 당시 enabled set에 결속한다. production과 동일 code path가 아니면
   sandbox variant에만 적용하고 enablement/branch 변경 시 해당 Adapter verdict만 보류한다.
3. retired import/call 차단, legacy store absent/unreadable, 필요시 poisoned old result인 negative environment에서
   대표 public harness를 실행한다. 모든 공용 utility symbol audit는 하지 않는다.
4. Candidate/VerificationResult response-loss readback 뒤 verify/fresh verify/remediation implement와
   overlapping-root adoption 같은 다음 합법적 public transition이 정확히 한 번 진행되는지 확인한다.
5. flow 14를 Candidate source A publish -> canonical B drift -> restart -> verify(A)가 retained A를 실제
   input으로 사용 -> historical result와 NOT_CURRENT/UNKNOWN 반환 순서로 명시했다.

다음만 답하라.

- F1~F5를 `CLOSED | STILL_OPEN | OVERCORRECTED`로 판정하고 concrete line/state sequence를 근거로 써라.
- 새 probe/report metadata/negative environment가 caller Interface, 정상 path, product durable state,
  failure state 또는 permanent test ledger를 불필요하게 늘리는지 공격하라.
- production isolation probe가 semantic model grading으로 변하지 않았는지, Adapter scope report가 새
  authorization/audit protocol인지, negative environment가 공용 utility까지 금지하는 과수정인지 확인하라.
- public post-commit liveness가 orphan transition/occupancy를 실제로 구별하고, retained-source sequence가
  historical Candidate와 current work를 혼동하지 않는지 확인하라.
- 새 material finding은 initial에서 놓친 concrete Phase 1~6 failure path가 있을 때만 제시하라. Phase 8
  삭제 구현이나 exhaustive fault matrix를 현재 blocker로 끌어오지 마라.
- 사용자 결정이 필요한 실제 tradeoff가 있는지 분리하라.
- 모든 finding이 닫혔고 새 material finding·사용자 결정·ceremony 회귀가 없으면 명시하라.

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
product별 Adapter 구현·후속 migration 세부, reviewer를 만족시키기 위한 식별자·상태·protocol 추가는
Critical/High finding으로 취급하지 마라. 실제 위험이면 implementation check나 Phase 8 gate로 분류하라.
목적을 약화하거나 복잡성만 순증가시키는 correction으로는 수렴을 선언하지 마라.

[Oracle 자기참조·재위임 금지]
너는 지정된 local source·test·runtime evidence를 읽는 reviewer다. `oracle` 또는
`oracle-browser-slots`를 실행하거나 Oracle session·slot·browser·metadata·transcript를
조회·대기·관리하지 마라. 자기 자신·다른 Oracle·다른 모델·agent에게 검토를 재위임하지 마라.
그런 활동의 session 상태·모델 상태·출력·주장을 finding 근거로 쓰지 마라. review에 필요한 근거가
지정 경로에 없으면 이를 missing evidence로 적고, 운영 도구를 호출해 보완하지 마라.
