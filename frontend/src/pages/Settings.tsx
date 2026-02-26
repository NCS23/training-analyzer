import { useState, useEffect } from 'react';
import { Heart } from 'lucide-react';
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
import type { KarvonenZone } from '@/api/athlete';

export function SettingsPage() {
  const [restingHr, setRestingHr] = useState('');
  const [maxHr, setMaxHr] = useState('');
  const [zones, setZones] = useState<KarvonenZone[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadSettings();
  }, []);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-6">
      <header>
        <div className="flex items-center gap-3 mb-1">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-accent-3-100)]">
            <Heart className="w-5 h-5 text-[var(--color-accent-3-600)]" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-3xl font-semibold text-[var(--color-text-base)]">Einstellungen</h1>
            <p className="text-sm text-[var(--color-text-muted)]">
              Herzfrequenz-Daten fuer die Karvonen-Zonenberechnung.
            </p>
          </div>
        </div>
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
        </CardBody>
        <CardFooter className="justify-end pt-4">
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={saving || !restingHr || !maxHr}
          >
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
                  className="flex items-center justify-between py-2 px-3 rounded-md"
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
