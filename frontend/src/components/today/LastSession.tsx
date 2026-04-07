import { useNavigate, Link } from 'react-router-dom';
import { Card, CardBody } from '@nordlig/components';
import { Activity, Clock, MapPin, Heart, Dumbbell, ChevronRight, List } from 'lucide-react';
import type { LastSessionSummary } from '@/api/fitness';

interface Props {
  session: LastSessionSummary;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatDate(isoDate: string): string {
  try {
    const d = new Date(isoDate);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return 'Heute';
    if (d.toDateString() === yesterday.toDateString()) return 'Gestern';
    return d.toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'short' });
  } catch {
    return isoDate;
  }
}

const TYPE_ICON: Record<string, typeof Activity> = {
  running: Activity,
  strength: Dumbbell,
};

export function LastSession({ session }: Props) {
  const navigate = useNavigate();
  const isRunning = session.workout_type === 'running';
  const TypeIcon = TYPE_ICON[session.workout_type] ?? Activity;

  return (
    <section aria-label="Letzte Session">
      <Card elevation="raised">
        <CardBody>
          <button
            type="button"
            className="flex items-center justify-between gap-3 w-full text-left"
            onClick={() => navigate(`/sessions/${session.id}`)}
          >
            {/* Icon */}
            <div className="flex items-center justify-center h-10 w-10 shrink-0 rounded-full bg-[var(--color-bg-subtle)]">
              <TypeIcon className="h-5 w-5 text-[var(--color-interactive-primary)]" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <p className="text-sm font-medium text-[var(--color-text-base)]">
                  {formatDate(session.date)}
                </p>
                {session.training_type && (
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {session.training_type}
                  </span>
                )}
              </div>

              {/* Metriken inline */}
              <div className="mt-0.5 flex flex-wrap gap-x-3 text-xs text-[var(--color-text-muted)]">
                {isRunning ? (
                  <>
                    {session.distance_km != null && (
                      <Metric icon={MapPin}>{session.distance_km.toFixed(1)} km</Metric>
                    )}
                    {session.duration_seconds != null && (
                      <Metric icon={Clock}>{formatDuration(session.duration_seconds)}</Metric>
                    )}
                    {session.avg_pace_formatted && (
                      <Metric icon={Activity}>{session.avg_pace_formatted}/km</Metric>
                    )}
                    {session.avg_heartrate != null && (
                      <Metric icon={Heart}>{Math.round(session.avg_heartrate)} bpm</Metric>
                    )}
                  </>
                ) : (
                  <>
                    {session.exercise_count != null && (
                      <Metric icon={Dumbbell}>{session.exercise_count} Übungen</Metric>
                    )}
                    {session.duration_seconds != null && (
                      <Metric icon={Clock}>{formatDuration(session.duration_seconds)}</Metric>
                    )}
                  </>
                )}
              </div>

              {/* Vergleich — emotional hervorgehoben */}
              {session.comparison_message && (
                <p
                  className="mt-1 text-xs font-medium"
                  style={{
                    color: session.comparison_message.includes('schneller')
                      ? 'var(--color-text-success)'
                      : 'var(--color-text-muted)',
                  }}
                >
                  {session.comparison_message}
                </p>
              )}
            </div>

            {/* Chevron */}
            <ChevronRight className="h-4 w-4 shrink-0 text-[var(--color-text-muted)]" />
          </button>

          {/* Link zu allen Sessions */}
          <div className="mt-3 pt-3 border-t border-[var(--color-border-default)]">
            <Link
              to="/sessions"
              className="flex items-center gap-1.5 text-xs font-medium text-[var(--color-interactive-primary)] hover:underline"
            >
              <List className="h-3.5 w-3.5" />
              Alle Sessions
            </Link>
          </div>
        </CardBody>
      </Card>
    </section>
  );
}

function Metric({ icon: Icon, children }: { icon: typeof Activity; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-0.5">
      <Icon className="h-3 w-3" />
      {children}
    </span>
  );
}
