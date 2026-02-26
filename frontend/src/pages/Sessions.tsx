import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Badge,
  Skeleton,
  SkeletonKeyframes,
  Pagination,
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

const PAGE_SIZE = 20;

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

/* ─── Skeleton Loader ─── */

function SessionCardSkeleton() {
  return (
    <Card elevation="raised">
      <CardBody>
        <div className="flex items-center gap-4">
          <Skeleton className="w-11 h-11 rounded-xl shrink-0" />
          <div className="flex-1 space-y-2.5">
            <Skeleton className="h-4 w-48 rounded" />
            <div className="flex gap-1.5">
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
            <div className="flex gap-3">
              <Skeleton className="h-3 w-12 rounded" />
              <Skeleton className="h-3 w-10 rounded" />
              <Skeleton className="h-3 w-16 rounded" />
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function SessionsLoadingSkeleton() {
  return (
    <>
      <SkeletonKeyframes />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <SessionCardSkeleton key={i} />
        ))}
      </div>
    </>
  );
}

/* ─── Main Component ─── */

export function SessionsPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const loadSessions = useCallback(async (page: number) => {
    setLoading(true);
    try {
      const result = await listSessions(page, PAGE_SIZE);
      setSessions(result.sessions);
      setTotal(result.total);
      setCurrentPage(result.page);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions(1);
  }, [loadSessions]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handlePageChange = (page: number) => {
    loadSessions(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header className="flex items-end justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">Sessions</h1>
          {!loading && (
            <p className="text-xs text-[var(--color-text-muted)] mt-1">{total} Trainings</p>
          )}
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

      {loading ? (
        <SessionsLoadingSkeleton />
      ) : sessions.length === 0 ? (
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
        <>
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

          {totalPages > 1 && (
            <div className="flex justify-center pt-2">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                variant="compact"
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
