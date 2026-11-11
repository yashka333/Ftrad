import type { PathId } from '@frog-traders/shared';

export type Route =
  | { name: 'menu' }
  | { name: 'work' }
  | { name: 'office'; path: PathId }
  | { name: 'frogs' }
  | { name: 'shop' }
  | { name: 'fusion' }
  | { name: 'market' };

type Listener = (r: Route) => void;

/** Screen navigation with a back stack, like the pages in Mini Hero. */
export class Router {
  private stack: Route[] = [{ name: 'menu' }];
  private listeners = new Set<Listener>();

  get current(): Route {
    return this.stack[this.stack.length - 1]!;
  }

  get canGoBack(): boolean {
    return this.stack.length > 1;
  }

  onChange(fn: Listener): void {
    this.listeners.add(fn);
  }

  go(r: Route): void {
    if (r.name === 'menu') this.stack = [r];
    else this.stack.push(r);
    this.emit();
  }

  back(): void {
    if (this.stack.length > 1) this.stack.pop();
    this.emit();
  }

  private emit() {
    for (const fn of this.listeners) fn(this.current);
  }
}

export const ROUTE_TITLES: Record<Route['name'], string> = {
  menu: '',
  work: 'Go to work',
  office: '',
  frogs: 'My frogs',
  shop: 'Shop',
  fusion: 'Fusion',
  market: 'Market',
};
