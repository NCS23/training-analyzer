import { describe, it, expect } from 'vitest';
import { paceColor, hrZoneColor, computeHRZoneBoundaries } from './colorScale';
import type { HRZoneBoundary } from './colorScale';

describe('paceColor', () => {
  it('returns green-ish for t=0 (fastest)', () => {
    const color = paceColor(0);
    // Should be rgb(0,220,30) — green
    expect(color).toBe('rgb(0,220,30)');
  });

  it('returns red-ish for t=1 (slowest)', () => {
    const color = paceColor(1);
    // Should be rgb(255,0,30) — red
    expect(color).toBe('rgb(255,0,30)');
  });

  it('returns yellow-ish for t=0.5 (middle)', () => {
    const color = paceColor(0.5);
    // Should be rgb(255,220,30) — yellow
    expect(color).toBe('rgb(255,220,30)');
  });

  it('clamps values below 0', () => {
    expect(paceColor(-0.5)).toBe(paceColor(0));
  });

  it('clamps values above 1', () => {
    expect(paceColor(1.5)).toBe(paceColor(1));
  });
});

describe('computeHRZoneBoundaries', () => {
  const zones = computeHRZoneBoundaries(50, 190);

  it('returns 5 zones', () => {
    expect(zones).toHaveLength(5);
  });

  it('computes Karvonen boundaries correctly', () => {
    // Zone 1: 50 + (190-50)*0.5 = 120 to 50 + 140*0.6 = 134
    expect(zones[0].lowerBpm).toBe(120);
    expect(zones[0].upperBpm).toBe(134);
    expect(zones[0].zone).toBe(1);
    expect(zones[0].name).toBe('Recovery');
  });

  it('has correct zone 5 upper bound', () => {
    // Zone 5: 50 + 140*0.9 = 176 to 50 + 140*1.0 = 190
    expect(zones[4].lowerBpm).toBe(176);
    expect(zones[4].upperBpm).toBe(190);
  });

  it('each zone has a color', () => {
    for (const z of zones) {
      expect(z.color).toMatch(/^#[0-9a-f]{6}$/);
    }
  });
});

describe('hrZoneColor', () => {
  const zones: HRZoneBoundary[] = computeHRZoneBoundaries(50, 190);

  it('returns zone 1 color for HR below zone 1', () => {
    expect(hrZoneColor(100, zones)).toBe(zones[0].color);
  });

  it('returns zone 1 color for HR in zone 1 range', () => {
    expect(hrZoneColor(125, zones)).toBe(zones[0].color);
  });

  it('returns zone 3 color for HR in zone 3 range', () => {
    // Zone 3: 148-162
    expect(hrZoneColor(155, zones)).toBe(zones[2].color);
  });

  it('returns zone 5 color for HR above zone 5', () => {
    expect(hrZoneColor(200, zones)).toBe(zones[4].color);
  });
});
