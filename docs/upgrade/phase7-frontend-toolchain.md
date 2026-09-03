# Phase 7 — frontend toolchain modernization

Captured: 2026-09-03 (Asia/Seoul)

## Result

**PASS — frontend toolchain modernization is complete and Phase 8 may proceed.**

Phase 7 changed the frontend build/lint toolchain only. The xterm runtime dependency set stayed on the Phase 6 baseline, the Phase 5/6 C hardening remained intact, and no production file or process was deployed/restarted.

The one non-zero final audit result is an npm registry **deprecation** classification for the intentionally retained ESLint 9.39.5 generation. It is not a vulnerability finding. `yarn npm audit --all --severity high` reports no audit suggestions, and the two Phase 1 Webpack advisories are gone. ESLint 10 remains intentionally deferred so the xterm 6 migration does not share a second lint-generation jump.

## Source baseline

- start HEAD: `7708b79a39a90b188e51333018dbbc05a13e2934`
- end HEAD: `7708b79a39a90b188e51333018dbbc05a13e2934`
- Phase 7 was performed in the existing dirty working tree containing the uncommitted Phase 5/6 hardening work; that work was not reset, reverted, or overwritten.
- Phase 6 backend candidate used for regression tests:
  - `/tmp/ttyd-stage-phase6/x86_64-linux-musl/bin/ttyd`
  - SHA-256 `ff207b7aa58e29db61a3c2f74dfd238065f8760fbe2cc77ecca0aa3749c2e86c`

Pre-Phase-7 recorded hashes:

| Artifact | Before SHA-256 |
| --- | --- |
| `html/package.json` | `d39a1e4a192253377c99e06fcff57cd2953cfa9b47bde22c5c1bb2b358545f2e` |
| `html/yarn.lock` | `f5f66efc4105d9291926110be34cbffdc77b85b40901c9a90fc99c3ae1915009` |
| `html/dist/inline.html` | `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887` |
| `staging/index.html` | `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887` |
| `src/html.h` | `6f3716ebd951e101df883bb14922f067c023f11561aa088ef487814183727cf3` |
| production `index.html` | `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887` |
| production ttyd binary | `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c` |

## Node and Yarn

Host defaults at Phase 7 start were Node `v24.18.0` and Yarn `3.6.3`.

Phase 7 target and validation environment:

- Node `v24.20.0`
- Yarn `4.18.0`
- `html/.node-version`: `24.20.0`
- `packageManager`: `yarn@4.18.0`
- package engine policy: `>=24.20.0 <25`

To avoid mutating the host runtime, the official Node 24.20.0 Linux x64 distribution was extracted under `/tmp/node-v24.20.0-linux-x64` and all final frontend validation used that Node explicitly. Yarn 4.18.0 was selected with Corepack using an isolated `/tmp/corepack-phase7` home. The repository pin, rather than the machine-global Yarn 3 install, is the Phase 7 source of truth.

Final explicit checks:

```text
node --version -> v24.20.0
corepack yarn --version -> 4.18.0
```

## Dependency matrix

### Lint / TypeScript

| Package | Before | Phase 7 |
| --- | ---: | ---: |
| TypeScript | 5.3.3 | **6.0.3** |
| GTS | 5.2.0 | **7.0.0** |
| ESLint | 8.57.0 | **9.39.5** |
| `@typescript-eslint/eslint-plugin` | 7.1.1 | **8.69.0** |
| `@typescript-eslint/parser` | missing direct peer | **8.69.0** |
| Prettier | missing direct peer | **3.9.6** |
| `eslint-plugin-prettier` | 5.1.3 | **5.5.6** |
| `eslint-webpack-plugin` | 4.0.1 | **6.0.0** |
| `@types/node` | not direct | **24.13.3** |

TypeScript 7.0.2 was intentionally rejected because `@typescript-eslint/parser` 8.69.0 declares TypeScript `<6.1.0`. TypeScript 6.0.3 is the latest 6.0 release and fits the frozen peer range.

ESLint 10 was also intentionally not adopted. GTS 7 is an ESLint 9-generation toolchain; keeping ESLint 9 separates lint modernization from the next xterm migration.

### Webpack group

| Package | Before | Phase 7 |
| --- | ---: | ---: |
| webpack | 5.90.3 | **5.110.3** |
| webpack-cli | 5.1.4 | **7.2.3** |
| webpack-dev-server | 5.0.2 | **6.0.0** |
| webpack-merge | 5.10.0 | **6.0.1** |
| copy-webpack-plugin | 12.0.2 | **14.0.0** |
| css-loader | 6.10.0 | **7.1.5** |
| css-minimizer-webpack-plugin | 6.0.0 | **8.0.0** |
| html-webpack-plugin | 5.6.0 | **5.6.8** |
| mini-css-extract-plugin | 2.8.1 | **2.10.2** |
| sass | 1.71.1 | **1.103.1** |
| sass-loader | 14.1.1 | **17.0.1** |
| style-loader | 3.3.4 | **4.0.0** |
| terser-webpack-plugin | 5.3.10 | **5.6.1** |
| ts-loader | 9.5.1 | **9.6.2** |

### Gulp / stream tools

| Package | Before | Phase 7 |
| --- | ---: | ---: |
| gulp | 4.0.2 | **5.0.1** |
| gulp-rename | 2.0.0 | **2.1.0** |
| through2 | 4.0.2 | **5.0.11** |
| gulp-clean | 0.4.0 | 0.4.0 |
| gulp-gzip | 1.4.2 | 1.4.2 |
| gulp-inline-source | 4.0.0 | 4.0.0 |

`through2` 5 exposes its preferred CommonJS-visible named export as `objectTransform`; the Gulp pipeline was minimally changed from `through2.obj(...)` to `objectTransform(...)`. The generated artifact semantics are unchanged.

## Removed and added direct dependencies

Removed:

- `eslint-plugin-node` 11.1.0 — no source/config usage remained after flat-config migration; GTS 7 provides the maintained `eslint-plugin-n` stack.
- `scssfmt` 1.0.7 — repository search found no usage outside `package.json`/the old lockfile.

Added explicitly:

- `@typescript-eslint/parser` 8.69.0 — resolves the baseline missing-peer defect.
- Prettier 3.9.6 — resolves the baseline `eslint-plugin-prettier` missing-peer defect.
- `@types/node` 24.13.3 — TypeScript 6 requires explicit Node globals for the existing `process`/`require` usage in the frontend entry.

Yarn 4 additionally reported one peer edge where `eslint-plugin-n` did not provide TypeScript to `ts-declaration-location`. `html/.yarnrc.yml` now declares a narrow `packageExtensions` entry supplying TypeScript 6.0.3 to `eslint-plugin-n`. `ts-declaration-location` accepts TypeScript `>=4.0.0`, so this satisfies rather than overrides an incompatible range.

## ESLint flat-config migration

Removed legacy files:

- `html/.eslintrc.json`
- `html/.eslintignore`

Added:

- `html/eslint.config.js`

The flat config preserves the previous project-specific behavior:

- TS/TSX `jsxPragma: h`
- `@typescript-eslint/no-duplicate-enum-values: off`
- Gulp/Webpack config files permit unpublished development requires via `n/no-unpublished-require: off`
- generated/cache paths are ignored through flat-config `ignores`
- Node globals for the CommonJS Gulp/Webpack config files are declared explicitly

No `ESLINT_USE_FLAT_CONFIG=false` compatibility escape hatch is used.

GTS 7 additionally enabled `no-floating-promises`; two reconnect calls were made explicit with `void`, and an unused `catch (e)` binding was reduced to `catch {}`. No bulk `gts fix` source rewrite was performed.

Prettier 3 changes the default trailing-comma policy. `trailingComma: 'es5'` is explicitly retained so the toolchain upgrade does not create formatting churn across the existing TypeScript source.

## TypeScript 6 compatibility choices

`html/tsconfig.json` retains the existing webpack-oriented compile behavior with minimal overrides:

- `composite: false` because this application intentionally disables declaration emit and is not a project-reference library build
- `ignoreDeprecations: "6.0"` keeps the existing `moduleResolution: "node"` behavior during Phase 7 rather than mixing a module-resolution migration into the toolchain upgrade
- `noUncheckedSideEffectImports: false` preserves existing SCSS/CSS side-effect imports without introducing fake module declarations
- `types: ["node"]` supplies the existing `process`/`require` globals through the new direct `@types/node` dependency

The `moduleResolution=node10` deprecation must be revisited before a future TypeScript 7 migration; it is intentionally not hidden as a permanent solution.

## Webpack-dev-server 6 migration

Webpack-dev-server 6 removed SockJS server support, so the old explicit:

```text
webSocketServer.type = sockjs
```

configuration was removed. WDS now uses its supported default `ws` transport. This change concerns only the dev-server control socket; the ttyd application WebSocket proxy at `/ws` remains configured separately and was not removed.

Port 9000 was already occupied by an unrelated/pre-existing process during validation. To test WDS 6 without touching that process, the config now keeps 9000 as the default while allowing an explicit `WEBPACK_DEV_SERVER_PORT` override. WDS 6 was started on port 19000, compiled successfully with Webpack 5.110.3, and shut down cleanly after the bounded validation run. Port 19000 was empty afterward.

The application proxy entries for `/token` and `/ws` remain present.

## Yarn 4 / lockfile

`html/yarn.lock` was migrated to Yarn 4 and refreshed only for the selected toolchain groups and their transitive graph.

Final lockfile cleanup also recursively refreshed `browserslist`/`caniuse-lite`; this removed the stale Browserslist warning without changing a direct runtime dependency. Final relevant resolution is Browserslist 4.28.8 / caniuse-lite 1.0.30001810.

Final lock SHA-256:

`647903c74aa620068c0aa7674de1288b94ce7bfe5d9488375eda3325318807e8`

`yarn install --immutable`: **PASS**, exit 0, no unresolved peer warning.

`yarn explain peer-requirements` showed no `✘` peer edge after the package extension was added.

## zmodem patch preservation

The custom patch file remains unchanged:

- `html/.yarn/patches/zmodem.js-npm-0.1.10-e5537fa2ed.patch`
- SHA-256 `5411e786ace86f7cc14db4723f129da1c21d04852f3c32a93f7021bdc64e37aa`

Final `yarn why zmodem.js` resolves the package through the same `patch:` locator and reports patch hash `064993`.

The frontend build includes the patched `zmodem.js` package successfully.

## xterm freeze

No xterm package was upgraded during Phase 7.

Final lock resolutions:

- `@xterm/addon-canvas` 0.6.0
- `@xterm/addon-fit` 0.9.0
- `@xterm/addon-image` 0.7.0
- `@xterm/addon-unicode11` 0.7.0
- `@xterm/addon-web-links` 0.10.0
- `@xterm/addon-webgl` 0.17.0
- `@xterm/xterm` **5.4.0**

This preserves the xterm 5 control group for Phase 8.

## Build and lint verification

All final commands below used Node 24.20.0 and Yarn 4.18.0.

| Gate | Result |
| --- | --- |
| `yarn install --immutable` | **PASS** |
| `yarn check` | **PASS** |
| `yarn build` | **PASS** |
| `yarn inline` | **PASS** |
| Webpack dev server startup on temporary port 19000 | **PASS** |

Final production bundle report:

- Webpack 5.110.3
- JS: approximately **708 KiB**
- CSS: approximately **4.8 KiB**
- no stale Browserslist warning after final recursive lock refresh

Phase 1 JS baseline was approximately 714 KiB, so the JS bundle decreased rather than increasing.

## Audit

Phase 1 direct findings were:

- Webpack 5.90.3 — GHSA-38r7-794h-5758
- webpack-dev-server 5.0.2 — GHSA-m28w-2pqf-7qgj

Final `yarn npm audit --all` no longer reports either advisory. Its only output is:

- ESLint 9.39.5 — npm deprecation classification, severity label `moderate`

This produces exit 1 but is not a vulnerability advisory. It is retained and documented because Phase 7 deliberately stays on the GTS 7 / ESLint 9 generation.

Final security threshold check:

```text
yarn npm audit --all --severity high
-> No audit suggestions
-> exit 0
```

No high or critical audit finding is present.

## Frontend artifact identity and size

Baseline production/staging inline HTML:

- SHA-256 `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887`
- raw size: 738,527 bytes
- deterministic gzip size: 192,890 bytes

Final Phase 7 candidate:

- `html/dist/inline.html` SHA-256 `c415eb492b2a8539a04c530922600c8b2381b9573ddbd099efd01df9226f9713`
- `staging/index.html` SHA-256 `c415eb492b2a8539a04c530922600c8b2381b9573ddbd099efd01df9226f9713`
- raw size: 732,575 bytes
- deterministic gzip size: 191,584 bytes
- `src/html.h` SHA-256 `2c2171443ce5927aab16c9aefcda6ea36dc884184cefcd78c2b72b0632b777a8`

The candidate is about 0.8% smaller raw and 0.7% smaller after gzip; there is no unexplained bundle growth.

The final inline artifact hash is exactly the hash used for the browser regression run. The later Browserslist-only lock cleanup reproduced the same inline hash, so no second browser behavior changed after testing.

## Browser regressions

A temporary Phase 6 candidate server was started only on `127.0.0.1:7684` with the Phase 7 `staging/index.html`.

### `staging/check_staging.py`

**PASS**

Preserved evidence includes:

- portrait toolbar: one row, no overflow
- landscape toolbar: one row, no overflow
- Enter bytes: `0d`
- Tab bytes: `09`
- Shift+Tab: `1b5b5a`
- normal/application/shift arrow sequences unchanged
- Ctrl+C / Ctrl+D behavior intact
- Escape behavior intact
- font controls intact
- fullscreen enter/exit intact

### `staging/check_touch_resize.py`

**PASS**

Touch control values remained identical to the xterm 5 baseline:

- before: `baseY=450`, `viewportY=450`
- drag down: `viewportY=428`
- reverse drag: `viewportY=450`
- resize stress final: `baseY=989`, `viewportY=989`, `rows=53`, `cols=52`
- page errors/unhandled rejections: `[]`

## Protocol and reconnect regressions

All used the explicit Phase 6 backend candidate.

### `staging/check_protocol_edges.py`

**PASS**

- fragmented input: true
- empty leading fragment: true
- fragmented empty message: true
- 65,536-byte input: exact length
- expected/actual payload SHA-256: `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`
- final empty frame: server alive
- new connection after empty frame: accepted

### `staging/check_fresh_session.py`

**PASS**

- takeover/resume PID preserved
- expired session obtains a new PID
- independent session PID differs
- detached output replayed

### `staging/check_reconnect.py`

**PASS**

- same PTY process across reconnect
- detached output replayed
- viewport returned to bottom

### `staging/check_omp_reconnect.py`

**PASS**

- same OMP process across disconnect/reconnect
- detached marker replayed

## Production untouched evidence

Production process after all Phase 7 work:

```text
3678814 /home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 -I /home/user01/.local/share/webterm/index.html /home/user01/.local/share/webterm/session.sh
```

This is the same PID recorded before Phase 7; no restart occurred.

Final production hashes remain exactly the Phase 1 values:

- `/home/user01/.local/bin/ttyd`: `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c`
- `/home/user01/.local/share/webterm/index.html`: `38a28e13ae2fe5ca8bff647a3d38e3b5f2b7f58ef6b5af96f1231bf679ef1887`

Temporary port 7684 was empty after the staging run. No Phase 7 candidate was copied into the production frontend path.

## Phase 7 source changes

Phase 7-specific tracked/generated changes are limited to the frontend toolchain and generated frontend header:

- delete `html/.eslintignore`
- delete `html/.eslintrc.json`
- update `html/.prettierrc.js`
- update `html/.yarnrc.yml`
- add `html/.node-version`
- add `html/eslint.config.js`
- update `html/package.json`
- update `html/yarn.lock`
- update `html/tsconfig.json`
- update `html/webpack.config.js`
- update `html/gulpfile.js`
- minimal lint-compatibility edits in `html/src/components/terminal/xterm/index.ts`
- regenerate `src/html.h`
- synchronize the ignored/staging `staging/index.html` candidate with `html/dist/inline.html`

The existing `src/http.c`, `src/protocol.c`, `src/server.c`, and `src/utils.c` modifications belong to Phase 5/6 and were not changed as part of this phase.

## Remaining known items

1. ESLint 9.39.5 is now registry-deprecated. Moving to ESLint 10 is intentionally deferred; doing it before xterm 6 would defeat the isolation objective of Phase 7.
2. `moduleResolution: "node"` is accepted in TypeScript 6 only with the documented `ignoreDeprecations: "6.0"` override. A modern module-resolution migration is required before TypeScript 7.
3. No production deployment has been authorized or performed.

## Phase 8 readiness

**Phase 8 xterm 6 migration may proceed.**

The frontend build/lint foundation is now Node 24.20 / Yarn 4 / TypeScript 6 / GTS 7 / ESLint 9 / Webpack 5.110.3, all existing xterm 5.4 browser controls are green, and the Phase 5/6 protocol/reconnect safety gates remain green. The next phase can therefore attribute new terminal behavior changes to the xterm migration rather than to a simultaneous build-toolchain change.
