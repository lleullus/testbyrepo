# Webterm Session Reconnect Lifecycle

Status: approved
Owner: user01
Scope: webterm session reconnect and 9-hour grace lifecycle

## Research

- `src/protocol.c`: `session_start_expiry()`는 클라이언트 WebSocket 단절 시 타이머를 가동하고, `session_grace_ms()`는 기본값 `SESSION_GRACE_DEFAULT_MS`(9시간 = 32,400초)를 제공함.
- `CUSTOMIZATION.md`: 기본 9시간 재접속 유예와 1~32400초의 `TTYD_RECONNECT_GRACE` 환경변수 지원을 규정함.
- `app.tsx`: 클라이언트는 브라우저 세션 동안 고유한 32바이트 16진수 `resumeId`를 유지함.

## Behavior Model

### States and Transitions
1. `CONNECTED`: WebSocket이 열려 있고 PTY와 클라이언트 간 입출력이 교환되는 상태.
2. `DISCONNECTED_RESTORABLE`: WebSocket이 닫혔으나 9시간 유예 타이머(`uv_timer_t`)가 가동 중인 상태. PTY 자식 프로세스는 계속 실행됨.
3. `RESUMED`: 동일한 `resumeId`를 가진 클라이언트가 9시간 이내에 재접속한 상태. 유예 타이머는 즉시 취소되고 터미널 세션이 복원됨.
   - `needs_redraw == false`: 보존된 8MB 백로그를 클라이언트에 재전송.
   - `needs_redraw == true`: 오래된 백로그는 폐기하고, master fd `TIOCGPGRP`로 foreground PGID에 `SIGWINCH`를 전송하여 TUI 화면 재그리기를 유도.
   - `terminal.reset()`은 호출하지 않음 (alternate screen 및 마우스/커서 모드 보존).
4. `EXPIRED`: 9시간 유예 시간이 경과한 상태. `session_expire_cb`가 실행되어 PTY 자식 프로세스에 시그널(SIGTERM/SIGHUP)을 발송하여 종료하고 세션 리스트에서 완전히 제거함.
5. `FRESH`: 신규 탭 생성 또는 세션 만료 후 재접속하여 새 PTY와 로그인 셸이 기동된 상태. 클라이언트는 `terminal.reset()`을 수행하여 이전 화면 상태를 초기화함.

## Counterexample Stress Test

- **경계 조건 1: 유예 만료 직전 재접속 경합**
  - 해결: `session_cancel_expiry()`가 타이머 핸들을 원자적으로 중단 및 `uv_close`하므로 만료 콜백과 재접속 간의 이중 처리가 방지됨.
- **경계 조건 2: 8MB 초과 후 재접속 시 xterm 모드 오염**
  - 해결: 클라이언트의 강제 `terminal.reset()`(full RIS)을 금지하고, 서버가 foreground PGID에 SIGWINCH만 전달하여 자식 TUI(vim/htop)가 스스로 재출력하도록 보장.

## Product Decision Return

None

## Conclusion

webterm 세션은 9시간 동안 단절 상태에서도 자식 프로세스를 유지하며, 9시간 내 재접속 시 이전 터미널 모드를 파괴하지 않고 정직하게 복구되며, 9시간 초과 시 자식 프로세스를 깔끔하게 회수한다.
