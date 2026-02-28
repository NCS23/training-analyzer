import { useState, useEffect } from 'react';
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
  Breadcrumbs,
  BreadcrumbItem,
} from '@nordlig/components';
import { ChevronRight } from 'lucide-react';
import { getAthleteSettings, updateAthleteSettings } from '@/api/athlete';
import type { KarvonenZone } from '@/api/athlete';

export function AthleteProfilePage() {
  const { toast } = useToast();

  // HR state
  const [restingHr, setRestingHr] = useState('');
  const [maxHr, setMaxHr] = useState('');
  const [zones, setZones] = useState<KarvonenZone[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Elevation state
  const [gainFactor, setGainFactor] = useState('10.0');
  const [lossFactor, setLossFactor] = useState('5.0');
  const [elevSaving, setElevSaving] = useState(false);
  const [elevError, setElevError] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await getAthleteSettings();
      setRestingHr(settings.resting_hr?.toString() || '');
      setMaxHr(settings.max_hr?.toString() || '');
      setGainFactor(settings.elevation_gain_factor.toString());
      setLossFactor(settings.elevation_loss_factor.toString());
      setZones(settings.karvonen_zones);
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
      const result = await updateAthleteSettings({ resting_hr: rhr, max_hr: mhr });
      setZones(result.karvonen_zones);
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
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <div className="space-y-2 pb-2">
        <Breadcrumbs separator={<ChevronRight className="w-3.5 h-3.5" />}>
          <BreadcrumbItem>
            <Link to="/settings" className="hover:underline underline-offset-2">
              Einstellungen
            </Link>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrent>Athletenprofil</BreadcrumbItem>
        </Breadcrumbs>
        <header>
          <h1 className="text-2xl md:text-3xl font-semibold text-[var(--color-text-base)]">
            Athletenprofil
          </h1>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Herzfrequenz-Zonen und Höhenkorrektur konfigurieren.
          </p>
        </header>
      </div>

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
          <Button variant="primary" onClick={handleSaveHR} disabled={saving || !restingHr || !maxHr}>
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
            Korrekturfaktoren für die höhenbereinigte Pace (Grade Adjusted Pace).
            Höhere Werte bedeuten stärkere Korrektur.
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
            disabled={elevSaving || !gainFactor || !lossFactor}
          >
            {elevSaving ? <Spinner size="sm" aria-hidden="true" /> : 'Speichern'}
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
                    {zone.lower_bpm}-{zone.upper_bpm} bpm
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mt-4">
              Berechnet via Karvonen-Formel: HR = Ruhe-HR + (Max-HR - Ruhe-HR) × Intensität%
            </p>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
