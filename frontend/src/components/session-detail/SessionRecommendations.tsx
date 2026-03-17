import { useEffect, useState } from 'react';
import { Card, CardHeader, CardBody, Button, Badge, Spinner } from '@nordlig/components';
import {
  Sparkles,
  RefreshCw,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Gauge,
  TrendingDown,
  BedDouble,
  SkipForward,
  TrendingUp,
  HeartPulse,
  ArrowLeftRight,
  Timer,
  Lightbulb,
} from 'lucide-react';
import type { AIRecommendation, RecommendationStatusValue } from '@/api/training';
import { useRecommendations } from '@/hooks/useRecommendations';
import { recommendationTypeLabels, recommendationPriorityConfig } from '@/constants/training';

// --- Icon-Mapping ---

const TYPE_ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  adjust_pace: Gauge,
  adjust_volume: TrendingDown,
  add_rest: BedDouble,
  skip_session: SkipForward,
  increase_volume: TrendingUp,
  reduce_intensity: HeartPulse,
  change_session_type: ArrowLeftRight,
  extend_warmup_cooldown: Timer,
  general: Lightbulb,
};

// --- Sub-Komponenten ---

function PriorityBadge({ priority }: { priority: string }) {
  const config = recommendationPriorityConfig[priority] ?? recommendationPriorityConfig.medium;
  return (
    <Badge variant={config.variant} size="xs">
      {config.label}
    </Badge>
  );
}

function StatusBadge({ status }: { status: RecommendationStatusValue }) {
  if (status === 'applied') {
    return (
      <Badge variant="primary-bold" size="xs">
        Übernommen
      </Badge>
    );
  }
  if (status === 'dismissed') {
    return (
      <Badge variant="neutral" size="xs">
        Abgelehnt
      </Badge>
    );
  }
  return null;
}

function RecommendationCard({
  recommendation,
  onUpdateStatus,
}: {
  recommendation: AIRecommendation;
  onUpdateStatus: (id: number, status: RecommendationStatusValue) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const Icon = TYPE_ICON_MAP[recommendation.type] ?? Lightbulb;
  const typeLabel = recommendationTypeLabels[recommendation.type] ?? 'Empfehlung';
  const isPending = recommendation.status === 'pending';

  return (
    <div
      className={`rounded-[var(--radius-md)] border p-3 sm:p-4 space-y-2 transition-opacity ${
        isPending
          ? 'border-[var(--color-border-default)] bg-[var(--color-bg-surface)]'
          : 'border-[var(--color-border-muted)] bg-[var(--color-bg-surface)] opacity-60'
      }`}
    >
      {/* Header: Icon + Titel + Badges */}
      <div className="flex items-start gap-2 sm:gap-3">
        <div className="mt-0.5 shrink-0">
          <Icon className="w-4 h-4 text-[var(--color-text-primary)]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-sm font-medium text-[var(--color-text-default)]">
              {recommendation.title}
            </span>
            <PriorityBadge priority={recommendation.priority} />
            <StatusBadge status={recommendation.status} />
          </div>
          <span className="text-xs text-[var(--color-text-muted)]">{typeLabel}</span>
        </div>

        {/* Expand/Collapse */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          aria-label={expanded ? 'Details zuklappen' : 'Details aufklappen'}
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-[var(--color-text-muted)]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[var(--color-text-muted)]" />
          )}
        </Button>
      </div>

      {/* Aktuell / Vorschlag (immer sichtbar wenn vorhanden) */}
      {(recommendation.current_value || recommendation.suggested_value) && (
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 pl-6 sm:pl-7">
          {recommendation.current_value && (
            <div className="text-xs">
              <span className="text-[var(--color-text-muted)]">Aktuell: </span>
              <span className="text-[var(--color-text-default)]">
                {recommendation.current_value}
              </span>
            </div>
          )}
          {recommendation.suggested_value && (
            <div className="text-xs">
              <span className="text-[var(--color-text-muted)]">Vorschlag: </span>
              <span className="font-medium text-[var(--color-text-primary)]">
                {recommendation.suggested_value}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Erweitert: Begründung + Aktionen */}
      {expanded && (
        <div className="pl-6 sm:pl-7 space-y-3">
          <p className="text-sm text-[var(--color-text-muted)]">{recommendation.reasoning}</p>

          {isPending && (
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onUpdateStatus(recommendation.id, 'applied')}
              >
                <Check className="w-3.5 h-3.5 mr-1" />
                Übernehmen
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onUpdateStatus(recommendation.id, 'dismissed')}
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Ablehnen
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- State-Komponenten ---

function EmptyState({ onGenerate, error }: { onGenerate: () => void; error: string | null }) {
  return (
    <Card elevation="raised">
      <CardBody>
        <div className="flex flex-col items-center gap-3 py-4">
          <Sparkles className="w-6 h-6 text-[var(--color-text-primary)]" />
          <p className="text-sm text-[var(--color-text-muted)] text-center">
            Lass dir konkrete Trainingsempfehlungen generieren
          </p>
          {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}
          <Button onClick={onGenerate}>
            <Sparkles className="w-4 h-4 mr-1.5" />
            Empfehlungen generieren
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}

function LoadingState() {
  return (
    <Card elevation="raised">
      <CardBody>
        <div className="flex flex-col items-center gap-3 py-6">
          <Spinner size="md" />
          <p className="text-sm text-[var(--color-text-muted)]">Empfehlungen werden generiert…</p>
        </div>
      </CardBody>
    </Card>
  );
}

function RecommendationsContent({
  recommendations,
  pendingCount,
  loading,
  error,
  onRefresh,
  onUpdateStatus,
}: {
  recommendations: AIRecommendation[];
  pendingCount: number;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onUpdateStatus: (id: number, status: RecommendationStatusValue) => void;
}) {
  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-[var(--color-text-warning)]" />
            <span className="text-sm font-semibold text-[var(--color-text-default)]">
              KI-Empfehlungen
            </span>
            {pendingCount > 0 && (
              <Badge variant="accent-bold" size="xs">
                {pendingCount} neu
              </Badge>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Neu
          </Button>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-2">
          {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}
          {recommendations.map((rec) => (
            <RecommendationCard key={rec.id} recommendation={rec} onUpdateStatus={onUpdateStatus} />
          ))}
        </div>
      </CardBody>
    </Card>
  );
}

// --- Sortier-Logik ---

function sortRecommendations(recs: AIRecommendation[]): AIRecommendation[] {
  return [...recs].sort((a, b) => {
    if (a.status === 'pending' && b.status !== 'pending') return -1;
    if (a.status !== 'pending' && b.status === 'pending') return 1;
    const prioA = recommendationPriorityConfig[a.priority]?.sortOrder ?? 1;
    const prioB = recommendationPriorityConfig[b.priority]?.sortOrder ?? 1;
    return prioA - prioB;
  });
}

// --- Hauptkomponente ---

interface SessionRecommendationsProps {
  sessionId: number;
  hasAnalysis: boolean;
}

export function SessionRecommendations({ sessionId, hasAnalysis }: SessionRecommendationsProps) {
  const { recommendations, loading, error, generate, fetch, updateStatus, pendingCount } =
    useRecommendations(sessionId);

  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (hasAnalysis && !initialized) {
      setInitialized(true);
      fetch();
    }
  }, [hasAnalysis, initialized, fetch]);

  if (!hasAnalysis) return null;

  if (!loading && recommendations.length === 0 && initialized) {
    return <EmptyState onGenerate={() => generate(false)} error={error} />;
  }

  if (loading && recommendations.length === 0) {
    return <LoadingState />;
  }

  if (recommendations.length === 0) return null;

  return (
    <RecommendationsContent
      recommendations={sortRecommendations(recommendations)}
      pendingCount={pendingCount}
      loading={loading}
      error={error}
      onRefresh={() => generate(true)}
      onUpdateStatus={updateStatus}
    />
  );
}
