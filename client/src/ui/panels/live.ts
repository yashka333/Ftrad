import type { Store } from '../../state/store';
import { clear } from '../components/el';
import { openModal, type Modal } from '../components/modal';

/** Opens a modal whose body re-renders every time new state arrives. */
export function livePanel(
  store: Store,
  title: string,
  iconKey: string | null,
  render: (body: HTMLElement, m: Modal) => void,
  opts: { wide?: boolean } = {},
): Modal {
  let unsub = () => {};
  const m = openModal(title, iconKey, { ...opts, onClose: () => unsub() });
  const draw = () => {
    const scroll = m.body.scrollTop;
    clear(m.body);
    render(m.body, m);
    m.body.scrollTop = scroll;
  };
  let first = true;
  unsub = store.subscribe(() => {
    if (first) {
      first = false;
      draw();
      return;
    }
    draw();
  });
  return m;
}
