# Upgrade regression baseline

Captured: 2026-09-02 (Asia/Seoul)

This file records the Phase 4 regression gates added before dependency changes. A failing gate is retained when it demonstrates an existing defect; it is not weakened to make the baseline green.

## Test binary and frontend

Protocol/reconnect tests used the explicit verified binary:

```text
TTYD_BIN=/home/user01/.local/bin/ttyd
version: 1.7.7-7708b79
sha256: 72ec5af3f3d830126c1105bf6f4ab0180b9b108a631abb7c7a29c3a23bd3359c
```

Browser tests used `staging/index.html`, whose SHA-256 was byte-identical to both `html/dist/inline.html` and the production frontend at Phase 1 capture.

## Existing gates

- `staging/check_staging.py`: PASS
- `staging/check_fresh_session.py` with explicit `TTYD_BIN`: PASS
- `staging/check_reconnect.py` with explicit `TTYD_BIN`: PASS
- `staging/check_omp_reconnect.py` with explicit `TTYD_BIN`: PASS

The exact PTY toolbar-byte assertions already present in `check_staging.py` remain the authoritative gate for Enter, Tab, Shift+Tab, normal/application cursor arrows and shifted arrows.

## New browser gate: `check_touch_resize.py`

Command:

```text
python3 staging/check_touch_resize.py
```

Result on the current xterm 5.4 baseline: PASS.

### Touch-scroll evidence

Before touch drag:

```json
{"baseY":450,"viewportY":450,"length":503,"rows":53,"cols":46}
```

After a downward finger drag:

```json
{"baseY":450,"viewportY":428,"length":503,"rows":53,"cols":46}
```

After the reverse finger drag:

```json
{"baseY":450,"viewportY":450,"length":503,"rows":53,"cols":46}
```

The test uses Chrome DevTools Protocol `Input.dispatchTouchEvent`, not mouse-wheel or mouse-drag emulation. This gives a concrete xterm 5.x control value for the xterm 6 migration.

### Resize/output stress evidence

The test streamed terminal output while alternating a 390×844 and 844×390 mobile viewport 20 times.

Final state:

```json
{"baseY":989,"viewportY":989,"length":1042,"rows":53,"cols":52}
```

Captured page errors/unhandled rejections: `[]`.

This gate must remain green after any xterm core/addon migration.

## New protocol gate: `check_protocol_edges.py`

Command:

```text
TTYD_BIN=/home/user01/.local/bin/ttyd python3 staging/check_protocol_edges.py
```

The test starts an isolated ttyd process on a random localhost port, so a crash does not affect the production process on port 7683.

### Fragmented input

Result: PASS.

A ttyd input message split across a binary WebSocket frame and continuation frame was reassembled and produced the expected `FRAGMENT_OK` shell marker.

### 64 KiB input integrity

Result: PASS.

The test switches the PTY to non-canonical/no-echo mode, starts a Python child that reads exactly 65,536 bytes, and sends one ttyd input message containing a deterministic printable-ASCII payload.

Observed:

- expected length: `65536`
- actual length: `65536`
- expected SHA-256: `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`
- actual SHA-256: `62b3a2ef06cf977623a5936a8fa653e3caecbf69b5f393ebdfe5022affc5331f`

The first development run used arbitrary byte values and caused the PTY line discipline to deliver a SIGQUIT control character to the child. That run was a test-design error and is explicitly excluded as product evidence. The committed test uses printable bytes so the measured property is transport length/integrity rather than terminal signal handling.

### Empty WebSocket binary frame

Result: FAIL on the current baseline, with an isolated server crash.

Observed after `ws.send_binary(b'')`:

```json
{
  "serverAlive": false,
  "returnCode": -11,
  "newConnectionAccepted": false
}
```

`-11` is the subprocess return code for termination by SIGSEGV on this Linux environment.

This converts the previously suspected zero-length handling problem into a reproducible local regression. The next server-safety phase must make this test pass with a minimal protocol guard before broader native dependency changes.

## Phase 4 acceptance

Phase 4 is accepted as a regression-gate phase even though the aggregate suite is intentionally red:

- existing functional/mobile/reconnect gates are green
- current xterm 5.4 touch scrolling has an objective passing control
- resize/output stress has an objective passing control
- fragmented and 64 KiB WebSocket input are verified on current libwebsockets 4.3.3
- empty-frame server survival is a confirmed failing baseline with an isolated reproducible SIGSEGV

The empty-frame assertion must not be removed, skipped, or converted to an expected crash during later upgrades. It is a release blocker until fixed.
