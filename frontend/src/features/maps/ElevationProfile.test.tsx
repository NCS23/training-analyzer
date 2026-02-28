import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ElevationProfile } from './ElevationProfile';
import type { GPSPoint } from '@/api/training';

// Mock ResizeObserver (needed by ResponsiveContainer)
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
vi.stubGlobal('ResizeObserver', MockResizeObserver);

/* ------------------------------------------------------------------ */
/*  Test Data                                                          */
/* ------------------------------------------------------------------ */

const mockPoints: GPSPoint[] = Array.from({ length: 20 }, (_, i) => ({
  lat: 52.52 + i * 0.001,
  lng: 13.405,
  alt: 50 + i * 2,
  hr: 120 + i,
  seconds: i * 10,
}));

const pointsWithoutAlt: GPSPoint[] = [
  { lat: 52.52, lng: 13.405, seconds: 0 },
  { lat: 52.521, lng: 13.405, seconds: 10 },
];

/* ------------------------------------------------------------------ */
/*  Tests                                                              */
/* ------------------------------------------------------------------ */

describe('ElevationProfile', () => {
  it('renders nothing when no altitude data', () => {
    const { container } = render(
      <ElevationProfile points={pointsWithoutAlt} totalAscentM={null} totalDescentM={null} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('renders summary metrics', () => {
    render(<ElevationProfile points={mockPoints} totalAscentM={150} totalDescentM={80} />);
    expect(screen.getByText(/150 m/)).toBeInTheDocument();
    expect(screen.getByText(/80 m/)).toBeInTheDocument();
  });

  it('renders min/max altitude range', () => {
    render(<ElevationProfile points={mockPoints} totalAscentM={null} totalDescentM={null} />);
    // After smoothing, min/max are slightly compressed from raw 50-88
    expect(screen.getByText(/\d+–\d+ m/)).toBeInTheDocument();
  });

  it('renders chart container with aria-label', () => {
    render(<ElevationProfile points={mockPoints} totalAscentM={150} totalDescentM={80} />);
    const chart = screen.getByLabelText(/Höhenprofil/);
    expect(chart).toBeInTheDocument();
  });

  it('renders with responsive height classes', () => {
    render(<ElevationProfile points={mockPoints} totalAscentM={null} totalDescentM={null} />);
    const chart = screen.getByLabelText(/Höhenprofil/);
    expect(chart.className).toContain('h-[150px]');
    expect(chart.className).toContain('md:h-[200px]');
  });
});
