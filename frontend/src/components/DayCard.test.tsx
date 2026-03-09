import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { DayCard } from './DayCard';
import type { RunDetails, WeeklyPlanEntry } from '@/api/weekly-plan';
import { createEmptySegment } from '@/api/segment';

/** Create a RunDetails with a default steady segment. */
function makeRunDetails(overrides: Partial<RunDetails> & { run_type: RunDetails['run_type'] }): RunDetails {
  const base: RunDetails = {
    run_type: overrides.run_type,
    target_duration_minutes: overrides.target_duration_minutes ?? null,
    target_pace_min: overrides.target_pace_min ?? null,
    target_pace_max: overrides.target_pace_max ?? null,
    target_hr_min: overrides.target_hr_min ?? null,
    target_hr_max: overrides.target_hr_max ?? null,
    intervals: overrides.intervals ?? null,
    segments: overrides.segments ?? [
      createEmptySegment(0, {
        segment_type: 'steady',
        target_duration_minutes: overrides.target_duration_minutes ?? null,
        target_pace_min: overrides.target_pace_min ?? null,
        target_pace_max: overrides.target_pace_max ?? null,
        target_hr_min: overrides.target_hr_min ?? null,
        target_hr_max: overrides.target_hr_max ?? null,
      }),
    ],
  };
  return base;
}

const baseEntry: WeeklyPlanEntry = {
  day_of_week: 0,
  sessions: [{ position: 0, training_type: 'running' }],
  is_rest_day: false,
  notes: null,
  plan_id: null,
  edited: false,
};

const noop = () => {};

const defaultProps = {
  weekStart: '2026-08-03',
  isToday: false,
  compliance: undefined,
  showCompliance: false,
  onUpdate: noop,
  onNavigateSession: vi.fn(),
};

describe('DayCard edited indicator', () => {
  it('renders pencil icon for generated + edited entry', () => {
    render(<DayCard entry={{ ...baseEntry, plan_id: 1, edited: true }} {...defaultProps} />);
    expect(screen.getByLabelText('Manuell bearbeitet')).toBeDefined();
  });

  it('does not render pencil icon for manual entry', () => {
    render(<DayCard entry={{ ...baseEntry, plan_id: null, edited: false }} {...defaultProps} />);
    expect(screen.queryByLabelText('Manuell bearbeitet')).toBeNull();
  });

  it('does not render pencil icon for generated + unedited entry', () => {
    render(<DayCard entry={{ ...baseEntry, plan_id: 1, edited: false }} {...defaultProps} />);
    expect(screen.queryByLabelText('Manuell bearbeitet')).toBeNull();
  });
});

describe('DayCard compact card', () => {
  it('renders session type on card', () => {
    const runEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: makeRunDetails({ run_type: 'easy', target_duration_minutes: 45 }),
        },
      ],
    };
    render(<DayCard entry={runEntry} {...defaultProps} />);
    expect(screen.getByText('Lockerer Lauf')).toBeDefined();
    expect(screen.getByText(/45′/)).toBeDefined();
  });

  it('renders multiple sessions on card', () => {
    const multiEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: makeRunDetails({ run_type: 'easy', target_duration_minutes: 45 }),
        },
        { position: 1, training_type: 'strength' },
      ],
    };
    render(<DayCard entry={multiEntry} {...defaultProps} />);
    expect(screen.getByText('Lockerer Lauf')).toBeDefined();
    expect(screen.getByText('Kraft')).toBeDefined();
  });

  it('renders rest day', () => {
    const restEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [],
      is_rest_day: true,
    };
    render(<DayCard entry={restEntry} {...defaultProps} />);
    expect(screen.getByText('Ruhe')).toBeDefined();
  });

  it('renders dash for empty day', () => {
    const emptyEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [],
      is_rest_day: false,
    };
    render(<DayCard entry={emptyEntry} {...defaultProps} />);
    expect(screen.getByText('—')).toBeDefined();
  });
});

describe('DayCard per-session detail dialog', () => {
  it('opens session dialog when session row is clicked', async () => {
    const user = userEvent.setup();
    render(<DayCard entry={baseEntry} {...defaultProps} />);
    await user.click(screen.getByLabelText('Laufen Details'));
    // Dialog shows session label
    expect(screen.getByText(/Session 1/)).toBeDefined();
  });

  it('shows full run details in session dialog', async () => {
    const user = userEvent.setup();
    const runEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: makeRunDetails({
            run_type: 'tempo',
            target_duration_minutes: 40,
            target_pace_min: '4:30',
            target_pace_max: '5:00',
            target_hr_min: 160,
            target_hr_max: 175,
          }),
        },
      ],
    };
    render(<DayCard entry={runEntry} {...defaultProps} />);
    await user.click(screen.getByLabelText('Tempolauf Details'));
    // "Tempolauf" appears on card row and in dialog title
    expect(screen.getAllByText(/Tempolauf/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('40 min')).toBeDefined();
    expect(screen.getAllByText(/4:30/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/160 – 175 bpm/)).toBeDefined();
  });

  it('shows segments in session dialog', async () => {
    const user = userEvent.setup();
    const segEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: makeRunDetails({
            run_type: 'intervals',
            segments: [
              createEmptySegment(0, { segment_type: 'warmup', target_duration_minutes: 10 }),
              createEmptySegment(1, { segment_type: 'work', target_duration_minutes: 3 }),
              createEmptySegment(2, { segment_type: 'recovery_jog', target_duration_minutes: 2 }),
              createEmptySegment(3, { segment_type: 'cooldown', target_duration_minutes: 5 }),
            ],
          }),
        },
      ],
    };
    render(<DayCard entry={segEntry} {...defaultProps} />);
    await user.click(screen.getByLabelText('Intervalle Details'));
    expect(screen.getByText('Warm-up')).toBeDefined();
    expect(screen.getByText('Arbeit')).toBeDefined();
    expect(screen.getByText('Trab')).toBeDefined();
    expect(screen.getByText('Cool-down')).toBeDefined();
  });

  it('shows kebab menu with edit option in session dialog', async () => {
    const user = userEvent.setup();
    render(<DayCard entry={baseEntry} {...defaultProps} />);
    await user.click(screen.getByLabelText('Laufen Details'));
    await user.click(screen.getByLabelText('Session Optionen'));
    expect(screen.getByText('Bearbeiten')).toBeDefined();
  });

  it('switches to edit mode and shows editor fields', async () => {
    const user = userEvent.setup();
    render(<DayCard entry={baseEntry} {...defaultProps} />);
    await user.click(screen.getByLabelText('Laufen Details'));
    await user.click(screen.getByLabelText('Session Optionen'));
    await user.click(screen.getByText('Bearbeiten'));
    expect(screen.getByText('Speichern')).toBeDefined();
    expect(screen.getByText('Abbrechen')).toBeDefined();
    expect(screen.getByLabelText('Session Notizen')).toBeDefined();
  });

  it('opens different dialogs for different sessions', async () => {
    const user = userEvent.setup();
    const multiEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: makeRunDetails({ run_type: 'easy', target_duration_minutes: 45 }),
        },
        { position: 1, training_type: 'strength' },
      ],
    };
    render(<DayCard entry={multiEntry} {...defaultProps} />);

    // Click first session
    await user.click(screen.getByLabelText('Lockerer Lauf Details'));
    expect(screen.getByText(/Session 1/)).toBeDefined();
    // "Lockerer Lauf" appears on card row and in dialog title
    expect(screen.getAllByText(/Lockerer Lauf/).length).toBeGreaterThanOrEqual(1);
  });

  it('shows strength session in dialog', async () => {
    const user = userEvent.setup();
    const strengthEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [{ position: 0, training_type: 'strength' }],
    };
    render(<DayCard entry={strengthEntry} {...defaultProps} />);
    await user.click(screen.getByLabelText('Kraft Details'));
    expect(screen.getByText(/Session 1/)).toBeDefined();
    // "Kraft" appears in dialog title and read-only body
    expect(screen.getAllByText('Kraft').length).toBeGreaterThanOrEqual(1);
  });
});
