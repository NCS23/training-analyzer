import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
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
import { Copy, Dumbbell, Footprints, Moon, Plus } from 'lucide-react';
import type {
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  PhaseWeeklyTemplateSessionEntry,
  PhaseWeeklyTemplates,
  PhaseType,
} from '@/api/training-plans';
import { DAY_LABELS } from '@/constants/plan';
import { usePhaseWeeklyTemplate } from '@/hooks/usePhaseWeeklyTemplate';
import { TemplateSessionEditor } from './phase-weekly-template/TemplateSessionEditor';

// --- Constants ---

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

const DAY_TYPE_OPTIONS = [
  { value: 'rest', label: 'Ruhetag' },
  { value: 'running', label: 'Laufen' },
  { value: 'strength', label: 'Kraft' },
];

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

// eslint-disable-next-line max-lines-per-function -- JSX-heavy template editor
export function PhaseWeeklyTemplateEditor({
  template,
  weeklyTemplates,
  phaseType,
  startWeek,
  endWeek,
  onChange,
  onChangeWeeklyTemplates,
}: Props) {
  const tmpl = usePhaseWeeklyTemplate({
    template,
    weeklyTemplates,
    phaseType,
    startWeek,
    endWeek,
    onChange,
    onChangeWeeklyTemplates,
  });

  return (
    <div className="space-y-2">
      {/* Week selector: [Alle] [W1] [W2] ... + separate copy button */}
      {tmpl.totalWeeks > 1 && (
        <div className="flex items-center gap-1.5">
          <SegmentedControl
            size="sm"
            items={[
              { value: 'all', label: 'Alle' },
              ...Array.from({ length: tmpl.totalWeeks }, (_, i) => ({
                value: String(i + 1),
                label: `W${i + 1}`,
              })),
            ]}
            value={tmpl.perWeekMode ? String(tmpl.clampedActiveWeek) : 'all'}
            onChange={tmpl.handleTabChange}
          />
          {tmpl.perWeekMode && (
            <Popover open={tmpl.copyPopoverOpen} onOpenChange={tmpl.setCopyPopoverOpen}>
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
                  {tmpl.otherWeeks.map((w) => (
                    <Button
                      key={w}
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        tmpl.handleCopyFromWeek(w);
                        tmpl.setCopyPopoverOpen(false);
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
          const dayTypes = getDayTypes(tmpl.currentTemplate.days[i]);
          const isEmpty = dayTypes.length === 0;
          const dayEntry = tmpl.currentTemplate.days[i];

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
                        if (val) tmpl.handleDayTypeChange(i, val);
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
                            onUpdate={(updated) => tmpl.updateDaySession(i, idx, updated)}
                            onRemove={() => tmpl.removeDaySession(i, idx)}
                            onMakeRest={() => tmpl.handleDayTypeChange(i, 'rest')}
                          />
                        </CardBody>
                      </Card>
                    ))}

                  {/* Add Session button */}
                  {dayEntry.sessions.length > 0 && !dayEntry.is_rest_day && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => tmpl.addDaySession(i)}
                      className="w-full"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Session hinzufügen
                    </Button>
                  )}

                  {/* Day notes — only for rest days */}
                  {dayEntry.is_rest_day && (
                    <div>
                      <Label className="text-xs mb-1">Notiz</Label>
                      <Input
                        type="text"
                        value={dayEntry.notes ?? ''}
                        onChange={(e) =>
                          tmpl.updateDay(i, { ...dayEntry, notes: e.target.value || null })
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
