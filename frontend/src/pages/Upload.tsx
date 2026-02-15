import { useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  Input,
  Label,
  Select,
  Textarea,
  FileUpload,
  Alert,
  AlertDescription,
  Badge,
  Progress,
  Spinner,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Separator,
} from '@nordlig/components';

type TrainingType = 'running' | 'strength';
type TrainingSubType = 'interval' | 'tempo' | 'longrun' | 'recovery' | 'knee_dominant' | 'hip_dominant';
type LapType = 'warmup' | 'interval' | 'pause' | 'tempo' | 'longrun' | 'cooldown' | 'recovery' | 'unclassified';

interface UploadFormData {
  csvFile: File | null;
  trainingDate: string;
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

interface ParsedData {
  laps?: Lap[];
  summary?: any;
  hr_zones?: any;
  hr_zones_working?: any;
  hr_timeseries?: any[];
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

export default function UploadPage() {
  const [formData, setFormData] = useState<UploadFormData>({
    csvFile: null,
    trainingDate: new Date().toISOString().split('T')[0],
    trainingType: 'running',
    trainingSubtype: '',
    notes: '',
  });

  const [parsedData, setParsedData] = useState<ParsedData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lapOverrides, setLapOverrides] = useState<{ [key: number]: LapType }>({});

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

    const data = new FormData();
    data.append('csv_file', formData.csvFile);
    data.append('training_date', formData.trainingDate);
    data.append('training_type', formData.trainingType);
    if (formData.trainingSubtype) {
      data.append('training_subtype', formData.trainingSubtype);
    }
    if (formData.notes) {
      data.append('notes', formData.notes);
    }

    try {
      const apiBase = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8001`;
      const response = await fetch(`${apiBase}/api/training/upload`, {
        method: 'POST',
        body: data,
      });

      const result = await response.json();

      if (result.success) {
        setParsedData(result.data);
        setLapOverrides({});
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
    }
  };

  const getEffectiveLapType = (lap: Lap): LapType => {
    return lapOverrides[lap.lap_number] || lap.suggested_type || 'unclassified';
  };

  const recalculateHRZones = () => {
    if (!parsedData?.laps) return;

    const workingLaps = parsedData.laps.filter(lap => {
      const type = getEffectiveLapType(lap);
      return type !== 'warmup' && type !== 'cooldown' && type !== 'pause';
    });

    if (workingLaps.length > 0) {
      let totalSeconds = 0;
      let zone1 = 0, zone2 = 0, zone3 = 0;

      workingLaps.forEach(lap => {
        const duration = lap.duration_formatted.split(':').reduce((acc, time) => (60 * acc) + +time, 0);
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

  const currentSubtypes = formData.trainingType === 'running' ? runningSubtypes : strengthSubtypes;

  return (
    <div className="min-h-screen bg-[var(--color-bg-base)] py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <Card elevation="raised">
          <CardHeader>
            <h1 className="text-2xl font-bold text-[var(--color-text-base)] flex items-center gap-2">
              <Activity className="w-7 h-7 text-[color:var(--color-interactive-primary)]" aria-hidden="true" />
              Training Upload
            </h1>
          </CardHeader>

          <CardBody>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Upload */}
              <FileUpload
                label="CSV Datei"
                accept=".csv"
                onUpload={handleFileUpload}
                onRemove={handleFileRemove}
                instructionText={formData.csvFile ? formData.csvFile.name : 'CSV Datei hier ablegen oder klicken'}
                subText="Apple Watch Export (.csv)"
              />

              {/* Date */}
              <div className="space-y-2">
                <Label htmlFor="trainingDate">Trainingsdatum</Label>
                <Input
                  id="trainingDate"
                  type="date"
                  value={formData.trainingDate}
                  onChange={(e) => setFormData({ ...formData, trainingDate: e.target.value })}
                  required
                />
              </div>

              {/* Training Type */}
              <div className="space-y-2">
                <Label>Trainingstyp</Label>
                <div className="grid grid-cols-2 gap-4">
                  <Button
                    type="button"
                    variant={formData.trainingType === 'running' ? 'primary' : 'secondary'}
                    onClick={() => setFormData({ ...formData, trainingType: 'running', trainingSubtype: '' })}
                  >
                    Laufen
                  </Button>
                  <Button
                    type="button"
                    variant={formData.trainingType === 'strength' ? 'primary' : 'secondary'}
                    onClick={() => setFormData({ ...formData, trainingType: 'strength', trainingSubtype: '' })}
                  >
                    Kraft
                  </Button>
                </div>
              </div>

              {/* Subtype */}
              <div className="space-y-2">
                <Label>Trainingsart (optional)</Label>
                <Select
                  options={[{ value: '', label: '-- Auswählen --' }, ...currentSubtypes]}
                  value={formData.trainingSubtype}
                  onChange={(val) => setFormData({ ...formData, trainingSubtype: (val ?? '') as TrainingSubType | '' })}
                  placeholder="-- Auswählen --"
                />
              </div>

              {/* Notes */}
              <Textarea
                label="Notizen (optional)"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                placeholder="Wie hast du dich gefühlt?"
              />

              {/* Error */}
              {error && (
                <Alert variant="error" closeable onClose={() => setError(null)}>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Submit */}
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

            {/* Results */}
            {parsedData && (
              <div className="mt-8">
                <Separator className="mb-6" />
                <h2 className="text-xl font-bold text-[var(--color-text-base)] mb-4">
                  Analyse-Ergebnisse
                </h2>

                {/* Summary */}
                {parsedData.summary && (
                  <Card elevation="raised" className="mb-6">
                    <CardBody>
                      <h3 className="text-lg font-semibold text-[var(--color-text-base)] mb-4">
                        Zusammenfassung
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {parsedData.summary.total_distance_km && (
                          <div>
                            <p className="text-sm text-[var(--color-text-muted)]">Distanz</p>
                            <p className="text-2xl font-bold text-[var(--color-text-base)]">
                              {parsedData.summary.total_distance_km} km
                            </p>
                          </div>
                        )}
                        <div>
                          <p className="text-sm text-[var(--color-text-muted)]">Dauer</p>
                          <p className="text-2xl font-bold text-[var(--color-text-base)]">
                            {parsedData.summary.total_duration_formatted}
                          </p>
                        </div>
                        {parsedData.summary.avg_pace_formatted && (
                          <div>
                            <p className="text-sm text-[var(--color-text-muted)]">Pace</p>
                            <p className="text-2xl font-bold text-[var(--color-text-base)]">
                              {parsedData.summary.avg_pace_formatted} /km
                            </p>
                          </div>
                        )}
                        <div>
                          <p className="text-sm text-[var(--color-text-muted)]">Ø HF</p>
                          <p className="text-2xl font-bold text-[var(--color-text-base)]">
                            {parsedData.summary.avg_hr_bpm} bpm
                          </p>
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                )}

                {/* HR Zones */}
                {parsedData.hr_zones && (
                  <div className={`grid gap-6 mb-6 ${parsedData.laps?.length ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
                    {/* Overall */}
                    <Card elevation="raised">
                      <CardBody>
                        <h3 className="text-lg font-semibold text-[var(--color-text-base)] mb-4">
                          HF-Zonen Gesamt
                        </h3>
                        <p className="text-sm text-[var(--color-text-muted)] mb-4">
                          {parsedData.laps?.length ? 'Komplette Session (alle Laps)' : 'Komplette Session'}
                        </p>
                        <div className="space-y-3">
                          {Object.entries(parsedData.hr_zones).map(([key, zone]: [string, any]) => (
                            <div key={key}>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-[var(--color-text-base)]">{zone.label}</span>
                                <span className="font-medium text-[var(--color-text-base)]">{zone.percentage}%</span>
                              </div>
                              <Progress
                                value={zone.percentage}
                                size="sm"
                                color={
                                  key.includes('recovery') ? 'success' :
                                  key.includes('base') ? 'warning' :
                                  'error'
                                }
                              />
                            </div>
                          ))}
                        </div>
                      </CardBody>
                    </Card>

                    {/* Working Laps */}
                    {parsedData.laps && parsedData.laps.length > 0 && (
                      <Card elevation="raised">
                        <CardBody>
                          <h3 className="text-lg font-semibold text-[var(--color-text-base)] mb-4">
                            HF-Zonen Arbeits-Laps
                          </h3>
                          <p className="text-sm text-[var(--color-text-muted)] mb-4">
                            Nur Intervalle/Tempo (ohne Warm-up/Cool-down/Pausen)
                          </p>
                          {parsedData.hr_zones_working ? (
                            <div className="space-y-3">
                              {Object.entries(parsedData.hr_zones_working).map(([key, zone]: [string, any]) => (
                                <div key={key}>
                                  <div className="flex justify-between text-sm mb-1">
                                    <span className="text-[var(--color-text-base)]">{zone.label}</span>
                                    <span className="font-medium text-[var(--color-text-base)]">{zone.percentage}%</span>
                                  </div>
                                  <Progress
                                    value={zone.percentage}
                                    size="sm"
                                    color={
                                      key.includes('recovery') ? 'success' :
                                      key.includes('base') ? 'warning' :
                                      'error'
                                    }
                                  />
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-center py-8">
                              <p className="text-[var(--color-text-muted)] text-sm mb-2">Noch nicht berechnet</p>
                              <p className="text-[var(--color-text-muted)] text-xs">
                                Überprüfe die Lap-Typen unten und klicke auf &quot;HF-Zonen berechnen&quot;
                              </p>
                            </div>
                          )}
                        </CardBody>
                      </Card>
                    )}
                  </div>
                )}

                {/* Laps Table */}
                {parsedData.laps && parsedData.laps.length > 0 && (
                  <Card elevation="raised" className="mb-6">
                    <CardHeader className="flex flex-row items-center justify-between">
                      <h3 className="text-lg font-semibold text-[var(--color-text-base)]">
                        Laps ({parsedData.laps.length})
                      </h3>
                      <Button variant="primary" size="sm" onClick={recalculateHRZones}>
                        <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
                        HF-Zonen berechnen
                      </Button>
                    </CardHeader>
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>#</TableHead>
                            <TableHead>Typ</TableHead>
                            <TableHead>Dauer</TableHead>
                            <TableHead>Distanz</TableHead>
                            <TableHead>Pace</TableHead>
                            <TableHead>Ø HF</TableHead>
                            <TableHead>Ø Kadenz</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {parsedData.laps.map((lap: Lap) => (
                            <TableRow key={lap.lap_number}>
                              <TableCell className="font-medium">{lap.lap_number}</TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <Select
                                    options={lapTypeOptions}
                                    value={getEffectiveLapType(lap)}
                                    onChange={(val) => handleLapTypeChange(lap.lap_number, val)}
                                    inputSize="sm"
                                    className="w-40"
                                  />
                                  {lap.confidence && !lapOverrides[lap.lap_number] && (
                                    <Badge
                                      variant={confidenceBadgeVariant[lap.confidence]}
                                      size="sm"
                                    >
                                      {lap.confidence}
                                    </Badge>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>{lap.duration_formatted}</TableCell>
                              <TableCell>{lap.distance_km ? `${lap.distance_km} km` : '-'}</TableCell>
                              <TableCell>{lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}</TableCell>
                              <TableCell>{lap.avg_hr_bpm ? `${lap.avg_hr_bpm} bpm` : '-'}</TableCell>
                              <TableCell>{lap.avg_cadence_spm ? `${lap.avg_cadence_spm} spm` : '-'}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </Card>
                )}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
