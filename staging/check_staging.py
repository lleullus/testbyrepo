#!/usr/bin/env python3
import json
import os
import re
import shlex
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


def set_device(width, height):
    call(
        'Emulation.setDeviceMetricsOverride',
        {'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': True},
    )
    time.sleep(0.2)


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
    call(
        'Input.dispatchTouchEvent',
        {
            'type': 'touchStart',
            'touchPoints': [{'x': point['x'], 'y': point['y'], 'radiusX': 2, 'radiusY': 2, 'force': 1, 'id': 1}],
        },
    )
    call('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    time.sleep(0.15)


def insert_text(text):
    call('Input.insertText', {'text': text})
    time.sleep(0.05)

def dispatch_physical_text_action(text, code, key_code, shift=False, invalidate=False):
    evaluate(
        f"""(async () => {{
            const textarea = document.querySelector('.xterm-helper-textarea');
            const keyOptions = {{
                key:{json.dumps(text)}, code:{json.dumps(code)}, keyCode:{key_code}, which:{key_code},
                shiftKey:{str(shift).lower()}, bubbles:true, cancelable:true
            }};
            textarea.dispatchEvent(new KeyboardEvent('keydown', keyOptions));
            await new Promise(resolve => setTimeout(resolve, 0));
            textarea.dispatchEvent(new InputEvent('beforeinput', {{
                data:{json.dumps(text)}, inputType:'insertText', isComposing:false,
                bubbles:true, cancelable:true
            }}));
            if ({str(invalidate).lower()}) textarea.blur();
            textarea.value = {json.dumps(text)};
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            textarea.dispatchEvent(new InputEvent('input', {{
                data:{json.dumps(text)}, inputType:'insertText', isComposing:false, bubbles:true
            }}));
            textarea.dispatchEvent(new KeyboardEvent('keyup', keyOptions));
            return true;
        }})()"""
    )


def dispatch_physical_enter_action():
    evaluate(
        """(() => {
            const textarea = document.querySelector('.xterm-helper-textarea');
            const diagnosticAt = performance.now();
            const keyOptions = {
                key:'Enter', code:'Enter', keyCode:13, which:13,
                bubbles:true, cancelable:true
            };
            textarea.dispatchEvent(new KeyboardEvent('keydown', keyOptions));
            textarea.dispatchEvent(new InputEvent('beforeinput', {
                data:null, inputType:'insertLineBreak', isComposing:false,
                bubbles:true, cancelable:true
            }));
            textarea.value = '\\n';
            textarea.setSelectionRange(1, 1);
            textarea.dispatchEvent(new InputEvent('input', {
                data:null, inputType:'insertLineBreak', isComposing:false, bubbles:true
            }));
            textarea.dispatchEvent(new KeyboardEvent('keyup', keyOptions));
            window.__r8PhysicalEnterEvents = (window.ttydDiagnostics?.().events || []).filter(
                event => event.at >= diagnosticAt && ['terminal-data', 'input-sent'].includes(event.event)
            );
            return true;
        })()"""
    )


def dispatch_ended_composition_then_physical_enter(text):
    evaluate(
        f"""(() => {{
            const textarea = document.querySelector('.xterm-helper-textarea');
            const diagnosticAt = performance.now();
            textarea.dispatchEvent(new CompositionEvent('compositionstart', {{data:'', bubbles:true}}));
            textarea.dispatchEvent(new CompositionEvent('compositionupdate', {{data:{json.dumps(text)}, bubbles:true}}));
            textarea.dispatchEvent(new InputEvent('beforeinput', {{
                data:{json.dumps(text)}, inputType:'insertCompositionText', isComposing:true,
                bubbles:true, cancelable:true
            }}));
            textarea.value = {json.dumps(text)};
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            textarea.dispatchEvent(new InputEvent('input', {{
                data:{json.dumps(text)}, inputType:'insertCompositionText', isComposing:true, bubbles:true
            }}));
            textarea.dispatchEvent(new CompositionEvent('compositionend', {{data:{json.dumps(text)}, bubbles:true}}));
            const downOptions = {{
                key:'Enter', code:'', keyCode:13, which:13,
                bubbles:true, cancelable:true
            }};
            textarea.dispatchEvent(new KeyboardEvent('keydown', downOptions));
            textarea.dispatchEvent(new InputEvent('beforeinput', {{
                data:null, inputType:'insertLineBreak', isComposing:false,
                bubbles:true, cancelable:true
            }}));
            textarea.value = {json.dumps(text + chr(10))};
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            textarea.dispatchEvent(new InputEvent('input', {{
                data:null, inputType:'insertLineBreak', isComposing:false, bubbles:true
            }}));
            textarea.dispatchEvent(new KeyboardEvent('keyup', {{
                key:'Enter', code:'Enter', keyCode:13, which:13,
                bubbles:true, cancelable:true
            }}));
            window.__r8EndedCompositionEnterEvents = (window.ttydDiagnostics?.().events || []).filter(
                event => event.at >= diagnosticAt && ['terminal-data', 'input-sent'].includes(event.event)
            );
            return true;
        }})()"""
    )


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

def start_composition(text):
    evaluate(
        f"""(() => {{
            const textarea = document.querySelector('.xterm-helper-textarea');
            textarea.dispatchEvent(new CompositionEvent('compositionstart', {{data:'', bubbles:true}}));
            const before = textarea.value;
            textarea.setSelectionRange(before.length, before.length);
            textarea.dispatchEvent(new CompositionEvent('compositionupdate', {{data:{json.dumps(text)}, bubbles:true}}));
            textarea.dispatchEvent(new InputEvent('beforeinput', {{data:{json.dumps(text)}, inputType:'insertCompositionText', isComposing:true, bubbles:true, cancelable:true}}));
            textarea.value = before + {json.dumps(text)};
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            textarea.dispatchEvent(new InputEvent('input', {{data:{json.dumps(text)}, inputType:'insertCompositionText', isComposing:true, bubbles:true}}));
            return true;
        }})()"""
    )


def end_composition(text):
    evaluate(
        f"""(() => {{
            const textarea = document.querySelector('.xterm-helper-textarea');
            textarea.dispatchEvent(new CompositionEvent('compositionend', {{data:{json.dumps(text)}, bubbles:true}}));
            textarea.dispatchEvent(new InputEvent('input', {{data:{json.dumps(text)}, inputType:'insertText', isComposing:false, bubbles:true}}));
            return true;
        }})()"""
    )
    time.sleep(0.05)

def rapid_composition_sequence(values):
    evaluate(
        f"""(() => {{
            const textarea = document.querySelector('.xterm-helper-textarea');
            for (const text of {json.dumps(values, ensure_ascii=False)}) {{
                textarea.dispatchEvent(new CompositionEvent('compositionstart', {{data:'', bubbles:true}}));
                textarea.dispatchEvent(new CompositionEvent('compositionupdate', {{data:text, bubbles:true}}));
                textarea.dispatchEvent(new InputEvent('beforeinput', {{
                    data:text, inputType:'insertCompositionText', isComposing:true,
                    bubbles:true, cancelable:true
                }}));
                textarea.value = text;
                textarea.setSelectionRange(textarea.value.length, textarea.value.length);
                textarea.dispatchEvent(new InputEvent('input', {{
                    data:text, inputType:'insertCompositionText', isComposing:true, bubbles:true
                }}));
                textarea.dispatchEvent(new CompositionEvent('compositionend', {{data:text, bubbles:true}}));
            }}
            return true;
        }})()"""
    )


def visibility_invalidate():
    evaluate(
        """(() => {
            Object.defineProperty(document, 'visibilityState', {value:'hidden', configurable:true});
            document.dispatchEvent(new Event('visibilitychange'));
            Object.defineProperty(document, 'visibilityState', {value:'visible', configurable:true});
            document.dispatchEvent(new Event('visibilitychange'));
            return true;
        })()"""
    )
    time.sleep(0.05)

def disconnect_input_owner():
    before = evaluate("window.ttydDiagnostics().inputEpoch")
    evaluate("window.__webtermTestSockets.at(-1).close(4000, 'stale-input-check')")
    wait_until(f"window.ttydDiagnostics().inputEpoch > {before} && !window.ttydDiagnostics().composing")


def dispatch_textarea_edit(input_type, value, before_data=None, input_data=None):
    evaluate(
        f"""(() => {{
            const textarea = document.querySelector('.xterm-helper-textarea');
            textarea.dispatchEvent(new InputEvent('beforeinput', {{
                data:{json.dumps(before_data)}, inputType:{json.dumps(input_type)},
                isComposing:false, bubbles:true, cancelable:true
            }}));
            textarea.value = {json.dumps(value)};
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            textarea.dispatchEvent(new InputEvent('input', {{
                data:{json.dumps(input_data)}, inputType:{json.dumps(input_type)},
                isComposing:false, bubbles:true
            }}));
            return textarea.value;
        }})()"""
    )
    time.sleep(0.05)

def blur_textarea():
    evaluate("document.querySelector('.xterm-helper-textarea').blur()")
    time.sleep(0.05)


def paste_text(text):
    evaluate(
        f"""(() => {{
            const transfer = new DataTransfer();
            transfer.setData('text/plain', {json.dumps(text)});
            return document.querySelector('.xterm-helper-textarea').dispatchEvent(
                new ClipboardEvent('paste', {{clipboardData:transfer, bubbles:true, cancelable:true}})
            );
        }})()"""
    )


def terminal_tap():
    point = center('#terminal-container .xterm-screen')
    call(
        'Input.dispatchTouchEvent',
        {
            'type': 'touchStart',
            'touchPoints': [{'x': point['x'], 'y': point['y'], 'radiusX': 2, 'radiusY': 2, 'force': 1, 'id': 1}],
        },
    )
    call('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    time.sleep(0.15)


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


key_capture_index = 0


def capture_toolbar_bytes(action, application_cursor=False, settle=False):
    global key_capture_index
    key_capture_index += 1
    marker = f'KEY_{key_capture_index}'
    cursor_mode = '\x1b[?1h' if application_cursor else '\x1b[?1l'
    terminal_tap()
    term_input('\x03')
    time.sleep(0.1)
    settled_read = (
        "import time;time.sleep(0.15);ready,_,_=select.select([fd],[],[],0);"
        "data+=os.read(fd,64) if ready else b'';"
        if settle
        else ''
    )
    script = (
        "import os,select,termios,tty;"
        "fd=0;old=termios.tcgetattr(fd);"
        f"print({cursor_mode!r}+{(marker + '_READY')!r},end='',flush=True);"
        "tty.setraw(fd);termios.tcflush(fd,termios.TCIFLUSH);"
        "ready,_,_=select.select([fd],[],[],2.0);data=os.read(fd,64) if ready else b'';"
        + settled_read
        + "termios.tcsetattr(fd,termios.TCSADRAIN,old);"
        + f"print('\\n\\x1b[?1l{marker}_HEX='+data.hex(),flush=True)"
    )
    send_command('python3 -c ' + shlex.quote(script))
    wait_text(marker + '_READY')
    wait_until(
        f"Boolean(window.term) && window.term.modes.applicationCursorKeysMode === {str(application_cursor).lower()}"
    )
    action()
    text = wait_text(marker + '_HEX=')
    matches = re.findall(re.escape(marker) + r'_HEX=([0-9a-f]*)', text)
    if not matches:
        raise AssertionError(f'key bytes not captured for {marker}: {text[-1200:]}')
    return matches[-1]

def preedit_state():
    return evaluate(
        """(() => {
            const view = document.querySelector('.composition-view');
            const textarea = document.querySelector('.xterm-helper-textarea');
            if (!view || !textarea) return null;
            const vr = view.getBoundingClientRect();
            const tr = textarea.getBoundingClientRect();
            return {
                active: view.classList.contains('active'),
                text: view.textContent || '',
                viewRect: {left: vr.left, top: vr.top, width: vr.width, height: vr.height},
                textareaRect: {left: tr.left, top: tr.top, width: tr.width, height: tr.height},
                textareaAriaLabel: textarea.getAttribute('aria-label'),
                focused: document.activeElement === textarea,
                textareaValue: textarea.value,
                selectionStart: textarea.selectionStart,
                selectionEnd: textarea.selectionEnd,
            };
        })()"""
    )


def capture_visible_preedit(text):
    global key_capture_index
    key_capture_index += 1
    marker = f'PREEDIT_{key_capture_index}'
    terminal_tap()
    term_input('\x03')
    time.sleep(0.1)
    script = (
        "import os,select,termios,tty;"
        "fd=0;old=termios.tcgetattr(fd);"
        f"print({(marker + '_READY')!r},flush=True);"
        "tty.setraw(fd);termios.tcflush(fd,termios.TCIFLUSH);"
        "ready,_,_=select.select([fd],[],[],0.6);pre=os.read(fd,64) if ready else b'';"
        f"print('\\n{marker}_PRE='+pre.hex(),flush=True);"
        "ready,_,_=select.select([fd],[],[],2.0);post=os.read(fd,64) if ready else b'';"
        "termios.tcsetattr(fd,termios.TCSADRAIN,old);"
        f"print('\\n{marker}_POST='+post.hex(),flush=True)"
    )
    send_command('python3 -c ' + shlex.quote(script))
    wait_text(marker + '_READY')
    start_composition(text)
    visible = preedit_state()
    before_commit_text = wait_text(marker + '_PRE=')
    before_matches = re.findall(re.escape(marker) + r'_PRE=([0-9a-f]*)', before_commit_text)
    assert before_matches and before_matches[-1] == '', before_commit_text[-1200:]
    end_composition(text)
    after_commit_text = wait_text(marker + '_POST=')
    after_matches = re.findall(re.escape(marker) + r'_POST=([0-9a-f]*)', after_commit_text)
    assert after_matches, after_commit_text[-1200:]
    cleared = preedit_state()
    return {
        'draft': text,
        'beforeCommitPtyHex': before_matches[-1],
        'beforeCommitView': visible,
        'afterCommitPtyHex': after_matches[-1],
        'afterCommitView': cleared,
    }


def ui_state():
    return evaluate(
        """(() => {
            const toolbar = document.querySelector('.mobile-toolbar');
            const buttons = [...document.querySelectorAll('.mobile-toolbar button')];
            const toolbarRows = [...document.querySelectorAll('.toolbar-row')];
            const textarea = document.querySelector('.xterm-helper-textarea');
            if (!toolbar || !textarea || !window.term || toolbarRows.length === 0) return null;
            const tr = toolbar.getBoundingClientRect();
            const rowStates = toolbarRows.map(row => {
                const rowButtons = [...row.querySelectorAll('button')];
                const tops = rowButtons.map(button => Math.round(button.getBoundingClientRect().top));
                return {
                    labels: rowButtons.map(button => (button.textContent || '').trim()),
                    oneLine: tops.length > 0 && tops.every(top => top === tops[0]),
                    overflow: row.scrollWidth > row.clientWidth,
                    height: Math.round(row.getBoundingClientRect().height),
                };
            });
            return {
                labels: buttons.map(b => (b.textContent || '').trim()),
                rowCount: toolbarRows.length,
                rowStates,
                toolbarTop: Math.round(tr.top),
                toolbarBottom: Math.round(tr.bottom),
                toolbarHeight: Math.round(tr.height),
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                toolbarOverflow: toolbar.scrollWidth > toolbar.clientWidth,
                activeIsTextarea: document.activeElement === textarea,
                activeTag: document.activeElement ? document.activeElement.tagName : null,
                coarse: matchMedia('(pointer: coarse)').matches,
                maxTouchPoints: navigator.maxTouchPoints,
                fontSize: Number(window.term.options.fontSize),
                ctrlPressed: document.querySelector('.ctrl-button')?.getAttribute('aria-pressed') === 'true',
                shiftPressed: document.querySelector('.shift-button')?.getAttribute('aria-pressed') === 'true',
                fullscreen: Boolean(document.fullscreenElement),
                rows: window.term.rows,
                cols: window.term.cols,
                applicationCursorKeysMode: window.term.modes.applicationCursorKeysMode,
                fullscreenButton: Boolean(document.querySelector('button[aria-label*="fullscreen" i]')),
                diagnostics: window.ttydDiagnostics?.(),
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
    set_device(390, 844)
    call('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
    call(
        'Page.addScriptToEvaluateOnNewDocument',
        {
            'source': """(() => {
                const NativeWebSocket = window.WebSocket;
                window.__webtermTestSockets = [];
                window.WebSocket = class extends NativeWebSocket {
                    constructor(...args) {
                        super(...args);
                        window.__webtermTestSockets.push(this);
                    }
                };
            })();"""
        },
    )
    call('Page.navigate', {'url': URL})

    wait_until("document.readyState === 'complete' && Boolean(document.querySelector('.mobile-toolbar'))")
    wait_until("Boolean(document.querySelector('.xterm-helper-textarea') && window.term)")
    time.sleep(0.5)

    initial = ui_state()
    results['initial'] = initial
    expected_labels = ['TAB', '⇧', '←', '↑', '↓', '→', '↵', 'ESC', 'CTRL', 'A−', 'A+', '⛶']
    assert initial['labels'] == expected_labels, initial
    assert initial['rowCount'] == 1 and not initial['toolbarOverflow'], initial
    assert initial['rowStates'][0]['labels'] == expected_labels, initial
    assert initial['rowStates'][0]['oneLine'] and not initial['rowStates'][0]['overflow'], initial
    assert 34 <= initial['toolbarHeight'] <= 36, initial
    assert initial['toolbarBottom'] == initial['viewportHeight'] and initial['fullscreenButton'], initial
    assert initial['maxTouchPoints'] > 0, initial
    assert not initial['activeIsTextarea'] and not initial['shiftPressed'], initial

    set_device(844, 390)
    landscape = ui_state()
    results['landscape'] = landscape
    assert landscape['labels'] == expected_labels, landscape
    assert landscape['rowCount'] == 1 and not landscape['toolbarOverflow'], landscape
    assert landscape['rowStates'][0]['oneLine'] and not landscape['rowStates'][0]['overflow'], landscape
    assert landscape['toolbarBottom'] == landscape['viewportHeight'], landscape
    set_device(390, 844)

    if os.environ.get('WEBTERM_UI_ONLY') == '1':
        print(json.dumps({'initial': initial, 'landscape': landscape, 'PASS': True}, ensure_ascii=False, indent=2))
        raise SystemExit(0)

    terminal_tap()
    wait_until("Boolean(window.ttydDiagnostics?.().inputReady)", timeout=15)
    terminal_tap()
    after_terminal_tap = ui_state()
    results['terminalTapFocus'] = after_terminal_tap['activeIsTextarea']
    assert after_terminal_tap['activeIsTextarea'], {
        'owner': {
            key: after_terminal_tap['diagnostics'][key]
            for key in ('inputReady', 'inputEpoch', 'focusIntent', 'focused')
        },
        'events': after_terminal_tap['diagnostics']['events'][-5:],
    }

    tap('.escape-button')
    after_escape_tap = ui_state()
    results['escapePreservesFocus'] = after_escape_tap['activeIsTextarea']
    assert after_escape_tap['activeIsTextarea'], after_escape_tap

    tap('.shift-button')
    shift_armed = ui_state()
    results['shiftArmed'] = shift_armed
    assert shift_armed['shiftPressed'] and shift_armed['activeIsTextarea'], {
        'state': {'shift': shift_armed['shiftPressed'], 'focus': shift_armed['activeIsTextarea']},
        'events': [(e['event'], e.get('value')) for e in shift_armed['diagnostics']['events'][-10:]],
    }
    terminal_tap()
    shift_after_terminal_tap = ui_state()
    results['shiftClearsOnTerminalTap'] = shift_after_terminal_tap
    assert shift_after_terminal_tap['activeIsTextarea'] and not shift_after_terminal_tap['shiftPressed'], shift_after_terminal_tap

    tap('.ctrl-button')
    assert ui_state()['ctrlPressed'], ui_state()
    tap('.shift-button')
    modifier_exclusive = ui_state()
    results['modifierExclusive'] = modifier_exclusive
    assert modifier_exclusive['shiftPressed'] and not modifier_exclusive['ctrlPressed'], modifier_exclusive
    tap('.shift-button')
    assert not ui_state()['shiftPressed'], ui_state()

    tap('.shift-button')
    assert ui_state()['shiftPressed'], ui_state()
    tap('.enter-button')
    shift_after_enter = ui_state()
    results['shiftClearsOnEnter'] = shift_after_enter
    assert not shift_after_enter['shiftPressed'] and shift_after_enter['activeIsTextarea'], shift_after_enter

    tap('.ctrl-button')
    assert ui_state()['ctrlPressed'], ui_state()
    tap('.enter-button')
    ctrl_after_enter = ui_state()
    results['ctrlClearsOnEnter'] = ctrl_after_enter
    assert not ctrl_after_enter['ctrlPressed'] and ctrl_after_enter['activeIsTextarea'], ctrl_after_enter

    tap('.ctrl-button')
    assert ui_state()['ctrlPressed'], ui_state()
    tap('.tab-button')
    ctrl_after_tab = ui_state()
    results['ctrlClearsOnTab'] = ctrl_after_tab
    assert not ctrl_after_tab['ctrlPressed'] and ctrl_after_tab['activeIsTextarea'], ctrl_after_tab
    terminal_tap()
    term_input('\x03')
    time.sleep(0.1)

    ctrl_after_arrows = {}
    for selector in ('.arrow-left', '.arrow-up', '.arrow-down', '.arrow-right'):
        tap('.ctrl-button')
        assert ui_state()['ctrlPressed'], ui_state()
        tap(selector)
        state = ui_state()
        ctrl_after_arrows[selector] = state['ctrlPressed']
        assert not state['ctrlPressed'] and state['activeIsTextarea'], (selector, state)
        terminal_tap()
        term_input('\x03')
        time.sleep(0.1)
    results['ctrlClearsOnArrows'] = ctrl_after_arrows

    enter_hex = capture_toolbar_bytes(lambda: tap('.enter-button'))
    results['enterBytes'] = enter_hex
    assert enter_hex == '0d', enter_hex

    tab_hex = capture_toolbar_bytes(lambda: tap('.tab-button'))
    shift_tab_hex = capture_toolbar_bytes(lambda: (tap('.shift-button'), tap('.tab-button')))
    results['tabBytes'] = {'tab': tab_hex, 'shiftTab': shift_tab_hex}
    assert tab_hex == '09', tab_hex
    assert shift_tab_hex == '1b5b5a', shift_tab_hex
    assert not ui_state()['shiftPressed'] and ui_state()['activeIsTextarea'], ui_state()

    normal_arrows = {}
    normal_expected = {
        '.arrow-left': '1b5b44',
        '.arrow-up': '1b5b41',
        '.arrow-down': '1b5b42',
        '.arrow-right': '1b5b43',
    }
    for selector, expected in normal_expected.items():
        actual = capture_toolbar_bytes(lambda selector=selector: tap(selector))
        normal_arrows[selector] = actual
        assert actual == expected, (selector, actual)
    results['normalArrowBytes'] = normal_arrows

    application_arrows = {}
    application_expected = {
        '.arrow-left': '1b4f44',
        '.arrow-up': '1b4f41',
        '.arrow-down': '1b4f42',
        '.arrow-right': '1b4f43',
    }
    for selector, expected in application_expected.items():
        actual = capture_toolbar_bytes(lambda selector=selector: tap(selector), application_cursor=True)
        application_arrows[selector] = actual
        assert actual == expected, (selector, actual)
    results['applicationArrowBytes'] = application_arrows

    shifted_arrows = {}
    shifted_expected = {
        '.arrow-left': '1b5b313b3244',
        '.arrow-up': '1b5b313b3241',
        '.arrow-down': '1b5b313b3242',
        '.arrow-right': '1b5b313b3243',
    }
    for selector, expected in shifted_expected.items():
        actual = capture_toolbar_bytes(lambda selector=selector: (tap('.shift-button'), tap(selector)))
        shifted_arrows[selector] = actual
        assert actual == expected, (selector, actual)
        assert not ui_state()['shiftPressed'], ui_state()
    results['shiftArrowBytes'] = shifted_arrows
    ordinary_english_value = 'x'
    ordinary_english_hex = capture_toolbar_bytes(lambda: insert_text(ordinary_english_value))
    results['ordinaryEnglishInputBytes'] = ordinary_english_hex
    assert ordinary_english_hex == ordinary_english_value.encode().hex(), ordinary_english_hex

    physical_enter_hex = capture_toolbar_bytes(dispatch_physical_enter_action, settle=True)
    results['physicalEnterDualEventBytes'] = physical_enter_hex
    assert physical_enter_hex == '0d', physical_enter_hex
    physical_enter_events = evaluate("window.__r8PhysicalEnterEvents")
    results['physicalEnterSenderEvents'] = physical_enter_events
    assert [event['event'] for event in physical_enter_events] == ['terminal-data', 'input-sent'], physical_enter_events

    repeated_physical_enter_count = 3
    repeated_physical_enter_hex = capture_toolbar_bytes(
        lambda: [dispatch_physical_enter_action() for _ in range(repeated_physical_enter_count)],
        settle=True,
    )
    results['repeatedPhysicalEnterDualEventBytes'] = repeated_physical_enter_hex
    assert repeated_physical_enter_hex == '0d' * repeated_physical_enter_count, repeated_physical_enter_hex

    software_linebreak_hex = capture_toolbar_bytes(
        lambda: dispatch_textarea_edit('insertLineBreak', '\n', None, None), settle=True
    )
    results['softwareLinebreakBytes'] = software_linebreak_hex
    assert software_linebreak_hex == '0d', software_linebreak_hex

    ended_composition_value = '다'
    ended_composition_enter_hex = capture_toolbar_bytes(
        lambda: dispatch_ended_composition_then_physical_enter(ended_composition_value), settle=True
    )
    results['endedCompositionThenPhysicalEnterBytes'] = ended_composition_enter_hex
    assert ended_composition_enter_hex == (ended_composition_value.encode() + b'\r').hex(), ended_composition_enter_hex
    ended_composition_enter_events = evaluate("window.__r8EndedCompositionEnterEvents")
    results['endedCompositionThenPhysicalEnterSenderEvents'] = ended_composition_enter_events
    assert [event['event'] for event in ended_composition_enter_events] == [
        'input-sent',
        'terminal-data',
        'input-sent',
    ], ended_composition_enter_events

    physical_space_hex = capture_toolbar_bytes(
        lambda: dispatch_physical_text_action(' ', 'Space', 32), settle=True
    )
    results['physicalSpaceDualEventBytes'] = physical_space_hex
    assert physical_space_hex == '20', physical_space_hex

    repeated_space_count = 6
    repeated_space_hex = capture_toolbar_bytes(
        lambda: [
            dispatch_physical_text_action(' ', 'Space', 32) for _ in range(repeated_space_count)
        ],
        settle=True,
    )
    results['repeatedPhysicalSpaceDualEventBytes'] = repeated_space_hex
    assert repeated_space_hex == '20' * repeated_space_count, repeated_space_hex

    punctuation_hex = capture_toolbar_bytes(
        lambda: dispatch_physical_text_action('!', 'Digit1', 49, shift=True), settle=True
    )
    results['physicalPunctuationDualEventBytes'] = punctuation_hex
    assert punctuation_hex == '21', punctuation_hex

    physical_ascii = [('a', 'KeyA', 65), ('b', 'KeyB', 66), ('1', 'Digit1', 49), ('2', 'Digit2', 50)]
    physical_ascii_value = ''.join(value for value, _, _ in physical_ascii)
    physical_ascii_hex = capture_toolbar_bytes(
        lambda: [dispatch_physical_text_action(*action) for action in physical_ascii], settle=True
    )
    results['physicalAsciiDualEventBytes'] = physical_ascii_hex
    assert physical_ascii_hex == physical_ascii_value.encode().hex(), physical_ascii_hex

    stale_physical_hex = capture_toolbar_bytes(
        lambda: (
            dispatch_physical_text_action('q', 'KeyQ', 81, invalidate=True),
            dispatch_textarea_edit('insertText', 'z', 'z', 'z'),
        ),
        settle=True,
    )
    results['invalidatedPhysicalThenSoftwareInputBytes'] = stale_physical_hex
    assert stale_physical_hex == '717a', stale_physical_hex

    paste_value = 'c'
    paste_hex = capture_toolbar_bytes(lambda: (tap('.ctrl-button'), paste_text(paste_value)))
    results['pasteBytes'] = paste_hex
    assert paste_hex == paste_value.encode().hex(), {
        'hex': paste_hex,
        'events': ui_state()['diagnostics']['events'][-12:],
    }
    assert not ui_state()['ctrlPressed'] and ui_state()['activeIsTextarea'], ui_state()

    composition_results = {}
    for composition_value in ('한', 'hello'):
        composition_result = capture_visible_preedit(composition_value)
        composition_results[composition_value] = composition_result
        assert composition_result['beforeCommitPtyHex'] == '', composition_result
        visible = composition_result['beforeCommitView']
        assert visible['active'] and visible['text'] == composition_value, composition_result
        assert visible['focused'] and visible['textareaAriaLabel'], composition_result
        assert visible['viewRect']['width'] > 0 and visible['viewRect']['height'] > 0, composition_result
        assert abs(visible['viewRect']['left'] - visible['textareaRect']['left']) < 1, composition_result
        assert abs(visible['viewRect']['top'] - visible['textareaRect']['top']) < 1, composition_result
        assert composition_result['afterCommitPtyHex'] == composition_value.encode().hex(), composition_result
        cleared = composition_result['afterCommitView']
        assert not cleared['active'] and cleared['text'] == '', composition_result
        assert cleared['textareaValue'] == '', composition_result
    results['syntheticCompositionPreedit'] = composition_results
    results['syntheticCompositionBytes'] = composition_results['한']['afterCommitPtyHex']

    accumulated_value = '한글abc'
    accumulated_space_hex = capture_toolbar_bytes(
        lambda: (
            start_composition(accumulated_value),
            end_composition(accumulated_value),
            dispatch_textarea_edit('insertText', ' ', ' ', accumulated_value + ' '),
        ),
        settle=True,
    )
    results['accumulatedThenSpaceBytes'] = accumulated_space_hex
    assert accumulated_space_hex == (accumulated_value + ' ').encode().hex(), accumulated_space_hex
    settled_space_state = preedit_state()
    results['accumulatedThenSpaceTextarea'] = settled_space_state
    assert settled_space_state['textareaValue'] == '', settled_space_state

    rapid_values = ['가', '나', '다']
    rapid_value = ''.join(rapid_values)
    rapid_hex = capture_toolbar_bytes(lambda: rapid_composition_sequence(rapid_values), settle=True)
    results['rapidCompositionBytes'] = rapid_hex
    assert rapid_hex == rapid_value.encode().hex(), rapid_hex

    rapid_space_hex = capture_toolbar_bytes(
        lambda: (
            rapid_composition_sequence(rapid_values),
            time.sleep(0.02),
            dispatch_textarea_edit('insertText', ' ', ' ', ' '),
        ),
        settle=True,
    )
    results['rapidCompositionThenSpaceBytes'] = rapid_space_hex
    assert rapid_space_hex == (rapid_value + ' ').encode().hex(), rapid_space_hex

    rapid_backspace_hex = capture_toolbar_bytes(
        lambda: (
            rapid_composition_sequence(rapid_values),
            time.sleep(0.02),
            dispatch_textarea_edit('deleteContentBackward', '', None, None),
        ),
        settle=True,
    )
    results['rapidCompositionThenBackspaceBytes'] = rapid_backspace_hex
    assert rapid_backspace_hex == (rapid_value.encode() + b'\x7f').hex(), rapid_backspace_hex

    accumulated_delete_value = 'abc'
    accumulated_delete_hex = capture_toolbar_bytes(
        lambda: (
            start_composition(accumulated_delete_value),
            end_composition(accumulated_delete_value),
            dispatch_textarea_edit('deleteContentBackward', '', None, None),
        ),
        settle=True,
    )
    results['accumulatedThenBackspaceBytes'] = accumulated_delete_hex
    assert accumulated_delete_hex == (accumulated_delete_value.encode() + b'\x7f').hex(), accumulated_delete_hex
    settled_delete_state = preedit_state()
    results['accumulatedThenBackspaceTextarea'] = settled_delete_state
    assert settled_delete_state['textareaValue'] == '', settled_delete_state

    paste_following_value = '붙여넣기123'
    paste_following_hex = capture_toolbar_bytes(
        lambda: (paste_text(paste_following_value), dispatch_textarea_edit('insertText', 'x', 'x', 'x')),
        settle=True,
    )
    results['pasteThenInputBytes'] = paste_following_hex
    assert paste_following_hex == (paste_following_value + 'x').encode().hex(), paste_following_hex

    stale_composition_value = '늦음'
    post_invalidation_value = 'z'
    stale_composition_hex = capture_toolbar_bytes(
        lambda: (
            start_composition(stale_composition_value),
            blur_textarea(),
            end_composition(stale_composition_value),
            dispatch_textarea_edit('insertText', post_invalidation_value, post_invalidation_value, post_invalidation_value),
        ),
        settle=True,
    )
    results['staleCompositionThenInputBytes'] = stale_composition_hex
    assert stale_composition_hex == post_invalidation_value.encode().hex(), stale_composition_hex

    visibility_stale_value = '숨김'
    visibility_post_value = 'v'
    visibility_stale_hex = capture_toolbar_bytes(
        lambda: (
            start_composition(visibility_stale_value),
            visibility_invalidate(),
            end_composition(visibility_stale_value),
            terminal_tap(),
            dispatch_textarea_edit('insertText', visibility_post_value, visibility_post_value, visibility_post_value),
        ),
        settle=True,
    )
    results['visibilityStaleCompositionThenInputBytes'] = visibility_stale_hex
    assert visibility_stale_hex == visibility_post_value.encode().hex(), visibility_stale_hex

    disconnect_stale_value = '단절'
    disconnect_post_value = 'd'
    disconnect_stale_hex = capture_toolbar_bytes(
        lambda: (
            start_composition(disconnect_stale_value),
            disconnect_input_owner(),
            end_composition(disconnect_stale_value),
            wait_until("window.ttydDiagnostics().inputReady", timeout=15),
            terminal_tap(),
            dispatch_textarea_edit('insertText', disconnect_post_value, disconnect_post_value, disconnect_post_value),
        ),
        settle=True,
    )
    results['disconnectStaleCompositionThenInputBytes'] = disconnect_stale_hex
    assert disconnect_stale_hex == disconnect_post_value.encode().hex(), disconnect_stale_hex

    composing_enter_value = '가'
    composing_enter_hex = capture_toolbar_bytes(
        lambda: (start_composition(composing_enter_value), press_enter(), end_composition(composing_enter_value))
    )
    results['syntheticComposingEnterBytes'] = composing_enter_hex
    assert composing_enter_hex == composing_enter_value.encode().hex(), composing_enter_hex
    composing_enter_view = preedit_state()
    results['syntheticComposingEnterView'] = composing_enter_view
    assert not composing_enter_view['active'] and composing_enter_view['text'] == '', composing_enter_view

    composing_cancel_value = '나'
    composing_cancel_hex = capture_toolbar_bytes(
        lambda: (start_composition(composing_cancel_value), tap('.escape-button'), end_composition(composing_cancel_value))
    )
    results['syntheticComposingEscapeBytes'] = composing_cancel_hex
    assert composing_cancel_hex == '', composing_cancel_hex
    composing_cancel_view = preedit_state()
    results['syntheticComposingEscapeView'] = composing_cancel_view
    assert not composing_cancel_view['active'] and composing_cancel_view['text'] == '', composing_cancel_view

    ctrl_escape_hex = capture_toolbar_bytes(lambda: (tap('.ctrl-button'), tap('.escape-button')))
    plain_c_hex = capture_toolbar_bytes(lambda: term_input('c'))
    results['ctrlEscapeThenCBytes'] = {'escape': ctrl_escape_hex, 'c': plain_c_hex}
    assert ctrl_escape_hex == '1b' and plain_c_hex == '63', results['ctrlEscapeThenCBytes']
    assert ui_state()['activeIsTextarea'], ui_state()

    terminal_tap()
    before_font = ui_state()
    tap('.font-increase-button')
    after_plus = ui_state()
    results['fontPlus'] = {'before': before_font, 'after': after_plus}
    assert after_plus['activeIsTextarea'], after_plus
    assert after_plus['fontSize'] == min(32, before_font['fontSize'] + 1), after_plus
    assert after_plus['rows'] <= before_font['rows'] and after_plus['cols'] <= before_font['cols'], (before_font, after_plus)
    assert (after_plus['rows'], after_plus['cols']) != (before_font['rows'], before_font['cols']), (before_font, after_plus)

    terminal_tap()
    tap('.font-decrease-button')
    after_minus = ui_state()
    results['fontMinus'] = after_minus
    assert after_minus['activeIsTextarea'], after_minus
    assert after_minus['fontSize'] == before_font['fontSize'], after_minus

    send_command('echo C_BEGIN; sleep 9999')
    wait_text('C_BEGIN')
    tap('.ctrl-button')
    ctrl_armed = ui_state()
    results['ctrlArmed'] = ctrl_armed
    assert ctrl_armed['ctrlPressed'] and ctrl_armed['activeIsTextarea'], ctrl_armed
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
    tap('.escape-button')
    assert ui_state()['activeIsTextarea'], ui_state()
    terminal_tap()
    press_enter()
    time.sleep(0.2)
    tap('.ctrl-button')
    assert ui_state()['ctrlPressed'] and ui_state()['activeIsTextarea'], ui_state()
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
    tap('.fullscreen-button')
    time.sleep(0.4)
    full_on = ui_state()
    results['fullscreenEnter'] = full_on
    assert full_on['fullscreen'] and full_on['activeIsTextarea'], full_on
    tap('.fullscreen-button')
    time.sleep(0.4)
    full_off = ui_state()
    results['fullscreenExit'] = full_off
    assert not full_off['fullscreen'] and full_off['activeIsTextarea'], full_off

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
