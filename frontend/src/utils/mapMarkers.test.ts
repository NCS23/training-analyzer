import { describe, it, expect } from 'vitest';
import {
  buildKmPopupHtml,
  buildLapPopupHtml,
  LAP_TYPE_COLORS,
  LAP_TYPE_DASHED,
  LAP_TYPE_LABELS,
} from './mapMarkers';
import type { KmMarkerData, LapMarkerData } from './mapMarkers';

/* ------------------------------------------------------------------ */
/*  buildKmPopupHtml                                                   */
/* ------------------------------------------------------------------ */

describe('buildKmPopupHtml', () => {
  const fullKm: KmMarkerData = {
    km_number: 3,
    lat: 52.52,
    lng: 13.405,
    pace_formatted: '4:42',
    pace_corrected_formatted: '4:35',
    avg_hr_bpm: 152,
    duration_formatted: '4:42',
    elevation_gain_m: 12,
    elevation_loss_m: 3,
    is_partial: false,
    distance_km: 1.0,
  };

  it('includes km number in title', () => {
    const html = buildKmPopupHtml(fullKm);
    expect(html).toContain('Km 3');
  });

  it('includes pace, HR, duration', () => {
    const html = buildKmPopupHtml(fullKm);
    expect(html).toContain('4:42 /km');
    expect(html).toContain('152 bpm');
    expect(html).toContain('Dauer: 4:42');
  });

  it('includes corrected pace (GAP)', () => {
    const html = buildKmPopupHtml(fullKm);
    expect(html).toContain('GAP: 4:35 /km');
  });

  it('includes elevation gain and loss', () => {
    const html = buildKmPopupHtml(fullKm);
    expect(html).toContain('↑12m');
    expect(html).toContain('↓3m');
  });

  it('shows partial km distance for partial splits', () => {
    const partial: KmMarkerData = { ...fullKm, is_partial: true, distance_km: 0.73 };
    const html = buildKmPopupHtml(partial);
    expect(html).toContain('0.73 km');
    expect(html).not.toContain('Km 3');
  });

  it('omits missing optional fields', () => {
    const minimal: KmMarkerData = {
      ...fullKm,
      pace_formatted: null,
      pace_corrected_formatted: null,
      avg_hr_bpm: null,
      elevation_gain_m: null,
      elevation_loss_m: null,
    };
    const html = buildKmPopupHtml(minimal);
    expect(html).toContain('Km 3');
    expect(html).toContain('Dauer:');
    expect(html).not.toContain('/km');
    expect(html).not.toContain('bpm');
    expect(html).not.toContain('GAP');
  });
});

/* ------------------------------------------------------------------ */
/*  buildLapPopupHtml                                                  */
/* ------------------------------------------------------------------ */

describe('buildLapPopupHtml', () => {
  const lap: LapMarkerData = {
    lap_number: 2,
    lat: 52.52,
    lng: 13.405,
    type: 'interval',
    pace_formatted: '3:55',
    duration_formatted: '4:00',
    avg_hr_bpm: 172,
    distance_km: 1.0,
  };

  it('includes lap number and type label', () => {
    const html = buildLapPopupHtml(lap);
    expect(html).toContain('Lap 2');
    expect(html).toContain('Intervall');
  });

  it('includes pace, HR, duration, distance', () => {
    const html = buildLapPopupHtml(lap);
    expect(html).toContain('3:55 /km');
    expect(html).toContain('172 bpm');
    expect(html).toContain('Dauer: 4:00');
    expect(html).toContain('1 km');
  });

  it('omits missing optional fields', () => {
    const minimal: LapMarkerData = {
      ...lap,
      pace_formatted: null,
      avg_hr_bpm: null,
      distance_km: null,
    };
    const html = buildLapPopupHtml(minimal);
    expect(html).toContain('Lap 2');
    expect(html).not.toContain('/km');
    expect(html).not.toContain('bpm');
    expect(html).not.toContain('Distanz');
  });
});

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

describe('LAP_TYPE_COLORS', () => {
  it('has colors for common types', () => {
    expect(LAP_TYPE_COLORS.interval).toBe('#4f46e5');
    expect(LAP_TYPE_COLORS.warmup).toBe('#94a3b8');
    expect(LAP_TYPE_COLORS.working).toBe('#0ea5e9');
  });
});

describe('LAP_TYPE_DASHED', () => {
  it('warmup and cooldown are dashed', () => {
    expect(LAP_TYPE_DASHED.has('warmup')).toBe(true);
    expect(LAP_TYPE_DASHED.has('cooldown')).toBe(true);
  });

  it('interval is not dashed', () => {
    expect(LAP_TYPE_DASHED.has('interval')).toBe(false);
  });
});

describe('LAP_TYPE_LABELS', () => {
  it('has German labels', () => {
    expect(LAP_TYPE_LABELS.interval).toBe('Intervall');
    expect(LAP_TYPE_LABELS.pause).toBe('Pause');
  });
});
