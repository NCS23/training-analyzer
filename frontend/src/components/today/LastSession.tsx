import { useNavigate } from 'react-router-dom';
import { Card, CardBody, Button, Badge } from '@nordlig/components';
import { Activity, Clock, MapPin, Heart, Dumbbell, ChevronRight } from 'lucide-react';
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

const WORKOUT_BADGE: Record<string, 'neutral' | 'info' | 'warning'> = {
  running: 'info',
  strength: 'warning',
};

export function LastSession({ session }: Props) {
  const navigate = useNavigate();
  const isRunning = session.workout_type === 'running';

  return (
    <section aria-label="Letzte Session">
      <Card elevation="raised">
        <CardBody>
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm font-medium text-[var(--color-text-base)]">Letzte Session</p>
                <Badge variant={WORKOUT_BADGE[session.workout_type] ?? 'neutral'} size="sm">
                  {isRunning ? 'Laufen' : 'Kraft'}
                </Badge>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                {formatDate(session.date)}
                {session.training_type && ` · ${session.training_type}`}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/sessions/${session.id}`)}
              aria-label="Session-Details öffnen"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>

          {/* Metriken */}
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
            {isRunning ? (
              <>
                {session.distance_km != null && (
                  <MetricItem icon={<MapPin className="h-3.5 w-3.5" />}>
                    {session.distance_km.toFixed(1)} km
                  </MetricItem>
                )}
                {session.duration_seconds != null && (
                  <MetricItem icon={<Clock className="h-3.5 w-3.5" />}>
                    {formatDuration(session.duration_seconds)}
                  </MetricItem>
                )}
                {session.avg_pace_formatted && (
                  <MetricItem icon={<Activity className="h-3.5 w-3.5" />}>
                    {session.avg_pace_formatted} /km
                  </MetricItem>
                )}
                {session.avg_heartrate != null && (
                  <MetricItem icon={<Heart className="h-3.5 w-3.5" />}>
                    {Math.round(session.avg_heartrate)} bpm
                  </MetricItem>
                )}
              </>
            ) : (
              <>
                {session.exercise_count != null && (
                  <MetricItem icon={<Dumbbell className="h-3.5 w-3.5" />}>
                    {session.exercise_count} Übungen
                  </MetricItem>
                )}
                {session.tonnage_kg != null && (
                  <MetricItem icon={<Activity className="h-3.5 w-3.5" />}>
                    {session.tonnage_kg.toFixed(0)} kg Volumen
                  </MetricItem>
                )}
                {session.duration_seconds != null && (
                  <MetricItem icon={<Clock className="h-3.5 w-3.5" />}>
                    {formatDuration(session.duration_seconds)}
                  </MetricItem>
                )}
              </>
            )}
          </div>

          {/* Vergleichs-Message */}
          {session.comparison_message && (
            <p className="mt-3 text-xs text-[var(--color-text-subtle)]">
              {session.comparison_message}
            </p>
          )}
        </CardBody>
      </Card>
    </section>
  );
}

function MetricItem({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1 text-sm text-[var(--color-text-base)]">
      <span className="text-[var(--color-text-muted)]">{icon}</span>
      {children}
    </div>
  );
}
