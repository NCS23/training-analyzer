import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@nordlig/components';
import { DAY_LABELS } from '@/constants/plan';

interface MoveSessionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentDay: number;
  sessionLabel: string;
  onSelectDay: (targetDay: number) => void;
}

export function MoveSessionDialog({
  open,
  onOpenChange,
  currentDay,
  sessionLabel,
  onSelectDay,
}: MoveSessionDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Session verschieben</DialogTitle>
        </DialogHeader>

        <p className="text-xs text-[var(--color-text-muted)] -mt-1">
          <span className="font-medium text-[var(--color-text-base)]">{sessionLabel}</span> auf
          welchen Tag verschieben?
        </p>

        <div className="grid grid-cols-7 gap-1.5">
          {DAY_LABELS.map((label, day) => {
            const isCurrent = day === currentDay;
            return (
              <button
                key={day}
                type="button"
                disabled={isCurrent}
                onClick={() => onSelectDay(day)}
                className={[
                  'flex flex-col items-center justify-center py-2.5 rounded-[var(--radius-component-sm)]',
                  'text-xs font-medium transition-colors duration-100 motion-reduce:transition-none',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
                  isCurrent
                    ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] cursor-default'
                    : 'bg-[var(--color-bg-surface)] text-[var(--color-text-base)] hover:bg-[var(--color-bg-surface-hover)]',
                ].join(' ')}
                aria-label={`${label}${isCurrent ? ' (aktuell)' : ''}`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}
