# Phase 5 — zero-length WebSocket crash fix

Captured: 2026-09-03 (Asia/Seoul)

## Scope

This phase changes only the ttyd WebSocket receive path needed to prevent a zero-length WebSocket message from dereferencing an absent protocol byte. No frontend dependency, native dependency version, production artifact, port, Funnel route, or session launcher is changed.

## Reproduced baseline failure

The Phase 4 isolated regression test used the verified installed binary:

- `/home/user01/.local/bin/ttyd`
- version `1.7.7-7708b79`
- SHA-256 `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c`

A final zero-length binary WebSocket message produced:

```json
{
  "serverAlive": false,
  "returnCode": -11,
  "newConnectionAccepted": false
}
```

On this Linux environment, subprocess return code `-11` means termination by SIGSEGV.

The same baseline binary passed fragmented non-empty input and a 65,536-byte printable payload with exact SHA-256 equality, so the failing property was isolated to the empty-message path rather than general WebSocket input handling.

## Root cause in the local source

Before the fix, `LWS_CALLBACK_RECEIVE` allocated/appended `len` bytes and then immediately evaluated `pss->buffer[0]`. When the first callback for a WebSocket message had `len == 0` and there was no accumulated buffer, no protocol command byte existed to read.

## Minimal source change

The receive path now handles only the missing-command case before the existing allocation and command dispatch:

```c
if (len == 0 && pss->buffer == NULL) {
  if (lws_remaining_packet_payload(wsi) > 0 || !lws_is_final_fragment(wsi)) return 0;
  lwsl_warn("ignored empty WS message\n");
  break;
}
```

Semantics:

1. an empty non-final first fragment is ignored until a later continuation provides data;
2. a complete empty WebSocket message has no ttyd protocol command and is ignored;
3. an empty continuation after already accumulated data still follows the existing accumulated-message path;
4. non-empty receive, authentication, command dispatch and cleanup code are unchanged.

## Candidate build

A static x86_64-musl candidate was built successfully using the repository's existing `scripts/cross-build.sh` and the same dependency pins as the current custom build:

- zlib `1.3.1`
- json-c `0.17`
- libuv `1.44.2`
- Mbed TLS `2.28.5`
- libwebsockets `4.3.3`

Python CMake fallback used:

`/home/user01/.local/lib/python3.12/site-packages/cmake/data/bin/cmake`

Candidate binary:

- path: `/tmp/ttyd-stage-phase5/x86_64-linux-musl/bin/ttyd`
- version: `1.7.7-7708b79`
- SHA-256: `fea9046d140d73b660febd00bb21e932c8124641762b528454f16a15cc980cae`

The differing binary hash is expected because `src/protocol.c` changed while the dependency pins remained the same.

## Protocol regression result

Command:

```text
TTYD_BIN=/tmp/ttyd-stage-phase5/x86_64-linux-musl/bin/ttyd python3 staging/check_protocol_edges.py
```

Result: PASS.

Verified simultaneously:

- fragmented non-empty input: PASS
- empty initial fragment followed by valid continuation: PASS
- completely empty fragmented message: server survives and continues processing input
- 65,536-byte input length: exact
- 65,536-byte input SHA-256: exact
- final zero-length binary message: server remains alive
- new client connection after zero-length message: accepted

Observed large-input SHA-256 on both sides:

`62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`

Observed empty-frame result after the fix:

```json
{
  "serverAlive": true,
  "returnCode": null,
  "newConnectionAccepted": true
}
```

## Existing regression results with candidate backend

All passed:

- `staging/check_fresh_session.py`
- `staging/check_reconnect.py`
- `staging/check_omp_reconnect.py`
- `staging/check_staging.py`
- `staging/check_touch_resize.py`

The touch-scroll control remained `viewportY 450 -> 428 -> 450`, and the 20-iteration resize/output stress test reported no page errors or unhandled rejections.

## Sanitizer boundary

The current x86_64-musl cross compiler returns only the unresolved basenames `libasan.a` and `libubsan.a` for `-print-file-name`, so this cross toolchain does not expose usable ASan/UBSan runtimes. No sanitizer result is claimed for Phase 5.

This does not affect the direct before/after runtime reproduction: the old isolated binary terminates with SIGSEGV on the same empty-frame test and the rebuilt candidate survives it while preserving the other tested behavior.

A future disposable native build environment with sanitizer runtimes should rerun `check_protocol_edges.py`; sanitizer coverage remains an additional verification item, not a reason to weaken the now-reproducible release gate.

## Production state

The Phase 5 candidate was not installed. Production remains on the previously verified `/home/user01/.local/bin/ttyd` and port `7683`. Temporary port `7684` instances were used only for staging/browser verification and were terminated afterwards.

## Reverification on 2026-09-03

Phase 5 was executed again from the current workspace before moving to later maintenance phases.

The unchanged production binary was confirmed as:

- version: `1.7.7-7708b79`
- SHA-256: `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c`
- running only on the production command line using port `7683`

The current expanded `check_protocol_edges.py` reproduces the old-binary SIGSEGV even earlier than the original final-empty-frame check: after normal fragmented input succeeds, an empty initial non-final fragment followed by a valid continuation causes the old installed binary to terminate with return code `-11`. This is consistent with the same root cause: the receive path attempts to interpret a protocol command when no command byte has yet been accumulated.

A fresh static x86_64-musl candidate rebuild completed successfully with the unchanged dependency pins. The rebuilt candidate remained byte-identical to the previously recorded Phase 5 candidate:

- path: `/tmp/ttyd-stage-phase5/x86_64-linux-musl/bin/ttyd`
- version: `1.7.7-7708b79`
- SHA-256: `fea9046d140d73b660febd00bb21e932c8124641762b528454f16a15cc980cae`
- file type: statically linked, stripped x86-64 ELF

Fresh candidate verification results:

- `staging/check_protocol_edges.py`: PASS
  - normal fragmented input: PASS
  - empty leading fragment + continuation: PASS
  - completely empty fragmented message: PASS
  - 65,536-byte input length and SHA-256: exact
  - final zero-length binary message: server alive
  - new client after zero-length message: accepted
- `staging/check_fresh_session.py`: PASS
- `staging/check_reconnect.py`: PASS
- `staging/check_omp_reconnect.py`: PASS
- `staging/check_staging.py`: PASS
- `staging/check_touch_resize.py`: PASS
  - touch viewport control remained `450 -> 428 -> 450`
  - 20 resize/output iterations completed with no page errors or unhandled rejections

The musl cross compiler still returns only the unresolved basenames `libasan.a` and `libubsan.a` from `-print-file-name`, so no ASan/UBSan execution is claimed.

After verification, the temporary port `7684` listener was terminated and a process check showed only the original production ttyd on port `7683`. No candidate binary, frontend artifact, Funnel configuration, dependency version, or session launcher was deployed.
