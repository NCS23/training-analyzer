import { useState, useCallback } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Spinner,
  Alert,
  AlertDescription,
} from '@nordlig/components';
import { Sparkles, RefreshCw, Lightbulb } from 'lucide-react';
import { analyzeSession } from '@/api/training';
import type { SessionAnalysis } from '@/api/training';

interface SessionAIAnalysisProps {
  sessionId: number;
  cachedAnalysis: SessionAnalysis | null;
  onAnalysisLoaded: (analysis: SessionAnalysis) => void;
}

function IntensitySection({ text }: { text: string }) {
  return (
    <div className="space-y-1">
      <span className="text-sm font-medium text-[var(--color-text-default)]">Intensität</span>
      <p className="text-sm text-[var(--color-text-muted)]">{text}</p>
    </div>
  );
}

function RecommendationsList({ items }: { items: string[] }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-1.5">
        <Lightbulb className="w-4 h-4 text-[var(--color-text-warning)]" />
        <span className="text-sm font-medium text-[var(--color-text-default)]">Empfehlungen</span>
      </div>
      <ul className="space-y-1 pl-5.5">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-[var(--color-text-muted)] list-disc">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function AnalysisContent({
  analysis,
  onRefresh,
  loading,
  error,
}: {
  analysis: SessionAnalysis;
  onRefresh: () => void;
  loading: boolean;
  error: string | null;
}) {
  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--color-text-primary)]" />
            <span className="text-sm font-semibold text-[var(--color-text-default)]">
              KI-Analyse
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Neu
          </Button>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-4">
          <p className="text-sm text-[var(--color-text-default)]">{analysis.summary}</p>
          <IntensitySection text={analysis.intensity_text} />
          <div className="space-y-1">
            <span className="text-sm font-medium text-[var(--color-text-default)]">
              HF-Zonen-Bewertung
            </span>
            <p className="text-sm text-[var(--color-text-muted)]">{analysis.hr_zone_assessment}</p>
          </div>
          {analysis.plan_comparison && (
            <div className="space-y-1">
              <span className="text-sm font-medium text-[var(--color-text-default)]">
                Soll/Ist-Vergleich
              </span>
              <p className="text-sm text-[var(--color-text-muted)]">{analysis.plan_comparison}</p>
            </div>
          )}
          {analysis.fatigue_indicators && (
            <Alert variant="warning">
              <AlertDescription>{analysis.fatigue_indicators}</AlertDescription>
            </Alert>
          )}
          {analysis.recommendations.length > 0 && (
            <RecommendationsList items={analysis.recommendations} />
          )}
          {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}
        </div>
      </CardBody>
    </Card>
  );
}

export function SessionAIAnalysis({
  sessionId,
  cachedAnalysis,
  onAnalysisLoaded,
}: SessionAIAnalysisProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = useCallback(
    async (forceRefresh = false) => {
      setLoading(true);
      setError(null);
      try {
        const result = await analyzeSession(sessionId, forceRefresh);
        onAnalysisLoaded(result);
      } catch {
        setError('Analyse fehlgeschlagen. Bitte erneut versuchen.');
      } finally {
        setLoading(false);
      }
    },
    [sessionId, onAnalysisLoaded],
  );

  if (!cachedAnalysis && !loading) {
    return (
      <Card elevation="raised">
        <CardBody>
          <div className="flex flex-col items-center gap-3 py-4">
            <Sparkles className="w-8 h-8 text-[var(--color-text-primary)]" />
            <p className="text-sm text-[var(--color-text-muted)] text-center">
              Lass dein Training von der KI analysieren
            </p>
            {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}
            <Button onClick={() => handleAnalyze(false)} disabled={loading}>
              <Sparkles className="w-4 h-4 mr-1.5" />
              KI-Analyse starten
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card elevation="raised">
        <CardBody>
          <div className="flex flex-col items-center gap-3 py-6">
            <Spinner size="md" />
            <p className="text-sm text-[var(--color-text-muted)]">Analyse läuft…</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!cachedAnalysis) return null;

  return (
    <AnalysisContent
      analysis={cachedAnalysis}
      onRefresh={() => handleAnalyze(true)}
      loading={loading}
      error={error}
    />
  );
}
