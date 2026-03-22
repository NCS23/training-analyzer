import { Card, CardHeader, CardBody, Button, Spinner } from '@nordlig/components';
import { Sparkles, ThumbsUp, Lightbulb } from 'lucide-react';
import type { RaceAnalysis } from '@/api/training';

interface RaceAIAnalysisProps {
  analysis: RaceAnalysis | null;
  isAnalyzing: boolean;
  onTrigger: () => void;
}

export function RaceAIAnalysis({ analysis, isAnalyzing, onTrigger }: RaceAIAnalysisProps) {
  return (
    <Card elevation="raised">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--color-text-muted)]" />
            <h2 className="text-sm font-semibold text-[var(--color-text-base)]">
              KI-Wettkampfanalyse
            </h2>
          </div>
          {!analysis && !isAnalyzing && (
            <Button variant="secondary" size="sm" onClick={onTrigger}>
              Analyse starten
            </Button>
          )}
        </div>
      </CardHeader>
      <CardBody>
        {isAnalyzing && (
          <div className="flex items-center justify-center gap-2 py-6">
            <Spinner size="sm" />
            <span className="text-sm text-[var(--color-text-muted)]">Analyse laeuft...</span>
          </div>
        )}

        {!analysis && !isAnalyzing && (
          <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
            Starte die KI-Analyse fuer eine detaillierte Wettkampfbewertung
          </p>
        )}

        {analysis && (
          <div className="space-y-4">
            <p className="text-sm text-[var(--color-text-base)]">{analysis.summary}</p>

            {analysis.pacing_assessment && (
              <div>
                <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-1">
                  Pacing-Bewertung
                </p>
                <p className="text-sm text-[var(--color-text-base)]">
                  {analysis.pacing_assessment}
                </p>
              </div>
            )}

            {analysis.goal_assessment && (
              <div>
                <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-1">
                  Zielbewertung
                </p>
                <p className="text-sm text-[var(--color-text-base)]">{analysis.goal_assessment}</p>
              </div>
            )}

            {analysis.what_went_well.length > 0 && (
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <ThumbsUp className="w-3 h-3 text-[var(--color-text-success)]" />
                  <p className="text-xs font-semibold text-[var(--color-text-success)]">
                    Was gut lief
                  </p>
                </div>
                <ul className="space-y-1">
                  {analysis.what_went_well.map((item, i) => (
                    <li key={i} className="text-sm text-[var(--color-text-base)] pl-4">
                      • {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {analysis.lessons_learned.length > 0 && (
              <div>
                <div className="flex items-center gap-1 mb-1">
                  <Lightbulb className="w-3 h-3 text-[var(--color-text-warning)]" />
                  <p className="text-xs font-semibold text-[var(--color-text-warning)]">
                    Learnings
                  </p>
                </div>
                <ul className="space-y-1">
                  {analysis.lessons_learned.map((item, i) => (
                    <li key={i} className="text-sm text-[var(--color-text-base)] pl-4">
                      • {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
