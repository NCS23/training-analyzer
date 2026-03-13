import { vi, describe, it, expect } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { CategoryTonnageChart } from './CategoryTonnageChart';
import type { CategoryTonnageTrendResponse } from '@/api/progression';

// Mock recharts — jsdom has no ResizeObserver
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
}));

const MOCK_DATA: CategoryTonnageTrendResponse = {
  weeks: [
    {
      week: '2026-W10',
      week_start: '2026-03-02',
      categories: [
        { category: 'push', tonnage_kg: 600, exercise_count: 2, set_count: 6 },
        { category: 'legs', tonnage_kg: 500, exercise_count: 1, set_count: 3 },
      ],
      total_tonnage_kg: 1100,
    },
    {
      week: '2026-W11',
      week_start: '2026-03-09',
      categories: [
        { category: 'push', tonnage_kg: 650, exercise_count: 2, set_count: 8 },
        { category: 'pull', tonnage_kg: 300, exercise_count: 1, set_count: 4 },
      ],
      total_tonnage_kg: 950,
    },
  ],
  aggregated: [
    { category: 'push', tonnage_kg: 1250, exercise_count: 4, set_count: 14 },
    { category: 'legs', tonnage_kg: 500, exercise_count: 1, set_count: 3 },
    { category: 'pull', tonnage_kg: 300, exercise_count: 1, set_count: 4 },
  ],
  total_tonnage_kg: 2050,
  period_days: 90,
};

describe('CategoryTonnageChart', () => {
  it('renders heading and total tonnage', () => {
    render(<CategoryTonnageChart data={MOCK_DATA} />);
    expect(screen.getByText('Kategorie-Tonnage')).toBeInTheDocument();
    expect(screen.getByText(/2\.0t/)).toBeInTheDocument();
  });

  it('renders view toggle with Gesamt and Trend', () => {
    render(<CategoryTonnageChart data={MOCK_DATA} />);
    expect(screen.getByText('Gesamt')).toBeInTheDocument();
    expect(screen.getByText('Trend')).toBeInTheDocument();
  });

  it('renders nothing when data is null', () => {
    render(<CategoryTonnageChart data={null} />);
    expect(screen.queryByText('Kategorie-Tonnage')).not.toBeInTheDocument();
  });

  it('renders nothing when aggregated is empty', () => {
    const emptyData: CategoryTonnageTrendResponse = {
      weeks: [],
      aggregated: [],
      total_tonnage_kg: 0,
      period_days: 90,
    };
    render(<CategoryTonnageChart data={emptyData} />);
    expect(screen.queryByText('Kategorie-Tonnage')).not.toBeInTheDocument();
  });

  it('formats large tonnage as tons', () => {
    const largeData: CategoryTonnageTrendResponse = {
      ...MOCK_DATA,
      total_tonnage_kg: 5400,
    };
    render(<CategoryTonnageChart data={largeData} />);
    expect(screen.getByText(/5\.4t/)).toBeInTheDocument();
  });

  it('formats small tonnage as kg', () => {
    const smallData: CategoryTonnageTrendResponse = {
      ...MOCK_DATA,
      total_tonnage_kg: 750,
    };
    render(<CategoryTonnageChart data={smallData} />);
    expect(screen.getByText(/750 kg/)).toBeInTheDocument();
  });
});
