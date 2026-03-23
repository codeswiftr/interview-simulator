import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderPage } from '../../test/utils/pageTestUtils';
import InterviewPage from '../InterviewPage';

// Mock audio recording hook
vi.mock('../../hooks/useAudioRecording', () => ({
  useAudioRecording: () => ({
    state: 'idle',
    duration: 0,
    previewUrl: null,
    previewBlob: null,
    mimeType: null,
    error: null,
    start: vi.fn(),
    stop: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    reset: vi.fn(),
    playPreview: vi.fn(),
    pausePreview: vi.fn(),
    isPlaying: false,
    currentTime: 0,
    previewDuration: 0,
  }),
}));

// Mock coaching hint hook
vi.mock('../../hooks/useCoachingHint', () => ({
  useCoachingHint: () => ({
    hint: null,
    isLoading: false,
    getHint: vi.fn(),
    clearHint: vi.fn(),
    isCoachEnabled: false,
    toggleCoach: vi.fn(),
  }),
}));

describe('InterviewPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Page Structure', () => {
    it('should render without crashing', () => {
      const { container } = renderPage(<InterviewPage />, {
        initialRoute: '/interview/test-id',
      });

      expect(container).toBeInTheDocument();
    });

    it('should render within providers without errors', () => {
      renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      // Page should render without throwing context errors
      expect(document.body.textContent).not.toContain('useInterview must be used');
    });

    it('should render content', () => {
      const { container } = renderPage(<InterviewPage />, { initialRoute: '/interview/test-id' });

      // Container should have content
      expect(container.innerHTML.length).toBeGreaterThan(0);
    });
  });
});
