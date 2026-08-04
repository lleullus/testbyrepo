# Phase 5 Oracle follow-up 2 prompt

같은 대화에서 아래 문서를 DevSpace MCP plugin으로 다시 읽고, 파일을 수정하지 말고 최종 재공격만
수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-5-VERIFICATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
```

follow-up 1의 두 잔여 지적을 다음처럼 최소 수정했다.

1. exact Candidate의 unresolved observation item은 Phase 6 safety gate가 authoritative하게
   `RESOLVED | SAFE`라고 판정할 때까지 이후 모든 same-Candidate verification에 계속 적용된다. 중간
   `UNDETERMINED` result가 지우지 않는다. history scan 또는 carry-forward representation은 숨겼다.
2. 각 subattempt는 observation plan에서 **그 subattempt에 pre-fixed된 request**에 결속된다. 동일-request
   retry/poll만 같은 binding을 공유하고, action/readback은 서로 다른 pre-fixed binding을 유지한다.

다음만 답하라.

- F1과 F2를 `CLOSED | STILL_OPEN | OVERCORRECTED`로 판정하고 구체 line/state sequence를 근거로 써라.
- 이미 CLOSED였던 F3나 initial 범위를 근거 없이 다시 열지 마라. 새 material finding은 이 correction이
  직접 만든 regression이거나 앞선 답변에서 놓친 구체 source/test failure path일 때만 제시하라.
- public Interface, 정상 경로, durable state, failure state 또는 제거 대상 ceremony가 순증가했는지
  명시하라.
- Phase 6 mechanism과 Phase 7 fault injection 세부는 현재 blocker로 끌어오지 마라.
- 사용자 결정이 필요한 실제 tradeoff가 있는지 분리하라.
- F1/F2가 닫혔고 새 material finding·사용자 결정·ceremony 회귀가 없으면 그 사실을 명시하라.

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
