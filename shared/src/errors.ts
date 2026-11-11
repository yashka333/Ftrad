export const ERRORS = {
  'unauthorized': 'Log in to play.',
  'invalid-request': 'Something in that request was off. Try again.',
  'not-found': 'Not found.',
  'bad-name': 'Use 3 to 20 letters, digits, spaces, dots or dashes.',
  'frog-not-found': 'Frog not found.',
  'insufficient-token': 'Not enough FROG in your wallet.',
  'frog-limit': 'You can hold up to 500 frogs.',
  'bad-pack': 'That pack size is not on sale.',
  'office-full': 'All 5 desks in this office are taken.',
  'desk-taken': 'Another frog already sits at this desk.',
  'bad-desk': 'That desk does not exist.',
  'no-desk': 'Give this frog a desk first.',
  'too-tired': 'This frog is out of stamina. Let it rest first.',
  'already-working': 'This frog is already working.',
  'already-resting': 'This frog is already resting.',
  'casino-not-found': 'Casino not found.',
  'sold-out': 'Sold out: none left.',
  'no-boss': 'Get a Boss Frog first.',
  'below-withdrawal-minimum': 'Withdraw from 100,000 FROG in the chest.',
  'withdrawal-too-soon': 'One withdrawal a day: the next one opens later.',
  'wallet-below-minimum': 'Your wallet must hold 2,500 FROG to withdraw.',
  'dev-only': 'Only available in dev mode.',
  'no-free-packs': 'No free packs to open.',
  'not-tradeable': 'Only Legendary and Mythic frogs can be traded.',
  'bad-price': 'Set a price from 1,000 to 1,000,000,000 FROG.',
  'too-many-listings': 'You can list up to 20 frogs at once.',
  'listing-not-found': 'This frog is no longer on sale.',
  'not-your-listing': 'This is not your listing.',
  'own-listing': 'You cannot buy your own frog.',
  'bad-signature': 'Wallet signature check failed. Try connecting again.',
  'nonce-expired': 'The sign-in request expired. Connect again.',
  'rate-limited': 'Too many requests at once. Wait a moment.',
  'internal': 'Something went wrong. Try again.',
} as const;

export type ErrorCode = keyof typeof ERRORS;

export class GameError extends Error {
  constructor(public code: ErrorCode, public status = 400) {
    super(ERRORS[code]);
  }
}

export function errorMessage(code: string): string {
  return (ERRORS as Record<string, string>)[code] ?? ERRORS.internal;
}
