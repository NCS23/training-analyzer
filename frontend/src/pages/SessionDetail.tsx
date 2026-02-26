import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSession, deleteSession, updateSessionNotes, updateTrainingType } from '@/api/training';
import type { SessionDetail, LapDetail, HRZone, TrainingTypeInfo } from '@/api/training';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Progress,
  Select,
  Textarea,
  Spinner,
  Alert,
  AlertDescription,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@nordlig/components';
import {
  ArrowLeft,
  Calendar,
  Clock,
  MapPin,
  Heart,
  Footprints,
  Timer,
  Trash2,
  Check,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { de } from 'date-fns/locale';

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

const trainingTypeOptions = Object.entries(trainingTypeLabels).map(([value, label]) => ({
  value,
  label,
}));

const workoutTypeLabels: Record<string, string> = {
  running: 'Laufen',
  strength: 'Kraft',
};

const lapTypeLabels: Record<string, string> = {
  warmup: 'Warm-up',
  interval: 'Intervall',
  pause: 'Pause',
  tempo: 'Tempo',
  longrun: 'Long Run',
  cooldown: 'Cool-down',
  recovery: 'Recovery',
  unclassified: 'Unklassifiziert',
};

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'EEEE, d. MMMM yyyy', { locale: de });
  } catch {
    return dateStr;
  }
}

export function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const sessionId = Number(id);

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Notes state
  const [notes, setNotes] = useState('');
  const [notesSaved, setNotesSaved] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const notesTimer = useRef<ReturnType<typeof setTimeout>>();

  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Training type state
  const [trainingTypeInfo, setTrainingTypeInfo] = useState<TrainingTypeInfo | null>(null);
  const [savingTrainingType, setSavingTrainingType] = useState(false);

  const loadSession = useCallback(async () => {
    if (!sessionId || isNaN(sessionId)) {
      setError('Ungueltige Session-ID.');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await getSession(sessionId);
      setSession(data);
      setNotes(data.notes || '');
      setTrainingTypeInfo(data.training_type);
    } catch {
      setError('Session konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Auto-save notes with debounce
  const saveNotes = useCallback(
    async (value: string) => {
      if (!sessionId) return;
      setSavingNotes(true);
      try {
        await updateSessionNotes(sessionId, value || null);
        setNotesSaved(true);
        setTimeout(() => setNotesSaved(false), 2000);
      } catch {
        setError('Notizen konnten nicht gespeichert werden.');
      } finally {
        setSavingNotes(false);
      }
    },
    [sessionId],
  );

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setNotes(value);
    setNotesSaved(false);

    if (notesTimer.current) clearTimeout(notesTimer.current);
    notesTimer.current = setTimeout(() => saveNotes(value), 1000);
  };

  // Delete
  const handleDelete = async () => {
    if (!sessionId) return;
    setDeleting(true);
    try {
      await deleteSession(sessionId);
      navigate('/sessions', { replace: true });
    } catch {
      setError('Session konnte nicht geloescht werden.');
      setDeleting(false);
    }
  };

  // Training type override
  const handleTrainingTypeOverride = async (newType: string | undefined) => {
    if (!sessionId || !newType) return;
    setSavingTrainingType(true);
    try {
      const result = await updateTrainingType(sessionId, newType);
      if (result.training_type) {
        setTrainingTypeInfo(result.training_type);
      }
    } catch {
      setError('Training Type konnte nicht gespeichert werden.');
    } finally {
      setSavingTrainingType(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/sessions')}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="h-7 w-48 bg-[var(--color-bg-muted)] rounded animate-pulse" />
        </div>
        {/* Skeleton cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} elevation="raised" padding="compact" className="bg-white">
              <CardBody>
                <div className="h-4 w-16 bg-[var(--color-bg-muted)] rounded animate-pulse mb-2" />
                <div className="h-7 w-24 bg-[var(--color-bg-muted)] rounded animate-pulse" />
              </CardBody>
            </Card>
          ))}
        </div>
        <Card elevation="raised" className="bg-white">
          <CardBody className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </CardBody>
        </Card>
      </div>
    );
  }

  // Error state
  if (error && !session) {
    return (
      <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/sessions')}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <h1 className="text-xl font-semibold text-[var(--color-text-base)]">Session</h1>
        </div>
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!session) return null;

  const laps = session.laps || [];
  const hrZones = session.hr_zones;

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/sessions')}
            aria-label="Zurueck zur Liste"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="min-w-0">
            <h1 className="text-xl font-semibold text-[var(--color-text-base)] truncate">
              {formatDate(session.date)}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="info" size="sm">
                {workoutTypeLabels[session.workout_type] || session.workout_type}
              </Badge>
              {trainingTypeInfo?.effective && (
                <Badge
                  variant={trainingTypeBadgeVariant[trainingTypeInfo.effective] ?? 'info'}
                  size="sm"
                >
                  {trainingTypeLabels[trainingTypeInfo.effective] ?? trainingTypeInfo.effective}
                </Badge>
              )}
              {trainingTypeInfo?.override && (
                <Badge variant="info" size="sm">
                  Manuell
                </Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {!showDeleteConfirm ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDeleteConfirm(true)}
              aria-label="Session loeschen"
            >
              <Trash2 className="w-4 h-4 text-[var(--color-text-error)]" />
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-[var(--color-text-error)]">Wirklich loeschen?</span>
              <Button
                variant="primary"
                size="sm"
                onClick={handleDelete}
                disabled={deleting}
                className="bg-[var(--color-bg-error)] hover:bg-[var(--color-bg-error-hover)]"
              >
                {deleting ? <Spinner size="sm" /> : 'Ja, loeschen'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowDeleteConfirm(false)}>
                Abbrechen
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Key Metrics Grid */}
      <section aria-label="Kennzahlen">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {session.duration_sec != null && (
            <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-accent-1-500)]">
              <CardBody>
                <div className="flex items-center gap-1.5 mb-1">
                  <Clock className="w-3.5 h-3.5 text-[var(--color-accent-1-500)]" aria-hidden />
                  <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Dauer</p>
                </div>
                <p className="text-2xl font-bold text-[var(--color-text-base)]">
                  {formatDuration(session.duration_sec)}
                </p>
              </CardBody>
            </Card>
          )}
          {session.distance_km != null && (
            <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-primary-1-500)]">
              <CardBody>
                <div className="flex items-center gap-1.5 mb-1">
                  <MapPin className="w-3.5 h-3.5 text-[var(--color-primary-1-500)]" aria-hidden />
                  <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Distanz</p>
                </div>
                <p className="text-2xl font-bold text-[var(--color-text-base)]">
                  {session.distance_km} <span className="text-sm font-normal text-[var(--color-text-muted)]">km</span>
                </p>
              </CardBody>
            </Card>
          )}
          {session.pace && (
            <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-accent-2-500)]">
              <CardBody>
                <div className="flex items-center gap-1.5 mb-1">
                  <Timer className="w-3.5 h-3.5 text-[var(--color-accent-2-500)]" aria-hidden />
                  <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Pace</p>
                </div>
                <p className="text-2xl font-bold text-[var(--color-text-base)]">
                  {session.pace} <span className="text-sm font-normal text-[var(--color-text-muted)]">/km</span>
                </p>
              </CardBody>
            </Card>
          )}
          {session.hr_avg != null && (
            <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-accent-3-500)]">
              <CardBody>
                <div className="flex items-center gap-1.5 mb-1">
                  <Heart className="w-3.5 h-3.5 text-[var(--color-accent-3-500)]" aria-hidden />
                  <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Ø Herzfrequenz</p>
                </div>
                <p className="text-2xl font-bold text-[var(--color-text-base)]">
                  {session.hr_avg} <span className="text-sm font-normal text-[var(--color-text-muted)]">bpm</span>
                </p>
              </CardBody>
            </Card>
          )}
        </div>
        {/* Secondary metrics */}
        {(session.hr_max != null || session.hr_min != null || session.cadence_avg != null) && (
          <div className="grid grid-cols-3 gap-4 mt-4">
            {session.hr_max != null && (
              <Card elevation="raised" padding="compact" className="bg-white">
                <CardBody>
                  <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Max HF</p>
                  <p className="text-lg font-semibold text-[var(--color-text-base)]">
                    {session.hr_max} <span className="text-sm font-normal text-[var(--color-text-muted)]">bpm</span>
                  </p>
                </CardBody>
              </Card>
            )}
            {session.hr_min != null && (
              <Card elevation="raised" padding="compact" className="bg-white">
                <CardBody>
                  <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Min HF</p>
                  <p className="text-lg font-semibold text-[var(--color-text-base)]">
                    {session.hr_min} <span className="text-sm font-normal text-[var(--color-text-muted)]">bpm</span>
                  </p>
                </CardBody>
              </Card>
            )}
            {session.cadence_avg != null && (
              <Card elevation="raised" padding="compact" className="bg-white">
                <CardBody>
                  <div className="flex items-center gap-1.5 mb-1">
                    <Footprints
                      className="w-3.5 h-3.5 text-[var(--color-primary-1-500)]"
                      aria-hidden
                    />
                    <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Ø Kadenz</p>
                  </div>
                  <p className="text-lg font-semibold text-[var(--color-text-base)]">
                    {session.cadence_avg} <span className="text-sm font-normal text-[var(--color-text-muted)]">spm</span>
                  </p>
                </CardBody>
              </Card>
            )}
          </div>
        )}
      </section>

      {/* Training Type Override */}
      {session.workout_type === 'running' && (
        <Card elevation="raised" padding="spacious" className="bg-white">
          <CardBody>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="text-sm text-[var(--color-text-muted)]">Trainingstyp:</span>
                {trainingTypeInfo?.effective ? (
                  <>
                    <Badge
                      variant={trainingTypeBadgeVariant[trainingTypeInfo.effective] ?? 'info'}
                      size="md"
                    >
                      {trainingTypeLabels[trainingTypeInfo.effective] ?? trainingTypeInfo.effective}
                    </Badge>
                    {trainingTypeInfo.confidence != null && !trainingTypeInfo.override && (
                      <span className="text-xs text-[var(--color-text-muted)]">
                        ({trainingTypeInfo.confidence}% Konfidenz)
                      </span>
                    )}
                    {trainingTypeInfo.override && (
                      <Badge variant="info" size="sm">
                        Manuell
                      </Badge>
                    )}
                  </>
                ) : (
                  <span className="text-sm text-[var(--color-text-muted)]">Nicht erkannt</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {savingTrainingType ? (
                  <Spinner size="sm" />
                ) : (
                  <Select
                    options={trainingTypeOptions}
                    value={trainingTypeInfo?.effective ?? undefined}
                    onChange={handleTrainingTypeOverride}
                    inputSize="sm"
                    className="w-44"
                    placeholder="Typ aendern"
                  />
                )}
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* HR Zones */}
      {hrZones && Object.keys(hrZones).length > 0 && (
        <section aria-label="Herzfrequenz-Zonen">
          <Card elevation="raised" className="bg-white">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                HF-Zonen Verteilung
              </h2>
            </CardHeader>
            <CardBody>
              <div className="space-y-3">
                {Object.entries(hrZones).map(([key, zone]: [string, HRZone]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--color-text-muted)]">{zone.label}</span>
                      <span className="font-medium text-[var(--color-text-base)]">
                        {zone.percentage}%
                        {zone.seconds != null && (
                          <span className="text-[var(--color-text-muted)] ml-1">
                            ({formatDuration(zone.seconds)})
                          </span>
                        )}
                      </span>
                    </div>
                    <Progress
                      value={zone.percentage}
                      size="sm"
                      color={
                        key.includes('recovery') || key.includes('zone_1')
                          ? 'success'
                          : key.includes('base') || key.includes('zone_2')
                            ? 'warning'
                            : 'error'
                      }
                    />
                  </div>
                ))}
              </div>
              {/* Textual alternative for accessibility */}
              <div className="sr-only">
                {Object.entries(hrZones).map(([, zone]: [string, HRZone]) => (
                  <span key={zone.label}>
                    {zone.label}: {zone.percentage}%.{' '}
                  </span>
                ))}
              </div>
            </CardBody>
          </Card>
        </section>
      )}

      {/* Laps Table */}
      {laps.length > 0 && (
        <section aria-label="Laps">
          <Card elevation="raised" className="bg-white">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Laps ({laps.length})
              </h2>
            </CardHeader>
            <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Typ</TableHead>
                    <TableHead>Dauer</TableHead>
                    <TableHead>Distanz</TableHead>
                    <TableHead>Pace</TableHead>
                    <TableHead>Ø HF</TableHead>
                    <TableHead>Kadenz</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {laps.map((lap: LapDetail) => {
                    const effectiveType = lap.user_override || lap.suggested_type || 'unclassified';
                    return (
                      <TableRow key={lap.lap_number}>
                        <TableCell className="font-medium text-[var(--color-text-muted)]">
                          {lap.lap_number}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              effectiveType === 'warmup' || effectiveType === 'cooldown'
                                ? 'info'
                                : effectiveType === 'pause'
                                  ? 'warning'
                                  : effectiveType === 'interval'
                                    ? 'error'
                                    : 'success'
                            }
                            size="sm"
                          >
                            {lapTypeLabels[effectiveType] || effectiveType}
                          </Badge>
                        </TableCell>
                        <TableCell>{lap.duration_formatted}</TableCell>
                        <TableCell>
                          {lap.distance_km != null ? `${lap.distance_km} km` : '-'}
                        </TableCell>
                        <TableCell>
                          {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                        </TableCell>
                        <TableCell>{lap.avg_hr_bpm != null ? `${lap.avg_hr_bpm}` : '-'}</TableCell>
                        <TableCell>
                          {lap.avg_cadence_spm != null ? `${lap.avg_cadence_spm}` : '-'}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </Card>
        </section>
      )}

      {/* Notes */}
      <section aria-label="Notizen">
        <Card elevation="raised" className="bg-white">
          <CardHeader className="flex flex-row items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Notizen</h2>
            <div className="flex items-center gap-2">
              {savingNotes && <Spinner size="sm" />}
              {notesSaved && (
                <span className="flex items-center gap-1 text-xs text-[var(--color-text-success)]">
                  <Check className="w-3 h-3" aria-hidden />
                  Gespeichert
                </span>
              )}
            </div>
          </CardHeader>
          <CardBody>
            <Textarea
              value={notes}
              onChange={handleNotesChange}
              rows={3}
              placeholder="Wie hast du dich gefuehlt? Notizen zum Training..."
            />
          </CardBody>
        </Card>
      </section>

      {/* Session metadata */}
      <footer className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" aria-hidden />
          <span>
            Erstellt:{' '}
            {session.created_at
              ? format(parseISO(session.created_at), 'dd.MM.yyyy HH:mm', { locale: de })
              : '-'}
          </span>
        </div>
        <span>Session #{session.id}</span>
      </footer>
    </div>
  );
}
