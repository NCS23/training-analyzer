import { useState, useEffect, useCallback } from 'react';
import { Card, CardBody, Button, Badge, Spinner, Input, useToast } from '@nordlig/components';
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
  ArrowRight,
  Bot,
  Monitor,
} from 'lucide-react';
import { getChangelog, updateChangelogReason } from '@/api/training-plans';
import type {
  PlanChangeLogEntry,
  ChangelogCategory,
  FieldChange,
  DayChange,
} from '@/api/training-plans';

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

type CategoryFilter = ChangelogCategory | 'all';

const CATEGORY_TABS: { key: CategoryFilter; label: string }[] = [
  { key: 'all', label: 'Alle' },
  { key: 'content', label: 'Inhaltlich' },
  { key: 'structure', label: 'Struktur' },
  { key: 'technical', label: 'Technisch' },
  { key: 'meta', label: 'Meta' },
];

const CATEGORY_BADGE_VARIANT: Record<string, 'primary' | 'accent' | 'info' | 'neutral'> = {
  content: 'primary',
  structure: 'accent',
  technical: 'info',
  meta: 'neutral',
};

const CATEGORY_LABELS: Record<string, string> = {
  content: 'Inhaltlich',
  structure: 'Struktur',
  technical: 'Technisch',
  meta: 'Meta',
};

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  system: <Monitor className="w-3 h-3" />,
  ai_suggestion: <Bot className="w-3 h-3" />,
  compliance_check: <Bot className="w-3 h-3" />,
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

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return '–';
  if (typeof val === 'boolean') return val ? 'Ja' : 'Nein';
  return String(val);
}

function FieldChangesPanel({ changes }: { changes: FieldChange[] }) {
  return (
    <div className="space-y-1">
      {changes.map((fc, i) => (
        <div key={i} className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          <span className="font-medium text-[var(--color-text-base)]">{fc.label}:</span>
          <span>{formatValue(fc.from)}</span>
          <ArrowRight className="w-3 h-3 shrink-0 text-[var(--color-text-muted)]" />
          <span className="font-medium text-[var(--color-text-base)]">{formatValue(fc.to)}</span>
        </div>
      ))}
    </div>
  );
}

function DayChangesPanel({ days }: { days: DayChange[] }) {
  return (
    <div className="space-y-2">
      {days.map((day, i) => (
        <div key={i}>
          <p className="text-xs font-medium text-[var(--color-text-base)]">{day.day_name}</p>
          <div className="pl-3 mt-0.5">
            <FieldChangesPanel changes={day.field_changes} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ChangelogDetailsPanel({ entry }: { entry: PlanChangeLogEntry }) {
  const details = entry.details;
  if (!details) return null;

  const source = details.source as string | undefined;
  const showSourceIndicator = source && source !== 'user' && SOURCE_ICONS[source];

  return (
    <div className="space-y-2">
      {showSourceIndicator && (
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          {SOURCE_ICONS[source]}
          <span className="capitalize">{source === 'ai_suggestion' ? 'KI-Vorschlag' : source === 'system' ? 'System' : source}</span>
        </div>
      )}

      {details.field_changes && details.field_changes.length > 0 && (
        <FieldChangesPanel changes={details.field_changes} />
      )}

      {details.changed_days && details.changed_days.length > 0 && (
        <DayChangesPanel days={details.changed_days} />
      )}

      {/* Legacy: flat changed_fields array */}
      {!details.field_changes && !details.changed_days && details.changed_fields && (
        <p className="text-xs text-[var(--color-text-muted)]">
          Geaendert: {(details.changed_fields as string[]).join(', ')}
        </p>
      )}

      {/* Fallback: key-value pairs for unknown structures */}
      {!details.field_changes && !details.changed_days && !details.changed_fields && (
        <div className="space-y-0.5">
          {Object.entries(details)
            .filter(([k]) => !['source', 'category'].includes(k))
            .map(([k, v]) => (
              <p key={k} className="text-xs text-[var(--color-text-muted)]">
                <span className="font-medium text-[var(--color-text-base)]">{k}:</span>{' '}
                {typeof v === 'object' ? JSON.stringify(v) : formatValue(v)}
              </p>
            ))}
        </div>
      )}
    </div>
  );
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
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all');

  const loadEntries = useCallback(async () => {
    setLoading(true);
    try {
      const cat = categoryFilter === 'all' ? undefined : categoryFilter;
      const result = await getChangelog(planId, PAGE_SIZE, 0, cat);
      setEntries(result.entries);
      setTotal(result.total);
    } catch {
      // silently fail — changelog is non-critical
    } finally {
      setLoading(false);
    }
  }, [planId, categoryFilter]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  const handleLoadMore = async () => {
    setLoadingMore(true);
    try {
      const cat = categoryFilter === 'all' ? undefined : categoryFilter;
      const result = await getChangelog(planId, PAGE_SIZE, entries.length, cat);
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

  const handleCategoryChange = (cat: CategoryFilter) => {
    setCategoryFilter(cat);
    setExpandedId(null);
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
          {/* Category filter tabs */}
          <div className="flex gap-1 mb-3 flex-wrap" role="tablist" aria-label="Kategorie-Filter">
            {CATEGORY_TABS.map((tab) => (
              <Button
                key={tab.key}
                variant={categoryFilter === tab.key ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => handleCategoryChange(tab.key)}
                role="tab"
                aria-selected={categoryFilter === tab.key}
                className="text-xs"
              >
                {tab.label}
              </Button>
            ))}
          </div>

          {loading ? (
            <div className="flex justify-center py-4">
              <Spinner size="sm" />
            </div>
          ) : entries.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
              {categoryFilter === 'all'
                ? 'Noch keine Aenderungen protokolliert.'
                : 'Keine Eintraege in dieser Kategorie.'}
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
                      {entry.category && (
                        <Badge
                          variant={CATEGORY_BADGE_VARIANT[entry.category] ?? 'neutral'}
                          size="xs"
                          className="shrink-0"
                        >
                          {CATEGORY_LABELS[entry.category] ?? entry.category}
                        </Badge>
                      )}
                      <span className="text-xs text-[var(--color-text-muted)] shrink-0">
                        {formatRelativeTime(entry.created_at)}
                      </span>
                    </Button>

                    {isExpanded && (
                      <div className="pl-8 pr-2 pb-2 space-y-2">
                        {entry.reason && !isEditingReason && (
                          <p className="text-xs text-[var(--color-text-muted)]">
                            <span className="font-medium text-[var(--color-text-base)]">Grund:</span>{' '}
                            {entry.reason}
                          </p>
                        )}

                        <ChangelogDetailsPanel entry={entry} />

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
