import { Info } from 'lucide-react';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@nordlig/components';

interface InfoHintProps {
  /** Content shown in the hover card. Can be a string or JSX. */
  content: React.ReactNode;
  /** Icon size in px (default: 14). */
  size?: number;
  /** Preferred side for the card (default: 'top'). */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Max width of the card (default: 260px). */
  maxWidth?: number;
}

/**
 * Small (i) icon that shows explanatory text on hover / tap-and-hold.
 * Use wherever a term or concept needs clarification.
 */
export function InfoHint({ content, size = 14, side = 'top', maxWidth = 260 }: InfoHintProps) {
  return (
    <HoverCard openDelay={200} closeDelay={100}>
      <HoverCardTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center justify-center rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]"
          aria-label="Info"
        >
          <Info style={{ width: size, height: size }} />
        </button>
      </HoverCardTrigger>
      <HoverCardContent
        side={side}
        showArrow
        className="text-xs leading-relaxed"
        style={{ maxWidth }}
      >
        {content}
      </HoverCardContent>
    </HoverCard>
  );
}
