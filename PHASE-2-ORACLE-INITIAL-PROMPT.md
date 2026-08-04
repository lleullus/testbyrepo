# Phase 2 Oracle initial review prompt

DevSpace 모드로 작업하라. 아래 절대경로를 반드시 DevSpace MCP plugin으로 직접 읽고, 파일
첨부나 대화에 포함된 요약을 source authority로 대체하지 마라. owner password, auth.json,
token 또는 OAuth credential을 요청하거나 읽지 마라.

- `/home/user01/project/iis-skills-simplify-leads/PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/SKILL.md`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/references/implementation-handoff-v1.md`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/SKILL.md`
- `/home/user01/project/iis-skills-simplify-leads/baseline-capsule/PROTOCOL.md`
- `/home/user01/project/iis-skills-simplify-leads/matt/skills/to-tickets/SKILL.md`
- `/home/user01/project/iis-skills-simplify-leads/README.md`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tools/implementation-result/implementation_result.py`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/tools/verification-run/verification_run.py`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/contract/test_skill_contract.py`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/pilot/test_process_verification_pilots.py`

`PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md`를 수정하지 말고 적대적으로 검토하라.
이 repository는 Implementation Lead와 Verification Lead의 현재 복잡한 workflow를 실제 사용자
가치를 잃지 않는 더 작은 Interface 뒤로 숨기기 위한 재설계 worktree다.

이번 단계의 단 하나의 질문은 다음이다.

> 정상 caller가 알아야 할 최소 호출과 결과는 무엇이며, 중단 또는 재시작 뒤 어떤 결과 의미만
> 보장할 것인가?

이번 단계는 final CLI spelling, serialized schema, durable state/concurrency, Worker execution,
verification evidence runner, risky external-effect mechanism, runtime verification와 legacy 제거를
정하지 않는다. 그것들은 Phase 3~8 소유다.

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

특히 다음을 공격하라.

1. `implement(work, worker)`, `verify(candidate)`, `inspect(work)`가 정말 최소인가.
2. 한 Module Interface가 내부 actor 독립성을 흐리거나 caller가 self-certification하게 만드는가.
3. `inspect(work)`와 same-meaning 재호출의 recovery 약속이 work identity 또는 concurrency를
   몰래 가정하거나 Phase 3·6의 mechanism을 선결하는가.
4. `Candidate`, `ImplementationStopped`, `VERIFIED`, `NOT_SATISFIED`, `UNDETERMINED`,
   `NoConclusiveResult`가 Phase 1 의미를 보존하면서 불필요하게 많은 상태를 만들지는 않는가.
5. source/planning drift, 사용자 변경 보존 불확실성, verification 중 mutation, ambiguous effect
   후 restart에서 긍정 결과나 unsafe replay가 가능한가.
6. 현재 확인된 실제 consumer와 source가 요구하지 않는 새 개념이 들어갔는가.

출력은 다음 순서로 작성하라.

1. 취지와 단계 경계 재진술
2. material finding을 severity 순으로 작성. finding마다 위 필수 여섯 항목 포함
3. 각 finding에 가장 작은 correction 제안 또는 후속 Phase 위임
4. finding이 없으면 왜 이 Interface/복구 의미가 Phase 1을 보존하고 caller 표면을 줄이는지 근거
5. 확인하지 못한 사항과 Phase 7 runtime 검증 항목

설계 파일을 수정하지 말라. 위 절대경로를 DevSpace MCP plugin으로 직접 읽은 source와 tests만
근거로 사용하라.
