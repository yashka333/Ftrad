import { el, icon, clear } from './el';
import { url } from '../../game/assets';

export interface Modal {
  body: HTMLElement;
  close(): void;
  setTitle(t: string): void;
}

let current: Modal | null = null;

/** Opens a pixel-framed window. Only one is open at a time. */
export function openModal(
  title: string,
  iconKey: string | null,
  opts: { wide?: boolean; onClose?: () => void } = {},
): Modal {
  current?.close();
  const root = document.getElementById('modal-root')!;
  const titleEl = el('h2', { class: 'modal-title', text: title });
  const body = el('div', { class: 'modal-body' });
  const closeBtn = el('button', { class: 'modal-close', attrs: { type: 'button', 'aria-label': 'Close' }, text: 'X' });
  const win = el(
    'section',
    { class: `modal${opts.wide ? ' modal-wide' : ''}`, attrs: { role: 'dialog', 'aria-modal': 'true', 'aria-label': title } },
    el('header', { class: 'modal-head' }, iconKey ? icon(url(iconKey), '', 'px-icon modal-icon') : null, titleEl, closeBtn),
    body,
  );
  const backdrop = el('div', { class: 'modal-backdrop' }, win);
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Escape') m.close();
  };
  const m: Modal = {
    body,
    close() {
      document.removeEventListener('keydown', onKey);
      backdrop.remove();
      if (current === m) current = null;
      opts.onClose?.();
    },
    setTitle(t) {
      titleEl.textContent = t;
    },
  };
  closeBtn.addEventListener('click', () => m.close());
  backdrop.addEventListener('pointerdown', (e) => {
    if (e.target === backdrop) m.close();
  });
  document.addEventListener('keydown', onKey);
  clear(root);
  root.append(backdrop);
  current = m;
  closeBtn.focus({ preventScroll: true });
  return m;
}

export function closeModal() {
  current?.close();
}
