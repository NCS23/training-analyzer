/**
 * Hook for upload page form state and running workflow handlers.
 */
import { useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { parseTraining, uploadTraining } from '@/api/training';
import type { TrainingParseResponse } from '@/api/training';

type TrainingType = 'running' | 'strength';

// eslint-disable-next-line max-lines-per-function -- consolidated upload form hook
export function useUploadForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const preselect = (location.state as { preselect?: string } | null)?.preselect;

  // Wizard step: 0 = Upload, 1 = Review (running only)
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

  // Running review state
  const [parseResult, setParseResult] = useState<TrainingParseResponse | null>(null);
  const [lapOverrides, setLapOverrides] = useState<Record<number, string>>({});
  const [trainingTypeOverride, setTrainingTypeOverride] = useState<string | null>(null);

  const isRunning = trainingType === 'running';
  const isStrength = trainingType === 'strength';

  // File handlers
  const handleFileUpload = useCallback((files: File[]) => {
    if (files[0]) setCsvFile(files[0]);
  }, []);

  const handleFileRemove = useCallback(() => setCsvFile(null), []);

  // Running: parse CSV → review step
  const handleNext = useCallback(async () => {
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
  }, [csvFile, trainingDate, trainingType, notes]);

  // Running: back to step 0
  const handleBack = useCallback(() => {
    setStep(0);
    setParseResult(null);
    setLapOverrides({});
    setTrainingTypeOverride(null);
    setError(null);
  }, []);

  // Running: create session
  const handleCreateRunning = useCallback(
    async (selectedPlannedId: number | null) => {
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
    },
    [csvFile, trainingDate, trainingType, notes, rpe, lapOverrides, trainingTypeOverride, navigate],
  );

  // Derived
  const laps = parseResult?.data?.laps;
  const effectiveType = trainingTypeOverride || parseResult?.metadata?.training_type_auto;

  return {
    step,
    trainingType,
    setTrainingType,
    trainingDate,
    setTrainingDate,
    csvFile,
    notes,
    setNotes,
    loading,
    creating,
    setCreating,
    error,
    setError,
    rpe,
    setRpe,
    parseResult,
    lapOverrides,
    setLapOverrides,
    trainingTypeOverride,
    setTrainingTypeOverride,
    isRunning,
    isStrength,
    laps,
    effectiveType,
    handleFileUpload,
    handleFileRemove,
    handleNext,
    handleBack,
    handleCreateRunning,
    navigate,
  };
}
