import { useEffect, useState, useCallback } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Badge,
  Spinner,
  Breadcrumbs,
  BreadcrumbItem,
} from '@nordlig/components';
import {
  Sparkles,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  Activity,
  Gauge,
  Calendar,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { WeeklyReview, OverallRating, FatigueLevel } from '@/api/training';
import { useWeeklyReview } from '@/hooks/useWeeklyReview';

// --- Hilfsfunktionen ---

function getMonday(d: Date): Date {
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(d.getFullYear(), d.getMonth(), diff);
}

function formatWeekStart(d: Date): string {
  return d.toISOString().split('T')[0];
}

function formatDateRange(weekStart: Date): string {
  const end = new Date(weekStart);
  end.setDate(end.getDate() + 6);
  const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' };
  return `${weekStart.toLocaleDateString('de-DE', opts)} – ${end.toLocaleDateString('de-DE', opts)}`;
}

function shiftWeek(weekStart: Date, delta: number): Date {
  const d = new Date(weekStart);
  d.setDate(d.getDate() + delta * 7);
  return d;
}

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

function WeekNavigator({
  weekStart,
  onNavigate,
}: {
  weekStart: Date;
  onNavigate: (d: Date) => void;
}) {
  const today = getMonday(new Date());
  const isCurrentWeek = formatWeekStart(weekStart) === formatWeekStart(today);

  return (
    <div className="flex items-center gap-2">
      <Button variant="ghost" size="sm" onClick={() => onNavigate(shiftWeek(weekStart, -1))}>
        <ChevronLeft className="w-4 h-4" />
      </Button>
      <div className="text-center min-w-[140px]">
        <span className="text-sm font-medium text-[var(--color-text-default)]">
          {formatDateRange(weekStart)}
        </span>
        {isCurrentWeek && (
          <span className="block text-xs text-[var(--color-text-muted)]">Aktuelle Woche</span>
        )}
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onNavigate(shiftWeek(weekStart, 1))}
        disabled={isCurrentWeek}
      >
        <ChevronRight className="w-4 h-4" />
      </Button>
    </div>
  );
}

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
    <Card elevation="raised">
      <CardBody>
        <div className="flex flex-col items-center gap-3 py-6">
          <Sparkles className="w-8 h-8 text-[var(--color-text-primary)]" />
          <p className="text-sm text-[var(--color-text-muted)] text-center max-w-xs">
            Lass dir ein KI-Review deiner Trainingswoche generieren — mit Zusammenfassung,
            Highlights und Empfehlungen.
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
      </CardBody>
    </Card>
  );
}

function LoadingState() {
  return (
    <Card elevation="raised">
      <CardBody>
        <div className="flex flex-col items-center gap-3 py-8">
          <Spinner size="md" />
          <p className="text-sm text-[var(--color-text-muted)]">Review wird generiert…</p>
        </div>
      </CardBody>
    </Card>
  );
}

function VolumeSection({ review }: { review: WeeklyReview }) {
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

function ListSection({
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

function ReviewContent({
  review,
  loading,
  error,
  onRefresh,
}: {
  review: WeeklyReview;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  const rating = ratingConfig[review.overall_rating] ?? ratingConfig.moderate;
  const fatigue = fatigueConfig[review.fatigue_assessment] ?? fatigueConfig.moderate;
  const RatingIcon = rating.icon;

  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-[var(--color-text-primary)]" />
            <span className="text-sm font-semibold text-[var(--color-text-default)]">
              Wochen-Review
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Neu
          </Button>
        </div>
      </CardHeader>
      <CardBody>
        <div className="space-y-4">
          {error && <p className="text-sm text-[var(--color-text-error)]">{error}</p>}

          {/* Bewertung + Ermüdung */}
          <div className="flex flex-wrap gap-2">
            <Badge
              variant={rating.variant as 'success' | 'warning' | 'error' | 'primary'}
              size="xs"
            >
              <RatingIcon className="w-3 h-3 mr-1" />
              {rating.label}
            </Badge>
            <Badge
              variant={fatigue.variant as 'success' | 'warning' | 'error' | 'primary'}
              size="xs"
            >
              <Gauge className="w-3 h-3 mr-1" />
              Ermüdung: {fatigue.label}
            </Badge>
          </div>

          {/* Zusammenfassung */}
          <p className="text-sm text-[var(--color-text-default)]">{review.summary}</p>

          {/* Volumen */}
          <VolumeSection review={review} />

          {/* Highlights */}
          <ListSection title="Highlights" items={review.highlights} icon={CheckCircle2} />

          {/* Verbesserungspotenzial */}
          <ListSection
            title="Verbesserungspotenzial"
            items={review.improvements}
            icon={AlertTriangle}
          />

          {/* Empfehlungen für nächste Woche */}
          <ListSection
            title="Empfehlungen für nächste Woche"
            items={review.next_week_recommendations}
            icon={Lightbulb}
          />
        </div>
      </CardBody>
    </Card>
  );
}

// --- Hauptkomponente ---

export function WeeklyReviewPage() {
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const { review, loading, error, generate, fetch } = useWeeklyReview();
  const [initialized, setInitialized] = useState(false);

  const weekKey = formatWeekStart(weekStart);

  const handleFetch = useCallback(
    async (ws: Date) => {
      setInitialized(true);
      await fetch(formatWeekStart(ws));
    },
    [fetch],
  );

  useEffect(() => {
    handleFetch(weekStart);
  }, [weekKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleNavigate = useCallback((d: Date) => {
    setWeekStart(d);
    setInitialized(false);
  }, []);

  const handleGenerate = useCallback(() => {
    generate(weekKey, false);
  }, [generate, weekKey]);

  const handleRefresh = useCallback(() => {
    generate(weekKey, true);
  }, [generate, weekKey]);

  return (
    <div className="p-4 pt-6 md:p-6 md:pt-8 max-w-5xl mx-auto space-y-6">
      <header className="space-y-2 pb-2">
        <Breadcrumbs>
          <BreadcrumbItem>
            <Link to="/dashboard">Dashboard</Link>
          </BreadcrumbItem>
          <BreadcrumbItem>Wochen-Review</BreadcrumbItem>
        </Breadcrumbs>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h1 className="text-xl font-bold text-[var(--color-text-default)]">
            Wöchentliches KI-Review
          </h1>
          <WeekNavigator weekStart={weekStart} onNavigate={handleNavigate} />
        </div>
      </header>

      {loading && !review && <LoadingState />}

      {!loading && !review && initialized && (
        <EmptyState onGenerate={handleGenerate} loading={loading} error={error} />
      )}

      {review && (
        <ReviewContent review={review} loading={loading} error={error} onRefresh={handleRefresh} />
      )}
    </div>
  );
}
