import { Card, CardBody, Badge, Progress } from '@nordlig/components';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { FitnessScoreResponse } from '@/api/fitness';
import { ScoreRing } from './ScoreRing';

interface Props {
  data: FitnessScoreResponse;
}

const FORM_COLOR: Record<string, string> = {
  green: 'var(--color-text-success)',
  yellow: 'var(--color-text-warning)',
  orange: 'var(--color-text-error)',
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
          {/* Hero: Ring + Status */}
          <div className="flex items-center gap-5">
            <ScoreRing score={data.score} />

            <div className="flex-1 min-w-0 space-y-2">
              {/* Form + Trend */}
              <div>
                <span className="text-base font-semibold" style={{ color: formColor }}>
                  {data.form.label}
                </span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <TrendIcon trend={data.trend} />
                  <span className="text-xs text-[var(--color-text-muted)]">{data.trend_label}</span>
                </div>
              </div>

              {/* Sub-Scores als Progress-Bars */}
              <div className="space-y-2">
                <SubScore label="Ausdauer" value={data.endurance_score} />
                <SubScore label="Kraft" value={data.strength_score} />
              </div>
            </div>
          </div>

          {/* Empfehlung (1 Zeile) */}
          <p className="mt-4 text-sm text-[var(--color-text-muted)]">{data.form.recommendation}</p>

          {/* ACWR nur wenn nicht optimal */}
          {data.acwr && data.acwr.zone !== 'optimal' && (
            <div className="mt-3 flex items-center gap-2">
              <Badge variant={data.acwr.zone === 'danger' ? 'error' : 'warning'} size="sm">
                ACWR {data.acwr.ratio.toFixed(1)}
              </Badge>
              <span className="text-xs text-[var(--color-text-muted)] line-clamp-1">
                {data.acwr.message}
              </span>
            </div>
          )}
        </CardBody>
      </Card>
    </section>
  );
}

function SubScore({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-[var(--color-text-muted)] w-16 shrink-0">{label}</span>
      <Progress value={value} max={100} size="sm" className="flex-1" />
      <span className="text-xs font-medium tabular-nums text-[var(--color-text-base)] w-6 text-right">
        {value}
      </span>
    </div>
  );
}
