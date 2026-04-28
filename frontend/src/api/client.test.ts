import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Install an in-memory localStorage BEFORE importing client.ts.
// jsdom in this project's setup provides a partial Storage that doesn't
// expose removeItem reliably under spies, so we replace it cleanly.
const memoryStore = new Map<string, string>();
const memoryStorage = {
  getItem: (k: string) => memoryStore.get(k) ?? null,
  setItem: (k: string, v: string) => {
    memoryStore.set(k, v);
  },
  removeItem: (k: string) => {
    memoryStore.delete(k);
  },
  clear: () => memoryStore.clear(),
  key: (i: number) => Array.from(memoryStore.keys())[i] ?? null,
  get length() {
    return memoryStore.size;
  },
};
Object.defineProperty(globalThis, 'localStorage', {
  value: memoryStorage,
  configurable: true,
  writable: true,
});

import { clearTokensAndRedirectToLogin } from './client';

describe('clearTokensAndRedirectToLogin (#769)', () => {
  let originalLocation: Location;

  beforeEach(() => {
    memoryStore.clear();
    memoryStore.set('ta_access_token', 'a');
    memoryStore.set('ta_refresh_token', 'r');
    memoryStore.set('training-analyzer-auth', '{"state":{"accessToken":"a","refreshToken":"r"}}');
    originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: { pathname: '/chat', href: 'http://test/chat' },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
    memoryStore.clear();
    vi.restoreAllMocks();
  });

  it('clears flat ta_access_token, ta_refresh_token AND zustand persist-store key', () => {
    clearTokensAndRedirectToLogin();
    expect(memoryStore.has('ta_access_token')).toBe(false);
    expect(memoryStore.has('ta_refresh_token')).toBe(false);
    // Critical for #769: without this, zustand rehydrates an invalid token
    // and the user lands on /login → NotFoundPage instead of the login screen.
    expect(memoryStore.has('training-analyzer-auth')).toBe(false);
  });

  it('navigates to /login when not already there', () => {
    clearTokensAndRedirectToLogin();
    expect((window.location as { href: string }).href).toBe('/login');
  });

  it('does not redirect when already on /login (avoids redirect loop)', () => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: { pathname: '/login', href: 'http://test/login' },
    });
    clearTokensAndRedirectToLogin();
    expect((window.location as { href: string }).href).toBe('http://test/login');
  });
});
