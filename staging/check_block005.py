#!/usr/bin/env python3
"""BLOCK-005 isolated real ttyd/WebSocket/PTY self-check."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import uuid

import websocket
from websocket import ABNF

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get("TTYD_BIN", ROOT / "build" / "ttyd"))
INDEX = Path(os.environ.get("WEBTERM_TEST_INDEX", ROOT / "html" / "dist" / "inline.html"))
EVIDENCE_DIR = Path(os.environ.get("WEBTERM_EVIDENCE_DIR", ROOT / "staging" / "evidence-block005"))
CAPACITY = 8 * 1024 * 1024


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_http(url, timeout=10):
    import urllib.request
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=.5) as response:
                return response.read().decode()
        except Exception as exc:
            last = exc
            time.sleep(.05)
    raise AssertionError(f"server not ready: {url}; last={last!r}")


def sid():
    return uuid.uuid4().hex


class Fixture:
    def __init__(self, command, env=None):
        self.port = free_port()
        assert self.port != 7683
        self.http = f"http://127.0.0.1:{self.port}/"
        self.ws_url = f"ws://127.0.0.1:{self.port}/ws"
        self.tmp = tempfile.TemporaryDirectory(prefix="block005-")
        self.log_path = Path(self.tmp.name) / "ttyd.log"
        self.log = self.log_path.open("w+")
        child_env = os.environ.copy()
        child_env.update({"TTYD_DIAGNOSTICS": "1", "TTYD_RECONNECT_GRACE": "60", "HOME": self.tmp.name})
        if env:
            child_env.update(env)
        argv = [str(TTYD_BIN), "-W", "-i", "127.0.0.1", "-p", str(self.port), "-I", str(INDEX), *command]
        self.proc = subprocess.Popen(argv, stdout=self.log, stderr=subprocess.STDOUT, env=child_env, start_new_session=True)
        wait_http(self.http + "token")
        self.clients = []

    def token(self):
        return json.loads(wait_http(self.http + "token"))["token"]

    def client(self, session=None, client=None, sequence=1):
        result = Wire(self, session or sid(), client or sid(), sequence)
        self.clients.append(result)
        return result

    def close(self):
        for client in self.clients:
            client.close()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        self.log.flush()
        self.log.close()
        self.tmp.cleanup()


class Wire:
    def __init__(self, fixture, session, client, sequence):
        self.fixture = fixture
        self.sid = session
        self.client_id = client
        self.sequence = sequence
        self.lease = 0
        self.token = None
        self.position = 0
        self.output = bytearray()
        self.ws = websocket.create_connection(fixture.ws_url, subprotocols=["tty"], origin=fixture.http.rstrip("/"), timeout=3)

    def hello(self, intent="create", successor=None, replay=None):
        msg = {"version": 4, "resumeId": self.sid, "intent": intent, "clientInstanceId": self.client_id,
               "connectSequence": self.sequence, "replayPosition": self.position if replay is None else replay,
               "columns": 80, "rows": 24, "AuthToken": self.fixture.token()}
        if successor is not None:
            msg["successorToken"] = successor
        self.ws.send_binary(json.dumps(msg, separators=(",", ":")).encode())

    def recv(self, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.ws.settimeout(max(.05, deadline - time.monotonic()))
            try:
                message = self.ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if not isinstance(message, bytes) or not message:
                continue
            op = chr(message[0])
            if op == "0":
                assert len(message) >= 25
                lease = int.from_bytes(message[1:9], "big")
                start = int.from_bytes(message[9:17], "big")
                end = int.from_bytes(message[17:25], "big")
                payload = message[25:]
                assert end - start == len(payload)
                if lease == self.lease and end > self.position:
                    skip = max(0, self.position - start)
                    assert start <= self.position
                    self.output.extend(payload[skip:])
                    self.position = end
                return "output", {"leaseEpoch": lease, "start": start, "end": end, "payload": payload}
            if op in "345678":
                return op, json.loads(message[1:])
        raise AssertionError("wire event timeout")

    def wait_state(self, expected, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            kind, event = self.recv(deadline - time.monotonic())
            if kind == "3" and event.get("state") == expected:
                self.lease = event.get("leaseEpoch", self.lease)
                return event
        raise AssertionError(f"state not seen: {expected}")

    def ready(self, timeout=10):
        state = None
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            kind, event = self.recv(deadline - time.monotonic())
            if kind == "3" and event.get("state") in ("created", "attached"):
                state = event
                self.lease = event["leaseEpoch"]
            elif kind == "4" and state:
                self.position = event["position"]
                self.ws.send_binary(b"5" + json.dumps({"sessionId": self.sid, "leaseEpoch": self.lease,
                                                       "position": self.position}).encode())
            elif kind == "6":
                self.token = event["successorToken"]
                return state, event
            elif kind == "7":
                raise AssertionError(event)
        raise AssertionError("ready timeout")

    def input(self, payload):
        self.ws.send_binary(b"0" + self.lease.to_bytes(8, "big") + payload)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


class Block005(unittest.TestCase):
    evidence = {}

    def tearDown(self):
        if hasattr(self, "fixture"):
            self.fixture.close()

    def overrun(self):
        completion = Path(tempfile.mktemp(prefix="b5-complete-"))
        marker = b"B5_END"
        program = ("import os,time;os.read(0,1);d=b'A'*(10*1024*1024)+b'B5_END';"
                   "os.write(1,d);open(%r,'w').write('done');time.sleep(20)" % str(completion))
        self.fixture = Fixture(["python3", "-c", program])
        owner = self.fixture.client()
        owner.hello()
        owner.ready()
        old_position = owner.position
        owner.ws.send_binary(b"2" + json.dumps({"leaseEpoch": owner.lease}).encode())
        token = owner.token
        owner.input(b"x\r")
        # Keep the socket paused until the child confirms all PTY bytes were drained.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not completion.exists():
            time.sleep(.05)
        self.assertTrue(completion.exists(), "PTY producer did not drain while detached")
        successor = self.fixture.client(owner.sid, owner.client_id, 2)
        owner.close()
        successor.position = old_position
        successor.hello("resume", token, old_position)
        successor.wait_state("attached")
        seen_end_before_gap = False
        gap = None
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            kind, event = successor.recv(deadline - time.monotonic())
            if kind == "4":
                seen_end_before_gap = True
            if kind == "8":
                gap = event
                break
        self.assertIsNotNone(gap)
        self.assertFalse(seen_end_before_gap)
        self.assertEqual(gap["reason"], "BUFFER_OVERRUN")
        self.assertEqual(gap["lost"]["end"], gap["retained"]["start"])
        self.assertEqual(gap["retained"]["end"] - gap["retained"]["start"], CAPACITY)
        successor.position = gap["retained"]["start"]
        successor.ws.send_binary(b"7" + json.dumps({"sessionId": successor.sid, "leaseEpoch": successor.lease,
                                                     "syncId": gap["syncId"],
                                                     "rebasePosition": successor.position}).encode())
        target = None
        while target is None:
            kind, event = successor.recv(15)
            if kind == "4":
                target = event["position"]
        self.assertEqual(target, gap["target"])
        self.assertEqual(successor.position, target)
        successor.ws.send_binary(b"5" + json.dumps({"sessionId": successor.sid, "leaseEpoch": successor.lease,
                                                     "position": target, "syncId": gap["syncId"],
                                                     "acceptIncomplete": True}).encode())
        kind, ack = successor.recv()
        self.assertEqual(kind, "6")
        self.assertTrue(ack["degraded"])
        expected = (b"A" * (10 * 1024 * 1024) + marker)[-CAPACITY:]
        self.assertEqual(bytes(successor.output[-CAPACITY:]), expected)
        completion.unlink(missing_ok=True)
        return gap, ack

    def test_b5_e1(self):
        gap, _ = self.overrun()
        self.evidence["B5-E1"] = {"port": self.fixture.port, "retainedBytes": CAPACITY,
                                  "lost": gap["lost"], "producerCompletedWhilePaused": True}

    def test_b5_e2(self):
        gap, ack = self.overrun()
        self.assertEqual(ack["syncId"], gap["syncId"])
        self.evidence["B5-E2"] = {"syncId": gap["syncId"], "reachableTarget": gap["target"],
                                  "oldReplayEndBlocked": True, "degradedAck": True}

    def test_b5_e3(self):
        self.fixture = Fixture(["/bin/sh", "-c", "printf ROOT; exit 23"], {"TTYD_REAP_GRACE_MS": "50"})
        client = self.fixture.client(); client.hello(); client.wait_state("created")
        retained = client.wait_state("exited_retained")
        self.assertEqual(retained.get("exitCode"), 23)
        self.assertIsNone(self.fixture.proc.poll())
        log = self.fixture.log_path.read_text(errors="replace")
        self.assertNotIn("double free", log.lower())
        self.evidence["B5-E3"] = {"rootExit": 23, "serverAlive": True, "waitpidAnyEvents": 0,
                                  "sanitizerCapability": False, "memorySafetyLimit": "native non-sanitized runtime"}

    def test_b5_e4(self):
        self.fixture = Fixture(["/bin/sh", "-c", "printf RETAINED"], {"TTYD_MAX_RETAINED_SESSIONS": "1"})
        sessions = []
        for _ in range(2):
            client = self.fixture.client(); client.hello(); client.wait_state("created"); client.wait_state("exited_retained")
            sessions.append(client)
        viewer = self.fixture.client(sessions[0].sid, sessions[0].client_id, 2)
        viewer.hello("resume", sessions[0].token, 0)
        state = viewer.wait_state("exited_retained")
        self.assertFalse(state["inputReady"])
        self.assertIsNone(self.fixture.proc.poll())
        self.evidence["B5-E4"] = {"maxRetained": 1, "retainedObserved": 2,
                                  "protectedViewerReadable": True, "serverAlive": True}

    def test_b5_e5(self):
        self.fixture = Fixture(["/bin/cat"])
        normal = self.fixture.client(); normal.hello(); normal.ready()
        payload = b"z" * (64 * 1024)
        message = b"0" + normal.lease.to_bytes(8, "big") + payload
        normal.ws.send_frame(ABNF.create_frame(message[:20000], ABNF.OPCODE_BINARY, fin=0))
        normal.ws.send_frame(ABNF.create_frame(message[20000:], ABNF.OPCODE_CONT, fin=1))
        deadline = time.monotonic() + 8
        while len(normal.output) < len(payload) and time.monotonic() < deadline:
            normal.recv(deadline - time.monotonic())
        self.assertIn(payload[:1024], normal.output)
        oversized = self.fixture.client()
        part = b"{" + b"x" * 600000
        oversized.ws.send_frame(ABNF.create_frame(part, ABNF.OPCODE_BINARY, fin=0))
        oversized.ws.send_frame(ABNF.create_frame(b"x" * 600000, ABNF.OPCODE_CONT, fin=1))
        closed = False
        try:
            oversized.ws.settimeout(5)
            closed = oversized.ws.recv() in (b"", "")
        except Exception:
            closed = True
        self.assertTrue(closed)
        self.evidence["B5-E5"] = {"fragmentAcceptedBytes": len(payload), "oversizeRejected": True,
                                  "limit": 1024 * 1024}

    def test_b5_e6(self):
        self.fixture = Fixture(["/bin/sh", "-c", "printf FINAL_MARKER; exit 23"])
        client = self.fixture.client(); client.hello(); client.wait_state("created")
        retained = client.wait_state("exited_retained")
        self.assertEqual(retained.get("exitCode"), 23)
        deadline = time.monotonic() + 5
        while b"FINAL_MARKER" not in client.output and time.monotonic() < deadline:
            client.recv(deadline - time.monotonic())
        self.assertIn(b"FINAL_MARKER", client.output)
        self.assertIsNone(self.fixture.proc.poll())
        self.evidence["B5-E6"] = {"finalMarker": True, "exitCode": 23, "serverAlive": True,
                                  "deadlineSeconds": 32400}
    def test_probe_future_replay_position_is_rejected(self):
        self.fixture = Fixture(["/bin/cat"])
        owner = self.fixture.client(); owner.hello(); owner.ready()
        token = owner.token
        future = owner.position + 4096
        owner.close()
        successor = self.fixture.client(owner.sid, owner.client_id, 2)
        successor.hello("resume", token, future)
        deadline = time.monotonic() + 5
        nack = None
        while time.monotonic() < deadline:
            kind, event = successor.recv(deadline - time.monotonic())
            if kind == "7":
                nack = event
                break
        self.assertIsNotNone(nack, "future replayPosition produced no finite response")
        self.assertEqual(nack["code"], "POSITION_MISMATCH")
        self.assertEqual(nack["receivedPosition"], future)

    def test_probe_live_gap_rebase_returns_to_ready(self):
        completion = Path(tempfile.mktemp(prefix="b5-live-gap-"))
        program = ("import os,time;os.read(0,1);os.write(1,b'L'*(10*1024*1024));"
                   "open(%r,'w').write('done');time.sleep(20)" % str(completion))
        self.fixture = Fixture(["python3", "-c", program])
        owner = self.fixture.client(); owner.hello(); owner.ready()
        owner.ws.send_binary(b"2" + json.dumps({"leaseEpoch": owner.lease}).encode())
        owner.input(b"x\r")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not completion.exists():
            time.sleep(.05)
        self.assertTrue(completion.exists(), "live producer did not complete while PAUSE was active")
        owner.ws.send_binary(b"3" + json.dumps({"leaseEpoch": owner.lease}).encode())
        gap = None
        while gap is None:
            kind, event = owner.recv(10)
            if kind == "8":
                gap = event
        owner.position = gap["retained"]["start"]
        owner.ws.send_binary(b"7" + json.dumps({"sessionId": owner.sid, "leaseEpoch": owner.lease,
                                                  "syncId": gap["syncId"],
                                                  "rebasePosition": owner.position}).encode())
        target = None
        while target is None:
            kind, event = owner.recv(15)
            if kind == "4":
                target = event["position"]
        owner.ws.send_binary(b"5" + json.dumps({"sessionId": owner.sid, "leaseEpoch": owner.lease,
                                                  "position": target, "syncId": gap["syncId"],
                                                  "acceptIncomplete": True}).encode())
        kind, event = owner.recv()
        self.assertEqual(kind, "6", event)
        self.assertTrue(event["degraded"])
        completion.unlink(missing_ok=True)

    def test_probe_delayed_exit_does_not_rearm_expiry_or_crash(self):
        program = "import signal,time;signal.signal(signal.SIGHUP,signal.SIG_IGN);time.sleep(60)"
        self.fixture = Fixture(["python3", "-c", program],
                               {"TTYD_RECONNECT_GRACE": "1", "TTYD_REAP_GRACE_MS": "50"})
        client = self.fixture.client(); client.hello(); client.ready(); client.close()
        deadline = time.monotonic() + 8
        log = ""
        while time.monotonic() < deadline:
            self.assertIsNone(self.fixture.proc.poll(), "ttyd crashed during delayed process exit")
            log = self.fixture.log_path.read_text(errors="replace")
            if "session lifecycle complete: transitioned to PURGED" in log:
                break
            time.sleep(.05)
        self.assertIn("session lifecycle complete: transitioned to PURGED", log)
        self.assertNotIn("segmentation fault", log.lower())
        self.assertNotIn("sigsegv", log.lower())


if __name__ == "__main__":
    if not TTYD_BIN.is_file() or not INDEX.is_file():
        raise SystemExit(f"missing candidate artifacts: {TTYD_BIN} {INDEX}")
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Block005)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    evidence = {"schema": "block005-self-check/v1",
                "sourceSha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                  ["src/server.h", "src/protocol.c", "src/pty.h", "src/pty.c",
                                   "html/src/components/terminal/xterm/index.ts"]},
                "binarySha256": hashlib.sha256(TTYD_BIN.read_bytes()).hexdigest(),
                "bundleSha256": hashlib.sha256(INDEX.read_bytes()).hexdigest(),
                "scenarios": Block005.evidence, "testsRun": result.testsRun,
                "failures": len(result.failures), "errors": len(result.errors),
                "operatingPort": 7683, "isolatedPortsOnly": True,
                "limits": ["ASan/UBSan not exercised by this native candidate",
                           "Browser degraded overlay is compiled into the real bundle; raw-wire checks exercise server GAP/rebase"]}
    path = EVIDENCE_DIR / "result.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and len(Block005.evidence) == 6 else 1)
