#!/usr/bin/env python3
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request

import websocket

URL = os.environ.get('WEBTERM_URL', 'http://127.0.0.1:7684/')
RESIZE_ITERATIONS = int(os.environ.get('WEBTERM_RESIZE_ITERATIONS', '20'))


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def http_json(url, method='GET'):
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


debug_port = free_port()
profile = tempfile.TemporaryDirectory(prefix='webterm-touch-resize-')
chrome = subprocess.Popen(
    [
        'google-chrome',
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--remote-allow-origins=*',
        f'--remote-debugging-port={debug_port}',
        f'--user-data-dir={profile.name}',
        'about:blank',
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True,
)

ws = None
next_id = 0


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
    result = call(
        'Runtime.evaluate',
        {'expression': expression, 'returnByValue': True, 'awaitPromise': True},
    )
    remote = result.get('result', {})
    return remote.get('value')


def wait_until(expression, timeout=10):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = evaluate(expression)
        if last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'wait timeout: {expression}; last={last!r}')


def set_device(width, height):
    call(
        'Emulation.setDeviceMetricsOverride',
        {'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': True},
    )
    time.sleep(0.08)


def term_input(text):
    evaluate(f'window.term.input({json.dumps(text)}, true); true')


def buffer_text():
    return evaluate(
        """(() => {
            const b = window.term.buffer.active;
            const out = [];
            for (let i = Math.max(0, b.length - 120); i < b.length; i++) {
                const line = b.getLine(i);
                if (line) out.push(line.translateToString(true));
            }
            return out.join('\\n');
        })()"""
    )


def wait_text(marker, timeout=10):
    deadline = time.time() + timeout
    last = ''
    while time.time() < deadline:
        last = buffer_text()
        if marker in last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'missing terminal marker {marker!r}; tail={last[-1600:]}')


def buffer_state():
    return evaluate(
        """(() => {
            const b = window.term.buffer.active;
            return {
                baseY: b.baseY,
                viewportY: b.viewportY,
                length: b.length,
                rows: window.term.rows,
                cols: window.term.cols,
            };
        })()"""
    )


def tap_terminal():
    point = evaluate(
        """(() => {
            const r = document.querySelector('#terminal-container .xterm-screen').getBoundingClientRect();
            return {x: r.left + r.width / 2, y: r.top + r.height / 2};
        })()"""
    )
    params = {'x': point['x'], 'y': point['y'], 'button': 'left', 'clickCount': 1}
    call('Input.dispatchMouseEvent', {'type': 'mousePressed', **params})
    call('Input.dispatchMouseEvent', {'type': 'mouseReleased', **params})
    time.sleep(0.15)


def touch_drag(start_fraction, end_fraction):
    rect = evaluate(
        """(() => {
            const r = document.querySelector('#terminal-container .xterm-screen').getBoundingClientRect();
            return {left:r.left, top:r.top, width:r.width, height:r.height};
        })()"""
    )
    x = rect['left'] + rect['width'] * 0.5
    start_y = rect['top'] + rect['height'] * start_fraction
    end_y = rect['top'] + rect['height'] * end_fraction
    call(
        'Input.dispatchTouchEvent',
        {
            'type': 'touchStart',
            'touchPoints': [
                {'x': x, 'y': start_y, 'radiusX': 2, 'radiusY': 2, 'force': 1, 'id': 1}
            ],
        },
    )
    for step in range(1, 11):
        y = start_y + (end_y - start_y) * step / 10
        call(
            'Input.dispatchTouchEvent',
            {
                'type': 'touchMove',
                'touchPoints': [
                    {'x': x, 'y': y, 'radiusX': 2, 'radiusY': 2, 'force': 1, 'id': 1}
                ],
            },
        )
        time.sleep(0.04)
    call('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    time.sleep(0.5)


results = {'url': URL, 'resizeIterations': RESIZE_ITERATIONS}
try:
    deadline = time.time() + 10
    while True:
        try:
            http_json(f'http://127.0.0.1:{debug_port}/json/version')
            break
        except Exception:
            if time.time() >= deadline:
                raise
            time.sleep(0.1)

    target = http_json(f'http://127.0.0.1:{debug_port}/json/new?about:blank', method='PUT')
    ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=10)
    call('Page.enable')
    call('Runtime.enable')
    set_device(390, 844)
    call('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
    call('Page.navigate', {'url': URL})
    wait_until("document.readyState === 'complete' && Boolean(window.term)")
    wait_until("Boolean(document.querySelector('#terminal-container .xterm-screen'))")

    evaluate(
        """(() => {
            window.__upgradeRegressionErrors = [];
            window.addEventListener('error', event => {
                window.__upgradeRegressionErrors.push('error:' + (event.message || String(event.error)));
            });
            window.addEventListener('unhandledrejection', event => {
                window.__upgradeRegressionErrors.push('rejection:' + String(event.reason));
            });
            return true;
        })()"""
    )

    # The terminal object can exist before a remote WebSocket has completed its
    # first shell attach, especially through Funnel. Focus the xterm explicitly
    # before injecting test input, then prove end-to-end input/output readiness
    # before creating the scrollback used by the gesture assertion.
    tap_terminal()
    term_input('echo TOUCH_RESIZE_READY\r')
    wait_text('TOUCH_RESIZE_READY', timeout=15)

    # Create enough scrollback to make touch movement observable.
    term_input('seq 1 500\r')
    wait_until('window.term.buffer.active.baseY > 200', timeout=15)
    evaluate('window.term.scrollToBottom(); true')
    time.sleep(0.2)
    touch_before = buffer_state()

    # A finger moving down should move the viewport upward into scrollback.
    touch_drag(0.30, 0.72)
    touch_after_down = buffer_state()
    assert touch_after_down['viewportY'] < touch_before['viewportY'], (
        touch_before,
        touch_after_down,
    )

    # Reverse the gesture and verify the viewport moves back toward the bottom.
    touch_drag(0.72, 0.30)
    touch_after_up = buffer_state()
    assert touch_after_up['viewportY'] > touch_after_down['viewportY'], (
        touch_after_down,
        touch_after_up,
    )
    results['touchScroll'] = {
        'before': touch_before,
        'afterDragDown': touch_after_down,
        'afterDragUp': touch_after_up,
    }

    # Stream output while repeatedly changing the mobile viewport. This targets
    # xterm buffer/fit races that are not exercised by a single orientation change.
    evaluate('window.term.scrollToBottom(); true')
    producer = (
        "python3 -c \"import time;"
        "[(print('RESIZE_%04d'%i,flush=True),time.sleep(.003)) for i in range(1200)];"
        "print('RESIZE_DONE',flush=True)\"\r"
    )
    term_input(producer)
    for index in range(RESIZE_ITERATIONS):
        if index % 2 == 0:
            set_device(844, 390)
        else:
            set_device(390, 844)

    wait_until(
        """(() => {
            const b = window.term.buffer.active;
            for (let i = Math.max(0, b.length - 1600); i < b.length; i++) {
                const line = b.getLine(i);
                if (line && line.translateToString(true).includes('RESIZE_DONE')) return true;
            }
            return false;
        })()""",
        timeout=20,
    )
    final_state = buffer_state()
    errors = evaluate('window.__upgradeRegressionErrors.slice()')
    results['resizeStress'] = {'final': final_state, 'pageErrors': errors}
    assert final_state['rows'] > 0 and final_state['cols'] > 0, final_state
    assert errors == [], errors

    results['PASS'] = True
    print(json.dumps(results, indent=2))
finally:
    if ws is not None:
        try:
            ws.close()
        except Exception:
            pass
    try:
        os.killpg(chrome.pid, signal.SIGTERM)
    except Exception:
        pass
    try:
        chrome.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(chrome.pid, signal.SIGKILL)
        except Exception:
            pass
        chrome.wait()
    profile.cleanup()
