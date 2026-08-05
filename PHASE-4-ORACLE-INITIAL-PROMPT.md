# Phase 4 Oracle initial review prompt

아래 절대 경로의 파일을 **DevSpace MCP plugin으로 직접 읽어라.** 파일 첨부를 기다리거나 Oracle
session·slot·browser를 조회하지 마라. 어떤 파일도 수정하지 말고 설계 review만 수행하라.

```text
/home/user01/project/iis-skills-simplify-leads/IMPLEMENTATION-VERIFICATION-SIMPLIFICATION-PLAN.md
/home/user01/project/iis-skills-simplify-leads/PHASE-1-PURPOSE-PRESERVATION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-2-EXTERNAL-INTERFACE-RECOVERY-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-3-DURABLE-WORK-STATE-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/PHASE-4-IMPLEMENTATION-EXECUTION-CONTRACT.md
/home/user01/project/iis-skills-simplify-leads/implementation-lead/SKILL.md
/home/user01/project/iis-skills-simplify-leads/implementation-lead/references/task-ownership.md
/home/user01/project/iis-skills-simplify-leads/implementation-lead/tools/implementation-transaction/implementation_transaction.py
/home/user01/project/iis-skills-simplify-leads/implementation-lead/tests/implementation-transaction/test_implementation_transaction.py
/home/user01/project/iis-skills-simplify-leads/baseline-capsule/PROTOCOL.md
/home/user01/project/iis-skills-simplify-leads/baseline-capsule/baseline_capsule.py
```

## 정확한 review 질문

Phase 4의 단 하나의 질문은 다음이다.

> 선택된 Worker 결과와 사용자 기존·동시 변경을 보존하면서 exact Candidate를 어떻게 만들고
> canonical source에 채택할 것인가?

초안은 Worker가 canonical source를 직접 바꾸는 현재 방식을 버리고, private candidate workspace에서
Worker를 실행한 뒤 immutable baseline B, private Worker result W, occupancy 뒤 live source L을
대조한다. same-path conflict는 canonical mutation 전에 멈추고, disjoint delta만 adoption plan으로
적용하며, final source를 immutable하게 retain한 뒤 Candidate를 publication한다.

현재 source/test의 중요한 사실은 `test_same_task_replacement_overlap_stays_captured_and_fails_closed`가
같은 path의 pre-dispatch external change 뒤 Worker overwrite를 실제 canonical tree에 먼저 수행하고,
그 뒤 reconciliation publication만 막는다는 점이다. 이것은 판정 fail-closed이지만 이미 덮어쓴 user
bytes의 preservation은 아니다. 반대로 current Baseline Capsule은 complete retained physical payload와
stable identity를 제공한다.

다음을 우선 공격하라.

1. private workspace + B/W/L adoption이 위 실제 preservation 결함을 닫으면서 Phase 1~3과 모순되는가.
2. Worker Adapter의 “workspace 밖 write 불가”가 실제 보장에 필요한 최소 seam인지, 아니면 구현 불가능한
   가정·범위 확장인지.
3. crash 중 canonical multi-path adoption을 immutable plan과 per-path exact state만으로 재조정하는 것이
   충분한지, 아니면 user change loss·duplicate mutation·영구 recovery 불능의 구체 경로가 남는지.
4. immutable final Candidate source retention이 Phase 2의 exact candidate recoverability에 필요한지,
   Baseline Capsule·Phase 3 result state와 중복 ceremony인지.
5. task/envelope/event/criterion accounting/budget를 삭제하고 “현재 한 call” private progress와 final
   source closure만 남겨도 known due-now implementation gap 부재를 정직하게 보장하는지.
6. 초안이 Phase 5 verification, Phase 6 dangerous effects, Phase 7 fault injection 또는 구 storage/schema를
   Phase 4 Interface로 끌어올렸는지.

findings first, severity 순으로 쓰되 각 finding에 구체 파일·line과 재현 가능한 source-state sequence를
인용하라. confirmed defect, inference, missing runtime verification을 구분하라. Critical/High가 없더라도
목적 손실·복잡성 회귀가 있으면 적어라. 동의를 위한 `CONVERGED`를 선언하지 말고, correction이 꼭
필요할 때만 caller Interface를 늘리지 않는 가장 작은 correction을 제안하라.

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
