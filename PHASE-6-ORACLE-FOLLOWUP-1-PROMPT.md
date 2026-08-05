# Phase 6 Oracle follow-up 1 prompt

같은 대화에서 아래 두 문서를 DevSpace MCP plugin으로 다시 읽어라. 파일을 수정하지 말고 설계 review만
수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-6-DANGEROUS-EFFECT-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
```

initial F1~F3를 source/test와 strongest counterargument에 대조해 모두 `ACCEPT_WITH_BOUNDARY`로 최소
반영했다.

1. F1: fixed effect observation은 action-bearing 또는 readback-only일 수 있다. implementation effect의
   complete bundle에서 fixed Adapter/canonical target/action occurrence/final disposition/resolution만 담은
   nonsemantic safety projection을 Candidate 뒤에도 적용한다. 같은 occurrence의 verification action을
   억제하고 fresh readback만 새 evidence로 얻는다. 별도 occurrence authority가 있을 때만 새 action이다.
2. F2: credential/user data/protected target 사용 자체와 routine request accounting은 dangerous effect
   조건에서 제외했다. authenticated pure read는 opaque credential/current read authority/privacy/
   redaction/bounded execution을 만족하는 fixed read-only Adapter observation이다. durable mutation,
   externally visible consequence, duplicate consequence 또는 cleanup 필요가 있을 때만 effect lifecycle이다.
3. F3: granting authority는 Candidate/private workspace/Verifier/effect가 쓸 수 없는 authoritative
   namespace에서만 온다. Candidate content는 권한을 좁히거나 금지할 수 있지만 새 effect grant나 소비된
   occurrence를 만들 수 없다. caller token·generic policy engine은 추가하지 않았다.

다음만 답하라.

- initial F1~F3를 `CLOSED | STILL_OPEN | OVERCORRECTED`로 판정하고 concrete line/state sequence를 써라.
- correction이 caller Interface, 정상 read/effect 경로, durable state, failure state를 불필요하게 늘리거나
  authorization/replay/ledger ceremony를 이름만 바꿔 재도입했는지 공격하라.
- safety projection이 implementation semantic evidence를 fresh Verifier에 유출하거나, readback-only가
  planning이 요구한 새 occurrence를 부당하게 대체하는 경로가 있는지 확인하라.
- non-self-grant provenance가 Candidate 안의 deny/restriction과 external grant의 교집합을 유지하는지,
  반대로 repository authority를 전부 무시하게 만드는 과수정인지 확인하라.
- 새 material purpose-loss finding은 initial에서 놓친 이유와 지정 source/test의 구체 근거가 있을 때만
  제시하라. Phase 7 fault injection이나 product별 Adapter 구현은 blocker로 끌어오지 마라.
- 사용자 결정이 필요한 실제 tradeoff가 있는지 분리하라.
- 세 finding이 닫혔고 새 material finding·사용자 결정·ceremony 회귀가 없으면 그 사실을 명시하라.

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
