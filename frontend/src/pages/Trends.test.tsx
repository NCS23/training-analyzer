import { vi, describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { TrendsPage } from './Trends';

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
}));

// Mock API
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

describe('TrendsPage', () => {
  it('renders heading and time range selector', async () => {
    render(<TrendsPage />);
    await waitFor(() => {
      expect(screen.getByText('Trends')).toBeInTheDocument();
    });
    expect(screen.getByText('4W')).toBeInTheDocument();
  });

  it('shows insights after loading', async () => {
    render(<TrendsPage />);
    await waitFor(() => {
      expect(screen.getByText('Pace verbessert!')).toBeInTheDocument();
    });
  });

  it('shows summary totals', async () => {
    render(<TrendsPage />);
    await waitFor(() => {
      expect(screen.getByText('25.0 km')).toBeInTheDocument();
    });
  });
});
