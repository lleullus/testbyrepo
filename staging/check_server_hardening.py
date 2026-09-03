#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build-native' / 'ttyd'))
INDEX = ROOT / 'staging' / 'index.html'
CC = os.environ.get('CC', 'cc')


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


def check_sprintf_gate():
    pattern = re.compile(r'\bsprintf\s*\(')
    matches = []
    for path in sorted((ROOT / 'src').glob('*.c')):
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if pattern.search(line):
                matches.append(f'{path.relative_to(ROOT)}:{lineno}:{line.strip()}')
    assert not matches, 'remaining sprintf calls:\n' + '\n'.join(matches)
    return 0


def write_executable(path, text):
    path.write_text(text)
    path.chmod(0o755)


def check_open_uri_injection():
    with tempfile.TemporaryDirectory(prefix='ttyd-phase6-open-uri-') as tmp:
        tmp = Path(tmp)
        fake_bin = tmp / 'fake-bin'
        fake_bin.mkdir()
        capture = tmp / 'argv.txt'
        marker = tmp / 'SHOULD_NOT_EXIST'
        harness_c = tmp / 'open_uri_harness.c'
        harness_bin = tmp / 'open_uri_harness'

        write_executable(fake_bin / 'xset', '#!/bin/sh\nexit 0\n')
        write_executable(
            fake_bin / 'xdg-open',
            '#!/bin/sh\nprintf "%s\\n%s\\n" "$#" "$1" > "$CAPTURE"\nexit 0\n',
        )
        harness_c.write_text(
            '#include <stdio.h>\n'
            'int open_uri(char *uri);\n'
            'int main(int argc, char **argv) {\n'
            '  if (argc != 2) return 2;\n'
            '  return open_uri(argv[1]);\n'
            '}\n'
        )
        subprocess.run(
            [CC, '-std=gnu11', str(harness_c), str(ROOT / 'src' / 'utils.c'), '-o', str(harness_bin)],
            check=True,
            cwd=ROOT,
        )

        uri = f'http://example.invalid/;touch {marker}'
        env = os.environ.copy()
        env['PATH'] = str(fake_bin) + os.pathsep + env.get('PATH', '')
        env['CAPTURE'] = str(capture)
        result = subprocess.run([str(harness_bin), uri], env=env, cwd=ROOT, check=False)
        assert result.returncode == 0, result.returncode
        assert capture.exists(), 'fake xdg-open was not executed'
        argv = capture.read_text().splitlines()
        assert argv == ['1', uri], argv
        assert not marker.exists(), f'shell injection marker was created: {marker}'
        return {'argvCount': 1, 'argv1': uri, 'markerCreated': False}


def check_long_initial_messages():
    if not TTYD_BIN.exists():
        raise AssertionError(f'ttyd test binary not found: {TTYD_BIN}; set TTYD_BIN explicitly')

    port = free_port()
    http = f'http://127.0.0.1:{port}/'
    ws_url = f'ws://127.0.0.1:{port}/ws'
    long_command_arg = 'C' * 5000
    long_pref = 'P' * 5000
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
            '-t',
            f'phase6Long={long_pref}',
            '/bin/sh',
            '-c',
            'sleep 30',
            long_command_arg,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    ws = None
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

        messages = {}
        deadline = time.time() + 8
        while time.time() < deadline and len(messages) < 3:
            message = ws.recv()
            if isinstance(message, bytes) and message[:1] in (b'1', b'2', b'3'):
                messages.setdefault(message[:1], message)

        title = messages.get(b'1')
        prefs = messages.get(b'2')
        state = messages.get(b'3')
        assert title is not None and len(title) > 4096, None if title is None else len(title)
        assert prefs is not None and len(prefs) > 4096, None if prefs is None else len(prefs)
        assert long_command_arg.encode() in title, 'long command/title payload was truncated'
        assert long_pref.encode() in prefs, 'long preferences payload was truncated'
        assert state == b'3fresh', state
        assert proc.poll() is None, proc.poll()
        return {
            'titleBytes': len(title),
            'preferencesBytes': len(prefs),
            'sessionState': state[1:].decode(),
            'serverAlive': True,
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
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


results = {
    'ttydBin': str(TTYD_BIN),
    'remainingSprintf': check_sprintf_gate(),
    'openUri': check_open_uri_injection(),
    'longInitialMessages': check_long_initial_messages(),
}
print(json.dumps(results, indent=2, sort_keys=True))
