import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Spinner,
  Alert,
  AlertDescription,
  ToggleGroup,
  ToggleGroupItem,
} from '@nordlig/components';
import { TrendingUp, Heart, MapPin } from 'lucide-react';
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
import { getTrends } from '@/api/trends';
import type { TrendResponse, WeeklyDataPoint } from '@/api/trends';

type TimeRange = '7' | '28' | '90';

const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  '7': '7 Tage',
  '28': '4 Wochen',
  '90': '3 Monate',
};

function formatWeekLabel(weekStart: string): string {
  try {
    const d = new Date(weekStart);
    return `${d.getDate()}.${d.getMonth() + 1}.`;
  } catch {
    return weekStart;
  }
}

function formatPace(secPerKm: number): string {
  const mins = Math.floor(secPerKm / 60);
  const secs = Math.round(secPerKm % 60);
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function TrendsPage() {
  const [data, setData] = useState<TrendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>('28');

  const loadTrends = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getTrends(parseInt(timeRange, 10));
      setData(result);
    } catch {
      setError('Trend-Daten konnten nicht geladen werden');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    loadTrends();
  }, [loadTrends]);

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.weeks.map((w: WeeklyDataPoint) => ({
      ...w,
      label: formatWeekLabel(w.week_start),
      pace_display: w.avg_pace_sec_per_km ? formatPace(w.avg_pace_sec_per_km) : null,
    }));
  }, [data]);

  const insightVariant = (type: string): 'success' | 'warning' | 'info' => {
    switch (type) {
      case 'positive':
        return 'success';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 pb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Trends
          </h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Entwicklung deiner Trainingsdaten über die Zeit.
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

      {loading && (
        <div className="flex items-center justify-center min-h-[30vh]">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!loading && data && chartData.length === 0 && (
        <Card elevation="raised">
          <CardBody className="py-12 text-center">
            <p className="text-sm text-[var(--color-text-muted)]">
              Keine Trainingsdaten im gewählten Zeitraum vorhanden.
            </p>
          </CardBody>
        </Card>
      )}

      {!loading && data && chartData.length > 0 && (
        <>
          {/* Insights */}
          {data.insights.length > 0 && (
            <div className="space-y-2">
              {data.insights.map((insight, i) => (
                <Alert key={i} variant={insightVariant(insight.type)}>
                  <AlertDescription>{insight.message}</AlertDescription>
                </Alert>
              ))}
            </div>
          )}

          {/* Pace Trend */}
          <Card elevation="raised" padding="spacious">
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[var(--color-primary-1-500)]" />
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                  Pace-Entwicklung
                </h2>
              </div>
            </CardHeader>
            <CardBody>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    />
                    <YAxis
                      domain={['auto', 'auto']}
                      tickFormatter={(v: number) => formatPace(v)}
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                      reversed
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-default)',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(value: number) => [formatPace(value), 'Ø Pace']}
                      labelFormatter={(label: string) => `KW ${label}`}
                    />
                    <Line
                      type="monotone"
                      dataKey="avg_pace_sec_per_km"
                      stroke="var(--color-primary-1-500)"
                      strokeWidth={2}
                      dot={{ r: 4, fill: 'var(--color-primary-1-500)' }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardBody>
          </Card>

          {/* HR Trend */}
          <Card elevation="raised" padding="spacious">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Heart className="w-4 h-4 text-[var(--color-accent-3-500)]" />
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                  Herzfrequenz-Entwicklung
                </h2>
              </div>
            </CardHeader>
            <CardBody>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    />
                    <YAxis
                      domain={['auto', 'auto']}
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-default)',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(value: number) => [`${value} bpm`, 'Ø HF']}
                      labelFormatter={(label: string) => `KW ${label}`}
                    />
                    <Line
                      type="monotone"
                      dataKey="avg_hr_bpm"
                      stroke="var(--color-accent-3-500)"
                      strokeWidth={2}
                      dot={{ r: 4, fill: 'var(--color-accent-3-500)' }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardBody>
          </Card>

          {/* Volume Trend */}
          <Card elevation="raised" padding="spacious">
            <CardHeader>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-[var(--color-accent-1-500)]" />
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                  Wochenvolumen
                </h2>
              </div>
            </CardHeader>
            <CardBody>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--color-bg-elevated)',
                        border: '1px solid var(--color-border-default)',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                      formatter={(value: number, name: string) => {
                        if (name === 'total_distance_km') return [`${value} km`, 'Distanz'];
                        if (name === 'total_duration_sec')
                          return [formatDuration(value), 'Dauer'];
                        return [value, name];
                      }}
                      labelFormatter={(label: string) => `KW ${label}`}
                    />
                    <Bar
                      dataKey="total_distance_km"
                      fill="var(--color-accent-1-400)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {/* Summary row */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-[var(--color-border-subtle)]">
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Gesamt-Distanz</p>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {chartData.reduce((s, w) => s + w.total_distance_km, 0).toFixed(1)} km
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Gesamt-Dauer</p>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {formatDuration(chartData.reduce((s, w) => s + w.total_duration_sec, 0))}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Sessions</p>
                  <p className="text-sm font-medium text-[var(--color-text-base)]">
                    {chartData.reduce((s, w) => s + w.session_count, 0)}
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
