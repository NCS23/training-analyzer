import { describe, expect, it } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { SessionComparisonSection } from './SessionComparisonSection';
import type { ComparisonResponse, MatchedSegment, SegmentDelta } from '@/api/training';
import { createEmptySegment } from '@/api/segment';

function makeSegment(overrides: Partial<ReturnType<typeof createEmptySegment>> = {}) {
  return createEmptySegment(0, { segment_type: 'steady', ...overrides });
}

function makeComparison(overrides: Partial<ComparisonResponse> = {}): ComparisonResponse {
  return {
    planned_entry_id: 1,
    planned_run_type: null,
    segments: [],
    has_mismatch: false,
    planned_count: 0,
    actual_count: 0,
    ...overrides,
  };
}

const nullDelta: SegmentDelta = {
  pace_delta_seconds: null,
  pace_delta_formatted: null,
  hr_avg_delta: null,
  duration_delta_seconds: null,
  distance_delta_km: null,
};

function makeMatched(overrides: Partial<MatchedSegment> = {}): MatchedSegment {
  return {
    position: 0,
    segment_type: 'steady',
    match_quality: 'matched',
    planned: makeSegment({ target_pace_min: '5:00', target_pace_max: '5:30' }),
    actual: makeSegment({ actual_pace_formatted: '5:15' }),
    delta: { ...nullDelta, pace_delta_seconds: 0, pace_delta_formatted: '+0:00' },
    ...overrides,
  };
}

function makeDelta(overrides: Partial<SegmentDelta> = {}): SegmentDelta {
  return { ...nullDelta, ...overrides };
}

describe('SessionComparisonSection — layout', () => {
  it('renders heading and table', () => {
    render(<SessionComparisonSection comparison={makeComparison({ segments: [makeMatched()] })} />);
    expect(screen.getByText('Soll/Ist-Vergleich')).toBeDefined();
    expect(screen.getByRole('table')).toBeDefined();
  });

  it('renders run type badge when present', () => {
    render(
      <SessionComparisonSection
        comparison={makeComparison({ planned_run_type: 'easy', segments: [makeMatched()] })}
      />,
    );
    expect(screen.getByText('easy')).toBeDefined();
  });

  it('does not render run type badge when null', () => {
    render(<SessionComparisonSection comparison={makeComparison({ segments: [makeMatched()] })} />);
    expect(screen.queryByText('easy')).toBeNull();
  });

  it('shows mismatch alert when has_mismatch is true', () => {
    const comparison = makeComparison({
      has_mismatch: true,
      planned_count: 3,
      actual_count: 5,
      segments: [makeMatched()],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getByText(/Segment-Anzahl weicht ab/)).toBeDefined();
    expect(screen.getByText(/3 geplant/)).toBeDefined();
  });

  it('hides mismatch alert when has_mismatch is false', () => {
    render(<SessionComparisonSection comparison={makeComparison({ segments: [makeMatched()] })} />);
    expect(screen.queryByText(/Segment-Anzahl weicht ab/)).toBeNull();
  });
});

describe('SessionComparisonSection — rows + deltas', () => {
  it('renders correct position numbers', () => {
    const comparison = makeComparison({
      segments: [makeMatched({ position: 0 }), makeMatched({ position: 1 })],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getByText('1')).toBeDefined();
    expect(screen.getByText('2')).toBeDefined();
  });

  it('shows pace delta text', () => {
    const comparison = makeComparison({
      segments: [
        makeMatched({
          delta: makeDelta({ pace_delta_seconds: 12, pace_delta_formatted: '+0:12' }),
        }),
      ],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getByText('+0:12')).toBeDefined();
  });

  it('shows dash for missing delta values', () => {
    const comparison = makeComparison({
      segments: [
        makeMatched({
          planned: null,
          actual: null,
          match_quality: 'unmatched_planned',
          delta: null,
        }),
      ],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getAllByText('–').length).toBeGreaterThan(0);
  });

  it('renders duration delta formatted', () => {
    const comparison = makeComparison({
      segments: [makeMatched({ delta: makeDelta({ duration_delta_seconds: 65 }) })],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getByText('+1:05')).toBeDefined();
  });

  it('applies error color for positive (slower) pace delta', () => {
    const comparison = makeComparison({
      segments: [
        makeMatched({
          delta: makeDelta({ pace_delta_seconds: 12, pace_delta_formatted: '+0:12' }),
        }),
      ],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getByText('+0:12').closest('td')?.className).toContain('color-text-error');
  });

  it('applies success color for negative (faster) pace delta', () => {
    const comparison = makeComparison({
      segments: [
        makeMatched({
          delta: makeDelta({ pace_delta_seconds: -5, pace_delta_formatted: '-0:05' }),
        }),
      ],
    });
    render(<SessionComparisonSection comparison={comparison} />);
    expect(screen.getByText('-0:05').closest('td')?.className).toContain('color-text-success');
  });
});
