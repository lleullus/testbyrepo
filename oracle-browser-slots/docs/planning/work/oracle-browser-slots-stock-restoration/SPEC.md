# Oracle Browser Slots Stock Flow Restoration and Slot 4 Verification

Status: approved
Owner: user

## Problem

래퍼(oracle-browser-slots)에 잘못 도입되었던 strict pre-child 게이트(6ec078be)로 인해 stock Oracle의 정상적인 브라우저 세션 제어 흐름이 방해받아 사전 차단되는 퇴행이 발생했다. 롤백(1800689b)을 통해 strict 게이트는 제거되었으나, 슬롯 4의 라이브 런타임에 에러 탭(Try again) 및 Cloudflare challenge가 남아 있어 stock Oracle의 ChatGPT Project end-to-end 프롬프트 실행 성공이 온전히 입증되지 못한 상태다.

## Desired Outcome

클린 HEAD(1800689b) 베이스라인에서 래퍼 수준의 strict 사전 차단 없이 stock Oracle 본래의 프로세스 전송 흐름을 유지한다. 슬롯 4의 런타임 세션을 안전하게 정리 및 정상화하고, 고유 nonce 프롬프트를 전송하여 stock Oracle이 ChatGPT 프로젝트 대화에서 완전한 응답을 수신(exit code 0)하고 슬롯이 정상 해제(occupancy: null)됨을 라이브 검증으로 확증한다.

## Requirements

- 래퍼는 child 프로세스(stock Oracle) 기동 전 목적지 페이지 강제 탐색, composer 존재 여부 검사, 강제 탭 고정 등의 strict 차단 게이트를 일절 수행하지 않고, argv-preserving 실행 경계를 유지해야 한다.
- 브라우저 슬롯 런타임은 WSLg 환경(DISPLAY=:0, WAYLAND_DISPLAY=wayland-0, XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir)을 준수하여 상시 정상 가동 상태를 유지해야 한다.
- 슬롯 4에서 stock Oracle 실행 시, 원격 Chrome 브라우저의 정상 ChatGPT 세션을 활용하여 실제 고유 nonce 프롬프트가 성공적으로 전송되고 어시스턴트 응답이 완료되어 프로세스가 exit code 0으로 종료되어야 한다.
- 작업 완료 후 래퍼의 슬롯 상태 조회 시 즉시 status: 사용 가능, occupancy: null로 복귀하여 자원 누수가 없어야 한다.

## Non-Goals

- 롤백으로 분리된 커밋 6306d498 및 d6d548b8(Pro identity 및 reasoning 복원)을 본 인크리먼트 내에서 성급하게 재통합하지 않는다.
- ChatGPT 또는 Cloudflare의 내부 정책/메커니즘을 변경하거나 우회하는 임의의 래퍼 코드를 작성하지 않는다.
- 가상 단위 테스트 개수만으로 라이브 브라우저 동작 검증을 대체하지 않는다.

## Implementation Constraints

- 현재 Git HEAD 1800689b를 베이스라인으로 유지하며, 퇴행 유발 함수(_prepare_strict_destination)를 복원하지 않는다.
- /home/user01/tmp 및 프로젝트 내 미추적 파일(docs/investigation/, tmp/)을 임의로 삭제하거나 초기화하지 않는다.
- 런타임 검증은 단일 고유 nonce 문자열(예: VERIFY_SMOKE_TIMESTAMP)을 사용하여 재현 및 증명을 명확히 한다.

## Verification Expectations

- Outcome: 래퍼의 strict 차단 없이 stock Oracle이 정상 기동되어 슬롯 4 브라우저를 통해 고유 nonce 프롬프트를 성공적으로 전송하고 어시스턴트 응답을 온전히 수신하여 exit code 0으로 종료되며, 실행 후 슬롯 4가 즉시 사용 가능 상태(occupancy: null)로 복귀한다.
  Acceptance boundary: ./bin/oracle-browser-slots CLI 실행 및 슬롯 상태 조회 표면
  Trigger or inspection target: ./bin/oracle-browser-slots run --slot 4 --job-id verify-smoke-job -- /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --wait -p "Reply with exactly: VERIFY_SMOKE_NONCE"
  Expected observable result: 프로세스 exit code 0 종료, 표준 출력에 VERIFY_SMOKE_NONCE 응답 포함, 슬롯 4 status: 사용 가능 및 occupancy: null 복귀
  Authoritative readback: ./bin/oracle-browser-slots run 표준 출력 및 exit code; ./bin/oracle-browser-slots status --slot 4 JSON 출력
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | 로컬 관리형 브라우저 슬롯 4 및 stock Oracle CLI 실행 표면
  External condition: 로컬 브라우저 슬롯 4(포트 19225) 기동 및 ChatGPT 인증 세션 유지

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성

## UI / UX

Not applicable

## Open Questions

None
