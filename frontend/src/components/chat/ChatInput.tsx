import { useState, useCallback } from 'react';
import { Send, Square } from 'lucide-react';
import { Button, Textarea } from '@nordlig/components';

interface ChatInputProps {
  onSend: (message: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
  streaming?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onCancel,
  disabled = false,
  streaming = false,
  placeholder = 'Stelle eine Frage zu deinem Training...',
}: ChatInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-2 items-start">
      <div className="flex-1 [&>div>div:last-child]:hidden">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          autoResize
          inputSize="sm"
          className="!min-h-[44px] max-h-[150px]"
        />
      </div>
      {streaming ? (
        <Button variant="secondary" size="sm" onClick={onCancel} aria-label="Antwort abbrechen">
          <Square className="w-4 h-4" />
        </Button>
      ) : (
        <Button
          variant="primary"
          size="sm"
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          aria-label="Nachricht senden"
        >
          <Send className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
}
