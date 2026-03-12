import { GripVertical, Moon } from 'lucide-react';
import { useDraggable } from '@dnd-kit/core';

export function DraggableRestDay({
  onClick,
  dayOfWeek,
  iconColor,
}: {
  onClick: () => void;
  dayOfWeek: number;
  iconColor: string;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `rest-${dayOfWeek}`,
    data: { type: 'rest' as const, dayOfWeek },
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
        aria-label="Ruhetag ziehen zum Verschieben"
      >
        <GripVertical className="w-3 h-3" />
      </button>
      <div className="flex-1 min-w-0">
        {/* prettier-ignore */}
        <button // ds-ok — kompakter Klick-Handler in Card-Row, kein DS-Button
          type="button"
          onClick={onClick}
          className={[
            'flex items-center gap-1.5 w-full text-left min-h-[22px]',
            'rounded-[var(--radius-component-sm)] px-1 -mx-1',
            'hover:bg-[var(--color-bg-surface-hover)] transition-colors duration-100 motion-reduce:transition-none',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
          ].join(' ')}
          aria-label="Ruhetag ändern"
        >
          <Moon className={`w-3.5 h-3.5 shrink-0 ${iconColor}`} />
          <span className="text-xs text-[var(--color-text-muted)]">Ruhe</span>
        </button>
      </div>
    </div>
  );
}
