import type { WeekRewriteSuggestion } from './WeekRewriteCard';

/**
 * Parst Wochen-Umstrukturierungs-Vorschläge aus der KI-Antwort.
 *
 * Format: ```week-rewrite\n{JSON}\n```
 */
export function parseWeekRewrites(content: string): {
  text: string;
  rewrites: WeekRewriteSuggestion[];
} {
  const rewrites: WeekRewriteSuggestion[] = [];

  const text = content.replace(/```week-rewrite\n([\s\S]*?)```/g, (_match, json: string) => {
    try {
      const parsed = JSON.parse(json) as WeekRewriteSuggestion;
      if (
        parsed.review_week_start &&
        parsed.summary &&
        Array.isArray(parsed.recommendations) &&
        parsed.recommendations.length > 0
      ) {
        rewrites.push(parsed);
      }
    } catch {
      // Fehlerhaftes JSON → ignorieren
    }
    return '';
  });

  return { text: text.trim(), rewrites };
}
