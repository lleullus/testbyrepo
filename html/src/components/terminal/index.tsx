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
    shiftArmed: boolean;
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
        this.state = { modal: false, fontSize, ctrlArmed: false, shiftArmed: false, isFullscreen: false };
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

    render({ id }: Props, { modal, fontSize, ctrlArmed, shiftArmed, isFullscreen }: State) {
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
                    <div class="toolbar-row">
                        <button class="toolbar-button tab-button" type="button" onClick={this.sendTab}>
                            TAB
                        </button>
                        <button
                            class={shiftArmed ? 'toolbar-button shift-button active' : 'toolbar-button shift-button'}
                            type="button"
                            aria-label="Shift"
                            aria-pressed={shiftArmed}
                            onClick={this.toggleShift}
                        >
                            ⇧
                        </button>
                        <button
                            class="toolbar-button arrow-button arrow-left"
                            type="button"
                            aria-label="Arrow left"
                            onClick={() => this.sendArrow('left')}
                        >
                            ←
                        </button>
                        <button
                            class="toolbar-button arrow-button arrow-up"
                            type="button"
                            aria-label="Arrow up"
                            onClick={() => this.sendArrow('up')}
                        >
                            ↑
                        </button>
                        <button
                            class="toolbar-button arrow-button arrow-down"
                            type="button"
                            aria-label="Arrow down"
                            onClick={() => this.sendArrow('down')}
                        >
                            ↓
                        </button>
                        <button
                            class="toolbar-button arrow-button arrow-right"
                            type="button"
                            aria-label="Arrow right"
                            onClick={() => this.sendArrow('right')}
                        >
                            →
                        </button>
                        <button
                            class="toolbar-button enter-button"
                            type="button"
                            aria-label="Enter"
                            onClick={this.sendEnter}
                        >
                            ↵
                        </button>
                        <button class="toolbar-button escape-button" type="button" onClick={this.sendEscape}>
                            ESC
                        </button>
                        <button
                            class={ctrlArmed ? 'toolbar-button ctrl-button active' : 'toolbar-button ctrl-button'}
                            type="button"
                            aria-pressed={ctrlArmed}
                            onClick={this.toggleCtrl}
                        >
                            CTRL
                        </button>
                        <button
                            class="toolbar-button font-decrease-button"
                            type="button"
                            aria-label={`Decrease font size; current ${fontSize} pixels`}
                            onClick={() => this.changeFontSize(-1)}
                        >
                            A−
                        </button>
                        <button
                            class="toolbar-button font-increase-button"
                            type="button"
                            aria-label={`Increase font size; current ${fontSize} pixels`}
                            onClick={() => this.changeFontSize(1)}
                        >
                            A+
                        </button>
                        <button
                            class={
                                isFullscreen
                                    ? 'toolbar-button fullscreen-button active'
                                    : 'toolbar-button fullscreen-button'
                            }
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
                <div
                    id={id}
                    class="terminal-container"
                    ref={c => (this.container = c as HTMLElement)}
                    onPointerDown={this.handleTerminalPointerDown}
                >
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

    private clearShiftArmed() {
        if (this.state.shiftArmed) this.setState({ shiftArmed: false });
    }

    private clearCtrlArmed() {
        if (this.state.ctrlArmed) this.xterm.setCtrlArmed(false);
    }

    @bind
    private handleTerminalPointerDown() {
        this.clearShiftArmed();
    }

    @bind
    private sendTab() {
        this.blurTerminalAndHideKeyboard();
        const shifted = this.state.shiftArmed;
        this.clearShiftArmed();
        this.clearCtrlArmed();
        this.xterm.sendTab(shifted);
    }

    @bind
    private toggleShift() {
        this.blurTerminalAndHideKeyboard();
        const shiftArmed = !this.state.shiftArmed;
        if (shiftArmed && this.state.ctrlArmed) this.xterm.setCtrlArmed(false);
        this.setState({ shiftArmed });
    }

    private sendArrow(direction: 'left' | 'up' | 'down' | 'right') {
        this.blurTerminalAndHideKeyboard();
        const shifted = this.state.shiftArmed;
        this.clearShiftArmed();
        this.clearCtrlArmed();
        this.xterm.sendArrow(direction, shifted);
    }

    @bind
    private sendEnter() {
        this.blurTerminalAndHideKeyboard();
        this.clearShiftArmed();
        this.clearCtrlArmed();
        this.xterm.sendEnter();
    }

    @bind
    private sendEscape() {
        this.blurTerminalAndHideKeyboard();
        this.clearShiftArmed();
        this.xterm.sendEscape();
    }

    @bind
    private toggleCtrl() {
        this.blurTerminalAndHideKeyboard();
        this.clearShiftArmed();
        this.xterm.toggleCtrlArmed();
    }

    private changeFontSize(delta: number) {
        this.blurTerminalAndHideKeyboard();
        this.clearShiftArmed();
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
        this.clearShiftArmed();
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
