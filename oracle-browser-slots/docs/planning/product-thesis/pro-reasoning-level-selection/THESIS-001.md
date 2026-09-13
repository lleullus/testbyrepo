# Oracle Browser Pro 추론 3단계 개별 선택 Product Thesis

Result: CALIBRATED

## Source Authority

- 명시적 사용자 요구: 현재 Pro 추론에는 3가지 강도가 존재한다. Oracle Browser에서는 현재 하나만 고를 수 있으므로, Pro 추론 강도에서 세 강도를 각각 지정하고 선택할 수 있어야 한다.
- 명시적 진행 경계: 이번 요청은 IIS 사전조사 후 Product Thesis까지이며, 구현·Spec·Ticket 작성은 포함하지 않는다.
- 사용자 관찰 권위: “현재 Pro 추론에는 3가지가 있다”와 “현재 Oracle Browser는 하나밖에 못 고른다”는 현재 제품 상태로 수용한다.
- Repository evidence: `/home/user01/project/oracle/oracle-browser-slots/docs/investigation/pro-reasoning-level-selection/INV-001.md`. 이 자료는 현재 기술 상태와 제약의 근거이며 제품 요구의 독립 권위는 아니다.
- 기존 계획 경계: `gpt-model-reasoning-elevation`의 INV/SPEC/TICKET/PLAN은 top-level 5단계 slider의 단일 `pro`/`6 Pro` elevation을 다룬다. 새 Pro 내부 3단계 의미를 승인하거나 충족하지 않는다.

## Reason to Exist

Oracle Browser의 현재 공개 입력, 내부 reasoning intent, UI selector 및 세션 evidence가 모두 Pro를 단일 `pro` 값으로 축약한다. 운영자는 Pro를 요청할 수는 있지만 Pro 내부의 어느 강도를 의도했는지 지정할 수 없고, 실행 후에도 어느 강도가 실제 선택되었는지 구별할 수 없다.

이 결손은 단순 옵션 부족이 아니다. 세 강도가 서로 다른 응답 시간·추론 자원·결과 특성을 제공하는데도 시스템이 이를 하나로 합치면, 운영자의 비용/지연/품질 선택권이 사라지고 “요청한 강도로 실행했다”는 결과도 증명할 수 없다. 이름만 세 개 추가해 모두 같은 `pro` 동작으로 보내는 것은 현재 결손을 가리는 거짓 완료다.

## Core Utility

운영자는 각 Oracle Browser 상담마다 현재 Pro가 제공하는 세 추론 강도 중 정확히 하나를 명시적으로 선택하고, Oracle Browser가 그 동일 강도를 실제 ChatGPT Pro UI에 적용한 뒤에만 요청을 제출했으며, 완료 후에도 세션 readback으로 그 사실을 구별해 확인할 수 있다.

이 효용은 특정 CLI spelling, DOM selector, slider/메뉴 구현에 종속되지 않는다. 지속되어야 할 값은 **의도한 Pro 세부 강도와 실제 적용·기록된 Pro 세부 강도의 동일성**이다.

## Core Completion Loop

1. **의도 입력**: 운영자가 한 상담 또는 명시적 followup에 대해 Pro 내부 세 강도 중 하나를 지정한다. 세 값은 입력 시점부터 서로 다른 의미로 유지되어야 한다. 하나의 `pro`로 조기 정규화하면 이후 단계가 올바른 강도를 복구할 수 없으므로 제품 약속이 깨진다.
2. **capability 책임**: managed wrapper는 요청이 Pro-capable 슬롯에서만 실행되도록 현재 entitlement 경계를 적용한다. 세 강도가 같은 슬롯군을 공유하더라도 이것은 routing equality일 뿐 selection equality가 아니다.
3. **의도 보존**: CLI/config/MCP/followup 중 지원 대상으로 채택된 진입 표면은 선택한 세부 강도를 canonical identity로 stock browser controller까지 손실 없이 전달한다. alias가 있더라도 서로 다른 세 강도를 같은 canonical 값으로 합치면 안 된다.
4. **시스템 작업**: Oracle Browser는 현재 ChatGPT Pro control을 열고, 요청한 세부 강도에 대응하는 정확한 control/position/item을 선택한다. 이미 선택된 경우에도 추측하지 않고 현재 selected-state를 읽는다.
5. **도메인 판정**: 시스템은 현재 UI에서 발견한 세 강도와 요청 강도의 관계가 유일한지, 해당 슬롯이 그 강도를 실제 제공하는지, 선택 후 readback이 요청과 일치하는지 판정한다. control 부재, 중복 매칭, label/position 불명, entitlement 부족은 임의 기본값이나 가장 가까운 강도로 대체하지 않는다.
6. **제출 경계**: 요청한 정확한 세부 강도가 positive readback으로 확인된 경우에만 prompt를 제출한다. 검증 실패 상태에서 “현재 Pro니까 충분하다”고 제출하면 사용자의 강도 선택과 실제 결과 사이 인과가 끊어진다.
7. **관찰 가능한 결과**: session evidence는 requested Pro sublevel, resolved Pro sublevel, verification result 및 해당 turn/attempt를 서로 구별해 남긴다. wrapper lifecycle 성공만으로 실제 강도 적용을 주장하지 않는다.
8. **운영자 결과**: 운영자는 실행 전에는 원하는 품질/지연 선택을 통제하고, 실행 후에는 그 선택이 실제 적용된 consultation 결과인지 확인할 수 있다.

### 필수 Core Behavior 구체화

- 세 강도 각각은 독립적으로 요청 가능해야 한다. 세 값 중 둘만 구현하거나 셋째를 “기본 Pro”로 암묵 처리하면 요구를 충족하지 않는다.
- 명시 선택은 해당 invocation에 귀속된다. 이전 탭, 이전 turn, config default 또는 부모 세션의 저장값이 현재 UI selected-state를 대신할 수 없다.
- followup에서 강도를 명시하면 같은 대화의 원 슬롯에서 그 강도를 다시 적용·검증한다. 강도를 생략한 followup의 의미는 현재 UI 선택 유지이며, 과거 metadata를 현재 선택의 증거로 재사용하는 것이 아니다.
- unsupported 또는 관찰 불가능한 강도는 prompt 제출 전 명시적으로 실패해야 한다. silent fallback, nearest-level 선택, top-level `pro`로의 collapse는 금지된다.
- 기존 base-model identity와 reasoning-only `6 Pro` 구분은 유지되어야 한다. 세부 강도 지원을 이유로 모델 선택 증거와 reasoning 선택 증거를 섞으면 잘못된 모델에서 성공을 주장할 수 있다.

## Required Outcomes / Means

### 명시적 Required Outcome

- 현재 Pro 추론의 세 강도를 각각 지정하고 선택할 수 있다.

### 결과에서 필연적으로 도출되는 Required Behavior

- 세 요청값은 입력부터 UI target과 durable readback까지 서로 구별된다. 이유: 어느 값이 실행되었는지 구별할 수 없으면 “각각 선택”을 관찰할 수 없다.
- 실제 selected-state가 요청한 세부 강도와 일치해야 한다. 이유: 입력 수용만으로는 UI 적용을 보장하지 않는다.
- 선택 검증은 prompt 제출보다 먼저 완료된다. 이유: 제출 후 발견한 오선택은 이미 잘못된 강도로 consultation을 실행한 뒤다.
- 실패 시 선택되지 않은 강도로 자동 제출하지 않는다. 이유: silent fallback은 운영자의 명시 선택을 무효화하면서 성공처럼 보인다.
- session readback은 requested/resolved 세부 강도를 포함한다. 이유: wrapper의 슬롯 성공이나 generic `verified: true`만으로는 세 강도 중 무엇이 실행됐는지 증명할 수 없다.

### Required Means

- 현재 관리형 Pro-capable 슬롯 경계 보존. Plus 슬롯에 Pro 세부 강도를 강제 배정하지 않는다.
- 모델 identity와 reasoning identity의 분리 및 기존 fail-closed 검증 보존.

## Candidate / Supporting Means

- 기존 `--browser-thinking-time` 옵션을 확장해 세 canonical Pro sublevel을 받는 방식. 공개 호환성이 좋지만 정확한 token 이름은 downstream Behavior/API planning이 정한다.
- 계층형 canonical 값(예: `pro:<level>` 개념) 또는 별도 Pro sublevel 필드. 어느 표현을 택하든 세 값의 end-to-end identity가 보존되어야 한다.
- 현재 UI label을 canonical naming의 출발점으로 채택하는 방식. UI label 변화에 대한 alias/normalization 정책은 replaceable means이며 제품 효용 자체가 아니다.
- 세 강도가 동일 entitlement를 가진다는 evidence가 확보되면 wrapper routing은 기존 Pro 슬롯군 `(1, 2, 10)`을 공유할 수 있다. 이는 implementation simplification이지 강도 collapse 허용이 아니다.
- CLI 외 user config, MCP 및 followup에 같은 vocabulary를 투영하는 범위와 순서. 최종 지원 표면은 downstream Scope/Behavior planning이 결정하되, 지원한다고 선언한 표면은 동일 truth boundary를 지켜야 한다.
- DOM 조작 방식은 radio click, nested menu, slider position 등 current evidence에 맞게 선택할 수 있다. 구현 메커니즘은 replaceable하다.

## Non-Core / Defer Candidates

- Plus 슬롯 3, 4, 5에 Pro entitlement를 추가하거나 우회하는 작업.
- API engine의 reasoning effort 체계 변경.
- GPT 외 모델 또는 Deep Research의 추론 강도 체계 변경.
- 슬롯 allocator, queue, origin metadata schema의 일반 재설계. 세 강도의 capability 차이가 실제로 발견될 때만 필요한 만큼 재검토한다.
- 모든 legacy Pro Standard/Extended 코드를 일괄 정리하는 작업. 현재 production truth를 방해하거나 새 의미와 충돌하는 부분만 후속 Scope에서 판단한다.
- 응답 품질이 각 강도에서 얼마나 좋아지는지 평가하는 benchmark. 이 제품 의미의 핵심은 강도별 품질 우열을 보증하는 것이 아니라 요청 강도를 정확히 적용·증명하는 것이다.
- 세 강도의 user-facing token spelling을 Product Thesis에서 고정하는 일. 현재 UI evidence와 호환성 판단 후 downstream owner가 정한다.

## Truth / Causal Invariants

- **요청 동일성**: 기록된 requested sublevel은 운영자가 현재 invocation에 명시한 값과 동일해야 한다.
- **선택 동일성**: resolved sublevel은 prompt 제출 직전 실제 Pro UI selected-state에서 관찰한 값이어야 하며 config, slot capability, 과거 turn 또는 agent 보고값으로 대체할 수 없다.
- **인과 순서**: capability 확인 → exact selection → positive readback → prompt 제출 순서가 유지되어야 한다.
- **세 값 구별성**: 서로 다른 두 Pro sublevel 요청이 동일한 canonical target/evidence로 합쳐지면 안 된다.
- **실패 정직성**: exact selected-state를 증명할 수 없으면 consultation 성공으로 제출·기록하지 않는다.
- **routing/selection 분리**: 같은 슬롯군에 배정되었다는 사실은 같은 reasoning 강도를 선택했다는 증거가 아니다.
- **model/reasoning 분리**: `6 Pro` 같은 reasoning-only label은 base-model picker identity를 대신하지 않으며, base-model 검증도 reasoning sublevel readback을 대신하지 않는다.
- **turn 귀속성**: followup과 retry의 evidence는 해당 turn/attempt에 귀속되어야 하며 이전 성공 evidence가 현재 선택을 대신하지 않는다.
- **권위 경계**: wrapper lifecycle readback은 슬롯·대화·실행을 증명하고, stock browser selection evidence는 실제 Pro 세부 강도를 증명한다. 한쪽의 성공만으로 전체 결과를 주장하지 않는다.

## Success Observation

동일한 Pro-capable managed 환경에서 운영자가 세 Pro 강도를 각각 명시한 세 개의 독립 invocation을 실행했을 때, 각 invocation이 다음을 모두 관찰 가능하게 제공하면 Core Utility가 성립한다.

- 입력/readback에 서로 다른 세 requested sublevel이 보존된다.
- prompt 제출 전에 현재 UI의 정확한 corresponding selected-state가 확인된다.
- resolved sublevel이 requested sublevel과 각각 일치한다.
- session metadata에서 turn/attempt와 함께 `verified: true` 및 정확한 requested/resolved sublevel을 구별해 읽을 수 있다.
- unavailable/ambiguous/mismatched control에서는 prompt가 제출되지 않고 명시적 실패가 남는다.
- explicit followup override도 부모 원 슬롯에서 동일한 선택·검증 경계를 다시 통과한다.

다음은 그럴듯하지만 실패한 결과다.

- CLI가 세 token을 받지만 모두 `reasoningIntent: "pro"`로 저장한다.
- 세 token 모두 top-level slider maximum만 선택한다.
- UI 선택은 달라도 metadata가 세 경우 모두 `resolvedLevel: "pro"`라고만 기록한다.
- wrapper가 Pro 슬롯 `(1, 2, 10)`을 골랐다는 이유만으로 정확한 sublevel 선택을 성공 처리한다.
- 이전 turn의 verified evidence 또는 현재 composer pill의 generic `Pro` label을 현재 sublevel 증거로 재사용한다.
- 요청한 강도가 없을 때 default, nearest 또는 최고 강도로 자동 제출한다.

## Open Product Meaning

None. 세 강도의 정확한 현재 UI label, 공개 token spelling, DOM control 방식, 지원 표면의 rollout 순서는 downstream evidence-backed Behavior/Scope 결정이다. 이들은 “세 강도를 각각 지정하고 실제 선택·증명한다”는 제품 결과를 바꾸지 않는다.
