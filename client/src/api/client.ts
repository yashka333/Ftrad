import { errorMessage, type PathId, type PublicState } from '@frog-traders/shared';

export class ApiError extends Error {
  constructor(public code: string, message: string, public status: number) {
    super(message);
  }
}

async function request<T>(method: 'GET' | 'POST', url: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, {
      method,
      credentials: 'same-origin',
      headers: body !== undefined ? { 'content-type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError('network', 'No connection. Try again in a moment.', 0);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const code = (data as { error?: string }).error ?? 'internal';
    throw new ApiError(code, errorMessage(code), res.status);
  }
  return data as T;
}

export interface CommandResult<T = unknown> {
  result: T;
  state: PublicState;
}

/** Every endpoint the game uses, in one place. */
export const api = {
  health: () => request<{ status: string; devMode?: boolean }>('GET', '/api/health'),
  state: () => request<PublicState>('GET', '/api/state'),
  login: (name: string) => request<PublicState>('POST', '/api/session', { name }),
  signOut: () => request<{ ok: true }>('POST', '/api/session/sign-out', {}),
  summon: (count: number) => request<CommandResult<PublicState['player']['frogs']>>('POST', '/api/packs/open', { count }),
  assign: (frogId: number, path: PathId, desk: number) =>
    request<CommandResult>('POST', '/api/frogs/go-work', { frogId, path, desk }),
  stop: (frogId: number) => request<CommandResult>('POST', '/api/frogs/stop', { frogId }),
  work: (frogId: number) => request<CommandResult>('POST', '/api/frogs/work', { frogId }),
  rest: (frogId: number) => request<CommandResult>('POST', '/api/frogs/rest', { frogId }),
  autoSeat: () => request<CommandResult<number>>('POST', '/api/frogs/auto-seat', {}),
  buyBoss: () => request<CommandResult>('POST', '/api/boss/buy', {}),
  switchBoss: (on: boolean) => request<CommandResult>('POST', '/api/boss/switch', { on }),
  withdraw: () => request<CommandResult>('POST', '/api/withdrawals', {}),
  faucet: () => request<CommandResult>('POST', '/api/dev/faucet', {}),
};
