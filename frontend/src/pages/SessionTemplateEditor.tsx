import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import {
  Button,
  Card,
  CardBody,
  Input,
  NumberInput,
  Select,
  Label,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
  useToast,
  Breadcrumbs,
  BreadcrumbItem,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@nordlig/components';
import {
  Dumbbell,
  Footprints,
  Plus,
  Trash2,
  Save,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  GripVertical,
  Pencil,
  EllipsisVertical,
} from 'lucide-react';
import {
  createSessionTemplate,
  getSessionTemplate,
  updateSessionTemplate,
} from '@/api/session-templates';
import type { ExerciseCategory } from '@/api/session-templates';
import type { RunDetails } from '@/api/weekly-plan';
import { createEmptySegment } from '@/api/segment';
import { categoryBadgeVariant, trainingTypeOptions } from '@/constants/training';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import { RunDetailsEditor } from '@/components/RunDetailsEditor';
import {
  type ExerciseForm,
  CATEGORY_OPTIONS,
  CATEGORY_LABELS,
  EXERCISE_TYPE_OPTIONS,
  createDefaultExercise,
  exerciseFormToApi,
  apiExerciseToForm,
} from '@/utils/exercise-helpers';

// --- Types ---

/** Supported template session types. Extensible for future types. */
type TemplateSessionType = 'strength' | 'running';

const SESSION_TYPE_OPTIONS: { value: TemplateSessionType; label: string; icon: string }[] = [
  { value: 'strength', label: 'Kraft', icon: 'dumbbell' },
  { value: 'running', label: 'Laufen', icon: 'footprints' },
];

const RUN_TYPE_OPTIONS = trainingTypeOptions.map((opt) => ({
  value: opt.value,
  label: opt.label,
}));

// --- Component ---

export function SessionTemplateEditorPage() {
  const navigate = useNavigate();
  const { templateId } = useParams<{ templateId: string }>();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const isEdit = templateId != null && templateId !== 'new';
  const [editMode, setEditMode] = useState(() => searchParams.get('edit') === 'true');
  const isEditing = !isEdit || editMode;

  // Form state — shared
  const [templateName, setTemplateName] = useState('');
  const [description, setDescription] = useState('');
  const [sessionType, setSessionType] = useState<TemplateSessionType>('strength');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(isEdit);
  const [error, setError] = useState<string | null>(null);

  // Strength-specific state
  const [exercises, setExercises] = useState<ExerciseForm[]>([createDefaultExercise()]);

  // Running-specific state
  const [runType, setRunType] = useState<string>('easy');
  const [runDetails, setRunDetails] = useState<RunDetails | null>(null);

  // Exercise library for suggestions
  const [libraryExercises, setLibraryExercises] = useState<Exercise[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<string | null>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Load exercise library (only needed for strength)
  useEffect(() => {
    if (sessionType !== 'strength' && !isEdit) return;
    listExercises()
      .then((res) => setLibraryExercises(res.exercises))
      .catch(() => {});
  }, [sessionType, isEdit]);

  // Load existing template for edit mode
  const loadTemplate = useCallback(async () => {
    if (!templateId) return;
    try {
      const tmpl = await getSessionTemplate(Number(templateId));
      setTemplateName(tmpl.name);
      setDescription(tmpl.description ?? '');
      setSessionType(tmpl.session_type as TemplateSessionType);

      if (tmpl.session_type === 'strength') {
        if (tmpl.exercises.length > 0) {
          setExercises(tmpl.exercises.map(apiExerciseToForm));
        }
      } else if (tmpl.session_type === 'running' && tmpl.run_details) {
        setRunType(tmpl.run_details.run_type);
        setRunDetails(tmpl.run_details);
      }
    } catch {
      toast({ title: 'Template nicht gefunden', variant: 'error' });
      navigate('/plan/templates');
    } finally {
      setLoading(false);
    }
  }, [templateId, navigate, toast]);

  useEffect(() => {
    if (isEdit) loadTemplate();
  }, [isEdit, loadTemplate]);

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (suggestionsRef.current && !suggestionsRef.current.contains(e.target as Node)) {
        setShowSuggestions(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // --- Run Details handling ---

  const handleRunTypeChange = useCallback((newType: string | undefined) => {
    if (!newType) return;
    setRunType(newType);
    // Preserve existing details but update run_type
    setRunDetails((prev) =>
      prev ? { ...prev, run_type: newType as RunDetails['run_type'] } : null,
    );
  }, []);

  const handleRunDetailsChange = useCallback(
    (details: RunDetails | null) => {
      if (details) {
        setRunDetails({ ...details, run_type: runType as RunDetails['run_type'] });
      } else {
        setRunDetails(null);
      }
    },
    [runType],
  );

  // --- Exercise CRUD ---

  const updateExercise = useCallback((exerciseId: string, updates: Partial<ExerciseForm>) => {
    setExercises((prev) => prev.map((ex) => (ex.id === exerciseId ? { ...ex, ...updates } : ex)));
  }, []);

  const removeExercise = useCallback((exerciseId: string) => {
    setExercises((prev) => {
      const filtered = prev.filter((ex) => ex.id !== exerciseId);
      return filtered.length === 0 ? [createDefaultExercise()] : filtered;
    });
  }, []);

  const addExercise = useCallback(() => {
    setExercises((prev) => [...prev, createDefaultExercise()]);
  }, []);

  const moveExercise = useCallback((index: number, direction: -1 | 1) => {
    setExercises((prev) => {
      const newIndex = index + direction;
      if (newIndex < 0 || newIndex >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[newIndex]] = [next[newIndex], next[index]];
      return next;
    });
  }, []);

  // --- Exercise name suggestions ---

  const getFilteredSuggestions = useCallback(
    (query: string): Exercise[] => {
      if (!query.trim()) return libraryExercises.slice(0, 10);
      const lower = query.toLowerCase();
      return libraryExercises.filter((ex) => ex.name.toLowerCase().includes(lower)).slice(0, 8);
    },
    [libraryExercises],
  );

  const selectSuggestion = useCallback(
    (exerciseId: string, exercise: Exercise) => {
      const categoryMap: Record<string, ExerciseCategory> = {
        push: 'push',
        pull: 'pull',
        legs: 'legs',
        core: 'core',
        cardio: 'cardio',
      };
      updateExercise(exerciseId, {
        name: exercise.name,
        category: categoryMap[exercise.category] ?? 'push',
      });
      setShowSuggestions(null);
    },
    [updateExercise],
  );

  // --- Submit ---

  const handleSubmit = useCallback(async () => {
    if (!templateName.trim()) {
      setError('Template-Name darf nicht leer sein.');
      return;
    }

    // Type-specific validation
    if (sessionType === 'strength') {
      const validExercises = exercises.filter((ex) => ex.name.trim());
      if (validExercises.length === 0) {
        setError('Mindestens eine Übung mit Namen erforderlich.');
        return;
      }
    }

    setSubmitting(true);
    setError(null);

    try {
      if (sessionType === 'strength') {
        const validExercises = exercises.filter((ex) => ex.name.trim());
        if (isEdit) {
          await updateSessionTemplate(Number(templateId), {
            name: templateName.trim(),
            description: description.trim() || undefined,
            exercises: validExercises.map(exerciseFormToApi),
          });
        } else {
          await createSessionTemplate({
            name: templateName.trim(),
            description: description.trim() || undefined,
            session_type: 'strength',
            exercises: validExercises.map(exerciseFormToApi),
          });
        }
      } else {
        // Running (and future types that use run_details)
        const details: RunDetails = runDetails ?? {
          run_type: runType as RunDetails['run_type'],
          target_duration_minutes: null,
          target_pace_min: null,
          target_pace_max: null,
          target_hr_min: null,
          target_hr_max: null,
          intervals: null,
          segments: [createEmptySegment(0, { segment_type: 'steady' })],
        };

        if (isEdit) {
          await updateSessionTemplate(Number(templateId), {
            name: templateName.trim(),
            description: description.trim() || undefined,
            run_details: { ...details, run_type: runType as RunDetails['run_type'] },
          });
        } else {
          await createSessionTemplate({
            name: templateName.trim(),
            description: description.trim() || undefined,
            session_type: sessionType,
            run_details: { ...details, run_type: runType as RunDetails['run_type'] },
          });
        }
      }

      toast({ title: isEdit ? 'Template aktualisiert' : 'Template erstellt', variant: 'success' });
      navigate('/plan/templates');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Speichern.');
    } finally {
      setSubmitting(false);
    }
  }, [
    templateName,
    description,
    sessionType,
    exercises,
    runType,
    runDetails,
    isEdit,
    templateId,
    navigate,
    toast,
  ]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div
      className={`p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6${isEditing ? ' pb-24' : ''}`}
    >
      {/* Breadcrumbs + Header */}
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/plan" className="hover:underline underline-offset-2">
              Plan
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <Link to="/plan/templates" className="hover:underline underline-offset-2">
              Vorlagen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>
            {isEdit ? templateName || 'Template' : 'Neues Template'}
          </BreadcrumbItem>
        </Breadcrumbs>
        <header className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl md:text-2xl font-semibold text-[var(--color-text-base)]">
              {!isEdit
                ? 'Neues Session-Template'
                : isEditing
                  ? 'Template bearbeiten'
                  : templateName}
            </h1>
            {isEditing && (
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                {sessionType === 'strength'
                  ? 'Übungen, Sätze und Gewichte als Vorlage definieren.'
                  : 'Lauftyp, Dauer, Pace und Segmente als Vorlage definieren.'}
              </p>
            )}
          </div>
          {isEdit && (
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
                  onSelect={() => setEditMode(true)}
                >
                  Bearbeiten
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </header>
      </div>

      {isEditing && error && (
        <Alert variant="error">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Template Meta */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          {isEditing ? (
            <div className="space-y-4">
              {/* Session Type Selector — only for new templates */}
              {!isEdit && (
                <div>
                  <Label className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]">
                    Trainingsart
                  </Label>
                  <div className="flex gap-2">
                    {SESSION_TYPE_OPTIONS.map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setSessionType(opt.value)}
                        className={`flex items-center gap-2 px-4 py-2.5 min-h-[44px] text-sm rounded-[var(--radius-component-md)] border transition-colors duration-150 motion-reduce:transition-none ${
                          sessionType === opt.value
                            ? 'border-[var(--color-border-focus)] bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                            : 'border-[var(--color-border-default)] bg-[var(--color-bg-base)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]'
                        }`}
                        aria-pressed={sessionType === opt.value}
                      >
                        {opt.icon === 'dumbbell' ? (
                          <Dumbbell className="w-4 h-4" />
                        ) : (
                          <Footprints className="w-4 h-4" />
                        )}
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Edit mode: show locked session type badge */}
              {isEdit && (
                <div className="flex items-center gap-2">
                  <Label className="text-xs font-medium text-[var(--color-text-muted)]">
                    Trainingsart:
                  </Label>
                  <Badge variant="neutral" size="sm">
                    {sessionType === 'strength' ? 'Kraft' : 'Laufen'}
                  </Badge>
                </div>
              )}

              <div>
                <Label
                  htmlFor="template-name"
                  className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
                >
                  Template-Name
                </Label>
                <Input
                  id="template-name"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder={
                    sessionType === 'strength'
                      ? 'z.B. Studio Tag 1 — Kniedominant'
                      : 'z.B. Intervall 4×3min'
                  }
                  inputSize="md"
                />
              </div>
              <div>
                <Label
                  htmlFor="template-description"
                  className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]"
                >
                  Beschreibung (optional)
                </Label>
                <textarea
                  id="template-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Fokus, Ziele, Hinweise…"
                  rows={2}
                  className="w-full rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-input-bg)] px-3 py-2 text-sm text-[var(--color-text-base)] placeholder:text-[var(--color-text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--color-border-focus)] transition-colors duration-150 motion-reduce:transition-none resize-none"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <Badge variant="neutral" size="sm">
                {sessionType === 'strength' ? 'Kraft' : 'Laufen'}
              </Badge>
              {description && (
                <p className="text-sm text-[var(--color-text-muted)]">{description}</p>
              )}
            </div>
          )}
        </CardBody>
      </Card>

      {/* ===== STRENGTH ===== */}
      {sessionType === 'strength' && isEditing && (
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Übungen ({exercises.filter((e) => e.name.trim()).length})
          </h2>

          {exercises.map((exercise, exIndex) => (
            <Card key={exercise.id} elevation="raised" padding="spacious">
              <CardBody>
                <div className="space-y-4">
                  {/* Exercise Header */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <Dumbbell className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                      <span className="text-xs font-medium text-[var(--color-text-muted)]">
                        Übung {exIndex + 1}
                      </span>
                      {exercise.name && (
                        <Badge
                          variant={categoryBadgeVariant[exercise.category] ?? 'neutral'}
                          size="xs"
                        >
                          {CATEGORY_LABELS[exercise.category] ?? exercise.category}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {/* Reorder buttons */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveExercise(exIndex, -1)}
                        disabled={exIndex === 0}
                        aria-label="Nach oben"
                        className="!p-1"
                      >
                        <GripVertical className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                      </Button>
                      {exercise.name && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            updateExercise(exercise.id, {
                              collapsed: !exercise.collapsed,
                            })
                          }
                          aria-label={exercise.collapsed ? 'Aufklappen' : 'Zuklappen'}
                        >
                          {exercise.collapsed ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronUp className="w-4 h-4" />
                          )}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeExercise(exercise.id)}
                        aria-label="Übung entfernen"
                      >
                        <Trash2 className="w-4 h-4 text-[var(--color-text-error)]" />
                      </Button>
                    </div>
                  </div>

                  {/* Exercise Details (expanded) */}
                  {!exercise.collapsed && (
                    <>
                      {/* Name + suggestions */}
                      <div
                        className="relative"
                        ref={showSuggestions === exercise.id ? suggestionsRef : undefined}
                      >
                        <Input
                          value={exercise.name}
                          onChange={(e) => {
                            updateExercise(exercise.id, {
                              name: e.target.value,
                            });
                            setShowSuggestions(exercise.id);
                          }}
                          onFocus={() => setShowSuggestions(exercise.id)}
                          placeholder="Übungsname (z.B. Kniebeugen)"
                          inputSize="md"
                        />
                        {showSuggestions === exercise.id && (
                          <div className="absolute z-10 mt-1 w-full rounded-[var(--radius-component-md)] bg-[var(--color-bg-elevated)] border border-[var(--color-border-default)] shadow-[var(--shadow-md)] max-h-48 overflow-y-auto">
                            {' '}
                            {/* // ds-ok */}
                            {getFilteredSuggestions(exercise.name).map((ex) => (
                              <button
                                key={ex.id}
                                type="button"
                                className="w-full text-left px-3 py-2.5 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-muted)] transition-colors duration-150 motion-reduce:transition-none flex items-center justify-between"
                                onClick={() => selectSuggestion(exercise.id, ex)}
                              >
                                <span>{ex.name}</span>
                                <Badge
                                  variant={categoryBadgeVariant[ex.category] ?? 'neutral'}
                                  size="xs"
                                >
                                  {CATEGORY_LABELS[ex.category] ?? ex.category}
                                </Badge>
                              </button>
                            ))}
                            {getFilteredSuggestions(exercise.name).length === 0 && (
                              <p className="px-3 py-2.5 text-xs text-[var(--color-text-muted)]">
                                Keine Übung gefunden.
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Category + Type selector */}
                      {exercise.name && (
                        <>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs text-[var(--color-text-muted)]">
                              Kategorie:
                            </span>
                            {CATEGORY_OPTIONS.map((cat) => (
                              <button
                                key={cat.value}
                                type="button"
                                onClick={() =>
                                  updateExercise(exercise.id, {
                                    category: cat.value,
                                  })
                                }
                                className={`px-2.5 py-1 text-xs rounded-[var(--radius-component-sm)] transition-colors duration-150 motion-reduce:transition-none ${
                                  exercise.category === cat.value
                                    ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                                    : 'bg-[var(--color-bg-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-muted)]'
                                }`}
                              >
                                {cat.label}
                              </button>
                            ))}
                          </div>

                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs text-[var(--color-text-muted)]">Typ:</span>
                            {EXERCISE_TYPE_OPTIONS.map((t) => (
                              <button
                                key={t.value}
                                type="button"
                                onClick={() =>
                                  updateExercise(exercise.id, {
                                    exercise_type: t.value,
                                  })
                                }
                                className={`px-2.5 py-1 text-xs rounded-[var(--radius-component-sm)] transition-colors duration-150 motion-reduce:transition-none ${
                                  exercise.exercise_type === t.value
                                    ? 'bg-[var(--color-bg-primary-subtle)] text-[var(--color-text-primary)] font-medium'
                                    : 'bg-[var(--color-bg-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg-muted)]'
                                }`}
                              >
                                {t.label}
                              </button>
                            ))}
                          </div>

                          {/* Sets / Reps / Weight */}
                          <div className="grid grid-cols-3 gap-3">
                            <div>
                              <Label className="mb-1 block text-xs text-[var(--color-text-muted)]">
                                Sätze
                              </Label>
                              <NumberInput
                                value={exercise.sets}
                                onChange={(val) => updateExercise(exercise.id, { sets: val })}
                                min={1}
                                max={20}
                                step={1}
                                inputSize="sm"
                                decrementLabel="Sätze reduzieren"
                                incrementLabel="Sätze erhöhen"
                              />
                            </div>
                            <div>
                              <Label className="mb-1 block text-xs text-[var(--color-text-muted)]">
                                Reps
                              </Label>
                              <NumberInput
                                value={exercise.reps}
                                onChange={(val) => updateExercise(exercise.id, { reps: val })}
                                min={1}
                                max={100}
                                step={1}
                                inputSize="sm"
                                decrementLabel="Reps reduzieren"
                                incrementLabel="Reps erhöhen"
                              />
                            </div>
                            <div>
                              <Label className="mb-1 block text-xs text-[var(--color-text-muted)]">
                                Gewicht (kg)
                              </Label>
                              <NumberInput
                                value={exercise.weight_kg}
                                onChange={(val) => updateExercise(exercise.id, { weight_kg: val })}
                                min={0}
                                max={999}
                                step={2.5}
                                inputSize="sm"
                                decrementLabel="Gewicht reduzieren"
                                incrementLabel="Gewicht erhöhen"
                              />
                            </div>
                          </div>

                          {/* Notes */}
                          <div>
                            <Input
                              value={exercise.notes}
                              onChange={(e) =>
                                updateExercise(exercise.id, {
                                  notes: e.target.value,
                                })
                              }
                              placeholder="Notizen (optional)"
                              inputSize="sm"
                            />
                          </div>
                        </>
                      )}
                    </>
                  )}

                  {/* Collapsed summary */}
                  {exercise.collapsed && exercise.name && (
                    <p className="text-sm text-[var(--color-text-muted)]">
                      {exercise.sets}×{exercise.reps}
                      {exercise.weight_kg > 0 ? ` @ ${exercise.weight_kg} kg` : ''}
                      {exercise.notes ? ` · ${exercise.notes}` : ''}
                    </p>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}

          {/* Add exercise */}
          <Button variant="secondary" onClick={addExercise} className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            Übung hinzufügen
          </Button>
        </div>
      )}

      {/* ===== STRENGTH: Read-Only ===== */}
      {sessionType === 'strength' && !isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)] mb-3">
              Übungen ({exercises.filter((e) => e.name.trim()).length})
            </h2>
            {exercises.filter((e) => e.name.trim()).length === 0 ? (
              <p className="text-xs text-[var(--color-text-muted)] text-center py-4">
                Keine Übungen definiert.
              </p>
            ) : (
              <div className="space-y-2">
                {exercises
                  .filter((e) => e.name.trim())
                  .map((exercise, idx) => (
                    <div
                      key={exercise.id ?? `ro-${idx}`}
                      className="py-2 px-3 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)] space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="text-sm font-medium text-[var(--color-text-base)] truncate">
                            {exercise.name}
                          </span>
                          <Badge
                            variant={categoryBadgeVariant[exercise.category] ?? 'neutral'}
                            size="xs"
                          >
                            {CATEGORY_LABELS[exercise.category] ?? exercise.category}
                          </Badge>
                          {exercise.exercise_type !== 'kraft' && (
                            <Badge variant="neutral" size="xs">
                              {EXERCISE_TYPE_OPTIONS.find((t) => t.value === exercise.exercise_type)
                                ?.label ?? exercise.exercise_type}
                            </Badge>
                          )}
                        </div>
                        <span className="text-sm text-[var(--color-text-muted)] shrink-0 ml-2">
                          {exercise.sets}×{exercise.reps}
                          {exercise.weight_kg > 0 ? ` @ ${exercise.weight_kg} kg` : ''}
                        </span>
                      </div>
                      {exercise.notes && (
                        <p className="text-xs text-[var(--color-text-muted)] italic">
                          {exercise.notes}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* ===== RUNNING: Run Details Editor ===== */}
      {sessionType === 'running' && isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Lauf-Details</h2>

              {/* Run Type Selector */}
              <div>
                <Label className="mb-1.5 block text-xs font-medium text-[var(--color-text-muted)]">
                  Lauftyp
                </Label>
                <Select
                  options={RUN_TYPE_OPTIONS}
                  value={runType}
                  onChange={handleRunTypeChange}
                  inputSize="md"
                  aria-label="Lauftyp"
                />
              </div>

              {/* RunDetailsEditor — handles duration, pace, HR, segments */}
              <RunDetailsEditor
                runDetails={runDetails}
                runType={runType}
                onChange={handleRunDetailsChange}
              />
            </div>
          </CardBody>
        </Card>
      )}

      {/* ===== RUNNING: Read-Only ===== */}
      {sessionType === 'running' && !isEditing && (
        <Card elevation="raised" padding="spacious">
          <CardBody>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)] mb-3">
              Lauf-Details
            </h2>
            <div className="space-y-3">
              {/* Run type + overall metrics */}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="neutral" size="sm">
                    {RUN_TYPE_OPTIONS.find((o) => o.value === runType)?.label ?? runType}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-2 gap-x-4 mt-2">
                  {runDetails?.target_duration_minutes != null && (
                    <div>
                      <span className="block text-xs text-[var(--color-text-muted)]">Dauer</span>
                      <p className="text-sm text-[var(--color-text-base)]">
                        {runDetails.target_duration_minutes} min
                      </p>
                    </div>
                  )}
                  {(runDetails?.target_pace_min || runDetails?.target_pace_max) && (
                    <div>
                      <span className="block text-xs text-[var(--color-text-muted)]">Pace</span>
                      <p className="text-sm text-[var(--color-text-base)]">
                        {runDetails.target_pace_min ?? '?'} – {runDetails.target_pace_max ?? '?'}{' '}
                        min/km
                      </p>
                    </div>
                  )}
                  {(runDetails?.target_hr_min != null || runDetails?.target_hr_max != null) && (
                    <div>
                      <span className="block text-xs text-[var(--color-text-muted)]">
                        Herzfrequenz
                      </span>
                      <p className="text-sm text-[var(--color-text-base)]">
                        {runDetails?.target_hr_min ?? '?'} – {runDetails?.target_hr_max ?? '?'} bpm
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Intervals */}
              {runDetails?.intervals && runDetails.intervals.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-[var(--color-text-base)] mb-2">
                    Segmente ({runDetails.intervals.length})
                  </h3>
                  <div className="space-y-1">
                    {runDetails.intervals.map((interval, iIdx) => {
                      const typeLabel: Record<string, string> = {
                        warmup: 'Einlaufen',
                        cooldown: 'Auslaufen',
                        steady: 'Steady',
                        work: 'Belastung',
                        recovery_jog: 'Trab-Pause',
                        rest: 'Pause',
                        strides: 'Steigerungen',
                        drills: 'Lauf-ABC',
                      };
                      return (
                        <div
                          key={iIdx}
                          className="flex items-center justify-between py-1.5 px-3 rounded-[var(--radius-component-sm)] bg-[var(--color-bg-surface)]"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-xs font-medium text-[var(--color-text-base)]">
                              {typeLabel[interval.type] ?? interval.type}
                            </span>
                            {interval.repeats > 1 && (
                              <span className="text-xs text-[var(--color-text-muted)]">
                                ×{interval.repeats}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)] shrink-0 ml-2">
                            {interval.duration_minutes != null && (
                              <span>{interval.duration_minutes} min</span>
                            )}
                            {interval.distance_km != null && <span>{interval.distance_km} km</span>}
                            {(interval.target_pace_min || interval.target_pace_max) && (
                              <span>
                                {interval.target_pace_min ?? '?'}–{interval.target_pace_max ?? '?'}
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Fixed ActionBar — edit mode */}
      {isEditing && (
        <div
          role="toolbar"
          className="fixed bottom-[82px] lg:bottom-0 left-0 lg:left-[224px] right-0 z-40 bg-[var(--color-actionbar-bg)] border-t border-[var(--color-actionbar-border)] rounded-t-[var(--radius-actionbar)] [box-shadow:var(--shadow-actionbar-default)] px-[var(--spacing-actionbar-padding-x)] py-[var(--spacing-actionbar-padding-y)] flex items-center justify-between gap-[var(--spacing-actionbar-gap)]"
        >
          <span className="text-xs text-[var(--color-actionbar-text)] hidden sm:inline">
            Ungespeicherte Änderungen
          </span>
          <div className="flex gap-2 ml-auto">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (isEdit) {
                  setEditMode(false);
                  loadTemplate();
                } else {
                  navigate('/plan/templates');
                }
              }}
            >
              Abbrechen
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSubmit}
              disabled={submitting || !templateName.trim()}
            >
              {submitting ? (
                <Spinner size="sm" aria-hidden="true" />
              ) : (
                <>
                  <Save className="w-4 h-4 mr-1" />
                  {isEdit ? 'Speichern' : 'Erstellen'}
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
