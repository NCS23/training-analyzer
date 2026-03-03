import { Button, Input, Select } from '@nordlig/components';
import { Check, ChevronDown, Dumbbell, Footprints, Minus, Moon, Pencil, Plus } from 'lucide-react';
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

// --- SessionEditor (inline) ---

interface SessionEditorProps {
  session: PlannedSession;
  canRemove: boolean;
  onUpdate: (updated: PlannedSession) => void;
  onRemove: () => void;
}

function SessionEditor({ session, canRemove, onUpdate, onRemove }: SessionEditorProps) {
  const runDetails = session.run_details ?? null;

  const handleTypeChange = (val: string) => {
    if (val === 'running') {
      onUpdate({ ...session, training_type: 'running', run_details: null });
    } else {
      onUpdate({ ...session, training_type: 'strength', run_details: undefined });
    }
  };

  const handleRunTypeChange = (runType: string) => {
    onUpdate({
      ...session,
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: runDetails?.target_duration_minutes ?? null,
        target_pace_min: runDetails?.target_pace_min ?? null,
        target_pace_max: runDetails?.target_pace_max ?? null,
        target_hr_min: runDetails?.target_hr_min ?? null,
        target_hr_max: runDetails?.target_hr_max ?? null,
        intervals: runDetails?.intervals ?? null,
      },
    });
  };

  const updateRunDetails = (rd: RunDetails) => {
    onUpdate({ ...session, run_details: rd });
  };

  return (
    <div className="space-y-2">
      {/* Session header: label + type + remove */}
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <Select
            options={SESSION_TYPE_OPTIONS}
            value={session.training_type}
            onChange={(val) => {
              if (val) handleTypeChange(val);
            }}
            inputSize="sm"
            aria-label="Trainingstyp"
          />
        </div>
        {canRemove && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRemove}
            aria-label="Session entfernen"
            className="shrink-0"
          >
            <Minus className="w-4 h-4" />
          </Button>
        )}
      </div>

      {session.training_type === 'running' && (
        <div className="space-y-2">
          <Select
            options={RUN_TYPE_OPTIONS}
            value={runDetails?.run_type ?? 'easy'}
            onChange={(val) => {
              if (val) handleRunTypeChange(val);
            }}
            inputSize="sm"
            aria-label="Lauftyp"
          />
          <RunDetailsEditor
            runDetails={runDetails}
            runType={runDetails?.run_type ?? 'easy'}
            onChange={(rd) => {
              if (rd) updateRunDetails(rd);
            }}
          />
        </div>
      )}

      {/* Session notes */}
      <Input
        type="text"
        value={session.notes ?? ''}
        onChange={(e) => onUpdate({ ...session, notes: e.target.value || null })}
        inputSize="sm"
        placeholder="Notizen"
        aria-label="Session Notizen"
      />
    </div>
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

  const addSession = () => {
    const newSession: PlannedSession = {
      position: entry.sessions.length,
      training_type: 'running',
    };
    onUpdate({ sessions: [...entry.sessions, newSession] });
  };

  // --- Initial type select (when no sessions) ---

  const handleInitialTypeChange = (val: string) => {
    if (val === 'rest') {
      onUpdate({ sessions: [], is_rest_day: true });
    } else if (val === 'strength') {
      onUpdate({
        sessions: [{ position: 0, training_type: 'strength' }],
        is_rest_day: false,
      });
    } else if (val === 'running') {
      onUpdate({
        sessions: [{ position: 0, training_type: 'running' }],
        is_rest_day: false,
      });
    } else {
      onUpdate({ sessions: [], is_rest_day: false, notes: null });
    }
  };

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

      {/* Expanded editor */}
      {isExpanded && (
        <div className="px-[var(--spacing-sm)] pb-[var(--spacing-sm)] pt-[var(--spacing-sm)] border-t border-[var(--color-border-muted)] space-y-3">
          {/* No sessions and not rest day → initial type selector */}
          {!hasPlanSessions && !entry.is_rest_day && (
            <Select
              options={INITIAL_TYPE_OPTIONS}
              value=""
              onChange={(val) => handleInitialTypeChange(val ?? '')}
              inputSize="sm"
              aria-label="Trainingstyp"
            />
          )}

          {/* Rest day → show selector to switch back */}
          {entry.is_rest_day && (
            <Select
              options={INITIAL_TYPE_OPTIONS}
              value="rest"
              onChange={(val) => handleInitialTypeChange(val ?? '')}
              inputSize="sm"
              aria-label="Trainingstyp"
            />
          )}

          {/* Sessions list */}
          {hasPlanSessions &&
            entry.sessions.map((session, idx) => (
              <div
                key={idx}
                className="rounded-[var(--radius-component-sm)] bg-[var(--color-bg-muted)] p-[var(--spacing-xs)] space-y-2"
              >
                <span className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                  Session {idx + 1}
                </span>
                <SessionEditor
                  session={session}
                  canRemove={entry.sessions.length > 1}
                  onUpdate={(updated) => updateSession(idx, updated)}
                  onRemove={() => removeSession(idx)}
                />
              </div>
            ))}

          {/* Add Session button */}
          {hasPlanSessions && !entry.is_rest_day && entry.sessions.length < MAX_SESSIONS && (
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
      )}
    </div>
  );
}
