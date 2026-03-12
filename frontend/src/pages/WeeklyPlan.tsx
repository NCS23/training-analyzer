import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  Card,
  CardBody,
  Button,
  Spinner,
  Alert,
  AlertDescription,
  useToast,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import {
  ChevronLeft,
  ChevronRight,
  Dumbbell,
  Footprints,
  Minus,
  Moon,
  Save,
  EllipsisVertical,
  Trash2,
  TrendingDown,
  TrendingUp,
  Upload,
} from 'lucide-react';
import {
  getWeeklyPlan,
  saveWeeklyPlan,
  syncToPlan,
  getCompliance,
  clearWeeklyPlan,
} from '@/api/weekly-plan';
import type { WeeklyPlanEntry, ComplianceResponse } from '@/api/weekly-plan';
import { formatTonnage } from '@/hooks/useTonnageCalc';
import { DayCard } from '@/components/DayCard';
import { SyncToPlanBar } from '@/components/SyncToPlanBar';
import { SaveWeeklyPlanDialog } from '@/components/SaveWeeklyPlanDialog';

// --- Helpers ---

const CATEGORY_LABELS: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Legs',
  core: 'Core',
  cardio: 'Cardio',
  drills: 'Drills',
};

function categoryLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key;
}

function getMondayOfWeek(d: Date): string {
  const copy = new Date(d);
  const day = copy.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  copy.setDate(copy.getDate() + diff);
  return copy.toISOString().split('T')[0];
}

function addWeeks(dateStr: string, weeks: number): string {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + weeks * 7);
  return d.toISOString().split('T')[0];
}

function formatDateRange(weekStart: string): string {
  const start = new Date(weekStart);
  const end = new Date(weekStart);
  end.setDate(end.getDate() + 6);

  const startDay = start.getDate();
  const endDay = end.getDate();
  const startMonth = start.toLocaleDateString('de-DE', { month: 'short' });
  const endMonth = end.toLocaleDateString('de-DE', { month: 'short' });

  if (startMonth === endMonth) {
    return `${startDay}. – ${endDay}. ${startMonth}`;
  }
  return `${startDay}. ${startMonth} – ${endDay}. ${endMonth}`;
}

const RUN_TYPE_LABELS: Record<string, string> = {
  recovery: 'Regeneration',
  easy: 'Lockerer Lauf',
  long_run: 'Langer Lauf',
  progression: 'Steigerungslauf',
  tempo: 'Tempolauf',
  intervals: 'Intervalle',
  repetitions: 'Repetitions',
  fartlek: 'Fahrtspiel',
  race: 'Wettkampf',
};

// --- Component ---

// eslint-disable-next-line complexity, max-lines-per-function -- TODO: E16 Refactoring
export function WeeklyPlanPage() {
  const navigate = useNavigate();
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

  // Load week data + compliance
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

        // Remove session from source
        const [moved] = source.sessions.splice(sessionIdx, 1);
        // Re-index source positions
        source.sessions.forEach((s, i) => {
          s.position = i;
        });

        // Add to target
        moved.position = target.sessions.length;
        target.sessions.push(moved);

        // If target is a rest day, clear rest flag
        if (target.is_rest_day) {
          target.is_rest_day = false;
        }

        return next;
      });
      setDirty(true);
    },
    [],
  );

  // --- Move rest day ---

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

  // --- Drag & Drop ---

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
            handleMoveRestDay(data.dayOfWeek, targetDay);
          } else {
            handleMoveSession(data.dayOfWeek, data.sessionIdx, targetDay);
          }
        }
      }
    },
    [handleMoveSession, handleMoveRestDay],
  );

  const activeDragSession =
    activeDragData?.type === 'session'
      ? entries.find((e) => e.day_of_week === activeDragData.day)?.sessions[activeDragData.idx]
      : null;

  // --- Save ---

  /** Internal save: persist weekly plan entries. */
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

  /** Save only this week (no sync to plan template). */
  const handleSaveWeekOnly = useCallback(async () => {
    const result = await doSave();
    if (result) {
      toast({ title: 'Wochenplan gespeichert', variant: 'success' });
      const hasEditedPlanEntries = result.entries.some((e) => e.plan_id != null && e.edited);
      setShowSyncBar(hasEditedPlanEntries);
    }
  }, [doSave, toast]);

  /** Save this week AND sync changes back to plan template. */
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

  /** Click handler: show dialog if plan-linked, otherwise save directly. */
  const handleSaveClick = useCallback(() => {
    const isPlanLinked = entries.some((e) => e.plan_id != null);
    if (isPlanLinked && dirty) {
      setShowSaveDialog(true);
    } else {
      handleSaveWeekOnly();
    }
  }, [entries, dirty, handleSaveWeekOnly]);

  // --- Delete week ---

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

  // Stats
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
            // eslint-disable-next-line max-depth -- TODO: E16 Refactoring
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

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Week Navigation + Stats */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">Wochenplan</h2>
            {hasContent && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button
                    type="button"
                    aria-label="Aktionen"
                    className="inline-flex items-center justify-center w-8 h-8 rounded-[var(--radius-interactive)] text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] hover:bg-[var(--color-bg-subtle)] transition-colors duration-150 motion-reduce:transition-none cursor-pointer"
                  >
                    <EllipsisVertical className="w-4 h-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    icon={<Trash2 />}
                    destructive
                    onSelect={() => setShowDeleteDialog(true)}
                  >
                    Woche löschen
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigateWeek(-1)}
              aria-label="Vorherige Woche"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <div className="text-center flex-1 min-w-0">
              <p className="text-sm font-semibold text-[var(--color-text-base)]">
                {formatDateRange(weekStart)}
              </p>
              {!isCurrentWeek && (
                <button
                  type="button"
                  onClick={goToCurrentWeek}
                  className="text-xs text-[var(--color-text-link)] hover:underline mt-0.5 min-h-[28px]"
                >
                  Aktuelle Woche
                </button>
              )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigateWeek(1)}
              aria-label="Nächste Woche"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          {/* Stats row */}
          {(stats.strength > 0 || stats.running > 0) && (
            <div className="flex items-center justify-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
              {stats.running > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Footprints className="w-3 h-3" /> {stats.running}× Laufen
                  {stats.totalMinutes > 0 && (
                    <span className="text-[var(--color-text-base)] font-medium ml-0.5">
                      ({Math.round(stats.totalMinutes)} min)
                    </span>
                  )}
                </span>
              )}
              {stats.strength > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Dumbbell className="w-3 h-3" /> {stats.strength}× Kraft
                  {compliance?.strength_summary &&
                    compliance.strength_summary.total_tonnage_kg > 0 &&
                    (() => {
                      const ss = compliance.strength_summary;
                      const fmt = formatTonnage(ss.total_tonnage_kg);
                      return (
                        <>
                          <span className="text-[var(--color-text-base)] font-medium ml-0.5">
                            ({fmt.value}
                            <span className="text-[var(--color-text-muted)] font-normal">
                              {fmt.unit}
                            </span>
                            )
                          </span>
                          {ss.tonnage_delta_kg != null && ss.trend && (
                            <span
                              className={`inline-flex items-center gap-0.5 ml-0.5 font-medium ${
                                ss.trend === 'up'
                                  ? 'text-[var(--color-text-success)]'
                                  : ss.trend === 'down'
                                    ? 'text-[var(--color-text-error)]'
                                    : 'text-[var(--color-text-muted)]'
                              }`}
                            >
                              {ss.trend === 'up' && <TrendingUp className="w-3 h-3" />}
                              {ss.trend === 'down' && <TrendingDown className="w-3 h-3" />}
                              {ss.trend === 'stable' && <Minus className="w-3 h-3" />}
                              {ss.tonnage_delta_kg > 0 ? '+' : ''}
                              {Math.round(ss.tonnage_delta_kg)}kg
                            </span>
                          )}
                        </>
                      );
                    })()}
                </span>
              )}
              {stats.rest > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Moon className="w-3 h-3" /> {stats.rest}× Ruhe
                </span>
              )}
            </div>
          )}

          {/* Category breakdown row */}
          {compliance?.strength_summary && compliance.strength_summary.categories.length > 0 && (
            <div className="flex items-center justify-center gap-3 mt-1.5 text-[10px] text-[var(--color-text-muted)]">
              {compliance.strength_summary.categories.map((cat) => {
                const fmt = formatTonnage(cat.tonnage_kg);
                return (
                  <span key={cat.category} className="inline-flex items-center gap-1">
                    <span className="capitalize">{categoryLabel(cat.category)}</span>
                    <span className="font-medium text-[var(--color-text-base)]">
                      {fmt.value}
                      <span className="text-[var(--color-text-muted)] font-normal">{fmt.unit}</span>
                    </span>
                  </span>
                );
              })}
            </div>
          )}

          {/* Compliance bar — session-level progress */}
          {compliance &&
            (() => {
              let planned = 0;
              let completed = 0;
              for (const ce of compliance.entries) {
                if (ce.is_rest_day) {
                  planned++;
                  if (ce.status === 'rest_ok') completed++;
                } else {
                  const types = ce.planned_types;
                  planned += types.length;
                  for (const pt of types) {
                    if (ce.actual_sessions.some((a) => a.workout_type === pt)) {
                      completed++;
                    }
                  }
                }
              }
              if (planned === 0) return null;
              return (
                <div className="mt-3 pt-5 border-t border-[var(--color-border-muted)]">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-[var(--color-text-muted)]">Umsetzung</p>
                    <p className="text-xs font-medium text-[var(--color-text-base)]">
                      {completed}/{planned}
                    </p>
                  </div>
                  <div className="mt-1.5 h-2 rounded-full bg-[var(--color-border-muted)] overflow-hidden">
                    <div
                      className="h-full rounded-full bg-[var(--color-interactive-primary)] transition-all duration-500 motion-reduce:transition-none"
                      style={{
                        width: `${Math.round((completed / planned) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })()}
          {/* Day grid */}
          <div className="mt-10">
            {loading ? (
              <div className="flex justify-center py-8">
                <Spinner size="lg" />
              </div>
            ) : (
              <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
                <div
                  className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-[var(--spacing-sm)]"
                  role="grid"
                  aria-label="Wochenplan"
                >
                  {entries.map((entry) => {
                    const isToday =
                      isCurrentWeek &&
                      new Date().getDay() === (entry.day_of_week === 6 ? 0 : entry.day_of_week + 1);
                    const dayCompliance = compliance?.entries.find(
                      (c) => c.day_of_week === entry.day_of_week,
                    );

                    return (
                      <DayCard
                        key={entry.day_of_week}
                        entry={entry}
                        weekStart={weekStart}
                        isToday={isToday}
                        compliance={dayCompliance}
                        showCompliance={hasContent}
                        onUpdate={(updates) => updateEntry(entry.day_of_week, updates)}
                        onNavigateSession={(id) => navigate(`/sessions/${id}`)}
                        onMoveSession={(sessionIdx, targetDay) =>
                          handleMoveSession(entry.day_of_week, sessionIdx, targetDay)
                        }
                        onMoveRestDay={(targetDay) =>
                          handleMoveRestDay(entry.day_of_week, targetDay)
                        }
                      />
                    );
                  })}
                </div>

                <DragOverlay>
                  {activeDragData?.type === 'rest' && (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-paper)] shadow-[var(--shadow-raised)] border border-[var(--color-border-muted)]">
                      <Moon className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      <span className="text-xs font-medium text-[var(--color-text-base)]">
                        Ruhetag
                      </span>
                    </div>
                  )}
                  {activeDragSession && (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-paper)] shadow-[var(--shadow-raised)] border border-[var(--color-border-muted)]">
                      {activeDragSession.training_type === 'strength' ? (
                        <Dumbbell className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      ) : (
                        <Footprints className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      )}
                      <span className="text-xs font-medium text-[var(--color-text-base)]">
                        {activeDragSession.training_type === 'strength'
                          ? (activeDragSession.template_name ?? 'Kraft')
                          : (RUN_TYPE_LABELS[activeDragSession.run_details?.run_type ?? 'easy'] ??
                            'Laufen')}
                      </span>
                    </div>
                  )}
                </DragOverlay>
              </DndContext>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Delete Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wochenplan löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Alle Einträge für die Woche {formatDateRange(weekStart)} werden gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteWeek} disabled={deleting}>
              {deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Sync-to-Plan Bar */}
      {showSyncBar && linkedPlanId && editedPlanCount > 0 && (
        <SyncToPlanBar
          planId={linkedPlanId}
          weekStart={weekStart}
          editedCount={editedPlanCount}
          onSynced={() => {
            setShowSyncBar(false);
            loadWeek(weekStart);
          }}
          onDismiss={() => setShowSyncBar(false)}
        />
      )}

      {/* Quick action */}
      <Button
        variant="secondary"
        size="sm"
        onClick={() => navigate('/sessions/new')}
        className="w-full"
      >
        <Upload className="w-4 h-4 mr-1" />
        Training hochladen
      </Button>

      {/* Save Dialog (plan-linked) */}
      <SaveWeeklyPlanDialog
        open={showSaveDialog}
        onOpenChange={setShowSaveDialog}
        onSaveWeekOnly={handleSaveWeekOnly}
        onSaveAndSync={handleSaveAndSync}
      />

      {/* Save button */}
      {dirty && (
        <div className="sticky bottom-4 z-10">
          <Button
            variant="primary"
            onClick={handleSaveClick}
            disabled={saving}
            className="w-full"
            size="lg"
          >
            {saving ? <Spinner size="sm" className="mr-2" /> : <Save className="w-4 h-4 mr-2" />}
            {saving ? 'Speichern...' : 'Wochenplan speichern'}
          </Button>
        </div>
      )}
    </div>
  );
}
