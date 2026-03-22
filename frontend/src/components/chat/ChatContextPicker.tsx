import { useState } from 'react';
import { Pin, X } from 'lucide-react';
import { Button, Input } from '@nordlig/components';
import type { ChatContext } from './ChatContextBadge';

interface ChatContextPickerProps {
  onSelect: (context: ChatContext) => void;
  disabled?: boolean;
}

/**
 * Kompakter Kontext-Picker — User kann Session-ID oder Wochendatum eingeben.
 * Auf Mobile vertikal gestackt, auf Desktop inline.
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
    <div className="flex flex-col gap-2 p-2 rounded-[var(--radius-md)] bg-[var(--color-bg-surface)] border border-[var(--color-border-default)]">
      <div className="flex items-center justify-between">
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
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setOpen(false)}
          aria-label="Schließen"
          className="!p-1 !min-h-0 !min-w-0"
        >
          <X className="w-3.5 h-3.5" />
        </Button>
      </div>
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={mode === 'session' ? 'Session-ID (z.B. 42)' : 'Datum (z.B. 2026-03-16)'}
          inputSize="sm"
          className="!min-h-[32px] !text-xs flex-1"
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
          className="!text-xs !px-3 !py-1 !min-h-0"
        >
          Anheften
        </Button>
      </div>
    </div>
  );
}
