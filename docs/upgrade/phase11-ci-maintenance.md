# Phase 11 CI modernization and maintenance report

Captured: 2026-09-03 (Asia/Seoul)

## Result

**PASS for local implementation and validation.**

Phase 11 converted the repository from upstream-era CI assumptions to maintenance CI that reflects the Phase 7-10 deployed stack. No production ttyd file, frontend file, session launcher, Funnel route, or production process was modified or restarted.

A real GitHub-hosted Actions run still requires the changes to be committed/pushed or opened as a PR. Workflow syntax was validated locally with actionlint 1.7.7 before this phase was accepted.

## Production boundary

Production identity at Phase 11 start:

```text
ttyd PID: 1204576
ttyd command: /home/user01/.local/bin/ttyd -W -i 127.0.0.1 -p 7683 -I /home/user01/.local/share/webterm/index.html /home/user01/.local/share/webterm/session.sh
ttyd sha256: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
frontend sha256: 8083f8add847fa2f43ff9dcb84dcc4cf08a2427aa7bb498c4c02c5de0cc45027
Funnel /terminal: http://127.0.0.1:7683
```

The same PID, hashes, command line and Funnel target were observed again after all Phase 11 edits and local tests.

The Phase 10 rollback directory remains untouched:

```text
/home/user01/.local/share/webterm/backups/phase10-20260903-2208/
```

## Problems in the previous CI

### Frontend

The old frontend workflow used:

- Ubuntu 22.04;
- Node 18;
- `corepack prepare yarn@stable`;
- mutable `yarn install`;
- `html/*` path filters which did not represent nested source changes.

That no longer matched the deployed frontend, which is pinned to Node 24.20.0, Yarn 4.18.0, TypeScript 6.0.3, Webpack 5.110.3 and xterm 6.0.0.

### Backend

The old backend workflow presented 11 cross targets as one equal matrix even though Phase 9 obtained complete reproducible-build and regression evidence only for x86_64 Linux static musl. The current checksum-closed cross-build also intentionally has a frozen musl toolchain SHA-256 only for the validated x86_64 target; other targets must not be presented as production-supported merely because historical target names remain in the script.

### Docker / release

The old Docker workflow automatically pushed to the upstream `tsl0922/ttyd` Docker Hub namespace on main/tag events. That behavior is inappropriate for this maintained fork.

The old release workflow automatically reacted to any tag and moved directly toward GitHub Release creation without first requiring the Phase 7-10 frontend/native/browser regression gates.

## CI support policy

### Tier 1 — required

```text
x86_64 Linux static musl
```

Selected native versions:

- zlib 1.3.2;
- json-c 0.19;
- libuv 1.52.1;
- Mbed TLS 3.6.7;
- libwebsockets 4.5.8;
- musl toolchain release 2021-11-23.

The native build continues to use checksum-verified downloads and fails closed for an unknown component/toolchain version.

### Not currently Tier 1

i686, ARM variants, AArch64, MIPS variants, PowerPC variants, s390x and Windows remain outside the required production support claim until their toolchain archive checksums and target-specific build/runtime tests are explicitly established.

Phase 11 therefore removed the misleading all-target required matrix rather than weakening the checksum policy to make historical targets green.

## Frontend workflow

`.github/workflows/frontend.yml` now:

1. triggers on `html/**`, `src/html.h`, and its own workflow file;
2. supports `workflow_call` and manual dispatch;
3. uses `ubuntu-24.04`;
4. reads Node from `html/.node-version` (`24.20.0`);
5. enables Corepack but relies on repository `packageManager: yarn@4.18.0` rather than `yarn@stable`;
6. runs `yarn install --immutable`;
7. runs `yarn check`;
8. runs `yarn build`;
9. fails if the generated `src/html.h` differs from the committed file;
10. rebuilds the standalone inline artifact;
11. runs `yarn why zmodem.js` so the patched zmodem resolution remains visible in CI.

Local evidence:

```text
yarn install --immutable: PASS
yarn check: PASS
yarn build: PASS
yarn inline: PASS
yarn why zmodem.js: PASS
```

`src/html.h` SHA-256 before and after the clean production build remained identical:

```text
e06d3aa110fb53912cf673654be09c0afe463cd49fc41408a46082ce488443e9
```

The zmodem resolution still reports the repository Yarn patch URL.

High-severity registry audit:

```text
yarn npm audit --all --severity high
No audit suggestions
exit 0
```

## Required x86_64 backend workflow

`.github/workflows/backend.yml` now builds one explicit Tier 1 candidate in disposable runner temporary directories.

It installs a Python virtual environment with `websocket-client` and then runs the following against the newly built candidate:

- `staging/check_protocol_edges.py`;
- `staging/check_server_hardening.py`;
- `staging/check_open_uri.py`;
- `staging/check_exit_lifecycle.py`;
- `staging/check_fresh_session.py`;
- `staging/check_reconnect.py`;
- `staging/check_staging.py` against a disposable localhost listener;
- `staging/check_touch_resize.py` against the same disposable listener;
- `staging/check_xterm6_compat.py` against the same disposable listener.

The x86_64 binary is uploaded only after these gates pass.

The Phase 5 empty-frame server-survival assertion remains inside `check_protocol_edges.py`; it has not been skipped or converted to an expected failure.

### OMP reconnect boundary

`staging/check_omp_reconnect.py` launches the local OMP executable from `~/.bun/bin/omp` and exercises a live OMP tool call. A generic GitHub-hosted runner does not contain that project-specific binary/provider environment. It is therefore not falsely advertised as a portable GitHub-hosted required job.

The exact test was still executed locally against the Phase 11 freshly rebuilt candidate and passed, including same OMP PID and detached-output replay. It remains a local/self-hosted/manual release gate unless a controlled self-hosted OMP CI runner is introduced later.

## Weekly/manual reproducibility

The backend workflow now has a second job that runs only for schedule/manual events. It builds the selected x86_64 stack from two independent build roots with a shared verified download cache and requires `cmp` byte equality after showing both SHA-256 values.

This preserves the Phase 9 reproducibility requirement without doubling every PR's native-build cost.

## Local native verification

A clean Phase 11 build used disposable roots:

```text
CROSS_ROOT=/tmp/ttyd-phase11-cross
STAGE_ROOT=/tmp/ttyd-phase11-stage
BUILD_ROOT=/tmp/ttyd-phase11-build
DOWNLOAD_ROOT=/tmp/ttyd-phase11-downloads
BUILD_TARGET=x86_64
```

Result: **PASS**.

Candidate SHA-256:

```text
2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
```

This is byte-identical to the selected Phase 9 reproducible artifact and the currently deployed production ttyd.

## Local candidate regression results

### Protocol edges

**PASS**

Observed:

- fragmented input: PASS;
- empty leading fragment: PASS;
- fragmented empty message: PASS;
- 65,536-byte input length and SHA-256 integrity: PASS;
- zero-length binary frame: server remained alive and accepted a new connection.

### Server hardening

**PASS**

Observed:

- long initial preference/title messages survived;
- `open_uri` payload remained one argument;
- command-injection marker was not created;
- remaining `sprintf` occurrences in the protected paths: 0.

### `open_uri` focused test

**PASS** — URI preserved as one argument; marker injection false.

### Exit lifecycle

**PASS as the existing documented policy test.** The custom resume branch still records the upstream `--once/--exit-no-conn` lifecycle behavior as deferred policy rather than silently changing custom session semantics.

### Fresh/resume

**PASS** — takeover/resume PID preserved, independent/expired sessions separated, detached output replayed.

### Browser reconnect

**PASS** — same PTY process, detached output replay, viewport restored to bottom.

### OMP reconnect

**PASS** — same OMP PID, in-flight tool marker observed before disconnect, detached marker replayed after resume.

### Mobile/key browser regression

**PASS** against disposable `127.0.0.1:7684`.

The exact Enter, Tab, Shift+Tab, normal/application/shifted arrow byte assertions remained green, together with Ctrl+C/Ctrl+D/Escape, toolbar layout, font sizing and fullscreen.

### Touch/resize

**PASS**.

Latest observation:

```text
viewport: 454 -> 433 -> 454
resize iterations: 20
page errors/unhandled rejections: []
```

### xterm 6 compatibility

**PASS**.

Default renderer, Unicode 11, image/web-links addon smoke, legacy canvas-preference fallback, WebGL load and WebGL context-loss fallback all passed.

The disposable listener was terminated afterward and port 7684 was confirmed free.

## Dependency drift automation

`scripts/collect-upgrade-freeze.mjs` now supports:

```text
--check
--output PATH
```

`--check` is intentionally read-only. It fetches official registry/release metadata and prints a compact drift report without rewriting `docs/upgrade/dependency-freeze.json`, so scheduled CI does not create timestamp-only repository changes.

The default invocation still updates the frozen evidence JSON when a human intentionally refreshes the captured report.

Current read-only drift observation:

```text
Node repository generation: >=24.20.0 <25
Node current official LTS: v24.20.0
Yarn repository/current registry: 4.18.0 / 4.18.0
TypeScript repository/latest: 6.0.3 / 7.0.2
ESLint repository/latest: 9.39.5 / 10.9.1
xterm repository/latest: 6.0.0 / 6.0.0
```

Native metadata currently reports newer major-generation candidates such as Mbed TLS 4.2.0 and libwebsockets 5.0.0. These are informational only; Phase 9 already documented why those generations were not accepted.

`.github/workflows/maintenance.yml` runs weekly/manual and performs:

1. Node setup from `.node-version`;
2. Yarn immutable install;
3. high-severity npm audit;
4. read-only official dependency drift collection.

## Dependabot policy

`.github/dependabot.yml` changed from daily npm updates to weekly maintenance.

- npm `/html`: weekly Monday;
- xterm minor/patch updates grouped together;
- frontend development minor/patch updates grouped together;
- major updates remain separate changes rather than being hidden in those groups;
- GitHub Actions updates are now tracked weekly as a separate ecosystem;
- no auto-merge policy was introduced.

## Docker policy

`.github/workflows/docker.yml` is now manual build-only.

It no longer:

- runs automatically on `main` or tags;
- logs into Docker Hub;
- references Docker Hub secrets;
- pushes to `tsl0922/ttyd`;
- claims unverified multi-architecture production support.

The manual job builds the checksum-pinned x86_64 candidate and validates Ubuntu/Alpine amd64 image construction with `push: false`.

## Release policy

`.github/workflows/release.yml` is now manual-only.

A manual run always invokes the reusable frontend and backend validation workflows first. GitHub Release publishing occurs only when the dispatch input `publish=true` is explicitly set and the supplied tag matches the CMake project version. The publish job alone receives `contents: write`; normal validation stays `contents: read`.

The release remains a draft and no Phase 11 command created a tag or GitHub Release.

## CI configuration validation

A new `.github/workflows/ci-config.yml` runs on workflow configuration changes and installs exact `actionlint v1.7.7` before validating all GitHub Actions workflows.

Local result:

```text
actionlint v1.7.7: PASS
```

Dependabot YAML was also parsed locally with Python/PyYAML: **PASS**.

## Permissions / external safety

All normal CI workflows explicitly default to:

```yaml
permissions:
  contents: read
```

Only the explicitly approved release publish job elevates to `contents: write`.

No workflow points browser or PTY tests at the production Funnel URL. Automated browser tests use disposable localhost ttyd instances only.

No registry publishing secret is used by the Docker workflow.

## Deferred/manual maintenance items

The following remain intentionally separate from Phase 11:

1. ESLint 10 migration;
2. TypeScript 7 and module-resolution migration;
3. Mbed TLS 4 integration;
4. libwebsockets 5 integration;
5. OpenSSL 4 evaluation;
6. future xterm upgrades and removal/reassessment of the xterm-6-specific touch compatibility layer;
7. physical Android Chrome + Korean IME verification;
8. visual image/Sixel pixel-output inspection;
9. full production support claims for non-x86_64 cross targets;
10. portable automated OMP reconnect CI until a controlled OMP-capable runner exists.

## Final production safety check

After all Phase 11 work:

```text
PID: 1204576
ttyd sha256: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
frontend sha256: 8083f8add847fa2f43ff9dcb84dcc4cf08a2427aa7bb498c4c02c5de0cc45027
Funnel /terminal -> http://127.0.0.1:7683
port 7684: free
```

No production restart occurred during Phase 11.

## Acceptance

Phase 11 is accepted locally because:

- frontend install/check/build is reproducible and immutable;
- generated embedded frontend remains synchronized;
- x86_64 checksum-pinned native build is green and reproduces the deployed SHA-256;
- server/protocol/session/reconnect/browser/touch/xterm regressions are green on a disposable candidate;
- OMP reconnect was separately verified in the local environment where OMP actually exists;
- high-severity npm audit is green;
- dependency drift reporting is read-only;
- actionlint validates the new workflow graph;
- Docker/release publishing is no longer automatic;
- production identity and Funnel routing remained unchanged.
