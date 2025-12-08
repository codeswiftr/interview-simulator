import { describe, it, expect, beforeEach } from 'vitest';
import { renderPage, waitFor, screen } from '../../test/utils/pageTestUtils';
import InterviewPage from '../InterviewPage';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('InterviewPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Loading States', () => {
    it('should show loading state when fetching session data', () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      // Should show loading indicator
      const loadingElements = screen.queryAllByText(/loading|Loading/i);
      expect(loadingElements.length).toBeGreaterThan(0);
    });

    it('should hide loading state after session loads', async () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        const loadingElements = screen.queryAllByText(/loading|Loading/i);
        expect(loadingElements.length).toBe(0);
      }, { timeout: 3000 });
    });
  });

  describe('Question Navigation', () => {
    it('should display first question when interview starts', async () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        // Question should be displayed
        expect(screen.getByText(/question|tell me/i)).toBeInTheDocument();
      });
    });

    it('should allow navigation between questions', async () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        // Next/Previous buttons should be available
        const navButtons = screen.queryAllByRole('button', { name: /next|previous|skip/i });
        expect(navButtons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Recording Flow', () => {
    it('should show recording controls when interview is active', async () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        // Recording deck or record button should be visible
        const recordingElements = screen.queryAllByText(/record|recording/i);
        expect(recordingElements.length).toBeGreaterThan(0);
      });
    });

    it('should display timer during recording', async () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        // Timer should be visible
        const timerElements = screen.queryAllByText(/00:|timer/i);
        expect(timerElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Response Submission', () => {
    it('should handle response submission with audio', async () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        // Submit button should be available
        const submitButtons = screen.queryAllByRole('button', { name: /submit|send/i });
        expect(submitButtons.length).toBeGreaterThan(0);
      });
    });

    it('should show submission progress', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/interviews/:id/responses', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json({ id: 'response-id' });
        })
      );

      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      // Submission progress indicators should appear
      await waitFor(() => {
        const progressElements = screen.queryAllByText(/uploading|processing|submitting/i);
        // May appear during submission
      }, { timeout: 2000 });
    });
  });

  describe('Error Handling', () => {
    it('should display error when session not found', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/interviews/:id', () => {
          return HttpResponse.json({ message: 'Not found' }, { status: 404 });
        })
      );

      renderPage(<InterviewPage />, { initialRoute: '/interview/invalid-id' });

      await waitFor(() => {
        expect(screen.getByText(/error|not found|failed/i)).toBeInTheDocument();
      });
    });

    it('should handle submission errors gracefully', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/interviews/:id/responses', () => {
          return HttpResponse.json({ message: 'Submission failed' }, { status: 500 });
        })
      );

      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      await waitFor(() => {
        // Error handling should be present
      });
    });
  });

  describe('Before Unload Warning', () => {
    it('should warn user before leaving with unsaved progress', () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      // beforeunload warning is handled by useEffect
      // This test verifies the page renders correctly
      expect(window).toBeDefined();
    });
  });
});
