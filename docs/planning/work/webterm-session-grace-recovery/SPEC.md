# Webterm Session Grace and Continuous Drain Recovery

Status: approved
Owner: user01
Source-Increment: docs/planning/scope-shaping/webterm-session-grace-recovery/increments/INC-001.md

## Problem

현재 `webterm`(ttyd 1.7.7 커스텀 포크)은 모바일 단말(안드로이드 폰)에서 원격 워크스테이션 개발 시 다음과 같은 4가지 중대 결함을 가지고 있다:
1. 세션 재접속 대기 유예 시간(reconnect grace)이 기본 6시간(21,600초)으로 하드코딩되어 있어 이동 및 장시간 업무 공백 시 세션이 조기 소멸됨.
2. 클라이언트 전송 지연 또는 `PAUSE` 수신 시 `protocol.c:371-374` 및 `pty.c:65`에서 PTY read까지 멈추어, 모바일 슬립 중 호스트의 OMP subagent, 빌드, 배치 작업이 stdout write에서 영구 block됨.
3. 버퍼 오버플로 후 재접속 시 `protocol.c:624`가 `pty_kill(-process->pid, SIGWINCH)`를 호출하여 foreground TUI(vim/htop/OMP)가 아닌 background shell group에 시그널을 날려 화면이 복구되지 않음.
4. 클라이언트가 복원 시 `terminal.reset()`(full RIS)을 때려 alternate screen과 키 모드를 파괴하며, `xterm/index.ts:488`의 rAF 진단 루프가 상시 동작하여 모바일 배터리를 낭비함.
5. 운영 환경이 실행 메모리(9/8 deleted 바이너리), 디스크 바이너리(9/10 WIP), 프로덕션 HTML(9/4)로 분리된 런타임 3중 드리프트 상태임.

## Desired Outcome

1. 세션 재접속 유예 시간을 기본 9시간(32,400초)으로 확장하고 환경변수(`TTYD_RECONNECT_GRACE=1..32400`)로 제어 가능하게 함.
2. PTY read를 WebSocket 전송 상태와 완전히 분리하여 세션당 단일 8MB bounded output queue로 continuous drain을 유지함으로써 모바일 슬립 중에도 호스트 작업이 절대 멈추지 않고 완주되도록 보장함.
3. Master PTY fd의 `TIOCGPGRP`로 foreground PGID를 획득해 `SIGWINCH`를 전달함으로써 재접속 시 TUI 화면이 깨짐 없이 자가 복구되도록 함.
4. `fresh` 세션에서만 `terminal.reset()`을 수행하고 `resumed` 복원 시에는 reset을 금지하며, rAF 루프를 `diagnosticsEnabled` 모드로 완전 격리함.
5. `resumed-reset-v1`, `resetGate`, `terminal_recovery` 등 가상 가드레일을 걷어내고 `needs_redraw` 단일 플래그로 축소함.
6. 실행 중 데몬 바이너리(`/proc/$LIVE_PID/exe`) 백업 보존, 단일 RC 해시 고정, 7684 스테이징 검증 후 원자적 교체 및 단 1회 재기동으로 3중 드리프트를 완전히 해소함.

## Requirements

1. `src/protocol.c`의 `#define SESSION_GRACE_MAX_SECONDS (9 * 60 * 60)`로 수정하고, `CUSTOMIZATION.md`의 유예 시간 설명을 9시간(1~32400초)으로 동기화할 것.
2. `pty.c`의 정상 read 경로에서 `uv_read_stop()`을 제거하고, `protocol.c`의 `pss->pty_buf`와 `session->backlog`를 세션 단일 8MB bounded output queue로 통합하여 PTY 출력을 상시 drain할 것. 클라이언트 `PAUSE` 수신 시 WS 전송만 보류하고 PTY read는 중단하지 말 것.
3. 8MB 초과 시 기존 큐를 폐기하고 `needs_redraw = true`로 설정하며, 이후 PTY 출력은 계속 drain하되 폐기할 것.
4. `pty.c`에 `pty_signal_foreground(pty_process *process, int sig)`를 구현하여 master fd `TIOCGPGRP`로 foreground PGID를 구해 `kill(-pgid, sig)`를 발송할 것 (`ESRCH` 시 1회 재시도).
5. `needs_redraw == true` 상태에서 클라이언트 소비 재개 시 오래된 큐 재생(replay)을 생략하고 foreground PGID에 `SIGWINCH`를 발송한 뒤 플래그를 해제할 것.
6. `html/src/components/terminal/xterm/index.ts`에서 `resumed` 복원 시 `terminal.reset()`을 호출하지 말고, `fresh` 세션 생성 시에만 `terminal.reset()`을 수행할 것.
7. `xterm/index.ts`의 `monitorAnimationFrames` rAF 루프를 `this.diagnosticsEnabled` 조건 하에서만 실행하도록 격리할 것.
8. `resumed-reset-v1:<gen>` 세션 상태, `resetGate`, `terminal_recovery` capability, `TTYD_TERMINAL_RECOVERY` 환경변수를 전면 제거할 것.
9. 릴리즈 절차를 준수하여 실행 데몬(`/proc/$LIVE_PID/exe`) 백업, 단일 RC 해시 고정, 7684 스테이징 검증 후 데몬 정지 및 원자적 교체(`mv`)를 거쳐 단 1회 재기동할 것.

## Non-Goals

- WebSocket ping/pong 하트비트 주기(5초/30초) 변경
- 모바일 툴바 레이아웃 또는 UI 테마 재설계
- Sixel 그래픽 지원 복원
- tmux 기반 세션 영속화 도구 재도입

## Implementation Constraints

- Tailscale Funnel 설정(`/terminal -> 127.0.0.1:7683`)을 변경하지 않는다.
- `session.sh`의 독립 신규 로그인 셸 기동 원칙을 보존한다.
- `TTYD_RECONNECT_GRACE` 허용 범위는 1~32400초이며 `SESSION_GRACE_MAX_SECONDS` 매크로와 엄격히 일치해야 한다.
- 동일한 단일 바이트열(`RC_TTYD`, `RC_HTML`)만 스테이징에서 프로덕션으로 승격한다.

## Verification Expectations

- Outcome: 세션 재접속 유예 시간(reconnect grace)이 9시간(32,400초)으로 확장되고 환경변수로 제어 가능하다.
  Acceptance boundary: canonical source and test runner
  Trigger or inspection target: src/protocol.c lines 20-22, 94-102 and CUSTOMIZATION.md
  Expected observable result: SESSION_GRACE_MAX_SECONDS가 (9 * 60 * 60)로 정의되고, TTYD_RECONNECT_GRACE=32400이 정상 수용됨
  Authoritative readback: src/protocol.c source assertion and CUSTOMIZATION.md text
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | src/protocol.c
  External condition: None
  Persistence storage identity and lifecycle boundary: libuv session timer (32,400,000 ms)

- Outcome: 클라이언트 PAUSE 및 네트워크 지연 시에도 PTY read가 멈추지 않고 상시 배출(continuous drain)되어 호스트 프로세스가 block되지 않는다.
  Acceptance boundary: PTY stream and process execution
  Trigger or inspection target: PTY read loop during client flow pause
  Expected observable result: 클라이언트 PAUSE 상태에서 8MB 초과 출력이 발생해도 PTY read가 계속 돌아 호스트 프로세스가 정상 종료됨
  Authoritative readback: process exit code 0 and completion marker generated before resume
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | continuous drain queue in protocol.c
  External condition: None

- Outcome: 세션 버퍼 오버플로 후 재접속 시 foreground process group에만 정확히 SIGWINCH가 전달되어 TUI 화면이 재그려진다.
  Acceptance boundary: PTY signal handling
  Trigger or inspection target: pty_signal_foreground() with master fd TIOCGPGRP
  Expected observable result: foreground TUI 프로세스 그룹(PGID)에 SIGWINCH 시그널이 도달함
  Authoritative readback: foreground child SIGWINCH trap receipt
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Ticket Scope creates | pty_signal_foreground in pty.c
  External condition: None

- Outcome: 세션 복원 시 클라이언트 terminal.reset()이 발생하지 않아 alternate screen과 키 모드가 보존되고, diagnostics 미지정 시 rAF 루프가 돌지 않는다.
  Acceptance boundary: frontend xterm component
  Trigger or inspection target: html/src/components/terminal/xterm/index.ts
  Expected observable result: resumed 상태에서 terminal.reset() 미호출, diagnosticsEnabled=false일 때 requestAnimationFrame 미호출
  Authoritative readback: inline.html bundle inspection and browser execution
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | html/src/components/terminal/xterm/index.ts
  External condition: None
  UI rendered state and interaction readback: alternate screen preservation and zero-rAF loop when diagnostics disabled

- Outcome: 실행 중 데몬 백업, 단일 RC 바이트열 고정, 7684 스테이징 검증 후 원자적 교체 및 단 1회 재기동으로 3중 드리프트가 완전히 해소된다.
  Acceptance boundary: production daemon process and disk binaries
  Trigger or inspection target: /proc/$LIVE_PID/exe backup and /proc/$NEW_PID/exe hash verification
  Expected observable result: 실행 데몬 바이너리 해시가 빌드된 RC_TTYD와 100% 일치하고 Funnel 7683 서비스 정상 응답
  Authoritative readback: sha256sum /proc/$NEW_PID/exe == sha256sum ~/.local/bin/ttyd == RC_TTYD and sha256sum ~/.local/share/webterm/index.html == RC_HTML (revalidated by sha256sum -c SHA256SUMS.txt)
  Disposition: Independent
  Independent verification required: yes
  Acceptance surface: Existing | /home/user01/.local/bin/ttyd and /home/user01/.local/share/webterm/index.html
  External condition: None

## Behavior Authorities

- docs/planning/behavior/lifecycles/session-reconnect-lifecycle.md | Scope: webterm session reconnect and 9-hour grace lifecycle
- docs/planning/behavior/invariants/pty-continuous-drain.md | Scope: non-blocking PTY read and flow control decoupling invariants

## UI / UX

Bounded rendered contract:
- 390px 포트레이트 무스크롤 단일 행 하단 툴바(TAB, Shift, 화살표, Enter, ESC, CTRL, 폰트 조절, 전체화면)의 기존 레이아웃 및 스타일을 엄격히 보존함.
- 터치/모바일 기기 로드 시 가상 키보드 자동 팝업을 방지하고 툴바 버튼 조작 시 터미널 입력을 blur하여 포커스 간섭을 차단함.
- `fresh` 세션 시작 시에만 `terminal.reset()`을 수행하고, `resumed` 세션 복원 시에는 `terminal.reset()`을 호출하지 않아 alternate screen 렌더링을 보존함.
- `?diagnostics=1` 파라미터가 없는 환경에서는 requestAnimationFrame 계측 루프를 실행하지 않음.
- 이 Spec 자체가 범위 내 UI 권한으로 기능함 (this Spec itself).

## Open Questions

None
