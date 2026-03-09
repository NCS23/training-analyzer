import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardBody,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  SegmentedControl,
} from '@nordlig/components';
import { Calendar, Clock, FileText, Target } from 'lucide-react';
import type {
  TrainingPlan,
  TrainingPhase,
  PhaseWeeklyTemplate,
  PhaseWeeklyTemplateDayEntry,
  PhaseWeeklyTemplateSessionEntry,
} from '@/api/training-plans';
import type { RunDetails } from '@/api/weekly-plan';
import type { Segment } from '@/api/segment';
import { trainingTypeLabels, trainingTypeBadgeVariant, lapTypeLabels } from '@/constants/training';
import { PhaseTimeline } from '@/components/PhaseTimeline';
import {
  PHASE_TYPES,
  DAY_LABELS,
  formatDateDE,
  getWeekNumber,
  getCurrentWeekStart,
} from '@/components/plan-helpers';

// --- Helpers ---

const DAY_NAMES = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

function formatRunDetails(details: RunDetails | null | undefined): string {
  if (!details) return '';
  const parts: string[] = [];
  if (details.target_duration_minutes) parts.push(`${details.target_duration_minutes} min`);
  if (details.target_pace_min && details.target_pace_max) {
    parts.push(`${details.target_pace_min}–${details.target_pace_max}/km`);
  } else if (details.target_pace_min) {
    parts.push(`${details.target_pace_min}/km`);
  }
  if (details.target_hr_min && details.target_hr_max) {
    parts.push(`HR ${details.target_hr_min}–${details.target_hr_max}`);
  }
  return parts.join(' · ');
}

function formatSegmentDetail(seg: Segment): string {
  const typeLabel = lapTypeLabels[seg.segment_type] ?? seg.segment_type;
  const parts: string[] = [];

  // Target
  if (seg.repeats > 1) {
    if (seg.target_distance_km) {
      const d =
        seg.target_distance_km >= 1
          ? `${seg.target_distance_km}km`
          : `${seg.target_distance_km * 1000}m`;
      parts.push(`${seg.repeats}×${d}`);
    } else if (seg.target_duration_minutes) {
      parts.push(`${seg.repeats}×${seg.target_duration_minutes}′`);
    } else {
      parts.push(`${seg.repeats}×`);
    }
  } else {
    if (seg.target_distance_km) {
      const d =
        seg.target_distance_km >= 1
          ? `${seg.target_distance_km} km`
          : `${seg.target_distance_km * 1000}m`;
      parts.push(d);
    } else if (seg.target_duration_minutes) {
      parts.push(`${seg.target_duration_minutes} min`);
    }
  }

  // Pace
  if (seg.target_pace_min && seg.target_pace_max) {
    parts.push(`${seg.target_pace_min}–${seg.target_pace_max}/km`);
  } else if (seg.target_pace_min) {
    parts.push(`${seg.target_pace_min}/km`);
  }

  // HR
  if (seg.target_hr_min && seg.target_hr_max) {
    parts.push(`HR ${seg.target_hr_min}–${seg.target_hr_max}`);
  }

  // Exercise name
  if (seg.exercise_name) {
    parts.push(seg.exercise_name);
  }

  return `${typeLabel}: ${parts.join(' · ') || '—'}`;
}

function formatSegmentsSummary(segments: Segment[]): string[] | null {
  if (segments.length === 0) return null;
  return segments.map(formatSegmentDetail);
}

function getSessionLabel(session: PhaseWeeklyTemplateSessionEntry): string {
  if (session.training_type === 'strength') return 'Kraft';
  return trainingTypeLabels[session.run_type ?? 'easy'] ?? session.run_type ?? 'Lauf';
}

function getSessionBadgeVariant(session: PhaseWeeklyTemplateSessionEntry) {
  if (session.training_type === 'strength') return 'neutral' as const;
  return trainingTypeBadgeVariant[session.run_type ?? 'easy'] ?? ('primary' as const);
}

function calcDurationWeeks(startDate: string, endDate: string): number {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffMs = end.getTime() - start.getTime();
  return Math.max(1, Math.round(diffMs / (7 * 24 * 60 * 60 * 1000)));
}

// --- Sub-Components ---

function SessionDetails({ session }: { session: PhaseWeeklyTemplateSessionEntry }) {
  if (session.training_type === 'strength') {
    const exercises = session.exercises;
    return (
      <div className="space-y-0.5">
        {session.template_name && (
          <p className="text-xs text-[var(--color-text-muted)]">
            Vorlage:{' '}
            <span className="font-medium text-[var(--color-text-base)]">
              {session.template_name}
            </span>
          </p>
        )}
        {exercises && exercises.length > 0 ? (
          <ul className="text-xs text-[var(--color-text-muted)] space-y-0.5 pl-3 list-disc marker:text-[var(--color-text-disabled)]">
            {exercises.map((ex, i) => (
              <li key={i}>
                {ex.name} — {ex.sets}×{ex.reps}
                {ex.weight_kg != null && ` · ${ex.weight_kg}kg`}
              </li>
            ))}
          </ul>
        ) : (
          <span className="text-sm text-[var(--color-text-muted)]">
            {session.notes ?? 'Krafttraining'}
          </span>
        )}
        {session.notes && exercises && exercises.length > 0 && (
          <p className="text-xs text-[var(--color-text-muted)] italic">{session.notes}</p>
        )}
      </div>
    );
  }

  const details = session.run_details;
  const detailStr = formatRunDetails(details);

  // Prefer segments (new) over intervals (legacy)
  const segments = details?.segments ?? [];
  const segmentLines = segments.length > 0 ? formatSegmentsSummary(segments) : null;

  if (!detailStr && !segmentLines && !session.notes) {
    return <span className="text-sm text-[var(--color-text-disabled)]">—</span>;
  }

  return (
    <div className="space-y-0.5">
      {detailStr && <p className="text-sm text-[var(--color-text-base)]">{detailStr}</p>}
      {segmentLines && (
        <ul className="text-xs text-[var(--color-text-muted)] space-y-0.5 pl-3 list-disc marker:text-[var(--color-text-disabled)]">
          {segmentLines.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      )}
      {session.notes && (
        <p className="text-xs text-[var(--color-text-muted)] italic">{session.notes}</p>
      )}
    </div>
  );
}

function DayRow({ day, dayIdx }: { day: PhaseWeeklyTemplateDayEntry; dayIdx: number }) {
  const dayLabel = (
    <>
      <span className="hidden sm:inline">{DAY_NAMES[dayIdx]}</span>
      <span className="sm:hidden">{DAY_LABELS[dayIdx]}</span>
    </>
  );

  if (day.is_rest_day) {
    return (
      <TableRow>
        <TableCell className="font-medium text-sm">{dayLabel}</TableCell>
        <TableCell>
          <span className="text-sm text-[var(--color-text-muted)]">Ruhetag</span>
        </TableCell>
        <TableCell>
          {day.notes ? (
            <p className="text-xs italic text-[var(--color-text-muted)]">{day.notes}</p>
          ) : (
            <span className="text-sm text-[var(--color-text-disabled)]">—</span>
          )}
        </TableCell>
      </TableRow>
    );
  }

  if (day.sessions.length === 0) {
    return (
      <TableRow>
        <TableCell className="font-medium text-sm">{dayLabel}</TableCell>
        <TableCell>
          <span className="text-sm text-[var(--color-text-disabled)]">—</span>
        </TableCell>
        <TableCell>
          {day.notes ? (
            <p className="text-xs italic text-[var(--color-text-muted)]">{day.notes}</p>
          ) : (
            <span className="text-sm text-[var(--color-text-disabled)]">—</span>
          )}
        </TableCell>
      </TableRow>
    );
  }

  return (
    <>
      {day.sessions.map((session, sIdx) => {
        const isLast = sIdx === day.sessions.length - 1;
        return (
          <TableRow key={sIdx}>
            {sIdx === 0 ? (
              <TableCell
                className="font-medium text-sm align-top"
                rowSpan={day.sessions.length > 1 ? day.sessions.length : undefined}
              >
                {dayLabel}
              </TableCell>
            ) : null}
            <TableCell className="align-top">
              <Badge variant={getSessionBadgeVariant(session)} size="xs">
                {getSessionLabel(session)}
              </Badge>
            </TableCell>
            <TableCell>
              <SessionDetails session={session} />
              {isLast && day.notes && (
                <p className="text-xs italic text-[var(--color-text-muted)] mt-1">{day.notes}</p>
              )}
            </TableCell>
          </TableRow>
        );
      })}
    </>
  );
}

function WeeklyTemplateTable({ template }: { template: PhaseWeeklyTemplate }) {
  if (!template || template.days.length !== 7) return null;

  return (
    <div className="overflow-x-auto -mx-1">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-20">Tag</TableHead>
            <TableHead className="w-28">Typ</TableHead>
            <TableHead>Details</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {template.days.map((day, dayIdx) => (
            <DayRow key={dayIdx} day={day} dayIdx={dayIdx} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function PerWeekTabs({
  weeklyTemplates,
  fallbackTemplate,
  totalWeeks,
}: {
  weeklyTemplates: Record<string, PhaseWeeklyTemplate>;
  fallbackTemplate: PhaseWeeklyTemplate | null;
  totalWeeks: number;
}) {
  const [activeWeek, setActiveWeek] = useState('1');
  const items = Array.from({ length: totalWeeks }, (_, i) => ({
    value: String(i + 1),
    label: `W${i + 1}`,
  }));
  const template = weeklyTemplates[activeWeek] ?? fallbackTemplate;

  return (
    <div className="space-y-3">
      <SegmentedControl items={items} value={activeWeek} onChange={setActiveWeek} size="sm" />
      {template && template.days.length === 7 ? (
        <WeeklyTemplateTable template={template} />
      ) : (
        <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
          Keine Vorlage für Woche {activeWeek}
        </p>
      )}
    </div>
  );
}

function PhaseCard({ phase }: { phase: TrainingPhase }) {
  const totalWeeks = phase.end_week - phase.start_week + 1;
  const hasTemplate = phase.weekly_template && phase.weekly_template.days.length === 7;
  const perWeekMode =
    phase.weekly_templates && Object.keys(phase.weekly_templates.weeks).length > 0;
  const phaseTypeLabel =
    PHASE_TYPES.find((t) => t.value === phase.phase_type)?.label ?? phase.phase_type;

  return (
    <Card elevation="raised" padding="spacious">
      <CardBody className="space-y-5">
        {/* Header */}
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base font-semibold text-[var(--color-text-base)]">{phase.name}</h3>
            <Badge variant="neutral" size="xs">
              {phaseTypeLabel}
            </Badge>
            <Badge variant="neutral" size="xs">
              Woche {phase.start_week}–{phase.end_week}
            </Badge>
          </div>
          {phase.notes && (
            <p className="text-sm text-[var(--color-text-muted)] leading-relaxed mt-1">
              {phase.notes}
            </p>
          )}
        </div>

        {/* Weekly Template */}
        {(hasTemplate || perWeekMode) && (
          <div className="space-y-3 pt-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Wochenvorlage
              <span className="font-normal normal-case tracking-normal ml-1">
                ({perWeekMode ? 'Individuell' : 'Übergreifend'})
              </span>
            </h4>

            {hasTemplate && !perWeekMode && (
              <WeeklyTemplateTable template={phase.weekly_template!} />
            )}

            {perWeekMode && phase.weekly_templates && (
              <PerWeekTabs
                weeklyTemplates={phase.weekly_templates.weeks}
                fallbackTemplate={phase.weekly_template}
                totalWeeks={totalWeeks}
              />
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}

// --- Main Component ---

interface TrainingPlanReadViewProps {
  plan: TrainingPlan;
}

export function TrainingPlanReadView({ plan }: TrainingPlanReadViewProps) {
  const weekNumber =
    plan.status === 'active' ? getWeekNumber(plan.start_date, getCurrentWeekStart()) : 0;
  const durationWeeks = calcDurationWeeks(plan.start_date, plan.end_date);
  const goal = plan.goal_summary;
  const raceDate = goal?.race_date ?? plan.target_event_date;

  return (
    <div className="space-y-6">
      {/* ── Overview Card ────────────────────────────────────────── */}
      <Card elevation="raised" padding="spacious">
        <CardBody className="space-y-5">
          {/* Heading + Description */}
          <div>
            <h2 className="text-base font-semibold text-[var(--color-text-base)]">Überblick</h2>
            {plan.description && (
              <p className="text-sm text-[var(--color-text-muted)] leading-relaxed mt-1">
                {plan.description}
              </p>
            )}
          </div>

          {/* Goal section */}
          {goal && (
            <div className="space-y-2 pt-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Ziel
                <span className="font-normal normal-case tracking-normal ml-1">
                  (
                  <Link to="/plan/goals" className="hover:underline underline-offset-2">
                    {goal.title}
                  </Link>
                  )
                </span>
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-[10px]">
                {goal.target_time_formatted && (
                  <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                    <div className="flex items-center gap-1 mb-1 sm:mb-2">
                      <Clock className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]" />
                      <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                        Zielzeit
                      </p>
                    </div>
                    <p className="text-sm sm:text-base font-semibold text-[var(--color-text-base)] leading-none">
                      {goal.target_time_formatted}
                    </p>
                  </div>
                )}
                {raceDate && (
                  <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                    <div className="flex items-center gap-1 mb-1 sm:mb-2">
                      <Calendar className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]" />
                      <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                        Wettkampf
                      </p>
                    </div>
                    <p className="text-sm sm:text-base font-semibold text-[var(--color-text-base)] leading-none">
                      {formatDateDE(raceDate)}
                    </p>
                  </div>
                )}
                {goal.days_until != null && (
                  <div className="col-span-2 sm:col-span-1 rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                    <div className="flex items-center gap-1 mb-1 sm:mb-2">
                      <Target className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]" />
                      <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                        Countdown
                      </p>
                    </div>
                    <p className="text-sm sm:text-base font-semibold text-[var(--color-text-base)] leading-none">
                      {goal.days_until > 0
                        ? `${goal.days_until} Tage`
                        : goal.days_until === 0
                          ? 'Heute!'
                          : 'Vergangen'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Date metrics */}
          <div className="space-y-2 pt-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
              Zeitraum
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-[10px]">
              <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                <div className="flex items-center gap-1 mb-1 sm:mb-2">
                  <Calendar className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]" />
                  <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                    Start
                  </p>
                </div>
                <p className="text-sm sm:text-base font-semibold text-[var(--color-text-base)] leading-none">
                  {formatDateDE(plan.start_date)}
                </p>
              </div>
              <div className="rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                <div className="flex items-center gap-1 mb-1 sm:mb-2">
                  <Calendar className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]" />
                  <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                    Ende
                  </p>
                </div>
                <p className="text-sm sm:text-base font-semibold text-[var(--color-text-base)] leading-none">
                  {formatDateDE(plan.end_date)}
                </p>
              </div>
              <div className="col-span-2 sm:col-span-1 rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-default)] px-2.5 py-2 sm:px-3.5 sm:py-3">
                <div className="flex items-center gap-1 mb-1 sm:mb-2">
                  <Clock className="w-[10px] h-[10px] sm:w-[11px] sm:h-[11px] text-[var(--color-text-muted)]" />
                  <p className="text-[10px] sm:text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                    Dauer
                  </p>
                </div>
                <p className="text-sm sm:text-base font-semibold text-[var(--color-text-base)] leading-none">
                  {durationWeeks} Wochen
                </p>
              </div>
            </div>
          </div>

          {/* Wochenpläne count */}
          {plan.weekly_plan_week_count > 0 && (
            <span className="text-xs text-[var(--color-text-muted)]">
              <FileText className="w-3 h-3 inline-block mr-1 align-text-bottom" />
              {plan.weekly_plan_week_count} Wochenpläne generiert
            </span>
          )}

          {/* Phase Timeline */}
          {plan.phases.length > 1 && (
            <div className="space-y-2 pt-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Phasenübersicht
                <span className="font-normal normal-case tracking-normal ml-1">
                  ({plan.phases.length} Phasen)
                </span>
              </h2>
              <PhaseTimeline phases={plan.phases} weekNumber={weekNumber} />
            </div>
          )}
        </CardBody>
      </Card>

      {/* ── Phase Cards ──────────────────────────────────────────── */}
      {plan.phases.length === 0 ? (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
              Keine Phasen definiert.
            </p>
          </CardBody>
        </Card>
      ) : (
        plan.phases
          .slice()
          .sort((a, b) => a.start_week - b.start_week)
          .map((phase) => <PhaseCard key={phase.id} phase={phase} />)
      )}
    </div>
  );
}
