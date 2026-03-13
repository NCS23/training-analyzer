import { useState, useMemo } from 'react';
import { Card, CardBody, CardHeader, SegmentedControl } from '@nordlig/components';
import { BarChart3 } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { CATEGORY_LABELS } from '@/constants/training';
import type { CategoryTonnageTrendResponse } from '@/api/progression';

type ViewMode = 'total' | 'trend';

const VIEW_ITEMS = [
  { value: 'total', label: 'Gesamt' },
  { value: 'trend', label: 'Trend' },
];

/** Mapping category keys to chart color tokens */
const CATEGORY_COLORS: Record<string, string> = {
  push: 'var(--color-chart-1)',
  pull: 'var(--color-chart-2)',
  legs: 'var(--color-chart-3)',
  core: 'var(--color-chart-4)',
  cardio: 'var(--color-chart-5)',
  drills: 'var(--color-chart-5)',
};

const TOOLTIP_STYLE = {
  backgroundColor: 'var(--color-bg-elevated)',
  border: '1px solid var(--color-border-default)',
  borderRadius: '8px',
  fontSize: '12px',
};

const AXIS_TICK = { fontSize: 11, fill: 'var(--color-text-muted)' };

function categoryLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? key;
}

function formatTonnage(kg: number): string {
  return kg >= 1000 ? `${(kg / 1000).toFixed(1)}t` : `${Math.round(kg)} kg`;
}

function formatWeekLabel(weekStart: string): string {
  const [, month, day] = weekStart.split('-');
  return `${day}.${month}.`;
}

interface Props {
  data: CategoryTonnageTrendResponse | null;
}

/** Aggregated horizontal bar chart — tonnage per category over the entire period. */
function AggregatedView({ data }: { data: CategoryTonnageTrendResponse }) {
  const chartData = useMemo(
    () =>
      data.aggregated.map((c) => ({
        category: categoryLabel(c.category),
        tonnage: c.tonnage_kg,
        fill: CATEGORY_COLORS[c.category] ?? 'var(--color-chart-1)',
      })),
    [data.aggregated],
  );

  if (chartData.length === 0) return null;

  return (
    <div className="h-[200px]" aria-label="Kategorie-Tonnage Balkendiagramm">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border-muted)"
            horizontal={false}
          />
          <XAxis
            type="number"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => formatTonnage(v)}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            width={60}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value: number) => [formatTonnage(value), 'Tonnage']}
          />
          <Bar dataKey="tonnage" radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {chartData.map((entry, i) => (
              <rect key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Stacked bar chart — week-over-week tonnage per category. */
function TrendView({ data }: { data: CategoryTonnageTrendResponse }) {
  const { chartData, categories } = useMemo(() => {
    const allCats = new Set<string>();
    for (const week of data.weeks) {
      for (const c of week.categories) {
        allCats.add(c.category);
      }
    }
    const cats = Array.from(allCats).sort();

    const rows = data.weeks.map((week) => {
      const row: Record<string, string | number> = {
        label: formatWeekLabel(week.week_start),
      };
      for (const cat of cats) {
        const found = week.categories.find((c) => c.category === cat);
        row[cat] = found ? found.tonnage_kg : 0;
      }
      return row;
    });

    return { chartData: rows, categories: cats };
  }, [data.weeks]);

  if (chartData.length === 0) return null;

  return (
    <div className="h-[220px]" aria-label="Kategorie-Tonnage Trend">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-muted)" />
          <XAxis dataKey="label" tick={AXIS_TICK} tickLine={false} axisLine={false} />
          <YAxis
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => formatTonnage(v)}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value: number, name: string) => [formatTonnage(value), categoryLabel(name)]}
          />
          <Legend formatter={(value: string) => categoryLabel(value)} />
          {categories.map((cat) => (
            <Bar
              key={cat}
              dataKey={cat}
              stackId="tonnage"
              fill={CATEGORY_COLORS[cat] ?? 'var(--color-chart-1)'}
              radius={[0, 0, 0, 0]}
              isAnimationActive={false}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CategoryTonnageChart({ data }: Props) {
  const [view, setView] = useState<ViewMode>('total');

  if (!data || data.aggregated.length === 0) return null;

  return (
    <Card elevation="raised" padding="spacious">
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[var(--color-text-primary)]" />
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Kategorie-Tonnage
            </h2>
          </div>
          <SegmentedControl
            size="sm"
            value={view}
            onChange={(v) => setView(v as ViewMode)}
            items={VIEW_ITEMS}
          />
        </div>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Tonnage nach Muskelgruppe{view === 'trend' ? ' pro Woche' : ' gesamt'}. Insgesamt{' '}
          {formatTonnage(data.total_tonnage_kg)}.
        </p>
      </CardHeader>
      <CardBody>
        {view === 'total' ? <AggregatedView data={data} /> : <TrendView data={data} />}
      </CardBody>
    </Card>
  );
}
