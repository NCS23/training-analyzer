import { useEffect, useState } from 'react';
import { Button, Dialog, DialogContent, DialogHeader, DialogTitle } from '@nordlig/components';
import { Dumbbell, Footprints, Loader2 } from 'lucide-react';
import { listSessionTemplates, type SessionTemplateSummary } from '@/api/session-templates';

const RUN_TYPE_LABELS: Record<string, string> = {
  recovery: 'Regeneration',
  easy: 'Lockerer Lauf',
  long_run: 'Langer Lauf',
  progression: 'Steigerungslauf',
  tempo: 'Tempolauf',
  intervals: 'Intervalle',
  repetitions: 'Repetitions',
  fartlek: 'Fahrtspiel',
  race: 'Wettkampf',
};

interface TemplatePickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sessionType: string;
  onSelect: (template: SessionTemplateSummary | null) => void;
}

export function TemplatePickerDialog({
  open,
  onOpenChange,
  sessionType,
  onSelect,
}: TemplatePickerDialogProps) {
  const [templates, setTemplates] = useState<SessionTemplateSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    listSessionTemplates(sessionType)
      .then((res) => setTemplates(res.templates))
      .catch(() => setTemplates([]))
      .finally(() => setLoading(false));
  }, [open, sessionType]);

  const handleSelect = (template: SessionTemplateSummary | null) => {
    onSelect(template);
    onOpenChange(false);
  };

  const typeLabel = sessionType === 'running' ? 'Lauf' : 'Kraft';
  const TypeIcon = sessionType === 'running' ? Footprints : Dumbbell;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            <TypeIcon className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
            {typeLabel}-Vorlage waehlen
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-1.5 max-h-[50vh] overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="w-5 h-5 animate-spin text-[var(--color-text-muted)]" />
            </div>
          )}

          {!loading && templates.length === 0 && (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
              Keine Vorlagen vorhanden.
            </p>
          )}

          {!loading &&
            templates.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => handleSelect(t)}
                className={[
                  'flex items-center justify-between w-full text-left px-3 py-2.5',
                  'rounded-[var(--radius-component-sm)]',
                  'hover:bg-[var(--color-bg-surface-hover)]',
                  'transition-colors duration-100 motion-reduce:transition-none',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)]',
                ].join(' ')}
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[var(--color-text-base)] truncate">
                    {t.name}
                  </p>
                  <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    {sessionType === 'running' && t.run_type
                      ? (RUN_TYPE_LABELS[t.run_type] ?? t.run_type)
                      : sessionType === 'strength'
                        ? `${t.exercise_count} Uebungen · ${t.total_sets} Saetze`
                        : ''}
                  </p>
                </div>
              </button>
            ))}
        </div>

        <div className="pt-2 border-t border-[var(--color-border-muted)]">
          <Button variant="ghost" size="sm" className="w-full" onClick={() => handleSelect(null)}>
            Ohne Vorlage
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
