# Phase 9 native dependency modernization report

Captured: 2026-09-03 (Asia/Seoul)

## Result

**PASS — validated x86_64-musl candidate; production not deployed.**

Selected default native stack:

- zlib 1.3.2
- json-c 0.19
- libuv 1.52.1
- Mbed TLS 3.6.7
- libwebsockets 4.5.8
- 2021-11-23 x86_64-linux-musl cross toolchain

The production ttyd process, `/home/user01/.local/bin/ttyd`, listener on port 7683, production frontend, Funnel configuration and session launcher were not modified or restarted during Phase 9.

## Build-system changes

`scripts/cross-build.sh` now:

1. uses `set -euo pipefail`;
2. downloads source/toolchain archives to files before extraction;
3. verifies SHA-256 before use and fails closed for unknown versions;
4. verifies the frozen x86_64 musl toolchain archive;
5. supports separate Mbed TLS and OpenSSL TLS build paths;
6. scopes the historical libwebsockets 4.3.x CMake workaround so it cannot corrupt newer LWS CMake files;
7. supports the tested native-version matrix by environment override;
8. defaults to the validated Phase 9 stack;
9. applies an Mbed TLS `-ffile-prefix-map` so absolute disposable build roots are not embedded in the final artifact.

There is no fallback from a checksum mismatch to unverified source extraction.

## Selected artifact

Default build path used for final verification:

```text
/tmp/ttyd-stage-phase9-default/x86_64-linux-musl/bin/ttyd
```

Observed properties:

```text
version: ttyd version 1.7.7-7708b79
SHA-256: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
file: ELF 64-bit LSB executable, x86-64, statically linked, stripped
file size: 1,582,232 bytes
size(1): text=1,340,179 data=237,560 bss=19,120 dec=1,596,859
ldd: not a dynamic executable
readelf -d: no dynamic section
```

Installed production baseline for comparison:

```text
SHA-256: 72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c
file size: 1,316,984 bytes
```

The selected candidate is 265,248 bytes larger, approximately 20.1%, while retaining a statically linked/stripped deployment shape. The tested OpenSSL 3.6.1 + LWS 4.5.8 alternative was 7,370,664 bytes and was therefore not selected as the default.

## Regression verification on the final default binary

### PTY/session semantics

`staging/check_fresh_session.py`: PASS

- takeover/resume kept the original shell PID;
- an independent resume ID produced an independent PTY;
- grace expiry created a new PTY;
- detached output replayed.

`staging/check_reconnect.py`: PASS

- PID before/after reconnect identical;
- detached output replayed;
- terminal returned to the bottom after reconnect.

`staging/check_omp_reconnect.py`: PASS

- OMP PID before/after disconnect identical;
- detached marker replayed.

### WebSocket protocol edges

`staging/check_protocol_edges.py`: PASS

Verified:

- fragmented input: PASS;
- empty leading fragment: PASS;
- fragmented empty message: PASS;
- 65,536-byte client input received at exact length;
- expected/actual payload SHA-256 both `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`;
- zero-length binary frame did not terminate the server;
- a new connection was accepted after the zero-length frame.

### Server hardening

`staging/check_server_hardening.py`: PASS

- >5 KiB preferences/title initial messages remained safe;
- `openUri` adversarial value remained one argv and did not create a shell marker;
- remaining `sprintf` count: 0.

### Browser/mobile/xterm 6

A temporary selected-candidate ttyd instance was bound only to `127.0.0.1:7684` with `staging/index.html` and then terminated.

`staging/check_staging.py`: PASS

- mobile toolbar remained a single row in portrait and landscape;
- Enter/Tab/Shift+Tab and normal/application/shifted arrow bytes remained exact;
- Ctrl+C, Ctrl+D, Escape, font-resize and fullscreen tests passed.

`staging/check_touch_resize.py`: PASS

- touch scroll moved viewport `450 -> 429 -> 450`;
- 20 alternating mobile viewport resizes during output completed;
- captured page errors/unhandled rejections: `[]`.

`staging/check_xterm6_compat.py`: PASS

- xterm 6 DOM/default renderer path passed;
- Unicode 11, Image and WebLinks addon smoke tests passed;
- legacy canvas preference safely fell back to default renderer;
- WebGL loaded and context-loss fallback returned safely to default renderer.

## TLS verification

A temporary self-signed certificate was used with the final default binary on localhost port 7684. This did not alter production TLS material.

Observed:

- HTTPS `/token`: PASS;
- forced TLS 1.2 connection: `TLSv1.2`;
- forced TLS 1.3 connection: `TLSv1.3`;
- WSS tty authentication/session state: `fresh`.

Mbed TLS 3.6.7 was selected over OpenSSL 3.6.1 because both paths passed the required TLS checks, while Mbed TLS preserves the existing backend architecture and produced a substantially smaller static artifact.

## Rejected/deferred candidates

### Mbed TLS 4.2.0

The official release asset and checksum were validated and Mbed TLS itself built. libwebsockets 4.x then failed against removed Mbed TLS public API/header surfaces such as `mbedtls/entropy.h`. Direct Mbed TLS 4 integration is deferred until LWS/ttyd integration explicitly supports it.

### OpenSSL 3.6.1

Build and TLS behavior passed and the backend remains supported by the script as an explicit alternative. It was not selected by default because the static LWS 4.5.8 ttyd artifact was 7,370,664 bytes and would introduce a much larger backend/packaging change without a demonstrated deployment requirement.

### OpenSSL 4.0.2

Source metadata/checksum remains frozen for future evaluation, but it was not promoted as a Phase 9 production candidate because the lower-risk OpenSSL 3.6.1 control was sufficient to compare TLS backend behavior.

### libwebsockets 5.0.0

LWS itself built, but ttyd's final static link failed to resolve the LWS dependency set (`ssl`, `crypto`, `z`, `uv`). LWS 5 also exposed a deprecated URI API warning in the current ttyd source. No linker workaround was added solely to force this major upgrade through.

## Reproducibility

Before the reproducibility fix, identical selected versions built under different `/tmp` roots produced different ttyd SHA-256 values. Binary inspection identified absolute Mbed TLS source filenames embedded by `__FILE__`.

After applying `-ffile-prefix-map=${BUILD_DIR}=.` to the Mbed TLS build, two clean independent roots produced exactly the same binary:

```text
repro-a: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
repro-b: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
default: 2e34d0685f08d7b74235d7e656a6d40f008c39b1b77e80843fe5ac3a2c45d9d8
```

Thus the selected x86_64-musl artifact is reproducible across the three verified build roots.

## Sanitizer status

ASan/UBSan were probed in the exact frozen 2021 x86_64-musl cross toolchain.

```text
x86_64-linux-musl-gcc -print-file-name=libasan.a  -> libasan.a
x86_64-linux-musl-gcc -print-file-name=libubsan.a -> libubsan.a
```

Link probes then failed with:

```text
ld: cannot find -lasan
ld: cannot find -lubsan
```

Classification: **verification-toolchain limitation, not a ttyd test failure.** No sanitizer error was observed because this frozen cross toolchain does not contain the sanitizer runtimes. Phase 9 therefore does not claim sanitizer coverage. If sanitizer coverage becomes a release requirement, it must be performed in a separate compatible native compiler/runtime environment without silently changing the frozen production cross toolchain.

## Production boundary

Phase 9 intentionally stops at a verified candidate. It did not:

- overwrite `/home/user01/.local/bin/ttyd`;
- restart the production ttyd process;
- change listener port 7683;
- alter `/home/user01/.local/share/webterm/index.html`;
- alter `/home/user01/.local/share/webterm/session.sh`;
- change Funnel or external routing.

Deployment and rollback remain a separate phase.
