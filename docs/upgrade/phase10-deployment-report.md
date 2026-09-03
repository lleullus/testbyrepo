# Phase 10 production deployment and rollback report

Captured: 2026-09-03 (Asia/Seoul)

## Result

**PASS — the Phase 9 native candidate and Phase 8 xterm 6 frontend are now deployed on the production localhost listener and are passing local and Funnel smoke/regression checks.**

No Funnel routing rule or session launcher content was changed.

## Deployment boundary

Production command before and after deployment:

```text
/home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 -I /home/user01/.local/share/webterm/index.html /home/user01/.local/share/webterm/session.sh
```

Old process:

```text
PID: 3678814
started: 2026-08-28 14:40:37 +09:00
```

New process:

```text
PID: 1204576
started: 2026-09-03 22:18:17 +09:00
listener: 127.0.0.1:7683
```

The running executable was verified through `/proc/1204576/exe` after restart.

## Before/after artifact identity

### ttyd

Before:

```text
path: /home/user01/.local/bin/ttyd
sha256: 72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c
```

After:

```text
path: /home/user01/.local/bin/ttyd
sha256: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
running /proc executable sha256: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
```

The deployed binary is the byte-identical reproducible Phase 9 x86_64-musl candidate built from:

- zlib 1.3.2
- json-c 0.19
- libuv 1.52.1
- Mbed TLS 3.6.7
- libwebsockets 4.5.8

### frontend

Before:

```text
path: /home/user01/.local/share/webterm/index.html
sha256: 38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887
```

After:

```text
path: /home/user01/.local/share/webterm/index.html
sha256: 8083f8add847fa2f43ff9dcb84dcc4cf08a2427aa7bb498c4c02c5de0cc45027
```

The after value matches `staging/index.html` used by the Phase 8/9 regression gates.

### session launcher

The launcher was not changed.

```text
path: /home/user01/.local/share/webterm/session.sh
sha256: 920f762d66e23e810da22bae10c3eb1c401f6c2d9d2b70fd1288010076d1745c
```

## Backup / rollback set

The pre-deployment production files were copied before any replacement to:

```text
/home/user01/.local/share/webterm/backups/phase10-20260903-2208/
```

Verified backup hashes:

```text
72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c  ttyd
38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887  index.html
920f762d66e23e810da22bae10c3eb1c401f6c2d9d2b70fd1288010076d1745c  session.sh
```

The backup ttyd and backup frontend were also started together on the disposable localhost port 7684. The rollback instance successfully served `/token`, then it was terminated and port 7684 was confirmed free again. This verifies that the preserved files remain a runnable rollback set without temporarily downgrading the live 7683 service.

## Replacement method

The new binary and frontend were first copied to same-filesystem temporary names and their SHA-256/modes were verified. They were then renamed over the production paths, so file replacement itself was atomic.

The old ttyd process continued running from its already-open executable inode during file replacement. It was subsequently terminated with SIGTERM after both new files were in place. Port 7683 was confirmed free before the new process was started with the exact previous command line.

This kept the service interruption limited to the process restart window.

## Local production verification

Immediately after restart:

- `127.0.0.1:7683` was listening under PID 1204576.
- `http://127.0.0.1:7683/token` returned successfully.
- `/proc/1204576/exe` matched the selected Phase 9 SHA-256.
- process command line matched the prior production command.

Process observation after the regression passes:

```text
CPU: approximately 0.1%
RSS: approximately 17.8 MiB
```

### Browser/mobile regression on the real 7683 listener

`WEBTERM_URL=http://127.0.0.1:7683/ python3 staging/check_staging.py`: **PASS**

Verified on the deployed production frontend/backend pair:

- single-row mobile toolbar in portrait and landscape;
- terminal focus/blur behavior;
- exact Enter, Tab, Shift+Tab bytes;
- normal/application/shifted cursor-arrow sequences;
- Ctrl+C, Ctrl+D and Escape behavior;
- font resize and fullscreen behavior.

`WEBTERM_URL=http://127.0.0.1:7683/ python3 staging/check_touch_resize.py`: **PASS**

Latest local observation:

```text
touch viewport: 452 -> 431 -> 452
resize iterations: 20
page errors/unhandled rejections: []
```

`WEBTERM_URL=http://127.0.0.1:7683/ python3 staging/check_xterm6_compat.py`: **PASS**

Verified default renderer, Unicode 11, Image/WebLinks addon smoke, canvas-preference fallback, WebGL load and WebGL context-loss fallback.

## Funnel / external production verification

Existing routing was inspected and left unchanged:

```text
https://desktop-balmtav-1.tail42cd28.ts.net/terminal -> http://127.0.0.1:7683
```

External `/terminal/token`: **PASS**

Direct external WSS session test:

```text
first attach: fresh
same resume id after disconnect: resumed
```

This verifies Funnel HTTPS/WSS routing and the deployed backend's resume protocol through the actual public path.

### External browser/mobile tests

`WEBTERM_URL=https://desktop-balmtav-1.tail42cd28.ts.net/terminal/ python3 staging/check_staging.py`: **PASS**

This exercised the actual Funnel path with mobile emulation and real command/key traffic.

`WEBTERM_URL=https://desktop-balmtav-1.tail42cd28.ts.net/terminal/ python3 staging/check_xterm6_compat.py`: **PASS**

This exercised the xterm 6 frontend through Funnel, including an actual terminal command marker in each renderer case.

`WEBTERM_URL=https://desktop-balmtav-1.tail42cd28.ts.net/terminal/ python3 staging/check_touch_resize.py`: **PASS** after a test-harness correction described below.

External touch observation:

```text
touch viewport: 453 -> 432 -> 453
resize iterations: 20
page errors/unhandled rejections: []
```

## Deployment-time test-harness correction

The first external `check_touch_resize.py` executions timed out while trying to create scrollback. The terminal already displayed a live shell prompt, and the separate external `check_staging.py` mobile test passed all actual input/key traffic. Investigation showed that `check_touch_resize.py` injected `window.term.input(...)` without first generating the explicit terminal tap that a touch user performs and that `check_staging.py` already performs.

The touch/resize test was strengthened rather than skipped:

1. it now performs a real CDP tap on the xterm screen before synthetic command input;
2. it sends an explicit `TOUCH_RESIZE_READY` shell marker;
3. it waits for that marker before generating the 500-line scrollback;
4. only then does it perform the touch gesture and resize assertions.

With this end-to-end readiness gate, both local 7683 and the real Funnel path pass. The touch-scroll assertion itself was not weakened.

## Rollback procedure

Rollback material is already verified at:

```text
/home/user01/.local/share/webterm/backups/phase10-20260903-2208/
```

If rollback becomes necessary:

1. copy the backup `ttyd` to a temporary file in `/home/user01/.local/bin/` and verify SHA-256 `72ec5af3...`;
2. copy the backup `index.html` to a temporary file beside the production frontend and verify SHA-256 `38a28e13...`;
3. atomically rename the two temporary files over the live paths;
4. terminate the current ttyd PID only;
5. confirm port 7683 is free;
6. start the exact production command shown at the top of this report;
7. verify `/token`, external `/terminal/token`, WSS `fresh`, and the mobile smoke test.

Do **not** restart `codexpro-http.service` as part of ttyd rollback: the ttyd process is managed independently within the user session, and restarting that broader service would unnecessarily affect unrelated tooling.

## Final status

At the end of Phase 10:

- production binary is the Phase 9 candidate: **yes**;
- production frontend is the Phase 8 xterm 6 artifact: **yes**;
- localhost listener 7683 healthy: **yes**;
- public Funnel `/terminal` route healthy: **yes**;
- external WSS fresh/resume healthy: **yes**;
- local mobile/key/browser regression healthy: **yes**;
- external mobile/key/browser regression healthy: **yes**;
- touch-scroll + resize stress healthy locally and externally: **yes**;
- rollback artifacts preserved and runnable: **yes**;
- Funnel configuration modified: **no**;
- session launcher modified: **no**.

Phase 10 deployment is accepted.
