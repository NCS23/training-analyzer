/**
 * Hook for weekly plan drag-and-drop interactions.
 */
import { useState, useCallback } from 'react';
import {
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import type { WeeklyPlanEntry } from '@/api/weekly-plan';

interface UseWeeklyPlanDragDropOptions {
  entries: WeeklyPlanEntry[];
  onMoveSession: (fromDay: number, sessionIdx: number, targetDay: number) => void;
  onMoveRestDay: (fromDay: number, targetDay: number) => void;
}

export function useWeeklyPlanDragDrop({
  entries,
  onMoveSession,
  onMoveRestDay,
}: UseWeeklyPlanDragDropOptions) {
  const [activeDragData, setActiveDragData] = useState<{
    type: 'session' | 'rest';
    day: number;
    idx: number;
  } | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
    useSensor(TouchSensor, {
      activationConstraint: { delay: 200, tolerance: 5 },
    }),
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const data = event.active.data.current as
      | { type: 'session'; dayOfWeek: number; sessionIdx: number }
      | { type: 'rest'; dayOfWeek: number }
      | undefined;
    if (!data) return;
    if (data.type === 'rest') {
      setActiveDragData({ type: 'rest', day: data.dayOfWeek, idx: -1 });
    } else {
      setActiveDragData({ type: 'session', day: data.dayOfWeek, idx: data.sessionIdx });
    }
  }, []);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      setActiveDragData(null);
      const { active, over } = event;
      if (!over) return;

      const data = active.data.current as
        | { type: 'session'; dayOfWeek: number; sessionIdx: number }
        | { type: 'rest'; dayOfWeek: number }
        | undefined;
      const overId = String(over.id);
      const targetMatch = overId.match(/^day-(\d+)$/);

      if (data && targetMatch) {
        const targetDay = parseInt(targetMatch[1]);
        if (data.dayOfWeek !== targetDay) {
          if (data.type === 'rest') {
            onMoveRestDay(data.dayOfWeek, targetDay);
          } else {
            onMoveSession(data.dayOfWeek, data.sessionIdx, targetDay);
          }
        }
      }
    },
    [onMoveSession, onMoveRestDay],
  );

  const activeDragSession =
    activeDragData?.type === 'session'
      ? entries.find((e) => e.day_of_week === activeDragData.day)?.sessions[activeDragData.idx]
      : null;

  return {
    sensors,
    activeDragData,
    activeDragSession,
    handleDragStart,
    handleDragEnd,
  };
}
