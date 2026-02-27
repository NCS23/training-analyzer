import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test/test-utils';
import UploadPage from './Upload';

// Mock the API module
vi.mock('@/api/training', () => ({
  parseTraining: vi.fn(),
  uploadTraining: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

async function getMocks() {
  const mod = await import('@/api/training');
  return {
    parseTraining: vi.mocked(mod.parseTraining),
    uploadTraining: vi.mocked(mod.uploadTraining),
  };
}

describe('UploadPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the upload wizard', () => {
    render(<UploadPage />);
    expect(screen.getByText('Training Upload')).toBeInTheDocument();
    expect(screen.getByText('Training importieren')).toBeInTheDocument();
    expect(screen.getByText('Weiter')).toBeInTheDocument();
  });

  it('renders training type toggle', () => {
    render(<UploadPage />);
    expect(screen.getByText('Laufen')).toBeInTheDocument();
    expect(screen.getByText('Kraft')).toBeInTheDocument();
  });

  it('Weiter button is disabled without file', () => {
    render(<UploadPage />);
    const button = screen.getByText('Weiter');
    expect(button).toBeDisabled();
  });

  it('shows review step after successful parse', async () => {
    const { parseTraining } = await getMocks();
    parseTraining.mockResolvedValue({
      success: true,
      data: {
        laps: [
          {
            lap_number: 1,
            duration_seconds: 300,
            duration_formatted: '05:00',
            distance_km: 1.0,
            pace_min_per_km: 5.0,
            pace_formatted: '5:00',
            avg_hr_bpm: 140,
            suggested_type: 'easy',
            confidence: 'high',
          },
        ],
        summary: {
          total_duration_seconds: 300,
          total_duration_formatted: '05:00',
          total_distance_km: 1.0,
          avg_hr_bpm: 140,
          avg_pace_formatted: '5:00',
        },
      },
      metadata: {
        training_type_auto: 'easy',
        training_type_confidence: 85,
      },
    });

    render(<UploadPage />);

    // Simulate file upload via the FileUpload's onUpload callback
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    Object.defineProperty(fileInput, 'files', { value: [file] });
    fireEvent.change(fileInput);

    // Click "Weiter"
    const button = screen.getByText('Weiter');
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Klassifikation prüfen')).toBeInTheDocument();
    });

    expect(screen.getByText('Session anlegen')).toBeInTheDocument();
    expect(screen.getByText('Zurück')).toBeInTheDocument();
  });

  it('navigates back from review to upload step', async () => {
    const { parseTraining } = await getMocks();
    parseTraining.mockResolvedValue({
      success: true,
      data: {
        laps: null,
        summary: {
          total_duration_seconds: 600,
          avg_hr_bpm: 130,
        },
      },
      metadata: {
        training_type_auto: 'easy',
        training_type_confidence: 90,
      },
    });

    render(<UploadPage />);

    // Upload file and go to review
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    Object.defineProperty(fileInput, 'files', { value: [file] });
    fireEvent.change(fileInput);

    fireEvent.click(screen.getByText('Weiter'));

    await waitFor(() => {
      expect(screen.getByText('Klassifikation prüfen')).toBeInTheDocument();
    });

    // Click "Zurück"
    fireEvent.click(screen.getByText('Zurück'));

    expect(screen.getByText('Training importieren')).toBeInTheDocument();
    expect(screen.getByText('Weiter')).toBeInTheDocument();
  });

  it('creates session and navigates on success', async () => {
    const { parseTraining, uploadTraining } = await getMocks();
    parseTraining.mockResolvedValue({
      success: true,
      data: {
        laps: null,
        summary: { total_duration_seconds: 600, avg_hr_bpm: 130 },
      },
      metadata: { training_type_auto: 'easy', training_type_confidence: 90 },
    });
    uploadTraining.mockResolvedValue({ success: true, session_id: 42 });

    render(<UploadPage />);

    // Upload file and go to review
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    Object.defineProperty(fileInput, 'files', { value: [file] });
    fireEvent.change(fileInput);

    fireEvent.click(screen.getByText('Weiter'));

    await waitFor(() => {
      expect(screen.getByText('Session anlegen')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Session anlegen'));

    await waitFor(() => {
      expect(uploadTraining).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/sessions/42', { state: { uploaded: true } });
    });
  });

  it('shows error when parse fails', async () => {
    const { parseTraining } = await getMocks();
    parseTraining.mockRejectedValue(new Error('Network error'));

    render(<UploadPage />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    Object.defineProperty(fileInput, 'files', { value: [file] });
    fireEvent.change(fileInput);

    fireEvent.click(screen.getByText('Weiter'));

    await waitFor(() => {
      expect(screen.getByText(/Netzwerkfehler/)).toBeInTheDocument();
    });
  });
});
