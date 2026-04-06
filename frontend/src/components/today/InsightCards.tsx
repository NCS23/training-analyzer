import {
  AlertTriangle,
  AlertCircle,
  Flame,
  BatteryLow,
  TrendingUp,
  TrendingDown,
  Zap,
  Dumbbell,
  CalendarX,
  CheckCircle,
  Info,
} from 'lucide-react';
import type { InsightResponse } from '@/api/fitness';

interface Props {
  insights: InsightResponse[];
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  'alert-triangle': AlertTriangle,
  'alert-circle': AlertCircle,
  flame: Flame,
  'battery-low': BatteryLow,
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
  zap: Zap,
  dumbbell: Dumbbell,
  'calendar-x': CalendarX,
  'check-circle': CheckCircle,
  info: Info,
};

const TYPE_COLOR: Record<InsightResponse['type'], string> = {
  warning: 'var(--color-text-error)',
  recommendation: 'var(--color-text-warning)',
  trend: 'var(--color-interactive-primary)',
  achievement: 'var(--color-text-success)',
  info: 'var(--color-text-muted)',
};

export function InsightCards({ insights }: Props) {
  if (insights.length === 0) return null;

  return (
    <section aria-label="Trainings-Insights" className="space-y-0">
      {insights.map((insight, i) => {
        const IconComponent = ICON_MAP[insight.icon] ?? Info;
        const color = TYPE_COLOR[insight.type] ?? 'var(--color-text-muted)';

        return (
          <div
            key={`${insight.type}-${insight.title}-${i}`}
            className={`flex gap-3 py-3 ${i > 0 ? 'border-t border-[var(--color-border-default)]' : ''}`}
          >
            <div className="mt-0.5 shrink-0" style={{ color }} aria-hidden="true">
              <IconComponent className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-[var(--color-text-base)]">{insight.title}</p>
              <p className="mt-0.5 text-xs text-[var(--color-text-muted)] leading-relaxed">
                {insight.message}
              </p>
            </div>
          </div>
        );
      })}
    </section>
  );
}
