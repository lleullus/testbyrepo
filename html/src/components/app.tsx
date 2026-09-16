import { h, Component } from 'preact';

import { Terminal } from './terminal';

import type { ITerminalOptions, ITheme } from '@xterm/xterm';
import type { ClientOptions, FlowControl, SessionBinding, SessionRequest } from './terminal/xterm';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const path = window.location.pathname.replace(/[/]+$/, '');
const endpoint = `${window.location.origin}${path}`;
const sessionKey = `webterm.session.v1:${endpoint}`;
const validSessionId = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{32}$/i.test(value);
const randomSessionId = () =>
    Array.from(window.crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');

let currentSession: SessionRequest | undefined;
try {
    const stored = window.sessionStorage.getItem(sessionKey);
    if (stored !== null) {
        const parsed = JSON.parse(stored) as { version?: unknown; id?: unknown };
        if (parsed.version === 1 && validSessionId(parsed.id)) {
            currentSession = { id: parsed.id, intent: 'resume', persisted: true };
        } else {
            window.sessionStorage.removeItem(sessionKey);
        }
    }
} catch {
    currentSession = undefined;
}

const session = {
    current: currentSession,
    create() {
        const request: SessionRequest = { id: randomSessionId(), intent: 'create', persisted: false };
        try {
            window.sessionStorage.setItem(sessionKey, JSON.stringify({ version: 1, id: request.id }));
            request.persisted = true;
        } catch {
            request.persisted = false;
        }
        this.current = request;
        return request;
    },
    markCreated(request: SessionRequest) {
        request.intent = 'resume';
        this.current = request;
    },
} as SessionBinding;

const wsParams = new URLSearchParams(window.location.search);
wsParams.delete('resume');
const wsQuery = wsParams.toString();
const wsBaseUrl = [protocol, '//', window.location.host, path, '/ws', wsQuery ? `?${wsQuery}` : ''].join('');
const tokenUrl = [window.location.protocol, '//', window.location.host, path, '/token'].join('');
const clientOptions = {
    rendererType: 'webgl',
    disableLeaveAlert: false,
    disableResizeOverlay: false,
    enableZmodem: false,
    enableTrzsz: false,
    enableSixel: false,
    isWindows: false,
    unicodeVersion: '11',
} as ClientOptions;
const termOptions = {
    fontSize: 13,
    fontFamily: 'Consolas,Liberation Mono,Menlo,Courier,monospace',
    theme: {
        foreground: '#d2d2d2',
        background: '#2b2b2b',
        cursor: '#adadad',
        black: '#000000',
        red: '#d81e00',
        green: '#5ea702',
        yellow: '#cfae00',
        blue: '#427ab3',
        magenta: '#89658e',
        cyan: '#00a7aa',
        white: '#dbded8',
        brightBlack: '#686a66',
        brightRed: '#f54235',
        brightGreen: '#99e343',
        brightYellow: '#fdeb61',
        brightBlue: '#84b0d8',
        brightMagenta: '#bc94b7',
        brightCyan: '#37e6e8',
        brightWhite: '#f1f1f0',
    } as ITheme,
    allowProposedApi: true,
} as ITerminalOptions;
const flowControl = {
    limit: 100000,
    highWater: 10,
    lowWater: 4,
} as FlowControl;

export class App extends Component {
    render() {
        return (
            <Terminal
                id="terminal-container"
                wsBaseUrl={wsBaseUrl}
                tokenUrl={tokenUrl}
                session={session}
                clientOptions={clientOptions}
                termOptions={termOptions}
                flowControl={flowControl}
            />
        );
    }
}
