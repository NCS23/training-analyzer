import { useState } from 'react';
import { Upload, FileText, Calendar, Activity, RefreshCw } from 'lucide-react';

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
  hr_zones_working?: any;  // <- Diese Zeile hinzufügen
  hr_timeseries?: any[];
}

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFormData({ ...formData, csvFile: e.target.files[0] });
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFormData({ ...formData, csvFile: e.dataTransfer.files[0] });
    }
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
      const response = await fetch('http://192.168.68.52:8001/api/training/upload', {
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

  const handleLapTypeChange = (lapNumber: number, newType: LapType) => {
    setLapOverrides({
      ...lapOverrides,
      [lapNumber]: newType
    });
  };

  const getEffectiveLapType = (lap: Lap): LapType => {
    return lapOverrides[lap.lap_number] || lap.suggested_type || 'unclassified';
  };

  const recalculateHRZones = () => {
    if (!parsedData?.laps) return;

    // Filter working laps (exclude warmup/cooldown)
    const workingLaps = parsedData.laps.filter(lap => {
      const type = getEffectiveLapType(lap);
      return type !== 'warmup' && type !== 'cooldown' && type !== 'pause';
    });

    // Calculate HR zones for working laps only
    if (workingLaps.length > 0) {
      let totalSeconds = 0;
      let zone1 = 0, zone2 = 0, zone3 = 0;

      workingLaps.forEach(lap => {
        const duration = lap.duration_formatted.split(':').reduce((acc, time) => (60 * acc) + +time, 0);
        totalSeconds += duration;

        const hr = lap.avg_hr_bpm || 0;
        if (hr < 150) {
          zone1 += duration;
        } else if (hr < 160) {
          zone2 += duration;
        } else {
          zone3 += duration;
        }
      });

      // Update parsed data with new zones
      setParsedData({
        ...parsedData,
        hr_zones_working: {
          zone_1_recovery: {
            seconds: zone1,
            percentage: Math.round((zone1 / totalSeconds) * 100 * 10) / 10,
            label: '< 150 bpm',
          },
          zone_2_base: {
            seconds: zone2,
            percentage: Math.round((zone2 / totalSeconds) * 100 * 10) / 10,
            label: '150-160 bpm',
          },
          zone_3_tempo: {
            seconds: zone3,
            percentage: Math.round((zone3 / totalSeconds) * 100 * 10) / 10,
            label: '> 160 bpm',
          },
        }
      });
    }
  };

  const runningSubtypes: TrainingSubType[] = ['interval', 'tempo', 'longrun', 'recovery'];
  const strengthSubtypes: TrainingSubType[] = ['knee_dominant', 'hip_dominant'];

  const currentSubtypes = formData.trainingType === 'running' 
    ? runningSubtypes 
    : strengthSubtypes;

  const lapTypes: LapType[] = ['warmup', 'interval', 'pause', 'tempo', 'longrun', 'cooldown', 'recovery', 'unclassified'];

  const lapTypeLabels: Record<LapType, string> = {
    warmup: '🔥 Warm-up',
    interval: '⚡ Intervall',
    pause: '💤 Pause',
    tempo: '🏃 Tempo',
    longrun: '🏃‍♂️ Longrun',
    cooldown: '❄️ Cool-down',
    recovery: '🧘 Recovery',
    unclassified: '❓ Unklassifiziert'
  };

  const confidenceColors = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-orange-100 text-orange-800'
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Activity className="w-8 h-8 text-blue-600" />
            Training Upload
          </h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload */}
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors cursor-pointer"
            >
              <input
                type="file"
                id="csvFile"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="csvFile" className="cursor-pointer">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">
                  {formData.csvFile 
                    ? formData.csvFile.name 
                    : 'CSV Datei hier ablegen oder klicken'}
                </p>
                <p className="text-sm text-gray-400">Apple Watch Export (.csv)</p>
              </label>
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                Trainingsdatum
              </label>
              <input
                type="date"
                value={formData.trainingDate}
                onChange={(e) => setFormData({ ...formData, trainingDate: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>

            {/* Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trainingstyp
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, trainingType: 'running', trainingSubtype: '' })}
                  className={`px-4 py-3 rounded-md font-medium ${
                    formData.trainingType === 'running'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  🏃 Laufen
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, trainingType: 'strength', trainingSubtype: '' })}
                  className={`px-4 py-3 rounded-md font-medium ${
                    formData.trainingType === 'strength'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  🏋️ Kraft
                </button>
              </div>
            </div>

            {/* Subtype */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trainingsart (optional)
              </label>
              <select
                value={formData.trainingSubtype}
                onChange={(e) => setFormData({ ...formData, trainingSubtype: e.target.value as TrainingSubType })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md"
              >
                <option value="">-- Auswählen --</option>
                {currentSubtypes.map((type) => (
                  <option key={type} value={type}>
                    {type.replace('_', ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileText className="w-4 h-4 inline mr-2" />
                Notizen (optional)
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-md"
                placeholder="Wie hast du dich gefühlt?"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !formData.csvFile}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300"
            >
              {loading ? 'Analysiere...' : 'Training analysieren'}
            </button>
          </form>

          {/* Results */}
          {parsedData && (
            <div className="mt-8 border-t pt-6">
              <h2 className="text-2xl font-bold mb-4">Analyse-Ergebnisse</h2>
              
              {parsedData.summary && (
                <div className="bg-blue-50 rounded-lg p-6 mb-6">
                  <h3 className="text-lg font-semibold mb-4">Zusammenfassung</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {parsedData.summary.total_distance_km && (
                      <div>
                        <p className="text-sm text-gray-600">Distanz</p>
                        <p className="text-2xl font-bold">
                          {parsedData.summary.total_distance_km} km
                        </p>
                      </div>
                    )}
                    <div>
                      <p className="text-sm text-gray-600">Dauer</p>
                      <p className="text-2xl font-bold">
                        {parsedData.summary.total_duration_formatted}
                      </p>
                    </div>
                    {parsedData.summary.avg_pace_formatted && (
                      <div>
                        <p className="text-sm text-gray-600">Pace</p>
                        <p className="text-2xl font-bold">
                          {parsedData.summary.avg_pace_formatted} /km
                        </p>
                      </div>
                    )}
                    <div>
                      <p className="text-sm text-gray-600">Ø HF</p>
                      <p className="text-2xl font-bold">
                        {parsedData.summary.avg_hr_bpm} bpm
                      </p>
                    </div>
                  </div>
                </div>
              )}


{/* HR Zones */}
{parsedData.hr_zones && (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
    {/* HR Zones - Overall (always shown) */}
    <div className="bg-gray-50 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">📊 HF-Zonen Gesamt</h3>
      <p className="text-sm text-gray-600 mb-4">
        {parsedData.laps && parsedData.laps.length > 0 
          ? 'Komplette Session (alle Laps)' 
          : 'Komplette Session'}
      </p>
      <div className="space-y-3">
        {Object.entries(parsedData.hr_zones).map(([key, zone]: [string, any]) => (
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span>{zone.label}</span>
              <span className="font-medium">{zone.percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  key.includes('recovery') ? 'bg-green-500' :
                  key.includes('base') ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${zone.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* HR Zones - Working Laps (only for running with laps) */}
    {parsedData.laps && parsedData.laps.length > 0 && (
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">🎯 HF-Zonen Arbeits-Laps</h3>
        <p className="text-sm text-gray-600 mb-4">
          Nur Intervalle/Tempo (ohne Warm-up/Cool-down/Pausen)
        </p>
        {parsedData.hr_zones_working ? (
          <div className="space-y-3">
            {Object.entries(parsedData.hr_zones_working).map(([key, zone]: [string, any]) => (
              <div key={key}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{zone.label}</span>
                  <span className="font-medium">{zone.percentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      key.includes('recovery') ? 'bg-green-500' :
                      key.includes('base') ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${zone.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">📋</div>
            <p className="text-gray-600 text-sm mb-2">Noch nicht berechnet</p>
            <p className="text-gray-500 text-xs">
              Überprüfe die Lap-Typen in der Tabelle unten und klicke dann auf "Arbeits-Laps HF-Zonen berechnen"
            </p>
          </div>
        )}
      </div>
    )}
  </div>
)}

              {/* LAPS TABLE with Classification */}
              {parsedData.laps && parsedData.laps.length > 0 && (
                <div className="bg-white rounded-lg border mb-6 overflow-hidden">
                  <div className="flex justify-between items-center p-4 bg-gray-50 border-b">
                    <h3 className="text-lg font-semibold">
                      Laps ({parsedData.laps.length})
                    </h3>
                    <button
                    onClick={recalculateHRZones}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Arbeits-Laps HF-Zonen berechnen
                  </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">#</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Typ</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Dauer</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Distanz</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Pace</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Ø HF</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Ø Kadenz</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {parsedData.laps.map((lap: Lap) => (
                          <tr key={lap.lap_number} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm font-medium">{lap.lap_number}</td>
                            <td className="px-4 py-3 text-sm">
                              <div className="flex items-center gap-2">
                                <select
                                  value={getEffectiveLapType(lap)}
                                  onChange={(e) => handleLapTypeChange(lap.lap_number, e.target.value as LapType)}
                                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                                >
                                  {lapTypes.map(type => (
                                    <option key={type} value={type}>
                                      {lapTypeLabels[type]}
                                    </option>
                                  ))}
                                </select>
                                {lap.confidence && !lapOverrides[lap.lap_number] && (
                                  <span className={`px-2 py-1 rounded text-xs ${confidenceColors[lap.confidence]}`}>
                                    {lap.confidence}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm">{lap.duration_formatted}</td>
                            <td className="px-4 py-3 text-sm">
                              {lap.distance_km ? `${lap.distance_km} km` : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {lap.avg_hr_bpm ? `${lap.avg_hr_bpm} bpm` : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              {lap.avg_cadence_spm ? `${lap.avg_cadence_spm} spm` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}


            </div>
          )}
        </div>
      </div>
    </div>
  );
}