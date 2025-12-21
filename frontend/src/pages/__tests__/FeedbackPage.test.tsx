import { describe, it, expect, beforeEach } from 'vitest';
import { renderPage } from '../../test/utils/pageTestUtils';
import FeedbackPage from '../FeedbackPage';

describe('FeedbackPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Page Structure', () => {
    it('should render without crashing', () => {
      const { container } = renderPage(<FeedbackPage />, {
        initialRoute: '/interview/test-id/feedback',
      });

      expect(container).toBeInTheDocument();
    });

    it('should render within providers without errors', () => {
      renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      // Page should render without throwing context errors
      expect(document.body.textContent).not.toContain('must be used within');
    });

    it('should render content', () => {
      const { container } = renderPage(<FeedbackPage />, { initialRoute: '/interview/test-id/feedback' });

      // Container should have content
      expect(container.innerHTML.length).toBeGreaterThan(0);
    });
  });
});
