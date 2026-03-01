import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Badge,
  Spinner,
  EmptyState,
  useToast,
  Breadcrumbs,
  BreadcrumbItem,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import {
  Plus,
  ChevronRight,
  EllipsisVertical,
  Copy,
  Trash2,
  ClipboardList,
  Footprints,
} from 'lucide-react';
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
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumbs + Header */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/settings" className="hover:underline underline-offset-2">
              Einstellungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Session-Templates</BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex flex-wrap items-start justify-between gap-y-3">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
              Session-Templates
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              Vorlagen für Kraft- und Lauftraining erstellen und verwalten.
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/settings/templates/new')}
          >
            <Plus className="w-4 h-4 mr-1" />
            Neues Template
          </Button>
        </header>
      </div>

      {/* Template List */}
      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Templates ({templates.length})
          </h2>
        </CardHeader>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : templates.length === 0 ? (
            <EmptyState
              title="Noch keine Session-Templates"
              description="Erstelle dein erstes Template mit Übungen, Sätzen und Gewichten."
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate('/settings/templates/new')}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Template erstellen
                </Button>
              }
            />
          ) : (
            <div className="space-y-1">
              {templates.map((tmpl) => (
                <div
                  key={tmpl.id}
                  className="flex items-center gap-3 py-2.5 px-3 rounded-[var(--radius-component-sm)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                >
                  {tmpl.session_type === 'running' ? (
                    <Footprints className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  ) : (
                    <ClipboardList className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  )}

                  <button
                    type="button"
                    onClick={() => navigate(`/settings/templates/${tmpl.id}`)}
                    className="flex-1 min-w-0 text-left"
                    aria-label={`${tmpl.name} bearbeiten`}
                  >
                    <span className="text-sm font-medium text-[var(--color-text-base)] truncate block">
                      {tmpl.name}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {tmpl.session_type === 'running'
                        ? tmpl.run_type ?? 'Lauf-Template'
                        : `${tmpl.exercise_count} Übungen · ${tmpl.total_sets} Sätze`}
                    </span>
                  </button>

                  <Badge variant="neutral" size="sm">
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
                      <DropdownMenuItem
                        icon={<Copy />}
                        onSelect={() => handleDuplicate(tmpl.id)}
                      >
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
