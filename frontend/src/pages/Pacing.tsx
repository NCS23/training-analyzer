import { useState, useEffect, useCallback } from 'react';
import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Card,
  CardBody,
  useToast,
} from '@nordlig/components';
import { Printer, Info } from 'lucide-react';
import { listGoals } from '@/api/goals';
import type { RaceGoal } from '@/api/goals';
import { generatePacing } from '@/api/pacing';
import type { PacingRequest, PacingResponse } from '@/api/pacing';
import { PacingForm } from '@/components/pacing/PacingForm';
import { PacingTable } from '@/components/pacing/PacingTable';
import { PacingChart } from '@/components/pacing/PacingChart';

const PRINT_STYLES = `
@media print {
  body * { visibility: hidden; }
  .pacing-result, .pacing-result * { visibility: visible; }
  .pacing-result { position: absolute; left: 0; top: 0; width: 100%; }
  .print\\:hidden { display: none !important; }
}`;

function PacingResult({ result }: { result: PacingResponse }) {
  return (
    <div className="space-y-4 pacing-result">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold text-[var(--color-text-base)]">
            {result.strategy_label}
          </h2>
          <Badge variant="primary" size="sm">
            {result.distance_km} km
          </Badge>
          <Badge variant="neutral" size="sm">
            {result.target_time_formatted}
          </Badge>
          <Badge variant="neutral" size="sm">
            &#x2300; {result.avg_pace_formatted}/km
          </Badge>
        </div>
        <Button variant="ghost" size="sm" onClick={() => window.print()} className="print:hidden">
          <Printer size={16} />
          Drucken
        </Button>
      </div>

      {result.weather_adjustment && (
        <Alert variant="info">
          <AlertDescription>
            <strong>Wetter-Anpassung:</strong> {result.weather_adjustment.description} (+
            {result.weather_adjustment.penalty_sec_per_km.toFixed(0)}s/km auf Zielzeit)
          </AlertDescription>
        </Alert>
      )}

      <PacingChart result={result} />
      <PacingTable result={result} />

      {result.notes.length > 0 && (
        <Card elevation="flat">
          <CardBody>
            <div className="flex items-start gap-2">
              <Info size={16} className="text-[var(--color-text-muted)] mt-0.5 shrink-0" />
              <ul className="text-sm text-[var(--color-text-muted)] space-y-1">
                {result.notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

export function PacingPage() {
  const { toast } = useToast();
  const [goals, setGoals] = useState<RaceGoal[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PacingResponse | null>(null);

  const loadGoals = useCallback(async () => {
    try {
      const res = await listGoals();
      setGoals(res.goals);
    } catch {
      // Goals sind optional — kein harter Fehler
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  const handleGenerate = async (params: PacingRequest) => {
    setLoading(true);
    try {
      setResult(await generatePacing(params));
    } catch {
      toast({ title: 'Fehler beim Generieren der Pacing-Strategie', variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-4">
            Pacing-Strategie erstellen
          </h2>
          <PacingForm goals={goals} loading={loading} onGenerate={handleGenerate} />
        </CardBody>
      </Card>

      {result && <PacingResult result={result} />}
      <style>{PRINT_STYLES}</style>
    </div>
  );
}
