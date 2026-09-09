# Web Terminal Customization

## Baseline

- Upstream project: `https://github.com/tsl0922/ttyd.git`
- Upstream tag: `1.7.7`
- Baseline commit: `40e79c706be14029b391f369bee6613c31667abb`
- Custom branch: `custom/android-mobile-toolbar`

## Purpose

Maintain the custom ttyd 1.7.7 frontend used by the Android Web Terminal without changing the existing Tailscale Funnel route or fresh-shell runtime model.

## Customized source

- `src/server.c`
  - preserve the five-second WebSocket probe cadence while allowing a 30-second PONG/valid-traffic grace period before closing a live terminal
- `src/protocol.c`
  - retain resumable sessions for six hours by default; `TTYD_RECONNECT_GRACE` accepts values from 1 through 21600 seconds
- `html/src/components/terminal/index.tsx`
  - single-row compact bottom toolbar: TAB / Shift / arrows / Enter / ESC / CTRL / font-size / fullscreen
  - Shift as a one-shot modifier for TAB and arrow keys
  - Enter sends CR and clears armed Shift/CTRL state
  - CTRL clears when TAB or an arrow is used because Ctrl+TAB / Ctrl+arrow are not implemented
  - terminal blur before toolbar actions
  - keyboard-safe toolbar interaction
- `html/src/components/terminal/xterm/index.ts`
  - mobile/touch auto-focus policy
  - terminal blur and control-data handling
  - TAB / Shift+Tab and Enter byte sequences
  - normal/application cursor-mode arrows and Shift+arrow sequences
- `html/src/style/index.scss`
  - compact single-row bottom toolbar layout sized to fit 390px portrait without horizontal scrolling
- `html/src/template.html`
  - mobile viewport configuration
- `staging/check_staging.py`
  - portrait/landscape single-row UI and focus checks
  - PTY byte checks for Enter, TAB, Shift+Tab, normal/application arrows and Shift+arrows
  - modifier cleanup on Enter/TAB/arrows plus CTRL, font resize and fullscreen regression checks
- `staging/check_fresh_session.py`
  - fresh-session regression check

## Runtime policy

Production runtime files remain outside this repository:

- frontend artifact: `/home/user01/.local/share/webterm/index.html`
- session launcher: `/home/user01/.local/share/webterm/session.sh`
- ttyd binary: `/home/user01/.local/bin/ttyd`
- production port: `7683`
- staging port: `7684`

`session.sh` must continue to start a fresh login shell per ttyd connection. Do not add tmux or session reuse.
Resumable sessions default to a six-hour reconnect grace. `TTYD_RECONNECT_GRACE` may shorten that window for testing or operations, up to 21600 seconds.

Keep the default five-second WebSocket probe cadence. The 30-second validity grace is deliberate: browser rendering, WSL forwarding, or a transient network handoff can delay a valid PONG long enough to otherwise discard a live OMP terminal. Do not shorten it without reproducing and verifying the disconnect behavior.

Do not change or reset Tailscale Funnel. Production must remain `/terminal -> 127.0.0.1:7683` at the existing external URL.

## Build

From `html/`:

```bash
yarn check
yarn inline
```

The deployable standalone artifact is:

```text
html/dist/inline.html
```

## Staging

Copy the built artifact to:

```text
staging/index.html
```

Run staging without a max-client limit:

```bash
/home/user01/.local/bin/ttyd \
  -W \
  -i 127.0.0.1 \
  -p 7684 \
  -I /home/user01/project/webterm/ttyd-1.7.7/staging/index.html \
  /home/user01/.local/share/webterm/session.sh
```

Do not connect staging port 7684 to Funnel.

Run:

```bash
python3 staging/check_staging.py
python3 staging/check_fresh_session.py
```

## Production deployment

Only after staging passes:

1. Back up `/home/user01/.local/share/webterm/index.html`.
2. Copy `html/dist/inline.html` to `/home/user01/.local/share/webterm/index.html`.
3. Restart production ttyd on port 7683 with the existing runtime paths and without `-m`.
4. Verify the external Funnel URL, fresh sessions, toolbar behavior, fullscreen, PTY resize and Android keyboard behavior.

A source-tree relocation by itself does not require a production restart or production artifact replacement.

## Android focus policy

Toolbar interaction and terminal typing interaction must stay separate.

- Page load on touch/mobile: do not auto-focus xterm input.
- Toolbar actions: blur terminal input and do not refocus it afterward.
- Terminal body tap: may focus xterm and summon the Android keyboard.
- Shift is a toolbar-only one-shot modifier for TAB and arrow keys; terminal body tap clears it.
- CTRL and Shift are mutually exclusive when arming modifiers.
- TAB or an arrow clears an armed CTRL state; Ctrl+TAB and Ctrl+arrow are intentionally unsupported.
- Arrow buttons must follow xterm's `applicationCursorKeysMode`; Shift+arrow uses xterm's modifier form.
- `navigator.virtualKeyboard.hide()` may be used only as a best-effort helper; correct focus ownership is the primary mechanism.

## Rollback

Frontend rollback is limited to restoring the previous production `index.html` and restarting ttyd. Funnel and `session.sh` are not rollback targets unless they were explicitly changed in a separate task.
