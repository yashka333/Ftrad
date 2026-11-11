import { el } from '../components/el';

/** Pages that are designed next. */
export function renderPlaceholder(host: HTMLElement, title: string, text: string) {
  host.append(el('div', { class: 'placeholder panel' }, el('h2', { class: 'panel-title', text: title }), el('p', { class: 'panel-sub', text })));
}
