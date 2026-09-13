# TICKET-001: Three Exact Pro Model/Version Choices

Status: done
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/oracle
Worker:
UI: yes

## Goal

Oracle Browser 운영자가 `Latest`, `GPT-5.6 Sol`, `GPT-5.5` 중 하나와 Power=`Pro`를 명시하면 managed slot `1`, `2`, `10`의 initial run과 supported same-origin followup에서 exact row·Power·identity가 prompt 제출 전에 검증되고, requested/resolved model·Power·slot/origin evidence를 구별해 확인하며 mismatch는 fallback 없이 실패하게 한다.

## Acceptance Criteria

- Pro model/version choice는 정확히 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`로 표현되고 Power intent `Pro`와 별도로 보존되며, 선택된 public request vocabulary가 두 축을 손실 없이 전달한다.
- Initial run은 requested exact row 하나의 checked state, Power=`Pro`, Power 선택 전후 model/version identity continuity를 같은 invocation/turn/attempt에서 확인한 뒤에만 prompt를 제출한다.
- `Latest` 요청은 invocation 시점의 current latest Pro-capable track으로 resolve되고 requested choice `Latest`와 actual resolved model/version을 분리해 evidence에 보존하며 current GPT version을 영구 Latest 의미로 고정하지 않는다.
- 성공 및 실패 evidence는 requested choice, checked/resolved model/version, resolved Power, verification status, turn/attempt를 Stock browser 경계에 귀속하고 assigned slot과 original conversation origin은 Wrapper 경계에 귀속해 함께 판정할 수 있게 한다.
- Supported explicit followup은 parent와 같은 slot/profile/conversation에서 requested choice를 유지하거나 변경하고 새 turn의 exact row와 Power=`Pro`를 재검증하며 이전 turn evidence를 재사용하지 않는다. Model/version choice 또는 Power intent를 생략하면 current conversation state를 보존하되 생략된 값을 새 requested choice나 verified Pro result로 추정·기록하지 않는다.
- Requested row unavailable, multiple/no checked row, wrong row, lower Power, model identity drift, contradictory combined display 또는 unsupported slot은 prompt 제출과 cross-row/cross-slot fallback 전에 귀속 가능한 실패로 끝나고 다른 row/current/nearest/Latest를 성공으로 기록하지 않는다.
- 세 choice 모두 managed slot `1`, `2`, `10`에서 허용되고 자동 배정 상대순서 `1 → 2 → 10`을 유지하며, explicit slot `3`, `4`, `5`는 claim과 prompt 제출 전에 거절되고 followup은 다른 slot으로 migration하지 않는다.
- Existing ChatGPT picker의 labels/layout과 native mouse·keyboard-compatible accessibility semantics를 보존하고, exact checked row와 Power maximum semantic state를 primary rendered readback으로 사용하며, bounded wait 뒤 unavailable·ambiguous 상태는 기존 오류/evidence surface에서 실패로 관찰된다.

## Scope

Oracle Browser의 model/version request projection, current ChatGPT model row 및 Power selection/verification, initial·resumed followup submission gate, Stock session evidence와 managed-wrapper model/reasoning slot eligibility·assignment·origin readback. Existing ChatGPT picker interaction은 bounded rendered contract로 직접 관찰하지만 외부 UI 자체는 변경하지 않는다.

## Non-Goals

- ChatGPT picker UI 복제·대체 또는 시각적 재설계
- 슬롯 `3`, `4`, `5`의 일반 capability 정책, 슬롯 `1`, `2`, `10`의 상대 우선순위 또는 cross-slot conversation migration 변경
- 모델 품질·속도 비교, API engine routing, Deep Research, image generation, attachment 또는 browser lifecycle 재설계
- 실제 OpenAI internal model slug의 영구 public contract화
- 과거 planning artifact 삭제·재작성

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1, 2, 3, 4, 7, 8
  Behavior authority ordinals: 1, 2
  Initial state: Authenticated and unoccupied managed slot `1`, `2`, or `10` exposes the current `Latest`, `GPT-5.6 Sol`, `GPT-5.5` rows and Pro Power control; no prompt for this invocation has been submitted.
  Trigger or inspection target: Each exact model/version choice with Power=`Pro` through an initial Oracle Browser request and managed-slot routing.
  Acceptance boundary: Oracle Browser CLI/managed-wrapper process, actual ChatGPT picker/Power control, submitted conversation turn, and persisted Stock/Wrapper session evidence.
  Expected observable result: The assigned eligible slot has only the requested row checked and Power at Pro with continuous model identity before one prompt submission; requested/resolved model, Power, slot and turn/attempt evidence agree without collapsing their authorities.
  Authoritative readback: Live checked row, Power slider semantic state, non-contradictory closed/equivalent display, Stock `modelSelection` and `reasoningSelection`, Wrapper assigned-slot/session metadata, submitted user turn, and process result.
  Decision boundary: All three requested choices independently reach the exact row+Pro pre-submit gate and attributable evidence on an eligible slot, or any choice exhibits mismatch, inferred identity, premature submission, or missing attribution.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | Oracle Browser CLI와 authenticated managed slot `1`, `2`, `10`의 ChatGPT browser targets 및 session metadata.
  External condition: At least one eligible managed slot is authenticated, unoccupied, and exposes the current three model/version rows and Pro Power control; slot-wide routing support is also inspectable at the canonical CLI/source boundary.
  UI rendered state and interaction readback: Existing desktop ChatGPT picker에서 exact row checked state와 Power maximum semantic state를 읽으며, new custom UI·mobile layout·asset·motion은 없다.
- Parent outcome ordinal: 2
  AC ordinals: 4, 5, 7, 8
  Behavior authority ordinals: 1, 2
  Initial state: A successful eligible parent browser session has a recoverable conversation URL, persisted slot/origin and model identity, and its original managed slot remains authenticated and available.
  Trigger or inspection target: Explicit same-choice and changed-choice Pro followups plus a followup omitting model/version or Power intent.
  Acceptance boundary: Managed wrapper followup, resumed ChatGPT conversation picker/submission behavior, parent-child origin metadata, and turn-indexed Stock evidence.
  Expected observable result: Explicit choice stays on the parent origin and is freshly verified at the new turn before submission; omitted values preserve current state without creating inferred requested/verified evidence; no prior-turn evidence or cross-slot migration is used.
  Authoritative readback: Parent and followup slot/profile/conversation identity, current checked row and Power state, turn/attempt-indexed selection evidence, submitted user turn, and Wrapper process/session result.
  Decision boundary: Explicit followup evidence belongs to the new turn and same origin while omission remains non-assertive, or any stale evidence reuse, skipped explicit selection, fabricated omitted intent, or migration contradicts the contract.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | managed wrapper followup, recoverable ChatGPT conversation, browser picker와 session evidence.
  External condition: A successful eligible parent browser session and authenticated original managed slot remain available for the followup observation.
  UI rendered state and interaction readback: Resumed conversation의 existing picker에서 explicit requested row와 Pro state를 새 turn에 확인하고, unavailable/ambiguous state는 submit 전 실패로 관찰한다.
- Parent outcome ordinal: 3
  AC ordinals: 1, 2, 4, 6, 7, 8
  Behavior authority ordinals: 1, 2
  Initial state: A request targets an unsupported slot or a controlled current picker state where requested row, checked-state uniqueness, Power, model continuity, or combined display cannot satisfy the requested conjunction.
  Trigger or inspection target: Explicit slot `3`, `4`, or `5`; unavailable row; wrong/multiple/no checked row; lower Power; model identity drift; or contradictory combined display.
  Acceptance boundary: Wrapper compatibility/claim boundary and Stock browser pre-submit selection boundary.
  Expected observable result: The invocation fails before prompt submission and before cross-row/cross-slot fallback, preserving attributable non-success evidence without reporting another choice as selected.
  Authoritative readback: Wrapper rejection/process result, Stock selection failure evidence with turn/attempt attribution, live picker state when applicable, and absence of a submitted user turn for the failed invocation.
  Decision boundary: The exact unsupported or mismatched state produces no submitted prompt and no successful fallback evidence, or any prompt/fallback/success assertion contradicts the contract.
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | wrapper compatibility/rejection boundary와 Stock browser pre-submit evidence boundary.
  External condition: None for canonical unsupported-slot and deterministic mismatch boundaries; live option availability cases require the current authenticated picker.
  Absence terminal condition: 해당 invocation/turn의 requested selection failure 뒤 새 user prompt turn이 conversation에 존재하지 않는다.
  UI rendered state and interaction readback: Existing picker의 checked row, Power semantic state와 unavailable/ambiguous/mismatch 상태가 error evidence와 일치하고 fallback selection이 성공으로 표시되지 않는다.

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성
- docs/planning/behavior/contexts/pro-model-version-selection.md | Scope: Oracle Browser initial run과 explicit followup에서 model/version choice와 Power=Pro를 결합해 선택·검증·귀속하는 행동

## References

- ../SPEC.md
