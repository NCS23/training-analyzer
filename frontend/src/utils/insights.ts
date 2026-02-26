import type { SessionDetail, HRZone } from '@/api/training';

export type InsightType = 'positive' | 'warning' | 'neutral';

export interface Insight {
  type: InsightType;
  message: string;
}

/**
 * Generates rule-based insights from session data.
 * No AI — pure heuristics based on HR zones, pace, training type, etc.
 */
export function generateInsights(session: SessionDetail): Insight[] {
  const insights: Insight[] = [];
  const effectiveType = session.training_type?.effective;

  // ─── HR Zone Analysis ───
  if (session.hr_zones) {
    const zones = session.hr_zones;
    const totalSeconds = Object.values(zones).reduce((s, z) => s + z.seconds, 0);

    if (totalSeconds > 0) {
      const highZoneSeconds = getHighZoneSeconds(zones);
      const highZonePercent = (highZoneSeconds / totalSeconds) * 100;

      // Easy/Recovery run with too much time in high zones
      if (
        (effectiveType === 'easy' || effectiveType === 'recovery') &&
        highZonePercent > 30
      ) {
        insights.push({
          type: 'warning',
          message: `${Math.round(highZonePercent)}% der Zeit in hohen HF-Zonen — für einen ${effectiveType === 'easy' ? 'Easy Run' : 'Recovery Run'} zu intensiv.`,
        });
      }

      // Long run intensity check
      if (effectiveType === 'long_run' && highZonePercent > 40) {
        insights.push({
          type: 'warning',
          message: `${Math.round(highZonePercent)}% in hohen Zonen — Long Runs sollten überwiegend im aeroben Bereich stattfinden.`,
        });
      }

      // Good zone distribution for easy/recovery
      if (
        (effectiveType === 'easy' || effectiveType === 'recovery') &&
        highZonePercent <= 15
      ) {
        insights.push({
          type: 'positive',
          message: 'Gute Intensitätssteuerung — Großteil des Trainings im aeroben Bereich.',
        });
      }
    }
  }

  // ─── Pace Consistency (Laps) ───
  if (session.laps && session.laps.length >= 3 && effectiveType !== 'intervals') {
    const workingLaps = session.laps.filter(
      (l) => {
        const type = l.user_override || l.suggested_type;
        return type !== 'warmup' && type !== 'cooldown' && type !== 'pause';
      },
    );

    if (workingLaps.length >= 3) {
      const paces = workingLaps
        .map((l) => l.pace_min_per_km)
        .filter((p): p is number => p != null && p > 0);

      if (paces.length >= 3) {
        const avgPace = paces.reduce((a, b) => a + b, 0) / paces.length;
        const variance = paces.reduce((s, p) => s + Math.pow(p - avgPace, 2), 0) / paces.length;
        const cv = (Math.sqrt(variance) / avgPace) * 100;

        if (cv < 5) {
          insights.push({
            type: 'positive',
            message: 'Pace sehr konstant gehalten — gleichmäßige Belastung.',
          });
        } else if (cv > 15) {
          insights.push({
            type: 'neutral',
            message: 'Pace-Schwankungen zwischen den Laps — prüfe, ob das beabsichtigt war.',
          });
        }
      }
    }
  }

  // ─── Cadence Check (Running) ───
  if (session.workout_type === 'running' && session.cadence_avg) {
    if (session.cadence_avg < 160) {
      insights.push({
        type: 'warning',
        message: `Kadenz von ${session.cadence_avg} spm ist niedrig — ein Zielwert von 170+ kann die Laufökonomie verbessern.`,
      });
    } else if (session.cadence_avg >= 175) {
      insights.push({
        type: 'positive',
        message: `Gute Kadenz (${session.cadence_avg} spm) — effiziente Schrittfrequenz.`,
      });
    }
  }

  // ─── Duration Check ───
  if (session.duration_sec) {
    if (effectiveType === 'recovery' && session.duration_sec > 3600) {
      insights.push({
        type: 'neutral',
        message: 'Recovery Run über 60 Minuten — kürzere Einheiten sind oft effektiver für die Erholung.',
      });
    }
  }

  return insights;
}

function getHighZoneSeconds(zones: Record<string, HRZone>): number {
  let seconds = 0;
  for (const [key, zone] of Object.entries(zones)) {
    // Consider zones with index >= 3 as "high" (typically tempo/threshold and above)
    const zoneNum = parseInt(key.replace(/\D/g, ''), 10);
    if (zoneNum >= 3) {
      seconds += zone.seconds;
    }
  }
  return seconds;
}
