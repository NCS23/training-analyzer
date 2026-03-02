import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Input,
  Label,
  Select,
  Badge,
  Spinner,
  EmptyState,
  useToast,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  Breadcrumbs,
  BreadcrumbItem,
} from '@nordlig/components';
import { Plus, Star, ChevronRight, EllipsisVertical } from 'lucide-react';
import { categoryBadgeVariant } from '@/constants/training';
import { listExercises, createExercise, toggleFavorite } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';

const categoryOptions = [
  { value: '', label: 'Alle Kategorien' },
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
];

const createCategoryOptions = categoryOptions.filter((o) => o.value !== '');

const categoryLabels: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
};



export function ExerciseLibraryPage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);

  // Create dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState('push');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadExercises = useCallback(async () => {
    try {
      setLoading(true);
      const result = await listExercises({
        category: category || undefined,
        search: search.trim() || undefined,
        favoritesOnly,
      });
      setExercises(result.exercises);
    } catch {
      toast({ title: 'Laden fehlgeschlagen', variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [category, search, favoritesOnly, toast]);

  useEffect(() => {
    loadExercises();
  }, [loadExercises]);

  const handleCreate = async () => {
    if (!newName.trim()) {
      setCreateError('Name darf nicht leer sein');
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      await createExercise({ name: newName.trim(), category: newCategory });
      toast({ title: 'Übung erstellt', variant: 'success' });
      setNewName('');
      setNewCategory('push');
      setShowCreateDialog(false);
      await loadExercises();
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setCreateError(msg || 'Erstellen fehlgeschlagen');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleFavorite = async (ex: Exercise) => {
    try {
      await toggleFavorite(ex.id);
      await loadExercises();
    } catch {
      toast({ title: 'Fehler beim Aktualisieren', variant: 'error' });
    }
  };

  return (
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      {/* Breadcrumbs + Header (grouped for tighter spacing) */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/settings" className="hover:underline underline-offset-2">
              Einstellungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Übungsbibliothek</BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
              Übungsbibliothek
            </h1>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              Übungen verwalten, Favoriten setzen, eigene Übungen hinzufügen.
            </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger>
              <button
                type="button"
                className="shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-[var(--radius-component-sm)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                aria-label="Aktionen"
              >
                <EllipsisVertical className="w-5 h-5" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                icon={<Plus />}
                onSelect={() => {
                  setShowCreateDialog(true);
                  setCreateError(null);
                  setNewName('');
                  setNewCategory('push');
                }}
              >
                Neue Übung
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
      </div>

      {/* Filters */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Übung suchen…"
                inputSize="sm"
                aria-label="Suche"
              />
            </div>
            <div className="w-full sm:w-40">
              <Select
                options={categoryOptions}
                value={category}
                onChange={(val) => setCategory(val || '')}
                inputSize="sm"
                aria-label="Kategorie-Filter"
              />
            </div>
            <Button
              variant={favoritesOnly ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setFavoritesOnly(!favoritesOnly)}
              aria-label={favoritesOnly ? 'Alle anzeigen' : 'Nur Favoriten'}
            >
              <Star className={`w-4 h-4 ${favoritesOnly ? 'fill-current' : ''}`} />
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Create dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Neue Übung erstellen</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="create-exercise-name">Name</Label>
              <Input
                id="create-exercise-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Übungsname…"
                inputSize="sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreate();
                }}
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="create-exercise-category">Kategorie</Label>
              <Select
                options={createCategoryOptions}
                value={newCategory}
                onChange={(val) => setNewCategory(val || 'push')}
                inputSize="sm"
                aria-label="Kategorie"
              />
            </div>
            {createError && <p className="text-sm text-[var(--color-text-error)]">{createError}</p>}
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => setShowCreateDialog(false)}>
              Abbrechen
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreate} disabled={creating}>
              {creating ? <Spinner size="sm" aria-hidden="true" /> : 'Erstellen'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Exercise List */}
      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Übungen ({exercises.length})
          </h2>
        </CardHeader>
        <CardBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : exercises.length === 0 ? (
            <EmptyState
              title="Keine Übungen gefunden"
              description={
                search || category
                  ? 'Versuche andere Filter oder erstelle eine neue Übung.'
                  : 'Erstelle deine erste eigene Übung.'
              }
            />
          ) : (
            <div className="space-y-1">
              {exercises.map((ex) => (
                <div
                  key={ex.id}
                  className="flex items-center gap-3 py-2.5 px-3 rounded-[var(--radius-component-sm)] hover:bg-[var(--color-bg-hover)] transition-colors motion-reduce:transition-none"
                >
                  <button
                    type="button"
                    onClick={() => handleToggleFavorite(ex)}
                    className="shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center"
                    aria-label={ex.is_favorite ? 'Favorit entfernen' : 'Als Favorit markieren'}
                  >
                    <Star
                      className={`w-4 h-4 transition-colors motion-reduce:transition-none ${
                        ex.is_favorite
                          ? 'text-[var(--color-status-warning)] fill-current'
                          : 'text-[var(--color-text-muted)]'
                      }`}
                    />
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate(`/settings/exercises/${ex.id}`)}
                    className="flex-1 min-w-0 text-left"
                    aria-label={`${ex.name} Details anzeigen`}
                  >
                    <span className="text-sm font-medium text-[var(--color-text-base)] truncate block">
                      {ex.name}
                    </span>
                    {ex.usage_count > 0 && (
                      <span className="text-xs text-[var(--color-text-muted)]">
                        {ex.usage_count}x verwendet
                      </span>
                    )}
                  </button>

                  <Badge variant={categoryBadgeVariant[ex.category] ?? 'neutral'} size="sm">
                    {categoryLabels[ex.category] ?? ex.category}
                  </Badge>

                  <ChevronRight className="w-4 h-4 shrink-0 text-[var(--color-text-muted)]" />
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
