#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build-native' / 'ttyd'))
INDEX = ROOT / 'staging' / 'index.html'
GRACE = int(os.environ.get('WEBTERM_TEST_GRACE', '2'))


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
    raise AssertionError(f'ttyd did not become ready: {url}')


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


def recv_output(ws, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        message = ws.recv()
        if isinstance(message, bytes) and message[:1] == b'0':
            return message[1:].decode('utf-8', errors='replace')
    raise AssertionError('terminal output not received')


def wait_session_state(ws, expected, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        message = ws.recv()
        if not isinstance(message, bytes) or not message:
            continue
        if message[:1] == b'3':
            state = message[1:].decode('utf-8', errors='replace')
            assert state == expected, (state, expected)
            return state
    raise AssertionError(f'session state not received: {expected}')


def wait_match(ws, pattern, timeout=5):
    text = ''
    deadline = time.time() + timeout
    regex = re.compile(pattern)
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
    raise AssertionError(f'pattern not received: {pattern!r}\n{text[-2000:]}')


def shell_pid(ws, label):
    ws.send_binary(b'0echo ' + label.encode() + b'=$$\r')
    match, _ = wait_match(ws, re.escape(label) + r'=(\d+)')
    return int(match.group(1))


def disable_echo(ws):
    ws.send_binary(b'0stty -echo\r')
    time.sleep(0.1)


def set_marker(ws, value):
    ws.send_binary(f'0export WEBTERM_RESUME_MARKER={value}\r'.encode())
    ws.send_binary(b'0echo MARKER_SET=$WEBTERM_RESUME_MARKER\r')
    match, _ = wait_match(ws, r'MARKER_SET=([A-Za-z0-9_-]+)')
    assert match.group(1) == value, match.group(1)


def marker(ws):
    ws.send_binary(b'0echo MARKER_NOW=$WEBTERM_RESUME_MARKER\r')
    match, _ = wait_match(ws, r'MARKER_NOW=([A-Za-z0-9_-]*)')
    return match.group(1)


port = free_port()
http = f'http://127.0.0.1:{port}/'
ws_base = f'ws://127.0.0.1:{port}/ws'
env = os.environ.copy()
env['TTYD_RECONNECT_GRACE'] = str(GRACE)
deps_lib = ROOT / '.build-deps' / 'root' / 'usr' / 'lib' / 'x86_64-linux-gnu'
env['LD_LIBRARY_PATH'] = str(deps_lib) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
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
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

resume_a = 'a' * 32
resume_b = 'b' * 32
connections = []
try:
    wait_http(http + 'token')

    ws_a1 = connect(http, ws_base, resume_a)
    connections.append(ws_a1)
    wait_session_state(ws_a1, 'fresh')
    pid_a1 = shell_pid(ws_a1, 'PID_A1')
    disable_echo(ws_a1)
    set_marker(ws_a1, 'preserved')

    ws_b = connect(http, ws_base, resume_b)
    connections.append(ws_b)
    wait_session_state(ws_b, 'fresh')
    pid_b = shell_pid(ws_b, 'PID_B')
    assert pid_b != pid_a1, (pid_a1, pid_b)

    # Same page id takes over a stale active connection without replacing the PTY.
    ws_a2 = connect(http, ws_base, resume_a)
    connections.append(ws_a2)
    wait_session_state(ws_a2, 'resumed')
    pid_a2 = shell_pid(ws_a2, 'PID_A2')
    assert pid_a2 == pid_a1, (pid_a1, pid_a2)
    assert marker(ws_a2) == 'preserved'

    # Generate output after the websocket is gone. It must be drained from the
    # PTY, buffered by ttyd, and replayed on the next attach in raw ANSI order.
    ws_a2.send_binary(b'0(sleep 0.35; echo DETACHED_OUTPUT=$$) &\r')
    ws_a2.close()
    connections.remove(ws_a2)
    time.sleep(0.7)

    ws_a3 = connect(http, ws_base, resume_a)
    connections.append(ws_a3)
    wait_session_state(ws_a3, 'resumed')
    match, backlog_text = wait_match(ws_a3, r'DETACHED_OUTPUT=(\d+)', timeout=5)
    assert int(match.group(1)) == pid_a1, backlog_text[-1500:]
    pid_a3 = shell_pid(ws_a3, 'PID_A3')
    assert pid_a3 == pid_a1, (pid_a1, pid_a3)
    assert marker(ws_a3) == 'preserved'

    ws_a3.close()
    connections.remove(ws_a3)
    time.sleep(GRACE + 0.8)

    # Once the configured grace window (shortened in test) expires, the same
    # page id starts a genuinely fresh shell.
    ws_a4 = connect(http, ws_base, resume_a)
    connections.append(ws_a4)
    wait_session_state(ws_a4, 'fresh')
    pid_a4 = shell_pid(ws_a4, 'PID_A4')
    disable_echo(ws_a4)
    assert pid_a4 != pid_a1, (pid_a1, pid_a4)
    assert marker(ws_a4) != 'preserved'

    print(
        json.dumps(
            {
                'pidAInitial': pid_a1,
                'pidATakeover': pid_a2,
                'pidAResume': pid_a3,
                'pidAExpired': pid_a4,
                'pidIndependent': pid_b,
                'detachedOutputReplayed': True,
                'graceSeconds': GRACE,
                'PASS': True,
            },
            indent=2,
        )
    )
finally:
    for ws in connections:
        try:
            ws.close()
        except Exception:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
    if proc.returncode not in (0, -15):
        stderr = proc.stderr.read() if proc.stderr else ''
        if stderr:
            print(stderr[-4000:])
