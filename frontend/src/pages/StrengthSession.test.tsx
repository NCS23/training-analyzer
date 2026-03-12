import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/test-utils';
import userEvent from '@testing-library/user-event';
import { StrengthSessionPage } from './StrengthSession';

// Mock API modules
vi.mock('@/api/strength', () => ({
  createStrengthSession: vi.fn(),
  getLastCompleteStrengthSession: vi.fn().mockResolvedValue({ found: false, session: null }),
}));

vi.mock('@/api/session-templates', () => ({
  listSessionTemplates: vi.fn().mockResolvedValue({ templates: [] }),
  getSessionTemplate: vi.fn(),
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
  const strength = await import('@/api/strength');
  return {
    createStrengthSession: vi.mocked(strength.createStrengthSession),
  };
}

// eslint-disable-next-line max-lines-per-function -- TODO: E16 Refactoring
describe('StrengthSessionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with header and initial exercise', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText('Krafttraining erfassen')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Übungsname')).toBeInTheDocument();
    expect(screen.getByText('Training speichern')).toBeInTheDocument();
  });

  it('renders exercises container with count', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText(/Übungen \(/)).toBeInTheDocument();
  });

  it('renders date and duration inputs', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText('Datum')).toBeInTheDocument();
    expect(screen.getByText('Dauer (Minuten)')).toBeInTheDocument();
  });

  it('renders RPE slider with default value', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText('Belastung (RPE)')).toBeInTheDocument();
    expect(screen.getByText(/5 — Mittel/)).toBeInTheDocument();
  });

  it('renders notes textarea', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByPlaceholderText('Wie lief das Training?')).toBeInTheDocument();
    expect(screen.getByText('Notizen (optional)')).toBeInTheDocument();
  });

  it('shows add exercise button', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText('Übung hinzufügen')).toBeInTheDocument();
  });

  it('submit button is disabled when no exercise name is entered', () => {
    render(<StrengthSessionPage />);

    const submitButton = screen.getByText('Training speichern').closest('button');
    expect(submitButton).toBeDisabled();
  });

  it('adds a new exercise when clicking add button', async () => {
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    // Initially 1 name input
    expect(screen.getAllByPlaceholderText('Übungsname')).toHaveLength(1);

    await user.click(screen.getByText('Übung hinzufügen'));

    // Now 2 name inputs
    expect(screen.getAllByPlaceholderText('Übungsname')).toHaveLength(2);
  });

  it('removes an exercise', async () => {
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    // Add a second exercise
    await user.click(screen.getByText('Übung hinzufügen'));
    expect(screen.getAllByPlaceholderText('Übungsname')).toHaveLength(2);

    // Remove the first one
    const removeButtons = screen.getAllByLabelText('Übung entfernen');
    await user.click(removeButtons[0]);

    // Should still have at least one exercise
    expect(screen.getAllByPlaceholderText('Übungsname')).toHaveLength(1);
  });

  it('submits successfully and navigates to session detail', async () => {
    const mocks = await getMocks();
    mocks.createStrengthSession.mockResolvedValue({
      success: true,
      session_id: 42,
      metrics: {
        total_exercises: 1,
        total_sets: 3,
        total_tonnage_kg: 1800,
        completed_sets: 3,
      },
    });

    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    // Type exercise name
    const nameInput = screen.getByPlaceholderText('Übungsname');
    await user.type(nameInput, 'Bankdrücken');

    // Submit
    const submitButton = screen.getByText('Training speichern').closest('button');
    expect(submitButton).not.toBeDisabled();
    await user.click(submitButton!);

    await waitFor(() => {
      expect(mocks.createStrengthSession).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/sessions/42');
    });
  });

  it('shows error when submission fails', async () => {
    const mocks = await getMocks();
    mocks.createStrengthSession.mockRejectedValue(new Error('Server-Fehler'));

    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    // Type exercise name
    const nameInput = screen.getByPlaceholderText('Übungsname');
    await user.type(nameInput, 'Rudern');

    // Submit
    const submitButton = screen.getByText('Training speichern').closest('button');
    await user.click(submitButton!);

    await waitFor(() => {
      expect(screen.getByText('Server-Fehler')).toBeInTheDocument();
    });
  });

  it('navigates back when clicking back button', async () => {
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await user.click(screen.getByLabelText('Zurück'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('shows set header labels', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText('#')).toBeInTheDocument();
    expect(screen.getByText('Wdh.')).toBeInTheDocument();
    expect(screen.getByText('kg')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('shows add set button', () => {
    render(<StrengthSessionPage />);

    expect(screen.getByText('Satz hinzufügen')).toBeInTheDocument();
  });
});
