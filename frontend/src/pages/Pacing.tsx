import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Card,
  CardBody,
  useToast,
} from '@nordlig/components';
import { Printer, Info, Download, CalendarPlus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { listGoals } from '@/api/goals';
import {
  generatePacing,
  exportPacingFit,
  transferPacingToWeeklyPlan,
  listSavedStrategies,
} from '@/api/pacing';
import type { PacingRequest, PacingResponse } from '@/api/pacing';
import { PacingForm } from '@/components/pacing/PacingForm';
import type { SavedStrategyPrefill } from '@/components/pacing/PacingForm';
import { PacingTable } from '@/components/pacing/PacingTable';
import { PacingChart } from '@/components/pacing/PacingChart';

const PRINT_STYLES = `
@media print {
  body * { visibility: hidden; }
  .pacing-result, .pacing-result * { visibility: visible; }
  .pacing-result { position: absolute; left: 0; top: 0; width: 100%; }
  .print\\:hidden { display: none !important; }
}`;

function PacingActions({ params }: { params: PacingRequest }) {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [exporting, setExporting] = useState(false);
  const [transferring, setTransferring] = useState(false);

  const handleFitExport = async () => {
    setExporting(true);
    try {
      await exportPacingFit(params);
    } catch {
      toast({ title: 'Fehler beim FIT-Export', variant: 'error' });
    } finally {
      setExporting(false);
    }
  };

  const handleTransfer = async () => {
    if (!params.goal_id) return;
    setTransferring(true);
    try {
      const res = await transferPacingToWeeklyPlan({
        goal_id: params.goal_id,
        pacing_request: params,
      });
      toast({ title: res.message, variant: 'success' });
      navigate(`/plan?week=${res.race_date}`);
    } catch {
      toast({ title: 'Fehler beim Übernehmen in den Wochenplan', variant: 'error' });
    } finally {
      setTransferring(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2 print:hidden">
      {params.goal_id && (
        <Button variant="secondary" size="sm" onClick={handleTransfer} disabled={transferring}>
          <CalendarPlus size={16} />
          {transferring ? 'Übernehme…' : 'In Wochenplan übernehmen'}
        </Button>
      )}
      <Button variant="ghost" size="sm" onClick={handleFitExport} disabled={exporting}>
        <Download size={16} />
        {exporting ? 'Exportiere…' : 'FIT exportieren'}
      </Button>
      <Button variant="ghost" size="sm" onClick={() => window.print()}>
        <Printer size={16} />
        Drucken
      </Button>
    </div>
  );
}

function PacingResult({ result, params }: { result: PacingResponse; params: PacingRequest }) {
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
        <PacingActions params={params} />
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
  const { data: goalsData } = useQuery({
    queryKey: ['goals'],
    queryFn: listGoals,
  });
  const goals = goalsData?.goals ?? [];
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PacingResponse | null>(null);
  const [lastParams, setLastParams] = useState<PacingRequest | null>(null);
  const [prefill, setPrefill] = useState<SavedStrategyPrefill | null>(null);

  const handleGenerate = async (params: PacingRequest) => {
    setLoading(true);
    try {
      setLastParams(params);
      setResult(await generatePacing(params));
    } catch {
      toast({ title: 'Fehler beim Generieren der Pacing-Strategie', variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleGoalChange = useCallback(async (goalId: number | null) => {
    if (!goalId) {
      setResult(null);
      setLastParams(null);
      setPrefill(null);
      return;
    }
    try {
      const { strategies } = await listSavedStrategies(goalId);
      if (strategies.length > 0) {
        const latest = strategies[0]; // neueste zuerst
        // Ergebnis direkt anzeigen
        setResult({
          strategy: latest.strategy,
          strategy_label: latest.strategy_label,
          distance_km: latest.distance_km,
          target_time_seconds: latest.target_time_seconds,
          target_time_formatted: latest.target_time_formatted,
          avg_pace_sec_per_km: latest.avg_pace_sec_per_km,
          avg_pace_formatted: latest.avg_pace_formatted,
          splits: latest.splits,
          weather_adjustment: latest.weather_adjustment,
          notes: latest.notes,
        });
        setLastParams({
          target_time_seconds: latest.target_time_seconds,
          distance_km: latest.distance_km,
          strategy: latest.strategy as 'even' | 'negative' | 'effort_based',
          elevation_preset: (latest.elevation_preset as 'flat' | 'rolling' | 'hilly') ?? 'flat',
          goal_id: goalId,
        });
        setPrefill({
          strategy: latest.strategy,
          elevation_preset: latest.elevation_preset,
          weather_adjustment: latest.weather_adjustment,
        });
      } else {
        setResult(null);
        setLastParams(null);
        setPrefill(null);
      }
    } catch {
      // Fehler ignorieren — Formular bleibt leer
      setPrefill(null);
    }
  }, []);

  return (
    <div className="space-y-6">
      <Card elevation="raised" padding="spacious">
        <CardBody>
          <h2 className="text-lg font-semibold text-[var(--color-text-base)] mb-4">
            Pacing-Strategie erstellen
          </h2>
          <PacingForm
            goals={goals}
            loading={loading}
            onGenerate={handleGenerate}
            onGoalChange={handleGoalChange}
            savedStrategyPrefill={prefill}
          />
        </CardBody>
      </Card>

      {result && lastParams && <PacingResult result={result} params={lastParams} />}
      <style>{PRINT_STYLES}</style>
    </div>
  );
}
