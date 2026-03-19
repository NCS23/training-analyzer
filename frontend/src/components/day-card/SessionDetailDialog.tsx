import { useEffect, useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  Button,
  Input,
  Label,
  Select,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import {
  ArrowRightLeft,
  BookmarkPlus,
  CircleCheck,
  CircleSlash,
  Download,
  EllipsisVertical,
  LayoutTemplate,
  Pencil,
  Trash2,
} from 'lucide-react';
import type { PlannedSession, RunDetails } from '@/api/weekly-plan';
import { exportPlannedSessionFit } from '@/api/weekly-plan';
import { createEmptySegment } from '@/api/segment';
import { getPresetSegments, hasSegmentData } from '@/config/segmentPresets';
import { RUN_TYPE_LABELS, RUN_TYPE_OPTIONS, SESSION_TYPE_OPTIONS } from '@/constants/plan';
import { getSessionTemplate, type TemplateExercise } from '@/api/session-templates';
import { MoveSessionDialog } from '../MoveSessionDialog';
import { RunDetailsEditor } from '../RunDetailsEditor';
import { SaveAsTemplateDialog } from '../SaveAsTemplateDialog';
import { StrengthExerciseEditor } from '../StrengthExerciseEditor';
import { TemplatePickerDialog } from '../TemplatePickerDialog';
import { SessionReadOnlyView } from './SessionReadOnlyView';

export interface SessionDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  session: PlannedSession;
  sessionIndex: number;
  dayOfWeek: number;
  canRemove: boolean;
  onUpdate: (updated: PlannedSession) => void;
  onRemove: () => void;
  onMoveSession?: (targetDay: number) => void;
}

// eslint-disable-next-line complexity, max-lines-per-function -- Dialog mit Read/Edit-Modus, Kebab-Menü, Segment-Bestätigung
export function SessionDetailDialog({
  open,
  onOpenChange,
  session,
  sessionIndex,
  dayOfWeek,
  canRemove,
  onUpdate,
  onRemove,
  onMoveSession,
}: SessionDetailDialogProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [local, setLocal] = useState<PlannedSession>(session);
  const [showSaveAsTemplate, setShowSaveAsTemplate] = useState(false);
  const [showAssignTemplate, setShowAssignTemplate] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [pendingRunType, setPendingRunType] = useState<string | null>(null);
  const [templateExercises, setTemplateExercises] = useState<TemplateExercise[]>([]);

  // Sync when dialog opens
  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocal(session);
    setIsEditing(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  // Fetch template exercises only as fallback for legacy sessions without embedded exercises
  useEffect(() => {
    if (
      !open ||
      !session.template_id ||
      session.training_type !== 'strength' ||
      (session.exercises && session.exercises.length > 0)
    ) {
      setTemplateExercises([]);
      return;
    }
    getSessionTemplate(session.template_id)
      .then((t) => setTemplateExercises(t.exercises))
      .catch(() => setTemplateExercises([]));
  }, [open, session.template_id, session.training_type, session.exercises]);

  const rd = isEditing ? (local.run_details ?? null) : (session.run_details ?? null);
  const current = isEditing ? local : session;
  const handleTypeChange = (val: string) => {
    if (val === 'running') {
      setLocal({ ...local, training_type: 'running', run_details: null, exercises: undefined });
    } else {
      setLocal({ ...local, training_type: 'strength', run_details: undefined });
    }
  };

  const applyRunTypeWithPreset = (runType: string) => {
    const preset = getPresetSegments(runType as RunDetails['run_type']);
    setLocal({
      ...local,
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: null,
        target_pace_min: null,
        target_pace_max: null,
        target_hr_min: null,
        target_hr_max: null,
        intervals: null,
        segments: preset,
      },
    });
  };

  const applyRunTypeKeepSegments = (runType: string) => {
    const existingRd = local.run_details;
    setLocal({
      ...local,
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: existingRd?.target_duration_minutes ?? null,
        target_pace_min: existingRd?.target_pace_min ?? null,
        target_pace_max: existingRd?.target_pace_max ?? null,
        target_hr_min: existingRd?.target_hr_min ?? null,
        target_hr_max: existingRd?.target_hr_max ?? null,
        intervals: existingRd?.intervals ?? null,
        segments: existingRd?.segments ?? [createEmptySegment(0, { segment_type: 'steady' })],
      },
    });
  };

  const handleRunTypeChange = (runType: string) => {
    if (hasSegmentData(local.run_details?.segments)) {
      setPendingRunType(runType);
    } else {
      applyRunTypeWithPreset(runType);
    }
  };

  const handleSave = () => {
    onUpdate(local);
    setIsEditing(false);
    onOpenChange(false);
  };

  const handleCancel = () => {
    if (isEditing) {
      setLocal(session);
      setIsEditing(false);
    } else {
      onOpenChange(false);
    }
  };

  const handleRemove = () => {
    onRemove();
    onOpenChange(false);
  };

  const handleAssignTemplate = async (
    template: import('@/api/session-templates').SessionTemplateSummary | null,
  ) => {
    setShowAssignTemplate(false);
    if (!template) return;

    try {
      const full = await getSessionTemplate(template.id);
      const updated: PlannedSession = {
        ...session,
        template_id: full.id,
        template_name: full.name,
        run_details:
          session.training_type === 'running'
            ? (full.run_details ?? session.run_details)
            : session.run_details,
        exercises:
          session.training_type === 'strength'
            ? full.exercises?.length
              ? full.exercises
              : session.exercises
            : session.exercises,
        notes:
          session.training_type === 'strength'
            ? (full.description ?? session.notes)
            : session.notes,
      };
      onUpdate(updated);
      setLocal(updated);
    } catch {
      // Silently fail — session stays unchanged
    }
  };

  const sessionLabel =
    current.training_type === 'strength'
      ? (current.template_name ?? 'Kraft')
      : (RUN_TYPE_LABELS[rd?.run_type ?? 'easy'] ?? 'Laufen');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>
              Session {sessionIndex + 1} — {sessionLabel}
            </DialogTitle>
            {!isEditing && (
              <DropdownMenu>
                <DropdownMenuTrigger>
                  <Button variant="ghost" size="sm" aria-label="Session Optionen">
                    <EllipsisVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem icon={<Pencil />} onSelect={() => setIsEditing(true)}>
                    Bearbeiten
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    icon={session.status === 'skipped' ? <CircleCheck /> : <CircleSlash />}
                    onSelect={() =>
                      onUpdate({
                        ...session,
                        status: session.status === 'skipped' ? 'active' : 'skipped',
                      })
                    }
                  >
                    {session.status === 'skipped' ? 'Wieder aktivieren' : 'Ausfallen lassen'}
                  </DropdownMenuItem>
                  {onMoveSession && (
                    <DropdownMenuItem
                      icon={<ArrowRightLeft />}
                      onSelect={() => setShowMoveDialog(true)}
                    >
                      Verschieben
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    icon={<LayoutTemplate />}
                    onSelect={() => setShowAssignTemplate(true)}
                  >
                    Vorlage zuweisen
                  </DropdownMenuItem>
                  {((session.training_type === 'running' && session.run_details) ||
                    (session.training_type === 'strength' &&
                      session.exercises &&
                      session.exercises.length > 0)) && (
                    <DropdownMenuItem
                      icon={<BookmarkPlus />}
                      onSelect={() => setShowSaveAsTemplate(true)}
                    >
                      Als Vorlage speichern
                    </DropdownMenuItem>
                  )}
                  {session.training_type === 'running' &&
                    session.id != null &&
                    session.run_details?.segments &&
                    session.run_details.segments.length > 0 && (
                      <DropdownMenuItem
                        icon={<Download />}
                        onSelect={async () => {
                          try {
                            await exportPlannedSessionFit(session.id!);
                          } catch {
                            // Fehler still ignorieren — kein Toast verfuegbar
                          }
                        }}
                      >
                        Als FIT exportieren
                      </DropdownMenuItem>
                    )}
                  {canRemove && (
                    <DropdownMenuItem icon={<Trash2 />} onSelect={handleRemove}>
                      Entfernen
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto">
          {/* --- READ-ONLY --- */}
          {!isEditing && (
            <SessionReadOnlyView
              session={current}
              runDetails={rd}
              templateExercises={templateExercises}
            />
          )}

          {/* --- EDIT MODE --- */}
          {isEditing && (
            <div className="space-y-3">
              <div>
                <Label className="text-xs mb-1">Trainingstyp</Label>
                <Select
                  options={SESSION_TYPE_OPTIONS}
                  value={local.training_type}
                  onChange={(val) => {
                    if (val) handleTypeChange(val);
                  }}
                  inputSize="sm"
                  aria-label="Trainingstyp"
                />
              </div>

              {local.training_type === 'running' && (
                <div className="space-y-2">
                  <div>
                    <Label className="text-xs mb-1">Lauftyp</Label>
                    <Select
                      options={RUN_TYPE_OPTIONS}
                      value={local.run_details?.run_type ?? 'easy'}
                      onChange={(val) => {
                        if (val) handleRunTypeChange(val);
                      }}
                      inputSize="sm"
                      aria-label="Lauftyp"
                    />
                  </div>
                  <RunDetailsEditor
                    runDetails={local.run_details ?? null}
                    runType={local.run_details?.run_type ?? 'easy'}
                    onChange={(newRd) => {
                      if (newRd) setLocal({ ...local, run_details: newRd });
                    }}
                  />
                </div>
              )}

              {local.training_type === 'strength' && (
                <StrengthExerciseEditor
                  exercises={local.exercises ?? null}
                  onChange={(exercises) =>
                    setLocal({ ...local, exercises: exercises ?? undefined })
                  }
                />
              )}

              <div>
                <Label className="text-xs mb-1">Notizen</Label>
                <Input
                  type="text"
                  value={local.notes ?? ''}
                  onChange={(e) => setLocal({ ...local, notes: e.target.value || null })}
                  inputSize="sm"
                  placeholder="Notizen"
                  aria-label="Session Notizen"
                />
              </div>
            </div>
          )}
        </div>

        {isEditing && (
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={handleCancel}>
              Abbrechen
            </Button>
            <Button size="sm" onClick={handleSave}>
              Speichern
            </Button>
          </DialogFooter>
        )}
      </DialogContent>

      {session.training_type === 'running' && session.run_details && (
        <SaveAsTemplateDialog
          open={showSaveAsTemplate}
          onOpenChange={setShowSaveAsTemplate}
          runDetails={session.run_details}
          defaultName={RUN_TYPE_LABELS[session.run_details.run_type] ?? 'Laufen'}
        />
      )}
      {session.training_type === 'strength' && session.exercises && (
        <SaveAsTemplateDialog
          open={showSaveAsTemplate}
          onOpenChange={setShowSaveAsTemplate}
          exercises={session.exercises}
          sessionType="strength"
          defaultName={session.template_name ?? 'Krafttraining'}
        />
      )}

      <TemplatePickerDialog
        open={showAssignTemplate}
        onOpenChange={setShowAssignTemplate}
        sessionType={session.training_type}
        onSelect={handleAssignTemplate}
      />

      {onMoveSession && (
        <MoveSessionDialog
          open={showMoveDialog}
          onOpenChange={setShowMoveDialog}
          currentDay={dayOfWeek}
          sessionLabel={sessionLabel}
          onSelectDay={(targetDay) => {
            setShowMoveDialog(false);
            onOpenChange(false);
            onMoveSession(targetDay);
          }}
        />
      )}

      <AlertDialog
        open={pendingRunType !== null}
        onOpenChange={(alertOpen) => {
          if (!alertOpen) setPendingRunType(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Segmente ersetzen?</AlertDialogTitle>
            <AlertDialogDescription>
              Du hast bereits Segmente konfiguriert. Moechtest du sie mit der Vorlage fuer &ldquo;
              {RUN_TYPE_LABELS[pendingRunType ?? ''] ?? pendingRunType}&rdquo; ersetzen?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                if (pendingRunType) applyRunTypeKeepSegments(pendingRunType);
                setPendingRunType(null);
              }}
            >
              Beibehalten
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingRunType) applyRunTypeWithPreset(pendingRunType);
                setPendingRunType(null);
              }}
            >
              Ersetzen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Dialog>
  );
}
