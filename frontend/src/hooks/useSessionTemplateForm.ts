/**
 * Hook for session template form state, loading, and submission.
 */
import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '@nordlig/components';
import {
  createSessionTemplate,
  getSessionTemplate,
  updateSessionTemplate,
} from '@/api/session-templates';
import type { RunDetails } from '@/api/weekly-plan';
import { createEmptySegment } from '@/api/segment';
import type { ExerciseForm } from '@/utils/exercise-helpers';
import { exerciseFormToApi, apiExerciseToForm } from '@/utils/exercise-helpers';

type TemplateSessionType = 'strength' | 'running';

interface UseSessionTemplateFormOptions {
  templateId: string | undefined;
  exercises: ExerciseForm[];
  setExercises: (exercises: ExerciseForm[]) => void;
}

// eslint-disable-next-line max-lines-per-function -- consolidated template form hook
export function useSessionTemplateForm({
  templateId,
  exercises,
  setExercises,
}: UseSessionTemplateFormOptions) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const isEdit = templateId != null && templateId !== 'new';
  const [editMode, setEditMode] = useState(() => searchParams.get('edit') === 'true');
  const isEditing = !isEdit || editMode;

  // Form fields
  const [templateName, setTemplateName] = useState('');
  const [description, setDescription] = useState('');
  const [sessionType, setSessionType] = useState<TemplateSessionType>('strength');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(isEdit);
  const [error, setError] = useState<string | null>(null);

  // Running state
  const [runType, setRunType] = useState<string>('easy');
  const [runDetails, setRunDetails] = useState<RunDetails | null>(null);

  // Load existing template
  const loadTemplate = useCallback(async () => {
    if (!templateId) return;
    try {
      const tmpl = await getSessionTemplate(Number(templateId));
      setTemplateName(tmpl.name);
      setDescription(tmpl.description ?? '');
      setSessionType(tmpl.session_type as TemplateSessionType);

      if (tmpl.session_type === 'strength') {
        if (tmpl.exercises.length > 0) {
          setExercises(tmpl.exercises.map(apiExerciseToForm));
        }
      } else if (tmpl.session_type === 'running' && tmpl.run_details) {
        setRunType(tmpl.run_details.run_type);
        setRunDetails(tmpl.run_details);
      }
    } catch {
      toast({ title: 'Template nicht gefunden', variant: 'error' });
      navigate('/plan/templates');
    } finally {
      setLoading(false);
    }
  }, [templateId, navigate, toast, setExercises]);

  useEffect(() => {
    if (isEdit) loadTemplate();
  }, [isEdit, loadTemplate]);

  // Run details handlers
  const handleRunTypeChange = useCallback((newType: string | undefined) => {
    if (!newType) return;
    setRunType(newType);
    setRunDetails((prev) =>
      prev ? { ...prev, run_type: newType as RunDetails['run_type'] } : null,
    );
  }, []);

  const handleRunDetailsChange = useCallback(
    (details: RunDetails | null) => {
      if (details) {
        setRunDetails({ ...details, run_type: runType as RunDetails['run_type'] });
      } else {
        setRunDetails(null);
      }
    },
    [runType],
  );

  // Submit
  const handleSubmit = useCallback(async () => {
    if (!templateName.trim()) {
      setError('Template-Name darf nicht leer sein.');
      return;
    }

    if (sessionType === 'strength') {
      const validExercises = exercises.filter((ex) => ex.name.trim());
      if (validExercises.length === 0) {
        setError('Mindestens eine Übung mit Namen erforderlich.');
        return;
      }
    }

    setSubmitting(true);
    setError(null);

    try {
      if (sessionType === 'strength') {
        const validExercises = exercises.filter((ex) => ex.name.trim());
        if (isEdit) {
          await updateSessionTemplate(Number(templateId), {
            name: templateName.trim(),
            description: description.trim() || undefined,
            exercises: validExercises.map(exerciseFormToApi),
          });
        } else {
          await createSessionTemplate({
            name: templateName.trim(),
            description: description.trim() || undefined,
            session_type: 'strength',
            exercises: validExercises.map(exerciseFormToApi),
          });
        }
      } else {
        const details: RunDetails = runDetails ?? {
          run_type: runType as RunDetails['run_type'],
          target_duration_minutes: null,
          target_pace_min: null,
          target_pace_max: null,
          target_hr_min: null,
          target_hr_max: null,
          intervals: null,
          segments: [createEmptySegment(0, { segment_type: 'steady' })],
        };

        if (isEdit) {
          await updateSessionTemplate(Number(templateId), {
            name: templateName.trim(),
            description: description.trim() || undefined,
            run_details: { ...details, run_type: runType as RunDetails['run_type'] },
          });
        } else {
          await createSessionTemplate({
            name: templateName.trim(),
            description: description.trim() || undefined,
            session_type: sessionType,
            run_details: { ...details, run_type: runType as RunDetails['run_type'] },
          });
        }
      }

      toast({ title: isEdit ? 'Template aktualisiert' : 'Template erstellt', variant: 'success' });
      navigate('/plan/templates');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Speichern.');
    } finally {
      setSubmitting(false);
    }
  }, [
    templateName,
    description,
    sessionType,
    exercises,
    runType,
    runDetails,
    isEdit,
    templateId,
    navigate,
    toast,
  ]);

  return {
    isEdit,
    isEditing,
    editMode,
    setEditMode,
    templateName,
    setTemplateName,
    description,
    setDescription,
    sessionType,
    setSessionType,
    submitting,
    loading,
    error,
    runType,
    runDetails,
    handleRunTypeChange,
    handleRunDetailsChange,
    handleSubmit,
    loadTemplate,
    navigate,
  };
}
