# Oracle Browser Pro-capable 3강도 선택 Product Thesis

Result: CALIBRATED

## Source Authority

- 최신 명시적 사용자 요구: Oracle Browser의 Pro 추론 강도에서 세 가지를 각각 지정하여 선택할 수 있어야 한다.
- 최신 명시적 슬롯 경계: 이 세 강도는 관리 슬롯 `1`, `2`, `10`에만 적용한다. 슬롯 `3`, `4`, `5`는 이 제품 선택군의 실행 대상이 아니다.
- 사용자 요청에 따른 live 확인: 슬롯 1, 2, 10의 현재 ChatGPT DOM을 직접 검사했다.
- Current repository investigation: `/home/user01/project/oracle/oracle-browser-slots/docs/investigation/pro-reasoning-level-selection/INV-002.md` (`VALID`).
- 교정된 runtime 사실: 세 강도는 Pro 아래에 중첩된 sublevel이 아니다. 단일 top-level Power slider의 마지막 세 sibling 위치인 `High`(index 2), `Extra High`(index 3), `Pro`(index 4)다.
- 이전 source disposition: `INV-001.md`와 `THESIS-001.md`의 “Pro 내부 3단계” 해석은 live DOM 확인 전의 잘못된 모델이므로 이 Thesis가 대체한다. 이전 파일은 immutable history로만 보존한다.
- 기존 planning authority와의 차이: `oracle-browser-managed-slots.md`의 기존 `extended/high -> (3,4,5,1,2,10)` 정책은 최신 사용자 지시와 충돌한다. 최신 명시적 사용자 지시가 우선한다.
- 진행 경계: 이번 요청은 재사전조사와 Product Thesis 재작성까지다. Scope, Behavior 상세 설계, Spec, Ticket, 구현 및 verification은 포함하지 않는다.

## Reason to Exist

ChatGPT의 현재 Pro-capable 계정 UI는 하나의 Power slider에서 `High`, `Extra High`, `Pro`를 서로 다른 고강도 선택으로 제공한다. Stock Oracle도 이 세 값을 각각 입력받고, canonical intent로 구별하고, slider target을 선택하며, prompt 제출 전에 결과를 검증할 수 있다.

하지만 managed Oracle Browser wrapper는 세 값을 하나의 제품 선택군으로 취급하지 않는다. `Extra High`와 `Pro`는 슬롯 1, 2, 10으로 제한하면서 `High`는 슬롯 3, 4, 5를 포함하고 그 슬롯을 우선한다. 따라서 운영자가 세 고강도 중 하나를 고르는 동일한 기능을 사용한다고 생각해도 `High`만 다른 계정 capability와 profile 경계로 빠질 수 있다.

이 차이는 단순한 후보 순서 문제가 아니다. `High`가 슬롯 3, 4, 5에서 시작되면 managed followup은 부모 원 슬롯을 유지하므로 같은 대화에서 `Extra High`나 `Pro`로 올릴 수 없다. 현재 followup은 다른 Pro-capable 슬롯으로 대화를 옮기지 않으며 옮겨서도 안 된다. 결과적으로 세 강도가 하나의 연속적인 운영 선택처럼 보이지만 실제 대화 lifecycle에서는 닫혀 있지 않다.

이 작업이 존재해야 하는 이유는 새로운 slider나 새로운 reasoning 종류를 만드는 데 있지 않다. 이미 존재하는 세 선택을 **동일한 Pro-capable managed 실행 경계에서 예측 가능하게 지정·선택·검증·변경할 수 있게 하는 것**이다.

## Core Utility

운영자는 Oracle Browser 상담을 시작하거나 명시적으로 followup할 때 `High`, `Extra High`, `Pro` 중 정확히 하나를 선택할 수 있고, 세 선택 모두 정확히 관리 슬롯 1, 2, 10 중 하나에서 실행되며, 요청한 Power 위치가 prompt 제출 전에 실제 선택·검증되었음을 session readback으로 확인할 수 있다.

운영자가 얻는 지속 가능한 가치는 다음 두 가지가 결합된 결과다.

1. **선택 통제**: 세 고강도를 서로 다른 요청으로 지정하고 같은 대화 안에서 명시적으로 바꿀 수 있다.
2. **실행 경계의 일관성**: 어느 강도를 골라도 Pro-capable 슬롯 집합과 conversation origin continuity가 유지된다.

세 값의 이름을 노출하는 것만으로는 충분하지 않다. `High`가 슬롯 3, 4, 5로 라우팅되거나, 요청 강도와 실제 slider selected-state가 다르거나, session evidence가 이를 증명하지 못하면 Core Utility는 없다.

## Core Completion Loop

1. **운영자 의도 입력**
   - 운영자는 현재 invocation에 대해 `High`, `Extra High`, `Pro` 중 하나를 명시한다.
   - 세 값은 각각 독립된 선택이다. `High`를 일반/Plus reasoning으로 재해석하거나 세 값을 모두 generic `pro`로 합치지 않는다.

2. **managed eligibility 판정**
   - Wrapper는 세 값 모두에 대해 exact compatible slot set `(1, 2, 10)`을 산출한다.
   - 슬롯 3, 4, 5는 준비·로그인·비점유 상태와 무관하게 이 선택군의 후보가 아니다.
   - 자동 submit은 후보 순서를 `1 → 2 → 10`으로 유지하고, 명시 run은 이 집합 밖의 슬롯을 claim 전에 거절한다.

3. **conversation origin 보존**
   - Initial run은 선택한 Pro-capable 슬롯에서 대화를 시작한다.
   - Explicit followup은 부모 세션의 원 슬롯을 유지한다.
   - 부모가 슬롯 1, 2, 10에 있으므로 세 강도 사이의 명시 변경이 profile 또는 conversation migration 없이 가능하다.

4. **canonical intent 전달**
   - 요청은 Stock Oracle에 `high`, `extra-high`, `pro` 중 대응하는 canonical intent로 전달된다.
   - 기존 alias가 사용되더라도 최종 intent는 정확히 하나로 귀결되며 다른 강도로 silent fallback하지 않는다.

5. **현재 UI 선택**
   - Browser controller는 현재 ChatGPT composer의 단일 top-level Power slider를 연다.
   - `High`는 position 2, `Extra High`는 position 3, `Pro`는 position 4를 목표로 한다.
   - 이미 해당 위치라면 현재 selected-state를 읽고, 아니라면 trusted input으로 정확한 위치로 이동한다.

6. **제출 전 검증**
   - Live label/announcement와 slider position이 requested intent에 대응하는지 확인한다.
   - `High`는 `High, 3 of 5.`, `Extra High`는 `Extra High, 4 of 5.`, `Pro`는 `Pro, 5 of 5.`라는 current semantic state에 대응한다.
   - Pro는 maximum position과 닫힌 composer pill의 `6 Pro` elevation까지 현재 기존 계약대로 확인한다.
   - 모델 identity, reasoning owner/control continuity 및 requested/resolved equality가 확인되지 않으면 prompt를 제출하지 않는다.

7. **durable readback**
   - Stock session evidence는 `requestedIntent`, `resolvedLevel`, `verified`, `managedSlotId`, `turnIndex`, `attemptIndex`를 현재 invocation에 귀속해 남긴다.
   - Wrapper lifecycle readback은 실제 assigned slot과 origin continuity를 남긴다.
   - 두 readback을 함께 보아야 “요청한 세 강도 중 하나가 허용된 슬롯에서 실제 적용됐다”는 결과가 성립한다.

8. **운영자 결과**
   - 운영자는 세 값 중 무엇을 요청했는지, 어느 managed slot에서 실행됐는지, 실제 어떤 Power 위치가 적용됐는지, 제출 전 검증이 성공했는지를 확인한다.
   - 같은 conversation의 다음 명시 followup에서 다른 두 강도로 변경해도 같은 원 슬롯과 대화가 유지된다.

## Core Behavior Concretization

### 세 강도의 정확한 의미

- `High`: top-level Power slider의 index 2, current announcement `High, 3 of 5.`
- `Extra High`: top-level Power slider의 index 3, current announcement `Extra High, 4 of 5.`
- `Pro`: top-level Power slider의 index 4, current announcement `Pro, 5 of 5.`, current closed pill `6 Pro`

이들은 “Pro mode를 먼저 선택한 뒤 나오는 세 하위 옵션”이 아니다. 하나의 slider에 놓인 sibling 선택이다. 따라서 downstream 설계는 `proSublevel` 같은 허구의 중첩 domain을 만들지 않고 현재 canonical intents를 보존해야 한다.

### 선택과 슬롯의 결합

세 강도를 하나의 제품군으로 묶는 이유는 단순 label 유사성이 아니라 최신 사용자 지정 실행 경계다. 세 값 모두 슬롯 1, 2, 10만 사용한다. 같은 tuple을 사용한다는 사실은 세 강도를 동일 값으로 합쳐도 된다는 뜻이 아니다. Slot eligibility는 같고 UI target과 requested/resolved intent는 다르다.

### Initial invocation

- `High`, `Extra High`, `Pro` 중 하나를 명시하면 wrapper는 `(1,2,10)` 안에서만 슬롯을 선택한다.
- 사용할 수 있는 슬롯이 없으면 queue 또는 명시 실패라는 기존 lifecycle 계약을 적용한다.
- 슬롯 3, 4, 5를 대체 후보로 사용하지 않는다.

### Explicit-slot run

- 슬롯 1, 2, 10에서는 세 값 모두 compatibility gate를 통과할 수 있다.
- 슬롯 3, 4, 5에 세 값 중 하나를 명시하면 child 실행 및 prompt 제출 전에 거절한다.
- “High는 그 슬롯도 기술적으로 표시할 수 있다”는 사실은 최신 제품 eligibility를 무효화하지 않는다. 제품 경계는 capability maximum만이 아니라 사용자 지정 운영 정책을 포함한다.

### Followup

- 부모 세션이 슬롯 1, 2, 10에서 생성되었고 explicit reasoning이 주어지면 같은 원 슬롯에서 해당 강도를 다시 선택·검증한다.
- reasoning을 생략한 followup은 현재 UI 선택을 그대로 두는 기존 의미를 유지한다. 임의로 세 값 중 하나를 default하지 않는다.
- 목표 밖 슬롯에서 생성된 historical parent에 세 값 중 하나를 명시했을 때 다른 슬롯으로 migration하거나 새 conversation으로 fallback하지 않는다. 현재 원 슬롯 continuity 계약에 따라 명시 실패해야 한다.

### 실패와 fallback

다음 조건에서는 prompt가 제출되지 않아야 한다.

- 요청값이 세 canonical intent 중 하나로 해석되지 않음
- Wrapper가 exact `(1,2,10)` eligibility를 확정하지 못함
- 원 슬롯 followup이 요청 강도를 지원하지 않음
- Power control이 없거나 하나보다 많아 owner가 모호함
- 현재 slider range/label이 known mapping과 맞지 않음
- native interaction 후 requested position으로 이동하지 않음
- requested intent와 resolved level이 다름
- model identity 또는 control continuity가 깨짐
- Pro 요청에서 maximum/`6 Pro` readback이 확인되지 않음

Nearest level, 현재 level, default level, generic Pro 또는 다른 슬롯으로의 silent fallback은 허용되지 않는다.

## Required Outcomes / Means

### Required Outcomes

- 운영자는 `High`, `Extra High`, `Pro`를 각각 명시해 선택할 수 있다.
- 세 선택 모두 슬롯 1, 2, 10에서만 실행된다.
- 자동 배정, explicit run, followup compatibility가 같은 eligibility 의미를 사용한다.
- 요청한 선택과 실제 Power selected-state가 일치한다.
- 실행 결과에서 exact requested/resolved level과 managed slot을 확인할 수 있다.
- 같은 Pro-capable 원 슬롯의 conversation에서 세 강도 사이 explicit followup 변경이 가능하다.

### Required Means

- 세 canonical intent `high`, `extra-high`, `pro`의 구별을 유지한다.
- Wrapper의 High/extended compatibility를 최신 exact slot boundary에 맞춘다.
- Stock의 existing native Power slider selection을 사용한다.
- Prompt-before-reasoning 순서와 fail-closed verification을 유지한다.
- Managed followup의 원 슬롯/profile/conversation continuity를 유지한다.
- Wrapper routing readback과 Stock selection evidence를 서로 다른 권위로 유지한다.

### Derived Necessity

- High를 `(1,2,10)`으로 제한하는 것은 단순 구현 선호가 아니다. 세 선택을 동일 conversation lifecycle에서 상호 변경 가능한 하나의 제품 선택군으로 제공하려면 최초 High도 Pro-capable 원 슬롯에서 시작해야 한다.
- 슬롯 3, 4, 5의 기술적 High 지원보다 최신 사용자 지정 제품 경계가 우선한다. 기술적으로 가능한 경로가 제품적으로 허용된 경로를 자동 결정하지 않는다.

## Candidate / Supporting Means

- Existing public option `--browser-thinking-time high|extra-high|pro`를 그대로 사용한다. 새 옵션 family보다 현재 contract 재사용이 단순하다.
- Existing aliases `extended`와 `heavy`를 각각 High와 Extra High로 계속 받을 수 있다. 단, alias도 동일한 exact slot policy로 귀결되어야 한다.
- Wrapper 내부에서 세 canonical values를 하나의 `pro-capable-high-intensity` routing class로 묶을 수 있다. 이는 route classification일 뿐 reasoning identity 통합이 아니다.
- User config와 MCP 표면을 현재 세-value vocabulary에 정렬하는 일은 supporting means다. 어느 표면을 같은 Increment에 포함할지는 Scope/Behavior owner가 판단한다.
- User docs에서 legacy `Pro Standard/Extended` 설명을 current five-step Power model로 교체하는 일은 truth-alignment supporting work다.
- Existing `BrowserManagedSlotCapability.maximumReasoning`을 그대로 둘지, eligibility policy를 별도로 명시할지는 구현 선택이다. 현재 제품 결과는 exact route와 readback으로 판단한다.
- Existing test matrix의 `high_slots`를 product group에 맞게 바꾸고 run/submit/followup rejection을 함께 관찰하는 것은 verification candidate다.

## Non-Core / Defer Candidates

- 새로운 `ProSublevel` 타입 또는 nested Pro domain 도입. Live DOM에 그런 구조가 없다.
- 새로운 slider component, selector family 또는 UI automation architecture 작성. 현재 Stock 경로가 세 위치를 이미 처리한다.
- 슬롯 3, 4, 5의 계정이나 UI capability 제거. 이번 요구는 그 슬롯의 일반 기능을 제거하는 것이 아니라 이 세-value managed product route에서 제외하는 것이다.
- 슬롯 1, 2, 10 사이의 상대순서 변경. 현재 `1 → 2 → 10`을 유지한다.
- Followup slot migration 또는 conversation 복제.
- API engine reasoning effort 변경.
- GPT 외 모델, Deep Research, image generation 또는 일반 browser mode 재설계.
- 응답 품질 자체가 High/Extra High/Pro 이름과 선형적으로 비례한다는 보장.
- Legacy compatibility code 전체 삭제. 현재 product path와 충돌하는 부분만 후속 owner가 판단한다.
- 기존 `gpt-model-reasoning-elevation` Ticket의 상태 복구나 verification. 새 제품 의미와 별도 delivery bookkeeping 문제다.

## Truth / Causal Invariants

- **실제 구조의 진실성**: 세 값은 top-level `High`, `Extra High`, `Pro`다. nested Pro sublevel로 기록하거나 설명하지 않는다.
- **요청 구별성**: `high`, `extra-high`, `pro`는 서로 다른 requested/resolved identity를 유지한다.
- **exact slot set**: 세 값의 initial managed candidates는 정확히 `(1,2,10)`이다. 슬롯 3,4,5를 포함하거나 fallback으로 사용하지 않는다.
- **ordering 보존**: 자동 할당의 상대순서는 `1 → 2 → 10`이다.
- **routing/selection 분리**: 같은 candidate tuple을 사용해도 세 Power target은 각각 index 2,3,4로 다르다.
- **현재 UI 권위**: 실제 selected-state는 current DOM readback으로 증명한다. config, test fixture, slot capability 또는 과거 metadata는 현재 선택을 대신하지 않는다.
- **인과 순서**: compatible slot 결정 → original slot/profile 확보 → exact UI selection → positive readback → prompt 제출 순서를 지킨다.
- **requested/resolved equality**: 요청 intent와 resolved level이 다르면 성공이 아니다.
- **Pro 강화 검증**: Pro는 level label뿐 아니라 maximum position 및 current `6 Pro` elevation을 확인한다.
- **model/reasoning 분리**: `6 Pro` reasoning pill은 base model identity를 대체하지 않는다.
- **followup continuity**: explicit followup은 부모의 슬롯/profile/conversation을 유지하며 다른 슬롯으로 옮기지 않는다.
- **turn 귀속성**: 선택 evidence는 해당 turn과 attempt에 귀속된다. 이전 turn의 성공을 현재 선택 성공으로 재사용하지 않는다.
- **실패 정직성**: unavailable, ambiguous, mismatched, unsupported 상태를 성공이나 default 선택으로 바꾸지 않는다.
- **권위 결합**: Wrapper readback은 올바른 slot/origin을, Stock evidence는 올바른 Power selection을 증명한다. 둘 중 하나만으로 전체 제품 결과를 주장하지 않는다.

## Success Observation

Core Utility는 다음 observable sequence가 성립할 때 확인된다.

### Initial 선택 세트

각각 독립적인 `High`, `Extra High`, `Pro` 요청에서:

- Wrapper의 compatible candidates가 정확히 `[1,2,10]`이다.
- 실제 assigned slot이 1, 2, 10 중 하나다.
- 슬롯 3, 4, 5는 available이어도 선택되지 않는다.
- Stock session evidence의 `requestedIntent`가 각각 `high`, `extra-high`, `pro`다.
- Prompt 제출 전 live selected-state가 각각 Power index 2, 3, 4에 대응한다.
- `resolvedLevel`이 요청값과 각각 일치하고 `verified: true`다.
- Pro 요청에서는 maximum 및 닫힌 `6 Pro` readback이 확인된다.

### Explicit run rejection

슬롯 3, 4, 5에 `High`, `Extra High`, `Pro` 중 하나를 지정하면:

- child process/queue/prompt 제출 전에 compatibility rejection이 발생한다.
- 요청 수준을 낮추거나 다른 값으로 바꾸지 않는다.

### Followup continuity

슬롯 1, 2 또는 10에서 시작한 같은 conversation에 대해 강도를 `High → Extra High → Pro` 또는 다른 명시 순서로 변경하면:

- 모든 turn이 부모의 동일 origin slot/profile/conversation에서 실행된다.
- 매 turn마다 requested/resolved level이 새 요청과 일치한다.
- 이전 turn evidence가 현재 turn verification을 대신하지 않는다.

### 거짓 성공의 반례

다음은 feature가 있어 보이지만 Core Utility가 없는 상태다.

- CLI help에 세 값이 보이지만 High가 슬롯 3, 4, 5로 배정된다.
- Extra High와 Pro만 1, 2, 10에 있고 High는 기존 tuple을 유지한다.
- `gpt-6-pro` model일 때만 우연히 세 값이 1, 2, 10으로 가고 다른 허용 model에서는 High가 새 경계를 우회한다.
- Initial High는 슬롯 3에서 성공하지만 같은 conversation의 Pro followup은 원 슬롯 incompatibility로 실패한다.
- Wrapper tuple은 맞지만 slider가 요청과 다른 위치에 있고 prompt가 제출된다.
- 세 요청의 metadata가 모두 generic `pro` 또는 동일 resolved value로 기록된다.
- Pro pill `6 Pro`만 보고 High/Extra High/Pro 중 실제 current position을 추정한다.
- 슬롯 3,4,5가 비어 있다는 환경 조건 때문에 테스트가 통과하지만 eligibility 자체는 여전히 그 슬롯들을 포함한다.

## Counterexample Gates

1. 모든 옵션과 문서가 존재해도 High가 슬롯 3,4,5로 가면 durable utility가 없는가? **예.** 세 선택군의 managed boundary와 followup closure가 깨진다.
2. Core Utility 문장이 형식상 참이어도 prompt 전 exact selection verification이 빠지면 loop가 깨지는가? **예.** 요청과 실제 Power 위치의 인과가 없다.
3. 제품이 성공을 표시해도 assigned slot 또는 selected-state readback이 거짓일 수 있는가? **예.** Wrapper와 Stock의 두 권위가 모두 필요하다.

세 질문의 반례를 Success Observation과 Truth Invariants가 차단하므로 calibrated 상태다.

## Open Product Meaning

None. 사용자는 세 선택의 실제 의미(`High`, `Extra High`, `Pro`)와 exact 적용 슬롯(`1`, `2`, `10`)을 확정했다. CLI spelling 유지, alias 범위, config/MCP projection, wrapper 내부 분류 방식, legacy cleanup 및 exact verification flow는 downstream Scope/Behavior/implementation planning 소유이며 Core Utility를 변경하지 않는다.
