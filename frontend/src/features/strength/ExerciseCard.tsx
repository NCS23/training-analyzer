import { useCallback, useState, useRef, useEffect } from 'react';
import { Input, Select, Button, Alert, AlertDescription } from '@nordlig/components';
import { Plus, Trash2, Copy, Star } from 'lucide-react';
import type { ExerciseInput, ExerciseCategory, SetInput } from '@/api/strength';
import { getLastExerciseSets } from '@/api/strength';
import type { Exercise } from '@/api/exercises';
import { SetRow } from './SetRow';

const categoryOptions = [
  { value: 'push', label: 'Push' },
  { value: 'pull', label: 'Pull' },
  { value: 'legs', label: 'Beine' },
  { value: 'core', label: 'Core' },
  { value: 'cardio', label: 'Cardio' },
];

const defaultSet: SetInput = { reps: 8, weight_kg: 0, status: 'completed' };

interface ExerciseCardProps {
  index: number;
  exercise: ExerciseInput;
  onChange: (index: number, exercise: ExerciseInput) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
  exerciseLibrary?: Exercise[];
}

export function ExerciseCard({
  index,
  exercise,
  onChange,
  onRemove,
  canRemove,
  exerciseLibrary,
}: ExerciseCardProps) {
  const [lastSetsHint, setLastSetsHint] = useState<SetInput[] | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLDivElement>(null);

  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredSuggestions =
    exerciseLibrary?.filter(
      (ex) =>
        exercise.name.length >= 1 &&
        ex.name.toLowerCase().includes(exercise.name.toLowerCase()) &&
        ex.name.toLowerCase() !== exercise.name.toLowerCase(),
    ) ?? [];

  const handleSelectSuggestion = useCallback(
    (suggestion: Exercise) => {
      onChange(index, {
        ...exercise,
        name: suggestion.name,
        category: suggestion.category as ExerciseCategory,
      });
      setShowSuggestions(false);
    },
    [exercise, index, onChange],
  );

  const handleSetChange = useCallback(
    (setIndex: number, updated: SetInput) => {
      const newSets = [...exercise.sets];
      newSets[setIndex] = updated;
      onChange(index, { ...exercise, sets: newSets });
    },
    [exercise, index, onChange],
  );

  const handleSetRemove = useCallback(
    (setIndex: number) => {
      const newSets = exercise.sets.filter((_, i) => i !== setIndex);
      onChange(index, { ...exercise, sets: newSets });
    },
    [exercise, index, onChange],
  );

  const handleAddSet = useCallback(() => {
    const lastSet = exercise.sets[exercise.sets.length - 1];
    const newSet: SetInput = lastSet ? { ...lastSet, status: 'completed' } : { ...defaultSet };
    onChange(index, { ...exercise, sets: [...exercise.sets, newSet] });
  }, [exercise, index, onChange]);

  const handleNameBlur = useCallback(async () => {
    if (!exercise.name.trim()) return;
    try {
      const result = await getLastExerciseSets(exercise.name.trim());
      if (result.found && result.exercise) {
        setLastSetsHint(
          result.exercise.sets.map((s) => ({
            reps: s.reps,
            weight_kg: s.weight_kg,
            status: (s.status as SetInput['status']) || 'completed',
          })),
        );
      } else {
        setLastSetsHint(null);
      }
    } catch {
      // Silently ignore — quick-add is optional
    }
  }, [exercise.name]);

  const handleApplyLastSets = useCallback(() => {
    if (!lastSetsHint) return;
    onChange(index, { ...exercise, sets: lastSetsHint });
    setLastSetsHint(null);
  }, [lastSetsHint, exercise, index, onChange]);

  return (
    <div className="rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] p-4 space-y-3">
      {/* Exercise header: name, category, remove */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0 grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div className="relative" ref={inputRef}>
            <Input
              value={exercise.name}
              onChange={(e) => {
                onChange(index, { ...exercise, name: e.target.value });
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={handleNameBlur}
              placeholder="Übungsname"
              inputSize="sm"
              aria-label={`Übung ${index + 1} Name`}
              autoComplete="off"
            />
            {showSuggestions && filteredSuggestions.length > 0 && (
              <div
                ref={suggestionsRef}
                className="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto rounded-[var(--radius-component-md)] border border-[var(--color-border-default)] bg-[var(--color-bg-elevated)] shadow-[var(--shadow-md)]"
              >
                {filteredSuggestions.slice(0, 8).map((suggestion) => (
                  <button
                    key={suggestion.id}
                    type="button"
                    className="w-full text-left px-3 py-2 text-sm text-[var(--color-text-base)] hover:bg-[var(--color-bg-hover)] flex items-center justify-between gap-2 transition-colors motion-reduce:transition-none"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      handleSelectSuggestion(suggestion);
                    }}
                  >
                    <span className="truncate">{suggestion.name}</span>
                    <span className="flex items-center gap-1 shrink-0">
                      {suggestion.is_favorite && (
                        <Star
                          className="w-3 h-3 text-[var(--color-status-warning)]"
                          fill="currentColor"
                        />
                      )}
                      <span className="text-xs text-[var(--color-text-muted)]">
                        {suggestion.category}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <Select
            options={categoryOptions}
            value={exercise.category}
            onChange={(val) =>
              onChange(index, { ...exercise, category: (val || 'push') as ExerciseCategory })
            }
            inputSize="sm"
            aria-label={`Übung ${index + 1} Kategorie`}
          />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
          disabled={!canRemove}
          aria-label={`Übung ${index + 1} entfernen`}
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Set header */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <span className="w-6 shrink-0 text-center">#</span>
        <span className="flex-1">Wdh.</span>
        <span className="flex-1">kg</span>
        <span className="w-28 shrink-0">Status</span>
        <span className="w-8 shrink-0" />
      </div>

      {/* Set rows */}
      {exercise.sets.map((set, setIndex) => (
        <SetRow
          key={setIndex}
          index={setIndex}
          set={set}
          onChange={handleSetChange}
          onRemove={handleSetRemove}
          canRemove={exercise.sets.length > 1}
        />
      ))}

      {/* Quick-Add hint */}
      {lastSetsHint && (
        <Alert variant="info">
          <AlertDescription className="flex items-center justify-between gap-2">
            <span className="text-sm">Letzte Session: {lastSetsHint.length} Sätze gefunden</span>
            <Button variant="ghost" size="sm" onClick={handleApplyLastSets}>
              <Copy className="w-3.5 h-3.5 mr-1" />
              Übernehmen
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Button variant="ghost" size="sm" onClick={handleAddSet} className="w-full">
        <Plus className="w-3.5 h-3.5 mr-1" />
        Satz hinzufügen
      </Button>
    </div>
  );
}
