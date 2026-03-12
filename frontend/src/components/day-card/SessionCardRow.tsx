import { Dumbbell, Footprints } from 'lucide-react';
import type { PlannedSession } from '@/api/weekly-plan';
import { RUN_TYPE_LABELS } from '@/constants/plan';
import { TYPE_ICON_COLORS } from './day-card-constants';
import { getSessionTypeKey } from './day-card-helpers';

// eslint-disable-next-line complexity -- bedingte Detail-Felder für Running/Strength
export function SessionCardRow({
  session,
  onClick,
}: {
  session: PlannedSession;
  onClick: () => void;
}) {
  const typeKey = getSessionTypeKey(session);
  const iconColor = TYPE_ICON_COLORS[typeKey] ?? TYPE_ICON_COLORS.empty;
  const rd = session.run_details;
  const isSkipped = session.status === 'skipped';

  const label =
    session.training_type === 'strength'
      ? (session.template_name ?? 'Kraft')
      : rd?.run_type
        ? (RUN_TYPE_LABELS[rd.run_type] ?? rd.run_type)
        : 'Laufen';

  const details: string[] = [];
  if (session.training_type === 'strength') {
    const exCount = session.exercises?.length;
    if (exCount) details.push(`${exCount} Üb.`);
  }
  if (session.training_type === 'running') {
    if (rd?.target_duration_minutes) details.push(`${rd.target_duration_minutes}′`);
    if (rd?.target_pace_min) {
      details.push(
        rd.target_pace_max ? `${rd.target_pace_min}–${rd.target_pace_max}` : rd.target_pace_min,
      );
    }
    const segs = rd?.segments ?? [];
    if (segs.length > 1) {
      const workSegs = segs.filter((s) => s.segment_type === 'work');
      if (workSegs.length > 0) {
        const first = workSegs[0];
        const dur = first.target_duration_minutes ? `${first.target_duration_minutes}′` : '';
        details.push(`${workSegs.length}×${dur}`);
      }
    }
  }

  const Icon = session.training_type === 'strength' ? Dumbbell : Footprints;

  return (
    // prettier-ignore
    <button // ds-ok — asChild-ähnlicher Klick-Handler, kein DS-Button
      type="button"
      onClick={onClick}
      className={[
        'flex flex-col min-w-0 w-full text-left min-h-[22px]',
        'rounded-[var(--radius-component-sm)] px-1 -mx-1 py-0.5',
        'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-100 motion-reduce:transition-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
        isSkipped ? 'opacity-50' : '',
      ].join(' ')}
      aria-label={`${label} Details${isSkipped ? ' (übersprungen)' : ''}`}
    >
      <div className="flex items-start gap-1.5">
        <Icon className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${iconColor}`} />
        <span
          className={[
            'text-xs font-medium break-words',
            isSkipped
              ? 'text-[var(--color-text-muted)] line-through'
              : 'text-[var(--color-text-base)]',
          ].join(' ')}
        >
          {label}
        </span>
      </div>
      {details.length > 0 && (
        <span className="text-[10px] text-[var(--color-text-muted)] truncate pl-5">
          {details.join(' · ')}
        </span>
      )}
    </button>
  );
}
