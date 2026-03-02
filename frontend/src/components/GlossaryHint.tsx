import { InfoHint } from './InfoHint';

interface GlossaryEntry {
  term: string;
  description: string;
}

interface GlossaryHintProps {
  /** List of term/description pairs to show. */
  entries: GlossaryEntry[];
  /** Icon size (default: 14). */
  size?: number;
  /** Preferred side (default: 'bottom'). */
  side?: 'top' | 'right' | 'bottom' | 'left';
}

/**
 * Info icon that shows a glossary of terms on hover.
 * Use in table headers or section labels to explain terminology.
 */
export function GlossaryHint({ entries, size = 14, side = 'bottom' }: GlossaryHintProps) {
  return (
    <InfoHint
      size={size}
      side={side}
      maxWidth={300}
      content={
        <dl className="space-y-1.5">
          {entries.map(({ term, description }) => (
            <div key={term}>
              <dt className="font-medium text-[var(--color-text-base)]">{term}</dt>
              <dd className="text-[var(--color-text-muted)]">{description}</dd>
            </div>
          ))}
        </dl>
      }
    />
  );
}
