import { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  Tooltip,
} from '@nordlig/components';
import { Check, Pencil, Plus } from 'lucide-react';
import { useDroppable } from '@dnd-kit/core';
import type { PlannedSession, WeeklyPlanEntry, ComplianceDayEntry } from '@/api/weekly-plan';
import { getSessionTemplate } from '@/api/session-templates';
import { formatTonnage } from '@/hooks/useTonnageCalc';
import { DAY_LABELS } from '@/constants/plan';
import { TemplatePickerDialog } from '../TemplatePickerDialog';
import { INITIAL_TYPE_OPTIONS, MAX_SESSIONS, TYPE_ICON_COLORS } from './day-card-constants';
import { getEntryTypeKey, getDateStr, isDayInPast } from './day-card-helpers';
import { DraggableSessionRow } from './DraggableSessionRow';
import { DraggableRestDay } from './DraggableRestDay';
import { SessionDetailDialog } from './SessionDetailDialog';
import { DayWeatherBar } from './DayWeatherBar';
import { RestDayDialog } from './RestDayDialog';

interface DayCardProps {
  entry: WeeklyPlanEntry;
  weekStart: string;
  isToday: boolean;
  compliance: ComplianceDayEntry | undefined;
  showCompliance: boolean;
  onUpdate: (updates: Partial<WeeklyPlanEntry>) => void;
  onNavigateSession: (sessionId: number) => void;
  onMoveSession?: (sessionIdx: number, targetDay: number) => void;
  onMoveRestDay?: (targetDay: number) => void;
}

// eslint-disable-next-line complexity, max-lines-per-function -- Orchestrator mit Compliance-Rendering + Mutation-Helpern
export function DayCard({
  entry,
  weekStart,
  isToday,
  compliance,
  showCompliance,
  onUpdate,
  onNavigateSession,
  onMoveSession,
  onMoveRestDay,
}: DayCardProps) {
  const { setNodeRef: dropRef, isOver } = useDroppable({
    id: `day-${entry.day_of_week}`,
  });

  const primaryTypeKey = getEntryTypeKey(entry);
  const primaryIconColor = TYPE_ICON_COLORS[primaryTypeKey] ?? TYPE_ICON_COLORS.empty;
  const isPast = isDayInPast(weekStart, entry.day_of_week);
  const isCompleted = compliance?.status === 'completed' || compliance?.status === 'rest_ok';
  const isPartial = compliance?.status === 'partial';
  const hasActualSessions = compliance?.actual_sessions && compliance.actual_sessions.length > 0;

  const hasPlanSessions = entry.sessions.length > 0;
  const [openSessionIdx, setOpenSessionIdx] = useState<number | null>(null);
  const [showRestDayDialog, setShowRestDayDialog] = useState(false);
  const [pendingSessionType, setPendingSessionType] = useState<string | null>(null);

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

  const addSession = (type: string) => {
    if (type === 'rest') {
      onUpdate({ sessions: [], is_rest_day: true });
    } else if (type === 'running' || type === 'strength') {
      setPendingSessionType(type);
    }
  };

  const addEmptySession = (type: string) => {
    const newSession: PlannedSession = {
      position: entry.sessions.length,
      training_type: type,
    };
    onUpdate({ sessions: [...entry.sessions, newSession], is_rest_day: false });
  };

  const handleTemplatePicked = async (
    template: import('@/api/session-templates').SessionTemplateSummary | null,
  ) => {
    const type = pendingSessionType;
    setPendingSessionType(null);
    if (!type) return;

    if (!template) {
      addEmptySession(type);
      return;
    }

    try {
      const full = await getSessionTemplate(template.id);
      const newSession: PlannedSession = {
        position: entry.sessions.length,
        training_type: type,
        template_id: full.id,
        template_name: full.name,
        run_details: type === 'running' ? (full.run_details ?? null) : undefined,
        exercises: type === 'strength' ? (full.exercises ?? undefined) : undefined,
        notes: type === 'strength' ? (full.description ?? null) : undefined,
      };
      onUpdate({ sessions: [...entry.sessions, newSession], is_rest_day: false });
    } catch {
      addEmptySession(type);
    }
  };

  const clearDay = () => {
    onUpdate({ sessions: [], is_rest_day: false, notes: null });
  };

  return (
    <>
      <div
        ref={dropRef}
        className={[
          'flex flex-col min-w-[120px] rounded-[var(--radius-component-md)]',
          'bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)]',
          'transition-all duration-200 motion-reduce:transition-none',
          isOver
            ? 'ring-2 ring-[var(--color-interactive-primary)] bg-[var(--color-bg-surface-hover)]'
            : isToday
              ? 'ring-2 ring-[var(--color-border-focus)]'
              : '',
        ].join(' ')}
      >
        {/* Day label + date header */}
        <div className="p-[var(--spacing-sm)] pb-0">
          <div className="flex items-baseline justify-between mb-1">
            <span className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
              {DAY_LABELS[entry.day_of_week]}
            </span>
            <div className="flex items-center gap-1">
              {entry.plan_id != null && entry.edited && (
                <Tooltip
                  content="Manuell bearbeitet — wird bei Regenerierung übersprungen"
                  side="top"
                >
                  <span className="inline-flex">
                    <Pencil
                      className="w-2.5 h-2.5 text-[var(--color-text-muted)]"
                      aria-label="Manuell bearbeitet"
                    />
                  </span>
                </Tooltip>
              )}
              <span className="text-xs text-[var(--color-text-muted)]">
                {getDateStr(weekStart, entry.day_of_week)}.
              </span>
            </div>
          </div>
        </div>

        {/* Wetter-Forecast */}
        {entry.weather && (
          <DayWeatherBar weather={entry.weather} />
        )}

        {/* Session rows — each one clickable */}
        <div className="px-[var(--spacing-sm)] pb-[var(--spacing-xs)] flex flex-col gap-0.5">
          {entry.is_rest_day ? (
            <DraggableRestDay
              onClick={() => setShowRestDayDialog(true)}
              dayOfWeek={entry.day_of_week}
              iconColor={primaryIconColor}
            />
          ) : hasPlanSessions ? (
            entry.sessions.map((session, idx) => (
              <DraggableSessionRow
                key={idx}
                session={session}
                onClick={() => setOpenSessionIdx(idx)}
                dayOfWeek={entry.day_of_week}
                sessionIdx={idx}
              />
            ))
          ) : (
            <span className="text-xs text-[var(--color-text-disabled)] px-1">—</span>
          )}

          {/* Add session / set type — always available when not at max */}
          {!entry.is_rest_day && entry.sessions.length < MAX_SESSIONS && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                {/* prettier-ignore */}
                <button // ds-ok — kompakter Plus-Trigger in Card-Grid, kein DS-Button
                  type="button"
                  className={[
                    'flex items-center gap-1 w-full min-h-[22px] px-1 -mx-1',
                    'rounded-[var(--radius-component-sm)]',
                    'text-[10px] text-[var(--color-text-disabled)]',
                    'hover:text-[var(--color-text-muted)] hover:bg-[var(--color-bg-surface-hover)]',
                    'transition-colors duration-100 motion-reduce:transition-none',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
                  ].join(' ')}
                  aria-label="Session hinzufügen"
                >
                  <Plus className="w-3 h-3" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                {INITIAL_TYPE_OPTIONS.filter((o) => o.value !== '').map((opt) => (
                  <DropdownMenuItem key={opt.value} onSelect={() => addSession(opt.value)}>
                    {opt.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        {/* Compliance — past days only */}
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
            {compliance.planned_template_name && (
              <p className="text-[10px] text-[var(--color-text-muted)] truncate mt-0.5">
                Soll: {compliance.planned_template_name}
                {compliance.planned_exercise_count
                  ? ` (${compliance.planned_exercise_count} Üb.)`
                  : ''}
              </p>
            )}
            {hasActualSessions &&
              compliance.actual_sessions.map((s) =>
                // prettier-ignore
                <button // ds-ok — kompakter Klick-Link auf Session, kein DS-Button
                  key={s.session_id}
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onNavigateSession(s.session_id);
                  }}
                  className="block text-[10px] text-[var(--color-text-link)] hover:underline mt-0.5 min-h-[22px]"
                >
                  {s.workout_type === 'strength' ? (
                    <>
                      {s.template_name ?? 'Kraft'}
                      {s.total_tonnage_kg != null && s.total_tonnage_kg > 0
                        ? `: ${formatTonnage(s.total_tonnage_kg).value}${formatTonnage(s.total_tonnage_kg).unit}`
                        : ''}
                      {s.exercise_count ? ` (${s.exercise_count} Üb.)` : ''}
                    </>
                  ) : (
                    <>
                      {s.distance_km ? `${s.distance_km.toFixed(1)}km` : ''}
                      {s.pace ? ` ${s.pace}/km` : ''}
                    </>
                  )}
                </button>,
              )}
          </div>
        )}
      </div>

      {/* Per-session detail dialog */}
      {openSessionIdx !== null && entry.sessions[openSessionIdx] && (
        <SessionDetailDialog
          open={true}
          onOpenChange={(dialogOpen) => {
            if (!dialogOpen) setOpenSessionIdx(null);
          }}
          session={entry.sessions[openSessionIdx]}
          sessionIndex={openSessionIdx}
          dayOfWeek={entry.day_of_week}
          canRemove={true}
          onUpdate={(updated) => updateSession(openSessionIdx, updated)}
          onRemove={() => {
            removeSession(openSessionIdx);
            setOpenSessionIdx(null);
          }}
          onMoveSession={
            onMoveSession
              ? (targetDay) => {
                  onMoveSession(openSessionIdx, targetDay);
                  setOpenSessionIdx(null);
                }
              : undefined
          }
        />
      )}

      {/* Rest day dialog */}
      <RestDayDialog
        open={showRestDayDialog}
        onOpenChange={setShowRestDayDialog}
        notes={entry.notes}
        dayOfWeek={entry.day_of_week}
        onSaveNotes={(notes) => onUpdate({ notes })}
        onRemoveRestDay={clearDay}
        onMoveRestDay={
          onMoveRestDay
            ? (targetDay) => {
                setShowRestDayDialog(false);
                onMoveRestDay(targetDay);
              }
            : undefined
        }
      />

      {/* Template picker dialog */}
      {pendingSessionType && (
        <TemplatePickerDialog
          open={true}
          onOpenChange={(tpOpen) => {
            if (!tpOpen) setPendingSessionType(null);
          }}
          sessionType={pendingSessionType}
          onSelect={handleTemplatePicked}
        />
      )}
    </>
  );
}
