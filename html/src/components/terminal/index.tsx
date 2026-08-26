import { bind } from 'decko';
import { Component, h } from 'preact';
import { Xterm, XtermOptions } from './xterm';

import '@xterm/xterm/css/xterm.css';
import { Modal } from '../modal';

interface Props extends XtermOptions {
    id: string;
}

interface State {
    modal: boolean;
    fontSize: number;
    ctrlArmed: boolean;
    isFullscreen: boolean;
}

const FONT_STORAGE_KEY = 'webterm.fontSize';
const MIN_FONT_SIZE = 10;
const MAX_FONT_SIZE = 30;

function clampFontSize(value: number): number {
    return Math.min(MAX_FONT_SIZE, Math.max(MIN_FONT_SIZE, value));
}

function getInitialFontSize(props: Props): number {
    const fallback = clampFontSize(props.termOptions.fontSize ?? 13);
    try {
        const stored = window.localStorage.getItem(FONT_STORAGE_KEY);
        if (stored === null) return fallback;
        const parsed = Number.parseInt(stored, 10);
        return Number.isFinite(parsed) ? clampFontSize(parsed) : fallback;
    } catch {
        return fallback;
    }
}

export class Terminal extends Component<Props, State> {
    private container: HTMLElement;
    private xterm: Xterm;

    constructor(props: Props) {
        super(props);
        const fontSize = getInitialFontSize(props);
        this.state = { modal: false, fontSize, ctrlArmed: false, isFullscreen: false };
        this.xterm = new Xterm(
            { ...props, termOptions: { ...props.termOptions, fontSize } },
            this.showModal,
            this.handleCtrlState
        );
    }

    async componentDidMount() {
        document.addEventListener('fullscreenchange', this.handleFullscreenChange);
        await this.xterm.refreshToken();
        this.xterm.open(this.container);
        this.xterm.connect();
    }

    componentWillUnmount() {
        document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
        this.xterm.dispose();
    }

    render({ id }: Props, { modal, fontSize, ctrlArmed, isFullscreen }: State) {
        return (
            <div class="webterm-root">
                <div
                    class="mobile-toolbar"
                    role="toolbar"
                    aria-label="Terminal controls"
                    onPointerDown={event => {
                        event.stopPropagation();
                        this.blurTerminalAndHideKeyboard();
                    }}
                >
                    <div class="toolbar-group">
                        <button class="toolbar-button" type="button" onClick={this.sendEscape}>
                            ESC
                        </button>
                        <button
                            class={ctrlArmed ? 'toolbar-button ctrl-button active' : 'toolbar-button ctrl-button'}
                            type="button"
                            aria-pressed={ctrlArmed}
                            onClick={this.toggleCtrl}
                        >
                            {ctrlArmed ? 'CTRL●' : 'CTRL'}
                        </button>
                    </div>
                    <div class="toolbar-group font-group">
                        <button class="toolbar-button" type="button" onClick={() => this.changeFontSize(-1)}>
                            A−
                        </button>
                        <span class="font-size-status" aria-label={`Font size ${fontSize} pixels`}>
                            {fontSize}
                        </span>
                        <button class="toolbar-button" type="button" onClick={() => this.changeFontSize(1)}>
                            A+
                        </button>
                    </div>
                    <div class="toolbar-group fullscreen-group">
                        <button
                            class={isFullscreen ? 'toolbar-button active' : 'toolbar-button'}
                            type="button"
                            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                            aria-pressed={isFullscreen}
                            onClick={this.toggleFullscreen}
                        >
                            ⛶
                        </button>
                    </div>
                </div>
                <div id={id} class="terminal-container" ref={c => (this.container = c as HTMLElement)}>
                    <Modal show={modal}>
                        <label class="file-label">
                            <input onChange={this.sendFile} class="file-input" type="file" multiple />
                            <span class="file-cta">Choose files…</span>
                        </label>
                    </Modal>
                </div>
            </div>
        );
    }

    private blurTerminalAndHideKeyboard() {
        this.xterm.blur();
        const virtualKeyboard = (navigator as Navigator & { virtualKeyboard?: { hide(): void } }).virtualKeyboard;
        try {
            virtualKeyboard?.hide();
        } catch {
            // The VirtualKeyboard API is optional; blur is the primary guarantee.
        }
    }

    @bind
    private sendEscape() {
        this.blurTerminalAndHideKeyboard();
        this.xterm.sendEscape();
    }

    @bind
    private toggleCtrl() {
        this.blurTerminalAndHideKeyboard();
        this.xterm.toggleCtrlArmed();
    }

    private changeFontSize(delta: number) {
        this.blurTerminalAndHideKeyboard();
        const fontSize = clampFontSize(this.state.fontSize + delta);
        if (fontSize === this.state.fontSize) return;

        this.setState({ fontSize });
        try {
            window.localStorage.setItem(FONT_STORAGE_KEY, String(fontSize));
        } catch {
            // Preference persistence is best-effort only.
        }
        this.xterm.setFontSize(fontSize);
    }

    @bind
    private handleCtrlState(ctrlArmed: boolean) {
        this.setState({ ctrlArmed });
    }

    @bind
    private handleFullscreenChange() {
        this.setState({ isFullscreen: Boolean(document.fullscreenElement) });
        this.xterm.fit();
    }

    @bind
    private async toggleFullscreen() {
        this.blurTerminalAndHideKeyboard();
        try {
            if (!document.fullscreenElement) {
                await document.documentElement.requestFullscreen();
            } else {
                await document.exitFullscreen();
            }
        } catch (error) {
            console.warn('[ttyd] Fullscreen request failed', error);
        }
    }

    @bind
    showModal() {
        this.setState({ modal: true });
    }

    @bind
    sendFile(event: Event) {
        this.setState({ modal: false });
        const files = (event.target as HTMLInputElement).files;
        if (files) this.xterm.sendFile(files);
    }
}
