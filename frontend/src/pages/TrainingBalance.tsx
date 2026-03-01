import { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
  Progress,
} from '@nordlig/components';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Dumbbell,
  Footprints,
  Info,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { getTrainingBalance } from '@/api/training-balance';
import type { TrainingBalanceResponse } from '@/api/training-balance';

const PERIOD_OPTIONS = [
  { value: 7, label: '7 Tage' },
  { value: 28, label: '4 Wochen' },
  { value: 90, label: '3 Monate' },
];

const INSIGHT_ICONS = {
  positive: CheckCircle,
  warning: AlertTriangle,
  neutral: Info,
} as const;

const INSIGHT_COLORS = {
  positive: 'text-[var(--color-text-success)]',
  warning: 'text-[var(--color-text-warning)]',
  neutral: 'text-[var(--color-text-muted)]',
} as const;

export function TrainingBalancePage() {
  const [data, setData] = useState<TrainingBalanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(28);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getTrainingBalance(days)
      .then(setData)
      .catch(() => setError('Daten konnten nicht geladen werden.'))
      .finally(() => setLoading(false));
  }, [days]);

  const volumeChartData = useMemo(() => {
    if (!data) return [];
    return data.volume_weeks.map((w) => ({
      week: w.week.replace(/\d{4}-W/, 'KW'),
      km: w.running_km,
      change: w.volume_change_percent,
    }));
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 pt-6 max-w-5xl mx-auto">
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <header className="pb-2">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Trainingsbalance
        </h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Intensitätsverteilung, Volumen und Muskelgruppen.
        </p>
      </header>

      {/* Period selector */}
      <div className="flex items-center gap-2">
        {PERIOD_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setDays(opt.value)}
            className={`px-3 py-1.5 text-xs rounded-[var(--radius-component-sm)] transition-colors duration-150 motion-reduce:transition-none min-h-[44px] ${
              days === opt.value
                ? 'bg-[var(--color-bg-info-subtle)] text-[var(--color-text-info)] font-medium'
                : 'bg-[var(--color-bg-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-muted)]'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Sport Mix */}
      {data.sport_mix.total_sessions > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[var(--color-text-primary)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Trainingsmix
              </h2>
            </div>
          </CardHeader>
          <CardBody>
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-1.5 text-sm">
                <Footprints className="w-4 h-4 text-[var(--color-text-success)]" />
                <span className="text-[var(--color-text-base)] font-medium">
                  {data.sport_mix.running_sessions}
                </span>
                <span className="text-[var(--color-text-muted)]">Laufen</span>
                <Badge variant="neutral" size="xs">
                  {data.sport_mix.running_percent.toFixed(0)}%
                </Badge>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <Dumbbell className="w-4 h-4 text-[var(--color-text-info)]" />
                <span className="text-[var(--color-text-base)] font-medium">
                  {data.sport_mix.strength_sessions}
                </span>
                <span className="text-[var(--color-text-muted)]">Kraft</span>
                <Badge variant="neutral" size="xs">
                  {data.sport_mix.strength_percent.toFixed(0)}%
                </Badge>
              </div>
            </div>
            <div className="h-2 rounded-full bg-[var(--color-bg-subtle)] overflow-hidden flex">
              <div
                className="h-full bg-[var(--color-bg-success)] transition-all duration-500 motion-reduce:transition-none"
                style={{ width: `${data.sport_mix.running_percent}%` }}
              />
              <div
                className="h-full bg-[var(--color-bg-info)] transition-all duration-500 motion-reduce:transition-none"
                style={{ width: `${data.sport_mix.strength_percent}%` }}
              />
            </div>
          </CardBody>
        </Card>
      )}

      {/* Intensity Distribution */}
      {data.intensity.total_sessions > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[var(--color-text-primary)]" />
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                  Intensitätsverteilung
                </h2>
              </div>
              {data.intensity.is_polarized && (
                <Badge variant="success" size="xs">
                  Polarisiert
                </Badge>
              )}
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              Ziel: ~80% locker, ~20% intensiv (Polarized Training).
            </p>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Locker ({data.intensity.easy_sessions} Sessions)
                  </span>
                  <span className="text-xs font-medium text-[var(--color-text-base)]">
                    {data.intensity.easy_percent.toFixed(0)}%
                  </span>
                </div>
                <Progress
                  value={data.intensity.easy_percent}
                  color="success"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Moderat ({data.intensity.moderate_sessions} Sessions)
                  </span>
                  <span className="text-xs font-medium text-[var(--color-text-base)]">
                    {data.intensity.moderate_percent.toFixed(0)}%
                  </span>
                </div>
                <Progress
                  value={data.intensity.moderate_percent}
                  color="warning"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Intensiv ({data.intensity.hard_sessions} Sessions)
                  </span>
                  <span className="text-xs font-medium text-[var(--color-text-base)]">
                    {data.intensity.hard_percent.toFixed(0)}%
                  </span>
                </div>
                <Progress
                  value={data.intensity.hard_percent}
                  color="error"
                />
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Volume Chart */}
      {volumeChartData.length > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Footprints className="w-4 h-4 text-[var(--color-text-primary)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Wochenvolumen
              </h2>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              Lauf-Kilometer pro Woche. Rot markiert = &gt;10% Steigerung.
            </p>
          </CardHeader>
          <CardBody>
            <div className="h-48" aria-label="Wochenvolumen Balkendiagramm">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={volumeChartData}>
                  <XAxis
                    dataKey="week"
                    tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    tickLine={false}
                    axisLine={false}
                    unit=" km"
                  />
                  <Tooltip
                    contentStyle={{
                      fontSize: 12,
                      borderRadius: 'var(--radius-component-sm)',
                      border: '1px solid var(--color-border-default)',
                      background: 'var(--color-bg-base)',
                    }}
                    formatter={(value: number) => {
                      return [`${value.toFixed(1)} km`, 'Distanz'];
                    }}
                  />
                  <Bar dataKey="km" radius={[4, 4, 0, 0]}>
                    {volumeChartData.map((entry, index) => (
                      <Cell
                        key={index}
                        fill={
                          entry.change !== null && entry.change > 10
                            ? 'var(--color-bg-error)'
                            : 'var(--color-bg-primary)'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Muscle Group Balance */}
      {data.muscle_groups.length > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Dumbbell className="w-4 h-4 text-[var(--color-text-primary)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Muskelgruppen-Balance
              </h2>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {data.muscle_groups.map((mg) => (
                <div key={mg.group}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-[var(--color-text-base)]">
                      {mg.group}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {mg.total_sets} Sätze · {mg.percentage.toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={mg.percentage} color="default" />
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Insights */}
      {data.insights.length > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-[var(--color-text-primary)]" />
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Erkenntnisse
              </h2>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {data.insights.map((insight, i) => {
                const InsightIcon = INSIGHT_ICONS[insight.type];
                const colorClass = INSIGHT_COLORS[insight.type];
                return (
                  <div
                    key={i}
                    className="flex items-start gap-2.5"
                  >
                    <InsightIcon
                      className={`w-4 h-4 mt-0.5 shrink-0 ${colorClass}`}
                    />
                    <p className="text-sm text-[var(--color-text-base)]">
                      {insight.message}
                    </p>
                  </div>
                );
              })}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Empty state */}
      {data.sport_mix.total_sessions === 0 && (
        <Card elevation="raised" padding="spacious">
          <CardBody className="text-center py-12">
            <Activity className="w-8 h-8 text-[var(--color-text-disabled)] mx-auto mb-3" />
            <p className="text-sm text-[var(--color-text-muted)]">
              Keine Trainings im gewählten Zeitraum.
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
