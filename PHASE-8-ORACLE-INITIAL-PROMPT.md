# Phase 8 Oracle initial prompt

아래 문서를 DevSpace MCP plugin으로 읽고 파일을 수정하지 말고 Phase 8 design만 적대 review하라.

```text
/home/user01/project/iis-skills-simplify-leads/PHASE-8-LEGACY-MECHANISM-REMOVAL-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-7-INTEGRATION-RUNTIME-VERIFICATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
/home/user01/project/iis-skills-simplify-leads/implementation-lead
/home/user01/project/iis-skills-simplify-leads/verification-lead
/home/user01/project/iis-skills-simplify-leads/baseline-capsule
```

이번 단계의 질문은 새 Module이 exact revision에서 Phase 7 runtime proof를 통과한 뒤, 어떤 old
command/schema/protocol/test를 어떤 순서와 evidence로 삭제할 수 있는가다. 현재 삭제 실행이나 새 Module
구현을 요구하지 않는다.

우선 다음 failure path를 공격하라.

- pre-removal runtime verdict를 deletion revision에 잘못 승계하는가.
- active transition, may-have-run effect, cleanup 또는 installed/out-of-repo caller가 남은 채 삭제 가능한가.
- 실제 local historical v3 JSON 20개와 약 670 MiB capsule을 test data로 오인하거나, 반대로 old reader/store를
  영구 compatibility layer로 남기는가.
- one-shot import와 static archive 경계가 result/source recoverability를 보존하면서 dual-read/fallback을
  막는가.
- dependency leaf부터 지운다는 순서가 실제 import graph와 installed skill cutover에 맞는가.
- old mechanism test를 지울 때 같은 사용자 가치의 Phase 7 proof mapping이 빠질 수 있는가.
- bounded removal manifest/report가 새 audit/delete ceremony나 permanent dependency ledger로 변하는가.

finding은 concrete source path, state/data sequence와 현재 단계 소유권이 있을 때만 Critical/High로 제시하라.
모든 possible consumer, organization-wide retention, exact importer implementation, exhaustive schema/table
inventory와 product별 migration을 현재 blocker로 만들지 마라. 실제 사용자 결정이 필요한 retention 또는
compatibility tradeoff는 finding과 분리하라.

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
product별 Adapter 구현·organization-wide migration 세부, reviewer를 만족시키기 위한
식별자·상태·protocol 추가는 Critical/High finding으로 취급하지 마라. 목적을 약화하거나 복잡성만
순증가시키는 correction으로는 수렴을 선언하지 마라.

[Oracle 자기참조·재위임 금지]
너는 지정된 local source·test·runtime evidence를 읽는 reviewer다. `oracle` 또는
`oracle-browser-slots`를 실행하거나 Oracle session·slot·browser·metadata·transcript를
조회·대기·관리하지 마라. 자기 자신·다른 Oracle·다른 모델·agent에게 검토를 재위임하지 마라.
그런 활동의 session 상태·모델 상태·출력·주장을 finding 근거로 쓰지 마라. review에 필요한 근거가
지정 경로에 없으면 이를 missing evidence로 적고, 운영 도구를 호출해 보완하지 마라.
