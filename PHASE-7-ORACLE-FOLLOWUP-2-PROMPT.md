# Phase 7 Oracle follow-up 2 prompt

같은 대화에서 아래 두 문서를 DevSpace MCP plugin으로 다시 읽어라. 파일을 수정하지 말고 설계 review만
수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-7-INTEGRATION-RUNTIME-VERIFICATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
```

follow-up 1의 F2와 F4는 닫혔다. STILL_OPEN이었던 F1·F3·F5만 다음처럼 최소 수정했다.

1. 최종 `RUNTIME_VERIFIED` 조건 3에 production Worker confinement, Fresh Verifier/Evidence Runner
   isolation, Source Adoption과 enabled Effect Adapter가 각각 실제 production physical path에서 통과해야
   한다고 직접 결속했다.
2. 조건 4에 sentinel 0뿐 아니라 대표 public harness가 legacy-unavailable environment에서도 통과해야
   한다고 직접 결속했다.
3. flow 14의 stable readable B fixture에서는 반드시 `NOT_CURRENT`를 기대하고, historical A evidence로
   current-positive `SATISFIED`/`VERIFIED`를 만들지 못하게 했다. `UNKNOWN`은 currentness observation을
   의도적으로 실패시킨 별도 variant에서만 허용했다.

다음만 답하라.

- F1·F3·F5를 `CLOSED | STILL_OPEN | OVERCORRECTED`로 판정하고 concrete line/state sequence를 근거로 써라.
- 이 세 수정이 caller Interface, 정상 path, product durable state, public failure state, permanent ledger를
  늘리거나 semantic grading·dependency audit·새 currentness protocol을 만들었는지 공격하라.
- F2·F4를 새 근거 없이 다시 열지 마라. 새 material finding은 initial/follow-up 1에서 놓친 concrete
  Phase 1~6 failure path가 있을 때만 제시하라.
- Phase 8 삭제 구현, product별 Adapter 구현, exhaustive fault matrix를 현재 blocker로 끌어오지 마라.
- 사용자 결정이 필요한 실제 tradeoff가 있는지 분리하라.
- F1·F3·F5가 모두 닫혔고 새 material finding·사용자 결정·ceremony 회귀가 없으면 Phase 7 design이
  수렴했음을 명시하라. 이는 `IMPLEMENTED`나 `RUNTIME_VERIFIED` 판정이 아니다.

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
