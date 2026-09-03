# Phase 6 — upstream server hardening selective backport

Captured: 2026-09-03 (Asia/Seoul)

## Scope and baseline

Phase 6 selectively backports the required server-side hardening before dependency upgrades. The Phase 5 zero-length WebSocket receive guard and the custom native session resume/reconnect implementation are preserved. Frontend dependencies, native dependency versions, production `index.html`, Funnel, `session.sh`, and the production ttyd binary/process were not changed.

Verified Phase 5 baseline candidate:

- path: `/tmp/ttyd-stage-phase5/x86_64-linux-musl/bin/ttyd`
- version: `1.7.7-7708b79`
- SHA-256: `fea9046d140d73b660febd00bb21e932c8124641762b528454f16a15cc980cae`

The Phase 5 receive guard remains in `src/protocol.c`:

```c
if (len == 0 && pss->buffer == NULL) {
  if (lws_remaining_packet_payload(wsi) > 0 || !lws_is_final_fragment(wsi)) return 0;
  lwsl_warn("ignored empty WS message\n");
  break;
}
```

## Upstream items

Evaluated upstream commits:

- `e2819f2a338db80b487867987e99994c3781aada` — `replace sprintf with snprintf`
- `05275453d752856dbd66437be253e055082a02fc` — `refactor open_uri to prevent potential shell injection`
- `ae1dd49ad818be617a83cf584899e17c3b0680f3` — `fix --once/--exit-no-conn not waiting for process to exit`

The required A and B behaviors were manually/selectively implemented rather than cherry-picked. This was necessary because the current fork contains Phase 5 and native resume changes, and because a mechanical `sprintf` to `snprintf` replacement is unsafe when the returned required length is later used as a write length.

`ae1dd49...` was not applied. Its lifecycle behavior remains deferred as described below.

## `sprintf` audit

Before Phase 6 there were 12 `sprintf` calls under `src`:

- `src/server.c`: 4
- `src/protocol.c`: 5
- `src/http.c`: 1
- `src/utils.c`: 2

After Phase 6, the source-level gate reports zero remaining `sprintf` calls under `src`.

### Handling by area

| Area | Phase 6 handling |
| --- | --- |
| `src/protocol.c` initial title | calculate exact size with `snprintf(NULL, 0, ...)`, allocate `LWS_PRE + capacity`, format again, validate the second return value, and pass only the validated written length to `lws_write` |
| `src/protocol.c` preferences | exact dynamic sizing; no silent truncation or unchecked length reuse |
| `src/protocol.c` session state | exact dynamic sizing; wire values remain `fresh`, `resumed`, or `resumed-reset` |
| `src/protocol.c` host/origin | format into a separate `origin_host[256]`; reject formatting failure/truncation and avoid source/destination overlap after `lws_parse_uri` |
| `src/http.c` token JSON | calculate exact size, allocate exact capacity, validate second format pass, and use that exact body/content length |
| `src/server.c` terminal type | fixed destination with explicit capacity |
| `src/server.c` `~/` index expansion | exact dynamic capacity; formatting failure/truncation is an error |
| `src/server.c` server header | fixed capacity; formatting failure/truncation aborts startup |
| `src/server.c` browser URL | fixed capacity; formatting failure/truncation is rejected |
| `src/utils.c` URI launcher | shell command construction removed entirely on Unix/macOS |

The initial-message change is intentionally stronger than upstream's mechanical fixed-buffer conversion: a truncating `snprintf` return value cannot become an out-of-bounds `lws_write` length.

## `open_uri` shell-injection removal

Old Unix/macOS behavior constructed a shell command containing the URI and called `system()`. Linux therefore exposed the URI to shell parsing in an `xdg-open ...` command string.

New behavior:

- Windows/Cygwin keeps the existing `ShellExecute` path.
- Linux keeps the fixed, non-user-input `system("xset -q > /dev/null 2>&1")` display-availability check.
- Unix/macOS uses `fork()`.
- The child redirects stdout/stderr to `/dev/null` when possible.
- macOS executes `open`; other Unix executes `xdg-open`.
- The URI is one `argv` element.
- `execvp()` is used; URI data is not evaluated by a shell.
- The parent uses `waitpid()` and reports success only for a normal child exit with status 0.

No unrelated subprocess abstraction was added.

## Hardening regressions

`staging/check_server_hardening.py`: **PASS**

- remaining `sprintf`: `0`
- fake `xdg-open` executed with exactly one URI argument
- marker injection: `false`
- long initial title: `5039` bytes, not truncated
- long preferences: `5021` bytes, not truncated
- session state: `fresh`
- server remained alive

`staging/check_open_uri.py`: **PASS**

- `xdg-open` argv count: `1`
- URI preserved as one argument: `true`
- test URI included semicolon, ampersand, dollar expansion syntax, backtick syntax, pipe, redirect, spaces, and quote characters
- marker injection: `false`

## `--once` / `--exit-no-conn` lifecycle

Focused observational test: `staging/check_exit_lifecycle.py`.

Latest Phase 6 candidate observation:

### `--once`

- server exited within 3 seconds: `true`
- disconnect-to-observation: approximately `0.003` seconds
- server return code: `0`
- child alive at immediate observation: `false`
- reconnect/resume possible after observation: `false`

### `--exit-no-conn`

- server exited within 3 seconds: `true`
- disconnect-to-observation: approximately `0.001` seconds
- server return code: `0`
- child alive at immediate observation: `true`
- reconnect/resume possible after observation: `false`

Immediate child-liveness is timing-sensitive and is not treated as a policy assertion. The stable result is that both modes currently terminate the server immediately enough to prevent reconnect/resume. The intended relationship between these options, child lifetime, reconnect grace, and resumable sessions is not defined for this custom fork.

Decision: **DEFERRED due to custom native session resume semantics**.

`ae1dd49...` was not applied and lifecycle source behavior was not changed. Test child processes were cleaned up after observation.

## Phase 6 candidate build

Dependency pins remained unchanged:

- zlib `1.3.1`
- json-c `0.17`
- libuv `1.44.2`
- Mbed TLS `2.28.5`
- libwebsockets `4.3.3`

Build/stage configuration:

- cross root: `/tmp/ttyd-cross-phase6`
- dependency build root: `/tmp/ttyd-build-phase6`
- stage root: `/tmp/ttyd-stage-phase6`
- ttyd CMake build directory used by `scripts/cross-build.sh`: `/home/user01/project/webterm/ttyd-1.7.7/build`
- CMake: `/home/user01/.local/lib/python3.12/site-packages/cmake/data/bin/cmake`

The full cross-build completed successfully. After the host/origin overlap fix, only the ttyd target was incrementally rebuilt in the same cross-build configuration and reinstalled into the same Phase 6 stage root.

Final candidate:

- path: `/tmp/ttyd-stage-phase6/x86_64-linux-musl/bin/ttyd`
- version: `1.7.7-7708b79`
- SHA-256: `ff207b7aa58e29db61a3c2f74dfd238065f8760fbe2cc77ecca0aa3749c2e86c`
- file: x86-64 ELF, statically linked, stripped

## Protocol and session regressions

`staging/check_protocol_edges.py`: **PASS**

- fragmented input: PASS
- empty leading fragment: PASS
- fragmented empty message: PASS
- 65,536-byte input length: exact
- expected SHA-256: `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`
- actual SHA-256: `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`
- final empty frame kept server alive: `true`
- new connection accepted after empty frame: `true`

`staging/check_fresh_session.py`: **PASS**

- takeover/resume retained the same PTY process
- detached output replayed
- grace expiration produced a new process as expected

`staging/check_reconnect.py`: **PASS**

- PID before/after reconnect: `951167` / `951167`
- detached output replayed: `true`
- terminal returned to bottom: `true`

`staging/check_omp_reconnect.py`: **PASS**

- OMP PID before/after reconnect: `951455` / `951455`
- detached marker replayed: `true`
- disconnect duration: `6` seconds
- grace: `20` seconds

No session-resume or reconnect-grace source was changed in Phase 6.

## Browser/mobile regression

The Phase 6 candidate was launched temporarily on `127.0.0.1:7684` with `staging/index.html`. Production port `7683` was not touched.

`staging/check_staging.py`: **PASS**

- mobile toolbar: 1 row, no overflow
- Enter: `0d`
- Tab: `09`
- Shift+Tab: `1b5b5a`
- normal arrows: PASS
- application cursor arrows: PASS
- shifted arrows: PASS
- Ctrl+C / Ctrl+D / ESC: PASS
- font resize: PASS
- fullscreen enter/exit: PASS

`staging/check_touch_resize.py`: **PASS**

- touch viewport Y: `452 -> 430 -> 452`
- resize stress iterations: `20`
- page errors: `[]`

The temporary 7684 ttyd instance exited cleanly after the browser tests.

## Sanitizer status

The Phase 6 musl cross compiler reports only bare names:

```text
-print-file-name=libasan.a
libasan.a

-print-file-name=libubsan.a
libubsan.a
```

**sanitizer runtime unavailable in current musl cross toolchain**

No ASan/UBSan PASS is claimed.

## Production state

Production remained unchanged through the final verification:

- process PID: `3678814`
- port: `7683`
- binary: `/home/user01/.local/bin/ttyd`
- version: `1.7.7-7708b79`
- SHA-256: `72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c`
- final `pgrep -a ttyd`: only the production process remained
- temporary 7684 instance: cleaned up
- lifecycle test child PIDs: absent after cleanup
- Phase 6 candidate was not copied to production
- production ttyd was not killed or restarted
- production index, Funnel, and `session.sh` were not changed

## Completion status

Required gates:

- [PASS] Phase 5 zero-length guard preserved
- [PASS] unsafe `sprintf` audit completed
- [PASS] remaining `sprintf` under `src`: 0
- [PASS] fixed-buffer `snprintf` capacities checked
- [PASS] no unchecked truncating `snprintf` return reused as write length
- [PASS] URI removed from shell command construction
- [PASS] `open_uri` injection regression
- [PASS] static x86_64-musl candidate build
- [PASS] `check_protocol_edges.py`
- [PASS] `check_fresh_session.py`
- [PASS] `check_reconnect.py`
- [PASS] `check_omp_reconnect.py`
- [PASS] `check_staging.py`
- [PASS] `check_touch_resize.py`
- [PASS] temporary 7684 cleanup
- [PASS] production 7683 untouched
- [DEFERRED] `--once` / `--exit-no-conn` lifecycle fix — custom native session resume semantics require an explicit policy decision
- [UNAVAILABLE] sanitizer runtime; no sanitizer PASS claimed

## Phase 7 readiness

**Phase 7 may proceed from the Phase 6 source-hardening perspective.**

Mandatory A+B hardening is implemented and all required source/runtime/browser regressions pass. The lifecycle item is explicitly deferred for the allowed custom-resume-semantics reason. The Phase 6 candidate remains a staging artifact only; this result does not authorize production deployment.
