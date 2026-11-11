type Attrs = Record<string, string | number | boolean | undefined>;
type Child = Node | string | number | null | undefined | false;

export interface ElOptions {
  class?: string;
  text?: string;
  html?: string;
  attrs?: Attrs;
  style?: Partial<CSSStyleDeclaration> & Record<string, string>;
  on?: Partial<{ [K in keyof HTMLElementEventMap]: (e: HTMLElementEventMap[K]) => void }>;
}

/** Small DOM builder so panels read like markup. */
export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  opts: ElOptions = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (opts.class) node.className = opts.class;
  if (opts.text !== undefined) node.textContent = opts.text;
  if (opts.html !== undefined) node.innerHTML = opts.html;
  if (opts.attrs) {
    for (const [k, v] of Object.entries(opts.attrs)) {
      if (v === undefined || v === false) continue;
      node.setAttribute(k, v === true ? '' : String(v));
    }
  }
  if (opts.style) {
    for (const [k, v] of Object.entries(opts.style)) {
      if (v === undefined) continue;
      // custom properties (--accent) need setProperty; Object.assign drops them
      if (k.startsWith('--')) node.style.setProperty(k, String(v));
      else (node.style as unknown as Record<string, string>)[k] = String(v);
    }
  }
  if (opts.on) {
    for (const [k, fn] of Object.entries(opts.on)) node.addEventListener(k, fn as EventListener);
  }
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : String(c));
  }
  return node;
}

export function icon(src: string, alt = '', cls = 'px-icon'): HTMLImageElement {
  return el('img', { class: cls, attrs: { src, alt, draggable: 'false' } });
}

export function button(label: Child | Child[], onClick: () => void, cls = 'btn'): HTMLButtonElement {
  const parts = Array.isArray(label) ? label : [label];
  return el('button', { class: cls, attrs: { type: 'button' }, on: { click: () => onClick() } }, ...parts);
}

export function clear(node: Element) {
  while (node.firstChild) node.firstChild.remove();
}
