import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { parseTraining, uploadTraining } from '@/api/training';
import type { ParsedLap, TrainingParseResponse } from '@/api/training';
import { trainingTypeOptions, lapTypeOptions } from '@/constants/training';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  DatePicker,
  Label,
  Select,
  Textarea,
  FileUpload,
  Alert,
  AlertDescription,
  Spinner,
  ToggleGroup,
  ToggleGroupItem,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@nordlig/components';
import { StrengthForm } from '@/features/strength';

/* ------------------------------------------------------------------ */
/*  State types                                                       */
/* ------------------------------------------------------------------ */

type TrainingType = 'running' | 'strength';

interface UploadFormData {
  csvFile: File | null;
  trainingDate: Date;
  trainingType: TrainingType;
  notes: string;
}

/* ------------------------------------------------------------------ */
/*  Component                                                         */
/* ------------------------------------------------------------------ */

export default function UploadPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Pre-select strength if navigated with state
  const preselect = (location.state as { preselect?: string } | null)?.preselect;

  // Wizard step: 0 = Upload, 1 = Prüfen (only for running)
  const [step, setStep] = useState(0);

  const [formData, setFormData] = useState<UploadFormData>({
    csvFile: null,
    trainingDate: new Date(),
    trainingType: preselect === 'strength' ? 'strength' : 'running',
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Review step state (running only)
  const [parseResult, setParseResult] = useState<TrainingParseResponse | null>(null);
  const [lapOverrides, setLapOverrides] = useState<Record<number, string>>({});
  const [trainingTypeOverride, setTrainingTypeOverride] = useState<string | null>(null);

  /* ---- Handlers ---- */

  const handleFileUpload = (files: File[]) => {
    if (files[0]) {
      setFormData({ ...formData, csvFile: files[0] });
    }
  };

  const handleFileRemove = () => {
    setFormData({ ...formData, csvFile: null });
  };

  // Step 0 → next: Parse CSV, then review
  const handleNext = async () => {
    if (!formData.csvFile) {
      setError('Bitte Datei auswählen');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await parseTraining({
        csvFile: formData.csvFile,
        trainingDate: formData.trainingDate.toISOString().split('T')[0],
        trainingType: formData.trainingType,
        notes: formData.notes || undefined,
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

  // Step 1: Create session (running)
  const handleCreate = async () => {
    if (!formData.csvFile) return;

    setCreating(true);
    setError(null);

    try {
      const result = await uploadTraining({
        csvFile: formData.csvFile,
        trainingDate: formData.trainingDate.toISOString().split('T')[0],
        trainingType: formData.trainingType,
        notes: formData.notes || undefined,
        lapOverrides: Object.keys(lapOverrides).length > 0 ? lapOverrides : undefined,
        trainingTypeOverride: trainingTypeOverride || undefined,
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
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      {/* Page Header */}
      <header>
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Neues Training
        </h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          {formData.trainingType === 'strength'
            ? 'Uebungen, Saetze und Gewichte erfassen'
            : 'Lade eine Exportdatei deiner Sportuhr hoch'}
        </p>
      </header>

      {/* Type Selector — always visible when not in review step */}
      {step === 0 && (
        <Card elevation="raised">
          <CardBody>
            <ToggleGroup
              type="single"
              variant="outline"
              value={formData.trainingType}
              onValueChange={(val) => {
                if (val) setFormData({ ...formData, trainingType: val as TrainingType });
              }}
              className="w-full"
            >
              <ToggleGroupItem value="running" className="flex-1">
                Laufen
              </ToggleGroupItem>
              <ToggleGroupItem value="strength" className="flex-1">
                Kraft
              </ToggleGroupItem>
            </ToggleGroup>
          </CardBody>
        </Card>
      )}

      {/* ============== Running: Step 0 — Upload ============== */}
      {formData.trainingType === 'running' && step === 0 && (
        <Card elevation="raised">
          <CardHeader>
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
              Training importieren
            </h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <FileUpload
              accept=".csv,.fit"
              onUpload={handleFileUpload}
              onRemove={handleFileRemove}
              instructionText={
                formData.csvFile ? formData.csvFile.name : 'Datei hier ablegen oder klicken'
              }
              subText="Unterstützt: CSV, Garmin/Wahoo FIT"
            />

            <div className="space-y-2">
              <Label>Trainingsdatum</Label>
              <DatePicker
                value={formData.trainingDate}
                onChange={(date) => {
                  if (date) setFormData({ ...formData, trainingDate: date });
                }}
                maxDate={new Date()}
                placeholder="Datum wählen"
              />
            </div>

            <Textarea
              label="Notizen"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={2}
              placeholder="Wie hast du dich gefühlt? (optional)"
            />
          </CardBody>
          <CardFooter className="justify-end pt-4">
            <Button
              variant="primary"
              onClick={handleNext}
              disabled={!formData.csvFile || loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner size="sm" aria-hidden="true" />
                  Analysiere...
                </span>
              ) : (
                'Weiter'
              )}
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* ============== Running: Step 1 — Review ============== */}
      {formData.trainingType === 'running' && step === 1 && parseResult && (
        <Card elevation="raised">
          <CardHeader>
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
              Klassifikation prüfen
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mt-1">
              Automatisch erkannte Zuordnungen. Bei Bedarf anpassen.
            </p>
          </CardHeader>
          <CardBody className="space-y-6">
            <div className="space-y-2">
              <Label>Trainingstyp</Label>
              <Select
                options={trainingTypeOptions}
                value={effectiveType ?? undefined}
                onChange={(val) => setTrainingTypeOverride(val ?? null)}
                placeholder="Typ wählen"
              />
            </div>

            {laps && laps.length > 0 && (
              <div className="space-y-2">
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
          <CardFooter className="justify-between pt-4">
            <Button variant="ghost" onClick={handleBack} disabled={creating}>
              Zurück
            </Button>
            <Button variant="primary" onClick={handleCreate} disabled={creating}>
              {creating ? (
                <span className="flex items-center gap-2">
                  <Spinner size="sm" aria-hidden="true" />
                  Erstelle Session...
                </span>
              ) : (
                'Session anlegen'
              )}
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* ============== Strength Form ============== */}
      {formData.trainingType === 'strength' && <StrengthForm />}

      {/* Error (running only — StrengthForm has its own error) */}
      {formData.trainingType === 'running' && error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
