import { Link } from 'react-router-dom';
import type { ParsedLap } from '@/api/training';
import { trainingTypeOptions, lapTypeOptions } from '@/constants/training';
import { ExerciseCard } from '@/features/strength/ExerciseCard';
import { useUploadForm } from '@/hooks/useUploadForm';
import { usePlannedSessionLinking } from '@/hooks/usePlannedSessionLinking';
import { useStrengthUpload } from '@/hooks/useStrengthUpload';
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
/*  Component                                                          */
/* ------------------------------------------------------------------ */

// eslint-disable-next-line max-lines-per-function, complexity -- JSX-heavy page component
export default function UploadPage() {
  const form = useUploadForm();
  const planned = usePlannedSessionLinking(form.trainingDate);
  const strength = useStrengthUpload({
    trainingType: form.trainingType,
    trainingDate: form.trainingDate,
    notes: form.notes,
    rpe: form.rpe,
    csvFile: form.csvFile,
    selectedPlannedId: planned.selectedPlannedId,
    navigate: form.navigate,
    setCreating: form.setCreating,
    setError: form.setError,
  });

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
          <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)]">
            Neues Training
          </h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Training erfassen und analysieren.
          </p>
        </header>
      </div>

      {/* Type Selector — visible in step 0 */}
      {form.step === 0 && (
        <Card elevation="raised">
          <CardBody>
            <div className="space-y-1.5">
              <Label>Trainingstyp</Label>
              <Select
                options={[
                  { value: 'running', label: 'Laufen' },
                  { value: 'strength', label: 'Kraft' },
                ]}
                value={form.trainingType}
                onChange={(val) => {
                  if (val) form.setTrainingType(val as 'running' | 'strength');
                }}
                placeholder="Typ wählen"
              />
            </div>
          </CardBody>
        </Card>
      )}

      {/* Error */}
      {form.error && (
        <Alert variant="error" closeable onClose={() => form.setError(null)}>
          <AlertDescription>{form.error}</AlertDescription>
        </Alert>
      )}

      {/* ============== Step 0: Import / Create ============== */}
      {form.step === 0 && (
        <>
          {/* Card 1: Training Meta */}
          <Card elevation="raised">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Training</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <FileUpload
                accept=".csv,.fit,application/octet-stream"
                onUpload={form.handleFileUpload}
                onRemove={form.handleFileRemove}
                instructionText={
                  form.csvFile
                    ? form.csvFile.name
                    : form.isStrength
                      ? 'Optional: Datei von Sportuhr hochladen'
                      : 'Datei hier ablegen oder klicken'
                }
                subText={
                  form.isStrength
                    ? 'CSV, FIT — Herzfrequenz wird automatisch übernommen'
                    : 'Unterstützt: CSV, Garmin/Wahoo FIT'
                }
              />

              <div className={`grid grid-cols-1 gap-4 ${form.isStrength ? 'sm:grid-cols-2' : ''}`}>
                <div className="space-y-1.5">
                  <Label>Datum</Label>
                  <DatePicker
                    value={form.trainingDate}
                    onChange={(date) => {
                      if (date) form.setTrainingDate(date);
                    }}
                    maxDate={new Date()}
                    placeholder="Datum wählen"
                  />
                </div>
                {form.isStrength && (
                  <div className="space-y-1.5">
                    <Label>Dauer (min)</Label>
                    <NumberInput
                      value={strength.duration}
                      onChange={strength.setDuration}
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
                    ...planned.plannedSessions.map((ps) => {
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
                  value={planned.selectedPlannedId != null ? String(planned.selectedPlannedId) : ''}
                  onChange={(val) => planned.setSelectedPlannedId(val ? Number(val) : null)}
                  placeholder="Keine Zuordnung"
                />
                {planned.plannedSessions.length === 0 && (
                  <p className="text-[10px] text-[var(--color-text-disabled)]">
                    Keine geplanten Sessions für diesen Tag
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>RPE (Anstrengung): {form.rpe}</Label>
                <Slider
                  value={[form.rpe]}
                  onValueChange={([val]) => form.setRpe(val)}
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
          {form.isStrength && (strength.availableTemplates.length > 0 || strength.lastSession) && (
            <Card elevation="raised">
              <CardBody className="space-y-3">
                {strength.availableTemplates.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <ClipboardList className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                    <span className="text-sm text-[var(--color-text-muted)]">Aus Plan laden:</span>
                    {strength.loadingPlan && <Spinner size="sm" />}
                    {strength.availableTemplates.map((tpl) => (
                      <Button
                        key={tpl.id}
                        variant="secondary"
                        size="sm"
                        onClick={() => strength.handleLoadFromPlan(tpl.id)}
                        disabled={strength.loadingPlan}
                      >
                        {tpl.name}
                      </Button>
                    ))}
                  </div>
                )}
                {strength.lastSession && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={strength.handleCloneLastSession}
                    className="w-full"
                  >
                    <RotateCcw className="w-4 h-4 mr-1.5" />
                    Letztes Training übernehmen ({strength.lastSession.date})
                  </Button>
                )}
              </CardBody>
            </Card>
          )}

          {/* Card 3: Exercises (Strength only) */}
          {form.isStrength && (
            <Card elevation="raised">
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
                    Übungen ({strength.exercises.length})
                  </h2>
                  {strength.tonnage.total > 0 && (
                    <div className="flex items-center gap-1.5" aria-live="polite">
                      <span className="text-xs text-[var(--color-text-muted)]">Tonnage</span>
                      <span className="text-sm font-semibold tabular-nums text-[var(--color-text-base)]">
                        {strength.formatted.value}
                        <span className="text-xs font-normal text-[var(--color-text-muted)] ml-0.5">
                          {strength.formatted.unit}
                        </span>
                      </span>
                      {strength.tonnageDelta !== null && strength.tonnageDelta !== 0 && (
                        <span
                          className={`text-xs flex items-center gap-0.5 ${
                            strength.tonnageDelta > 0
                              ? 'text-[var(--color-text-success)]'
                              : 'text-[var(--color-text-error)]'
                          }`}
                        >
                          {strength.tonnageDelta > 0 ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {strength.tonnageDelta > 0 ? '+' : ''}
                          {Math.round(strength.tonnageDelta)} kg
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardBody className="space-y-4">
                {strength.exercises.map((ex, idx) => (
                  <ExerciseCard
                    key={idx}
                    index={idx}
                    exercise={ex}
                    onChange={strength.handleExerciseChange}
                    onRemove={strength.handleExerciseRemove}
                    canRemove={strength.exercises.length > 1}
                    exerciseLibrary={strength.exerciseLibrary}
                  />
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={strength.handleAddExercise}
                  className="w-full"
                >
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
                value={form.notes}
                onChange={(e) => form.setNotes(e.target.value)}
                rows={2}
                placeholder="Wie war das Training? (optional)"
              />
            </CardBody>
          </Card>

          {/* Submit (Running) */}
          {form.isRunning && (
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={form.handleNext}
                disabled={!form.csvFile || form.loading}
              >
                {form.loading ? (
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
          {form.isStrength && (
            <div className="flex justify-end">
              <Button
                variant="primary"
                onClick={strength.handleCreateStrength}
                disabled={!strength.canSubmitStrength || form.creating}
              >
                {form.creating ? (
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
      {form.isRunning && form.step === 1 && form.parseResult && (
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
                  value={form.effectiveType ?? undefined}
                  onChange={(val) => form.setTrainingTypeOverride(val ?? null)}
                  placeholder="Typ wählen"
                />
              </div>

              {form.laps && form.laps.length > 0 && (
                <div className="space-y-1.5">
                  <Label>Laps ({form.laps.length})</Label>
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
                        {form.laps.map((lap: ParsedLap) => {
                          const effectiveLapType =
                            form.lapOverrides[lap.lap_number] ||
                            lap.suggested_type ||
                            'unclassified';
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
                                      form.setLapOverrides((prev) => ({
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
            <Button variant="secondary" onClick={form.handleBack} disabled={form.creating}>
              Zurück
            </Button>
            <Button
              variant="primary"
              onClick={() => form.handleCreateRunning(planned.selectedPlannedId)}
              disabled={form.creating}
            >
              {form.creating ? (
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
