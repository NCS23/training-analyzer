import { Card, CardBody } from '@nordlig/components';
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
          <p className="text-sm font-medium text-[var(--color-text-base)]">Diese Woche</p>

          {/* Tages-Punkte */}
          <div className="mt-3 flex items-end justify-between gap-1" aria-hidden="true">
            {data.days.map((day) => (
              <div key={day.date} className="flex flex-1 flex-col items-center gap-1">
                <DayDot status={day.status} />
                <span className="text-[10px] text-[var(--color-text-muted)]">{day.day_name}</span>
              </div>
            ))}
          </div>

          {/* Zusammenfassung */}
          <div className="mt-4 flex gap-4 text-sm">
            <div>
              <span className="font-medium text-[var(--color-text-base)]">
                {data.sessions_completed}
              </span>
              <span className="text-[var(--color-text-muted)] ml-1">
                Session{data.sessions_completed !== 1 ? 's' : ''}
              </span>
            </div>
            {data.distance_completed_km > 0 && (
              <div>
                <span className="font-medium text-[var(--color-text-base)]">
                  {data.distance_completed_km.toFixed(1)}
                </span>
                <span className="text-[var(--color-text-muted)] ml-1">km</span>
              </div>
            )}
            {data.time_completed_seconds > 0 && (
              <div>
                <span className="font-medium text-[var(--color-text-base)]">
                  {formatDuration(data.time_completed_seconds)}
                </span>
                <span className="text-[var(--color-text-muted)] ml-1">Zeit</span>
              </div>
            )}
          </div>
        </CardBody>
      </Card>
    </section>
  );
}

type DayStatus = 'completed' | 'planned' | 'skipped' | 'extra' | 'rest';

const DOT_STYLES: Record<DayStatus, string> = {
  completed: 'h-3 w-3 rounded-full bg-[var(--color-interactive-primary)]',
  planned: 'h-3 w-3 rounded-full border-2 border-[var(--color-interactive-primary)] bg-transparent',
  skipped: 'h-3 w-3 rounded-full bg-[var(--color-text-error)] opacity-60',
  extra: 'h-3 w-3 rounded-full bg-[var(--color-text-success)]',
  rest: 'h-3 w-3 rounded-full bg-[var(--color-border-default)]',
};

function DayDot({ status }: { status: DayStatus }) {
  return <span className={DOT_STYLES[status]} />;
}
