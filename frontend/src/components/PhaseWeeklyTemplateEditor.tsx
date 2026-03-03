import { useState, useCallback } from 'react';
import { Button, Label, Select, Separator } from '@nordlig/components';
import { ChevronDown, Dumbbell, Footprints, Minus, Moon, Plus } from 'lucide-react';
import type {
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  PhaseWeeklyTemplateSessionEntry,
  PhaseWeeklyTemplates,
  RunType,
  PhaseType,
} from '@/api/training-plans';
import type { RunDetails } from '@/api/weekly-plan';
import { RunDetailsEditor } from './RunDetailsEditor';

const DAY_LABELS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

const MAX_SESSIONS = 3;

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

const DAY_TYPE_SHORT: Record<DayType, string> = {
  rest: 'Ruhe',
  easy: 'Easy',
  tempo: 'Tempo',
  intervals: 'Int.',
  progression: 'Prog.',
  fartlek: 'Fartl.',
  long_run: 'Long',
  recovery: 'Rec.',
  strength: 'Kraft',
};

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

const RUN_TYPE_OPTIONS: { value: RunType; label: string }[] = [
  { value: 'easy', label: 'Easy Run' },
  { value: 'recovery', label: 'Recovery' },
  { value: 'long_run', label: 'Long Run' },
  { value: 'progression', label: 'Progression' },
  { value: 'tempo', label: 'Tempo' },
  { value: 'intervals', label: 'Intervalle' },
  { value: 'repetitions', label: 'Repetitions' },
  { value: 'fartlek', label: 'Fartlek' },
  { value: 'race', label: 'Wettkampf' },
];

const SESSION_TYPE_OPTIONS = [
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
];

const INITIAL_TYPE_OPTIONS = [
  { value: '', label: 'Leer' },
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
  { value: 'rest', label: 'Ruhetag' },
];

// Default templates per phase type
const PHASE_TYPE_DEFAULTS: Record<PhaseType, DayType[]> = {
  base: ['easy', 'strength', 'easy', 'easy', 'strength', 'long_run', 'rest'],
  build: ['easy', 'strength', 'progression', 'easy', 'easy', 'long_run', 'rest'],
  peak: ['easy', 'intervals', 'easy', 'tempo', 'strength', 'long_run', 'rest'],
  taper: ['easy', 'fartlek', 'rest', 'easy', 'rest', 'easy', 'rest'],
  transition: ['easy', 'rest', 'easy', 'rest', 'strength', 'rest', 'rest'],
};

// --- Helpers ---

function getSessionDayType(session: PhaseWeeklyTemplateSessionEntry): DayType {
  if (session.training_type === 'strength') return 'strength';
  if (session.training_type === 'running' && session.run_type) return session.run_type as DayType;
  return 'easy';
}

function getDayTypes(day: PhaseWeeklyTemplateDayEntry): DayType[] {
  if (day.is_rest_day) return ['rest'];
  if (day.sessions.length === 0) return [];
  return day.sessions.map(getSessionDayType);
}

function dayTypeToEntry(dayOfWeek: number, type: DayType): PhaseWeeklyTemplateDayEntry {
  if (type === 'rest') {
    return { day_of_week: dayOfWeek, sessions: [], is_rest_day: true, notes: null };
  }
  if (type === 'strength') {
    return {
      day_of_week: dayOfWeek,
      sessions: [
        { position: 0, training_type: 'strength', run_type: null, template_id: null, notes: null },
      ],
      is_rest_day: false,
      notes: null,
    };
  }
  return {
    day_of_week: dayOfWeek,
    sessions: [
      {
        position: 0,
        training_type: 'running',
        run_type: type as RunType,
        template_id: null,
        notes: null,
      },
    ],
    is_rest_day: false,
    notes: null,
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
      sessions: d.sessions.map((s) => ({
        ...s,
        run_details: s.run_details
          ? {
              ...s.run_details,
              intervals: s.run_details.intervals
                ? s.run_details.intervals.map((iv) => ({ ...iv }))
                : null,
            }
          : s.run_details,
      })),
    })),
  };
}

// --- TemplateSessionEditor (inline) ---

interface TemplateSessionEditorProps {
  session: PhaseWeeklyTemplateSessionEntry;
  canRemove: boolean;
  onUpdate: (updated: PhaseWeeklyTemplateSessionEntry) => void;
  onRemove: () => void;
}

function TemplateSessionEditor({
  session,
  canRemove,
  onUpdate,
  onRemove,
}: TemplateSessionEditorProps) {
  const handleTypeChange = (val: string) => {
    if (val === 'strength') {
      onUpdate({ ...session, training_type: 'strength', run_type: null, run_details: undefined });
    } else {
      onUpdate({ ...session, training_type: 'running', run_type: 'easy', run_details: undefined });
    }
  };

  const handleRunTypeChange = (runType: string) => {
    onUpdate({ ...session, run_type: runType as RunType, run_details: undefined });
  };

  const handleRunDetailsChange = (details: RunDetails | null) => {
    onUpdate({ ...session, run_details: details ?? undefined });
  };

  return (
    <div className="space-y-2">
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
        <>
          <Select
            options={RUN_TYPE_OPTIONS}
            value={session.run_type ?? 'easy'}
            onChange={(val) => {
              if (val) handleRunTypeChange(val);
            }}
            inputSize="sm"
            aria-label="Lauftyp"
          />
          <RunDetailsEditor
            runDetails={session.run_details ?? null}
            runType={session.run_type}
            onChange={handleRunDetailsChange}
          />
        </>
      )}

      {session.training_type === 'strength' && (
        <p className="text-xs text-[var(--color-text-muted)] italic">
          Krafttraining — Details werden im Wochenplan konfiguriert
        </p>
      )}
    </div>
  );
}

// --- Compact day cell for grid ---

function DayCellIcon({ type }: { type: DayType }) {
  if (type === 'rest') return <Moon className="w-3 h-3 text-[var(--color-text-muted)]" />;
  if (type === 'strength')
    return <Dumbbell className="w-3 h-3 text-[var(--color-secondary-1-500)]" />;
  return <Footprints className="w-3 h-3 text-[var(--color-primary-1-500)]" />;
}

// --- Main Component ---

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

  const clampedActiveWeek = Math.min(activeWeek, totalWeeks);

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

  // --- Day mutation helpers ---

  const updateDay = useCallback(
    (dayIndex: number, updatedDay: PhaseWeeklyTemplateDayEntry) => {
      const newDays = currentTemplate.days.map((day, i) => (i === dayIndex ? updatedDay : day));
      updateTemplate({ days: newDays });
    },
    [currentTemplate, updateTemplate],
  );

  const updateDaySession = useCallback(
    (dayIndex: number, sessionIndex: number, updated: PhaseWeeklyTemplateSessionEntry) => {
      const day = currentTemplate.days[dayIndex];
      const newSessions = day.sessions.map((s, i) => (i === sessionIndex ? updated : s));
      updateDay(dayIndex, { ...day, sessions: newSessions });
    },
    [currentTemplate, updateDay],
  );

  const removeDaySession = useCallback(
    (dayIndex: number, sessionIndex: number) => {
      const day = currentTemplate.days[dayIndex];
      const newSessions = day.sessions
        .filter((_, i) => i !== sessionIndex)
        .map((s, i) => ({ ...s, position: i }));
      updateDay(dayIndex, { ...day, sessions: newSessions });
    },
    [currentTemplate, updateDay],
  );

  const addDaySession = useCallback(
    (dayIndex: number) => {
      const day = currentTemplate.days[dayIndex];
      const newSession: PhaseWeeklyTemplateSessionEntry = {
        position: day.sessions.length,
        training_type: 'running',
        run_type: 'easy',
        template_id: null,
        notes: null,
      };
      updateDay(dayIndex, { ...day, sessions: [...day.sessions, newSession] });
    },
    [currentTemplate, updateDay],
  );

  const handleInitialTypeChange = useCallback(
    (dayIndex: number, val: string) => {
      if (val === 'rest') {
        updateDay(dayIndex, {
          day_of_week: dayIndex,
          sessions: [],
          is_rest_day: true,
          notes: null,
        });
      } else if (val === 'strength') {
        updateDay(dayIndex, {
          day_of_week: dayIndex,
          sessions: [
            {
              position: 0,
              training_type: 'strength',
              run_type: null,
              template_id: null,
              notes: null,
            },
          ],
          is_rest_day: false,
          notes: null,
        });
      } else if (val === 'running') {
        updateDay(dayIndex, {
          day_of_week: dayIndex,
          sessions: [
            {
              position: 0,
              training_type: 'running',
              run_type: 'easy',
              template_id: null,
              notes: null,
            },
          ],
          is_rest_day: false,
          notes: null,
        });
      } else {
        updateDay(dayIndex, {
          day_of_week: dayIndex,
          sessions: [],
          is_rest_day: false,
          notes: null,
        });
      }
    },
    [updateDay],
  );

  const handleLoadDefaults = useCallback(() => {
    const defaultTemplate = createDefaultTemplate(phaseType);
    updateTemplate(defaultTemplate);
    setExpandedDay(null);
  }, [phaseType, updateTemplate]);

  const handleTogglePerWeek = useCallback(() => {
    if (perWeekMode) {
      const week1 = weeklyTemplates?.weeks['1'];
      if (week1) {
        onChange(cloneTemplate(week1));
      }
      onChangeWeeklyTemplates(null);
    } else {
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
  const expandedDayLabel = expandedDay !== null ? DAY_LABELS[expandedDay] : '';

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
          const dayTypes = getDayTypes(currentTemplate.days[i]);
          const isExpanded = expandedDay === i;
          const isEmpty = dayTypes.length === 0;

          return (
            <div key={label} className="text-center">
              <span className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                {label}
              </span>
              {/* Day content — shows session badges */}
              <button
                type="button"
                onClick={() => setExpandedDay(isExpanded ? null : i)}
                className={`
                  w-full mt-0.5 py-1 px-0.5 rounded-t-[var(--radius-component-sm)]
                  min-h-[44px] flex flex-col items-center justify-center gap-0.5
                  transition-colors motion-reduce:transition-none
                  hover:bg-[var(--color-bg-surface-hover)]
                  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]
                  ${isEmpty ? 'bg-[var(--color-bg-base)]' : ''}
                `}
                aria-expanded={isExpanded}
                aria-label={`${label} bearbeiten`}
              >
                {isEmpty ? (
                  <span className="text-[10px] text-[var(--color-text-disabled)]">—</span>
                ) : (
                  dayTypes.map((type, idx) => (
                    <div key={idx} className="flex items-center gap-0.5">
                      <DayCellIcon type={type} />
                      <span
                        className={`text-[10px] font-medium ${DAY_TYPE_COLORS[type].split(' ')[1] ?? 'text-[var(--color-text-base)]'}`}
                      >
                        {DAY_TYPE_SHORT[type]}
                      </span>
                    </div>
                  ))
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
                  ${
                    isExpanded
                      ? 'bg-[var(--color-bg-surface-hover)]'
                      : 'bg-[var(--color-bg-muted)] hover:bg-[var(--color-bg-surface-hover)]'
                  }
                `}
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

      {/* Expanded day detail panel */}
      {expandedDay !== null && expandedDayEntry && (
        <div className="border border-[var(--color-border-muted)] rounded-[var(--radius-component-md)] p-[var(--spacing-sm)] space-y-3 bg-[var(--color-bg-paper)]">
          <span className="text-xs font-semibold text-[var(--color-text-base)]">
            {expandedDayLabel}
          </span>

          {/* No sessions and not rest day → initial type selector */}
          {expandedDayEntry.sessions.length === 0 && !expandedDayEntry.is_rest_day && (
            <Select
              options={INITIAL_TYPE_OPTIONS}
              value=""
              onChange={(val) => handleInitialTypeChange(expandedDay, val ?? '')}
              inputSize="sm"
              aria-label="Trainingstyp"
            />
          )}

          {/* Rest day → show selector to switch back */}
          {expandedDayEntry.is_rest_day && (
            <>
              <Select
                options={INITIAL_TYPE_OPTIONS}
                value="rest"
                onChange={(val) => handleInitialTypeChange(expandedDay, val ?? '')}
                inputSize="sm"
                aria-label="Trainingstyp"
              />
              <p className="text-xs text-[var(--color-text-muted)] italic">Ruhetag</p>
            </>
          )}

          {/* Sessions list */}
          {expandedDayEntry.sessions.length > 0 &&
            expandedDayEntry.sessions.map((session, idx) => (
              <div key={idx}>
                {idx > 0 && <Separator className="my-3" />}
                <TemplateSessionEditor
                  session={session}
                  canRemove={expandedDayEntry.sessions.length > 1}
                  onUpdate={(updated) => updateDaySession(expandedDay, idx, updated)}
                  onRemove={() => removeDaySession(expandedDay, idx)}
                />
              </div>
            ))}

          {/* Add Session button */}
          {expandedDayEntry.sessions.length > 0 &&
            !expandedDayEntry.is_rest_day &&
            expandedDayEntry.sessions.length < MAX_SESSIONS && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => addDaySession(expandedDay)}
                className="w-full"
                aria-label="Session hinzufügen"
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
