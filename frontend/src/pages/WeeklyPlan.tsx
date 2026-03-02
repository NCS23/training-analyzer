import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
  EllipsisVertical,
  Footprints,
  Moon,
  Save,
  Trash2,
  Upload,
} from 'lucide-react';
import { getWeeklyPlan, saveWeeklyPlan, getCompliance, clearWeeklyPlan } from '@/api/weekly-plan';
import type { WeeklyPlanEntry, ComplianceResponse } from '@/api/weekly-plan';
import { DayCard } from '@/components/DayCard';
import { SyncToPlanBar } from '@/components/SyncToPlanBar';

// --- Helpers ---

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

// --- Component ---

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
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showSyncBar, setShowSyncBar] = useState(false);

  // Load week data + compliance
  const loadWeek = useCallback(
    async (ws: string) => {
      setLoading(true);
      setError(null);
      setSelectedDay(null);
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

  // --- Save ---

  const handleSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const nonEmptyEntries = entries.filter(
        (e) => e.training_type != null || e.is_rest_day || e.notes,
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
          training_type: e.training_type,
          template_id: e.template_id,
          is_rest_day: e.is_rest_day,
          notes: e.notes,
          run_details: e.run_details,
        })),
      });
      setEntries(result.entries);
      setDirty(false);
      toast({ title: 'Wochenplan gespeichert', variant: 'success' });
      // Show sync bar if there are edited entries linked to a plan
      const hasEditedPlanEntries = result.entries.some((e) => e.plan_id != null && e.edited);
      setShowSyncBar(hasEditedPlanEntries);
    } catch {
      setError('Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  }, [entries, weekStart, toast]);

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
      if (e.is_rest_day) rest++;
      else if (e.training_type === 'strength') strength++;
      else if (e.training_type === 'running') {
        running++;
        if (e.run_details?.target_duration_minutes) {
          totalMinutes += e.run_details.target_duration_minutes;
        }
      }
    }
    return { strength, running, rest, totalMinutes };
  }, [entries]);

  const isCurrentWeek = weekStart === getMondayOfWeek(new Date());
  const hasContent = entries.some((e) => e.training_type != null || e.is_rest_day);
  const linkedPlanId = entries.find((e) => e.plan_id != null)?.plan_id ?? null;
  const editedPlanCount = entries.filter((e) => e.plan_id != null && e.edited).length;

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-7xl mx-auto space-y-4">
      {/* Header with kebab menu */}
      <header className="flex items-start justify-between gap-2 pb-2">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Wochenplan
        </h1>
        {hasContent && (
          <DropdownMenu>
            <DropdownMenuTrigger>
              <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
                <EllipsisVertical className="w-4 h-4" />
              </Button>
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
      </header>

      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Week Navigation + Stats */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigateWeek(-1)}
              aria-label="Vorherige Woche"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <div className="text-center">
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
                </span>
              )}
              {stats.rest > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Moon className="w-3 h-3" /> {stats.rest}× Ruhe
                </span>
              )}
            </div>
          )}

          {/* Compliance bar */}
          {compliance && compliance.planned_count > 0 && (
            <div className="mt-3 pt-3 border-t border-[var(--color-border-muted)]">
              <div className="flex items-center justify-between">
                <p className="text-xs text-[var(--color-text-muted)]">Umsetzung</p>
                <p className="text-xs font-medium text-[var(--color-text-base)]">
                  {compliance.completed_count}/{compliance.planned_count}
                </p>
              </div>
              <div className="mt-1.5 h-2 rounded-full bg-[var(--color-border-muted)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--color-interactive-primary)] transition-all duration-500 motion-reduce:transition-none"
                  style={{
                    width: `${Math.round((compliance.completed_count / compliance.planned_count) * 100)}%`,
                  }}
                />
              </div>
            </div>
          )}
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

      {/* 7-Day Grid */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : (
            <div
              className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-[var(--spacing-xs)]"
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
                    isExpanded={selectedDay === entry.day_of_week}
                    compliance={dayCompliance}
                    showCompliance={hasContent}
                    onToggleExpand={() =>
                      setSelectedDay(selectedDay === entry.day_of_week ? null : entry.day_of_week)
                    }
                    onUpdate={(updates) => updateEntry(entry.day_of_week, updates)}
                    onNavigateSession={(id) => navigate(`/sessions/${id}`)}
                  />
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>

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

      {/* Save button */}
      {dirty && (
        <div className="sticky bottom-4 z-10">
          <Button
            variant="primary"
            onClick={handleSave}
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
