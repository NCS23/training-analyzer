import { useState, useCallback } from 'react';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  Button,
  Card,
  CardBody,
  Input,
  Label,
  Popover,
  PopoverTrigger,
  PopoverContent,
  SegmentedControl,
  Select,
} from '@nordlig/components';
import { Copy, Dumbbell, Footprints, LayoutTemplate, Moon, Plus, Trash2 } from 'lucide-react';
import type {
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  PhaseWeeklyTemplateSessionEntry,
  PhaseWeeklyTemplates,
  RunType,
  PhaseType,
} from '@/api/training-plans';
import type { RunDetails } from '@/api/weekly-plan';
import type { TemplateExercise } from '@/api/session-templates';
import { getSessionTemplate } from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';
import { getPresetSegments, hasSegmentData } from '@/config/segmentPresets';
import { DAY_LABELS, SESSION_TYPE_OPTIONS } from '@/constants/plan';
import { RunDetailsEditor } from './RunDetailsEditor';
import { StrengthExerciseEditor } from './StrengthExerciseEditor';
import { TemplatePickerDialog } from './TemplatePickerDialog';

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

const DAY_TYPE_LABELS: Record<DayType, string> = {
  rest: 'Ruhetag',
  easy: 'Easy Run',
  tempo: 'Tempo',
  intervals: 'Intervalle',
  progression: 'Progression',
  fartlek: 'Fartlek',
  long_run: 'Long Run',
  recovery: 'Recovery',
  strength: 'Kraft',
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

const DAY_TYPE_OPTIONS = [
  { value: 'rest', label: 'Ruhetag' },
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
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
        exercises: s.exercises ? s.exercises.map((ex) => ({ ...ex })) : s.exercises,
      })),
    })),
  };
}

// --- TemplateSessionEditor (inline) ---

interface TemplateSessionEditorProps {
  session: PhaseWeeklyTemplateSessionEntry;
  canRemove: boolean;
  showRestOption?: boolean;
  onUpdate: (updated: PhaseWeeklyTemplateSessionEntry) => void;
  onRemove: () => void;
  onMakeRest?: () => void;
}

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
function TemplateSessionEditor({
  session,
  canRemove,
  showRestOption,
  onUpdate,
  onRemove,
  onMakeRest,
}: TemplateSessionEditorProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pendingRunType, setPendingRunType] = useState<string | null>(null);

  const typeOptions = showRestOption
    ? [{ value: 'rest', label: 'Ruhetag' }, ...SESSION_TYPE_OPTIONS]
    : SESSION_TYPE_OPTIONS;

  const handleTypeChange = (val: string) => {
    if (val === 'rest') {
      onMakeRest?.();
      return;
    }
    if (val === 'strength') {
      onUpdate({
        ...session,
        training_type: 'strength',
        run_type: null,
        run_details: undefined,
        exercises: null,
      });
    } else {
      const preset = getPresetSegments('easy');
      onUpdate({
        ...session,
        training_type: 'running',
        run_type: 'easy',
        run_details: {
          run_type: 'easy',
          target_duration_minutes: null,
          target_pace_min: null,
          target_pace_max: null,
          target_hr_min: null,
          target_hr_max: null,
          intervals: null,
          segments: preset,
        },
        exercises: undefined,
      });
    }
  };

  const applyRunTypeWithPreset = (runType: string) => {
    const preset = getPresetSegments(runType as RunType);
    onUpdate({
      ...session,
      run_type: runType as RunType,
      run_details: {
        run_type: runType as RunDetails['run_type'],
        target_duration_minutes: null,
        target_pace_min: null,
        target_pace_max: null,
        target_hr_min: null,
        target_hr_max: null,
        intervals: null,
        segments: preset,
      },
    });
  };

  const applyRunTypeKeepSegments = (runType: string) => {
    onUpdate({
      ...session,
      run_type: runType as RunType,
      run_details: session.run_details
        ? { ...session.run_details, run_type: runType as RunDetails['run_type'] }
        : undefined,
    });
  };

  const handleRunTypeChange = (runType: string) => {
    if (hasSegmentData(session.run_details?.segments)) {
      setPendingRunType(runType);
    } else {
      applyRunTypeWithPreset(runType);
    }
  };

  const handleRunDetailsChange = (details: RunDetails | null) => {
    onUpdate({ ...session, run_details: details ?? undefined });
  };

  const handleExercisesChange = (exercises: TemplateExercise[] | null) => {
    onUpdate({ ...session, exercises });
  };

  const handleTemplateSelect = async (tmplSummary: SessionTemplateSummary | null) => {
    setPickerOpen(false);
    if (!tmplSummary) return;
    try {
      const full = await getSessionTemplate(tmplSummary.id);
      if (session.training_type === 'strength') {
        onUpdate({
          ...session,
          template_id: full.id,
          template_name: full.name,
          exercises: full.exercises.length > 0 ? full.exercises : null,
          notes: full.description ?? session.notes,
        });
      } else if (session.training_type === 'running' && full.run_details) {
        onUpdate({
          ...session,
          template_id: full.id,
          template_name: full.name,
          run_details: full.run_details,
          run_type: full.run_details.run_type as RunType,
        });
      }
    } catch {
      /* template fetch failed — ignore */
    }
  };

  return (
    <div className="space-y-2">
      <div>
        <Label className="text-xs mb-1">Trainingstyp</Label>
        <Select
          options={typeOptions}
          value={session.training_type}
          onChange={(val) => {
            if (val) handleTypeChange(val);
          }}
          inputSize="sm"
          aria-label="Trainingstyp"
        />
      </div>

      {/* Template picker button + name */}
      <div className="space-y-1">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setPickerOpen(true)}
          className="w-full"
        >
          <LayoutTemplate className="w-4 h-4 mr-1" />
          {session.template_id ? 'Vorlage wechseln' : 'Vorlage laden'}
        </Button>
        {session.template_name && (
          <p className="text-xs text-[var(--color-text-muted)] truncate px-1">
            Vorlage:{' '}
            <span className="font-medium text-[var(--color-text-base)]">
              {session.template_name}
            </span>
          </p>
        )}
      </div>

      {session.training_type === 'running' && (
        <>
          <div>
            <Label className="text-xs mb-1">Lauftyp</Label>
            <Select
              options={RUN_TYPE_OPTIONS}
              value={session.run_type ?? 'easy'}
              onChange={(val) => {
                if (val) handleRunTypeChange(val);
              }}
              inputSize="sm"
              aria-label="Lauftyp"
            />
          </div>
          <RunDetailsEditor
            runDetails={session.run_details ?? null}
            runType={session.run_type}
            onChange={handleRunDetailsChange}
          />
        </>
      )}

      {session.training_type === 'strength' && (
        <StrengthExerciseEditor
          exercises={session.exercises ?? null}
          onChange={handleExercisesChange}
        />
      )}

      {/* Notes */}
      <div>
        <Label className="text-xs mb-1">Notiz</Label>
        <Input
          type="text"
          value={session.notes ?? ''}
          onChange={(e) => onUpdate({ ...session, notes: e.target.value || null })}
          inputSize="sm"
          placeholder={
            session.training_type === 'running'
              ? 'z.B. lockerer Dauerlauf, Fokus Technik'
              : 'z.B. Aufwärmen, Mobilität'
          }
          aria-label="Session Notiz"
        />
      </div>

      {canRemove && (
        <div className="flex justify-end pt-3">
          <Button variant="destructive-outline" size="sm" onClick={onRemove}>
            <Trash2 className="w-4 h-4 mr-1" />
            Session entfernen
          </Button>
        </div>
      )}

      {/* Template Picker Dialog */}
      <TemplatePickerDialog
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        sessionType={session.training_type}
        onSelect={handleTemplateSelect}
      />

      {/* Preset confirmation dialog */}
      <AlertDialog
        open={pendingRunType !== null}
        onOpenChange={(open) => {
          if (!open) setPendingRunType(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Segmente ersetzen?</AlertDialogTitle>
            <AlertDialogDescription>
              Du hast bereits Segmente konfiguriert. Moechtest du sie mit der Vorlage fuer &ldquo;
              {RUN_TYPE_OPTIONS.find((o) => o.value === pendingRunType)?.label ?? pendingRunType}
              &rdquo; ersetzen?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                if (pendingRunType) applyRunTypeKeepSegments(pendingRunType);
                setPendingRunType(null);
              }}
            >
              Beibehalten
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (pendingRunType) applyRunTypeWithPreset(pendingRunType);
                setPendingRunType(null);
              }}
            >
              Ersetzen
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// --- Compact day cell for grid ---

function DayCellIcon({ type }: { type: DayType }) {
  if (type === 'rest') return <Moon className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />;
  if (type === 'strength')
    return <Dumbbell className="w-3.5 h-3.5 text-[var(--color-secondary-1-500)]" />;
  return <Footprints className="w-3.5 h-3.5 text-[var(--color-primary-1-500)]" />;
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

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
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
        // Switch to shared mode
        if (perWeekMode) {
          const week1 = weeklyTemplates?.weeks['1'];
          if (week1) onChange(cloneTemplate(week1));
          onChangeWeeklyTemplates(null);
        }
      } else {
        const weekNum = Number(value);
        if (!perWeekMode) {
          // Switch to per-week mode — clone shared into all weeks
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
      // Accordion resets automatically on template change
    },
    [weeklyTemplates, clampedActiveWeek, onChangeWeeklyTemplates],
  );

  const otherWeeks = Array.from({ length: totalWeeks }, (_, i) => i + 1).filter(
    (w) => w !== clampedActiveWeek,
  );

  return (
    <div className="space-y-2">
      {/* Week selector: [Alle] [W1] [W2] ... + separate copy button */}
      {totalWeeks > 1 && (
        <div className="flex items-center gap-1.5">
          <SegmentedControl
            size="sm"
            items={[
              { value: 'all', label: 'Alle' },
              ...Array.from({ length: totalWeeks }, (_, i) => ({
                value: String(i + 1),
                label: `W${i + 1}`,
              })),
            ]}
            value={perWeekMode ? String(clampedActiveWeek) : 'all'}
            onChange={handleTabChange}
          />
          {perWeekMode && (
            <Popover open={copyPopoverOpen} onOpenChange={setCopyPopoverOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Von anderer Woche kopieren"
                  className="h-7 w-7 p-0 bg-[var(--color-seg-bg)] rounded-[var(--radius-seg-container)]"
                >
                  <Copy className="w-3.5 h-3.5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="start" className="p-2 w-auto">
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-[var(--color-text-muted)] px-2 py-1">
                    Kopieren von
                  </span>
                  {otherWeeks.map((w) => (
                    <Button
                      key={w}
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        handleCopyFromWeek(w);
                        setCopyPopoverOpen(false);
                      }}
                    >
                      Woche {w}
                    </Button>
                  ))}
                </div>
              </PopoverContent>
            </Popover>
          )}
        </div>
      )}

      {/* Day list (Accordion) */}
      <Accordion
        type="multiple"
        className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)]"
      >
        {DAY_LABELS.map((label, i) => {
          const dayTypes = getDayTypes(currentTemplate.days[i]);
          const isEmpty = dayTypes.length === 0;
          const dayEntry = currentTemplate.days[i];

          return (
            <AccordionItem key={label} value={label}>
              <AccordionTrigger>
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="text-xs font-semibold text-[var(--color-text-muted)] w-6 shrink-0">
                    {label}
                  </span>
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {isEmpty ? (
                      <span className="text-xs text-[var(--color-text-disabled)]">—</span>
                    ) : (
                      dayTypes.map((type, idx) => (
                        <div key={idx} className="flex items-center gap-1">
                          <DayCellIcon type={type} />
                          <span className="text-xs font-medium text-[var(--color-text-base)]">
                            {DAY_TYPE_LABELS[type]}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {/* Day type selector — only for rest days */}
                  {dayEntry.is_rest_day && (
                    <Select
                      options={DAY_TYPE_OPTIONS}
                      value="rest"
                      onChange={(val) => {
                        if (val) handleDayTypeChange(i, val);
                      }}
                      inputSize="sm"
                      aria-label="Tagestyp"
                    />
                  )}

                  {/* Sessions list */}
                  {dayEntry.sessions.length > 0 &&
                    dayEntry.sessions.map((session, idx) => (
                      <Card key={idx} elevation="flat" padding="compact">
                        <CardBody>
                          <TemplateSessionEditor
                            session={session}
                            canRemove={dayEntry.sessions.length > 1}
                            showRestOption={idx === 0}
                            onUpdate={(updated) => updateDaySession(i, idx, updated)}
                            onRemove={() => removeDaySession(i, idx)}
                            onMakeRest={() => handleDayTypeChange(i, 'rest')}
                          />
                        </CardBody>
                      </Card>
                    ))}

                  {/* Add Session button */}
                  {dayEntry.sessions.length > 0 && !dayEntry.is_rest_day && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => addDaySession(i)}
                      className="w-full"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Session hinzufügen
                    </Button>
                  )}

                  {/* Day notes — only for rest days (sessions have their own notes field) */}
                  {dayEntry.is_rest_day && (
                    <div>
                      <Label className="text-xs mb-1">Notiz</Label>
                      <Input
                        type="text"
                        value={dayEntry.notes ?? ''}
                        onChange={(e) =>
                          updateDay(i, { ...dayEntry, notes: e.target.value || null })
                        }
                        inputSize="sm"
                        placeholder="z.B. optional Yoga, Mobilität"
                        aria-label={`${DAY_LABELS[i]} Notiz`}
                      />
                    </div>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          );
        })}
      </Accordion>
    </div>
  );
}
