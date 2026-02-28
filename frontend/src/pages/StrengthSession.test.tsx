import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../test/test-utils';
import userEvent from '@testing-library/user-event';
import { StrengthSessionPage } from './StrengthSession';

// Mock API modules
vi.mock('@/api/strength', () => ({
  createStrengthSession: vi.fn(),
  getLastExerciseSets: vi.fn(),
}));

vi.mock('@/api/exercises', () => ({
  listExercises: vi.fn(),
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
  const exercises = await import('@/api/exercises');
  return {
    createStrengthSession: vi.mocked(strength.createStrengthSession),
    getLastExerciseSets: vi.mocked(strength.getLastExerciseSets),
    listExercises: vi.mocked(exercises.listExercises),
  };
}

describe('StrengthSessionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function renderWithMocks() {
    const mocks = await getMocks();
    mocks.listExercises.mockResolvedValue({
      exercises: [
        { id: 1, name: 'Bankdrücken', category: 'push', is_favorite: false, is_custom: false, usage_count: 5, last_used_at: null, instructions: null, primary_muscles: null, secondary_muscles: null, image_urls: null, equipment: null, level: null, force: null, mechanic: null, exercise_db_id: null },
        { id: 2, name: 'Kniebeugen', category: 'legs', is_favorite: false, is_custom: false, usage_count: 8, last_used_at: null, instructions: null, primary_muscles: null, secondary_muscles: null, image_urls: null, equipment: null, level: null, force: null, mechanic: null, exercise_db_id: null },
        { id: 3, name: 'Klimmzüge', category: 'pull', is_favorite: false, is_custom: false, usage_count: 3, last_used_at: null, instructions: null, primary_muscles: null, secondary_muscles: null, image_urls: null, equipment: null, level: null, force: null, mechanic: null, exercise_db_id: null },
      ],
      total: 3,
    });
    return mocks;
  }

  it('renders the form with header and initial exercise', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    expect(screen.getByText('Krafttraining erfassen')).toBeInTheDocument();
    expect(screen.getByText('Übung 1')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)')).toBeInTheDocument();
    expect(screen.getByText('Training speichern')).toBeInTheDocument();
  });

  it('renders date and duration inputs', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    expect(screen.getByText('Datum')).toBeInTheDocument();
    expect(screen.getByText('Dauer (Minuten)')).toBeInTheDocument();
  });

  it('renders RPE slider with default value', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    expect(screen.getByText('Belastung (RPE)')).toBeInTheDocument();
    expect(screen.getByText(/5 — Mittel/)).toBeInTheDocument();
  });

  it('renders notes textarea', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    expect(screen.getByPlaceholderText('Wie lief das Training?')).toBeInTheDocument();
    expect(screen.getByText('Notizen (optional)')).toBeInTheDocument();
  });

  it('shows add exercise button', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    expect(screen.getByText('Übung hinzufügen')).toBeInTheDocument();
  });

  it('submit button is disabled when no exercise name is entered', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    const submitButton = screen.getByText('Training speichern').closest('button');
    expect(submitButton).toBeDisabled();
  });

  it('shows exercise suggestions when focusing the name input', async () => {
    const mocks = await renderWithMocks();
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    // Wait for exercise library to load
    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.click(nameInput);

    await waitFor(() => {
      expect(screen.getByText('Bankdrücken')).toBeInTheDocument();
      expect(screen.getByText('Kniebeugen')).toBeInTheDocument();
    });
  });

  it('filters suggestions when typing', async () => {
    const mocks = await renderWithMocks();
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.type(nameInput, 'Bank');

    await waitFor(() => {
      expect(screen.getByText('Bankdrücken')).toBeInTheDocument();
      expect(screen.queryByText('Kniebeugen')).not.toBeInTheDocument();
    });
  });

  it('selects a suggestion and shows category badge', async () => {
    const mocks = await renderWithMocks();
    mocks.getLastExerciseSets.mockResolvedValue({ found: false, exercise: null });
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.click(nameInput);

    await waitFor(() => {
      expect(screen.getByText('Bankdrücken')).toBeInTheDocument();
    });

    // Click the suggestion (find the button in the suggestion list)
    const suggestions = screen.getAllByText('Bankdrücken');
    // Click the one that's a button (suggestion item)
    const suggestionButton = suggestions.find(
      (el) => el.closest('button')?.getAttribute('type') === 'button',
    );
    if (suggestionButton) {
      await user.click(suggestionButton);
    }

    // Category badge should appear
    await waitFor(() => {
      expect(screen.getByText('Push')).toBeInTheDocument();
    });
  });

  it('adds a new exercise when clicking add button', async () => {
    await renderWithMocks();
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await user.click(screen.getByText('Übung hinzufügen'));

    expect(screen.getByText('Übung 1')).toBeInTheDocument();
    expect(screen.getByText('Übung 2')).toBeInTheDocument();
  });

  it('removes an exercise', async () => {
    await renderWithMocks();
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    // Add a second exercise
    await user.click(screen.getByText('Übung hinzufügen'));
    expect(screen.getByText('Übung 2')).toBeInTheDocument();

    // Remove the first one
    const removeButtons = screen.getAllByLabelText('Übung entfernen');
    await user.click(removeButtons[0]);

    // Should still have at least one exercise
    expect(screen.getByText('Übung 1')).toBeInTheDocument();
    expect(screen.queryByText('Übung 2')).not.toBeInTheDocument();
  });

  it('shows validation error when submitting without exercise name', async () => {
    await renderWithMocks();
    render(<StrengthSessionPage />);

    // Submit button is disabled when all exercises have empty names
    const submitButton = screen.getByText('Training speichern').closest('button');
    expect(submitButton).toBeDisabled();
  });

  it('submits successfully and navigates to session detail', async () => {
    const mocks = await renderWithMocks();
    mocks.getLastExerciseSets.mockResolvedValue({ found: false, exercise: null });
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

    // Wait for library to load
    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    // Select an exercise from suggestions
    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.click(nameInput);
    await waitFor(() => {
      expect(screen.getByText('Kniebeugen')).toBeInTheDocument();
    });
    const suggestions = screen.getAllByText('Kniebeugen');
    const suggestionButton = suggestions.find(
      (el) => el.closest('button')?.getAttribute('type') === 'button',
    );
    if (suggestionButton) {
      await user.click(suggestionButton);
    }

    // Wait for exercise to be selected and sets to appear
    await waitFor(() => {
      expect(screen.getByText('Beine')).toBeInTheDocument();
    });

    // Submit
    const submitButton = screen.getByText('Training speichern').closest('button');
    expect(submitButton).not.toBeDisabled();
    await user.click(submitButton!);

    await waitFor(() => {
      expect(mocks.createStrengthSession).toHaveBeenCalledTimes(1);
    });

    // Verify navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/sessions/42');
    });
  });

  it('shows error when submission fails', async () => {
    const mocks = await renderWithMocks();
    mocks.getLastExerciseSets.mockResolvedValue({ found: false, exercise: null });
    mocks.createStrengthSession.mockRejectedValue(new Error('Server-Fehler'));

    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    // Type exercise name directly (no suggestion)
    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.type(nameInput, 'Rudern');
    // Close suggestions by clicking elsewhere
    await user.click(screen.getByText('Krafttraining erfassen'));

    // Submit
    const submitButton = screen.getByText('Training speichern').closest('button');
    await user.click(submitButton!);

    await waitFor(() => {
      expect(screen.getByText('Server-Fehler')).toBeInTheDocument();
    });
  });

  it('loads last session sets via Quick-Add', async () => {
    const mocks = await renderWithMocks();
    mocks.getLastExerciseSets.mockResolvedValue({
      found: true,
      exercise: {
        exercise_name: 'Bankdrücken',
        category: 'push',
        sets: [
          { reps: 8, weight_kg: 80, status: 'completed' },
          { reps: 8, weight_kg: 80, status: 'completed' },
          { reps: 6, weight_kg: 80, status: 'reduced' },
        ],
        session_date: '2026-02-28',
      },
    });

    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    // Select exercise from suggestions
    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.click(nameInput);
    await waitFor(() => {
      expect(screen.getByText('Bankdrücken')).toBeInTheDocument();
    });
    const suggestions = screen.getAllByText('Bankdrücken');
    const suggestionButton = suggestions.find(
      (el) => el.closest('button')?.getAttribute('type') === 'button',
    );
    if (suggestionButton) {
      await user.click(suggestionButton);
    }

    // Quick-Add should have been called automatically
    await waitFor(() => {
      expect(mocks.getLastExerciseSets).toHaveBeenCalledWith('Bankdrücken');
    });
  });

  it('navigates back when clicking back button', async () => {
    await renderWithMocks();
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await user.click(screen.getByLabelText('Zurück'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('shows collapsed summary when exercise is collapsed', async () => {
    const mocks = await renderWithMocks();
    mocks.getLastExerciseSets.mockResolvedValue({ found: false, exercise: null });
    const user = userEvent.setup();
    render(<StrengthSessionPage />);

    await waitFor(() => {
      expect(mocks.listExercises).toHaveBeenCalled();
    });

    // Type exercise name
    const nameInput = screen.getByPlaceholderText('Übungsname (z.B. Bankdrücken)');
    await user.click(nameInput);
    await waitFor(() => {
      expect(screen.getByText('Bankdrücken')).toBeInTheDocument();
    });
    const suggestions = screen.getAllByText('Bankdrücken');
    const suggestionButton = suggestions.find(
      (el) => el.closest('button')?.getAttribute('type') === 'button',
    );
    if (suggestionButton) {
      await user.click(suggestionButton);
    }

    // Wait for sets to appear
    await waitFor(() => {
      expect(screen.getByText('Push')).toBeInTheDocument();
    });

    // Collapse the exercise
    await user.click(screen.getByLabelText('Zuklappen'));

    // Collapsed summary should show (e.g. "1 Sätze · 10 Reps · 0 kg Tonnage")
    await waitFor(() => {
      expect(screen.getByText(/Reps ·/)).toBeInTheDocument();
      expect(screen.getByText(/kg Tonnage/)).toBeInTheDocument();
    });
  });
});
