import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { parseTraining, uploadTraining } from '@/api/training';
import type { ParsedLap, TrainingParseResponse } from '@/api/training';
import { getPlannedSessionsForDate } from '@/api/weekly-plan';
import type { PlannedSessionOption } from '@/api/weekly-plan';
import { trainingTypeOptions, lapTypeOptions } from '@/constants/training';
import { ChevronRight } from 'lucide-react';
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

export default function UploadPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Pre-select strength → redirect to dedicated strength page
  const preselect = (location.state as { preselect?: string } | null)?.preselect;

  useEffect(() => {
    if (preselect === 'strength') {
      navigate('/sessions/new/strength', { replace: true });
    }
  }, [preselect, navigate]);

  // Wizard step: 0 = Upload, 1 = Prüfen
  const [step, setStep] = useState(0);

  // Shared state
  const [trainingDate, setTrainingDate] = useState<Date>(new Date());
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rpe, setRpe] = useState(5);

  // Review step
  const [parseResult, setParseResult] = useState<TrainingParseResponse | null>(null);
  const [lapOverrides, setLapOverrides] = useState<Record<number, string>>({});
  const [trainingTypeOverride, setTrainingTypeOverride] = useState<string | null>(null);

  // Planned session linking
  const [plannedSessions, setPlannedSessions] = useState<PlannedSessionOption[]>([]);
  const [selectedPlannedId, setSelectedPlannedId] = useState<number | null>(null);

  // Load planned sessions for selected date
  useEffect(() => {
    const dateStr = trainingDate.toISOString().split('T')[0];
    getPlannedSessionsForDate(dateStr)
      .then(setPlannedSessions)
      .catch(() => setPlannedSessions([]));
    setSelectedPlannedId(null);
  }, [trainingDate]);

  /* ---- Handlers ---- */

  const handleFileUpload = (files: File[]) => {
    if (files[0]) setCsvFile(files[0]);
  };

  const handleFileRemove = () => setCsvFile(null);

  // Step 0 → Parse CSV
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
        trainingType: 'running',
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

  // Step 1 → Create session
  const handleCreateRunning = async () => {
    if (!csvFile) return;

    setCreating(true);
    setError(null);

    try {
      const result = await uploadTraining({
        csvFile,
        trainingDate: trainingDate.toISOString().split('T')[0],
        trainingType: 'running',
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

  /* ---- Derived data for review step ---- */
  const laps = parseResult?.data?.laps;
  const autoType = parseResult?.metadata?.training_type_auto;
  const effectiveType = trainingTypeOverride || autoType;

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
                value="running"
                onChange={(val) => {
                  if (val === 'strength') {
                    navigate('/sessions/new/strength');
                  }
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

      {/* ============== Step 0: Import ============== */}
      {step === 0 && (
        <>
          {/* Card 1: Import + Datum */}
          <Card elevation="raised">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Training</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <FileUpload
                accept=".csv,.fit"
                onUpload={handleFileUpload}
                onRemove={handleFileRemove}
                instructionText={csvFile ? csvFile.name : 'Datei hier ablegen oder klicken'}
                subText="Unterstützt: CSV, Garmin/Wahoo FIT"
              />

              <div className="grid grid-cols-1 gap-4">
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

          {/* Card 2: Notizen */}
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

          {/* Submit */}
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
        </>
      )}

      {/* ============== Step 1 — Review ============== */}
      {step === 1 && parseResult && (
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
