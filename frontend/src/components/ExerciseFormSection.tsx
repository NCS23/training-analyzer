/**
 * Shared Übungs-Formular-Section für Erstellen und Bearbeiten.
 * Wird identisch in StrengthSession.tsx und StrengthExercisesEditor.tsx verwendet.
 * Enthält: Exercise-Name mit DB-Autocomplete, Category-Select, Set-Type-Select,
 * dynamische Set-Rows je Typ, CRUD-Buttons.
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { Button, Input, NumberInput, Select } from '@nordlig/components';
import { Plus, Trash2, Star } from 'lucide-react';
import { listExercises } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';
import type { ExerciseCategory, SetStatus, SetType } from '@/api/strength';
import { SET_TYPE_OPTIONS, SET_TYPE_FIELDS } from '@/api/strength';
import { genId, createDefaultSet, createDefaultExercise } from './exercise-form-helpers';
import type { ExerciseForm, SetForm } from './exercise-form-helpers';

// --- Constants ---

const CATEGORY_SELECT_OPTIONS = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
  { value: 'drills', label: 'Lauf-ABC' },
];

const STATUS_SELECT_OPTIONS = [
  { value: 'completed', label: 'Fertig' },
  { value: 'reduced', label: 'Reduziert' },
  { value: 'skipped', label: 'Übersprungen' },
];

// --- Sub-Components ---

function DurationFormInput({
  value,
  onChange,
  label,
}: {
  value: number;
  onChange: (sec: number) => void;
  label: string;
}) {
  const mins = Math.floor(value / 60);
  const secs = value % 60;

  return (
    <div className="flex items-center gap-0.5">
      <NumberInput
        value={mins}
        onChange={(m) => onChange(m * 60 + secs)}
        min={0}
        max={1440}
        step={1}
        inputSize="sm"
        aria-label={`${label} Minuten`}
        incrementLabel="Minute hinzufügen"
        decrementLabel="Minute entfernen"
      />
      <span className="text-xs text-[var(--color-text-muted)]">:</span>
      <NumberInput
        value={secs}
        onChange={(s) => onChange(mins * 60 + Math.min(s, 59))}
        min={0}
        max={59}
        step={1}
        inputSize="sm"
        aria-label={`${label} Sekunden`}
        incrementLabel="Sekunde hinzufügen"
        decrementLabel="Sekunde entfernen"
      />
    </div>
  );
}

function SetHeader({ setType }: { setType: SetType }) {
  const fields = SET_TYPE_FIELDS[setType];
  return (
    <div className="hidden sm:flex items-center gap-2 text-xs text-[var(--color-text-muted)] px-1">
      <span className="w-6 shrink-0 text-center">#</span>
      {fields.reps && <span className="flex-1">Wdh.</span>}
      {fields.weight && <span className="flex-1">kg</span>}
      {fields.duration && <span className="flex-1">Min:Sek</span>}
      {fields.distance && <span className="flex-1">Meter</span>}
      <span className="w-28 shrink-0">Status</span>
      <span className="w-8 shrink-0" />
    </div>
  );
}

function SetStatusControls({
  set,
  setIndex,
  onUpdate,
  onRemove,
  canRemove,
}: {
  set: SetForm;
  setIndex: number;
  onUpdate: (updates: Partial<SetForm>) => void;
  onRemove: () => void;
  canRemove: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 sm:w-28 sm:flex-none sm:shrink-0">
        <Select
          options={STATUS_SELECT_OPTIONS}
          value={set.status}
          onChange={(val) => onUpdate({ status: (val as SetStatus) || 'completed' })}
          inputSize="sm"
        />
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        disabled={!canRemove}
        aria-label={`Satz ${setIndex + 1} entfernen`}
        className="shrink-0"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </Button>
    </div>
  );
}

interface SetRowFormProps {
  set: SetForm;
  setIndex: number;
  setType: SetType;
  onUpdate: (updates: Partial<SetForm>) => void;
  onRemove: () => void;
  canRemove: boolean;
}

function SetRowForm({ set, setIndex, setType, onUpdate, onRemove, canRemove }: SetRowFormProps) {
  const fields = SET_TYPE_FIELDS[setType];

  return (
    <div className={`space-y-2 sm:space-y-0 px-1 ${set.status === 'skipped' ? 'opacity-50' : ''}`}>
      {/* Zeile 1: Index + Werte-Inputs */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--color-text-muted)] w-6 shrink-0 text-center tabular-nums">
          {setIndex + 1}
        </span>

        {fields.reps && (
          <div className="flex-1 min-w-0">
            <NumberInput
              value={set.reps ?? 0}
              onChange={(val) => onUpdate({ reps: val })}
              min={0}
              max={999}
              step={1}
              inputSize="sm"
              aria-label={`Satz ${setIndex + 1} Wiederholungen`}
              incrementLabel="Wiederholung hinzufügen"
              decrementLabel="Wiederholung entfernen"
            />
          </div>
        )}

        {fields.weight && (
          <div className="flex-1 min-w-0">
            <NumberInput
              value={set.weight_kg ?? 0}
              onChange={(val) => onUpdate({ weight_kg: val })}
              min={0}
              max={999}
              step={2.5}
              inputSize="sm"
              aria-label={`Satz ${setIndex + 1} Gewicht kg`}
              incrementLabel="Gewicht erhöhen"
              decrementLabel="Gewicht verringern"
            />
          </div>
        )}

        {fields.duration && (
          <div className="flex-1 min-w-0">
            <DurationFormInput
              value={set.duration_sec ?? 0}
              onChange={(sec) => onUpdate({ duration_sec: sec })}
              label={`Satz ${setIndex + 1}`}
            />
          </div>
        )}

        {fields.distance && (
          <div className="flex-1 min-w-0">
            <NumberInput
              value={set.distance_m ?? 0}
              onChange={(val) => onUpdate({ distance_m: val })}
              min={0}
              max={99999}
              step={5}
              inputSize="sm"
              aria-label={`Satz ${setIndex + 1} Distanz m`}
              incrementLabel="Distanz erhöhen"
              decrementLabel="Distanz verringern"
            />
          </div>
        )}

        {/* Status + Delete: inline ab sm */}
        <div className="hidden sm:block">
          <SetStatusControls
            set={set}
            setIndex={setIndex}
            onUpdate={onUpdate}
            onRemove={onRemove}
            canRemove={canRemove}
          />
        </div>
      </div>

      {/* Zeile 2 (nur Mobile): Status + Delete */}
      <div className="pl-8 sm:hidden">
        <SetStatusControls
          set={set}
          setIndex={setIndex}
          onUpdate={onUpdate}
          onRemove={onRemove}
          canRemove={canRemove}
        />
      </div>
    </div>
  );
}

// --- ExerciseFormCard (extracted for ESLint max-lines-per-function) ---

interface ExerciseFormCardProps {
  exercise: ExerciseForm;
  suggestions: Exercise[];
  autocompleteRef?: React.RefObject<HTMLDivElement | null>;
  onNameChange: (val: string) => void;
  onNameFocus: () => void;
  onCategoryChange: (val: string | undefined) => void;
  onSetTypeChange: (val: string | undefined) => void;
  onSelectSuggestion: (s: Exercise) => void;
  onRemove: () => void;
  onUpdateSet: (setId: string, updates: Partial<SetForm>) => void;
  onRemoveSet: (setId: string) => void;
  onAddSet: () => void;
}

function ExerciseFormCard({
  exercise,
  suggestions,
  autocompleteRef,
  onNameChange,
  onNameFocus,
  onCategoryChange,
  onSetTypeChange,
  onSelectSuggestion,
  onRemove,
  onUpdateSet,
  onRemoveSet,
  onAddSet,
}: ExerciseFormCardProps) {
  return (
    <div className="rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] p-4 space-y-3">
      {/* Exercise name + category + set type + delete */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0 grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div className="relative" ref={autocompleteRef}>
            <Input
              value={exercise.name}
              onChange={(e) => onNameChange(e.target.value)}
              onFocus={onNameFocus}
              placeholder="Übungsname"
              inputSize="sm"
              autoComplete="off"
            />
            {suggestions.length > 0 && (
              <div className="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] shadow-[var(--shadow-md)]">
                {suggestions.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-hover)] flex items-center justify-between gap-2 transition-colors motion-reduce:transition-none"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      onSelectSuggestion(s);
                    }}
                  >
                    <span className="truncate">{s.name}</span>
                    <span className="flex items-center gap-1 shrink-0">
                      {s.is_favorite && (
                        <Star
                          className="w-3 h-3 text-[var(--color-status-warning)]"
                          fill="currentColor"
                        />
                      )}
                      <span className="text-xs text-[var(--color-text-muted)]">
                        {CATEGORY_SELECT_OPTIONS.find((o) => o.value === s.category)?.label ??
                          s.category}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <Select
            options={CATEGORY_SELECT_OPTIONS}
            value={exercise.category}
            onChange={onCategoryChange}
            inputSize="sm"
          />
          <Select
            options={SET_TYPE_OPTIONS}
            value={exercise.setType}
            onChange={onSetTypeChange}
            inputSize="sm"
          />
        </div>
        <Button variant="ghost" size="sm" onClick={onRemove} aria-label="Übung entfernen">
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Set header */}
      <SetHeader setType={exercise.setType} />

      {/* Set rows */}
      {exercise.sets.map((set, setIndex) => (
        <SetRowForm
          key={set.id}
          set={set}
          setIndex={setIndex}
          setType={exercise.setType}
          onUpdate={(updates) => onUpdateSet(set.id, updates)}
          onRemove={() => onRemoveSet(set.id)}
          canRemove={exercise.sets.length > 1}
        />
      ))}

      {/* Add set */}
      <Button variant="ghost" size="sm" onClick={onAddSet} className="w-full">
        <Plus className="w-3.5 h-3.5 mr-1" />
        Satz hinzufügen
      </Button>
    </div>
  );
}

// --- Props ---

interface ExerciseFormSectionProps {
  exercises: ExerciseForm[];
  setExercises: React.Dispatch<React.SetStateAction<ExerciseForm[]>>;
  /** Hide the built-in tonnage summary (e.g. when the parent has its own). */
  hideTonnageSummary?: boolean;
}

// --- Component ---

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
export function ExerciseFormSection({
  exercises,
  setExercises,
  hideTonnageSummary: _hideTonnageSummary = false,
}: ExerciseFormSectionProps) {
  const [libraryExercises, setLibraryExercises] = useState<Exercise[]>([]);
  const [activeAutocomplete, setActiveAutocomplete] = useState<string | null>(null);
  const autocompleteRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listExercises()
      .then((res) => setLibraryExercises(res.exercises))
      .catch(() => {});
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (autocompleteRef.current && !autocompleteRef.current.contains(e.target as Node)) {
        setActiveAutocomplete(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // --- Exercise CRUD ---

  const updateExercise = useCallback(
    (exerciseId: string, updates: Partial<ExerciseForm>) => {
      setExercises((prev) => prev.map((ex) => (ex.id === exerciseId ? { ...ex, ...updates } : ex)));
    },
    [setExercises],
  );

  const removeExercise = useCallback(
    (exerciseId: string) => {
      setExercises((prev) => {
        const filtered = prev.filter((ex) => ex.id !== exerciseId);
        return filtered.length === 0 ? [createDefaultExercise()] : filtered;
      });
    },
    [setExercises],
  );

  const addExercise = useCallback(() => {
    setExercises((prev) => [...prev, createDefaultExercise()]);
  }, [setExercises]);

  // --- Set type change ---

  const handleSetTypeChange = useCallback(
    (exerciseId: string, newType: SetType) => {
      setExercises((prev) =>
        prev.map((ex) => {
          if (ex.id !== exerciseId) return ex;
          const newSets = ex.sets.map((s) => ({ ...s, type: newType }));
          return { ...ex, setType: newType, sets: newSets };
        }),
      );
    },
    [setExercises],
  );

  // --- Set CRUD ---

  const updateSet = useCallback(
    (exerciseId: string, setId: string, updates: Partial<SetForm>) => {
      setExercises((prev) =>
        prev.map((ex) =>
          ex.id === exerciseId
            ? { ...ex, sets: ex.sets.map((s) => (s.id === setId ? { ...s, ...updates } : s)) }
            : ex,
        ),
      );
    },
    [setExercises],
  );

  const addSet = useCallback(
    (exerciseId: string) => {
      setExercises((prev) =>
        prev.map((ex) => {
          if (ex.id !== exerciseId) return ex;
          const lastSet = ex.sets[ex.sets.length - 1];
          const newSet: SetForm = lastSet
            ? { ...lastSet, id: genId('set'), status: 'completed' }
            : createDefaultSet(ex.setType);
          return { ...ex, sets: [...ex.sets, newSet] };
        }),
      );
    },
    [setExercises],
  );

  const removeSet = useCallback(
    (exerciseId: string, setId: string) => {
      setExercises((prev) =>
        prev.map((ex) => {
          if (ex.id !== exerciseId) return ex;
          const filtered = ex.sets.filter((s) => s.id !== setId);
          return { ...ex, sets: filtered.length === 0 ? [createDefaultSet(ex.setType)] : filtered };
        }),
      );
    },
    [setExercises],
  );

  // --- Autocomplete helpers ---

  const getFilteredSuggestions = useCallback(
    (query: string) => {
      if (!query.trim() || query.trim().length < 1) return [];
      const q = query.toLowerCase();
      return libraryExercises
        .filter((ex) => ex.name.toLowerCase().includes(q) && ex.name.toLowerCase() !== q)
        .slice(0, 8);
    },
    [libraryExercises],
  );

  const selectSuggestion = useCallback(
    (exerciseId: string, suggestion: Exercise) => {
      const updates: Partial<ExerciseForm> = {
        name: suggestion.name,
        category: (suggestion.category as ExerciseCategory) || 'push',
      };
      if (suggestion.default_set_type) {
        updates.setType = suggestion.default_set_type as SetType;
      }
      updateExercise(exerciseId, updates);
      if (suggestion.default_set_type) {
        handleSetTypeChange(exerciseId, suggestion.default_set_type as SetType);
      }
      setActiveAutocomplete(null);
    },
    [updateExercise, handleSetTypeChange],
  );

  // --- Render ---

  return (
    <div className="space-y-6">
      {exercises.map((exercise) => (
        <ExerciseFormCard
          key={exercise.id}
          exercise={exercise}
          suggestions={
            activeAutocomplete === exercise.id ? getFilteredSuggestions(exercise.name) : []
          }
          autocompleteRef={activeAutocomplete === exercise.id ? autocompleteRef : undefined}
          onNameChange={(val) => {
            updateExercise(exercise.id, { name: val });
            setActiveAutocomplete(val.trim().length >= 1 ? exercise.id : null);
          }}
          onNameFocus={() => {
            if (exercise.name.trim().length >= 1) setActiveAutocomplete(exercise.id);
          }}
          onCategoryChange={(val) =>
            updateExercise(exercise.id, {
              category: (val || 'push') as ExerciseCategory,
            })
          }
          onSetTypeChange={(val) =>
            handleSetTypeChange(exercise.id, (val || 'weight_reps') as SetType)
          }
          onSelectSuggestion={(s) => selectSuggestion(exercise.id, s)}
          onRemove={() => removeExercise(exercise.id)}
          onUpdateSet={(setId, updates) => updateSet(exercise.id, setId, updates)}
          onRemoveSet={(setId) => removeSet(exercise.id, setId)}
          onAddSet={() => addSet(exercise.id)}
        />
      ))}

      {/* Add exercise button */}
      <div className="flex justify-center">
        <Button variant="ghost" onClick={addExercise}>
          <Plus className="w-4 h-4 mr-2" />
          Übung hinzufügen
        </Button>
      </div>
    </div>
  );
}
