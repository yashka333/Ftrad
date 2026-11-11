import { el } from './el';

export function toast(message: string, kind: 'info' | 'error' | 'success' = 'info') {
  const root = document.getElementById('toast-root');
  if (!root) return;
  const t = el('div', { class: `toast toast-${kind}`, text: message, attrs: { role: 'status' } });
  root.append(t);
  requestAnimationFrame(() => t.classList.add('show'));
  window.setTimeout(() => {
    t.classList.remove('show');
    window.setTimeout(() => t.remove(), 300);
  }, kind === 'error' ? 4200 : 2800);
}
