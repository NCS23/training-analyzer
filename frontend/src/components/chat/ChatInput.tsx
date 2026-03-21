import { useState, useCallback, useEffect } from 'react';
import { Mic, MicOff, Send, Square } from 'lucide-react';
import { Button, Textarea } from '@nordlig/components';
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition';

interface ChatInputProps {
  onSend: (message: string) => void;
  onCancel?: () => void;
  disabled?: boolean;
  streaming?: boolean;
  placeholder?: string;
  /** Optionaler angehefteter Kontext (Badge über dem Input) */
  contextBadge?: React.ReactNode;
}

export function ChatInput({
  onSend,
  onCancel,
  disabled = false,
  streaming = false,
  placeholder = 'Stelle eine Frage zu deinem Training...',
  contextBadge,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const { isListening, transcript, isSupported, error, startListening, stopListening } =
    useSpeechRecognition();

  // Erkannten Text ins Input übernehmen
  useEffect(() => {
    if (transcript) {
      setValue(transcript);
    }
  }, [transcript]);

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

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div className="space-y-2">
      {contextBadge}
      {error && <p className="text-xs text-[var(--color-text-error)]">{error}</p>}
      <div className="flex gap-2 items-start">
        <div className="flex-1 [&>div>div:last-child]:hidden">
          <Textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={isListening ? 'Sprich jetzt...' : placeholder}
            rows={1}
            autoResize
            inputSize="sm"
            className="!min-h-[44px] max-h-[150px]"
          />
        </div>
        {isSupported && !streaming && (
          <Button
            variant={isListening ? 'primary' : 'ghost'}
            size="sm"
            onClick={handleMicClick}
            disabled={disabled}
            aria-label={isListening ? 'Aufnahme stoppen' : 'Spracheingabe starten'}
            className={isListening ? 'motion-reduce:animate-none' : ''}
            style={isListening ? { animation: 'typing-dot 1.4s ease-in-out infinite' } : undefined}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </Button>
        )}
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
    </div>
  );
}
