import { h, Component } from 'preact';

import { Terminal } from './terminal';

import type { ITerminalOptions, ITheme } from '@xterm/xterm';
import type { ClientOptions, FlowControl, SessionBinding, SessionRequest } from './terminal/xterm';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const path = window.location.pathname.replace(/[/]+$/, '');
const endpoint = `${window.location.origin}${path}`;
const sessionKey = `webterm.session.v2:${endpoint}`;
const validSessionId = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{32}$/i.test(value);
const validToken = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
const randomSessionId = () =>
    Array.from(window.crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');

type StoredBindingV2 = {
    version: 2;
    id: string;
    clientInstanceId: string;
    state: 'pending-create' | 'approved';
    connectSequence: number;
    successorToken?: string;
    leaseEpoch?: number;
    inFlight?: { intent: 'create' | 'resume'; connectSequence: number };
};

let storedBinding: StoredBindingV2 | undefined;
try {
    const stored = window.sessionStorage.getItem(sessionKey);
    if (stored !== null) {
        const parsed = JSON.parse(stored) as StoredBindingV2;
        if (
            parsed.version === 2 &&
            validSessionId(parsed.id) &&
            validSessionId(parsed.clientInstanceId) &&
            Number.isSafeInteger(parsed.connectSequence) &&
            parsed.connectSequence >= 0 &&
            ((parsed.state === 'approved' && validToken(parsed.successorToken)) || parsed.state === 'pending-create')
        )
            storedBinding = parsed;
        else window.sessionStorage.removeItem(sessionKey);
    }
} catch {
    storedBinding = undefined;
}

const persist = (binding: StoredBindingV2) => {
    try {
        window.sessionStorage.setItem(sessionKey, JSON.stringify(binding));
        return true;
    } catch {
        return false;
    }
};

const requestFrom = (binding: StoredBindingV2, intent: 'create' | 'resume', sequence: number): SessionRequest => ({
    id: binding.id,
    intent,
    clientInstanceId: binding.clientInstanceId,
    connectSequence: sequence,
    successorToken: binding.successorToken,
    leaseEpoch: binding.leaseEpoch,
    persisted: true,
});

let currentSession: SessionRequest | undefined;
if (storedBinding) {
    const intent = storedBinding.state === 'approved' ? 'resume' : 'create';
    const sequence = storedBinding.inFlight?.connectSequence ?? storedBinding.connectSequence + 1;
    storedBinding.inFlight = { intent, connectSequence: sequence };
    const persisted = persist(storedBinding);
    currentSession = requestFrom(storedBinding, intent, sequence);
    currentSession.persisted = persisted;
}

const session = {
    current: currentSession,
    create() {
        const binding: StoredBindingV2 = {
            version: 2,
            id: randomSessionId(),
            clientInstanceId: randomSessionId(),
            state: 'pending-create',
            connectSequence: 0,
            inFlight: { intent: 'create', connectSequence: 1 },
        };
        storedBinding = binding;
        const request = requestFrom(binding, 'create', 1);
        request.persisted = persist(binding);
        this.current = request;
        return request;
    },
    begin(request: SessionRequest, fresh: boolean) {
        const binding = storedBinding;
        if (!binding || binding.id !== request.id || binding.clientInstanceId !== request.clientInstanceId)
            return request;
        if (!fresh) return request;
        const sequence = Math.max(binding.connectSequence, binding.inFlight?.connectSequence ?? 0) + 1;
        binding.inFlight = { intent: request.intent, connectSequence: sequence };
        const next = { ...request, connectSequence: sequence, persisted: persist(binding) };
        this.current = next;
        return next;
    },
    commitReady(request: SessionRequest, successorToken: string, leaseEpoch: number) {
        const binding = storedBinding;
        if (!binding || binding.id !== request.id || !validToken(successorToken)) return false;
        binding.state = 'approved';
        binding.connectSequence = request.connectSequence;
        binding.successorToken = successorToken;
        binding.leaseEpoch = leaseEpoch;
        delete binding.inFlight;
        const persisted = persist(binding);
        request.intent = 'resume';
        request.successorToken = successorToken;
        request.leaseEpoch = leaseEpoch;
        request.persisted = persisted;
        this.current = request;
        return persisted;
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
