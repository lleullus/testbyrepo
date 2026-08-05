# Phase 2 Oracle follow-up 2 prompt

같은 Phase 2 검토를 계속한다. DevSpace MCP plugin으로 아래 최신 파일을 다시 직접 읽고 파일을
수정하지 마라.

- `/home/user01/project/iis-skills-simplify-leads/PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/SKILL.md`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/SKILL.md`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/tools/verification-run/verification_run.py`

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
근거가 지정 파일에 없으면 이를 missing evidence로 적고, 운영 도구를 호출해 보완하지 마라.

다음을 재공격하라.

1. valid historical result와 live currentness를 분리한 correction이 follow-up F1을 닫았는가.
2. VerificationResult에서 exact Candidate를 재검증 입력으로 복구한다는 correction이 F2를 닫았는가.
3. ImplementationStopped의 durable publication을 거부한 F4 판정이 Phase 1과 restart 계약에 비춰
   정당한가. 응답 유실 뒤 NoConclusiveResult와 fail-closed implement 재평가로 충분한지 공격하라.
4. 위 correction이 새 caller 상태·identity protocol·historical-result 오용을 도입했는가.
5. 전체 `implement`, `verify`, `inspect` Interface와 복구 의미에 다른 material 결함이 남았는가.

각 항목에 `CLOSED`, `STILL_OPEN`, `REGRESSED`, F4에는 추가로 `REJECTION_JUSTIFIED` 또는
`REJECTION_UNSAFE`를 판정하라. 새 material finding에는 필수 여섯 항목과 최소 correction 및
단계 위임을 포함하라. 새 finding과 unresolved user decision이 없으면 Phase 2가
`DESIGN_CONVERGED` 가능한지 명시하라.
