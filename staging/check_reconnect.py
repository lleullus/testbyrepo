#!/usr/bin/env python3
import base64
import json
import os
import hashlib
from pathlib import Path
import re
import signal
import shlex
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build' / 'ttyd'))
INDEX = Path(os.environ.get('WEBTERM_TEST_INDEX', ROOT / 'html' / 'dist' / 'inline.html'))
MANUAL_TARGET = os.environ.get('WEBTERM_TEST_MANUAL', '')
RETRY_OPEN_CLOSE_TEST = os.environ.get('WEBTERM_TEST_RETRY_OPEN_CLOSE') == '1'
EVIDENCE_PATH = os.environ.get('WEBTERM_EVIDENCE_PATH')


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_http(url, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return response.read()
        except Exception:
            time.sleep(0.1)
    raise AssertionError(f'server not ready: {url}')


class TcpProxy:
    def __init__(self, listen_port, target_port):
        self.listen_port = listen_port
        self.target_port = target_port
        self.blackholed_bytes = 0
        self.filtered_frame_prefixes = []
        self.control_frames = []
        self.blocked = False
        self.drop_heartbeat_replies = False
        self.drop_after_upgrade = False
        self.upgrade_drops = 0
        self.stopped = False
        self.lock = threading.Lock()
        self.connections = set()
        self.pairs = []
        self.next_pair_id = 0
        self.next_websocket_index = 0
        self.blocked_websockets = set()
        self.preserved_client_eof = 0
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(('127.0.0.1', listen_port))
        self.listener.listen()
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.thread.start()

    def _accept_loop(self):
        while not self.stopped:
            try:
                client, _ = self.listener.accept()
            except OSError:
                return
            if self.blocked:
                client.close()
                continue
            try:
                upstream = socket.create_connection(('127.0.0.1', self.target_port), timeout=2)
                upstream.settimeout(None)
            except OSError:
                client.close()
                continue
            with self.lock:
                self.next_pair_id += 1
                pair = {
                    'id': self.next_pair_id,
                    'client': client,
                    'upstream': upstream,
                    'websocket_index': None,
                    'active': True,
                    'client_pending': b'',
                    'server_pending': b'',
                }
                self.pairs.append(pair)
                self.connections.add(client)
                self.connections.add(upstream)
            threading.Thread(target=self._pump, args=(pair, client, upstream, False), daemon=True).start()
            threading.Thread(target=self._pump, args=(pair, upstream, client, True), daemon=True).start()

    @staticmethod
    def _frame_parts(frame):
        length = frame[1] & 0x7F
        header_len = 2
        if length == 126:
            length = int.from_bytes(frame[2:4], 'big')
            header_len = 4
        elif length == 127:
            length = int.from_bytes(frame[2:10], 'big')
            header_len = 10
        masked = bool(frame[1] & 0x80)
        if masked:
            mask = frame[header_len:header_len + 4]
            header_len += 4
        payload = frame[header_len:header_len + length]
        if masked:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        return frame[0] & 0x0F, payload

    def _forward_frames(self, pair, data, target, upstream_to_client):
        key = 'server_pending' if upstream_to_client else 'client_pending'
        pending = pair[key] + data
        while len(pending) >= 2:
            length = pending[1] & 0x7F
            header_len = 2
            if length == 126:
                if len(pending) < 4:
                    break
                length = int.from_bytes(pending[2:4], 'big')
                header_len = 4
            elif length == 127:
                if len(pending) < 10:
                    break
                length = int.from_bytes(pending[2:10], 'big')
                header_len = 10
            if pending[1] & 0x80:
                header_len += 4
            frame_len = header_len + length
            if len(pending) < frame_len:
                break
            frame = pending[:frame_len]
            pending = pending[frame_len:]
            opcode, payload = self._frame_parts(frame)
            direction = 'server-to-client' if upstream_to_client else 'client-to-server'
            websocket_index = pair['websocket_index']
            if opcode >= 8:
                with self.lock:
                    self.control_frames.append(
                        {
                            'websocket': websocket_index,
                            'direction': direction,
                            'opcode': opcode,
                            'payload': payload.hex(),
                        }
                    )
            if upstream_to_client and self.drop_heartbeat_replies:
                with self.lock:
                    self.filtered_frame_prefixes.append((opcode, payload[:16].hex()))
            blocked = websocket_index in self.blocked_websockets
            heartbeat_dropped = upstream_to_client and self.drop_heartbeat_replies and opcode == 2 and payload[:1] == b'5'
            if blocked or heartbeat_dropped:
                with self.lock:
                    self.blackholed_bytes += frame_len
                continue
            target.sendall(frame)
        pair[key] = pending

    def _pump(self, pair, source, target, upstream_to_client):
        response_pending = b''
        response_complete = not upstream_to_client
        passthrough = False
        try:
            while True:
                data = source.recv(65536)
                if not data:
                    break
                if not upstream_to_client:
                    if pair['websocket_index'] is None:
                        target.sendall(data)
                    else:
                        self._forward_frames(pair, data, target, False)
                    continue
                if passthrough:
                    target.sendall(data)
                    continue

                response_pending += data
                if not response_complete:
                    marker = response_pending.find(b'\r\n\r\n')
                    if marker < 0:
                        continue
                    marker += 4
                    headers = response_pending[:marker]
                    target.sendall(headers)
                    response_pending = response_pending[marker:]
                    if b' 101 ' not in headers.split(b'\r\n', 1)[0]:
                        target.sendall(response_pending)
                        response_pending = b''
                        passthrough = True
                        continue
                    with self.lock:
                        self.next_websocket_index += 1
                        pair['websocket_index'] = self.next_websocket_index
                    response_complete = True
                    if self.drop_after_upgrade:
                        with self.lock:
                            self.upgrade_drops += 1
                        break

                if response_pending:
                    self._forward_frames(pair, response_pending, target, True)
                    response_pending = b''
        except OSError:
            pass
        finally:
            websocket_index = pair['websocket_index']
            preserve_upstream = not upstream_to_client and websocket_index in self.blocked_websockets and not self.stopped
            if preserve_upstream:
                with self.lock:
                    self.preserved_client_eof += 1
                    self.connections.discard(source)
                try:
                    source.close()
                except OSError:
                    pass
                return
            pair['active'] = False
            for sock in (source, target):
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass
                with self.lock:
                    self.connections.discard(sock)

    def blackhole(self):
        self.drop_heartbeat_replies = True

    def blackhole_current_websocket(self):
        with self.lock:
            active = [pair for pair in self.pairs if pair['active'] and pair['websocket_index'] is not None]
            if not active:
                raise AssertionError('no active websocket to blackhole')
            index = max(pair['websocket_index'] for pair in active)
            self.blocked_websockets.add(index)
            return index

    def frames_for(self, websocket_index):
        with self.lock:
            return [frame.copy() for frame in self.control_frames if frame['websocket'] == websocket_index]

    def disconnect(self):
        self.blocked = True
        with self.lock:
            sockets = list(self.connections)
        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def drop_each_upgrade(self):
        self.disconnect()
        self.blocked = False
        self.drop_after_upgrade = True

    def reconnect(self):
        self.blocked = False
        self.drop_heartbeat_replies = False
        self.drop_after_upgrade = False

    def close(self):
        self.stopped = True
        try:
            self.listener.close()
        except OSError:
            pass
        self.disconnect()


ttyd_port = free_port()
proxy_port = free_port()
direct_http = f'http://127.0.0.1:{ttyd_port}/'
http = f'http://127.0.0.1:{proxy_port}/'
env = os.environ.copy()
env['TTYD_RECONNECT_GRACE'] = '180' if (MANUAL_TARGET or RETRY_OPEN_CLOSE_TEST) else '90'
env['TTYD_DIAGNOSTICS'] = '1'
ttyd = subprocess.Popen(
    [
        str(TTYD_BIN),
        '-W',
        '-P',
        '60',
        '-i',
        '127.0.0.1',
        '-p',
        str(ttyd_port),
        '-I',
        str(INDEX),
        '/bin/bash',
        '-l',
    ],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    start_new_session=True,
)
proxy = TcpProxy(proxy_port, ttyd_port)

chrome_port = free_port()
profile = tempfile.TemporaryDirectory(prefix='webterm-reconnect-chrome-')
chrome = subprocess.Popen(
    [
        'google-chrome',
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--remote-allow-origins=*',
        f'--remote-debugging-port={chrome_port}',
        f'--user-data-dir={profile.name}',
        'about:blank',
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)

ws = None
next_id = 0


def http_json(url, method='GET'):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def call(method, params=None):
    global next_id
    next_id += 1
    command_id = next_id
    ws.send(json.dumps({'id': command_id, 'method': method, 'params': params or {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get('id') != command_id:
            continue
        if 'error' in message:
            raise RuntimeError(f"CDP {method}: {message['error']}")
        return message.get('result', {})


def evaluate(expression):
    result = call('Runtime.evaluate', {'expression': expression, 'returnByValue': True})
    return result.get('result', {}).get('value')


def wait_until(expression, timeout=10):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = evaluate(expression)
        if last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'wait timeout: {expression}; last={last!r}')


def click_selector(selector):
    rect = wait_until(
        f"(() => {{ const e=document.querySelector({json.dumps(selector)}); if (!e) return null; const r=e.getBoundingClientRect(); return r.width && r.height ? {{x:r.x+r.width/2,y:r.y+r.height/2}} : null; }})()"
    )
    call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': rect['x'], 'y': rect['y'], 'button': 'left', 'clickCount': 1})
    call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': rect['x'], 'y': rect['y'], 'button': 'left', 'clickCount': 1})


def diagnostics():
    return evaluate("window.ttydDiagnostics ? window.ttydDiagnostics() : null")


def emit_result(result):
    screenshot = call('Page.captureScreenshot', {'format': 'png'}).get('data')
    if EVIDENCE_PATH:
        path = Path(EVIDENCE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path = path.with_suffix('.png')
        screenshot_bytes = base64.b64decode(screenshot)
        screenshot_path.write_bytes(screenshot_bytes)
        result['screenshot'] = str(screenshot_path)
        result['screenshotSha256'] = hashlib.sha256(screenshot_bytes).hexdigest()
        path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


def term_input(text):
    evaluate(f"window.term.input({json.dumps(text)}, true)")
    time.sleep(0.05)


def send_command(command):
    term_input(command)
    term_input('\r')


def buffer_text(lines=240):
    return evaluate(
        f"""(() => {{
            const term = window.term;
            if (!term) return '';
            const b = term.buffer.active;
            const out = [];
            for (let i = Math.max(0, b.length - {lines}); i < b.length; i++) {{
                const line = b.getLine(i);
                if (line) out.push(line.translateToString(true));
            }}
            return out.join('\\n');
        }})()"""
    )


def wait_text(marker, timeout=10):
    deadline = time.time() + timeout
    last = ''
    while time.time() < deadline:
        last = buffer_text()
        if marker in last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'missing marker {marker!r}; tail={last[-1800:]}')



def wait_pid(label, timeout=10):
    deadline = time.time() + timeout
    last = ''
    pattern = re.compile(re.escape(label) + r'=(\d+)')
    while time.time() < deadline:
        last = buffer_text()
        matches = pattern.findall(last)
        if matches:
            return int(matches[-1])
        time.sleep(0.1)
    raise AssertionError(f'missing numeric pid marker {label}: {last[-1500:]}')

def raw_duplicate(resume_id):
    with urllib.request.urlopen(http + 'token', timeout=5) as response:
        auth_token = json.load(response).get('token', '')
    contender = websocket.create_connection(
        f'ws://127.0.0.1:{proxy_port}/ws?resume={resume_id}',
        subprotocols=['tty'],
        origin=http.rstrip('/'),
        timeout=15,
    )
    contender.send_binary(
        json.dumps(
            {
                'version': 4,
                'intent': 'resume',
                'replayPosition': 0,
                'AuthToken': auth_token,
                'columns': 111,
                'rows': 33,
            }
        ).encode()
    )
    states = []
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            message = contender.recv()
            if not isinstance(message, bytes) or message[:1] != b'3':
                continue
            state = json.loads(message[1:])
            assert state['version'] == 4, state
            states.append(state['state'])
            if state['state'] == 'checking':
                contender.send_binary(b'0echo CONTENDER_SHOULD_NOT_RUN\r')
                contender.send_binary(b'1' + json.dumps({'columns': 111, 'rows': 33}).encode())
            elif state['state'] == 'conflict':
                return states
            else:
                raise AssertionError(state)
    finally:
        contender.close()
    raise AssertionError(f'raw contender did not settle: {states}')


def challenge_roundtrip(frames):
    pings = [frame for frame in frames if frame['direction'] == 'server-to-client' and frame['opcode'] == 9 and len(frame['payload']) == 32]
    pongs = [frame for frame in frames if frame['direction'] == 'client-to-server' and frame['opcode'] == 10]
    return bool(pings) and any(pong['payload'] == pings[-1]['payload'] for pong in pongs)


try:
    wait_http(direct_http + 'token')
    deadline = time.time() + 8
    while True:
        try:
            http_json(f'http://127.0.0.1:{chrome_port}/json/version')
            break
        except Exception:
            if time.time() > deadline:
                raise
            time.sleep(0.1)

    target = http_json(f'http://127.0.0.1:{chrome_port}/json/new?about:blank', method='PUT')
    ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=10)
    call('Page.enable')
    call('Runtime.enable')
    call('Network.enable')
    call('Page.bringToFront')
    call('Page.navigate', {'url': http + '?diagnostics=1&disableLeaveAlert=true'})
    wait_until("document.readyState === 'complete' && Boolean(window.term) && Boolean(window.ttydDiagnostics)")
    wait_until("document.body.innerText.includes('No saved tab session')")
    click_selector('.terminal-container button')
    wait_until("window.ttydDiagnostics().state === 'application-ready'", timeout=15)
    assert evaluate("document.visibilityState") == 'visible'

    pid_command = "export WEBTERM_TEST_SHELL_PID=$BASHPID; echo BROWSER_PID_BEFORE=$WEBTERM_TEST_SHELL_PID"
    send_command(pid_command)
    pid_before = wait_pid('BROWSER_PID_BEFORE')

    if MANUAL_TARGET or RETRY_OPEN_CLOSE_TEST:
        target_kind = MANUAL_TARGET or 'overlay'
        assert target_kind in ('overlay', 'toolbar'), target_kind
        capture_path = Path(profile.name) / f'pty-{target_kind}.bin'
        payload = f'POST_READY_{target_kind.upper()}'.encode()
        send_command('stty -echo')
        time.sleep(0.2)
        reader = (
            'import os,tty;'
            'tty.setraw(0);'
            f'f=open({str(capture_path)!r},"wb",buffering=0);'
            "os.write(1,b'\\r\\nCAPTURE_ARMED_7B91\\r\\n');"
            f'd=os.read(0,{len(payload)});f.write(d);'
            "os.write(1,b'\\r\\nCAPTURE_COMPLETE_7B91\\r\\n')"
        )
        send_command('python3 -c ' + shlex.quote(reader))
        wait_text('CAPTURE_ARMED_7B91')
        assert capture_path.exists() and capture_path.stat().st_size == 0

        disconnected_at = time.monotonic()
        if RETRY_OPEN_CLOSE_TEST:
            proxy.drop_each_upgrade()
        else:
            proxy.disconnect()
        wait_until("window.ttydDiagnostics().state === 'disconnected'", timeout=70)
        wait_until("document.body.innerText.includes('Automatic recovery paused')", timeout=70)
        stopped_after = time.monotonic() - disconnected_at
        assert 58 <= stopped_after <= 68, stopped_after
        assert capture_path.stat().st_size == 0, capture_path.read_bytes()
        before_recovery = diagnostics()

        proxy.reconnect()
        click_selector('.terminal-container button' if target_kind == 'overlay' else '.enter-button')
        wait_until("window.ttydDiagnostics().state === 'application-ready'", timeout=20)
        assert capture_path.stat().st_size == 0, capture_path.read_bytes()
        term_input(payload.decode())
        deadline = time.time() + 5
        while time.time() < deadline and capture_path.stat().st_size < len(payload):
            time.sleep(0.05)
        captured = capture_path.read_bytes()
        assert captured == payload, (captured, payload)
        after_recovery = diagnostics()
        os.kill(pid_before, 0)
        emit_result(
            {
                'mode': f'manual-{target_kind}',
                'pidStillAlive': pid_before,
                'automaticRetryStoppedAfterSeconds': round(stopped_after, 2),
                'websocketUpgradeDrops': proxy.upgrade_drops,
                'ptyBytesDuringRecovery': 0,
                'postReadyPayloadBytes': len(payload),
                'postReadyPayloadDeliveries': 1,
                'generationBeforeRecovery': before_recovery['connectionGeneration'],
                'generationAfterRecovery': after_recovery['connectionGeneration'],
                'inputReady': after_recovery['inputReady'],
                'PASS': True,
            }
        )
        raise SystemExit(0)

    stored_session = json.loads(
        evaluate(
            "(() => { const k=Object.keys(sessionStorage).find(k => k.startsWith('webterm.session.v1:')); return k ? sessionStorage.getItem(k) : null; })()"
        )
    )
    live_owner_websocket = proxy.next_websocket_index
    visible_frames_before = len(proxy.frames_for(live_owner_websocket))
    visible_duplicate_states = raw_duplicate(stored_session['id'])
    visible_frames = proxy.frames_for(live_owner_websocket)[visible_frames_before:]
    assert visible_duplicate_states == ['checking', 'conflict'], visible_duplicate_states
    assert challenge_roundtrip(visible_frames), visible_frames

    hidden_target = http_json(f'http://127.0.0.1:{chrome_port}/json/new?about:blank', method='PUT')
    call('Target.activateTarget', {'targetId': hidden_target['id']})
    wait_until("document.visibilityState === 'hidden'", timeout=5)
    hidden_frames_before = len(proxy.frames_for(live_owner_websocket))
    hidden_duplicate_states = raw_duplicate(stored_session['id'])
    hidden_frames = proxy.frames_for(live_owner_websocket)[hidden_frames_before:]
    assert hidden_duplicate_states == ['checking', 'conflict'], hidden_duplicate_states
    assert challenge_roundtrip(hidden_frames), hidden_frames
    call('Page.bringToFront')
    wait_until("document.visibilityState === 'visible'", timeout=5)
    call('Target.closeTarget', {'targetId': hidden_target['id']})

    send_command("printf 'OWNER_GEOMETRY='; stty size")
    geometry_text = wait_text('OWNER_GEOMETRY=')
    geometry_match = re.findall(r'OWNER_GEOMETRY=(\d+)\s+(\d+)', geometry_text)
    assert geometry_match and geometry_match[-1] != ('33', '111'), geometry_match
    assert 'CONTENDER_SHOULD_NOT_RUN' not in geometry_text, geometry_text[-2000:]

    session_storage_before = evaluate(
        "(() => { const k=Object.keys(sessionStorage).find(k => k.startsWith('webterm.session.v1:')); return k ? sessionStorage.getItem(k) : null; })()"
    )
    diagnostic_before_reload = diagnostics()
    send_command('export WEBTERM_RELOAD_MARKER=preserved; echo RELOAD_CONTEXT=$WEBTERM_RELOAD_MARKER')
    wait_text('RELOAD_CONTEXT=preserved')
    call('Page.navigate', {'url': http + '?diagnostics=1&disableLeaveAlert=true'})
    wait_until("document.readyState === 'complete' && Boolean(window.term) && Boolean(window.ttydDiagnostics)")
    reload_state = wait_until(
        "['application-ready','session-conflict'].includes(window.ttydDiagnostics().state) && window.ttydDiagnostics().state",
        timeout=20,
    )
    reload_conflict_retried = reload_state == 'session-conflict'
    if reload_conflict_retried:
        time.sleep(0.3)
        click_selector('.terminal-container button')
        wait_until("window.ttydDiagnostics().state === 'application-ready'", timeout=20)
    session_storage_after = evaluate(
        "(() => { const k=Object.keys(sessionStorage).find(k => k.startsWith('webterm.session.v1:')); return k ? sessionStorage.getItem(k) : null; })()"
    )
    assert session_storage_before and session_storage_after == session_storage_before
    reload_text = wait_text('RELOAD_CONTEXT=preserved')
    diagnostic_after_reload = diagnostics()
    assert diagnostic_after_reload['sessionDiagnosticId'] == diagnostic_before_reload['sessionDiagnosticId']

    send_command('echo BROWSER_PID_AFTER_RELOAD=$BASHPID')
    pid_after_reload = wait_pid('BROWSER_PID_AFTER_RELOAD')
    assert pid_after_reload == pid_before, (pid_before, pid_after_reload)
    checking_capture_path = Path(profile.name) / 'pty-checking.bin'
    checking_payload = b'POST_CHECK_READY_R2'
    send_command('stty -echo')
    time.sleep(0.2)
    checking_reader = (
        'import os,tty;'
        'tty.setraw(0);'
        f'f=open({str(checking_capture_path)!r},"wb",buffering=0);'
        "os.write(1,b'\\r\\nCHECKING_CAPTURE_ARMED\\r\\n');"
        f'd=os.read(0,{len(checking_payload)});f.write(d);'
        "os.write(1,b'\\r\\nCHECKING_CAPTURE_COMPLETE\\r\\n')"
    )
    send_command('python3 -c ' + shlex.quote(checking_reader))
    wait_text('CHECKING_CAPTURE_ARMED')
    assert checking_capture_path.exists() and checking_capture_path.stat().st_size == 0


    blackhole_generation = diagnostics()['connectionGeneration']
    blackhole_started = time.monotonic()
    stale_owner_websocket = proxy.blackhole_current_websocket()
    try:
        wait_until(
            "window.ttydDiagnostics().events.some(e => e.event === 'heartbeat-timeout')",
            timeout=45,
        )
        wait_until("window.ttydDiagnostics().state === 'checking-owner'", timeout=10)
    except AssertionError as error:
        raise AssertionError(
            f'{error}; serverFrames={proxy.filtered_frame_prefixes[-20:]}; controls={proxy.frames_for(stale_owner_websocket)[-20:]}'
        ) from error
    liveness_during = diagnostics()
    checking_event = next(event for event in reversed(liveness_during['events']) if event['event'] == 'session-checking')
    checking_screenshot_path = None
    if EVIDENCE_PATH:
        checking_screenshot_path = str(Path(EVIDENCE_PATH).with_name(Path(EVIDENCE_PATH).stem + '-checking.png'))
        Path(checking_screenshot_path).write_bytes(base64.b64decode(call('Page.captureScreenshot', {'format': 'png'})['data']))
    checking_generation = diagnostics()['connectionGeneration']
    click_selector('.terminal-container')
    click_selector('.enter-button')
    click_selector('.enter-button')
    assert diagnostics()['connectionGeneration'] == checking_generation
    assert checking_capture_path.stat().st_size == 0, checking_capture_path.read_bytes()
    assert proxy.blackholed_bytes > 0, proxy.blackholed_bytes
    blackhole_duration = time.monotonic() - blackhole_started
    wait_until(
        f"window.ttydDiagnostics().state === 'application-ready' && window.ttydDiagnostics().connectionGeneration > {blackhole_generation}",
        timeout=15,
    )
    assert checking_capture_path.stat().st_size == 0, checking_capture_path.read_bytes()
    term_input(checking_payload.decode())
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and checking_capture_path.stat().st_size < len(checking_payload):
        time.sleep(0.05)
    checking_captured = checking_capture_path.read_bytes()
    assert checking_captured == checking_payload, (checking_captured, checking_payload)
    send_command('stty sane')
    liveness_after = diagnostics()
    ready_event = next(
        event
        for event in reversed(liveness_after['events'])
        if event['event'] == 'session-attached' and event['at'] >= checking_event['at']
    )
    owner_check_seconds = (ready_event['at'] - checking_event['at']) / 1000
    stale_controls = proxy.frames_for(stale_owner_websocket)
    stale_pings = [
        frame
        for frame in stale_controls
        if frame['direction'] == 'server-to-client' and frame['opcode'] == 9 and len(frame['payload']) == 32
    ]
    stale_pongs = [
        frame
        for frame in stale_controls
        if frame['direction'] == 'client-to-server' and frame['opcode'] == 10 and stale_pings and frame['payload'] == stale_pings[-1]['payload']
    ]
    assert stale_pings and not stale_pongs, stale_controls
    liveness_after = diagnostics()
    heartbeat_timeout_observed = any(event['event'] == 'heartbeat-timeout' for event in liveness_during['events'])
    assert heartbeat_timeout_observed

    repeat_generations = []
    for _ in range(20):
        generation = diagnostics()['connectionGeneration']
        proxy.disconnect()
        wait_until("window.ttydDiagnostics().state !== 'application-ready'", timeout=5)
        time.sleep(0.1)
        proxy.reconnect()
        wait_until(
            f"window.ttydDiagnostics().state === 'application-ready' && window.ttydDiagnostics().connectionGeneration > {generation}",
            timeout=15,
        )
        repeat_generations.append(diagnostics()['connectionGeneration'])

    send_command('echo BROWSER_PID_FINAL=$BASHPID')
    pid_final = wait_pid('BROWSER_PID_FINAL')
    assert pid_final == pid_before, (pid_before, pid_final)
    final_diagnostic = diagnostics()
    assert not final_diagnostic['connectInFlight']
    assert final_diagnostic['inputReady']

    emit_result(
        {
            'mode': 'same-tab-liveness-repeat',
            'pidBefore': pid_before,
            'pidAfterReload': pid_after_reload,
            'pidFinal': pid_final,
            'sameProcess': True,
            'sameSessionStorage': True,
            'blackholeDetectionSeconds': round(blackhole_duration, 2),
            'liveOwnerWebsocket': live_owner_websocket,
            'visibleDuplicateTransitions': visible_duplicate_states,
            'visibleNativePingPong': challenge_roundtrip(visible_frames),
            'hiddenDuplicateTransitions': hidden_duplicate_states,
            'hiddenNativePingPong': challenge_roundtrip(hidden_frames),
            'contenderInputMarkerAbsent': 'CONTENDER_SHOULD_NOT_RUN' not in geometry_text,
            'contenderResizeRejected': geometry_match[-1] != ('33', '111'),
            'staleOwnerWebsocket': stale_owner_websocket,
            'staleNativePingObserved': bool(stale_pings),
            'staleMatchingPongObserved': bool(stale_pongs),
            'ownerCheckSeconds': round(owner_check_seconds, 3),
            'checkingScreenshot': checking_screenshot_path,
            'oldClientEofPreservedByProxy': proxy.preserved_client_eof,
            'checkingGestureGenerationStable': checking_generation == blackhole_generation + 1,
            'checkingGesturePtyBytes': 0,
            'checkingPostReadyPayloadBytes': len(checking_captured),
            'checkingPostReadyPayloadDeliveries': 1,
            'livenessFailureState': liveness_during['state'],
            'sameDiagnosticSession': True,
            'heartbeatTimeoutObserved': heartbeat_timeout_observed,
            'blackholedBytes': proxy.blackholed_bytes,
            'reloadConflictRetriedAfterOldClose': reload_conflict_retried,
            'replayedMarkerVisible': 'RELOAD_CONTEXT=preserved' in reload_text,
            'blackholeLivenessFailureDetected': True,
            'generationAfterLivenessRecovery': liveness_after['connectionGeneration'],
            'repeatRecoveries': len(repeat_generations),
            'repeatGenerationsStrictlyIncreasing': all(
                later > earlier for earlier, later in zip(repeat_generations, repeat_generations[1:])
            ),
            'finalInputReady': final_diagnostic['inputReady'],
            'finalConnectInFlight': final_diagnostic['connectInFlight'],
            'PASS': True,
        }
    )
finally:
    if ws is not None:
        try:
            ws.close()
        except Exception:
            pass
    proxy.close()
    for proc in (chrome, ttyd):
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
    profile.cleanup()
