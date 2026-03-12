/**
 * Hook for phase weekly template state and day mutation logic.
 */
import { useState, useCallback } from 'react';
import type {
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  PhaseWeeklyTemplateSessionEntry,
  PhaseWeeklyTemplates,
  RunType,
  PhaseType,
} from '@/api/training-plans';

// --- Default templates per phase type ---

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

const PHASE_TYPE_DEFAULTS: Record<PhaseType, DayType[]> = {
  base: ['easy', 'strength', 'easy', 'easy', 'strength', 'long_run', 'rest'],
  build: ['easy', 'strength', 'progression', 'easy', 'easy', 'long_run', 'rest'],
  peak: ['easy', 'intervals', 'easy', 'tempo', 'strength', 'long_run', 'rest'],
  taper: ['easy', 'fartlek', 'rest', 'easy', 'rest', 'easy', 'rest'],
  transition: ['easy', 'rest', 'easy', 'rest', 'strength', 'rest', 'rest'],
};

function dayTypeToEntry(dayOfWeek: number, type: DayType): PhaseWeeklyTemplateDayEntry {
  if (type === 'rest') {
    return { day_of_week: dayOfWeek, sessions: [], is_rest_day: true, notes: null };
  }
  if (type === 'strength') {
    return {
      day_of_week: dayOfWeek,
      sessions: [
        {
          position: 0,
          training_type: 'strength',
          run_type: null,
          template_id: null,
          notes: null,
          exercises: null,
        },
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

export function createDefaultTemplate(phaseType: PhaseType): PhaseWeeklyTemplate {
  const types = PHASE_TYPE_DEFAULTS[phaseType];
  return {
    days: types.map((type, i) => dayTypeToEntry(i, type)),
  };
}

export function cloneTemplate(template: PhaseWeeklyTemplate): PhaseWeeklyTemplate {
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
        exercises: s.exercises ? s.exercises.map((ex) => ({ ...ex })) : s.exercises,
      })),
    })),
  };
}

interface UsePhaseWeeklyTemplateOptions {
  template: PhaseWeeklyTemplate | null;
  weeklyTemplates: PhaseWeeklyTemplates | null;
  phaseType: PhaseType;
  startWeek: number;
  endWeek: number;
  onChange: (template: PhaseWeeklyTemplate) => void;
  onChangeWeeklyTemplates: (templates: PhaseWeeklyTemplates | null) => void;
}

// eslint-disable-next-line max-lines-per-function -- consolidated template state hook
export function usePhaseWeeklyTemplate({
  template,
  weeklyTemplates,
  phaseType,
  startWeek,
  endWeek,
  onChange,
  onChangeWeeklyTemplates,
}: UsePhaseWeeklyTemplateOptions) {
  const totalWeeks = Math.max(1, endWeek - startWeek + 1);
  const perWeekMode = weeklyTemplates !== null && Object.keys(weeklyTemplates.weeks).length > 0;
  const [activeWeek, setActiveWeek] = useState(1);
  const [copyPopoverOpen, setCopyPopoverOpen] = useState(false);

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

  const handleDayTypeChange = useCallback(
    (dayIndex: number, val: string) => {
      const day = currentTemplate.days[dayIndex];
      if (val === 'rest') {
        updateDay(dayIndex, {
          day_of_week: dayIndex,
          sessions: [],
          is_rest_day: true,
          notes: day.notes ?? null,
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
      } else {
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
      }
    },
    [currentTemplate, updateDay],
  );

  const handleTabChange = useCallback(
    (value: string) => {
      if (value === 'all') {
        if (perWeekMode) {
          const week1 = weeklyTemplates?.weeks['1'];
          if (week1) onChange(cloneTemplate(week1));
          onChangeWeeklyTemplates(null);
        }
      } else {
        const weekNum = Number(value);
        if (!perWeekMode) {
          const weeks: Record<string, PhaseWeeklyTemplate> = {};
          for (let w = 1; w <= totalWeeks; w++) {
            weeks[String(w)] = cloneTemplate(sharedTemplate);
          }
          onChangeWeeklyTemplates({ weeks });
        }
        setActiveWeek(weekNum);
      }
    },
    [perWeekMode, weeklyTemplates, sharedTemplate, totalWeeks, onChange, onChangeWeeklyTemplates],
  );

  const handleCopyFromWeek = useCallback(
    (sourceWeek: number) => {
      if (!weeklyTemplates) return;
      const source = weeklyTemplates.weeks[String(sourceWeek)];
      if (!source) return;
      const updatedWeeks = { ...weeklyTemplates.weeks };
      updatedWeeks[String(clampedActiveWeek)] = cloneTemplate(source);
      onChangeWeeklyTemplates({ weeks: updatedWeeks });
    },
    [weeklyTemplates, clampedActiveWeek, onChangeWeeklyTemplates],
  );

  const otherWeeks = Array.from({ length: totalWeeks }, (_, i) => i + 1).filter(
    (w) => w !== clampedActiveWeek,
  );

  return {
    totalWeeks,
    perWeekMode,
    clampedActiveWeek,
    currentTemplate,
    copyPopoverOpen,
    setCopyPopoverOpen,
    otherWeeks,
    updateDay,
    updateDaySession,
    removeDaySession,
    addDaySession,
    handleDayTypeChange,
    handleTabChange,
    handleCopyFromWeek,
  };
}
