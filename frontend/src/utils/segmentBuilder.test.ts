import { describe, it, expect } from 'vitest';
import { buildPaceSegments, buildHRSegments } from './segmentBuilder';
import { computeHRZoneBoundaries } from './colorScale';
import type { GPSPoint } from '@/api/training';

/* ------------------------------------------------------------------ */
/*  Test data                                                          */
/* ------------------------------------------------------------------ */

/** Generate a straight-line run of N points with constant speed. */
function makeRunPoints(count: number, speedMs = 3.0): GPSPoint[] {
  return Array.from({ length: count }, (_, i) => ({
    lat: 52.52 + i * 0.001, // ~111m apart
    lng: 13.405,
    alt: 50,
    hr: 140 + (i % 10),
    speed: speedMs,
    seconds: i * 37, // ~37s per ~111m at 3 m/s
  }));
}

const runPoints = makeRunPoints(30);

/** Points without speed field — should use haversine fallback. */
const pointsNoSpeed: GPSPoint[] = Array.from({ length: 30 }, (_, i) => ({
  lat: 52.52 + i * 0.001,
  lng: 13.405,
  hr: 130,
  seconds: i * 37,
}));

/* ------------------------------------------------------------------ */
/*  buildPaceSegments                                                  */
/* ------------------------------------------------------------------ */

describe('buildPaceSegments', () => {
  it('returns empty for fewer than 2 points', () => {
    expect(buildPaceSegments([])).toEqual([]);
    expect(buildPaceSegments([runPoints[0]])).toEqual([]);
  });

  it('builds segments from speed field', () => {
    const segments = buildPaceSegments(runPoints, 100);
    expect(segments.length).toBeGreaterThan(0);

    for (const seg of segments) {
      expect(seg.positions.length).toBeGreaterThanOrEqual(2);
      expect(seg.color).toMatch(/^rgb\(/);
      expect(seg.label).toMatch(/\/km$/);
      expect(seg.value).toBeGreaterThan(0);
    }
  });

  it('builds segments from haversine fallback', () => {
    const segments = buildPaceSegments(pointsNoSpeed, 100);
    expect(segments.length).toBeGreaterThan(0);
  });

  it('segment positions are consecutive lat/lng tuples', () => {
    const segments = buildPaceSegments(runPoints, 200);
    for (const seg of segments) {
      for (const pos of seg.positions) {
        expect(pos).toHaveLength(2);
        expect(pos[0]).toBeGreaterThan(0); // lat
      }
    }
  });

  it('respects segmentLengthM parameter', () => {
    const shortSegs = buildPaceSegments(runPoints, 50);
    const longSegs = buildPaceSegments(runPoints, 500);
    // Shorter segment length → more segments
    expect(shortSegs.length).toBeGreaterThanOrEqual(longSegs.length);
  });
});

/* ------------------------------------------------------------------ */
/*  buildHRSegments                                                    */
/* ------------------------------------------------------------------ */

describe('buildHRSegments', () => {
  const zones = computeHRZoneBoundaries(50, 190);

  it('returns empty for fewer than 2 points', () => {
    expect(buildHRSegments([], zones)).toEqual([]);
  });

  it('returns empty for no zones', () => {
    expect(buildHRSegments(runPoints, [])).toEqual([]);
  });

  it('builds segments with HR zone colors', () => {
    const segments = buildHRSegments(runPoints, zones, 100);
    expect(segments.length).toBeGreaterThan(0);

    for (const seg of segments) {
      expect(seg.positions.length).toBeGreaterThanOrEqual(2);
      expect(seg.color).toMatch(/^#[0-9a-f]{6}$/);
      expect(seg.label).toMatch(/bpm$/);
      expect(seg.value).toBeGreaterThan(0);
    }
  });

  it('assigns correct zone color for known HR', () => {
    // All points at 140 bpm → Zone 2 (134-148 bpm)
    const constHrPoints: GPSPoint[] = Array.from({ length: 20 }, (_, i) => ({
      lat: 52.52 + i * 0.001,
      lng: 13.405,
      hr: 140,
      seconds: i * 37,
    }));

    const segments = buildHRSegments(constHrPoints, zones, 100);
    expect(segments.length).toBeGreaterThan(0);
    // Zone 2 color is #10b981
    for (const seg of segments) {
      expect(seg.color).toBe('#10b981');
    }
  });
});
