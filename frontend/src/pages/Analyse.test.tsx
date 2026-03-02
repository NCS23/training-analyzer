import { vi, describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { AnalysePage } from './Analyse';

// Mock recharts — jsdom has no ResizeObserver
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => <div />,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Cell: () => <div />,
}));

// Mock API — Running Trends
vi.mock('@/api/trends', () => ({
  getTrends: vi.fn().mockResolvedValue({
    weeks: [
      {
        week: '2026-W08',
        week_start: '2026-02-16',
        session_count: 3,
        total_distance_km: 25.0,
        total_duration_sec: 7200,
        avg_pace_sec_per_km: 360,
        avg_pace_formatted: '6:00',
        avg_hr_bpm: 155,
      },
    ],
    insights: [{ type: 'positive', message: 'Pace verbessert!' }],
  }),
}));

// Mock API — Training Balance
vi.mock('@/api/training-balance', () => ({
  getTrainingBalance: vi.fn().mockResolvedValue({
    period_days: 28,
    sport_mix: {
      running_sessions: 3,
      strength_sessions: 2,
      running_percent: 60,
      strength_percent: 40,
      total_sessions: 5,
    },
    intensity: {
      easy_percent: 70,
      moderate_percent: 20,
      hard_percent: 10,
      easy_sessions: 3,
      moderate_sessions: 1,
      hard_sessions: 1,
      total_sessions: 5,
      is_polarized: false,
    },
    volume_weeks: [],
    muscle_groups: [],
    insights: [],
  }),
}));

describe('AnalysePage', () => {
  it('renders heading and time range selector', async () => {
    render(<AnalysePage />);
    await waitFor(() => {
      expect(screen.getByText('Analyse')).toBeInTheDocument();
    });
    expect(screen.getByText('4W')).toBeInTheDocument();
  });

  it('renders all three tabs', () => {
    render(<AnalysePage />);
    expect(screen.getByText('Laufen')).toBeInTheDocument();
    expect(screen.getByText('Kraft')).toBeInTheDocument();
    expect(screen.getByText('Balance')).toBeInTheDocument();
  });

  it('shows insights after loading', async () => {
    render(<AnalysePage />);
    await waitFor(() => {
      expect(screen.getByText('Pace verbessert!')).toBeInTheDocument();
    });
  });

  it('shows summary totals', async () => {
    render(<AnalysePage />);
    await waitFor(() => {
      expect(screen.getByText('25.0 km')).toBeInTheDocument();
    });
  });
});
