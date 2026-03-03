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
  Minus,
  Moon,
  Pencil,
  Plus,
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

/**
 * Icon colors per training type.
 * Uses NDS primary/secondary palette for cohesive, non-accent differentiation.
 */
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

// --- Card-level session row (compact, for the card itself) ---

function SessionCardRow({ session }: { session: PlannedSession }) {
  const typeKey = getSessionTypeKey(session);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.empty;
  const rd = session.run_details;

  if (session.training_type === 'strength') {
    return (
      <div className="flex items-center gap-1.5">
        <Dumbbell className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
        <span className="text-xs font-medium text-[var(--color-text-base)]">Kraft</span>
      </div>
    );
  }

  if (session.training_type === 'running') {
    const shortLabel = rd?.run_type ? (RUN_TYPE_SHORT[rd.run_type] ?? rd.run_type) : 'Laufen';
    const details: string[] = [];
    if (rd?.target_duration_minutes) details.push(`${rd.target_duration_minutes}′`);
    if (rd?.target_pace_min) {
      details.push(
        rd.target_pace_max ? `${rd.target_pace_min}–${rd.target_pace_max}` : rd.target_pace_min,
      );
    }
    // For intervals/reps/fartlek, show compact segment info
    if (rd?.intervals && rd.intervals.length > 0) {
      const workSegs = rd.intervals.filter((s) => s.type === 'work');
      if (workSegs.length > 0) {
        const first = workSegs[0];
        const dur = first.duration_minutes ? `${first.duration_minutes}′` : '';
        details.push(`${workSegs.length}×${dur}`);
      }
    }

    return (
      <div className="flex items-center gap-1.5 min-w-0">
        <Footprints className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
        <span className="text-xs font-medium text-[var(--color-text-base)] truncate">
          {shortLabel}
        </span>
        {details.length > 0 && (
          <span className="text-[10px] text-[var(--color-text-muted)] truncate">
            {details.join(' · ')}
          </span>
        )}
      </div>
    );
  }

  return null;
}

// --- Read-only detail view (for the dialog) ---

function SessionDetailView({
  session,
  index,
  total,
}: {
  session: PlannedSession;
  index: number;
  total: number;
}) {
  const rd = session.run_details;
  const typeKey = getSessionTypeKey(session);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.easy;

  return (
    <div className="space-y-2">
      {/* Session label when multiple */}
      {total > 1 && (
        <span className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
          Session {index + 1}
        </span>
      )}

      {session.training_type === 'strength' && (
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <Dumbbell className={`w-4 h-4 ${iconColor}`} />
            <span className="text-sm font-medium text-[var(--color-text-base)]">Kraft</span>
          </div>
          {session.notes && (
            <p className="text-xs text-[var(--color-text-muted)] italic pl-5.5">{session.notes}</p>
          )}
        </div>
      )}

      {session.training_type === 'running' && (
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <Footprints className={`w-4 h-4 ${iconColor}`} />
            <span className="text-sm font-medium text-[var(--color-text-base)]">
              {RUN_TYPE_LABELS[rd?.run_type ?? 'easy'] ?? rd?.run_type ?? 'Laufen'}
            </span>
          </div>

          {/* Detail grid */}
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

          {/* Segments */}
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

          {/* Notes */}
          {session.notes && (
            <p className="text-xs text-[var(--color-text-muted)] italic pl-5.5">{session.notes}</p>
          )}
        </div>
      )}
    </div>
  );
}

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

// --- DayDetailDialog (read-only + edit mode via kebab) ---

interface DayDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entry: WeeklyPlanEntry;
  dayLabel: string;
  onUpdate: (updates: Partial<WeeklyPlanEntry>) => void;
}

function DayDetailDialog({ open, onOpenChange, entry, dayLabel, onUpdate }: DayDetailDialogProps) {
  const [isEditing, setIsEditing] = useState(false);

  // Local copy for editing
  const [localSessions, setLocalSessions] = useState<PlannedSession[]>(entry.sessions);
  const [localIsRestDay, setLocalIsRestDay] = useState(entry.is_rest_day);

  // Sync when dialog opens
  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocalSessions(entry.sessions);
    setLocalIsRestDay(entry.is_rest_day);
    setIsEditing(false);
  }
  if (open !== prevOpen) setPrevOpen(open);

  const updateSession = (idx: number, updated: PlannedSession) => {
    setLocalSessions((prev) => prev.map((s, i) => (i === idx ? updated : s)));
  };

  const removeSession = (idx: number) => {
    setLocalSessions((prev) =>
      prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, position: i })),
    );
  };

  const addSession = () => {
    setLocalSessions((prev) => [...prev, { position: prev.length, training_type: 'running' }]);
  };

  const handleTypeChange = (idx: number, val: string) => {
    if (val === 'running') {
      updateSession(idx, { ...localSessions[idx], training_type: 'running', run_details: null });
    } else {
      updateSession(idx, {
        ...localSessions[idx],
        training_type: 'strength',
        run_details: undefined,
      });
    }
  };

  const handleRunTypeChange = (idx: number, runType: string) => {
    const session = localSessions[idx];
    const rd = session.run_details;
    updateSession(idx, {
      ...session,
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: rd?.target_duration_minutes ?? null,
        target_pace_min: rd?.target_pace_min ?? null,
        target_pace_max: rd?.target_pace_max ?? null,
        target_hr_min: rd?.target_hr_min ?? null,
        target_hr_max: rd?.target_hr_max ?? null,
        intervals: rd?.intervals ?? null,
      },
    });
  };

  const handleInitialTypeChange = (val: string) => {
    if (val === 'rest') {
      setLocalSessions([]);
      setLocalIsRestDay(true);
    } else if (val === 'strength') {
      setLocalSessions([{ position: 0, training_type: 'strength' }]);
      setLocalIsRestDay(false);
    } else if (val === 'running') {
      setLocalSessions([{ position: 0, training_type: 'running' }]);
      setLocalIsRestDay(false);
    } else {
      setLocalSessions([]);
      setLocalIsRestDay(false);
    }
  };

  const handleSave = () => {
    onUpdate({ sessions: localSessions, is_rest_day: localIsRestDay });
    setIsEditing(false);
    onOpenChange(false);
  };

  const handleCancel = () => {
    if (isEditing) {
      // Reset to original and go back to read-only
      setLocalSessions(entry.sessions);
      setLocalIsRestDay(entry.is_rest_day);
      setIsEditing(false);
    } else {
      onOpenChange(false);
    }
  };

  const hasSessions = isEditing ? localSessions.length > 0 : entry.sessions.length > 0;
  const sessions = isEditing ? localSessions : entry.sessions;
  const isRestDay = isEditing ? localIsRestDay : entry.is_rest_day;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>{dayLabel}</DialogTitle>
            {!isEditing && (
              <DropdownMenu>
                <DropdownMenuTrigger>
                  <Button variant="ghost" size="sm" aria-label="Optionen">
                    <EllipsisVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem icon={<Pencil />} onSelect={() => setIsEditing(true)}>
                    Bearbeiten
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto">
          {/* --- READ-ONLY MODE --- */}
          {!isEditing && (
            <>
              {hasSessions &&
                sessions.map((session, idx) => (
                  <SessionDetailView
                    key={idx}
                    session={session}
                    index={idx}
                    total={sessions.length}
                  />
                ))}

              {isRestDay && (
                <div className="flex items-center gap-2 py-2">
                  <Moon className="w-4 h-4 text-[var(--color-text-muted)]" />
                  <span className="text-sm text-[var(--color-text-muted)]">Ruhetag</span>
                </div>
              )}

              {!hasSessions && !isRestDay && (
                <p className="text-sm text-[var(--color-text-disabled)] italic py-2">
                  Kein Training geplant
                </p>
              )}
            </>
          )}

          {/* --- EDIT MODE --- */}
          {isEditing && (
            <>
              {!hasSessions && !localIsRestDay && (
                <Select
                  options={INITIAL_TYPE_OPTIONS}
                  value=""
                  onChange={(val) => handleInitialTypeChange(val ?? '')}
                  inputSize="sm"
                  aria-label="Trainingstyp"
                />
              )}

              {localIsRestDay && (
                <Select
                  options={INITIAL_TYPE_OPTIONS}
                  value="rest"
                  onChange={(val) => handleInitialTypeChange(val ?? '')}
                  inputSize="sm"
                  aria-label="Trainingstyp"
                />
              )}

              {hasSessions &&
                localSessions.map((session, idx) => {
                  const rd = session.run_details ?? null;
                  return (
                    <div
                      key={idx}
                      className="rounded-[var(--radius-component-sm)] bg-[var(--color-bg-muted)] p-[var(--spacing-sm)] space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                          Session {idx + 1}
                        </span>
                        {localSessions.length > 1 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeSession(idx)}
                            aria-label="Session entfernen"
                          >
                            <Minus className="w-4 h-4" />
                          </Button>
                        )}
                      </div>

                      <Select
                        options={SESSION_TYPE_OPTIONS}
                        value={session.training_type}
                        onChange={(val) => {
                          if (val) handleTypeChange(idx, val);
                        }}
                        inputSize="sm"
                        aria-label="Trainingstyp"
                      />

                      {session.training_type === 'running' && (
                        <div className="space-y-2">
                          <Select
                            options={RUN_TYPE_OPTIONS}
                            value={rd?.run_type ?? 'easy'}
                            onChange={(val) => {
                              if (val) handleRunTypeChange(idx, val);
                            }}
                            inputSize="sm"
                            aria-label="Lauftyp"
                          />
                          <RunDetailsEditor
                            runDetails={rd}
                            runType={rd?.run_type ?? 'easy'}
                            onChange={(newRd) => {
                              if (newRd) updateSession(idx, { ...session, run_details: newRd });
                            }}
                          />
                        </div>
                      )}

                      <Input
                        type="text"
                        value={session.notes ?? ''}
                        onChange={(e) =>
                          updateSession(idx, { ...session, notes: e.target.value || null })
                        }
                        inputSize="sm"
                        placeholder="Notizen"
                        aria-label="Session Notizen"
                      />
                    </div>
                  );
                })}

              {hasSessions && !localIsRestDay && localSessions.length < MAX_SESSIONS && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={addSession}
                  className="w-full"
                  aria-label="Session hinzufuegen"
                >
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  Session
                </Button>
              )}
            </>
          )}
        </div>

        {/* Footer only in edit mode */}
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

// --- Component ---

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
  const hasSessions = compliance?.actual_sessions && compliance.actual_sessions.length > 0;

  const hasPlanSessions = entry.sessions.length > 0;
  const [showDialog, setShowDialog] = useState(false);
  const dayLabel = `${DAY_LABELS[entry.day_of_week]} ${getDateStr(weekStart, entry.day_of_week)}.`;

  return (
    <>
      <div
        className={[
          'flex flex-col rounded-[var(--radius-component-md)]',
          'bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)]',
          'transition-shadow duration-200 motion-reduce:transition-none',
          isToday ? 'ring-2 ring-[var(--color-border-focus)]' : '',
          'cursor-pointer',
        ].join(' ')}
      >
        {/* Card body — click opens dialog */}
        <button
          type="button"
          onClick={() => setShowDialog(true)}
          className={[
            'p-[var(--spacing-sm)] text-left w-full min-h-[44px]',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--color-border-focus)]',
            'rounded-[var(--radius-component-md)]',
            'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-150 motion-reduce:transition-none',
          ].join(' ')}
          aria-label={`${DAY_LABELS[entry.day_of_week]} Details anzeigen`}
        >
          {/* Day label + date */}
          <div className="flex items-baseline justify-between mb-1.5">
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

          {/* Session rows — compact */}
          <div className="min-h-[28px] flex flex-col gap-1">
            {entry.is_rest_day ? (
              <div className="flex items-center gap-1.5">
                <Moon className={`w-3.5 h-3.5 ${primaryIconColor}`} />
                <span className="text-xs text-[var(--color-text-muted)]">Ruhe</span>
              </div>
            ) : hasPlanSessions ? (
              entry.sessions.map((session, idx) => <SessionCardRow key={idx} session={session} />)
            ) : (
              <span className="text-xs text-[var(--color-text-disabled)]">—</span>
            )}
          </div>
        </button>

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
            {hasSessions &&
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

      {/* Detail / Edit dialog */}
      <DayDetailDialog
        open={showDialog}
        onOpenChange={setShowDialog}
        entry={entry}
        dayLabel={dayLabel}
        onUpdate={onUpdate}
      />
    </>
  );
}
