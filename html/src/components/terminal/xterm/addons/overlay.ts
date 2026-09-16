// ported from hterm.Terminal.prototype.showOverlay
// https://chromium.googlesource.com/apps/libapps/+/master/hterm/js/hterm_terminal.js
import { bind } from 'decko';
import { ITerminalAddon, Terminal } from '@xterm/xterm';

interface OverlayChoice {
    label: string;
    action: (event: Event) => void;
}

export class OverlayAddon implements ITerminalAddon {
    private terminal!: Terminal;
    private overlayNode: HTMLElement;
    private overlayTimeout?: number;
    private action?: (event: Event) => void;
    private persistent = false;
    private choiceActions = new Map<HTMLButtonElement, (event: Event) => void>();

    constructor() {
        this.overlayNode = document.createElement('div');
        this.overlayNode.className = 'terminal-overlay';
        this.overlayNode.style.cssText = `border-radius: 15px;
font-size: large;
opacity: 0.9;
padding: 0.6em 0.8em;
position: absolute;
display: flex;
flex-direction: column;
align-items: center;
gap: 0.55em;
max-width: min(90%, 32em);
text-align: center;
z-index: 2;
-webkit-user-select: none;
-webkit-transition: opacity 180ms ease-in;
-moz-user-select: none;
-moz-transition: opacity 180ms ease-in;`;
        this.overlayNode.addEventListener('pointerdown', this.handlePointerDown, true);
        this.overlayNode.addEventListener('click', this.handleClick, true);
    }

    activate(terminal: Terminal): void {
        this.terminal = terminal;
    }

    dispose(): void {
        if (this.overlayTimeout !== undefined) window.clearTimeout(this.overlayTimeout);
        this.overlayTimeout = undefined;
        this.action = undefined;
        this.choiceActions.clear();
        this.overlayNode.removeEventListener('pointerdown', this.handlePointerDown, true);
        this.overlayNode.removeEventListener('click', this.handleClick, true);
        this.overlayNode.remove();
    }

    clearAction(): void {
        this.persistent = false;
        this.action = undefined;
    }

    @bind
    private handlePointerDown(event: PointerEvent) {
        event.preventDefault();
        event.stopPropagation();
        (this.choiceActionFor(event) ?? this.action)?.(event);
    }

    @bind
    private handleClick(event: MouseEvent) {
        event.preventDefault();
        event.stopPropagation();
        if (event.detail === 0) (this.choiceActionFor(event) ?? this.action)?.(event);
    }

    private choiceActionFor(event: Event): ((event: Event) => void) | undefined {
        const target = event.target;
        if (!(target instanceof Element)) return undefined;
        const button = target.closest('button');
        if (!(button instanceof HTMLButtonElement) || button.parentElement !== this.overlayNode) return undefined;
        return this.choiceActions.get(button);
    }

    @bind
    showAction(message: string, label: string, action: (event: Event) => void): void {
        if (this.overlayTimeout !== undefined) window.clearTimeout(this.overlayTimeout);
        this.overlayTimeout = undefined;
        this.persistent = true;
        this.action = action;
        this.render(message, label);
    }

    @bind
    showChoices(message: string, choices: readonly OverlayChoice[]): void {
        if (this.overlayTimeout !== undefined) window.clearTimeout(this.overlayTimeout);
        this.overlayTimeout = undefined;
        this.persistent = true;
        this.action = undefined;
        this.render(message, undefined, choices);
    }

    @bind
    showOverlay(message: string, timeout?: number): void {
        if (this.persistent) return;
        this.action = undefined;
        this.render(message);
        if (this.overlayTimeout !== undefined) window.clearTimeout(this.overlayTimeout);
        if (!timeout) return;

        this.overlayTimeout = window.setTimeout(() => {
            this.overlayNode.style.opacity = '0';
            this.overlayTimeout = window.setTimeout(() => {
                this.overlayNode.remove();
                this.overlayTimeout = undefined;
                this.overlayNode.style.opacity = '0.9';
            }, 200);
        }, timeout);
    }

    private render(message: string, actionLabel?: string, choices: readonly OverlayChoice[] = []) {
        if (!this.terminal.element) return;
        this.overlayNode.style.color = '#101010';
        this.overlayNode.style.backgroundColor = '#f0f0f0';
        this.overlayNode.style.opacity = '0.9';
        this.overlayNode.style.pointerEvents = actionLabel || choices.length > 0 ? 'auto' : 'none';
        this.overlayNode.replaceChildren();
        this.choiceActions.clear();

        const text = document.createElement('span');
        text.textContent = message;
        this.overlayNode.appendChild(text);
        const actions = actionLabel ? [{ label: actionLabel, action: this.action as (event: Event) => void }] : choices;
        for (const choice of actions) {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = choice.label;
            button.style.cssText = 'min-height:34px;padding:0.35em 0.8em;touch-action:manipulation;cursor:pointer';
            if (!actionLabel) this.choiceActions.set(button, choice.action);
            this.overlayNode.appendChild(button);
        }

        if (!this.overlayNode.parentNode) this.terminal.element.appendChild(this.overlayNode);
        const terminalSize = this.terminal.element.getBoundingClientRect();
        const overlaySize = this.overlayNode.getBoundingClientRect();
        this.overlayNode.style.top = (terminalSize.height - overlaySize.height) / 2 + 'px';
        this.overlayNode.style.left = (terminalSize.width - overlaySize.width) / 2 + 'px';
    }
}
