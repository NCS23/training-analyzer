import { Card, CardBody, Badge } from '@nordlig/components';
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

// Lucide-Icon-Map für Backend-Icon-Namen
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

const TYPE_BADGE: Record<
  InsightResponse['type'],
  'error' | 'warning' | 'success' | 'info' | 'neutral'
> = {
  warning: 'error',
  recommendation: 'warning',
  trend: 'info',
  achievement: 'success',
  info: 'neutral',
};

export function InsightCards({ insights }: Props) {
  if (insights.length === 0) return null;

  return (
    <section aria-label="Trainings-Insights">
      <div className="space-y-2">
        {insights.map((insight, i) => (
          <InsightCard key={`${insight.type}-${insight.title}-${i}`} insight={insight} />
        ))}
      </div>
    </section>
  );
}

function InsightCard({ insight }: { insight: InsightResponse }) {
  const IconComponent = ICON_MAP[insight.icon] ?? Info;
  const badgeVariant = TYPE_BADGE[insight.type] ?? 'neutral';

  return (
    <Card elevation="flat">
      <CardBody>
        <div className="flex gap-3">
          <div className="mt-0.5 shrink-0 text-[var(--color-text-muted)]" aria-hidden="true">
            <IconComponent className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-medium text-[var(--color-text-base)]">{insight.title}</p>
              <Badge variant={badgeVariant} size="sm">
                {insight.type === 'warning'
                  ? 'Warnung'
                  : insight.type === 'recommendation'
                    ? 'Tipp'
                    : insight.type === 'achievement'
                      ? 'Erfolg'
                      : insight.type === 'trend'
                        ? 'Trend'
                        : 'Info'}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-[var(--color-text-subtle)]">{insight.message}</p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
