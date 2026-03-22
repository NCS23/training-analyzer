import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { Card, CardBody } from '@nordlig/components';
import type { PacingResponse } from '@/api/pacing';

interface PacingChartProps {
  result: PacingResponse;
}

function formatPace(sec: number): string {
  const mins = Math.floor(sec / 60);
  const secs = Math.round(sec % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function PacingChart({ result }: PacingChartProps) {
  const data = result.splits.map((s) => ({
    km: s.distance_km < 1 ? `${s.km}*` : String(s.km),
    pace: s.target_pace_sec_per_km,
    gain: s.elevation_gain_m,
    loss: s.elevation_loss_m,
  }));

  const paces = data.map((d) => d.pace);
  const minPace = Math.floor(Math.min(...paces) / 10) * 10 - 10;
  const maxPace = Math.ceil(Math.max(...paces) / 10) * 10 + 10;

  return (
    <Card elevation="raised">
      <CardBody>
        <h3 className="text-sm font-semibold text-[var(--color-text-base)] mb-3">Pace-Verlauf</h3>
        <div className="h-48 md:h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-muted)" />
              <XAxis
                dataKey="km"
                tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                tickLine={false}
              />
              <YAxis
                yAxisId="pace"
                domain={[minPace, maxPace]}
                reversed
                tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                tickFormatter={formatPace}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                yAxisId="elev"
                orientation="right"
                tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                tickLine={false}
                axisLine={false}
                hide
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--color-bg-elevated)',
                  border: '1px solid var(--color-border-default)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                }}
                formatter={(value, name) => {
                  const v = Number(value);
                  if (name === 'pace') return [formatPace(v) + '/km', 'Pace'];
                  if (name === 'gain') return [v.toFixed(0) + 'm', 'Anstieg'];
                  if (name === 'loss') return [v.toFixed(0) + 'm', 'Abstieg'];
                  return [String(value), String(name)];
                }}
              />
              <Bar
                yAxisId="elev"
                dataKey="gain"
                fill="var(--color-chart-2)"
                opacity={0.3}
                radius={[2, 2, 0, 0]}
              />
              <Line
                yAxisId="pace"
                type="monotone"
                dataKey="pace"
                stroke="var(--color-chart-1)"
                strokeWidth={2}
                dot={{ r: 3, fill: 'var(--color-chart-1)' }}
                activeDot={{ r: 5 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardBody>
    </Card>
  );
}
