# GPT 모델 및 Pro 추론 지원을 위한 Oracle Browser 개편

Status: approved
Owner: user

## Problem

현재 Oracle Browser 래퍼(oracle-browser-slots) 및 Stock Oracle(@steipete/oracle)은 최신 ChatGPT 웹 UI 체계와 단절되어 있어 GPT-5.5, GPT-5.6 Sol, GPT-6 Pro 및 5단계 Pro 추론(Pro, 5 of 5. 선택 시 6 Pro 승격)을 정상 실행할 수 없다.
1) 래퍼(runner.py)가 gpt-5.6, gpt-5.6-sol 외의 모델을 거부하고 -m 단축 플래그 파싱이 누락되어 있음.
2) Stock CLI가 gpt-6-pro를 기본 모델(gpt-5.6-sol)로 무음 다운그레이드함.
3) Stock thinkingTime.ts의 stableModelFingerprint가 role="menuitemradio"를 수집하지 못해 모델 지문이 null이 되면서 model-mismatch 예외로 prompt 제출 전 조기 실패함.
4) Radix UI 슬라이더가 synthetic KeyboardEvent를 무시함.

## Desired Outcome

사용자가 gpt-5.5, gpt-5.6-sol, gpt-6-pro 및 pro 추론 강도를 요청했을 때, 무음 다운그레이드나 허위 검증 실패(model-mismatch) 없이 실제 해당 모델과 5단계 Pro 추론(6 Pro 승격)으로 정상 실행·완료되고 올바른 메타데이터(verified: true)를 얻는다.

## Requirements

- runner.py의 MODEL_FLAGS에 -m 플래그를 추가하고, compatible_slots에서 gpt-5.5, gpt-6, gpt-6-pro 모델을 정상 수용해야 한다.
- pro 추론 강도 및 gpt-6-pro는 반드시 Pro 지원 슬롯(1, 2, 10)으로만 라우팅되어야 하며, gpt-5.5는 일반/Pro 슬롯을 적절히 지원해야 한다.
- thinkingTime.ts의 stableModelFingerprint는 role="menuitemradio"를 정상 수집하여 모델 지문이 null이 되는 결함을 해결해야 한다.
- pro 추론 강도 요청 시 슬라이더 5단계 선택에 따른 Composer Pill의 6 Pro 라벨 변경을 모델 불일치가 아닌 정상 승격(Elevation)으로 인정해야 한다.
- Radix UI 슬라이더 조작 시 무시되는 synthetic KeyboardEvent 대신 CDP 레벨의 네이티브 포인터/마우스 이벤트 디스패치를 지원해야 한다.
- modelSelection.ts의 isReasoningOnlyLabel 정규식에 닫힌 상태의 6 Pro(6Pro) 라벨 패턴을 추가해야 한다.
- Stock TypeScript 소스 수정 후 pnpm run build를 통해 dist/bin/oracle-cli.js 실행 바이너리를 동기화해야 한다.
- 기존 126개 단위 테스트 및 스톡 vitest 테스트 스위트가 깨짐 없이 통과해야 한다.

## Non-Goals

- Plus 계정 슬롯(3, 4, 5)에 Pro 추론 강제 배정 (계정 entitlement 한계).
- 브라우저 모드와 무관한 다중 모델 API 플래그(--models) 지원.
- followup 세션의 originating_slot 스키마 변경 (이전 부모 세션 호환성 보존).

## Implementation Constraints

- --browser-model-strategy current 정책을 기본 유지한다.
- originating_slot dict 비교 로직의 무결성을 깨뜨리지 않는다.

## Verification Expectations

- Outcome: 래퍼와 스톡 런타임이 gpt-5.5, gpt-5.6-sol, gpt-6-pro 및 pro 추론 강도를 정상 수용하고, 슬롯 2(Pro 계정)에서 5단계 슬라이더와 6 Pro 라벨 승격이 model-mismatch 없이 completed로 성공하며, 단위 및 vitest 테스트가 100% 통과한다.
  Acceptance boundary: oracle-browser-slots CLI, pytest 테스트 스위트, vitest 테스트 스위트 및 ChatGPT 브라우저 실행 표면
  Trigger or inspection target: python3 -m pytest; pnpm exec vitest run tests/browser/modelSelection.test.ts tests/browser/thinkingTime.test.ts tests/browser/reasoningSelection.test.ts; ./bin/oracle-browser-slots run --slot 2 --job-id verify-pro-elevation -- /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --engine browser --browser-model-strategy current --model gpt-6-pro --browser-thinking-time pro -p "ping"
  Expected observable result: 단위/스톡 테스트 100% PASS, 슬롯 2 실행 exit code 0 및 completed 종료, meta.json 내 reasoningSelection.resolvedLevel: "pro", verified: true 확인
  Authoritative readback: pytest/vitest 콘솔 출력; oracle-browser-slots run JSON 이벤트; ~/.oracle/sessions/*/meta.json
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | 로컬 관리형 브라우저 슬롯 2 및 oracle-browser-slots CLI
  External condition: 슬롯 2(포트 19223) 기동 및 Pro 계정 로그인 세션 유지

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성

## UI / UX

Not applicable

## Open Questions

None
