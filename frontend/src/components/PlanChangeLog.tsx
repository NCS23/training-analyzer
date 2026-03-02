import { useState, useEffect, useCallback } from 'react';
import { Card, CardBody, Button, Spinner, Input, useToast } from '@nordlig/components';
import {
  FilePlus,
  Pencil,
  Plus,
  Settings2,
  Trash2,
  CalendarPlus,
  ArrowUpToLine,
  PenLine,
  Upload,
  Dumbbell,
  ChevronDown,
  ChevronUp,
  MessageSquarePlus,
} from 'lucide-react';
import { getChangelog, updateChangelogReason } from '@/api/training-plans';
import type { PlanChangeLogEntry } from '@/api/training-plans';

const PAGE_SIZE = 20;

const CHANGE_TYPE_ICONS: Record<string, React.ReactNode> = {
  plan_created: <FilePlus className="w-3.5 h-3.5" />,
  plan_updated: <Pencil className="w-3.5 h-3.5" />,
  phase_added: <Plus className="w-3.5 h-3.5" />,
  phase_updated: <Settings2 className="w-3.5 h-3.5" />,
  phase_deleted: <Trash2 className="w-3.5 h-3.5" />,
  weekly_generated: <CalendarPlus className="w-3.5 h-3.5" />,
  back_sync: <ArrowUpToLine className="w-3.5 h-3.5" />,
  manual_edit: <PenLine className="w-3.5 h-3.5" />,
  yaml_import: <Upload className="w-3.5 h-3.5" />,
  session_configured: <Dumbbell className="w-3.5 h-3.5" />,
};

function formatRelativeTime(isoDate: string): string {
  const now = new Date();
  const date = new Date(isoDate);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'gerade eben';
  if (diffMin < 60) return `vor ${diffMin} Min.`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `vor ${diffH} Std.`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 7) return `vor ${diffD} Tag${diffD > 1 ? 'en' : ''}`;
  return date.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' });
}

interface PlanChangeLogProps {
  planId: number;
}

export function PlanChangeLog({ planId }: PlanChangeLogProps) {
  const { toast } = useToast();
  const [entries, setEntries] = useState<PlanChangeLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingReasonId, setEditingReasonId] = useState<number | null>(null);
  const [reasonInput, setReasonInput] = useState('');

  const loadEntries = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getChangelog(planId, PAGE_SIZE, 0);
      setEntries(result.entries);
      setTotal(result.total);
    } catch {
      // silently fail — changelog is non-critical
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  const handleLoadMore = async () => {
    setLoadingMore(true);
    try {
      const result = await getChangelog(planId, PAGE_SIZE, entries.length);
      setEntries((prev) => [...prev, ...result.entries]);
      setTotal(result.total);
    } catch {
      toast({ title: 'Laden fehlgeschlagen', variant: 'error' });
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSaveReason = async (logId: number) => {
    if (!reasonInput.trim()) return;
    try {
      const updated = await updateChangelogReason(planId, logId, reasonInput.trim());
      setEntries((prev) => prev.map((e) => (e.id === logId ? updated : e)));
      setEditingReasonId(null);
      setReasonInput('');
    } catch {
      toast({ title: 'Speichern fehlgeschlagen', variant: 'error' });
    }
  };

  const hasMore = entries.length < total;

  return (
    <Card elevation="raised" padding="spacious">
      <CardBody>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between -m-1 p-1"
        >
          <span className="text-sm font-semibold text-[var(--color-text-base)]">
            Aenderungshistorie{total > 0 && ` (${total})`}
          </span>
          {isOpen ? (
            <ChevronUp className="w-4 h-4 text-[var(--color-text-muted)]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[var(--color-text-muted)]" />
          )}
        </Button>

        <div
          className={`overflow-hidden transition-all duration-300 motion-reduce:transition-none ${
            isOpen ? 'max-h-[2000px] mt-3' : 'max-h-0'
          }`}
        >
          {loading ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          ) : entries.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
              Noch keine Aenderungen protokolliert.
            </p>
          ) : (
            <div className="space-y-1" role="list" aria-label="Aenderungshistorie">
              {entries.map((entry) => {
                const isExpanded = expandedId === entry.id;
                const isEditingReason = editingReasonId === entry.id;

                return (
                  <div key={entry.id} role="listitem">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                      className="w-full flex items-center gap-2 text-left px-2 py-1.5 min-h-[36px]"
                    >
                      <span className="text-[var(--color-text-muted)] shrink-0">
                        {CHANGE_TYPE_ICONS[entry.change_type] ?? <Pencil className="w-3.5 h-3.5" />}
                      </span>
                      <span className="text-xs text-[var(--color-text-base)] flex-1 truncate">
                        {entry.summary}
                      </span>
                      <span className="text-xs text-[var(--color-text-muted)] shrink-0">
                        {formatRelativeTime(entry.created_at)}
                      </span>
                    </Button>

                    {isExpanded && (
                      <div className="pl-8 pr-2 pb-2 space-y-2">
                        {entry.details && (
                          <pre className="text-xs text-[var(--color-text-muted)] bg-[var(--color-bg-surface)] rounded-[var(--radius-component-sm)] p-2 overflow-x-auto">
                            {JSON.stringify(entry.details, null, 2)}
                          </pre>
                        )}

                        {entry.reason && !isEditingReason && (
                          <p className="text-xs text-[var(--color-text-muted)]">
                            <span className="font-medium">Grund:</span> {entry.reason}
                          </p>
                        )}

                        {isEditingReason ? (
                          <div className="flex gap-2">
                            <Input
                              value={reasonInput}
                              onChange={(e) => setReasonInput(e.target.value)}
                              placeholder="Grund eingeben..."
                              inputSize="sm"
                              autoFocus
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveReason(entry.id);
                                if (e.key === 'Escape') {
                                  setEditingReasonId(null);
                                  setReasonInput('');
                                }
                              }}
                            />
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleSaveReason(entry.id)}
                              disabled={!reasonInput.trim()}
                            >
                              OK
                            </Button>
                          </div>
                        ) : (
                          !entry.reason && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setEditingReasonId(entry.id);
                                setReasonInput('');
                              }}
                              className="text-xs"
                            >
                              <MessageSquarePlus className="w-3 h-3 mr-1" />
                              Grund hinzufuegen
                            </Button>
                          )
                        )}
                      </div>
                    )}
                  </div>
                );
              })}

              {hasMore && (
                <div className="pt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="w-full"
                  >
                    {loadingMore ? <Spinner size="sm" /> : 'Mehr laden'}
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
