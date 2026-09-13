# Adaptive Planning Mandate

Mode: IIS Adaptive Planning
Status: active
Revision: 1
Owner: user
Project-Root: /home/user01/project/oracle/oracle-browser-slots
Applies-To: pro-reasoning-level-selection

## Desired Product Outcome

Oracle Browser 운영자가 Power=`Pro`를 유지하면서 `Latest`, `GPT-5.6 Sol`, `GPT-5.5` 중 정확히 하나를 명시하고, managed slot `1`, `2`, `10`의 initial run과 supported followup에서 요청한 model/version row와 Pro Power가 함께 적용·검증된 상담을 실행하며 그 선택과 실제 resolution, Power, slot/origin을 귀속 가능한 evidence로 확인한다.

## Why / User Value

현재 Latest+Pro에 사실상 고정된 성공 경로를 세 개의 명시적 Pro model/version choice로 완성해, 운영자가 의도한 모델 track과 실제 실행된 track이 어긋난 상담을 성공으로 오인하지 않게 한다.

## Decision Priorities

1. 요청 choice, checked model/version row, Power=`Pro`, model identity continuity가 같은 turn/attempt에 결합된 진실한 성공 판정.
2. Stock Oracle의 native model-picker/Power 제어권과 Wrapper의 slot/origin 권위 분리 및 보존.
3. `Latest`의 동적 의미, exact selection, fail-closed 및 same-origin followup 불변식 보존.
4. 기존 public surface와 구현을 가능한 한 재사용하는 최소·직접적 설계.

## Hard Constraints

- 제품 choice는 정확히 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`이며 `High`, `Extra High`, `Pro`라는 reasoning-level 선택군으로 바꾸지 않는다.
- Power intent는 model/version intent와 분리된 `Pro`다.
- 적용 managed slot 집합과 자동 배정 상대순서는 정확히 `(1,2,10)` 및 `1 → 2 → 10`이다.
- Exact row와 Pro의 positive evidence가 모두 확인되기 전 prompt를 제출하지 않는다.
- 요청하지 않은 row, nearest version, current row 또는 Latest로 silent fallback하지 않는다.
- Followup은 원 slot/profile/conversation을 유지하며 다른 slot으로 migration하지 않는다.
- Stock browser evidence와 Wrapper lifecycle evidence의 권위를 하나의 불투명 boolean으로 합치지 않는다.
- 사용자 지정 전달 역할은 Ready Ticket Plan=Outer Main 직접, Plan Review=DeepSeek V4.1 Flash Max, Implementation Worker=Luna Max, Final Verifier=Luna Max, Coverage=Luna Max로 유지한다.

## Non-Goals

- ChatGPT picker UI 자체 복제 또는 대체.
- 슬롯 `3`, `4`, `5`의 일반 capability 정책이나 슬롯 `1`, `2`, `10`의 상대 우선순위 변경.
- Conversation의 다른 slot/profile migration.
- 모델 응답 품질·속도 비교, API engine routing, Deep Research, image generation, attachment 또는 browser lifecycle 재설계.
- 실제 OpenAI internal model slug를 영구 public contract로 고정.
- 과거 planning artifact 삭제 또는 정정.

## Delegated Planning Authority

- Product Thesis와 현재 repository/runtime evidence에 따라 하나 또는 필요한 수의 현재 Increment를 선택·재형성하고, 전체 bounded outcome이 충족될 때까지 성공 후 re-entry한다.
- Core Utility를 보존하는 범위에서 exact public request vocabulary, legacy alias 처리, config/MCP/skill projection 범위, closed/equivalent semantic readback 및 scenario 분할을 결정한다.
- 명백히 우월한 하나의 Behavior/UI/Scope/Spec/Ticket 선택이 현재 권위와 evidence로 결정되면 반복 승인 질문 없이 채택한다.
- Candidate / Supporting Means는 Goal과 Required Outcomes를 충족하는 최소 수단으로 선택·대체·보류할 수 있다.

## Continuation Authority

BOUNDED_OUTCOME

Meaning: maximum authorized success-continuation ceiling after a delivered current Increment, not the terminal condition of every invocation.

## Return-to-User Boundary

- 현재 권위와 evidence로 하나의 우월한 답을 정할 수 없는 material product-policy 또는 public compatibility trade-off.
- 로그인, CAPTCHA, 2단계 인증, 계정/model entitlement 또는 workspace 접근처럼 운영자의 직접 조치가 필요한 외부 조건.
- 배포, credential 변경, shared/production mutation, destructive action 또는 현재 지시가 허용하지 않은 외부 효과.

## Source User Authority

- 사용자는 최신 CALIBRATED Product Thesis를 정확히 따르는 IIS Adaptive Planning 전체 실행을 지시했다.
- 사용자는 Ready Ticket Plan은 Outer Main 직접, Plan Review는 DeepSeek V4.1 Flash Max, Implementation Worker는 Luna Max, Final Verifier와 Coverage는 Luna Max로 지정했다.
- Product meaning source: `/home/user01/project/oracle/oracle-browser-slots/docs/planning/product-thesis/pro-reasoning-level-selection/THESIS-003.md`.
- Repository evidence source: `/home/user01/project/oracle/oracle-browser-slots/docs/investigation/pro-reasoning-level-selection/INV-003.md`.

## Notes

- This Mandate delegates IIS planning judgment only; it does not make Adaptive Planning the implementation or verification authority.
- Continuation Authority is the maximum success-continuation ceiling. The invocation-local Adaptive Run Contract defines the actual Run Completion Boundary and Completion Predicate.
- Explicit Adaptive activation separately supplies Outer Main's default current-Increment implementation/verification handoff unless the user opts out.
- A Run Completion Boundary broader than this ceiling requires an explicit current Mandate revision/adoption before downstream planning/delivery mutation; never silently stop early or expand authority.
- Neither the Mandate nor Adaptive activation authorizes deployment, credentials, production/shared external mutation, destructive action, worker selection, or adversarial-consensus activation.
- Canonical IIS artifacts remain governed by current Baseline schemas and validators.
