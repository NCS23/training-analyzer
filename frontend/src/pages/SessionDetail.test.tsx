import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test/test-utils';
import userEvent from '@testing-library/user-event';
import { SessionDetailPage } from './SessionDetail';
import type { SessionDetail } from '@/api/training';

// Mock API — all functions imported by the component
vi.mock('@/api/training', () => ({
  getSession: vi.fn(),
  deleteSession: vi.fn(),
  updateSessionNotes: vi.fn(),
  updateTrainingType: vi.fn(),
  updateLapOverrides: vi.fn(),
  getSessionTrack: vi.fn(),
  getWorkingZones: vi.fn(),
  getKmSplits: vi.fn(),
  recalculateSessionZones: vi.fn(),
  updateSessionDate: vi.fn(),
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

// Session with confirmed (user_override set) laps — no auto-edit
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
  rpe: null,
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
      user_override: 'warmup',
      start_seconds: 0,
      end_seconds: 300,
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
      suggested_type: 'steady',
      confidence: 'medium',
      user_override: 'steady',
      start_seconds: 300,
      end_seconds: 900,
    },
  ],
  hr_zones: {
    zone_1_recovery: { seconds: 300, percentage: 35.7, label: '< 150 bpm' },
    zone_2_base: { seconds: 240, percentage: 28.6, label: '150-160 bpm' },
    zone_3_tempo: { seconds: 300, percentage: 35.7, label: '> 160 bpm' },
  },
  has_gps: false,
  planned_entry_id: null,
  athlete_resting_hr: 65,
  athlete_max_hr: 185,
  exercises: null,
  ai_analysis: null,
  weather: null,
  location_name: null,
  air_quality: null,
  surface: null,
  elevation_corrected: false,
  created_at: '2025-02-25T08:00:00',
  updated_at: '2025-02-25T08:15:00',
};

// Session with unconfirmed laps — triggers auto-edit + classification banner
const mockSessionUnconfirmed: SessionDetail = {
  ...mockSession,
  laps: mockSession.laps!.map((l) => ({ ...l, user_override: null })),
};

async function getMocks() {
  const mod = await import('@/api/training');
  return {
    getSession: vi.mocked(mod.getSession),
    deleteSession: vi.mocked(mod.deleteSession),
    updateSessionNotes: vi.mocked(mod.updateSessionNotes),
    updateTrainingType: vi.mocked(mod.updateTrainingType),
    updateLapOverrides: vi.mocked(mod.updateLapOverrides),
  };
}

/** Open the "Aktionen" dropdown and click a menu item by text. */
async function clickDropdownItem(user: ReturnType<typeof userEvent.setup>, itemText: string) {
  const trigger = screen.getByRole('button', { name: 'Aktionen' });
  await user.click(trigger);
  const item = await screen.findByText(itemText);
  await user.click(item);
}

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
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
      expect(screen.getByText('8.5')).toBeInTheDocument();
    });

    expect(screen.getByText('145')).toBeInTheDocument();
    expect(screen.getByText('4:42')).toBeInTheDocument();
  });

  it('renders metrics grid with all values', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByLabelText('Kennzahlen')).toBeInTheDocument();
    });
    expect(screen.getByText('8.5')).toBeInTheDocument();
    expect(screen.getByText('4:42')).toBeInTheDocument();
  });

  it('shows training type badge in header', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Easy Run')).toBeInTheDocument();
    });
  });

  it('shows edit fields only in edit mode', async () => {
    const user = userEvent.setup();
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Easy Run')).toBeInTheDocument();
    });

    // Edit fields not visible in read-only mode
    expect(screen.queryByText('Trainingstyp')).not.toBeInTheDocument();
    expect(screen.queryByText('Datum')).not.toBeInTheDocument();

    // Enter edit mode via dropdown
    await clickDropdownItem(user, 'Bearbeiten');

    // Now edit fields should be visible
    expect(screen.getByText('Trainingstyp')).toBeInTheDocument();
    expect(screen.getByText('Datum')).toBeInTheDocument();
  });

  it('renders HR zones', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('HF-Zonen Gesamt')).toBeInTheDocument();
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

  it('shows lap badges in read-only mode', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Warm-up')).toBeInTheDocument();
    });
    expect(screen.getByText('Steady')).toBeInTheDocument();
  });

  it('renders notes as read-only text by default', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Notizen')).toBeInTheDocument();
    });
    // Notes shown as text, not textarea
    expect(screen.getByText('Gutes Training')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('shows textarea for notes in edit mode', async () => {
    const user = userEvent.setup();
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Notizen')).toBeInTheDocument();
    });

    // Enter edit mode via dropdown
    await clickDropdownItem(user, 'Bearbeiten');

    // Now textarea should be visible
    expect(screen.getByDisplayValue('Gutes Training')).toBeInTheDocument();
  });

  it('shows "Keine Notizen" when notes are empty', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue({ ...mockSession, notes: null });

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Keine Notizen')).toBeInTheDocument();
    });
  });

  it('toggles edit mode via dropdown and ActionBar', async () => {
    const user = userEvent.setup();
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Easy Run')).toBeInTheDocument();
    });

    // Enter edit mode via dropdown
    await clickDropdownItem(user, 'Bearbeiten');
    expect(screen.getByText('Ungespeicherte Änderungen')).toBeInTheDocument();
    expect(screen.getByText('Abbrechen')).toBeInTheDocument();

    // Click "Abbrechen" to exit edit mode
    fireEvent.click(screen.getByText('Abbrechen'));
    expect(screen.queryByText('Ungespeicherte Änderungen')).not.toBeInTheDocument();
  });

  it('shows delete confirmation dialog', async () => {
    const user = userEvent.setup();
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Easy Run')).toBeInTheDocument();
    });

    // Open delete dialog via dropdown
    await clickDropdownItem(user, 'Löschen');
    expect(screen.getByText('Session löschen?')).toBeInTheDocument();
  });

  it('deletes session and navigates away', async () => {
    const user = userEvent.setup();
    const { getSession, deleteSession } = await getMocks();
    getSession.mockResolvedValue(mockSession);
    deleteSession.mockResolvedValue(undefined);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Easy Run')).toBeInTheDocument();
    });

    // Open delete dialog via dropdown
    await clickDropdownItem(user, 'Löschen');

    // Click the confirmation button in the AlertDialog
    const deleteButtons = screen.getAllByRole('button', { name: 'Löschen' });
    // The AlertDialog action button is the last one
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);

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
      expect(screen.getByText('8.5')).toBeInTheDocument();
    });
    expect(screen.queryByText(/Laps/)).not.toBeInTheDocument();
  });

  it('renders session without HR zones', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue({ ...mockSession, hr_zones: null });

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('8.5')).toBeInTheDocument();
    });
    expect(screen.queryByText('HF-Zonen Verteilung')).not.toBeInTheDocument();
  });

  it('does not auto-open edit mode for unconfirmed laps', async () => {
    const { getSession } = await getMocks();
    getSession.mockResolvedValue(mockSessionUnconfirmed);

    render(<SessionDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('8.5')).toBeInTheDocument();
    });

    // Edit mode should NOT be auto-opened (classification review now happens on upload page)
    expect(screen.queryByText('Bearbeitungsmodus')).not.toBeInTheDocument();
    // No classification banner
    expect(screen.queryByText(/automatisch erkannt/)).not.toBeInTheDocument();
  });
});
