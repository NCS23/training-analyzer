import { Link } from 'react-router-dom';
import { CalendarPlus, ChevronRight } from 'lucide-react';
import { Button } from '@nordlig/components';

export interface PlanCreatedInfo {
  plan_id: number;
  plan_name: string;
  status?: string;
  weeks: number;
  weeks_generated: number;
  phases: number | { name: string }[];
  start_date: string;
  end_date: string;
  race_date?: string;
}

interface PlanCreatedCardProps {
  plan: PlanCreatedInfo;
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function PlanCreatedCard({ plan }: PlanCreatedCardProps) {
  const isDraft = plan.status === 'draft';

  return (
    <div className="my-2 rounded-[var(--radius-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-base)] p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-[var(--color-bg-primary-subtle)] flex items-center justify-center">
          <CalendarPlus className="w-4 h-4 text-[var(--color-text-primary)]" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-[var(--color-text-base)]">
              Trainingsplan erstellt
            </p>
            {isDraft && (
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[var(--color-bg-warning-subtle)] text-[var(--color-text-warning)]">
                Entwurf
              </span>
            )}
          </div>
          <p className="text-xs text-[var(--color-text-muted)]">{plan.plan_name}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-[var(--color-text-muted)]">Zeitraum: </span>
          <span className="text-[var(--color-text-base)]">
            {formatDate(plan.start_date)} – {formatDate(plan.end_date)}
          </span>
        </div>
        <div>
          <span className="text-[var(--color-text-muted)]">Wochen: </span>
          <span className="text-[var(--color-text-base)]">{plan.weeks_generated}</span>
        </div>
        <div>
          <span className="text-[var(--color-text-muted)]">Phasen: </span>
          <span className="text-[var(--color-text-base)]">
            {Array.isArray(plan.phases) ? plan.phases.length : plan.phases}
          </span>
        </div>
        {plan.race_date && (
          <div>
            <span className="text-[var(--color-text-muted)]">Wettkampf: </span>
            <span className="text-[var(--color-text-base)]">{formatDate(plan.race_date)}</span>
          </div>
        )}
      </div>

      <div className="flex gap-2 pt-1">
        <Link to={`/plan/programs/${plan.plan_id}`}>
          <Button variant="primary" size="sm" className="!text-xs !px-3 !py-1.5 !min-h-0">
            {isDraft ? 'Plan ansehen' : 'Zum Wochenplan'}
            <ChevronRight className="w-3 h-3 ml-1" />
          </Button>
        </Link>
        {!isDraft && (
          <Link to="/plan">
            <Button variant="ghost" size="sm" className="!text-xs !px-3 !py-1.5 !min-h-0">
              Wochenplan
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
