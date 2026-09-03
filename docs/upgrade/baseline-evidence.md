# Upgrade baseline evidence

Captured: 2026-09-02 (Asia/Seoul)

This file records observed baseline facts before dependency or runtime changes. Failed verification preconditions are kept separate from component failures.

## Repository

- Workspace: `/home/user01/project/webterm/ttyd-1.7.7`
- CodexPro workspace ID: `ws_e9a7b0694697938aec12a80d`
- Branch: `custom/android-mobile-toolbar`
- HEAD: `7708b79a39a90b188e51333018dbbc05a13e2934`
- Upstream remote: `https://github.com/tsl0922/ttyd.git`
- Upstream 1.7.7 baseline commit: `40e79c706be14029b391f369bee6613c31667abb`
- Worktree before Phase 1 verification: clean (`show_changes`: 0 files, 0 additions, 0 deletions)
- No tag points at current HEAD.

Recent local commits from HEAD back to the upstream baseline:

1. `7708b79` Extend reconnect grace to 60 minutes
2. `1826060` Extend reconnect grace to 10 minutes
3. `efd8bf7` Make static cross-build reproducible
4. `0d921cd` Add native PTY session resume
5. `bb3e5f6` mobile: add enter toolbar key
6. `b50ec01` mobile: compact toolbar to one row
7. `07ec067` mobile: add tab shift and arrow toolbar keys
8. `dbedbcd` test: add web terminal staging checks and docs
9. `3959f1d` mobile: add keyboard-safe compact terminal toolbar
10. `40e79c7` Bump to 1.7.7

## Production runtime

Observed installed binary:

- Path: `/home/user01/.local/bin/ttyd`
- Version: `ttyd version 1.7.7-7708b79`
- SHA-256: `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c`
- File type: `ELF 64-bit LSB executable, x86-64, statically linked, stripped`

Observed running command line:

```text
/home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 -I /home/user01/.local/share/webterm/index.html /home/user01/.local/share/webterm/session.sh
```

The production process was PID `3678814` at capture time. PID is observational only and is not a deployment identifier.

## Toolchain

- Node.js: `v24.18.0`
- Yarn: `3.6.3`
- Python: `3.12.3`
- Google Chrome: `150.0.7871.46`
- C compiler: GCC `13.3.0`
- CMake: unavailable in this CodexPro execution environment (`cmake: command not found`, exit 127)

The missing CMake executable is a verification-environment limitation. It is not evidence that the C project fails to build.

## Frontend artifact identity

Before and after `yarn inline`, the active frontend artifacts remained unchanged.

- `html/dist/inline.html`: `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887`
- `staging/index.html`: `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887`
- `/home/user01/.local/share/webterm/index.html`: `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887`
- `src/html.h`: `6f3716ebd951e101df883bb14922f067c023f11561aa088ef487814183727cf3`

Thus the repository staging artifact, generated inline artifact, and production frontend were byte-identical at the baseline capture.

## Baseline install/build verification

### `yarn install --immutable`

Result: exit 0 with peer-dependency warnings.

Observed unmet peer declarations:

- project does not provide `@typescript-eslint/parser`, requested by `@typescript-eslint/eslint-plugin`
- project does not provide `prettier`, requested by `eslint-plugin-prettier`

These are baseline dependency-graph defects to resolve during the lint/toolchain phase; they are not hidden by the upgrade plan.

### `yarn check`

Result: exit 0.

### `yarn inline`

Result: exit 0 with Webpack `5.90.3`.

Observed bundle:

- JS: approximately 714 KiB
- CSS: approximately 4.8 KiB

Observed warnings:

- outdated Browserslist/caniuse-lite data
- Node `DEP0180`: deprecated `fs.Stats` constructor

### `yarn npm audit --all`

Result: exit 1 with two direct build-tool findings:

1. `webpack 5.90.3`, GHSA-38r7-794h-5758, low, patched at `>=5.104.0`
2. `webpack-dev-server 5.0.2`, GHSA-m28w-2pqf-7qgj, moderate, patched at `>=5.2.6`

These findings are concrete reasons to update the bundler group before xterm migration.

## Baseline regression suite

A temporary ttyd instance was started on `127.0.0.1:7684` using the same staging artifact and session launcher. It was terminated after the browser test.

### `python3 staging/check_staging.py`

Result: exit 0, `PASS: true`.

Verified among other existing assertions:

- single-row mobile toolbar in portrait and landscape
- textarea focus ownership
- modifier exclusivity and cleanup
- Enter = `0d`
- Tab = `09`
- Shift+Tab = `1b5b5a`
- normal cursor arrows = CSI sequences
- application cursor arrows = SS3 sequences
- Shift+arrows = modifier CSI sequences
- Ctrl+C and Ctrl+D behavior
- Escape visibility through `cat -v`
- font resize and fullscreen behavior

### `python3 staging/check_fresh_session.py`

First invocation without `TTYD_BIN` exited 1 because the script defaulted to the absent path `build-native/ttyd` and Python raised `FileNotFoundError`.

Classification: test precondition / missing local native test binary, not ttyd runtime failure.

The same script was then run with the explicit verified binary:

```text
TTYD_BIN=/home/user01/.local/bin/ttyd
```

Result: exit 0, `PASS: true`.

Observed:

- initial and takeover/resume PID identical
- independent session PID different
- expired session PID different
- detached output replayed

### `python3 staging/check_reconnect.py`

Run with explicit `TTYD_BIN=/home/user01/.local/bin/ttyd`.

Result: exit 0, `PASS: true`.

Observed:

- same PTY process before and after reconnect
- detached output replayed
- viewport returned to bottom

### `python3 staging/check_omp_reconnect.py`

Run with explicit `TTYD_BIN=/home/user01/.local/bin/ttyd`.

Result: exit 0, `PASS: true`.

Observed:

- same OMP process across disconnect/reconnect
- detached marker replayed

## Baseline acceptance

Phase 1 baseline is considered captured because:

- source worktree started clean
- production binary and frontend identity are recorded
- frontend clean install/check/build pass
- existing browser/reconnect/session tests pass when their explicit binary precondition is satisfied
- known dependency warnings and audit findings are recorded instead of being normalized away
- native rebuild remains unverified until a disposable environment with CMake is provided
