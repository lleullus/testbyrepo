# Adaptive Planning Mandate

Mode: IIS Adaptive Planning
Status: active
Revision: 1
Owner: user01
Project-Root: /home/user01/project/oracle/oracle-browser-slots
Applies-To: oracle-browser-slots-stock-restoration

## Desired Product Outcome

래퍼 수준의 strict pre-child 게이트를 배제한 클린 HEAD(1800689b) 베이스라인에서, stock Oracle의 브라우저 세션 제어권을 온전히 보존하고 슬롯 4의 ChatGPT 프로젝트 워크스페이스 대화 실행(고유 nonce 프롬프트 전송 및 응답 수신)과 슬롯 자원 해제(occupancy: null)를 end-to-end 라이브 검증으로 확증한다.

## Why / User Value

이전에 정상 작동하던 stock Oracle 경로에 잘못된 wrapper-level strict 사전 차단이 추가되어 발생했던 퇴행을 바로잡고, 사용자 가치 없는 가상 단위 테스트 통과에 속지 않고 실제 라이브 브라우저 상에서 동작하는 신뢰할 수 있는 실행 환경을 회복한다.

## Decision Priorities

1. 기존 작동하던 stock Oracle 경로의 완전한 복원 및 제어권 보존 (래퍼의 임의 차단 배제).
2. 가상 단위 테스트 대신 실제 라이브 브라우저/CDP 표면에서의 관측 가능한 완료 증거 확보.
3. 최소 침습적이고 단순한 구조 유지 (불필요한 wrapper 복잡도 및 재시도 메커니즘 억제).
4. 후속 기능(Pro identity, reasoning selection)은 본 검증 완료 후 엄격히 분리하여 안전하게 취급.

## Hard Constraints

- 래퍼 수준의 strict pre-child 게이트(`_prepare_strict_destination`, 임의 탭 고정, composer 사전 강제 등)를 재도입하지 않는다.
- Git 트래킹 작업 트리는 HEAD `1800689b`를 유지하며, `/home/user01/tmp` 및 저장소 내 미추적 디렉터리를 임의로 삭제하지 않는다.
- 브라우저 슬롯 기동 및 검증 시 WSLg 그래픽 환경변수(`DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`, `XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir`)를 반드시 준수한다.
- 라이브 프롬프트 검증은 실제 고유 nonce 문자열을 사용하며, 가상 목업(mock)이나 가짜 성공을 주장하지 않는다.

## Non-Goals

- 본 인크리먼트 내에서 롤백된 커밋 `6306d498` 및 `d6d548b8`의 대규모 모델/추론 로직을 섣불리 통합하지 않는다 (추후 별도 인크리먼트로 분리).
- 일반적인 ChatGPT/Cloudflare 웹사이트의 내부 인증 로직을 래퍼 코드로 우회하거나 해킹하지 않는다.

## Delegated Planning Authority

- 슬롯 4 런타임 정리 및 stock Oracle 실행 복원을 위한 단일 정밀 Increment 및 Ready Ticket 구성.
- 의사결정 우선순위에 따른 검증 플로우 및 수용 기준(AC) 구체화.
- 불필요한 계획 단계 팽창 억제 및 최소 필수 경로 선택.

## Continuation Authority

CURRENT_INCREMENT

Meaning: maximum authorized success-continuation ceiling after a delivered current Increment, not the terminal condition of every invocation.

## Return-to-User Boundary

- 라이브 브라우저 상에서 자동화 불가능한 대화형 Cloudflare 캡차 또는 2단계 인증 등 사람의 직접 브라우저 조작이 불가피한 경우.
- stock Oracle 자체의 상위 바이너리 결함이나 원격 ChatGPT 서비스의 영구적 차단이 확인된 경우.

## Source User Authority

- 사용자 지시: "파이널 베리파이어를 솔 미디엄으로 하고 나머지는 전부 류나 맥스로 한다. 너는 아우터 메인으로서 모든 것을 관장하고 이 어댑티브 플래닝을 책임지는 거다. II스킬즈 제대로 읽고 시작해"
- 사전 조사 대체 핸드오프: `/home/user01/tmp/oracle-browser-slots-rollback-failure-handoff.md`

## Notes

- 본 Mandate는 IIS 기획 판단 권한을 정의하며, 실행 및 검증은 Outer Main의 총괄 하에 지정된 모델(Implementation: Luna Max, Verification: Sol Medium)의 서브에이전트 또는 격리된 실행자로 수행된다.
- Continuation Authority는 CURRENT_INCREMENT로 설정되어 현재 단일 인크리먼트 완료에 집중한다.
