import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWeeklyReview } from './useWeeklyReview';
import type { WeeklyReview } from '@/api/training';

const MOCK_REVIEW: WeeklyReview = {
  id: 1,
  week_start: '2026-03-16',
  summary: 'Gute Trainingswoche mit solidem Volumen.',
  volume_comparison: {
    planned_km: null,
    actual_km: 42.0,
    planned_sessions: null,
    actual_sessions: 4,
    planned_hours: null,
    actual_hours: 5.5,
  },
  highlights: ['Guter Long Run', 'Konstante Paces'],
  improvements: ['Mehr Stretching'],
  next_week_recommendations: ['Tempolauf einfügen'],
  overall_rating: 'good',
  fatigue_assessment: 'moderate',
  session_count: 4,
  provider: 'Claude (test)',
  cached: false,
  created_at: '2026-03-17T10:00:00',
};

const mockGenerateWeeklyReview = vi.fn();
const mockGetWeeklyReview = vi.fn();

vi.mock('@/api/training', () => ({
  generateWeeklyReview: (...args: unknown[]) => mockGenerateWeeklyReview(...args),
  getWeeklyReview: (...args: unknown[]) => mockGetWeeklyReview(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('useWeeklyReview', () => {
  it('starts with empty state', () => {
    const { result } = renderHook(() => useWeeklyReview());
    expect(result.current.review).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('generate() calls API and sets review', async () => {
    mockGenerateWeeklyReview.mockResolvedValue(MOCK_REVIEW);
    const { result } = renderHook(() => useWeeklyReview());

    await act(async () => {
      await result.current.generate('2026-03-16');
    });

    expect(mockGenerateWeeklyReview).toHaveBeenCalledWith('2026-03-16', false);
    expect(result.current.review).not.toBeNull();
    expect(result.current.review?.summary).toBe('Gute Trainingswoche mit solidem Volumen.');
  });

  it('generate(weekStart, true) passes forceRefresh', async () => {
    mockGenerateWeeklyReview.mockResolvedValue(MOCK_REVIEW);
    const { result } = renderHook(() => useWeeklyReview());

    await act(async () => {
      await result.current.generate('2026-03-16', true);
    });

    expect(mockGenerateWeeklyReview).toHaveBeenCalledWith('2026-03-16', true);
  });

  it('generate() sets error on failure', async () => {
    mockGenerateWeeklyReview.mockRejectedValue(new Error('API Error'));
    const { result } = renderHook(() => useWeeklyReview());

    await act(async () => {
      await result.current.generate('2026-03-16');
    });

    expect(result.current.error).toBe('Wochen-Review konnte nicht generiert werden.');
    expect(result.current.review).toBeNull();
  });

  it('fetch() loads stored review', async () => {
    mockGetWeeklyReview.mockResolvedValue({ ...MOCK_REVIEW, cached: true });
    const { result } = renderHook(() => useWeeklyReview());

    await act(async () => {
      await result.current.fetch('2026-03-16');
    });

    expect(mockGetWeeklyReview).toHaveBeenCalledWith('2026-03-16');
    expect(result.current.review).not.toBeNull();
    expect(result.current.cached).toBe(true);
  });

  it('fetch() silently handles missing review', async () => {
    mockGetWeeklyReview.mockRejectedValue(new Error('404'));
    const { result } = renderHook(() => useWeeklyReview());

    await act(async () => {
      await result.current.fetch('2026-03-16');
    });

    expect(result.current.review).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
