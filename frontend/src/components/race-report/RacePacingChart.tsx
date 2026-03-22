import { Card, CardHeader, CardBody, Badge } from '@nordlig/components';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';
import type { PacingStrategy } from '@/api/training';
import type { KmSplit } from '@/api/training';

interface RacePacingChartProps {
  splits: KmSplit[];
  pacing: PacingStrategy | null;
  targetPaceSec?: number;
}

const PACING_BADGE_VARIANT: Record<string, 'success' | 'warning' | 'neutral'> = {
  negative_split: 'success',
  even_split: 'neutral',
  positive_split: 'warning',
};

export function RacePacingChart({ splits, pacing, targetPaceSec }: RacePacingChartProps) {
  const fullSplits = splits.filter((s) => !s.is_partial);
  if (fullSplits.length === 0) return null;

  const data = fullSplits.map((s) => ({
    km: `${s.km_number}`,
    pace: s.pace_min_per_km ? Math.round(s.pace_min_per_km * 60) : 0,
    paceFormatted: s.pace_formatted ?? '-',
  }));

  const paces = data.map((d) => d.pace).filter((p) => p > 0);
  const minPace = Math.max(0, Math.min(...paces) - 30);
  const maxPace = Math.max(...paces) + 15;

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Pace pro Kilometer
          </h2>
          {pacing && (
            <Badge variant={PACING_BADGE_VARIANT[pacing.type] ?? 'neutral'} size="xs">
              {pacing.label}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardBody>
        {pacing && (
          <div className="flex gap-4 mb-3 text-xs text-[var(--color-text-muted)]">
            <span>1. Haelfte: {pacing.first_half_pace_formatted}/km</span>
            <span>2. Haelfte: {pacing.second_half_pace_formatted}/km</span>
          </div>
        )}
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
            <XAxis dataKey="km" tick={{ fontSize: 11 }} />
            <YAxis
              domain={[minPace, maxPace]}
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) =>
                `${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')}`
              }
              reversed
            />
            <Tooltip
              formatter={(value) => {
                const v = Number(value);
                return [`${Math.floor(v / 60)}:${String(v % 60).padStart(2, '0')}/km`, 'Pace'];
              }}
              labelFormatter={(l) => `Km ${l}`}
            />
            <Bar dataKey="pace" fill="var(--color-bg-primary)" radius={[2, 2, 0, 0]} />
            {targetPaceSec && (
              <ReferenceLine
                y={targetPaceSec}
                stroke="var(--color-text-success)"
                strokeDasharray="4 4"
                label={{
                  value: 'Ziel',
                  position: 'right',
                  fontSize: 11,
                  fill: 'var(--color-text-success)',
                }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  );
}
