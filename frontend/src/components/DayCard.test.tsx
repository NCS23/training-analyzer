import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
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
    render(
      <DayCard
        entry={{ ...baseEntry, plan_id: 1, edited: true }}
        {...defaultProps}
      />,
    );
    expect(screen.getByLabelText('Manuell bearbeitet')).toBeDefined();
  });

  it('does not render pencil icon for manual entry', () => {
    render(
      <DayCard
        entry={{ ...baseEntry, plan_id: null, edited: false }}
        {...defaultProps}
      />,
    );
    expect(screen.queryByLabelText('Manuell bearbeitet')).toBeNull();
  });

  it('does not render pencil icon for generated + unedited entry', () => {
    render(
      <DayCard
        entry={{ ...baseEntry, plan_id: 1, edited: false }}
        {...defaultProps}
      />,
    );
    expect(screen.queryByLabelText('Manuell bearbeitet')).toBeNull();
  });
});

describe('DayCard multi-session header', () => {
  it('renders multiple session icons in collapsed header', () => {
    const multiEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        { position: 0, training_type: 'running', run_details: { run_type: 'easy', target_duration_minutes: 45, target_pace_min: null, target_pace_max: null, target_hr_min: null, target_hr_max: null, intervals: null } },
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

describe('DayCard expanded editor', () => {
  it('renders add session button in expanded state', () => {
    render(
      <DayCard
        entry={baseEntry}
        {...defaultProps}
        isExpanded={true}
      />,
    );
    expect(screen.getByLabelText('Session hinzufuegen')).toBeDefined();
  });

  it('does not render add session button at max sessions', () => {
    const maxEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        { position: 0, training_type: 'running' },
        { position: 1, training_type: 'strength' },
        { position: 2, training_type: 'running' },
      ],
    };
    render(
      <DayCard
        entry={maxEntry}
        {...defaultProps}
        isExpanded={true}
      />,
    );
    expect(screen.queryByLabelText('Session hinzufuegen')).toBeNull();
  });

  it('renders remove button per session when multiple sessions', () => {
    const twoSessionEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [
        { position: 0, training_type: 'running' },
        { position: 1, training_type: 'strength' },
      ],
    };
    render(
      <DayCard
        entry={twoSessionEntry}
        {...defaultProps}
        isExpanded={true}
      />,
    );
    const removeButtons = screen.getAllByLabelText('Session entfernen');
    expect(removeButtons).toHaveLength(2);
  });

  it('does not render remove button for single session', () => {
    render(
      <DayCard
        entry={baseEntry}
        {...defaultProps}
        isExpanded={true}
      />,
    );
    expect(screen.queryByLabelText('Session entfernen')).toBeNull();
  });

  it('shows initial type selector when no sessions and not rest day', () => {
    const emptyEntry: WeeklyPlanEntry = {
      ...baseEntry,
      sessions: [],
      is_rest_day: false,
    };
    render(
      <DayCard
        entry={emptyEntry}
        {...defaultProps}
        isExpanded={true}
      />,
    );
    expect(screen.getByLabelText('Trainingstyp')).toBeDefined();
  });
});
