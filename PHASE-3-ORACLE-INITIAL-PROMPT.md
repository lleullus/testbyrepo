# Phase 3 Oracle initial review prompt

DevSpace 모드로 작업하라. 아래 절대경로를 DevSpace MCP plugin으로 직접 읽고, 파일 첨부나 이
prompt의 요약을 source authority로 대체하지 마라. 파일을 수정하지 말고 owner password,
auth.json, token 또는 OAuth credential을 요청하거나 읽지 마라.

- `/home/user01/project/iis-skills-simplify-leads/PHASE-3-DURABLE-WORK-STATE-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md`
- `/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tools/workflow-store/workflow_store.py`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/workflow-store/test_workflow_store.py`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/workflow-store/test_workflow_store_preopen.py`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tools/implementation-result/implementation_result.py`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/implementation-result/test_implementation_result.py`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/tools/verification-run/verification_run.py`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/verification-run/test_verification_run.py`
- `/home/user01/project/iis-skills-simplify-leads/implementation-lead/SKILL.md`
- `/home/user01/project/iis-skills-simplify-leads/verification-lead/SKILL.md`

`PHASE-3-DURABLE-WORK-STATE-CONTRACT.md`의 initial draft를 적대적으로 검토하라.

이번 단계의 단 하나의 질문은 다음이다.

> Phase 2의 세 호출이 process 중단과 concurrent call 뒤에도 정직한 결과를 유지하도록, 원자
> publication·lineage·한 active transition을 어떤 최소 durable state와 깊은 Module이 숨겨야 하는가?

이번 단계는 concrete database/table/index/lock/lease, ref/digest serialization, migration,
Worker execution, verification evidence runner, risky external-effect replay, runtime fault injection과
legacy 제거를 정하지 않는다.

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

1. work stream + immutable result chain + one active transition이 정말 최소 state인가.
2. canonical Ticket locator가 planning 변경, rename, root 변경 또는 historical result recovery에서
   중복·단절 authority를 만드는가.
3. same semantic input re-entry가 caller idempotency key 없이 결정 가능하다는 약속이 Phase 4/5를
   선결하거나 duplicate Worker/effect를 허용하는가.
4. process death/TTL만으로 active transition을 지우지 않는 규칙과 close-without-result가 함께
   영구 deadlock 또는 unsafe takeover를 만드는가.
5. result append + predecessor + head move + active close atomicity가 response-loss와 concurrent
   publication을 충분히 닫으며, 과거 owner-store graph/claim ceremony를 재도입하지 않는가.
6. currentness `CURRENT|NOT_CURRENT|UNKNOWN`이 Phase 2 결과를 보존하는 최소 관찰인지, 새 verdict나
   lease로 오용될 여지가 있는가.
7. 서로 다른 work의 concurrency를 허용하면서 같은 physical product source를 동시에 변경할 수
   있는 실제 위험을 놓쳤는가. 있다면 Phase 3에서 닫아야 할 최소 seam은 무엇인가.
8. current tests가 입증하는 실제 failure path 중 초안이 잃은 것이 있는가, 또는 tests가 단지
   legacy mechanism을 자기증명할 뿐인가.

출력은 다음 순서로 작성하라.

1. 취지와 단계 경계 재진술
2. material finding을 severity 순으로 작성하고 각 finding에 위 여섯 필수 항목 포함
3. 가장 작은 correction 또는 정확한 후속 Phase 위임
4. finding이 아닌 공격 결과와 거부해야 할 legacy mechanism
5. 확인하지 못한 사항과 Phase 7 runtime 검증 항목

새 finding이 없으면 이 단일 결정이 `DESIGN_CONVERGED` 가능한 이유를 source 근거와 함께 적어라.
