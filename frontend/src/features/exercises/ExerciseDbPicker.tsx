import { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalBody,
  ModalFooter,
  Input,
  Badge,
  Button,
  Spinner,
  EmptyState,
  useToast,
} from '@nordlig/components';
import { Check, Search } from 'lucide-react';
import { searchExerciseDb, enrichExercise } from '@/api/exercises';
import type { Exercise, ExerciseDbEntry } from '@/api/exercises';

interface ExerciseDbPickerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  exerciseId: number;
  currentDbId: string | null;
  onEnriched: (exercise: Exercise) => void;
}

const equipmentLabels: Record<string, string> = {
  barbell: 'Langhantel',
  dumbbell: 'Kurzhantel',
  cable: 'Kabelzug',
  machine: 'Maschine',
  'body only': 'Körpergewicht',
  'e-z curl bar': 'EZ-Stange',
  'medicine ball': 'Medizinball',
  kettlebells: 'Kettlebell',
  bands: 'Bänder',
  'foam roll': 'Faszienrolle',
  other: 'Sonstiges',
  'exercise ball': 'Gymnastikball',
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

export function ExerciseDbPicker({
  open,
  onOpenChange,
  exerciseId,
  currentDbId,
  onEnriched,
}: ExerciseDbPickerProps) {
  const { toast } = useToast();

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [results, setResults] = useState<ExerciseDbEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [enriching, setEnriching] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Fetch results
  const fetchResults = useCallback(
    async (query: string) => {
      setLoading(true);
      try {
        const res = await searchExerciseDb({
          q: query || undefined,
          limit: 50,
        });
        setResults(res.exercises);
        setTotal(res.total);
      } catch {
        toast({ title: 'Suche fehlgeschlagen', variant: 'error' });
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    if (!open) return;
    fetchResults(debouncedSearch);
  }, [open, debouncedSearch, fetchResults]);

  // Reset on open
  useEffect(() => {
    if (open) {
      setSelectedId(currentDbId);
      setSearch('');
    }
  }, [open, currentDbId]);

  const handleConfirm = async () => {
    if (!selectedId || selectedId === currentDbId) return;
    setEnriching(true);
    try {
      const updated = await enrichExercise(exerciseId, selectedId);
      onEnriched(updated);
      onOpenChange(false);
      toast({ title: 'Zuordnung aktualisiert', variant: 'success' });
    } catch {
      toast({ title: 'Fehler bei der Zuordnung', variant: 'error' });
    } finally {
      setEnriching(false);
    }
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent size="lg">
        <ModalHeader>
          <ModalTitle>Zuordnung wählen</ModalTitle>
          <ModalDescription>{total} Übungen in der Datenbank</ModalDescription>
          <div className="relative mt-2">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Übung suchen (deutsch oder englisch)…"
              inputSize="sm"
              className="pl-9"
              autoFocus
            />
          </div>
        </ModalHeader>

        <ModalBody>
          {loading ? (
            <div className="flex justify-center py-8">
              <Spinner size="lg" />
            </div>
          ) : results.length === 0 ? (
            <EmptyState
              title="Keine Ergebnisse"
              description="Versuche einen anderen Suchbegriff."
            />
          ) : (
            <ul role="listbox" className="space-y-1" aria-label="Übungen aus der Datenbank">
              {results.map((ex) => {
                const isSelected = selectedId === ex.id;
                const isCurrent = currentDbId === ex.id;

                return (
                  <li
                    key={ex.id}
                    role="option"
                    aria-selected={isSelected}
                    tabIndex={0}
                    onClick={() => setSelectedId(ex.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setSelectedId(ex.id);
                      }
                    }}
                    className={`flex items-center gap-3 p-3 rounded-[var(--radius-component-md)] cursor-pointer transition-colors motion-reduce:transition-none ${
                      isSelected
                        ? 'bg-[var(--color-bg-subtle)] ring-1 ring-[var(--color-border-focus)]'
                        : 'hover:bg-[var(--color-bg-hover)]'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--color-text-base)] truncate">
                          {ex.name_de ?? ex.name}
                        </span>
                        {isCurrent && (
                          <Badge variant="success" size="xs">
                            aktuell
                          </Badge>
                        )}
                      </div>
                      {ex.name_de && (
                        <span className="text-xs text-[var(--color-text-muted)] truncate block">
                          {ex.name}
                        </span>
                      )}
                      <div className="flex flex-wrap gap-1 mt-1">
                        {ex.equipment && (
                          <Badge variant="neutral" size="xs">
                            {equipmentLabels[ex.equipment] ?? ex.equipment}
                          </Badge>
                        )}
                        {ex.primary_muscles.slice(0, 3).map((m) => (
                          <Badge key={m} variant="neutral" size="xs">
                            {muscleLabels[m] ?? m}
                          </Badge>
                        ))}
                        {ex.level && (
                          <Badge variant="neutral" size="xs">
                            {ex.level}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {isSelected && (
                      <Check className="w-5 h-5 shrink-0 text-[var(--color-status-success)]" />
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </ModalBody>

        {selectedId &&
          selectedId !== currentDbId &&
          (() => {
            const selected = results.find((r) => r.id === selectedId);
            if (!selected) return null;
            const ghBase =
              'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises';
            const handleImgError = (e: React.SyntheticEvent<HTMLImageElement>) => {
              const img = e.currentTarget;
              // Try GitHub fallback once, then hide
              if (!img.dataset.fallback) {
                img.dataset.fallback = 'true';
                const fileName = img.src.split('/').pop();
                img.src = `${ghBase}/${selected.id}/${fileName}`;
              } else {
                img.style.display = 'none';
              }
            };
            return (
              <div
                key={selected.id}
                className="border-t border-[var(--color-border-default)] px-6 py-4"
              >
                <p className="text-xs font-medium text-[var(--color-text-muted)] mb-2">
                  Vorschau: {selected.name_de ?? selected.name}
                </p>
                <div className="flex gap-3">
                  <img
                    src={`/static/exercises/${selected.id}/0.jpg`}
                    alt={`${selected.name} – Startposition`}
                    className="w-1/2 max-h-48 object-contain rounded-[var(--radius-component-md)] bg-[var(--color-bg-subtle)]"
                    onError={handleImgError}
                  />
                  <img
                    src={`/static/exercises/${selected.id}/1.jpg`}
                    alt={`${selected.name} – Endposition`}
                    className="w-1/2 max-h-48 object-contain rounded-[var(--radius-component-md)] bg-[var(--color-bg-subtle)]"
                    onError={handleImgError}
                  />
                </div>
              </div>
            );
          })()}

        <ModalFooter>
          <Button variant="secondary" size="sm" onClick={() => onOpenChange(false)}>
            Abbrechen
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleConfirm}
            disabled={!selectedId || selectedId === currentDbId || enriching}
          >
            {enriching ? <Spinner size="sm" aria-hidden="true" /> : 'Zuordnen'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
