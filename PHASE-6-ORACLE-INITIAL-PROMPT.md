# Phase 6 Oracle initial review prompt

아래 절대 경로의 파일을 **DevSpace MCP plugin으로 직접 읽어라.** 파일 첨부를 기다리거나 Oracle
session·slot·browser를 조회하지 마라. 어떤 파일도 수정하지 말고 설계 review만 수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
/home/user01/project/iis-skills-simplify-leads/PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-3-DURABLE-WORK-STATE-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-4-IMPLEMENTATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-5-VERIFICATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-6-DANGEROUS-EFFECT-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/verification-lead/SKILL.md
/home/user01/project/iis-skills-simplify-leads/verification-lead/references/freeze-22-evidence.md
/home/user01/project/iis-skills-simplify-leads/verification-lead/tools/verification-run/verification_run.py
/home/user01/project/iis-skills-simplify-leads/implementation-lead/tools/workflow-store/workflow_store.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/verification-run/test_verification_run.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/pilot/test_process_verification_pilots.py
```

## 정확한 review 질문

Phase 6의 단 하나의 질문은 다음이다.

> 실제 동의·비재실행·authoritative readback이 필요한 effect만 어떤 고정 Seam으로 분리할 것인가?

초안은 caller의 `implement`, `verify`, `inspect`를 바꾸지 않는다. 내부 Effect Observation Module이
fixed effect observation을 받아 exact current authority가 action·target·final disposition을 실제로
허용할 때만 고정 Adapter를 실행한다. 외부 dispatch 전에 durable `may-have-run`을 남기고, ambiguous
effect를 재호출만으로 반복하지 않으며, action/readback/cleanup의 모든 started subattempt를 하나의
complete evidence bundle로 반환한다. generic authorization ref/scope digest, replay-scope command,
caller-visible ACTION/READBACK/CLEANUP graph와 correlation placeholder는 제거한다.

다음을 우선 공격하라.

1. effect 분류가 safe-local로 잘못 낮아져 외부 write/network/credential operation이 Phase 5 Runner로
   우회하거나, 반대로 ordinary read-only observation까지 과도하게 막는 재현 가능한 경로가 있는지.
2. ready Ticket·verify 호출·Coordinator mint를 동의로 보지 않고 current planning/repository/product/
   target authority가 exact intent·target·consequence·disposition·occurrence를 허용해야 한다는 조건이
   “실제 동의”를 보존하는지. caller approval token을 되살리지 않고 닫아야 할 최소 누락이 있는지.
3. current `issue_authorization`은 Coordinator가 arbitrary scope digest를 발급하고 verifier가 invocation과
   digest 일치만 확인한다. 이를 제거하면서 실제로 잃는 사용자 가치와 단순 ceremony를 구분하라.
4. unresolved effect를 같은 Candidate뿐 아니라 새 Candidate에서도 overlapping target/action consequence에
   적용하는 것이 실제 duplicate effect를 막는 필요한 보장인지, 또는 work-wide history/semantic matching을
   부당하게 도입하는 범위 확장인지.
5. prior ambiguity를 authoritative readback, provider-enforced exact idempotency 또는 pre-fixed unique
   correlation로만 닫고 세부를 Adapter에 숨기는 방식이 unsafe replay를 막는지. 문자열 equality나
   caller assertion이 safety로 승격되는 잔여 경로가 있는지.
6. action 전에 cleanup authority·request·final observation까지 확보하고, action may-have-run 뒤에는
   contradiction/drift가 있어도 containment readback/cleanup만 허용하는 ordering이 맞는지. cleanup이
   오히려 위험하거나 authority가 철회된 경우의 의미가 모순되는지.
7. persistent effect는 authoritative readback을 필수화하되 fixed Adapter의 authoritative terminal receipt만
   예외로 둔 것이 action response를 readback으로 가장하는 우회가 되는지.
8. implementation check도 같은 seam을 사용하되 그 success evidence는 verification에 재사용하지 않고
   unresolved safety fact만 적용하는 구분이 독립 검증과 duplicate-effect 방지를 함께 지키는지.
9. evidence privacy/redaction과 direct observable sufficiency가 충돌할 때 `UNDETERMINED`로 닫는 경계가
   맞는지. secret resolver나 policy engine을 지금 Interface로 끌어올릴 근거가 있는지.
10. current source/test가 입증하는 effect 보장 중 초안이 잘못 삭제했거나, 반대로 user value가 아닌
    mechanism을 이름만 바꿔 되살린 것이 있는지.

findings first, severity 순으로 쓰되 각 finding에 구체 파일·line과 재현 가능한 effect/source-state
sequence를 인용하라. confirmed defect, inference, missing runtime verification을 구분하라. Critical/High가
없더라도 목적 손실·복잡성 회귀가 있으면 적어라. 동의를 위한 `CONVERGED`를 선언하지 말고,
correction이 꼭 필요할 때만 caller Interface를 늘리지 않는 가장 작은 correction을 제안하라.

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
