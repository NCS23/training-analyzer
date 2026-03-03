import { useEffect, useState } from 'react';
import {
  Button,
  Input,
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
  Check,
  CircleCheck,
  CircleSlash,
  Clock,
  Dumbbell,
  EllipsisVertical,
  Footprints,
  Gauge,
  GripVertical,
  Heart,
  LayoutTemplate,
  Layers,
  Moon,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react';
import { useDroppable, useDraggable } from '@dnd-kit/core';
import type {
  PlannedSession,
  RunDetails,
  WeeklyPlanEntry,
  ComplianceDayEntry,
} from '@/api/weekly-plan';
import type { Segment } from '@/api/segment';
import { createEmptySegment } from '@/api/segment';
import { lapTypeLabels } from '@/constants/training';
import { getSessionTemplate, type TemplateExercise } from '@/api/session-templates';
import { MoveSessionDialog } from './MoveSessionDialog';
import { RunDetailsEditor } from './RunDetailsEditor';
import { SaveAsTemplateDialog } from './SaveAsTemplateDialog';
import { TemplatePickerDialog } from './TemplatePickerDialog';

/** Convert RunInterval[] to Segment[] for display (fallback for old data without segments). */
function intervalsToDisplaySegments(
  intervals: {
    type: string;
    duration_minutes?: number | null;
    distance_km?: number | null;
    target_pace_min: string | null;
    target_pace_max: string | null;
    target_hr_min: number | null;
    target_hr_max: number | null;
    repeats: number;
    notes?: string | null;
    exercise_name?: string | null;
  }[],
): Segment[] {
  return intervals.map((iv, i) =>
    createEmptySegment(i, {
      segment_type: iv.type as Segment['segment_type'],
      target_duration_minutes: iv.duration_minutes ?? null,
      target_distance_km: iv.distance_km ?? null,
      target_pace_min: iv.target_pace_min,
      target_pace_max: iv.target_pace_max,
      target_hr_min: iv.target_hr_min,
      target_hr_max: iv.target_hr_max,
      repeats: iv.repeats,
      notes: iv.notes ?? null,
      exercise_name: iv.exercise_name ?? null,
    }),
  );
}

// --- Constants ---

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const RUN_TYPE_LABELS: Record<string, string> = {
  recovery: 'Regeneration',
  easy: 'Lockerer Lauf',
  long_run: 'Langer Lauf',
  progression: 'Steigerungslauf',
  tempo: 'Tempolauf',
  intervals: 'Intervalle',
  repetitions: 'Repetitions',
  fartlek: 'Fahrtspiel',
  race: 'Wettkampf',
};

const RUN_TYPE_OPTIONS = [
  { value: 'recovery', label: 'Regeneration' },
  { value: 'easy', label: 'Lockerer Lauf' },
  { value: 'long_run', label: 'Langer Lauf' },
  { value: 'progression', label: 'Steigerungslauf' },
  { value: 'tempo', label: 'Tempolauf' },
  { value: 'intervals', label: 'Intervalle' },
  { value: 'repetitions', label: 'Repetitions' },
  { value: 'fartlek', label: 'Fahrtspiel' },
  { value: 'race', label: 'Wettkampf' },
];

const INITIAL_TYPE_OPTIONS = [
  { value: '', label: 'Leer' },
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
  { value: 'rest', label: 'Ruhetag' },
];

const SESSION_TYPE_OPTIONS = [
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
];

const MAX_SESSIONS = 3;

const TYPE_ICON_COLORS: Record<string, string> = {
  easy: 'text-[var(--color-primary-1-500)]',
  recovery: 'text-[var(--color-primary-1-400)]',
  tempo: 'text-[var(--color-primary-2-500)]',
  intervals: 'text-[var(--color-primary-2-600)]',
  long_run: 'text-[var(--color-primary-1-600)]',
  progression: 'text-[var(--color-primary-1-600)]',
  repetitions: 'text-[var(--color-primary-2-600)]',
  fartlek: 'text-[var(--color-primary-2-400)]',
  race: 'text-[var(--color-primary-2-700)]',
  strength: 'text-[var(--color-secondary-1-500)]',
  rest: 'text-[var(--color-text-muted)]',
  empty: 'text-[var(--color-text-disabled)]',
};

// --- Helpers ---

function getSessionTypeKey(session: PlannedSession): string {
  if (session.training_type === 'strength') return 'strength';
  if (session.training_type === 'running' && session.run_details?.run_type) {
    return session.run_details.run_type;
  }
  if (session.training_type === 'running') return 'easy';
  return 'empty';
}

function getEntryTypeKey(entry: WeeklyPlanEntry): string {
  if (entry.is_rest_day) return 'rest';
  if (entry.sessions.length === 0) return 'empty';
  return getSessionTypeKey(entry.sessions[0]);
}

function getDateStr(weekStart: string, dayOfWeek: number): string {
  const d = new Date(weekStart);
  d.setDate(d.getDate() + dayOfWeek);
  return d.getDate().toString();
}

function isDayInPast(weekStart: string, dayOfWeek: number): boolean {
  const d = new Date(weekStart);
  d.setDate(d.getDate() + dayOfWeek);
  d.setHours(23, 59, 59, 999);
  return d < new Date();
}

// --- Card-level session row (compact, clickable) ---

function SessionCardRow({ session, onClick }: { session: PlannedSession; onClick: () => void }) {
  const typeKey = getSessionTypeKey(session);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.empty;
  const rd = session.run_details;
  const isSkipped = session.status === 'skipped';

  const label =
    session.training_type === 'strength'
      ? 'Kraft'
      : rd?.run_type
        ? (RUN_TYPE_LABELS[rd.run_type] ?? rd.run_type)
        : 'Laufen';

  const details: string[] = [];
  if (session.training_type === 'running') {
    if (rd?.target_duration_minutes) details.push(`${rd.target_duration_minutes}′`);
    if (rd?.target_pace_min) {
      details.push(
        rd.target_pace_max ? `${rd.target_pace_min}–${rd.target_pace_max}` : rd.target_pace_min,
      );
    }
    const segs = rd?.segments ?? rd?.intervals;
    if (segs && segs.length > 0) {
      const workSegs = segs.filter((s) =>
        'segment_type' in s ? s.segment_type === 'work' : s.type === 'work',
      );
      if (workSegs.length > 0) {
        const first = workSegs[0];
        const dur =
          'target_duration_minutes' in first
            ? first.target_duration_minutes
              ? `${first.target_duration_minutes}′`
              : ''
            : first.duration_minutes
              ? `${first.duration_minutes}′`
              : '';
        details.push(`${workSegs.length}×${dur}`);
      }
    }
  }

  const Icon = session.training_type === 'strength' ? Dumbbell : Footprints;

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'flex flex-col min-w-0 w-full text-left min-h-[22px]',
        'rounded-[var(--radius-component-sm)] px-1 -mx-1 py-0.5',
        'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-100 motion-reduce:transition-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
        isSkipped ? 'opacity-50' : '',
      ].join(' ')}
      aria-label={`${label} Details${isSkipped ? ' (übersprungen)' : ''}`}
    >
      <div className="flex items-center gap-1.5">
        <Icon className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
        <span
          className={[
            'text-xs font-medium truncate',
            isSkipped
              ? 'text-[var(--color-text-muted)] line-through'
              : 'text-[var(--color-text-base)]',
          ].join(' ')}
        >
          {label}
        </span>
      </div>
      {details.length > 0 && (
        <span className="text-[10px] text-[var(--color-text-muted)] truncate pl-5">
          {details.join(' · ')}
        </span>
      )}
    </button>
  );
}

// --- DraggableSessionRow (wraps SessionCardRow with drag handle) ---

function DraggableSessionRow({
  session,
  onClick,
  dayOfWeek,
  sessionIdx,
}: {
  session: PlannedSession;
  onClick: () => void;
  dayOfWeek: number;
  sessionIdx: number;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `session-${dayOfWeek}-${sessionIdx}`,
    data: { type: 'session' as const, dayOfWeek, sessionIdx },
  });

  return (
    <div
      ref={setNodeRef}
      className={[
        'flex items-start gap-0.5',
        isDragging ? 'opacity-30' : '',
        'transition-opacity duration-150 motion-reduce:transition-none',
      ].join(' ')}
    >
      <button
        type="button"
        {...attributes}
        {...listeners}
        className={[
          'mt-0.5 p-1 touch-none cursor-grab shrink-0',
          'hidden lg:block',
          'text-[var(--color-text-disabled)] hover:text-[var(--color-text-muted)]',
          'transition-colors duration-100 motion-reduce:transition-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
          'rounded-[var(--radius-component-sm)]',
        ].join(' ')}
        aria-label="Ziehen zum Verschieben"
      >
        <GripVertical className="w-3 h-3" />
      </button>
      <div className="flex-1 min-w-0">
        <SessionCardRow session={session} onClick={onClick} />
      </div>
    </div>
  );
}

// --- DraggableRestDay (wraps rest day button with drag handle) ---

function DraggableRestDay({
  onClick,
  dayOfWeek,
  iconColor,
}: {
  onClick: () => void;
  dayOfWeek: number;
  iconColor: string;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `rest-${dayOfWeek}`,
    data: { type: 'rest' as const, dayOfWeek },
  });

  return (
    <div
      ref={setNodeRef}
      className={[
        'flex items-start gap-0.5',
        isDragging ? 'opacity-30' : '',
        'transition-opacity duration-150 motion-reduce:transition-none',
      ].join(' ')}
    >
      <button
        type="button"
        {...attributes}
        {...listeners}
        className={[
          'mt-0.5 p-1 touch-none cursor-grab shrink-0',
          'hidden lg:block',
          'text-[var(--color-text-disabled)] hover:text-[var(--color-text-muted)]',
          'transition-colors duration-100 motion-reduce:transition-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
          'rounded-[var(--radius-component-sm)]',
        ].join(' ')}
        aria-label="Ruhetag ziehen zum Verschieben"
      >
        <GripVertical className="w-3 h-3" />
      </button>
      <div className="flex-1 min-w-0">
        <button
          type="button"
          onClick={onClick}
          className={[
            'flex items-center gap-1.5 w-full text-left min-h-[22px]',
            'rounded-[var(--radius-component-sm)] px-1 -mx-1',
            'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-100 motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
          ].join(' ')}
          aria-label="Ruhetag ändern"
        >
          <Moon className={`w-4 h-4 ${iconColor}`} />
          <span className="text-xs text-[var(--color-text-muted)]">Ruhe</span>
        </button>
      </div>
    </div>
  );
}

// --- SegmentRow ---

function SegmentRow({ segment }: { segment: Segment }) {
  const label = lapTypeLabels[segment.segment_type] ?? segment.segment_type;
  const parts: string[] = [];
  if (segment.target_duration_minutes) parts.push(`${segment.target_duration_minutes} min`);
  if (segment.target_distance_km) {
    parts.push(
      segment.target_distance_km >= 1
        ? `${segment.target_distance_km} km`
        : `${segment.target_distance_km * 1000}m`,
    );
  }
  if (segment.target_pace_min) {
    parts.push(
      segment.target_pace_max
        ? `${segment.target_pace_min}–${segment.target_pace_max}/km`
        : `${segment.target_pace_min}/km`,
    );
  }
  if (segment.target_hr_min || segment.target_hr_max) {
    parts.push(`${[segment.target_hr_min, segment.target_hr_max].filter(Boolean).join('–')} bpm`);
  }

  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs rounded-[var(--radius-component-sm)] bg-[var(--color-bg-muted)] px-2 py-1">
      {segment.repeats > 1 && (
        <span className="text-[var(--color-text-muted)] font-medium">{segment.repeats}×</span>
      )}
      <span className="font-medium text-[var(--color-text-base)]">{label}</span>
      {segment.exercise_name && (
        <span className="italic text-[var(--color-text-muted)]">{segment.exercise_name}</span>
      )}
      {parts.length > 0 && (
        <span className="text-[var(--color-text-muted)]">{parts.join(' · ')}</span>
      )}
      {segment.notes && (
        <span className="text-[10px] text-[var(--color-text-muted)] basis-full">
          {segment.notes}
        </span>
      )}
    </div>
  );
}

// --- SessionDetailDialog (per-session: read-only + edit via kebab) ---

interface SessionDetailDialogProps {
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

function SessionDetailDialog({
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
  const [templateExercises, setTemplateExercises] = useState<TemplateExercise[]>([]);

  // Sync when dialog opens
  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocal(session);
    setIsEditing(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  // Fetch template exercises when a strength session has a template_id
  useEffect(() => {
    if (!open || !session.template_id || session.training_type !== 'strength') {
      setTemplateExercises([]);
      return;
    }
    getSessionTemplate(session.template_id)
      .then((t) => setTemplateExercises(t.exercises))
      .catch(() => setTemplateExercises([]));
  }, [open, session.template_id, session.training_type]);

  const rd = isEditing ? (local.run_details ?? null) : (session.run_details ?? null);
  const current = isEditing ? local : session;
  const handleTypeChange = (val: string) => {
    if (val === 'running') {
      setLocal({ ...local, training_type: 'running', run_details: null });
    } else {
      setLocal({ ...local, training_type: 'strength', run_details: undefined });
    }
  };

  const handleRunTypeChange = (runType: string) => {
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
        segments: existingRd?.segments,
      },
    });
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
        notes:
          session.training_type === 'strength'
            ? (full.description ?? session.notes)
            : session.notes,
      };
      onUpdate(updated);
    } catch {
      // Silently fail — session stays unchanged
    }
  };

  const sessionLabel =
    current.training_type === 'strength'
      ? 'Kraft'
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
                  {session.training_type === 'running' && session.run_details && (
                    <DropdownMenuItem
                      icon={<BookmarkPlus />}
                      onSelect={() => setShowSaveAsTemplate(true)}
                    >
                      Als Vorlage speichern
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
            <>
              {current.training_type === 'strength' && (
                <div className="space-y-3">
                  {current.template_name && (
                    <p className="text-xs text-[var(--color-text-muted)]">
                      Vorlage:{' '}
                      <span className="font-medium text-[var(--color-text-base)]">
                        {current.template_name}
                      </span>
                    </p>
                  )}

                  {templateExercises.length > 0 && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                        <Dumbbell className="w-3 h-3" />
                        <span>Übungen</span>
                      </div>
                      <div className="space-y-0.5">
                        {templateExercises.map((ex, i) => (
                          <div
                            key={i}
                            className="flex items-baseline justify-between text-xs px-2 py-1 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)]"
                          >
                            <span className="text-[var(--color-text-base)] font-medium truncate mr-2">
                              {ex.name}
                            </span>
                            <span className="text-[var(--color-text-muted)] whitespace-nowrap">
                              {ex.sets}×{ex.reps}
                              {ex.weight_kg != null && ` · ${ex.weight_kg}kg`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {!current.template_id && !current.notes && (
                    <p className="text-xs text-[var(--color-text-disabled)] italic">
                      Keine Vorlage verknüpft
                    </p>
                  )}

                  {current.notes && (
                    <p className="text-xs text-[var(--color-text-muted)] italic">{current.notes}</p>
                  )}
                </div>
              )}

              {current.training_type === 'running' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-xs">
                    <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
                      <Clock className="w-3 h-3" />
                      Dauer
                    </span>
                    <span className="text-[var(--color-text-base)]">
                      {rd?.target_duration_minutes ? `${rd.target_duration_minutes} min` : '—'}
                    </span>

                    <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
                      <Gauge className="w-3 h-3" />
                      Pace
                    </span>
                    <span className="text-[var(--color-text-base)]">
                      {rd?.target_pace_min
                        ? `${rd.target_pace_min}${rd.target_pace_max ? ` – ${rd.target_pace_max}` : ''} /km`
                        : '—'}
                    </span>

                    <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
                      <Heart className="w-3 h-3" />
                      HF
                    </span>
                    <span className="text-[var(--color-text-base)]">
                      {rd?.target_hr_min || rd?.target_hr_max
                        ? `${[rd?.target_hr_min, rd?.target_hr_max].filter(Boolean).join(' – ')} bpm`
                        : '—'}
                    </span>
                  </div>

                  {(() => {
                    const displaySegs =
                      rd?.segments && rd.segments.length > 0
                        ? rd.segments
                        : rd?.intervals && rd.intervals.length > 0
                          ? intervalsToDisplaySegments(rd.intervals)
                          : null;
                    return displaySegs ? (
                      <div className="space-y-1">
                        <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                          <Layers className="w-3 h-3" />
                          <span>Segmente</span>
                        </div>
                        <div className="space-y-0.5">
                          {displaySegs.map((seg, i) => (
                            <SegmentRow key={i} segment={seg} />
                          ))}
                        </div>
                      </div>
                    ) : null;
                  })()}

                  {current.notes && (
                    <p className="text-xs text-[var(--color-text-muted)] italic">{current.notes}</p>
                  )}
                </div>
              )}
            </>
          )}

          {/* --- EDIT MODE --- */}
          {isEditing && (
            <div className="space-y-3">
              <Select
                options={SESSION_TYPE_OPTIONS}
                value={local.training_type}
                onChange={(val) => {
                  if (val) handleTypeChange(val);
                }}
                inputSize="sm"
                aria-label="Trainingstyp"
              />

              {local.training_type === 'running' && (
                <div className="space-y-2">
                  <Select
                    options={RUN_TYPE_OPTIONS}
                    value={local.run_details?.run_type ?? 'easy'}
                    onChange={(val) => {
                      if (val) handleRunTypeChange(val);
                    }}
                    inputSize="sm"
                    aria-label="Lauftyp"
                  />
                  <RunDetailsEditor
                    runDetails={local.run_details ?? null}
                    runType={local.run_details?.run_type ?? 'easy'}
                    onChange={(newRd) => {
                      if (newRd) setLocal({ ...local, run_details: newRd });
                    }}
                  />
                </div>
              )}

              <Input
                type="text"
                value={local.notes ?? ''}
                onChange={(e) => setLocal({ ...local, notes: e.target.value || null })}
                inputSize="sm"
                placeholder="Notizen"
                aria-label="Session Notizen"
              />
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

      {session.run_details && (
        <SaveAsTemplateDialog
          open={showSaveAsTemplate}
          onOpenChange={setShowSaveAsTemplate}
          runDetails={session.run_details}
          defaultName={RUN_TYPE_LABELS[session.run_details.run_type] ?? 'Laufen'}
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
    </Dialog>
  );
}

// --- RestDayDialog ---

interface RestDayDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  notes: string | null;
  dayOfWeek: number;
  onSaveNotes: (notes: string | null) => void;
  onRemoveRestDay: () => void;
  onMoveRestDay?: (targetDay: number) => void;
}

function RestDayDialog({
  open,
  onOpenChange,
  notes,
  dayOfWeek,
  onSaveNotes,
  onRemoveRestDay,
  onMoveRestDay,
}: RestDayDialogProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [localNotes, setLocalNotes] = useState(notes ?? '');
  const [showMoveDialog, setShowMoveDialog] = useState(false);

  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocalNotes(notes ?? '');
    setIsEditing(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  const handleSave = () => {
    onSaveNotes(localNotes.trim() || null);
    setIsEditing(false);
    onOpenChange(false);
  };

  const handleRemove = () => {
    onRemoveRestDay();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>
              <span className="flex items-center gap-2">
                <Moon className="w-4 h-4 text-[var(--color-text-muted)]" />
                Ruhetag
              </span>
            </DialogTitle>
            {!isEditing && (
              <DropdownMenu>
                <DropdownMenuTrigger>
                  <Button variant="ghost" size="sm" aria-label="Ruhetag Optionen">
                    <EllipsisVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem icon={<Pencil />} onSelect={() => setIsEditing(true)}>
                    Bearbeiten
                  </DropdownMenuItem>
                  <DropdownMenuItem icon={<CircleSlash />} onSelect={handleRemove}>
                    Ausfallen lassen
                  </DropdownMenuItem>
                  {onMoveRestDay && (
                    <DropdownMenuItem
                      icon={<ArrowRightLeft />}
                      onSelect={() => setShowMoveDialog(true)}
                    >
                      Verschieben
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem icon={<Trash2 />} onSelect={handleRemove}>
                    Entfernen
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-3">
          {!isEditing && (
            <p className="text-sm text-[var(--color-text-muted)]">
              {notes ? notes : 'Keine Notizen.'}
            </p>
          )}

          {isEditing && (
            <Input
              type="text"
              value={localNotes}
              onChange={(e) => setLocalNotes(e.target.value)}
              inputSize="sm"
              placeholder="Notizen (z.B. Regeneration, Stretching)"
              aria-label="Ruhetag Notizen"
            />
          )}
        </div>

        {isEditing && (
          <DialogFooter>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setLocalNotes(notes ?? '');
                setIsEditing(false);
              }}
            >
              Abbrechen
            </Button>
            <Button size="sm" onClick={handleSave}>
              Speichern
            </Button>
          </DialogFooter>
        )}
      </DialogContent>

      {onMoveRestDay && (
        <MoveSessionDialog
          open={showMoveDialog}
          onOpenChange={setShowMoveDialog}
          currentDay={dayOfWeek}
          sessionLabel="Ruhetag"
          onSelectDay={(targetDay) => {
            setShowMoveDialog(false);
            onOpenChange(false);
            onMoveRestDay(targetDay);
          }}
        />
      )}
    </Dialog>
  );
}

// --- DayCard Component ---

interface DayCardProps {
  entry: WeeklyPlanEntry;
  weekStart: string;
  isToday: boolean;
  compliance: ComplianceDayEntry | undefined;
  showCompliance: boolean;
  onUpdate: (updates: Partial<WeeklyPlanEntry>) => void;
  onNavigateSession: (sessionId: number) => void;
  onMoveSession?: (sessionIdx: number, targetDay: number) => void;
  onMoveRestDay?: (targetDay: number) => void;
}

export function DayCard({
  entry,
  weekStart,
  isToday,
  compliance,
  showCompliance,
  onUpdate,
  onNavigateSession,
  onMoveSession,
  onMoveRestDay,
}: DayCardProps) {
  const { setNodeRef: dropRef, isOver } = useDroppable({
    id: `day-${entry.day_of_week}`,
  });

  const primaryTypeKey = getEntryTypeKey(entry);
  const primaryIconColor = TYPE_ICON_COLORS[primaryTypeKey] ?? TYPE_ICON_COLORS.empty;
  const isPast = isDayInPast(weekStart, entry.day_of_week);
  const isCompleted = compliance?.status === 'completed' || compliance?.status === 'rest_ok';
  const isPartial = compliance?.status === 'partial';
  const hasActualSessions = compliance?.actual_sessions && compliance.actual_sessions.length > 0;

  const hasPlanSessions = entry.sessions.length > 0;
  const [openSessionIdx, setOpenSessionIdx] = useState<number | null>(null);
  const [showRestDayDialog, setShowRestDayDialog] = useState(false);
  const [pendingSessionType, setPendingSessionType] = useState<string | null>(null);

  // --- Session mutation helpers ---
  const updateSession = (idx: number, updated: PlannedSession) => {
    const newSessions = entry.sessions.map((s, i) => (i === idx ? updated : s));
    onUpdate({ sessions: newSessions });
  };

  const removeSession = (idx: number) => {
    const newSessions = entry.sessions
      .filter((_, i) => i !== idx)
      .map((s, i) => ({ ...s, position: i }));
    onUpdate({ sessions: newSessions });
  };

  const addSession = (type: string) => {
    if (type === 'rest') {
      onUpdate({ sessions: [], is_rest_day: true });
    } else if (type === 'running' || type === 'strength') {
      // Open template picker — user can pick a template or "Ohne Vorlage"
      setPendingSessionType(type);
    }
  };

  const addEmptySession = (type: string) => {
    const newSession: PlannedSession = {
      position: entry.sessions.length,
      training_type: type,
    };
    onUpdate({ sessions: [...entry.sessions, newSession], is_rest_day: false });
  };

  const handleTemplatePicked = async (
    template: import('@/api/session-templates').SessionTemplateSummary | null,
  ) => {
    const type = pendingSessionType;
    setPendingSessionType(null);
    if (!type) return;

    if (!template) {
      addEmptySession(type);
      return;
    }

    // Load full template to get run_details
    try {
      const full = await getSessionTemplate(template.id);
      const newSession: PlannedSession = {
        position: entry.sessions.length,
        training_type: type,
        template_id: full.id,
        template_name: full.name,
        run_details: type === 'running' ? (full.run_details ?? null) : undefined,
        notes: type === 'strength' ? (full.description ?? null) : undefined,
      };
      onUpdate({ sessions: [...entry.sessions, newSession], is_rest_day: false });
    } catch {
      // Fallback: create empty session if template load fails
      addEmptySession(type);
    }
  };

  const clearDay = () => {
    onUpdate({ sessions: [], is_rest_day: false, notes: null });
  };

  return (
    <>
      <div
        ref={dropRef}
        className={[
          'flex flex-col rounded-[var(--radius-component-md)]',
          'bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)]',
          'transition-all duration-200 motion-reduce:transition-none',
          isOver
            ? 'ring-2 ring-[var(--color-interactive-primary)] bg-[var(--color-bg-surface-hover)]'
            : isToday
              ? 'ring-2 ring-[var(--color-border-focus)]'
              : '',
        ].join(' ')}
      >
        {/* Day label + date header */}
        <div className="p-[var(--spacing-sm)] pb-0">
          <div className="flex items-baseline justify-between mb-1">
            <span className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
              {DAY_LABELS[entry.day_of_week]}
            </span>
            <div className="flex items-center gap-1">
              {entry.plan_id != null && entry.edited && (
                <Pencil
                  className="w-2.5 h-2.5 text-[var(--color-text-muted)]"
                  aria-label="Manuell bearbeitet"
                />
              )}
              <span className="text-xs text-[var(--color-text-muted)]">
                {getDateStr(weekStart, entry.day_of_week)}.
              </span>
            </div>
          </div>
        </div>

        {/* Session rows — each one clickable */}
        <div className="px-[var(--spacing-sm)] pb-[var(--spacing-xs)] flex flex-col gap-0.5">
          {entry.is_rest_day ? (
            <DraggableRestDay
              onClick={() => setShowRestDayDialog(true)}
              dayOfWeek={entry.day_of_week}
              iconColor={primaryIconColor}
            />
          ) : hasPlanSessions ? (
            entry.sessions.map((session, idx) => (
              <DraggableSessionRow
                key={idx}
                session={session}
                onClick={() => setOpenSessionIdx(idx)}
                dayOfWeek={entry.day_of_week}
                sessionIdx={idx}
              />
            ))
          ) : (
            <span className="text-xs text-[var(--color-text-disabled)] px-1">—</span>
          )}

          {/* Add session / set type — always available when not at max */}
          {!entry.is_rest_day && entry.sessions.length < MAX_SESSIONS && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <button
                  type="button"
                  className={[
                    'flex items-center gap-1 w-full min-h-[22px] px-1 -mx-1',
                    'rounded-[var(--radius-component-sm)]',
                    'text-[10px] text-[var(--color-text-disabled)]',
                    'hover:text-[var(--color-text-muted)] hover:bg-[var(--color-bg-surface-hover)]',
                    'transition-colors duration-100 motion-reduce:transition-none',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
                  ].join(' ')}
                  aria-label="Session hinzufügen"
                >
                  <Plus className="w-3 h-3" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {INITIAL_TYPE_OPTIONS.filter((o) => o.value !== '').map((opt) => (
                  <DropdownMenuItem key={opt.value} onSelect={() => addSession(opt.value)}>
                    {opt.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        {/* Compliance — past days only */}
        {showCompliance && isPast && compliance && compliance.status !== 'empty' && (
          <div className="px-[var(--spacing-xs)] pb-1.5">
            {isCompleted && (
              <div className="flex items-center gap-1 mb-0.5">
                <Check className="w-3 h-3 text-[var(--color-text-success)]" />
                <span className="text-[10px] text-[var(--color-text-success)]">Erledigt</span>
              </div>
            )}
            {isPartial && (
              <div className="flex items-center gap-1 mb-0.5">
                <Check className="w-3 h-3 text-[var(--color-text-warning)]" />
                <span className="text-[10px] text-[var(--color-text-warning)]">Teilweise</span>
              </div>
            )}
            {hasActualSessions &&
              compliance.actual_sessions.map((s) => (
                <button
                  key={s.session_id}
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onNavigateSession(s.session_id);
                  }}
                  className="block text-[10px] text-[var(--color-text-link)] hover:underline mt-0.5 min-h-[22px]"
                >
                  {s.distance_km ? `${s.distance_km.toFixed(1)}km` : ''}
                  {s.pace ? ` ${s.pace}/km` : ''}
                </button>
              ))}
          </div>
        )}
      </div>

      {/* Per-session detail dialog */}
      {openSessionIdx !== null && entry.sessions[openSessionIdx] && (
        <SessionDetailDialog
          open={true}
          onOpenChange={(open) => {
            if (!open) setOpenSessionIdx(null);
          }}
          session={entry.sessions[openSessionIdx]}
          sessionIndex={openSessionIdx}
          dayOfWeek={entry.day_of_week}
          canRemove={true}
          onUpdate={(updated) => updateSession(openSessionIdx, updated)}
          onRemove={() => {
            removeSession(openSessionIdx);
            setOpenSessionIdx(null);
          }}
          onMoveSession={
            onMoveSession
              ? (targetDay) => {
                  onMoveSession(openSessionIdx, targetDay);
                  setOpenSessionIdx(null);
                }
              : undefined
          }
        />
      )}

      {/* Rest day dialog */}
      <RestDayDialog
        open={showRestDayDialog}
        onOpenChange={setShowRestDayDialog}
        notes={entry.notes}
        dayOfWeek={entry.day_of_week}
        onSaveNotes={(notes) => onUpdate({ notes })}
        onRemoveRestDay={clearDay}
        onMoveRestDay={
          onMoveRestDay
            ? (targetDay) => {
                setShowRestDayDialog(false);
                onMoveRestDay(targetDay);
              }
            : undefined
        }
      />

      {/* Template picker dialog */}
      {pendingSessionType && (
        <TemplatePickerDialog
          open={true}
          onOpenChange={(open) => {
            if (!open) setPendingSessionType(null);
          }}
          sessionType={pendingSessionType}
          onSelect={handleTemplatePicked}
        />
      )}
    </>
  );
}
