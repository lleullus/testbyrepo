# Phase 5 Oracle initial review prompt

아래 절대 경로의 파일을 **DevSpace MCP plugin으로 직접 읽어라.** 파일 첨부를 기다리거나 Oracle
session·slot·browser를 조회하지 마라. 어떤 파일도 수정하지 말고 설계 review만 수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
/home/user01/project/iis-skills-simplify-leads/PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-3-DURABLE-WORK-STATE-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-4-IMPLEMENTATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-5-VERIFICATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/verification-lead/SKILL.md
/home/user01/project/iis-skills-simplify-leads/verification-lead/references/freeze-22-evidence.md
/home/user01/project/iis-skills-simplify-leads/verification-lead/tools/verification-run/verification_run.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/verification-run/test_verification_run.py
/home/user01/project/iis-skills-simplify-leads/verification-lead/tests/pilot/test_process_verification_pilots.py
```

## 정확한 review 질문

Phase 5의 단 하나의 질문은 다음이다.

> exact Candidate source를 수정하지 않고, 구현과 분리된 fresh plan과 runner-owned direct evidence로
> 모든 AC를 어떻게 독립 판정할 것인가?

초안은 외부 `verify(candidate)` 호출을 유지하면서, 내부 fresh Verifier가 모든 AC의 observation
level과 fixed observation을 evidence acquisition 전에 계획하게 한다. Evidence Runner만 immutable
Candidate의 source evidence 또는 격리된 실행 evidence를 만들고, Verifier는 그 evidence만으로
`SATISFIED | NOT_SATISFIED | UNDETERMINED`를 판정한다. current actor/capability, caller draft,
run/flow/step command, sealedPlanDigest, attempt/event ledger, `BLOCKED | INCOMPLETE` 이중 public status와
별도 contradiction command는 제거한다.

다음을 우선 공격하라.

1. fresh Verifier에게 implementation check/Worker prose/이전 plan·verdict·evidence를 주지 않는 것만으로
   독립성이 충분한지, 근거 있는 최소 추가 조건이 필요한지.
2. 모든 AC observation을 첫 evidence 전에 한 번 고정하고, shared observation과 AC coverage만 내부에
   숨기는 방식이 post-hoc cherry-picking과 disconnected component success를 실제로 막는지.
3. retained Candidate를 read-only source view로 제공하고 writable scratch가 source namespace와 겹치지
   않게 하는 계약이 “검증 중 source 수정 금지”를 닫는지. writable copy/overlay로 바뀌어 실행 대상이
   Candidate가 아니게 되는 잔여 경로가 있는지.
4. Runner가 fixed request와 complete direct evidence를 소유하고 unsupported conclusive verdict를
   `UNDETERMINED`로 낮추는 방식이 caller-authored outcome, missing evidence=product failure, favorable
   attempt selection을 막는지.
5. generic event/attempt ledger를 없애고 immutable plan, 현재 한 observation의 may-have-run state,
   completed evidence bundle만 남겼을 때 crash/restart, contradiction-before-drift와 response loss가
   정직한 결과를 유지하는지.
6. `BLOCKED`와 `INCOMPLETE`를 Phase 2의 `UNDETERMINED` reason으로 합치고 별도 contradiction command를
   없애도 실제 consumer 행동이나 AC result 의미가 사라지지 않는지.
7. Phase 6 effect replay/readback과 Phase 7 fault injection을 Phase 5 계약으로 끌어오지 않으면서도,
   unsafe effect를 실행하거나 이전 ambiguous effect를 반복하는 허점이 없는지.
8. current source/test가 입증하는 핵심 보장 중 초안이 잘못 삭제한 것이 있는지. freeze-22의 모든
   mechanism을 보존하라는 주장이 아니라, Phase 1~3 사용자 가치에 실제 필요한 항목만 구분하라.

findings first, severity 순으로 쓰되 각 finding에 구체 파일·line과 재현 가능한 evidence/source-state
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
