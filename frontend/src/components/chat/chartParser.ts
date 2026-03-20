import type { ChartData } from './ChatChart';

/**
 * Parst spezielle Code-Blöcke aus der KI-Antwort und gibt ChartData zurück.
 * Format: ```chart\n{JSON}\n```
 */
export function parseChartBlocks(content: string): { text: string; charts: ChartData[] } {
  const charts: ChartData[] = [];
  const text = content.replace(/```chart\n([\s\S]*?)```/g, (_match, json: string) => {
    try {
      const parsed = JSON.parse(json) as ChartData;
      if (parsed.data && parsed.xKey && parsed.yKey) {
        charts.push(parsed);
      }
    } catch {
      // Fehlerhaftes JSON → ignorieren, Text beibehalten
    }
    return ''; // Chart-Block aus Text entfernen
  });

  return { text: text.trim(), charts };
}
