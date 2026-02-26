import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload } from 'lucide-react';
import { parseTraining, uploadTraining } from '@/api/training';
import type { ParsedLap, TrainingParseResponse } from '@/api/training';
import {
  trainingTypeOptions,
  lapTypeOptions,
} from '@/constants/training';
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
/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

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

  // Wizard step: 0 = Upload, 1 = Prüfen
  const [step, setStep] = useState(0);

  const [formData, setFormData] = useState<UploadFormData>({
    csvFile: null,
    trainingDate: new Date(),
    trainingType: 'running',
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Review step state
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

  // Step 0 → next: Parse CSV, then review (running) or upload directly (strength)
  const handleNext = async () => {
    if (!formData.csvFile) {
      setError('Bitte CSV Datei auswählen');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (formData.trainingType === 'strength') {
        // Strength: skip review, upload directly
        const result = await uploadTraining({
          csvFile: formData.csvFile,
          trainingDate: formData.trainingDate.toISOString().split('T')[0],
          trainingType: formData.trainingType,
          notes: formData.notes || undefined,
        });

        if (result.success && result.session_id) {
          navigate(`/sessions/${result.session_id}`, { state: { uploaded: true } });
        } else {
          setError(result.errors?.join(', ') || 'Upload fehlgeschlagen');
        }
      } else {
        // Running: parse first, then show review step
        const result = await parseTraining({
          csvFile: formData.csvFile,
          trainingDate: formData.trainingDate.toISOString().split('T')[0],
          trainingType: formData.trainingType,
          notes: formData.notes || undefined,
        });

        if (result.success && result.data) {
          setParseResult(result);

          // Initialize lap overrides from suggested types
          const initialOverrides: Record<number, string> = {};
          if (result.data.laps) {
            for (const lap of result.data.laps) {
              initialOverrides[lap.lap_number] = lap.suggested_type || 'unclassified';
            }
          }
          setLapOverrides(initialOverrides);

          // Initialize training type override from auto classification
          setTrainingTypeOverride(result.metadata?.training_type_auto || null);

          setStep(1);
        } else {
          setError(result.errors?.join(', ') || 'Analyse fehlgeschlagen');
        }
      }
    } catch (err) {
      setError('Netzwerkfehler: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Create session
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
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      {/* Page Header */}
      <header className="flex items-center gap-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-primary-1-100)]">
          <Upload className="w-5 h-5 text-[var(--color-primary-1-600)]" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-3xl font-semibold text-[var(--color-text-base)]">Training Upload</h1>
          <p className="text-xs text-[var(--color-text-muted)]">
            Apple Watch Daten hochladen
          </p>
        </div>
      </header>

      {/* Step Card */}
      <Card elevation="raised">
        {/* ============== Step 0: Upload ============== */}
        {step === 0 && (
          <>
            <CardHeader>
              <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
                CSV Datei hochladen
              </h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <FileUpload
                label="CSV Datei"
                accept=".csv"
                onUpload={handleFileUpload}
                onRemove={handleFileRemove}
                instructionText={
                  formData.csvFile ? formData.csvFile.name : 'CSV Datei hier ablegen oder klicken'
                }
                subText="Apple Watch Export (.csv)"
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

              <div className="space-y-2">
                <Label>Trainingstyp</Label>
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
                    {formData.trainingType === 'strength' ? 'Erstelle Session...' : 'Analysiere...'}
                  </span>
                ) : formData.trainingType === 'strength' ? (
                  'Session anlegen'
                ) : (
                  'Weiter'
                )}
              </Button>
            </CardFooter>
          </>
        )}

        {/* ============== Step 1: Prüfen ============== */}
        {step === 1 && parseResult && (
          <>
            <CardHeader>
              <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
                Klassifikation prüfen
              </h2>
              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                Die folgenden Zuordnungen wurden automatisch erkannt. Passe sie bei Bedarf an — sie bestimmen, wie dein Training in der Auswertung kategorisiert wird.
              </p>
            </CardHeader>
            <CardBody className="space-y-8">
              {/* Training Type */}
              <div>
                <Label className="mb-1">Trainingstyp</Label>
                <p className="text-xs text-[var(--color-text-muted)] mb-3">
                  Bestimmt die Gesamtkategorisierung deiner Session (z.B. Easy Run, Tempo, Intervall).
                </p>
                <Select
                  options={trainingTypeOptions}
                  value={effectiveType ?? undefined}
                  onChange={(val) => setTrainingTypeOverride(val ?? null)}
                  placeholder="Typ wählen"
                />
              </div>

              {/* Lap Table */}
              {laps && laps.length > 0 && (
                <div>
                  <Label className="mb-1">Lap-Klassifikation ({laps.length} Laps)</Label>
                  <p className="text-xs text-[var(--color-text-muted)] mb-3">
                    Jeder Lap wurde einem Typ zugeordnet. Das beeinflusst die Berechnung von Arbeitsphasen und Erholungszeiten.
                  </p>
                  <div className="overflow-x-auto rounded-[var(--radius-component-md)] border border-[var(--color-border-default)]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12">#</TableHead>
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
                                  className="w-36"
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
          </>
        )}
      </Card>

      {/* Error */}
      {error && (
        <Alert variant="error" closeable onClose={() => setError(null)}>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
