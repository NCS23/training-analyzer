import { useState, useCallback } from 'react';
import type {
  AIRecommendation,
  RecommendationsList,
  RecommendationStatusValue,
} from '@/api/training';
import {
  generateRecommendations,
  getRecommendations,
  updateRecommendationStatus,
} from '@/api/training';

interface UseRecommendationsReturn {
  recommendations: AIRecommendation[];
  loading: boolean;
  error: string | null;
  cached: boolean;
  provider: string | null;
  generate: (forceRefresh?: boolean) => Promise<void>;
  fetch: () => Promise<void>;
  updateStatus: (id: number, status: RecommendationStatusValue) => Promise<void>;
  pendingCount: number;
}

export function useRecommendations(sessionId: number): UseRecommendationsReturn {
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cached, setCached] = useState(false);
  const [provider, setProvider] = useState<string | null>(null);

  const applyResult = useCallback((result: RecommendationsList) => {
    setRecommendations(result.recommendations);
    setCached(result.cached);
    setProvider(result.provider);
  }, []);

  const generate = useCallback(
    async (forceRefresh = false) => {
      setLoading(true);
      setError(null);
      try {
        const result = await generateRecommendations(sessionId, forceRefresh);
        applyResult(result);
      } catch {
        setError('Empfehlungen konnten nicht generiert werden.');
      } finally {
        setLoading(false);
      }
    },
    [sessionId, applyResult],
  );

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getRecommendations(sessionId);
      applyResult(result);
    } catch {
      // Keine gespeicherten Empfehlungen — kein Fehler anzeigen
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }, [sessionId, applyResult]);

  const updateStatus = useCallback(async (id: number, status: RecommendationStatusValue) => {
    try {
      const updated = await updateRecommendationStatus(id, status);
      setRecommendations((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch {
      setError('Status-Update fehlgeschlagen.');
    }
  }, []);

  const pendingCount = recommendations.filter((r) => r.status === 'pending').length;

  return {
    recommendations,
    loading,
    error,
    cached,
    provider,
    generate,
    fetch,
    updateStatus,
    pendingCount,
  };
}
