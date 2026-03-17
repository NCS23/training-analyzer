import { useEffect, useCallback, useState } from 'react';
import {
  Card,
  CardBody,
  Button,
  Badge,
  Spinner,
  Alert,
  AlertDescription,
} from '@nordlig/components';
import {
  Sparkles,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  Activity,
  Gauge,
  Calendar,
  CalendarPlus,
} from 'lucide-react';
import type { WeeklyReview, OverallRating, FatigueLevel } from '@/api/training';
import { applyRecommendations } from '@/api/weekly-plan';
import { useWeeklyReview } from '@/hooks/useWeeklyReview';

// --- Config ---

const ratingConfig: Record<
  OverallRating,
  { label: string; variant: string; icon: typeof CheckCircle2 }
> = {
  excellent: { label: 'Ausgezeichnet', variant: 'success', icon: CheckCircle2 },
  good: { label: 'Gut', variant: 'primary', icon: TrendingUp },
  moderate: { label: 'Mäßig', variant: 'warning', icon: Activity },
  poor: { label: 'Schwach', variant: 'error', icon: TrendingDown },
};

const fatigueConfig: Record<FatigueLevel, { label: string; variant: string }> = {
  low: { label: 'Niedrig', variant: 'success' },
  moderate: { label: 'Moderat', variant: 'primary' },
  high: { label: 'Hoch', variant: 'warning' },
  critical: { label: 'Kritisch', variant: 'error' },
};

// --- Sub-Komponenten ---

function EmptyState({
  onGenerate,
  loading,
  error,
}: {
  onGenerate: () => void;
  loading: boolean;
  error: string | null;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-6">
      <Sparkles className="w-8 h-8 text-[var(--color-text-primary)]" />
      <p className="text-sm text-[var(--color-text-muted)] text-center max-w-xs">
        Lass dir ein KI-Review deiner Trainingswoche generieren — mit Zusammenfassung, Highlights
        und Empfehlungen.
      </p>
      {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}
      <Button onClick={onGenerate} disabled={loading}>
        {loading ? (
          <Spinner size="sm" className="mr-1.5" />
        ) : (
          <Sparkles className="w-4 h-4 mr-1.5" />
        )}
        Review generieren
      </Button>
    </div>
  );
}

function VolumeRow({ review }: { review: WeeklyReview }) {
  const vol = review.volume_comparison;
  return (
    <div className="grid grid-cols-3 gap-3">
      <div className="rounded-[var(--radius-md)] bg-[var(--color-bg-surface)] p-3 text-center">
        <span className="text-lg font-semibold text-[var(--color-text-default)]">
          {vol.actual_km}
        </span>
        <span className="block text-xs text-[var(--color-text-muted)]">km</span>
      </div>
      <div className="rounded-[var(--radius-md)] bg-[var(--color-bg-surface)] p-3 text-center">
        <span className="text-lg font-semibold text-[var(--color-text-default)]">
          {vol.actual_sessions}
        </span>
        <span className="block text-xs text-[var(--color-text-muted)]">Sessions</span>
      </div>
      <div className="rounded-[var(--radius-md)] bg-[var(--color-bg-surface)] p-3 text-center">
        <span className="text-lg font-semibold text-[var(--color-text-default)]">
          {vol.actual_hours}
        </span>
        <span className="block text-xs text-[var(--color-text-muted)]">Stunden</span>
      </div>
    </div>
  );
}

function ListItems({
  title,
  items,
  icon: Icon,
}: {
  title: string;
  items: string[];
  icon: typeof Lightbulb;
}) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5">
        <Icon className="w-4 h-4 text-[var(--color-text-primary)]" />
        <span className="text-sm font-medium text-[var(--color-text-default)]">{title}</span>
      </div>
      <ul className="space-y-1.5 pl-5.5">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-[var(--color-text-muted)] list-disc">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ApplySection({
  applying,
  applyError,
  appliedCount,
  onApply,
}: {
  applying: boolean;
  applyError: string | null;
  appliedCount: number | null;
  onApply: () => void;
}) {
  return (
    <div className="pt-2 border-t border-[var(--color-border-muted)] space-y-2">
      {applyError && (
        <Alert variant="error">
          <AlertDescription>{applyError}</AlertDescription>
        </Alert>
      )}
      {appliedCount !== null && appliedCount > 0 && (
        <Alert variant="success">
          <AlertDescription>
            {appliedCount} {appliedCount === 1 ? 'Empfehlung' : 'Empfehlungen'} in den Plan der
            nächsten Woche übernommen.
          </AlertDescription>
        </Alert>
      )}
      {appliedCount === null && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onApply}
          disabled={applying}
          className="w-full"
        >
          {applying ? (
            <Spinner size="sm" className="mr-1.5" />
          ) : (
            <CalendarPlus className="w-4 h-4 mr-1.5" />
          )}
          {applying ? 'Wird übernommen…' : 'In Wochenplan übernehmen'}
        </Button>
      )}
    </div>
  );
}

function ReviewBody({
  review,
  loading,
  error,
  applying,
  applyError,
  appliedCount,
  onRefresh,
  onApply,
}: {
  review: WeeklyReview;
  loading: boolean;
  error: string | null;
  applying: boolean;
  applyError: string | null;
  appliedCount: number | null;
  onRefresh: () => void;
  onApply: () => void;
}) {
  const rating = ratingConfig[review.overall_rating] ?? ratingConfig.moderate;
  const fatigue = fatigueConfig[review.fatigue_assessment] ?? fatigueConfig.moderate;
  const RatingIcon = rating.icon;
  const hasRecommendations = review.next_week_recommendations.length > 0;

  return (
    <>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-[var(--color-text-primary)]" />
          <span className="text-sm font-semibold text-[var(--color-text-default)]">KI-Review</span>
        </div>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
          Neu
        </Button>
      </div>

      <div className="space-y-4 mt-3">
        {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}

        {/* Bewertung + Ermüdung */}
        <div className="flex flex-wrap gap-2">
          <Badge variant={rating.variant as 'success' | 'warning' | 'error' | 'primary'} size="xs">
            <RatingIcon className="w-3 h-3 mr-1" />
            {rating.label}
          </Badge>
          <Badge variant={fatigue.variant as 'success' | 'warning' | 'error' | 'primary'} size="xs">
            <Gauge className="w-3 h-3 mr-1" />
            Ermüdung: {fatigue.label}
          </Badge>
        </div>

        {/* Zusammenfassung */}
        <p className="text-sm text-[var(--color-text-default)]">{review.summary}</p>

        {/* Volumen */}
        <VolumeRow review={review} />

        {/* Highlights */}
        <ListItems title="Highlights" items={review.highlights} icon={CheckCircle2} />

        {/* Verbesserungspotenzial */}
        <ListItems
          title="Verbesserungspotenzial"
          items={review.improvements}
          icon={AlertTriangle}
        />

        {/* Empfehlungen für nächste Woche */}
        <ListItems
          title="Empfehlungen für nächste Woche"
          items={review.next_week_recommendations}
          icon={Lightbulb}
        />

        {/* In Plan übernehmen */}
        {hasRecommendations && (
          <ApplySection
            applying={applying}
            applyError={applyError}
            appliedCount={appliedCount}
            onApply={onApply}
          />
        )}
      </div>
    </>
  );
}

// --- Hauptkomponente ---

interface WeeklyReviewSectionProps {
  weekStart: string;
  onRecommendationsApplied?: () => void;
}

export function WeeklyReviewSection({
  weekStart,
  onRecommendationsApplied,
}: WeeklyReviewSectionProps) {
  const { review, loading, error, generate, fetch: fetchReview } = useWeeklyReview();
  const [initialized, setInitialized] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [appliedCount, setAppliedCount] = useState<number | null>(null);

  const handleFetch = useCallback(
    async (ws: string) => {
      setInitialized(true);
      setAppliedCount(null);
      setApplyError(null);
      await fetchReview(ws);
    },
    [fetchReview],
  );

  useEffect(() => {
    handleFetch(weekStart);
  }, [weekStart]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleGenerate = useCallback(() => {
    setAppliedCount(null);
    setApplyError(null);
    generate(weekStart, false);
  }, [generate, weekStart]);

  const handleRefresh = useCallback(() => {
    setAppliedCount(null);
    setApplyError(null);
    generate(weekStart, true);
  }, [generate, weekStart]);

  const handleApply = useCallback(async () => {
    if (!review?.next_week_recommendations.length) return;

    setApplying(true);
    setApplyError(null);
    try {
      const result = await applyRecommendations({
        week_start: weekStart,
        recommendations: review.next_week_recommendations,
      });
      setAppliedCount(result.applied_count);
      onRecommendationsApplied?.();
    } catch {
      setApplyError('Empfehlungen konnten nicht übernommen werden.');
    } finally {
      setApplying(false);
    }
  }, [review, weekStart, onRecommendationsApplied]);

  return (
    <Card elevation="raised">
      <CardBody>
        {loading && !review && (
          <div className="flex flex-col items-center gap-3 py-8">
            <Spinner size="md" />
            <p className="text-sm text-[var(--color-text-muted)]">Review wird geladen…</p>
          </div>
        )}

        {!loading && !review && initialized && (
          <EmptyState onGenerate={handleGenerate} loading={loading} error={error} />
        )}

        {review && (
          <ReviewBody
            review={review}
            loading={loading}
            error={error}
            applying={applying}
            applyError={applyError}
            appliedCount={appliedCount}
            onRefresh={handleRefresh}
            onApply={handleApply}
          />
        )}
      </CardBody>
    </Card>
  );
}
