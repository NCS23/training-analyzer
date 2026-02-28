import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardBody,
  Button,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
  useToast,
  Select,
} from '@nordlig/components';
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Dumbbell,
  Footprints,
  Moon,
  Save,
  Trash2,
} from 'lucide-react';
import { getWeeklyPlan, saveWeeklyPlan } from '@/api/weekly-plan';
import type { WeeklyPlanEntry } from '@/api/weekly-plan';
import { listTrainingPlans } from '@/api/training-plans';
import type { TrainingPlanSummary } from '@/api/training-plans';

// --- Helpers ---

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
const DAY_NAMES = [
  'Montag',
  'Dienstag',
  'Mittwoch',
  'Donnerstag',
  'Freitag',
  'Samstag',
  'Sonntag',
];

function getMondayOfWeek(d: Date): string {
  const copy = new Date(d);
  const day = copy.getDay();
  // getDay: 0=Sun, so adjust: Mon=1 -> offset 0
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

function getDateForDay(weekStart: string, dayOfWeek: number): string {
  const d = new Date(weekStart);
  d.setDate(d.getDate() + dayOfWeek);
  return d.getDate().toString();
}

type DayType = 'strength' | 'running' | 'rest' | 'empty';

function getDayType(entry: WeeklyPlanEntry): DayType {
  if (entry.is_rest_day) return 'rest';
  if (entry.training_type === 'strength') return 'strength';
  if (entry.training_type === 'running') return 'running';
  return 'empty';
}

const typeOptions = [
  { value: '', label: 'Kein Training' },
  { value: 'strength', label: 'Kraft' },
  { value: 'running', label: 'Laufen' },
  { value: 'rest', label: 'Ruhetag' },
];

/** Warn if strength is planned adjacent to running (both directions). */
function getProximityWarning(
  entries: WeeklyPlanEntry[],
  dayOfWeek: number,
): string | null {
  const current = entries.find((e) => e.day_of_week === dayOfWeek);
  if (!current || current.training_type !== 'strength') return null;

  const prev = entries.find((e) => e.day_of_week === dayOfWeek - 1);
  const next = entries.find((e) => e.day_of_week === dayOfWeek + 1);

  if (prev?.training_type === 'running' && next?.training_type === 'running') {
    return 'Kraft zwischen zwei Laufeinheiten';
  }
  if (prev?.training_type === 'running') {
    return 'Kraft direkt nach Laufeinheit';
  }
  if (next?.training_type === 'running') {
    return 'Kraft direkt vor Laufeinheit';
  }
  return null;
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

  // Training plans for linking
  const [plans, setPlans] = useState<TrainingPlanSummary[]>([]);

  // Selected day for editing
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  // Load plans
  useEffect(() => {
    listTrainingPlans('strength')
      .then((res) => setPlans(res.plans))
      .catch(() => {});
  }, []);

  // Load week data
  const loadWeek = useCallback(
    async (ws: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await getWeeklyPlan(ws);
        setEntries(result.entries);
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

  const navigateWeek = useCallback(
    (direction: -1 | 1) => {
      setWeekStart((prev) => addWeeks(prev, direction));
    },
    [],
  );

  const goToCurrentWeek = useCallback(() => {
    setWeekStart(getMondayOfWeek(new Date()));
  }, []);

  // --- Day editing ---

  const updateEntry = useCallback(
    (dayOfWeek: number, updates: Partial<WeeklyPlanEntry>) => {
      setEntries((prev) =>
        prev.map((e) =>
          e.day_of_week === dayOfWeek ? { ...e, ...updates } : e,
        ),
      );
      setDirty(true);
    },
    [],
  );

  const setDayType = useCallback(
    (dayOfWeek: number, type: DayType) => {
      if (type === 'rest') {
        updateEntry(dayOfWeek, {
          training_type: null,
          is_rest_day: true,
          plan_id: null,
          plan_name: null,
        });
      } else if (type === 'strength') {
        updateEntry(dayOfWeek, {
          training_type: 'strength',
          is_rest_day: false,
        });
      } else if (type === 'running') {
        updateEntry(dayOfWeek, {
          training_type: 'running',
          is_rest_day: false,
          plan_id: null,
          plan_name: null,
        });
      } else {
        updateEntry(dayOfWeek, {
          training_type: null,
          is_rest_day: false,
          plan_id: null,
          plan_name: null,
          notes: null,
        });
      }
    },
    [updateEntry],
  );

  const setPlanForDay = useCallback(
    (dayOfWeek: number, planId: number | null) => {
      const plan = plans.find((p) => p.id === planId);
      updateEntry(dayOfWeek, {
        plan_id: planId,
        plan_name: plan?.name ?? null,
      });
    },
    [plans, updateEntry],
  );

  // --- Save ---

  const handleSave = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const nonEmptyEntries = entries.filter(
        (e) => e.training_type != null || e.is_rest_day || e.notes,
      );
      if (nonEmptyEntries.length === 0) {
        // Nothing to save — could clear
        toast({ title: 'Keine Einträge zum Speichern', variant: 'warning' });
        setSaving(false);
        return;
      }
      const result = await saveWeeklyPlan({
        week_start: weekStart,
        entries: nonEmptyEntries.map((e) => ({
          day_of_week: e.day_of_week,
          training_type: e.training_type,
          plan_id: e.plan_id,
          is_rest_day: e.is_rest_day,
          notes: e.notes,
        })),
      });
      setEntries(result.entries);
      setDirty(false);
      toast({ title: 'Wochenplan gespeichert', variant: 'success' });
    } catch {
      setError('Speichern fehlgeschlagen.');
    } finally {
      setSaving(false);
    }
  }, [entries, weekStart, toast]);

  // Plan options for select
  const planOptions = useMemo(
    () => [
      { value: '', label: 'Kein Plan' },
      ...plans.map((p) => ({ value: String(p.id), label: p.name })),
    ],
    [plans],
  );

  // Compute stats
  const stats = useMemo(() => {
    let strength = 0;
    let running = 0;
    let rest = 0;
    for (const e of entries) {
      if (e.is_rest_day) rest++;
      else if (e.training_type === 'strength') strength++;
      else if (e.training_type === 'running') running++;
    }
    return { strength, running, rest };
  }, [entries]);

  const isCurrentWeek = weekStart === getMondayOfWeek(new Date());

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <header className="pb-2">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Wochenplan
        </h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Trainingseinheiten für die Woche planen.
        </p>
      </header>

      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Week Navigation */}
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
                  className="text-xs text-[var(--color-text-info)] hover:underline mt-0.5"
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

          {/* Stats */}
          {(stats.strength > 0 || stats.running > 0 || stats.rest > 0) && (
            <div className="flex items-center justify-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
              {stats.strength > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Dumbbell className="w-3 h-3" /> {stats.strength}× Kraft
                </span>
              )}
              {stats.running > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Footprints className="w-3 h-3" /> {stats.running}× Laufen
                </span>
              )}
              {stats.rest > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Moon className="w-3 h-3" /> {stats.rest}× Ruhe
                </span>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* Day Cards */}
      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry) => {
            const dayType = getDayType(entry);
            const isSelected = selectedDay === entry.day_of_week;
            const isToday =
              isCurrentWeek &&
              new Date().getDay() ===
                (entry.day_of_week === 6 ? 0 : entry.day_of_week + 1);
            const proximityWarning = getProximityWarning(
              entries,
              entry.day_of_week,
            );

            return (
              <Card
                key={entry.day_of_week}
                elevation="raised"
                padding="spacious"
                className={`transition-colors motion-reduce:transition-none ${
                  isToday
                    ? 'ring-2 ring-[var(--color-border-focus)]'
                    : ''
                }`}
              >
                <CardBody>
                  <div className="space-y-3">
                    {/* Day header row */}
                    <button
                      type="button"
                      onClick={() =>
                        setSelectedDay(isSelected ? null : entry.day_of_week)
                      }
                      className="w-full flex items-center justify-between min-h-[44px]"
                      aria-expanded={isSelected}
                      aria-label={`${DAY_NAMES[entry.day_of_week]} bearbeiten`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex flex-col items-center w-10">
                          <span className="text-xs font-medium text-[var(--color-text-muted)]">
                            {DAY_LABELS[entry.day_of_week]}
                          </span>
                          <span className="text-lg font-semibold text-[var(--color-text-base)]">
                            {getDateForDay(weekStart, entry.day_of_week)}
                          </span>
                        </div>

                        {dayType === 'strength' && (
                          <div className="flex items-center gap-2">
                            <Dumbbell className="w-4 h-4 text-[var(--color-text-info)]" />
                            <span className="text-sm text-[var(--color-text-base)]">
                              Kraft
                            </span>
                            {entry.plan_name && (
                              <Badge variant="info" size="xs">
                                {entry.plan_name}
                              </Badge>
                            )}
                          </div>
                        )}

                        {dayType === 'running' && (
                          <div className="flex items-center gap-2">
                            <Footprints className="w-4 h-4 text-[var(--color-text-success)]" />
                            <span className="text-sm text-[var(--color-text-base)]">
                              Laufen
                            </span>
                          </div>
                        )}

                        {dayType === 'rest' && (
                          <div className="flex items-center gap-2">
                            <Moon className="w-4 h-4 text-[var(--color-text-muted)]" />
                            <span className="text-sm text-[var(--color-text-muted)]">
                              Ruhetag
                            </span>
                          </div>
                        )}

                        {dayType === 'empty' && (
                          <span className="text-sm text-[var(--color-text-disabled)]">
                            Nicht geplant
                          </span>
                        )}
                      </div>

                      {entry.notes && !isSelected && (
                        <span className="text-xs text-[var(--color-text-muted)] truncate max-w-[120px]">
                          {entry.notes}
                        </span>
                      )}
                    </button>

                    {/* Proximity warning */}
                    {proximityWarning && (
                      <div className="flex items-center gap-2 px-1 py-1.5 text-xs text-[var(--color-text-warning)]">
                        <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                        <span>{proximityWarning}</span>
                      </div>
                    )}

                    {/* Expanded editor */}
                    {isSelected && (
                      <div className="space-y-3 pt-2 border-t border-[var(--color-border-subtle)]">
                        <div>
                          <label className="text-xs text-[var(--color-text-muted)] mb-1 block">
                            Trainingstyp
                          </label>
                          <Select
                            options={typeOptions}
                            value={
                              dayType === 'rest'
                                ? 'rest'
                                : entry.training_type ?? ''
                            }
                            onChange={(val) =>
                              setDayType(
                                entry.day_of_week,
                                (val || 'empty') as DayType,
                              )
                            }
                            inputSize="sm"
                            aria-label="Trainingstyp"
                          />
                        </div>

                        {entry.training_type === 'strength' &&
                          plans.length > 0 && (
                            <div>
                              <label className="text-xs text-[var(--color-text-muted)] mb-1 block">
                                Trainingsplan (optional)
                              </label>
                              <Select
                                options={planOptions}
                                value={
                                  entry.plan_id ? String(entry.plan_id) : ''
                                }
                                onChange={(val) =>
                                  setPlanForDay(
                                    entry.day_of_week,
                                    val ? Number(val) : null,
                                  )
                                }
                                inputSize="sm"
                                aria-label="Trainingsplan"
                              />
                            </div>
                          )}

                        <div>
                          <label className="text-xs text-[var(--color-text-muted)] mb-1 block">
                            Notizen (optional)
                          </label>
                          <input
                            type="text"
                            value={entry.notes ?? ''}
                            onChange={(e) =>
                              updateEntry(entry.day_of_week, {
                                notes: e.target.value || null,
                              })
                            }
                            placeholder="z.B. Tempolauf, leichtes Training…"
                            className="w-full rounded-[var(--radius-component-sm)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] px-3 py-2 text-sm text-[var(--color-text-base)] placeholder:text-[var(--color-text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] transition-colors duration-150 motion-reduce:transition-none"
                          />
                        </div>

                        {/* Quick clear */}
                        {dayType !== 'empty' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setDayType(entry.day_of_week, 'empty')
                            }
                          >
                            <Trash2 className="w-3.5 h-3.5 mr-1 text-[var(--color-text-error)]" />
                            Leeren
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </CardBody>
              </Card>
            );
          })}
        </div>
      )}

      {/* Quick actions: navigate to strength session or just start running */}
      <div className="flex gap-3">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate('/sessions/new/strength')}
          className="flex-1"
        >
          <Dumbbell className="w-4 h-4 mr-1" />
          Training starten
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate('/sessions/new')}
          className="flex-1"
        >
          <Footprints className="w-4 h-4 mr-1" />
          Lauf hochladen
        </Button>
      </div>

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
            {saving ? (
              <Spinner size="sm" className="mr-2" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {saving ? 'Speichern...' : 'Wochenplan speichern'}
          </Button>
        </div>
      )}
    </div>
  );
}
