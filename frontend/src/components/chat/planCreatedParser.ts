import type { PlanCreatedInfo } from './PlanCreatedCard';

/**
 * Parst Plan-Erstellungs-Blöcke aus der KI-Antwort.
 *
 * Format: ```plan-created\n{JSON}\n```
 * Die KI wird per System-Prompt instruiert, dieses Format nach
 * erfolgreicher Plan-Erstellung zu verwenden.
 */
export function parsePlanCreated(content: string): {
  text: string;
  plans: PlanCreatedInfo[];
} {
  const plans: PlanCreatedInfo[] = [];

  const text = content.replace(/```plan-created\n([\s\S]*?)```/g, (_match, json: string) => {
    try {
      const parsed = JSON.parse(json) as PlanCreatedInfo;
      if (parsed.plan_id && parsed.plan_name) {
        plans.push(parsed);
      }
    } catch {
      // Fehlerhaftes JSON ignorieren
    }
    return '';
  });

  return { text: text.trim(), plans };
}
