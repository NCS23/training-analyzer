/**
 * Hook für Segment-Editing auf einer Route (#532).
 * Verwaltet RouteSegments und bietet Auto-Segmentierung.
 */

import { useState, useCallback } from 'react';
import type { RouteSegment } from '@/api/routes';

export interface UseSegmentEditorReturn {
  segments: RouteSegment[];
  activeSegment: number | null;
  setSegments: (segments: RouteSegment[]) => void;
  addSegment: () => void;
  updateSegment: (index: number, segment: RouteSegment) => void;
  deleteSegment: (index: number) => void;
  setActiveSegment: (index: number | null) => void;
  autoSegment: (distanceKm: number) => void;
}

/** Standard-Aufteilung: 15% Warmup, 70% Steady, 15% Cooldown. */
function createDefaultSegments(distanceKm: number): RouteSegment[] {
  if (distanceKm <= 0) return [];

  const warmupEnd = Math.round(distanceKm * 0.15 * 10) / 10;
  const cooldownStart = Math.round(distanceKm * 0.85 * 10) / 10;

  return [
    { segment_type: 'warmup', start_km: 0, end_km: warmupEnd },
    { segment_type: 'steady', start_km: warmupEnd, end_km: cooldownStart },
    { segment_type: 'cooldown', start_km: cooldownStart, end_km: Math.round(distanceKm * 10) / 10 },
  ];
}

export function useSegmentEditor(initialSegments: RouteSegment[] = []): UseSegmentEditorReturn {
  const [segments, setSegmentsState] = useState<RouteSegment[]>(initialSegments);
  const [activeSegment, setActiveSegment] = useState<number | null>(null);

  const setSegments = useCallback((segs: RouteSegment[]) => {
    setSegmentsState(segs);
  }, []);

  const addSegment = useCallback(() => {
    setSegmentsState((prev) => {
      if (prev.length === 0) return prev;

      // Teile letztes Segment in der Mitte
      const last = prev[prev.length - 1];
      const mid = Math.round(((last.start_km + last.end_km) / 2) * 10) / 10;
      if (mid <= last.start_km || mid >= last.end_km) return prev;

      const updated = [...prev];
      updated[prev.length - 1] = { ...last, end_km: mid };
      updated.push({ segment_type: 'steady', start_km: mid, end_km: last.end_km });
      return updated;
    });
  }, []);

  const updateSegment = useCallback((index: number, segment: RouteSegment) => {
    setSegmentsState((prev) => {
      const updated = [...prev];
      updated[index] = segment;
      return updated;
    });
  }, []);

  const deleteSegment = useCallback((index: number) => {
    setSegmentsState((prev) => {
      if (prev.length <= 1) return [];

      const updated = [...prev];
      const removed = updated.splice(index, 1)[0];

      // Nachbar-Segment erweitern um die Lücke zu füllen
      if (index > 0) {
        updated[index - 1] = { ...updated[index - 1], end_km: removed.end_km };
      } else if (updated.length > 0) {
        updated[0] = { ...updated[0], start_km: removed.start_km };
      }

      return updated;
    });
    setActiveSegment(null);
  }, []);

  const autoSegment = useCallback((distanceKm: number) => {
    setSegmentsState(createDefaultSegments(distanceKm));
    setActiveSegment(null);
  }, []);

  return {
    segments,
    activeSegment,
    setSegments,
    addSegment,
    updateSegment,
    deleteSegment,
    setActiveSegment,
    autoSegment,
  };
}
