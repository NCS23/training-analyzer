import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Badge,
  Spinner,
  Progress,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import {
  Upload,
  Activity,
  Clock,
  MapPin,
  Heart,
  TrendingUp,
  EllipsisVertical,
  Target,
  Calendar,
  Footprints,
  Dumbbell,
} from 'lucide-react';
import { listSessions } from '@/api/training';
import type { SessionSummary } from '@/api/training';
import { listGoals, getGoalProgress } from '@/api/goals';
import type { GoalProgress } from '@/api/goals';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [goalProgress, setGoalProgress] = useState<GoalProgress | null>(null);

  useEffect(() => {
    loadSessions();
    loadGoalProgress();
  }, []);

  const loadSessions = async () => {
    try {
      const result = await listSessions(1, 100);
      setSessions(result.sessions);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const loadGoalProgress = async () => {
    try {
      const goalsRes = await listGoals();
      const activeGoal = goalsRes.goals.find((g) => g.is_active);
      if (activeGoal) {
        const progress = await getGoalProgress(activeGoal.id);
        setGoalProgress(progress);
      }
    } catch {
      // Goal progress is optional — don't block the dashboard
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  // Calculate summary stats
  const totalSessions = sessions.length;
  const totalDistance = sessions.reduce((sum, s) => sum + (s.distance_km || 0), 0);
  const totalDuration = sessions.reduce((sum, s) => sum + (s.duration_sec || 0), 0);
  const avgHr =
    sessions.length > 0
      ? Math.round(
          sessions.reduce((sum, s) => sum + (s.hr_avg || 0), 0) /
            sessions.filter((s) => s.hr_avg).length,
        )
      : 0;

  if (totalSessions === 0) {
    return (
      <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
        <header className="pb-2">
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Dashboard
          </h1>
        </header>

        <Card elevation="raised">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-[var(--radius-2xl)] bg-[var(--color-bg-primary-subtle)] mb-4">
              <Activity className="w-8 h-8 text-[var(--color-primary-1-500)]" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-2">
              Willkommen beim Training Analyzer
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-6 max-w-sm">
              Noch keine Trainings vorhanden. Lade dein erstes Training hoch, um deine Analyse zu
              starten.
            </p>
            <Button variant="primary" onClick={() => navigate('/sessions/new')}>
              <Upload className="w-4 h-4 mr-2" />
              Training hochladen
            </Button>
          </CardBody>
        </Card>
      </div>
    );
  }

  const recentSessions = sessions.slice(0, 5);

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Dashboard
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
      </header>

      {/* Stat Metrics — same pattern as SessionDetail */}
      <Card elevation="raised">
        <CardBody>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-[10px]">
            <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
              <div className="flex items-center gap-1 mb-1 sm:mb-2">
                <TrendingUp className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-primary-1-500)]" />
                <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-primary-1-500)] uppercase tracking-wider">
                  Sessions
                </p>
              </div>
              <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                {totalSessions}
              </p>
            </div>
            <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
              <div className="flex items-center gap-1 mb-1 sm:mb-2">
                <MapPin className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-primary-1-500)]" />
                <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-primary-1-500)] uppercase tracking-wider">
                  Distanz
                </p>
              </div>
              <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                {totalDistance.toFixed(1)}
                <span className="text-[11px] sm:text-sm font-normal text-[var(--color-text-muted)] ml-0.5">
                  km
                </span>
              </p>
            </div>
            <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
              <div className="flex items-center gap-1 mb-1 sm:mb-2">
                <Clock className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-primary-1-500)]" />
                <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-primary-1-500)] uppercase tracking-wider">
                  Trainingszeit
                </p>
              </div>
              <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                {formatDuration(totalDuration)}
              </p>
            </div>
            {avgHr > 0 && (
              <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                <div className="flex items-center gap-1 mb-1 sm:mb-2">
                  <Heart className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-primary-1-500)]" />
                  <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-primary-1-500)] uppercase tracking-wider">
                    Ø HF
                  </p>
                </div>
                <p className="text-base sm:text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                  {avgHr}
                  <span className="text-[11px] sm:text-sm font-normal text-[var(--color-text-muted)] ml-0.5">
                    bpm
                  </span>
                </p>
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Goal Progress Card */}
      {goalProgress &&
        (() => {
          const isAhead = goalProgress.pace_gap_sec !== null && goalProgress.pace_gap_sec <= 0;
          const isBehind = goalProgress.pace_gap_sec !== null && goalProgress.pace_gap_sec > 0;
          return (
            <div
              className="cursor-pointer rounded-[var(--radius-xl)] border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-6 py-6 [box-shadow:var(--shadow-card-raised)] transition-shadow hover:[box-shadow:var(--shadow-card-hover)] motion-reduce:transition-none"
              onClick={() => navigate('/settings/goals')}
              role="link"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && navigate('/settings/goals')}
            >
              {/* Goal header */}
              <div className="flex items-start justify-between gap-3 mb-1">
                <div className="flex items-start gap-2 text-[15px] font-semibold leading-[1.4] flex-1 min-w-0">
                  <Target className="w-4 h-4 mt-0.5 shrink-0 text-[var(--color-primary-1-500)]" />
                  {goalProgress.goal.title}
                </div>
                {goalProgress.goal.days_until > 0 ? (
                  <span className="inline-flex shrink-0 items-center gap-[5px] rounded-full border border-[var(--color-primary-1-200)] bg-[var(--color-bg-primary-subtle)] px-3 py-1.5 text-[11.5px] font-medium text-[var(--color-primary-1-600)]">
                    <Calendar className="w-[11px] h-[11px]" />
                    {goalProgress.goal.days_until} Tage
                  </span>
                ) : goalProgress.goal.days_until === 0 ? (
                  <Badge variant="warning" size="xs">
                    Heute
                  </Badge>
                ) : (
                  <Badge variant="neutral" size="xs">
                    Vergangen
                  </Badge>
                )}
              </div>
              <p className="text-[12.5px] text-[var(--color-text-muted)] mb-5">
                {goalProgress.goal.distance_km} km · Zielzeit{' '}
                {goalProgress.goal.target_time_formatted}
              </p>

              {/* Pace tiles — gp-tile pattern: bg-paper + border */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-5">
                <div className="rounded-[var(--radius-lg)] border border-[var(--color-border-default)] bg-[var(--color-bg-paper)] px-3.5 py-3">
                  <div className="flex items-center gap-[5px] mb-[6px]">
                    <Target className="w-[11px] h-[11px] text-[var(--color-text-muted)]" />
                    <p className="text-[11px] font-semibold uppercase tracking-[0.5px] text-[var(--color-text-muted)]">
                      Ziel
                    </p>
                  </div>
                  <p className="text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                    {goalProgress.target_pace_formatted}
                    <span className="text-[12px] font-normal text-[var(--color-text-muted)] ml-[1px]">
                      /km
                    </span>
                  </p>
                </div>
                <div className="rounded-[var(--radius-lg)] border border-[var(--color-border-default)] bg-[var(--color-bg-paper)] px-3.5 py-3">
                  <div className="flex items-center gap-[5px] mb-[6px]">
                    <Activity className="w-[11px] h-[11px] text-[var(--color-text-muted)]" />
                    <p className="text-[11px] font-semibold uppercase tracking-[0.5px] text-[var(--color-text-muted)]">
                      Aktuell
                    </p>
                  </div>
                  <p className="text-[22px] font-semibold text-[var(--color-text-base)] leading-none">
                    {goalProgress.current_pace_formatted ?? '—'}
                    {goalProgress.current_pace_formatted && (
                      <span className="text-[12px] font-normal text-[var(--color-text-muted)] ml-[1px]">
                        /km
                      </span>
                    )}
                  </p>
                </div>
                <div className="col-span-2 sm:col-span-1 rounded-[var(--radius-lg)] border border-[var(--color-border-default)] bg-[var(--color-bg-paper)] px-3.5 py-3">
                  <div className="flex items-center gap-[5px] mb-[6px]">
                    <TrendingUp className="w-[11px] h-[11px] text-[var(--color-text-muted)]" />
                    <p className="text-[11px] font-semibold uppercase tracking-[0.5px] text-[var(--color-text-muted)]">
                      Differenz
                    </p>
                  </div>
                  <p
                    className={`text-[22px] font-semibold leading-none ${
                      isAhead
                        ? 'text-[var(--color-text-success)]'
                        : isBehind
                          ? 'text-[var(--color-text-warning)]'
                          : 'text-[var(--color-text-base)]'
                    }`}
                  >
                    {goalProgress.pace_gap_sec !== null
                      ? `${isAhead ? '−' : '+'}${goalProgress.pace_gap_formatted}`
                      : '—'}
                    {goalProgress.pace_gap_sec !== null && (
                      <span className="text-[12px] font-normal text-[var(--color-text-muted)] ml-[1px]">
                        /km
                      </span>
                    )}
                  </p>
                </div>
              </div>

              {/* Progress Bar */}
              {goalProgress.progress_percent !== null && (
                <div className="mb-5">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[12.5px] text-[var(--color-text-muted)]">
                      Fortschritt zum Ziel-Pace
                    </p>
                    <p className="text-[12.5px] text-[var(--color-text-muted)]">
                      {Math.round(goalProgress.progress_percent)}%
                    </p>
                  </div>
                  <Progress
                    value={Math.min(100, goalProgress.progress_percent)}
                    color={
                      goalProgress.progress_percent >= 100
                        ? 'success'
                        : goalProgress.progress_percent >= 70
                          ? 'default'
                          : 'warning'
                    }
                  />
                </div>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between">
                {goalProgress.weekly_pace_trend_label && goalProgress.sessions_used > 0 ? (
                  <p
                    className={`text-xs font-medium ${
                      goalProgress.weekly_pace_trend_sec !== null &&
                      goalProgress.weekly_pace_trend_sec > 0
                        ? 'text-[var(--color-text-success)]'
                        : goalProgress.weekly_pace_trend_sec !== null &&
                            goalProgress.weekly_pace_trend_sec < 0
                          ? 'text-[var(--color-text-warning)]'
                          : 'text-[var(--color-text-muted)]'
                    }`}
                  >
                    <TrendingUp className="w-3 h-3 inline mr-1" />
                    {goalProgress.weekly_pace_trend_label}
                  </p>
                ) : (
                  <p className="text-xs text-[var(--color-text-muted)] italic">
                    Noch keine Trend-Daten
                  </p>
                )}
                {goalProgress.sessions_used > 0 && (
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {goalProgress.sessions_used} Session
                    {goalProgress.sessions_used > 1 ? 's' : ''}
                  </p>
                )}
              </div>
            </div>
          );
        })()}

      {/* Letzte Trainings — simple title, no accent bar */}
      <div>
        <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-3">
          Letzte Trainings
        </h2>
        <div className="space-y-2.5">
          {recentSessions.map((session) => (
            <div
              key={session.id}
              className="flex items-center gap-3 cursor-pointer rounded-[var(--radius-xl)] border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-5 py-3.5 [box-shadow:var(--shadow-card-raised)] transition-shadow hover:[box-shadow:var(--shadow-card-hover)] motion-reduce:transition-none"
              onClick={() => navigate(`/sessions/${session.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && navigate(`/sessions/${session.id}`)}
            >
              {/* Icon */}
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--color-bg-primary-subtle)] text-[var(--color-primary-1-500)]">
                {session.workout_type === 'strength' ? (
                  <Dumbbell className="w-[18px] h-[18px]" />
                ) : (
                  <Footprints className="w-[18px] h-[18px]" />
                )}
              </div>
              {/* Body */}
              <div className="flex-1 min-w-0">
                <p className="text-[14px] font-semibold text-[var(--color-text-base)]">
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
                <div className="flex items-center gap-3 text-[12px] text-[var(--color-text-muted)] mt-[3px]">
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
                      {session.duration_sec && <span>{formatDuration(session.duration_sec)}</span>}
                    </>
                  ) : (
                    <>
                      {session.distance_km && <span>{session.distance_km} km</span>}
                      {session.duration_sec && <span>{formatDuration(session.duration_sec)}</span>}
                      {session.hr_avg && <span>{session.hr_avg} bpm</span>}
                    </>
                  )}
                </div>
              </div>
              {/* Badge */}
              <span className="shrink-0 rounded-full border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] px-3 py-1 text-[12px] font-medium text-[var(--color-text-muted)]">
                {session.workout_type === 'running' ? 'Laufen' : 'Kraft'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
