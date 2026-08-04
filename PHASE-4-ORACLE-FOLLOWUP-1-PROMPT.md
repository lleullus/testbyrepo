# Phase 4 Oracle follow-up 1 prompt

같은 DevSpace conversation에서 아래 수정된 파일을 다시 직접 읽어라. 파일을 수정하지 말고 review만
수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-3-DURABLE-WORK-STATE-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-4-IMPLEMENTATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
```

initial F1~F3에 대해 주 설계자는 각각 가장 강한 반론을 먼저 작성한 뒤 다음처럼 판정했다.

1. F1 `ACCEPT_WITH_BOUNDARY`: Source Adoption seam을 expected-state 검사와 mutation이 한 선형화점에
   있고 actual state를 잃지 않는 conditional operation으로 강화했다. CAS/atomic exchange 등 concrete
   primitive와 fault injection은 올리지 않았다.
2. F2 `ACCEPT_WITH_BOUNDARY`: per-path ledger/generation/witness를 추가하지 않았다. canonical mutation
   may-have-started 뒤 crash가 나면 source equality는 resume authority가 아니며 자동 write continuation과
   rollback을 금지했다. current source를 retain할 수 있으면 추가 write 없는 ImplementationStopped/safe
   close, 아니면 active transition/occupancy를 fail-closed 유지한다.
3. F3 `ACCEPT`: Phase 3 occupancy gate를 private Worker dispatch가 아니라 first canonical product
   mutation으로 좁혔다. 같은-work active transition 단일성은 duplicate private Worker를 막고,
   overlapping roots의 adoption만 occupancy로 직렬화한다.

추가로 final Candidate retained source의 lifetime이 complete Candidate/VerificationResult recoverability
lifetime보다 짧을 수 없음을 명시해 Baseline Capsule의 독립 7일 expiry를 그대로 재사용하지 못하게
했다.

다음만 공격하라.

- F1 correction이 precheck/write race에서 actual user state를 정말 보존하는 semantic contract인지,
  아니면 여전히 overwrite 허용 문구가 남았는지.
- F2 correction이 ABA와 duplicate mutation을 막으면서 Phase 3 safe close 의미와 모순되지 않는지.
  새 per-path ledger나 rollback protocol이 실제로 불가피하다는 주장은 concrete failure sequence가
  있을 때만 하라.
- F3 correction이 cross-work canonical mutation loss를 막으면서 private Worker loop를 불필요하게
  직렬화하지 않는지.
- 세 correction이 다른 Phase 1~4 invariant를 깨거나 caller Interface, normal path, durable state를
  구 ceremony 수준으로 다시 키웠는지.
- initial에서 없던 새 material Critical/High 또는 사용자 결정이 실제 source/contract 근거로
  생겼는지.

각 initial finding에 `CLOSED`, `STILL_OPEN`, `REJECTION_JUSTIFIED` 중 하나를 주고, 새 finding은 같은
evidence/complexity 기준을 전부 충족할 때만 별도로 제시하라. C/H=0이나 합의 자체를 목표로 삼지
마라.

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
