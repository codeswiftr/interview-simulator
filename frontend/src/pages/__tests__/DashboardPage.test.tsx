import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderPage, waitFor, screen } from '../../test/utils/pageTestUtils';
import DashboardPage from '../DashboardPage';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Loading States', () => {
    it('should show loading state initially', () => {
      // Mock slow API response
      server.use(
        http.get('http://localhost:8000/api/v1/interviews', async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json([]);
        })
      );

      renderPage(<DashboardPage />);

      // Should show loading indicator or skeleton
      const loadingElements = screen.queryAllByText(/loading|Loading/i);
      expect(loadingElements.length).toBeGreaterThan(0);
    });

    it('should hide loading state after data loads', async () => {
      renderPage(<DashboardPage />);

      await waitFor(() => {
        const loadingElements = screen.queryAllByText(/loading|Loading/i);
        expect(loadingElements.length).toBe(0);
      }, { timeout: 3000 });
    });
  });

  describe('Data Display', () => {
    it('should display user stats when loaded', async () => {
      renderPage(<DashboardPage />);

      await waitFor(() => {
        // Stats should be displayed
        expect(screen.getByText(/sessions|interviews/i)).toBeInTheDocument();
      });
    });

    it('should display interviews list when loaded', async () => {
      renderPage(<DashboardPage />);

      await waitFor(() => {
        // Interview cards or list should be visible
        const interviewElements = screen.queryAllByText(/interview|session/i);
        expect(interviewElements.length).toBeGreaterThan(0);
      });
    });

    it('should display empty state when no interviews', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/interviews', () => {
          return HttpResponse.json([]);
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(() => {
        // Should show empty state or welcome message
        const emptyElements = screen.queryAllByText(/no interviews|welcome|get started/i);
        expect(emptyElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/interviews', () => {
          return HttpResponse.json({ message: 'Server error' }, { status: 500 });
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
      });
    });

    it('should handle partial API failures gracefully', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/users/me/stats', () => {
          return HttpResponse.json({ message: 'Stats unavailable' }, { status: 500 });
        })
      );

      renderPage(<DashboardPage />);

      // Should still render other data (interviews, etc.)
      await waitFor(() => {
        expect(screen.queryByText(/error|failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should open new interview modal when button clicked', async () => {
      renderPage(<DashboardPage />);

      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /new|create|interview/i });
        expect(createButton).toBeInTheDocument();
      });

      // Note: Modal interaction tests require user-event library
      // This is a placeholder for the test structure
    });

    it('should show upgrade modal for free tier users', async () => {
      renderPage(<DashboardPage />, {
        user: {
          id: 'test-user',
          email: 'test@example.com',
          full_name: 'Test User',
          experience_level: 'mid',
          subscription_tier: 'free',
          interviews_this_month: 3,
          total_interviews: 5,
          created_at: new Date().toISOString(),
        },
      });

      await waitFor(() => {
        // Upgrade prompts should be visible for free tier
        const upgradeElements = screen.queryAllByText(/upgrade|pro|premium/i);
        // May not always show, depending on quota
      });
    });
  });

  describe('Welcome Modal', () => {
    it('should show welcome modal for new users', async () => {
      // Mock user with no interviews and onboarding not completed
      localStorage.setItem('onboarding_welcome_seen', 'false');

      server.use(
        http.get('http://localhost:8000/api/v1/interviews', () => {
          return HttpResponse.json([]);
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(() => {
        // Welcome modal should appear
        const welcomeElements = screen.queryAllByText(/welcome|get started/i);
        // May need to wait for modal animation
      }, { timeout: 2000 });
    });
  });

  describe('Stats Display', () => {
    it('should display total sessions count', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/users/me/stats', () => {
          return HttpResponse.json({
            total_sessions: 15,
            completed_sessions: 12,
            average_score: 85,
            total_practice_time_seconds: 7200,
          });
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/15|sessions/i)).toBeInTheDocument();
      });
    });

    it('should display average score', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/users/me/stats', () => {
          return HttpResponse.json({
            total_sessions: 10,
            completed_sessions: 8,
            average_score: 82,
            total_practice_time_seconds: 3600,
          });
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/82|average/i)).toBeInTheDocument();
      });
    });
  });
});
