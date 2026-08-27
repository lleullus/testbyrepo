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
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build-native' / 'ttyd'))
INDEX = ROOT / 'staging' / 'index.html'
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


def connect(http, ws_base):
    ws = websocket.create_connection(
        f'{ws_base}?resume={RESUME_ID}',
        subprotocols=['tty'],
        origin=http.rstrip('/'),
        timeout=1,
    )
    auth = json.dumps({'AuthToken': token(http), 'columns': 100, 'rows': 30}).encode()
    ws.send_binary(auth)
    return ws


def wait_session_state(ws, expected, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        if isinstance(message, bytes) and message[:1] == b'3':
            state = message[1:].decode('utf-8', errors='replace')
            assert state == expected, (state, expected)
            return state
    raise AssertionError(f'session state not received: {expected}')


def wait_output_regex(ws, pattern, timeout=30):
    regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    deadline = time.time() + timeout
    text = ''
    while time.time() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        if not isinstance(message, bytes) or message[:1] != b'0':
            continue
        text += message[1:].decode('utf-8', errors='replace')
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

prompt = (
    'Use the bash tool exactly once. In that bash command, first print one token formed by concatenating '
    'OMP_, TOOL_, and STARTED with no spaces. Then call the shell sleep utility for four seconds, then print '
    'one token formed by concatenating OMP_, DETACHED_, and DONE with no spaces. After the tool finishes, '
    'reply with the single word FINISHED.'
)

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
        '--auto-approve',
        '--max-time=40',
        prompt,
    ],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)

connections = []
try:
    wait_http(http + 'token')
    ws1 = connect(http, ws_base)
    connections.append(ws1)
    wait_session_state(ws1, 'fresh')
    omp_pid = wait_child_pid(proc.pid)
    assert_alive(omp_pid)

    # The start marker is emitted by the bash tool immediately before sleep,
    # so receiving it proves the tool is in flight without depending on OMP UI text.
    _, started_output = wait_output_regex(ws1, r'OMP_TOOL_STARTED', timeout=30)
    ws1.close()
    connections.remove(ws1)

    time.sleep(6.0)
    assert_alive(omp_pid)

    ws2 = connect(http, ws_base)
    connections.append(ws2)
    wait_session_state(ws2, 'resumed')
    _, replay = wait_output_regex(ws2, r'OMP_DETACHED_DONE', timeout=20)
    assert_alive(omp_pid)

    current_child = wait_child_pid(proc.pid)
    assert current_child == omp_pid, (omp_pid, current_child)

    print(
        json.dumps(
            {
                'ompPidBefore': omp_pid,
                'ompPidAfter': current_child,
                'toolStartedBeforeDrop': 'OMP_TOOL_STARTED' in started_output,
                'detachedMarkerReplayed': 'OMP_DETACHED_DONE' in replay,
                'sameOmpProcess': True,
                'disconnectSeconds': 6,
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
