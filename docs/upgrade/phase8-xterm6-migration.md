# Phase 8 — xterm.js 6 migration

Captured: 2026-09-03 (Asia/Seoul)

## Result

**PASS — the xterm.js 6 candidate is buildable and passes the required automated mobile, renderer, reconnect, session and protocol gates. No production file or process was deployed or restarted.**

Phase 8 changed only the xterm runtime dependency group, the xterm integration code, generated frontend artifacts, and xterm-specific staging coverage. The Phase 5/6 backend hardening and custom session resume/reconnect semantics were preserved. The Phase 7 Node/Yarn/TypeScript/ESLint/Webpack toolchain was not upgraded again.

Two manual/visual checks remain explicitly outside the automated result: a physical Android Chrome + Korean IME run, and pixel-level Sixel rendering. Their addon/toolbar paths have automated smoke coverage, but they are not mislabeled as manually verified.

## Source and production baseline

Phase 8 started from the Phase 7 working tree without resetting or overwriting the existing uncommitted Phase 5–7 work.

Phase 6 backend candidate used for all backend-coupled regression tests:

- `/tmp/ttyd-stage-phase6/x86_64-linux-musl/bin/ttyd`
- SHA-256 `ff207b7aa58e29db61a3c2f74dfd238065f8760fbe2cc77ecca0aa3749c2e86c`

Pre-Phase-8 frontend hashes:

| Artifact | Before SHA-256 |
| --- | --- |
| `html/package.json` | `6768c8b3efb71c10af7deab44024ef5f5af6c0d3e6a533f4662d6eee5ad474e9` |
| `html/yarn.lock` | `647903c74aa620068c0aa7674de1288b94ce7bfe5d9488375eda3325318807e8` |
| `html/src/components/terminal/xterm/index.ts` | `908fd19b226769324002b2f5733f140b9ef52f382969d410c6ce7339566db2bd` |
| `html/dist/inline.html` | `c415eb492b2a8539a04c530922600c8b2381b9573ddbd099efd01df9226f9713` |
| `staging/index.html` | `c415eb492b2a8539a04c530922600c8b2381b9573ddbd099efd01df9226f9713` |
| `src/html.h` | `2c2171443ce5927aab16c9aefcda6ea36dc884184cefcd78c2b72b0632b777a8` |

Production remained a forbidden deployment target throughout Phase 8:

- `/home/user01/.local/bin/ttyd`
- `/home/user01/.local/share/webterm/index.html`
- production port `7683`
- production PID `3678814`

## Frozen toolchain retained

All final frontend commands used the isolated Phase 7 runtime rather than the host default Node:

- Node `v24.20.0` from `/tmp/node-v24.20.0-linux-x64`
- Yarn `4.18.0` through Corepack with `/tmp/corepack-phase7`
- TypeScript `6.0.3`
- GTS `7.0.0`
- ESLint `9.39.5`
- Webpack `5.110.3`

No Phase 8 update was made to Node, Yarn, TypeScript, ESLint, GTS, Webpack, Sass, Preact, or any native backend dependency.

## xterm dependency migration

The xterm runtime group is now exact-pinned for the migration candidate:

| Package | Phase 7 | Phase 8 |
| --- | ---: | ---: |
| `@xterm/xterm` | 5.4.0 | **6.0.0** |
| `@xterm/addon-fit` | 0.9.0 | **0.11.0** |
| `@xterm/addon-image` | 0.7.0 | **0.9.0** |
| `@xterm/addon-unicode11` | 0.7.0 | **0.9.0** |
| `@xterm/addon-web-links` | 0.10.0 | **0.12.0** |
| `@xterm/addon-webgl` | 0.17.0 | **0.19.0** |
| `@xterm/addon-canvas` | 0.6.0 | **removed** |

`yarn why @xterm/xterm` resolves exactly `@xterm/xterm@npm:6.0.0`.

`yarn why @xterm/addon-canvas` returns no dependency, and a repository search under `html` finds no remaining `addon-canvas` reference. This also removes the xterm-5-only canvas peer edge rather than forcing it into the xterm 6 graph.

Final lockfile SHA-256:

`cb37fdec8aaa57cb5d90ae13790fbb013ce554d77538700572247ee7bd651096`

`yarn explain peer-requirements` reports only satisfied (`✓`) edges and no failing (`✘`) peer edge.

The custom zmodem patch was preserved unchanged:

- patch SHA-256 `5411e786ace86f7cc14db4723f129da1c21d04852f3c32a93f7021bdc64e37aa`
- `yarn why zmodem.js` still resolves the same `patch:` locator with patch hash `064993`

## Renderer compatibility adaptation

`html/src/components/terminal/xterm/index.ts` was minimally adapted for xterm 6.

### Canvas

`CanvasAddon` import, state and load/dispose paths were removed.

The legacy client preference value remains accepted:

```text
rendererType=canvas
```

It now means:

1. dispose any active WebGL addon
2. do not attempt to load the removed CanvasAddon
3. continue with xterm 6's default renderer
4. log that the canvas renderer is unavailable with xterm 6

This preserves configuration compatibility without retaining an incompatible package.

### WebGL

`rendererType=webgl` still attempts `WebglAddon`.

The fallback is now the xterm 6 default renderer, not CanvasAddon.

The WebGL addon reference is cleared before disposal so a stale renderer reference is not retained. Both load failure and context loss are covered.

Automated renderer results:

- normal headless Chrome: WebGL addon loaded successfully
- `WEBGL_lose_context`: context loss was actually requested and observed; ttyd logged fallback to the default renderer; terminal input/output still worked afterward; no page error/unhandled rejection occurred
- Chrome with GPU and software rasterizer disabled: WebGL load failed as intended and the default-renderer fallback remained operational with no page error
- legacy `rendererType=canvas`: default-renderer fallback worked with no page error
- `rendererType=dom`: default-renderer path worked with no page error

These cases are implemented in `staging/check_xterm6_compat.py`.

## Touch scrolling compatibility

### Initial xterm 6 result

Before adding any ttyd compatibility code, the existing real-touch regression gate failed exactly as expected for the recorded xterm 6.0.0 touch regression.

Control state:

```json
{"baseY":450,"viewportY":450,"length":503,"rows":53,"cols":46}
```

After a downward CDP touch drag on the unmodified xterm 6 candidate:

```json
{"baseY":450,"viewportY":450,"length":503,"rows":53,"cols":46}
```

The viewport did not move.

### Local compatibility layer

A small application-level compatibility handler was added instead of copying xterm private implementation.

Properties of the workaround:

- uses public `Terminal.scrollLines()` and public buffer/row state
- registers only on touch/coarse-pointer clients
- handles one-finger vertical movement
- converts accumulated pixel movement into terminal lines
- calls `preventDefault()` only while terminal scrollback exists
- listeners are registered in ttyd's existing disposable lifecycle
- no xterm private object, internal service, or generated/minified implementation is accessed

This is intentionally removable when a future xterm version with native touch scrolling is adopted; it must not be left in place blindly alongside a future built-in implementation.

### Final touch result

With the compatibility layer:

```json
before:        {"baseY":450,"viewportY":450,"length":503,"rows":53,"cols":46}
after drag:    {"baseY":450,"viewportY":429,"length":503,"rows":53,"cols":46}
after reverse: {"baseY":450,"viewportY":450,"length":503,"rows":53,"cols":46}
```

The test uses Chrome DevTools Protocol `Input.dispatchTouchEvent`, not a wheel event or mouse drag.

`staging/check_touch_resize.py`: **PASS**.

## Resize/output stress and xterm buffer risk

The existing stress test already creates scrollback (`baseY > 200`), streams output, and alternates mobile viewport dimensions so row count repeatedly grows and shrinks while `ybase > 0`.

Phase 8 additionally ran the test with `WEBTERM_RESIZE_ITERATIONS=80`.

Final 80-iteration state:

```json
{
  "baseY": 970,
  "viewportY": 970,
  "length": 1023,
  "rows": 53,
  "cols": 52
}
```

Captured page errors/unhandled rejections: `[]`.

No `BufferLine`, `lineFeed`, erase-buffer or resize TypeError occurred. This is the release gate for the frozen xterm 6 `Buffer.resize` risk; the upstream issue remaining open does not weaken the local assertion.

## Mobile toolbar / PTY byte contract

`staging/check_staging.py`: **PASS** on the final xterm 6 candidate.

Wire-level results remain unchanged:

- Enter: `0d`
- Tab: `09`
- Shift+Tab: `1b5b5a`
- normal Left/Up/Down/Right: `1b5b44`, `1b5b41`, `1b5b42`, `1b5b43`
- application cursor Left/Up/Down/Right: `1b4f44`, `1b4f41`, `1b4f42`, `1b4f43`
- Shift+arrows: `1b5b313b3244/41/42/43`
- Ctrl+C path: PASS
- Ctrl+D path: PASS
- Escape path: PASS
- single-row toolbar portrait/landscape: PASS
- terminal/textarea focus behavior: PASS
- font +/-: PASS
- fullscreen enter/exit: PASS

The toolbar ESC/CTRL paths send their bytes through ttyd's own `sendData()` path, so they do not depend on xterm's physical-key IME translation.

### CJK IME status

Automated coarse-pointer/mobile toolbar tests cover ESC, Ctrl+C and Ctrl+D after the xterm 6 migration and remain green.

A physical Android Chrome session with a Korean IME and a physical-keyboard IME interaction was **not executed in this headless environment**. That manual check remains recommended before production deployment and is not represented as PASS here.

## Addon smoke coverage

`staging/check_xterm6_compat.py` verifies addon loading on the final candidate:

- `Unicode11Addon`: load PASS and `window.term.unicode.activeVersion === "11"`
- `ImageAddon`: `enableSixel=1` load path PASS; no JavaScript error
- `WebLinksAddon`: terminal open/input/output smoke PASS with the addon loaded unconditionally
- `WebglAddon`: load, context-loss fallback, and forced load-failure fallback PASS

Limitations are explicit:

- actual Sixel pixel rendering was not visually validated
- an actual web-link click/navigation was not automated; the load/open smoke path is validated

## Reconnect/session behavior

No Phase 8 source edit was made to reconnect timers, session-state protocol handling, resume IDs, reconnect scroll restoration, or backend session code.

All backend-coupled tests used the exact Phase 6 candidate SHA recorded above.

### `staging/check_fresh_session.py`

**PASS**

- initial/takeover/resume PID preserved
- independent session PID differs
- expired session obtains a new PID
- detached output replayed

### `staging/check_reconnect.py`

**PASS**

- same PTY process before/after reconnect
- detached output replayed
- final viewport at bottom

### `staging/check_omp_reconnect.py`

**PASS**

- same OMP process across disconnect/reconnect
- detached marker replayed

## Protocol edge regression

`staging/check_protocol_edges.py` with the Phase 6 candidate: **PASS**.

Observed:

- fragmented input: true
- empty leading fragment: true
- fragmented empty message: true
- 65,536-byte input exact length
- expected/actual payload SHA-256 `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`
- final empty WebSocket binary frame: server alive
- new connection after empty frame: accepted

The Phase 5 zero-length receive guard remains effective.

## Build, lint and audit

Final explicit gates using Node 24.20.0 / Yarn 4.18.0:

| Gate | Result |
| --- | --- |
| `yarn install --immutable` | **PASS** |
| `yarn check` | **PASS** |
| `yarn build` | **PASS** |
| `yarn inline` | **PASS** |
| `yarn npm audit --all --severity high` | **PASS — no audit suggestions** |

`yarn npm audit --all` still exits 1 solely for the already documented ESLint 9.39.5 registry deprecation classification. This is not a newly introduced xterm vulnerability and ESLint 10 remains intentionally outside Phase 8.

## Final frontend artifacts

Final Phase 8 hashes:

| Artifact | Phase 8 SHA-256 |
| --- | --- |
| `html/package.json` | `63a511224d0572b26ae1bd7882c38a248478f30cb7ead2d6729f2a69b03e5fc2` |
| `html/yarn.lock` | `cb37fdec8aaa57cb5d90ae13790fbb013ce554d77538700572247ee7bd651096` |
| `html/src/components/terminal/xterm/index.ts` | `d31eb175303fd6a53a7173062b6faa2e042765727188a49159b3014e84ebbb78` |
| `html/dist/inline.html` | `8083f8add847fa2f43ff9dcb84dcc4cf08a2427aa7bb498c4c02c5de0cc45027` |
| `staging/index.html` | `8083f8add847fa2f43ff9dcb84dcc4cf08a2427aa7bb498c4c02c5de0cc45027` |
| `src/html.h` | `e06d3aa110fb53912cf673654be09c0afe463cd49fc41408a46082ce488443e9` |

`src/html.h` was independently decoded/decompressed and its embedded HTML is byte-identical to `html/dist/inline.html`:

- embedded gzip bytes: `202862`
- decompressed bytes: `732901`
- decompressed SHA-256: `8083f8add847fa2f43ff9dcb84dcc4cf08a2427aa7bb498c4c02c5de0cc45027`
- equality check: `True`

The final `staging/index.html` hash is exactly the artifact exercised by the browser regression suite.

## Bundle size review

Phase 7 candidate:

- inline raw: `732575` bytes
- deterministic gzip: `191584` bytes

Phase 8 candidate:

- inline raw: `732901` bytes
- deterministic gzip: `201183` bytes
- active Webpack JS: approximately `707 KiB`
- active CSS: approximately `5.87 KiB`

Delta:

- raw: `+326` bytes (`+0.045%`)
- deterministic gzip: `+9599` bytes (`+5.01%`)

The raw bundle is essentially flat and the active JS bundle is not larger in the Webpack size report. The gzip increase is attributable to the changed xterm 6 code/CSS compression profile rather than an accidental extra dependency: the xterm module group contains six packages after CanvasAddon removal, `addon-canvas` is absent, and the source/lock scope was reviewed. The increase is recorded rather than hidden because compressed transfer/storage size matters for the embedded frontend.

## Known xterm 6 issue disposition

### Touch scrolling regression (#5489)

**Reproduced before workaround, gated, and locally mitigated.**

The mitigation is application-level and uses public xterm APIs only. The real touch test now passes. This compatibility code should be reconsidered/removed during a future xterm release migration rather than carried forward automatically.

### Buffer resize regression (#6063)

**Local stress gate PASS.**

Eighty alternating resizes with scrollback and concurrent output produced no page error or unhandled rejection. The upstream issue status does not convert this into an ignored/expected failure.

### CJK IME Ctrl/Escape issue (#6067)

**ttyd toolbar path PASS; physical IME path not manually tested.**

Toolbar-generated ESC/Ctrl sequences remain byte-correct because they bypass xterm's physical-key IME handling. A real Android/Korean-IME check remains a pre-production recommendation.

## Production safety check

After all Phase 8 tests:

```text
3678814 /home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 -I /home/user01/.local/share/webterm/index.html /home/user01/.local/share/webterm/session.sh
```

The production PID is unchanged.

Production hashes are unchanged from Phase 1/7:

- ttyd binary: `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c`
- production `index.html`: `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887`

Temporary port `7684` is empty after testing.

No Phase 8 candidate was copied into either production path and no production restart was performed.

## Phase 8 source scope

Phase 8-specific source/generated work is limited to:

- `html/package.json` — xterm exact pins and CanvasAddon removal
- `html/yarn.lock` — corresponding xterm graph refresh
- `html/src/components/terminal/xterm/index.ts` — renderer compatibility and touch-scroll compatibility
- `src/html.h` — regenerated embedded frontend
- ignored/generated `html/dist/inline.html`
- ignored/staging `staging/index.html`
- `staging/check_xterm6_compat.py` — renderer/addon/context-loss coverage
- this report

Existing Phase 5/6 C-file modifications and Phase 7 toolchain/config changes remain in the dirty working tree but were not expanded as part of Phase 8.

## Remaining risks

1. The touch-scroll compatibility layer is intentionally xterm-6-specific. A future xterm version with its own repaired touch gesture implementation must be tested without double-scrolling.
2. The frozen xterm 6 buffer-resize issue is still upstream risk even though the strengthened local stress gate is green.
3. Physical Android Chrome + Korean IME interaction remains a manual pre-production check.
4. Sixel addon loading is verified, but actual image pixel output was not visually checked in headless Chrome.
5. The embedded candidate's deterministic gzip size is about 5% larger than Phase 7 despite essentially flat raw size; this is documented and should remain visible in future size comparisons.

## Phase 9 readiness

**Phase 9 may proceed from the xterm-migration perspective.**

The required automated Phase 8 gates are green and the candidate remains isolated from production. This PASS means the xterm 6 candidate is technically validated for the next maintenance phase; it is not production-deployment authorization.
