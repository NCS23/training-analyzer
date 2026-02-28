import { useState, useEffect, useCallback, useRef } from 'react';
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
  Select,
  Input,
  DatePicker,
} from '@nordlig/components';
import {
  Upload,
  Dumbbell,
  Footprints,
  Activity,
  ChevronRight,
  EllipsisVertical,
  Search,
  X,
} from 'lucide-react';
import { listSessions } from '@/api/training';
import type { SessionSummary, SessionFilters } from '@/api/training';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';

const PAGE_SIZE = 20;

const workoutTypeLabels: Record<string, string> = {
  running: 'Laufen',
  strength: 'Kraft',
};

const workoutTypeOptions = [
  { value: '', label: 'Alle Typen' },
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
];

const trainingTypeLabels: Record<string, string> = {
  recovery: 'Recovery',
  easy: 'Easy Run',
  long_run: 'Long Run',
  tempo: 'Tempo',
  intervals: 'Intervall',
  race: 'Wettkampf',
  hill_repeats: 'Bergsprints',
};

const trainingTypeOptions = [
  { value: '', label: 'Alle Trainingstypen' },
  { value: 'recovery', label: 'Recovery' },
  { value: 'easy', label: 'Easy Run' },
  { value: 'long_run', label: 'Long Run' },
  { value: 'tempo', label: 'Tempo' },
  { value: 'intervals', label: 'Intervall' },
  { value: 'race', label: 'Wettkampf' },
  { value: 'hill_repeats', label: 'Bergsprints' },
];

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
          <Skeleton className="w-11 h-11 rounded-[var(--radius-xl)] shrink-0" />
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

/* ─── Filter helpers ─── */

const EMPTY_FILTERS: SessionFilters = {};

function hasActiveFilters(filters: SessionFilters): boolean {
  return !!(
    filters.workoutType ||
    filters.trainingType ||
    filters.dateFrom ||
    filters.dateTo ||
    filters.search
  );
}

/* ─── Main Component ─── */

export function SessionsPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [filters, setFilters] = useState<SessionFilters>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState('');
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();

  const loadSessions = useCallback(async (page: number, currentFilters: SessionFilters) => {
    setLoading(true);
    try {
      const result = await listSessions(page, PAGE_SIZE, currentFilters);
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
    loadSessions(1, filters);
  }, [loadSessions, filters]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handlePageChange = (page: number) => {
    loadSessions(page, filters);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const updateFilter = (key: keyof SessionFilters, value: string | undefined) => {
    setFilters((prev) => {
      const next = { ...prev, [key]: value || undefined };
      // Clean undefined keys
      Object.keys(next).forEach((k) => {
        if (next[k as keyof SessionFilters] === undefined) {
          delete next[k as keyof SessionFilters];
        }
      });
      return next;
    });
    setCurrentPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchInput(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      updateFilter('search', value.trim() || undefined);
    }, 400);
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    setSearchInput('');
    setCurrentPage(1);
  };

  const active = hasActiveFilters(filters);

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header className="flex items-end justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Sessions
          </h1>
          {!loading && (
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              {total} {active ? 'Treffer' : 'Trainings'}
            </p>
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
              <EllipsisVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              icon={<Upload className="w-4 h-4" />}
              onSelect={() => navigate('/sessions/new')}
            >
              Neues Training
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Filter bar — always visible */}
      <Card elevation="raised">
        <CardBody>
          <div className="space-y-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
              <Input
                value={searchInput}
                onChange={handleSearchChange}
                placeholder="Notizen durchsuchen..."
                inputSize="sm"
                className="pl-9"
              />
            </div>

            {/* Dropdowns + dates */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Select
                options={workoutTypeOptions}
                value={filters.workoutType ?? ''}
                onChange={(val) => updateFilter('workoutType', val || undefined)}
                inputSize="sm"
                placeholder="Workout-Typ"
              />
              <Select
                options={trainingTypeOptions}
                value={filters.trainingType ?? ''}
                onChange={(val) => updateFilter('trainingType', val || undefined)}
                inputSize="sm"
                placeholder="Trainingstyp"
              />
              <DatePicker
                value={filters.dateFrom ? parseISO(filters.dateFrom) : undefined}
                onChange={(d) => updateFilter('dateFrom', d ? format(d, 'yyyy-MM-dd') : undefined)}
                inputSize="sm"
                placeholder="Von"
              />
              <DatePicker
                value={filters.dateTo ? parseISO(filters.dateTo) : undefined}
                onChange={(d) => updateFilter('dateTo', d ? format(d, 'yyyy-MM-dd') : undefined)}
                inputSize="sm"
                placeholder="Bis"
              />
            </div>

            {/* Clear */}
            {active && (
              <div className="flex justify-end">
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="w-3.5 h-3.5" />
                  Filter zurücksetzen
                </Button>
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {loading ? (
        <SessionsLoadingSkeleton />
      ) : sessions.length === 0 ? (
        <Card elevation="raised">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-[var(--radius-2xl)] bg-[var(--color-primary-1-50)] mb-4">
              <Activity className="w-8 h-8 text-[var(--color-primary-1-500)]" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-2">
              {active ? 'Keine Treffer' : 'Keine Sessions vorhanden'}
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-6 max-w-sm">
              {active
                ? 'Versuche andere Filterkriterien oder setze die Filter zurück.'
                : 'Lade dein erstes Training hoch, um hier deine Trainingshistorie zu sehen.'}
            </p>
            {active ? (
              <Button variant="secondary" onClick={clearFilters}>
                <X className="w-4 h-4 mr-2" />
                Filter zurücksetzen
              </Button>
            ) : (
              <Button variant="primary" onClick={() => navigate('/sessions/new')}>
                <Upload className="w-4 h-4 mr-2" />
                Training hochladen
              </Button>
            )}
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
                  className="cursor-pointer hover:shadow-[var(--shadow-md)] transition-shadow rounded-[var(--radius-component-md)]"
                  onClick={() => navigate(`/sessions/${session.id}`)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/sessions/${session.id}`)}
                >
                  <Card elevation="raised">
                    <CardBody>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-11 h-11 shrink-0 rounded-[var(--radius-xl)] bg-[var(--color-primary-1-50)]">
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
                            {session.workout_type === 'strength' ? (
                              <>
                                {session.exercises_count != null && (
                                  <span>{session.exercises_count} Übungen</span>
                                )}
                                {session.total_tonnage_kg != null && (
                                  <span>
                                    {session.total_tonnage_kg >= 1000
                                      ? `${(session.total_tonnage_kg / 1000).toFixed(1)}t`
                                      : `${session.total_tonnage_kg} kg`}
                                  </span>
                                )}
                                {session.duration_sec && (
                                  <span>{formatDuration(session.duration_sec)}</span>
                                )}
                              </>
                            ) : (
                              <>
                                {session.distance_km && <span>{session.distance_km} km</span>}
                                {session.duration_sec && (
                                  <span>{formatDuration(session.duration_sec)}</span>
                                )}
                                {session.pace && <span>{session.pace} /km</span>}
                                {session.hr_avg && <span>{session.hr_avg} bpm</span>}
                              </>
                            )}
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
