import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export interface ChartData {
  type: 'bar' | 'line';
  title?: string;
  data: Record<string, string | number>[];
  xKey: string;
  yKey: string;
  yLabel?: string;
  color?: string;
}

interface ChatChartProps {
  chart: ChartData;
}

const DEFAULT_COLOR = 'var(--color-interactive-primary)';

/**
 * Mini-Chart für den KI-Chat.
 * Unterstützt Bar- und Line-Charts mit Recharts.
 */
export function ChatChart({ chart }: ChatChartProps) {
  const { type, title, data, xKey, yKey, yLabel, color = DEFAULT_COLOR } = chart;

  if (!data?.length) return null;

  return (
    <div className="my-2 space-y-1">
      {title && <p className="text-xs font-medium text-[var(--color-text-muted)]">{title}</p>}
      <div className="h-[160px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {type === 'bar' ? (
            <BarChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey={xKey} tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  fontSize: 11,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border-default)',
                }}
                labelStyle={{ fontWeight: 600 }}
              />
              <Bar dataKey={yKey} fill={color} radius={[3, 3, 0, 0]} name={yLabel ?? yKey} />
            </BarChart>
          ) : (
            <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey={xKey} tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  fontSize: 11,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border-default)',
                }}
                labelStyle={{ fontWeight: 600 }}
              />
              <Line
                type="monotone"
                dataKey={yKey}
                stroke={color}
                strokeWidth={2}
                dot={{ r: 3 }}
                name={yLabel ?? yKey}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
