import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Spinner,
  Alert,
  AlertDescription,
  Badge,
  Select,
  ToggleGroup,
  ToggleGroupItem,
  EmptyState,
} from '@nordlig/components';
import { Dumbbell, Trophy, TrendingUp, Weight, ArrowUp, ArrowDown, Minus } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import {
  getExerciseList,
  getExerciseProgression,
  getPersonalRecords,
  getTonnageTrend,
} from '@/api/progression';
import type {
  ExerciseListItem,
  ExerciseHistoryResponse,
  PersonalRecord,
  TonnageTrendResponse,
} from '@/api/progression';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';

type TimeRange = '28' | '90' | '180';

const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  '28': '4 Wochen',
  '90': '3 Monate',
  '180': '6 Monate',
};

const CATEGORY_LABELS: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
};

const PR_TYPE_LABELS: Record<string, string> = {
  max_weight: 'Max. Gewicht',
  max_volume_set: 'Bester Satz',
  max_tonnage_session: 'Max. Tonnage',
};

function formatDateShort(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'dd.MM.', { locale: de });
  } catch {
    return dateStr;
  }
}

function formatDateFull(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'dd.MM.yyyy', { locale: de });
  } catch {
    return dateStr;
  }
}

export function StrengthProgressionPage() {
  const [exercises, setExercises] = useState<ExerciseListItem[]>([]);
  const [selectedExercise, setSelectedExercise] = useState<string | null>(null);
  const [history, setHistory] = useState<ExerciseHistoryResponse | null>(null);
  const [prs, setPrs] = useState<PersonalRecord[]>([]);
  const [tonnageTrend, setTonnageTrend] = useState<TonnageTrendResponse | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>('90');
  const [loading, setLoading] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load exercises + PRs + tonnage on mount
  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [exerciseRes, prRes, tonnageRes] = await Promise.all([
        getExerciseList(),
        getPersonalRecords(),
        getTonnageTrend(parseInt(timeRange, 10)),
      ]);
      setExercises(exerciseRes.exercises);
      setPrs(prRes.records);
      setTonnageTrend(tonnageRes);

      // Auto-select first exercise
      if (exerciseRes.exercises.length > 0 && !selectedExercise) {
        setSelectedExercise(exerciseRes.exercises[0].name);
      }
    } catch {
      setError('Daten konnten nicht geladen werden');
    } finally {
      setLoading(false);
    }
  }, [timeRange, selectedExercise]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Load exercise history when selection changes
  useEffect(() => {
    if (!selectedExercise) return;
    let cancelled = false;
    setLoadingHistory(true);

    getExerciseProgression(selectedExercise)
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch(() => {
        if (!cancelled) setHistory(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedExercise]);

  // Reload tonnage when time range changes
  useEffect(() => {
    getTonnageTrend(parseInt(timeRange, 10))
      .then(setTonnageTrend)
      .catch(() => {});
  }, [timeRange]);

  // Chart data for exercise progression
  const weightChartData = useMemo(() => {
    if (!history) return [];
    return history.data_points.map((p) => ({
      ...p,
      label: formatDateShort(p.date),
    }));
  }, [history]);

  // Chart data for tonnage trend
  const tonnageChartData = useMemo(() => {
    if (!tonnageTrend) return [];
    return tonnageTrend.weeks.map((w) => ({
      ...w,
      label: formatDateShort(w.week_start),
    }));
  }, [tonnageTrend]);

  // Group PRs by exercise
  const prsByExercise = useMemo(() => {
    const grouped: Record<string, PersonalRecord[]> = {};
    for (const pr of prs) {
      if (!grouped[pr.exercise_name]) grouped[pr.exercise_name] = [];
      grouped[pr.exercise_name].push(pr);
    }
    return grouped;
  }, [prs]);

  const exerciseOptions = useMemo(
    () =>
      exercises.map((e) => ({
        value: e.name,
        label: `${e.name} (${e.session_count}x)`,
      })),
    [exercises],
  );

  if (loading) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto">
        <div className="flex items-center justify-center min-h-[40vh]">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (exercises.length === 0) {
    return (
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
        <header className="pb-2">
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Kraft-Progression
          </h1>
        </header>
        <EmptyState
          icon={<Dumbbell className="w-10 h-10" />}
          title="Noch keine Krafttraining-Daten"
          description="Erstelle deine erste Krafttraining-Session, um die Progression zu sehen."
        />
      </div>
    );
  }

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 pb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Kraft-Progression
          </h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Gewichtsverlauf, PRs und Tonnage-Trends.
          </p>
        </div>
        <ToggleGroup
          type="single"
          value={timeRange}
          onValueChange={(v) => {
            if (v) setTimeRange(v as TimeRange);
          }}
        >
          {(Object.entries(TIME_RANGE_LABELS) as [TimeRange, string][]).map(([value, label]) => (
            <ToggleGroupItem key={value} value={value}>
              {label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </header>

      {/* Exercise Selector + Weight Progression */}
      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[var(--color-chart-1)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Gewichtsverlauf
              </h2>
            </div>
            <Select
              options={exerciseOptions}
              value={selectedExercise ?? undefined}
              onChange={(val) => {
                if (val) setSelectedExercise(val);
              }}
              inputSize="sm"
              className="w-full sm:w-56"
              placeholder="Übung wählen"
            />
          </div>
        </CardHeader>
        <CardBody>
          {loadingHistory ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="md" />
            </div>
          ) : weightChartData.length > 0 ? (
            <>
              {/* Progression indicator */}
              {history?.weight_progression != null && (
                <div className="flex items-center gap-2 mb-4">
                  {history.weight_progression > 0 ? (
                    <Badge variant="success" size="xs">
                      <ArrowUp className="w-3 h-3 mr-0.5" />+{history.weight_progression} kg
                    </Badge>
                  ) : history.weight_progression < 0 ? (
                    <Badge variant="warning" size="xs">
                      <ArrowDown className="w-3 h-3 mr-0.5" />
                      {history.weight_progression} kg
                    </Badge>
                  ) : (
                    <Badge variant="info" size="xs">
                      <Minus className="w-3 h-3 mr-0.5" />
                      Gleich
                    </Badge>
                  )}
                  <span className="text-xs text-[var(--color-text-muted)]">
                    vs. vorherige Session
                  </span>
                </div>
              )}
              <div className="h-[220px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={weightChartData}
                    margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    />
                    <YAxis
                      domain={['auto', 'auto']}
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                      tickFormatter={(v: number) => `${v}kg`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-default)',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(value: number, name: string) => {
                        if (name === 'max_weight_kg') return [`${value} kg`, 'Max. Gewicht'];
                        if (name === 'tonnage_kg') return [`${value} kg`, 'Tonnage'];
                        return [value, name];
                      }}
                      labelFormatter={(label: string) => label}
                    />
                    <Line
                      type="monotone"
                      dataKey="max_weight_kg"
                      stroke="var(--color-chart-1)"
                      strokeWidth={2}
                      dot={{ r: 4, fill: 'var(--color-chart-1)' }}
                      connectNulls
                      name="max_weight_kg"
                    />
                    <Line
                      type="monotone"
                      dataKey="tonnage_kg"
                      stroke="var(--color-chart-2)"
                      strokeWidth={1.5}
                      strokeDasharray="5 3"
                      dot={{ r: 3, fill: 'var(--color-chart-2)' }}
                      connectNulls
                      name="tonnage_kg"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <p className="text-sm text-[var(--color-text-muted)] py-8 text-center">
              Keine Daten für diese Übung vorhanden.
            </p>
          )}
        </CardBody>
      </Card>

      {/* Tonnage Trend */}
      {tonnageChartData.length > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Weight className="w-4 h-4 text-[var(--color-chart-2)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Wochen-Tonnage
              </h2>
              {tonnageTrend?.trend_direction && (
                <Badge
                  variant={
                    tonnageTrend.trend_direction === 'up'
                      ? 'success'
                      : tonnageTrend.trend_direction === 'down'
                        ? 'warning'
                        : 'info'
                  }
                  size="xs"
                >
                  {tonnageTrend.trend_direction === 'up'
                    ? 'Steigend'
                    : tonnageTrend.trend_direction === 'down'
                      ? 'Sinkend'
                      : 'Stabil'}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardBody>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={tonnageChartData}
                  margin={{ top: 5, right: 10, left: -10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                  <YAxis
                    tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    tickFormatter={(v: number) =>
                      v >= 1000 ? `${(v / 1000).toFixed(1)}t` : `${v}kg`
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--color-bg-elevated)',
                      border: '1px solid var(--color-border-default)',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    formatter={(value: number) => [
                      value >= 1000 ? `${(value / 1000).toFixed(1)} t` : `${Math.round(value)} kg`,
                      'Tonnage',
                    ]}
                    labelFormatter={(label: string) => `KW ${label}`}
                  />
                  <Bar
                    dataKey="total_tonnage_kg"
                    fill="var(--color-chart-2)"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Summary */}
            {tonnageTrend && (
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-[var(--color-border-subtle)]">
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Gesamt-Tonnage</p>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {tonnageTrend.total_tonnage_kg >= 1000
                      ? `${(tonnageTrend.total_tonnage_kg / 1000).toFixed(1)} t`
                      : `${Math.round(tonnageTrend.total_tonnage_kg)} kg`}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Ø pro Woche</p>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {tonnageTrend.avg_weekly_tonnage_kg >= 1000
                      ? `${(tonnageTrend.avg_weekly_tonnage_kg / 1000).toFixed(1)} t`
                      : `${Math.round(tonnageTrend.avg_weekly_tonnage_kg)} kg`}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Wochen</p>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {tonnageChartData.length}
                  </p>
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Personal Records */}
      {Object.keys(prsByExercise).length > 0 && (
        <Card elevation="raised">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-[var(--color-chart-3)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Persönliche Bestleistungen
              </h2>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {Object.entries(prsByExercise).map(([exerciseName, exercisePrs]) => (
                <div key={exerciseName} className="space-y-2">
                  <h3 className="text-sm font-medium text-[var(--color-text-base)]">
                    {exerciseName}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {exercisePrs.map((pr, i) => (
                      <div
                        key={i}
                        className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-2.5"
                      >
                        <p className="text-xs text-[var(--color-text-muted)] mb-0.5">
                          {PR_TYPE_LABELS[pr.record_type] ?? pr.record_type}
                        </p>
                        <p className="text-base font-semibold text-[var(--color-text-base)] tabular-nums">
                          {pr.value >= 1000
                            ? `${(pr.value / 1000).toFixed(1)} t`
                            : `${pr.value} ${pr.unit}`}
                        </p>
                        {pr.detail && (
                          <p className="text-xs text-[var(--color-text-muted)]">{pr.detail}</p>
                        )}
                        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                          {formatDateFull(pr.date)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Exercise Overview */}
      <Card elevation="raised">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Dumbbell className="w-4 h-4 text-[var(--color-text-muted)]" />
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Alle Übungen ({exercises.length})
            </h2>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-2">
            {exercises.map((ex) => (
              <button
                key={ex.name}
                type="button"
                onClick={() => setSelectedExercise(ex.name)}
                className={`w-full text-left rounded-[var(--radius-component-md)] px-3 py-2.5 transition-colors duration-200 motion-reduce:transition-none ${
                  selectedExercise === ex.name
                    ? 'bg-[var(--color-bg-info-subtle)] border border-[var(--color-border-info)]'
                    : 'bg-[var(--color-bg-surface)] hover:bg-[var(--color-bg-muted)]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-[var(--color-text-base)]">
                      {ex.name}
                    </span>
                    <Badge variant="info" size="xs">
                      {CATEGORY_LABELS[ex.category] ?? ex.category}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                    <span>{ex.session_count}x</span>
                    {ex.last_max_weight_kg > 0 && <span>{ex.last_max_weight_kg} kg</span>}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
