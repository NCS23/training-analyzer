import { describe, it, expect } from 'vitest';
import {
  haversineMeters,
  buildElevationProfile,
  smoothAltitude,
  getElevationSummary,
} from './gpsUtils';
import type { GPSPoint } from '@/api/training';

/* ------------------------------------------------------------------ */
/*  haversineMeters                                                    */
/* ------------------------------------------------------------------ */

describe('haversineMeters', () => {
  it('returns 0 for identical points', () => {
    expect(haversineMeters(52.52, 13.405, 52.52, 13.405)).toBe(0);
  });

  it('calculates known distance Berlin → Hamburg (~255 km)', () => {
    const dist = haversineMeters(52.52, 13.405, 53.5511, 9.9937);
    expect(dist).toBeGreaterThan(250_000);
    expect(dist).toBeLessThan(260_000);
  });

  it('calculates short distance (~100m)', () => {
    // ~100m offset at equator
    const dist = haversineMeters(0, 0, 0, 0.0009);
    expect(dist).toBeGreaterThan(90);
    expect(dist).toBeLessThan(110);
  });
});

/* ------------------------------------------------------------------ */
/*  buildElevationProfile                                              */
/* ------------------------------------------------------------------ */

describe('buildElevationProfile', () => {
  const points: GPSPoint[] = [
    { lat: 52.52, lng: 13.405, alt: 34, hr: 120, seconds: 0 },
    { lat: 52.521, lng: 13.405, alt: 36, hr: 125, seconds: 10 },
    { lat: 52.522, lng: 13.405, alt: 38, hr: 130, seconds: 20 },
  ];

  it('returns empty array for empty input', () => {
    expect(buildElevationProfile([])).toEqual([]);
  });

  it('builds correct number of data points', () => {
    const result = buildElevationProfile(points);
    expect(result).toHaveLength(3);
  });

  it('first point has distanceKm = 0', () => {
    const result = buildElevationProfile(points);
    expect(result[0].distanceKm).toBe(0);
  });

  it('cumulative distance increases', () => {
    const result = buildElevationProfile(points);
    expect(result[1].distanceKm).toBeGreaterThan(0);
    expect(result[2].distanceKm).toBeGreaterThan(result[1].distanceKm);
  });

  it('preserves altitude values', () => {
    const result = buildElevationProfile(points);
    expect(result[0].altitudeM).toBe(34);
    expect(result[1].altitudeM).toBe(36);
    expect(result[2].altitudeM).toBe(38);
  });

  it('preserves pointIndex for map sync', () => {
    const result = buildElevationProfile(points);
    expect(result[0].pointIndex).toBe(0);
    expect(result[1].pointIndex).toBe(1);
    expect(result[2].pointIndex).toBe(2);
  });

  it('skips points without altitude', () => {
    const mixed: GPSPoint[] = [
      { lat: 52.52, lng: 13.405, alt: 34, seconds: 0 },
      { lat: 52.521, lng: 13.405, seconds: 10 }, // no alt
      { lat: 52.522, lng: 13.405, alt: 38, seconds: 20 },
    ];
    const result = buildElevationProfile(mixed);
    expect(result).toHaveLength(2);
    expect(result[0].pointIndex).toBe(0);
    expect(result[1].pointIndex).toBe(2);
  });

  it('skips GPS glitches (>500m between consecutive points)', () => {
    const glitchy: GPSPoint[] = [
      { lat: 52.52, lng: 13.405, alt: 34, seconds: 0 },
      { lat: 53.52, lng: 13.405, alt: 36, seconds: 1 }, // ~111km jump
      { lat: 52.521, lng: 13.405, alt: 38, seconds: 2 },
    ];
    const result = buildElevationProfile(glitchy);
    // Distance should not include the glitchy jump
    expect(result[result.length - 1].distanceKm).toBeLessThan(1);
  });

  it('preserves hr data', () => {
    const result = buildElevationProfile(points);
    expect(result[0].hr).toBe(120);
    expect(result[1].hr).toBe(125);
  });
});

/* ------------------------------------------------------------------ */
/*  smoothAltitude                                                     */
/* ------------------------------------------------------------------ */

describe('smoothAltitude', () => {
  it('returns original data if fewer than windowSize points', () => {
    const data = [
      { distanceKm: 0, altitudeM: 100, pointIndex: 0, seconds: 0 },
      { distanceKm: 0.1, altitudeM: 200, pointIndex: 1, seconds: 10 },
    ];
    const result = smoothAltitude(data, 5);
    expect(result).toEqual(data);
  });

  it('smooths noisy altitude data', () => {
    const data = Array.from({ length: 10 }, (_, i) => ({
      distanceKm: i * 0.1,
      altitudeM: 100 + (i % 2 === 0 ? 10 : -10), // alternating ±10
      pointIndex: i,
      seconds: i * 10,
    }));
    const result = smoothAltitude(data, 3);

    // Smoothed values should be closer to 100 than the raw alternating values
    for (const d of result.slice(1, -1)) {
      expect(Math.abs(d.altitudeM - 100)).toBeLessThan(10);
    }
  });

  it('preserves non-altitude fields', () => {
    const data = [
      { distanceKm: 0, altitudeM: 100, pointIndex: 0, seconds: 0, hr: 120 },
      { distanceKm: 0.1, altitudeM: 110, pointIndex: 1, seconds: 10, hr: 125 },
      { distanceKm: 0.2, altitudeM: 105, pointIndex: 2, seconds: 20, hr: 130 },
      { distanceKm: 0.3, altitudeM: 115, pointIndex: 3, seconds: 30, hr: 135 },
      { distanceKm: 0.4, altitudeM: 108, pointIndex: 4, seconds: 40, hr: 140 },
      { distanceKm: 0.5, altitudeM: 112, pointIndex: 5, seconds: 50, hr: 145 },
    ];
    const result = smoothAltitude(data, 3);
    expect(result[2].pointIndex).toBe(2);
    expect(result[2].seconds).toBe(20);
    expect(result[2].hr).toBe(130);
  });
});

/* ------------------------------------------------------------------ */
/*  getElevationSummary                                                */
/* ------------------------------------------------------------------ */

describe('getElevationSummary', () => {
  it('returns null for empty data', () => {
    expect(getElevationSummary([])).toBeNull();
  });

  it('calculates min and max altitude', () => {
    const data = [
      { distanceKm: 0, altitudeM: 50, pointIndex: 0, seconds: 0 },
      { distanceKm: 1, altitudeM: 120, pointIndex: 1, seconds: 60 },
      { distanceKm: 2, altitudeM: 80, pointIndex: 2, seconds: 120 },
    ];
    const summary = getElevationSummary(data);
    expect(summary).not.toBeNull();
    expect(summary!.minAltitudeM).toBe(50);
    expect(summary!.maxAltitudeM).toBe(120);
  });
});
