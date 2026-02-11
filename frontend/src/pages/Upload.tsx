import { useState } from 'react';
import { Upload, FileText, Calendar, Activity } from 'lucide-react';

type TrainingType = 'running' | 'strength';
type TrainingSubType = 'interval' | 'tempo' | 'longrun' | 'recovery' | 'knee_dominant' | 'hip_dominant';

interface UploadFormData {
  csvFile: File | null;
  trainingDate: string;
  trainingType: TrainingType;
  trainingSubtype: TrainingSubType | '';
  notes: string;
}

interface ParsedData {
  laps?: any[];
  summary?: any;
  hr_zones?: any;
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
      } else {
        setError(result.errors?.join(', ') || 'Upload fehlgeschlagen');
      }
    } catch (err) {
      setError('Netzwerkfehler: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const runningSubtypes: TrainingSubType[] = ['interval', 'tempo', 'longrun', 'recovery'];
  const strengthSubtypes: TrainingSubType[] = ['knee_dominant', 'hip_dominant'];

  const currentSubtypes = formData.trainingType === 'running' 
    ? runningSubtypes 
    : strengthSubtypes;

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
    <h2 className="text-2xl font-bold mb-4">📊 Analyse-Ergebnisse</h2>
    
    {parsedData.summary && (
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 mb-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Zusammenfassung</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {parsedData.summary.total_distance_km && (
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Distanz</p>
              <p className="text-2xl font-bold text-gray-900">
                {parsedData.summary.total_distance_km} <span className="text-lg text-gray-600">km</span>
              </p>
            </div>
          )}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Dauer</p>
            <p className="text-2xl font-bold text-gray-900">
              {parsedData.summary.total_duration_formatted}
            </p>
          </div>
          {parsedData.summary.avg_pace_formatted && (
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Pace</p>
              <p className="text-2xl font-bold text-gray-900">
                {parsedData.summary.avg_pace_formatted} <span className="text-lg text-gray-600">/km</span>
              </p>
            </div>
          )}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Ø HF</p>
            <p className="text-2xl font-bold text-gray-900">
              {parsedData.summary.avg_hr_bpm} <span className="text-lg text-gray-600">bpm</span>
            </p>
          </div>
        </div>
      </div>
    )}

    {/* LAPS TABLE */}
    {parsedData.laps && parsedData.laps.length > 0 && (
      <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden border border-gray-200">
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">
            🏃 Laps ({parsedData.laps.length})
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">#</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Dauer</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Distanz</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Pace</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Ø HF</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Ø Kadenz</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {parsedData.laps.map((lap: any, index: number) => (
                <tr 
                  key={lap.lap_number} 
                  className={`hover:bg-blue-50 transition-colors ${
                    index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-bold text-sm">
                      {lap.lap_number}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {lap.duration_formatted}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {lap.distance_km ? `${lap.distance_km} km` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {lap.pace_formatted ? `${lap.pace_formatted} /km` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {lap.avg_hr_bpm ? `${lap.avg_hr_bpm} bpm` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {lap.avg_cadence_spm ? `${lap.avg_cadence_spm} spm` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}

    {/* HF-ZONEN */}
    {parsedData.hr_zones && (
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">💓 HF-Zonen</h3>
        <div className="space-y-4">
          {Object.entries(parsedData.hr_zones).map(([key, zone]: [string, any]) => (
            <div key={key}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">{zone.label}</span>
                <span className="text-sm font-bold text-gray-900">{zone.percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
                <div
                  className={`h-4 rounded-full transition-all duration-500 ${
                    key.includes('recovery') ? 'bg-gradient-to-r from-green-400 to-green-600' :
                    key.includes('base') ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' :
                    'bg-gradient-to-r from-red-400 to-red-600'
                  }`}
                  style={{ width: `${zone.percentage}%` }}
                />
              </div>
            </div>
          ))}
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