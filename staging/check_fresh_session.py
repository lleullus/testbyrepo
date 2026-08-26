#!/usr/bin/env python3
import json
import re
import time
import urllib.request

import websocket

HTTP = 'http://127.0.0.1:7684/'
WS = 'ws://127.0.0.1:7684/ws'


def token():
    with urllib.request.urlopen(HTTP + 'token', timeout=5) as response:
        return json.load(response).get('token', '')


def connect():
    ws = websocket.create_connection(
        WS,
        subprotocols=['tty'],
        origin='http://127.0.0.1:7684',
        timeout=5,
    )
    auth = json.dumps({'AuthToken': token(), 'columns': 80, 'rows': 24}).encode()
    ws.send_binary(auth)
    return ws


def shell_pid(ws, label):
    ws.send_binary(b'0echo ' + label.encode() + b'=$$\r')
    text = ''
    deadline = time.time() + 5
    while time.time() < deadline:
        message = ws.recv()
        if not isinstance(message, bytes) or not message:
            continue
        if message[:1] != b'0':
            continue
        text += message[1:].decode('utf-8', errors='replace')
        match = re.search(re.escape(label) + r'=(\d+)', text)
        if match:
            return int(match.group(1))
    raise AssertionError(f'PID marker not received for {label}: {text[-1000:]}')


ws1 = connect()
ws2 = None
ws3 = None
try:
    pid1 = shell_pid(ws1, 'PID_A')
    ws2 = connect()
    pid2 = shell_pid(ws2, 'PID_B')
    assert pid1 != pid2, (pid1, pid2)

    ws1.close()
    ws1 = None
    time.sleep(0.2)

    ws3 = connect()
    pid3 = shell_pid(ws3, 'PID_RELOAD')
    assert pid1 != pid3, (pid1, pid3)
    assert pid2 != pid3, (pid2, pid3)

    print(json.dumps({'pidA': pid1, 'pidB': pid2, 'pidReload': pid3, 'PASS': True}, indent=2))
finally:
    for ws in (ws1, ws2, ws3):
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
