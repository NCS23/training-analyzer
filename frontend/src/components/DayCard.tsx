import {
  Select,
  Input,
} from '@nordlig/components';
import {
  Check,
  ChevronDown,
  Dumbbell,
  Footprints,
  Moon,
} from 'lucide-react';
import type { RunDetails, WeeklyPlanEntry, ComplianceDayEntry } from '@/api/weekly-plan';

// --- Constants ---

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const RUN_TYPE_SHORT: Record<string, string> = {
  recovery: 'Rec.',
  easy: 'Easy',
  long_run: 'Long',
  tempo: 'Tempo',
  intervals: 'Int.',
};

const RUN_TYPE_OPTIONS = [
  { value: 'recovery', label: 'Regeneration' },
  { value: 'easy', label: 'Lockerer Lauf' },
  { value: 'long_run', label: 'Langer Lauf' },
  { value: 'tempo', label: 'Tempolauf' },
  { value: 'intervals', label: 'Intervalle' },
];

const TYPE_OPTIONS = [
  { value: '', label: 'Leer' },
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
  { value: 'rest', label: 'Ruhetag' },
];

/**
 * Icon colors per training type.
 * Matches DESIGN_REVIEW.md: Quality=Lila, Recovery=Gruen, Longrun=Blau, Kraft=Orange
 * Uses tailwind.config workout palette.
 */
const TYPE_ICON_COLORS: Record<string, string> = {
  easy: 'text-workout-recovery',
  recovery: 'text-workout-recovery',
  tempo: 'text-workout-quality',
  intervals: 'text-workout-quality',
  long_run: 'text-workout-longrun',
  strength: 'text-workout-strength',
  rest: 'text-[var(--color-text-muted)]',
  empty: 'text-[var(--color-text-disabled)]',
};

// --- Helpers ---

function getTypeKey(entry: WeeklyPlanEntry): string {
  if (entry.is_rest_day) return 'rest';
  if (entry.training_type === 'strength') return 'strength';
  if (entry.training_type === 'running' && entry.run_details?.run_type) {
    return entry.run_details.run_type;
  }
  if (entry.training_type === 'running') return 'easy';
  return 'empty';
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
  const typeKey = getTypeKey(entry);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.empty;
  const isPast = isDayInPast(weekStart, entry.day_of_week);
  const isCompleted = compliance?.status === 'completed' || compliance?.status === 'rest_ok';
  const hasSessions = compliance?.actual_sessions && compliance.actual_sessions.length > 0;

  const handleTypeChange = (val: string) => {
    if (val === 'rest') {
      onUpdate({ training_type: null, is_rest_day: true, template_id: null, template_name: null, run_details: null });
    } else if (val === 'strength') {
      onUpdate({ training_type: 'strength', is_rest_day: false, run_details: null });
    } else if (val === 'running') {
      onUpdate({ training_type: 'running', is_rest_day: false });
    } else {
      onUpdate({ training_type: null, is_rest_day: false, template_id: null, template_name: null, notes: null, run_details: null });
    }
  };

  const handleRunTypeChange = (runType: string) => {
    const current = entry.run_details;
    onUpdate({
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: current?.target_duration_minutes ?? null,
        target_pace_min: current?.target_pace_min ?? null,
        target_pace_max: current?.target_pace_max ?? null,
        target_hr_min: current?.target_hr_min ?? null,
        target_hr_max: current?.target_hr_max ?? null,
        intervals: current?.intervals ?? null,
      },
    });
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
          <span className="text-xs text-[var(--color-text-muted)]">
            {getDateStr(weekStart, entry.day_of_week)}.
          </span>
        </div>

        {/* Training type — icon + label */}
        <div className="min-h-[28px] flex items-center">
          {entry.is_rest_day ? (
            <div className="flex items-center gap-1.5">
              <Moon className={`w-3.5 h-3.5 ${iconColor}`} />
              <span className="text-xs text-[var(--color-text-muted)]">Ruhe</span>
            </div>
          ) : entry.training_type === 'strength' ? (
            <div className="flex items-center gap-1.5">
              <Dumbbell className={`w-3.5 h-3.5 ${iconColor}`} />
              <span className="text-xs font-medium text-[var(--color-text-base)]">Kraft</span>
            </div>
          ) : entry.training_type === 'running' ? (
            <div className="flex flex-col gap-0.5">
              <div className="flex items-center gap-1.5">
                <Footprints className={`w-3.5 h-3.5 ${iconColor}`} />
                <span className="text-xs font-medium text-[var(--color-text-base)]">
                  {entry.run_details?.run_type
                    ? RUN_TYPE_SHORT[entry.run_details.run_type] ?? entry.run_details.run_type
                    : 'Laufen'}
                </span>
              </div>
              {entry.run_details?.target_duration_minutes && (
                <span className="text-[10px] text-[var(--color-text-muted)] pl-5">
                  {entry.run_details.target_duration_minutes} min
                </span>
              )}
              {entry.run_details?.target_pace_min && (
                <span className="text-[10px] text-[var(--color-text-muted)] pl-5">
                  {entry.run_details.target_pace_min}
                  {entry.run_details.target_pace_max
                    ? `–${entry.run_details.target_pace_max}`
                    : ''}{' '}
                  /km
                </span>
              )}
            </div>
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
          <Select
            options={TYPE_OPTIONS}
            value={entry.is_rest_day ? 'rest' : entry.training_type ?? ''}
            onChange={(val) => handleTypeChange(val ?? '')}
            inputSize="sm"
            aria-label="Trainingstyp"
          />

          {entry.training_type === 'running' && (
            <>
              <Select
                options={RUN_TYPE_OPTIONS}
                value={entry.run_details?.run_type ?? 'easy'}
                onChange={(val) => {
                  if (val) handleRunTypeChange(val);
                }}
                inputSize="sm"
                aria-label="Lauftyp"
              />

              {entry.run_details?.run_type && (
                <div className="grid grid-cols-1 gap-2.5">
                  <Input
                    type="number"
                    min={5}
                    max={360}
                    value={entry.run_details.target_duration_minutes ?? ''}
                    onChange={(e) => {
                      const val = e.target.value ? Number(e.target.value) : null;
                      onUpdate({
                        run_details: { ...entry.run_details!, target_duration_minutes: val },
                      });
                    }}
                    inputSize="sm"
                    placeholder="Dauer (min)"
                    aria-label="Dauer in Minuten"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      type="text"
                      value={entry.run_details.target_pace_min ?? ''}
                      onChange={(e) =>
                        onUpdate({
                          run_details: {
                            ...entry.run_details!,
                            target_pace_min: e.target.value || null,
                          },
                        })
                      }
                      inputSize="sm"
                      placeholder="Pace von"
                      aria-label="Pace von"
                    />
                    <Input
                      type="text"
                      value={entry.run_details.target_pace_max ?? ''}
                      onChange={(e) =>
                        onUpdate({
                          run_details: {
                            ...entry.run_details!,
                            target_pace_max: e.target.value || null,
                          },
                        })
                      }
                      inputSize="sm"
                      placeholder="Pace bis"
                      aria-label="Pace bis"
                    />
                  </div>
                </div>
              )}
            </>
          )}

          <Input
            type="text"
            value={entry.notes ?? ''}
            onChange={(e) => onUpdate({ notes: e.target.value || null })}
            inputSize="sm"
            placeholder="Notizen"
            aria-label="Notizen"
          />
        </div>
      )}
    </div>
  );
}
