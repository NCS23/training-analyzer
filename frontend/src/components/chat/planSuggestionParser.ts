import type { PlanSuggestion } from './PlanSuggestionCard';

/**
 * Parst Plan-Vorschläge aus der KI-Antwort.
 *
 * Format: ```plan-change\n{JSON}\n```
 * Die KI wird per System-Prompt instruiert, dieses Format zu verwenden.
 */
export function parsePlanSuggestions(content: string): {
  text: string;
  suggestions: PlanSuggestion[];
} {
  const suggestions: PlanSuggestion[] = [];

  const text = content.replace(/```plan-change\n([\s\S]*?)```/g, (_match, json: string) => {
    try {
      const parsed = JSON.parse(json) as PlanSuggestion;
      if (parsed.action && parsed.day && parsed.description) {
        suggestions.push(parsed);
      }
    } catch {
      // Fehlerhaftes JSON → ignorieren
    }
    return '';
  });

  return { text: text.trim(), suggestions };
}
