# Phase 1 — 목적 보존 계약

상태: `DESIGN_CONVERGED`

## 단일 결정

Implementation Lead와 Verification Lead의 단순화가 끝난 뒤에도 성공이라고 부를 수
있는 결과는 무엇이며, 그 결과를 외부에서 최소한 어떻게 구분할 수 있어야 하는가를
정한다. 이 문서는 그 결과 계약만 정한다. 호출 형식, 저장 방식, 재시작 규칙, 동시성,
실행기와 legacy 제거는 정하지 않는다.

## 보존할 사용자 가치

1. 준비된 Ticket의 정확한 Acceptance Criteria에 대해 구현 후보가 만들어진다.
2. 구현 과정이 Ticket 범위 밖의 기존 사용자 변경을 지우거나 구현자가 만든 변경인 것처럼
   바꾸어 주장하지 않는다.
3. 구현 완료 주장이 최종 제품 동작의 합격 판정을 대신하지 않는다.
4. 최종 판정은 구현 주체와 분리된 새 검증 관점에서, 후보 source와 실제 source 검토 및/또는
   제품 흐름 관찰에 근거해 수행된다.
5. 긍정적 결과는 어떤 planning 기준, 어떤 후보 source, 어떤 AC, 어떤 독립 evidence에 관한
   것인지 서로 대조할 수 있다. 하나라도 대조할 수 없으면 긍정적 최종 판정을 내리지 않는다.

## 최소 결과 계약

### A. 구현 후보 결과

구현 단계가 외부에 남기는 의미는 하나뿐이다. **이 후보는 Implementation Lead가 확인한
due-now 구현·통합 의무 중 알려진 미완료가 없어서 다음 독립 검증에 넘겨도 되는 구현
후보다.** 이는 최종 성공 선언이 아니다.

그 결과는 다음 관찰을 가능하게 해야 한다.

- 후보가 대응하는 정확한 planning 입력과 AC 집합을 식별할 수 있다.
- 검증자가 실제로 검토할 후보 source를 식별하고 다시 읽을 수 있다.
- 구현 범위의 변경과 구현에 귀속하지 않은 기존/동시 변경을 구별할 수 있다. 후자는 후보에
  존재할 수 있지만 구현 성공의 근거가 되거나 조용히 삭제되어서는 안 된다.
- 구현 단계에서 수행한 check은 구현 폐쇄의 보조 근거일 수 있으나, AC 만족 또는 최종 runtime
  성공의 증거로 승격되지 않는다.

### B. 독립 검증 결과

검증 단계가 외부에 남기는 의미는 하나뿐이다. **식별된 후보 source가 식별된 planning의 각
AC를 충족했는지, 충족하지 못했는지, 또는 아직 판정할 수 없는지에 관한 독립 판정이다.**

충족 또는 불충족이라는 결론적 AC 판정에는 최소한 다음 관찰이 결속되어야 한다.

- 검토한 후보 source와 planning/AC가 구현 후보 결과의 그것과 일치한다.
- 모든 AC가 빠짐없이 독립 검증의 대상이 되었다.
- 각 AC의 판정은 검증 단계가 직접 읽은 source 및/또는 직접 실행해 얻은 evidence로 설명된다.
- 결론적 판정의 evidence는 그 AC와 승인된 planning이 요구한 관찰 수준에 충분해야 한다. runtime
  결과·외부효과·readback이 요구되면 source review나 구현 check만으로 대체하지 않는다.
- 구현 Worker의 서술, 구현 단계의 check, 이전 검증의 결론은 단독으로 이 판정을 만들 수 없다.
- 검증 중 source를 수정하지 않는다. 수정이 필요하면 그 검증은 현재 후보의 긍정 판정을
  만들지 않고 구현 단계로 되돌아간다.

### C. 정직한 미확정

planning, 후보 source, AC coverage, 독립 evidence 중 하나가 누락·불일치·판독 불능이면 결과는
`검증된 성공`이 아니다. 또한 evidence의 부족 자체는 AC가 충족되지 않았다는 증명이 아니다.
그 경우는 **미확정**으로 남아야 하며, **실패**는 충분한 independent evidence가 AC 불충족을
보일 때만 가능하다. 이 Phase는 상태 이름이나 복구 경로를 정하지 않으며, 그 의미만 고정한다.

## 최소 외부 관찰과 숨길 구현

| 외부에서 알아야 할 사실 | Module 안에 숨겨야 할 선택 |
| --- | --- |
| 후보가 어떤 planning/AC와 어떤 source에 관한 것인지 | digest·handle·파일 형식·저장소·수명·lease의 구체 형식 |
| 구현 후보인지, 독립 검증 판정인지 | actor capability, claim, budget, transaction, ledger, replay의 표현과 수명 |
| 각 AC가 독립 evidence로 판정되었는지 | check 순서, runner 내부 step/lock, evidence 수집·redaction·publication 방식 |
| 기존 사용자 변경이 보존됐는지 또는 보존을 입증하지 못했는지 | before/after snapshot, path partition, baseline capture와 reconciliation 알고리즘 |
| 긍정 판정이 가능한지 | status enum, schema, atomic publication, restart와 remediation protocol |

따라서 외부 Interface는 구현의 proof machinery를 호출자가 조립하는 API가 아니라, 후보와
독립 판정의 위 네 가지 관찰을 제공하는 작은 결과 경계여야 한다. 구체적인 함수·CLI·payload는
Phase 2에서만 정한다.

## 실제 Seam과 근거

- 현재 Implementation Lead는 정확한 Ticket/AC, pre-existing work 보존, 후보 source identity와
  별도 `implementation-handoff-v1`을 명시하고, 이를 최종 검증이라고 부르지 않는다
  (`implementation-lead/SKILL.md`의 Purpose, Mutation boundary, Handoff sections).
- 현재 Verification Lead는 같은 planning/source에 대한 fresh read-only Assessor의 AC 판정과
  `verification-result-v1`을 분리한다 (`verification-lead/SKILL.md`의 Purpose, role separation,
  sealed draft sections).
- Baseline Capsule은 변경 전 physical source identity와 payload를 보존하지만 planning 또는
  verdict를 소유하지 않는다 (`baseline-capsule/PROTOCOL.md`의 Purpose 및 Public interface).
- 현재 command surface도 구현 handoff publication과 검증 run/result publication을 분리한다:
  `implementation_result.py --help`은 `publish`만, `verification_run.py --help`은 별도
  `open-verification`/`seal-run`/`execute-step`/`publish-result`을 제공한다.
- 현재 in-repo의 명시적 소비자는 README와 Matt Ticket 지침이다. 후자는 동일한 raw AC identity를
  handoff와 verification result에 공유하되 별도의 사용자용 AC 식별자를 더하지 말라고 한다
  (`matt/skills/to-tickets/SKILL.md`). 별도 제품 runtime consumer는 이 조사에서 발견되지 않았다.
- runtime baseline: `python3 baseline-capsule/run_tests.py`,
  `python3 implementation-lead/run_tests.py`, `python3 verification-lead/run_tests.py`가 모두
  통과했다. 특히 구현 check가 final verdict가 될 수 없음을 확인하는 pilot과, runner-owned
  evidence가 `VERIFIED`를 만들고 disconnected flow를 거부하는 process pilots가 있다.

## 허용한 실패·복구 의미

- 현재 후보와 planning/AC/evidence의 결속을 확인할 수 없으면 긍정 최종 판정을 하지 않는다.
- 기존 사용자 변경의 보존을 입증할 수 없으면 그 후보를 구현 성공으로 조용히 넘기지 않는다.
- 검증 중 수정이 필요하면 현재 검증 결과는 수정된 source에 대한 판정이 될 수 없다.

재시작 뒤의 결과 가시성, 어느 실패가 재시도 가능한지, 동시 실행의 선형성, durable record의
형태, effects의 readback은 이 단계에서 의도적으로 미결정이다.

## 최소 시나리오

1. Ticket/AC와 후보 source가 일치하고, 범위 밖 사용자 변경은 보존된다. 구현 결과는 독립
   검증 대기 후보만 나타낸다.
2. fresh verifier가 그 후보 source에서 모든 AC를 source review와/또는 제품 흐름으로 직접
   확인한다. runtime 관찰이 요구된 AC는 실제 그 관찰을 얻어야 한다. 그때만 긍정 최종 판정이
   가능하다.
3. 구현 check가 통과해도 독립 evidence가 없으면 최종 성공이 아니다.
4. 후보 source 또는 Ticket/AC가 검증 시작 뒤 달라지면 그 관찰은 현재 후보의 긍정 evidence가
   아니다.
5. 검증 중 결함을 발견해 source 변경이 필요하면 현재 검증은 결함 또는 미확정으로 끝나고,
   수정된 후보는 새 구현 결과와 새 독립 검증을 거친다.
6. 필요한 관찰을 얻지 못한 것은 성공도 불충족도 증명하지 않는다. AC 불충족이라는 결론에는
   그 결론에 충분한 independent evidence가 필요하다.

## 명시적 범위 밖

- caller 함수명·argument·응답 schema와 status enum
- source identity의 해시/저장/retention 방식과 user-change 보존 알고리즘
- durable workflow state, claim/lock/transaction/lineage/concurrency
- Worker dispatch·ownership reconciliation·runner의 executor와 fault injection
- 외부효과 authorization, replay, readback
- runtime 통합 검증 및 현재 legacy mechanism 삭제

## Oracle finding 판정 기록

### F1 — AC 관찰 수준과 evidence 충분성

```text
ORACLE_CLAIM
각 AC의 직접 source/evidence만으로는 runtime 결과·effect·readback을 요구한 AC가 source
review만으로 긍정 판정되는 것을 막지 못한다.

STRONGEST_COUNTERARGUMENT
초안은 planning/AC 결속과 직접 evidence를 이미 요구하며, evidence 선택은 Phase 5의 소유다.
따라서 이 지적으로 sealed plan, evidence taxonomy, runner protocol을 Phase 1로 올리면 과설계다.

PURPOSE_INVARIANT_AT_RISK
정확한 구현의 최종 판정과 source·AC·evidence 결속. AC가 요구한 관찰을 하지 않은 긍정
결론은 independent verification을 구현 check의 다른 이름으로 축소한다.

CONCRETE_EVIDENCE
현재 초안의 “source 및/또는 직접 실행 evidence”와 “source review와/또는 제품 흐름” 문구는
runtime 관찰이 필요한 AC의 evidence 적합성을 명시하지 않았다. 현재 Ticket 지침은 observable
outcome을 AC로 삼으며, verification pilot은 runner-owned execution의 완전성을 보일 뿐 그
실행이 승인된 product observation인지 보장하지 않는다.

CURRENT_PHASE_OWNERSHIP
긍정 verification 결과가 무엇을 의미하는지는 Phase 1의 단일 결정이다. evidence를 어느
runner가 어떻게 선택·seal·실행하는지는 Phase 5에 남긴다.

SMALLEST_CORRECTION
B절에 “AC와 승인된 planning이 요구한 관찰 수준에 충분한 evidence가 필요하고, runtime
결과·effect·readback은 source review나 implementation check로 대체하지 않는다”를 추가했다.

COMPLEXITY_DELTA
Caller Interface, 호출 단계, durable state, status, protocol 증가 0. planning이 runtime
관찰을 요구한 경우에만 실제 그 관찰을 요구한다. sealed plan/flow ID/digest/evidence schema는
추가하지 않는다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — 결과 의미의 누락만 수용한다. evidence mechanism 요구는
DEFER_TO_PHASE_5.
```

### F2 — candidate-ready의 알려진 구현·통합 미완료 부재

```text
ORACLE_CLAIM
현재 후보 결과는 planning/source 식별과 user-change 보존을 말하지만, Implementation Lead가
알고 있는 due-now 구현·통합 미완료가 없어야 한다는 뜻을 고정하지 않는다.

STRONGEST_COUNTERARGUMENT
“독립 검증에 넘겨도 되는 구현 후보”라는 자연어는 implementation sufficiency를 함축한다.
그러나 Phase 1에서 이를 명시하지 않으면 Phase 2 Interface가 알려진 미완료 후보도 정상
candidate로 표현할 수 있다. task accounting이나 unresolved-items field를 보존하는 것은 별개다.

PURPOSE_INVARIANT_AT_RISK
Implementation Lead의 정확한 구현 책임, 구현과 검증의 분리, 불필요한 verification 재검사와
왕복 비용의 방지.

CONCRETE_EVIDENCE
현재 Implementation Lead 계약은 implementation sufficiency를 소유하고 handoff 전 알려진
구현 미완료가 없어야 한다고 명시한다. 초안의 후보 관찰에는 이 부재가 없었다. 구현 check가
최종 verdict가 아님을 보이는 pilot도 이 누락을 대체하지 못한다.

CURRENT_PHASE_OWNERSHIP
candidate-ready의 의미는 Phase 1 소유다. 구현 closure 절차, check, integration 조사, task
목록은 Phase 4 소유다.

SMALLEST_CORRECTION
A절 첫 문장에 “Implementation Lead가 확인한 due-now 구현·통합 의무 중 알려진 미완료가
없는 후보”를 추가했다.

COMPLEXITY_DELTA
Caller Interface, 호출 단계, durable state, status 증가 0. 새 task 목록, criterion accounting,
transaction/envelope, unresolvedImplementationItems field를 도입하지 않는다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — candidate 결과의 의미만 수용한다. completion record의 data shape와
구현 closure algorithm은 DEFER_TO_PHASE_4.
```

### F3 — evidence 부족과 결론적 AC 불충족의 구분

```text
ORACLE_CLAIM
F1 보강은 긍정 판정에만 충분한 evidence를 요구한다. evidence 누락·불일치·판독 불능이
AC 불충족이라는 결론으로 오인될 수 있다.

STRONGEST_COUNTERARGUMENT
초안은 이미 “충족·불충족·판정 불능”의 세 결과 의미를 언급하며 F1은 success overclaim을
막았다. 그러나 C절의 “미확정 또는 실패”는 evidence 부족과 contradiction을 구분하지 않아
올바른 후보의 불필요한 remediation을 허용할 수 있다. contradiction record·status enum을
넣는 것은 별개의 과설계다.

PURPOSE_INVARIANT_AT_RISK
독립 검증의 정확성, source·AC·evidence 결속, 근거 없는 재구현이 사용자 변경에 주는 위험과
정상 실행 비용의 방지.

CONCRETE_EVIDENCE
현재 Verification Lead 계약은 valid exact contradiction과 evidence/identity/sequence
incompleteness를 서로 다른 결과로 다룬다. 초안의 긍정 evidence 문구는 결론적 불충족에는
적용되지 않았고, C절은 evidence 부족을 미확정 또는 실패로 남길 수 있었다.

CURRENT_PHASE_OWNERSHIP
AC 불충족이라는 결론의 의미는 Phase 1 소유다. 어떤 evidence를 모으고 contradiction을
도출·저장하는지는 Phase 5 소유다.

SMALLEST_CORRECTION
“충족 또는 불충족이라는 결론적 AC 판정” 모두에 sufficient evidence를 요구하고,
evidence 부족 자체는 불충족 증명이 아니며 미확정이라는 C절 문장으로 좁혔다.

COMPLEXITY_DELTA
Caller Interface, 호출 단계, durable state, status, protocol 증가 0. 새 evidence bit,
contradiction record, sealed obligation, ledger는 추가하지 않는다.

DISPOSITION
ACCEPT_WITH_BOUNDARY — 결과 의미의 누락만 수용한다. contradiction mechanism과 evidence
completeness implementation은 DEFER_TO_PHASE_5.
```

## Source-only 재공격과 수렴 판정

재공격은 이 문서, `implementation-lead/SKILL.md`, `verification-lead/SKILL.md`,
`matt/skills/to-tickets/SKILL.md`, 기존 test/runtime baseline만으로 수행했다. 세 번째
Oracle follow-up의 자기 session readback·상태·그에 의존한 결론은 이 판정에 사용하지 않았다.

- **F1 닫힘:** B절은 결론적 AC 판정의 evidence가 planning이 요구한 관찰 수준에 충분해야
  한다고 고정한다. runtime·effect·readback AC를 source review나 implementation check만으로
  결론 낼 수 없으며, source-only AC에는 충분한 source evidence를 허용한다.
- **F2 닫힘:** A절의 candidate-ready는 알려진 due-now 구현·통합 미완료가 없는 후보일 뿐,
  final product certification이 아니다. task accounting과 closure algorithm은 Phase 4에 남는다.
- **F3 닫힘:** C절은 evidence 부족을 미확정으로, 충분한 independent evidence가 보인 AC
  불충족만을 실패로 분리한다. 새 status, contradiction record, evidence schema를 요구하지 않는다.

독립성은 fresh verifier와 구현 check의 비최종성(B절), source currentness는 candidate와
planning/AC의 일치 및 변경 뒤 관찰의 비유효성(B절과 시나리오 4), 사용자 변경 보존은 A절의
변경 구별·비허위 귀속 규칙으로 이미 남아 있다. freshness actor ID, source identity 형식,
evidence 공개 형식, sealed plan, durable publication, recovery, concurrency, executor,
contradiction mechanism, audit/replay는 현재 결과 의미를 바꾸지 않는 후속 단계 선택으로
분류한다.

**판정: `DESIGN_CONVERGED`.** F1~F3이 확인된 결과 의미 결함을 모두 닫았고, 새 Phase 1
finding은 없다. Phase 2의 Interface·복구 의미, Phase 4의 구현 closure, Phase 5의 evidence
selection/execution을 이 계약에 앞당겨 넣지 않는다.

## 완료 판단

- 구현 후보와 독립 검증 결과를 분리하면서, Ticket/AC·source·evidence 결속과 사용자 변경 보존을
  빠뜨리지 않았다.
- caller에 capability·claim·audit·replay·workflow protocol을 요구하지 않았다.
- source identity, storage, recovery, concurrency, execution method 같은 후속 단계 결정을
  Interface로 올리지 않았다.
- 확인 불가능한 경우에 긍정 결론을 내리지 않는 최소 fail-closed 의미를 정했다.
- evidence 부족을 AC 불충족과 혼동하지 않고, 양방향 결론적 AC 판정에만 충분한 evidence를
  요구한다.
