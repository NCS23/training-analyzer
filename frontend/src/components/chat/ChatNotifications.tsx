import { useEffect, useState } from 'react';
import { AlertTriangle, Info, X } from 'lucide-react';
import { Button } from '@nordlig/components';
import type { ChatNotification } from '@/api/chat';
import { getChatNotifications } from '@/api/chat';

interface ChatNotificationsProps {
  onQuickAction: (question: string) => void;
  /** Callback wenn sich die Anzahl ändert (für Badge) */
  onCountChange?: (count: number) => void;
}

export function ChatNotifications({ onQuickAction, onCountChange }: ChatNotificationsProps) {
  const [notifications, setNotifications] = useState<ChatNotification[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  useEffect(() => {
    void getChatNotifications().then((res) => {
      setNotifications(res.notifications);
      onCountChange?.(res.count);
    });
  }, [onCountChange]);

  const visible = notifications.filter((n) => !dismissed.has(n.type));

  if (visible.length === 0) return null;

  return (
    <div className="space-y-2 mb-3">
      {visible.map((n) => (
        <div
          key={n.type}
          className={`flex items-start gap-2 rounded-[var(--radius-md)] px-3 py-2 text-xs ${
            n.severity === 'warning'
              ? 'bg-[var(--color-bg-warning-subtle)] text-[var(--color-text-warning)]'
              : 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)]'
          }`}
        >
          {n.severity === 'warning' ? (
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          ) : (
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          )}
          <div className="flex-1 space-y-1">
            <p className="font-medium">{n.title}</p>
            <p className="opacity-80">{n.message}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onQuickAction(n.suggested_question)}
              className="!text-xs !px-0 !py-0 !min-h-0 underline"
            >
              {n.suggested_question}
            </Button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDismissed((prev) => new Set([...prev, n.type]))}
            aria-label="Benachrichtigung schließen"
            className="!p-0.5 !min-h-0 !min-w-0 shrink-0"
          >
            <X className="w-3 h-3" />
          </Button>
        </div>
      ))}
    </div>
  );
}
