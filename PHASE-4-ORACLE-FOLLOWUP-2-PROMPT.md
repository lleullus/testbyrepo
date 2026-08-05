# Phase 4 Oracle follow-up 2 prompt

아래 수정된 문서를 DevSpace MCP plugin으로 다시 읽고 최종 semantic closure만 짧게 재공격하라. 파일은
수정하지 마라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-3-DURABLE-WORK-STATE-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-4-IMPLEMENTATION-EXECUTION-CONTRACT.md
```

initial F1 precheck/write race, F2 crash ABA, F3 occupancy/private Worker conflict에 반영된 correction을
source-state sequence로 다시 공격하고 각각 `CLOSED` 또는 `STILL_OPEN`으로 판정하라. 특히 다음을
확인하라.

- conditional mutation은 linearization 시 actual state mismatch면 actual bytes/physical identity를
  잃지 않고 intended bytes를 canonical path에 남기지 않으며, 못 지키는 Adapter는 mutation을 시작하지
  않는다.
- canonical mutation may-have-started 뒤 crash면 exact equality는 resume/attribution authority가 아니고,
  추가 write 없이 safe close 가능한 경우와 fail-closed 유지가 분리된다.
- occupancy는 canonical adoption만 직렬화하고 격리된 private Worker는 같은-work transition 단일성만
  적용받는다.
- final Candidate source retention은 result recoverability lifetime에 결속된다.

새 material finding이나 사용자 결정이 실제로 필요하면 concrete source-state sequence와 가장 작은
correction을 제시하라. 없으면 없다고 명시하라. runtime Adapter/fault-injection 미검증은 설계 defect와
구분하라.

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
