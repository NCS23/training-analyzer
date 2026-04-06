import { Card, CardBody } from '@nordlig/components';
import { Check } from 'lucide-react';
import type { WeekProgressResponse } from '@/api/fitness';

interface Props {
  data: WeekProgressResponse;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function WeekProgress({ data }: Props) {
  return (
    <section aria-label="Wochenfortschritt">
      <Card elevation="raised">
        <CardBody>
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[var(--color-text-base)]">Diese Woche</p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {data.sessions_completed} Session{data.sessions_completed !== 1 ? 's' : ''}
              {data.distance_completed_km > 0 && ` · ${data.distance_completed_km.toFixed(1)} km`}
              {data.time_completed_seconds > 0 &&
                ` · ${formatDuration(data.time_completed_seconds)}`}
            </p>
          </div>

          {/* Tages-Circles */}
          <div className="mt-3 flex items-center justify-between" aria-hidden="true">
            {data.days.map((day) => (
              <DayCircle key={day.date} dayName={day.day_name} status={day.status} />
            ))}
          </div>
        </CardBody>
      </Card>
    </section>
  );
}

type DayStatus = 'completed' | 'planned' | 'skipped' | 'extra' | 'rest';

const CIRCLE_BASE =
  'flex items-center justify-center h-8 w-8 rounded-full transition-colors duration-300 motion-reduce:transition-none';

const CIRCLE_STYLES: Record<DayStatus, string> = {
  completed: `${CIRCLE_BASE} bg-[var(--color-interactive-primary)] text-[var(--color-text-on-primary)]`,
  planned: `${CIRCLE_BASE} border-2 border-[var(--color-interactive-primary)] bg-transparent`,
  skipped: `${CIRCLE_BASE} bg-[var(--color-bg-error-subtle)]`,
  extra: `${CIRCLE_BASE} bg-[var(--color-text-success)] text-[var(--color-text-on-primary)]`,
  rest: `${CIRCLE_BASE} bg-[var(--color-bg-subtle)]`,
};

function DayCircle({ dayName, status }: { dayName: string; status: DayStatus }) {
  const showCheck = status === 'completed' || status === 'extra';

  return (
    <div className="flex flex-col items-center gap-1.5">
      <span className={CIRCLE_STYLES[status]}>
        {showCheck ? <Check className="h-4 w-4" strokeWidth={2.5} /> : null}
      </span>
      <span className="text-[10px] text-[var(--color-text-muted)]">{dayName}</span>
    </div>
  );
}
