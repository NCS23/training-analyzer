import { MessageSquarePlus, Trash2 } from 'lucide-react';
import { Button } from '@nordlig/components';
import type { ConversationSummary } from '@/api/chat';

interface ConversationListProps {
  conversations: ConversationSummary[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: ConversationListProps) {
  return (
    <div className="space-y-2">
      <Button variant="primary" size="sm" onClick={onNew} className="w-full">
        <MessageSquarePlus className="w-4 h-4 mr-1.5" />
        Neue Unterhaltung
      </Button>

      {conversations.length === 0 && (
        <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
          Noch keine Unterhaltungen
        </p>
      )}

      <div className="space-y-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(conv.id)}
            onKeyDown={(e) => e.key === 'Enter' && onSelect(conv.id)}
            className={`group flex items-center gap-2 rounded-[var(--radius-sm)] px-3 py-2 text-sm cursor-pointer transition-colors ${
              activeId === conv.id
                ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)]'
                : 'text-[var(--color-text-base)] hover:bg-[var(--color-bg-neutral-subtle)]'
            }`}
          >
            <div className="flex-1 min-w-0">
              <div className="truncate font-medium">{conv.title}</div>
              <div className="text-[10px] text-[var(--color-text-muted)]">
                {formatDate(conv.updated_at)} · {conv.message_count} Nachrichten
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 !p-1 hover:bg-[var(--color-bg-error-subtle)] hover:text-[var(--color-text-error)]"
              aria-label={`${conv.title} löschen`}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
