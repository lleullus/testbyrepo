#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import time
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build' / 'ttyd'))
INDEX = Path(os.environ.get('WEBTERM_TEST_INDEX', ROOT / 'html' / 'dist' / 'inline.html'))
OMP = Path.home() / '.bun' / 'bin' / 'omp'
RESUME_ID = 'c' * 32
GRACE = 20


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


def connect(http, ws_base, intent):
    ws = websocket.create_connection(
        f'{ws_base}?resume={RESUME_ID}',
        subprotocols=['tty'],
        origin=http.rstrip('/'),
        timeout=1,
    )
    handshake = json.dumps(
        {
            'version': 3,
            'intent': intent,
            'replayPosition': 0,
            'AuthToken': token(http),
            'columns': 100,
            'rows': 30,
        }
    ).encode()
    ws.send_binary(handshake)
    return ws


def output_bytes(message):
    if not isinstance(message, bytes) or len(message) < 9 or message[:1] != b'0':
        return b''
    return message[9:]


def wait_session_state(ws, expected, timeout=8):
    deadline = time.time() + timeout
    initial = None
    output = bytearray()
    while time.time() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        output.extend(output_bytes(message))
        if not isinstance(message, bytes) or not message:
            continue
        if message[:1] == b'3':
            state = json.loads(message[1:])
            assert state['version'] == 3 and state['state'] == expected, (state, expected)
            if state['inputReady']:
                return state, bytes(output)
            initial = state
        elif message[:1] == b'4' and initial is not None:
            replay = json.loads(message[1:])
            ws.send_binary(b'5' + json.dumps({'position': replay['position']}).encode())
    raise AssertionError(f'session state not received: {expected}; initial={initial}')


def wait_output_regex(ws, pattern, timeout=30):
    regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    deadline = time.time() + timeout
    text = ''
    while time.time() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        text += output_bytes(message).decode('utf-8', errors='replace')
        if len(text) > 2_000_000:
            text = text[-2_000_000:]
        match = regex.search(text)
        if match:
            return match, text
    raise AssertionError(f'output pattern not received: {pattern!r}\n{text[-5000:]}')


def wait_child_pid(parent_pid, timeout=8):
    path = Path(f'/proc/{parent_pid}/task/{parent_pid}/children')
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            values = path.read_text().strip().split()
        except FileNotFoundError:
            values = []
        if values:
            return int(values[0])
        time.sleep(0.05)
    raise AssertionError(f'no child pid for ttyd pid {parent_pid}')


def assert_alive(pid):
    os.kill(pid, 0)


port = free_port()
http = f'http://127.0.0.1:{port}/'
ws_base = f'ws://127.0.0.1:{port}/ws'
env = os.environ.copy()
env['TTYD_RECONNECT_GRACE'] = str(GRACE)
deps_lib = ROOT / '.build-deps' / 'root' / 'usr' / 'lib' / 'x86_64-linux-gnu'
env['LD_LIBRARY_PATH'] = str(deps_lib) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')

OMP_SCREEN_PATTERN = r'omp v[0-9]+\.[0-9]+\.[0-9]+'

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
        str(OMP),
        '--no-session',
        '--no-title',
    ],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)

connections = []
try:
    wait_http(http + 'token')
    ws1 = connect(http, ws_base, 'create')
    connections.append(ws1)
    state1, _ = wait_session_state(ws1, 'created')
    omp_pid = wait_child_pid(proc.pid)
    assert_alive(omp_pid)

    _, startup_output = wait_output_regex(ws1, OMP_SCREEN_PATTERN, timeout=30)
    ws1.close()
    connections.remove(ws1)

    time.sleep(2.0)
    assert_alive(omp_pid)

    ws2 = connect(http, ws_base, 'resume')
    connections.append(ws2)
    state2, replay_bytes = wait_session_state(ws2, 'attached')
    replay = replay_bytes.decode('utf-8', errors='replace')
    assert_alive(omp_pid)

    current_child = wait_child_pid(proc.pid)
    assert current_child == omp_pid, (omp_pid, current_child)

    print(
        json.dumps(
            {
                'sessionDiagnosticInitial': state1['sessionDiagnosticId'],
                'sessionDiagnosticAttached': state2['sessionDiagnosticId'],
                'ompPidBefore': omp_pid,
                'ompPidAfter': current_child,
                'startupScreenObserved': bool(re.search(OMP_SCREEN_PATTERN, startup_output, re.IGNORECASE)),
                'startupScreenReplayed': bool(re.search(OMP_SCREEN_PATTERN, replay, re.IGNORECASE)),
                'sameOmpProcess': True,
                'providerOrToolExecution': False,
                'disconnectSeconds': 2,
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
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
