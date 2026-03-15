import { useState, useEffect, useMemo, useRef } from 'react';
import { Link } from 'react-router-dom';
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
  useToast,
} from '@nordlig/components';
import { getAthleteSettings, updateAthleteSettings } from '@/api/athlete';
import { useApiKeySettings } from '@/hooks/useApiKeySettings';
import { ApiKeyCard } from '@/components/settings/ApiKeyCard';

// Karvonen zone definitions — mirrors backend/app/services/hr_zone_calculator.py
const KARVONEN_ZONES = [
  { zone: 1, name: 'Recovery', pctMin: 0.5, pctMax: 0.6, color: '#94a3b8' },
  { zone: 2, name: 'Base', pctMin: 0.6, pctMax: 0.7, color: '#10b981' },
  { zone: 3, name: 'Tempo', pctMin: 0.7, pctMax: 0.8, color: '#f59e0b' },
  { zone: 4, name: 'Threshold', pctMin: 0.8, pctMax: 0.9, color: '#f97316' },
  { zone: 5, name: 'VO2max', pctMin: 0.9, pctMax: 1.0, color: '#ef4444' },
] as const;

/** Compute Karvonen zones client-side (mirrors backend formula). */
function calculateKarvonenZones(rhr: number, mhr: number) {
  return KARVONEN_ZONES.map((z) => ({
    zone: z.zone,
    name: z.name,
    color: z.color,
    lower_bpm: Math.round(rhr + (mhr - rhr) * z.pctMin),
    upper_bpm: Math.round(rhr + (mhr - rhr) * z.pctMax),
  }));
}

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
export function AthleteProfilePage() {
  const { toast } = useToast();
  const apiKeys = useApiKeySettings();

  // HR state
  const [restingHr, setRestingHr] = useState('');
  const [maxHr, setMaxHr] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track saved HR values for dirty detection
  const savedHrRef = useRef({ restingHr: '', maxHr: '' });

  // Elevation state
  const [gainFactor, setGainFactor] = useState('10.0');
  const [lossFactor, setLossFactor] = useState('5.0');
  const [elevSaving, setElevSaving] = useState(false);
  const [elevError, setElevError] = useState<string | null>(null);

  // Track saved elevation values for dirty detection
  const savedElevRef = useRef({ gainFactor: '10.0', lossFactor: '5.0' });

  // Live-preview: compute zones from current input values
  const liveZones = useMemo(() => {
    const rhr = parseInt(restingHr, 10);
    const mhr = parseInt(maxHr, 10);
    if (isNaN(rhr) || isNaN(mhr) || rhr >= mhr) return null;
    return calculateKarvonenZones(rhr, mhr);
  }, [restingHr, maxHr]);

  // Dirty detection
  const hrDirty = restingHr !== savedHrRef.current.restingHr || maxHr !== savedHrRef.current.maxHr;
  const elevDirty =
    gainFactor !== savedElevRef.current.gainFactor ||
    lossFactor !== savedElevRef.current.lossFactor;

  useEffect(() => {
    loadSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- runs once on mount
  }, []);

  const loadSettings = async () => {
    try {
      const [settings] = await Promise.all([getAthleteSettings(), apiKeys.loadKeys()]);
      const rhr = settings.resting_hr?.toString() || '';
      const mhr = settings.max_hr?.toString() || '';
      const gf = settings.elevation_gain_factor.toString();
      const lf = settings.elevation_loss_factor.toString();
      setRestingHr(rhr);
      setMaxHr(mhr);
      setGainFactor(gf);
      setLossFactor(lf);
      savedHrRef.current = { restingHr: rhr, maxHr: mhr };
      savedElevRef.current = { gainFactor: gf, lossFactor: lf };
    } catch {
      setError('Einstellungen konnten nicht geladen werden');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveHR = async () => {
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
      await updateAthleteSettings({ resting_hr: rhr, max_hr: mhr });
      savedHrRef.current = { restingHr, maxHr };
      toast({ title: 'Herzfrequenz gespeichert', variant: 'success' });
    } catch {
      setError('Speichern fehlgeschlagen');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveElevation = async () => {
    const gf = parseFloat(gainFactor);
    const lf = parseFloat(lossFactor);

    if (isNaN(gf) || gf < 0 || gf > 30) {
      setElevError('Anstieg-Faktor muss zwischen 0 und 30 liegen');
      return;
    }
    if (isNaN(lf) || lf < 0 || lf > 20) {
      setElevError('Abstieg-Faktor muss zwischen 0 und 20 liegen');
      return;
    }

    setElevSaving(true);
    setElevError(null);

    try {
      await updateAthleteSettings({
        elevation_gain_factor: gf,
        elevation_loss_factor: lf,
      });
      savedElevRef.current = { gainFactor, lossFactor };
      toast({ title: 'Höhenkorrektur gespeichert', variant: 'success' });
    } catch {
      setElevError('Speichern fehlgeschlagen');
    } finally {
      setElevSaving(false);
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
    <div className="p-4 pt-8 md:p-6 md:pt-10 max-w-5xl mx-auto space-y-6">
      <header className="pb-2">
        <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
          Athletenprofil
        </h1>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Herzfrequenz-Zonen, Höhenkorrektur und API-Schlüssel konfigurieren.
        </p>
      </header>

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

          {/* Karvonen Zones — live preview from current inputs */}
          {liveZones && (
            <div className="mt-6 pt-6 border-t border-[var(--color-border-default)]">
              <h3 className="text-sm font-semibold text-[var(--color-text-base)] mb-3">
                Karvonen-Zonen (5 Zonen)
              </h3>
              <div className="space-y-2">
                {liveZones.map((zone) => (
                  <div
                    key={zone.zone}
                    className="flex items-center justify-between py-2 px-3 rounded-[var(--radius-component-sm)]"
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
                      {zone.lower_bpm}–{zone.upper_bpm} bpm
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mt-3">
                Berechnet via Karvonen-Formel: HR = Ruhe-HR + (Max-HR − Ruhe-HR) × Intensität%
              </p>
            </div>
          )}
        </CardBody>
        <CardFooter className="justify-end pt-4">
          <Button
            variant="primary"
            onClick={handleSaveHR}
            disabled={saving || !restingHr || !maxHr || !hrDirty}
          >
            {saving ? <Spinner size="sm" aria-hidden="true" /> : 'Speichern'}
          </Button>
        </CardFooter>
      </Card>

      {/* Elevation Correction */}
      <Card elevation="raised" padding="spacious">
        <CardHeader>
          <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
            Höhenkorrektur (GAP)
          </h2>
        </CardHeader>
        <CardBody>
          <p className="text-xs text-[var(--color-text-muted)] mb-4">
            Korrekturfaktoren für die höhenbereinigte Pace (Grade Adjusted Pace). Höhere Werte
            bedeuten stärkere Korrektur.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="gain-factor">Anstieg (Sek/km pro 100m)</Label>
              <Input
                id="gain-factor"
                type="number"
                min={0}
                max={30}
                step={0.5}
                placeholder="10.0"
                value={gainFactor}
                onChange={(e) => setGainFactor(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="loss-factor">Abstieg (Sek/km pro 100m)</Label>
              <Input
                id="loss-factor"
                type="number"
                min={0}
                max={20}
                step={0.5}
                placeholder="5.0"
                value={lossFactor}
                onChange={(e) => setLossFactor(e.target.value)}
              />
            </div>
          </div>

          {elevError && (
            <Alert variant="error" closeable onClose={() => setElevError(null)} className="mt-4">
              <AlertDescription>{elevError}</AlertDescription>
            </Alert>
          )}
        </CardBody>
        <CardFooter className="justify-end pt-4">
          <Button
            variant="primary"
            onClick={handleSaveElevation}
            disabled={elevSaving || !gainFactor || !lossFactor || !elevDirty}
          >
            {elevSaving ? <Spinner size="sm" aria-hidden="true" /> : 'Speichern'}
          </Button>
        </CardFooter>
      </Card>

      {/* API Keys */}
      <ApiKeyCard keys={apiKeys} />

      {/* KI Debug Log Link */}
      <Card elevation="raised" padding="spacious">
        <CardBody className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">KI Analyse-Log</h3>
            <p className="text-xs text-[var(--color-text-muted)]">
              Alle KI-Anfragen und -Antworten einsehen
            </p>
          </div>
          <Link to="/ki-log">
            <Button variant="secondary" size="sm">
              Log öffnen
            </Button>
          </Link>
        </CardBody>
      </Card>
    </div>
  );
}
