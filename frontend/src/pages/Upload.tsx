import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { parseTraining, uploadTraining } from '@/api/training';
import type { ParsedLap, TrainingParseResponse } from '@/api/training';
import { getPlannedSessionsForDate } from '@/api/weekly-plan';
import type { PlannedSessionOption } from '@/api/weekly-plan';
import { trainingTypeOptions, lapTypeOptions } from '@/constants/training';
import type { ExerciseInput } from '@/api/strength';
import { createStrengthSession, getLastCompleteStrengthSession } from '@/api/strength';
import type { LastCompleteSession } from '@/api/strength';
import type { Exercise } from '@/api/exercises';
import { listExercises } from '@/api/exercises';
import { listSessionTemplates, getSessionTemplate } from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';
import { ExerciseCard } from '@/features/strength/ExerciseCard';
import { useTonnageCalc, formatTonnage } from '@/hooks/useTonnageCalc';
import {
  Plus,
  ChevronRight,
  ClipboardList,
  RotateCcw,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  DatePicker,
  Label,
  Select,
  Textarea,
  FileUpload,
  Alert,
  AlertDescription,
  Spinner,
  Breadcrumbs,
  BreadcrumbItem,
  NumberInput,
  Slider,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@nordlig/components';

/* ------------------------------------------------------------------ */
/*  Types & Defaults                                                   */
/* ------------------------------------------------------------------ */

type TrainingType = 'running' | 'strength';

const defaultExercise: ExerciseInput = {
  name: '',
  category: 'push',
  sets: [{ reps: 8, weight_kg: 0, status: 'completed' }],
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function UploadPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Pre-select strength if navigated with state
  const preselect = (location.state as { preselect?: string } | null)?.preselect;

  // Wizard step: 0 = Upload, 1 = Prüfen (only for running)
  const [step, setStep] = useState(0);

  // Shared state
  const [trainingType, setTrainingType] = useState<TrainingType>(
    preselect === 'strength' ? 'strength' : 'running',
  );
  const [trainingDate, setTrainingDate] = useState<Date>(new Date());
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rpe, setRpe] = useState(5);

  // Running: review step
  const [parseResult, setParseResult] = useState<TrainingParseResponse | null>(null);
  const [lapOverrides, setLapOverrides] = useState<Record<number, string>>({});
  const [trainingTypeOverride, setTrainingTypeOverride] = useState<string | null>(null);

  // Planned session linking
  const [plannedSessions, setPlannedSessions] = useState<PlannedSessionOption[]>([]);
  const [selectedPlannedId, setSelectedPlannedId] = useState<number | null>(null);

  // Strength state
  const [duration, setDuration] = useState(60);
  const [exercises, setExercises] = useState<ExerciseInput[]>([{ ...defaultExercise }]);
  const [exerciseLibrary, setExerciseLibrary] = useState<Exercise[]>([]);
  const [availableTemplates, setAvailableTemplates] = useState<SessionTemplateSummary[]>([]);
  const [lastSession, setLastSession] = useState<LastCompleteSession | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);

  const isRunning = trainingType === 'running';
  const isStrength = trainingType === 'strength';

  // Tonnage calculation (strength only)
  const namedExercises = exercises.filter((ex) => ex.name.trim());
  const tonnage = useTonnageCalc(namedExercises);
  const tonnageDelta =
    lastSession && tonnage.total > 0 ? tonnage.total - lastSession.total_tonnage_kg : null;

  /* ---- Data loading ---- */

  // Load planned sessions for selected date
  useEffect(() => {
    const dateStr = trainingDate.toISOString().split('T')[0];
    getPlannedSessionsForDate(dateStr)
      .then(setPlannedSessions)
      .catch(() => setPlannedSessions([]));
    setSelectedPlannedId(null);
  }, [trainingDate]);

  // Load strength data when switching to strength mode
  useEffect(() => {
    if (trainingType === 'strength') {
      listExercises()
        .then((res) => setExerciseLibrary(res.exercises))
        .catch(() => {});
      listSessionTemplates('strength')
        .then((res) => setAvailableTemplates(res.templates))
        .catch(() => {});
      getLastCompleteStrengthSession()
        .then((res) => {
          if (res.found && res.session) setLastSession(res.session);
        })
        .catch(() => {});
    }
  }, [trainingType]);

  /* ---- Running handlers ---- */

  const handleFileUpload = (files: File[]) => {
    if (files[0]) setCsvFile(files[0]);
  };

  const handleFileRemove = () => setCsvFile(null);

  const handleNext = async () => {
    if (!csvFile) {
      setError('Bitte Datei auswählen');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await parseTraining({
        csvFile,
        trainingDate: trainingDate.toISOString().split('T')[0],
        trainingType,
        notes: notes || undefined,
      });

      if (result.success && result.data) {
        setParseResult(result);
        const initialOverrides: Record<number, string> = {};
        if (result.data.laps) {
          for (const lap of result.data.laps) {
            initialOverrides[lap.lap_number] = lap.suggested_type || 'unclassified';
          }
        }
        setLapOverrides(initialOverrides);
        setTrainingTypeOverride(result.metadata?.training_type_auto || null);
        setStep(1);
      } else {
        setError(result.errors?.join(', ') || 'Analyse fehlgeschlagen');
      }
    } catch (err) {
      setError('Netzwerkfehler: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRunning = async () => {
    if (!csvFile) return;

    setCreating(true);
    setError(null);

    try {
      const result = await uploadTraining({
        csvFile,
        trainingDate: trainingDate.toISOString().split('T')[0],
        trainingType,
        notes: notes || undefined,
        rpe,
        lapOverrides: Object.keys(lapOverrides).length > 0 ? lapOverrides : undefined,
        trainingTypeOverride: trainingTypeOverride || undefined,
        plannedEntryId: selectedPlannedId ?? undefined,
      });

      if (result.success && result.session_id) {
        navigate(`/sessions/${result.session_id}`, { state: { uploaded: true } });
      } else {
        setError(result.errors?.join(', ') || 'Upload fehlgeschlagen');
      }
    } catch (err) {
      setError('Netzwerkfehler: ' + (err as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleBack = () => {
    setStep(0);
    setParseResult(null);
    setLapOverrides({});
    setTrainingTypeOverride(null);
    setError(null);
  };

  /* ---- Strength handlers ---- */

  const handleExerciseChange = useCallback((idx: number, updated: ExerciseInput) => {
    setExercises((prev) => {
      const next = [...prev];
      next[idx] = updated;
      return next;
    });
  }, []);

  const handleExerciseRemove = useCallback((idx: number) => {
    setExercises((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const handleAddExercise = useCallback(() => {
    setExercises((prev) => [
      ...prev,
      { ...defaultExercise, sets: [{ reps: 8, weight_kg: 0, status: 'completed' }] },
    ]);
  }, []);

  const handleCloneLastSession = useCallback(() => {
    if (!lastSession) return;
    const hasContent = exercises.some((ex) => ex.name.trim());
    if (hasContent && !window.confirm('Aktuelle Eingabe überschreiben?')) return;

    setExercises(
      lastSession.exercises.map((ex) => ({
        name: ex.name,
        category: ex.category,
        sets: ex.sets.map((s) => ({ ...s, status: 'completed' as const })),
      })),
    );
    if (lastSession.duration_minutes) {
      setDuration(lastSession.duration_minutes);
    }
  }, [lastSession, exercises]);

  const handleLoadFromPlan = useCallback(async (planId: number) => {
    setLoadingPlan(true);
    try {
      const plan = await getSessionTemplate(planId);
      const loaded: ExerciseInput[] = plan.exercises.map((ex) => ({
        name: ex.name,
        category: ex.category,
        sets: Array.from({ length: ex.sets }, () => ({
          reps: ex.reps,
          weight_kg: ex.weight_kg ?? 0,
          status: 'completed' as const,
        })),
      }));
      if (loaded.length > 0) setExercises(loaded);
    } catch {
      setError('Plan konnte nicht geladen werden.');
    } finally {
      setLoadingPlan(false);
    }
  }, []);

  const canSubmitStrength =
    exercises.length > 0 && exercises.every((ex) => ex.name.trim().length > 0);

  const handleCreateStrength = useCallback(async () => {
    if (!canSubmitStrength) return;

    setCreating(true);
    setError(null);

    try {
      const result = await createStrengthSession({
        date: trainingDate.toISOString().split('T')[0],
        duration_minutes: duration,
        exercises,
        notes: notes.trim() || undefined,
        rpe,
        trainingFile: csvFile || undefined,
        plannedEntryId: selectedPlannedId ?? undefined,
      });

      if (result.success) {
        navigate(`/sessions/${result.session_id}`, { state: { uploaded: true } });
      }
    } catch (err) {
      setError('Fehler beim Speichern: ' + (err as Error).message);
    } finally {
      setCreating(false);
    }
  }, [
    canSubmitStrength,
    trainingDate,
    duration,
    exercises,
    notes,
    rpe,
    csvFile,
    selectedPlannedId,
    navigate,
  ]);

  /* ---- Derived data for review step ---- */
  const laps = parseResult?.data?.laps;
  const autoType = parseResult?.metadata?.training_type_auto;
  const effectiveType = trainingTypeOverride || autoType;

  const formatted = formatTonnage(tonnage.total);

  /* ---- Render ---- */

  return (
    <div className="px-4 pb-4 pt-4 md:px-6 md:pb-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumbs + Header */}
      <div className="space-y-1 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/sessions" className="hover:underline underline-offset-2">
              Sessions
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Neues Training</BreadcrumbItem>
        </Breadcrumbs>
        <header>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Neues Training
          </h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Training erfassen und analysieren.
          </p>
        </header>
      </div>

      {/* Type Selector — visible in step 0 */}
      {step === 0 && (
        <Card elevation="raised">
          <CardBody>
            <div className="space-y-1.5">
              <Label>Trainingstyp</Label>
              <Select
                options={[
                  { value: 'running', label: 'Laufen' },
                  { value: 'strength', label: 'Kraft' },
                ]}
                value={trainingType}
                onChange={(val) => {
                  if (val) setTrainingType(val as TrainingType);
                }}
                placeholder="Typ wählen"
              />
            </div>
          </CardBody>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* ============== Step 0: Import / Create ============== */}
      {step === 0 && (
        <>
          {/* Card 1: Training Meta */}
          <Card elevation="raised">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Training</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <FileUpload
                accept=".csv,.fit"
                onUpload={handleFileUpload}
                onRemove={handleFileRemove}
                instructionText={
                  csvFile
                    ? csvFile.name
                    : isStrength
                      ? 'Optional: Datei von Sportuhr hochladen'
                      : 'Datei hier ablegen oder klicken'
                }
                subText={
                  isStrength
                    ? 'CSV, FIT — Herzfrequenz wird automatisch übernommen'
                    : 'Unterstützt: CSV, Garmin/Wahoo FIT'
                }
              />

              <div className={`grid grid-cols-1 gap-4 ${isStrength ? 'sm:grid-cols-2' : ''}`}>
                <div className="space-y-1.5">
                  <Label>Datum</Label>
                  <DatePicker
                    value={trainingDate}
                    onChange={(date) => {
                      if (date) setTrainingDate(date);
                    }}
                    maxDate={new Date()}
                    placeholder="Datum wählen"
                  />
                </div>
                {isStrength && (
                  <div className="space-y-1.5">
                    <Label>Dauer (min)</Label>
                    <NumberInput
                      value={duration}
                      onChange={setDuration}
                      min={1}
                      max={300}
                      step={5}
                      aria-label="Trainingsdauer in Minuten"
                      incrementLabel="5 Minuten mehr"
                      decrementLabel="5 Minuten weniger"
                    />
                  </div>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>Geplante Session zuordnen</Label>
                <Select
                  options={[
                    { value: '', label: 'Keine Zuordnung' },
                    ...plannedSessions.map((ps) => {
                      const typeLabel = ps.training_type === 'running' ? 'Laufen' : 'Kraft';
                      const detail = ps.run_type
                        ? ` — ${ps.run_type}`
                        : ps.template_name
                          ? ` — ${ps.template_name}`
                          : '';
                      return {
                        value: String(ps.id),
                        label: `${typeLabel}${detail}`,
                      };
                    }),
                  ]}
                  value={selectedPlannedId != null ? String(selectedPlannedId) : ''}
                  onChange={(val) => setSelectedPlannedId(val ? Number(val) : null)}
                  placeholder="Keine Zuordnung"
                />
                {plannedSessions.length === 0 && (
                  <p className="text-[10px] text-[var(--color-text-disabled)]">
                    Keine geplanten Sessions für diesen Tag
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>RPE (Anstrengung): {rpe}</Label>
                <Slider
                  value={[rpe]}
                  onValueChange={([val]) => setRpe(val)}
                  min={1}
                  max={10}
                  step={1}
                  showValue
                  aria-label="Rate of Perceived Exertion"
                />
              </div>
            </CardBody>
          </Card>

          {/* Card 2: Templates + Clone (Strength only) */}
          {isStrength && (availableTemplates.length > 0 || lastSession) && (
            <Card elevation="raised">
              <CardBody className="space-y-3">
                {availableTemplates.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <ClipboardList className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                    <span className="text-sm text-[var(--color-text-muted)]">Aus Plan laden:</span>
                    {loadingPlan && <Spinner size="sm" />}
                    {availableTemplates.map((tpl) => (
                      <Button
                        key={tpl.id}
                        variant="secondary"
                        size="sm"
                        onClick={() => handleLoadFromPlan(tpl.id)}
                        disabled={loadingPlan}
                      >
                        {tpl.name}
                      </Button>
                    ))}
                  </div>
                )}
                {lastSession && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleCloneLastSession}
                    className="w-full"
                  >
                    <RotateCcw className="w-4 h-4 mr-1.5" />
                    Letztes Training übernehmen ({lastSession.date})
                  </Button>
                )}
              </CardBody>
            </Card>
          )}

          {/* Card 3: Exercises (Strength only) */}
          {isStrength && (
            <Card elevation="raised">
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                    Übungen ({exercises.length})
                  </h2>
                  {tonnage.total > 0 && (
                    <div className="flex items-center gap-1.5" aria-live="polite">
                      <span className="text-xs text-[var(--color-text-muted)]">Tonnage</span>
                      <span className="text-sm font-semibold tabular-nums text-[var(--color-text-base)]">
                        {formatted.value}
                        <span className="text-xs font-normal text-[var(--color-text-muted)] ml-0.5">
                          {formatted.unit}
                        </span>
                      </span>
                      {tonnageDelta !== null && tonnageDelta !== 0 && (
                        <span
                          className={`text-xs flex items-center gap-0.5 ${
                            tonnageDelta > 0
                              ? 'text-[var(--color-text-success)]'
                              : 'text-[var(--color-text-error)]'
                          }`}
                        >
                          {tonnageDelta > 0 ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {tonnageDelta > 0 ? '+' : ''}
                          {Math.round(tonnageDelta)} kg
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardBody className="space-y-4">
                {exercises.map((ex, idx) => (
                  <ExerciseCard
                    key={idx}
                    index={idx}
                    exercise={ex}
                    onChange={handleExerciseChange}
                    onRemove={handleExerciseRemove}
                    canRemove={exercises.length > 1}
                    exerciseLibrary={exerciseLibrary}
                  />
                ))}
                <Button variant="ghost" size="sm" onClick={handleAddExercise} className="w-full">
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  Übung hinzufügen
                </Button>
              </CardBody>
            </Card>
          )}

          {/* Card 4: Notizen */}
          <Card elevation="raised">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Notizen</h2>
            </CardHeader>
            <CardBody>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Wie war das Training? (optional)"
              />
            </CardBody>
          </Card>

          {/* Submit (Running) */}
          {isRunning && (
            <div className="flex justify-end">
              <Button variant="primary" onClick={handleNext} disabled={!csvFile || loading}>
                {loading ? (
                  <span className="flex items-center gap-2">
                    <Spinner size="sm" aria-hidden="true" />
                    Analysiere...
                  </span>
                ) : (
                  'Weiter'
                )}
              </Button>
            </div>
          )}

          {/* Submit (Strength) */}
          {isStrength && (
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={handleCreateStrength}
                disabled={!canSubmitStrength || creating}
              >
                {creating ? (
                  <span className="flex items-center gap-2">
                    <Spinner size="sm" aria-hidden="true" />
                    Speichere...
                  </span>
                ) : (
                  'Session anlegen'
                )}
              </Button>
            </div>
          )}
        </>
      )}

      {/* ============== Running: Step 1 — Review ============== */}
      {isRunning && step === 1 && parseResult && (
        <>
          <Card elevation="raised">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                Klassifikation prüfen
              </h2>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">
                Automatisch erkannte Zuordnungen. Bei Bedarf anpassen.
              </p>
            </CardHeader>
            <CardBody className="space-y-6">
              <div className="space-y-1.5">
                <Label>Trainingstyp</Label>
                <Select
                  options={trainingTypeOptions}
                  value={effectiveType ?? undefined}
                  onChange={(val) => setTrainingTypeOverride(val ?? null)}
                  placeholder="Typ wählen"
                />
              </div>

              {laps && laps.length > 0 && (
                <div className="space-y-1.5">
                  <Label>Laps ({laps.length})</Label>
                  <div className="overflow-x-auto rounded-[var(--radius-component-md)] border border-[var(--color-border-default)]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-8">#</TableHead>
                          <TableHead>Typ</TableHead>
                          <TableHead>Dauer</TableHead>
                          <TableHead>Pace</TableHead>
                          <TableHead>Ø HF</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {laps.map((lap: ParsedLap) => {
                          const effectiveLapType =
                            lapOverrides[lap.lap_number] || lap.suggested_type || 'unclassified';
                          return (
                            <TableRow key={lap.lap_number}>
                              <TableCell className="font-medium text-[var(--color-text-muted)]">
                                {lap.lap_number}
                              </TableCell>
                              <TableCell>
                                <Select
                                  options={lapTypeOptions}
                                  value={effectiveLapType}
                                  onChange={(val) => {
                                    if (val) {
                                      setLapOverrides((prev) => ({
                                        ...prev,
                                        [lap.lap_number]: val,
                                      }));
                                    }
                                  }}
                                  inputSize="sm"
                                  className="w-32 min-w-0"
                                />
                              </TableCell>
                              <TableCell>{lap.duration_formatted}</TableCell>
                              <TableCell>
                                {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                              </TableCell>
                              <TableCell>
                                {lap.avg_hr_bpm != null ? `${lap.avg_hr_bpm}` : '-'}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Submit */}
          <div className="flex justify-between">
            <Button variant="secondary" onClick={handleBack} disabled={creating}>
              Zurück
            </Button>
            <Button variant="primary" onClick={handleCreateRunning} disabled={creating}>
              {creating ? (
                <span className="flex items-center gap-2">
                  <Spinner size="sm" aria-hidden="true" />
                  Erstelle Session...
                </span>
              ) : (
                'Session anlegen'
              )}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
