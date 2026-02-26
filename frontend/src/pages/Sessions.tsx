import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Badge,
  Spinner,
} from '@nordlig/components';
import { Upload, Dumbbell, Activity, ChevronRight } from 'lucide-react';
import { listSessions } from '@/api/training';
import type { SessionSummary } from '@/api/training';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';

const workoutTypeLabels: Record<string, string> = {
  running: 'Laufen',
  strength: 'Kraft',
};

const trainingTypeLabels: Record<string, string> = {
  recovery: 'Recovery',
  easy: 'Easy Run',
  long_run: 'Long Run',
  tempo: 'Tempo',
  intervals: 'Intervall',
  race: 'Wettkampf',
  hill_repeats: 'Bergsprints',
};

const trainingTypeBadgeVariant: Record<string, 'info' | 'success' | 'warning' | 'error'> = {
  recovery: 'info',
  easy: 'success',
  long_run: 'success',
  tempo: 'warning',
  intervals: 'error',
  race: 'error',
  hill_repeats: 'warning',
};

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function SessionsPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await listSessions();
      setSessions(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-primary-1-100)]">
            <Dumbbell className="w-5 h-5 text-[var(--color-primary-1-600)]" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[var(--color-text-base)]">Sessions</h1>
            <p className="text-xs text-[var(--color-text-muted)]">{sessions.length} Trainings</p>
          </div>
        </div>
        <Button variant="primary" size="sm" onClick={() => navigate('/sessions/new')}>
          <Upload className="w-4 h-4 mr-2" />
          Hochladen
        </Button>
      </header>

      {sessions.length === 0 ? (
        <Card elevation="raised" className="bg-white">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--color-primary-1-50)] mb-4">
              <Activity className="w-8 h-8 text-[var(--color-primary-1-500)]" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-2">
              Keine Sessions vorhanden
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-6 max-w-sm">
              Lade dein erstes Training hoch, um hier deine Trainingshistorie zu sehen.
            </p>
            <Button variant="primary" onClick={() => navigate('/sessions/new')}>
              <Upload className="w-4 h-4 mr-2" />
              Training hochladen
            </Button>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => {
            const effectiveType = session.training_type?.effective;
            return (
              <div
                key={session.id}
                className="cursor-pointer hover:shadow-md transition-shadow rounded-[var(--radius-component-md)]"
                onClick={() => navigate(`/sessions/${session.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && navigate(`/sessions/${session.id}`)}
              >
                <Card elevation="raised" padding="compact" className="bg-white">
                  <CardBody>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-[var(--color-primary-1-50)]">
                          <Activity className="w-5 h-5 text-[var(--color-primary-1-500)]" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-[var(--color-text-base)]">
                            {(() => {
                              try {
                                return format(parseISO(session.date), 'EEEE, d. MMM yyyy', { locale: de });
                              } catch {
                                return session.date;
                              }
                            })()}
                          </p>
                          <div className="flex items-center gap-3 mt-0.5">
                            <Badge variant="info" size="sm">
                              {workoutTypeLabels[session.workout_type] || session.workout_type}
                            </Badge>
                            {effectiveType && (
                              <Badge
                                variant={trainingTypeBadgeVariant[effectiveType] ?? 'info'}
                                size="sm"
                              >
                                {trainingTypeLabels[effectiveType] ?? effectiveType}
                              </Badge>
                            )}
                            <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                              {session.distance_km && <span>{session.distance_km} km</span>}
                              {session.duration_sec && <span>{formatDuration(session.duration_sec)}</span>}
                              {session.pace && <span>{session.pace} /km</span>}
                              {session.hr_avg && <span>{session.hr_avg} bpm</span>}
                            </div>
                          </div>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                    </div>
                  </CardBody>
                </Card>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
