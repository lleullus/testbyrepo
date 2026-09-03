# Upstream delta review: ttyd 1.7.7 baseline to current main

Captured: 2026-09-02 (Asia/Seoul)

## Exact comparison points

- Local custom HEAD: `7708b79a39a90b188e51333018dbbc05a13e2934`
- Upstream 1.7.7 baseline: `40e79c706be14029b391f369bee6613c31667abb`
- Official upstream default branch from `git ls-remote --symref upstream HEAD`: `refs/heads/main`
- Official upstream HEAD at capture: `2922cb89f518bae4d0fcf4d757a7419638fc71fc`
- Commits after 1.7.7 baseline: 24

The upstream object was fetched successfully as `FETCH_HEAD`. This repository does not currently expose a local `upstream/main` ref, so comparisons in this review use the exact upstream HEAD SHA instead of assuming a remote-tracking ref exists.

## Scope summary

Historical diff from the 1.7.7 baseline to upstream HEAD affects 21 relevant files across server, frontend, cross-build, packaging, and CI. The large `src/html.h` delta is generated frontend content and must not be treated as an independent source change.

Important upstream current-state observations:

- upstream frontend remains on xterm 5.5.0, Node `>=12`, Yarn 3.6.3, TypeScript 5.3.3, Webpack 5.90.3
- upstream cross-build has moved from Mbed TLS to OpenSSL and currently pins zlib 1.3.2, json-c 0.18, OpenSSL 3.6.1, libuv 1.52.1, libwebsockets 4.5.7
- this custom branch already has a stronger viewport declaration than upstream's newest mobile viewport commit: current `html/src/template.html` uses `width=device-width, initial-scale=1, viewport-fit=cover`

Therefore upstream `main` is a source of specific server/build fixes, not a complete dependency-modernization target.

## Commit-by-commit disposition

| Upstream commit | Change | Files/area | Disposition for this fork | Reason / gate |
|---|---|---|---|---|
| `114d994` | man-page typo | man | omit | no runtime effect |
| `8ea2e50` | writable message | `src/server.c` | inspect/backport if still applicable | low-risk user-facing correctness; verify against custom server changes |
| `d0134c8` | xterm 5.5.0 | frontend | use as control/reference, do not cherry-pick generated artifact | xterm 5.5 is useful as a control group before v6, but final target is v6 |
| `b1eaaee` | xterm clipboard addon | frontend | defer | clipboard behavior must be evaluated with xterm 6/OSC52 and browser permission model, not mixed into baseline upgrade |
| `4dad131` | publish Docker image to GHCR | CI/packaging | defer until support matrix | only relevant if upstream-style Docker publishing is retained |
| `9c87671` | `closeOnDisconnect` option | frontend | do not blindly backport | custom branch has native reconnect/resume semantics; this option can conflict with the project's reconnect contract |
| `f3fe06a` | sync man client options | docs | defer | only after accepted client options are finalized |
| `db77fde` | `--srv-buf-size` option | server | optional/defer | feature addition, not required for current maintenance objective |
| `05422dc` | copyright year | metadata | omit | no runtime effect |
| `eccebc6` | bump libwebsockets | cross-build | evaluate in native phase, not direct cherry-pick | LWS changes affect protocol/paste/TLS behavior; must pass long-paste/fragment/reconnect tests |
| `7762c24` | zlib 1.3.2 | cross-build | adopt candidate | official current zlib stable is 1.3.2; apply with archive checksum and native tests |
| `e2819f2` | replace `sprintf` with `snprintf` | server C | high-priority selective backport candidate | bounded formatting is an isolated robustness improvement; review custom overlap and sanitizer tests |
| `04a920c` | Ubuntu base update | Docker | defer until support matrix | packaging-only; update only retained target |
| `ae1dd49` | `--once/--exit-no-conn` process wait fix | protocol | selective backport if options retained | behavioral bug fix; verify process-lifecycle tests |
| `0527545` | harden `open_uri` against shell injection | `src/utils.c` | high-priority selective backport/reimplementation candidate | security-relevant input handling; verify whether feature is reachable and add focused test if retained |
| `11b58a9` | MSVC native support | C/CMake | defer | only if Windows becomes a supported release target |
| `bbe59b4` | workflow image bumps | CI | reimplement in CI-modernization phase | do not copy old upstream Node/Yarn assumptions; align with frozen toolchain |
| `1cacc5a` | add MSVC build workflow | Windows CI | defer | support-matrix dependent |
| `b32125b` | README update | docs | omit/reconcile later | no runtime effect |
| `c47ae13` | copyright year | metadata | omit | no runtime effect |
| `a9b2d19` | cross-build overhaul | CMake/cross-build | selectively reimplement | contains useful OpenSSL/libuv/LWS modernization but must add checksums and retained-target policy rather than copy `curl | tar` behavior |
| `647d55a` | remove Dependabot config | CI | reject for maintained fork | this fork needs explicit dependency update visibility; automation policy will be designed separately |
| `58e6e6b` | MSVC build update | Windows CI | defer | support-matrix dependent |
| `2922cb8` | mobile viewport meta | frontend template | already superseded locally | custom template already contains `width=device-width, initial-scale=1, viewport-fit=cover` |

## Priority extraction

### Priority A: evaluate before dependency migration

1. `e2819f2` — bounded formatting (`snprintf`)
2. `0527545` — `open_uri` shell-injection hardening
3. `ae1dd49` — process-exit lifecycle fix, if relevant options are supported

These should be reviewed as small server-side changes with focused tests and should not be bundled with xterm or toolchain updates.

### Priority B: use as compatibility reference

1. `d0134c8` — xterm 5.5.0 baseline
2. `b1eaaee` — clipboard addon behavior

The upstream frontend is not sufficiently modern to serve as the final frontend target; it is useful as a known intermediate reference only.

### Priority C: native modernization input

1. `7762c24` — zlib 1.3.2
2. `eccebc6` — libwebsockets bump history
3. `a9b2d19` — OpenSSL/libuv/libwebsockets cross-build overhaul

The current upstream cross-build values at capture are:

- zlib `1.3.2`
- json-c `0.18`
- OpenSSL `3.6.1`
- libuv `1.52.1`
- libwebsockets `4.5.7`

These values are evidence of upstream integration choices, not automatic target approvals. The maintained fork will freeze official current metadata independently and then run protocol/TLS/paste/reconnect gates.

## Merge policy

Do not merge or rebase upstream `main` wholesale during phases 1-4.

Reasons:

1. local commits modify reconnect/session semantics and mobile frontend behavior after 1.7.7
2. upstream generated `src/html.h` would create high-noise conflicts
3. upstream frontend toolchain is still old and would not solve the intended dependency modernization
4. several upstream additions are optional features or packaging changes unrelated to this deployment
5. selective server fixes can be tested and reverted independently

The implementation phase must take upstream changes by behavior and test evidence, not by assuming upstream HEAD as the new base.
