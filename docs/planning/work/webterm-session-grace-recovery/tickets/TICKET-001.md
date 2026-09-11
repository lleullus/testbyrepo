# TICKET-001: Webterm 세션 유예 9시간 확장 및 무단절 PTY 복구 릴리즈

Status: done
Parent-Spec: ../SPEC.md
Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Worker:
UI: yes

## Goal

webterm 세션 재접속 유예 시간을 기본 9시간(32,400초)으로 확장하고, PTY read 상시 배출(continuous drain)로 모바일 슬립 중 호스트 프로세스 무단절을 보장하며, foreground PGID SIGWINCH 재그리기, reset 경계 분리, rAF 누수 격리, 가상 가드레일 축소 및 단일 바이트열 기반 원자적 릴리즈를 완수한다.

## Acceptance Criteria

- src/protocol.c의 SESSION_GRACE_MAX_SECONDS가 (9 * 60 * 60)로 수정되고 CUSTOMIZATION.md의 허용 범위(1~32400초)가 동기화된다.
- pty.c에서 uv_read_stop()을 정상 경로에서 제거하고, 세션 단일 8MB bounded output queue로 통합하여 클라이언트 PAUSE 시에도 PTY read가 멈추지 않고 상시 배출(continuous drain)된다.
- pty.c에 pty_signal_foreground()를 구현하여 master fd TIOCGPGRP로 foreground PGID를 구해 SIGWINCH를 전송하고 버퍼 오버플로 복구 시 TUI 화면을 재그린다.
- xterm/index.ts에서 fresh 세션에서만 terminal.reset()을 수행하고 resumed 복원 시에는 reset을 생략하며, rAF 루프를 diagnosticsEnabled 모드로 격리한다.
- resumed-reset-v1, resetGate, terminal_recovery를 제거하고 needs_redraw 단일 플래그로 축소한다.
- 실행 중 데몬(/proc/$LIVE_PID/exe) 백업, 단일 RC 해시 고정(RC_TTYD, RC_HTML), 7684 스테이징 검증 후 원자적 교체 및 단 1회 재기동으로 3중 드리프트를 완전히 해소한다.

## Scope

- src/protocol.c
- src/pty.c
- src/pty.h
- src/server.h
- html/src/components/terminal/xterm/index.ts
- CUSTOMIZATION.md
- staging/check_protocol_edges.py
- continuous drain queue in protocol.c
- pty_signal_foreground in pty.c

## Non-Goals

- WebSocket ping/pong 하트비트 주기(5초/30초) 변경
- 모바일 툴바 레이아웃 및 테마 재설계
- Sixel 지원 복원 및 tmux 도구 도입

## Blockers

None

## Verification

- Parent outcome ordinal: 1
  AC ordinals: 1
  Behavior authority ordinals: 1
  Initial state: ttyd 소스 코드에서 재접속 유예 기본 상수가 6시간으로 하드코딩되어 있음
  Trigger or inspection target: src/protocol.c lines 20-22, 94-102 and CUSTOMIZATION.md
  Acceptance boundary: canonical source and test runner
  Expected observable result: SESSION_GRACE_MAX_SECONDS가 (9 * 60 * 60)로 정의되고, TTYD_RECONNECT_GRACE=32400이 정상 수용됨
  Authoritative readback: src/protocol.c source assertion and CUSTOMIZATION.md text
  Decision boundary: 32400초(9시간) 소스 정의 및 문서 동기화 확인
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | src/protocol.c
  External condition: None
  Persistence storage identity and lifecycle boundary: libuv session timer (32,400,000 ms)

- Parent outcome ordinal: 2
  AC ordinals: 2
  Behavior authority ordinals: 2
  Initial state: 클라이언트 전송 지연 또는 PAUSE 수신 시 PTY read가 정지되는 구조
  Trigger or inspection target: PTY read loop during client flow pause
  Acceptance boundary: PTY stream and process execution
  Expected observable result: 클라이언트 PAUSE 상태에서 8MB 초과 출력이 발생해도 PTY read가 계속 돌아 호스트 프로세스가 정상 종료됨
  Authoritative readback: process exit code 0 and completion marker generated before resume
  Decision boundary: 클라이언트 PAUSE 중 호스트 프로세스 완주 확인
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | continuous drain queue in protocol.c
  External condition: None

- Parent outcome ordinal: 3
  AC ordinals: 3, 5
  Behavior authority ordinals: 1
  Initial state: 버퍼 오버플로 후 SIGWINCH가 background shell group으로 전달됨
  Trigger or inspection target: pty_signal_foreground() with master fd TIOCGPGRP
  Acceptance boundary: PTY signal handling
  Expected observable result: foreground TUI 프로세스 그룹(PGID)에 SIGWINCH 시그널이 도달함
  Authoritative readback: foreground child SIGWINCH trap receipt
  Decision boundary: foreground PGID 대상 SIGWINCH 도달 확인
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | pty_signal_foreground in pty.c
  External condition: None

- Parent outcome ordinal: 4
  AC ordinals: 4
  Behavior authority ordinals: 1, 2
  Initial state: 세션 복원 시 terminal.reset() 호출 및 rAF 진단 루프 상시 구동
  Trigger or inspection target: html/src/components/terminal/xterm/index.ts
  Acceptance boundary: frontend xterm component
  Expected observable result: resumed 상태에서 terminal.reset() 미호출, diagnosticsEnabled=false일 때 requestAnimationFrame 미호출
  Authoritative readback: inline.html bundle inspection and browser execution
  Decision boundary: alternate screen 모드 보존 및 rAF 비활성화 확인
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | html/src/components/terminal/xterm/index.ts
  External condition: None
  UI rendered state and interaction readback: alternate screen preservation and zero-rAF loop when diagnostics disabled

- Parent outcome ordinal: 5
  AC ordinals: 6
  Behavior authority ordinals: 1
  Initial state: 실행 메모리(deleted 바이너리), 디스크 바이너리(WIP), 프로덕션 HTML(9/4) 3중 드리프트 상태
  Trigger or inspection target: /proc/$LIVE_PID/exe backup and /proc/$NEW_PID/exe hash verification
  Acceptance boundary: production daemon process and disk binaries
  Expected observable result: 실행 데몬 바이너리 해시가 빌드된 RC_TTYD와 100% 일치하고 Funnel 7683 서비스 정상 응답
  Authoritative readback: sha256sum /proc/$NEW_PID/exe == sha256sum ~/.local/bin/ttyd == RC_TTYD and sha256sum ~/.local/share/webterm/index.html == RC_HTML (revalidated by sha256sum -c SHA256SUMS.txt)
  Decision boundary: 프로덕션 데몬 바이너리 및 HTML 해시와 RC_TTYD/RC_HTML SHA-256 일치 확인
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | /home/user01/.local/bin/ttyd and /home/user01/.local/share/webterm/index.html
  External condition: None

## Behavior Authorities

- docs/planning/behavior/lifecycles/session-reconnect-lifecycle.md | Scope: webterm session reconnect and 9-hour grace lifecycle
- docs/planning/behavior/invariants/pty-continuous-drain.md | Scope: non-blocking PTY read and flow control decoupling invariants

## References

- ../SPEC.md
