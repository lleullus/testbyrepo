#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request

import websocket

ROOT = Path(__file__).resolve().parents[1]
TTYD_BIN = Path(os.environ.get('TTYD_BIN', ROOT / 'build-native' / 'ttyd'))
INDEX = ROOT / 'staging' / 'index.html'
RETRY_WINDOW_TEST = os.environ.get('WEBTERM_TEST_RETRY_WINDOW') == '1'
RETRY_OPEN_CLOSE_TEST = os.environ.get('WEBTERM_TEST_RETRY_OPEN_CLOSE') == '1'


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
        self.blocked = False
        self.drop_after_upgrade = False
        self.upgrade_drops = 0
        self.stopped = False
        self.lock = threading.Lock()
        self.connections = set()
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
            except OSError:
                client.close()
                continue
            with self.lock:
                self.connections.add(client)
                self.connections.add(upstream)
            threading.Thread(target=self._pump, args=(client, upstream, False), daemon=True).start()
            threading.Thread(target=self._pump, args=(upstream, client, True), daemon=True).start()

    def _pump(self, source, target, upstream_to_client):
        headers = b''
        try:
            while True:
                data = source.recv(65536)
                if not data:
                    break
                target.sendall(data)
                if upstream_to_client and self.drop_after_upgrade:
                    headers = (headers + data)[-8192:]
                    if b'101 ' in headers and b'\r\n\r\n' in headers:
                        with self.lock:
                            self.upgrade_drops += 1
                        break
        except OSError:
            pass
        finally:
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
env['TTYD_RECONNECT_GRACE'] = '90' if (RETRY_WINDOW_TEST or RETRY_OPEN_CLOSE_TEST) else '10'
deps_lib = ROOT / '.build-deps' / 'root' / 'usr' / 'lib' / 'x86_64-linux-gnu'
env['LD_LIBRARY_PATH'] = str(deps_lib) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
ttyd = subprocess.Popen(
    [str(TTYD_BIN), '-W', '-i', '127.0.0.1', '-p', str(ttyd_port), '-I', str(INDEX), '/bin/bash', '-l'],
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


def extract_pid(text, label):
    matches = re.findall(re.escape(label) + r'=(\d+)', text)
    if not matches:
        raise AssertionError(f'missing pid marker {label}: {text[-1500:]}')
    return int(matches[-1])


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
    call('Page.navigate', {'url': http})
    wait_until("document.readyState === 'complete' && Boolean(window.term)")
    time.sleep(0.5)

    pid_command = "export WEBTERM_TEST_SHELL_PID=$BASHPID; echo BROWSER_PID_BEFORE=$WEBTERM_TEST_SHELL_PID"
    send_command(pid_command)
    before_text = wait_text('BROWSER_PID_BEFORE=')
    pid_before = extract_pid(before_text, 'BROWSER_PID_BEFORE')

    if RETRY_OPEN_CLOSE_TEST:
        disconnected_at = time.monotonic()
        proxy.drop_each_upgrade()
        wait_until("document.body.innerText.includes('Reconnecting')", timeout=15)
        wait_until(
            "document.body.innerText.includes('Press') && document.body.innerText.includes('Reconnect')",
            timeout=70,
        )
        stopped_after = time.monotonic() - disconnected_at
        assert 58 <= stopped_after <= 66, stopped_after
        assert proxy.upgrade_drops >= 3, proxy.upgrade_drops
        time.sleep(6)
        assert evaluate("document.body.innerText.includes('Press') && document.body.innerText.includes('Reconnect')")
        os.kill(pid_before, 0)
        print(
            json.dumps(
                {
                    'pidStillAlive': pid_before,
                    'websocketUpgradeDrops': proxy.upgrade_drops,
                    'automaticRetryStoppedAfterSeconds': round(stopped_after, 2),
                    'manualReconnectPromptStable': True,
                    'PASS': True,
                },
                indent=2,
            )
        )
        raise SystemExit(0)

    if RETRY_WINDOW_TEST:
        disconnected_at = time.monotonic()
        proxy.disconnect()
        wait_until("document.body.innerText.includes('Reconnecting')", timeout=15)
        wait_until(
            "document.body.innerText.includes('Press') && document.body.innerText.includes('Reconnect')",
            timeout=70,
        )
        stopped_after = time.monotonic() - disconnected_at
        assert 58 <= stopped_after <= 66, stopped_after
        time.sleep(6)
        assert evaluate("document.body.innerText.includes('Press') && document.body.innerText.includes('Reconnect')")
        os.kill(pid_before, 0)
        print(
            json.dumps(
                {
                    'pidStillAlive': pid_before,
                    'automaticRetryStoppedAfterSeconds': round(stopped_after, 2),
                    'manualReconnectPromptStable': True,
                    'PASS': True,
                },
                indent=2,
            )
        )
        raise SystemExit(0)

    send_command("for i in $(seq 1 220); do echo SCROLL_$i; done; echo SCROLL_READY")
    wait_text('SCROLL_READY')
    evaluate('window.term.scrollToTop(); true')
    scroll_before = evaluate(
        "({baseY: window.term.buffer.active.baseY, viewportY: window.term.buffer.active.viewportY})"
    )
    assert scroll_before['baseY'] > 0, scroll_before
    assert scroll_before['viewportY'] < scroll_before['baseY'], scroll_before

    detached_command = "(sleep 2; echo BROWSER_DETACHED_OUTPUT=$WEBTERM_TEST_SHELL_PID) &"
    send_command(detached_command)
    time.sleep(0.2)

    proxy.disconnect()
    wait_until(
        "document.body.innerText.includes('Reconnecting') || document.body.innerText.includes('Connection Closed')",
        timeout=15,
    )
    time.sleep(2.5)
    os.kill(pid_before, 0)

    proxy.reconnect()
    deadline = time.time() + 15
    detached_pid = None
    while time.time() < deadline and detached_pid is None:
        text = buffer_text()
        matches = re.findall(r'BROWSER_DETACHED_OUTPUT=(\d+)', text)
        if matches:
            detached_pid = int(matches[-1])
        else:
            time.sleep(0.1)
    assert detached_pid == pid_before, (pid_before, detached_pid)

    after_command = "echo BROWSER_PID_AFTER=$BASHPID"
    deadline = time.time() + 15
    pid_after = None
    while time.time() < deadline and pid_after is None:
        send_command(after_command)
        time.sleep(0.5)
        text = buffer_text()
        matches = re.findall(r'BROWSER_PID_AFTER=(\d+)', text)
        if matches:
            pid_after = int(matches[-1])
    assert pid_after == pid_before, (pid_before, pid_after)

    scroll_after = evaluate(
        "({baseY: window.term.buffer.active.baseY, viewportY: window.term.buffer.active.viewportY})"
    )
    assert scroll_after['baseY'] >= scroll_before['baseY'], (scroll_before, scroll_after)
    assert scroll_after['viewportY'] == scroll_after['baseY'], scroll_after

    print(
        json.dumps(
            {
                'pidBefore': pid_before,
                'pidAfter': pid_after,
                'detachedPid': detached_pid,
                'scrollBefore': scroll_before,
                'scrollAfter': scroll_after,
                'detachedOutputReplayed': True,
                'sameProcess': True,
                'atBottom': True,
                'PASS': True,
            },
            indent=2,
        )
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
