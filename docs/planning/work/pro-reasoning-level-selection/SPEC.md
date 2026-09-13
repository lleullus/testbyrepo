# Specification: Oracle Browser Pro Model/Version Selection

Status: approved
Owner: user
Source-Increment: None

## Product Meaning Binding

Schema: iis-product-meaning/v2
Source: /home/user01/project/oracle/oracle-browser-slots/docs/planning/product-thesis/pro-reasoning-level-selection/THESIS-003.md
Fingerprint: sha256:90ec9b560e05eaada0052c5ab5214c4ccfa8c2c5f84b6d799a1b44f8880e041e

## Problem

Oracle Browser의 current Pro 경로는 Power와 model/version이라는 두 축을 사용하지만 최종 성공 판정이 사실상 `Latest`와 `6 Pro`에 고정돼 있다. 그 결과 운영자는 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`를 각각 Power=`Pro`와 결합해 요청·실행·증명할 수 없고, resumed followup에서는 explicit model/version choice가 적용되지 않을 수 있다.

## Desired Outcome

운영자는 Oracle Browser에서 `Latest`, `GPT-5.6 Sol`, `GPT-5.5` 중 정확히 하나와 Power=`Pro`를 명시해 managed slot `1`, `2`, `10`의 initial run 또는 supported same-origin followup을 실행한다. Prompt는 requested row, Pro Power, model identity continuity가 같은 turn/attempt에서 확인된 뒤에만 제출되며, 결과 evidence는 requested choice, actual resolution, Power, assigned slot과 conversation origin을 구별해 보여 준다.

## Requirements

- Pro model/version choice는 정확히 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`이고 Power intent `Pro`와 별도로 보존되어야 한다.
- 세 choice 모두 managed slot `1`, `2`, `10`의 initial run과 supported explicit followup에서 사용할 수 있어야 하며, 자동 배정의 기존 상대순서 `1 → 2 → 10`과 원 slot/profile/conversation 연속성을 유지해야 한다.
- Initial run과 explicit choice가 있는 followup은 requested exact row 하나와 Power=`Pro`를 prompt 제출 전에 현재 상태로 확인하고, Power 선택 전후 model/version identity가 유지됨을 확인해야 한다.
- `Latest`는 invocation 시점의 current latest Pro-capable track을 뜻하며, requested choice와 actual resolved model/version을 분리해 기록해야 한다.
- 결과 evidence는 같은 invocation/turn/attempt의 requested choice, checked/resolved model/version, resolved Power, verification status를 보존하고 Wrapper의 assigned slot/origin evidence와 구별 가능하게 연결해야 한다.
- Requested row unavailable, ambiguous checked state, wrong row, lower Power, model identity change, combined readback contradiction 또는 unsupported slot은 prompt 제출 전에 실패해야 하며 다른 row/current/nearest/Latest 또는 다른 slot으로 fallback하지 않아야 한다.
- Followup에서 model/version choice 또는 Power intent를 생략하면 current conversation state를 보존하되 생략된 값을 새 requested choice나 verified Pro 결과로 추정·기록하지 않아야 한다.

## Non-Goals

- ChatGPT picker UI 자체 복제·대체 또는 기존 외부 UI의 시각적 재설계.
- 슬롯 `3`, `4`, `5`의 capability 정책, 슬롯 `1`, `2`, `10`의 상대 우선순위 또는 cross-slot conversation migration 변경.
- 모델 응답 품질·속도 비교, API engine routing, Deep Research, image generation, attachment 또는 browser lifecycle 재설계.
- 실제 OpenAI internal model slug를 영구 public contract로 고정.
- 과거 investigation, Thesis, Spec 또는 Ticket history 삭제·재작성.

## Implementation Constraints

- Current ChatGPT model-picker와 Power control의 trusted/native interaction을 사용하고 exact checked-row 및 semantic Power readback을 얻어야 한다. 별도 picker를 복제하거나 selection을 추정하는 우회 경로를 만들지 않는다.
- Model/version evidence와 Power evidence는 별도 의미를 유지하면서 동일 turn/attempt의 성공 판정에서 결합되어야 한다. Stock browser evidence와 Wrapper slot/origin evidence의 권위를 하나의 불투명 boolean으로 대체하지 않는다.
- Closed composer display는 combined consistency signal로 사용할 수 있지만 `6 Pro` 같은 단일 문자열을 세 choice 전체의 단독 성공 조건으로 사용하지 않는다.
- 기존 managed-slot 식별, 단일 점유, 중복 방지, 자동 배정 및 followup 원점 규칙을 보존한다.
- Exact public flag spelling, legacy alias normalization, private data shape, source 경로, component 경계와 구현 순서는 Ticket delivery가 선택할 수 있다. 단, 선택된 public vocabulary는 세 choice와 Power 축을 손실 없이 표현해야 한다.

## Verification Expectations

- Outcome: Initial run에서 `Latest`, `GPT-5.6 Sol`, `GPT-5.5` 각각을 Power=`Pro`와 결합해 실행하고 requested choice와 actual resolution을 구별해 확인할 수 있다.
  Acceptance boundary: Oracle Browser CLI/managed-wrapper 실행과 actual ChatGPT model-picker·Power control 및 persisted Stock/Wrapper session evidence.
  Trigger or inspection target: 세 exact model/version choice 각각과 Power=`Pro`를 지정한 initial browser request 및 managed slot routing.
  Expected observable result: Assigned slot은 `1`, `2`, `10` 중 하나이고 requested row 하나가 checked이며 Power가 Pro이고 model identity가 유지된 뒤에만 prompt가 제출되며, requested/resolved model·Power·slot evidence가 같은 invocation/turn에 귀속된다.
  Authoritative readback: Live checked model/version row, Power slider semantic state, non-contradictory closed/equivalent display, Stock `modelSelection`·`reasoningSelection`, Wrapper assigned-slot/session metadata와 process result.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | Oracle Browser CLI와 authenticated managed slot `1`, `2`, `10`의 ChatGPT browser targets 및 session metadata.
  External condition: At least one eligible managed slot is authenticated, unoccupied, and exposes the current three model/version rows and Pro Power control; slot-wide routing support is also inspectable at the canonical CLI/source boundary.
  UI rendered state and interaction readback: Existing desktop ChatGPT picker에서 exact row checked state와 Power maximum semantic state를 읽으며, new custom UI·mobile layout·asset·motion은 없다.
- Outcome: Explicit followup은 같은 slot/profile/conversation에서 requested choice를 유지하거나 바꾸고 새 turn의 row+Power evidence로만 성공하며, omitted choice는 추정되지 않는다.
  Acceptance boundary: Managed wrapper followup과 resumed ChatGPT conversation의 current picker state, turn evidence 및 parent-origin metadata.
  Trigger or inspection target: Slot `1`, `2`, `10`에서 생성된 parent browser session에 explicit supported choice+Pro followup, choice 변경 followup, 그리고 model/version 또는 Power를 생략한 followup.
  Expected observable result: Conversation origin은 유지되고 explicit choice는 새 turn에서 exact row와 Pro로 재검증되며 이전 turn evidence가 재사용되지 않는다. 생략한 값은 current state를 보존하되 requested/verified 값으로 새로 기록되지 않는다.
  Authoritative readback: Parent와 child의 slot/profile/conversation origin, current checked row와 Power state, turn/attempt-indexed Stock selection evidence 및 submitted user turn.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | managed wrapper followup, recoverable ChatGPT conversation, browser picker와 session evidence.
  External condition: A successful eligible parent browser session and authenticated original managed slot remain available for the followup observation.
  UI rendered state and interaction readback: Resumed conversation의 existing picker에서 explicit requested row와 Pro state를 새 turn에 확인하고, unavailable/ambiguous state는 submit 전 실패로 관찰한다.
- Outcome: Unsupported, unavailable, ambiguous 또는 mismatched choice/Power/slot 상태가 silent fallback이나 prompt submission 없이 귀속 가능한 실패로 끝난다.
  Acceptance boundary: Oracle Browser CLI/managed wrapper rejection와 pre-submit browser selection boundary.
  Trigger or inspection target: Slot `3`, `4`, `5` explicit request, unavailable requested row, wrong/multiple/no checked row, lower Power, model identity drift 및 contradictory combined display.
  Expected observable result: Request가 prompt 제출 및 cross-slot fallback 전에 실패하고 원인별 non-success evidence를 남기며 다른 row나 Latest를 성공으로 기록하지 않는다.
  Authoritative readback: Wrapper rejection/process result, Stock selection failure evidence와 turn/attempt attribution, ChatGPT conversation의 submitted-user-turn 부재.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | wrapper compatibility/rejection boundary와 Stock browser pre-submit evidence boundary.
  External condition: None for canonical unsupported-slot and deterministic mismatch boundaries; live option availability cases require the current authenticated picker.
  Absence terminal condition: 해당 invocation/turn의 requested selection failure 뒤 새 user prompt turn이 conversation에 존재하지 않는다.
  UI rendered state and interaction readback: Existing picker의 checked row, Power semantic state와 unavailable/ambiguous/mismatch 상태가 error evidence와 일치하고 fallback selection이 성공으로 표시되지 않는다.

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성
- docs/planning/behavior/contexts/pro-model-version-selection.md | Scope: Oracle Browser initial run과 explicit followup에서 model/version choice와 Power=Pro를 결합해 선택·검증·귀속하는 행동

## UI / UX

This Spec itself is the scoped UI authority for this bounded rendered contract. Existing ChatGPT picker interaction is the exact rendered scope exercised by this work.

- 기존 ChatGPT model/version rows `Latest`, `GPT-5.6 Sol`, `GPT-5.5`와 Power slider의 표시·레이아웃·copy를 그대로 사용한다. 새 Oracle UI나 picker를 만들지 않는다.
- Exact requested row의 semantic checked state와 Power control의 `Pro` maximum state를 primary rendered readback으로 사용한다. Closed composer display는 이 둘과 모순이 없는 consistency signal이다.
- Picker mount 또는 state 반영은 bounded하게 기다리고, requested row/control이 unavailable·ambiguous이거나 상태가 모순되면 prompt를 제출하지 않고 기존 Oracle 오류/evidence surface에 실패를 표시한다.
- Existing native mouse/keyboard-compatible control semantics와 accessibility state를 보존한다. Synthetic-only state mutation, custom mobile surface, new assets 또는 motion은 도입하지 않는다.
- Success presentation은 기존 prompt/session result surface와 structured evidence를 사용하며, selected row와 Power를 실제보다 강하게 보이게 하는 새 badge나 inferred label을 추가하지 않는다.

## Open Questions

None
