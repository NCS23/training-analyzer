import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock client.ts BEFORE importing chat.ts so the named imports
// resolve to mocks. apiClient is also referenced for baseURL.
vi.mock('./client', () => {
  return {
    apiClient: { defaults: { baseURL: 'http://test' } },
    getAccessToken: vi.fn(),
    refreshAccessTokenOrRedirect: vi.fn(),
    clearTokensAndRedirectToLogin: vi.fn(),
  };
});

import { streamChatMessage } from './chat';
import {
  clearTokensAndRedirectToLogin,
  getAccessToken,
  refreshAccessTokenOrRedirect,
} from './client';

function makeStreamResponse(status: number, body = ''): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, { status });
}

describe('streamChatMessage — Auth + Refresh-Retry (#765)', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    vi.mocked(getAccessToken).mockReset();
    vi.mocked(refreshAccessTokenOrRedirect).mockReset();
    vi.mocked(clearTokensAndRedirectToLogin).mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends Authorization header from getAccessToken (no longer relies on apiClient defaults)', async () => {
    vi.mocked(getAccessToken).mockReturnValue('initial-token');
    fetchMock.mockResolvedValueOnce(makeStreamResponse(200, 'data: {"type":"done"}\n'));

    await streamChatMessage({ message: 'hi' }, () => {});

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0];
    expect((init as RequestInit).headers).toMatchObject({
      Authorization: 'Bearer initial-token',
    });
  });

  it('on 401 refreshes token once and retries with new token', async () => {
    vi.mocked(getAccessToken).mockReturnValue('expired-token');
    vi.mocked(refreshAccessTokenOrRedirect).mockResolvedValueOnce('fresh-token');
    fetchMock
      .mockResolvedValueOnce(makeStreamResponse(401))
      .mockResolvedValueOnce(makeStreamResponse(200, 'data: {"type":"done"}\n'));

    const events: unknown[] = [];
    await streamChatMessage({ message: 'hi' }, (e) => events.push(e));

    expect(refreshAccessTokenOrRedirect).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [, retryInit] = fetchMock.mock.calls[1];
    expect((retryInit as RequestInit).headers).toMatchObject({
      Authorization: 'Bearer fresh-token',
    });
    expect(events).toEqual([{ type: 'done' }]);
  });

  it('on persistent 401 after refresh, clears tokens and redirects', async () => {
    vi.mocked(getAccessToken).mockReturnValue('expired-token');
    vi.mocked(refreshAccessTokenOrRedirect).mockResolvedValueOnce('fresh-token');
    fetchMock
      .mockResolvedValueOnce(makeStreamResponse(401))
      .mockResolvedValueOnce(makeStreamResponse(401));

    await expect(streamChatMessage({ message: 'hi' }, () => {})).rejects.toThrow(/401/);
    expect(clearTokensAndRedirectToLogin).toHaveBeenCalledTimes(1);
  });

  it('on refresh failure, propagates error (refresh helper itself redirects)', async () => {
    vi.mocked(getAccessToken).mockReturnValue('expired-token');
    vi.mocked(refreshAccessTokenOrRedirect).mockRejectedValueOnce(new Error('No refresh token'));
    fetchMock.mockResolvedValueOnce(makeStreamResponse(401));

    await expect(streamChatMessage({ message: 'hi' }, () => {})).rejects.toThrow(
      /No refresh token/,
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('parses multiple data: events from the stream body', async () => {
    vi.mocked(getAccessToken).mockReturnValue('t');
    fetchMock.mockResolvedValueOnce(
      makeStreamResponse(
        200,
        'data: {"type":"start"}\ndata: {"type":"token","content":"Hi"}\ndata: {"type":"done"}\n',
      ),
    );

    const events: unknown[] = [];
    await streamChatMessage({ message: 'hi' }, (e) => events.push(e));
    expect(events).toEqual([{ type: 'start' }, { type: 'token', content: 'Hi' }, { type: 'done' }]);
  });
});
