import { describe, it, expect } from 'vitest';
import { getPresetSegments, hasSegmentData } from './segmentPresets';
import { createEmptySegment } from '../api/segment';
import { SESSION_TYPES } from '../constants/taxonomy';

describe('getPresetSegments', () => {
  it('returns a single steady segment for easy runs', () => {
    const segs = getPresetSegments('easy');
    expect(segs).toHaveLength(1);
    expect(segs[0].segment_type).toBe('steady');
    expect(segs[0].target_duration_minutes).toBe(40);
  });

  it('returns warm-up + steady + cool-down for tempo', () => {
    const segs = getPresetSegments('tempo');
    expect(segs).toHaveLength(3);
    expect(segs.map((s) => s.segment_type)).toEqual(['warmup', 'steady', 'cooldown']);
    expect(segs[0].target_duration_minutes).toBe(10);
    expect(segs[1].target_duration_minutes).toBe(20);
    expect(segs[2].target_duration_minutes).toBe(10);
  });

  it('returns work + recovery with repeats for intervals', () => {
    const segs = getPresetSegments('intervals');
    expect(segs).toHaveLength(4);
    expect(segs.map((s) => s.segment_type)).toEqual(['warmup', 'work', 'recovery_jog', 'cooldown']);
    expect(segs[1].repeats).toBe(4);
    expect(segs[2].repeats).toBe(4);
  });

  it('returns work + recovery with repeats for repetitions', () => {
    const segs = getPresetSegments('repetitions');
    const work = segs.find((s) => s.segment_type === 'work');
    const recovery = segs.find((s) => s.segment_type === 'recovery_jog');
    expect(work?.repeats).toBe(6);
    expect(work?.target_duration_minutes).toBe(1);
    expect(recovery?.repeats).toBe(6);
    expect(recovery?.target_duration_minutes).toBe(3);
  });

  it('returns 4 segments for progression', () => {
    const segs = getPresetSegments('progression');
    expect(segs).toHaveLength(4);
    expect(segs.map((s) => s.segment_type)).toEqual(['warmup', 'steady', 'steady', 'cooldown']);
  });

  it('has correct sequential positions', () => {
    for (const type of SESSION_TYPES) {
      const segs = getPresetSegments(type);
      segs.forEach((seg, i) => {
        expect(seg.position).toBe(i);
      });
    }
  });

  it('covers all session types', () => {
    for (const type of SESSION_TYPES) {
      const segs = getPresetSegments(type);
      expect(segs.length).toBeGreaterThanOrEqual(1);
    }
  });

  it('sets all Ist fields to null', () => {
    const segs = getPresetSegments('intervals');
    for (const seg of segs) {
      expect(seg.actual_duration_seconds).toBeNull();
      expect(seg.actual_distance_km).toBeNull();
      expect(seg.actual_pace_formatted).toBeNull();
      expect(seg.actual_hr_avg).toBeNull();
    }
  });
});

describe('hasSegmentData', () => {
  it('returns false for null/undefined/empty', () => {
    expect(hasSegmentData(null)).toBe(false);
    expect(hasSegmentData(undefined)).toBe(false);
    expect(hasSegmentData([])).toBe(false);
  });

  it('returns false for a single empty default segment', () => {
    expect(hasSegmentData([createEmptySegment(0, { segment_type: 'steady' })])).toBe(false);
    expect(hasSegmentData([createEmptySegment(0, { segment_type: 'work' })])).toBe(false);
  });

  it('returns true for multiple segments', () => {
    expect(
      hasSegmentData([
        createEmptySegment(0, { segment_type: 'steady' }),
        createEmptySegment(1, { segment_type: 'steady' }),
      ]),
    ).toBe(true);
  });

  it('returns true for non-default segment type', () => {
    expect(hasSegmentData([createEmptySegment(0, { segment_type: 'warmup' })])).toBe(true);
  });

  it('returns true when duration is set', () => {
    expect(
      hasSegmentData([
        createEmptySegment(0, { segment_type: 'steady', target_duration_minutes: 30 }),
      ]),
    ).toBe(true);
  });

  it('returns true when pace is set', () => {
    expect(
      hasSegmentData([createEmptySegment(0, { segment_type: 'steady', target_pace_min: '5:00' })]),
    ).toBe(true);
  });

  it('returns true when HR is set', () => {
    expect(
      hasSegmentData([createEmptySegment(0, { segment_type: 'work', target_hr_min: 140 })]),
    ).toBe(true);
  });

  it('returns true when notes are set', () => {
    expect(
      hasSegmentData([
        createEmptySegment(0, { segment_type: 'work', notes: 'lockerer Dauerlauf' }),
      ]),
    ).toBe(true);
  });

  it('returns true when repeats > 1', () => {
    expect(hasSegmentData([createEmptySegment(0, { segment_type: 'work', repeats: 4 })])).toBe(
      true,
    );
  });

  it('ignores empty string notes', () => {
    expect(hasSegmentData([createEmptySegment(0, { segment_type: 'steady', notes: '' })])).toBe(
      false,
    );
  });
});
