import { bind } from 'decko';
import type { IDisposable, ITerminalOptions } from '@xterm/xterm';
import { Terminal } from '@xterm/xterm';
import { WebglAddon } from '@xterm/addon-webgl';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { ImageAddon } from '@xterm/addon-image';
import { Unicode11Addon } from '@xterm/addon-unicode11';
import { OverlayAddon } from './addons/overlay';
import { ZmodemAddon } from './addons/zmodem';

import '@xterm/xterm/css/xterm.css';

const TEXTAREA_CONTEXT_LIMIT = 64;

interface TtydTerminal extends Terminal {
    fit(): void;
}

export type InputModifier = 'none' | 'shift' | 'ctrl';

export interface InputOwnerSnapshot {
    modifier: InputModifier;
    focusIntent: 'inactive' | 'typing';
    composing: boolean;
    inputEpoch: number;
}

interface HandledDomReplay {
    offset: number;
    text: string;
}

interface CompositionTransaction {
    sequence: number;
    inputEpoch: number;
    connectionGeneration: number;
    serverConnectionGeneration: number;
    beforeValue: string;
    start: number;
    end: number;
    handledDomReplay?: HandledDomReplay;
    handledTextareaTail: string;
    compositionData: string;
    inputData: string;
    lastData: string;
    draft: string;
    cancelled: boolean;
    ended: boolean;
}

interface PhysicalKeyAction {
    inputEpoch: number;
    connectionGeneration: number;
    serverConnectionGeneration: number;
    inputType: 'insertText' | 'insertLineBreak';
    expectedTerminalText: string;
    key: string;
    code: string;
    terminalText?: string;
    released?: boolean;
}

interface TextInputTransaction {
    inputEpoch: number;
    beforeValue: string;
    inputType: string;
    data: string | null;
}

interface PointerCandidate {
    pointerId: number;
    x: number;
    y: number;
    selection: string;
}

interface TtydDiagnosticEvent {
    at: number;
    event: string;
    value?: number;
}

export interface TtydDiagnosticsSnapshot {
    state:
        | 'no-session'
        | 'connecting'
        | 'connected'
        | 'replaying'
        | 'checking-owner'
        | 'application-ready'
        | 'render-lagging'
        | 'terminal-state-lost'
        | 'session-conflict'
        | 'session-expired'
        | 'session-exited'
        | 'session-unknown'
        | 'session-exited-retained'
        | 'session-rejected-capacity'
        | 'session-error'
        | 'takeover-pending'
        | 'session-displaced'
        | 'session-stale'
        | 'disconnected';
    connectionGeneration: number;
    serverConnectionGeneration: number;
    terminalEpoch: number;
    sessionDiagnosticId: number;
    appliedPosition: number;
    replayTarget: number;
    inputReady: boolean;
    inputEpoch: number;
    inputModifier: InputModifier;
    focusIntent: 'inactive' | 'typing';
    composing: boolean;
    connectInFlight: boolean;
    heartbeatOutstanding: boolean;
    pendingBytes: number;
    pendingAgeMs: number;
    pendingBytesHighWater: number;
    socketBufferedAmount: number;
    parserCallbacks: number;
    renderEvents: number;
    animationFrames: number;
    maxAnimationFrameGapMs: number;
    activeBuffer: 'normal' | 'alternate';
    mouseTrackingMode: string;
    visibility: DocumentVisibilityState;
    focused: boolean;
    geometryApplyCount: number;
    geometrySendCount: number;
    lastValidGeometry?: { cols: number; rows: number };
    events: readonly TtydDiagnosticEvent[];
}

declare global {
    interface Window {
        term: TtydTerminal;
        ttydDiagnostics?: () => TtydDiagnosticsSnapshot;
    }
}

enum Command {
    // server side
    OUTPUT = '0',
    SET_WINDOW_TITLE = '1',
    SET_PREFERENCES = '2',
    SET_SESSION_STATE = '3',
    REPLAY_END = '4',
    HEARTBEAT_REPLY = '5',

    // client side
    INPUT = '0',
    RESIZE_TERMINAL = '1',
    PAUSE = '2',
    RESUME = '3',
    HEARTBEAT = '4',
    SESSION_READY = '5',
    TAKEOVER = '6',
}
type Preferences = ITerminalOptions & ClientOptions;

export type RendererType = 'dom' | 'canvas' | 'webgl';

export interface ClientOptions {
    rendererType: RendererType;
    disableLeaveAlert: boolean;
    disableResizeOverlay: boolean;
    enableZmodem: boolean;
    enableTrzsz: boolean;
    enableSixel: boolean;
    titleFixed?: string;
    isWindows: boolean;
    trzszDragInitTimeout: number;
    unicodeVersion: string;
}

export interface FlowControl {
    limit: number;
    highWater: number;
    lowWater: number;
}

export interface SessionRequest {
    id: string;
    intent: 'create' | 'resume';
    persisted: boolean;
}

export interface SessionBinding {
    current?: SessionRequest;
    create(): SessionRequest;
    markCreated(request: SessionRequest): void;
}

export interface XtermOptions {
    wsBaseUrl: string;
    tokenUrl: string;
    session: SessionBinding;
    flowControl: FlowControl;
    clientOptions: ClientOptions;
    termOptions: ITerminalOptions;
}

function toDisposable(f: () => void): IDisposable {
    return { dispose: f };
}

function addEventListener(
    target: EventTarget,
    type: string,
    listener: EventListener,
    options?: boolean | AddEventListenerOptions
): IDisposable {
    target.addEventListener(type, listener, options);
    return toDisposable(() => target.removeEventListener(type, listener, options));
}

function createDeferred<T>() {
    let resolve!: (value?: T | PromiseLike<T>) => void;
    const promise = new Promise<T>(settle => {
        resolve = value => settle(value as T);
    });
    return { promise, resolve };
}

const RECONNECT_WINDOW_MS = 60_000;
const RECONNECT_MAX_DELAY_MS = 5_000;
const TOKEN_TIMEOUT_MS = 10_000;
const ATTEMPT_TIMEOUT_MS = 30_000;
const HEARTBEAT_INTERVAL_MS = 5_000;
const HEARTBEAT_TIMEOUT_MS = 30_000;

type AttemptResult = 'ready' | 'retry' | 'stop';

export class Xterm {
    private disposables: IDisposable[] = [];
    private socketDisposables: IDisposable[] = [];
    private textEncoder = new TextEncoder();
    private textDecoder = new TextDecoder();
    private pendingBytes = 0;
    private pendingSince = 0;
    private pendingBytesHighWater = 0;
    private flowPausedGeneration?: number;
    private connectionGeneration = 0;
    private serverConnectionGeneration = 0;
    private terminalEpoch = 0;
    private sessionDiagnosticId = 0;
    private appliedPosition = 0;
    private replayTarget = 0;
    private inputReady = false;
    private parserCallbacks = 0;
    private renderEvents = 0;
    private animationFrames = 0;
    private lastAnimationFrame = 0;
    private maxAnimationFrameGapMs = 0;
    private animationFrame?: number;
    private connectionState: TtydDiagnosticsSnapshot['state'] = 'disconnected';
    private isExitedRetained = false;
    private diagnosticEvents: TtydDiagnosticEvent[] = [];
    private diagnosticsEnabled = new URLSearchParams(window.location.search).get('diagnostics') === '1';
    private terminal!: Terminal;
    private fitAddon = new FitAddon();
    private overlayAddon = new OverlayAddon();
    private webglAddon?: WebglAddon;
    private fitFrame?: number;
    private terminalContainer?: HTMLElement;
    private lastValidGeometry?: { cols: number; rows: number };
    private lastSentGeometry?: { serverGeneration: number; cols: number; rows: number };
    private handshakeGeometry?: { connectionGeneration: number; cols: number; rows: number };
    private geometryApplyCount = 0;
    private geometrySendCount = 0;
    private zmodemAddon?: ZmodemAddon;

    private socket?: WebSocket;
    private token = '';
    private request?: SessionRequest;
    private title?: string;
    private titleFixed?: string;
    private resizeOverlay = true;
    private reconnect = true;
    private disposed = false;
    private preferencesApplied = false;
    private connectPromise?: Promise<void>;
    private attemptResolve?: (result: AttemptResult) => void;
    private fetchAbort?: AbortController;
    private reconnectStartedAt = 0;
    private reconnectAttempts = 0;
    private reconnectTimer?: number;
    private reconnectDelayResolve?: () => void;
    private attemptTimer?: number;
    private heartbeatTimer?: number;
    private heartbeatNonce?: string;
    private heartbeatSentAt = 0;
    private heartbeatCounter = 0;
    private automaticRecoveryExhausted = false;
    private consumeRecoveryClick = false;
    private displaced = false;
    private takeoverPending = false;
    private takeoverOwnerGeneration = 0;
    private inputModifier: InputModifier = 'none';
    private focusIntent: InputOwnerSnapshot['focusIntent'] = 'inactive';
    private inputEpoch = 0;
    private compositionSequence = 0;
    private composition?: CompositionTransaction;
    private discardedComposition?: CompositionTransaction;
    private pendingTextInput?: TextInputTransaction;
    private compositionTextareaStyle?: { width: string; height: string; lineHeight: string };
    private handledTextareaTail = '';
    private handledPhysicalKeyTail = '';
    private handledTextareaTailRequiresAnchor = false;
    private pointerCandidate?: PointerCandidate;
    private physicalKeyActions: PhysicalKeyAction[] = [];
    private toolbarInteraction = false;

    private writeFunc = (data: ArrayBuffer) => this.writeData(new Uint8Array(data));

    constructor(
        private options: XtermOptions,
        private sendCb: () => void,
        private inputStateCb: (snapshot: InputOwnerSnapshot) => void = () => undefined,
        private fontSizeCb: (fontSize: number) => void = () => undefined
    ) {
        this.request = options.session.current;
    }

    dispose() {
        this.disposed = true;
        this.invalidateInputOwner(true);
        this.connectionGeneration++;
        this.fetchAbort?.abort();
        this.fetchAbort = undefined;
        this.clearReconnectTimers();
        this.clearHeartbeat();
        this.clearSocket(true);
        if (this.animationFrame !== undefined) {
            window.cancelAnimationFrame(this.animationFrame);
            this.animationFrame = undefined;
        }
        if (this.fitFrame !== undefined) {
            window.cancelAnimationFrame(this.fitFrame);
            this.fitFrame = undefined;
        }
        for (const disposable of this.disposables) disposable.dispose();
        this.disposables.length = 0;
        this.overlayAddon.dispose();
        this.terminal?.dispose();
    }

    private recordDiagnostic(event: string, value?: number) {
        if (!this.diagnosticsEnabled) return;
        this.diagnosticEvents.push({ at: performance.now(), event, value });
        if (this.diagnosticEvents.length > 256) this.diagnosticEvents.splice(0, this.diagnosticEvents.length - 256);
    }

    private diagnosticsSnapshot(): TtydDiagnosticsSnapshot {
        const now = performance.now();
        return {
            state: this.connectionState,
            connectionGeneration: this.connectionGeneration,
            serverConnectionGeneration: this.serverConnectionGeneration,
            terminalEpoch: this.terminalEpoch,
            sessionDiagnosticId: this.sessionDiagnosticId,
            appliedPosition: this.appliedPosition,
            replayTarget: this.replayTarget,
            inputReady: this.inputReady,
            inputEpoch: this.inputEpoch,
            inputModifier: this.inputModifier,
            focusIntent: this.focusIntent,
            composing: this.composition !== undefined && !this.composition.cancelled,
            connectInFlight: this.connectPromise !== undefined,
            heartbeatOutstanding: this.heartbeatNonce !== undefined,
            pendingBytes: this.pendingBytes,
            pendingAgeMs: this.pendingSince === 0 ? 0 : now - this.pendingSince,
            pendingBytesHighWater: this.pendingBytesHighWater,
            socketBufferedAmount: this.socket?.bufferedAmount ?? 0,
            parserCallbacks: this.parserCallbacks,
            renderEvents: this.renderEvents,
            animationFrames: this.animationFrames,
            maxAnimationFrameGapMs: this.maxAnimationFrameGapMs,
            activeBuffer: this.terminal.buffer.active.type,
            mouseTrackingMode: this.terminal.modes.mouseTrackingMode,
            visibility: document.visibilityState,
            focused: document.hasFocus() && document.activeElement === this.terminal.textarea,
            geometryApplyCount: this.geometryApplyCount,
            geometrySendCount: this.geometrySendCount,
            lastValidGeometry: this.lastValidGeometry && { ...this.lastValidGeometry },
            events: this.diagnosticEvents.slice(),
        };
    }

    private monitorAnimationFrames = (now: number) => {
        if (!this.diagnosticsEnabled) {
            this.animationFrame = undefined;
            return;
        }
        if (this.lastAnimationFrame !== 0)
            this.maxAnimationFrameGapMs = Math.max(this.maxAnimationFrameGapMs, now - this.lastAnimationFrame);
        this.lastAnimationFrame = now;
        this.animationFrames++;
        this.animationFrame = window.requestAnimationFrame(this.monitorAnimationFrames);
    };

    private flowThresholds() {
        const { limit, highWater, lowWater } = this.options.flowControl;
        return {
            high: Math.max(1, limit) * Math.max(1, highWater),
            low: Math.max(0, limit) * Math.max(0, lowWater),
        };
    }

    private sendFlowControl(command: Command.PAUSE | Command.RESUME) {
        const socket = this.socket;
        if (socket?.readyState !== WebSocket.OPEN) return;
        if (command === Command.PAUSE) {
            if (this.flowPausedGeneration === this.connectionGeneration) return;
            this.flowPausedGeneration = this.connectionGeneration;
        } else {
            if (this.flowPausedGeneration !== this.connectionGeneration) return;
            this.flowPausedGeneration = undefined;
        }
        socket.send(this.textEncoder.encode(command));
        this.recordDiagnostic(command === Command.PAUSE ? 'flow-pause' : 'flow-resume', this.pendingBytes);
    }

    @bind
    private register<T extends IDisposable>(d: T): T {
        this.disposables.push(d);
        return d;
    }

    @bind
    public sendFile(files: FileList) {
        this.zmodemAddon?.sendFile(files);
    }

    public blur() {
        this.terminal?.blur();
    }

    private inputSnapshot(): InputOwnerSnapshot {
        return {
            modifier: this.inputModifier,
            focusIntent: this.focusIntent,
            composing: this.composition !== undefined && !this.composition.cancelled,
            inputEpoch: this.inputEpoch,
        };
    }

    private emitInputState() {
        this.inputStateCb(this.inputSnapshot());
    }

    private setModifier(modifier: InputModifier) {
        if (this.inputModifier === modifier) return;
        this.inputModifier = modifier;
        this.emitInputState();
    }

    public toggleShift() {
        this.setModifier(this.inputModifier === 'shift' ? 'none' : 'shift');
    }

    public toggleCtrl() {
        this.setModifier(this.inputModifier === 'ctrl' ? 'none' : 'ctrl');
    }

    public clearModifierForLocalAction() {
        this.setModifier('none');
    }

    public beginToolbarInteraction() {
        this.toolbarInteraction = true;
    }

    public endToolbarInteraction() {
        window.setTimeout(() => {
            if (this.focusIntent === 'typing' && document.activeElement !== this.terminal.textarea)
                this.terminal.focus();
            this.toolbarInteraction = false;
        }, 500);
    }

    private setFocusIntent(focusIntent: InputOwnerSnapshot['focusIntent']) {
        if (this.focusIntent === focusIntent) return;
        this.focusIntent = focusIntent;
        this.emitInputState();
    }

    private activateTypingFocus() {
        if (!this.inputReady || this.displaced) return;
        if (this.inputModifier === 'shift') this.setModifier('none');
        this.discardedComposition = undefined;
        this.setFocusIntent('typing');
        this.terminal.focus();
    }

    private invalidateInputOwner(blur: boolean) {
        if (blur) {
            this.clearHandledTextareaContext();
        } else {
            // A browser/IME layout switch may blur and immediately refocus the textarea. Keep the
            // sent tail only for an exact DOM anchor match; never use it as an unanchored prefix.
            this.handledTextareaTailRequiresAnchor = true;
        }
        this.inputEpoch++;
        this.pendingTextInput = undefined;
        this.pointerCandidate = undefined;
        this.physicalKeyActions.length = 0;
        if (this.composition) {
            this.composition.cancelled = true;
            this.discardedComposition = this.composition;
            this.composition = undefined;
        }
        this.clearLocalPreedit();
        this.resetOwnedTextarea();
        this.inputModifier = 'none';
        this.focusIntent = 'inactive';
        if (blur) this.terminal?.blur();
        this.emitInputState();
    }

    private renderLocalPreedit(text: string) {
        const textarea = this.terminal.textarea;
        const view = this.terminal.element?.querySelector<HTMLElement>('.composition-view');
        if (!textarea || !view) return;
        if (!this.compositionTextareaStyle) {
            this.compositionTextareaStyle = {
                width: textarea.style.width,
                height: textarea.style.height,
                lineHeight: textarea.style.lineHeight,
            };
        }
        view.textContent = text;
        view.style.left = textarea.style.left;
        view.style.top = textarea.style.top;
        view.style.height = textarea.style.height;
        view.style.lineHeight = textarea.style.lineHeight;
        view.style.fontFamily = this.terminal.options.fontFamily ?? '';
        view.style.fontSize = `${this.terminal.options.fontSize ?? 15}px`;
        view.classList.add('active');
        const bounds = view.getBoundingClientRect();
        textarea.style.width = `${Math.max(bounds.width, 1)}px`;
        textarea.style.height = `${Math.max(bounds.height, 1)}px`;
        textarea.style.lineHeight = `${Math.max(bounds.height, 1)}px`;
    }

    private clearLocalPreedit() {
        const view = this.terminal?.element?.querySelector<HTMLElement>('.composition-view');
        if (view) {
            view.classList.remove('active');
            view.textContent = '';
        }
        const textarea = this.terminal?.textarea;
        if (textarea && this.compositionTextareaStyle) {
            textarea.style.width = this.compositionTextareaStyle.width;
            textarea.style.height = this.compositionTextareaStyle.height;
            textarea.style.lineHeight = this.compositionTextareaStyle.lineHeight;
        }
        this.compositionTextareaStyle = undefined;
    }

    private resetOwnedTextarea() {
        const textarea = this.terminal?.textarea;
        if (!textarea) return;
        textarea.value = '';
        textarea.setSelectionRange(0, 0);
    }

    private rememberHandledTextareaText(text: string, physical = false) {
        if (/[^\x20-\x7e\u0080-\uffff]/.test(text)) {
            this.clearHandledTextareaContext();
            return;
        }
        const retainedTail = this.handledTextareaTailRequiresAnchor ? '' : this.handledTextareaTail;
        this.handledTextareaTail = (retainedTail + text).slice(-TEXTAREA_CONTEXT_LIMIT);
        this.handledTextareaTailRequiresAnchor = false;
        this.handledPhysicalKeyTail = physical
            ? (this.handledPhysicalKeyTail + text).slice(-TEXTAREA_CONTEXT_LIMIT)
            : '';
    }

    private clearHandledTextareaContext() {
        this.handledTextareaTail = '';
        this.handledTextareaTailRequiresAnchor = false;
        this.handledPhysicalKeyTail = '';
    }

    private replayedPrefixLength(text: string, handledTail: string): number {
        const maximum = Math.min(Math.max(0, text.length - 1), handledTail.length);
        for (let length = maximum; length > 0; length--) {
            if (text.startsWith(handledTail.slice(-length))) return length;
        }
        return 0;
    }

    private findHandledDomReplay(
        beforeValue: string,
        start: number,
        handledTail: string
    ): HandledDomReplay | undefined {
        // Android hardware IMEs can restore already-sent terminal text into xterm's hidden textarea
        // immediately before starting composition. Treat only an exact tail match at the caret as replay.
        const maximum = Math.min(start, handledTail.length);
        for (let length = maximum; length > 0; length--) {
            const text = handledTail.slice(-length);
            const offset = start - length;
            if (beforeValue.slice(offset, start) === text) return { offset, text };
        }
        return undefined;
    }

    private removeHandledDomReplay(value: string, replay?: HandledDomReplay) {
        if (!replay || !value.startsWith(replay.text, replay.offset)) return value;
        return value.slice(0, replay.offset) + value.slice(replay.offset + replay.text.length);
    }

    private cancelComposition() {
        const transaction = this.composition;
        if (!transaction) return false;
        transaction.cancelled = true;
        this.composition = undefined;
        this.discardedComposition = transaction;
        this.resetOwnedTextarea();
        this.clearLocalPreedit();
        this.emitInputState();
        return true;
    }

    private compositionText(transaction: CompositionTransaction, eventData = ''): string {
        const rawCurrent = this.terminal.textarea?.value ?? transaction.beforeValue;
        const current = this.removeHandledDomReplay(rawCurrent, transaction.handledDomReplay);
        const before = transaction.beforeValue;
        const beforePrefix = before.slice(0, transaction.start);
        const beforeSuffix = before.slice(transaction.end);
        const anchored = beforePrefix.length > 0 || beforeSuffix.length > 0;
        const reportedComposition =
            eventData || transaction.compositionData || transaction.inputData || transaction.lastData;
        let inserted: string;
        if (
            current.startsWith(beforePrefix) &&
            current.endsWith(beforeSuffix) &&
            current.length >= beforePrefix.length + beforeSuffix.length
        ) {
            inserted = current.slice(beforePrefix.length, current.length - beforeSuffix.length);
        } else {
            let prefix = 0;
            while (prefix < before.length && prefix < current.length && before[prefix] === current[prefix]) prefix++;
            let suffix = 0;
            while (
                suffix < before.length - prefix &&
                suffix < current.length - prefix &&
                before[before.length - 1 - suffix] === current[current.length - 1 - suffix]
            )
                suffix++;
            inserted = current.slice(prefix, current.length - suffix);
        }
        let result = inserted || reportedComposition;
        const replayContext = transaction.handledDomReplay?.text || (!anchored ? transaction.handledTextareaTail : '');
        if (result && replayContext) {
            const replayedLength = this.replayedPrefixLength(result, replayContext);
            if (replayedLength > 0) {
                const replayedText = result.slice(0, replayedLength);
                const remainder = result.slice(replayedLength);
                const anchoredReplayIsProven =
                    !transaction.handledDomReplay ||
                    (reportedComposition.length > 0 && remainder === reportedComposition) ||
                    (/^[\x20-\x7e]+$/.test(replayedText) && /[\u0080-\uffff]/.test(remainder));
                if (anchoredReplayIsProven) result = remainder;
            }
        }
        return result;
    }

    private settleComposition(eventData = '') {
        const transaction = this.composition;
        if (!transaction) return false;
        const text = this.compositionText(transaction, eventData);
        this.composition = undefined;
        this.pendingTextInput = undefined;
        this.physicalKeyActions = this.physicalKeyActions.filter(
            action =>
                action.inputEpoch !== transaction.inputEpoch ||
                action.connectionGeneration !== transaction.connectionGeneration ||
                action.serverConnectionGeneration !== transaction.serverConnectionGeneration
        );
        this.clearLocalPreedit();
        this.resetOwnedTextarea();
        const valid =
            !transaction.cancelled &&
            transaction.inputEpoch === this.inputEpoch &&
            transaction.connectionGeneration === this.connectionGeneration &&
            transaction.serverConnectionGeneration === this.serverConnectionGeneration;
        if (valid && text && this.sendData(text)) this.rememberHandledTextareaText(text);
        this.emitInputState();
        return true;
    }

    private sendPlainText(text: string, physical = false) {
        const modifier = this.inputModifier;
        this.setModifier('none');
        const outbound =
            modifier === 'ctrl' && /^[a-zA-Z]$/.test(text)
                ? String.fromCharCode(text.toUpperCase().charCodeAt(0) - 64)
                : text;
        if (this.sendData(outbound)) this.rememberHandledTextareaText(text, physical);
    }

    private beginPhysicalKeyAction(event: KeyboardEvent) {
        if (event.isComposing || event.keyCode === 229) return;
        const inputType = event.key === 'Enter' ? 'insertLineBreak' : event.key.length === 1 ? 'insertText' : undefined;
        if (!inputType) return;
        if (this.physicalKeyActions.length >= 16) this.physicalKeyActions.splice(0, 1);
        this.physicalKeyActions.push({
            inputEpoch: this.inputEpoch,
            connectionGeneration: this.connectionGeneration,
            serverConnectionGeneration: this.serverConnectionGeneration,
            inputType,
            expectedTerminalText: inputType === 'insertLineBreak' ? '\r' : event.key,
            key: event.key,
            code: event.code,
        });
    }

    private rememberTerminalData(data: string) {
        for (const action of this.physicalKeyActions) {
            if (
                action.terminalText === undefined &&
                action.inputEpoch === this.inputEpoch &&
                action.connectionGeneration === this.connectionGeneration &&
                action.serverConnectionGeneration === this.serverConnectionGeneration &&
                action.expectedTerminalText === data
            ) {
                action.terminalText = data;
                return true;
            }
        }
        return false;
    }

    private consumePhysicalKeyEchoes(inputType: string, text: string) {
        const textInsertion =
            inputType === 'insertText' ||
            inputType === 'insertReplacementText' ||
            inputType === 'insertCompositionText' ||
            inputType === 'insertFromComposition';
        const lineBreak = inputType === 'insertLineBreak';
        if (!textInsertion && !lineBreak) return { text, echo: false, lineBreak: false };
        let remaining = text;
        let echo = false;
        while (true) {
            const index = this.physicalKeyActions.findIndex(
                action =>
                    action.inputEpoch === this.inputEpoch &&
                    action.connectionGeneration === this.connectionGeneration &&
                    action.serverConnectionGeneration === this.serverConnectionGeneration &&
                    action.terminalText !== undefined &&
                    (lineBreak ? action.inputType === 'insertLineBreak' : action.inputType === 'insertText')
            );
            if (index === -1) break;
            const action = this.physicalKeyActions[index];
            if (lineBreak) {
                this.physicalKeyActions.splice(index, 1);
                return { text: remaining, echo: true, lineBreak: action.terminalText === '\r' };
            }
            if (!remaining.startsWith(action.terminalText!)) break;
            remaining = remaining.slice(action.terminalText!.length);
            this.physicalKeyActions.splice(index, 1);
            echo = true;
        }
        return { text: remaining, echo, lineBreak: false };
    }

    private ownsTextInput(event: InputEvent) {
        return (
            event.isComposing ||
            event.inputType.includes('Composition') ||
            event.inputType === 'insertText' ||
            event.inputType === 'insertReplacementText' ||
            event.inputType === 'insertLineBreak' ||
            event.inputType === 'deleteContentBackward' ||
            event.inputType === 'deleteContentForward'
        );
    }

    private handleCompositionStart = (event: CompositionEvent) => {
        event.stopImmediatePropagation();
        if (this.composition?.ended) this.settleComposition(this.composition.lastData);
        else if (this.composition) this.cancelComposition();
        this.setModifier('none');
        this.pendingTextInput = undefined;
        this.physicalKeyActions = this.physicalKeyActions.filter(action => action.terminalText !== undefined);
        this.discardedComposition = undefined;
        const textarea = this.terminal.textarea;
        const rawBeforeValue = textarea?.value ?? '';
        const rawStart = textarea?.selectionStart ?? rawBeforeValue.length;
        const rawEnd = textarea?.selectionEnd ?? rawStart;
        const handledDomReplay = this.findHandledDomReplay(rawBeforeValue, rawStart, this.handledPhysicalKeyTail);
        const unanchoredHandledTextareaTail = this.handledTextareaTailRequiresAnchor ? '' : this.handledTextareaTail;
        const removedLength = handledDomReplay?.text.length ?? 0;
        const beforeValue = this.removeHandledDomReplay(rawBeforeValue, handledDomReplay);
        const start = rawStart - removedLength;
        const end = rawEnd - removedLength;
        this.composition = {
            sequence: ++this.compositionSequence,
            inputEpoch: this.inputEpoch,
            connectionGeneration: this.connectionGeneration,
            serverConnectionGeneration: this.serverConnectionGeneration,
            beforeValue,
            start,
            end,
            handledDomReplay,
            handledTextareaTail: unanchoredHandledTextareaTail,
            compositionData: event.data,
            inputData: '',
            lastData: event.data,
            draft: event.data,
            cancelled: false,
            ended: false,
        };
        this.renderLocalPreedit(event.data);
        this.emitInputState();
    };

    private handleCompositionUpdate = (event: CompositionEvent) => {
        event.stopImmediatePropagation();
        if (!this.composition) return;
        this.composition.lastData = event.data;
        this.composition.compositionData = event.data;
        this.composition.draft = event.data;
        this.renderLocalPreedit(event.data);
    };

    private handleCompositionEnd = (event: CompositionEvent) => {
        event.stopImmediatePropagation();
        const transaction = this.composition;
        if (!transaction) return;
        transaction.lastData = event.data || transaction.lastData;
        if (event.data) transaction.compositionData = event.data;
        transaction.ended = true;
        const sequence = transaction.sequence;
        window.setTimeout(() => {
            if (this.composition?.sequence === sequence)
                this.settleComposition(event.data || transaction.compositionData);
        }, 0);
    };

    private handleBeforeInput = (event: InputEvent) => {
        if (!this.ownsTextInput(event) && !this.composition) return;
        event.stopImmediatePropagation();
        if (this.composition) {
            if ((event.isComposing || event.inputType.includes('Composition')) && event.data !== null) {
                this.composition.inputData = event.data;
                this.composition.lastData = event.data;
                this.composition.draft = event.data;
                this.renderLocalPreedit(event.data);
            }
            return;
        }
        if (this.discardedComposition && (event.isComposing || event.inputType.includes('Composition'))) return;
        this.discardedComposition = undefined;
        this.resetOwnedTextarea();
        this.pendingTextInput = {
            inputEpoch: this.inputEpoch,
            beforeValue: this.terminal.textarea?.value ?? '',
            inputType: event.inputType,
            data: event.data,
        };
    };

    private handleInput = (event: InputEvent) => {
        if (!this.ownsTextInput(event) && !this.composition && !this.discardedComposition) return;
        event.stopImmediatePropagation();
        if (this.composition) {
            const transaction = this.composition;
            const previousDraft = transaction.draft;
            if (event.data !== null) transaction.inputData = event.data;
            if (event.data) transaction.lastData = event.data;
            const candidate = this.compositionText(transaction);
            const physical = this.consumePhysicalKeyEchoes(event.inputType, candidate);
            if (physical.echo) {
                const consumed = candidate.slice(0, candidate.length - physical.text.length);
                if (!transaction.handledDomReplay && consumed) {
                    transaction.handledDomReplay = { offset: transaction.start, text: consumed };
                }
                if (!physical.text) {
                    transaction.inputData = transaction.compositionData;
                    transaction.lastData = transaction.compositionData;
                }
            }
            transaction.draft = physical.text;
            this.renderLocalPreedit(transaction.draft);
            if (
                physical.echo &&
                physical.text === '' &&
                previousDraft === '' &&
                !event.isComposing &&
                !event.inputType.includes('Composition')
            )
                return;
            if (!event.isComposing && !event.inputType.includes('Composition')) this.settleComposition();
            return;
        }
        if (this.discardedComposition) {
            this.discardedComposition = undefined;
            this.resetOwnedTextarea();
            return;
        }
        const transaction = this.pendingTextInput;
        this.pendingTextInput = undefined;
        if (!transaction || transaction.inputEpoch !== this.inputEpoch) {
            this.resetOwnedTextarea();
            return;
        }
        const text = this.terminal.textarea?.value || event.data || transaction.data || '';
        const physical = this.consumePhysicalKeyEchoes(transaction.inputType, text);
        this.resetOwnedTextarea();
        if (transaction.inputType === 'insertLineBreak') {
            this.setModifier('none');
            this.clearHandledTextareaContext();
            if (!physical.lineBreak) this.sendData('\r');
            return;
        }
        if (transaction.inputType === 'deleteContentBackward') {
            this.setModifier('none');
            this.clearHandledTextareaContext();
            this.sendData('\x7f');
            return;
        }
        if (transaction.inputType === 'deleteContentForward') {
            this.setModifier('none');
            this.clearHandledTextareaContext();
            this.sendData('\x1b[3~');
            return;
        }
        if (physical.text) this.sendPlainText(physical.text);
    };

    private handlePaste = (event: ClipboardEvent) => {
        const text = event.clipboardData?.getData('text/plain');
        if (text === undefined) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        this.setModifier('none');
        if (this.composition) this.cancelComposition();
        this.pendingTextInput = undefined;
        this.physicalKeyActions.length = 0;
        this.resetOwnedTextarea();
        this.terminal.paste(text);
    };

    private handleInputKeyDown = (event: KeyboardEvent) => {
        if (this.composition?.ended) this.settleComposition(this.composition.lastData);
        if (this.composition) {
            event.stopImmediatePropagation();
            if (event.key === 'Escape') {
                event.preventDefault();
                this.setModifier('none');
                this.cancelComposition();
            }
            return;
        }
        if (event.keyCode === 229) {
            event.stopImmediatePropagation();
            return;
        }
        this.discardedComposition = undefined;
        this.pendingTextInput = undefined;
        if (event.key === 'Enter' || event.key === 'Escape') this.setModifier('none');
        this.beginPhysicalKeyAction(event);
    };

    private handleInputKeyUp = (event: KeyboardEvent) => {
        for (let index = this.physicalKeyActions.length - 1; index >= 0; index--) {
            const action = this.physicalKeyActions[index];
            if (action.released || (action.code !== event.code && action.key !== event.key)) continue;
            if (action.terminalText === undefined) {
                this.physicalKeyActions.splice(index, 1);
            } else {
                action.released = true;
                window.setTimeout(() => {
                    const staleIndex = this.physicalKeyActions.indexOf(action);
                    if (staleIndex !== -1) this.physicalKeyActions.splice(staleIndex, 1);
                }, 2000);
            }
            return;
        }
    };

    private isDirectInputTarget(target: EventTarget | null) {
        return target instanceof Element && !target.closest('a,button,input,select,[role="button"],.terminal-overlay');
    }

    private handleTerminalPointerDown = (event: PointerEvent) => {
        if (event.target instanceof Element && event.target.closest('.terminal-overlay')) return;
        if (this.claimRecoveryPointer(event)) return;
        if (
            event.pointerType !== 'touch' &&
            (!event.isPrimary || event.button !== 0 || !this.isDirectInputTarget(event.target))
        ) {
            this.pointerCandidate = undefined;
            return;
        }
        this.pointerCandidate = {
            pointerId: event.pointerId,
            x: event.clientX,
            y: event.clientY,
            selection: this.terminal.getSelection(),
        };
    };

    private handleTerminalPointerMove = (event: PointerEvent) => {
        const candidate = this.pointerCandidate;
        if (!candidate || candidate.pointerId !== event.pointerId) return;
        if (Math.hypot(event.clientX - candidate.x, event.clientY - candidate.y) > 8) this.pointerCandidate = undefined;
    };

    private handleTerminalPointerUp = (event: PointerEvent) => {
        const candidate = this.pointerCandidate;
        this.pointerCandidate = undefined;
        if (this.consumeRecoveryClick)
            window.setTimeout(() => {
                this.consumeRecoveryClick = false;
            }, 0);
        if (
            !candidate ||
            candidate.pointerId !== event.pointerId ||
            !this.isDirectInputTarget(event.target) ||
            this.terminal.getSelection() !== candidate.selection
        )
            return;
        this.activateTypingFocus();
    };

    private handleTerminalPointerCancel = () => {
        this.pointerCandidate = undefined;
    };

    public fit() {
        if (!this.terminal || this.fitFrame !== undefined) return;
        this.fitFrame = window.requestAnimationFrame(() => {
            this.fitFrame = undefined;
            if (!this.terminalContainer || document.visibilityState === 'hidden') return;
            const rect = this.terminalContainer.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return;
            this.fitAddon.fit();
            const { cols, rows } = this.terminal;
            if (!Number.isInteger(cols) || !Number.isInteger(rows) || cols <= 0 || rows <= 0) return;
            const previous = this.lastValidGeometry;
            this.lastValidGeometry = { cols, rows };
            if (!previous || previous.cols !== cols || previous.rows !== rows) this.geometryApplyCount++;
            this.sendCurrentGeometry();
        });
    }

    public setFontSize(fontSize: number) {
        if (!this.terminal) return;
        const normalized = Math.min(32, Math.max(8, Math.round(fontSize)));
        this.fontSizeCb(normalized);
        if (this.terminal.options.fontSize === normalized) return;
        this.terminal.options.fontSize = normalized;
        this.fit();
    }

    public sendEscape() {
        this.clearHandledTextareaContext();
        this.setModifier('none');
        if (this.cancelComposition()) return;
        this.sendData('\x1b');
    }

    public sendTab() {
        this.clearHandledTextareaContext();
        const shifted = this.inputModifier === 'shift';
        this.setModifier('none');
        this.sendData(shifted ? '\x1b[Z' : '\t');
    }

    public sendEnter() {
        this.clearHandledTextareaContext();
        this.setModifier('none');
        if (this.composition) {
            this.settleComposition();
            return;
        }
        this.sendData('\r');
    }

    public sendArrow(direction: 'left' | 'up' | 'down' | 'right') {
        this.clearHandledTextareaContext();
        const shifted = this.inputModifier === 'shift';
        this.setModifier('none');
        const suffix = { left: 'D', up: 'A', down: 'B', right: 'C' }[direction];
        if (shifted) {
            this.sendData(`\x1b[1;2${suffix}`);
            return;
        }

        const prefix = this.terminal?.modes.applicationCursorKeysMode ? '\x1bO' : '\x1b[';
        this.sendData(prefix + suffix);
    }

    public claimRecoveryPointer(event: Event, createNew = false): boolean {
        if (this.inputReady) return false;
        event.preventDefault();
        event.stopPropagation();
        this.consumeRecoveryClick = event.type === 'pointerdown';
        this.invalidateInputOwner(true);
        if (this.displaced) return true;
        this.requestRecovery(createNew);
        return true;
    }

    public requestRecoveryFromToolbar(): boolean {
        if (this.inputReady) return false;
        this.invalidateInputOwner(true);
        if (!this.displaced) this.requestRecovery(false);
        return true;
    }

    private requestRecovery(createNew: boolean) {
        if (this.disposed || this.displaced || this.connectPromise) return;
        if (createNew || !this.request || this.connectionState === 'no-session') {
            this.request = this.options.session.create();
            this.appliedPosition = 0;
            this.replayTarget = 0;
            this.terminalEpoch++;
        }
        this.takeoverPending = false;
        this.takeoverOwnerGeneration = 0;
        this.connectionState = 'disconnected';
        this.automaticRecoveryExhausted = false;
        this.reconnectStartedAt = performance.now();
        this.reconnectAttempts = 0;
        this.beginRecovery();
    }

    @bind
    private onWindowUnload(event: BeforeUnloadEvent) {
        event.preventDefault();
        if (this.socket?.readyState === WebSocket.OPEN) {
            const message = 'Close terminal tab? The session remains available during the reconnect grace period.';
            event.returnValue = message;
            return message;
        }
        return undefined;
    }

    private async waitForGeometry(): Promise<boolean> {
        this.fit();
        const deadline = performance.now() + ATTEMPT_TIMEOUT_MS;
        while (!this.disposed && !this.lastValidGeometry && performance.now() < deadline) {
            const frame = createDeferred<void>();
            window.requestAnimationFrame(() => frame.resolve());
            await frame.promise;
            this.fit();
        }
        return this.lastValidGeometry !== undefined;
    }

    private sendCurrentGeometry() {
        const geometry = this.lastValidGeometry;
        const socket = this.socket;
        if (
            !geometry ||
            !this.inputReady ||
            this.serverConnectionGeneration <= 0 ||
            socket?.readyState !== WebSocket.OPEN
        )
            return;
        const previous = this.lastSentGeometry;
        if (
            previous?.serverGeneration === this.serverConnectionGeneration &&
            previous.cols === geometry.cols &&
            previous.rows === geometry.rows
        )
            return;
        socket.send(
            this.textEncoder.encode(
                Command.RESIZE_TERMINAL + JSON.stringify({ columns: geometry.cols, rows: geometry.rows })
            )
        );
        this.lastSentGeometry = { serverGeneration: this.serverConnectionGeneration, ...geometry };
        this.geometrySendCount++;
        this.recordDiagnostic('geometry-sent', geometry.cols * 10000 + geometry.rows);
    }

    @bind
    public open(parent: HTMLElement) {
        this.terminalContainer = parent;
        this.terminal = new Terminal(this.options.termOptions);
        const { terminal, fitAddon, overlayAddon } = this;
        window.term = terminal as TtydTerminal;
        window.term.fit = () => this.fit();
        if (this.diagnosticsEnabled) window.ttydDiagnostics = () => this.diagnosticsSnapshot();

        terminal.loadAddon(fitAddon);
        terminal.loadAddon(overlayAddon);
        terminal.loadAddon(new WebLinksAddon());

        terminal.open(parent);
        this.initListeners();
        this.fit();
        if (this.request) {
            this.reconnectStartedAt = performance.now();
            this.beginRecovery();
        } else {
            this.connectionState = 'no-session';
            overlayAddon.showAction('No saved tab session. Continuity is unavailable.', 'Start New Session', event =>
                this.claimRecoveryPointer(event)
            );
        }
    }

    private registerTouchScroll(element: HTMLElement): IDisposable {
        let lastY: number | undefined;
        let remainder = 0;
        const reset = () => {
            lastY = undefined;
            remainder = 0;
        };
        const onTouchStart = (event: TouchEvent) => {
            if (event.touches.length !== 1) {
                reset();
                return;
            }
            lastY = event.touches[0].clientY;
            remainder = 0;
        };
        const onTouchMove = (event: TouchEvent) => {
            if (event.touches.length !== 1 || lastY === undefined) return;
            const currentY = event.touches[0].clientY;
            const deltaY = currentY - lastY;
            lastY = currentY;
            if (this.terminal.buffer.active.baseY <= 0) return;

            event.preventDefault();
            event.stopPropagation();
            const lineHeight = Math.max(element.clientHeight / Math.max(this.terminal.rows, 1), 1);
            remainder += deltaY;
            const lines = Math.trunc(remainder / lineHeight);
            if (lines === 0) return;
            remainder -= lines * lineHeight;
            this.terminal.scrollLines(-lines);
        };
        const passive = { passive: true } as AddEventListenerOptions;
        const active = { passive: false } as AddEventListenerOptions;
        element.addEventListener('touchstart', onTouchStart, passive);
        element.addEventListener('touchmove', onTouchMove, active);
        element.addEventListener('touchend', reset, passive);
        element.addEventListener('touchcancel', reset, passive);
        return toDisposable(() => {
            element.removeEventListener('touchstart', onTouchStart, passive);
            element.removeEventListener('touchmove', onTouchMove, active);
            element.removeEventListener('touchend', reset, passive);
            element.removeEventListener('touchcancel', reset, passive);
        });
    }

    @bind
    private initListeners() {
        const { terminal, overlayAddon, register, sendData } = this;
        register(
            terminal.onTitleChange(data => {
                if (data && data !== '' && !this.titleFixed) {
                    document.title = data + ' | ' + this.title;
                }
            })
        );
        register(terminal.onData(this.onTerminalData));
        register(
            terminal.onBinary(data => {
                this.recordDiagnostic('terminal-binary', data.length);
                sendData(Uint8Array.from(data, v => v.charCodeAt(0)));
            })
        );
        register(
            terminal.onWriteParsed(() => {
                this.parserCallbacks++;
            })
        );
        register(
            terminal.onRender(() => {
                this.renderEvents++;
                if (this.composition) this.renderLocalPreedit(this.composition.draft);
            })
        );
        register(
            terminal.onResize(({ cols, rows }) => {
                if (this.resizeOverlay) overlayAddon.showOverlay(`${cols}x${rows}`, 300);
            })
        );
        register(
            terminal.onSelectionChange(() => {
                if (this.terminal.getSelection() === '') return;
                try {
                    document.execCommand('copy');
                } catch {
                    return;
                }
                this.overlayAddon?.showOverlay('\u2702', 200);
            })
        );
        register(
            terminal.onKey(event => {
                if (this.inputReady || event.domEvent.key !== 'Enter') return;
                event.domEvent.preventDefault();
                event.domEvent.stopPropagation();
                this.requestRecovery(false);
            })
        );
        const terminalElement = terminal.element;
        const isTouchDevice =
            (window.matchMedia?.('(pointer: coarse)').matches ?? false) || navigator.maxTouchPoints > 0;
        if (terminalElement && isTouchDevice) register(this.registerTouchScroll(terminalElement));
        if (this.terminalContainer) {
            const container = this.terminalContainer;
            const capture = true;
            register(
                addEventListener(container, 'compositionstart', this.handleCompositionStart as EventListener, capture)
            );
            register(
                addEventListener(container, 'compositionupdate', this.handleCompositionUpdate as EventListener, capture)
            );
            register(
                addEventListener(container, 'compositionend', this.handleCompositionEnd as EventListener, capture)
            );
            register(addEventListener(container, 'beforeinput', this.handleBeforeInput as EventListener, capture));
            register(addEventListener(container, 'input', this.handleInput as EventListener, capture));
            register(addEventListener(container, 'paste', this.handlePaste as EventListener, capture));
            register(addEventListener(container, 'keydown', this.handleInputKeyDown as EventListener, capture));
            register(addEventListener(container, 'keyup', this.handleInputKeyUp as EventListener, capture));
            register(
                addEventListener(container, 'pointerdown', this.handleTerminalPointerDown as EventListener, capture)
            );
            register(
                addEventListener(container, 'pointermove', this.handleTerminalPointerMove as EventListener, capture)
            );
            register(addEventListener(container, 'pointerup', this.handleTerminalPointerUp as EventListener, capture));
            register(addEventListener(container, 'pointercancel', this.handleTerminalPointerCancel, capture));
        }
        if (terminal.textarea) {
            register(
                addEventListener(terminal.textarea, 'blur', () => {
                    if (this.toolbarInteraction) {
                        queueMicrotask(() => {
                            if (this.focusIntent === 'typing') this.terminal.focus();
                        });
                        return;
                    }
                    if (this.focusIntent === 'typing') this.invalidateInputOwner(false);
                })
            );
        }
        register(addEventListener(window, 'resize', this.fit));
        if (window.visualViewport) {
            register(addEventListener(window.visualViewport, 'resize', this.fit));
            register(addEventListener(window.visualViewport, 'scroll', this.fit));
        }
        if (typeof ResizeObserver !== 'undefined' && this.terminalContainer) {
            const observer = new ResizeObserver(() => this.fit());
            observer.observe(this.terminalContainer);
            register(toDisposable(() => observer.disconnect()));
        }
        register(addEventListener(window, 'beforeunload', this.onWindowUnload));
        register(addEventListener(document, 'visibilitychange', this.handleVisibilityReturn));
        register(addEventListener(window, 'pageshow', this.handleVisibilityReturn));
        register(addEventListener(window, 'online', this.handleVisibilityReturn));
        register(
            addEventListener(
                document,
                'click',
                event => {
                    if (!this.consumeRecoveryClick) return;
                    this.consumeRecoveryClick = false;
                    event.preventDefault();
                    event.stopPropagation();
                },
                true
            )
        );
        register(
            addEventListener(window, 'pointercancel', () => {
                this.consumeRecoveryClick = false;
            })
        );
        if (this.diagnosticsEnabled && this.animationFrame === undefined)
            this.animationFrame = window.requestAnimationFrame(this.monitorAnimationFrames);
    }

    @bind
    public writeData(data: string | Uint8Array, endPosition?: number, generation: number = this.connectionGeneration) {
        const bytes = typeof data === 'string' ? this.textEncoder.encode(data).byteLength : data.byteLength;
        const { high, low } = this.flowThresholds();
        const afterWrite = () => {
            this.pendingBytes = Math.max(0, this.pendingBytes - bytes);
            if (this.pendingBytes === 0) this.pendingSince = 0;
            if (generation === this.connectionGeneration && endPosition !== undefined)
                this.appliedPosition = Math.max(this.appliedPosition, endPosition);
            if (this.flowPausedGeneration === this.connectionGeneration && this.pendingBytes < low)
                this.sendFlowControl(Command.RESUME);
        };

        if (this.pendingBytes === 0) this.pendingSince = performance.now();
        this.pendingBytes += bytes;
        this.pendingBytesHighWater = Math.max(this.pendingBytesHighWater, this.pendingBytes);
        if (this.pendingBytes > high) {
            this.connectionState = 'render-lagging';
            this.sendFlowControl(Command.PAUSE);
        }
        this.terminal.write(data, afterWrite);
    }

    @bind
    public sendData(data: string | Uint8Array): boolean {
        const { socket, textEncoder } = this;
        if (
            this.displaced ||
            !this.inputReady ||
            this.isExitedRetained ||
            this.serverConnectionGeneration <= 0 ||
            socket?.readyState !== WebSocket.OPEN
        )
            return false;

        if (typeof data === 'string') {
            const payload = new Uint8Array(data.length * 3 + 1);
            payload[0] = Command.INPUT.charCodeAt(0);
            const stats = textEncoder.encodeInto(data, payload.subarray(1));
            socket.send(payload.subarray(0, (stats.written as number) + 1));
        } else {
            const payload = new Uint8Array(data.length + 1);
            payload[0] = Command.INPUT.charCodeAt(0);
            payload.set(data, 1);
            socket.send(payload);
        }
        this.recordDiagnostic('input-sent', typeof data === 'string' ? data.length : data.byteLength);
        return true;
    }

    @bind
    private onTerminalData(data: string) {
        this.recordDiagnostic('terminal-data', data.length);
        const physical = this.rememberTerminalData(data);
        this.sendPlainText(data, physical);
    }

    private requestTakeover(ownerGeneration: number) {
        const socket = this.socket;
        const geometry = this.lastValidGeometry;
        if (
            this.disposed ||
            this.displaced ||
            this.takeoverPending ||
            ownerGeneration <= 0 ||
            !geometry ||
            socket?.readyState !== WebSocket.OPEN
        )
            return;
        this.takeoverPending = true;
        this.takeoverOwnerGeneration = ownerGeneration;
        this.connectionState = 'takeover-pending';
        this.overlayAddon.clearAction();
        this.overlayAddon.showOverlay('Takeover requested...');
        socket.send(
            this.textEncoder.encode(
                Command.TAKEOVER + JSON.stringify({ ownerGeneration, columns: geometry.cols, rows: geometry.rows })
            )
        );
        this.recordDiagnostic('takeover-requested', ownerGeneration);
    }

    private cancelTakeover() {
        if (this.displaced || this.inputReady) return;
        this.takeoverPending = false;
        this.takeoverOwnerGeneration = 0;
        this.invalidateInputOwner(true);
        this.clearSocket(true);
        this.clearHeartbeat();
        this.connectionState = 'session-conflict';
        this.overlayAddon.clearAction();
        this.overlayAddon.showAction('Takeover cancelled. The original tab remains active.', 'Retry', event =>
            this.claimRecoveryPointer(event)
        );
    }

    private enterDisplaced() {
        if (this.displaced) return;
        this.displaced = true;
        this.takeoverPending = false;
        this.takeoverOwnerGeneration = 0;
        this.inputReady = false;
        this.invalidateInputOwner(true);
        this.connectionGeneration++;
        this.fetchAbort?.abort();
        this.fetchAbort = undefined;
        this.clearReconnectTimers();
        this.clearHeartbeat();
        this.clearSocket(true);
        this.connectionState = 'session-displaced';
        this.overlayAddon.clearAction();
        this.overlayAddon.showOverlay('세션이 다른 탭으로 이동되었습니다');
        this.recordDiagnostic('session-displaced');
    }

    private beginRecovery() {
        if (this.disposed || this.displaced || this.connectPromise || !this.request) return;
        this.connectPromise = this.runRecovery().finally(() => {
            this.connectPromise = undefined;
        });
    }

    private async runRecovery() {
        this.clearHeartbeat();
        while (!this.disposed && !this.displaced) {
            const elapsed = performance.now() - this.reconnectStartedAt;
            if (elapsed >= RECONNECT_WINDOW_MS || !this.reconnect) {
                this.showManualReconnect();
                return;
            }

            const result = await this.connectAttempt();
            if (result === 'ready' || result === 'stop' || this.disposed) return;

            const remaining = RECONNECT_WINDOW_MS - (performance.now() - this.reconnectStartedAt);
            if (remaining <= 0) continue;
            const delay = Math.min(1000 * 2 ** Math.min(this.reconnectAttempts, 3), RECONNECT_MAX_DELAY_MS, remaining);
            this.reconnectAttempts++;
            const delayGate = createDeferred<void>();
            this.reconnectDelayResolve = delayGate.resolve;
            this.reconnectTimer = window.setTimeout(() => {
                this.reconnectTimer = undefined;
                this.reconnectDelayResolve = undefined;
                delayGate.resolve();
            }, delay);
            await delayGate.promise;
        }
    }

    private async waitForParserDrain(): Promise<boolean> {
        const deadline = performance.now() + ATTEMPT_TIMEOUT_MS;
        while (!this.disposed && this.pendingBytes > 0 && performance.now() < deadline) {
            const parserTick = createDeferred<void>();
            window.setTimeout(parserTick.resolve, 16);
            await parserTick.promise;
        }
        if (this.pendingBytes === 0) return true;
        this.connectionState = 'terminal-state-lost';
        this.overlayAddon.showAction('Terminal parser did not settle. Input remains blocked.', 'Retry', event =>
            this.claimRecoveryPointer(event)
        );
        return false;
    }

    private async connectAttempt(): Promise<AttemptResult> {
        if (!(await this.waitForParserDrain()) || !(await this.waitForGeometry()) || !this.request || this.disposed)
            return 'stop';
        this.invalidateInputOwner(true);
        const generation = ++this.connectionGeneration;
        const request = this.request;
        this.clearSocket(true);
        this.flowPausedGeneration = undefined;
        this.inputReady = false;
        this.connectionState = 'connecting';
        this.recordDiagnostic('connecting', generation);
        this.overlayAddon.clearAction();
        this.overlayAddon.showOverlay('Connecting...');

        this.fetchAbort?.abort();
        const controller = new AbortController();
        this.fetchAbort = controller;
        const tokenTimeout = Math.min(
            TOKEN_TIMEOUT_MS,
            RECONNECT_WINDOW_MS - (performance.now() - this.reconnectStartedAt)
        );
        if (tokenTimeout <= 0) {
            this.fetchAbort = undefined;
            return 'retry';
        }
        this.attemptTimer = window.setTimeout(() => controller.abort(), tokenTimeout);
        try {
            const response = await fetch(this.options.tokenUrl, { signal: controller.signal, cache: 'no-store' });
            if (!response.ok) throw new Error(`token response ${response.status}`);
            const body = (await response.json()) as { token?: unknown };
            if (typeof body.token !== 'string') throw new Error('token response missing token');
            this.token = body.token;
        } catch (error) {
            if (!this.disposed) console.warn(`[ttyd] fetch ${this.options.tokenUrl}:`, error);
            return this.disposed ? 'stop' : 'retry';
        } finally {
            if (this.attemptTimer !== undefined) window.clearTimeout(this.attemptTimer);
            this.attemptTimer = undefined;
            if (this.fetchAbort === controller) this.fetchAbort = undefined;
        }

        if (this.disposed || generation !== this.connectionGeneration) return 'stop';
        const url = new URL(this.options.wsBaseUrl);
        url.searchParams.set('resume', request.id);
        const socket = new WebSocket(url, ['tty']);
        socket.binaryType = 'arraybuffer';
        this.socket = socket;
        this.socketDisposables.push(
            addEventListener(socket, 'open', () => this.handleSocketOpen(socket, generation, request)),
            addEventListener(socket, 'message', event => this.onSocketData(event as MessageEvent, socket, generation)),
            addEventListener(socket, 'close', event => this.handleSocketClose(event as CloseEvent, socket, generation)),
            addEventListener(socket, 'error', () => console.warn('[ttyd] websocket error'))
        );

        const attempt = createDeferred<AttemptResult>();
        this.attemptResolve = attempt.resolve;
        const attemptTimeout = Math.min(
            ATTEMPT_TIMEOUT_MS,
            RECONNECT_WINDOW_MS - (performance.now() - this.reconnectStartedAt)
        );
        if (attemptTimeout <= 0) {
            this.clearSocket(true);
            this.settleAttempt('retry');
            return attempt.promise;
        }
        this.attemptTimer = window.setTimeout(() => {
            if (generation !== this.connectionGeneration) return;
            this.recordDiagnostic('attempt-timeout', generation);
            this.clearSocket(true);
            this.settleAttempt('retry');
        }, attemptTimeout);
        return attempt.promise;
    }

    private handleSocketOpen(socket: WebSocket, generation: number, request: SessionRequest) {
        if (socket !== this.socket || generation !== this.connectionGeneration || this.disposed) return;
        const geometry = this.lastValidGeometry;
        if (!geometry) {
            this.clearSocket(true);
            this.settleAttempt('retry');
            return;
        }
        const message = JSON.stringify({
            version: 3,
            intent: request.intent,
            replayPosition: this.appliedPosition,
            AuthToken: this.token,
            columns: geometry.cols,
            rows: geometry.rows,
        });
        this.handshakeGeometry = { connectionGeneration: generation, ...geometry };
        socket.send(this.textEncoder.encode(message));
        this.connectionState = 'connected';
        this.recordDiagnostic('connected', generation);
    }

    private handleSocketClose(event: CloseEvent, socket: WebSocket, generation: number) {
        if (socket !== this.socket || generation !== this.connectionGeneration || this.disposed) return;
        const stopped = this.connectionState.startsWith('session-') || this.connectionState === 'no-session';
        this.clearSocket(false);
        this.clearHeartbeat();
        this.inputReady = false;
        this.invalidateInputOwner(true);
        this.handshakeGeometry = undefined;
        this.flowPausedGeneration = undefined;
        this.recordDiagnostic('disconnected', event.code);
        if (stopped) return;
        this.connectionState = 'disconnected';
        if (this.attemptResolve) {
            this.settleAttempt('retry');
            return;
        }
        this.overlayAddon.showOverlay('Connection lost. Recovering...');
        this.reconnectStartedAt = performance.now();
        this.reconnectAttempts = 0;
        this.automaticRecoveryExhausted = false;
        if (this.reconnect) this.beginRecovery();
        else this.showManualReconnect();
    }

    private settleAttempt(result: AttemptResult) {
        const resolve = this.attemptResolve;
        if (!resolve) return;
        this.attemptResolve = undefined;
        if (this.attemptTimer !== undefined) window.clearTimeout(this.attemptTimer);
        this.attemptTimer = undefined;
        resolve(result);
    }

    private clearSocket(close: boolean) {
        const socket = this.socket;
        this.socket = undefined;
        for (const disposable of this.socketDisposables) disposable.dispose();
        this.socketDisposables.length = 0;
        if (close && socket && socket.readyState < WebSocket.CLOSING) socket.close();
    }

    private clearReconnectTimers() {
        if (this.reconnectTimer !== undefined) window.clearTimeout(this.reconnectTimer);
        if (this.attemptTimer !== undefined) window.clearTimeout(this.attemptTimer);
        this.reconnectTimer = undefined;
        this.attemptTimer = undefined;
        this.reconnectDelayResolve?.();
        this.reconnectDelayResolve = undefined;
        this.attemptResolve?.('stop');
        this.attemptResolve = undefined;
    }

    private showManualReconnect() {
        this.automaticRecoveryExhausted = true;
        this.connectionState = 'disconnected';
        this.overlayAddon.showAction('Automatic recovery paused.', 'Reconnect', event =>
            this.claimRecoveryPointer(event)
        );
    }

    @bind
    private handleVisibilityReturn() {
        this.fit();
        if (document.visibilityState === 'hidden') {
            this.invalidateInputOwner(true);
            return;
        }
        if (this.disposed || this.displaced) return;
        if (this.inputReady) {
            this.sendHeartbeat();
        } else if (!this.automaticRecoveryExhausted) {
            if (this.reconnectStartedAt === 0) this.reconnectStartedAt = performance.now();
            this.beginRecovery();
        }
    }

    private startHeartbeat() {
        this.clearHeartbeat();
        this.heartbeatTimer = window.setInterval(() => this.sendHeartbeat(), HEARTBEAT_INTERVAL_MS);
        this.sendHeartbeat();
    }

    private sendHeartbeat() {
        const socket = this.socket;
        if (
            this.displaced ||
            !this.inputReady ||
            document.visibilityState === 'hidden' ||
            socket?.readyState !== WebSocket.OPEN
        )
            return;
        if (this.heartbeatNonce) {
            if (Date.now() - this.heartbeatSentAt < HEARTBEAT_TIMEOUT_MS) return;
            this.recordDiagnostic('heartbeat-timeout', this.connectionGeneration);
            this.inputReady = false;
            this.invalidateInputOwner(true);
            this.clearSocket(true);
            this.clearHeartbeat();
            this.connectionState = 'disconnected';
            this.reconnectStartedAt = performance.now();
            this.reconnectAttempts = 0;
            this.automaticRecoveryExhausted = false;
            this.beginRecovery();
            return;
        }
        const nonce = `${this.connectionGeneration}:${++this.heartbeatCounter}`;
        this.heartbeatNonce = nonce;
        this.heartbeatSentAt = Date.now();
        socket.send(this.textEncoder.encode(Command.HEARTBEAT + nonce));
        this.recordDiagnostic('heartbeat-sent', this.heartbeatCounter);
    }

    private clearHeartbeat() {
        if (this.heartbeatTimer !== undefined) window.clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = undefined;
        this.heartbeatNonce = undefined;
        this.heartbeatSentAt = 0;
    }

    @bind
    private parseOptsFromUrlQuery(query: string): Preferences {
        const { terminal } = this;
        const { clientOptions } = this.options;
        const prefs = {} as Preferences;
        const queryObj = Array.from(new URLSearchParams(query) as unknown as Iterable<[string, string]>);

        for (const [k, queryVal] of queryObj) {
            let v = clientOptions[k];
            if (v === undefined) v = terminal.options[k];
            switch (typeof v) {
                case 'boolean':
                    prefs[k] = queryVal === 'true' || queryVal === '1';
                    break;
                case 'number':
                case 'bigint':
                    prefs[k] = Number.parseInt(queryVal, 10);
                    break;
                case 'string':
                    prefs[k] = queryVal;
                    break;
                case 'object':
                    prefs[k] = JSON.parse(queryVal);
                    break;
                default:
                    console.warn(`[ttyd] maybe unknown option: ${k}=${queryVal}, treating as string`);
                    prefs[k] = queryVal;
                    break;
            }
        }

        return prefs;
    }

    private async settleReplay(socket: WebSocket, generation: number, position: number, truncated: boolean) {
        const deadline = performance.now() + ATTEMPT_TIMEOUT_MS;
        while (
            !this.disposed &&
            socket === this.socket &&
            generation === this.connectionGeneration &&
            (this.pendingBytes > 0 || this.appliedPosition < position) &&
            performance.now() < deadline
        ) {
            const parserTick = createDeferred<void>();
            window.setTimeout(parserTick.resolve, 16);
            await parserTick.promise;
        }
        if (
            this.disposed ||
            socket !== this.socket ||
            generation !== this.connectionGeneration ||
            this.pendingBytes > 0 ||
            this.appliedPosition < position
        ) {
            this.recordDiagnostic('replay-settlement-failed', position);
            this.clearSocket(true);
            this.settleAttempt('retry');
            return;
        }

        for (let frame = 0; frame < 2; frame++) {
            const rendered = createDeferred<void>();
            window.requestAnimationFrame(() => rendered.resolve());
            await rendered.promise;
        }
        if (socket !== this.socket || generation !== this.connectionGeneration || socket.readyState !== WebSocket.OPEN)
            return;
        this.replayTarget = position;
        if (this.isExitedRetained) {
            this.inputReady = false;
            this.invalidateInputOwner(true);
            this.recordDiagnostic('replay-settled', position);
            return;
        }
        this.connectionState = truncated ? 'terminal-state-lost' : 'replaying';
        socket.send(this.textEncoder.encode(Command.SESSION_READY + JSON.stringify({ position })));
        this.recordDiagnostic('replay-settled', position);
    }

    private onSocketData(event: MessageEvent, socket: WebSocket, generation: number) {
        if (socket !== this.socket || generation !== this.connectionGeneration || !(event.data instanceof ArrayBuffer))
            return;
        const rawData = event.data;
        const bytes = new Uint8Array(rawData);
        if (bytes.length === 0) return;
        const command = String.fromCharCode(bytes[0]);

        switch (command) {
            case Command.OUTPUT: {
                if (bytes.length < 9) return;
                const view = new DataView(rawData);
                const endPosition = view.getUint32(1) * 0x1_0000_0000 + view.getUint32(5);
                const data = rawData.slice(9);
                if (this.zmodemAddon) {
                    this.writeFunc(data);
                    this.appliedPosition = Math.max(this.appliedPosition, endPosition);
                } else {
                    this.writeData(new Uint8Array(data), endPosition, generation);
                }
                break;
            }
            case Command.SET_WINDOW_TITLE:
                this.title = this.textDecoder.decode(rawData.slice(1));
                document.title = this.title;
                break;
            case Command.SET_PREFERENCES:
                if (!this.preferencesApplied) {
                    this.preferencesApplied = true;
                    this.applyPreferences({
                        ...this.options.clientOptions,
                        ...JSON.parse(this.textDecoder.decode(rawData.slice(1))),
                        ...this.parseOptsFromUrlQuery(window.location.search),
                    } as Preferences);
                }
                break;
            case Command.SET_SESSION_STATE: {
                const message = JSON.parse(this.textDecoder.decode(rawData.slice(1))) as {
                    version?: number;
                    state?: string;
                    sessionDiagnosticId?: number;
                    connectionGeneration?: number;
                    ownerGeneration?: number;
                    replay?: { from?: number; to?: number; truncated?: boolean };
                    inputReady?: boolean;
                    exitCode?: number;
                    exitSignal?: number;
                };
                if (message.version !== 3 || typeof message.state !== 'string') {
                    this.connectionState = 'session-error';
                    this.overlayAddon.showAction('Session protocol mismatch.', 'Retry', pointer =>
                        this.claimRecoveryPointer(pointer)
                    );
                    this.settleAttempt('stop');
                    return;
                }
                this.serverConnectionGeneration = message.connectionGeneration ?? 0;
                this.sessionDiagnosticId = message.sessionDiagnosticId ?? 0;
                this.replayTarget = message.replay?.to ?? 0;
                const truncated = message.replay?.truncated === true;
                this.recordDiagnostic(`session-${message.state}`, this.serverConnectionGeneration);

                if (message.state === 'displaced') {
                    this.enterDisplaced();
                    this.settleAttempt('stop');
                    return;
                }

                if (message.state === 'checking') {
                    this.inputReady = false;
                    this.invalidateInputOwner(true);
                    this.connectionState = 'checking-owner';
                    this.overlayAddon.showOverlay('Checking previous connection...');
                    break;
                }
                if (message.state === 'exited_retained') {
                    this.isExitedRetained = true;
                    this.takeoverPending = false;
                    this.takeoverOwnerGeneration = 0;
                    this.inputReady = false;
                    this.invalidateInputOwner(true);
                    this.connectionState = 'session-exited-retained';
                    const exitCode = message.exitCode ?? 0;
                    const exitSignal = message.exitSignal ?? 0;
                    const statusText =
                        exitSignal > 0 ? `작업 완료 (신호: ${exitSignal})` : `작업 완료 (종료 코드: ${exitCode})`;
                    const notice = truncated ? `${statusText} - 이전 출력이 절사됨 (최신 8 MiB 보존)` : statusText;
                    this.overlayAddon.showAction(notice, 'Start New Session', pointer =>
                        this.claimRecoveryPointer(pointer, true)
                    );
                    break;
                }
                if (message.state === 'created' || message.state === 'attached') {
                    this.takeoverPending = false;
                    this.takeoverOwnerGeneration = 0;
                    this.overlayAddon.clearAction();
                    if (message.state === 'created' && this.request) this.options.session.markCreated(this.request);
                    if (message.inputReady) {
                        this.inputReady = true;
                        this.reconnectStartedAt = 0;
                        this.reconnectAttempts = 0;
                        this.automaticRecoveryExhausted = false;
                        this.connectionState = truncated ? 'terminal-state-lost' : 'application-ready';
                        this.overlayAddon.showOverlay(
                            truncated ? '이전 출력이 절사됨 (최신 8 MiB 보존)' : 'Input ready',
                            600
                        );
                        if (this.request && !this.request.persisted)
                            this.overlayAddon.showOverlay('Ephemeral session: reload continuity is unavailable.', 2500);
                        this.startHeartbeat();
                        this.settleAttempt('ready');
                        const handshake = this.handshakeGeometry;
                        if (handshake?.connectionGeneration === generation) {
                            this.lastSentGeometry = {
                                serverGeneration: this.serverConnectionGeneration,
                                cols: handshake.cols,
                                rows: handshake.rows,
                            };
                        }
                        this.sendCurrentGeometry();
                        const isTouchDevice =
                            (window.matchMedia?.('(pointer: coarse)').matches ?? false) || navigator.maxTouchPoints > 0;
                        if (!isTouchDevice) this.activateTypingFocus();
                    } else {
                        this.inputReady = false;
                        this.invalidateInputOwner(true);
                        this.connectionState = 'replaying';
                        this.overlayAddon.showOverlay('Session accepted. Restoring screen...');
                    }
                    break;
                }
                this.inputReady = false;
                this.invalidateInputOwner(true);
                this.automaticRecoveryExhausted = true;
                this.takeoverPending = false;
                if (message.state === 'conflict' && typeof message.ownerGeneration === 'number') {
                    this.takeoverOwnerGeneration = message.ownerGeneration;
                    this.connectionState = 'session-conflict';
                    this.overlayAddon.showChoices('세션이 이미 다른 탭에서 사용 중입니다', [
                        {
                            label: '이 화면으로 가져오기 (Take Over)',
                            action: () => this.requestTakeover(message.ownerGeneration as number),
                        },
                        { label: '취소', action: () => this.cancelTakeover() },
                    ]);
                    this.settleAttempt('stop');
                    break;
                }
                this.takeoverOwnerGeneration = 0;
                const stopped = message.state as
                    'conflict' | 'stale' | 'expired' | 'exited' | 'unknown' | 'error' | 'rejected_capacity';
                const labels: Record<string, readonly [string, string]> = {
                    conflict: ['Session ownership changed. Reconnect to recheck.', 'Retry'],
                    stale: ['Session ownership changed. Reconnect to recheck.', 'Retry'],
                    expired: ['Session expired. No new shell was started.', 'Start New Session'],
                    exited: ['Session exited. Results are not retained by this block.', 'Start New Session'],
                    unknown: ['Recovery target cannot be confirmed.', 'Start New Session'],
                    rejected_capacity: ['서버 수용 한도에 도달했습니다. 잠시 후 다시 시도하십시오.', 'Retry'],
                    error: ['Session protocol error. No shell was started.', 'Retry'],
                };
                const [label, action] = labels[stopped] ?? labels.error;
                this.connectionState = (
                    stopped === 'rejected_capacity' ? 'session-rejected-capacity' : `session-${stopped}`
                ) as TtydDiagnosticsSnapshot['state'];
                const createNew = stopped === 'expired' || stopped === 'exited' || stopped === 'unknown';
                this.overlayAddon.showAction(label, action, pointer => this.claimRecoveryPointer(pointer, createNew));
                this.settleAttempt('stop');
                break;
            }
            case Command.REPLAY_END: {
                const message = JSON.parse(this.textDecoder.decode(rawData.slice(1))) as {
                    version?: number;
                    position?: number;
                    truncated?: boolean;
                };
                if (message.version === 3 && typeof message.position === 'number')
                    void this.settleReplay(socket, generation, message.position, message.truncated === true);
                break;
            }
            case Command.HEARTBEAT_REPLY: {
                const nonce = this.textDecoder.decode(rawData.slice(1));
                if (nonce === this.heartbeatNonce) {
                    this.heartbeatNonce = undefined;
                    this.heartbeatSentAt = 0;
                    this.recordDiagnostic('heartbeat-received', this.heartbeatCounter);
                }
                break;
            }
            default:
                console.warn(`[ttyd] unknown command: ${command}`);
                break;
        }
    }

    @bind
    private applyPreferences(prefs: Preferences) {
        const { terminal, register } = this;
        if (prefs.enableZmodem || prefs.enableTrzsz) {
            this.zmodemAddon = new ZmodemAddon({
                zmodem: prefs.enableZmodem,
                trzsz: prefs.enableTrzsz,
                windows: prefs.isWindows,
                trzszDragInitTimeout: prefs.trzszDragInitTimeout,
                onSend: this.sendCb,
                sender: this.sendData,
                writer: this.writeData,
            });
            this.writeFunc = data => this.zmodemAddon?.consume(data);
            terminal.loadAddon(register(this.zmodemAddon));
        }

        for (const [key, value] of Object.entries(prefs)) {
            switch (key) {
                case 'rendererType':
                    this.setRendererType(value);
                    break;
                case 'disableLeaveAlert':
                    if (value) {
                        window.removeEventListener('beforeunload', this.onWindowUnload);
                        console.log('[ttyd] Leave site alert disabled');
                    }
                    break;
                case 'disableResizeOverlay':
                    if (value) {
                        console.log('[ttyd] Resize overlay disabled');
                        this.resizeOverlay = false;
                    }
                    break;
                case 'disableReconnect':
                    if (value) {
                        console.log('[ttyd] Reconnect disabled');
                        this.reconnect = false;
                    }
                    break;
                case 'enableZmodem':
                    if (value) console.log('[ttyd] Zmodem enabled');
                    break;
                case 'enableTrzsz':
                    if (value) console.log('[ttyd] trzsz enabled');
                    break;
                case 'trzszDragInitTimeout':
                    if (value) console.log(`[ttyd] trzsz drag init timeout: ${value}`);
                    break;
                case 'enableSixel':
                    if (value) {
                        terminal.loadAddon(register(new ImageAddon()));
                        console.log('[ttyd] Sixel enabled');
                    }
                    break;
                case 'titleFixed':
                    if (!value || value === '') return;
                    console.log(`[ttyd] setting fixed title: ${value}`);
                    this.titleFixed = value;
                    document.title = value;
                    break;
                case 'isWindows':
                    if (value) console.log('[ttyd] is windows');
                    break;
                case 'unicodeVersion':
                    switch (value) {
                        case 6:
                        case '6':
                            console.log('[ttyd] setting Unicode version: 6');
                            break;
                        case 11:
                        case '11':
                        default:
                            console.log('[ttyd] setting Unicode version: 11');
                            terminal.loadAddon(new Unicode11Addon());
                            terminal.unicode.activeVersion = '11';
                            break;
                    }
                    break;
                default:
                    console.log(`[ttyd] option: ${key}=${JSON.stringify(value)}`);
                    if (key === 'fontSize') {
                        this.setFontSize(Number(value));
                    } else {
                        if (terminal.options[key] instanceof Object) {
                            terminal.options[key] = Object.assign({}, terminal.options[key], value);
                        } else {
                            terminal.options[key] = value;
                        }
                        if (key.indexOf('font') === 0) this.fit();
                    }
                    break;
            }
        }
    }

    @bind
    private setRendererType(value: RendererType) {
        const { terminal } = this;
        const disposeWebglRenderer = () => {
            const addon = this.webglAddon;
            this.webglAddon = undefined;
            try {
                addon?.dispose();
            } catch {
                // ignore
            }
        };
        const enableWebglRenderer = () => {
            if (this.webglAddon) return;
            const addon = new WebglAddon();
            this.webglAddon = addon;
            try {
                addon.onContextLoss(() => {
                    if (this.webglAddon !== addon) return;
                    console.warn('[ttyd] WebGL context lost, falling back to default renderer');
                    disposeWebglRenderer();
                });
                terminal.loadAddon(addon);
                console.log('[ttyd] WebGL renderer loaded');
            } catch (e) {
                console.warn('[ttyd] WebGL renderer could not be loaded, falling back to default renderer', e);
                disposeWebglRenderer();
            }
        };

        switch (value) {
            case 'canvas':
                disposeWebglRenderer();
                console.log('[ttyd] canvas renderer is unavailable with xterm 6; using default renderer');
                break;
            case 'webgl':
                enableWebglRenderer();
                break;
            case 'dom':
                disposeWebglRenderer();
                console.log('[ttyd] default renderer loaded');
                break;
            default:
                break;
        }
    }
}
