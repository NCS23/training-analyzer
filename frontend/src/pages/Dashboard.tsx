import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, CardBody, Spinner, Toolbar, ToolbarButton } from '@nordlig/components';
import { Upload, LayoutDashboard, Activity, Clock, MapPin, Heart, TrendingUp } from 'lucide-react';
import { listSessions } from '@/api/training';
import type { SessionSummary } from '@/api/training';
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
      <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
        <header className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-primary-1-100)]">
            <LayoutDashboard className="w-5 h-5 text-[var(--color-primary-1-600)]" />
          </div>
          <h1 className="text-3xl font-semibold text-[var(--color-text-base)]">Dashboard</h1>
        </header>

        <Card elevation="raised">
          <CardBody className="flex flex-col items-center py-16 text-center">
            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--color-primary-1-50)] mb-4">
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
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-primary-1-100)]">
            <LayoutDashboard className="w-5 h-5 text-[var(--color-primary-1-600)]" />
          </div>
          <h1 className="text-3xl font-semibold text-[var(--color-text-base)]">Dashboard</h1>
        </div>
        <Toolbar aria-label="Dashboard-Aktionen">
          <ToolbarButton
            onClick={() => navigate('/sessions/new')}
            icon={<Upload />}
          >
            Hochladen
          </ToolbarButton>
        </Toolbar>
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
              className="cursor-pointer hover:shadow-md transition-shadow rounded-[var(--radius-component-md)]"
              onClick={() => navigate(`/sessions/${session.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && navigate(`/sessions/${session.id}`)}
            >
              <Card elevation="raised" padding="compact">
                <CardBody>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--color-primary-1-50)]">
                        <Activity className="w-4 h-4 text-[var(--color-primary-1-500)]" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[var(--color-text-base)]">
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
                        <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                          {session.distance_km && <span>{session.distance_km} km</span>}
                          {session.duration_sec && (
                            <span>{formatDuration(session.duration_sec)}</span>
                          )}
                          {session.hr_avg && <span>{session.hr_avg} bpm</span>}
                        </div>
                      </div>
                    </div>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {session.workout_type === 'running' ? 'Laufen' : 'Kraft'}
                    </span>
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
