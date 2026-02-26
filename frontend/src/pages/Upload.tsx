import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, RefreshCw, Save } from 'lucide-react';
import { uploadTraining, updateLapOverrides, updateTrainingType } from '@/api/training';
import type { TrainingTypeInfo } from '@/api/training';
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
  Badge,
  Progress,
  ToggleGroup,
  ToggleGroupItem,
  Spinner,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@nordlig/components';

type TrainingType = 'running' | 'strength';
type TrainingSubType =
  | 'interval'
  | 'tempo'
  | 'longrun'
  | 'recovery'
  | 'knee_dominant'
  | 'hip_dominant';
type LapType =
  | 'warmup'
  | 'interval'
  | 'pause'
  | 'tempo'
  | 'longrun'
  | 'cooldown'
  | 'recovery'
  | 'unclassified';

interface UploadFormData {
  csvFile: File | null;
  trainingDate: Date;
  trainingType: TrainingType;
  trainingSubtype: TrainingSubType | '';
  notes: string;
}

interface Lap {
  lap_number: number;
  duration_formatted: string;
  distance_km?: number;
  pace_formatted?: string;
  avg_hr_bpm?: number;
  avg_cadence_spm?: number;
  suggested_type?: LapType;
  confidence?: 'high' | 'medium' | 'low';
  user_override?: LapType;
}

interface HRZone {
  label: string;
  percentage: number;
  seconds?: number;
  minutes?: number;
  range?: string;
}

interface SessionSummary {
  duration_formatted?: string;
  total_duration_formatted?: string;
  distance_km?: number;
  total_distance_km?: number;
  avg_pace_formatted?: string;
  avg_hr_bpm?: number;
  max_hr_bpm?: number;
  avg_cadence_spm?: number;
  calories?: number;
}

interface HRTimeseriesPoint {
  timestamp: number;
  hr: number;
}

interface ParsedData {
  laps?: Lap[];
  summary?: SessionSummary;
  hr_zones?: Record<string, HRZone>;
  hr_zones_working?: Record<string, HRZone>;
  hr_timeseries?: HRTimeseriesPoint[];
}

const runningSubtypes: { value: TrainingSubType; label: string }[] = [
  { value: 'interval', label: 'Intervall' },
  { value: 'tempo', label: 'Tempo' },
  { value: 'longrun', label: 'Long Run' },
  { value: 'recovery', label: 'Recovery' },
];

const strengthSubtypes: { value: TrainingSubType; label: string }[] = [
  { value: 'knee_dominant', label: 'Knee Dominant' },
  { value: 'hip_dominant', label: 'Hip Dominant' },
];

const lapTypeOptions: { value: LapType; label: string }[] = [
  { value: 'warmup', label: 'Warm-up' },
  { value: 'interval', label: 'Intervall' },
  { value: 'pause', label: 'Pause' },
  { value: 'tempo', label: 'Tempo' },
  { value: 'longrun', label: 'Long Run' },
  { value: 'cooldown', label: 'Cool-down' },
  { value: 'recovery', label: 'Recovery' },
  { value: 'unclassified', label: 'Unklassifiziert' },
];

const confidenceBadgeVariant = {
  high: 'success',
  medium: 'warning',
  low: 'error',
} as const;

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

export default function UploadPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<UploadFormData>({
    csvFile: null,
    trainingDate: new Date(),
    trainingType: 'running',
    trainingSubtype: '',
    notes: '',
  });

  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lapOverrides, setLapOverrides] = useState<{ [key: number]: LapType }>({});
  const [savingOverrides, setSavingOverrides] = useState(false);
  const [overridesSaved, setOverridesSaved] = useState(false);
  const [trainingTypeInfo, setTrainingTypeInfo] = useState<TrainingTypeInfo | null>(null);
  const [savingTrainingType, setSavingTrainingType] = useState(false);

  const handleFileUpload = (files: File[]) => {
    if (files[0]) {
      setFormData({ ...formData, csvFile: files[0] });
    }
  };

  const handleFileRemove = () => {
    setFormData({ ...formData, csvFile: null });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.csvFile) {
      setError('Bitte CSV Datei auswählen');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await uploadTraining({
        csvFile: formData.csvFile,
        trainingDate: formData.trainingDate.toISOString().split('T')[0],
        trainingType: formData.trainingType,
        trainingSubtype: formData.trainingSubtype || undefined,
        notes: formData.notes || undefined,
      });

      if (result.success && result.session_id) {
        setParsedData(result.data as ParsedData);
        setSessionId(result.session_id);
        setLapOverrides({});

        // Training Type aus Metadata extrahieren
        const meta = result.metadata;
        if (meta?.training_type_auto) {
          setTrainingTypeInfo({
            auto: meta.training_type_auto as string,
            confidence: (meta.training_type_confidence as number) ?? null,
            override: null,
            effective: meta.training_type_auto as string,
          });
        }
      } else {
        setError(result.errors?.join(', ') || 'Upload fehlgeschlagen');
      }
    } catch (err) {
      setError('Netzwerkfehler: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleLapTypeChange = (lapNumber: number, newType: string | undefined) => {
    if (newType) {
      setLapOverrides({ ...lapOverrides, [lapNumber]: newType as LapType });
      setOverridesSaved(false);
    }
  };

  const getEffectiveLapType = (lap: Lap): LapType => {
    return lapOverrides[lap.lap_number] || lap.suggested_type || 'unclassified';
  };

  const recalculateHRZones = () => {
    if (!parsedData?.laps) return;

    const workingLaps = parsedData.laps.filter((lap) => {
      const type = getEffectiveLapType(lap);
      return type !== 'warmup' && type !== 'cooldown' && type !== 'pause';
    });

    if (workingLaps.length > 0) {
      let totalSeconds = 0;
      let zone1 = 0,
        zone2 = 0,
        zone3 = 0;

      workingLaps.forEach((lap) => {
        const duration = lap.duration_formatted
          .split(':')
          .reduce((acc, time) => 60 * acc + +time, 0);
        totalSeconds += duration;
        const hr = lap.avg_hr_bpm || 0;
        if (hr < 150) zone1 += duration;
        else if (hr < 160) zone2 += duration;
        else zone3 += duration;
      });

      setParsedData({
        ...parsedData,
        hr_zones_working: {
          zone_1_recovery: {
            seconds: zone1,
            percentage: Math.round((zone1 / totalSeconds) * 1000) / 10,
            label: '< 150 bpm',
          },
          zone_2_base: {
            seconds: zone2,
            percentage: Math.round((zone2 / totalSeconds) * 1000) / 10,
            label: '150-160 bpm',
          },
          zone_3_tempo: {
            seconds: zone3,
            percentage: Math.round((zone3 / totalSeconds) * 1000) / 10,
            label: '> 160 bpm',
          },
        },
      });
    }
  };

  const handleSaveOverrides = async () => {
    if (!sessionId || Object.keys(lapOverrides).length === 0) return;

    setSavingOverrides(true);
    try {
      const overrides = Object.entries(lapOverrides).map(([lapNumber, type]) => ({
        lap_number: Number(lapNumber),
        user_override: type,
      }));

      const result = await updateLapOverrides({ sessionId, overrides });

      if (result.success && parsedData) {
        setParsedData({
          ...parsedData,
          laps: result.laps as unknown as Lap[],
          hr_zones_working: result.hr_zones_working as unknown as Record<string, HRZone>,
        });
        setOverridesSaved(true);
        setLapOverrides({});
      }
    } catch (err) {
      setError('Speichern fehlgeschlagen: ' + (err as Error).message);
    } finally {
      setSavingOverrides(false);
    }
  };

  const handleTrainingTypeOverride = async (newType: string | undefined) => {
    if (!sessionId || !newType) return;

    setSavingTrainingType(true);
    try {
      const result = await updateTrainingType(sessionId, newType);
      if (result.training_type) {
        setTrainingTypeInfo(result.training_type);
      }
    } catch (err) {
      setError('Training Type speichern fehlgeschlagen: ' + (err as Error).message);
    } finally {
      setSavingTrainingType(false);
    }
  };

  const hasUnsavedOverrides = Object.keys(lapOverrides).length > 0;

  const currentSubtypes = formData.trainingType === 'running' ? runningSubtypes : strengthSubtypes;

  return (
    <div className="py-8 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Page Header */}
        <header>
          <div className="flex items-center gap-3 mb-1">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-primary-1-100)]">
              <Activity
                className="w-5 h-5 text-[var(--color-primary-1-600)]"
                aria-hidden="true"
              />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-[var(--color-text-base)]">
                Training Upload
              </h1>
              <p className="text-sm text-[var(--color-text-muted)]">
                Lade deine Apple Watch Daten hoch und analysiere dein Training.
              </p>
            </div>
          </div>
        </header>

        {/* Upload Form */}
        <Card elevation="raised" padding="spacious" className="overflow-hidden bg-white border border-[var(--color-border-default)]">
          <form onSubmit={handleSubmit} className="space-y-6">
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                <Label>Trainingsart</Label>
                <Select
                  options={[{ value: '', label: 'Optional' }, ...currentSubtypes]}
                  value={formData.trainingSubtype}
                  onChange={(val) =>
                    setFormData({
                      ...formData,
                      trainingSubtype: (val ?? '') as TrainingSubType | '',
                    })
                  }
                  placeholder="Optional"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Trainingstyp</Label>
              <ToggleGroup
                type="single"
                variant="outline"
                value={formData.trainingType}
                onValueChange={(val) => {
                  if (val)
                    setFormData({
                      ...formData,
                      trainingType: val as TrainingType,
                      trainingSubtype: '',
                    });
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

            {error && (
              <Alert variant="error" closeable onClose={() => setError(null)}>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              variant="primary"
              disabled={loading || !formData.csvFile}
              className="w-full"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Spinner size="sm" aria-hidden="true" />
                  Analysiere...
                </span>
              ) : (
                'Training analysieren'
              )}
            </Button>
          </form>
        </Card>

        {/* Results */}
        {parsedData && (
          <section className="space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-1 h-6 rounded-full bg-[var(--color-primary-1-500)]" />
              <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
                Analyse-Ergebnisse
              </h2>
            </div>

            {/* Summary Stats */}
            {parsedData.summary && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {parsedData.summary.total_distance_km && (
                  <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-primary-1-500)]">
                    <CardBody>
                      <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Distanz</p>
                      <p className="text-2xl font-bold text-[var(--color-text-base)]">
                        {parsedData.summary.total_distance_km} <span className="text-sm font-normal text-[var(--color-text-muted)]">km</span>
                      </p>
                    </CardBody>
                  </Card>
                )}
                <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-accent-1-500)]">
                  <CardBody>
                    <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Dauer</p>
                    <p className="text-2xl font-bold text-[var(--color-text-base)]">
                      {parsedData.summary.total_duration_formatted}
                    </p>
                  </CardBody>
                </Card>
                {parsedData.summary.avg_pace_formatted && (
                  <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-accent-2-500)]">
                    <CardBody>
                      <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Pace</p>
                      <p className="text-2xl font-bold text-[var(--color-text-base)]">
                        {parsedData.summary.avg_pace_formatted} <span className="text-sm font-normal text-[var(--color-text-muted)]">/km</span>
                      </p>
                    </CardBody>
                  </Card>
                )}
                <Card elevation="raised" padding="compact" className="bg-white border-l-4 border-l-[var(--color-accent-3-500)]">
                  <CardBody>
                    <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Ø Herzfrequenz</p>
                    <p className="text-2xl font-bold text-[var(--color-text-base)]">
                      {parsedData.summary.avg_hr_bpm} <span className="text-sm font-normal text-[var(--color-text-muted)]">bpm</span>
                    </p>
                  </CardBody>
                </Card>
              </div>
            )}

            {/* Training Type Classification */}
            {trainingTypeInfo && (
              <Card elevation="raised" padding="spacious" className="bg-white">
                <CardBody>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-[var(--color-text-muted)]">
                        Erkannter Trainingstyp:
                      </span>
                      <Badge
                        variant={
                          trainingTypeBadgeVariant[trainingTypeInfo.effective ?? ''] ?? 'info'
                        }
                        size="md"
                      >
                        {trainingTypeLabels[trainingTypeInfo.effective ?? ''] ??
                          trainingTypeInfo.effective}
                      </Badge>
                      {trainingTypeInfo.confidence !== null && !trainingTypeInfo.override && (
                        <span className="text-xs text-[var(--color-text-muted)]">
                          ({trainingTypeInfo.confidence}% Konfidenz)
                        </span>
                      )}
                      {trainingTypeInfo.override && (
                        <Badge variant="info" size="sm">
                          Manuell
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {savingTrainingType ? (
                        <Spinner size="sm" />
                      ) : (
                        <Select
                          options={trainingTypeOptions}
                          value={trainingTypeInfo.effective ?? undefined}
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
            {parsedData.hr_zones && (
              <div
                className={`grid gap-4 ${parsedData.laps?.length ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}
              >
                <Card elevation="raised" className="bg-white">
                  <CardBody>
                    <h3 className="text-sm font-semibold text-[var(--color-text-base)] mb-1">
                      HF-Zonen Gesamt
                    </h3>
                    <p className="text-xs text-[var(--color-text-muted)] mb-4">
                      {parsedData.laps?.length ? 'Alle Laps' : 'Komplette Session'}
                    </p>
                    <div className="space-y-3">
                      {Object.entries(parsedData.hr_zones).map(([key, zone]: [string, HRZone]) => (
                        <div key={key}>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-[var(--color-text-muted)]">{zone.label}</span>
                            <span className="font-medium text-[var(--color-text-base)]">
                              {zone.percentage}%
                            </span>
                          </div>
                          <Progress
                            value={zone.percentage}
                            size="sm"
                            color={
                              key.includes('recovery')
                                ? 'success'
                                : key.includes('base')
                                  ? 'warning'
                                  : 'error'
                            }
                          />
                        </div>
                      ))}
                    </div>
                  </CardBody>
                </Card>

                {parsedData.laps && parsedData.laps.length > 0 && (
                  <Card elevation="raised" className="bg-white">
                    <CardBody>
                      <h3 className="text-sm font-semibold text-[var(--color-text-base)] mb-1">
                        HF-Zonen Arbeits-Laps
                      </h3>
                      <p className="text-xs text-[var(--color-text-muted)] mb-4">
                        Ohne Warm-up, Cool-down, Pausen
                      </p>
                      {parsedData.hr_zones_working ? (
                        <div className="space-y-3">
                          {Object.entries(parsedData.hr_zones_working).map(
                            ([key, zone]: [string, HRZone]) => (
                              <div key={key}>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-[var(--color-text-muted)]">
                                    {zone.label}
                                  </span>
                                  <span className="font-medium text-[var(--color-text-base)]">
                                    {zone.percentage}%
                                  </span>
                                </div>
                                <Progress
                                  value={zone.percentage}
                                  size="sm"
                                  color={
                                    key.includes('recovery')
                                      ? 'success'
                                      : key.includes('base')
                                        ? 'warning'
                                        : 'error'
                                  }
                                />
                              </div>
                            ),
                          )}
                        </div>
                      ) : (
                        <p className="text-xs text-[var(--color-text-muted)] py-6 text-center">
                          Überprüfe die Lap-Typen und klicke &quot;Neu berechnen&quot;
                        </p>
                      )}
                    </CardBody>
                  </Card>
                )}
              </div>
            )}

            {/* Laps Table */}
            {parsedData.laps && parsedData.laps.length > 0 && (
              <Card elevation="raised" className="bg-white">
                <CardHeader className="flex flex-row items-center justify-between">
                  <h3 className="text-sm font-semibold text-[var(--color-text-base)]">
                    Laps ({parsedData.laps.length})
                  </h3>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" onClick={recalculateHRZones}>
                      <RefreshCw className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
                      Neu berechnen
                    </Button>
                    {sessionId && hasUnsavedOverrides && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleSaveOverrides}
                        disabled={savingOverrides}
                      >
                        {savingOverrides ? (
                          <Spinner size="sm" aria-hidden="true" />
                        ) : (
                          <Save className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
                        )}
                        Speichern
                      </Button>
                    )}
                    {overridesSaved && !hasUnsavedOverrides && (
                      <Badge variant="success" size="sm">
                        Gespeichert
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <div className="overflow-x-auto -mx-[var(--spacing-card-padding-normal)]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead className="min-w-[200px]">Typ</TableHead>
                        <TableHead>Dauer</TableHead>
                        <TableHead>Distanz</TableHead>
                        <TableHead>Pace</TableHead>
                        <TableHead>Ø HF</TableHead>
                        <TableHead>Kadenz</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {parsedData.laps.map((lap: Lap) => (
                        <TableRow key={lap.lap_number}>
                          <TableCell className="font-medium text-[var(--color-text-muted)]">
                            {lap.lap_number}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Select
                                options={lapTypeOptions}
                                value={getEffectiveLapType(lap)}
                                onChange={(val) => handleLapTypeChange(lap.lap_number, val)}
                                inputSize="sm"
                                className="w-36"
                              />
                              {lap.confidence && !lapOverrides[lap.lap_number] && (
                                <Badge variant={confidenceBadgeVariant[lap.confidence]} size="sm">
                                  {lap.confidence}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>{lap.duration_formatted}</TableCell>
                          <TableCell>{lap.distance_km ? `${lap.distance_km} km` : '-'}</TableCell>
                          <TableCell>
                            {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                          </TableCell>
                          <TableCell>{lap.avg_hr_bpm ? `${lap.avg_hr_bpm}` : '-'}</TableCell>
                          <TableCell>
                            {lap.avg_cadence_spm ? `${lap.avg_cadence_spm}` : '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </Card>
            )}
            {/* Success Action */}
            {sessionId && (
              <div className="flex justify-end">
                <Button variant="primary" onClick={() => navigate(`/sessions/${sessionId}`)}>
                  Zur Session
                </Button>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
