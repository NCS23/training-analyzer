import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
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
import {
  trainingTypeLabels,
  trainingTypeOptions as baseTrainingTypeOptions,
} from '@/constants/training';
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

const trainingTypeOptions = [
  { value: '', label: 'Alle Trainingstypen' },
  ...baseTrainingTypeOptions,
];

/* Colored border-style tags using primary/neutral tokens */
const tagBase =
  'inline-flex items-center rounded-full border-[1.5px] px-[var(--spacing-xs)] py-[3px] text-[11.5px] font-medium';
const workoutTagStyle = `${tagBase} bg-[var(--color-bg-primary-subtle)] text-[var(--color-primary-1-600)] border-[var(--color-primary-1-200)]`;
const strengthTagStyle = `${tagBase} bg-[var(--color-primary-2-50)] text-[var(--color-primary-2-600)] border-[var(--color-primary-2-200)]`;
const trainingTagStyle = `${tagBase} bg-[var(--color-secondary-1-100)] text-[var(--color-secondary-1-600)] border-[var(--color-secondary-1-200)]`;

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

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
export function SessionsPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [filters, setFilters] = useState<SessionFilters>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState('');
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(null);

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
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      <header className="pb-2">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Sessions
          </h1>
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
                Training hochladen
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {!loading && (
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            {total} {active ? 'Treffer' : 'Trainings'}
          </p>
        )}
      </header>

      {/* Filter bar — always visible */}
      <div className="rounded-[var(--radius-xl)] border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-5 py-4 [box-shadow:var(--shadow-card-raised)]">
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
      </div>

      {loading ? (
        <SessionsLoadingSkeleton />
      ) : sessions.length === 0 ? (
        <Card elevation="raised">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-[var(--radius-2xl)] bg-[var(--color-bg-primary-subtle)] mb-[var(--spacing-md)]">
              <Activity className="w-8 h-8 text-[var(--color-primary-1-500)]" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-2">
              {active ? 'Keine Treffer' : 'Keine Sessions vorhanden'}
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-[var(--spacing-lg)] max-w-sm">
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
          <div className="space-y-2.5">
            {/* eslint-disable-next-line complexity -- TODO: E16 Refactoring */}
            {sessions.map((session) => {
              const effectiveType = session.training_type?.effective;
              return (
                <div
                  key={session.id}
                  className="flex items-center gap-3 cursor-pointer rounded-[var(--radius-xl)] border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-5 py-[var(--spacing-md)] [box-shadow:var(--shadow-card-raised)] transition-shadow hover:[box-shadow:var(--shadow-card-hover)] motion-reduce:transition-none"
                  onClick={() => navigate(`/sessions/${session.id}`)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/sessions/${session.id}`)}
                >
                  {/* Icon */}
                  <div className="flex h-[var(--spacing-xl)] w-[var(--spacing-xl)] shrink-0 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--color-bg-primary-subtle)] text-[var(--color-interactive-primary)]">
                    {session.workout_type === 'strength' ? (
                      <Dumbbell className="w-[18px] h-[18px]" />
                    ) : (
                      <Footprints className="w-[18px] h-[18px]" />
                    )}
                  </div>
                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    <p className="text-[14px] font-semibold text-[var(--color-text-base)] mb-[5px]">
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
                    {/* Location + Wetter + Tageszeit */}
                    {(session.location_name || session.weather_label || session.daytime_label) && (
                      <p className="text-[11px] text-[var(--color-text-muted)] mb-[4px] truncate">
                        {[session.location_name, session.weather_label, session.daytime_label]
                          .filter(Boolean)
                          .join(' · ')}
                      </p>
                    )}
                    {/* Colored border tags */}
                    <div className="flex items-center gap-1.5 flex-wrap mb-[6px]">
                      <span
                        className={
                          session.workout_type === 'strength' ? strengthTagStyle : workoutTagStyle
                        }
                      >
                        {workoutTypeLabels[session.workout_type] || session.workout_type}
                      </span>
                      {effectiveType && (
                        <span className={trainingTagStyle}>
                          {trainingTypeLabels[effectiveType] ?? effectiveType}
                        </span>
                      )}
                    </div>
                    {/* Meta */}
                    <div className="text-[12px] text-[var(--color-text-muted)]">
                      {session.workout_type === 'strength'
                        ? [
                            session.exercises_count != null && `${session.exercises_count} Übungen`,
                            session.total_tonnage_kg != null &&
                              (session.total_tonnage_kg >= 1000
                                ? `${(session.total_tonnage_kg / 1000).toFixed(1)}t`
                                : `${session.total_tonnage_kg} kg`),
                            session.duration_sec && formatDuration(session.duration_sec),
                          ]
                            .filter(Boolean)
                            .join(' \u00b7 ')
                        : [
                            session.distance_km && `${session.distance_km} km`,
                            session.duration_sec && formatDuration(session.duration_sec),
                            session.pace && `${session.pace} /km`,
                            session.hr_avg && `${session.hr_avg} bpm`,
                          ]
                            .filter(Boolean)
                            .join(' \u00b7 ')}
                    </div>
                  </div>
                  {/* Chevron */}
                  <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
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
