import { GripVertical } from 'lucide-react';
import { useDraggable } from '@dnd-kit/core';
import type { PlannedSession } from '@/api/weekly-plan';
import { SessionCardRow } from './SessionCardRow';

export function DraggableSessionRow({
  session,
  onClick,
  dayOfWeek,
  sessionIdx,
}: {
  session: PlannedSession;
  onClick: () => void;
  dayOfWeek: number;
  sessionIdx: number;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `session-${dayOfWeek}-${sessionIdx}`,
    data: { type: 'session' as const, dayOfWeek, sessionIdx },
  });

  return (
    <div
      ref={setNodeRef}
      className={[
        'flex items-start gap-0.5',
        isDragging ? 'opacity-30' : '',
        'transition-opacity duration-150 motion-reduce:transition-none',
      ].join(' ')}
    >
      {/* prettier-ignore */}
      <button // ds-ok — dnd-kit Drag-Handle, kein DS-Button
        type="button"
        {...attributes}
        {...listeners}
        className={[
          'mt-0.5 p-1 touch-none cursor-grab shrink-0',
          'block',
          'text-[var(--color-text-disabled)] hover:text-[var(--color-text-muted)]',
          'transition-colors duration-100 motion-reduce:transition-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
          'rounded-[var(--radius-component-sm)]',
        ].join(' ')}
        aria-label="Ziehen zum Verschieben"
      >
        <GripVertical className="w-3 h-3" />
      </button>
      <div className="flex-1 min-w-0">
        <SessionCardRow session={session} onClick={onClick} />
      </div>
    </div>
  );
}
