// ds-ok-file: native HTML select fuer scroll-UX (#786 — cmdk-Combobox scrollt
// in unserem Layout nach 6 Iterationen weiterhin nicht). Optisch via DS-Tokens
// an Nordlig Select angeglichen. Verwendung NUR an Stellen mit langen Listen.
import { ChevronDown } from 'lucide-react';
import { useId } from 'react';

export interface NativeSelectOption {
  value: string;
  label: string;
}

interface NativeSelectProps {
  options: NativeSelectOption[];
  value?: string;
  onChange?: (value: string | undefined) => void;
  placeholder?: string;
  inputSize?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  className?: string;
  'aria-label'?: string;
  id?: string;
}

const SIZE_CLASSES: Record<NonNullable<NativeSelectProps['inputSize']>, string> = {
  sm: 'h-9 text-xs px-2 pr-7',
  md: 'h-10 text-sm px-3 pr-8',
  lg: 'h-11 text-base px-4 pr-9',
};

/**
 * Native HTML select mit DS-Styling — gezielter Workaround fuer #786.
 *
 * Hintergrund: Nordlig Select (intern cmdk-Combobox) hat in der Praxis
 * (#774/#776/#778/#780/#782/#784) ein nicht-funktionierendes Scroll-Verhalten
 * bei langen Listen. Browser-natives select triggert auf Mobile den System-
 * Wheel-Picker (iOS) und auf Desktop den nativen Browser-Dropdown — beides
 * scrollt nativ und perfekt.
 */
export function NativeSelect({
  options,
  value,
  onChange,
  placeholder,
  inputSize = 'md',
  disabled = false,
  className = '',
  'aria-label': ariaLabel,
  id,
}: NativeSelectProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className={`relative ${className}`}>
      <select // ds-ok: native fuer scroll-UX (#786)
        id={selectId}
        value={value ?? ''}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(e) => onChange?.(e.target.value || undefined)}
        className={[
          'w-full appearance-none cursor-pointer',
          'bg-[var(--color-input-bg)] text-[var(--color-input-text)]',
          'border border-[var(--color-input-border)]',
          'rounded-[var(--radius-input)]',
          'focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] focus:ring-offset-1',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          SIZE_CLASSES[inputSize],
        ].join(' ')}
      >
        {placeholder && !value && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]"
        aria-hidden="true"
      />
    </div>
  );
}
