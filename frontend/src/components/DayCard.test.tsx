import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { DayCard } from './DayCard';
import type { WeeklyPlanEntry } from '@/api/weekly-plan';

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
  isExpanded: false,
  compliance: undefined,
  showCompliance: false,
  onToggleExpand: noop,
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

describe('DayCard multi-session header', () => {
  it('renders multiple session icons in collapsed header', () => {
    const multiEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: {
            run_type: 'easy',
            target_duration_minutes: 45,
            target_pace_min: null,
            target_pace_max: null,
            target_hr_min: null,
            target_hr_max: null,
            intervals: null,
          },
        },
        { position: 1, training_type: 'strength' },
      ],
    };
    render(<DayCard entry={multiEntry} {...defaultProps} />);
    // Both session labels should be visible
    expect(screen.getByText('Easy')).toBeDefined();
    expect(screen.getByText('Kraft')).toBeDefined();
  });

  it('renders single session as before', () => {
    render(<DayCard entry={baseEntry} {...defaultProps} />);
    expect(screen.getByText('Laufen')).toBeDefined();
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

describe('DayCard expanded view', () => {
  it('renders edit button in expanded state', () => {
    render(<DayCard entry={baseEntry} {...defaultProps} isExpanded={true} />);
    expect(screen.getByLabelText('Training bearbeiten')).toBeDefined();
  });

  it('renders read-only session summary in expanded state', () => {
    const runEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: {
            run_type: 'tempo',
            target_duration_minutes: 40,
            target_pace_min: '4:30',
            target_pace_max: '5:00',
            target_hr_min: 160,
            target_hr_max: 175,
            intervals: null,
          },
        },
      ],
    };
    render(<DayCard entry={runEntry} {...defaultProps} isExpanded={true} />);
    // Expanded summary shows full run type label
    expect(screen.getByText('Tempolauf')).toBeDefined();
    // Details appear in both collapsed header and expanded summary
    expect(screen.getAllByText('40 min').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/4:30/).length).toBeGreaterThanOrEqual(1);
    // HR only in expanded summary
    expect(screen.getByText(/160–175 bpm/)).toBeDefined();
  });

  it('shows empty state for unplanned day', () => {
    const emptyEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [],
      is_rest_day: false,
    };
    render(<DayCard entry={emptyEntry} {...defaultProps} isExpanded={true} />);
    expect(screen.getByText('Kein Training geplant')).toBeDefined();
  });

  it('shows rest day state in expanded view', () => {
    const restEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [],
      is_rest_day: true,
    };
    render(<DayCard entry={restEntry} {...defaultProps} isExpanded={true} />);
    expect(screen.getByText('Ruhetag')).toBeDefined();
  });

  it('shows session notes in read-only summary', () => {
    const noteEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [{ position: 0, training_type: 'running', notes: 'Locker bleiben' }],
    };
    render(<DayCard entry={noteEntry} {...defaultProps} isExpanded={true} />);
    expect(screen.getByText('Locker bleiben')).toBeDefined();
  });

  it('shows segment count in summary', () => {
    const segEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        {
          position: 0,
          training_type: 'running',
          run_details: {
            run_type: 'intervals',
            target_duration_minutes: null,
            target_pace_min: null,
            target_pace_max: null,
            target_hr_min: null,
            target_hr_max: null,
            intervals: [
              {
                type: 'work',
                duration_minutes: 3,
                target_pace_min: null,
                target_pace_max: null,
                target_hr_min: null,
                target_hr_max: null,
                repeats: 1,
              },
              {
                type: 'recovery_jog',
                duration_minutes: 2,
                target_pace_min: null,
                target_pace_max: null,
                target_hr_min: null,
                target_hr_max: null,
                repeats: 1,
              },
            ],
          },
        },
      ],
    };
    render(<DayCard entry={segEntry} {...defaultProps} isExpanded={true} />);
    expect(screen.getByText('2 Seg.')).toBeDefined();
  });
});

describe('DayCard edit dialog', () => {
  it('opens edit dialog when edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<DayCard entry={baseEntry} {...defaultProps} isExpanded={true} />);
    await user.click(screen.getByLabelText('Training bearbeiten'));
    expect(screen.getByText(/Training bearbeiten/)).toBeDefined();
  });

  it('renders add session button in dialog', async () => {
    const user = userEvent.setup();
    render(<DayCard entry={baseEntry} {...defaultProps} isExpanded={true} />);
    await user.click(screen.getByLabelText('Training bearbeiten'));
    expect(screen.getByLabelText('Session hinzufuegen')).toBeDefined();
  });

  it('does not render add session button at max sessions in dialog', async () => {
    const user = userEvent.setup();
    const maxEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        { position: 0, training_type: 'running' },
        { position: 1, training_type: 'strength' },
        { position: 2, training_type: 'running' },
      ],
    };
    render(<DayCard entry={maxEntry} {...defaultProps} isExpanded={true} />);
    await user.click(screen.getByLabelText('Training bearbeiten'));
    expect(screen.queryByLabelText('Session hinzufuegen')).toBeNull();
  });

  it('renders remove button per session in dialog when multiple sessions', async () => {
    const user = userEvent.setup();
    const twoSessionEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        { position: 0, training_type: 'running' },
        { position: 1, training_type: 'strength' },
      ],
    };
    render(<DayCard entry={twoSessionEntry} {...defaultProps} isExpanded={true} />);
    await user.click(screen.getByLabelText('Training bearbeiten'));
    const removeButtons = screen.getAllByLabelText('Session entfernen');
    expect(removeButtons).toHaveLength(2);
  });

  it('does not render remove button for single session in dialog', async () => {
    const user = userEvent.setup();
    render(<DayCard entry={baseEntry} {...defaultProps} isExpanded={true} />);
    await user.click(screen.getByLabelText('Training bearbeiten'));
    expect(screen.queryByLabelText('Session entfernen')).toBeNull();
  });

  it('renders per-session notes input in dialog', async () => {
    const user = userEvent.setup();
    const twoSessionEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        { position: 0, training_type: 'running', notes: 'Locker bleiben' },
        { position: 1, training_type: 'strength', notes: null },
      ],
    };
    render(<DayCard entry={twoSessionEntry} {...defaultProps} isExpanded={true} />);
    await user.click(screen.getByLabelText('Training bearbeiten'));
    const notesInputs = screen.getAllByLabelText('Session Notizen');
    expect(notesInputs).toHaveLength(2);
  });
});
