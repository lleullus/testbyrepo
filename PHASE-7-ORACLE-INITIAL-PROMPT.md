# Phase 7 Oracle initial review prompt

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
/home/user01/project/iis-skills-simplify-leads/PHASE-7-INTEGRATION-RUNTIME-VERIFICATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/baseline-capsule/run_tests.py
/home/user01/project/iis-skills-simplify-leads/implementation-lead/run_tests.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/run_tests.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/references/freeze-22-evidence.md
/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/implementation-transaction/test_implementation_transaction.py
/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/workflow-store/test_workflow_store.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/verification-run/test_verification_run.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/pilot/test_process_verification_pilots.py
```

## 정확한 review 질문

Phase 7의 단 하나의 질문은 다음이다.

> 대표 flow, restart, failure와 remediation에서 Phase 1~6 목적 보존을 어떤 최소 runtime evidence로
> 실행 증명할 것인가?

초안은 새 public `implement/verify/inspect`를 주 test surface로 삼고, public outcome만으로 물리 보장을
구분할 수 없는 Source Adoption과 Effect Observation Adapter에만 conformance harness를 둔다. 정상,
user-change preservation, fresh verification, evidence shortage/contradiction, response loss, concurrency,
critical failpoint, effect authority/non-reexecution/readback/cleanup, remediation flow를 실행한다. 새 path가
legacy CLI/store orchestration을 호출하면 sentinel이 실패한다. deterministic fake만 통과하거나 legacy
test count/Freeze 22만 통과해도 `RUNTIME_VERIFIED`라고 하지 않는다.

다음을 우선 공격하라.

1. public outcome harness와 두 Adapter conformance만으로 Phase 1~6의 실제 물리 보장을 증명할 수 있는지.
   내부 state assertion을 금지해 오히려 crash ordering·fresh namespace·atomicity 결함을 놓치는 경로가
   있는지.
2. production Adapter가 같은 conformance를 통과해야 한다는 조건이 fake-only self-certification을
   막는지. sandbox/non-production target만으로 production transport/authority/readback 의미를 과장하는
   경로와 가장 작은 correction을 구분하라.
3. legacy-call sentinel이 얇은 facade, hidden import, legacy store read, old result conversion과 shadow
   certification을 실제로 막는지. 모든 legacy symbol을 audit해야 한다는 과설계 없이 닫을 수 있는지.
4. 24개 public flow와 9개 fault boundary가 사용자 가치별 대표 증거인지, freeze-22를 다른 checklist로
   다시 만든 과설계인지. 중복 flow를 삭제할 수 있거나 빠진 load-bearing flow가 있는지.
5. dirty source, same-path overwrite race, conditional mutation, canonical-mutation crash/no-resume와 retained
   Candidate lifecycle이 실제 user-change preservation을 입증하는지.
6. fresh Verifier namespace, full-AC plan, runner-owned evidence, disconnected flow, evidence shortage와 direct
   contradiction/drift precedence가 implementation self-certification을 막는지.
7. effect marker/dispatch ordering, no-authority zero dispatch, authenticated pure read, ambiguous effect의
   same/new-Candidate non-reexecution, completed implementation occurrence의 readback-only, cleanup/final
   disposition을 test Adapter와 enabled production Adapter에서 어떻게 과장 없이 증명하는지.
8. `NOT_SATISFIED -> implement -> new Candidate -> fresh full-AC verify`와 authority-delta stop이 remediation
   의미를 충분히 다루는지. legacy Remediation Lead protocol을 test에 되살리는 요구는 하지 마라.
9. 정상 비용 증거를 public command 3개/legacy call 0/effect-state 0으로 잡은 것이 사용자 취지를 실제로
   확인하는지, wall-clock/token/byte threshold가 반드시 필요한 concrete consumer 근거가 있는지.
10. Phase 7 design convergence와 향후 `RUNTIME_VERIFIED`를 명확히 구분했는지. 새 Module이 미구현인데
    현재 baseline 통과를 새 runtime proof로 잘못 읽는 잔여 문구가 있는지.

findings first, severity 순으로 쓰되 각 finding에 구체 파일·line과 재현 가능한 test/source/effect-state
sequence를 인용하라. confirmed defect, inference, missing runtime verification을 구분하라. Critical/High가
없더라도 목적 손실·복잡성 회귀가 있으면 적어라. correction이 꼭 필요할 때만 caller Interface나 새
per-test ledger를 늘리지 않는 가장 작은 correction을 제안하라.

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
