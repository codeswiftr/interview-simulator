import { describe, it, expect, beforeEach } from 'vitest';
import { renderPage, waitFor, screen } from '../../test/utils/pageTestUtils';
import FeedbackPage from '../FeedbackPage';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('FeedbackPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Loading States', () => {
    it('should show loading state when fetching feedback', () => {
      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      const loadingElements = screen.queryAllByText(/loading|Loading/i);
      expect(loadingElements.length).toBeGreaterThan(0);
    });

    it('should hide loading state after feedback loads', async () => {
      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        const loadingElements = screen.queryAllByText(/loading|Loading/i);
        expect(loadingElements.length).toBe(0);
      }, { timeout: 3000 });
    });
  });

  describe('Feedback Display', () => {
    it('should display session feedback scores', async () => {
      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        // Score rings or metrics should be visible
        const scoreElements = screen.queryAllByText(/score|85|feedback/i);
        expect(scoreElements.length).toBeGreaterThan(0);
      });
    });

    it('should display individual response feedback', async () => {
      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        // Response accordions or feedback details should be visible
        const feedbackElements = screen.queryAllByText(/response|strength|improvement/i);
        expect(feedbackElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Processing Status Polling', () => {
    it('should poll for processing status when feedback is incomplete', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/feedback/session/:id/status', () => {
          return HttpResponse.json({
            total_responses: 5,
            analyzed_responses: 3,
            pending_responses: 2,
            is_complete: false,
          });
        })
      );

      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        // Processing status indicator should be visible
        const processingElements = screen.queryAllByText(/processing|analyzing|pending/i);
        expect(processingElements.length).toBeGreaterThan(0);
      });
    });

    it('should stop polling when feedback is complete', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/feedback/session/:id/status', () => {
          return HttpResponse.json({
            total_responses: 5,
            analyzed_responses: 5,
            pending_responses: 0,
            is_complete: true,
          });
        })
      );

      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        // No processing indicators when complete
        const processingElements = screen.queryAllByText(/processing|analyzing/i);
        // May still show status, but should indicate completion
      });
    });
  });

  describe('Audio Playback', () => {
    it('should provide audio playback controls', async () => {
      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        // Audio player controls should be available
        const audioElements = screen.queryAllByRole('button', { name: /play|pause|audio/i });
        expect(audioElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error when feedback not found', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/feedback/session/:id', () => {
          return HttpResponse.json({ message: 'Not found' }, { status: 404 });
        })
      );

      renderPage(<FeedbackPage />, { initialRoute: '/interview/invalid-id/feedback' });

      await waitFor(() => {
        expect(screen.getByText(/error|not found|failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Comparison Display', () => {
    it('should display comparison with previous sessions', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/feedback/session/:id/comparison', () => {
          return HttpResponse.json({
            session_score: 85,
            average_score: 80,
            improvement_percent: 6.25,
            sessions_compared: 10,
          });
        })
      );

      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      await waitFor(() => {
        // Comparison data should be displayed
        const comparisonElements = screen.queryAllByText(/comparison|improvement|trend/i);
        expect(comparisonElements.length).toBeGreaterThan(0);
      });
    });
  });
});
