import { useState } from 'react';
import { Pin } from 'lucide-react';
import { Button, Input } from '@nordlig/components';
import type { ChatContext } from './ChatContextBadge';

interface ChatContextPickerProps {
  onSelect: (context: ChatContext) => void;
  disabled?: boolean;
}

/**
 * Kompakter Kontext-Picker — User kann Session-ID oder Wochendatum eingeben.
 * Wird als Popover-artiges Dropdown über dem Chat-Input angezeigt.
 */
export function ChatContextPicker({ onSelect, disabled }: ChatContextPickerProps) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<'session' | 'week'>('session');
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    if (mode === 'session') {
      onSelect({ type: 'session', id: trimmed, label: `#${trimmed}` });
    } else {
      onSelect({ type: 'week', id: trimmed, label: trimmed });
    }
    setInputValue('');
    setOpen(false);
  };

  if (!open) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(true)}
        disabled={disabled}
        aria-label="Kontext anheften"
        className="!p-1.5 !min-h-0 !min-w-0"
      >
        <Pin className="w-3.5 h-3.5" />
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2 p-2 rounded-[var(--radius-md)] bg-[var(--color-bg-surface)] border border-[var(--color-border-default)]">
      <div className="flex gap-1">
        <Button
          variant={mode === 'session' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => setMode('session')}
          className="!text-xs !px-2 !py-1 !min-h-0"
        >
          Session
        </Button>
        <Button
          variant={mode === 'week' ? 'primary' : 'ghost'}
          size="sm"
          onClick={() => setMode('week')}
          className="!text-xs !px-2 !py-1 !min-h-0"
        >
          Woche
        </Button>
      </div>
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder={mode === 'session' ? 'Session-ID (z.B. 42)' : 'Datum (z.B. 2026-03-16)'}
        inputSize="sm"
        className="!min-h-[32px] !text-xs w-40"
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSubmit();
          if (e.key === 'Escape') setOpen(false);
        }}
        autoFocus
      />
      <Button
        variant="primary"
        size="sm"
        onClick={handleSubmit}
        disabled={!inputValue.trim()}
        className="!text-xs !px-2 !py-1 !min-h-0"
      >
        Anheften
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(false)}
        className="!text-xs !px-2 !py-1 !min-h-0"
      >
        ✕
      </Button>
    </div>
  );
}
