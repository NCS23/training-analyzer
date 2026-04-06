import { Card, CardBody, Badge } from '@nordlig/components';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { FitnessScoreResponse } from '@/api/fitness';

interface Props {
  data: FitnessScoreResponse;
}

const FORM_COLOR: Record<string, string> = {
  green: 'var(--color-text-success)',
  yellow: 'var(--color-text-warning)',
  orange: 'var(--color-text-error)',
};

const ACWR_BADGE: Record<string, 'success' | 'warning' | 'error' | 'neutral'> = {
  low: 'neutral',
  optimal: 'success',
  warning: 'warning',
  danger: 'error',
};

function TrendIcon({ trend }: { trend: FitnessScoreResponse['trend'] }) {
  if (trend === 'rising')
    return <TrendingUp className="h-4 w-4 text-[var(--color-text-success)]" />;
  if (trend === 'falling')
    return <TrendingDown className="h-4 w-4 text-[var(--color-text-error)]" />;
  return <Minus className="h-4 w-4 text-[var(--color-text-muted)]" />;
}

export function ScoreSection({ data }: Props) {
  const formColor = FORM_COLOR[data.form.color] ?? 'var(--color-text-base)';

  return (
    <section aria-label="Fitness-Score">
      <Card elevation="raised">
        <CardBody>
          {/* Hauptscore */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-[var(--color-text-muted)]">Fitness-Score</p>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-5xl font-bold tabular-nums text-[var(--color-text-base)]">
                  {data.score}
                </span>
                <span className="text-sm text-[var(--color-text-muted)]">/ 100</span>
              </div>
            </div>
            <div className="text-right space-y-1">
              <div className="text-sm font-medium" style={{ color: formColor }}>
                {data.form.label}
              </div>
              <div className="flex items-center gap-1 justify-end">
                <TrendIcon trend={data.trend} />
                <span className="text-xs text-[var(--color-text-muted)]">{data.trend_label}</span>
              </div>
            </div>
          </div>

          {/* Sub-Scores */}
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-[var(--radius-component-sm)] bg-[var(--color-bg-subtle)] p-3">
              <p className="text-xs text-[var(--color-text-muted)]">Ausdauer</p>
              <p className="text-xl font-semibold tabular-nums text-[var(--color-text-base)] mt-0.5">
                {data.endurance_score}
              </p>
            </div>
            <div className="rounded-[var(--radius-component-sm)] bg-[var(--color-bg-subtle)] p-3">
              <p className="text-xs text-[var(--color-text-muted)]">Kraft</p>
              <p className="text-xl font-semibold tabular-nums text-[var(--color-text-base)] mt-0.5">
                {data.strength_score}
              </p>
            </div>
          </div>

          {/* Kontext-Nachricht */}
          {data.context_message && (
            <p className="mt-4 text-sm text-[var(--color-text-subtle)]">{data.context_message}</p>
          )}

          {/* Form-Empfehlung */}
          <p className="mt-2 text-xs text-[var(--color-text-muted)]">{data.form.recommendation}</p>

          {/* ACWR */}
          {data.acwr && (
            <div className="mt-4 flex items-center gap-2">
              <Badge variant={ACWR_BADGE[data.acwr.zone] ?? 'neutral'} size="sm">
                ACWR {data.acwr.ratio.toFixed(2)}
              </Badge>
              <span className="text-xs text-[var(--color-text-muted)]">{data.acwr.message}</span>
            </div>
          )}
        </CardBody>
      </Card>
    </section>
  );
}
