# PLAN-001: Webterm 세션 유예 9시간 확장 및 무단절 PTY 복구 실행 계획서 (v8 - 오라클 슬롯 3 PTY 리소스 라이프사이클 완전 무결본)

Project-Root: /home/user01/project/webterm/ttyd-1.7.7
Work-Slug: webterm-session-grace-recovery
Ticket: docs/planning/work/webterm-session-grace-recovery/tickets/TICKET-001.md
Parent-Spec: docs/planning/work/webterm-session-grace-recovery/SPEC.md

## 1. Product Contracts and Current Evidence

- **적용 티켓**: `TICKET-001.md` (Webterm 세션 유예 9시간 확장 및 무단절 PTY 복구 릴리즈)
- **적용 부모 스펙**: `SPEC.md`
- **적용 행동 권한**:
  - `docs/planning/behavior/lifecycles/session-reconnect-lifecycle.md` (9시간 세션 라이프사이클)
  - `docs/planning/behavior/invariants/pty-continuous-drain.md` (PTY continuous drain 불변성)
- **기존 소스 및 런타임 근거**:
  - `src/protocol.c`: `SESSION_GRACE_MAX_SECONDS` (현재 6*60*60), `session_grace_ms()`, `process_read_cb()`, `attach_process()`, `session_buffer_append()`, `callback_tty()`, `spawn_process()`
  - `src/pty.c` 및 `src/pty.h`: `process_init()`, `pty_spawn()`, `read_cb()`, `process_free()`, `async_free_cb()`, `pty_write()`, `pty_pause()`, `pty_resume()`
  - `src/server.h`: `struct pss_tty`, `struct tty_session`
  - `html/src/components/terminal/xterm/index.ts`: `open()`, `initListeners()`, `sendFlowControl()`
  - `CUSTOMIZATION.md`: 6시간 기술 문서
  - `staging/check_protocol_edges.py`: 프로토콜 회귀 테스트

## 2. Obligations, Preserved Paths, Scope, and Non-Goals

### 달성 의무
1. `SESSION_GRACE_MAX_SECONDS` 9시간(`9 * 60 * 60 = 32,400초`) 확장 및 `CUSTOMIZATION.md` 동기화.
2. `pty.c` 리소스 라이프사이클 무결성 및 센티널 초기화:
   - `process_init()`에서 `process->pty = -1; process->pid = -1; process->async_initialized = false; process->thread_started = false;`를 명시적으로 초기화하여 `forkpty()` 이전 실패 시 caller가 `process_free()`를 호출해도 fd 0이 오인 해제되지 않도록 보장.
   - `pty_spawn()`의 명시적 **Spawn Transaction 3단계 커밋/롤백 상태 머신** 구현:
     - `SPAWN_COMMITTED` 정의: `pipe/fd 복제 성공` -> `uv_read_start 성공` -> `uv_async_init 성공` -> `uv_thread_create 성공`의 모든 단계를 통과한 경우에만 성립 (`process->thread_started = true; return 0;`).
     - `uv_async_init` 경계 기준 **실패 소유권(Failure Ownership) 이원화**:
       - `uv_async_init` 이전 실패 (`!process->async_initialized`):
         - in/out 파이프 `uv_close` 및 NULL화 후 `error_master`로 분기: `close(master)`, `uv_kill(pid, SIGKILL)`, `waitpid(pid, NULL, 0)`, `process->pty = -1`, `process->pid = -1`.
         - 호출자 `spawn_process()`가 `if (!process->async_initialized) { process_free(process); free(process); }`로 즉시 객체 해제.
       - `uv_thread_create` 실패 (`process->async_initialized == true`):
         - `uv_read_stop(process->out)` 호출.
         - master fd double-close 방지 및 단일 cleanup: child 프로세스를 kill/reap (`uv_kill(pid, SIGKILL); waitpid(pid, NULL, 0); process->pid = -1;`).
         - 임베디드 async 핸들 메모리 use-after-free 방지를 위해 `uv_close((uv_handle_t *)&process->async, async_free_cb);` 호출 (close 완료 시 libuv가 `async_free_cb`를 통해 `free(process)`를 호출하도록 소유권 위임).
         - `process_free(process);`를 호출하여 master fd(`process->pty`) 및 in/out 파이프를 정확히 1회 정리 (이후 `error_master`로 재진입하지 않고 즉시 에러 코드 반환).
         - 호출자 `spawn_process()`는 `async_initialized`이므로 `free(process)`를 수행하지 않음.
     - `process_free()`에서는 `process->tid != 0` 대신 명시적 `if (process->thread_started)` 플래그로만 `uv_thread_join()` 수행.
3. 정상 read 콜백의 `uv_read_stop()` 및 `attach_process()`의 `pty_pause()`를 전면 제거하여 PTY 출력을 상시 continuous drain함.
4. `pss->pty_buf`와 `session->backlog`를 세션 단일 8MB bounded output queue로 통합하고, `unconsumed = output_len - output_offset` 기준으로 용량을 계산하며 compaction 시 `output_len = unconsumed; output_offset = 0;`으로 정합성을 닫음.
5. `session_output_append()`에 최상단 `if (session->needs_redraw)` 상태 게이트를 두어 overflow 발생 후부터 복구 성공 시까지 모든 후속 PTY 출력을 일관되게 discard(폐기) 모드로 유지.
6. `Command.PAUSE` 수신 시 WS 전송만 보류(`pss->client_flow_paused = true`)하고 PTY read는 절대 정지하지 않음.
7. master fd `TIOCGPGRP`로 foreground PGID를 획득하여 `SIGWINCH`를 전송하는 `pty_signal_foreground()`를 `src/pty.h`에 선언하고 Linux 구현 및 Windows safe stub 제공. `ESRCH` 발생 시 동일 PGID 여부와 무관하게 1회 재시도.
8. 재접속 또는 클라이언트 소비 재개 시 `needs_redraw == true`이면 오래된 큐를 비우고 `pty_signal_foreground()`가 `true`를 반환한 성공 시점에만 `session->needs_redraw = false;`로 복구 완료 처리 (단일 recovery helper). 실패 시 플래그 유지 및 discard 상태 지속.
9. `fresh` 세션에서만 `terminal.reset()` 수행, `resumed` 복원 시에는 reset 금지.
10. `xterm/index.ts` rAF 루프를 `diagnosticsEnabled` 조건부 실행으로 완전 격리.
11. `resume_reset`, `terminal_recovery`, `TerminalRecovery` JSON capability, `TTYD_TERMINAL_RECOVERY` env, `resumed-reset[-v1]` state, `resetGate`를 백엔드/프론트엔드/테스트 전반에서 전면 제거하고 `needs_redraw` 단일화.
12. 실행 중 데몬(`/proc/$LIVE_PID/exe`) 백업, 단일 RC 해시 고정(`RC_TTYD`, `RC_HTML`), staging/promotion 직전 `sha256sum -c` 검증, 7684 스테이징 검증 후 원자적 교체 및 단 1회 재기동.

### 보존 경로 및 불변성
- 390px 단일 행 하단 툴바 레이아웃 및 가상 키보드 방지 포커스 정책 엄격 보존
- `session.sh`의 신규 셸 기동 원칙 및 Tailscale Funnel 7683 라우팅 무변경

### Non-Goals
- WebSocket ping/pong 주기 변경, Sixel 복원, tmux 도입

## 3. Causal Hypotheses, Competing Explanations, and Discriminating Checks

- **가설 1 (호스트 프로세스 정지 원인)**:
  - 관측: 모바일 단절/슬립 시 호스트의 OMP/빌드 작업이 정지됨.
  - 원인: `protocol.c:371-374` 및 `pty.c:65`에서 PTY 출력을 읽을 때마다 `uv_read_stop()`을 호출하고 WS writable 콜백이 `pty_buf`를 소비할 때까지 `pty_resume()`을 지연시키며, `attach_process()` 진입 시에도 `pty_pause()`를 호출함.
  - 대안 설명: 자식 프로세스가 stdin을 기다려 멈춘 것인가? -> 반증: stdout 리다이렉션 시 정상 완료됨. 즉 stdout slave PTY 버퍼 포화가 원인임.
  - 판별 검증: 클라이언트 PAUSE 상태에서 10MB 출력 스크립트 구동 시 프로세스가 block되지 않고 정상 종료 코드 0 및 완료 마커를 파일에 쓰는지 확인 (RESUME 전 확인).
- **가설 2 (SIGWINCH 전달 실패 원인)**:
  - 관측: 세션 복원 후 TUI(vim/htop) 화면이 갱신되지 않음.
  - 원인: `pty_kill(-process->pid, SIGWINCH)`는 셸 프로세스 그룹에만 신호를 보내고 foreground TUI process group에는 도달하지 않음.
  - 대안 설명: TUI가 SIGWINCH를 무시하는가? -> 반증: 수동으로 `kill -WINCH <vim_pid>` 실행 시 즉시 redraw됨.
  - 판별 검증: foreground 자식 프로세스에서 `os.tcgetpgrp(0)`를 확인하고 `trap 'echo TRAP_OK' WINCH` 등록 후 복구 시그널 수신 확인.

## 4. State Owners, Shared Interfaces, and Affected Callers

- **세션 큐 소유자**: `struct tty_session` 내 `output_buf`, `output_len`, `output_offset`, `output_cap`, `needs_redraw`
- **시그널 인터페이스**: `src/pty.h` 내 `bool pty_signal_foreground(pty_process *process, int sig);` 선언 및 `src/pty.c` 구현
- **프로세스 센티널 및 라이프사이클 플래그**: `process->pty` (-1 센티널), `process->pid` (-1 센티널), `process->async_initialized`, `process->thread_started`
- **프로세스 객체 최종 해제(final free) 소유권**:
  - `uv_async_init` 이전 실패: 호출자 `protocol.c:spawn_process()` (`process_free(process); free(process);`)
  - `uv_async_init` 이후 실패 및 정상 커밋: `pty.c:async_free_cb()` (`free((uv_async_t *)handle->data)`)
- **영향받는 호출자**:
  - `src/protocol.c`: `process_read_cb`, `callback_tty` (`LWS_CALLBACK_SERVER_WRITEABLE`, `LWS_CALLBACK_RECEIVE`), `attach_process`, `session_start_expiry`, `spawn_process`
  - `html/src/components/terminal/xterm/index.ts`: `open`, `initListeners`

## 5. Change Structure and Step-by-Step Implementation

### Step 1: 세션 유예 시간 상수 및 문서 수정
- `src/protocol.c`:
  ```c
  #define SESSION_GRACE_MAX_SECONDS (9 * 60 * 60)
  #define SESSION_GRACE_DEFAULT_MS (SESSION_GRACE_MAX_SECONDS * 1000ULL)
  ```
- `CUSTOMIZATION.md`: 6시간 -> 9시간, 21600 -> 32400초 동기화.

### Step 2: PTY 프로세스 센티널 및 트랜잭션 롤백 무결성 구현
- `src/pty.h`:
  - `struct pty_process`에 `bool async_initialized;`, `bool thread_started;` 추가.
- `src/pty.c`:
  - `process_init()` 센티널 초기화:
    ```c
    pty_process *process = xmalloc(sizeof(pty_process));
    memset(process, 0, sizeof(pty_process));
    process->ctx = ctx;
    process->loop = loop;
    process->argv = argv;
    process->envp = envp;
    process->columns = 80;
    process->rows = 24;
    process->exit_code = -1;
    process->pty = -1; // 센티널: fd 0 오인 close 방지
    process->pid = -1;
    process->async_initialized = false;
    process->thread_started = false;
    return process;
    ```
  - `process_free()` 명시적 상태 검사:
    ```c
    #ifndef _WIN32
      if (process->pty >= 0) {
        close(process->pty);
        process->pty = -1;
      }
      if (process->thread_started) {
        uv_thread_join(&process->tid);
        process->thread_started = false;
      }
    #endif
      if (process->in != NULL) {
        uv_close((uv_handle_t *) process->in, close_cb);
        process->in = NULL;
      }
      if (process->out != NULL) {
        uv_close((uv_handle_t *) process->out, close_cb);
        process->out = NULL;
      }
      if (process->argv != NULL) free(process->argv);
      if (process->cwd != NULL) free(process->cwd);
      char **p = process->envp;
      for (; *p; p++) free(*p);
      free(process->envp);
    ```
  - `pty_spawn()` 커밋/롤백 상태 머신:
    ```c
    process->pty = master;
    process->pid = pid;
    process->read_cb = read_cb;
    process->exit_cb = exit_cb;
    process->out->data = process;
    process->paused = true;
    process->async_initialized = false;
    process->thread_started = false;

    // Stage 1: uv_read_start
    int rc = uv_read_start((uv_stream_t *)process->out, alloc_cb, read_cb);
    if (rc != 0) {
        status = rc;
        goto error_pipes;
    }
    process->paused = false;

    // Stage 2: uv_async_init
    process->async.data = process;
    rc = uv_async_init(process->loop, &process->async, async_cb);
    if (rc != 0) {
        status = rc;
        uv_read_stop((uv_stream_t *)process->out);
        goto error_pipes;
    }
    process->async_initialized = true;

    // Stage 3: uv_thread_create
    rc = uv_thread_create(&process->tid, wait_cb, process);
    if (rc != 0) {
        status = rc;
        uv_read_stop((uv_stream_t *)process->out);
        // child 프로세스 회수
        uv_kill(pid, SIGKILL);
        waitpid(pid, NULL, 0);
        process->pid = -1;
        // async handle은 close callback이 final free(process)를 소유하도록 스케줄
        uv_close((uv_handle_t *)&process->async, async_free_cb);
        // master fd 및 파이프 정리 (정확히 1회 정리)
        process_free(process);
        return status; // error_master로 재진입하지 않음 (double-close 원천 차단)
    }
    process->thread_started = true;

    // SPAWN_COMMITTED: 3단계 모두 성공한 경우에만 정상 반환
    return 0;

    error_pipes:
      if (process->in != NULL) {
        uv_close((uv_handle_t *) process->in, close_cb);
        process->in = NULL;
      }
      if (process->out != NULL) {
        uv_close((uv_handle_t *) process->out, close_cb);
        process->out = NULL;
      }
    error_master:
      close(master);
      process->pty = -1;
      uv_kill(pid, SIGKILL);
      waitpid(pid, NULL, 0);
      process->pid = -1;
      return status;
    ```
- `src/protocol.c`의 `spawn_process()` failure path:
  ```c
  if (pty_spawn(process, process_read_cb, process_exit_cb) != 0) {
      lwsl_err("pty_spawn: %d (%s)\n", errno, strerror(errno));
      process->ctx = NULL;
      if (!process->async_initialized) {
          process_free(process);
          free(process); // uv_async_init 이전 실패 시에만 호출자가 final-free 소유
      }
      session_release(session);
      return false;
  }
  ```
- `src/pty.c`의 `read_cb()`:
  - 정상 데이터 수신(`n > 0`) 및 zero-read(`n == 0`) 경로에서 `uv_read_stop()` 호출 전면 제거.
  - `n == 0`은 단순히 `free(buf->base); return;` 처리.
  - `n < 0` (에러/EOF) 경로에서만 `uv_read_stop()` 호출 및 `process->paused = true;` 설정.
  - `attach_process()` 내의 `pty_pause(session->process)` 호출 제거.
- `src/protocol.c`:
  - `resume_pty_if_allowed()` 함수 완전 삭제.
  - `pss->pty_buf` 제거.
  - 세션 단일 큐 구조체 정의:
    ```c
    struct tty_session {
        char *output_buf;
        size_t output_len;
        size_t output_offset; // 이미 WS로 송신 완료된 바이트 위치
        size_t output_cap;
        bool needs_redraw;
        uint64_t dropped_output_bytes;
        ...
    };
    ```
  - 지속 폐기 모드 및 컴팩션이 적용된 `session_output_append(session, data, len)`:
    ```c
    static void session_output_append(struct tty_session *session, const char *data, size_t len) {
        if (session == NULL || len == 0) return;
        // 지속 폐기 상태(DISCARD_UNTIL_REDRAW) 체크
        if (session->needs_redraw) {
            session->dropped_output_bytes += len;
            return;
        }
        size_t unconsumed = session->output_len - session->output_offset;
        if (unconsumed + len > SESSION_BACKLOG_MAX) {
            // 8MB 초과: 큐 즉시 해제 및 discard 모드 진입
            free(session->output_buf);
            session->output_buf = NULL;
            session->output_len = 0;
            session->output_offset = 0;
            session->output_cap = 0;
            session->needs_redraw = true;
            session->dropped_output_bytes += len;
            return;
        }
        // 컴팩션: 소비된 prefix가 있으면 미소비 바이트를 버퍼 선두로 재정렬하고 output_len을 unconsumed로 갱신
        if (session->output_offset > 0) {
            if (unconsumed > 0) {
                memmove(session->output_buf, session->output_buf + session->output_offset, unconsumed);
            }
            session->output_len = unconsumed;
            session->output_offset = 0;
        }
        // 버퍼 확장 및 데이터 추가
        if (session->output_len + len > session->output_cap) {
            size_t new_cap = session->output_cap == 0 ? 64 * 1024 : session->output_cap * 2;
            while (new_cap < session->output_len + len) new_cap *= 2;
            if (new_cap > SESSION_BACKLOG_MAX) new_cap = SESSION_BACKLOG_MAX;
            session->output_buf = xrealloc(session->output_buf, new_cap);
            session->output_cap = new_cap;
        }
        memcpy(session->output_buf + session->output_len, data, len);
        session->output_len += len;
    }
    ```
  - `process_read_cb()`: PTY에서 읽은 데이터를 즉시 `session_output_append()`에 넣고, 클라이언트가 접속되어 있고 `!client_flow_paused`이면 `schedule_writable(client)`만 호출. PTY read는 절대 멈추지 않음.
  - `callback_tty()`의 `LWS_CALLBACK_RECEIVE`:
    - `Command.PAUSE` 수신 시 `pss->client_flow_paused = true;`만 설정 (PTY pause 호출 금지).
    - `Command.RESUME` 수신 시 `pss->client_flow_paused = false; schedule_writable(pss);`.
  - `callback_tty()`의 `LWS_CALLBACK_SERVER_WRITEABLE`:
    - 복구 시도: `if (session->needs_redraw) { session_discard_and_redraw(session, pss); }`
    - `session->output_len > session->output_offset`인 미소비 바이트를 LWS frame으로 전송하고 `output_offset` 전진.

### Step 3: Foreground PGID SIGWINCH 구현 및 시그널 성공 시에만 플래그 해제
- `src/pty.h`:
  ```c
  bool pty_signal_foreground(pty_process *process, int sig);
  ```
- `src/pty.c`:
  ```c
  #ifndef _WIN32
  bool pty_signal_foreground(pty_process *process, int sig) {
      if (process == NULL || process->pty < 0) return false;
      pid_t pgid = 0;
      if (ioctl(process->pty, TIOCGPGRP, &pgid) < 0 || pgid <= 1) return false;
      if (kill(-pgid, sig) == 0) return true;
      if (errno != ESRCH) return false;
      // ESRCH 발생 시 1회 재시도 (동일 PGID 여부 무관하게 kill 재시도)
      pid_t retry = 0;
      if (ioctl(process->pty, TIOCGPGRP, &retry) < 0 || retry <= 1) return false;
      return kill(-retry, sig) == 0;
  }
  #else
  bool pty_signal_foreground(pty_process *process, int sig) { return false; }
  #endif
  ```
- `src/protocol.c`:
  ```c
  static bool session_discard_and_redraw(struct tty_session *session, struct pss_tty *pss) {
      if (session == NULL || session->process == NULL) return false;
      free(session->output_buf);
      session->output_buf = NULL;
      session->output_len = 0;
      session->output_offset = 0;
      session->output_cap = 0;
      
      // SIGWINCH가 성공적으로 전달된 경우에만 needs_redraw를 해제
      if (!pty_signal_foreground(session->process, SIGWINCH)) {
          return false; // needs_redraw 유지, discard 모드 지속
      }
      session->needs_redraw = false;
      return true;
  }
  ```

### Step 4: 백엔드/프론트엔드/테스트 전반의 가상 가드레일 완전 제거
- `src/server.h`: `resume_reset`, `terminal_recovery` 필드 제거.
- `src/protocol.c`:
  - `build_env()`에서 `TTYD_TERMINAL_RECOVERY=1` 주입 제거.
  - JSON auth 파싱에서 `TerminalRecovery` 필드 파싱 제거.
  - `session_state()`를 단순화하여 `pss->resumed ? "resumed" : "fresh"` 2개 상태만 반환 (`resumed-reset[-v1]` 제거).
- `html/src/components/terminal/xterm/index.ts`:
  - `TerminalRecovery: 1` auth 전송 제거.
  - `resetGate`, `beginResetGate`, `clearResetGate`, `maybeCompleteResetGate` 전면 삭제.
  - `state === 'fresh'`일 때만 `this.terminal.reset()` 호출. `state === 'resumed'`에서는 reset 호출 금지.
  - `monitorAnimationFrames` rAF 루프를 `if (this.diagnosticsEnabled)` 조건부로만 시작하도록 격리.
- `staging/check_protocol_edges.py`:
  - `RECOVERY_ENV`, `resumed-reset-v1` 단언 제거.
  - foreground python 프로세스(`os.tcgetpgrp(0)`) 대상 `SIGWINCH` 수신 및 PAUSE 중 10MB 출력 시 호스트 완주 단언으로 갱신.

### Step 5: 단일 RC 파이프라인 및 원자적 릴리즈 시퀀스
1. 실행 중 데몬 보존:
   ```bash
   LIVE_PID=$(ss -ltnp 'sport = :7683' | grep -o 'pid=[0-9]*' | cut -d= -f2)
   mkdir -p ~/.local/state/webterm/releases/20260911-pre-wip
   cp "/proc/$LIVE_PID/exe" ~/.local/state/webterm/releases/20260911-pre-wip/ttyd.live-old
   cp ~/.local/share/webterm/index.html ~/.local/state/webterm/releases/20260911-pre-wip/index.live-old.html
   tr '\0' '\n' <"/proc/$LIVE_PID/environ" | grep '^TTYD_' > ~/.local/state/webterm/releases/20260911-pre-wip/env.ttyd.live.txt || true
   ```
2. 빌드 및 불변 RC 바이트열 고정 (덮어쓰기 방지):
   ```bash
   (cd html && yarn inline)
   (mkdir -p build && cd build && cmake .. && make -j$(nproc))
   RC_DIR="$HOME/.local/state/webterm/releases/20260911-rc1-$(date +%s)"
   mkdir "$RC_DIR"
   cp build/ttyd "$RC_DIR/ttyd"
   cp html/dist/inline.html "$RC_DIR/index.html"
   (cd "$RC_DIR" && sha256sum ttyd index.html > SHA256SUMS.txt)
   chmod -R a-w "$RC_DIR" # 쓰기 금지 동결
   ```
3. 스테이징(7684)에 동일 바이트열 승격 및 사전 검증:
   ```bash
   (cd "$RC_DIR" && sha256sum -c SHA256SUMS.txt)
   cp "$RC_DIR/index.html" staging/index.html
   cmp -s "$RC_DIR/index.html" staging/index.html
   TTYD_BIN="$RC_DIR/ttyd" python3 staging/check_protocol_edges.py
   python3 staging/check_fresh_session.py
   ```
4. 동일 파일시스템 내 임시 파일 배치 및 서비스 중단 하의 atomic rename:
   ```bash
   (cd "$RC_DIR" && sha256sum -c SHA256SUMS.txt) # 프로덕션 배포 직전 재검증
   cp "$RC_DIR/index.html" ~/.local/share/webterm/.index.html.new
   cp "$RC_DIR/ttyd" ~/.local/bin/.ttyd.new
   chmod 0755 ~/.local/bin/.ttyd.new
   
   kill -TERM "$LIVE_PID"
   while ss -ltnp 'sport = :7683' | grep -q ttyd; do sleep 0.1; done
   
   mv ~/.local/share/webterm/.index.html.new ~/.local/share/webterm/index.html
   mv ~/.local/bin/.ttyd.new ~/.local/bin/ttyd
   
   nohup /home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 \
     -I /home/user01/.local/share/webterm/index.html \
     /home/user01/.local/share/webterm/session.sh \
     >> /home/user01/.local/state/webterm/ttyd.log 2>&1 &
   ```
5. 최종 해시 Readback:
   - `sha256sum /proc/$NEW_PID/exe == sha256sum ~/.local/bin/ttyd == RC_TTYD`
   - `sha256sum ~/.local/share/webterm/index.html == RC_HTML`
   - `sha256sum -c $RC_DIR/SHA256SUMS.txt` 재검증 통과

## 6. Implementation Self-Check and Acceptance Path

1. **Flow 1 검사 (Grace)**:
   - 소스 상수 확인: `SESSION_GRACE_MAX_SECONDS == (9 * 60 * 60)`
   - `TTYD_RECONNECT_GRACE=32400` 주입 시 타이머 정상 가동 확인
2. **Flow 2 검사 (Continuous Drain)**:
   - WebSocket 클라이언트 연결 -> `Command.PAUSE` 전송 -> 백그라운드에서 10MB 출력 프로세스 실행 -> **RESUME 전에** 프로세스 정상 종료(exit 0) 및 완료 파일 생성 확인
3. **Flow 3 검사 (Foreground SIGWINCH)**:
   - 대화형 셸 내에서 별도 foreground python 프로세스(`os.tcgetpgrp(0)`) 실행 -> 9MB burst 출력으로 overflow 유발 -> disconnect -> reconnect -> foreground child의 `SIGWINCH` trap 확인
4. **Flow 4 검사 (xterm reset & rAF 브라우저 실행 검증)**:
   - `inline.html` 번들 내 `TerminalRecovery` 문자열 부재 확인
   - 브라우저 실행 검증: `resumed` 접속 시 alternate screen 보존 및 `diagnosticsEnabled=false`일 때 requestAnimationFrame 미호출 확인
5. **Flow 5 검사 (릴리즈 해시 일치)**:
   - `sha256sum /proc/$NEW_PID/exe == sha256sum ~/.local/bin/ttyd == RC_TTYD`
   - `sha256sum ~/.local/share/webterm/index.html == RC_HTML`
   - `sha256sum -c $RC_DIR/SHA256SUMS.txt` 재검증 통과
   - `curl -I http://127.0.0.1:7683/` -> HTTP 200

## 7. Permitted Local Discretion and Return Conditions

- **허용되는 로컬 재량**:
  - `session_output_append()` 내 큐 메모리 realloc 상세 단계
  - `session_discard_and_redraw()` 내부 로깅 문구
- **업스트림 반환 조건 (Return to Matt/Scope)**:
  - Linux PTY `TIOCGPGRP`가 WSL 환경에서 예측 불가능한 권한 오류(EPERM 등)를 반환하는 경우
  - 8MB 큐 메모리 제한에 대한 정책적 재검토가 필요한 경우
