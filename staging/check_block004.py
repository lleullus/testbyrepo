#!/usr/bin/env python3
"""BLOCK-004 isolated real ttyd/WebSocket/PTY/Chromium self-check."""
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
import urllib.request
import uuid

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get("TTYD_BIN", ROOT / "build" / "ttyd"))
INDEX = Path(os.environ.get("WEBTERM_TEST_INDEX", ROOT / "html" / "dist" / "inline.html"))
EVIDENCE_DIR = Path(os.environ.get("WEBTERM_EVIDENCE_DIR", ROOT / "staging" / "evidence-block004"))
CHROME = os.environ.get("CHROME_BIN", shutil.which("google-chrome") or shutil.which("chromium") or "")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_http(url, timeout=10):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return response.read()
        except Exception as exc:
            last = exc
            time.sleep(0.05)
    raise AssertionError(f"server not ready: {url}; last={last!r}")


def session_id():
    return uuid.uuid4().hex


def be64(value):
    return value.to_bytes(8, "big")


class TtydFixture:
    def __init__(self, command=None):
        self.port = free_port()
        self.http = f"http://127.0.0.1:{self.port}/"
        self.ws_url = f"ws://127.0.0.1:{self.port}/ws"
        self.tmp = tempfile.TemporaryDirectory(prefix="block004-")
        self.log_path = Path(self.tmp.name) / "ttyd.log"
        self.log = self.log_path.open("w+")
        argv = [
            str(TTYD_BIN), "-W", "-i", "127.0.0.1", "-p", str(self.port),
            "-I", str(INDEX), *(command or ["/bin/bash", "--noprofile", "--norc"]),
        ]
        env = os.environ.copy()
        env.update({"TTYD_DIAGNOSTICS": "1", "TTYD_RECONNECT_GRACE": "60", "TTYD_READY_DEADLINE_MS": "200",
                    "HOME": self.tmp.name})
        self.proc = subprocess.Popen(argv, stdout=self.log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        wait_http(self.http + "token")
        self.clients = []

    def token(self):
        return json.loads(wait_http(self.http + "token"))["token"]

    def client(self, sid=None, client_id=None, sequence=1):
        client = WireClient(self, sid or session_id(), client_id or session_id(), sequence)
        self.clients.append(client)
        return client

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


class WireClient:
    def __init__(self, fixture, sid, client_id, sequence):
        self.fixture = fixture
        self.sid = sid
        self.client_id = client_id
        self.sequence = sequence
        self.lease = 0
        self.token = None
        self.position = 0
        self.output = bytearray()
        self.ws = websocket.create_connection(
            fixture.ws_url, subprotocols=["tty"], origin=fixture.http.rstrip("/"), timeout=3
        )

    def hello(self, intent="create", successor=None, version=4, replay=None):
        message = {
            "version": version,
            "resumeId": self.sid,
            "intent": intent,
            "clientInstanceId": self.client_id,
            "connectSequence": self.sequence,
            "replayPosition": self.position if replay is None else replay,
            "columns": 80,
            "rows": 24,
            "AuthToken": self.fixture.token(),
        }
        if successor is not None:
            message["successorToken"] = successor
        self.ws.send_binary(json.dumps(message, separators=(",", ":")).encode())

    def recv_event(self, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.ws.settimeout(max(0.05, deadline - time.monotonic()))
            try:
                message = self.ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if not isinstance(message, bytes) or not message:
                continue
            opcode = chr(message[0])
            if opcode == "0":
                if len(message) < 25:
                    raise AssertionError("short v4 OUTPUT")
                lease = int.from_bytes(message[1:9], "big")
                start = int.from_bytes(message[9:17], "big")
                end = int.from_bytes(message[17:25], "big")
                payload = message[25:]
                assert end - start == len(payload), (start, end, len(payload))
                if lease == self.lease and end > self.position:
                    skip = max(0, self.position - start)
                    assert start <= self.position, (start, self.position)
                    self.output.extend(payload[skip:])
                    self.position = end
                return "output", {"leaseEpoch": lease, "start": start, "end": end, "payload": payload}
            if opcode in "34567":
                return opcode, json.loads(message[1:])
        raise AssertionError("wire event timeout")

    def wait_state(self, expected, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            kind, event = self.recv_event(deadline - time.monotonic())
            if kind == "3" and event.get("state") == expected:
                if isinstance(event.get("leaseEpoch"), int):
                    self.lease = event["leaseEpoch"]
                return event
        raise AssertionError(f"state not seen: {expected}")

    def ready(self, expected=("created", "attached"), timeout=10):
        deadline = time.monotonic() + timeout
        state = None
        while time.monotonic() < deadline:
            kind, event = self.recv_event(deadline - time.monotonic())
            if kind == "3" and event.get("state") in expected:
                state = event
                self.lease = event["leaseEpoch"]
            elif kind == "4" and state is not None:
                assert event["version"] == 4 and event["leaseEpoch"] == self.lease
                self.position = max(self.position, event["position"])
                self.ws.send_binary(
                    b"5" + json.dumps({"sessionId": self.sid, "leaseEpoch": self.lease, "position": event["position"]}).encode()
                )
            elif kind == "6":
                assert event["leaseEpoch"] == self.lease and event["position"] == self.position
                self.token = event["successorToken"]
                return state, event
            elif kind == "7":
                raise AssertionError(f"unexpected NACK: {event}")
        raise AssertionError("READY_ACK timeout")

    def input(self, data):
        self.ws.send_binary(b"0" + be64(self.lease) + data)

    def wait_text(self, pattern, timeout=8):
        regex = re.compile(pattern)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            text = self.output.decode(errors="replace")
            match = regex.search(text)
            if match:
                return match
            self.recv_event(deadline - time.monotonic())
        raise AssertionError(f"text not seen: {pattern!r}; tail={self.output[-500:]!r}")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

class ChromeCdp:
    def __init__(self, url, hidden_no_raf=False):
        if not CHROME:
            raise AssertionError("Chrome binary unavailable")
        self.port = free_port()
        self.profile = tempfile.TemporaryDirectory(prefix="block004-chrome-")
        self.proc = subprocess.Popen([
            CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
            f"--remote-debugging-port={self.port}", f"--user-data-dir={self.profile.name}", "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_http(f"http://127.0.0.1:{self.port}/json/version")
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/json/new?about:blank", method="PUT")
        with urllib.request.urlopen(request, timeout=5) as response:
            target = json.load(response)
        self.ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=5, suppress_origin=True)
        self.next_id = 0
        self.call("Runtime.enable")
        self.call("Page.enable")
        if hidden_no_raf:
            self.call("Page.addScriptToEvaluateOnNewDocument", {"source": "Object.defineProperty(document,'visibilityState',{get:()=> 'hidden'});window.requestAnimationFrame=()=>0;"})
        self.call("Page.navigate", {"url": url})

    def call(self, method, params=None):
        self.next_id += 1
        ident = self.next_id
        self.ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == ident:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def evaluate(self, expression):
        return self.call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True}).get("result", {}).get("value")

    def wait_ready(self, timeout=15):
        deadline = time.monotonic() + timeout
        clicked = False
        while time.monotonic() < deadline:
            if not clicked:
                clicked = bool(self.evaluate("(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes('Start New Session')); if(b){b.click();return true}return false})()"))
            state = self.evaluate("window.ttydDiagnostics?.()")
            if state and state.get("inputReady"):
                return state
            time.sleep(0.1)
        raise AssertionError(f"browser did not become ready: {self.evaluate('window.ttydDiagnostics?.()')}")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        self.profile.cleanup()


class Block004(unittest.TestCase):
    evidence = {}

    def setUp(self):
        self.fixture = TtydFixture()

    def tearDown(self):
        self.fixture.close()

    def test_b4_e1(self):
        bad = self.fixture.client()
        bad.hello(version=3)
        mismatch = bad.wait_state("version_mismatch")
        self.assertEqual(mismatch["version"], 4)
        owner = self.fixture.client()
        owner.hello()
        state, _ = owner.ready()
        owner.input(b"echo PID=$$\r")
        pid = owner.wait_text(r"PID=(\d+)").group(1)
        successor = self.fixture.client(owner.sid, owner.client_id, owner.sequence + 1)
        successor.position = owner.position
        successor.hello("resume", owner.token)
        state2, _ = successor.ready(("attached",))
        successor.input(b"echo PID2=$$\r")
        pid2 = successor.wait_text(r"PID2=(\d+)").group(1)
        self.assertEqual(pid, pid2)
        self.assertGreater(state2["leaseEpoch"], state["leaseEpoch"])
        self.evidence["B4-E1"] = {"samePtyPid": pid, "epochs": [state["leaseEpoch"], state2["leaseEpoch"]]}

    def test_b4_e2(self):
        owner = self.fixture.client()
        owner.hello()
        state, _ = owner.ready()
        contender = self.fixture.client(owner.sid, session_id(), 1)
        contender.hello("resume", owner.token)
        conflict = contender.wait_state("conflict")
        self.assertEqual(conflict["leaseEpoch"], state["leaseEpoch"])
        contender.ws.send_binary(b"6" + json.dumps({
            "observedLeaseEpoch": conflict["leaseEpoch"], "connectSequence": 2, "columns": 80, "rows": 24
        }).encode())
        state2, _ = contender.ready(("attached",))
        self.assertGreater(state2["leaseEpoch"], state["leaseEpoch"])
        stale = self.fixture.client(owner.sid, session_id(), 1)
        stale.hello("resume", owner.token)
        stale.wait_state("conflict")
        stale.ws.send_binary(b"6" + json.dumps({
            "observedLeaseEpoch": state["leaseEpoch"], "connectSequence": 2, "columns": 80, "rows": 24
        }).encode())
        stale_state = stale.wait_state("stale")
        self.assertEqual(stale_state["leaseEpoch"], state2["leaseEpoch"])
        self.evidence["B4-E2"] = {"conflict": conflict["leaseEpoch"], "casEpoch": state2["leaseEpoch"]}

        provisional = self.fixture.client()
        provisional.hello()
        provisional.wait_state("created")
        timeout_state = provisional.wait_state("ready_timeout", timeout=35)
        self.assertEqual(timeout_state["state"], "ready_timeout")
        self.evidence["B4-E2"]["readyDeadline"] = "expired"
    def test_b4_e3(self):
        chrome = ChromeCdp(self.fixture.http + "?diagnostics=1", hidden_no_raf=True)
        try:
            state = chrome.wait_ready()
            self.assertGreaterEqual(state["parserCallbacks"], 1)
            self.assertEqual(state["state"], "application-ready")
            self.assertEqual(state["animationFrames"], 0)
            self.assertEqual(state["visibility"], "hidden")
            frozen = True
            try:
                chrome.call("Page.setWebLifecycleState", {"state": "frozen"})
                time.sleep(0.2)
                chrome.call("Page.setWebLifecycleState", {"state": "active"})
            except RuntimeError:
                frozen = False
            self.evidence["B4-E3"] = {
                "parserCallbacks": state["parserCallbacks"],
                "frozenCapability": frozen,
                "animationFrames": state["animationFrames"],
                "fallbackGeometry": state.get("lastValidGeometry") is None,
            }
        finally:
            chrome.close()

    def test_b4_e4(self):
        client = self.fixture.client()
        client.hello()
        state = client.wait_state("created")
        client.lease = state["leaseEpoch"]
        target = None
        while target is None:
            kind, event = client.recv_event()
            if kind == "output":
                continue
            if kind == "4":
                target = event["position"]
        client.ws.send_binary(b"5" + json.dumps({
            "sessionId": client.sid, "leaseEpoch": client.lease, "position": target + 1
        }).encode())
        kind, nack = client.recv_event()
        self.assertEqual((kind, nack["code"]), ("7", "POSITION_MISMATCH"))
        client.ws.send_binary(b"5" + json.dumps({
            "sessionId": client.sid, "leaseEpoch": client.lease, "position": target
        }).encode())
        kind, ack = client.recv_event()
        self.assertEqual(kind, "6")
        self.assertEqual(ack["position"], target)
        self.evidence["B4-E4"] = {"nack": nack["code"], "ackPosition": target}

    def test_b4_e5(self):
        self.fixture.close()
        self.fixture = TtydFixture(["/bin/sh", "-c", "printf RETAINED_DONE"])
        client = self.fixture.client()
        client.hello()
        state = client.wait_state("created")
        client.lease = state["leaseEpoch"]
        saw_retained = False
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                kind, event = client.recv_event(deadline - time.monotonic())
            except (AssertionError, websocket.WebSocketConnectionClosedException):
                break
            if kind == "3" and event.get("state") == "exited_retained":
                saw_retained = True
                break
        viewer = self.fixture.client(client.sid, client.client_id, client.sequence + 1)
        viewer.hello("resume", client.token)
        retained = viewer.wait_state("exited_retained")
        self.assertFalse(retained["inputReady"])
        fresh = self.fixture.client()
        fresh.hello()
        fresh_state, _ = fresh.ready()
        self.assertEqual(fresh_state["state"], "created")
        self.evidence["B4-E5"] = {"retained": saw_retained or retained["state"] == "exited_retained", "freshSession": fresh.sid}

    def test_b4_e6(self):
        self.fixture.close()
        capture_fd, capture_name = tempfile.mkstemp(prefix="block004-input-")
        os.close(capture_fd)
        capture = Path(capture_name)
        program = (
            "import os;"
            f"p={str(capture)!r};"
            "print('READY',flush=True);"
            "d=os.read(0,1);"
            "open(p,'ab').write(d)"
        )
        self.fixture = TtydFixture(["python3", "-c", program])
        chrome = ChromeCdp(self.fixture.http + "?diagnostics=1")
        try:
            deadline = time.monotonic() + 5
            clicked = False
            while time.monotonic() < deadline and not clicked:
                clicked = bool(chrome.evaluate("(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes('Start New Session'));if(!b)return false;b.click();b.click();return true})()"))
                time.sleep(0.05)
            self.assertTrue(clicked)
            state = chrome.wait_ready()
            connecting = [event for event in state["events"] if event["event"] == "connecting"]
            self.assertGreaterEqual(len(connecting), 2)
            self.assertTrue(state["inputReady"])
            self.assertEqual(state["pendingBytes"], 0)
            self.assertEqual(capture.read_bytes(), b"")
            self.evidence["B4-E6"] = {"latestReady": True, "preemptedAttempts": len(connecting), "ptyBytes": 0}
        finally:
            chrome.close()
            capture.unlink(missing_ok=True)


if __name__ == "__main__":
    if not TTYD_BIN.is_file() or not INDEX.is_file():
        raise SystemExit(f"missing candidate artifacts: {TTYD_BIN} {INDEX}")
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Block004)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    evidence = {
        "schema": "block004-self-check/v1",
        "binarySha256": hashlib.sha256(TTYD_BIN.read_bytes()).hexdigest(),
        "bundleSha256": hashlib.sha256(INDEX.read_bytes()).hexdigest(),
        "scenarios": Block004.evidence,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "operatingPort": 7683,
        "isolatedPortsOnly": True,
        "limits": ["BLOCK-005 buffer/reaper/pruning defects are outside this check", "Android hardware is not exercised"],
    }
    path = EVIDENCE_DIR / "result.json"
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and len(Block004.evidence) == 6 else 1)
