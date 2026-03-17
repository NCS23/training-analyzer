import { useState, useCallback } from 'react';
import type { WeeklyReview } from '@/api/training';
import { generateWeeklyReview, getWeeklyReview } from '@/api/training';

interface UseWeeklyReviewReturn {
  review: WeeklyReview | null;
  loading: boolean;
  error: string | null;
  cached: boolean;
  generate: (weekStart: string, forceRefresh?: boolean) => Promise<void>;
  fetch: (weekStart: string) => Promise<void>;
}

export function useWeeklyReview(): UseWeeklyReviewReturn {
  const [review, setReview] = useState<WeeklyReview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cached, setCached] = useState(false);

  const generate = useCallback(async (weekStart: string, forceRefresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const result = await generateWeeklyReview(weekStart, forceRefresh);
      setReview(result);
      setCached(result.cached);
    } catch {
      setError('Wochen-Review konnte nicht generiert werden.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetch = useCallback(async (weekStart: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getWeeklyReview(weekStart);
      setReview(result);
      setCached(result.cached);
    } catch {
      // Kein gespeichertes Review — kein Fehler
      setReview(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    review,
    loading,
    error,
    cached,
    generate,
    fetch,
  };
}
