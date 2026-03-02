import { Info } from 'lucide-react';
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@nordlig/components';

interface InfoHintProps {
  /** Content shown in the popover. Can be a string or JSX. */
  content: React.ReactNode;
  /** Icon size in px (default: 14). */
  size?: number;
  /** Preferred side for the popover (default: 'top'). */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Max width of the popover (default: 260px). */
  maxWidth?: number;
}

/**
 * Small (i) icon that shows explanatory text on tap/click.
 * Works on both desktop and mobile (touch).
 */
export function InfoHint({
  content,
  size = 14,
  side = 'top',
  maxWidth = 260,
}: InfoHintProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center justify-center rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]"
          aria-label="Info"
        >
          <Info style={{ width: size, height: size }} />
        </button>
      </PopoverTrigger>
      <PopoverContent
        side={side}
        showArrow
        className="text-xs leading-relaxed"
        style={{ maxWidth }}
      >
        {content}
      </PopoverContent>
    </Popover>
  );
}
