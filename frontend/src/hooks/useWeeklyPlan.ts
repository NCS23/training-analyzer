/**
 * Hook for weekly plan data, editing, saving, and deletion.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useToast } from '@nordlig/components';
import {
  getWeeklyPlan,
  saveWeeklyPlan,
  syncToPlan,
  getCompliance,
  clearWeeklyPlan,
} from '@/api/weekly-plan';
import type { WeeklyPlanEntry, ComplianceResponse } from '@/api/weekly-plan';
import { getMondayOfWeek, addWeeks } from '@/utils/weeklyPlanUtils';

// eslint-disable-next-line max-lines-per-function -- consolidated weekly plan hook
export function useWeeklyPlan() {
  const { toast } = useToast();

  const [weekStart, setWeekStart] = useState(() => getMondayOfWeek(new Date()));
  const [entries, setEntries] = useState<WeeklyPlanEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [compliance, setCompliance] = useState<ComplianceResponse | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showSyncBar, setShowSyncBar] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // --- Load ---

  const loadWeek = useCallback(
    async (ws: string) => {
      setLoading(true);
      setError(null);
      setShowSyncBar(false);
      try {
        const [planResult, complianceResult] = await Promise.all([
          getWeeklyPlan(ws),
          getCompliance(ws).catch(() => null),
        ]);
        setEntries(planResult.entries);
        setCompliance(complianceResult);
        setDirty(false);
      } catch {
        toast({ title: 'Laden fehlgeschlagen', variant: 'error' });
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    loadWeek(weekStart);
  }, [weekStart, loadWeek]);

  const navigateWeek = useCallback((direction: -1 | 1) => {
    setWeekStart((prev) => addWeeks(prev, direction));
  }, []);

  const goToCurrentWeek = useCallback(() => {
    setWeekStart(getMondayOfWeek(new Date()));
  }, []);

  // --- Day editing ---

  const updateEntry = useCallback((dayOfWeek: number, updates: Partial<WeeklyPlanEntry>) => {
    setEntries((prev) => prev.map((e) => (e.day_of_week === dayOfWeek ? { ...e, ...updates } : e)));
    setDirty(true);
  }, []);

  const handleMoveSession = useCallback(
    (fromDay: number, sessionIdx: number, targetDay: number) => {
      setEntries((prev) => {
        const next = prev.map((e) => ({ ...e, sessions: [...e.sessions] }));
        const source = next.find((e) => e.day_of_week === fromDay);
        const target = next.find((e) => e.day_of_week === targetDay);
        if (!source || !target || !source.sessions[sessionIdx]) return prev;

        const [moved] = source.sessions.splice(sessionIdx, 1);
        source.sessions.forEach((s, i) => {
          s.position = i;
        });
        moved.position = target.sessions.length;
        target.sessions.push(moved);
        if (target.is_rest_day) target.is_rest_day = false;
        return next;
      });
      setDirty(true);
    },
    [],
  );

  const handleMoveRestDay = useCallback((fromDay: number, targetDay: number) => {
    setEntries((prev) => {
      const next = prev.map((e) => ({ ...e, sessions: [...e.sessions] }));
      const source = next.find((e) => e.day_of_week === fromDay);
      const target = next.find((e) => e.day_of_week === targetDay);
      if (!source || !target) return prev;

      const movedNotes = source.notes;
      source.is_rest_day = false;
      source.notes = null;
      target.is_rest_day = true;
      target.sessions = [];
      target.notes = movedNotes;
      return next;
    });
    setDirty(true);
  }, []);

  // --- Save ---

  const doSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const nonEmptyEntries = entries.filter(
        (e) => e.sessions.length > 0 || e.is_rest_day || e.notes,
      );
      if (nonEmptyEntries.length === 0) {
        toast({ title: 'Keine Einträge zum Speichern', variant: 'warning' });
        setSaving(false);
        return;
      }
      const result = await saveWeeklyPlan({
        week_start: weekStart,
        entries: nonEmptyEntries.map((e) => ({
          day_of_week: e.day_of_week,
          is_rest_day: e.is_rest_day,
          notes: e.notes,
          sessions: e.sessions,
        })),
      });
      setEntries(result.entries);
      setDirty(false);
      return result;
    } catch {
      setError('Speichern fehlgeschlagen.');
      return null;
    } finally {
      setSaving(false);
    }
  }, [entries, weekStart, toast]);

  const handleSaveWeekOnly = useCallback(async () => {
    const result = await doSave();
    if (result) {
      toast({ title: 'Wochenplan gespeichert', variant: 'success' });
      const hasEditedPlanEntries = result.entries.some((e) => e.plan_id != null && e.edited);
      setShowSyncBar(hasEditedPlanEntries);
    }
  }, [doSave, toast]);

  const handleSaveAndSync = useCallback(
    async (applyToAll: boolean) => {
      const result = await doSave();
      if (!result) return;

      const planId = result.entries.find((e) => e.plan_id != null)?.plan_id;
      if (!planId) {
        toast({ title: 'Wochenplan gespeichert', variant: 'success' });
        return;
      }

      try {
        const syncResult = await syncToPlan({
          week_start: weekStart,
          plan_id: planId,
          apply_to_all_weeks: applyToAll,
        });
        toast({
          title: `Gespeichert & in Phase "${syncResult.phase_name}" übernommen`,
          description: applyToAll
            ? 'Alle Wochen der Phase aktualisiert'
            : `Woche ${syncResult.week_key} aktualisiert`,
          variant: 'success',
        });
        setShowSyncBar(false);
      } catch {
        toast({ title: 'Gespeichert, aber Sync fehlgeschlagen', variant: 'warning' });
        setShowSyncBar(true);
      }
    },
    [doSave, weekStart, toast],
  );

  const handleSaveClick = useCallback(() => {
    const isPlanLinked = entries.some((e) => e.plan_id != null);
    if (isPlanLinked && dirty) {
      setShowSaveDialog(true);
    } else {
      handleSaveWeekOnly();
    }
  }, [entries, dirty, handleSaveWeekOnly]);

  // --- Delete ---

  const handleDeleteWeek = useCallback(async () => {
    setDeleting(true);
    try {
      await clearWeeklyPlan(weekStart);
      toast({ title: 'Wochenplan gelöscht', variant: 'success' });
      await loadWeek(weekStart);
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
      setShowDeleteDialog(false);
    }
  }, [weekStart, toast, loadWeek]);

  // --- Stats ---

  const stats = useMemo(() => {
    let strength = 0;
    let running = 0;
    let rest = 0;
    let totalMinutes = 0;
    for (const e of entries) {
      if (e.is_rest_day) {
        rest++;
      } else {
        for (const s of e.sessions) {
          if (s.training_type === 'strength') strength++;
          else if (s.training_type === 'running') {
            running++;
            // eslint-disable-next-line max-depth
            if (s.run_details?.target_duration_minutes) {
              totalMinutes += s.run_details.target_duration_minutes;
            }
          }
        }
      }
    }
    return { strength, running, rest, totalMinutes };
  }, [entries]);

  const isCurrentWeek = weekStart === getMondayOfWeek(new Date());
  const hasContent = entries.some((e) => e.sessions.length > 0 || e.is_rest_day);
  const linkedPlanId = entries.find((e) => e.plan_id != null)?.plan_id ?? null;
  const editedPlanCount = entries.filter((e) => e.plan_id != null && e.edited).length;

  return {
    weekStart,
    entries,
    loading,
    saving,
    error,
    dirty,
    compliance,
    showDeleteDialog,
    setShowDeleteDialog,
    deleting,
    showSyncBar,
    setShowSyncBar,
    showSaveDialog,
    setShowSaveDialog,
    navigateWeek,
    goToCurrentWeek,
    updateEntry,
    handleMoveSession,
    handleMoveRestDay,
    handleSaveWeekOnly,
    handleSaveAndSync,
    handleSaveClick,
    handleDeleteWeek,
    stats,
    isCurrentWeek,
    hasContent,
    linkedPlanId,
    editedPlanCount,
    loadWeek,
  };
}
