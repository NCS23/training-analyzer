import type { SessionDetail, HRZone } from '@/api/training';

export type InsightType = 'positive' | 'warning' | 'neutral';

export interface Insight {
  type: InsightType;
  message: string;
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

/** Check if the session uses 5-zone Karvonen (vs 3-zone fallback). */
function isKarvonen(zones: Record<string, HRZone>): boolean {
  return Object.values(zones).some((z) => z.zone != null && z.zone >= 4);
}

/** Get the upper BPM of a specific Karvonen zone (by zone number). */
function zoneUpperBpm(zones: Record<string, HRZone>, zoneNum: number): number | null {
  for (const z of Object.values(zones)) {
    if (z.zone === zoneNum && z.label) {
      const match = z.label.match(/(\d+)\s*-\s*(\d+)/);
      if (match) return parseInt(match[2], 10);
    }
  }
  return null;
}

/** Sum seconds in zones >= minZone. */
function secondsInZonesAbove(zones: Record<string, HRZone>, minZone: number): number {
  let seconds = 0;
  for (const [key, zone] of Object.entries(zones)) {
    const num = zone.zone ?? parseInt(key.replace(/\D/g, ''), 10);
    if (num >= minZone) seconds += zone.seconds;
  }
  return seconds;
}

const EXCLUDED_LAP_TYPES = new Set(['warmup', 'cooldown', 'rest']);

/** Weighted average cadence from working laps only. */
function workingCadence(session: SessionDetail): number | null {
  if (!session.laps || session.laps.length === 0) return null;

  let totalWeighted = 0;
  let totalDuration = 0;

  for (const lap of session.laps) {
    const type = lap.user_override || lap.suggested_type;
    if (type && EXCLUDED_LAP_TYPES.has(type)) continue;
    if (!lap.avg_cadence_spm || lap.duration_seconds <= 0) continue;

    totalWeighted += lap.avg_cadence_spm * lap.duration_seconds;
    totalDuration += lap.duration_seconds;
  }

  return totalDuration > 0 ? Math.round(totalWeighted / totalDuration) : null;
}

/** Sum seconds in zones <= maxZone. */
function secondsInZonesBelow(zones: Record<string, HRZone>, maxZone: number): number {
  let seconds = 0;
  for (const [key, zone] of Object.entries(zones)) {
    const num = zone.zone ?? parseInt(key.replace(/\D/g, ''), 10);
    if (num <= maxZone) seconds += zone.seconds;
  }
  return seconds;
}

/* ------------------------------------------------------------------ */
/*  Insights                                                           */
/* ------------------------------------------------------------------ */

/**
 * Generates rule-based insights with actionable advice.
 * Uses the user's personal Karvonen zones when available.
 */
// eslint-disable-next-line complexity -- TODO: E16 Refactoring
export function generateInsights(session: SessionDetail): Insight[] {
  const insights: Insight[] = [];
  const effectiveType = session.training_type?.effective;

  // ─── HR Zone Analysis ───
  if (session.hr_zones) {
    const zones = session.hr_zones;
    const totalSeconds = Object.values(zones).reduce((s, z) => s + z.seconds, 0);
    const karvonen = isKarvonen(zones);

    if (totalSeconds > 0) {
      // "High" = Tempo+ (Zone 3+) for Karvonen, Zone 3 for fallback
      const highSeconds = secondsInZonesAbove(zones, 3);
      const highPercent = (highSeconds / totalSeconds) * 100;

      // "Low" = Recovery + Base (Zone 1-2)
      const lowSeconds = secondsInZonesBelow(zones, 2);
      const lowPercent = (lowSeconds / totalSeconds) * 100;

      // BPM boundary: upper limit of Zone 2 (Base) = where it gets intense
      const baseUpperBpm = zoneUpperBpm(zones, 2);
      const bpmHint = baseUpperBpm ? ` (bei dir unter ${baseUpperBpm} bpm)` : '';

      // Easy/Recovery: too much time in high zones
      if ((effectiveType === 'easy' || effectiveType === 'recovery') && highPercent > 30) {
        const label = effectiveType === 'easy' ? 'Easy Run' : 'Recovery Run';
        const zoneNames = karvonen ? 'Tempo, Threshold oder VO2max' : 'Tempo';
        insights.push({
          type: 'warning',
          message: `${Math.round(highPercent)}% der Zeit in ${zoneNames}-Zonen — für einen ${label} zu intensiv. Tipp: Halte dich in den Recovery- und Base-Zonen${bpmHint}. Bewusst langsamer starten und das Tempo an der Herzfrequenz orientieren, nicht am Gefühl.`,
        });
      }

      // Long run: too much time in high zones
      if (effectiveType === 'long_run' && highPercent > 40) {
        const zoneNames = karvonen ? 'Tempo/Threshold/VO2max' : 'hohen';
        insights.push({
          type: 'warning',
          message: `${Math.round(highPercent)}% in ${zoneNames}-Zonen — Long Runs sollten überwiegend in Recovery und Base stattfinden${bpmHint}. An Steigungen lieber das Tempo reduzieren statt die HF hochzutreiben.`,
        });
      }

      // Good zone distribution for easy/recovery
      if ((effectiveType === 'easy' || effectiveType === 'recovery') && lowPercent >= 85) {
        insights.push({
          type: 'positive',
          message: `${Math.round(lowPercent)}% in Recovery- und Base-Zonen — genau so baut man Grundlagenausdauer auf.`,
        });
      }
    }
  }

  // ─── Pace Consistency (Laps) ───
  if (session.laps && session.laps.length >= 3 && effectiveType !== 'intervals') {
    const workingLaps = session.laps.filter((l) => {
      const type = l.user_override || l.suggested_type;
      return type !== 'warmup' && type !== 'cooldown' && type !== 'pause';
    });

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
            message:
              'Pace sehr konstant gehalten — gleichmäßige Belastung ist ein Zeichen guter Tempokontrolle.',
          });
        } else if (cv > 15) {
          insights.push({
            type: 'neutral',
            message:
              'Deutliche Pace-Schwankungen zwischen den Laps. Falls nicht beabsichtigt (z.B. durch Gelände): Versuche den ersten Kilometer bewusst ruhig anzugehen — das hilft, das Tempo über die gesamte Distanz stabiler zu halten.',
          });
        }
      }
    }
  }

  // ─── Cadence Check (Running, Working Laps only) ───
  if (session.workout_type === 'running') {
    const cadenceFromWorking = workingCadence(session);
    const cadence = cadenceFromWorking ?? session.cadence_avg;

    if (cadence) {
      if (cadence < 160) {
        insights.push({
          type: 'warning',
          message: `Kadenz von ${cadence} spm im Arbeitsbereich ist niedrig. Eine höhere Schrittfrequenz (Ziel: 170–180 spm) reduziert die Belastung auf Gelenke und verbessert die Laufökonomie. Tipp: Kürzere, schnellere Schritte statt größerer — ein Metronom oder Musik mit passender BPM kann helfen.`,
        });
      } else if (cadence >= 175) {
        insights.push({
          type: 'positive',
          message: `Gute Kadenz (${cadence} spm) im Arbeitsbereich — effiziente Schrittfrequenz, die Gelenke und Sehnen schont.`,
        });
      }
    }
  }

  // ─── Duration Check ───
  if (session.duration_sec) {
    if (effectiveType === 'recovery' && session.duration_sec > 3600) {
      insights.push({
        type: 'neutral',
        message:
          'Recovery Run über 60 Minuten. Für die Regeneration reichen oft 20–40 Minuten — der Körper profitiert mehr von der Kürze und niedrigen Intensität als von der Dauer.',
      });
    }
  }

  return insights;
}
