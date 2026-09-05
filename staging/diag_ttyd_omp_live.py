#!/usr/bin/env python3
import base64
import glob
import json
import os
import shlex
import socket
import subprocess
import tempfile
import time
import urllib.parse
import uuid
import urllib.request

import websocket

TTYD_BIN = "/home/user01/.local/bin/ttyd"
INDEX = "/home/user01/.local/share/webterm/index.html"
SESSION_SH = "/home/user01/.local/share/webterm/session.sh"
OMP = "/home/user01/.bun/bin/omp"
PROJECT = "/home/user01/project/webterm/ttyd-1.7.7"
SESS_GLOB = os.path.expanduser("~/.omp/agent/sessions/**/*.jsonl")


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_http(url, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                response.read(32)
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"http timeout: {url}")


def http_json(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


class Page:
    def __init__(self, chrome_port, url):
        target = http_json(
            f"http://127.0.0.1:{chrome_port}/json/new?{urllib.parse.quote(url, safe=':/?=&')}",
            method="PUT",
        )
        self.ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=10)
        self.next_id = 0
        self.events = []
        self.call("Page.enable")
        self.call("Runtime.enable")
        self.call("Network.enable")
        self.call("Page.navigate", {"url": url})
        self.wait("document.readyState === 'complete' && Boolean(window.term)", 10)
        time.sleep(0.5)

    def _handle(self, message):
        obj = json.loads(message)
        if "method" in obj:
            self.events.append(obj)
        return obj

    def call(self, method, params=None):
        self.next_id += 1
        command_id = self.next_id
        self.ws.send(json.dumps({"id": command_id, "method": method, "params": params or {}}))
        while True:
            obj = self._handle(self.ws.recv())
            if obj.get("id") != command_id:
                continue
            if "error" in obj:
                raise RuntimeError(f"CDP {method}: {obj['error']}")
            return obj.get("result", {})

    def evaluate(self, expression):
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
                "userGesture": True,
            },
        )
        return result.get("result", {}).get("value")

    def wait(self, expression, timeout=8):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            last = self.evaluate(expression)
            if last:
                return last
            time.sleep(0.1)
        raise RuntimeError(f"wait timeout: {expression}; last={last!r}")

    def input(self, text):
        self.evaluate(f"window.term.input({json.dumps(text)}, true)")

    def command(self, command):
        self.input(command)
        self.input("\r")

    def press_enter(self):
        self.evaluate("document.querySelector('.xterm-helper-textarea')?.focus()")
        key = {
            "key": "Enter",
            "code": "Enter",
            "windowsVirtualKeyCode": 13,
            "nativeVirtualKeyCode": 13,
        }
        self.call("Input.dispatchKeyEvent", {"type": "keyDown", **key})
        self.call("Input.dispatchKeyEvent", {"type": "keyUp", **key})

    def text(self, lines=250):
        return self.evaluate(
            f"""(() => {{
              const b=window.term.buffer.active,out=[];
              for(let i=Math.max(0,b.length-{lines}); i<b.length; i++) {{
                const l=b.getLine(i); if(l) out.push(l.translateToString(true));
              }}
              return out.join('\\n');
            }})()"""
        ) or ""

    def wait_text(self, marker, timeout=20):
        deadline = time.time() + timeout
        last = ""
        while time.time() < deadline:
            last = self.text()
            if marker in last:
                return last
            time.sleep(0.2)
        raise RuntimeError(f"missing {marker!r}; tail={last[-2500:]}")

    def drain_events(self):
        old_timeout = self.ws.gettimeout()
        self.ws.settimeout(0.02)
        try:
            while True:
                try:
                    self._handle(self.ws.recv())
                except websocket.WebSocketTimeoutException:
                    break
        finally:
            self.ws.settimeout(old_timeout)

    def flow_frames(self):
        self.drain_events()
        frames = []
        for event in self.events:
            if event.get("method") != "Network.webSocketFrameSent":
                continue
            response = event.get("params", {}).get("response", {})
            payload = response.get("payloadData", "")
            opcode = response.get("opcode")
            if opcode == 2:
                try:
                    decoded = base64.b64decode(payload).decode("latin1")
                except Exception:
                    decoded = payload
            else:
                decoded = payload
            if decoded in ("2", "3"):
                frames.append(decoded)
        return frames

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def sessions_snapshot():
    snapshot = {}
    for path in glob.glob(SESS_GLOB, recursive=True):
        try:
            stat = os.stat(path)
            snapshot[path] = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            pass
    return snapshot


def find_session(before, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        candidates = []
        for path, meta in sessions_snapshot().items():
            if path in before and meta == before[path]:
                continue
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    header = json.loads(handle.readline())
                if os.path.realpath(str(header.get("cwd", ""))) == os.path.realpath(PROJECT):
                    candidates.append((meta[0], path, header))
            except Exception:
                pass
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1], candidates[0][2]
        time.sleep(0.2)
    raise RuntimeError("could not locate new OMP session")


server_port = free_port()
chrome_port = free_port()
profile = tempfile.TemporaryDirectory(prefix="ttyd-live-diag-chrome-")
server_env = os.environ.copy()
server_env["OMP_LOCAL_LIVE_RESUME"] = "1"
server = subprocess.Popen(
    [
        TTYD_BIN,
        "-W",
        "-i",
        "127.0.0.1",
        "-p",
        str(server_port),
        "-I",
        INDEX,
        SESSION_SH,
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    env=server_env,
    start_new_session=True,
)
chrome = subprocess.Popen(
    [
        "google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--remote-allow-origins=*",
        f"--remote-debugging-port={chrome_port}",
        f"--user-data-dir={profile.name}",
        "about:blank",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)
page1 = None
page2 = None
gate_file = None
try:
    wait_http(f"http://127.0.0.1:{server_port}/token")
    wait_http(f"http://127.0.0.1:{chrome_port}/json/version")
    before = sessions_snapshot()
    url = f"http://127.0.0.1:{server_port}/?disableLeaveAlert=1"

    page1 = Page(chrome_port, url)
    token = uuid.uuid4().hex[:12]
    start_marker = f"TTYD_START_{token}"
    mid_marker = f"TTYD_MID_{token}"
    end_marker = f"TTYD_END_{token}"
    gate_file = f"/tmp/ttyd-live-gate-{token}"
    prompt = (
        "Use the bash tool exactly once. In that bash command print the value of LIVE_START_MARKER, "
        "wait until the file named by LIVE_GATE_FILE exists, print the value of LIVE_MID_MARKER, "
        "sleep for two seconds, then print the value of LIVE_END_MARKER. After the tool finishes reply with FINISHED."
    )
    command1 = (
        f"cd {shlex.quote(PROJECT)} && "
        f"LIVE_START_MARKER={shlex.quote(start_marker)} "
        f"LIVE_MID_MARKER={shlex.quote(mid_marker)} "
        f"LIVE_END_MARKER={shlex.quote(end_marker)} "
        f"LIVE_GATE_FILE={shlex.quote(gate_file)} "
        f"{shlex.quote(OMP)} --auto-approve --no-title --max-time=90 {shlex.quote(prompt)}"
    )
    page1.command(command1)
    page1.wait_text(start_marker, timeout=35)
    session_path, header = find_session(before)
    session_id = header.get("id") or header.get("sessionId")

    page2 = Page(chrome_port, url)
    command2 = (
        f"cd {shlex.quote(PROJECT)} && "
        f"{shlex.quote(OMP)} --resume {shlex.quote(session_path)} --auto-approve --no-title --max-time=90"
    )
    page2.command(command2)
    second_initial = page2.wait_text("Joined collab session", timeout=40)
    joined_before_mid = mid_marker not in page1.text()
    with open(gate_file, "w", encoding="utf-8") as gate:
        gate.write("go\n")

    first_mid = False
    second_mid = False
    first_end = False
    second_end = False
    deadline = time.time() + 20
    while time.time() < deadline:
        text1 = page1.text()
        text2 = page2.text()
        first_mid = first_mid or (mid_marker in text1)
        second_mid = second_mid or (mid_marker in text2)
        first_end = first_end or (end_marker in text1)
        second_end = second_end or (end_marker in text2)
        if first_end and second_end:
            break
        time.sleep(0.25)

    result = {
        "ttydBin": TTYD_BIN,
        "index": INDEX,
        "sessionPath": session_path,
        "sessionId": session_id,
        "startMarker": start_marker,
        "midMarker": mid_marker,
        "endMarker": end_marker,
        "firstSawStart": True,
        "joinedBeforeMid": joined_before_mid,
        "firstSawMid": first_mid,
        "secondSawMidLive": second_mid,
        "firstSawEnd": first_end,
        "secondSawEndLive": second_end,
        "secondInitialHadStart": start_marker in second_initial,
        "firstFlowFrames": page1.flow_frames(),
        "secondFlowFrames": page2.flow_frames(),
        "secondTail": page2.text()[-3000:],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
finally:
    if gate_file:
        try:
            os.remove(gate_file)
        except FileNotFoundError:
            pass
    if page1:
        page1.close()
    if page2:
        page2.close()
    for process in (chrome, server):
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
    profile.cleanup()
