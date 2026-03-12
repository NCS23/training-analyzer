/**
 * Hook for linking uploads to planned sessions by date.
 */
import { useState, useEffect } from 'react';
import { getPlannedSessionsForDate } from '@/api/weekly-plan';
import type { PlannedSessionOption } from '@/api/weekly-plan';

export function usePlannedSessionLinking(trainingDate: Date) {
  const [plannedSessions, setPlannedSessions] = useState<PlannedSessionOption[]>([]);
  const [selectedPlannedId, setSelectedPlannedId] = useState<number | null>(null);

  useEffect(() => {
    const dateStr = trainingDate.toISOString().split('T')[0];
    getPlannedSessionsForDate(dateStr)
      .then(setPlannedSessions)
      .catch(() => setPlannedSessions([]));
    setSelectedPlannedId(null);
  }, [trainingDate]);

  return { plannedSessions, selectedPlannedId, setSelectedPlannedId };
}
