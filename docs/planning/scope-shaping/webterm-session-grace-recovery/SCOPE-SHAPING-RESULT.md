# Webterm Session Grace and Continuous Drain Recovery - Scope Shaping Result

Status: confirmed
Owner: user01
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Work-Slug: webterm-session-grace-recovery
Scope-Revision: SHAPE-001
Planning-Shape: bounded

## Original Request

"기본 대기 시간 6시간인거 9시간으로 늘리려고해 -> 위 내용 기반으로 iis 사전조사 진행해", "기반으로 해서 런 컨트랙 아주 상세하게 작성해", "휴리스틱 루나 맥스 플랜 리뷰어 오라클 브라우저 3번 슬롯... 워커 루나 맥스, 검증 루나 맥스 그리고 넉 ㅏ아우터 메인으로 루프 책임 골 아웃컴 집중해서 시작해"

## Intent Horizon

모바일 브라우저가 장시간 화면 슬립, 배터리 절전, 네트워크 단절(지하철/이동) 상태에 진입하더라도 호스트 워크스테이션에서 구동 중인 작업(OMP subagent, 장시간 빌드 및 테스트)이 중간에 얼어붙지 않고 끝까지 완주되며, 최대 9시간 이내에 모바일 브라우저로 복귀 시 세션이 깨짐 없이 최신 터미널 화면으로 안정적으로 재동기화되는 무단절 모바일 개발 터미널 환경을 확립한다.

## Current Product State

- 프로덕션 ttyd 데몬(PID 237930)은 9월 8일 기동된 deleted 바이너리(MD5: 51d5cb...)로 기본 6시간 유예로 실행 중임
- 디스크 바이너리는 9월 10일 빌드(MD5: dc1f9e...), 프로덕션 HTML은 9월 4일 빌드(MD5: 9b1637...)인 런타임 3중 드리프트 상태임
- `src/protocol.c`의 세션 재접속 유예 기본 및 최대 상수는 6시간(21,600초)으로 하드코딩되어 있음
- PTY read가 정상 데이터 전송 및 PAUSE 상태에서 WebSocket 전송 속도에 결합되어 전송 지연 시 PTY read가 정지되어 호스트 프로세스가 block되는 결함 존재
- 버퍼 오버플로 복구 시 SIGWINCH가 foreground TUI가 아닌 background shell group으로 전달되는 결함 존재
- 클라이언트 `terminal.reset()`이 alternate screen 및 키 모드를 날려 TUI 화면을 깨뜨리고, rAF 진단 루프가 상시 실행되어 모바일 배터리를 낭비하는 결함 존재

## Investigation Assignments

None

## Verified Material Claims

### Claim 1

Classification: FACT
Primary Evidence: src/protocol.c lines 371-374, src/pty.c line 65
Counterexample Tested: WebSocket writable 콜백이 지연될 때 pss->pty_buf가 해소되지 않아 PTY read가 멈추고 자식 프로세스가 stdout write에서 block되는 인과 확인
Lead Finding: PTY read를 WebSocket 전송 상태와 완전히 분리하여 세션당 단일 8MB bounded output queue로 continuous drain을 유지해야 함
Planning Relevance: BOUNDARY

### Claim 2

Classification: FACT
Primary Evidence: src/protocol.c line 624, src/pty.c line 179
Counterexample Tested: uv_kill(-process->pid, SIGWINCH)는 셸 프로세스 그룹에만 시그널을 전달하여 대화형 foreground TUI(vim/OMP)가 시그널을 수신하지 못함을 확인
Lead Finding: Master PTY fd의 TIOCGPGRP ioctl로 현재 foreground PGID를 획득하여 시그널을 전달하는 pty_signal_foreground()가 필수적임
Planning Relevance: BOUNDARY

### Claim 3

Classification: FACT
Primary Evidence: src/protocol.c lines 20-22, 94-102, CUSTOMIZATION.md lines 18-19, 53-55
Counterexample Tested: 환경변수 TTYD_RECONNECT_GRACE만 32400으로 주입 시 SESSION_GRACE_MAX_SECONDS 초과로 기본값(21600)으로 강제 폴백됨을 확인
Lead Finding: 소스 매크로 상수 SESSION_GRACE_MAX_SECONDS를 (9 * 60 * 60)로 수정하고 문서를 동기화해야 함
Planning Relevance: PLANNING_CONSTRAINT

### Claim 4

Classification: FACT
Primary Evidence: html/src/components/terminal/xterm/index.ts lines 488-489, 736-745
Counterexample Tested: resumed 복원 시 terminal.reset()은 TUI 모드를 날리며, rAF 루프는 diagnosticsEnabled 조건 없이 상시 구동되어 모바일 배터리를 소모함
Lead Finding: fresh 세션에서만 terminal.reset()을 유지하고 resumed에서는 제거하며, rAF 루프는 진단 모드로 격리해야 함
Planning Relevance: BOUNDARY

## Planning Boundary

### Outcome

webterm 세션 재접속 유예 시간 9시간 확장 및 PTY continuous drain, foreground TUI SIGWINCH 재그리기, reset 경계 분리, rAF 누수 격리, 가상 가드레일 축소, 단일 바이트열 기반 원자적 릴리즈가 결합된 안정적 세션 연속성 확립.

### Includes

- `src/protocol.c`의 세션 재접속 유예 시간 상수 `(9 * 60 * 60)` (32,400초) 확장 및 `CUSTOMIZATION.md` 동기화
- PTY read 상시 drain 및 세션 단일 8MB bounded output queue 통합 (PAUSE 시 WS 발송만 보류)
- master fd `TIOCGPGRP` 기반 foreground PGID 대상 SIGWINCH 신호 전송 구현
- `fresh` 세션 생성 시에만 `terminal.reset()` 수행, `resumed` 세션 복원 시에는 reset 금지
- `xterm/index.ts` rAF 진단 루프의 `diagnosticsEnabled` 조건부 실행 격리
- `resumed-reset-v1`, `resetGate`, `terminal_recovery` 제거 및 `backlog_overflow`를 `needs_redraw` 단일 플래그로 대체
- 실행 중 데몬(`/proc/$LIVE_PID/exe`) 백업, 단일 RC 해시 고정, 7684 스테이징 검증 후 원자적 교체 및 단 1회 재기동

### Excludes

- WebSocket ping/pong 하트비트 주기(5초/30초) 변경
- 모바일 하단 툴바 레이아웃 또는 UI 테마 재설계
- Sixel 그래픽 지원 기능 복원
- tmux 기반 세션 영속화 도구 재도입

## Planning Constraints

- Tailscale Funnel 설정(`/terminal -> 127.0.0.1:7683`)을 절대 수정하거나 재설정하지 않음
- `session.sh`는 접속마다 독립적인 신규 로그인 셸(`/bin/bash -l`)을 기동함
- 세션 재접속 유예 기본값은 9시간(32,400초)이며, `TTYD_RECONNECT_GRACE` 허용 범위는 1~32400초임
- 정확히 동일한 단일 바이트열(`RC_TTYD`, `RC_HTML`)을 스테이징(7684) 검증 후 프로덕션(7683)에 원자적으로 승격함

## Candidate Outcome Areas

None

## Product Capability Dependencies

None

## Decisions Reserved For Matt

- `xterm` 클라이언트의 재접속 및 세션 복원 상태 오버레이 표시 문구 정책
- `TIOCGPGRP` 조회 실패 또는 `ESRCH` 발생 시의 재시도 횟수 및 예외 처리 정책

## Delivery Context

- 릴리즈 시 `/proc/$LIVE_PID/environ`에서 `TTYD_*` 환경변수를 보존함
- 안드로이드 실기기 스테이징 검증 시 Windows 호스트에서 `adb reverse --no-rebind tcp:17684 tcp:7684` 활용

## Outside The Assessed Landscape

- 다중 사용자 동시 접속 분배 및 외부 인증 통합
- 클라우드 브라우저 기반 원격 개발 세션 관리

## Construction Candidates

### Candidate A

Outcome Area: None
Current Product State: 6시간 유예 하드코딩, PTY-WS 결합으로 인한 호스트 프로세스 정지 위험, foreground PGID 시그널 누락, rAF 배터리 누수 및 런타임 3중 드리프트 상태
Target Product State: 9시간 유예 지원, PTY continuous drain으로 호스트 작업 무단절 보장, foreground PGID SIGWINCH로 TUI 깨짐 없는 복구, 가상 가드레일 축소 및 단일 바이트열로 원자적 배포 완료된 런타임
Actor Or Operator: 모바일 단말에서 원격 개발 작업을 수행하는 개발자 및 호스트 시스템 운영자
Trigger Or Inspection Target: 9시간 이내 모바일 재접속 및 8MB 초과 출력 후 세션 복원 동작
Observable Result: 모바일 슬립/오프라인 중에도 호스트 작업이 절대 멈추지 않고 완료되며, 9시간 내 재접속 시 TUI 화면이 깨짐 없이 즉시 재그려짐
Authoritative Readback: 소스 매크로 32400초 확인, 스테이징 프로토콜 테스트 통과, 프로덕션 ttyd 프로세스의 /proc/$PID/exe 해시가 RC_TTYD와 100% 일치
Durable Foundation: 장시간 오프라인 상태에서도 호스트 프로세스를 절대 블로킹하지 않는 안전한 PTY drain 기반 및 정직한 TUI 복구 구조
Future Policy Avoided: 복잡한 ring-buffer 백로그, 별도 클라이언트 상태머신, 커스텀 프로토콜 에포크 핸드셰이크
Lead Disposition: SELECT
Reason: 호스트 프로세스 무단절과 모바일 세션 연속성이라는 핵심 유틸리티를 최소한의 직접적인 코드로 완벽하게 만족하는 유일한 지속 가능한 설계임

## Provisional Construction Horizon

None

## Selected Next Increment

### INC-001: Webterm Session Grace and Continuous Drain Recovery

#### Work Package

None

#### Suggested Work Slug

webterm-session-grace-recovery

#### Selected Candidate

Candidate A

#### Current Product State

6시간 유예 하드코딩, PTY-WS 결합으로 인한 호스트 프로세스 정지 위험, foreground PGID 시그널 누락, rAF 배터리 누수 및 런타임 3중 드리프트 상태

#### Target Product State

9시간 유예 지원, PTY continuous drain으로 호스트 작업 무단절 보장, foreground PGID SIGWINCH로 TUI 깨짐 없는 복구, 가상 가드레일 축소 및 단일 바이트열로 원자적 배포 완료된 런타임

#### Observable Outcome

Actor Or Operator: 모바일 단말에서 원격 개발 작업을 수행하는 개발자 및 호스트 시스템 운영자
Trigger Or Inspection Target: 9시간 이내 모바일 재접속 및 8MB 초과 출력 후 세션 복원 동작
Observable Result: 모바일 슬립/오프라인 중에도 호스트 작업이 절대 멈추지 않고 완료되며, 9시간 내 재접속 시 TUI 화면이 깨짐 없이 즉시 재그려짐
Authoritative Readback: 소스 매크로 32400초 확인, 스테이징 프로토콜 테스트 통과, 프로덕션 ttyd 프로세스의 /proc/$PID/exe 해시가 RC_TTYD와 100% 일치

#### Includes

- `src/protocol.c`의 `SESSION_GRACE_MAX_SECONDS`를 `(9 * 60 * 60)`로 수정 및 `CUSTOMIZATION.md` 동기화
- PTY read 상시 유지 및 세션 단일 8MB bounded output queue 통합 (continuous drain)
- master fd `TIOCGPGRP` 기반 foreground PGID 대상 `SIGWINCH` 신호 함수 `pty_signal_foreground()` 구현
- `fresh`에서만 `terminal.reset()` 수행, `resumed`에서는 reset 금지
- `xterm/index.ts` rAF 루프를 `diagnosticsEnabled` 조건부 실행으로 격리
- `resumed-reset-v1`, `resetGate`, `terminal_recovery` 제거 및 `needs_redraw` 단일화
- 실행 중 데몬 백업, 단일 RC 해시 고정, 7684 스테이징 검증 후 원자적 교체 및 단 1회 재기동

#### Excludes

- WebSocket ping/pong 하트비트 변경
- 모바일 툴바 레이아웃 및 테마 수정
- Sixel 지원 복원 및 tmux 도구 도입

#### Required Product Dependencies

None

#### Preserved Foundations

- 390px 무스크롤 단일 행 하단 툴바 및 가상 키보드 분리 포커스 정책
- 접속 시 독립 신규 로그인 셸 기동 원칙 (`session.sh`)
- Tailscale Funnel 기반 외부 안전 접근 엔드포인트

#### Decisions Reserved For Matt

- xterm 클라이언트의 재접속 상태 오버레이 문구 세부 정책
- foreground SIGWINCH 재시도(ESRCH 발생 시) 간격 및 한도 정책

#### Deferred Until Re-entry

None

#### Verification Boundary

- `src/protocol.c` 및 `CUSTOMIZATION.md`의 32,400초 소스 일치 단언
- `staging/check_protocol_edges.py`를 통한 foreground PGID SIGWINCH 수신 및 continuous drain 회귀 검증
- 프로덕션 포트 7683 가동 ttyd 프로세스의 `/proc/$PID/exe` 해시와 `$RC_TTYD` 바이트 일치 단언

#### Re-entry Contract

프로덕션 배포 완료 후 모바일 Chrome 브라우저에서 Funnel URL을 통해 7683 포트에 정상 접속하여 단일 행 툴바 동작 및 9시간 세션 유지 동작을 실기기에서 검증함

#### Delivery Context

- 릴리즈 시 `/proc/$LIVE_PID/exe` 및 환경변수 백업
- ADB reverse 포워딩을 통한 스테이징 실기기 검증

#### Artifact

./increments/INC-001.md

## Unresolved Material Questions

None

## Confirmation

Confirmed By: user01
Confirmed Scope: Planning landscape, Planning Constraints, and exactly one Selected Next Increment; Decisions Reserved For Matt remain open and Provisional Construction Horizon remains non-normative
