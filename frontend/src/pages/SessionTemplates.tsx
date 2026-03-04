import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardBody,
  Button,
  Badge,
  Spinner,
  EmptyState,
  useToast,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import { Plus, EllipsisVertical, Copy, Trash2, ClipboardList, Footprints } from 'lucide-react';
import {
  listSessionTemplates,
  deleteSessionTemplate,
  duplicateSessionTemplate,
} from '@/api/session-templates';
import type { SessionTemplateSummary } from '@/api/session-templates';

export function SessionTemplatesPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [templates, setTemplates] = useState<SessionTemplateSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTemplates = useCallback(async () => {
    try {
      setLoading(true);
      const result = await listSessionTemplates();
      setTemplates(result.templates);
    } catch {
      toast({ title: 'Laden fehlgeschlagen', variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleDelete = async (templateId: number, name: string) => {
    try {
      await deleteSessionTemplate(templateId);
      toast({ title: `"${name}" gelöscht`, variant: 'success' });
      await loadTemplates();
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    }
  };

  const handleDuplicate = async (templateId: number) => {
    try {
      await duplicateSessionTemplate(templateId);
      toast({ title: 'Template dupliziert', variant: 'success' });
      await loadTemplates();
    } catch {
      toast({ title: 'Duplizieren fehlgeschlagen', variant: 'error' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Template List */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
              Vorlagen ({templates.length})
            </h2>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  aria-label="Aktionen"
                  className="inline-flex items-center justify-center w-8 h-8 rounded-[var(--radius-interactive)] text-[var(--color-text-muted)] hover:text-[var(--color-text-base)] hover:bg-[var(--color-bg-subtle)] transition-colors duration-150 motion-reduce:transition-none cursor-pointer"
                >
                  <EllipsisVertical className="w-4 h-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem icon={<Plus />} onSelect={() => navigate('/plan/templates/new')}>
                  Neues Template
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : templates.length === 0 ? (
            <EmptyState
              title="Noch keine Session-Templates"
              description="Erstelle dein erstes Template mit Übungen, Sätzen und Gewichten."
              action={
                <Button variant="primary" size="sm" onClick={() => navigate('/plan/templates/new')}>
                  <Plus className="w-4 h-4 mr-1" />
                  Template erstellen
                </Button>
              }
            />
          ) : (
            <div className="space-y-3">
              {templates.map((tmpl) => (
                <div
                  key={tmpl.id}
                  className="flex items-center gap-3 p-3 rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)] transition-colors motion-reduce:transition-none"
                >
                  {tmpl.session_type === 'running' ? (
                    <Footprints className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  ) : (
                    <ClipboardList className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  )}

                  <button
                    type="button"
                    onClick={() => navigate(`/plan/templates/${tmpl.id}`)}
                    className="flex-1 min-w-0 text-left"
                    aria-label={`${tmpl.name} bearbeiten`}
                  >
                    <span className="text-sm font-medium text-[var(--color-text-base)] truncate block">
                      {tmpl.name}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {tmpl.session_type === 'running'
                        ? (tmpl.run_type ?? 'Lauf-Template')
                        : `${tmpl.exercise_count} Übungen · ${tmpl.total_sets} Sätze`}
                    </span>
                  </button>

                  <Badge
                    variant={tmpl.session_type === 'strength' ? 'primary-bold' : 'accent'}
                    size="sm"
                  >
                    {tmpl.session_type === 'strength' ? 'Kraft' : 'Laufen'}
                  </Badge>

                  <DropdownMenu>
                    <DropdownMenuTrigger>
                      <button
                        type="button"
                        className="shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-[var(--radius-component-sm)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                        aria-label="Aktionen"
                      >
                        <EllipsisVertical className="w-4 h-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem icon={<Copy />} onSelect={() => handleDuplicate(tmpl.id)}>
                        Duplizieren
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        icon={<Trash2 />}
                        onSelect={() => handleDelete(tmpl.id, tmpl.name)}
                        className="text-[var(--color-text-error)]"
                      >
                        Löschen
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
