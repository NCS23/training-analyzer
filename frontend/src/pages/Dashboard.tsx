import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
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
      <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
        <header className="pb-2">
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Dashboard
          </h1>
        </header>

        <Card elevation="raised">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-[var(--radius-2xl)] bg-[var(--color-bg-primary-subtle)] mb-4">
              <Activity className="w-8 h-8 text-[var(--color-bg-primary-subtle0)]" />
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
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header className="flex items-end justify-between gap-4 pb-2">
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
              Laufen hochladen
            </DropdownMenuItem>
            <DropdownMenuItem
              icon={<Dumbbell className="w-4 h-4" />}
              onSelect={() => navigate('/sessions/new/strength')}
            >
              Krafttraining erfassen
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card elevation="raised" padding="compact">
          <CardBody>
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="w-5 h-5 text-[var(--color-chart-1)]" />
              <p className="text-xs font-medium text-[var(--color-chart-1)] uppercase tracking-wider">
                Sessions
              </p>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-base)]">{totalSessions}</p>
          </CardBody>
        </Card>
        <Card elevation="raised" padding="compact">
          <CardBody>
            <div className="flex items-center gap-1.5 mb-2">
              <MapPin className="w-5 h-5 text-[var(--color-chart-2)]" />
              <p className="text-xs font-medium text-[var(--color-chart-2)] uppercase tracking-wider">
                Distanz
              </p>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-base)]">
              {totalDistance.toFixed(1)}{' '}
              <span className="text-sm font-normal text-[var(--color-text-muted)]">km</span>
            </p>
          </CardBody>
        </Card>
        <Card elevation="raised" padding="compact">
          <CardBody>
            <div className="flex items-center gap-1.5 mb-2">
              <Clock className="w-5 h-5 text-[var(--color-chart-3)]" />
              <p className="text-xs font-medium text-[var(--color-chart-3)] uppercase tracking-wider">
                Trainingszeit
              </p>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-base)]">
              {formatDuration(totalDuration)}
            </p>
          </CardBody>
        </Card>
        {avgHr > 0 && (
          <Card elevation="raised" padding="compact">
            <CardBody>
              <div className="flex items-center gap-1.5 mb-2">
                <Heart className="w-5 h-5 text-[var(--color-chart-4)]" />
                <p className="text-xs font-medium text-[var(--color-chart-4)] uppercase tracking-wider">
                  Ø HF
                </p>
              </div>
              <p className="text-2xl font-bold text-[var(--color-text-base)]">
                {avgHr}{' '}
                <span className="text-sm font-normal text-[var(--color-text-muted)]">bpm</span>
              </p>
            </CardBody>
          </Card>
        )}
      </div>

      {/* Goal Progress Card */}
      {goalProgress &&
        (() => {
          const isAhead =
            goalProgress.pace_gap_sec !== null && goalProgress.pace_gap_sec <= 0;
          const isBehind =
            goalProgress.pace_gap_sec !== null && goalProgress.pace_gap_sec > 0;
          return (
            <Card
              elevation="raised"
              padding="spacious"
              hoverable
              className="cursor-pointer"
              onClick={() => navigate('/settings/goals')}
              role="link"
            >
              <CardHeader>
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-[var(--color-text-primary)]" />
                    <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                      {goalProgress.goal.title}
                    </h2>
                  </div>
                  {goalProgress.goal.days_until > 0 ? (
                    <Badge variant="info" size="xs">
                      <Calendar className="w-3 h-3 mr-1" />
                      {goalProgress.goal.days_until} Tage
                    </Badge>
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
                <p className="text-xs text-[var(--color-text-muted)] mt-1">
                  {goalProgress.goal.distance_km} km · Zielzeit{' '}
                  {goalProgress.goal.target_time_formatted}
                </p>
              </CardHeader>
              <CardBody>
                <div className="space-y-6">
                  {/* Pace Metrics — flat surface boxes, NO card-on-card */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Target className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                        <p className="text-xs text-[var(--color-text-muted)]">Ziel</p>
                      </div>
                      <p className="text-xl font-bold text-[var(--color-text-base)] tabular-nums">
                        {goalProgress.target_pace_formatted}
                        <span className="text-xs font-normal text-[var(--color-text-muted)] ml-1">
                          /km
                        </span>
                      </p>
                    </div>
                    <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Activity className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                        <p className="text-xs text-[var(--color-text-muted)]">Aktuell</p>
                      </div>
                      <p className="text-xl font-bold text-[var(--color-text-base)] tabular-nums">
                        {goalProgress.current_pace_formatted ?? '—'}
                        {goalProgress.current_pace_formatted && (
                          <span className="text-xs font-normal text-[var(--color-text-muted)] ml-1">
                            /km
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="col-span-2 sm:col-span-1 rounded-[var(--radius-component-md)] bg-[var(--color-bg-surface)] px-3 py-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingUp className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                        <p className="text-xs text-[var(--color-text-muted)]">Differenz</p>
                      </div>
                      <p
                        className={`text-xl font-bold tabular-nums ${
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
                          <span className="text-xs font-normal text-[var(--color-text-muted)] ml-1">
                            /km
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {goalProgress.progress_percent !== null && (
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs text-[var(--color-text-muted)]">
                          Fortschritt zum Ziel-Pace
                        </p>
                        <p className="text-xs font-medium text-[var(--color-text-base)]">
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

                  {/* Trend + Sessions */}
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
              </CardBody>
            </Card>
          );
        })()}

      {/* Recent Sessions */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-1 h-6 rounded-full bg-[var(--color-bg-primary-subtle0)]" />
          <h2 className="text-lg font-semibold text-[var(--color-text-base)]">Letzte Trainings</h2>
        </div>
        <div className="space-y-3">
          {recentSessions.map((session) => (
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
                    <div className="flex items-center justify-center w-11 h-11 shrink-0 rounded-[var(--radius-xl)] bg-[var(--color-bg-primary-subtle)]">
                      {session.workout_type === 'strength' ? (
                        <Dumbbell className="w-5 h-5 text-[var(--color-bg-primary-subtle0)]" />
                      ) : (
                        <Footprints className="w-5 h-5 text-[var(--color-bg-primary-subtle0)]" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
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
                        <Badge variant="info" size="xs">
                          {session.workout_type === 'running' ? 'Laufen' : 'Kraft'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)] mt-1">
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
                            {session.hr_avg && <span>{session.hr_avg} bpm</span>}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
