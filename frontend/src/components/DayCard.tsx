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
} from '@nordlig/components';
import {
  Check,
  ChevronDown,
  Clock,
  Dumbbell,
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
  WeeklyPlanEntry,
  ComplianceDayEntry,
} from '@/api/weekly-plan';
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

// --- SessionSummary (read-only, compact) ---

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

function SessionSummary({ session }: { session: PlannedSession }) {
  const rd = session.run_details;

  if (session.training_type === 'strength') {
    return (
      <div className="flex items-center gap-1.5">
        <Dumbbell className="w-3.5 h-3.5 text-[var(--color-secondary-1-500)]" />
        <span className="text-xs font-medium text-[var(--color-text-base)]">Kraft</span>
        {session.notes && (
          <span className="text-[10px] text-[var(--color-text-muted)] truncate ml-1">
            — {session.notes}
          </span>
        )}
      </div>
    );
  }

  if (session.training_type === 'running') {
    const typeKey = rd?.run_type ?? 'easy';
    const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.easy;
    const hasDetails =
      rd?.target_duration_minutes || rd?.target_pace_min || rd?.target_hr_min || rd?.target_hr_max;
    const segmentCount = rd?.intervals?.length ?? 0;

    return (
      <div className="space-y-0.5">
        <div className="flex items-center gap-1.5">
          <Footprints className={`w-3.5 h-3.5 ${iconColor}`} />
          <span className="text-xs font-medium text-[var(--color-text-base)]">
            {RUN_TYPE_LABELS[typeKey] ?? typeKey}
          </span>
        </div>
        {(hasDetails || segmentCount > 0) && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 pl-5">
            {rd?.target_duration_minutes && (
              <span className="flex items-center gap-0.5 text-[10px] text-[var(--color-text-muted)]">
                <Clock className="w-2.5 h-2.5" />
                {rd.target_duration_minutes} min
              </span>
            )}
            {rd?.target_pace_min && (
              <span className="flex items-center gap-0.5 text-[10px] text-[var(--color-text-muted)]">
                <Gauge className="w-2.5 h-2.5" />
                {rd.target_pace_min}
                {rd.target_pace_max ? `–${rd.target_pace_max}` : ''}/km
              </span>
            )}
            {(rd?.target_hr_min || rd?.target_hr_max) && (
              <span className="flex items-center gap-0.5 text-[10px] text-[var(--color-text-muted)]">
                <Heart className="w-2.5 h-2.5" />
                {[rd?.target_hr_min, rd?.target_hr_max].filter(Boolean).join('–')} bpm
              </span>
            )}
            {segmentCount > 0 && (
              <span className="flex items-center gap-0.5 text-[10px] text-[var(--color-text-muted)]">
                <Layers className="w-2.5 h-2.5" />
                {segmentCount} Seg.
              </span>
            )}
          </div>
        )}
        {session.notes && (
          <p className="text-[10px] text-[var(--color-text-muted)] italic pl-5 truncate">
            {session.notes}
          </p>
        )}
      </div>
    );
  }

  return null;
}

// --- SessionEditDialog ---

interface SessionEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessions: PlannedSession[];
  isRestDay: boolean;
  dayLabel: string;
  onUpdate: (updates: Partial<WeeklyPlanEntry>) => void;
}

function SessionEditDialog({
  open,
  onOpenChange,
  sessions,
  isRestDay,
  dayLabel,
  onUpdate,
}: SessionEditDialogProps) {
  // Local copy for editing — commit on save
  const [localSessions, setLocalSessions] = useState<PlannedSession[]>(sessions);
  const [localIsRestDay, setLocalIsRestDay] = useState(isRestDay);

  // Sync local state when dialog opens with new data
  const [prevOpen, setPrevOpen] = useState(false);
  if (open && !prevOpen) {
    setLocalSessions(sessions);
    setLocalIsRestDay(isRestDay);
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
    onOpenChange(false);
  };

  const hasSessions = localSessions.length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{dayLabel} — Training bearbeiten</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto">
          {/* No sessions and not rest day → initial type selector */}
          {!hasSessions && !localIsRestDay && (
            <Select
              options={INITIAL_TYPE_OPTIONS}
              value=""
              onChange={(val) => handleInitialTypeChange(val ?? '')}
              inputSize="sm"
              aria-label="Trainingstyp"
            />
          )}

          {/* Rest day → show selector to switch back */}
          {localIsRestDay && (
            <Select
              options={INITIAL_TYPE_OPTIONS}
              value="rest"
              onChange={(val) => handleInitialTypeChange(val ?? '')}
              inputSize="sm"
              aria-label="Trainingstyp"
            />
          )}

          {/* Sessions */}
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

          {/* Add session */}
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
        </div>

        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
            Abbrechen
          </Button>
          <Button size="sm" onClick={handleSave}>
            Speichern
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// --- SessionHeader (collapsed session display) ---

function SessionHeaderRow({ session }: { session: PlannedSession }) {
  const typeKey = getSessionTypeKey(session);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.empty;
  const runDetails = session.run_details ?? null;

  if (session.training_type === 'strength') {
    return (
      <div className="flex items-center gap-1.5">
        <Dumbbell className={`w-3.5 h-3.5 ${iconColor}`} />
        <span className="text-xs font-medium text-[var(--color-text-base)]">Kraft</span>
      </div>
    );
  }

  if (session.training_type === 'running') {
    return (
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <Footprints className={`w-3.5 h-3.5 ${iconColor}`} />
          <span className="text-xs font-medium text-[var(--color-text-base)]">
            {runDetails?.run_type
              ? (RUN_TYPE_SHORT[runDetails.run_type] ?? runDetails.run_type)
              : 'Laufen'}
          </span>
        </div>
        {runDetails?.target_duration_minutes && (
          <span className="text-[10px] text-[var(--color-text-muted)] pl-5">
            {runDetails.target_duration_minutes} min
          </span>
        )}
        {runDetails?.target_pace_min && (
          <span className="text-[10px] text-[var(--color-text-muted)] pl-5">
            {runDetails.target_pace_min}
            {runDetails.target_pace_max ? `–${runDetails.target_pace_max}` : ''} /km
          </span>
        )}
      </div>
    );
  }

  return null;
}

// --- Component ---

interface DayCardProps {
  entry: WeeklyPlanEntry;
  weekStart: string;
  isToday: boolean;
  isExpanded: boolean;
  compliance: ComplianceDayEntry | undefined;
  showCompliance: boolean;
  onToggleExpand: () => void;
  onUpdate: (updates: Partial<WeeklyPlanEntry>) => void;
  onNavigateSession: (sessionId: number) => void;
}

export function DayCard({
  entry,
  weekStart,
  isToday,
  isExpanded,
  compliance,
  showCompliance,
  onToggleExpand,
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
  const [showEditDialog, setShowEditDialog] = useState(false);
  const dayLabel = `${DAY_LABELS[entry.day_of_week]} ${getDateStr(weekStart, entry.day_of_week)}.`;

  return (
    <div
      className={[
        'flex flex-col rounded-[var(--radius-component-md)]',
        'bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)]',
        'transition-shadow duration-200 motion-reduce:transition-none',
        isToday ? 'ring-2 ring-[var(--color-border-focus)]' : '',
        isExpanded ? 'shadow-[var(--shadow-elevated)]' : '',
      ].join(' ')}
    >
      {/* Compact header — always visible */}
      <button
        type="button"
        onClick={onToggleExpand}
        className={[
          'p-[var(--spacing-sm)] text-left w-full min-h-[44px]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--color-border-focus)]',
          'rounded-t-[var(--radius-component-md)]',
          !isExpanded ? 'rounded-b-[var(--radius-component-md)]' : '',
          'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-150 motion-reduce:transition-none',
        ].join(' ')}
        aria-expanded={isExpanded}
        aria-label={`${DAY_LABELS[entry.day_of_week]} bearbeiten`}
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

        {/* Training type — icon + label for all sessions */}
        <div className="min-h-[28px] flex flex-col gap-1">
          {entry.is_rest_day ? (
            <div className="flex items-center gap-1.5">
              <Moon className={`w-3.5 h-3.5 ${primaryIconColor}`} />
              <span className="text-xs text-[var(--color-text-muted)]">Ruhe</span>
            </div>
          ) : hasPlanSessions ? (
            entry.sessions.map((session, idx) => <SessionHeaderRow key={idx} session={session} />)
          ) : (
            <span className="text-xs text-[var(--color-text-disabled)]">—</span>
          )}
        </div>

        {/* Edit affordance */}
        <div className="flex justify-center mt-1.5">
          <ChevronDown
            className={[
              'w-3.5 h-3.5 text-[var(--color-text-disabled)]',
              'transition-transform duration-150 motion-reduce:transition-none',
              isExpanded ? 'rotate-180' : '',
            ].join(' ')}
          />
        </div>
      </button>

      {/* Compliance — past days only, subtle (Hygge: nie bestrafend) */}
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

      {/* Expanded detail view (read-only) */}
      {isExpanded && (
        <div className="px-[var(--spacing-sm)] pb-[var(--spacing-sm)] pt-[var(--spacing-sm)] border-t border-[var(--color-border-muted)] space-y-2">
          {/* Sessions read-only summary */}
          {hasPlanSessions &&
            entry.sessions.map((session, idx) => (
              <div key={idx}>
                {entry.sessions.length > 1 && (
                  <span className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                    Session {idx + 1}
                  </span>
                )}
                <SessionSummary session={session} />
              </div>
            ))}

          {/* Rest day or empty — show current state */}
          {!hasPlanSessions && entry.is_rest_day && (
            <div className="flex items-center gap-1.5">
              <Moon className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
              <span className="text-xs text-[var(--color-text-muted)]">Ruhetag</span>
            </div>
          )}

          {!hasPlanSessions && !entry.is_rest_day && (
            <p className="text-xs text-[var(--color-text-disabled)] italic">
              Kein Training geplant
            </p>
          )}

          {/* Edit button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowEditDialog(true)}
            className="w-full"
            aria-label="Training bearbeiten"
          >
            <Pencil className="w-3.5 h-3.5 mr-1" />
            Bearbeiten
          </Button>
        </div>
      )}

      {/* Edit dialog */}
      <SessionEditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        sessions={entry.sessions}
        isRestDay={entry.is_rest_day}
        dayLabel={dayLabel}
        onUpdate={onUpdate}
      />
    </div>
  );
}
