import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useRecommendations } from './useRecommendations';
import type { RecommendationsList, AIRecommendation } from '@/api/training';

const MOCK_RECOMMENDATION: AIRecommendation = {
  id: 1,
  session_id: 42,
  type: 'adjust_pace',
  title: 'Long Run Tempo reduzieren',
  target_session_id: null,
  current_value: '5:20 min/km',
  suggested_value: '5:40 min/km',
  reasoning: 'Die HF war im oberen Zone-2-Bereich.',
  priority: 'high',
  status: 'pending',
  created_at: '2026-03-17T10:00:00',
};

const MOCK_RESPONSE: RecommendationsList = {
  recommendations: [MOCK_RECOMMENDATION],
  session_id: 42,
  provider: 'Claude (test)',
  cached: false,
};

const mockGenerateRecommendations = vi.fn();
const mockGetRecommendations = vi.fn();
const mockUpdateRecommendationStatus = vi.fn();

vi.mock('@/api/training', () => ({
  generateRecommendations: (...args: unknown[]) => mockGenerateRecommendations(...args),
  getRecommendations: (...args: unknown[]) => mockGetRecommendations(...args),
  updateRecommendationStatus: (...args: unknown[]) => mockUpdateRecommendationStatus(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useRecommendations', () => {
  it('starts with empty state', () => {
    const { result } = renderHook(() => useRecommendations(42));

    expect(result.current.recommendations).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.pendingCount).toBe(0);
  });

  it('generate() calls API and sets recommendations', async () => {
    mockGenerateRecommendations.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useRecommendations(42));

    await act(async () => {
      await result.current.generate();
    });

    expect(mockGenerateRecommendations).toHaveBeenCalledWith(42, false);
    expect(result.current.recommendations).toHaveLength(1);
    expect(result.current.recommendations[0].title).toBe('Long Run Tempo reduzieren');
    expect(result.current.pendingCount).toBe(1);
  });

  it('generate(true) passes forceRefresh', async () => {
    mockGenerateRecommendations.mockResolvedValue(MOCK_RESPONSE);
    const { result } = renderHook(() => useRecommendations(42));

    await act(async () => {
      await result.current.generate(true);
    });

    expect(mockGenerateRecommendations).toHaveBeenCalledWith(42, true);
  });

  it('generate() sets error on failure', async () => {
    mockGenerateRecommendations.mockRejectedValue(new Error('API Error'));
    const { result } = renderHook(() => useRecommendations(42));

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.error).toBe('Empfehlungen konnten nicht generiert werden.');
    expect(result.current.recommendations).toEqual([]);
  });

  it('fetch() loads stored recommendations', async () => {
    mockGetRecommendations.mockResolvedValue({ ...MOCK_RESPONSE, cached: true });
    const { result } = renderHook(() => useRecommendations(42));

    await act(async () => {
      await result.current.fetch();
    });

    expect(mockGetRecommendations).toHaveBeenCalledWith(42);
    expect(result.current.recommendations).toHaveLength(1);
    expect(result.current.cached).toBe(true);
  });

  it('fetch() silently handles missing recommendations', async () => {
    mockGetRecommendations.mockRejectedValue(new Error('404'));
    const { result } = renderHook(() => useRecommendations(42));

    await act(async () => {
      await result.current.fetch();
    });

    expect(result.current.recommendations).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('updateStatus() updates single recommendation', async () => {
    mockGenerateRecommendations.mockResolvedValue(MOCK_RESPONSE);
    mockUpdateRecommendationStatus.mockResolvedValue({
      ...MOCK_RECOMMENDATION,
      status: 'dismissed',
    });

    const { result } = renderHook(() => useRecommendations(42));

    await act(async () => {
      await result.current.generate();
    });

    await act(async () => {
      await result.current.updateStatus(1, 'dismissed');
    });

    await waitFor(() => {
      expect(result.current.recommendations[0].status).toBe('dismissed');
      expect(result.current.pendingCount).toBe(0);
    });
  });
});
