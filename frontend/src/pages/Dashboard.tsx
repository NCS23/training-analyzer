import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  Badge,
  Spinner,
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
        <header>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Dashboard
          </h1>
        </header>

        <Card elevation="raised">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-[var(--radius-2xl)] bg-[var(--color-primary-1-50)] mb-4">
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
              Training hochladen
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card
          elevation="raised"
          padding="compact"
          className="border-l-4 border-l-[var(--color-primary-1-500)]"
        >
          <CardBody>
            <div className="flex items-center gap-1.5 mb-1">
              <TrendingUp className="w-3.5 h-3.5 text-[var(--color-primary-1-500)]" />
              <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                Sessions
              </p>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-base)]">{totalSessions}</p>
          </CardBody>
        </Card>
        <Card
          elevation="raised"
          padding="compact"
          className="border-l-4 border-l-[var(--color-accent-1-500)]"
        >
          <CardBody>
            <div className="flex items-center gap-1.5 mb-1">
              <MapPin className="w-3.5 h-3.5 text-[var(--color-accent-1-500)]" />
              <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                Distanz
              </p>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-base)]">
              {totalDistance.toFixed(1)}{' '}
              <span className="text-sm font-normal text-[var(--color-text-muted)]">km</span>
            </p>
          </CardBody>
        </Card>
        <Card
          elevation="raised"
          padding="compact"
          className="border-l-4 border-l-[var(--color-accent-2-500)]"
        >
          <CardBody>
            <div className="flex items-center gap-1.5 mb-1">
              <Clock className="w-3.5 h-3.5 text-[var(--color-accent-2-500)]" />
              <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                Trainingszeit
              </p>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-base)]">
              {formatDuration(totalDuration)}
            </p>
          </CardBody>
        </Card>
        {avgHr > 0 && (
          <Card
            elevation="raised"
            padding="compact"
            className="border-l-4 border-l-[var(--color-accent-3-500)]"
          >
            <CardBody>
              <div className="flex items-center gap-1.5 mb-1">
                <Heart className="w-3.5 h-3.5 text-[var(--color-accent-3-500)]" />
                <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
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
      {goalProgress && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-[var(--color-primary-1-500)]" />
                <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                  {goalProgress.goal.title}
                </h2>
              </div>
              <div className="flex items-center gap-2">
                {goalProgress.goal.days_until > 0 ? (
                  <Badge variant="info" size="sm">
                    <Calendar className="w-3 h-3 mr-1" />
                    {goalProgress.goal.days_until} Tage
                  </Badge>
                ) : goalProgress.goal.days_until === 0 ? (
                  <Badge variant="warning" size="sm">Heute</Badge>
                ) : (
                  <Badge variant="neutral" size="sm">Vergangen</Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              {/* Pace Comparison */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-[var(--color-text-muted)] mb-1">Ziel-Pace</p>
                  <p className="text-lg font-bold text-[var(--color-text-base)]">
                    {goalProgress.target_pace_formatted}{' '}
                    <span className="text-xs font-normal text-[var(--color-text-muted)]">
                      min/km
                    </span>
                  </p>
                </div>
                {goalProgress.current_pace_formatted ? (
                  <div>
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Aktueller Pace</p>
                    <p className="text-lg font-bold text-[var(--color-text-base)]">
                      {goalProgress.current_pace_formatted}{' '}
                      <span className="text-xs font-normal text-[var(--color-text-muted)]">
                        min/km
                      </span>
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Aktueller Pace</p>
                    <p className="text-sm text-[var(--color-text-muted)] italic">
                      Keine Daten
                    </p>
                  </div>
                )}
                {goalProgress.pace_gap_label && (
                  <div>
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Differenz</p>
                    <p
                      className={`text-lg font-bold ${
                        goalProgress.pace_gap_sec !== null && goalProgress.pace_gap_sec <= 0
                          ? 'text-[var(--color-text-success)]'
                          : 'text-[var(--color-text-warning)]'
                      }`}
                    >
                      {goalProgress.pace_gap_label}
                    </p>
                  </div>
                )}
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
                  <div className="h-2 rounded-full bg-[var(--color-bg-subtle)] overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500 motion-reduce:transition-none"
                      style={{
                        width: `${Math.min(100, goalProgress.progress_percent)}%`,
                        backgroundColor:
                          goalProgress.progress_percent >= 100
                            ? 'var(--color-status-success)'
                            : goalProgress.progress_percent >= 70
                              ? 'var(--color-primary-1-500)'
                              : 'var(--color-status-warning)',
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Estimated Finish & Prognosis */}
              {goalProgress.estimated_finish_formatted && (
                <div className="pt-2 border-t border-[var(--color-border-subtle)] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[var(--color-text-muted)]">
                        Geschaetzte Finish-Zeit
                      </p>
                      <p className="text-sm font-medium text-[var(--color-text-base)]">
                        {goalProgress.estimated_finish_formatted}
                      </p>
                    </div>
                    {goalProgress.finish_delta_label && (
                      <div className="text-center">
                        <p className="text-xs text-[var(--color-text-muted)]">Differenz</p>
                        <p
                          className={`text-sm font-medium ${
                            goalProgress.finish_delta_seconds !== null &&
                            goalProgress.finish_delta_seconds <= 0
                              ? 'text-[var(--color-text-success)]'
                              : 'text-[var(--color-text-warning)]'
                          }`}
                        >
                          {goalProgress.finish_delta_label}
                        </p>
                      </div>
                    )}
                    <div className="text-right">
                      <p className="text-xs text-[var(--color-text-muted)]">Zielzeit</p>
                      <p className="text-sm font-medium text-[var(--color-text-base)]">
                        {goalProgress.goal.target_time_formatted}
                      </p>
                    </div>
                  </div>

                  {/* Trend & Weeks to Goal */}
                  {goalProgress.weekly_pace_trend_label && (
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-[var(--color-text-muted)]">
                          Trend (8 Wochen)
                        </p>
                        <p
                          className={`text-sm font-medium ${
                            goalProgress.weekly_pace_trend_sec !== null &&
                            goalProgress.weekly_pace_trend_sec > 0
                              ? 'text-[var(--color-text-success)]'
                              : goalProgress.weekly_pace_trend_sec !== null &&
                                  goalProgress.weekly_pace_trend_sec < 0
                                ? 'text-[var(--color-text-warning)]'
                                : 'text-[var(--color-text-base)]'
                          }`}
                        >
                          {goalProgress.weekly_pace_trend_label}
                        </p>
                      </div>
                      {goalProgress.weeks_to_goal !== null && goalProgress.weeks_to_goal > 0 && (
                        <div className="text-right">
                          <p className="text-xs text-[var(--color-text-muted)]">
                            Ziel erreichbar in
                          </p>
                          <p className="text-sm font-medium text-[var(--color-text-base)]">
                            ~{goalProgress.weeks_to_goal} Wochen
                          </p>
                          {goalProgress.goal_reachable !== null && (
                            <Badge
                              variant={goalProgress.goal_reachable ? 'success' : 'warning'}
                              size="sm"
                              className="mt-1"
                            >
                              {goalProgress.goal_reachable ? 'Machbar' : 'Knapp'}
                            </Badge>
                          )}
                        </div>
                      )}
                      {goalProgress.weeks_to_goal === 0 && (
                        <div className="text-right">
                          <Badge variant="success" size="sm">Ziel-Pace erreicht</Badge>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {goalProgress.sessions_used > 0 && (
                <p className="text-xs text-[var(--color-text-muted)]">
                  Basierend auf {goalProgress.sessions_used} Session
                  {goalProgress.sessions_used > 1 ? 's' : ''} der letzten 4 Wochen
                </p>
              )}

              {goalProgress.sessions_used === 0 && (
                <p className="text-xs text-[var(--color-text-muted)] italic">
                  Noch keine Tempo-/Intervall-Sessions in den letzten 4 Wochen.
                  Lade Trainings hoch, um deinen Fortschritt zu sehen.
                </p>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Recent Sessions */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-1 h-6 rounded-full bg-[var(--color-primary-1-500)]" />
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
              <Card elevation="raised" padding="compact">
                <CardBody>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 shrink-0 rounded-[var(--radius-lg)] bg-[var(--color-primary-1-50)]">
                      <Activity className="w-4 h-4 text-[var(--color-primary-1-500)]" />
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
                        <span className="text-xs text-[var(--color-text-muted)] shrink-0">
                          {session.workout_type === 'running' ? 'Laufen' : 'Kraft'}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                        {session.distance_km && <span>{session.distance_km} km</span>}
                        {session.duration_sec && (
                          <span>{formatDuration(session.duration_sec)}</span>
                        )}
                        {session.hr_avg && <span>{session.hr_avg} bpm</span>}
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
