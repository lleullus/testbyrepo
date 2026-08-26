#!/usr/bin/env python3
import json
import os
import re
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request

import websocket

URL = os.environ.get('WEBTERM_URL', 'http://127.0.0.1:7684/')


def free_port():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def http_json(url, method='GET'):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


port = free_port()
profile = tempfile.TemporaryDirectory(prefix='webterm-chrome-')
proc = subprocess.Popen(
    [
        'google-chrome',
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--disable-dev-shm-usage',
        '--remote-allow-origins=*',
        f'--remote-debugging-port={port}',
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


def evaluate(expression, user_gesture=False):
    result = call(
        'Runtime.evaluate',
        {
            'expression': expression,
            'returnByValue': True,
            'awaitPromise': True,
            'userGesture': user_gesture,
        },
    )
    remote = result.get('result', {})
    if 'value' in remote:
        return remote['value']
    return None


def wait_until(expression, timeout=8):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = evaluate(expression)
        if last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'wait timeout: {expression}; last={last!r}')


def center(selector):
    return evaluate(
        f"""(() => {{
            const e = document.querySelector({json.dumps(selector)});
            if (!e) return null;
            const r = e.getBoundingClientRect();
            return {{x: r.left + r.width / 2, y: r.top + r.height / 2}};
        }})()"""
    )


def tap(selector):
    point = center(selector)
    if point is None:
        raise AssertionError(f'missing selector: {selector}')
    params = {
        'x': point['x'],
        'y': point['y'],
        'button': 'left',
        'clickCount': 1,
    }
    call('Input.dispatchMouseEvent', {'type': 'mousePressed', **params})
    call('Input.dispatchMouseEvent', {'type': 'mouseReleased', **params})
    time.sleep(0.15)


def insert_text(text):
    call('Input.insertText', {'text': text})
    time.sleep(0.05)


def press_enter():
    key = {
        'key': 'Enter',
        'code': 'Enter',
        'windowsVirtualKeyCode': 13,
        'nativeVirtualKeyCode': 13,
    }
    call('Input.dispatchKeyEvent', {'type': 'keyDown', **key})
    call('Input.dispatchKeyEvent', {'type': 'keyUp', **key})
    time.sleep(0.1)


def terminal_tap():
    tap('#terminal-container .xterm-screen')


def term_input(text):
    evaluate(f"window.term.input({json.dumps(text)}, true)")
    time.sleep(0.05)


def send_command(command):
    terminal_tap()
    term_input(command)
    term_input('\r')


def buffer_text():
    return evaluate(
        """(() => {
            const term = window.term;
            if (!term) return '';
            const b = term.buffer.active;
            const out = [];
            for (let i = Math.max(0, b.length - 80); i < b.length; i++) {
                const line = b.getLine(i);
                if (line) out.push(line.translateToString(true));
            }
            return out.join('\\n');
        })()"""
    )


def wait_text(marker, timeout=5):
    deadline = time.time() + timeout
    last = ''
    while time.time() < deadline:
        last = buffer_text()
        if marker in last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'missing terminal marker {marker!r}; tail={last[-1200:]}')


def ui_state():
    return evaluate(
        """(() => {
            const toolbar = document.querySelector('.mobile-toolbar');
            const buttons = [...document.querySelectorAll('.mobile-toolbar button')];
            const textarea = document.querySelector('.xterm-helper-textarea');
            if (!toolbar || !textarea || !window.term) return null;
            const tr = toolbar.getBoundingClientRect();
            const tops = buttons.map(b => Math.round(b.getBoundingClientRect().top));
            return {
                labels: buttons.map(b => (b.textContent || '').trim()),
                oneRow: tops.every(t => t === tops[0]),
                toolbarTop: Math.round(tr.top),
                toolbarBottom: Math.round(tr.bottom),
                toolbarHeight: Math.round(tr.height),
                viewportHeight: window.innerHeight,
                toolbarOverflow: toolbar.scrollWidth > toolbar.clientWidth,
                activeIsTextarea: document.activeElement === textarea,
                activeTag: document.activeElement ? document.activeElement.tagName : null,
                coarse: matchMedia('(pointer: coarse)').matches,
                maxTouchPoints: navigator.maxTouchPoints,
                fontSize: Number(document.querySelector('.font-size-status')?.textContent),
                ctrlPressed: document.querySelector('.ctrl-button')?.getAttribute('aria-pressed') === 'true',
                fullscreen: Boolean(document.fullscreenElement),
                rows: window.term.rows,
                cols: window.term.cols,
                fullscreenButton: Boolean(document.querySelector('button[aria-label*="fullscreen" i]')),
            };
        })()"""
    )


results = {}
try:
    deadline = time.time() + 8
    while True:
        try:
            http_json(f'http://127.0.0.1:{port}/json/version')
            break
        except Exception:
            if time.time() > deadline:
                raise
            time.sleep(0.1)

    target = http_json(f'http://127.0.0.1:{port}/json/new?about:blank', method='PUT')
    ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=10)
    call('Page.enable')
    call('Runtime.enable')
    call(
        'Emulation.setDeviceMetricsOverride',
        {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True},
    )
    call('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
    call('Page.navigate', {'url': URL})

    wait_until("document.readyState === 'complete' && Boolean(document.querySelector('.mobile-toolbar'))")
    wait_until("Boolean(document.querySelector('.xterm-helper-textarea') && window.term)")
    time.sleep(0.5)

    initial = ui_state()
    results['initial'] = initial
    assert initial['labels'] == ['ESC', 'CTRL', 'A−', 'A+', '⛶'], initial
    assert initial['oneRow'] and not initial['toolbarOverflow'], initial
    assert initial['toolbarBottom'] == initial['viewportHeight'] and initial['fullscreenButton'], initial
    assert initial['maxTouchPoints'] > 0, initial
    assert not initial['activeIsTextarea'], initial

    if os.environ.get('WEBTERM_UI_ONLY') == '1':
        print(json.dumps({'initial': initial, 'PASS': True}, ensure_ascii=False, indent=2))
        raise SystemExit(0)

    terminal_tap()
    after_terminal_tap = ui_state()
    results['terminalTapFocus'] = after_terminal_tap['activeIsTextarea']
    assert after_terminal_tap['activeIsTextarea'], after_terminal_tap

    tap('.mobile-toolbar button')
    after_escape_tap = ui_state()
    results['escapeBlur'] = not after_escape_tap['activeIsTextarea']
    assert not after_escape_tap['activeIsTextarea'], after_escape_tap

    terminal_tap()
    before_font = ui_state()
    tap('.font-group button:last-child')
    after_plus = ui_state()
    results['fontPlus'] = {'before': before_font, 'after': after_plus}
    assert not after_plus['activeIsTextarea'], after_plus
    assert after_plus['fontSize'] == min(30, before_font['fontSize'] + 1), after_plus
    assert after_plus['rows'] <= before_font['rows'] and after_plus['cols'] <= before_font['cols'], (before_font, after_plus)
    assert (after_plus['rows'], after_plus['cols']) != (before_font['rows'], before_font['cols']), (before_font, after_plus)

    terminal_tap()
    tap('.font-group button:first-child')
    after_minus = ui_state()
    results['fontMinus'] = after_minus
    assert not after_minus['activeIsTextarea'], after_minus
    assert after_minus['fontSize'] == before_font['fontSize'], after_minus

    send_command('echo C_BEGIN; sleep 9999')
    wait_text('C_BEGIN')
    tap('.ctrl-button')
    ctrl_armed = ui_state()
    results['ctrlArmed'] = ctrl_armed
    assert ctrl_armed['ctrlPressed'] and not ctrl_armed['activeIsTextarea'], ctrl_armed
    terminal_tap()
    term_input('c')
    time.sleep(0.4)
    assert not ui_state()['ctrlPressed'], ui_state()
    send_command('echo C_OK')
    c_text = wait_text('C_OK')
    results['ctrlC'] = {'C_OK': 'C_OK' in c_text}
    assert 'C_OK' in c_text, c_text[-1200:]

    send_command('cat -v')
    time.sleep(0.2)
    terminal_tap()
    tap('.mobile-toolbar button:first-child')
    assert not ui_state()['activeIsTextarea'], ui_state()
    terminal_tap()
    press_enter()
    time.sleep(0.2)
    tap('.ctrl-button')
    assert ui_state()['ctrlPressed'] and not ui_state()['activeIsTextarea'], ui_state()
    terminal_tap()
    term_input('d')
    time.sleep(0.3)
    send_command('echo D_OK')
    d_text = wait_text('D_OK')
    results['escapeAndCtrlD'] = {'escapeVisible': '^[' in d_text, 'D_OK': 'D_OK' in d_text}
    assert '^[' in d_text and 'D_OK' in d_text, d_text[-1200:]

    send_command('echo TESTPID=$$')
    pid_text = wait_text('TESTPID=')
    pids = re.findall(r'TESTPID=(\d+)', pid_text)
    assert pids, pid_text[-1200:]
    first_pid = pids[-1]

    terminal_tap()
    tap('.fullscreen-group button')
    time.sleep(0.4)
    full_on = ui_state()
    results['fullscreenEnter'] = full_on
    assert full_on['fullscreen'] and not full_on['activeIsTextarea'], full_on
    tap('.fullscreen-group button')
    time.sleep(0.4)
    full_off = ui_state()
    results['fullscreenExit'] = full_off
    assert not full_off['fullscreen'] and not full_off['activeIsTextarea'], full_off

    results['freshReload'] = 'checked separately with direct tty websocket connections'
    results['PASS'] = True
    print(json.dumps(results, ensure_ascii=False, indent=2))
finally:
    if ws is not None:
        try:
            ws.close()
        except Exception:
            pass
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass
    profile.cleanup()
