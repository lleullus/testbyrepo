# Web Terminal Customization

## Baseline

- Upstream project: `https://github.com/tsl0922/ttyd.git`
- Upstream tag: `1.7.7`
- Baseline commit: `40e79c706be14029b391f369bee6613c31667abb`
- Custom branch: `custom/android-mobile-toolbar`

## Purpose

Maintain the custom ttyd 1.7.7 server and frontend used by the Android Web Terminal without changing the existing Tailscale Funnel route. The server and browser bundle form one versioned session-protocol unit.

## Customized source

- `src/server.c`
  - preserve the five-second WebSocket probe cadence while allowing a 30-second PONG/valid-traffic grace period before closing a live terminal
- `src/protocol.c`, `src/server.h`
  - retain resumable sessions for nine hours by default; `TTYD_RECONNECT_GRACE` accepts values from 1 through 32400 seconds
  - use session wire protocol v3; distinguish explicit create from resume, reject v1/v2/legacy/unknown resume requests without spawning, and report created/attached/checking/conflict/displaced/expired/exited/unknown states
  - when an otherwise valid resume finds an attached owner, keep at most one contender and send that owner one native WebSocket Ping within two seconds; an exact Pong within ten seconds preserves the owner and returns an explicit Takeover offer, while timeout detaches the stale transport before attaching the contender
  - accept Takeover only as a generation-bound compare-and-swap from that offer; attach the requester to the same process, terminate the previous browser as displaced, and prevent automatic reclaim
  - govern output backlogs with a finite 8 MiB (`SESSION_BACKLOG_MAX = 8388608` bytes) rolling circular buffer; older output beyond 8 MiB is truncated cleanly without blocking the child PTY pipe and without dropping into full-redraw wipeouts
  - report truncation status (`truncated: true` and `droppedBytes`) explicitly in `SET_SESSION_STATE` and `REPLAY_END`
  - preserve exit codes, exit signals, and final 8 MiB output tails in `EXITED_RETAINED` state for disconnected sessions across the 32400-second (9-hour) lifecycle; allow results readback with zero new shell spawns, zero PTY input bytes, and without extending the original 9-hour deadline
  - synchronize foreground TUI layout via `TIOCGPGRP` foreground PGID signal forwarding (`SIGWINCH`) with fallback to session root PID; eliminate destructive Full RIS (`terminal.reset()`) and fabricated keystrokes
  - enforce owned process tree finite cleanup via 2-stage escalation: `SIGHUP` followed by a 3-second grace timer and `SIGKILL`, auditing `/proc` before transitioning to `PURGED` (retaining `TERMINATING` if any process remains unkillable)
  - manage resource accounting and admission limits (`TTYD_MAX_SESSIONS`, `TTYD_MAX_RETAINED_SESSIONS`, `TTYD_MAX_TOTAL_BUFFER_BYTES`); reject new session creation requests honestly (`rejected_capacity`) when limits are reached without silent eviction of protected sessions
- `html/src/components/app.tsx`
  - bind one 128-bit session ID to the tab and normalized endpoint in `sessionStorage`; a missing or unusable value requires an explicit new-session action
- `html/src/components/terminal/index.tsx`
  - expose input-owner snapshots through the single-row toolbar: TAB / Shift / arrows / Enter / ESC / CTRL / font-size / fullscreen
  - prevent toolbar pointer/mouse focus transfer so an active Android keyboard and composition remain available; inactive toolbar use does not focus xterm
  - use the input owner for mutually exclusive one-shot Shift/CTRL transitions and keep font size in the 8..32 range
- `html/src/components/terminal/xterm/index.ts`, `html/src/components/terminal/xterm/addons/overlay.ts`
  - use one generation-scoped token/socket/retry/heartbeat/input coordinator and block every input/resize sender while the server reports `checking` and until replay and input readiness are acknowledged
  - classify direct terminal activation separately from moved/cancelled touch, selection, links, controls and overlays; only a valid ready direct activation focuses the textarea
  - own composition, beforeinput/input and paste at ancestor capture before xterm's textarea handlers; commit current-generation text once, keep composing Enter commit-only, make composing ESC local-only, and discard stale/cancelled transactions without replay
  - clear pending modifiers on paste/composition/lifecycle transitions; apply CTRL only to one ordinary alphabetic input and never to paste or IME text
  - keep owner checking inside the existing 30-second connection attempt and 60-second monotonic recovery window; recovery gestures join an in-flight check instead of restarting its deadline
  - preserve xterm screen state during recovery; no reconnect reset or invented Enter/ESC/Ctrl+L input
  - make the recovery overlay and toolbar Enter start the same local-only recovery action after the 60-second automatic window
  - use one coalesced fit path for viewport, container, fullscreen and font changes; hidden/zero geometry never overwrites or reaches the server
  - display honest truncation notice `이전 출력이 절사됨 (최신 8 MiB 보존)` whenever output backlog was truncated
  - support read-only `exited_retained` result inspection displaying `작업 완료 (종료 코드: N)` and final output with zero PTY input allowed and an explicit `Start New Session` action
  - display capacity rejection notice and retry action when server capacity limits are reached
- `html/src/style/index.scss`
  - compact 35px single-row bottom toolbar layout sized for 390px and shrinkable at 360px without horizontal scrolling, with Safe Area padding
- `html/src/template.html`
  - mobile viewport configuration with `interactive-widget=resizes-content`
- `staging/check_staging.py`
  - portrait/landscape single-row UI, direct-focus and toolbar-focus preservation checks
  - PTY byte checks for Enter, TAB, Shift+Tab, normal/application arrows, Shift+arrows, CTRL/ESC, paste and synthetic composition mechanics
  - modifier cleanup, font 8..32 and fullscreen regression checks
- `staging/check_fresh_session.py`, `staging/check_reconnect.py`, `staging/check_protocol_edges.py`, `staging/check_omp_reconnect.py`, `staging/check_exit_lifecycle.py`, `staging/check_server_hardening.py`
  - exercise wire v3 create/resume, native Ping/Pong ownership, explicit Takeover/displaced behavior, stale and concurrent offers, bounded owner-check races, state/replay preservation, browser liveness, manual recovery with zero PTY-byte leakage, and safe local OMP screen replay

## Runtime policy

Production runtime files remain outside this repository:

- frontend artifact: `/home/user01/.local/share/webterm/index.html`
- session launcher: `/home/user01/.local/share/webterm/session.sh`
- ttyd binary: `/home/user01/.local/bin/ttyd`
- production port: `7683`
- staging port: `7684`

Resumable sessions default to a nine-hour reconnect grace. `TTYD_RECONNECT_GRACE` may shorten that window for isolated testing, up to 32400 seconds. Browser recovery retries for 60 seconds, probes visible sessions every five seconds, and treats 30 seconds without the matching application heartbeat reply as dead.

An occupied-session resume does not treat registry ownership alone as proof of life. It enters non-ready `checking`, allows two seconds for a single native control Ping to be written, and then observes the current owner for the exact Pong for ten seconds. A matching timely Pong produces `conflict`; timeout detaches only that stale transport and attaches the waiting contender to the same process. A contender close, owner close, process exit, third contender, timer failure, send failure or shutdown settles and clears the bounded check. These local limits do not change the global WebSocket validity policy or the 32400-second session grace.

Keep the server's default five-second WebSocket probe cadence and 30-second validity grace. Native owner-check Pong proves only the old transport's current round trip; application heartbeat success likewise proves socket liveness only. Session attachment, replay settlement and input readiness remain separate states.

Do not change or reset Tailscale Funnel. Production must remain `/terminal -> 127.0.0.1:7683` at the existing external URL.


## Supervision and Logrotate

- systemd user service unit: `/home/user01/.config/systemd/user/webterm.service`
  - supervises the candidate ttyd daemon, external bundle, session launcher, and `TTYD_RECONNECT_GRACE=32400`
  - restart policy: `Restart=on-failure`, `RestartSec=2s`, `StartLimitIntervalSec=60s`, `StartLimitBurst=5`
  - logging target: `StandardOutput=append:/home/user01/.local/state/webterm/ttyd.log`
  - WSL2 prerequisite: user lingering enabled via `loginctl enable-linger user01` (`Linger=yes`), with `XDG_RUNTIME_DIR=/run/user/1000` for user-manager access
  - note: in-memory resumable sessions and retained results do not survive daemon restarts; daemon restart resets in-memory session tables, and previous session IDs will honestly report `unknown`/`expired`
- logrotate configuration: `/home/user01/.config/logrotate/webterm.conf`
  - rotater policy for `/home/user01/.local/state/webterm/ttyd.log`: `size 10M`, `rotate 5`, `compress`, `missingok`, `notifempty`, `copytruncate`
  - copytruncate ensures the live daemon continues logging uninterrupted without requiring daemon restarts or HUP signals
## Build

Build the compatible browser and server candidates from the same working tree. From `html/`:

```bash
corepack yarn inline
```

Then build the configured out-of-tree C target, for example:

```bash
cmake --build build --target ttyd
```

The standalone browser artifact is `html/dist/inline.html`; it must be paired with the `build/ttyd` produced from the same protocol sources.

## Staging

Run an isolated candidate on an unused non-production port with explicit candidate paths:

```bash
TTYD_RECONNECT_GRACE=90 TTYD_DIAGNOSTICS=1 \
  ./build/ttyd -W -i 127.0.0.1 -p 7684 \
  -I ./html/dist/inline.html /home/user01/.local/share/webterm/session.sh
```

Do not connect staging port 7684 to Funnel. Do not use the production binary as evidence for candidate server behavior.

Run the targeted protocol and browser harnesses with explicit `TTYD_BIN` and `WEBTERM_TEST_INDEX` when their defaults are not the intended candidate. The harnesses allocate their own ports where documented; never point them at 7683.

## Production deployment

The session protocol is a hard-atomic server/browser cutover. A frontend-only copy is incompatible and must not be exposed. Deployment requires separate current authorization, a verified maintenance boundary for existing in-memory sessions, and an atomic replacement of the compatible ttyd binary and `index.html`, followed by `/terminal`, `/terminal/token`, `/terminal/ws`, session continuity and Android recovery readback. This repository build procedure does not authorize a port-7683 restart or Funnel change.

## Android focus and input policy

Toolbar interaction and terminal typing interaction must stay separate.

- Page load, reconnect, page return and inactive toolbar use do not auto-focus xterm input.
- A ready terminal body's direct activation may focus the textarea; scrolling, moved/cancelled touch, selection, links and controls do not count as typing activation.
- Toolbar pointer/mouse down prevents native focus transfer. When typing is active, toolbar controls preserve textarea focus and keyboard/composition availability; they never call blur or `navigator.virtualKeyboard.hide()`.
- Shift and CTRL are mutually exclusive owner state. Shift applies once to TAB/arrows; CTRL applies once to an ordinary alphabetic input. Body activation clears Shift and preserves CTRL.
- Paste and composition clear pending modifiers. Paste is never CTRL-transformed.
- Composition text is sent only from the capture transaction. Composing Enter commits without CR/LF; composing ESC cancels locally without remote Escape. Disconnect, hide, displaced owner or a generation change invalidates pending text without replay.
- Arrow buttons follow xterm's `applicationCursorKeysMode`; Shift+arrow uses xterm's modifier form.
- The actual Android Chrome/IME behavior must be checked with a short functional checklist and PTY readback; desktop synthetic composition is supporting mechanics evidence only.

## Rollback

Rollback must restore a mutually compatible ttyd binary and `index.html`; restoring only one side is not a valid protocol rollback. Because in-memory resumable sessions do not survive daemon replacement, any production restart or rollback requires a separately approved maintenance boundary and explicit accounting for existing sessions. Funnel and `session.sh` are not rollback targets unless changed by a separate authorized task.
