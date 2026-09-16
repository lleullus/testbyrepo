#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import threading
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build' / 'ttyd'))
INDEX = Path(os.environ.get('WEBTERM_TEST_INDEX', ROOT / 'html' / 'dist' / 'inline.html'))
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


def connect(http, ws_base, resume_id, intent):
    ws = websocket.create_connection(
        f'{ws_base}?resume={resume_id}',
        subprotocols=['tty'],
        origin=http.rstrip('/'),
        timeout=5,
    )
    handshake = json.dumps(
        {
            'version': 3,
            'intent': intent,
            'replayPosition': 0,
            'AuthToken': token(http),
            'columns': 80,
            'rows': 24,
        }
    ).encode()
    ws.send_binary(handshake)
    return ws

def pump_owner_control(ws, stop, observed):
    ws.settimeout(0.2)
    try:
        while not stop.is_set():
            try:
                frame = ws.recv_frame()
            except websocket.WebSocketTimeoutException:
                continue
            except websocket.WebSocketConnectionClosedException:
                return
            if frame.opcode == websocket.ABNF.OPCODE_PING:
                observed.append(frame.data.hex())
                ws.pong(frame.data)
            elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
                return
    finally:
        ws.settimeout(5)


def output_bytes(message):
    if not isinstance(message, bytes) or len(message) < 9 or message[:1] != b'0':
        return b''
    return message[9:]


def wait_session(ws, expected, timeout=8, observed_states=None):
    deadline = time.time() + timeout
    replay = bytearray()
    initial = None
    while time.time() < deadline:
        message = ws.recv()
        replay.extend(output_bytes(message))
        if not isinstance(message, bytes) or not message:
            continue
        if message[:1] == b'3':
            state = json.loads(message[1:])
            assert state['version'] == 3, state
            if observed_states is not None:
                observed_states.append(state['state'])
            if state['state'] == 'checking':
                initial = state
                continue
            assert state['state'] == expected, (state, expected)
            if state['state'] not in ('created', 'attached'):
                return state, bytes(replay)
            if state['inputReady']:
                return state, bytes(replay)
            initial = state
        elif message[:1] == b'4' and initial is not None:
            settled = json.loads(message[1:])
            ws.send_binary(b'5' + json.dumps({'position': settled['position']}).encode())
    raise AssertionError(f'session did not become ready: {expected}; initial={initial}')

def wait_state(ws, expected, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        message = ws.recv()
        if not isinstance(message, bytes) or message[:1] != b'3':
            continue
        state = json.loads(message[1:])
        assert state['version'] == 3 and state['state'] == expected, (state, expected)
        return state
    raise AssertionError(f'session state not received: {expected}')


def receive_challenge_ping(ws, timeout=3):
    ws.settimeout(0.2)
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            try:
                frame = ws.recv_frame()
            except websocket.WebSocketTimeoutException:
                continue
            if frame.opcode == websocket.ABNF.OPCODE_PING:
                if len(frame.data) == 16:
                    return frame
                ws.pong(frame.data)
    finally:
        ws.settimeout(5)
    raise AssertionError('native owner challenge Ping not received')


def wait_match(ws, pattern, timeout=5):
    text = ''
    deadline = time.time() + timeout
    regex = re.compile(pattern)
    while time.time() < deadline:
        try:
            message = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        text += output_bytes(message).decode('utf-8', errors='replace')
        match = regex.search(text)
        if match:
            return match, text
    raise AssertionError(f'pattern not received: {pattern!r}\n{text[-2000:]}')


def shell_pid(ws, label):
    ws.send_binary(b'0echo ' + label.encode() + b'=$$\r')
    match, _ = wait_match(ws, re.escape(label) + r'=(\d+)')
    return int(match.group(1))


def set_marker(ws, value):
    ws.send_binary(f'0export WEBTERM_RESUME_MARKER={value}\r'.encode())
    ws.send_binary(b'0echo MARKER_SET=$WEBTERM_RESUME_MARKER\r')
    match, _ = wait_match(ws, r'MARKER_SET=([A-Za-z0-9_-]+)')
    assert match.group(1) == value, match.group(1)


def marker(ws):
    ws.send_binary(b'0echo MARKER_NOW=$WEBTERM_RESUME_MARKER\r')
    match, _ = wait_match(ws, r'MARKER_NOW=([A-Za-z0-9_-]+)')
    return match.group(1)


port = free_port()
http = f'http://127.0.0.1:{port}/'
ws_base = f'ws://127.0.0.1:{port}/ws'
env = os.environ.copy()
env['TTYD_RECONNECT_GRACE'] = str(GRACE)
env['TTYD_DIAGNOSTICS'] = '1'
proc = subprocess.Popen(
    [str(TTYD_BIN), '-W', '-i', '127.0.0.1', '-p', str(port), '-I', str(INDEX), '/bin/bash', '--noprofile', '--norc'],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

server_logs = []


def drain_server_logs():
    for line in proc.stderr:
        server_logs.append(line.rstrip())


server_log_thread = threading.Thread(target=drain_server_logs, daemon=True)
server_log_thread.start()

resume_a = 'a' * 32
resume_b = 'b' * 32
resume_c = 'c' * 32
resume_d = 'd' * 32
resume_e = 'e' * 32
resume_f = 'f' * 32
resume_g = '1' * 32
resume_h = '2' * 32
resume_i = '3' * 32
resume_j = '4' * 32
resume_k = '5' * 32
resume_l = '6' * 32
resume_m = '7' * 32
resume_n = '8' * 32
connections = []
results = {}
try:
    wait_http(http + 'token')

    ws_a1 = connect(http, ws_base, resume_a, 'create')
    connections.append(ws_a1)
    state_a1, _ = wait_session(ws_a1, 'created')
    pid_a1 = shell_pid(ws_a1, 'PID_A1')
    set_marker(ws_a1, 'preserved')

    ws_b = connect(http, ws_base, resume_b, 'create')
    connections.append(ws_b)
    wait_session(ws_b, 'created')
    pid_b = shell_pid(ws_b, 'PID_B')
    assert pid_b != pid_a1, (pid_a1, pid_b)

    owner_stop = threading.Event()
    owner_pings = []
    owner_pump = threading.Thread(target=pump_owner_control, args=(ws_a1, owner_stop, owner_pings), daemon=True)
    owner_pump.start()
    conflict_states = []
    conflict_started = time.monotonic()
    ws_conflict = connect(http, ws_base, resume_a, 'resume')
    connections.append(ws_conflict)
    conflict, _ = wait_session(ws_conflict, 'conflict', observed_states=conflict_states)
    conflict_seconds = time.monotonic() - conflict_started
    owner_stop.set()
    owner_pump.join(timeout=2)
    assert owner_pings and len(bytes.fromhex(owner_pings[-1])) == 16, owner_pings
    assert conflict['ownerGeneration'] == state_a1['connectionGeneration'], conflict
    owner_pid = shell_pid(ws_a1, 'OWNER_STILL_ACTIVE')
    assert owner_pid == pid_a1

    ws_conflict.send_binary(
        b'6' +
        json.dumps(
            {
                'ownerGeneration': conflict['ownerGeneration'],
                'columns': 91,
                'rows': 27,
            }
        ).encode()
    )
    displaced_a1 = wait_state(ws_a1, 'displaced')
    takeover_a, _ = wait_session(ws_conflict, 'attached')
    assert takeover_a['sessionDiagnosticId'] == state_a1['sessionDiagnosticId']
    assert shell_pid(ws_conflict, 'PID_AFTER_TAKEOVER') == pid_a1
    ws_conflict.send_binary(
        b'6' + json.dumps({'ownerGeneration': conflict['ownerGeneration'], 'columns': 92, 'rows': 28}).encode()
    )
    assert shell_pid(ws_conflict, 'PID_AFTER_DUPLICATE_TAKEOVER') == pid_a1
    ws_a1.close()
    connections.remove(ws_a1)
    ws_conflict.close()
    connections.remove(ws_conflict)
    time.sleep(0.3)
    ws_a2 = connect(http, ws_base, resume_a, 'resume')
    connections.append(ws_a2)
    state_a2, replay_a2 = wait_session(ws_a2, 'attached')
    pid_a2 = shell_pid(ws_a2, 'PID_A2')
    assert pid_a2 == pid_a1, (pid_a1, pid_a2)
    assert marker(ws_a2) == 'preserved'
    assert b'MARKER_SET=preserved' in replay_a2

    ws_a2.send_binary(b'0(sleep 0.35; echo DETACHED_OUTPUT=$$) &\r')
    ws_a2.close()
    connections.remove(ws_a2)
    time.sleep(0.7)
    ws_a3 = connect(http, ws_base, resume_a, 'resume')
    connections.append(ws_a3)
    _, replay_a3 = wait_session(ws_a3, 'attached')
    assert f'DETACHED_OUTPUT={pid_a1}'.encode() in replay_a3, replay_a3[-1500:]
    assert shell_pid(ws_a3, 'PID_A3') == pid_a1

    ws_a3.close()
    connections.remove(ws_a3)
    time.sleep(GRACE + 0.8)
    ws_expired = connect(http, ws_base, resume_a, 'resume')
    connections.append(ws_expired)
    expired, _ = wait_session(ws_expired, 'expired')
    ws_expired.close()
    connections.remove(ws_expired)

    ws_d = connect(http, ws_base, resume_d, 'create')
    connections.append(ws_d)
    wait_session(ws_d, 'created')
    pid_d = shell_pid(ws_d, 'PID_D')
    assert pid_d != pid_a1

    ws_c = connect(http, ws_base, resume_c, 'create')
    connections.append(ws_c)
    wait_session(ws_c, 'created')
    pid_c = shell_pid(ws_c, 'PID_C')
    ws_c.send_binary(b'0exit 7\r')
    try:
        while ws_c.recv():
            pass
    except Exception:
        pass
    ws_c.close()
    connections.remove(ws_c)
    time.sleep(0.2)
    ws_exited = connect(http, ws_base, resume_c, 'resume')
    connections.append(ws_exited)
    exited, _ = wait_session(ws_exited, 'exited')

    ws_unknown = connect(http, ws_base, resume_e, 'resume')
    connections.append(ws_unknown)
    unknown, _ = wait_session(ws_unknown, 'unknown')
    ws_unknown.close()
    connections.remove(ws_unknown)

    ws_g = connect(http, ws_base, resume_g, 'create')
    connections.append(ws_g)
    wait_session(ws_g, 'created')
    pid_g = shell_pid(ws_g, 'PID_G')
    contender_g = connect(http, ws_base, resume_g, 'resume')
    connections.append(contender_g)
    wait_state(contender_g, 'checking')
    delayed_ping_g = receive_challenge_ping(ws_g)
    contender_g.close()
    connections.remove(contender_g)
    time.sleep(0.2)
    ws_g.pong(delayed_ping_g.data)
    assert shell_pid(ws_g, 'PID_G_AFTER_CANCEL') == pid_g

    ws_h = connect(http, ws_base, resume_h, 'create')
    connections.append(ws_h)
    wait_session(ws_h, 'created')
    pid_h = shell_pid(ws_h, 'PID_H')
    contender_h1 = connect(http, ws_base, resume_h, 'resume')
    connections.append(contender_h1)
    wait_state(contender_h1, 'checking')
    delayed_ping_h = receive_challenge_ping(ws_h)
    contender_h2 = connect(http, ws_base, resume_h, 'resume')
    connections.append(contender_h2)
    third_error, _ = wait_session(contender_h2, 'error')
    contender_h2.close()
    connections.remove(contender_h2)
    contender_h1.close()
    connections.remove(contender_h1)
    ws_h.pong(delayed_ping_h.data)
    assert shell_pid(ws_h, 'PID_H_AFTER_THIRD') == pid_h

    ws_i = connect(http, ws_base, resume_i, 'create')
    connections.append(ws_i)
    state_i, _ = wait_session(ws_i, 'created')
    pid_i = shell_pid(ws_i, 'PID_I')
    contender_i = connect(http, ws_base, resume_i, 'resume')
    connections.append(contender_i)
    wait_state(contender_i, 'checking')
    receive_challenge_ping(ws_i)
    old_close_started = time.monotonic()
    ws_i.close()
    connections.remove(ws_i)
    attached_i, _ = wait_session(contender_i, 'attached', timeout=5)
    old_close_seconds = time.monotonic() - old_close_started
    assert shell_pid(contender_i, 'PID_I_ATTACHED') == pid_i

    ws_j = connect(http, ws_base, resume_j, 'create')
    connections.append(ws_j)
    state_j, _ = wait_session(ws_j, 'created')
    ws_j.send_binary(b'0sleep 1; exit 7\r')
    contender_j = connect(http, ws_base, resume_j, 'resume')
    connections.append(contender_j)
    wait_state(contender_j, 'checking')
    exited_j, _ = wait_session(contender_j, 'exited', timeout=5)

    ws_k = connect(http, ws_base, resume_k, 'create')
    connections.append(ws_k)
    wait_session(ws_k, 'created')
    pid_k = shell_pid(ws_k, 'PID_K')
    contender_k = connect(http, ws_base, resume_k, 'resume')
    connections.append(contender_k)
    predeadline_started = time.monotonic()
    wait_state(contender_k, 'checking')
    predeadline_ping = receive_challenge_ping(ws_k)
    time.sleep(9.0)
    ws_k.pong(predeadline_ping.data)
    predeadline_conflict, _ = wait_session(contender_k, 'conflict', timeout=2)
    predeadline_seconds = time.monotonic() - predeadline_started
    assert shell_pid(ws_k, 'PID_K_AFTER_PONG') == pid_k

    ws_l = connect(http, ws_base, resume_l, 'create')
    connections.append(ws_l)
    state_l, _ = wait_session(ws_l, 'created')
    pid_l = shell_pid(ws_l, 'PID_L')
    contender_l = connect(http, ws_base, resume_l, 'resume')
    connections.append(contender_l)
    postdeadline_started = time.monotonic()
    wait_state(contender_l, 'checking')
    postdeadline_ping = receive_challenge_ping(ws_l)
    time.sleep(10.05)
    late_pong_write = True
    try:
        ws_l.pong(postdeadline_ping.data)
    except websocket.WebSocketException:
        late_pong_write = False
    attached_l, _ = wait_session(contender_l, 'attached', timeout=3)
    postdeadline_seconds = time.monotonic() - postdeadline_started
    assert shell_pid(contender_l, 'PID_L_ATTACHED') == pid_l

    ws_n = connect(http, ws_base, resume_n, 'create')
    connections.append(ws_n)
    state_n, _ = wait_session(ws_n, 'created')
    pid_n = shell_pid(ws_n, 'PID_N')

    contender_n1 = connect(http, ws_base, resume_n, 'resume')
    connections.append(contender_n1)
    wait_state(contender_n1, 'checking')
    ping_n1 = receive_challenge_ping(ws_n)
    ws_n.pong(ping_n1.data)
    offer_n1, _ = wait_session(contender_n1, 'conflict')

    contender_n2 = connect(http, ws_base, resume_n, 'resume')
    connections.append(contender_n2)
    wait_state(contender_n2, 'checking')
    ping_n2 = receive_challenge_ping(ws_n)
    ws_n.pong(ping_n2.data)
    offer_n2, _ = wait_session(contender_n2, 'conflict')
    assert offer_n1['ownerGeneration'] == offer_n2['ownerGeneration'] == state_n['connectionGeneration']

    contender_n1.send_binary(
        b'6' +
        json.dumps({'ownerGeneration': offer_n1['ownerGeneration'], 'columns': 81, 'rows': 25}).encode()
    )
    wait_state(ws_n, 'displaced')
    attached_n1, _ = wait_session(contender_n1, 'attached')
    assert shell_pid(contender_n1, 'PID_N_AFTER_FIRST_CAS') == pid_n

    contender_n2.send_binary(
        b'6' +
        json.dumps({'ownerGeneration': offer_n2['ownerGeneration'], 'columns': 82, 'rows': 26}).encode()
    )
    refreshed_n2, _ = wait_session(contender_n2, 'conflict')
    assert refreshed_n2['ownerGeneration'] == attached_n1['connectionGeneration']
    assert shell_pid(contender_n1, 'PID_N_AFTER_STALE_CAS') == pid_n

    contender_n2.send_binary(
        b'6' +
        json.dumps({'ownerGeneration': refreshed_n2['ownerGeneration'], 'columns': 83, 'rows': 27}).encode()
    )
    wait_state(contender_n1, 'displaced')
    attached_n2, _ = wait_session(contender_n2, 'attached')
    assert attached_n2['sessionDiagnosticId'] == state_n['sessionDiagnosticId']
    assert shell_pid(contender_n2, 'PID_N_AFTER_SECOND_CAS') == pid_n
    ws_n.close()
    connections.remove(ws_n)
    contender_n1.close()
    connections.remove(contender_n1)

    ws_legacy = websocket.create_connection(
        f'{ws_base}?resume={resume_f}',
        subprotocols=['tty'],
        origin=http.rstrip('/'),
        timeout=5,
    )
    connections.append(ws_legacy)
    ws_legacy.send_binary(
        json.dumps(
            {
                'version': 1,
                'intent': 'create',
                'replayPosition': 0,
                'AuthToken': token(http),
                'columns': 80,
                'rows': 24,
            }
        ).encode()
    )
    legacy, _ = wait_session(ws_legacy, 'error')

    ws_m = connect(http, ws_base, resume_m, 'create')
    connections.append(ws_m)
    wait_session(ws_m, 'created')
    pid_m = shell_pid(ws_m, 'PID_M')
    contender_m = connect(http, ws_base, resume_m, 'resume')
    connections.append(contender_m)
    wait_state(contender_m, 'checking')
    receive_challenge_ping(ws_m)
    shutdown_started = time.monotonic()
    proc.terminate()
    proc.wait(timeout=5)
    shutdown_seconds = time.monotonic() - shutdown_started
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(pid_m, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f'pending-check child survived server shutdown: {pid_m}')
    server_log_thread.join(timeout=2)

    ws_legacy.close()
    connections.remove(ws_legacy)

    results = {
        'sessionDiagnosticInitial': state_a1['sessionDiagnosticId'],
        'sessionDiagnosticAttached': state_a2['sessionDiagnosticId'],
        'sameDiagnosticSession': state_a1['sessionDiagnosticId'] == state_a2['sessionDiagnosticId'],
        'pidInitial': pid_a1,
        'pidAttached': pid_a2,
        'pidIndependent': pid_b,
        'pidExplicitNewAfterExpiry': pid_d,
        'pidExited': pid_c,
        'conflictState': conflict['state'],
        'conflictTransitions': conflict_states,
        'ownerChallengePingCount': len(owner_pings),
        'ownerChallengeSeconds': round(conflict_seconds, 3),
        'expiredState': expired['state'],
        'exitedState': exited['state'],
        'unknownState': unknown['state'],
        'legacyProtocolState': legacy['state'],
        'activeOwnerPreserved': True,
        'boundedReplayRestoredMarker': True,
        'graceSeconds': GRACE,
        'contenderCancellationOwnerPreserved': True,
        'thirdContenderState': third_error['state'],
        'oldCloseAttachSeconds': round(old_close_seconds, 3),
        'oldCloseSameSession': state_i['sessionDiagnosticId'] == attached_i['sessionDiagnosticId'],
        'rootExitPendingState': exited_j['state'],
        'predeadlineState': predeadline_conflict['state'],
        'predeadlineSeconds': round(predeadline_seconds, 3),
        'postdeadlineState': attached_l['state'],
        'takeoverState': takeover_a['state'],
        'displacedState': displaced_a1['state'],
        'takeoverSameSession': takeover_a['sessionDiagnosticId'] == state_a1['sessionDiagnosticId'],
        'duplicateTakeoverNoReattach': True,
        'staleTakeoverRefreshedOwnerGeneration': refreshed_n2['ownerGeneration'],
        'simultaneousTakeoverSingleOwner': attached_n2['connectionGeneration'],
        'postdeadlineSeconds': round(postdeadline_seconds, 3),
        'latePongSocketWriteAccepted': late_pong_write,
        'latePongDidNotReverseOwnership': True,
        'pendingShutdownSeconds': round(shutdown_seconds, 3),
        'pendingShutdownChildReaped': True,
        'ownerCheckDiagnostics': [line for line in server_logs if 'diag event=owner-check-' in line],
        'PASS': True,
    }
    print(json.dumps(results, indent=2))
finally:
    for connection in connections:
        try:
            connection.close()
        except Exception:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    server_log_thread.join(timeout=2)
    if not results.get('PASS'):
        print('\n'.join(server_logs[-80:]))
