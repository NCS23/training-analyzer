import { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Button,
  Input,
  Label,
  Alert,
  AlertDescription,
  Spinner,
  Badge,
  DatePicker,
  useToast,
} from '@nordlig/components';
import { format } from 'date-fns';
import { getAthleteSettings, updateAthleteSettings } from '@/api/athlete';
import type { KarvonenZone } from '@/api/athlete';
import { listGoals, createGoal, updateGoal, deleteGoal } from '@/api/goals';
import type { RaceGoal } from '@/api/goals';

function parseTimeToSeconds(timeStr: string): number | null {
  const parts = timeStr.split(':').map((p) => parseInt(p, 10));
  if (parts.some(isNaN)) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return null;
}

export function SettingsPage() {
  const [restingHr, setRestingHr] = useState('');
  const [maxHr, setMaxHr] = useState('');
  const [zones, setZones] = useState<KarvonenZone[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Goal state
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [goalsLoading, setGoalsLoading] = useState(true);
  const [goalError, setGoalError] = useState<string | null>(null);
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [goalSaving, setGoalSaving] = useState(false);
  const [goalTitle, setGoalTitle] = useState('');
  const [goalDate, setGoalDate] = useState<Date | undefined>(undefined);
  const [goalDistance, setGoalDistance] = useState('');
  const [goalTimeH, setGoalTimeH] = useState('');
  const [goalTimeM, setGoalTimeM] = useState('');
  const [goalTimeS, setGoalTimeS] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadGoals = useCallback(async () => {
    try {
      const res = await listGoals();
      setGoals(res.goals);
    } catch {
      setGoalError('Ziele konnten nicht geladen werden');
    } finally {
      setGoalsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  const loadSettings = async () => {
    try {
      const settings = await getAthleteSettings();
      setRestingHr(settings.resting_hr?.toString() || '');
      setMaxHr(settings.max_hr?.toString() || '');
      setZones(settings.karvonen_zones);
    } catch {
      setError('Einstellungen konnten nicht geladen werden');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    const rhr = parseInt(restingHr, 10);
    const mhr = parseInt(maxHr, 10);

    if (isNaN(rhr) || isNaN(mhr)) {
      setError('Bitte beide Werte eingeben');
      return;
    }

    if (rhr >= mhr) {
      setError('Ruhe-HF muss kleiner als Max-HF sein');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const result = await updateAthleteSettings({
        resting_hr: rhr,
        max_hr: mhr,
      });
      setZones(result.karvonen_zones);
      toast({ title: 'Einstellungen gespeichert', variant: 'success' });
    } catch {
      setError('Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const resetGoalForm = () => {
    setGoalTitle('');
    setGoalDate(undefined);
    setGoalDistance('');
    setGoalTimeH('');
    setGoalTimeM('');
    setGoalTimeS('');
    setGoalError(null);
  };

  const handleCreateGoal = async () => {
    const dist = parseFloat(goalDistance);
    if (!goalTitle.trim()) {
      setGoalError('Bitte einen Titel eingeben');
      return;
    }
    if (!goalDate) {
      setGoalError('Bitte ein Datum waehlen');
      return;
    }
    if (isNaN(dist) || dist <= 0) {
      setGoalError('Bitte eine gueltige Distanz eingeben');
      return;
    }

    const timeStr = `${goalTimeH || '0'}:${goalTimeM || '0'}:${goalTimeS || '0'}`;
    const totalSeconds = parseTimeToSeconds(timeStr);
    if (!totalSeconds || totalSeconds <= 0) {
      setGoalError('Bitte eine gueltige Zielzeit eingeben');
      return;
    }

    setGoalSaving(true);
    setGoalError(null);

    try {
      await createGoal({
        title: goalTitle.trim(),
        race_date: format(goalDate, 'yyyy-MM-dd'),
        distance_km: dist,
        target_time_seconds: totalSeconds,
      });
      toast({ title: 'Wettkampf-Ziel erstellt', variant: 'success' });
      resetGoalForm();
      setShowGoalForm(false);
      await loadGoals();
    } catch {
      setGoalError('Erstellen fehlgeschlagen');
    } finally {
      setGoalSaving(false);
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

  const handleDeleteGoal = async (goalId: number) => {
    setDeletingId(goalId);
    try {
      await deleteGoal(goalId);
      toast({ title: 'Ziel geloescht', variant: 'success' });
      await loadGoals();
    } catch {
      toast({ title: 'Loeschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeletingId(null);
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
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Einstellungen
        </h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Herzfrequenz-Daten und Wettkampf-Ziele verwalten.
        </p>
      </header>

      {/* Race Goals */}
      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Wettkampf-Ziele
            </h2>
            {!showGoalForm && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  resetGoalForm();
                  setShowGoalForm(true);
                }}
              >
                Neues Ziel
              </Button>
            )}
          </div>
        </CardHeader>
        <CardBody>
          {/* Create form */}
          {showGoalForm && (
            <div className="space-y-4 pb-4 mb-4 border-b border-[var(--color-border-subtle)]">
              <div className="space-y-2">
                <Label htmlFor="goal-title">Titel</Label>
                <Input
                  id="goal-title"
                  placeholder="z.B. Hamburg Halbmarathon"
                  value={goalTitle}
                  onChange={(e) => setGoalTitle(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Wettkampf-Datum</Label>
                  <DatePicker
                    value={goalDate}
                    onChange={setGoalDate}
                    inputSize="md"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="goal-distance">Distanz (km)</Label>
                  <Input
                    id="goal-distance"
                    type="number"
                    min={0.1}
                    step={0.1}
                    placeholder="z.B. 21.1"
                    value={goalDistance}
                    onChange={(e) => setGoalDistance(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Zielzeit (HH:MM:SS)</Label>
                <div className="grid grid-cols-3 gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={23}
                    placeholder="Std"
                    value={goalTimeH}
                    onChange={(e) => setGoalTimeH(e.target.value)}
                    aria-label="Stunden"
                  />
                  <Input
                    type="number"
                    min={0}
                    max={59}
                    placeholder="Min"
                    value={goalTimeM}
                    onChange={(e) => setGoalTimeM(e.target.value)}
                    aria-label="Minuten"
                  />
                  <Input
                    type="number"
                    min={0}
                    max={59}
                    placeholder="Sek"
                    value={goalTimeS}
                    onChange={(e) => setGoalTimeS(e.target.value)}
                    aria-label="Sekunden"
                  />
                </div>
              </div>

              {goalError && (
                <Alert variant="error" closeable onClose={() => setGoalError(null)}>
                  <AlertDescription>{goalError}</AlertDescription>
                </Alert>
              )}

              <div className="flex justify-end gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    resetGoalForm();
                    setShowGoalForm(false);
                  }}
                >
                  Abbrechen
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleCreateGoal}
                  disabled={goalSaving}
                >
                  {goalSaving ? <Spinner size="sm" aria-hidden="true" /> : 'Erstellen'}
                </Button>
              </div>
            </div>
          )}

          {/* Goals list */}
          {goalsLoading ? (
            <div className="flex justify-center py-6">
              <Spinner size="sm" />
            </div>
          ) : goals.length === 0 ? (
            <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
              Noch keine Wettkampf-Ziele definiert.
            </p>
          ) : (
            <div className="space-y-3">
              {goals.map((goal) => (
                <div
                  key={goal.id}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-[var(--radius-md)] border ${
                    goal.is_active
                      ? 'border-[var(--color-border-accent)] bg-[var(--color-bg-info-subtle)]'
                      : 'border-[var(--color-border-subtle)] opacity-60'
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-[var(--color-text-base)] truncate">
                        {goal.title}
                      </span>
                      {goal.is_active && <Badge variant="info" size="sm">Aktiv</Badge>}
                      {goal.days_until > 0 ? (
                        <Badge variant="neutral" size="sm">
                          {goal.days_until} Tage
                        </Badge>
                      ) : goal.days_until === 0 ? (
                        <Badge variant="warning" size="sm">Heute</Badge>
                      ) : (
                        <Badge variant="neutral" size="sm">Vergangen</Badge>
                      )}
                    </div>
                    <div className="text-xs text-[var(--color-text-muted)] mt-1 flex flex-wrap gap-x-3">
                      <span>{new Date(goal.race_date).toLocaleDateString('de-DE')}</span>
                      <span>{goal.distance_km} km</span>
                      <span>Zielzeit: {goal.target_time_formatted}</span>
                      <span>Pace: {goal.target_pace_formatted} min/km</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleActive(goal)}
                    >
                      {goal.is_active ? 'Deaktivieren' : 'Aktivieren'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteGoal(goal.id)}
                      disabled={deletingId === goal.id}
                    >
                      {deletingId === goal.id ? (
                        <Spinner size="sm" aria-hidden="true" />
                      ) : (
                        'Loeschen'
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>

      {/* HR Settings */}
      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">Herzfrequenz</h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="resting-hr">Ruheherzfrequenz (bpm)</Label>
              <Input
                id="resting-hr"
                type="number"
                min={30}
                max={120}
                placeholder="z.B. 50"
                value={restingHr}
                onChange={(e) => setRestingHr(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-hr">Maximale Herzfrequenz (bpm)</Label>
              <Input
                id="max-hr"
                type="number"
                min={120}
                max={230}
                placeholder="z.B. 190"
                value={maxHr}
                onChange={(e) => setMaxHr(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <Alert variant="error" closeable onClose={() => setError(null)} className="mt-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardBody>
        <CardFooter className="justify-end pt-4">
          <Button variant="primary" onClick={handleSave} disabled={saving || !restingHr || !maxHr}>
            {saving ? <Spinner size="sm" aria-hidden="true" /> : 'Speichern'}
          </Button>
        </CardFooter>
      </Card>

      {/* Karvonen Zones Preview */}
      {zones && (
        <Card elevation="raised" padding="spacious">
          <CardHeader>
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              Karvonen-Zonen (5 Zonen)
            </h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {zones.map((zone) => (
                <div
                  key={zone.zone}
                  className="flex items-center justify-between py-2 px-3 rounded-[var(--radius-md)]"
                  style={{ backgroundColor: `${zone.color}15` }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: zone.color }}
                    />
                    <span className="text-sm font-medium text-[var(--color-text-base)]">
                      Zone {zone.zone}: {zone.name}
                    </span>
                  </div>
                  <span className="text-sm text-[var(--color-text-muted)]">
                    {zone.lower_bpm}-{zone.upper_bpm} bpm
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-4">
              Berechnet via Karvonen-Formel: HR = Ruhe-HR + (Max-HR - Ruhe-HR) × Intensitaet%
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
