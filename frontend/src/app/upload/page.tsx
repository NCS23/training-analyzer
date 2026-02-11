'use client';

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
            {/* File Upload Area */}
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

            {/* Training Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                Trainingsdatum
              </label>
              <input
                type="date"
                value={formData.trainingDate}
                onChange={(e) => setFormData({ ...formData, trainingDate: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Training Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trainingstyp
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, trainingType: 'running', trainingSubtype: '' })}
                  className={`px-4 py-3 rounded-md font-medium transition-colors ${
                    formData.trainingType === 'running'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🏃 Laufen
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, trainingType: 'strength', trainingSubtype: '' })}
                  className={`px-4 py-3 rounded-md font-medium transition-colors ${
                    formData.trainingType === 'strength'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🏋️ Kraft
                </button>
              </div>
            </div>

            {/* Training Subtype */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trainingsart (optional)
              </label>
              <select
                value={formData.trainingSubtype}
                onChange={(e) => setFormData({ ...formData, trainingSubtype: e.target.value as TrainingSubType })}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Wie hast du dich gefühlt? Besonderheiten?"
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !formData.csvFile}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Analysiere...' : 'Training analysieren'}
            </button>
          </form>

          {/* Parsed Data Display */}
          {parsedData && (
            <div className="mt-8 border-t pt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Analyse-Ergebnisse
              </h2>
              
              {/* Summary Stats */}
              {parsedData.summary && (
                <div className="bg-blue-50 rounded-lg p-6 mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Zusammenfassung</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {parsedData.summary.total_distance_km && (
                      <div>
                        <p className="text-sm text-gray-600">Distanz</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {parsedData.summary.total_distance_km} km
                        </p>
                      </div>
                    )}
                    <div>
                      <p className="text-sm text-gray-600">Dauer</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {parsedData.summary.total_duration_formatted}
                      </p>
                    </div>
                    {parsedData.summary.avg_pace_formatted && (
                      <div>
                        <p className="text-sm text-gray-600">Pace</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {parsedData.summary.avg_pace_formatted} min/km
                        </p>
                      </div>
                    )}
                    <div>
                      <p className="text-sm text-gray-600">Ø HF</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {parsedData.summary.avg_hr_bpm} bpm
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* HF Zones */}
              {parsedData.hr_zones && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">HF-Zonen</h3>
                  <div className="space-y-3">
                    {Object.entries(parsedData.hr_zones).map(([key, zone]: [string, any]) => (
                      <div key={key}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-700">{zone.label}</span>
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
              )}

              {/* Raw JSON (Debug) */}
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-900">
                  Rohdaten anzeigen
                </summary>
                <pre className="mt-2 bg-gray-100 p-4 rounded-md text-xs overflow-auto">
                  {JSON.stringify(parsedData, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}