# GPT 모델 및 Pro 추론 지원을 위한 Wrapper 및 Stock 개편

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/oracle/oracle-browser-slots
Worker:
UI: no

## Goal

Oracle Browser 래퍼(oracle-browser-slots)와 Stock Oracle(@steipete/oracle)을 최신 ChatGPT UI에 맞춰 개편하여 gpt-5.5, gpt-5.6-sol, gpt-6-pro 및 5단계 Pro 추론 강도(6 Pro 승격)를 완벽하게 지원한다.

## Acceptance Criteria

- runner.py의 MODEL_FLAGS에 -m이 포함되어 -m 단축 플래그로 모델을 지정해도 모델 라우팅이 정상 작동한다.
- runner.py의 compatible_slots에서 gpt-5.5, gpt-6, gpt-6-pro가 허용되고, gpt-6-pro 및 pro 추론 요청은 슬롯 1, 2, 10으로 고정 라우팅되며, gpt-5.5는 standard 시 전 슬롯(1~5, 10), high 시 (3, 4, 5, 1, 2, 10), pro 시 (1, 2, 10)으로 매핑된다.
- thinkingTime.ts의 stableModelFingerprint가 role="menuitemradio"를 수집하여 라이브 DOM에서 모델 지문이 null이 되지 않는다.
- pro 추론 강도 적용 시 5단계 슬라이더 선택에 따른 6 Pro 라벨 변경이 정상 승격으로 인정되어 model-mismatch 예외를 발생시키지 않는다.
- Radix UI 슬라이더 조작 시 무시되는 synthetic KeyboardEvent 대신 CDP 레벨의 마우스/포인터 클릭 시퀀스가 정상 동작한다.
- modelSelection.ts의 isReasoningOnlyLabel에 닫힌 상태의 6 Pro(6Pro) 라벨이 등록되어 모델 선택기 검증을 통과한다.
- Stock TypeScript 소스 수정 후 pnpm run build가 성공적으로 완료되어 dist/bin/oracle-cli.js에 반영된다.
- oracle-browser-slots의 pytest 단위 테스트(기존 126개 및 신규 모델 케이스)가 100% 통과한다.
- Stock Oracle의 브라우저 vitest 테스트 스위트가 100% 통과한다.
- 슬롯 2 라이브 실행에서 --model gpt-6-pro --browser-thinking-time pro 요청이 rejection이나 model-mismatch 없이 completed로 완료되고 meta.json에 reasoningSelection.resolvedLevel: "pro", verified: true가 기록된다.

## Scope

- oracle_browser_slots/runner.py 모델 및 추론 라우팅
- src/browser/actions/thinkingTime.ts 모델 지문 수집 및 6 Pro 승격 가드
- src/browser/actions/modelSelection.ts 라벨 판정
- tests/test_slots.py 및 Stock vitest 테스트
- Stock TypeScript 빌드 파이프라인

## Non-Goals

- Plus 계정 슬롯(3, 4, 5)에 Pro 추론 강제 배정
- 다중 모델 API 플래그(--models) 지원
- followup 세션의 originating_slot 스키마 변경

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
  Behavior authority ordinals: 1
  Initial state: 클린 베이스라인에서 슬롯 2(포트 19223)가 Pro 계정으로 로그인되어 있고 래퍼 및 스톡 런타임이 gpt-5.6-sol에 고정되어 있음
  Trigger or inspection target: python3 -m pytest; pnpm exec vitest run tests/browser/modelSelection.test.ts tests/browser/thinkingTime.test.ts tests/browser/reasoningSelection.test.ts; ./bin/oracle-browser-slots run --slot 2 --job-id verify-pro-elevation -- /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --engine browser --browser-model-strategy current --model gpt-6-pro --browser-thinking-time pro -p "ping"
  Acceptance boundary: oracle-browser-slots CLI, pytest 테스트 스위트, vitest 테스트 스위트 및 ChatGPT 브라우저 실행 표면
  Expected observable result: 단위 및 스톡 vitest 테스트 100% PASS, 슬롯 2 라이브 실행 exit code 0 및 completed 종료, meta.json 내 reasoningSelection.resolvedLevel: "pro", verified: true 확인
  Authoritative readback: pytest/vitest 콘솔 출력; ./bin/oracle-browser-slots run JSON 출력; ~/.oracle/sessions/*/meta.json
  Decision boundary: 모든 테스트 PASS 및 슬롯 2에서 gpt-6-pro + pro 추론 completed 성공 시 통과; 테스트 실패, rejection, model-mismatch 예외 발생 또는 verified: false 시 실패
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | 로컬 관리형 브라우저 슬롯 2 및 oracle-browser-slots CLI
  External condition: 슬롯 2(포트 19223) 기동 및 Pro 계정 로그인 세션 유지

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성

## References

- ../SPEC.md
- /home/user01/project/oracle/oracle-browser-slots/docs/investigation/gpt-model-reasoning-elevation/INV-001.md
