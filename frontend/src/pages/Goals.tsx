import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardBody,
  Button,
  Input,
  Label,
  Alert,
  AlertDescription,
  Spinner,
  Badge,
  DatePicker,
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
  DropdownMenuSeparator,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from '@nordlig/components';
import { format } from 'date-fns';
import { Plus, EllipsisVertical, Trash2, Power, Pencil, Trophy } from 'lucide-react';
import { listGoals, createGoal, updateGoal, deleteGoal } from '@/api/goals';
import type { RaceGoal } from '@/api/goals';

function parseTimeToSeconds(timeStr: string): number | null {
  const parts = timeStr.split(':').map((p) => parseInt(p, 10));
  if (parts.some(isNaN)) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return null;
}

export function GoalsPage() {
  const { toast } = useToast();

  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingGoal, setDeletingGoal] = useState<RaceGoal | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [editingGoal, setEditingGoal] = useState<RaceGoal | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [distance, setDistance] = useState('');
  const [timeH, setTimeH] = useState('');
  const [timeM, setTimeM] = useState('');
  const [timeS, setTimeS] = useState('');

  const loadGoals = useCallback(async () => {
    try {
      const res = await listGoals();
      setGoals(res.goals);
    } catch {
      toast({ title: 'Ziele konnten nicht geladen werden', variant: 'error' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  const resetForm = () => {
    setTitle('');
    setDate(undefined);
    setDistance('');
    setTimeH('');
    setTimeM('');
    setTimeS('');
    setError(null);
    setEditingGoal(null);
  };

  const openEditDialog = (goal: RaceGoal) => {
    const totalSec = goal.target_time_seconds;
    setEditingGoal(goal);
    setTitle(goal.title);
    setDate(new Date(goal.race_date));
    setDistance(goal.distance_km.toString());
    setTimeH(Math.floor(totalSec / 3600).toString());
    setTimeM(Math.floor((totalSec % 3600) / 60).toString());
    setTimeS((totalSec % 60).toString());
    setError(null);
    setShowDialog(true);
  };

  const handleSave = async () => {
    const dist = parseFloat(distance);
    if (!title.trim()) {
      setError('Bitte einen Titel eingeben');
      return;
    }
    if (!date) {
      setError('Bitte ein Datum wählen');
      return;
    }
    if (isNaN(dist) || dist <= 0) {
      setError('Bitte eine gültige Distanz eingeben');
      return;
    }

    const timeStr = `${timeH || '0'}:${timeM || '0'}:${timeS || '0'}`;
    const totalSeconds = parseTimeToSeconds(timeStr);
    if (!totalSeconds || totalSeconds <= 0) {
      setError('Bitte eine gültige Zielzeit eingeben');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        title: title.trim(),
        race_date: format(date, 'yyyy-MM-dd'),
        distance_km: dist,
        target_time_seconds: totalSeconds,
      };

      if (editingGoal) {
        await updateGoal(editingGoal.id, payload);
        toast({ title: 'Wettkampf-Ziel aktualisiert', variant: 'success' });
      } else {
        await createGoal(payload);
        toast({ title: 'Wettkampf-Ziel erstellt', variant: 'success' });
      }
      resetForm();
      setShowDialog(false);
      await loadGoals();
    } catch {
      setError(editingGoal ? 'Aktualisierung fehlgeschlagen' : 'Erstellen fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (goal: RaceGoal) => {
    try {
      await updateGoal(goal.id, { is_active: !goal.is_active });
      await loadGoals();
    } catch {
      toast({ title: 'Aktualisierung fehlgeschlagen', variant: 'error' });
    }
  };

  const handleDelete = async () => {
    if (!deletingGoal) return;
    setDeleting(true);
    try {
      await deleteGoal(deletingGoal.id);
      toast({ title: `„${deletingGoal.title}" gelöscht`, variant: 'success' });
      setDeletingGoal(null);
      await loadGoals();
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Create / Edit Dialog */}
      <Dialog
        open={showDialog}
        onOpenChange={(open) => {
          if (!open) resetForm();
          setShowDialog(open);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingGoal ? 'Ziel bearbeiten' : 'Neues Wettkampf-Ziel'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="goal-title">Titel</Label>
              <Input
                id="goal-title"
                placeholder="z.B. Hamburg Halbmarathon"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                inputSize="sm"
                autoFocus
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Wettkampf-Datum</Label>
                <DatePicker value={date} onChange={setDate} inputSize="sm" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="goal-distance">Distanz (km)</Label>
                <Input
                  id="goal-distance"
                  type="number"
                  min={0.1}
                  step={0.1}
                  placeholder="z.B. 21.1"
                  value={distance}
                  onChange={(e) => setDistance(e.target.value)}
                  inputSize="sm"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Zielzeit (HH:MM:SS)</Label>
              <div className="grid grid-cols-3 gap-2">
                <Input
                  type="number"
                  min={0}
                  max={23}
                  placeholder="Std"
                  value={timeH}
                  onChange={(e) => setTimeH(e.target.value)}
                  inputSize="sm"
                  aria-label="Stunden"
                />
                <Input
                  type="number"
                  min={0}
                  max={59}
                  placeholder="Min"
                  value={timeM}
                  onChange={(e) => setTimeM(e.target.value)}
                  inputSize="sm"
                  aria-label="Minuten"
                />
                <Input
                  type="number"
                  min={0}
                  max={59}
                  placeholder="Sek"
                  value={timeS}
                  onChange={(e) => setTimeS(e.target.value)}
                  inputSize="sm"
                  aria-label="Sekunden"
                />
              </div>
            </div>
            {error && (
              <Alert variant="error" closeable onClose={() => setError(null)}>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => setShowDialog(false)}>
              Abbrechen
            </Button>
            <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
              {saving ? (
                <Spinner size="sm" aria-hidden="true" />
              ) : editingGoal ? (
                'Speichern'
              ) : (
                'Erstellen'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <AlertDialog
        open={!!deletingGoal}
        onOpenChange={(open) => {
          if (!open) setDeletingGoal(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Ziel löschen?</AlertDialogTitle>
            <AlertDialogDescription>
              „{deletingGoal?.title}" wird unwiderruflich gelöscht.
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

      {/* Goals */}
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
              Wettkampf-Ziele ({goals.length})
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
                <DropdownMenuItem
                  icon={<Plus />}
                  onSelect={() => {
                    resetForm();
                    setShowDialog(true);
                  }}
                >
                  Neues Ziel
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          {goals.length === 0 ? (
            <EmptyState
              title="Keine Wettkampf-Ziele"
              description="Erstelle dein erstes Wettkampf-Ziel, um deinen Fortschritt zu verfolgen."
            />
          ) : (
            <div className="space-y-3">
              {goals.map((goal) => (
                <div
                  key={goal.id}
                  className={`flex items-center gap-3 p-3 rounded-[var(--radius-component-md)] bg-[var(--color-bg-paper)] border border-[var(--color-border-muted)] transition-colors motion-reduce:transition-none ${!goal.is_active ? 'opacity-50' : ''}`}
                >
                  <Trophy className="w-4 h-4 text-[var(--color-text-muted)] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-semibold text-[var(--color-text-base)] truncate block">
                      {goal.title}
                    </span>
                    <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                      {new Date(goal.race_date).toLocaleDateString('de-DE', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                      {' · '}
                      {goal.distance_km} km{' · '}
                      {goal.target_time_formatted}
                      {' · '}
                      {goal.target_pace_formatted} /km
                      {goal.days_until > 0 && ` · ${goal.days_until} Tage`}
                      {goal.days_until === 0 && ' · Heute'}
                    </p>
                    {goal.training_plan_summary ? (
                      <Link
                        to={`/plan/programs/${goal.training_plan_summary.id}`}
                        className="text-xs text-[var(--color-interactive-primary)] hover:underline mt-0.5 inline-block"
                      >
                        Plan: {goal.training_plan_summary.name}
                      </Link>
                    ) : (
                      <Link
                        to={`/plan/programs/new?goalId=${goal.id}`}
                        className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-interactive-primary)] hover:underline mt-0.5 inline-block"
                      >
                        + Trainingsplan erstellen
                      </Link>
                    )}
                  </div>
                  <Badge variant={goal.is_active ? 'info' : 'neutral'} size="sm">
                    {goal.is_active ? 'Aktiv' : 'Inaktiv'}
                  </Badge>
                  <DropdownMenu>
                    <DropdownMenuTrigger>
                      <Button variant="ghost" size="sm" aria-label={`${goal.title} Aktionen`}>
                        <EllipsisVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem icon={<Pencil />} onSelect={() => openEditDialog(goal)}>
                        Bearbeiten
                      </DropdownMenuItem>
                      <DropdownMenuItem icon={<Power />} onSelect={() => handleToggleActive(goal)}>
                        {goal.is_active ? 'Deaktivieren' : 'Aktivieren'}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        icon={<Trash2 />}
                        destructive
                        onSelect={() => setDeletingGoal(goal)}
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
