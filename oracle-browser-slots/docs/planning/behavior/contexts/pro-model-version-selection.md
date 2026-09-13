# Pro Model/Version Selection

Status: approved
Owner: user
Scope: Oracle Browser initial run과 explicit followup에서 model/version choice와 Power=Pro를 결합해 선택·검증·귀속하는 행동

## Research

- Current live ChatGPT picker에는 서로 독립적인 두 축이 있다. model/version row는 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`이고 Power slider는 `Instant`, `Medium`, `High`, `Extra High`, `Pro`다. Source: `docs/investigation/pro-reasoning-level-selection/INV-003.md` Findings 1–2.
- Current Stock Oracle은 initial run에서 model row를 선택한 뒤 매 prompt 제출 직전에 reasoning을 선택하지만, resumed conversation에서는 model picker를 건너뛴다. Current Pro final approval은 closed pill `6 Pro`에 고정돼 있다. Source: `INV-003.md` Findings 4–5 및 current `src/browser/index.ts`, `src/browser/actions/thinkingTime.ts`.
- Wrapper는 model/reasoning 조합의 slot eligibility와 slot/origin lifecycle을 소유하고, actual checked row나 Power state는 증명하지 않는다. Source: `INV-003.md` Findings 6–7.
- 적용 managed slot의 식별·점유·배정·followup 경계는 기존 승인 authority `docs/planning/behavior/contexts/oracle-browser-managed-slots.md`가 소유한다.

## Behavior Model

- 운영자가 선택할 수 있는 Pro model/version choice는 정확히 `Latest`, `GPT-5.6 Sol`, `GPT-5.5`다. `Pro`는 별도 Power intent이며 세 choice 모두에 적용된다.
- 한 요청은 정확히 하나의 requested choice를 가진다. Current UI에서 그 exact row 하나만 checked이고 Power가 `Pro`일 때만 requested selection이 성립한다.
- `Latest`는 invocation 시점의 current latest Pro-capable track이다. Evidence는 requested choice `Latest`와 당시 resolved model/version을 분리해 보존하며, 현재 GPT-6이라는 관찰을 영구 의미로 바꾸지 않는다.
- Initial run은 requested row를 선택·확인한 후 Power=`Pro`를 선택·확인한다. Power 조작 전후 model/version identity가 연속이어야 한다.
- Explicit followup은 parent의 같은 slot/profile/conversation에서 수행한다. 운영자가 choice를 명시하면 현재 turn에서 requested row와 Power=`Pro`를 다시 선택·검증할 수 있으며, 이전 turn의 선택 evidence를 재사용하지 않는다.
- Followup에서 model/version choice를 생략하면 기존 conversation의 current selection을 보존하고 새 requested choice를 만들거나 추정하지 않는다. 생략된 choice를 `Latest`, parent request 또는 다른 세 choice로 기록하지 않는다. Power intent도 명시되지 않으면 새 Pro 선택·검증 성공을 주장하지 않는다.
- 성공 evidence는 같은 invocation/turn/attempt에 귀속된 requested choice, exact checked row와 resolved model/version, Power=`Pro`, model identity continuity를 포함한다. Wrapper evidence의 assigned slot과 original conversation origin은 별도 권위로 결합해 읽는다.
- Closed composer pill 또는 equivalent semantic display는 checked row와 Power readback의 결합에 모순이 없는지 확인하는 consistency signal이다. 특정 한 문자열은 세 choice 전체의 단독 성공 권위가 아니다.
- Requested row가 이미 checked이거나 Power가 이미 Pro여도 현재 positive readback을 새 요청/turn에 귀속해 확인해야 한다.
- Current UI에서 requested row 또는 단일 명확한 Power control을 찾을 수 없거나, 둘 이상의 row가 checked되거나, selection state가 없거나, 다른 row/lower Power/model change/combined readback contradiction이 관찰되면 prompt 제출 전에 실패한다. Nearest/current/Latest fallback은 없다.
- UI mount나 state 반영을 기다리는 동작은 bounded하다. 제한 안에 positive conjunction을 얻지 못하면 실패하며, success로 추정하거나 prompt를 먼저 제출하지 않는다.
- Retry는 prompt 제출 전 selection attempt만 다시 수행할 수 있다. 각 attempt는 자체 evidence를 가지며 실패 attempt의 evidence를 다음 attempt나 turn의 성공으로 재사용하지 않는다. Prompt가 제출된 뒤 selection 실패 복구 명목으로 같은 prompt를 중복 제출하지 않는다.
- 여러 상담이 동시에 실행되더라도 각 run은 기존 managed-slot 단일 점유 경계를 따르고 evidence를 자신의 slot, conversation, turn, attempt에만 귀속한다. 한 run의 checked row나 Power evidence가 다른 run을 승인하지 않는다.
- Slot eligibility, 자동 배정 순서, unsupported slot 거절, followup 원점 및 slot 장애 격리는 `oracle-browser-managed-slots.md`의 승인된 규칙을 그대로 적용한다.

## Counterexample Stress Test

- Power만 Pro이고 checked row가 다르거나 불명확한 구현은 세 choice를 구별하지 못하므로 실패다.
- Requested row만 맞고 Power가 lower level인 구현은 Pro 상담이 아니므로 실패다.
- `6 Pro` 문자열만 승인하는 구현은 GPT-5.6 Sol/GPT-5.5를 거짓 실패시키고 Latest를 영구 GPT-6으로 굳히므로 금지한다.
- Row 선택 뒤 Power 조작이 다른 row로 바꾸는데 slider success만 남기는 구현은 model continuity를 깨므로 실패다.
- Resumed conversation이라는 이유로 explicit followup choice를 무조건 건너뛰는 구현은 requested change를 적용하지 못하므로 금지한다.
- 반대로 choice를 생략한 followup을 임의의 explicit choice로 기록하는 구현은 운영자 의도를 위조하므로 금지한다.
- 이전 turn의 verified evidence를 새 followup에 복사하는 구현은 current selection drift를 탐지하지 못하므로 금지한다.
- Slot assignment만으로 browser selection 성공을 주장하거나 browser evidence만으로 slot/origin을 주장하는 구현은 권위 경계를 대체하므로 금지한다.
- UI 지연 중 prompt를 먼저 제출하고 사후에 selection을 확인하는 구현은 pre-submit gate를 깨므로 금지한다.
- 동시 run이 다른 slot이나 conversation의 evidence를 공유하는 구현은 귀속과 원점 연속성을 깨므로 금지한다.

## Product Decision Return

None

## Conclusion

Oracle Browser의 Pro 선택은 exact model/version row 하나와 별도 Power=`Pro`의 결합이다. Initial run과 explicit followup은 prompt 제출 전 같은 turn/attempt의 positive row·Power·identity evidence를 요구하며, Wrapper의 slot/origin evidence와 권위를 분리해 함께 읽는다. `Latest`는 동적이고, 생략된 followup choice는 추정하지 않으며, unavailable·ambiguous·mismatch·drift는 fallback 없이 제출 전에 실패한다.
