# Stock Oracle 경로 복원 및 슬롯 4 라이브 프롬프트 검증

Status: ready
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/oracle/oracle-browser-slots
Worker:
UI: no

## Goal

래퍼의 strict pre-child 게이트를 배제한 clean HEAD(1800689b) 베이스라인에서 stock Oracle의 실행 권한을 온전히 보존하고, 슬롯 4의 런타임 세션 정리 및 고유 nonce 프롬프트 라이브 실행을 통해 ChatGPT Project 대화 응답 수신과 슬롯 자원 정상 해제를 완결한다.

## Acceptance Criteria

- [AC-1] 래퍼 실행기(JobRunner)는 child 프로세스 기동 전 임의의 destination 준비, composer 검사, strict 탭 고정을 강제하지 않으며, stock Oracle 명령을 원본 그대로(argv-preserving) 실행한다.
- [AC-2] 슬롯 4 브라우저 인스턴스는 WSLg 환경에서 정상 구동 중이어야 하며, 런타임 세션에서 잔여 에러 탭(Try again)이 정리되고 정상 project 대화 페이지가 준비되어야 한다.
- [AC-3] ./bin/oracle-browser-slots run --slot 4 --job-id verify-smoke-job -- /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --wait -p "Reply with exactly: VERIFY_SMOKE_NONCE" 명령 실행 시 stock Oracle이 정상 시작되어 대화 응답을 수신하고 exit code 0으로 종료되어야 한다.
- [AC-4] stock Oracle의 응답 텍스트에 전송된 고유 nonce(VERIFY_SMOKE_NONCE)가 그대로 포함되어 있어야 한다.
- [AC-5] 실행 완료 직후 ./bin/oracle-browser-slots status --slot 4 조회 시 status: 사용 가능, occupancy: null로 즉시 복귀해야 한다.

## Scope

- stock Oracle 브라우저 슬롯 실행 흐름 보존
- 슬롯 4 세션 정상화 및 비정상 탭 정리
- 고유 nonce 라이브 프롬프트 실행 및 응답 수신
- 실행 후 슬롯 자원 점유 해제 확인

## Non-Goals

- 롤백된 커밋 6306d498 및 d6d548b8의 모델/추론 복원 작업 병합
- 래퍼 내부의 새로운 차단/재시도 게이트 추가
- mock이나 가상 단위 테스트만을 근거로 한 완료 판정

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1, 2, 3, 4, 5
  Behavior authority ordinals: 1
  Initial state: 클린 HEAD(1800689b) 베이스라인에서 슬롯 4(포트 19225)가 WSLg 환경에서 구동 중이고 래퍼에 strict pre-child 게이트가 없음
  Trigger or inspection target: ./bin/oracle-browser-slots run --slot 4 --job-id verify-smoke-job -- /home/user01/.nvm/versions/node/v24.18.0/bin/oracle --wait -p "Reply with exactly: VERIFY_SMOKE_NONCE"
  Acceptance boundary: ./bin/oracle-browser-slots CLI 실행 및 슬롯 상태 조회 표면
  Expected observable result: 프로세스 exit code 0 종료, 표준 출력에 VERIFY_SMOKE_NONCE 응답 포함, 실행 직후 슬롯 4 상태가 status: 사용 가능 및 occupancy: null로 복귀
  Authoritative readback: ./bin/oracle-browser-slots run 표준 출력 및 exit code; ./bin/oracle-browser-slots status --slot 4 JSON 출력
  Decision boundary: exit code 0 및 응답 본문 내 고유 nonce 포함 확인 시 통과; 비정상 종료, Cloudflare/Try again 차단 잔류 또는 occupancy 미해제 시 실패
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | 로컬 관리형 브라우저 슬롯 4 및 stock Oracle CLI 실행 표면
  External condition: 로컬 브라우저 슬롯 4(포트 19225) 기동 및 ChatGPT 인증 세션 유지

## Behavior Authorities

- docs/planning/behavior/contexts/oracle-browser-managed-slots.md | Scope: 운영자가 명시적으로 관리하는 Oracle Browser 슬롯의 식별, 준비 상태, 실행 적격성, 자동 배정 및 followup 원 슬롯 연속성

## References

- ../SPEC.md
