# Oracle Browser Power=Pro 3모델 선택 Product Thesis

Result: CALIBRATED

## Source Authority

- 최신 명시적 사용자 요구: Oracle Browser의 Pro에서 지원되는 세 선택을 각각 지정하여 선택할 수 있어야 한다.
- 최신 명시적 managed slot 경계: 이 기능은 슬롯 `1`, `2`, `10`에 적용한다.
- 사용자 교정: 요구된 세 선택은 `High`, `Extra High`, `Pro`가 아니다.
- Current live product evidence: Power=`Pro`일 때 advanced model/version view에 정확히 `Latest`, `GPT-5.6 Sol`, `GPT-5.5` 세 radio row가 있다.
- Current runtime resolution: checked `Latest` + Power=`Pro`는 현재 `gpt-6-pro` 및 closed display `6 Pro`로 resolve된다.
- Current investigation: `/home/user01/project/oracle/oracle-browser-slots/docs/investigation/pro-reasoning-level-selection/INV-003.md` (`VALID`).
- Superseded history: `INV-001`, `INV-002`, `THESIS-001`, `THESIS-002`는 immutable history로 보존하지만 현재 제품 의미의 권위가 아니다. 특히 `THESIS-002`의 High/Extra High/Pro 선택군은 잘못된 축이다.
- Current task boundary: 재사전조사와 Product Thesis까지다. Scope Shaping, Behavior Design, Spec, Ticket, 구현 및 verification verdict는 포함하지 않는다.

## Reason to Exist

현재 ChatGPT Pro picker는 하나의 값만 고르는 단순 목록이 아니다. 사용자는 **Power 축**과 **model/version 축**을 함께 선택한다.

```text
Power axis:
Instant | Medium | High | Extra High | Pro

Model/version axis:
Latest | GPT-5.6 Sol | GPT-5.5
```

사용자가 말한 Pro의 세 선택은 Power를 `Pro`에 둔 상태에서 model/version 축의 세 행 중 하나를 고르는 것이다. 현재 `Latest`를 선택하면 GPT-6 Pro가 되지만, `Latest`는 “GPT-6”이라는 영구 고정 이름이 아니라 그 시점의 최신 Pro model track이다. 다른 두 선택은 이전 Pro families를 명시적으로 유지할 수 있게 한다.

Oracle Browser는 현재 세 선택을 완전한 하나의 제품 capability로 제공하지 못한다. Stock config와 model selector에는 세 model family를 겨냥하는 구성요소가 있고 Wrapper도 canonical Pro 조합을 슬롯 1,2,10으로 보낼 수 있다. 그러나 최종 Pro approval은 closed pill `6 Pro`만 인정한다. 이 검증은 현재 Latest+Pro에만 맞고 explicit GPT-5.6 Sol+Pro 또는 GPT-5.5+Pro를 같은 수준으로 선택·증명하지 못한다. User-reported current state인 “세 개 중 하나만 고를 수 있음”과 일치하는 구조적 결손이다.

이 기능이 존재해야 하는 이유는 단순히 메뉴에 세 label이 보이게 하는 것이 아니다. 운영자가 원하는 Pro model/version을 **의도적으로 고르고**, managed slot에서 **실제로 그 row와 Pro Power가 함께 적용됐음을 확인한 뒤**, 그 조합으로 상담을 실행할 수 있게 하는 것이다.

## Core Utility

운영자는 Oracle Browser 상담에서 다음 Pro choices 중 정확히 하나를 명시할 수 있다.

1. `Latest`
2. `GPT-5.6 Sol`
3. `GPT-5.5`

선택된 상담은 슬롯 `1`, `2`, `10` 중 하나에서 실행되고, prompt 제출 전에 다음 conjunction이 확인된다.

```text
requested model/version choice
= checked model/version row
AND Power = Pro
AND model identity remained continuous
```

운영자는 결과 evidence에서 자신이 요청한 choice, 실제 resolved model/version display, Power=`Pro`, assigned managed slot을 확인할 수 있다. `Latest`는 실행 시점의 latest Pro model로 resolve되며, 그 실제 resolution도 기록된다.

## Core Completion Loop

1. **의도 입력**
   - 운영자는 `Latest`, `GPT-5.6 Sol`, `GPT-5.5` 중 하나를 명시한다.
   - 선택은 model/version intent다. `High`, `Extra High`, `Pro` 중 하나를 고르는 reasoning-level intent와 혼합하지 않는다.
   - Power intent는 별도로 `Pro`로 고정된다.

2. **managed eligibility 판정**
   - Wrapper는 세 Pro choice 모두에 대해 exact candidate slots `(1,2,10)`을 산출한다.
   - Auto submit은 기존 상대순서 `1 → 2 → 10`을 유지한다.
   - Explicit run은 이 집합 밖의 슬롯을 claim이나 child 실행 전에 거절한다.
   - Followup은 부모 session의 원 슬롯이 1,2,10인지 확인하고 다른 슬롯으로 migration하지 않는다.

3. **Stock request projection**
   - User-facing choice는 Stock Oracle이 손실 없이 구별할 model target으로 변환된다.
   - `Latest`는 dynamic latest row를 의미한다. 현재 내부 canonical route가 `gpt-6-pro → Latest`더라도 제품 의미를 영구 GPT-6 alias로 축소하지 않는다.
   - `GPT-5.6 Sol`과 `GPT-5.5`는 각각 해당 visible row를 목표로 한다.
   - 세 요청 모두 별도 Power intent `pro`를 동반한다.

4. **model/version row 선택**
   - Browser controller는 current picker의 advanced model/version view를 연다.
   - 요청한 exact row가 이미 checked이면 그 상태를 읽는다.
   - 아니라면 요청 row만 선택한다.
   - Nearest version, 현재 checked row 또는 Latest로 silent fallback하지 않는다.

5. **Power=Pro 선택**
   - Browser controller는 같은 picker의 Power control에서 maximum `Pro` position을 선택한다.
   - Current UI에서는 slider min `0`, max `4`, Pro `aria-valuenow=4`, announcement `Pro, 5 of 5.`다.
   - Power 선택 과정에서 model/version row가 바뀌지 않아야 한다.

6. **결합된 제출 전 검증**
   - Exact requested row가 checked인지 확인한다.
   - Power가 `Pro`인지 확인한다.
   - Model-selection 전후의 model identity continuity를 확인한다.
   - Closed composer display 또는 equivalent semantic readback이 선택 row와 Pro의 결합을 나타내는지 확인한다.
   - `Latest`는 current resolution을 별도로 캡처한다. 현재는 `gpt-6-pro` / `6 Pro`다.
   - 어느 한 신호라도 unavailable, ambiguous, mismatch 또는 changed이면 prompt를 제출하지 않는다.

7. **prompt 제출과 session evidence**
   - 위 검증이 성공한 뒤에만 prompt를 제출한다.
   - Stock evidence는 requested model choice, resolved model/version, requested reasoning=`pro`, resolved Power=`pro`, verification status, turn/attempt attribution을 보존한다.
   - Wrapper evidence는 assigned slot과 original conversation origin을 보존한다.
   - 두 evidence를 함께 보아야 전체 제품 결과가 성립한다.

8. **운영자 결과와 반복 사용**
   - 운영자는 어떤 Pro choice가 실제 실행됐는지 확인한다.
   - 새 initial request뿐 아니라 explicit followup에서도 지원되는 choice를 다시 명시할 수 있다.
   - Followup은 같은 slot/profile/conversation을 유지하면서 새 turn에 대한 row+Power 검증을 다시 수행한다.

## Core Behavior Concretization

### Choice 1 — Latest

- Visible row: `Latest`
- Current React value: `latest`
- Current selected display version: `6`
- Current resolved model slug: `gpt-6-pro`
- Current closed display with Pro: `6 Pro`
- Durable meaning: invocation 시점의 latest Pro-capable model track
- Forbidden collapse: `Latest == GPT-6 forever`

### Choice 2 — GPT-5.6 Sol

- Visible row: `GPT-5.6 Sol`
- Current React value: `5.6`
- Product result: 이 exact row가 checked이고 Power가 `Pro`인 조합
- Existing source projection candidate: `gpt-5.6-sol` model target + `reasoningIntent=pro`
- Current gap: final Pro approval이 `6 Pro`에 고정되어 이 explicit combination을 semantic하게 승인하지 못한다.

### Choice 3 — GPT-5.5

- Visible row: `GPT-5.5`
- Current React value: `5.5`
- Product result: 이 exact row가 checked이고 Power가 `Pro`인 조합
- Existing source projection candidates are asymmetric: `gpt-5.5-pro` is projected through legacy `Thinking 5.5`, while current UI exposes `GPT-5.5` as the version row and Pro as the separate Power choice.
- Current gap: current visible row, model request, Pro selection and final evidence가 하나의 positive path로 정렬되어 있지 않다.

### Two-axis model

```text
requested outcome = model/version row × Power

Latest       × Pro
GPT-5.6 Sol  × Pro
GPT-5.5      × Pro
```

세 결과의 Power 값은 모두 같지만 model/version identity가 다르다. 반대로 row가 맞아도 Power가 Medium/High/Extra High이면 요청한 Pro result가 아니다.

### Initial run

- 세 choice 중 하나를 explicit하게 받는다.
- Slots 1,2,10 중 하나를 배정한다.
- Exact row를 선택한 뒤 Power=Pro를 선택·검증한다.
- 결합 evidence가 없으면 submit하지 않는다.

### Explicit-slot run

- 슬롯 1,2,10만 허용한다.
- 슬롯 3,4,5 또는 unmanaged slot은 세 choice 모두 fail closed한다.
- 다른 slot으로 자동 fallback하지 않는다.

### Followup

- Parent가 슬롯 1,2,10에서 생성된 경우 같은 origin에서 choice를 명시적으로 유지하거나 변경할 수 있다.
- Choice를 생략한 followup의 default/상속 의미는 downstream Behavior owner가 existing contract와 함께 구체화하되, 생략을 임의의 세 choice로 거짓 기록하면 안 된다.
- Explicit choice가 있으면 current turn에 대해 exact row+Power verification을 새로 수행한다.
- Parent slot이 target set 밖이면 conversation migration으로 우회하지 않는다.

### Failure behavior

다음은 prompt-before-submit failure다.

- 요청 choice가 세 값 중 하나로 해석되지 않음
- Requested row가 현재 제공되지 않음
- 둘 이상의 row가 checked되거나 checked state가 없음
- Requested row 대신 다른 row가 selected됨
- Power control이 없거나 ambiguous함
- Power가 Pro가 아니거나 maximum state가 확인되지 않음
- Row 선택 후 Power 선택 과정에서 model identity가 바뀜
- Closed/equivalent readback이 requested row+Pro와 모순됨
- Wrapper assigned slot이 1,2,10 밖임
- Followup origin continuity가 깨짐

## Required Outcomes / Means

### Required Outcomes

- 운영자는 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`를 각각 Pro choice로 명시할 수 있다.
- 세 choice는 모두 slots `1`, `2`, `10`에서 initial run과 supported followup 경로를 제공한다.
- 각 choice는 exact visible model/version row와 Power=`Pro`의 conjunction으로 실행된다.
- Requested choice, resolved model/version, resolved Power, assigned slot을 결과에서 구별해 확인할 수 있다.
- `Latest`는 dynamic semantic을 유지하며 현재 실제 resolution을 기록한다.
- 다른 row, lower Power 또는 Latest로 silent fallback하지 않는다.

### Required Means

- Model/version intent와 Power intent를 별도 값으로 보존한다.
- Current visible rows `Latest`, `GPT-5.6 Sol`, `GPT-5.5`를 exact-match 가능한 selection surface로 취급한다.
- Existing trusted/native model-picker 및 Power interaction을 사용한다.
- Model row와 Power를 prompt 제출 전에 결합 검증한다.
- `6 Pro`에 고정된 final approval을 selected version에 종속된 semantic verification으로 교체한다.
- Wrapper run/submit/followup에서 exact slot set `(1,2,10)`과 origin continuity를 유지한다.
- Stock browser evidence와 Wrapper lifecycle evidence를 함께 사용하되 권위를 합쳐 하나의 불투명 boolean으로 만들지 않는다.

### Derived Necessities

- 세 choice가 같은 Power position을 공유하므로 reasoning evidence만으로 어느 choice인지 증명할 수 없다.
- 세 choice가 같은 slot set을 공유하므로 slot assignment만으로 어느 choice인지 증명할 수 없다.
- 따라서 exact model row evidence와 Pro Power evidence의 conjunction이 불가피하다.
- `Latest`를 영구 GPT-6 token으로만 노출하면 future Latest가 바뀌는 순간 제품 약속이 거짓이 된다. Dynamic intent와 observed resolution을 분리해야 한다.

## Candidate / Supporting Means

- Existing `--model`과 `--browser-thinking-time pro` 조합을 정렬해 세 choice를 표현할 수 있다. 새 public flag는 필수로 확정되지 않았다.
- User-facing choice enum을 `latest | gpt-5.6-sol | gpt-5.5`로 두고 내부 canonical model token으로 projection할 수 있다.
- 기존 `gpt-6-pro` token을 current Latest route의 내부 mechanism으로 재사용할 수 있다. 다만 user-facing Latest semantic까지 고정 GPT-6로 만들면 안 된다.
- GPT-5.5 legacy `Thinking 5.5` matcher를 current advanced row `GPT-5.5`와 정렬할 수 있다.
- Closed pill exact text 하나보다 checked row + slider semantics를 primary proof로 삼고 closed pill은 combined consistency evidence로 사용할 수 있다.
- Session `modelSelection`과 `reasoningSelection`을 유지하면서 둘을 같은 turn/attempt에 묶는 aggregate success condition을 둘 수 있다.
- Existing wrapper capability matrix는 재사용하되 세 named choices와 initial/run/followup observable scenarios로 projection해야 한다.
- CLI, config, MCP, Oracle Browser skill에서 동일 choice vocabulary를 노출하는 범위는 downstream Scope Shaping에서 결정한다.

## Non-Core / Defer Candidates

- `High`, `Extra High`, `Pro`를 세 requested choices로 다시 정의하는 것
- Nested `ProSublevel` domain 또는 secondary Pro slider 도입
- ChatGPT picker UI 자체를 복제하거나 대체하는 것
- Slots 3,4,5의 일반 capability 정책 변경
- Slots 1,2,10의 상대 우선순위 변경
- Conversation을 다른 slot/profile로 migration하는 기능
- GPT-5.6 Sol 및 GPT-5.5 Pro 응답의 품질·속도 비교
- API engine model routing 변경
- Deep Research, image generation, attachments 또는 browser lifecycle 재설계
- Literal `--model latest` 지원을 필수 수단으로 확정하는 것
- 과거 planning artifact 삭제
- 실제 OpenAI internal model slug를 영구 public contract로 만드는 것

## Truth / Causal Invariants

- **정확한 세 선택**: 제품 choice는 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`다.
- **축 분리**: 이 세 값은 model/version axis이고 `Pro`는 Power axis다.
- **결합 결과**: 성공은 requested row checked AND Power=Pro다.
- **Latest dynamicity**: Latest는 current latest row를 뜻하고 resolved model은 observation이다. 현재 GPT-6 Pro라는 사실을 영구 계약으로 만들지 않는다.
- **Exact selection**: 요청하지 않은 row, nearest version, current row 또는 Latest로 fallback하지 않는다.
- **Exact slots**: initial managed candidates는 정확히 `(1,2,10)`이다.
- **Ordering**: automatic assignment의 상대순서는 `1 → 2 → 10`이다.
- **Pre-submit gate**: row와 Power의 positive evidence가 모두 있기 전에는 prompt를 제출하지 않는다.
- **Model continuity**: Power 선택 전후 model/version identity가 유지돼야 한다.
- **No single-string authority**: `6 Pro` 같은 한 current display string만으로 세 choice 전체를 판정하지 않는다.
- **Current UI authority**: visible option availability와 checked/Power state는 current DOM이 권위다.
- **Evidence attribution**: model, Power, turn, attempt, managed slot을 현재 invocation에 귀속한다.
- **Authority separation**: Stock은 UI selection을, Wrapper는 slot/origin을 증명한다.
- **Followup continuity**: explicit followup은 parent slot/profile/conversation을 유지한다.
- **Failure honesty**: unsupported, unavailable, ambiguous, mismatch를 성공 또는 default로 바꾸지 않는다.

## Success Observation

### Scenario A — Latest Pro

운영자가 `Latest`를 요청하면:

- Assigned slot은 1,2,10 중 하나다.
- Advanced view의 `Latest` row가 checked다.
- Power는 `Pro, 5 of 5.`다.
- Current resolved model/version이 캡처된다.
- 현재 배포에서는 `gpt-6-pro` / `6 Pro`가 관찰된다.
- Requested choice `Latest`, resolved current model, Power `Pro`, verified status가 함께 남는다.

### Scenario B — GPT-5.6 Sol Pro

운영자가 `GPT-5.6 Sol`을 요청하면:

- Assigned slot은 1,2,10 중 하나다.
- `GPT-5.6 Sol` row가 checked다.
- `Latest`와 `GPT-5.5` row는 unchecked다.
- Power는 `Pro` maximum이다.
- Closed/equivalent identity가 selected 5.6 track과 Pro를 모순 없이 나타낸다.
- `6 Pro`만을 요구해 거짓 실패하거나 Latest로 되돌아가지 않는다.

### Scenario C — GPT-5.5 Pro

운영자가 `GPT-5.5`를 요청하면:

- Assigned slot은 1,2,10 중 하나다.
- `GPT-5.5` row가 checked다.
- 다른 두 row는 unchecked다.
- Power는 `Pro` maximum이다.
- Legacy `Thinking 5.5` target이 current row와 정확히 연결되거나 current vocabulary로 교체된다.
- Requested/resolved evidence가 GPT-5.5 Pro outcome을 구별한다.

### Scenario D — Followup

동일한 slot 1,2,10 conversation에서 explicit choice를 바꾸면:

- 같은 slot/profile/conversation을 유지한다.
- 새 requested row가 checked된다.
- Power=Pro가 다시 확인된다.
- 이전 turn evidence를 재사용하지 않는다.
- 새 turn의 requested/resolved model과 Power가 기록된다.

### Scenario E — Rejection

- Slot 3,4,5를 explicit하게 지정하면 claim 및 prompt 전에 거절한다.
- Requested row가 unavailable이면 다른 row로 fallback하지 않는다.
- Row는 맞지만 Power가 lower level이면 submit하지 않는다.
- Power는 Pro지만 row가 다르면 submit하지 않는다.
- Combined identity가 ambiguous하면 submit하지 않는다.

### 거짓 성공의 반례

다음은 제품 결과가 아니다.

- High/Extra High/Pro를 세 선택으로 노출한다.
- 세 label을 help에만 추가하고 실제 row는 Latest 하나만 선택한다.
- Wrapper가 `(1,2,10)`을 반환했다는 이유로 browser 성공을 선언한다.
- Power=Pro만 확인하고 checked model row를 무시한다.
- Requested row만 확인하고 실제 Power가 High/Extra High인 상태로 제출한다.
- GPT-5.6 Sol 또는 GPT-5.5 요청 뒤 final verification 때문에 Latest로 되돌아간다.
- 모든 성공 metadata를 generic `Pro`로 기록해 세 choice를 구별할 수 없다.
- Latest를 GPT-6으로 영구 고정해 ChatGPT의 future Latest 변경을 놓친다.
- Initial run만 지원하고 explicit followup에서는 choice를 보존·변경할 수 없다.

## Counterexample Gates

1. 세 choice 이름을 제공해도 exact requested row와 Power=Pro를 함께 증명하지 못하면 Core Utility가 없는가? **예.** 사용자가 고른 최종 Pro model을 알 수 없다.
2. Core Utility 문장이 형식상 참이어도 `Latest`를 영구 GPT-6으로 고정하면 causal loop가 깨지는가? **예.** Latest의 지속 가능한 의미가 사라진다.
3. 제품이 성공을 표시해도 model row 또는 Power readback 중 하나가 거짓일 수 있는가? **예.** 두 축과 wrapper origin의 독립 evidence가 모두 필요하다.

Success Observation과 Truth Invariants가 세 반례를 차단하므로 Product Thesis는 calibrated다.

## Open Product Meaning

None. 사용자는 세 choice를 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`로 교정했고 적용 slots를 `1`, `2`, `10`으로 확정했다. Exact public flag spelling, legacy alias 처리, closed-pill matcher 구현, config/MCP/skill projection 범위 및 scenario 분할은 downstream planning과 implementation 소유이며 Core Utility를 변경하지 않는다.
