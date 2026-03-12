import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  deleteSession,
  updateSessionNotes,
  updateSessionDate,
  updateTrainingType,
  updateLapOverrides,
  updateSessionRpe,
  updatePlannedEntry,
  recalculateSessionZones,
} from '@/api/training';
import type { SessionDetail, LapDetail, HRZone, TrainingTypeInfo } from '@/api/training';
import { getPlannedSessionsForDate } from '@/api/weekly-plan';
import type { PlannedSessionOption } from '@/api/weekly-plan';
import { useToast } from '@nordlig/components';
import { format } from 'date-fns';

export interface SessionEditingState {
  // Notes
  notes: string;
  savingNotes: boolean;
  handleNotesChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;

  // Delete
  showDeleteConfirm: boolean;
  setShowDeleteConfirm: (show: boolean) => void;
  deleting: boolean;
  handleDelete: () => Promise<void>;

  // Training type
  trainingTypeInfo: TrainingTypeInfo | null;
  savingTrainingType: boolean;
  handleTrainingTypeOverride: (newType: string | undefined) => Promise<void>;

  // Date
  savingDate: boolean;
  handleDateChange: (newDate: Date | undefined) => Promise<void>;

  // Planned entry
  plannedSessions: PlannedSessionOption[];
  savingPlannedEntry: boolean;
  handlePlannedEntryChange: (val: string | undefined) => Promise<void>;

  // Edit mode
  isEditing: boolean;
  setIsEditing: (editing: boolean) => void;

  // Lap overrides
  savingLaps: boolean;
  handleLapTypeChange: (lapNumber: number, newType: string | undefined) => Promise<void>;

  // RPE
  localRpe: number | null;
  handleRpeChange: (value: number) => Promise<void>;

  // Recalculate zones
  showRecalcDialog: boolean;
  setShowRecalcDialog: (show: boolean) => void;
  recalcRestingHr: string;
  setRecalcRestingHr: (val: string) => void;
  recalcMaxHr: string;
  setRecalcMaxHr: (val: string) => void;
  recalculating: boolean;
  openRecalcDialog: () => void;
  handleRecalculateZones: () => Promise<void>;
}

interface UseSessionEditingParams {
  sessionId: number;
  session: SessionDetail | null;
  setSession: React.Dispatch<React.SetStateAction<SessionDetail | null>>;
  setError: (error: string | null) => void;
  localLaps: LapDetail[];
  setLocalLaps: React.Dispatch<React.SetStateAction<LapDetail[]>>;
  setWorkingHrZones: React.Dispatch<React.SetStateAction<Record<string, HRZone> | null>>;
}

// eslint-disable-next-line max-lines-per-function -- hook manages all editing state
export function useSessionEditing({
  sessionId,
  session,
  setSession,
  setError,
  localLaps,
  setLocalLaps,
  setWorkingHrZones,
}: UseSessionEditingParams): SessionEditingState {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Notes
  const [notes, setNotes] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);
  const notesTimer = useRef<ReturnType<typeof setTimeout>>(null);

  // Sync notes from session
  useEffect(() => {
    if (session) setNotes(session.notes || '');
  }, [session?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveNotes = useCallback(
    async (value: string) => {
      if (!sessionId) return;
      setSavingNotes(true);
      try {
        await updateSessionNotes(sessionId, value || null);
        toast({ title: 'Notizen gespeichert', variant: 'success' });
      } catch {
        setError('Notizen konnten nicht gespeichert werden.');
      } finally {
        setSavingNotes(false);
      }
    },
    [sessionId, toast, setError],
  );

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setNotes(value);
    if (notesTimer.current) clearTimeout(notesTimer.current);
    notesTimer.current = setTimeout(() => saveNotes(value), 1000);
  };

  // Delete
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!sessionId) return;
    setDeleting(true);
    try {
      await deleteSession(sessionId);
      toast({ title: 'Session gelöscht', variant: 'success' });
      navigate('/sessions', { replace: true });
    } catch {
      setError('Session konnte nicht gelöscht werden.');
      setDeleting(false);
    }
  };

  // Training type
  const [trainingTypeInfo, setTrainingTypeInfo] = useState<TrainingTypeInfo | null>(null);
  const [savingTrainingType, setSavingTrainingType] = useState(false);

  useEffect(() => {
    if (session) setTrainingTypeInfo(session.training_type);
  }, [session?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleTrainingTypeOverride = async (newType: string | undefined) => {
    if (!sessionId || !newType) return;
    setSavingTrainingType(true);
    try {
      const result = await updateTrainingType(sessionId, newType);
      if (result.training_type) {
        setTrainingTypeInfo(result.training_type);
      }
      toast({ title: 'Trainingstyp gespeichert', variant: 'success' });
    } catch {
      setError('Training Type konnte nicht gespeichert werden.');
    } finally {
      setSavingTrainingType(false);
    }
  };

  // Date
  const [savingDate, setSavingDate] = useState(false);

  const handleDateChange = async (newDate: Date | undefined) => {
    if (!sessionId || !newDate || !session) return;
    const dateStr = format(newDate, 'yyyy-MM-dd');
    if (dateStr === session.date) return;
    setSavingDate(true);
    try {
      const result = await updateSessionDate(sessionId, dateStr);
      setSession(result);
      toast({ title: 'Datum gespeichert', variant: 'success' });
    } catch {
      setError('Datum konnte nicht gespeichert werden.');
    } finally {
      setSavingDate(false);
    }
  };

  // Planned entry
  const [plannedSessions, setPlannedSessions] = useState<PlannedSessionOption[]>([]);
  const [savingPlannedEntry, setSavingPlannedEntry] = useState(false);

  // Edit mode
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (!isEditing || !session) return;
    getPlannedSessionsForDate(session.date)
      .then(setPlannedSessions)
      .catch(() => setPlannedSessions([]));
  }, [isEditing, session?.date]); // eslint-disable-line react-hooks/exhaustive-deps

  const handlePlannedEntryChange = async (val: string | undefined) => {
    if (!sessionId || !session) return;
    const newId = val ? parseInt(val) : null;
    if (newId === session.planned_entry_id) return;
    setSavingPlannedEntry(true);
    try {
      const result = await updatePlannedEntry(sessionId, newId);
      setSession(result);
      toast({ title: 'Zuordnung gespeichert', variant: 'success' });
    } catch {
      setError('Zuordnung konnte nicht gespeichert werden.');
    } finally {
      setSavingPlannedEntry(false);
    }
  };

  // Lap overrides
  const [savingLaps, setSavingLaps] = useState(false);

  const handleLapTypeChange = async (lapNumber: number, newType: string | undefined) => {
    if (!sessionId || !newType) return;
    setSavingLaps(true);
    try {
      const overrides = localLaps.map((l) => ({
        lap_number: l.lap_number,
        user_override:
          l.lap_number === lapNumber
            ? newType
            : l.user_override || l.suggested_type || 'unclassified',
      }));
      const result = await updateLapOverrides({ sessionId, overrides });
      if (result.laps) {
        setLocalLaps(result.laps as unknown as LapDetail[]);
      }
      if (result.hr_zones_working) {
        setWorkingHrZones(result.hr_zones_working as Record<string, HRZone>);
      }
      toast({ title: 'Lap-Typ gespeichert', variant: 'success' });
    } catch {
      setError('Lap-Typ konnte nicht gespeichert werden.');
    } finally {
      setSavingLaps(false);
    }
  };

  // RPE
  const [localRpe, setLocalRpe] = useState<number | null>(null);

  const handleRpeChange = useCallback(
    async (value: number) => {
      if (!sessionId) return;
      setLocalRpe(value);
      try {
        await updateSessionRpe(sessionId, value);
        setSession((prev) => (prev ? { ...prev, rpe: value } : prev));
        toast({ title: 'RPE gespeichert', variant: 'success' });
      } catch {
        setError('RPE konnte nicht gespeichert werden.');
      }
    },
    [sessionId, toast, setSession, setError],
  );

  // Recalculate zones
  const [showRecalcDialog, setShowRecalcDialog] = useState(false);
  const [recalcRestingHr, setRecalcRestingHr] = useState('');
  const [recalcMaxHr, setRecalcMaxHr] = useState('');
  const [recalculating, setRecalculating] = useState(false);

  const openRecalcDialog = () => {
    setRecalcRestingHr(session?.athlete_resting_hr?.toString() ?? '');
    setRecalcMaxHr(session?.athlete_max_hr?.toString() ?? '');
    setShowRecalcDialog(true);
  };

  const handleRecalculateZones = async () => {
    if (!sessionId) return;
    const rhr = parseInt(recalcRestingHr, 10);
    const mhr = parseInt(recalcMaxHr, 10);
    if (isNaN(rhr) || isNaN(mhr) || rhr >= mhr) {
      toast({ title: 'Ruhe-HF muss kleiner als Max-HF sein', variant: 'error' });
      return;
    }
    setRecalculating(true);
    try {
      const result = await recalculateSessionZones(sessionId, { resting_hr: rhr, max_hr: mhr });
      if (result.hr_zones) {
        setSession((prev) =>
          prev
            ? {
                ...prev,
                hr_zones: result.hr_zones,
                athlete_resting_hr: result.athlete_resting_hr,
                athlete_max_hr: result.athlete_max_hr,
              }
            : prev,
        );
      }
      setShowRecalcDialog(false);
      toast({ title: 'HF-Zonen aktualisiert', variant: 'success' });
    } catch {
      toast({ title: 'Neuberechnung fehlgeschlagen', variant: 'error' });
    } finally {
      setRecalculating(false);
    }
  };

  return {
    notes,
    savingNotes,
    handleNotesChange,
    showDeleteConfirm,
    setShowDeleteConfirm,
    deleting,
    handleDelete,
    trainingTypeInfo,
    savingTrainingType,
    handleTrainingTypeOverride,
    savingDate,
    handleDateChange,
    plannedSessions,
    savingPlannedEntry,
    handlePlannedEntryChange,
    isEditing,
    setIsEditing,
    savingLaps,
    handleLapTypeChange,
    localRpe,
    handleRpeChange,
    showRecalcDialog,
    setShowRecalcDialog,
    recalcRestingHr,
    setRecalcRestingHr,
    recalcMaxHr,
    setRecalcMaxHr,
    recalculating,
    openRecalcDialog,
    handleRecalculateZones,
  };
}
