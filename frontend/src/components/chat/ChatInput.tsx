import { useState, useRef, useCallback } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@nordlig/components';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Stelle eine Frage zu deinem Training...',
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
    }
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        className="flex-1 min-h-[44px] max-h-[150px] resize-none rounded-[var(--radius-md)] border border-[var(--color-border-base)] bg-[var(--color-bg-base)] px-3 py-2.5 text-sm text-[var(--color-text-base)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] disabled:opacity-50"
      />
      <Button
        variant="primary"
        size="sm"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        aria-label="Nachricht senden"
      >
        <Send className="w-4 h-4" />
      </Button>
    </div>
  );
}
