import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test/test-utils';
import { SessionDetailPage } from './SessionDetail';
import type { SessionDetail } from '@/api/training';

// Mock API
vi.mock('@/api/training', () => ({
  getSession: vi.fn(),
  deleteSession: vi.fn(),
  updateSessionNotes: vi.fn(),
  updateTrainingType: vi.fn(),
}));

// Mock useParams and useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: '1' }),
    useNavigate: () => mockNavigate,
  };
});

const mockSession: SessionDetail = {
  id: 1,
  date: '2025-02-25',
  workout_type: 'running',
  subtype: null,
  training_type: {
    auto: 'easy',
    confidence: 75,
    override: null,
    effective: 'easy',
  },
  duration_sec: 2400,
  distance_km: 8.5,
  pace: '4:42',
  hr_avg: 145,
  hr_max: 168,
  hr_min: 110,
  cadence_avg: 172,
  notes: 'Gutes Training',
  laps: [
    {
      lap_number: 1,
      duration_seconds: 300,
      duration_formatted: '05:00',
      distance_km: 0.9,
      pace_min_per_km: 5.56,
      pace_formatted: '5:33',
      avg_hr_bpm: 135,
      max_hr_bpm: 145,
      min_hr_bpm: 120,
      avg_cadence_spm: 165,
      suggested_type: 'warmup',
      confidence: 'high',
      user_override: null,
    },
    {
      lap_number: 2,
      duration_seconds: 600,
      duration_formatted: '10:00',
      distance_km: 2.0,
      pace_min_per_km: 5.0,
      pace_formatted: '5:00',
      avg_hr_bpm: 155,
      max_hr_bpm: 168,
      min_hr_bpm: 140,
      avg_cadence_spm: 175,
      suggested_type: 'tempo',
      confidence: 'medium',
      user_override: null,
    },
  ],
  hr_zones: {
    zone_1_recovery: { seconds: 300, percentage: 35.7, label: '< 150 bpm' },
    zone_2_base: { seconds: 240, percentage: 28.6, label: '150-160 bpm' },
    zone_3_tempo: { seconds: 300, percentage: 35.7, label: '> 160 bpm' },
  },
  created_at: '2025-02-25T08:00:00',
  updated_at: '2025-02-25T08:15:00',
};

async function getMocks() {
  const mod = await import('@/api/training');
  return {
    getSession: vi.mocked(mod.getSession),
    deleteSession: vi.mocked(mod.deleteSession),
    updateSessionNotes: vi.mocked(mod.updateSessionNotes),
    updateTrainingType: vi.mocked(mod.updateTrainingType),
  };
}

describe('SessionDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', async () => {
    const { getSession } = await getMocks();
    getSession.mockReturnValue(new Promise(() => {})); // Never resolves

    render(<SessionDetailPage />);
    expect(document.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders session data after loading', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('8.5 km')).toBeInTheDocument();
    });

    expect(screen.getByText('145 bpm')).toBeInTheDocument();
    expect(screen.getByText('4:42 /km')).toBeInTheDocument();
  });

  it('renders metrics grid with all values', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Kennzahlen')).toBeInTheDocument();
    });
    // Check specific metric values (unique per card)
    expect(screen.getByText('8.5 km')).toBeInTheDocument();
    expect(screen.getByText('4:42 /km')).toBeInTheDocument();
  });

  it('renders training type badge', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Trainingstyp:')).toBeInTheDocument();
    });
    expect(screen.getByText('(75% Konfidenz)')).toBeInTheDocument();
  });

  it('renders HR zones', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('HF-Zonen Verteilung')).toBeInTheDocument();
    });
  });

  it('renders laps table', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Laps (2)')).toBeInTheDocument();
    });
    expect(screen.getByText('05:00')).toBeInTheDocument();
    expect(screen.getByText('10:00')).toBeInTheDocument();
  });

  it('renders notes field with existing notes', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Notizen')).toBeInTheDocument();
    });
    const textarea = screen.getByDisplayValue('Gutes Training');
    expect(textarea).toBeInTheDocument();
  });

  it('shows delete confirmation dialog', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Session loeschen')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Session loeschen'));
    expect(screen.getByText('Wirklich loeschen?')).toBeInTheDocument();
    expect(screen.getByText('Ja, loeschen')).toBeInTheDocument();
    expect(screen.getByText('Abbrechen')).toBeInTheDocument();
  });

  it('cancels delete when clicking Abbrechen', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Session loeschen')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Session loeschen'));
    fireEvent.click(screen.getByText('Abbrechen'));
    expect(screen.queryByText('Wirklich loeschen?')).not.toBeInTheDocument();
  });

  it('deletes session and navigates away', async () => {
    const { getSession, deleteSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);
    deleteSession.mockResolvedValue(undefined);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Session loeschen')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Session loeschen'));
    fireEvent.click(screen.getByText('Ja, loeschen'));

    await waitFor(() => {
      expect(deleteSession).toHaveBeenCalledWith(1);
      expect(mockNavigate).toHaveBeenCalledWith('/sessions', { replace: true });
    });
  });

  it('shows error state when session not found', async () => {
    const { getSession } = await getMocks();
    getSession.mockRejectedValue(new Error('Not found'));

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Session konnte nicht geladen werden.')).toBeInTheDocument();
    });
  });

  it('renders session without laps', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue({ ...mockSession, laps: null });

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('8.5 km')).toBeInTheDocument();
    });
    expect(screen.queryByText(/Laps/)).not.toBeInTheDocument();
  });

  it('renders session without HR zones', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue({ ...mockSession, hr_zones: null });

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('8.5 km')).toBeInTheDocument();
    });
    expect(screen.queryByText('HF-Zonen Verteilung')).not.toBeInTheDocument();
  });
});
