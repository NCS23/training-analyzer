import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Input,
  Select,
  Badge,
  Spinner,
  useToast,
  Breadcrumbs,
  BreadcrumbItem,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
  Textarea,
  MultiSelect,
  Label,
} from '@nordlig/components';
import {
  Star,
  Dumbbell,
  EllipsisVertical,
  Pencil,
  Trash2,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { categoryBadgeVariant } from '@/constants/training';
import { getExercise, toggleFavorite, updateExercise, deleteExercise } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import { MuscleMap } from '@/features/exercises/MuscleMap';
import { ExerciseDbPicker } from '@/features/exercises/ExerciseDbPicker';

const categoryLabels: Record<string, string> = {
  push: 'Push',
  pull: 'Pull',
  legs: 'Beine',
  core: 'Core',
  cardio: 'Cardio',
  drills: 'Lauf-ABC',
};

const categoryOptions = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'drills', label: 'Lauf-ABC' },
];

const equipmentLabels: Record<string, string> = {
  barbell: 'Langhantel',
  dumbbell: 'Kurzhantel',
  'body only': 'Körpergewicht',
  cable: 'Kabelzug',
  machine: 'Maschine',
  'e-z curl bar': 'EZ-Stange',
  'exercise ball': 'Gymnastikball',
  'foam roll': 'Faszienrolle',
  kettlebells: 'Kettlebell',
  bands: 'Widerstandsband',
  other: 'Sonstige',
};

const levelLabels: Record<string, string> = {
  beginner: 'Anfänger',
  intermediate: 'Fortgeschritten',
  expert: 'Experte',
};

const forceLabels: Record<string, string> = {
  push: 'Drücken',
  pull: 'Ziehen',
  static: 'Statisch',
};

const mechanicLabels: Record<string, string> = {
  compound: 'Mehrgelenkig',
  isolation: 'Eingelenkig',
};

const muscleLabels: Record<string, string> = {
  abdominals: 'Bauch',
  abductors: 'Abduktoren',
  adductors: 'Adduktoren',
  biceps: 'Bizeps',
  calves: 'Waden',
  chest: 'Brust',
  forearms: 'Unterarme',
  glutes: 'Gesäß',
  hamstrings: 'Beinbeuger',
  lats: 'Latissimus',
  'lower back': 'Unterer Rücken',
  'middle back': 'Mittlerer Rücken',
  neck: 'Nacken',
  quadriceps: 'Quadrizeps',
  shoulders: 'Schultern',
  traps: 'Trapezius',
  triceps: 'Trizeps',
};

const muscleOptions = Object.entries(muscleLabels)
  .map(([value, label]) => ({ value, label }))
  .sort((a, b) => a.label.localeCompare(b.label, 'de'));

// eslint-disable-next-line complexity, max-lines-per-function -- TODO: E16 Refactoring
export function ExerciseDetailPage() {
  const { exerciseId } = useParams<{ exerciseId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showDbPicker, setShowDbPicker] = useState(false);

  // Edit mode fields
  const [editName, setEditName] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editInstructions, setEditInstructions] = useState('');
  const [editPrimaryMuscles, setEditPrimaryMuscles] = useState<string[]>([]);
  const [editSecondaryMuscles, setEditSecondaryMuscles] = useState<string[]>([]);

  const enterEditMode = useCallback((ex: Exercise) => {
    setEditName(ex.name);
    setEditCategory(ex.category);
    setEditInstructions((ex.instructions ?? []).join('\n'));
    setEditPrimaryMuscles(ex.primary_muscles ?? []);
    setEditSecondaryMuscles(ex.secondary_muscles ?? []);
    setIsEditing(true);
  }, []);

  useEffect(() => {
    if (!exerciseId) return;
    setLoading(true);
    getExercise(Number(exerciseId))
      .then((ex) => {
        setExercise(ex);
        const params = new URLSearchParams(window.location.search);
        if (params.get('edit') === 'true') {
          enterEditMode(ex);
          navigate(`/plan/exercises/${exerciseId}`, { replace: true });
        }
      })
      .catch(() => {
        toast({ title: 'Übung nicht gefunden', variant: 'error' });
        navigate('/plan/exercises');
      })
      .finally(() => setLoading(false));
  }, [exerciseId, navigate, toast, enterEditMode]);

  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
  }, []);

  const handleSave = useCallback(async () => {
    if (!exercise) return;
    if (!editName.trim()) {
      toast({ title: 'Name darf nicht leer sein', variant: 'error' });
      return;
    }
    setSaving(true);
    try {
      const instructions = editInstructions
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const updated = await updateExercise(exercise.id, {
        name: editName.trim(),
        category: editCategory,
        instructions,
        primary_muscles: editPrimaryMuscles,
        secondary_muscles: editSecondaryMuscles,
      });
      setExercise(updated);
      setIsEditing(false);
      toast({ title: 'Übung gespeichert', variant: 'success' });
    } catch {
      toast({ title: 'Fehler beim Speichern', variant: 'error' });
    } finally {
      setSaving(false);
    }
  }, [
    exercise,
    editName,
    editCategory,
    editInstructions,
    editPrimaryMuscles,
    editSecondaryMuscles,
    toast,
  ]);

  const handleToggleFavorite = useCallback(async () => {
    if (!exercise) return;
    try {
      const updated = await toggleFavorite(exercise.id);
      setExercise(updated);
    } catch {
      toast({ title: 'Fehler beim Aktualisieren', variant: 'error' });
    }
  }, [exercise, toast]);

  const handleDelete = useCallback(async () => {
    if (!exercise) return;
    setDeleting(true);
    try {
      await deleteExercise(exercise.id);
      toast({ title: 'Übung gelöscht', variant: 'success' });
      navigate('/plan/exercises');
    } catch {
      toast({ title: 'Fehler beim Löschen', variant: 'error' });
      setDeleting(false);
    }
  }, [exercise, navigate, toast]);

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!exercise) return null;

  const hasMuscles =
    (exercise.primary_muscles && exercise.primary_muscles.length > 0) ||
    (exercise.secondary_muscles && exercise.secondary_muscles.length > 0);

  return (
    <div
      className={`p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6 ${isEditing ? 'pb-20' : ''}`}
    >
      {/* Breadcrumbs + Header (grouped for tighter spacing) */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan" className="hover:underline underline-offset-2">
              Plan
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/plan/exercises" className="hover:underline underline-offset-2">
              Übungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>{exercise.name}</BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)] truncate">
                {exercise.name}
              </h1>
              <Badge variant={categoryBadgeVariant[exercise.category] ?? 'neutral'} size="xs">
                {categoryLabels[exercise.category] ?? exercise.category}
              </Badge>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleToggleFavorite}
            aria-label={exercise.is_favorite ? 'Favorit entfernen' : 'Als Favorit markieren'}
          >
            <Star
              className={`w-5 h-5 transition-colors motion-reduce:transition-none ${
                exercise.is_favorite
                  ? 'text-[var(--color-status-warning)] fill-current'
                  : 'text-[var(--color-text-muted)]'
              }`}
            />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger>
              <Button variant="ghost" size="sm" aria-label="Aktionen" className="shrink-0">
                <EllipsisVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                icon={<Pencil />}
                disabled={isEditing}
                onSelect={() => enterEditMode(exercise)}
              >
                Bearbeiten
              </DropdownMenuItem>
              <DropdownMenuItem
                icon={<Sparkles />}
                disabled={isEditing}
                onSelect={() => setShowDbPicker(true)}
              >
                {exercise.exercise_db_id ? 'Zuordnung ändern' : 'Anreichern'}
              </DropdownMenuItem>
              {exercise.is_custom && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    icon={<Trash2 />}
                    destructive
                    onSelect={() => setShowDeleteConfirm(true)}
                  >
                    Löschen
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
      </div>

      {/* Details */}
      {(exercise.equipment || exercise.level || exercise.force || exercise.mechanic) && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {exercise.equipment && (
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Ausrüstung</span>
                  <p className="text-sm font-medium text-[var(--color-text-base)] mt-0.5">
                    <Dumbbell className="w-3.5 h-3.5 inline-block mr-1 align-text-bottom" />
                    {equipmentLabels[exercise.equipment] ?? exercise.equipment}
                  </p>
                </div>
              )}
              {exercise.level && (
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Schwierigkeit</span>
                  <p className="text-sm font-medium text-[var(--color-text-base)] mt-0.5">
                    {levelLabels[exercise.level] ?? exercise.level}
                  </p>
                </div>
              )}
              {exercise.force && (
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Kraft</span>
                  <p className="text-sm font-medium text-[var(--color-text-base)] mt-0.5">
                    {forceLabels[exercise.force] ?? exercise.force}
                  </p>
                </div>
              )}
              {exercise.mechanic && (
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Mechanik</span>
                  <p className="text-sm font-medium text-[var(--color-text-base)] mt-0.5">
                    {mechanicLabels[exercise.mechanic] ?? exercise.mechanic}
                  </p>
                </div>
              )}
            </div>
            {exercise.exercise_db_id && (
              <div className="flex items-center justify-between pt-3 mt-3 border-t border-[var(--color-border-default)]">
                <div className="min-w-0">
                  <span className="text-xs text-[var(--color-text-muted)]">
                    Datenbank-Zuordnung
                  </span>
                  <p className="text-sm text-[var(--color-text-base)] truncate">
                    {exercise.exercise_db_id.replace(/_/g, ' ')}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDbPicker(true)}
                  className="shrink-0 ml-3"
                >
                  Ändern
                </Button>
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Delete confirmation */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Übung löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              Diese Aktion kann nicht rückgängig gemacht werden. Die Übung wird unwiderruflich
              gelöscht.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Abbrechen</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={deleting}>
              {deleting ? <Spinner size="sm" /> : 'Löschen'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit: Name + Category */}
      {isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="edit-exercise-name">Name</Label>
                <Input
                  id="edit-exercise-name"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  inputSize="sm"
                  aria-label="Übungsname"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-exercise-category">Kategorie</Label>
                <Select
                  options={categoryOptions}
                  value={editCategory}
                  onChange={(val) => setEditCategory(val || editCategory)}
                  inputSize="sm"
                  aria-label="Kategorie"
                />
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* 1. Instructions */}
      {isEditing ? (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Anleitung</h2>
          </CardHeader>
          <CardBody className="space-y-1.5">
            <Textarea
              value={editInstructions}
              onChange={(e) => setEditInstructions(e.target.value)}
              placeholder="Ein Schritt pro Zeile…"
              rows={8}
              aria-label="Anleitung bearbeiten"
            />
            <p className="text-xs text-[var(--color-text-muted)]">
              Jede Zeile wird als ein Schritt dargestellt.
            </p>
          </CardBody>
        </Card>
      ) : (
        exercise.instructions &&
        exercise.instructions.length > 0 && (
          <Card elevation="raised" padding="spacious">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Anleitung</h2>
            </CardHeader>
            <CardBody>
              <ol className="space-y-3">
                {exercise.instructions.map((step, idx) => (
                  <li key={idx} className="flex gap-3">
                    <span className="shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-[var(--color-bg-subtle)] text-xs font-semibold text-[var(--color-text-muted)]">
                      {idx + 1}
                    </span>
                    <span className="text-sm text-[var(--color-text-base)] leading-relaxed">
                      {step}
                    </span>
                  </li>
                ))}
              </ol>
            </CardBody>
          </Card>
        )
      )}

      {/* 2. Muscles */}
      {isEditing ? (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Muskelgruppen</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <MuscleMap
              primaryMuscles={editPrimaryMuscles}
              secondaryMuscles={editSecondaryMuscles}
            />
            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label>Primäre Muskeln</Label>
                <MultiSelect
                  options={muscleOptions}
                  value={editPrimaryMuscles}
                  onChange={setEditPrimaryMuscles}
                  placeholder="Muskeln auswählen…"
                  inputSize="sm"
                  aria-label="Primäre Muskeln"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Sekundäre Muskeln</Label>
                <MultiSelect
                  options={muscleOptions}
                  value={editSecondaryMuscles}
                  onChange={setEditSecondaryMuscles}
                  placeholder="Muskeln auswählen…"
                  inputSize="sm"
                  aria-label="Sekundäre Muskeln"
                />
              </div>
            </div>
          </CardBody>
        </Card>
      ) : (
        hasMuscles && (
          <Card elevation="raised" padding="spacious">
            <CardHeader>
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Muskelgruppen</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <MuscleMap
                primaryMuscles={exercise.primary_muscles ?? []}
                secondaryMuscles={exercise.secondary_muscles ?? []}
              />
              <div className="border-t border-[var(--color-border-default)] pt-3 space-y-2">
                {exercise.primary_muscles && exercise.primary_muscles.length > 0 && (
                  <div className="border-l-2 border-[var(--color-status-error)] pl-3">
                    <span className="text-xs font-medium text-[var(--color-text-muted)] block">
                      Primär
                    </span>
                    <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                      {exercise.primary_muscles.map((m) => (
                        <span key={m} className="text-sm text-[var(--color-text-base)]">
                          {muscleLabels[m] ?? m}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {exercise.secondary_muscles && exercise.secondary_muscles.length > 0 && (
                  <div className="border-l-2 border-[var(--color-status-warning)] pl-3">
                    <span className="text-xs font-medium text-[var(--color-text-muted)] block">
                      Sekundär
                    </span>
                    <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                      {exercise.secondary_muscles.map((m) => (
                        <span key={m} className="text-sm text-[var(--color-text-base)]">
                          {muscleLabels[m] ?? m}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardBody>
          </Card>
        )
      )}

      {/* 3. Images */}
      {exercise.image_urls && exercise.image_urls.length > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Ausführung</h2>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 gap-4">
              {exercise.image_urls.map((url, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="rounded-[var(--radius-component-md)] overflow-hidden bg-[var(--color-bg-subtle)]">
                    <img
                      src={url}
                      alt={`${exercise.name} — ${idx === 0 ? 'Startposition' : 'Endposition'}`}
                      className="w-full h-auto object-cover"
                      loading="lazy"
                    />
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] text-center">
                    {idx === 0 ? 'Startposition' : 'Endposition'}
                  </p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* 5. Usage Stats */}
      {exercise.usage_count > 0 && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              <span>{exercise.usage_count}x in Trainings verwendet</span>
              {exercise.last_used_at && (
                <>
                  <span>·</span>
                  <span>
                    Zuletzt: {new Date(exercise.last_used_at).toLocaleDateString('de-DE')}
                  </span>
                </>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* No data placeholder — with action buttons */}
      {!isEditing &&
        !hasMuscles &&
        !exercise.instructions?.length &&
        !exercise.image_urls?.length && (
          <Card elevation="raised" padding="spacious">
            <CardBody>
              <div className="text-center py-6">
                <Dumbbell className="w-8 h-8 mx-auto text-[var(--color-text-muted)] mb-3" />
                <p className="text-sm text-[var(--color-text-muted)] mb-4">
                  Keine Details verfügbar für diese Übung.
                </p>
                <div className="flex flex-col sm:flex-row justify-center gap-2">
                  <Button variant="secondary" size="sm" onClick={() => setShowDbPicker(true)}>
                    <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                    Daten anreichern
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => enterEditMode(exercise)}>
                    <Pencil className="w-3.5 h-3.5 mr-1.5" />
                    Manuell bearbeiten
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

      {/* Fixed edit mode bar — fixed instead of sticky to work with overflow-x-hidden parent */}
      {isEditing && (
        <div
          role="toolbar"
          className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40 bg-[var(--color-actionbar-bg)] border-t border-[var(--color-actionbar-border)] rounded-t-[var(--radius-actionbar)] [box-shadow:var(--shadow-actionbar-default)] px-[var(--spacing-actionbar-padding-x)] py-[var(--spacing-actionbar-padding-y)] flex items-center justify-between gap-[var(--spacing-actionbar-gap)]"
        >
          <span className="text-xs text-[var(--color-actionbar-text)] hidden sm:inline">
            Ungespeicherte Änderungen
          </span>
          <div className="flex gap-2 ml-auto">
            <Button variant="ghost" size="sm" onClick={handleCancelEdit} disabled={saving}>
              Abbrechen
            </Button>
            <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
              {saving ? <Spinner size="sm" /> : 'Speichern'}
            </Button>
          </div>
        </div>
      )}

      {/* Exercise DB Picker */}
      <ExerciseDbPicker
        open={showDbPicker}
        onOpenChange={setShowDbPicker}
        exerciseId={exercise.id}
        currentDbId={exercise.exercise_db_id}
        onEnriched={(updated) => setExercise(updated)}
      />
    </div>
  );
}
