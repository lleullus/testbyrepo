#!/usr/bin/env python3
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request

import websocket

URL = os.environ.get('WEBTERM_URL', 'http://127.0.0.1:7684/')


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def http_json(url, method='GET'):
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


debug_port = free_port()
profile = tempfile.TemporaryDirectory(prefix='webterm-xterm6-')
disable_gpu = os.environ.get('XTERM6_DISABLE_GPU') == '1'
chrome_args = [
    'google-chrome',
    '--headless=new',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--remote-allow-origins=*',
    f'--remote-debugging-port={debug_port}',
    f'--user-data-dir={profile.name}',
]
if disable_gpu:
    chrome_args.extend(['--disable-gpu', '--disable-software-rasterizer'])
chrome_args.append('about:blank')
chrome = subprocess.Popen(
    chrome_args,
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
    if remote.get('subtype') == 'error':
        raise RuntimeError(remote.get('description', 'runtime error'))
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


def buffer_text():
    return evaluate(
        """(() => {
            const term = window.term;
            if (!term) return '';
            const b = term.buffer.active;
            const out = [];
            for (let i = Math.max(0, b.length - 100); i < b.length; i++) {
                const line = b.getLine(i);
                if (line) out.push(line.translateToString(true));
            }
            return out.join('\\n');
        })()"""
    )


def wait_text(marker, timeout=8):
    deadline = time.time() + timeout
    last = ''
    while time.time() < deadline:
        last = buffer_text()
        if marker in last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'missing terminal marker {marker!r}; tail={last[-1600:]}')


def run_case(name, params, fragment=''):
    query = urllib.parse.urlencode(params)
    target_url = URL + ('&' if '?' in URL else '?') + query + fragment
    call('Page.navigate', {'url': target_url})
    wait_until("document.readyState === 'complete' && Boolean(window.term && window.term.element)")
    wait_until("Boolean(document.querySelector('.xterm-helper-textarea'))")
    time.sleep(0.6)

    marker = f'XTERM6_{name.upper()}_OK'
    evaluate(f"window.term.input({json.dumps('echo ' + marker + '\\r')}, true); true")
    wait_text(marker)
    state = evaluate(
        """(() => ({
            rows: window.term.rows,
            cols: window.term.cols,
            unicodeVersion: window.term.unicode.activeVersion,
            errors: (window.__xterm6Errors || []).slice(),
            logs: (window.__xterm6Logs || []).slice(),
            canvases: document.querySelectorAll('#terminal-container canvas').length
        }))()"""
    )
    assert state['rows'] > 0 and state['cols'] > 0, state
    assert state['errors'] == [], state
    return state


results = {'url': URL}
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
    call(
        'Page.addScriptToEvaluateOnNewDocument',
        {
            'source': """(() => {
                window.__xterm6Errors = [];
                window.__xterm6Logs = [];
                addEventListener('error', event => {
                    window.__xterm6Errors.push('error:' + (event.message || String(event.error)));
                });
                addEventListener('unhandledrejection', event => {
                    window.__xterm6Errors.push('rejection:' + String(event.reason));
                });
                for (const level of ['log', 'warn', 'error']) {
                    const original = console[level].bind(console);
                    console[level] = (...args) => {
                        try {
                            window.__xterm6Logs.push(level + ':' + args.map(v => {
                                if (typeof v === 'string') return v;
                                try { return JSON.stringify(v); } catch { return String(v); }
                            }).join(' '));
                        } catch {}
                        original(...args);
                    };
                }
            })();"""
        },
    )
    call(
        'Emulation.setDeviceMetricsOverride',
        {'width': 800, 'height': 600, 'deviceScaleFactor': 1, 'mobile': False},
    )

    dom = run_case('dom', {'rendererType': 'dom', 'unicodeVersion': '11', 'enableSixel': '1'})
    assert dom['unicodeVersion'] == '11', dom
    assert any('default renderer loaded' in line for line in dom['logs']), dom
    assert any('Sixel enabled' in line for line in dom['logs']), dom
    results['dom'] = dom
    results['unicode11Addon'] = True
    results['imageAddonLoad'] = True
    results['webLinksAddonSmoke'] = True

    canvas = run_case('canvas', {'rendererType': 'canvas', 'unicodeVersion': '11'})
    assert any('canvas renderer is unavailable with xterm 6; using default renderer' in line for line in canvas['logs']), canvas
    results['canvasLegacyFallback'] = canvas

    webgl = run_case('webgl', {'rendererType': 'webgl', 'unicodeVersion': '11'})
    loaded = any('WebGL renderer loaded' in line for line in webgl['logs'])
    fallback = any('WebGL renderer could not be loaded, falling back to default renderer' in line for line in webgl['logs'])
    assert loaded or fallback, webgl
    if disable_gpu:
        assert fallback and not loaded, webgl
    results['webgl'] = {
        'gpuDisabled': disable_gpu,
        'loaded': loaded,
        'initialFallback': fallback,
        'state': webgl,
    }

    if loaded:
        loss_requested = evaluate(
            """(() => {
                for (const canvas of document.querySelectorAll('#terminal-container canvas')) {
                    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                    const extension = gl?.getExtension('WEBGL_lose_context');
                    if (!extension) continue;
                    extension.loseContext();
                    return true;
                }
                return false;
            })()"""
        )
        results['webgl']['contextLossRequested'] = bool(loss_requested)
        if loss_requested:
            wait_until(
                "(window.__xterm6Logs || []).some(line => line.includes('WebGL context lost, falling back to default renderer'))",
                timeout=5,
            )
            evaluate("window.term.input('echo XTERM6_CONTEXT_LOSS_OK\\r', true); true")
            wait_text('XTERM6_CONTEXT_LOSS_OK')
            post_loss = evaluate(
                """(() => ({
                    errors: (window.__xterm6Errors || []).slice(),
                    logs: (window.__xterm6Logs || []).slice(),
                    rows: window.term.rows,
                    cols: window.term.cols
                }))()"""
            )
            assert post_loss['errors'] == [], post_loss
            assert post_loss['rows'] > 0 and post_loss['cols'] > 0, post_loss
            results['webgl']['postContextLoss'] = post_loss

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
