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
INDEX = ROOT / 'staging' / 'index.html'


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


def process_exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def observe(option):
    port = free_port()
    http = f'http://127.0.0.1:{port}/'
    ws_url = f'ws://127.0.0.1:{port}/ws?resume={'a' * 32}'
    proc = subprocess.Popen(
        [
            str(TTYD_BIN),
            option,
            '-W',
            '-i',
            '127.0.0.1',
            '-p',
            str(port),
            '-I',
            str(INDEX),
            '/bin/sh',
            '-c',
            'echo LIFECYCLE_PID=$$; sleep 30',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    ws = None
    child_pid = None
    try:
        wait_http(http + 'token')
        ws = websocket.create_connection(
            ws_url,
            subprotocols=['tty'],
            origin=http.rstrip('/'),
            timeout=5,
        )
        with urllib.request.urlopen(http + 'token', timeout=5) as response:
            auth_token = json.load(response).get('token', '')
        ws.send_binary(json.dumps({'AuthToken': auth_token, 'columns': 80, 'rows': 24}).encode())

        text = ''
        deadline = time.time() + 8
        while time.time() < deadline and child_pid is None:
            message = ws.recv()
            if not isinstance(message, bytes) or message[:1] != b'0':
                continue
            text += message[1:].decode('utf-8', errors='replace')
            match = re.search(r'LIFECYCLE_PID=(\d+)', text)
            if match:
                child_pid = int(match.group(1))
        assert child_pid is not None, text[-1000:]

        before_close = time.monotonic()
        ws.close()
        ws = None
        server_exited = False
        return_code = None
        try:
            return_code = proc.wait(timeout=3)
            server_exited = True
        except subprocess.TimeoutExpired:
            pass
        elapsed = time.monotonic() - before_close
        child_alive = process_exists(child_pid)

        return {
            'option': option,
            'serverExitedWithin3s': server_exited,
            'serverReturnCode': return_code,
            'disconnectToObservationSeconds': round(elapsed, 3),
            'childPid': child_pid,
            'childAliveAfterObservation': child_alive,
            'resumePossibleAfterObservation': not server_exited,
        }
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        if child_pid is not None and process_exists(child_pid):
            try:
                os.kill(child_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


if not TTYD_BIN.exists():
    raise SystemExit(f'ttyd test binary not found: {TTYD_BIN}; set TTYD_BIN explicitly')

results = {
    'ttydBin': str(TTYD_BIN),
    'once': observe('--once'),
    'exitNoConn': observe('--exit-no-conn'),
    'policyDefined': False,
    'decision': 'DEFERRED due to custom native session resume semantics',
}
print(json.dumps(results, indent=2, sort_keys=True))
