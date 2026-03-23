import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import VideoFeedbackCard from '../VideoFeedbackCard';

// Mock the API module so tests never make real HTTP calls
vi.mock('@/lib/api', () => ({
  videoAPI: {
    getVideoFeedback: vi.fn(),
  },
}));

// Convenience import after the mock is registered
import { videoAPI } from '@/lib/api';

const mockGetVideoFeedback = vi.mocked(videoAPI.getVideoFeedback);

const MOCK_FEEDBACK = {
  id: 'fb-001',
  response_id: 'resp-abc',
  engagement_score: 0.82,       // 82%
  eye_contact_percentage: 74.5,
};

describe('VideoFeedbackCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('renders engagement score correctly', () => {
    it('displays the engagement label and percentage', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce(MOCK_FEEDBACK);

      render(<VideoFeedbackCard responseId="resp-abc" />);

      await waitFor(() => {
        expect(screen.getByText('Engagement')).toBeInTheDocument();
      });

      // engagement_score 0.82 → 82%
      expect(screen.getByText('82%')).toBeInTheDocument();
    });

    it('renders the progress bar with correct aria attributes', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce(MOCK_FEEDBACK);

      render(<VideoFeedbackCard responseId="resp-abc" />);

      await waitFor(() => {
        const bar = screen.getByRole('progressbar', { name: /engagement score/i });
        expect(bar).toBeInTheDocument();
        expect(bar).toHaveAttribute('aria-valuenow', '82');
        expect(bar).toHaveAttribute('aria-valuemin', '0');
        expect(bar).toHaveAttribute('aria-valuemax', '100');
      });
    });

    it('displays the Video Analysis heading', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce(MOCK_FEEDBACK);

      render(<VideoFeedbackCard responseId="resp-abc" />);

      await waitFor(() => {
        expect(screen.getByText('Video Analysis')).toBeInTheDocument();
      });
    });
  });

  describe('renders eye contact percentage correctly', () => {
    it('shows rounded eye contact percentage inside the ring', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce(MOCK_FEEDBACK);

      render(<VideoFeedbackCard responseId="resp-abc" />);

      // 74.5 rounds to 75
      await waitFor(() => {
        expect(screen.getByText('75%')).toBeInTheDocument();
      });
    });

    it('shows the Eye Contact label', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce(MOCK_FEEDBACK);

      render(<VideoFeedbackCard responseId="resp-abc" />);

      await waitFor(() => {
        expect(screen.getByText('Eye Contact')).toBeInTheDocument();
      });
    });

    it('rounds a fractional eye contact value', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce({
        ...MOCK_FEEDBACK,
        eye_contact_percentage: 33.3,
      });

      render(<VideoFeedbackCard responseId="resp-abc" />);

      await waitFor(() => {
        expect(screen.getByText('33%')).toBeInTheDocument();
      });
    });
  });

  describe('renders nothing when API returns 404', () => {
    it('returns null when getVideoFeedback resolves to null (feature flag off)', async () => {
      mockGetVideoFeedback.mockResolvedValueOnce(null);

      const { container } = render(<VideoFeedbackCard responseId="resp-abc" />);

      await waitFor(() => {
        // Loading skeleton should be gone and nothing meaningful rendered
        expect(screen.queryByText('Video Analysis')).not.toBeInTheDocument();
        expect(screen.queryByText('Engagement')).not.toBeInTheDocument();
        expect(screen.queryByText('Eye Contact')).not.toBeInTheDocument();
      });

      // Container should be effectively empty (the component returned null)
      expect(container.firstChild).toBeNull();
    });

    it('shows a loading skeleton while the request is in flight', () => {
      // Promise that never resolves — simulates in-flight request
      mockGetVideoFeedback.mockReturnValueOnce(new Promise(() => {}));

      render(<VideoFeedbackCard responseId="resp-abc" />);

      expect(screen.getByLabelText('Loading video feedback')).toBeTruthy();
    });
  });
});
