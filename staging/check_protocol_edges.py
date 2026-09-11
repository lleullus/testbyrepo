#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import time
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build' / 'ttyd'))
INDEX = ROOT / 'staging' / 'index.html'
PASTE_SIZE = int(os.environ.get('WEBTERM_TEST_PASTE_SIZE', str(64 * 1024)))


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_http(url, timeout=8):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return response.read()
        except Exception as exc:
            last = exc
            time.sleep(0.1)
    raise AssertionError(f'ttyd did not become ready: {url}; last={last!r}')


def token(http):
    with urllib.request.urlopen(http + 'token', timeout=5) as response:
        return json.load(response).get('token', '')


def connect(http, ws_base, resume_id):
    ws = websocket.create_connection(
        f'{ws_base}?resume={resume_id}',
        subprotocols=['tty'],
        origin=http.rstrip('/'),
        timeout=5,
    )
    auth = json.dumps({'AuthToken': token(http), 'columns': 80, 'rows': 24}).encode()
    ws.send_binary(auth)
    return ws


def wait_session_state(ws, expected=None, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        message = ws.recv()
        if not isinstance(message, bytes) or not message:
            continue
        if message[:1] == b'3':
            state = message[1:].decode('utf-8', errors='replace')
            if expected is not None:
                assert state == expected, (state, expected)
            return state
    raise AssertionError(f'session state not received: {expected}')


def wait_match(ws, pattern, timeout=8):
    text = ''
    regex = re.compile(pattern)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        if not isinstance(message, bytes) or not message or message[:1] != b'0':
            continue
        text += message[1:].decode('utf-8', errors='replace')
        match = regex.search(text)
        if match:
            return match, text
    raise AssertionError(f'pattern not received: {pattern!r}\n{text[-3000:]}')


def send_input(ws, data):
    ws.send_binary(b'0' + data)


def send_command(ws, command):
    send_input(ws, command.encode() + b'\r')


def send_fragmented_input(ws, data, split):
    payload = b'0' + data
    assert 0 < split < len(payload)
    first = websocket.ABNF.create_frame(
        payload[:split], websocket.ABNF.OPCODE_BINARY, fin=0
    )
    second = websocket.ABNF.create_frame(
        payload[split:], websocket.ABNF.OPCODE_CONT, fin=1
    )
    ws.send_frame(first)
    ws.send_frame(second)


if not TTYD_BIN.exists():
    raise SystemExit(
        f'ttyd test binary not found: {TTYD_BIN}; set TTYD_BIN to an explicit verified binary'
    )

port = int(os.environ.get('WEBTERM_TEST_PORT', '7684'))
http = f'http://127.0.0.1:{port}/'
ws_base = f'ws://127.0.0.1:{port}/ws'
proc = subprocess.Popen(
    [
        str(TTYD_BIN),
        '-W',
        '-i',
        '127.0.0.1',
        '-p',
        str(port),
        '-I',
        str(INDEX),
        '/bin/bash',
        '-l',
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
connections = []
results = {
    'ttydBin': str(TTYD_BIN),
    'pasteSize': PASTE_SIZE,
}

try:
    wait_http(http + 'token')
    ws = connect(http, ws_base, 'e' * 32)
    connections.append(ws)
    wait_session_state(ws)

    # Verify that fragmented WebSocket input is reassembled as one ttyd input message.
    send_fragmented_input(ws, b'echo FRAGMENT_OK\r', split=6)
    wait_match(ws, r'FRAGMENT_OK')
    results['fragmentedInput'] = True

    # An empty initial fragment must not be interpreted as a complete ttyd
    # command. The following continuation still carries one valid input message.
    ws.send_frame(websocket.ABNF.create_frame(b'', websocket.ABNF.OPCODE_BINARY, fin=0))
    ws.send_frame(
        websocket.ABNF.create_frame(
            b'0echo EMPTY_FRAGMENT_OK\r', websocket.ABNF.OPCODE_CONT, fin=1
        )
    )
    wait_match(ws, r'EMPTY_FRAGMENT_OK')
    results['emptyLeadingFragment'] = True

    # A completely empty fragmented WebSocket message is also invalid at the
    # ttyd protocol layer but must be harmless to the server process.
    ws.send_frame(websocket.ABNF.create_frame(b'', websocket.ABNF.OPCODE_BINARY, fin=0))
    ws.send_frame(websocket.ABNF.create_frame(b'', websocket.ABNF.OPCODE_CONT, fin=1))
    time.sleep(0.2)
    assert proc.poll() is None, proc.poll()
    send_command(ws, 'echo AFTER_FRAGMENTED_EMPTY_OK')
    wait_match(ws, r'AFTER_FRAGMENTED_EMPTY_OK')
    results['fragmentedEmptyMessage'] = True

    # Put the PTY into non-canonical/no-echo mode, then feed one large ttyd input
    # message to a child that reads an exact byte count and reports its digest.
    send_command(ws, 'stty -icanon -echo min 1 time 0')
    time.sleep(0.2)
    send_command(ws, 'echo RAW_MODE_READY')
    wait_match(ws, r'RAW_MODE_READY')

    payload = bytes(ord('a') + (index % 26) for index in range(PASTE_SIZE))
    expected_sha = hashlib.sha256(payload).hexdigest()
    reader = (
        'import hashlib,sys;'
        f'd=sys.stdin.buffer.read({PASTE_SIZE});'
        "print('PASTE_LEN=%d PASTE_SHA=%s' % (len(d),hashlib.sha256(d).hexdigest()),flush=True)"
    )
    send_command(ws, 'python3 -c ' + shlex.quote(reader))
    time.sleep(0.3)
    send_input(ws, payload)
    match, _ = wait_match(ws, r'PASTE_LEN=(\d+) PASTE_SHA=([0-9a-f]{64})', timeout=15)
    actual_len = int(match.group(1))
    actual_sha = match.group(2)
    results['largeInput'] = {
        'expectedLength': PASTE_SIZE,
        'actualLength': actual_len,
        'expectedSha256': expected_sha,
        'actualSha256': actual_sha,
    }
    assert actual_len == PASTE_SIZE, results['largeInput']
    assert actual_sha == expected_sha, results['largeInput']

    send_command(ws, 'stty sane')
    time.sleep(0.2)
    send_command(ws, 'echo PASTE_OK')
    wait_match(ws, r'PASTE_OK')

    # PAUSE gates only WebSocket transmission. PTY output must continue draining
    # while a 10 MiB writer completes and records its marker before RESUME.
    drain_marker = Path(f'/tmp/webterm-drain-{os.getpid()}.marker')
    overflow_marker = Path(f'/tmp/webterm-overflow-{os.getpid()}.marker')
    redraw_marker = Path(f'/tmp/webterm-redraw-{os.getpid()}.marker')
    for marker in (drain_marker, overflow_marker, redraw_marker):
        marker.unlink(missing_ok=True)

    ws.send_binary(b'2')
    drain_writer = (
        'import os\n'
        'd=b"D"*(10*1024*1024)\n'
        'n=0\n'
        'while n<len(d):\n'
        ' n+=os.write(1,d[n:])\n'
        f'open({str(drain_marker)!r},"w").write("DONE")'
    )
    send_command(ws, 'python3 -c ' + shlex.quote(drain_writer))
    deadline = time.time() + 20
    while time.time() < deadline and not drain_marker.exists():
        time.sleep(0.1)
    assert drain_marker.exists() and drain_marker.read_text() == 'DONE', 'PTY output blocked while PAUSE was active'
    results['continuousDrain'] = {'completedBeforeResume': True, 'marker': str(drain_marker)}
    ws.send_binary(b'3')
    time.sleep(0.2)

    # A detached overflow must persist needs_redraw and signal the foreground
    # shell process group after the resumable reconnect.
    redraw_trap = f"trap 'printf WINCH > {redraw_marker}' WINCH"
    send_command(ws, redraw_trap)
    time.sleep(0.2)
    overflow_writer = (
        'import os\n'
        'd=b"R"*(9*1024*1024)\n'
        'n=0\n'
        'while n<len(d):\n'
        ' n+=os.write(1,d[n:])\n'
        f'open({str(overflow_marker)!r},"w").write("DONE")'
    )
    send_command(ws, '(sleep 0.3; python3 -c ' + shlex.quote(overflow_writer) + ') &')
    ws.close()
    connections.remove(ws)
    deadline = time.time() + 20
    while time.time() < deadline:
        if overflow_marker.exists() and overflow_marker.read_text() == 'DONE':
            break
        time.sleep(0.1)
    assert overflow_marker.exists() and overflow_marker.read_text() == 'DONE', 'detached PTY output did not complete'

    ws = connect(http, ws_base, 'e' * 32)
    connections.append(ws)
    recovery_state = wait_session_state(ws, expected='resumed')
    deadline = time.time() + 8
    while time.time() < deadline and not redraw_marker.exists():
        time.sleep(0.1)
    assert redraw_marker.exists() and redraw_marker.read_text() == 'WINCH', 'foreground SIGWINCH was not observed'
    results['overflowRecovery'] = {
        'sessionState': recovery_state,
        'sigwinchObserved': True,
    }

    # Zero-length WebSocket data is legal at the transport layer. A malformed or
    # empty ttyd message must never kill the server process. Keep this as a permanent
    # regression gate for the receive-path zero-length guard.
    ws.send_binary(b'')
    time.sleep(0.5)
    process_alive = proc.poll() is None
    results['emptyFrame'] = {
        'serverAlive': process_alive,
        'returnCode': proc.poll(),
        'newConnectionAccepted': False,
    }

    if process_alive:
        wait_http(http + 'token', timeout=3)
        ws_after = connect(http, ws_base, 'f' * 32)
        connections.append(ws_after)
        wait_session_state(ws_after)
        send_command(ws_after, 'echo AFTER_EMPTY_OK')
        wait_match(ws_after, r'AFTER_EMPTY_OK')
        results['emptyFrame']['newConnectionAccepted'] = True

    assert results['emptyFrame']['serverAlive'], results['emptyFrame']
    assert results['emptyFrame']['newConnectionAccepted'], results['emptyFrame']

    results['PASS'] = True
    print(json.dumps(results, indent=2))
finally:
    for connection in connections:
        try:
            connection.close()
        except Exception:
            pass
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    if not results.get('PASS'):
        results['serverReturnCode'] = proc.poll()
        try:
            stdout, stderr = proc.communicate(timeout=1)
        except Exception:
            stdout, stderr = '', ''
        results['serverStdoutTail'] = stdout[-2000:]
        results['serverStderrTail'] = stderr[-4000:]
        print(json.dumps(results, indent=2))
