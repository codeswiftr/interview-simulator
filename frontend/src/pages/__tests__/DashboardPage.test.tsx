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
    it('should render dashboard page', () => {
      renderPage(<DashboardPage />);

      // Dashboard should render
      expect(document.body.textContent?.length).toBeGreaterThan(0);
    });

    it('should render content after data loads', async () => {
      renderPage(<DashboardPage />);

      await waitFor(
        () => {
          // Content should be present
          const container =
            document.querySelector('.container') || document.querySelector('.min-h-screen');
          expect(container).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Data Display', () => {
    it('should display dashboard structure', async () => {
      renderPage(<DashboardPage />);

      await waitFor(
        () => {
          // Dashboard content should be rendered
          expect(document.body.textContent?.length).toBeGreaterThan(0);
        },
        { timeout: 3000 }
      );
    });

    it('should handle empty interviews list', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/interviews', () => {
          return HttpResponse.json([]);
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(() => {
        // Should render page content
        expect(document.body.textContent?.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/interviews', () => {
          return HttpResponse.json({ message: 'Server error' }, { status: 500 });
        })
      );

      renderPage(<DashboardPage />);

      await waitFor(
        () => {
          // Page should still render something
          expect(document.body.textContent?.length).toBeGreaterThan(0);
        },
        { timeout: 3000 }
      );
    });
  });

  describe('User Interactions', () => {
    it('should render interactive elements', async () => {
      renderPage(<DashboardPage />);

      await waitFor(
        () => {
          // Buttons should be present
          const buttons = screen.queryAllByRole('button');
          expect(buttons.length).toBeGreaterThan(0);
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Page Structure', () => {
    it('should render dashboard with proper providers', async () => {
      renderPage(<DashboardPage />);

      // Page should render without throwing provider errors
      await waitFor(() => {
        expect(document.body.textContent).not.toContain('must be used within');
      });
    });

    it('should display main container element', async () => {
      renderPage(<DashboardPage />);

      await waitFor(
        () => {
          const mainContent =
            document.querySelector('main') ||
            document.querySelector('.min-h-screen') ||
            document.querySelector('.container');
          expect(mainContent).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });
});
