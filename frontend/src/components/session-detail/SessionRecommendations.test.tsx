import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import userEvent from '@testing-library/user-event';
import { SessionRecommendations } from './SessionRecommendations';
import type { RecommendationsList, AIRecommendation } from '@/api/training';

const MOCK_RECOMMENDATIONS: AIRecommendation[] = [
  {
    id: 1,
    session_id: 42,
    type: 'adjust_pace',
    title: 'Long Run Tempo reduzieren',
    target_session_id: null,
    current_value: '5:20 min/km',
    suggested_value: '5:40 min/km',
    reasoning: 'Die HF war im oberen Zone-2-Bereich.',
    priority: 'high',
    status: 'pending',
    created_at: '2026-03-17T10:00:00',
  },
  {
    id: 2,
    session_id: 42,
    type: 'add_rest',
    title: 'Ruhetag einlegen',
    target_session_id: null,
    current_value: 'Tempo-Lauf geplant',
    suggested_value: 'Ruhetag',
    reasoning: 'Regeneration nötig nach intensiver Woche.',
    priority: 'medium',
    status: 'pending',
    created_at: '2026-03-17T10:00:00',
  },
];

const MOCK_RESPONSE: RecommendationsList = {
  recommendations: MOCK_RECOMMENDATIONS,
  session_id: 42,
  provider: 'Claude (test)',
  cached: true,
};

const mockGetRecommendations = vi.fn();
const mockGenerateRecommendations = vi.fn();
const mockUpdateRecommendationStatus = vi.fn();

vi.mock('@/api/training', () => ({
  getRecommendations: (...args: unknown[]) => mockGetRecommendations(...args),
  generateRecommendations: (...args: unknown[]) => mockGenerateRecommendations(...args),
  updateRecommendationStatus: (...args: unknown[]) => mockUpdateRecommendationStatus(...args),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('SessionRecommendations', () => {
  it('renders nothing when hasAnalysis is false', () => {
    render(<SessionRecommendations sessionId={42} hasAnalysis={false} />);
    expect(screen.queryByText('KI-Empfehlungen')).not.toBeInTheDocument();
    expect(screen.queryByText('Empfehlungen generieren')).not.toBeInTheDocument();
  });

  it('shows generate button when no recommendations exist', async () => {
    mockGetRecommendations.mockResolvedValue({
      ...MOCK_RESPONSE,
      recommendations: [],
    });

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('Empfehlungen generieren')).toBeInTheDocument();
    });
  });

  it('shows recommendation cards after fetching', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('KI-Empfehlungen')).toBeInTheDocument();
      expect(screen.getByText('Long Run Tempo reduzieren')).toBeInTheDocument();
      expect(screen.getByText('Ruhetag einlegen')).toBeInTheDocument();
    });
  });

  it('shows current and suggested values', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('5:20 min/km')).toBeInTheDocument();
      expect(screen.getByText('5:40 min/km')).toBeInTheDocument();
    });
  });

  it('shows pending count badge', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('2 neu')).toBeInTheDocument();
    });
  });

  it('expands card to show reasoning and action buttons', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);
    const user = userEvent.setup();

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('Long Run Tempo reduzieren')).toBeInTheDocument();
    });

    // Reasoning should not be visible initially
    expect(screen.queryByText(/HF war im oberen Zone-2/)).not.toBeInTheDocument();

    // Click expand button
    const expandButtons = screen.getAllByLabelText('Details aufklappen');
    await user.click(expandButtons[0]);

    // Now reasoning and actions should be visible
    expect(screen.getByText(/HF war im oberen Zone-2/)).toBeInTheDocument();
    expect(screen.getByText('Übernehmen')).toBeInTheDocument();
    expect(screen.getByText('Ablehnen')).toBeInTheDocument();
  });

  it('calls updateStatus when dismiss is clicked', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);
    mockUpdateRecommendationStatus.mockResolvedValue({
      ...MOCK_RECOMMENDATIONS[0],
      status: 'dismissed',
    });
    const user = userEvent.setup();

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('Long Run Tempo reduzieren')).toBeInTheDocument();
    });

    // Expand first card
    const expandButtons = screen.getAllByLabelText('Details aufklappen');
    await user.click(expandButtons[0]);

    // Click dismiss
    await user.click(screen.getByText('Ablehnen'));

    expect(mockUpdateRecommendationStatus).toHaveBeenCalledWith(1, 'dismissed');
  });

  it('calls generate with forceRefresh on Neu button', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);
    mockGenerateRecommendations.mockResolvedValue(MOCK_RESPONSE);
    const user = userEvent.setup();

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('KI-Empfehlungen')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Neu'));

    expect(mockGenerateRecommendations).toHaveBeenCalledWith(42, true);
  });

  it('shows priority badges', async () => {
    mockGetRecommendations.mockResolvedValue(MOCK_RESPONSE);

    render(<SessionRecommendations sessionId={42} hasAnalysis={true} />);

    await waitFor(() => {
      expect(screen.getByText('Hoch')).toBeInTheDocument();
      expect(screen.getByText('Mittel')).toBeInTheDocument();
    });
  });
});
