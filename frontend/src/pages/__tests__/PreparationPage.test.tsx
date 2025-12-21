import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderPage, waitFor, screen } from '../../test/utils/pageTestUtils';
import PreparationPage from '../PreparationPage';
import type { VoiceInputButtonProps } from '../../components/common/VoiceInputButton';

// Mock VoiceInputButton to avoid speech recognition API in tests
vi.mock('../../components/common/VoiceInputButton', () => ({
  VoiceInputButton: ({ onTranscript, disabled }: VoiceInputButtonProps) => (
    <button
      onClick={() => onTranscript && onTranscript('Mocked transcript')}
      disabled={disabled}
      data-testid="voice-input-button"
    >
      Voice
    </button>
  ),
}));

// Mock useSpeechSynthesis
vi.mock('../../hooks/useSpeechSynthesis', () => ({
  useSpeechSynthesis: () => ({
    speak: vi.fn(),
    stop: vi.fn(),
    isSpeaking: false,
    isSupported: false,
    error: null,
    setVoice: vi.fn(),
    setRate: vi.fn(),
    setPitch: vi.fn(),
    setVolume: vi.fn(),
    voices: [],
  }),
}));

// Mock useSpeechRecognition
vi.mock('../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: () => ({
    startListening: vi.fn(),
    stopListening: vi.fn(),
    resetTranscript: vi.fn(),
    transcript: '',
    isListening: false,
    isSupported: false,
  }),
}));

// Mock useConversationMode
vi.mock('../../hooks/useConversationMode', () => ({
  useConversationMode: () => ({
    mode: 'idle',
    startConversation: vi.fn(),
    endConversation: vi.fn(),
    mentorSay: vi.fn(),
    transitionTo: vi.fn(),
    interrupt: vi.fn(),
  }),
}));

describe('PreparationPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Detective Stage', () => {
    it('should render detective stage intro when page loads', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Detective stage intro should be displayed
        expect(screen.getByText(/step 1|answer questions/i)).toBeInTheDocument();
      });
    });

    it('should display help text explaining the flow', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        expect(screen.getByText(/help us understand your experience/i)).toBeInTheDocument();
      });
    });

    it('should show back to questions button', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        expect(screen.getByText(/back to questions/i)).toBeInTheDocument();
      });
    });
  });

  describe('Component Structure', () => {
    it('should render within PreparationProvider context', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      // Page should render without throwing context errors
      await waitFor(() => {
        expect(document.body.textContent).not.toContain('usePreparation must be used');
      });
    });

    it('should render main content container', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      // The main page container should exist
      await waitFor(() => {
        const container = document.querySelector('.container');
        expect(container).toBeInTheDocument();
      });
    });
  });
});
