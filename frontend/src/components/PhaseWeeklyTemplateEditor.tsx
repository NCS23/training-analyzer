import { useState, useCallback } from 'react';
import { Label } from '@nordlig/components';
import { ChevronDown } from 'lucide-react';
import type {
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  PhaseWeeklyTemplates,
  RunType,
  PhaseType,
} from '@/api/training-plans';
import type { RunDetails } from '@/api/weekly-plan';
import { RunDetailsEditor } from './RunDetailsEditor';

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

type DayType =
  | 'rest'
  | 'easy'
  | 'tempo'
  | 'intervals'
  | 'progression'
  | 'fartlek'
  | 'long_run'
  | 'recovery'
  | 'strength';

const DAY_TYPE_OPTIONS: { value: DayType; label: string; short: string }[] = [
  { value: 'rest', label: 'Ruhetag', short: 'Ruhe' },
  { value: 'easy', label: 'Easy Run', short: 'Easy' },
  { value: 'tempo', label: 'Tempo', short: 'Tempo' },
  { value: 'intervals', label: 'Intervalle', short: 'Int.' },
  { value: 'progression', label: 'Progression', short: 'Prog.' },
  { value: 'fartlek', label: 'Fartlek', short: 'Fartl.' },
  { value: 'long_run', label: 'Long Run', short: 'Long' },
  { value: 'recovery', label: 'Recovery', short: 'Rec.' },
  { value: 'strength', label: 'Kraft', short: 'Kraft' },
];

const DAY_TYPE_COLORS: Record<DayType, string> = {
  rest: 'bg-[var(--color-bg-muted)] text-[var(--color-text-muted)]',
  easy: 'bg-[var(--color-primary-1-50)] text-[var(--color-primary-1-600)]',
  tempo: 'bg-[var(--color-primary-2-50)] text-[var(--color-primary-2-600)]',
  intervals: 'bg-[var(--color-primary-2-100)] text-[var(--color-primary-2-700)]',
  progression: 'bg-[var(--color-primary-1-100)] text-[var(--color-primary-1-600)]',
  fartlek: 'bg-[var(--color-primary-2-50)] text-[var(--color-primary-2-500)]',
  long_run: 'bg-[var(--color-primary-1-100)] text-[var(--color-primary-1-700)]',
  recovery: 'bg-[var(--color-primary-1-50)] text-[var(--color-primary-1-500)]',
  strength: 'bg-[var(--color-secondary-1-100)] text-[var(--color-secondary-1-600)]',
};

// Default templates per phase type
const PHASE_TYPE_DEFAULTS: Record<PhaseType, DayType[]> = {
  base: ['easy', 'strength', 'easy', 'easy', 'strength', 'long_run', 'rest'],
  build: ['easy', 'strength', 'progression', 'easy', 'easy', 'long_run', 'rest'],
  peak: ['easy', 'intervals', 'easy', 'tempo', 'strength', 'long_run', 'rest'],
  taper: ['easy', 'fartlek', 'rest', 'easy', 'rest', 'easy', 'rest'],
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
    return {
      day_of_week: dayOfWeek,
      training_type: null,
      is_rest_day: true,
      run_type: null,
      template_id: null,
      notes: null,
      run_details: null,
    };
  }
  if (type === 'strength') {
    return {
      day_of_week: dayOfWeek,
      training_type: 'strength',
      is_rest_day: false,
      run_type: null,
      template_id: null,
      notes: null,
      run_details: null,
    };
  }
  return {
    day_of_week: dayOfWeek,
    training_type: 'running',
    is_rest_day: false,
    run_type: type as RunType,
    template_id: null,
    notes: null,
    // run_details: keep null — will be auto-calculated unless user sets details
  };
}

function createDefaultTemplate(phaseType: PhaseType): PhaseWeeklyTemplate {
  const types = PHASE_TYPE_DEFAULTS[phaseType];
  return {
    days: types.map((type, i) => dayTypeToEntry(i, type)),
  };
}

function cloneTemplate(template: PhaseWeeklyTemplate): PhaseWeeklyTemplate {
  return {
    days: template.days.map((d) => ({
      ...d,
      run_details: d.run_details
        ? {
            ...d.run_details,
            intervals: d.run_details.intervals
              ? d.run_details.intervals.map((iv) => ({ ...iv }))
              : null,
          }
        : d.run_details,
    })),
  };
}

/** Check if a running day has any explicitly set RunDetails. */
function hasRunDetails(day: PhaseWeeklyTemplateDayEntry): boolean {
  const rd = day.run_details;
  if (!rd) return false;
  return (
    rd.target_duration_minutes !== null ||
    rd.target_pace_min !== null ||
    rd.intervals !== null
  );
}

interface Props {
  template: PhaseWeeklyTemplate | null;
  weeklyTemplates: PhaseWeeklyTemplates | null;
  phaseType: PhaseType;
  startWeek: number;
  endWeek: number;
  onChange: (template: PhaseWeeklyTemplate) => void;
  onChangeWeeklyTemplates: (templates: PhaseWeeklyTemplates | null) => void;
}

export function PhaseWeeklyTemplateEditor({
  template,
  weeklyTemplates,
  phaseType,
  startWeek,
  endWeek,
  onChange,
  onChangeWeeklyTemplates,
}: Props) {
  const totalWeeks = Math.max(1, endWeek - startWeek + 1);
  const perWeekMode = weeklyTemplates !== null && Object.keys(weeklyTemplates.weeks).length > 0;
  const [activeWeek, setActiveWeek] = useState(1);
  const [expandedDay, setExpandedDay] = useState<number | null>(null);

  // Ensure activeWeek stays in bounds
  const clampedActiveWeek = Math.min(activeWeek, totalWeeks);

  // Resolve the template to display
  const sharedTemplate = template ?? createDefaultTemplate(phaseType);
  const currentTemplate = perWeekMode
    ? (weeklyTemplates?.weeks[String(clampedActiveWeek)] ?? sharedTemplate)
    : sharedTemplate;

  const updateTemplate = useCallback(
    (newTemplate: PhaseWeeklyTemplate) => {
      if (perWeekMode && weeklyTemplates) {
        const updatedWeeks = { ...weeklyTemplates.weeks };
        updatedWeeks[String(clampedActiveWeek)] = newTemplate;
        onChangeWeeklyTemplates({ weeks: updatedWeeks });
      } else {
        onChange(newTemplate);
      }
    },
    [perWeekMode, weeklyTemplates, clampedActiveWeek, onChange, onChangeWeeklyTemplates],
  );

  const handleDayChange = useCallback(
    (dayIndex: number, newType: DayType) => {
      const newDays = currentTemplate.days.map((day, i) =>
        i === dayIndex ? dayTypeToEntry(dayIndex, newType) : day,
      );
      updateTemplate({ days: newDays });
    },
    [currentTemplate, updateTemplate],
  );

  const handleRunDetailsChange = useCallback(
    (dayIndex: number, runDetails: RunDetails | null) => {
      const newDays = currentTemplate.days.map((day, i) =>
        i === dayIndex ? { ...day, run_details: runDetails } : day,
      );
      updateTemplate({ days: newDays });
    },
    [currentTemplate, updateTemplate],
  );

  const handleLoadDefaults = useCallback(() => {
    const defaultTemplate = createDefaultTemplate(phaseType);
    updateTemplate(defaultTemplate);
    setExpandedDay(null);
  }, [phaseType, updateTemplate]);

  const handleTogglePerWeek = useCallback(() => {
    if (perWeekMode) {
      // Deactivate: take week 1 as new shared template
      const week1 = weeklyTemplates?.weeks['1'];
      if (week1) {
        onChange(cloneTemplate(week1));
      }
      onChangeWeeklyTemplates(null);
    } else {
      // Activate: copy current shared template to all weeks
      const weeks: Record<string, PhaseWeeklyTemplate> = {};
      for (let w = 1; w <= totalWeeks; w++) {
        weeks[String(w)] = cloneTemplate(sharedTemplate);
      }
      onChangeWeeklyTemplates({ weeks });
      setActiveWeek(1);
    }
    setExpandedDay(null);
  }, [perWeekMode, weeklyTemplates, sharedTemplate, totalWeeks, onChange, onChangeWeeklyTemplates]);

  const handleCopyFromWeek = useCallback(
    (sourceWeek: number) => {
      if (!weeklyTemplates) return;
      const source = weeklyTemplates.weeks[String(sourceWeek)];
      if (!source) return;
      const updatedWeeks = { ...weeklyTemplates.weeks };
      updatedWeeks[String(clampedActiveWeek)] = cloneTemplate(source);
      onChangeWeeklyTemplates({ weeks: updatedWeeks });
      setExpandedDay(null);
    },
    [weeklyTemplates, clampedActiveWeek, onChangeWeeklyTemplates],
  );

  const expandedDayEntry = expandedDay !== null ? currentTemplate.days[expandedDay] : null;
  const expandedDayType = expandedDayEntry ? getDayType(expandedDayEntry) : null;
  const expandedDayLabel = expandedDay !== null ? DAY_LABELS[expandedDay] : '';
  const expandedDayTypeName = expandedDayType
    ? DAY_TYPE_OPTIONS.find((o) => o.value === expandedDayType)?.label
    : '';
  const showRunDetailsForExpanded =
    expandedDayEntry?.training_type === 'running' && expandedDayEntry.run_type;

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

      {/* Per-week toggle */}
      {totalWeeks > 1 && (
        <label className="flex items-center gap-2 cursor-pointer min-h-[44px]">
          <input
            type="checkbox"
            checked={perWeekMode}
            onChange={handleTogglePerWeek}
            className="w-4 h-4 rounded-[var(--radius-component-sm)] border-[var(--color-border-default)] accent-[var(--color-primary-1-600)]"
          />
          <span className="text-xs text-[var(--color-text-base)]">
            Wochen individuell gestalten
          </span>
        </label>
      )}

      {/* Week tabs */}
      {perWeekMode && (
        <div className="space-y-2">
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {Array.from({ length: totalWeeks }, (_, i) => i + 1).map((w) => (
              <button
                key={w}
                type="button"
                onClick={() => {
                  setActiveWeek(w);
                  setExpandedDay(null);
                }}
                className={`
                  shrink-0 min-w-[44px] min-h-[44px] px-3 py-1.5
                  rounded-[var(--radius-component-sm)] text-xs font-medium
                  transition-colors motion-reduce:transition-none
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]
                  ${
                    w === clampedActiveWeek
                      ? 'bg-[var(--color-primary-1-600)] text-white'
                      : 'bg-[var(--color-bg-muted)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]'
                  }
                `}
              >
                W{w}
              </button>
            ))}
          </div>

          {/* Copy from week */}
          {totalWeeks > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[var(--color-text-muted)]">Kopieren von:</span>
              <div className="flex gap-1">
                {Array.from({ length: totalWeeks }, (_, i) => i + 1)
                  .filter((w) => w !== clampedActiveWeek)
                  .map((w) => (
                    <button
                      key={w}
                      type="button"
                      onClick={() => handleCopyFromWeek(w)}
                      className="text-[10px] text-[var(--color-text-link)] hover:underline underline-offset-2 min-h-[44px] min-w-[44px] flex items-center justify-center"
                    >
                      W{w}
                    </button>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 7-day grid */}
      <div className="grid grid-cols-7 gap-1">
        {DAY_LABELS.map((label, i) => {
          const dayType = getDayType(currentTemplate.days[i]);
          const dayOption = DAY_TYPE_OPTIONS.find((o) => o.value === dayType);
          const isExpanded = expandedDay === i;
          const dayHasDetails = hasRunDetails(currentTemplate.days[i]);

          return (
            <div key={label} className="text-center">
              <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                {label}
              </span>
              {/* Type cycle button */}
              <button
                type="button"
                onClick={() => {
                  const currentIdx = DAY_TYPE_OPTIONS.findIndex((o) => o.value === dayType);
                  const nextIdx = (currentIdx + 1) % DAY_TYPE_OPTIONS.length;
                  handleDayChange(i, DAY_TYPE_OPTIONS[nextIdx].value);
                  if (expandedDay === i) setExpandedDay(null);
                }}
                className={`
                  w-full mt-0.5 py-1.5 px-0.5 rounded-t-[var(--radius-component-sm)]
                  text-[11px] font-medium leading-tight text-center
                  transition-colors motion-reduce:transition-none
                  min-h-[44px] flex items-center justify-center
                  ${DAY_TYPE_COLORS[dayType]}
                  hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]
                `}
                title={dayOption?.label}
              >
                {dayOption?.short}
                {dayHasDetails && (
                  <span className="ml-0.5 text-[8px] opacity-70">*</span>
                )}
              </button>
              {/* Expand toggle */}
              <button
                type="button"
                onClick={() => setExpandedDay(isExpanded ? null : i)}
                className={`
                  w-full flex items-center justify-center
                  min-h-[22px] rounded-b-[var(--radius-component-sm)]
                  transition-colors motion-reduce:transition-none
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]
                  ${isExpanded
                    ? 'bg-[var(--color-bg-surface-hover)]'
                    : 'bg-[var(--color-bg-muted)] hover:bg-[var(--color-bg-surface-hover)]'
                  }
                `}
                aria-expanded={isExpanded}
                aria-label={`${label} Details ${isExpanded ? 'schliessen' : 'oeffnen'}`}
              >
                <ChevronDown
                  className={`w-3 h-3 text-[var(--color-text-muted)] transition-transform duration-150 motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`}
                />
              </button>
            </div>
          );
        })}
      </div>
      <p className="text-[10px] text-[var(--color-text-muted)]">
        Klick zum Wechseln: Ruhe → Easy → Tempo → Intervalle → Long Run → Recovery → Kraft
      </p>

      {/* Expanded day detail panel */}
      {expandedDay !== null && expandedDayEntry && (
        <div className="border border-[var(--color-border-muted)] rounded-[var(--radius-component-md)] p-[var(--spacing-sm)] space-y-2 bg-[var(--color-bg-paper)]">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[var(--color-text-base)]">
              {expandedDayLabel}
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">
              {expandedDayTypeName}
            </span>
          </div>

          {showRunDetailsForExpanded ? (
            <RunDetailsEditor
              runDetails={expandedDayEntry.run_details ?? null}
              runType={expandedDayEntry.run_type ?? null}
              onChange={(details) => handleRunDetailsChange(expandedDay, details)}
            />
          ) : expandedDayEntry.is_rest_day ? (
            <p className="text-xs text-[var(--color-text-muted)] italic">Ruhetag</p>
          ) : expandedDayEntry.training_type === 'strength' ? (
            <p className="text-xs text-[var(--color-text-muted)] italic">
              Krafttraining — Details werden im Wochenplan konfiguriert
            </p>
          ) : (
            <p className="text-xs text-[var(--color-text-muted)] italic">
              Wird automatisch berechnet
            </p>
          )}
        </div>
      )}
    </div>
  );
}
