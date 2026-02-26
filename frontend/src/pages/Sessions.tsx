import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Badge,
  Spinner,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import { Upload, Dumbbell, Footprints, Activity, ChevronRight, EllipsisVertical } from 'lucide-react';
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
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header className="flex items-end justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">Sessions</h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">{sessions.length} Trainings</p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
              <EllipsisVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem icon={<Upload className="w-4 h-4" />} onSelect={() => navigate('/sessions/new')}>
              Training hochladen
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {sessions.length === 0 ? (
        <Card elevation="raised">
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
                <Card elevation="raised">
                  <CardBody>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-11 h-11 shrink-0 rounded-xl bg-[var(--color-primary-1-50)]">
                        {session.workout_type === 'strength' ? (
                          <Dumbbell className="w-5 h-5 text-[var(--color-primary-1-500)]" />
                        ) : (
                          <Footprints className="w-5 h-5 text-[var(--color-primary-1-500)]" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0 space-y-2.5">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-medium text-[var(--color-text-base)] truncate">
                            {(() => {
                              try {
                                return format(parseISO(session.date), 'EEEE, d. MMM yyyy', {
                                  locale: de,
                                });
                              } catch {
                                return session.date;
                              }
                            })()}
                          </p>
                          <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                        </div>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <Badge variant="info" size="xs">
                            {workoutTypeLabels[session.workout_type] || session.workout_type}
                          </Badge>
                          {effectiveType && (
                            <Badge
                              variant={trainingTypeBadgeVariant[effectiveType] ?? 'info'}
                              size="xs"
                            >
                              {trainingTypeLabels[effectiveType] ?? effectiveType}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                          {session.distance_km && <span>{session.distance_km} km</span>}
                          {session.duration_sec && (
                            <span>{formatDuration(session.duration_sec)}</span>
                          )}
                          {session.pace && <span>{session.pace} /km</span>}
                          {session.hr_avg && <span>{session.hr_avg} bpm</span>}
                        </div>
                      </div>
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
