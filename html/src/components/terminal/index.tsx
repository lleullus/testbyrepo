import { bind } from 'decko';
import { Component, h } from 'preact';
import { InputOwnerSnapshot, Xterm, XtermOptions } from './xterm';

import '@xterm/xterm/css/xterm.css';
import { Modal } from '../modal';

interface Props extends XtermOptions {
    id: string;
}

interface State {
    modal: boolean;
}

const FONT_STORAGE_KEY = 'webterm.fontSize';
const MIN_FONT_SIZE = 8;
const MAX_FONT_SIZE = 32;

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
    private toolbar: HTMLElement;
    private fontSize: number;
    private inputOwner: InputOwnerSnapshot = {
        modifier: 'none',
        focusIntent: 'inactive',
        composing: false,
        inputEpoch: 0,
    };
    private isFullscreen = false;

    constructor(props: Props) {
        super(props);
        this.fontSize = getInitialFontSize(props);
        this.state = { modal: false };
        this.xterm = new Xterm(
            { ...props, termOptions: { ...props.termOptions, fontSize: this.fontSize } },
            this.showModal,
            this.handleInputState,
            this.handleFontSize
        );
    }

    componentDidMount() {
        document.addEventListener('fullscreenchange', this.handleFullscreenChange);
        this.toolbar = this.container.parentElement?.querySelector('.mobile-toolbar') as HTMLElement;
        this.toolbar.addEventListener('pointerdown', this.handleToolbarPointerDown, true);
        this.toolbar.addEventListener('mousedown', this.handleToolbarPointerDown, true);
        this.xterm.open(this.container);
    }

    componentWillUnmount() {
        document.removeEventListener('fullscreenchange', this.handleFullscreenChange);
        this.toolbar.removeEventListener('pointerdown', this.handleToolbarPointerDown, true);
        this.toolbar.removeEventListener('mousedown', this.handleToolbarPointerDown, true);
        this.xterm.dispose();
    }

    render({ id }: Props, { modal }: State) {
        const { fontSize, inputOwner, isFullscreen } = this;
        const shiftArmed = inputOwner.modifier === 'shift';
        const ctrlArmed = inputOwner.modifier === 'ctrl';
        return (
            <div class="webterm-root">
                <div class="mobile-toolbar" role="toolbar" aria-label="Terminal controls">
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

    @bind
    private handleToolbarPointerDown(event: Event) {
        event.stopPropagation();
        this.xterm.beginToolbarInteraction();
        const target = event.target as Element;
        if (target.closest('.enter-button') && this.xterm.claimRecoveryPointer(event)) return;
        event.preventDefault();
    }
    @bind
    private sendTab() {
        this.xterm.endToolbarInteraction();
        this.xterm.sendTab();
    }

    @bind
    private toggleShift() {
        this.xterm.endToolbarInteraction();
        this.xterm.toggleShift();
    }

    private sendArrow(direction: 'left' | 'up' | 'down' | 'right') {
        this.xterm.endToolbarInteraction();
        this.xterm.sendArrow(direction);
    }

    @bind
    private sendEnter() {
        this.xterm.endToolbarInteraction();
        if (this.xterm.requestRecoveryFromToolbar()) return;
        this.xterm.sendEnter();
    }

    @bind
    private sendEscape() {
        this.xterm.endToolbarInteraction();
        this.xterm.sendEscape();
    }

    @bind
    private toggleCtrl() {
        this.xterm.endToolbarInteraction();
        this.xterm.toggleCtrl();
    }

    private changeFontSize(delta: number) {
        this.xterm.endToolbarInteraction();
        this.xterm.clearModifierForLocalAction();
        const fontSize = clampFontSize(this.fontSize + delta);
        if (fontSize === this.fontSize) return;

        this.fontSize = fontSize;
        try {
            window.localStorage.setItem(FONT_STORAGE_KEY, String(fontSize));
        } catch {
            // Preference persistence is best-effort only.
        }
        this.xterm.setFontSize(fontSize);
    }

    @bind
    private handleInputState(inputOwner: InputOwnerSnapshot) {
        this.inputOwner = inputOwner;
        const shift = this.container?.parentElement?.querySelector('.shift-button');
        const ctrl = this.container?.parentElement?.querySelector('.ctrl-button');
        const shiftArmed = inputOwner.modifier === 'shift';
        const ctrlArmed = inputOwner.modifier === 'ctrl';
        shift?.classList.toggle('active', shiftArmed);
        shift?.setAttribute('aria-pressed', String(shiftArmed));
        ctrl?.classList.toggle('active', ctrlArmed);
        ctrl?.setAttribute('aria-pressed', String(ctrlArmed));
    }

    @bind
    private handleFontSize(fontSize: number) {
        this.fontSize = fontSize;
        this.container?.parentElement
            ?.querySelector('.font-decrease-button')
            ?.setAttribute('aria-label', `Decrease font size; current ${fontSize} pixels`);
        this.container?.parentElement
            ?.querySelector('.font-increase-button')
            ?.setAttribute('aria-label', `Increase font size; current ${fontSize} pixels`);
    }

    @bind
    private handleFullscreenChange() {
        this.isFullscreen = Boolean(document.fullscreenElement);
        const button = this.container?.parentElement?.querySelector('.fullscreen-button');
        button?.classList.toggle('active', this.isFullscreen);
        button?.setAttribute('aria-pressed', String(this.isFullscreen));
        button?.setAttribute('aria-label', this.isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen');
        button?.setAttribute('title', this.isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen');
        this.xterm.fit();
    }

    @bind
    private async toggleFullscreen() {
        this.xterm.clearModifierForLocalAction();
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
