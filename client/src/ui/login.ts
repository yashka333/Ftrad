import type { PublicState } from '@frog-traders/shared';
import { api } from '../api/client';
import { Flicker } from '../game/animations/flicker';
import { url } from '../game/assets';
import { el } from './components/el';

/** Title screen: the crossroads with flickering signs and a name field. */
export function showLogin(host: HTMLElement): Promise<PublicState> {
  return new Promise((resolve) => {
    const overlays = (['left', 'center', 'right'] as const).map((k) =>
      el('img', { class: 'hub-layer', attrs: { src: url(`scenes/hub-sign-${k}-off`), alt: '' }, style: { opacity: '0' } }),
    );
    const flickers = overlays.map((img) => new Flicker((lit) => (img.style.opacity = lit ? '0' : '1')));
    let raf = 0;
    const loop = () => {
      const now = performance.now();
      for (const f of flickers) f.update(now);
      raf = requestAnimationFrame(loop);
    };
    loop();

    const input = el('input', {
      class: 'input',
      attrs: { id: 'player-name', type: 'text', maxlength: 20, minlength: 3, required: true, placeholder: 'Your trader name', autocomplete: 'nickname' },
    });
    const error = el('p', { class: 'form-error', attrs: { role: 'alert' } });
    const submit = el('button', { class: 'btn btn-main btn-big', attrs: { type: 'submit' }, text: 'Start trading' });
    const form = el(
      'form',
      { class: 'login-form' },
      el('label', { class: 'label', attrs: { for: 'player-name' }, text: 'Name' }),
      input,
      submit,
      error,
      el('p', { class: 'fine', text: 'Stage 1 test build: name login and test tokens. Phantom login comes next.' }),
    );
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      submit.disabled = true;
      error.textContent = '';
      try {
        const s = await api.login(input.value);
        cancelAnimationFrame(raf);
        screen.remove();
        resolve(s);
      } catch (err) {
        error.textContent = err instanceof Error ? err.message : 'Could not log in.';
        submit.disabled = false;
      }
    });

    const screen = el(
      'div',
      { class: 'login' },
      el('div', { class: 'hub' }, el('img', { class: 'hub-base', attrs: { src: url('scenes/hub'), alt: 'A frog in a trench coat facing three trading houses' } }), ...overlays),
      el(
        'div',
        { class: 'login-card' },
        el('img', { class: 'logo big', attrs: { src: url('ui/logo'), alt: 'Frog Traders' } }),
        el('p', { class: 'tagline', text: 'Summon frogs. Send them to trade. Collect while you sleep.' }),
        form,
      ),
    );
    host.append(screen);
    input.focus();
  });
}
