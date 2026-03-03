import { useState } from 'react';
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
  Check,
  Clock,
  Dumbbell,
  EllipsisVertical,
  Footprints,
  Gauge,
  Heart,
  Layers,
  Moon,
  Pencil,
  Plus,
  Trash2,
} from 'lucide-react';
import type {
  PlannedSession,
  RunDetails,
  RunInterval,
  WeeklyPlanEntry,
  ComplianceDayEntry,
} from '@/api/weekly-plan';
import { lapTypeLabels } from '@/constants/training';
import { RunDetailsEditor } from './RunDetailsEditor';

// --- Constants ---

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const RUN_TYPE_SHORT: Record<string, string> = {
  recovery: 'Rec.',
  easy: 'Easy',
  long_run: 'Long',
  progression: 'Prog.',
  tempo: 'Tempo',
  intervals: 'Int.',
  repetitions: 'Reps',
  fartlek: 'Fartl.',
  race: 'Race',
};

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

function SessionCardRow({
  session,
  onClick,
}: {
  session: PlannedSession;
  onClick: () => void;
}) {
  const typeKey = getSessionTypeKey(session);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.empty;
  const rd = session.run_details;

  const shortLabel =
    session.training_type === 'strength'
      ? 'Kraft'
      : rd?.run_type
        ? (RUN_TYPE_SHORT[rd.run_type] ?? rd.run_type)
        : 'Laufen';

  const details: string[] = [];
  if (session.training_type === 'running') {
    if (rd?.target_duration_minutes) details.push(`${rd.target_duration_minutes}′`);
    if (rd?.target_pace_min) {
      details.push(
        rd.target_pace_max ? `${rd.target_pace_min}–${rd.target_pace_max}` : rd.target_pace_min,
      );
    }
    if (rd?.intervals && rd.intervals.length > 0) {
      const workSegs = rd.intervals.filter((s) => s.type === 'work');
      if (workSegs.length > 0) {
        const first = workSegs[0];
        const dur = first.duration_minutes ? `${first.duration_minutes}′` : '';
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
        'flex items-center gap-1.5 min-w-0 w-full text-left min-h-[22px]',
        'rounded-[var(--radius-component-sm)] px-1 -mx-1',
        'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-100 motion-reduce:transition-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
      ].join(' ')}
      aria-label={`${shortLabel} Details`}
    >
      <Icon className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
      <span className="text-xs font-medium text-[var(--color-text-base)] truncate">
        {shortLabel}
      </span>
      {details.length > 0 && (
        <span className="text-[10px] text-[var(--color-text-muted)] truncate">
          {details.join(' · ')}
        </span>
      )}
    </button>
  );
}

// --- SegmentRow ---

function SegmentRow({ segment }: { segment: RunInterval }) {
  const label = lapTypeLabels[segment.type] ?? segment.type;
  const parts: string[] = [];
  if (segment.duration_minutes) parts.push(`${segment.duration_minutes} min`);
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
    <div className="flex items-center gap-2 text-xs rounded-[var(--radius-component-sm)] bg-[var(--color-bg-muted)] px-2 py-1">
      {segment.repeats > 1 && (
        <span className="text-[var(--color-text-muted)] font-medium">{segment.repeats}×</span>
      )}
      <span className="font-medium text-[var(--color-text-base)]">{label}</span>
      {parts.length > 0 && (
        <span className="text-[var(--color-text-muted)]">{parts.join(' · ')}</span>
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
  canRemove: boolean;
  onUpdate: (updated: PlannedSession) => void;
  onRemove: () => void;
}

function SessionDetailDialog({
  open,
  onOpenChange,
  session,
  sessionIndex,
  canRemove,
  onUpdate,
  onRemove,
}: SessionDetailDialogProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [local, setLocal] = useState<PlannedSession>(session);

  // Sync when dialog opens
  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocal(session);
    setIsEditing(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  const rd = isEditing ? (local.run_details ?? null) : (session.run_details ?? null);
  const current = isEditing ? local : session;
  const typeKey = getSessionTypeKey(current);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.easy;

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

  const sessionLabel =
    current.training_type === 'strength'
      ? 'Kraft'
      : (RUN_TYPE_LABELS[rd?.run_type ?? 'easy'] ?? 'Laufen');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Session {sessionIndex + 1} — {sessionLabel}</DialogTitle>
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
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <Dumbbell className={`w-4 h-4 ${iconColor}`} />
                    <span className="text-sm font-medium text-[var(--color-text-base)]">Kraft</span>
                  </div>
                  {current.notes && (
                    <p className="text-xs text-[var(--color-text-muted)] italic pl-5.5">
                      {current.notes}
                    </p>
                  )}
                </div>
              )}

              {current.training_type === 'running' && (
                <div className="space-y-2">
                  <div className="flex items-center gap-1.5">
                    <Footprints className={`w-4 h-4 ${iconColor}`} />
                    <span className="text-sm font-medium text-[var(--color-text-base)]">
                      {RUN_TYPE_LABELS[rd?.run_type ?? 'easy'] ?? rd?.run_type ?? 'Laufen'}
                    </span>
                  </div>

                  <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 pl-5.5 text-xs">
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

                  {rd?.intervals && rd.intervals.length > 0 && (
                    <div className="pl-5.5 space-y-1">
                      <div className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                        <Layers className="w-3 h-3" />
                        <span>Segmente</span>
                      </div>
                      <div className="space-y-0.5">
                        {rd.intervals.map((seg, i) => (
                          <SegmentRow key={i} segment={seg} />
                        ))}
                      </div>
                    </div>
                  )}

                  {current.notes && (
                    <p className="text-xs text-[var(--color-text-muted)] italic pl-5.5">
                      {current.notes}
                    </p>
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
}

export function DayCard({
  entry,
  weekStart,
  isToday,
  compliance,
  showCompliance,
  onUpdate,
  onNavigateSession,
}: DayCardProps) {
  const primaryTypeKey = getEntryTypeKey(entry);
  const primaryIconColor = TYPE_ICON_COLORS[primaryTypeKey] ?? TYPE_ICON_COLORS.empty;
  const isPast = isDayInPast(weekStart, entry.day_of_week);
  const isCompleted = compliance?.status === 'completed' || compliance?.status === 'rest_ok';
  const isPartial = compliance?.status === 'partial';
  const hasActualSessions =
    compliance?.actual_sessions && compliance.actual_sessions.length > 0;

  const hasPlanSessions = entry.sessions.length > 0;
  const [openSessionIdx, setOpenSessionIdx] = useState<number | null>(null);

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
      const newSession: PlannedSession = {
        position: entry.sessions.length,
        training_type: type,
      };
      onUpdate({ sessions: [...entry.sessions, newSession], is_rest_day: false });
    }
  };

  const clearDay = () => {
    onUpdate({ sessions: [], is_rest_day: false, notes: null });
  };

  return (
    <>
      <div
        className={[
          'flex flex-col rounded-[var(--radius-component-md)]',
          'bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)]',
          'transition-shadow duration-200 motion-reduce:transition-none',
          isToday ? 'ring-2 ring-[var(--color-border-focus)]' : '',
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
            <button
              type="button"
              onClick={clearDay}
              className={[
                'flex items-center gap-1.5 w-full text-left min-h-[22px]',
                'rounded-[var(--radius-component-sm)] px-1 -mx-1',
                'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-100 motion-reduce:transition-none',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
              ].join(' ')}
              aria-label="Ruhetag aendern"
            >
              <Moon className={`w-3.5 h-3.5 ${primaryIconColor}`} />
              <span className="text-xs text-[var(--color-text-muted)]">Ruhe</span>
            </button>
          ) : hasPlanSessions ? (
            entry.sessions.map((session, idx) => (
              <SessionCardRow
                key={idx}
                session={session}
                onClick={() => setOpenSessionIdx(idx)}
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
                  aria-label="Session hinzufuegen"
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
          canRemove={entry.sessions.length > 1}
          onUpdate={(updated) => updateSession(openSessionIdx, updated)}
          onRemove={() => {
            removeSession(openSessionIdx);
            setOpenSessionIdx(null);
          }}
        />
      )}
    </>
  );
}
