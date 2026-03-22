import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { ElevationSegment } from '@/api/pacing';

interface ElevationChartProps {
  segments: ElevationSegment[];
}

export function ElevationChart({ segments }: ElevationChartProps) {
  const totalGain = segments.reduce((sum, s) => sum + s.gain_m, 0);
  const totalLoss = segments.reduce((sum, s) => sum + s.loss_m, 0);
  const chartData = segments.map((s) => ({
    km: `${s.km}`,
    gain: s.gain_m,
    loss: -s.loss_m,
  }));

  return (
    <div className="space-y-2">
      <div className="flex gap-4 text-xs text-[var(--color-text-muted)]">
        <span>
          Anstieg: <strong>{Math.round(totalGain)}m</strong>
        </span>
        <span>
          Abstieg: <strong>{Math.round(totalLoss)}m</strong>
        </span>
        <span>{segments.length} km</span>
      </div>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={0}>
            <XAxis
              dataKey="km"
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              interval={Math.max(0, Math.floor(chartData.length / 10) - 1)}
            />
            <YAxis
              tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
              width={30}
              tickFormatter={(v: number) => `${Math.abs(v)}`}
            />
            <Tooltip
              formatter={(value, name) => [
                `${Math.abs(Number(value)).toFixed(1)}m`,
                name === 'gain' ? 'Anstieg' : 'Abstieg',
              ]}
              labelFormatter={(label) => `km ${label}`}
              contentStyle={{
                fontSize: 12,
                borderRadius: 'var(--radius-component-sm)',
                border: '1px solid var(--color-border-muted)',
              }}
            />
            <ReferenceLine y={0} stroke="var(--color-border-muted)" />
            <Bar dataKey="gain" fill="var(--color-text-success)" radius={[2, 2, 0, 0]} />
            <Bar dataKey="loss" fill="var(--color-text-error)" radius={[0, 0, 2, 2]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
