import { useCallback } from 'react';
import { Label } from '@nordlig/components';
import type {
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  RunType,
  PhaseType,
} from '@/api/training-plans';

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

type DayType = 'rest' | 'easy' | 'tempo' | 'intervals' | 'long_run' | 'recovery' | 'strength';

const DAY_TYPE_OPTIONS: { value: DayType; label: string; short: string }[] = [
  { value: 'rest', label: 'Ruhetag', short: 'Ruhe' },
  { value: 'easy', label: 'Easy Run', short: 'Easy' },
  { value: 'tempo', label: 'Tempo', short: 'Tempo' },
  { value: 'intervals', label: 'Intervalle', short: 'Int.' },
  { value: 'long_run', label: 'Long Run', short: 'Long' },
  { value: 'recovery', label: 'Recovery', short: 'Rec.' },
  { value: 'strength', label: 'Kraft', short: 'Kraft' },
];

const DAY_TYPE_COLORS: Record<DayType, string> = {
  rest: 'bg-[var(--color-bg-muted)] text-[var(--color-text-muted)]',
  easy: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  tempo: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  intervals: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  long_run: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  recovery: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  strength: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
};

// Default templates per phase type
const PHASE_TYPE_DEFAULTS: Record<PhaseType, DayType[]> = {
  base: ['easy', 'strength', 'easy', 'easy', 'strength', 'long_run', 'rest'],
  build: ['easy', 'strength', 'tempo', 'easy', 'easy', 'long_run', 'rest'],
  peak: ['easy', 'intervals', 'easy', 'tempo', 'strength', 'long_run', 'rest'],
  taper: ['easy', 'tempo', 'rest', 'easy', 'rest', 'easy', 'rest'],
  transition: ['easy', 'rest', 'easy', 'rest', 'strength', 'rest', 'rest'],
};

function getDayType(day: PhaseWeeklyTemplateDayEntry): DayType {
  if (day.is_rest_day) return 'rest';
  if (day.training_type === 'strength') return 'strength';
  if (day.training_type === 'running' && day.run_type) return day.run_type as DayType;
  return 'rest';
}

function dayTypeToEntry(dayOfWeek: number, type: DayType): PhaseWeeklyTemplateDayEntry {
  if (type === 'rest') {
    return { day_of_week: dayOfWeek, training_type: null, is_rest_day: true, run_type: null, template_id: null, notes: null };
  }
  if (type === 'strength') {
    return { day_of_week: dayOfWeek, training_type: 'strength', is_rest_day: false, run_type: null, template_id: null, notes: null };
  }
  return {
    day_of_week: dayOfWeek,
    training_type: 'running',
    is_rest_day: false,
    run_type: type as RunType,
    template_id: null,
    notes: null,
  };
}

function createDefaultTemplate(phaseType: PhaseType): PhaseWeeklyTemplate {
  const types = PHASE_TYPE_DEFAULTS[phaseType];
  return {
    days: types.map((type, i) => dayTypeToEntry(i, type)),
  };
}

interface Props {
  template: PhaseWeeklyTemplate | null;
  phaseType: PhaseType;
  onChange: (template: PhaseWeeklyTemplate) => void;
}

export function PhaseWeeklyTemplateEditor({ template, phaseType, onChange }: Props) {
  const currentTemplate = template ?? createDefaultTemplate(phaseType);

  const handleDayChange = useCallback(
    (dayIndex: number, newType: DayType) => {
      const newDays = currentTemplate.days.map((day, i) =>
        i === dayIndex ? dayTypeToEntry(dayIndex, newType) : day,
      );
      onChange({ days: newDays });
    },
    [currentTemplate, onChange],
  );

  const handleLoadDefaults = useCallback(() => {
    onChange(createDefaultTemplate(phaseType));
  }, [phaseType, onChange]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>Wochen-Template</Label>
        <button
          type="button"
          onClick={handleLoadDefaults}
          className="text-xs text-[var(--color-text-link)] hover:underline underline-offset-2 min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          Standard laden
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {DAY_LABELS.map((label, i) => (
          <div key={label} className="text-center">
            <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
              {label}
            </span>
            <button
              type="button"
              onClick={() => {
                const current = getDayType(currentTemplate.days[i]);
                const currentIdx = DAY_TYPE_OPTIONS.findIndex((o) => o.value === current);
                const nextIdx = (currentIdx + 1) % DAY_TYPE_OPTIONS.length;
                handleDayChange(i, DAY_TYPE_OPTIONS[nextIdx].value);
              }}
              className={`
                w-full mt-0.5 py-1.5 px-0.5 rounded-[var(--radius-component-sm)]
                text-[11px] font-medium leading-tight text-center
                transition-colors motion-reduce:transition-none
                min-h-[44px] flex items-center justify-center
                ${DAY_TYPE_COLORS[getDayType(currentTemplate.days[i])]}
                hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]
              `}
              title={DAY_TYPE_OPTIONS.find((o) => o.value === getDayType(currentTemplate.days[i]))?.label}
            >
              {DAY_TYPE_OPTIONS.find((o) => o.value === getDayType(currentTemplate.days[i]))?.short}
            </button>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-[var(--color-text-muted)]">
        Klick zum Wechseln: Ruhe → Easy → Tempo → Intervalle → Long Run → Recovery → Kraft
      </p>
    </div>
  );
}
