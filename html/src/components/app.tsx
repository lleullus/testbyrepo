import { h, Component } from 'preact';

import { Terminal } from './terminal';

import type { ITerminalOptions, ITheme } from '@xterm/xterm';
import type { ClientOptions, FlowControl } from './terminal/xterm';

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const path = window.location.pathname.replace(/[/]+$/, '');
const resumeId = Array.from(window.crypto.getRandomValues(new Uint8Array(16)), byte =>
    byte.toString(16).padStart(2, '0')
).join('');
const wsParams = new URLSearchParams(window.location.search);
wsParams.set('resume', resumeId);
const wsUrl = [protocol, '//', window.location.host, path, '/ws?', wsParams.toString()].join('');
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
        foreground: '#333333',
        background: '#ffffff',
        cursor: '#333333',
        cursorAccent: '#ffffff',
        selectionBackground: '#add6ff',
        black: '#000000',
        red: '#cd3131',
        green: '#107c10',
        yellow: '#949800',
        blue: '#0451a5',
        magenta: '#bc05bc',
        cyan: '#0598bc',
        white: '#555555',
        brightBlack: '#666666',
        brightRed: '#cd3131',
        brightGreen: '#14ce14',
        brightYellow: '#b5ba00',
        brightBlue: '#0451a5',
        brightMagenta: '#bc05bc',
        brightCyan: '#0598bc',
        brightWhite: '#a5a5a5',
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
                wsUrl={wsUrl}
                tokenUrl={tokenUrl}
                clientOptions={clientOptions}
                termOptions={termOptions}
                flowControl={flowControl}
            />
        );
    }
}
